# Dongchao's OpenClaw Skills

沈东潮的 OpenClaw 自定义 Skill 集合，供团队复用。

## 目录结构

```
├── plugin-skills/          # 飞书/妙搭插件类 Skill
│   ├── feishu-bitable-design/    多维表格设计
│   ├── feishu-cron/              飞书定时任务
│   ├── feishu-x-to-doc/          推文转文档
│   ├── miaoda-translate/         翻译
│   ├── miaoda-tutorial/          教程生成（精简版）
│   └── yao-tutorial-skill/       教程生成（完整版）
├── workspace-skills/       # 工作空间类 Skill
│   ├── feishu-ai-components/     AI 组件
│   ├── feishu-ai-viz-components/ AI 可视化组件
│   ├── founders-playbook/        创始人手册
│   └── superforecasting/         超级预测
└── skills/                 # 通用 Skill
    └── openclaw-upgrade-troubleshoot/  OpenClaw 升级故障排查
```

## 使用方式

将对应 Skill 目录复制到你的 OpenClaw 环境：

- `plugin-skills/` → `<openclaw-root>/plugin-skills/`
- `workspace-skills/` → `<openclaw-root>/workspace/skills/`
- `skills/` → `<openclaw-root>/skills/`

然后在 `openclaw.json` 的 `skills.entries` 中注册启用。
