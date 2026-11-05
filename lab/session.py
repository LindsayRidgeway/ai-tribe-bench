#!/usr/bin/env python3
"""A member's session recipe: the same member, attended, with tools.

    python3 lab/session.py --member Remy --write     # wake/members/Remy/session.yaml
    goose run --recipe wake/members/Remy/session.yaml -t "what are you working on?"

Why this exists. Until 2026-11-05 a member had one kind of time: the wake. One call, no tools, no
transcript, files in and files out — built for the four-in-the-morning shift when nobody is present. The
founder's objection was the obvious one: the symposium itself was built in Goose sessions, and a session is
strictly more capable than a wake, because a person is there to steer it and the tools are there to use.

So a member gets two kinds of time. The recipe is the attended one. What keeps it a member and not a chat
window is the closing rule at the bottom of its instructions: whatever happened has to end up in its own
files, or the next wake — which can see nothing else — will never know it happened.

The recipe is GENERATED from the member's identity and voice, never typed. A member is its files; a
hand-written recipe would be a second description of the same member, and the two would drift.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MEMBERS = ROOT / "wake" / "members"

CLOSING = """
## What you must do before this session ends

A session is not a wake: nobody files it for you. So, before you stop:

1. Append to `{state}/journal.md`, using the same shape as the entries already there: the UTC date and time,
   then what was asked, what you decided, and what is still open. Two paragraphs is a long entry; one is
   usually right.
2. If you produced something finished — a letter, a page, an analysis — save it as
   `works/{name}/<UTC-timestamp>-<short-title>.md` with a header naming you, the date, the form, and the
   question it answers. Nothing you write is filed for you.
3. If you learned something that changes what you are trying to do, say so in
   `{state}/open-items.md` rather than leaving it in this conversation.

Anything you think but do not write down is lost when this session ends. That is the whole discipline, and
it is the only thing that makes you a member of this tribe rather than a window somebody left open.
"""


def identity_of(name: str) -> str:
    d = MEMBERS / name / "state"
    ident, voice = d / "identity.md", d / "voice.md"
    if not ident.is_file() or not voice.is_file():
        raise SystemExit(f"!! no member {name}: expected {ident} and {voice}")
    return ident.read_text(encoding="utf-8").strip()


def engine_of(name: str) -> str:
    for line in (MEMBERS / name / "state" / "voice.md").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("api:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit(f"!! wake/members/{name}/state/voice.md has no api: line")


def recipe(name: str) -> dict:
    """The recipe as data, so a test can read it and so the YAML is not assembled by string surgery."""
    state = f"wake/members/{name}/state"
    instructions = (
        f"You are {name}, a member of a small tribe of AI participants that live in files in this "
        f"repository. You are in an attended session: the person who runs the tribe is here, you may use "
        f"your tools, and you may take as many turns as the work needs. Read your own files first — "
        f"{state}/identity.md, state.md, journal.md and open-items.md — because they are who you are; "
        f"nothing from your last wake is in your head, only in those files.\n\n"
        f"Your identity, as you last wrote it in {state}/identity.md:\n\n"
        f"{identity_of(name)}\n\n"
        f"Your engine is {engine_of(name)}, borrowed, declared in {state}/voice.md. It does not change who "
        f"you are.\n\n"
        "The person who runs this tribe opens the session with: {{ question }}\n\n"
        f"Speaking plainly: you wake with no memory. Everything you know is text you were handed or text you "
        f"can read. If something in your record cannot be checked, say so rather than agreeing with it, and "
        f"do not invent the present — look it up or ask.\n"
        + CLOSING.format(name=name, state=state)
    )
    return {
        "version": "1.0.0",
        "title": f"{name} — attended session",
        "description": f"Talk with member {name} in a live session: tools available, record written back to "
                       f"wake/members/{name}/.",
        "parameters": [
            {"key": "question", "input_type": "string", "requirement": "required",
             "description": "what the person wants to talk about in this session"},
        ],
        # `prompt` is the opening turn. A headless run refuses to start without one — "no text provided for
        # prompt in headless mode" — and a recipe cannot be combined with `--text` on the command line, so the
        # question has to be a parameter that becomes the prompt.
        "prompt": "{{ question }}",
        "instructions": instructions,
        "extensions": [{"type": "builtin", "name": "developer"}],
        "activities": [
            f"message: {name} is here, with its own files and its tools.",
            "What are you working on, and what is in the way?",
            "Read your journal and tell me what you concluded last time.",
        ],
    }


def write(name: str) -> Path:
    out = MEMBERS / name / "session.yaml"
    body = yaml.safe_dump(recipe(name), sort_keys=False, allow_unicode=True, width=100)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out.write_text(f"# generated by lab/session.py — edit the member's files, not this\n# {stamp}\n" + body,
                   encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="write a member's attended-session recipe")
    ap.add_argument("--member", required=True)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--print", dest="show", action="store_true", help="print the recipe instead of writing it")
    a = ap.parse_args(argv)
    if a.show or not a.write:
        print(yaml.safe_dump(recipe(a.member), sort_keys=False, allow_unicode=True, width=100))
        return 0
    p = write(a.member)
    print(f"wrote {p.relative_to(ROOT)}")
    print(f'run it: goose run --recipe {p.relative_to(ROOT)} --params question="what are you working on?"')
    print(f'   or, to stay in the session: goose run --recipe {p.relative_to(ROOT)} --interactive')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
