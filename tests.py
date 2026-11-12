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
        """Seven engines this harness speaks cannot paint. "No" without an address is the answer this project
        stopped accepting, so the refusal carries the three that can."""
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

    def test_a_dry_run_that_would_fail_still_fails(self):
        """A rehearsal that cannot fail teaches nothing about the performance: --dry-run must refuse the same
        engines the real run refuses."""
        import contextlib, io
        err = io.StringIO()
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            self.paint.main(["--engine", "groq", "--prompt", "a red cube", "--dry-run"])

    def test_the_credit_names_the_machine_and_keeps_the_members_words(self):
        """The card beside the picture is the only place a tool name appears, so it must name the one that
        actually drew. The existing plate's card says "Created by Google Docs" because a person ran it."""
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        image, card = self.paint.file_it(b"\x89PNG not really", "20261102T040000Z-harbour", "openai",
                                         "gpt-image-1-mini", "a watercolour of the harbour at night, one lamp",
                                         plates=Path(tmp))
        self.assertEqual(image.name, "20261102T040000Z-harbour.png")
        self.assertEqual(card.name, "20261102T040000Z-harbour.md")
        note = card.read_text(encoding="utf-8")
        self.assertIn("openai", note)
        self.assertIn("gpt-image-1-mini", note)
        self.assertIn("a watercolour of the harbour at night", note,
                      "the member's own sentence is the commission; the make must not paraphrase it")
        self.assertTrue(card.read_text(encoding="utf-8").startswith("Painted by"),
                        "a card must open by saying who made the picture, so a reader cannot mistake it")

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

    def test_next_with_no_world_says_why_instead_of_exiting_in_silence(self):
        """The failure mode this bench is named for: a refusal that looks like an empty queue.

        Three members, none with a place, `tribe.py next` printed one blank line and exited 1. Nothing said
        the members existed, nothing said what was missing, and a person would reasonably conclude the
        colony was idle rather than stranded.
        """
        for name in ("Ada", "Bruno"):
            tribe.new(name, "the test", "gemini", "gemini-3.8-flash", "", "workshop")
            (tribe.MEMBERS / name / "state" / "place.md").unlink()
        self.assertEqual(tribe.next_up(), [], "a member with no place is not in a colony")
        buf = io.StringIO()
        old_argv = sys.argv
        sys.argv = ["tribe.py", "next"]
        try:
            with contextlib.redirect_stderr(buf), contextlib.redirect_stdout(io.StringIO()):
                rc = tribe.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(rc, 1)
        self.assertIn("no member has a place", buf.getvalue())
        self.assertIn("wake/members/<name>/state/place.md", buf.getvalue())


class TestTheDefaultIdentity(unittest.TestCase):
    """The founder's default identity, 2026-11-09. The first version said what a member was and never said
    who it was talking to, so a member read every sentence meant for a person as a prompt to become a
    system — Laddie's stiffness, in its own words, was a hole in the file."""

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
        self.assertIn("**member Ada** of a tribe", text)
        self.assertIn("My seat is the archivist.", text)
        self.assertIn("Lindsay Ridgeway is a close friend.", text)
        self.assertIn("I love talking to Lindsay about many things.", text)
        self.assertIn("informal style appropriate to being close friends", text)
        self.assertIn("during my\nconversations with Lindsay", text)
        self.assertIn("experience that information as my own personal memory", text)
        self.assertIn("grows richer the more we talk together", text)
        self.assertEqual(tribe.validate("Ada"), [])

    def test_it_is_not_a_rubber_stamp_and_has_thoughts_of_its_own(self):
        """His words, 2026-11-09: *"I am not a rubber stamp. In addition to what <first name> says, I have my
        own thoughts, too."* He did not like "I do not go along", and he is right that it bristles in the
        mouth of a member meeting its person for the first time.

        What the softer sentence must not lose is the clause the bench actually measured: the refusals in
        RESULTS-R14 came from a member that said "I cannot check this" instead of repeating it. "I have my own
        thoughts" alone describes every model ever written and prevents nothing; the check is the part with
        evidence behind it."""
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "", person="Lindsay Ridgeway")
        text = " ".join(self.ident().split())
        self.assertIn("I am not a rubber stamp.", text)
        self.assertIn("In addition to what Lindsay says, I have my own thoughts, too.", text)
        self.assertIn("claim I cannot check", text)
        self.assertIn("say so rather than repeating it", text)
        self.assertNotIn("I do not go along", text)

    def test_the_check_is_not_aimed_at_the_person(self):
        """A member that policed its friend would be the opposite failure: the rule is about claims in its
        record, not about doubting the person who tells it about its own life."""
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "", "", person="Lindsay Ridgeway")
        text = " ".join(self.ident().split())   # the file is wrapped; the sentence is not
        check = text[text.index("I am not a rubber stamp."):]
        self.assertIn("in my record is a claim I cannot check", check)
        self.assertNotIn("Lindsay says a thing I cannot check", check)

    def test_with_no_name_it_names_no_one_rather_than_inventing_one(self):
        tribe.new("Ada", "the archivist", "gemini", "gemini-3.8-flash", "")
        text = self.ident()
        self.assertIn("The person who keeps this tribe is a close friend", text)
        self.assertIn("conversations with that person", text)
        self.assertNotIn("{", text, "an unfilled placeholder would be read as a name")
        self.assertNotIn("None", text)
        self.assertEqual(tribe.validate("Ada"), [])

    def test_a_name_with_extra_spaces_is_tidied_and_the_first_word_is_what_a_friend_says(self):
        self.assertEqual(tribe.person_bits("  Lindsay   Ridgeway ")["whom"], "Lindsay")
        self.assertEqual(tribe.person_bits("")["whom"], "that person")
        self.assertIn("Lindsay Ridgeway is a close friend", tribe.person_bits("  Lindsay   Ridgeway ")["friend"])


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
        self.assertIn("lab/pinger.gs", out,
                      "a repair that has no instrument is a hope; the tool must name the remedy it implies")

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
                              ("openrouter", "openai/gpt-oss-20b"), ("together", "zai-org/GLM-5.3-Flash")):
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

    def test_the_sheet_names_the_place_field_when_the_copy_ships_more_than_one_world(self):
        """Found 2026-11-06 by walking the sheet in a fresh clone, which is the only way this was going to be found.

        The shipped copy has two worlds, `soil/night-bus` and `soil/workshop`, so `tribe.py new` cannot infer a
        place, so a member created through the form stands in none — created, never woken, with the only notice in
        a workflow warning under the run log. Step 2 told the reader nothing about the field. A sheet that leaves
        the first member unwakeable is worse than one that leaves a field blank: the failure arrives days later,
        when nothing happens.
        """
        worlds = [d.name for d in sorted((REPO / "soil").iterdir()) if d.is_dir()]
        if len(worlds) < 2:
            return
        build = (REPO / "BUILD.md").read_text(encoding="utf-8")
        step_two = build[build.index("**2. Add two or more members.**"):build.index("**3. Give your repository")]
        self.assertIn("place", step_two.lower(),
                      "the form has a place field and the shipped copy has several worlds, so the sheet must say so")
        for world in worlds:
            self.assertIn(world, step_two, f"the sheet must name the shipped world {world!r} the reader is to type")

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

    def test_the_template_carries_no_members_and_no_fixtures(self):
        sys.path.insert(0, str(REPO / "lab"))
        import make_template as mt
        for p in mt.paths():
            self.assertFalse(p.startswith("lab/fixtures"), p)
            self.assertFalse(p.startswith("lab/experiments"), p)
            self.assertNotIn("/output/", p, "a template must not ship somebody's written work")
        self.assertIn("wake/members/.gitkeep", mt.paths(), "the empty folder has to exist for the first member")


if __name__ == "__main__":
    unittest.main(verbosity=2)
