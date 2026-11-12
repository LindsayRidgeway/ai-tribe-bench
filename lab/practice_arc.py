#!/usr/bin/env python3
"""The learning curve, watched rather than asserted.

The founder, 2026-11-12: "Think how cool it will be to *see* players get better with practice."

Everything in this engine is already a function of balls hit — `skill()` is asymptotic in practice, movement speed
is built on it, the serve's pace and placement are built on it, the racquet goes back earlier, the errors shrink.
What was missing was a way to *look*. This writes the same twenty points at both ends of a career and a table of
what changes between them, so the claim "they are getting better" is a thing you can flip between in two tabs
instead of a paragraph in a design note.

    python3 lab/practice_arc.py                 # the table and the three films
    python3 lab/practice_arc.py --table-only    # just the numbers

Three films, not two, because the two ends of a career are not the interesting comparison: at zero practice half
the points are double faults and there is no tennis in the film at all. The middle one — a hundred and twenty
balls, a month of Sundays — is where rallies start happening, and it is the one that shows what practice buys.

The films are the same court, the same wind, the same clock, the same twenty rallies and the same pair; the only
thing that differs is how many balls they have hit before today. What changes as the number rises:

    balls  rating  rally  longest  balls reached  serve  double faults
        0    1.00   2.33        6            91%   49mph             14
      400    6.79   3.23       11            77%   72mph              0

Two of those are improvements in the obvious direction and one is not, and the one that is not is the interesting
one: a better player misses MORE balls, because they hit the ball where the other player cannot get to it. At zero
practice nobody is beaten to a ball — the points are lost by the beginner hitting them out, double-faulting, or
mishitting, which is exactly how a beginner loses a point in life. The film shows the two failure modes side by
side, which is the thing the founder asked to see.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tennis as T          # noqa: E402
import tennis_script as S   # noqa: E402

GAMES = Path(__file__).resolve().parent.parent / "games" / "tennis"
LEVELS = (0, 25, 60, 120, 250, 400, 700)
RALLIES = 40               # per level, for the table; the films use FILM_RALLIES
FILM_RALLIES = 20
CLOCK = 1793809110303      # the same clock as the page on the wall, so the wind is the same wind


def measure(practice: int, rallies: int = RALLIES) -> dict:
    """Play `rallies` points with both players on `practice` balls and count what a spectator could see."""
    data = S.play((practice, practice), ("Dmitri", "Gwen"), rallies, CLOCK, "clay")
    shots = data["shots"]
    runs = [s["run"] for s in shots if s.get("run")]
    serves = [s for s in shots if s["swing"] == "serve"]
    lens = [r["length"] for r in data["rallies"]]
    met = sum(1 for r in runs if r.get("met"))
    return {
        "balls": practice,
        "rating": data["players"][0]["rating"],
        "rally": statistics.mean(lens) if lens else 0.0,
        "longest": max(lens) if lens else 0,
        "reached": 100.0 * met / len(runs) if runs else 0.0,
        "run": statistics.mean([r["dist"] for r in runs]) if runs else 0.0,
        "serve": statistics.mean([s["power"] for s in serves]) if serves else 0.0,
        # a double fault is the only way a point ends with the server having hit two balls and lost neither to
        # the other player; the record says so in words, so it is counted in words
        "double_faults": sum(1 for r in data["rallies"] if "double fault" in (r["point"]["reason"] or "")),
        "points": len(data["rallies"]),
        "shots": len(shots),
    }


def table(rows: list[dict]) -> str:
    out = ["| balls before today | rating | mean rally | longest | balls reached | mean run | first serve "
           "| double faults |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['balls']} | {r['rating']:.2f} | {r['rally']:.2f} shots | {r['longest']} | "
                   f"{r['reached']:.0f}% | {r['run']:.1f}ft | {r['serve']:.0f}mph | "
                   f"{r['double_faults']} of {r['points']} |")
    return "\n".join(out)


def film(practice: int, out: Path, rallies: int = FILM_RALLIES) -> str:
    """Write one 3D page at a given practice level, from the template beside it."""
    data = S.play((practice, practice), ("Dmitri", "Gwen"), rallies, CLOCK, "clay")
    html = (GAMES / "replay3d.html").read_text().replace("__SCRIPT__", str(__import__("json").dumps(data)))
    out.write_text(html)
    lens = [r["length"] for r in data["rallies"]]
    return f"{out.name}: {len(data['shots'])} shots, rallies {lens}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table-only", action="store_true")
    a = ap.parse_args(argv)

    rows = [measure(p) for p in LEVELS]
    print(table(rows))
    if a.table_only:
        return 0

    print()
    for balls, name in ((0, "demo3d-000.html"), (120, "demo3d-120.html"), (400, "demo3d.html")):
        print(film(balls, GAMES / name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
