# 参与开发

Skill Lab 当前处于个人实验阶段，欢迎通过 Issue 或 Pull Request 提供反馈。请优先帮助验证核心问题：skill-set 隔离是否真的改善了 skill 采用判断。

## 本地环境

```bash
git clone https://github.com/apue/skill-lab.git
cd skill-lab
uv sync --dev
```

## 开发流程

1. 从 `main` 创建范围明确的 feature branch。
2. 行为变更先写失败测试，再写最小实现。
3. 更新与行为对应的中文文档。
4. 运行完整验证。

```bash
uv lock --check
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run skilllab --smoke-test
```

## 范围控制

初始 MVP 不接受以下方向的实现，除非已有真实使用证据并先更新设计：

- 自建 marketplace 或 registry。
- 跨 agent 管理平台。
- 自动 release watcher。
- 没有人工校准的单一 skill 质量分数。
- 与 skill 实验无关的通用 package manager 功能。

## Pull Request

PR 描述应包括：

- 要解决的用户问题。
- 为什么属于当前 MVP。
- 测试和人工验证证据。
- 是否改变配置、运行记录或 Codex adapter contract。
- 尚未解决的风险。

项目文档目前使用中文；代码标识、类型名和 commit message 使用英文。
