# Skill Lab 验收标准

Status: accepted

## 完成定义

- [ ] App Server discovery 能规范化 enabled、scope、source、dependency 和 error。
- [ ] Filesystem fallback 只访问标准 allowlisted roots，并进入只读 degraded 模式。
- [ ] Resolver 确定性实现 global、project、run 三层优先级和可解释 delta。
- [ ] Portable locator 不把机器绝对路径写入可提交配置。
- [ ] `.skilllab/config.toml`、嵌套 `.gitignore` 和 per-run JSON 遵守 project-root path guard。
- [ ] Selector 支持折叠、搜索、skill/package 切换、退出确认和 Review。
- [ ] Review 提供 Launch once、Save and launch、Launch normally。
- [ ] Experiment 使用相同 overrides preflight 后启动原生 Codex CLI。
- [ ] Degraded/错误状态始终保留 normal launch，除非 Codex CLI 本身不可执行。
- [ ] Experiment 与 passthrough records 遵守隐私契约并传播 Codex 退出码。
- [ ] 自动测试、Ruff、format、smoke-test 和内容审计通过。
- [ ] 真实 Codex macOS E2E 在发布前通过。
- [ ] 仓库包含 MIT License。

## 核心场景

1. Global enabled skill 被 project exclude 后默认禁用，run include 可临时恢复。
2. Global disabled skill 被 project include 后默认启用，run exclude 可临时关闭。
3. Save 将最终 staged 集合保存为相对 global 的最小差异。
4. 不可移植 skill 可 Launch once，但 Save 被解释性错误阻止。
5. App Server/per-cwd error 显示 degraded inventory，并允许 normal launch。
6. Preflight 集合变化不会以 experiment 启动，用户确认后可 normal launch。
7. Experiment record 创建失败时降级；passthrough record 失败仍启动 Codex。
8. `.skilllab` symlink 指向 project 外时拒绝写入。
9. Search 过滤时 package toggle 仍改变整个 package。
10. Codex 退出码由 `skilllab` 原样返回。

## 非验收范围

- Skill 生命周期管理、自动评价、团队配置、用户级状态和非 macOS 发布支持。
