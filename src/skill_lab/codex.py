"""Codex App Server protocol and native CLI launch adapter."""

import json
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from skill_lab.models import ResolvedSkill

Runner = Callable[..., subprocess.CompletedProcess[str]]


class CodexError(RuntimeError):
    """Base class for Codex adapter failures."""


class CodexProtocolError(CodexError):
    """Raised for incompatible or malformed App Server responses."""


class CodexUnavailableError(CodexError):
    """Raised when the Codex executable cannot be run."""


def _default_runner(argv: Sequence[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, **kwargs)  # noqa: S603
    except (FileNotFoundError, PermissionError) as exc:
        raise CodexUnavailableError(f"cannot execute Codex: {argv[0]}") from exc


def _toml_string(value: str) -> str:
    return json.dumps(value)


def build_skill_overrides(resolved: Sequence[ResolvedSkill]) -> list[str]:
    """Build a complete, one-shot skills.config layer for Codex."""
    rows: list[str] = []
    for item in sorted(resolved, key=lambda value: str(value.skill.runtime_path)):
        directory = str(item.skill.runtime_path.parent)
        enabled = "true" if item.enabled else "false"
        rows.append(f"{{path={_toml_string(directory)},enabled={enabled}}}")
    return ["-c", f"skills.config=[{','.join(rows)}]"]


class CodexClient:
    """Short-lived stdio JSONL client for Codex App Server."""

    def __init__(
        self,
        *,
        binary: str = "codex",
        timeout: float = 10.0,
        runner: Runner = _default_runner,
    ) -> None:
        self.binary = binary
        self.timeout = timeout
        self.runner = runner

    def list_skills(
        self,
        cwd: Path,
        *,
        force_reload: bool = False,
        extra_args: Sequence[str] = (),
    ) -> dict[str, object]:
        messages = [
            {
                "method": "initialize",
                "id": 0,
                "params": {
                    "clientInfo": {
                        "name": "skill_lab",
                        "title": "Skill Lab",
                        "version": "0.1.0",
                    }
                },
            },
            {"method": "initialized", "params": {}},
            {
                "method": "skills/list",
                "id": 1,
                "params": {"cwds": [str(cwd)], "forceReload": force_reload},
            },
        ]
        serialized = "".join(f"{json.dumps(message)}\n" for message in messages)
        try:
            completed = self.runner(
                [self.binary, *extra_args, "app-server"],
                input=serialized,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise CodexProtocolError("Codex App Server timed out") from exc
        if completed.returncode != 0:
            raise CodexProtocolError(
                f"Codex App Server exited with {completed.returncode}: {completed.stderr.strip()}"
            )
        response: dict[str, object] | None = None
        for line in completed.stdout.splitlines():
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CodexProtocolError("Codex App Server returned invalid JSON") from exc
            if isinstance(message, dict) and message.get("id") == 1:
                response = message
                break
        if response is None:
            raise CodexProtocolError("Codex App Server did not answer skills/list")
        if isinstance(response.get("error"), dict):
            error = response["error"]
            raise CodexProtocolError(str(error.get("message", "skills/list failed")))
        result = response.get("result")
        if not isinstance(result, dict):
            raise CodexProtocolError("skills/list returned an invalid result")
        return result

    def preflight(self, cwd: Path, resolved: Sequence[ResolvedSkill]) -> bool:
        """Check that one-shot overrides produce the exact reviewed state."""
        payload = self.list_skills(
            cwd, force_reload=True, extra_args=build_skill_overrides(resolved)
        )
        data = payload.get("data")
        if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
            raise CodexProtocolError("preflight returned an invalid catalog")
        rows = data[0].get("skills")
        errors = data[0].get("errors")
        if not isinstance(rows, list) or errors:
            return False
        actual = {
            Path(row["path"]).resolve(): row["enabled"]
            for row in rows
            if isinstance(row, dict)
            and isinstance(row.get("path"), str)
            and isinstance(row.get("enabled"), bool)
        }
        expected = {item.skill.runtime_path.resolve(): item.enabled for item in resolved}
        return actual == expected


def launch_codex(
    cwd: Path,
    resolved: Sequence[ResolvedSkill] | None = None,
    *,
    binary: str = "codex",
    runner: Runner = _default_runner,
) -> int:
    """Launch the native Codex TUI and return its exit code."""
    overrides = build_skill_overrides(resolved) if resolved is not None else []
    completed = runner([binary, *overrides, "-C", str(cwd)])
    return completed.returncode
