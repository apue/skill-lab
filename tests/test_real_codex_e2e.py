"""Opt-in release checks against the locally installed Codex binary."""

import fcntl
import os
import pty
import select
import shutil
import signal
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path

import pytest

from skill_lab.codex import CodexClient, build_skill_overrides
from skill_lab.discovery import normalize_skills_response
from skill_lab.models import ResolutionSource, ResolvedSkill

pytestmark = [
    pytest.mark.real_codex_e2e,
    pytest.mark.skipif(
        os.environ.get("SKILLLAB_REAL_CODEX_E2E") != "1",
        reason="set SKILLLAB_REAL_CODEX_E2E=1 to run the release gate",
    ),
    pytest.mark.skipif(sys.platform != "darwin", reason="MVP release gate targets macOS"),
]


def _isolated_environment(root: Path) -> dict[str, str]:
    home = root / "home"
    codex_home = root / "codex-home"
    home.mkdir()
    codex_home.mkdir()
    environment = dict(os.environ)
    environment.update(
        {
            "HOME": str(home),
            "CODEX_HOME": str(codex_home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_DATA_HOME": str(home / ".local/share"),
            "XDG_STATE_HOME": str(home / ".local/state"),
        }
    )
    return environment


def _fixture_project(root: Path) -> tuple[Path, Path]:
    project = root / "project"
    skill = root / "codex-home/skills/release-fixture/SKILL.md"
    project.mkdir()
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\n"
        "name: release-fixture\n"
        "description: Isolated Skill Lab release fixture\n"
        "---\n\n"
        "Use this only as a release fixture.\n"
    )
    return project, skill


def test_real_app_server_discovery_and_preflight(tmp_path: Path):
    binary = shutil.which("codex")
    if binary is None:
        pytest.skip("Codex CLI is not installed")
    environment = _isolated_environment(tmp_path)
    project, skill_path = _fixture_project(tmp_path)
    client = CodexClient(binary=binary, environment=environment)

    payload = client.list_skills(project, force_reload=True)
    discovery = normalize_skills_response(payload, project, Path(environment["CODEX_HOME"]))

    fixture = next(item for item in discovery.skills if item.name == "release-fixture")
    assert fixture.runtime_path == skill_path.resolve()
    resolved = tuple(
        ResolvedSkill(
            item,
            False if item.name == "release-fixture" else item.enabled,
            ResolutionSource.RUN,
        )
        for item in discovery.skills
    )
    assert client.preflight(project, resolved)


def test_real_native_codex_starts_in_a_pty(tmp_path: Path):
    binary = shutil.which("codex")
    if binary is None:
        pytest.skip("Codex CLI is not installed")
    environment = _isolated_environment(tmp_path)
    project, _skill_path = _fixture_project(tmp_path)
    client = CodexClient(binary=binary, environment=environment)
    payload = client.list_skills(project)
    discovery = normalize_skills_response(payload, project, Path(environment["CODEX_HOME"]))
    resolved = tuple(
        ResolvedSkill(item, item.enabled, ResolutionSource.RUN) for item in discovery.skills
    )

    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 100, 0, 0))
    process = subprocess.Popen(  # noqa: S603
        [binary, *build_skill_overrides(resolved), "-C", str(project)],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env=environment,
        start_new_session=True,
    )
    os.close(slave)
    output = bytearray()
    deadline = time.monotonic() + 10
    try:
        while time.monotonic() < deadline and not output and process.poll() is None:
            readable, _, _ = select.select([master], [], [], 0.25)
            if readable:
                output.extend(os.read(master, 65536))
        assert output, "Codex produced no terminal output"
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
        os.close(master)
