# Skill Lab 代码地图

Status: accepted

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

- `tests/test_resolution.py`、`test_config.py`：三层纯解析、locator、schema 和 path guard。
- `tests/test_discovery.py`、`test_codex.py`：catalog normalization、fallback 和 Codex contract。
- `tests/test_records.py`、`test_cli.py`：运行证据与完整编排。
- `tests/test_app.py`：Textual pilot 交互。
- `tests/test_real_codex_e2e.py`：隔离的 macOS release gate。

## 核心模块

- `models.py`：跨层不可变领域对象。
- `discovery.py`：App Server catalog normalization 与 allowlisted fallback。
- `resolution.py`：global/project/run 纯函数解析和最小 delta。
- `config.py`：项目 TOML persistence 与集中 path guard。
- `codex.py`：App Server JSONL adapter、preflight 和原生 CLI 启动。
- `records.py`：项目内 experiment/passthrough evidence。
- `app.py`：只负责 Textual 选择和 review。
- `cli.py`：依赖装配、降级和启动编排。

<!-- generated-codebase-map:start -->
## Generated Codebase Summary

- File count: 43

### Top Directories
- `docs`: 15 files
- `.`: 10 files
- `src`: 9 files
- `tests`: 8 files
- `.github`: 1 files

### File Types
- `.md`: 18
- `.py`: 17
- `<none>`: 4
- `.lock`: 1
- `.toml`: 1
- `.json`: 1
- `.yml`: 1
<!-- generated-codebase-map:end -->
