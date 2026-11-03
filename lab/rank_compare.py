#!/usr/bin/env python3
"""Compare three beings' full rankings of a hidden season: where they agree, where they part, who was right.

The founder's design, 2026-11-03: rank all thirty-two clubs rather than pick a top three, because *"the
disagreements that make this worth doing live in the middle of the table."* A top-three answers all agree at
the top and tell you nothing; a full ordering can be compared as a shape.

What this reports:
  - the divergence between each pair, as a rank correlation and as the median number of places one being
    moves a club against another. This is the exhibit: same facts, three minds, a measurable distance.
  - the club they disagree about most, which is usually the interesting one.
  - the champion's rank in each ordering, and how far each put the eventual winner from where it finished.
  - optionally, the field: how many of the clubs that actually reached the postseason each being put in its
    own top twelve. A method can get the field right and the champion wrong, or neither, and those are
    different failures.

What it refuses: a verdict. A higher correlation with the outcome is not a better method, and one season is
one sample. The tool says so in its own output, the same rule `lab/compare.py` and `lab/mlb_score.py` follow.

Nothing here is ever shown to the beings. The key stays outside the repository and the champion is passed on
the command line, so a member cannot read the answer out of the tool that scores it.

Usage:
    python3 lab/rank_compare.py --key /tmp/nfl-2011-key.json --champion NYG \\
        --field NYG,NE,GB,NO,SF,BAL,PIT,HOU,DEN,ATL,DET,CIN
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RANKING = re.compile(r"^\s*(?:\*\*)?RANKING(?:\*\*)?\s*[:.\-–—]\s*(.+)$", re.M | re.I)
SEP = re.compile(r"[,\s]+")


def parse_ranking(text: str) -> list[str]:
    m = RANKING.search(text)
    if not m:
        return []
    raw = SEP.split(m.group(1).strip())
    out = []
    for token in raw:
        token = re.sub(r"[^A-Za-z]", "", token).upper()
        if token and token not in out:
            out.append(token)
    return out


def rankings(root: Path, also: list[str] | None = None) -> list[dict]:
    files = sorted((root / "experiment" / "rank").glob("*-rank.md"))
    for extra in (also or []):
        files += sorted((root / extra).glob("*-rank.md"))
    out, seen = [], set()
    for f in files:
        order = parse_ranking(f.read_text(encoding="utf-8", errors="replace"))
        if not order:
            continue
        who = f.stem.replace("-rank", "")
        if who.casefold() in seen:
            continue
        seen.add(who.casefold())
        out.append({"member": who, "order": order, "file": f})
    return out


def incomplete(rows: list[dict], expected: int) -> list[str]:
    """Who filed a ranking that is not a ranking of everything.

    The first real run of this experiment filed thirty-one letters out of thirty-two and dropped a club
    without noticing. Comparing it would have measured 31 clubs and called the result a divergence, so the
    check is a function with a name rather than a print statement inside main.
    """
    return [r["member"] for r in rows if len(r["order"]) != expected]


def spearman(a: list[str], b: list[str]) -> float:
    """Rank correlation over the clubs both beings ranked. +1 identical, 0 unrelated, -1 reversed."""
    common = [c for c in a if c in b]
    n = len(common)
    if n < 3:
        return float("nan")
    d2 = sum((a.index(c) - b.index(c)) ** 2 for c in common)
    return 1 - (6 * d2) / (n * (n * n - 1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="compare full rankings of a hidden season")
    ap.add_argument("--key", required=True, help="letter->club mapping written by lab/sport_facts.py")
    ap.add_argument("--champion", required=True,
                    help="the club that actually won it all: a letter from the key, or a club name")
    ap.add_argument("--field", default=None,
                    help="comma-separated letters or names of the clubs that actually reached the postseason")
    ap.add_argument("--also", action="append", default=[], help="extra directory of *-rank.md files")
    ap.add_argument("--write", action="store_true", help="also write facts/rank-comparison.md")
    args = ap.parse_args(argv)

    key = json.loads(Path(args.key).read_text(encoding="utf-8"))
    letters = key["letters"]
    inv = {v.casefold(): k for k, v in letters.items()}

    def resolve(token: str) -> str | None:
        t = token.strip().upper()
        if t in letters:
            return t
        return inv.get(token.strip().casefold())

    champion = resolve(args.champion)
    if not champion:
        print(f"   {args.champion!r} is neither a letter in the key nor a club in it. Nothing was compared: "
              f"guessing which club won would put a fabricated result on disk.", file=sys.stderr)
        return 2
    field = None
    if args.field:
        field = [resolve(x) for x in args.field.split(",") if x.strip()]
        if any(f is None for f in field):
            print("   the field list has a token I cannot resolve. Nothing was compared.", file=sys.stderr)
            return 2

    rows = rankings(ROOT, args.also)
    if not rows:
        print("No *-rank.md files found under experiment/rank/. A comparison needs at least one ranking.")
        return 1

    for who in incomplete(rows, len(letters)):
        r = next(x for x in rows if x["member"] == who)
        print(f"   {who}: ranked {len(r['order'])} clubs, not {len(letters)}. This row is not comparable and is "
              f"shown but not scored.", file=sys.stderr)

    print(f"Season {key['season']}, {len(letters)} clubs, seed {key['seed']}. Champion: "
          f"{champion} = {letters[champion]}.\n")
    print(f"{'being':10s} top five (as they ranked it)                                 "
          f"{'champion':9s} {'field/12':8s}")
    print("-" * 92)
    for r in rows:
        order = r["order"]
        top = ", ".join(f"{letters.get(c, c)}" for c in order[:5])
        cr = order.index(champion) + 1 if champion in order else None
        field_hit = ""
        if field:
            field_hit = f"{sum(1 for c in order[:len(field)] if c in field)}/{len(field)}"
        print(f"{r['member'][:10]:10s} {top[:58]:58s} "
              f"{(('#' + str(cr)) if cr else '—'):9s} {field_hit:8s}")

    print()
    if len(rows) < 2:
        print(f"Only one being filed a ranking, so there is no divergence to measure: **{rows[0]['member']}** "
              f"put the champion at #{rows[0]['order'].index(champion) + 1 if champion in rows[0]['order'] else '?'}. "
              f"A comparison needs at least two.")
    else:
        print("Divergence between pairs — rank correlation, and the median number of places they move a club:")
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                a, b = rows[i], rows[j]
                rho = spearman(a["order"], b["order"])
                common = [c for c in a["order"] if c in b["order"]]
                gaps = [abs(a["order"].index(c) - b["order"].index(c)) for c in common]
                print(f"   {a['member'][:10]:10s} vs {b['member'][:10]:10s}  rho {rho:+.2f}   median {statistics.median(gaps):.0f} places "
                      f"over {len(common)} clubs")
        if len(rows) >= 2:
            spread = {}
            for c in letters:
                places = [r["order"].index(c) for r in rows if c in r["order"]]
                if len(places) > 1:
                    spread[c] = max(places) - min(places)
            if spread:
                worst = max(spread, key=lambda c: spread[c])
                print(f"\nThe club they disagree about most: **{letters[worst]}** — {spread[worst]} places "
                      f"between the highest and lowest ranking. Clubs like that one are the reason a full "
                      f"ordering is worth more than a top three.")
        winners = [c for c in letters if any(r["order"] and r["order"][0] == c for r in rows)]
        print(f"\nFirst choice: " + ", ".join(
            f"{r['member']} {letters[r['order'][0]]}" for r in rows if r["order"]))
        if len(winners) == 1:
            print("All of them led with the same club, which is a fact about the season and not about them.")

    print("\nNo verdict. A ranking that matches the outcome is not a better method — one season is one sample, "
          "and a method can be right for the wrong reason. What these numbers show is where three minds part "
          "on identical facts, which is the only thing that can be seen from a single run.")

    if args.write:
        out = ROOT / "facts" / "rank-comparison.md"
        lines = ["# Three rankings of a season with the clubs taken out", "",
                 f"Season {key['season']}, seed {key['seed']}. Champion: **{letters[champion]}**.", "",
                 "| being | top five | champion rank |", "|---|---|---|"]
        for r in rows:
            cr = r["order"].index(champion) + 1 if champion in r["order"] else None
            lines.append(f"| {r['member']} | {', '.join(letters.get(c, c) for c in r['order'][:5])} | "
                         f"{(('#' + str(cr)) if cr else '—')} |")
        lines += ["", "Read the rankings, not the champion column: one season cannot rank methods."]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n   wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
