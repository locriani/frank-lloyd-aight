#!/usr/bin/env python3
"""Deny a Write or Edit that breaks a line inside prose or caps the width of text.

The renderer lays text out, never the file. Zach, 2026-10-05: "you are not a word wrapping engine", and of a page capped at 860 pixels and 65 characters: "also page width caps. Yeah no".
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

WRAP = "line break inside prose; a paragraph or list item is one line and the renderer wraps it"
CAP = "width cap; text runs the width of the window, so remove it"

QUOTE = re.compile(r"^\s{0,3}(?:>\s?)+")
# What opens a block that keeps its own lines: a code fence, or a math fence alone on its line. A comment left open is the third (see _opens).
FENCE = re.compile(r"\s*(`{3,}|~{3,}|\$\$(?=\s*$))")
COMMENT = "<!--"
BREAKS = ("  ", "\\", "<br>", "<br/>", "<br />")
# ponytail: any line indented four or more is read as code, so a wrap inside a nested list item is missed; parse list depth if that shows up.
INDENT = re.compile(r"(?: {4}|\t)")
# A line nothing can run on from: blank, a heading, a table row, markup, a reference definition, an alert marker, a rule.
# ponytail: any line holding a pipe is read as a table row, so a wrap in prose that has a pipe in it is missed.
_CLOSED = r"#{1,6}\s|[^|\n]*\||<|\[[^\]]+\]:\s|\[![A-Za-z]+\]\s*$|(?:[-*_=]\s*){3,}$|$"
CLOSED = re.compile(rf"\s*(?:{_CLOSED})")
# A line that starts its own block, so it never continues the line above.
STARTS = re.compile(rf"\s*(?:{_CLOSED}|[-*+]\s|\d+[.)]\s)")
# ponytail: every absolute max-width is a cap, an image's or a tooltip's included; scope it by selector if one of those is ever wanted.
CAPPED = re.compile(
    r"(?<![-\w])(?:max-(?:width|inline-size)\s*:\s*[^;}\n\"']*?\d(?:px|ch|r?em|ex|pt)\b|(?:width|inline-size)\s*:\s*[^;}\n\"']*?\dch\b)",
    re.I,
)


def _opens(line: str) -> str | None:
    """The marker of the verbatim block this line opens, if it opens one."""
    mark = FENCE.match(line)
    if mark:
        return mark[1]
    return COMMENT if line.lstrip().startswith(COMMENT) and "-->" not in line else None


def _closes(line: str, block: str) -> bool:
    """A fence closes on a line that is only its own character, at least as long as it opened; a comment on its end mark."""
    if block == COMMENT:
        return "-->" in line
    run = line.strip()
    return len(run) >= len(block) and run == block[0] * len(run)


def markdown(text: str) -> list[tuple[int, str]]:
    out, block, prev, quoted = [], None, "", False
    rows = text.split("\n")
    # Front matter is closed by a second rule; a leading rule with none after it is only a rule.
    front = rows[0].strip() == "---" and any(row.strip() == "---" for row in rows[1:])
    for n, raw in enumerate(rows, 1):
        if front:
            front = n == 1 or raw.strip() != "---"
            continue
        line = QUOTE.sub("", raw)
        # A quote that starts under an unquoted line is a new block, not that line's continuation.
        was, quoted = quoted, line != raw
        if quoted and not was:
            prev = ""
        if block:
            block = None if _closes(line, block) else block
            continue
        block = _opens(line)
        if block:
            prev = ""
            continue
        code = INDENT.match(line)
        if prev and not code and not STARTS.match(line) and not prev.endswith(BREAKS):
            out.append((n, WRAP))
        prev = "" if code or CLOSED.match(line) else line
    return out


class _Text(HTMLParser):
    """Text nodes that carry a line break between words. Code, scripts, styles and drawings keep their own lines."""

    KEEP = {"pre", "script", "style", "textarea", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self.keep, self.out = 0, []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.keep += tag in self.KEEP

    def handle_endtag(self, tag: str) -> None:
        self.keep -= tag in self.KEEP and self.keep > 0

    def handle_data(self, data: str) -> None:
        # ponytail: a break that falls right beside an inline tag is its own text node and is missed.
        body = data.strip()
        if not self.keep and "\n" in body:
            lead = len(data) - len(data.lstrip())
            self.out.append((self.getpos()[0] + data[: lead + body.index("\n") + 1].count("\n"), WRAP))


def html(text: str) -> list[tuple[int, str]]:
    parser = _Text()
    parser.feed(text)
    parser.close()
    return parser.out


# Not declarations: a drawing's own size and label widths, a comment, and the condition of an at-rule such as a breakpoint.
SVG = re.compile(r"<svg\b.*?</svg>", re.I | re.S)
SKIPPED = (
    SVG,
    re.compile(r"/\*.*?\*/", re.S),
    re.compile(r"@(?:media|container|supports|import)\b[^{;]*", re.I),
    re.compile(r"\[[^\]\n]*\]"),  # an attribute selector's value is not a declaration
    re.compile(r"calc\([^()]*%[^()]*\)", re.I),  # a width worked out from a percentage follows the window
)
# Where a page holds CSS: a style element's body, or the value of a style attribute inside a real tag.
STYLED = re.compile(r"<style\b[^>]*>(.*?)</style>|<[a-z][^<>]*?\sstyle\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", re.I | re.S)


def _blank(m: re.Match) -> str:
    """The match as spaces, its line breaks kept, so every line number after it stays right."""
    return re.sub(r"[^\n]", " ", m[0])


def caps(text: str) -> list[tuple[int, str]]:
    """Width caps in CSS text."""
    for skip in SKIPPED:
        text = skip.sub(_blank, text)
    return [(text.count("\n", 0, m.start()) + 1, CAP) for m in CAPPED.finditer(text)]


def html_caps(text: str) -> list[tuple[int, str]]:
    """Width caps in a page's CSS only; a cap named in its prose is not one."""
    text = SVG.sub(_blank, text)
    kept = list(re.sub(r"[^\n]", " ", text))
    for m in STYLED.finditer(text):
        a, b = m.span(m.lastindex)
        kept[a:b] = text[a:b]
        kept[b] = ";"  # one declaration never runs on into the next style
    return caps("".join(kept))


CHECKS = {".md": (markdown,), ".markdown": (markdown,), ".html": (html, html_caps), ".htm": (html, html_caps), ".css": (caps,)}


def problems(name: str, text: str) -> list[tuple[int, str]]:
    """Each (line, what is wrong) in a file of this name; nothing for a file that is not prose or a page."""
    return sorted(found for check in CHECKS.get(Path(name).suffix.lower(), ()) for found in check(text))


def written(event: dict) -> tuple[str, str, set[int] | None]:
    """The file's path, its text as the call would leave it, and the lines the call writes (None: all of them)."""
    args = event.get("tool_input") or {}
    path = args.get("file_path") or ""
    if event.get("tool_name") == "Write":
        return path, args.get("content") or "", None
    old, new = args.get("old_string") or "", args.get("new_string") or ""
    try:
        before = Path(path).read_text()
    except (OSError, UnicodeDecodeError):
        before = ""
    if not old or old not in before:
        return path, new, None
    parts = before.split(old) if args.get("replace_all") else before.split(old, 1)
    after, lines = parts[0], set()
    for part in parts[1:]:
        first = after.count("\n") + 1
        lines.update(range(first, first + new.rstrip("\n").count("\n") + 1))
        after += new + part
    return path, after, lines


def main() -> int:
    try:
        event = json.load(sys.stdin)
        if event.get("tool_name") not in ("Write", "Edit"):
            return 0
        path, text, lines = written(event)
        # A wrap is named on the line that continues, so the line after the edit answers for a wrap. A cap answers only where it was written.
        found = [(n, why) for n, why in problems(path, text) if lines is None or n in lines or (why == WRAP and n - 1 in lines)]
    except (ValueError, TypeError, AttributeError, OSError):
        return 0
    if found:
        reason = "; ".join(f"{path}:{n} {why}" for n, why in found[:5])
        more = f"; and {len(found) - 5} more" if len(found) > 5 else ""
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason + more,
        }}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
