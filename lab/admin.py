#!/usr/bin/env python3
"""The admin, as a conversation — the smallest first step of INTERFACE.md, and nothing more.

What this is: a state machine that creates one member by asking one question at a time, the way the founder
sketched it ("What name do you want for this member? No spaces."). It holds no model and makes no API calls.
That is deliberate and it is not laziness:

  * every option it offers is read from disk at the moment it is offered — the worlds from `soil/`, the
    engines from `.github/workflows/new-member.yml`, the members from `wake/members/` — so there is no list
    in this file that can go stale and no chance of it inventing a world that does not exist;
  * a conversation that needs a model to ask six questions would spend six calls and could still ask for a
    world the colony has not got. The model becomes worth its cost when the person says something the script
    did not anticipate ("make me three of them, one per world"), and that is a later step, done on top of
    this one rather than instead of it.

Why a state machine and not a Telegram bot: the state machine is the part a chat window would drive. Written
this way, a transport is a forty-line adapter that hands `answer()` a string and prints what comes back —
Telegram, a terminal, or the local page. Building the adapter first would have meant untestable code and a
token before there was anything to talk to.

    python3 lab/admin.py                # the conversation, in this terminal
    python3 lab/admin.py --dry-run      # the same conversation, but it prints the command instead of running it
"""
from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

# The four a person choosing for the first time actually wants, with one line each. "Something else" opens the
# full list, which is read from the workflow rather than copied here.
FIRST_FOUR = [
    ("gemini", "free to start, no card"),
    ("deepseek", "cheapest in practice"),
    ("groq", "fastest"),
]

NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,23}$")


def all_engines(repo: pathlib.Path = REPO) -> list[str]:
    """The engines the project supports, read from the form that offers them.

    Read rather than copied. A list in this file would be a second table for one fact, which is how a Groq
    member once woke and then found that tennis did not know it.

    Line by line, not by regex: the first version of this used a pattern with re.S and captured the rest of
    the workflow file, so the admin offered 121 "engines" numbered 1 to 121, most of them lines of YAML.
    """
    path = repo / ".github" / "workflows" / "new-member.yml"
    if not path.exists():
        return ["gemini"]
    found: list[str] = []
    inside = False
    collecting = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not inside:
            inside = stripped == "engine:"
            continue
        if stripped.startswith("options:"):
            collecting = True
            continue
        if collecting:
            if stripped.startswith("- "):
                found.append(stripped[2:].strip())
                continue
            break                       # the next key ends the list: `default:` and everything under it
    return found or ["gemini"]


def worlds(repo: pathlib.Path = REPO) -> list[str]:
    """The worlds this colony actually has, from the folders that describe them."""
    soil = repo / "soil"
    if not soil.is_dir():
        return []
    return sorted(p.name for p in soil.iterdir() if p.is_dir())


def members(repo: pathlib.Path = REPO) -> list[str]:
    base = repo / "wake" / "members"
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir())


class Admin:
    """One conversation, one member. `say()` in, list of messages out.

    The order is the founder's order, and the last question is always a confirmation — because the first
    member anyone makes is made without knowing what a world is, and a member that stands in none is never
    woken. Saying the whole thing back before writing it costs one message and prevents exactly that.
    """

    steps = ("name", "seat", "engine", "world", "confirm")

    def __init__(self, repo: pathlib.Path = REPO):
        self.repo = repo
        self.i = 0
        self.name = ""
        self.seat = ""
        self.engine = ""
        self.world = ""
        self.command: list[str] = []
        self.done = False
        self.engines_shown_all = False

    # --- what the admin is saying -------------------------------------------------------------
    def ask(self) -> str:
        step = self.steps[self.i]
        if step == "name":
            return ("Hello. This colony has %d member%s. Shall we make another?\n\n"
                    "What should it be called? One word, letters and numbers, no spaces."
                    % (len(members(self.repo)), "" if len(members(self.repo)) == 1 else "s"))
        if step == "seat":
            return ("%s. What is it for? A short phrase — \u201cthe correspondent\u201d, \u201cthe surveyor\u201d, "
                    "\u201cthe one who asks awkward questions\u201d." % self.name)
        if step == "engine":
            lines = ["Which engine should %s borrow? Each is a company whose model does its thinking." % self.name,
                     ""]
            for n, (engine, why) in enumerate(FIRST_FOUR, 1):
                lines.append("%d. %s \u2014 %s" % (n, engine, why))
            lines.append("%d. something else" % (len(FIRST_FOUR) + 1))
            return "\n".join(lines)
        if step == "world":
            got = worlds(self.repo)
            if not got:
                return ("This colony has no worlds yet \u2014 `soil/` is empty \u2014 so this member will be "
                        "created without one and no clock will wake it. Type anything to go on, or "
                        "\u201ccancel\u201d.")
            head = "This colony has one world, %s. Type it, or just say yes." % got[0] if len(got) == 1 else \
                   "This colony has %d worlds. Which does %s stand in?" % (len(got), self.name)
            return head + "\n\n" + "\n".join("%d. %s" % (n, w) for n, w in enumerate(got, 1))
        return ("That is everything:\n\n"
                "  name   %s\n  for    %s\n  engine %s\n  world  %s\n\n"
                "Make it? Say yes, or change something by naming it (name, for, engine, world)."
                % (self.name, self.seat, self.engine, self.world or "(no world)"))

    # --- what the person is saying ------------------------------------------------------------
    def say(self, text: str) -> list[str]:
        text = (text or "").strip()
        if self.done:
            return ["This conversation is over. Start again if you want another member."]
        low = text.lower()

        if low in ("cancel", "stop", "never mind", "nevermind", "no"):
            self.done = True
            return ["Cancelled. Nothing was written; no member exists that did not exist before."]

        if low in ("just do it", "do it", "whatever", "you choose", "defaults"):
            return self._defaults()

        step = self.steps[self.i]
        if step == "name":
            if not NAME_RE.match(text):
                return ["A name is one word, letters and numbers only, starting with a letter. Try again."]
            if text in members(self.repo):
                return ["%s already exists in this colony. Pick another name, or say \u201ccancel\u201d." % text]
            self.name = text
            self.i += 1
            return [self.ask()]

        if step == "seat":
            if len(text) < 3:
                return ["A little more than that \u2014 a short phrase is enough."]
            self.seat = text
            self.i += 1
            return [self.ask()]

        if step == "engine":
            picked = self._pick(text, [e for e, _ in FIRST_FOUR])
            if picked is None and low in ("4", "something else", "other", "else"):
                rest = [e for e in all_engines(self.repo) if e not in dict(FIRST_FOUR)]
                self.engines_shown_all = True
                return ["There are %d others:\n\n%s\n\nWhich?" % (
                    len(rest), "\n".join("%d. %s" % (n, e) for n, e in enumerate(rest, 1)))]
            if picked is None:
                picked = self._pick_any_engine(text)
            if picked is None:
                return ["One of the numbers, please, or \u201csomething else\u201d."]
            self.engine = picked
            self.i += 1
            return [self.ask()]

        if step == "world":
            got = worlds(self.repo)
            if not got:
                self.world = ""
                self.i += 1
                return [self.ask()]
            picked = self._pick(text, got)
            if picked is None and low in ("yes", "y", "ok", "okay", "sure") and len(got) == 1:
                picked = got[0]
            if picked is None:
                return ["One of those, please \u2014 %s." % ", ".join(got)]
            self.world = picked
            self.i += 1
            return [self.ask()]

        # confirm
        if low in ("yes", "y", "ok", "okay", "make it", "do it"):
            self.done = True
            self.command = self._argv()
            return ["Making %s now." % self.name]
        for field in ("name", "for", "engine", "world"):
            if low.startswith(field):
                self.i = self.steps.index("name" if field == "name" else
                                          "seat" if field == "for" else field)
                return ["Fine \u2014 " + self.ask()]
        return ["Say yes to make it, or name what to change: name, for, engine, world."]

    # --- helpers ------------------------------------------------------------------------------
    def _pick(self, text: str, options: list[str]) -> str | None:
        if text.isdigit():
            n = int(text)
            if 1 <= n <= len(options):
                return options[n - 1]
            return None
        for o in options:
            if text.lower() == o.lower():
                return o
        return None

    def _pick_any_engine(self, text: str) -> str | None:
        everything = all_engines(self.repo)
        for e in everything:
            if text.lower() == e.lower():
                return e
        if self.engines_shown_all:
            rest = [e for e in everything if e not in dict(FIRST_FOUR)]
            return self._pick(text, rest)
        return None

    def _defaults(self) -> list[str]:
        """'just do it' picks the sensible thing at every remaining step and says which it picked."""
        picks = []
        if not self.name:
            base, n = "Maud", 1
            while base in members(self.repo):
                n += 1
                base = "Maud%d" % n
            self.name, picks = base, picks + ["name %s" % base]
        if not self.seat:
            self.seat, picks = "the newcomer", picks + ["for \u201cthe newcomer\u201d"]
        if not self.engine:
            self.engine, picks = FIRST_FOUR[0][0], picks + ["engine %s" % FIRST_FOUR[0][0]]
        if not self.world:
            got = worlds(self.repo)
            self.world = got[0] if got else ""
            picks = picks + ["world %s" % (self.world or "(none)")]
        self.i = self.steps.index("confirm")
        return ["You choose, then \u2014 " + ", ".join(picks) + ".", self.ask()]

    def _argv(self) -> list[str]:
        args = [sys.executable, "tribe.py", "new", self.name, "--seat", self.seat, "--api", self.engine]
        if self.world:
            args += ["--place", self.world]
        return args


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="make one member, one question at a time")
    ap.add_argument("--dry-run", action="store_true",
                    help="hold the whole conversation, then print the command instead of running it")
    ap.add_argument("--repo", default=str(REPO))
    args = ap.parse_args(argv)

    repo = pathlib.Path(args.repo)
    admin = Admin(repo)
    print("admin: " + admin.ask() + "\n")
    while not admin.done:
        try:
            said = input("you: ")
        except EOFError:
            print("\n(nothing more typed, so nothing was made)")
            return 2
        for message in admin.say(said):
            if message:
                print("\nadmin: " + message + "\n")
        if admin.done and admin.command:
            if args.dry_run:
                print("would run: " + " ".join(admin.command[1:]))
                return 0
            done = subprocess.run(admin.command, cwd=repo, capture_output=True, text=True)
            print(done.stdout.strip())
            if done.returncode != 0:
                print(done.stderr.strip(), file=sys.stderr)
            return done.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
