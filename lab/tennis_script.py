#!/usr/bin/env python3
"""Write a play script: the per-shot record a renderer replays.

The point of this file is that nothing in it decides anything. Face, power, error, flight and outcome all
come from `tennis.py` — the same integration that has judged every recorded match. This file only asks it,
writes down what it said, and adds two things the text record never needed: the ball's path through the
air, and the corridor of face angles that would have kept each shot in the court.

    python3 lab/tennis_script.py --rallies 3 --practice 0,300 --out games/tennis/demo.html

`--demo` inlines the script into `games/tennis/replay.html` so the page opens from a file, with no server
and no network.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tennis as T  # noqa: E402

CAP = 60          # the record's ceiling on a rally, stated rather than hidden
TRACE = 0.02      # seconds between ball positions in the script


def rating(balls: int) -> float:
    """The ladder the human asked for: the engine's own learning fraction, displayed on a 1.0-7.0 scale.

    Nothing is invented here. s is `Player.skill`'s curve; the rating is a monotone display of it, so the
    two can never disagree. Inverting it (rating -> balls) is `balls_for`.
    """
    return 1.0 + 6.0 * (1.0 - math.exp(-balls / 120.0))


def balls_for(r: float) -> float:
    s = max(1e-9, min(1 - 1e-9, (r - 1.0) / 6.0))
    return -120.0 * math.log(1.0 - s)


def corridor(p: T.Player, incoming, power: float, aim: float, contact, surface, wind) -> tuple[float, float]:
    """The range of face angles that would have landed this swing in the court.

    Same contact point, same power, same aim, same hands-free delivery: the only thing that moves is the
    face. A beginner's window is twenty degrees; a practised player's is two and a half. That difference is
    the whole game, and it is invisible in a score.
    """
    lo = hi = None
    f = -14.0
    while f <= 46.0:
        shot = T.strike(p, incoming, face=f, power=power, aim=aim, shot="rally",
                        surface=surface, wind=wind, clean=True, contact=contact)
        ok, _ = T.verdict(shot)
        if ok:
            if lo is None:
                lo = f
            hi = f
        f += 0.5
    return (lo, hi) if lo is not None else (None, None)


def play(practice: tuple[int, int], names, rallies: int, ms: int, surface: str) -> dict:
    wind_in = T.wind_at(ms)
    wv = T.wind_vector(*wind_in)
    rng = random.Random(ms)
    players = [T.Player(names[0], True, practice[0], rng=rng),
               T.Player(names[1], False, practice[1], rng=rng)]
    power = [55.0, 55.0]
    # Where each player's feet are. A rally is played by people who have to run to the ball, and until
    # 2026-11-10 this file did not track that at all: every contact was struck from the middle of the baseline,
    # so the renderer had no choice but to slide two puppets along a trolley. The engine's own interception
    # logic already computed where a player meets the ball; it now says so instead of only saying yes or no.
    where = [(2.0 if pl.north else T.LENGTH - 2.0, T.WIDTH / 2) for pl in players]
    carry = [None, None]          # the meeting point each player has been left standing at
    out_rallies, shots = [], []
    incoming, hitter = None, 0

    for rally_no in range(1, rallies + 1):
        idxs, length = [], 0
        while length < CAP:
            p = players[hitter]
            contact = carry[hitter] or T.contact_point(p, "rally")
            depth = T.NET_X + 20.0 if p.north else T.NET_X - 20.0
            face, pw = T.aim_at(p, (depth, T.WIDTH / 2), "rally", surface, wv, power=power[hitter])
            aim = T.WIDTH / 2
            shot = T.strike(p, incoming, face=face, power=pw, aim=aim, shot="rally",
                            surface=surface, wind=wv, contact=contact)
            ok, why = T.verdict(shot)
            traj = shot["traj"]
            tpath = T.flight(shot["contact"], shot["v0"], wv, surface, cl=shot["spin"], trace=TRACE)["path"]
            lo, hi = corridor(p, incoming, shot["power"], aim, shot["contact"], surface, wv)

            length += 1
            entry = {
                "n": len(shots),
                "rally": rally_no,
                "i": length,
                "player": p.name,
                "north": p.north,
                "face": round(shot["face"], 2),
                "power": round(shot["power"], 1),
                "aim": round(aim, 1),
                "sweet": bool(shot["sweet"]),
                "contact": [round(v, 2) for v in shot["contact"]],
                "v0": [round(v, 3) for v in shot["v0"]],
                "cl": round(shot["spin"], 4),
                "in": ok,
                "why": why,
                "land": [round(v, 2) for v in traj["land"]] if traj.get("land") else None,
                "net": [round(v, 2) for v in traj["net"]] if traj.get("net") else None,
                "bounce_speed": round(traj["bounce"]["speed_out"], 1) if traj.get("bounce") else None,
                "path": [[round(a, 3), round(b, 3), round(c, 3)] for _t, a, b, c in tpath],
                "corridor": [lo, hi],
            }
            shots.append(entry)
            idxs.append(entry["n"])

            if not ok:
                break
            other = players[1 - hitter]
            meet = T.intercept(other, traj["land"], traj["time"], traj["bounce"], surface,
                               frm=where[1 - hitter])
            available = traj["time"] + 1.0
            # A beaten player runs as far as the time allowed and arrives late; the picture shows them short,
            # which is what "beaten by the wide ball" looks like. Nobody is teleported to a contact.
            reachable_dist = min(meet["distance"], meet["speed"] * available)
            ux = (traj["land"][0] - where[1 - hitter][0]) / max(meet["distance"], 1e-6)
            uy = (traj["land"][1] - where[1 - hitter][1]) / max(meet["distance"], 1e-6)
            got_to = (where[1 - hitter][0] + ux * reachable_dist, where[1 - hitter][1] + uy * reachable_dist)
            entry["run"] = {
                "player": other.name, "north": other.north,
                "from": [round(v, 2) for v in where[1 - hitter]],
                "to": [round(v, 2) for v in (meet["meet"] if meet["ok"] else got_to)],
                "t0": 0.0, "t1": round(traj["time"] + meet["t_meet"], 3),
                "dist": round(meet["distance"], 1), "speed": round(meet["speed"], 1),
                "met": bool(meet["ok"]),
            }
            where[1 - hitter] = entry["run"]["to"] if meet["ok"] else got_to
            carry[1 - hitter] = (entry["run"]["to"][0], entry["run"]["to"][1],
                                 T.contact_point(other, "rally")[2])
            if not meet["ok"]:
                entry["why"] += f" — {other.name} {meet['why']}"
                break
            incoming = {"speed_in": traj["speed_in"], "traj": traj}
            hitter = 1 - hitter

        out_rallies.append({"rally": rally_no, "shots": idxs, "length": length,
                            "clock_ms": ms})
        incoming = None
        hitter = 0
        where = [(2.0 if pl.north else T.LENGTH - 2.0, T.WIDTH / 2) for pl in players]
        carry = [None, None]

    return {
        "generated": "lab/tennis_script.py — every number below came out of lab/tennis.py",
        "clock_ms": ms,
        "surface": surface,
        "wind": {"direction": wind_in[0], "mph": wind_in[1], "vector": [round(v, 2) for v in wv]},
        "court": {"length": T.LENGTH, "width": T.WIDTH, "net_x": T.NET_X,
                  "service_line": T.SERVICE_LINE if hasattr(T, "SERVICE_LINE") else 21.0,
                  "net_centre": T.NET_CENTRE, "net_posts": T.NET_POSTS},
        "players": [{"name": pl.name, "north": pl.north, "balls": practice[i],
                     "rating": round(rating(practice[i]), 2),
                     "control": round(pl.skill("control"), 3),
                     "sweet": round(pl.skill("sweet"), 3),
                     "reach": round(pl.skill("reach"), 3),
                     "body": pl.name.lower()}
                    for i, pl in enumerate(players)],
        "start": [{"name": pl.name, "north": pl.north,
                   "at": [round(v, 2) for v in wh]} for pl, wh in zip(players, where)],
        "rallies": out_rallies,
        "shots": shots,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rallies", type=int, default=3)
    ap.add_argument("--practice", default="0,300", help="balls hit before today, one per player")
    ap.add_argument("--names", default="Dmitri,Gwen")
    ap.add_argument("--surface", default="clay")
    ap.add_argument("--clock", type=int, default=1793809110303)
    ap.add_argument("--out", default=None, help="write the flat 2D page here")
    ap.add_argument("--out3d", default=None, help="write the 3D page here (needs a local server)")
    ap.add_argument("--json", default=None, help="write the raw script here too")
    a = ap.parse_args(argv)

    practice = tuple(int(x) for x in a.practice.split(","))
    names = tuple(a.names.split(","))
    data = play(practice, names, a.rallies, a.clock, a.surface)

    if a.json:
        Path(a.json).write_text(json.dumps(data, indent=1))

    games = Path(__file__).resolve().parent.parent / "games" / "tennis"
    for flag, name, label in ((a.out, "replay.html", "2D"), (a.out3d, "replay3d.html", "3D")):
        if not flag:
            continue
        html = (games / name).read_text().replace("__SCRIPT__", json.dumps(data))
        Path(flag).write_text(html)
        print(f"wrote {flag} ({len(html) // 1024} KB, {label}, {len(data['shots'])} shots)")

    lens = [r["length"] for r in data["rallies"]]
    print(f"{len(data['shots'])} shots, rally lengths {lens}, rating "
          f"{data['players'][0]['rating']} vs {data['players'][1]['rating']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
