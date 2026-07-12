from pathlib import Path

import skill_lab.cli as cli
from skill_lab import __version__
from skill_lab.cli import run
from skill_lab.codex import CodexProtocolError, CodexUnavailableError
from skill_lab.config import load_project_config
from skill_lab.models import LaunchChoice
from skill_lab.records import RunRecordError


def write_skill(project: Path, name: str = "alpha") -> Path:
    path = project / ".codex/skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"---\nname: {name}\ndescription: Test skill\n---\nBody\n")
    return path


class FakeClient:
    def __init__(self, payload=None, error: Exception | None = None, preflight=True):
        self.payload = payload
        self.error = error
        self.preflight_result = preflight
        self.preflight_calls = []

    def list_skills(self, cwd, *, force_reload=False, extra_args=()):
        if self.error:
            raise self.error
        return self.payload

    def preflight(self, cwd, resolved):
        self.preflight_calls.append((cwd, list(resolved)))
        return self.preflight_result


class FakeApp:
    choice = LaunchChoice.ONCE
    staged = set()

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.staged_enabled = set(self.staged)

    def run(self):
        return self.choice


def payload(project: Path, skill_path: Path, *, enabled=True):
    return {
        "data": [
            {
                "cwd": str(project),
                "skills": [
                    {
                        "name": "alpha",
                        "description": "Test skill",
                        "enabled": enabled,
                        "path": str(skill_path),
                        "scope": "repo",
                    }
                ],
                "errors": [],
            }
        ]
    }


def test_version_flag(capsys):
    assert run(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"skilllab {__version__}"


def test_smoke_test(capsys):
    assert run(["--smoke-test"]) == 0
    assert capsys.readouterr().out.strip() == "Skill Lab app constructed successfully"


def test_launch_once_preflights_records_and_propagates_exit_code(tmp_path: Path):
    skill_path = write_skill(tmp_path)
    client = FakeClient(payload(tmp_path, skill_path))
    FakeApp.choice = LaunchChoice.ONCE
    FakeApp.staged = {skill_path.resolve()}
    launched = []

    def launcher(cwd, resolved):
        launched.append((cwd, resolved))
        return 23

    exit_code = run(
        [],
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
        client=client,
        app_factory=FakeApp,
        launcher=launcher,
    )

    assert exit_code == 23
    assert client.preflight_calls
    assert launched[0][1][0].enabled is True
    records = list((tmp_path / ".skilllab/runs").glob("*.json"))
    assert len(records) == 1
    assert '"exit_code": 23' in records[0].read_text()


def test_save_and_launch_writes_minimal_project_defaults(tmp_path: Path):
    skill_path = write_skill(tmp_path)
    client = FakeClient(payload(tmp_path, skill_path, enabled=True))
    FakeApp.choice = LaunchChoice.SAVE
    FakeApp.staged = set()

    exit_code = run(
        [],
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
        client=client,
        app_factory=FakeApp,
        launcher=lambda cwd, resolved: 0,
    )

    assert exit_code == 0
    config = load_project_config(tmp_path)
    assert len(config.exclude) == 1
    assert not config.include


def test_app_server_failure_allows_passthrough_without_overrides(tmp_path: Path):
    write_skill(tmp_path)
    client = FakeClient(error=CodexProtocolError("unsupported"))
    FakeApp.choice = LaunchChoice.NORMAL
    FakeApp.staged = set()
    calls = []

    exit_code = run(
        [],
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
        client=client,
        app_factory=FakeApp,
        launcher=lambda cwd, resolved: calls.append((cwd, resolved)) or 0,
    )

    assert exit_code == 0
    assert calls == [(tmp_path, None)]
    record = next((tmp_path / ".skilllab/runs").glob("*.json"))
    assert '"effective_skills": "unknown"' in record.read_text()


def test_preflight_mismatch_can_fall_back_to_normal_launch(tmp_path: Path):
    skill_path = write_skill(tmp_path)
    client = FakeClient(payload(tmp_path, skill_path), preflight=False)
    FakeApp.choice = LaunchChoice.ONCE
    FakeApp.staged = {skill_path.resolve()}
    calls = []

    exit_code = run(
        [],
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
        client=client,
        app_factory=FakeApp,
        launcher=lambda cwd, resolved: calls.append((cwd, resolved)) or 9,
        confirm_normal=lambda reason: "preflight" in reason,
    )

    assert exit_code == 9
    assert calls == [(tmp_path, None)]


def test_invalid_project_config_enters_degraded_ui(tmp_path: Path):
    skill_path = write_skill(tmp_path)
    state = tmp_path / ".skilllab"
    state.mkdir()
    (state / "config.toml").write_text("schema_version = 99\n")
    captured = {}

    class DegradedApp(FakeApp):
        choice = LaunchChoice.NORMAL

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            captured.update(kwargs)

    calls = []
    exit_code = run(
        [],
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
        client=FakeClient(payload(tmp_path, skill_path)),
        app_factory=DegradedApp,
        launcher=lambda cwd, resolved: calls.append((cwd, resolved)) or 0,
    )

    assert exit_code == 0
    assert captured["resolution"] is None
    assert "schema_version" in captured["discovery"].errors[0]
    assert calls == [(tmp_path, None)]


def test_experiment_record_failure_can_fall_back_without_overrides(tmp_path: Path, monkeypatch):
    skill_path = write_skill(tmp_path)
    FakeApp.choice = LaunchChoice.ONCE
    FakeApp.staged = {skill_path.resolve()}
    monkeypatch.setattr(
        cli,
        "create_run_record",
        lambda *args, **kwargs: (_ for _ in ()).throw(RunRecordError("read-only project")),
    )
    calls = []

    exit_code = run(
        [],
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
        client=FakeClient(payload(tmp_path, skill_path)),
        app_factory=FakeApp,
        launcher=lambda cwd, resolved: calls.append((cwd, resolved)) or 0,
        confirm_normal=lambda reason: "read-only" in reason,
    )

    assert exit_code == 0
    assert calls == [(tmp_path, None)]


def test_missing_codex_is_the_only_passthrough_launch_blocker(tmp_path: Path):
    skill_path = write_skill(tmp_path)
    FakeApp.choice = LaunchChoice.NORMAL
    FakeApp.staged = set()

    def unavailable(cwd, resolved):
        raise CodexUnavailableError("cannot execute Codex: codex")

    assert (
        run(
            [],
            cwd=tmp_path,
            codex_home=tmp_path / "codex-home",
            client=FakeClient(payload(tmp_path, skill_path)),
            app_factory=FakeApp,
            launcher=unavailable,
        )
        == 127
    )


def test_passthrough_record_failure_does_not_block_codex(tmp_path: Path, monkeypatch):
    skill_path = write_skill(tmp_path)
    FakeApp.choice = LaunchChoice.NORMAL
    FakeApp.staged = set()
    monkeypatch.setattr(
        cli,
        "create_passthrough_record",
        lambda *args, **kwargs: (_ for _ in ()).throw(RunRecordError("read-only project")),
    )
    calls = []

    exit_code = run(
        [],
        cwd=tmp_path,
        codex_home=tmp_path / "codex-home",
        client=FakeClient(payload(tmp_path, skill_path)),
        app_factory=FakeApp,
        launcher=lambda cwd, resolved: calls.append((cwd, resolved)) or 4,
    )

    assert exit_code == 4
    assert calls == [(tmp_path, None)]
