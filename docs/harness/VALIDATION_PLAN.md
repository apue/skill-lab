# Skill Lab 验证计划

Status: review

## Validation Mode

Modes: strict-tdd + smoke-test + manual-acceptance + review-only

Reason:

- Python 入口和 TUI 生命周期属于确定性行为，采用严格 TDD。
- 实际终端启动采用 smoke test。
- TUI 文案与产品边界需要用户人工 review。
- 规格和架构文档采用一致性审查。

## Commands

```bash
uv lock --check
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run skilllab --version
uv run skilllab --smoke-test
TOKEN_PREFIX='g''ho_'
HOME_PREFIX='/''Users/'
API_PATTERN='api[_-]?''key'
PRIVATE_PATTERN='BEGIN .*PRIVATE ''KEY'
git grep -nE "${TOKEN_PREFIX}[A-Za-z0-9]+|${API_PATTERN}|${PRIVATE_PATTERN}|${HOME_PREFIX}" -- ':!.git/*'
```

## Pass Criteria

- 所有命令退出码为 0。
- pytest 覆盖版本输出、smoke-test 和 Textual pilot 退出流程。
- Ruff 没有 lint 或格式问题。
- smoke-test 不需要交互式终端且能证明应用可构造。
- 内容审计不发现 token、私钥或机器专用绝对路径。

## Manual Checks

- [ ] TUI 标题和说明文案符合产品定位。
- [ ] `q` 可以退出，无 traceback。
- [ ] README 的安装和开发命令可以复制执行。
- [ ] GitHub 仓库为 public。

## Known Gaps

- 本次不验证真实 skill scanning 和 Codex 启动。
- 终端颜色和小尺寸兼容性在完整 selector 实现时验证。
