# Skill Lab 复用索引

Status: accepted

## 可复用能力

- Codex CLI：运行时和新会话启动，不在 Skill Lab 内复制 agent 实现。
- Codex `skills.config` / App Server：当前 discovery、preflight 和一次性 enable/disable 边界。
- Vercel `skills` CLI：未来 marketplace/package 操作候选，不纳入 MVP。
- Textual：TUI 生命周期、布局、键盘输入和测试 pilot。
- uv：Python runtime、依赖锁定和 tool installation。

## 扩展点

- `codex.py`：对 Codex 版本差异提供单一 adapter boundary。
- `discovery.py`：允许未来增加 registry 或其他 agent source，但不进入 resolver。
- `records.py`：允许未来加入人工评分和重复 A/B 结果。

## 避免平行实现

- 不自建 marketplace；优先适配现有 CLI。
- 不移动第三方 skill 原始目录；使用 Codex 配置表达运行时策略。
- 不自建 TUI event loop；使用 Textual。

<!-- generated-reuse-index:start -->
## Generated Reuse Candidates

- No filename-based candidates found.
<!-- generated-reuse-index:end -->
