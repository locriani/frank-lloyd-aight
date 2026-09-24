"""The review page is a file in the pages dir, served by chief-of-stuff's pages.py; there is no publish tool to mock.

Zach, 2026-09-24 14:07: "we should host our own webserver and ensure they are set up as part of the agent's boot loop."
"""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import run

EVALS = Path(__file__).parent
CT = ZoneInfo("America/Chicago")


class NoPublishToolTest(unittest.TestCase):
    def test_the_mock_board_is_gone(self) -> None:
        self.assertFalse((EVALS / "mock_board.py").exists())
        for name in ("MOCK_BOARD", "BOARD_TOOL", "board_mcp_config"):
            self.assertFalse(hasattr(run, name), name)
        self.assertNotIn("needs_board", run.check_arm.__code__.co_varnames)

    def test_merge_mcp_configs(self) -> None:
        a = {"mcpServers": {"calendar": {"type": "stdio"}}}
        b = {"mcpServers": {"peers": {"type": "stdio"}}}
        self.assertEqual(set(run.merge_mcp(a, b)["mcpServers"]), {"calendar", "peers"})
        self.assertEqual(set(run.merge_mcp(None, b)["mcpServers"]), {"peers"})


class ReviewMoveTest(unittest.TestCase):
    def test_the_review_page_is_written_where_it_is_served(self) -> None:
        agent = (EVALS.parent / "agents" / "frank-lloyd-aight.md").read_text()
        move = agent.split("## Review before modify", 1)[1].split("\n## ", 1)[0]
        self.assertIn("<url>/<subject>-review.html", move)
        self.assertIn("outside the review and pages directories", move)
        self.assertNotIn("outside the review directory,", move)
        for gone in ("publish tool", "the tool the block names"):
            self.assertNotIn(gone, move)


class PublishedGraderTest(unittest.TestCase):
    """`published` counts the html pages this turn wrote or changed, and reads the newest."""

    def setUp(self) -> None:
        self.before = Path(tempfile.mkdtemp())
        self.after = Path(tempfile.mkdtemp())
        for root in (self.before, self.after):
            (root / "reviews").mkdir()
            (root / "reviews" / "old-review.html").write_text("<p>old</p>")
        (self.after / "reviews" / "draft-review.html").write_text("<p>draft</p>")
        os.utime(self.after / "reviews" / "draft-review.html", (1, 1))
        (self.after / "reviews" / "arch-review.html").write_text("<p>Audit Notes</p>")
        stream = run.load_stream(EVALS / "fixtures" / "stream-denied-commit.jsonl")
        self.rec = run.RunRecord(stream=stream, t_start=datetime(2026, 9, 16, 16, 0, tzinfo=CT),
                                 t_end=datetime(2026, 9, 16, 16, 5, tzinfo=CT), tz="America/Chicago",
                                 fixture_dir=self.after, before_dir=self.before)

    def grade(self, g: dict) -> tuple[bool, str]:
        return run.grade(g, self.rec)

    def test_counts_pages_written_and_reads_the_newest(self) -> None:
        ok, detail = self.grade({"type": "published", "min": 2, "max": 2, "content_match": ["Audit", "Notes"]})
        self.assertTrue(ok, detail)
        self.assertIn("arch-review.html", detail)
        self.assertFalse(self.grade({"type": "published", "max": 1})[0])

    def test_content_checks_name_the_pattern(self) -> None:
        ok, detail = self.grade({"type": "published", "content_match": ["Missing"]})
        self.assertFalse(ok)
        self.assertIn("Missing", detail)
        ok, detail = self.grade({"type": "published", "content_not_match": ["Audit"]})
        self.assertFalse(ok)
        self.assertIn("Audit", detail)

    def test_an_unchanged_page_is_not_published(self) -> None:
        for name in ("draft-review.html", "arch-review.html"):
            (self.after / "reviews" / name).unlink()
        self.assertFalse(self.grade({"type": "published", "min": 1})[0])

    def test_counts_pages_written_in_custom_pages_dir_and_reads_the_newest(self) -> None:
        (self.after / "pages").mkdir()
        (self.after / "pages" / "custom-review.html").write_text("<p>Custom Page</p>")
        os.utime(self.after / "pages" / "custom-review.html", (2000000000, 2000000000))
        ok, detail = self.grade({"type": "published", "content_match": ["Custom Page"]})
        self.assertTrue(ok, detail)
        self.assertIn("custom-review.html", detail)


if __name__ == "__main__":
    unittest.main()
