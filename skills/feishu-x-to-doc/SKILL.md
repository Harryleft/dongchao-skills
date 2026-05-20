---
name: feishu-x-to-doc
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
mutating: true
depends-on:
  - miaoda-translate
  - feishu-create-doc
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
| `atomic` | 媒体块（图片等），从 `entityMap` 取 URL |

**行内样式处理（inlineStyleRanges）：**
- `Bold` → `**文本**`
- `Italic` → `*文本*`

**实体处理（entityRanges + entityMap）：**
- `LINK` → `[文本](url)`

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
- **视频：** 飞书文档不支持内嵌视频，用缩略图 + 链接替代：`[▶ 观看视频](video_url)`
- **GIF：** 按图片处理
- **多图：** 按原始顺序依次嵌入

**不下载上传到飞书。** 图片直接引用 fxtwitter URL，飞书文档支持外部图片引用。如果图片链接失效，用户可点击原文链接查看。

### Step 4：翻译（如需要）

**判断规则：**
- 原文语言为英文 → 翻译为中文
- 原文语言为中文 → 保留原文
- 其他语言 → 翻译为中文

**翻译时加载 `miaoda-translate` SKILL**，遵循其三种模式、术语处理、格式保留、质量检查规则。

**翻译策略：**
- 长文（Article）：使用普通模式，先分析内容提取术语和难点，再翻译全文，确保术语一致
- 普通推文：使用快速模式直接翻译
- 用户要求"精翻"时：使用精细模式（分析→翻译→审校→润色）
- 互动数据、用户名、链接等元信息不翻译

**核心翻译原则（来自 miaoda-translate）：**
- **重写而非翻译**：用中文自然重写，不是逐句翻译。检验标准："读起来像是中文原创的吗？"
- **隐喻按意图翻译**：不直译字面意象，翻译作者意图
- **保留情感色彩**：不扁平化原文的情感表达
- **术语一致**：全文统一翻译，首次出现附英文原文

### Step 5：构建飞书云文档 Markdown

#### 文档结构模板

```markdown
**作者：** {author.name}（@{author.screen_name}）
**原文链接：** [{original_url}]({original_url})
**发布时间：** {created_at 本地化}
**互动数据：** {likes} 赞 · {retweets} 转 · {bookmarks} 收藏 · {views} 浏览

---

{正文内容（已翻译）}
```

#### 格式增强

- 在关键洞察处添加 `<callout>` 高亮块
- 对比/并列内容使用 `<grid>` 分栏
- 流程/架构优先用 Mermaid 可视化
- 数据汇总用表格
- 封面图用 `<image url="..." />` 插入（如有）

#### 格式增强原则

| 原文特征 | 增强方式 |
|---------|---------|
| 关键洞察/核心论断 | Callout（💡light-blue 或 ⚡light-yellow） |
| 对比/并列观点 | Grid 分栏（2-3 列） |
| 流程/架构描述 | Mermaid 图 |
| 数据/指标 | 表格 |
| 封面图 | `<image>` 插入 |
| 警告/风险 | Callout（⚠️light-yellow 或 ❌light-red） |

### Step 6：创建飞书云文档

调用 `feishu_create_doc` 工具：

```json
{
  "title": "{article.title 或推文前30字}",
  "markdown": "{构建好的 Markdown}"
}
```

**注意：** 长文档建议分段创建——先创建首段，再用 `feishu_update_doc` 的 append 模式追加后续内容。

### Step 7：返回结果

向用户返回：
- 文档标题
- 飞书文档链接
- 简要摘要（1-2 句话概括内容）

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| fxtwitter API 超时/失败 | 重试一次；仍失败则尝试 vxtwitter.com 替代端点：`curl -sL "https://vxtwitter.com/<screen_name>/status/<tweet_id>"`。如果替代端点也失败，用浏览器打开 fxtwitter.com 页面提取内容。**不要直接访问 x.com** |
| 推文已被删除/不存在 | 告知用户"该推文可能已被删除或不可访问" |
| 内容过长（>30,000 词） | 分段创建文档，使用 append 模式 |
| fxtwitter 返回 rate limit | 等待后重试，或告知用户稍后再试 |

## 反模式

| 反模式 | 为什么不行 |
|--------|-----------|
| 用浏览器直接爬 x.com | X 对 headless 浏览器有反爬，大概率超时或被墙 |
| 用 web_search 搜推文 | 搜索引擎索引不了具体推文内容 |
| 跳过翻译步骤 | 英文内容直接创建文档，对中文用户可读性差 |
| 不解析 inlineStyleRanges | 丢失原文的加粗、斜体等格式 |
| 翻译代码块和技术术语 | 代码和专有名词不应翻译 |
| 不添加原文链接 | 用户需要溯源 |

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
英文？──→ 是 → 加载 miaoda-translate 翻译
    │         否 → 保留原文
    ▼
构建飞书 Markdown（元信息 + 正文 + 格式增强）
    │
    ▼
feishu_create_doc 创建文档
    │
    ▼
返回文档链接 + 摘要
```
