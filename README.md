# lei-mu skills

一个面向 agent/runtime 的通用 Skills 仓库。

当前仓库主要收录可直接复用的工具型 Skill，优先提供：
- 明确的使用时机
- 最小依赖的实现
- 可直接落地的脚本或配置
- 适合公开分发与持续扩展的目录结构

## 当前 Skills

### 1. pushplus

路径：`skills/pushplus`

简介：
- 基于 PushPlus(推送加) 的消息通知 Skill
- 支持微信、邮件、短信、企业微信、钉钉、飞书等多种渠道
- 适合系统告警、任务完成提醒、失败通知、日报推送等场景

主要能力：
- 基础消息发送
- 多渠道同时发送
- 群组消息
- OpenAPI 查询与管理能力

入口文档：
- `skills/pushplus/SKILL.md`

## 仓库结构

```text
skills/
  pushplus/
    SKILL.md
    LICENSE
    references/
    scripts/
```

## 安装与使用

本仓库按 Skills 目录组织，可用于后续通过支持 Skill 安装能力的工具进行分发和集成。

如果你当前是直接本地使用，可按下面方式理解：

1. 进入目标 Skill 目录查看 `SKILL.md`
2. 配置该 Skill 所需环境变量
3. 按文档中的脚本示例或函数示例调用

## 环境变量说明

不同 Skill 会在各自的 `SKILL.md` 中声明所需环境变量。

以 `pushplus` 为例：
- `PUSHPLUS_TOKEN`：基础消息发送
- `PUSHPLUS_USER_TOKEN`：OpenAPI 用户 Token
- `PUSHPLUS_SECRET_KEY`：OpenAPI SecretKey

## 设计目标

这个仓库希望保持以下原则：
- 通用优先：尽量不绑定单一 agent 平台
- 最小依赖：优先使用标准库或轻依赖实现
- 可维护：目录清晰，文档和脚本边界明确
- 可扩展：后续可以持续新增更多独立 Skill

## 适用场景

这类 Skills 适合用于：
- 编码代理的任务完成通知
- 自动化任务结果推送
- 系统监控和异常告警
- 定时任务、日报、构建结果通知
- 需要外部消息触达的人机协作流程

## 开源说明

当前每个 Skill 可根据自身情况单独附带许可证。

`pushplus` 当前使用：
- MIT License

## 贡献说明

如果后续新增 Skill，建议保持以下约定：
- 每个 Skill 独立目录
- 提供 `SKILL.md`
- 提供最小可运行脚本或实现
- 说明环境变量、使用边界和风险操作

## 后续规划

当前仓库处于第一阶段，已公开第一个通知类 Skill：`pushplus`。

后续会继续补充更多适合 agent/runtime 使用的通用 Skills。
