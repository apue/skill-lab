# Skill Lab 产品规格

Status: review

## 目标

Skill Lab 是一个面向个人 Codex 用户的 TUI 实验启动器。它帮助用户在启动新 Codex 会话前，看清并选择本次运行可见的 skills，从而以可复现的方式比较“有 skill”和“无 skill”的实际效果。

## 核心问题

当前 skill 生态的主要困难不是安装，而是缺少可靠的采用证据：

- 全局 skills 会在不同项目之间产生上下文污染。
- 在同一对话中口头要求“不要使用某 skill”不能构成干净隔离。
- 手输 skill 名称容易出错，且用户很难确认最终有效集合。
- skill 的价值依赖任务、项目、模型和版本，不能只用全局启用状态表达。

## 用户与使用场景

- 用户：在本机使用 Codex 开发多个个人项目的开发者。
- 场景一：从全局 baseline 中为当前项目排除一个有干扰的通用 skill。
- 场景二：临时启用一个新 skill，启动干净会话进行体验。
- 场景三：确认选择后，将其保存为当前项目默认设置。
- 场景四：记录运行时的有效 skill 集合，为后续人工比较保留证据。

## MVP 要求

### TUI 选择器

- `skilllab` 在当前目录启动全屏 TUI。
- TUI 列出已发现的 skills，并显示有效启用状态与状态来源。
- 用户使用方向键导航、Space 切换待启动状态、`/` 搜索、Enter 进入确认页、`q` 退出。
- package 可以折叠，并允许整体或逐项切换。
- 确认页展示相对项目默认值的变更和最终有效 skill 集合。

### 启动语义

- `Launch once` 只影响本次新启动的 Codex 会话。
- `Save as project defaults and launch` 保存项目覆盖后再启动 Codex。
- 每次启动必须创建新 Codex 会话，不能依赖当前对话中的口头开关。
- 启动器必须使用精确的 Codex skill 配置，而不是移动原始 skill 目录。

### 配置层级

优先级从低到高：

1. 用户 global baseline。
2. 项目默认 include/exclude。
3. 本次运行临时覆盖。

冲突的同层设置必须报错，不静默猜测。

### 证据记录

每次由 Skill Lab 启动 Codex 时，记录：

- 时间与工作目录。
- 模型标识（可获得时）。
- 有效 skills 及其路径或版本指纹。
- 项目 Git commit（可获得时）。
- 本次是临时运行还是保存后的项目默认运行。

### 文件访问与子进程权限

- discovery 优先使用 Codex `skills/list`；文件系统 fallback 只读取明确配置的 skill roots。
- 不递归扫描整个 `~/.codex`，不读取 auth、session、log 或 history 数据。
- discovery 只读取 `SKILL.md` frontmatter 和必要 metadata，不执行第三方 skill 脚本。
- 只有用户明确选择 `Save as project defaults` 后，才能写入目标项目配置。
- MVP 不修改 `~/.codex/skills`、`~/.codex/config.toml` 或第三方 skill 源目录。
- Skill Lab 不降低其启动的 Codex 子进程现有 sandbox/approval 策略。

## 本次脚手架交付

- Python 3.12+、uv、Textual、pytest、Ruff 项目配置。
- 可通过 `uv run skilllab` 启动的最小 TUI。
- TUI 显示产品名称、当前工作目录、脚手架状态和退出提示。
- 单元测试、CLI smoke test 和中文主要文档。
- 不实现真实 skill 扫描、选择持久化或 Codex 启动。

## 非目标

- 自建 marketplace 或 registry。
- 安装、更新、删除 skills。
- 自动评价 skill 质量。
- X/社交平台作者关注和 release notes 监控。
- 团队配置同步、审批和权限管理。
- 跨 Claude、Cursor 等其他 agent 的统一管理。
- 在本次脚手架中实现完整 MVP 行为。
- 自定义 OS sandbox、RBAC 或通用 permission prompt framework。

## 约束

- 个人优先，不为未验证的团队需求增加复杂度。
- 正常使用以 TUI 为主，不要求用户手输 skill 名称列表。
- Marketplace/package 操作未来优先复用现有生态，不在本项目重造。
- 先验证隔离与人工比较是否有价值，再扩展生命周期管理。

## 开放问题

- [ ] 公开仓库采用何种开源许可证。
- [ ] MVP 通过 Codex app-server 还是 CLI `-c skills.config=...` 实现启动适配。

## 验收链接

见 `ACCEPTANCE.md`。
