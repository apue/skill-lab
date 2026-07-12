import json
import subprocess
from pathlib import Path

import pytest

from skill_lab.codex import (
    CodexClient,
    CodexProtocolError,
    build_skill_overrides,
    launch_codex,
)
from skill_lab.models import InstalledSkill, ResolutionSource, ResolvedSkill


class FakeRunner:
    def __init__(self, stdout: str = "", returncode: int = 0):
        self.stdout = stdout
        self.returncode = returncode
        self.calls: list[tuple[list[str], dict[str, object]]] = []

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), kwargs))
        return subprocess.CompletedProcess(argv, self.returncode, self.stdout, "")


class FakeStream:
    def __init__(self, process=None):
        self.process = process
        self.lines = []

    def write(self, value):
        self.process.received.append(json.loads(value))
        message = self.process.received[-1]
        if message["method"] == "initialize":
            self.process.stdout.lines.append(json.dumps({"id": 0, "result": {}}) + "\n")
        elif message["method"] == "skills/list":
            payload = {"data": [{"cwd": message["params"]["cwds"][0], "skills": [], "errors": []}]}
            self.process.stdout.lines.append(json.dumps({"id": 1, "result": payload}) + "\n")

    def flush(self):
        pass

    def readline(self):
        return self.lines.pop(0)

    def close(self):
        pass

    def read(self):
        return ""


class FakeProcess:
    def __init__(self):
        self.received = []
        self.stdout = FakeStream()
        self.stderr = FakeStream()
        self.stdin = FakeStream(self)
        self.returncode = 0

    def wait(self, timeout=None):
        return 0

    def terminate(self):
        self.returncode = -15


def resolved(name: str, enabled: bool) -> ResolvedSkill:
    skill = InstalledSkill(
        runtime_path=Path(f"/skills/{name}/SKILL.md"),
        locator=None,
        name=name,
        description=name,
        enabled=enabled,
        scope="user",
        package="user",
        fingerprint=f"sha256:{name}",
    )
    return ResolvedSkill(skill, enabled, ResolutionSource.RUN)


def test_app_server_client_sends_handshake_and_skills_list(tmp_path: Path):
    payload = {"data": [{"cwd": str(tmp_path), "skills": [], "errors": []}]}
    stdout = "\n".join(
        [
            json.dumps({"id": 0, "result": {"userAgent": "codex"}}),
            json.dumps({"id": 1, "result": payload}),
        ]
    )
    runner = FakeRunner(stdout)

    result = CodexClient(runner=runner).list_skills(tmp_path, force_reload=True)

    assert result == payload
    argv, kwargs = runner.calls[0]
    assert argv == ["codex", "app-server"]
    messages = [json.loads(line) for line in kwargs["input"].splitlines()]
    assert [message["method"] for message in messages] == [
        "initialize",
        "initialized",
        "skills/list",
    ]
    assert messages[-1]["params"] == {"cwds": [str(tmp_path)], "forceReload": True}
    assert kwargs["timeout"] == 10.0


def test_interactive_transport_waits_for_initialize_before_skills_list(tmp_path: Path):
    process = FakeProcess()
    calls = []

    def process_factory(*args, **kwargs):
        calls.append((args, kwargs))
        return process

    client = CodexClient(
        environment={"CODEX_HOME": str(tmp_path / "codex-home")},
        process_factory=process_factory,
        line_reader=lambda stream, timeout: stream.readline(),
    )

    result = client.list_skills(tmp_path)

    assert result["data"][0]["cwd"] == str(tmp_path)
    assert [message["method"] for message in process.received] == [
        "initialize",
        "initialized",
        "skills/list",
    ]
    assert calls[0][1]["env"] == {"CODEX_HOME": str(tmp_path / "codex-home")}


def test_app_server_client_reports_rpc_errors(tmp_path: Path):
    stdout = json.dumps({"id": 1, "error": {"code": -32601, "message": "missing"}})

    with pytest.raises(CodexProtocolError, match="missing"):
        CodexClient(runner=FakeRunner(stdout)).list_skills(tmp_path)


def test_skill_overrides_explicitly_set_every_discovered_skill():
    args = build_skill_overrides([resolved("alpha", True), resolved("beta", False)])

    assert args[0] == "-c"
    assert "skills.config=" in args[1]
    assert 'path="/skills/alpha/SKILL.md"' in args[1]
    assert "enabled=true" in args[1]
    assert 'path="/skills/beta/SKILL.md"' in args[1]
    assert "enabled=false" in args[1]


def test_preflight_requires_exact_enabled_paths(tmp_path: Path):
    alpha = resolved("alpha", True)
    beta = resolved("beta", False)
    payload = {
        "data": [
            {
                "cwd": str(tmp_path),
                "skills": [
                    {
                        "name": "alpha",
                        "description": "alpha",
                        "enabled": True,
                        "path": "/skills/alpha/SKILL.md",
                        "scope": "user",
                    },
                    {
                        "name": "beta",
                        "description": "beta",
                        "enabled": False,
                        "path": "/skills/beta/SKILL.md",
                        "scope": "user",
                    },
                ],
                "errors": [],
            }
        ]
    }
    stdout = json.dumps({"id": 1, "result": payload})
    client = CodexClient(runner=FakeRunner(stdout))

    assert client.preflight(tmp_path, [alpha, beta]) is True

    payload["data"][0]["skills"][1]["enabled"] = True
    mismatched = CodexClient(runner=FakeRunner(json.dumps({"id": 1, "result": payload})))
    assert mismatched.preflight(tmp_path, [alpha, beta]) is False


def test_native_launch_uses_argv_without_permission_overrides(tmp_path: Path):
    runner = FakeRunner(returncode=17)

    exit_code = launch_codex(tmp_path, [resolved("alpha", True)], runner=runner)

    assert exit_code == 17
    argv, kwargs = runner.calls[0]
    assert argv[:2] == ["codex", "-c"]
    assert argv[-2:] == ["-C", str(tmp_path)]
    assert kwargs == {}
    assert not any("sandbox" in arg or "approval" in arg for arg in argv)
