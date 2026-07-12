# Skill Lab 决策记录

Status: review

## 2026-07-12：把产品定义为实验启动器

Status: accepted

Context: 初始讨论扩张到 marketplace、package management、profile、watch 和自动评价。

Decision: 第一阶段只解决可复现的 skill-set 选择、新会话启动和证据记录。

Alternatives considered: 完整 skill 生命周期平台；简单 symlink 管理器。

Consequences: Marketplace、安装、更新、删除和 release watch 延后。

## 2026-07-12：TUI 作为主交互

Status: accepted

Context: `--with/--without` 要求手输 skill 列表，容易拼写错误且难以确认最终集合。

Decision: 默认命令 `skilllab` 进入 TUI；命令行参数未来只用于自动化。

Consequences: 脚手架需要可测试的终端应用生命周期。

## 2026-07-12：三层配置解析

Status: accepted

Decision: 使用 global baseline、project defaults 和 run overlay，后者覆盖前者。

Consequences: 项目可以排除 global skill；Space 只修改 staged run selection，持久化必须显式确认。

## 2026-07-12：Python + uv + Textual

Status: accepted

Context: 工具以文件、TOML、子进程和多选 TUI 为主，当前目标是快速验证产品价值。

Decision: Python 3.12+、uv、Textual、pytest 和 Ruff。

Alternatives considered: Node/pnpm/Ink；Bun 单文件编译；Rust/Ratatui。

Consequences: 优先开发速度；公开单文件 binary 延后评估。

## 2026-07-12：独立子仓库

Status: accepted

Decision: 在聚合目录中创建 `skill-lab/` 独立 Git 仓库，与其他 skills 仓库并列。

Consequences: 顶层目录保持无 Git；Skill Lab 独立发布和版本管理。
