---
name: dongchao-wechat-to-feishu-doc
description: "Convert WeChat Official Account / mp.weixin.qq.com articles into Feishu cloud documents while preserving readable structure, images, tables, code blocks, ASCII flowcharts, examples, and headings. Use when the user provides a WeChat article URL or saved WeChat HTML and asks to create, import, format, optimize, or repair a Feishu Docx version."
depends-on:
  - wechat-article-to-markdown
  - dongchao-feishu-publish
---

# 微信文章转飞书云文档

把微信公众号文章转换为飞书云文档时，优先交付可阅读、可协作的飞书 Docx，而不是追求逐像素还原微信样式。核心目标是：正文不丢、图片表格不丢、代码不散、流程图不碎、大纲不乱。抓取结果必须先落到本地并完成格式优化，再写入飞书。

本 Skill 不重新实现公众号抓取。抓取和原始 Markdown 生成优先复用成熟开源工具 `wechat-article-to-markdown`；本 Skill 负责把它产出的 Markdown 在本地做一次 AI 格式质检和修复，生成飞书更稳定的 Docx XML，再创建、覆盖、回读验证飞书云文档。文档创建后的归档、权限和群发统一交给 `dongchao-feishu-publish`。

## 工作流

1. **抓取原文并生成基础 Markdown**
   - 首选 `wechat-article-to-markdown "https://mp.weixin.qq.com/s/..."`。
   - 若命令不存在，优先用 `uv tool install wechat-article-to-markdown` 安装；没有 `uv` 时用 `pipx install wechat-article-to-markdown`。
   - 该工具通常会输出 `output/<文章标题>/<文章标题>.md` 和 `images/`，保留本地化图片、元数据和微信 `code-snippet` 代码块。
   - 抓取结果必须保存到工作区临时目录，例如 `tmp/wechat_articles/<slug>/`，不要直接边抓边写飞书。
   - 如果 DNS、包下载、浏览器内核或微信抓取失败，按网络/依赖问题处理并重试；不要误判为文章内容不可转换。
   - 只有在外部工具不可用或用户已经提供 HTML 时，才回退到浏览器 UA 抓取 HTML 并保存到工作区临时目录。

2. **本地生成 Feishu XML 草稿**
   - 若已有外部工具产出的 Markdown，优先运行 `scripts/wechat_markdown_to_feishu_xml.py --markdown input.md --out article.xml --manifest image_manifest.json`。
   - 若只有 HTML，先运行 `scripts/wechat_html_to_feishu_markdown.py --html article.html --source-url URL --out article.md`，再转 XML。
   - 对代码、流程图、目录树、命令、YAML、Few-Shot 示例输入，一律生成 `<pre><code>...</code></pre>`，不要依赖 Markdown 反引号围栏。
   - 外部工具已下载到本地的图片要保留相对路径；XML 脚本会为本地图片生成 `__WECHAT_IMAGE_###__` 占位点和 manifest，后续用于把图片插回原位置。
   - 详细兼容规则见 `references/richtext-compat.md`。

3. **本地 AI 格式质检与修复**
   - 写飞书前必须打开生成的 XML 做一次本地检查，重点看文章后半部分，因为代码块、项目列表和流程图最容易在后半段散掉。
   - 检查脚本输出的统计值：`pre`、`img`、`image_markers`、`table`、`ul`、`ol`。如果 `pre=0` 但文章含代码/流程图，或列表/表格数量明显异常，先修 XML 或转换规则。
   - 抽查关键词：`public User getUser`、`HTTP 客户端迁移流程`、`project-migration`、`效果评估报告` 等技术文章常见片段，确认它们在 `<pre>`、`<ul>/<ol>` 或 `<table>` 中，而不是普通段落。
   - 只有本地 XML 通过质检后，才允许写入飞书。

4. **创建或更新飞书文档**
   - 使用 `lark-cli docs +create --api-version v2 --as user --doc-format xml --content @relative/path.xml` 创建。
   - 若修复已有文档，使用 `docs +update --command overwrite --doc-format xml --content @relative/path.xml`。
   - 若飞书元标题是 `Untitled`，先 `drive +inspect`，再用 `drive files patch` 的 `new_title` 修正。
   - 如果 XML 里有本地图片占位点，创建后用 manifest 逐张 `docs +media-insert --file <path>` 上传，移动到对应 `__WECHAT_IMAGE_###__` 占位点后，再删除占位点。

5. **回读验证**
   - `docs +fetch --scope outline --max-depth 3` 检查大纲。
   - 用关键词检查示例、代码块、流程图、文末标记是否存在。
   - 如果使用了图片占位点，回读确认占位点已删除、图片已在对应段落附近出现。
   - 看到代码、流程图、目录结构散成普通段落时，回到转换稿修规则后重导。

6. **发布后治理**
   - 文档格式验证通过后，调用 `dongchao-feishu-publish`。
   - 传入文档标题、最终 `doc_url` 和用户提供的发布配置。
   - 发布配置至少包含：归档父节点、归档章节、管理者、通知群聊。缺失时先询问用户，不要使用历史运行中的内部链接、open_id 或 chat_id。
   - `dongchao-feishu-publish` 负责移动到知识库、写入指定章节、设置可读权限、授予指定管理者权限、发送指定群聊消息和最终验证。
   - 如果用户只是要求本地转换或只修复已有文档格式，不要自动执行发布后治理。

## 富文本兼容原则

- 微信文章是视觉富文本；飞书 Markdown 是语义文本。不要把微信 `<section><span>` 的视觉换行直接当语义结构。
- 普通段落、标题、表格、引用可转 Markdown。
- 代码块、命令、YAML、目录树、ASCII 图、流程图、Few-Shot 示例输入代码必须转飞书 XML `<pre>`。
- 只让真实文章章节进入大纲；示例里的 `# Before`、`## 目标`、`### Step` 放入 `<pre>` 或降级为加粗文本。
- 自动生成的飞书文档末尾保留 `（AI生成）`。

## 常见修复

- **示例碎片化**：把 `示例 / 1 / ：标题 / 输入 / 代码 / 输出` 重建为 `### 示例 1：标题`、`**输入**`、代码块、`**输出**`、列表。
- **代码散行**：连续出现 `public class`、`func`、`import`、`#!/bin/bash`、`go test`、`curl`、`name: ... description: >` 等信号时合并为 `<pre>`。
- **流程图碎裂**：连续出现 `↓`、`┌`、`├`、`└`、`Step 1` 等信号时整体合并为 `<pre>`。
- **大纲污染**：回读 outline 后，如果出现 `# Before`、`# 核心配置文件`、`# 确认 Skill...` 等标题，说明代码或注释没有被包进 `<pre>`。

## 脚本使用

外部工具抓取后，先生成本地 XML 草稿和图片 manifest：

```bash
wechat-article-to-markdown "https://mp.weixin.qq.com/s/..."

python3 .codex/skills/dongchao-wechat-to-feishu-doc/scripts/wechat_markdown_to_feishu_xml.py \
  --markdown "output/<文章标题>/<文章标题>.md" \
  --source-url 'https://mp.weixin.qq.com/s/...' \
  --out tmp/wechat_article_import/article.xml \
  --manifest tmp/wechat_article_import/image_manifest.json
```

HTML 回退路径：

```bash
python3 .codex/skills/dongchao-wechat-to-feishu-doc/scripts/wechat_html_to_feishu_markdown.py \
  --html tmp/wechat_article_import/article.html \
  --source-url 'https://mp.weixin.qq.com/s/...' \
  --out tmp/wechat_article_import/article.md

python3 .codex/skills/dongchao-wechat-to-feishu-doc/scripts/wechat_markdown_to_feishu_xml.py \
  --markdown tmp/wechat_article_import/article.md \
  --source-url 'https://mp.weixin.qq.com/s/...' \
  --out tmp/wechat_article_import/article.xml \
  --manifest tmp/wechat_article_import/image_manifest.json
```

`wechat_markdown_to_feishu_xml.py` 负责生成“更适合飞书导入”的 XML 草稿；AI 必须在本地检查并必要时修复 XML，再写入飞书。创建、覆盖由本 Skill 执行；归档、权限、群发等发布后治理动作统一由 `dongchao-feishu-publish` 执行。
