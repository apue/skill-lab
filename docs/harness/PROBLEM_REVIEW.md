# Problem Review

Status: complete

## App Server 在 stdin EOF 后不返回响应

- 症状：用一次性 `subprocess.run(input=...)` 发送 initialize 与 `skills/list` 时，真实 Codex 没有 stdout。
- 证据：fake contract 通过，但 `codex app-server` 真实探测超时/空响应。
- Triage：integration-contract。
- 根因：App Server 是长生命周期双向 JSONL 协议；客户端必须等待 initialize response 后再发送 initialized 和 request，不能把 EOF 当成批处理完成信号。
- 修复：默认 transport 改为交互式 `Popen` pipes，按 request ID 顺序等待响应，并保留注入 runner 的确定性单测 seam。
- 验证：真实 Codex discovery 返回 catalog；交互顺序单测和 real E2E 通过。

## Codex metadata 可解析但严格 YAML fallback 拒绝

- 症状：真实 App Server catalog 包含某些本地 `SKILL.md`，Skill Lab normalization 却因宽松 frontmatter 报错。
- 证据：Codex 已提供有效 name/description/path，PyYAML 对未加引号的 colon description 报错。
- Triage：authority-boundary。
- 根因：normal mode 错把本地 YAML parser 当成 App Server metadata 的权威来源。
- 修复：normal mode 信任 App Server 的结构化字段；本地 parse 只补 version/fingerprint，失败时降级为 hash。filesystem fallback 仍严格拒绝无效 metadata。
- 验证：loose-YAML regression test 与真实 catalog normalization 通过。

## skills.config 使用目录路径导致 override 静默失效

- 症状：隔离 E2E discovery 成功，但 preflight 无法禁用 fixture skill。
- 证据：真实 `skills/list` 在 directory-path override 后仍报告 enabled；改为完整 `SKILL.md` 路径后匹配。
- Triage：runtime-contract。
- 根因：adapter 将 runtime identity 的父目录写入 `skills.config.path`，而当前 Codex 的 per-skill selector 使用 `SKILL.md` 路径。
- 修复：一次性 override 对每个 discovered skill 写完整 runtime path；不放宽 exact preflight。
- 验证：unit contract、隔离 App Server preflight 和原生 PTY E2E 均通过。

## 剩余差距

Codex 内建 system skills 在当前版本中可能不支持逐项禁用。Skill Lab 仍允许 staged intent，但 exact preflight 不匹配时禁止实验启动并提供 normal launch，不会声称已实现运行时不支持的集合。
