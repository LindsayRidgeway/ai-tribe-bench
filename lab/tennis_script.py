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
SWAP_EVERY = 5    # points at one end before both players change ends, so neither is always the small one


def rating(balls: int) -> float:
    """The ladder the human asked for: the engine's own learning fraction, displayed on a 1.0-7.0 scale.

    Nothing is invented here. s is `Player.skill`'s curve; the rating is a monotone display of it, so the
    two can never disagree. Inverting it (rating -> balls) is `balls_for`.
    """
    return 1.0 + 6.0 * (1.0 - math.exp(-balls / 120.0))


def balls_for(r: float) -> float:
    s = max(1e-9, min(1 - 1e-9, (r - 1.0) / 6.0))
    return -120.0 * math.log(1.0 - s)


def corridor(p: T.Player, incoming, power: float, aim: float, contact, surface, wind,
             aim_x=None) -> tuple[float, float]:
    """The range of face angles that would have landed this swing in the court.

    Same contact point, same power, same aim, same hands-free delivery: the only thing that moves is the
    face. A beginner's window is twenty degrees; a practised player's is two and a half. That difference is
    the whole game, and it is invisible in a score.
    """
    lo = hi = None
    f = -14.0
    while f <= 46.0:
        shot = T.strike(p, incoming, face=f, power=power, aim=aim, aim_x=aim_x, shot="rally",
                        surface=surface, wind=wind, clean=True, contact=contact)
        ok, _ = T.verdict(shot)
        if ok:
            if lo is None:
                lo = f
            hi = f
        f += 0.5
    return (lo, hi) if lo is not None else (None, None)


def play(practice: tuple[int, int], names, rallies: int, ms: int, surface: str,
         swap_every: int = SWAP_EVERY) -> dict:
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
    # Where each player last aimed in this rally, so that a shot can avoid being the same shot again.
    last_aim = [None, None]
    out_rallies, shots = [], []
    incoming, hitter = None, 0
    # Which side of each player's body has been losing points, so that a ball sent to one corner and a ball sent
    # to the other can be told apart later. The engine's placement rule reads this when the corners are
    # equidistant; nothing else does.
    record = {pl.name: {"left": [0, 0], "right": [0, 0]} for pl in players}
    # The end each player began at. After a change of ends `pl.north` is no longer that, so it is kept here: the
    # players block and the page's opening positions read this, and every shot and run carries its own `north`.
    north0 = [pl.north for pl in players]

    for rally_no in range(1, rallies + 1):
        idxs, length = [], 0
        # Both players change ends every SWAP_EVERY points, so neither spends the whole film at the far baseline.
        # The founder, 2026-11-11: "even for rallies, it would be more interesting if half the time the male was
        # in the foreground, and half the time the female was... You don't want them changing after every point,
        # but maybe after ten points." Real matches change ends at the end of every odd game; practice has no
        # games, so the count is points here. Everything downstream already reads `pl.north` rather than assuming,
        # which is why this is a flip and not a refactor — the legs, the recovery spot, the serve corner, which
        # side of the body is the forehand, and which corner is "far" all follow.
        changed_ends = bool(rally_no > 1 and swap_every and (rally_no - 1) % swap_every == 0)
        if changed_ends:
            for pl in players:
                pl.north = not pl.north
            where = [(2.0 if pl.north else T.LENGTH - 2.0, T.WIDTH / 2) for pl in players]
            carry = [None, None]
        # Every point in tennis begins with a serve, and until 2026-11-11 this file began every point with a
        # groundstroke struck from the baseline — a rally with no opening ball, which is why a rally could be
        # one shot long. The server alternates for now; the game's own service order (a whole game, then the
        # other player) belongs to the scoring layer, and MATCH-FORMAT.md says so.
        server_i = (rally_no - 1) % 2
        hitter = server_i
        serve_no = 1          # first ball; a fault earns a second
        rallied = False
        server = players[server_i]
        # The corner is chosen once per point, at random, and both serves go there: a second serve is the same
        # intention with less pace, not a change of plan.
        serve_corner = rng.choice(T.serve_corners(server.north, server.skill("control")))
        # Who won it, recorded where the engine's own verdict is read rather than worked out again downstream:
        # a rally ends when a shot is out (the hitter loses it) or when the other player cannot reach a good one
        # (the hitter wins it). If it runs to the cap, nobody won it and the record says so.
        point = {"winner": None, "reason": "the rally ran to the cap without a result"}
        while length < CAP:
            p = players[hitter]
            other = players[1 - hitter]
            swing, plan = "rally", None          # set again below; a serve sets swing = "serve"
            serving = (hitter == server_i and serve_no <= 2 and not rallied)
            if serving:
                # A serve is struck from 8.8ft over the baseline, not at waist height, and it is judged by the
                # service box rather than by the court. A second serve keeps the corner and takes pace off and
                # height on: the ball is sent four feet shorter, which is what a higher, safer serve is.
                contact = T.contact_point(p, "serve")
                pace = (66.0 + 18.0 * rng.random()) * (1.0 if serve_no == 1 else 0.85)
                # A second serve is not the same ball with the pace taken off. It is aimed at the middle of the
                # same half of the box: the first serve attacks a corner because a fault costs nothing but a
                # serve, the second one cannot afford a corner at all. Until 2026-11-11 it kept the corner and
                # only lost 15% of its pace, and thirteen points in twenty-four were double faults at zero
                # practice — a beginner who cannot play a point cannot be watched playing one.
                target = (serve_corner if serve_no == 1
                          else (T.NET_X + (T.SERVICE_LINE - 6.0) * (1.0 if p.north else -1.0),
                                T.WIDTH / 2 + (5.5 if serve_corner[1] > T.WIDTH / 2 else -5.5)))
                face, pw = T.aim_at(p, target, "serve", surface, wv, power=pace, contact=contact)
                shot = T.strike(p, None, face=face, power=pw, aim=target[1], aim_x=target[0], shot="serve",
                                surface=surface, wind=wv, contact=contact)
                swing, plan = "serve", {"kind": "serve"}
                ok, why = T.serve_verdict(shot)
            else:
                contact = carry[hitter] or T.contact_point(p, "rally")
                # Where the ball is going: the far corner the other player is furthest from, not the middle of
                # the court. Until 2026-11-11 every shot in this file was aimed at T.WIDTH/2 and NET_X plus or
                # minus twenty, which is why the renderer showed two people trading balls down the centre.
                # A ball, not a corner: which shot, to where, how hard. The corner rule is the default drive and
                # it is still the founder's; the other four kinds are what stop twenty shots alternating left and
                # right like a metronome (his note, 2026-11-11).
                plan = T.choose_shot(p, other, where[hitter], where[1 - hitter], record, rng,
                                     last=last_aim[hitter])
                # At the net the ball is volleyed — taken out of the air before it bounces, at whatever height it
                # happens to be at, which is the reason a player comes to the net at all. Whether this ball is
                # one of those is decided when it is struck at this player, not here: see the receiving block
                # below, which is where the racquet's reach and the flight time are both known.
                swing = "volley" if (incoming and incoming.get("volley")) else "rally"
                if swing == "volley":
                    plan = T.choose_shot(p, other, where[hitter], where[1 - hitter], record, rng,
                                         height=contact[2], last=last_aim[hitter])
                target = plan["target"]
                face, pw = T.aim_at(p, target, "rally", surface, wv, power=plan["power"], contact=contact)
                shot = T.strike(p, incoming, face=face, power=pw, aim=target[1], aim_x=target[0], shot=swing,
                                surface=surface, wind=wv, contact=contact)
                ok, why = T.verdict(shot)
            if plan is not None:
                last_aim[hitter] = (target[0], target[1])
            aim = target[1]
            traj = shot["traj"]
            tpath = T.flight(shot["contact"], shot["v0"], wv, surface, cl=shot["spin"], trace=TRACE)["path"]
            # The engine's own traj carries no samples (it did not ask for a trace), so the volley lookup had an
            # empty list to search and never found a ball in the air. The traced path goes back onto the traj here.
            traj["path"] = tpath
            lo, hi = corridor(p, incoming, shot["power"], aim, shot["contact"], surface, wv, aim_x=target[0])

            length += 1
            entry = {
                "n": len(shots),
                "rally": rally_no,
                "i": length,
                "player": p.name,
                "north": p.north,
                "kind": "serve" if serving else "rally",
                "ball": "serve" if serving else plan["kind"],
                "swing": "serve" if serving else swing,
                "rush": round(float(shot.get("rush", 0.0)), 3) if not serving else 0.0,
                # Which side of the body the ball is on, and therefore which stroke it is. A right-hander's
                # forehand is struck on their right-hand side of the court and their backhand on their left;
                # until 2026-11-11 the record did not say, so the renderer solved the right arm at every ball
                # and a player hit a forehand from their backhand corner with the racquet on the wrong side of
                # their body. The founder saw it: "when the player hits a ball from their back-hand side, they
                # need to use a backhand stroke."
                "hand": ("fore" if T.side_of(shot["contact"][1], p.north) == "right" else "back")
                        if not serving else "fore",
                "face": round(shot["face"], 2),
                "power": round(shot["power"], 1),
                "aim": round(aim, 1),
                "target": [round(target[0], 1), round(target[1], 1)],
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
                if serving:
                    if serve_no == 1:
                        serve_no = 2        # a fault is not a lost point: the server has a second ball
                        continue
                    point = {"winner": other.name, "reason": f"double fault — {why}"}
                    break
                point = {"winner": players[1 - hitter].name, "reason": why}
                break
            if serving:
                rallied = True
            # Recovery. The player who has just hit does not stay where the ball was: they go back behind the
            # baseline to the centre, or forward to the net if the shot was an approach or a volley. Their `where`
            # becomes that spot, so the ball the other player hits next is aimed at a receiver standing where a
            # receiver actually stands. Before this the feet stayed at the contact point for the rest of the rally,
            # which is why both players drifted forward and stayed in the forecourt.
            came_in = (plan is not None and plan["kind"] == "approach") or swing == "volley"
            spot = T.recovery_spot(p, (shot["contact"][0], shot["contact"][1]), came_in)
            spd = T.movement_speed(p)
            d_rec = math.hypot(spot[0] - shot["contact"][0], spot[1] - shot["contact"][1])
            # A recovery is not bounded by the flight of the ball just struck: the player keeps moving while the
            # other one is hitting, which is most of the two seconds. Capped at 2.5s, which is a long time to jog
            # twenty feet and is where a real player would have arrived.
            t_rec = min(2.5, d_rec / max(spd, 1.0))
            ux = (spot[0] - shot["contact"][0]) / max(d_rec, 1e-6)
            uy = (spot[1] - shot["contact"][1]) / max(d_rec, 1e-6)
            where[hitter] = (shot["contact"][0] + ux * spd * t_rec, shot["contact"][1] + uy * spd * t_rec)
            carry[hitter] = None
            entry["recover"] = {"player": p.name, "north": p.north,
                                "from": [round(shot["contact"][0], 2), round(shot["contact"][1], 2)],
                                "to": [round(where[hitter][0], 2), round(where[hitter][1], 2)],
                                "t0": 0.0, "t1": round(t_rec, 3), "dist": round(d_rec, 1),
                                # `in_time` is not "they got back" — they always get back inside the 2.5s cap at
                                # this level; it is "they were back in the middle before the ball they had just
                                # hit had landed", which is the harder and more interesting of the two claims.
                                "speed": round(spd, 1), "in_time": bool(d_rec <= spd * traj["time"])}

            # ---- the ball arrives at the other player ------------------------------------------------
            # A volley is not decided when the net player's turn comes round two shots later: it is decided
            # here, while the ball is in the air at them, because that is the only moment at which the racquet's
            # reach and the flight time are both known. Deciding it later is why no volley ever fired: the
            # receiving check ran first, found that the net player could not get back to the landing point, and
            # ended the point — while the whole reason they were standing there was to take it before it landed.
            receiver_at = where[1 - hitter]
            vol = (T.volley_contact(other, traj, receiver_at)
                   if abs(receiver_at[0] - T.NET_X) < T.VOLLEY_ZONE else None)
            if vol is not None:
                entry["run"] = {
                    "player": other.name, "north": other.north,
                    "from": [round(v, 2) for v in receiver_at],
                    "to": [round(v, 2) for v in vol["feet"]],
                    "t0": 0.0, "t1": round(vol["t"], 3),
                    "dist": vol["step"], "speed": round(T.movement_speed(other), 1),
                    "met": True, "volley": True,
                }
                where[1 - hitter] = vol["feet"]
                carry[1 - hitter] = (vol["contact"][0], vol["contact"][1], vol["contact"][2])
                # The height the ball is at is the fact the next shot is chosen from.
                incoming = {"speed_in": traj["speed_in"], "traj": traj, "volley": True,
                            "height": round(vol["contact"][2], 2),
                            "rush": other.rush(vol["step"] / max(T.movement_speed(other), 1.0), vol["t"])}
                hitter = 1 - hitter
                continue

            meet = T.intercept(other, traj["land"], traj["time"], traj["bounce"], surface,
                               frm=receiver_at)
            available = traj["time"] + 1.0
            # A beaten player runs as far as the time allowed and arrives late; the picture shows them short,
            # which is what "beaten by the wide ball" looks like. Nobody is teleported to a contact.
            reachable_dist = min(meet["distance"], meet["speed"] * available)
            ux = (traj["land"][0] - receiver_at[0]) / max(meet["distance"], 1e-6)
            uy = (traj["land"][1] - receiver_at[1]) / max(meet["distance"], 1e-6)
            got_to = (receiver_at[0] + ux * reachable_dist, receiver_at[1] + uy * reachable_dist)
            entry["run"] = {
                "player": other.name, "north": other.north,
                "from": [round(v, 2) for v in receiver_at],
                "to": [round(v, 2) for v in (meet["meet"] if meet["ok"] else got_to)],
                "t0": 0.0, "t1": round(traj["time"] + meet["t_meet"], 3),
                "dist": round(meet["distance"], 1), "speed": round(meet["speed"], 1),
                "met": bool(meet["ok"]),
            }
            where[1 - hitter] = entry["run"]["to"] if meet["ok"] else got_to
            # The ball is met where it LANDS, and the feet stop a racquet's length short of it — which is what
            # `meet` already was, and what this line got wrong: it put the contact point on the player's own feet,
            # so every stroke in the game was struck with the body standing in the ball. The arm then folds to
            # almost nothing (0.9ft from shoulder to ball, measured) and no amount of arm solving makes that look
            # like a stroke. A ball is struck two to three feet from the middle of the body, with the racquet
            # carrying it out to where it actually is.
            carry[1 - hitter] = (traj["land"][0] if meet["ok"] else entry["run"]["to"][0],
                                 traj["land"][1] if meet["ok"] else entry["run"]["to"][1],
                                 T.contact_point(other, "rally")[2])
            if not meet["ok"]:
                entry["why"] += f" — {other.name} {meet['why']}"
                point = {"winner": p.name, "reason": f"{other.name} did not reach it — {meet['why']}"}
                break
            # How much time the other player had to get the racquet back for it. The run is the time their legs
            # need for the ground they have to cover; the flight is the ball's own; whether those two overlap is
            # the habit in question (Player.rush).
            run_time = min(traj["time"], entry["run"]["dist"] / max(entry["run"]["speed"], 1.0))
            incoming = {"speed_in": traj["speed_in"], "traj": traj, "rush": other.rush(run_time, traj["time"])}
            hitter = 1 - hitter

        # Credit the point to the corner it was aimed at, if the last ball is the one that decided it.
        if idxs:
            last = shots[idxs[-1]]
            tgt = last.get("target")
            if tgt:
                side = T.side_of(tgt[1], not last["north"])
                who = players[0].name if last["player"] == players[1].name else players[1].name
                record[who][side][1] += 1
                if point["winner"] == last["player"]:
                    record[who][side][0] += 1
        out_rallies.append({"rally": rally_no, "shots": idxs, "length": length,
                            "point": point, "clock_ms": ms,
                            "ends": {pl.name: pl.north for pl in players},
                            "changed_ends": changed_ends})
        incoming = None
        hitter = 0
        where = [(2.0 if pl.north else T.LENGTH - 2.0, T.WIDTH / 2) for pl in players]
        carry = [None, None]
        last_aim = [None, None]

    return {
        "generated": "lab/tennis_script.py — every number below came out of lab/tennis.py",
        "clock_ms": ms,
        "surface": surface,
        "wind": {"direction": wind_in[0], "mph": wind_in[1], "vector": [round(v, 2) for v in wv]},
        "court": {"length": T.LENGTH, "width": T.WIDTH, "net_x": T.NET_X,
                  "service_line": T.SERVICE_LINE if hasattr(T, "SERVICE_LINE") else 21.0,
                  "net_centre": T.NET_CENTRE, "net_posts": T.NET_POSTS},
        "players": [{"name": pl.name, "north": north0[i], "balls": practice[i],
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
    ap.add_argument("--swap-every", type=int, default=SWAP_EVERY,
                    help="points at one end before both players change ends (0 never)")
    ap.add_argument("--clock", type=int, default=1793809110303)
    ap.add_argument("--out", default=None, help="write the flat 2D page here")
    ap.add_argument("--out3d", default=None, help="write the 3D page here (needs a local server)")
    ap.add_argument("--json", default=None, help="write the raw script here too")
    a = ap.parse_args(argv)

    practice = tuple(int(x) for x in a.practice.split(","))
    names = tuple(a.names.split(","))
    data = play(practice, names, a.rallies, a.clock, a.surface, a.swap_every)

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
