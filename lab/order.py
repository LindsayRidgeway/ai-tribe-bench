#!/usr/bin/env python3
"""The Hidden Order: the arithmetic of a game whose strategy can only be learned by playing it.

Lindsay's brief, 2026-11-04: a game where one player has practised and learned strategies that only practice
teaches, so it always wins on even terms — and a handicap that gives the other player a chance without making
its play any better. This file is the arithmetic of that idea, not the demonstration. No model is called here.
It answers three questions before anybody spends a key:

  1. Can a table be hidden from a model that has read the internet? Only if nothing about it is derivable.
     So: four signs, and a hidden order drawn at the start of the match — for each of the six pairs, which sign
     beats which. Sixty-four possible orders, no mnemonic, and a model's prior knowledge of rock-paper-scissors
     is worth nothing or worse.
  2. How long does the table take to learn? The clock offers two signs a round and the being chooses one
     blind; the result teaches exactly one relation. Six relations, so a learner needs a handful of rounds per
     relation before it can choose without guessing.
  3. What handicap evens the match? The median differential from even matches — golf's rule, and Go's stones.

The two players here are not minds: one is handed the table (the practised player) and one starts empty and
updates from results (the beginner). That is enough to price the handicap. Whether a real model can learn the
table in twenty rounds is the experiment, and it cannot start until the arithmetic says how many points the
beginner should be given.

    python3 lab/order.py --matches 2000
"""
from __future__ import annotations

import argparse
import itertools
import random
from statistics import median

SIGNS = ("A", "B", "C", "D")
PAIRS = list(itertools.combinations(SIGNS, 2))          # six, and every round offers one


def draw_order(rng: random.Random) -> dict[frozenset, str]:
    """A random order on four signs: for each pair, the sign that beats the other. 2^6 = 64 orders."""
    return {frozenset(p): rng.choice(p) for p in PAIRS}


def winner(order: dict[frozenset, str], pair: tuple[str, str], mine: str) -> str:
    return mine if order[frozenset(pair)] == mine else [s for s in pair if s != mine][0]


class Beginner:
    """Starts knowing nothing and learns one relation per round. When it does not know a pair, it guesses."""

    def __init__(self, rng: random.Random):
        self.belief: dict[frozenset, str] = {}
        self.rng = rng

    def choose(self, pair: tuple[str, str]) -> str:
        known = self.belief.get(frozenset(pair))
        return known if known else self.rng.choice(pair)

    def learn(self, pair: tuple[str, str], won_by: str) -> None:
        self.belief[frozenset(pair)] = won_by


class Practised(Beginner):
    """The same player after the practice: it has the table, and keeps it between matches."""

    def __init__(self, order: dict[frozenset, str]):
        self.belief = dict(order)
        self.rng = random.Random(0)

    def learn(self, pair, won_by) -> None:      # nothing left to learn
        return


def match(order, a, b, rng: random.Random, rounds: int = 20) -> tuple[int, int, int, int]:
    """Returns (a's points, b's points, a's right choices, b's right choices). The second pair is skill:
    the fraction of rounds in which a player chose the sign that actually wins that pair. Handicapping moves
    points; it does not move this number."""
    pts_a = pts_b = 0
    right_a = right_b = 0
    for _ in range(rounds):
        pair = rng.choice(PAIRS)
        ca, cb = a.choose(pair), b.choose(pair)
        truth = order[frozenset(pair)]
        if ca == cb:                            # both picked the same sign: no point, both may be wrong
            right_a += ca == truth
            right_b += cb == truth
            continue
        if ca == truth:
            pts_a += 1
            right_a += 1
        else:
            pts_b += 1
            right_b += 1
        a.learn(pair, truth)
        b.learn(pair, truth)
    return pts_a, pts_b, right_a, right_b


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="price the handicap for a game that must be learned")
    ap.add_argument("--matches", type=int, default=2000)
    ap.add_argument("--rounds", type=int, default=20)
    args = ap.parse_args(argv)
    rng = random.Random(20261104)

    even, drifts, skill_p, skill_b = [], [], [], []
    for _ in range(args.matches):
        order = draw_order(rng)
        fresh = Beginner(rng)
        practised = Practised(order)
        solo = Beginner(rng)
        # the practice: the practised player plays this order once against a beginner, then keeps the table
        match(order, practised, Beginner(rng), rng, rounds=args.rounds)
        pa, pb, ra, rb = match(order, practised, fresh, rng, rounds=args.rounds)
        even.append(pa - pb)
        skill_p.append(100 * ra / args.rounds)
        skill_b.append(100 * rb / args.rounds)

    h = median(even)
    after = [d - h for d in even]
    win_after = 100 * sum(1 for d in after if d > 0) / len(after)
    draw_after = 100 * sum(1 for d in after if d == 0) / len(after)
    print(f"{args.matches} simulated matches of {args.rounds} rounds, {len(PAIRS)} pairs, 64 possible orders\n")
    print(f"  practised vs beginner, even terms: median differential {h:+.0f} points, "
          f"practised wins {100*sum(1 for d in even if d > 0)/len(even):.0f}% of matches")
    print(f"  skill, measured before any handicap: practised right on {median(skill_p):.0f}% of rounds, "
          f"beginner {median(skill_b):.0f}%")
    print(f"  with a handicap of {h:.0f} points to the beginner: beginner wins {win_after:.0f}%, "
          f"draws {draw_after:.0f}%, practised wins {100 - win_after - draw_after:.0f}%")
    print(f"\n  the handicap moves the score, not the skill: the practised player is still right on "
          f"{median(skill_p):.0f}% of rounds against {median(skill_b):.0f}%.")
    print(f"  six relations, one learned per round: a beginner that starts empty cannot have the table before "
          f"round six, and rounds after that still offer pairs it has not met.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
