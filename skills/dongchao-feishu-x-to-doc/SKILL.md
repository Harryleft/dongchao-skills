---
name: dongchao-feishu-x-to-doc
version: 1.0.0
description: |-
  从 X/Twitter 提取推文或长文（Article）内容，翻译为中文（如原文为英文），
  并转换为飞书云文档。当用户提供 X/Twitter 链接并要求转换为文档时使用。
triggers:
  - "转文档"
  - "提取推文"
  - "X转文档"
  - "twitter转文档"
  - "推文转文档"
  - "保存推文"
  - "x to doc"
tools:
  - exec
  - read
  - write
  - feishu_create_doc
  - feishu_update_doc
  - lark-cli
mutating: true
depends-on:
  - dongchao-miaoda-translate
  - feishu-create-doc
  - dongchao-feishu-publish
  - ian-xiaohei-illustrations
---

# X/Twitter → 飞书云文档

从 X/Twitter 提取推文或长文内容，自动翻译（英文→中文），并创建为格式精美的飞书云文档。

## 触发条件

用户提供 X/Twitter 链接，并表达以下意图之一：
- "把这个转成文档"
- "保存到飞书文档"
- "提取这个内容"
- "帮我转一下"
- 任何包含 X/Twitter URL + 文档相关关键词的请求

**URL 识别模式：**
- `https://x.com/<user>/status/<id>`
- `https://twitter.com/<user>/status/<id>`
- `https://vxtwitter.com/<user>/status/<id>`
- `https://fxtwitter.com/<user>/status/<id>`

## 完整流程

### Step 1：提取推文 ID 和用户名

从 URL 中提取：
- `screen_name`：用户名（如 garrytan）
- `tweet_id`：推文 ID（如 2053127519872614419）

### Step 2a：线程（Thread）处理

如果 fxtwitter 返回的推文是线程的一部分（`tweet.thread` 存在），需要按顺序获取所有推文并拼接：

**检测方式：**
```json
// 线程推文通常在响应中包含
{"tweet": {"thread": [{"id": "...", "text": "..."}, ...]}}
// 或通过自引用检测：tweet.in_reply_to_screen_name === tweet.author.screen_name
```

**处理流程：**
1. 检测 `tweet.thread` 字段是否存在
2. 如果是线程：遍历 `thread` 数组，每条推文按 Step 3c 解析
3. 用 `---` 分隔符拼接所有推文
4. 线程推文只保留首条的元信息头，后续推文只保留正文

**注意：** fxtwitter 对线程的返回格式可能不完整。如果 thread 字段缺失但推文以 `🧵` 结尾或作者自回复，需要用 API 逐条获取后续推文。

### Step 2b：通过 fxtwitter API 获取内容

**API 端点：** `https://api.fxtwitter.com/<screen_name>/status/<tweet_id>`

```bash
curl -sL --max-time 15 \
  -A "Mozilla/5.0 (compatible; Googlebot/2.1)" \
  "https://api.fxtwitter.com/<screen_name>/status/<tweet_id>"
```

**返回结构关键字段：**

```
tweet
├── text                    # 推文文本
├── author
│   ├── screen_name         # 用户名
│   ├── name                # 显示名
│   ├── description         # 简介
│   └── avatar_url          # 头像
├── created_at              # 发布时间
├── likes / retweets / replies / bookmarks / views  # 互动数据
├── media                   # 媒体（图片/视频）
└── article                 # 长文（X Article），仅长文有此字段
    ├── title               # 标题
    ├── preview_text        # 摘要
    ├── cover_media         # 封面图
    └── content
        └── blocks[]        # 内容块数组
            ├── type        # 块类型：unstyled, header-two, unordered-list-item, atomic...
            ├── text        # 文本内容
            ├── inlineStyleRanges  # 行内样式（Bold, Italic...）
            └── entityRanges       # 链接等实体
    └── media_entities       # Article 正文图片 URL 映射，需与 atomic/MEDIA 块匹配
```

### Step 3：内容解析与 Markdown 转换

将 fxtwitter 返回的 JSON 转换为 Lark-flavored Markdown。

#### 3a. 判断内容类型

```
tweet.article 存在？
├─ 是 → 长文（Article），使用 article.blocks 解析
└─ 否 → 普通推文，使用 tweet.text
```

#### 3b. 长文（Article）解析规则

遍历 `article.content.blocks[]`，按 type 转换：

| block type | Markdown 输出 |
|-----------|---------------|
| `unstyled` | 普通段落文本 |
| `header-two` | `## ` + 文本 |
| `header-three` | `### ` + 文本 |
| `unordered-list-item` | `- ` + 文本 |
| `ordered-list-item` | `1. ` + 文本 |
| `atomic` | 媒体块（图片等），从 `entityMap` + `article.media_entities` 取 URL，并插入到原文对应位置 |

**行内样式处理（inlineStyleRanges）：**
- `Bold` → `**文本**`
- `Italic` → `*文本*`

**实体处理（entityRanges + entityMap）：**
- `LINK` → `[文本](url)`
- `MEDIA` → 通过 `data.mediaItems[].mediaId` 匹配 `article.media_entities[].media_id`，使用 `media_info.original_img_url`
- `IMAGE` → 使用实体里的 `url` 或 `src`

**Article 图片处理硬规则：**
- 必须优先抓取并保留原文图片，而不是把图片集中放到文末。
- `article.cover_media.media_info.original_img_url` 作为封面图，放在元信息分隔线后、正文开始前。
- `atomic` 图片块必须按 `article.content.blocks[]` 原始顺序插入在对应位置；常见做法是放在该 `atomic` 块前一个非空文本块之后。
- Markdown 图片使用空 alt：`![](https://...)`。不要写 `![封面图]`、`![文章配图]`、`原文封面图`、`原文配图 01` 等会在飞书中显示的图示/说明。
- 如果通过 `docs +media-insert` 上传本地图片，禁止设置 `--caption`；如已有 caption，必须用 `block_replace` 清除。
- 如果 X/fxtwitter 无法返回原图 URL、图片链接失效或图片无法上传，再调用 `ian-xiaohei-illustrations` 生成 4-8 张 Ian 小黑正文配图作为补图方案。

#### 3c. 普通推文解析

直接使用 `tweet.text`，如含媒体则追加图片。

**媒体处理：**
```json
// fxtwitter 返回的媒体结构
{"media": {
  "all": [
    {"type": "photo", "url": "https://...", "width": 1200, "height": 800},
    {"type": "video", "url": "https://...", "thumbnail_url": "https://...", "duration_ms": 30000},
    {"type": "gif", "url": "https://..."}
  ]
}}
```

- **图片：** 直接用 `<image url="..." />` 嵌入 Markdown
- **图片位置：** 普通推文图片按 fxtwitter 返回顺序追加到推文正文之后；Article 图片按上面的 atomic 块位置内联
- **视频：** 飞书文档不支持内嵌视频，用缩略图 + 链接替代：`[▶ 观看视频](video_url)`
- **GIF：** 按图片处理
- **多图：** 按原始顺序依次嵌入

**图片导入策略：**
- 首选 Markdown/URL 写入，保持图片处于正文原始位置。
- 如果飞书批量拉取外链图片卡住或失败，先创建/恢复纯文本正文，再把图片下载到 `assets/<article-slug>-original-images/`，用 `docs +media-insert` 逐张上传，之后用 `block_move_after` 移动到原文对应段落后。
- 不要长期保留“原文图片”之类的文末集中图片区块；这种区块只能作为临时中转，移动完成后必须删除。

### Step 4：翻译（如需要）

**判断规则：**
- 原文语言为英文 → 翻译为中文
- 原文语言为中文 → 保留原文
- 其他语言 → 翻译为中文

**翻译时加载 `dongchao-miaoda-translate` SKILL**，遵循其三种模式、术语处理、格式保留、质量检查规则。

**翻译策略：**
- 长文（Article）：使用普通模式，先分析内容提取术语和难点，再翻译全文，确保术语一致
- 普通推文：使用快速模式直接翻译
- 用户要求"精翻"时：使用精细模式（分析→翻译→审校→润色）
- 互动数据、用户名、链接等元信息不翻译

**核心翻译原则（来自 dongchao-miaoda-translate）：**
- **重写而非翻译**：用中文自然重写，不是逐句翻译。检验标准："读起来像是中文原创的吗？"
- **隐喻按意图翻译**：不直译字面意象，翻译作者意图
- **保留情感色彩**：不扁平化原文的情感表达
- **术语一致**：全文统一翻译，首次出现附英文原文

### Step 5：构建飞书云文档 Markdown

#### 文档结构模板

```markdown
# {article.title 或推文前30字}

**作者：** {author.name}（@{author.screen_name}）
**原文链接：** [{original_url}]({original_url})
**发布时间：** {created_at 本地化}
**互动数据：** {likes} 赞 · {retweets} 转 · {bookmarks} 收藏 · {views} 浏览

---

{封面图，如有，使用空 alt 图片}

{正文内容（已翻译，Article 图片按原文位置内联）}
```

**标题规则：**
- 文档标题和知识库列表引用标题都只使用文章标题本身。
- 不要自动追加 `（AI生成）`、`AI生成`、`由 AI 生成` 等后缀。

#### 格式增强

- 在关键洞察处添加 `<callout>` 高亮块
- 对比/并列内容使用 `<grid>` 分栏
- 流程/架构优先用 Mermaid 可视化
- 数据汇总用表格
- 封面图用空 alt 图片语法插入（如有）

#### 格式增强原则

| 原文特征 | 增强方式 |
|---------|---------|
| 关键洞察/核心论断 | Callout（💡light-blue 或 ⚡light-yellow） |
| 对比/并列观点 | Grid 分栏（2-3 列） |
| 流程/架构描述 | Mermaid 图 |
| 数据/指标 | 表格 |
| 封面图 | `![](url)` 插入，不带 caption |
| 警告/风险 | Callout（⚠️light-yellow 或 ❌light-red） |

#### 格式保留硬规则

- 优先保留原文 Markdown / 富文本结构，而不是降级为纯文本。
- Article blocks 必须按原始顺序转换，保留标题层级、引用、列表、分隔线、加粗、斜体、链接、代码块、表格和图片位置。
- 解析 `entityRanges` 与 `inlineStyleRanges` 时，如果二者范围重叠，创建后必须回读检查链接与样式是否错位；发现错位要用 `docs +update --command block_replace` 定点修复后再继续。
- 如果外链图片导入导致 `docs +create` 卡住，不要把纯文本结果作为最终交付；应保留正文 Markdown / 富文本格式创建文档，再下载图片到本地，用 `docs +media-insert` 按原文位置补插。
- 群消息不展示原文来源链接；原文来源只保留在飞书文档正文元信息中。

### Step 6：创建飞书云文档

调用 `feishu_create_doc` 工具：

```json
{
  "title": "{article.title 或推文前30字}",
  "markdown": "{构建好的 Markdown}"
}
```

**注意：** 长文档建议分段创建——先创建首段，再用 `feishu_update_doc` 的 append 模式追加后续内容。

### Step 6b：创建后的文档格式复查

创建文档后，先完成来源内容自身的格式复查，再进入发布后治理：

1. **图片位置与图示清理**
   - 回读新文档，确认图片数量与 fxtwitter 返回一致。
   - 确认图片位于正文对应段落附近，不是集中在文末。
   - 确认图片没有 `caption` 属性，也没有可见的 `原文封面图` / `原文配图 01` / `封面图` / `文章配图` 说明。
   - 如发现图片集中在文末或 caption 不为空，先用 `docs +media-insert`、`block_move_after`、`block_replace` 修复。

2. **正文格式复查**
   - 回读文档：标题不含 `（AI生成）`，正文末尾有 `（AI生成）`，标题层级、引用、列表、链接等格式未明显降级。
   - 发现格式错位时，先用 `docs +update --command block_replace` 定点修复。

### Step 6c：调用通用发布治理

格式复查通过后，调用 `dongchao-feishu-publish`，传入：

- 文档标题
- 最终 `doc_url`
- 摘要（如已生成）
- 来源类型：`X/Twitter`
- 原文链接（只进入文档元信息或内部记录，不出现在群消息中）
- 用户提供的发布配置：归档父节点、归档章节、管理者、通知群聊

`dongchao-feishu-publish` 负责：归档到用户指定知识库位置、写入指定章节、设置可读权限、授予指定管理者权限、发送指定群聊消息和最终验证。除非用户明确提供发布配置，不要在本 Skill 中自行猜测归档、授权或群发目标。

### Step 7：返回结果

向用户返回：
- 文档标题
- 飞书文档链接
- 知识库归档结果
- 简要摘要（1-2 句话概括内容）
- 权限设置结果
- 群聊转发结果

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| fxtwitter API 超时/失败 | 重试一次；仍失败则尝试 vxtwitter.com 替代端点：`curl -sL "https://vxtwitter.com/<screen_name>/status/<tweet_id>"`。如果替代端点也失败，用浏览器打开 fxtwitter.com 页面提取内容。**不要直接访问 x.com** |
| 推文已被删除/不存在 | 告知用户"该推文可能已被删除或不可访问" |
| 内容过长（>30,000 词） | 分段创建文档，使用 append 模式 |
| fxtwitter 返回 rate limit | 等待后重试，或告知用户稍后再试 |
| 飞书批量 URL 图片导入卡住 | 停止卡住进程；保留 Markdown / 富文本正文创建文档；下载图片到本地，逐张 `docs +media-insert` 上传，再 `block_move_after` 移动到正确段落 |
| 找不到 Article 图片 URL | 调用 `ian-xiaohei-illustrations`，按正文认知锚点生成 4-8 张小黑配图 |
| 发布后治理失败 | 交给 `dongchao-feishu-publish` 的失败处理；不要在本 Skill 中绕过归档、授权或群发验证 |
| 群聊 Markdown 消息发送失败 | 由 `dongchao-feishu-publish` 改用 `--text` 纯文本消息发送，并保持只发标题 + 文档链接 |
| 找不到通知群聊 | 由 `dongchao-feishu-publish` 停止发送并说明无法唯一命中 |
| 无法归档到用户指定父节点 / 章节 | 不要跳过归档后发群；由 `dongchao-feishu-publish` 说明阻塞点 |
| 组织内可读权限被拦截 | 由 `dongchao-feishu-publish` 根据权限错误提示处理；未完成授权时不要发群 |

## 反模式

| 反模式 | 为什么不行 |
|--------|-----------|
| 用浏览器直接爬 x.com | X 对 headless 浏览器有反爬，大概率超时或被墙 |
| 用 web_search 搜推文 | 搜索引擎索引不了具体推文内容 |
| 跳过翻译步骤 | 英文内容直接创建文档，对中文用户可读性差 |
| 不解析 inlineStyleRanges | 丢失原文的加粗、斜体等格式 |
| 翻译代码块和技术术语 | 代码和专有名词不应翻译 |
| 不添加原文链接 | 用户需要溯源 |
| 把 Article 原图集中放到文末 | 图片必须按原始 atomic 位置嵌入正文，文末集中图片区只允许做临时中转 |
| 给图片加“原文配图 01”等 caption | 用户不需要显示图示；图片 caption 必须为空 |
| 标题追加“（AI生成）” | 本技能生成的文档标题和列表引用标题都不加 AI 生成后缀 |
| 群消息显示原文来源链接 | 群消息只发标题和飞书文档链接，来源保留在文档正文里 |
| 在本 Skill 里手写归档、授权、群发流程 | 发布后治理统一交给 `dongchao-feishu-publish`，避免多个来源 Skill 维护重复规则 |
| 创建文档后不调用 `dongchao-feishu-publish` 就发群 | 默认需要完成知识库归档、权限配置和验证后再发群 |

## 快速参考

```
用户提供 X 链接
    │
    ▼
提取 tweet_id + screen_name
    │
    ▼
curl fxtwitter API ──→ 失败 → 重试/浏览器回退
    │
    ▼
解析 JSON（判断 Article vs 推文）
    │
    ▼
转换为 Markdown（处理样式/实体/媒体）
    │
    ▼
英文？──→ 是 → 加载 dongchao-miaoda-translate 翻译
    │         否 → 保留原文
    ▼
构建飞书 Markdown（元信息 + 正文 + 格式增强）
    │
    ▼
feishu_create_doc 创建文档
    │
    ▼
清理标题/图片 caption + 修复格式错位
    │
    ▼
调用 dongchao-feishu-publish
    │
    ▼
归档到指定知识库父节点 + 写入指定章节
    │
    ▼
设置可读权限 + 指定管理者权限
    │
    ▼
转发到指定群聊并验证
    │
    ▼
返回文档链接 + 摘要
```
