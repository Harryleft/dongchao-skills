#!/usr/bin/env python3
"""Unit tests for parse-tweet.py — X/Twitter JSON → Markdown converter."""

import json
import subprocess
import sys
import os

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "parse-tweet.py")

def run_parse(data: dict) -> str:
    """Run parse-tweet.py with given data, return stdout."""
    proc = subprocess.run(
        [sys.executable, SCRIPT],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 0, f"parse-tweet.py failed: {proc.stderr}"
    return proc.stdout


def test_basic_tweet():
    """Regular tweet with text only."""
    data = {
        "tweet": {
            "text": "Hello world!",
            "author": {"name": "Test User", "screen_name": "testuser"},
            "likes": 100,
            "retweets": 50,
            "bookmarks": 20,
            "views": 5000,
            "created_at": "2026-05-20T00:00:00Z",
        }
    }
    md = run_parse(data)
    assert "Test User" in md
    assert "@testuser" in md
    assert "Hello world!" in md
    assert "100" in md  # likes
    print("✅ test_basic_tweet passed")


def test_article_tweet():
    """Tweet with Article (long-form content)."""
    data = {
        "tweet": {
            "text": "",
            "author": {"name": "Author", "screen_name": "author1"},
            "article": {
                "title": "My Article",
                "content": {
                    "blocks": [
                        {"type": "unstyled", "text": "First paragraph."},
                        {"type": "header-two", "text": "Section Title"},
                        {"type": "unordered-list-item", "text": "Bullet point"},
                        {"type": "ordered-list-item", "text": "Numbered item"},
                    ],
                    "entityMap": {},
                },
            },
            "created_at": "2026-05-20T00:00:00Z",
        }
    }
    md = run_parse(data)
    assert "## Section Title" in md
    assert "- Bullet point" in md
    assert "1. Numbered item" in md
    assert "First paragraph." in md
    print("✅ test_article_tweet passed")


def test_inline_styles():
    """Bold and italic inline styles."""
    data = {
        "tweet": {
            "text": "Bold and italic",
            "author": {"name": "A", "screen_name": "a"},
            "article": {
                "content": {
                    "blocks": [
                        {
                            "type": "unstyled",
                            "text": "This is bold and italic text",
                            "inlineStyleRanges": [
                                {"offset": 8, "length": 4, "style": "Bold"},
                                {"offset": 17, "length": 6, "style": "Italic"},
                            ],
                        }
                    ],
                    "entityMap": {},
                }
            },
        }
    }
    md = run_parse(data)
    assert "**bold**" in md.lower() or "**Bold**" in md
    assert "*italic*" in md.lower() or "*Italic*" in md
    print("✅ test_inline_styles passed")


def test_empty_tweet():
    """Tweet with minimal data."""
    data = {"tweet": {"author": {"name": "Min", "screen_name": "min"}}}
    md = run_parse(data)
    assert "Min" in md
    assert "@min" in md
    print("✅ test_empty_tweet passed")


def test_date_formatting():
    """Date is properly formatted."""
    data = {
        "tweet": {
            "text": "test",
            "author": {"name": "D", "screen_name": "d"},
            "created_at": "2026-01-15T08:30:00Z",
        }
    }
    md = run_parse(data)
    assert "2026-01-15" in md
    print("✅ test_date_formatting passed")


if __name__ == "__main__":
    test_basic_tweet()
    test_article_tweet()
    test_inline_styles()
    test_empty_tweet()
    test_date_formatting()
    print("\n🎉 All 5 unit tests passed!")
