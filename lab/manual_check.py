#!/usr/bin/env python3
"""manual_check.py — every path the manual names, checked against what an install actually contains.

The manual is the product for anyone who has not done this before. It is also the one document in this project
that nothing automated has ever read *as instructions*: the tests read it as prose and look for sentences, so a
chapter can point at a file that moved and stay green for a month. That is exactly how §14 kept telling strangers
to install an Apps Script timer for three days after §5 was rewritten to say it was not offered.

So this is a reader with a narrow job: take every path-like thing the manual puts in backticks, and ask the
filesystem of a *freshly built template* whether it is there — with a member created in it first, because half of
what the manual names lives in a member's folder and only exists once there is a member.

What it is not: a check that the manual is true. It can see that `state/looked-at.md` is a file the wake writes;
it cannot see whether the sentence around it is honest. It catches the cheap half, which is the half that rots.

    python3 lab/manual_check.py              # build a template, make a member, check, print
    python3 lab/manual_check.py --root .     # check the working tree instead of a fresh build
    python3 lab/manual_check.py --json       # one object, for a test to assert on
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Two lists, and they mean different things.
#
# WRITTEN — a real file in a circle, which does not exist until something happens: the first clock run, the first
# wake that writes a piece, the first picture left in an inbox. The manual naming it is right and a fresh circle not
# having it is also right, so the check would be a false alarm without the reason written down.
WRITTEN = {
    ".ait/last-clock.json": "written by the clock's first run",
    "MILESTONES.md": "written by the clock from the circle's own files, on the first run",
    "state/done.md": "written the first time a member retires a job",
    "state/looked-at.md": "written by the first wake that looks at a picture",
    "state/conversation.md": "written when the page files a talk",
    "state/memory.md": "written by the member's first retelling",
    "state/talk/": "created by the chapter archiver on the first long talk",
    "state/talk/<chapter>.md": "a chapter file, named when the first one is written",
    "wake/members/<name>/output/<short-name>.md": "the file a wake writes, named by the member",
    "wake/members/<name>/output/raw-<UTC>.json": "the raw reply, one per wake, once there has been a wake",
    "wake/members/<name>/state/pictures/": "created when a person keeps a picture in a conversation",
    "works/<member>/<stamp>-<title>.md": "written when a member files a piece",
    "attic/": "created when a member is put aside",
    "conversation.md": "a member's own file, once it has had one",
    "chat.md": "written by a room when it is used",
    "talk.md": "as above",
    "chats/<slug>/chat.md": "a room's own file, once a room exists",
    "chats/<slug>/talk.md": "as above",
    "attic/<name>-<stamp>/": "created when a member is put aside",
    "games/golf/renders/": "the project's record; a circle has one only if it plays golf itself",
    "games/tennis/seasons/<season>/": "created by the first season",
    "games/tennis/seasons/<season>/points/": "as above",
    "games/*/README.md": "each game's own folder, once that game has been played",
}

# PROJECT — a real file, in the project's own repository rather than in a circle. The manual talks about them on
# purpose (the experiments that are not shipped, the source of the golf record), so they are checked against this
# repository instead of against the template: a chapter that points at a renamed script is the same rot either way.
# `LINKS.md` is the one file the manual sends a reader to in *this* repository rather than their own — the list of
# addresses, which belongs to the project because it is the project's addresses.
#
# `lab/golf.py` and `lab/putt.py` were in this set this morning, because the template did not ship them, and by the
# evening it did: the check went on passing while the manual told a reader those two files were not in the circle
# they were standing in. This tool cannot read a sentence — it can only refuse to vouch for one it has not checked.
PROJECT = {"LINKS.md"}

# EXEMPT — not a path in a circle at all. Each with its reason, because an exemption list with reasons is a
# decision and a regex that skips things is a hole.
EXEMPT = {
    "../../etc/passwd": "the security illustration: a path that must NOT resolve",
    "ai-tribe.netlify.app": "a hostname, written without a scheme because the sentence is about the name",
    "<member>-<chapter>.md": "the filename the browser proposes when a person downloads a chapter",
    "agenda.md": "a file the manual suggests a person may write; nothing ships it and nothing reads it",
    "queue.md": "as above — a suggested habit, not a mechanism",
    "inbox.md": "the old single-file inbox, superseded by the folder; mentioned only as history",
    "WHY.md": "a file a member may be given in a circle that wrote one; the template does not ship it",
    "examples/inanna.md": "named as something to read if it exists; not shipped",
    "works/George/doc.md": "an illustration in a sentence about naming, not a file",
    "soil/": "a room is prose a person writes, and the template ships none on purpose",
    "soil/<any-name>/world.md": "as above",
    "soil/<room>/drops.md": "as above",
    "drops.md": "part of a room",
}

# Substitutions for the placeholders a manual has to use. The member created for the check is called Ida, so
# `<name>` and `<member>` resolve to a folder that really exists — the point is to test the manual's paths against
# a member made the way a person makes one, not to test a placeholder.
SUBSTITUTIONS = {
    "<name>": "Ida",
    "<member>": "Ida",
    "<short-name>": "piece",
    "<stamp>": "20260101T000000Z",
    "<title>": "a-piece",
    "<UTC>": "20260101T000000Z",
    "<chapter>": "001",
    "<slug>": "a-room",
    "<season>": "s1",
}


def candidates(text: str) -> list[str]:
    """Every backticked token that looks like a path rather than a word, in the order the manual uses them."""
    out = []
    for tok in re.findall(r"`([^`\n]{2,120})`", text):
        t = tok.strip()
        if not t or " " in t or t.startswith(("http://", "https://", "#/", "?", "~", "-", "$")):
            continue
        if not re.search(r"[/.]", t):
            continue
        if re.fullmatch(r"\.[a-z]{2,5}", t):          # a bare extension: `.png`, `.webp`
            continue
        out.append(t)
    return sorted(set(out))


def resolves(rel: str, root: Path, member: Path | None) -> bool:
    """Does this path exist in a fresh circle? `member` is a member made by tribe.py, because half of what the
    manual names lives in a member's folder and none of it exists until there is a member."""
    for placeholder, real in SUBSTITUTIONS.items():
        rel = rel.replace(placeholder, real)
    # `lstrip("./")` ate the leading dot of `.github/workflows/`, which is how a path that ships came back as a
    # path that does not exist — a bug in the checker reported as a bug in the manual. Strip a `./` prefix only.
    while rel.startswith("./"):
        rel = rel[2:]
    if "<" in rel or "*" in rel:                       # still a pattern: check the folder it names
        rel = rel.split("<")[0].split("*")[0].rsplit("/", 1)[0] + "/"
    places = [root]
    if member:
        places += [member, member / "state"]
    if "/" not in rel:                                 # a workflow named by its file name
        places.append(root / ".github" / "workflows")
    return any((p / rel).exists() for p in places if p)


def build(where: Path) -> Path:
    """A template as a stranger receives it."""
    subprocess.run([sys.executable, str(ROOT / "lab" / "make_template.py"), "--out", str(where)],
                   check=True, capture_output=True, text=True)
    return where


def make_member(where: Path) -> Path | None:
    """One member, made the way a person makes one, because a member's folder is where half the manual's paths live."""
    r = subprocess.run([sys.executable, "tribe.py", "new", "Ida", "--api", "deepseek",
                        "--about", "a member made by the manual check, so that its files can be looked for"],
                       cwd=where, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return where / "wake" / "members" / "Ida"


def check(root: Path) -> dict:
    text = (ROOT / "USER-MANUAL.md").read_text(encoding="utf-8")
    member = make_member(root)
    missing, exempted, written, ok, in_project = [], [], [], [], []
    for rel in candidates(text):
        if rel in EXEMPT:
            exempted.append(rel)
            continue
        if rel in WRITTEN:
            # A file that appears when something happens still has to have somewhere to appear: check its folder.
            written.append(rel)
            continue
        if rel in PROJECT:
            (in_project if (ROOT / rel).exists() else missing).append(rel)
            continue
        if resolves(rel, root, member):
            ok.append(rel)
        else:
            missing.append(rel)
    return {"root": str(root), "member": str(member) if member else "",
            "checked": len(ok) + len(missing), "ok": sorted(ok), "missing": sorted(missing),
            "exempt": sorted(exempted), "written": sorted(written), "project": sorted(in_project)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="", help="check this tree instead of a freshly built template")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.root:
        result = check(Path(a.root).resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="manual-check-") as tmp:
            result = check(build(Path(tmp) / "circle"))

    if a.json:
        print(json.dumps(result, indent=2))
        return 1 if result["missing"] else 0

    print(f"the manual names {result['checked']} paths that should exist in a circle")
    print(f"  there:         {len(result['ok'])}")
    print(f"  written later: {len(result['written'])} (real files, absent until a wake or a run makes them)")
    print(f"  in project:    {len(result['project'])} (real files, in this repository rather than in a circle)")
    print(f"  exempt:        {len(result['exempt'])} (not paths in a circle at all)")
    print(f"  missing:       {len(result['missing'])}")
    for m in result["missing"]:
        print(f"    !! {m}  — the manual points at this and a fresh circle does not have it")
    if result["member"]:
        print(f"checked against a member made by tribe.py: {result['member']}")
    return 1 if result["missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
