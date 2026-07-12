# Skill Lab 验证计划

Status: accepted

## Validation Mode

Selected modes: strict-tdd + contract-test + schema-check + Textual pilot + smoke-test + real-codex-e2e + manual-acceptance

Reason: Resolver、parser、path guard 和状态机需要严格 TDD；App Server/CLI 需要协议契约测试；TOML/JSON 需要 schema check；TUI 使用 pilot；发布前在 macOS 验证真实 Codex binary。

## Commands

```bash
uv lock --check
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run skilllab --version
uv run skilllab --smoke-test
uv run pytest -m real_codex_e2e
if git grep -nE 'gho_[A-Za-z0-9]+|api[_-]?key|BEGIN .*PRIVATE KEY|/Users/' -- ':!.git/*' ':!docs/superpowers/plans/*' ':!docs/harness/VALIDATION_PLAN.md'; then
  exit 1
fi
```

## Pass Criteria

- 常规测试不依赖真实用户 Codex state。
- real-codex-e2e 仅在发布 gate 显式启用并使用隔离 fixtures。
- 所有命令退出码为 0。
- 没有 token、私钥或提交范围内的机器专用绝对路径。

## Manual Checks

- [ ] 用 2–3 个真实 skills 比较有/无结果。
- [ ] 三层来源和 degraded 提示可理解。
- [ ] Normal launch 不携带 Skill Lab overrides。
- [ ] Codex 子进程保留用户现有 sandbox/approval。
