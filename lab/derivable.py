#!/usr/bin/env python3
"""Is everything derived from the shelf alone?

The claim the magazine rests on: *every published file is a function of the record.* If that is true, then
deleting all of them and rebuilding must reproduce them byte for byte, and anybody can check it in one
command. If it is false, somebody edited a published file by hand, or the builder has a hidden input — and
either way the record is not the source of what a reader sees.

    python3 lab/derivable.py            # check, print what differs, exit 1 if anything does

What counts as derived (and is deleted in the copy before rebuilding):

    issues/NN.md, issues/README.md, LEDGER.md, PROJECTS.md, MEMBERS.md

What does not, and must not be touched: works/, soil/, wake/members/*/state/. Those are the record.

Two things had to be fixed for this to be checkable at all. the finished issue carried today's date, so
two rebuilds a minute apart differed; it now carries the date of the newest work in it. And the issue index
did not exist, so `issues/` could gain a file nothing listed.
"""
from __future__ import annotations

import difflib
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DERIVED = ["LEDGER.md", "PROJECTS.md", "MEMBERS.md"]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


magazine = load(HERE / "magazine.py", "magazine_mod")


def derived_files(root: Path) -> list[Path]:
    out = [root / f for f in DERIVED]
    out += sorted(p for p in (root / "issues").glob("*.md"))
    return [p for p in out if p.exists()]


def rebuild(root: Path) -> None:
    issues = {str(w["issue"]) for w in magazine.load_all(root)}
    for issue in sorted(issues):
        text = magazine.build(issue, magazine.load_all(root), root)
        (root / "issues" / f"{int(issue):02d}.md").write_text(text, encoding="utf-8")
    (root / "issues" / "README.md").write_text(magazine.issue_index(), encoding="utf-8") \
        if hasattr(magazine, "issue_index") else None
    (root / "LEDGER.md").write_text(magazine.ledger(root), encoding="utf-8")
    (root / "PROJECTS.md").write_text(magazine.project_index(magazine.load_all(root)), encoding="utf-8")
    members = sorted({w["member"] for w in magazine.load_all(root)})
    (root / "MEMBERS.md").write_text(
        "\n\n".join(magazine.project(m, magazine.load_all(root), root).rstrip() for m in members) + "\n",
        encoding="utf-8")


def check() -> int:
    tmp = Path(tempfile.mkdtemp())
    work = tmp / "repo"
    shutil.copytree(HERE, work, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    before = {p.relative_to(work): p.read_text(encoding="utf-8") for p in derived_files(work)}
    for p in derived_files(work):
        p.unlink()
    rebuild(work)
    after = {p.relative_to(work): p.read_text(encoding="utf-8") for p in derived_files(work)}
    bad = 0
    for rel in sorted(set(before) | set(after)):
        a, b = before.get(rel, ""), after.get(rel, "")
        if a == b:
            print(f"  ok      {rel}")
            continue
        bad += 1
        how = "missing before" if rel not in before else ("not rebuilt" if rel not in after else "differs")
        print(f"  {how:<13} {rel}")
        if rel in before and rel in after:
            diff = list(difflib.unified_diff(a.splitlines(), b.splitlines(), "on disk", "rebuilt", lineterm="", n=1))
            for line in diff[:12]:
                print("    " + line)
    shutil.rmtree(tmp, ignore_errors=True)
    print()
    if bad:
        print(f"{bad} published file(s) are not a function of the record. Either somebody edited one by "
              f"hand, or the builder has an input that is not the shelf.")
        return 1
    print(f"every published file ({len(before)}) rebuilds byte for byte from works/, soil/ and member state.")
    return 0


if __name__ == "__main__":
    sys.exit(check())
