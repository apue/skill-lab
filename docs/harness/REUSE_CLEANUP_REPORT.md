# Skill Lab 复用与清理报告

Status: complete

## Existing Capabilities

- 当前目录中的 `personal-codex-skills/scripts/install_symlinks.py` 只负责安装 symlink，不能表达项目级运行隔离；拒绝复用为核心状态模型。
- Codex CLI 已能通过启动配置过滤 skills；未来通过 adapter 复用。
- uv 已安装并支持 tool workflow；直接复用。
- 当前 workspace 没有可复用的 Python TUI 应用。

## Extension Points

- Codex runtime adapter：隔离所有 CLI/app-server 版本相关逻辑。
- Package backend adapter：只有经过 MVP 证据证明需要后再引入。

## Deprecated or Removable Logic

- 新仓库没有 legacy 或 deprecated logic。

## Search Evidence

- 检查了当前聚合目录的 Git 仓库和 `pyproject.toml` / `package.json`。
- 搜索了 Textual、Ink、OpenTUI、Typer、Click 等 TUI/CLI 依赖。
- 检查了本机 uv、Python、Node、pnpm、Bun、Deno 和 Rust runtime。

## Decision

- Reuse: uv、Textual、Codex runtime configuration。
- New code: selector UI、三层 resolver、运行记录。
- Defer: marketplace/package adapter、自动 eval。
- Deprecate/delete: 无。

## Risks

- Codex 配置接口可能变化，必须保持 adapter boundary。
- TUI 成功不等于 skill 实验有价值，仍需真实 A/B 使用验证。
