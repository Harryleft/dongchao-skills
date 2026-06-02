# 安装指南

> 本文档面向 AI Agent，说明如何从 GitHub 下载、安装和使用这些 Skill。

## 仓库地址

```
https://github.com/Harryleft/dongchao-skills.git
```

## 安装步骤

### Step 1：确认 agent 根目录

```bash
# 妙搭云电脑默认路径
~/workspace/agent/

# 或查看当前配置
openclaw status
```

下文用 `$AGENT_ROOT` 指代这个路径。

### Step 2：克隆仓库

```bash
cd /tmp
git clone https://github.com/Harryleft/dongchao-skills.git
```

### Step 3：复制 Skill

所有 Skill 统一放在 `skills/` 目录下。根据 Skill 类型，复制到对应安装位置：

| Skill 名称 | 安装目标位置 |
|------------|------------|
| `dongchao-feishu-*` 开头 | `$AGENT_ROOT/plugin-skills/` |
| `dongchao-miaoda-*` 开头 | `$AGENT_ROOT/plugin-skills/` |
| 其他 | `$AGENT_ROOT/skills/` |

```bash
AGENT_ROOT=~/workspace/agent

# 飞书/妙搭插件类 Skill
for skill in dongchao-feishu-ai-components dongchao-feishu-ai-viz-components dongchao-feishu-bitable-design dongchao-feishu-cron dongchao-feishu-x-to-doc; do
  cp -r /tmp/dongchao-skills/skills/$skill $AGENT_ROOT/plugin-skills/
done

# 妙搭教程类 Skill
for skill in dongchao-miaoda-translate dongchao-miaoda-tutorial; do
  cp -r /tmp/dongchao-skills/skills/$skill $AGENT_ROOT/plugin-skills/
done

# 通用类 Skill
for skill in dongchao-founders-playbook dongchao-superforecasting; do
  cp -r /tmp/dongchao-skills/skills/$skill $AGENT_ROOT/skills/
done
```

### Step 4：注册 Skill

编辑 `$AGENT_ROOT/openclaw.json`，在 `skills.entries` 中**追加**需要的条目：

```json
{
  "skills": {
    "entries": {
      "dongchao-feishu-ai-components": { "enabled": true },
      "dongchao-feishu-ai-viz-components": { "enabled": true },
      "dongchao-feishu-bitable-design": { "enabled": true },
      "dongchao-feishu-cron": { "enabled": true },
      "dongchao-feishu-x-to-doc": { "enabled": true },
      "dongchao-founders-playbook": { "enabled": true },
      "dongchao-miaoda-translate": { "enabled": true },
      "dongchao-miaoda-tutorial": { "enabled": true },
      "dongchao-superforecasting": { "enabled": true }
    }
  }
}
```

> ⚠️ 追加而非覆盖，保留已有条目。

### Step 5：重启

```bash
# 妙搭云电脑
sh $AGENT_ROOT/scripts/restart.sh

# 标准环境
openclaw gateway restart
```

### Step 6：清理 & 验证

```bash
rm -rf /tmp/dongchao-skills
openclaw skills check
```

## 选择性安装

Skill 之间无依赖，按需复制和注册即可。

## 更新

重新执行 Step 2~5，已有文件会被覆盖。
