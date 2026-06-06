---
name: dongchao-feishu-publish
description: "对已创建的飞书 Docx 做发布后治理：归档到指定知识库位置，设置可读权限，给指定协作者管理权限，通知指定群聊，并回读验证。Use when a workflow has already produced a Feishu document URL/token and needs standard post-publish governance."
---

# 飞书文档发布治理

本 Skill 只处理“文档已创建之后”的固定发布动作。它不抓取原文、不翻译、不修正文档正文格式；微信、X/Twitter、RSS 等来源 Skill 负责产出飞书 Docx，本 Skill 负责归档、权限、群发和验证。

## 输入

必须拿到：
- `doc_url` 或 docx token
- 文档标题

必须拿到发布配置，缺失时先询问用户，不要猜测：
- `archive_parent_url`：归档父节点 wiki URL 或 node token
- `archive_section_title`：父页面内用于插入文档引用的章节标题
- `manager`：管理者配置，优先提供 `open_id`；也可提供 `name`、`email`、`department_hint` 供运行时唯一解析
- `notification_chat`：通知群配置，优先提供 `chat_id`；也可提供 `name` 供运行时唯一解析

可选：
- 摘要
- 来源类型、来源链接
- `archive_parent_title`：归档父节点标题，用于验证
- `link_share_entity`：默认 `tenant_readable`
- `manager_perm`：默认 `full_access`
- `notification_identity`：默认 `--as user`

## 发布配置变量

本仓库不得写死组织内部 URL、人员 open_id、群聊 chat_id、邮箱、部门名等租户信息。运行时从用户输入或项目私有配置中取得以下变量：

```yaml
doc_url: "<已创建的飞书 Docx URL>"
title: "<文档标题>"
publish:
  archive_parent_url: "<wiki URL 或 node token>"
  archive_parent_title: "<可选：父节点标题>"
  archive_section_title: "<父页面内归档章节标题>"
  link_share_entity: "tenant_readable"
  manager:
    open_id: "<可选：用户 open_id>"
    name: "<可选：姓名>"
    email: "<可选：邮箱>"
    department_hint: "<可选：部门关键词>"
    perm: "full_access"
  notification_chat:
    chat_id: "<可选：群聊 chat_id>"
    name: "<可选：群聊名称>"
  notification_identity: "user"
```

缺少 `archive_parent_url`、`archive_section_title`、管理者标识或群聊标识时，必须暂停并向用户索取。不能使用示例值、历史运行值或模型记忆中的内部 ID。

群消息固定为两行纯文本，第一行标题，第二行最终飞书文档链接。

## 工作流

1. **解析文档和归档目标**
   - 用 `drive +inspect --url <doc_url>` 获取 `token`、`type`、规范 URL 和标题。
   - 目标文档必须是 `docx`；不是 `docx` 时先说明限制，不要猜测迁移。
   - 用 `wiki +node-get --as user --node-token <archive_parent_url>` 获取 `space_id`、`node_token`、`obj_token`。
   - 如提供 `archive_parent_title`，确认解析到的节点标题一致。
   - 用 `docs +fetch --api-version v2 --as user --doc <archive_parent_url> --scope outline --max-depth 3` 确认存在 `<archive_section_title>`。

2. **移动到知识库**
   - 用 `wiki +move --as user --obj-token <docx_token> --obj-type docx --target-space-id <space_id> --target-parent-token <父节点node_token>`。
   - 如果返回异步任务，按返回的 `drive +task_result --scenario wiki_move` 继续轮询。
   - 记录移动后的最终 wiki/doc URL，后续群发使用这个最终链接。

3. **写入章节引用**
   - 用 outline 或 `docs +fetch --detail with-ids --scope keyword --keyword <archive_section_title>` 拿到归档章节的 block id。
   - 在该章节下插入列表引用：
     `<ul><li><cite doc-id="<docx_token>" file-type="docx" title="<clean_title>" type="doc"></cite></li></ul>`
   - `clean_title` 不允许带 `（AI生成）`。
   - 插入后用关键词或章节回读确认引用存在。

4. **设置权限**
   - 组织内可读：
     `drive permission.public patch --as user --params '{"token":"<token>","type":"docx"}' --data '{"link_share_entity":"<link_share_entity>","external_access":false,"share_entity":"same_tenant","security_entity":"anyone_can_view","comment_entity":"anyone_can_view"}'`
   - 管理者解析：
     - 如果 `manager.open_id` 已提供，直接使用该 open_id。
     - 如果未提供 open_id，用 `contact +search-user --as user --query "<manager.name 或 manager.email>"` 解析。
     - 如有 `manager.department_hint` 或 `manager.email`，用它们缩小候选。
     - 无法唯一命中时停止，列出候选让用户确认；不要猜。
   - 用 `drive permission.members create --as user --params '{"token":"<token>","type":"docx","need_notification":false}' --data '{"member_type":"openid","member_id":"<manager_open_id>","perm":"<manager_perm>","type":"user"}'` 授权。
   - 权限写操作是高影响操作。只有当前用户请求明确包含发布/授权/归档/群发时，才继续执行；若 CLI 返回确认门禁，按提示向用户确认后再追加 `--yes`。
   - 权限未完成时不要发送群消息。

5. **发送群消息**
   - 群聊解析：
     - 如果 `notification_chat.chat_id` 已提供，直接使用该 chat_id。
     - 如果未提供 chat_id，用 `im +chat-search --as user --query "<notification_chat.name>"` 解析。
     - 多个同名或未命中时停止并说明候选，不要猜。
   - 用 `im +messages-send --as <notification_identity> --chat-id <chat_id> --text "<标题>\n<最终文档链接>" --idempotency-key <stable-key>` 发送。
   - `stable-key` 必须短且稳定，建议 `pub-<doc前8位>-<序号>`，例如 `pub-FQ8G-001`；不要拼接完整 doc token 和 chat id，过长会触发字段校验失败。

6. **最终验证**
   - `wiki +node-list` 或 `wiki +node-get` 确认新文档在 `<archive_parent_title 或 archive_parent_url>` 节点下。
   - 回读 `<archive_section_title>` 章节，确认有该文档引用。
   - `permission.public.get` 确认 `link_share_entity=<link_share_entity>`。
   - 如可用，回读协作者权限确认 `<manager_open_id>=<manager_perm>`。
   - 用消息 ID 或 `im +messages-mget` 确认群消息发送成功。

## 失败处理

- 找不到归档父节点或章节：停止，不发群。
- 缺少归档父节点、章节名、管理者或群聊配置：停止，向用户索取变量。
- 管理者无法唯一解析：停止，列出候选让用户确认。
- 群聊无法唯一解析：停止，列出候选让用户确认。
- 组织内可读被租户策略、密级或外部分享策略拦截：说明具体错误和文档链接，不发群。
- 归档或授权失败：不要跳过后续验证直接发群。

## 返回结果

最终向用户简短返回：
- 文档标题和最终链接
- 归档结果
- 可读权限结果
- 管理者权限结果
- 群聊通知结果
