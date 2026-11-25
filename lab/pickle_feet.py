"""§5u: what practice buys in hands, in feet, and what a game count can see — re-runnable.

    python3 lab/pickle_feet.py                 # the three rows, 24 games each, steady hands
    python3 lab/pickle_feet.py --level dink
    python3 lab/pickle_feet.py --gap 0.37 --games 48    # the feet-only row at 96 games

Three conditions, each in the §5s two-half shape (the trait moves between seats, the pins do not, so anything
belonging to a seat and a clock is in both halves and drops out):

  hands  150 vs 250 balls, reach pinned at 6.0 for all four      -> the hands alone
  curve  150 vs 250 balls, the reach curve of §5t                -> the hands and the feet
  feet   200 vs 200 balls, reach pinned 6.00 vs 6.00 - gap       -> the feet alone

`curve` minus `hands` is what practice buys in feet; `feet` prices the same few inches when the hands are equal,
so the quantity arrives twice and the two routes can be compared. The numbers this prints are the page's §5u
tables: 21/24 for the hands at a 100-ball gap, 252 against 252 for the feet on top of them, and 54/96 — twelve
games short of anything — for 0.37 ft on their own.
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pickleball as pk

NAMES = ["A", "B", "C", "D"]
NORTH = ("A", "B")
CLOCK0 = 1234500


def one(level, practice, reach_for, clock):
    """One game. `reach_for` is None for the curve, else name -> ft. Returns (match, reach per player at the end)."""
    pk.REACH_FOR.clear()
    if reach_for:
        pk.REACH_FOR.update(reach_for)
    film = {}
    try:
        m, _out = pk.play_game(NAMES, practice, pk.make_chooser(level), wind_seed_ms=clock,
                               say=lambda *a, **k: None, film=film)
        shots = {}
        for s in film.get("shots") or []:
            shots[s["player"]] = shots.get(s["player"], 0) + 1
        reach = {n: pk.reach_of(type("P", (), {"name": n, "practice": practice[i],
                                              "shots": shots.get(n, 0)}))
                 for i, n in enumerate(NAMES)}
    finally:
        pk.REACH_FOR.clear()
    return m, reach


def halves(heads, seconds, games):
    """Two halves of one condition: `heads` and `seconds` are (practice, reach_for, seats) — the seats holding the
    advantage. Returns points for the advantage, games won, per-pin margins and the mean reach of each seat."""
    pts = won = 0
    per_half, margins, adv_reach, oth_reach = [], [], [], []
    for practice, reach_for, seats in (heads, seconds):
        hp = hg = 0
        for g in range(games):
            m, rch = one(LEVEL, practice, reach_for, CLOCK0 + g)
            i = 0 if seats[0] in NORTH else 1
            a, b = m.teams[i].score, m.teams[1 - i].score
            hp += a
            hg += 1 if a > b else 0
            margins.append(a - b)
            mine = NAMES[:2] if i == 0 else NAMES[2:]
            theirs = NAMES[2:] if i == 0 else NAMES[:2]
            adv_reach += [rch[n] for n in mine]
            oth_reach += [rch[n] for n in theirs]
        per_half.append((hp, hg))
        pts += hp
        won += hg
    agree = sum(1 for i in range(games) if margins[i] * margins[i + games] > 0)
    mean = lambda xs: round(sum(xs) / len(xs), 3)
    return {"pts": pts, "games": won, "halves": per_half, "agree": agree, "margins": margins,
            "reach": {"advantaged": mean(adv_reach), "other": mean(oth_reach)}}


ap = argparse.ArgumentParser()
ap.add_argument("--level", default="steady", choices=("steady", "dink", "place"))
ap.add_argument("--games", type=int, default=12, help="games a half")
ap.add_argument("--gap", type=float, default=0.37, help="ft, for the feet-only row")
ap.add_argument("--json", default=None)
args = ap.parse_args()
LEVEL = args.level
G = args.games
SIX = {"A": 6.0, "B": 6.0, "C": 6.0, "D": 6.0}
LONG, SHORT = {"A": 6.0, "B": 6.0, "C": 6.0 - args.gap, "D": 6.0 - args.gap}, \
              {"A": 6.0 - args.gap, "B": 6.0 - args.gap, "C": 6.0, "D": 6.0}
CONDS = [
    ("hands", (([150, 150, 250, 250], SIX, ("C", "D")), ([250, 250, 150, 150], SIX, ("A", "B")))),
    ("curve", (([150, 150, 250, 250], None, ("C", "D")), ([250, 250, 150, 150], None, ("A", "B")))),
    ("feet",  (([200] * 4, LONG, ("A", "B")), ([200] * 4, SHORT, ("C", "D")))),
]

out = {}
for label, hs in CONDS:
    r = halves(*hs, games=G)
    out[label] = r
    halves_str = "  ".join(f"{p} pts {w}/{G}" for p, w in r["halves"])
    print(f"{label:6s} {LEVEL} {2 * G} games: {r['pts']} pts, {r['games']}/{2 * G} games | "
          f"halves {halves_str} | pins agreeing {r['agree']}/{G} | reach "
          f"{r['reach']['advantaged']:.2f} vs {r['reach']['other']:.2f} ft", flush=True)
if args.json:
    json.dump(out, open(args.json, "w"), indent=1)
