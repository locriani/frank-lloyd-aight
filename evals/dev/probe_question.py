#!/usr/bin/env python3
"""Probe: under `claude -p --input-format stream-json --permission-prompt-tool stdio`, is AskUserQuestion
present, does a `control_request` arrive for it, and what does the wire format look like?

    python3 evals/dev/probe_question.py [--model haiku] [--tools Read,AskUserQuestion] [--timeout 120]

Acts as the host: allows AskUserQuestion with the first option of every question as the answer, denies
any other prompted tool. Prints a JSON summary: init tools, every control_request verbatim, the
responses sent, the assistant's final text, and the result event's permission_denials.
"""
from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

PROMPT = "Use the AskUserQuestion tool to ask me one question with two options, the recommended one first. Then say which option I picked."


def answer(request: dict) -> dict:
    tool = request.get("tool_name")
    if tool == "AskUserQuestion":
        inp = request.get("input", {})
        answers = {q["question"]: q["options"][0]["label"] for q in inp.get("questions", []) if q.get("options")}
        return {"behavior": "allow", "updatedInput": dict(inp, answers=answers)}
    return {"behavior": "deny", "message": f"{tool} blocked by probe"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="haiku")
    ap.add_argument("--tools", default="Read,AskUserQuestion")
    ap.add_argument("--timeout", type=float, default=120)
    a = ap.parse_args()
    cwd = Path(tempfile.mkdtemp(prefix="fla-probe-"))
    (cwd / "CLAUDE.md").write_text("# Probe\n\nThis is a throwaway directory.\n")
    cmd = [
        "claude", "-p", "--model", a.model,
        "--output-format", "stream-json", "--verbose", "--no-session-persistence",
        "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", json.dumps({"mcpServers": {}}),
        "--max-turns", "4", "--tools", *a.tools.split(","),
        "--input-format", "stream-json", "--permission-prompt-tool", "stdio",
    ]
    proc = subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    lines: queue.Queue[str | None] = queue.Queue()

    def pump() -> None:
        for line in proc.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=pump, daemon=True).start()
    proc.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": PROMPT}}) + "\n")
    proc.stdin.flush()
    summary: dict = {"command": cmd, "init_tools": None, "control_requests": [], "responses": [], "assistant_text": [], "result": None, "other_event_types": []}
    deadline = time.monotonic() + a.timeout
    while True:
        try:
            line = lines.get(timeout=max(deadline - time.monotonic(), 0.01))
        except queue.Empty:
            summary["timeout"] = True
            break
        if line is None:
            break
        if not line.strip():
            continue
        ev = json.loads(line)
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            summary["init_tools"] = ev.get("tools")
        elif t == "control_request":
            summary["control_requests"].append(ev)
            req = ev.get("request", {})
            if req.get("subtype") == "can_use_tool":
                data = answer(req)
            else:
                data = {}
            resp = {"type": "control_response", "response": {"subtype": "success", "request_id": ev.get("request_id"), "response": data}}
            summary["responses"].append(resp)
            proc.stdin.write(json.dumps(resp) + "\n")
            proc.stdin.flush()
        elif t == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    summary["assistant_text"].append(block["text"])
                elif block.get("type") == "tool_use":
                    summary.setdefault("tool_uses", []).append({"name": block.get("name"), "input": block.get("input")})
        elif t == "result":
            summary["result"] = {k: ev.get(k) for k in ("subtype", "num_turns", "permission_denials", "is_error")}
            break
        else:
            summary["other_event_types"].append(t if t != "system" else f"system/{ev.get('subtype')}")
    try:
        proc.stdin.close()
    except Exception:
        pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    summary["exit"] = proc.returncode
    summary["stderr_tail"] = proc.stderr.read()[-600:]
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
