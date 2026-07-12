# 安全说明

## 第三方 Skills

Agent skill 可能包含模型指令、脚本、网络访问方式和工具调用建议。Skill Lab 未来即使能发现或启动第三方 skill，也不会把“出现在 marketplace”视为可信证明。

在采用第三方 skill 前，应检查：

- `SKILL.md` 及其引用文件。
- 可执行脚本和安装步骤。
- 网络访问、凭据读取和环境变量使用。
- 混淆、编码或动态下载内容。
- skill 来源、固定 commit 和更新差异。

## 本地文件访问边界

Skill Lab 的 discovery 只应访问 Codex API 返回的数据或明确配置的 skill roots。读取 skill symlink 的目标仅用于 metadata discovery。

Skill Lab 不应：

- 递归扫描整个 `~/.codex`。
- 读取 Codex auth、session、log 或 history。
- 在 discovery 阶段执行第三方 skill 脚本。
- 修改安装在 `~/.codex/skills` 下的 artifacts 或其源仓库。
- 默认修改 `~/.codex/config.toml`。

目标项目写入必须由 `Save as project defaults` 明确触发，并在解析真实路径后验证写入目标仍位于 project root 内。

## Codex 子进程

Skill Lab 不负责取代 Codex 自身的 sandbox 和 approval policy。启动 Codex 时不得默认加入绕过审批或扩大文件系统权限的参数。

## 报告漏洞

请不要在公开 Issue 中披露可利用的安全问题。使用 GitHub 仓库的 **Security → Report a vulnerability** 私下提交报告，并包含：

- 受影响版本或 commit。
- 复现步骤和最小样例。
- 可能影响的数据、文件或凭据。
- 已知缓解方式。

如果 GitHub private vulnerability reporting 尚未启用，请只创建不含利用细节的 Issue，请求维护者开启私下沟通渠道。

## 支持范围

项目尚未发布稳定版本。安全修复优先应用到 `main`，是否回移旧版本将在首次正式发布前定义。
