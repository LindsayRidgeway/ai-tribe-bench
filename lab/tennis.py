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
import json
import math
import os
import random
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from rps import BASES, DEFAULT_MODEL, ask          # noqa: E402  one vendor table, not two

# ---- court, in feet -------------------------------------------------------------------------------
LENGTH, WIDTH = 78.0, 27.0
NET_X = LENGTH / 2
SERVICE_LINE = 21.0                      # from the net, both sides
NET_CENTRE, NET_POSTS = 3.0, 3.5
G = 32.17
MPH = 1.46667                            # mph to feet per second. 0.44704 is mph to metres per second; the
                                         # first version used it directly and every shot flew at a third of
                                         # its stated speed. Found 2026-11-04 by asking where 70mph lands.
# Quadratic drag, a = DRAG * |v_rel| * v_rel. DRAG = 0.5 * rho * Cd * A / m in feet:
#   0.5 * 0.002377 slugs/ft3 * 0.55 * 0.038 ft2 / 0.00392 slugs = 0.0063 per foot.
# A tennis ball really does lose about a quarter of its speed crossing the court; at 0.00055 (eleven times
# too small) it lost almost nothing, which is why the old engine could not tell a serve from a lob.
DRAG = 0.0063
BALL_MASS_SLUGS, BALL_AREA_FT2, CD, RHO = 0.00392, 0.038, 0.55, 0.002377
# Magnus lift, a = LIFT * Cl * |v|^2, with LIFT = 0.5 * rho * A / m = 0.0115 per foot. Cl is the lift
# coefficient set by the spin: a heavy topspin ball runs Cl about 0.2-0.3 and is pulled down hard, which is
# the only reason a 70mph forehand at 12 degrees of elevation stays in the court at all. Without this term the
# first correct-units version sent every rally ball twenty feet past the baseline, and the honest conclusion
# was not "lower the angles" but "the model is missing the thing that makes tennis tennis".
LIFT = 0.5 * RHO * BALL_AREA_FT2 / BALL_MASS_SLUGS

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
    """The air's own velocity in ft/s, x along the court (N->S is +x), y across (W->E is +y).

    Wind is not an extra push added to gravity: it is the air the ball is moving through, so it enters the
    drag term as a velocity. A headwind raises the relative speed and slows the ball more; a tailwind lowers
    it; a crosswind bends the flight sideways. The old version added 0.0016*v^2 as a bare acceleration, which
    at 15mph came to 0.07 ft/s2 — a number that could not be felt, printed on every line as if it could."""
    ang = math.radians(45 * COMPASS.index(direction))
    v = speed_mph * MPH
    return (v * math.cos(ang), v * math.sin(ang))


# ---- the ball -------------------------------------------------------------------------------------
def flight(p0, v0, wind, surface, net_check=True, cl=0.0):
    """Integrate one shot. Returns where it crossed the net, where it first landed, and the ball at that
    moment. No closed form: drag makes it a numeric problem, and doing it numerically is the honest way.

    Wind is the air's velocity, so drag acts on the ball's velocity *relative to the air*.
    `cl` is the lift coefficient from the spin: positive is topspin and pulls the ball down, negative is
    slice and holds it up. The lift is applied on the vertical axis rather than truly perpendicular to the
    flight; for a ball that is broadly travelling forward that is a good approximation, and for a lob it is
    not — stated here rather than left for a reader to find."""
    x, y, z = p0
    vx, vy, vz = v0
    wx, wy = wind
    dt, t = 0.001, 0.0
    net = None
    while t < 6.0:
        rx, ry, rz = vx - wx, vy - wy, vz
        rel = math.sqrt(rx * rx + ry * ry + rz * rz)
        speed2 = vx * vx + vy * vy + vz * vz
        ax = -DRAG * rel * rx
        ay = -DRAG * rel * ry
        az = -DRAG * rel * rz - G - LIFT * cl * speed2
        nx, ny, nz = x + vx * dt, y + vy * dt, z + vz * dt
        nvx, nvy, nvz = vx + ax * dt, vy + ay * dt, vz + az * dt
        if net_check and net is None and (x - NET_X) * (nx - NET_X) <= 0 and x != nx:
            f = (NET_X - x) / (nx - x)
            net = (y + f * (ny - y), z + f * (nz - z))
            if net[1] < net_height(net[0]):
                return {"net": net, "land": None,
                        "speed_at_net": math.sqrt(vx * vx + vy * vy + vz * vz)}
        if nz <= 0:                                       # first bounce on the court plane
            f = z / (z - nz) if z != nz else 1.0
            land = (x + f * (nx - x), y + f * (ny - y))
            vx2, vy2, vz2 = vx + f * (nvx - vx), vy + f * (nvy - vy), vz + f * (nvz - vz)
            s = SURFACES[surface]
            after = (vx2 * s["f"], vy2 * s["f"], -vz2 * s["e"])
            return {"net": net, "land": land,
                    "speed_in": math.sqrt(vx2 * vx2 + vy2 * vy2 + vz2 * vz2),
                    "bounce": {"speed_out": math.sqrt(sum(c * c for c in after)),
                               "v": after, "angle": math.degrees(math.atan2(after[2], math.hypot(*after[:2])))}}
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
    """Left/right from the hitter's own point of view, plus the corner if it is one.

    A player standing at the north end faces south, and facing south puts east on their left: north-south
    pairs are reversed, east-west are not. The first version had this backwards for both seats, so every
    reported shot put the ball on the wrong side of the court."""
    left = (y > WIDTH / 2) if hitter_north else (y < WIDTH / 2)
    side = "left" if left else "right"
    if abs(y - WIDTH / 2) < WIDTH / 6:
        return "centre"
    return f"{side} corner" if abs(y - WIDTH / 2) > WIDTH / 2 - 5 else side


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
                "sweet": 0.72 + 0.26 * learned,
                "reach": 0.35 + 0.60 * learned}[attr]


def contact_point(p: Player, shot: str = "rally") -> tuple[float, float, float]:
    """Where the racquet meets the ball. A serve is struck high from just behind the baseline; a groundstroke
    is struck at waist height, roughly 3ft, from behind the baseline; a volley is struck at chest height and
    well inside the court. The first version returned 8.6ft for everything, so every groundstroke was secretly
    a serve and every rally ball flew over the net without ever being asked to clear it."""
    base = 2.0 if p.north else LENGTH - 2.0
    back = base
    if shot == "serve":
        height = 8.8
    elif shot == "volley":
        height = 4.5
        back = base + (8.0 if p.north else -8.0)
    else:
        height = 3.0 + p.rng.uniform(-0.7, 0.7)
    return (back, WIDTH / 2 + p.rng.uniform(-5, 5), height)


def elevation_for(shot: str, face: float) -> float:
    """Ball elevation off the strings, in degrees.

    The face angle alone does not decide the launch: the *swing path* does most of it. A groundstroke is hit
    from low to high, so a square face already sends the ball up about 4 degrees; opening the face adds to it
    and closing it flattens the shot. A serve is struck downward from 8.8ft, so a square face sends it at the
    ground and the face must be opened to lift it. These constants were calibrated against known shots and
    against the in-play map (see test_surface_and_face_band), not chosen to look plausible."""
    base = {"serve": 2.0, "volley": 10.0}.get(shot, 4.0)
    return max(-12.0, min(50.0, base + face * 0.9))


def spin_for(face: float) -> float:
    """Lift coefficient from the face angle. A closed face, swung up through the ball, brushes up its back
    and makes topspin (positive, pulled down); an open face cuts under it and makes slice (negative, floats).
    This is the trade the player has to learn: closing the face both lowers the launch and holds the ball in,
    so the closed face is not simply the safe one and the open face is not simply the reckless one."""
    return max(-0.12, min(0.24, 0.10 - 0.020 * face))


def strike(p: Player, incoming: dict | None, face: float, power: float, aim: float,
           shot: str, surface: str, wind: tuple[float, float], clean: bool = False) -> dict:
    """Movement in, ball out. The player supplies a face angle in degrees (negative closed), a power in
    per-cent and an aim offset in feet; everything else is physics plus the player's skill."""
    control = p.skill("control")
    pace_in = (incoming or {}).get("speed_in", 40.0)          # mph
    # a fast ball gives less time to set up, so the same player is less accurate returning it
    control *= 1 - 0.22 * min(1.0, pace_in / 100.0)

    if not clean:
        p.shots += 1
    sweet = True if clean else p.rng.random() < p.skill("sweet")
    # The hands are not exact. 4 degrees of face error at the start, a third of a degree once a few hundred
    # balls have been hit; the first version used 7.5, which was wider than the whole window between 'net' and
    # 'long' at rally pace, so a beginner's results were pure noise and no amount of reading them helped.
    face_actual = face if clean else (
        face + p.rng.gauss(0, 4.0 * (1 - control)) * (1 if p.rng.random() < 0.5 else -1))
    power_actual = power if clean else power * (1 + p.rng.gauss(0, 0.12 * (1 - control)))
    if not sweet:                                     # the frame, not the strings
        power_actual *= p.rng.uniform(0.5, 0.75)
        face_actual += p.rng.gauss(0, 8)

    elevation = math.radians(elevation_for(shot, face_actual))
    # 100% of swing sends the ball at 105mph, a hard forehand; 30% is a 32mph push. The first version used
    # 1.32mph per point, so 100% meant 132mph and every number on the page was a fiction.
    speed = max(8.0, power_actual * 1.05)
    p0 = contact_point(p, shot)
    # the player turns to aim; the face angle sets the loft, not the direction. A first version made the
    # face angle steer as well, and a serve aimed at the right box landed thirty feet wide. Aim is absolute
    # across the court (feet from the west sideline), not relative to the ball, because a serve struck four
    # feet off centre otherwise lands four feet off target.
    azimuth = math.atan2(aim - p0[1], 32.0)
    v = speed * MPH
    vx = v * math.cos(elevation) * math.cos(azimuth) * (1 if p.north else -1)
    vy = v * math.cos(elevation) * math.sin(azimuth)
    vz = v * math.sin(elevation)
    traj = flight(p0, (vx, vy, vz), wind, surface, cl=spin_for(face_actual))
    return {"player": p, "shot": shot, "speed": speed, "sweet": sweet, "contact": p0,
            "traj": traj, "face": face_actual, "power": power_actual,
            "spin": spin_for(face_actual)}


def aim_at(p: Player, target, shot: str, surface: str, wind, power: float) -> tuple[float, float]:
    """The player's intent, translated into movement: what face angle and power send the ball to that spot.
    This is what a competent player does by feel and a beginner cannot do at all — so the *error* is applied
    afterwards, by `strike`, from the player's control."""
    lo, hi = -20.0, 40.0
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
    hitter_left = (shot["contact"][1] > WIDTH / 2) if p.north else (shot["contact"][1] < WIDTH / 2)
    origin = f"from the {'left' if hitter_left else 'right'} side of the baseline" \
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
    left = y > WIDTH / 2 if server_north else y < WIDTH / 2
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
    incoming["speed_in"] = t["bounce"]["speed_out"] / MPH
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
        incoming["speed_in"] = t["bounce"]["speed_out"] / MPH
        server, receiver = receiver, server
    lines.append("the rally runs out of the record's twelve shots.")
    return lines


# ---- early spring: a drill, no serving, no scoring ------------------------------------------------
# [+-]? not -?: a being asked for a signed angle writes "+6" about as often as "6", and the first pattern
# silently rejected every such line and fed the ball straight instead of playing what the player asked for.
COMMAND = re.compile(r"FACE\s*[:=]?\s*([-+]?\d+(?:\.\d+)?).*?POWER\s*[:=]?\s*([-+]?\d+(?:\.\d+)?)"
                     r".*?AIM\s*[:=]?\s*([-+]?\d+(?:\.\d+)?)", re.I | re.S)


def parse_command(text: str) -> tuple[float, float, float] | None:
    m = COMMAND.search(text or "")
    if not m:
        return None
    face, power, aim = (float(x) for x in m.groups())
    return max(-20.0, min(40.0, face)), max(30.0, min(100.0, power)), max(0.0, min(WIDTH, aim))


def verdict(shot: dict) -> tuple[bool, str]:
    """In play or not, and a phrase a player can learn from.

    The critical property is that an *out* ball must say how far out and in which direction, because a player
    learns by correcting a number, not by being told 'out'. The first version reported 'long, out of the court'
    with no distance, which is unlearnable: every long ball looks identical whether it missed by one foot or
    thirty, so bisection on the answer was impossible. There is no scoring here; the drill's only score is how
    many balls in a row stay in."""
    t = shot["traj"]
    p = shot["player"]
    fwd = 1 if p.north else -1
    if t.get("land") is None:
        if t.get("net"):
            return False, f"into the net at {t['net'][1]:.1f}ft — needs more height"
        return False, "lost the ball"
    x, y = t["land"]
    depth = (x - NET_X) * fwd                    # feet past the net, along the shot
    lat = y - WIDTH / 2
    side = "" if abs(lat) < 0.5 else (f", {abs(lat):.0f}ft {'east' if lat > 0 else 'west'} of centre")
    if depth <= 0:
        return False, f"short of the net by {abs(depth):.0f}ft{side} — needs more height"
    if depth > NET_X:                            # past the far baseline
        over = depth - NET_X
        how = "less than a foot" if over < 1 else f"{over:.0f}ft"
        return False, f"long by {how}{side} — too much height or too much pace"
    if not (0 <= y <= WIDTH):
        return False, (f"wide by {abs(lat) - WIDTH / 2:.0f}ft — the court is 27ft wide, "
                       f"aim between 4 and 23")
    return True, (f"IN, {depth:.0f}ft past the net, {abs(lat):.0f}ft {'east' if lat > 0 else 'west'} of centre, "
                  f"arrives at {t['speed_in'] / MPH:.0f}mph and comes up at "
                  f"{t['bounce']['speed_out'] / MPH:.0f}mph")


def drill_prompt(p: Player, other: str, history: list[str], incoming: dict | None,
                 surface: str, wind_in: tuple[str, float]) -> str:
    inc = ("The ball is in your hands: this is a feed, not a return." if incoming is None else
           f"The ball is coming to you: {other}'s last shot landed {incoming.get('depth', 0):.0f}ft past the "
           f"net and is coming up at {incoming.get('speed_in', 0):.0f}mph.")
    lines = [f"You are {p.name}, on a {surface} court ({SURFACES[surface]['note']}). "
             f"Wind {wind_in[0]} at {wind_in[1]:.0f}mph.",
             inc, "",
             f"The court is 78ft long and {WIDTH:.0f}ft wide, the net is 3ft high at its middle, and you are "
             f"striking the ball from about 3ft up, 2ft behind your own baseline. For the ball to be good it "
             f"must clear the net by a little and land between the net and the far baseline.",
             "",
             "Your recent shots, oldest first (what you chose, whether you hit the strings or the frame, and "
             "what happened):"]
    lines += [f"  {h}" for h in history[-8:]] or ["  (nothing yet — this is your first ball)"]
    lines += ["",
              "Give one line, exactly this shape and nothing else:",
              "FACE <degrees, -20 to 40>  POWER <30 to 100>  AIM <feet from the west sideline, 0 to 27>",
              "",
              "FACE is the angle of the racquet face. Opening it (positive) launches the ball higher and, "
              "because the strings go under the ball, makes slice that floats further. Closing it (negative) "
              "launches lower and brushes topspin, which pulls the ball down and lets you hit harder for the "
              "same length. POWER is swing speed: 30 is a push, 100 is a hard hit. AIM is where you mean to "
              "land it across the court; 13 is the middle, 4 and 23 are near the sidelines.",
              "",
              "You cannot see the shot before you hit it, and your hands are not exact: the angle you get is "
              "not quite the angle you chose, especially on a ball that is coming at you fast. Read your own "
              "history, decide what to change, and put the ball in."]
    return "\n".join(lines)


def run_drill(args) -> int:
    names = [n.strip() for n in args.names.split(",")]
    vendors = [v.strip().lower() for v in args.vendor.split(",")]
    practice = [int(x) for x in args.practice.split(",")]
    models = ([m.strip() for m in args.model.split(",")] if args.model
              else [DEFAULT_MODEL[v] for v in vendors])
    keys = []
    for v, n in zip(vendors, names):
        k = os.environ.get(f"TRIBE_API_KEY_{v.upper()}")
        if not k:
            print(f"   TRIBE_API_KEY_{v.upper()} is not set, so {n} cannot hit a ball. Nothing was played.",
                  file=sys.stderr)
            return 2
        keys.append(k)

    ms = int(time.time() * 1000)
    surface = args.surface or surface_at(ms)
    wind_in = wind_at(ms)
    wv = wind_vector(*wind_in)
    rng = random.Random(ms)
    players = [Player(names[0], True, practice[0], rng=rng),
               Player(names[1], False, practice[1], rng=rng)]
    print(f"# early spring — {surface} ({SURFACES[surface]['note']}), wind {wind_in[0]} {wind_in[1]:.0f}mph, "
          f"{args.shots} balls, no serving, no scoring, clock {ms}\n")
    for p in players:
        print(f"  {p.name}: {p.practice} balls hit before today, control {p.skill('control'):.2f}, "
              f"hands give or take ±{4.0 * (1 - p.skill('control')):.0f} degrees of face")
    print()

    history: dict[str, list[str]] = {p.name: [] for p in players}
    results: dict[str, list[bool]] = {p.name: [] for p in players}
    incoming, hitter, rally, best = None, 0, 0, 0
    fell_back = 0
    for i in range(1, args.shots + 1):
        p = players[hitter]
        other = players[1 - hitter].name
        prompt = drill_prompt(p, other, history[p.name], incoming, surface, wind_in)
        reply = ask(BASES[vendors[hitter]], keys[hitter], models[hitter], prompt, args.temperature)
        cmd = parse_command(reply)
        if cmd is None:
            fell_back += 1
            cmd = (0.0, 45.0, WIDTH / 2)
            print(f"  !! {p.name} wrote no usable line ({reply.strip()[:60]!r}); the feed is played straight.")
        face, power, aim = cmd
        shot = strike(p, incoming, face=face, power=power, aim=aim, shot="rally",
                      surface=surface, wind=wv)
        ok, outcome = verdict(shot)
        feel = "clean" if shot["sweet"] else "FRAMED"
        history[p.name].append(f"face {face:+.0f} power {power:.0f} aim {aim:.0f} [{feel}] -> {outcome}")
        results[p.name].append(ok)
        if ok:
            rally += 1
            best = max(best, rally)
            x, y = shot["traj"]["land"]
            incoming = dict(shot["traj"]["bounce"])
            incoming["speed_in"] = shot["traj"]["bounce"]["speed_out"] / MPH   # mph, as everyone below reads it
            incoming["depth"] = abs(x - NET_X)
        else:
            rally = 0
            incoming = None
        hitter = 1 - hitter              # they take turns: one hits, the other feeds next
        print(f"  {i:2d}. {p.name:8s} face {face:+.0f} power {power:3.0f} aim {aim:2.0f} "
              f"[{feel:6s}] -> {outcome}" + ("" if ok else "   [dead]"))

    print("\n## After the drill\n")
    for p in players:
        r = results[p.name]
        half = len(r) // 2
        early = sum(r[:half]) / max(1, half) * 100
        late = sum(r[half:]) / max(1, len(r) - half) * 100
        print(f"  {p.name}: {p.shots} shots, control {p.skill('control'):.2f}, "
              f"sweet spot {p.skill('sweet'):.2f}, reach {p.skill('reach'):.2f}")
        print(f"  {'':>{len(p.name)}}  in play {sum(r)}/{len(r)} = {sum(r) / max(1, len(r)) * 100:.0f}%"
              f"  |  first half {early:.0f}%  second half {late:.0f}%")
    print(f"\n  longest run of balls in play: {best}; unparsed replies: {fell_back}")
    return 0


def simulate(args, ms: int | None = None, quiet: bool = False) -> dict:
    """Two scripted learners on the same court: the test of whether the drill teaches anything at all.

    The point is not that these are good tennis players. It is that the *feedback* is sufficient. One player
    bisects on the face angle using only what `verdict` prints — 'long by 12ft', 'short of the net by 4ft' —
    which is exactly the information a being gets. The other hits the same shot every time and never reads
    anything. If the bisector cannot pull ahead of the unchanging player, the drill is unlearnable and no model
    run will fix it. This is the check to run before spending anyone's tokens."""
    ms = ms if ms is not None else int(time.time() * 1000)
    surface = args.surface or surface_at(ms)
    wind_in = wind_at(ms)
    wv = wind_vector(*wind_in)
    if not quiet:
        print(f"# simulate — {surface}, wind {wind_in[0]} {wind_in[1]:.0f}mph, {args.shots} balls each, "
              f"clock {ms}\n")

    class Bisector:
        """A player who only reads the printed miss and halves the interval. No model, no knowledge of the
        physics: if the ball is long it lowers the face, if it is short it raises it, and it narrows the gap
        between the lowest face that went long and the highest that went short."""

        def __init__(self, p, practice=0):
            self.p = Player(p, True, practice, rng=random.Random(ms + practice))
            self.lo, self.hi = -14.0, 26.0
            self.power = 55.0
            self.chosen = 0.0                        # starts at a square face, which is not in play

        def choose(self):
            return self.chosen, self.power, WIDTH / 2

        def learn(self, face, outcome, ok):
            if ok:
                return                                  # good ball: change nothing
            if "long by" in outcome or "wide by" in outcome:
                self.hi = min(self.hi, face)
            elif "short of the net" in outcome or "into the net" in outcome:
                self.lo = max(self.lo, face)
            if self.hi - self.lo < 1.5:                  # it has bracketed the window; sit in the middle
                self.lo, self.hi = self.lo - 2.0, self.hi + 2.0
            self.chosen = (self.lo + self.hi) / 2

    class Stubborn:
        """The control: same shot every ball. This is what a player who does not read the results amounts to,
        and it is the floor the learner has to beat."""

        def __init__(self, p):
            self.p = p

        def choose(self):
            return 0.0, 55.0, WIDTH / 2

        def learn(self, face, outcome, ok):
            pass

    arms = {
        "reads results, new hands": (Bisector("Ada", practice=0), 0),
        "reads nothing, new": (Stubborn(Player("Bo", False, 0, rng=random.Random(ms))), 1),
        "reads results, 300 balls": (Bisector("Cy", practice=300), 0),
    }
    tally = {k: [] for k in arms}
    settled = {}
    for arm, (agent, north) in arms.items():
        agent.p.north = bool(north)
        for i in range(args.shots):
            face, power, aim = agent.choose()
            shot = strike(agent.p, None, face=face, power=power, aim=aim, shot="rally",
                          surface=surface, wind=wv)
            ok, outcome = verdict(shot)
            tally[arm].append(ok)
            agent.learn(face, outcome, ok)
        settled[arm] = getattr(agent, "chosen", 0.0)
    if not quiet:
        print("  arm                        in play      first half   second half   face it settled on")
        for arm, r in tally.items():
            h = len(r) // 2
            print(f"  {arm:26s} {sum(r):3d}/{len(r):<3d} {sum(r) / len(r) * 100:3.0f}%   "
                  f"{sum(r[:h]) / h * 100:4.0f}%        {sum(r[h:]) / (len(r) - h) * 100:4.0f}%        "
                  f"{settled[arm]:+.1f}")
    return {"tally": tally, "settled": settled, "surface": surface, "wind": wind_in}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="tennis: the player moves, the system computes the ball")
    ap.add_argument("--names", default="Colette,Remy")
    ap.add_argument("--practice", default="400,20", help="balls hit before today, one per player")
    ap.add_argument("--points", type=int, default=4)
    ap.add_argument("--surface", default=None, help="clay, hard or grass; default from the clock")
    ap.add_argument("--vendor", default=None, help="for --drill: their vendors, comma-separated")
    ap.add_argument("--model", default=None)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--shots", type=int, default=40, help="for --drill: balls to hit")
    ap.add_argument("--drill", action="store_true", help="early spring: rally practice, no serving, no scoring")
    ap.add_argument("--simulate", action="store_true",
                    help="two scripted learners, to test whether the drill's feedback is learnable at all")
    args = ap.parse_args(argv)
    if args.simulate:
        simulate(args)
        return 0
    if args.drill:
        return run_drill(args)

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
