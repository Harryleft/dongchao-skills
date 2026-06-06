# Dongchao Skills

个人自研 Skill 统一放在本仓库的 `skills/<skill-name>` 下，并强制使用 `dongchao-` 前缀命名。各项目通过软链接引用这里的 Skill，不维护真实副本。

## 管理约定

- 个人自研 Skill 必须以 `dongchao-` 开头。
- 第三方依赖 Skill 可以放入本仓库作为子 Skill，但不加 `dongchao-` 前缀，并在说明中标注来源。
- 项目内 `.codex/skills/<skill-name>` 应软链接到本仓库 `skills/<skill-name>`。
- 修改自研 Skill 时优先修改本仓库，再让项目软链接自然生效。

## Skills

| Skill | 说明 |
|-------|------|
| `dongchao-feishu-ai-components` | 飞书 AI 组件 |
| `dongchao-feishu-ai-viz-components` | 飞书 AI 可视化组件 |
| `dongchao-feishu-bitable-design` | 多维表格设计 |
| `dongchao-feishu-cron` | 飞书定时任务 |
| `dongchao-feishu-publish` | 飞书文档发布治理 |
| `dongchao-feishu-x-to-doc` | X/Twitter 转飞书文档 |
| `dongchao-founders-playbook` | 创始人手册 |
| `dongchao-miaoda-translate` | 翻译 |
| `dongchao-miaoda-tutorial` | 教程生成（含妙记转教程、FDE 场景特化） |
| `dongchao-superforecasting` | 超级预测 |
| `dongchao-wechat-to-feishu-doc` | 微信文章转飞书文档 |
| `wechat-article-to-markdown` | 第三方依赖子 Skill：微信公众号文章抓取为 Markdown |
