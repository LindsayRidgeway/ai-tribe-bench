#!/usr/bin/env python3
"""Write `members.json` — the list a static page needs and a repository cannot serve.

    python3 lab/members.py --write     # rewrite it from wake/members/
    python3 lab/members.py --check     # non-zero if it disagrees with the shelf

A drop list on a phone needs a list, and GitHub Pages serves files, not directories. So the list is a file,
generated from the same shelf the rest of the project reads, and a test fails when the two disagree — the
same rule as the magazine pages: nothing published is typed twice.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMBERS = ROOT / "wake" / "members"
OUT = ROOT / "members.json"
WORKFLOW = ROOT / ".github" / "workflows" / "interactive.yml"


def fixtures() -> set[str]:
    """Names in `lab/fixtures.txt`: test members that must never appear in a published drop list.

    The bench keeps ten of them (a, b, trap, scaffold…) because the suite needs members to break. A colony
    keeps none. Without this list the public page offered a stranger a drop list of fixtures — the same
    defect as a shipped workflow defaulting to member "b"."""
    f = ROOT / "lab" / "fixtures.txt"
    if not f.is_file():
        return set()
    return {line.strip() for line in f.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")}


def collect(root: Path = MEMBERS) -> list[dict]:
    out = []
    if not root.is_dir():
        return out
    skip = fixtures()
    for d in sorted(root.iterdir()):
        if d.name in skip:
            continue
        voice = d / "state" / "voice.md"
        if not voice.is_file():
            continue
        text = voice.read_text(encoding="utf-8")
        api = re.search(r"^api:\s*(\S+)", text, re.M)
        ident = d / "state" / "identity.md"
        out.append({"name": d.name,
                    "engine": api.group(1) if api else "?",
                    "what": first_line(ident)})
    return out


def first_line(path: Path) -> str:
    """A member's own first sentence, trimmed to a phrase for a drop list. Not a description somebody wrote
    about it: what it says about itself."""
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip().lstrip("#").strip()
        if line and not line.lower().startswith(("identity", "i am not", "note")):
            return line[:110]
    return ""


def render(root: Path = MEMBERS) -> str:
    return json.dumps({"written": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "members": collect(root)}, indent=1) + "\n"


def sync_drop_list(names: list[str], wf: Path = WORKFLOW) -> bool:
    """Rewrite the `type: choice` options in interactive.yml so the phone's Run-workflow form offers exactly
    the members published in `members.json`.

    Same rule as everything else here: the list is generated, never typed twice. This is the second place the
    founder's phone found a stale list — a workflow whose drop list was correct when it was written and wrong
    the first time anybody added a member. Returns False when there is no such form to keep in step.
    """
    if not names or not wf.is_file():
        return False
    text = wf.read_text(encoding="utf-8")
    if "type: choice" not in text or "options:" not in text.split("type: choice", 1)[1]:
        return False
    head, rest = text.split("type: choice", 1)
    before, tail = rest.split("options:", 1)
    lines = tail.splitlines(keepends=True)
    lead = 0
    while lead < len(lines) and not lines[lead].strip():      # `options:` is followed by a newline
        lead += 1
    i = lead
    while i < len(lines) and lines[i].strip().startswith("- "):
        i += 1
    if i == lead:
        return False
    # Keep the indentation the block already had, so the file does not churn on every write.
    indent = lines[lead][: len(lines[lead]) - len(lines[lead].lstrip())]
    block = "".join(f"{indent}- {n}\n" for n in names)
    rest_tail = lines[i:]
    # The default has to be one of the options, or GitHub refuses the workflow file.
    for j, line in enumerate(rest_tail):
        s = line.strip()
        if s.startswith("default:"):
            current = s.split(":", 1)[1].strip().strip('"\'')
            if current not in names:
                rest_tail[j] = f'{line[: len(line) - len(line.lstrip())]}default: "{names[0]}"\n'
            break
    wf.write_text(head + "type: choice" + before + "options:" + "".join(lines[:lead]) + block
                  + "".join(rest_tail),
                  encoding="utf-8")
    return True


def drop_list(wf: Path = WORKFLOW) -> list[str]:
    """The names interactive.yml offers, so `--check` can hold the two lists together."""
    if not wf.is_file():
        return []
    text = wf.read_text(encoding="utf-8")
    if "type: choice" not in text:
        return []
    rest = text.split("type: choice", 1)[1]
    if "options:" not in rest:
        return []
    block = rest.split("options:", 1)[1].split("default:", 1)[0]
    return [l.strip().lstrip("- ").strip() for l in block.splitlines() if l.strip().startswith("- ")]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the member list a static page can fetch")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    fresh = json.loads(render())["members"]
    names = [m["name"] for m in fresh]
    if a.check:
        if not OUT.is_file():
            print(f"{OUT.name} is missing: run python3 lab/members.py --write")
            return 1
        on_disk = json.loads(OUT.read_text(encoding="utf-8")).get("members", [])
        if on_disk != fresh:
            print("members.json disagrees with the shelf:")
            print(f"  on disk: {[m['name'] for m in on_disk]}")
            print(f"  shelf:   {[m['name'] for m in fresh]}")
            return 1
        offered = drop_list()
        if offered and sorted(offered) != sorted(names):
            print("interactive.yml offers a drop list that is not the shelf:")
            print(f"  offered: {offered}")
            print(f"  shelf:   {names}")
            return 1
        print(f"members.json matches the shelf ({len(fresh)} member(s))")
        return 0
    OUT.write_text(render(), encoding="utf-8")
    kept = sync_drop_list(names)
    print(f"wrote {OUT.name}: {', '.join(names) or 'no members'}")
    if kept:
        print(f"and the Run-workflow drop list in {WORKFLOW.name}: {', '.join(drop_list())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
