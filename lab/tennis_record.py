#!/usr/bin/env python3
"""Re-decide a 3D record's reaches with the engine's own rule, and write the record back out.

Why this file exists rather than the generator that made the geometry. `games/tennis/seasons/*/rally.json` and the
demo pages carry a per-shot record — the ball's traced path, where each player's feet began and ended, the stance,
the walk between points — and the script that produced that geometry (`lab/tennis_script.py`) is **not on this
branch**. It lives on `origin/desi/tennis-video`, and it calls ten functions of an older `tennis.py` this branch
does not have (`intercept`, `volley_contact`, `recovery_spot`, `choose_shot`, `placement`, `hit_window`, a tracing
`flight`…). So the record's *geometry* cannot be regenerated here, and pretending otherwise would be inventing it.

What can be done honestly is what this file does: take a record's own geometry — every ball's contact point, launch
velocity and spin, every player's position — replay the ball through today's integrator, ask today's `interception`
about the player who has to get to it, and rewrite the record with the answer. A ball that is now out of reach ends
its rally, because under this rule no rally can have a shot after it. Every number written here comes from
`lab/tennis.py`; the only thing this file supplies is the order in which the questions are asked.

    python3 lab/tennis_record.py --in games/tennis/seasons/2026-spring/rally.json \\
                                 --out games/tennis/records/rally-out-of-reach.json
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tennis as T  # noqa: E402


def players_of(record: dict) -> dict[str, T.Player]:
    out = {}
    for p in record["players"]:
        out[p["name"]] = T.Player(p["name"], bool(p.get("north")), int(p.get("balls", 0)))
    return out


def replay_ball(shot: dict, wind, surface: str) -> dict | None:
    """The ball this shot hit, integrated again from the numbers the record used to launch it."""
    if not shot.get("v0") or not shot.get("contact"):
        return None
    traj = T.flight(tuple(shot["contact"]), tuple(shot["v0"]), wind, surface, cl=shot.get("cl", 0.0))
    if traj.get("land") is None:
        return None
    return traj


def decide(record: dict) -> tuple[dict, list[str]]:
    surface = record["surface"]
    wind = tuple(record["wind"]["vector"])
    people = players_of(record)
    shots = copy.deepcopy(record["shots"])
    notes: list[str] = []
    rallies = []

    for rally in record["rallies"]:
        idxs = list(rally["shots"])
        point = dict(rally.get("point") or {})
        kept: list[int] = []
        length = 0
        ended = "record"                            # the record's own boundary, if nothing else ends it
        for k in idxs:
            sh = shots[k]
            kept.append(k)
            length += 1
            if not sh.get("in"):
                ended = "out"                           # the ball missed the court; nothing to intercept
                break
            traj = replay_ball(sh, wind, surface)
            if traj is None:
                ended = "lost"
                break
            receiver = next(n for n in people if n != sh["player"])
            # Which end each player is at is a property of the shot, not of the record's opening lineup: these
            # players change ends every five points, and reading `record["players"]` for it put a runner on the
            # wrong half of the court for every rally after the first change. Nothing in the pictures looks more
            # broken than a person running away from the ball on the wrong side of the net.
            people[receiver].north = not bool(sh.get("north"))
            frm = sh["run"]["from"] if sh.get("run") else None
            m = T.interception(people[receiver], traj["land"], traj["time"], traj["bounce"], surface, frm=frm)
            run = {
                "player": receiver, "north": people[receiver].north,
                "from": [round(v, 2) for v in (frm or [0.0, 0.0])],
                "to": [round(v, 2) for v in m["got"]],
                "t0": 0.0, "t1": round(min(m["at"], traj["time"] + 1.2), 3),
                "dist": round(min(m["gap"], m["speed"] * max(0.0, m["have"] - T.SETTLE)), 1),
                "speed": round(m["speed"], 1),
                "met": bool(m["ok"]),
                "need": round(m["need"], 1), "have": round(m["have"], 2),
                "short": round(max(0.0, m["short_ft"]), 1),
                # the ball at the moment it was closest to them, and how far the feet still were from it —
                # the two numbers a viewer can check against the picture
                "ball": [round(v, 2) for v in m["meet"][:2]],
                "gap": round(math.hypot(m["meet"][0] - m["got"][0], m["meet"][1] - m["got"][1]), 1),
            }
            before = sh.get("run") or {}
            if before.get("volley"):
                run["volley"] = True
            sh["run"] = run
            if not m["ok"]:
                # a record that has been through this tool once already carries the previous verdict;
                # strip it rather than stacking two of them in one line
                base = re.sub(r"\s+—\s+\S+ \d+(?:\.\d+)?ft short of it.*$", "", str(sh.get("why", "")))
                sh["why"] = f"{base} — {receiver} {m['why']}".strip(" —")
                point = {"winner": sh["player"], "reason": f"{receiver} did not reach it — {m['why']}"}
                ended = "beat"
                notes.append(f"rally {rally['rally']}: {sh['player']} beat {receiver}, short {run['short']:.0f}ft "
                             f"after {length} shots")
                break
        kept_set = set(kept)
        shots = [s if i in kept_set else s for i, s in enumerate(shots)]
        rallies.append({"rally": rally["rally"], "shots": kept, "length": length, "point": point, "ended": ended,
                        "clock_ms": rally.get("clock_ms"),
                        "ends": rally.get("ends"), "changed_ends": rally.get("changed_ends")})

    alive = sorted({i for r in rallies for i in r["shots"]})
    remap = {old: new for new, old in enumerate(alive)}
    final = []
    for new, old in enumerate(alive):
        sh = shots[old]
        sh["n"] = new
        sh["i"] = new
        final.append(sh)
    for r in rallies:
        r["shots"] = [remap[i] for i in r["shots"]]
        for sh in final:
            if r["shots"] and sh["n"] == r["shots"][0]:
                sh["rally"] = r["rally"]

    out = copy.deepcopy(record)
    out["shots"] = final
    out["rallies"] = rallies
    out["generated"] = ("lab/tennis_record.py — the geometry is the 2026-spring record's, replayed through "
                        "lab/tennis.py; every reach decided by tennis.interception()")
    out["rebuilt"] = {"from": str(record.get("generated", ""))}
    return out, notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default="games/tennis/seasons/2026-spring/rally.json")
    ap.add_argument("--out", dest="dst", default="games/tennis/records/rally-out-of-reach.json")
    args = ap.parse_args(argv)
    record = json.loads(Path(args.src).read_text(encoding="utf-8"))
    out, notes = decide(record)
    Path(args.dst).parent.mkdir(parents=True, exist_ok=True)
    Path(args.dst).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    missed = [s for s in out["shots"] if (s.get("run") or {}).get("met") is False]
    print(f"{len(out['shots'])} shots kept of {len(record['shots'])}; {len(out['rallies'])} rallies; "
          f"{len(missed)} not reached")
    for line in notes:
        print(" ", line)
    print(f"  written: {args.dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
