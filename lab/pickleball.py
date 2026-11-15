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
    reachable                    the meeting problem: can they get to it before it passes them
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
import math
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tennis import (  # noqa: E402  the twelve, not a thirteenth copy
    COMPASS, G, MPH, RHO, Player, flight, load_season, member_chooser, movement_speed, net_height, open_book,
    parse_command, practice_of, reachable, record_session, save_season, season_paths, vendors_of, wind_at,
    wind_vector,
)

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
VOLLEY_ZONE = 4.0                        # ft outside the kitchen line: a player standing this close takes a
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
           clean: bool = False) -> dict:
    """Movement in, ball out. Face in degrees, power in per cent, aim in feet across the court.

    Spin is off by decision, not by omission: the design page measures the fitted lift coefficient's effect
    at 0.83 degrees of launch, against a third-shot-drop window 0.5 degrees wide, so a term that uncertain
    would be a fiction with a coefficient. `cl` is therefore always 0 and every line says so.
    """
    control = p.skill("control")
    pace_in = (incoming or {}).get("speed_in", 20.0)          # mph; pickleball rallies are slower than tennis
    control *= 1 - 0.18 * min(1.0, pace_in / 45.0)            # a hard ball gives less time to set the paddle
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
    traj = flight(p0, (vx, vy, vz), wind, surface, cl=0.0, drag=DRAG, lift=LIFT,
                  net_x=NET_X, surfaces=SURFACES, net_profile=net_profile)
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
@dataclass
class Positions:
    """One point per player, not a body. Advanced toward the ball by `movement_speed`, which is the same
    function the tennis engine uses; that is what makes the kitchen a decision instead of a boundary."""
    at: dict[str, tuple[float, float]] = field(default_factory=dict)

    def home(self, p: Player) -> tuple[float, float]:
        """Where a player waits: a couple of feet behind their own kitchen line in a dink exchange, or on
        the baseline if they have just served or received — the engine starts everyone on the baseline."""
        x = -1.0 if p.north else LENGTH + 1.0        # behind the baseline: the serve is struck from there
        return (x, CENTRELINE)

    def get(self, p: Player) -> tuple[float, float]:
        return self.at.setdefault(p.name, self.home(p))

    def move_toward(self, p: Player, target: tuple[float, float], seconds: float) -> tuple[float, float]:
        x, y = self.get(p)
        dx, dy = target[0] - x, target[1] - y
        d = math.hypot(dx, dy)
        step = min(d, movement_speed(p) * max(0.0, seconds))
        if d > 1e-9:
            x, y = x + dx / d * step, y + dy / d * step
        self.at[p.name] = (x, y)
        return self.at[p.name]


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
        # The shot type is the engine's, not the member's: the command is three numbers and none of them is
        # "volley". A player standing within four feet outside the kitchen line takes a deep ball out of the
        # air; anyone else lets it bounce. A player standing *inside* the kitchen never swings at it in the
        # air, because that is always a fault — so the only kitchen fault the sim can produce is the
        # momentum one, and the contact fault exists anyway for the day a fourth field is added.
        deep_ball = (incoming or {}).get("depth", 99.0) > 6.0
        can_volley = may_volley and deep_ball and 0 < feet_from_kitchen_line(here[0]) <= VOLLEY_ZONE
        shot_kind = "serve" if shot_no == 0 else ("volley" if can_volley else "groundstroke")
        if shot_kind == "volley":
            step = 1.2
            contact_pos = (here[0] + (step if p.north else -step), here[1])
        else:
            contact_pos = here
        face, power, aim = choose(p, players.get(_opponent_name(match, players, p.name)), incoming,
                                  shot_no, [], shot_kind, may_volley, contact_pos)
        shot = strike(p, incoming, face=face, power=power, aim=aim, shot=shot_kind, surface=surface,
                      wind=wind_vec, pos=contact_pos)
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
            return {"shots": shot_no, "why": "kitchen", "fault_by": hitter_team, "winner": 1 - hitter_team}
        if not ok:
            say(f"       -- {p.name} faulted: {why}")
            return {"shots": shot_no, "why": "out", "fault_by": hitter_team, "winner": 1 - hitter_team}
        t = shot["traj"]
        land = t["land"]
        if shot_no == 1 and not in_service_area(land, p.north, contact_pos[1]):
            say(f"       -- fault: the serve did not land in the diagonal service area "
                f"(the kitchen line is at {KITCHEN_LINE:.0f}ft and {NET_X + KITCHEN:.0f}ft)")
            return {"shots": shot_no, "why": "serve", "fault_by": hitter_team, "winner": 1 - hitter_team}
        bounced[not p.north] = True                  # it landed, so that side has had its bounce
        if shot_no == 1:
            receiver = match.receiver()
        else:
            receiver = _receiver_for(match, players, pos, land, hitter_team)
        rp = players[receiver]
        can, why_not = reachable(rp, land, t["time"], t["bounce"], surface,
                                 home_x=3.0, court_len=LENGTH, court_wid=WIDTH)
        if not can:
            say(f"       -- point: {rp.name} is {why_not}")
            return {"shots": shot_no, "why": "unreachable", "fault_by": None, "winner": hitter_team}
        pos.at[rp.name] = pos.move_toward(rp, land, t["time"] + 0.4)
        # the volley's momentum: the rules say a player carried into the kitchen after a volley has faulted,
        # even though the ball is already dead. Adjudicated on the position the follow-through leaves them in.
        if shot_kind == "volley" and 0 < feet_from_kitchen_line(contact_pos[0]) <= 2.0:
            carried = contact_pos[0] + (1.5 if p.north else -1.5)
            pos.at[p.name] = (carried, contact_pos[1])
            if in_kitchen(carried):
                say(f"       -- fault: {p.name} was carried into the kitchen by the volley's momentum "
                    f"({abs(carried - NET_X):.1f}ft from the net, inside the {KITCHEN:.0f}ft line) — "
                    f"the ball was already dead")
                return {"shots": shot_no, "why": "momentum", "fault_by": hitter_team, "winner": 1 - hitter_team}
        if shot_kind == "groundstroke":                 # follow the shot in: the pickleball approach step
            line_x = KITCHEN_LINE if p.north else NET_X + KITCHEN
            want_x = line_x - 4.0 if p.north else line_x + 4.0
            if (p.north and pos.get(p)[0] < want_x) or (not p.north and pos.get(p)[0] > want_x):
                pos.move_toward(p, (want_x, pos.get(p)[1]), 1.0)
        incoming = dict(t["bounce"])
        incoming["speed_in"] = t["bounce"]["speed_out"] / MPH
        incoming["depth"] = abs(land[0] - NET_X)
        hitter = receiver
        if shot_no >= RALLY_CAP:
            say(f"       -- rally of {shot_no}; the record's ceiling, not the game's.")
            return {"shots": shot_no, "why": "cap", "fault_by": None, "winner": None}


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
              wind_seed_ms: int | None = None, first_team: int = 0, say=print) -> tuple[Match, dict]:
    """A doubles game to 11, win by 2. Every rule that decides the score is in `Match`; this function only
    feeds it rallies and prints what happened."""
    match = new_match(names)
    serve_first(match, first_team)
    ms = wind_seed_ms if wind_seed_ms is not None else int(datetime.now(timezone.utc).timestamp() * 1000)
    wind_in = wind_for(ms)
    wind_vec = wind_vector(*wind_in)
    players = {}
    for i, n in enumerate(names):
        players[n] = Player(name=n, north=(i < 2), practice=practice[i])
    pos = Positions()
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
    while not match.over():
        rally_no += 1
        r = play_rally(match, players, pos, choose, surface, wind_vec, wind_in, say=say,
                       rally_no=rally_no, history=history)
        lengths.append(r["shots"])
        serving_team = match.serving
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
    say(f"  game: {match.teams[winner].names[0]}/{match.teams[winner].names[1]} "
        f"{match.teams[winner].score}-{match.teams[1 - winner].score} "
        f"({rally_no} rallies, mean {sum(lengths) / len(lengths):.1f} shots)")
    return match, {"results": results, "lengths": lengths, "wind": wind_in, "clock": ms,
                   "surface": surface, "why": r["why"] if lengths else "none"}


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
    ap.add_argument("--level", default="steady", choices=["beginner", "steady", "hard"])
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
        for g in range(max(1, args.game)):
            print(f"\n-- game {g + 1}")
            play_game(names, practice, scripted_chooser(args.level), surface=args.surface,
                      first_team=g % 2, wind_seed_ms=args.clock)
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
