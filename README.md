# Skill Lab

Skill Lab 是面向 macOS 个人 Codex 用户的 TUI 实验启动器。它在新会话启动前展示已安装 skills，合并 global baseline、project defaults 和本次 run overlay，并让用户确认最终集合后再启动原生 Codex CLI。

MVP 的原则是：实验结果必须可解释、可复现；如果 discovery、配置、preflight 或记录失败，则明确降级为普通 Codex 启动，不会伪装成有效实验，也不会阻止用户继续使用 Codex。

## 功能

- 通过 Codex App Server `skills/list` 获取当前项目的实际 catalog 和 enabled baseline。
- 搜索 name、description 和 package；按 package 折叠、多选 skills。
- 解析 global、project、run 三层状态，并在 review 页面展示最终集合与依赖提示。
- `Launch once` 使用一次性 `skills.config` overrides。
- `Save defaults and launch` 将最小差量写入项目内 `.skilllab/config.toml`。
- `Launch Codex normally` 不携带 Skill Lab overrides。
- 在 `.skilllab/runs/` 写入不含 prompt、对话或凭据的运行证据。

Skill Lab 不提供 marketplace、skill 安装/升级/删除、自动评分或团队权限管理。

## 环境要求

- macOS
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- 已安装且可执行的 Codex CLI

## 运行

```bash
git clone https://github.com/apue/skill-lab.git
cd skill-lab
uv sync --dev
uv run skilllab
```

也可以从本地 checkout 安装：

```bash
uv tool install --editable .
skilllab
```

常用按键：

- `↑/↓` 导航，`Space` 切换 skill 或 package。
- `←/→` 折叠或展开 package，`/` 搜索。
- `Enter` 进入 review 或执行当前 review action。
- `Esc` 返回，`q` 退出；有未提交选择时需要再次确认。

## 配置与运行记录

Skill Lab 的全部运行时写入都在当前项目 root 内：

```text
.skilllab/
├── config.toml       # 用户明确保存的 project defaults
├── .gitignore        # 默认忽略 runs/
└── runs/
    └── <run-id>.json # experiment 或 passthrough evidence
```

`.skilllab/config.toml` 使用可移植 locator，不保存机器专用绝对路径。`runs/` 默认被项目内 ignore 文件排除，是否提交 config 由项目自行决定。

## Degraded 模式

当 App Server 不可用或响应不兼容时，Skill Lab 只从明确允许的项目 skill root 和 `$CODEX_HOME/skills` 读取 metadata，展示 degraded inventory。由于此时无法确定 global enabled baseline，`Launch once` 和保存配置会被禁用；用户仍可选择普通 Codex 启动。

同样地，配置错误、preflight 不一致或实验记录创建失败都不会产生“已验证实验”记录。除 Codex CLI 本身不可执行外，普通启动路径始终保留。

## 隐私与权限边界

- 不递归扫描整个 `$CODEX_HOME`。
- 不读取 Codex auth、session、history 或 log。
- discovery 不执行 skill 脚本、安装命令或下载内容。
- MVP 不修改用户级 Codex 配置、skills 或第三方仓库。
- Skill Lab 不添加 sandbox/approval 绕过参数；新会话继承用户现有 Codex 权限策略。
- 符号链接目标只用于只读 metadata discovery；所有项目写入经过 realpath containment guard。

## 开发与验证

```bash
uv lock --check
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run skilllab --version
uv run skilllab --smoke-test
```

macOS 发布前可在完全隔离的临时 HOME/CODEX_HOME 中运行真实 Codex 门禁：

```bash
SKILLLAB_REAL_CODEX_E2E=1 uv run pytest -m real_codex_e2e
```

## 文档

- [产品规格](docs/harness/SPEC.md)
- [架构](docs/harness/ARCHITECTURE.md)
- [验收标准](docs/harness/ACCEPTANCE.md)
- [决策记录](docs/harness/DECISIONS.md)
- [验证计划](docs/harness/VALIDATION_PLAN.md)
- [MVP 设计](docs/superpowers/specs/2026-07-12-skill-lab-mvp-design.md)
- [MVP 实施计划](docs/superpowers/plans/2026-07-12-skill-lab-mvp.md)

## License

[MIT](LICENSE)
