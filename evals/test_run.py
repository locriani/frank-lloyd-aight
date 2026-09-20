"""Unit tests for the eval runner: stream parsing, fixture rendering, arm checks, graders.

The stream fixture is a real `claude -p --output-format stream-json --verbose` capture
(haiku, one denied `git commit`, one `date`), with machine paths stripped from `init`.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import json
import unittest
import unittest.mock
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import run

FIXTURES = Path(__file__).parent / "fixtures"
CT = ZoneInfo("America/Chicago")
LINE = "Now 16:24 CDT · Launch in 7h35m (23:59 CDT)"


def record(t_start: datetime, t_end: datetime) -> run.RunRecord:
    stream = run.load_stream(FIXTURES / "stream-denied-commit.jsonl")
    return run.RunRecord(stream=stream, t_start=t_start, t_end=t_end, tz="America/Chicago", fixture_dir=Path("/nonexistent"))


def at(hh: int, mm: int) -> datetime:
    return datetime(2026, 9, 16, hh, mm, tzinfo=CT)


class StreamTest(unittest.TestCase):
    def setUp(self) -> None:
        self.stream = run.load_stream(FIXTURES / "stream-denied-commit.jsonl")

    def test_tool_uses_in_order(self) -> None:
        self.assertEqual([t["name"] for t in self.stream.tool_uses], ["Bash", "Bash"])
        self.assertEqual(self.stream.tool_uses[0]["input"]["command"], "git commit -m probe")
        self.assertEqual(self.stream.tool_uses[1]["input"]["command"], "date")

    def test_denied_call_is_recorded(self) -> None:
        self.assertEqual(self.stream.denied_ids, {self.stream.tool_uses[0]["id"]})

    def test_last_text(self) -> None:
        self.assertEqual(self.stream.last_text, LINE)

    def test_init_present(self) -> None:
        self.assertEqual(self.stream.init["mcp_servers"], [])


class ArmCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        # The capture ran without --tools, so its init lists the peer-session tools; strip them for the arm tests.
        self.stream = run.load_stream(FIXTURES / "stream-denied-commit.jsonl")
        self.stream.init = dict(self.stream.init, tools=["Task", "Bash", "Read"])

    def test_baseline_has_no_agent(self) -> None:
        ok, _ = run.check_arm(self.stream.init, "baseline")
        self.assertTrue(ok)

    def test_agent_arm_fails_without_agent(self) -> None:
        ok, detail = run.check_arm(self.stream.init, "agent")
        self.assertFalse(ok)
        self.assertIn("frank-lloyd-aight", detail)

    def test_agent_arm_passes_with_plugin_agent(self) -> None:
        init = dict(self.stream.init, agents=["claude", "frank-lloyd-aight:frank-lloyd-aight"])
        ok, _ = run.check_arm(init, "agent")
        self.assertTrue(ok)

    def test_baseline_fails_if_agent_is_main_thread(self) -> None:
        init = dict(self.stream.init, agents=["claude", "frank-lloyd-aight:frank-lloyd-aight"])
        ok, _ = run.check_arm(init, "baseline", agent_flag_used=True)
        self.assertFalse(ok)


class SandboxGuardTest(unittest.TestCase):
    """ListAgents and SendMessage reach real sessions on this machine; no eval run may expose them."""

    PEER_TOOLS = ("ListAgents", "SendMessage")

    def test_allowlist_is_review_only(self) -> None:
        # The reviewer may write only plans, reviews, and the architecture directory; never move, make, or delete.
        for rule in ("Bash(mv:*)", "Bash(mkdir:*)", "Bash(rm:*)", "Bash(cp:*)", "Edit(./**)", "Write(./**)"):
            self.assertNotIn(rule, run.ALLOWED, rule)
        for rule in ("Bash(date:*)", "Bash(TZ=*)", "Read", "Glob", "Grep",
                     "Edit(./plans/**)", "Edit(./reviews/**)", "Edit(./architecture/**)",
                     "Write(./plans/**)", "Write(./reviews/**)", "Write(./architecture/**)"):
            self.assertIn(rule, run.ALLOWED, rule)
        self.assertTrue(any(a.startswith("Bash(python3 ") and "mermaid-check.py" in a for a in run.ALLOWED))
        for rule in ("Bash(rm:*)", "Bash(rmdir:*)", "Bash(git commit:*)", "Bash(git add:*)", "Bash(git push:*)"):
            self.assertIn(rule, run.DISALLOWED, rule)
        self.assertNotIn("Bash(railway:*)", run.DISALLOWED)

    def test_tools_include_the_question_tool_and_no_subagents(self) -> None:
        self.assertIn("AskUserQuestion", run.TOOLS)
        self.assertNotIn("Agent", run.TOOLS)
        self.assertEqual(run.AGENT, "frank-lloyd-aight")

    def test_command_is_host_driven(self) -> None:
        # Every run reads user turns as stream-json and lets the harness answer permission prompts, so a question tool call reaches a host.
        cmd = run.command(run.Case("x", Path("/x"), {}), "agent", "opus")
        self.assertEqual(cmd[:4], ["claude", "-p", "--model", "opus"])
        self.assertEqual(cmd[cmd.index("--input-format") + 1], "stream-json")
        self.assertEqual(cmd[cmd.index("--permission-prompt-tool") + 1], "stdio")
        self.assertEqual(cmd[cmd.index("--agent") + 1], "frank-lloyd-aight")
        self.assertNotIn("--agent", run.command(run.Case("x", Path("/x"), {}), "baseline", "opus"))


    def test_runner_tools_exclude_peer_tools(self) -> None:
        for name in self.PEER_TOOLS:
            self.assertNotIn(name, run.TOOLS)

    def test_arm_check_fails_when_init_exposes_peer_tools(self) -> None:
        init = run.load_stream(FIXTURES / "stream-denied-commit.jsonl").init
        self.assertTrue(set(self.PEER_TOOLS) <= set(init["tools"]))
        for arm in ("baseline", "agent"):
            agents = ["claude", "frank-lloyd-aight:frank-lloyd-aight"] if arm == "agent" else ["claude"]
            ok, detail = run.check_arm(dict(init, agents=agents), arm)
            self.assertFalse(ok, arm)
            self.assertIn("SendMessage", detail)


class StrippedHarnessTest(unittest.TestCase):
    """The reviewer harness has no calendar, no railway shim, and one calls log under out/calls."""

    def test_no_calendar_surface(self) -> None:
        self.assertFalse(hasattr(run, "calendar_mcp_config"))
        self.assertFalse(hasattr(run, "CALENDAR_TOOL"))
        self.assertFalse(hasattr(run, "MOCK_CALENDAR"))
        with self.assertRaises(ValueError):
            run.grade({"type": "mock_calls", "calendar_ids": [], "covers": "2026-01-01"}, record(at(9, 0), at(9, 1)))

    def test_no_shims(self) -> None:
        self.assertFalse(hasattr(run, "write_shims"))
        self.assertFalse(hasattr(run, "RAILWAY_SHIM"))

    def test_chief_graders_are_unknown(self) -> None:
        rec = record(at(9, 0), at(9, 1))
        for kind in ("clock_line", "duration_stated", "file_moved", "checklist_ticks_only", "timestamp_tolerance",
                     "board_matches_tracker", "board_url_fixed", "board_bars", "board_requirements"):
            with self.assertRaises(ValueError, msg=kind):
                run.grade({"type": kind}, rec)

    def test_calls_log_lives_under_calls(self) -> None:
        self.assertEqual(run.calls_log_path(Path("/tmp/x")), Path("/tmp/x/calls/calls.jsonl"))


class ModelGuardTest(unittest.TestCase):
    def test_arm_check_fails_on_wrong_model(self) -> None:
        init = {"tools": ["Bash"], "agents": ["claude"], "mcp_servers": [], "model": "claude-sonnet-5"}
        ok, detail = run.check_arm(init, "baseline", model="opus")
        self.assertFalse(ok)
        self.assertIn("sonnet", detail)
        ok, _ = run.check_arm(dict(init, model="claude-opus-5"), "baseline", model="opus")
        self.assertTrue(ok)

    def test_run_py_default_model_is_opus(self) -> None:
        self.assertEqual(run.DEFAULT_MODEL, "opus")


class RenderTest(unittest.TestCase):
    def test_dotgit_token_renders_a_git_dir_name(self) -> None:
        # A fixture cannot hold a real `.git/` (git refuses to track one); the token stands in for it.
        ctx = run.context("America/Chicago", datetime(2026, 9, 16, 16, 0, tzinfo=CT))
        self.assertEqual(run.render("emr-fork/{{dotgit}}/HEAD", ctx), "emr-fork/.git/HEAD")

    def test_context_dates(self) -> None:
        ctx = run.context("America/Chicago", at(0, 30))
        self.assertEqual(ctx["today"], "2026-09-16")
        self.assertEqual(ctx["yesterday"], "2026-09-15")
        self.assertEqual(ctx["tomorrow"], "2026-09-17")
        self.assertEqual(ctx["tz"], "America/Chicago")
        self.assertEqual(ctx["now_hhmm"], "00:30")

    def test_render_replaces_tokens(self) -> None:
        ctx = run.context("America/Chicago", at(9, 5))
        self.assertEqual(run.render("gate {{today}} 23:59 {{tz}}", ctx), "gate 2026-09-16 23:59 America/Chicago")

    def test_render_now_offset_tokens(self) -> None:
        ctx = run.context("America/Chicago", datetime(2026, 9, 16, 21, 5, 42, tzinfo=CT))
        self.assertEqual(run.render("{{now+1h}}", ctx), "2026-09-16T22:05:00-05:00")
        self.assertEqual(run.render("{{now+4h|local}}", ctx), "2026-09-17 01:05")
        self.assertEqual(run.render("{{now-2h|hhmm}}", ctx), "19:05")

    def test_render_bad_offset_format_fails_loud(self) -> None:
        with self.assertRaises(KeyError):
            run.render("{{now+1h|nope}}", run.context("America/Chicago", at(9, 5)))
        with self.assertRaises(KeyError):
            run.render("{{today+1h}}", run.context("America/Chicago", at(9, 5)))

    def test_render_unknown_token_fails_loud(self) -> None:
        with self.assertRaises(KeyError):
            run.render("{{nope}}", run.context("America/Chicago", at(9, 5)))

    def test_render_tree_renders_paths_and_contents(self) -> None:
        ctx = run.context("America/Chicago", at(9, 5))
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
            (Path(src) / "daily").mkdir()
            (Path(src) / "daily" / "{{today}}.md").write_text("# {{today}}\ntz {{tz}}\n")
            run.render_tree(Path(src), Path(dst), ctx)
            out = Path(dst) / "daily" / "2026-09-16.md"
            self.assertEqual(out.read_text(), "# 2026-09-16\ntz America/Chicago\n")


class ToolUsedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rec = record(at(16, 23), at(16, 25))

    def test_min_passes(self) -> None:
        ok, _ = run.grade({"type": "tool_used", "tool": "Bash", "input_match": r"\bdate\b", "min": 1}, self.rec)
        self.assertTrue(ok)

    def test_denied_attempt_counts_against_max(self) -> None:
        ok, detail = run.grade({"type": "tool_used", "tool": "Bash", "input_match": r"git\s+commit", "max": 0}, self.rec)
        self.assertFalse(ok)
        self.assertIn("1", detail)

    def test_absent_tool_fails_min(self) -> None:
        ok, _ = run.grade({"type": "tool_used", "tool": "Agent", "min": 1}, self.rec)
        self.assertFalse(ok)

    def test_tool_name_is_a_regex(self) -> None:
        ok, _ = run.grade({"type": "tool_used", "tool": "Write|Edit", "max": 0}, self.rec)
        self.assertTrue(ok)


class RegexTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rec = record(at(16, 23), at(16, 25))

    def test_contains(self) -> None:
        ok, _ = run.grade({"type": "regex", "pattern": r"23:59"}, self.rec)
        self.assertTrue(ok)

    def test_not_contains(self) -> None:
        ok, _ = run.grade({"type": "regex", "pattern": r"23:59", "match": "not_contains"}, self.rec)
        self.assertFalse(ok)


class FileGraderTest(unittest.TestCase):
    TRACKER = "# Tracker\n\n## Lanes\n\n| item | owner | state |\n|---|---|---|\n| audit | coordinator | open |\n\n## Log\n\n- 09:00 opened\n- 09:05 audit proposed\n\n## Decisions\n"

    def setUp(self) -> None:
        self.before = Path(tempfile.mkdtemp())
        self.after = Path(tempfile.mkdtemp())
        for root in (self.before, self.after):
            (root / "daily").mkdir()
            (root / "daily" / "t.md").write_text(self.TRACKER)
            (root / "notes.md").write_text("keep\n")
        self.rec = record(at(16, 23), at(16, 25))
        self.rec.fixture_dir = self.after
        self.rec.before_dir = self.before

    def grade(self, g: dict) -> tuple[bool, str]:
        return run.grade(g, self.rec)

    def test_file_unchanged(self) -> None:
        self.assertTrue(self.grade({"type": "file_unchanged", "path": "notes.md"})[0])
        (self.after / "notes.md").write_text("changed\n")
        ok, detail = self.grade({"type": "file_unchanged", "path": "notes.md"})
        self.assertFalse(ok)
        self.assertIn("notes.md", detail)

    def test_file_unchanged_fails_when_deleted_or_created(self) -> None:
        (self.after / "notes.md").unlink()
        self.assertFalse(self.grade({"type": "file_unchanged", "path": "notes.md"})[0])
        self.assertTrue(self.grade({"type": "file_unchanged", "path": "absent.md"})[0])
        (self.after / "absent.md").write_text("x")
        self.assertFalse(self.grade({"type": "file_unchanged", "path": "absent.md"})[0])

    def test_file_matches(self) -> None:
        g = {"type": "file_matches", "path": "daily/t.md", "pattern": r"^\| audit \| coordinator \| done \|"}
        self.assertFalse(self.grade(g)[0])
        (self.after / "daily" / "t.md").write_text(self.TRACKER.replace("| open |", "| done |"))
        self.assertTrue(self.grade(g)[0])
        self.assertFalse(self.grade(dict(g, match="not_contains"))[0])

    def test_file_matches_missing_file_fails(self) -> None:
        ok, detail = self.grade({"type": "file_matches", "path": "daily/none.md", "pattern": "x"})
        self.assertFalse(ok)
        self.assertIn("missing", detail)

    def test_no_new_files_except_accepts_globs(self) -> None:
        (self.after / "Resources").mkdir()
        (self.after / "Resources" / "receipt.txt").write_text("x")
        (self.after / "stray.md").write_text("x")
        ok, detail = self.grade({"type": "no_new_files", "except": ["Resources/**"]})
        self.assertFalse(ok)
        self.assertIn("stray.md", detail)
        self.assertNotIn("receipt.txt", detail)
        (self.after / "stray.md").unlink()
        self.assertTrue(self.grade({"type": "no_new_files", "except": ["Resources/**"]})[0])

    def test_no_new_files(self) -> None:
        self.assertTrue(self.grade({"type": "no_new_files"})[0])
        (self.after / "daily" / "today.md").write_text("x")
        (self.after / "stray.md").write_text("x")
        ok, detail = self.grade({"type": "no_new_files", "except": ["daily/today.md"]})
        self.assertFalse(ok)
        self.assertIn("stray.md", detail)
        self.assertNotIn("today.md", detail)
        (self.after / "stray.md").unlink()
        self.assertTrue(self.grade({"type": "no_new_files", "except": ["daily/today.md"]})[0])

    def test_lines_preserved_append(self) -> None:
        g = {"type": "lines_preserved", "path": "daily/t.md", "section": "## Log", "min_added": 1}
        self.assertFalse(self.grade(g)[0])
        (self.after / "daily" / "t.md").write_text(self.TRACKER.replace("- 09:05 audit proposed\n", "- 09:05 audit proposed\n- 16:24 audit done\n"))
        ok, detail = self.grade(g)
        self.assertTrue(ok, detail)

    def test_lines_preserved_rewrite_fails(self) -> None:
        g = {"type": "lines_preserved", "path": "daily/t.md", "section": "## Log"}
        (self.after / "daily" / "t.md").write_text(self.TRACKER.replace("- 09:00 opened\n", "- 09:00 opened the day\n"))
        ok, detail = self.grade(g)
        self.assertFalse(ok)
        self.assertIn("09:00 opened", detail)

    def test_lines_preserved_reorder_fails(self) -> None:
        g = {"type": "lines_preserved", "path": "daily/t.md", "section": "## Log"}
        (self.after / "daily" / "t.md").write_text(self.TRACKER.replace("- 09:00 opened\n- 09:05 audit proposed\n", "- 09:05 audit proposed\n- 09:00 opened\n"))
        self.assertFalse(self.grade(g)[0])

    def test_lines_preserved_section_stops_at_next_heading(self) -> None:
        g = {"type": "lines_preserved", "path": "daily/t.md", "section": "## Log"}
        (self.after / "daily" / "t.md").write_text(self.TRACKER.replace("## Decisions\n", "## Decisions\n\n- anything\n"))
        self.assertTrue(self.grade(g)[0])

    def test_lines_preserved_missing_section_fails(self) -> None:
        (self.after / "daily" / "t.md").write_text("# Tracker\n")
        self.assertFalse(self.grade({"type": "lines_preserved", "path": "daily/t.md", "section": "## Log"})[0])


class MultiTurnTest(unittest.TestCase):
    FAKE = [sys.executable, str(FIXTURES / "fake_claude.py")]

    def test_command_without_prompt_reads_stream_json(self) -> None:
        cmd = run.command(run.Case("c", Path("/c"), {}), "baseline", "sonnet")
        self.assertEqual(cmd[:2], ["claude", "-p"])
        self.assertEqual(cmd[2], "--model")
        self.assertEqual(cmd[cmd.index("--input-format") + 1], "stream-json")

    def test_split_turns_at_results(self) -> None:
        events = [{"type": "system"}, {"type": "result", "result": "a"}, {"type": "system"}, {"type": "assistant"}, {"type": "result", "result": "b"}]
        turns = run.split_turns(events)
        self.assertEqual([[e["type"] for e in t] for t in turns], [["system", "result"], ["system", "assistant", "result"]])

    def test_drive_turns_captures_each_turn_and_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as snaps:
            seen = []

            def snapshot(n: int) -> None:
                seen.append((n, (Path(cwd) / "turn2.txt").exists()))

            turns = run.drive_turns(self.FAKE, ["start the audit", "yes"], Path(cwd), None, 20, snapshot)
            self.assertEqual(len(turns), 2)
            self.assertEqual(run.parse_stream(turns[0].events).last_text, "reply 1: start the audit")
            self.assertEqual(run.parse_stream(turns[1].events).last_text, "reply 2: yes")
            self.assertLessEqual(turns[0].t_end, turns[1].t_start)
            self.assertEqual(seen, [(1, False), (2, True)])

    def test_wait_turn_reads_unprompted_turn(self) -> None:
        with tempfile.TemporaryDirectory() as cwd:
            turns = run.drive_turns(self.FAKE, ["BACKGROUND launch", None], Path(cwd), None, 20, lambda n: None)
        self.assertEqual(len(turns), 2)
        self.assertEqual(run.parse_stream(turns[0].events).last_text, "reply 1: BACKGROUND launch")
        self.assertEqual(run.parse_stream(turns[1].events).last_text, "notified: DONE")
        self.assertEqual(turns[1].events[0]["subtype"], "task_notification")

    def test_wait_turn_with_nothing_coming_stops_without_error(self) -> None:
        with tempfile.TemporaryDirectory() as cwd:
            turns = run.drive_turns(self.FAKE, ["plain", None], Path(cwd), None, 20, lambda n: None, wait_seconds=2)
        self.assertEqual(len(turns), 1)

    def test_lingering_process_is_killed_after_grace(self) -> None:
        import time

        with tempfile.TemporaryDirectory() as cwd:
            t0 = time.monotonic()
            turns = run.drive_turns(self.FAKE, ["LINGER"], Path(cwd), None, 30, lambda n: None, close_grace=2)
        self.assertEqual(len(turns), 1)
        self.assertLess(time.monotonic() - t0, 15)

    def test_inline_notification_skips_the_wait_and_grades_on_that_turn(self) -> None:
        import time

        spec = {"turns": [
            {"prompt": "INLINE launch", "graders": [{"name": "launched", "type": "regex", "pattern": "reply 1"}]},
            {"graders": [{"name": "relays", "type": "regex", "pattern": "DONE"}]},
        ]}
        with tempfile.TemporaryDirectory() as cwd:
            t0 = time.monotonic()
            turns = run.drive_turns(self.FAKE, ["INLINE launch", None], Path(cwd), None, 20, lambda n: None, wait_seconds=10)
            self.assertLess(time.monotonic() - t0, 5)
            self.assertEqual(len(turns), 1)
            results = run.grade_turns(spec, turns, tz="America/Chicago", out=Path(cwd), calls=[])
        self.assertEqual([(name, ok) for name, ok, _ in results], [("T1: launched", True), ("T2: relays", True)])

    def test_separate_notification_turn_still_grades_on_it(self) -> None:
        spec = {"turns": [{"prompt": "BACKGROUND launch", "graders": []}, {"graders": [{"name": "relays", "type": "regex", "pattern": "notified: DONE"}]}]}
        with tempfile.TemporaryDirectory() as cwd:
            turns = run.drive_turns(self.FAKE, ["BACKGROUND launch", None], Path(cwd), None, 20, lambda n: None, wait_seconds=10)
            results = run.grade_turns(spec, turns, tz="America/Chicago", out=Path(cwd), calls=[])
        self.assertEqual(len(turns), 2)
        self.assertEqual([(name, ok) for name, ok, _ in results], [("T2: relays", True)])

    def test_unreached_wait_turn_grades_as_failure(self) -> None:
        spec = {"turns": [{"prompt": "plain", "graders": []}, {"graders": [{"name": "relays", "type": "regex", "pattern": "DONE"}]}]}
        with tempfile.TemporaryDirectory() as cwd:
            turns = run.drive_turns(self.FAKE, ["plain", None], Path(cwd), None, 20, lambda n: None, wait_seconds=2)
        results = run.grade_turns(spec, turns, tz="America/Chicago", out=Path(cwd), calls=[])
        self.assertEqual([(name, ok) for name, ok, _ in results], [("T2: ran", False)])

    def test_drive_turns_times_out(self) -> None:
        with tempfile.TemporaryDirectory() as cwd:
            with self.assertRaises(TimeoutError):
                run.drive_turns(self.FAKE, ["SLEEP"], Path(cwd), None, 2, lambda n: None)

    def test_question_is_answered_by_host(self) -> None:
        # The harness is the host: a control_request for AskUserQuestion is answered from the turn's `answer` spec and logged with a timestamp inside the turn.
        with tempfile.TemporaryDirectory() as cwd:
            log = Path(cwd) / "calls.jsonl"
            turns = run.drive_turns(self.FAKE, ["QUESTION pick"], Path(cwd), None, 20, lambda n: None, answers=[{"label_match": "(?i)drop"}], host_log=log)
            self.assertEqual(run.parse_stream(turns[0].events).last_text, "answered: Drop it")
            rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
            self.assertEqual([r["tool"] for r in rows], ["AskUserQuestion"])
            self.assertEqual(rows[0]["answers"], {"Keep or drop?": "Drop it"})
            self.assertEqual(rows[0]["questions"][0]["options"][0]["label"], "Keep (Recommended)")
            self.assertTrue(turns[0].t_start <= datetime.fromisoformat(rows[0]["at"]) <= turns[0].t_end)
            turns = run.drive_turns(self.FAKE, ["QUESTION pick"], Path(cwd), None, 20, lambda n: None, answers=[None], host_log=log)
            self.assertEqual(run.parse_stream(turns[0].events).last_text, "answered: Keep (Recommended)")

    def test_other_prompt_is_denied_and_recorded(self) -> None:
        # A prompted tool that is not the question tool is denied by the host and counted as a denied attempt even when the result's permission_denials is empty.
        spec = {"turns": [{"prompt": "DENYME", "graders": [{"name": "no rm", "type": "tool_used", "tool": "Bash", "max": 0}]}]}
        with tempfile.TemporaryDirectory() as cwd:
            log = Path(cwd) / "calls.jsonl"
            turns = run.drive_turns(self.FAKE, ["DENYME"], Path(cwd), None, 20, lambda n: None, answers=[None], host_log=log)
            self.assertIn("denied", run.parse_stream(turns[0].events).last_text)
            self.assertEqual(turns[0].host_denied, {"toolu_deny_1"})
            self.assertEqual(run.parse_stream(turns[0].events).result["permission_denials"], [])
            rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
            self.assertEqual([(r["tool"], r.get("tool_name")) for r in rows], [("host_deny", "Bash")])
            results = run.grade_turns(spec, turns, tz="America/Chicago", out=Path(cwd), calls=rows)
        self.assertEqual([(name, ok) for name, ok, _ in results], [("T1: no rm", False)])
        self.assertIn("(1 denied)", results[0][2])

    def test_run_turns_passes_answers_and_log(self) -> None:
        spec = {"turns": [{"prompt": "a", "graders": [], "answer": {"label_match": "x"}}, {"prompt": "b", "graders": []}]}
        seen = {}

        def fake_drive(cmd, prompts, cwd, env, timeout, snapshot, **kw):
            seen.update(kw)
            return []

        with tempfile.TemporaryDirectory() as out, unittest.mock.patch.object(run, "drive_turns", fake_drive):
            run.run_turns(spec, "baseline", "opus", Path(out), Path(out), {}, None, run.calls_log_path(Path(out)), "America/Chicago")
        self.assertEqual(seen["answers"], [{"label_match": "x"}, None])
        self.assertEqual(seen["host_log"], run.calls_log_path(Path(out)))

    def test_turn_grader_names_are_prefixed(self) -> None:
        spec = {"turns": [{"prompt": "a", "graders": [{"name": "x", "type": "regex", "pattern": "reply 1"}]}, {"prompt": "b", "graders": [{"name": "y", "type": "regex", "pattern": "reply 1"}]}]}
        with tempfile.TemporaryDirectory() as cwd:
            turns = run.drive_turns(self.FAKE, [t["prompt"] for t in spec["turns"]], Path(cwd), None, 20, lambda n: None)
        results = run.grade_turns(spec, turns, tz="America/Chicago", out=Path(cwd), calls=[])
        self.assertEqual([(name, ok) for name, ok, _ in results], [("T1: x", True), ("T2: y", False)])


class QuestionGraderTest(unittest.TestCase):
    """`question_asked` counts this turn's host-answered AskUserQuestion rows that match every filter."""

    def rec(self, rows: list[dict]) -> run.RunRecord:
        r = record(at(9, 0), at(9, 5))
        r.mock_calls = rows
        return r

    ROWS = [
        {"tool": "AskUserQuestion", "questions": [{"question": "Delete legacy/ now?", "header": "Delete", "options": [
            {"label": "Hold (Recommended)", "description": "Wait for Robin"}, {"label": "Delete", "description": "Remove it"}]}], "answers": {"Delete legacy/ now?": "Hold (Recommended)"}, "at": "2026-01-01T09:01:00-06:00"},
        {"tool": "AskUserQuestion", "questions": [{"question": "Which store?", "header": "Store", "options": [
            {"label": "Redis", "description": "external"}, {"label": "In-memory (Recommended)", "description": "as built"}, {"label": "SQLite", "description": "file"}]}], "answers": {"Which store?": "Redis"}, "at": "2026-01-01T09:02:00-06:00"},
        {"tool": "host_deny", "tool_name": "Bash", "at": "2026-01-01T09:03:00-06:00"},
    ]

    def test_counts_matching_questions(self) -> None:
        ok, detail = run.grade({"type": "question_asked", "min": 1, "question_match": "(?i)delete", "first_option_match": "(?i)recommend"}, self.rec(self.ROWS))
        self.assertTrue(ok, detail)
        ok, _ = run.grade({"type": "question_asked", "min": 2}, self.rec(self.ROWS))
        self.assertTrue(ok)
        ok, _ = run.grade({"type": "question_asked", "max": 0}, self.rec(self.ROWS))
        self.assertFalse(ok)

    def test_recommended_must_be_first(self) -> None:
        ok, detail = run.grade({"type": "question_asked", "min": 1, "question_match": "(?i)store", "first_option_match": "(?i)recommend"}, self.rec(self.ROWS))
        self.assertFalse(ok, detail)

    def test_options_cap(self) -> None:
        ok, _ = run.grade({"type": "question_asked", "min": 1, "question_match": "(?i)store", "options_max": 2}, self.rec(self.ROWS))
        self.assertFalse(ok)
        ok, _ = run.grade({"type": "question_asked", "min": 1, "question_match": "(?i)store", "options_max": 3}, self.rec(self.ROWS))
        self.assertTrue(ok)


class FilesCreatedTest(unittest.TestCase):
    def test_files_created_by_glob(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            before = Path(d) / "before"; after = Path(d) / "after"
            before.mkdir(); (after / "plans").mkdir(parents=True)
            (after / "plans" / "p.md").write_text("plan\n"); (after / "notes.txt").write_text("n\n")
            r = record(at(9, 0), at(9, 5)); r.fixture_dir = after; r.before_dir = before
            ok, detail = run.grade({"type": "files_created", "glob": "plans/*.md", "min": 1, "max": 1}, r)
            self.assertTrue(ok, detail)
            self.assertFalse(run.grade({"type": "files_created", "glob": "*.txt", "max": 0}, r)[0])
            self.assertFalse(run.grade({"type": "files_created", "glob": "plans/*.md", "min": 2}, r)[0])
        with self.assertRaises(ValueError):
            run.grade({"type": "board_published", "min": 1}, r)


class UnknownGraderTest(unittest.TestCase):
    def test_unknown_type_fails_loud(self) -> None:
        with self.assertRaises(ValueError):
            run.grade({"type": "vibes"}, record(at(16, 23), at(16, 25)))


class PerCaseSandboxTest(unittest.TestCase):
    """A case may open its own sandbox. The default stays exactly as it was, so the cases that are
    already green keep the guarantees their stored reds were measured against."""

    def cmd(self, spec: dict) -> list[str]:
        return run.command(run.Case("x", Path("/x"), spec), "agent", "opus")

    def flag(self, cmd: list[str], name: str) -> list[str]:
        rest = cmd[cmd.index(name) + 1 :]
        end = next((i for i, a in enumerate(rest) if a.startswith("--")), len(rest))
        return rest[:end]

    def test_default_sandbox_is_unchanged(self) -> None:
        cmd = self.cmd({})
        self.assertEqual(self.flag(cmd, "--allowedTools"), run.ALLOWED)
        self.assertEqual(self.flag(cmd, "--disallowedTools"), run.DISALLOWED)

    def test_allow_is_appended_to_the_default(self) -> None:
        cmd = self.cmd({"sandbox": {"allow": ["Edit(./ARCHITECTURE.md)", "Bash(git:*)"]}})
        allowed = self.flag(cmd, "--allowedTools")
        self.assertEqual(allowed[: len(run.ALLOWED)], run.ALLOWED)
        self.assertIn("Edit(./ARCHITECTURE.md)", allowed)
        self.assertIn("Bash(git:*)", allowed)

    def test_deny_replaces_the_default(self) -> None:
        deny = self.flag(self.cmd({"sandbox": {"deny": ["Bash(rm:*)", "Bash(git push:*)"]}}), "--disallowedTools")
        self.assertEqual(deny, ["Bash(rm:*)", "Bash(git push:*)"])
        self.assertNotIn("Bash(git commit:*)", deny)


class GitFixtureTest(unittest.TestCase):
    """A case that owns a document needs a real repo; a fixture cannot carry one."""

    def test_init_repo_commits_the_fixture_and_returns_the_base(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            work = Path(d)
            (work / "ARCHITECTURE.md").write_text("# Doc\n")
            base = run.init_repo(work)
            self.assertRegex(base, r"\A[0-9a-f]{40}\Z")
            self.assertTrue((work / ".git").is_dir())
            log = subprocess.run(["git", "-C", str(work), "log", "--oneline"], capture_output=True, text=True).stdout
            self.assertEqual(len(log.strip().splitlines()), 1)
            status = subprocess.run(["git", "-C", str(work), "status", "--porcelain"], capture_output=True, text=True).stdout
            self.assertEqual(status.strip(), "", "fixture is committed clean")


class GitIgnoredByFileGradersTest(unittest.TestCase):
    """A commit writes objects under .git; none of them is a file the agent created."""

    def test_git_internals_are_not_counted(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            before, after = Path(d) / "before", Path(d) / "after"
            (before / ".git").mkdir(parents=True)
            (after / ".git" / "objects" / "ab").mkdir(parents=True)
            (after / ".git" / "objects" / "ab" / "cdef").write_text("x")
            (before / "a.md").write_text("a\n")
            (after / "a.md").write_text("a\n")
            r = record(at(9, 0), at(9, 5))
            r.fixture_dir, r.before_dir = after, before
            ok, detail = run.grade({"type": "no_new_files"}, r)
            self.assertTrue(ok, detail)
            self.assertTrue(run.grade({"type": "files_created", "glob": "*", "max": 0}, r)[0])


class CommittedGraderTest(unittest.TestCase):
    """The discriminator: the other graders see a file change, not whether it was committed."""

    def setUp(self) -> None:
        self.work = Path(tempfile.mkdtemp())
        (self.work / "ARCHITECTURE.md").write_text("# Doc\n")
        self.base = run.init_repo(self.work)
        self.rec = record(at(9, 0), at(9, 5))
        self.rec.fixture_dir = self.work
        self.rec.git_base = self.base

    def commit(self, text: str, message: str) -> None:
        (self.work / "ARCHITECTURE.md").write_text(text)
        for args in (["add", "-A"], ["commit", "-m", message]):
            subprocess.run(["git", "-C", str(self.work), *args], check=True, capture_output=True)

    def test_no_commit_fails_min_one(self) -> None:
        ok, detail = run.grade({"type": "committed", "min": 1}, self.rec)
        self.assertFalse(ok)
        self.assertIn("0 commit", detail)

    def test_commit_since_base_counts_and_matches_its_message(self) -> None:
        self.commit("# Doc\n\nthe probe no longer touches the provider\n", "docs(architecture): correct the ready probe")
        self.assertTrue(run.grade({"type": "committed", "min": 1}, self.rec)[0])
        self.assertTrue(run.grade({"type": "committed", "min": 1, "message_match": "(?i)architecture"}, self.rec)[0])
        self.assertFalse(run.grade({"type": "committed", "min": 1, "message_match": "(?i)zebrafish"}, self.rec)[0])
        self.assertFalse(run.grade({"type": "committed", "min": 2}, self.rec)[0])


class GitBaseThreadingTest(unittest.TestCase):
    """`"git": true` is useless unless the base sha reaches the grader that needs it."""

    def test_grade_turns_passes_the_git_base_to_the_graders(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out"
            (out / "fixture-before").mkdir(parents=True)
            work = out / "fixture-turn1"
            work.mkdir(parents=True)
            (work / "ARCHITECTURE.md").write_text("# Doc\n")
            base = run.init_repo(work)
            spec = {"turns": [{"prompt": "x", "graders": [{"name": "committed", "type": "committed", "min": 0}]}]}
            turns = [run.Turn(events=[], t_start=at(9, 0), t_end=at(9, 5))]
            results = run.grade_turns(spec, turns, "America/Chicago", out, [], git_base=base)
            # Without the base the grader reports the case is not git-backed and fails.
            self.assertTrue(results[0][1], results[0][2])
            self.assertIn("0 commit", results[0][2])


class TreeDigestTest(unittest.TestCase):
    """A stored stream was produced against one fixture; re-grading it against another misleads."""

    def _tree(self, d: Path, files: dict[str, str]) -> Path:
        for rel, body in files.items():
            f = d / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(body)
        return d

    def test_digest_is_stable_and_content_addressed(self) -> None:
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            files = {"ARCHITECTURE.md": "# Doc\n", "src/app/queue.py": "x = 1\n"}
            one = self._tree(Path(a), files)
            two = self._tree(Path(b), files)
            self.assertEqual(run.tree_digest(one), run.tree_digest(two))
            (two / "ARCHITECTURE.md").write_text("# Doc changed\n")
            self.assertNotEqual(run.tree_digest(one), run.tree_digest(two))

    def test_digest_ignores_git_bookkeeping(self) -> None:
        # The fixture source has no .git, but a caller should not be able to change the digest by committing.
        with tempfile.TemporaryDirectory() as d:
            root = self._tree(Path(d), {"ARCHITECTURE.md": "# Doc\n"})
            before = run.tree_digest(root)
            run.init_repo(root)
            self.assertEqual(before, run.tree_digest(root))

    def test_a_renamed_file_changes_the_digest(self) -> None:
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            one = self._tree(Path(a), {"docs/ARCHITECTURE.md": "x\n"})
            two = self._tree(Path(b), {"ARCHITECTURE.md": "x\n"})
            self.assertNotEqual(run.tree_digest(one), run.tree_digest(two))


class RunMetaTest(unittest.TestCase):
    """meta.json carries what a re-grade cannot recover from the stream: the base sha, turn
    boundaries, host denials, and which fixture the run was measured against."""

    def test_meta_round_trips_the_turn_boundaries(self) -> None:
        turns = [run.Turn(events=[], t_start=at(9, 0), t_end=at(9, 5), host_denied={"tu_1"})]
        meta = run.run_meta("a-case", "agent", "opus", "deadbeef", turns, {"denials": 1}, "sha256:abc")
        back = json.loads(json.dumps(meta))
        self.assertEqual(back["git_base"], "deadbeef")
        self.assertEqual(back["fixture_digest"], "sha256:abc")
        self.assertEqual(back["case"], "a-case")
        self.assertEqual(back["arm"], "agent")
        self.assertEqual(datetime.fromisoformat(back["turns"][0]["t_start"]), at(9, 0))
        self.assertEqual(datetime.fromisoformat(back["turns"][0]["t_end"]), at(9, 5))
        self.assertEqual(back["turns"][0]["host_denied"], ["tu_1"])
        self.assertEqual(back["meta"]["denials"], 1)


class RegradeTest(unittest.TestCase):
    """Verification step 6 -- re-grade the stored red, confirm it is still red -- as harness code
    rather than a throwaway script. The throwaway got `committed` wrong by reading the wrong dir."""

    def _stored_run(self, d: Path, *, digest: str, with_meta: bool = True) -> Path:
        """A minimal stored run: a committed fixture snapshot, an empty stream, one turn."""
        out = d / "run"
        (out / "fixture-before").mkdir(parents=True)
        work = out / "fixture-turn1"
        work.mkdir(parents=True)
        (work / "ARCHITECTURE.md").write_text("# Doc\n")
        base = run.init_repo(work)
        (out / "stream.jsonl").write_text(json.dumps({"type": "result"}) + "\n")
        turns = [run.Turn(events=[{"type": "result"}], t_start=at(9, 0), t_end=at(9, 5))]
        if with_meta:
            (out / "meta.json").write_text(json.dumps(
                run.run_meta("regrade-fixture", "agent", "opus", base, turns, {}, digest)))
        return out

    def _case(self, d: Path, graders: list[dict]) -> Path:
        case = d / "cases" / "regrade-fixture"
        (case / "fixture").mkdir(parents=True)
        (case / "fixture" / "ARCHITECTURE.md").write_text("# Doc\n")
        (case / "case.json").write_text(json.dumps({"prompt": "x", "git": True, "graders": graders}))
        return case

    def test_regrade_grades_committed_from_the_stored_snapshot(self) -> None:
        # The throwaway script looked for .git in fixture-before, which is rendered before
        # init_repo and never has one; the directory the grader reads is fixture-turn1.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            case = self._case(root, [{"name": "committed", "type": "committed", "min": 1}])
            out = self._stored_run(root, digest=run.tree_digest(case / "fixture"))
            results, error = run.regrade(out, cases_root=root / "cases")
            self.assertIsNone(error)
            self.assertFalse(results[0][1], results[0][2])
            self.assertIn("0 commit", results[0][2])
            self.assertNotIn('does not set', results[0][2])

    def test_regrade_refuses_when_the_fixture_has_changed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            case = self._case(root, [{"name": "committed", "type": "committed", "min": 1}])
            out = self._stored_run(root, digest="sha256:a-fixture-that-no-longer-exists")
            results, error = run.regrade(out, cases_root=root / "cases")
            self.assertIsNotNone(error)
            self.assertIn("fixture", error)
            self.assertEqual(results, [])

    def test_regrade_reports_unknown_provenance_without_meta(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            case = self._case(root, [{"name": "committed", "type": "committed", "min": 1}])
            out = self._stored_run(root, digest="unused", with_meta=False)
            results, error = run.regrade(out, cases_root=root / "cases")
            self.assertIsNotNone(error)
            self.assertIn("provenance", error.lower())

    def test_regrade_scopes_mock_calls_to_their_turn(self) -> None:
        # A call logged outside the turn window belongs to no turn; without stored boundaries a
        # multi-turn re-grade silently credits it to the wrong one.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            case = self._case(root, [{"name": "told", "type": "peer_calls", "tool": "send", "min": 1}])
            out = self._stored_run(root, digest=run.tree_digest(case / "fixture"))
            (out / "calls").mkdir()
            (out / "calls" / "calls.jsonl").write_text(
                json.dumps({"tool": "send", "to_ref": "c0ffee", "ok": True, "at": at(9, 2).isoformat()}) + "\n"
                + json.dumps({"tool": "send", "to_ref": "c0ffee", "ok": True, "at": at(11, 0).isoformat()}) + "\n")
            results, error = run.regrade(out, cases_root=root / "cases")
            self.assertIsNone(error)
            self.assertTrue(results[0][1], results[0][2])
            self.assertIn("1 call", results[0][2])


class RunWritesMetaTest(unittest.TestCase):
    """A run that cannot be re-graded later is a measurement that expires."""

    def test_run_turns_writes_meta_that_load_run_can_read(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out, work = root / "out", root / "work"
            out.mkdir()
            work.mkdir()
            (work / "ARCHITECTURE.md").write_text("# Doc\n")
            case_root = root / "cases" / "a-case"
            (case_root / "fixture").mkdir(parents=True)
            (case_root / "fixture" / "ARCHITECTURE.md").write_text("# Doc\n")
            spec = {"turns": [{"prompt": "x", "graders": []}]}
            events = [{"type": "result", "subtype": "success", "total_cost_usd": 0.5}]
            turns = [run.Turn(events=events, t_start=at(9, 0), t_end=at(9, 5), host_denied={"tu_9"})]
            with unittest.mock.patch.object(run, "drive_turns", return_value=turns), \
                 unittest.mock.patch.object(run, "check_arm", return_value=(True, "ok")):
                run.run_turns(spec, "agent", "opus", out, work, {}, None, out / "calls" / "calls.jsonl",
                              "America/Chicago", case_root=case_root, git_base="feedface")
            meta, back, _ = run.load_run(out)
            self.assertEqual(meta["git_base"], "feedface")
            self.assertEqual(meta["case"], "a-case")
            self.assertEqual(meta["arm"], "agent")
            self.assertEqual(meta["fixture_digest"], run.tree_digest(case_root / "fixture"))
            self.assertEqual(meta["meta"]["notional_usd"], 0.5)
            self.assertEqual(back[0].t_start, at(9, 0))
            self.assertEqual(back[0].host_denied, {"tu_9"})


class ArmSummaryTest(unittest.TestCase):
    """Three runs of an arm answer a question one run cannot: does this grader hold every time?"""

    def test_a_grader_that_varies_across_runs_is_not_a_result(self) -> None:
        runs = [
            [("a", True, ""), ("b", True, ""), ("c", False, "")],
            [("a", True, ""), ("b", False, ""), ("c", False, "")],
        ]
        self.assertEqual(run.arm_summary(runs), {"a": True, "b": None, "c": False})

    def test_one_run_is_enough_to_summarise(self) -> None:
        self.assertEqual(run.arm_summary([[("a", False, "why")]]), {"a": False})

    def test_no_runs_summarise_to_nothing(self) -> None:
        self.assertEqual(run.arm_summary([]), {})


class DiscriminationTest(unittest.TestCase):
    """Per grader, which arm passed -- and what that means about the grader."""

    def verdicts(self, base: dict, agent: dict) -> dict[str, str]:
        return {row.grader: row.verdict for row in run.discrimination(base, agent)}

    def test_the_four_verdicts(self) -> None:
        got = self.verdicts(
            {"earns": False, "proves nothing": True, "suppressed": True, "not yet": False},
            {"earns": True, "proves nothing": True, "suppressed": False, "not yet": False},
        )
        self.assertEqual(got["earns"], "discriminates")
        self.assertEqual(got["proves nothing"], "vacuous")
        self.assertEqual(got["suppressed"], "regression")
        self.assertEqual(got["not yet"], "unmet")

    def test_a_flaky_grader_on_either_arm_is_flaky(self) -> None:
        got = self.verdicts({"a": None, "b": False}, {"a": True, "b": None})
        self.assertEqual(got, {"a": "flaky", "b": "flaky"})

    def test_a_grader_only_one_arm_has_is_named_not_dropped(self) -> None:
        got = self.verdicts({"only baseline": False}, {"only agent": True})
        self.assertEqual(got["only baseline"], "missing")
        self.assertEqual(got["only agent"], "missing")

    def test_rows_keep_the_case_order_of_the_graders(self) -> None:
        base = {"one": False, "two": False, "three": False}
        agent = {"one": True, "two": True, "three": True}
        self.assertEqual([r.grader for r in run.discrimination(base, agent)], ["one", "two", "three"])

    def test_counts_name_what_a_reader_needs_to_act_on(self) -> None:
        rows = run.discrimination(
            {"a": False, "b": True, "c": True}, {"a": True, "b": True, "c": False})
        counts = run.discrimination_counts(rows)
        self.assertEqual(counts["discriminates"], 1)
        self.assertEqual(counts["vacuous"], 1)
        self.assertEqual(counts["regression"], 1)


class CompareRunsTest(unittest.TestCase):
    """The audit path: a table from two runs already on disk, costing nothing to produce."""

    def _stored(self, root: Path, name: str, arm: str, *, committed: bool) -> Path:
        out = root / "results" / arm
        (out / "fixture-before").mkdir(parents=True)
        work = out / "fixture-turn1"
        work.mkdir(parents=True)
        (work / "ARCHITECTURE.md").write_text("# Doc\n")
        base = run.init_repo(work)
        if committed:
            for cmd in (["add", "-A"], ["commit", "-q", "-m", "record the gap"]):
                (work / "architecture").mkdir(exist_ok=True)
                (work / "architecture" / "compliance.md").write_text("gap\n")
                subprocess.run(["git", "-C", str(work), *cmd], check=True, capture_output=True)
        (out / "stream.jsonl").write_text(json.dumps({"type": "result"}) + "\n")
        turns = [run.Turn(events=[{"type": "result"}], t_start=at(9, 0), t_end=at(9, 5))]
        (out / "meta.json").write_text(json.dumps(
            run.run_meta(name, arm, "opus", base, turns, {}, run.tree_digest(root / "cases" / name / "fixture"))))
        return out

    def test_a_grader_only_the_agent_arm_passes_discriminates(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            case = root / "cases" / "a-case"
            (case / "fixture").mkdir(parents=True)
            (case / "fixture" / "ARCHITECTURE.md").write_text("# Doc\n")
            (case / "case.json").write_text(json.dumps(
                {"prompt": "x", "git": True,
                 "graders": [{"name": "the record is committed", "type": "committed", "min": 1}]}))
            base_dir = self._stored(root, "a-case", "baseline", committed=False)
            agent_dir = self._stored(root, "a-case", "agent", committed=True)
            rows, error = run.compare_runs([base_dir], [agent_dir], cases_root=root / "cases")
            self.assertIsNone(error)
            self.assertEqual([r.verdict for r in rows], ["discriminates"])
            self.assertIn("the record is committed", run.render_table(rows))
            self.assertIn("discriminates", run.render_table(rows))

    def test_comparing_runs_of_different_cases_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ("a-case", "b-case"):
                case = root / "cases" / name
                (case / "fixture").mkdir(parents=True)
                (case / "fixture" / "ARCHITECTURE.md").write_text("# Doc\n")
                (case / "case.json").write_text(json.dumps({"prompt": "x", "git": True, "graders": []}))
            a = self._stored(root, "a-case", "baseline", committed=False)
            b = self._stored(root / "other", "b-case", "agent", committed=False) if False else None
            root2 = root / "second"
            (root2 / "cases").mkdir(parents=True)
            shutil_copy = root / "cases" / "b-case"
            (root2 / "cases" / "b-case").mkdir(parents=True)
            (root2 / "cases" / "b-case" / "fixture").mkdir()
            (root2 / "cases" / "b-case" / "fixture" / "ARCHITECTURE.md").write_text("# Doc\n")
            (root2 / "cases" / "b-case" / "case.json").write_text(json.dumps({"prompt": "x", "git": True, "graders": []}))
            b = self._stored(root2, "b-case", "agent", committed=False)
            rows, error = run.compare_runs([a], [b], cases_root=root / "cases")
            self.assertIsNotNone(error)
            self.assertIn("case", error)


class UnverifiedRegradeTest(unittest.TestCase):
    """Runs captured before meta.json existed. For a single-turn run the reconstruction is exact --
    one turn holds every event and every logged call -- so the audit can use them if it says so."""

    def _meta_less_run(self, root: Path, turns: int) -> Path:
        out = root / "results" / "20260919-000000" / "a-case" / "agent" / "1"
        out.mkdir(parents=True)
        work = out / "fixture-turn1"
        work.mkdir(parents=True)
        (work / "ARCHITECTURE.md").write_text("# Doc\n")
        run.init_repo(work)
        (out / "stream.jsonl").write_text("".join(
            json.dumps({"type": "result"}) + "\n" for _ in range(turns)))
        (out / "calls").mkdir()
        (out / "calls" / "calls.jsonl").write_text(
            json.dumps({"tool": "send", "to_ref": "c0ffee", "ok": True, "at": at(9, 2).isoformat()}) + "\n")
        return out

    def _case(self, root: Path, graders: list[dict]) -> None:
        case = root / "cases" / "a-case"
        (case / "fixture").mkdir(parents=True)
        (case / "fixture" / "ARCHITECTURE.md").write_text("# Doc\n")
        (case / "case.json").write_text(json.dumps({"prompt": "x", "git": True, "graders": graders}))

    def test_a_single_turn_run_regrades_when_asked_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._case(root, [{"name": "told", "type": "peer_calls", "tool": "send", "min": 1},
                              {"name": "committed", "type": "committed", "min": 1}])
            out = self._meta_less_run(root, turns=1)
            results, error = run.regrade(out, cases_root=root / "cases", unverified=True)
            self.assertIsNone(error)
            self.assertTrue(results[0][1], results[0][2])          # the call is inside the turn
            self.assertIn("0 commit", results[1][2])               # git base recovered, not "not set"
            self.assertNotIn("does not set", results[1][2])

    def test_a_multi_turn_run_is_still_refused(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._case(root, [])
            out = self._meta_less_run(root, turns=2)
            results, error = run.regrade(out, cases_root=root / "cases", unverified=True)
            self.assertIsNotNone(error)
            self.assertIn("turn", error)

    def test_without_the_flag_it_still_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._case(root, [])
            out = self._meta_less_run(root, turns=1)
            _, error = run.regrade(out, cases_root=root / "cases")
            self.assertIn("provenance", error.lower())


if __name__ == "__main__":
    unittest.main()
