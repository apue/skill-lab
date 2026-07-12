# 安全说明

## 第三方 Skills

Agent skill 可能包含模型指令、脚本、网络访问方式和工具调用建议。Skill Lab 未来即使能发现或启动第三方 skill，也不会把“出现在 marketplace”视为可信证明。

在采用第三方 skill 前，应检查：

- `SKILL.md` 及其引用文件。
- 可执行脚本和安装步骤。
- 网络访问、凭据读取和环境变量使用。
- 混淆、编码或动态下载内容。
- skill 来源、固定 commit 和更新差异。

## 报告漏洞

请不要在公开 Issue 中披露可利用的安全问题。使用 GitHub 仓库的 **Security → Report a vulnerability** 私下提交报告，并包含：

- 受影响版本或 commit。
- 复现步骤和最小样例。
- 可能影响的数据、文件或凭据。
- 已知缓解方式。

如果 GitHub private vulnerability reporting 尚未启用，请只创建不含利用细节的 Issue，请求维护者开启私下沟通渠道。

## 支持范围

项目尚未发布稳定版本。安全修复优先应用到 `main`，是否回移旧版本将在首次正式发布前定义。
