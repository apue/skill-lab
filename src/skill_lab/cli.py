"""Command-line entry point and dependency orchestration for Skill Lab."""

import argparse
import os
from collections.abc import Callable, Sequence
from contextlib import suppress
from pathlib import Path
from typing import NoReturn

from skill_lab import __version__
from skill_lab.app import SkillLabApp
from skill_lab.codex import CodexClient, CodexError, launch_codex
from skill_lab.config import (
    ConfigError,
    find_project_root,
    load_project_config,
    save_project_config,
)
from skill_lab.discovery import (
    DiscoveryError,
    discover_filesystem_inventory,
    normalize_skills_response,
)
from skill_lab.models import (
    DiscoveryMode,
    DiscoveryResult,
    LaunchChoice,
    ResolutionSource,
    ResolvedSkill,
    SkillLayer,
)
from skill_lab.records import (
    RunRecordError,
    create_passthrough_record,
    create_run_record,
    finish_run_record,
)
from skill_lab.resolution import ResolutionError, layer_for_final, resolve_skills


def _confirm_normal(reason: str) -> bool:
    print(f"Skill Lab experiment unavailable: {reason}")
    try:
        answer = input("Launch Codex normally instead? [y/N] ")
    except EOFError:
        return False
    return answer.strip().casefold() in {"y", "yes"}


def _staged_resolution(app, resolution) -> tuple[ResolvedSkill, ...]:
    project_by_path = {item.skill.runtime_path: item for item in resolution.project}
    staged: list[ResolvedSkill] = []
    for item in resolution.run:
        enabled = item.skill.runtime_path in app.staged_enabled
        project = project_by_path[item.skill.runtime_path]
        source = project.source if enabled == project.enabled else ResolutionSource.RUN
        staged.append(ResolvedSkill(item.skill, enabled, source))
    return tuple(staged)


def _passthrough(
    project_root: Path,
    invocation_cwd: Path,
    reason: str,
    launcher: Callable,
) -> int:
    del invocation_cwd  # reserved for a future passthrough schema addition
    record = None
    with suppress(RunRecordError):
        record = create_passthrough_record(project_root, reason=reason)
    try:
        exit_code = launcher(project_root, None)
    except CodexError as exc:
        print(str(exc))
        return 127
    if record is not None:
        try:
            finish_run_record(project_root, record, exit_code=exit_code)
            print(f"Skill Lab record: {record}")
        except RunRecordError:
            pass
    return exit_code


def run(
    argv: Sequence[str] | None = None,
    *,
    cwd: Path | None = None,
    codex_home: Path | None = None,
    client=None,
    app_factory=SkillLabApp,
    launcher: Callable = launch_codex,
    confirm_normal: Callable[[str], bool] = _confirm_normal,
) -> int:
    """Discover, review, preflight, record, and launch one Codex session."""
    parser = argparse.ArgumentParser(prog="skilllab")
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args(argv)

    if args.version:
        print(f"skilllab {__version__}")
        return 0

    if args.smoke_test:
        SkillLabApp()
        print("Skill Lab app constructed successfully")
        return 0

    invocation_cwd = (cwd or Path.cwd()).resolve()
    project_root = find_project_root(invocation_cwd)
    resolved_codex_home = (
        codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    ).resolve()
    codex_client = client or CodexClient()

    try:
        payload = codex_client.list_skills(project_root)
        discovery = normalize_skills_response(payload, project_root, resolved_codex_home)
    except (CodexError, DiscoveryError, OSError) as exc:
        inventory = discover_filesystem_inventory(project_root, resolved_codex_home)
        discovery = DiscoveryResult(
            inventory.skills,
            (str(exc), *inventory.errors),
            DiscoveryMode.DEGRADED,
        )

    resolution = None
    if discovery.mode is DiscoveryMode.EXACT:
        try:
            project_layer = load_project_config(project_root)
            resolution = resolve_skills(discovery.skills, project_layer, SkillLayer())
        except (ConfigError, ResolutionError) as exc:
            discovery = DiscoveryResult(discovery.skills, (str(exc),), DiscoveryMode.DEGRADED)

    app = app_factory(
        project_root=project_root,
        discovery=discovery,
        resolution=resolution,
    )
    choice = app.run()
    if choice is None:
        return 0
    if choice is LaunchChoice.NORMAL or resolution is None:
        return _passthrough(
            project_root,
            invocation_cwd,
            "; ".join(discovery.errors) or "user selected normal launch",
            launcher,
        )

    staged = _staged_resolution(app, resolution)
    try:
        if not codex_client.preflight(project_root, staged):
            if confirm_normal("Codex preflight did not match the reviewed skill set"):
                return _passthrough(project_root, invocation_cwd, "preflight mismatch", launcher)
            return 2
    except CodexError as exc:
        if confirm_normal(str(exc)):
            return _passthrough(project_root, invocation_cwd, str(exc), launcher)
        return 2

    saved_layer = None
    if choice is LaunchChoice.SAVE:
        try:
            saved_layer = layer_for_final(
                discovery.skills,
                enabled_runtime_paths=frozenset(app.staged_enabled),
            )
        except ResolutionError as exc:
            if confirm_normal(str(exc)):
                return _passthrough(project_root, invocation_cwd, str(exc), launcher)
            return 2

    try:
        record = create_run_record(
            project_root,
            mode="saved_defaults" if choice is LaunchChoice.SAVE else "experiment_once",
            invocation_cwd=invocation_cwd,
            resolved=staged,
            preflight={"matched": True},
        )
    except RunRecordError as exc:
        if confirm_normal(str(exc)):
            return _passthrough(project_root, invocation_cwd, str(exc), launcher)
        return 2

    if saved_layer is not None:
        try:
            save_project_config(project_root, saved_layer)
        except ConfigError as exc:
            if confirm_normal(str(exc)):
                return _passthrough(project_root, invocation_cwd, str(exc), launcher)
            return 2

    try:
        exit_code = launcher(project_root, staged)
    except CodexError as exc:
        print(str(exc))
        exit_code = 127
    try:
        finish_run_record(project_root, record, exit_code=exit_code)
        print(f"Skill Lab record: {record}")
    except RunRecordError as exc:
        print(f"Skill Lab could not finish record: {exc}")
    return exit_code


def main() -> NoReturn:
    """Console script entry point."""
    raise SystemExit(run())
