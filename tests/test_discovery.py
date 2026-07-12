import json
from pathlib import Path

from skill_lab.discovery import (
    discover_filesystem_inventory,
    fingerprint_skill,
    normalize_skills_response,
)
from skill_lab.models import DiscoveryMode, LocatorKind


def write_skill(path: Path, *, name: str, description: str = "Useful skill") -> Path:
    path.mkdir(parents=True)
    skill_md = path / "SKILL.md"
    skill_md.write_text(
        f"---\nname: {name}\ndescription: {description}\nversion: 1.2.3\n---\n\nDo work.\n"
    )
    return skill_md


def test_normalizes_current_codex_skills_list_contract(tmp_path: Path):
    project = tmp_path / "project"
    codex_home = tmp_path / "codex"
    skill_path = write_skill(codex_home / "skills/alpha", name="alpha")
    payload = {
        "data": [
            {
                "cwd": str(project),
                "skills": [
                    {
                        "name": "alpha",
                        "description": "Alpha description",
                        "enabled": True,
                        "path": str(skill_path),
                        "scope": "user",
                        "interface": {"displayName": "Alpha"},
                        "dependencies": {"tools": [{"type": "env_var", "value": "ALPHA_TOKEN"}]},
                    }
                ],
                "errors": [],
            }
        ]
    }

    result = normalize_skills_response(payload, project, codex_home)

    assert result.mode is DiscoveryMode.EXACT
    assert len(result.skills) == 1
    found = result.skills[0]
    assert found.runtime_path == skill_path.resolve()
    assert found.locator.kind is LocatorKind.CODEX_HOME
    assert found.enabled is True
    assert found.package == "user"
    assert found.dependencies == ("env_var:ALPHA_TOKEN",)


def test_codex_entry_errors_make_catalog_degraded(tmp_path: Path):
    payload = {"data": [{"cwd": str(tmp_path), "skills": [], "errors": [{"message": "bad skill"}]}]}

    result = normalize_skills_response(payload, tmp_path, tmp_path / "codex")

    assert result.mode is DiscoveryMode.DEGRADED
    assert result.errors == ("bad skill",)


def test_filesystem_inventory_checks_only_roots_and_direct_children(tmp_path: Path):
    project = tmp_path / "project"
    codex_home = tmp_path / "codex"
    project_skill = write_skill(project / ".codex/skills/local", name="local")
    user_skill = write_skill(codex_home / "skills/user", name="user")
    write_skill(codex_home / "skills/group/deep", name="too-deep")
    (codex_home / "skills/alias").symlink_to(user_skill.parent, target_is_directory=True)
    script_marker = tmp_path / "executed"
    (user_skill.parent / "install.sh").write_text(f"touch {script_marker}\n")

    result = discover_filesystem_inventory(project, codex_home)

    assert result.mode is DiscoveryMode.DEGRADED
    assert [item.name for item in result.skills] == ["local", "user"]
    assert {item.runtime_path for item in result.skills} == {
        project_skill.resolve(),
        user_skill.resolve(),
    }
    assert not script_marker.exists()


def test_fingerprint_prefers_version_then_hashes_metadata(tmp_path: Path):
    versioned = write_skill(tmp_path / "versioned", name="versioned")
    assert fingerprint_skill(versioned) == "version:1.2.3"

    unversioned = tmp_path / "plain"
    unversioned.mkdir()
    skill_md = unversioned / "SKILL.md"
    skill_md.write_text("---\nname: plain\ndescription: Plain\n---\nBody\n")
    (unversioned / "SKILL.json").write_text(json.dumps({"interface": {"displayName": "Plain"}}))

    first = fingerprint_skill(skill_md)
    (unversioned / "SKILL.json").write_text(json.dumps({"interface": {"displayName": "Changed"}}))
    second = fingerprint_skill(skill_md)

    assert first.startswith("sha256:")
    assert first != second
