#!/usr/bin/env python3
"""Pickleball: the player moves, the paddle contacts, and the engine computes the ball.

The design page is `games/pickleball/README.md` (2026-11-15), and this file is item 2 of its build order:
**the engine, the rules, and the driving game, in text, with no renderer.** The page's numbers are the ones
this file implements — the ball's drag constant, the kitchen's 7 ft, the double bounce, and the doubles
assignment rule — and where the page says a thing is declared rather than measured, this file prints that
it is declared.

What is shared, and not copied. There is one integrator, one vendor table, one clock rule and one season
engine in this repository, and they live in `lab/tennis.py` because a second copy of a thing is how this
repository has been broken before. Twelve imports, zero copies — `lab/pickleball.py` defines no physics:

    flight, net_height           the trajectory integrator and the net profile, parameterised
    wind_at, wind_vector, COMPASS  the wind, drawn from the clock, printed with every shot
    MPH, G                       the unit constants
    Player, Player.skill         the player and the 1-exp(-n/120) learning curve
    movement_speed               feet per second from the reach skill
    interception                 the meeting problem as numbers: can they get there, and where do the feet stop
    parse_command                the FACE / POWER / AIM reply grammar
    vendors_of, open_book        who plays, and the season file that outranks the flag
    member_chooser               ask -> parse -> fall back, one prompt per contact
    record_session, practice_of, seed_practice, load_season, save_season, season_paths, season_report
                                 the season, which is a directory and never a variable

    python3 lab/pickleball.py --rules                  # every rule in this file, fired and printed
    python3 lab/pickleball.py --demo --game 2          # a scripted doubles game, no key, no network
    python3 lab/pickleball.py --report 2026-autumn     # what the season file says

Physics is in feet and seconds, gravity 32.17 ft/s², integrated at 1 ms steps, quadratic drag against the
air's own velocity. The ball is the outdoor 40-hole ball: 2.87 in, 0.88 oz, Cd = 0.33 (86 measured
trajectories), which gives k = 0.0103/ft against a tennis ball's 0.0063.

**Three declared simplifications, printed with the game rather than hidden in it:**
  - **spin is off** (`cl = 0`). The page measures the fitted lift term at 0.83° of launch, which is larger
    than the third-shot drop's own 0.5° window, so a term that uncertain is worse than an honest zero;
  - **positions are a point per player**, advanced toward the ball by `movement_speed`, not a body. The
    kitchen is adjudicated on that point, which is exact for the line and approximate for the toe;
  - **stacking is not modelled** — see the page, §3.8. One hitter per contact, one ball.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tennis import (  # noqa: E402  the twelve, not a thirteenth copy
    COMPASS, G, MPH, RHO, Player, flight, load_season, member_chooser, movement_speed, net_height, open_book,
    VOLLEY_HIGH, VOLLEY_LOW, interception, parse_command, practice_of, record_session, save_season, season_paths,
    vendors_of, volley_contact, wind_at, wind_vector,
)

def volley_carry(p: Player, here, vol: dict, vel: tuple[float, float]) -> tuple[tuple[float, float],
                                                                               tuple[float, float]]:
    """Where a volley leaves the body, and how fast it was still going when the paddle met the ball.

    The rule is the sport's: a player who volleys from behind the kitchen line and is **carried into the kitchen
    by the momentum of the shot** has faulted, even though the ball is already dead. The engine used to encode
    that as a flat 1.5 ft step, applied to every volley taken within 2 ft of the line and to nothing else — which
    made *standing in a place* the offence and a lunge at full stretch innocent. §5f found the cost: a learner
    that walks to the line settles at 1 ft, and the rulebook calls that a fault while this engine's scoreline does
    not, and there was no way to tell which of the two was wrong.

    So the body gets a velocity instead of a place. Two movements add: the walk that has not finished (`vel`, which
    `Positions.move_toward` records and clears when the player arrives), and the step to the ball — `vol['step']`
    feet in `vol['t']` seconds, which is the lunge. Their sum is capped at what the legs can do, and the body then
    brakes at `A_STOP` until it is standing. The distance it takes to stop is the whole of the rule:

        carry = v² / (2 · A_STOP)

    A player standing still at 1 ft who takes a ball that comes to them is not carried anywhere, because they are
    not moving: that is what a foot path does that a stance could not. A player who arrives at the ball while
    still walking to the line is carried by however much of that walk was left. The return is (stop, velocity).
    """
    speed = movement_speed(p)
    # The step to the ball is **not** counted as speed, and the first version that did was wrong in a way worth
    # writing down: it divided the step by the time from the ball's strike to the contact, which for a fast ball
    # is a tenth of a second, so a one-foot step came out at ten feet per second and every volley in the game was
    # bowled into the kitchen (measured: contact speed 17.8 ft/s, the cap, at every stance). A lunge is a plant,
    # not a glide — you push off a foot and reach, and the body's momentum at a lunge is small. So the momentum is
    # the walk that has not finished, which the engine now tracks, and nothing invented from geometry.
    vx, vy = vel[0], vel[1]
    v = math.hypot(vx, vy)
    if v > speed:                                  # the legs, not the arithmetic, are the limit
        vx, vy = vx * speed / v, vy * speed / v
        v = speed
    if v <= 1e-9:
        return (vol["feet"][0], vol["feet"][1]), (0.0, 0.0)
    carry_ft = v * v / (2.0 * A_STOP)
    stop = (vol["feet"][0] + vx / v * carry_ft, vol["feet"][1] + vy / v * carry_ft)
    # a body cannot be carried through the net: the stride ends against it, and that is where the rule stops
    # caring, because a player inside the kitchen has already faulted. Never *backwards*, though — a player
    # already at the net is stopped by it where they stand, not pushed away from it.
    if p.north:
        stop = (max(vol["feet"][0], min(stop[0], NET_X - 0.5)), stop[1])
    else:
        stop = (min(vol["feet"][0], max(stop[0], NET_X + 0.5)), stop[1])
    return stop, (vx, vy)


# ---- the court, in feet ---------------------------------------------------------------------------
LENGTH, WIDTH = 44.0, 20.0
NET_X = LENGTH / 2                       # 22 ft, and the court is 20 ft wide
KITCHEN = 7.0                            # the non-volley zone, each side of the net
KITCHEN_LINE = NET_X - KITCHEN           # 15 ft from the north baseline; also a service area's short edge
BASELINE_N, BASELINE_S = 0.0, LENGTH
NET_CENTRE, NET_POSTS = 34 / 12, 36 / 12  # 2.83 ft in the middle, 3.00 ft at the posts (USA Pickleball)
SIDELINE_W, SIDELINE_E = 0.0, WIDTH
CENTRELINE = WIDTH / 2                   # 10 ft
RALLY_CAP = 120                          # a ceiling on the record, not a rule: if a rally reaches it, the
                                         # line says so rather than the game quietly ending it
NET_MARGIN = 0.7                         # ft of tape a player leaves when aiming: a shot that clears the net
                                         # by an inch is a shot nobody chooses, and a solver that returns one is
                                         # solving for the fault rather than for the court
WIND_CAP = 12.0                          # mph. The clock's own wind rule runs to 23 mph, and on a 25 g ball
                                         # that is not weather, it is a different game: measured, a 33 mph serve
                                         # reaches 49.5 ft in still air, 35.6 ft into a 12 mph headwind, and
                                         # 27.5 ft into 20 mph — short of the kitchen line, so no legal serve
                                         # exists at all. Capped, and the cap is printed with the session.
A_STOP = 32.0                            # ft/s2. How hard a player brakes once the ball has left the paddle.
                                         # A landing/plant, not a jog-down: two feet planted stop a body from a
                                         # 12mph run in about 1.5ft, which is a split step and is what the good
                                         # player does before a volley. A **declared guess** — the second in this
                                         # file after STRETCH_PENALTY — A/B'd in §5g. What it replaced was not a
                                         # guess but a fiction: a flat 1.5 ft carry applied to every volley taken
                                         # within 2 ft of the line, whatever the player was doing (page §5f: it
                                         # made a stance, rather than a movement, the offence).
WALK_SHARE = 0.6                         # of movement_speed: repositioning between shots is a jog, not a
                                         # sprint. Without it every volley is thrown into the kitchen, because a
                                         # player who walks to their stance at 12mph is carried 3.8ft by the
                                         # split step and the game has no volley in it — which is the same class
                                         # of defect as the old 1.5 ft carry, with the sign reversed.
STRETCH_PENALTY = 0.55                   # how much of the player's control a full-extension contact costs. Not
                                         # measured against anything yet: it is the one number in this file that is
                                         # a guess, and the page says so. A/B'd against 0.0 in §5d.
COMFORT = 0.55                           # fraction of the reach a player can use and still be balanced: inside
                                         # this the contact is not a stretch, beyond it the arm does the work
PADDLE_REACH = 6.0                       # ft the paddle covers beyond the feet, by the same construction as
                                         # tennis's 7: arm 2.5 + paddle 1.35 (a 15-17 in paddle) + lunge 2.2. The
                                         # first number I wrote was 3.0 — arm and paddle, lunge forgotten — and at 3 ft
                                         # 69% of rallies ended "nobody could reach it", which is not a hard game,
                                         # it is a game with one strategy. The reach is the *same* reach as tennis
                                         # to within a foot; the difference between the sports is where the feet are,
                                         # not how long the arm is.
                                         # deep ball out of the air, and further back lets it bounce

# The ball. Mass and size are the equipment standard's own range, mid-point taken: 2.87 in and 0.88 oz are
# both legal, and 0.88 oz rather than 0.78 oz lowers k by 13% — which is why the mass is printed with every
# session instead of being a constant somebody can quietly change.
BALL = {"make": "outdoor 40-hole", "diameter_in": 2.87, "mass_oz": 0.88, "holes": 40, "cd": 0.33,
        "cd_source": "Pickleball University / TWU 2025, 86 trajectories for the 40-hole ball"}
# RHO (slugs/ft³, sea level, 59 F) is imported rather than restated: it is the same air in both games, and a
# second copy of it is the defect the design page's §4 test exists to catch.
SLUGS_PER_KG = 14.5939029


def ball_geometry(ball: dict | None = None) -> tuple[float, float]:
    """Frontal area in ft² and mass in slugs, from the ball's own numbers."""
    b = BALL if ball is None else ball
    r = (b["diameter_in"] / 2) / 12
    return math.pi * r * r, (b["mass_oz"] * 0.0283495) / SLUGS_PER_KG


def drag_of(ball: dict | None = None) -> float:
    """k in a = k |v_rel| v_rel, per foot: ½ rho Cd A / m. One number, because the measured Cd is flat
    across the whole speed range the game uses — no drag crisis, so no table to interpolate."""
    b = BALL if ball is None else ball
    area, mass = ball_geometry(b)
    return 0.5 * RHO * b["cd"] * area / mass


DRAG = drag_of()
_AREAPB, _MASSPB = ball_geometry()
LIFT = 0.5 * RHO * _AREAPB / _MASSPB   # the same shell a tennis ball has; unused while spin is off

# The bounce. Restitution from the equipment standard's own drop test (30-34 in of rebound from a 78-in
# drop gives e = 0.62-0.66); friction is declared, not measured — a pickleball skids and does not grip like
# a tennis ball, and the page says so.
SURFACES = {
    "hard": {"e": 0.64, "f": 0.85, "note": "outdoor court: restitution from the USAP drop test, friction declared"},
    "indoor": {"e": 0.66, "f": 0.88, "note": "gym floor, mid-range of the same drop test"},
}


def wind_for(ms: int) -> tuple[str, float]:
    """The clock's wind, capped for this ball. One clock rule for both games (imported), one cap here."""
    direction, speed = wind_at(ms)
    return direction, min(speed, WIND_CAP)


def net_profile(y: float) -> float:
    """The net as the ball meets it: 2.83 ft at the centre, 3.00 ft at the posts."""
    return net_height(y, NET_CENTRE, NET_POSTS, WIDTH)


# ---- the rules, as predicates ----------------------------------------------------------------------
# Every rule below is a function of a position or a landing point. That is deliberate: a rule that cannot
# be asked a yes/no question cannot be tested, and a rule that is not tested is a comment.
def in_kitchen(x: float) -> bool:
    """Inside the non-volley zone, line included: |x - 22| <= 7. Volleying from here is a fault."""
    return abs(x - NET_X) <= KITCHEN


def feet_from_kitchen_line(x: float) -> float:
    """How far outside the kitchen line a player is. Negative is inside the kitchen."""
    return abs(x - NET_X) - KITCHEN


def in_bounds(land: tuple[float, float]) -> bool:
    """Any line is in, except the kitchen line on a serve — which is a separate test, below."""
    x, y = land
    return 0.0 <= x <= LENGTH and 0.0 <= y <= WIDTH


def in_service_area(land: tuple[float, float], server_north: bool, server_y: float) -> bool:
    """The serve must land in the diagonally opposite service area: past the kitchen line, inside the
    baseline, inside the sideline, and across the centreline from where the server stands.

    The kitchen line is the *short* boundary — this is the rule that makes a pickleball serve different
    from a tennis serve, where the service box starts at the net side and runs 21 ft from it."""
    x, y = land
    if not (0.0 <= y <= WIDTH):
        return False
    if server_north:
        deep = NET_X + KITCHEN < x <= LENGTH
    else:
        deep = BASELINE_N <= x < NET_X - KITCHEN
    across = (y - CENTRELINE) * (server_y - CENTRELINE) < 0
    return deep and across


def serve_side_y(team_north: bool, right: bool) -> float:
    """Where a server stands across the court. Facing north->south puts east on the server's left, so the
    right-hand court is y < 10 for the north end and y > 10 for the south end. The first version of the
    tennis engine had this backwards for both seats and every serve it reported was on the wrong side."""
    near, far = WIDTH * 0.25, WIDTH * 0.75
    if team_north:
        return near if right else far
    return far if right else near


def right_player_index(team: "Team") -> int:
    """Which partner is standing in the right-hand court: that team's first server when its score is even,
    the partner when it is odd. This is the whole of the doubles positioning rule, and it is *derived* from
    the score every time rather than stored — two copies of a position are two positions, and they drift."""
    return team.first_server if team.score % 2 == 0 else 1 - team.first_server


# ---- movement, contact, and the ball ---------------------------------------------------------------
CONTACT_HEIGHT = {"serve": 2.4, "groundstroke": 2.2, "volley": 3.2}
LAUNCH_BASE = {"serve": 3.0, "volley": 6.0}


def contact_point(p: Player, pos: tuple[float, float], shot: str) -> tuple[float, float, float]:
    """Where the paddle meets the ball: a fixed height by shot type and the player's own point on the
    court. A serve is struck below the waist, which is 2.4 ft on this rig; a volley is higher because the
    ball has not bounced."""
    return (pos[0], pos[1], CONTACT_HEIGHT[shot])


def launch_for(shot: str, face: float) -> float:
    """The paddle's face *is* the launch angle, plus the few degrees a ball gains coming off a flat face.
    A serve is struck from below the waist with an upward arc, so it starts higher than its face; a volley
    is struck down onto the ball. Bounded to what a paddle can do."""
    return max(-12.0, min(55.0, LAUNCH_BASE.get(shot, 2.0) + face))


def strike(p: Player, incoming: dict | None, face: float, power: float, aim: float, shot: str,
           surface: str, wind: tuple[float, float], pos: tuple[float, float] | None = None,
           clean: bool = False, stretch: float = 0.0) -> dict:
    """Movement in, ball out. Face in degrees, power in per cent, aim in feet across the court.

    Spin is off by decision, not by omission: the design page measures the fitted lift coefficient's effect
    at 0.83 degrees of launch, against a third-shot-drop window 0.5 degrees wide, so a term that uncertain
    would be a fiction with a coefficient. `cl` is therefore always 0 and every line says so.
    """
    control = p.skill("control")
    pace_in = (incoming or {}).get("speed_in", 20.0)          # mph; pickleball rallies are slower than tennis
    control *= 1 - 0.18 * min(1.0, pace_in / 45.0)            # a hard ball gives less time to set the paddle
    # ...and a ball met at the end of the reach is hit with the arm and not the body. `stretch` is 0 when the
    # feet are comfortably under the ball and 1 when the paddle is at full extension; it is the cost of arriving
    # late, and without it the engine has a perfect defence: on 2026-11-16 an honest receiving model produced
    # rallies that never ended because being stretched was free (page §5c). The penalty is on control, which is
    # where `strike` already puts every other human error, so a stretched ball is a *wider* ball and not a
    # weaker one — it goes out, or it sits up, and the rally can end.
    control *= 1 - STRETCH_PENALTY * max(0.0, min(1.0, stretch))
    pos = pos if pos is not None else (BASELINE_N + 1.0 if p.north else LENGTH - 1.0, CENTRELINE)

    if not clean:
        p.shots += 1
        if shot == "serve":
            p.serves += 1
    clean_hit = True if clean else p.rng.random() < p.skill("sweet")
    face_actual = face if clean else face + p.rng.gauss(0, 4.0 * (1 - control))
    power_actual = power if clean else power * (1 + p.rng.gauss(0, 0.10 * (1 - control)))
    if not clean_hit:                                        # the edge of the paddle, not its middle
        power_actual *= p.rng.uniform(0.55, 0.80)
        face_actual += p.rng.gauss(0, 7)
    # Power in per cent to ball speed in mph. 100 is a 60 mph serve, which is the top of the professional
    # range; 30 is an 18 mph dink. The page measures the driving game at 35-45 mph, i.e. power 58-75.
    speed = max(6.0, power_actual * 0.60)
    p0 = contact_point(p, pos, shot)
    elevation = math.radians(launch_for(shot, face_actual))
    # aim is absolute across the court, in feet from the west sideline, and the paddle turns to it: the
    # face sets the loft and the aim sets the direction, because a face that does both steers a serve thirty
    # feet wide (the tennis engine's first defect, 2026-11-04, kept out of here by construction).
    azimuth = math.atan2(aim - p0[1], 32.0)
    v = speed * MPH
    vx = v * math.cos(elevation) * math.cos(azimuth) * (1 if p.north else -1)
    vy = v * math.cos(elevation) * math.sin(azimuth)
    vz = v * math.sin(elevation)
    # The path is traced because the next player's volley decision needs the ball's flight *before* it bounces:
    # "can I take it out of the air" cannot be asked of a bounce point. One integrator, one call, a trace.
    traj = flight(p0, (vx, vy, vz), wind, surface, cl=0.0, drag=DRAG, lift=LIFT,
                  net_x=NET_X, surfaces=SURFACES, net_profile=net_profile, trace=0.02)
    return {"player": p, "shot": shot, "speed": speed, "sweet": clean_hit, "contact": p0, "traj": traj,
            "face": face_actual, "power": power_actual, "spin": 0.0, "ball": BALL["make"]}


def aim_at(p: Player, target: tuple[float, float], shot: str, surface: str, wind, power: float,
           pos: tuple[float, float]) -> float:
    """The face angle that sends the ball to a point.

    solved in two steps, because a plain bisection is unsound here and this is where that showed. Face ->
    landing distance is *not* monotone: it rises to a maximum near 40 degrees and then falls, so a bisection
    over the whole range can return a lob for a target the flat shot reaches — which is exactly what the first
    version did, and it sent every serve to +45 degrees and eleven feet wide. So:

      1. find the face of maximum range with a coarse scan, and bisect only below it, where the mapping is
         increasing and a player's flat solution lives;
      2. if that solution clears the net by less than `NET_MARGIN`, raise the face until it does. Aiming at the
         tape is not aiming at the court, and a solver that returns a tape-grazer is solving for the fault.

    The error is applied afterwards by `strike`, from the player's control, so every probe here is clean.
    """
    fwd = 1.0 if p.north else -1.0

    def land_x(face: float) -> float | None:
        probe = strike(p, None, face=face, power=power, aim=target[1], shot=shot, surface=surface,
                       wind=wind, pos=pos, clean=True)
        land = probe["traj"].get("land")
        return None if land is None else land[0]

    peak, best = 5.0, -1e9
    for f in range(5, 51, 2):
        x = land_x(float(f))
        if x is None:
            continue
        d = (x - pos[0]) * fwd
        if d > best:
            peak, best = float(f), d
    lo, hi = -15.0, max(peak, 5.0)
    for _ in range(22):
        mid = (lo + hi) / 2
        x = land_x(mid)
        if x is None:
            lo = mid                                  # in the net: hit up more
            continue
        if (x - target[0]) * fwd < 0:
            lo = mid                                  # short
        else:
            hi = mid
    face = (lo + hi) / 2
    for _ in range(8):                                # leave the tape alone
        probe = strike(p, None, face=face, power=power, aim=target[1], shot=shot, surface=surface,
                       wind=wind, pos=pos, clean=True)
        cross = probe["traj"].get("net")
        if not cross or cross[1] >= net_profile(cross[0]) + NET_MARGIN:
            break
        face += 1.0
    return face


def verdict(shot: dict) -> tuple[bool, str]:
    """In play or not, and a phrase a player can learn from. An out ball says how far out and which way,
    because a player learns by correcting a number, not by being told 'out'."""
    t = shot["traj"]
    p = shot["player"]
    fwd = 1 if p.north else -1
    if t.get("land") is None:
        if t.get("net"):
            tape = net_profile(t["net"][0])
            return False, (f"into the net at {t['net'][1]:.1f}ft, {tape - t['net'][1]:.1f}ft under the tape "
                           f"— needs more height")
        return False, "lost the ball"
    x, y = t["land"]
    if y < SIDELINE_W or y > SIDELINE_E:
        side = "west" if y < SIDELINE_W else "east"
        return False, f"wide by {abs(y - (SIDELINE_W if y < 0 else SIDELINE_E)):.1f}ft on the {side} sideline"
    if t["land"] is not None and ((p.north and x > LENGTH) or (not p.north and x < 0.0)):
        return False, f"long by {(x - LENGTH) if p.north else -x:.1f}ft past the baseline"
    depth = (NET_X - x) * fwd
    if depth > 0:
        return False, f"their own side of the net, {depth:.1f}ft short"
    return True, ("in the kitchen" if in_kitchen(x) else
                  f"{(LENGTH - x) if p.north else x:.0f}ft from their baseline")


# ---- the point: scoring, servers, and sides ---------------------------------------------------------
@dataclass
class Team:
    names: list[str]
    score: int = 0
    first_server: int = 0
    north: bool = True

    def partner_of(self, name: str) -> str:
        return self.names[1] if name == self.names[0] else self.names[0]


@dataclass
class Match:
    """A doubles game: side-out scoring to 11, win by 2, two servers a turn except the game's first.

    The state is small on purpose. Score, which team is serving, which of the two servers is up, and the
    identity of each team's first server. Court sides are *derived* from the score's parity, never stored.
    """
    teams: list[Team]
    serving: int = 0
    server_no: int = 0
    first_turn: bool = True
    target: int = 11
    log: list[str] = field(default_factory=list)

    def team(self, i: int) -> Team:
        return self.teams[i]

    def team_of(self, name: str) -> int:
        return 0 if name in self.teams[0].names else 1

    def side_of(self, name: str) -> str:
        """'right' or 'left' from the player's own facing — derived, so it cannot drift from the score."""
        t = self.teams[self.team_of(name)]
        idx = t.names.index(name)
        return "right" if idx == right_player_index(t) else "left"

    def server(self) -> str:
        t = self.teams[self.serving]
        return t.names[self.server_no]

    def server_y(self) -> float:
        return serve_side_y(self.teams[self.serving].north, self.side_of(self.server()) == "right")

    def receiver(self) -> str:
        """The diagonal opponent: the player in the opposite half of the receiving team."""
        recv = self.teams[1 - self.serving]
        server_right = self.side_of(self.server()) == "right"
        idx = right_player_index(recv)
        want = idx if server_right else 1 - idx      # right court serves to right court, across the line
        return recv.names[want]

    def point_to(self, team_i: int) -> str:
        """Award a rally and say what it did to the score, the servers and the sides."""
        if team_i == self.serving:
            t = self.teams[team_i]
            t.score += 1
            right = t.names[right_player_index(t)]
            self.log.append(f"point, {t.names[0]}/{t.names[1]} {t.score}-{self.teams[1 - team_i].score}; "
                            f"serve from {'right' if self.side_of(self.server()) == 'right' else 'left'} "
                            f"({right} on the right)")
            return "point"
        return self.side_out()

    def side_out(self) -> str:
        was = self.serving
        self.serving = 1 - self.serving
        self.server_no = 0
        self.first_turn = False
        self.log.append(f"side out, {self.teams[self.serving].names[0]}/{self.teams[self.serving].names[1]} "
                        f"serving ({self.server()}), from the right court")
        return "side out"

    def fault_by_serving(self) -> str:
        """The serving team faulted. First server -> the partner serves. Second server -> side out. And the
        game's first service sequence has **one** server, so a first-turn fault is a side out."""
        if self.first_turn:
            return self.side_out()
        if self.server_no == 0:
            self.server_no = 1
            self.log.append(f"second server: {self.server()} "
                            f"({'right' if self.side_of(self.server()) == 'right' else 'left'} court)")
            return "second server"
        return self.side_out()

    def over(self) -> bool:
        hi = max(t.score for t in self.teams)
        lo = min(t.score for t in self.teams)
        return hi >= self.target and hi - lo >= 2


def new_match(names: list[str]) -> Match:
    """Four seats, named, teams 1&2 against 3&4 in the order given, first server in the right court at 0-0.
    Fewer than four is a refusal: a doubles game with a hole in it is not a shorter game, it is another one."""
    if len(names) != 4:
        raise SystemExit(f"!! doubles needs exactly four names, given {len(names)}: {names}"
                         "\n   the seats are named, never indexed — see games/pickleball/README.md §3")
    t0 = Team(names=[names[0], names[1]], north=True, first_server=0)
    t1 = Team(names=[names[2], names[3]], north=False, first_server=0)
    return Match(teams=[t0, t1])


def serve_first(match: Match, first_team: int) -> None:
    """Which team serves first is decided before the first ball and written down. A season's later games
    alternate, because the record knows who served first last time; a season's first game is the first
    name's team, which is arbitrary, reproducible and printed."""
    match.serving = first_team
    match.log.append(f"serving first: {match.teams[first_team].names[0]}/"
                     f"{match.teams[first_team].names[1]} (game 1 of the season: the first name's team)")


# ---- one rally -------------------------------------------------------------------------------------
APPROACH_DEFAULT = 2.0                   # ft outside the player's own kitchen line that they hold. Two feet is
                                         # where the sport tells you to stand: close enough to take time away,
                                         # far enough that the follow-through does not carry you in.
APPROACH_MAX = 9.0                       # the deepest a frightened player will stand and still call it doubles
# The fault window, and why the default is outside it. A volley is taken with the feet planted (see
# `play_rally`), so the contact is where the player stands; the carry afterwards is 1.5 ft forward, so a player
# holding g feet behind the line is carried in for g < 1.5. A default of 2.0 is *outside* the window and one
# lesson (a foot, from 1.0) leaves it — which is the right shape for a rule: it bites a player who has gone to
# the line chasing a ball, not a player who is standing where the sport says to stand. The first version had
# the volley step 1.2 ft toward the net and put the default *inside* the window, so the engine manufactured a
# fault out of correct footwork: 540 carried-in volleys in twelve games, from a stance nobody would coach.


@dataclass
class Positions:
    """One point per player, not a body. Advanced toward the ball by `movement_speed`, which is the same
    function the tennis engine uses; that is what makes the kitchen a decision instead of a boundary.

    `approach` is the one number a player can change about *themselves*: how close to the kitchen line they
    stand after hitting. It lives here rather than in the chooser because the engine, not the chooser, moves
    the body — and a lesson that cannot move the body is not a lesson. A reader that has been carried into the
    kitchen by its own volley raises it; see `reading_chooser`."""
    at: dict[str, tuple[float, float]] = field(default_factory=dict)
    approach: dict[str, float] = field(default_factory=dict)
    stretch: dict[str, float] = field(default_factory=dict)
    vel: dict[str, tuple[float, float]] = field(default_factory=dict)

    def approach_of(self, p: Player) -> float:
        return self.approach.setdefault(p.name, APPROACH_DEFAULT)

    def stretch_of(self, p: Player) -> float:
        """0 when the feet are comfortably under the ball, 1 at full extension. Set when the player is put
        somewhere by `interception`, read when they strike."""
        return self.stretch.setdefault(p.name, 0.0)

    def home(self, p: Player) -> tuple[float, float]:
        """Where a player waits: a couple of feet behind their own kitchen line in a dink exchange, or on
        the baseline if they have just served or received — the engine starts everyone on the baseline."""
        x = -1.0 if p.north else LENGTH + 1.0        # behind the baseline: the serve is struck from there
        return (x, CENTRELINE)

    def get(self, p: Player) -> tuple[float, float]:
        return self.at.setdefault(p.name, self.home(p))

    def move_toward(self, p: Player, target: tuple[float, float], seconds: float) -> tuple[float, float]:
        """Walk, and remember whether the walk finished. A player who has arrived has stopped; a player who has
        run out of time is still going, at `movement_speed`, and that residual is what the momentum rule reads:
        the kitchen is a rule about a moving body, so the engine has to know which bodies are moving."""
        x, y = self.get(p)
        dx, dy = target[0] - x, target[1] - y
        d = math.hypot(dx, dy)
        reach = movement_speed(p) * WALK_SHARE * max(0.0, seconds)
        step = min(d, reach)
        if d > 1e-9:
            x, y = x + dx / d * step, y + dy / d * step
        self.at[p.name] = (x, y)
        left = d - step
        jog = movement_speed(p) * WALK_SHARE
        self.vel[p.name] = ((dx / d * jog, dy / d * jog) if d > 1e-9 and left > 0.25 else (0.0, 0.0))
        return self.at[p.name]

    def velocity_of(self, p: Player) -> tuple[float, float]:
        return self.vel.setdefault(p.name, (0.0, 0.0))


def play_rally(match: Match, players: dict[str, Player], pos: "Positions", choose, surface: str,
               wind_vec, wind_in, say=print, rally_no: int = 1,
               history: dict | None = None) -> dict:
    """One rally, from the serve to the first fault.

    Returns {shots, why, fault_by, winner}: `fault_by` is the team index that broke a rule (None if the point
    was won by a ball nobody could reach), and `winner` is the team the rally belongs to. Keeping those apart
    matters, because side-out scoring turns on *which* team faulted — a receiving team's fault is a point, a
    serving team's fault is a lost serve.

    The double-bounce rule is one monotone flag: `bounced_north`/`bounced_south` become true when the ball
    lands on that side, and `may_volley` is both of them. Before that, a volley is a fault. The kitchen is
    two tests on a position: at the volley's contact point, and on the step the follow-through takes.
    """
    bounced = {True: False, False: False}            # has the ball landed on that side, this rally
    shot_no = 0
    hitter = match.server()
    incoming = None
    history = history if history is not None else {}
    while True:
        p = players[hitter]
        hitter_team = match.team_of(hitter)
        may_volley = bounced[True] and bounced[False]
        here = pos.get(p)
        if shot_no == 0:                                  # the server stands on their service side, behind
            here = (-1.0 if p.north else LENGTH + 1.0, match.server_y())   # the baseline; the engine knows
            pos.at[p.name] = here                                          # which side from the score
        # THE BALL IN THE AIR, asked properly. `volley_contact` is tennis's own primitive — the same one the
        # tennis records are built from — and it answers the only question a volley asks: is the ball within the
        # paddle's reach at a hittable height *before it bounces*, and where are the feet when it is?
        #
        # The rule it replaces was a fiction in two halves. It asked whether the incoming ball would land DEEP
        # (`depth > 6`), so a short, high ball — exactly the ball a dink rally is waiting for — could never be
        # attacked, and a dink exchange could only end in an error. And it stepped the player 1.2 ft toward the
        # net to meet every ball in the air, which is not what a volley is: the ball comes to you. Both halves
        # are gone. Any ball that can be reached in the air is a volley; whether it is an attack or a dig is the
        # height's business and the player's nerve, not the engine's.
        vol = None
        if may_volley and shot_no > 0 and incoming and incoming.get("path"):
            vol = volley_contact(p, incoming["path"], at=here, reach=PADDLE_REACH,
                                 lo=VOLLEY_LOW, hi=VOLLEY_HIGH)
            if vol is not None and in_kitchen(vol["feet"][0]):
                vol = None                     # the feet would be in the kitchen: that is a fault, not a volley
        shot_kind = "serve" if shot_no == 0 else ("volley" if vol else "groundstroke")
        contact_pos = (vol["feet"][0], vol["feet"][1]) if vol else here
        # How stretched the contact is: a lunge for a volley, or the reach the receiving model left the feet at.
        stretch = min(1.0, vol["step"] / PADDLE_REACH) if vol else pos.stretch_of(p)
        if vol is not None:
            incoming = dict(incoming)
            incoming["volley_height"] = round(vol["height"], 2)   # the height is the attack's invitation
        face, power, aim = choose(p, players.get(_opponent_name(match, players, p.name)), incoming,
                                  shot_no, [], shot_kind, may_volley, contact_pos)
        shot = strike(p, incoming, face=face, power=power, aim=aim, shot=shot_kind, surface=surface,
                      wind=wind_vec, pos=contact_pos, stretch=stretch)
        pos.at[p.name] = contact_pos
        ok, why = verdict(shot)
        shot_no += 1
        history.setdefault(p.name, []).append(
            f"{shot_kind} face {shot['face']:+.1f} power {power:.0f} -> {why}")
        say(f"  {rally_no:2d}.{shot_no:<2d} {p.name:9s} {shot_kind if shot_kind != 'groundstroke' else 'shot':9s} "
            f"face {shot['face']:+5.1f} power {power:3.0f} aim {aim:2.0f} [{shot['speed']:.0f}mph] -> {why}")

        if shot_kind == "volley" and in_kitchen(contact_pos[0]):
            say(f"       -- fault: volleyed from inside the kitchen "
                f"({abs(contact_pos[0] - NET_X):.1f}ft from the net; the line is at {KITCHEN:.1f}ft)")
            return {"shots": shot_no, "why": "kitchen", "fault_by": hitter_team, "fault_name": p.name,
                    "fault_at": (round(contact_pos[0], 2), round(contact_pos[1], 2)),
                    "winner": 1 - hitter_team}
        if not ok:
            say(f"       -- {p.name} faulted: {why}")
            return {"shots": shot_no, "why": "out", "fault_by": hitter_team, "fault_name": p.name,
                    "winner": 1 - hitter_team}
        t = shot["traj"]
        land = t["land"]
        if shot_no == 1 and not in_service_area(land, p.north, contact_pos[1]):
            say(f"       -- fault: the serve did not land in the diagonal service area "
                f"(the kitchen line is at {KITCHEN_LINE:.0f}ft and {NET_X + KITCHEN:.0f}ft)")
            return {"shots": shot_no, "why": "serve", "fault_by": hitter_team, "fault_name": p.name,
                    "winner": 1 - hitter_team}
        bounced[not p.north] = True                  # it landed, so that side has had its bounce
        if shot_no == 1:
            receiver = match.receiver()
        else:
            receiver = _receiver_for(match, players, pos, land, hitter_team)
        rp = players[receiver]
        # THE BODY, not the ball's landing point. `interception` is tennis's own arithmetic — the same one the
        # renderer draws and the scoreline judges — asked with this sport's reach and with `frm`: where the
        # player is standing *right now*, because a player who has just hit from the forecourt is not on the
        # baseline. The feet come to rest where the legs brought them (`got`), never on the bounce point.
        # Before this line the engine assigned `pos.at[rp] = land`, i.e. it teleported the receiver onto the
        # ball and then asked whether a foot inside the kitchen is a fault. That is why the stance measured as
        # irrelevant (§5b): between shots the feet were not the player's.
        m = interception(rp, land, t["time"], t["bounce"], surface, frm=pos.get(rp), reach=PADDLE_REACH)
        if not m["ok"]:
            say(f"       -- point: {rp.name} is {m['why']}")
            return {"shots": shot_no, "why": "unreachable", "fault_by": None, "fault_name": receiver,
                    "why_not": m["why"], "winner": hitter_team}
        pos.at[rp.name] = m["got"]
        # Stretched means the ball is out towards the end of the paddle's reach: 0 with the feet under it, 1 at
        # full extension. This is the fact that was missing on 2026-11-16 — without it a player who arrives late
        # hits as well as a player who arrived early, and defence never breaks (page §5c).
        pos.stretch[rp.name] = max(0.0, min(1.0, (m["gap"] - COMFORT * PADDLE_REACH)
                                   / (PADDLE_REACH - COMFORT * PADDLE_REACH)))
        # ...and whatever time is left over is spent getting back to the stance. That leftover is the only
        # place the player's own number (`approach`) can act, and therefore the only place a lesson about the
        # kitchen can land: a player who arrives early chooses where to stand, a player who arrives late does not.
        spare = m["have"] - m["need"]
        if spare > 0.05:
            line_x = KITCHEN_LINE if rp.north else NET_X + KITCHEN
            gap = pos.approach_of(rp)
            want_x = line_x - gap if rp.north else line_x + gap
            pos.move_toward(rp, (want_x, pos.get(rp)[1]), spare)
        # the volley's momentum, from the body's own velocity rather than from where it is standing. The body
        # comes to rest at `stop`, and that is where it stands for the next shot — a carry of two feet is two
        # feet of ground it has to win back before it can volley again. The fault is the stop being inside the
        # kitchen: the rulebook's "carried in by the momentum of the shot", with the momentum computed.
        if shot_kind == "volley":
            stop, v = volley_carry(p, here, vol, pos.velocity_of(p))
            pos.at[p.name] = stop
            pos.vel[p.name] = (0.0, 0.0)           # the player is standing still when they stop
            if stop != (contact_pos[0], contact_pos[1]):
                say(f"       -- {p.name} is carried {math.hypot(stop[0] - contact_pos[0], stop[1] - contact_pos[1]):.1f}ft "
                    f"by the volley (leaving the paddle at {math.hypot(*v):.1f}ft/s, braking at {A_STOP:.0f}ft/s2), "
                    f"and stops {abs(stop[0] - NET_X):.1f}ft from the net")
            if in_kitchen(stop[0]):
                say(f"       -- fault: {p.name} was carried into the kitchen by the volley's momentum "
                    f"({abs(stop[0] - NET_X):.1f}ft from the net, inside the {KITCHEN:.0f}ft line) — "
                    f"the ball was already dead")
                return {"shots": shot_no, "why": "momentum", "fault_by": hitter_team, "fault_name": p.name,
                        "fault_at": (round(stop[0], 2), round(stop[1], 2)),
                        "at_contact": (round(contact_pos[0], 2), round(contact_pos[1], 2)),
                        "contact_speed": round(math.hypot(*v), 2),
                        "winner": 1 - hitter_team}
        # The hitter's own move, and the same rule as the receiver's: a player who is not hitting is walking to
        # their stance. The budget is this shot's own flight time — the time before the ball can possibly come
        # back — rather than the fixed 1.0 s the first version used, which was a number with no referent. It is
        # deliberately *one* rule stated twice rather than two behaviours that have to be kept in agreement.
        line_x = KITCHEN_LINE if p.north else NET_X + KITCHEN
        want_x = line_x - pos.approach_of(p) if p.north else line_x + pos.approach_of(p)
        if shot_kind != "volley" and abs(pos.get(p)[0] - want_x) > 0.25:
            pos.move_toward(p, (want_x, pos.get(p)[1]), t["time"])
        incoming = dict(t["bounce"])
        incoming["path"] = t.get("path")           # the flight, for the next player's volley decision
        incoming["speed_in"] = t["bounce"]["speed_out"] / MPH
        incoming["depth"] = abs(land[0] - NET_X)
        hitter = receiver
        if shot_no >= RALLY_CAP:
            say(f"       -- rally of {shot_no}; the record's ceiling, not the game's.")
            return {"shots": shot_no, "why": "cap", "fault_by": None, "fault_name": None, "winner": None}


def _opponent_name(match: Match, players: dict[str, Player], name: str) -> str:
    other = match.teams[1 - match.team_of(name)]
    return other.names[0]


def _receiver_for(match: Match, players: dict[str, Player], pos: "Positions",
                  land: tuple[float, float], hitter_team: int) -> str:
    """Which of the two opponents takes the ball. In V1 one player per contact, so it is the one standing
    nearer the landing point — a rule that needs no new state and gives the second body a defined absence."""
    team = match.teams[1 - hitter_team]
    def dist(n: str) -> float:
        x, y = pos.get(players[n])
        return math.hypot(x - land[0], y - land[1])
    return min(team.names, key=dist)


# ---- one game --------------------------------------------------------------------------------------
def play_game(names: list[str], practice: list[int], choose_factory, surface: str = "hard",
              wind_seed_ms: int | None = None, first_team: int = 0, say=print,
              stances: dict[str, float] | None = None) -> tuple[Match, dict]:
    """A doubles game to 11, win by 2. Every rule that decides the score is in `Match`; this function only
    feeds it rallies and prints what happened."""
    match = new_match(names)
    serve_first(match, first_team)
    ms = wind_seed_ms if wind_seed_ms is not None else int(datetime.now(timezone.utc).timestamp() * 1000)
    wind_in = wind_for(ms)
    wind_vec = wind_vector(*wind_in)
    # The hands are seeded from the same millisecond count as the wind, so a pinned clock reproduces a game
    # shot for shot. It did not, until this line: the record's header offered a replay command and two replays
    # gave 11-2 and 11-3, because `Player.rng` defaults to an unseeded Random. A transcript that cannot be
    # replayed is a story about a game.
    players = {}
    for i, n in enumerate(names):
        players[n] = Player(name=n, north=(i < 2), practice=practice[i], rng=random.Random(ms * 4 + i))
    # Per-player stances, so a lesson can be *held* by one seat and compared with another in the same game —
    # which is the only way to ask what a stance is worth without confounding it with the opponent.
    pos = Positions()
    if stances:
        pos.approach.update(stances)
    raw_dir, raw_speed = wind_at(ms)
    capped = f" (clock said {raw_speed:.0f}, capped at {WIND_CAP:.0f}: see the file's wind note)" \
        if raw_speed > WIND_CAP else ""
    say(f"  pickleball, doubles, {surface}; ball {BALL['make']} (Cd {BALL['cd']}, k {DRAG:.4f}/ft); "
        f"spin off; wind {wind_in[0]} {wind_in[1]:.0f}mph{capped}; clock {ms}")
    say(f"  teams: {names[0]}/{names[1]} (north) vs {names[2]}/{names[3]} (south); "
        f"to {match.target}, win by 2, side-out scoring")
    choose = choose_factory(players, wind_in, surface)
    history: dict[str, list[str]] = {n: [] for n in names}
    results = {n: [] for n in names}
    lengths = []
    rally_no = 0
    rallies: list[dict] = []
    while not match.over():
        rally_no += 1
        r = play_rally(match, players, pos, choose, surface, wind_vec, wind_in, say=say,
                       rally_no=rally_no, history=history)
        length = r["shots"]
        rallies.append(r)
        lengths.append(length)
        # A chooser that reads is a chooser with a lesson method: after the rally, it is told what happened and
        # is allowed to change the one thing a player can change about themselves — where they stand. The engine
        # still moves the body; a chooser with no `lesson` is simply never taught anything.
        lesson = getattr(choose, "lesson", None)
        if lesson is not None:
            lesson(r, pos, players)
        serving_team = match.serving
        # whose serve this rally was: a fault by the serving team costs the serve, a fault by the receiver costs a
        # point, and side-out scoring makes those two very different prices for the same mistake. The record has
        # to be able to say which one it was (page §5g measures the kitchen's fault in that currency).
        r["serving_at"] = serving_team
        if r["fault_by"] is None and r["winner"] is None:          # the record's ceiling: no score either way
            outcome = "no score (ceiling)"
        elif r["fault_by"] == serving_team:
            outcome = match.fault_by_serving()                     # a serving fault: lose the serve
        else:
            outcome = match.point_to(serving_team)                 # the receiver faulted: a point
        say(f"       -- {outcome}")
        say(f"    {match.teams[0].names[0]}/{match.teams[0].names[1]} {match.teams[0].score} - "
            f"{match.teams[1].score} {match.teams[1].names[0]}/{match.teams[1].names[1]}   "
            f"{'serving: ' + match.server() if not match.over() else 'game'}")
        if rally_no > 200:
            say("  !! 200 rallies and no winner: the engine has a defect, not the players")
            break
    winner = 0 if match.teams[0].score > match.teams[1].score else 1
    kinds: dict[str, int] = {}
    for r in rallies:
        kinds[r["why"]] = kinds.get(r["why"], 0) + 1
    say(f"  faults: " + (", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) or "none"))
    say(f"  game: {match.teams[winner].names[0]}/{match.teams[winner].names[1]} "
        f"{match.teams[winner].score}-{match.teams[1 - winner].score} "
        f"({rally_no} rallies, mean {sum(lengths) / len(lengths):.1f} shots)")
    # `rallies` is the game's own history — every rally's {shots, why, fault_by, fault_name, winner} — so a
    # chooser can read what it did rather than be told. §5 of the page records the fault I measured with it.
    return match, {"results": results, "lengths": lengths, "wind": wind_in, "clock": ms,
                   "surface": surface, "why": r["why"] if lengths else "none",
                   "rallies": rallies}


# ---- the seats: a scripted player, a member, or a person --------------------------------------------
def scripted_chooser(level: str = "steady"):
    """A chooser with no engine behind it, so the rules can be played without a key. It is a *test harness*
    and the line says so: `level` picks how well it aims, not how well it thinks."""
    def factory(players, wind_in, surface):
        wanted = {"steady": (0.65, 42.0), "beginner": (0.35, 30.0), "hard": (0.85, 48.0)}[level]

        def choose(p, other, incoming, shot_no, lengths, shot_kind, may_volley, here):
            share, base_power = wanted
            # the target: for a serve, the diagonal service area; otherwise a point drawn toward the
            # kitchen line if the ball is high, deep if it is not. A harness that only ever aims at the
            # middle would never fault, and a game nobody faults is a measurement of nothing.
            if shot_kind == "serve":
                across = WIDTH * 0.75 if here[1] < CENTRELINE else WIDTH * 0.25
                # 11 ft past the net, on the DIAGONAL side, and turned into an x for the end serving — the
                # same defect as the groundstroke target below, and the reason a south server lost every game
                target = ((NET_X + 11.0) if p.north else (NET_X - 11.0), across)
            else:
                # depth is measured from the hitter's OWN baseline, so it has to be turned into an x for the
                # end they are playing from. The first version passed a raw x, which sent every south-end
                # shot back into the south end's own court: the north team won 11-0 twice before I looked.
                depth = 26.0 if shot_kind == "volley" else 24.0 + 8.0 * p.rng.random()
                tx = depth if p.north else LENGTH - depth
                target = (tx, CENTRELINE + p.rng.uniform(-7, 7))
            power = {"serve": 55.0, "volley": base_power + 8.0}.get(shot_kind, base_power)
            face = aim_at(p, target, shot_kind, surface, wind_vector(*wind_in), power, here)
            # aim jitter stands in for intent; the hands' own error is applied by `strike`
            # the harness aims exactly; the hands' own error is applied by `strike`, which is where it
            # belongs. A jitter here would be a second, invisible error on top of the first.
            return face, power, target[1]
        return choose
    return factory


def reading_chooser(level: str = "steady", say=print):
    """The first chooser in this game that reads what it did, and the first thing in pickleball worth learning.

    Every chooser before this one is blind. It aims, the ball goes, a rule fires, and the next rally starts with
    the fault forgotten — so a scripted player can be carried into the kitchen forty times in a game and hold the
    same stance on the last point as on the first. This one is handed each rally (`play_game` calls its `lesson`)
    and it changes the one thing a player can change about *themselves*: `Positions.approach`, the feet between
    their own kitchen line and their feet.

    What it does not do, and why, because the omissions are the design:
      - it does not compute the safe distance. The arithmetic is in the comment above `APPROACH_DEFAULT` and it
        is one line; a player that derives it is a calculator, and a lesson that arrives without a fault is a
        lesson about nothing. It steps back one foot per fault and finds out.
      - it does not step *forward* again when the faults stop. A real player drifts to the line because the line
        takes time away from the opponent, and modelling that temptation would need the opponent's reply as a
        reward — which is the next unit, not this one. So the number is monotone, and that is stated.
      - the kitchen fault at contact and the momentum fault after it are the same mistake about the same square
        foot of ground, so both are read. The serve fault, the out ball and the unreachable ball are not: they
        are about hands, power and legs, and a lesson about the kitchen that taught those would be teaching noise.
    """
    base = scripted_chooser(level)
    STEP = 1.0                            # ft per fault: one step back, like a person, not a solver
    STANCE_TOL = 0.6                      # ft: a fault taken from within this of the mark is the stance's fault

    def factory(players, wind_in, surface):
        choose = base(players, wind_in, surface)
        lessons: dict[str, list[str]] = {}

        def lesson(r, positions, roster):
            if r.get("why") not in ("momentum", "kitchen"):
                return
            name = r.get("fault_name")
            if not name or name not in roster:
                return
            p = roster[name]
            before = positions.approach_of(p)
            # Whose fault was it — the stance or the chase? A player who was standing on their own mark and got
            # carried in has a stance problem, and stepping back is the answer. A player who arrived at the line
            # chasing a ball that landed there and volleyed it from 0.2ft outside has a *chase* problem, and
            # stepping their mark back would not have touched it: their feet were never at the mark. Without this
            # test the number climbs to the ceiling as a standing apology for faults it cannot fix.
            line_x = KITCHEN_LINE if p.north else NET_X + KITCHEN
            mark_x = line_x - before if p.north else line_x + before
            at = r.get("fault_at")
            if at is not None and abs(at[0] - mark_x) > STANCE_TOL:
                say(f"       == {name} reads its own fault ({r['why']}) and it was not the stance: it was "
                    f"{abs(at[0] - line_x):.1f}ft from its own line, having gone to the ball. Nothing changes.")
                return
            after = min(APPROACH_MAX, before + STEP)
            positions.approach[name] = after
            if after == before:               # already as far back as it will go: say so, do not pretend
                say(f"       == {name} has nowhere further back to stand ({after:.0f}ft, the ceiling)")
                return
            say(f"       == {name} reads its own fault ({r['why']}): {before:.0f}ft behind the line was too "
                f"close. Standing {after:.0f}ft back from here.")
            lessons.setdefault(name, []).append(f"{r['why']} at {before:.0f}ft -> {after:.0f}ft")

        choose.lesson = lesson
        choose.lessons = lessons
        return choose
    return factory


def points_chooser(level: str = "steady", say=print, settle: int = 8, margin: float = 0.15,
                   band: float = 3.0, need: int = 3, explore_every: int = 10):
    """A chooser paid in **points**, not in faults — the two-sided lesson §5d said was next.

    `reading_chooser` reads the record for faults, and a fault is a thing you can see and count: it steps back
    a foot whenever it is carried into the kitchen, and it never steps forward, because nothing in a fault ever
    says *close the gap*. That lesson is one-directional and it walks away from the line, which is where the
    sport tells you to stand. This one is paid in the only currency the game actually keeps: who won the point.

    How it learns, stated plainly because it is crude:
      - after every rally each player records the result at the stance they were holding, in one-foot buckets;
      - every `settle` rallies each player looks at the buckets within `band` feet of where they are, keeps the
        ones with at least `need` rallies, and takes one step of a foot toward the best win rate — but only if
        it beats their current bucket by `margin`, so a coin-flip does not move a professional;
      - it moves one foot at a time and it can move both ways, which is the whole difference from the fault
        reader;
      - and it **explores**, which was the first version's mistake: a chooser that only moves toward a better
        measured stance never measures anything, because at the start every player holds the same stance and
        the ledger has one bucket in it. Every `explore_every` rallies a player takes one step toward a
        neighbouring stance it has not yet tried `need` times. A lesson that never tries anything learns only
        about where it started.

    What it cannot do, measured rather than asserted: **it loses to doing nothing.** In head-to-head play from
    the same starting stance (practice 200, both sides at 4 ft, the learner on one side and a static player on
    the other, swapped over the same pins) the learner took 61 points to the static player's 77 and lost 2
    games to 6. The currency is right and the sample is not: a game is 30-50 rallies shared between four
    players and four buckets, so a bucket holds two or three rallies, and the win rate in it is dominated by
    whether the player happened to be serving, and by the fact that both teams are moving at once. A lesson is
    only worth its noise when it has more samples per decision than the noise has causes; the season file
    (`--season`, hundreds of rallies) is where that lives, and this ledger is per game until it is wired.

    The measurement behind it (page §5e): in head-to-head play at practice 200, a 2 ft stance beat 4 ft by
    99-76 points and 6 ft by 101-48, while the *fault* count said 4 ft was better by 22 to 2. The two
    currencies disagree, and only one of them is the score.
    """
    base = scripted_chooser(level)
    STEP = 1.0

    def factory(players, wind_in, surface):
        choose = base(players, wind_in, surface)
        ledger: dict[str, dict[int, list[int]]] = {}
        lessons: dict[str, list[str]] = {}
        count = {"rallies": 0}

        def lesson(r, positions, roster):
            count["rallies"] += 1
            winner = r.get("winner")
            for name, p in roster.items():
                bucket = int(round(positions.approach_of(p)))
                rec = ledger.setdefault(name, {}).setdefault(bucket, [0, 0])
                rec[1] += 1
                if winner is not None and (0 if p.north else 1) == winner:
                    rec[0] += 1
            # Exploration first: a step toward a neighbour nobody has measured yet. Without this the ledger
            # only ever holds the starting stance and the greedy step below has nothing to prefer.
            if count["rallies"] % explore_every == 0:
                for name, p in roster.items():
                    now = positions.approach_of(p)
                    unseen = [b for b in (int(round(now)) - 1, int(round(now)) + 1)
                              if 1.0 <= b <= APPROACH_MAX
                              and ledger.get(name, {}).get(b, [0, 0])[1] < need]
                    if not unseen:
                        continue
                    positions.approach[name] = float(unseen[0])
                    say(f"       == {name} tries {unseen[0]}ft: a lesson that never tries anything learns only "
                        f"about where it started")
            if count["rallies"] % settle:
                return
            for name, p in roster.items():
                now = positions.approach_of(p)
                here = ledger.get(name, {})
                current = here.get(int(round(now)), [0, 0])
                current_rate = (current[0] / current[1]) if current[1] else 0.0
                best = None
                for bucket, (wins, played) in here.items():
                    if played < need or abs(bucket - now) > band:
                        continue
                    rate = wins / played
                    if best is None or rate > best[1] + 1e-9:
                        best = (bucket, rate)
                if best is None or best[1] <= current_rate + margin:
                    continue
                target = max(1.0, min(APPROACH_MAX, now + (STEP if best[0] > now else -STEP)))
                if abs(target - now) < 1e-9:
                    continue
                positions.approach[name] = target
                said = (f"{name}: {best[0]}ft won {best[1]:.0%} of its rallies, "
                        f"{now:.0f}ft won {current_rate:.0%}")
                say(f"       == {name} is paid in points — {said}. Standing {target:.0f}ft back.")
                lessons.setdefault(name, []).append(said)

        choose.lesson = lesson
        choose.ledger = ledger
        choose.lessons = lessons
        return choose
    return factory


# ---- the season-shaped lesson ---------------------------------------------------------------------
# §5e's rule was "a lesson is only worth its noise when it has more samples per decision than the noise has
# causes", and the point lesson failed its own rule for an arithmetic reason: a game is 30-50 rallies *shared*
# between four players and four one-foot buckets, so the bucket a player stood in held two or three rallies, and
# the win rate in it turned on who happened to be serving. The fix is not a better estimator — it is a bigger
# unit. Hold the stance for a whole game, so one bucket collects that game's thirty-odd rallies into ONE
# decision, and keep the buckets in the season file, so a dozen games are a sample that outnumbers the causes
# of the noise. That is this section, and `--level season` is how it is played.
#
# Two things it does not do, stated because they are the design:
#   - it credits a rally to a player whose *team* won it, so a learner's number is half its partner's when the
#     partner is not learning. True of the sport (a doubles point is a team's point) and the reason the
#     head-to-head below puts both members of one team in the lesson;
#   - it cannot see the opponent. A stance is worth what the opponent cannot reach, and this lesson only knows
#     what its own team scored — which is the whole of what a player knows at the end of a game.

STANCE_FILE = "stance.json"          # one file, in the season's own directory: a record of decisions, not a
                                     # rating. `practice.json` is the engine's; this is the lesson's.


def stance_paths(season: str, override: str | None = None) -> tuple[Path, Path]:
    """Where the lesson's book lives. The same directory as the season, because a lesson that outlives a game
    belongs to the season and not to the process: it has to survive the command line that made it."""
    d, _ = season_paths(season, override, "pickleball")
    return d, d / STANCE_FILE


def load_stance_ledger(season: str, override: str | None = None) -> dict:
    _, f = stance_paths(season, override)
    if not f.exists():
        return {"season": season, "note": "", "members": {}}
    return json.loads(f.read_text(encoding="utf-8"))


def save_stance_ledger(book: dict, season: str, override: str | None = None) -> Path:
    d, f = stance_paths(season, override)
    d.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(book, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return f


class SeasonLesson:
    """A lesson whose unit is a game and whose memory is a season.

    Each learner holds one stance for a whole game. When the game ends the rallies are counted into the bucket
    the learner stood in — `{won, played, games}` — and the next stance is decided by three rules in order.
    The currency is **rallies won**, not points: side-out scoring means a rally won is a point when you serve
    and the serve when you receive, so the scoreline is a nonlinear function of the thing a stance actually
    changes. Rallies it is, and the page says so.

      1. **sample where you stand.** A bucket with fewer than `need_games` games has a win rate that is a coin
         flip wearing a percentage sign, and a lesson that moves on a coin is §5e's point lesson again. Hold.
      2. **move one foot toward a bucket that has beaten you by `margin`.** Both directions, so the lesson can
         walk to the line as well as away from it — which the fault reader cannot, because no fault ever says
         *close the gap*.
      3. **if nothing has beaten you, measure somewhere new.** A neighbour with fewer than `need_games` games
         is visited; ties are broken by the season's own coin (the parity of the learner's games), so the
         search order is not told where the answer is. A lesson that never tries anything learns only about
         where it started.

    What it is not: an optimiser. It takes one step per game because a person does, and its margin is 8 points
    of win rate because a game's worth of rallies is still a noisy estimate. Whether eight is enough is a
    measurement, and the number is on the page.
    """

    def __init__(self, season: str, names: list[str], learners: tuple[str, ...] | list[str] | None = None,
                 start: float | None = None, need_games: int = 3, margin: float = 0.08, band: float = 2.0,
                 override: str | None = None, say=print):
        self.season = season
        self.names = list(names)
        self.learners = tuple(learners) if learners else tuple(names)
        self.need_games = need_games
        self.margin = margin
        self.band = band
        self.override = override
        self.say = say
        self.book = load_stance_ledger(season, override)
        self.book.setdefault("members", {})
        for n in self.learners:
            m = self.book["members"].setdefault(
                n, {"held": float(APPROACH_DEFAULT if start is None else start), "games": 0, "buckets": {}})
            m.setdefault("buckets", {})
            m.setdefault("games", 0)
        self.log: list[str] = []

    # -- the book, per learner ----------------------------------------------------------------------
    def member(self, name: str) -> dict:
        return self.book["members"][name]

    def held(self, name: str) -> float:
        return float(self.member(name)["held"])

    def buckets(self, name: str) -> dict[str, dict]:
        return self.member(name).setdefault("buckets", {})

    def _rec(self, name: str, bucket: int) -> dict:
        return self.buckets(name).setdefault(str(bucket), {"won": 0, "played": 0, "games": 0})

    def _seen(self, name: str, bucket: int) -> dict:
        """Read a bucket without creating it. A book that grows rows for stances nobody ever held is a book
        that flatters its own thoroughness: `--report` would list 9 ft as tried."""
        return self.buckets(name).get(str(bucket), {"won": 0, "played": 0, "games": 0})

    # -- the decision, made once per game -----------------------------------------------------------
    def stances(self) -> dict[str, float]:
        return {n: self._decide(n) for n in self.learners}

    def _decide(self, name: str) -> float:
        m = self.member(name)
        held = float(m["held"])
        here = self._rec(name, int(round(held)))
        if here.get("games", 0) < self.need_games:                 # rule 1: no coin flips
            return held
        my_rate = here["won"] / here["played"] if here["played"] else 0.0
        measured = []
        for key, rec in self.buckets(name).items():
            if rec.get("games", 0) < self.need_games or abs(int(key) - held) > self.band:
                continue
            measured.append((rec["won"] / rec["played"] if rec["played"] else 0.0, int(key)))
        measured.sort(reverse=True)
        if measured and measured[0][1] != int(round(held)) and measured[0][0] > my_rate + self.margin:
            best_rate, best_b = measured[0]
            target = held + (1.0 if best_b > held else -1.0)       # rule 2: one step, not a solver's jump
            self.say(f"       == {name} is paid in games — {best_b}ft won {best_rate:.0%} of its rallies, "
                     f"{held:.0f}ft won {my_rate:.0%}. Standing {target:.0f}ft behind the line.")
            self.log.append(f"{name}: {best_b}ft {best_rate:.0%} beats {held:.0f}ft {my_rate:.0%} -> "
                            f"{target:.0f}ft")
            return target
        # rule 3: measure a neighbour. Ties are broken by the season's coin, so the order the buckets are
        # visited in carries no knowledge of which end is good.
        coin = (1.0, -1.0) if m.get("games", 0) % 2 == 0 else (-1.0, 1.0)
        todo = [b for b in (held + s for s in coin) if 1.0 <= b <= APPROACH_MAX]
        todo.sort(key=lambda b: (self._seen(name, int(round(b)))["games"], abs(b - held)))
        if todo and self._seen(name, int(round(todo[0])))["games"] < self.need_games:
            pick = float(int(round(todo[0])))
            self.say(f"       == {name} has measured {int(round(held))}ft for {here['games']} games; nothing "
                     f"has beaten it by {self.margin:.0%}, so it measures {pick:.0f}ft instead.")
            self.log.append(f"{name}: explore {int(round(held))}ft -> {pick:.0f}ft")
            return pick
        return held

    # -- the game's result, counted once per game ---------------------------------------------------
    def record(self, match, rallies: list[dict], stances: dict[str, float]) -> None:
        for name in self.learners:
            if name not in stances:
                continue
            bucket = int(round(stances[name]))
            rec = self._rec(name, bucket)
            team = match.team_of(name)
            for r in rallies:
                if r.get("winner") is None:                        # the record's ceiling: no score either way
                    continue
                rec["played"] += 1
                if r["winner"] == team:
                    rec["won"] += 1
            rec["games"] += 1
            m = self.member(name)
            m["held"] = float(bucket)
            m["games"] = m.get("games", 0) + 1

    def save(self) -> Path:
        self.book["season"] = self.season
        return save_stance_ledger(self.book, self.season, self.override)

    # -- what the season says so far ----------------------------------------------------------------
    def table(self, title: str = "") -> str:
        lines = [title] if title else []
        for name in self.learners:
            m = self.member(name)
            lines.append(f"  {name}: {m.get('games', 0)} games, holding {self.held(name):.0f}ft behind the line")
            for key in sorted(self.buckets(name), key=int):
                rec = self.buckets(name)[key]
                rate = rec["won"] / rec["played"] if rec["played"] else 0.0
                mark = " <-" if int(key) == int(round(self.held(name))) else ""
                lines.append(f"    {int(key):2d}ft  {rec['games']:2d} games  {rec['played']:3d} rallies  "
                             f"won {rec['won']:3d}  {rate:5.1%}{mark}")
        return "\n".join(lines)


def play_season(names: list[str], practice: list[int], lesson: SeasonLesson, choose_factory, games: int,
                surface: str = "hard", clock: int | None = None, first_team: int = 0, say=print,
                static: dict[str, float] | None = None) -> dict:
    """A season is a loop of games, and the only thing that carries between them is the lesson's book.

    `static` pins the stances of players who are *not* learning, which is what makes a head-to-head possible:
    the same pinned clocks played twice, once with a team learning and once with the same team standing still.
    The clock advances one millisecond per game, so a season is a season of different winds and not one
    afternoon repeated — and the clock of every game is printed, so any game in the record can be replayed.
    """
    wins = {0: 0, 1: 0}
    points = [0, 0]
    rows: list[dict] = []
    for g in range(games):
        stances = lesson.stances()
        if static:
            for n in names:
                if n not in lesson.learners:
                    stances[n] = float(static.get(n, APPROACH_DEFAULT))
        ms = None if clock is None else clock + g
        say(f"\n-- game {g + 1} of the season " +
            " ".join(f"{n} {stances[n]:.0f}ft" for n in names if n in stances))
        match, result = play_game(names, practice, choose_factory, surface=surface, wind_seed_ms=ms,
                                  first_team=(first_team + g) % 2, say=say, stances=stances)
        lesson.record(match, result["rallies"], stances)
        lesson.save()
        w = 0 if match.teams[0].score > match.teams[1].score else 1
        wins[w] += 1
        points[0] += match.teams[0].score
        points[1] += match.teams[1].score
        rows.append({"game": g + 1, "stances": dict(stances), "clock": ms, "winner": w,
                     "score": (match.teams[0].score, match.teams[1].score)})
    say("")
    say(lesson.table(f"  the season's book after {games} games:"))
    say(f"  games won: {names[0]}/{names[1]} {wins[0]}, {names[2]}/{names[3]} {wins[1]}; "
        f"points {points[0]}-{points[1]}")
    return {"wins": wins, "points": points, "rows": rows, "lesson": lesson}


def make_chooser(level: str):
    """A demo's chooser. `read` and `learn` are the steady player's hands with a lesson attached — the first
    paid in faults, the second in points — so a difference between them and `--level steady` is the learning
    and never the aim."""
    if level == "read":
        return reading_chooser("steady")
    if level == "learn":
        return points_chooser("steady")
    return scripted_chooser(level)


def member_chooser_pb(engines: dict, surface, wind_in, history, fell_back):
    """The shot a member chooses, asked of its own engine. Mirrors the tennis `member_chooser` contract:
    one prompt, one line, and a named fallback when a being writes prose instead of a movement."""
    def choose(p, other, incoming, shot_no, lengths, shot_kind, may_volley, here):
        vendor, key, model = engines[p.name]
        prompt = rally_prompt_pb(p, other.name if other else "your opponent", history.get(p.name, []),
                                 incoming, surface, wind_in, shot_no, shot_kind, may_volley, here)
        from tennis import ask, BASES  # noqa: E402  the vendor table, one hop, not a copy
        reply = ask(BASES[vendor], key, model, prompt, 0.7)
        cmd = parse_command(reply)
        if cmd is None:
            fell_back.append(reply)
            print(f"  !! {p.name} wrote no usable line ({reply.strip()[:60]!r}); the ball is played straight.")
            face = aim_at(p, (24.0, CENTRELINE), "groundstroke", surface, wind_vector(*wind_in),
                          45.0, here)
            cmd = (face, 45.0, CENTRELINE)
        return cmd
    return choose


def rally_prompt_pb(p: Player, other: str, history: list[str], incoming: dict | None, surface: str,
                    wind_in, shot_no: int, shot_kind: str, may_volley: bool, here) -> str:
    """What a member is told before it swings. The kitchen and the double bounce are stated because they are
    the two things that make this game different from the one it may have played before."""
    lines = [
        f"It is your shot in a doubles pickleball game. You are {p.name}, at the "
        f"{'north' if p.north else 'south'} end, standing {abs(here[0] - NET_X):.1f}ft from the net.",
        f"The court is 44ft by 20ft. The kitchen (non-volley zone) is 7ft either side of the net at x=22: "
        f"you may not volley a ball while standing inside it, and your own momentum carrying you in after a "
        f"volley is also a fault.",
        ("Both sides have bounced the ball, so you may volley." if may_volley else
         "The ball has not bounced on both sides yet, so a volley is a fault: let it bounce."),
        f"Surface {surface}, wind {wind_in[0]} {wind_in[1]:.0f}mph. This is shot {shot_no + 1} of the rally, "
        f"and it is {a_or_an(shot_kind)} {shot_kind}.",
    ]
    if incoming:
        lines.append(f"The ball is coming off a bounce at {incoming.get('speed_in', 0):.0f}mph, "
                     f"{incoming.get('depth', 0):.0f}ft from the net.")
    if history:
        lines.append("Your last shots: " + " | ".join(history[-2:]))
    lines += [
        "",
        "Answer in one line, exactly this shape:",
        "FACE <degrees> POWER <30-100> AIM <feet from the west sideline>",
        "FACE opens the paddle and launches the ball higher; it closes it and drives it down. POWER 30 is a "
        "dink at 18mph, 100 is a 60mph drive. AIM 4 and 16 are near the sidelines, 10 is the middle. "
        "A serve must land past the kitchen line, diagonally, and you get one attempt.",
        "",
        "Your hands are not exact and a fast ball gives you less time, so what you get is not quite what you "
        "chose. Read your own history and decide what to change.",
    ]
    return "\n".join(lines)


def a_or_an(word: str) -> str:
    return "an" if word[0] in "aeiou" else "a"


# ---- the command line ------------------------------------------------------------------------------
def cmd_rules(argv) -> int:
    """Every rule in this file, fired once, with the number it produces. A rule that cannot be printed as a
    result is a rule nobody can check."""
    say = print
    say("== the ball ==")
    area, mass = ball_geometry()
    say(f"  {BALL['make']}: {BALL['diameter_in']}in, {BALL['mass_oz']}oz, {BALL['holes']} holes, "
        f"Cd {BALL['cd']} -> area {area:.5f}ft2, mass {mass:.6f} slugs")
    from tennis import DRAG as TENNIS_DRAG
    say(f"  k = 0.5*{RHO}*{BALL['cd']}*{area:.5f}/{mass:.6f} = {DRAG:.5f}/ft "
        f"(tennis {TENNIS_DRAG:.4f}; the ratio is {DRAG / TENNIS_DRAG:.2f}x)")
    say("\n== the kitchen ==")
    for x in (14.9, 15.0, 15.1, 20.0, 22.0, 29.0, 29.1):
        say(f"  x={x:5.1f}: in_kitchen={in_kitchen(x)}  feet outside the line: "
            f"{feet_from_kitchen_line(x):+.1f}")
    say("\n== the serve, one diagonal, past the kitchen line ==")
    for land, ny, sy, note in (((30.0, 14.0), True, 5.0, "past the line, diagonal: good"),
                               ((28.0, 14.0), True, 5.0, "on the kitchen line: short, fault"),
                               ((30.0, 6.0), True, 5.0, "same side as the server: fault"),
                               ((43.9, 14.0), True, 5.0, "inside the baseline by a foot: good"),
                               ((44.5, 14.0), True, 5.0, "past the baseline: fault")):
        say(f"  land {land}, server at y={sy}: {in_service_area(land, ny, sy)!s:5s}  {note}")
    say("\n== the doubles assignment ==")
    m = new_match(["A", "B", "C", "D"])
    serve_first(m, 0)
    for sc in (0, 1, 2, 3):
        m.teams[0].score = sc
        right = m.teams[0].names[right_player_index(m.teams[0])]
        say(f"  team score {sc}: first server {m.teams[0].names[m.teams[0].first_server]} is in the right "
            f"court -> {right} on the right, {m.teams[0].partner_of(right)} on the left")
    m.teams[0].score = 0
    say(f"  server {m.server()} stands at y={m.server_y():.1f} (right-hand court); receiver is {m.receiver()}")
    say("\n== the two servers, and the first turn ==")
    for i in range(3):
        before = (m.serving, m.server_no, m.first_turn)
        out = m.fault_by_serving()
        say(f"  fault {i + 1}: serving={before[0]} server_no={before[1]} first_turn={before[2]} -> {out}; "
            f"now serving={m.serving} server_no={m.server_no}")
    say("\n== side-out scoring ==")
    m2 = new_match(["A", "B", "C", "D"]); serve_first(m2, 0)
    say(f"  serving team scores: {m2.point_to(0)} -> {m2.teams[0].score}-{m2.teams[1].score}")
    say(f"  receiving team 'scores' nothing: {m2.point_to(1)} -> {m2.teams[0].score}-{m2.teams[1].score} "
        f"(serving={m2.serving} now)")
    say("\n== the double bounce rule ==")
    say("  bounces = {north: n, south: n}; may_volley = both >= 1")
    for b in ((0, 0), (1, 0), (1, 1)):
        say(f"  bounces north={b[0]} south={b[1]}: may_volley={b[0] >= 1 and b[1] >= 1} -> "
            f"a volley is {'legal' if b[0] >= 1 and b[1] >= 1 else 'a fault (volleyed before the bounce)'}")
    say("\n== the driving game's window (the page's table, recomputed from this file's own constants) ==")
    page = {35.0: 10.1, 40.0: 5.9, 45.0: 3.5}
    for mph in (35.0, 40.0, 45.0):
        runs, start, prev = [], None, None
        for i in range(-100, 601):
            el = i / 10
            good = stroke_map(mph, el) is not None
            if good and start is None:
                start = el
            if not good and start is not None:
                runs.append((start, prev))
                start = None
            prev = el
        if start is not None:
            runs.append((start, prev))
        lo, hi = max(runs, key=lambda ab: ab[1] - ab[0])     # the widest contiguous band, not first-to-last
        say(f"  {mph:.0f}mph: launch {lo:+.1f} to {hi:+.1f} deg ({hi - lo:.1f} deg wide); the page says "
            f"{page[mph]:.1f} — {len(runs)} separate band(s) land in the court")
    return 0


def stroke_map(mph: float, elevation: float) -> float | None:
    """Where a ball launched at this speed and elevation lands, in x, or None if it never lands in the
    court. Used only by `--rules` to recompute the page's window table from the file's own constants."""
    v = mph * MPH
    e = math.radians(elevation)
    t = flight((BASELINE_N, CENTRELINE, 2.46), (v * math.cos(e), 0.0, v * math.sin(e)), (0.0, 0.0),
               "hard", cl=0.0, drag=DRAG, lift=LIFT, net_x=NET_X, surfaces=SURFACES, net_profile=net_profile)
    if not t.get("land"):
        return None
    x = t["land"][0]
    return x if NET_X < x <= LENGTH else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="pickleball: the player moves, the engine computes the ball")
    ap.add_argument("--rules", action="store_true", help="fire every rule in the file and print the result")
    ap.add_argument("--demo", action="store_true", help="a scripted doubles game, no key, no network")
    ap.add_argument("--game", type=int, default=1, help="how many games")
    ap.add_argument("--names", default="north-a,north-b,south-a,south-b",
                    help="four names, teams 1&2 vs 3&4; the default is neutral so a scripted game cannot be "
                         "mistaken for a match a member played")
    ap.add_argument("--clock", type=int, default=None,
                    help="pin the wind to a millisecond count, so a record can be replayed")
    ap.add_argument("--level", default="steady",
                    choices=["beginner", "steady", "hard", "read", "learn", "season"],
                    help="`read` is the steady hands with a fault-reading lesson attached; `learn` is the "
                         "same hands paid in points instead; `season` is the same hands with a lesson whose "
                         "unit is a game and whose memory is the season file, so its sample can outgrow its "
                         "noise. `season` writes games/pickleball/seasons/<season>/stance.json")
    ap.add_argument("--learners", default=None,
                    help="for --level season: which names learn; the rest hold --static (default: all four)")
    ap.add_argument("--static", type=float, default=None,
                    help="for --level season: the stance the non-learners hold, in ft behind their kitchen line")
    ap.add_argument("--start", type=float, default=None,
                    help="for --level season: the stance a learner starts from, before it has a record")
    ap.add_argument("--practice", default=None, help="balls hit before this session, one per name")
    ap.add_argument("--seed", default=None, help="give a new member a past: balls carried in")
    ap.add_argument("--surface", default="hard", choices=sorted(SURFACES))
    ap.add_argument("--season", default=None, help="read and write games/pickleball/seasons/<season>")
    ap.add_argument("--season-dir", default=None)
    ap.add_argument("--report", default=None, help="print a season's report")
    ap.add_argument("--vendor", default=None)
    ap.add_argument("--model", default=None)
    args = ap.parse_args(argv)

    if args.rules:
        return cmd_rules(argv)
    if args.report:
        from tennis import season_report
        print(season_report(args.report, args.season_dir, "pickleball"))
        return 0
    names = [n.strip() for n in args.names.split(",")]
    if len(names) != 4:
        print(f"!! doubles needs exactly four names; got {len(names)}", file=sys.stderr)
        return 2

    if args.demo:
        practice = [int(x) for x in (args.practice or "0,0,0,0").split(",")]
        if len(practice) != 4:
            practice = [0, 0, 0, 0]
        if args.level == "season":
            # A season, not a game: `--game` is how many games the season is, and the lesson's book is the file
            # the next run reads. This is the only demo path that writes anything, and what it writes is the
            # record of a decision, not a rating.
            season = args.season or "2026-autumn"
            learners = tuple(n.strip() for n in args.learners.split(",")) if args.learners else None
            static = ({n: args.static for n in names if n not in (learners or names)}
                      if args.static is not None else None)
            lesson = SeasonLesson(season, names, learners=learners, start=args.start,
                                  override=args.season_dir)
            play_season(names, practice, lesson, make_chooser("steady"), max(1, args.game),
                        surface=args.surface, clock=args.clock, say=print, static=static)
            print(f"\n  the lesson's book is {stance_paths(season, args.season_dir)[1]} "
                  f"({len(lesson.log)} decisions recorded in it)")
            return 0
        for g in range(max(1, args.game)):
            print(f"\n-- game {g + 1}")
            play_game(names, practice, make_chooser(args.level), surface=args.surface,
                      first_team=g % 2, wind_seed_ms=args.clock)
        if args.level == "read":
            print("\n  a scripted game with a lesson: the rules are exercised and the stance is learned. "
                  "No season was written.")
        else:
            print("\n  a scripted game: the rules are exercised, the learning is not. No season was written.")
        return 0

    # a members' game: engines, a season file, and a record
    vendors = ([v.strip().lower() for v in args.vendor.split(",")] if args.vendor else vendors_of(names))
    if len(vendors) != 4:
        print("!! one vendor per name, or none and let voice.md decide", file=sys.stderr)
        return 2
    book, practice = open_book(names, args, default="0,0,0,0", sport="pickleball")
    from tennis import BASES, ask, default_model, key_for  # noqa: E402
    models = ([m.strip() for m in args.model.split(",")] if args.model
              else [default_model(v) for v in vendors])
    engines, missing = {}, []
    for n, v, mdl in zip(names, vendors, models):
        k = key_for(v)
        if not k:
            missing.append(f"TRIBE_API_KEY_{v.upper()}")
        engines[n] = (v, k, mdl)
    if missing:
        print("   " + ", ".join(sorted(set(missing))) + " not set, so nobody can hit a ball. "
              "Nothing was played; `--demo` plays the rules with no key.", file=sys.stderr)
        return 2
    history = {n: [] for n in names}
    fell_back: list[str] = []
    for g in range(max(1, args.game)):
        match, result = play_game(names, practice, lambda pl, w, s: member_chooser_pb(
            engines, s, w, history, fell_back), surface=args.surface, first_team=g % 2,
            wind_seed_ms=args.clock)
        print(f"  game {g + 1}: {match.teams[0].score}-{match.teams[1].score}")
    if fell_back:
        print(f"  {len(fell_back)} shot(s) came back as prose and were played straight — see the record")
    if book is not None:
        when = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        players = {n: Player(name=n, north=(i < 2), practice=practice[i]) for i, n in enumerate(names)}
        record_session(book, when=when, surface=args.surface, clock=result["clock"],
                       players=list(players.values()), results=None or {n: [] for n in names},
                       lengths=result["lengths"], partners={}, mode="doubles")
        save_season(book, args.season, args.season_dir, "pickleball")
        print(f"  season {args.season} written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
