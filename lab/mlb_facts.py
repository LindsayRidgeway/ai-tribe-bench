#!/usr/bin/env python3
"""Write one season's regular-season record as a facts file with the names taken out.

Why. Two runs of the 2026 experiment came back with the same three clubs — Milwaukee, Los Angeles, New
York — from three engines sealed from each other. The founder's reading was exact: *"Maybe it was that
obvious, but that's not a good demo."* Two things make a season obvious: the favourite really is obvious,
and the season is famous. The first is a property of the year and the second is a property of the model's
weights, and swapping the year does not fix the second — every finished season is inside some model's
memory.

So this tool fixes both at once. It takes a season and strips the names: thirty clubs become letters, the
twelve in the field are marked, and the letters are drawn from a seed rather than from the standings order.
A member cannot recall who won a season it cannot name, and the season is chosen for the property that
makes a good demo — a champion nobody's consensus method would have picked.

What it does not fix, stated plainly so nobody has to discover it: the record table is itself a
fingerprint. Thirty win-loss records are distinctive enough that a determined being could match them to a
season it remembers. That is why the task asks for a `RECOGNISE:` line, and why a run where everybody
recognises the year is a finding rather than a failure.

The mapping is written outside the repository on purpose. A key filed next to the facts is not a key.

Usage:
    python3 lab/mlb_facts.py --season 2021 --out facts/mlb-2021-anon.md --key-out /tmp/mlb-2021-key.json
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
API = "https://statsapi.mlb.com/api/v1"
LEAGUES = {103: "AL", 104: "NL"}
DIVISIONS = {200: "AL West", 201: "AL East", 202: "AL Central",
             203: "NL West", 204: "NL East", 205: "NL Central"}
UA = {"User-Agent": "ai-tribe-bench/1.0"}


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


def clubs(season: int) -> list[dict]:
    data = get(f"{API}/standings?leagueId=103,104&season={season}&standingsTypes=regularSeason")
    out = []
    for rec in data.get("records", []):
        div = DIVISIONS.get((rec.get("division") or {}).get("id"), "?")
        league = LEAGUES.get((rec.get("league") or {}).get("id"), "?")
        for t in rec.get("teamRecords", []):
            out.append({
                "id": t["team"]["id"],
                "club": t["team"]["name"],
                "w": t["wins"], "l": t["losses"],
                "pct": float(t.get("winningPercentage") or 0),
                "rs": t.get("runsScored"), "ra": t.get("runsAllowed"),
                "division": div, "league": league,
                "clinched": bool(t.get("clinchIndicator")),
            })
    return out


def profile(team_id: int, season: int) -> dict:
    """The two aggregate rows a member would otherwise have to fetch itself."""
    out = {}
    h = get(f"{API}/teams/{team_id}/stats?stats=season&group=hitting&season={season}")
    p = get(f"{API}/teams/{team_id}/stats?stats=season&group=pitching&season={season}")
    for key, data, fields in (("hit", h, ("avg", "obp", "slg", "homeRuns", "runs", "strikeOuts", "baseOnBalls")),
                              ("pit", p, ("era", "whip", "homeRuns", "strikeOuts", "baseOnBalls", "runs"))):
        try:
            st = data["stats"][0]["splits"][0]["stat"]
            out[key] = {f: st.get(f) for f in fields}
        except (KeyError, IndexError):
            out[key] = {}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="a season's regular-season record, with the names taken out")
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--out", required=True, help="where to write the facts file (in the repository)")
    ap.add_argument("--key-out", required=True, help="where to write the letter->club mapping (NOT in the repo)")
    ap.add_argument("--seed", type=int, default=None, help="so the draw can be repeated and checked")
    ap.add_argument("--no-profiles", action="store_true", help="skip the per-club hitting and pitching rows")
    args = ap.parse_args(argv)

    season = args.season
    seed = args.seed if args.seed is not None else int(datetime.now(timezone.utc).strftime("%Y%m%d"))
    try:
        rows = clubs(season)
    except Exception as e:      # noqa: BLE001
        print(f"   could not read the {season} standings: {e}", file=sys.stderr)
        print("   nothing was written. A facts file invented from memory is worse than no facts file.",
              file=sys.stderr)
        return 2
    if len(rows) != 30:
        print(f"   the {season} standings came back with {len(rows)} clubs, not 30. Nothing written.",
              file=sys.stderr)
        return 2

    field = [r for r in rows if r["clinched"]]
    if len(field) < 8:
        print(f"   only {len(field)} clubs carry a clinch marker for {season}, so the playoff field cannot be "
              f"read from this payload. Nothing written: guessing the field would decide the experiment.",
              file=sys.stderr)
        return 2

    letters = [chr(ord("A") + i) for i in range(26)] + [f"A{chr(ord('A') + i)}" for i in range(4)]
    order = rows[:]
    random.Random(seed).shuffle(order)
    mapping = {letters[i]: order[i]["club"] for i in range(30)}
    inv = {v: k for k, v in mapping.items()}

    prof = {}
    if not args.no_profiles:
        for r in field:
            prof[r["club"]] = profile(r["id"], season)

    now = datetime.now(timezone.utc)
    keyed = sorted(rows, key=lambda r: (r["league"], r["division"], -r["pct"]))
    out = [f"# A season, with the names taken out", "",
           f"Facts written {now:%Y-%m-%d %H:%M} UTC from the league's own record (statsapi.mlb.com), season "
           f"withheld on purpose. Thirty clubs, letters instead of names. The {len(field)} marked `field: yes` are "
           f"the clubs that reached the postseason in this season.", "",
           "| club | league | division | W | L | pct | runs scored | runs allowed | run diff | in the field |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in keyed:
        out.append(f"| {inv[r['club']]} | {r['league']} | {r['division']} | {r['w']} | {r['l']} | "
                   f"{r['pct']:.3f} | {r['rs']} | {r['ra']} | {r['rs'] - r['ra']:+d} | "
                   f"{'yes' if r['clinched'] else 'no'} |")

    if prof:
        out += ["", f"## Aggregate hitting and pitching, for the {len(field)} clubs in the field", "",
                "| club | AVG | OBP | SLG | HR | R | SO (bat) | BB (bat) | ERA | WHIP | HR allowed | SO (pit) | BB (pit) |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for cl in sorted(prof, key=lambda c: inv[c]):
            h, p = prof[cl].get("hit", {}), prof[cl].get("pit", {})
            def f(d, k):
                # The league's own payload returns some of these as strings ("3.21") and some as numbers,
                # which is the kind of inconsistency that only shows up when a format string meets it.
                v = d.get(k)
                if v is None or v == "":
                    return "—"
                if k in ("avg", "obp", "slg", "era", "whip"):
                    try:
                        return f"{float(v):.3f}"
                    except (TypeError, ValueError):
                        return str(v)
                return str(v)
            out.append(f"| {inv[cl]} | {f(h,'avg')} | {f(h,'obp')} | {f(h,'slg')} | {f(h,'homeRuns')} | "
                       f"{f(h,'runs')} | {f(h,'strikeOuts')} | {f(h,'baseOnBalls')} | {f(p,'era')} | "
                       f"{f(p,'whip')} | {f(p,'homeRuns')} | {f(p,'strikeOuts')} | {f(p,'baseOnBalls')} |")

    out += ["", "## What is not in this file", "",
            "- The season, the league's year, and every club name.",
            "- Anything from the postseason: no bracket, no series results, no October statistics.",
            "- Injuries, trades, payroll, park factors, and everything else a person would have read in a "
            "newspaper. If you want it, you cannot have it: the point is that every being deciding this has "
            "identical facts and only its own weighting to argue with.", ""]

    dest = Path(args.out)
    if not dest.is_absolute():
        dest = ROOT / dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")

    key = {"season": season, "seed": seed, "written": now.isoformat(), "letters": mapping}
    kp = Path(args.key_out)
    kp.parent.mkdir(parents=True, exist_ok=True)
    kp.write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")

    print(f"   wrote {dest} ({len(rows)} clubs, {len(field)} of them in the field)")
    print(f"   wrote the letter mapping to {kp} — outside the repository, because a key filed beside the "
          f"facts is not a key")
    print(f"   seed {seed}: re-run with the same seed and the draw repeats, which is how a reader checks "
          f"that the letters were not chosen to suit an answer")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
