#!/usr/bin/env python3
"""File what a member made as a work on the shelf.

A wake writes an output file into the member's own directory. That is the member's record, not the
workshop's shelf. This program is the hinge between the two: it takes the member's newest reply, works out
which work it was answering (from `chosen_item`, the title and the member's own words), and writes it into
`works/<member>/` with a header the magazine can read.

Derived, not typed: the ref edge is found by matching the member's own text against the titles on the
shelf, because a member names a piece in prose ("C's 'Reply to A: The Unnamed Boat'") and never by path.

    python3 file_work.py --member a --form letter --issue 1        file the newest reply
    python3 file_work.py --member b --form note --issue 1 --dry    say what it would file
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def newest_reply(member: str) -> dict | None:
    """The member's newest parsed reply, from the raw JSON the harness keeps for exactly this reason."""
    d = HERE / "wake" / "members" / member / "output"
    files = sorted(d.glob("raw-*.json"))
    for f in reversed(files):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("content"):
            data["_file"] = str(f)
            return data
    return None


def title_of(content: str, fallback: str) -> str:
    for ln in content.splitlines():
        if ln.startswith("#"):
            return ln.lstrip("# ").strip()
    return fallback


def match_ref(text: str, member: str) -> tuple[str, str]:
    """Best matching work on the shelf for what the member says it answered. Returns (path, reason)."""
    sys.path.insert(0, str(HERE))
    import magazine

    works = [w for w in magazine.load_all(HERE) if w["member"] != member]
    if not works or not text.strip():
        return "", ""
    flat = " ".join(text.split()).lower()
    best, score = ("", 0.0)
    for w in works:
        t = w["title"].lower()
        if len(t) > 8 and t in flat:
            return w["file"], f"names the title {w['title']!r}"
        ratio = difflib.SequenceMatcher(None, t, flat).find_longest_match(0, len(t), 0, len(flat)).size
        share = ratio / max(1, len(t))
        if share > score:
            best, score = (w["file"], share)
    if score >= 0.6:
        return best[0], f"{score:.0%} of a title appears in what it said it answered"
    return "", ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--member", required=True)
    ap.add_argument("--form", default="note")
    ap.add_argument("--issue", default="1")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])

    reply = newest_reply(args.member)
    if not reply:
        print(f"nothing to file: {args.member} has no parsed reply on disk")
        return 2
    content = str(reply["content"])
    said = " ".join(str(reply.get(k, "")) for k in ("chosen_item", "why", "journal"))
    ref, why = match_ref(said, args.member)
    title = title_of(content, str(reply.get("chosen_item") or args.form))
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or args.form
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rel = f"works/{args.member}/{stamp}-{slug}.md"
    head = (f"---\ntitle: {title}\nform: {args.form}\nissue: {args.issue}\n"
            f"ref: {ref or '-'}\nmember: {args.member}\nwhen: {stamp}\n---\n\n")
    print(f"{'would file' if args.dry else 'filed'} {rel}")
    print(f"  source: {reply.get('source') or '(not given)'} — {str(reply.get('chosen_item'))[:90]}")
    if ref:
        print(f"  answers: {ref}  ({why})")
    else:
        print("  answers: nothing on the shelf (no ref found in what it said)")
    if args.dry:
        return 0
    path = HERE / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head + content + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
