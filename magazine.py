#!/usr/bin/env python3
"""Assemble an issue of the workshop magazine from the files the members wrote.

This is the piece that makes the bench a cohort rather than a game. A member's life is not a round: it is
a beat (what it is interested in), a soil (the world it is standing in), and a pile of works — pieces,
catalogues, a game, letters to each other about those works. The magazine is the thing that makes the
pile a *publication*: it takes what exists on disk, gives it an order, and shows the peer responses next
to the thing responded to.

Everything here is derived from files. There is no editorial judgement in this program and no stored copy
of a work: if a member wants its piece in the issue, the piece is in `works/`, and the assembler reads it
out of there. Hand-editing an issue is pointless — it is regenerated.

    python3 magazine.py --issue 1            print the issue
    python3 magazine.py --issue 1 --write    write issues/01.md
    python3 magazine.py --list               what works exist, and which issue each is in
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKS = HERE / "works"
ISSUES = HERE / "issues"
SOIL = HERE / "soil"


def read_work(path: Path) -> dict:
    """A work is a markdown file with a small header block. Everything else is the work."""
    text = path.read_text(encoding="utf-8")
    try:
        where = str(path.relative_to(HERE))
    except ValueError:
        where = str(path)   # a works directory outside the repository is legitimate; only the label differs
    meta: dict[str, str] = {"member": path.parent.name, "file": where}
    body = text
    lines = text.splitlines()
    if lines and (lines[0].strip() == "---" or re.match(r"^[a-z_]+:", lines[0])):
        if lines[0].strip() == "---":
            lines = lines[1:]
        head = []
        for i, ln in enumerate(lines):
            if not ln.strip():
                body = "\n".join(lines[i + 1:]).strip()
                break
            head.append(ln)
        for ln in head:
            if ":" in ln:
                k, _, v = ln.partition(":")
                meta[k.strip().lower()] = v.strip()
    else:
        body = text.strip()
    meta["body"] = body
    meta["title"] = meta.get("title") or first_heading(body) or path.stem.replace("-", " ")
    meta["form"] = (meta.get("form") or "piece").lower()
    meta["issue"] = meta.get("issue") or "1"
    meta["words"] = len(re.findall(r"\b[\w'-]+\b", body))
    return meta


def first_heading(body: str) -> str:
    for ln in body.splitlines():
        if ln.startswith("#"):
            return ln.lstrip("# ").strip()
    return ""


def load_all(root: Path | None = None) -> list[dict]:
    root = root or HERE
    out = []
    for p in sorted((root / "works").glob("*/*.md")):
        try:
            out.append(read_work(p))
        except OSError:
            continue
    return out


def drops(root: Path | None = None) -> list[str]:
    root = root or HERE
    try:
        text = (root / "soil" / "drops.md").read_text(encoding="utf-8")
    except OSError:
        return []
    return [ln for ln in text.splitlines() if ln.startswith("|") and "---" not in ln
            and not ln.lower().startswith("| when")]


def build(issue: str, works: list[dict] | None = None, root: Path | None = None) -> str:
    works = works if works is not None else load_all()
    mine = [w for w in works if str(w["issue"]) == str(issue)]
    pieces = [w for w in mine if w["form"] not in ("letter", "note")]
    letters = [w for w in mine if w["form"] in ("letter", "note")]
    now = datetime.now(timezone.utc)
    out = [f"# The Workshop — issue {issue}", "",
           f"*{len(pieces)} pieces and {len(letters)} letters, assembled from `works/` on "
           f"{now:%Y-%m-%d} by `magazine.py`. The pieces are the members'; the order is not.*", ""]
    if not mine:
        out += ["No works have been filed under this issue yet. A member files one by writing a file "
                "into `works/<member>/` with a header block: `title:`, `form:`, `issue:`.", ""]
        return "\n".join(out)

    out += ["## Contents", ""]
    for w in pieces:
        out.append(f"- **{w['title']}** — {w['member'].upper()}, {w['form']}, {w['words']} words")
    if letters:
        out.append(f"- *Letters*, {len(letters)} of them")
    out += [""]

    for w in pieces:
        out += ["---", "", f"## {w['title']}", "",
                f"*{w['member'].upper()} — {w['form']}, {w['words']} words*", "", w["body"], ""]
        replies = [l for l in letters if (l.get("ref") or "").lower() in
                   (w["title"].lower(), Path(w["file"]).stem.lower())]
        for r in replies:
            out += [f"> **{r['member'].upper()} wrote to {w['member'].upper()} about this:** "
                    f"{squash(r['body'])}", ""]

    if letters:
        out += ["---", "", "## Letters", ""]
        by_ref: dict[str, list[dict]] = {}
        for l in letters:
            by_ref.setdefault(l.get("ref") or "(unaddressed)", []).append(l)
        for ref, group in by_ref.items():
            out += [f"### On *{ref}*", ""]
            for l in group:
                out += [f"**{l['member'].upper()}** — {l['words']} words", "", l["body"], ""]

    d = drops(root)
    out += ["---", "", "## Colophon", "",
            "This issue was assembled from the files the members wrote; nothing in it was edited. A work "
            "appears if it is on disk and names this issue in its header. If you want a different "
            "magazine, change the soil or change the beats — the workshop does the rest.", ""]
    if d:
        out += [f"**In the workshop this month ({len(d)} drop(s) from the human):**", ""]
        for row in d[-5:]:
            cells = [c.strip() for c in row.strip("|").split("|")]
            out.append(f"- {cells[-1]} *({cells[0] if cells else ''})*")
        out.append("")
    members = sorted({w["member"] for w in works})
    if members:
        out += [f"**Members with work on file:** {', '.join(m.upper() for m in members)}. "
                f"**Issues with content:** "
                f"{', '.join(sorted({str(w['issue']) for w in works}))}.", ""]
    return "\n".join(out)


def squash(text: str, limit: int = 320) -> str:
    flat = re.sub(r"\s+", " ", re.sub(r"^#+.*$", "", text, flags=re.M)).strip()
    return flat[:limit] + ("…" if len(flat) > limit else "")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", default="1")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])

    works = load_all()
    if args.list:
        if not works:
            print("no works on file")
        for w in works:
            print(f"  issue {w['issue']:>3}  {w['member']:<4} {w['form']:<10} {w['words']:>5} words  "
                  f"{w['title']}")
        return 0

    text = build(args.issue, works)
    if args.write:
        ISSUES.mkdir(parents=True, exist_ok=True)
        path = ISSUES / f"{int(args.issue):02d}.md" if str(args.issue).isdigit() else ISSUES / f"{args.issue}.md"
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(HERE)}")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
