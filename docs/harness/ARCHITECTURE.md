# Skill Lab 架构

Status: review

## 总体设计

Skill Lab 采用“确定性解析器 + TUI 选择器 + Codex 适配器”的分层结构。TUI 只产生用户意图，配置解析器计算最终有效 skill 集合，Codex 适配器把该集合转换为新进程启动配置。运行证据独立落盘，避免 UI、配置和进程控制相互耦合。

## 模块边界

- `app.py`：Textual 应用组合、页面切换和键盘交互。
- `discovery.py`：从 Codex 和文件系统读取已安装 skills，不决定启用状态。
- `resolution.py`：合并 global、project 和 run overlay，产生可解释的有效集合。
- `config.py`：读取和写入用户/项目 TOML，不包含 TUI 逻辑。
- `codex.py`：生成并执行 Codex 启动命令，不负责选择策略。
- `records.py`：保存运行环境指纹和人工证据。
- `cli.py`：控制入口、退出码和依赖装配。

## 数据与控制流

```text
Codex/filesystem discovery
          │
          ▼
 InstalledSkill[]
          │
global + project config ──► resolver ◄── run overlay from TUI
                                  │
                                  ▼
                         EffectiveSkillSet
                           │             │
                           ▼             ▼
                    Codex launcher   run recorder
```

## 状态模型

“已下载”“当前项目允许”“本次运行启用”是不同概念。MVP 不把文件存在等同于启用状态。

- Installed：skill artifact 可被发现。
- Inherited：由 global baseline 或项目默认引入。
- Excluded：被更高优先级配置排除。
- Run override：仅本次启动改变。
- Effective：解析后的最终布尔状态。

## TUI 结构

MVP 计划包含三个页面：

1. Skill selector：分组、搜索、多选和来源说明。
2. Review：展示 delta 和最终集合。
3. Launch status：展示记录写入和 Codex 子进程状态。

本次脚手架只实现一个可启动的状态页，用来验证工程配置和 Textual 生命周期。

## 外部依赖

- Python 3.12+：运行时。
- uv：环境、锁文件和 tool 安装。
- Textual：TUI 框架。
- Codex CLI/app-server：未来运行时适配目标。
- pytest：测试。
- Ruff：lint 与格式检查。

## Capability Boundary

Skill Lab 采用应用级路径策略，而不是在 MVP 中实现 OS 级 sandbox。

### Discovery capability

- 首选 Codex `skills/list`，减少对用户目录的直接扫描。
- fallback 只接受明确配置的 skill roots。
- 允许跟随 skill symlink 读取目标 `SKILL.md` metadata。
- 禁止扫描整个 `~/.codex`，禁止读取 auth/session/log/history，禁止执行第三方脚本。

### Write capability

- TUI selection 本身不产生写入。
- `Launch once` 不写项目默认配置。
- `Save as project defaults and launch` 是目标项目写入的明确授权动作。
- 写入前解析目标路径和符号链接，验证目标位于 project root 内，再进行原子替换。
- MVP 不写 `~/.codex` 或任意用户级状态目录。

### Child process capability

Codex adapter 只提供 skill selection 和必要启动信息，不添加绕过 approval 或扩大 sandbox 的默认参数。Codex 子进程的权限仍由用户现有 Codex 配置控制。

## 错误处理原则

- 配置解析失败时不启动 Codex，并指出具体文件与字段。
- 同层 include/exclude 冲突时失败，不自动选择一方。
- 找不到 Codex 时保留用户配置，不产生部分运行记录。
- 记录写入失败时不声称实验可复现。
- 子进程退出码原样映射到 Skill Lab 的结果状态。

## 备选方案

### 每项目复制 skills

- 优点：直观、原生发现。
- 缺点：重复、升级漂移，且不能排除其他 global skills。
- 决策：拒绝作为主架构。

### 多个 CODEX_HOME

- 优点：隔离彻底。
- 缺点：同时分裂 auth、plugins、MCP 和会话状态。
- 决策：拒绝作为默认方案。

### TypeScript/Bun

- 优点：可编译单文件，TUI 组件生态丰富。
- 缺点：本阶段增加构建与发布复杂度。
- 决策：Python + uv + Textual 优先验证产品价值。

## 风险

- Codex skill 配置接口继续演进。
  - 缓解：把所有版本相关逻辑封装在 `codex.py`。
- TUI 选择状态与实际 Codex 可见集合不一致。
  - 缓解：启动前用 Codex prompt/config 诊断结果做契约验证。
- 过早扩张为 package manager。
  - 缓解：MVP 明确排除 marketplace、安装和更新。
- 路径遍历或 symlink 使项目写入逃逸到外部目录。
  - 缓解：集中 path guard，解析真实路径后验证 project-root containment，并以单元测试覆盖。
- discovery 意外读取 Codex 凭据或会话数据。
  - 缓解：优先 API discovery；fallback 使用 allowlisted roots 和明确文件名，不进行 home-directory crawl。
- skill 效果高度随机。
  - 缓解：记录环境，后续加入重复运行与人工评价，而不是单次自动评分。
