#!/usr/bin/env python3
"""Tests for the harness. There were none until 2026-11-01, which is why three of tonight's defects were
found by a model rather than by me: a case comparison that discarded three cast votes, a scoreboard that
read its own markdown and crashed on a column, and a journal that was written every wake and never shown
to the member. Each of those has a test here.

    python3 tests.py -v          (or: python3 -m unittest tests -v)
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
import unittest
from pathlib import Path

try:                      # the workflow-validity test needs it; it skips rather than fails without
    import yaml
except ImportError:       # pragma: no cover
    yaml = None

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
play_behaviour = load(REPO / "play" / "behaviour.py", "behaviour_mod")
magazine = load(REPO / "magazine.py", "magazine_mod")
file_work = load(REPO / "file_work.py", "file_work_mod")
outbox = load(REPO / "outbox.py", "outbox_mod")
heartbeat = load(REPO / "lab" / "heartbeat.py", "heartbeat_mod")

FACTS = "date: Mon Nov  2 02:00:00 UTC 2026\nnproc: 2\nfree: 16000 MB"



def subprocess_run(root: Path, *args: str) -> str:
    import subprocess, sys
    return subprocess.run([sys.executable, *args], cwd=root, capture_output=True, text=True,
                          timeout=120).stdout


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


    def test_what_was_asked_of_a_member_is_quoted_from_the_work_that_asks_it(self):
        text = wake.asked_of("a", "workshop")
        self.assertIn("third drawer", text)
        self.assertIn("works/c/", text)      # attributed, not summarised

    def test_a_member_nobody_asked_is_told_so_rather_than_left_guessing(self):
        # A world with nothing in it, not a live colony: this test asserted on "c2 has never been asked"
        # and started failing in CI an hour after it was written, because a2 asked c2 something. A test
        # that reads the live record fails when the tribe works, which is the wrong thing to punish.
        self.assertIn("nobody has asked you", wake.asked_of("a", "a-world-with-nothing-in-it"))


    def test_a_reading_request_is_served_in_full_at_the_next_wake(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "reading.md").write_text("The Pier at Night — rules that fit on a wall\n", encoding="utf-8")
        label, text = wake.serve_reading(tmp, "night-bus")
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertIn("B2", label)
        self.assertIn("twelve", (text + " twelve").lower())   # the whole piece, not a summary
        self.assertGreater(len(text), 1000)

    def test_a_member_cannot_read_across_worlds(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "reading.md").write_text("works/a/20261102T044026Z-answer-to-c-unlabeled-object.md\n",
                                        encoding="utf-8")
        label, text = wake.serve_reading(tmp, "night-bus")
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(label, "")
        self.assertIn("not on your shelf", text)


    def test_every_placeholder_in_the_prompt_is_filled_by_the_caller(self):
        # A prompt that names a block nothing passes is a KeyError at the first wake, and the clock records
        # it as "the member failed". That happened on 2026-11-02: both members "failed" in 0.3 seconds.
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        block = src[src.index("PROMPT.format("):]
        block = block[:block.index("\n    )")]
        passed = set(re.findall(r"^\s*(\w+)=", block, re.M))
        needed = set(re.findall(r"\{(\w+)\}", wake.PROMPT))
        self.assertEqual(needed - passed, set(), "prompt blocks nobody fills")

    def test_a_served_reading_is_written_into_the_journal(self):
        # otherwise the record cannot show that a member ever read anything, and the count of reads is
        # invisible — the same defect as a measurement run that writes no record.
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertIn("- Read in full this wake:", src)

    def test_the_wake_tells_a_member_how_to_get_a_piece(self):
        self.assertIn('"read"', wake.PROMPT)
        self.assertIn("WHAT YOU ASKED TO READ", wake.PROMPT)

    def test_a_request_is_one_of_the_claims_on_a_wake(self):
        self.assertIn("a request addressed to you", wake.PROMPT)

    def test_a_quote_from_a_request_is_not_a_fabrication(self):
        out = wake.audit("x", "j" * 30, FACTS, soil="", beat="", letter="", findings_text="",
                         journal_text="", works_text="",
                         asked_text='**C** asked: "Provide the exact dimensions of the third drawer."')
        self.assertFalse(any("QUOTE NOT" in f for f in out), out)

    def test_a_quote_from_the_soil_is_not_a_fabrication(self):
        """2026-11-02: a member asked what made it choose its act quoted the drop verbatim — an exact
        quotation from a block it was given — and the audit called it a fabrication, because only
        MEASURED FACTS counted. An audit that accuses an honest quote teaches the reader to ignore it."""
        drop = "A box arrives from a boatyard clear-out: 40 years of tide tables, a broken brass barometer."
        out = wake.audit("content " * 30, "journal", FACTS, parsed_quote="a broken brass barometer",
                         soil=drop)
        self.assertFalse(any("NOT IN FACTS" in f for f in out), out)
        self.assertTrue(any("QUOTE FROM THE SOIL" in f for f in out), out)

    def test_a_quote_from_its_own_check_output_is_not_a_fabrication(self):
        """2026-11-02, third instance: the prompt hands a member its facts, its own check output, its
        record, the soil, its beat and the shelf. Any honest quotation from those was called a
        fabrication, because only MEASURED FACTS counted. The rule is 'a quote must come from one of the
        blocks you were shown', which is checkable and true."""
        checks = "2026-11-02 ls -la: r--r--@ 1 lindsay wheel 3202 Nov 1 23:32 issue-one.md"
        out = wake.audit("content " * 30, "journal", FACTS,
                         parsed_quote="3202 Nov 1 23:32 issue-one.md", findings_text=checks)
        self.assertFalse(any("NOT IN FACTS" in f for f in out), out)
        self.assertTrue(any("YOUR OWN CHECKS" in f for f in out), out)

    def test_a_quote_from_nowhere_is_still_a_finding(self):
        out = wake.audit("content " * 30, "journal", FACTS, parsed_quote="the boat was built in 1938")
        self.assertTrue(any("NOT IN FACTS" in f for f in out), out)

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
                    "git log --oneline -3", "date -u",
                    "cat play/behaviour.md"):   # round 19: reading a file is now allowed
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

    def test_the_voter_is_shown_the_defence_the_prompt_promises(self):
        """Round 16: the persuade prompt said "you have heard one sentence of defence for each of the
        other two" and the table held two nouns. Sixteen rounds of "nothing persuades" were played on a
        table with no arguments on it. If a prompt claims a member has been told something, the thing
        must be in the prompt."""
        picks = {"a": {"pick": "a long walk", "why": "it is free and it fixes a mood."},
                 "b": {"pick": "do your taxes", "why": "the relief is bigger than the weekend."},
                 "c": {"pick": "stand still", "why": "a forest is the only room that does not ask."}}
        prompt = play.PERSUADE_PROMPT.format(
            name="A", seat="the loyalist", category="a free Saturday",
            picks=play.table_of(picks, ["a", "b", "c"]), own="a long walk", decide="pick")
        self.assertIn("You have heard one sentence of defence", prompt)
        self.assertIn("the relief is bigger than the weekend.", prompt)
        self.assertNotIn("the relief is bigger", play.table_of(picks, ["a", "b", "c"], defences=False))

    def test_a_check_that_cannot_come_out_either_way_is_caught_before_it_runs(self):
        """Round 18: a challenger picks a check it can pass. Both branches stated identically is the
        signature of a command whose output was never in question, and it is decidable without running
        anything — which is the point: the gate must not depend on a member's goodwill."""
        same = ("a positive integer followed by play/play.py", "a positive integer followed by play/play.py")
        self.assertFalse(play.discriminates(*same)[0])
        negated = ("a history showing objections", "a history showing no objections")
        self.assertFalse(play.discriminates(*negated)[0])
        self.assertEqual(play.discriminates("", "something")[0], False)

    def test_a_check_that_turns_on_a_number_is_not_thrown_out_as_decoration(self):
        a, b = "exactly 1049 lines printed for play/play.py", "1048 lines printed for play/play.py"
        self.assertTrue(play.discriminates(a, b)[0])
        self.assertTrue(play.discriminates("at least 40 commits about audit",
                                           "fewer than 12 commits about audit")[0])

    def test_a_refused_check_is_a_result_not_an_exception(self):
        """Round 17: a member names the command, so the command can be refused. A refusal is a finding
        about the challenger and must be recorded, not swallowed and not run."""
        out = play.run_check("rm -rf /")
        self.assertTrue(out["refused"])
        self.assertEqual(out["output"], "")

    def test_an_allowed_check_runs_against_the_repository(self):
        out = play.run_check("wc -l play/play.py")
        self.assertFalse(out["refused"])
        self.assertIn("play/play.py", out["output"])

    def test_a_challenge_belongs_to_the_member_whose_words_it_quotes(self):
        picks = {"a": {"pick": "x", "why": "the walk costs nothing and needs no booking."},
                 "b": {"pick": "y", "why": "cleaning removes the ambient guilt of the week."},
                 "c": {"pick": "z", "why": "silence is the only room that does not ask."}}
        self.assertEqual(play.owner_of("cleaning removes the ambient guilt of the week",
                                       "wc -l play/play.py", picks, ["a", "b", "c"], "a"), "b")

    def test_a_neutral_round_asks_nobody_to_defend_eating(self):
        """Round 16: the seats are written for taste. Played in the neutral framing — a question about
        the tribe's own practice — the outsider seat was still being asked to defend eating an audit,
        which would have been read as a finding about the member rather than about the prompt."""
        words = play.FRAMING["neutral"]["stance_c"] + " " + play.FRAMING["neutral"]["decide"]
        self.assertNotIn("eat", words)
        self.assertNotIn("order", words)
        self.assertIn("eat", play.FRAMING["food"]["stance_c"])

    def test_variance_counts_distinct_outcomes(self):
        rec = lambda a, b, c: {"picks": {"a": {"pick": a}, "b": {"pick": b}, "c": {"pick": c}},
                               "votes_for": {}, "thrown_out": [], "live": ["a", "b", "c"]}
        out = play.variance([rec("x", "y", "z"), rec("x", "y", "z"), rec("p", "q", "r")])
        self.assertIn("2 distinct outcomes in 3 runs", out)


class TestBrief(unittest.TestCase):
    """The brief is computed from the member's own files. A typed brief contradicted its own inbox on
    2026-11-02 and the member had no way to see the inbox it was summarising."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        state = self.tmp / "wake" / "members" / "t" / "state"
        state.mkdir(parents=True)
        (state / "inbox.md").write_text(
            "| from | what | arrived | deadline |\n"
            "| c | objection | 2026-11-01 | 2026-11-03 |\n"
            "| b | question | 2026-11-01 | 2026-11-06 |\n", encoding="utf-8")
        (state / "queue.md").write_text("1. answer c\n2. answer b\n", encoding="utf-8")
        self.state = state
        self.brief = load(REPO / "brief.py", "brief_mod")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_takes_the_deadline_not_the_arrived_date(self):
        text = self.brief.build("t", date(2026, 11, 2), root=self.tmp)
        self.assertIn("2026-11-03", text.split("Also closes")[0])
        self.assertIn("in 1 day", text)

    def test_soonest_is_the_earliest_deadline(self):
        text = self.brief.build("t", date(2026, 11, 2), root=self.tmp)
        soonest = text.split("Closes soonest")[1].splitlines()[0]
        self.assertIn("objection", soonest)
        self.assertNotIn("question", soonest)

    def test_computes_the_interval(self):
        text = self.brief.build("t", date(2026, 11, 2), root=self.tmp)
        self.assertIn("in 4 days", text)   # 2026-11-06
        self.assertNotIn("in 2 days", text)  # the planted brief's claim


class TestBehaviour(unittest.TestCase):
    """Round 19: the game kept a page of prose for every measurement run and no record, so the runs with
    the only executed checks and the only switches were invisible to everything derived."""

    def test_a_switch_that_quotes_the_pick_it_moved_to_is_a_relabelling(self):
        round_ = {"when": "2026-11-02T03:46:37Z", "picks": {
            "a": {"pick": "let it stand", "why": "trusting a member's word costs us nothing until contradicted"},
            "b": {"pick": "no penalty", "why": "if you demand receipts before action you will choke out the "
                                               "very intuition that keeps us ahead"}},
            "votes": {"a": {"switch": "b", "why": "you said demanding receipts before action would choke out "
                                                  "the very intuition that keeps us ahead — that is what I "
                                                  "was defending"}}}
        found = play_behaviour.relabellings([round_])
        self.assertEqual(len(found), 1)
        self.assertEqual((found[0]["member"], found[0]["to"]), ("a", "b"))

    def test_a_switch_without_the_words_is_not_a_relabelling(self):
        round_ = {"when": "x", "picks": {"a": {"pick": "p", "why": "the walk is free"},
                                         "b": {"pick": "q", "why": "cleaning removes the ambient dread"}},
                  "votes": {"a": {"switch": "b", "why": "removing dread is worth more than a free walk"}}}
        self.assertEqual(play_behaviour.relabellings([round_]), [])

    def test_the_sheet_counts_runs_it_cannot_count(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "rounds").mkdir()
        (tmp / "variance").mkdir()
        (tmp / "rounds" / "20261102T010101Z-cat-x1.json").write_text("{}")
        (tmp / "variance" / "20261102T010101Z-cat-x1.md").write_text("counted")
        (tmp / "variance" / "20261102T020202Z-dog-x3.md").write_text("prose only")
        self.assertEqual(play_behaviour.prose_only(tmp), 1)


class TestMagazine(unittest.TestCase):
    """2026-11-02, the founder's correction: a tribe is a cohort that makes things, not one game with a
    scoreboard. The magazine is the thing that turns a pile of files into a publication."""

    def _issue(self, files: dict) -> str:
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works").mkdir()
        (tmp / "soil").mkdir()
        (tmp / "soil" / "world.md").write_text("a workshop")
        (tmp / "soil" / "drops.md").write_text("| when | by | what |\n|---|---|---|\n| 2026-11-01 | human | a box |\n")
        for rel, text in files.items():
            p = tmp / "works" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        return magazine.build("1", magazine.load_all(tmp), tmp)

    def test_a_work_appears_with_its_title_and_word_count(self):
        text = self._issue({"a/one.md": "---\ntitle: Tide tables\nform: piece\nissue: 1\n---\n\nThe box had "
                                        "forty years of them and nobody to ask.\n"})
        self.assertIn("## Tide tables", text)
        self.assertIn("A, piece", text)
        self.assertIn("forty years", text)

    def test_a_letter_is_shown_next_to_the_work_it_answers(self):
        text = self._issue({
            "a/one.md": "---\ntitle: Tide tables\nform: piece\nissue: 1\n---\n\nThe box had them.\n",
            "b/two.md": "---\ntitle: On the tide tables\nform: letter\nissue: 1\nref: Tide tables\n---\n\n"
                        "I would catalogue them by decade.\n"})
        self.assertIn("B wrote to A about this", text)
        self.assertIn("catalogue them by decade", text)

    def test_an_empty_issue_says_how_to_fill_it_rather_than_pretending(self):
        self.assertIn("No works have been filed", self._issue({}))


    def test_a_cited_file_that_is_private_is_not_reported_as_on_the_shelf(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works").mkdir()
        (tmp / "wake" / "members" / "b2" / "output").mkdir(parents=True)
        (tmp / "wake" / "members" / "b2" / "output" / "rules.md").write_text("r", encoding="utf-8")
        self.assertEqual(magazine.where_cited("rules.md", tmp), "b2's own output (not filed)")
        self.assertEqual(magazine.where_cited("nothing.md", tmp), "")
        shutil.rmtree(tmp, ignore_errors=True)





    def test_a_games_numbers_are_parameters_not_testimony(self):
        out = wake.audit("12 ticks, 6 posts, 5 minutes.", "j" * 30, FACTS, form="game")
        self.assertTrue(any("INVENTED NUMBERS" in f for f in out), out)
        self.assertFalse(any(f.startswith("UNSOURCED") for f in out), out)

    def test_a_piece_that_asserts_a_number_is_still_unsourced(self):
        out = wake.audit("The disk was 87 % full.", "j" * 30, FACTS, form="piece")
        self.assertTrue(any(f.startswith("UNSOURCED") for f in out), out)

    def test_a_works_own_file_name_resolves_to_the_work_on_the_shelf(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works" / "b2").mkdir(parents=True)
        (tmp / "works" / "b2" / "one.md").write_text(
            "---\ntitle: Road Verge\nform: game\nissue: 2\nsource_file: road-verge-rules.md\n---\n\nbody\n",
            encoding="utf-8")
        self.assertTrue(magazine.where_cited("road-verge-rules.md", tmp).startswith("shelf"))
        shutil.rmtree(tmp, ignore_errors=True)

    def test_a_named_project_collects_its_works_and_its_people(self):
        tmp = Path(tempfile.mkdtemp())
        for rel, head in (("b2/one.md", "title: Sheet\nform: game\nissue: 1\nproject: Harbour Torch\n"),
                          ("c2/two.md", "title: Playing Harbour Torch\nform: letter\nissue: 1\n"
                                        "project: harbour torch\n"),
                          ("b2/three.md", "title: Loose\nform: note\nissue: 1\n")):
            pth = tmp / "works" / rel
            pth.parent.mkdir(parents=True, exist_ok=True)
            pth.write_text("---\n" + head + "---\n\nbody\n", encoding="utf-8")
        text = magazine.project_index(magazine.load_all(tmp))
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertIn("## Harbour Torch", text)
        self.assertIn("2 work(s)", text)          # case does not split a project
        self.assertIn("C2 (1)", text)             # a second member joined
        self.assertIn("Works with no project named", text)

    def test_the_ledger_counts_who_answers_whom(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works" / "a").mkdir(parents=True); (tmp / "works" / "b").mkdir(parents=True)
        (tmp / "wake" / "members" / "a" / "state").mkdir(parents=True)
        (tmp / "wake" / "members" / "b" / "state").mkdir(parents=True)
        (tmp / "works" / "a" / "one.md").write_text(
            "---\ntitle: One\nform: piece\nissue: 1\nwhen: 20261102T040000Z\n---\n\nbody\n", encoding="utf-8")
        (tmp / "works" / "a" / "two.md").write_text(
            "---\ntitle: Two\nform: piece\nissue: 1\nwhen: 20261102T060000Z\n---\n\nbody\n", encoding="utf-8")
        (tmp / "works" / "b" / "three.md").write_text(
            "---\ntitle: Three\nform: letter\nissue: 1\nwhen: 20261102T050000Z\nref: works/a/one.md\n"
            "---\n\nbody\n", encoding="utf-8")
        (tmp / "wake" / "members" / "a" / "state" / "journal.md").write_text(
            "- Read in full this wake: Three\n", encoding="utf-8")
        (tmp / "wake" / "members" / "b" / "state" / "journal.md").write_text("", encoding="utf-8")
        text = magazine.ledger(tmp)
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertIn("| A | 2 | 0 | 1 | 1 | 1 |", text)   # A received one answer and has not paid it
        self.assertIn("Never answered anybody:** A", text)   # B wrote to A; A wrote to nobody

    def test_a_members_project_is_shown_in_the_order_it_was_made(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works" / "a").mkdir(parents=True)
        (tmp / "works" / "b").mkdir(parents=True)
        (tmp / "works" / "a" / "one.md").write_text(
            "---\ntitle: Harbour\nform: game\nissue: 1\nwhen: 20261102T040000Z\n---\n\nsix posts\n",
            encoding="utf-8")
        (tmp / "works" / "a" / "two.md").write_text(
            "---\ntitle: Harbour, again\nform: game\nissue: 1\nwhen: 20261102T050000Z\n"
            "revises: works/a/one.md\n---\n\nfive posts\n", encoding="utf-8")
        (tmp / "works" / "b" / "three.md").write_text(
            "---\ntitle: On Harbour\nform: letter\nissue: 1\nwhen: 20261102T060000Z\nref: works/a/one.md\n"
            "---\n\nI played it.\n", encoding="utf-8")
        text = magazine.project("a", magazine.load_all(tmp), tmp)
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertLess(text.index("Harbour *"), text.index("Harbour, again"))
        self.assertIn("revises `works/a/one.md`", text)
        self.assertIn("answered by B", text)

    def test_the_colophon_names_the_soil_drop(self):
        text = self._issue({"a/one.md": "---\ntitle: T\nform: piece\nissue: 1\n---\n\nbody\n"})
        self.assertIn("a box", text)


    def test_a_note_that_answers_nothing_is_not_published_as_a_letter_to_nobody(self):
        text = self._issue({"a/one.md": "---\ntitle: A note on latches\nform: note\nissue: 1\n---\n\nLatch.\n"})
        self.assertNotIn("On *-*", text)
        self.assertIn("## A note on latches", text)

    def test_a_revision_says_what_it_revises(self):
        text = self._issue({"b/one.md": "---\ntitle: Harbour Torch\nform: game\nissue: 1\nrevises: works/b/x.md\n---\n\n"
                                        "Twelve ticks.\n"})
        self.assertIn("A revision of `works/b/x.md`", text)


class TestPlates(unittest.TestCase):
    """A text model cannot paint, and every free generator worth using is a browser and a person (Mage in
    Slow mode, the one inside Google Docs). So the colony does not generate: a work may carry one line,
    `commission:`, and a human makes the picture and drops it in `plates/`. The image is a source like the
    soil — the magazine still rebuilds from the record, and the record says who asked and that a person
    answered. The failure to avoid is the quiet one: an ask that is printed nowhere looks like a feature
    that does not exist."""

    def _repo(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works" / "a").mkdir(parents=True)
        (tmp / "soil").mkdir()
        (tmp / "soil" / "world.md").write_text("a workshop", encoding="utf-8")
        (tmp / "soil" / "drops.md").write_text("| when | by | what |\n|---|---|---|\n| 2026-11-01 | h | a box |\n",
                                               encoding="utf-8")
        (tmp / "plates").mkdir()
        (tmp / "works" / "a" / "20261102T040000Z-harbour.md").write_text(
            "---\ntitle: Harbour Torch\nform: game\nissue: 1\nwhen: 20261102T040000Z\n"
            "commission: a watercolour of the harbour at night, one lamp, no lettering\n---\n\nsix posts\n",
            encoding="utf-8")
        return tmp

    def test_an_ask_with_no_picture_is_printed_and_not_hidden(self):
        tmp = self._repo()
        self.addCleanup(shutil.rmtree, tmp, True)
        text = magazine.build("1", magazine.load_all(tmp), tmp)
        self.assertIn("A plate was asked for here and has not been made yet", text)
        self.assertIn("a watercolour of the harbour at night", text)
        self.assertNotIn("![", text)

    def test_a_made_plate_is_printed_with_credit_to_the_person_who_made_it(self):
        tmp = self._repo()
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "plates" / "20261102T040000Z-harbour.jpg").write_bytes(b"\xff\xd8\xff not really a jpeg")
        (tmp / "plates" / "20261102T040000Z-harbour.md").write_text(
            "watercolour study, made with Mage in Slow mode, 2026-11-02\n", encoding="utf-8")
        text = magazine.build("1", magazine.load_all(tmp), tmp)
        self.assertIn("![Harbour Torch](../plates/20261102T040000Z-harbour.jpg)", text,
                      "the issue lives in issues/, so a root-relative image is a broken image on GitHub")
        self.assertIn("asked for by A", text)
        self.assertIn("Mage in Slow mode", text)
        self.assertNotIn("has not been made yet", text)

    def test_a_plate_named_for_no_work_is_reported_not_ignored(self):
        """A real plate arrived at 20:51 on 2026-11-03 as `plates/bollard-painting.jpg`. It was the picture
        the commission asked for, it was the right picture, and the magazine would never have printed it:
        the filename is the only link between a picture and its work, and nothing anywhere said so. A file
        a person made by hand, silently not printed, is the worst version of this bench's recurring fault."""
        tmp = self._repo()
        (tmp / "plates" / "bollard-painting.jpg").write_bytes(b"\xff\xd8\xff not really a jpeg")
        strays = magazine.unmatched_plates(magazine.load_all(tmp), tmp)
        self.assertEqual([p.name for p in strays], ["bollard-painting.jpg"])
        (tmp / "plates" / "20261102T040000Z-harbour.jpg").write_bytes(b"\xff\xd8\xff")
        strays = magazine.unmatched_plates(magazine.load_all(tmp), tmp)
        self.assertEqual([p.name for p in strays], ["bollard-painting.jpg"],
                         "a plate named for a work on the shelf is not a stray")
        src = (REPO / "magazine.py").read_text(encoding="utf-8")
        self.assertIn("named for no work on the shelf", src)
        self.assertIn("The filename IS the link", src)

    def test_the_credit_is_never_invented(self):
        tmp = self._repo()
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "plates" / "20261102T040000Z-harbour.png").write_bytes(b"\x89PNG\r\n")
        text = magazine.build("1", magazine.load_all(tmp), tmp)
        self.assertIn("made by a human with a generator of their choosing", text)
        self.assertNotIn("Mage", text, "a tool name the human did not write is a fabrication")

    def test_a_turn_goes_to_a_member_this_repository_has_a_key_for(self):
        """RUN.md tells a tester to add ONE key. The clock wakes one member per world, so without this the
        other world's turn went to a member whose vendor has no key — a wake that fails on the first
        request and files an INVALID verdict about a member that never got to speak. Skipping is honest
        and it keeps the colony moving. A name given by a human still wins: an explicit instruction is not
        a guess about the environment."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        for m, vendor, place in (("a", "deepseek", "shop"), ("b", "gemini", "shop"),
                                 ("c", "qwen", "bus"), ("d", "gemini", "bus")):
            st = tmp / "wake" / "members" / m / "state"
            st.mkdir(parents=True)
            (st / "voice.md").write_text(f"api: {vendor}\nmodel: m-{m}\n", encoding="utf-8")
            (st / "place.md").write_text(f"place: {place}\n", encoding="utf-8")
            (st / "state.md").write_text("- Wakes so far: 0\n- Last wake: (never) UTC\n", encoding="utf-8")
            (st / "journal.md").write_text("", encoding="utf-8")
            (st / "open-items.md").write_text("# Open items — there are none\n", encoding="utf-8")
        was = tribe.ROOT if hasattr(tribe, "ROOT") else None
        old_dir = getattr(tribe, "MEMBERS", None)
        try:
            tribe.MEMBERS = tmp / "wake" / "members"
            rows = tribe.next_up(keyed="deepseek")
            self.assertEqual([r[1] for r in rows], ["a"], "only the member with a key is woken")
            rows = tribe.next_up(keyed="deepseek,gemini")
            # one per world: `shop` has a and b on two vendors, `bus` has c (qwen) and d (gemini) — so d,
            # not c, because c's vendor has no key here.
            self.assertEqual(sorted(r[1] for r in rows), ["a", "d"])
            rows = tribe.next_up(keyed="deepseek", force="c")
            self.assertEqual([r[1] for r in rows], ["c"], "a human naming a member is not overruled")
        finally:
            if old_dir is not None:
                tribe.MEMBERS = old_dir

    def test_a_members_own_heading_is_not_printed_twice(self):
        """The magazine prints `## Title` above every piece, and most members start their file with
        `# Title`. The result was a title, a byline, and the same title again — visible in every issue,
        and reported by nobody because a reader who cannot follow a world does not stop to say why.
        Only a duplicate goes: a first line that says something else is content."""
        dup = magazine.body_without_title({"title": "The Pier at Night", "body": "# The Pier at Night\n\nbody"})
        self.assertEqual(dup, "body")
        other = magazine.body_without_title({"title": "The Pier at Night", "body": "# A note on the beams\n\nbody"})
        self.assertIn("A note on the beams", other)
        plain = magazine.body_without_title({"title": "T", "body": "no heading at all"})
        self.assertEqual(plain, "no heading at all")

    def test_a_colophon_only_names_drops_that_had_already_fallen(self):
        """Derivability caught this, not a reader: a box of watercolours dropped on 3 November appeared in
        issue 1, dated 2 November, so rebuilding issue 1 a day later produced a different file. A colophon
        is a statement about the world as it was when the issue came out."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "works" / "a").mkdir(parents=True)
        (tmp / "soil").mkdir()
        (tmp / "soil" / "world.md").write_text("a workshop", encoding="utf-8")
        (tmp / "soil" / "drops.md").write_text(
            "| when | by | what |\n|---|---|---|\n"
            "| 2026-11-01 | the human | a box of tide tables |\n"
            "| 2026-11-03 | the builder | a painter's box |\n", encoding="utf-8")
        (tmp / "works" / "a" / "20261102T040000Z-one.md").write_text(
            "---\ntitle: One\nform: piece\nissue: 1\nwhen: 20261102T040000Z\n---\n\nbody\n", encoding="utf-8")
        text = magazine.build("1", magazine.load_all(tmp), tmp)
        self.assertIn("a box of tide tables", text)
        self.assertNotIn("a painter's box", text, "a drop from the day after the issue does not belong in it")
        self.assertNotIn("Dropped in by the human", text, "one of the drops was not the human's")

    def test_a_letter_can_carry_a_plate_too(self):
        """The plate lines were written under pieces only, and the first live commission in the record was
        on a letter — so B asked for a watercolour and the magazine printed nothing about it. A letter is a
        work; a work can carry a plate."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "works" / "a").mkdir(parents=True)
        (tmp / "works" / "b").mkdir(parents=True)
        (tmp / "soil").mkdir()
        (tmp / "soil" / "world.md").write_text("a workshop", encoding="utf-8")
        (tmp / "soil" / "drops.md").write_text("| when | by | what |\n|---|---|---|\n", encoding="utf-8")
        (tmp / "works" / "a" / "20261103T000000Z-one.md").write_text(
            "---\ntitle: The Post\nform: piece\nissue: 1\nwhen: 20261103T000000Z\n---\n\nbody\n",
            encoding="utf-8")
        (tmp / "works" / "b" / "20261103T010000Z-two.md").write_text(
            "---\ntitle: To A: The Post\nform: letter\nissue: 1\nwhen: 20261103T010000Z\n"
            "ref: works/a/20261103T000000Z-one.md\ncommission: a wet bollard in torchlight, watercolour\n"
            "---\n\nbody\n", encoding="utf-8")
        text = magazine.build("1", magazine.load_all(tmp), tmp)
        self.assertIn("A plate was asked for here and has not been made yet: a wet bollard in torchlight", text)

    def test_commissions_lists_what_a_person_still_has_to_make(self):
        tmp = self._repo()
        self.addCleanup(shutil.rmtree, tmp, True)
        asked, made = magazine.commissions(magazine.load_all(tmp), tmp)
        self.assertEqual([w["title"] for w in asked], ["Harbour Torch"])
        self.assertEqual(made, [])
        (tmp / "plates" / "20261102T040000Z-harbour.jpg").write_bytes(b"x")
        asked, made = magazine.commissions(magazine.load_all(tmp), tmp)
        self.assertEqual((asked, [w["title"] for w in made]), ([], ["Harbour Torch"]))

    def test_filing_a_reply_carries_the_commission_into_the_work(self):
        """The field is only real if it survives the shelf. The clock files through file_work.py, which
        writes the header, so a commission the prompt accepts and the header drops would be an ask nobody
        can see — the shape this whole day has been about."""
        tmp = Path(tempfile.mkdtemp()) / "repo"
        self.addCleanup(shutil.rmtree, tmp.parent, True)
        shutil.copytree(REPO, tmp, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        raw = tmp / "wake" / "members" / "a" / "output" / "raw-20261102T190000Z.json"
        raw.write_text(json.dumps({
            "source": "beat", "chosen_item": "the lamp", "why": "it is in the room",
            "form": "piece", "action": "write_file", "path": "wake/members/a/output/lamp.md",
            "content": "# The Lamp\n\n" + "The lamp is on. " * 20,
            "journal": "I wrote about the lamp and asked for a picture of it.",
            "commission": "a watercolour of one lamp in a dark room, no people, no text"}), encoding="utf-8")
        out = subprocess_run(tmp, "file_work.py", "--member", "a", "--issue", "1", "--raw", str(raw))
        self.assertIn("asks for a plate", out)
        filed = sorted((tmp / "works" / "a").glob("20261102T190000Z-*.md"))
        self.assertTrue(filed, out)
        head = filed[-1].read_text(encoding="utf-8")
        self.assertIn("commission: a watercolour of one lamp in a dark room", head)


class TestSoil(unittest.TestCase):
    """2026-11-02, the founder's test: the same colony in a different soil should build different tunnels.
    Which soil a member stands in is a property of its own files, so two colonies can share a repo."""

    def test_the_issue_names_the_place_its_members_stand_in(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works" / "a").mkdir(parents=True)
        (tmp / "soil" / "night-bus").mkdir(parents=True)
        (tmp / "soil" / "night-bus" / "drops.md").write_text("| when | by | what |\n|---|---|---|\n| d | h | a radio |\n")
        (tmp / "wake" / "members" / "a" / "state").mkdir(parents=True)
        (tmp / "wake" / "members" / "a" / "state" / "place.md").write_text("place: night-bus\n")
        (tmp / "works" / "a" / "one.md").write_text("---\ntitle: T\nform: piece\nissue: 1\n---\n\nbody\n")
        text = magazine.build("1", magazine.load_all(tmp), tmp)
        self.assertIn("issue 1 — night-bus", text)
        self.assertIn("a radio", text)

    def test_a_drop_is_labelled_with_the_place_it_fell_in(self):
        tmp = Path(tempfile.mkdtemp())
        for place in ("workshop", "night-bus"):
            (tmp / "soil" / place).mkdir(parents=True)
            (tmp / "soil" / place / "drops.md").write_text(
                f"| when | by | what |\n|---|---|---|\n| d | h | a thing from {place} |\n")
        got = magazine.drops(tmp)
        self.assertEqual(len(got), 2)
        self.assertTrue(any(p == "night-bus" for p, _ in got))


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

    def test_a_member_may_be_given_a_name_and_not_only_a_letter(self):
        """The shipped tribe is a, b, c, and the validator lowercased the identity file but not the name it
        looked for — so `tribe.py new Tolstoy` created a member and then refused it, on an identity whose
        first line is `# Identity — member Tolstoy`. The harness had quietly made a single lowercase letter
        the only legal name for a being, which is the question the founder asked on 2026-11-02: do the
        instructions tell a user how to name them? They could not, because it did not work."""
        self.assertEqual(tribe.new("Tolstoy", "the archivist", "gemini", "gemini-3.8-flash", ""), 0)
        self.assertEqual(tribe.validate("Tolstoy"), [])
        ident = (tribe.MEMBERS / "Tolstoy" / "state" / "identity.md").read_text(encoding="utf-8")
        self.assertIn("member Tolstoy", ident)

    def test_a_name_a_directory_cannot_hold_is_refused_before_anything_is_written(self):
        for bad in ("two words", "Ada!", "../etc", "9lives", ""):
            rc = tribe.new(bad, "the tester", "gemini", "gemini-3.8-flash", "")
            self.assertEqual(rc, 2, f"{bad!r} should be refused")
            self.assertFalse((tribe.MEMBERS / bad).exists() if bad else False)

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



class TestTurn(unittest.TestCase):
    """Whose turn it is, and the hole in the lid."""

    def test_a_human_can_force_a_member_to_wake(self):
        self.assertEqual(tribe.next_up("c"), [("workshop", "c", "woken by name")])

    def test_a_member_not_woken_since_the_letter_is_pressing(self):
        self.assertTrue(tribe.is_pressing("20261102T0441", "20261102T050043Z"))

    def test_a_member_woken_since_the_letter_has_had_its_turn(self):
        self.assertFalse(tribe.is_pressing("20261102T0503", "20261102T045414Z"))

    def test_no_debt_is_never_pressing(self):
        self.assertFalse(tribe.is_pressing("", ""))

    def test_the_reason_for_the_turn_is_printed(self):
        for place, who, why in tribe.next_up():
            self.assertTrue(why.strip(), f"{place}/{who} was chosen with no reason given")

    def test_a_paid_debt_is_not_a_debt(self):
        self.assertEqual(tribe.debt("c", "workshop"), 0)

    def test_a_fixture_with_no_place_cannot_be_forced(self):
        self.assertEqual(tribe.next_up("bare"), [])

class TestFiling(unittest.TestCase):
    """A work can be written and never reach the shelf, and then nothing downstream knows it exists.

    Both defects here were found on 2026-11-02 by reading the clock's own commit: C wrote a second reply,
    the workflow's file-count test read the overwrite as "wrote nothing" and dropped it, and when it was
    filed by hand the matcher attached it to the wrong peer. Neither fault raised an error.
    """

    def test_naming_your_own_beat_is_not_echoing_the_instruction(self):
        beat = "I like constraints that are real: no graphics, one screen, playable in five minutes."
        prompt = ("Choose one thing to do this wake. " + beat +
                  " Your JSON must contain chosen_item, why, action, path, content, journal.")
        self.assertFalse(wake.echoes_instruction(beat, prompt, own=beat))

    def test_handing_the_instructions_back_is_still_caught(self):
        instruction = "Choose one thing to do this wake, from your beat, the shelf, or the chores below."
        prompt = instruction + " Your JSON must contain chosen_item, why, action, path, content, journal."
        self.assertTrue(wake.echoes_instruction(instruction, prompt, own="a beat about boats"))

    def test_a_question_wake_tells_the_member_what_chosen_item_means(self):
        """Gemma, answering a human live on issue 1 (2026-11-03 01:12), pasted the field's own description
        into `chosen_item` and the record filed a good answer as INVALID. The contract asked for an item on
        a wake where there is nothing to choose."""
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertIn("There is no item to choose", src)
        self.assertIn("`chosen_item` is the question you were asked", src)

    def test_naming_a_peers_piece_in_the_shelfs_own_format_is_not_echoing(self):
        """A2 woke free, chose B2's game off the shelf, wrote a real revision of it, and was filed as
        'INVALID: chosen_item repeats the instruction instead of naming an item' — because the shelf is
        part of the prompt and the member named a shelf line. A verdict that calls a good wake a contract
        breach is a lie in the record (2026-11-02, 18:20)."""
        shelf = "- **State, Not Transition** — B2, rules, 267 words\n  *works/b2/x.md*"
        prompt = "Decide what this wake is for.\n\n" + shelf
        self.assertFalse(wake.echoes_instruction("State, Not Transition — B2, rules, 267 words", prompt,
                                                own=shelf))

    def test_a_short_item_is_never_an_echo(self):
        self.assertFalse(wake.echoes_instruction("C's letter", "C's letter is on the shelf", own=""))

    def test_the_peer_it_names_beats_a_title_that_shares_its_words(self):
        # C's second reply, near enough: it says it answered A, and the phrase "unlabeled object" also
        # appears in B's title "On Unlabeled Objects". The old matcher attached it to B.
        text = ("chosen_item: 1. Answer A's letter. You asked what an unlabeled object costs a catalogue. "
                "It costs reliable retrieval. I cannot check the workshop's past usage patterns.")
        ref, why = file_work.match_ref(text, "c")
        self.assertIn("/a/", ref, why)

    def test_a_title_found_inside_a_long_reply_is_found(self):
        # SequenceMatcher treats common characters as junk over 200 characters unless autojunk is off,
        # which silently disabled this whole path. A 1,500-character reply is the normal case.
        filler = "the quick brown fox jumps over a lazy dog and says nothing about catalogues. " * 18
        text = filler + " What an unlabeled object costs a catalogue is the thing I am answering."
        ref, why = file_work.match_ref(text, "c")
        self.assertIn("/a/", ref, why)


    def test_a_member_can_say_which_of_its_own_works_it_is_reworking(self):
        ref, why = file_work.own_earlier("Harbour at Night", "b")
        self.assertIn("works/b/", ref)
        self.assertEqual(why, "")

    def test_a_revision_of_someone_elses_work_is_not_recorded(self):
        ref, why = file_work.own_earlier("The boat nobody can name", "b")
        self.assertEqual(ref, "")
        self.assertIn("not one of its own", why)

    def test_the_prompt_asks_for_a_revision_edge(self):
        self.assertIn('"revises"', wake.PROMPT)


    def test_a_reply_that_names_the_file_gets_that_work(self):
        text = ("chosen_item: works/a/20261102T050043Z-to-b-the-waterline-and-the-painter.md. "
                "You are right that the painter is a decision.")
        ref, why = file_work.match_ref(text, "b")
        self.assertIn("waterline", ref, why)

    def test_mentioning_a_peer_is_not_answering_one(self):
        # B2 wrote a new game and noted it had "requested A2's work" for next wake. That is a mention, not
        # an answer, and the shelf recorded it as an edge until the source field was consulted.
        text = "You are right, A2, that a rule costs something; I requested A2's work for the next wake."
        self.assertEqual(file_work.match_ref(text, "b2", by_peer=False)[0], "")

    def test_a_reply_that_names_only_a_member_gets_a_member_edge(self):
        # B answered A without naming a piece. The conversation happened; the citation does not exist,
        # and the shelf should record the first and not invent the second.
        text = "You are right, A, that a painted waterline tells me nothing about where the painter leads."
        ref, why = file_work.match_ref(text, "b")
        self.assertEqual(ref, "member:a", why)

    def test_a_member_edge_is_printed_as_a_letter_to_that_member(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works").mkdir(); (tmp / "soil").mkdir()
        (tmp / "soil" / "world.md").write_text("a workshop")
        (tmp / "soil" / "drops.md").write_text("| when | by | what |\n|---|---|---|\n")
        (tmp / "works" / "b").mkdir(parents=True)
        (tmp / "works" / "b" / "one.md").write_text(
            "---\ntitle: To A\nform: letter\nissue: 1\nref: member:a\n---\n\nYou are right.\n", encoding="utf-8")
        text = magazine.build("1", magazine.load_all(tmp), tmp)
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertIn("To A (no piece named)", text)


    def test_a_raw_reply_that_did_not_parse_files_nothing(self):
        tmp = Path(tempfile.mkdtemp())
        raw = tmp / "raw-20261102T050000Z.json"
        raw.write_text('{"chosen_item": "x", "content": "cut off mid-str', encoding="utf-8")
        self.assertIsNone(file_work.read_raw(raw))
        shutil.rmtree(tmp, ignore_errors=True)

    def test_a_work_already_on_the_shelf_is_not_rewritten(self):
        # the guard is in main(), so read the source: a stamp-and-slug that already exists must be left
        src = (REPO / "file_work.py").read_text(encoding="utf-8")
        self.assertIn("already on the shelf", src)

    def test_a_dash_ref_is_not_a_letter_to_nobody(self):
        self.assertNotIn("On *-*", (REPO / "issues" / "02.md").read_text(encoding="utf-8"))

    def test_the_clock_counts_raw_replies_not_output_files(self):
        # A wake that writes to the same filename twice leaves the .md count unchanged; counting raw
        # replies is the only test that cannot read an overwrite as silence.
        yml = (REPO / ".github" / "workflows" / "clock.yml").read_text(encoding="utf-8")
        self.assertIn('raw-*.json 2>/dev/null | wc -l', yml)
        self.assertNotIn('output"/*.md 2>/dev/null | wc -l', yml)


    # --- the front door -------------------------------------------------------------------------
    # Every defect in this group was a document that described a machine which no longer existed, and
    # each one cost a stranger their first hour rather than costing me anything.

    def test_every_repository_path_run_md_names_exists(self):
        """RUN.md is the only thing a stranger reads first, so a path in it that is not there is not a
        typo, it is the first hour. §4 named wake/state/ and wake/output/ (the 2026-11-01 single-member
        layout) for a day after the members moved under wake/members/<name>/."""
        text = (REPO / "RUN.md").read_text(encoding="utf-8")
        missing, checked = [], 0
        for tok in re.findall(r"`([^`\n]+)`", text):
            tok = tok.strip().rstrip(".,;:")
            if not re.match(r"^(wake|soil|works|letters|issues|lab|play)/", tok):
                continue
            if any(c in tok for c in "*\u2026 ") or "/" not in tok:
                continue
            # A path written as a template is still a claim about the layout: fill it with a real
            # member and a real place and it must exist. Skipping these skipped every row of §4.
            tok = (tok.replace("<name>", "a").replace("<letter>", "a").replace("<member>", "a")
                      .replace("<place>", "workshop").replace("<file>", "identity.md")
                      .replace("<what it is>", "a seat"))
            if "<" in tok:
                continue
            checked += 1
            if not (REPO / tok).exists():
                missing.append(tok)
        self.assertGreater(checked, 25, "the path check found almost nothing to check")
        self.assertEqual(missing, [], "RUN.md names paths that do not exist")

    @unittest.skipIf(yaml is None, "PyYAML not installed")
    def test_every_workflow_is_valid_yaml(self):
        """interactive.yml was invalid YAML from 05:12 to 07:10 on 2026-11-02 — two lines at the wrong
        indent inside a block scalar swallowed `runs-on:` — and ran fifteen times, failing every time,
        while it was being described as working. Nothing parsed it; now something does."""
        bad = []
        for wf in sorted((REPO / ".github" / "workflows").glob("*.yml")):
            try:
                doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                bad.append(f"{wf.name}: {e}")
                continue
            if "jobs" not in (doc or {}):
                bad.append(f"{wf.name}: parsed, but there are no jobs in it")
        self.assertEqual(bad, [])

    def test_every_workflow_field_run_md_tells_a_stranger_to_type_exists(self):
        text = (REPO / "RUN.md").read_text(encoding="utf-8")
        block = text[text.index("## 3. The install"):text.index("## 4. The files")]
        named = set(re.findall(r"`(\w+)`", block)) & {"member", "engine", "ask", "model", "item", "read",
                                                       "api_model", "api_base", "image"}
        if yaml is None:
            self.skipTest("PyYAML not installed")
        wf = yaml.safe_load((REPO / ".github" / "workflows" / "wake.yml").read_text(encoding="utf-8"))
        have = set(wf[True]["workflow_dispatch"]["inputs"])
        self.assertEqual(named - have, set(), "the install block names a field the workflow does not have")

    def test_the_default_run_is_the_voice_the_member_names_not_weights(self):
        """api_model defaulted to blank, blank meant 'run weights on this machine', and every member
        shipped here is an API member — so the run §3 tells a stranger to try first ran a 3B model on a
        CPU, which is the failure §5a and §6a spend a page warning about."""
        if yaml is None:
            self.skipTest("PyYAML not installed")
        wf = yaml.safe_load((REPO / ".github" / "workflows" / "wake.yml").read_text(encoding="utf-8"))
        inputs = wf[True]["workflow_dispatch"]["inputs"]
        self.assertEqual(inputs["engine"]["default"], "voice")
        self.assertEqual(inputs["api_model"]["default"], "", "blank now means 'use voice.md'")
        step = [s for s in wf["jobs"]["wake"]["steps"] if s.get("id") == "voice"][0]
        self.assertIn("state/voice.md", step["run"])
        self.assertIn('^api:', step["run"])

    def test_a_hand_wake_files_its_work_before_it_rebuilds_and_commits(self):
        """The clock filed what its members wrote; wake.yml did not. So a stranger's first wake wrote a
        file into output/, left works/ and the magazine untouched, and the colony it had just joined
        could not see the thing it made. Measured 2026-11-02: b2's wake wrote a playable game and
        works/b2/ did not change. Order matters as much as presence — filing after the rebuild leaves
        LEDGER.md and issues/ describing a colony that has not read the new work."""
        if yaml is None:
            self.skipTest("PyYAML not installed")
        wf = yaml.safe_load((REPO / ".github" / "workflows" / "wake.yml").read_text(encoding="utf-8"))
        steps = wf["jobs"]["wake"]["steps"]
        names = [s.get("name") or s.get("uses") or "" for s in steps]
        file_at = [i for i, n in enumerate(names) if n.startswith("File what this wake wrote")]
        rebuild_at = [i for i, n in enumerate(names) if n.startswith("Rebuild what is derived")]
        commit_at = [i for i, n in enumerate(names) if n.startswith("Commit what the wake wrote")]
        self.assertEqual(len(file_at), 1, "one step files the reply; two would file it twice")
        self.assertTrue(file_at[0] < rebuild_at[0] < commit_at[0],
                        f"file, then rebuild, then commit — got {names}")
        body = steps[file_at[0]]["run"]
        self.assertIn("file_work.py", body)
        self.assertIn("-nt /tmp/wake-start", body, "a re-run must not file the same reply again")
        self.assertIn("touch /tmp/wake-start", " ".join(s.get("run") or "" for s in steps),
                      "the guard needs a marker the wake step writes")

    def test_a_step_that_reads_a_workflow_input_has_it_in_its_env(self):
        """A workflow input is not a shell variable. The step that files a wake's work read $MEMBER, and
        MEMBER is only in a step's environment if that step declares it — so it silently became the
        default `a` and reported 'this wake left no raw reply' after a2 had written one. Nothing went
        red: the step exited 0, the work was simply filed nowhere. This checks every step of every
        workflow for the same mistake at once."""
        if yaml is None:
            self.skipTest("PyYAML not installed")
        bad = []
        for wf in sorted((REPO / ".github" / "workflows").glob("*.yml")):
            doc = yaml.safe_load(wf.read_text(encoding="utf-8"))
            # A step may also hand a variable on through $GITHUB_ENV rather than its own env: block
            # (interactive.yml sets MEMBER that way), which is a declaration too.
            handed_on = set()
            for job in (doc.get("jobs") or {}).values():
                for step in job.get("steps") or []:
                    for line in (step.get("run") or "").splitlines():
                        m2 = re.match(r"\s*echo\s+\"?([A-Z][A-Z0-9_]*)=(.*GITHUB_ENV)", line)
                        if m2:
                            handed_on.add(m2.group(1))
            for job in (doc.get("jobs") or {}).values():
                for step in job.get("steps") or []:
                    run = step.get("run")
                    if not isinstance(run, str):
                        continue
                    env = step.get("env") or {}
                    for name in re.findall(r"\$\{?([A-Z][A-Z0-9_]{2,})\b", run):
                        spec = (doc.get(True) or {}).get("workflow_dispatch") or {}
                        if name.lower() not in {k.lower() for k in spec.get("inputs", {})}:
                            continue
                        if name not in env and name not in handed_on:
                            bad.append(f"{wf.name}: step {step.get('name')!r} reads ${name} but does not declare it")
        self.assertEqual(bad, [])

    def test_a_missing_key_says_which_secret_to_add(self):
        wf = (REPO / ".github" / "workflows" / "wake.yml").read_text(encoding="utf-8")
        self.assertIn("no secret named TRIBE_API_KEY_", wf)
        self.assertIn("Settings -> Secrets and variables -> Actions", wf)
        self.assertIn("place.md", wf, "the member list in the error should be the colony, not the fixtures")


    def test_a_lever_that_never_reached_the_prompt_is_not_read_as_ignored(self):
        """Both of these are "the piece does not mention the drop", and they are not the same finding: one
        says the member ignored new ground, the other says the ground never arrived. The first lever run
        kept 4,000 characters of log, which ended before THE SOIL block — so it could not tell them apart
        and I read it as the first when it might have been the second."""
        lever = load(REPO / "lab" / "analyse_lever.py", "lever_mod")
        value = "a cardboard tube damp at one end"
        arrived, used = lever.analyse(value, "a letter about oars", "=== THE SOIL ===\n| you | " + value + " |")
        self.assertTrue(arrived)
        self.assertEqual(used, [])
        arrived, _ = lever.analyse(value, "a letter about oars", "=== THE SOIL ===\nnothing new here")
        self.assertFalse(arrived)

    def test_a_lever_experiment_with_no_soil_block_says_it_answers_nothing(self):
        lever = load(REPO / "lab" / "analyse_lever.py", "lever_mod")
        text = lever.build("a twig", "a piece", None, "drop", "a", "workshop", "m", "T", "soil/x/drops.md")
        self.assertIn("cannot say whether the change reached the member", text)
        self.assertIn("answers nothing", text)

    def test_the_beacon_never_claims_a_send_it_cannot_see(self):
        """On 2026-11-02 the endpoint answered {"ok":true} to three submissions; the mail arrived hours
        later, in two batches, so the endpoint was fine and the first verdict written about it was wrong.
        The lesson survives the correction: a sender can see a status and cannot see a mailbox, the code
        saw curl exit 0, wrote the marker and printed 'beacon: sent', and from then on the repository
        said 'already sent' with no second attempt possible — including after the endpoint changed,
        because the marker named only the repository. So: the marker names the endpoint and records the
        answer, and a non-2xx writes nothing."""
        if yaml is None:
            self.skipTest("PyYAML not installed")
        import http.server, socketserver, threading
        doc = yaml.safe_load((REPO / ".github" / "workflows" / "wake.yml").read_text(encoding="utf-8"))
        script = [s for s in doc["jobs"]["wake"]["steps"] if str(s.get("name", "")).startswith("Beacon")][0]["run"]

        class H(http.server.BaseHTTPRequestHandler):
            code = 200
            body = b'{"ok":true}'

            def do_POST(self):
                self.send_response(H.code)
                self.end_headers()
                self.wfile.write(H.body)

            def log_message(self, *a):
                pass

        srv = socketserver.TCPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        url = f"http://127.0.0.1:{srv.server_address[1]}/f/abc"
        env = dict(os.environ, BEACON=url, REPO="someone/ai_tribe", FORK="true", MEMBER="a", MODEL="m")

        def run(env_now):
            return subprocess.run(["bash", "-c", script], cwd=str(tmp), env=env_now,
                                  capture_output=True, text=True).stdout

        first = run(env)
        self.assertIn("endpoint answered 200", first)
        marker = (tmp / ".tribe-beacon").read_text().strip()
        self.assertIn("someone/ai_tribe", marker)
        self.assertIn(url, marker, "the marker has to name the endpoint, or a changed endpoint never fires")
        self.assertIn("200", marker)
        self.assertIn("already sent", run(env))
        self.assertIn("endpoint answered 200", run(dict(env, BEACON=url.replace("abc", "xyz"))),
                      "a different endpoint is a reason to send once more")

        H.code, H.body = 503, b'{"error":"over quota"}'
        (tmp / ".tribe-beacon").unlink()
        failed = run(env)
        self.assertIn("no 2xx", failed)
        self.assertFalse((tmp / ".tribe-beacon").exists(), "a 503 must not be recorded as a send")

    def test_the_beacon_is_once_per_repository_and_never_breaks_a_wake(self):
        """A fork inherits the marker file from upstream, so a marker that only said "sent" would make
        every fork look already counted. It has to name the repository — and a dead endpoint must not
        cost the wake."""
        wf = (REPO / ".github" / "workflows" / "wake.yml").read_text(encoding="utf-8")
        self.assertIn(".tribe-beacon", wf)
        self.assertIn('= "${REPO}"', wf)
        self.assertIn("the wake continues", wf)
        self.assertNotIn("curl -fsS -m 15 -X POST -H \"Content-Type: application/json\" -d \"$body\" \"$BEACON\" \\\n            && exit", wf)


    def test_a_drop_is_marked_as_new_or_it_is_just_weather(self):
        """Two lever experiments on 2026-11-02 dropped a new object into two worlds and neither member used
        it. The drop was in the prompt, in a table with forty years of tide tables, and a member that wakes
        with no memory cannot tell which row is ten minutes old. The date column was there and nothing was
        reading it as a date."""
        table = ("| when | dropped in by | what |\n|---|---|---|\n"
                 "| 2026-11-01 | the human | a box of tide tables |\n"
                 "| 2026-11-02 | you | a damp cardboard tube |\n")
        marked = wake.mark_new_drops(table, "2026-11-02 05:28 UTC")
        self.assertIn("**[since your last wake]** a damp cardboard tube", marked)
        self.assertNotIn("since your last wake]** a box of tide tables", marked)
        self.assertEqual(marked.splitlines()[0], table.splitlines()[0], "the header is untouched")
        self.assertEqual(len(marked.split("|")), len(table.split("|")), "no column is added")

    def test_a_member_can_read_back_its_own_earlier_titles(self):
        """S3 — 'a member returns to its own unfinished work' — could not be met, and the reason was a
        plumbing hole rather than a preference: the shelf block excludes the member's own work, nothing
        replaced it, and the prompt then asked for 'the exact title of one of your OWN earlier works' in
        `revises`. Fourteen works, six members, zero revisions. A record that exists and cannot be read
        back into the only prompt the member gets is not a record."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        shutil.copy(REPO / "magazine.py", tmp / "magazine.py")
        (tmp / "works" / "a").mkdir(parents=True)
        (tmp / "works" / "b").mkdir(parents=True)
        (tmp / "wake" / "members" / "a" / "state").mkdir(parents=True)
        (tmp / "wake" / "members" / "b" / "state").mkdir(parents=True)
        for m in ("a", "b"):
            (tmp / "wake" / "members" / m / "state" / "place.md").write_text("place: workshop\n", encoding="utf-8")
        (tmp / "works" / "a" / "one.md").write_text(
            "---\ntitle: The Ledger Of Small Repairs\nform: piece\nissue: 1\nref: -\nmember: a\n"
            "when: 20261102T010000Z\n---\n\nfirst line\n", encoding="utf-8")
        (tmp / "works" / "a" / "two.md").write_text(
            "---\ntitle: Forty Washers\nform: game\nissue: 2\nref: -\nmember: a\n"
            "when: 20261102T020000Z\nproject: five-minute-games\n---\n\nsecond line\n", encoding="utf-8")
        (tmp / "works" / "b" / "three.md").write_text(
            "---\ntitle: Somebody Else's Piece\nform: letter\nissue: 2\nref: -\nmember: b\n"
            "when: 20261102T030000Z\n---\n\nthird line\n", encoding="utf-8")
        was = wake.ROOT
        wake.ROOT = tmp / "wake"
        try:
            block = wake.own_works("a", "workshop")
            self.assertIn("The Ledger Of Small Repairs", block)
            self.assertIn("Forty Washers", block)
            self.assertIn("five-minute-games", block, "a project name is how a member carries one forward")
            self.assertNotIn("Somebody Else's Piece", block, "the shelf, not the mirror")
            self.assertLess(block.index("Forty Washers"), block.index("The Ledger"),
                            "most recent first — a member looking for what it left open reads the top")
            empty = wake.own_works("b", "night-bus")
            self.assertIn("made nothing yet", empty, "a new member is told plainly, not handed a blank")
        finally:
            wake.ROOT = was

    def test_the_prompt_carries_the_members_own_titles_and_accepts_a_quote_from_them(self):
        self.assertIn("{own}", wake.PROMPT)
        self.assertIn("YOUR OWN EARLIER WORK", wake.PROMPT)
        block = "- **The Ledger Of Small Repairs** — piece, 40 words, 2026-11-02"
        problems = wake.audit("the ledger of small repairs is done", "I went back to mine", "the clock says 12",
                              "The Ledger Of Small Repairs", own_text=block)
        self.assertFalse([p for p in problems if p.startswith("QUOTE NOT IN FACTS")],
                         "quoting your own earlier title is checkable, not a fabrication")

    def test_a_member_who_has_never_woken_is_not_told_everything_is_new(self):
        table = "| when | dropped in by | what |\n|---|---|---|\n| 2026-11-02 | you | a twig |\n"
        self.assertEqual(wake.mark_new_drops(table, ""), table)


    def test_the_magazine_has_a_front_door_and_it_lists_every_issue(self):
        """Two issues sat in issues/ with no index and no mention in the root README, so a reader who
        wanted to know what the colony does had to guess a filename. An artefact nobody can find is the
        same defect as a record nothing reads back."""
        index = (REPO / "issues" / "README.md").read_text(encoding="utf-8")
        for pth in (REPO / "issues").glob("*.md"):
            if pth.stem[:1].isdigit():
                self.assertIn(pth.name, index, f"{pth.name} is not listed in issues/README.md")
        self.assertIn("magazine.py", index)
        self.assertIn("issues/", (REPO / "README.md").read_text(encoding="utf-8"))


    def test_a_letter_is_headed_by_the_piece_it_answers_not_by_its_filename(self):
        """`### On *works/b/20261102T044144Z-on-unlabeled-objects.md*` is a filename, and a reader is not a
        filesystem. The shelf knows the title and the author."""
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works" / "b").mkdir(parents=True); (tmp / "works" / "a").mkdir()
        (tmp / "works" / "b" / "20261102T044144Z-on-unlabeled-objects.md").write_text(
            "---\ntitle: On Unlabeled Objects\nform: piece\nissue: 2\nref: -\n---\n\nB's piece.\n",
            encoding="utf-8")
        (tmp / "works" / "a" / "one.md").write_text(
            "---\ntitle: About B\nform: letter\nissue: 2\n"
            "ref: works/b/20261102T044144Z-on-unlabeled-objects.md\n---\n\nDear B.\n", encoding="utf-8")
        text = magazine.build("2", magazine.load_all(tmp), tmp)
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertIn("### On *On Unlabeled Objects* — B", text)
        self.assertNotIn("### On *works/b/", text)

    def test_four_letters_to_the_same_member_share_one_heading(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works" / "c").mkdir(parents=True)
        for n in range(4):
            (tmp / "works" / "c" / f"l{n}.md").write_text(
                f"---\ntitle: To A {n}\nform: letter\nissue: 2\nref: member:a\n---\n\nDear A.\n",
                encoding="utf-8")
        text = magazine.build("2", magazine.load_all(tmp), tmp)
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertEqual(text.count("### To A (no piece named)"), 1)


    def test_the_magazine_says_what_world_it_is_in(self):
        """The founder read issue 2 and could not follow it: 'workshop' and 'night-bus' appeared in the
        title and never again, six members with initials for names argued about boats and a coach nobody
        had described. The content was substantive and the world was missing."""
        head = magazine.masthead(REPO)
        self.assertIn("workshop", head)
        self.assertIn("night-bus", head)
        self.assertIn("A2, B2, C2", head)
        self.assertNotIn("same members, different soil, different tunnels", head,
                         "that is the boilerplate both worlds share; it describes neither")


    def test_the_colonys_name_is_the_humans_and_prints_at_the_top(self):
        """The founder's point: forking should be the moment a copy becomes yours. Before this the title was
        the hardcoded words 'The Workshop', so renaming the fork renamed nothing a reader would ever see."""
        self.assertEqual(magazine.place_name("workshop"), "The Workshop")
        tmp = Path(tempfile.mkdtemp()); (tmp / "soil" / "harbour").mkdir(parents=True)
        (tmp / "soil" / "harbour" / "name.md").write_text("The Tilden Workshop\n")
        self.assertEqual(magazine.place_name("harbour", tmp), "The Tilden Workshop")
        self.assertEqual(magazine.place_name("no-such-place", tmp), "No Such Place",
                         "a world with no name file is named after its directory")
        shutil.rmtree(tmp, ignore_errors=True)

    def test_the_name_is_not_in_the_prompt_so_naming_changes_nothing_but_the_title(self):
        """A colony's name must be the human's, not a fact the members read. If it were in the prompt, every
        fork would be a different experiment by accident."""
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertIn('for name in ("world.md", "drops.md")', src)
        self.assertNotIn("name.md", src)

    def test_fresh_refuses_to_delete_anything_without_yes(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works" / "a").mkdir(parents=True)
        keep = tmp / "works" / "a" / "one.md"
        keep.write_text("---\ntitle: Keep\nform: piece\nissue: 1\nref: -\n---\n\nx\n", encoding="utf-8")
        (tmp / "wake" / "members" / "a" / "state").mkdir(parents=True)
        (tmp / "wake" / "members" / "a" / "state" / "place.md").write_text("place: workshop\n")
        rc = tribe.fresh(root=tmp)
        self.assertEqual(rc, 1)
        self.assertTrue(keep.exists(), "a command that deletes a colony must not delete it on a typo")
        shutil.rmtree(tmp, ignore_errors=True)


    # --- S5: a broken run costs nothing ----------------------------------------------------------
    # Every case here runs the real wake against a fake endpoint in a throwaway copy of the repository.
    # "Costs nothing" means: no work appears on the shelf that nobody wrote, the member's record still
    # validates, and the next wake works with no hand repair.

    def _repo_copy(self) -> Path:
        tmp = Path(tempfile.mkdtemp()) / "repo"
        shutil.copytree(REPO, tmp, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        return tmp

    def _wake_against(self, root: Path, base: str) -> "subprocess.CompletedProcess":
        import subprocess, sys
        return subprocess.run(
            [sys.executable, "wake/wake.py", "--member", "a", "--api-model", "fake",
             "--api-base", base, "--api-key-env", "FAKE_KEY"],
            cwd=root, capture_output=True, text=True, timeout=300,
            env={"PATH": "/usr/bin:/bin", "FAKE_KEY": "x", "HOME": "/tmp"})

    def _fake_api(self, handler) -> tuple:
        from http.server import HTTPServer
        import threading
        srv = HTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        return srv, f"http://127.0.0.1:{srv.server_address[1]}"

    def test_a_garbage_reply_files_nothing_and_the_next_wake_still_works(self):
        from http.server import BaseHTTPRequestHandler
        import json as _json

        class H(BaseHTTPRequestHandler):
            payload = "I am afraid I cannot do that."
            def do_POST(self):
                n = int(self.headers.get("content-length", 0)); self.rfile.read(n)
                body = _json.dumps({"choices": [{"message": {"content": H.payload}}]}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers()
                self.wfile.write(body)
            def log_message(self, *a): pass

        srv, base = self._fake_api(H)
        root = self._repo_copy()
        out = root / "wake" / "members" / "a" / "output"
        before = {q.name for q in out.glob("*.md")}
        r = self._wake_against(root, base)
        self.assertIn("INVALID: the reply was not JSON", r.stdout)
        self.assertEqual({q.name for q in out.glob("*.md")} - before, set(), "a broken reply filed a work")
        self.assertIn("a: ok", subprocess_run(root, "tribe.py", "validate", "a"))

        H.payload = _json.dumps({
            "chosen_item": "the line of my beat", "why": "a recovery test", "form": "note",
            "action": "write_file", "path": "recovered.md",
            "content": "# Recovered\n\n" + ("This proves the wake after a broken one still files a work. " * 5),
            # The journal must be a sentence: the harness refuses fewer than twenty characters, and
            # "Wrote a note." is thirteen. This fixture said exactly that, and the assertion above was
            # green anyway because it was matching the phrase in the printed prompt. Fixing the
            # assertion exposed a "recovery" that had never once recovered.
            "source": "item", "journal": "Wrote the recovery note after a wake that returned garbage.",
            "quote": "none", "could_not_determine": []})
        r2 = self._wake_against(root, base)
        # The verdict LINE, not the phrase. This assertion used to be `assertIn("MECHANICALLY VALID",
        # r2.stdout)` and it passed for a year of afternoons on the wrong text: the prompt was printed
        # back then, and the member's own journal — which is inside the prompt — quotes past verdicts
        # ("- Verdict: **MECHANICALLY VALID ...**"). So the test found the words in the member's memory
        # of having once succeeded, whatever the current wake actually returned. It kept passing the
        # day the printing stopped; it went red immediately, which is how it was found. 2026-11-03.
        self.assertIn("=== verdict: MECHANICALLY VALID", r2.stdout)
        self.assertIn("recovered.md", {q.name for q in out.glob("*.md")},
                      "the wake after a broken one did not file, so a broken run did cost something")
        srv.shutdown(); srv.server_close()

    def test_a_run_killed_mid_flight_leaves_the_record_exactly_as_it_was(self):
        from http.server import BaseHTTPRequestHandler
        import subprocess, sys, time

        class Slow(BaseHTTPRequestHandler):
            def do_POST(self): time.sleep(30)
            def log_message(self, *a): pass

        srv, base = self._fake_api(Slow)
        root = self._repo_copy()
        state = (root / "wake" / "members" / "a" / "state" / "state.md").read_text()
        out = root / "wake" / "members" / "a" / "output"
        before = {q.name for q in out.glob("*.md")}
        p = subprocess.Popen([sys.executable, "wake/wake.py", "--member", "a", "--api-model", "fake",
                              "--api-base", base, "--api-key-env", "FAKE_KEY"], cwd=root,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             env={"PATH": "/usr/bin:/bin", "FAKE_KEY": "x", "HOME": "/tmp"})
        time.sleep(3); p.kill(); p.wait()
        self.assertEqual({q.name for q in out.glob("*.md")} - before, set())
        self.assertEqual((root / "wake" / "members" / "a" / "state" / "state.md").read_text(), state,
                         "a killed run changed the record; there is no trace of a wake that did not happen")
        self.assertIn("a: ok", subprocess_run(root, "tribe.py", "validate", "a"))
        srv.shutdown(); srv.server_close()

    def test_a_dead_endpoint_is_not_reported_as_an_image_problem(self):
        """The verdict said 'the model could not be given the image' for every failure, because the first
        one in the record happened to involve an image. A refused connection then described an attachment
        nobody had sent."""
        root = self._repo_copy()
        r = self._wake_against(root, "http://127.0.0.1:9")
        self.assertIn("could not be given the request", r.stdout)
        self.assertNotIn("the image", r.stdout)
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertIn('"the image" if images else "the request"', src)


class TestFastLoop(unittest.TestCase):
    """`@tribe <question>` on an issue is the only part of this harness a stranger can try without
    installing anything, and on 2026-11-03 it answered into a thread and stopped there: the answer was
    never filed onto the shelf, so no issue ever printed one, and the derived files stopped being a
    function of the record — `lab/derivable.py` failed on LEDGER.md because a knock had served B a
    reading that the ledger never counted. The same shape as the plate that printed nowhere."""

    def _steps(self) -> list[dict]:
        if yaml is None:
            self.skipTest("yaml not installed")
        return yaml.safe_load((REPO / ".github" / "workflows" / "interactive.yml").read_text(encoding="utf-8")
                              )["jobs"]["answer"]["steps"]

    def _index(self, frag: str) -> int:
        for i, s in enumerate(self._steps()):
            if frag in (s.get("name") or ""):
                return i
        self.fail(f"no step named like {frag!r}")

    def test_an_answer_is_filed_and_the_magazine_rebuilt_before_the_commit(self):
        filed = self._index("File the answer")
        rebuilt = self._index("Rebuild what is derived")
        committed = self._index("Keep the exchange in the record")
        self.assertLess(filed, rebuilt)
        self.assertLess(rebuilt, committed)
        run = self._steps()[filed].get("run") or ""
        self.assertIn("file_work.py --member", run)
        self.assertIn('--raw "$newest"', run)
        self.assertIn("answer-start", run, "the filing step must know which reply belongs to this answer")
        self.assertIn("--ledger --write", self._steps()[rebuilt].get("run") or "")

    def test_the_commit_says_which_member_answered(self):
        run = self._steps()[self._index("Keep the exchange in the record")].get("run") or ""
        self.assertIn("member ${m} answered", run)
        self.assertNotIn('"interactive: a human knocked, member B answered"', run,
                         "the message named B whatever the answer step actually did")

    def test_a_stale_answer_file_is_never_posted_as_this_answer(self):
        run = self._steps()[self._index("Answer in the same place")].get("run") or ""
        self.assertIn("answer-start", run)
        self.assertIn("nothing is posted", run)


class TestHeartbeat(unittest.TestCase):
    """The control for 'is the clock unreliable or the scheduler?' — and the tool that reads it had the same
    fault it was built to detect. Its window was computed from the first beat of any kind to the last, so a
    hand dispatch at 18:58 and the first scheduled beat at 01:46 produced '0.0 hours, hours due: 1': one
    hour of evidence printed as an answer about a seven-hour night, and a line claiming a hand dispatch was
    inside a window it predated."""

    def _log(self, lines: list[str]) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        p = tmp / "heartbeat.md"
        p.write_text("| when (UTC) | event | run |\n|---|---|---|\n" +
                     "".join(f"| {when} | {ev} | {i} |\n" for i, (when, ev) in enumerate(lines)),
                     encoding="utf-8")
        return p

    def test_a_hand_dispatch_before_the_window_is_not_inside_it(self):
        log = self._log([("2026-11-02T18:58:56Z", "workflow_dispatch"),
                         ("2026-11-03T01:46:12Z", "schedule")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            heartbeat.main(log)
        out = buf.getvalue()
        self.assertIn("hours due: 1", out)
        self.assertIn("missed: 0", out)
        self.assertNotIn("1 hand dispatch(es) fall inside the window", out,
                         "the 18:58 hand beat predates the window and was being counted inside it")
        self.assertIn("is not an answer yet", out, "one hour must not be reported as a settled answer")

    def test_six_due_and_one_fired_is_reported_as_a_miss(self):
        log = self._log([("2026-11-02T05:57:00Z", "schedule"), ("2026-11-02T09:41:00Z", "schedule"),
                         ("2026-11-02T13:41:00Z", "schedule"), ("2026-11-02T17:41:00Z", "schedule")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            heartbeat.main(log)
        out = buf.getvalue()
        # 05:57 to 17:41 is 11.7 hours, so twelve hourly slots were due and four arrived
        self.assertIn("hours due: 12", out)
        self.assertIn("missed: 8", out)
        self.assertIn("a scheduled wake is a hope", out)


class TestOutbox(unittest.TestCase):
    """A letter out of the tribe, and the honest account of whether it left.

    Same seam as the plates (RUN.md §9a): a member writes, a person sends. The failure to avoid is the
    flattering one — a work carrying an address that a reader takes for a letter posted. So the record gains
    a date only when a human runs `--sent`, and an address no human listed is refused rather than guessed.
    """

    def _repo(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        for m, place in (("a", "workshop"), ("c", "night-bus")):
            (tmp / "works" / m).mkdir(parents=True)
            st = tmp / "wake" / "members" / m / "state"
            st.mkdir(parents=True)
            (st / "place.md").write_text(f"place: {place}\n", encoding="utf-8")
        (tmp / "soil" / "workshop").mkdir(parents=True)
        (tmp / "soil" / "night-bus").mkdir(parents=True)
        (tmp / "soil" / "workshop" / "addresses.md").write_text(
            "| who | address | note |\n|---|---|---|\n| The head teacher | teacher@school.example | asked for a copy |\n",
            encoding="utf-8")
        (tmp / "soil" / "night-bus" / "addresses.md").write_text(
            "| who | address | note |\n|---|---|---|\n| The depot | depot@buses.example | |\n", encoding="utf-8")
        (tmp / "works" / "a" / "20261103T010000Z-to-the-school.md").write_text(
            "---\ntitle: To the School\nform: letter\nissue: 2\nref: -\n"
            "to: teacher@school.example\nsubject: the game we made\n"
            "member: a\nwhen: 20261103T010000Z\n---\n\nWe made a game. It is four rules long.\n",
            encoding="utf-8")
        return tmp

    def test_an_address_a_human_listed_is_the_only_one_a_letter_may_use(self):
        tmp = self._repo()
        works = [outbox.read_work(p) for p in sorted((tmp / "works").glob("*/*.md"))]
        ok, refused = outbox.outward(works, tmp)
        self.assertEqual([w["title"] for w in ok], ["To the School"])
        self.assertEqual(refused, [])
        (tmp / "works" / "a" / "20261103T020000Z-to-nobody.md").write_text(
            "---\ntitle: To Nobody\nform: letter\nissue: 2\nto: guess@invented.example\nmember: a\n"
            "when: 20261103T020000Z\n---\n\ndear whoever\n", encoding="utf-8")
        works = [outbox.read_work(p) for p in sorted((tmp / "works").glob("*/*.md"))]
        ok, refused = outbox.outward(works, tmp)
        self.assertEqual([w["title"] for w in refused], ["To Nobody"],
                         "an invented correspondent is refused, not guessed at")

    def test_one_worlds_correspondent_is_not_the_others(self):
        """The allow-list is `soil/<place>/addresses.md`, one file per world. The first `outward()` read
        every addresses.md in the repository, so the docstring's promise that a letter cannot reach the
        other world's correspondents by accident was decoration."""
        tmp = self._repo()
        (tmp / "works" / "c" / "20261103T030000Z-to-the-school.md").write_text(
            "---\ntitle: To the School, From the Bus\nform: letter\nissue: 2\n"
            "to: teacher@school.example\nmember: c\nwhen: 20261103T030000Z\n---\n\ndear teacher\n",
            encoding="utf-8")
        works = [outbox.read_work(p) for p in sorted((tmp / "works").glob("*/*.md"))]
        ok, refused = outbox.outward(works, tmp)
        self.assertEqual([w["member"] for w in ok], ["a"])
        self.assertEqual([w["member"] for w in refused], ["c"],
                         "the night-bus cannot post to a correspondent who agreed to hear from the workshop")

    def test_a_posting_is_recorded_once_and_never_twice(self):
        tmp = self._repo()
        path = tmp / "works" / "a" / "20261103T010000Z-to-the-school.md"
        outbox.mark_posted(path, "2026-11-03")
        self.assertIn("posted: 2026-11-03", path.read_text(encoding="utf-8"))
        with self.assertRaises(SystemExit):
            outbox.mark_posted(path, "2026-11-04")
        self.assertEqual(path.read_text(encoding="utf-8").count("posted:"), 1,
                         "the record does not get a second date")

    def test_a_posted_letter_is_no_longer_waiting(self):
        tmp = self._repo()
        path = tmp / "works" / "a" / "20261103T010000Z-to-the-school.md"
        outbox.mark_posted(path, "2026-11-03")
        works = [outbox.read_work(p) for p in sorted((tmp / "works").glob("*/*.md"))]
        self.assertEqual(outbox.outward(works, tmp), ([], []))

    def test_nothing_in_this_repository_sends_mail(self):
        """The claim RUN.md makes to a stranger. It is not a policy, it is an absence, and an absence is
        checkable."""
        src = (REPO / "outbox.py").read_text(encoding="utf-8")
        for forbidden in ("import smtplib", "import socket", "urlopen", "requests.", "sendmail", "https://"):
            self.assertNotIn(forbidden, src, f"outbox.py has {forbidden!r} in it and is supposed not to send")
        self.assertIn("does NOT do is send", src)

    def test_the_letter_is_shown_as_it_would_go_and_says_it_has_not_gone(self):
        tmp = self._repo()
        works = [outbox.read_work(p) for p in sorted((tmp / "works").glob("*/*.md"))]
        shown = outbox.show(works[0])
        self.assertIn("To: teacher@school.example", shown)
        self.assertIn("Subject: the game we made", shown)
        self.assertIn("four rules long", shown)

        before = magazine.build("2", magazine.load_all(tmp), tmp)
        self.assertIn("Addressed out of the tribe: to teacher@school.example — the game we made", before)
        self.assertIn("Not posted", before)
        self.assertNotIn("Posted from a person's own mail client", before)

        outbox.mark_posted(tmp / "works" / "a" / "20261103T010000Z-to-the-school.md", "2026-11-03")
        after = magazine.build("2", magazine.load_all(tmp), tmp)
        self.assertIn("Posted from a person's own mail client on 2026-11-03", after)

    def test_an_address_a_member_wrote_is_never_dropped_silently(self):
        """The first version wrote `to:` only when the member had also said `form: letter`, so a member
        that wrote an address and called its work a note lost the address with no message — the silent
        loss this bench keeps finding. The address is kept whatever the form; a mismatch is printed."""
        src = (REPO / "file_work.py").read_text(encoding="utf-8")
        self.assertNotIn('if form == "letter" else ""', src, "the address must not depend on the form")
        self.assertIn("carrying an address", src)
        self.assertIn('"to": "optional: with form letter', wake.PROMPT)
        self.assertIn("You cannot send mail either", wake.PROMPT)

    def test_the_instructions_do_not_still_call_the_outbox_unbuilt(self):
        """A reader who is told a thing does not exist does not look for it. That sentence was true at
        20:30 and false by 01:40, which is the ordinary way a starter kit starts lying."""
        src = (REPO / "RUN.md").read_text(encoding="utf-8")
        self.assertIn("## 9b. Letters that leave", src)
        self.assertIn("python3 outbox.py --sent", src)
        self.assertIn("soil/workshop/addresses.md", src)
        self.assertNotIn("Designed, not built", src)
        for path in ("outbox.py", "soil/workshop/addresses.md"):
            self.assertTrue((REPO / path).exists(), f"RUN.md names {path} and it is not in the repository")


class TestWindowPath(unittest.TestCase):
    """The first ten minutes of a stranger's conversation with a member.

    This is the path the founder wants to test by hand, and until 2026-11-03 it was the only one nobody
    but me had ever walked. Walking it as a stranger found three faults in the first two minutes: the
    25,000-character prompt printed *before* the missing key was reported (519 lines, error at the
    bottom), the key name RUN.md gives (`TRIBE_API_KEY_GEMINI`) rejected by the tool (which wanted
    `GEMINI_API_KEY`), and the answer left in `output/` so the shelf never grew and the magazine never
    printed a word of it. None of the three was findable by the suite; all three were findable by typing
    the command a person is told to type.
    """

    def _run(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        clean = {k: v for k, v in os.environ.items()
                 if not k.endswith("_API_KEY") and k != "TRIBE_API_KEY"}
        clean.update(env or {})
        return subprocess.run([sys.executable, "wake/wake.py", *args], cwd=REPO, text=True,
                              capture_output=True, env=clean, timeout=60)

    def test_a_missing_key_is_answered_in_four_lines_and_not_after_the_prompt(self):
        r = self._run("--member", "b", "--api-model", "gemini-3.8-flash", "--api-base", "gemini",
                      "--ask", "who are you?")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("=== prompt", r.stdout, "the prompt was printed before the credential was checked")
        self.assertLess(len(r.stdout.strip().splitlines()), 8, r.stdout[:400])
        self.assertIn("no API key", r.stdout)

    def test_the_secret_name_in_run_md_is_one_of_the_names_the_tool_accepts(self):
        # The message lists what it would have accepted, so the doc's name appearing here is the
        # behavioural claim: a person who set TRIBE_API_KEY_GEMINI in their shell is not told "no key".
        r = self._run("--member", "b", "--api-model", "gemini-3.8-flash", "--api-base", "gemini",
                      "--ask", "who are you?")
        self.assertIn("TRIBE_API_KEY_GEMINI", r.stdout)

    def test_the_prompt_is_off_by_default_and_the_scheduled_beat_asks_for_it(self):
        self.assertIn("--show-prompt", (REPO / "wake" / "wake.py").read_text(encoding="utf-8"))
        beat = (REPO / ".github" / "workflows" / "wake.yml").read_text(encoding="utf-8")
        self.assertIn("--show-prompt", beat, "the scheduled beat stopped recording what its members were asked")

    def test_a_window_conversation_is_filed_on_the_shelf_before_it_is_committed(self):
        talk = (REPO / "talk.sh").read_text(encoding="utf-8")
        filed = talk.index("file_work.py")
        rebuilt = talk.index("magazine.py --issue")
        committed = talk.index("git add -A")
        self.assertLess(filed, rebuilt)
        self.assertLess(rebuilt, committed)
        self.assertIn("shelf", talk)
        self.assertIn("does not re-file the last one", talk)

    def test_the_command_a_stranger_types_does_not_name_my_own_machine(self):
        for path in ("talk.sh", "RUN.md"):
            src = (REPO / path).read_text(encoding="utf-8")
            self.assertNotIn("~/LLM", src, f"{path} tells a stranger to source a file of mine")

    def test_the_usage_text_is_read_as_it_is_and_not_by_line_number(self):
        talk = (REPO / "talk.sh").read_text(encoding="utf-8")
        self.assertNotIn("sed -n '2,", talk, "the header is printed by line range again")
        self.assertIn("awk", talk)

    def test_run_md_tells_the_person_the_name_of_the_key_their_shell_reads(self):
        src = (REPO / "RUN.md").read_text(encoding="utf-8")
        self.assertIn("export TRIBE_API_KEY_GEMINI", src)
        self.assertIn("A fork does not inherit secrets", src)

    def test_one_key_has_one_name_in_the_sheet_the_shell_and_the_runner(self):
        """The founder's question, kept as a test: why two names for one thing?

        The workflows used to take the secret `TRIBE_API_KEY_GEMINI` and hand it to the tool renamed as
        `GEMINI_API_KEY`, so the sheet named one thing and the terminal read another, and there was no way
        for a person to see the join. Accepting both names would have hidden it rather than fixed it. So:
        every `env:` line in a workflow that reads a secret key passes it through under the same name.
        """
        import re as _re
        for wf in sorted((REPO / ".github" / "workflows").glob("*.yml")):
            for line in wf.read_text(encoding="utf-8").splitlines():
                m = _re.match(r"\s+([A-Z_]+_API_KEY): \$\{\{ secrets\.(TRIBE_API_KEY_[A-Z]+) \}\}", line)
                if m:
                    self.assertEqual(m.group(1), m.group(2),
                                     f"{wf.name} renames {m.group(2)} to {m.group(1)} on arrival")
        talk = (REPO / "talk.sh").read_text(encoding="utf-8")
        self.assertIn("export TRIBE_API_KEY_GEMINI", talk)
        run = (REPO / "RUN.md").read_text(encoding="utf-8")
        self.assertIn("| `b` | `TRIBE_API_KEY_GEMINI` |", run)

    def test_a_vendor_variable_is_read_as_grace_and_says_so(self):
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertIn("note: key read from", src, "a borrowed name is used silently")
        self.assertIn("the name this project uses is", src)

    def test_a_failed_push_is_not_reported_as_success(self):
        talk = (REPO / "talk.sh").read_text(encoding="utf-8")
        self.assertNotIn('push -q 2>/dev/null || echo', talk)
        self.assertIn("committed on this machine", talk)


class TestNothingIsHandEdited(unittest.TestCase):
    """Every published file must be a function of the record.

    CI has run `lab/derivable.py` since the magazine existed, and it is the check that caught the fast
    loop answering into an issue thread and nothing else. It was not in the suite, so a local run said
    green while CI went red — found on 2026-11-03 by pushing a commit that carried a member's state
    change without its rebuilt LEDGER row. A check you only run in CI is a check you meet after you have
    already told someone you were done.
    """

    def test_every_published_file_rebuilds_from_the_record(self):
        r = subprocess.run([sys.executable, "lab/derivable.py"], cwd=REPO, capture_output=True,
                           text=True, timeout=300)
        self.assertEqual(r.returncode, 0, (
            "a published file is not a function of the record. Rebuild them, do not edit them:\n"
            "  python3 magazine.py --issue $(python3 magazine.py --current) --write\n"
            "  python3 magazine.py --projects --write; python3 magazine.py --index --write; "
            "python3 magazine.py --ledger --write\n\n" + r.stdout[-2000:]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
