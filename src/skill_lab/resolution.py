"""Pure three-layer skill state resolution."""

from collections.abc import Iterable, Sequence
from pathlib import Path

from skill_lab.models import (
    InstalledSkill,
    ResolutionResult,
    ResolutionSource,
    ResolvedSkill,
    SkillLayer,
    SkillLocator,
)


class ResolutionError(ValueError):
    """Raised when a deterministic effective set cannot be produced."""


def _validate_layer(name: str, layer: SkillLayer, known: set[SkillLocator]) -> None:
    conflict = layer.include & layer.exclude
    if conflict:
        raise ResolutionError(f"{name} layer has locators in both include and exclude: {conflict}")
    unknown = (layer.include | layer.exclude) - known
    if unknown:
        raise ResolutionError(f"{name} layer references unknown skill locator: {unknown}")


def _stable(skills: Iterable[InstalledSkill]) -> list[InstalledSkill]:
    return sorted(
        skills,
        key=lambda item: (item.package.casefold(), item.name.casefold(), str(item.runtime_path)),
    )


def resolve_skills(
    installed: Sequence[InstalledSkill], project: SkillLayer, run: SkillLayer
) -> ResolutionResult:
    """Apply project and run overrides over the discovered Codex baseline."""
    locator_counts: dict[SkillLocator, int] = {}
    for item in installed:
        if item.locator is not None:
            locator_counts[item.locator] = locator_counts.get(item.locator, 0) + 1
    ambiguous = {locator for locator, count in locator_counts.items() if count > 1}
    if ambiguous:
        raise ResolutionError(f"ambiguous skill locator: {ambiguous}")
    known = set(locator_counts)
    _validate_layer("project", project, known)
    _validate_layer("run", run, known)

    project_items: list[ResolvedSkill] = []
    run_items: list[ResolvedSkill] = []
    for item in _stable(installed):
        project_enabled = item.enabled
        project_source = ResolutionSource.GLOBAL
        if item.locator in project.include:
            project_enabled = True
            project_source = ResolutionSource.PROJECT
        elif item.locator in project.exclude:
            project_enabled = False
            project_source = ResolutionSource.PROJECT
        project_items.append(ResolvedSkill(item, project_enabled, project_source))

        run_enabled = project_enabled
        run_source = project_source
        if item.locator in run.include:
            run_enabled = True
            run_source = ResolutionSource.RUN
        elif item.locator in run.exclude:
            run_enabled = False
            run_source = ResolutionSource.RUN
        run_items.append(ResolvedSkill(item, run_enabled, run_source))

    return ResolutionResult(tuple(project_items), tuple(run_items), project, run)


def layer_for_final(
    installed: Sequence[InstalledSkill],
    *,
    enabled_locators: frozenset[SkillLocator] | None = None,
    enabled_runtime_paths: frozenset[Path] | None = None,
) -> SkillLayer:
    """Create the minimal project layer representing a desired final set."""
    if (enabled_locators is None) == (enabled_runtime_paths is None):
        raise TypeError("provide exactly one desired enabled set")
    include: set[SkillLocator] = set()
    exclude: set[SkillLocator] = set()
    for item in installed:
        desired = (
            item.locator in enabled_locators
            if enabled_locators is not None
            else item.runtime_path in enabled_runtime_paths  # type: ignore[operator]
        )
        if desired == item.enabled:
            continue
        if item.locator is None:
            raise ResolutionError(f"{item.name} cannot be saved as a project default")
        (include if desired else exclude).add(item.locator)
    return SkillLayer(frozenset(include), frozenset(exclude))
