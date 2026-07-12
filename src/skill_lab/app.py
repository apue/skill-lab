"""Textual selector and review UI for Skill Lab."""

from collections import defaultdict
from contextlib import suppress
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, OptionList, Static
from textual.widgets.option_list import Option

from skill_lab.models import (
    DiscoveryMode,
    DiscoveryResult,
    LaunchChoice,
    ResolutionResult,
    ResolutionSource,
)


class SkillLabApp(App[LaunchChoice | None]):
    """Stage skill intent and return one explicit launch action."""

    TITLE = "Skill Lab"
    SUB_TITLE = "Reproducible Codex skill experiments"
    BINDINGS = [
        Binding("q", "request_quit", "退出", priority=True),
        Binding("/", "search", "搜索", priority=True),
        Binding("space", "toggle", "切换", priority=True),
        Binding("right", "expand", "展开", priority=True),
        Binding("left", "collapse", "折叠", priority=True),
        Binding("enter", "review", "Review", priority=True),
        Binding("escape", "back", "返回", priority=True),
    ]

    CSS = """
    #root { padding: 1 2; }
    #project { color: $text-muted; margin-bottom: 1; }
    #search { margin-bottom: 1; }
    #skills { height: 1fr; border: round $primary; }
    #review { display: none; border: round $primary; padding: 1 2; }
    #review-summary { height: 1fr; }
    #actions { height: auto; align: center middle; }
    #actions Button { margin: 0 1; }
    #quit-warning { display: none; color: $warning; }
    """

    def __init__(
        self,
        *,
        project_root: Path | None = None,
        discovery: DiscoveryResult | None = None,
        resolution: ResolutionResult | None = None,
    ) -> None:
        super().__init__()
        self.project_root = project_root or Path.cwd()
        self.discovery = discovery or DiscoveryResult((), mode=DiscoveryMode.DEGRADED)
        self.resolution = resolution
        self.expanded: set[str] = set()
        self.search_query = ""
        self._confirm_quit = False
        self._initial_enabled = (
            {item.skill.runtime_path for item in resolution.run if item.enabled}
            if resolution
            else set()
        )
        self.staged_enabled = set(self._initial_enabled)

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="root"):
            yield Static(f"项目：{self.project_root}", id="project")
            yield Input(placeholder="搜索 name、description、package", id="search")
            yield Static("再次按 q 丢弃 staged changes", id="quit-warning")
            yield OptionList(id="skills")
            with Vertical(id="review"):
                yield Static(id="review-summary")
                with Horizontal(id="actions"):
                    yield Button("Launch once", id="launch-once", variant="primary")
                    yield Button("Save defaults and launch", id="save-launch")
                    yield Button("Launch Codex normally", id="launch-normal")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#search", Input).display = False
        self._refresh_options()
        self.query_one("#skills", OptionList).focus()

    def _packages(self) -> dict[str, list]:
        packages: dict[str, list] = defaultdict(list)
        for item in self.discovery.skills:
            packages[item.package].append(item)
        for values in packages.values():
            values.sort(key=lambda item: item.name.casefold())
        return dict(sorted(packages.items(), key=lambda pair: pair[0].casefold()))

    def _matching(self, item) -> bool:
        query = self.search_query.casefold()
        return (
            not query or query in " ".join((item.name, item.description, item.package)).casefold()
        )

    def _package_marker(self, items: list) -> str:
        states = {item.runtime_path in self.staged_enabled for item in items}
        return "[x]" if states == {True} else "[ ]" if states == {False} else "[-]"

    def _refresh_options(self) -> None:
        widget = self.query_one("#skills", OptionList)
        highlighted_id = widget.highlighted_option.id if widget.highlighted_option else None
        widget.clear_options()
        for package, items in self._packages().items():
            matching = [item for item in items if self._matching(item)]
            if not matching:
                continue
            arrow = "▼" if package in self.expanded or self.search_query else "▶"
            widget.add_option(
                Option(
                    f"{arrow} {self._package_marker(items)} {package} ({len(items)})",
                    id=f"package|{package}",
                )
            )
            if package in self.expanded or self.search_query:
                for item in matching:
                    marker = "[x]" if item.runtime_path in self.staged_enabled else "[ ]"
                    warning = " ⚠" if item.dependencies else ""
                    widget.add_option(
                        Option(
                            f"  {marker} {item.name} — {item.description}{warning}",
                            id=f"skill|{item.runtime_path}",
                        )
                    )
        if highlighted_id:
            with suppress(KeyError):
                widget.highlighted = widget.get_option_index(highlighted_id)
        if widget.option_count and widget.highlighted is None:
            widget.highlighted = 0

    def _selected_id(self) -> str | None:
        option = self.query_one("#skills", OptionList).highlighted_option
        return option.id if option else None

    def action_search(self) -> None:
        search = self.query_one("#search", Input)
        search.display = True
        search.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search":
            self.search_query = event.value
            self._refresh_options()

    def action_expand(self) -> None:
        selected = self._selected_id()
        if selected and selected.startswith("package|"):
            self.expanded.add(selected.split("|", 1)[1])
            self._refresh_options()

    def action_collapse(self) -> None:
        selected = self._selected_id()
        if selected and selected.startswith("package|"):
            self.expanded.discard(selected.split("|", 1)[1])
            self._refresh_options()

    def action_toggle(self) -> None:
        if self.resolution is None:
            return
        selected = self._selected_id()
        if not selected:
            return
        if selected.startswith("package|"):
            package = selected.split("|", 1)[1]
            items = self._packages()[package]
            enable = not all(item.runtime_path in self.staged_enabled for item in items)
            for item in items:
                if enable:
                    self.staged_enabled.add(item.runtime_path)
                else:
                    self.staged_enabled.discard(item.runtime_path)
        elif selected.startswith("skill|"):
            path = Path(selected.split("|", 1)[1])
            if path in self.staged_enabled:
                self.staged_enabled.remove(path)
            else:
                self.staged_enabled.add(path)
        self._confirm_quit = False
        self.query_one("#quit-warning", Static).display = False
        self._refresh_options()

    def _review_text(self) -> str:
        if self.resolution is None:
            errors = "\n".join(f"- {error}" for error in self.discovery.errors)
            return f"Degraded inventory\n\n{errors}\n\nEffective skills are unknown."
        project = self.resolution.project_delta
        run_changes = self.staged_enabled ^ self._initial_enabled
        project_by_path = {item.skill.runtime_path: item for item in self.resolution.project}
        enabled = []
        for item in self.discovery.skills:
            if item.runtime_path not in self.staged_enabled:
                continue
            project_item = project_by_path[item.runtime_path]
            source = (
                project_item.source.value if project_item.enabled else ResolutionSource.RUN.value
            )
            enabled.append(f"{item.name} [{source}]")
        warnings = sorted(
            {
                warning
                for item in self.discovery.skills
                if item.runtime_path in self.staged_enabled
                for warning in item.dependencies
            }
        )
        return (
            f"Project vs global: +{len(project.include)} / -{len(project.exclude)}\n"
            f"Run vs project: {len(run_changes)} changes\n\n"
            f"Final enabled ({len(enabled)}): {', '.join(enabled) or '(none)'}\n"
            f"Dependency warnings: {', '.join(warnings) or '(none)'}"
        )

    def action_review(self) -> None:
        review = self.query_one("#review", Vertical)
        if review.display and isinstance(self.focused, Button):
            self._choose_button(self.focused)
            return
        self.query_one("#skills", OptionList).display = False
        self.query_one("#search", Input).display = False
        review.display = True
        self.query_one("#review-summary", Static).update(self._review_text())
        exact = self.resolution is not None
        self.query_one("#launch-once", Button).display = exact
        self.query_one("#save-launch", Button).display = exact
        target = self.query_one("#launch-once" if exact else "#launch-normal", Button)
        target.focus()

    def action_back(self) -> None:
        review = self.query_one("#review", Vertical)
        if review.display:
            review.display = False
            self.query_one("#skills", OptionList).display = True
            self.query_one("#skills", OptionList).focus()

    def action_request_quit(self) -> None:
        if self.staged_enabled != self._initial_enabled and not self._confirm_quit:
            self._confirm_quit = True
            self.query_one("#quit-warning", Static).display = True
            return
        self.exit(None)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self._choose_button(event.button)

    def _choose_button(self, button: Button) -> None:
        choices = {
            "launch-once": LaunchChoice.ONCE,
            "save-launch": LaunchChoice.SAVE,
            "launch-normal": LaunchChoice.NORMAL,
        }
        choice = choices.get(button.id or "")
        if choice is not None:
            self.exit(choice)
