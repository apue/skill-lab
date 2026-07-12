"""Codex App Server protocol and native CLI launch adapter."""

import json
import selectors
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from skill_lab.models import ResolvedSkill

Runner = Callable[..., subprocess.CompletedProcess[str]]
ProcessFactory = Callable[..., subprocess.Popen[str]]
LineReader = Callable[[Any, float], str]


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


def _default_process_factory(argv: Sequence[str], **kwargs: Any) -> subprocess.Popen[str]:
    try:
        return subprocess.Popen(argv, **kwargs)  # noqa: S603
    except (FileNotFoundError, PermissionError) as exc:
        raise CodexUnavailableError(f"cannot execute Codex: {argv[0]}") from exc


def _default_line_reader(stream: Any, timeout: float) -> str:
    with selectors.DefaultSelector() as selector:
        selector.register(stream, selectors.EVENT_READ)
        if not selector.select(timeout):
            raise CodexProtocolError("Codex App Server timed out")
    return stream.readline()


def _toml_string(value: str) -> str:
    return json.dumps(value)


def build_skill_overrides(resolved: Sequence[ResolvedSkill]) -> list[str]:
    """Build a complete, one-shot skills.config layer for Codex."""
    rows: list[str] = []
    for item in sorted(resolved, key=lambda value: str(value.skill.runtime_path)):
        skill_file = str(item.skill.runtime_path)
        enabled = "true" if item.enabled else "false"
        rows.append(f"{{path={_toml_string(skill_file)},enabled={enabled}}}")
    return ["-c", f"skills.config=[{','.join(rows)}]"]


class CodexClient:
    """Short-lived stdio JSONL client for Codex App Server."""

    def __init__(
        self,
        *,
        binary: str = "codex",
        timeout: float = 10.0,
        environment: Mapping[str, str] | None = None,
        runner: Runner | None = None,
        process_factory: ProcessFactory = _default_process_factory,
        line_reader: LineReader = _default_line_reader,
    ) -> None:
        self.binary = binary
        self.timeout = timeout
        self.environment = dict(environment) if environment is not None else None
        self.runner = runner
        self.process_factory = process_factory
        self.line_reader = line_reader

    @staticmethod
    def _messages(cwd: Path, force_reload: bool) -> list[dict[str, object]]:
        return [
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

    @staticmethod
    def _result(response: dict[str, object]) -> dict[str, object]:
        if isinstance(response.get("error"), dict):
            error = response["error"]
            raise CodexProtocolError(str(error.get("message", "skills/list failed")))
        result = response.get("result")
        if not isinstance(result, dict):
            raise CodexProtocolError("skills/list returned an invalid result")
        return result

    def _read_response(self, process: Any, request_id: int) -> dict[str, object]:
        while True:
            line = self.line_reader(process.stdout, self.timeout)
            if not line:
                error = process.stderr.read().strip()
                raise CodexProtocolError(f"Codex App Server closed before response: {error}")
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CodexProtocolError("Codex App Server returned invalid JSON") from exc
            if isinstance(message, dict) and message.get("id") == request_id:
                return message

    def list_skills(
        self,
        cwd: Path,
        *,
        force_reload: bool = False,
        extra_args: Sequence[str] = (),
    ) -> dict[str, object]:
        messages = self._messages(cwd, force_reload)
        if self.runner is None:
            process_kwargs: dict[str, object] = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "bufsize": 1,
            }
            if self.environment is not None:
                process_kwargs["env"] = self.environment
            process = self.process_factory(
                [self.binary, *extra_args, "app-server"],
                **process_kwargs,
            )
            if process.stdin is None or process.stdout is None or process.stderr is None:
                raise CodexProtocolError("Codex App Server pipes are unavailable")
            try:
                process.stdin.write(f"{json.dumps(messages[0])}\n")
                process.stdin.flush()
                self._result(self._read_response(process, 0))
                for message in messages[1:]:
                    process.stdin.write(f"{json.dumps(message)}\n")
                process.stdin.flush()
                return self._result(self._read_response(process, 1))
            finally:
                process.stdin.close()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=1)

        serialized = "".join(f"{json.dumps(message)}\n" for message in messages)
        try:
            runner_kwargs: dict[str, object] = {
                "input": serialized,
                "capture_output": True,
                "text": True,
                "timeout": self.timeout,
            }
            if self.environment is not None:
                runner_kwargs["env"] = self.environment
            completed = self.runner(
                [self.binary, *extra_args, "app-server"],
                **runner_kwargs,
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
        return self._result(response)

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
