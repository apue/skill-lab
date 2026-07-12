from pathlib import Path

import pytest

from skill_lab.config import (
    ConfigError,
    find_project_root,
    guard_project_path,
    load_project_config,
    make_locator,
    save_project_config,
)
from skill_lab.models import LocatorKind, SkillLayer, SkillLocator


def test_find_project_root_uses_git_root_then_cwd(tmp_path: Path):
    repo = tmp_path / "repo"
    nested = repo / "src" / "pkg"
    nested.mkdir(parents=True)
    (repo / ".git").mkdir()

    assert find_project_root(nested) == repo.resolve()
    plain = tmp_path / "plain"
    plain.mkdir()
    assert find_project_root(plain) == plain.resolve()


def test_make_locator_uses_project_codex_home_and_system_bases(tmp_path: Path):
    project = tmp_path / "project"
    codex_home = tmp_path / "codex"
    project_skill = project / ".codex/skills/local/SKILL.md"
    user_skill = codex_home / "skills/user/SKILL.md"

    assert make_locator(project_skill, "repo", "local", project, codex_home) == SkillLocator(
        LocatorKind.PROJECT, ".codex/skills/local/SKILL.md", "local"
    )
    assert make_locator(user_skill, "user", "user", project, codex_home) == SkillLocator(
        LocatorKind.CODEX_HOME, "skills/user/SKILL.md", "user"
    )
    system_locator = make_locator(
        codex_home / "skills/.system/builtin/SKILL.md",
        "system",
        "builtin",
        project,
        codex_home,
    )
    assert system_locator == SkillLocator(LocatorKind.SYSTEM, "builtin", "builtin")
    assert make_locator(Path("/external/SKILL.md"), "user", "external", project, codex_home) is None


def test_project_config_round_trips_and_keeps_empty_config(tmp_path: Path):
    include = SkillLocator(LocatorKind.CODEX_HOME, "skills/alpha/SKILL.md", "alpha")
    exclude = SkillLocator(LocatorKind.SYSTEM, "bundled", "bundled")
    layer = SkillLayer(frozenset({include}), frozenset({exclude}))

    path = save_project_config(tmp_path, layer)

    assert path == tmp_path / ".skilllab/config.toml"
    assert load_project_config(tmp_path) == layer
    save_project_config(tmp_path, SkillLayer())
    text = path.read_text()
    assert "schema_version = 1" in text
    assert load_project_config(tmp_path) == SkillLayer()


def test_project_config_rejects_unknown_schema_and_conflict(tmp_path: Path):
    state = tmp_path / ".skilllab"
    state.mkdir()
    config = state / "config.toml"
    config.write_text("schema_version = 2\n")
    with pytest.raises(ConfigError, match="unsupported schema_version"):
        load_project_config(tmp_path)

    config.write_text(
        "schema_version = 1\n"
        '[[include]]\nkind = "system"\nvalue = "same"\nname = "same"\n'
        '[[exclude]]\nkind = "system"\nvalue = "same"\nname = "same"\n'
    )
    with pytest.raises(ConfigError, match="both include and exclude"):
        load_project_config(tmp_path)


def test_path_guard_rejects_skilllab_symlink_escape(tmp_path: Path):
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / ".skilllab").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ConfigError, match="outside project root"):
        guard_project_path(project, project / ".skilllab/config.toml")
    with pytest.raises(ConfigError, match="outside project root"):
        save_project_config(project, SkillLayer())
