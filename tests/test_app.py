from textual.widgets import Static

from skill_lab.app import SkillLabApp


async def test_app_renders_scaffold_status():
    app = SkillLabApp()
    async with app.run_test():
        assert app.query_one("#title", Static)
        assert app.query_one("#project", Static)
        assert app.query_one("#status", Static)


async def test_q_quits_app():
    app = SkillLabApp()
    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()
        assert not app.is_running
