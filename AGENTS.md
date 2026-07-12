# Skill Lab Agent Guide

本文件适用于整个仓库。使用 Codex 或其他 coding agent 开发 Skill Lab 时，先阅读本文件以及与任务相关的 `docs/harness/` 文档。

## 项目目标

Skill Lab 是面向个人 Codex 用户的 TUI 实验启动器。当前目标是让用户在新 Codex 会话启动前，以可见、可解释、可复现的方式选择有效 skill 集合。

优先解决：

- 已安装 skill discovery。
- global baseline、project defaults 和 run overlay 三层解析。
- TUI 搜索、多选、package 折叠和 review。
- 新 Codex 会话启动和运行证据记录。

当前不做：

- 自建 marketplace、registry 或通用 package manager。
- skill install/update/remove。
- 自动质量评分、release watcher、团队权限或跨 agent 管理。

不要因为某个未来功能“可能有用”而扩大当前任务范围。新增范围必须先更新 `docs/harness/SPEC.md`、`ACCEPTANCE.md` 和 `DECISIONS.md`。

## 技术栈

- Python 3.12+
- uv
- Textual
- pytest + pytest-asyncio
- Ruff

常用命令：

```bash
uv sync --dev
uv run skilllab
uv run skilllab --smoke-test
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## 开发流程

1. 行为变更先写失败测试并确认失败原因正确。
2. 写最小实现使测试通过。
3. 运行完整测试、Ruff 和 smoke-test。
4. 行为、架构或安全边界变化时同步更新对应文档。
5. 不把未决定的未来功能写进执行规格；放入 backlog 或 Issue。

测试应验证结果和契约，不绑定无关的内部执行路径。TUI 行为优先使用 Textual pilot 测试；子进程和路径策略使用确定性单元测试。

## 模块边界

- `app.py`：TUI 组合和用户交互，不直接扫描文件或启动 Codex。
- `discovery.py`：只读发现和 metadata 解析，不决定启用策略。
- `resolution.py`：纯函数合并配置层，不进行 I/O。
- `config.py`：Skill Lab 自身配置的受控读写。
- `codex.py`：Codex 版本适配和子进程启动。
- `records.py`：实验运行记录。
- `cli.py`：入口、参数和依赖装配。

新增代码应保持这些边界；不要从 TUI event handler 直接写任意文件或拼接 shell command。

## 文件访问与安全边界

Skill Lab 自身的权限与它启动的 Codex 子进程权限必须分开处理。

### 允许读取

- 当前目标项目中完成配置解析所需的文件。
- Codex `skills/list` 返回的数据。
- 明确配置的 skill roots，例如 `~/.codex/skills`。
- skill discovery 所需的 `SKILL.md` frontmatter 和必要 metadata。
- skill symlink 的目标，但仅用于只读 metadata discovery。

### 禁止读取或扫描

- 不递归扫描整个 `~/.codex`。
- 不读取 `~/.codex/auth.json`、session、log、history 或其他凭据/对话数据。
- 不在 discovery 阶段执行 skill 附带脚本、安装命令或动态下载内容。

### 写入规则

- 开发本仓库时，只修改本仓库内与当前任务相关的文件。
- 运行时只有用户明确选择 `Save as project defaults` 后，才可写目标项目配置。
- 所有目标项目写入必须在解析符号链接后的 project root 内，并采用集中、可测试的 path guard。
- MVP 不直接修改 `~/.codex/skills`、`~/.codex/config.toml` 或第三方 skill 源仓库。
- MVP 不写入任意外部路径；未来用户级 Skill Lab 状态目录必须单独设计并获得明确批准。

Codex 子进程必须继承用户现有 sandbox/approval 策略。不得默认添加绕过审批、扩大文件系统权限或降低 sandbox 的参数。

## 文档职责

- `docs/harness/SPEC.md`：已决定、可实现的产品行为。
- `docs/harness/ARCHITECTURE.md`：模块边界和数据流。
- `docs/harness/ACCEPTANCE.md`：完成标准。
- `docs/harness/DECISIONS.md`：重要选择及简短理由。
- `docs/harness/VALIDATION_PLAN.md`：验证模式和命令。
- `docs/superpowers/specs/`：已批准设计。
- `docs/superpowers/plans/`：可执行实施计划。

不要在规格中混入未决定的 proposal，也不要让 decision log 重复整份规格。

## Git 与公开安全

- 保留用户已有改动，不重置或覆盖无关文件。
- 提交前检查 diff、测试和格式。
- 推送公开仓库前检查 token、私钥、认证文件和机器专用绝对路径。
- 默认使用 feature branch 和 Draft PR；未经用户明确要求不合并。
