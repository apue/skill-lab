"""Read-only Codex skill discovery and metadata normalization."""

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

import yaml

from skill_lab.config import make_locator
from skill_lab.models import DiscoveryMode, DiscoveryResult, InstalledSkill


class DiscoveryError(ValueError):
    """Raised when a discovery payload or metadata file is invalid."""


def _frontmatter(skill_md: Path) -> dict[str, object]:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        raise DiscoveryError(f"cannot read skill metadata: {skill_md}") from exc
    if not text.startswith("---\n"):
        raise DiscoveryError(f"missing YAML frontmatter: {skill_md}")
    try:
        raw, _body = text[4:].split("\n---", 1)
        data = yaml.safe_load(raw)
    except (ValueError, yaml.YAMLError) as exc:
        raise DiscoveryError(f"invalid YAML frontmatter: {skill_md}") from exc
    if not isinstance(data, dict):
        raise DiscoveryError(f"invalid YAML frontmatter: {skill_md}")
    return data


def fingerprint_skill(skill_md: Path) -> str:
    """Return a declared version or a hash of the two allowed metadata files."""
    metadata = _frontmatter(skill_md)
    version = metadata.get("version")
    if isinstance(version, (str, int, float)):
        return f"version:{version}"
    digest = hashlib.sha256()
    digest.update(skill_md.read_bytes())
    skill_json = skill_md.with_name("SKILL.json")
    if skill_json.is_file():
        digest.update(skill_json.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _version(skill_md: Path) -> str | None:
    value = _frontmatter(skill_md).get("version")
    return str(value) if isinstance(value, (str, int, float)) else None


def _dependencies(value: object) -> tuple[str, ...]:
    if not isinstance(value, dict) or not isinstance(value.get("tools"), list):
        return ()
    rendered: list[str] = []
    for tool in value["tools"]:
        if isinstance(tool, dict) and isinstance(tool.get("type"), str):
            item = tool.get("value") or tool.get("description") or "unknown"
            rendered.append(f"{tool['type']}:{item}")
    return tuple(rendered)


def _skill_from_codex(row: object, project_root: Path, codex_home: Path) -> InstalledSkill:
    required = {"name": str, "description": str, "enabled": bool, "path": str, "scope": str}
    if not isinstance(row, dict) or any(not isinstance(row.get(k), t) for k, t in required.items()):
        raise DiscoveryError("invalid SkillMetadata in skills/list response")
    path = Path(row["path"]).resolve()
    return InstalledSkill(
        runtime_path=path,
        locator=make_locator(path, row["scope"], row["name"], project_root, codex_home),
        name=row["name"],
        description=row["description"],
        enabled=row["enabled"],
        scope=row["scope"],
        package=row["scope"],
        version=_version(path),
        fingerprint=fingerprint_skill(path),
        dependencies=_dependencies(row.get("dependencies")),
    )


def _error_message(value: object) -> str:
    if isinstance(value, dict):
        for key in ("message", "error"):
            if isinstance(value.get(key), str):
                return value[key]
    return json.dumps(value, sort_keys=True)


def normalize_skills_response(
    payload: object, project_root: Path, codex_home: Path
) -> DiscoveryResult:
    """Normalize the v2 skills/list response for exactly one requested cwd."""
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise DiscoveryError("invalid skills/list response")
    entries = payload["data"]
    if len(entries) != 1 or not isinstance(entries[0], dict):
        raise DiscoveryError("skills/list must return exactly one cwd entry")
    entry = entries[0]
    if not isinstance(entry.get("skills"), list) or not isinstance(entry.get("errors"), list):
        raise DiscoveryError("invalid skills/list cwd entry")
    errors = tuple(_error_message(value) for value in entry["errors"])
    unique: dict[Path, InstalledSkill] = {}
    for row in entry["skills"]:
        item = _skill_from_codex(row, project_root, codex_home)
        unique.setdefault(item.runtime_path, item)
    skills = tuple(sorted(unique.values(), key=lambda item: (item.package, item.name.casefold())))
    mode = DiscoveryMode.DEGRADED if errors else DiscoveryMode.EXACT
    return DiscoveryResult(skills, errors, mode)


def _candidate_skill_files(root: Path) -> Iterable[Path]:
    if (root / "SKILL.md").is_file():
        yield root / "SKILL.md"
    if not root.is_dir():
        return
    try:
        children = sorted(root.iterdir(), key=lambda path: path.name.casefold())
    except OSError:
        return
    for child in children:
        candidate = child / "SKILL.md"
        if candidate.is_file():
            yield candidate


def discover_filesystem_inventory(project_root: Path, codex_home: Path) -> DiscoveryResult:
    """Discover metadata from the two standard roots without inferring enablement."""
    roots = (project_root / ".codex/skills", codex_home / "skills")
    unique: dict[Path, InstalledSkill] = {}
    errors: list[str] = []
    for root in roots:
        for candidate in _candidate_skill_files(root):
            path = candidate.resolve()
            if path in unique:
                continue
            try:
                metadata = _frontmatter(path)
                name = metadata.get("name")
                description = metadata.get("description")
                if not isinstance(name, str) or not isinstance(description, str):
                    raise DiscoveryError(f"skill requires name and description: {path}")
                scope = "repo" if root == roots[0] else "user"
                unique[path] = InstalledSkill(
                    runtime_path=path,
                    locator=make_locator(path, scope, name, project_root, codex_home),
                    name=name,
                    description=description,
                    enabled=False,
                    scope=scope,
                    package=scope,
                    version=_version(path),
                    fingerprint=fingerprint_skill(path),
                )
            except DiscoveryError as exc:
                errors.append(str(exc))
    skills = tuple(sorted(unique.values(), key=lambda item: (item.package, item.name.casefold())))
    return DiscoveryResult(skills, tuple(errors), DiscoveryMode.DEGRADED)
