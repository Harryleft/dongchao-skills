# 沈东潮的 OpenClaw Skills 安装指南

> 本文档面向 AI Agent，说明如何从 GitHub 下载、安装和使用沈东潮的自定义 OpenClaw Skills。

---

## 一、仓库地址

```
https://github.com/Harryleft/dongchao-openclaw-skills.git
```

## 二、目录结构说明

```
dongchao-openclaw-skills/
├── README.md
├── plugin-skills/              → 复制到 <agent-root>/plugin-skills/
│   ├── feishu-bitable-design/       多维表格设计
│   ├── feishu-cron/                 飞书定时任务
│   ├── feishu-x-to-doc/            推文转文档
│   ├── miaoda-translate/            翻译
│   ├── miaoda-tutorial/             教程生成（精简版）
│   └── yao-tutorial-skill/          教程生成（完整版）
├── workspace-skills/           → 复制到 <agent-root>/workspace/skills/
│   ├── feishu-ai-components/        AI 组件
│   ├── feishu-ai-viz-components/    AI 可视化组件
│   ├── founders-playbook/           创始人手册
│   └── superforecasting/            超级预测
└── skills/                     → 复制到 <agent-root>/skills/
    └── openclaw-upgrade-troubleshoot/  OpenClaw 升级故障排查
```

**三个目录对应三个安装位置，必须放对：**

| 仓库目录 | 安装目标位置 | 说明 |
|---------|------------|------|
| `plugin-skills/*` | `<agent-root>/plugin-skills/` | 飞书/妙搭插件类 |
| `workspace-skills/*` | `<agent-root>/workspace/skills/` | 工作空间类 |
| `skills/*` | `<agent-root>/skills/` | 通用类 |

## 三、安装步骤

### Step 1：确认 agent 根目录

```bash
# 通常在以下位置之一
~/workspace/agent/          # 妙搭云电脑默认路径
# 或查看当前配置
openclaw status
```

下文用 `$AGENT_ROOT` 指代这个路径。

### Step 2：克隆仓库

```bash
cd /tmp
git clone https://github.com/Harryleft/dongchao-openclaw-skills.git
```

### Step 3：复制 Skill 到对应位置

```bash
AGENT_ROOT=~/workspace/agent

# plugin-skills → plugin-skills/
cp -r /tmp/dongchao-openclaw-skills/plugin-skills/* $AGENT_ROOT/plugin-skills/

# workspace-skills → workspace/skills/
cp -r /tmp/dongchao-openclaw-skills/workspace-skills/* $AGENT_ROOT/workspace/skills/

# skills → skills/
cp -r /tmp/dongchao-openclaw-skills/skills/* $AGENT_ROOT/skills/
```

### Step 4：注册 Skill 到 openclaw.json

编辑 `$AGENT_ROOT/openclaw.json`，在 `skills.entries` 中添加需要启用的 Skill：

```json
{
  "skills": {
    "entries": {
      "feishu-bitable-design": { "enabled": true },
      "feishu-cron": { "enabled": true },
      "feishu-x-to-doc": { "enabled": true },
      "miaoda-translate": { "enabled": true },
      "miaoda-tutorial": { "enabled": true },
      "yao-tutorial-skill": { "enabled": true },
      "feishu-ai-components": { "enabled": true },
      "feishu-ai-viz-components": { "enabled": true },
      "founders-playbook": { "enabled": true },
      "superforecasting": { "enabled": true },
      "openclaw-upgrade-troubleshoot": { "enabled": true }
    }
  }
}
```

> ⚠️ 不要覆盖已有的 `skills.entries`，只需要把新的条目**追加**进去。已有的条目保持不变。

### Step 5：重启 OpenClaw

```bash
# 妙搭云电脑环境
sh $AGENT_ROOT/scripts/restart.sh

# 标准 OpenClaw 环境
openclaw gateway restart
```

### Step 6：清理

```bash
rm -rf /tmp/dongchao-openclaw-skills
```

## 四、验证安装

重启后，检查 Skill 是否出现在可用列表中：

```bash
openclaw skills check
```

或在对话中直接测试，例如：
- "帮我设置一个定时任务" → 触发 `feishu-cron`
- "生成一份教程" → 触发 `miaoda-tutorial` 或 `yao-tutorial-skill`

## 五、选择性安装

如果不需要全部 Skill，只复制和注册需要的即可。各 Skill 相互独立，无依赖关系。

## 六、更新

仓库有更新时，重新执行 Step 2~5 即可。复制时已有文件会被覆盖。

```bash
cd /tmp && rm -rf dongchao-openclaw-skills
git clone https://github.com/Harryleft/dongchao-openclaw-skills.git
# 然后重复 Step 3~5
```

## 七、注意事项

1. **目录位置必须对应**：`plugin-skills` 的内容放 `plugin-skills/`，`workspace-skills` 的内容放 `workspace/skills/`，放错位置 Skill 无法加载
2. **openclaw.json 是追加不是覆盖**：编辑时保留已有配置，只追加新条目
3. **修改后必须重启**：Skill 文件的变更需要重启 OpenClaw 才能生效
4. **Skill 之间无依赖**：可以按需安装，不需要全装
