#!/usr/bin/env python3
"""parse-tweet.py — Parse fxtwitter JSON into Lark-flavored Markdown.

Usage: parse-tweet.py < input.json > output.md
       parse-tweet.py input.json

Reads fxtwitter API JSON from stdin or file, outputs Markdown suitable
for feishu_create_doc.
"""

import json
import sys
from datetime import datetime, timezone


def parse_inline_styles(text: str, ranges: list) -> str:
    """Apply inline style ranges (Bold/Italic) to text."""
    if not ranges:
        return text

    # Sort ranges by start position, descending (apply from end to preserve offsets)
    sorted_ranges = sorted(ranges, key=lambda r: r.get("offset", 0), reverse=True)

    for r in sorted_ranges:
        offset = r.get("offset", 0)
        length = r.get("length", 0)
        style = r.get("style", "")

        if offset + length > len(text):
            continue

        segment = text[offset:offset + length]
        replacement = segment

        if style == "Bold":
            replacement = f"**{segment}**"
        elif style == "Italic":
            replacement = f"*{segment}*"

        text = text[:offset] + replacement + text[offset + length:]

    return text


def parse_entity_links(text: str, entity_ranges: list, entity_map: dict) -> str:
    """Apply entity ranges (LINK) to text."""
    if not entity_ranges or not entity_map:
        return text

    sorted_ranges = sorted(entity_ranges, key=lambda r: r.get("offset", 0), reverse=True)

    for r in sorted_ranges:
        offset = r.get("offset", 0)
        length = r.get("length", 0)
        key = str(r.get("key", ""))

        entity = entity_map.get(key, {})
        if entity.get("type") != "LINK":
            continue

        url = entity.get("url", "")
        if offset + length > len(text):
            continue

        segment = text[offset:offset + length]
        replacement = f"[{segment}]({url})"
        text = text[:offset] + replacement + text[offset + length:]

    return text


def parse_article(article: dict) -> str:
    """Parse X Article blocks into Markdown."""
    blocks = article.get("content", {}).get("blocks", [])
    entity_map = article.get("content", {}).get("entityMap", {})
    lines = []

    for block in blocks:
        block_type = block.get("type", "unstyled")
        text = block.get("text", "")
        inline_styles = block.get("inlineStyleRanges", [])
        entity_ranges = block.get("entityRanges", [])

        # Apply inline styles first, then entity links
        text = parse_inline_styles(text, inline_styles)
        text = parse_entity_links(text, entity_ranges, entity_map)

        if block_type == "header-two":
            lines.append(f"## {text}")
        elif block_type == "header-three":
            lines.append(f"### {text}")
        elif block_type == "unordered-list-item":
            lines.append(f"- {text}")
        elif block_type == "ordered-list-item":
            lines.append(f"1. {text}")
        elif block_type == "atomic":
            # Media block - extract image URL from entity map
            for er in entity_ranges:
                key = str(er.get("key", ""))
                entity = entity_map.get(key, {})
                if entity.get("type") == "IMAGE":
                    url = entity.get("url", entity.get("src", ""))
                    if url:
                        lines.append(f'<image url="{url}" />')
        else:  # unstyled and others
            if text:
                lines.append(text)

    return "\n\n".join(lines)


def format_date(date_str: str) -> str:
    """Parse and localize date string."""
    try:
        # fxtwitter returns ISO format
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return date_str


def build_markdown(data: dict) -> str:
    """Build complete Markdown document from fxtwitter response."""
    tweet = data.get("tweet", {})
    author = tweet.get("author", {})
    article = tweet.get("article")

    # Metadata header
    parts = []
    parts.append(f'**作者：** {author.get("name", "Unknown")}（@{author.get("screen_name", "")}）')

    original_url = ""
    if tweet.get("url"):
        original_url = tweet["url"]
    elif author.get("screen_name") and tweet.get("id"):
        original_url = f'https://x.com/{author["screen_name"]}/status/{tweet["id"]}'

    if original_url:
        parts.append(f"**原文链接：** [{original_url}]({original_url})")

    created_at = tweet.get("created_at", "")
    if created_at:
        parts.append(f"**发布时间：** {format_date(created_at)}")

    # Engagement metrics
    metrics = []
    if tweet.get("likes") is not None:
        metrics.append(f'{tweet["likes"]:,} 赞')
    if tweet.get("retweets") is not None:
        metrics.append(f'{tweet["retweets"]:,} 转')
    if tweet.get("bookmarks") is not None:
        metrics.append(f'{tweet["bookmarks"]:,} 收藏')
    if tweet.get("views") is not None:
        metrics.append(f'{tweet["views"]:,} 浏览')
    if metrics:
        parts.append(f'**互动数据：** {" · ".join(metrics)}')

    parts.append("---")

    # Body content
    if article:
        parts.append(parse_article(article))
    else:
        # Regular tweet
        body = tweet.get("text", "")
        if body:
            parts.append(body)

        # Append media images
        media = tweet.get("media", {})
        if media:
            all_media = media.get("all", [])
            for m in all_media:
                if m.get("type") == "photo":
                    url = m.get("url", "")
                    if url:
                        parts.append(f'<image url="{url}" />')

    return "\n\n".join(parts)


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    md = build_markdown(data)
    print(md)


if __name__ == "__main__":
    main()
