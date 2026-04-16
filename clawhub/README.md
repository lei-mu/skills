# ClawHub 发布说明

本文档说明当前仓库中 Skills 发布到 ClawHub 的规则、触发方式和配置约定。

## 一、当前发布入口

当前发布流程由 GitHub Actions 驱动，主要工作流如下：

- `.github/workflows/skill-validate.yml`
  - 用于校验发布配置和 Skill 元数据
  - 不会真实发布
- `.github/workflows/skill-publish.yml`
  - 用于预演发布或真实发布

## 二、发布元数据来源

当前规则已经固定为“两处分别负责不同信息”：

### 1. `clawhub/skills.publish.json`

负责发布层元数据：

- `source`
  - Skill 目录路径
  - 例如：`skills/pushplus`
- `slug`
  - Skill 唯一标识
  - 用于 `clawhub skill publish --slug`
- `name`
  - 发布显示名称
  - 用于 `clawhub skill publish --name`
- `publish`
  - 是否纳入自动发布管理

示例：

```json
{
  "skills": [
    {
      "source": "skills/pushplus",
      "slug": "pushplus",
      "name": "pushplus",
      "publish": true
    }
  ]
}
```

### 2. `skills/<skill>/SKILL.md`

负责 Skill 自身元数据：

- `version`
  - 发布版本号
- `changelog`
  - 发布说明
- `description`
  - Skill 描述
- `tags`
  - Skill 标签

当前发布流程中：

- `version` 从 `SKILL.md` 获取
- `changelog` 默认从 `SKILL.md` 获取

## 三、字段职责说明

### `slug`

- `slug` 是 Skill 的唯一标识
- 建议保持稳定，不要随便改
- 用于安装、版本查询、发布和后续平台识别

### `name`

- `name` 是发布显示名称
- 用于 `clawhub skill publish --name`
- 可以根据商店展示需求调整

### `source`

- `source` 是 Skill 的目录路径
- 当前脚本会把它作为发布目录使用
- 例如：

```bash
clawhub skill publish skills/pushplus --slug pushplus --name "pushplus"
```

也就是说：

- `source` 不是 `slug`
- `source` 不是显示名称
- `source` 就是 Skill 的实际目录路径

### `publish`

- `publish: true`
  - 表示该 Skill 会进入发布候选集合
- `publish: false`
  - 表示该 Skill 会被跳过，不参与发布流程

它的作用是“是否纳入自动发布管理”，不是是否真实发布，也不是是否 dry-run。

## 四、dry-run 规则

当前 `dry_run` 只在 `workflow_dispatch` 手动触发时生效。

### 手动触发时

在 GitHub Actions 页面手动运行 `Skill Publish`：

- `dry_run=true`
  - 默认值
  - 会执行登录、配置校验、版本探测
  - 不会真实发布
- `dry_run=false`
  - 会真实执行发布

### Tag 触发时

当通过 Git tag 触发发布时：

- `dry_run` 会被强制设为 `false`
- 即 Tag 触发一定是正式发布

## 五、Git Tag 的作用

当前 Git Tag 有两个作用：

### 1. 作为正式发布触发器

只有符合下面格式的 Tag 才会触发发布：

```text
skill-<slug>-v<version>
```

例如：

```text
skill-pushplus-v1.0.2
```

### 2. 作为发布参数来源

Tag 会解析出：

- `slug`
- `expected_version`

例如：

```text
skill-pushplus-v1.0.2
```

会解析成：

- `slug = pushplus`
- `expected_version = 1.0.2`

后续流程会校验：

- `skills.publish.json` 中存在 `slug=pushplus`
- 对应 `SKILL.md` 中的 `version` 必须等于 `1.0.2`

## 六、单 Skill 与批量发布规则

### Tag 触发

Tag 触发永远只发布一个 Skill。

例如本地有 `a`、`b`、`c` 三个待发布 Skill，如果推送：

```bash
git tag skill-a-v1.2.3
git push origin skill-a-v1.2.3
```

则只会发布 `a`，不会发布 `b`、`c`。

原因是 Tag 触发后，工作流会把 `skill_slug` 固定为 `a`，后续解析脚本只会筛选这个 Skill。

### 手动触发并指定 `skill_slug`

只发布指定的一个 Skill。

### 手动触发且不指定 `skill_slug`

会处理 `skills.publish.json` 中所有 `publish=true` 的 Skill。

因此当前规则可以总结为：

- Tag 触发：单 Skill 正式发布
- 手动触发 + 指定 `skill_slug`：单 Skill 预演或正式发布
- 手动触发 + 不指定 `skill_slug`：批量预演或批量发布

## 七、当前推荐用法

### 1. 校验配置

运行 `Skill Validate`，仅做校验，不发布。

### 2. 预演发布

手动运行 `Skill Publish`，保持：

- `dry_run=true`

这样可以先验证：

- 发布配置是否正确
- `SKILL.md` 版本是否正确
- 远端版本是否已存在

### 3. 正式发布

有两种方式：

#### 方式 A：手动正式发布

手动运行 `Skill Publish`，并设置：

- `dry_run=false`

#### 方式 B：Tag 正式发布

```bash
git tag skill-pushplus-v1.0.2
git push origin skill-pushplus-v1.0.2
```

Tag 方式更适合正式发版，因为它同时明确了：

- 发布哪个 Skill
- 发布哪个版本

## 八、维护建议

- `slug` 尽量保持稳定，不要频繁变更
- `name` 可以按商店展示需求调整
- 每次发布前同步更新 `SKILL.md` 中的 `version`
- 每次发布前同步更新 `SKILL.md` 中的 `changelog`
- 新增 Skill 但暂不发布时，可先设置 `publish=false`
