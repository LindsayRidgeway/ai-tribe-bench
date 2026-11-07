#!/usr/bin/env python3
"""Check ENGINES.md against the promises the rest of the project makes about it.

Written 2026-11-06 because the founder asked how to edit that page without breaking it, and the honest
answer was "you cannot, by hand, without a checker". The page is not prose that happens to mention
engines: `tests.py` slices it on its headings, and a table cell is the only place a price is allowed to
appear. Every rule below is one that a careless edit would violate silently — a footnote reference with
no note reads fine and renders as literal text; a footnote whose number skips one breaks the numbering
for every note after it; a table row with four cells still renders and quietly loses its last column.

Two ways to use it:

    python3 lab/check_engines.py              # human sentences, exit 1 if anything is wrong
    python3 lab/check_engines.py --quiet      # nothing but the count; exit code carries the answer

`tests.py` runs the same checks as one test, so a green suite and a green checker cannot disagree.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PAGE = REPO / "ENGINES.md"

# The headings `tests.py` slices on. Renaming one of these does not fail a rendering anywhere; it
# fails a test that is looking for a section and finds the whole rest of the file instead.
ANCHORS = [
    "### The three engines this page recommends",
    "### Other possibilities",
    "### On your own machine",
    "### What Goose calls them",
    "### Notes",
]
# "### What Goose calls them, if you are using a computer" is the heading as written; the tests slice on
# the shorter prefix, so the checker matches prefixes too and both stay true if the tail of a heading moves.

# Sentences this page has been corrected for saying. They would come back by accident, in a rewrite,
# because they were true once.
FORBIDDEN = [
    ("The rest, which the harness also speaks",
     "every engine in the harness has now been woken; a section for the uncalled is a place for guesses to hide"),
    ("does not work here at all",
     "Claude works here as of 2026-11-06; the page must not keep claiming otherwise"),
]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod



NUM_WORDS = {19: "nineteen", 20: "twenty", 21: "twenty-one", 22: "twenty-two", 23: "twenty-three"}


def renumber(text: str) -> tuple[str, dict[int, int]]:
    """Renumber the notes into first-reference order, and say what moved.

    Written because I did it by hand three times and got it wrong once each time. Nothing about the numbers
    means anything except reading order, so the only correct numbering is the one a script computes.
    """
    defs = list(re.finditer(r"^\[\^(\d+)\]:", text, re.M))
    if not defs:
        return text, {}
    body = text[:defs[0].start()]
    blocks: list[tuple[int, str]] = []
    for a, b in zip(defs, defs[1:] + [None]):
        end = b.start() if b else len(text)
        blocks.append((int(a.group(1)), text[a.start():end].rstrip() + "\n"))
    firsts: list[int] = []
    for m in re.finditer(r"\[\^(\d+)\](?!:)", body):
        n = int(m.group(1))
        if n not in firsts:
            firsts.append(n)
    known = [n for n, _ in blocks]
    order = [n for n in firsts if n in known] + [n for n in known if n not in firsts]
    mapping = {old: new for new, old in enumerate(order, 1)}

    def swap(t: str) -> str:
        # The reference first, then the prose number that points at it: "note 17.[^17]" is two statements of the
        # same fact, and renumbering only the bracket leaves the sentence telling the reader the wrong note —
        # which happened on 2026-11-07 and was caught by reading, not by this program.
        def one(m):
            old_n = int(m.group(1))
            new_n = mapping.get(old_n, old_n)
            return f"[^{new_n}]"
        t = re.sub(r"\[\^(\d+)\]", one, t)
        return re.sub(r"(note )(\d+)(\.\[\^)", lambda m: f"{m.group(1)}{mapping.get(int(m.group(2)), int(m.group(2)))}{m.group(3)}", t)

    by_old = dict(blocks)
    out = swap(body) + "\n".join(swap(by_old[old]) for old in order)
    word = NUM_WORDS.get(len(order), str(len(order)))
    out = re.sub(r"(\w+) notes at the end", f"{word} notes at the end", out, count=1)
    return out, mapping


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def problems(text: str | None = None) -> list[str]:
    """Every way the page currently breaks a promise, as a sentence a person can act on."""
    text = PAGE.read_text(encoding="utf-8") if text is None else text
    out: list[str] = []
    lines = text.splitlines()

    # 1. the anchors, once each, in reading order
    positions = []
    idx = {}
    for heading in ANCHORS:
        hits = [n for n, line in enumerate(lines) if line.startswith(heading)]
        if len(hits) != 1:
            out.append(f"the heading {heading!r} appears {len(hits)} times; exactly once, or a test that slices the "
                       f"page on it reads the wrong half")
        else:
            positions.append(hits[0])
            idx[heading] = hits[0]
    if positions != sorted(positions):
        out.append("the sections are out of order: recommended, other possibilities, own machine, Goose names, notes")
    for a, b in zip(ANCHORS, ANCHORS[1:]):
        if a in idx and b in idx and idx[a] > idx[b]:
            out.append(f"{b!r} must come after {a!r}")

    # 2. tables: same number of cells as their header, and no cell left empty
    i = 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
            width = len(_cells(lines[i]))
            j = i + 2
            while j < len(lines) and lines[j].startswith("|"):
                cells = _cells(lines[j])
                if len(cells) != width:
                    out.append(f"line {j + 1}: {len(cells)} cells in a {width}-column table — {lines[j][:70]}")
                for k, cell in enumerate(cells):
                    if not cell:
                        out.append(f"line {j + 1}, column {k + 1}: blank cell. A blank price reads as free")
                j += 1
            i = j
        else:
            i += 1

    # 3. the price rule, in the one table that has prices next to claims
    if "### Other possibilities" in text:
        block = text[text.index("### Other possibilities"):text.index("### On your own machine")]
        for line in block.splitlines():
            if line.startswith("| `"):
                cells = _cells(line)
                price = cells[3] if len(cells) > 3 else ""
                if price and "$" not in price and not price.startswith("not printed here"):
                    out.append(f"{cells[0]}: price cell is neither a figure nor the phrase 'not printed here' — "
                               f"{price[:60]}")

    # 4. footnotes: every reference has a note, every note is referenced, numbers are 1..N by first ref
    refs = [(m.start(), int(m.group(1))) for m in re.finditer(r"\[\^(\d+)\](?!:)", text)]
    defs = [(m.start(), int(m.group(1))) for m in re.finditer(r"^\[\^(\d+)\]:", text, re.M)]
    ref_nums, def_nums = [n for _, n in refs], [n for _, n in defs]
    for n in sorted(set(ref_nums) - set(def_nums)):
        out.append(f"Footnote [^{n}] is referenced but never defined; it renders as literal text")
    for n in sorted(set(def_nums) - set(ref_nums)):
        out.append(f"Footnote [^{n}] is defined but never referenced; nothing points at it")
    if def_nums and sorted(def_nums) != list(range(1, len(def_nums) + 1)):
        out.append(f"The notes are numbered {sorted(def_nums)[:3]}…{sorted(def_nums)[-1:]} — they must be 1..N with "
                   f"no gaps, or every number after the gap is off by one")
    first_refs = []
    for _, n in refs:
        if n not in first_refs:
            first_refs.append(n)
    if def_nums and first_refs != [n for n in first_refs if n in def_nums] and False:  # pragma: no cover
        pass
    if def_nums and [n for n in first_refs if n in def_nums] != sorted(def_nums):
        out.append("The notes are not in first-reference order; renumbering by reading order is how this page says "
                   "things in the order a reader meets them")
    m = re.search(r"(\w+) notes at the end", text)
    words = {19: "nineteen", 20: "twenty", 21: "twenty-one", 22: "twenty-two"}
    if m and def_nums:
        said = m.group(1).lower()
        actual = words.get(len(def_nums), str(len(def_nums)))
        if said != actual:
            out.append(f"The prose says {said!r} notes and there are {len(def_nums)} — say {actual!r}")

    # 4b. a prose number and its reference are the same fact; they must agree
    for m in re.finditer(r"note (\d+)\.\[\^(\d+)\]", text):
        if m.group(1) != m.group(2):
            out.append(f"the prose says 'note {m.group(1)}' and the reference beside it is [^{m.group(2)}] — "
                       f"renumber by running --renumber rather than by editing the number")

    # 5. the forbidden sentences
    for phrase, why in FORBIDDEN:
        if phrase in text:
            out.append(f"The page still says {phrase!r}: {why}")

    # 6. every engine the harness speaks is on the page, and every row names the right secret
    rps = load(REPO / "lab" / "rps.py", "rps_for_engine_page")
    for engine in sorted(rps.BASES):
        if f"`{engine}`" not in text:
            out.append(f"`{engine}` is an engine the harness speaks and the page never names it")
        elif engine != "local" and f"TRIBE_API_KEY_{engine.upper()}" not in text:
            out.append(f"`{engine}` is listed without its secret name TRIBE_API_KEY_{engine.upper()}")
    for engine, model in sorted(rps.DEFAULT_MODEL.items()):
        if model not in text:
            out.append(f"{engine}'s default model {model!r} is not printed on the page — a default a reader cannot "
                       f"find is a default only the code knows")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="check ENGINES.md against the promises made about it")
    ap.add_argument("--quiet", action="store_true", help="print nothing but the verdict")
    ap.add_argument("--renumber", action="store_true",
                    help="renumber the notes into first-reference order, in place, and print what moved")
    a = ap.parse_args()
    if a.renumber:
        body = PAGE.read_text(encoding="utf-8")
        new, mapping = renumber(body)
        if new != body:
            PAGE.write_text(new, encoding="utf-8")
            moved = {o: n for o, n in mapping.items() if o != n}
            print("renumbered " + (", ".join(f"{o}->{n}" for o, n in sorted(moved.items())) or "nothing"))
        else:
            print("already in first-reference order")
        return 0
    found = problems()
    if a.quiet:
        print("ok" if not found else f"{len(found)} problem(s)")
        return 1 if found else 0
    if not found:
        body = PAGE.read_text(encoding="utf-8")
        notes = len(re.findall(r"^\[\^", body, re.M))
        print(f"ENGINES.md: {len(body.splitlines())} lines, {notes} notes, nothing broken.")
        return 0
    print(f"ENGINES.md: {len(found)} problem(s), worst first:\n")
    for n, p in enumerate(found, 1):
        print(f"{n}. {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
