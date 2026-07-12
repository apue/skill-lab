# Skill Lab 架构

Status: accepted

## 总体设计

Skill Lab 使用“Codex adapter + discovery normalizer + pure resolver + project persistence + Textual selector”的分层结构。App Server 只提供结构化 skill catalog 与 preflight；真正的交互会话始终由原生 Codex CLI 承载。任何实验能力故障都降级为显式 normal launch，不伪造可复现证据。

## 模块边界

- `models.py`：不可变领域类型、portable locator、错误与运行模式。
- `discovery.py`：规范化 App Server catalog、受限 filesystem inventory、package grouping 和 fingerprints。
- `resolution.py`：纯函数合并 global/project/run，不做 I/O。
- `config.py`：project root 识别、TOML schema、locator resolution、path guard 与原子写入。
- `codex.py`：App Server JSONL 协议、能力探测、一次性 overrides、preflight 与 CLI 子进程。
- `records.py`：project-local JSON 运行记录。
- `app.py`：Textual selector/review/degraded UI，只表达用户意图。
- `cli.py`：依赖装配、TUI 结果处理、启动和退出码。

## 数据流

```text
codex app-server skills/list ──► discovery ──► InstalledSkill[]
           │                         │
           │ failure                 ▼
           └────────► fallback inventory / degraded UI

InstalledSkill[] + project config + staged overlay
                         │
                         ▼
                   pure resolver
                         │
                         ▼
                   review snapshot
                         │
              same override preflight
                         │ exact match
                         ▼
                 native Codex CLI
                    │          │
                    ▼          ▼
                 records     exit code
```

## 核心类型

- `SkillLocator(kind, value, name)`：项目配置的稳定引用。
- `InstalledSkill(runtime_path, locator, name, description, enabled, scope, package, version, fingerprint, dependencies)`。
- `SkillLayer(include, exclude)`。
- `ResolvedSkill(skill, enabled, source)`。
- `ResolutionResult(project, run, project_delta, run_delta)`。
- `DiscoveryResult(skills, errors, mode)`。
- `LaunchRequest(mode, cwd, effective_skills)` 与 `LaunchResult(exit_code, record_path)`。

## 安全边界

- Discovery 只访问明确允许的 skill metadata 文件。
- 所有项目写入经过集中 realpath containment guard。
- 子进程通过 argv 启动，不拼接 shell command。
- Skill Lab 不添加降低 sandbox、绕过 approval 或扩大 writable roots 的参数。
- Passthrough 不声称知道 effective skills。
- 记录不包含对话、凭据、环境变量或外部绝对路径。

## 错误策略

- 配置、catalog 或 preflight 错误禁用 experiment/save，但保留 normal launch。
- Codex CLI 不存在或无法执行时返回明确错误。
- Experiment record 无法创建时降级；passthrough record 失败不阻塞。
- 子进程退出码原样传播。
