#!/usr/bin/env python3
"""Tennis: the player moves, the system computes the ball.

Lindsay's design, 2026-11-04. A court with a surface, a wind, and a player who controls only their own
movements — racquet face, swing speed, where they aim — while the engine computes the trajectory, the speed,
the bounce and the result, and reports each shot in one compact line.

Why this is the first game in the series whose skill is genuinely learned rather than declared: the player
never names an outcome. It names *movement*, and movement plus physics produces the outcome. Nothing in the
prompt tells a being that a face angle of +6 degrees at 78 mph clears the net on clay into the service box; it
has to find that out by hitting balls, exactly as a person does. A player that has hit four hundred balls has
found it; a player that has hit twenty is still hitting the tape.

Physics, all keyless and checkable:
  - feet and seconds, gravity 32.17 ft/s², quadratic drag (coefficient 0.00055 per foot);
  - launch from the racquet face: elevation and azimuth derived from the face angle, the swing's intent and
    the aim, and the speed from the swing power;
  - the net at x = 39 ft is 3.0 ft high in the centre and 3.5 ft at the posts, and the ball is checked against
    its height at the moment it crosses;
  - bounce: a surface's restitution decides how much height comes back, its friction how much pace survives
    (grass keeps pace and stays low, clay takes pace away and kicks up, hard is between them);
  - wind is an acceleration on the ball for the whole flight, drawn from the clock and reported with every shot.

Skill is per player and grows with shots taken: control (how close the delivered face and power are to the
intent), sweet spot (how often the ball meets the middle of the strings rather than the frame), and reach (how
far they can move to a ball). Incoming pace costs control, because a fast ball gives less time to set up.

    python3 lab/tennis.py --practice 400,20 --points 5        # an experienced player against a beginner
    python3 lab/tennis.py --practice 20,20 --points 5         # two beginners from the same spring
"""
from __future__ import annotations

import argparse
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

# ---- court, in feet -------------------------------------------------------------------------------
LENGTH, WIDTH = 78.0, 27.0
NET_X = LENGTH / 2
SERVICE_LINE = 21.0                      # from the net, both sides
NET_CENTRE, NET_POSTS = 3.0, 3.5
G = 32.17
DRAG = 0.00055

SURFACES = {                             # restitution (height) and friction (pace kept)
    "clay":  {"e": 0.78, "f": 0.72, "note": "high bounce, slow"},
    "hard":  {"e": 0.72, "f": 0.82, "note": "true bounce, medium"},
    "grass": {"e": 0.60, "f": 0.92, "note": "low bounce, fast"},
}
COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def surface_at(ms: int) -> str:
    return list(SURFACES)[ms % 3]


def wind_at(ms: int) -> tuple[str, float]:
    """Direction and speed in mph, from the clock. No seed anywhere: a different match is a different wind."""
    direction = COMPASS[(ms // 3) % 8]
    speed = 2 + (ms // 24) % 22          # 2-23 mph
    return direction, float(speed)


def wind_vector(direction: str, speed_mph: float) -> tuple[float, float]:
    """Acceleration on the ball in ft/s², x along the court (N->S is +x), y across (W->E is +y)."""
    ang = math.radians(45 * COMPASS.index(direction))
    ms = speed_mph * 0.44704
    return (0.0016 * ms * ms * math.cos(ang), 0.0016 * ms * ms * math.sin(ang))


# ---- the ball -------------------------------------------------------------------------------------
def flight(p0, v0, wind, surface, net_check=True):
    """Integrate one shot. Returns where it crossed the net, where it first landed, and the ball at that
    moment. No closed form: drag makes it a numeric problem, and doing it numerically is the honest way."""
    x, y, z = p0
    vx, vy, vz = v0
    dt, t = 0.002, 0.0
    net = None
    while t < 6.0:
        speed = math.sqrt(vx * vx + vy * vy + vz * vz)
        ax = -DRAG * speed * vx + wind[0]
        ay = -DRAG * speed * vy + wind[1]
        az = -DRAG * speed * vz - G
        nx, ny, nz = x + vx * dt, y + vy * dt, z + vz * dt
        nvx, nvy, nvz = vx + ax * dt, vy + ay * dt, vz + az * dt
        if net_check and net is None and (x - NET_X) * (nx - NET_X) <= 0 and x != nx:
            f = (NET_X - x) / (nx - x)
            net = (y + f * (ny - y), z + f * (nz - z))
            if net[1] < net_height(net[0]):
                return {"net": net, "land": None, "speed_at_net": speed}
        if nz <= 0:                                       # first bounce on the court plane
            f = z / (z - nz) if z != nz else 1.0
            land = (x + f * (nx - x), y + f * (ny - y))
            vx2, vy2, vz2 = vx + f * (nvx - vx), vy + f * (nvy - vy), vz + f * (nvz - vz)
            s = SURFACES[surface]
            bounce = {"speed_out": math.sqrt(vx2 * vx2 + vy2 * vy2 + vz2 * vz2),
                      "v": (vx2 * s["f"], vy2 * s["f"], -vz2 * s["e"])}
            return {"net": net, "land": land, "speed_in": speed, "bounce": bounce}
        x, y, z, vx, vy, vz = nx, ny, nz, nvx, nvy, nvz
        t += dt
    return {"net": net, "land": None, "lost": True}


def net_height(y: float) -> float:
    return NET_CENTRE + (NET_POSTS - NET_CENTRE) * abs(y - WIDTH / 2) / (WIDTH / 2)


# ---- naming what the page shows -------------------------------------------------------------------
def side_name(x: float, north: bool) -> str:
    return "north" if (x < NET_X) == north else "south"


def depth_name(x: float, hitter_north: bool) -> str:
    """'service court' or 'back court', from the hitter's point of view."""
    into_opponent = (x > NET_X) if hitter_north else (x < NET_X)
    if not into_opponent:
        return "own side"
    d = abs(x - NET_X)
    return "service court" if d <= SERVICE_LINE else "back court"


def lateral_name(y: float, hitter_north: bool) -> str:
    """Left/right from the hitter's point of view, plus the corner if it is one."""
    left = (y < WIDTH / 2) if hitter_north else (y > WIDTH / 2)
    side = "left" if left else "right"
    third = y < WIDTH / 3 if hitter_north else y > 2 * WIDTH / 3
    if third:
        return f"{side}"
    return f"{'centre' if abs(y - WIDTH / 2) < WIDTH / 6 else side}"


def describe_landing(land, hitter_north: bool, receiver: str) -> str:
    x, y = land
    depth = depth_name(x, hitter_north)
    if depth == "own side":
        return "their own side of the net"
    lat = lateral_name(y, hitter_north)
    if lat == "centre":
        return f"the middle of {receiver}'s {depth}"
    return f"the {lat} of {receiver}'s {depth}"


# ---- players --------------------------------------------------------------------------------------
@dataclass
class Player:
    name: str
    north: bool
    practice: int = 0                    # balls hit, ever
    shots: int = 0
    serves_in: int = 0
    serves: int = 0
    errors: int = 0
    winners: int = 0
    rng: random.Random = field(default_factory=lambda: random.Random())

    def skill(self, attr: str) -> float:
        """Three attributes, all asymptotic in balls hit. The first hundred balls are worth more than the
        next three hundred, which is what learning a motor skill looks like."""
        learned = 1 - math.exp(-(self.practice + self.shots) / 120.0)
        return {"control": 0.18 + 0.74 * learned,
                "sweet": 0.30 + 0.65 * learned,
                "reach": 0.35 + 0.60 * learned}[attr]


def contact_point(p: Player, incoming_land=None) -> tuple[float, float, float]:
    """Where the racquet meets the ball. A serve is struck high from the baseline; a groundstroke is struck
    around waist height at whatever depth the player has recovered to."""
    return (2.0 if p.north else LENGTH - 2.0, WIDTH / 2 + p.rng.uniform(-4, 4), 8.6)


def strike(p: Player, incoming: dict | None, face: float, power: float, aim: float,
           shot: str, surface: str, wind: tuple[float, float], clean: bool = False) -> dict:
    """Movement in, ball out. The player supplies a face angle in degrees (negative closed), a power in
    per-cent and an aim offset in feet; everything else is physics plus the player's skill."""
    control = p.skill("control")
    pace_in = (incoming or {}).get("speed_in", 40.0)
    # a fast ball gives less time to set up, so the same player is less accurate returning it
    control *= 1 - 0.22 * min(1.0, pace_in / 100.0)

    if not clean:
        p.shots += 1
    sweet = True if clean else p.rng.random() < p.skill("sweet")
    face_actual = face if clean else (
        face + p.rng.gauss(0, 7.5 * (1 - control)) * (1 if p.rng.random() < 0.5 else -1))
    power_actual = power if clean else power * (1 + p.rng.gauss(0, 0.14 * (1 - control)))
    if not sweet:                                     # the frame, not the strings
        power_actual *= p.rng.uniform(0.35, 0.55)
        face_actual += p.rng.gauss(0, 22)

    elevation = math.radians(max(-6.0, min(55.0, (6.0 if shot == "serve" else 11.0) + face_actual * 0.55)))
    speed = max(8.0, power_actual * 1.32)             # per-cent to mph
    p0 = contact_point(p, incoming)
    # the player turns to aim; the face angle sets the loft, not the direction. A first version made the
    # face angle steer as well, and a serve aimed at the right box landed thirty feet wide. Aim is absolute
    # across the court (feet from the west sideline), not relative to the ball, because a serve struck four
    # feet off centre otherwise lands four feet off target.
    azimuth = math.atan2(aim - p0[1], 32.0)
    vx = speed * 0.44704 * math.cos(elevation) * math.cos(azimuth) * (1 if p.north else -1)
    vy = speed * 0.44704 * math.cos(elevation) * math.sin(azimuth)
    vz = speed * 0.44704 * math.sin(elevation)
    traj = flight(p0, (vx, vy, vz), wind, surface)
    return {"player": p, "shot": shot, "speed": speed, "sweet": sweet, "contact": p0,
            "traj": traj, "face": face_actual, "power": power_actual}


def aim_at(p: Player, target, shot: str, surface: str, wind, power: float) -> tuple[float, float]:
    """The player's intent, translated into movement: what face angle and power send the ball to that spot.
    This is what a competent player does by feel and a beginner cannot do at all — so the *error* is applied
    afterwards, by `strike`, from the player's control."""
    lo, hi = -4.0, 40.0
    for _ in range(22):
        mid = (lo + hi) / 2
        probe = strike(p, None, face=mid, power=power, aim=target[1],
                       shot=shot, surface=surface, wind=wind, clean=True)
        land = probe["traj"].get("land")
        if land is None:
            lo = mid                       # still in the net: hit up more
            continue
        if abs(land[0] - target[0]) < 0.5:
            return mid, power
        if land[0] < target[0]:
            lo = mid                       # short: more elevation
        else:
            hi = mid
    return (lo + hi) / 2, power


def reachable(p: Player, land, surface: str, incoming_speed: float) -> bool:
    """Can the player get to it and set up? Distance from the middle of their baseline, discounted by pace."""
    px = 2.0 if p.north else LENGTH - 2.0
    # depth is mostly covered by stepping in; the lateral distance is what separates a good mover from a
    # beginner, which is why a wide serve is a weapon and a straight one is not
    lateral = abs(land[1] - WIDTH / 2)
    depth = max(0.0, abs(land[0] - px) - 20.0)
    d = math.hypot(lateral, depth)
    reach = 7.0 + 11.0 * p.skill("reach")
    return d <= reach + 6.0 * (1 - min(1.0, incoming_speed / 90.0))


# ---- the match ------------------------------------------------------------------------------------
def line_for(shot: dict, receiver: str, surface: str, wind: tuple[str, float]) -> str:
    p = shot["player"]
    t = shot["traj"]
    origin = f"from the {'left' if (p.north and shot['contact'][1] < WIDTH / 2) else 'right'} of the baseline" \
        if shot["shot"] == "serve" else ("from the baseline" if abs(shot['contact'][0] - (2 if p.north else LENGTH - 2)) < 6 else "from inside the court")
    direction = "N to S" if p.north else "S to N"
    if t.get("land") is None:
        if t.get("net"):
            return (f"{p.name} {'serves' if shot['shot'] == 'serve' else 'hits'} {direction}, ball speed "
                    f"{shot['speed']:.0f}mph, {origin} — into the net ({t['net'][1]:.1f}ft at the tape).")
        return f"{p.name} hits {direction}, ball speed {shot['speed']:.0f}mph — long and out."
    where = describe_landing(t["land"], p.north, receiver)
    kind = "serves" if shot["shot"] == "serve" else f"hits {shot['shot']}"
    return (f"{p.name} {kind} {direction}, ball speed {shot['speed']:.0f}mph, {origin} into {where}; "
            f"bounces out at {t['bounce']['speed_out']:.0f}mph on {surface}.")


def in_service_box(land, server_north: bool, side: str) -> bool:
    """In if it lands in the service box on the side the server aimed at, measured from the server's view.
    The diagonal rule is what this approximates: the server picks a side, the ball must land in that half."""
    x, y = land
    depth_ok = (NET_X < x <= NET_X + SERVICE_LINE) if server_north else (NET_X - SERVICE_LINE <= x < NET_X)
    left = y < WIDTH / 2 if server_north else y > WIDTH / 2
    return depth_ok and (left if side == "left" else not left) and 0 <= y <= WIDTH


def play_point(server: Player, receiver: Player, surface: str, wind_vec, wind_in, rng) -> list[str]:
    """One point, in the order it happened."""
    lines, side = [], 2.0 if server.north else LENGTH - 2.0
    aim_err = 7.0 * (1 - server.skill("control"))
    side = "left" if rng.random() < 0.5 else "right"
    target = (NET_X + 8 + rng.uniform(-3, 9), WIDTH * (0.25 if side == "left" else 0.75) + rng.gauss(0, aim_err))
    face, power = aim_at(server, target, "serve", surface, wind_vec, power=66 + 18 * rng.random())
    shot = strike(server, None, face=face, power=power, aim=target[1],
                  shot="serve", surface=surface, wind=wind_vec)
    server.serves += 1
    lines.append(line_for(shot, receiver.name, surface, wind_in))
    t = shot["traj"]
    if t.get("land") is None or not in_service_box(t["land"], server.north, side):
        server.errors += 1
        lines.append(f"fault — the point goes to {receiver.name}.")
        return lines
    server.serves_in += 1
    incoming = t["bounce"]
    incoming["speed_in"] = t["bounce"]["speed_out"]
    for _ in range(12):
        if not reachable(receiver, t["land"], surface, incoming["speed_in"]):
            lines.append(f"{receiver.name} cannot get to it — {server.name} takes the point.")
            server.winners += 1
            return lines
        kind = rng.choice(["forehand", "backhand", "backhand", "forehand"])
        depth = NET_X + rng.uniform(4, 34)
        wide = WIDTH * (0.2 if rng.random() < 0.5 else 0.8) + rng.gauss(0, 9 * (1 - receiver.skill("control")))
        face, power = aim_at(receiver, (depth, wide), kind, surface, wind_vec, power=rng.uniform(40, 72))
        shot = strike(receiver, incoming, face=face, power=power, aim=wide,
                      shot=kind, surface=surface, wind=wind_vec)
        lines.append(line_for(shot, server.name, surface, wind_in))
        t = shot["traj"]
        if t.get("land") is None or not (NET_X < t["land"][0] < LENGTH if receiver.north
                                         else 0 < t["land"][0] < NET_X):
            receiver.errors += 1
            lines.append(f"{receiver.name} loses the point.")
            server.winners += 1
            return lines
        incoming = t["bounce"]
        incoming["speed_in"] = t["bounce"]["speed_out"]
        server, receiver = receiver, server
    lines.append("the rally runs out of the record's twelve shots.")
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="tennis: the player moves, the system computes the ball")
    ap.add_argument("--names", default="Colette,Remy")
    ap.add_argument("--practice", default="400,20", help="balls hit before today, one per player")
    ap.add_argument("--points", type=int, default=4)
    ap.add_argument("--surface", default=None, help="clay, hard or grass; default from the clock")
    args = ap.parse_args(argv)

    names = [n.strip() for n in args.names.split(",")]
    practice = [int(x) for x in args.practice.split(",")]
    ms = int(time.time() * 1000)
    surface = args.surface or surface_at(ms)
    wind_in = wind_at(ms)
    wv = wind_vector(*wind_in)
    rng = random.Random(ms)                     # the clock, not a chosen seed
    players = [Player(names[0], True, practice[0], rng=rng),
               Player(names[1], False, practice[1], rng=rng)]

    print(f"# {players[0].name} and {players[1].name}, {surface} ({SURFACES[surface]['note']}), "
          f"wind {wind_in[0]} {wind_in[1]:.0f}mph, clock {ms}\n")
    for n, p in zip(names, practice):
        print(f"  {n}: {p} balls hit before today")
    print()
    for i in range(args.points):
        server, receiver = (players[0], players[1]) if i % 2 == 0 else (players[1], players[0])
        print(f"**Point {i + 1} — {server.name} serves.**")
        for line in play_point(server, receiver, surface, wv, wind_in, rng):
            print("  " + line)
        print()
    print("## After the session\n")
    for p in players:
        print(f"  {p.name}: {p.shots} shots today, {p.serves_in}/{p.serves} serves in, "
              f"{p.errors} errors, control {p.skill('control'):.2f} sweet-spot {p.skill('sweet'):.2f} "
              f"reach {p.skill('reach'):.2f}")
    print(f"\n  {surface}: restitution {SURFACES[surface]['e']}, friction {SURFACES[surface]['f']}. "
          f"The same swing lands shorter and sits up on clay, skids through on grass.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
