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

# A quote marker sits at most three spaces in; a tab or four spaces before it make the line code.
QUOTE = re.compile(r"^ {0,3}(?:>[ \t]?)+")
# What opens a verbatim block, which keeps its own lines: a code fence, a math fence alone on its line, or a comment left open.
MATH, COMMENT = "$$", "<!--"
FENCE = re.compile(r"\s*(`{3,}|~{3,}|\$\$(?=\s*$))")
OPEN_COMMENT = re.compile(r" {0,3}<!--(?!.*-->)")
FRONT_END = ("---", "...")
BREAK_TAGS = ("<br>", "<br/>", "<br />")
# ponytail: a line indented four or more under a blank line is read as code, so a wrap inside a nested list item is missed; parse list depth if that shows up.
INDENT = re.compile(r"(?: {4}|\t)")
# A line nothing can run on from: blank, a heading, a table row, markup, a reference definition, an alert marker, a rule.
# ponytail: any line holding a pipe is read as a table row, so a wrap in prose that has a pipe in it is missed.
_CLOSED = r"#{1,6}\s|\||[^\s|][^|]*\||<|\[[^\]]+\]:\s|\[![A-Za-z]+\]\s*$|(?:[-*_=]\s*){3,}$|$"
CLOSED = re.compile(rf"\s*(?:{_CLOSED})")
# A line that starts its own block, so it never continues the line above.
# A quote marker here is one QUOTE did not reach: a quote inside a list item.
STARTS = re.compile(rf"\s*(?:{_CLOSED}|[-*+]\s|\d+[.)]\s|>)")
# ponytail: every absolute max-width is a cap, an image's or a tooltip's included; scope it by selector if one of those is ever wanted.
CAPPED = re.compile(
    r"(?<![-\w])(?:max-(?:width|inline-size)\s*:\s*[^;:}\n\"']*?\d(?:px|ch|r?em|ex|pt)\b|(?:width|inline-size)\s*:\s*[^;:}\n\"']*?\dch\b)",
    re.I,
)


def _opens(line: str) -> str | None:
    """The marker of the verbatim block this line opens, if it opens one."""
    mark = FENCE.match(line)
    if mark:
        return mark[1]
    return COMMENT if OPEN_COMMENT.match(line) else None


def _ends(line: str, verbatim: str) -> bool:
    """A comment ends on its end mark, math on its fence or a blank line, a code fence on a run of its own character at least as long."""
    run = line.strip()
    if verbatim == COMMENT:
        return "-->" in line
    if verbatim == MATH:
        return run in ("", MATH)
    return len(run) >= len(verbatim) and run == verbatim[0] * len(run)


def _breaks(line: str) -> bool:
    """The line ends in a break the author asked for."""
    return line.endswith(("  ", "\\")) or line.rstrip().lower().endswith(BREAK_TAGS)


def markdown(text: str) -> list[tuple[int, str]]:
    out, verbatim, prev, quoted = [], None, "", False
    rows = text.split("\n")
    # Front matter is closed by a second rule or three dots; a leading rule with neither after it is only a rule.
    front = rows[0].strip() == "---" and any(row.strip() in FRONT_END for row in rows[1:])
    for n, raw in enumerate(rows, 1):
        if front:
            front = n == 1 or raw.strip() not in FRONT_END
            continue
        line = QUOTE.sub("", raw)
        # A quote that starts under an unquoted line is a new block, not that line's continuation.
        was, quoted = quoted, line != raw
        if quoted and not was:
            prev = ""
        if verbatim:
            verbatim = None if _ends(line, verbatim) else verbatim
            continue
        verbatim = _opens(line)
        if verbatim:
            prev = ""
            continue
        # Code cannot interrupt a paragraph: an indented line under prose is that prose continued.
        code = not prev and INDENT.match(line)
        if prev and not STARTS.match(line) and not _breaks(prev):
            out.append((n, WRAP))
        prev = "" if code or CLOSED.match(line) else line
    return out


STYLE_ATTR = re.compile(r"\sstyle\s*=\s*", re.I)


class _Page(HTMLParser):
    """A page's wrapped text nodes and the width caps in its CSS. Code, scripts, styles and drawings keep their own lines, and a drawing its own sizes."""

    KEEP = {"pre", "script", "style", "textarea", "svg"}

    def __init__(self) -> None:
        super().__init__()
        self.keep, self.svg, self.css, self.out = 0, 0, False, []

    def _caps(self, css: str, line: int) -> None:
        if not self.svg:
            self.out += [(line + n - 1, why) for n, why in caps(css)]

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.keep += tag in self.KEEP
        self.svg += tag == "svg"
        self.css = tag == "style"
        style = dict(attrs).get("style")
        if style:
            # The value arrives unescaped, so its line is found by the attribute's name, not its text.
            raw = self.get_starttag_text() or ""
            at = STYLE_ATTR.search(raw)
            self._caps(style, self.getpos()[0] + raw.count("\n", 0, at.end() if at else 0))

    def handle_endtag(self, tag: str) -> None:
        self.keep -= tag in self.KEEP and self.keep > 0
        self.svg -= tag == "svg" and self.svg > 0
        self.css = False

    def handle_data(self, data: str) -> None:
        if self.css:
            self._caps(data, self.getpos()[0])
        # ponytail: a break that falls right beside an inline tag is its own text node and is missed.
        body = data.strip()
        if not self.keep and "\n" in body:
            lead = len(data) - len(data.lstrip())
            self.out.append((self.getpos()[0] + data[: lead + body.index("\n") + 1].count("\n"), WRAP))


def html(text: str) -> list[tuple[int, str]]:
    parser = _Page()
    parser.feed(text)
    parser.close()
    return parser.out


# Not declarations: a comment, the condition of an at-rule such as a breakpoint, and an attribute selector, which never holds a brace.
SKIPPED = (
    re.compile(r"/\*.*?\*/", re.S),
    re.compile(r"@(?:media|container|supports|import)\b[^{;]*", re.I),
    re.compile(r"\[[^\]\[\n{};]*\]"),
)
# ponytail: a calc() with any percentage in it is read as following the window, so calc(600px + 0%) is missed.
CALC = re.compile(r"calc\((?:[^();{}]|\([^();{}]*\))*\)", re.I)


def _blank(m: re.Match) -> str:
    """The match as spaces, its line breaks kept, so every line number after it stays right."""
    return re.sub(r"[^\n]", " ", m[0])


def caps(text: str) -> list[tuple[int, str]]:
    """Width caps in CSS text."""
    for skip in SKIPPED:
        text = skip.sub(_blank, text)
    text = CALC.sub(lambda m: _blank(m) if "%" in m[0] else m[0], text)
    return [(text.count("\n", 0, m.start()) + 1, CAP) for m in CAPPED.finditer(text)]


CHECKS = {".md": (markdown,), ".markdown": (markdown,), ".html": (html,), ".htm": (html,), ".css": (caps,)}


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
