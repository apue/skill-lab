from pathlib import Path

import pytest
from textual.widgets import Button, Input, OptionList, Static

from skill_lab.app import SkillLabApp
from skill_lab.models import (
    DiscoveryMode,
    DiscoveryResult,
    InstalledSkill,
    LaunchChoice,
    LocatorKind,
    SkillLayer,
    SkillLocator,
)
from skill_lab.resolution import resolve_skills


def skill(name: str, package: str, enabled: bool) -> InstalledSkill:
    return InstalledSkill(
        runtime_path=Path(f"/skills/{package}/{name}/SKILL.md"),
        locator=SkillLocator(LocatorKind.CODEX_HOME, f"skills/{name}/SKILL.md", name),
        name=name,
        description=f"Description for {name}",
        enabled=enabled,
        scope="user",
        package=package,
        fingerprint=f"sha256:{name}",
    )


def exact_app() -> SkillLabApp:
    skills = (skill("alpha", "package-a", True), skill("beta", "package-a", False))
    discovery = DiscoveryResult(skills, mode=DiscoveryMode.EXACT)
    return SkillLabApp(
        project_root=Path("/project"),
        discovery=discovery,
        resolution=resolve_skills(skills, SkillLayer(), SkillLayer()),
    )


async def test_packages_start_collapsed_and_expand_with_right():
    app = exact_app()
    async with app.run_test() as pilot:
        options = app.query_one("#skills", OptionList)
        assert options.option_count == 1
        assert "package-a" in str(options.get_option_at_index(0).prompt)

        await pilot.press("right")
        await pilot.pause()
        assert options.option_count == 3


async def test_search_matches_description_and_package():
    app = exact_app()
    async with app.run_test() as pilot:
        await pilot.press("/")
        search = app.query_one("#search", Input)
        assert search.display
        await pilot.press("d", "e", "s", "c", "r", "i", "p", "t", "i", "o", "n")
        await pilot.pause()

        options = app.query_one("#skills", OptionList)
        assert options.option_count == 3


async def test_mixed_package_space_enables_every_skill():
    app = exact_app()
    async with app.run_test() as pilot:
        await pilot.press("space")
        await pilot.pause()
        assert set(app.staged_enabled) == {
            Path("/skills/package-a/alpha/SKILL.md"),
            Path("/skills/package-a/beta/SKILL.md"),
        }


async def test_filtered_package_toggle_still_changes_hidden_members():
    app = exact_app()
    async with app.run_test() as pilot:
        await pilot.press("/")
        await pilot.press("a", "l", "p", "h", "a")
        await pilot.pause()
        app.query_one("#skills", OptionList).focus()
        await pilot.press("space")
        await pilot.pause()

        assert app.staged_enabled == {
            Path("/skills/package-a/alpha/SKILL.md"),
            Path("/skills/package-a/beta/SKILL.md"),
        }


async def test_review_shows_three_actions_and_launch_once_is_default():
    app = exact_app()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()

        assert app.query_one("#review-summary", Static).display
        assert app.query_one("#launch-once", Button).display
        assert app.query_one("#save-launch", Button).display
        assert app.query_one("#launch-normal", Button).display
        assert app.focused.id == "launch-once"

        await pilot.click("#launch-once")
        assert app.return_value is LaunchChoice.ONCE


async def test_enter_activates_focused_review_action():
    app = exact_app()
    async with app.run_test() as pilot:
        await pilot.press("enter", "enter")
        await pilot.pause()
        assert app.return_value is LaunchChoice.ONCE


@pytest.mark.parametrize(
    ("button_id", "choice"),
    [("save-launch", LaunchChoice.SAVE), ("launch-normal", LaunchChoice.NORMAL)],
)
async def test_review_returns_each_non_default_action(button_id: str, choice: LaunchChoice):
    app = exact_app()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.click(f"#{button_id}")
        assert app.return_value is choice


async def test_degraded_review_only_allows_normal_launch():
    inventory = (skill("alpha", "user", False),)
    app = SkillLabApp(
        project_root=Path("/project"),
        discovery=DiscoveryResult(
            inventory, errors=("app-server unavailable",), mode=DiscoveryMode.DEGRADED
        ),
        resolution=None,
    )
    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()

        assert not app.query_one("#launch-once", Button).display
        assert not app.query_one("#save-launch", Button).display
        assert app.query_one("#launch-normal", Button).display


async def test_q_requires_confirmation_after_staged_change():
    app = exact_app()
    async with app.run_test() as pilot:
        await pilot.press("space", "q")
        await pilot.pause()
        assert app.is_running
        assert app.query_one("#quit-warning", Static).display

        await pilot.press("q")
        await pilot.pause()
        assert not app.is_running
