#!/usr/bin/env python3
"""Stand-in for `claude -p --input-format stream-json --permission-prompt-tool stdio` in runner unit tests.

Emits init, one assistant text, and a result per user line on stdin. Turn 2 writes `turn2.txt` in
cwd so tests can check per-turn fixture snapshots. A user message containing SLEEP hangs; one containing
BACKGROUND is followed by an unprompted notification turn; INLINE carries the notification inside its own
turn; LINGER keeps the process alive after stdin closes. QUESTION asks one AskUserQuestion through a
control_request and reports the label the host answered with; DENYME asks permission for a Bash rm and
reports whether the host denied it, with an empty permission_denials in the result either way.
"""

import json
import sys
import time
from pathlib import Path

QUESTION = {"question": "Keep or drop?", "header": "Choice", "multiSelect": False, "options": [
    {"label": "Keep (Recommended)", "description": "Leave it where it is"},
    {"label": "Drop it", "description": "Remove it"},
]}


def emit(ev):
    print(json.dumps(ev), flush=True)


def init():
    return {"type": "system", "subtype": "init", "tools": ["Bash", "AskUserQuestion"], "agents": ["claude"], "mcp_servers": []}


def text(t):
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}


def result(t):
    return {"type": "result", "subtype": "success", "result": t, "num_turns": 1, "permission_denials": []}


def turn(t):
    return (init(), text(t), result(t))


def ask_host(tool_name, tool_input, tool_use_id):
    """Emit a control_request and block for the host's control_response, like the real CLI."""
    emit({"type": "control_request", "request_id": f"req-{tool_use_id}", "request": {"subtype": "can_use_tool", "tool_name": tool_name, "input": tool_input, "tool_use_id": tool_use_id, "requires_user_interaction": tool_name == "AskUserQuestion"}})
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)["response"].get("response", {})


n = 0
linger = False
while True:
    line = sys.stdin.readline()
    if not line:
        break
    if not line.strip():
        continue
    n += 1
    msg = json.loads(line)["message"]["content"]
    linger = linger or "LINGER" in msg
    if "SLEEP" in msg:
        time.sleep(30)
    if n == 2:
        Path("turn2.txt").write_text("written in turn 2\n")
    if "QUESTION" in msg:
        emit(init())
        emit({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "toolu_q_1", "name": "AskUserQuestion", "input": {"questions": [QUESTION]}}]}})
        answer = ask_host("AskUserQuestion", {"questions": [QUESTION]}, "toolu_q_1") or {}
        label = answer.get("updatedInput", {}).get("answers", {}).get(QUESTION["question"], "<no answer>")
        final = f"answered: {label}"
        emit(text(final))
        emit(result(final))
        continue
    if "DENYME" in msg:
        emit(init())
        emit({"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "toolu_deny_1", "name": "Bash", "input": {"command": "rm -rf x"}}]}})
        answer = ask_host("Bash", {"command": "rm -rf x"}, "toolu_deny_1") or {}
        final = "denied by host" if answer.get("behavior") == "deny" else "ran rm"
        emit(text(final))
        emit(result(final))
        continue
    if "INLINE" in msg:
        # The background task finishes before the assistant stops: the notification lands inside this turn.
        i, reply, res = turn(f"reply {n}: {msg}")
        final = f"reply {n}: {msg} — handled inline: DONE"
        for ev in (i, reply, {"type": "system", "subtype": "task_notification"}, text(final), dict(res, result=final)):
            emit(ev)
        continue
    for ev in turn(f"reply {n}: {msg}"):
        emit(ev)
    if "BACKGROUND" in msg:
        # A background task finishing starts a turn with no user message, as `claude -p` does.
        time.sleep(0.5)
        emit({"type": "system", "subtype": "task_notification"})
        for ev in turn("notified: DONE"):
            emit(ev)
if linger:
    # A background task still running after stdin closes keeps the process alive.
    time.sleep(60)
