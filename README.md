# Skill Lab

Skill Lab 是一个面向个人 Codex 用户的 TUI 实验启动器。它的目标不是收集更多 skills，而是帮助你在启动新 Codex 会话前，精确看见并选择本次运行可用的 skill 集合，从而更可靠地判断某个 skill 是否真的改善了实际任务。

> 当前状态：项目脚手架。TUI、测试和工程配置已经可运行；skill discovery、选择器和 Codex launcher 尚未实现。

## 为什么需要 Skill Lab

- 全局 skills 可能在不同技术栈项目之间相互干扰。
- 在同一对话里口头要求“不要使用某 skill”不能形成干净隔离。
- `--with/--without` 手输 skill 名称容易出错，也难以确认最终集合。
- skill 的价值依赖项目、任务、模型和版本，应该通过可复现体验判断。

Skill Lab 的第一阶段只解决：

```text
选择本次 skill set
        ↓
确认最终有效集合
        ↓
启动干净 Codex 会话
        ↓
记录环境与人工判断
```

## 计划中的交互

```text
Skill Lab
Project: ~/Developer/my-ios-app

 Global baseline
   [✓] code-exploration                 global
   [✓] verification-before-completion   global

 Superpowers                                      1/3
 ▾ [◐] github:obra/superpowers
      [ ] brainstorming                  project excluded
      [✓] systematic-debugging           inherited
      [ ] writing-plans                  run override

 Installed, inactive
   [ ] ios-design                        available

──────────────────────────────────────────────────────
 ↑/↓ navigate   Space toggle   / search
 Enter review   r reset        q quit
```

Space 只修改待启动选择。确认页再决定：

- `Launch once`：只影响本次新会话。
- `Save as project defaults and launch`：保存当前项目覆盖后启动。

## 当前可运行内容

### 环境要求

- [uv](https://docs.astral.sh/uv/)
- macOS、Linux 或 Windows 终端

uv 会根据 `.python-version` 安装并使用 Python 3.12，不要求修改系统 Python。

### 开发运行

```bash
git clone https://github.com/apue/skill-lab.git
cd skill-lab
uv sync --dev
uv run skilllab
```

按 `q` 退出当前脚手架界面。

### 安装为本机工具

在本地 checkout 中执行：

```bash
uv tool install --editable .
skilllab
```

### 非交互诊断

```bash
uv run skilllab --version
uv run skilllab --smoke-test
```

## 开发检查

```bash
uv lock --check
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## MVP 边界

MVP 将实现：

1. 已安装 skill discovery。
2. global baseline、project defaults 和 run overlay 三层解析。
3. TUI 搜索、多选、package 折叠和 review 页面。
4. 新 Codex 会话启动。
5. 运行环境证据记录。

明确延后：

- Marketplace、install/update/remove。
- 自动 skill 评分和 LLM judge。
- release notes 和作者动态监控。
- 团队配置和跨 agent 支持。

## 文档

- [产品规格](docs/harness/SPEC.md)
- [架构](docs/harness/ARCHITECTURE.md)
- [验收标准](docs/harness/ACCEPTANCE.md)
- [决策记录](docs/harness/DECISIONS.md)
- [验证计划](docs/harness/VALIDATION_PLAN.md)
- [设计说明](docs/superpowers/specs/2026-07-12-skill-lab-design.md)
- [初始脚手架实施计划](docs/superpowers/plans/2026-07-12-initial-scaffold.md)

## 项目原则

- 先证明 skill 隔离和比较有价值，再扩展管理功能。
- TUI 是默认交互，不要求用户记忆 skill 标识。
- 下载、项目可见性和本次运行启用是三个不同状态。
- 结果评价优先保留人的判断，不急于用单一自动分数替代。
- 第三方 skill 视为不可信的指令和代码，使用前需要审查。

## License

当前尚未选择开源许可证。仓库公开可见不代表已授予复制、修改或再分发权利；许可证将在项目方向 review 后决定。
