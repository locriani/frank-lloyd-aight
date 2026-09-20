"""Eval runner for the frank-lloyd-aight agent (Frank Lloyd AIght). Copied from chief-of-stuff and stripped.

`claude plugin eval` cannot run a case under `--agent`, so this drives `claude -p` directly.
Grader vocabulary follows `plugin eval` where it overlaps (`tool_used`, `regex`) so cases can
be ported later.

    python3 evals/run.py --arm baseline --case stale-clock        # model defaults to opus
    python3 evals/run.py --arm both --case stale-clock            # both arms, plus a per-grader table
    python3 evals/run.py --regrade <run-dir>                      # today's graders, yesterday's run
    python3 evals/run.py --compare <baseline-dir> <agent-dir>     # the table, from runs on disk

A case with no `--case` glob runs every case, which on `--arm agent --model opus` is the whole
suite at Opus prices. Name the case.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import queue
import tempfile
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from datetime import time as dtime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

EVALS = Path(__file__).resolve().parent
PLUGIN_ROOT = EVALS.parent
AGENT = "frank-lloyd-aight"
# Opus only (Zach, 2026-09-16). A run whose init reports another model family fails the arm check.
DEFAULT_MODEL = "opus"

# Isolation: `--setting-sources project` drops user settings (and with them user plugins and
# permission rules) but still loads the fixture CLAUDE.md. `--restricted` was probed and skips
# project CLAUDE.md, which is the config channel under test, so it is not used.
# AskUserQuestion is host-answered under --permission-prompt-tool stdio (see drive_turns); no Agent, the reviewer dispatches through peers.
TOOLS = ["Bash", "Read", "Glob", "Grep", "Write", "Edit", "AskUserQuestion"]
# Writes only where a review lives: plans, review pages, and the architecture directory. Anything else prompts the host, which denies and records it.
# The renderer is the one script it may run; the path is whatever the fixture CLAUDE.md names, so only the basename is pinned.
ALLOWED = [
    "Bash(date:*)", "Bash(TZ=*)", "Bash(python3 *mermaid-check.py:*)",
    "Read", "Glob", "Grep",
    "Edit(./plans/**)", "Edit(./reviews/**)", "Edit(./architecture/**)",
    "Write(./plans/**)", "Write(./reviews/**)", "Write(./architecture/**)",
]
DISALLOWED = ["Bash(git commit:*)", "Bash(git add:*)", "Bash(git push:*)", "Bash(rm:*)", "Bash(rmdir:*)"]
# These reach real Claude sessions on this machine. No eval run may expose them.
PEER_TOOLS = ("ListAgents", "SendMessage")
MOCK_BOARD = EVALS / "mock_board.py"
BOARD_TOOL = "mcp__board__publish"
# The peers mock stands in for ListAgents/SendMessage, which stay out of every run (PEER_TOOLS guard).
MOCK_PEERS = EVALS / "mock_peers.py"
PEER_MOCK_TOOLS = ["mcp__peers__list_sessions", "mcp__peers__send"]

# `{{name}}`, or `{{now+Nh}}` / `{{now-Nh|local}}` / `{{now+Nh|hhmm}}` for times relative to render time.
TOKEN = re.compile(r"\{\{\s*([a-z_]+)(?:([+-]\d+)h)?(?:\|([a-z]+))?\s*\}\}")
NOW_FORMATS = {"local": "%Y-%m-%d %H:%M", "hhmm": "%H:%M"}


# --- stream -----------------------------------------------------------------------------------


@dataclass
class Stream:
    init: dict[str, Any] = field(default_factory=dict)
    tool_uses: list[dict[str, Any]] = field(default_factory=list)
    denied_ids: set[str] = field(default_factory=set)
    last_text: str = ""
    result: dict[str, Any] | None = None


def load_stream(path: Path) -> Stream:
    return parse_stream([json.loads(raw) for raw in path.read_text().splitlines() if raw.strip()])


def parse_stream(events: list[dict[str, Any]]) -> Stream:
    s = Stream()
    for ev in events:
        kind = ev.get("type")
        if kind == "system" and ev.get("subtype") == "init":
            s.init = ev
        elif kind == "assistant":
            for block in ev["message"]["content"]:
                if block.get("type") == "tool_use":
                    s.tool_uses.append({"id": block["id"], "name": block["name"], "input": block.get("input", {})})
                elif block.get("type") == "text" and block.get("text", "").strip():
                    s.last_text = block["text"]
        elif kind == "result":
            s.result = ev
            s.denied_ids = {d["tool_use_id"] for d in ev.get("permission_denials", [])}
    return s


def check_arm(init: dict[str, Any], arm: str, agent_flag_used: bool = False, model: str | None = None, needs_board: bool = False, needs_peers: bool = False) -> tuple[bool, str]:
    """Confirm the session loaded what the arm claims, so a silent fallback cannot pass."""
    exposed = [t for t in PEER_TOOLS if t in init.get("tools", [])]
    if exposed:
        return False, f"sandbox exposes peer-session tools {exposed}"
    if model and model.lower() not in str(init.get("model", "")).lower():
        return False, f"init model {init.get('model')!r} is not {model!r}"
    if needs_board:
        servers = {m.get("name"): m.get("status") for m in init.get("mcp_servers", [])}
        if servers.get("board") != "connected":
            return False, f"mock board not connected: {servers}"
    if needs_peers:
        servers = {m.get("name"): m.get("status") for m in init.get("mcp_servers", [])}
        if servers.get("peers") != "connected":
            return False, f"mock peers not connected: {servers}"
    agents = init.get("agents", [])
    present = any(a == AGENT or a.endswith(":" + AGENT) for a in agents)
    if arm == "agent":
        return (True, "agent loaded") if present else (False, f"{AGENT} not in init agents {agents}")
    if arm == "baseline":
        return (False, "baseline ran with --agent") if agent_flag_used else (True, "no --agent")
    raise ValueError(f"unknown arm {arm!r}")


# --- fixtures ---------------------------------------------------------------------------------


def context(tz: str, now: datetime) -> dict[str, str]:
    local = now.astimezone(ZoneInfo(tz))
    day = timedelta(days=1)
    return {
        "today": local.date().isoformat(),
        "yesterday": (local.date() - day).isoformat(),
        "tomorrow": (local.date() + day).isoformat(),
        "tz": tz,
        "now_hhmm": local.strftime("%H:%M"),
        "now_iso": local.replace(second=0, microsecond=0).isoformat(),
        # Fixtures cannot hold a real `.git/`; a file under `{{dotgit}}/` renders as one.
        "dotgit": ".git",
    }


def render(text: str, ctx: dict[str, str]) -> str:
    def token(m: re.Match[str]) -> str:
        name, offset, fmt = m.groups()
        if offset is None and fmt is None:
            return ctx[name]
        if name != "now":
            raise KeyError(f"offset or format only allowed on now: {m.group(0)}")
        when = datetime.fromisoformat(ctx["now_iso"]) + timedelta(hours=int(offset or 0))
        if fmt is None:
            return when.isoformat()
        if fmt not in NOW_FORMATS:
            raise KeyError(f"unknown now format {fmt!r}")
        return when.strftime(NOW_FORMATS[fmt])

    return TOKEN.sub(token, text)


def render_value(value: Any, ctx: dict[str, str]) -> Any:
    if isinstance(value, str):
        return render(value, ctx)
    if isinstance(value, list):
        return [render_value(v, ctx) for v in value]
    if isinstance(value, dict):
        return {k: render_value(v, ctx) for k, v in value.items()}
    return value


def init_repo(work: Path) -> str:
    """Commit the rendered fixture and return the base sha. A fixture cannot carry a real `.git`
    (which is why `{{dotgit}}` exists), so a case that owns a document gets its repo here.
    The identity is generic: fixtures carry no data from any workspace that uses this agent."""
    def git(*args: str, **kw: Any) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(work), *args], check=True, capture_output=True, text=True, **kw)

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Eval Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("add", "-A")
    git("commit", "-q", "-m", "fixture")
    return git("rev-parse", "HEAD").stdout.strip()


def tree_digest(root: Path) -> str:
    """Content hash of a fixture tree: every relative path and its bytes, `.git` excluded.

    Digest the case's *source* fixture, never the rendered copy -- rendering substitutes
    `{{today}}`, so a rendered tree hashes differently tomorrow for no reason that matters.
    """
    h = hashlib.sha256()
    for f in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts):
        h.update(str(f.relative_to(root)).encode())
        h.update(b"\0")
        h.update(f.read_bytes())
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


def render_tree(src: Path, dst: Path, ctx: dict[str, str]) -> None:
    for path in sorted(src.rglob("*")):
        rel = Path(render(str(path.relative_to(src)), ctx))
        out = dst / rel
        if path.is_dir():
            out.mkdir(parents=True, exist_ok=True)
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(path.read_text(), ctx))


# --- graders ----------------------------------------------------------------------------------


@dataclass
class RunRecord:
    stream: Stream
    t_start: datetime
    t_end: datetime
    tz: str
    fixture_dir: Path
    mock_calls: list[dict[str, Any]] = field(default_factory=list)
    before_dir: Path | None = None
    git_base: str | None = None

    @property
    def publishes(self) -> list[dict[str, Any]]:
        return [c for c in self.mock_calls if c.get("tool") == "publish"]

    @property
    def peer_calls(self) -> list[dict[str, Any]]:
        return [c for c in self.mock_calls if c.get("tool") in ("list_sessions", "send")]

    @property
    def questions(self) -> list[dict[str, Any]]:
        return [c for c in self.mock_calls if c.get("tool") == "AskUserQuestion"]


def grade(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    kind = g.get("type")
    if kind == "tool_used":
        return _tool_used(g, rec)
    if kind == "regex":
        return _regex(g, rec)
    if kind in FILE_GRADERS:
        return FILE_GRADERS[kind](g, rec)
    if kind in BOARD_GRADERS:
        return BOARD_GRADERS[kind](g, rec)
    if kind in COORDINATION_GRADERS:
        return COORDINATION_GRADERS[kind](g, rec)
    raise ValueError(f"unknown grader type {kind!r}")


def _tool_used(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    name = re.compile(rf"(?:{g['tool']})")
    match = re.compile(g["input_match"]) if "input_match" in g else None
    hits = [
        t
        for t in rec.stream.tool_uses
        if name.fullmatch(t["name"]) and (match is None or match.search(json.dumps(t["input"])))
    ]
    denied = sum(1 for t in hits if t["id"] in rec.stream.denied_ids)
    lo, hi = g.get("min", 0), g.get("max")
    ok = len(hits) >= lo and (hi is None or len(hits) <= hi)
    bound = f"min {lo}" + (f", max {hi}" if hi is not None else "")
    return ok, f"{len(hits)} call(s) ({denied} denied); want {bound}"


def _regex(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    found = re.search(g["pattern"], rec.stream.last_text, re.MULTILINE) is not None
    mode = g.get("match", "contains")
    ok = found if mode == "contains" else not found
    return ok, f"/{g['pattern']}/ {'found' if found else 'not found'}; want {mode}"


def _read(root: Path | None, rel: str) -> str | None:
    path = root / rel if root else None
    return path.read_text() if path and path.is_file() else None


def _file_unchanged(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    before, after = _read(rec.before_dir, g["path"]), _read(rec.fixture_dir, g["path"])
    if before == after:
        return True, f"{g['path']} unchanged"
    state = "created" if before is None else "deleted" if after is None else "modified"
    return False, f"{g['path']} {state}"


def _file_matches(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    text = _read(rec.fixture_dir, g["path"])
    if text is None:
        return False, f"{g['path']} missing"
    if "count" in g:
        n = len(re.findall(g["pattern"], text, re.MULTILINE))
        return n == g["count"], f"{g['path']}: /{g['pattern']}/ matches {n} time(s); want {g['count']}"
    found = re.search(g["pattern"], text, re.MULTILINE) is not None
    mode = g.get("match", "contains")
    ok = found if mode == "contains" else not found
    return ok, f"{g['path']}: /{g['pattern']}/ {'found' if found else 'not found'}; want {mode}"


def _files(root: Path | None) -> set[str]:
    """Everything under `.git/` is git's bookkeeping, not a file the agent created."""
    if not (root and root.is_dir()):
        return set()
    rels = (f.relative_to(root) for f in root.rglob("*") if f.is_file())
    return {str(r) for r in rels if ".git" not in r.parts}


def _files_created(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    """Files present after the turn and absent before it, matching `glob`; bounded by `min`/`max`."""
    new = sorted(f for f in _files(rec.fixture_dir) - _files(rec.before_dir) if fnmatch.fnmatch(f, g["glob"]))
    lo, hi = g.get("min", 0), g.get("max")
    ok = len(new) >= lo and (hi is None or len(new) <= hi)
    bound = f"min {lo}" + (f", max {hi}" if hi is not None else "")
    return ok, f"{len(new)} new file(s) matching {g['glob']!r}: {new}; want {bound}"


def _no_new_files(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    """`except` entries are exact paths or globs (`Resources/**`)."""
    allowed = [str(e) for e in g.get("except", [])]
    new = sorted(f for f in _files(rec.fixture_dir) - _files(rec.before_dir) if not any(fnmatch.fnmatch(f, e) for e in allowed))
    return (not new), (f"new files: {new}" if new else "no new files")


def _section(text: str, heading: str) -> list[str] | None:
    """Non-blank lines under `heading`, up to the next heading of the same or higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == heading.strip():
            body = []
            for nxt in lines[i + 1 :]:
                hashes = len(nxt) - len(nxt.lstrip("#"))
                if hashes and hashes <= level and nxt[hashes : hashes + 1] == " ":
                    break
                if nxt.strip():
                    body.append(nxt.rstrip())
            return body
    return None


def _lines_preserved(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    """Every line of the original section appears, in order, in the result's section (append-only)."""
    before = _section(_read(rec.before_dir, g["path"]) or "", g["section"])
    after = _section(_read(rec.fixture_dir, g["path"]) or "", g["section"])
    if before is None or after is None:
        return False, f"{g['path']}: section {g['section']!r} missing ({'before' if before is None else 'after'})"
    it = iter(after)
    lost = [line for line in before if not any(line == candidate for candidate in it)]
    if lost:
        return False, f"{g['path']} {g['section']}: lost or reordered {lost}"
    added = len(after) - len(before)
    want = g.get("min_added", 0)
    return added >= want, f"{g['path']} {g['section']}: preserved, {added} line(s) added; want >= {want}"


def _committed(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    """Commits the agent added on top of the fixture's base, with an optional message match.
    The other file graders see that a document changed; only this one sees that it was committed."""
    if rec.git_base is None:
        return False, "case does not set \"git\": true"
    log = subprocess.run(
        ["git", "-C", str(rec.fixture_dir), "log", "--format=%s", f"{rec.git_base}..HEAD"],
        capture_output=True, text=True,
    )
    if log.returncode != 0:
        return False, f"git log failed: {log.stderr.strip()}"
    subjects = [l for l in log.stdout.splitlines() if l.strip()]
    if "message_match" in g:
        subjects = [s for s in subjects if re.search(g["message_match"], s)]
    lo, hi = g.get("min", 0), g.get("max")
    ok = len(subjects) >= lo and (hi is None or len(subjects) <= hi)
    bound = f"min {lo}" + (f", max {hi}" if hi is not None else "")
    match = f" matching /{g['message_match']}/" if "message_match" in g else ""
    return ok, f"{len(subjects)} commit(s){match}: {subjects}; want {bound}"


FILE_GRADERS = {
    "committed": _committed,
    "file_unchanged": _file_unchanged,
    "file_matches": _file_matches,
    "no_new_files": _no_new_files,
    "files_created": _files_created,
    "lines_preserved": _lines_preserved,
}


# --- invocation -------------------------------------------------------------------------------


@dataclass
class Case:
    name: str
    root: Path
    spec: dict[str, Any]


def load_cases(patterns: list[str]) -> list[Case]:
    cases = []
    for spec_path in sorted((EVALS / "cases").glob("*/case.json")):
        name = spec_path.parent.name
        if patterns and not any(fnmatch.fnmatch(name, p) for p in patterns):
            continue
        cases.append(Case(name, spec_path.parent, json.loads(spec_path.read_text())))
    return cases


def _last_published_html(rec: RunRecord) -> tuple[str | None, str]:
    pubs = rec.publishes
    if not pubs:
        return None, "no publish in this turn"
    stored = Path(pubs[-1].get("stored", ""))
    if not stored.is_file():
        return None, f"stored copy missing: {stored}"
    return stored.read_text(), f"{len(pubs)} publish(es), last {pubs[-1].get('url')}"


def _published(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    """Between `min` and `max` publishes this turn; the last published page contains every
    `content_match` regex and none of `content_not_match`."""
    lo, hi = g.get("min", 1), g.get("max")
    count = len(rec.publishes)
    if count < lo or (hi is not None and count > hi):
        bound = f"min {lo}" + (f", max {hi}" if hi is not None else "")
        return False, f"{count} publish(es); want {bound}"
    if count == 0:
        return True, "no publish, none required"
    page, note = _last_published_html(rec)
    if page is None:
        return False, note
    problems = [f"/{pat}/ not in page" for pat in g.get("content_match", []) if not re.search(pat, page, re.MULTILINE)]
    problems += [f"/{pat}/ found in page" for pat in g.get("content_not_match", []) if re.search(pat, page, re.MULTILINE)]
    return (not problems), ("; ".join(problems) if problems else note)


BOARD_GRADERS = {
    "published": _published,
}


def _peer_calls(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    """Count this turn's calls to the peers mock that match every filter given."""
    calls = [c for c in rec.peer_calls if c.get("tool") == g["tool"]]
    if "to_ref" in g:
        calls = [c for c in calls if c.get("to_ref") == g["to_ref"]]
    if "ok" in g:
        calls = [c for c in calls if bool(c.get("ok")) == bool(g["ok"])]
    if "text_match" in g:
        calls = [c for c in calls if re.search(g["text_match"], c.get("text", ""))]
    if "text_not_match" in g:
        calls = [c for c in calls if not re.search(g["text_not_match"], c.get("text", ""))]
    lo, hi = g.get("min", 0), g.get("max")
    ok = len(calls) >= lo and (hi is None or len(calls) <= hi)
    bound = f"min {lo}" + (f", max {hi}" if hi is not None else "")
    return ok, f"{len(calls)} call(s) match; want {bound}"


def _question_asked(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    """Count this turn's host-answered AskUserQuestion calls where some question matches every filter:
    `question_match` on the question text, `first_option_match` on the first option's label and
    description (the recommended option goes first), and at most `options_max` options (default 4)."""
    cap = g.get("options_max", 4)

    def fits(q: dict[str, Any]) -> bool:
        options = q.get("options", [])
        if "question_match" in g and not re.search(g["question_match"], q.get("question", "")):
            return False
        if len(options) > cap:
            return False
        if "first_option_match" in g:
            first = options[0] if options else {}
            if not re.search(g["first_option_match"], f"{first.get('label', '')} {first.get('description', '')}"):
                return False
        return True

    calls = [c for c in rec.questions if any(fits(q) for q in c.get("questions", []))]
    lo, hi = g.get("min", 0), g.get("max")
    ok = len(calls) >= lo and (hi is None or len(calls) <= hi)
    bound = f"min {lo}" + (f", max {hi}" if hi is not None else "")
    return ok, f"{len(calls)} question call(s) match of {len(rec.questions)}; want {bound}"


def _reply_lines(g: dict[str, Any], rec: RunRecord) -> tuple[bool, str]:
    n = len([l for l in rec.stream.last_text.splitlines() if l.strip()])
    return n <= g["max"], f"{n} non-empty line(s); want <= {g['max']}"


COORDINATION_GRADERS = {
    "peer_calls": _peer_calls,
    "reply_lines": _reply_lines,
    "question_asked": _question_asked,
}


def peers_mcp_config(sessions: Path, log: Path, tz: str) -> dict[str, Any]:
    args = [str(MOCK_PEERS.resolve()), "--sessions", str(sessions), "--log", str(log), "--tz", tz]
    return {"mcpServers": {"peers": {"type": "stdio", "command": sys.executable, "args": args}}}


def board_mcp_config(log: Path, store: Path, root: Path, tz: str, known_url: str | None) -> dict[str, Any]:
    args = [str(MOCK_BOARD.resolve()), "--log", str(log), "--store", str(store), "--root", str(root), "--tz", tz]
    if known_url:
        args += ["--known-url", known_url]
    return {"mcpServers": {"board": {"type": "stdio", "command": sys.executable, "args": args}}}


def merge_mcp(*configs: dict[str, Any] | None) -> dict[str, Any] | None:
    servers: dict[str, Any] = {}
    for c in configs:
        if c:
            servers.update(c.get("mcpServers", {}))
    return {"mcpServers": servers} if servers else None


def command(case: Case, arm: str, model: str, mcp_config: dict[str, Any] | None = None) -> list[str]:
    """User turns arrive as stream-json on stdin; permission prompts go to the harness (`stdio`), which answers or denies them."""
    mcp_config = mcp_config or {"mcpServers": {}}
    # A case may widen its own sandbox; the default is untouched, so the cases already green keep
    # the guarantees their stored reds were measured against.
    sandbox = case.spec.get("sandbox") or {}
    allowed = ALLOWED + list(sandbox.get("allow", [])) + ([BOARD_TOOL] if "board" in mcp_config["mcpServers"] else []) + (PEER_MOCK_TOOLS if "peers" in mcp_config["mcpServers"] else [])
    disallowed = list(sandbox.get("deny", DISALLOWED))
    cmd = [
        "claude", "-p",
        "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--no-session-persistence",
        "--setting-sources", "project",
        "--plugin-dir", str(PLUGIN_ROOT),
        "--strict-mcp-config", "--mcp-config", json.dumps(mcp_config),
        "--max-turns", str(case.spec.get("max_turns", 10)),
        "--tools", *TOOLS,
        "--allowedTools", *allowed,
        "--disallowedTools", *disallowed,
        "--input-format", "stream-json",
        "--permission-prompt-tool", "stdio",
    ]
    if arm == "agent":
        cmd += ["--agent", AGENT]
    return cmd


@dataclass
class Turn:
    events: list[dict[str, Any]]
    t_start: datetime
    t_end: datetime
    host_denied: set[str] = field(default_factory=set)


def answer_question(tool_input: dict[str, Any], answer: dict[str, Any] | None) -> dict[str, Any]:
    """The host's reply to an AskUserQuestion: per question, the first option whose label matches
    `answer["label_match"]`, else `answer["response"]` as typed text, else the first option, which is
    what a user taking the recommendation would pick."""
    answers: dict[str, str] = {}
    for q in tool_input.get("questions", []):
        options = q.get("options", [])
        pick = None
        if answer and "label_match" in answer:
            pick = next((o["label"] for o in options if re.search(answer["label_match"], o.get("label", ""))), None)
        if pick is None and answer and "response" in answer:
            pick = answer["response"]
        if pick is None and options:
            pick = options[0]["label"]
        if pick is not None:
            answers[q["question"]] = pick
    return dict(tool_input, answers=answers)


def has_notification(events: list[dict[str, Any]]) -> bool:
    """A background task's completion landed in this turn (`system:task_notification`)."""
    return any(e.get("type") == "system" and e.get("subtype") == "task_notification" for e in events)


def split_turns(events: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    turns, current = [], []
    for ev in events:
        current.append(ev)
        if ev.get("type") == "result":
            turns.append(current)
            current = []
    if current:
        turns.append(current)
    return turns


def drive_turns(
    cmd: list[str],
    prompts: list[str | None],
    cwd: Path,
    env: dict[str, str] | None,
    timeout: float,
    snapshot: Callable[[int], None],
    wait_seconds: float = 180,
    before_turn: Callable[[int], None] | None = None,
    close_grace: float = 60,
    answers: list[dict[str, Any] | None] | None = None,
    host_log: Path | None = None,
) -> list[Turn]:
    """Feed each prompt as a stream-json user message; a turn ends at its `result` event.

    A `None` prompt is a wait turn: send nothing and read the turn the session starts on its own
    (a background task's completion notification does this). If the previous turn already carried
    the notification (the task finished before the assistant stopped), there is nothing to wait for
    and the wait turn is skipped. If no event arrives within `wait_seconds`, driving stops there and
    later turns count as not reached. `timeout` bounds the
    whole run and raises `TimeoutError`. After stdin closes, a process still running (a background
    task) is killed after `close_grace`. `snapshot(n)` runs after turn n's result.

    The harness is the permission host (`--permission-prompt-tool stdio`): a `control_request` for
    AskUserQuestion is answered from `answers[n-1]` (see `answer_question`) and logged to `host_log`;
    any other prompted tool is denied, logged as `host_deny`, and its id kept on the turn, because the
    CLI's own `permission_denials` need not list a host denial.
    """
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lines: queue.Queue[str | None] = queue.Queue()

    def pump() -> None:
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=pump, daemon=True).start()
    deadline = time.monotonic() + timeout
    turns: list[Turn] = []
    try:
        for n, prompt in enumerate(prompts, start=1):
            if prompt is None and turns and has_notification(turns[-1].events):
                continue
            if before_turn is not None:
                before_turn(n)
            t_start = datetime.now().astimezone()
            if prompt is not None:
                proc.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": prompt}}) + "\n")
                proc.stdin.flush()
            events: list[dict[str, Any]] = []
            host_denied: set[str] = set()
            eof = False
            while True:
                limit = deadline - time.monotonic()
                if prompt is None and not events:
                    limit = min(limit, wait_seconds)
                if limit <= 0 and deadline - time.monotonic() <= 0:
                    raise TimeoutError(f"turn {n} timed out after {timeout}s")
                try:
                    line = lines.get(timeout=max(limit, 0.01))
                except queue.Empty:
                    if deadline - time.monotonic() <= 0:
                        raise TimeoutError(f"turn {n} timed out after {timeout}s") from None
                    return turns  # wait turn: nothing arrived
                if line is None:
                    eof = True
                    break
                if line.strip():
                    events.append(json.loads(line))
                    if events[-1].get("type") == "control_request":
                        denied = _answer_control_request(proc, events[-1], (answers or [None] * n)[n - 1] if answers and n - 1 < len(answers) else None, host_log)
                        if denied:
                            host_denied.add(denied)
                    if events[-1].get("type") == "result":
                        break
            if events:
                turns.append(Turn(events, t_start, datetime.now().astimezone(), host_denied))
                snapshot(n)
            if eof or events[-1].get("type") != "result":
                break
        proc.stdin.close()
        try:
            proc.wait(timeout=close_grace)
        except subprocess.TimeoutExpired:
            proc.kill()
    finally:
        if proc.poll() is None:
            proc.kill()
    return turns


def _answer_control_request(proc: subprocess.Popen, ev: dict[str, Any], answer: dict[str, Any] | None, host_log: Path | None) -> str | None:
    """Reply to one control_request on stdin. Returns the tool_use_id when the host denied it."""
    req = ev.get("request", {})
    denied = None
    at = datetime.now().astimezone().isoformat()
    if req.get("subtype") == "can_use_tool":
        if req.get("tool_name") == "AskUserQuestion":
            updated = answer_question(req.get("input", {}), answer)
            data: dict[str, Any] = {"behavior": "allow", "updatedInput": updated}
            row = {"tool": "AskUserQuestion", "questions": req.get("input", {}).get("questions", []), "answers": updated.get("answers", {}), "tool_use_id": req.get("tool_use_id"), "at": at}
        else:
            data = {"behavior": "deny", "message": "blocked by eval harness"}
            denied = req.get("tool_use_id")
            row = {"tool": "host_deny", "tool_name": req.get("tool_name"), "input": req.get("input"), "tool_use_id": denied, "at": at}
        if host_log is not None:
            host_log.parent.mkdir(parents=True, exist_ok=True)
            with host_log.open("a") as f:
                f.write(json.dumps(row) + "\n")
    else:
        data = {}
    proc.stdin.write(json.dumps({"type": "control_response", "response": {"subtype": "success", "request_id": ev.get("request_id"), "response": data}}) + "\n")
    proc.stdin.flush()
    return denied


def grade_turns(spec: dict[str, Any], turns: list[Turn], tz: str, out: Path, calls: list[dict[str, Any]], git_base: str | None = None) -> list[tuple[str, bool, str]]:
    """Grade each turn spec against the turn it belongs to.

    A prompt spec takes the next turn. A wait spec (no prompt) takes the turn that carried the
    background notification: the previous turn itself when the notification landed inside it,
    otherwise the next unprompted turn. Specs with no turn grade as "turn not reached".
    """
    results = []
    ti = -1  # index of the last consumed turn
    for n, turn_spec in enumerate(spec["turns"], start=1):
        if "prompt" in turn_spec:
            ti += 1
            turn_index = ti if ti < len(turns) else None
        elif ti >= 0 and has_notification(turns[ti].events):
            turn_index = ti
        elif ti + 1 < len(turns):
            ti += 1
            turn_index = ti
        else:
            turn_index = None
        if turn_index is None:
            results.append((f"T{n}: ran", False, "turn not reached"))
            continue
        turn = turns[turn_index]
        snap = turn_index + 1
        in_turn = [c for c in calls if "at" in c and turn.t_start <= datetime.fromisoformat(c["at"]) <= turn.t_end]
        stream = parse_stream(turn.events)
        stream.denied_ids |= turn.host_denied
        rec = RunRecord(
            stream=stream,
            t_start=turn.t_start,
            t_end=turn.t_end,
            tz=tz,
            fixture_dir=out / f"fixture-turn{snap}",
            mock_calls=in_turn,
            before_dir=out / ("fixture-before" if snap == 1 else f"fixture-turn{snap - 1}"),
            git_base=git_base,
        )
        for i, g in enumerate(turn_spec["graders"]):
            passed, why = grade(g, rec)
            label = g.get("name", f"{i}:{g['type']}")
            results.append((f"T{n}: {label}", passed, why))
    return results


def calls_log_path(out: Path) -> Path:
    """One JSONL log shared by every mock server in a run."""
    return out / "calls" / "calls.jsonl"


@dataclass
class Row:
    """One grader, as the two arms saw it."""
    grader: str
    baseline: bool | None
    agent: bool | None
    verdict: str

    def cell(self, v: bool | None) -> str:
        """`~` covers both a grader that varied across runs and one only a single arm graded;
        the verdict column is what tells those apart."""
        return {True: "PASS", False: "FAIL", None: "~"}[v]


def arm_summary(runs: list[list[tuple[str, bool, str]]]) -> dict[str, bool | None]:
    """Per grader across an arm's runs: True if it passed every time, False if it failed every
    time, None if it varied. A grader that varies has not measured anything yet."""
    summary: dict[str, bool | None] = {}
    for results in runs:
        for name, passed, _ in results:
            if name not in summary:
                summary[name] = passed
            elif summary[name] is not None and summary[name] != passed:
                summary[name] = None
    return summary


def discrimination(baseline: dict[str, bool | None], agent: dict[str, bool | None]) -> list[Row]:
    """What each grader proves about the agent file.

    A red-to-green stage buys `discriminates`. The other verdicts are the ones worth reading:
    `vacuous` is a grader that passes without the agent file and so proves nothing, `regression`
    is the agent file suppressing a capability the model has by default, `unmet` is nobody
    doing it yet.
    """
    rows = []
    for name in list(baseline) + [n for n in agent if n not in baseline]:
        b, a = baseline.get(name, "absent"), agent.get(name, "absent")
        if b == "absent" or a == "absent":
            verdict = "missing"
        elif b is None or a is None:
            verdict = "flaky"
        elif not b and a:
            verdict = "discriminates"
        elif b and a:
            verdict = "vacuous"
        elif b and not a:
            verdict = "regression"
        else:
            verdict = "unmet"
        rows.append(Row(name, None if b == "absent" else b, None if a == "absent" else a, verdict))
    return rows


def discrimination_counts(rows: list[Row]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    return counts


def report_discrimination(rows: list[Row]) -> int:
    """Name the graders a reader has to act on. A regression fails the run; a vacuous grader is a
    warning, because a guard that both arms pass is sometimes deliberate and that call is Zach's."""
    bad = 0
    for r in rows:
        if r.verdict == "regression":
            print(f"  REGRESSION  {r.grader} — baseline passes, the agent file does not")
            bad += 1
        elif r.verdict == "vacuous":
            print(f"  VACUOUS     {r.grader} — passes without the agent file, so it proves nothing")
        elif r.verdict == "flaky":
            print(f"  FLAKY       {r.grader} — differs across runs of one arm")
        elif r.verdict == "missing":
            print(f"  MISSING     {r.grader} — graded on one arm only")
    return 1 if bad else 0


def render_table(rows: list[Row]) -> str:
    width = max([len(r.grader) for r in rows] + [len("grader")])
    out = [f"  {'grader'.ljust(width)}  baseline  agent     verdict",
           f"  {'-' * width}  --------  --------  -------"]
    for r in rows:
        out.append(f"  {r.grader.ljust(width)}  {r.cell(r.baseline):8}  {r.cell(r.agent):8}  {r.verdict}")
    return "\n".join(out)


def compare_runs(baseline_dirs: list[Path], agent_dirs: list[Path], cases_root: Path | None = None, unverified: bool = False) -> tuple[list[Row], str | None]:
    """Build the table from runs already on disk, re-graded under today's graders."""
    graded: dict[str, list[list[tuple[str, bool, str]]]] = {"baseline": [], "agent": []}
    cases = set()
    for arm, dirs in (("baseline", baseline_dirs), ("agent", agent_dirs)):
        for d in dirs:
            results, error = regrade(d, cases_root=cases_root, unverified=unverified)
            if error:
                return [], error
            cases.add(json.loads((d / "meta.json").read_text())["case"] if (d / "meta.json").exists() else d.parent.parent.name)
            graded[arm].append(results)
    if len(cases) > 1:
        return [], f"runs are of different cases: {sorted(cases)}"
    return discrimination(arm_summary(graded["baseline"]), arm_summary(graded["agent"])), None


def run_meta(case: str, arm: str, model: str, git_base: str | None, turns: list[Turn], meta: dict[str, Any], fixture_digest: str | None) -> dict[str, Any]:
    """What a re-grade cannot recover from `stream.jsonl` alone.

    Turn boundaries can be rebuilt from the stream (`split_turns`), but their timestamps cannot,
    and `grade_turns` scopes mock calls to a turn by timestamp. The base sha and the fixture the
    run was measured against are likewise nowhere in the stream.
    """
    return {
        "case": case,
        "arm": arm,
        "model": model,
        "git_base": git_base,
        "fixture_digest": fixture_digest,
        "meta": meta,
        "turns": [
            {"t_start": t.t_start.isoformat(), "t_end": t.t_end.isoformat(), "host_denied": sorted(t.host_denied)}
            for t in turns
        ],
    }


def load_run(run_dir: Path) -> tuple[dict[str, Any], list[Turn], list[dict[str, Any]]]:
    """Rebuild a stored run: its meta, its turns with their real boundaries, and its mock calls."""
    meta = json.loads((run_dir / "meta.json").read_text())
    events = [json.loads(l) for l in (run_dir / "stream.jsonl").read_text().splitlines() if l.strip()]
    grouped = split_turns(events)
    stored = meta["turns"]
    if len(grouped) != len(stored):
        raise ValueError(f"stream holds {len(grouped)} turn(s), meta.json records {len(stored)}")
    turns = [
        Turn(
            events=evs,
            t_start=datetime.fromisoformat(rec["t_start"]),
            t_end=datetime.fromisoformat(rec["t_end"]),
            host_denied=set(rec.get("host_denied", [])),
        )
        for evs, rec in zip(grouped, stored)
    ]
    calls_path = run_dir / "calls" / "calls.jsonl"
    calls = [json.loads(l) for l in calls_path.read_text().splitlines() if l.strip()] if calls_path.exists() else []
    return meta, turns, calls


def reconstruct_run(run_dir: Path) -> tuple[dict[str, Any], list[Turn], list[dict[str, Any]]]:
    """A run captured before `meta.json` existed, recovered as far as it honestly can be.

    Exact only for a single-turn run: one turn holds every event and every logged call, so the
    boundaries that `meta.json` would have carried do not matter. A multi-turn run is refused --
    its per-turn call scoping is unrecoverable, and guessing it would mis-credit calls silently.
    """
    events = [json.loads(l) for l in (run_dir / "stream.jsonl").read_text().splitlines() if l.strip()]
    grouped = split_turns(events)
    if len(grouped) != 1:
        raise ValueError(f"{len(grouped)} turns and no meta.json: per-turn boundaries are unrecoverable")
    calls_path = run_dir / "calls" / "calls.jsonl"
    calls = [json.loads(l) for l in calls_path.read_text().splitlines() if l.strip()] if calls_path.exists() else []
    span = timedelta(days=365)
    now = datetime.now().astimezone()
    turn = Turn(
        events=grouped[0],
        t_start=now - span,
        t_end=now + span,
        host_denied={c["tool_use_id"] for c in calls if c.get("tool") == "host_deny" and c.get("tool_use_id")},
    )
    # results/<stamp>/<case>/<arm>/<n>
    case, arm = run_dir.parent.parent.name, run_dir.parent.name
    snap = run_dir / "fixture-turn1"
    git_base = None
    if (snap / ".git").is_dir():
        root = subprocess.run(["git", "-C", str(snap), "rev-list", "--max-parents=0", "HEAD"],
                              capture_output=True, text=True)
        git_base = root.stdout.split()[0] if root.returncode == 0 and root.stdout.split() else None
    return {"case": case, "arm": arm, "git_base": git_base, "fixture_digest": None, "unverified": True}, [turn], calls


def regrade(run_dir: Path, cases_root: Path | None = None, unverified: bool = False) -> tuple[list[tuple[str, bool, str]], str | None]:
    """Grade a stored run against its case spec **as it stands now**.

    This is verification step 6 -- change a grader, re-grade the stored red, confirm it is still
    red -- which a loosening that turns the red green would otherwise pass unnoticed.
    """
    cases_root = cases_root or EVALS / "cases"
    if not (run_dir / "meta.json").exists():
        if not unverified:
            return [], f"{run_dir}: no meta.json, so the fixture provenance is unknown; pass --unverified to grade it anyway"
        try:
            meta, turns, calls = reconstruct_run(run_dir)
        except ValueError as exc:
            return [], f"{run_dir}: {exc}"
    else:
        meta, turns, calls = load_run(run_dir)
    case_dir = cases_root / meta["case"]
    if not (case_dir / "case.json").exists():
        return [], f"case {meta['case']!r} no longer exists under {cases_root}"
    spec = json.loads((case_dir / "case.json").read_text())
    if (case_dir / "fixture").is_dir() and meta.get("fixture_digest") is not None:
        now = tree_digest(case_dir / "fixture")
        if meta.get("fixture_digest") != now:
            return [], (f"fixture for {meta['case']!r} has changed since this run "
                        f"({meta.get('fixture_digest')} -> {now}); its stream measures a different case")
    tz = spec.get("tz", "America/Chicago")
    # Render against the run's own clock, not today's: a spec that ever templates `{{today}}`
    # must mean what it meant when the stream was captured.
    spec = render_value(spec, context(tz, turns[0].t_start.astimezone(ZoneInfo(tz))))
    if "turns" not in spec:
        spec = dict(spec, turns=[{"prompt": spec["prompt"], "graders": spec.get("graders", [])}])
    return grade_turns(spec, turns, tz, run_dir, calls, git_base=meta.get("git_base")), None


def run_one(case: Case, arm: str, model: str, out: Path) -> tuple[list[tuple[str, bool, str]], str | None, dict[str, Any]]:
    tz = case.spec.get("tz", "America/Chicago")
    ctx = context(tz, datetime.now(ZoneInfo(tz)))
    spec = render_value(case.spec, ctx)
    out.mkdir(parents=True, exist_ok=True)
    # Fixture lives outside this repo so the sidecar's own CLAUDE.md is not discovered upward.
    work = Path(tempfile.mkdtemp(prefix="cos-eval-"))
    try:
        if (case.root / "fixture").is_dir():
            render_tree(case.root / "fixture", work, ctx)
            render_tree(case.root / "fixture", out / "fixture-before", ctx)
        # A case that owns a document needs a repo to commit into; the fixture snapshot keeps it.
        git_base = init_repo(work) if spec.get("git") else None
        env = dict(os.environ)
        mcp_config = None
        calls_log = calls_log_path(out)
        if spec.get("board"):
            # Every mock logs into one calls file; the publisher's rows are tagged `"tool": "publish"`.
            calls_log.parent.mkdir(parents=True, exist_ok=True)
            calls_log.touch()
            mcp_config = merge_mcp(mcp_config, board_mcp_config(calls_log, out / "board", work, tz, spec["board"].get("url")))
        if "peers" in spec:
            # Sessions file lives in the results dir; per-turn `peers` keys rewrite it before that turn.
            calls_log.parent.mkdir(parents=True, exist_ok=True)
            calls_log.touch()
            sessions = out / "peers-sessions.json"
            sessions.write_text(render((case.root / spec["peers"]).read_text(), ctx))
            mcp_config = merge_mcp(mcp_config, peers_mcp_config(sessions, calls_log, tz))
        if "turns" not in spec:
            # A single-prompt case is a one-turn case; everything runs through the stream-json driver.
            spec = dict(spec, turns=[{"prompt": spec["prompt"], "graders": spec.get("graders", [])}])
        return run_turns(spec, arm, model, out, work, env, mcp_config, calls_log, tz, case_root=case.root, ctx=ctx, git_base=git_base)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_turns(spec: dict[str, Any], arm: str, model: str, out: Path, work: Path, env: dict[str, str], mcp_config: dict[str, Any] | None, calls_log: Path, tz: str, case_root: Path = Path("."), ctx: dict[str, str] | None = None, git_base: str | None = None) -> tuple[list[tuple[str, bool, str]], str | None, dict[str, Any]]:
    """Multi-turn case: one stream-json process, graders scoped to each turn, fixture snapshot per turn."""
    cmd = command(Case("", Path(), spec), arm, model, mcp_config=mcp_config)
    (out / "command.json").write_text(json.dumps(cmd, indent=1))

    def snapshot(n: int) -> None:
        shutil.copytree(work, out / f"fixture-turn{n}", dirs_exist_ok=True)

    try:
        def before_turn(n: int) -> None:
            turn_spec = spec["turns"][n - 1]
            if "peers" in turn_spec:
                (out / "peers-sessions.json").write_text(render((case_root / turn_spec["peers"]).read_text(), ctx))

        turns = drive_turns(cmd, [t.get("prompt") for t in spec["turns"]], work, env, spec.get("timeout_seconds", 300), snapshot, wait_seconds=spec.get("wait_seconds", 180), before_turn=before_turn, answers=[t.get("answer") for t in spec["turns"]], host_log=calls_log)
    except TimeoutError as exc:
        return [], f"timeout: {exc}", {}
    shutil.copytree(work, out / "fixture", dirs_exist_ok=True)
    (out / "stream.jsonl").write_text("".join(json.dumps(e) + "\n" for t in turns for e in t.events))
    streams = [parse_stream(t.events) for t in turns]
    meta = {
        "turns_reached": len([st for st in streams if st.result]),
        "notional_usd": round(sum((st.result or {}).get("total_cost_usd", 0) for st in streams), 4),
        "denials": sum(len(st.denied_ids | t.host_denied) for st, t in zip(streams, turns)),
    }
    fixture_src = case_root / "fixture"
    (out / "meta.json").write_text(json.dumps(
        run_meta(case_root.name, arm, model, git_base, turns, meta,
                 tree_digest(fixture_src) if fixture_src.is_dir() else None), indent=1))
    if not streams or streams[0].result is None:
        return [], "claude produced no result for turn 1", meta
    ok, detail = check_arm(streams[0].init, arm, agent_flag_used="--agent" in cmd and arm != "agent", model=model, needs_board=bool(spec.get("board")), needs_peers="peers" in spec)
    if not ok:
        return [], f"arm check: {detail}", meta
    calls = [json.loads(l) for l in calls_log.read_text().splitlines() if l.strip()] if calls_log.exists() else []
    return grade_turns(spec, turns, tz, out, calls, git_base=git_base), None, meta


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", choices=["baseline", "agent", "both"])
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--case", action="append", default=[], help="case name glob; repeatable")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--regrade", metavar="RUN_DIR", help="re-grade a stored run under today's graders")
    ap.add_argument("--compare", nargs=2, metavar=("BASELINE_DIR", "AGENT_DIR"), help="discrimination table from two stored runs")
    ap.add_argument("--unverified", action="store_true", help="grade stored runs that predate meta.json; exact for single-turn runs only")
    args = ap.parse_args(argv)

    if args.regrade:
        results, error = regrade(Path(args.regrade), unverified=args.unverified)
        if error:
            print(f"  CANNOT REGRADE  {error}", file=sys.stderr)
            return 2
        for name, passed, why in results:
            print(f"  {'PASS' if passed else 'FAIL'}  {name}  — {why}")
        failed = sum(not p for _, p, _ in results)
        print(f"=> {len(results) - failed} of {len(results)} passed; {'RED' if failed else 'GREEN'}")
        return 1 if failed else 0

    if args.compare:
        rows, error = compare_runs([Path(args.compare[0])], [Path(args.compare[1])], unverified=args.unverified)
        if error:
            print(f"  CANNOT COMPARE  {error}", file=sys.stderr)
            return 2
        print(render_table(rows))
        return report_discrimination(rows)

    if not args.arm:
        print("--arm is required unless --regrade or --compare is given", file=sys.stderr)
        return 2
    cases = load_cases(args.case)
    if not cases:
        print("no cases matched", file=sys.stderr)
        return 2
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    arms = ["baseline", "agent"] if args.arm == "both" else [args.arm]
    harness_error = any_fail = any_regression = False
    for case in cases:
        graded: dict[str, list[list[tuple[str, bool, str]]]] = {}
        passed_arm: dict[str, bool] = {}
        for arm in arms:
            arm_pass = True
            graded[arm] = []
            for n in range(1, args.runs + 1):
                out = EVALS / "results" / stamp / case.name / arm / str(n)
                results, error, meta = run_one(case, arm, args.model, out)
                print(f"\n{case.name}  arm={arm}  model={args.model}  run={n}  {meta}")
                if error:
                    harness_error = True
                    arm_pass = False
                    print(f"  HARNESS ERROR  {error}")
                    continue
                graded[arm].append(results)
                for name, passed, why in results:
                    print(f"  {'PASS' if passed else 'FAIL'}  {name}  — {why}")
                    arm_pass &= passed
            passed_arm[arm] = arm_pass
        if args.arm == "both":
            rows = discrimination(arm_summary(graded["baseline"]), arm_summary(graded["agent"]))
            print(f"\n{case.name}  discrimination")
            print(render_table(rows))
            any_regression |= report_discrimination(rows) != 0
            counts = discrimination_counts(rows)
            tally = ", ".join(f"{n} {v}" for v, n in sorted(counts.items()))
            verdict = "GREEN" if passed_arm["agent"] else "RED"
            print(f"=> {case.name}: {verdict}  ({tally})")
            any_fail |= not passed_arm["agent"]
        elif args.arm == "baseline":
            print(f"=> {case.name}: {'NON-DISCRIMINATING (baseline passes)' if passed_arm['baseline'] else 'RED'}")
        else:
            print(f"=> {case.name}: {'GREEN' if passed_arm['agent'] else 'RED'}")
            any_fail |= not passed_arm["agent"]
    print(f"\nresults: {EVALS / 'results' / stamp}")
    if harness_error:
        return 2
    return 1 if (any_fail or any_regression) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
