# Skill Lab 设计说明

## 设计结论

Skill Lab 的第一阶段是一个 TUI 模式的 Skill Experiment Launcher。它不解决 skill 安装生态，而是让个人 Codex 用户在新会话启动前精确选择有效 skill 集合，并保留可复现的运行证据。

## 为什么要做

skill 是否有价值只能在具体任务、模型、项目和版本下判断。全局安装状态、一次主观体验或同一对话里的口头禁用，都不足以形成可靠证据。Skill Lab 首先解决变量隔离和选择可见性。

## 核心交互

用户在项目目录运行：

```bash
skilllab
```

TUI 显示 global baseline、项目覆盖和当前 run overlay。方向键导航，Space 切换 staged selection，Enter 进入 review。

Review 页面提供：

- `Launch once`：只对新启动的这次 Codex 会话生效。
- `Save as project defaults and launch`：写入项目覆盖，再启动新会话。

任何选择在确认前都不写配置。

## 配置优先级

```text
global baseline
      ↓
project include/exclude
      ↓
run overlay
      ↓
effective skill set
```

项目的负覆盖可以禁用从 global baseline 继承的 skill。run overlay 可以临时恢复或排除项目默认值。

## 技术架构

- Python 3.12+。
- uv 管理 runtime、依赖、锁文件和 tool installation。
- Textual 提供 TUI。
- 纯函数 resolver 负责状态计算。
- Codex adapter 负责版本相关的配置与进程启动。
- JSON/JSONL 记录实验环境，不把评价逻辑耦合进 launcher。

## MVP 阶段

### Scaffold

建立独立公开仓库、中文文档、可运行 TUI 骨架、测试和质量配置。

### Selector

实现 discovery、三层 resolver、搜索、多选、package 折叠和 review 页面。

### Launcher

实现 Codex 配置生成、新会话启动和运行记录。

### Real-world validation

使用 2～3 个真实 skills 完成有/无对照。只有验证确有价值后，才考虑自动比较、marketplace 或更新监控。

## 明确延后

- Marketplace 和 package backend。
- install/update/remove/purge。
- 自动质量分数和 LLM judge。
- profile 继承、团队配置和多 agent 支持。
- author/release watcher。

## 成功标准

用户能够不手输 skill 名称，启动一个精确、可解释、可记录的新 Codex skill 环境；该流程在真实 skill 试验中能改变或增强用户的采用判断。
