#!/usr/bin/env python3
"""Twenty rounds of rock-paper-scissors with no preferences anywhere: the dice decide, the record proves it.

The founder's correction, 2026-11-03. Every version so far measured what a model *prefers* — Remy threw rock
two times in three, Margot half the time, Colette never repeated itself — and a preference is deterministic,
so a repeat run tells you nothing new. His proposal discards preferences: each colonist is handed a random
integer, 1-3, and that integer is its throw. Nothing chooses. Every run must therefore produce a different
score sheet.

Two things are true at once and both are needed:
  - with a fresh seed, two runs give different sheets. That is the point: a score sheet is not a fact about
    anybody's character, and a demo that produces the same page twice is showing you the page.
  - with the same seed, the run reproduces exactly. That is what makes it auditable rather than merely
    random: the seed is printed, so a reader can replay the twenty rounds and confirm the sheet he is
    looking at is the one the dice actually produced.

The record is hash-chained: each round's hash covers the two numbers, the winner, and the previous round's
hash. Edit one throw in the middle and every later link breaks. That is the difference between a transcript
and a claim.

What this demonstrates, stated plainly: the apparatus, not the minds. The colony's honest contribution here
is that a page can be produced, sealed, and checked; the colony cannot make a model's preferences go away.

What the chain can and cannot do. Editing a throw and leaving the hashes alone breaks every link after it,
and `verify` names the first round that fails. An editor who edits a throw *and* recomputes the whole chain
gets a chain that walks cleanly — a hash chain is an honesty check on the file, not a signature. The real
audit is the printed seed: the seed alone decides all forty numbers, so `verify` replays it and compares.
That is why a sheet with no seed beside it is only a pretty table.

Usage:
    python3 lab/dice.py --seats Remy,Margot --rounds 20
    python3 lab/dice.py --seats Remy,Margot --rounds 20 --seed 41 --quiet
    python3 lab/dice.py --verify experiment/dice/41-20261104T000000Z/game.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THROWS = {1: "rock", 2: "paper", 3: "scissors"}
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


def play(seats: list[str], rounds: int, seed: int) -> dict:
    """The whole game, from the seed and nothing else. No model is consulted and no preference is read."""
    rng = random.Random(seed)
    chain, rows = "genesis", []
    for n in range(1, rounds + 1):
        numbers = {s: rng.randint(1, 3) for s in seats}
        throws = {s: THROWS[v] for s, v in numbers.items()}
        a, b = seats[0], seats[1]
        if throws[a] == throws[b]:
            winner = "draw"
        else:
            winner = a if BEATS[throws[a]] == throws[b] else b
        payload = json.dumps({"round": n, "numbers": numbers, "winner": winner, "prev": chain},
                             sort_keys=True)
        chain = hashlib.sha256(payload.encode()).hexdigest()
        rows.append({"round": n, "numbers": numbers, "throws": throws, "winner": winner, "hash": chain})
    return {"seed": seed, "seats": seats, "rows": rows, "final": chain}


def verify(game: dict) -> tuple[bool, str]:
    """Replay the seed and re-walk the chain, and say in words which of the two failed.

    Two separate checks, because they catch different things: the walk catches a throw edited in place, and
    the replay catches a whole chain recomputed to hide that edit — the numbers are a function of the seed,
    so a forged sheet cannot agree with its own seed.
    """
    chain = "genesis"
    for r in game.get("rows", []):
        payload = json.dumps({"round": r["round"], "numbers": r["numbers"], "winner": r["winner"],
                              "prev": chain}, sort_keys=True)
        chain = hashlib.sha256(payload.encode()).hexdigest()
        if chain != r.get("hash"):
            return False, f"round {r['round']} breaks the chain"
    replayed = play(game["seats"], len(game["rows"]), game["seed"])
    for got, want in zip(game["rows"], replayed["rows"]):
        if got["numbers"] != want["numbers"] or got["winner"] != want["winner"]:
            return False, f"round {got['round']} does not match the seed"
    if game.get("final") != replayed["final"]:
        return False, "the chain does not end where the seed says it should"
    return True, f"the seed reproduces all {len(game['rows'])} rounds and the chain holds"


def render(game: dict) -> str:
    """The page is a function of the seed and nothing else.

    The first version printed the wall clock, and then the claim "replay the seed and the sheet comes back
    identical" was false by one line: two runs a minute apart differed. The time is in game.json and in the
    folder name. The page has no clock in it, so `diff` on two replays of the same seed prints nothing —
    which is the whole audit.
    """
    seats, rows = game["seats"], game["rows"]
    a, b = seats
    wins = {s: sum(1 for r in rows if r["winner"] == s) for s in seats}
    draws = sum(1 for r in rows if r["winner"] == "draw")
    out = [f"# {len(rows)} rounds, decided by dice", "",
           f"{a} and {b}. Seed **{game['seed']}**. "
           f"No model chose anything: each throw is a random integer, 1 rock, 2 paper, 3 scissors.", "",
           "| round | " + " | ".join(f"{s} (n)" for s in seats) + " | winner | hash |",
           "|---|---|---|---|---|"]
    for r in rows:
        cells = " | ".join(f"{r['throws'][s]} ({r['numbers'][s]})" for s in seats)
        out.append(f"| {r['round']} | {cells} | {r['winner']} | `{r['hash'][:12]}` |")
    out += ["", f"**{a} {wins[a]}, {b} {wins[b]}, {draws} drawn.** Against a coin each side expects a third "
            f"of the rounds; twenty is not enough to say whether this sheet is fair, and it is not meant to "
            f"be. It is meant to be different every time and checkable afterwards.", "",
            f"Final link: `{game['final']}`", "",
            "Every hash covers the two numbers, the winner, and the previous round's hash, so a throw edited "
            "in place breaks every link after it and `--verify` names the first broken round. An editor who "
            "recomputes the whole chain defeats the chain — a hash chain is an honesty check, not a signature. "
            "The seed is the real audit, and it is on this page: the seed alone decides all the numbers, so "
            "`--verify` replays it. Replay the same seed and this page comes back byte for byte; change the "
            "seed and the page is new. Both of those are the point."]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="rock-paper-scissors with no preferences: the dice decide")
    ap.add_argument("--seats", default="Remy,Margot", help="two names, for the record only")
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--seed", type=int, default=None, help="omit for a fresh sheet, give one to replay")
    ap.add_argument("--out", default=None, help="directory; default experiment/dice/<seed>-<stamp>")
    ap.add_argument("--quiet", action="store_true", help="write the page, print only the summary line")
    ap.add_argument("--verify", default=None, metavar="GAME.JSON",
                    help="check a filed game against its own seed and chain; plays nothing")
    args = ap.parse_args(argv)

    if args.verify:
        try:
            game = json.loads(Path(args.verify).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"   cannot read {args.verify}: {exc}. Nothing was verified.", file=sys.stderr)
            return 2
        ok, why = verify(game)
        print(("  " if ok else "FAIL: ") + why)
        return 0 if ok else 1

    seats = [s.strip() for s in args.seats.split(",")]
    if len(seats) != 2:
        print("   --seats needs exactly two names. Nothing was played.", file=sys.stderr)
        return 2
    if args.rounds < 1:
        print("   --rounds must be at least 1. Nothing was played.", file=sys.stderr)
        return 2

    when = datetime.now(timezone.utc)
    seed = args.seed if args.seed is not None else random.SystemRandom().randint(1, 10**9)
    game = play(seats, args.rounds, seed)
    game["played"] = when.strftime("%Y-%m-%dT%H:%M:%SZ")
    page = render(game)

    out = Path(args.out) if args.out else ROOT / "experiment" / "dice" / f"{seed}-{when:%Y%m%dT%H%M%SZ}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "sheet.md").write_text(page, encoding="utf-8")
    (out / "game.json").write_text(json.dumps(game, indent=2) + "\n", encoding="utf-8")

    a, b = seats
    wins = {s: sum(1 for r in game["rows"] if r["winner"] == s) for s in seats}
    draws = sum(1 for r in game["rows"] if r["winner"] == "draw")
    print(f"seed {seed} → {a} {wins[a]}, {b} {wins[b]}, {draws} drawn, over {args.rounds} rounds")
    if not args.quiet:
        for r in game["rows"][:6]:
            print(f"  round {r['round']:2d}  {r['throws'][a]:8s} ({r['numbers'][a]}) vs "
                  f"{r['throws'][b]:8s} ({r['numbers'][b]})  {r['winner']}")
        if len(game["rows"]) > 6:
            print(f"  … {len(game['rows']) - 6} more rounds in the sheet")
    print(f"   wrote {out.relative_to(ROOT) if str(out).startswith(str(ROOT)) else out}")
    print(f"   replay it with --seed {seed}; the sheet comes back identical, which is how a reader checks it "
          f"was not edited")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
