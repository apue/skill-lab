import json
from pathlib import Path

import pytest

from skill_lab.models import (
    InstalledSkill,
    LocatorKind,
    ResolutionSource,
    ResolvedSkill,
    SkillLocator,
)
from skill_lab.records import (
    RunRecordError,
    create_passthrough_record,
    create_run_record,
    finish_run_record,
)


def resolved_skill(tmp_path: Path) -> ResolvedSkill:
    skill = InstalledSkill(
        runtime_path=tmp_path / "external/alpha/SKILL.md",
        locator=SkillLocator(LocatorKind.CODEX_HOME, "skills/alpha/SKILL.md", "alpha"),
        name="alpha",
        description="alpha",
        enabled=True,
        scope="user",
        package="user",
        fingerprint="sha256:abc",
        version=None,
        dependencies=("env_var:ALPHA_TOKEN",),
    )
    return ResolvedSkill(skill, True, ResolutionSource.RUN)


def test_experiment_record_is_project_local_private_and_finishable(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()

    path = create_run_record(
        project,
        mode="experiment_once",
        invocation_cwd=project,
        resolved=[resolved_skill(tmp_path)],
        codex_version="codex-cli 0.144.1",
        git_commit="abc123",
        preflight={"matched": True},
    )

    assert path.parent == project / ".skilllab/runs"
    assert (project / ".skilllab/.gitignore").read_text() == "/runs/\n"
    text = path.read_text()
    assert str(tmp_path / "external") not in text
    data = json.loads(text)
    assert data["status"] == "started"
    assert data["effective_skills"][0]["locator"]["value"] == "skills/alpha/SKILL.md"
    assert data["dependency_warnings"] == ["env_var:ALPHA_TOKEN"]

    finish_run_record(project, path, exit_code=17)
    finished = json.loads(path.read_text())
    assert finished["status"] == "failed"
    assert finished["exit_code"] == 17
    assert "ended_at" in finished


def test_passthrough_record_never_claims_effective_skills(tmp_path: Path):
    path = create_passthrough_record(tmp_path, reason="app-server unavailable")
    data = json.loads(path.read_text())

    assert data["mode"] == "passthrough"
    assert data["effective_skills"] == "unknown"
    assert data["reason"] == "app-server unavailable"


def test_records_reject_skilllab_symlink_escape(tmp_path: Path):
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / ".skilllab").symlink_to(outside, target_is_directory=True)

    with pytest.raises(RunRecordError, match="outside project root"):
        create_passthrough_record(project, reason="degraded")
