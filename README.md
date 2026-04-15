# luch skills

一个面向 agent/runtime 的通用 Skills 仓库。

当前仓库主要收录可直接复用的工具型 Skill，优先提供：
- 明确的使用时机
- 最小依赖的实现
- 可直接落地的脚本或配置
- 适合公开分发与持续扩展的目录结构


## 安装与使用

本仓库按 Skills 目录组织，可用于后续通过支持 Skill 安装能力的工具进行分发和集成。

### 方式 1：直接克隆仓库

适合当前本地使用或自行挑选某个 Skill 集成。

```bash
git clone https://github.com/lei-mu/skills.git
cd skills
```

如果你已配置 GitHub SSH，也可以使用：

```bash
git clone git@github.com:lei-mu/skills.git
cd skills
```

如果你当前是直接本地使用，可按下面方式理解：

1. 进入目标 Skill 目录查看 `SKILL.md`
2. 配置该 Skill 所需环境变量
3. 按文档中的脚本示例或函数示例调用

### 方式 2：通过 `npx skills add` 安装

适合后续通过 Skills 安装工具直接引入仓库中的 Skill。

示例：

安装技能

```bash
npx skills add lei-mu/skills
```

安装特定skills

```bash
npx skills add lei-mu/skills --skill <skill-name>
```

说明：
- 上述命令为公开分发场景下的示例写法，具体格式取决于你使用的 Skills 安装工具版本
- 如果安装工具支持从仓库中选择具体 Skill，建议优先选择目标 Skill，例如 `pushplus`
- 如果某个安装工具版本不支持 `--skill` 参数，请以该工具的实际文档为准
- 安装完成后，仍需按对应 Skill 的 `SKILL.md` 配置环境变量

### 方式 3：特定技能商店

|              | 仓库路径 | clawhub.ai slug                     |
| ------------ | -------- | ----------------------------------- |
| **安装命令** |          | `npx clawhub@latest install <slug>` |
|              | pushplus | pushplus                            |


## Skills list

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

当前已包含：
- `pushplus`：MIT License
