# Skill Lab 代码地图

Status: review

## 当前结构

- `src/skill_lab/`：Python 包和 CLI/TUI 入口。
- `tests/`：确定性单元测试和 Textual pilot 测试。
- `docs/harness/`：规格、架构、验收、决策和验证证据。
- `docs/superpowers/`：已批准设计与实施计划。
- `.agent-improvement-loop/`：未来反馈、eval 和修复记录模板。

## 入口

- `src/skill_lab/cli.py:main`：`skilllab` console script。
- `src/skill_lab/app.py:SkillLabApp`：Textual 应用。

## 测试

- `tests/test_cli.py`：版本和非交互 smoke-test。
- `tests/test_app.py`：TUI 构造、渲染和退出。

## 计划模块

- `discovery.py`：skill discovery。
- `resolution.py`：配置优先级和有效集合。
- `config.py`：TOML persistence。
- `codex.py`：Codex adapter。
- `records.py`：实验运行记录。
