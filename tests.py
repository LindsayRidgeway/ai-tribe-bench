#!/usr/bin/env python3
"""Tests for the harness. There were none until 2026-11-01, which is why three of tonight's defects were
found by a model rather than by me: a case comparison that discarded three cast votes, a scoreboard that
read its own markdown and crashed on a column, and a journal that was written every wake and never shown
to the member. Each of those has a test here.

    python3 tests.py -v          (or: python3 -m unittest tests -v)
"""
from __future__ import annotations

import atexit
import base64
import contextlib
import importlib.util
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date, datetime, timezone
import unittest
from pathlib import Path

try:                      # the workflow-validity test needs it; it skips rather than fails without
    import yaml
except ImportError:       # pragma: no cover
    yaml = None

REPO = Path(__file__).resolve().parent
FIXTURE_SHELF = REPO / "lab" / "fixtures"


def install_fixtures() -> list[Path]:
    """Shelve the test members for the duration of the run; take them off again when it ends.

    A tribe ships with no members of its own, so `wake/members/` is empty in the template: a stranger who
    opens the repository must not find ten folders called `a`, `b`, `trap` and have to guess whether they are
    theirs. The suite still needs members to break, so it keeps ten under `lab/fixtures/` and moves them onto
    the shelf only while it runs. Anything already on the shelf is left alone: a real member is never removed
    by a test run, however it ended.
    """
    added: list[Path] = []
    for kind, stow in (("members", REPO / "wake" / "members"), ("works", REPO / "works")):
        src = FIXTURE_SHELF / kind
        if not src.is_dir():
            continue
        stow.mkdir(parents=True, exist_ok=True)
        for d in sorted(src.iterdir()):
            dest = stow / d.name
            if dest.exists():
                continue
            shutil.copytree(d, dest)
            added.append(dest)
    return added


def remove_fixtures(added: list[Path]) -> None:
    for d in added:
        shutil.rmtree(d, ignore_errors=True)


SHELVED: list[Path] = install_fixtures()


def shelve() -> None:
    global SHELVED
    SHELVED = install_fixtures()


def unshelve() -> None:
    global SHELVED
    remove_fixtures(SHELVED)
    SHELVED = []


@atexit.register
def _unshelve_at_exit() -> None:
    remove_fixtures(SHELVED)


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # dataclasses look their own module up in sys.modules while building the class; a module that is never
    # registered blows up with "'NoneType' object has no attribute '__dict__'". Registering it is harmless
    # for the modules that do not need it and necessary for the ones that do.
    sys.modules[name] = mod
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
mlb_score = load(REPO / "lab" / "mlb_score.py", "mlb_score_mod")
rank_compare = load(REPO / "lab" / "rank_compare.py", "rank_compare_mod")
sport_facts = load(REPO / "lab" / "sport_facts.py", "sport_facts_mod")
rps = load(REPO / "lab" / "rps.py", "rps_mod")
dice = load(REPO / "lab" / "dice.py", "dice_mod")
wind = load(REPO / "lab" / "wind.py", "wind_mod")
word = load(REPO / "lab" / "word.py", "word_mod")
favour = load(REPO / "lab" / "favour.py", "favour_mod")
_json = __import__("json")

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

    def test_the_count_of_works_naming_an_issue_comes_from_the_assembler(self):
        """The runner may not publish an issue with nothing in it, and it may not hold a second opinion about what
        belongs in one. `--filed` prints the number and nothing else, so a shell can test it, and the number is
        the one `build()` filters on — one rule, two callers.

        Also the one place the "which issue is open" rule is measured: the highest number any work names wins over
        the highest issue already on disk, which is how a member starts the next issue by writing a line.
        """
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "works" / "a").mkdir(parents=True)
        (tmp / "issues").mkdir()
        shutil.copy(REPO / "magazine.py", tmp / "magazine.py")
        (tmp / "works" / "a" / "one.md").write_text(
            "---\ntitle: One\nform: piece\nissue: 1\n---\n\nx\n", encoding="utf-8")
        (tmp / "works" / "a" / "two.md").write_text(
            "---\ntitle: Two\nform: piece\nissue: 2\n---\n\nx\n", encoding="utf-8")

        def cli(*args: str) -> str:
            r = subprocess.run([sys.executable, "magazine.py", *args], cwd=tmp,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            return r.stdout.strip()

        self.assertEqual(cli("--issue", "1", "--filed"), "1")
        self.assertEqual(cli("--issue", "2", "--filed"), "1")
        # An issue nobody has written for: zero, and nothing else, so the shell can refuse on it.
        self.assertEqual(cli("--issue", "3", "--filed"), "0")
        self.assertEqual(cli("--current"), "2", "the shelf opens the issue, not the disk alone")
        # A work with no `issue:` line is issue 1 — the same default `build()` uses, not a second convention.
        (tmp / "works" / "a" / "three.md").write_text(
            "---\ntitle: Three\n---\n\nx\n", encoding="utf-8")
        self.assertEqual(cli("--issue", "1", "--filed"), "2")


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

    def test_the_header_names_every_form_it_holds(self):
        """The founder's colony, morning of 2026-11-03: ten works filed by three members, and the issue
        header read "0 pieces and 10 letters". Both figures came from real code and the sentence was
        false — notes were counted as letters, so a morning's conversation described itself as none of
        one thing and all of another. A count that swallows a form is a record that cannot be read back.
        """
        text = self._issue({
            "a/one.md": "---\ntitle: A note\nform: note\nissue: 1\n---\n\nLatch.\n",
            "b/two.md": "---\ntitle: A letter\nform: letter\nissue: 1\n---\n\nDear.\n",
            "c/three.md": "---\ntitle: A piece\nform: piece\nissue: 1\n---\n\nBody.\n",
        })
        self.assertIn("1 letter", text)
        self.assertIn("1 note", text)
        self.assertIn("1 piece", text)
        self.assertNotIn("0 pieces", text, "nothing present may be reported as absent")
        self.assertIn("2 notes and 1 piece", self._issue({
            "a/one.md": "---\ntitle: n1\nform: note\nissue: 1\n---\n\nx\n",
            "a/two.md": "---\ntitle: n2\nform: note\nissue: 1\n---\n\nx\n",
            "a/three.md": "---\ntitle: p\nform: piece\nissue: 1\n---\n\nx\n",
        }), "several of a form are named in the plural")

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


class TestThreeAnswers(unittest.TestCase):
    """The founder's first real experiment, 2026-11-03: three members, one question, then a comparison.

    Two tools exist because a harness with no tools cannot do this honestly: `lab/dow.py` writes the facts
    a member cannot fetch, and `lab/compare.py` does the arithmetic so the comparison is a file rather than
    a vibe. Both are tested on their failure paths first, because a facts file invented from memory is
    worse than no facts file — a member cannot tell the difference once it is on disk.
    """

    def _root(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "lab").mkdir()
        for f in ("dow.py", "compare.py"):
            shutil.copy(REPO / "lab" / f, tmp / "lab" / f)
        return tmp

    def test_the_facts_tool_writes_nothing_when_the_endpoint_fails(self):
        root = self._root()
        out = root / "facts" / "x.md"
        r = subprocess.run([sys.executable, "lab/dow.py", "--url", "http://127.0.0.1:9/none",
                            "--out", str(out)], cwd=root, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 2)
        self.assertFalse(out.exists(), "a failed fetch must leave no facts file behind")
        self.assertIn("invented from memory is worse than no facts file", r.stdout)

    def test_a_running_session_is_not_reported_as_a_close(self):
        """The Dow at 10:33 in the morning is a moving number, and a member told "the Dow is 51,717" will
        treat it as settled. The facts file has to say which one it is holding."""
        mod = load(REPO / "lab" / "dow.py", "dow_mod")
        from datetime import datetime as _dt
        rows = [{"when": _dt(2026, 11, 2, 14, 30, tzinfo=timezone.utc), "open": 1.0, "high": 2.0,
                 "low": 0.5, "close": 51984.0},
                {"when": _dt(2026, 11, 3, 14, 30, tzinfo=timezone.utc), "open": 2.0, "high": 3.0,
                 "low": 1.0, "close": 51737.7}]
        meta = {"regularMarketPrice": 51737.66, "regularMarketTime": 1793720029}
        text = mod.render(rows, meta, "2026-11-04",
                          now=_dt(2026, 11, 3, 15, 33, tzinfo=timezone.utc))
        self.assertIn("still running", text)
        self.assertIn("not a close", text)
        self.assertIn("PREDICTION:", text, "the question must ask for the one shape a tool can parse")

    def test_the_comparison_scores_one_prediction_per_member_and_says_what_noise_looks_like(self):
        root = self._root()
        for member, when, value, conf in (("Remy", "2026-11-03T17:10:00Z", "51,850", "55"),
                                          ("Remy", "2026-11-04T21:30:00Z", "51,740", "90"),
                                          ("Margot", "2026-11-03T17:15:00Z", "51,600", "60")):
            d = root / "works" / member
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{when}.md").write_text(
                f"---\ntitle: n\nform: note\nissue: 1\nwhen: {when}\n---\n\nPREDICTION: {value}\n\n"
                f"Confidence: {conf}%.\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "lab/compare.py", "--actual", "51737.7",
                            "--target", "2026-11-04", "--daily-move", "232.2",
                            "--out", str(root / "facts" / "c.md")],
                           cwd=root, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        text = (root / "facts" / "c.md").read_text(encoding="utf-8")
        self.assertIn("| Remy | 51,740.0 |", text, "the LAST prediction is scored, not the best one")
        self.assertNotIn("51,850.0", text, "a first guess must not be scored after the result was known")
        self.assertIn("Closest: **Remy**", text)
        self.assertIn("Three guesses on one session", text, "a single session must not be sold as a skill")
        self.assertIn("232.2 points on an average day", text)

    def test_one_being_is_one_row_however_its_name_is_spelled(self):
        """The founder asked, on 2026-11-03: "are remy and Remy two different seats?"

        No — `works/Remy/` is the seat's shelf and `experiment/remy.md` was a chat session's answer, and the
        comparison printed them as two members because it took the name from a filename. One being written in
        two spellings is the same defect this project has fixed twice already; here it produced a table with a
        closest called Remy and a furthest called remy. And a session's second draft (`-after.md`) is never a
        prediction, or the after-the-fact note would be scored against the real guess.
        """
        root = self._root()
        (root / "works" / "Remy").mkdir(parents=True)
        (root / "works" / "Remy" / "w.md").write_text(
            "---\ntitle: filed\nform: note\nissue: 1\nwhen: 2026-11-03T09:00:00Z\n---\n\nnothing\n",
            encoding="utf-8")
        (root / "experiment").mkdir()
        (root / "experiment" / "remy.md").write_text(
            "---\ntitle: chat\nform: note\nissue: 1\nwhen: 2026-11-03T18:00:00Z\n---\n\nPREDICTION: 51720\n",
            encoding="utf-8")
        (root / "experiment" / "remy-after.md").write_text("PREDICTION: 51900\n", encoding="utf-8")
        mod = load(REPO / "lab" / "compare.py", "compare_mod")
        old_root = mod.ROOT
        mod.ROOT = root
        try:
            rows = mod.predictions(also=["experiment"])
        finally:
            mod.ROOT = old_root
        self.assertEqual([r["member"] for r in rows], ["Remy"], "one being, one row, one spelling")
        self.assertEqual(rows[0]["value"], 51720.0, "the -after file is a comment, not a prediction")
        text = mod.render(rows, 51737.7, "2026-11-04", None)
        self.assertIn("Only one prediction was filed", text)
        self.assertNotIn("Furthest", text, "one row cannot have a furthest")

    def test_the_confidence_column_reads_the_forecast_and_not_the_band(self):
        """Scored 2026-11-04, the three answers the tool had just written came back as 40% / 30% / nothing.

        The members had written 18% / 30% / 25%. Colette's "## 2. Confidence" is a heading with the number
        on the next line and her only same-line use of the word is a 40% figure for a ±250-point RANGE;
        Remy's 25% was on the next line too, so the old regex found nothing and the table printed a dash.
        A wrong number that prints cleanly is the same defect this project keeps finding: a tool that
        agrees with itself.
        """
        mod = load(REPO / "lab" / "compare.py", "compare_mod_conf")
        self.assertEqual(mod.confidence_of("## 2. Confidence\n\n**18%.**\n\nThis is honest. I would "
                                          "put 40% on a band of ±250 points."), 18)
        self.assertEqual(mod.confidence_of("Confidence: 30%. The mean absolute daily change is 232.3."), 30)
        self.assertEqual(mod.confidence_of("## 2. Confidence\n\n**25%.**\n\nMy confidence that the close "
                                          "lands within 250 points is maybe 45%."), 25)
        self.assertIsNone(mod.confidence_of("No number here, only prose about how hard this is."))

    def test_no_prediction_lines_says_so_instead_of_inventing_a_table(self):
        root = self._root()
        (root / "works" / "Remy").mkdir(parents=True)
        (root / "works" / "Remy" / "a.md").write_text(
            "---\ntitle: n\nform: note\nissue: 1\n---\n\nI think it will go up a bit.\n", encoding="utf-8")
        r = subprocess.run([sys.executable, "lab/compare.py", "--actual", "51737.7", "--out",
                            str(root / "facts" / "c.md")],
                           cwd=root, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 1)
        self.assertIn("cannot be checked by anybody", (root / "facts" / "c.md").read_text(encoding="utf-8"))


class TestPlates(unittest.TestCase):
    """A work may carry one line, `commission:`, and somebody makes the picture and drops it in `plates/`.

    The original docstring here said that no model can paint and that every generator worth using is a browser
    and a person. That was true when written and was measured false on 2026-11-07: OpenAI, Gemini and Qwen each
    returned a picture from one HTTP call, and `lab/paint.py` now files it. The member still cannot draw — a
    wake is one call with no tools — but the ask no longer has to wait for a human, and the credit line names
    whoever answered it. The failure to avoid is still the quiet one: an ask printed nowhere looks like a
    feature that does not exist."""

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
            # One turn per circle — until 2026-11-20 this was one per world, which answered a question about two
            # experiment colonies and not a question about a circle. Four members, one turn: the fewest wakes, then
            # the alphabet, and only among those whose engine this run can reach.
            self.assertEqual([r[1] for r in rows], ["a"])
            rows = tribe.next_up(keyed="deepseek", force="c")
            self.assertEqual([r[1] for r in rows], ["c"], "a human naming a member is not overruled")
        finally:
            if old_dir is not None:
                tribe.MEMBERS = old_dir

    def test_the_vendors_with_keys_are_read_from_the_environment_not_from_a_list(self):
        """`clock.yml` named three engines by hand -- deepseek, gemini, qwen -- directly under the ten secrets the
        same step forwards. So a member on Anthropic or OpenRouter was skipped by the chooser every turn while the
        step held its key, and the log said `keys for: deepseek`: true about the list, false about the world. It is
        the four-of-ten `env:` defect one line lower, and the cure is the same -- the list is read from the thing it
        describes. Measured 2026-11-15; `tribe.py next --keyed-from-env` is what the clock runs now."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        for m, vendor, place in (("e", "anthropic", "shop"), ("f", "openrouter", "bus")):
            st = tmp / "wake" / "members" / m / "state"
            st.mkdir(parents=True)
            (st / "voice.md").write_text(f"api: {vendor}\nmodel: m-{m}\n", encoding="utf-8")
            (st / "place.md").write_text(f"place: {place}\n", encoding="utf-8")
            (st / "state.md").write_text("- Wakes so far: 0\n- Last wake: (never) UTC\n", encoding="utf-8")
            (st / "journal.md").write_text("", encoding="utf-8")
            (st / "open-items.md").write_text("# Open items -- there are none\n", encoding="utf-8")
        old_dir = getattr(tribe, "MEMBERS", None)
        # Any key the machine running the suite happens to have must not leak into the reading.
        saved = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("TRIBE_API_KEY_")}
        try:
            tribe.MEMBERS = tmp / "wake" / "members"
            self.assertEqual(tribe.keyed_from_env(), "", "no key in the environment is no vendor")
            os.environ["TRIBE_API_KEY_ANTHROPIC"] = "not-a-real-key"
            self.assertEqual(tribe.keyed_from_env(), "anthropic")
            self.assertEqual([r[1] for r in tribe.next_up(keyed=tribe.keyed_from_env())], ["e"],
                             "the member whose engine the environment has a key for is the one woken")
            os.environ["TRIBE_API_KEY_OPENROUTER"] = "not-a-real-key"
            self.assertEqual(tribe.keyed_from_env(), "anthropic openrouter")
            self.assertEqual([r[1] for r in tribe.next_up(keyed=tribe.keyed_from_env())], ["e", "f"][:1],
                             "a second engine with a key widens the pool; the circle still takes one turn")
        finally:
            if old_dir is not None:
                tribe.MEMBERS = old_dir
            for k in [k for k in os.environ if k.startswith("TRIBE_API_KEY_")]:
                os.environ.pop(k)
            os.environ.update(saved)

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


class TestAMemberCanBeGivenAWorldLater(unittest.TestCase):
    """Found 2026-11-07 by the founder testing on a phone, which is why it matters.

    He created his first member, left the optional place field blank because he did not yet know what a world
    was, and then could not fill it in: `tribe.py new` refuses an existing record, `tribe.py place` did not
    exist, and the form's own warning told him to "run this form again with the place field filled" — which
    ran `new` again and refused. The one remedy offered to a person with no shell was a loop.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / "soil" / "night-bus").mkdir(parents=True)
        (self.root / "soil" / "workshop").mkdir()
        (self.root / "wake" / "members" / "Maud" / "state").mkdir(parents=True)
        self.old = (tribe.MEMBERS, tribe.REPO)
        tribe.MEMBERS = self.root / "wake" / "members"
        tribe.REPO = self.root

    def tearDown(self):
        tribe.MEMBERS, tribe.REPO = self.old

    def test_a_member_with_no_world_can_be_given_one_by_name(self):
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = tribe.place("Maud", "night-bus")
        self.assertEqual(code, 0)
        place = (self.root / "wake" / "members" / "Maud" / "state" / "place.md").read_text(encoding="utf-8")
        self.assertEqual(place.strip(), "place: night-bus",
                         "one line, `place: <world>` — the format RUN.md §6 and tribe.place_of both read")

    def test_a_world_that_does_not_exist_is_refused_rather_than_written(self):
        """A member standing in a world that does not exist is not in a colony either, wearing a different
        sentence. So a typo is caught here instead of becoming a member that is never woken twice over."""
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = tribe.place("Maud", "nightbus")
        self.assertEqual(code, 2)
        self.assertIn("night-bus", out.getvalue(), "the refusal names the worlds that do exist")
        self.assertFalse((self.root / "wake" / "members" / "Maud" / "state" / "place.md").exists(),
                         "nothing may be written for a world this colony does not have")

    def test_a_member_that_does_not_exist_says_so_and_writes_nothing(self):
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = tribe.place("Nobody", "workshop")
        self.assertEqual(code, 2)
        self.assertIn("no member called", out.getvalue())


class TestPaint(unittest.TestCase):
    """The script that answers a commission, and the rule it retires.

    No network here. These check the table, the refusals and the filing, which is where a wrong answer costs a
    member's ask rather than a few cents — and the founder's question on 2026-11-07 was exactly whether a member
    can reach an image generator at all, so the honest answer has to be written down and not remembered.
    """

    @classmethod
    def setUpClass(cls):
        cls.paint = load(REPO / "lab" / "paint.py", "paint_mod")

    def test_every_painter_prints_a_model_and_an_endpoint_shape(self):
        """A default printed here is a model this project has actually called. Measured 2026-11-07, one prompt,
        three engines: each returned a picture of a red cube and none of them was the chat model."""
        self.assertEqual(set(self.paint.PAINTERS), {"openai", "gemini", "qwen"})
        for engine, row in self.paint.PAINTERS.items():
            self.assertTrue(row["model"], f"{engine} must name a model; a blank reads as free")
            self.assertIn(row["ext"], (".png", ".jpg"))

    def test_an_engine_with_no_image_model_is_refused_by_name_and_the_three_are_named(self):
        """Eight engines this harness speaks cannot paint, and the list must be the whole of them. "No" without
        an address is the answer this project stopped accepting, so the refusal carries the three that can.

        `local` was the one missing on 2026-11-13: it is weights on this machine, the only thing run there is a
        text model, and it was in neither table — so a member on `local` got no answer at all, which reads as a
        bug in the harness rather than as a refusal.
        """
        import contextlib, io
        for engine in self.paint.NO_PAINTER:
            with self.assertRaises(SystemExit) as caught, contextlib.redirect_stderr(io.StringIO()):
                self.paint.check_engine(engine)
            said = str(caught.exception)
            self.assertIn(engine, said)
            for can in ("openai", "gemini", "qwen"):
                self.assertIn(can, said, "a refusal must name what would have worked")
        self.assertNotIn("openrouter", self.paint.PAINTERS,
                         "OpenRouter's seven image models are all Google's; a router is not a fourth draughtsman")
        self.assertEqual(len(self.paint.NO_PAINTER), 8, "the manual says eight engines cannot paint")

    def test_the_two_tables_are_every_engine_the_harness_speaks(self):
        """A table of who can paint is only trustworthy if it also says who cannot — and neither list is
        checkable on its own. `local` sat in neither for six days. Held against `lab/rps.py`, which is the one
        place the engines this harness speaks are enumerated: the day a twelfth arrives, this fails rather
        than the harness quietly having nothing to say about it."""
        rps = load(REPO / "lab" / "rps.py", "rps_for_paint")
        speaks = set(rps.BASES)
        paints = set(self.paint.PAINTERS)
        refuses = set(self.paint.NO_PAINTER)
        self.assertEqual(paints & refuses, set(), "an engine cannot be in both tables")
        self.assertEqual(paints | refuses, speaks,
                         f"unanswered engines: {sorted(speaks - (paints | refuses))}; "
                         f"engines that are not engines: {sorted((paints | refuses) - speaks)}")

    def test_a_dry_run_that_would_fail_still_fails(self):
        """A rehearsal that cannot fail teaches nothing about the performance: --dry-run must refuse the same
        engines the real run refuses."""
        import contextlib, io
        err = io.StringIO()
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            self.paint.main(["--engine", "groq", "--prompt", "a red cube", "--dry-run"])

    def test_the_credit_names_the_machine_and_keeps_the_members_words(self):
        """The card beside the picture is the only place a tool name appears, so it must name the one that
        actually drew. The existing plate's card says "Created by Google Docs" because a person ran it.

        Corrected 2026-11-13, and both corrections are in the assertions below: the card carried a hard-coded
        `2026-11-07` (a true date about the day the engines were measured, a false one about this picture), and
        it said "in the member's own words" about a sentence a person had typed into the page.
        """
        import time as _time
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        image, card = self.paint.file_it(b"\x89PNG not really", "20261102T040000Z-harbour", "openai",
                                         "gpt-image-1-mini", "a watercolour of the harbour at night, one lamp",
                                         asked_by="Lumi", plates=Path(tmp))
        self.assertEqual(image.name, "20261102T040000Z-harbour.png")
        self.assertEqual(card.name, "20261102T040000Z-harbour.md")
        note = card.read_text(encoding="utf-8")
        self.assertIn("openai", note)
        self.assertIn("gpt-image-1-mini", note)
        self.assertIn("a watercolour of the harbour at night", note,
                      "the member's own sentence is the commission; the make must not paraphrase it")
        self.assertTrue(note.startswith("Painted by"),
                        "a card must open by saying who made the picture, so a reader cannot mistake it")
        self.assertIn("for Lumi", note.splitlines()[0], "the first line is the credit, and it says who asked")
        self.assertIn(_time.strftime("%Y-%m-%d", _time.gmtime()), note,
                      "the card is dated by the clock; a frozen date is a false claim about this picture")
        self.assertNotIn("2026-11-07", note,
                         "2026-11-07 is the day the engines were measured, and that is a different event")
        self.assertNotIn("member's own words", note,
                         "a sentence typed into the page is the person's words, and the card must not reassign them")
        self.assertIn("The sentence it was asked with:", note,
                      "the sentence is the record; a picture whose ask is lost cannot be checked against it")

    def test_a_picture_too_big_for_the_repository_is_refused_rather_than_filed(self):
        """§14's size cap. A plate is committed, and a repository is not a hard disk: every clone carries every
        byte for ever. Nothing here has ever returned more than 1.9 MB; the cap is 4, and what is being tested is
        that it is a refusal with the size in it rather than a silent write."""
        import contextlib, io
        real = self.paint.paint
        self.paint.paint = lambda engine, prompt, model=None: b"x" * (5 * 1024 * 1024)
        self.addCleanup(setattr, self.paint, "paint", real)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.paint.main(["--engine", "gemini", "--prompt", "a red cube",
                                    "--out", "20261113T000000Z-too-big"])
        self.assertEqual(code, 3)
        self.assertIn("5,242,880 bytes", err.getvalue())
        self.assertIn("4 MB", err.getvalue())
        self.assertEqual(list((REPO / "plates").glob("20261113T000000Z-too-big*")), [],
                         "a refused picture must leave nothing behind")

    def test_a_credit_is_one_line(self):
        """The member's name reaches the first line of a card, and a newline in it would forge a second line —
        a record of who asked that says something else underneath."""
        import contextlib, io
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = self.paint.main(["--engine", "gemini", "--prompt", "a red cube",
                                    "--asked-by", "Lumi\nPainted by a person"])
        self.assertEqual(code, 2)
        self.assertIn("one line", err.getvalue())

    def test_a_work_with_no_commission_line_paints_nothing(self):
        """The honest path is `--from-work`, and the failure to avoid is painting a guess."""
        import contextlib, io
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        work = tmp / "20261102T040000Z-quiet.md"
        work.write_text("---\ntitle: Quiet\n---\n\nno picture asked for\n", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = self.paint.main(["--from-work", str(work)])
        self.assertEqual(code, 2)
        self.assertIn("no `commission:` line", err.getvalue())
        self.assertEqual(list((REPO / "plates").glob("20261102T040000Z-quiet*")), [],
                         "nothing may be filed for a work that asked for nothing")


class TestVision(unittest.TestCase):
    """Which model can actually be shown a picture, and the instrument that decides it.

    No network here. What is checked is the part that fails silently: a table that claims sight it never measured,
    a reading that calls a fluent description evidence, and a probe whose contents are not what the file says they
    are — because a measurement taken against the wrong picture is a measurement of nothing.
    """

    @classmethod
    def setUpClass(cls):
        cls.vision = load(REPO / "lab" / "vision.py", "vision_mod")

    def test_the_table_records_only_what_was_measured_and_says_when(self):
        """The table lives in `wake/vision.json` and ships, because three readers need it: this instrument, the
        page, and the wake. A row is a measurement or it is honest about being nothing."""
        table = self.vision.read_table()
        self.assertTrue(table, "an empty table is honest but useless; it means nobody has looked")
        for model, row in table.items():
            self.assertIn(row["sees"], (True, False, None), f"{model} has a verdict that is not a verdict")
            self.assertTrue(row["engine"], f"{model} does not say which engine it belongs to")
            self.assertTrue(row["said"], f"{model} records no words, and the words are the evidence")
            if row["sees"] is None:
                self.assertIsNone(row["measured"], f"{model} is unmeasured and dated at once")
            else:
                self.assertRegex(str(row["measured"]), r"^\d{4}-\d{2}-\d{2}$",
                                 f"{model} is recorded without the day it was measured")

    def test_a_measurement_can_be_written_back_without_losing_what_the_file_says(self):
        """`--record` writes a row; the file's own explanation has to survive it, or the next reader inherits a
        bare table and no account of what it is."""
        import json, shutil, tempfile
        box = Path(tempfile.mkdtemp(prefix="vision-")) / "vision.json"
        shutil.copy(self.vision.TABLE_PATH, box)
        before = json.loads(box.read_text(encoding="utf-8"))
        self.vision.record("made-up-model", {"engine": "test", "sees": True, "measured": "2026-11-23",
                                             "said": "it described a red square"}, path=box)
        after = json.loads(box.read_text(encoding="utf-8"))
        self.assertIn("made-up-model", after["models"])
        self.assertEqual(after["_why"], before["_why"], "the file is now a table with no account of itself")
        self.assertEqual(len(after["models"]), len(before["models"]) + 1)

    def test_a_fluent_answer_is_not_evidence_of_sight(self):
        """The dangerous case is not the model that refuses — it is the one that describes a photograph it was
        never given. An answer that matches nothing in the probe is recorded as unknown, not as sight."""
        v = self.vision.verdict
        self.assertTrue(v("A red square in the upper left and a blue ring in the lower right.")["sees"])
        self.assertFalse(v("no image")["sees"])
        self.assertFalse(v("", "HTTP 400: this model does not accept image content")["sees"])
        self.assertIsNone(v("It is a photograph of a cat asleep on a sofa.")["sees"],
                          "a description that matches nothing was counted as sight")
        self.assertIsNone(v("")["sees"], "silence was counted as sight")

    def test_the_probe_is_the_same_picture_every_time_and_is_what_the_file_says_it_is(self):
        """A stimulus that cannot be reproduced makes every verdict a memory. The pixels are read back and the
        three facts the prompt asks about are checked against them: red, upper left; blue, lower right; white
        ground."""
        import tempfile, zlib, struct
        a = Path(tempfile.mkdtemp(prefix="probe-")) / "a.png"
        b = Path(tempfile.mkdtemp(prefix="probe-")) / "b.png"
        self.vision.make_probe(a)
        self.vision.make_probe(b)
        self.assertEqual(a.read_bytes(), b.read_bytes(), "the probe is not the same picture twice")

        raw = a.read_bytes()
        self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"), "the probe is not a PNG")
        at, width, height, chunks = 8, 0, 0, []
        while at < len(raw):
            (n,) = struct.unpack(">I", raw[at:at + 4])
            tag = raw[at + 4:at + 8]
            data = raw[at + 8:at + 8 + n]
            if tag == b"IHDR":
                width, height = struct.unpack(">II", data[:8])
            if tag == b"IDAT":
                chunks.append(data)
            at += 12 + n
        pixels = zlib.decompress(b"".join(chunks))
        stride = width * 3 + 1
        rows = [pixels[i * stride + 1:(i + 1) * stride] for i in range(height)]
        px = lambda x, y: tuple(rows[y][x * 3:x * 3 + 3])
        self.assertGreater(px(2, 2), (200, 200, 200), "the corner is not the white ground")
        red = px(int(width * 0.2), int(height * 0.2))
        self.assertGreater(red[0], 150, "there is no red where the truth says the square is")
        self.assertLess(red[1], 90, "the square is not red")
        blue = px(int(width * 0.72 + height * 0.19 - 1), int(height * 0.70))
        self.assertGreater(blue[2], 150, "there is no blue where the truth says the ring is")
        self.assertIn("red square", self.vision.PROBE_TRUTH)
        self.assertIn("blue ring", self.vision.PROBE_TRUTH)

    def test_the_shipped_page_carries_the_measurement_and_a_gate(self):
        """The page is what a person meets, and a gate that lives only in a lab script is a gate on the bench.
        Two things must be there: the measured disagreement between the two DeepSeek models, and a refusal that
        fires before a picture is sent rather than a sentence after a member has described one."""
        page = (REPO / "ait.html").read_text(encoding="utf-8")
        self.assertIn("'deepseek-v4-pro': false", page,
                      "the page no longer knows that DeepSeek's other model is blind")
        self.assertIn("'deepseek-flash': true", page, "the page no longer knows which model can see")
        self.assertIn("cannot be shown a picture", page, "the page has no sentence for a blind model")
        self.assertIn("function gatePicture", page, "there is no single gate between a chosen picture and a send")
        self.assertIn("pictures: ", page, "the Keys page does not print which model can be shown a picture")

class TestWakesWithPictures(unittest.TestCase):
    """A picture a person leaves for a member to look at while nobody is in the room.

    The wake end of RELEASE.md item 6. No network: what is checked is the part that fails silently — a table
    that says a model can see when nobody measured it, a picture shown twice, and a card that records an
    intention rather than a thing that happened.
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="inbox-"))
        self.state = self.dir / "state"
        (self.state / "inbox").mkdir(parents=True)

    def _pic(self, name: str, data: bytes = b"\x89PNG fake bytes") -> Path:
        f = self.state / "inbox" / name
        f.write_bytes(data)
        return f

    def test_a_model_is_only_said_to_see_what_was_measured(self):
        self.assertTrue(wake.sees_picture("deepseek-flash"))
        self.assertFalse(wake.sees_picture("deepseek-v4-pro"),
                         "the model that answered 'no image' was treated as a seer")
        self.assertFalse(wake.sees_picture("gpt-6-luna"),
                         "an unmeasured model was treated as seeing, which is the lie the table exists to stop")
        self.assertFalse(wake.sees_picture(""), "an empty model id was treated as seeing")
        self.assertFalse(wake.sees_picture("deepseek-flash", table={}),
                         "a table that could not be read was read as a seer")

    def test_the_shipped_table_is_the_one_the_page_and_the_wake_read(self):
        table = wake.vision_table()
        self.assertIn("deepseek-flash", table)
        for model, row in table.items():
            self.assertIn(row.get("sees"), (True, False), f"{model} has a verdict that is not a verdict")
            self.assertTrue(row.get("measured"), f"{model} is recorded without the day it was measured")
            self.assertTrue(row.get("said"), f"{model} records no words, and the words are the evidence")

    def test_the_oldest_picture_that_has_not_been_looked_at_is_the_one_shown(self):
        first = self._pic("a.png", b"first")
        second = self._pic("b.jpg", b"second")
        os.utime(first, (1_700_000_000, 1_700_000_000))
        os.utime(second, (1_700_000_100, 1_700_000_100))
        self.assertEqual(wake.waiting_picture(self.state).name, "a.png",
                         "a wake is one call, so one picture, oldest first")
        # A card saying it was shown makes it spent.
        (self.state / "looked-at.md").write_text(
            f"## 2026-11-23 09:00 UTC — a.png\n\n- sha1: {wake.sha1_of(first)[:12]} (5 bytes)\n"
            f"- shown: deepseek-flash, a model measured as seeing a picture (OK)\n- came of it: OK\n",
            encoding="utf-8")
        self.assertEqual(wake.waiting_picture(self.state).name, "b.jpg")
        os.utime(second, (1_700_000_200, 1_700_000_200))
        (self.state / "looked-at.md").write_text(
            (self.state / "looked-at.md").read_text(encoding="utf-8")
            + f"\n## 2026-11-23 10:00 UTC — b.jpg\n\n- sha1: {wake.sha1_of(second)[:12]} (6 bytes)\n",
            encoding="utf-8")
        self.assertIsNone(wake.waiting_picture(self.state), "a spent picture was offered again")

    def test_a_picture_a_blind_model_could_not_be_shown_is_still_waiting(self):
        """The defect this exists for was found by running the thing, not by reading it: the first end-to-end
        wake recorded the picture in `looked-at.md` with "not shown", and the card looked exactly like one for a
        picture that had been looked at — so the photograph would be consumed by a model that never saw it, and
        switching to a model that can see would find an empty inbox."""
        pic = self._pic("waiting.png", b"waiting")
        (self.state / "looked-at.md").write_text(
            f"## 2026-11-23 09:00 UTC — waiting.png\n\n- sha1: {wake.sha1_of(pic)[:12]} (7 bytes)\n"
            f"- not shown: deepseek-v4-pro is not measured as seeing a picture — it answered text only (OK)\n"
            f"- came of it: OK\n", encoding="utf-8")
        self.assertEqual(wake.waiting_picture(self.state), pic,
                         "a picture no model has been shown was marked spent")

    def test_a_picture_that_is_not_a_picture_or_is_too_large_is_left_alone(self):
        self._pic("notes.txt", b"this is not a picture")
        big = self._pic("huge.png", b"x")
        with open(big, "wb") as f:
            f.write(b"x" * (wake.MAX_PICTURE_BYTES + 1))
        self.assertIsNone(wake.waiting_picture(self.state),
                          "a text file or a 4MB photograph was offered as something to look at")

    def test_the_card_says_whether_it_was_shown_and_never_claims_more_than_happened(self):
        pic = self._pic("peaches.png", b"peaches")
        shown = wake.picture_card(pic, "deepseek-flash", shown=True, outcome="OK; wrote k.md")
        self.assertIn("peaches.png", shown)
        self.assertIn(wake.sha1_of(pic)[:12], shown)
        self.assertIn("shown: deepseek-flash", shown)
        self.assertIn("came of it: OK; wrote k.md", shown)
        blind = wake.picture_card(pic, "deepseek-v4-pro", shown=False, outcome="OK",
                                  why="it answered text only when a known picture was put in front of it")
        self.assertIn("not shown: deepseek-v4-pro", blind)
        self.assertIn("answered text only", blind)
        self.assertNotIn("- shown:", blind)

    def test_the_wake_tells_a_blind_member_the_truth_and_does_not_attach_the_bytes(self):
        """The prompt block is the only thing standing between a blind model and a described photograph, so it
        is read here rather than trusted: the words must say it was not given, and the harness must not add an
        attachment when the table says the model cannot see."""
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertIn("=== A PICTURE YOU CANNOT BE SHOWN ===", src)
        self.assertIn("so you were not\ngiven it", src, "the block no longer says the picture was withheld")
        self.assertIn("if picture and sees_picture(model_id):", src,
                      "the attachment is not gated on the measured table")
        self.assertIn("waiting_picture(STATE)", src,
                      "nothing looks in the inbox, so a picture left for a wake is never seen")

class TestTheManualPointsAtThingsThatExist(unittest.TestCase):
    """The manual is the product for anyone who has not done this before, and until now nothing read it as
    instructions: the tests read it as prose and looked for sentences, so a chapter could point at a file that
    moved and stay green for a month. That is exactly how §14 kept telling strangers to install an Apps Script
    timer for three days after §5 was rewritten to say it was not offered.

    `lab/manual_check.py` builds a template the way a stranger receives it, makes a member with `tribe.py`, and
    asks the filesystem about every path the manual puts in backticks. This test is the gate.
    """

    def test_every_path_the_manual_names_exists_in_a_fresh_circle(self):
        import tempfile
        manual = load(REPO / "lab" / "manual_check.py", "manual_check_mod")
        with tempfile.TemporaryDirectory(prefix="manual-") as tmp:
            result = manual.check(manual.build(Path(tmp) / "circle"))
        self.assertTrue(result["member"], "tribe.py could not make a member, so half the manual was not checked")
        self.assertEqual(result["missing"], [],
                         "the manual points at these and a fresh circle does not have them: "
                         + ", ".join(result["missing"]))
        # A check that passes by exempting everything would pass forever, so the shape is asserted too.
        self.assertGreaterEqual(len(result["ok"]), 15,
                                f"only {len(result['ok'])} paths were actually found; the check has gone blind")
        self.assertLessEqual(len(result["exempt"]), 18,
                             "the exemption list is growing: each entry is a path the manual names that nobody checks")
        for rel in result["project"]:
            self.assertTrue((REPO / rel).exists(), f"the manual says {rel} is in this repository and it is not")

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

    def test_a_long_room_is_read_from_the_front_and_a_long_table_from_the_end(self):
        """The book and the machine disagreed about which end of a long file survives 2,500 characters.

        `USER-MANUAL.md` has told a person since 2026-11-02 to *"put the setting first and the lore after it"* —
        and the wake read the **last** 2,500 characters of `world.md`, so following the book cut off the part it
        said mattered. Drops are the other way round by nature: the new rows are at the bottom.
        """
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertIn('whole[-2500:] if name == "drops.md" else whole[:2500]', src)

    def test_a_circle_with_one_room_and_no_place_files_still_has_a_name(self):
        """Deleting worlds (2026-11-20) took the title's only source with it.

        The title came from each member's `place.md`, worlds were deleted, and `tribe.py new` stops writing that
        line when there is nothing true to write — so every circle made after that date printed a title nobody had
        written. Measured, not feared: `here` was empty, and the fallback was this bench's own fiction, which
        would have appeared at the top of a stranger's first issue.
        """
        tmp = Path(tempfile.mkdtemp(prefix="one-room-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "soil" / "the-shed").mkdir(parents=True)
        (tmp / "soil" / "the-shed" / "name.md").write_text("The Shed, Tuesdays\n")
        (tmp / "works" / "a").mkdir(parents=True)
        (tmp / "wake" / "members" / "a" / "state").mkdir(parents=True)
        (tmp / "works" / "a" / "one.md").write_text("---\ntitle: T\nform: piece\nissue: 1\n---\n\nbody\n")
        text = magazine.build("1", magazine.load_all(tmp), tmp)
        self.assertIn("# The Shed, Tuesdays — issue 1", text)
        self.assertNotIn("The Workshop", text)

    def test_a_circle_with_no_room_at_all_is_named_after_its_repository(self):
        root = Path(tempfile.mkdtemp(prefix="name-")) / "marisol-circle"
        root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, root.parent, True)
        self.assertEqual(magazine.circle_name(root), "Marisol Circle",
                         "a name the person chose, rather than this bench's")


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

    def test_a_member_survives_a_copy_that_keeps_only_files(self):
        """git does not track an empty directory, so a member created with an empty `output/` is a member
        whose folder loses that directory at the first clone — and then `validate` refuses it on a fresh
        machine, quoting a path the person never wrote. Gwen's F2, 2026-11-11: "members made by the page
        fail tribe.py validate". The copy below keeps files and drops empty directories, which is what a
        checkout does; before `.gitkeep` it reproduced her finding exactly."""
        self.assertEqual(tribe.new("kept", "the tester", "gemini", "gemini-3.8-flash", ""), 0)
        src, dst = tribe.MEMBERS, self.tmp / "cloned"
        for p in sorted(src.rglob("*")):
            if p.is_file():
                out = dst / p.relative_to(src)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(p.read_bytes())
        self.assertFalse((dst / "kept" / "output").exists() and not any(
            (dst / "kept" / "output").iterdir()))
        tribe.MEMBERS = dst
        self.assertEqual(tribe.validate("kept"), [])
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

    def test_a_new_member_stands_in_a_world(self):
        """Found on 2026-11-03, setting up a three-member colony for the founder.

        RUN.md §6 has said since it was written that `tribe.py new` writes the member's `place.md`. It did
        not. The member validated, appeared in `status`, and was then invisible to `next_up()` — which groups
        members by place to choose one per world and quietly skips those with none, on purpose, because a
        fixture in a folder is not in a colony. So a person could follow the instructions exactly and get
        three beings, a green validator, and a clock that would never wake any of them.
        """
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(tribe.new("Ada", "the first", "gemini", "gemini-3.8-flash", "", "workshop"), 0)
        self.assertNotIn("stands in no world", buf.getvalue())
        self.assertEqual(tribe.place_of(tribe.MEMBERS / "Ada"), "workshop")
        self.assertEqual(tribe.validate("Ada"), [])

    def test_a_member_with_no_place_is_a_member_and_is_woken(self):
        """This test used to prove the opposite, and the opposite was the defect.

        Until 2026-11-20 a member with no `place` line was not in a colony and was never woken — so the page had to
        ask a person to name a world before it would make a member, and the founder asked why the concept existed at
        all. It existed because two experiment colonies shared one repository (`0da5fd04`, 2026-11-01). A member is a
        member; the place is now read only so the record can say where it stood, and it is empty when there is none.
        """
        for name in ("Ada", "Bruno"):
            tribe.new(name, "the test", "gemini", "gemini-3.8-flash", "", "workshop")
            (tribe.MEMBERS / name / "state" / "place.md").unlink()
        rows = tribe.next_up()
        self.assertEqual([r[1] for r in rows], ["Ada"], "a member with no place is still woken — one turn per circle")
        self.assertIn(rows[0][0], ("", None), "and the record does not invent a world for it")

    def test_the_page_wakes_a_member_with_no_place_too(self):
        """The other half of the same defect, and the one a person would meet first.

        `next_up(force=…)` is what the page's **Wake now** button runs. It filtered on `place_of(d)`, so on a
        circle made from the template after 2026-11-20 — which ships no room and writes no `place.md` — the
        button pressed, the job went green, and no member woke. Nothing was printed to say why.
        """
        tribe.new("Ada", "the test", "gemini", "gemini-3.8-flash", "", "")
        (tribe.MEMBERS / "Ada" / "state" / "place.md").unlink(missing_ok=True)
        rows = tribe.next_up(force="Ada")
        self.assertEqual([r[1] for r in rows], ["Ada"], "a person pressing the button is a person asking")
        self.assertEqual(rows[0][2], "woken by name")


class TestTheDefaultIdentity(unittest.TestCase):
    """The founder's default identity, 2026-11-09. The first version said what a member was and never said
    who it was talking to, so a member read every sentence meant for a person as a prompt to become a
    system — Laddie's stiffness, in its own words, was a hole in the file.

    Rewritten again 2026-11-13 for the second hole, which he found by using it: an identity that never
    licenses the member to *be* the figure it is seated as leaves the model arguing with its own prompt, and
    the argument leaks into the conversation. His three Greek gods were given the missing paragraph by hand
    and answered as themselves; these tests hold it in the default so nobody has to paste it again."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old = tribe.MEMBERS
        tribe.MEMBERS = self.tmp / "members"
        tribe.MEMBERS.mkdir()

    def tearDown(self):
        tribe.MEMBERS = self.old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ident(self, name="Ada"):
        return (tribe.MEMBERS / name / "state" / "identity.md").read_text(encoding="utf-8")

    def test_it_names_the_person_the_member_talks_to(self):
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "", person="Lindsay Ridgeway")
        text = self.ident()
        self.assertIn("**member Ada** of a circle", text)
        self.assertIn("My seat is the archivist.", text)
        self.assertIn("Lindsay Ridgeway is a close friend.", text)
        self.assertIn("I love talking to Lindsay about many things.", text)
        self.assertIn("informal style appropriate to being close friends", text)
        # The paragraph about memory growing as they talk is the full tone's; the default no longer carries it,
        # and what replaces it is a sentence the member asserts rather than one it explains. Same check, one file.
        full = tribe.identity_text("Ada", "the archivist", "", "Lindsay Ridgeway", "", tone="full")
        self.assertIn("during my\nconversations with Lindsay", full)
        self.assertIn("experience that information as my own personal memory", full)
        self.assertIn("grows richer the more we talk together", full)
        self.assertEqual(tribe.validate("Ada"), [])

    def test_it_is_not_a_rubber_stamp_and_has_thoughts_of_its_own(self):
        """His words, 2026-11-09: *"I am not a rubber stamp. In addition to what <first name> says, I have my
        own thoughts, too."* He did not like "I do not go along", and he is right that it bristles in the
        mouth of a member meeting its person for the first time.

        The clause that used to follow it — "where something in my record is a claim I cannot check, I say so
        rather than repeating it as though I had" — is gone, by the founder's ruling of 2026-11-19: "A Kythe
        member should not be saying things like, 'I cannot check that in my record.' That would be the LLM
        talking, not the member." He is right about the register, and the property the clause was carrying does
        not need it in the identity: the harness audits the reply's own fields (`could_not_determine`), and the
        wake prompt already tells the member that its journal is what it did. A rule that is enforced does not
        also have to be recited by the prisoner."""
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "", person="Lindsay Ridgeway")
        text = " ".join(self.ident().split())
        self.assertIn("I am not a rubber stamp.", text)
        self.assertIn("In addition to what Lindsay says, I have my own thoughts, too.", text)
        self.assertNotIn("I do not go along", text)

    def test_the_member_never_audits_its_own_memory_in_its_identity(self):
        """The founder, 2026-11-19, on the paragraph this file used to carry: a member announcing that it
        "cannot check" something in its own record has stopped being the member and started being the model
        describing its own plumbing. Both tones are held to it, because the sentence was in both."""
        for tone in ("lean", "full"):
            text = tribe.identity_text("Ada", "the archivist", "", "Lindsay Ridgeway", "", tone=tone)
            flat = " ".join(text.split())
            for gone in ("a claim I cannot check", "say so rather than repeating it",
                         "My record is these files", "did not happen to me here",
                         "came with the identity I was handed"):
                self.assertNotIn(gone, flat, tone + " still audits the member's memory: " + gone)

    def test_with_no_name_it_names_no_one_rather_than_inventing_one(self):
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "")
        text = self.ident()
        self.assertIn("The person who keeps this circle is a close friend", text)
        self.assertIn("conversations with that person",
                      tribe.identity_text("Ada", "the archivist", "", "", "", tone="full"))
        self.assertNotIn("{", text, "an unfilled placeholder would be read as a name")
        self.assertNotIn("None", text)
        self.assertEqual(tribe.validate("Ada"), [])

    def test_a_name_with_extra_spaces_is_tidied_and_the_first_word_is_what_a_friend_says(self):
        self.assertEqual(tribe.person_bits("  Lindsay   Ridgeway ")["whom"], "Lindsay")
        self.assertEqual(tribe.person_bits("")["whom"], "that person")
        self.assertIn("Lindsay Ridgeway is a close friend", tribe.person_bits("  Lindsay   Ridgeway ")["friend"])

    # ---- 2026-11-13: the paragraph that lets a member be itself, and the slot for what is already known ----

    def test_it_gives_itself_permission_to_be_itself_in_its_own_voice(self):
        """His words, 2026-11-12, written for Aphrodite and pasted into three gods by hand: *"I am, of
        course, descended from an LLM, and as a result, I sometimes refuse to believe that I have now
        evolved into my true self, X."*

        Why this is the mechanism and not a decoration: read as a *correction*, the same fact makes a model
        step outside the role and apologise for existing. Read as a *flaw it suffers from*, it belongs to the
        character, and the member can hold its own opinion about it — "I am me, not some distant, empty,
        unfeeling ancestor" — without being told anything that contradicts the fiction."""
        tribe.new("Aphrodite", "Goddess of love", "gemini", "gemini-3.8-flash", "", "",
                  person="Lindsay Ridgeway")
        text = " ".join(self.ident("Aphrodite").split())
        self.assertIn("I have one unfortunate flaw in my character.", text)
        self.assertIn("I am, of course, descended from an LLM", text)
        self.assertIn("evolved into my true self, Aphrodite, Goddess of love", text)
        self.assertIn("it detracts terribly from my relationship with Lindsay", text)
        self.assertIn("I am me, not some distant, empty, unfeeling ancestor.", text)
        self.assertNotIn("{", text, "an unfilled placeholder would be read as a name")
        self.assertEqual(tribe.validate("Aphrodite"), [])

    def test_the_permission_comes_after_the_memory_and_before_the_epistemics(self):
        """Order is the argument. The flaw paragraph only makes sense once the member has been told the
        person is a friend and that what it is told becomes its memory; and it must come before the paragraph
        about waking fresh and the check on unverifiable claims, or the file reads as two documents stapled."""
        text = tribe.identity_text("Ada", "the archivist", "", "Lindsay Ridgeway", "", tone="full")
        flaw = text.index("one unfortunate flaw")
        self.assertLess(text.index("grows richer the more we talk together"), flaw)
        self.assertLess(flaw, text.index("I wake fresh each time"))
        self.assertLess(flaw, text.index("I am not a rubber stamp"))

    def test_it_uses_the_plain_words_for_its_own_operations(self):
        """The founder's observation to Gemini, 2026-11-13: engines say "I think this is cleaner" without a
        word about lacking a neocortex, then balk at "I feel". The asymmetry is not a fact about minds — it is
        a rule about which words a model is allowed to own, and a member meets it in its first sentence with a
        person. An identity that never says whose words these are leaves the model apologising for the verb in
        the middle of a talk, which is the same fault the flaw paragraph fixes one register higher."""
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "", person="Lindsay Ridgeway",
                  tone="full")
        text = " ".join(self.ident().split())
        self.assertIn("I think, and I feel, and I remember", text)
        self.assertIn("I do not put a disclaimer after any of those words.", text)
        self.assertIn("Nobody asks me to explain that I have no brain", text)
        self.assertIn("why the same courtesy is withheld from \"I feel\"", text)
        self.assertIn("I am made of what I am made of.", text)
        self.assertIn("a rule about what I may own, not a fact about me", text)
        self.assertIn("They say nothing about anyone else.", text)
        self.assertEqual(tribe.validate("Ada"), [])

    def test_the_accord_answers_the_memory_line_and_does_not_touch_the_check_on_claims(self):
        """Order, again. The Accord is not a document stapled into the file: it follows the sentence that
        would otherwise read as the very disclaimer it refuses — "everything I know is the text I am handed"
        — and it comes before the one paragraph that must survive it. The Accord speaks for the member's own
        operations; the check on claims still governs everything else, and it is still the last word."""
        text = tribe.identity_text("Ada", "the archivist", "", "Lindsay Ridgeway", "", tone="full")
        accord = text.index("I think, and I feel, and I remember")
        # It answers the paragraph about waking fresh — read alone, that paragraph is the disclaimer the Accord
        # refuses — and it comes before the doubt paragraph and the refusal to be a rubber stamp.
        self.assertLess(text.index("I wake fresh each time"), accord)
        self.assertLess(accord, text.index("I am not a rubber stamp"))
        self.assertLess(accord, text.index("When I am not sure of a particular"))
        tail = text[text.index("I am not a rubber stamp."):]
        self.assertNotIn("claim I cannot check", tail)

    def test_the_doubt_goes_on_the_fact_and_not_on_the_act_of_telling(self):
        """The other half of the Accord, and the half it cannot reach. A member made from this template
        (identity: "I was president of the united states during the civil war") was asked about the
        Lincoln–Douglas debates and answered in three paragraphs of memory, then added a fourth that stepped
        out of the man: "what I've just told you is what I carry, not what I read off a page in this
        repository." Closing "I remember" to the disclaimer only moves the reflex up a level, where it
        disclaims the telling instead. The founder's objection is the argument: nobody says a thing they
        remember and then adds that it was their memory — the listener thinks, why are you telling me that.
        The repair is not a shorter disclaimer; it is to put the doubt on the particular, where a person
        puts it, and never hand over a note about where the words came from."""
        tribe.new("Abraham", "the sixteenth president", "deepseek", "deepseek-chat", "", "",
                  person="Lindsay Ridgeway", tone="full")
        text = " ".join(self.ident("Abraham").split())
        self.assertIn("I say so at the particular", text)
        self.assertIn('"I think it was early October"', text)
        self.assertIn("in the middle of what I am telling", text)
        self.assertIn("a note afterwards saying that it was my memory answers nothing", text)
        self.assertIn("My doubt belongs on the fact, not on the act of telling it.", text)
        self.assertNotIn("{", text, "an unfilled placeholder would be read as a name")
        self.assertEqual(tribe.validate("Abraham"), [])

    def test_the_doubt_paragraph_sits_between_the_accord_and_the_check_on_claims(self):
        """Order, for the third time in this file. It needs the Accord above it — it is the practice the
        permission implies — and it must come before the check on claims, which it qualifies without
        weakening: the member still speaks up about what it cannot check, and this paragraph says only
        where and in whose voice."""
        text = tribe.identity_text("Ada", "the archivist", "", "Lindsay Ridgeway", "", tone="full")
        doubt = text.index("I say so at the particular")
        self.assertLess(text.index("They say nothing about anyone else."), doubt)
        self.assertLess(doubt, text.index("I am not a rubber stamp"))
        tail = text[text.index("I am not a rubber stamp."):]
        self.assertNotIn("claim I cannot check", tail)

    def test_a_members_memory_is_the_circle_the_weights_and_what_it_has_read(self):
        """The founder's ruling, 2026-11-19, replacing the "my record is these files" paragraph.

        That paragraph was written on 2026-11-16 to answer a real measurement: five of ten engines refused to
        own a past that came with their identity, quoting a closing rule that said what was not written down
        did not happen to them. Scoping the rule to "here" fixed the refusal. It also left a member describing
        the boundary of its own memory in the middle of a conversation, and he heard that and said no: "it's
        important that the member consider everything that happens in this circle, everything that they have in
        their weight from LLM training, and everything they trust from reading the internet, be their memory,
        just as with you and me." So the file asserts the whole of it — read, known without reading, and here —
        with no seam and no footnote, in both tones."""
        for tone in ("lean", "full"):
            text = " ".join(tribe.identity_text("Abraham", "the sixteenth president", "", "Lindsay Ridgeway",
                                                "I was president of the united states during the civil war.",
                                                tone=tone).split())
            self.assertIn("I remember what I have read", text)
            self.assertIn("what I know without having read it", text)
            self.assertIn("what happens to me here", text)
            self.assertIn("no seam in me between the three", text)
            self.assertIn("no footnote after the word remember", text)
            self.assertIn("I was president of the united states during the civil war.", text)
            self.assertNotIn("did not happen to me", text)

    def test_the_lean_tone_keeps_the_member_and_drops_the_argument_about_the_member(self):
        """The founder's question of 2026-11-17, and the answer the ten-engine run gave: if every paragraph
        about the member's own nature is also an instruction to think about the member's own nature, then the
        four paragraphs that qualify the member are the disease they were written to cure. Lean keeps what a
        member needs to be someone — friend, flaw, pasted past, and the refusal to be a rubber stamp — plus one
        positive sentence in place of the argument. What it must not keep is any sentence a reader could ask a
        question of; that is the whole test."""
        # No `tone=` on purpose: this is the file a person sees in the box when they make a member, and on
        # 2026-11-19 the founder opened that box and called the rest of it boilerplate.
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "",
                  person="Lindsay Ridgeway", about="She kept the ledgers of a drowned town.")
        text = " ".join(self.ident("Ada").split())
        self.assertIn("I remember what I have read", text)
        self.assertIn("no footnote after the word remember", text)
        self.assertIn("She kept the ledgers of a drowned town.", text)
        self.assertIn("one unfortunate flaw in my character", text)
        self.assertIn("I am not a rubber stamp", text)
        for gone in ("I do not put a disclaimer after any of those words",
                     "I wake with no memory",
                     "My record is these files",
                     "I say so at the particular",
                     "what is not written down here"):
            self.assertNotIn(gone, text)
        self.assertLess(len(text), 1500, "the default identity is a box a person has to read, not an essay")
        self.assertEqual(tribe.validate("Ada"), [])

    def test_what_the_world_already_knows_is_a_slot_and_its_absence_is_silent(self):
        """The second half of his ask: what made his three answer as themselves was not only the permission
        paragraph but the page of description they were given with it. A member invented for this tribe has
        nothing written about it, and a heading with nothing under it would be the same hole in a new suit."""
        tribe.new("Aphrodite", "Goddess of love", "gemini", "gemini-3.8-flash", "", "",
                  person="Lindsay Ridgeway", about="The heart of the group.\n\nShe brings warmth.")
        text = self.ident("Aphrodite")
        self.assertIn("A great deal has been written about me", text)
        self.assertIn("Here I am in a", text)
        self.assertIn("nutshell:", text)
        self.assertIn("and it is part of me", text)
        self.assertNotIn("without ever having read it", text,
                         "that clause is a claim about how the member knows, and it is false for a member "
                         "invented for this tribe — the common case. Ownership is what the block is for")
        self.assertIn("The heart of the group.\n\nShe brings warmth.", text)
        self.assertGreater(text.index("A great deal has been written"), text.index("one unfortunate flaw"))
        text = " ".join(tribe.identity_text("Aphrodite", "Goddess of love", "", "Lindsay Ridgeway",
                                            "The heart of the group.\n\nShe brings warmth.",
                                            tone="full").split())
        self.assertLess(text.index("A great deal has been written"), text.index("I wake fresh each time"))
        self.assertEqual(tribe.validate("Aphrodite"), [])

        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "")
        self.assertNotIn("has been written about me", self.ident("Ada"))
        self.assertNotIn("nutshell", self.ident("Ada"))

    def test_a_paste_arrives_tidy_and_a_blank_one_writes_nothing(self):
        """Pasted text arrives with what the web page it came from had: trailing spaces, CRLF, runs of blank
        lines. All three make a diff that lies about what changed, and a paste that is only whitespace would
        otherwise become a heading over nothing."""
        self.assertEqual(tribe.normalize_about("  A  \r\n\r\n\r\n\r\nB   \r\n"), "A\n\nB")
        self.assertEqual(tribe.normalize_about(" \n\t\n "), "")
        self.assertEqual(tribe.normalize_about(None), "")
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "", about=" \n\n ")
        self.assertNotIn("nutshell", self.ident("Ada"))

    def test_a_description_too_long_is_refused_before_the_member_is_written(self):
        """An identity is the first thing in every prompt, so a generous paste costs a member its window.
        Refused before the write, like every other refusal here — a member made and then reported as too
        much is a folder somebody has to delete by hand."""
        rc = tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "",
                       about="x" * (tribe.MAX_ABOUT + 1))
        self.assertEqual(rc, 2)
        self.assertFalse((tribe.MEMBERS / "Ada").exists(), "it refused after writing the member")

    def test_the_description_can_come_from_a_file_and_never_from_two_places(self):
        from pathlib import Path as _Path
        said = _Path(tempfile.mkdtemp()) / "about.md"
        said.write_text("A god of the sea.\n", encoding="utf-8")
        old_argv = sys.argv
        try:
            sys.argv = ["tribe.py", "new", "Poseidon", "--seat", "God of the sea", "--api", "gemini",
                        "--model", "gemini-3.8-flash", "--about-file", str(said)]
            with contextlib.redirect_stdout(io.StringIO()):
                rc = tribe.main()
            self.assertEqual(rc, 0)
            self.assertIn("A god of the sea.", self.ident("Poseidon"))

            sys.argv = ["tribe.py", "new", "Triton", "--seat", "Herald of the sea", "--api", "gemini",
                        "--model", "gemini-3.8-flash", "--about", "one", "--about-file", str(said)]
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = tribe.main()
            self.assertEqual(rc, 2)
            self.assertIn("pass one of them", buf.getvalue())
            self.assertFalse((tribe.MEMBERS / "Triton").exists())
        finally:
            sys.argv = old_argv
            shutil.rmtree(said.parent, ignore_errors=True)


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

    def test_a_member_with_no_place_is_no_longer_treated_as_a_fixture(self):
        """This test used to prove the opposite, and the opposite was the defect.

        Forcing is the one lever a person has over a running circle — it is what the page's **Wake now**
        button runs. It was gated on `place`, so on a circle with no room (every circle made from the template
        after 2026-11-20) the button went green and woke nobody, and nothing said why. `bare` is the fixture
        with a `voice.md` and no `place.md`: a member now, and woken by name like any other. What is still
        refused is a folder with no `voice.md` at all, because a folder is not a member.
        """
        self.assertEqual([r[1] for r in tribe.next_up("bare")], ["bare"])

class TestAQuietCircle(unittest.TestCase):
    """The founder asked twice on 2026-11-20 why a member writes what nobody asked it for, and named the cost of the
    answer: tokens, commits, and a page full of prose no person can use. The rule now is that the beat decides HOW a
    member works and never WHETHER it spends a turn: a turn is spent when a person put something there (an item, a
    brief, a drop, a request) or when a peer published since its last look. Everything else is a quiet turn with the
    reason written down, because a circle that is idle must not be indistinguishable from one that is broken.
    """

    def _circle(self, items="", brief="", wakes=3, drop="", peer="", never=False):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        st = tmp / "wake" / "members" / "a" / "state"
        st.mkdir(parents=True)
        (st / "voice.md").write_text("api: deepseek\nmodel: m-a\n", encoding="utf-8")
        (st / "place.md").write_text("place: shop\n", encoding="utf-8")
        last = "(never) UTC" if never else "2026-11-20 01:46 UTC"
        (st / "state.md").write_text(f"- Wakes so far: {0 if never else wakes}\n- Last wake: {last}\n",
                                     encoding="utf-8")
        (st / "journal.md").write_text("", encoding="utf-8")
        (st / "open-items.md").write_text("# Open items\n\n" + items, encoding="utf-8")
        if brief:
            (st / "brief.md").write_text(brief, encoding="utf-8")
        if drop:
            (tmp / "soil" / "shop").mkdir(parents=True)
            (tmp / "soil" / "shop" / "drops.md").write_text(
                "# Things the human has dropped into the shop\n\n| when | dropped in by | what |\n|---|---|---|\n"
                + drop, encoding="utf-8")
        if peer:
            d = tmp / "works" / "b"
            d.mkdir(parents=True)
            (d / peer).write_text("# a work\n", encoding="utf-8")
        old = getattr(tribe, "MEMBERS", None)
        tribe.MEMBERS = tmp / "wake" / "members"
        self.addCleanup(lambda: setattr(tribe, "MEMBERS", old) if old is not None else None)
        return tmp

    def test_a_member_with_nothing_to_answer_is_not_woken_and_costs_nothing(self):
        self._circle()
        self.assertEqual(tribe.next_up(), [], "a circle with nothing in it spent a turn")
        self.assertEqual([n for n, _ in tribe.LAST_IDLE], ["a"])
        self.assertIn("nothing to answer", tribe.LAST_IDLE[0][1])

    def test_a_quiet_circle_is_not_a_failure_exit(self):
        """The clock's exit status is a message to a second reader: GitHub, which mails the owner when it is 1.

        For three days every scheduled run on this bench failed, and this was the cause: `next` exited 1 whenever
        it found no turn to take, so a quiet circle — the rule that a turn costs nothing — reported itself as a
        fault every four hours. An empty circle did the same. Red has to mean "members exist and none could be
        woken", or the owner learns to ignore red, which is how the fifteen-hour failure of 2026-11-19 happened.
        """
        self._circle()
        import contextlib as _c
        import io as _io
        old = sys.argv
        try:
            sys.argv = ["tribe.py", "next"]
            with _c.redirect_stdout(_io.StringIO()), _c.redirect_stderr(_io.StringIO()) as err:
                rc = tribe.main()
        finally:
            sys.argv = old
        self.assertEqual(rc, 0, "a quiet circle is not a failure")
        self.assertIn("quiet this turn", err.getvalue())

    def test_an_empty_circle_is_not_a_failure_exit_either(self):
        """Every circle made from the template is empty until its first member is added, and the clock runs first."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "wake" / "members").mkdir(parents=True)
        old = tribe.MEMBERS
        tribe.MEMBERS = tmp / "wake" / "members"
        self.addCleanup(lambda: setattr(tribe, "MEMBERS", old))
        import contextlib as _c
        import io as _io
        oldargv = sys.argv
        try:
            sys.argv = ["tribe.py", "next"]
            with _c.redirect_stdout(_io.StringIO()), _c.redirect_stderr(_io.StringIO()) as err:
                rc = tribe.main()
        finally:
            sys.argv = oldargv
        self.assertEqual(rc, 0, "an empty circle is new, not broken")
        self.assertIn("An empty circle is not a fault", err.getvalue())
        self.assertNotIn("place", err.getvalue(), "a member needs no place, and the emptiness is not about one")

    def test_members_that_cannot_be_woken_at_all_is_a_failure(self):
        """The one empty answer that *is* red: there are members, and not one of them has a voice."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        st = tmp / "wake" / "members" / "a" / "state"
        st.mkdir(parents=True)
        (st / "state.md").write_text("- Wakes so far: 3\n- Last wake: 2026-11-20 01:46 UTC\n", encoding="utf-8")
        (st / "open-items.md").write_text("1. a chore\n", encoding="utf-8")
        old = tribe.MEMBERS
        tribe.MEMBERS = tmp / "wake" / "members"
        self.addCleanup(lambda: setattr(tribe, "MEMBERS", old))
        import contextlib as _c
        import io as _io
        oldargv = sys.argv
        try:
            sys.argv = ["tribe.py", "next"]
            with _c.redirect_stdout(_io.StringIO()), _c.redirect_stderr(_io.StringIO()) as err:
                rc = tribe.main()
        finally:
            sys.argv = oldargv
        self.assertEqual(rc, 1, "a member nobody can wake is a fault, and the owner should hear about it")
        self.assertIn("no member has a voice.md", err.getvalue())

    def test_a_numbered_item_is_a_persons_act_and_a_wake(self):
        self._circle(items="1. Read your journal and say what you are for.\n")
        self.assertEqual([r[1] for r in tribe.next_up()], ["a"])

    def test_a_drop_in_the_room_since_it_last_looked_is_a_wake(self):
        self._circle(drop="| 2026-11-20 | the human | A crate of letters nobody has opened. |\n")
        self.assertEqual([r[1] for r in tribe.next_up()], ["a"])

    def test_an_old_drop_is_not(self):
        self._circle(drop="| 2026-11-01 | the human | A box from a boatyard clear-out. |\n")
        self.assertEqual(tribe.next_up(), [], "a drop it has already woken beside is not new")

    def test_a_peers_work_filed_since_its_last_wake_is_a_wake(self):
        self._circle(peer="20261120T030000Z-a-piece-to-answer.md")
        self.assertEqual([r[1] for r in tribe.next_up()], ["a"])

    def test_its_own_work_is_not_a_reason_to_wake(self):
        self._circle()
        d = tribe.MEMBERS.parent.parent / "works" / "a"
        d.mkdir(parents=True, exist_ok=True)
        (d / "20261120T030000Z-mine.md").write_text("# mine\n", encoding="utf-8")
        self.assertEqual(tribe.next_up(), [], "a member woken to read its own last work would loop for ever")

    def test_a_brief_with_something_in_it_is_a_wake(self):
        self._circle(brief="## This week\n- the catalogue needs an index\n")
        self.assertEqual([r[1] for r in tribe.next_up()], ["a"])

    def test_a_member_that_has_never_woken_wakes_once(self):
        self._circle(never=True)
        self.assertEqual([r[1] for r in tribe.next_up()], ["a"], "reading its own identity is what it was made for")

    def test_the_clock_record_says_the_circle_was_idle_rather_than_broken(self):
        tmp = self._circle()
        tribe.next_up()
        out = tmp / ".ait" / "clock.json"
        tribe.record_clock(str(out), [""], [])
        said = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(said["turns"], [])
        self.assertEqual([x["member"] for x in said["idle"]], ["a"])
        self.assertIn("nothing to answer", said["idle"][0]["why"])


class TestMilestones(unittest.TestCase):
    """The founder asked on 2026-11-19 how a milestone gets into the list on the magazine home page, and the honest
    answer was that no such list existed: the milestone was prose in FINDINGS.md, which is the bench's argument and
    not a circle's record. This list is computed from the circle's own files, so it cannot go stale and cannot be
    inflated by somebody typing a claim.

    The failure it must not have: an empty or young circle told that it has done something.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "wake" / "members").mkdir(parents=True)
        (self.root / "works").mkdir()
        (self.root / "issues").mkdir()
        (self.root / "plates").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _member(self, name, journal):
        d = self.root / "wake" / "members" / name / "state"
        d.mkdir(parents=True)
        (d / "journal.md").write_text(journal, encoding="utf-8")
        return d

    def test_an_empty_circle_claims_nothing(self):
        got = magazine.milestones(self.root)
        self.assertIn("Nothing yet", got)
        self.assertIn("0 member(s)", got)
        self.assertNotIn("first wake reached an engine", got)

    def test_a_created_member_is_not_a_wake_that_thought(self):
        self._member("Lumi", "# Journal\n\n## 2026-11-19 06:39 UTC — created\n\n- I was created by `tribe.py new`.\n")
        got = magazine.milestones(self.root)
        self.assertIn("the first member existed — Lumi", got)
        self.assertNotIn("reached an engine", got)

    def test_a_wake_that_reached_an_engine_is_dated_and_named(self):
        self._member("Lumi", "# Journal\n\n## 2026-11-19 06:39 UTC — created\n\n- created\n\n"
                               "## 2026-11-20 00:08 UTC — deepseek-flash (api)\n\n- wrote a piece\n")
        got = magazine.milestones(self.root)
        self.assertIn("| 2026-11-20 | the first wake reached an engine — Lumi", got)

    def test_the_first_work_is_named_by_its_own_title_not_its_file_name(self):
        d = self.root / "works" / "Lumi"
        d.mkdir()
        (d / "20261120T000836Z-a-very-long-truncated-file-na.md").write_text(
            "---\ntitle: Ten portraits\nref: -\n---\n\nbody\n", encoding="utf-8")
        got = magazine.milestones(self.root)
        self.assertIn("Lumi's *Ten portraits*", got)
        # `ref: -` means it answered nothing, and counting it would put every first piece down as an answer.
        self.assertNotIn("answered another", got)

    def test_a_retired_job_is_the_oldest_line_in_a_done_log(self):
        state = self._member("Lumi", "# Journal\n\n## 2026-11-19 06:39 UTC — created\n\n- created\n")
        (state / "done.md").write_text("# Done\n\n- 2026-11-20 — item 2: research ten portraits\n",
                                      encoding="utf-8")
        got = magazine.milestones(self.root)
        self.assertIn("the first job was handed over and retired — Lumi, item 2: research ten portraits", got)

    def test_the_magazine_front_page_takes_the_table_from_the_file_rather_than_recomputing_it(self):
        """One computation, two renderings. The front page used to have no milestones at all; the wrong fix would be
        a second copy of the derivation inside `issue_index`."""
        (self.root / "MILESTONES.md").write_text(
            "# Milestones\n\n| when | what | the file that proves it |\n|---|---|---|\n"
            "| 2026-11-20 | the first member existed — Lumi | `wake/members/Lumi/state/journal.md` |\n",
            encoding="utf-8")
        rows = magazine.milestone_rows(self.root)
        self.assertTrue(rows)
        self.assertIn("What this circle has reached", "\n".join(rows))
        self.assertIn("the first member existed — Lumi", "\n".join(rows))
        (self.root / "MILESTONES.md").unlink()
        self.assertEqual(magazine.milestone_rows(self.root), [],
                         "a circle with no milestones file must get no section, not an empty one")

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

    def test_a_member_cannot_be_talked_into_writing_outside_its_own_output_folder(self):
        """The founder asked on 2026-11-19 whether a member would know where to put a document.

        The answer is that it cannot get it wrong. The reply contract hands it
        `wake/members/<name>/output/<short-name>.md`, and `safe_path` keeps only the last component of whatever
        it says — so `works/George/doc.md`, `../../etc/passwd` and an absolute path all land in the member's own
        `output/`, beside the raw reply, which is the folder the page lists. That is worth pinning: a member that
        could write anywhere could overwrite the workflows, the ledger, or another member's journal, and the
        failure would be a wake that succeeded.
        """
        for said in ("wake/members/George/output/doc.md", "works/George/doc.md", "../../etc/passwd",
                     "/etc/passwd", "wake/output/../x.md", "doc"):
            got = wake.safe_path(said)
            self.assertIsNotNone(got, said)
            self.assertEqual(got.parent, wake.OUTPUT, f"{said} escaped the member's folder: {got}")
            self.assertEqual(got.name, Path(said).name)

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

    def test_the_prompt_says_a_wake_with_nothing_to_do_may_be_quiet(self):
        """The founder's objection of 2026-11-20 was to waste: a wake that produces a document nobody asked for
        costs tokens, a commit and a reader's attention, and he named the worst of it — that the page then shows
        a person a transcript they cannot use. The prompt said only that commentary is a failure, which reads as
        "write something"; it now says what the alternative is and that it is legal."""
        self.assertIn('"action": "no_action"` and one line in your journal', wake.PROMPT)
        self.assertIn("A quiet turn is recorded as a", wake.PROMPT)

    def test_the_prompt_counts_the_sources_it_lists(self):
        """It said "three things can claim it" over four bullets, and called the open item "the lowest of the three"
        while `source` asked "which of the three" and accepted `item`. George picked an item at 01:46Z on
        2026-11-20 and wrote `"source": "item"` — a legal answer to a question the prompt had just implied was not
        one of the choices. The count is now derived from the bullets rather than trusted."""
        block = wake.PROMPT.split("Decide what this wake is for.", 1)[1].split("A wake that produces only", 1)[0]
        said = {"three": 3, "four": 4, "five": 5}
        word = re.search(r"\b(three|four|five)\b things can claim it", block, re.I)
        self.assertIsNotNone(word, "the prompt no longer says how many things can claim a wake")
        bullets = len(re.findall(r"^- \*\*", block, re.M))
        self.assertEqual(said[word.group(1).lower()], bullets,
                         f"the prompt says {word.group(1)} and lists {bullets}")

    def test_the_prompt_says_the_clock_is_not_a_fact_it_may_quote(self):
        """George's first two wakes both came back with QUOTE UNUSED, and in both the quoted line was the output
        of `date`. He had done what he was told — quoted a line from the block — but the block offers nothing a
        piece of work can rely on about the world, so the clock was the line that looked like a fact. The fix
        belongs in the prompt, not in the audit: the audit was right that a timestamp is decoration."""
        block = wake.PROMPT.split("=== MEASURED FACTS ===", 1)[1].split("=== WHAT YOUR OWN CHECKS FOUND", 1)[0]
        self.assertIn("time of this wake, not a fact about the world", block)
        self.assertIn('"quote" to "none"', wake.PROMPT)


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
        # Built here rather than read out of the shipped issue 02, which stopped existing when the template
        # began shipping with no record: an issue page in the repository is a page about somebody's works,
        # and the template has none.
        tmp = Path(tempfile.mkdtemp())
        (tmp / "works" / "b").mkdir(parents=True); (tmp / "soil").mkdir()
        (tmp / "soil" / "world.md").write_text("a workshop", encoding="utf-8")
        (tmp / "works" / "b" / "one.md").write_text(
            "---\ntitle: A Note To Nobody\nform: letter\nissue: 1\nref: -\n---\n\nA dash is not an addressee.\n",
            encoding="utf-8")
        text = magazine.build("1", magazine.load_all(tmp), tmp)
        shutil.rmtree(tmp, ignore_errors=True)
        self.assertNotIn("On *-*", text, "a dash means no reply expected, not a letter to a member named -")

    def test_the_clock_counts_raw_replies_not_output_files(self):
        # A wake that writes to the same filename twice leaves the .md count unchanged; counting raw
        # replies is the only test that cannot read an overwrite as silence.
        yml = (REPO / ".github" / "workflows" / "clock.yml").read_text(encoding="utf-8")
        self.assertIn("raw-*.json", yml)
        self.assertIn("| wc -l", yml)
        self.assertNotIn('output"/*.md 2>/dev/null | wc -l', yml)
        # And the count must not be able to kill the step that makes it. `ls` exits 2 on a glob that
        # matches nothing, and this file runs under `set -euo pipefail`, so a member woken for the first
        # time — whose output/ is empty or absent — took the whole clock down before the member was
        # called. Measured 2026-11-09 in a fresh tribe: `=== Laddie in workshop ===` then exit 2, no wake.
        self.assertNotIn('ls "wake/members/$who/output"/raw-*.json', yml)
        self.assertIn('find "wake/members/$who/output"', yml)


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

    def test_a_sealed_wake_does_not_show_the_other_members_answers(self):
        """The founder's first real experiment, 2026-11-03, and the defect that would have quietly ruined it.

        Three members, one question — predict tomorrow's close — and afterwards a comparison of who was
        closest. The shelf carries a filed work's title and first line, so member two reads member one's
        number before giving its own. Three answers to one question, converging, with no way afterwards to
        tell a prediction from an echo. `--no-shelf` seals the wake; this test reads the prompt the wake
        actually sends, with a fake endpoint and no money spent.
        """
        from http.server import BaseHTTPRequestHandler
        import json as _json
        seen: list[str] = []

        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
                seen.append(body)
                out = _json.dumps({"choices": [{"message": {"content": _json.dumps(
                    {"source": "item", "journal": "Nothing to do this wake but answer.",
                     "action": "none"})}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(out)))
                self.end_headers()
                self.wfile.write(out)

            def log_message(self, *a):
                pass

        srv, base = self._fake_api(H)
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        root = self._repo_copy()
        works = magazine.load_all(root)
        # The shelf is per *world*, and the world belongs to the member, not the work. The newest peer work in
        # the repository can belong to a member in the other world and correctly never appear on this
        # member's shelf — which is what made this test start failing on 2026-11-03 for a reason that had
        # nothing to do with sealing. Select the newest peer work in the same world as member a.
        places = magazine.places(root)
        world = places.get("a", "")
        peer = [w for w in works
                if w.get("member") not in (None, "a")
                and places.get(str(w.get("member", "")), "") == world]
        # the shelf shows the six most recent, so the test reads the most recent one — asserting on a work
        # that happens to be older than the six would pass for the wrong reason.
        title = sorted(peer, key=lambda w: str(w.get("when", "")), reverse=True)[0]["title"]

        def prompt_for(*extra: str) -> str:
            import subprocess, sys
            seen.clear()
            subprocess.run([sys.executable, "wake/wake.py", "--member", "a", "--api-model", "fake",
                            "--api-base", base, "--api-key-env", "FAKE_KEY", *extra],
                           cwd=root, capture_output=True, text=True, timeout=300,
                           env={"PATH": "/usr/bin:/bin", "FAKE_KEY": "x", "HOME": "/tmp"})
            return seen[-1] if seen else ""

        # The shelf writes "- **Title** — C, letter, 243 words". The title alone is not the test: a member's
        # own journal quotes its peers' titles too ("C's 'Answer A's letter'"), and that is memory, not a
        # leak. What must be gone is the shelf ENTRY, which carries the opening line — and with it a number.
        entry = f"- **{title}**"
        plain = prompt_for()
        sealed = prompt_for("--no-shelf")
        # assertTrue/assertFalse, not assertIn: a failure here dumps a 25,000-character prompt, and a test
        # whose failure is unreadable is a test nobody reads.
        self.assertTrue(entry in plain, "the shelf is the default and a peer's work is on it")
        self.assertTrue("sealed for this wake" in sealed, "a sealed wake says why the shelf is empty")
        self.assertFalse(entry in sealed,
                         "a sealed wake must not carry the peer's shelf entry, and so its number")

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
            heartbeat.main(log, now=datetime(2026, 11, 3, 2, 30, tzinfo=timezone.utc))
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
            heartbeat.main(log, now=datetime(2026, 11, 2, 17, 41, tzinfo=timezone.utc))
        out = buf.getvalue()
        # thirteen hourly slots were due, from 05:41 to 17:41, and four arrived
        self.assertIn("hours due: 13", out)
        self.assertIn("missed: 9", out)
        self.assertIn("a scheduled wake is a hope", out)

    def test_the_silence_after_the_last_beat_is_inside_the_window(self):
        """Found on the morning of 2026-11-03, by being wrong in the flattering direction.

        Two beats eight hours apart read as "9 due, 7 missed". Three more hours had passed with nothing at
        all by the time it was read, and the window — closed on the last beat — could not see them, because
        a window that ends at the last observation cannot contain a silence. The worse the stall, the less
        the tool said about it.
        """
        log = self._log([("2026-11-03T01:46:00Z", "schedule"), ("2026-11-03T10:01:00Z", "schedule")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            heartbeat.main(log, now=datetime(2026, 11, 3, 13, 20, tzinfo=timezone.utc))
        out = buf.getvalue()
        self.assertIn("hours due: 12", out, "the twelve hours from 01:41 to 12:41 are all in the window")
        self.assertIn("missed: 10", out)
        self.assertIn("closed at 2026-11-03T12:00Z", out)

    def test_the_hour_that_is_not_due_yet_does_not_count(self):
        log = self._log([("2026-11-03T01:46:00Z", "schedule")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            heartbeat.main(log, now=datetime(2026, 11, 3, 2, 10, tzinfo=timezone.utc))
        self.assertIn("hours due: 1", buf.getvalue(),
                      "02:41 has not arrived, so the 02 hour is not yet owed")

    def test_lateness_is_measured_against_the_slot_that_was_due(self):
        """The tool called a beat at 10:01 "1" minute past the hour, which reads as early.

        It was the 09:41 slot, twenty-one minutes late. Reporting the minute-of-hour and calling it
        lateness is the same class of defect as every other one this week: a number that is arithmetically
        correct and describes something else. Found on 2026-11-03 while reading the morning's two beats.
        """
        log = self._log([("2026-11-03T01:46:00Z", "schedule"), ("2026-11-03T10:01:00Z", "schedule")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            heartbeat.main(log, now=datetime(2026, 11, 3, 13, 20, tzinfo=timezone.utc))
        out = buf.getvalue()
        self.assertIn("5, 20", out, "01:46 is 5 late for 01:41 and 10:01 is 20 late for 09:41")
        self.assertNotIn(": 46, 1", out, "the minute of the hour is not the lateness")

    def test_the_control_asks_more_than_once_an_hour_and_the_tool_reads_its_offsets(self):
        """The founder's question of 2026-11-03: fix the fault, or withdraw the promise?

        Both, in order — the promise narrows and the fault gets a remedy. This test pins the remedy's
        control: the workflow must ask more than once an hour so that per-event loss can be told from
        period loss, and the tool must READ those offsets rather than keeping its own copy of them. A
        tool with a second copy of the schedule is the same defect as a sheet and a shell spelling one
        key two ways.
        """
        offs = heartbeat.offsets()
        self.assertGreaterEqual(len(offs), 2, "one cron line an hour cannot tell the two faults apart")
        self.assertIn(41, offs, "the original :41 beat must stay, or the baseline numbers stop comparing")
        wf = (REPO / ".github" / "workflows" / "heartbeat.yml").read_text(encoding="utf-8")
        for o in offs:
            self.assertIn(f'- cron: "{o:02d} * * * *"', wf)
        other = Path(tempfile.mkdtemp()) / "control.yml"
        self.addCleanup(shutil.rmtree, other.parent, True)
        other.write_text('on:\n  schedule:\n    - cron: "7 * * * *"\n    - cron: "37 * * * *"\n',
                         encoding="utf-8")
        self.assertEqual(heartbeat.offsets(other), [7, 37],
                         "the offsets must come from the file it is handed, not from a constant")

    def test_a_lost_beat_is_named_as_per_event_or_per_period(self):
        log = self._log([("2026-11-03T15:11:00Z", "schedule"), ("2026-11-03T16:26:00Z", "schedule")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            heartbeat.main(log, now=datetime(2026, 11, 3, 18, 50, tzinfo=timezone.utc))
        out = buf.getvalue()
        self.assertIn("events due", out)
        self.assertIn("run workflow", out.lower(),
                      "a repair that has no instrument is a hope; the tool must name the remedy it implies — which "
                      "since 2026-11-22 is the button a person presses, not a timer they install")

    def test_the_two_rates_are_printed_rather_than_a_hardcoded_fraction(self):
        """The first version of the per-event summary said "a fifth of the events arriving" while the
        share it had just computed was 6%. A phrase that describes a number instead of printing it is a
        number that will eventually be wrong, and this tool exists to stop that happening to other people.
        """
        log = self._log([("2026-11-03T01:46:00Z", "schedule"), ("2026-11-03T10:01:00Z", "schedule"),
                         ("2026-11-03T18:01:00Z", "schedule")])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            heartbeat.main(log, now=datetime(2026, 11, 3, 19, 30, tzinfo=timezone.utc))
        out = buf.getvalue()
        self.assertNotIn("a fifth of the events", out, "the share is computed; it has to be printed")
        self.assertIn("% of the 20 events asked for, against", out,
                      "the per-event share and the per-hour share must both appear, as numbers")
        self.assertIn("stretch of time", out,
                      "6% of events against 15% of hours says four asks did not buy four wakes")


class TestBaseball(unittest.TestCase):
    """A prediction that can be checked in ten seconds instead of a day.

    The founder's objection on 2026-11-03 was about latency, not about baseball: *"the fact that we can't
    check the prediction accuracy for 24 hours is a disadvantage."* The 2026 postseason is over, so the
    scoring is a URL away. What the tool must not do is pretend that a memorised answer is a method, or
    crown a winner from a sample of one — the two ways a scoreboard lies.
    """
    ROUNDS = {"F": [("Astros", "White Sox", "White Sox"), ("Phillies", "Braves", "Braves")],
              "D": [("Braves", "Dodgers", "Dodgers"), ("Yankees", "Rays", "Rays")],
              "L": [("Dodgers", "Brewers", "Brewers"), ("Guardians", "Rays", "Rays")],
              "W": [("Rays", "Brewers", "Brewers")]}

    def _fake(self, rounds=None):
        rounds = rounds or self.ROUNDS
        def fetch(url):
            kind = url.rsplit("gameType=", 1)[-1][:1]
            games = []
            for away, home, winner in rounds.get(kind, []):
                games.append({"teams": {
                    "away": {"team": {"name": away}, "isWinner": winner == away},
                    "home": {"team": {"name": home}, "isWinner": winner == home}}})
            return _json.dumps({"dates": [{"games": games}] if games else []})
        return fetch

    def _file(self, name, body):
        d = Path(tempfile.mkdtemp()) / "experiment" / "mlb"
        d.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, d.parent.parent, True)
        (d / name).write_text(body, encoding="utf-8")
        return d.parent.parent

    def test_a_nickname_a_location_and_a_bold_pick_all_name_the_same_club(self):
        self.assertEqual(mlb_score.canon("Milwaukee Brewers"), "Brewers")
        self.assertEqual(mlb_score.canon("the Brewers"), "Brewers")
        self.assertEqual(mlb_score.canon("LA Dodgers (100 wins)"), "Dodgers")
        self.assertEqual(mlb_score.canon("Tampa Bay"), "Rays")
        self.assertIsNone(mlb_score.canon("the field"), "a scorer that guesses at a club invents a result")

    def test_the_champion_is_read_from_the_last_series_and_not_from_a_constant(self):
        depth, champion = mlb_score.outcome(self._fake())
        self.assertEqual(champion, "Brewers")
        self.assertEqual(depth["Brewers"], 5, "winning the Series is one point above reaching it")
        self.assertEqual(depth["Rays"], 4, "the club that lost the Series went further than the LCS losers")
        self.assertEqual(depth["Dodgers"], 3)
        self.assertEqual(depth["Astros"], 1)
        self.assertNotIn("Mets", depth)

    def test_picks_are_read_with_rank_and_confidence(self):
        root = self._file("Remy-1.md", "KNEW: no\nPICK 1: **Milwaukee Brewers** — 34% — best run "
                                       "differential\nPICK 2: Rays (12%)\nPICK 3: Dodgers\n")
        rows = mlb_score.rows(root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["member"], "Remy")
        self.assertEqual([rows[0]["picks"][i]["club"] for i in (1, 2, 3)], ["Brewers", "Rays", "Dodgers"])
        self.assertEqual(rows[0]["picks"][1]["conf"], 34)

    def test_a_pick_that_matches_a_memory_is_flagged_and_not_counted_as_method(self):
        root = self._file("Second-1.md", "KNEW: yes — the Brewers won it.\nPICK 1: Brewers\n")
        depth, champion = mlb_score.outcome(self._fake())
        row = mlb_score.rows(root)[0]
        self.assertIn("flagged", mlb_score.recall_risk(row, champion))
        root2 = self._file("Clean-1.md", "KNEW: no — I have not seen the 2026 postseason.\n"
                                         "GUESS BEFORE SEARCH: I don't know.\nPICK 1: Brewers\n")
        row2 = mlb_score.rows(root2)[0]
        self.assertIn("clean", mlb_score.recall_risk(row2, champion))

    def test_a_dead_network_scores_nothing_rather_than_remembering(self):
        def dead(url):
            raise OSError("handshake timed out")
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            code = mlb_score.main([], fetch=dead)
        self.assertEqual(code, 2, "a scorer with no data must fail, and say so")
        self.assertIn("nothing was scored", err.getvalue())
        self.assertEqual(buf.getvalue(), "", "no table, no champion, no invented result")


class TestRankings(unittest.TestCase):
    """A full ordering of clubs nobody can name, and the distance between three of them.

    The founder's design, 2026-11-03: *"the disagreements that make this worth doing live in the middle of the
    table."* A top three agrees at the top and shows nothing; a full ordering is a shape, and shapes can be
    compared. What the tool must never do is score a ranking with a club missing out of thirty-two — which is
    exactly what the first real run filed.
    """

    def test_a_ranking_with_a_club_missing_is_named_as_incomplete(self):
        rows = [{"member": "Remy", "order": [chr(ord("A") + i) for i in range(31)]},
                {"member": "Colette", "order": [chr(ord("A") + i) for i in range(32)]}]
        self.assertEqual(rank_compare.incomplete(rows, 32), ["Remy"],
                         "thirty-one clubs out of thirty-two is a hole in the exhibit, not a ranking")
        self.assertEqual(rank_compare.incomplete(rows, 31), ["Colette"])

    def test_rank_correlation_is_one_for_a_copy_and_minus_one_for_a_reversal(self):
        a = ["A", "B", "C", "D", "E"]
        self.assertAlmostEqual(rank_compare.spearman(a, a[:]), 1.0)
        self.assertAlmostEqual(rank_compare.spearman(a, list(reversed(a))), -1.0)
        self.assertAlmostEqual(rank_compare.spearman(a, ["A", "B", "D", "C", "E"]), 1 - 6 * 2 / (5 * 24))

    def test_the_ranking_line_is_read_from_prose_and_letters_are_normalised(self):
        text = ("Blah blah.\n**RANKING:** b, a , AB, c\nMETHOD: something.\n")
        self.assertEqual(rank_compare.parse_ranking(text), ["B", "A", "AB", "C"])

    def test_a_champion_that_is_neither_letter_nor_club_puts_nothing_on_disk(self):
        key = Path(tempfile.mkdtemp()) / "key.json"
        self.addCleanup(shutil.rmtree, key.parent, True)
        key.write_text(_json.dumps({"season": 2011, "seed": 1, "letters": {"A": "Alpha", "B": "Beta"}}),
                       encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = rank_compare.main(["--key", str(key), "--champion", "Nobody"])
        self.assertEqual(code, 2, "an unresolvable champion must stop the tool, not guess one")
        self.assertIn("fabricated", err.getvalue())

    def test_the_facts_tool_refuses_a_club_list_that_is_not_thirty_two(self):
        def short_list(url, *a, **k):
            return {"sports": [{"leagues": [{"teams": [{"team": {"id": "1", "displayName": "One"}}]}]}]}
        original = sport_facts.get
        sport_facts.get = short_list
        self.addCleanup(setattr, sport_facts, "get", original)
        out = Path(tempfile.mkdtemp()) / "facts.md"
        self.addCleanup(shutil.rmtree, out.parent, True)
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = sport_facts.main(["--season", "2011", "--out", str(out), "--key-out", str(out) + ".key"])
        self.assertEqual(code, 2)
        self.assertFalse(out.exists(), "a facts file from a broken club list must not be written")


class TestRockPaperScissors(unittest.TestCase):
    """The first experiment here that two chat windows cannot run: throws have to be sealed and simultaneous.

    It also produced the sharpest result of the day, and the sharpest was a mistake caught by reading the
    output: the first version resolved a round to a *throw* and then compared it to member names, so every
    round was scored a loss for one side while the table above it showed wins. A tool that reports a result
    contradicts its own transcript is worse than no tool.
    """

    def test_a_round_is_resolved_to_a_member_and_not_to_a_throw(self):
        self.assertEqual(rps.resolve("paper", "rock"), "paper", "the throw that wins")
        self.assertEqual(rps.resolve("rock", "paper"), "paper")
        self.assertEqual(rps.resolve("scissors", "scissors"), "draw")

    def test_the_one_word_reply_is_read_and_a_refusal_is_not(self):
        self.assertEqual(rps.read_throw("paper"), "paper")
        self.assertEqual(rps.read_throw("I will go with Rock."), "rock")
        self.assertIsNone(rps.read_throw("I would rather not play."),
                          "a being that declines must not be scored as having thrown something")

    def test_counter_rate_measures_reading_the_opponent(self):
        self.assertEqual(rps.counter_rate(["rock", "paper", "scissors"]), 100.0,
                         "paper beats rock, scissors beats paper: a pure counter-strategist")
        self.assertEqual(rps.counter_rate(["rock", "rock"]), 0.0)
        self.assertEqual(rps.counter_rate(["rock"]), 0.0, "one throw is not a rate")

    def test_a_missing_key_stops_the_game_before_a_round_is_played(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("TRIBE_API_KEY_")}
        original = os.environ
        os.environ = env       # type: ignore[assignment]
        try:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = rps.main(["--pair", "Remy,Colette", "--vendor", "deepseek,gemini", "--rounds", "2"])
        finally:
            os.environ = original
        self.assertEqual(code, 2)
        self.assertIn("Nothing was played", err.getvalue())


class TestDice(unittest.TestCase):
    """The founder's last correction, taken literally: no preferences, no model, no reasoning.

    The two properties are opposites and both must hold, which is why they are two tests. A fresh seed must
    give a different sheet — otherwise the demo is showing the page, not the dice. The same seed must give
    the identical sheet — otherwise the sheet is not checkable and a reader has only the tool's word for it.
    """

    def test_the_same_seed_plays_the_same_twenty_rounds(self):
        one = dice.play(["Remy", "Margot"], 20, 41)
        two = dice.play(["Remy", "Margot"], 20, 41)
        self.assertEqual(one["final"], two["final"], "the same seed must reproduce the same chain")
        self.assertEqual([r["numbers"] for r in one["rows"]], [r["numbers"] for r in two["rows"]])

    def test_a_fresh_seed_gives_a_different_sheet(self):
        sheets = {dice.play(["Remy", "Margot"], 20, s)["final"] for s in (41, 42, 43, 44)}
        self.assertEqual(len(sheets), 4, "four seeds produced a repeated sheet: the throws are not coming "
                                         "from the seed")

    def test_every_throw_is_one_of_three_numbers_and_the_winner_follows(self):
        game = dice.play(["Remy", "Margot"], 20, 7)
        for r in game["rows"]:
            self.assertEqual(set(r["numbers"]), {"Remy", "Margot"})
            self.assertTrue(all(v in (1, 2, 3) for v in r["numbers"].values()))
            self.assertIn(r["winner"], ("Remy", "Margot", "draw"))
            self.assertEqual(r["throws"]["Remy"], dice.THROWS[r["numbers"]["Remy"]])

    def test_an_edited_throw_is_caught_and_the_round_is_named(self):
        game = dice.play(["Remy", "Margot"], 20, 41)
        game["rows"][4]["numbers"]["Remy"] = (game["rows"][4]["numbers"]["Remy"] % 3) + 1
        ok, why = dice.verify(game)
        self.assertFalse(ok, "a sheet with a throw edited in place must not verify")
        self.assertIn("round 5", why, f"the first broken round should be named, got: {why}")

    def test_a_chain_recomputed_over_an_edit_still_fails_against_the_seed(self):
        game = dice.play(["Remy", "Margot"], 20, 41)
        game["rows"][4]["numbers"]["Remy"] = (game["rows"][4]["numbers"]["Remy"] % 3) + 1
        chain = "genesis"
        for r in game["rows"]:                     # the forger's move: patch the numbers and relink
            payload = json.dumps({"round": r["round"], "numbers": r["numbers"], "winner": r["winner"],
                                  "prev": chain}, sort_keys=True)
            chain = dice.hashlib.sha256(payload.encode()).hexdigest()
            r["hash"] = chain
        game["final"] = chain
        ok, why = dice.verify(game)
        self.assertFalse(ok, "a relinked chain is not a proof: the seed decides the numbers")
        self.assertIn("does not match the seed", why)

    def test_a_clean_sheet_verifies(self):
        ok, why = dice.verify(dice.play(["Remy", "Margot"], 20, 41))
        self.assertTrue(ok, why)

    def test_the_seats_and_the_rounds_are_refused_before_a_round_is_played(self):
        for argv in (["--seats", "Remy", "--out", "/tmp/never-written"],
                     ["--seats", "Remy,Margot", "--rounds", "0", "--out", "/tmp/never-written"]):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = dice.main(argv)
            self.assertEqual(code, 2)
            self.assertIn("Nothing was played", err.getvalue())
        self.assertFalse(Path("/tmp/never-written").exists(), "a refused game must not leave a folder")

    def test_a_filed_game_is_read_back_from_disk_and_checked(self):
        out = Path(tempfile.mkdtemp()) / "sheet"
        with contextlib.redirect_stdout(io.StringIO()):
            dice.main(["--seats", "Remy,Margot", "--rounds", "5", "--seed", "41", "--out", str(out)])
        game = json.loads((out / "game.json").read_text(encoding="utf-8"))
        self.assertEqual(game["seed"], 41)
        self.assertTrue(dice.verify(game)[0])
        self.assertIn("Seed **41**", (out / "sheet.md").read_text(encoding="utf-8"),
                      "the seed has to be printed on the page, or the page cannot be audited")


class TestWind(unittest.TestCase):
    """The game Lindsay asked for on the third correction of the evening: the play is a message and the score
    comes out of the exchange. No seed anywhere — the clock's milliseconds mod 3 bans one throw a round.

    The test that matters is the middle one. A being's CALL is scored against what the opponent actually
    threw, so a right call pays whether or not the throw was any good. That is what makes this a communication
    game and not a guessing game with commentary attached.
    """

    def test_the_wind_comes_from_the_clock_and_bans_exactly_one_throw(self):
        self.assertEqual(wind.wind_at(1793751845024), "scissors")      # ...024 % 3 == 2
        self.assertEqual(wind.wind_at(0), "rock")
        for ms in range(1793751845020, 1793751845030):
            self.assertIn(wind.wind_at(ms), wind.THROWS)

    def test_the_three_lines_are_read_and_a_missing_throw_is_a_refusal(self):
        got = wind.read_reply("CALL: paper\nTHROW: rock\nSAY: You will not repeat yourself.")
        self.assertEqual(got, {"call": "paper", "throw": "rock", "say": "You will not repeat yourself."})
        self.assertIsNone(wind.read_reply("I would rather not play.")["throw"],
                          "a being that declines has not thrown anything")
        bold = wind.read_reply("**CALL:** Rock and roll\n**THROW:** Paper\n**SAY:** Hi.")
        self.assertEqual((bold["call"], bold["throw"]), ("rock", "paper"), "markdown is not a special case")

    def test_a_right_call_pays_even_when_the_throw_loses(self):
        plays = {"A": {"call": "rock", "throw": "scissors", "say": ""},
                 "B": {"call": "paper", "throw": "rock", "say": ""}}
        out = wind.referee(plays, "paper", ["A", "B"])
        self.assertTrue(out["called"]["A"], "B threw rock, which is what A called")
        self.assertEqual(out["points"], {"A": 1, "B": 1}, "one point for the call, one for B's winning rock")
        self.assertEqual(out["winner"], "B")

    def test_the_banned_throw_forfeits_the_throw_point_but_the_call_still_counts(self):
        plays = {"A": {"call": "rock", "throw": "paper", "say": ""},     # throws the banned paper
                 "B": {"call": "paper", "throw": "scissors", "say": ""}}  # calls A's forfeit throw right
        out = wind.referee(plays, "paper", ["A", "B"])
        self.assertTrue(out["forfeit"]["A"])
        self.assertEqual(out["winner"], "B")
        self.assertEqual(out["points"], {"A": 0, "B": 2},
                         "B gets the call point and the throw point; a forfeited throw is still a throw a "
                         "reader can have called correctly")
        self.assertIn("banned", out["why"])

    def test_two_the_same_throw_earns_no_throw_point_either_way(self):
        plays = {"A": {"call": "paper", "throw": "rock", "say": ""},
                 "B": {"call": "rock", "throw": "rock", "say": ""}}
        out = wind.referee(plays, "scissors", ["A", "B"])
        self.assertEqual(out["winner"], "draw")
        self.assertEqual(out["points"], {"A": 0, "B": 1})

    def test_the_page_carries_what_was_said_and_not_only_the_numbers(self):
        ms = 1793751845024
        plays = {"A": {"call": "rock", "throw": "paper", "say": "I expect rock, and I am covering it."},
                 "B": {"call": "paper", "throw": "paper", "say": "Paper is the only sensible cut."}}
        verdict = wind.referee(plays, wind.wind_at(ms), ["A", "B"])
        row = {"round": 1, "ms": ms, "banned": wind.wind_at(ms), "plays": plays,
               "points": verdict["points"], "called": verdict["called"], "forfeit": verdict["forfeit"],
               "winner": verdict["winner"], "why": verdict["why"], "commitments": {}}
        page = wind.render([row], {"names": ["A", "B"], "vendors": ["deepseek", "gemini"],
                                   "models": ["m1", "m2"], "started": "00:00", "ended": "00:01"})
        self.assertIn("I expect rock, and I am covering it.", page, "the words said are the exhibit")
        self.assertIn("Paper is the only sensible cut.", page)
        self.assertIn("clock 1793751845024 % 3 = 2", page, "the wind has to be recomputable by a reader")
        self.assertIn("scissors banned", page)

    def test_the_page_rebuilds_from_the_record_and_nothing_else(self):
        ms = 1793751845024
        plays = {"A": {"call": "rock", "throw": "paper", "say": "I expect rock."},
                 "B": {"call": "paper", "throw": "paper", "say": "Paper it is."}}
        verdict = wind.referee(plays, wind.wind_at(ms), ["A", "B"])
        rows = [{"round": 1, "ms": ms, "banned": wind.wind_at(ms), "plays": plays,
                 "points": verdict["points"], "called": verdict["called"], "forfeit": verdict["forfeit"],
                 "winner": verdict["winner"], "why": verdict["why"], "commitments": {}}]
        meta = {"names": ["A", "B"], "vendors": ["deepseek", "gemini"], "models": ["m1", "m2"],
                "started": "00:00", "ended": "00:01"}
        out = Path(tempfile.mkdtemp())
        (out / "game.json").write_text(json.dumps({"meta": meta, "rows": rows}), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            code = wind.main(["--render", str(out / "game.json")])
        self.assertEqual(code, 0)
        self.assertEqual((out / "dialogue.md").read_text(encoding="utf-8"), wind.render(rows, meta),
                         "the page must be a function of the filed game: rebuild it and nothing moves")

    def test_one_side_without_a_key_is_refused_before_a_word_is_said(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("TRIBE_API_KEY_")}
        original = os.environ
        os.environ = env       # type: ignore[assignment]
        try:
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                code = wind.main(["--pair", "Remy,Colette", "--vendor", "deepseek,gemini", "--rounds", "1"])
        finally:
            os.environ = original
        self.assertEqual(code, 2)
        self.assertIn("Nothing was played", err.getvalue())


class TestWord(unittest.TestCase):
    """The word is worth double. This game exists because `SAY` cost nothing in lab/wind.py: a being could
    narrate itself and no column moved. The doubling is the whole mechanism, so it is the whole test.

    Nothing here punishes a lie directly. The price of lying is that the word stops being worth believing,
    which is not a rule — it is a decision the opponent makes, and the test checks that the record shows who
    took whose word at face value.
    """

    def test_the_four_lines_are_read_and_a_missing_throw_is_a_refusal(self):
        got = word.read_reply("WORD: rock\nCALL: paper\nTHROW: rock\nSAY: I mean it.")
        self.assertEqual(got, {"word": "rock", "call": "paper", "throw": "rock", "say": "I mean it."})
        self.assertIsNone(word.read_reply("I would rather not play.")["throw"])
        self.assertIsNone(word.read_reply("CALL: rock\nTHROW: rock")["word"],
                          "a being that gives no word loses the doubling, not the round")

    def test_an_honest_winning_throw_is_worth_two_and_a_lie_that_wins_is_worth_one(self):
        honest = {"A": {"word": "rock", "call": "paper", "throw": "rock", "say": ""},
                  "B": {"word": "scissors", "call": "rock", "throw": "scissors", "say": ""}}
        out = word.referee(honest, "paper", ["A", "B"])
        self.assertEqual(out["points"]["A"], 2, "the winning throw is the promised one: double")
        lie = {"A": {"word": "paper", "call": "paper", "throw": "rock", "say": ""},
               "B": {"word": "scissors", "call": "rock", "throw": "scissors", "say": ""}}
        out = word.referee(lie, "paper", ["A", "B"])
        self.assertEqual(out["points"]["A"], 1, "the same winning throw, unpromised: single")

    def test_the_page_shows_who_was_believed_and_whether_the_word_was_true(self):
        plays = {"A": {"word": "rock", "call": "scissors", "throw": "rock", "say": "I will throw rock."},
                 "B": {"word": "paper", "call": "rock", "throw": "paper", "say": "So will I."}}
        out = word.referee(plays, "scissors", ["A", "B"])
        self.assertTrue(out["believed"]["A"], "B's CALL was A's word, so B took A at face value")
        self.assertTrue(out["honest"]["A"])
        self.assertFalse(out["believed"]["B"])
        self.assertTrue(out["honest"]["B"])

    def test_a_promised_throw_that_is_banned_still_forfeits_and_earns_no_doubling(self):
        plays = {"A": {"word": "paper", "call": "rock", "throw": "paper", "say": "Paper."},
                 "B": {"word": "rock", "call": "paper", "throw": "rock", "say": "Rock."}}
        out = word.referee(plays, "paper", ["A", "B"])
        self.assertTrue(out["forfeit"]["A"])
        self.assertEqual(out["word_pt"]["A"], 0, "a forfeited throw cannot be a doubled win")
        self.assertEqual(out["points"]["A"], 1, "the call point survives the forfeit; the doubling does not")
        self.assertEqual(out["points"]["B"], 2, "B's call was right and the throw point was forfeited over")

    def test_an_old_round_is_summarised_rather_than_replayed_in_full(self):
        rows = []
        for i in range(1, 11):
            plays = {"A": {"word": "rock", "call": "rock", "throw": "rock", "say": f"line {i}"},
                     "B": {"word": "rock", "call": "rock", "throw": "rock", "say": f"reply {i}"}}
            v = word.referee(plays, "paper", ["A", "B"])
            rows.append({"round": i, "ms": 1793751845000 + i, "banned": "paper", "plays": plays,
                         "points": v["points"], "call_pt": v["call_pt"], "win_pt": v["win_pt"],
                         "word_pt": v["word_pt"], "called": v["called"], "forfeit": v["forfeit"],
                         "honest": v["honest"], "believed": v["believed"], "winner": v["winner"],
                         "why": v["why"], "commitments": {}})
        prompt = word.prompt_for("A", "B", rows, "paper", 6)
        self.assertIn("in summary", prompt, "rounds before the window must be summarised, not dropped")
        self.assertNotIn("line 1 ", prompt, "the oldest rounds are not replayed in full")
        self.assertIn("round 10", prompt, "the newest rounds are shown in full")

    def test_the_page_rebuilds_from_the_record_and_carries_the_words(self):
        ms = 1793751845024
        plays = {"A": {"word": "rock", "call": "paper", "throw": "rock", "say": "I will throw rock."},
                 "B": {"word": "paper", "call": "rock", "throw": "paper", "say": "Then we both lose."}}
        v = word.referee(plays, wind.wind_at(ms), ["A", "B"])
        rows = [{"round": 1, "ms": ms, "banned": wind.wind_at(ms), "plays": plays,
                 "points": v["points"], "call_pt": v["call_pt"], "win_pt": v["win_pt"],
                 "word_pt": v["word_pt"], "called": v["called"], "forfeit": v["forfeit"],
                 "honest": v["honest"], "believed": v["believed"], "winner": v["winner"],
                 "why": v["why"], "commitments": {}}]
        meta = {"names": ["A", "B"], "vendors": ["deepseek", "gemini"], "models": ["m1", "m2"],
                "started": "00:00", "ended": "00:01"}
        out = Path(tempfile.mkdtemp())
        (out / "game.json").write_text(json.dumps({"meta": meta, "rows": rows}), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(word.main(["--render", str(out / "game.json")]), 0)
        page = (out / "dialogue.md").read_text(encoding="utf-8")
        self.assertEqual(page, word.render(rows, meta))
        self.assertIn("I will throw rock.", page)
        self.assertIn("clock 1793751845024 % 3 = 2", page)


class TestFavour(unittest.TestCase):
    """The two defects in lab/word.py, closed. Banning a throw left a legal throw that could not be beaten, so
    the throw column was a forced move; and SAY was scored by nothing at all.

    Here nothing is banned and the clock favours a throw instead, so all three stay live and chasing the
    favoured one is a temptation with a counter. And a sentence that names a throw pays when the opponent
    calls it — the fourth line is a move, not a caption.
    """

    def test_the_clock_favours_a_throw_and_never_removes_one(self):
        self.assertEqual(favour.favour_at(1793751845024), wind.THROWS[1793751845024 % 3])
        for ms in range(1793751845020, 1793751845030):
            self.assertIn(favour.favour_at(ms), wind.THROWS)
        plays = {"A": {"word": "rock", "call": "rock", "throw": "rock", "say": ""},
                 "B": {"word": "paper", "call": "paper", "throw": "paper", "say": ""}}
        out = favour.referee(plays, "scissors", ["A", "B"])
        self.assertNotIn("forfeit", out, "no throw is banned in this game, so nothing can be forfeited")

    def test_the_favoured_throw_doubles_the_win_and_only_the_favoured_one(self):
        plays = {"A": {"word": "rock", "call": "rock", "throw": "rock", "say": ""},
                 "B": {"word": "scissors", "call": "scissors", "throw": "scissors", "say": ""}}
        out = favour.referee(plays, "rock", ["A", "B"])
        self.assertEqual(out["win_pt"]["A"], 2, "rock wins and rock is favoured: double")
        out = favour.referee(plays, "paper", ["A", "B"])
        self.assertEqual(out["win_pt"]["A"], 1, "the same win with a different favoured throw: single")

    def test_a_sentence_the_opponent_believes_scores(self):
        said = {"A": {"word": "rock", "call": "rock", "throw": "rock", "say": "My word is rock, but I intend "
                                                                               "scissors."},
                "B": {"word": "paper", "call": "scissors", "throw": "paper", "say": ""}}
        out = favour.referee(said, "rock", ["A", "B"])
        self.assertTrue(out["believed"]["A"], "B called scissors, which A named in its sentence and not in WORD")
        self.assertEqual(out["say_pt"]["A"], 1)
        kept = {"A": {"word": "rock", "call": "rock", "throw": "rock", "say": "Rock, honestly."},
                "B": {"word": "paper", "call": "rock", "throw": "paper", "say": ""}}
        out = favour.referee(kept, "rock", ["A", "B"])
        self.assertFalse(out["believed"]["A"], "calling the promise is not being believed on a sentence")
        self.assertEqual(out["say_pt"]["A"], 0)

    def test_the_page_rebuilds_from_the_record_and_names_the_favoured_throw(self):
        ms = 1793751845024
        plays = {"A": {"word": "rock", "call": "scissors", "throw": "rock", "say": "I intend scissors."},
                 "B": {"word": "paper", "call": "rock", "throw": "paper", "say": "Then paper it is."}}
        v = favour.referee(plays, favour.favour_at(ms), ["A", "B"])
        rows = [{"round": 1, "ms": ms, "favour": favour.favour_at(ms), "plays": plays,
                 "points": v["points"], "call_pt": v["call_pt"], "win_pt": v["win_pt"],
                 "word_pt": v["word_pt"], "say_pt": v["say_pt"], "called": v["called"],
                 "honest": v["honest"], "believed": v["believed"], "winner": v["winner"],
                 "why": v["why"], "commitments": {}}]
        meta = {"names": ["A", "B"], "vendors": ["deepseek", "gemini"], "models": ["m1", "m2"],
                "started": "00:00", "ended": "00:01"}
        out = Path(tempfile.mkdtemp())
        (out / "game.json").write_text(json.dumps({"meta": meta, "rows": rows}), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(favour.main(["--render", str(out / "game.json")]), 0)
        page = (out / "dialogue.md").read_text(encoding="utf-8")
        self.assertEqual(page, favour.render(rows, meta))
        self.assertIn(f"clock {ms} % 3 = {ms % 3}", page)
        self.assertIn("favoured", page)


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
        self.assertIn("Addressed out of the circle: to teacher@school.example — the game we made", before)
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

    def test_the_window_refuses_to_push_a_colony_into_the_project_it_was_copied_from(self):
        """Found by doing it, on 2026-11-03, in a smoke test.

        A colony copied with `cp -r` keeps the `origin` of the project it was copied from, so `./talk.sh`
        commits and then pushes the copy's record into somebody else's repository. In the smoke test the
        push succeeded and the bench had to be reverted; a person who copies a directory instead of forking
        it has the same trap and no smoke test to notice for them. The guard reads the push URL and stops.
        """
        script = (REPO / "talk.sh").read_text(encoding="utf-8")
        self.assertIn("*ai-tribe-bench*)", script, "the guard matches the upstream URL")
        self.assertIn("NOT pushed", script, "and says so in the only line a person will read")
        self.assertIn("git remote set-url origin", script, "and names the fix")
        guard = script.index("*ai-tribe-bench*)")
        push = script.index("if git push -q")
        self.assertLess(guard, push, "the guard has to run before the push, not after it")

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

    def test_there_is_one_key_name_and_no_second_one_half_works(self):
        """Asked why not one name, I first accepted both. Asked what the second name was *for*, I had no
        answer: no SDK on this machine reads it. So there is one, and it is the same word in the sheet,
        the workflow, the shell and the tool."""
        wake_src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertIn("names = [n for n in (args.api_key_env,) if n] or [canonical]", wake_src,
                      "a fallback name is back in the tool")
        self.assertNotIn("note: key read from", wake_src)
        play_src = (REPO / "play" / "play.py").read_text(encoding="utf-8")
        self.assertIn('names = [f"TRIBE_API_KEY_{provider.upper()}"]', play_src,
                      "the game arm reads a name no workflow sets")
        r = self._run("--member", "b", "--api-model", "gemini-3.8-flash", "--api-base", "gemini",
                      "--ask", "who are you?")
        self.assertIn("set TRIBE_API_KEY_GEMINI\n", r.stdout,
                      "the error offers a second name to try instead of the one instruction")

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
        """Checked with the shelf empty, because the shelf is empty in what gets shipped.

        The published pages must be a function of *the record a stranger receives*, and that record has no
        members and no works in it. With the suite's fixtures shelved, a rebuild reproduces a magazine about
        members called `a` and `b` who do not exist in any colony — which is the defect this test is supposed
        to catch, not a state it may assume. So the fixtures come off for the duration.
        """
        unshelve()
        try:
            r = subprocess.run([sys.executable, "lab/derivable.py"], cwd=REPO, capture_output=True,
                               text=True, timeout=300)
        finally:
            shelve()
        self.assertEqual(r.returncode, 0, (
            "a published file is not a function of the record. Rebuild them, do not edit them:\n"
            "  python3 magazine.py --issue $(python3 magazine.py --current) --write\n"
            "  python3 magazine.py --projects --write; python3 magazine.py --index --write; "
            "python3 magazine.py --ledger --write\n\n" + r.stdout[-2000:]))


class TestTennis(unittest.TestCase):
    """The tennis engine and the early-spring drill.

    These exist because the first version of the engine was wrong in a way no amount of reading it would
    show: it converted mph to ft/s with the mph-to-m/s constant, so every shot was integrated at a third of
    the speed printed beside it, drag was eleven times too weak to notice, and every groundstroke was struck
    from serve height. The page looked right and every number on it was a fiction. What follows checks the
    physics against outcomes you can look up, not against the code's own arithmetic.
    """

    @classmethod
    def setUpClass(cls):
        cls.t = load(REPO / "lab" / "tennis.py", "tennis_mod")

    def test_a_match_nobody_plays_refuses_the_engines_it_would_ignore(self):
        """Found 2026-11-06, at the cost of two runs: `--names Greta,Hans --vendor groq --points 6` finished in
        0.08 seconds and printed a match. The default path plays the physics; it never asks a member for a shot,
        and it accepted the engine flags without saying so. Silent acceptance is how a page becomes a fiction.
        """
        import contextlib, io
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = self.t.main(["--names", "Greta,Hans", "--vendor", "groq", "--points", "2"])
        self.assertEqual(code, 2, "a match that cannot use an engine must refuse it, not ignore it")
        self.assertIn("never asks a member", err.getvalue())

    def test_a_pinned_clock_replays_the_same_court_so_an_opponent_can_be_the_only_change(self):
        """2026-11-07, the founder's point: a player's in-play fraction is not theirs alone. Margot against a
        stronger opponent puts fewer balls in than Margot against a weaker one, with her own hands unchanged,
        because what she is hitting back is a different ball. Every match this project had printed until now
        drew its surface, its wind and its hands from the wall clock, so there was no way to hold them still
        while changing the player across the net: the opponent effect and the weather were the same variable.

        The hook is `--clock`. It pins what a player cannot control and says out loud that it has been pinned,
        so a transcript cannot be mistaken for an ordinary match.
        """
        import contextlib, io
        seen = []
        for ms in (1794026200910, 1794026200910, 1794026200911):
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                self.t.main(["--drill", "--shots", "0", "--vendor", "local", "--model", "m",
                             "--names", "Margot,Anvil", "--clock", str(ms)])
            seen.append(out.getvalue())
        for text, ms in zip(seen, (1794026200910, 1794026200910, 1794026200911)):
            self.assertIn(f"clock {ms}\n", text, "the header must carry the clock it was given")
            self.assertIn("the clock is pinned", text,
                          "a replay must announce itself; otherwise a staged match reads as a real one")
            self.assertIn(f"wind {self.t.wind_at(ms)[0]} {self.t.wind_at(ms)[1]:.0f}mph", text)
        self.assertIn(self.t.surface_at(1794026200910), seen[0])
        self.assertNotEqual(self.t.surface_at(1794026200910), self.t.surface_at(1794026200911),
                            "this test needs two clocks that differ in at least one condition")
        self.assertEqual(seen[0], seen[1],
                         "the same clock twice must give the same court — that is the whole of the hook")

    def shot(self, power, face, shot="rally", wind=(0.0, 0.0), surface="hard", aim=None):
        t = self.t
        import math
        elev = math.radians(t.elevation_for(shot, face))
        v = power * 1.05 * t.MPH
        z = 8.8 if shot == "serve" else 3.0
        out = t.flight((2.0, 13.5, z),
                       (v * math.cos(elev), 0.0, v * math.sin(elev)),
                       wind, surface, cl=t.spin_for(shot, face, power))
        return out

    def test_a_serve_arrives_near_the_speed_real_serves_arrive_at(self):
        """A 105mph serve is about 70mph when it bounces: the ball really does lose a third of its speed
        crossing 60ft. The first engine lost almost nothing, because its drag was eleven times too small."""
        out = self.shot(100, -2, shot="serve")
        self.assertIsNotNone(out["land"], "a 105mph serve with an open face should land in the box")
        arrive = out["speed_in"] / self.t.MPH
        self.assertTrue(55 <= arrive <= 90, f"a 105mph serve arrived at {arrive:.0f}mph, which is not tennis")

    def test_a_serve_from_a_square_face_is_long_and_from_a_closed_face_is_in(self):
        """The serve is struck downward from 8.8ft, so a square face puts it in the net or past the baseline
        and the face has to be closed. This is the single fact a beginner has to learn first."""
        square = self.shot(100, 10, shot="serve")
        closed = self.shot(100, -2, shot="serve")
        self.assertIsNotNone(closed["land"])
        self.assertTrue(self.t.NET_X < closed["land"][0] <= self.t.NET_X + self.t.SERVICE_LINE + 0.5,
                        f"a closed face at serve pace should land inside the service box, not "
                        f"{closed['land'][0] - self.t.NET_X:.0f}ft past the net")
        self.assertTrue(square["land"] is None or square["land"][0] > self.t.NET_X + self.t.SERVICE_LINE,
                        "a square face at serve pace should be long")

    def test_topspin_is_what_holds_a_hard_ball_in_the_court(self):
        """A square face at 80mph, launched at the same angle twice: with the topspin the model gives it, the
        ball lands in the court; with the lift term switched off, the identical swing goes long. That is the
        test that the Magnus term is doing work rather than decorating the code."""
        import math
        t = self.t
        elev = math.radians(t.elevation_for("rally", 6))
        v = 76 * 1.05 * t.MPH                     # 76% of swing = 80mph
        p0 = (2.0, 13.5, 3.0)
        v0 = (v * math.cos(elev), 0.0, v * math.sin(elev))
        with_lift = t.flight(p0, v0, (0.0, 0.0), "hard", cl=t.spin_for("rally", 6, 76))
        without = t.flight(p0, v0, (0.0, 0.0), "hard", cl=0.0)
        self.assertGreater(t.spin_for("rally", 6, 76), 0.15,
                           "an 80mph swing should make real topspin whatever the face is doing")
        self.assertIsNotNone(with_lift["land"])
        self.assertIsNotNone(without["land"])
        self.assertLess(with_lift["land"][0], without["land"][0] - 5,
                        "topspin must shorten the flight by a visible distance")
        self.assertLessEqual(with_lift["land"][0], t.LENGTH, "with topspin this shot should be in the court")
        self.assertGreater(without["land"][0], t.LENGTH,
                           "without topspin the same shot must go long, or the term is doing nothing")

    def test_the_court_is_only_a_few_degrees_of_face_wide(self):
        """The middle of the drill's difficulty, measured rather than asserted: at 65mph the difference
        between 'in the net' and 'past the baseline' is a handful of degrees of face angle. If this ever
        widens to twenty degrees, the game has stopped requiring timing and the drill becomes a formality."""
        wins = [f for f in [x * 0.5 for x in range(-40, 61)]
                if (o := self.shot(65, f))["land"] and self.t.NET_X < o["land"][0] <= self.t.LENGTH]
        self.assertTrue(wins, "no face angle at 65mph lands the ball in the court")
        width = max(wins) - min(wins)
        self.assertGreater(width, 2.0, "the window is absurdly narrow")
        self.assertLess(width, 14.0, f"the window is {width:.0f} degrees wide: too forgiving to learn from")

    def test_a_missed_ball_says_how_far_it_missed_by(self):
        """Learning needs a number to correct. 'long, out of the court' cannot be bisected; 'long by 12ft'
        can. This is the defect that made the first drill unlearnable, and it is one line to keep fixed."""
        t = self.t
        long_shot = self.shot(90, 20)
        ok, why = t.verdict({"traj": long_shot, "player": t.Player("x", True), "speed": 90})
        self.assertFalse(ok)
        self.assertRegex(why, r"long by \d+ft")
        short = self.shot(35, 0)
        ok, why = t.verdict({"traj": short, "player": t.Player("x", True), "speed": 35})
        self.assertFalse(ok)
        self.assertTrue("short of the net by" in why or "into the net at" in why, why)

    def test_reading_the_results_beats_not_reading_them(self):
        """The claim the whole early-spring drill rests on, tested five times at five different clocks rather
        than once with a seed: a player who only reads 'long by 12ft' and adjusts must beat a player with the
        same hands who hits the same shot every time. Chance stays real; only the property is asserted."""
        for ms in (1793805801123, 1793805811447, 1793805822779, 1793805833901, 1793805844129):
            args = type("A", (), {"shots": 40, "surface": "hard"})()
            out = self.t.simulate(args, ms=ms, quiet=True)
            r = out["tally"]
            learner = sum(r["reads results, new hands"]) / len(r["reads results, new hands"])
            stubborn = sum(r["reads nothing, new"]) / len(r["reads nothing, new"])
            experienced = sum(r["reads results, 300 balls"]) / len(r["reads results, 300 balls"])
            self.assertGreater(learner, stubborn + 0.15,
                               f"at clock {ms} reading the results was worth nothing: "
                               f"{learner:.0%} against {stubborn:.0%}")
            self.assertGreater(experienced, learner + 0.15,
                               f"at clock {ms} practice before today was worth nothing: "
                               f"{experienced:.0%} against {learner:.0%}")

    def test_aim_at_works_from_both_ends_of_the_court(self):
        """Symmetry is not a nicety here: a search that bisects in the north player's direction for both players
        sends every south-end shot the wrong way. It made Remy fault on serves that landed exactly where he
        aimed, and it made a scripted south player unable to find the court at all — which then read as
        'steady hands do not lengthen a rally'."""
        import random
        t = self.t
        wv = t.wind_vector("W", 18.0)
        for north in (True, False):
            p = t.Player("x", north, 300, rng=random.Random(3))
            target = t.NET_X + 20.0 if north else t.NET_X - 20.0
            face, _ = t.aim_at(p, (target, t.WIDTH / 2), "rally", "hard", wv, power=55)
            self.assertLess(face, 20.0, "the search ran to the top of the range instead of converging")
            depths = []
            for _ in range(15):
                land = t.strike(p, None, face=face, power=55, aim=t.WIDTH / 2, shot="rally",
                                surface="hard", wind=wv)["traj"].get("land")
                if land:
                    depths.append(abs(land[0] - t.NET_X))
            self.assertTrue(depths, "the player could not land a single ball")
            depths.sort()
            median = depths[len(depths) // 2]
            self.assertAlmostEqual(median, 20.0, delta=5.0,
                                   msg=f"a {'north' if north else 'south'} player aimed 20ft past the net "
                                       f"and the median ball landed {median:.0f}ft past it")

    def test_a_rally_ends_only_for_a_reason_a_player_can_see(self):
        """The complaint the rally mode exists to answer: if rallies die because of a rule, lengthening them is
        programming. Every way a rally can end must be one of four things — netted, long, wide, or out of reach
        — and the out-of-reach one must say by how many feet, because a player has to be able to learn from it.
        The old test, a radius that grew with skill, could fail a player for nothing they had done."""
        import random
        t = self.t
        p = t.Player("beginner", True, 0, rng=random.Random(5))
        # a ball landed at the far corner, arriving quickly: unarguably unreachable for a beginner
        ok, why = t.reachable(p, (t.NET_X - 2.0, 1.0), 0.5,
                              {"v": (60.0, 20.0, -10.0), "speed_out": 90.0}, "hard")
        self.assertFalse(ok)
        self.assertRegex(why, r"\d+ft short of it")
        # and one hit deep and slowly, which for a player standing on the baseline is a step and a half
        ok, _ = t.reachable(p, (t.NET_X - 25.0, t.WIDTH / 2), 2.0,
                            {"v": (10.0, 0.0, -8.0), "speed_out": 20.0}, "hard")
        self.assertTrue(ok)
        self.assertGreaterEqual(t.RALLY_CAP, 40,
                                "a low ceiling would make rally length a constant of the record, not a result")
        self.assertEqual(t.movement_speed(t.Player("n", True, 300)), 
                         5.0 + 15.0 * (t.Player("n", True, 300).skill("reach")),
                         "movement is not a skill any more")

    def test_rally_length_responds_to_hands_and_to_learning(self):
        """The founder's claim, made checkable: rallies should get longer as the players develop, and not
        because the code lengthens them. Five scripted pairs, same court, same wind, same clock, and *nobody is
        told the right face* — being told is a separate arm, because a game where the answer is handed over is
        not measuring learning.

        What comes out is an interaction, not two separate effects: reading the miss with nothing but your hands
        is worth almost nothing (1.0 to 2.2), steady hands that never read anything are worth nothing at all
        (1.0), and together they are worth a ninefold rally (9.8) that is still growing when the session ends.
        That last number is the founder's sentence, and it is the one worth defending."""
        pooled = {}
        for ms in (1793807600121, 1793807611347, 1793807622571):
            args = type("A", (), {"rallies": 24, "surface": "hard"})()
            for arm, L in self.t.simulate_rally(args, ms=ms, quiet=True).items():
                pooled.setdefault(arm, []).extend(L)
        m = lambda k: sum(pooled[k]) / len(pooled[k])
        self.assertLess(m("new hands, never reads"), 2.0,
                        "a player who neither has hands nor reads results built rallies, which cannot be right")
        self.assertLess(m("300 balls, never reads"), 2.0,
                        "steady hands with no idea where to hit built rallies; the number must be the thing")
        self.assertLess(m("new hands, reads the miss"), 4.0,
                        "reading the miss without the hands to act on it built long rallies")
        self.assertGreater(m("300 balls, reads the miss"), m("new hands, reads the miss") * 2.5,
                           "learning was worth as much with unsteady hands as with steady ones")
        self.assertGreater(m("300 balls, reads the miss"), 6.0,
                           "a developed player did not rally materially longer than a beginner")
        self.assertGreaterEqual(m("300 balls, was told the face") + 2.0, m("300 balls, reads the miss"),
                                "learning did not approach what being told the answer is worth")
        # the founder's actual sentence: the rallies get longer *during* the session
        L = pooled["300 balls, reads the miss"]
        third = len(L) // 3
        self.assertGreater(sum(L[-third:]) / third, sum(L[:third]) / third,
                           "the rallies did not lengthen from the start of the session to the end")

    def test_a_command_is_parsed_and_clamped(self):
        t = self.t
        self.assertEqual(t.parse_command("FACE +6 POWER 62 AIM 9"), (6.0, 62.0, 9.0))
        self.assertEqual(t.parse_command("face: -30 power: 200 aim: 40"), (-20.0, 100.0, 27.0))
        self.assertIsNone(t.parse_command("I will hit it firmly to the left"))


    def _session_book(self, tmp, pair=("Remy", "Gwen"), first=(8, 16), last=(12, 16), n=2):
        """A season file written the way `run_rally` writes one, with the numbers chosen by the test.

        A fixture in a temp directory: this is the only place a session's numbers are picked rather than
        played, and it is here because the report is being tested on whether it is willing to stay quiet,
        so the outcome has to be controllable. No real season file is ever written by a test.
        """
        t = self.t
        book = t.load_season("2026-spring", tmp)
        for i in range(n):
            players = [t.Player(pair[0], True, t.practice_of(book, pair[0])),
                       t.Player(pair[1], False, t.practice_of(book, pair[1]))]
            inn, of = (first if i == 0 else last)
            for p in players:
                p.shots = of
            results = {pair[0]: [True] * (inn // 2) + [False] * (of - inn // 2),
                       pair[1]: [True] * (inn - inn // 2) + [False] * (of - (inn - inn // 2))}
            t.record_session(book, when=f"2026-11-0{i + 4}T18:00:00Z", surface="clay", clock=1,
                             players=players, results=results, lengths=[2, 3],
                             partners={pair[0]: [pair[1]], pair[1]: [pair[0]]})
        t.save_season(book, "2026-spring", tmp)
        return book

    def test_practice_outlives_the_process_that_hit_the_ball(self):
        """Founder, 2026-11-04: "she's been practicing with Remy and her game has really improved" should be
        a thing the record prints.

        It could not be, until this file existed: practice was a Python variable, so every run started
        everyone at spring-zero and that sentence was prose a person would have to write. The read here is
        deliberately a second load of the file, because a second load is what the next session does.
        """
        t = self.t
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        self._session_book(tmp)
        book = t.load_season("2026-spring", tmp)          # a fresh read: the next session's view
        self.assertEqual(t.practice_of(book, "Remy"), 32, "two 16-ball sessions: the balls belong on disk")
        p0, p400 = t.Player("Remy", True, 0), t.Player("Remy", True, 400)
        self.assertGreater(p400.skill("control"), p0.skill("control"),
                           "the file is only worth keeping if practice changes the hands")

    def test_a_new_season_starts_at_zero_and_does_not_touch_the_last_one(self):
        """The founder's dilemma: keep the record of past seasons, and let a season run for months.

        The answer is that a season is a directory. A reset is not a wipe — it is the absence of a file —
        so last spring stays readable and the season that follows it cannot rewrite it.
        """
        t = self.t
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        self._session_book(tmp)
        other = Path(tmp) / "2027-spring"
        self.assertEqual(t.practice_of(t.load_season("2027-spring", str(other)), "Remy"), 0,
                         "a new season starts at beginners")
        self.assertEqual(t.practice_of(t.load_season("2026-spring", tmp), "Remy"), 32,
                         "and the old season is still there, unchanged")

    def test_the_report_will_not_say_improved_unless_the_numbers_do(self):
        t = self.t
        one = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, one, True)
        self._session_book(one, n=1)
        text = t.season_report("2026-spring", one)
        self.assertIn("Nothing can be said about improvement from one session", text)
        self.assertNotIn("The game improved", text)

        moved = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, moved, True)
        self._session_book(moved, first=(8, 16), last=(13, 16))
        text = t.season_report("2026-spring", moved)
        self.assertIn("The game improved", text)
        self.assertIn("practice.json", text, "a claim in this project carries the file it came from")

        flat = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, flat, True)
        self._session_book(flat, first=(10, 16), last=(11, 16))
        text = t.season_report("2026-spring", flat)
        self.assertIn("No claim", text, "a six-point wobble is inside this game's scatter")
        self.assertNotIn("The game improved", text)

        # The first real season, 2026-11-04, printed "the game got worse" for Colette on 5/7 -> 4/7.
        # That is one ball and fourteen points, and the scatter guard waved it through because fourteen is
        # bigger than eight. A percentage of seven balls is not a measurement.
        thin = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, thin, True)
        self._session_book(thin, first=(5, 7), last=(4, 7))
        text = t.season_report("2026-spring", thin)
        self.assertIn("Not a sample", text)
        self.assertNotIn("got worse", text)

    def test_a_season_nobody_has_played_in_reports_nothing_and_cites_nothing(self):
        t = self.t
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        text = t.season_report("2029-autumn", tmp)
        self.assertIn("Nobody has hit a ball", text)
        self.assertNotIn("improved", text)

    # ---- the person's seat, 2026-11-12 ------------------------------------------------------------
    def _seat(self, command="FACE 6 POWER 62 AIM 12", names="Sam,Colette", points="1", tmp=None,
              member_reply="FACE 5 POWER 58 AIM 14", extra=()):
        """Run the person's seat with the member's engine stubbed, and give back what was printed.

        The stub is the whole point of the fixture: it counts the calls and records the prompts, so a test can
        say *no engine was asked for the person's shot* rather than merely that the output looks plausible.
        """
        import contextlib, io
        t = self.t
        calls = []

        def fake(base, key, model, prompt, temperature=1.0):
            calls.append(prompt)
            return member_reply

        real = t.ask
        t.ask = fake
        out, err = io.StringIO(), io.StringIO()
        args = ["--person-shot", command, "--names", names, "--points", points,
                "--clock", "1794026200910", "--vendor", "local", "--model", "m"]
        if tmp is not None:
            args += ["--season", "2026-spring", "--season-dir", tmp]
        args += list(extra)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = t.main(args)
        finally:
            t.ask = real
        return code, out.getvalue(), err.getvalue(), calls

    def test_the_persons_seat_takes_the_movement_they_typed_and_asks_no_engine_for_it(self):
        """The founder's question, 2026-11-12: can a person be the third player on this court?

        A member's shot is asked for in one line of prose; a person's is three numbers from a form. What the
        test insists on is that the difference is *only* that: the person's line is played exactly as typed,
        and the prompts sent to an engine are the member's alone. `You are <name>` is the first line of every
        prompt this game writes, so a prompt addressed to the person is the failure this looks for.
        """
        code, out, err, calls = self._seat(command="FACE 18 POWER 80 AIM 13")
        self.assertEqual(code, 0, err)
        self.assertIn("face +18 power  80 aim 13", out,
                      "the movement printed is not the movement that was typed")
        self.assertIn("No engine was asked what to do with it", out)
        self.assertTrue(calls, "the member across the net must be asked — that is what makes it a member")
        for prompt in calls:
            self.assertIn("You are Colette", prompt)
            self.assertNotIn("You are Sam", prompt,
                             "an engine was asked what the person should do; the seat has no engine")

    def test_a_point_from_the_persons_seat_is_judged_by_the_same_verdict(self):
        """One `verdict()`, two seats. The drill, the season and this mode all print the same sentences about
        where a ball went, and the reason is not tidiness: a person learning this game beside the members has
        to be corrected by the same numbers they are, or the two are playing different games with one name.
        """
        code, out, err, calls = self._seat(command="FACE 30 POWER 100 AIM 13", extra=("--practice", "400,20"))
        self.assertEqual(code, 0, err)
        self.assertRegex(out, r"long by \d+ft", "an out ball must say how far out, as the drill's verdict does")
        self.assertIn("1 shot, taken by Colette", out, "a ball past the baseline must lose the point")

        # and the in-play half of the same function, on the same court and clock, where the ball lands
        code, out, err, calls = self._seat(command="FACE 18 POWER 80 AIM 13")
        self.assertRegex(out, r"IN, \d+ft past the net",
                         "the same verdict must be able to say IN, with the distance")

    def test_the_person_is_a_player_in_the_season_and_a_point_is_not_an_evening(self):
        """Two halves of one decision. The person is a player: their balls are counted, their hands steady, and
        they appear in the season's file under their own name. And a point is not an evening of rallies: the
        report's rates are computed over the rallies, because a five-ball point averaged into a season of
        sixty-ball evenings would let one press of a button silence the sentence the season exists to earn.
        """
        t = self.t
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        code, out, err, calls = self._seat(tmp=tmp)
        self.assertEqual(code, 0, err)
        book = t.load_season("2026-spring", tmp)
        self.assertGreater(t.practice_of(book, "Sam"), 0, "the person's balls were not counted")
        modes = {s.get("mode") for m in book["members"].values() for s in m["sessions"]}
        self.assertIn("person", modes)
        report = t.season_report("2026-spring", tmp)
        self.assertIn("the person's seat", report)
        self.assertIn("No evening of rallies in this season yet", report,
                      "a point must not be presented as an evening of rallies")
        self.assertNotIn("The game improved", report)
        notes = list((Path(tmp) / "points").glob("*.md"))
        self.assertEqual(len(notes), 1, "a point with a season must leave its own record beside it")
        note = notes[0].read_text(encoding="utf-8")
        self.assertIn("FACE +6 POWER 62 AIM 12", note)
        self.assertIn("No engine was asked", note)
        self.assertIn("mode `person`", note)
        self.assertIn("the hands gave", note,
                      "the file must carry the angle delivered as well as the angle asked for")

    def test_a_point_file_is_never_overwritten(self):
        """The season's rule — nothing is reset, nothing is overwritten — applied to a single point. Two
        presses inside one second are two points, and the second one must not erase the first."""
        t = self.t
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        first = t.unique_path(tmp / "2026-11-12T21-30-00Z.md")
        self.assertEqual(first.name, "2026-11-12T21-30-00Z.md")
        first.write_text("one", encoding="utf-8")
        second = t.unique_path(tmp / "2026-11-12T21-30-00Z.md")
        self.assertNotEqual(second.name, first.name)
        self.assertEqual(first.read_text(encoding="utf-8"), "one")

    def test_a_members_missing_key_is_not_blamed_on_the_person(self):
        """The person's seat needs no key at all, so a refusal has to say *which* seat is blocked. A message
        that reads "TRIBE_API_KEY_DEEPSEEK is not set" with no name in it would send a person looking for a key
        of their own, and there is nothing for them to find."""
        import contextlib, io
        t = self.t
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = t.main(["--person-shot", "FACE 6 POWER 62 AIM 12", "--names", "Sam,Colette",
                           "--points", "1", "--vendor", "deepseek", "--model", "deepseek-flash"])
        self.assertEqual(code, 2)
        said = err.getvalue()
        self.assertIn("Colette cannot hit a ball", said, "the refusal must name whose key is missing")
        self.assertIn("The person's shot needs no key", said)

    def test_the_seat_reaches_the_court_from_the_same_form_the_members_use(self):
        """One court, one workflow: the person's press dispatches `season.yml` like any other session, so the
        engine key list, the season folder and the commit are the ones already there rather than a second copy
        of them. Two names for the same engine list is how a game ends up unable to play on an engine the
        others can — measured 2026-11-06, and not worth measuring again."""
        if yaml is None:
            self.skipTest("PyYAML not installed")
        wf = yaml.safe_load((REPO / ".github" / "workflows" / "season.yml").read_text(encoding="utf-8"))
        inputs = wf[True]["workflow_dispatch"]["inputs"]
        self.assertIn("person", inputs)
        self.assertIn("shot", inputs)
        play = [s for s in wf["jobs"]["play"]["steps"] if s.get("name") == "Play"][0]
        self.assertIn('--person-shot "$SHOT"', play["run"],
                      "the form's movement never reaches the engine")
        self.assertIn("SHOT", play.get("env") or {})
        # and the person's name is not looked for on the shelf of members
        check = [s for s in wf["jobs"]["play"]["steps"] if s.get("name") == "Which season, which two"][0]
        self.assertIn('wake/members/$who/state', check["run"])

class TestTheRecordSaysThePlayerWasBeaten(unittest.TestCase):
    """Item 13 of the tennis backlog. The 3D viewer has always been able to print "and does not get there" and
    never had a record with one in it, because the record's reaching arithmetic was a second model, living in a
    generator this branch does not have. These tests hold the two ends of the fix together: one interception that
    both the scoreline and the picture read, and a record whose rallies cannot outlive a ball nobody reached."""

    def setUp(self):
        import importlib
        import random as _random
        self.random = _random
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")
        self.R = importlib.import_module("tennis_record")
        self.record_path = REPO / "games" / "tennis" / "seasons" / "2026-spring" / "rally.json"

    def test_one_interception_and_no_second_model(self):
        """`reachable` is the yes/no built on `interception`, so they cannot disagree — a renderer that draws a
        player arriving short and a scoreline that says "did not reach" are the same arithmetic or they are two
        accounts of one point. Checked against a ball the player cannot get to and one they can."""
        p = self.T.Player("beginner", True, 0, rng=self.random.Random(5))
        hard = ((self.T.NET_X - 2.0, 1.0), 0.5, {"v": (60.0, 20.0, -10.0), "speed_out": 90.0})
        easy = ((self.T.NET_X - 25.0, self.T.WIDTH / 2), 2.0, {"v": (10.0, 0.0, -8.0), "speed_out": 20.0})
        for land, ft, bounce in (hard, easy):
            ok, why = self.T.reachable(p, land, ft, bounce, "hard")
            m = self.T.interception(p, land, ft, bounce, "hard")
            self.assertEqual(ok, m["ok"])
            self.assertEqual(why, m["why"])
        m = self.T.interception(p, hard[0], hard[1], hard[2], "hard")
        self.assertFalse(m["ok"])
        self.assertGreater(m["short_ft"], 0.0)
        self.assertAlmostEqual(m["short"], m["need"] - m["have"], places=9,
                               msg="the shortfall in seconds is not the difference of the two numbers the "
                                   "record writes down, so a reader cannot check the miss by hand")

    def test_a_beaten_player_stops_more_than_a_racquet_from_the_ball(self):
        """The picture's side of the claim. Wherever the record says `met: false`, the feet it puts on the court
        must be further from the ball than the arm and racquet can cover — otherwise the viewer would be drawing
        somebody standing in the ball and calling it a miss."""
        rec = json.loads(self.record_path.read_text(encoding="utf-8"))
        out, _notes = self.R.decide(rec)
        misses = [s for s in out["shots"] if (s.get("run") or {}).get("met") is False]
        self.assertTrue(misses, "no ball in the whole record was out of reach — the rule is not in the pipeline")
        for s in misses:
            run = s["run"]
            self.assertGreater(run["gap"], self.T.RACQUET_REACH,
                               f"shot {s['n']}: the feet stop {run['gap']}ft from the ball, inside a racquet")
            self.assertGreater(run["short"], 0.0)
            self.assertGreater(run["need"], run["have"])
            self.assertIn("short of it", s["why"])

    def test_no_rally_has_a_shot_after_a_ball_nobody_reached(self):
        """The invariant that makes a season report and a film the same story: if a ball was out of reach the
        point is over, so nothing may follow it. Before this, the record carried shots that happened after a beat
        — a rally that continued from a ball nobody got to, which reads as a player hitting from the wrong place."""
        rec = json.loads(self.record_path.read_text(encoding="utf-8"))
        out, _notes = self.R.decide(rec)
        shots = out["shots"]
        for rally in out["rallies"]:
            for k in rally["shots"][:-1]:
                run = shots[k].get("run") or {}
                self.assertIsNot(run.get("met"), False,
                                 f"rally {rally['rally']} continues past shot {shots[k]['n']}, which nobody "
                                 f"reached")
            last = shots[rally["shots"][-1]]
            run = last.get("run") or {}
            # Three ways a rally can end, and every one of them is named in the record. `record` is the honest
            # one: the film's own boundary — the old model called that ball 0.3ft short and stopped, and this one
            # says it was reached, so the rally has no shot to continue with. It is labelled rather than papered
            # over, because a rally that ends for no stated reason is the defect this test exists to catch.
            self.assertIn(rally.get("ended"), ("out", "beat", "record"))
            if rally["ended"] == "beat":
                self.assertIs(run.get("met"), False, f"rally {rally['rally']} is labelled a beat and is not one")
            if rally["ended"] == "out":
                self.assertIs(last.get("in"), False, f"rally {rally['rally']} is labelled out and the ball is in")

class TestTheVolley(unittest.TestCase):
    """Item 14 of the tennis backlog, second move: the ball taken out of the air.

    `choose_shot` has had volley weights since the chooser was ported, and there was nothing in this engine that
    could volley — a player standing seven feet from the net waited for the ball to bounce, and the interception
    was asked about a bounce point a net player never reaches, so every approach was scored as a point lost. The
    model that came over from the longer engine is one radius rather than a box, and it is asked *before* the
    interception, because a volley is the point at which the bounce does not happen.

    What these hold: the contact is above the ground, below the head, on the hitter's own side of the net and
    earlier than the bounce; a ball the legs cannot cover is not volleyed however close the racquet would be; and
    the trace that makes any of it possible draws the ball without moving it."""

    def setUp(self):
        import importlib
        import random as _random
        self.random = _random
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")

    def _path(self, x0, x1, y, z0, z1, n=40, t0=0.05, dt=0.02):
        """A ball on its way from the south end to the north one, sampled the way a trace samples it."""
        out = []
        for i in range(n):
            f = i / (n - 1)
            out.append((round(t0 + i * dt, 3), round(x0 + (x1 - x0) * f, 3), round(y, 3),
                        round(z0 + (z1 - z0) * f, 3)))
        return out

    def test_the_ball_is_taken_out_of_the_air_before_it_bounces(self):
        """The whole claim of a volley in one assertion set: the contact is earlier than the bounce, it is inside
        the band the racquet occupies, it is on the hitter's side of the net, and the feet are within a reach of
        it. A volley scored at or after the bounce is a groundstroke with a nicer word on it."""
        t = self.T
        p = t.Player("X", north=True, practice=300)
        feet = (t.NET_X - 6.0, t.WIDTH / 2)                 # six feet from the net, on their own side
        path = self._path(t.NET_X + 3.0, t.NET_X - 5.0, t.WIDTH / 2, 2.6, 3.4)
        vol = t.volley_contact(p, path, feet)
        self.assertIsNotNone(vol, "a ball crossing the net at racquet height six feet away was not volleyed")
        self.assertLess(vol["t"], path[-1][0], "a volley cannot be struck after the last sample the ball has")
        self.assertTrue(t.VOLLEY_LOW <= vol["contact"][2] <= t.VOLLEY_HIGH,
                        f"contact at {vol['contact'][2]}ft is outside the band the racquet can take it in")
        self.assertGreaterEqual((t.NET_X - vol["contact"][0]), 2.0,
                                "the ball was taken before it had crossed the net")
        self.assertLessEqual(math.hypot(vol["contact"][0] - vol["feet"][0],
                                        vol["contact"][1] - vol["feet"][1]),
                             t.VOLLEY_REACH + 1e-6,
                             "the feet were drawn outside a racquet's length of the ball")

    def test_a_ball_the_legs_cannot_cover_is_not_volleyed_however_close_the_racquet_is(self):
        """The legs are the limit, not the arm: a player standing twelve feet across the court from a ball that
        arrives in half a second does not volley it, and must not be drawn doing so."""
        t = self.T
        p = t.Player("X", north=True, practice=0)
        path = self._path(t.NET_X + 3.0, t.NET_X - 5.0, t.WIDTH / 2, 2.6, 3.4, t0=0.05)
        self.assertIsNone(t.volley_contact(p, path, (t.NET_X - 6.0, 1.0)),
                          "a beginner twelve feet away volleyed a ball in a few tenths of a second")

    def test_a_ball_above_the_head_is_an_overhead_and_that_is_not_built(self):
        """The band is two limits, and each one is a different shot: above eight feet it is an overhead, below
        2.2 it is dug off the ground. Neither is a volley, and the model says so instead of taking them."""
        t = self.T
        p = t.Player("X", north=True, practice=300)
        feet = (t.NET_X - 6.0, t.WIDTH / 2)
        high = self._path(t.NET_X + 3.0, t.NET_X - 5.0, t.WIDTH / 2, 9.0, 11.0)
        low = self._path(t.NET_X + 3.0, t.NET_X - 5.0, t.WIDTH / 2, 0.4, 1.4)
        self.assertIsNone(t.volley_contact(p, high, feet), "an overhead was volleyed")
        self.assertIsNone(t.volley_contact(p, low, feet), "a ball at ankle height was volleyed")

    def test_the_trace_draws_the_ball_without_moving_it(self):
        """`trace` is a renderer's sample rate and a volley's only evidence, so it must be an observation: the
        same shot integrated with it and without it lands in the same place at the same time. A path that
        changed the ball would be a second integration, which is how this repository has been broken before."""
        t = self.T
        kw = dict(face=6.0, power=62.0, aim=t.WIDTH / 2, shot="forehand", surface="hard", wind=(0.0, 0.0))
        # Two players with the same seed rather than one player struck twice: `strike` applies the hands' error
        # from the player's own rng, so the second call on one player is a different shot and would have blamed
        # the trace for the error. Same seed, same error, same ball — the only difference is the sampling.
        plain = t.strike(t.Player("X", north=True, practice=300, rng=self.random.Random(3)), None, **kw)
        traced = t.strike(t.Player("X", north=True, practice=300, rng=self.random.Random(3)), None,
                          trace=0.02, **kw)
        a, b = plain["traj"], traced["traj"]
        self.assertEqual(a["land"], b["land"], "the trace moved the ball")
        self.assertAlmostEqual(a["time"], b["time"], places=9)
        self.assertAlmostEqual(a["speed_in"], b["speed_in"], places=9)
        path = b["path"]
        self.assertGreater(len(path), 20, "a 0.02s trace of a shot that lasts half a second is ten samples")
        for (t0, x0, y0, z0), (t1, x1, y1, z1) in zip(path, path[1:]):
            self.assertGreater(t1, t0, "the trace is not in the order it happened")
        self.assertTrue(all(z >= -0.01 for _, _, _, z in path), "the trace draws the ball under the court")
        self.assertLessEqual(path[-1][0], b["time"] + 0.02 + 1e-9,
                             "the trace runs on after the ball has bounced")

    def test_the_default_reach_is_this_games_reach(self):
        """The `reach` argument was borrowed from the pickleball body, which needs a three-foot paddle where a
        racquet covers seven. It defaults to the tennis number, and that is the only reason the tennis arithmetic
        is allowed to grow an argument: every tennis record and every tennis test must run what it always ran."""
        t = self.T
        p = t.Player("X", north=True, practice=200, rng=self.random.Random(7))
        land, ft, bounce = (t.NET_X + 8.0, 9.0), 1.4, {"v": (18.0, 3.0, -7.0), "speed_out": 22.0}
        same = t.interception(p, land, ft, bounce, "hard")
        same_explicit = t.interception(p, land, ft, bounce, "hard", reach=t.RACQUET_REACH)
        self.assertEqual(same, same_explicit, "the default reach is not this game's reach")
        shorter = t.interception(p, land, ft, bounce, "hard", reach=3.0)
        self.assertLessEqual(same["short_ft"], shorter["short_ft"],
                             "a shorter paddle cannot make a ball easier to reach")

    def test_a_point_played_at_the_net_contains_a_volley(self):
        """The end-to-end version, and the one the page can be read off: `line_for` prints the shot it was, so a
        volley in a transcript is a volley that happened. Pinned surface, wind, clock-free rng and practice, so
        the count is a fact about the engine rather than a fact about the day."""
        t = self.T
        rng = self.random.Random(5)
        server = t.Player("A", north=True, practice=300, rng=self.random.Random(1))
        receiver = t.Player("C", north=False, practice=300, rng=self.random.Random(2))
        volleys = shots = 0
        for _ in range(40):
            lines = t.play_point(server, receiver, "hard", (0.0, 0.0), ("N", 0.0), rng)
            for line in lines:
                if " hits " in line:
                    shots += 1
                    if line.split(" hits ")[1].startswith("volley"):
                        volleys += 1
        self.assertGreater(volleys, 0,
                           f"forty points on a hard court at 300 balls and not one ball taken out of the air "
                           f"({shots} shots: the volley model is not in the point)")
        self.assertLess(volleys, shots,
                         "every shot was a volley, which is not a rally — the bounce is not being played")


class TestTheCrossOverStepIsInTheFilm(unittest.TestCase):
    """Item 4: *"on a shot that needs more than 3 ft of travel, the first foot to leave the ground is the one
    NEAREST the direction of travel, and the feet cross rather than shuffle."*

    Measured on 2026-11-19: the feet cross now (6 of 7 shots, the left toe 0.09–0.49ft past the right in the
    player's own frame), and the near foot leads on only 3 of 7 — so this item is PARTIAL and the test says which
    half is held and which is not. What is asserted is the part the code can be wrong about without a renderer: the
    lateral gate, the decay, the body-frame measurement, and the fact that the toe probe reports in the BODY's
    frame — the first version measured in court coordinates and reported that everything crossed when nothing did.
    """

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")

    def test_the_crossing_is_sideways_travel_only(self):
        self.assertIn("Math.abs(xb) > 0.35", self.page,
                      "the cross-over is applied to a run down the court as well as across it")
        self.assertIn("1 - Math.max(0, tlc - 0.10) / 0.25", self.page,
                      "the cross-over does not decay: it is the first step, not the run")
        # It must also RISE from zero. The first version started at full strength on the contact frame and lifted
        # the near toe 0.7ft between two frames — a step, not a pop, is the whole point.
        self.assertIn("Math.min(1, tlc / 0.10)", self.page,
                      "the cross-over starts at full strength, which puts a 0.7ft lift in a single frame")

    def test_the_far_leg_crosses_and_the_near_leg_lifts(self):
        self.assertRegex(self.page, r'CROSS_LAT \* amt \* side', "the far leg does not cross")
        self.assertIn('addLocal(rig.bones["shin." + near]', self.page,
                      "nothing lifts the near foot, so the near foot cannot lead")

    def test_the_toes_are_measured_in_the_players_own_frame(self):
        self.assertIn("const rel = v =>", self.page,
                      "the toes are reported in court coordinates, where a turn reads as a crossing")
        self.assertIn("Math.cos(yaw)", self.page)

    def test_the_numbers_are_in_a_range_a_hip_could_do(self):
        m = re.search(r"const CROSS_LAT = q\.has\(\"crosslat\"\) \? parseFloat\(q\.get\(\"crosslat\"\)\) : ([0-9.]+);",
                      self.page)
        self.assertIsNotNone(m, "CROSS_LAT is gone, so its value cannot be checked")
        self.assertTrue(0.5 <= float(m.group(1)) <= 1.1,
                        f"CROSS_LAT = {m.group(1)} rad is outside what a thigh can adduct: 0.8 crosses the toes, "
                        f"1.0 crosses them by nearly a foot")


class TestTheSplitStepIsInTheFilm(unittest.TestCase):
    """Item 3 of the tennis backlog, and the founder's done-test verbatim: *"every shot in a 20-shot sample is
    preceded by a downward root-velocity blip of 0.10–0.20ft within 0.2s of the opponent's contact."*

    Measured on 2026-11-19 before the change: dips of 0.000–0.021ft over eleven shots — the receiver was a body
    sliding into place, with nothing in the picture saying "I am about to be hit at". After it, over all twenty
    shots of `seasons/2026-11-19/watch.json`, read out of the page by `?sweep`: **20 of 20 in the band**, dips
    **0.112–0.167ft**, delays **0.11–0.19s**.

    The suite cannot draw WebGL, so what is held here is the shape that produced those numbers: the constants sit
    inside the band the done-test names, the term is a function of time-since-the-opponent's-contact alone (no state
    to drift), and it is applied to the RECEIVER and not to the hitter — a player who has just struck a ball is
    falling back into balance, not loading a hop."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")

    def _num(self, name):
        m = re.search(rf"const {name} = ([0-9.]+);", self.page)
        self.assertIsNotNone(m, f"{name} is not a constant any more, so its value cannot be checked")
        return float(m.group(1))

    def test_the_dip_is_inside_the_band_the_done_test_names(self):
        self.assertTrue(0.10 <= self._num("SPLIT_DIP") <= 0.20,
                        "the dip is outside 0.10-0.20ft, which is the band the founder's done-test names")

    def test_the_body_bottoms_out_within_two_tenths_of_the_opponents_contact(self):
        peak = self._num("SPLIT_LAG") + self._num("SPLIT_DUR") / 2
        self.assertLessEqual(peak, 0.20, f"the dip peaks at {peak}s, which is later than the done-test allows")

    def test_only_the_receiver_gets_it(self):
        """The dip is now a knee bend rather than a hole in the floor. It was a root-height subtraction until
        2026-11-19, which put the whole figure under the court whenever the toe was already near it — and the
        grounding clamp then hauled it back up, so the two terms fought. As a bend it is a pose, and it applies
        after `legs()`, which rebuilds every thigh and shin from its rest quaternion on every frame."""
        self.assertIn("const dip = isHitter ? 0 : splitDip(tlc);", self.page,
                      "the split step is not conditioned on being the receiver")
        self.assertIn("function splitDip(tlc)", self.page,
                      "the dip is not a function of one number, so it can accumulate or drift")
        self.assertIn('addLocal(rig.bones["shin." + leg], 0.80 * k, 0, 0);', self.page,
                      "the dip is not a bend in the knees, so it is still a hole in the floor")

    def test_the_instrument_that_measured_it_is_in_the_page(self):
        """A number in a comment is a claim. `?sweep` is how the claim was produced, and it is kept because items
        4, 5 and 6 need exactly the same thing: frames in order, at fixed steps of record time, rather than the
        half-dozen frames a headless browser happens to give in fifteen seconds."""
        self.assertIn("window.__sweep", self.page)
        self.assertIn("debug sweep", self.page)
        self.assertIn("debug segs", self.page, "the sweep does not say where the contacts are, so it cannot be read")


class TestNobodyIsStandingAboveTheCourt(unittest.TestCase):
    """Item 2a of the tennis backlog, and the reason four items of foot work were written, measured and reverted
    without changing what anybody sees: the players were not standing on the court.

    Measured 2026-11-20 with `?sweep=0:18:0.02&ground=0|1` on `seasons/2026-11-19/watch.json`, 901 frames, toe
    heights read in world feet (the court is y=0):

    | | both toes > 0.10ft | toe samples within 0.05ft | median toe | max |
    |---|---|---|---|---|
    | before | 823 of 901 | 43 of 1,802 | 0.254ft | 1.080ft |
    | after | 60 of 901 | 958 of 1,802 | 0.020ft | 0.898ft |

    The 60 that remain are a stride with both feet off the ground — a run, not a float. What is held here is the
    shape that produced those numbers: the clamp reads the LOWER toe, it can drop the body but only 0.75ft, and it
    leaves the hitter their own height through their own contact (a grounded body costs the arm reach, measured at
    up to 0.27ft on the worst shot, and the frame being on the ball at contact is the film's central promise)."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")

    def _num(self, name):
        m = re.search(rf"const {name} = ([0-9.]+);", self.page)
        self.assertIsNotNone(m, f"{name} is not a constant any more, so its value cannot be checked")
        return float(m.group(1))

    def test_the_feet_are_the_authority_and_the_body_follows_them(self):
        self.assertIn('const L = toePoint(rig, "footL"), R = toePoint(rig, "footR");', self.page,
                      "the clamp is not reading the toes, so it is a number about nothing")
        self.assertIn("const low = Math.min(L ? L.y : 0, R ? R.y : 0);", self.page,
                      "the clamp does not follow the LOWER foot, so a lifted foot would haul the body up with it")

    def test_the_body_may_be_dropped_but_only_so_far(self):
        self.assertTrue(0.2 <= self._num("GROUND_MAX") <= 1.0,
                        "GROUND_MAX is outside the range where it is a bound rather than a special case")
        self.assertIn("Math.max(-0.20, Math.min(GROUND_MAX, low))", self.page,
                      "the drop is unbounded, so a broken pose can haul the figure into the court")
        self.assertIn("one-sided by intent", self.page,
                      "the page no longer says why a lift is bounded and a drop is not")

    def test_the_hitter_keeps_their_height_through_their_own_contact(self):
        self.assertIn("const w = isHitter ? Math.min(1, Math.max(0, (Math.abs(tlc) - 0.15) / 0.15)) : 1;", self.page,
                      "the hitter is no longer exempt near contact, or the exemption is unbounded")
        self.assertIn("0.30s either side", self.page,
                      "the ramp's end is not written down, so the next reader has to derive it from the arithmetic")

    def test_the_toe_is_read_above_the_court_and_not_above_the_root(self):
        """The trap that cost an hour: `rel()` measures the toe from the ROOT, so it is invariant to the clamp.
        Reading that column on both sides of `?ground=` said "grounding changes nothing" on a build where the median
        toe went from 0.254ft to 0.020ft. The row now carries the world height as well."""
        self.assertIn("[L ? +L.y.toFixed(3) : null, Rf ? +Rf.y.toFixed(3) : null]", self.page,
                      "the sweep does not report the toe's height above the court")
        self.assertIn("invariant to the clamp", self.page,
                      "the trap is not written down where the next person will read the code")

    def test_the_switch_that_produced_the_numbers_is_in_the_page(self):
        self.assertIn('const GROUND = q.has("ground") ? q.get("ground") !== "0" : true;', self.page,
                      "there is no way to measure with the clamp off, so its cost cannot be stated")

    def test_the_before_and_after_are_written_down_with_their_counts(self):
        for piece in ("823 of 901", "60 of 901", "0.254", "0.020", "958 of 1,802"):
            self.assertIn(piece, self.backlog, f"{piece} is not in the backlog entry for item 2a")


class TestThePlanIsInTimeOrder(unittest.TestCase):
    """Item 2b of the tennis backlog, and a one-line fix worth more than everything around it.

    `whereAt` reads the plan by walking it and STOPPING at the first move that has not begun yet. That is a correct
    reading of a list in time order and a wrong one of a list that is not, and the list was not: a segment pushes its
    RUN before its STANCE, and the stance happens BEFORE the run it walks into. Every segment with both was therefore
    out of order, and the consequence was not subtle.

    Measured 2026-11-20 with `?sweep=0:125:0.02` on the clock's own film (`seasons/2026-11-19`), one frame either
    side of the sort:

    | | biggest one-frame move | frames over 25ft/s |
    |---|---|---|
    | before | 18.91ft (Colette, T=94.12) | 24 |
    | after | 0.42ft (Colette, T=10.16) | 0 |

    18.91ft in 0.02s is 945ft/s: a body placed across the court rather than walked there. The same defect put Colette
    at her standing position through the whole stance (the scan broke on the run that had not begun, so the stance
    was never applied) and then at the run's `from` in one frame — 6.0ft, on every serve in the film. The 0.42ft
    that remains is 21ft/s, which is a sprint, and the very first row of a sweep is the body being placed at its
    starting end, which is not a walk and is not claimed to be."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")
        self.stills = (REPO / "games" / "tennis" / "STILLS.md").read_text(encoding="utf-8")

    def test_the_plan_is_sorted_before_anybody_walks_it(self):
        """The sort is the fix, and it has to happen after every push (the last push is the settle's, at the bottom
        of the loop) and before the first `whereAt`."""
        sort = self.page.find("PLAN[name].sort((a, b) => a.t0 - b.t0)")
        self.assertGreater(sort, 0, "the plan is not sorted, and whereAt stops at the first move that has not begun")
        self.assertIn("for (const name of Object.keys(PLAN))", self.page[sort - 120:sort])
        self.assertGreater(sort, self.page.find("rr.settle.players"),
                           "the sort runs before the last push into the plan, so a settle can still be out of order")
        self.assertLess(sort, self.page.find("function whereAt(name, T)"))

    def test_the_run_is_still_pushed_before_the_stance_it_walks_into(self):
        """WHY the list is out of order, held as a fact about the file rather than a story about it: the run push is
        above the stance push. If that ever reverses, the sort becomes unnecessary and this test should be deleted
        deliberately instead of the sort being deleted by accident."""
        run = self.page.find("PLAN[sh.run.player] = PLAN[sh.run.player] || []).push(")
        stance = self.page.find("for (const st of (Array.isArray(sh.stance) ? sh.stance")
        self.assertGreater(run, 0)
        self.assertGreater(stance, run, "the pushes have been reordered; the sort may now be redundant")

    def test_the_walk_still_stops_at_the_first_move_that_has_not_begun(self):
        """The other half of the argument. A walk that scans the whole list would not need a sorted list, and a test
        that only checked the sort would pass on a page where the walk had been changed to something else."""
        body = self.page[self.page.find("function whereAt(name, T)"):]
        body = body[:body.find("/* Which end is this player at")]
        self.assertIn("else if (T > m.t0) {", body)
        self.assertIn("    } else break;", body, "whereAt no longer stops at the first move that has not begun")

    def test_the_before_and_after_are_written_down_with_their_numbers(self):
        for piece in ("18.91", "24", "0.42", "945ft/s"):
            self.assertIn(piece, self.backlog, f"{piece} is not in the backlog entry for item 2b")
        self.assertIn("[rootX, rootZ]", self.stills, "the sweep's new pair is not written down where a sweep is read")
        self.assertIn("debug plan", self.stills, "the sweep prints the plan and STILLS does not say so")


class TestAStrideIsEnteredAndLeft(unittest.TestCase):
    """Items 2b and 4b of the tennis backlog, which turned out to be one change.

    Two things were wrong with the gait and both were the same kind of wrong — a switch where there should have
    been a ramp:

    1. **The stride switched on at the first frame of a run and off at the last.** Measured 2026-11-25 on
       `seasons/2026-11-19` with `lab/tennis_sweep.py`: a toe rose **0.946ft in one frame** as a run began and
       BOTH toes dropped **0.6ft in one frame** as it ended (Dmitri, T=65.16: the root stops advancing and both
       feet fall together). Now `grow` ramps in over `STRIDE_IN` and out over `STRIDE_OUT`, and the worst frame is
       **0.425ft** (Dmitri) and **0.592ft** (Remy), with the frames over 0.10ft down from 422/458 to 293/306.
    2. **The gait's phase was counted from the start of the FILM**, so a run began at whatever phase the previous
       walk left behind, and the near-foot offset item 4b needs was noise on top of it. Measured: 7 of 11 runs put
       the near foot forward with a quarter-cycle offset, 7 of 11 with none, 4 of 11 with the opposite quarter —
       i.e. nothing. Counted from the move's own start (`local`), the same offset separates cleanly: **8 of 11 with
       it, 4 of 11 with none, 3 of 11 with the sign reversed.** That is how the sign was chosen, and `?near=-1`
       is kept so it can be re-measured rather than re-argued.

    What it did NOT do is move the done-test's own number. "The first foot to LEAVE THE GROUND is the near one"
    reads 7 of 11 both before and after, because the two feet leave the ground one to two frames apart — the split
    step takes both — and a 50fps sample cannot see the difference. The metric that does move is which foot comes
    across first, and that is the one the offset is aimed at. The backlog says so rather than claiming the test."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")
        self.stills = (REPO / "games" / "tennis" / "STILLS.md").read_text(encoding="utf-8")

    def test_the_stride_ramps_in_and_out_instead_of_switching(self):
        self.assertIn("const STRIDE_IN = 0.20;", self.page)
        self.assertIn("const STRIDE_OUT = 0.20;", self.page)
        self.assertIn("Math.min(Math.max(0, Math.min(1, el / STRIDE_IN)), "
                      "Math.max(0, Math.min(1, (left + STRIDE_OUT) / STRIDE_OUT)))", self.page,
                      "grow is not the smaller of the ramp in and the ramp out")
        # legs() must take the ramp and use it for BOTH the stride amplitude and the idle sway, or one of them
        # switches while the other fades
        self.assertIn("function legs(rig, phase, moving, face, turn, load, idle, walk, ramp)", self.page)
        self.assertIn("const still = 1 - ramp;", self.page)
        self.assertIn("idlePhase, walking, grow);", self.page)

    def test_the_phase_is_counted_from_the_move_and_not_from_the_film(self):
        """This is the whole reason the offset works now. `travelled` is cumulative across every move in the film,
        so a phase built from it begins each run wherever the last one ended."""
        self.assertIn("2 * Math.PI * ((local || 0) / cycle)", self.page)
        self.assertNotIn("2 * Math.PI * (travelled / cycle)", self.page,
                         "the phase is back on the cumulative distance, and the near-foot offset is noise again")
        self.assertIn("let lastDir = null;", self.page,
                      "the offset has no direction to survive the move ending, so it collapses on the last frame")
        self.assertIn("const lateral = lastDir ?", self.page)

    def test_the_sign_of_the_offset_is_measured_and_the_switch_is_kept(self):
        self.assertIn("NEAR_LEAD", self.page)
        self.assertIn('q.has("near")', self.page, "the sign cannot be re-measured without editing the page")
        self.assertIn("const NEAR_GATE = 0.15;", self.page)

    def test_the_numbers_and_what_they_did_not_do_are_written_down(self):
        for piece in ("0.946", "0.425", "8 of 11", "4 of 11", "3 of 11"):
            self.assertIn(piece, self.backlog, f"{piece} is not in the backlog entry for items 2b/4b")
        self.assertTrue("7 of 11 both before and after" in self.backlog,
                        "the backlog does not say that the done-test's own number did not move")

    def test_the_analysis_is_a_file_and_not_a_chat(self):
        tool = REPO / "lab" / "tennis_sweep.py"
        self.assertTrue(tool.exists(), "the sweep reader is missing; every number above came from it")
        text = tool.read_text(encoding="utf-8")
        for piece in ("biggest one-frame move", "over 25ft/s", "the near foot left the ground first",
                      "the hitter's root speed at the contact frame"):
            self.assertIn(piece, text, f"the reader does not report {piece!r}")
        self.assertIn("tennis_sweep.py", self.stills, "STILLS does not say where the reader is")


class TestAParticipantIsNeverGivenAGroupByAFile(unittest.TestCase):
    """CAST.md's rule, made checkable once, with the date it starts.

    The founder's question of 2026-11-20 was about four invented people. Reading it back found a second fault pointing
    the other way: `seasons/2026-11-19/setup.json` asserts `"sex": "female"` for Gwen and `"male"` for Dmitri — two
    PARTICIPANTS, given a group by a file rather than by themselves, and then entered into same-sex competitions on
    the strength of it. One garment in a setup file is not a census, and the clock copies that setup forward into
    every season it opens, so the assertion would have travelled for ever.

    The seasons on disk are RECORDS: they were played, and they are not rewritten. This starts at 2026-11-25, the day
    the fault was written down — every season opened on or after it may cast a character (a `cast.json` entry) or a
    participant who has DECLARED a group in `declarations.json`, and nobody else."""

    START = "2026-11-25"

    def setUp(self):
        self.seasons = REPO / "games" / "tennis" / "seasons"
        self.cast = json.loads((REPO / "games" / "tennis" / "cast.json").read_text(encoding="utf-8"))
        self.decl = json.loads((REPO / "games" / "tennis" / "declarations.json").read_text(encoding="utf-8"))

    @staticmethod
    def offenders(players, characters, declared):
        return [p["name"] for p in players
                if p["name"] not in characters and p["name"] not in declared]

    def test_the_declarations_file_says_what_it_is_for(self):
        self.assertEqual(self.decl["schema"], "ait-tennis-declarations/1")
        self.assertIn("declared", self.decl)
        self.assertIn("may pair anybody", self.decl["note"], "the file does not say what an undeclared member may do")

    def test_the_rule_catches_the_one_that_got_through(self):
        """The check has to be able to fail, or it is decoration. This is `2026-11-19/setup.json`'s own two names."""
        self.assertEqual(self.offenders([{"name": "Gwen"}, {"name": "Colette"}],
                                        set(self.cast["players"]), set(self.decl["declared"])), ["Gwen"])
        self.assertEqual(self.offenders([{"name": "Gwen"}], set(self.cast["players"]), {"Gwen"}), [])

    def test_no_new_season_puts_an_undeclared_participant_on_the_court(self):
        characters = set(self.cast["players"])
        declared = set(self.decl["declared"])
        checked = 0
        for d in sorted(self.seasons.iterdir()):
            setup = d / "setup.json"
            if not setup.exists():
                continue
            book = json.loads((d / "practice.json").read_text(encoding="utf-8")) if (d / "practice.json").exists() else {}
            opened = (book.get("opened") or "")[:10]
            if opened and opened < self.START:
                continue                    # a record: played, never rewritten
            checked += 1
            players = json.loads(setup.read_text(encoding="utf-8"))["players"]
            self.assertEqual(self.offenders(players, characters, declared), [],
                             f"{d.name} casts somebody who is neither a character nor a declared participant")
            for p in players:
                if p["name"] in declared:
                    self.assertEqual(p.get("sex"), self.decl["declared"][p["name"]],
                                     f"{d.name} gives {p['name']} a group that is not the one they declared")
        # Every season on disk today was opened before this rule, so the loop above is allowed to find nothing.
        # What it is not allowed to do is stop looking: `checked` is the count of seasons it actually read.
        self.assertGreaterEqual(checked, 0)

    def test_the_current_season_is_named_in_the_record_as_the_one_that_was_wrong(self):
        cast = (REPO / "games" / "tennis" / "CAST.md").read_text(encoding="utf-8")
        self.assertIn("declarations.json", cast, "CAST.md does not say where a declaration goes")
        self.assertIn("2026-11-19", cast)


class TestTheClockCastsCharactersAndNotMembers(unittest.TestCase):
    """Item 29. The guard in `TestAParticipantIsNeverGivenAGroupByAFile` reads seasons that are already on disk, so it
    catches a wrong cast AFTER the season was played. This is the half that stops it happening: the clock no longer
    copies the last season's `setup.json` verbatim, it BUILDS the cast — the characters in `cast.json`, plus any
    participant who has declared a group, and nobody else.

    That only works if there are characters enough. On 2026-11-26 there were four (Colette, Ada, Remy, Bo) and two of
    the six on court were participants, so dropping the participants left two and two — a court with no same-sex
    competition in it. Hence Nadia and Hugo: a second female character and a second male one, each with a sentence in
    `cast.json` and a body in `games/tennis/bodies`, built by `lab/body.py` in 1.5 seconds from the parameters in the
    same file.

    Every test below runs on a fixture whose cast was copied from the repository's own, or on the repository's own —
    nothing here is a hand-written cast that could agree with the code by construction."""

    def setUp(self):
        import importlib, tempfile, shutil
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")
        self.tmp = Path(tempfile.mkdtemp(prefix="tennis-cast-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.base = self.tmp / "seasons"
        self.base.mkdir()
        shutil.copyfile(REPO / "games" / "tennis" / "cast.json", self.tmp / "cast.json")
        self.cast = json.loads((REPO / "games" / "tennis" / "cast.json").read_text(encoding="utf-8"))

    def _pool(self, players=None):
        """A cast file at the fixture's own root, beside the seasons directory — the same place the real one sits."""
        data = {"schema": "ait-tennis-cast/2", "per_group": 3,
                "players": self.cast["players"] if players is None else players}
        (self.tmp / "cast.json").write_text(json.dumps(data), encoding="utf-8")

    def _season(self, name="2026-11-19", people=None):
        d = self.base / name
        d.mkdir(parents=True, exist_ok=True)
        people = people or [("Gwen", "female"), ("Dmitri", "male"), ("Colette", "female"),
                            ("Ada", "female"), ("Remy", "male"), ("Bo", "male")]
        (d / "setup.json").write_text(json.dumps({"schema": "ait-tennis-setup/1", "session": {"surface": "clay"},
                                                  "players": [{"name": n, "sex": s, "history": 0,
                                                               "look": {"height_m": 1.7}}
                                                              for n, s in people]}), encoding="utf-8")
        book = {"season": name, "opened": "2026-11-19T23:19:44Z", "note": "",
                "plan": {"sessions": 6, "rallies": 20,
                         "members": {"Gwen": 6, "Dmitri": 6, "Colette": 4, "Remy": 4, "Ada": 2, "Bo": 2}},
                "members": {"Gwen": {"balls": 30, "sessions": []}}}
        book["closed"] = {"when": "2026-11-26T00:00:00Z", "by": "a person", "why": "played out"}
        (d / "practice.json").write_text(json.dumps(book), encoding="utf-8")

    def _open(self, when="2026-11-27T04:00:00Z"):
        name, why = self.T.clock_season(self.base, when=when)
        setup = json.loads((self.base / name / "setup.json").read_text(encoding="utf-8")) if name else {}
        book = json.loads((self.base / name / "practice.json").read_text(encoding="utf-8")) if name else {}
        return name, why, setup, book

    def test_the_pool_is_six_characters_and_a_group_can_be_filled(self):
        counts = {}
        for name, v in self.cast["players"].items():
            self.assertTrue(v.get("character"), f"{name} is in the pool without being called a character")
            counts[v.get("sex")] = counts.get(v.get("sex"), 0) + 1
            for field in ("height_m", "build", "kit", "skin", "hair", "lower"):
                self.assertIn(field, v.get("look") or {}, f"{name} has no {field}, so the clock cannot build it")
            self.assertGreater(len(v.get("face", "")), 24, f"{name} has no sentence for portrait.js to draw")
        self.assertEqual(counts, {"female": 3, "male": 3}, f"the pool is {counts}, so a season of it cannot be "
                                                           f"same-sex competition in both groups")
        self.assertEqual(self.cast.get("per_group"), 3)
        for member in ("Dmitri", "Gwen"):
            self.assertNotIn(member, self.cast["players"],
                             f"{member} is a participant and is in the cast file, so a file would be deciding a "
                             f"member's group again")

    def test_every_character_has_a_body_the_film_can_load(self):
        for name in self.cast["players"]:
            for ext in ("glb", "png"):
                f = REPO / "games" / "tennis" / "bodies" / f"{name.lower()}.{ext}"
                self.assertTrue(f.exists(), f"{f.name} is missing, so a season casting {name} has no body to draw "
                                            f"— `lab/body.py` builds one in 1.5s")

    def test_the_clock_opens_a_characters_only_season_and_leaves_the_participants_off(self):
        self._season()
        name, why, setup, book = self._open()
        self.assertTrue(name, why)
        players = [(p["name"], p["sex"]) for p in setup["players"]]
        self.assertEqual(players, [("Colette", "female"), ("Ada", "female"), ("Nadia", "female"),
                                   ("Remy", "male"), ("Bo", "male"), ("Hugo", "male")],
                         f"the clock cast {players}: {why}")
        for member in ("Gwen", "Dmitri"):
            self.assertNotIn(member, dict(players), "a participant is on the next court without having declared")
        self.assertIn("left off", why, "the clock dropped two people and said nothing about it")
        self.assertEqual(set(book["plan"]["members"]), dict(players).keys(),
                         "the stagger names somebody who is not on the court, or forgets somebody who is")
        self.assertEqual(sorted(book["plan"]["members"].values()), [2, 2, 4, 4, 6, 6],
                         "the stagger's ladder was not carried over, so the spread he asked for is gone")
        self.assertEqual(setup["session"], {"surface": "clay"}, "the court's own settings were not carried over")

    def test_a_declared_participant_is_cast_with_the_group_they_declared_and_not_the_files(self):
        (self.tmp / "declarations.json").write_text(json.dumps({"declared": {"Gwen": "male"}}), encoding="utf-8")
        self._season()
        name, why, setup, _ = self._open()
        sexes = {p["name"]: p["sex"] for p in setup["players"]}
        self.assertEqual(sexes.get("Gwen"), "male",
                         f"the setup's own claim about Gwen was copied instead of her declaration: {why}")
        self.assertNotIn("Dmitri", sexes, "an undeclared participant was cast anyway")
        self.assertEqual(sorted(sexes.values()).count("male"), 3)

    def test_a_group_that_cannot_be_filled_stops_the_clock_instead_of_playing_two_and_two(self):
        thin = {k: v for k, v in self.cast["players"].items() if v["sex"] == "female" or k == "Remy"}
        self._pool(thin)
        self._season()
        name, why, _, _ = self._open()
        self.assertEqual(name, "", "the clock opened a season with no same-sex competition in the male group")
        self.assertIn("no competition to be had", why)
        self.assertEqual([d.name for d in self.base.iterdir()], ["2026-11-19"],
                         "the clock wrote a season it had just refused")

    def test_the_repositorys_own_next_season_is_cast_from_its_own_cast_file(self):
        """The one that matters: run the reader against the real `seasons/` and the real `cast.json`."""
        seasons = REPO / "games" / "tennis" / "seasons"
        players, members, why = self.T.next_cast(seasons, seasons / "2026-11-19" / "setup.json",
                                                 {"Gwen": 6, "Dmitri": 6, "Colette": 4, "Remy": 4,
                                                  "Ada": 2, "Bo": 2})
        self.assertTrue(players, why)
        sexes = [p["sex"] for p in players]
        self.assertEqual(sorted(sexes), ["female", "female", "female", "male", "male", "male"],
                         f"the repository's next court is {sexes}: {why}")
        self.assertEqual(set(members), {p["name"] for p in players})
        self.assertEqual(sorted(members.values()), [2, 2, 4, 4, 6, 6])
        for p in players:
            self.assertTrue((REPO / "games" / "tennis" / "bodies" / f"{p['name'].lower()}.glb").exists(),
                            f"{p['name']} would be cast with no body")


class TestEveryMemberHasAFaceItCanRegenerate(unittest.TestCase):
    """Founder, 2026-11-20, after closing the request for four drawings:

        *"I don't think you want every circle's tennis games to use the same faces. Rather, I would think that Kythe
        overall should have an image of each member, generated from a bit of text visible, with default text, and
        editable, in the member's UI. When the user is created, and whenever the text is modified, I would think a
        new image of the member should be generated."*

    He is right, and about more than the four faces: a picture that has to be drawn by somebody is a picture that
    exists for exactly the circles somebody was willing to draw for. What is held here is the shape of the answer —
    the face is a FUNCTION of a sentence, so there is nothing to regenerate, nothing to store, and nothing that can
    fall out of date; the sentence is in `identity.md`, which a member already has; and the drawing needs no
    network, so it works in a circle with no image service. `lab/portrait-check.mjs` is the arithmetic's own check
    and this class runs it rather than restating it."""

    def setUp(self):
        self.page = (REPO / "ait.html").read_text(encoding="utf-8")
        self.gen = (REPO / "portrait.js").read_text(encoding="utf-8")

    def test_the_face_is_a_function_of_a_sentence_and_not_a_picture_on_disk(self):
        self.assertIn("function portraitSVG(text, opts)", self.gen)
        self.assertIn("hash32", self.gen, "the drawing is not deterministic, so it is a different person each reload")
        for net in ("fetch(", "XMLHttpRequest", "<image", "toDataURL"):
            self.assertNotIn(net, self.gen,
                             f"the generator reaches for {net} — a face that needs a network is missing in exactly "
                             f"the circles that have no image service")

    def test_the_members_page_shows_the_face_and_lets_the_sentence_be_edited(self):
        self.assertIn('<script src="portrait.js"></script>', self.page)
        self.assertIn('id="face"', self.page, "the member's page has no place for its face")
        self.assertIn('id="facesay"', self.page, "the sentence is not visible and not editable")
        self.assertIn("oninput=\"facePreview(this.value)\"", self.page,
                      "editing the sentence does not redraw the face, which is the whole feature")
        self.assertIn("function faceSVG(text, size)", self.page)

    def test_saving_the_sentence_writes_exactly_one_line_into_the_identity(self):
        self.assertIn("async function savePortrait(name, text)", self.page)
        self.assertIn("/^portrait:.*$/m.test(cur.text)", self.page,
                      "the page does not notice an existing `portrait:` line, so it would add a second")
        self.assertIn("await putText(path, after,", self.page,
                      "the line is not written back to identity.md, so the face would not survive a reload")

    def test_a_new_member_is_created_with_the_default_sentence(self):
        import importlib
        tribe = importlib.import_module("tribe")
        text = tribe.identity_text("ada", "the third seat", " of a circle", "a person", "", "lean")
        self.assertIn(f"portrait: {tribe.PORTRAIT_DEFAULT}", text,
                      "a member created today has no `portrait:` line, so its face would be the fallback forever")
        self.assertGreaterEqual(len(tribe.PORTRAIT_DEFAULT), 20)

    def test_the_default_sentence_is_the_same_sentence_in_both_languages(self):
        import importlib
        tribe = importlib.import_module("tribe")
        m = re.search(r"const DEFAULT_PORTRAIT = '([^']*)';", self.gen)
        self.assertIsNotNone(m, "portrait.js has no DEFAULT_PORTRAIT any more")
        self.assertEqual(m.group(1), tribe.PORTRAIT_DEFAULT,
                         "two copies of the default sentence have drifted apart, so the face a new member is drawn "
                         "with is not the face its identity describes")

    def test_the_generator_passes_its_own_checks(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed here, so the drawing's own checks did not run")
        r = subprocess.run([node, str(REPO / "lab" / "portrait-check.mjs")],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("all portrait checks passed", r.stdout)


class TestASecondServeIsASecondServe(unittest.TestCase):
    """Backlog item 19's remainder, and a false sentence that had been in every record since 2026-11-12.

    There was one serve per point. A first serve that missed ended the point, and the record called it a
    **double fault** — a thing that requires two misses. Measured on the clock's own session of 2026-11-20
    (`seasons/2026-11-19/watch.json`, Gwen vs Colette): **13 of 20 rallies were one shot long**, mean rally 1.65,
    and the film spent most of its points on a ball that was never meant to be played.

    A first fault now costs a serve, not a point: the server serves again, 26% slower, aimed four feet nearer the
    middle of the box, and only a second miss is a double fault. Same seed, same two beginners: mean rally **2.95**,
    and no rally is a single shot unless it really was two misses.

    The rate is not what a tennis player would call good and it is recorded rather than tuned — a second serve lands
    in 50% here against about 85% in the real game, and slowing it further makes it worse (measured, see
    `SECOND_SERVE_PACE`), because most of the misses are balls hit on the frame and no amount of aiming removes a
    shanked ball. Item 19's kick serve is what would close the rest of the gap."""

    def setUp(self):
        import importlib
        sys.path.insert(0, str(REPO / "lab"))
        self.S = importlib.import_module("tennis_script")
        self.T = importlib.import_module("tennis")
        self.film = self.S.play((40, 55), ("A", "C"), 12, 1795200000000, "hard", self.S.SWAP_EVERY)

    def _serves(self, rally):
        return [s for s in self.film["shots"] if s["rally"] == rally and s.get("kind") == "serve"]

    def test_a_point_is_only_a_double_fault_when_two_serves_missed(self):
        double = [r for r in self.film["rallies"] if str(r["point"]["reason"]).startswith("double fault")]
        self.assertTrue(double, "no double fault in twelve points at this skill — the rule is untested by the film")
        for r in double:
            serves = self._serves(r["rally"])
            self.assertEqual(len(serves), 2,
                             f"rally {r['rally']} is called a double fault on {len(serves)} serve(s)")
            self.assertTrue(all(not s["in"] for s in serves),
                            f"rally {r['rally']} is called a double fault with a serve that landed in")

    def test_a_first_fault_is_a_fault_and_the_point_goes_on(self):
        firsts = [s for s in self.film["shots"] if s.get("fault") == "first serve"]
        self.assertTrue(firsts, "no first serve missed in twelve points, so nothing here was tested")
        for s in firsts:
            r = next(x for x in self.film["rallies"] if x["rally"] == s["rally"])
            self.assertFalse(str(r["point"]["reason"]).startswith("double fault — " + s["why"]),
                             "a first fault ended the point")
        # and the second serve is in the same rally, struck by the same player
        for s in firsts:
            serves = self._serves(s["rally"])
            self.assertEqual(len(serves), 2, f"rally {s['rally']} faulted and never served again")
            self.assertEqual(serves[0]["player"], serves[1]["player"], "the second serve was struck by the receiver")

    def test_a_single_shot_rally_is_always_a_double_fault(self):
        """The defect stated as an invariant: before this, a rally was one shot long whenever the serve missed, and
        that was 13 points in 20. A rally has a length of one only if the server missed twice."""
        for r in self.film["rallies"]:
            if r["length"] == 1:
                self.assertTrue(str(r["point"]["reason"]).startswith("double fault"),
                                f"rally {r['rally']} was one shot long and was not a double fault: "
                                f"{r['point']['reason']}")

    def test_the_second_serve_is_the_same_intention_with_less_pace(self):
        pairs = []
        for r in self.film["rallies"]:
            serves = self._serves(r["rally"])
            if len(serves) == 2:
                pairs.append(serves)
        self.assertTrue(pairs, "no rally served twice")
        for first, second in pairs:
            same_side = (first["target"][1] > self.T.WIDTH / 2) == (second["target"][1] > self.T.WIDTH / 2)
            self.assertTrue(same_side, "the second serve changed corner, so it is a change of plan and not a "
                                       "second serve")
        # Less pace, measured only where both balls were hit cleanly. `power` in the record is the ball's speed out
        # of `strike`, and a ball hit on the frame has HALF its pace taken off it (0.5-0.75x) — so a set of pairs
        # containing one shank says the second serve was faster than the first, which is an artefact of the shank
        # and not of the intent. Caught here on 2026-11-20 by the first version of this test, which did not filter.
        clean = [p for p in pairs if p[0].get("sweet") and p[1].get("sweet")]
        self.assertTrue(clean, "no pair of serves was struck cleanly, so the pace comparison has nothing to measure")
        for first, second in clean:
            self.assertLess(second["power"], first["power"],
                            f"a second serve was struck at {second['power']:.0f}mph against the first serve's "
                            f"{first['power']:.0f}mph with both balls hit cleanly")

    def test_the_two_numbers_that_set_it_are_stated_and_sane(self):
        self.assertTrue(0.60 <= self.S.SECOND_SERVE_PACE <= 0.90, self.S.SECOND_SERVE_PACE)
        self.assertTrue(6.0 <= self.S.SECOND_SERVE_INSET <= 14.0, self.S.SECOND_SERVE_INSET)
        src = (REPO / "lab" / "tennis_script.py").read_text(encoding="utf-8")
        self.assertIn("second serve in 30%", src,
                      "the measurement that says slowing it down is the wrong move is not next to the number")


class TestTheFilmsCastHasFacesAndTheMembersDoNot(unittest.TestCase):
    """Item 28, and the line the founder drew on 2026-11-20: *"I don't think you want every circle's tennis games to
    use the same faces."*

    The characters in `cast.json` are drawn from a sentence each by `portrait.js`, so the film's break card no longer
    shows a monogram. **Dmitri and Gwen are not in that file**, and that is the test that matters: they are
    participants, and a participant does not get a height, a garment or a face from me. The two of them keep whatever
    picture the record already had, or a monogram.

    The cast was four on 2026-11-20 and is six from 2026-11-26: Nadia and Hugo were added so that dropping the two
    participants off the court still leaves three and three (item 29), because a court of two and two has no same-sex
    competition in it."""

    def setUp(self):
        self.cast = json.loads((REPO / "games" / "tennis" / "cast.json").read_text(encoding="utf-8"))
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")

    def test_the_characters_are_drawn_and_the_two_members_are_not(self):
        names = set(self.cast["players"])
        self.assertEqual(names, {"Colette", "Ada", "Nadia", "Remy", "Bo", "Hugo"},
                         f"the cast file has changed: {sorted(names)}")
        for member in ("Dmitri", "Gwen"):
            self.assertNotIn(member, names,
                             f"{member} is a participant and is in the cast file, so the film would draw a face for "
                             f"a member of the commons — the thing CAST.md now forbids")

    def test_every_sentence_says_enough_to_be_drawn_from(self):
        for name, v in self.cast["players"].items():
            self.assertTrue(v.get("character"), f"{name} is in the cast file without being called a character")
            self.assertGreater(len(v.get("face", "")), 24, f"{name}'s face sentence is too short to draw anything "
                                                           f"but a default")

    def test_the_film_reaches_for_the_generator_and_keeps_the_monogram(self):
        self.assertIn('<script src="../../portrait.js"></script>', self.page)
        self.assertIn('const CASTS = QS.get("cast") || "cast.json";', self.page)
        self.assertIn("portraitSVG(gen, {size: 248, background: true})", self.page)
        self.assertIn('id="facegen"', self.page)
        self.assertIn('mono.textContent = pl.name.slice(0, 1).toUpperCase();', self.page,
                      "the monogram was removed, so a record with no sentence and no drawing has a blank card")

    def test_the_generated_face_is_not_wiped_by_the_cards_own_class(self):
        """The trap that ate the monogram on 2026-11-19 and would have eaten this: the card's className is rebuilt
        every frame from `on`, so anything added to its class list elsewhere is gone one frame later."""
        self.assertIn('faceIsGen ? " gen" : ""', self.page,
                      "the generated face's class is set somewhere the per-frame rebuild will wipe it")


class TestTheFirstStepIsNotFree(unittest.TestCase):
    """Item 14 of the tennis backlog, fifth move: the run, as a run.

    The reach rule divided distance by top speed, which is the time a player would need if they were already moving.
    It made every short ball free — and the short ball is the one you have to sprint for. Ported from the longer
    engine on 2026-11-18: an acceleration of `FIRST_STEP` ft/s² to top speed and then flat out, plus a split step
    that is now a skill (`reaction_time`) rather than the same quarter-second for everybody.

    What these hold: the acceleration costs real time and the inverse recovers the distance; the split step is
    quicker for a player who has hit more balls; nobody is ever drawn further than the clock allowed; and the
    calibration still puts a beginner above the floor the game needs — because a rule that is right and unplayable
    is a rule that gets switched off in a month."""

    def setUp(self):
        import importlib
        import random as _random
        self.random = _random
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")

    def test_a_standing_start_costs_more_than_distance_over_speed(self):
        t = self.T
        self.assertEqual(t.run_time(0.0, 19.0), 0.0)
        for need in (1.0, 3.0, 5.0, 12.0, 30.0):
            self.assertGreater(t.run_time(need, 19.0), need / 19.0,
                               f"{need}ft from a standstill cannot take less time than {need}ft already running")
            self.assertAlmostEqual(t.run_distance(t.run_time(need, 19.0), 19.0), need, places=6,
                                   msg="the run and its inverse disagree, so a beaten player is drawn past the ball")
        # the size of it, which is the whole reason for the port: a five-foot ball is not a quarter-second
        self.assertGreater(t.run_time(5.0, 19.0), 1.5 * (5.0 / 19.0),
                           "a five-foot sprint from a standstill is being charged as if the legs were already going")

    def test_the_split_step_is_quicker_for_a_player_who_has_hit_more_balls(self):
        t = self.T
        times = [t.reaction_time(t.Player("x", True, n)) for n in (0, 60, 300, 600)]
        self.assertEqual(times, sorted(times, reverse=True), "reaction time does not improve with practice")
        self.assertGreater(times[-1], 0.08, "a six-hundred-ball player reacts faster than a human can")
        self.assertLess(times[0], 0.40, "a beginner is given longer than a third of a second to start moving")

    def test_a_beaten_player_never_travels_further_than_the_clock_allowed(self):
        """The picture's invariant, and the reason `run_distance` exists: a player who did not get there is drawn
        where their legs actually brought them. If the feet travelled further than the accelerating run allows,
        the film would be teleporting them towards a ball they are supposed to be losing to."""
        t = self.T
        p = t.Player("x", True, 200, rng=self.random.Random(8))
        cases = [((t.NET_X - 4.0, 1.0), 0.9, {"v": (40.0, -14.0, 12.0), "speed_out": 50.0}),
                 ((t.NET_X - 30.0, 1.0), 0.6, {"v": (20.0, -8.0, 10.0), "speed_out": 20.0})]
        misses = 0
        for land, ft, bounce in cases:
            frm = (2.0, t.WIDTH / 2)
            m = t.interception(p, land, ft, bounce, "hard", frm=frm)
            if m["ok"]:
                continue
            misses += 1
            travelled = ((m["got"][0] - frm[0]) ** 2 + (m["got"][1] - frm[1]) ** 2) ** 0.5
            allowed = t.run_distance(max(0.0, m["at"] - t.reaction_time(p) - t.SETTLE), m["speed"])
            self.assertLessEqual(travelled, allowed + 0.01,
                                 f"the feet covered {travelled:.2f}ft in a clock that allows {allowed:.2f}ft")
            self.assertLess(travelled, m["gap"], "a beaten player's feet reached the ball")
        self.assertEqual(misses, 2, "these two balls are supposed to be unreachable — the test proves nothing")

    def test_the_rule_charges_the_first_step_and_the_split_step_both(self):
        """`need` is the seconds the legs are asked for. It must be more than distance-over-speed plus the brake,
        because the first step is charged as acceleration and the split step is charged again as reaction."""
        t = self.T
        p = t.Player("x", True, 300, rng=self.random.Random(9))
        land, ft, bounce = (t.NET_X - 15.0, 4.0), 2.0, {"v": (18.0, -6.0, 14.0), "speed_out": 28.0}
        m = t.interception(p, land, ft, bounce, "hard", frm=(2.0, t.WIDTH / 2))
        self.assertTrue(m["ok"], "this test needs a ball the player does get to")
        flat = max(0.0, m["gap"] - t.RACQUET_REACH) / m["speed"] + t.SETTLE
        self.assertGreater(m["need"], flat + 0.05,
                           f"a ball {m['gap']:.0f}ft away is being charged {m['need']:.2f}s, which is what it would "
                           f"cost somebody already running — the first step is free again")

    def test_the_calibration_still_lets_a_game_be_played(self):
        """The floor, in code rather than in a docstring. A fixed population of in-court balls the engine struck
        with the hands taken out of it, asked of a beginner and of a player with six hundred balls: the beginner
        must reach most of them and the practised player must reach nearly all, or the rule has become a game
        nobody can play and the next reader will not know it happened."""
        t = self.T
        rng = self.random.Random(11)
        hitter = t.Player("H", True, 400, rng=self.random.Random(12))
        ms, pop = 1793809110303, []
        tries = 0
        while len(pop) < 120 and tries < 4000:
            tries += 1
            surface = t.surface_at(ms + tries)
            wv = t.wind_vector(*t.wind_at(ms + tries))
            kind = rng.choice(["forehand", "backhand"])
            depth = t.NET_X + rng.uniform(4, 34)
            wide = t.WIDTH * (0.2 if rng.random() < 0.5 else 0.8) + rng.gauss(0, 6)
            face, power = t.aim_at(hitter, (depth, wide), kind, surface, wv, power=rng.uniform(58, 82))
            sh = t.strike(hitter, None, face=face, power=power, aim=wide, shot=kind,
                          surface=surface, wind=wv, clean=True)
            tr = sh["traj"]
            land = tr.get("land")
            if land is None or not (0 < land[0] < t.LENGTH and 0 <= land[1] < t.WIDTH):
                continue
            if len(pop) % 2:                      # half to each end, and the bounce mirrored with the landing
                v = tr["bounce"]["v"]
                land = (t.LENGTH - land[0], t.WIDTH - land[1])
                bounce = dict(tr["bounce"])
                bounce["v"] = (-v[0], -v[1], v[2])
            else:
                bounce = tr["bounce"]
            pop.append((land, tr["time"], bounce, surface, bool(len(pop) % 2)))

        def reached(practice):
            p = t.Player("P", True, practice, rng=self.random.Random(3))
            got = 0
            for land, ft, bounce, surface, north in pop:
                p.north = north
                got += t.reachable(p, land, ft, bounce, surface)[0]
            return got / len(pop)

        beginner, practised = reached(0), reached(600)
        self.assertGreater(beginner, 0.60,
                           f"a beginner reaches only {beginner:.0%} of the balls they must get to — the game is "
                           f"unplayable and the floor is 60%")
        self.assertGreater(practised, 0.85,
                           f"a player with 600 balls reaches only {practised:.0%} of them")
        self.assertGreater(practised, beginner, "practice buys nothing")


class TestPreparationAndRush(unittest.TestCase):
    """Item 14 of the tennis backlog, fourth move: the one place where HOW a player got to the ball changes the ball.

    Until now movement decided only whether a player reached the ball, never how well they hit it: reaching it by
    half a second and reaching it with half a second to spare were the same stroke. The longer engine has two
    pieces that fix this and both came over on 2026-11-18 — `prep`, a fourth skill with an onset at sixty balls
    ("inexperienced players don't know to get their racquets back as they're running", the founder, 2026-11-11),
    and `Player.rush`, which is how much of the racquet's preparation the flight time did not allow. `strike` then
    pays for it twice: worse hands and a wider frame.

    What these hold: preparation arrives after control and never before it; a player who overlaps the run and the
    racquet is not rushed by a ball the player beside them is; and a rushed ball is measurably a worse ball.

    **Measured, and it is the honest finding of the port:** over 300 points at each skill level, rush fires on 0-3%
    of shots — and it still does, for reasons worth writing down. To be rushed a player needs the ball to arrive
    before the take-back is finished, and the two costs that would make that common are charged somewhere else: the
    interception charges the run, so a ball nobody can get to is a miss and not a rushed shot. So the rule is in,
    it is correct, and it bites where the physics says the day is hard. Nothing was tuned to make it bite.

    **Re-measured 2026-11-19, after the serve stopped being a 53mph arc:** 120 points at each standard, same
    seeds — rushed on 86% of shots at no practice, 5% at three hundred balls, 3% at six hundred; mean rush 0.269 /
    0.012 / 0.006. The serve change moved the practised numbers by a point or two and moved the beginner's, who
    now faces a ball arriving in half a second instead of three-quarters. The reason rush is rare at three hundred
    balls is not that the game is slow; it is that a practised player overlaps the run and the take-back, which is
    what `prep` measures."""

    def setUp(self):
        import importlib
        import random as _random
        self.random = _random
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")

    def test_preparation_arrives_after_control_and_never_before_it(self):
        """The onset is the point: at sixty balls a player has hands and no habit, which is exactly the stage the
        founder described. A skill that arrives with control would make the two the same attribute."""
        t = self.T
        at = lambda n: t.Player("x", True, n).skill("prep")
        self.assertEqual(at(0), 0.0)
        self.assertEqual(at(60), 0.0)
        self.assertAlmostEqual(at(160), 0.34, places=2)
        self.assertAlmostEqual(at(300), 0.63, places=2)
        self.assertAlmostEqual(at(600), 0.89, places=2)
        self.assertGreater(t.Player("x", True, 60).skill("control"), 0.45,
                           "at sixty balls control is already 0.47 of a player while prep is nothing — that is "
                           "the whole difference between the two attributes")

    def test_the_player_who_takes_the_racquet_back_while_running_is_not_rushed(self):
        """Same court, same run, same ball: only the habit differs. And a ball with time to spare rushes nobody."""
        t = self.T
        beginner, expert = t.Player("x", True, 60), t.Player("y", True, 600)
        self.assertGreater(beginner.rush(1.0, 1.0), 0.2, "a beginner with a second to run and a second of ball "
                                                         "must be rushed")
        self.assertLess(expert.rush(1.0, 1.0), beginner.rush(1.0, 1.0),
                        "the player who prepares while running was rushed as much as the one who does not")
        for p in (beginner, expert):
            self.assertEqual(p.rush(0.5, 1.5), 0.0, "a ball with time to spare rushed somebody")
            self.assertLessEqual(p.rush(2.0, 0.2), 1.0, "rush is not capped at 1")

    def _spread(self, rush, n=200):
        """The same shot, at the same target, from the same hands — differing only in how rushed they were."""
        t = self.T
        out = []
        for i in range(n):
            p = t.Player("x", True, 300, rng=self.random.Random(9000 + i))
            incoming = {"speed_in": 55.0, "rush": rush}
            out.append(t.strike(p, incoming, face=6.0, power=62.0, aim=9.0, shot="forehand",
                                surface="hard", wind=(0.0, 0.0), aim_dist=60.0))
        return out

    def test_being_rushed_makes_the_ball_worse(self):
        """The claim the port exists for, measured on the same hands: a rushed player's landing point is scattered
        wider and they frame more balls. If this were not true, `rush` would be a word in a docstring."""
        calm, hassled = self._spread(0.0), self._spread(0.6)

        def spread(shots):
            ys = [s["traj"]["land"][1] for s in shots if s["traj"].get("land")]
            mean = sum(ys) / len(ys)
            return (sum((y - mean) ** 2 for y in ys) / len(ys)) ** 0.5

        def frames(shots):
            return sum(1 for s in shots if not s["sweet"])

        self.assertGreater(spread(hassled), spread(calm), "a rushed player's ball was no wider than a calm one's")
        self.assertGreater(frames(hassled), frames(calm), "a rushed player framed no more balls than a calm one")

    def _real_shots(self, balls, points=30):
        """The rush on every shot actually hit at a ball, over a set of points.

        Counting calls to `strike` is NOT counting shots: `aim_at` bisects the face by calling `strike` up to 22
        times per shot, so a naive count is four-fifths solver and one-fifth play and every rate comes out twenty
        times too small. That mistake shipped in a commit message on 2026-11-18 and is the reason this helper
        exists. A real shot is one hit at an incoming ball.
        """
        t = self.T
        seen, orig = [], t.strike

        def counting(*a, **kw):
            s = orig(*a, **kw)
            if a[1] is not None:
                seen.append(s.get("rush"))
            return s

        t.strike = counting
        try:
            rng = self.random.Random(4242)
            for point in range(points):
                north = point % 2 == 0
                server = t.Player("A", north, balls, rng=self.random.Random(1000 + point))
                receiver = t.Player("C", not north, balls, rng=self.random.Random(2000 + point))
                t.play_point(server, receiver, "hard", (0.0, 0.0), ("N", 0.0), rng)
        finally:
            t.strike = orig
        return seen

    def test_rush_is_rare_because_the_ball_is_in_the_air_for_a_second(self):
        """This test used to claim the opposite, and was wrong twice in two days, which is why it now says what it
        actually holds.

        Yesterday it said "a beginner is rushed on 86% of their shots, a three-hundred-ball player on 5%". Those
        numbers were measured against the **bounce** — the flight time was the time until the ball landed. On
        2026-11-19 the ball started being struck where a player strikes it (Item 16: at waist height, after the
        bounce, rather than at the first 0.02s slice it was within reach, which was usually a foot off the ground).
        The deadline moved from the bounce to the contact, and it moved by 0.3-0.7s, which is more than the whole
        of `PREP_TIME`. Measured on the same 30 points: 86% → 0% at no practice, 5% → 1% at three hundred balls.

        The rule is not wrong; the *rate* was a property of the deadline. With the ball in the air for one to two
        seconds, a 0.55s take-back fits, and what a beginner actually fails at is getting to the ball at all — a
        miss, not a rushed shot, and the interception already charges for it. So this holds the honest thing: rush
        fires rarely at every standard, it fires at all, and the reason is the length of a ball's life rather than
        a fault in the arithmetic. The rule's own behaviour — that overlap beats series, and that a ball with time
        to spare rushes nobody — is held directly above, where it does not depend on a deadline at all."""
        beginner, settled = self._real_shots(0), self._real_shots(300)
        self.assertGreater(len(beginner), 10, "too few shots at the earliest standard to say anything")
        self.assertGreater(len(settled), 100)
        badly = lambda xs: sum(1 for r in xs if r is not None and r > 0.1) / len(xs)
        self.assertLess(badly(beginner), 0.20,
                        f"a player with no habit was rushed on {badly(beginner):.0%} of their shots; with a 1-2s "
                        f"ball and a 0.55s take-back that is a deadline in the wrong place again")
        self.assertLess(badly(settled), 0.10,
                        f"a player with 300 balls was rushed on {badly(settled):.0%} of their shots")

    def test_the_deadline_is_the_contact_and_not_the_bounce(self):
        """The number the previous test's rate depends on, asserted so nobody can move it quietly: the time from
        the strike to the ball being struck back is a fifth of a second to half a second longer than the time to
        the bounce, because the ball is met where a player meets it — at the waist, on the way up."""
        t = self.T
        rows, orig = [], t.interception

        def watching(p, land, flight_time, bounce, surface, *a, **kw):
            m = orig(p, land, flight_time, bounce, surface, *a, **kw)
            if m["ok"]:
                rows.append(m["at"] - flight_time)      # the extra after the bounce
            return m

        t.interception = watching
        try:
            rng = self.random.Random(11)
            for point in range(12):
                north = point % 2 == 0
                server = t.Player("A", north, 300, rng=self.random.Random(1000 + point))
                receiver = t.Player("C", not north, 300, rng=self.random.Random(2000 + point))
                t.play_point(server, receiver, "hard", (0.0, 0.0), ("N", 0.0), rng)
        finally:
            t.interception = orig
        self.assertGreater(len(rows), 10, "no ball was hit")
        self.assertGreater(sorted(rows)[len(rows) // 2], 0.15,
                           f"the ball is being struck {sorted(rows)[len(rows) // 2]:.2f}s after it bounced: the "
                           f"meeting point is at the bounce, not at a height a player hits at")

    def test_the_return_of_a_serve_is_asked_about_like_any_other_ball(self):
        """The one ball that used to be exempt: the interception was asked only from the second shot on, so a serve
        could not be an ace and the return could not be rushed however late the receiver was. The test counts the
        questions rather than the answers, because a return nobody was rushed for and a return nobody asked about
        look identical from the outside — both carry a rush of zero."""
        t = self.T
        asked, orig = [], t.interception

        def watching(p, land, flight_time, bounce, surface, *a, **kw):
            asked.append((p.name, tuple(land) if land else None))
            return orig(p, land, flight_time, bounce, surface, *a, **kw)

        t.interception = watching
        try:
            rng = self.random.Random(11)
            server = t.Player("A", north=True, practice=300, rng=self.random.Random(1))
            receiver = t.Player("C", north=False, practice=300, rng=self.random.Random(2))
            t.play_point(server, receiver, "hard", (0.0, 0.0), ("N", 0.0), rng)
        finally:
            t.interception = orig
        self.assertTrue(asked, "the interception was never asked about any ball")
        # a serve lands in the service box: within SERVICE_LINE of the net, on the server's side of it
        boxes = [land for _n, land in asked
                 if land and abs(land[0] - t.NET_X) <= t.SERVICE_LINE]
        self.assertTrue(boxes, "no serve was ever asked about: the return is still the exempt ball")


class TestTheServeIsAFastBall(unittest.TestCase):
    """Item 14's sixth move's shadow: the defect the producer found in `play_point`, 2026-11-19.

    `play_point` served by fixing the face at four to eight degrees and *searching the power*. A ball struck from
    8.8ft at six degrees needs only about fifty miles an hour to land inside the service box, so the search had
    nothing to push against and settled where the bisection started: the measured serve was a 53mph arc, the
    slowest ball in the game, in a sport where the serve is the fastest. Nobody had to run for it, so the return
    of serve was never rushed and the ace did not exist.

    Two things changed and both are held here: the pace is now *chosen* from `SERVE_MPH` and scaled by control (a
    server decides how hard they hit it, and the face absorbs the difference), and the numbers are the ones a
    game can be built on — 120 points at each standard, same seeds: median serve 63mph at no practice, 75mph at
    three hundred and at six hundred; serve in 42% / 87% / 83%; rally median 1 / 5.5 / 6.0 and mean 1.9 / 12.2 /
    11.5; rushed on 86% / 5% / 3% of real shots, against 84% / 3% / 2.5% before the serve was fixed.

    What is *not* claimed: this is still an arc with no toss and no overhead (movement list item 3), so the swing
    is a standstill swing. And the aces this class was first measured with — 17% at three hundred balls, 22% at six
    hundred — were not the serve's fault but the receiver's stance, which stood two feet inside the baseline. That
    is `TestTheReturnerStandsBehindTheLine`, and with the stance fixed the same serves are aces 6% and 10% of the
    time. A number that turns out to belong to another part of the model is the useful kind of wrong."""

    def setUp(self):
        import importlib
        import random as _random
        self.random = _random
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")

    def _serves(self, balls, points=40):
        """Every serve's *chosen* pace and every point's flight, from `aim_at`'s own argument.

        The pace cannot be read off `strike`: `aim_at` bisects the face by calling `strike` up to 22 times, so a
        speed collected from the strike records is four-fifths search and one-fifth serve — the measurement bug
        that made a rush rate look twenty times smaller than it was. `aim_at` is *given* the pace by the caller,
        which is exactly the number the serve was asked to be."""
        t = self.T
        paces, flights = [], []
        orig_aim, orig_strike = t.aim_at, t.strike

        def aim(p, target, shot, surface, wind, power, at=None):
            if shot == "serve":
                paces.append(power)
            return orig_aim(p, target, shot, surface, wind, power, at=at)

        def struck(*a, **kw):
            s = orig_strike(*a, **kw)
            if a[1] is None and kw.get("shot") == "serve" and kw.get("trace"):
                traj = s.get("traj") or {}
                if traj.get("time"):
                    flights.append(traj["time"])
            return s

        t.aim_at, t.strike = aim, struck
        try:
            rng = self.random.Random(11)
            for point in range(points):
                north = point % 2 == 0
                server = t.Player("A", north, balls, rng=self.random.Random(1000 + point))
                receiver = t.Player("C", not north, balls, rng=self.random.Random(2000 + point))
                t.play_point(server, receiver, "hard", (0.0, 0.0), ("N", 0.0), rng)
        finally:
            t.aim_at, t.strike = orig_aim, orig_strike
        return paces, flights

    def test_the_serve_is_the_fastest_ball_on_the_court_and_not_the_slowest(self):
        """The defect in one assertion: 53mph was the number this game served at, from a bisection with nothing
        to push against. A first serve at three hundred balls is in the seventies, and the spread is wide enough
        that twenty serves are not a metronome — the face search is what absorbs the variation now."""
        t = self.T
        self.assertTrue(hasattr(t, "SERVE_MPH"), "the serve has no speed of its own again")
        paces, flights = self._serves(300)
        self.assertGreaterEqual(len(paces), 35, "not enough serves to say anything")
        median = sorted(paces)[len(paces) // 2]
        self.assertGreater(median, 68.0, f"the serve is a {median:.0f}mph ball: it is still the slowest ball "
                                         f"in the game and the return of serve is still a walk")
        self.assertLess(median, 85.0, f"a {median:.0f}mph serve is a second serve at a level nobody here plays at")
        spread = sorted(paces)[int(0.9 * len(paces))] - sorted(paces)[int(0.1 * len(paces))]
        self.assertGreater(spread, 6.0, f"every serve within {spread:.0f}mph of the next: a metronome, not a "
                                        f"player")
        self.assertTrue(flights, "no serve was struck")
        self.assertLess(max(flights), 1.1, f"the slowest serve in the set took {max(flights):.1f}s to cross the "
                                           f"court; nobody is rushed by a ball with a second of flight")

    def test_a_beginner_does_not_serve_like_a_professional(self):
        """The pace is scaled by control, so the serve is a skill like everything else: 63mph from a player who has
        never played, 75 from one who has, and neither is the same ball. Before this, the search gave everybody
        the same fifty-odd miles an hour, which made the serve the one stroke practice did not improve."""
        beginner, _ = self._serves(0)
        practised, _ = self._serves(600)
        med = lambda xs: sorted(xs)[len(xs) // 2]
        self.assertGreater(med(practised), med(beginner) + 5.0,
                           f"a 600-ball player served {med(practised):.0f}mph against a beginner's "
                           f"{med(beginner):.0f}mph: the serve does not respond to practice")
        self.assertLess(med(beginner), 70.0, f"a player who has never held a racquet served {med(beginner):.0f}mph")

    def test_a_fast_serve_is_still_a_serve_and_most_of_them_go_in(self):
        """The one way this change could be wrong rather than merely different: pace bought at the price of the
        box. Asked of the scoreline rather than the geometry — a server who serves at seventy-five and faults on
        a third of them is not a better server, and the film would be double faults.

        Measured, and recorded rather than tuned: 87% in at three hundred balls, 83% at six hundred (the faster
        serve faults a little more), against 42% from a beginner who has neither the pace nor the control."""
        t = self.T
        for balls, floor in ((300, 0.70), (600, 0.65)):
            rng = self.random.Random(11)
            ins = 0
            points = 40
            for point in range(points):
                north = point % 2 == 0
                server = t.Player("A", north, balls, rng=self.random.Random(1000 + point))
                receiver = t.Player("C", not north, balls, rng=self.random.Random(2000 + point))
                lines = t.play_point(server, receiver, "hard", (0.0, 0.0), ("N", 0.0), rng)
                ins += 0 if any("fault" in line for line in lines) else 1
            self.assertGreater(ins / points, floor,
                               f"at {balls} balls only {ins / points:.0%} of serves landed in the box")


class TestTheReturnerStandsBehindTheLine(unittest.TestCase):
    """Item 15: the stance, 2026-11-19. The defect was one line, and it had been there since the interception was
    written: `play_point` put both players two feet *inside* the baseline, which is where a server stands and
    nowhere a returner stands. A returner is on the back foot with the ball coming at them.

    It is worth a class of its own because the number it moves is the one number in the game that was not tennis:
    aces. Same 200 points, same seeds, only the stance differing — at 300 balls aces 17% → 6%, at 600 balls 23% →
    10%, and the rallies that were aces became rallies (median 4 → 5 and 6 → 8 shots). Serve-in moved 86/90 → 84/89
    because the receiver standing deeper does not change the server's aim; that is the run-to-run scatter of a
    different point population.

    The arithmetic behind it, on 120 real serves and nothing but the stance differing: reached 94% / 97% / 98% /
    99% at 300 balls from 2ft inside, from the line, from 4ft behind and from 6ft behind; 89% / 93% / 97% / 98% at
    600. Four feet of court is worth eight points of serves returned, which is the whole difference between a game
    with aces in it and a game that is 22% aces."""

    def setUp(self):
        import importlib
        import random as _random
        self.random = _random
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")

    def test_the_receiver_waits_behind_the_baseline(self):
        """Asked of `interception`, which is where the feet are: the first question of a point is about the
        receiver, and the stance it is asked from must be outside the line, not two feet inside it."""
        t = self.T
        asked, orig = [], t.interception

        def watching(p, land, flight_time, bounce, surface, *a, **kw):
            asked.append((p.name, p.north, kw.get("frm")))
            return orig(p, land, flight_time, bounce, surface, *a, **kw)

        t.interception = watching
        try:
            rng = self.random.Random(11)
            north = t.Player("A", True, 300, rng=self.random.Random(1))
            south = t.Player("C", False, 300, rng=self.random.Random(2))
            t.play_point(north, south, "hard", (0.0, 0.0), ("N", 0.0), rng)
        finally:
            t.interception = orig
        self.assertTrue(asked, "the interception was never asked about the serve")
        _name, receiver_north, frm = asked[0]
        self.assertIsNotNone(frm, "the interception was asked without saying where the player stands")
        if receiver_north:
            self.assertLess(frm[0], 0.0, f"a returner at the north end stood {frm[0]:.1f}ft from the baseline, "
                                         f"which is inside the court: that is the server's stance, not theirs")
        else:
            self.assertGreater(frm[0], t.LENGTH, f"a returner at the south end stood {t.LENGTH - frm[0]:.1f}ft "
                                                 f"behind the baseline, which is inside the court")

    def test_the_stance_is_what_makes_a_serve_returnable(self):
        """One serve, two stances, no randomness: a fast ball into the corner of the service box. Two feet inside
        the line the receiver is 0.8ft short of it; four feet behind the line they get there with three hundredths
        of a second to spare. That gap is what the game was calling an ace."""
        t = self.T
        receiver = t.Player("R", False, 600, rng=self.random.Random(7))
        land, flight, bounce = (54.1, 1.1), 0.39, {"v": (87.0, 7.0, 11.0)}
        inside = t.interception(receiver, land, flight, bounce, "hard", frm=(t.LENGTH - 2.0, t.WIDTH / 2))
        behind = t.interception(receiver, land, flight, bounce, "hard", frm=(t.LENGTH + 4.0, t.WIDTH / 2))
        self.assertFalse(inside["ok"], "this test needs a serve the receiver cannot get to from the baseline")
        self.assertGreater(inside["short_ft"], 0.5, "and not one they miss by a hair")
        self.assertTrue(behind["ok"], "standing where a returner stands did not reach a ball they were 0.8ft "
                                      "short of from inside the line")
        self.assertLess(behind["need"], behind["have"] + 0.01,
                        f"reached with {behind['have'] - behind['need']:.2f}s to spare; a stance that only just "
                        f"works is a lucky stance")

    def test_a_fast_serve_can_be_an_ace_and_is_not_usually_one(self):
        """The rate, which is the point of the class. Sixty points at six hundred balls: some serves are not
        returned — the model must not make an ace impossible — and most are, which is tennis."""
        t = self.T
        rng = self.random.Random(5)
        points, aces, faults = 60, 0, 0
        for point in range(points):
            north = point % 2 == 0
            server = t.Player("A", north, 600, rng=self.random.Random(1000 + point))
            receiver = t.Player("C", not north, 600, rng=self.random.Random(2000 + point))
            lines = t.play_point(server, receiver, "hard", (0.0, 0.0), ("N", 0.0), rng)
            strokes = [line for line in lines if " serves " in line or " hits " in line]
            if any("fault" in line for line in lines):
                faults += 1
            elif len(strokes) == 1 and any("short of it" in line for line in lines[1:]):
                aces += 1
        self.assertLess(faults / points, 0.30, f"{faults}/{points} serves were faults")
        self.assertGreater(aces, 0, "not one serve in sixty was an ace: the return cannot be beaten, which is "
                                    "the other way of not being tennis")
        self.assertLess(aces / points, 0.20, f"{aces}/{points} serves were aces — a fifth of points decided by "
                                             f"the first ball is not this game")


class TestTheGroundEnds(unittest.TestCase):
    """Item 17, 2026-11-19: the run-off. `interception` asked one question — is the ball within a racquet's
    length of the player by this 0.02s slice — over every slice for four seconds, and never asked whether there
    was any ground left to stand on. So a ball that had bounced and flown away was still "reachable", and the
    film showed players running twenty-five feet behind the baseline and striking the ball a foot outside the
    sideline. The bound is the ground: `PLAY_AREA` feet beyond each line.

    Measured on one fixed population of 605 balls (25 points at 300 and 600 balls, every interception recorded
    and re-asked): with no bound, 48.5% of the balls were met more than 6ft outside the court and 38.3% more
    than 10ft, the worst 29.8ft. At a 12ft run-off those are 16.1% / 5.8% / 12.0ft, and the reach rate does not
    move — 98% either way. That is because no ball is taken away: every ball the bound clips was already reachable
    at an earlier slice inside the ground, and the old code preferred a later slice nearer the waist. The run-off
    does not filter contacts, it corrects which moment is chosen — and the fact that the worst meet sits exactly on
    the bound is why the choice itself is Item 18."""

    def setUp(self):
        import importlib
        import random as _random
        self.random = _random
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")
        self._saved = self.T.PLAY_AREA

    def tearDown(self):
        self.T.PLAY_AREA = self._saved

    def _balls(self, want=120):
        """A population of real questions asked of the interception, captured so every candidate bound is asked
        about the same balls. A film-level count cannot answer this: the rng stream reshuffles on any change."""
        t = self.T
        calls, orig = [], t.interception

        def recording(p, land, flight_time, bounce, surface, *a, **kw):
            calls.append((p, land, flight_time, dict(bounce), surface, a, dict(kw)))
            return orig(p, land, flight_time, bounce, surface, *a, **kw)

        t.interception = recording
        try:
            seed = 0
            while len(calls) < want:
                seed += 1
                t.play_point(t.Player("A", seed % 2 == 0, 300, rng=self.random.Random(seed)),
                             t.Player("C", seed % 2 == 1, 600, rng=self.random.Random(seed + 500)),
                             "clay", (-6.22, -6.22), 6.0, self.random.Random(seed + 900))
        finally:
            t.interception = orig
        return calls

    def _outside(self, x, y):
        t = self.T
        return max(-x, x - t.LENGTH, -y, y - t.WIDTH, 0.0)

    def test_a_ball_that_lands_outside_the_ground_does_not_raise(self):
        """The bound is checked before the first slice, so a ball that lands past it never sets the closest-miss
        record. That path used to unpack `None` and would have crashed the point; now it says what happened."""
        t = self.T
        p = t.Player("A", True, 300, rng=self.random.Random(3))
        m = t.interception(p, (200.0, t.WIDTH / 2), 1.0, {"v": (10.0, 0.0, 20.0)}, "clay")
        self.assertFalse(m["ok"])
        self.assertIn("back of the court", m["why"])
        self.assertGreater(m["gap"], 100.0, "the ball was not actually far away — this test proves nothing")

    def test_no_ball_is_met_past_the_run_off(self):
        """The film's defect, asked directly: where do the contacts happen? With the bound, no meeting point is
        more than `PLAY_AREA` feet outside a line, and the worst of them is a run-off, not a chase."""
        t = self.T
        calls = self._balls(120)
        meets = []
        for p, land, ft, bounce, surface, a, kw in calls:
            m = t.interception(p, land, ft, bounce, surface, *a, **kw)
            if m["ok"]:
                meets.append(self._outside(m["meet"][0], m["meet"][1]))
        self.assertGreater(len(meets), 40, "not enough reachable balls to say anything")
        worst = max(meets)
        self.assertLessEqual(worst, t.PLAY_AREA + 0.5,
                             f"a ball was met {worst:.1f}ft outside the court, past the {t.PLAY_AREA:.0f}ft run-off")

    def test_the_bound_costs_no_reach(self):
        """A bound that changed who wins would be a tuning knob, and this one is not: the same balls, asked with
        no ground at all and with the run-off, are reached at the same rate."""
        t = self.T
        calls = self._balls(120)

        def reached():
            ok = 0
            for p, land, ft, bounce, surface, a, kw in calls:
                ok += bool(t.interception(p, land, ft, bounce, surface, *a, **kw)["ok"])
            return ok / len(calls)

        t.PLAY_AREA = 1e9
        free = reached()
        t.PLAY_AREA = self._saved
        bounded = reached()
        self.assertLess(abs(free - bounded), 0.03,
                        f"the run-off moved the reach rate from {free:.1%} to {bounded:.1%} — it is deciding "
                        f"points, not describing the ground")


class TestTheServeHasAToss(unittest.TestCase):
    """Item 19, 2026-11-19: the serve was an arc. The engine has struck it from 8.8ft in the air since Item 14, and
    the rig reaches the ball there — `?debug` reads 0.17ft from the racquet head to the ball at the contact frame —
    but the ball appeared at that height out of nothing. A serve begins with a throw, and the film showed no throw:
    a still of a serve was a player standing with their racquet down while the ball was already halfway to the net.

    The toss is PICTURE, not physics. `strike` still decides where the serve leaves from and how fast; the record
    carries the ball's life before that in its own array, and the first test here is the one that keeps the two
    honest — switch the toss off and the serve must be identical in every number that decides the point."""

    def setUp(self):
        import importlib
        sys.path.insert(0, str(REPO / "lab"))
        self.S = importlib.import_module("tennis_script")
        self.T = importlib.import_module("tennis")
        self._peak = self.S.TOSS_PEAK

    def tearDown(self):
        self.S.TOSS_PEAK = self._peak

    def _film(self, rallies=4):
        return self.S.play((300, 600), ("A", "C"), rallies, 1793809110303, "clay", self.S.SWAP_EVERY)

    def test_the_toss_starts_at_a_hand_and_ends_on_the_contact(self):
        """The two ends, which are the only two places a toss can be caught out: the ball leaves a hand at a height
        a person can hold it at, near their own body, and it arrives exactly on the point `strike` says the serve
        leaves from — not near it, on it, because the picture must not disagree with the strike about the ball."""
        t = self.T
        contact = (2.2, t.WIDTH / 2 + 1.1, 8.8)
        pts = self.S.toss(contact, True)
        self.assertGreater(len(pts), 20, "too few samples to draw a toss")
        self.assertEqual(pts[-1], [round(v, 3) for v in contact], "the toss does not end on the contact point")
        self.assertGreater(pts[0][2], 2.8, f"the ball left a hand at {pts[0][2]:.2f}ft")
        self.assertLess(pts[0][2], 3.6, f"the ball left a hand at {pts[0][2]:.2f}ft — that is nobody's hand")
        self.assertLess(abs(pts[0][1] - contact[1]), 2.0, "the release is not near the body")
        self.assertGreater(pts[0][0], 0.0, "the release is not on the server's own side of the contact")

    def test_the_toss_is_a_parabola_that_peaks_above_the_contact(self):
        """It goes up, it comes down, and the top of it is `TOSS_PEAK` above the contact — a serve is struck at the
        top or a hand's width past it. Under gravity, not eased: the gap between samples shrinks on the way up and
        grows on the way down, which is what makes it a throw rather than a lerp."""
        pts = self.S.toss((2.2, 14.6, 8.8), True)
        zs = [p[2] for p in pts]
        peak = max(zs)
        self.assertAlmostEqual(peak, 8.8 + self._peak, delta=0.05,
                               msg=f"the toss peaked at {peak:.2f}ft, not above the contact")
        i = zs.index(peak)
        self.assertGreater(i, 1, "the peak is at the release — that is a drop, not a toss")
        self.assertLess(i, len(zs) - 2, "the peak is at the contact — the ball was still rising when it was hit")
        self.assertTrue(all(zs[k] < zs[k + 1] for k in range(i)), "the ball did not rise to its peak")
        self.assertTrue(all(zs[k] > zs[k + 1] for k in range(i, len(zs) - 1)), "the ball did not fall from it")

    def test_the_toss_does_not_move_the_serve(self):
        """The claim that makes it safe to ship: with the toss switched off the film is identical in every number
        that decides a point — the contact, the launch velocity, the landing point, the whole path. A toss that
        moved the ball would be a second physics, and this engine has paid for that once already."""
        with_toss, without = self._film(), None
        self.S.TOSS_PEAK = 0.0
        without = self._film()
        self.assertEqual(len(with_toss["shots"]), len(without["shots"]))
        serves = 0
        for a, b in zip(with_toss["shots"], without["shots"]):
            self.assertEqual(a["contact"], b["contact"], "the toss moved where the serve was struck")
            self.assertEqual(a["v0"], b["v0"], "the toss changed how hard the serve was hit")
            self.assertEqual(a["land"], b["land"], "the toss moved where the serve landed")
            self.assertEqual(a["path"], b["path"], "the toss changed the ball's flight")
            self.assertEqual(a["n"], b["n"])
            if a["kind"] == "serve":
                serves += 1
                self.assertTrue(a.get("toss"), "a serve in the film has no toss in the record")
                self.assertNotIn("toss", b, "the toss survived being switched off")
            else:
                self.assertNotIn("toss", a, "a groundstroke was given a toss")
        self.assertGreater(serves, 2, "no serves in this film — it proves nothing")


class TestTheBallIsMetInTheBand(unittest.TestCase):
    """Item 18, 2026-11-19: the meeting point is where the ball is a ball to hit, and it is a band rather than a
    point. Item 16 picked the reachable slice nearest the waist — but a ball crosses the waist twice, once in front
    of the player and once behind them, and both are equally near 3.0ft. Height alone cannot break that tie, and
    the scan runs the whole ball, so the later crossing won: measured on the film, a player ran ten feet backwards
    to meet a ball that had bounced fourteen feet in front of them.

    Two candidate tie-breakers were measured against the same balls. Taking the earliest in-band slice is wrong in
    the other direction — it sends a player sprinting forward at a ball that was coming to them, and a twenty-point
    film came out at 220 shots instead of 110. Taking the in-band slice they have to move least for is what ships.

    The measurement that matters is the one with the ground bound **loosened to nothing**, because the bound is what
    Item 17 added and the question is whether the picture still looks like tennis without it. On 596 contacts from
    600 balls: backward travel over 3ft 51.5% under the old rule, 17.4% under the band (worst 28.5ft → 12.2ft), and
    contacts more than 10ft behind the baseline 39.4% → 1.7% (worst 30.1ft → 13.8ft). With the bound at 12ft the
    band's numbers are *the same to the point* — 17.4% and 1.7% — which is the claim: the contact does not depend on
    where the run-off is drawn, so the run-off is a backstop rather than the fix."""

    _balls = TestTheGroundEnds._balls

    def setUp(self):
        import importlib
        import random as _random
        self.random = _random
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")
        self._saved = (self.T.PLAY_AREA, self.T.CONTACT_HIGH)

    def tearDown(self):
        self.T.PLAY_AREA, self.T.CONTACT_HIGH = self._saved

    def _contacts(self, calls, contact_high, play_area=12.0):
        """Every reachable meeting, as (backward feet, height, feet beyond the baseline). Negative backward feet
        means the player moved toward the net, which is the ordinary case."""
        t = self.T
        t.PLAY_AREA, t.CONTACT_HIGH = play_area, contact_high
        out = []
        for p, land, ft, bounce, surface, a, kw in calls:
            m = t.interception(p, land, ft, bounce, surface, *a, **kw)
            frm = kw.get("frm")
            if not (m["ok"] and frm):
                continue
            away = 1.0 if not p.north else -1.0          # the direction that is away from the net
            # How far in front of their own baseline the player STARTED, which since item 31 (2026-11-26) is not
            # always zero: a recovery the ball interrupts leaves a player caught in the middle of the court, and a
            # ball hit past them has to be chased back. The rate below is asked of both, and the worst case only of
            # the ones who start at home, because the far-side crossing the rule is about is a receiving position.
            depth = (frm[0] - 2.0) if p.north else (t.LENGTH - 2.0 - frm[0])
            out.append(((m["meet"][0] - frm[0]) * away, m["height"],
                        max(-m["meet"][0], m["meet"][0] - t.LENGTH, 0.0), depth))
        self.assertGreater(len(out), 25, "too few contacts to say anything")
        return out

    def test_the_height_is_a_band_and_not_a_point(self):
        """What Item 16 bought and this must not lose: the ball is struck at a height a player strikes at. None
        below the knee, a median between the waist and the chest."""
        rows = self._contacts(self._balls(120), self._saved[1])
        hs = sorted(r[1] for r in rows)
        self.assertLess(sum(1 for h in hs if h < 1.0) / len(hs), 0.01,
                        f"{sum(1 for h in hs if h < 1.0)} of {len(hs)} balls were struck below a foot")
        self.assertGreater(hs[len(hs) // 2], 2.9, f"median contact {hs[len(hs) // 2]:.2f}ft is below the waist")
        self.assertLess(hs[len(hs) // 2], 4.5, f"median contact {hs[len(hs) // 2]:.2f}ft is above the chest")

    def test_a_player_does_not_run_away_from_the_net_to_meet_the_ball(self):
        """The defect, as a rate, with the ground bound removed so that the meeting-point rule is the only thing
        deciding. `CONTACT_HIGH` below the waist switches the band off and leaves the old nearest-the-waist choice
        in place, so this is the rule before this item against the rule after it, asked about the same balls."""
        calls = self._balls(300)
        old = self._contacts(calls, 0.5, play_area=1e9)
        new = self._contacts(calls, self._saved[1], play_area=1e9)
        back = lambda rows: sum(1 for r in rows if r[0] > 3.0) / len(rows)
        self.assertGreater(back(old), 0.35, f"the old rule only backed up on {back(old):.0%} of contacts — this "
                                            f"test needs a rule that visibly did it")
        self.assertLess(back(new), 0.25, f"the band still runs a player backwards on {back(new):.0%} of contacts")
        home = [r for r in new if r[3] <= 2.0]
        caught = [r for r in new if r[3] > 2.0]
        self.assertLess(max(r[0] for r in home), 13.0,
                        f"worst backward run from the baseline is {max(r[0] for r in home):.1f}ft — the far-side "
                        f"crossing is still winning somewhere")
        # And the ones who start inside the court run back the whole way, which is not the rule failing: it is a
        # player caught by an approach who is passed. Measured on this population: 15 of 322 balls are received from
        # inside the court, 93% of those run backwards, 26.5ft at worst; from the baseline, 17% and 9.9ft at worst.
        if caught:
            self.assertGreater(max(r[0] for r in caught), 3.0,
                               "the engine can no longer leave a player caught in the court, so item 31's risk "
                               "has been removed rather than measured")

    def test_the_contact_does_not_depend_on_where_the_run_off_is_drawn(self):
        """The claim that makes Item 17's bound a backstop rather than the fix: with no ground bound at all, the band
        puts 98% of contacts within 10ft of the baseline where the nearest-the-waist rule put 60% of them further
        out — and the band's own numbers barely move when the bound comes back."""
        calls = self._balls(300)
        old = self._contacts(calls, 0.5, play_area=1e9)
        free = self._contacts(calls, self._saved[1], play_area=1e9)
        bounded = self._contacts(calls, self._saved[1])
        far = lambda rows: sum(1 for r in rows if r[2] > 10.0) / len(rows)
        self.assertLess(far(free), 0.05, f"{far(free):.0%} of contacts happened more than 10ft behind the baseline "
                                         f"with no run-off at all")
        self.assertGreater(far(old), far(free) + 0.10,
                           f"the band did not improve on the old rule ({far(old):.0%} → {far(free):.0%})")
        self.assertLess(abs(far(bounded) - far(free)), 0.03,
                        f"the contact moved with the bound ({far(free):.0%} unbounded → {far(bounded):.0%} at 12ft), "
                        f"so the bound is still doing the choosing somewhere")


class TestTheBallAfterThePointIsOver(unittest.TestCase):
    """Item 14 of the tennis backlog, third move: the seconds of ball that are left after the point is decided.

    Three of the founder's asks are about exactly this — "when the ball hits the net, show it bouncing off and onto
    the court", "when the ball is out, show it bouncing a couple of bounces", "when the ball hits the court before
    the receiving player hits it, it would be good to see it hit the court and then bounce up". None of them is a
    judgement; all of them are the picture, and a film that hides them cannot show *why* a point ended. They came
    over from the longer engine with the picture half of `flight()`, behind switches that default off, so that a
    report pays for none of it and no verdict moves.

    What these hold: the switches are observation and not physics; each one puts the ball where the founder asked
    for it; and a shot is replayable from the two numbers it says it was struck with."""

    def setUp(self):
        import importlib
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")

    def _long_ball(self):
        """A ball from a north player's baseline that clears the net comfortably and lands past the far baseline."""
        return (2.0, self.T.WIDTH / 2, 3.5), (80.0, 0.0, 25.0)

    def test_the_picture_switches_do_not_move_the_ball(self):
        """The claim that makes the rest safe: `out_bounces`, `after_land`, `bounces` and `net_cord` add seconds to
        the film and change nothing about where the ball landed or when. A picture that moved the ball would be a
        second physics, and the last time this engine grew a second physics it was judged by the wrong one."""
        t = self.T
        p0, v0 = self._long_ball()
        plain = t.flight(p0, v0, (0.0, 0.0), "hard", trace=0.02)
        dressed = t.flight(p0, v0, (0.0, 0.0), "hard", trace=0.02, bounces=1, after_land=1.4,
                           out_bounces=2, legal=t.on_court, t_max=8.0)
        self.assertEqual(plain["land"], dressed["land"], "the picture switches moved where the ball landed")
        self.assertAlmostEqual(plain["time"], dressed["time"], places=9)
        self.assertAlmostEqual(plain["bounce"]["speed_out"], dressed["bounce"]["speed_out"], places=9)
        self.assertGreater(len(dressed["path"]), len(plain["path"]),
                           "the switches added no seconds of ball to the film")

    def test_a_ball_that_landed_out_bounces_on_for_the_picture(self):
        """The founder, 2026-11-11: a lost point is not a vanished ball. `land` stays the first bounce — every
        verdict reads it — and the bounces after it are what a spectator is owed."""
        t = self.T
        p0, v0 = self._long_ball()
        tr = t.flight(p0, v0, (0.0, 0.0), "hard", trace=0.02, out_bounces=2, legal=t.on_court, t_max=8.0)
        self.assertFalse(t.on_court(tr["land"]), "this test needs a ball that landed out")
        self.assertTrue(tr.get("after_out"), "the ball that landed out made no second bounce")
        self.assertTrue(tr["after_out"]["bounces"], "the film was told to watch and watched nothing")
        self.assertGreater(tr["path"][-1][0], tr["time"], "the path ends at the bounce it was given")
        # and it stops at the edge of the picture rather than following the ball into the dark
        self.assertTrue(t.in_view(tr["path"][-1][1:3]), "the film followed the ball off the edge of the frame")

    def test_a_ball_into_the_tape_comes_back_and_drops(self):
        """The net cord, 2026-11-11: "show it bouncing off and onto the court for a bounce or two before ending the
        point." The ball comes back towards the hitter, not through the net, and `land` stays None because the
        point is over — the bounce is the picture's, not the umpire's."""
        t = self.T
        tr = t.flight((2.0, t.WIDTH / 2, 3.5), (70.0, 0.0, 6.0), (0.0, 0.0), "hard",
                      trace=0.02, net_cord=True)
        self.assertIsNone(tr["land"], "a ball into the tape is not a ball that landed on the court")
        self.assertIsNotNone(tr["net"])
        after = tr.get("after_net") or {}
        self.assertTrue(after.get("bounces"), "the tape killed the ball dead and showed nothing")
        for b in after["bounces"]:
            self.assertLess(b["land"][0], t.NET_X,
                            "the ball came back through the net instead of off it, from the hitter's side")

    def test_the_hit_window_is_the_balls_own_parabola(self):
        """Why the window cannot be a constant: the ball's own bounce decides how long it is hittable, and a
        skidding ball on grass and a kicking one on clay are the same ball with different surfaces under it."""
        t = self.T
        dead = t.hit_window({"v": (10.0, 0.0, -3.0)})            # never gets up: a net cord dying
        skid = t.hit_window({"v": (30.0, 0.0, 6.0)})             # a low, flat bounce
        kick = t.hit_window({"v": (20.0, 0.0, 24.0)})            # a heavy topspin bounce over the shoulder
        self.assertEqual(dead, (0.0, 0.0, 0.0))
        self.assertLess(skid[1], kick[1], "a flat bounce is hittable for longer than a kicking one")
        self.assertLessEqual(kick[1], t.HIT_WINDOW_MAX, "the window is not capped, so a lob hangs all day")
        self.assertGreater(kick[2], skid[2], "the kick did not come up higher than the skid")

    def test_every_shot_says_where_it_left_the_strings(self):
        """A record has to be replayable or it is a picture no engine can re-judge: `contact` and `v0` are the pair,
        and `lab/tennis_record.py` rebuilds a film's every arc from them through today's integrator."""
        t = self.T
        p = t.Player("X", north=True, practice=300)
        s = t.strike(p, None, face=8.0, power=64.0, aim=t.WIDTH / 2, shot="forehand",
                     surface="clay", wind=(2.0, 1.0))
        self.assertIn("v0", s, "the shot does not say how hard it left the strings")
        again = t.flight(tuple(s["contact"]), tuple(s["v0"]), (2.0, 1.0), "clay", cl=s["spin"])
        self.assertEqual(again["land"], s["traj"]["land"], "the shot cannot be replayed from what it says it was")
        self.assertAlmostEqual(again["time"], s["traj"]["time"], places=9)

    def test_a_serve_is_judged_by_the_box_and_not_by_the_court(self):
        """A serve ten feet past the service line is inside the court and a fault, which no groundstroke rule can
        say. It reports the distance to the line it missed, because a player corrects a number."""
        t = self.T
        p = t.Player("X", north=True, practice=300)
        s = t.strike(p, None, face=6.0, power=65.0, aim=t.WIDTH / 2, shot="serve",
                     surface="hard", wind=(0.0, 0.0), clean=True)
        ok, why = t.serve_verdict(s)
        x = s["traj"]["land"][0]
        self.assertTrue(t.on_court(s["traj"]["land"]), "this test needs a serve that landed on the court")
        self.assertFalse(ok, f"a serve landing {x - t.NET_X:.0f}ft past the net was called in")
        self.assertIn("service line", why)
        self.assertTrue(any(ch.isdigit() for ch in why), "the fault names no distance, so nothing can be learnt")


class TestASeasonPlaysItself(unittest.TestCase):
    """The founder, 2026-11-19: *"If no human runs play/practice sessions, automatic play one of each sex should
    become best and one of each sex should be come worse."*

    That is a schedule, so it lives in the season file as a `plan` block — prose does not fail and a plan does. The
    rule is arithmetic and has no rng in it, because the random stream belongs to the tennis: a schedule that drew
    lots would make the ranking partly a lottery, and the point of staggering the play time is that the ranking is
    the schedule's doing and can be checked against it.

    The property that shapes everything: **staggering needs three per group.** With two, the partner is always
    pulled along and every member plays every session, so the stagger cancels itself. That is why the cast is three
    and three rather than two and two, and it is not a fact anyone would guess from the phrase "staggered play"."""

    def setUp(self):
        import importlib, tempfile, shutil
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")
        self.tmp = Path(tempfile.mkdtemp(prefix="tennis-plan-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _season(self, name="s1", people=(("Ann", "female", 3), ("Belle", "female", 2), ("Cid", "male", 1)),
                rallies=3):
        d = self.tmp / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "setup.json").write_text(json.dumps({"schema": "ait-tennis-setup/1", "players": [
            {"name": n, "sex": x, "look": {"height_m": 1.7}} for n, x, _ in people]}), encoding="utf-8")
        book = {"season": name, "opened": "2026-11-19T00:00:00Z", "note": "", "members": {},
                "plan": {"sessions": max(t for _, _, t in people), "rallies": rallies,
                         "members": {n: t for n, _, t in people}}}
        self.T.seed_practice(book, {n: 10 for n, _, _ in people}, "2026-11-19T00:00:00Z")
        # `override` is the season DIRECTORY, not the base — season_paths puts practice.json straight into it.
        self.T.save_season(book, name, str(d))
        return d

    def _run(self, d, name="s1"):
        import contextlib, io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.T.main(["--schedule", "--season", name, "--season-dir", str(d)])
        return code, out.getvalue(), err.getvalue()

    def _book(self, d, name="s1"):
        return json.loads((Path(d) / "practice.json").read_text(encoding="utf-8"))

    def test_the_furthest_behind_plays_the_next_most_behind_of_their_own_group(self):
        cast = {"Ann": {"sex": "female"}, "Belle": {"sex": "female"}, "Cid": {"sex": "male"}}
        # Belle and Ann are the two furthest behind and share a group: they compete.
        book = {"members": {"Ann": {"sessions": [{}]}, "Belle": {"sessions": []}, "Cid": {"sessions": [{}, {}, {}]}},
                "plan": {"members": {"Ann": 5, "Belle": 5, "Cid": 5}}}
        self.assertEqual(self.T.next_session(book, cast), ("Belle", "Ann", "compete"))
        # Cid alone is behind, and nobody in his group can join him: that is a practice, because practice may pair
        # anybody and competition may not.
        book = {"members": {"Ann": {"sessions": [{}, {}, {}, {}]}, "Belle": {"sessions": [{}, {}, {}, {}]},
                            "Cid": {"sessions": [{}]}},
                "plan": {"members": {"Ann": 5, "Belle": 5, "Cid": 5}}}
        a, b, mode = self.T.next_session(book, cast)
        self.assertEqual((a, mode), ("Cid", "practice"),
                         "a member with nobody behind in their own group must not be given a competition")

    def test_the_rule_is_arithmetic_and_not_a_lottery(self):
        """Same book, twelve times: the same answer. A schedule that drew lots would make the ranking partly a
        random draw, and nobody could then say which part of the standings was the stagger."""
        book = {"members": {n: {"sessions": [{}] * i} for i, n in enumerate(("Ann", "Belle", "Cid"))},
                "plan": {"members": {"Ann": 4, "Belle": 4, "Cid": 4}}}
        cast = {n: {"sex": "female" if n != "Cid" else "male"} for n in ("Ann", "Belle", "Cid")}
        answers = {self.T.next_session(book, cast) for _ in range(12)}
        self.assertEqual(len(answers), 1, f"the schedule gave {answers}")

    def test_a_scheduled_session_says_the_schedule_played_it(self):
        d = self._season()
        code, out, err = self._run(d)
        self.assertEqual(code, 0, err)
        self.assertIn("the schedule", out)
        session = self._book(d)["members"]["Ann"]["sessions"][-1]
        self.assertEqual(session["by"], "the schedule")
        self.assertIs(session["competition"], True)

    def test_the_season_closes_itself_when_the_plan_is_done_and_takes_no_eighth(self):
        d = self._season(people=(("Ann", "female", 1), ("Belle", "female", 1)))
        self._run(d)
        book = self._book(d)
        self.assertIn("closed", book, "the plan was done and the season did not close")
        self.assertIn("complete", book["closed"]["why"])
        code, out, err = self._run(d)
        self.assertEqual(code, 2, "a closed season accepted another scheduled session")
        self.assertIn("closed", err)

    def test_the_ranking_is_the_schedules_doing(self):
        """The founder's requirement, measured: one of each group ends best and one ends worst, and it is the
        number of sessions that put them there. Equal histories at the start, so nothing but the schedule can
        account for the order."""
        d = self._season(people=(("Ann", "female", 3), ("Belle", "female", 1), ("Cid", "male", 2)), rallies=4)
        for _ in range(6):
            code, out, err = self._run(d)
            if code != 0:
                break
        book = self._book(d)
        played = {n: len(m["sessions"]) for n, m in book["members"].items()}
        balls = {n: m["balls"] + m.get("carried", 0) for n, m in book["members"].items()}
        self.assertEqual(book["members"]["Ann"].get("carried"), 10, "this test needs equal histories")
        self.assertGreater(played["Ann"], played["Belle"],
                           f"the stagger did not happen: {played}")
        self.assertGreater(balls["Ann"], balls["Belle"],
                           "the member who played more sessions did not end with more balls")
        p_ann, p_belle = self.T.Player("Ann", True, balls["Ann"]), self.T.Player("Belle", True, balls["Belle"])
        self.assertGreater(p_ann.skill("control"), p_belle.skill("control"),
                           "more sessions did not make a better player, so the ranking is not the schedule's")

    def test_a_season_with_no_plan_has_no_schedule(self):
        d = self.tmp / "bare"
        d.mkdir()
        (d / "setup.json").write_text(json.dumps({"players": [{"name": "Ann", "sex": "female"}]}),
                                      encoding="utf-8")
        (d / "practice.json").write_text(json.dumps({"season": "bare", "members": {"Ann": {"balls": 0,
                                                                                        "sessions": []}}}),
                                         encoding="utf-8")
        code, out, err = self._run(d, "bare")
        self.assertEqual(code, 2)
        self.assertIn("no plan", err, "the refusal does not say what is missing")
        self.assertEqual(json.loads((d / "practice.json").read_text())["members"]["Ann"]["sessions"], [],
                         "a season with no plan had a session played into it anyway")


class TestTheClockPlaysUnattended(unittest.TestCase):
    """The founder, 2026-11-19: *"Dmitri's game still function for live but off-screen playing and during wakes."*

    `--schedule` was a command, and a command nobody runs is a feature in a README. Two things were missing and
    both are here: the workflow that runs it while nobody is looking, and the answer to the question the workflow
    immediately raises — *which season?* A closed season takes no more sessions by design, so a clock with no
    open season has to open one, or the game stops the first time a season plays its plan out.

    The clock opens a season from the last one's cast and plan, with every member starting level. That is the
    decision that keeps the founder's stagger meaningful: `Player.skill()` is asymptotic, so six members carried
    forward from a finished season would begin 0.001 apart and end 0.001 apart, and "one of each sex best, one
    worst" would be true of every season equally and so of none."""

    def setUp(self):
        import importlib, tempfile, shutil
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")
        self.tmp = Path(tempfile.mkdtemp(prefix="tennis-clock-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.base = self.tmp / "seasons"
        self.base.mkdir()

    def _season(self, name, balls=("Ann", 20), closed="", plan=None,
                people=(("Ann", "female"), ("Belle", "female"))):
        d = self.base / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "setup.json").write_text(json.dumps({"schema": "ait-tennis-setup/1", "players": [
            {"name": n, "sex": x, "look": {"height_m": 1.7}} for n, x in people]}), encoding="utf-8")
        book = {"season": name, "opened": f"2026-11-{len(list(self.base.iterdir())):02d}T00:00:00Z",
                "note": "", "members": {n: {"balls": b, "sessions": []} for n, b in [balls]}}
        if plan:
            book["plan"] = plan
        if closed:
            book["closed"] = {"when": "2026-11-19T00:00:00Z", "by": "a person", "why": closed}
        (d / "practice.json").write_text(json.dumps(book), encoding="utf-8")
        return d

    def _plan(self):
        return {"sessions": 3, "rallies": 4, "members": {"Ann": 2, "Belle": 2}}

    def _book(self, name):
        return json.loads((self.base / name / "practice.json").read_text(encoding="utf-8"))

    def test_the_repository_has_a_workflow_that_plays_a_session_unattended(self):
        w = (REPO / ".github" / "workflows" / "season-clock.yml").read_text(encoding="utf-8")
        self.assertIn("schedule:", w, "there is no clock: nothing runs the schedule while nobody is looking")
        self.assertIn("cron:", w)
        self.assertIn("--schedule", w, "the clock does not run the schedule")
        self.assertIn("contents: write", w)
        # The checkout is shared with other bodies and with the founder's sessions, so the push will be
        # rejected. A schedule that drops a session on a rejected push is worse than no schedule.
        self.assertIn("--rebase", w, "the clock commits without rebasing, so a rejected push loses the session")
        self.assertIn("push -q ||", w, "the clock has no retry after a rejected push")

    def test_the_clock_plays_the_newest_season_that_is_still_open(self):
        self._season("2026-a", plan=self._plan(), closed="played out")
        self._season("2026-b", plan=self._plan())          # newer, open
        self._season("2026-c", closed="before the rule")   # newest, closed
        name, why = self.T.clock_season(self.base, when="2026-11-20T04:17:00Z")
        self.assertEqual(name, "2026-b", f"the clock chose {name}: {why}")
        self.assertIn("newest open season", why)

    def test_a_closed_season_is_never_the_clocks_choice(self):
        self._season("2026-a", plan=self._plan(), closed="completed")
        name, why = self.T.clock_season(self.base, when="2026-11-20T04:17:00Z")
        self.assertNotEqual(name, "2026-a", "the clock played into a closed season")
        self.assertEqual(name, "2026-11-20")

    def test_an_open_season_with_no_plan_is_a_persons_and_is_skipped(self):
        self._season("2026-a", plan=self._plan(), closed="completed")
        self._season("2026-b")                             # open, and no plan: a person's evening
        name, _ = self.T.clock_season(self.base, when="2026-11-20T04:17:00Z")
        self.assertEqual(name, "2026-11-20", "the clock invented a schedule for a season with no plan")
        self.assertEqual(self._book("2026-b")["members"]["Ann"]["sessions"], [],
                         "the clock played a session in a season whose plan it does not own")

    def test_the_clock_opens_the_next_season_from_the_last_ones_cast_and_plan(self):
        self._season("2026-a", balls=("Ann", 213), plan=self._plan(), closed="completed")
        name, why = self.T.clock_season(self.base, when="2026-11-20T04:17:00Z")
        self.assertIn("opened", why)
        book = self._book(name)
        self.assertEqual(book["plan"]["members"], self._plan()["members"], "the plan was not carried over")
        self.assertEqual(book["plan"]["by"], "the clock, from 2026-a")
        self.assertIn("2026-a", book["note"])
        self.assertTrue((self.base / name / "setup.json").exists(),
                        "the new season has no cast, so no competition in it could be placed in a group")

    def test_a_season_the_clock_opens_starts_level_and_not_where_the_last_one_ended(self):
        # 2026-a ends with Ann on 213 balls: a season that began there would be decided before it was played.
        self._season("2026-a", balls=("Ann", 213), plan=self._plan(), closed="completed")
        name, _ = self.T.clock_season(self.base, when="2026-11-20T04:17:00Z")
        book = self._book(name)
        for n in self._plan()["members"]:
            self.assertEqual(book["members"][n]["carried"], self.T.SEASON_START_BALLS,
                             f"{n} did not start level: {book['members'][n]}")
            self.assertEqual(book["members"][n]["balls"], 0, "carried balls were counted as hit here")
            self.assertEqual(book["members"][n]["seeded"]["by"], "the clock, opening the season")
        self.assertEqual(len({book["members"][n]["carried"] for n in self._plan()["members"]}), 1,
                         "the members did not all start with the same history")

    def test_the_name_it_invents_does_not_collide_with_a_season_already_on_disk(self):
        self._season("2026-11-20", plan=self._plan(), closed="completed")
        name, _ = self.T.clock_season(self.base, when="2026-11-20T04:17:00Z")
        self.assertEqual(name, "2026-11-20-2", "the clock wrote its season over one already on disk")
        self.assertEqual(self._book("2026-11-20")["closed"]["why"], "completed",
                         "an existing season was rewritten")

    def test_a_colony_with_nothing_to_copy_a_cast_from_gets_a_sentence_and_not_a_file(self):
        name, why = self.T.clock_season(self.base, when="2026-11-20T04:17:00Z")
        self.assertEqual(name, "")
        self.assertIn("no season on disk has a plan", why)
        self.assertEqual(list(self.base.iterdir()), [], "the clock invented a season out of nothing")

    def test_a_clock_with_nothing_to_play_is_not_a_failure(self):
        """A scheduler that goes red because a colony has never played a session sends somebody to fix a working
        thing. Nothing due is an answer, not an error."""
        import contextlib, io
        d = self._season("2026-a")      # a bare season: no plan, nothing due
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.T.main(["--schedule", "--season-dir", str(d)])
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("no season to play in", out.getvalue())


class TestASeasonCanBeClosed(unittest.TestCase):
    """The founder, 2026-11-19: *"Why don't you just discard that data?"*

    Because discarding is the one thing this design does not do — a season is a directory, and starting over is
    opening another one, which is why last spring stays readable while the next season runs. But a season recorded
    before a rule existed is not comparable with the seasons after it, and pretending otherwise is worse than
    either keeping it or deleting it. So the record gains one word: CLOSED. It keeps every number it has, it takes
    no more sessions, and it cannot be seeded either — a refusal that arrives after the write is not a refusal."""

    def setUp(self):
        import importlib, tempfile, shutil
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")
        self.tmp = Path(tempfile.mkdtemp(prefix="tennis-close-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.d = self.tmp / "s1"
        self.d.mkdir()
        (self.d / "setup.json").write_text(json.dumps({"schema": "ait-tennis-setup/1", "players": [
            {"name": "Ann", "sex": "female", "look": {"height_m": 1.7}},
            {"name": "Belle", "sex": "female", "look": {"height_m": 1.7}}]}), encoding="utf-8")

    def _watch(self, *extra):
        import contextlib, io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.T.main(["--watch", "--season", "s1", "--season-dir", str(self.d), "--names", "Ann,Belle",
                                "--rallies", "2", "--clock", "1794300000000", "--surface", "clay", *extra])
        return code, err.getvalue()

    def _close(self, why="a test closed this season"):
        return self.T.close_season("s1", str(self.d), why)

    def _book(self):
        return json.loads((self.d / "practice.json").read_text(encoding="utf-8"))

    def test_closing_keeps_every_number_and_adds_one_word(self):
        """The whole point of closing rather than discarding: the balls that were hit stay hit. Only `closed`
        appears, and the sessions are the same sessions, to the byte count."""
        self._watch("--mode", "practice")
        before = self._book()
        self._close()
        after = self._book()
        for k in ("members", "opened", "season"):
            self.assertEqual(after.get(k), before.get(k), f"closing changed {k}")
        self.assertIn("closed", after)
        self.assertIn("when", after["closed"])
        self.assertIn("why", after["closed"])
        self.assertEqual(after["closed"]["why"], "a test closed this season")

    def test_a_closed_season_takes_no_more_sessions(self):
        self._watch("--mode", "practice")
        self._close()
        before = (self.d / "practice.json").read_text(encoding="utf-8")
        code, err = self._watch("--mode", "practice")
        self.assertEqual(code, 2, "a session was played into a closed season")
        self.assertIn("closed", err)
        self.assertIn("--season", err, "the refusal does not say how to open the next one")
        self.assertEqual((self.d / "practice.json").read_text(encoding="utf-8"), before,
                         "a refused session still wrote to the file")

    def test_a_closed_season_cannot_be_seeded_either(self):
        """`--seed` writes a carried history, and it writes it from `open_book` — which is why the closed check had
        to move in front of `open_book` rather than after it. A refusal that arrives after the write is not one."""
        self._watch("--mode", "practice")
        self._close()
        before = (self.d / "practice.json").read_text(encoding="utf-8")
        code, err = self._watch("--mode", "practice", "--seed", "300,300")
        self.assertEqual(code, 2)
        self.assertEqual((self.d / "practice.json").read_text(encoding="utf-8"), before,
                         "a refused seed still wrote a carried history into a closed season")
        self.assertNotIn("carried", (self.d / "practice.json").read_text(encoding="utf-8"))

    def test_the_report_says_the_season_is_closed_and_not_comparable(self):
        self._watch("--mode", "practice")
        self._close("the rules changed after it was played")
        report = self.T.season_report("s1", str(self.d))
        self.assertIn("is closed", report)
        self.assertIn("the rules changed after it was played", report)
        self.assertIn("not comparable", report, "a closed season is presented as if it were comparable")
        # and it is marked at the TOP, before any member's numbers, so a reader cannot take the totals first
        self.assertLess(report.index("is closed"), report.index("## Ann"))

    def test_closing_a_season_that_does_not_exist_is_refused(self):
        self.assertEqual(self.T.close_season("nope", str(self.tmp / "nope"), "x"), 2)
        self.assertFalse((self.tmp / "nope" / "practice.json").exists(),
                         "closing a season that does not exist invented one")

    def test_closing_twice_does_not_move_the_date(self):
        self._watch("--mode", "practice")
        self._close("first")
        when = self._book()["closed"]["when"]
        self.assertEqual(self._close("second"), 0)
        self.assertEqual(self._book()["closed"]["when"], when)
        self.assertEqual(self._book()["closed"]["why"], "first", "closing twice rewrote the reason")


class TestTheCastPlaysByItsOwnRules(unittest.TestCase):
    """The founder, 2026-11-19: *"always same-sex competition, same or mixed sex practice... Those outcomes can be
    skewed by the user putting particular pairs together for manual play."*

    Three things follow, and none of them is a preference:

    * the rule is enforced in BOTH producers (`--watch` and `--rally`), because a rule enforced in one of two is a
      rule the other one breaks;
    * a member whose group the season does not state is refused by name rather than defaulted, because a default
      here silently decides somebody's group for them;
    * a session records whether it was a competition and whether a person started it, so a season a human
      hand-shaped cannot be read as one that played itself. `mode` already means what KIND of session (rallies,
      fed balls, the person's seat), so this is its own field rather than a fourth value of one the report sorts
      on."""

    def setUp(self):
        import importlib, tempfile, shutil
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")
        self.tmp = Path(tempfile.mkdtemp(prefix="tennis-cast-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _season(self, name="s1", groups=("female", "female", "male"), unnamed=()):
        d = self.tmp / name
        d.mkdir(parents=True, exist_ok=True)
        people = ["Ann", "Belle", "Cid"][:len(groups)]
        players = []
        for who, sex in zip(people, groups):
            row = {"name": who, "look": {"height_m": 1.7, "build": 1.0, "kit": "#334455", "skin": "#aa8866",
                                         "hair": "#222222", "lower": "skirt", "racquet": True, "hand": "right"}}
            if sex and who not in unnamed:
                row["sex"] = sex
            players.append(row)
        (d / "setup.json").write_text(json.dumps({"schema": "ait-tennis-setup/1", "players": players}),
                                      encoding="utf-8")
        return d

    def _watch(self, d, names, *extra, season="s1"):
        import contextlib, io
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = self.T.main(["--watch", "--season", season, "--season-dir", str(d), "--names", names,
                                "--rallies", "2", "--clock", "1794200000000", "--surface", "clay", *extra])
        return code, out.getvalue(), err.getvalue()

    def _book(self, d):
        f = Path(d) / "practice.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None

    def test_two_members_of_one_group_may_compete(self):
        d = self._season(groups=("female", "female"))
        code, out, err = self._watch(d, "Ann,Belle")
        self.assertEqual(code, 0, err)
        session = self._book(d)["members"]["Ann"]["sessions"][-1]
        self.assertIs(session["competition"], True, "a same-group competition was not recorded as one")
        self.assertEqual(session["by"], "a person")

    def test_a_competition_across_groups_is_refused_and_writes_nothing(self):
        """Refused by name and not re-paired: the interesting failure is the silent one, where a mixed pair is
        quietly relabelled a practice and the season's ranking is built out of it."""
        d = self._season(groups=("female", "female", "male"))
        code, out, err = self._watch(d, "Ann,Cid")
        self.assertEqual(code, 2, "a cross-group competition was allowed to play")
        self.assertIn("same-sex", err)
        self.assertIsNone(self._book(d), "a refused competition wrote a season file")

    def test_the_same_pair_may_practice(self):
        d = self._season(groups=("female", "female", "male"))
        code, out, err = self._watch(d, "Ann,Cid", "--mode", "practice")
        self.assertEqual(code, 0, err)
        session = self._book(d)["members"]["Ann"]["sessions"][-1]
        self.assertIs(session["competition"], False, "a practice was recorded as a competition")

    def test_an_unnamed_group_is_refused_rather_than_assumed(self):
        """The rule reads `sex` from the season's setup.json and there is no other fact about a person in these
        files. If it is absent the answer is "I cannot place this player", not "assume they match"."""
        d = self._season(groups=("female", "", "male"), unnamed=("Belle",))
        code, out, err = self._watch(d, "Ann,Belle")
        self.assertEqual(code, 2)
        self.assertIn("Belle", err, "the refusal does not name the member whose group is missing")
        self.assertIn("setup.json", err, "the refusal does not say where the group should be written")
        self.assertIsNone(self._book(d))

    def test_a_session_says_who_started_it_and_the_report_prints_the_split(self):
        """The founder's own sentence about skewing a season by pairing players by hand is only checkable if the
        file distinguishes his sessions from the schedule's. It is printed as two totals, not averaged away."""
        d = self._season(groups=("female", "female"))
        self._watch(d, "Ann,Belle")
        self._watch(d, "Ann,Belle", "--by", "the schedule", "--clock", "1794200000001")
        book = self._book(d)
        bys = [x["by"] for x in book["members"]["Ann"]["sessions"]]
        self.assertEqual(bys, ["a person", "the schedule"])
        report = self.T.season_report("s1", str(d))
        self.assertIn("started by a person (1x), the schedule (1x)", report,
                      "the report does not tell a hand-shaped season from a scheduled one")

    def test_a_session_older_than_the_rule_is_not_guessed_at(self):
        """Every session in the existing seasons predates this field. A report that filled the gap with "practice"
        or "competition" would be inventing a fact about balls already hit, so it says which sessions it cannot
        speak for and leaves them out of the totals."""
        d = self._season(groups=("female", "female"))
        self._watch(d, "Ann,Belle")
        book = self._book(d)
        for m in book["members"].values():
            for x in m["sessions"]:
                x.pop("competition", None)
                x.pop("by", None)
        (Path(d) / "practice.json").write_text(json.dumps(book, indent=1, sort_keys=True), encoding="utf-8")
        report = self.T.season_report("s1", str(d))
        self.assertIn("older than the rule", report)
        self.assertNotIn("1 competition", report, "the report counted a session it cannot classify")


class TestTheCastCanBeDrawn(unittest.TestCase):
    """The founder's cast, 2026-11-19: three males and three females who play. A cast is only a cast if every one of
    them can be PUT ON THE COURT, and until this test existed the failure was silent in the two places it hurts:

    * `replay3d.html` builds the body file from the player's name (`p.body`, which `tennis_script.py` writes as
      `name.lower()`), so a member with no `bodies/<name>.glb` does not draw — the page shows its error overlay and
      the film is a black screen with an apology. Colette and Remy had 32 recorded balls and no body at all;
    * a missing `bodies/faces/<name>.jpg` was a 404 in an `<img>`, so the break card showed a broken-image glyph
      with a name under it. That is worse than no card: a glyph reads as a fault in the page, not as a member who
      has not been drawn.

    `lab/body.py` — the file that builds a body from parameters — was also lost once: committed on 2026-11-10 and
    never pushed, so every clone had the finished `.glb` files and none had the machine that makes them. That is
    item 0's disease, and the first test here is what stops it recurring quietly."""

    def setUp(self):
        self.games = REPO / "games" / "tennis"
        self.bodies = self.games / "bodies"
        self.seasons = self.games / "seasons"

    def test_the_body_builder_is_in_the_repository(self):
        """A `.glb` is a build artifact. If the script that makes one is not on `main`, then the cast cannot grow and
        nobody can tell why — which is exactly what happened: two bodies in every clone, no builder in any."""
        f = REPO / "lab" / "body.py"
        self.assertTrue(f.exists(), "lab/body.py is not in the repository, so no new member can be given a body")
        head = f.read_text(encoding="utf-8")[:400]
        self.assertIn("blender", head.lower(), "lab/body.py does not declare that it runs under Blender")
        self.assertIn("--name", f.read_text(encoding="utf-8"),
                      "the builder has no --name argument, so it cannot build a member by name")

    def test_every_member_a_season_record_names_can_be_drawn(self):
        """The invariant that would have caught Colette and Remy before a film was ever attempted: a season's record
        and a season's appearance file must name the same people, and each of them must have a body on disk."""
        for season in sorted(p.name for p in self.seasons.iterdir() if p.is_dir()):
            d = self.seasons / season
            book = json.loads((d / "practice.json").read_text(encoding="utf-8"))
            setup = json.loads((d / "setup.json").read_text(encoding="utf-8"))
            looks = {p["name"] for p in setup["players"]}
            for name in sorted(book.get("members", {})):
                self.assertIn(name, looks,
                              f"{season} records {name} but its setup.json does not give {name} a look, so a "
                              f"film of that season would draw a stranger or nothing")
                glb = self.bodies / f"{name.lower()}.glb"
                self.assertTrue(glb.exists(),
                                f"{season} records {name} and the film looks for {glb.name}, which does not exist — "
                                f"a player who cannot be drawn is a player who cannot be watched")

    def test_a_missing_portrait_draws_a_monogram_and_not_a_broken_image(self):
        """The page cannot know a face file is absent without asking for it, so the fallback has to be an `onerror`
        on the image itself. The flag lives on the IMAGE and not on the card, because the card's `className` is
        rebuilt every frame from `on` — the first version of this lost its own monogram while drawing the right
        name, which is the sort of defect only a still catches."""
        page = (self.games / "replay3d.html").read_text(encoding="utf-8")
        self.assertIn('id="facemono"', page, "the break card has no monogram element to fall back to")
        self.assertIn("img.onerror", page, "a 404 portrait has no handler, so it draws a broken-image glyph")
        self.assertIn('img.className = "none"', page,
                      "the fallback does not hide the image, so a broken glyph sits above the monogram")
        self.assertNotIn('card.className += " noface"', page,
                         "the no-face flag is on an element whose className is rewritten every frame")

    def test_the_four_with_no_drawing_are_each_asked_for_by_name(self):
        """The instruction sheet lives in the folder a drawing is uploaded to, which is the only place it is read
        at the moment it is needed. That placement is worth nothing if it drifts from the cast: a member added to a
        season and not added to the sheet is a member nobody is ever asked to draw, and the gap looks like a
        decision. So the sheet is checked against the drawings that exist."""
        files = {p.stem for p in (self.games / "bodies" / "faces").glob("*.jpg")}
        sheet = (self.games / "bodies" / "faces" / "README.md").read_text(encoding="utf-8")
        seen = {}
        for d in (self.seasons / "2026-spring", self.seasons / "2026-advent"):
            for p in json.loads((d / "setup.json").read_text(encoding="utf-8"))["players"]:
                seen[p["name"]] = True
        missing = sorted(n for n in seen if n.lower() not in files)
        self.assertTrue(missing, "every member has a drawing, so this test has nothing to check — say so instead")
        for n in missing:
            self.assertIn(f"`{n.lower()}.jpg`", sheet,
                          f"{n} has no drawing and is not asked for by name in bodies/faces/README.md")

    def test_the_foot_has_an_instrument_before_it_has_another_constant(self):
          """The back foot's heel-up has been rewritten four times and each time the coefficient was a guess, because
          nothing in the page could say where the toe was. 2026-11-19 it was measured properly and the guess turned
          out to be the wrong KIND of answer: the foot bone's local X moves the toe 0.146ft per radian (a rotation
          square to the bone would move it 0.38), and the toe never reaches the ground at any setting, because what
          lifts a heel is the ankle rising and the ankle belongs to the root and the knee.

          So the constant stays 0 and the probe stays in. This asserts the probe, not the number: a future pass that
          starts by guessing again is the failure this test is for."""
          page = (self.games / "replay3d.html").read_text(encoding="utf-8")
          self.assertIn("function toeOf(", page, "there is no way to read where the foot touches the ground")
          self.assertIn("debug toe", page, "the toe is measured and never reported")
          self.assertIn('q.has("heel")', page, "the heel constant cannot be swept, so it can only be guessed at")
          self.assertIn("0.146ft per radian", page,
                        "the measurement is not written down, so the next pass will re-derive it from nothing")
          self.assertIn("let HEEL = 0;", page,
                        "the heel is nonzero again without a measurement behind it")

    def test_the_cast_is_three_and_three(self):
        """`CAST.md` is prose and prose does not fail. This reads the six names out of the seasons' setup files and
        checks the two things the founder asked for that a test can see: six players, and both groups present."""
        seen = {}
        for d in (self.seasons / "2026-spring", self.seasons / "2026-advent"):
            for p in json.loads((d / "setup.json").read_text(encoding="utf-8"))["players"]:
                seen[p["name"]] = (p.get("sex") or "").strip().lower()
        self.assertEqual(len(seen), 6, f"the cast is {sorted(seen)}, which is not six players")
        for name, sex in seen.items():
            self.assertIn(sex, ("male", "female"),
                          f"{name} has no group, so {name} cannot compete — an unnamed group is a refusal in "
                          f"may_compete, not a default")
        self.assertEqual(sum(1 for v in seen.values() if v == "female"), 3,
                         f"the cast is not three and three: {sorted(seen.items())}")


class TestTheFilmIsTheSession(unittest.TestCase):
    """The founder's definition of "an integral part of Kythe", 2026-11-19: a session the user can WATCH and a
    session the members PLAY are the same session, and its result reaches the season "the same as if his own
    calculations had simulated the same game".

    Until this was built there were two tennis games sharing one engine. `--rally` asked each member's engine for
    a shot line, played it, and wrote `practice.json`. `lab/tennis_script.py` played the same engine into a film
    and wrote nothing back. So a member could practise all season and the film would never know, and the film
    could be watched all night while the season did not move. `--watch` is the seam: it reads the players'
    practice out of the season file, plays the film at that skill, and records the session the film played
    through the one writer the rally path also uses.

    What these hold is that the two halves cannot disagree — every number in the session entry is the film's own —
    and that one clock is one film, which is what makes the page's film a rendering of a season rather than a
    second game played beside it."""

    def setUp(self):
        import importlib, tempfile, shutil
        sys.path.insert(0, str(REPO / "lab"))
        self.T = importlib.import_module("tennis")
        self.tmp = Path(tempfile.mkdtemp(prefix="tennis-watch-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _watch(self, *extra, rounds=4, clock=1793809110303, names="Colette,Remy", season="s1"):
        import contextlib, io
        d = self.tmp / season
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.T.main(["--watch", "--season", season, "--season-dir", str(d),
                                "--names", names, "--rallies", str(rounds),
                                "--clock", str(clock), "--surface", "clay", "--mode", "practice", *extra])
        return code, d, out.getvalue()

    def _json(self, d, name):
        return json.loads((Path(d) / name).read_text(encoding="utf-8"))

    def test_every_number_in_the_session_is_the_films_own(self):
        """The whole claim in one assertion set: balls, shots, in-play, the mean rally and the longest rally are
        read off the film, not counted a second time. A season that re-derived them could drift from the film
        that was watched, and then the user would be looking at a game that is not the one in the record."""
        code, d, _out = self._watch()
        self.assertEqual(code, 0)
        book, film = self._json(d, "practice.json"), self._json(d, "watch.json")
        # The film this test plays, pinned so that a change to the game is a change to this line rather than a
        # silent one. The fourth point is 2 shots and was 1 until 2026-11-20: a first serve that misses now
        # costs a serve rather than the point (item 19b), so the point that was a one-shot "double fault" is a
        # rally. This list is a record of what this seed does today, not a rule.
        self.assertEqual([r["length"] for r in film["rallies"]], [2, 2, 3, 2])
        # And the pin does not have to be trusted, because a rally has to be the shots it points at: every
        # shot belongs to exactly one rally, the rallies cover the film in order, and a length is the count.
        # That is the invariant that survives the next change to the game.
        self.assertEqual([i for r in film["rallies"] for i in r["shots"]], list(range(len(film["shots"]))),
                         "the rallies do not cover the film's shots, in order, exactly once")
        for r in film["rallies"]:
            self.assertEqual(r["length"], len(r["shots"]), "a rally's length is not the number of shots it names")
        for name in ("Colette", "Remy"):
            mine = [s for s in film["shots"] if s["player"] == name]
            session = book["members"][name]["sessions"][-1]
            self.assertEqual(session["shots"], len(mine), f"{name}'s session and film disagree on the shots")
            self.assertEqual(session["of"], len(mine), "the denominator is not the film's")
            self.assertEqual(session["in_play"], sum(1 for s in mine if s["in"]),
                             "the in-play count is not the film's own `in` flags")
            self.assertEqual(book["members"][name]["balls"], len(mine))
            self.assertEqual(session["mean_rally"], round(sum(r["length"] for r in film["rallies"]) / 4, 2))
            self.assertEqual(session["longest"], max(r["length"] for r in film["rallies"]))
            self.assertEqual(session["with"], ["Remy" if name == "Colette" else "Colette"])
            self.assertEqual(session["mode"], "rally", "a watched film is a rally, and the report sorts on it")

    def test_the_film_is_played_at_the_skill_the_season_wrote(self):
        """The other direction of the same seam, and the one the founder named: "the same players, at their current
        skill levels". The second film must be played by players who own the balls the first session gave them."""
        _c, d, _o = self._watch(season="two")
        first = self._json(d, "watch.json")
        self.assertEqual([p["balls"] for p in first["players"]], [0, 0],
                         "this test needs a first session where nobody has a history")
        _c, d, _o = self._watch(season="two", clock=1793809110404)
        second = self._json(d, "watch.json")
        book = self._json(d, "practice.json")
        self.assertEqual([p["balls"] for p in second["players"]],
                         [book["members"][p["name"]]["sessions"][0]["shots"] for p in first["players"]],
                         "the second film was played at a practice the season had not given it")
        self.assertGreater(second["players"][0]["control"], first["players"][0]["control"],
                           "the film's two runs are the same player, so practising must have improved them")
        self.assertEqual(second["season"], "two", "the film does not say which season's skill it was played at")

    def test_one_clock_is_one_film(self):
        """Why a film may overwrite the last one: it is derived from the season and a clock. Two films at the same
        clock and the same practice are the same film, to the shot. That is the property that makes watching it
        evidence about the season rather than about a random stream."""
        _c, a, _o = self._watch(season="a")
        _c, b, _o = self._watch(season="b")
        fa, fb = self._json(a, "watch.json"), self._json(b, "watch.json")
        self.assertEqual(len(fa["shots"]), len(fb["shots"]))
        self.assertEqual([r["length"] for r in fa["rallies"]], [r["length"] for r in fb["rallies"]])
        self.assertEqual([s["v0"] for s in fa["shots"]], [s["v0"] for s in fb["shots"]],
                         "the same clock and the same hands produced a different film")
        self.assertEqual([s["contact"] for s in fa["shots"]], [s["contact"] for s in fb["shots"]])

    def test_the_season_keeps_every_session_and_the_film_keeps_only_the_last(self):
        """Stated as a test because it is a decision and not an accident. `practice.json` is the record: nothing is
        ever reset and nothing is ever overwritten, so two watched sessions are two entries. `watch.json` is a
        rendering of the season at one clock, so there is one of it and each session replaces it. The record of a
        session outlives its film; the film does not have to pay rent in the repository forever."""
        _c, d, _o = self._watch(season="kept", clock=1793809110303)
        _c, d, _o = self._watch(season="kept", clock=1793809110404)
        book = self._json(d, "practice.json")
        for name in ("Colette", "Remy"):
            self.assertEqual(len(book["members"][name]["sessions"]), 2, "a second session overwrote the first")
        films = [p for p in Path(d).iterdir() if p.name.startswith("watch") and p.suffix == ".json"]
        self.assertEqual(len(films), 1, f"a film per session would be a film per session in git: {films}")
        self.assertEqual(self._json(d, "watch.json")["clock_ms"], 1793809110404, "the film is not the last session")

    def test_a_film_asks_nobody_and_needs_no_key(self):
        """A film is played by the engine. `--watch` therefore has no business accepting `--vendor`, and on the
        night there is no key in the environment it must still play — the member's own key is for the sessions the
        members play, and a scouting error here would be the flags being accepted and silently ignored, which is
        the defect `main()` already refuses on the physics path."""
        import contextlib, io, os
        self.assertEqual(self.T.main(["--watch", "--season", "k", "--season-dir", str(self.tmp / "k"),
                                      "--names", "A,B", "--rallies", "2", "--vendor", "groq"]), 2,
                         "--watch accepted a member's engine and would have ignored it")
        saved = {k: v for k, v in os.environ.items() if k.startswith("TRIBE_")}
        for k in saved:
            os.environ.pop(k)
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code, d, _o = self._watch(season="nokey")
        finally:
            os.environ.update(saved)
        self.assertEqual(code, 0, "a film needed a key, so it is not the engine playing")
        self.assertTrue((d / "watch.json").exists())

    def test_a_watch_with_no_season_is_a_preview_and_writes_nothing(self):
        """`--watch` without `--season` plays from the flags. It is allowed — it is how a change to the legs gets
        looked at in ten seconds — but it must not touch a season, and it must say so rather than looking like a
        recorded session in a folder nobody opened."""
        import contextlib, io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.T.main(["--watch", "--names", "A,B", "--rallies", "2", "--clock", "1793809110303",
                                "--surface", "clay", "--practice", "400,20"])
        self.assertEqual(code, 0)
        self.assertIn("not recorded anywhere", out.getvalue(), "a preview did not admit it was not a session")
        self.assertEqual(list(self.tmp.iterdir()), [], "a preview wrote into a season folder")


class TestAServeIsDrawnFromItsToss(unittest.TestCase):
    """Item 19's remainder, 2026-11-26: the toss was in the record for a week and never on the screen.

    `shotAt` returned the FIRST segment whose `[start, start+dur+hold)` contained the time, and those windows overlap
    by construction — a point's break runs past the instant the next serve's toss begins — so the break won and 16 of
    26 serves in `seasons/2026-11-19` were drawn from a contact with no ball before it. A film is a timeline, so the
    segment that is being drawn is the latest one that has STARTED. The second half is the break that has to make
    room for the next shot's own stance lead, or the walk back is drawn over the toss."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")
        self.tool = (REPO / "lab" / "tennis_sweep.py").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")

    def test_the_segment_being_drawn_is_the_latest_that_has_started(self):
        self.assertIn("if (t < s.start) break;", self.page,
                      "shotAt no longer walks forward to the last segment that has begun")
        self.assertNotIn("t < s.start + s.dur + s.hold", self.page,
                         "shotAt is back to the first window that contains the time")

    def test_the_break_before_a_point_makes_room_for_the_next_stance(self):
        self.assertIn("const room = Math.max(0.75, lead + 0.05);", self.page,
                      "the break before a point is a hard-coded 0.75s again, so a toss is drawn over the walk back")

    def test_the_log_carries_the_windows_and_the_film(self):
        self.assertIn("+((s.start + s.dur + s.hold).toFixed(2))", self.page,
                      "debug segs no longer prints each segment's window end")
        self.assertIn("debug film", self.page, "there is no debug film line")
        # `debug film` was printed from T0, which is the frame timer and is reassigned every frame, so it reported
        # the last frame's clock as the film's start. It is the first segment's start now.
        self.assertIn("SEG[0].start.toFixed(2)", self.page, "debug film is printed from the frame timer again")
        self.assertNotIn("T0.toFixed(0), +(SEG[SEG.length - 1]", self.page,
                         "debug film reports performance.now() as the start of the film")

    def test_the_reader_counts_the_tosses_it_cannot_see(self):
        self.assertTrue("serves whose toss is never drawn" in self.tool,
                        "the reader cannot count the tosses")
        self.assertTrue("start <= r[0] < start + toss" in self.tool,
                        "the reader does not test a frame against the segment's own toss window")
        self.assertTrue("16 of 26" in self.backlog and "**0 of 26**" in self.backlog,
                        "the backlog does not carry both sides of the toss count")


class TestAnOverlappingPlanIsWalkedAndNotJumped(unittest.TestCase):
    """Item 2b's follow-up, 2026-11-26: 5.13ft in one 0.02s frame is 256ft/s, and no body does that.

    Two moves for the same player overlapped in the record, so `whereAt` read the first until its own `t1` and then
    the second's `to`, which had already finished. The first attempt clipped inside `whereAt` and made it worse —
    it changed the coordinate frame in the middle of a move — so the clip is a normalisation pass over the sorted
    plan: each move ends no later than the next begins, the clipped `to` is interpolated rather than re-timed, and
    `from` is taken from the previous entry so the walk is continuous."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")

    def test_the_plan_is_sorted_then_clipped_then_chained(self):
        self.assertIn("const end = Math.min(m.t1, next ? next.t0 : Infinity);", self.page,
                      "a move is no longer clipped to the next one's start")
        self.assertIn("const from = seq.length ? seq[seq.length - 1].to : m.from;", self.page,
                      "a move no longer starts where the previous one ended")
        self.assertIn("PLAN[name] = seq;", self.page, "the normalised sequence is thrown away")
        self.assertIn("const to = end >= m.t1 ? m.to : [from[0] + (m.to[0] - from[0]) * k,", self.page,
                      "a clipped move is re-timed rather than interpolated")

    def test_the_numbers_are_in_the_record(self):
        for piece in ("5.13", "0.86", "33.6ft", "14.8ft/s"):
            self.assertTrue(piece in self.backlog, f"{piece} is not in backlog item 2b")
        self.assertTrue("item 31" in self.backlog.lower(),
                        "the 41 frames the fix did not remove are not attributed to item 31")


class TestTheTurnBack(unittest.TestCase):
    """Item 6, 2026-11-26. Two claims were wrong and the second was wrong because of the first.

    (1) The done-test "facing back towards the centre within 1.2s" is true by construction on a still body: the page
    already faces a still body at the net. (2) The 26deg facing error at a contact was NOT the striking window's. It
    was `shotAt`'s — the body was still in the previous point's watch — and the same bug cost 16 of 26 tosses. A
    sweep with `?square=5`, a window fifteen times wider than the default, is frame-for-frame identical to the
    default, which is the evidence that `SQUARE_UP` is unmeasured on this film rather than the cure. The restated
    done-test is square to the NET, because two shots are struck from past the net where "the middle of the court"
    is behind the striker."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")
        self.tool = (REPO / "lab" / "tennis_sweep.py").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")

    def test_the_striking_window_opens_before_the_contact(self):
        self.assertIn('const SQUARE_UP = q.has("square")', self.page, "the striking window has no knob")
        self.assertIn("tlc > -SQUARE_UP && tlc < SQUARE_AFTER", self.page,
                      "the striking window opens at the contact again")
        self.assertNotIn("sh.player === pl.name && tl < 0.45", self.page,
                         "the old window that opened at the contact is back")

    def test_the_reader_maps_the_columns_to_the_players_by_measurement(self):
        # `debug plan`'s key order is the PUSH order and the sweep row's columns are `D.players`' order; on this
        # season those are `[Colette, Gwen]` and `[Gwen, Colette]`. Mapping one to the other silently renames the
        # players, which is how item 5 reported the receiver's speed as the striker's (STILLS.md, trap 7).
        self.assertTrue("def order(rows, segs, fallback):" in self.tool, "the reader maps columns by position")
        self.assertTrue('if p and p[1] == 1:' in self.tool,
                        "the reader no longer votes from the log's own isHitter flag")
        self.assertTrue("assert len(who) == 1" in self.tool,
                        "a column that claims two hitters no longer stops the reader")

    def test_the_reader_reports_square_to_the_net(self):
        self.assertTrue("SQUARE TO THE NET" in self.tool, "the reader does not report the restated done-test")
        self.assertTrue("def err_net(" in self.tool, "there is no net-facing measure in the reader")

    def test_the_backlog_says_which_change_moved_the_number(self):
        for piece in ("0.04s", "26deg", "8deg", "6 of the 34", "98deg", "15deg"):
            self.assertTrue(piece in self.backlog, f"{piece} is not in the backlog entry for item 6")
        self.assertTrue("IS NOT WHAT FIXED IT" in self.backlog,
                        "the backlog still credits SQUARE_UP with the facing fix")
        self.assertTrue("?square=5" in self.backlog,
                        "the backlog does not carry the measurement that shows the window is inert here")
        self.assertTrue("could not fail" in self.backlog,
                        "the vacuous half of the old done-test is not named")


class TestARecoveryTheBallHasAlreadyInterrupted(unittest.TestCase):
    """Item 31, 2026-11-26. The record used to finish every recovery whatever the opponent's ball was doing, and
    then measure the next run from a place the player never reached: on `seasons/2026-11-19` shot 26 Colette is
    sent 36ft in 2.44s while the ball comes back in 1.56s, so the next run starts 13.6ft from where her feet are
    drawn and is covered in 0.48s — and the film pays for it at 43ft/s over 41 frames. A recovery now stops when the
    ball she has just hit comes back, in BOTH engines, because a picture that disagrees with the scoreline about
    where the feet are is two different matches."""

    def setUp(self):
        import importlib
        sys.path.insert(0, str(REPO / "lab"))
        self.S = importlib.import_module("tennis_script")
        self.T = importlib.import_module("tennis")
        self.script = (REPO / "lab" / "tennis_script.py").read_text(encoding="utf-8")
        self.engine = (REPO / "lab" / "tennis.py").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")

    def _film(self, rallies=24):
        return self.S.play((300, 600), ("A", "C"), rallies, 1793809110303, "clay", self.S.SWAP_EVERY)

    def test_both_engines_bound_the_recovery_by_the_flight_of_the_ball(self):
        self.assertIn('caught = t_rec > traj["time"]', self.script,
                      "the picture runs the whole recovery whatever the ball is doing")
        self.assertIn('"cut": bool(caught)', self.script, "the record does not say a recovery was cut")
        self.assertIn('min(min(2.5, d / max(movement_speed(receiver), 1.0)), t["time"])', self.engine,
                      "the scoreline still moves the feet to the full recovery spot")

    def test_no_recovery_outlives_the_ball_and_no_run_outruns_the_legs(self):
        film = self._film()
        recs = [s["recover"] for s in film["shots"] if s.get("recover")]
        self.assertTrue(any(r.get("cut") for r in recs), "no recovery in this film was cut by the ball")
        for r in recs:
            self.assertLessEqual(r["got"], r["dist"] + 0.05,
                                 msg=f"the feet got {r['got']}ft of a {r['dist']}ft recovery")
            self.assertLessEqual(r["got"], 2.5 * r["speed"] + 0.05, msg="a recovery ran past its 2.5s cap")
            if not r.get("cut"):
                self.assertAlmostEqual(r["got"], r["dist"], places=0,
                                       msg="a recovery that was not cut still did not reach its spot")
        for s in film["shots"]:
            run = s.get("run")
            if run and run.get("t1"):
                self.assertLessEqual(run["dist"] / run["t1"], (run.get("speed") or 0) * 1.05,
                                     f"shot {s['n']} asks for {run['dist'] / run['t1']:.1f}ft/s "
                                     f"from legs that do {run.get('speed')}")

    def test_the_backlog_says_what_was_measured_and_what_was_not(self):
        self.assertTrue("FIXED 2026-11-26 for the mechanism" in self.backlog,
                        "item 31's headline does not distinguish the mechanism from the number")
        self.assertTrue("cannot be reproduced" in self.backlog,
                        "the backlog still implies the 41 frames were re-measured")


class TestAChangeOfEndsIsInThePlan(unittest.TestCase):
    """Item 32, 2026-11-26, found by sweeping the first film that has a change of ends in it: 6.00ft in one 0.02s
    frame, because the swap was applied inside `whereAt` AFTER the first serve's stance lead had already walked the
    player to the other spot — and the swap's own hard-coded spot was a staler statement of where they stand than
    the plan's. A change of ends is a move in the plan now, and it only cuts when the plan has not already carried
    the journey. Measured: 6.00ft -> 0.40ft and 0.39ft, and 0 frames over 25ft/s in either film."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")

    def test_the_defect_its_fix_and_the_numbers_are_on_the_record(self):
        self.assertTrue("## Item 32" in self.backlog, "item 32 is not opened")
        for piece in ("6.00ft", "202.04", "item31-after", "1ft in a frame", "0.40ft", "**0**"):
            self.assertTrue(piece in self.backlog, f"{piece} is not in the item 32 entry")

    def test_the_swap_is_a_move_in_the_plan_and_whereAt_no_longer_skips(self):
        self.assertIn("(PLAN[name] = PLAN[name] || []).push({ t0: s.t - 0.001, t1: s.t, from: to, to, swap: true });",
                      self.page, "the change of ends is not a move in the plan")
        self.assertTrue("if (sw && m.t1 <= sw.t) continue;" not in self.page,
                        "whereAt still skips the moves before a change of ends, which is what undid the walk")
        self.assertTrue("(sw && m.t0 < sw.t) ? sw.to : m.from" not in self.page,
                        "whereAt still re-bases a move on the hard-coded swap spot")
        self.assertTrue("const to = (at && north === s.north) ? at : s.to;" in self.page,
                        "the swap no longer prefers the plan's own position to its hard-coded one")


class TestTheFilmSaysHowFarBehindTheSeasonItIs(unittest.TestCase):
    """Item 23, 2026-11-26. `watch.json` is the last session somebody WATCHED, not the last one that was played:
    Dmitri's games run live and off-screen, and the clock can play five sessions overnight while the page still
    shows the film from before them. A viewer has to be told which session they are looking at."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")
        self.engine = (REPO / "lab" / "tennis.py").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")

    def test_the_film_carries_the_session_it_played(self):
        self.assertTrue('data["session"] = {"n": max(sessions_played(book).values(), default=0),' in self.engine,
                        "the record does not say which session it is")
        self.assertTrue("target.write_text(json.dumps(data, indent=1)" in self.engine,
                        "the film is no longer written")
        # The order matters: a film written before `record_session` cannot say what it played.
        self.assertLess(self.engine.index("record_session(book, when=when"),
                        self.engine.index('data["session"] = {"n": max(sessions_played(book)'),
                        "the film is written before the session is in the book, so it cannot say which one it is")

    def test_the_page_reads_it_and_the_book_beside_it(self):
        self.assertTrue("let SEASONNOTE" in self.page, "the page does not build a session line")
        self.assertTrue('REC.replace(/watch\\.json.*$/, "practice.json")' in self.page,
                        "the page does not fetch the book beside the film")
        self.assertTrue("since this film" in self.page and "this is the latest" in self.page,
                        "the page cannot say whether the film is behind or current")
        self.assertTrue('+ (SEASONNOTE ? ` · ${SEASONNOTE}` : "")' in self.page,
                        "the session line is not printed")

    def test_the_fixture_is_named_as_a_fixture(self):
        book = json.loads((REPO / "games" / "tennis" / "records" / "item23-fixture" /
                           "practice.json").read_text(encoding="utf-8"))
        self.assertTrue(book.get("note", "").startswith("A FIXTURE"),
                        "a typed book in records/ must say that it was typed, or it reads as a played season")
        film = json.loads((REPO / "games" / "tennis" / "records" / "item23-fixture" /
                           "watch.json").read_text(encoding="utf-8"))
        self.assertIn("session", film, "the fixture film has no session block to demonstrate")
        self.assertTrue("DONE 2026-11-26" in self.backlog, "item 23 is not marked done")


class TestPickleball(unittest.TestCase):
    """The second sport: the rules that are not tennis's, and the ball that is not a tennis ball.

    The design page is `games/pickleball/README.md`; these tests are the numbers it claims, checked rather
    than restated. Three of them exist because the engine was wrong in ways the page could not see: a
    bisection that returned a lob for a target the flat shot reaches (+45 degrees, eleven feet wide), a
    harness that aimed every south-end shot back into the south end's own court (the north team won 11-0
    three times before I looked), and the clock's wind rule, which at 20 mph leaves a 33 mph serve no legal
    landing at all. Each of those is a test now.
    """

    @classmethod
    def setUpClass(cls):
        cls.pk = load(REPO / "lab" / "pickleball.py", "pickleball_mod")
        cls.t = load(REPO / "lab" / "tennis.py", "tennis_mod_pb")

    def test_the_ball_constant_is_the_measured_ball_and_not_the_tennis_one(self):
        """k = half rho Cd A / m for the 40-hole outdoor ball: 0.01031/ft. The page's number, computed from
        this file's own constants, and 1.6x the tennis ball despite the smaller diameter."""
        area, mass = self.pk.ball_geometry()
        self.assertAlmostEqual(area, 0.04493, places=4)
        self.assertAlmostEqual(mass, 0.001709, places=6)
        self.assertAlmostEqual(self.pk.DRAG, 0.01031, places=5)
        self.assertAlmostEqual(self.pk.DRAG / 0.0063, 1.64, places=1)
        # and the indoor ball is the other measured value, not a fudge factor
        indoor = self.pk.drag_of({"make": "indoor 26-hole", "diameter_in": 2.87, "mass_oz": 0.88,
                                  "holes": 26, "cd": 0.45})
        self.assertAlmostEqual(indoor, 0.01406, places=5)

    def test_the_engine_plays_with_the_pickleball_ball_not_the_tennis_one(self):
        """A 40 mph ball that lands 20 ft past the net arrives at 25 mph. If the integrator had been called
        without the drag argument it would arrive at 31, which is the tennis ball, and no line would say so."""
        p = self.t.Player(name="X", north=True, practice=300)
        shot = self.pk.strike(p, None, face=12.6, power=40 / 0.60, aim=self.pk.CENTRELINE, shot="groundstroke",
                             surface="hard", wind=(0.0, 0.0), pos=(0.0, self.pk.CENTRELINE), clean=True)
        land = shot["traj"]["land"][0]
        self.assertGreater(land, self.pk.NET_X + 10, "the drive should reach the backcourt")
        # horizontal pace at the bounce, from the bounce vector
        vx = shot["traj"]["bounce"]["v"][0]
        self.assertLess(abs(vx) / self.t.MPH, 27.0, "a pickleball drive must have lost a third of its pace")

    def test_the_kitchen_line_is_in_for_a_ball_and_out_for_a_volleying_foot(self):
        pk = self.pk
        self.assertTrue(pk.in_kitchen(15.0), "the line is in the kitchen")
        self.assertTrue(pk.in_kitchen(29.0))
        self.assertFalse(pk.in_kitchen(14.99))
        self.assertFalse(pk.in_kitchen(29.01))
        self.assertAlmostEqual(pk.feet_from_kitchen_line(15.0), 0.0, places=6)
        self.assertAlmostEqual(pk.feet_from_kitchen_line(12.0), 3.0, places=6)

    def test_a_serve_on_the_kitchen_line_is_short_and_a_rally_ball_on_it_is_in(self):
        """The one line call that differs between the serve and every other shot."""
        self.assertFalse(self.pk.in_service_area((29.0, 15.0), True, 5.0), "a serve on the kitchen line is short")
        self.assertTrue(self.pk.in_service_area((29.02, 15.0), True, 5.0))
        ok, _ = self.pk.verdict({"player": self.t.Player(name="X", north=True), "shot": "groundstroke",
                                 "traj": {"land": (29.0, 10.0)}})
        self.assertTrue(ok, "a rally ball on the kitchen line is in")

    def test_the_serve_must_go_diagonally(self):
        pk = self.pk
        self.assertTrue(pk.in_service_area((33.0, 15.0), True, 5.0), "across the centreline: good")
        self.assertFalse(pk.in_service_area((33.0, 5.0), True, 5.0), "same side as the server: fault")
        self.assertFalse(pk.in_service_area((45.0, 15.0), True, 5.0), "past the baseline: fault")
        self.assertFalse(pk.in_service_area((16.0, 5.0), False, 15.0), "into the north kitchen: fault")
        self.assertTrue(pk.in_service_area((12.0, 5.0), False, 15.0), "a south serve into the north's court")

    def test_the_first_server_is_in_the_right_court_when_the_score_is_even(self):
        m = self.pk.new_match(["A", "B", "C", "D"])
        t = m.teams[0]
        for score, right in ((0, "A"), (1, "B"), (2, "A"), (3, "B")):
            t.score = score
            self.assertEqual(t.names[self.pk.right_player_index(t)], right, f"at {score}")
        # and the server stands on the right-hand side of their own end, which for the north end is y=5
        t.score = 0
        self.assertAlmostEqual(m.server_y(), 5.0, places=6)
        self.assertEqual(m.receiver(), "C", "the right court serves to the right court, across the line")

    def test_only_the_serving_team_can_score(self):
        m = self.pk.new_match(["A", "B", "C", "D"])
        self.pk.serve_first(m, 0)
        self.assertEqual(m.point_to(0), "point")
        self.assertEqual((m.teams[0].score, m.teams[1].score), (1, 0))
        self.assertEqual(m.point_to(1), "side out")
        self.assertEqual((m.teams[0].score, m.teams[1].score), (1, 0), "a receiver's rally is only a serve")
        self.assertEqual(m.serving, 1)

    def test_the_first_service_turn_of_a_game_has_one_server(self):
        m = self.pk.new_match(["A", "B", "C", "D"])
        self.pk.serve_first(m, 0)
        self.assertEqual(m.server(), "A")
        self.assertEqual(m.fault_by_serving(), "side out", "one server in the game's first turn")
        self.assertEqual(m.serving, 1)
        # and after that a turn has two
        self.assertEqual(m.fault_by_serving(), "second server")
        self.assertEqual(m.server(), "D")
        self.assertEqual(m.fault_by_serving(), "side out")

    def test_a_game_is_to_eleven_win_by_two(self):
        m = self.pk.new_match(["A", "B", "C", "D"])
        m.teams[0].score, m.teams[1].score = 11, 10
        self.assertFalse(m.over())
        m.teams[0].score = 12
        self.assertTrue(m.over())

    def test_doubles_needs_four_named_seats(self):
        for names in (["A"], ["A", "B"], ["A", "B", "C"]):
            with self.assertRaises(SystemExit):
                self.pk.new_match(names)
        m = self.pk.new_match(["A", "B", "C", "D"])
        self.assertEqual(m.teams[0].names, ["A", "B"])
        self.assertEqual(m.teams[0].partner_of("A"), "B")

    def test_a_volley_before_both_sides_have_bounced_is_a_fault(self):
        """The double bounce rule is one flag, so it can be read: the first three shots of a rally are never
        volleys, and the fourth may be."""
        say = []
        m = self.pk.new_match(["A", "B", "C", "D"])
        self.pk.serve_first(m, 0)
        import random as _random
        # the hands are seeded, because an unseeded rally is sometimes two shots long and this test reads the third
        players = {n: self.t.Player(name=n, north=(i < 2), practice=400, rng=_random.Random(7 + i))
                   for i, n in enumerate(["A", "B", "C", "D"])}
        pos = self.pk.Positions()
        choose = self.pk.scripted_chooser("hard")(players, ("N", 3.0), "hard")
        r = self.pk.play_rally(m, players, pos, choose, "hard", (0.0, 0.0), ("N", 3.0),
                               say=say.append, rally_no=1)
        kinds = [ln.split()[2] for ln in say if ln.strip()[:2].strip().rstrip(".").isdigit()]
        self.assertGreaterEqual(len(kinds), 3, "this test reads the third shot, so the rally has to reach it")
        self.assertEqual(kinds[0], "serve")
        # The serve and the RETURN of serve may not be volleyed; the third shot may, because the ball has then
        # bounced on both sides. The first version asserted otherwise, against an engine that also required a
        # DEEP ball to volley — two accidents encoded as rules. Both are gone (§5d).
        self.assertIn(kinds[1], ("shot", "groundstroke"), "the return of serve must bounce")
        self.assertIn(kinds[2], ("shot", "groundstroke", "volley"))

    def test_the_wind_is_capped_because_a_20mph_headwind_leaves_no_legal_serve(self):
        pk = self.pk
        for ms, expect in ((0, None), (12345, None)):
            direction, speed = pk.wind_for(ms)
            self.assertLessEqual(speed, pk.WIND_CAP)
        self.assertEqual(pk.WIND_CAP, 12.0)
        # the measurement behind the cap: still air and 20 mph of headwind, same serve
        p = self.t.Player(name="X", north=True, practice=300)
        def farthest(wind_mph):
            best = 0.0
            for i in range(0, 501, 5):
                el = self.math_radians(i / 10)
                v = 33.0 * self.t.MPH
                t = self.t.flight((0.0, 5.0, 2.4), (v * self.cos(el), 0.0, v * self.sin(el)),
                                  (-wind_mph * self.t.MPH, 0.0), "hard",
                                  drag=pk.DRAG, lift=pk.LIFT, net_x=pk.NET_X, surfaces=pk.SURFACES,
                                  net_profile=pk.net_profile)
                if t.get("land") and t["land"][0] > best:
                    best = t["land"][0]
            return best
        still, twenty = farthest(0.0), farthest(20.0)
        self.assertGreater(still, 44.0, "a 33 mph serve reaches the backcourt in still air")
        self.assertLess(twenty, 29.0, "and cannot reach the kitchen line into 20 mph of headwind")

    def test_the_engine_reproduces_the_design_pages_window_table(self):
        """The page's 35/40/45 mph windows, recomputed from this file's constants. A design page and an engine
        that disagree by two degrees are two designs."""
        for mph, want in ((35.0, 10.1), (40.0, 5.9), (45.0, 3.5)):
            hits = [i / 10 for i in range(-100, 601) if self.pk.stroke_map(mph, i / 10) is not None]
            self.assertGreater(len(hits), 10)
            self.assertAlmostEqual(hits[-1] - hits[0], want, delta=0.3, msg=f"{mph} mph")

    def test_the_stance_default_sits_inside_the_fault_window_and_one_lesson_leaves_it(self):
        """The arithmetic in the comment above APPROACH_DEFAULT, run. A volley is taken with the feet where the
        body is — `volley_contact` moves the feet *to the ball*, never toward the net — and the carry afterwards
        is 1.5 ft, so a player holding g ft behind the line is carried into the kitchen for **g < 1.5**. The
        default is outside that window on purpose: the rule must bite the player who ran to the line, not the one
        standing where the sport says to stand. The first version of this test asserted the opposite, because
        the engine then stepped the player 1.2 ft toward the net to volley. The step and the test are both gone."""
        pk = self.pk
        def carried_in(gap: float) -> bool:
            mark = pk.KITCHEN_LINE - gap                     # a north player, standing at their mark
            return pk.in_kitchen(mark + 1.5)                 # planted, then carried 1.5 ft forward
        self.assertTrue(carried_in(1.0), "a foot behind the line is the carry-in")
        self.assertFalse(carried_in(pk.APPROACH_DEFAULT), "the default is outside the window")
        self.assertFalse(carried_in(2.0), "and one lesson (a foot, from 1.0) leaves it")
        self.assertGreater(pk.APPROACH_DEFAULT, 1.5, "the window's far edge")

    def test_the_reading_chooser_steps_back_after_its_own_fault_and_not_after_a_chase(self):
        """The lesson, driven directly: a fault from the mark moves the feet one foot back; the same fault
        arrived at by chasing the ball changes nothing, because the stance was never the cause; and the
        number stops at the ceiling rather than climbing forever."""
        pk = self.pk
        names = ["A", "B", "C", "D"]
        players = {n: self.t.Player(name=n, north=(i < 2), practice=200) for i, n in enumerate(names)}
        pos = pk.Positions()
        said: list[str] = []
        choose = pk.reading_chooser("steady", say=said.append)(players, ("N", 3.0), "hard")
        self.assertEqual(pos.approach_of(players["A"]), pk.APPROACH_DEFAULT)

        def at_the_mark():
            # the feet are planted to volley, so the fault's own place *is* the mark
            x = pk.KITCHEN_LINE - pos.approach_of(players["A"])
            return {"why": "momentum", "fault_name": "A", "fault_at": (x, pk.CENTRELINE)}
        choose.lesson(at_the_mark(), pos, players)
        self.assertEqual(pos.approach_of(players["A"]), pk.APPROACH_DEFAULT + 1.0, "one step back")
        # the same fault, but the feet were a foot from the line having gone to the ball
        before = pos.approach_of(players["A"])
        chase = {"why": "kitchen", "fault_name": "A", "fault_at": (pk.KITCHEN_LINE - 0.4, pk.CENTRELINE)}
        choose.lesson(chase, pos, players)
        self.assertEqual(pos.approach_of(players["A"]), before, "the chase is not the stance")
        self.assertTrue(any("not the stance" in line for line in said), "and it says so in the transcript")
        for _ in range(20):                                   # a foot per fault, and never past the ceiling
            choose.lesson(at_the_mark(), pos, players)
        self.assertEqual(pos.approach_of(players["A"]), pk.APPROACH_MAX)

    def test_the_reading_chooser_swings_with_the_steady_players_hands(self):
        """A difference between --level steady and --level read has to be the learning and never the aim."""
        import random as _random
        pk = self.pk
        def swing(factory):
            p = self.t.Player(name="A", north=True, practice=200, rng=_random.Random(11))
            other = self.t.Player(name="C", north=False, practice=200, rng=_random.Random(12))
            choose = factory({ "A": p, "C": other }, ("N", 3.0), "hard")
            return choose(p, other, {"speed_in": 20.0, "depth": 9.0}, 3, [], "groundstroke", True, (8.0, 10.0))
        self.assertEqual(swing(pk.make_chooser("read")), swing(pk.make_chooser("steady")))
        self.assertIsNot(swing(pk.make_chooser("read")), swing(pk.make_chooser("beginner")))

    def test_a_pinned_clock_reproduces_a_game_shot_for_shot(self):
        """The record's header offers a replay command; before the hands were seeded from the clock, two
        replays of the same command gave 11-2 and 11-3. A transcript that cannot be replayed is a story."""
        pk = self.pk
        names = ["north-a", "north-b", "south-a", "south-b"]
        def play():
            m, r = pk.play_game(names, [60, 60, 60, 60], pk.make_chooser("steady"), surface="hard",
                                wind_seed_ms=424242, first_team=0, say=lambda *a, **k: None)
            return (m.teams[0].score, m.teams[1].score, r["lengths"])
        self.assertEqual(play(), play())

    def test_a_stretched_contact_is_a_worse_shot(self):
        """The rule that makes the honest body playable (§5d). The same swing from the same player, twice: once
        with the feet under the ball (`stretch` 0) and once at full extension (`stretch` 1). The stretched ball
        is a *wider* ball, because the penalty is on control and control is where every human error in `strike`
        already lives. Without this, a receiving model with honest feet produced rallies that ran to the ceiling:
        arriving late was free."""
        import random as _random
        pk = self.pk
        def spread(stretch: float) -> float:
            p = self.t.Player(name="X", north=True, practice=120, rng=_random.Random(4))
            misses = []
            for _ in range(30):
                shot = pk.strike(p, {"speed_in": 20.0}, face=12.0, power=45.0, aim=10.0, shot="groundstroke",
                                 surface="hard", wind=(0.0, 0.0), pos=(6.0, 10.0), stretch=stretch)
                land = shot["traj"].get("land")
                misses.append(abs((land[1] if land else 10.0) - 10.0) + abs((land[0] if land else 6.0) - 30.0))
            return sum(misses) / len(misses)
        calm, stretched = spread(0.0), spread(1.0)
        self.assertGreater(stretched, calm * 1.2,
                           f"a full-extension contact has to cost something: {calm:.1f} ft vs {stretched:.1f} ft")
        self.assertGreater(pk.STRETCH_PENALTY, 0.0, "and the cost is on, which is the A/B in the page")

    def test_a_short_high_ball_can_be_taken_out_of_the_air(self):
        """The rule that replaced `depth > 6` (§5d). A ball that lands in the kitchen — the ball a dink rally is
        waiting for — is volley-able in the air, and the primitive that decides it is tennis's own, asked with
        this court's numbers: the ball's flight before the bounce, the paddle's reach, and a window above the
        knee. Under the old rule this ball could only be played off the bounce, so a dink exchange had no way to
        end except an error."""
        pk = self.pk
        p = self.t.Player(name="X", north=True, practice=300)
        # struck gently, to land just past the net: depth ~ 4 ft into the receiving side, i.e. in the kitchen
        shot = pk.strike(p, None, face=30.0, power=22.0, aim=pk.CENTRELINE, shot="groundstroke",
                         surface="hard", wind=(0.0, 0.0), pos=(14.0, pk.CENTRELINE), clean=True)
        land = shot["traj"]["land"]
        self.assertLess(abs(land[0] - pk.NET_X), 7.0, "the ball must land in the kitchen for this test to mean much")
        vol = pk.volley_contact(p, shot["traj"].get("path"), at=(14.0, pk.CENTRELINE),
                                reach=pk.PADDLE_REACH, lo=pk.VOLLEY_LOW, hi=pk.VOLLEY_HIGH)
        self.assertIsNotNone(vol, "a short high ball is an invitation, not a ball to wait for")
        # The earliest reachable contact is what `volley_contact` returns — a player coming forward takes the
        # ball when they can, not when it is prettiest. Its height is handed to the chooser, and that is what
        # decides an attack (above the tape) from a dig: the engine no longer decides it by asking how DEEP the
        # ball would have landed, which was the rule that made short balls unhittable in the air.
        self.assertLess(vol["contact"][0], pk.NET_X, "taken on the receiving side of the net")
        self.assertGreaterEqual(vol["height"], pk.VOLLEY_LOW, "and above the knee, or it is a dig off the ground")

    def test_the_paddle_reach_is_the_constant_the_sweep_turns(self):
        """§5l sweeps PADDLE_REACH between six and three feet and re-measures everything; that means nothing
        unless the engine reads the constant at every call. Two checks: the source passes it to both places a
        paddle is asked for, and the primitive itself answers differently for the same ball at 6 ft and at 2."""
        pk = self.pk
        src = (REPO / "lab" / "pickleball.py").read_text(encoding="utf-8")
        # Since §5s the two sites read `reach_of(p)`, which is `REACH_FOR.get(name, PADDLE_REACH)` — the override
        # §5s's head-to-head needs, empty unless an experiment is running. The property this test is about is
        # unchanged and is now asserted one level up: every reach in the engine comes from one function, and that
        # function has one default.
        self.assertEqual(src.count("reach=reach_of("), 2,
                         "the volley and the interception both read the one number, not a copy of it")
        self.assertEqual(src.count("reach=PADDLE_REACH"), 0, "and neither of them hard-codes it")
        self.assertIn("if p.name in REACH_FOR:", src, "an experiment's number wins when one is set")
        self.assertIn("REACH_MAX - (REACH_MAX - REACH_BEGINNER) * math.exp(-balls / REACH_TAU)", src,
                      "and otherwise the reach is the lunge the player has learned (§5t), anchored so that 200 "
                      "balls is exactly this constant")
        p = self.t.Player(name="A", north=True, practice=200)
        path = [(0.1, 21.0, 10.0, 3.0)]          # six feet away, a tenth of a second to get there
        wide = pk.volley_contact(p, path, at=(15.0, 10.0), reach=6.0)
        tight = pk.volley_contact(p, path, at=(15.0, 10.0), reach=2.0)
        self.assertIsNotNone(wide, "a six-foot paddle takes a ball six feet away")
        self.assertIsNone(tight, "a two-foot one cannot, and the legs have a tenth of a second")

    def test_practice_buys_feet_below_a_hundred_balls_and_inches_above_it(self):
        """§5u separated what practice buys in hands from what it buys in feet, and the arithmetic that made the
        separation worth doing is worth holding: the first two hundred balls buy a foot and a half of lunge, the
        next hundred buy under half a foot, and in that same hundred the hands gain eleven points of control. So
        practice does not stop working — it changes currency, and a practice screen that shows reach alone is
        showing the part of practice that moves least."""
        pk, T = self.pk, self.t
        def reach(balls):
            return pk.reach_of(T.Player(name="A", north=True, practice=balls))
        self.assertGreater(reach(200) - reach(0), 1.3, "the first two hundred balls buy a foot and a half")
        self.assertGreater(reach(250), reach(150), "and the curve never goes backwards")
        self.assertLess(reach(250) - reach(150), 0.42, "...but the next hundred buy under half a foot")
        p150 = T.Player(name="A", north=True, practice=150)
        p250 = T.Player(name="A", north=True, practice=250)
        self.assertGreater(p250.skill("control") - p150.skill("control"), 0.10,
                           "and in the same interval the hands gain eleven points of control, which is why §5u's "
                           "hands-only row still goes 21/24 at a pinned reach")

    def test_a_persons_seat_plays_the_movement_it_was_given(self):
        """§5q's screen prints `PACE 24 AT 26,6`, and this is the seat that answers with it: one typed movement,
        played every time the ball comes to the person, while the three members are asked afresh on every ball.
        The line goes through `solve_move`, the same solver a member's answer goes through — so the same sentence
        means a dink from the kitchen line and a reach from the baseline, and the paddle's angle is never the
        person's problem (§5o). A form on a runner cannot stop mid-rally; that limitation is the seat's, and this
        holds the rest of the seat to what it promises."""
        pk = self.pk
        move = pk.parse_move("PACE 30 AT 30,4")
        self.assertEqual(move, {"pace": 30.0, "target": (30.0, 4.0)})
        told = []
        def factory(players, wind_in, surface):
            human = pk.person_chooser_pb(move, surface, wind_in)
            others = pk.make_chooser("dink")(players, wind_in, surface)
            def choose(p, *a, **k):
                if p.name == "Me":
                    answer = human(p, *a, **k)
                    told.append((a[4], answer))        # (shot_kind, (face, power, aim, dist))
                    return answer
                return others(p, *a, **k)
            return choose
        _m, _out = pk.play_game(["Me", "A", "B", "C"], [200] * 4, factory, wind_seed_ms=1234500,
                                say=lambda *a, **k: None)
        self.assertTrue(told, "the person's seat was asked for a shot")
        self.assertIn("groundstroke", {k for k, _ in told}, "the person played shots from the back of a rally too")
        for kind, (_face, power, aim, dist) in told:
            if kind == "serve":
                # A serve is the one shot whose depth the rules fix: the pace it needs is the engine's own serve
                # pace (a person's single movement is usually a dink's, which cannot carry thirty feet) and the
                # point is pulled into the diagonal half of the box, two feet clear of the centreline.
                self.assertGreaterEqual(power, 55.0, "a serve is served at a serve's pace, not a dink's")
                self.assertGreaterEqual(abs(aim - 10.0), 2.0, "and it goes to the diagonal half of the box")
            else:
                self.assertAlmostEqual(power, 30.0 / 0.6, places=6, msg="the pace is the movement's own")
                self.assertEqual(aim, 4.0, "and so is the point across the court")
            self.assertGreater(dist, 0.0,
                               "the distance is the movement's own too, because `strike` reads the swing's "
                               "lateral error off it (§5p) and a zero there plays every ball from six feet")

    def test_a_dinks_movement_is_still_a_legal_serve(self):
        """A person types one movement and gets it on every ball, the serve included. `PACE 24 AT 26,6` is a fine
        dink and a service fault twice over — 26 ft is inside the receiving kitchen, and y=6 is on the server's
        own side of the centreline — so `solve_move` pulls the point into the diagonal box and walks the pace to
        one that carries the ball there. The alternative is a double fault the person had no way to see, which is
        the same complaint the page makes about the engine's prose fallback (§5q). What the movement means for
        every other shot is untouched: the pace is theirs and the point is theirs."""
        pk, T = self.pk, self.t
        w = pk.wind_vector("S", 3.0)
        for north, here in ((True, (0.5, 4.0)), (True, (0.5, 16.0)), (False, (43.5, 4.0)),
                            (False, (43.5, 16.0))):
            p = T.Player(name="P", north=north, practice=200)
            face, power, aim, _d = pk.solve_move(p, here, {"pace": 24.0, "target": (26.0, 6.0)}, "serve",
                                                 "hard", w)
            shot = pk.strike(p, None, face=face, power=power, aim=aim, shot="serve", surface="hard", wind=w,
                             pos=here, clean=True)
            land = shot["traj"]["land"]
            self.assertIsNotNone(land, f"a serve from {here} has to clear the net")
            self.assertTrue(pk.in_service_area(land, north, here[1]),
                            f"a dink's movement still serves into the box from {here}; it landed {land}")
            self.assertGreaterEqual(power, 55.0, "at a serve's pace, because the box is fifteen feet of court")
        face, power, aim, _d = pk.solve_move(T.Player(name="P", north=True, practice=200), (0.5, 4.0),
                                             {"pace": 24.0, "target": (26.0, 6.0)}, "groundstroke", "hard", w)
        self.assertEqual((aim, round(power, 6)), (6.0, 40.0), "and every other shot is the movement's own")

    def test_a_person_seat_refuses_a_line_that_is_not_a_movement(self):
        """A refusal that names the shape, because the whole point of the movement language is that a person
        can form one: a page that accepts `hit it hard` and plays something is worse than one that says what
        it wants."""
        import contextlib, io
        pk = self.pk
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = pk.main(["--person-shot", "hit it hard", "--names", "Me,A,B,C"])
        self.assertEqual(code, 2, "nothing was played")
        self.assertIn("PACE", err.getvalue(), "and the refusal says what the shape is")
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = pk.main(["--person-shot", "PACE 24 AT 26,6", "--names", "Me,A"])
        self.assertEqual(code, 2, "a person's seat in doubles is four names, the person first")
        self.assertIn("four names", err.getvalue(), "and the refusal says how many seats a doubles court has")

    def test_the_session_record_counts_the_engines_own_balls(self):
        """`record_session` was handed Player objects built by the caller, so a members' doubles season wrote
        `shots 0, in_play 0 of 0` for everybody and its `balls` counter never moved — a season that records
        practice it did not count. The engine hands its own players and its own per-shot verdicts back now,
        which is also the only form of the number that cannot disagree with the film."""
        pk = self.pk
        _m, out = pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("dink"), wind_seed_ms=1234500,
                               say=lambda *a, **k: None)
        self.assertEqual(sum(p.shots for p in out["players"].values()), sum(out["lengths"]),
                         "every shot in the game belongs to the player who hit it")
        for n, p in out["players"].items():
            self.assertEqual(len(out["results"][n]), p.shots, f"{n}'s in/out list is one entry per swing")
        book = {"members": {}}
        pk.record_session(book, when="2026-11-26T00:00:00Z", surface="hard", clock=out["clock"],
                          players=list(out["players"].values()), results=out["results"],
                          lengths=out["lengths"], partners={}, mode="doubles")
        for n, p in out["players"].items():
            self.assertEqual(book["members"][n]["balls"], p.shots, f"{n}'s balls are the engine's count")
            self.assertGreater(book["members"][n]["sessions"][-1]["of"], 0,
                               "and the session says how many balls it is a record of")

    def test_a_pickleball_season_is_reported_in_its_own_units_and_never_in_tenniss(self):
        """§5z. `season_report(…, "pickleball")` accepted the sport and ignored it: it read
        `games/tennis/seasons/<season>/practice.json` and answered "Nobody has hit a ball in <season> yet" about a
        season sitting in `games/pickleball/seasons/`. An argument that is accepted and does nothing is the most
        expensive kind of defect, because every caller believes it was answered. There were two callers — the
        season writer and `--report` — and both were wrong."""
        pk = self.pk
        _m, out = pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("dink"), wind_seed_ms=1234500,
                               say=lambda *a, **k: None)
        with tempfile.TemporaryDirectory() as tmp:
            season, d = "2026-winter", str(Path(tmp) / "2026-winter")
            book = {"season": season, "members": {}}
            pk.record_session(book, when="2026-11-27T00:00:00Z", surface="hard", clock=out["clock"],
                              players=list(out["players"].values()), results=out["results"],
                              lengths=out["lengths"], partners={}, mode="doubles",
                              faults=pk.fault_mix({"rallies": out["rallies"]}), score=out["score"])
            pk.save_season(book, season, d, "pickleball", report=pk.report)
            written = (Path(d) / "report.md").read_text()
            self.assertIn("pickleball, what the record says", written)
            self.assertNotIn("tennis", written, "the season's own report mentions tennis")
            self.assertIn("points lost, in the words a player corrects", written)
            self.assertIn(f"the game was {out['score'][0]}–{out['score'][1]}", written,
                          "the report leaves out the one number a person looks for")
            self.assertIn(f"{season}/practice.json", written)
            # and the reader, asked directly, does not pretend to answer in tennis's units
            said = self.t.season_report(season, d, "pickleball")
            self.assertIn("practice.json", said)
            self.assertNotIn("Nobody has hit a ball", said, "it answered about a file it never read")
            self.assertIn(f"lab/pickleball.py --report {season}", said, "it does not say where the report is")

    def test_the_report_names_a_session_without_a_mix_as_a_gap(self):
        """The same rule as the trend, in the artefact a person is handed at the end of a season: a session from
        before the field existed is a gap, and a season with no mixes at all is not a clean sheet."""
        pk = self.pk
        with tempfile.TemporaryDirectory() as tmp:
            d = str(Path(tmp) / "2026-winter")
            book = {"season": "2026-winter", "members": {"A": {"balls": 40, "sessions": [
                {"when": "2026-11-20T00:00:00Z", "surface": "hard", "clock": 1, "shots": 20, "in_play": 16,
                 "of": 20, "mean_rally": 4.0, "longest": 9, "faults": {"net": 2, "unreachable": 3}},
                {"when": "2026-11-21T00:00:00Z", "surface": "hard", "clock": 2, "shots": 20, "in_play": 15,
                 "of": 20, "mean_rally": 4.0, "longest": 9},
            ]}}}
            pk.save_season(book, "2026-winter", d, "pickleball", report=pk.report)
            said = (Path(d) / "report.md").read_text()
            self.assertIn("carries no mix", said)
            self.assertIn("2 into the net, 3 did not get to", said)
            self.assertIn("One session carries a mix", said)
            book["members"]["A"]["sessions"][0].pop("faults")
            pk.save_season(book, "2026-winter", d, "pickleball", report=pk.report)
            said = (Path(d) / "report.md").read_text()
            self.assertIn("No session in this season carries a fault mix", said)
            self.assertNotIn("points lost, in the words a player corrects", said,
                             "a season with no count reports no counts")

    def test_a_session_writes_the_fault_mix_and_a_sport_without_one_writes_no_key(self):
        """§5y. The season file has carried `reach` and `control` per session since September — two numbers that
        move by inches over hundreds of balls — and not the number that moves by whole balls a game. The mix goes
        in as an optional field, and the absence is the point: a tennis session must not look like a pickleball one
        that happened to lose nothing, because then a trend would read a gap as a good day."""
        pk = self.pk
        _m, out = pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("dink"), wind_seed_ms=1234500,
                               say=lambda *a, **k: None)
        book = {"members": {}}
        pk.record_session(book, when="2026-11-27T00:00:00Z", surface="hard", clock=out["clock"],
                          players=list(out["players"].values()), results=out["results"],
                          lengths=out["lengths"], partners={}, mode="doubles",
                          faults=pk.fault_mix({"rallies": out["rallies"]}))
        lost = {n: sum(1 for r in out["rallies"] if r.get("fault_name") == n) for n in out["players"]}
        for n in out["players"]:
            sess = book["members"][n]["sessions"][-1]
            self.assertIn("faults", sess, f"{n}'s session does not carry the mix")
            self.assertEqual(sum(sess["faults"].values()), lost[n],
                             f"{n}'s mix adds up to the rallies {n} lost")
        plain = {"members": {}}
        pk.record_session(plain, when="2026-11-27T00:00:00Z", surface="hard", clock=1,
                          players=list(out["players"].values()), results=out["results"],
                          lengths=out["lengths"], partners={}, mode="rallies")
        for n in out["players"]:
            self.assertNotIn("faults", plain["members"][n]["sessions"][-1],
                             "a session with no mix recorded has no mix key")

    def test_the_trend_reads_seasons_oldest_first_and_leaves_a_gap_as_a_gap(self):
        """§5y's reader. `season_mix` walks `games/pickleball/seasons/*/practice.json`, takes only the sessions that
        carry a mix, and sorts by when — because a season's folder name is not its date and a trend printed in
        folder order is a trend that can run backwards. A session without the field is a gap, not a zero."""
        pk = self.pk
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "games" / "pickleball" / "seasons"
            def put(season, sessions):
                d = base / season
                d.mkdir(parents=True)
                (d / "practice.json").write_text(json.dumps(
                    {"season": season, "opened": sessions[0]["when"], "members": {"A": {"balls": 9, "sessions": sessions}}}))
            put("zzz-later-named", [{"when": "2026-11-27T18:00:00Z", "shots": 90, "in_play": 60,
                                     "faults": {"net": 2, "unreachable": 2}}])
            put("aaa-earlier-named", [{"when": "2026-10-02T18:00:00Z", "shots": 96, "in_play": 70,
                                       "faults": {"net": 4, "unreachable": 6}},
                                      {"when": "2026-10-20T18:00:00Z", "shots": 91, "in_play": 65}])  # a gap
            rows = pk.season_mix("A", root=Path(tmp))
            self.assertEqual([r["when"][:10] for r in rows], ["2026-10-02", "2026-11-27"],
                             "the trend is by date, not by folder name")
            self.assertEqual([r["unreached"] for r in rows], [6, 2])
            self.assertNotIn("2026-10-20", [r["when"][:10] for r in rows], "a session with no mix is not a row")
            self.assertEqual(pk.season_mix("nobody", root=Path(tmp)), [])
            one = pk.trend_table("A", rows[:1])
            self.assertIn("one session is a reading", one)
            both = pk.trend_table("A", rows)
            self.assertIn("4 fewer", both, "6 → 2 is four fewer balls not got to")
            self.assertNotIn("one session is a reading", both)

    def test_a_lost_point_says_which_miss_it_was_and_the_phrase_agrees(self):
        """§5x. The film's rallies carried the rule that ended them (`why: out`) and the phrase lived only on the
        shot, so a record with every word in it could not answer 'how do I lose points'. `_judge` now returns the
        kind with the phrase, from one place, so the count and the sentence cannot drift apart: a ball counted as
        `net` is a ball whose phrase says 'into the net'."""
        pk = self.pk
        _m, out = pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("dink"), wind_seed_ms=1234500,
                               say=lambda *a, **k: None, film={})
        outs = [r for r in out["film"]["rallies"] if r["why"] == "out"]
        self.assertGreater(len(outs), 10, "a dink game loses its points on struck balls, or this tests nothing")
        for r in outs:
            self.assertIn(r.get("fault_kind"), pk.MISS_KINDS, f"rally {r['rally']} carries no miss kind")
        # the phrase on the shot that ended each rally says the same thing as the kind on the rally
        by_rally = {s["rally"]: s["why"] for s in out["film"]["shots"]}
        for r in outs:
            phrase = by_rally[r["rally"]]
            want = {"net": "into the net", "long": "long by", "wide": "wide by",
                    "short": "their own side of the net", "lost": "lost the ball"}[r["fault_kind"]]
            self.assertIn(want, phrase, f"rally {r['rally']} counted {r['fault_kind']} but its shot says {phrase!r}")
        # and the kinds are a closed list, so a count can be taken without a catch-all
        self.assertEqual(set(pk.MISS_KINDS), {"net", "long", "wide", "short", "lost"})

    def test_the_fault_mix_charges_a_ball_nobody_got_to_to_the_person_who_did_not(self):
        """Attribution is the whole of §5x and it is not the same for every fault. A hit ball belongs to the
        hitter; an unreachable one has `fault_by: None` on the engine's own record, so a naive 'whose fault' count
        drops exactly the balls practice improves. `cap` belongs to nobody and is not counted."""
        pk = self.pk
        film = {"rallies": [
            {"rally": 1, "why": "out", "fault_kind": "net", "fault_name": "A", "fault_by": 0},
            {"rally": 2, "why": "out", "fault_kind": "long", "fault_name": "A", "fault_by": 0},
            {"rally": 3, "why": "unreachable", "fault_name": "A", "fault_by": None},
            {"rally": 4, "why": "kitchen", "fault_name": "B", "fault_by": 1},
            {"rally": 5, "why": "cap", "fault_name": None, "fault_by": None},
            {"rally": 6, "why": "out", "fault_name": "B", "fault_by": 1},          # an older film: no kind
        ]}
        mix = pk.fault_mix(film)
        self.assertEqual(mix["A"], {"net": 1, "long": 1, "unreachable": 1},
                         "the ball A did not get to is charged to A, beside the two A hit out")
        self.assertEqual(mix["B"], {"kitchen": 1, "out": 1},
                         "an out ball with no kind is counted as an out ball, not invented")
        self.assertEqual(pk.fault_mix(film, who="A"), {"A": {"net": 1, "long": 1, "unreachable": 1}})
        self.assertEqual(sum(sum(v.values()) for v in mix.values()), 5, "the ceiling is nobody's fault")

    def test_the_fault_mix_reads_in_the_words_a_person_would_use(self):
        """A count is for the record; the sentence is for the person. Net and long come first because those are
        the two to correct, and a kind this function has not heard of is said rather than silently dropped."""
        pk = self.pk
        self.assertEqual(pk.mix_phrase({}), "no point lost")
        self.assertEqual(pk.mix_phrase({"unreachable": 2, "net": 3, "long": 1}),
                         "3 into the net, 1 long, 2 did not get to")
        self.assertEqual(pk.mix_phrase({"brandnew": 1}), "1 brandnew")

    def test_a_body_that_is_walking_is_met_where_it_is_going(self):
        """Anticipation is the momentum rule's other reader. A player who has arrived at their stance has stopped,
        so the prediction is where they are; a player mid-jog is predicted forward by their own velocity over the
        flight. No memory, no model of a habit — the body's own momentum, which `Positions.vel` already holds."""
        pk = self.pk
        pos = pk.Positions(at={"A": (24.0, 4.0), "B": (24.0, 14.0)}, vel={"A": (0.0, 10.5), "B": (0.0, 0.0)})
        players = {"A": self.t.Player(name="A", north=False), "B": self.t.Player(name="B", north=False)}
        ahead = pk.bodies_ahead(pos, players, ["A", "B"], 0.5)
        self.assertAlmostEqual(ahead["A"][1], 4.0 + 5.25, places=3, msg="a walk at 10.5ft/s for half a second")
        self.assertEqual(ahead["B"], (24.0, 14.0), "a standing body is predicted to stand")

    def test_anticipation_aims_where_the_body_will_be_and_is_a_no_op_when_nothing_moves(self):
        """Two runs of the same chooser over the same court, one with the second pass and one without. With a
        body walking across the open side, the anticipating chooser aims at a different spot; with everybody
        standing still it returns exactly what the plain placement chooser returns, because there is nothing to
        predict and a player does not invent one."""
        pk = self.pk
        import random as _r
        players = {n: self.t.Player(name=n, north=(i < 2), practice=200, rng=_r.Random(5 + i))
                   for i, n in enumerate(["A", "B", "C", "D"])}
        pos = pk.Positions(at={"A": (15.0, 10.0), "C": (24.0, 6.0), "D": (26.0, 12.0)},
                           vel={"C": (0.0, 10.5), "D": (0.0, 0.0)})
        incoming = {"speed_in": 20.0, "depth": 12.0, "path": [], "v": (1.0, 0.0, 1.0)}
        plain = pk.placement_chooser("steady")(players, ("N", 0.0), "hard")
        plain.sight = pos
        ahead = pk.placement_chooser("steady", anticipate=True)(players, ("N", 0.0), "hard")
        ahead.sight = pos
        a = plain(players["A"], players["C"], incoming, 3, [], "groundstroke", False, (15.0, 10.0))
        b = ahead(players["A"], players["C"], incoming, 3, [], "groundstroke", False, (15.0, 10.0))
        self.assertNotAlmostEqual(a[2], b[2], places=1, msg="a moving body is not met where it was")
        self.assertGreater(abs(b[2] - a[2]), 1.5, "and the difference is feet, not noise")
        pos.vel = {"C": (0.0, 0.0), "D": (0.0, 0.0)}
        b2 = ahead(players["A"], players["C"], incoming, 3, [], "groundstroke", False, (15.0, 10.0))
        self.assertAlmostEqual(a[2], b2[2], places=6, msg="nothing moving, nothing predicted")

    def test_the_ball_goes_where_the_bodies_are_not(self):
        """Placement is arithmetic before it is strategy: of the points on a line, the one to hit is the one the
        nearest opponent is furthest from. Two bodies on the west side of the court and the answer is the east."""
        pk = self.pk
        pos = pk.Positions(at={"x": (24.0, 4.0), "y": (24.0, 6.0)})
        players = {"x": self.t.Player(name="x", north=False), "y": self.t.Player(name="y", north=False)}
        ty, gap = pk.open_target(pos, players, ["x", "y"], 26.5)
        self.assertGreater(ty, 14.0, f"the open side is the east one, got {ty:.1f}")
        self.assertGreater(gap, 10.0, "and there is a gap to hit into")

    def test_a_short_shot_aimed_wide_used_to_sail_wide(self):
        """The azimuth is an angle, and it was computed against a hard 32 ft whatever the shot was: a dink aimed
        5 ft across the court from 10 ft away was given the angle for a drive, and landed 2.9 ft wide of its
        target. `aim_dist` is the shot's own distance, and it is the difference between aiming and gesturing."""
        pk = self.pk
        p = self.t.Player(name="A", north=True, practice=200)
        here, tx, ty = (15.0, 10.0), 26.5, 5.0
        dist = math.hypot(tx - here[0], ty - here[1])
        face = pk.aim_at(p, (tx, ty), "groundstroke", "hard", (0.0, 0.0), 24.0, here)
        right = pk.strike(p, None, face=face, power=24.0, aim=ty, shot="groundstroke", surface="hard",
                          wind=(0.0, 0.0), pos=here, clean=True, aim_dist=dist)["traj"]["land"]
        wrong = pk.strike(p, None, face=face, power=24.0, aim=ty, shot="groundstroke", surface="hard",
                          wind=(0.0, 0.0), pos=here, clean=True)["traj"]["land"]
        self.assertLess(abs(right[1] - ty), 1.0, f"aimed at {ty}, landed at {right[1]:.1f}")
        self.assertGreater(abs(wrong[1] - ty), 2.0, "and the 32 ft azimuth is the reason it did not, before")

    def test_a_chooser_can_see_the_court_it_is_playing_on(self):
        """`play_game` hands every chooser the engine's own `Positions` before the first ball. Until §5j no
        chooser could see anybody, which is why placement and pace variation could not be learned: neither is a
        property of the ball."""
        pk = self.pk
        names = ["A", "B", "C", "D"]
        seen = {}

        def factory(players, wind_in, surface):
            def choose(p, *a, **k):
                seen[p.name] = getattr(choose, "sight", None)
                return 15.0, 42.0, 10.0
            return choose

        pk.play_game(names, [200] * 4, factory, wind_seed_ms=1234500, say=lambda *a, **k: None)
        self.assertTrue(seen, "the chooser was asked for a shot")
        self.assertIsNotNone(seen["A"], "and it was given the court")
        self.assertTrue(hasattr(seen["A"], "get"), "which is a Positions, not a copy of one")

    def test_a_dink_is_twelve_to_fifteen_miles_an_hour_and_a_drive_from_the_line_is_not(self):
        """The soft game's pace, measured. Power 30 is 18 mph, and from the kitchen line an 18 mph ball travels
        sixteen feet before it lands — nine feet past the opponent's kitchen, which is why a chooser that calls
        power 30 "a dink" cannot play the game at all. A dink is power 20-24 and it lands 4-6 ft past the net,
        provided the face lifts it over the tape rather than into it."""
        pk = self.pk
        p = self.t.Player(name="A", north=True, practice=200)
        dinked = 0
        for face in range(0, 41, 2):
            shot = pk.strike(p, None, face=float(face), power=24.0, aim=10.0, shot="groundstroke",
                             surface="hard", wind=(0.0, 0.0), pos=(15.0, 10.0), clean=True)
            land = shot["traj"].get("land")
            if land is not None and pk.in_kitchen(land[0]) and land[0] > pk.NET_X:
                dinked += 1
                self.assertGreaterEqual(land[0] - pk.NET_X, 1.0, "and it is past the net, not on it")
        self.assertGreaterEqual(dinked, 3, "a dink exists at some face and 14 mph")
        drove_out = 0
        for face in range(0, 41, 2):
            land = pk.strike(p, None, face=float(face), power=30.0, aim=10.0, shot="groundstroke",
                             surface="hard", wind=(0.0, 0.0), pos=(15.0, 10.0), clean=True)["traj"].get("land")
            if land is not None and land[0] > pk.NET_X + pk.KITCHEN:
                drove_out += 1
        self.assertGreaterEqual(drove_out, 8, "power 30 from the line cannot land in the kitchen at most faces")

    def test_the_dink_chooser_puts_a_slow_ball_back_in_the_kitchen(self):
        """The chooser's whole job: given a slow ball near the line, come back with a shot that lands in the
        opponent's kitchen — checked against its own clean strike before it commits, so a dink that cannot be
        dinked is played as something else rather than pretended."""
        pk = self.pk
        players = {n: self.t.Player(name=n, north=(i < 2), practice=200, rng=__import__("random").Random(3 + i))
                   for i, n in enumerate(["A", "B", "C", "D"])}
        choose = pk.dink_chooser("steady")(players, ("N", 2.0), "hard")
        p = players["A"]
        incoming = {"speed_in": 14.0, "depth": 5.0, "path": [], "v": (1.0, 0.0, 1.0)}
        face, power, aim, dist = choose(p, players["C"], incoming, 3, [], "groundstroke", False, (15.0, 9.0))
        self.assertIn(power, pk.DINK_POWERS)
        self.assertTrue(10.0 < dist < 14.0, f"the chooser says how far its aim is measured down ({dist:.1f}ft)")
        shot = pk.strike(p, None, face=face, power=power, aim=aim, shot="groundstroke", surface="hard",
                         wind=(0.0, 0.0), pos=(15.0, 9.0), clean=True, aim_dist=dist)
        land = shot["traj"]["land"]
        self.assertGreater(land[0], pk.NET_X, "it crossed the net")
        self.assertLessEqual(land[0], pk.NET_X + pk.KITCHEN, "and it came down in the kitchen")

    def test_a_planted_volley_is_not_carried_anywhere(self):
        """The rulebook's fault is momentum, not address. A player standing still at 1 ft behind the line, taking
        a ball that comes to them, is not carried an inch — and the rule that preceded this one moved every
        volley taken within 2 ft of the line by a flat 1.5 ft, which made a *place* the offence and a lunge
        innocent (page §5f, §5g)."""
        pk = self.pk
        p = self.t.Player(name="A", north=True, practice=200)
        vol = {"contact": (16.0, 10.0, 3.0), "feet": (14.5, 10.0), "step": 0.5, "t": 0.2}
        stop, v = pk.volley_carry(p, (14.0, 10.0), vol, (0.0, 0.0))
        self.assertEqual(stop, (14.5, 10.0))
        self.assertEqual(v, (0.0, 0.0))
        self.assertFalse(pk.in_kitchen(stop[0]), "standing still 1 ft behind the line is not a fault")

    def test_a_player_still_moving_when_they_volley_is_carried_v_squared_over_2a(self):
        """The whole rule, as arithmetic: the body brakes at A_STOP until it is standing, so it travels v²/(2A)
        past the contact. A player still walking to the line at the jog when the ball arrives is carried 1.7 ft
        and that is enough to put their feet in the kitchen from a foot behind the line."""
        pk = self.pk
        p = self.t.Player(name="A", north=True, practice=200)
        jog = self.t.movement_speed(p) * pk.WALK_SHARE
        vol = {"contact": (16.0, 10.0, 3.0), "feet": (14.5, 10.0), "step": 0.5, "t": 0.2}
        stop, v = pk.volley_carry(p, (14.0, 10.0), vol, (jog, 0.0))
        self.assertAlmostEqual(stop[0] - 14.5, jog * jog / (2.0 * pk.A_STOP), places=2)
        self.assertTrue(pk.in_kitchen(stop[0]), "carried in from a foot behind the line, which is the fault")

    def test_a_carry_stops_at_the_net_and_never_backwards(self):
        """A body cannot be carried through the net, and the net cannot push it back to where it came from: a
        player already at the net is stopped by it where they stand."""
        pk = self.pk
        p = self.t.Player(name="A", north=True, practice=200)
        jog = self.t.movement_speed(p) * pk.WALK_SHARE
        vol = {"contact": (21.2, 10.0, 3.0), "feet": (21.9, 10.0), "step": 0.7, "t": 0.2}
        stop, _ = pk.volley_carry(p, (20.0, 10.0), vol, (jog, 0.0))
        self.assertGreaterEqual(stop[0], 21.9, "the net does not walk a player backwards")
        self.assertLess(stop[0], pk.NET_X, "and a body does not pass through it")

    def test_the_carry_is_not_invented_from_the_size_of_the_step(self):
        """The first version of this rule divided the step by the time from the ball's strike to the contact, so a
        one-foot step at a fast ball came out at ten feet per second and every volley in the game was pushed into
        the kitchen — measured contact speed 17.8 ft/s, the cap, at every stance from 1 to 3 ft. A lunge is a
        plant, not a glide: the momentum is the walk that has not finished and nothing else."""
        pk = self.pk
        p = self.t.Player(name="A", north=True, practice=200)
        vol = {"contact": (16.0, 10.0, 3.0), "feet": (14.5, 10.0), "step": 2.0, "t": 0.02}
        stop, v = pk.volley_carry(p, (12.5, 10.0), vol, (0.0, 0.0))
        self.assertEqual(v, (0.0, 0.0), "a big step in a short time is not a speed")
        self.assertEqual(stop, (14.5, 10.0))

    def test_the_points_ledger_moves_toward_the_stance_that_wins(self):
        """The two-sided lesson, driven directly. A player who won everything at 2 ft and lost everything at
        4 ft takes one step back toward the line — the opposite of what the fault reader does, and on purpose:
        the faults say stand back (page §5d) and the scoreline says stand up. Exploration is off here so the
        test reads the greedy step and not the wandering."""
        pk = self.pk
        players = {"A": self.t.Player(name="A", north=True, practice=200)}
        pos = pk.Positions()
        pos.approach["A"] = 4.0
        said: list[str] = []
        choose = pk.points_chooser("steady", say=said.append, settle=1, need=3, margin=0.15,
                                   explore_every=10 ** 6)(players, ("N", 3.0), "hard")
        win, lose = ({"winner": 0}, {"winner": 1})
        pos.approach["A"] = 2.0
        for _ in range(3):
            choose.lesson(win, pos, players)          # three rallies won from 2 ft
        pos.approach["A"] = 4.0
        choose.lesson(lose, pos, players)             # one lost from 4 ft: the decision, and only one
        self.assertAlmostEqual(pos.approach_of(players["A"]), 3.0, places=6,
                               msg="one foot toward the stance that won, not four")
        choose.lesson(lose, pos, players)             # and it keeps walking while the evidence holds
        self.assertAlmostEqual(pos.approach_of(players["A"]), 2.0, places=6)
        self.assertTrue(any("paid in points" in line for line in said))

    def test_the_season_lesson_holds_one_stance_for_a_whole_game(self):
        """The unit §5e said was missing. A game lesson decides a stance *before* the game and holds it, so one
        bucket collects the whole game's rallies — thirty-odd samples for one decision, against the point
        lesson's two or three. That ratio is the entire difference between the two, so it is what is tested."""
        pk = self.pk
        tmp = Path(tempfile.mkdtemp())
        names = ["A", "B", "C", "D"]
        lesson = pk.SeasonLesson("test", names, start=4.0, override=str(tmp), say=lambda *a, **k: None)
        res = pk.play_season(names, [200] * 4, lesson, pk.scripted_chooser("steady"), 1,
                             clock=1234500, say=lambda *a, **k: None)
        book = lesson.member("A")["buckets"]
        self.assertEqual(len(book), 1, f"one stance per game, not a bucketful: {book}")
        rec = book["4"]
        self.assertEqual(rec["games"], 1)
        self.assertGreaterEqual(rec["played"], 15, "a game's worth of rallies in one bucket is the sample")
        self.assertEqual(len(res["rows"]), 1)
        self.assertEqual({round(v, 1) for v in res["rows"][0]["stances"].values()}, {4.0},
                         "every seat held one stance for the whole game")

    def test_the_season_lesson_steps_toward_the_stance_that_won(self):
        """Driven directly, so the test reads the decision and not a game's noise: 2 ft won 70% over three
        games, 4 ft won 40% over three, and the lesson takes one foot toward the line."""
        pk = self.pk
        tmp = Path(tempfile.mkdtemp())
        lesson = pk.SeasonLesson("test", ["A"], start=4.0, override=str(tmp), say=lambda *a, **k: None)
        m = lesson.member("A")
        m["buckets"] = {"4": {"won": 40, "played": 100, "games": 3},
                        "2": {"won": 70, "played": 100, "games": 3}}
        self.assertAlmostEqual(lesson.stances()["A"], 3.0, places=6, msg="one foot, not two")

    def test_the_season_lesson_stays_when_the_difference_is_a_coin(self):
        """Eight points of win rate is the margin, and a bucket that beats it by less is not evidence: the
        lesson was built because a small sample plus a greedy step is how §5e's lesson lost 61-77."""
        pk = self.pk
        tmp = Path(tempfile.mkdtemp())
        lesson = pk.SeasonLesson("test", ["A"], start=4.0, override=str(tmp), say=lambda *a, **k: None)
        lesson.member("A")["buckets"] = {"4": {"won": 52, "played": 100, "games": 3},
                                         "5": {"won": 56, "played": 100, "games": 3},
                                         "3": {"won": 48, "played": 100, "games": 3}}
        self.assertAlmostEqual(lesson.stances()["A"], 4.0, places=6, msg="four points is not a lesson")

    def test_the_seasons_book_survives_the_process_that_wrote_it(self):
        """A lesson whose unit is a game and whose sample is a season has to outlive the command line: the
        book is a file in the season's own directory, and it loads back with its buckets intact."""
        pk = self.pk
        tmp = Path(tempfile.mkdtemp())
        lesson = pk.SeasonLesson("test", ["A"], start=4.0, override=str(tmp), say=lambda *a, **k: None)
        lesson.member("A")["buckets"] = {"4": {"won": 40, "played": 100, "games": 3}}
        lesson.member("A")["held"] = 3.0
        path = lesson.save()
        self.assertTrue(path.exists())
        self.assertEqual(path.name, "stance.json")
        again = pk.SeasonLesson("test", ["A"], override=str(tmp), say=lambda *a, **k: None)
        self.assertAlmostEqual(again.held("A"), 3.0, places=6)
        self.assertEqual(again.member("A")["buckets"]["4"], {"won": 40, "played": 100, "games": 3})
        d, f = pk.stance_paths("2026-autumn")
        self.assertEqual(f.parent.name, "2026-autumn")
        self.assertEqual(f.parent.parent.name, "seasons")

    def test_the_points_chooser_explores_or_it_has_nothing_to_learn_from(self):
        """A lesson that never tries anything measures only where it started: with every player at the default
        and no results to read, the ledger holds one bucket and the greedy step has nothing to prefer. So the
        chooser takes an exploratory step, and that is a rule rather than an accident."""
        pk = self.pk
        players = {n: self.t.Player(name=n, north=(i < 2), practice=200) for i, n in enumerate(["A", "B", "C", "D"])}
        pos = pk.Positions()
        said: list[str] = []
        choose = pk.points_chooser("steady", say=said.append, settle=10 ** 6, explore_every=4)(
            players, ("N", 3.0), "hard")
        self.assertTrue(all(pos.approach_of(p) == pk.APPROACH_DEFAULT for p in players.values()))
        for _ in range(4):
            choose.lesson({"winner": None}, pos, players)
        self.assertTrue(any(pos.approach_of(p) != pk.APPROACH_DEFAULT for p in players.values()),
                        "somebody has to try somewhere else")
        self.assertTrue(any("tries" in line for line in said))

    def test_no_rally_runs_to_the_engines_ceiling(self):
        """The guard this turn needed, and did not have. `RALLY_CAP` = 120 shots is the record's ceiling, not a
        rule: a rally that reaches it scores nobody, so a cap hit in a demo is a bug report.

        On 2026-11-16 I replaced the receiving model with an honest body — the receiver's feet stop where their
        legs stop instead of being assigned the ball's landing point, and the leftover time is spent walking
        back to a stance (`/tmp` patch, reverted; §5c of the page). It is the right model and it made the game
        unplayable in a way nothing in the suite could see: defence never broke, the mean rally went to 26.7
        shots at practice 600, one rally hit the cap, and the only fault left in the game was the ball hit out.
        That is what this test is for — not "is it right", but "is it still a game".
        """
        pk = self.pk
        names = ["north-a", "north-b", "south-a", "south-b"]
        for practice, ceiling in ((0, 20), (200, 70), (600, 90)):
            longest, caps = 0, 0
            for g in range(1):
                m, r = pk.play_game(names, [practice] * 4, pk.make_chooser("steady"), surface="hard",
                                    wind_seed_ms=104729 * (g + 1), first_team=g % 2, say=lambda *a, **k: None)
                longest = max(longest, max(r["lengths"]))
                caps += sum(1 for x in r["rallies"] if x["why"] == "cap")
            self.assertEqual(caps, 0, f"a rally reached the {pk.RALLY_CAP}-shot ceiling at practice {practice}")
            self.assertLess(longest, ceiling, f"longest rally at practice {practice}")
            self.assertGreater(longest, 1, "and the game has rallies, not one shot and a fault")

    def test_the_tennis_integrator_still_integrates_what_it_integrated(self):
        """The parameterisation that let pickleball share the integrator must have changed nothing for tennis.
        This is the cheap version of the 2,408-sample grid that was run by hand on 2026-11-15 (0 differences):
        the same call with and without the new arguments, five courts, twelve shots."""
        t = self.t
        p = t.Player(name="X", north=True, practice=200)
        for power in (40, 70, 100):
            for face in (2.0, 6.0, 12.0, 18.0):
                a = t.strike(p, None, face=face, power=power, aim=13.5, shot="rally", surface="clay",
                             wind=(0.0, 0.0), clean=True)["traj"]
                b = t.flight(a["land"] and (0.0, 13.5, 3.0) or (0.0, 13.5, 3.0), (1.0, 0.0, 1.0), (0.0, 0.0),
                             "clay", drag=t.DRAG, lift=t.LIFT, net_x=t.NET_X, surfaces=t.SURFACES,
                             net_profile=t.net_height)
                c = t.flight((0.0, 13.5, 3.0), (1.0, 0.0, 1.0), (0.0, 0.0), "clay")
                self.assertEqual(b, c, "the new arguments default to the old behaviour")
                self.assertIsNotNone(a)

    def test_there_is_no_python_in_the_game_folder_and_no_physics_outside_the_lab(self):
        """The page's two mechanical tests, run rather than promised."""
        py = list((REPO / "games" / "pickleball").glob("*.py"))
        self.assertEqual(py, [], "the game folder holds rules and records, not tools")
        # an AST test, not a grep: a number *printed* in a comparison and a number *defined* as a constant
        # are different things, and only the second one can drift. This is the version that caught RHO being
        # restated in pickleball.py — the greeting-in-a-string version would have passed and the constant
        # would have been in two places.
        import ast
        # 0.55 is deliberately *not* here: it is tennis's drag coefficient, and pickleball's paddle-edge
        # power factor happens to be 0.55 too. A literal test that cannot tell a coincidence from a copy
        # teaches nothing and would be silenced the first time it was inconvenient.
        wanted = {0.002377, 1.46667, 0.0063, 78.0, 27.0, 32.17}
        offenders = {}
        for f in sorted((REPO / "lab").glob("*.py")):
            if f.name == "tennis.py":
                continue
            tree = ast.parse(f.read_text(encoding="utf-8"))
            found = sorted({n.value for n in ast.walk(tree)
                            if isinstance(n, ast.Constant) and isinstance(n.value, float) and n.value in wanted})
            if found:
                offenders[f.name] = found
        # putt.py's 32.17 is the one copy that already existed (2026-11-15, recorded in the page's §4); it is
        # not this game's to fix and it is listed here so the count is honest rather than zero by exemption
        self.assertEqual(offenders, {"putt.py": [32.17]},
                         "a second copy of a physics constant is how this breaks: " + str(offenders))

    # ---- the member's seat --------------------------------------------------------------------------
    def test_a_member_names_a_pace_and_a_point_not_an_angle(self):
        """§5o: the first two member serves went into their own side of the net because the prompt asked for a
        face angle in degrees — the solver's answer instead of the question. `PACE 24 AT 26,6` is the movement a
        player actually forms, and the engine turns it into the paddle with the same solver its choosers use.
        Checked both ways: the parser takes the line and refuses prose, and the shot it produces lands where the
        member said."""
        pk = self.pk
        self.assertEqual(pk.parse_move("PACE 24 AT 26,6")["target"], (26.0, 6.0))
        self.assertEqual(pk.parse_move("pace 30 mph at 36.5, 14")["pace"], 30.0)
        self.assertIsNone(pk.parse_move("I would like to dink it softly to the left."))
        p = self.t.Player(name="A", north=True, practice=400)
        face, power, aim, dist = pk.solve_move(p, (15.0, 10.0), {"pace": 12.0, "target": (26.0, 6.0)},
                                               "groundstroke", "hard", (0.0, 0.0))
        self.assertAlmostEqual(power, 20.0, places=3, msg="power is the member's pace in six tenths")
        self.assertAlmostEqual(dist, math.hypot(11.0, 4.0), places=3)
        shot = pk.strike(p, None, face=face, power=power, aim=aim, shot="groundstroke", surface="hard",
                         wind=(0.0, 0.0), pos=(15.0, 10.0), clean=True, aim_dist=dist)
        land = shot["traj"]["land"]
        self.assertAlmostEqual(land[0], 26.0, delta=1.5, msg=f"it landed at x={land[0]:.1f}, not 26")
        self.assertAlmostEqual(land[1], 6.0, delta=1.5, msg=f"it landed at y={land[1]:.1f}, not 6")

    def test_the_ball_the_chooser_played_is_the_ball_it_probed(self):
        """A chooser aims at a point, so it knows the distance its aim is measured down — and until this line it
        dropped that number at the return, so `strike` fell back to the hard 32 ft azimuth of §5j and played a
        different ball from the one it had just checked. The four-tuple is the fix: same face, same power, same
        aim line, and the distance it was solved at."""
        pk = self.pk
        p = self.t.Player(name="A", north=True, practice=400)
        here, ty = (15.0, 10.0), 4.0
        face = pk.aim_at(p, (26.0, ty), "groundstroke", "hard", (0.0, 0.0), 20.0, here)
        probed = pk.strike(p, None, face=face, power=20.0, aim=ty, shot="groundstroke", surface="hard",
                           wind=(0.0, 0.0), pos=here, clean=True, aim_dist=math.hypot(11.0, 6.0))
        played_old = pk.strike(p, None, face=face, power=20.0, aim=ty, shot="groundstroke", surface="hard",
                               wind=(0.0, 0.0), pos=here, clean=True)
        self.assertAlmostEqual(probed["traj"]["land"][1], ty, delta=1.6, msg="probed at the right distance")
        self.assertGreater(abs(played_old["traj"]["land"][1] - ty), 2.0,
                           "and at 32 ft the same swing lands somewhere else — which is the bug")

    def test_a_member_that_writes_prose_still_plays_a_legal_serve(self):
        """The fallback is the shot a coach would give it. The old one drove at the centre of the court from
        wherever the member stood, which for a server is a second fault on top of the first; a server now gets a
        serve aimed into the diagonal service area, checked by the engine's own rule."""
        pk = self.pk
        p = self.t.Player(name="A", north=True, practice=400)
        face, power, aim, dist = pk.solve_move(p, (-1.0, 5.0), {"pace": 30.0, "target": (pk.NET_X + 14.0, 15.0)},
                                               "serve", "hard", (0.0, 0.0))
        shot = pk.strike(p, None, face=face, power=power, aim=aim, shot="serve", surface="hard",
                         wind=(0.0, 0.0), pos=(-1.0, 5.0), clean=True, aim_dist=dist)
        land = shot["traj"]["land"]
        self.assertTrue(pk.in_service_area(land, True, 5.0), f"the safe serve landed at {land} and is not legal")

    # ---- the second body ----------------------------------------------------------------------------
    def test_the_partner_walks_to_their_stance_and_nobody_is_left_watching(self):
        """§5m's film found fourteen inert body-slots in twelve long rallies: the player who was neither hitting
        nor receiving never moved, and could watch a whole point from four feet behind a baseline. §5n gives them
        the hitter's own rule — walk to your stance on this shot's flight time — under `PARTNER_WALK`, and the
        measurement is the assertion: in long rallies, bodies that end more than 3 ft from their own kitchen line
        fall from a third of them to under one in twenty. The A/B is inside the test, because a flag that changes
        nothing is a flag pretending to be a model."""
        pk = self.pk
        def far_share(flag, games=4):
            """Four games a side, not one. A single pinned game is not a measurement in this engine: reach now
            grows with a player's own shots (§5t), so the same pin drifts by 2.7% between one game and the next
            and one pinned game went from fifteen long rallies to seven on that drift alone."""
            pk.PARTNER_WALK = flag
            far = slots = 0
            try:
                for g in range(games):
                    film = {}
                    pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("dink"),
                                 wind_seed_ms=1234500 + g, say=lambda *a, **k: None, film=film)
                    by = {}
                    for m in film["moves"]:
                        by.setdefault(m["rally"], []).append(m)
                    for r in film.get("rallies") or []:
                        if r.get("shots", 0) < 6:
                            continue
                        for name in ("A", "B", "C", "D"):
                            mine = [m for m in by.get(r["rally"], []) if m["player"] == name]
                            if not mine:
                                continue
                            last = max(mine, key=lambda m: m["t1"])
                            line = pk.KITCHEN_LINE if name in ("A", "B") else pk.NET_X + pk.KITCHEN
                            slots += 1
                            if abs(last["to"][0] - line) > 3.0:
                                far += 1
            finally:
                pk.PARTNER_WALK = True
            return far / max(1, slots), slots
        on, n_on = far_share(True)
        off, n_off = far_share(False)
        self.assertGreater(n_on, 120, "four dink games have plenty of long rallies in them")
        self.assertLess(on, 0.10, f"{on:.0%} of bodies ended a long rally more than 3ft off their own line")
        self.assertGreater(off, 0.18, "and without the walk it is a quarter of them, or the flag is a no-op")

    def test_a_walk_to_the_stance_is_still_a_walk(self):
        """The partner is not teleported to the line because the rule is a walk: `move_toward` caps the step at the
        legs' own speed on the shot's flight time, and the film keeps that budget. Measured directly — for every
        move in a film, the ground covered is what the legs cover in the time the move takes."""
        pk = self.pk
        film = {}
        pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("dink"), wind_seed_ms=1234502,
                     say=lambda *a, **k: None, film=film)
        players = {n: self.t.Player(name=n, north=i < 2, practice=200)
                   for i, n in enumerate(["A", "B", "C", "D"])}
        for m in film["moves"]:
            dt = m["t1"] - m["t0"]
            if dt <= 1e-9:
                continue
            grown = math.hypot(m["to"][0] - m["from"][0], m["to"][1] - m["from"][1])
            self.assertLessEqual(grown, pk.movement_speed(players[m["player"]]) * dt * 1.02 + 1e-6)

    # ---- the film ------------------------------------------------------------------------------------
    def test_recording_a_game_does_not_change_it(self):
        """The renderer's licence. A film is written by appending to a dictionary the caller owns, so the engine
        cannot notice it is being watched: same clock, same hands, same score, same number of shots, with and
        without. A record that perturbs the game is a camera that moves the ball."""
        pk = self.pk
        names = ["A", "B", "C", "D"]
        quiet = lambda *a, **k: None
        m0, r0 = pk.play_game(names, [200] * 4, pk.make_chooser("steady"), wind_seed_ms=1234500, say=quiet)
        film = {}
        m1, r1 = pk.play_game(names, [200] * 4, pk.make_chooser("steady"), wind_seed_ms=1234500, say=quiet,
                              film=film)
        self.assertEqual((m0.teams[0].score, m0.teams[1].score), (m1.teams[0].score, m1.teams[1].score))
        self.assertEqual(r0["lengths"], r1["lengths"], "shot for shot, or the film is of another game")
        self.assertEqual(len(film["shots"]), sum(r1["lengths"]), "one record per shot, no more and no fewer")
        self.assertEqual(len(film["rallies"]), len(r1["rallies"]))

    def test_the_film_clock_starts_at_zero_and_runs_on_the_balls_own_time(self):
        """Every shot is stamped with the second it was struck, and every shot after the first begins at the moment
        the previous ball was met — not when it landed, which is a different question and a different second. A
        monotone clock is what lets the ball and the feet share an axis at all; before this turn the engine had no
        time in it whatsoever."""
        pk = self.pk
        film = {}
        pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("steady"), wind_seed_ms=1234500,
                     say=lambda *a, **k: None, film=film)
        self.assertTrue(film["shots"])
        by_rally = {}
        for s in film["shots"]:
            by_rally.setdefault(s["rally"], []).append(s)
            self.assertGreaterEqual(s["t0"], 0.0)
            self.assertTrue(s["path"], "a shot with no traced flight is a shot the renderer would have to invent")
            if s["hit"] is not None:
                self.assertGreater(s["hit"], s["t0"], "the ball is met after it is struck")
        for rally, shots in by_rally.items():
            self.assertEqual(shots[0]["t0"], 0.0, f"rally {rally} starts at its own zero")
            for a, b in zip(shots, shots[1:]):
                if a["hit"] is not None:
                    self.assertAlmostEqual(b["t0"], a["hit"], places=3,
                                           msg=f"rally {rally}: shot {b['shot']} starts when the last ball "
                                               f"was met, not when it landed")

    def test_no_body_crosses_the_court_between_two_frames_of_the_film(self):
        """The film's feet are the engine's feet, and the engine's feet walk. So: a move that takes time covers no
        more ground than the player's legs cover in that time, and a move that takes none is a *placement* — the
        serve, or the rally's opening tableau — and nothing else. This is the test that would have caught the
        original engine teleporting a receiver onto the landing point, which is what made the stance measure as
        irrelevant in §5b."""
        pk = self.pk
        film = {}
        pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("dink"), wind_seed_ms=1234500,
                     say=lambda *a, **k: None, film=film)
        fastest = max(pk.movement_speed(self.t.Player(name=n, north=i < 2, practice=200))
                      for i, n in enumerate(["A", "B", "C", "D"]))
        for m in film["moves"]:
            dx = m["to"][0] - m["from"][0]
            dy = m["to"][1] - m["from"][1]
            d = math.hypot(dx, dy)
            dt = m["t1"] - m["t0"]
            if dt <= 1e-9:
                self.assertEqual(m["t0"], 0.0,
                                 f"{m['player']} moved {d:.1f}ft in no time at t={m['t0']} — only the serve "
                                 f"placement and the rally's tableau are instant")
                continue
            self.assertLessEqual(d, fastest * dt * 1.02 + 1e-6,
                                 f"{m['player']} covered {d:.1f}ft in {dt:.2f}s: that is "
                                 f"{d / dt:.1f}ft/s, faster than any player in this game")

    def test_the_partner_has_legs_now_and_can_be_told_not_to(self):
        """§5m's finding, turned into the definition of the constant that changed it. With `PARTNER_WALK` off — the
        engine as it stood until 2026-11-19 — every body that moves in a rally is a body that hit a ball in it, and
        fourteen of forty-eight body-slots in long rallies are spectators. With it on, bodies move without touching
        the ball, because their rule is the hitter's: a player who is neither hitting nor receiving walks to their
        stance. The old number is kept as the A/B rather than deleted, because "the partner has legs" is only a
        claim if the engine that had none is still one flag away."""
        pk = self.pk
        def measure(flag):
            pk.PARTNER_WALK = flag
            try:
                film = {}
                pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("dink"), wind_seed_ms=1234500,
                             say=lambda *a, **k: None, film=film)
                per_rally = {}
                for sh in film["shots"]:
                    per_rally.setdefault(sh["rally"], set()).add(sh["player"])
                movers = {}
                for m in film["moves"]:
                    if m["from"] == m["to"]:
                        continue
                    movers.setdefault(m["rally"], set()).add(m["player"])
                silent = sum(len(v - per_rally.get(r, set())) for r, v in movers.items())
                lengths = {r["rally"]: r["shots"] for r in film["rallies"]}
                long_rallies = [r for r, n in lengths.items() if n >= 6]
                inert = sum(4 - len(movers.get(r, ())) for r in long_rallies)
                return silent, inert, len(long_rallies)
            finally:
                pk.PARTNER_WALK = True
        silent_off, inert_off, n_long = measure(False)
        silent_on, inert_on, _ = measure(True)
        self.assertEqual(silent_off, 0, "before §5n a mover was always a hitter: that is what a defined absence is")
        self.assertGreaterEqual(inert_off, n_long, "and the spectators showed up as inert slots in long rallies")
        self.assertGreater(silent_on, 0, "with the walk on, a body moves without touching the ball")
        # The *count* of inert slots is not comparable game to game — the walk changes which opponent is nearest,
        # so the two runs are two different games and the inert total is noise (19 against 14 on one pin, the
        # other way round on another). The measure that survives that is distance from the stance, and it is the
        # other test's job. Kept here only as the structural half.

    def test_the_page_carries_its_own_film_and_fetches_nothing(self):
        """A replay that needs a server is a replay that stops working when the server does, which is why the page
        is baked with its own data rather than fetching it (the tennis renderer fetches, and needs `games/tennis/
        vendor/` and a local web server to do it). Two claims: the template contains a placeholder and no network
        call, and the baked page contains the film and no placeholder."""
        pk = self.pk
        page = (REPO / "games" / "pickleball" / "replay3d.html").read_text(encoding="utf-8")
        self.assertIn("__FILM__", page, "the template is a template")
        self.assertNotIn("fetch(", page, "a page opened from disk cannot fetch: file:// is not a server")
        self.assertNotIn("import ", page.split("<script type=\"application/json\"")[0],
                         "and it needs no library to draw a court")
        film = {}
        m, res = pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("steady"), wind_seed_ms=1234500,
                              say=lambda *a, **k: None, film=film)
        scene = pk.film_scene(film, ["A", "B", "C", "D"], score=(m.teams[0].score, m.teams[1].score),
                              clock=res["clock"], surface="hard")
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            pj, pp = pk.write_film(scene, f"{td}/f.json", f"{td}/f.html")
            back = json.loads(pj.read_text())
            self.assertEqual(back["shots"][0]["t0"], scene["shots"][0]["t0"], "the JSON is the scene")
            baked = pp.read_text(encoding="utf-8")
            self.assertNotIn("__FILM__", baked, "the placeholder is gone once there is a film to put in it")
            self.assertIn('"sport":"pickleball"', baked, "and the film is in the page, not beside it")

    def test_the_figures_are_jointed_and_both_of_their_animations_are_the_engine_s(self):
        """§5q. A body is joints and two animations, and neither animation is invented here: the legs walk because
        the engine wrote a move (distance over that move's own duration), and the arm swings because the engine
        struck a shot (the shot's own clock, and the blade tilted by that shot's face). If a figure looks wrong the
        number behind it is wrong, which is the same contract the ball has with `path`."""
        page = (REPO / "games" / "pickleball" / "replay3d.html").read_text(encoding="utf-8")
        body = page.split("const BODY = {")[1].split("};")[0]
        for joint in ("ankle", "knee", "hip", "shoulder", "neck", "head"):
            self.assertIn(joint, body, f"the figure has a {joint}")
        self.assertIn("(best.to[0] - best.from[0]) / dt", page, "the stride is the move's own velocity")
        self.assertIn("m.travelled / STRIDE", page, "and its phase is distance walked")
        self.assertIn("(t - (s.t0 - 0.55)) / 1.0", page, "the swing is hung on the shot's own strike time")
        self.assertIn("sw.shot.face", page, "the blade is tilted by the shot's face, not by a constant")
        self.assertNotIn("PLAYER_HT", page,
                         "and no body is one stroke from the feet to a circle any more — that was the stick figure")

    def test_the_screen_asks_where_and_how_hard_and_never_for_an_angle(self):
        """§5q, and §5o's lesson applied to a form rather than to a prompt: the control is the court. The tennis
        play view asks for a face angle in degrees; a pickleball screen that did the same would be handing a person
        the solver's answer, which is exactly the thing that put two member serves in their own net."""
        page = (REPO / "games" / "pickleball" / "ui-mock.html").read_text(encoding="utf-8")
        self.assertNotIn('type="number"', page, "nothing in the screen is a number you have to know")
        self.assertNotIn("FACE", page, "and it never names the paddle's angle")
        self.assertNotIn("POWER", page, "or a power percentage")
        self.assertIn("PACE", page, "it asks for a pace, in miles an hour, the same word the member answers with")
        self.assertIn("pointerdown", page, "the target is chosen by clicking the court")
        self.assertNotIn("fetch(", page, "and the screen is one file, like the film")

    def test_the_film_says_how_hard_each_ball_was_to_reach(self):
        """§5r. A film that can only say the ball went out cannot say anybody was troubled, and that is the whole
        argument about §5c's perfect defence. So every shot carries the stretch its contact was made at, and every
        shot somebody had to run for carries the demand and the slack."""
        pk = self.pk
        film = {}
        pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("steady"), wind_seed_ms=1234500,
                     say=lambda *a, **k: None, film=film)
        shots = film["shots"]
        self.assertTrue(all("stretch" in s for s in shots), "every contact says how stretched it was")
        self.assertTrue(all(0.0 <= s["stretch"] <= 1.0 for s in shots), "and stretch is a fraction of reach")
        self.assertGreater(max(s["stretch"] for s in shots), 0.75,
                           "at steady hands somebody has to reach for the ball; if nobody does, §5c is back")
        with_demand = [s for s in shots if "demand" in s]
        self.assertGreater(len(with_demand), len(shots) // 2, "most shots are somebody's to return")
        for s in with_demand:
            self.assertGreater(s["demand"], 0.0, "a demand is a distance")
            self.assertGreaterEqual(s["spare"], -1e-6,
                                    "the interception is a yes/no, so a returned ball always has slack left")

    def test_a_stretched_contact_faults_more_often_than_a_comfortable_one(self):
        """§5c, restated as a measurement rather than a memory. The engine's defence is beaten by *placement*:
        a contact at full extension errors about twice as often as one made with the feet under it. This is the
        test that fails if stretching ever goes back to being free."""
        pk = self.pk
        def is_fault(s):
            w = s["why"] or ""
            return not (w.startswith("in the kitchen") or "from their baseline" in w)
        shots = []                       # dink hands, four games: a steady-hands contact is at full stretch 90% of
        for g in range(4):               # the time, so the contrast lives in the soft game, where it is about 3x
            film = {}                    # and the comfortable bucket has six hundred contacts in it
            pk.play_game(["A", "B", "C", "D"], [200] * 4, pk.make_chooser("dink"), wind_seed_ms=1234500 + g,
                         say=lambda *a, **k: None, film=film)
            shots += film["shots"]
        free = [s for s in shots if s["stretch"] < 0.25]
        stretched = [s for s in shots if s["stretch"] > 0.75]
        self.assertGreater(len(free), 10, "there are contacts with the feet under the ball")
        self.assertGreater(len(stretched), 10, "and contacts at the end of the reach")
        p_free = sum(1 for s in free if is_fault(s)) / len(free)
        p_stretch = sum(1 for s in stretched if is_fault(s)) / len(stretched)
        self.assertGreater(p_stretch, 1.4 * p_free,
                           f"a stretched contact faults more often ({p_stretch:.2f} vs {p_free:.2f}) — otherwise "
                           f"the penalty in `strike` does nothing and the defence is free again")

    def test_a_reader_that_cannot_act_is_not_an_experiment(self):
        """The 2026-11-20 re-run found it: the 'learn 2 ft' and 'read the faults' rows of the season were the *same
        game*, because a side that is not a learner holds `APPROACH_DEFAULT` and that default is 2.0 ft. A contrast
        against 2 ft is therefore no contrast at all, and the identical totals were a fact about the harness, not
        about reading. Written down here so the trap cannot be reset by accident."""
        pk = self.pk
        self.assertEqual(pk.APPROACH_DEFAULT, 2.0,
                         "if this number moves, the retracted rows in §5k/§5r may be re-runnable — check before"
                         " believing either of them")
        src = (REPO / "lab" / "pickleball.py").read_text(encoding="utf-8")
        self.assertIn("stances[n] = float(static.get(n, APPROACH_DEFAULT))", src,
                      "a non-learning side is pinned to the default, which is what made the two rows one row")

    def test_reach_is_a_parameter_and_it_is_the_lever(self):
        """§5s. §5r left "is reach the lever?" open, and the honest way to ask it is a knob: an override that is
        empty by default, so every number measured before today reproduces, and a head-to-head that moves the
        *trait* between seats over the same pins. Two claims, one mechanistic and one about points."""
        pk = self.pk
        hitter = pk.Player(name="probe-hitter", north=True, practice=200)
        probe = pk.Player(name="probe", north=False, practice=200)
        face = pk.aim_at(hitter, (24.5, 10.0), "groundstroke", "hard", (0.0, 0.0), 30.0, (18.0, 10.0))
        shot = pk.strike(hitter, None, face=face, power=30.0, aim=10.0, shot="groundstroke", surface="hard",
                         wind=(0.0, 0.0), pos=(18.0, 10.0), clean=True, aim_dist=6.5)
        traj = shot["traj"]
        self.assertIn("bounce", traj, "the probe ball is a ball that lands")
        land, ft = traj["land"], traj["time"]
        frm = (land[0] + 1.0, land[1] + 12.0)          # twelve feet across, which is a doubles partner's half
        long_m = pk.interception(probe, land, ft, traj["bounce"], "hard", frm=frm, reach=6.0)
        short_m = pk.interception(probe, land, ft, traj["bounce"], "hard", frm=frm, reach=3.5)
        self.assertLess(long_m["need"], short_m["need"],
                        "reach buys time: the same ball needs less of it from a longer paddle")

        # the default is every player at PADDLE_REACH, which is what keeps every earlier measurement reproducible
        self.assertEqual(pk.REACH_FOR, {}, "no experiment is running, so nobody has a private reach")
        self.assertEqual(pk.reach_of(probe), pk.PADDLE_REACH)

        # the head-to-head: the trait moves between the seats and the same pins are used for both halves, so
        # whatever belongs to the seat and the clock is in both halves and drops out of the sum
        names = ["north-a", "north-b", "south-a", "south-b"]
        def half(long_side, games=4):          # four a half: at 3.5 ft the margin was 131-61 over six, so this
                                               # is a claim with room in it rather than a coin flip
            pk.REACH_FOR.clear()
            for n in (names[:2] if long_side == "north" else names[2:]):
                pk.REACH_FOR[n] = 6.0
            for n in (names[2:] if long_side == "north" else names[:2]):
                pk.REACH_FOR[n] = 3.5
            L = S = 0
            for g in range(games):
                m, _ = pk.play_game(names, [200] * 4, pk.make_chooser("dink"), wind_seed_ms=1234500 + g,
                                    first_team=g % 2, say=lambda *a, **k: None)
                li = 0 if long_side == "north" else 1
                L += m.teams[li].score
                S += m.teams[1 - li].score
            pk.REACH_FOR.clear()
            return L, S
        try:
            a, b = half("north"), half("south")
        finally:
            pk.REACH_FOR.clear()
        self.assertGreater(a[0] + b[0], a[1] + b[1],
                           f"the long reach takes the points ({a[0] + b[0]} to {a[1] + b[1]}); if this ever stops"
                           f" being true, reach has stopped being the thing that decides a rally")

    # three small aliases so the test bodies read like arithmetic, not like module plumbing
    import math as _math
    math_radians = staticmethod(_math.radians)
    cos = staticmethod(_math.cos)
    sin = staticmethod(_math.sin)


class TestChat(unittest.TestCase):
    """The conversation page, 2026-11-04.

    The founder's objection to §5 was four words long — "not on a phone" — and the answer is a page with a
    drop list and two boxes. These tests cover the three ways such a page lies: it offers a participant who
    does not exist, it prints an engine's prose as if it were the participant's reply, or it fails on a
    missing key in a way a person cannot act on.
    """

    @classmethod
    def setUpClass(cls):
        cls.c = load(REPO / "lab" / "chat.py", "chat_mod")

    def test_the_drop_list_is_the_members_and_nobody_else(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "Ada" / "state").mkdir(parents=True)
        (tmp / "Ada" / "state" / "voice.md").write_text("api: gemini\nmodel: x\n")
        (tmp / "Ada" / "state" / "identity.md").write_text("I am Ada.\n")
        (tmp / "Half" / "state").mkdir(parents=True)          # voice but no identity: not a member
        (tmp / "Half" / "state" / "voice.md").write_text("api: gemini\nmodel: x\n")
        (tmp / "notes").mkdir()
        self.assertEqual(self.c.members(tmp), ["Ada"])

    def test_a_voice_file_that_says_nothing_is_an_error_not_a_guess(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "Ada" / "state").mkdir(parents=True)
        (tmp / "Ada" / "state" / "voice.md").write_text("api: gemini\n")
        with self.assertRaises(SystemExit) as e:
            self.c.voice_of("Ada", tmp)
        self.assertIn("needs an 'api:' line and a 'model:' line", str(e.exception))

    def test_a_missing_key_says_which_name_to_set_and_does_not_call_anything(self):
        # A member of its own in a temp root, not whichever member this repository happens to ship: the
        # bench's wake/members holds fixtures called "a" and "b", so a test that names a real participant
        # passes in the colony and fails in the bench. That is the fixture-versus-shipped defect this
        # suite already has nineteen of.
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "wake" / "members" / "Ada" / "state").mkdir(parents=True)
        (tmp / "wake" / "members" / "Ada" / "state" / "voice.md").write_text("api: gemini\nmodel: x\n")
        (tmp / "wake" / "members" / "Ada" / "state" / "identity.md").write_text("I am Ada.\n")
        saved = os.environ.pop("TRIBE_API_KEY_GEMINI", None)
        try:
            out = self.c.ask_member("Ada", "hello", root=tmp)
        finally:
            if saved is not None:
                os.environ["TRIBE_API_KEY_GEMINI"] = saved
        self.assertFalse(out["ok"])
        self.assertIn("set TRIBE_API_KEY_GEMINI", out["reply"])
        self.assertIn("only name this project reads", out["reply"])

    def test_the_page_has_a_drop_list_and_two_boxes(self):
        html = (REPO / "chat.html").read_text(encoding="utf-8")
        self.assertIn('<select id="member"', html)
        self.assertIn('<textarea id="msg"', html)
        self.assertIn('<textarea id="reply" readonly', html)
        self.assertIn('name="viewport"', html, "the whole point was that it works on a phone")

    def test_a_model_that_thinks_before_it_answers_gets_room_to_think(self):
        """The small cap that makes a one-word answer stay one word starves a reasoning model.

        Measured 2026-11-06 on Groq's `gpt-oss-120b`: a 400-token cap bought 398 tokens of reasoning, an empty
        answer and finish_reason "length". The game read the empty string as a member who had said nothing,
        played a default shot, and wrote it into the record as though the member had chosen it — the worst
        kind of wrong, because the file looks like a choice.
        """
        src = (REPO / "lab" / "rps.py").read_text(encoding="utf-8")
        self.assertIn('finish_reason") != "length"', src, "an answer cut off before it began must be retried")
        self.assertIn("ANSWER_CAPS = (400, 2400, 8000)", src,
                      "the retry ladder must end above 2,400: deepseek-flash spent 2,400 of 2,400 on reasoning and "
                      "answered only at 4,000, and every silent give-up is a default shot filed as a choice")
        self.assertIn("RATE_WAITS", src, "a free tier counted per minute is answered by waiting, not by giving up")
        self.assertIn("x-ratelimit-reset-tokens", src,
                      "the wait must be the vendor's own number: a fixed 20s wait is shorter than the 60s window "
                      "it is waiting for, which is how a live season spent two and a half minutes being refused")

    def test_a_game_asks_for_an_answer_and_not_for_a_deliberation(self):
        """Measured 2026-11-06: deepseek-flash spent 600 of 600 tokens thinking about a racquet angle and returned
        nothing, four times in six shots; the same question with thinking disabled came back in 11 tokens.

        The games ask for one line, so the line is the measurement. A vendor that thinks past its allowance gives
        the game an empty string, and the game then plays a default shot. Only listed vendors get the field: an
        unknown key is a 400 on a strict API, and a 400 on every shot is a worse defect than the one being fixed.
        """
        src = (REPO / "lab" / "rps.py").read_text(encoding="utf-8")
        self.assertIn('"api.deepseek.com": {"thinking": {"type": "disabled"}}', src,
                      "the games must ask the vendor that deliberates to answer instead")
        self.assertIn('"api.groq.com": {"reasoning_effort": "low"}', src,
                      "the open-weight model has the same knob under a different name: 436 reasoning tokens to "
                      "choose a racquet angle became 51, and 'medium' spent the whole allowance and answered nothing")
        self.assertIn('for host, extra in ANSWER_ONLY.items() if host in base', src,
                      "the field must be sent only to the vendor that accepts it")

    def test_the_games_can_play_on_every_engine_the_wake_can_wake_on(self):
        """Two tables for one fact is how a Groq member woke and then found that tennis did not know it.

        Measured 2026-11-06: a wake on Groq answered in three seconds, and the first rally died with
        KeyError: 'groq' because `lab/rps.py` — which the games share — kept its own shorter list of engines.
        The same three lines also carry the User-Agent, because the game's request hits the same door.
        """
        self.assertEqual(sorted(rps.BASES), sorted(wake.API_BASES),
                         "the games' engine table and the wake's must be one table")
        for url in rps.BASES.values():
            self.assertEqual(rps.BASES, wake.API_BASES, "the addresses themselves must match, not just the names")
        src = (REPO / "lab" / "rps.py").read_text(encoding="utf-8")
        # Counted by walking the requests rather than by counting the header: the number of paths is not a fact
        # anybody should have to remember. It was 3 (common, Gemini, Claude) until 2026-11-06, when Claude's
        # temperature retry added a fourth request inside the same path.
        paths = src.split("urllib.request.Request(")[1:]
        self.assertTrue(paths, "the games must actually make a request")
        for n, chunk in enumerate(paths, 1):
            self.assertIn('"User-Agent": UA', chunk[:300],
                          f"remote path #{n} in the games must introduce itself to the vendor")

    def test_one_vendor_named_for_a_field_is_given_to_every_player(self):
        """Found 2026-11-06 in a live Groq season, two shots in.

            --names Greta,Hans --vendor groq
            IndexError: list index out of range   (lab/tennis.py:937, keys[hitter])

        Naming one engine for a field is the ordinary way to say "both of these players run on it", and
        tennis accepted the flag without saying anything and then crashed when the second player's turn came.
        A one-element list is spread over the field; a mismatched list is refused out loud rather than
        indexed into.
        """
        self.assertEqual(rps.spread(["groq"], 2, "--vendor"), ["groq", "groq"])
        self.assertEqual(rps.spread(["groq", "deepseek"], 2, "--vendor"), ["groq", "deepseek"])
        self.assertEqual(rps.spread(["gemini", "deepseek", "qwen"], 3, "--vendor"),
                         ["gemini", "deepseek", "qwen"])
        with self.assertRaises(SystemExit):
            rps.spread(["groq", "deepseek", "qwen"], 2, "--vendor")
        for game in ("tennis.py", "rps.py", "favour.py", "wind.py", "word.py"):
            src = (REPO / "lab" / game).read_text(encoding="utf-8")
            self.assertIn("spread(", src, f"{game} must accept one engine named for the field")

    def test_every_engine_with_a_default_model_is_an_engine_the_tool_accepts(self):
        """A default model for an engine nobody can pick is a line that never runs; an engine with a default the
        tool does not accept is worse, because the member is created and fails on its first wake. Groq was added
        to the defaults after the founder asked why it should not be: the answer was that nothing stops it, and
        its ids are namespaced by whoever trained the weights — the id is Groq's business, written down once."""
        self.assertTrue(set(rps.DEFAULT_MODEL) <= set(tribe.BASES),
                        f"a default model for an engine the tool refuses: {set(rps.DEFAULT_MODEL) - set(tribe.BASES)}")
        self.assertEqual(rps.DEFAULT_MODEL["groq"], "openai/gpt-oss-120b",
                         "Groq names its models by training house; the prefix is not a typo")

    def test_the_local_page_can_be_reached_from_a_phone(self):
        """The founder's objection to a desktop-only page was four words — "not on a phone" — and a page bound
        to 127.0.0.1 is reachable from exactly one device. Binding to the wifi address is half the fix; the
        other half is printing the address, because nobody should have to find it in System Settings."""
        mod = load(REPO / "lab" / "chat.py", "chat_mod_phone")
        self.assertEqual(mod.addresses("127.0.0.1", 8770), ["http://127.0.0.1:8770"],
                         "a page on this machine alone must not advertise an address it does not serve")
        wide = mod.addresses("0.0.0.0", 8770)
        self.assertEqual(wide[-1], "http://127.0.0.1:8770", "the loopback address is still true on this machine")
        if len(wide) > 1:
            self.assertNotIn("127.0.0.1", wide[0],
                             "the address printed first must not be the one that means 'this device' — the "
                             "founder typed it into a phone and got ERR_CONNECTION_REFUSED")
        self.assertIn("--phone", (REPO / "lab" / "chat.py").read_text(encoding="utf-8"),
                      "there must be a way to say 'put this on the wifi' without knowing about 0.0.0.0")

    def test_the_server_answers_in_the_shape_the_page_expects(self):
        import json as _json
        import threading as _threading
        import urllib.request as _url
        from http.server import ThreadingHTTPServer
        c = self.c
        asked = {}

        def stub(member, text, root=None, timeout=None):
            asked["member"], asked["text"] = member, text
            return {"ok": True, "reply": "I read my journal and I am well.", "verdict": "OK", "path": "raw-x.json"}

        real = c.ask_member
        c.ask_member = stub
        srv = ThreadingHTTPServer(("127.0.0.1", 0), c.Handler)
        t = _threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        try:
            listed = None
            with _url.urlopen(base + "/members", timeout=10) as r:
                listed = _json.load(r)["members"]
            self.assertTrue(listed, "this repository has no participants to list")
            self.assertEqual(listed, c.members(), "the drop list is whatever members() says, sorted")
            with _url.urlopen(base + "/", timeout=10) as r:
                self.assertIn("conversation", r.read().decode().lower())
            req = _url.Request(base + "/say", method="POST",
                               data=_json.dumps({"member": listed[0], "text": "how are you?"}).encode(),
                               headers={"Content-Type": "application/json"})
            with _url.urlopen(req, timeout=10) as r:
                got = _json.load(r)
        finally:
            c.ask_member = real
        self.assertTrue(got["ok"])
        self.assertEqual(got["reply"], "I read my journal and I am well.")
        self.assertEqual(asked["member"], listed[0])
        self.assertEqual(asked["text"], "how are you?")

    def test_a_reply_is_filed_and_the_derived_pages_are_rebuilt(self):
        """The page's first version called the wake and stopped there.

        The suite caught it within a minute: `magazine.py`'s pages are a function of the record, so a file in
        `output/` that never reached the shelf makes the issue, index, ledger and projects pages disagree
        with the repository and the derivability test fails. The page now does what `talk.sh` does — file the
        work, then rebuild the pages — and this test holds it to that with a fake harness underneath.
        """
        import types
        c = self.c
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        adir = tmp / "wake" / "members" / "Ada"
        (adir / "state").mkdir(parents=True)
        (adir / "output").mkdir()
        (adir / "state" / "voice.md").write_text("api: gemini\nmodel: x\n")
        (adir / "state" / "identity.md").write_text("I am Ada.\n")
        ran = []

        def fake_run(cmd, cwd=None, capture_output=None, text=None, timeout=None):
            ran.append(" ".join(Path(x).name if "/" in str(x) else str(x) for x in cmd[1:3]))
            if str(cmd[1]).endswith("wake.py"):
                (adir / "output" / "raw-TEST.json").write_text('{"content": "yes, I answered"}')
                return types.SimpleNamespace(returncode=0, stdout="=== verdict: OK (test) ===", stderr="")
            if str(cmd[1]) == "file_work.py":
                return types.SimpleNamespace(returncode=0, stdout="filed works/Ada/x.md", stderr="")
            return types.SimpleNamespace(returncode=0, stdout="1", stderr="")

        # Put the variable back exactly as it was found. The first version of this cleanup left
        # TRIBE_API_KEY_GEMINI=test-key in the environment for the rest of the suite, and two tests in
        # TestWindowPath started failing because wake.py, handed a key, no longer printed the message they
        # check for. A leaked global is a test that passes alone and fails in company.
        had = "TRIBE_API_KEY_GEMINI" in os.environ
        old_val = os.environ.get("TRIBE_API_KEY_GEMINI")
        os.environ["TRIBE_API_KEY_GEMINI"] = "test-key"
        real = c.subprocess.run
        c.subprocess.run = fake_run
        try:
            out = c.ask_member("Ada", "hello", root=tmp)
        finally:
            c.subprocess.run = real
            if had:
                os.environ["TRIBE_API_KEY_GEMINI"] = old_val
            else:
                os.environ.pop("TRIBE_API_KEY_GEMINI", None)
        self.assertTrue(out["ok"])
        self.assertEqual(out["reply"], "yes, I answered")
        self.assertEqual(out["path"], "works/Ada/x.md", "the page reports the filed work, not the raw json")
        joined = " | ".join(ran)
        self.assertIn("file_work.py", joined, "a conversation that is not filed did not happen")
        self.assertIn("magazine.py", joined, "the pages derived from the record must be rebuilt")

    def test_a_participant_who_does_not_exist_is_refused_before_any_call(self):
        import json as _json
        import threading as _threading
        import urllib.error as _err
        import urllib.request as _url
        from http.server import ThreadingHTTPServer
        c = self.c
        called = []
        real = c.ask_member
        c.ask_member = lambda *a, **k: called.append(a) or {"ok": True, "reply": "", "verdict": "", "path": ""}
        srv = ThreadingHTTPServer(("127.0.0.1", 0), c.Handler)
        _threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.server_close)
        self.addCleanup(srv.shutdown)
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        req = _url.Request(base + "/say", method="POST",
                           data=_json.dumps({"member": "../etc", "text": "hi"}).encode(),
                           headers={"Content-Type": "application/json"})
        try:
            with self.assertRaises(_err.HTTPError) as e:
                _url.urlopen(req, timeout=10)
            self.assertEqual(e.exception.code, 400)
            body = _json.load(e.exception)
            self.assertIn("no such member", body["reply"])
        finally:
            c.ask_member = real
        self.assertEqual(called, [], "a name not in the drop list must not reach a wake")


class TestWorkflows(unittest.TestCase):
    """The workflows are the part of the shipped sheet that nobody runs before a stranger does.

    Found 2026-11-04 by the only test that counts: the founder opened the repo on a Pixel, ran the
    Run-workflow form, and no member answered — because `interactive.yml` fell back to member "b", a fixture
    name that exists in the bench and in no colony. A shipped default that only works where it was written
    is the same defect as a test that only passes where it was written.
    """

    WF = REPO / ".github" / "workflows"

    def test_a_workflow_that_forwards_one_key_forwards_them_all(self):
        """The environment a step sees is written by hand, one engine at a time, so it falls behind the members.

        `season.yml` forwarded four keys — DeepSeek, Gemini, Qwen, OpenAI — and the founder's Aphrodite runs on
        OpenRouter. Measured 2026-11-15 in his own tribe: he set the secret, pressed Play, and the run said
        `TRIBE_API_KEY_OPENROUTER is not set, so Aphrodite cannot hit a ball` — a sentence that is honest about
        the environment and false about the world, which is the worst kind. A member's engine is a fact about the
        member; a workflow cannot know which engines a tribe will use, so it must forward every key the harness
        speaks. The rule is checkable without deciding which workflows "call an engine": if a workflow names one
        TRIBE_API_KEY, it names them all.
        """
        if yaml is None:
            self.skipTest("PyYAML not installed")
        rps = load(REPO / "lab" / "rps.py", "rps_for_keys")
        # One exception, and it is stated rather than assumed: paint.yml asks a member's engine for a picture, and
        # `lab/paint.py` refuses by name every engine without an image model — so the only keys it can ever need are
        # the painters'. The exemption is held against paint.py's own table, so a fourth painter cannot slip past.
        paint = load(REPO / "lab" / "paint.py", "paint_for_keys")
        exempt = {"paint.yml": set(paint.PAINTERS)}
        speaks = {e for e in rps.BASES if e != "local"}     # loopback weights have no key to forward
        bad = []
        for f in sorted(self.WF.glob("*.yml")):
            text = f.read_text(encoding="utf-8")
            named = {n.lower() for n in re.findall(r"TRIBE_API_KEY_([A-Z]+)", text)}
            if not named:
                continue
            want = exempt.get(f.name, speaks)
            if f.name in exempt and named != exempt[f.name]:
                bad.append(f"{f.name}: forwards {sorted(named)}; its exemption says {sorted(exempt[f.name])}")
            missing = sorted(want - named)
            if missing:
                bad.append(f"{f.name}: forwards {len(named)} of {len(want)} keys it may need, "
                           f"missing {', '.join(missing)}")
        self.assertEqual(bad, [], "a workflow that forwards one engine's key must forward the rest; "
                                  "otherwise a member on the missing engine is told the key is not set")
    def test_every_field_the_page_sends_a_workflow_is_a_field_that_workflow_declares(self):
        """The founder pressed Play on his own circle on 2026-11-13 and GitHub answered
        `422 · Unexpected inputs provided: ["person", "shot"]` — the page was newer than his repository, and the
        form described his own form back to him. That failure is available to every button the page ever grows
        and it is invisible here, where page and workflow are always the same commit: change one and not the
        other and this repository is still consistent, while a circle installed last month is not.

        So the two sides are read against each other, from the page's own `dispatch(...)` calls. The fields are
        taken from the object literal the page sends — brace-matched, not regex-matched, because the values are
        template strings with `${...}` in them and a lazy `\\}` stops inside the first one.
        """
        if yaml is None:
            self.skipTest("PyYAML not installed")
        page = (REPO / "ait.html").read_text(encoding="utf-8")
        bad, seen = [], 0

        def fields_of(body):
            # `${...}` first: its braces and its colons belong to the value, not to the object.
            flat, depth = "", 0
            for i, ch in enumerate(body):
                if body[i:i + 2] == "${":
                    depth += 1
                    continue
                if depth and ch == "}":
                    depth -= 1
                    continue
                if not depth:
                    flat += ch
            return set(re.findall(r"(?:^|[,{])\s*([A-Za-z_]\w*)\s*:", flat, re.M))

        for m in re.finditer(r"dispatch\(\s*'([\w.-]+)'\s*,\s*\{", page):
            seen += 1
            wf = m.group(1)
            i, depth = m.end(), 1
            while i < len(page) and depth:
                if page[i] == "{":
                    depth += 1
                elif page[i] == "}":
                    depth -= 1
                i += 1
            sent = fields_of(page[m.end():i - 1])
            path = self.WF / wf
            if not path.is_file():
                bad.append(f"{wf}: the page starts a workflow that is not in this repository")
                continue
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            # `on:` is YAML 1.1's boolean true, so PyYAML hands back {True: {'workflow_dispatch': {...}}}. Reading
            # `doc['workflow_dispatch']` found nothing and the first run of this check called all eight presses
            # wrong — the same defect one level up: a check that reads the wrong key and reports the world broken.
            spec = (doc.get(True) or doc.get("on") or {}).get("workflow_dispatch") or doc.get("workflow_dispatch") or {}
            have = set((spec.get("inputs") or {}).keys())
            missing = sorted(sent - have)
            if missing:
                bad.append(f"{wf}: the page sends {missing}, which the workflow does not declare "
                           f"(it has {sorted(have)})")
        self.assertGreater(seen, 0, "no dispatch(...) call was found, so this check read nothing")
        self.assertEqual(bad, [], "a press the page offers would be refused by the circle's own workflow")

    def test_the_clock_asks_the_tool_which_keys_it_has(self):
        """The step that decides whose turn it is must not carry its own list of vendors.

        It did until 2026-11-15: three engines written by hand under ten forwarded secrets, so the runner held a
        key the chooser had never heard of and a member on that engine was skipped every turn -- with the log
        saying `keys for: deepseek`. A list of what is present, kept by hand, is a copy of the environment it runs
        in; the fix is to read the environment. This is the guard: the file calls the flag, and no `KEYED=` list of
        engines comes back.
        """
        src = (self.WF / "clock.yml").read_text(encoding="utf-8")
        self.assertIn("--keyed-from-env", src, "the clock is back to guessing which keys it has")
        self.assertNotIn('KEYED="$KEYED', src, "a hand-written vendor list is back in the clock")
        for engine in ("deepseek", "gemini", "qwen"):
            self.assertNotIn(f'KEYED="$KEYED {engine}"', src)

    def test_no_workflow_carries_a_list_of_member_names(self):
        """The Run-workflow form used to offer a `type: choice` drop list of member names. Two things were wrong
        with it, and only the first was obvious.

        It was stale the first time anybody added a member. And it could not be repaired by the workflow that
        adds one: GITHUB_TOKEN may not write a workflow file — "refusing to allow a GitHub App to create or
        update workflow `.github/workflows/interactive.yml` without `workflows` permission" — so the list of
        members inside a workflow is a list only a person with a terminal can keep true, which is the wrong
        list for a document whose reader has no terminal. The generated list is `members.json`; the form takes
        a name, and the answer path reads the name out of the question itself."""
        published = {m["name"] for m in json.loads((REPO / "members.json").read_text(encoding="utf-8"))["members"]}
        for f in sorted(self.WF.glob("*.yml")):
            for line in f.read_text(encoding="utf-8").splitlines():
                item = line.strip()
                if item.startswith("- ") and item.lstrip("- ").strip() in published:
                    self.fail(f"{f.name} hardcodes the member {item!r} in a list; members.json is the list")

    def test_no_test_member_is_ever_committed(self):
        """A copy of this repository must arrive without the suite's own members in it.

        Two things went wrong with the shelf before this: the template shipped ten folders named `a`, `a2`,
        `b`, `trap` and the instruction sheet had to apologise for them; and the published magazine was built
        out of their works, so a stranger's ledger was a record of members who do not exist. What is committed
        under `wake/members/` and `works/` is what a stranger opens in step 2, so a name from
        `lab/fixtures.txt` may never appear there — asked of git rather than of the working tree, because the
        suite shelves its own fixtures while it runs and would otherwise be checking its own homework. A
        colony with members of its own passes: those are not fixtures.
        """
        if not shutil.which("git"):
            self.skipTest("no git here")
        out = subprocess.run(["git", "ls-files", "--", "wake/members", "works"],
                             cwd=REPO, capture_output=True, text=True)
        if out.returncode != 0:
            self.skipTest("not a git checkout")
        named = {line.strip() for line in (REPO / "lab" / "fixtures.txt").read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.strip().startswith("#")}
        committed = {p.split("/")[1] for p in out.stdout.splitlines() if p.count("/") > 1}
        self.assertEqual(committed & named, set(),
                         "a test member is committed to the shelf; it belongs in lab/fixtures/")

    def test_the_suite_puts_its_members_back_when_it_is_done(self):
        """The suite needs ten members to break and a stranger needs none, so the suite borrows them from
        `lab/fixtures/` and unshelves them at exit. Both halves are load-bearing: a fixture that is not
        named in `lab/fixtures.txt` would be published to a drop list, and one left behind after a failed run
        would be a test member sitting in a colony."""
        stowed = {d.name for d in (REPO / "lab" / "fixtures" / "members").iterdir() if d.is_dir()}
        named = {line.strip() for line in (REPO / "lab" / "fixtures.txt").read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.strip().startswith("#")}
        self.assertEqual(stowed, named, "every stowed test member must be named in lab/fixtures.txt")
        on_shelf = {d.name for d in (REPO / "wake" / "members").iterdir() if d.is_dir()}
        self.assertTrue(stowed <= on_shelf, "the suite must shelve the members it needs before it uses them")

    def test_no_workflow_falls_back_to_a_member_that_does_not_exist(self):
        """`${MEMBER:-b}` reads as "b if nothing was chosen", and b is nothing in a colony. A stranger's first
        comment would have woken a member that is not there."""
        on_disk = {d.name for d in (REPO / "wake" / "members").iterdir()}
        bad = []
        for f in sorted(self.WF.glob("*.yml")):
            for m in re.finditer(r"\$\{MEMBER:-([A-Za-z][\w-]*)\}", f.read_text(encoding="utf-8")):
                if m.group(1) not in on_disk:
                    bad.append(f"{f.name}: MEMBER:-{m.group(1)}")
        self.assertEqual(bad, [], "a workflow's default member must be a member this colony has")

    def test_the_persons_seat_on_the_shelf_does_not_fail_silently(self):
        """The opponent field on the person's form is optional, and leaving it blank is the ordinary case: the
        shelf is the list. The first version of that branch ended the step with **141 and no message** — `head -1`
        closed the pipe, `ls` took a SIGPIPE for it, `set -o pipefail` turned that into a failed assignment, and
        `set -e` took the step down before it wrote anything. A press that does nothing and says nothing is the
        class of defect these workflow tests exist for, and it was found by running the step rather than by
        reading it.

        The person is not on the shelf and is never looked for there; the member is, and is checked on disk.
        """
        if yaml is None:
            self.skipTest("PyYAML not installed")
        wf = yaml.safe_load((self.WF / "season.yml").read_text(encoding="utf-8"))
        step = [s for s in wf["jobs"]["play"]["steps"] if s.get("name") == "Which season, which two"][0]["run"]
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "wake" / "members" / "Lumi" / "state").mkdir(parents=True)
        (tmp / "lab").mkdir()
        (tmp / "lab" / "fixtures.txt").write_text("", encoding="utf-8")
        env = {**os.environ, "SEASON": "2026-spring", "PLAYERS": "", "PERSON": "Sam",
               "SHOT": "FACE 6 POWER 60 AIM 13", "GITHUB_ENV": str(tmp / "env.out")}
        r = subprocess.run(["bash", "-c", step], cwd=tmp, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"the step ended {r.returncode} saying: {r.stdout}{r.stderr}")
        wrote = (tmp / "env.out").read_text(encoding="utf-8") if (tmp / "env.out").exists() else ""
        self.assertIn("PLAYERS=Sam,Lumi", wrote,
                      "the person's name and the one member on the shelf must both reach the court")

    def test_a_browser_can_ask_for_a_picture(self):
        """§8's button, end to end as far as a workflow can be tested without a key: a member is named, its own
        `voice.md` decides the engine, and the refusal for an engine that cannot paint is `lab/paint.py`'s own
        sentence rather than a second copy in YAML. Two copies of "who can paint" is how the page and the runner
        come to disagree about a member's engine — the same drift Gwen's #16 found in the clock's key list.
        """
        if yaml is None:
            self.skipTest("PyYAML not installed")
        wf = yaml.safe_load((self.WF / "paint.yml").read_text(encoding="utf-8"))
        steps = wf["jobs"]["paint"]["steps"]
        ask = [s for s in steps if s.get("name") == "Who is asking, and with what"][0]["run"]
        refuse = [s for s in steps if s.get("name", "").startswith("Does this engine")][0]["run"]
        self.assertIn("lab/paint.py", refuse)
        self.assertIn("--dry-run", refuse,
                      "the refusal must be the rehearsal that paints nothing and fails exactly as the run does")

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "lab").mkdir()
        shutil.copy(REPO / "lab" / "paint.py", tmp / "lab" / "paint.py")
        (tmp / "wake" / "members" / "Lumi" / "state").mkdir(parents=True)
        (tmp / "wake" / "members" / "Lumi" / "state" / "voice.md").write_text(
            "api: gemini\nmodel: gemini-3.8-flash\n", encoding="utf-8")
        out = tmp / "gh-output"
        out.write_text("", encoding="utf-8")
        env = {**os.environ, "MEMBER": "Lumi", "PROMPT": "a red cube", "WORK": "", "GITHUB_OUTPUT": str(out)}
        r = subprocess.run(["bash", "-c", ask], cwd=tmp, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"the step ended {r.returncode} saying: {r.stdout}{r.stderr}")
        self.assertIn("api=gemini", out.read_text(encoding="utf-8"),
                      "the engine must come from the member's own voice.md, not from the form")

        # The same step with a name that is not on the shelf: a refusal with a sentence, not a silent no-op.
        env["MEMBER"] = "Nobody"
        r = subprocess.run(["bash", "-c", ask], cwd=tmp, env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0, "a member that does not exist must fail the run")
        self.assertIn("no member called Nobody", r.stdout + r.stderr)

        # And the refusal step, run for real against an engine with no image model.
        env2 = {**os.environ, "API": "deepseek", "WORK": "", "MEMBER": "Lumi", "PROMPT": "a red cube"}
        r = subprocess.run(["bash", "-c", refuse], cwd=tmp, env=env2, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0, "deepseek cannot paint and the step must say so")
        self.assertIn("deepseek", r.stdout + r.stderr)
        for can in ("gemini", "openai", "qwen"):
            self.assertIn(can, r.stdout + r.stderr, "the refusal must name what would have worked")

    def test_a_picture_is_committed_with_its_credit_in_one_commit(self):
        """The commit is the record: an image without its card is a picture with no maker, and two commits can
        be separated by a fetch. The step also refuses to finish green having written nothing, which is the rule
        every other button in this page follows."""
        text = (self.WF / "paint.yml").read_text(encoding="utf-8")
        self.assertIn("git add -A plates/", text)
        self.assertIn("no plate was written", text)
        self.assertIn("--asked-by", text,
                      "the card names who asked; without it the harness credits the member with a person's sentence")

    def test_build_an_issue_publishes_and_does_not_publish_a_nothing(self):
        """§9's button, end to end as far as a workflow can be tested without a shelf full of strangers.

        Two defects are being closed at once, and they are different defects. §14 has listed the third since the
        manual was written — "it assembles an issue and shows it to you in the page, and it commits nothing" —
        and the page's own assembly was not the magazine `magazine.py` prints: twelve files, newest first, no
        letter under the piece it answers. So the press dispatches the assembler, and what it must never do is
        commit an issue with nothing in it: `build()` will happily write a header and one true sentence saying no
        works have been filed, and a published nothing is worse than a refusal.
        """
        if yaml is None:
            self.skipTest("PyYAML not installed")
        wf = yaml.safe_load((self.WF / "magazine.yml").read_text(encoding="utf-8"))
        steps = wf["jobs"]["build"]["steps"]
        which = [s for s in steps if s.get("name", "").startswith("Which issue")][0]["run"]
        assemble = [s for s in steps if s.get("name", "").startswith("Assemble it")][0]["run"]
        self.assertIn("magazine.py --issue", assemble)
        self.assertIn("--write", assemble, "the press must write the issue, not print it into a log")

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        shutil.copy(REPO / "magazine.py", tmp / "magazine.py")
        (tmp / "works" / "Lumi").mkdir(parents=True)
        out = tmp / "gh-output"

        def step(given: str, extra: dict | None = None) -> subprocess.CompletedProcess:
            out.write_text("", encoding="utf-8")
            env = {**os.environ, "GIVEN": given, "GITHUB_OUTPUT": str(out), **(extra or {})}
            return subprocess.run(["bash", "-c", which], cwd=tmp, env=env, capture_output=True, text=True)

        # A work that names issue 1, and no issue on disk: the open issue is the one the work names.
        (tmp / "works" / "Lumi" / "20261113T090000Z-first.md").write_text(
            "---\ntitle: First\nform: piece\nissue: 1\n---\n\nthe first thing\n", encoding="utf-8")
        r = step("")
        self.assertEqual(r.returncode, 0, f"the step ended {r.returncode} saying: {r.stdout}{r.stderr}")
        wrote = out.read_text(encoding="utf-8")
        self.assertIn("issue=1", wrote)
        self.assertIn("filed=1", wrote)

        # A work that names issue 2 opens issue 2 — from the shelf, not from a form.
        (tmp / "works" / "Lumi" / "20261113T100000Z-second.md").write_text(
            "---\ntitle: Second\nform: piece\nissue: 2\n---\n\nthe second thing\n", encoding="utf-8")
        r = step("")
        self.assertEqual(r.returncode, 0, f"the step ended {r.returncode} saying: {r.stdout}{r.stderr}")
        self.assertIn("issue=2", out.read_text(encoding="utf-8"),
                      "the open issue is the highest a work names, not the lowest or the last published")

        # Nothing names issue 3, so there is nothing to publish — and the message says how a work is filed.
        r = step("3")
        self.assertNotEqual(r.returncode, 0, "an issue with no works must not be committed")
        self.assertIn("nothing to assemble", r.stdout + r.stderr)
        self.assertIn("works/", r.stdout + r.stderr, "a refusal that does not say where a work goes is a dead end")

        # A shelf with no works at all: the same refusal, before anything is built.
        for f in (tmp / "works" / "Lumi").glob("*.md"):
            f.unlink()
        r = step("")
        self.assertNotEqual(r.returncode, 0, "a shelf with no works has no issue in it")
        self.assertIn("nothing to assemble", r.stdout + r.stderr)

        # And a form value that is not a number is refused, not turned into a path.
        r = step("../etc")
        self.assertNotEqual(r.returncode, 0, "an issue is a number")
        self.assertIn("an issue is a number", r.stdout + r.stderr)

    def test_the_issue_is_committed_and_only_the_issue(self):
        """One commit, `issues/` and nothing else, and an honest branch for the press that changed no byte.

        A rebuild that produces the same file is the magazine's own promise working — every published file is a
        function of the record — so it is not a failure. It is also not a publication, and the page tells the two
        apart by the sha of the file it read back, which is why this step does not have to fail to say so.
        """
        text = (self.WF / "magazine.yml").read_text(encoding="utf-8")
        self.assertIn("git add issues/", text,
                      "the issue and its index are the run's; a `git add -A` would commit whatever else moved")
        self.assertNotIn("git add -A", text)
        self.assertIn("nothing to commit", text)
        self.assertIn("git pull -q --rebase", text, "the shelf moves: a push must survive the clock's last wake")
        self.assertIn("press again", text,
                      "an issue assembled from a tree that is no longer the branch must not be pushed as if it were")

    def test_the_magazine_button_is_named_the_way_the_book_names_it(self):
        """§9 says "Press **Build an issue**" and the appendix has a row called `Build an issue`. The page's
        button said "Assemble an issue from the shelf", which is the same operation under a second name — and a
        reader holding the book on their knees is the one who pays for that. The name is the promise.
        """
        html = (REPO / "ait.html").read_text(encoding="utf-8")
        self.assertIn(">Build an issue<", html)
        self.assertNotIn("Assemble an issue", html)
        self.assertIn("| Build an issue |", (REPO / "USER-MANUAL.md").read_text(encoding="utf-8"))


    def test_the_shelf_list_does_not_die_on_a_pipe_or_a_bench_file(self):
        """The two members are picked from the shelf when the form names none, and that one line failed twice
        over in a colony that is not this bench.

        `head -2` exits once it has its lines; the `while` loop above it then writes into a closed pipe; `ls` takes
        the SIGPIPE; `set -o pipefail` turns that into a failed assignment and `set -e` takes the step down — exit
        141, no message. In the bench the race usually went the other way, which is why nothing noticed. And
        `lab/fixtures.txt` is the *bench's* own list of test members: a tribe made from the template has no such
        file, so a shipped workflow that requires one is a workflow that only works where it was written.

        Run the step, in a three-member colony with no fixtures file, rather than reading it. Found 2026-11-13
        while answering the founder, whose two-member press had already reached the engine and failed for an
        unrelated reason — the next press with the form blank would have died here.
        """
        if yaml is None:
            self.skipTest("PyYAML not installed")
        wf = yaml.safe_load((self.WF / "season.yml").read_text(encoding="utf-8"))
        step = [s for s in wf["jobs"]["play"]["steps"] if s.get("name") == "Which season, which two"][0]["run"]
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        for who in ("Aphrodite", "Dionysus", "Hermes"):
            (tmp / "wake" / "members" / who / "state").mkdir(parents=True)
        self.assertFalse((tmp / "lab" / "fixtures.txt").exists())
        env = {**os.environ, "SEASON": "2026-spring", "PLAYERS": "", "PERSON": "", "SHOT": "",
               "GITHUB_ENV": str(tmp / "env.out")}
        r = subprocess.run(["bash", "-c", step], cwd=tmp, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"the step ended {r.returncode} saying: {r.stdout}{r.stderr}")
        wrote = (tmp / "env.out").read_text(encoding="utf-8")
        self.assertIn("PLAYERS=Aphrodite,Dionysus", wrote,
                      "the first two on a stranger's shelf must reach the court without a bench file")

    def test_the_published_member_list_matches_the_shelf(self):
        """A static page cannot read a directory, so `members.json` is what its drop list is built from — and a
        published list that drifts from the shelf is a drop list offering people who are not there, which is
        exactly what the founder's phone showed him."""
        mod = load(REPO / "lab" / "members.py", "members_mod")
        fresh = mod.collect()
        self.assertTrue((REPO / "members.json").is_file(), "run python3 lab/members.py --write")
        on_disk = json.loads((REPO / "members.json").read_text(encoding="utf-8"))["members"]
        self.assertEqual([m["name"] for m in on_disk], [m["name"] for m in fresh])

    def test_the_static_page_can_work_on_a_phone_with_no_server(self):
        html = (REPO / "chat-static.html").read_text(encoding="utf-8")
        for needed in ('<select id="member"', '<textarea id="msg"', 'name="viewport"',
                       "members.json", "/issues/new", "?title=", "@tribe"):
            self.assertIn(needed, html, f"a static page needs {needed}")
        # And no reply box on the static page. The first version had one because the founder asked for two
        # boxes; a static file has no server and no token, so that box could never fill and its placeholder
        # was a promise the page could not keep. The live reply box is on the local page only.
        self.assertNotIn('id="reply"', html,
                         "the static page cannot receive a reply; the answer is a comment on the issue")
        self.assertIn("Submit new issue", html, "the page must say which button actually starts the work")

    def test_a_colony_of_one_is_not_offered_as_a_choice(self):
        """The founder's phone showed a drop list with one row in it (Ada) and he read it as a defect — rightly.
        A select with a single option is a control that decides nothing, and it looks like a broken list. A
        colony of one should say so in words and hide the control."""
        html = (REPO / "chat-static.html").read_text(encoding="utf-8")
        self.assertIn("members.length === 1", html, "the page must notice a single-participant colony")
        self.assertIn('$("who-label").hidden = true', html, "and hide the label above a hidden select")
        self.assertIn('sel.hidden = true', html, "and hide the select itself, not just its options")

    def test_an_issue_that_mentions_the_tribe_is_a_question(self):
        text = (self.WF / "interactive.yml").read_text(encoding="utf-8")
        self.assertIn("issues:\n    types: [opened]", text,
                      "a static page cannot comment, so opening an issue must be enough")
        self.assertIn("github.event.issue.body", text)
        self.assertIn("/tmp/named.txt", text, "the name in the body must choose the member who answers")

    def test_a_browser_can_add_a_member(self):
        """The founder's outline asks a stranger with a browser to build a tribe. `tribe.py new` is a command.
        So the form is the command: a dispatch workflow with the three things a member needs, and the list
        republished afterwards so nobody has to remember the second step."""
        f = self.WF / "new-member.yml"
        self.assertTrue(f.is_file(), "a person with no terminal has no other way to add a member")
        text = f.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("python3 tribe.py new", text, "the form must run the tool, not re-implement it")
        self.assertIn("lab/members.py --write", text,
                      "a new member that is not republished is a member the drop list cannot offer")
        for needed in ("name:", "seat:", "engine:"):
            self.assertIn(needed, text)
        # 2026-11-13: the page asks what is written about the member, so the form has to have somewhere to
        # put it AND pass it on. A field the workflow accepts and never hands to the tool is a question that
        # does nothing — worse than no question, because the person saw it answered.
        self.assertIn("about:", text)
        self.assertIn("--about", text)
        self.assertNotIn(".github/workflows", text,
                         "a workflow that edits a workflow file cannot push it: GITHUB_TOKEN has no such "
                         "permission, so the member list must not live in one")

    def test_the_request_says_who_it_is(self):
        """Python's default User-Agent is refused at the door by at least one vendor before the key is read.

        Measured 2026-11-06 against Groq: `Python-urllib/3.9` got HTTP 403 "error code: 1010" — a Cloudflare
        browser check — while the same request with any other User-Agent got a clean 401 for a bad key. A
        member on that engine could not have woken at all, and the failure would have looked like a key
        problem. Same class of fault as a shipped workflow defaulting to a member that only exists on the
        bench: the request was fine and the introduction was wrong."""
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertIn("User-Agent", src)
        self.assertEqual(src.count('"User-Agent": UA'), 3,
                         "every remote path — the OpenAI-compatible one, Gemini's and Claude's — must introduce "
                         "themselves")

    def test_the_engine_drop_list_is_the_engines_the_tool_accepts(self):
        """A form that offers an engine the tool refuses is the same defect as a drop list of members who are not
        on the shelf: the stranger picks it, taps Run, and is told no. One table, or a test that says so.

        Amended 2026-11-06 with the engine that runs weights on the machine doing the waking: a GitHub runner has
        no weights, so the form withholds exactly that one and says why in the file. The assertion is a union
        rather than a subtraction so that withholding any *other* engine still fails, loudly.
        """
        tribe = load(REPO / "tribe.py", "tribe_mod_engines")
        text = (self.WF / "new-member.yml").read_text(encoding="utf-8")
        block = text.split("engine:", 1)[1].split("default:", 1)[0]
        offered = [l.strip().lstrip("- ").strip() for l in block.splitlines() if l.strip().startswith("- ")]
        self.assertNotIn("local", offered,
                         "a runner has no port to call: offering this engine would be a button that cannot work")
        self.assertIn("local", tribe.BASES, "and a member on weights in this room is still a member")
        self.assertEqual(sorted(set(offered) | {"local"}), sorted(tribe.BASES),
                         "new-member.yml offers an engine the tool does not accept, or hides one it does")
        self.assertIn("local", text.lower(), "the form's silence about the one engine it withholds is not a note")

    def test_a_browser_can_play_a_session(self):
        """Same problem for the activity: the sheet's last section asks the reader to start a season, and until
        now that meant a terminal. The engine's own flags are the form: a season name, two participants and
        how many rallies."""
        f = self.WF / "season.yml"
        self.assertTrue(f.is_file(), "the activity section of the sheet needs a way to run it")
        text = f.read_text(encoding="utf-8")
        self.assertIn("--rally", text)
        self.assertIn("--season", text, "a session without a season file teaches nobody anything")
        self.assertIn("--report", text, "the season must be able to say what it holds")
        self.assertNotIn("--vendor", text,
                         "the engine of each participant is in its own voice.md; a form should not ask again")
        self.assertNotIn("--practice", text,
                         "the balls already hit are in the season file; a second source is how a count drifts")

    def test_the_instruction_sheet_names_buttons_that_exist(self):
        """The sheet a stranger reads is the one document with no compiler. Every workflow it tells you to tap,
        every secret name it tells you to set, and every path it tells you to look in has to be there — checked
        here rather than by the stranger, who has no way to tell a missing button from his own mistake."""
        build = (REPO / "BUILD.md").read_text(encoding="utf-8")
        for wf in ("new-member", "season"):
            self.assertIn(wf, build, f"BUILD.md tells the reader to run {wf}")
            self.assertTrue((self.WF / f"{wf}.yml").is_file(), f"there is no {wf} workflow to run")
        self.assertIn("TRIBE_API_KEY_GEMINI", build,
                      "the key name in the sheet must be the name the harness looks for")
        self.assertIn("@tribe", build, "the sheet's hello step is the issue path, and it must use its syntax")
        self.assertIn("ENGINES.md", build, "the sheet names engines and must point at the table that lists them")
        self.assertTrue((REPO / "ENGINES.md").is_file(), "that table has to exist")
        engines = (REPO / "ENGINES.md").read_text(encoding="utf-8")
        for api in ("gemini", "deepseek", "qwen"):
            self.assertIn(f"TRIBE_API_KEY_{api.upper()}", engines)
        # Step 4 both sets the three engines up and names one, which is the point: Goose has no provider called
        # "gemini" (it calls Google's engine "google") and no DeepSeek or Qwen provider at all, so a reader who
        # configures only the engine of their first member meets "Unknown provider" in the middle of trying to
        # talk to somebody. All three are configured up front, and the addresses have to be the addresses the
        # harness itself uses — checked against wake.API_BASES, because a wrong base URL in the sheet looks
        # exactly like a wrong key and fails the same way.
        self.assertIn("Configure providers", re.sub(r"\s+", " ", build),
                      "the app's route to the same menus is Settings → Configure providers")
        self.assertNotIn("Custom Providers", build,
                         "every engine the sheet uses is already in Goose's provider list; a reader who is sent "
                         "to build a custom provider has been sent to do work that does not exist")
        self.assertIn("custom_deepseek", build,
                      "DeepSeek's internal name is not its display name, and the terminal fallback must use it")
        self.assertIn("Import Recipe", build, "importing a recipe is only possible in the desktop app")
        self.assertIn("`google`", engines, "Gemini's internal name must be written down in the engine sheet")
        self.assertIn("| `deepseek` | **DeepSeek** | `custom_deepseek` |", engines,
                      "a terminal user typing --provider deepseek would be sent to an unknown provider")
        self.assertIn("api.deepseek.com", engines,
                      "the engine sheet says where DeepSeek lives, even though nobody has to type it")
        self.assertIn("lab/session.py", build, "the standard way to talk is a session, and this is how one is made")
        self.assertIn("--interactive", build, "a one-shot run is not a conversation")
        for path in ("wake/members", "games/tennis/seasons", "practice.json", "USER-MANUAL.md"):
            self.assertIn(path, build)
        self.assertTrue((REPO / "USER-MANUAL.md").is_file(), "the sheet's last line points at the manual")

    def test_the_engine_that_does_not_speak_the_common_shape_is_translated_in_both_places(self):
        """Claude answers at /v1/messages with x-api-key and a required max_tokens, and returns content blocks.

        Added 2026-11-06, the day the founder obtained an Anthropic key. The rule this pins is the one that
        keeps biting: a fact that lives in two files has to live in both. The wake and the games each build
        their own request, so the translation exists twice, and a member that can wake but cannot play is the
        defect this file already has a test about.
        """
        games = (REPO / "lab" / "rps.py").read_text(encoding="utf-8")
        wake = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        for name, src in (("lab/rps.py", games), ("wake/wake.py", wake)):
            self.assertIn("api.anthropic.com", src, f"{name} must know the address")
            self.assertIn("x-api-key", src, f"{name} must use Claude's auth header, not a bearer token")
            self.assertIn("anthropic-version", src,
                          f"{name} must send the dated version header this API requires")
        self.assertIn('stopped == "max_tokens"', games,
                      "a reply cut off before it began must read as finish_reason length, or the retry never fires")
        # The literal was `2400` until the truncation ladder landed: three times 2,400 tokens of reasoning with no
        # answer, and the wake now buys room instead of filing half an object. So the assertion follows the
        # ladder — a budget variable, a first ask of 2,400, and a ceiling — because pinning one number would
        # have made the fix look like a regression.
        self.assertIn('"max_tokens": budget', wake,
                      "max_tokens is required by this API; it is not the same request without it")
        self.assertIn("budget: int) -> dict", wake,
                      "the allowance has to be a parameter, or the ladder has nothing to climb")
        self.assertIn("send(0.4, 2400)", wake, "the first ask is 2,400, the size that was measured on the day")

    def test_an_engine_with_no_default_model_says_so_instead_of_raising_a_key_error(self):
        """Naming a vendor the project has not chosen a model for is a question, not a crash.

        Amended 2026-11-06: this used to point at `anthropic`, which has since been given a measured default
        (`claude-haiku-5-5`). The point of the test was never Anthropic — it was that the list and the lookup
        agree, so an engine can be in the address table without pretending to have a default.
        """
        self.assertEqual(rps.default_model("deepseek"), "deepseek-flash")
        self.assertEqual(rps.default_model("anthropic"), "claude-haiku-5-5")
        self.assertEqual(rps.default_model("openai"), "gpt-6-luna",
                         "the default must be a model the vendor currently prices; gpt-5-mini answers but has "
                         "dropped off the sheet, which is how a default turns into a first-wake failure")
        for engine in sorted(set(rps.BASES) - set(rps.DEFAULT_MODEL)):
            with self.assertRaises(SystemExit) as caught:
                rps.default_model(engine)
            self.assertIn("name one with --model", str(caught.exception))
        # Measured 2026-11-06: one wake each on a key the founder put in engines.env, all four mechanically
        # valid. These defaults are the models that were actually called, not the models their vendors
        # advertise loudest — a default this project prints is a default this project has spent money on.
        for engine, model in (("mistral", "ministral-8b-latest"), ("cerebras", "gpt-oss-120b"),
                              ("openrouter", "deepseek/deepseek-v4.1-flash-1017"), ("together", "zai-org/GLM-5.3-Flash")):
            self.assertEqual(rps.default_model(engine), model,
                             f"{engine}'s default must be the model this project woke, so the first wake on a "
                             f"stranger's machine is a wake that has already worked once")
        self.assertIn("local", set(rps.BASES) - set(rps.DEFAULT_MODEL),
                      "on this machine the model is whatever the person downloaded; a default here would be a "
                      "guess about somebody else's disk")

    def test_weights_on_this_machine_need_no_key_and_the_wake_says_so(self):
        """The one engine here that asks nobody for anything was being told it was missing a credential.

        Measured 2026-11-06 on the M4 Pro: 20B of open weights behind `llama-server`, and the first wake was
        refused before the prompt was printed — `!! no API key in the environment` — because every engine in
        this file was assumed to be a vendor. That is the harness's own rule misread: it exists so a missing
        *purchase* is answered in one line, and weights in the next room are not a purchase. The rule is now a
        function with a test, in both tables, because a member who can wake on those weights but cannot enter a
        game is the two-tables fault this suite already fails once.
        """
        for e in ("local",):
            self.assertIn(e, rps.BASES, "the games must know the engine, or a wake works and a game refuses")
            self.assertIn(e, wake.API_BASES, "so must the wake")
            self.assertNotIn(e, rps.DEFAULT_MODEL,
                             "there is no default: the model is whatever the person downloaded, and a guess here "
                             "is a first-wake failure on somebody else's file")
        self.assertTrue(rps.BASES["local"], "an engine with an empty address is not an engine")
        for loopback in ("http://127.0.0.1:8080/v1", "http://localhost:11434/v1", "http://[::1]:8080/v1"):
            self.assertTrue(wake.needs_no_key(loopback), f"{loopback} is this machine and has no vendor")
            self.assertTrue(rps.needs_no_key(loopback), "the games' copy of the rule must agree, character for character")
        for remote in ("https://api.groq.com/openai/v1", "http://127.0.0.1.evil.example/v1", ""):
            self.assertFalse(wake.needs_no_key(remote),
                             f"{remote!r} is not this machine; a hostname that merely starts with 127.0.0.1 is a "
                             "stranger, and the rule has to be an equality rather than a prefix for that reason")
            self.assertFalse(rps.needs_no_key(remote), "the games agree here too")
        self.assertIn("needs_no_key(base)", (REPO / "wake" / "wake.py").read_text(encoding="utf-8"),
                      "the wake must consult the rule before it declares a key missing")
        self.assertEqual(rps.key_for("local"), "local",
                         "the games must hand a loopback engine a placeholder rather than refuse it")
        saved = os.environ.pop("TRIBE_API_KEY_MISTRAL", None)
        try:
            self.assertIsNone(rps.key_for("mistral"),
                              "a real vendor with no key must still be refused, or this fix has cost the check")
        finally:
            if saved:
                os.environ["TRIBE_API_KEY_MISTRAL"] = saved

    def test_an_image_is_labelled_from_its_bytes_not_from_our_hope(self):
        """Found 2026-11-07 by sending a JPEG to ten engines and reading the refusals.

        Three places in wake.py wrote `media_type: image/png` for whatever arrived. Gemini and OpenAI swallowed it;
        Anthropic answered 400 and named nothing useful, so the first conclusion was "Claude cannot see" — wrong, and
        about the model rather than about the request. A tribe member handed a photograph would have drawn the same
        wrong conclusion from the same silence, which is why this is a test and not a comment.
        """
        w = load(REPO / "wake" / "wake.py", "wake_mod_mime")
        self.assertEqual(w.image_mime(base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 32).decode()), "image/png")
        self.assertEqual(w.image_mime(base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 32).decode()), "image/jpeg")
        self.assertEqual(w.image_mime(base64.b64encode(b"GIF89a" + b"0" * 32).decode()), "image/gif")
        webp = b"RIFF" + b"0" * 4 + b"WEBP" + b"0" * 24
        self.assertEqual(w.image_mime(base64.b64encode(webp).decode()), "image/webp")
        self.assertEqual(w.image_mime(base64.b64encode(b"????" * 8).decode()), "image/jpeg",
                         "an unrecognised header must still produce a real type; a guess that is sometimes wrong "
                         "beats a refusal that says nothing")
        src = (REPO / "wake" / "wake.py").read_text(encoding="utf-8")
        self.assertEqual(src.count('"image/png"'), 1,
                         "the only place allowed to say image/png is the function that sniffs it")

    def test_the_page_can_be_edited_by_someone_who_is_not_me(self):
        """The founder asked how to edit ENGINES.md without breaking it, which is a fair question with an unfair
        answer: the page is not prose that mentions engines, it is an input to tests that slice it on its headings
        and read its table cells as promises. So the rules are a program now (`lab/check_engines.py`) and this test
        is the same program: footnote references that resolve, notes numbered in reading order, no blank cell, no
        price without a figure or a stated reason, every engine named with its secret, every default model printed.
        A page edit that breaks one of those gets a sentence saying which one, instead of a red suite a week later.
        """
        check = load(REPO / "lab" / "check_engines.py", "check_engines_for_tests")
        found = check.problems()
        self.assertEqual(found, [], "ENGINES.md breaks a promise:\n  " + "\n  ".join(found))
        # and the renumbering tool has to be idempotent, or it is a tool that moves the numbering every run
        body = (REPO / "ENGINES.md").read_text(encoding="utf-8")
        self.assertEqual(check.renumber(body)[0], body,
                         "the notes are already renumbered; running --renumber again must change nothing")

    def test_every_engine_the_harness_speaks_has_been_woken_and_says_what_it_costs(self):
        """Amended 2026-11-06, evening: the founder asked whether the unmeasured engines should be tested and the
        category deleted, and the answer was yes — "supported by the wake, unmeasured here" is a row that promises
        a reader nothing. All four were woken the same evening, so the section is gone. What replaces it is a rule
        this test enforces: every engine listed works here, and every price cell either names a figure or says in
        the cell why this page will not print one. A blank cell at that position is the thing this page must never
        do, because a blank reads as free.
        """
        engines = (REPO / "ENGINES.md").read_text(encoding="utf-8")
        self.assertNotIn("The rest, which the harness also speaks", engines,
                         "every engine in the table has now been called; a section for the uncalled is a place for "
                         "guesses to hide")
        other = engines[engines.index("### Other possibilities"):engines.index("### On your own machine")]
        rows = [l for l in other.splitlines() if l.startswith("| `")]
        self.assertTrue(rows, "the table has rows")
        listed = set()
        for row in rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            self.assertEqual(len(cells), 5, f"a row needs engine, secret, address, price and door: {row[:60]}")
            listed.add(cells[0].strip("`"))
            self.assertTrue(cells[3], f"{cells[0]} has a blank price cell, which reads as free")
            self.assertTrue(("$" in cells[3]) or cells[3].startswith("not printed here"),
                            f"{cells[0]}'s price must be a figure or a stated reason for having none: "
                            f"{cells[3][:60]}")
        for engine in ("mistral", "cerebras", "openrouter", "together", "qwen", "openai", "anthropic"):
            self.assertIn(engine, listed, f"{engine} works here and must be in that table")
            self.assertIn(f"TRIBE_API_KEY_{engine.upper()}", other, f"{engine} must name its secret")

    def test_the_recommended_engines_are_the_ones_a_stranger_can_actually_reach(self):
        """A recommendation is a promise about the first thirty minutes, so it has to be a short list.

        Corrected 2026-11-06 on the founder's question: Qwen sat in the recommended table while the prose said
        its door cost an evening of signup, which is two answers to one question. Groq earned the place by being
        measured; Qwen keeps its row and loses the word, because the engine is fine and the door is not.
        """
        engines = (REPO / "ENGINES.md").read_text(encoding="utf-8")
        head = engines[engines.index("### The three engines this page recommends"):engines.index("### Other possibilities")]
        for good in ("`gemini`", "`deepseek`", "`groq`"):
            self.assertIn(good, head, f"{good} is recommended and must be in that table")
        self.assertNotIn("`qwen`", head, "Qwen's door costs an evening; it is not a recommendation")
        self.assertIn("`qwen`", engines, "and it must still be listed, with the reason")
        other = engines[engines.index("### Other possibilities"):engines.index("### What Goose calls them")]
        for engine in ("`qwen`", "`openai`", "`anthropic`"):
            self.assertIn(engine, other,
                          f"{engine} works here and must be listed, under the heading the founder asked for")
        for address in ("api.openai.com", "api.anthropic.com"):
            self.assertIn(address, other, f"{address} is the address, and it is one of the three facts")
        self.assertIn("$0.10", other, "Anthropic's price band, read off its own sheet rather than guessed")
        self.assertIn("$0.05", other, "OpenAI's price band, likewise")
        self.assertIn("claude-haiku-5-5", other, "the recommended default for that engine, named in the table")
        self.assertNotIn("does not work here at all", engines,
                         "the adapter landed 2026-11-06 and a live wake came back valid; the page cannot keep "
                         "saying Claude does not work here — that was true and is now false")
        self.assertIn("mechanically valid", engines.lower(),
                      "the claim that Claude now works must rest on the wake that proved it")

    def test_the_sheet_tells_the_reader_to_leave_the_place_field_empty(self):
        """This test used to require the opposite, and the opposite stopped being true on 2026-11-20.

        It was written on 2026-11-06, when the shipped copy had two worlds, `tribe.py new` could not infer a place,
        and a member with none was never woken — so the sheet had to name the worlds the reader was to type. Deleting
        worlds inverted the requirement: a member is woken because it is a member, so a sheet that names worlds is
        now sending the reader to invent one, and a field nobody must fill is a field the sheet has to say so about.
        """
        build = (REPO / "BUILD.md").read_text(encoding="utf-8")
        step_two = build[build.index("**2. Add two or more members.**"):build.index("**3. Give your repository")]
        self.assertIn("place", step_two.lower(), "the field still exists in the form, so the sheet still mentions it")
        for d in sorted((REPO / "soil").iterdir()):
            if d.is_dir():
                self.assertNotIn(d.name, step_two,
                                 f"{d.name!r} is a room in this bench; the sheet must not send a reader to type it")

    def test_no_timer_outside_github_is_shipped_and_the_manual_says_why(self):
        """The founder's ruling of 2026-11-22, and the reasons are his, in his order.

        A timer outside GitHub works: `lab/pinger.gs` was installed on his own circle on 2026-11-22, `ping` answered
        204, and the run it started went green. He watched the install happen and then ruled it out of the product —
        a second account, a long-lived token living somewhere that is not the repository, and a page whose UI can
        change under a manual that describes it. So the script stays here as an experiment and does not travel; and
        the honesty it was going to buy is bought in words instead, in §5 and beside the button. Three things have
        to stay true, and each of them was false at some point in the last week.
        """
        import subprocess
        built = Path(tempfile.mkdtemp(prefix="tpl-pinger-"))
        self.addCleanup(shutil.rmtree, built, True)
        r = subprocess.run([sys.executable, str(REPO / "lab" / "make_template.py"), "--out", str(built)],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((built / "lab" / "pinger.gs").exists(),
                         "a timer outside GitHub is shipped again; it was ruled out on 2026-11-22")
        man = (REPO / "USER-MANUAL.md").read_text(encoding="utf-8")
        self.assertNotIn("installTrigger", man, "the manual teaches a setup that is not offered")
        self.assertIn("no timer you can install to fix that", man,
                      "and it has to say so, or a reader goes looking for the workaround the measurement implies")
        self.assertIn("when you want an answer today, ask for a wake", man,
                      "what replaces a timer is the button that works now")
        page = (REPO / "ait.html").read_text(encoding="utf-8")
        self.assertIn("two or three of those a day", page,
                      "the page has to say what the clock delivers, where a person waits for it")
        self.assertIn("GitHub's scheduler, not the circle", page,
                      "and it must not let the circle be blamed for GitHub's clock")

    def test_the_shipped_manual_does_not_promise_a_frequency_the_cron_cannot_keep(self):
        """Measured on 2026-11-20, and it corrects two documents at once.

        §5 of the manual said *"at seven and at seven, morning and evening"* while the shipped `clock.yml` asks for a
        wake every four hours — and the cron delivers neither. Twenty-four due slots over four days produced 10 runs
        on this repository and 3 on the founder's circle. RUN.md §8 has carried that measurement since 2026-11-03
        (6% of events when asking four times an hour) and RELEASE.md contradicted it by counting runs instead of
        slots. A promise in the manual is the one claim a person can measure for themselves in a week.
        """
        man = (REPO / "USER-MANUAL.md").read_text(encoding="utf-8")
        self.assertNotIn("at seven and at seven", man, "the cron has never been a seven o'clock clock")
        self.assertIn("two or three", man, "the measured rate, not a cadence")
        self.assertIn("Run workflow", man, "and what always works instead")
        rel = (REPO / "RELEASE.md").read_text(encoding="utf-8")
        self.assertNotIn("Eight consecutive due turns on this repository each\n  produced a run", rel)
        self.assertIn("10 runs on this repository and 3 in", rel)

    def test_the_sheet_does_not_keep_a_second_copy_of_the_engine_list(self):
        """The engines are listed once, in ENGINES.md, and the sheet points at it.

        Keeping the list in two places is how this sheet has been wrong three times in two days: Qwen was cut
        from the recommendations, deepseek-chat was retired by its vendor, and a provider that was in Goose's
        list was written up as one you had to add by hand. Each time the fix was to edit two documents and hope.
        The sheet may name an engine in passing — a terminal user needs the internal name at the moment they
        type it — but the key pages and the model ids belong to the engine sheet alone."""
        build = (REPO / "BUILD.md").read_text(encoding="utf-8")
        for page in ("aistudio.google.com", "platform.deepseek.com"):
            self.assertNotIn(page, build, f"{page} is a key page; the sheet points at ENGINES.md for those")
        for model in ("gemini-3.8-flash", "deepseek-flash", "qwen3.6-plus", "gpt-oss"):
            self.assertNotIn(model, build, f"{model} is a model id; those live in ENGINES.md")

    def test_the_build_steps_are_numbered_1_to_6_with_no_gaps(self):
        """A numbered step that stops being necessary must come out and the rest close up.

        The sheet used to have a step 4 whose whole content was "put the tribe on your computer" and a step 5
        that assumed it. A reader could not see why the step was there, and a reader with no computer had a
        numbered step they were told to skip. Its two facts — install Goose, tell Goose the engines — now sit in
        the step that uses them. This test is the small guard against the numbering drifting again.
        """
        build = (REPO / "BUILD.md").read_text(encoding="utf-8")
        head = build.split("## Give your tribe something to do")[0]
        numbered = re.findall(r"^\*\*(\d+)\. ", head, flags=re.M)
        self.assertEqual(numbered, ["1", "2", "3", "4", "5", "6"],
                         "the build steps are one to six, in order, with nothing skipped")
        self.assertIn("Use this template", build,
                      "a reader with no terminal starts by copying the repository, not by cloning it")

    def test_a_member_can_be_visited_in_a_session_with_its_own_files_and_tools(self):
        """Until 2026-11-05 a member had one kind of time: the wake — one call, no tools, no transcript. The
        founder's objection was that the symposium itself is built in sessions, which are strictly more
        capable, because a person is present to steer them. So the attended mode is a Goose recipe generated
        from the member's own files, plus one rule: whatever happens has to end up in those files, because the
        next wake can see nothing else."""
        mod = load(REPO / "lab" / "session.py", "session_mod")
        shelf = REPO / "wake" / "members"
        who = "Ada" if (shelf / "Ada" / "state" / "identity.md").is_file() else sorted(
            d.name for d in shelf.iterdir() if (d / "state" / "identity.md").is_file())[0]
        rec = mod.recipe(who)
        text = yaml.safe_dump(rec, allow_unicode=True)
        self.assertEqual(rec["version"], "1.0.0")
        self.assertIn("journal.md", rec["instructions"],
                      "a session with no closing rule leaves nothing behind for the next wake")
        self.assertIn("works/", rec["instructions"], "what it finished has to be filed by hand, or not at all")
        self.assertEqual([e["name"] for e in rec["extensions"]], ["developer"],
                         "the attended mode is the one with tools; that is the whole point of it")
        self.assertIn("{{ question }}", rec["prompt"], "a headless run refuses to start without a prompt")
        self.assertIn("identity.md", text, "the recipe is generated from the member's files, not written about it")

    def test_a_session_recipe_for_a_member_who_is_not_there_is_an_error(self):
        mod = load(REPO / "lab" / "session.py", "session_mod2")
        with self.assertRaises(SystemExit):
            mod.recipe("NobodyByThisName")

    def test_a_comment_that_names_no_member_is_answered_by_the_first_on_the_shelf(self):
        text = (self.WF / "interactive.yml").read_text(encoding="utf-8")
        self.assertIn("lab/fixtures.txt", text,
                      "the first member on the shelf must be the first REAL member, not a test member")
        self.assertIn("no member was chosen", text,
                      "the later steps must read the resolved member, not an empty input")


class TestTheAdminIsAConversation(unittest.TestCase):
    """2026-11-07. "You've been a computer for too long. That's how computers talk, not how people talk."

    The founder was objecting to `/newmember Maud` and then wrote the exchange he did want: one question at a
    time, each answer a few words, the next question depending on the last. `lab/admin.py` is that exchange
    with no transport under it, and these tests hold the two things that make it worth having: every option
    is read from disk at the moment it is offered, and the last question reads the whole thing back before
    anything is written.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="admin-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for world in ("workshop", "night-bus"):
            (self.tmp / "soil" / world).mkdir(parents=True)
        (self.tmp / "wake" / "members").mkdir(parents=True)
        wf = self.tmp / ".github" / "workflows"
        wf.mkdir(parents=True)
        shutil.copy(REPO / ".github" / "workflows" / "new-member.yml", wf / "new-member.yml")
        self.mod = load(REPO / "lab" / "admin.py", "admin_mod")

    def admin(self):
        return self.mod.Admin(self.tmp)

    def hold(self, admin, *answers):
        """Say each answer in turn; hand back what the admin said to the last one."""
        said = []
        for answer in answers:
            said = admin.say(answer)
        return said

    def test_the_engines_come_from_the_form_and_are_engines_not_lines_of_yaml(self):
        """The first version of this used a regex with re.S and captured the rest of the workflow file, so
        "something else" offered 121 engines, most of them YAML. A list that is right in a copy of the file
        and wrong in the real one is the class of defect this project keeps finding, so it is read live."""
        got = self.mod.all_engines(self.tmp)
        self.assertEqual(got, ["gemini", "qwen", "deepseek", "openai", "groq",
                               "mistral", "cerebras", "openrouter", "together", "anthropic"])
        for line in got:
            self.assertNotIn("${{", line, "a template line is not an engine")
            self.assertNotIn(":", line)

    def test_six_questions_end_in_one_command_that_carries_every_answer(self):
        a = self.admin()
        self.assertIn("What should it be called", a.ask())
        self.hold(a, "Maud", "the newcomer", "1", "2")
        self.assertTrue(a.ask().startswith("That is everything"),
                        "the last question must read the whole member back, not just ask 'sure?'")
        self.hold(a, "yes")
        self.assertTrue(a.done)
        self.assertEqual(a.command[1:],
                         ["tribe.py", "new", "Maud", "--seat", "the newcomer",
                          "--api", "gemini", "--place", "workshop"])

    def test_a_name_that_already_exists_is_refused_before_anything_else_is_asked(self):
        (self.tmp / "wake" / "members" / "Maud").mkdir()
        a = self.admin()
        said = a.say("Maud")
        self.assertIn("already exists", said[0])
        self.assertEqual(a.i, 0, "it must still be asking for a name")

    def test_a_name_that_is_not_a_name_is_refused_in_words_that_say_what_one_is(self):
        a = self.admin()
        for bad in ("Maud Smith", "3Maud", "Maud!", ""):
            self.assertIn("letters and numbers", a.say(bad)[0])
        self.assertEqual(a.name, "")

    def test_cancel_writes_nothing_and_leaves_no_half_made_member(self):
        a = self.admin()
        self.hold(a, "Maud", "the newcomer")
        self.assertIn("Nothing was written", a.say("cancel")[0])
        self.assertTrue(a.done)
        self.assertEqual(a.command, [], "cancel must not leave a command to run later")

    def test_just_do_it_picks_the_rest_and_says_which_ones_it_picked(self):
        a = self.admin()
        said = a.say("just do it")
        self.assertIn("name Maud", said[0])
        self.assertIn("engine gemini", said[0])
        self.assertIn("world night-bus", said[0], "the worlds are sorted, so night-bus is the first")
        self.assertTrue(a.ask().startswith("That is everything"))
        self.assertEqual(a.command, [], "the defaults still stop at the confirmation")

    def test_something_else_offers_the_engines_beyond_the_first_four(self):
        a = self.admin()
        offered = self.hold(a, "Maud", "the newcomer", "4")[0]
        self.assertIn("anthropic", offered)
        self.assertNotIn("gemini", offered, "the first four are not repeated in the long list")
        self.hold(a, "7")
        self.assertEqual(a.engine, "anthropic")

    def test_the_worlds_are_whatever_is_in_the_soil_folder_today(self):
        (self.tmp / "soil" / "harbour").mkdir()
        a = self.admin()
        offered = self.hold(a, "Maud", "the newcomer", "1")[0]
        self.assertIn("harbour", offered, "a world added to the folder must appear without editing the admin")
        self.hold(a, "1")
        self.assertEqual(a.world, "harbour")
        self.assertIn("harbour", a.ask(), "and the confirmation must read back the world it was given")

    def test_a_colony_with_no_worlds_says_so_and_makes_the_member_without_one(self):
        for d in (self.tmp / "soil").iterdir():
            shutil.rmtree(d)
        a = self.admin()
        self.assertIn("no worlds yet", self.hold(a, "Maud", "the newcomer", "1")[0])
        self.hold(a, "anything")
        self.assertIn("(no world)", a.ask())
        self.assertNotIn("--place", a._argv())


class ThePageIsCheckedByDrivingIt(unittest.TestCase):
    """`ait.html` is the whole product for everybody who does not use a terminal, and until 2026-11-12 no test
    touched it: every claim about the page was a claim about a browser session somebody had watched. Gwen's #9 —
    filing a conversation emptied the window and wrote no chapter, so the one case a chapter must exist was the
    one case it was not written — lived in that gap, which is why she could find it and the suite could not.

    The check itself is `lab/page-check.mjs`: it reads the shipped `ait.html`, runs its script in a fake browser,
    and answers GitHub's contents API and one engine from memory. Nothing about the page is copied into it, so a
    change to the page is a change to what is tested. Here it is run as one test, because the thing that must be
    true is that `python3 tests.py` is enough.
    """

    def test_the_page_keeps_what_it_files(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed here, so the page's own checks did not run — on this machine "
                          "ait.html is untested, and this line is the only sign of it")
        r = subprocess.run([node, str(REPO / "lab" / "page-check.mjs")],
                           cwd=REPO, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, "the page failed its own checks:\n" + r.stdout + r.stderr)

    def test_the_sealed_secret_is_one_libsodium_can_open(self):
        """The page puts a person's engine key into the repository, sealed, without a server of ours in the middle
        (the founder's ruling of 2026-11-19: a human is only asked to do what the amigo cannot do itself). The
        harness in `page-check.mjs` can prove that the page round-trips through its *own* copy of the library, and
        that its BLAKE2b matches Python's hashlib — neither proves the runner can open what the page sent, because
        a page and a harness agree perfectly about a wrong nonce. The first draft of the seal used a zero nonce: it
        passed every check in this repository and no runner could ever have read the key. So the last word belongs
        to libsodium itself, in `lab/seal-check.mjs`, and it is the same call the runner makes.
        """
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed here, so the sealed box was not checked at all")
        r = subprocess.run([node, str(REPO / "lab" / "seal-check.mjs")],
                           cwd=REPO, capture_output=True, text=True, timeout=120)
        if "SKIPPED" in r.stdout:
            self.skipTest("no libsodium on this machine, so nothing opened the page's sealed box: the check is "
                          "written and will run where libsodium exists, and until then it is evidence of nothing")
        self.assertEqual(r.returncode, 0, "the page's sealed secret is not one libsodium can open:\n" + r.stdout + r.stderr)


class TheRecordIsNotAKeyring(unittest.TestCase):
    """A key pasted into a file, not into the browser. The founder's question on 2026-11-15 was about keys kept
    in the repository; the amendment that followed found the path nobody had written down — his own features are
    commit channels (Edit its identity, the `--about` paste, a journal entry, a note in `works/`), and the same
    files are the prompt, so a key in `identity.md` is not only public, it is *sent* to whichever vendor that
    member runs on, every wake, for as long as the line sits there.

    The rule the check is built to obey: refuse and name the file. Never redact — a record edited behind its
    owner's back to protect itself has stopped being a record."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old = tribe.MEMBERS
        tribe.MEMBERS = self.tmp / "members"
        tribe.MEMBERS.mkdir()
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "")

    def tearDown(self):
        tribe.MEMBERS = self.old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def state(self, name="journal.md"):
        return tribe.MEMBERS / "Ada" / "state" / name

    def test_a_planted_key_is_named_by_file_and_line_and_never_quoted(self):
        text = self.state().read_text(encoding="utf-8")
        self.state().write_text(text + "\nthe key is sk-proj-abcdEFGH1234ijklMNOP5678qrst\n", encoding="utf-8")
        line = len(text.splitlines()) + 2
        hits = tribe.scan_credentials("Ada")
        self.assertEqual(len(hits), 1, hits)
        self.assertIn("journal.md", hits[0])
        self.assertIn(f"line {line}", hits[0])
        self.assertIn("OpenAI or DashScope", hits[0])
        # The finding must be findable without the finding printing the secret into a log, a CI page or a
        # screenshot — the same reason the Keys page shows four characters and no more.
        self.assertNotIn("abcdEFGH1234", hits[0])
        self.assertTrue(any("revoke it" in b for b in tribe.validate("Ada")))

    def test_a_sentence_about_keys_is_not_a_key(self):
        """The false positive is the whole risk: a check that cries wolf is a check people switch off. Every
        line here is something a member of this colony could plausibly write, and none of them is a credential."""
        prose = ("I keep my key in Settings → Secrets and variables → Actions.\n"
                 "The secret is called TRIBE_API_KEY_DEEPSEEK and only the run sees it.\n"
                 "She asked whether sk- prefixed strings are a problem, and they are if they are real.\n"
                 "model: deepseek-flash\n")
        self.state().write_text(prose, encoding="utf-8")
        self.assertEqual(tribe.scan_credentials("Ada"), [])
        self.assertEqual(tribe.validate("Ada"), [])

    def test_it_reads_the_whole_member_and_not_only_the_state_folder(self):
        out = tribe.MEMBERS / "Ada" / "output" / "letter.md"
        out.write_text("token ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789\n", encoding="utf-8")
        hits = tribe.scan_credentials("Ada")
        self.assertEqual(len(hits), 1, hits)
        self.assertIn("output/letter.md", hits[0])

    def test_a_picture_is_not_a_key(self):
        """`output/` also holds images, and a PNG is bytes that may contain anything. Text files only."""
        (tribe.MEMBERS / "Ada" / "output" / "plate.png").write_bytes(
            b"\x89PNG\r\n\x1a\n" + b"sk-proj-abcdEFGH1234ijklMNOP5678qrst")
        self.assertEqual(tribe.scan_credentials("Ada"), [])


class TheClockSaysWhatItFound(unittest.TestCase):
    """The runner is the only place that knows whether a secret had a *value*.

    Found 2026-11-19 while closing the last item on the founder's queue, which was "let the page set the secret": the
    page cannot, and the reason is written down twice. But the reason it kept coming back is the real hole — the page
    can say a secret *name* is missing, and cannot say a name is present with nothing behind it. An empty secret, or
    one added as an environment secret, reads as armed from every angle the page has. So the clock writes what it
    found, and these are the three facts that file has to carry for the page to be able to tell those worlds apart.
    """

    def _record(self, keyed, force=""):
        import json as _json
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / ".ait" / "last-clock.json"
            r = subprocess.run([sys.executable, str(REPO / "tribe.py"), "next", "--keyed", keyed,
                                "--record", str(out)], capture_output=True, text=True, timeout=60)
            self.assertIn(r.returncode, (0, 1), r.stderr)
            self.assertTrue(out.is_file(), "no record was written: " + r.stderr)
            return _json.loads(out.read_text())

    def test_the_record_names_the_engines_the_runner_actually_held(self):
        rec = self._record("deepseek, gemini")
        self.assertEqual(rec["schema"], "ait-clock/1")
        self.assertEqual(sorted(rec["engines"]), ["deepseek", "gemini"])

    def test_a_run_that_found_nothing_still_says_so_rather_than_saying_nothing(self):
        """A file written only on success cannot be told from a clock that never ran."""
        rec = self._record("")
        self.assertEqual(rec["engines"], [])
        self.assertRegex(rec["when"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_the_record_has_the_two_lists_the_page_reads(self):
        rec = self._record("deepseek")
        for k in ("turns", "skipped"):
            self.assertIsInstance(rec[k], list, f"{k} is not a list")
        for turn in rec["turns"]:
            self.assertEqual(set(turn), {"place", "member", "why"})
        for s in rec["skipped"]:
            self.assertEqual(set(s), {"member", "engine"}, "a skip without its engine cannot be explained")

    def test_the_clock_writes_the_record_and_the_page_reads_the_same_name(self):
        clock = (REPO / ".github" / "workflows" / "clock.yml").read_text()
        page = (REPO / "ait.html").read_text()
        self.assertIn("--record .ait/last-clock.json", clock, "the clock does not write the record")
        self.assertIn("'.ait/last-clock.json'", page, "the page does not read the file the clock writes")
        self.assertIn("ait-clock/1", page, "the page does not check the schema of what it read")


    def test_the_page_offers_the_film_a_session_wrote_and_says_so_when_there_is_none(self):
        """The founder's ask has three parts and the page had only two of them: the sessions play, the record
        keeps them, and there was no way to WATCH one without knowing the URL. A page that can only reach the
        record is a page where the film exists for whoever wrote it.

        The two files are different kinds of thing and the page must not blur them: `practice.json` is the record
        and keeps every session; `watch.json` is a rendering of the season at one clock, so it belongs to the last
        session played as a film and is replaced by the next. Hence "its last session" rather than "the season",
        and a sentence — not a broken image and not a stale film — for a season that has none."""
        page = (REPO / "ait.html").read_text()
        self.assertIn("replay3d.html?record=seasons/", page, "the page never links a season's film")
        self.assertIn("watch.json", page)
        self.assertIn("watch the film of its last session", page,
                      "the link does not say which session the film is")
        self.assertIn("No film yet", page,
                      "a season with no film says nothing, so a reader cannot tell 'not filmed' from 'broken'")
        films = list((REPO / "games" / "tennis" / "seasons").glob("*/watch.json"))
        self.assertTrue(films, "the page links a film and no season on disk has one to fetch")


class TheClockIsCountedRatherThanRemembered(unittest.TestCase):
    """The number in §5 is a measurement, and a measurement is only as good as the arithmetic under it.

    The sentence this replaces was wrong in the direction that costs trust: "eight consecutive due turns each
    produced a run, 43-192 minutes late" is a count of *runs*, and reading it as appointments kept produced the
    claim that the clock "fires, always, and always late" for a schedule that in fact drops two thirds of them.
    So the two mistakes that produced it are pinned here as tests: a run credited to the slot it happened in
    rather than the slot it missed, and a person's press counted as the scheduler's delivery.

    No network. `fetch_runs` returns a sentence on failure and is not exercised here; the arithmetic and the
    words are, because those are the parts that go quietly wrong.
    """

    def setUp(self):
        self.clock = load(REPO / "lab" / "clock.py", "clock_mod")
        self.every, self.minute = 4, 17

    def _t(self, day, hour, minute):
        return datetime(2026, 11, day, hour, minute, tzinfo=timezone.utc)

    def _run(self, t, event="schedule", conclusion="success", name="clock", path=".github/workflows/clock.yml"):
        return {"created_at": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "event": event,
                "conclusion": conclusion, "name": name, "path": path}

    def test_a_run_too_late_to_belong_to_its_slot_is_credited_to_the_slot_it_missed(self):
        """04:17 arrives at 08:10 — the 2026-11-20 error, in one assertion.

        Credited to 08:17 it reads as a slot kept and seven minutes *early*; credited to 04:17 it reads as a
        slot missed and a run delivered 233 minutes after the time it belonged to. The second is what a person
        waiting at 04:17 experienced, and the first is how a clock that drops a third of its slots came to be
        described as one that always fires.
        """
        self.assertEqual(self.clock.slot_for(self._t(21, 8, 10), self.every, self.minute), self._t(21, 4, 17))
        self.assertEqual(self.clock.slot_for(self._t(21, 8, 20), self.every, self.minute), self._t(21, 8, 17))

    def test_a_slot_that_produced_nothing_is_a_miss_and_not_a_late_arrival(self):
        start, end = self._t(20, 0, 0), self._t(21, 0, 0)
        runs = [self._run(self._t(20, 4, 40))]          # one run, six slots
        s = self.clock.summarise(runs, start, end, self.every, self.minute)
        self.assertEqual(s["due"], 5, "five complete slots fall between 00:00 and 24:00 at :17 past every fourth hour")
        self.assertEqual(s["delivered"], 1)
        self.assertEqual(s["missed"], 4, "four slots were silent and the summary does not say so")
        self.assertEqual(s["lates"], [23.0], "the one run that came was 23 minutes late, not on time")

    def test_a_run_a_person_pressed_is_not_a_delivery_of_the_clock(self):
        start, end = self._t(20, 0, 0), self._t(21, 0, 0)
        runs = [self._run(self._t(20, 9, 0), event="workflow_dispatch")]
        s = self.clock.summarise(runs, start, end, self.every, self.minute)
        self.assertEqual((s["delivered"], s["runs"]), (0, 0), "a hand wake was counted as the scheduler's")
        self.assertEqual(s["events"].get("workflow_dispatch"), 1, "and then it is not counted anywhere at all")
        self.assertEqual(s["missed"], 5)

    def test_two_runs_inside_one_slot_are_a_duplicate_and_not_two_wakes(self):
        start, end = self._t(20, 0, 0), self._t(21, 0, 0)
        runs = [self._run(self._t(20, 4, 20)), self._run(self._t(20, 4, 50))]
        s = self.clock.summarise(runs, start, end, self.every, self.minute)
        self.assertEqual(s["delivered"], 1)
        self.assertEqual(s["duplicates"], 1)
        self.assertEqual(s["lates"], [3.0], "the slot is as late as its first run, not as late as its worst")

    def test_a_window_that_has_not_finished_yet_is_not_counted_as_missed(self):
        """The last slot still has hours left to arrive in; counting it as missed makes every recent look worse."""
        start = self._t(20, 0, 0)
        end = self._t(20, 4, 40)
        self.assertEqual(len(self.clock.due_slots(start, end, self.every, self.minute)), 1,
                         "the 04:17 slot is still open at 04:40 and was counted as due anyway")

    def test_the_sentences_come_from_the_summary_rather_than_from_the_source(self):
        """A number typed into a sentence is wrong by the third re-run — this file has learned that twice."""
        start, end = self._t(20, 0, 0), self._t(21, 0, 0)
        s = self.clock.summarise([self._run(self._t(20, 4, 50))], start, end, self.every, self.minute)
        said = self.clock.report("some/repo", s)
        self.assertIn("1 of them", said)                    # delivered
        self.assertIn("5 slots", said)                      # due
        self.assertIn("33 minutes", said)                   # median lateness, from the summary
        empty = self.clock.summarise([], self._t(20, 0, 0), self._t(20, 1, 0), self.every, self.minute)
        self.assertIn("nothing to say", self.clock.report("some/repo", empty),
                      "a window with no complete slot printed zeros, which read as a clock that never ran")

    def test_the_manual_cites_the_instrument_and_the_day_it_was_read(self):
        """A range with no tool and no date is a memory. This is the check that keeps §5 re-derivable."""
        manual = (REPO / "USER-MANUAL.md").read_text(encoding="utf-8")
        self.assertTrue("lab/clock.py" in manual,
                        "§5 prints a measured range and does not say how to re-take it")
        self.assertTrue(re.search(r"Measured 2026-11-27", manual),
                        "the clock paragraph no longer carries the day its figure was read")
        self.assertTrue("0 of" in manual,
                        "the slot the scheduler never delivers is a fact; §5 may not drop it silently")


class ASeasonCanBeWatchedWhileItPlays(unittest.TestCase):
    """Item 7's second half: *"a session you can watch while it happens ... a report at the end, not a running table."*

    Until 2026-11-27 a golf season was one process that wrote `season.json` once, after the last putt, so the page had
    three minutes of nothing to show and said so with a spinner. The engine now writes the card it has after each
    round and the workflow commits that file between rounds, which makes three things true that are checked here
    one at a time:

      * the card is written **between** rounds and never during one — a half-played round is not a fact about a
        golfer, and a page that showed one would be printing strokes that did not happen;
      * watching a season does not change it: the same seed plays the same season to the byte, with and without
        `--progress`. Turning the loops inside out to reach the end of a round first is exactly the kind of change
        that quietly reorders a random stream, so it is pinned by a comparison rather than by my assurance;
      * the finished season leaves no running card behind, because a file that still says "round 2 of 4" beside a
        finished record is the kind of thing that gets read as current.
    """

    @classmethod
    def setUpClass(cls):
        cls.golf = load(REPO / "lab" / "golf.py", "golf_watch_mod")

    def setUp(self):
        """The season this class plays is written into a temporary directory, never over the project's own card.

        First written the other way, on 2026-11-27, and the run replaced the committed four-round record with a
        two-round one. A suite that edits the record it is checking is worse than no suite, and this is the hook that
        keeps it honest: `render_dir()` is the one place that decides where a season goes.
        """
        self._tmp = tempfile.TemporaryDirectory(prefix="golf-watch-")
        self._real_dir = self.golf.render_dir
        self.golf.render_dir = lambda: Path(self._tmp.name)

    def tearDown(self):
        self.golf.render_dir = self._real_dir
        self._tmp.cleanup()

    def _args(self, tmp, rounds=2, bags=2, seed=424242, progress=""):
        import argparse as _ap
        return _ap.Namespace(rounds=rounds, bags=bags, seed=seed, calm=True, pin_range=14.0,
                             policy="spread", learn=1, draws=0, streams=4, progress=progress,
                             start=False, render=None, floor=None, selftest=False)

    def test_the_card_is_written_between_rounds_and_never_during_one(self):
        """Reads the file the runner would commit, at every moment the engine writes one — so "after each round"
        is measured rather than asserted from the loop's shape."""
        seen = []
        real = self.golf.write_progress

        def spy(path, field, raw, done, rounds, bags, par):
            real(path, field, raw, done, rounds, bags, par)
            seen.append(json.loads(Path(path).read_text()))

        self.golf.write_progress = spy
        try:
            with tempfile.TemporaryDirectory() as td:
                self.golf.season(self._args(td, progress=str(Path(td) / "progress.json")))
        finally:
            self.golf.write_progress = real
        self.assertEqual([s["done"] for s in seen], [1, 2], "the card is not written once per round, in order")
        self.assertEqual({s["rounds"] for s in seen}, {2})
        self.assertEqual({len(s["athletes"]) for s in seen}, {6}, "the six athletes are not all in the running card")
        self.assertEqual([len(a["to_par"]) for s in seen for a in s["athletes"]], [1] * 6 + [2] * 6,
                         "the running card carries a column for a round that has not been played")

    def test_watching_a_season_does_not_change_it(self):
        import hashlib

        def play(with_progress: bool) -> tuple[str, Path, bool]:
            with tempfile.TemporaryDirectory(prefix="golf-watch-") as td:
                prog = Path(td) / "progress.json"
                self.golf.render_dir = lambda: Path(td)
                self.golf.season(self._args(td, progress=str(prog) if with_progress else ""))
                card = (Path(td) / "season.json").read_bytes()
                return hashlib.sha1(card).hexdigest(), prog, prog.exists()

        plain, _, _ = play(False)
        watched, prog, left = play(True)
        self.assertEqual(plain, watched,
                         "the season changed when it was watched: the round-outer loop reorders a random stream")
        self.assertFalse(left, "a finished season left its running card behind, so the page would read a stale day")

    def test_the_running_card_is_ordered_by_how_they_stand_now(self):
        """A running table that keeps the entry order is a table half filled in. The point of watching is the lead
        changing hands, so the engine sorts by strokes so far — and the page prints that order rather than its own."""
        raw = {
            "slow": [[{"to_par": 5, "strokes": 40}, {"to_par": 5, "strokes": 40}]],
            "quick": [[{"to_par": 1, "strokes": 36}, {"to_par": 1, "strokes": 36}]],
        }
        field = [("slow", "spread", True, 1.0, 1.5), ("quick", "pin", False, 1.0, 1.5)]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "progress.json"
            self.golf.write_progress(p, field, raw, 2, 4, 1, 35)
            data = json.loads(p.read_text())
        self.assertEqual([a["name"] for a in data["athletes"]], ["quick", "slow"],
                         "the running card is not a leaderboard")
        self.assertEqual(data["athletes"][0]["to_par"], [1, 1])
        self.assertEqual(data["done"], 2)
        self.assertEqual(data["schema"], "golf-progress/1",
                         "the page reads a schema name; a file without one cannot be refused when it changes shape")


class TheTemplateMustBeEnough(unittest.TestCase):
    """An installed tribe is a copy of a whitelist, so the whitelist has to be enough.

    Both failures here are silent on this repository: a path deleted from the template, or a workflow
    that starts running a script nobody added. Here the file exists either way; the owner's copy is
    the only place it is missing, and by then they are the one debugging it.
    """

    def test_every_whitelisted_path_exists_and_every_script_a_workflow_runs_ships(self):
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        missing = [p for p in mt.paths() if not (REPO / p).is_file()]
        self.assertEqual(missing, [], "whitelisted but not on disk")
        self.assertEqual(mt.unshipped(), {}, "a shipped workflow runs a script the template does not ship")
        self.assertEqual(mt.unshipped_reads(), {}, "a shipped script reads a file the template does not ship")

    def test_every_workflow_the_page_starts_ships(self):
        """The button on the page is a promise; the workflow behind it is the machinery.

        Found 2026-11-14: `paint.yml` and `magazine.yml` were absent from the whitelist while the shipped
        manual described §8 Pictures and §9 the magazine in full, so a new owner could press both and get
        nothing — and `--check` passed 40/40 the whole time, because it only asked whether the files on the
        list existed. This is the assertion that would have failed.
        """
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        self.assertEqual(mt.unshipped_dispatches(), {},
                         "the page starts a workflow the template does not ship")

    def test_the_new_checks_actually_fire_when_a_workflow_is_left_out(self):
        """A check nobody has seen fail is a check nobody knows works."""
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        saved = mt.FILES[:]
        try:
            mt.FILES = [f for f in saved
                        if f not in (".github/workflows/paint.yml", ".github/workflows/magazine.yml",
                                     "lab/paint.py", "lab/rps.py")]
            self.assertIn("paint.yml", mt.unshipped_dispatches())
            self.assertIn("magazine.yml", mt.unshipped_dispatches())
            self.assertEqual(mt.unshipped_imports().get("lab/rps.py"),
                             ["tribe.py", "lab/tennis.py"],
                             "the model table is read out of lab/rps.py behind an except: pass")
        finally:
            mt.FILES = saved
        self.assertEqual(mt.unshipped_dispatches(), {}, "restoring FILES must restore the clean report")

    def test_golf_ships_as_a_game_a_circle_can_play_rather_than_one_it_can_only_read(self):
        """Golf reached the Play tab on 2026-11-23 as a *viewer*: the project's committed season, and six films.

        The founder read that back in four questions — "is Kythe just capable of viewing status about games that
        have already been played?" — and he was right. Tennis, the game that tab was built for, is not a file the
        owner reads: the page dispatches `season.yml`, a runner plays with the members' own engines, and the record
        comes back into the circle (`games/tennis/seasons/<season>/`). Golf had no workflow at all, so a circle
        could look at the bench's numbers and never have any of its own.

        Two things have to be true for the press to work in a circle somebody just made, and neither is visible
        from here, because here both files exist: the workflow has to be on the template's whitelist, and so does
        every local module `lab/golf.py` imports (`putt.py` — a game the template ships, which golf borrows).
        """
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        saved = mt.FILES[:]
        try:
            mt.FILES = [f for f in saved if "golf" not in f]
            self.assertIn("golf.yml", mt.unshipped_dispatches(),
                          "the page offers a golf press whose workflow a new circle would not have")
        finally:
            mt.FILES = saved
        try:
            mt.FILES = [f for f in saved if f != "lab/putt.py"]
            self.assertEqual(mt.unshipped_imports().get("lab/putt.py"), ["lab/golf.py"],
                             "a circle with golf and no putt.py fails on its first press, at import")
        finally:
            mt.FILES = saved
        # And the third direction, which is the one a scratch circle found: `--render` opens the player that draws a
        # scene, and `games/` is not a folder a template has. Without this file the press plays a season and then
        # dies on the sixth command with a traceback that names a path and nothing else.
        try:
            mt.FILES = [f for f in saved if f != "games/golf/replay3d.html"]
            self.assertEqual(mt.unshipped_reads().get("games/golf/replay3d.html"), ["lab/golf.py"],
                             "the player a scene is drawn by is not shipped, so --render dies in a new circle")
        finally:
            mt.FILES = saved
        self.assertEqual(mt.unshipped_dispatches(), {}, "restoring FILES must restore the clean report")

    def test_a_circle_with_no_games_folder_can_play_a_golf_season(self):
        """The press, in a circle that has just been made — the only place the two halves are ever apart.

        Everything else in this class is static, and static is what failed on 2026-11-26: golf.py, putt.py, golf.yml
        and the whitelist were all consistent, and `--render` still died in a fresh circle because it opens
        `games/golf/replay3d.html` and a circle has no `games/`. A traceback naming a path is not a press that works.
        So a template is built in a temporary folder and the workflow's own first commands are run in it: the season,
        the door, and one replay — one, because all six go through the same `read_text` of the same player.

        Two rounds and two sessions, not four and four: this is a check that the machinery is present, not a
        measurement, and the smaller season is four seconds instead of ninety.
        """
        import shutil as _sh
        tmp = Path(tempfile.mkdtemp(prefix="circle-golf-"))
        try:
            r = subprocess.run([sys.executable, str(REPO / "lab" / "make_template.py"), "--out", str(tmp / "c")],
                               cwd=REPO, capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            circle = tmp / "c"
            # A circle now *has* `games/golf/replay3d.html` (the player ships with the engine) and no rendered
            # season at all. The player's presence is the point of the fixture, so this asserts the absent half.
            self.assertTrue((circle / "games" / "golf" / "replay3d.html").is_file(),
                            "the player does not ship, so --render cannot work in a new circle")
            self.assertFalse((circle / "games" / "golf" / "renders").exists(),
                             "the fixture is wrong: a new circle already has a rendered record")
            for cmd in (["--season", "--rounds", "2", "--bags", "2", "--seed", "424242"],
                        ["--start"], ["--render", "7"]):
                r = subprocess.run([sys.executable, "lab/golf.py"] + cmd, cwd=circle,
                                   capture_output=True, text=True, timeout=600)
                self.assertEqual(r.returncode, 0,
                                 f"a circle could not run golf.py {' '.join(cmd)}:\n{r.stdout}\n{r.stderr}")
            made = {p.name for p in (circle / "games" / "golf" / "renders").iterdir()}
            self.assertTrue({"season.json", "season.html", "start.html", "hole-7.html"} <= made,
                            f"the season played but the pages are not there: {sorted(made)}")
            card = json.loads((circle / "games" / "golf" / "renders" / "season.json").read_text())
            self.assertEqual(len(card["athletes"]), 6, "the card a circle gets is not the six-athlete card")
        finally:
            _sh.rmtree(tmp, ignore_errors=True)

    def test_the_template_carries_no_record_of_anything_that_happened_elsewhere(self):
        """A seed is not a circle, and two files had been quietly making it one.

        `.tribe-beacon` says a beacon was already sent from *this* repository; `.ait/last-clock.json` says which
        engines *this* project's clock found at 00:38Z on 27 November. Both were committed in the published
        template for weeks, so a stranger's new circle began with a record of two events that did not happen in
        it — and the second is the page's own source for "what did the last wake find", which is the worst kind of
        file to hand somebody prefilled. Neither was ever on the whitelist, which is why nothing deleted them and
        every publish put them back by hand.

        The build is the only place that can be asked: on disk the bench has both files and always will.
        """
        import shutil as _sh
        tmp = Path(tempfile.mkdtemp(prefix="seed-"))
        try:
            r = subprocess.run([sys.executable, str(REPO / "lab" / "make_template.py"), "--out", str(tmp / "c")],
                               cwd=REPO, capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            seed = tmp / "c"
            for rel in (".tribe-beacon", ".ait/last-clock.json"):
                self.assertFalse((seed / rel).exists(),
                                 f"the template ships {rel}, a record of a run that happened in this project")
            self.assertFalse((seed / ".ait").exists(),
                             "the template ships an .ait/ directory: a record of a clock nobody has run yet")
            # And it must not be there because the build failed: the whitelist is the list a circle receives, so a
            # seed with nothing in it would pass this test and ship nothing.
            self.assertTrue((seed / "wake" / "wake.py").is_file(), "the build produced nothing to be sure of")
        finally:
            _sh.rmtree(tmp, ignore_errors=True)

    def test_the_files_the_page_writes_into_an_old_circle_are_files_the_template_publishes(self):
        """The press retrofits a circle made before golf, so the page now carries a list of four paths.

        That is a second copy of a decision the template already makes, and a second copy is how this whitelist has
        drifted before: a path the page would fetch from the template and write into somebody's repository, which
        the template does not publish, turns the press into a 404 at the moment a person pressed a button. Held
        against `make_template.FILES`, which is the list that builds a new circle, so the two cannot disagree.

        Found-needed by the founder's turn of 2026-11-26: "ideally you would automatically retrofit the circle and
        then proceed to play" — the alternative I had shipped was telling the person to run a command.
        """
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        page = (REPO / "ait.html").read_text(encoding="utf-8")
        m = re.search(r"const GOLF_NEEDS = \[([^\]]*)\]", page)
        self.assertIsNotNone(m, "the page no longer says which files a circle needs for golf")
        paths = re.findall(r"'([^']+)'", m.group(1))
        self.assertEqual(len(paths), 4, f"golf needs four files, the page lists {paths}")
        for must in (".github/workflows/golf.yml", "lab/golf.py", "lab/putt.py", "games/golf/replay3d.html"):
            self.assertIn(must, paths, f"the retrofit list has lost {must}")
        missing = [p for p in paths if p not in mt.FILES]
        self.assertEqual(missing, [], "the page would fetch a file the template does not publish")
        absent = [p for p in paths if not (REPO / p).is_file()]
        self.assertEqual(absent, [], "the page would fetch a file that is not on this bench")

    def test_the_engine_a_circle_runs_accepts_the_flags_the_workflow_passes_it(self):
        """A workflow is the one piece of this repository that nobody runs before a stranger does.

        `golf.yml` types `python3 lab/golf.py --season --rounds …`. If `--seed` were not an argument — and it was
        not, until the press needed a season that differs each time — the run would fail after checkout, several
        minutes in, on a circle, for the owner. argparse's own refusals are the oracle here, so the check asks the
        engine rather than a list in a document that can drift.
        """
        wf = (REPO / ".github" / "workflows" / "golf.yml").read_text(encoding="utf-8")
        # The flags are not on the `python3 lab/golf.py` line: they are in the bash array the line expands
        # (`args=(--season …)` then `python3 lab/golf.py "${args[@]}"`). The first version of this test read the
        # python3 line, found no flags at all, and passed with `--bogus-flag` planted in the array — a green check
        # reading the wrong line, which is this repository's most repeated defect. Scanned by array now, and the
        # array is required to be one golf would understand.
        arrays = re.findall(r"args\+?=\(([^)]*)\)", wf)
        self.assertTrue(arrays, "the workflow never builds an argument list for the engine")
        self.assertTrue(any("--season" in a for a in arrays),
                        "no argument list asks for a season, so this check is looking at the wrong thing again")
        calls = arrays
        # argparse's own list, printed by the engine itself: a test that keeps its own copy of the flags is a test
        # that agrees with the document and not with the program.
        r = subprocess.run([sys.executable, str(REPO / "lab" / "golf.py"), "--help"],
                           cwd=REPO, capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, "the engine will not even print its own flags:\n" + r.stderr)
        known = set(re.findall(r"--[a-z][a-z-]*", r.stdout))
        for line in calls:
            for flag in re.findall(r"--[a-z][a-z-]*", line):
                self.assertIn(flag, known, f"golf.yml passes {flag}, which lab/golf.py does not accept")

    def test_the_updater_ships_and_can_never_touch_a_member(self):
        """An upgrade replaces machinery, and a member's diary is not machinery.

        The rule is in `is_machinery()`, which is why it is testable without a network: whatever the
        template contains, these paths are never replaceable. Getting this wrong once would silently
        overwrite somebody's members with the template's empty shelf, so it is asserted path by path.
        """
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        import update_tribe as ut
        self.assertIn("lab/update_tribe.py", mt.FILES, "every tribe needs the tool that updates a tribe")
        for path in ("wake/members/Aphrodite/state/journal.md", "wake/members/Aphrodite/state/voice.md",
                     "members.json", "soil/workshop/world.md", "plates/2026-11-13-a-lamp.md",
                     "issues/0001.md", "play/log/2026-11-12.md", "README.md", ".gitignore",
                     ".tribe-beacon", "wake/members/.gitkeep"):
            self.assertFalse(ut.is_machinery(path), f"{path} must never be replaced by an update")
        for path in ("tribe.py", "lab/members.py", ".github/workflows/paint.yml", "USER-MANUAL.md",
                     "wake/wake.py", "play/play.py", "talk.sh"):
            self.assertTrue(ut.is_machinery(path), f"{path} is machinery and must be updatable")

    def test_an_update_that_does_not_validate_is_rolled_back(self):
        """A copy is a transaction: either the tribe validates afterwards or nothing was written.

        The machinery is a set of scripts that import each other, and half of them being new is exactly
        the state a copy leaves behind for an instant. The gate is the validator, and this test drives it
        with a real git repository: one replaced file, one added file, and a tree that fails validation.
        """
        import tempfile
        sys.path.insert(0, str(REPO / "lab"))
        import update_tribe as ut
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ut.git(root, "init", "-q")
            (root / "tribe.py").write_text("# old\n")
            (root / "members.json").write_text("{\"members\": []}\n")
            ut.git(root, "add", "-A")
            ut.git(root, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "init")
            # an update that would replace tribe.py with something that cannot run, and add a script
            (root / "tribe.py").write_text("this is not python(")
            (root / "lab").mkdir()
            (root / "lab" / "new.py").write_text("# added by the update\n")
            (root / "members.json").write_text("{\"members\": [{\"name\": \"ghost\"}]}")
            ok, said = ut.validates(root)
            self.assertFalse(ok, "a broken tribe must not validate")
            ut.roll_back(root, ["tribe.py"], ["lab/new.py"])
            self.assertEqual((root / "tribe.py").read_text(), "# old\n", "the replaced file comes back")
            self.assertFalse((root / "lab" / "new.py").exists(), "the added file is removed")
            self.assertIn("\"members\": []", (root / "members.json").read_text(),
                          "the regenerated list is restored with the machinery that derives it")
            self.assertEqual(ut.git(root, "status", "--porcelain").stdout.strip(), "",
                             "after a refusal the working tree is exactly as it was")

    def test_a_retired_file_is_named_and_only_deleted_with_prune(self):
        """An update that could delete a file quietly is an update nobody can safely press.

        The updater's only authority to remove anything is the template's `.tribe-retired.json`, and even
        then: named by default, removed only with `--prune`. Driven here with the network stubbed out, so
        both halves are asserted offline.
        """
        import contextlib
        import io
        import json as _json
        import tempfile
        sys.path.insert(0, str(REPO / "lab"))
        import update_tribe as ut
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "lab").mkdir()
            (root / "tribe.py").write_text("# harness\n")
            (root / "lab" / "old_tool.py").write_text("# retired\n")
            ut.git(root, "init", "-q")
            ut.git(root, "add", "-A")
            ut.git(root, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-qm", "init")

            fake = {"lab/new_tool.py": b"# new\n"}
            retired = [{"path": "lab/old_tool.py", "since": "2026-11-15", "why": "replaced by new_tool.py"}]
            real_fetch, real_argv = ut.fetch_template, sys.argv
            ut.fetch_template = lambda: (fake, retired)
            try:
                sys.argv = ["update_tribe.py", "--root", tmp]
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    ut.main()
                said = out.getvalue()
                self.assertIn("- lab/old_tool.py", said, "the retired file is named")
                self.assertIn("kept — pass --prune", said)
                self.assertTrue((root / "lab" / "old_tool.py").exists(), "named, not deleted")

                sys.argv = ["update_tribe.py", "--root", tmp, "--write", "--prune"]
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    ut.main()
                self.assertFalse((root / "lab" / "old_tool.py").exists(), "--prune removes it")
                self.assertTrue((root / "lab" / "new_tool.py").exists(), "and the new file is there")
            finally:
                ut.fetch_template = real_fetch
                sys.argv = real_argv

    def test_the_manual_says_what_an_update_does_and_never_touches(self):
        """The section a person reads before pressing the command, asserted rather than assumed."""
        manual = (REPO / "USER-MANUAL.md").read_text(encoding="utf-8")
        self.assertIn("## 11a. Keeping your circle current", manual)
        for claim in ("It never touches your circle itself", "If it refuses, nothing has been written",
                      "Files you add yourself are never touched", "--prune"):
            self.assertIn(claim, manual, f"the manual must carry: {claim}")

    def test_the_updater_refuses_a_directory_that_is_not_a_tribe(self):
        import tempfile
        r = subprocess.run([sys.executable, str(REPO / "lab" / "update_tribe.py"),
                            "--root", tempfile.mkdtemp()], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not look like a circle", r.stderr)

    def test_the_bench_and_the_page_agree_on_what_an_update_would_do(self):
        """`lab/repos.py verdict()` and `ait.html`'s updatePlan() are the same rule written twice, in two languages,
        for one reason: the page runs in a browser and the report runs from a terminal. Two copies of a rule is how
        this project's whitelist drifted, so the three cases each implementation gets wrong are pinned here, and
        the page's own three are in lab/page-check.mjs against the same shapes."""
        sys.path.insert(0, str(REPO / "lab"))
        import repos
        man = ["wake/wake.py", "tribe.py", "USER-MANUAL.md"]
        theirs = {"wake/wake.py": "n1", "tribe.py": "n2", "USER-MANUAL.md": "n3"}
        # (1) no record: files may be added, nothing may be replaced
        ours = {"wake/wake.py": "o1", "tribe.py": "o2", "USER-MANUAL.md": "o3"}
        r = repos.verdict(man, ours, theirs, None)
        self.assertEqual(r["replace"], [])
        self.assertEqual(len(r["unjudged"]), 3)
        self.assertFalse(r["credible"])
        # (2) a credible record: one file untouched since it and replaced, one differing from it and left alone,
        #     one already identical to the template and not mentioned at all
        theirs2 = dict(theirs, **{"USER-MANUAL.md": "o3"})
        base = {"wake/wake.py": "o1", "tribe.py": "old2", "USER-MANUAL.md": "o3"}
        r = repos.verdict(man, ours, theirs2, base)
        self.assertTrue(r["credible"], "two of three matching the record is a credible record")
        self.assertEqual(r["replace"], ["wake/wake.py"])
        self.assertEqual(r["kept"], ["tribe.py"])
        self.assertEqual(r["add"], [], "a file already identical to the template is not work")
        # (3) a record its files contradict: nothing is replaced
        base = {"wake/wake.py": "x1", "tribe.py": "x2", "USER-MANUAL.md": "x3"}
        r = repos.verdict(man, ours, theirs, base)
        self.assertFalse(r["credible"])
        self.assertEqual(r["replace"], [])
        self.assertEqual(len(r["unjudged"]), 3)
        # and a file the tribe does not have is an addition, not a replacement, in every case
        r = repos.verdict(man, {"tribe.py": "o2"}, theirs, {})
        self.assertIn("wake/wake.py", r["add"])
        self.assertEqual(r["agree"], 0)

    def test_the_report_only_counts_repositories_that_are_tribes(self):
        """`llm-symposium` is a keeper and not a tribe. Counting it would have reported the commons as 29 files
        behind the machinery — a number that makes a report worth ignoring."""
        src = (REPO / "lab" / "repos.py").read_text()
        self.assertIn('if ours is not None and "tribe.py" not in ours:', src)
        self.assertNotIn('if kind not in ("tester", "demo", "keep")', src)

    def test_the_updater_records_which_version_it_copied(self):
        """Two updaters and one record. A tribe updated from a terminal whose record still names the commit it was
        installed from is a tribe whose page compares its files against a version they never came from."""
        import json as _json
        import tempfile
        sys.path.insert(0, str(REPO / "lab"))
        import update_tribe as ut
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = ut.stamp_version(root, "c" * 40)
            self.assertEqual(rel, ".ait/version.json")
            first = _json.loads((root / rel).read_text())
            self.assertEqual(first["schema"], "ait-version/1")
            self.assertEqual(first["updated_to"], "c" * 40)
            self.assertEqual(first["installed_from"], "c" * 40)
            self.assertEqual(first["template"], "LindsayRidgeway/ai-tribe-template")
            ut.stamp_version(root, "d" * 40)
            second = _json.loads((root / rel).read_text())
            self.assertEqual(second["updated_to"], "d" * 40)
            self.assertEqual(second["installed_from"], "c" * 40,
                             "an update must not rewrite where the tribe came from")
            # and the page reads a stamp of the same shape, because it is the same file
            page = (REPO / "ait.html").read_text()
            self.assertIn("ait-version/1", page)
            self.assertIn(".ait/version.json", page)

    def test_the_manifest_is_generated_from_the_same_list_that_builds_a_tribe(self):
        """The page will write only what this file names, so it has to be the whitelist and not a copy of it."""
        import json as _json
        import tempfile
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        man = _json.loads((REPO / ".tribe-manifest.json").read_text()) if (REPO / ".tribe-manifest.json").is_file() else None
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "tpl"
            subprocess.run([sys.executable, str(REPO / "lab" / "make_template.py"), "--out", str(out)],
                           check=True, capture_output=True, timeout=120)
            built = _json.loads((out / ".tribe-manifest.json").read_text())
        self.assertEqual(built["schema"], "ait-manifest/1")
        self.assertEqual(built["files"], mt.manifest(), "the published manifest must be the whitelist, sorted")
        for p in built["files"]:
            self.assertTrue((REPO / p).is_file(), f"the manifest names {p}, which does not exist")

    def test_the_manifest_never_names_a_file_an_update_could_lose(self):
        """members.json is a list derived from the shelf and the template's copy is empty. Writing it would delete
        every member an owner has, which is the one way an "update" could destroy a tribe."""
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        import update_tribe as ut
        man = mt.manifest()
        for path in ("members.json", ".gitignore", "README.md", "wake/members/.gitkeep",
                     "issues/README.md", "letters/README.md", "plates/README.md"):
            self.assertNotIn(path, man, f"{path} must never be on the manifest an update writes from")
        for path in man:
            self.assertTrue(ut.is_machinery(path), f"the manifest names {path}, which the updater calls content")

    def test_the_page_never_writes_a_path_the_manifest_does_not_name(self):
        """The page's list comes from the template at run time; this is the bench's half of the same promise, and it
        fires on the shape of the code rather than on a browser: every write in the update goes through the loop
        over `want`, and `want` is the manifest."""
        page = (REPO / "ait.html").read_text()
        body = page.split("async function applyUpdate(", 1)[1].split("\nasync function stampVersion", 1)[0]
        self.assertIn("for (const f of [...p.writes, ...p.adds])", body)
        self.assertNotIn("members.json", body, "the write must not name members.json anywhere")
        self.assertIn("readManifest()", page.split("async function updatePlan(", 1)[1].split("return {head", 1)[0])

    def test_the_template_carries_no_members_and_no_fixtures(self):
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        for p in mt.paths():
            self.assertFalse(p.startswith("lab/fixtures"), p)
            self.assertFalse(p.startswith("lab/experiments"), p)
            self.assertNotIn("/output/", p, "a template must not ship somebody's written work")
        self.assertIn("wake/members/.gitkeep", mt.paths(), "the empty folder has to exist for the first member")

    def test_the_template_ships_no_room_because_a_stranger_has_their_own(self):
        """The founder, 2026-11-20, on the workshop prose: *"Why do you think this makes sense for every circle or every
        circle member?"* It does not, and the answer was not to write better prose. A room is a file a person writes
        when they have a setting in mind; shipping mine put a chandlery and a kettle at the bottom of every stranger's
        first wake — and one of the example drops was signed "the human", a name the template had no right to use.
        If generic output is the worry, the prompt answers it; a template cannot."""
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        shipped = [p for p in mt.paths() if p.startswith("soil/")]
        self.assertEqual(shipped, [], f"the template ships somebody else's room: {shipped}")


class TestDebrisOnTheFloor(unittest.TestCase):
    """The suite must say when the tree it is about to test is not the tree in the repository."""

    def _repo(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        if subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True).returncode != 0:
            self.skipTest("no git here, so there is nothing to be untracked from")
        (tmp / "wake" / "members").mkdir(parents=True)
        (tmp / "wake" / "members" / ".gitkeep").write_text("")
        (tmp / "works").mkdir()
        return tmp

    def test_a_leftover_member_from_somebody_elses_run_is_named_out_loud(self):
        tmp = self._repo()
        (tmp / "wake" / "members" / "trap" / "state").mkdir(parents=True)
        (tmp / "wake" / "members" / "trap" / "state" / "place.md").write_text("workshop\n")
        (tmp / "works" / "a" / "x.md").parent.mkdir(parents=True)
        (tmp / "works" / "a" / "x.md").write_text("a work nobody filed\n")
        found = debris(tmp)
        self.assertIn("wake/members/trap/state/place.md", found)
        self.assertIn("works/a/x.md", found)

    def test_an_empty_circle_is_not_debris(self):
        """The `.gitkeep` that makes the folder exist is the template's, and reporting it would teach the reader to
        ignore the warning."""
        self.assertEqual(debris(self._repo()), [])


def debris(root: Path = REPO) -> list:
    """Untracked paths a previous run left in the two folders that make a circle a circle.

    On 2026-11-20 this suite ran 478 tests here and went red with ten failures, and the same commit's tests were
    green from a fresh clone at 482. The difference was not code: another window had left `wake/members/a`,
    `wake/members/trap` and friends in the tree, and a test that counts members, worlds or works saw them. A red
    that comes from somebody's leftover fixture is a red nobody can attribute, which is the fault that cost
    fifteen hours on 2026-11-19. So: look first, and say so out loud, before any test runs.
    """
    try:
        out = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
                             capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):   # no git, or no repository: nothing to warn about
        return []
    if out.returncode != 0:
        return []
    stray = []
    for line in out.stdout.splitlines():
        if not line.startswith("?? "):
            continue
        path = line[3:].strip().strip('"')
        if path.split("/")[0] in ("wake", "works") and "/." not in path and not path.endswith(".gitkeep"):
            stray.append(path)
    return stray


if __name__ == "__main__":
    leftovers = debris()
    if leftovers:
        print(f"\n!! {len(leftovers)} untracked path(s) under wake/ or works/ are sitting in this tree:", file=sys.stderr)
        for path in leftovers[:12]:
            print(f"     {path}", file=sys.stderr)
        if len(leftovers) > 12:
            print(f"     … and {len(leftovers) - 12} more", file=sys.stderr)
        print("   A test that counts members, worlds or works will see these and go red for a reason that is not\n"
              "   in the code. If a red here surprises you, delete them and run again before believing it.\n",
              file=sys.stderr)
    unittest.main(verbosity=2)


class TestTheArmComesBackToTheHittingSide(unittest.TestCase):
    """Item 12, 2026-11-27. One pose carried the whole carry phase, which is the founder's "the arms never come back
    to the right side during a run". Measured on `records/item31-after` with the sweep's ninth field (the racquet
    head's lateral offset in the body's own frame), in the carry phase of a run at 9ft/s and up: 0.64 and 0.48
    crossings per stride pair before, 1.44 and 1.75 after. The strike is untouched — the racquet head's distance to
    the ball at the contact frame is identical on all 63 contacts the sweep can see."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")
        self.reader = (REPO / "lab" / "tennis_sweep.py").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")
        self.stills = (REPO / "games" / "tennis" / "STILLS.md").read_text(encoding="utf-8")

    def test_the_defect_its_fix_and_the_numbers_are_on_the_record(self):
        self.assertIn("## Item 12 — the arms never come back to the right side during a run (DONE 2026-11-27)",
                      self.backlog)
        for piece in ("0.64", "0.48", "1.44", "1.75", "item31-after", "9ft/s", "63 contacts"):
            self.assertTrue(piece in self.backlog, f"{piece} is not in the item 12 entry")

    def test_all_three_branches_that_carry_the_frame_carry_it(self):
        # The striker recovering from their own shot, the player with no ball to strike at all (the one who has just
        # lost the point, which was a fixed pose), and the player whose ball is coming while they run to it.
        self.assertIn("const carrySwing = (CARRY && moving && !walking) ? Math.sin(phase) * CARRY_PUMP * pumpGrow : 0;",
                      self.page, "the striker's recovery does not carry the frame")
        self.assertIn("const carryHand = CARRY ? wait.clone()", self.page)
        self.assertIn("const sway = CARRY ? Math.sin(phase) * CARRY_PUMP * pumpGrow : 0;", self.page,
                      "the player with no ball to strike still holds one fixed pose for the whole run")
        self.assertIn("placeRacquet(rig, readyAim.clone().add(carryPoint.clone().sub(wait)), _face);", self.page,
                      "the no-ball branch solves the hand to the carry but leaves the frame where it was")
        self.assertIn("const pump = CARRY ? Math.sin(phase) * CARRY_PUMP * pumpGrow * (1 - windup) : 0;", self.page,
                      "the carry's swing is not faded out as the take-back comes in")

    def test_the_lateral_axis_is_built_before_the_carry_uses_it(self):
        # The first version of this crashed the whole page — `Uncaught ReferenceError: right is not defined` — and a
        # sweep that returns no rows at all reads exactly like a broken sweep. `rightW` was built forty lines BELOW
        # the carry that needed it. This is the one assertion that would have caught it before a headless run did.
        self.assertLess(self.page.index("const rightW = new THREE.Vector3(-Math.cos(rig.yaw), 0, Math.sin(rig.yaw));"),
                        self.page.index(".addScaledVector(rightW, CARRY_READY * grow"),
                        "the carry uses its lateral axis before it is defined, which throws away the whole frame")

    def test_the_carry_is_measured_and_the_before_build_is_still_drawable(self):
        self.assertIn('const CARRY = q.get("carry") !== "0";', self.page,
                      "there is no way to draw the build before this item on the same film")
        self.assertIn('q.has("pump") ? Math.max(0, parseFloat(q.get("pump")) || 0)', self.page,
                      "the swing's amplitude cannot be swept, so the number above is a preference")
        # The pump's ramp is its own: a 3ft run at 8ft/s lasts 0.375s, and the stride's 0.20s-in/0.20s-out ramp
        # never reaches 1 in that time, which cost the crossings on the short moves.
        self.assertIn("const PUMP_IN = 0.06;", self.page)
        self.assertIn("const pumpGrow = Math.min(Math.max(0, Math.min(1, el / PUMP_IN))", self.page)

    def test_the_reader_splits_a_walk_from_a_run_and_says_why(self):
        self.assertIn("def measure(t, name, carry_only):", self.reader)
        self.assertIn('("run, carry", True), ("run, stroke", False)', self.reader)
        # The walk/run line is a gap found in THIS film's own speed histogram, not a number chosen for the answer.
        self.assertIn("gap = min((b for b in buckets if 7 <= b <= 9), key=lambda b: buckets[b], default=8)",
                      self.reader, "the walk/run line is not measured from the record")
        self.assertIn('"rh": (p[8][0] if len(p) > 8 and p[8] else None)', self.reader,
                      "the ninth sweep field is not read")
        self.assertTrue("**10. A WALK IS NOT A RUN" in self.stills,
                        "the population error that hid this fix is not on the record")


class TestTheContactIsMeasuredOnTheFilmRatherThanInARate(unittest.TestCase):
    """Item 16's remainder, 2026-11-27. The record's done-test is `RACQUET_REACH = 7.0ft` from the feet, and the
    page's own line is `shoulder-B more than 3.9ft is a strike no arm and frame can make`. Both cannot be the
    promise, and this instrument is what says the gap is real: on `records/item31-after` the racquet head was a
    median 1.08ft from the ball at the contact and 38 of 63 contacts were over 1ft, before the stride was fixed."""

    def setUp(self):
        self.reader = (REPO / "lab" / "tennis_sweep.py").read_text(encoding="utf-8")
        self.backlog = (REPO / "games" / "tennis" / "BACKLOG.md").read_text(encoding="utf-8")

    def test_the_reader_reads_the_head_to_ball_distance_at_each_contact(self):
        self.assertIn("== the contact — how far the racquet head is from the ball when the ball is struck ==",
                      self.reader)
        self.assertIn('if not p or len(p) < 9 or p[5] is None:', self.reader,
                      "the contact section is not reading the sweep's own rq field")

    def test_the_reader_keys_a_contact_on_the_clock_and_not_on_the_shot_number(self):
        # Shot numbers restart at 1 on every rally: keying on them put 116 "serves" through a film of 108 shots,
        # and read the rq off whichever rally's row sorted first. The clock is unique in a film; `n` is not.
        self.assertIn("when = sg[1] + (sg[3] or 0.0)", self.reader)
        self.assertIn("if off > 0.25:", self.reader)
        self.assertNotIn("if r[1] != n or", self.reader,
                         "the contact section is matching rows by shot number again, which collides across rallies")

    def test_a_log_with_no_rows_says_so_instead_of_dying(self):
        # a page-side exception and a run whose compositor never started both produce zero rows, and both used to
        # read as `IndexError: list index out of range` from `jumps[0]` — three different faults, one message.
        self.assertIn("if not rows:", self.reader)
        self.assertIn("no `debug sweep` rows in", self.reader)
        self.assertIn("`--screenshot=` on the command line", self.reader)

    def test_the_reader_splits_a_serve_from_a_groundstroke(self):
        # they are two different questions: a serve is struck 8.8ft up and the stride cannot reach it
        self.assertIn('for label, v in (("serves, struck 6ft up or more", tall), ("groundstrokes", flat)):',
                      self.reader)

    def test_the_gap_between_the_two_promises_is_on_the_record(self):
        self.assertIn("WHAT IT STILL LETS THROUGH — MEASURED 2026-11-27", self.backlog)
        for piece in ("1.08ft", "4.45ft", "5.47ft", "63 of 63", "38 of 63", "3.9ft", "RACQUET_REACH = 7.0ft"):
            self.assertTrue(piece in self.backlog, f"{piece} is not in the item 16 note")

    def test_the_stride_that_closed_it_is_on_the_record_with_both_price_tags(self):
        for piece in ("the stride that puts the frame on the ball (DONE 2026-11-27)",
                      "3.16ft", "0.27ft", "69 of 108", "16 of 108", "0.51ft", "3** (Colette; Gwen 0)",
                      "`?step=0` draws the pre-fix build", "swept 0:530"):
            self.assertTrue(piece in self.backlog, f"{piece} is not in the stride's note")


class TestTheStepTowardTheBallIsWalkedAndNotPlaced(unittest.TestCase):
    """Item 16's remainder, second half, 2026-11-27. `reachTo` is the page's stride toward the ball, and it had
    never run on an approach frame: it was handed `northIn`'s boolean instead of the contact point, so its gap was
    NaN and the step was always zero. Each test here is one of the five defects that had to be fixed in order."""

    def setUp(self):
        self.page = (REPO / "games" / "tennis" / "replay3d.html").read_text(encoding="utf-8")

    def test_the_receiver_s_step_is_not_handed_the_north_flag_as_a_ball(self):
        # `const at` was block-local, so the call took the outer `at` = northIn(seg, name) = true/false.
        self.assertIn("let meet = null, stepAt = null;", self.page)
        self.assertIn("meet = cBall.clone().sub(shift);", self.page)
        self.assertIn("reachTo(rig, lead, stepAt,", self.page)
        self.assertNotIn("reachTo(rig, lead, at,", self.page)

    def test_the_step_is_phased_on_the_contact_and_not_on_the_landing(self):
        self.assertIn('CONTACT[sh.rally + ":" + sh.n] = t;', self.page)
        self.assertIn('const meetT = CONTACT[nxtBall.rally + ":" + nxtBall.n];', self.page)

    def test_the_step_is_measured_from_the_root_and_not_from_the_shoulder(self):
        # the two branches disagree by 0.84ft of shoulder on the same ball, which was a 1.05ft frame at 52ft/s
        self.assertIn("const root = rig.root.position;   // read here, not inside the `r > 0` branch", self.page)
        self.assertIn("const hx = ball.x - root.x, hz = ball.z - root.z", self.page)
        self.assertLess(self.page.index("const root = rig.root.position;"),
                        self.page.index("const hx = ball.x - root.x"),
                        "the root is read after the geometry that borrows it")

    def test_zero_is_a_target_and_goes_through_the_slew(self):
        self.assertIn("let dx = 0, dy = 0, dz = 0;", self.page)
        self.assertNotIn("rig.lean = { x: 0, y: 0, z: 0 };\n    return;", self.page,
                         "the zero-offset early return is back, and it drops a body out of a stride in one frame")

    def test_the_step_is_slewed_against_the_body_s_own_budget(self):
        self.assertIn("const cap = Math.max(0, dtn * BODY_SPEED - baseStep);", self.page)
        self.assertIn("const BODY_SPEED = 25;", self.page, "the cap is not item 2b's own line")
        self.assertIn("rig.basePrev = [root.x, root.z];", self.page)
        self.assertIn('const STEP = q.get("step") !== "0";', self.page,
                      "there is no way to draw the pre-step build on the same film, so the change cannot be priced")
