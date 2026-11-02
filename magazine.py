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
            w = read_work(p)
        except OSError:
            continue
        # The file is stored relative to the root it was loaded from, always. An absolute path when the
        # root was a temp directory meant a ref written as "works/a/one.md" never matched the work it
        # pointed at, so a project view showed a piece with no answer and a conversation with nobody in it.
        try:
            w["file"] = str(p.relative_to(root))
        except ValueError:
            w["file"] = str(p)
        out.append(w)
    return out


def drops(root: Path | None = None) -> list[tuple[str, str]]:
    """Every drop in every soil, labelled with the place it fell in. Derived: the file is the drop."""
    root = root or HERE
    out: list[tuple[str, str]] = []
    for f in sorted((root / "soil").glob("*/drops.md")) + sorted((root / "soil").glob("drops.md")):
        place = f.parent.name if f.parent.name != "soil" else "the soil"
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        for ln in text.splitlines():
            if ln.startswith("|") and "---" not in ln and not ln.lower().startswith("| when"):
                out.append((place, ln))
    return out


def places(root: Path | None = None, members: list[str] | None = None) -> dict[str, str]:
    """Which world each member stands in, read from its own files."""
    root = root or HERE
    out = {}
    for m in (members or [p.name for p in (root / "wake" / "members").glob("*") if p.is_dir()]):
        f = root / "wake" / "members" / m / "state" / "place.md"
        try:
            line = f.read_text(encoding="utf-8").strip().splitlines()[0]
            out[m] = line.split(":", 1)[1].strip() if ":" in line else ""
        except (OSError, IndexError):
            out[m] = ""
    return out


CITE_RE = re.compile(r"`?([A-Za-z0-9_.-]+\.md)`?")


def cited(body: str) -> list[str]:
    """Files a piece points at, by name. Cheap and specific: a citation is a claim about the shelf."""
    return sorted({m.group(1) for m in CITE_RE.finditer(body)
                   if not m.group(1).lower().startswith(("readme", "run"))})


def where_cited(name: str, root: Path | None = None) -> str:
    """Where a cited file actually is: "shelf", "a member's own output", or "" for nowhere.

    Three answers, not two. B2 cited harbour-torch-rules.md, which it had written into its own output
    directory but never filed, so "no such file" would have been false and "found" would have hidden the
    seam: the rules exist, the shelf does not have them, and no other member can read them.
    """
    root = root or HERE
    stem = name.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    if list((root / "works").glob(f"*/{stem}.md")):
        return "shelf"
    if any(stem == p.stem for p in root.glob("*.md")):
        return "shelf"
    for pth in (root / "wake" / "members").glob(f"*/output/{stem}.md"):
        return f"{pth.parts[-3]}'s own output (not filed)"
    for pth in (root / "wake" / "members").glob(f"*/state/{stem}.md"):
        return f"{pth.parts[-3]}'s private state (not published)"
    return ""


def build(issue: str, works: list[dict] | None = None, root: Path | None = None) -> str:
    works = works if works is not None else load_all()
    mine = [w for w in works if str(w["issue"]) == str(issue)]
    pieces = [w for w in mine if w["form"] not in ("letter", "note")]
    letters = [w for w in mine if w["form"] in ("letter", "note")]
    now = datetime.now(timezone.utc)
    here = sorted({p for p in places(root, sorted({w["member"] for w in mine})).values() if p})
    where = f" — {', '.join(here)}" if here else ""
    out = [f"# The Workshop — issue {issue}{where}", "",
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
                f"*{w['member'].upper()} — {w['form']}, {w['words']} words*", ""]
        if w.get("revises"):
            # b2 wrote two drafts of one game and the magazine printed them as two unrelated games.
            out += [f"*A revision of `{w['revises']}`.*", ""]
        out += [w["body"], ""]
        replies = [l for l in letters if (l.get("ref") or "").lower() in
                   (w["title"].lower(), Path(w["file"]).stem.lower())]
        for r in replies:
            out += [f"> **{r['member'].upper()} wrote to {w['member'].upper()} about this:** "
                    f"{squash(r['body'])}", ""]

    if letters:
        out += ["---", "", "## Letters", ""]
        by_ref: dict[str, list[dict]] = {}
        for l in letters:
            ref = (l.get("ref") or "").strip()
            by_ref.setdefault("(unaddressed)" if ref in ("", "-", "none") else ref, []).append(l)
        for ref, group in by_ref.items():
            if ref.startswith("member:"):
                who = ref.split(":", 1)[1].upper()
                for l in group:
                    out += [f"### To {who} (no piece named)", "",
                            f"**{l['member'].upper()}** — {l['form']}, {l['words']} words", "", l["body"], ""]
                continue
            if ref == "(unaddressed)":
                # A note that answers nothing is not a letter "On -". Publishing a member's standalone
                # piece under an empty reference was the magazine telling the reader it was a reply.
                for l in group:
                    out += [f"### {l['title']}", "",
                            f"**{l['member'].upper()}** — {l['form']}, {l['words']} words", "", l["body"], ""]
                continue
            out += [f"### On *{ref}*", ""]
            for l in group:
                out += [f"**{l['member'].upper()}** — {l['words']} words", "", l["body"], ""]

    d = drops(root)
    out += ["---", "", "## Colophon", "",
            "This issue was assembled from the files the members wrote; nothing in it was edited. A work "
            "appears if it is on disk and names this issue in its header. If you want a different "
            "magazine, change the soil or change the beats — the workshop does the rest.", ""]
    if d:
        out += [f"**Dropped in by the human ({len(d)}):**", ""]
        for place, row in d[-6:]:
            cells = [c.strip() for c in row.strip("|").split("|")]
            out.append(f"- *{place}* — {cells[-1]} *({cells[0] if cells else ''})*")
        out.append("")
    members = sorted({w["member"] for w in works})
    if members:
        out += [f"**Members with work on file:** {', '.join(m.upper() for m in members)}. "
                f"**Issues with content:** "
                f"{', '.join(sorted({str(w['issue']) for w in works}))}.", ""]
    return "\n".join(out)


def reply_graph(works: list[dict]) -> list[tuple[str, str, str]]:
    """Who answered whom, derived from the `ref` line in each work's header.

    This is the tunnel map. A tribe that only writes is a shelf; a tribe whose works point at each other
    is a workshop. Nothing here is typed: the edge exists if a file names another file (or its title).
    """
    by_file = {w["file"]: w for w in works}
    by_title = {w["title"].lower(): w for w in works}
    edges = []
    for w in works:
        ref = (w.get("ref") or "").strip()
        if not ref or ref == "-":
            continue
        target = by_file.get(ref) or by_title.get(ref.lower())
        if target is None:
            for f, t in by_file.items():
                if ref in f or ref in t["title"].lower():
                    target = t
                    break
        if target is not None and target["file"] != w["file"]:
            edges.append((w["member"], target["member"], w["title"]))
    return edges


def round_robin(works: list[dict], issue: str,
                root: Path | None = None) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]]]:
    """The edges, and the pairs a full round-robin still needs — scoped to each member's own world.

    Two faults were found here on 2026-11-02, both from computing against the wrong set. (1) Edges were
    resolved only among works in the issue, so an answer that crossed issues — A2 answering A's
    issue-one piece from the coach — disappeared; a ref points at a work, not at an issue. (2) The missing
    pairs were computed across every member in the repository, so the report suggested A answer B2, who
    lives in a different world and cannot see A's shelf. A round-robin is per world, because a shelf is.
    """
    mine = [w for w in works if str(w["issue"]) == str(issue)]
    every_file = {w["file"] for w in mine}
    edges = [(a, b, t) for a, b, t in reply_graph(works)
             if any(w["member"] == a and w["title"] == t for w in mine) or a in
             {w["member"] for w in mine}]
    edges = [e for e in edges if e[2] in {w["title"] for w in mine}]
    have = {(a, b) for a, b, _t in edges if a != b}
    answered = {a for a, _b in have}
    where = places(root, sorted({w["member"] for w in works})) if root else {}
    by_place: dict[str, list[str]] = {}
    for m, pl in (where or {w["member"]: "" for w in works}).items():
        by_place.setdefault(pl, []).append(m)
    missing = []
    for pl, group in by_place.items():
        if len(group) < 2:
            continue
        for a in sorted(group):
            if a not in answered:
                missing += [(a, b) for b in sorted(group) if b != a]
    return edges, sorted(set(missing))


def ledger(root: Path | None = None) -> str:
    """One row per member: what it made, whom it answered, who answered it, what it was served, what it owes.

    Everything here is derived from files that already exist — works, journals, state — so the row cannot
    disagree with the record. The point is to make the shape of the society visible at a glance: a member
    with six works and no answers given is a hermit, not a collaborator, and a member with an answer owed to
    it since three wakes ago is a conversation that stopped.
    """
    root = root or HERE
    works = load_all(root)
    where = places(root)
    by_member: dict[str, list[dict]] = {}
    for w in works:
        by_member.setdefault(w["member"], []).append(w)
    members = sorted(by_member)
    rows = []
    for m in members:
        mine = by_member[m]
        files = {str(w["file"]).lower() for w in mine} | {str(w["title"]).lower() for w in mine}
        given = [w for w in mine if (w.get("ref") or "").strip() not in ("", "-", "none")]
        received = [w for w in works if w.get("member") != m and (w.get("ref") or "").lower() in files]
        owed = [w for w in received
                if not any(str(x.get("when", "")) > str(w.get("when", ""))
                           and (x.get("ref") or "").lower() in {str(w["file"]).lower(), str(w["title"]).lower()}
                           for x in mine)]
        journal = ""
        try:
            journal = (root / "wake" / "members" / m / "state" / "journal.md").read_text(encoding="utf-8")
        except OSError:
            pass
        reads = journal.count("- Read in full this wake:")
        pending = ""
        try:
            pending = (root / "wake" / "members" / m / "state" / "reading.md").read_text(encoding="utf-8").strip()
        except OSError:
            pass
        rows.append((where.get(m, ""), m, len(mine), len(given), len(received), len(owed), reads,
                     "queued" if pending and not pending.startswith("(nothing") else ""))
    out = ["# Who is talking to whom", "",
           "| world | member | works | answers given | answers received | owed | reads served | reading |",
           "|---|---|---|---|---|---|---|---|"]
    for place, m, nw, g, r, o, rd, q in sorted(rows):
        out.append(f"| {place} | {m.upper()} | {nw} | {g} | {r} | {o} | {rd} | {q} |")
    silent = [m.upper() for place, m, nw, g, r, o, rd, q in sorted(rows) if g == 0 and nw > 1]
    if silent:
        out += ["", f"**Never answered anybody:** {', '.join(silent)}"]
    owed_total = sum(o for *_x, o, _r, _q in rows)
    out += ["", f"**Answers owed across the colony:** {owed_total}"]
    return "\n".join(out) + "\n"


def project(member: str, works: list[dict], root: Path | None = None) -> str:
    """One member's work in the order it was made — the longitudinal view the issue cannot give.

    An issue is a night; a project is a tunnel. The magazine has been chronological across everybody, so a
    member building one thing over five wakes appeared five times as five unrelated pieces, and B2's two
    drafts of one game sat side by side with no line between them. A reader who wants to watch a member get
    better at something needs the member's own timeline: what it made, in what order, what it answered, what
    it revised, and what is still owed to it.
    """
    mine = sorted([w for w in works if w.get("member") == member], key=lambda w: str(w.get("when", "")))
    if not mine:
        return f"# {member.upper()} — nothing on the shelf\n"
    asked_by_others = []
    for w in works:
        if w.get("member") != member and (w.get("ref") or "").lower() in {
                str(x["file"]).lower() for x in mine} | {str(x["title"]).lower() for x in mine}:
            asked_by_others.append(w)
    out = [f"# {member.upper()} — {len(mine)} work(s), {mine[0].get('when', '')[:8]} to "
           f"{mine[-1].get('when', '')[:8]}", ""]
    forms: dict[str, int] = {}
    for w in mine:
        forms[w["form"]] = forms.get(w["form"], 0) + 1
    out += ["*" + ", ".join(f"{n} {f}" for f, n in sorted(forms.items(), key=lambda kv: -kv[1])) + "*", ""]
    prev = ""
    for w in mine:
        when = str(w.get("when", ""))
        stamp = f"{when[6:8]}/{when[4:6]} {when[9:11]}:{when[11:13]}" if len(when) >= 13 else when
        line = f"- **{stamp}** — {w['title']} *({w['form']}, {w['words']} w)*"
        out.append(line)
        if w.get("ref") and w["ref"].strip() not in ("-", ""):
            out.append(f"  - answers `{w['ref']}`")
        if w.get("revises"):
            out.append(f"  - revises `{w['revises']}`")
        answered_by = [x for x in works if x.get("member") != member
                       and (x.get("ref") or "").lower() in {str(w["file"]).lower(), str(w["title"]).lower()}]
        for x in answered_by:
            out.append(f"  - answered by {x['member'].upper()} — {x['title']}")
        prev = w["title"]
    out += ["", "## Written back to " + member.upper(), ""]
    if not asked_by_others:
        out.append("*(nobody has written back to this member yet)*")
    places_map = places(root) if root else {}
    for w in sorted(asked_by_others, key=lambda w: str(w.get("when", ""))):
        other = places_map.get(w["member"], "")
        here = places_map.get(member, "")
        where = "" if (not places_map or other == here) else f" — in {other}, a world {member.upper()} cannot see"
        out.append(f"- {w['member'].upper()} — {w['title']} *({w.get('when', '')[:8]})*{where}")
    return "\n".join(out) + "\n"


def squash(text: str, limit: int = 320) -> str:
    flat = re.sub(r"\s+", " ", re.sub(r"^#+.*$", "", text, flags=re.M)).strip()
    return flat[:limit] + ("…" if len(flat) > limit else "")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", default="1")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--current", action="store_true",
                    help="the issue currently open: the highest issue on disk, or 1")
    ap.add_argument("--citations", action="store_true",
                    help="files a work cites that are not on the shelf — invented provenance, caught cheaply")
    ap.add_argument("--project", default="", help="one member's works in order — the long view")
    ap.add_argument("--ledger", action="store_true", help="one row per member: works, answers, debts, reads")
    ap.add_argument("--projects", action="store_true", help="every member's timeline; with --write, PROJECTS.md")
    ap.add_argument("--links", action="store_true",
                    help="who answered whom this issue, and which members have not answered anyone")
    args = ap.parse_args(argv if argv is not None else sys.argv[1:])

    works = load_all()
    if args.list:
        if not works:
            print("no works on file")
        for w in works:
            print(f"  issue {w['issue']:>3}  {w['member']:<4} {w['form']:<10} {w['words']:>5} words  "
                  f"{w['title']}")
        return 0

    if args.current:
        nums = []
        for pth in (HERE / "issues").glob("*.md"):
            stem = pth.stem.split("-")[0]
            if stem.isdigit():
                nums.append(int(stem))
        for w in works:
            if str(w["issue"]).isdigit():
                nums.append(int(w["issue"]))
        print(max(nums) if nums else 1)
        return 0

    if args.ledger:
        text = ledger(HERE)
        if args.write:
            (HERE / "LEDGER.md").write_text(text, encoding="utf-8")
            print("wrote LEDGER.md")
        else:
            print(text, end="")
        return 0

    if args.project:
        print(project(args.project.lower(), works, HERE), end="")
        return 0

    if args.projects:
        members = sorted({w["member"] for w in works})
        text = "\n\n".join(project(m, works, HERE).rstrip() for m in members) + "\n"
        if args.write:
            (HERE / "PROJECTS.md").write_text(text, encoding="utf-8")
            print(f"wrote PROJECTS.md — {len(members)} member(s)")
        else:
            print(text, end="")
        return 0

    if args.citations:
        bad = 0
        for w in works:
            for name in cited(w["body"]):
                found = where_cited(name, HERE)
                if found != "shelf":
                    bad += 1
                    print(f"{w['member']:<4} {w['title']!r} cites {name!r} — "
                          + (f"in {found}, which no other member can read" if found else "no such file anywhere"))
        print(f"{bad} citation(s) not on the shelf" if bad else "every cited file is on the shelf")
        return 0

    if args.links:
        edges, missing = round_robin(works, args.issue, HERE)
        print(f"issue {args.issue}: {len(edges)} reply edge(s)")
        for a, b, title in edges:
            print(f"  {a.upper()} -> {b.upper()}  ({title})")
        answered = sorted({a for a, _b, _t in edges})
        silent = sorted({w["member"] for w in works} - set(answered))
        if silent:
            print(f"  not answered anyone: {', '.join(m.upper() for m in silent)}")
            for a, b in missing[:6]:
                print(f"    could: {a.upper()} -> {b.upper()}")
        else:
            print("  every member with work has answered someone")
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
