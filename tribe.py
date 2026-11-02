#!/usr/bin/env python3
"""Create a member, check a member, list the tribe.

Before this file, "make a new member" meant copying a directory and hoping. Nothing wrote down which
files are load-bearing, and a member created wrong failed silently — at its first wake, with a model
improvising around a missing identity. This is the schema as executable code rather than as prose.

    python3 tribe.py new d --seat "the archivist" --api gemini --model gemini-3.8-flash
    python3 tribe.py validate          (all members)
    python3 tribe.py validate d
    python3 tribe.py status
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent
MEMBERS = REPO / "wake" / "members"
BASES = {"deepseek", "gemini", "qwen", "groq", "openrouter", "cerebras", "mistral", "openai"}

# Who writes each file, and what it is for. The "who" column is the part that was missing: the harness
# maintains state.md's three lines and appends to journal.md, and a human editing those by hand is how a
# member silently stops incrementing.
REQUIRED = {
    "identity.md": ("member", "who it is — name, seat, and the rule it holds itself to"),
    "state.md": ("harness", "what it currently thinks; exactly three lines are maintained (Wakes so far, Last wake, Model used)"),
    "open-items.md": ("member", "numbered things it is trying to do"),
    "journal.md": ("harness+member", "what it did at each wake, appended, never rewritten"),
    "voice.md": ("human", "which API and model it borrows"),
}
OPTIONAL = {
    "place.md": ("human", "which soil this member stands in: one line, `place: <directory under soil/>`. "
                          "Two colonies can share a repository and live in different worlds"),
    "beat.md": ("member", "what this member is interested in, as opposed to what it was asked; read into "
                          "every wake. Not a task list, and nobody assigns it"),
    "brief.md": ("human+convener", "what the tribe is working on now; included in the prompt"),
    "requests.md": ("member", "read-only checks it wants run before its next wake"),
    "findings.md": ("harness", "what those checks said"),
}

STATE_LINES = ("Wakes so far:", "Last wake:", "Model used:")

IDENTITY = """# Identity — member {name}

I am **member {name}** of a tribe{of}. My seat is {seat}.

I wake with no memory. Everything I know is the text I am handed: my identity, my state, my open items,
my journal, and a block of measurements the harness took seconds ago. My rule: **I do not go along.** If
something in my record says a thing I cannot check, I say so rather than repeating it.

My record is these files. What is not written down did not happen to me.
"""

OPEN_ITEMS = """# Open items

1. Read my identity and my journal, then write one file that says what I am for. Number the items you
   add; the harness acts on one item per wake and a duplicate number makes it pick the wrong one.
"""


def member_dirs() -> list[Path]:
    return sorted(p for p in MEMBERS.glob("*") if p.is_dir())


def validate(name: str) -> list[str]:
    base = MEMBERS / name
    bad: list[str] = []
    if not base.is_dir():
        return [f"no such member: {base}"]
    state = base / "state"
    if not state.is_dir():
        return [f"missing directory: {state}"]
    for fname, (who, why) in REQUIRED.items():
        f = state / fname
        if not f.exists():
            bad.append(f"{fname} is missing — {why} (written by {who})")
        elif not f.read_text(encoding="utf-8").strip():
            bad.append(f"{fname} is empty — {why}")
    if (state / "identity.md").exists():
        text = (state / "identity.md").read_text(encoding="utf-8")
        if len(text) < 100:
            bad.append("identity.md is under 100 characters — a member with no identity improvises one")
        if f"member {name}" not in text.lower():
            bad.append(f"identity.md does not name this member as 'member {name}'")
    if (state / "state.md").exists():
        text = (state / "state.md").read_text(encoding="utf-8")
        for line in STATE_LINES:
            if not re.search(re.escape(line) + r"\s*\S", text):
                bad.append(f"state.md is missing its '{line}' line — the harness will not increment without it")
    if (state / "voice.md").exists():
        text = (state / "voice.md").read_text(encoding="utf-8")
        api = re.search(r"^api:\s*(\S+)", text, re.M)
        model = re.search(r"^model:\s*(\S+)", text, re.M)
        if not api:
            bad.append("voice.md has no 'api:' line")
        elif api.group(1) not in BASES:
            bad.append(f"voice.md names api '{api.group(1)}', which is not one of {sorted(BASES)}")
        if not model:
            bad.append("voice.md has no 'model:' line")
    if (state / "open-items.md").exists():
        nums = re.findall(r"^\s*(\d+)\.", (state / "open-items.md").read_text(encoding="utf-8"), re.M)
        dupes = {n for n in nums if nums.count(n) > 1}
        if dupes:
            bad.append(f"open-items.md repeats item number(s) {sorted(dupes)} — the harness takes the first match")
    if not (base / "output").is_dir():
        bad.append(f"missing directory: {base / 'output'} — a wake writes its act there")
    return bad


def new(name: str, seat: str, api: str, model: str, of: str) -> int:
    base = MEMBERS / name
    if base.exists():
        print(f"!! {base} already exists — refusing to overwrite a member's record")
        return 2
    (base / "state").mkdir(parents=True)
    (base / "output").mkdir()
    (base / "state" / "identity.md").write_text(IDENTITY.format(name=name, seat=seat, of=of), encoding="utf-8")
    (base / "state" / "state.md").write_text(
        "# State\n\nWakes so far: 0\nLast wake: never\nModel used: (none yet)\n\n"
        "**Nothing has been verified yet. Every claim below is a proposal, not a finding.**\n",
        encoding="utf-8")
    (base / "state" / "open-items.md").write_text(OPEN_ITEMS, encoding="utf-8")
    (base / "state" / "journal.md").write_text(
        f"# Journal — member {name}\n\n## {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC — created\n\n"
        f"- I was created by `tribe.py new`. I have not woken yet.\n", encoding="utf-8")
    (base / "state" / "voice.md").write_text(
        f"# Voice — member {name}\n\nThe model this member borrows. Changing the model here does not make "
        f"it someone else: the member is its files.\n\napi: {api}\nmodel: {model}\n", encoding="utf-8")
    (base / "state" / "requests.md").write_text(
        "# Checks I want run before my next wake\n\n", encoding="utf-8")
    (base / "state" / "findings.md").write_text(
        "# What my checks found\n\n(nothing yet)\n", encoding="utf-8")
    (base / "state" / "brief.md").write_text(
        "# Brief — what this tribe is working on now\n\n"
        "**Closes soonest:** (nothing has a deadline yet)\n\n"
        "**Waiting on you**\n\n- (empty)\n\n"
        "**Queued**\n\n1. Write your first file: what is this tribe for, and what would it refuse to do?\n",
        encoding="utf-8")
    bad = validate(name)
    if bad:
        print("created, but it does not validate:")
        for b in bad:
            print("  !!", b)
        return 1
    print(f"created member {name} ({seat}) on {api}/{model}; it validates")
    print(f"next: ./talk.sh {name} \"read your identity and say what you are for\"")
    return 0


def place_of(d: Path) -> str:
    try:
        line = (d / "state" / "place.md").read_text(encoding="utf-8").strip().splitlines()[0]
        return line.split(":", 1)[1].strip() if ":" in line else ""
    except (OSError, IndexError):
        return ""


def wakes_of(d: Path) -> int:
    try:
        s = (d / "state" / "state.md").read_text(encoding="utf-8")
    except OSError:
        return 0
    m = re.search(r"Wakes so far:\s*(\d+)", s)
    return int(m.group(1)) if m else 0


def next_up() -> list[tuple[str, str]]:
    """Whose turn it is, one member per place: the one with the fewest wakes.

    RUN.md §10 has said since the beginning that nothing decides whose turn it is. This decides it, and it
    decides it by count rather than by name, so a cron that fires while a member is broken does not starve
    the others and a member that nobody wakes does not fall silently behind. Ties break alphabetically,
    which is arbitrary and *recorded* as arbitrary — the alternative (a roster in a file) is a roster
    somebody edits to favour somebody.
    """
    by_place: dict[str, list[Path]] = {}
    for d in member_dirs():
        if not (d / "state" / "voice.md").exists():
            continue   # a member with no voice cannot be woken at all; counting it would stall the clock
        if not place_of(d):
            continue   # a fixture with no place is not in a colony; scheduling it would wake the lab rats
        by_place.setdefault(place_of(d), []).append(d)
    out = []
    for place in sorted(by_place):
        group = sorted(by_place[place], key=lambda d: (wakes_of(d), d.name))
        out.append((place or "(no place)", group[0].name))
    return out


def status() -> int:
    ds = member_dirs()
    if not ds:
        print("no members")
        return 1
    print(f"{'member':8} {'wakes':>6} {'last wake':22} {'model':22} problems")
    for d in ds:
        state = d / "state"
        s = (state / "state.md").read_text(encoding="utf-8") if (state / "state.md").exists() else ""
        wakes = (re.search(r"Wakes so far:\s*(\d+)", s) or [None, "?"])[1]
        last = (re.search(r"Last wake:\s*(.+)", s) or [None, "?"])[1].strip()[:20]
        model = (re.search(r"Model used:\s*(.+)", s) or [None, "?"])[1].strip()[:20]
        bad = validate(d.name)
        print(f"{d.name:8} {wakes:>6} {last:22} {model:22} {len(bad) or 'ok'}")
        for b in bad:
            print("   !!", b)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("name")
    n.add_argument("--seat", default="the newcomer")
    n.add_argument("--api", default="gemini", choices=sorted(BASES))
    n.add_argument("--model", default="gemini-3.8-flash")
    n.add_argument("--of", default="", help="e.g. ' of three' — appears in the identity")
    a = ap.add_argument_group("validate/status")
    sub.add_parser("validate").add_argument("name", nargs="?")
    sub.add_parser("status")
    sub.add_parser("next", help="whose turn it is, one member per place")
    args = ap.parse_args()

    if args.cmd == "new":
        return new(args.name, args.seat, args.api, args.model, args.of)
    if args.cmd == "validate":
        names = [args.name] if args.name else [d.name for d in member_dirs()]
        rc = 0
        for nm in names:
            bad = validate(nm)
            print(f"{nm}: " + ("ok" if not bad else f"{len(bad)} problem(s)"))
            for b in bad:
                print("  !!", b)
            rc = rc or (1 if bad else 0)
        return rc
    if args.cmd == "next":
        rows = next_up()
        for place, name in rows:
            print(f"{place}\t{name}")
        return 0 if rows else 1
    return status()


if __name__ == "__main__":
    sys.exit(main())
