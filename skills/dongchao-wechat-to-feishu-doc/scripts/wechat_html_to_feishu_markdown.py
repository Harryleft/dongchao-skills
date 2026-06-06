#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path


class Node:
    def __init__(self, tag="root", attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = []
        self.parent = parent


class Parser(HTMLParser):
    void_tags = {"br", "img", "meta", "link", "input", "hr"}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node()
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag.lower(), attrs, self.current)
        self.current.children.append(node)
        if node.tag not in self.void_tags:
            self.current = node

    def handle_endtag(self, tag):
        tag = tag.lower()
        cur = self.current
        while cur.parent is not None:
            if cur.tag == tag:
                self.current = cur.parent
                return
            cur = cur.parent

    def handle_data(self, data):
        if data:
            self.current.children.append(data)

    def handle_entityref(self, name):
        self.current.children.append(unescape(f"&{name};"))

    def handle_charref(self, name):
        self.current.children.append(unescape(f"&#{name};"))


def find_by_attr(node, key, value):
    if isinstance(node, Node):
        if node.attrs.get(key) == value:
            return node
        for child in node.children:
            found = find_by_attr(child, key, value)
            if found:
                return found
    return None


def text_of(node):
    if isinstance(node, str):
        return node
    return "".join(text_of(c) for c in node.children)


def clean_space(text):
    text = re.sub(r"[\u200b\ufeff]", "", text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    return text.strip()


def image_src(node):
    for key in ("data-src", "src", "data-backsrc"):
        src = node.attrs.get(key)
        if src:
            return ("https:" + src if src.startswith("//") else src).replace("&amp;", "&")
    return ""


def pre(lang, body):
    lang_attr = f' lang="{escape(lang, quote=True)}"' if lang else ""
    return f"<pre{lang_attr}><code>{escape(body.strip(), quote=False)}</code></pre>"


def inline_md(node):
    if isinstance(node, str):
        return clean_space(unescape(node)).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
    if node.tag == "br":
        return "\n"
    if node.tag == "img":
        src = image_src(node)
        return f"\n\n![]({src})\n\n" if src else ""
    body = clean_space("".join(inline_md(c) for c in node.children))
    if not body:
        return ""
    if node.tag in {"strong", "b"}:
        return f"**{body}**"
    if node.tag in {"em", "i"}:
        return f"*{body}*"
    if node.tag == "a" and node.attrs.get("href"):
        return f"[{body}]({node.attrs['href']})"
    return body


def iter_tags(node, tag):
    if isinstance(node, Node):
        if node.tag == tag:
            yield node
        for child in node.children:
            yield from iter_tags(child, tag)


def render_table(node):
    rows = []
    for tr in iter_tags(node, "tr"):
        row = []
        for child in tr.children:
            if isinstance(child, Node) and child.tag in {"td", "th"}:
                row.append(clean_space(inline_md(child)).replace("\n", " ") or " ")
        if row:
            rows.append(row)
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    lines.extend("| " + " | ".join(r) + " |" for r in rows[1:])
    return ["\n".join(lines)]


def has_block_child(node):
    return any(isinstance(c, Node) and c.tag in {"p", "section", "div", "blockquote", "table", "ul", "ol", "li"} for c in node.children)


def render_blocks(node):
    if isinstance(node, str):
        text = clean_space(node)
        return [text] if text else []
    if node.tag == "img":
        src = image_src(node)
        return [f"![]({src})"] if src else []
    if node.tag == "table":
        return render_table(node)
    if node.tag == "blockquote":
        inner = "\n\n".join(render_children(node)) or inline_md(node)
        return ["\n".join("> " + line for line in inner.splitlines())] if inner else []
    if node.tag in {"h1", "h2", "h3", "h4"}:
        text = clean_space(inline_md(node))
        level = {"h1": 2, "h2": 3, "h3": 4, "h4": 4}[node.tag]
        return [("#" * level) + " " + text] if text else []
    if node.tag in {"p", "section", "div", "li"}:
        if has_block_child(node):
            return render_children(node)
        text = clean_space(inline_md(node))
        if not text:
            return []
        return [f"- {text}" if node.tag == "li" else text]
    return render_children(node)


def render_children(node):
    out = []
    for child in node.children:
        out.extend(render_blocks(child))
    return [b for b in (clean_space(x) for x in out) if b]


def normalize_headings(blocks):
    out = []
    for block in blocks:
        if block.startswith("#### "):
            text = block[5:].strip()
            if text == "阅读建议" or re.match(r"^[一二三四五六七八九十]+、", text):
                out.append("## " + text)
            elif re.match(r"^\d+\.\d+", text):
                out.append("### " + text)
            else:
                out.append("### " + text)
        else:
            out.append(block)
    return out


def protect_obvious_code(blocks):
    out = []
    i = 0
    code_re = re.compile(r"^(public |private |protected |class |func |def |package |import |return |#!/|go test|go build|go vet|grep -rn|curl |mkdir -p|touch |name:|description:|metadata:|version:|├|└|│|↓|▼|┌|Step [0-9])")
    while i < len(blocks):
        if code_re.search(blocks[i]):
            chunk = [blocks[i]]
            i += 1
            while i < len(blocks) and not blocks[i].lstrip().startswith("![") and (code_re.search(blocks[i]) or len(chunk) < 4 and blocks[i] not in {"**输出**：", "**输入**："}):
                chunk.append(blocks[i])
                i += 1
            out.append(pre("", "\n".join(chunk)))
        else:
            out.append(blocks[i])
            i += 1
    return out


def normalize_markdown_for_feishu(raw):
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")

    body = convert_fences_for_feishu(raw).strip()
    if "（AI生成）" not in body:
        body = body.rstrip() + "\n\n（AI生成）"
    return body + "\n"


def looks_like_unlabeled_code(lines):
    sample = [line.strip() for line in lines if line.strip()][:4]
    if not sample:
        return False
    joined = "\n".join(sample)
    return bool(
        re.search(
            r"^(# |---$|--- |[+]{3} |@@ |package |import |func |def |class |public |private |protected |return |name:|description:|metadata:|mkdir |go test|curl |grep |#!/|┌|├|└|│|↓)",
            joined,
            re.M,
        )
    )


def convert_fences_for_feishu(raw):
    lines = raw.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"^(```|~~~)([A-Za-z0-9_+.#-]*)[ \t]*$", line.strip())
        if not match:
            out.append(line)
            i += 1
            continue

        fence, lang = match.group(1), match.group(2).strip()
        if not lang:
            lookahead = []
            j = i + 1
            while j < len(lines) and len(lookahead) < 8:
                if lines[j].strip():
                    lookahead.append(lines[j])
                j += 1
            if not looks_like_unlabeled_code(lookahead):
                i += 1
                continue

        chunk = []
        i += 1
        while i < len(lines) and lines[i].strip() != fence:
            chunk.append(lines[i])
            i += 1
        if i < len(lines) and lines[i].strip() == fence:
            i += 1
        out.extend(["", pre(lang, "\n".join(chunk)), ""])
    return "\n".join(out)


def extract_title(raw):
    match = re.search(r"var msg_title\s*=\s*'([^']*)'", raw)
    return clean_space(unescape(match.group(1))) if match else "微信文章"


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--html")
    source.add_argument("--markdown")
    parser.add_argument("--out", required=True)
    parser.add_argument("--source-url", default="")
    args = parser.parse_args()

    if args.markdown:
        raw = Path(args.markdown).read_text(encoding="utf-8")
        body = normalize_markdown_for_feishu(raw)
        if args.source_url and args.source_url not in body:
            lines = body.splitlines()
            insert_at = 1 if lines and lines[0].startswith("# ") else 0
            lines[insert_at:insert_at] = ["", f"原文链接：{args.source_url}"]
            body = "\n".join(lines).strip() + "\n"
        Path(args.out).write_text(body, encoding="utf-8")
        print(f"wrote={args.out}")
        print(f"images={body.count('![](')} pre={body.count('<pre')}")
        return

    raw = Path(args.html).read_text(encoding="utf-8")
    html_parser = Parser()
    html_parser.feed(raw)
    content = find_by_attr(html_parser.root, "id", "js_content")
    if content is None:
        raise SystemExit("未找到微信正文容器 js_content")

    title = extract_title(raw)
    blocks = protect_obvious_code(normalize_headings(render_children(content)))
    header = [f"# {title}"]
    if args.source_url:
        header.extend(["", f"原文链接：{args.source_url}"])
    body = "\n\n".join(header + [""] + blocks + ["", "（AI生成）"]).strip() + "\n"
    Path(args.out).write_text(body, encoding="utf-8")
    print(f"wrote={args.out}")
    print(f"title={title}")
    print(f"images={body.count('![](')} pre={body.count('<pre')}")


if __name__ == "__main__":
    main()
