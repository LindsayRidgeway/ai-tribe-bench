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
import json
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
.github/workflows/paint.yml
.github/workflows/magazine.yml
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
lab/tennis_script.py
lab/rps.py
lab/paint.py
lab/update_tribe.py
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
# One room, not two. Until 2026-11-20 this shipped the whole `soil/` tree, which meant every new circle arrived with a
# choice it had not asked for: the workshop and the night bus, both written by me. `Worlds` is gone from the product
# (RELEASE.md, "Deleting worlds"), so a new circle gets one example room to rewrite or delete.
DIRS = ["soil/workshop"]

# What an *update* may replace, as opposed to what a new tribe starts with. Almost the same set, and the
# difference is the whole of the risk: `members.json` is a list derived from the shelf and a template copy of it is
# empty, so writing it would delete an owner's members; `.gitignore` is a file owners add to; the READMEs under
# issues/ and the .gitkeep that holds `wake/members/` open are the owner's, not the code's. `update_tribe.py`
# reaches the same answer from the other direction (is_machinery), and this file is where the list is published so
# that the page does not have to hold a third copy of it — three lists with the same names in two languages is how
# a whitelist starts lying.
MANIFEST_NOT_MACHINERY = (".gitignore", "members.json", "README.md",
                          "issues/README.md", "letters/README.md", "plates/README.md",
                          "wake/members/.gitkeep")


def manifest() -> list[str]:
    """The paths an update is allowed to write. Published in the template as .tribe-manifest.json."""
    return sorted(p for p in FILES if p not in MANIFEST_NOT_MACHINERY)

TEMPLATE_README = """# Your circle

This is your circle's repository. Kythe is the page you read it with; this is the record.

- `wake/members/` — your members. One folder each. Empty until you make one.
- `soil/` — the rooms a member can live in. Two are here as examples.
- `.github/workflows/` — the clock that wakes a member, and the jobs Kythe starts for you.
- `USER-MANUAL.md` — the manual. It is the longest file here and the only one you may want to read.
- `REFERENCE.md` — every file, what writes it, what breaks without it.

You do not need to edit anything. If you do, keep it text: the circle is plain Markdown and Python
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


CODE_SUFFIXES = (".py", ".html", ".mjs", ".sh")


def dispatched() -> dict[str, list[str]]:
    """Workflow names the shipped code starts, mapped to the shipped files that start them.

    `unshipped()` above watches the direction *inside* a workflow: a shipped workflow that runs a script
    nobody added. This watches the direction the owner actually presses: a file we ship offers a button and
    names the workflow behind it. If that workflow is not on the list, the press is a promise with no
    machinery behind it — `paint.yml` and `magazine.yml` were both missing until 2026-11-14 while
    `USER-MANUAL.md` §8 and §9 shipped in full and described both cards, and `--check` passed, because it
    only ever asked whether the files already on the list existed.

    Only code is scanned, never the manual: prose names instruments like `lab/chat.py` that a tribe is
    deliberately not given, and a check that fires on a correct sentence is a check somebody switches off.

    `ait.html` is scanned by name rather than through the list, because it is *not* in a tribe's
    repository: the page is served once, from the project's own site, and it is the one file every
    owner of every tribe uses. A workflow it names must exist in the repository the button will reach.
    """
    out: dict[str, list[str]] = {}
    page = ROOT / "ait.html"
    candidates = list(FILES) + (["ait.html"] if page.is_file() else [])
    for p in candidates:
        path = ROOT / p
        if not p.endswith(CODE_SUFFIXES) or not path.is_file():
            continue
        text = path.read_text(errors="replace")
        for m in re.finditer(r"""['"]([a-z0-9_-]+\.yml)['"]""", text):
            owners = out.setdefault(m.group(1), [])
            if p not in owners:
                owners.append(p)
    return out


def unshipped_dispatches() -> dict[str, list[str]]:
    """Workflows the shipped code starts that the template would not contain."""
    return {k: v for k, v in dispatched().items() if f".github/workflows/{k}" not in FILES}


def unshipped_imports() -> dict[str, list[str]]:
    """Local modules a shipped script imports and the template would not contain.

    The same silent failure as `unshipped()`, one step earlier: not a workflow calling a missing script,
    but a script calling a missing module. Nothing in this repository notices, because here it imports.

    Both shapes are caught, because both are in use: `from lab.x import …`, and `sys.path.insert(...)` then
    `from x import …` — which is how `tribe.py` reads the model table out of `lab/rps.py` to decide whether
    a new member can ever answer. That one is wrapped in `except Exception: return ""`, so a missing module
    is not an error there, it is a member created and unable to speak, which is the defect its own comment
    describes. A name only counts as local when `lab/<name>.py` exists on this bench, so no stdlib import
    can ever trip this.
    """
    local = {p.stem for p in (ROOT / "lab").glob("*.py")}
    out: dict[str, list[str]] = {}
    for p in FILES:
        path = ROOT / p
        if not p.endswith(".py") or not path.is_file():
            continue
        text = path.read_text(errors="replace")
        for m in re.finditer(r"^\s*(?:from|import)\s+(?:lab\.)?([A-Za-z0-9_]+)", text, re.M):
            if m.group(1) not in local:
                continue
            want = f"lab/{m.group(1)}.py"
            if want not in FILES:
                owners = out.setdefault(want, [])
                if p not in owners:
                    owners.append(p)
    return out


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
    if not (ROOT / ".tribe-retired.json").is_file():
        missing.append(".tribe-retired.json")
    if a.check:
        for p in missing:
            print(f"missing: {p}")
        print(f"{len(want) - len(missing)}/{len(want)} present")
        bad = unshipped()
        for script, wfs in bad.items():
            print(f"a workflow runs {script}, which the template does not ship ({', '.join(wfs)})")
        no_wf = unshipped_dispatches()
        for wf, where in no_wf.items():
            print(f"{', '.join(where)} starts {wf}, which the template does not ship")
        no_mod = unshipped_imports()
        for mod, where in no_mod.items():
            print(f"{', '.join(where)} imports {mod}, which the template does not ship")
        return 1 if (missing or bad or no_wf or no_mod) else 0

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
    # The retired list is the updater's only authority for deleting anything, so it must travel with the
    # template and must be reproducible from this bench like every other file. It is not in FILES because a
    # tribe never receives it: `update_tribe.py` reads it out of the tarball and keeps it out of the copy.
    retired = ROOT / ".tribe-retired.json"
    if retired.is_file():
        shutil.copy2(retired, out / ".tribe-retired.json")
    # The update's manifest travels with the template and is generated here, so it cannot disagree with what a new
    # tribe is made of. A page or a script that writes files into someone's repository asks this list first.
    (out / ".tribe-manifest.json").write_text(json.dumps(
        {"schema": "ait-manifest/1",
         "about": "Paths an update may write. Generated by lab/make_template.py from the same whitelist that builds "
                  "a new tribe; never edited by hand. The page reads the template's current copy — a copy inside a "
                  "tribe's repository is the receipt from the commit that tribe was generated from.",
         "files": manifest()}, indent=1) + "\n")
    print(f"built {out}: {len(want) - len(missing)} files")
    if missing:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
