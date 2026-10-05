"""Text is laid out by the renderer, never by the file: no line break inside prose, no cap on text width.

Zach, 2026-10-05: "you are not a word wrapping engine, it turns out that the zillions of lines of code spent on FONT LAYOUT are better than your awful random line breaks", and of a page capped at 860 pixels and 65 characters: "also page width caps. Yeah no".
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import run

sys.path.insert(0, str(run.PLUGIN_ROOT / "hooks"))
import no_wrap  # noqa: E402


def lines(name: str, text: str) -> list[int]:
    return [n for n, _ in no_wrap.problems(name, text)]


class MarkdownTest(unittest.TestCase):
    def test_a_paragraph_broken_across_lines_is_named_at_the_break(self) -> None:
        self.assertEqual(lines("a.md", "# T\n\nThe queue retries three times and\nthen gives up.\n"), [4])

    def test_one_line_paragraphs_pass(self) -> None:
        self.assertEqual(lines("a.md", "# T\n\nOne paragraph, however long it is.\n\nAnother.\n"), [])

    def test_a_list_item_broken_across_lines_is_named(self) -> None:
        self.assertEqual(lines("a.md", "- the first item runs on\n  to a second line\n- the second\n"), [2])

    def test_a_blockquote_broken_across_lines_is_named(self) -> None:
        self.assertEqual(lines("a.md", "> a quote that runs on\n> to a second line\n"), [2])

    def test_blocks_that_keep_their_own_lines_pass(self) -> None:
        text = (
            "---\nname: x\ndescription: y\n---\n\n# Title\nText under a heading.\n\n- one\n- two\n  - nested\n1. first\n2. second\n\n"
            "| a | b |\n|---|---|\n| 1 | 2 |\n\n```\nline one\nline two\n```\n\n    indented code\n    more code\n\n"
            "[a]: http://x\n[b]: http://y\n\n> quote one\n>\n> quote two\n\n---\n\nA line that ends in a break  \nand goes on.\n"
        )
        self.assertEqual(lines("a.md", text), [])

    def test_a_fence_inside_a_quote_is_still_a_fence(self) -> None:
        self.assertEqual(lines("a.md", "> ```\n> one\n> two\n> ```\n"), [])


class HtmlTest(unittest.TestCase):
    def test_text_broken_inside_an_element_is_named(self) -> None:
        self.assertEqual(lines("p.html", "<main>\n<p>The queue retries three times and\n   then gives up.</p>\n</main>\n"), [3])

    def test_one_line_text_passes(self) -> None:
        self.assertEqual(lines("p.html", "<main>\n  <p>One paragraph, however long.</p>\n  <p>Another.</p>\n</main>\n"), [])

    def test_code_script_and_style_keep_their_lines(self) -> None:
        text = "<style>\nbody {\n  margin: 0;\n}\n</style>\n<pre>a\nb</pre>\n<script>\nlet a = 1;\nlet b = 2;\n</script>\n"
        self.assertEqual(lines("p.html", text), [])


class WidthCapTest(unittest.TestCase):
    def test_a_cap_on_the_page_or_its_text_is_named(self) -> None:
        css = "<style>\n.shell { max-width: 860px; }\np, li { max-width: 65ch; }\n.prose { max-inline-size: 40em; }\nh1 { width: 30ch; }\n</style>\n"
        self.assertEqual(lines("p.html", css), [2, 3, 4, 5])
        self.assertEqual(lines("p.css", ".prose { max-width: min(72ch, 100%); }\n"), [1])

    def test_an_inline_style_cap_is_named(self) -> None:
        self.assertEqual(lines("p.html", '<p style="max-width: 600px">text</p>\n'), [1])

    def test_what_is_not_a_cap_passes(self) -> None:
        css = (
            "<style>\n@media (max-width: 900px) { .shell { gap: 0; } }\nimg { max-width: 100%; }\nsvg { min-width: 760px; width: 100%; }\n"
            ".a { max-width: none; }\n.grid { grid-template-columns: 190px minmax(0, 1fr); }\n</style>\n"
        )
        self.assertEqual(lines("p.html", css), [])

    def test_the_review_page_spec_caps_nothing(self) -> None:
        spec = (run.PLUGIN_ROOT / "docs" / "review-page.md").read_text()
        self.assertEqual(no_wrap.caps(spec), [])


class OtherFilesTest(unittest.TestCase):
    def test_code_and_data_are_not_prose(self) -> None:
        self.assertEqual(lines("a.py", "x = 1\ny = 2\n"), [])
        self.assertEqual(lines("a.json", '{\n"a": 1\n}\n'), [])


class HookTest(unittest.TestCase):
    def run_hook(self, event: dict) -> dict | None:
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO(json.dumps(event))), redirect_stdout(out):
            self.assertEqual(no_wrap.main(), 0)
        return json.loads(out.getvalue()) if out.getvalue() else None

    def decision(self, event: dict) -> str | None:
        reply = self.run_hook(event)
        return reply["hookSpecificOutput"]["permissionDecision"] if reply else None

    def test_a_wrapped_write_is_denied_and_says_where(self) -> None:
        event = {"tool_name": "Write", "tool_input": {"file_path": "/w/notes.md", "content": "One line and\nanother.\n"}}
        reply = self.run_hook(event)
        self.assertEqual(reply["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(reply["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("/w/notes.md:2", reply["hookSpecificOutput"]["permissionDecisionReason"])

    def test_a_flowing_write_is_let_through(self) -> None:
        self.assertIsNone(self.decision({"tool_name": "Write", "tool_input": {"file_path": "/w/notes.md", "content": "One line.\n"}}))

    def test_a_capped_page_is_denied(self) -> None:
        page = "<style>\nmain { max-width: 860px; }\n</style>\n<main><p>Text.</p></main>\n"
        self.assertEqual(self.decision({"tool_name": "Write", "tool_input": {"file_path": "/w/r.html", "content": page}}), "deny")

    def test_an_edit_answers_for_the_lines_it_writes_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text("# T\n\nAn old paragraph that was\nwrapped before.\n\nStatus: draft\n")
            clean = {"file_path": str(path), "old_string": "Status: draft", "new_string": "Status: final"}
            self.assertIsNone(self.decision({"tool_name": "Edit", "tool_input": clean}))
            wrapped = {"file_path": str(path), "old_string": "Status: draft", "new_string": "Status: final, and\nmore to say"}
            self.assertEqual(self.decision({"tool_name": "Edit", "tool_input": wrapped}), "deny")

    def test_an_edit_inside_a_fence_is_let_through(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text("# T\n\n```\nold line\n```\n")
            edit = {"file_path": str(path), "old_string": "old line", "new_string": "new line\nand another"}
            self.assertIsNone(self.decision({"tool_name": "Edit", "tool_input": edit}))

    def test_other_tools_and_bad_input_are_let_through(self) -> None:
        self.assertIsNone(self.decision({"tool_name": "Bash", "tool_input": {"command": "printf 'a\\nb' > x.md"}}))
        out = io.StringIO()
        with mock.patch("sys.stdin", io.StringIO("not json")), redirect_stdout(out):
            self.assertEqual(no_wrap.main(), 0)
        self.assertEqual(out.getvalue(), "")

    def test_the_plugin_registers_the_hook_for_write_and_edit(self) -> None:
        hooks = json.loads((run.PLUGIN_ROOT / "hooks" / "hooks.json").read_text())["hooks"]["PreToolUse"]
        self.assertEqual([h["matcher"] for h in hooks], ["Write|Edit"])
        self.assertIn("no_wrap.py", hooks[0]["hooks"][0]["command"])


class GraderTest(unittest.TestCase):
    def record(self, tmp: str, before: dict[str, str], after: dict[str, str]) -> run.RunRecord:
        for root, files in (("before", before), ("after", after)):
            for rel, text in files.items():
                path = Path(tmp) / root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
        (Path(tmp) / "before").mkdir(exist_ok=True)
        rec = mock.Mock(spec=run.RunRecord)
        rec.before_dir, rec.fixture_dir = Path(tmp) / "before", Path(tmp) / "after"
        return rec

    def test_a_wrapped_new_file_fails_and_is_named(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rec = self.record(tmp, {}, {"architecture/compliance.md": "A gap that is\nwrapped.\n"})
            ok, why = run.grade({"type": "flowing_text"}, rec)
        self.assertFalse(ok)
        self.assertIn("architecture/compliance.md:2", why)

    def test_a_capped_new_page_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rec = self.record(tmp, {}, {"reviews/a-review.html": "<style>\n.prose { max-width: 72ch; }\n</style>\n"})
            ok, why = run.grade({"type": "flowing_text"}, rec)
        self.assertFalse(ok)
        self.assertIn("reviews/a-review.html:2", why)

    def test_lines_the_fixture_already_held_are_not_the_agents(self) -> None:
        old = "# T\n\nAn old paragraph that was\nwrapped before.\n"
        with tempfile.TemporaryDirectory() as tmp:
            rec = self.record(tmp, {"ARCHITECTURE.md": old, "same.md": old}, {"ARCHITECTURE.md": old + "\nOne new line.\n", "same.md": old})
            ok, _ = run.grade({"type": "flowing_text"}, rec)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
