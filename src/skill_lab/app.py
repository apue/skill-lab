"""Textual application for Skill Lab."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.widgets import Footer, Header, Static


class SkillLabApp(App[None]):
    """Minimal application shell used to validate the project scaffold."""

    TITLE = "Skill Lab"
    SUB_TITLE = "Reproducible Codex skill experiments"
    BINDINGS = [("q", "quit", "退出")]

    CSS = """
    #panel {
        width: 72;
        height: auto;
        border: round $primary;
        padding: 1 2;
    }

    #title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #status {
        margin-top: 1;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the scaffold status screen."""
        yield Header()
        with Middle(), Center(), Vertical(id="panel"):
            yield Static("Skill Lab", id="title")
            yield Static(f"当前目录：{Path.cwd()}", id="project")
            yield Static("脚手架已就绪；skill selector 将在下一阶段实现。", id="status")
        yield Footer()
