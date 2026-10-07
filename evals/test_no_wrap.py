"""Text is laid out by the renderer, never by the file: no line break inside prose, no cap on text width.

Zach, 2026-10-05: "you are not a word wrapping engine, it turns out that the zillions of lines of code spent on FONT LAYOUT are better than your awful random line breaks", and of a page capped at 860 pixels and 65 characters: "also page width caps. Yeah no".
"""

from __future__ import annotations

import io
import json
import re
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


    def test_a_longer_fence_holds_a_shorter_one(self) -> None:
        nested = "````markdown\n```\nline one\nline two\n```\n````\n"
        self.assertEqual(lines("a.md", nested), [])
        self.assertEqual(lines("a.md", nested + "\nA paragraph\nwrapped.\n"), [9])

    def test_a_quote_under_a_paragraph_is_its_own_block(self) -> None:
        self.assertEqual(lines("a.md", "A complete paragraph.\n> A separate one-line quote.\n"), [])


    def test_markdown_blocks_the_reviews_found_refused(self) -> None:
        for name, text in (
            ("a GitHub alert", "> [!NOTE]\n> One line of note text.\n"),
            ("a table with no leading pipe", "Name | Value\n--- | ---\na | b\n"),
            ("indented code in a quote", ">     first = 1\n>     second = 2\n"),
            ("a math block", "$$\nx = 1\ny = 2\n$$\n"),
            ("a comment over several lines", "<!--\na comment\nover lines\n-->\n"),
            ("a line ended with a break tag", "A line<br>\nanother.\n"),
            ("a fence line with text inside a fence", "```md\n```python\nx = 1\ny = 2\n```\n"),
        ):
            self.assertEqual(lines("a.md", text), [], name)

    def test_what_the_review_of_those_fixes_found_refused(self) -> None:
        self.assertEqual(lines("a.md", "Run:\n\n\t> make build\n\t> make test\n"), [], "tab-indented code that starts with >")
        self.assertEqual(lines("a.md", "---\ntitle: A\nauthor: B\n...\n\nBody.\n"), [], "front matter closed with three dots")

    def test_a_quote_inside_a_list_item_is_its_own_block(self) -> None:
        self.assertEqual(lines("a.md", "- item text\n    > quoted line\n"), [])
        self.assertEqual(lines("a.md", "1. item text\n    > quoted line\n"), [])
        self.assertEqual(lines("a.md", "- a\n    - b\n        > quoted\n"), [])
        self.assertEqual(lines("a.md", "- item text\n    continued here\n"), [2])

    def test_each_exemption_still_lets_a_wrap_be_named(self) -> None:
        for name, text, want in (
            ("after a tilde fence", "~~~\na\nb\n~~~\n\nA sentence\nwrapped.\n", [7]),
            ("after a one-line comment", "<!-- note -->\nA sentence\nwrapped.\n", [3]),
            ("after every spelling of a break tag", "A line<br/>\nb<br />\nc<BR>\nd\ne\n", [5]),
            ("under inline math", "$$x = 1$$\ncontinued\n", [2]),
            ("after a math fence nothing closes", "$$\n\nA sentence is\nwrapped here.\n", [4]),
            ("after a comment mark inside indented code", "    <!--\n    code\n\nA sentence is\nwrapped here.\n", [5]),
            ("in a quote, on an indented continuation", "> A sentence is\n>     wrapped here.\n", [2]),
        ):
            self.assertEqual(lines("a.md", text), want, name)

    def test_a_leading_rule_is_not_front_matter(self) -> None:
        self.assertEqual(lines("a.md", "---\nA sentence is\nwrapped here.\n"), [3])


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

    def test_a_cap_is_a_declaration_not_a_mention_or_a_media_query(self) -> None:
        self.assertEqual(lines("a.css", "@media ( max-width: 900px) { main { padding: 0; } }\n"), [])
        self.assertEqual(lines("a.css", "@media (\n  max-width: 900px\n) { main { padding: 0; } }\n"), [])
        self.assertEqual(lines("a.css", "/* max-width: 860px; is forbidden */\nmain { width: 100%; }\n"), [])
        self.assertEqual(lines("a.html", "<p>Do not use max-width: 860px; on this page.</p>\n"), [])
        self.assertEqual(lines("a.html", '<p style="max-width: 100%"><b style="font-size: 12px">text</b></p>\n'), [])
        self.assertEqual(lines("a.css", "main { max-width:\n  860px; }\n"), [1])
        self.assertEqual(lines("a.css", "@media (max-width: 900px) { main { max-width: 500px; } }\n"), [1])

    def test_what_the_reviews_found_refused_as_a_cap(self) -> None:
        self.assertEqual(lines("a.css", "main { max-width: calc(100% - 2rem); }\n"), [])
        self.assertEqual(lines("a.css", "@import url(x.css) (max-width: 600px);\n"), [])
        self.assertEqual(lines("a.css", "[style*='max-width: 10px'] { color: red; }\n"), [])
        self.assertEqual(lines("a.html", '<pre>&lt;p style="max-width: 600px"&gt;</pre>\n'), [])
        self.assertEqual(lines("a.html", '<p data-style="max-width: 600px">text</p>\n'), [])

    def test_each_exemption_still_lets_a_cap_be_named(self) -> None:
        self.assertEqual(lines("a.css", 'a::before{content:"["}main{max-width:600px}a::after{content:"]"}\n'), [1])
        self.assertEqual(lines("a.css", "main { max-width: calc(600px - 2rem); }\n"), [1])
        self.assertEqual(lines("a.css", "main { max-width: calc(100% - var(--g) - 2rem); }\n"), [])
        self.assertEqual(lines("a.html", '<div x-show="a > 1" style="max-width: 600px">text</div>\n'), [1])
        self.assertEqual(lines("a.html", '<p title="a < b" style="max-width: 600px">text</p>\n'), [1])
        self.assertEqual(lines("a.html", '<p\n  class="a"\n  style="max-width: 600px">text</p>\n'), [3])

    def test_a_style_value_with_an_entity_is_named_on_its_own_line(self) -> None:
        page = '<p\n class="a"\n style="font-family: &quot;A&quot;; max-width: 600px">t</p>\n'
        self.assertEqual(lines("a.html", page), [3])

    def test_an_inline_diagram_keeps_its_own_size_and_lines(self) -> None:
        # A rendered Mermaid diagram states its drawn size and its label widths in its own styles. That is the drawing, not the page's text.
        page = (
            '<div class="diagram"><svg style="max-width: 1738.77px">\n<foreignObject><div style="max-width: 200px">a label\nbroken</div></foreignObject>\n'
            '</svg></div>\n<p style="max-width: 60rem">text</p>\n'
        )
        self.assertEqual(lines("p.html", page), [5])

    def test_the_review_page_spec_caps_nothing(self) -> None:
        spec = (run.PLUGIN_ROOT / "docs" / "review-page.md").read_text()
        self.assertEqual(no_wrap.caps(spec), [])


    def test_the_plan_page_spec_caps_nothing(self) -> None:
        spec = (run.PLUGIN_ROOT / "docs" / "plan-page.md").read_text()
        self.assertEqual(no_wrap.caps(spec), [])
        self.assertEqual(no_wrap.markdown(spec), [])


class PageThemeTest(unittest.TestCase):
    def block(self, text: str, selector: str) -> str:
        match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", text)
        self.assertIsNotNone(match, selector)
        return match.group(1)

    def test_the_theme_file_exists_and_caps_nothing(self) -> None:
        path = run.PLUGIN_ROOT / "docs" / "page-theme.css"
        self.assertTrue(path.is_file())
        self.assertEqual(no_wrap.caps(path.read_text()), [])

    def test_the_theme_has_the_three_token_blocks(self) -> None:
        text = (run.PLUGIN_ROOT / "docs" / "page-theme.css").read_text()
        for selector in (":root {", "@media (prefers-color-scheme: dark) {", ':root:not([data-theme="light"])', ':root[data-theme="dark"]'):
            with self.subTest(selector=selector):
                self.assertIn(selector, text)

    def test_the_two_dark_blocks_hold_the_same_tokens(self) -> None:
        text = (run.PLUGIN_ROOT / "docs" / "page-theme.css").read_text()
        automatic = self.block(text, ':root:not([data-theme="light"])')
        explicit = self.block(text, ':root[data-theme="dark"]')
        declarations = r"(--[\w-]+|color-scheme)\s*:\s*([^;]+);"
        self.assertEqual(
            {(name, value.strip()) for name, value in re.findall(declarations, automatic)},
            {(name, value.strip()) for name, value in re.findall(declarations, explicit)},
        )

    def test_both_dark_blocks_set_color_scheme(self) -> None:
        text = (run.PLUGIN_ROOT / "docs" / "page-theme.css").read_text()
        for selector in (':root:not([data-theme="light"])', ':root[data-theme="dark"]'):
            with self.subTest(selector=selector):
                self.assertIn("color-scheme: dark;", self.block(text, selector))

    def test_the_theme_defines_the_review_tokens(self) -> None:
        text = (run.PLUGIN_ROOT / "docs" / "page-theme.css").read_text()
        light = self.block(text, ":root")
        tokens = (
            "--ground", "--ground-2", "--paper", "--ink", "--ink-2", "--muted", "--rule", "--deployed",
            "--inflight", "--inflight-soft", "--designed", "--designed-soft", "--warn", "--warn-soft",
            "--f-head", "--f-body", "--f-mono",
        )
        for token in tokens:
            with self.subTest(token=token):
                self.assertRegex(light, re.escape(token) + r"\s*:\s*[^;\s][^;]*;")

    def test_neither_spec_embeds_the_stylesheet(self) -> None:
        for name in ("review-page.md", "plan-page.md"):
            with self.subTest(name=name):
                text = (run.PLUGIN_ROOT / "docs" / name).read_text()
                self.assertNotIn("--ground:", text)
                self.assertNotIn("--accent:#1c6a49", text)

    def test_both_specs_name_the_theme_file(self) -> None:
        for name in ("review-page.md", "plan-page.md"):
            with self.subTest(name=name):
                text = (run.PLUGIN_ROOT / "docs" / name).read_text()
                self.assertIn("page-theme.css", text)


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

    def test_an_edit_does_not_answer_for_a_cap_on_the_line_below(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.css"
            path.write_text("body { color: red; }\nmain { max-width: 860px; }\n")
            unrelated = {"file_path": str(path), "old_string": "red", "new_string": "blue"}
            self.assertIsNone(self.decision({"tool_name": "Edit", "tool_input": unrelated}))
            capping = {"file_path": str(path), "old_string": "color: red", "new_string": "max-width: 40em"}
            self.assertEqual(self.decision({"tool_name": "Edit", "tool_input": capping}), "deny")

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

    def test_joining_two_fixture_paragraphs_is_the_agents_wrap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rec = self.record(tmp, {"a.md": "First paragraph.\n\nSecond paragraph.\n"}, {"a.md": "First paragraph.\nSecond paragraph.\n"})
            ok, why = run.grade({"type": "flowing_text"}, rec)
        self.assertFalse(ok)
        self.assertIn("a.md:2", why)

    def test_lines_the_fixture_already_held_are_not_the_agents(self) -> None:
        old = "# T\n\nAn old paragraph that was\nwrapped before.\n"
        with tempfile.TemporaryDirectory() as tmp:
            rec = self.record(tmp, {"ARCHITECTURE.md": old, "same.md": old}, {"ARCHITECTURE.md": old + "\nOne new line.\n", "same.md": old})
            ok, _ = run.grade({"type": "flowing_text"}, rec)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
