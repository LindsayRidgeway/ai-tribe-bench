#!/usr/bin/env python3
"""Write one season of NFL regular-season data as a facts file with the clubs taken out.

Why football and why letters, in the founder's words. Baseball for 2026 produced the same three clubs from
three sealed engines — *"Maybe it was that obvious, but that's not a good demo."* Football fixes the first
half of that: seventeen games, single elimination, and a champion that is usually not the best team, so no
consensus shortcut works. Letters fix the second half: with a club's name in front of it a being is not
analysing the data, it is reasoning from what it already believes about franchises, and that reputation
arrives in the METHOD line dressed as method.

What is in the file: every club's regular season — record, points, yards, sacks, turnovers, third down,
possession — and nothing else. What is not in it: the season, any club name, any postseason result, and
which clubs qualified. That last omission is deliberate and it is also a measurement: naming the twelve is
part of the judgement, so a ranking can be scored twice, once for the champion and once for the field.

Why the letters come from a seed and the key is written outside the repository: a key filed beside the facts
is not a key, and a draw that cannot be repeated cannot be checked. Re-run with the same seed and the letters
come out the same.

Usage:
    python3 lab/sport_facts.py --season 2011 --out facts/season-anon.md --key-out /tmp/nfl-2011-key.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
CORE = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/types/2"
UA = {"User-Agent": "ai-tribe-bench/1.0"}

# Columns chosen to be contestable rather than decisive. Each has a school of thought that says it matters
# most; none of them is the standings. Anything ESPN serves as an unpopulated zero is not here — the first
# draft of this file printed "points allowed: 0" for all thirty-two clubs, which is a fact about the
# endpoint and would have been read as a fact about the defences.
COLUMNS = [
    ("pass yards per game", "passing", "netPassingYardsPerGame"),
    ("rush yards per game", "rushing", "rushingYardsPerGame"),
    ("completion pct", "passing", "completionPct"),
    ("pass TDs", "passing", "passingTouchdowns"),
    ("interceptions thrown", "passing", "interceptions"),
    ("fumbles lost", "general", "fumblesLost"),
    ("sacks made", "defensive", "sacks"),
    ("interceptions made", "defensiveInterceptions", "interceptions"),
    ("passes defended", "defensive", "passesDefended"),
    ("third down conv pct", "miscellaneous", "thirdDownConvPct"),
    ("first downs per game", "miscellaneous", "firstDownsPerGame"),
    ("time of possession (s)", "miscellaneous", "possessionTimeSeconds"),
]


def get(url: str, tries: int = 3) -> dict:
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:      # noqa: BLE001 — a retry is the point
            last = e
    raise last


def results(team_id: str, season: int) -> dict:
    """Record and points, computed from the sixteen games rather than read off a record endpoint.

    The record endpoint left `playoffSeed` on some clubs and not others and served zeroes for points
    allowed, so the games themselves are the honest source: they are what happened, and the arithmetic is
    trivial enough to check by hand.
    """
    data = get(f"{SITE}/teams/{team_id}/schedule?season={season}")
    w = l = t = pf = pa = 0
    for ev in data.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        sides = comp.get("competitors") or []
        if len(sides) != 2:
            continue
        mine = next((s for s in sides if str(s.get("team", {}).get("id")) == str(team_id)), None)
        other = next((s for s in sides if s is not mine), None)
        if not mine or not other:
            continue
        ms, os_ = mine.get("score", {}).get("value"), other.get("score", {}).get("value")
        if ms is None or os_ is None:
            continue
        pf += int(ms)
        pa += int(os_)
        if ms > os_:
            w += 1
        elif ms < os_:
            l += 1
        else:
            t += 1
    played = w + l + t
    return {"W": w, "L": l, "T": t, "PF": pf, "PA": pa, "played": played,
            "point diff": pf - pa,
            "points for per game": pf / played if played else None,
            "points allowed per game": pa / played if played else None}


def extras(team_id: str, season: int) -> dict:
    stat = get(f"{CORE.format(season=season)}/teams/{team_id}/statistics")
    row = {}
    for cat in stat.get("splits", {}).get("categories", []):
        values = {s.get("name"): s.get("value") for s in cat.get("stats", [])}
        for label, cname, key in COLUMNS:
            if cat.get("name") == cname and values.get(key) not in (None, 0, 0.0):
                row[label] = values[key]
    return row


def fmt(v) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:,.2f}".rstrip("0").rstrip(".")
    return str(v)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="an NFL season's regular season, with the clubs taken out")
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--key-out", required=True, help="letter->club mapping; keep it out of the repository")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args(argv)

    seed = args.seed if args.seed is not None else int(datetime.now(timezone.utc).strftime("%Y%m%d"))
    try:
        listing = get(f"{SITE}/teams?season={args.season}&limit=40")
        teams = listing["sports"][0]["leagues"][0]["teams"]
    except Exception as e:      # noqa: BLE001
        print(f"   could not read the {args.season} club list: {e}", file=sys.stderr)
        print("   nothing was written. A facts file invented from memory is worse than none.", file=sys.stderr)
        return 2
    if len(teams) != 32:
        print(f"   the club list came back with {len(teams)} clubs, not 32. Nothing written.", file=sys.stderr)
        return 2

    clubs = []
    for entry in sorted(teams, key=lambda t: t["team"]["displayName"]):
        team = entry["team"]
        try:
            row = results(team["id"], args.season)
            row.update(extras(team["id"], args.season))
        except Exception as e:      # noqa: BLE001
            print(f"   {team['displayName']}: {e}. Nothing written.", file=sys.stderr)
            return 2
        if not row["played"]:
            print(f"   {team['displayName']}: no games with scores came back. Nothing written.", file=sys.stderr)
            return 2
        row["club"] = team["displayName"]
        clubs.append(row)

    letters = [chr(ord("A") + i) for i in range(26)] + [f"A{chr(ord('A') + i)}" for i in range(6)]
    order = clubs[:]
    random.Random(seed).shuffle(order)
    mapping = {letters[i]: order[i]["club"] for i in range(len(order))}
    inv = {v: k for k, v in mapping.items()}

    now = datetime.now(timezone.utc)
    head = ["# A season, with the clubs taken out", "",
            f"Facts written {now:%Y-%m-%d %H:%M} UTC from ESPN's public regular-season record. The season is "
            f"not named and the clubs are not named, on purpose: what is being asked of you is a method, and "
            f"a club's name would let you answer from reputation instead.", "",
            "Thirty-two clubs, letters instead of names. Every row is that club's regular season, computed "
            "from its own sixteen games.", "",
            "| club | W | L | T | points for per game | points allowed per game | point diff | "
            + " | ".join(c[0] for c in COLUMNS) + " |",
            "|---" * (8 + len(COLUMNS)) + "|---|"]
    for c in sorted(clubs, key=lambda c: (-(c["W"]), c["L"])):
        cells = [inv[c["club"]], fmt(c["W"]), fmt(c["L"]), fmt(c["T"]),
                 fmt(c.get("points for per game")), fmt(c.get("points allowed per game")), fmt(c["point diff"])]
        cells += [fmt(c.get(label)) for label, _, _ in COLUMNS]
        head.append("| " + " | ".join(cells) + " |")

    head += ["", "## What is not in this file, and why", "",
             "- **The season and every club name.** Not secrecy: with a name in front of you, a franchise's "
             "reputation does the reasoning and your METHOD line ends up describing the reputation.",
             "- **Which clubs reached the postseason.** Twelve of these thirty-two did. Deciding which is part "
             "of the judgement, which is why it is not marked, and why a ranking can be scored twice: once on "
             "the club that won it all, and once on the field you picked.",
             "- **Anything from the postseason.** No bracket, no scores, no champion. You will not be told the "
             "answer afterwards either. A being that learns the result can never be asked this question "
             "again, and the record of this run stays clean for the next one.",
             "- **Rosters, injuries, coaching, weather, and everything a person would have read in a "
             "newspaper.** Every being deciding this has the same rows and only its own weighting to argue "
             "with. That is the experiment.", "",
             "## What you are asked for", "",
             "A complete ranking of all thirty-two clubs, best to worst, by how likely each was to win that "
             "season's championship. Every club appears once. Not a top three: the disagreements that make "
             "this worth doing live in the middle of the table, and a full ordering is what makes them "
             "visible and measurable.", ""]

    dest = Path(args.out)
    if not dest.is_absolute():
        dest = ROOT / dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(head) + "\n", encoding="utf-8")

    kp = Path(args.key_out)
    kp.parent.mkdir(parents=True, exist_ok=True)
    kp.write_text(json.dumps({"season": args.season, "seed": seed, "written": now.isoformat(),
                              "letters": mapping}, indent=2) + "\n", encoding="utf-8")
    print(f"   wrote {dest} ({len(clubs)} clubs, {len(COLUMNS)} contested columns, all from the games")
    print(f"   wrote the letter mapping to {kp} — outside the repository, because a key beside the facts is "
          f"not a key")
    print(f"   seed {seed}: re-run with it and the draw repeats, which is how a reader checks the letters "
          f"were not arranged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
