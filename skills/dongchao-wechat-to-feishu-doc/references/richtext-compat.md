# 富文本兼容规则

## 识别优先级

1. 先保护代码和图形，再处理普通 Markdown。
2. 优先生成飞书 Docx XML；Markdown 直传只作为回退路径。
3. 遇到疑似代码、命令、YAML、目录树、ASCII 流程图时，使用 `<pre>`，不要使用 Markdown 反引号。
4. 只有真实文章章节进入大纲；示例内部标题放进 `<pre>` 或加粗。
5. 外部工具 `wechat-article-to-markdown` 产出的标准 fenced code block 也要转换成 `<pre>`，因为飞书导入时反引号围栏容易被拆成普通段落。
6. 本地图片不能直接依赖 Markdown 相对路径导入；先生成 `__WECHAT_IMAGE_###__` 占位点和 manifest，创建文档后再把本地图片插回原位置。

## 应转为 `<pre>` 的信号

- 代码：`public class`、`public ...(`、`func `、`package `、`import `、`def `、`return `、`#!/bin/bash`
- 命令：`go test`、`go build`、`go vet`、`grep -rn`、`curl `、`mkdir -p`、`touch `
- YAML：`---`、`name:`、`description:`、`metadata:`、`version:`
- 目录树：`├──`、`└──`、`│`、`scripts/`、`references/`
- 流程图：`↓`、`▼`、`┌`、`└`、`Step 1`、`Step 2`

## 推荐结构

示例块：

```xml
<h3>示例 1：安全漏洞（严重问题）</h3>
<p><b>输入</b>：</p>
<pre lang="java"><code>...</code></pre>
<p><b>输出</b>：</p>
<ul><li>...</li></ul>
```

流程图：

```xml
<p><b>决策流程图</b>：</p>
<pre><code>输入：...
├─ 是 → ...
└─ 否 → ...</code></pre>
```

目录结构：

```xml
<pre><code>my-skill/
├── SKILL.md
└── scripts/</code></pre>
```

## 验证清单

- outline 中只有真实章节，没有代码注释标题。
- 关键词回读中，代码和流程图以 `<pre>` 出现。
- 图片数量与原文抽取结果大体一致。
- 表格仍为表格，不是普通段落。
- 外部工具本地化的 `images/` 相对路径仍在 manifest 中，并在飞书里被替换成真实图片块。
- 文档中不残留 `__WECHAT_IMAGE_###__` 图片占位点。
- 文末有 `（AI生成）`。
