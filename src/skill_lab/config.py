"""Project root, portable locator, and project configuration handling."""

import json
import os
import tempfile
import tomllib
from pathlib import Path

from skill_lab.models import LocatorKind, SkillLayer, SkillLocator

SCHEMA_VERSION = 1


class ConfigError(ValueError):
    """Raised for unsafe or invalid Skill Lab project configuration."""


def find_project_root(cwd: Path) -> Path:
    """Return the containing Git root, or the resolved cwd outside Git."""
    current = cwd.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def guard_project_path(project_root: Path, candidate: Path) -> Path:
    """Resolve a prospective path and ensure it remains under project_root."""
    root = project_root.resolve()
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ConfigError(f"path resolves outside project root: {candidate}") from exc
    return resolved


def make_locator(
    runtime_path: Path,
    scope: str,
    name: str,
    project_root: Path,
    codex_home: Path,
) -> SkillLocator | None:
    """Create a portable locator when the runtime path has a supported base."""
    path = runtime_path.resolve(strict=False)
    for kind, base in (
        (LocatorKind.PROJECT, project_root.resolve()),
        (LocatorKind.CODEX_HOME, codex_home.resolve()),
    ):
        try:
            relative = path.relative_to(base)
        except ValueError:
            continue
        return SkillLocator(kind, relative.as_posix(), name)
    if scope == "system":
        return SkillLocator(LocatorKind.SYSTEM, name, name)
    return None


def _parse_locators(value: object, field: str) -> frozenset[SkillLocator]:
    if value is None:
        return frozenset()
    if not isinstance(value, list):
        raise ConfigError(f"{field} must be an array of locator tables")
    parsed: set[SkillLocator] = set()
    for row in value:
        if not isinstance(row, dict) or set(row) != {"kind", "value", "name"}:
            raise ConfigError(f"invalid {field} locator")
        try:
            parsed.add(SkillLocator(LocatorKind(row["kind"]), row["value"], row["name"]))
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"invalid {field} locator") from exc
    return frozenset(parsed)


def load_project_config(project_root: Path) -> SkillLayer:
    """Load the versioned project layer; a missing file means no overrides."""
    path = project_root / ".skilllab/config.toml"
    if not path.exists():
        return SkillLayer()
    guard_project_path(project_root, path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"invalid project config: {path}") from exc
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ConfigError(f"unsupported schema_version: {data.get('schema_version')!r}")
    unexpected = set(data) - {"schema_version", "include", "exclude"}
    if unexpected:
        raise ConfigError(f"unknown project config fields: {sorted(unexpected)}")
    layer = SkillLayer(
        _parse_locators(data.get("include"), "include"),
        _parse_locators(data.get("exclude"), "exclude"),
    )
    if layer.include & layer.exclude:
        raise ConfigError("a locator cannot appear in both include and exclude")
    return layer


def _encode_layer(layer: SkillLayer) -> str:
    lines = [f"schema_version = {SCHEMA_VERSION}", ""]
    for field, locators in (("include", layer.include), ("exclude", layer.exclude)):
        for locator in sorted(locators):
            lines.extend(
                [
                    f"[[{field}]]",
                    f"kind = {json.dumps(locator.kind.value)}",
                    f"value = {json.dumps(locator.value)}",
                    f"name = {json.dumps(locator.name)}",
                    "",
                ]
            )
    return "\n".join(lines)


def save_project_config(project_root: Path, layer: SkillLayer) -> Path:
    """Atomically save a validated project override layer."""
    if layer.include & layer.exclude:
        raise ConfigError("a locator cannot appear in both include and exclude")
    state_dir = guard_project_path(project_root, project_root / ".skilllab")
    state_dir.mkdir(parents=True, exist_ok=True)
    path = guard_project_path(project_root, state_dir / "config.toml")
    fd, temporary = tempfile.mkstemp(prefix=".config.", suffix=".toml", dir=state_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(_encode_layer(layer))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return path
