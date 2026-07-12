# Skill Lab Initial Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立一个可安装、可测试、可启动的 Python/uv/Textual Skill Lab 骨架，并提供完整中文 review 文档。

**Architecture:** console script `skilllab` 由 `cli.py` 解析无交互的版本/smoke-test 模式，默认启动 `SkillLabApp`。Textual 应用只验证本次脚手架的生命周期；真实 discovery、resolver 和 Codex adapter 按架构文档延后。

**Tech Stack:** Python 3.12+、uv、Textual、pytest、pytest-asyncio、Ruff、GitHub Actions。

## Global Constraints

- 本次不实现真实 skill discovery、配置持久化或 Codex 启动。
- 默认用户入口必须是 TUI，不要求输入 `--with/--without` skill 列表。
- 所有确定性 Python 行为先写失败测试，再写实现。
- 公开提交不得包含 token、认证文件或机器专用绝对路径。
- 文档先使用中文；代码标识和提交信息使用英文。

---

### Task 1: Python package and CLI contract

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `src/skill_lab/__init__.py`
- Create: `tests/test_cli.py`
- Create: `src/skill_lab/cli.py`

**Interfaces:**
- Produces: `skill_lab.__version__: str`
- Produces: `skill_lab.cli.run(argv: Sequence[str] | None = None) -> int`
- Produces: `skill_lab.cli.main() -> NoReturn`

- [x] **Step 1: Write package configuration and failing CLI tests**

Create `pyproject.toml` with the `skilllab` console script, Textual runtime dependency, pytest/pytest-asyncio/Ruff dev dependencies, and Ruff/pytest configuration. Create tests that require `--version` and `--smoke-test` to return zero without opening an interactive terminal.

```python
from skill_lab import __version__
from skill_lab.cli import run


def test_version_flag(capsys):
    assert run(["--version"]) == 0
    assert capsys.readouterr().out.strip() == f"skilllab {__version__}"


def test_smoke_test(capsys):
    assert run(["--smoke-test"]) == 0
    assert capsys.readouterr().out.strip() == "Skill Lab app constructed successfully"
```

- [x] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/test_cli.py -v`

Expected: FAIL because `skill_lab.cli` does not exist.

- [x] **Step 3: Implement the minimal CLI**

```python
import argparse
from collections.abc import Sequence
from typing import NoReturn

from skill_lab import __version__
from skill_lab.app import SkillLabApp


def run(argv: Sequence[str] | None = None) -> int:
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

    SkillLabApp().run()
    return 0


def main() -> NoReturn:
    raise SystemExit(run())
```

- [x] **Step 4: Run focused tests and verify GREEN**

Run: `uv run pytest tests/test_cli.py -v`

Expected: 2 passed.

- [x] **Step 5: Commit**

```bash
git add pyproject.toml .python-version .gitignore src/skill_lab tests/test_cli.py uv.lock
git commit -m "feat: add skilllab package and CLI"
```

### Task 2: Minimal Textual application

**Files:**
- Create: `tests/test_app.py`
- Create: `src/skill_lab/app.py`

**Interfaces:**
- Produces: `skill_lab.app.SkillLabApp(App[None])`
- Produces widget IDs: `#title`, `#project`, `#status`
- Keyboard contract: `q` invokes application quit.

- [x] **Step 1: Write failing Textual pilot tests**

```python
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
```

- [x] **Step 2: Run the tests and verify RED**

Run: `uv run pytest tests/test_app.py -v`

Expected: FAIL because `SkillLabApp` is missing or does not expose the widget contract.

- [x] **Step 3: Implement the minimal Textual app**

```python
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Center, Middle
from textual.widgets import Footer, Header, Static


class SkillLabApp(App[None]):
    TITLE = "Skill Lab"
    SUB_TITLE = "Reproducible Codex skill experiments"
    BINDINGS = [("q", "quit", "退出")]

    CSS = """
    #panel { width: 72; height: auto; border: round $primary; padding: 1 2; }
    #title { text-style: bold; color: $accent; margin-bottom: 1; }
    #status { margin-top: 1; color: $text-muted; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Middle(), Center():
            with Static(id="panel"):
                yield Static("Skill Lab", id="title")
                yield Static(f"当前目录：{Path.cwd()}", id="project")
                yield Static("脚手架已就绪；skill selector 将在下一阶段实现。", id="status")
        yield Footer()
```

- [x] **Step 4: Run focused and full tests**

Run: `uv run pytest tests/test_app.py -v && uv run pytest`

Expected: all tests pass.

- [x] **Step 5: Commit**

```bash
git add src/skill_lab/app.py tests/test_app.py
git commit -m "feat: add Textual scaffold app"
```

### Task 3: Documentation, CI, and public readiness

**Files:**
- Create: `README.md`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `.github/workflows/ci.yml`
- Modify: `docs/harness/CODEBASE_MAP.md`

**Interfaces:**
- CI contract: Python 3.12 and 3.13 run locked tests and Ruff checks.
- Documentation contract: install, run, test, scope, roadmap and review links are copyable.

- [x] **Step 1: Add user and contributor documentation**

README must include project status, problem statement, non-goals, TUI sketch, uv install/development commands, document index and roadmap. CONTRIBUTING must describe branch, test and documentation expectations. SECURITY must warn that third-party skills are untrusted instructions/code and provide private reporting guidance without inventing an email address.

- [x] **Step 2: Add CI workflow**

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@08807647e7069bb48b6ef5acd8ec9567f424441b # v8.1.0
        with:
          python-version: ${{ matrix.python-version }}
          enable-cache: true
      - run: uv sync --frozen --dev
      - run: uv run pytest
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run skilllab --smoke-test
```

- [x] **Step 3: Run complete validation**

Run:

```bash
uv lock --check
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run skilllab --version
uv run skilllab --smoke-test
```

Expected: every command exits zero with no warnings.

- [x] **Step 4: Audit public content**

Run:

```bash
TOKEN_PREFIX='g''ho_'
HOME_PREFIX='/''Users/'
API_PATTERN='api[_-]?''key'
PRIVATE_PATTERN='BEGIN .*PRIVATE ''KEY'
git grep -nE "${TOKEN_PREFIX}[A-Za-z0-9]+|${API_PATTERN}|${PRIVATE_PATTERN}|${HOME_PREFIX}" -- ':!.git/*'
git status --short
```

Expected: the grep command returns no matches; status contains only intended files.

- [x] **Step 5: Commit**

```bash
git add README.md CONTRIBUTING.md SECURITY.md .github docs .agent-improvement-loop
git commit -m "docs: add project design and contributor guidance"
```

## Plan Self-Review

- Spec coverage: scaffold packaging, TUI lifecycle, tests, docs, CI and public audit are covered.
- Deferred features: discovery, resolver and Codex launcher remain explicitly outside this plan.
- Type consistency: `SkillLabApp`, `run`, `main` and widget IDs are consistent across tasks.
- Placeholder scan: no implementation placeholder is required to execute this plan; product roadmap items are intentional non-goals.

## Execution Notes

- 2026-07-12：Task 1 的 smoke-test 依赖 `SkillLabApp`，因此先补 Task 2 的失败测试，再将 CLI 与最小 Textual app 合并到同一个 RED-GREEN cycle。四个测试均先因缺少模块失败，再在最小实现后通过。
- 2026-07-12：真实 PTY 启动显示标题、当前目录、脚手架状态和 `q` 退出提示；发送 `q` 后进程以零退出码结束。
