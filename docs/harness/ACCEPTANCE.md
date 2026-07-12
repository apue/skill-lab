# Skill Lab 验收标准

Status: review

## 本次交付完成定义

- [ ] 仓库为独立 Git 项目，并有公开 GitHub remote。
- [ ] `pyproject.toml` 明确 Python、依赖、CLI、pytest 和 Ruff 配置。
- [ ] `uv lock` 成功生成锁文件。
- [ ] `uv run skilllab` 可启动 Textual TUI，用户可按 `q` 退出。
- [ ] 自动测试覆盖入口元数据和 TUI 基本渲染/退出行为。
- [ ] `uv run pytest` 全部通过。
- [ ] `uv run ruff check .` 和 `uv run ruff format --check .` 通过。
- [ ] README、产品规格、架构、决策、验证计划和实施计划可供中文 review。
- [ ] 根目录 `AGENTS.md` 规定范围、验证、模块边界和文件访问策略。
- [ ] 公开前检查提交文件，不包含 token、认证文件或机器专用绝对路径。

## 验收场景

1. Given 新 clone 的仓库和已安装的 uv，When 执行 `uv sync --dev`，Then 项目依赖可被确定性安装。
2. Given 依赖已安装，When 执行 `uv run skilllab`，Then 终端显示 Skill Lab 脚手架界面。
3. Given TUI 已启动，When 用户按 `q`，Then 应用正常退出且无 traceback。
4. Given 项目源码，When 执行测试和 Ruff 命令，Then 所有自动化检查通过。

## 人工 Review 清单

- [ ] 产品目标聚焦于 skill 效果实验，而不是库存管理。
- [ ] MVP 与未来功能边界清楚。
- [ ] TUI 是主要交互，不依赖手输 skill 列表。
- [ ] global、project 和 run overlay 三层语义可理解。
- [ ] `Launch once` 与 `Save as project defaults and launch` 区别清楚。
- [ ] 模块边界支持未来替换 Codex 适配方式。
- [ ] 权限文档区分 Skill Lab 本身与 Codex 子进程，并禁止读取 Codex 凭据/会话数据。

## 非本次验收范围

- 真实 skill discovery。
- skill 多选和 package 折叠。
- 配置保存。
- Codex 子进程启动。
- A/B 比较与评价录入。
