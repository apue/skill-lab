from pathlib import Path

import pytest

from skill_lab.models import InstalledSkill, LocatorKind, SkillLayer, SkillLocator
from skill_lab.resolution import ResolutionError, layer_for_final, resolve_skills


def skill(name: str, *, enabled: bool) -> InstalledSkill:
    locator = SkillLocator(LocatorKind.CODEX_HOME, f"skills/{name}/SKILL.md", name)
    return InstalledSkill(
        runtime_path=Path(f"/runtime/{name}/SKILL.md"),
        locator=locator,
        name=name,
        description=f"{name} description",
        enabled=enabled,
        scope="user",
        package="user",
        fingerprint=f"sha256:{name}",
    )


def test_resolver_applies_global_project_and_run_layers():
    alpha = skill("alpha", enabled=True)
    beta = skill("beta", enabled=False)

    result = resolve_skills(
        [beta, alpha],
        SkillLayer(include=frozenset({beta.locator}), exclude=frozenset({alpha.locator})),
        SkillLayer(include=frozenset({alpha.locator})),
    )

    assert [(item.skill.name, item.enabled, item.source.value) for item in result.project] == [
        ("alpha", False, "project"),
        ("beta", True, "project"),
    ]
    assert [(item.skill.name, item.enabled, item.source.value) for item in result.run] == [
        ("alpha", True, "run"),
        ("beta", True, "project"),
    ]
    assert result.project_delta.exclude == frozenset({alpha.locator})
    assert result.run_delta.include == frozenset({alpha.locator})


def test_resolver_rejects_conflicts_and_unknown_locators():
    alpha = skill("alpha", enabled=True)
    missing = SkillLocator(LocatorKind.SYSTEM, "missing", "missing")

    with pytest.raises(ResolutionError, match="project.*both include and exclude"):
        resolve_skills(
            [alpha],
            SkillLayer(include=frozenset({alpha.locator}), exclude=frozenset({alpha.locator})),
            SkillLayer(),
        )

    with pytest.raises(ResolutionError, match="run.*unknown skill locator"):
        resolve_skills([alpha], SkillLayer(), SkillLayer(include=frozenset({missing})))


def test_resolver_rejects_ambiguous_portable_locators():
    alpha = skill("alpha", enabled=True)
    duplicate = InstalledSkill(**{**alpha.__dict__, "runtime_path": Path("/other/alpha/SKILL.md")})

    with pytest.raises(ResolutionError, match="ambiguous skill locator"):
        resolve_skills([alpha, duplicate], SkillLayer(), SkillLayer())


def test_layer_for_final_creates_minimal_delta_from_global():
    alpha = skill("alpha", enabled=True)
    beta = skill("beta", enabled=False)

    layer = layer_for_final([alpha, beta], enabled_locators=frozenset({beta.locator}))

    assert layer.include == frozenset({beta.locator})
    assert layer.exclude == frozenset({alpha.locator})


def test_layer_for_final_rejects_unportable_skill_changes():
    alpha = skill("alpha", enabled=True)
    unportable = InstalledSkill(
        runtime_path=Path("/external/temp/SKILL.md"),
        locator=None,
        name="temp",
        description="temporary",
        enabled=False,
        scope="user",
        package="user",
        fingerprint="sha256:temp",
    )

    with pytest.raises(ResolutionError, match="cannot be saved as a project default"):
        layer_for_final(
            [alpha, unportable], enabled_runtime_paths=frozenset({unportable.runtime_path})
        )
