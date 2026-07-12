"""Project-local experiment and passthrough evidence records."""

import json
import os
import tempfile
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from skill_lab.config import ConfigError, guard_project_path
from skill_lab.models import ResolvedSkill

RECORD_SCHEMA_VERSION = 1


class RunRecordError(RuntimeError):
    """Raised when project-local evidence cannot be written safely."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _atomic_text(path: Path, text: str) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _prepare(project_root: Path) -> Path:
    try:
        state = guard_project_path(project_root, project_root / ".skilllab")
        state.mkdir(parents=True, exist_ok=True)
        ignore = guard_project_path(project_root, state / ".gitignore")
        if not ignore.exists() or ignore.read_text(encoding="utf-8") != "/runs/\n":
            _atomic_text(ignore, "/runs/\n")
        runs = guard_project_path(project_root, state / "runs")
        runs.mkdir(parents=True, exist_ok=True)
        return runs
    except (ConfigError, OSError) as exc:
        raise RunRecordError(str(exc)) from exc


def _record_path(project_root: Path) -> Path:
    runs = _prepare(project_root)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return runs / f"{stamp}-{uuid.uuid4()}.json"


def _write_json(project_root: Path, path: Path, data: dict[str, Any]) -> None:
    try:
        guarded = guard_project_path(project_root, path)
        _atomic_text(guarded, json.dumps(data, indent=2, sort_keys=True) + "\n")
    except (ConfigError, OSError, TypeError) as exc:
        raise RunRecordError(str(exc)) from exc


def _locator(item: ResolvedSkill) -> dict[str, str] | None:
    locator = item.skill.locator
    if locator is None:
        return None
    return {"kind": locator.kind.value, "value": locator.value, "name": locator.name}


def create_run_record(
    project_root: Path,
    *,
    mode: str,
    invocation_cwd: Path,
    resolved: Sequence[ResolvedSkill],
    codex_version: str | None = None,
    model: str | None = None,
    git_commit: str | None = None,
    preflight: dict[str, Any] | None = None,
) -> Path:
    """Create the required pre-launch evidence for an exact experiment."""
    path = _record_path(project_root)
    try:
        relative_cwd = invocation_cwd.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise RunRecordError("invocation cwd is outside project root") from exc
    skills = [
        {
            "locator": _locator(item),
            "name": item.skill.name,
            "scope": item.skill.scope,
            "version": item.skill.version,
            "fingerprint": item.skill.fingerprint,
            "enabled": item.enabled,
            "source": item.source.value,
        }
        for item in resolved
        if item.enabled
    ]
    warnings = sorted(
        {warning for item in resolved if item.enabled for warning in item.skill.dependencies}
    )
    data: dict[str, Any] = {
        "schema_version": RECORD_SCHEMA_VERSION,
        "run_id": path.stem.split("-", 1)[1],
        "mode": mode,
        "status": "started",
        "started_at": _utc_now(),
        "invocation_cwd": relative_cwd or ".",
        "codex_version": codex_version,
        "model": model,
        "git_commit": git_commit,
        "effective_skills": skills,
        "dependency_warnings": warnings,
        "preflight": preflight or {},
    }
    _write_json(project_root, path, data)
    return path


def create_passthrough_record(project_root: Path, *, reason: str) -> Path:
    """Best-effort evidence for a normal Codex launch with unknown skills."""
    path = _record_path(project_root)
    data = {
        "schema_version": RECORD_SCHEMA_VERSION,
        "run_id": path.stem.split("-", 1)[1],
        "mode": "passthrough",
        "status": "started",
        "started_at": _utc_now(),
        "effective_skills": "unknown",
        "reason": reason,
    }
    _write_json(project_root, path, data)
    return path


def finish_run_record(project_root: Path, path: Path, *, exit_code: int) -> None:
    """Atomically finish an existing record with the child result."""
    try:
        guarded = guard_project_path(project_root, path)
        data = json.loads(guarded.read_text(encoding="utf-8"))
    except (ConfigError, OSError, json.JSONDecodeError) as exc:
        raise RunRecordError(str(exc)) from exc
    data["status"] = "completed" if exit_code == 0 else "failed"
    data["exit_code"] = exit_code
    data["ended_at"] = _utc_now()
    _write_json(project_root, guarded, data)
