#!/usr/bin/env python3
"""Play a season from the setup file Dmitri's Play page writes.

    python3 lab/run_season.py --setup games/tennis/players.json

The contract is `games/tennis/SETUP.md`: the page decides who plays, on what, and what they look like; this
file turns that into a record the viewer can fetch. Five steps, in the order the contract needs them:

1. read `players.json` (`schema: ait-tennis-setup/1`) and resolve what is absent — a missing `look` is a body
   file's own appearance, a missing `history` is nought balls, a missing `rallies` is eight points;
2. write the **provenance copy** `seasons/<season>/setup.json`, once and never again (§3). A season's numbers
   have to be re-derivable a year later, so a pointer to a file that has since been edited is not enough; and
   the copy is what the picture reads, so repainting January by editing March is not possible;
3. play `session.rallies` points at each member's carried ball count — `history` is balls, not a rating,
   and the same formula turns 300 given balls into the same hands as 300 hit ones (§1);
4. write `seasons/<season>/rally.json` — the record — which `replay3d.html?record=…` fetches;
5. print the one link the Play page needs.

What this does NOT do: it does not touch the season book. `practice.json` and `report.md` are `lab/tennis.py
--rally --season …`'s job, and they are the record of what was hit rather than the film of one evening. This
file writes the film. Two writers to one folder is fine because they write different files — but the ball
counts this season adds are the book's, not this file's.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tennis_script as TS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TENNIS = ROOT / "games" / "tennis"
SCHEMA = "ait-tennis-setup/1"


def resolve(setup: dict) -> dict:
    """Fill in what the page may leave out, and refuse what it may not."""
    if setup.get("schema") != SCHEMA:
        raise SystemExit(f"not a {SCHEMA} file: schema is {setup.get('schema')!r}")
    players = setup.get("players") or []
    if len(players) != 2:
        raise SystemExit(f"a match is two members; this file has {len(players)}")
    session = dict(setup.get("session") or {})
    session.setdefault("season", time.strftime("%Y-%m"))
    session.setdefault("surface", "clay")
    session.setdefault("rallies", 8)
    session.setdefault("temperature", 1.0)
    for p in players:
        p.setdefault("look", {})
        p.setdefault("history", 0)
    return {"players": players, "session": session}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="play a season from a setup file")
    ap.add_argument("--setup", default=str(TENNIS / "players.json"))
    ap.add_argument("--clock", type=int, default=None, help="seed and timestamp (default: now)")
    ap.add_argument("--force", action="store_true", help="replay a season that already has a record")
    a = ap.parse_args(argv)

    raw = json.loads(Path(a.setup).read_text())
    cfg = resolve(raw)
    sess = cfg["session"]
    folder = TENNIS / "seasons" / sess["season"]

    # §3: once, and never updated. A season that already has a copy was played under it; rewriting the copy
    # would repaint a match that has already happened.
    copy = folder / "setup.json"
    if copy.exists() and not a.force:
        raise SystemExit(f"{copy} exists — that season was played under it. Nothing is rewritten; "
                         f"pick another season name, or --force if you mean to replay this one.")
    folder.mkdir(parents=True, exist_ok=True)
    copy.write_text(json.dumps(raw, indent=1) + "\n")

    names = tuple(p["name"] for p in cfg["players"])
    practice = tuple(int(p["history"]) for p in cfg["players"])
    clock = a.clock if a.clock is not None else int(time.time() * 1000)
    data = TS.play(practice, names, sess["rallies"], clock, sess["surface"])

    rec = folder / "rally.json"
    rec.write_text(json.dumps(data))
    print(f"wrote {copy} and {rec} ({rec.stat().st_size // 1024} KB, {len(data['shots'])} shots)")
    print(f"rallies {[r['length'] for r in data['rallies']]}")
    print(f"open: games/tennis/replay3d.html?record=seasons/{sess['season']}/rally.json"
          f"   (and replay.html for the top-down view)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
