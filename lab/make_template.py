#!/usr/bin/env python3
"""Build the tribe template — the files an installed tribe actually needs.

Why a separate repository rather than a flag on this one: a tribe is not a copy of the bench. The
bench carries fixtures, experiment logs, eleven hundred game records and the tests that guard them.
An owner opening their tribe should find their members and nothing else.

Why a whitelist rather than a blacklist: a new file lands in this repository most days. A blacklist
would ship each one to every future owner until somebody noticed. A whitelist ships only files
somebody decided a tribe needs, and adding one is a decision that shows up in a diff.

    python3 lab/make_template.py --out /tmp/tribe-template
    python3 lab/make_template.py --out /tmp/tribe-template --check   # report missing paths only

The `--check` mode is the one that belongs in tests: it fails if a whitelisted path has been
deleted, which would otherwise turn into a broken install and a puzzled owner.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# A tribe needs three things: the harness that wakes a member, the workflows that schedule it, and
# the empty rooms it will fill. Everything else in this repository is the project's own record.
FILES = """
.github/workflows/clock.yml
.github/workflows/wake.yml
.github/workflows/interactive.yml
.github/workflows/new-member.yml
.github/workflows/attic.yml
.github/workflows/play.yml
.github/workflows/season.yml
tribe.py
brief.py
check.py
file_work.py
magazine.py
outbox.py
talk.sh
members.json
wake/wake.py
wake/members/.gitkeep
play/play.py
play/behaviour.py
play/behaviour.md
play/log.py
lab/members.py
lab/tennis.py
lab/rps.py
issues/README.md
letters/README.md
plates/README.md
README.md
USER-MANUAL.md
REFERENCE.md
MANIFEST.md
.gitignore
""".split()

# Whole directories that are content rather than code: the worlds a member can be placed in, as
# examples the owner can copy or delete.
DIRS = ["soil"]

TEMPLATE_README = """# Your tribe

This is your tribe's repository. AIT is the page you read it with; this is the record.

- `wake/members/` — your members. One folder each. Empty until you make one.
- `soil/` — the rooms a member can live in. Two are here as examples.
- `.github/workflows/` — the clock that wakes a member, and the jobs AIT starts for you.
- `USER-MANUAL.md` — the manual. It is the longest file here and the only one you may want to read.
- `REFERENCE.md` — every file, what writes it, what breaks without it.

You do not need to edit anything. If you do, keep it text: the tribe is plain Markdown and Python
read by a machine that has no database.

**This repository is private and should stay private.** It holds your members' diaries.
"""


def workflow_refs() -> dict[str, list[str]]:
    """Every script a shipped workflow runs, mapped to the workflows that run it.

    The whitelist is hand-kept, so it can fall behind: a workflow starts calling a script that was
    never added, and the install is broken in a way no test on this repository would notice, because
    here the file exists. This is the check that notices.
    """
    out: dict[str, list[str]] = {}
    for wf in sorted((ROOT / ".github/workflows").glob("*.yml")):
        if str(wf.relative_to(ROOT)) not in FILES:
            continue
        text = wf.read_text()
        for m in re.finditer(r"python3\s+([A-Za-z0-9_./-]+\.py)", text):
            out.setdefault(m.group(1), []).append(wf.name)
        for m in re.finditer(r"\./([A-Za-z0-9_./-]+\.sh)", text):
            out.setdefault(m.group(1), []).append(wf.name)
    return out


def unshipped(include_dirs: bool = True) -> dict[str, list[str]]:
    """Scripts a workflow runs that the template would not contain."""
    shipped = set(FILES)
    if include_dirs:
        for d in DIRS:
            shipped |= {str(p.relative_to(ROOT)) for p in (ROOT / d).rglob("*") if p.is_file()}
    return {k: v for k, v in workflow_refs().items() if k not in shipped}


def paths() -> list[str]:
    out = list(FILES)
    for d in DIRS:
        base = ROOT / d
        if not base.is_dir():
            continue
        out += [str(p.relative_to(ROOT)) for p in sorted(base.rglob("*")) if p.is_file()]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="directory to build the template into")
    ap.add_argument("--check", action="store_true", help="only report whitelisted paths that are missing")
    a = ap.parse_args()
    if not a.check and not a.out:
        ap.error("--out is required unless --check")

    want = paths()
    missing = [p for p in want if not (ROOT / p).is_file()]
    if a.check:
        for p in missing:
            print(f"missing: {p}")
        print(f"{len(want) - len(missing)}/{len(want)} present")
        bad = unshipped()
        for script, wfs in bad.items():
            print(f"a workflow runs {script}, which the template does not ship ({', '.join(wfs)})")
        return 1 if (missing or bad) else 0

    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for p in want:
        if p in missing:
            print(f"missing, skipped: {p}", file=sys.stderr)
            continue
        dst = out / p
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / p, dst)
    (out / "README.md").write_text(TEMPLATE_README)
    print(f"built {out}: {len(want) - len(missing)} files")
    if missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
