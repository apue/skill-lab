# Skill Lab 产品规格

Status: accepted

## 目标

Skill Lab 是面向 macOS 个人 Codex 用户的 TUI 实验启动器。它让用户在启动新 Codex 会话前查看、调整和确认本次运行的有效 skill 集合，并记录足以解释实验环境的证据。

成功意味着：用户无需手输 skill 名称即可选择；每个状态都有 global、project 或 run 来源；实验启动使用经过 Codex 预检的精确集合；Skill Lab 故障不会阻止普通 Codex 启动；所有 Skill Lab 写入都位于当前 project root 内。

## Discovery

- 正常模式通过本地 `codex app-server` 的 `skills/list` 获取当前项目的 name、description、enabled、path、scope、interface 和 dependencies。
- App Server 只负责结构化 discovery 和启动预检，最终会话统一由原生 Codex CLI 启动。
- App Server 启动、协议、超时、schema 或 per-cwd error 会使实验能力进入 degraded 状态；不得把部分 App Server 结果与 filesystem 结果混合后声称完整。
- Filesystem fallback 只读 `<project-root>/.codex/skills` 与 `$CODEX_HOME/skills`；`CODEX_HOME` 未设置时使用 `~/.codex/skills`。
- Fallback 只检查 root 本身和直接 skill 子目录，可跟随 skill symlink；只读取或哈希 `SKILL.md` 与可选 `SKILL.json`。
- Fallback 不递归扫描整个 `.codex`，不读取 config、auth、session、log、history，不执行脚本或下载内容。
- Fallback 只能展示 inventory，不能推断 global enabled，因而不能 Save 或精确实验启动。

## Skill 身份与版本

- 运行时 identity 是解析后的绝对 `SKILL.md` 路径，用于去重、选择和一次性 Codex override。
- 可提交配置使用 portable locator：`project-relative`、`codex-home-relative` 或 `system`。
- `project-relative` 相对 project root；`codex-home-relative` 相对 `$CODEX_HOME`；`system` 使用 Codex scope 与唯一 skill name。
- 无法生成 portable locator 的 skill 可用于 `Launch once`，但不得保存为项目 defaults。
- 版本指纹优先采用声明 version；缺失时计算 `SKILL.md` 与可选 `SKILL.json` 文件字节的 SHA-256，不读取其他资源。

## 三层配置

优先级从低到高：

1. Codex `skills/list.enabled` 提供的 global baseline。
2. 项目 defaults。
3. 当前进程内的 run overlay。

- Project defaults 保存相对 global baseline 的最小 include/exclude 差异。
- Run overlay 保存相对 project effective state 的临时差异。
- 同层冲突、未发现 locator、歧义 locator、未知 schema 或配置错误会禁用实验模式，但不影响 normal launch。
- `Save as project defaults and launch` 把 staged 最终集合重算为相对 global 的最小差异，写入配置，清空 run overlay，再启动同一最终集合。
- 空 override 仍保存版本化空配置。

## TUI

- Project root 使用 Git top-level；非 Git 目录使用启动 cwd。
- 当前 App Server contract 不提供 package/source 字段，因此 MVP 使用 scope 作为稳定分组；package 默认折叠，方向键导航，左右键展开/折叠，Space 切换 skill 或完整 package，Enter 进入 Review，`q` 退出。
- 混合 package 的 Space 行为是 mixed -> all enabled -> all disabled。
- `/` 对 name、description、package 做大小写不敏感子串搜索，保持稳定排序；过滤期间切换 package 仍影响完整 package。
- 有 staged changes 时 `q` 需要确认丢弃；无变化时直接退出。
- Review 展示 project 相对 global、run 相对 project、最终 enabled 集合、来源和 dependency warnings。
- Review 始终提供 `Launch once`、`Save as project defaults and launch`、`Launch Codex normally`；默认焦点为 `Launch once`。

## 启动语义

- 所有会话通过原生 Codex CLI 子进程启动。
- 实验启动只增加一次性 skill overrides，不写 `~/.codex`，不改变 sandbox、approval 或其他用户配置。
- 实验启动前必须使用相同 overrides 调用短生命周期 App Server，确认实际 enabled 集合与 Review 完全一致。
- Preflight 失败或集合变化时展示原因；用户二次确认后可 normal launch，不得自动把旧 staged state 当作实验配置。
- `Launch Codex normally` 忽略 Skill Lab project/run 层并继承用户现有 Codex 配置。
- Codex 结束后更新记录、打印记录路径和退出状态，以 Codex 退出码返回 shell，不恢复 Textual 页面。
- 只有找不到或无法启动 Codex CLI 本身时，Skill Lab 无法提供 normal launch。

## 项目写入与运行证据

唯一写入命名空间：

```text
.skilllab/
├── config.toml
├── .gitignore
└── runs/
    └── <UTC timestamp>-<run id>.json
```

- `config.toml` 是可提交的项目 defaults，包含 `schema_version` 和 portable include/exclude locators。
- `.gitignore` 只忽略 `/runs/`；Skill Lab 不修改项目根 `.gitignore`。
- `runs/` 是本机证据。
- 写入使用同目录临时文件和原子替换；解析 symlink 后真实目标必须位于 project root。
- Save 时已确认的 TUI 最终状态是权威，可覆盖会话期间的外部配置变更。
- Experiment record 在启动前创建，退出后更新，包含 schema、run ID、UTC 时间、状态、退出码、模式、project-relative cwd、Git commit、Codex 版本/模型、解析摘要、最终 skills、fingerprints、dependency warnings 与 preflight。
- 不记录 prompt、对话、环境变量、auth 信息或外部绝对路径。
- Experiment record 创建失败时只允许 normal launch。
- Normal launch 尽力记录为 `passthrough`，`effective_skills = unknown`；记录失败不影响启动。

## 支持范围与非目标

- 正式支持 macOS、Python 3.12+、uv、Textual 和通过能力探测的 Codex CLI。
- 许可证为 MIT。
- 不实现 marketplace、registry、install/update/remove、自动评分、团队同步、跨 agent 管理、用户级 Skill Lab 状态目录或 Windows/Linux 正式支持。
