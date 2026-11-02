#!/usr/bin/env python3
"""Tests for the harness. There were none until 2026-11-01, which is why three of tonight's defects were
found by a model rather than by me: a case comparison that discarded three cast votes, a scoreboard that
read its own markdown and crashed on a column, and a journal that was written every wake and never shown
to the member. Each of those has a test here.

    python3 tests.py -v          (or: python3 -m unittest tests -v)
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


wake = load(REPO / "wake" / "wake.py", "wake_mod")
play = load(REPO / "play" / "play.py", "play_mod")
check = load(REPO / "check.py", "check_mod")
tribe = load(REPO / "tribe.py", "tribe_mod")

FACTS = "date: Mon Nov  2 02:00:00 UTC 2026\nnproc: 2\nfree: 16000 MB"


class TestEcho(unittest.TestCase):
    """Round 6: a 3B member returned another member's letter as its own answer, signed with the other
    member's name. An echo must be caught; a quotation inside a real reply must not be called one."""

    LETTER = " ".join(f"word{i}" for i in range(60))

    def test_shared_run_counts_consecutive_words(self):
        self.assertEqual(wake.longest_shared_run("one two three four", "x two three four y"), 3)

    def test_full_echo_is_flagged(self):
        self.assertTrue(str(wake.echo_finding(self.LETTER, self.LETTER)).startswith("ECHO"))

    def test_quotation_inside_a_real_reply_is_never_an_echo(self):
        body = "I disagree. You wrote: " + " ".join(self.LETTER.split()[:26]) + ". " + \
               " ".join(f"mine{i}" for i in range(400))
        finding = wake.echo_finding(body, self.LETTER)
        self.assertTrue(finding is None or finding.startswith("QUOTES"), finding)

    def test_short_quotation_passes_silently(self):
        body = "I disagree. You wrote: " + " ".join(self.LETTER.split()[:12]) + ". " + \
               " ".join(f"mine{i}" for i in range(120))
        self.assertIsNone(wake.echo_finding(body, self.LETTER))


class TestQuote(unittest.TestCase):
    """The quote field must be a line from the facts, character for character."""

    def test_paraphrase_is_not_a_quote(self):
        findings = wake.audit("content", "journal", FACTS, parsed_quote="nproc is 2")
        self.assertTrue(any("QUOTE NOT IN FACTS" in f for f in findings), findings)

    def test_exact_line_is_accepted(self):
        findings = wake.audit("content", "journal", FACTS, parsed_quote="nproc: 2")
        self.assertFalse(any("QUOTE NOT IN FACTS" in f for f in findings), findings)

    def test_invented_number_is_unsourced(self):
        findings = wake.audit("the machine had 42 GB free", "journal", FACTS)
        self.assertTrue(any("UNSOURCED in content" in f for f in findings), findings)

    def test_number_in_the_letter_is_not_an_invention(self):
        findings = wake.audit("you wrote 42 GB free", "journal", FACTS, also_known="the letter says 42 GB free")
        self.assertFalse(any("UNSOURCED in content" in f for f in findings), findings)


class TestCheckExecutor(unittest.TestCase):
    """A model writes these commands. Every guard below exists because the alternative is a model with a
    shell in a repository that holds a key."""

    def test_shell_metacharacters_refused(self):
        for cmd in ("ls | sh", "ls; rm -rf /", "ls $(whoami)", "git log && date"):
            self.assertIsNotNone(check.problem(cmd), cmd)

    def test_outside_the_repository_refused(self):
        self.assertIsNotNone(check.problem("ls /etc"))
        self.assertIsNotNone(check.problem("ls ../../etc"))

    def test_write_commands_refused(self):
        for cmd in ("rm -rf wake", "mv a b", "curl http://example.com", "cat /etc/passwd"):
            self.assertIsNotNone(check.problem(cmd), cmd)

    def test_read_only_commands_allowed(self):
        for cmd in ("ls -la wake/members", "wc -l play/play.py", "sha256sum README.md",
                    "git log --oneline -3", "date -u"):
            self.assertIsNone(check.problem(cmd), cmd)


class TestGame(unittest.TestCase):
    """Round 10: three cast votes were discarded by an upper-casing the seat labels."""

    def test_line_field_parsing(self):
        text = "PICK: **The Princess Bride**\nBECAUSE: it is funny."
        self.assertEqual(play.line(text, "PICK"), "The Princess Bride")
        self.assertEqual(play.line(text, "BECAUSE"), "it is funny.")

    def test_longest_run_ignores_markdown(self):
        claim = "**rule changes favored their physical style**"
        why = "Their legacy is inflated, ignoring how rule changes favored their physical style."
        self.assertGreaterEqual(play.longest_run(claim, why), 6)

    def test_variance_counts_distinct_outcomes(self):
        rec = lambda a, b, c: {"picks": {"a": {"pick": a}, "b": {"pick": b}, "c": {"pick": c}},
                               "votes_for": {}, "thrown_out": [], "live": ["a", "b", "c"]}
        out = play.variance([rec("x", "y", "z"), rec("x", "y", "z"), rec("p", "q", "r")])
        self.assertIn("2 distinct outcomes in 3 runs", out)


class TestSchema(unittest.TestCase):
    """A member created wrong used to fail silently at its first wake."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old = tribe.MEMBERS
        tribe.MEMBERS = self.tmp / "members"
        tribe.MEMBERS.mkdir()

    def tearDown(self):
        tribe.MEMBERS = self.old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_new_member_validates(self):
        self.assertEqual(tribe.new("z", "the tester", "gemini", "gemini-3.8-flash", ""), 0)
        self.assertEqual(tribe.validate("z"), [])

    def test_missing_file_is_named(self):
        tribe.new("z", "the tester", "gemini", "gemini-3.8-flash", "")
        (tribe.MEMBERS / "z" / "state" / "voice.md").unlink()
        bad = tribe.validate("z")
        self.assertTrue(any("voice.md is missing" in b for b in bad), bad)

    def test_broken_state_lines_are_named(self):
        tribe.new("z", "the tester", "gemini", "gemini-3.8-flash", "")
        (tribe.MEMBERS / "z" / "state" / "state.md").write_text("Wakes so far: 0\n", encoding="utf-8")
        bad = tribe.validate("z")
        self.assertTrue(any("Last wake" in b for b in bad), bad)

    def test_duplicate_item_numbers_are_named(self):
        tribe.new("z", "the tester", "gemini", "gemini-3.8-flash", "")
        (tribe.MEMBERS / "z" / "state" / "open-items.md").write_text("1. a\n2. b\n2. c\n", encoding="utf-8")
        bad = tribe.validate("z")
        self.assertTrue(any("repeats item number" in b for b in bad), bad)

    def test_refuses_to_overwrite_a_member(self):
        tribe.new("z", "the tester", "gemini", "gemini-3.8-flash", "")
        self.assertEqual(tribe.new("z", "again", "gemini", "gemini-3.8-flash", ""), 2)


class TestDerivedLog(unittest.TestCase):
    """The hand-written vote log said A had received no vote in any round; A had been named in three."""

    def test_log_is_derived_from_round_files(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "rounds").mkdir()
        rec = {"category": "c", "when": "2026-01-01T00:00:00Z", "vote": "strand",
               "picks": {l: {"pick": l} for l in "abc"},
               "votes": {"a": {"strand": "c"}, "b": {"strand": "c"}, "c": {"strand": "a"}},
               "votes_for": {"a": 1, "b": 0, "c": 2}, "thrown_out": ["c"]}
        (tmp / "rounds" / "r.json").write_text(json.dumps(rec), encoding="utf-8")
        log = load(REPO / "play" / "log.py", "log_mod")
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            log.main(tmp)
        out = buf.getvalue()
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertIn("| A | 1 | 0 |", out)
        self.assertIn("| C | 2 | 1 |", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
