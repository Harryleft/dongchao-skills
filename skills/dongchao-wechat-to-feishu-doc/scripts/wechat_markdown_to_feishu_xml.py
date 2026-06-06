#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from html import escape
from pathlib import Path


def inline(text: str) -> str:
    text = escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = escape(match.group(2), quote=True)
        return f'<a href="{href}">{label}</a>'

    return re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link, text)


def pre(lang: str, body: str) -> str:
    lang_attr = f' lang="{escape(lang, quote=True)}"' if lang else ""
    return f"<pre{lang_attr}><code>{escape(body.strip(), quote=False)}</code></pre>"


def table_block(lines: list[str]) -> str:
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    if len(rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in rows[1]):
        header, body = rows[0], rows[2:]
    else:
        header, body = rows[0], rows[1:]
    width = max(len(row) for row in rows)
    header = header + [""] * (width - len(header))
    thead = "<thead><tr>" + "".join(f"<th>{inline(cell)}</th>" for cell in header) + "</tr></thead>"
    body_xml = []
    for row in body:
        row = row + [""] * (width - len(row))
        body_xml.append("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>")
    return "<table>" + thead + "<tbody>" + "".join(body_xml) + "</tbody></table>"


def list_block(lines: list[str], ordered: bool = False) -> str:
    tag = "ol" if ordered else "ul"
    items = []
    for line in lines:
        item = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", line).strip()
        seq = ' seq="auto"' if ordered else ""
        items.append(f"<li{seq}>{inline(item)}</li>")
    return f"<{tag}>" + "".join(items) + f"</{tag}>"


def quote_block(lines: list[str]) -> str:
    body = "<br/>".join(inline(re.sub(r"^>\s?", "", line).strip()) for line in lines)
    return f"<blockquote><p>{body}</p></blockquote>"


def looks_like_code(lines: list[str], broad: bool = True) -> bool:
    sample = "\n".join(line for line in lines if line.strip())
    stripped = "\n".join(line.strip() for line in lines if line.strip())
    code_signal = bool(
        re.search(
            r"(^|\n)\s*(--- |\+\+\+ |@@ |package |import |func |def |class |public |private |protected |return |name:|description:|metadata:|mkdir |go test|go build|curl |grep |python |#!/|┌|├|└|│|↓|Step \d|[0-9]+\. 确认|try:|except |for |if |echo |\{|\}|\"mcpServers\")",
            sample,
        )
        or bool(re.search(r"(^|\n)\s*(func |def |import |package |return |#!/|┌|├|└|│|↓|Step \d)", stripped))
    )
    if broad:
        code_signal = code_signal or bool(re.search(r"(^|\n)\s*#{1,6} ", sample))
    return code_signal


def paragraph(lines: list[str]) -> str:
    if len([line for line in lines if line.strip()]) > 1 and looks_like_code(lines, broad=False):
        return pre("", "\n".join(lines))
    body = "<br/>".join(inline(line.strip()) for line in lines if line.strip())
    return f"<p>{body}</p>" if body else ""


def allowed_heading(level: int, text: str) -> bool:
    plain = re.sub(r"<[^>]+>", "", text).strip()
    if level == 1:
        return True
    if plain == "阅读建议":
        return True
    if re.match(r"^[一二三四五六七八九十]+、", plain):
        return True
    if re.match(r"^\d+\.\d+", plain):
        return True
    if re.match(r"^示例\s*\d+", plain):
        return True
    if re.match(r"^方案\s*[A-Z]", plain):
        return True
    if plain.startswith("Q:"):
        return True
    if plain.startswith("反模式"):
        return True
    if plain.startswith("附录"):
        return True
    if plain in {
        "审查报告格式",
        "反模式速查表",
        "写的内容对不对",
        "结构合不合理",
        "工程结构合不合理",
        "安全过关了吗",
        "可维护性够好吗",
    }:
        return True
    return False


def clean_title(text: str) -> str:
    return text.replace("（AI生成）", "").strip()


def image_block(
    href: str,
    image_base: Path,
    image_items: list[dict[str, str]],
    local_image_mode: str,
) -> str:
    if href.startswith(("http://", "https://")):
        return f'<img href="{escape(href, quote=True)}"/>'

    path = (image_base / href).resolve() if not Path(href).is_absolute() else Path(href).resolve()
    marker = f"__WECHAT_IMAGE_{len(image_items) + 1:03d}__"
    image_items.append({"marker": marker, "source": href, "path": str(path)})

    if local_image_mode == "href":
        return f'<img href="{escape(str(path), quote=True)}"/>'
    return f"<p><code>{marker}</code></p>"


def convert_lines(lines: list[str], image_base: Path, local_image_mode: str) -> tuple[list[str], list[dict[str, str]]]:
    out: list[str] = []
    buf: list[str] = []
    image_items: list[dict[str, str]] = []
    i = 0

    def flush_paragraph() -> None:
        nonlocal buf
        if buf:
            block = paragraph(buf)
            if block:
                out.append(block)
            buf = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        fence = re.match(r"^```([A-Za-z0-9_+.#-]*)\s*$", stripped)
        if fence:
            flush_paragraph()
            lang = fence.group(1)
            chunk: list[str] = []
            nested = 0
            nested_seen = False
            i += 1
            while i < len(lines):
                inner_open = re.match(r"^```([A-Za-z0-9_+.#-]+)\s*$", lines[i].strip())
                inner_close = lines[i].strip() == "```"
                if not lang and inner_open:
                    nested += 1
                    nested_seen = True
                    chunk.append(lines[i])
                    i += 1
                    continue
                if inner_close:
                    if not lang and nested > 0:
                        nested -= 1
                        chunk.append(lines[i])
                        i += 1
                        continue
                    break
                chunk.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            if not lang and not nested_seen and not looks_like_code(chunk, broad=True):
                nested_blocks, nested_images = convert_lines(chunk, image_base, local_image_mode)
                out.extend(nested_blocks)
                image_items.extend(nested_images)
            else:
                out.append(pre(lang, "\n".join(chunk)))
            continue

        image = re.match(r"^!\[[^\]]*\]\(([^)]+)\)$", stripped)
        if image:
            flush_paragraph()
            out.append(image_block(image.group(1), image_base, image_items, local_image_mode))
            i += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            text = inline(heading.group(2).strip())
            if level == 1:
                text = clean_title(text)
                out.append(f"<title>{text}</title>")
                out.append(f"<h1>{text}</h1>")
            elif allowed_heading(level, text):
                plain = re.sub(r"<[^>]+>", "", text).strip()
                if plain == "阅读建议" or re.match(r"^[一二三四五六七八九十]+、", plain):
                    level = 2
                elif re.match(r"^\d+\.\d+", plain):
                    level = 3
                elif re.match(r"^示例\s*\d+", plain):
                    level = 3
                elif re.match(r"^方案\s*[A-Z]", plain):
                    level = 3
                elif plain.startswith(("Q:", "反模式", "附录")):
                    level = 3
                out.append(f"<h{level}>{text}</h{level}>")
            else:
                out.append(f"<p><b>{text}</b></p>")
            i += 1
            continue

        if stripped == "---":
            flush_paragraph()
            out.append("<hr/>")
            i += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i])
                i += 1
            out.append(table_block(table_lines))
            continue

        if re.match(r"^\s*[-*]\s+", line):
            flush_paragraph()
            list_lines = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                list_lines.append(lines[i])
                i += 1
            out.append(list_block(list_lines))
            continue

        if re.match(r"^\s*\d+[.)]\s+", line):
            flush_paragraph()
            list_lines = []
            while i < len(lines) and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                list_lines.append(lines[i])
                i += 1
            out.append(list_block(list_lines, ordered=True))
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i])
                i += 1
            out.append(quote_block(quote_lines))
            continue

        buf.append(line)
        i += 1

    flush_paragraph()
    return out, image_items


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--manifest")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--local-image-mode", choices=["marker", "href"], default="marker")
    args = parser.parse_args()

    markdown_path = Path(args.markdown)
    raw = markdown_path.read_text(encoding="utf-8")
    blocks, image_items = convert_lines(raw.splitlines(), markdown_path.parent, args.local_image_mode)

    if args.source_url and args.source_url not in raw:
        insert_at = 2 if len(blocks) >= 2 and blocks[0].startswith("<title>") else 0
        blocks.insert(insert_at, f"<p>原文链接：<a href=\"{escape(args.source_url, quote=True)}\">{escape(args.source_url, quote=False)}</a></p>")

    body = "\n\n".join(blocks).strip()
    if "（AI生成）" not in body:
        body += "\n\n<p>（AI生成）</p>"

    Path(args.out).write_text(body + "\n", encoding="utf-8")
    if args.manifest:
        manifest = {"markdown": str(markdown_path), "xml": args.out, "images": image_items}
        Path(args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"wrote={args.out}")
    print(
        "stats="
        f"pre:{body.count('<pre')} "
        f"img:{body.count('<img')} "
        f"image_markers:{body.count('__WECHAT_IMAGE_')} "
        f"table:{body.count('<table')} "
        f"ul:{body.count('<ul>')} "
        f"ol:{body.count('<ol>')}"
    )
    if args.manifest:
        print(f"manifest={args.manifest}")


if __name__ == "__main__":
    main()
