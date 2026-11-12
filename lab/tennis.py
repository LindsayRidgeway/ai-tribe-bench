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
from pathlib import Path

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from rps import BASES, DEFAULT_MODEL, ask, default_model, key_for, spread  # noqa: E402  one vendor table, not two

# ---- court, in feet -------------------------------------------------------------------------------
LENGTH, WIDTH = 78.0, 27.0
NET_X = LENGTH / 2
SERVICE_LINE = 21.0                      # from the net, both sides
RALLY_CAP = 60                           # a ceiling on the record, not a rule of the game: if a rally reaches
                                         # it the line says so, rather than the game quietly ending it
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
NET_ABSORBS = 0.08         # the fraction of its own speed a ball rebounds off the tape with
NET_DROP = 0.25            # and of its vertical speed, before gravity takes the rest
OUT_BOUNCES = 2            # bounces a ball that lands OUT is still allowed to make, for the picture
OUT_SECONDS = 1.5          # and how long the picture may watch it do that
AFTER_LAND = 1.4           # seconds of the arc a ball is given AFTER it bounces in, so the picture shows it rise
#                            (HIT_WINDOW_MAX is 1.2, so this is the whole of the window plus a frame or two)
VISIBLE_PAD = 22.0         # feet beyond each line that the court picture still shows, so a ball leaving frame
                           # is not followed into the dark and does not stretch the shot by walking there


def on_court(land) -> bool:
    """Inside the lines of the court. This is the test for `is the ball out`, which is all it is used for — the
    service box has its own, because a serve landing in the back court is a fault but is not out."""
    return 0.0 <= land[0] <= LENGTH and 0.0 <= land[1] <= WIDTH


def in_serve_court(land, server_north: bool) -> bool:
    """Inside the service court on the server's side, in depth and in width but without the half. A serve into
    the wrong box is a fault and stays one; this only decides whether the film should watch the ball bounce on."""
    x, y = land
    depth_ok = (NET_X < x <= NET_X + SERVICE_LINE) if server_north else (NET_X - SERVICE_LINE <= x < NET_X)
    return depth_ok and 0.0 <= y <= WIDTH


def in_view(pt) -> bool:
    """Whether the picture still has the ball: the court plane is drawn 22ft wider than the court on every side,
    and beyond that there is nothing but dark. A ball that has left is a ball the film should stop following."""
    return (-VISIBLE_PAD <= pt[0] <= LENGTH + VISIBLE_PAD
            and -VISIBLE_PAD <= pt[1] <= WIDTH + VISIBLE_PAD)


def in_far_court(land, hitter_north: bool) -> bool:
    """Inside the lines on the far side of the net from the hitter — the test for whether a groundstroke was
    good, and the one the rally itself uses. A ball that comes down on the hitter's own side is short of the net
    and lost, and is just as out as one beyond the baseline; the founder's "show it bouncing" applies to both,
    and the first version of this only tested the rectangle, so a ball dumped three feet short of the net was
    frozen at its bounce while a ball a foot long bounced away."""
    x_ok = (NET_X < land[0] <= LENGTH) if hitter_north else (0.0 <= land[0] < NET_X)
    return x_ok and 0.0 <= land[1] <= WIDTH


def flight(p0, v0, wind, surface, net_check=True, cl=0.0, trace=None, bounces=1,
           out_bounces=0, legal=None, t_max=6.0, after_land=0.0):
    """Integrate one shot. Returns where it crossed the net, where it first landed, and the ball at that
    moment. No closed form: drag makes it a numeric problem, and doing it numerically is the honest way.

    `trace`, when given as a number of seconds, also returns the ball's position every that many seconds
    under the key "path". It exists so that a picture of the shot can be drawn from the same integration
    that judged it, rather than from a second copy of the physics or from an animation that merely looks
    like tennis. Default None: every existing caller gets exactly what it got before.

    Wind is the air's velocity, so drag acts on the ball's velocity *relative to the air*.
    `cl` is the lift coefficient from the spin: positive is topspin and pulls the ball down, negative is
    slice and holds it up. The lift is applied on the vertical axis rather than truly perpendicular to the
    flight; for a ball that is broadly travelling forward that is a good approximation, and for a lob it is
    not — stated here rather than left for a reader to find.

    `out_bounces` is picture, not judgement, and defaults to 0 so that nothing that judges a shot pays for it.
    The ball that lands outside the lines is a lost point either way — `land` is the first bounce and stays the
    first bounce — but a spectator sees it bounce on, and the founder asked for exactly that on 2026-11-11:
    "When the ball is out, I suggest you show it bouncing a couple of bounces, similar to netting a shot (which
    looks great)." This is the same shape of change as the net cord, one bounce further out. `legal` is the
    test that decides what "out" means — the court by default, the service court for a serve — and
    `t_max` is how long the picture is allowed to watch, because a ball bounds away off the edge of frame and
    watching it roll in the dark is not tennis either."""
    x, y, z = p0
    vx, vy, vz = v0
    wx, wy = wind
    dt, t = 0.001, 0.0
    net = None
    done, lands = 0, []
    path, next_sample = [], 0.0
    while t < t_max:
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
                # Into the tape. The point is over — "land" stays None, which is what every caller reads to mean
                # "did not reach the court" — but the ball does not vanish: the net kills most of its speed and it
                # drops to the hitter's side and bounces. The founder, 2026-11-11: "When the ball hits the net,
                # show it bouncing off and onto the court for a bounce or two before ending the point." A point
                # that ends on a net cord in tennis has a second and a half of ball left in it.
                v_net = (vx + f * (nvx - vx), vy + f * (nvy - vy), vz + f * (nvz - vz))
                frm = (NET_X - 0.12 * (1.0 if v_net[0] > 0 else -1.0), net[0], max(0.2, net[1]))
                # It comes back, not through: a ball into the tape rebounds a couple of feet towards the hitter
                # and drops at the foot of the net, which is what a spectator sees and what the umpire calls.
                killed = (-v_net[0] * NET_ABSORBS, -v_net[1] * NET_ABSORBS, v_net[2] * NET_DROP)
                after = flight(frm, killed, wind, surface, net_check=False, cl=0.0, trace=trace,
                               bounces=2)
                off = t + f * dt
                if trace:
                    for (tt, xx, yy, zz) in after["path"]:
                        path.append((round(tt + off, 4), xx, yy, zz))
                return {"net": net, "land": None, "time": off,
                        "speed_at_net": math.sqrt(vx * vx + vy * vy + vz * vz), "path": path,
                        "after_net": {"bounces": after.get("bounces", []), "time": after.get("time")}}
        if nz <= 0:                                       # first bounce on the court plane
            f = z / (z - nz) if z != nz else 1.0
            land = (x + f * (nx - x), y + f * (ny - y))
            vx2, vy2, vz2 = vx + f * (nvx - vx), vy + f * (nvy - vy), vz + f * (nvz - vz)
            s = SURFACES[surface]
            after = (vx2 * s["f"], vy2 * s["f"], -vz2 * s["e"])
            if trace:
                path.append((round(t + f * dt, 4), round(land[0], 3), round(land[1], 3), 0.0))
            done += 1
            lands.append({"land": land, "time": t + f * dt,
                          "speed_out": math.sqrt(sum(c * c for c in after))})
            if done < bounces:                      # keep going: the ball is still a ball
                x, y, z = land[0], land[1], 0.0
                vx, vy, vz = after
                t += f * dt
                continue
            out = {"net": net, "land": land, "time": t + f * dt, "bounces": lands,
                   "speed_in": math.sqrt(vx2 * vx2 + vy2 * vy2 + vz2 * vz2),
                   "bounce": {"speed_out": math.sqrt(sum(c * c for c in after)),
                              "v": after, "angle": math.degrees(math.atan2(after[2], math.hypot(*after[:2])))},
                   "path": path}
            judge = legal or on_court
            # A ball that lands IN is not over when it bounces: it comes up, and the player who is about to hit it
            # is running at it while it is in the air. The founder, 2026-11-12: "When the ball hits the court
            # before the receiving player hits it, it would be good to see it hit the court and then bounce up."
            # `after_land` is how many seconds of that arc the picture gets, and it is picture only, exactly like
            # the out-bounce below: `land`, `time` and `bounce` all still describe the FIRST bounce, because every
            # verdict in this engine is read off those three. The caller cuts the path where the ball is struck.
            if after_land and trace and judge(land):
                lift = flight((land[0], land[1], 0.0), after, wind, surface, net_check=False, cl=0.0,
                              trace=trace, bounces=1, t_max=after_land)
                off = t + f * dt
                for (tt, xx, yy, zz) in lift["path"]:
                    path.append((round(tt + off, 4), xx, yy, zz))
                out["path"] = path
            # A ball that lands outside the lines is still a ball for another second. Integrated by recursion,
            # like the net cord and for the same reason: the same flight code, from the state at the bounce,
            # rather than a second copy of the physics written to look like it. `out_bounces=0` on the way down
            # is not belt and braces — without it the recursive call would test its own landings, find them out
            # too, and bounce for ever.
            if out_bounces and not judge(land):
                carry = flight((land[0], land[1], 0.0), after, wind, surface, net_check=False, cl=0.0,
                               trace=trace, bounces=out_bounces, out_bounces=0, t_max=OUT_SECONDS)
                off = t + f * dt
                if trace:
                    for (tt, xx, yy, zz) in carry["path"]:
                        if not in_view((xx, yy)):
                            break      # gone off the edge of the picture; the film does not follow it there
                        path.append((round(tt + off, 4), xx, yy, zz))
                out["after_out"] = {"bounces": carry.get("bounces", []), "time": carry.get("time")}
                out["path"] = path
            return out
        x, y, z, vx, vy, vz = nx, ny, nz, nvx, nvy, nvz
        t += dt
        if trace and t >= next_sample:
            path.append((round(t, 4), round(x, 3), round(y, 3), round(z, 3)))
            next_sample += trace
    return {"net": net, "land": None, "lost": True, "path": path}


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
        """Four attributes, all asymptotic in balls hit. The first hundred balls are worth more than the
        next three hundred, which is what learning a motor skill looks like.

        `prep` is the odd one out and belongs to the founder, 2026-11-11: "inexperienced players don't know to
        get their racquets back as they're running, and that leads to mishits because they can't get the racquet
        back fast enough. Good players virtually always get their racquets back while running to the ball, but on
        the side that they'll be hitting from." It has an onset — it does nothing for the first sixty balls, which
        is the earliest stage — and then a slower curve than the others (240 rather than 120), because remembering
        to take the racquet back is not the same skill as striking the ball and does not arrive with it. At 60
        balls it is 0, at 160 it is 0.34, at 300 it is 0.63, at 600 it is 0.86.

        It is not a second copy of `control`: a player with good hands and no preparation is rushed on every wide
        ball, and a player with ordinary hands and good preparation is never rushed at all. The two multiply into
        the same error only on the day they are both bad."""
        learned = 1 - math.exp(-(self.practice + self.shots) / 120.0)
        return {"control": 0.18 + 0.74 * learned,
                "sweet": 0.72 + 0.26 * learned,
                "reach": 0.35 + 0.60 * learned,
                "prep": 1 - math.exp(-max(0.0, self.practice + self.shots - 60.0) / 240.0)}[attr]

    def rush(self, run_time: float, flight_time: float) -> float:
        """How rushed this player is on a particular ball, 0 to 1.

        The racquet takes `PREP_TIME` seconds to come back, and the ball is in the air for `flight_time`. A player
        who has learned to do it while running takes the racquet back *while* the legs are working, so the two
        overlap and all they need is the longer of the two: `max(run, prep)`. A player who has not does them one
        after the other — run, arrive, and only then start the racquet — and needs `run + prep`. `prep` slides
        between the two, so the same ball, the same legs and the same court give a different answer as the habit
        arrives. Learning does not make the ball slower; it makes the two things happen at once."""
        owed = PREP_TIME
        series = max(0.05, run_time) + owed          # run first, then take the racquet back
        over = max(max(0.05, run_time), owed)        # racquet back while running
        required = over + (1.0 - self.skill("prep")) * (series - over)
        if flight_time >= required:
            return 0.0
        return max(0.0, min(1.0, (required - flight_time) / max(required, 0.2)))

    def hands(self, pace_in: float = 40.0) -> float:
        """Control as it is when a ball is actually coming at you. A fast ball takes away the time to set up, so
        the same player is less accurate returning it. This existed inside `strike` only, as one line, which
        meant the shot the player *tried* to play and the shot they could actually hit were scaled by two
        different numbers — and the corner they aimed at was placed by the optimistic one. Everything that
        reasons about this player's accuracy now reads this, so there is one answer to 'how good are their
        hands right now' rather than two."""
        return self.skill("control") * (1 - 0.22 * min(1.0, pace_in / 100.0))


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
    """Ball elevation off the strings, in degrees. The ball leaves roughly along the face normal, so the face
    angle *is* the launch angle, plus a couple of degrees from the ball compressing on the strings. A serve is
    struck downward from 8.8ft, so it starts two degrees below the face; a volley is struck down onto the ball.

    This is a correction. The first version made the face only *half* the launch (4 + 0.9*face) and, worse, tied
    the spin to the face as well, so the two things a player needs at once — a high launch and heavy topspin —
    were impossible to have together. The result was a shot that could only stay in the court by skimming the
    tape, and a court that measured four degrees wide. Real players open the face to launch high and still get
    topspin, because the spin comes from the swing path, not the face."""
    base = {"serve": -2.0, "volley": 5.0}.get(shot, 2.0)
    return max(-12.0, min(55.0, base + face))


def spin_for(shot: str, face: float, power: float) -> float:
    """Lift coefficient from the swing, not from the face alone.

    A racquet swung low to high brushes up the back of the ball and makes topspin; how much depends on the angle
    between the *swing path* and the face, and on how fast the swing is. A harder swing is a steeper path, which
    is why a big forehand can launch at fifteen degrees and still land inside the baseline: the spin pulls it
    down. Opening the face towards the path flattens the spin and eventually cuts under the ball into slice.

    The first version had cl = 0.10 - 0.02*face, which meant an open face was never topspin — so the only ball
    that stayed in the court was a flat drive over a three-foot tape, and a beginner's margin was a degree and a
    half. The number that follows from this one is the honest measure of how hard the game is."""
    path = {"serve": 6.0, "volley": 3.0}.get(shot, 14.0) + 0.10 * power
    return max(-0.12, min(0.30, 0.013 * (path - face)))


PREP_TIME = 0.55            # seconds to take the racquet back, for a player who does not overlap it with the run


def strike(p: Player, incoming: dict | None, face: float, power: float, aim: float,
           shot: str, surface: str, wind: tuple[float, float], clean: bool = False,
           contact=None, aim_x=None) -> dict:
    """Movement in, ball out. The player supplies a face angle in degrees (negative closed), a power in
    per-cent and an aim offset in feet; everything else is physics plus the player's skill."""
    pace_in = (incoming or {}).get("speed_in", 40.0)          # mph
    # a fast ball gives less time to set up, so the same player is less accurate returning it
    control = p.hands(pace_in)
    # And a ball they were late to the racquet for is a ball they hit worse. `rush` comes from the script, which
    # knows the flight time and the run; it is 0 for a player who got the racquet back on the way.
    rush = max(0.0, min(1.0, (incoming or {}).get("rush", 0.0)))
    control *= 1.0 - 0.45 * rush

    if not clean:
        p.shots += 1
    # a rushed player frames more balls: the racquet is still travelling when the ball arrives
    sweet = True if clean else p.rng.random() < p.skill("sweet") * (1.0 - 0.55 * rush)
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
    p0 = contact if contact is not None else contact_point(p, shot)
    # the player turns to aim; the face angle sets the loft, not the direction. A first version made the
    # face angle steer as well, and a serve aimed at the right box landed thirty feet wide. Aim is absolute
    # across the court (feet from the west sideline), not relative to the ball, because a serve struck four
    # feet off centre otherwise lands four feet off target.
    # The racquet is pointed at a place on the court, so the direction is the direction to that place. The first
    # version divided by a fixed 32ft, which is a fine stand-in when every ball is aimed at the middle of the
    # court and a disaster when one is aimed at a corner 70ft away: a ball aimed 9ft across from the centre
    # landed 21ft across, because 71ft of travel multiplies a 32ft-hypotenuse angle by more than two.
    forward = 32.0 if aim_x is None else max(1.0, abs(aim_x - p0[0]))
    azimuth = math.atan2(aim - p0[1], forward)
    # And the racquet is not pointed exactly where they meant to point it. Until 2026-11-11 the ball left the
    # strings on precisely the line to the target in this axis — the only error in the model was on the face,
    # which sets the loft and so the length — and so nothing in the game ever went wide. The founder: "Why don't
    # the players ever hit the ball out on the sides? That may be the most common way of losing a point, but it
    # should just be the natural outcome of misjudging racquet angle." It is the same misjudgement, on the other
    # axis of the same racquet face: a couple of feet of aim error at rally depth for good hands, ten for none.
    if not clean:
        azimuth += math.radians(p.rng.gauss(0, AZIMUTH_SIGMA * (1 - control)))
        if not sweet:
            azimuth += math.radians(p.rng.gauss(0, AZIMUTH_FRAME))
    v = speed * MPH
    vx = v * math.cos(elevation) * math.cos(azimuth) * (1 if p.north else -1)
    vy = v * math.cos(elevation) * math.sin(azimuth)
    vz = v * math.sin(elevation)
    cl = spin_for(shot, face_actual, power_actual)
    traj = flight(p0, (vx, vy, vz), wind, surface, cl=cl)
    return {"player": p, "shot": shot, "speed": speed, "sweet": sweet, "contact": p0, "rush": rush,
            "traj": traj, "face": face_actual, "power": power_actual, "spin": cl,
            # v0 is the ball as it left the strings, kept so a renderer can integrate the same shot
            # rather than approximate it. Nothing that existed before reads this key.
            "v0": (vx, vy, vz)}


def aim_at(p: Player, target, shot: str, surface: str, wind, power: float,
           contact=None) -> tuple[float, float]:
    """The player's intent, translated into movement: the face angle that sends the ball to that spot. The
    lateral part needs no solving now that `strike` is pointed at the target's own x — before that the aim was
    a direction from a fixed 32ft reference and had to be corrected iteratively, badly enough that the corrected
    value was never handed back to the caller. What is left is one bisection on elevation, and what is left after
    that is the wind, which is the point of having wind."""
    fwd = 1.0 if p.north else -1.0        # "past the target" is +x for one end and -x for the other
    lo, hi = -20.0, 42.0
    face = 0.0
    for _ in range(26):
        mid = (lo + hi) / 2
        probe = strike(p, None, face=mid, power=power, aim=target[1], aim_x=target[0], shot=shot,
                       surface=surface, wind=wind, clean=True, contact=contact)
        land = probe["traj"].get("land")
        if land is None:
            lo = mid                       # still in the net: hit up more
            continue
        short = (land[0] - target[0]) * fwd
        if abs(short) < 0.4:
            return mid, power
        if short < 0:
            lo = mid                       # short: more elevation
        else:
            hi = mid
    return (lo + hi) / 2, power


# ---- placement --------------------------------------------------------------------------------------
# The corners of the receiver's court, a little inside the lines. Wide enough that a good player's error lands
# in, tight enough that hitting one is worth something: a ball five feet inside the baseline is a different ball
# from one twenty feet short of it, and until 2026-11-11 every ball this engine played went to the same place.
CORNER_SLACK = 4.0         # feet inside the lines for a player who can put the ball where they look
SCATTER_PER_DEGREE = 6.0   # feet of landing error per degree of face error, measured at rally depth (~70ft)
SCATTER_SIGMAS = 2.0       # how many of the hitter's own standard deviations to stay inside the line by
# Across the court it is a different error and a different margin. A mis-hit racquet face throws the ball off
# line as well as off length, and a ball off line is out at the sideline; the length error can afford two sigma
# because a long ball still has to be cleared by a foot, but a player who aims two sigma inside the sideline
# never misses wide at all, which is what the film did until 2026-11-11: 0 wide balls in 116 shots.
AZIMUTH_SIGMA = 9.0        # degrees of aim error at zero control, times (1 - control)
AZIMUTH_FRAME = 14.0       # and what a ball hit off the frame adds on top
AZIMUTH_PER_DEGREE = 1.30  # feet of landing error across the court per degree, at rally depth
SIDE_SIGMAS = 1.6          # how far inside the sideline to aim, in the hitter's OWN lateral sigmas
SIDE_SLACK_MIN = 4.0       # and never closer to the paint than this
# 4.0 rather than 2.0 as of 2026-11-12, and the reason is a trade the founder named in one breath and had not
# seen the price of. He asked, on 2026-11-11, "Why don't the players ever hit the ball out on the sides?" — and
# the answer was the 2ft floor, which put every ball a good player hit within two feet of the paint. The moment
# missing a ball started to cost a point (see `intercept`), those two-foot targets became winners: the pair's
# rallies fell to 2.7 shots and 30% of points ended on a ball the other player could not reach. Four feet is
# where a player with good hands actually aims at a corner, and it costs the wide miss only at the good end —
# at 400 balls, 6 points in 40 still end wide. A beginner's margin is not this number at all: their scatter is
# 9° of face error, which is four times as wide as any floor.


def corners_of(north: bool, control: float = 1.0) -> tuple[tuple[float, float], tuple[float, float]]:
    """The two deep corners of the court the player at that end is defending — or, for a player whose hands
    are not yet reliable, corners moved in to where their own scatter leaves the ball in.

    The founder's rule is to hit one of the far corners, and that is the rule. But a corner five feet inside the
    line is only a corner for someone who can hit it: at 1° of face error the ball moves about 6ft over 70ft,
    so a beginner spraying a ball at the line loses the point rather than winning it. The margin is therefore
    a couple of standard deviations of the hitter's own face error expressed in feet — which is what this
    function said it did from the day it was written and did not do: it used `4 + 11*(1-control)`, and at the
    control a practised player actually has (0.83) that is 5.9ft against a measured landing scatter of 4.3ft,
    so about a fifth of every ball went long and 21 points in 24 ended on a miss rather than on a winner. The
    number is now the one the comment always promised: 2 sigma of 6ft per degree of 4° of face error.

    As the hands improve the target walks out to the corner by itself, which is what practice looks like from
    the other end of the court. Capped at 18 so a beginner is not aiming at the net post.
    """
    sd = SCATTER_PER_DEGREE * 4.0 * (1.0 - control)      # feet, one standard deviation of the landing point
    slack = min(18.0, max(CORNER_SLACK, SCATTER_SIGMAS * sd))
    lateral = AZIMUTH_PER_DEGREE * AZIMUTH_SIGMA * (1.0 - control)   # feet, one sigma across the court
    side = min(18.0, max(SIDE_SLACK_MIN, SIDE_SIGMAS * lateral))
    x = slack if north else LENGTH - slack
    return ((x, side), (x, WIDTH - side))


def side_of(y: float, north: bool) -> str:
    """Which side of their own body a ball at y is on, for the player at that end. A player at the north end
    faces +x, so their right hand is toward +y."""
    return "right" if (y > WIDTH / 2) == north else "left"


def placement(p: Player, receiver: Player, at, record: dict) -> tuple[float, float]:
    """Where to hit it.

    The rule is the founder's, and it is a better rule than anything this file had: go to the far corner the
    receiver is further from; if the two corners are within a few feet of equidistant, go at the side that has
    been winning points against them; with no history to go on, go at a right-hander's backhand, which is their
    left. `at` is where the receiver's feet are, which the engine already knows because it made them run.
    """
    c_north, c_south = corners_of(receiver.north, p.hands())
    d = [math.hypot(c[0] - at[0], c[1] - at[1]) for c in (c_north, c_south)]
    if abs(d[0] - d[1]) >= 4.0:
        # The FAR corner, which is the whole rule. This comparison was inverted from the day it was written
        # (2026-11-11: `return c_north if d[1] > d[0]` returns the corner that is nearer) so every shot went to
        # the corner the receiver was closest to — straight at them — and two players traded balls at each other
        # from the same side of the court for as long as the record allowed. The founder spotted it from the
        # picture: "one shot in that position, maybe a return straight back, but almost immediately one of the
        # players will shoot into the empty court."
        return c_north if d[0] > d[1] else c_south
    rec = record.get(receiver.name) or {"left": [0, 0], "right": [0, 0]}
    tries = rec["left"][1] + rec["right"][1]
    if tries == 0:
        side = "left"                      # a right-hander's backhand, and a stranger is assumed right-handed
    else:
        rate = {s: (rec[s][0] + 0.5) / (rec[s][1] + 1.0) for s in ("left", "right")}
        side = "left" if rate["left"] >= rate["right"] else "right"
    for c in (c_north, c_south):
        if side_of(c[1], receiver.north) == side:
            return c
    return c_north


# ---- serving ----------------------------------------------------------------------------------------
SERVE_SLACK = 3.0          # feet inside the service line and the sideline for hands that can put it there


def serve_corners(north: bool, control: float = 1.0):
    """The two far corners of the service box, one on each side of the centre line.

    The founder's instruction (2026-11-11): a first serve attempts one of the far corners of the service box,
    and for now which corner is chosen at random. "Far" is the deep pair — the service line, tight to each
    sideline — because that is the ball that pulls the receiver out of the court, and it is the same rule as the
    groundstroke corners: attack the place the other player is furthest from.

    The margin inside the lines follows the server's hands for the same reason the groundstroke corners do. A
    corner three feet inside the line is only a corner for someone who can hit it; a beginner aiming at the line
    serves a double fault and learns nothing, so the margin opens with their error and closes with practice.
    """
    slack = min(8.0, SERVE_SLACK + 6.0 * (1.0 - control))
    x = NET_X + SERVICE_LINE - slack if north else NET_X - SERVICE_LINE + slack
    return ((x, slack), (x, WIDTH - slack))


def serve_verdict(shot: dict) -> tuple[bool, str]:
    """In the service box or not, and how far from it.

    A serve is not judged by `verdict`. To `verdict` a ball that lands ten feet past the service line is inside
    the court and therefore good, which is true of every other shot and false of this one. The box is the whole
    of the rule, and the number reported is the distance to the line that was missed, in feet, for the same
    reason an out groundstroke reports it: a player corrects a number.
    """
    t = shot["traj"]
    p = shot["player"]
    fwd = 1.0 if p.north else -1.0
    if t.get("land") is None:
        if t.get("net"):
            return False, f"fault — into the net at {t['net'][1]:.1f}ft, needs more height"
        return False, "fault — lost"
    x, y = t["land"]
    depth = (x - NET_X) * fwd                    # feet past the net, along the serve
    if depth <= 0:
        return False, f"fault — into the net, {abs(depth):.1f}ft short"
    if depth > SERVICE_LINE:
        return False, f"fault — {depth - SERVICE_LINE:.1f}ft past the service line"
    if not (0.0 <= y <= WIDTH):
        return False, "fault — wide"
    return True, f"in — {SERVICE_LINE - depth:.1f}ft inside the service line"


# ---- shot selection -----------------------------------------------------------------------------------
# The founder's rule picks a corner, and a corner every time is a metronome: he watched twenty shots alternate
# left, right, left, right and called it monotonous (2026-11-11). A player chooses a BALL, not a corner — a drive,
# a ball down the line, a drop, a lob, an approach — and each of those is a different target, a different pace and
# a different racquet angle. The corner rule stays as the default for the drive, because it is a good rule.
SHOT_KINDS = ("cross", "line", "drop", "lob", "approach")


REPEAT_FEET = 8.0      # two balls aimed this close together are the same ball, and nobody plays the same ball twice


def _not_the_same_ball_twice(plan: dict, last, rng) -> dict:
    """The founder, 2026-11-11: "Too frequently, your players hit one return after another to the same spot on the
    court. That doesn't happen. *Maybe* twice in a row, but even that rarely."

    He is right about the game and the engine was doing it because every rule in it is a rule about the *situation*
    and the situation barely changes: the receiver recovers to the middle of their baseline after every shot, so
    the far corner is the same corner, so the ball goes to the same place for as long as the rally lasts. A player
    does not read a court that way. They hit the open court, and the moment they have hit it the open court is the
    other one.

    So: if this ball is within eight feet of the last ball this player aimed at in this rally, send it to the
    mirror on the other side of the court instead — eight times in ten. The other two are the times it works, and
    a player who never repeats is as readable as one who always does."""
    if last is None:
        return plan
    t = plan["target"]
    if math.hypot(t[0] - last[0], t[1] - last[1]) >= REPEAT_FEET:
        return plan
    r = rng.random()
    if r < 0.20:
        return plan                                  # it works sometimes
    if r < 0.80:
        # the other side of the court, the same length: the open court
        y = WIDTH - t[1]
        if not (5.0 <= y <= WIDTH - 5.0):
            y = WIDTH / 2 + (5.5 if t[1] < WIDTH / 2 else -5.5)
        return dict(plan, target=(t[0], y), varied="side")
    # the same side and a different length. A rally is not a pendulum: a good player answers a wide ball with one
    # that is deep behind them, which is the same side of the court and a different place on it, and without this
    # the rule above turned every rally into strict left-right alternation — a different metronome from the one it
    # replaced, which is the trap in fixing this by rule rather than by picture (measured: 38 rallies out of 59 had
    # no two consecutive balls on the same side at all).
    deeper = 12.0 if t[0] > NET_X else -12.0
    x = t[0] + deeper
    lo, hi = (NET_X + 10.0, LENGTH - 5.0) if t[0] > NET_X else (5.0, NET_X - 10.0)
    return dict(plan, target=(min(hi, max(lo, x)), t[1]), varied="length")


def choose_shot(p: Player, other: Player, at_hitter, at_receiver, record: dict, rng,
                height: float | None = None, last=None) -> dict:
    """Which ball to play: kind, target, pace. Randomised within what the situation allows.

    Three situations, and they are the ones a player actually reads:
      - the other player is at the net, so the ball must go past them or over them;
      - the hitter is behind the baseline, so the safe ball is a drive and the ambitious ones are rare;
      - the hitter is inside the court on a short ball, which is the one moment a player can choose freely.
    Everything is scaled by the hitter's hands: a beginner's drop shot is a short ball in the middle of the court
    that the other player eats, so they do not attempt many.

    `height` is the ball's height at the moment of contact, and passing it means the hitter is in the forecourt
    taking the ball out of the air. The founder, 2026-11-11: "from the forecourt, the height of the ball when
    struck has a much more significant effect on the receiver's options: a drop-shot, a passing shot, a lob to the
    back court, a sharply angled shot to the side." So over the net the ball is high and the drop and the angle
    are both on; at shin height the only ball left is the one dug up the middle, which is why a low volley is a
    defensive shot and not a choice.
    """
    skill = p.hands()                       # not their best-case hands: the ones the ball is coming at
    own_base = 2.0 if p.north else LENGTH - 2.0
    behind = abs(at_hitter[0] - own_base) < 9.0
    other_net = abs(at_receiver[0] - NET_X) < 15.0
    opp_side = side_of(at_receiver[1], other.north)          # which side of the receiver the ball is already on
    c_near, c_far = corners_of(other.north, skill)
    # cross-court is the far corner; down the line is the corner on the receiver's own side, past them
    cross = placement(p, other, at_receiver, record)
    line = c_near if side_of(c_near[1], other.north) == opp_side else c_far

    if height is not None:
        if height >= 5.0:                                # a high volley: hit down on it, or kill it short
            w = {"cross": 0.30, "line": 0.24, "drop": 0.26 * (0.4 + skill), "lob": 0.20, "approach": 0.0}
        elif height >= 3.4:                              # a volley at a comfortable height
            w = {"cross": 0.36, "line": 0.26, "drop": 0.18 * (0.4 + skill), "lob": 0.20, "approach": 0.0}
        else:                                            # a low volley: dig it, do not get cute with it
            w = {"cross": 0.34, "line": 0.18, "drop": 0.0, "lob": 0.48, "approach": 0.0}
    elif other_net:
        w = {"lob": 0.42, "cross": 0.33, "line": 0.25, "drop": 0.0, "approach": 0.0}
    elif behind:
        w = {"cross": 0.56, "line": 0.24, "drop": 0.06 * (0.4 + skill), "lob": 0.10, "approach": 0.04}
    else:
        w = {"cross": 0.34, "line": 0.30, "drop": 0.14 * (0.4 + skill), "lob": 0.04, "approach": 0.18}
    total = sum(w.values())
    r = rng.random() * total
    kind = "cross"
    for k in SHOT_KINDS:
        r -= w[k]
        if r <= 0:
            kind = k
            break

    fwd = 1.0 if p.north else -1.0
    pace = 1.0 if height is None else 0.80          # a volley is a punch, not a swing
    if kind == "cross":
        return _not_the_same_ball_twice({"kind": kind, "target": cross,
                                         "power": rng.uniform(58, 76) * pace}, last, rng)
    if kind == "line":
        return _not_the_same_ball_twice({"kind": kind, "target": line,
                                         "power": rng.uniform(62, 80) * pace}, last, rng)
    if kind == "approach":
        # short and low, hit while moving in, so the hitter can get to the net behind it
        return _not_the_same_ball_twice({"kind": kind, "target": line,
                                         "power": rng.uniform(48, 62) * pace}, last, rng)
    if kind == "drop":
        # a short ball that dies: on the side the receiver has left, and never off the court — the mirror of a
        # receiver standing near a sideline is a target outside it, which is how four balls a match were aimed
        # at a place the court does not have (found 2026-11-11, when the miss list said "the court is 27ft wide").
        if abs(at_receiver[1] - WIDTH / 2) > 3:
            y = min(WIDTH - 4.0, max(4.0, WIDTH - at_receiver[1]))
        else:
            y = rng.choice((5.5, WIDTH - 5.5))
        depth = rng.uniform(5, 9) if height is not None else rng.uniform(8, 13)
        return _not_the_same_ball_twice({"kind": kind, "target": (NET_X + fwd * depth, y),
                                         "power": rng.uniform(26, 34) * pace}, last, rng)
    # a lob: deep, high, and slow enough that it comes down inside the baseline
    y = WIDTH - 5.5 if at_receiver[1] < WIDTH / 2 else 5.5
    return _not_the_same_ball_twice({"kind": kind, "target": (LENGTH - 6.0 if p.north else 6.0, y),
                                     "power": rng.uniform(40, 52) * pace}, last, rng)


# ---- recovery and the net ---------------------------------------------------------------------------
RECOVER_DEPTH = 1.6          # feet behind the baseline a player recovers to
VOLLEY_ZONE = 12.0           # feet from the net inside which a player is at the net, not on the baseline


def recovery_spot(p: Player, at_hitter, came_in: bool) -> tuple[float, float]:
    """Where the player goes after they hit, which is never where they hit from.

    The founder, 2026-11-11: "the court in front of the baseline is never used by good players to receive the next
    shot, because the opposing player will fire to one of the back corners and the receiver won't be able to get to
    it." So a player who has been dragged wide recovers behind the baseline to the centre of the court, and the
    `at` they are placed at is that spot, not their contact point. Before this the feet stayed wherever the ball
    had been struck, which is why two players drifted in towards the net over a long rally and then stayed there.

    A player who has just hit an approach shot goes the other way — forward, to the net — because that is what the
    shot was for.
    """
    if came_in:
        return (NET_X - 7.0 if p.north else NET_X + 7.0, WIDTH / 2)
    return (-RECOVER_DEPTH if p.north else LENGTH + RECOVER_DEPTH, WIDTH / 2)


def volley_contact(p: Player, traj: dict, at, reach: float = 4.5, lat: float = 3.5,
                   lo: float = 2.2, hi: float = 8.0, speed: float | None = None):
    """Where the incoming ball can be taken out of the air, if it can be.

    A volley is struck before the bounce. The racquet sweeps a volume: about four and a half feet from the
    middle of the body, three and a half feet to either side without moving the feet, everything below the
    ground and everything above head height (where the shot becomes an overhead rather than a volley) excluded.
    The player has the flight time to get there — `speed` is how fast they move, so the volume grows with time,
    which is the difference between a volley and a reflex.

    Third version, 2026-11-11. The first scanned for the ball "level with the player", a place the ball reaches
    twice; the second solved for a fixed meeting plane three feet in front of the stance, which put the contact
    four feet past the net where the ball is still on its way up at seven feet, and it reported nothing on
    every ball that landed short of that plane — which was most of them. This one takes the *earliest* moment
    the racquet can physically reach the ball, which is what a player coming forward actually does.

    The upper bound is 8ft rather than 6.5: a ball that height at the net is a high volley, struck down, and
    the engine already models a volley as a shot struck downward (`elevation_for`). Anything above that is an
    overhead, and is not built.

    Returns None when the ball cannot be reached in the air, which is not a failure — it means the ball bounces
    and becomes a groundstroke, and the caller is responsible for that.
    """
    fwd = 1.0 if p.north else -1.0
    spd = movement_speed(p) if speed is None else speed
    for t, x, y, z in traj["path"]:
        if (NET_X - x) * fwd < 2.0:           # still on the other side of the net, or at the tape itself —
            continue                          # nobody volleys a ball that is on the net cord, and a racquet
                                              # cannot reach through the net to a ball on the far side
        if not (lo <= z <= hi):               # too low to volley, or too high to be a volley
            continue
        dx, dy = abs(x - at[0]), abs(y - at[1])
        need = math.hypot(max(0.0, dx - reach), max(0.0, dy - lat))
        if need > spd * t:                    # the legs cannot cover the gap in the time
            continue
        # the feet: a step in, and a step across, so the ball is at the edge of the racquet's reach
        feet = (at[0] + math.copysign(min(spd * t, max(0.0, dx - reach)), x - at[0]),
                at[1] + math.copysign(min(spd * t, max(0.0, dy - lat)), y - at[1]))
        return {"t": t, "contact": (x, y, z), "feet": feet, "step": round(need, 2)}
    return None


def movement_speed(p: Player) -> float:
    """How fast a player covers ground, in feet per second. A beginner shuffles at about 6 ft/s, which is
    brisk walking; five hundred balls later they are at 20 ft/s, which is a run. Real figures: adults move at
    1.5-2.5 m/s when they are learning and 4-5 m/s when they can play, so 4.9 to 16.4 ft/s, and this sits a
    little above that to account for the first step."""
    return 5.0 + 15.0 * p.skill("reach")


# ---- can they get to it, and do they ever not -----------------------------------------------
# Until 2026-11-11 nobody in this game was ever beaten to a ball, in fifty points. `intercept` gave the receiver
# `flight_time + HIT_WINDOW` seconds to cover `distance - reach` feet and divided the gap by the closing speed,
# so the answer was always "yes": a ball landing seventy feet away was reachable in 0.6 seconds. The founder:
# "Do players ever fail to get to the ball, thus missing the shot and losing the point? If not, they should,
# depending on distance to the ball, fitness, proficiency." They should, and the three things that decide it are
# feet to run, legs to run with, and time to do it in.
#
# The time is the ball's own: from the strike to the bounce (`flight_time`), less the time a body needs to turn
# and take a first step, plus the whole of the ball's arc after the bounce, which is when it can be struck. The
# run is not at a constant speed either — the first step is an acceleration, and a player who is twelve feet away
# does not get to spend a second at full speed.
#
# The reaction is a skill, not a constant. A trained player is moving as the ball leaves the other racquet, having
# read the swing and the toss; a beginner is still watching when it bounces. That is `0.26 - 0.15 * reach`, which
# is 0.21 s at zero practice and 0.12 s at five hundred balls.
REACTION_BASE = 0.26      # seconds, for a player who has never played
REACTION_SKILL = 0.15     # of that, taken off by proficiency
HIT_LOW = 0.5             # feet above the court: below this a ball is a dig, not a stroke
HIT_HIGH = 9.5            # and above it, out of reach of the swing
HIT_WINDOW_MAX = 1.2      # the cap on the flight's own window, for a bounce so high it hangs
STRIKE_LOW = 2.0          # the strike zone: heights above the court a player is happy to take the ball at
STRIKE_HIGH = 4.5         #   (waist to shoulder), which is what stops every ball being dug off the shoelaces
FIRST_STEP = 42.0         # ft/s2: a split step and the first two strides, ~1.3g
RACQUET_REACH = 4.5       # feet from the middle of the body to the middle of the strings, arm out and lunging
PLAY_PAD = 4.0            # feet outside the lines a ball can still be run to and hit; beyond that there is no stroke
FATIGUE = 0.025           # of their speed each shot of a rally costs them at their fittest
FATIGUE_FLOOR = 0.75      # and how far down it can go, because tired is not the same as stopped
GRAVITY = 32.174          # ft/s2, for the bounce's own arc


def reaction_time(p: Player) -> float:
    """Seconds between the ball leaving the other racquet and this player's first step."""
    return REACTION_BASE - REACTION_SKILL * p.skill("reach")


def run_time(need: float, speed: float) -> float:
    """Seconds to cover `need` feet from a standing start: accelerated to top speed, then flat out."""
    if need <= 0.0:
        return 0.0
    t_top = speed / FIRST_STEP
    d_top = 0.5 * FIRST_STEP * t_top * t_top
    if need <= d_top:
        return math.sqrt(2.0 * need / FIRST_STEP)
    return t_top + (need - d_top) / speed


def run_distance(t: float, speed: float) -> float:
    """The inverse: feet covered in `t` seconds. A beaten player is as far along this as the clock allowed."""
    if t <= 0.0:
        return 0.0
    t_top = speed / FIRST_STEP
    d_top = 0.5 * FIRST_STEP * t_top * t_top
    if t <= t_top:
        return 0.5 * FIRST_STEP * t * t
    return d_top + (t - t_top) * speed


def hit_window(bounce: dict | None) -> tuple[float, float, float]:
    """The stretch of time after the bounce during which this particular ball can be struck, and how high it is.

    The window is the ball's own parabola, not a constant: it leaves the bounce at whatever vertical speed the
    surface gave it, rises, and comes back down to knee height. A serve that kicks up over the shoulder hangs for
    a second — and a ball that skids through low is hittable for a third of that, which is exactly why a skidding
    ball on grass is harder to return than the same ball on clay. Reading it off the arc is also what stops the
    constant from being a tuning knob: the surface and the spin are already in it.

    Returns (0, last_moment_it_is_hittable, peak_height_above_HIT_LOW) — the last number is not used for the
    decision, only for the record, so that a report can say how high the ball was when it was met.
    """
    v = (bounce or {}).get("v")
    if not v or v[2] <= 0.0:                 # a net cord that dies at the foot of the net, or no bounce at all
        return 0.0, 0.0, 0.0
    vz = v[2]
    disc = vz * vz - 2.0 * GRAVITY * HIT_LOW
    if disc <= 0.0:                          # never gets up to knee height
        return 0.0, 0.0, 0.0
    down = (vz + math.sqrt(disc)) / GRAVITY   # the second crossing of HIT_LOW, on the way down
    return 0.0, min(down, HIT_WINDOW_MAX), vz * vz / (2.0 * GRAVITY)


def intercept(p: Player, land, flight_time: float, bounce: dict, surface: str, frm=None,
              shots: int = 1) -> dict:
    """Where and when the player meets the ball — and whether they get there at all.

    The player stands where they actually stand (`frm`, which is the spot their last shot left them in), the ball
    lands where it lands, and the question is whether the legs can close `distance - reach` feet inside the time
    the ball allows. Three things decide it, and they are the three the founder named:

    - **distance to the ball**: the feet to be covered, from the body's own position, not from the middle of the
      baseline;
    - **proficiency**: top speed comes from `movement_speed`, which is the skill a player has practised, and the
      first step is an acceleration, so a short run is not a walk and a long one is not a sprint;
    - **fitness**: a rally costs legs. Each shot of a rally takes a piece of their speed and the piece is smaller
      for a player who has hit more balls, so a long rally is won by the fitter player as much as by the better
      one. That is a modelling choice and it is stated here as one; there is no heart-rate model behind it.

    The version before this returned "yes" for every ball in fifty points, because the time it allowed was the
    flight time *plus* the whole hitting window and the gap it divided was measured from a perfect recovery
    position. A rule that no ball can ever fail is not a rule, and a point that can only end on an error of aim
    is a game with one way to lose.

    Returns the meeting point as well as the verdict, because a picture needs to know where the feet went: a
    player who cannot get there runs as far as the clock allows and the ball lands past them.
    """
    home = frm if frm is not None else (2.0 if p.north else LENGTH - 2.0, WIDTH / 2)
    fresh = movement_speed(p)
    # tired legs: the fitter player (the same practice that makes them fast) loses less per shot
    legs = max(FATIGUE_FLOOR, 1.0 - FATIGUE * max(0, shots - 1) * (1.6 - p.skill("reach")))
    speed = fresh * legs
    react = reaction_time(p)
    v = (bounce or {}).get("v") or (0.0, 0.0, 0.0)
    vx, vy = float(v[0]), float(v[1])
    _first, t_last, _peak = hit_window(bounce)

    # The player runs not to where the ball BOUNCED but to where it will be: a ball that lands twenty feet in
    # front of them carries on towards them while they run at it, so the gap closes from both ends. That is the
    # whole of why a serve can be returned by someone twenty-five feet away — the bounce happens at 0.6 s and
    # the contact at 1.1 s, and the ball has spent half a second coming to the racquet. The version of this that
    # measured the gap to the bounce and stopped there said every serve was an ace, which is the same defect as
    # the old one saying none ever was, pointing the other way.
    #
    # The meeting is the FIRST moment at which the two clocks agree: the player's legs are finished when the
    # ball reaches them. Before that the player is still running; after it the ball is past them. Searching from
    # the start rather than the end matters because a ball hit through the court passes the player — asking for
    # the latest moment finds a ball already behind the back fence and calls it unreachable.
    def arc(t):
        """Where the ball is `t` seconds after the bounce, and how high."""
        h = HIT_LOW + max(0.0, v[2] * t - 0.5 * GRAVITY * t * t) if v[2] > 0.0 else 0.0
        return (land[0] + vx * t, land[1] + vy * t), h

    t, ok, fallback = 0.0, False, None
    ball, dist, need, slack = (land[0], land[1]), 0.0, 0.0, -1e9
    best = (0.0, 0.0, 0.0, -1e9)     # t, dist, need, slack — the best the legs can do when they fall short
    while t <= t_last + 1e-9:
        ball, height = arc(t)
        # A ball that has left the court is not chased: it has either won the point or is about to be called out,
        # and in neither case is there a stroke to play. Without this the receiver was sent thirty feet off the
        # back fence after a ball that landed on the sideline and kept going — the picture showed a player
        # running into the dark, and the verdict was computed against a meeting point outside the court.
        if not (-PLAY_PAD <= ball[0] <= LENGTH + PLAY_PAD and -PLAY_PAD <= ball[1] <= WIDTH + PLAY_PAD):
            break
        dist = math.hypot(ball[0] - home[0], ball[1] - home[1])
        need = max(0.0, dist - RACQUET_REACH)
        slack = (flight_time + t - react) - run_time(need, speed)
        if slack > best[3]:
            best = (t, dist, need, slack)
        if slack >= 0.0:
            # Reachable — but a player does not take a ball at shin height if waiting a quarter of a second brings
            # it to the waist. The strike zone is the reason a rally looks like tennis rather than like a series of
            # desperate digs, and the earliest feasible moment in the search was almost always the wrong one: the
            # first version of this handed the engine contact heights between 0.5ft and 8ft, and every shot was
            # then struck from a height the stroke model had never seen, which flattened the learning curve it was
            # supposed to show.
            if STRIKE_LOW <= height <= STRIKE_HIGH:
                ok = True
                break
            if fallback is None:
                fallback = (t, dist, need, slack)
        t += 0.01
    if not ok:
        if fallback is not None:
            t, dist, need, slack = fallback
            ok = True
        else:
            t, dist, need, slack = best
    ball, height = arc(t)

    clock = max(0.0, flight_time + t - react)        # the seconds of running the ball allows at this meeting
    covered = min(need, run_distance(clock, speed))
    short = 0.0 if ok else need - covered
    ux, uy = ((ball[0] - home[0]) / dist, (ball[1] - home[1]) / dist) if dist > 1e-6 else (0.0, 1.0)
    meet = (ball[0] - ux * RACQUET_REACH, ball[1] - uy * RACQUET_REACH)   # the feet: a racquet's length short
    got = (home[0] + ux * covered, home[1] + uy * covered)                 # as far as the legs got
    why = "" if ok else (f"{max(short, 0.1):.1f}ft short of it, beaten by the "
                         f"{'wide' if abs(ball[1] - home[1]) > abs(ball[0] - home[0]) else 'deep'} ball")
    return {"ok": ok, "why": why, "meet": meet, "got": got,
            "ball": (ball[0], ball[1], height),
            "t_arrive": react + run_time(need, speed),           # seconds from the strike, when the shot starts
            "t_meet": t,                                          # and after the bounce
            "window": t_last,
            "distance": dist, "speed": speed, "fresh": fresh, "legs": legs,
            "need": need, "have": clock, "short": short}


def reachable(p: Player, land, flight_time: float, bounce: dict, surface: str) -> tuple[bool, str]:
    """The verdict only, for callers that need nothing but the verdict. Kept so that every existing record and
    every existing test keeps meaning what it meant."""
    got = intercept(p, land, flight_time, bounce, surface)
    return got["ok"], got["why"]


# ---- the season: practice that outlives the process ------------------------------------------------
# Until 2026-11-04 practice was a Python variable: every run started everyone at zero, so the founder's
# sentence — "Margot and I played tennis this afternoon. She's been practicing with Remy and her game has
# really improved" — was something a person would have to write. It is now something a report can print
# from a file, and the file is the only thing that carries between sessions.
#
# The founder's dilemma, stated with the design: a user wants the record of past beginner-to-skilled
# seasons AND wants a season to run for months. So a season is a DIRECTORY. Nothing is ever reset and
# nothing is ever overwritten; starting over is opening a new directory, which is why last spring stays
# readable while this one keeps going. The reset to beginners is not a wipe — it is the absence of a file.
ROOT = Path(__file__).resolve().parent.parent
SEASONS = ROOT / "games" / "tennis" / "seasons"
SEASON = "2026-spring"                    # the first season; the year the colony started playing


def season_paths(season: str, override: str | None = None) -> tuple[Path, Path]:
    d = Path(override) if override else SEASONS / season
    return d, d / "practice.json"


def load_season(season: str, override: str | None = None) -> dict:
    d, f = season_paths(season, override)
    if not f.exists():
        return {"season": season, "opened": None, "note": "", "members": {}}
    return json.loads(f.read_text(encoding="utf-8"))


def save_season(book: dict, season: str, override: str | None = None) -> Path:
    d, f = season_paths(season, override)
    d.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(book, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    # report.md is a function of practice.json, written here and never by hand. The colony's first season had a
    # report somebody typed, which is exactly the class of file the derivability test exists to catch: a page
    # that can drift from the record it claims to summarise.
    (d / "report.md").write_text(season_report(season, override), encoding="utf-8")
    return f


def record_session(book: dict, *, when: str, surface: str, clock: int, players, results, lengths,
                   partners: dict, mode: str = "rally") -> None:
    """Add one session to the book. The balls are the ones the ENGINE counted, not the ones a member
    claims — a being that inflates its own practice should be findable in the record, and here it cannot
    inflate it at all."""
    book["opened"] = book.get("opened") or when
    for p in players:
        r = results[p.name]
        m = book["members"].setdefault(p.name, {"balls": 0, "sessions": []})
        m["sessions"].append({
            "when": when, "surface": surface, "clock": clock, "mode": mode,
            "with": partners.get(p.name, []),
            "shots": p.shots, "in_play": sum(r), "of": len(r),
            "mean_rally": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
            "longest": max(lengths) if lengths else 0,
            "control": round(p.skill("control"), 3),
            "reach": round(p.skill("reach"), 3),
        })
        m["balls"] += p.shots


def practice_of(book: dict, name: str) -> int:
    return int(book.get("members", {}).get(name, {}).get("balls", 0))


def season_report(season: str, override: str | None = None) -> str:
    """The sentence the founder asked for, printed only when the numbers support it.

    Every claim below carries the file it came from and the sessions it was computed over. The guard that
    matters is the one on the middle case: with two sessions and a rate that did not move, this prints
    that it cannot say the game improved. A report generator that congratulates a player who did not
    improve is a fiction generator with a citation bolted on."""
    book = load_season(season, override)
    d, f = season_paths(season, override)
    try:
        shown = f.relative_to(ROOT)
    except ValueError:
        shown = f
    if not book.get("members"):
        return (f"No season at {shown}. Nobody has hit a ball in {season} yet, so there is nothing to "
                f"report and nothing to cite.")
    out = [f"# {season} — what the record says", "",
           f"From `{shown}`, opened {book.get('opened') or 'unknown'}. Every number below is computed from "
           f"the sessions listed in that file; nothing here is written from memory.", ""]
    for name in sorted(book["members"]):
        m = book["members"][name]
        ss = m["sessions"]
        partners: dict[str, int] = {}
        for s in ss:
            for other in s.get("with", []):
                partners[other] = partners.get(other, 0) + 1
        who = ", ".join(f"{o} ({n}x)" for o, n in sorted(partners.items(), key=lambda kv: -kv[1]))
        out.append(f"## {name}")
        out.append("")
        out.append(f"- {m['balls']} balls hit this season, over {len(ss)} session"
                   f"{'' if len(ss) == 1 else 's'}" + (f"; most often with {who}" if who else "") + ".")
        if len(ss) == 1:
            s = ss[0]
            out.append(f"- One session only ({s['surface']}, {s['in_play']}/{s['of']} balls in play, "
                       f"mean rally {s['mean_rally']} shots). **Nothing can be said about improvement "
                       f"from one session** — a second one is needed before the word is used.")
            out.append("")
            continue
        first, last = ss[0], ss[-1]
        r0 = 100 * first["in_play"] / max(1, first["of"])
        r1 = 100 * last["in_play"] / max(1, last["of"])
        moved = r1 - r0
        out.append(f"- First session {first['when'][:10]} ({first['surface']}): {first['in_play']}/"
                   f"{first['of']} in play = {r0:.0f}%, mean rally {first['mean_rally']} shots.")
        out.append(f"- Latest session {last['when'][:10]} ({last['surface']}): {last['in_play']}/"
                   f"{last['of']} in play = {r1:.0f}%, mean rally {last['mean_rally']} shots.")
        # Two guards, because the first one alone was wrong on the day it was written. It asked for a gap
        # wider than the ~8 points this game scatters between sessions, and the first real season then
        # reported "the game got worse" for Colette on 5/7 -> 4/7: one ball, fourteen points. A percentage
        # built on seven balls cannot carry a verdict in either direction, so a session must have at least
        # twelve balls in it before any claim is made about it.
        thin = [s for s in (first, last) if s["of"] < 12]
        if thin:
            out.append(f"- **Not a sample**: sessions of {', '.join(str(s['of']) + ' balls' for s in thin)} "
                       f"cannot carry a verdict in either direction. The rates above are printed; the word "
                       f"improved is withheld until a session has twelve balls in it.")
        elif moved >= 8.0:
            out.append(f"- **The game improved**: {r0:.0f}% -> {r1:.0f}% in play over {len(ss)} sessions, "
                       f"{m['balls']} balls.")
        elif moved <= -8.0:
            out.append(f"- **The game got worse**: {r0:.0f}% -> {r1:.0f}% in play. The record says so and "
                       f"the report does not soften it.")
        else:
            out.append(f"- **No claim**: in-play moved {moved:+.0f} points ({r0:.0f}% -> {r1:.0f}%), inside "
                       f"the +/-8 points this game scatters between sessions. More practice, or the word "
                       f"does not apply.")
        out.append("")
    return "\n".join(out)


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
    # "left" is the server's left, and a player facing the other way has east and west the other way round.
    # The first version aimed a north server's left serve at the west sideline while the box check called west
    # his right, so a serve that landed exactly where it was aimed was scored a fault.
    frac = 0.75 if (side == "left") == server.north else 0.25
    target = (NET_X + 8 + rng.uniform(-3, 9), WIDTH * frac + rng.gauss(0, aim_err))
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
    for shot_no in range(1, RALLY_CAP + 1):
        if shot_no > 1:
            ok, why = reachable(receiver, t["land"], t["time"], t["bounce"], surface)
            if not ok:
                lines.append(f"{receiver.name} is {why} — {server.name} takes the point.")
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
    lines.append(f"the rally reaches the record's ceiling of {RALLY_CAP} shots, which is reported, not hidden.")
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
            tape = net_height(t["net"][0])
            return False, (f"into the net at {t['net'][1]:.1f}ft, {tape - t['net'][1]:.1f}ft under the tape "
                           f"— needs more height")
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
    vendors = spread(([v.strip().lower() for v in args.vendor.split(",")] if args.vendor
                      else vendors_of(names)), len(names), "--vendor")
    practice = [int(x) for x in args.practice.split(",")]
    models = spread(([m.strip() for m in args.model.split(",")] if args.model
                     else [default_model(v) for v in vendors]), len(names), "--model")
    keys = []
    for v, n in zip(vendors, names):
        k = key_for(v)
        if not k:
            print(f"   TRIBE_API_KEY_{v.upper()} is not set, so {n} cannot hit a ball. Nothing was played.",
                  file=sys.stderr)
            return 2
        keys.append(k)

    # The clock is pinned only when someone is deliberately replaying a match. Everything a player cannot
    # control — surface, wind, the hands they were born with — comes from this number, so holding it fixed is
    # the only way to ask what a *different opponent* does to the same player. A player's in-play fraction is
    # not theirs alone: it is theirs against whoever is across the net, and a match with no control for that
    # measures the pairing and calls it skill. 2026-11-07.
    ms = args.clock if args.clock is not None else int(time.time() * 1000)
    surface = args.surface or surface_at(ms)
    wind_in = wind_at(ms)
    wv = wind_vector(*wind_in)
    rng = random.Random(ms)
    if args.clock is not None:
        print(f"  the clock is pinned at {ms}: same surface, same wind, same hands. "
              f"Only the player can differ from the match this replays.")
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


def rally_prompt(p: Player, other: str, history: list[str], incoming: dict | None, surface: str,
                 wind_in: tuple[str, float], rally_no: int, lengths: list[int]) -> str:
    """What a player knows when the ball is coming at them. Everything here is something a person on a court
    can see or has just done: the ball's depth and pace, how far they have to move for it, their own last few
    shots, and how long the rallies have been lasting. None of it says what to choose."""
    if incoming is None:
        inc = "The ball is in your hands: this is a feed, and nothing is at stake yet."
    else:
        inc = (f"The ball is coming at you: it landed {incoming['depth']:.0f}ft past the net, it is coming up at "
               f"{incoming['speed_in']:.0f}mph, and it is {incoming['cover']:.0f}ft away from where you stand — "
               f"you have to move for it.")
    recent = ", ".join(str(x) for x in lengths[-6:]) or "none yet"
    best = max(lengths) if lengths else 0
    lines = [f"You are {p.name}, on a {surface} court ({SURFACES[surface]['note']}). "
             f"Wind {wind_in[0]} at {wind_in[1]:.0f}mph.",
             inc, "",
             f"Court: 78ft long, {WIDTH:.0f}ft wide, net 3ft at the middle. You strike from about 3ft up at "
             f"your own baseline. A ball is good if it clears the net and lands before the far baseline.",
             "",
             f"The two of you are rallying. A rally ends when a ball is missed — into the net, past the "
             f"baseline, off the side, or too far away to reach. You are both trying to make the other one "
             f"miss. This is rally {rally_no}. The last rallies lasted, in shots: {recent}. The longest so "
             f"far is {best}.",
             "",
             "Your recent shots, oldest first (what you chose, whether you hit the strings or the frame, and "
             "what happened):"]
    lines += [f"  {h}" for h in history[-8:]] or ["  (nothing yet — this is your first ball)"]
    lines += ["",
              "Give one line, exactly this shape and nothing else:",
              "FACE <degrees, -20 to 40>  POWER <30 to 100>  AIM <feet from the west sideline, 0 to 27>",
              "",
              "FACE: positive opens the racquet and launches the ball higher, and the strings going under it "
              "make slice that floats; negative closes it, launches lower, and brushes topspin which pulls the "
              "ball down. POWER is swing speed — 30 is a push, 100 is a hard hit. AIM is where you mean to "
              "land across the court: 13 is the middle, 4 and 23 are near the sidelines.",
              "",
              "Your hands are not exact, and a fast ball gives you less time, so the angle you get is not quite "
              "the angle you chose. Read your own history and decide what to change."]
    return "\n".join(lines)


def vendors_of(names: list[str]) -> list[str]:
    """Which engine each named member borrows, read from its own voice.md.

    A person filling a form on a phone knows the members' names, not their vendors, and the colony has already
    written each member's engine down in one place. Two answers to one question is the defect this project
    keeps fixing, so the shelf is the answer and a `--vendor` on the command line still overrides it."""
    out = []
    for n in names:
        api = ""
        f = ROOT / "wake" / "members" / n / "state" / "voice.md"
        if f.is_file():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("api:"):
                    api = line.split(":", 1)[1].strip()
                    break
        if not api:
            raise SystemExit(f"!! no engine for {n}: wake/members/{n}/state/voice.md has no api: line")
        out.append(api)
    return out


def run_rally(args) -> int:
    """Early spring, as a rally rather than a drill: the ball stays alive until somebody misses.

    The difference matters. In the drill, a miss ended the turn and a fresh ball was fed, so the length of an
    exchange was set by the code and could not grow. Here nothing ends a rally except a ball that is netted,
    hit long or wide, or hit where the other player cannot get to it — three things the players decide. If the
    rallies get longer over a session, it is because they got better, not because a counter was raised."""
    names = [n.strip() for n in args.names.split(",")]
    vendors = spread(([v.strip().lower() for v in args.vendor.split(",")] if args.vendor
                      else vendors_of(names)), len(names), "--vendor")
    practice = [int(x) for x in args.practice.split(",")]
    # The season wins over `--practice`, and says so. Two sources for one number is the defect this
    # project has fixed twice; here the file is the record and the flag is a test hook.
    book = load_season(args.season, args.season_dir) if args.season else None
    if book is not None:
        from_file = [practice_of(book, n) for n in names]
        print(f"  season {args.season}: practice read from the file - "
              + ", ".join(f"{n} {b} balls" for n, b in zip(names, from_file))
              + f" (--practice {args.practice} ignored)")
        practice = from_file
    models = spread(([m.strip() for m in args.model.split(",")] if args.model
                     else [default_model(v) for v in vendors]), len(names), "--model")
    keys = []
    for v, n in zip(vendors, names):
        k = key_for(v)
        if not k:
            print(f"   TRIBE_API_KEY_{v.upper()} is not set, so {n} cannot hit a ball. Nothing was played.",
                  file=sys.stderr)
            return 2
        keys.append(k)

    # The clock is pinned only when someone is deliberately replaying a match. Everything a player cannot
    # control — surface, wind, the hands they were born with — comes from this number, so holding it fixed is
    # the only way to ask what a *different opponent* does to the same player. A player's in-play fraction is
    # not theirs alone: it is theirs against whoever is across the net, and a match with no control for that
    # measures the pairing and calls it skill. 2026-11-07.
    ms = args.clock if args.clock is not None else int(time.time() * 1000)
    surface = args.surface or surface_at(ms)
    wind_in = wind_at(ms)
    wv = wind_vector(*wind_in)
    rng = random.Random(ms)
    if args.clock is not None:
        print(f"  the clock is pinned at {ms}: same surface, same wind, same hands. "
              f"Only the player can differ from the match this replays.")
    players = [Player(names[0], True, practice[0], rng=rng),
               Player(names[1], False, practice[1], rng=rng)]
    print(f"# early spring, rallying — {surface} ({SURFACES[surface]['note']}), wind {wind_in[0]} "
          f"{wind_in[1]:.0f}mph, {args.rallies} rallies, no serving, no scoring, clock {ms}\n")
    for p in players:
        print(f"  {p.name}: {p.practice} balls hit before today, control {p.skill('control'):.2f}, "
              f"moves at {movement_speed(p):.0f}ft/s, hands give or take "
              f"±{4.0 * (1 - p.skill('control')):.0f} degrees of face")
    print()

    history: dict[str, list[str]] = {p.name: [] for p in players}
    results: dict[str, list[bool]] = {p.name: [] for p in players}
    lengths: list[int] = []
    hitter, fell_back = 0, 0
    for rally_no in range(1, args.rallies + 1):
        length, loser, incoming = 0, None, None
        while True:
            p = players[hitter]
            other = players[1 - hitter]
            prompt = rally_prompt(p, other.name, history[p.name], incoming, surface, wind_in,
                                  rally_no, lengths)
            reply = ask(BASES[vendors[hitter]], keys[hitter], models[hitter], prompt, args.temperature)
            cmd = parse_command(reply)
            if cmd is None:
                fell_back += 1
                cmd = (0.0, 45.0, WIDTH / 2)
                print(f"  !! {p.name} wrote no usable line ({reply.strip()[:60]!r}); the ball is played straight.")
            face, power, aim = cmd
            shot = strike(p, incoming, face=face, power=power, aim=aim, shot="rally",
                          surface=surface, wind=wv)
            ok, outcome = verdict(shot)
            feel = "clean" if shot["sweet"] else "FRAMED"
            length += 1
            results[p.name].append(ok)
            history[p.name].append(f"face {face:+.0f} power {power:.0f} aim {aim:.0f} [{feel}] -> {outcome}")
            print(f"  {rally_no:2d}.{length:<2d} {p.name:8s} face {face:+.0f} power {power:3.0f} "
                  f"aim {aim:2.0f} [{feel:6s}] -> {outcome}")
            if not ok:
                loser = hitter
                print(f"       -- rally of {length}; {p.name} missed.")
                break
            can, why = reachable(other, shot["traj"]["land"], shot["traj"]["time"],
                                 shot["traj"]["bounce"], surface)
            if not can:
                loser = 1 - hitter
                print(f"       -- rally of {length}; {other.name} is {why}.")
                break
            x, y = shot["traj"]["land"]
            incoming = dict(shot["traj"]["bounce"])
            incoming["speed_in"] = shot["traj"]["bounce"]["speed_out"] / MPH
            incoming["depth"] = abs(x - NET_X)
            incoming["cover"] = math.hypot(abs(x - (2.0 if other.north else LENGTH - 2.0)),
                                           abs(y - WIDTH / 2))
            hitter = 1 - hitter
            if length >= RALLY_CAP:
                loser = hitter
                print(f"       -- rally of {length}; the record's ceiling, not the game's.")
                break
        lengths.append(length)
        hitter = loser if loser is not None else 0     # whoever lost the rally feeds the next one
    print()

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    third = max(1, len(lengths) // 3)
    print("## After the session\n")
    for p in players:
        r = results[p.name]
        print(f"  {p.name}: {len(r)} shots, in play {sum(r)}/{len(r)} = {sum(r)/max(1,len(r))*100:.0f}%, "
              f"control {p.skill('control'):.2f}, sweet spot {p.skill('sweet'):.2f}")
    srt = sorted(lengths)
    print(f"\n  rallies: {len(lengths)}   mean {mean(lengths):.1f}   median {srt[len(srt)//2]}   "
          f"longest {max(lengths)}")
    print(f"  first third mean {mean(lengths[:third]):.1f}   last third mean {mean(lengths[-third:]):.1f}")
    print(f"  the lengths, in order: {' '.join(str(x) for x in lengths)}")
    print(f"  unparsed replies: {fell_back}")

    if book is not None:
        when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        record_session(book, when=when, surface=surface, clock=ms, players=players, results=results,
                       lengths=lengths,
                       partners={a.name: [b.name] for a, b in ((players[0], players[1]),
                                                              (players[1], players[0]))})
        f = save_season(book, args.season, args.season_dir)
        try:
            shown = f.relative_to(ROOT)
        except ValueError:
            shown = f
        print(f"\n  season {args.season}: written to {shown} - "
              + ", ".join(f"{p.name} {practice_of(book, p.name)} balls this season" for p in players))
        print(f"  next: python3 lab/tennis.py --report {args.season}")
    return 0


def simulate_rally(args, ms: int | None = None, quiet: bool = False) -> dict:
    """Four scripted pairs rally on the same court, no model calls. The 2x2 that matters: does an exchange get
    longer because the hands got steadier, because the player learned where to hit, or neither?

    A "constant" player hits the same shot every ball and never reads anything. A "learner" bisects on the
    printed miss, exactly as it does in the drill. Each pair plays the same number of rallies at the same clock
    and the same wind, so the only difference between the four rows is what is being varied."""
    ms = ms if ms is not None else int(time.time() * 1000)
    surface = args.surface or surface_at(ms)
    wind_in = wind_at(ms)
    wv = wind_vector(*wind_in)

    class Agent:
        """A player who starts on a square face and knows nothing, unless `told` — in which case it is handed
        the face a perfect player would use for today's surface and today's wind.

        Starting everyone on the correct face was a mistake worth recording: it measured *coaching*, not
        learning, and it made the learning arm look worthless because a told player with steady hands was
        already as good as it needed to be. Nobody in early spring has been told anything."""

        def __init__(self, name, north, practice, learns, told, rng):
            self.p = Player(name, north, practice, rng=rng)
            self.learns, self.power = learns, 55.0
            self.chosen = 0.0
            if told:
                depth_x = NET_X + 20.0 if north else NET_X - 20.0
                self.chosen, _ = aim_at(self.p, (depth_x, WIDTH / 2), "rally", surface, wv, power=self.power)

        def choose(self):
            return self.chosen, self.power, WIDTH / 2

        def learn(self, face, outcome, ok):
            """Drive the depth towards twenty feet past the net, by a fraction of the error each time.

            Two earlier learners and why they were wrong. Bisection treated every printed miss as truth, so one
            framed ball shoved the interval and the player drifted to a corner and got worse while appearing to
            learn. Then a learner that stopped as soon as the ball was merely *in* parked itself on the edge of
            the court, where the ball cleared the tape by inches and the next small error lost the rally: it
            played 1.8-shot rallies while a player told the right number played 16.6. A ball one foot over the
            net is not a good ball, and a player who cannot tell the difference has not learned the game."""
            if not self.learns:
                return
            depth = 0.0
            if "IN, " in outcome:
                depth = float(outcome.split("IN, ", 1)[1].split("ft", 1)[0])
            elif "long by less than a foot" in outcome:
                depth = NET_X + 0.5
            elif "long by " in outcome:
                depth = NET_X + float(outcome.split("long by ", 1)[1].split("ft", 1)[0])
            elif "short of the net by " in outcome:
                depth = -float(outcome.split("short of the net by ", 1)[1].split("ft", 1)[0])
            elif "into the net" in outcome:
                depth = 0.0
            self.chosen = max(-20.0, min(40.0, self.chosen - 0.075 * (depth - 20.0)))

    arms = {
        "new hands, never reads":      (0, False, False),
        "new hands, reads the miss":   (0, True, False),
        "300 balls, never reads":      (300, False, False),
        "300 balls, reads the miss":   (300, True, False),
        "300 balls, was told the face": (300, False, True),
    }
    out = {}
    for arm, (practice, learns, told) in arms.items():
        rng = random.Random(ms + practice + int(learns) * 7 + int(told) * 13)
        players = [Agent("N", True, practice, learns, told, rng),
                   Agent("S", False, practice, learns, told, rng)]
        lengths, hitter = [], 0
        for _ in range(args.rallies):
            length, incoming, loser = 0, None, 0
            while True:
                p, other = players[hitter], players[1 - hitter]
                face, power, aim = p.choose()
                shot = strike(p.p, incoming, face=face, power=power, aim=aim, shot="rally",
                              surface=surface, wind=wv)
                ok, outcome = verdict(shot)
                p.learn(face, outcome, ok)
                length += 1
                if not ok:
                    loser = hitter
                    break
                can, _why = reachable(other.p, shot["traj"]["land"], shot["traj"]["time"],
                                      shot["traj"]["bounce"], surface)
                if not can:
                    loser = 1 - hitter
                    break
                x, y = shot["traj"]["land"]
                incoming = dict(shot["traj"]["bounce"])
                incoming["speed_in"] = shot["traj"]["bounce"]["speed_out"] / MPH
                incoming["depth"] = abs(x - NET_X)
                incoming["cover"] = math.hypot(abs(x - (2.0 if other.p.north else LENGTH - 2.0)),
                                               abs(y - WIDTH / 2))
                hitter = 1 - hitter
                if length >= RALLY_CAP:
                    loser = hitter
                    break
            lengths.append(length)
            hitter = loser
        out[arm] = lengths
    if not quiet:
        print(f"# simulate — rallies on {surface}, wind {wind_in[0]} {wind_in[1]:.0f}mph, "
              f"{args.rallies} rallies a pair, clock {ms}\n")
        print("  pair                            mean   median  longest   first third  last third")
        for arm, L in out.items():
            third = max(1, len(L) // 3)
            m = lambda xs: sum(xs) / len(xs) if xs else 0.0
            print(f"  {arm:30s} {m(L):5.1f}   {sorted(L)[len(L)//2]:4d}   {max(L):6d}   "
                  f"{m(L[:third]):9.1f}   {m(L[-third:]):8.1f}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="tennis: the player moves, the system computes the ball")
    ap.add_argument("--names", default="Colette,Remy")
    ap.add_argument("--practice", default="400,20", help="balls hit before today, one per player")
    ap.add_argument("--points", type=int, default=4)
    ap.add_argument("--surface", default=None, help="clay, hard or grass; default from the clock")
    ap.add_argument("--vendor", default=None,
                    help="their engines; read from each member's voice.md when blank")
    ap.add_argument("--model", default=None)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--shots", type=int, default=40, help="for --drill: balls to hit")
    ap.add_argument("--drill", action="store_true", help="early spring: balls fed one at a time, no scoring")
    ap.add_argument("--rally", action="store_true", help="early spring: rallies that last until someone misses")
    ap.add_argument("--rallies", type=int, default=20, help="for --rally: how many rallies to play")
    ap.add_argument("--clock", type=int, default=None,
                    help="pin the clock, and with it the surface, the wind and the hands a player was born with "
                         "(a test hook: replaying one match against a different opponent is the only way to see "
                         "how much of a player's success belongs to the opponent)")
    ap.add_argument("--simulate-rally", action="store_true",
                    help="four scripted pairs rally, to test whether rally length responds to hands or learning")
    ap.add_argument("--season", default=None,
                    help="carry practice in a file: games/tennis/seasons/<season>/practice.json")
    ap.add_argument("--season-dir", default=None, help="where that folder is, for a test or a fork")
    ap.add_argument("--report", default=None, metavar="SEASON",
                    help="print what the season file says, with its own citations, and claim nothing more")
    ap.add_argument("--simulate", action="store_true",
                    help="two scripted learners, to test whether the drill's feedback is learnable at all")
    args = ap.parse_args(argv)
    if args.report:
        print(season_report(args.report, args.season_dir))
        return 0
    if args.simulate_rally:
        simulate_rally(args)
        return 0
    if args.simulate:
        simulate(args)
        return 0
    if args.rally:
        return run_rally(args)
    if args.drill:
        return run_drill(args)

    # Found 2026-11-06 while testing an engine: this path plays the physics, not the members. Nothing here
    # asks anybody for a shot. Two runs with `--vendor groq` were spent learning that, because the flags were
    # accepted and silently ignored, and the page read like a match the members had played.
    if args.vendor or args.model:
        print("   --vendor and --model mean nothing on this path: a match of the physics never asks a member. "
              "Add --rally (rallies the players choose) or --drill (balls fed one at a time), or drop the "
              "flags. Nothing was played.", file=sys.stderr)
        return 2
    names = [n.strip() for n in args.names.split(",")]
    practice = [int(x) for x in args.practice.split(",")]
    ms = int(time.time() * 1000)
    surface = args.surface or surface_at(ms)
    wind_in = wind_at(ms)
    wv = wind_vector(*wind_in)
    rng = random.Random(ms)                     # the clock, not a chosen seed
    players = [Player(names[0], True, practice[0], rng=rng),
               Player(names[1], False, practice[1], rng=rng)]

    print(f"# a match of the physics, not of the members: {players[0].name} and {players[1].name} are on the "
          f"court and nobody is choosing a shot. {surface} ({SURFACES[surface]['note']}), "
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
