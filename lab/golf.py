#!/usr/bin/env python3
"""Golf: a bag, a course, and the number that says which club was wrong.

`games/putt/` taught one thing — pace and line, two unknown numbers, closed by bisection. Golf is a
different question, and it is worth being precise about why, because the obvious version of this game
is "putt, from further away", which would teach nothing:

    on the green the athlete has ONE tool and learns its two numbers;
    on the course the athlete has SIX tools and does not know what any of them does,
    and the shot it hits now decides the problem it faces next.

So the lever is **choice of club**, the second lever is **how hard it swings** (a fraction of that
club's nominal speed), and the number back is the one a golfer reads off the fairway: how far short or
long, how far left or right, in yards. What it must learn from those numbers alone is a table — the
distance each club gives it — and the shape of the effort curve, which it does not know is a curve.

That is the whole design. The athlete is scripted; a scripted athlete that cannot learn this game
proves the feedback is insufficient, which is the only thing worth learning before a member plays it.

The ball is `lab/tennis.py`'s integrator with golf's constants passed in — not a second copy of the
loop, which is how this repository has been broken before. The roll is `lab/putt.py`'s friction law,
a = STIMPMETER² / (2 · stimp), for the same reason.

    python3 lab/golf.py                  # three rounds of nine, then six holes never played
    python3 lab/golf.py --learn 0        # the control: the same athlete, never allowed to update
    python3 lab/golf.py --selftest       # the checks every number below rests on

WHAT IS CALIBRATED AND WHAT IS MEASURED. Nothing here was measured on a launch monitor. The six clubs'
nominal ball speeds, launch angles and spin rates are priors from published tour averages, and the
four drag/lift constants were fitted so those six priors come out as the carries listed in `CLUBS`.
`--selftest` prints the fit residual so the size of that assumption is visible rather than implied. A
model calibrated to a table is only as good as the table; it is not evidence about a real golf ball,
and no finding in `games/golf/README.md` rests on the model being right about physics — only on it
being consistent, which the selftest checks directly.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tennis import flight, G, MPH, RHO  # noqa: E402  the one integrator, not a second copy of the loop
from putt import (  # noqa: E402  the short game is already a game
    STIMPMETER_SPEED, Athlete as PuttAthlete, Green, Hole as PuttHole, attempt as putt_attempt,
)

# G, MPH and RHO are tennis's, imported rather than restated. They lived here for a day as three fresh literals
# (2026-11-19), which is how a physics constant ends up in two places with one of them drifting later: the test
# that caught it was already there (`test_there_is_no_python_in_the_game_folder_and_no_physics_outside_the_lab`)
# and it was the first thing that turned this repository's CI red, where it sat for fifteen hours unowned.
FT_PER_YD = 3.0

# A golf ball: 45.93 g and 1.68 in in diameter. In feet and slugs, which is the units the integrator uses.
BALL_MASS = 0.003147      # slugs
BALL_R = 0.07             # ft, half of 1.68 in
BALL_AREA = math.pi * BALL_R ** 2
LIFT_BASE = 0.5 * RHO * BALL_AREA / BALL_MASS     # 0.00581 per foot: the a = LIFT·Cl·v² multiplier

# Drag and lift against the spin ratio S = ω·r / v. Both were fitted (2026-11-19) to the six carries in
# CLUBS, by turning four numbers until the six came out within a few yards of the priors. The cap on Cl
# is not decoration: without it a 7-iron's 7000 rpm gives a lift acceleration near 2g and the ball glides
# 240 yd, which is the single most useful thing this model taught me about itself — high spin does not
# add carry, it adds drag, and a model that only adds lift gets irons that out-drive a driver.
CL_SPIN = 1.6844          # Cl = min(CL_CAP, CL_SPIN · S)
CL_CAP = 0.1313
CD_0 = 0.1876             # Cd = min(CD_CAP, CD_0 + CD_SPIN · S)
CD_SPIN = 0.4692
CD_CAP = 0.2838

# The lie. One effect, one number: a ball struck out of rough leaves at 88% of the speed the same swing
# would give from fairway. It is a prior, not a measurement, and it is the only lie effect modelled —
# no flyer, no buried ball, no uphill or downhill stance.
ROUGH_SPEED = 0.88               # ball speed from rough, as a fraction of the same swing from fairway
ROUGH_LOSS = 0.20                # what that plus the lost roll comes to in distance, which is what the
#                                  athlete is told it costs: measured at 0.198-0.213 across three clubs

# Sand, the second lie, and the first one added for a reason other than itself: pass 4 put a bunker beside
# the green to see whether a miss with a *direction* changes where a player should aim. Same shape as the
# rough — a fraction of ball speed, a restitution `flight` already takes, one number for the distance — and
# deliberately no fourth thing: no lip to carry, no plugged lie, no spin killed dead. What is not modelled
# turns out to be the whole of a bunker, and the selftest says so rather than this comment.
SAND_SPEED = 0.70                # ball speed from sand, as a fraction of the same swing off grass
SAND_LOSS = 0.45                 # what that comes to in total distance, measured (selftest) then told
SAND_E = 0.30                    # restitution: sand halves the run-out (9.8 yd against 17.3)
SAND_PEN = 1.70                  # the athlete's price for a ball in the sand, in strokes. *Measured*, not
#                                  guessed, and measured twice: 1.67 strokes against a green lie at the same
#                                  distance over the 27 sand landings the drawn courses produce, and 2.00 from
#                                  a ball 1.5 ft from the face (4 strokes against 2). It was 1.00 by guess in
#                                  pass 4, then 0.30 measured — and the lip is what moved it, because without a
#                                  lip there is nothing to hit. Worth remembering that this one number moved
#                                  the ±14 ft answer by 0.9 strokes a round while it was wrong.

# What the short game costs, in strokes, measured by playing it out (pass 10; `--costs` re-measures).
#
# These two numbers replaced a step function. Until pass 10 `target()` scored a landing as
# `P(on the green) + 0.3 * P(inside 25 ft of the pin)`, which is not strokes and cannot tell a 3 ft putt from
# a 24 ft one -- and the pass that went looking for the honest version found something worse: **the game's
# putter is deterministic**, so it holes out in two strokes from two feet and from twenty-eight, and there is
# no gradient in distance on the green for any objective to find. What is left is two costs and a lie:
# on the green 2.00, off it 2.60 (a chip and a putt), and the sand at the athlete's own price on top.
COST_ON_GREEN = 2.00             # strokes to hole out from anywhere on the green, 2 ft to 28 ft, flat
COST_OFF_GREEN = 2.60            # the same from the fringe or the rough: a chip, then the same two

# What the turf keeps of the ball's horizontal speed at the first bounce, and how fast a rolling ball
# stops. The second is putt's own law, so a stimp reading means the same thing in both games; the first
# is a single prior chosen so a driver runs out about 20 yd and a 7-iron about 10.
ROLL_RETAIN = 0.25
STIMP_FAIRWAY = 8.0
STIMP_ROUGH = 5.5

# Strike dispersion. A model with none of it plays golf nobody would recognise: every shot finishes
# exactly where the arithmetic said, so the athlete converges to par or better and the card is a
# spreadsheet. These two numbers are the athlete's hands — 1.1° of clubface error and 1.5% of ball speed,
# drawn from a seeded generator so a run is reproducible — and they are priors, not measurements.
# Note what they do to the experiment: the speed error is zero-mean noise around a club's true distance,
# so the table still converges on the mean, while the ball never lands where the table says it will.
FACE_SD = 1.1             # degrees
SPEED_SD = 0.015          # fraction of ball speed
DEFAULT_SEED = 20261119


@dataclass(frozen=True)
class Club:
    name: str
    speed_mph: float      # ball speed at a nominal (100%) swing, from published tour averages
    launch: float         # degrees above the ground
    spin: float           # rpm
    prior_carry: float    # yd — the number the fitting above was aimed at, NOT measured here


# Six clubs is not a full bag. It is the smallest bag in which choosing a club is a decision: with two
# clubs every problem has one answer, and with fourteen most of them have none worth thinking about.
CLUBS = [
    Club("driver", 167, 10.9, 2686, 260),
    Club("3 wood", 158, 12.5, 3200, 235),
    Club("5 iron", 135, 14.5, 5000, 190),
    Club("7 iron", 120, 16.3, 7000, 155),
    Club("9 iron", 102, 20.0, 8600, 130),
    Club("sand wedge", 82, 28.0, 10000, 100),
]
CLUB_BY_NAME = {c.name: c for c in CLUBS}

_BAG_CACHE: dict[str, float] | None = None


def bag() -> dict[str, float]:
    """What this model gives each club at a full swing from fairway, carry + run, in yards.

    Cached because the athlete asks for it once and the selftest asks for it repeatedly. Its own inherited
    table is this, less ten per cent: not a guess about the athlete, a statement that a first bag is wrong.
    """
    global _BAG_CACHE
    if _BAG_CACHE is None:
        _BAG_CACHE = {c.name: shot((0.0, 0.0), c, 1.0, 0.0)["total"] / FT_PER_YD for c in CLUBS}
    return _BAG_CACHE


def spin_ratio(club: Club, speed_ft_s: float) -> float:
    omega = club.spin * 2.0 * math.pi / 60.0
    return omega * BALL_R / max(1e-6, speed_ft_s)


def aero(club: Club, speed_ft_s: float) -> tuple[float, float]:
    s = spin_ratio(club, speed_ft_s)
    cl = min(CL_CAP, CL_SPIN * s)
    cd = min(CD_CAP, CD_0 + CD_SPIN * s)
    return cl, 0.5 * RHO * cd * BALL_AREA / BALL_MASS


# What each lie takes off the swing, as a fraction of ball speed. One table, so a lie cannot be added to the
# game and forgotten in the physics.
LIE_SPEED = {"fairway": 1.0, "rough": ROUGH_SPEED, "sand": SAND_SPEED}


def _height_at(path, start: tuple[float, float], distance: float) -> float | None:
    """The ball's height the first time it is `distance` ft from where it started, interpolated between the
    integrator's samples. None if it never gets that far — a ball that lands in the sand short of the face
    cannot hit a face it never reaches."""
    prev = None
    for (_, x, y, z) in path or ():
        d = math.hypot(x - start[0], y - start[1])
        if d >= distance:
            if prev is None:
                return z
            (_, px, py, pz) = prev
            pd = math.hypot(px - start[0], py - start[1])
            f = 0.0 if d == pd else (distance - pd) / (d - pd)
            return pz + f * (z - pz)
        prev = (_, x, y, z)
    return None


# ---- one shot ---------------------------------------------------------------------------------------
def shot(start: tuple[float, float], club: Club, effort: float, aim: float,
         lie: str = "fairway", wind: tuple[float, float] = (0.0, 0.0),
         surface: dict | None = None, lip: float | None = None,
         trace: float | None = None) -> dict:
    """Strike, fly, bounce, run out. Every length is in feet, every angle in degrees clockwise from north.

    `effort` is the fraction of the club's nominal ball speed, which is the one thing an athlete controls
    that a launch monitor cannot argue with. `aim` is the bearing the ball leaves on. The rest point is
    where a spectator would walk to.
    """
    surf = surface or {"fairway": {"e": 0.4, "f": 1.0}, "rough": {"e": 0.3, "f": 1.0},
                       "sand": {"e": SAND_E, "f": 1.0}}
    speed = club.speed_mph * MPH * effort * LIE_SPEED.get(lie, 1.0)
    cl, drag = aero(club, speed)
    a = math.radians(aim)
    v0 = (speed * math.cos(math.radians(club.launch)) * math.sin(a),
          speed * math.cos(math.radians(club.launch)) * math.cos(a),
          speed * math.sin(math.radians(club.launch)))
    out = flight((start[0], start[1], 0.0), v0, wind, lie, net_check=False,
                 cl=-cl, drag=drag, lift=LIFT_BASE, surfaces=surf, t_max=20.0,
                 trace=trace if trace is not None else (0.01 if lip is not None else None))
    if lip is not None:
        h = _height_at(out.get("path"), start, lip)
        if h is not None and h < LIP_H:
            # Into the face. The stroke is gone and the ball is where it was, which is what a spectator sees and
            # why a player who tries to be clever from the bottom of a bunker makes it worse.
            return dict(land=start, rest=start, carry=0.0, roll=0.0, total=0.0, lost=False, lip=True,
                        stop_at=lip, path=out.get("path"),
                        hang=0.0, cl=cl, drag=drag, speed=speed, descent=0.0)
    land = out.get("land")
    if not land:                                    # cannot happen with these constants; if it does, say so
        return dict(land=start, rest=start, carry=0.0, roll=0.0, total=0.0, lost=True,
                    hang=out.get("time", 0.0), cl=cl, drag=drag, speed=speed)
    bx, by, _ = out["bounce"]["v"]
    vh = math.hypot(bx, by)
    ux, uy = (bx / vh, by / vh) if vh > 1e-9 else (math.sin(a), math.cos(a))
    stimp = STIMP_ROUGH if lie in ("rough", "sand") else STIMP_FAIRWAY
    a_roll = STIMPMETER_SPEED ** 2 / (2.0 * stimp)
    roll = (ROLL_RETAIN * vh) ** 2 / (2.0 * a_roll)
    carry = math.hypot(land[0] - start[0], land[1] - start[1])
    rest = (land[0] + ux * roll, land[1] + uy * roll)
    return dict(land=land, rest=rest, carry=carry, roll=roll, total=carry + roll, lost=False,
                path=out.get("path"), stop_at=None,
                hang=out.get("time", 0.0), cl=cl, drag=drag, speed=speed,
                descent=math.degrees(math.atan2(-out["bounce"]["v"][2], vh)))


# ---- the course -------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Hole:
    yards: float
    par: int
    label: str = ""
    pin: float = 0.0                 # ft the flag is cut right of the green's centre; negative is left
    wind: tuple[float, float] = (0.0, 0.0)      # (bearing the wind blows FROM, mph)
    sand: int = 0                    # +1 the bunker guards the right of the green, −1 the left, 0 none
                                     # (it stays where the greenkeeper put it: the pin moves, the sand does not)

    @property
    def flag(self) -> tuple[float, float]:
        return self.pin, self.yards * FT_PER_YD

    @property
    def centre(self) -> tuple[float, float]:
        return 0.0, self.yards * FT_PER_YD


# Nine holes with the flag cut where a greenkeeper cuts it — four of them within a club's length of the
# green's edge — and a wind on every one. The wind is what the athlete can read and does not model; the pin
# is what it can see and must decide about.
# Six of the nine have sand on one flank and three have none, three a side, so "the pin is cut toward the
# sand" and "the pin is cut away from it" are both samples and neither is the special case. The bunkers do
# not move with the pin: that is the whole point of them here.
COURSE = [Hole(410, 4, "1", pin=+13, wind=(200, 14), sand=+1),
          Hole(165, 3, "2", pin=-11, wind=(5, 12), sand=-1),
          Hole(520, 5, "3", pin=+4, wind=(180, 15), sand=0),
          Hole(300, 4, "4", pin=-14, wind=(250, 10), sand=+1),
          Hole(145, 3, "5", pin=+12, wind=(90, 16), sand=0),
          Hole(385, 4, "6", pin=-3, wind=(355, 9), sand=-1),
          Hole(95, 3, "7", pin=-13, wind=(225, 12), sand=+1),
          Hole(450, 4, "8", pin=+11, wind=(170, 18), sand=-1),
          Hole(500, 5, "9", pin=-9, wind=(330, 10), sand=0)]
HELD_OUT = [Hole(130, 3, "H1", pin=+12, wind=(20, 11), sand=+1),
            Hole(375, 4, "H2", pin=-10, wind=(190, 14), sand=0),
            Hole(480, 5, "H3", pin=+6, wind=(0, 13), sand=-1),
            Hole(190, 3, "H4", pin=-12, wind=(270, 9), sand=+1),
            Hole(340, 4, "H5", pin=+2, wind=(150, 12), sand=0),
            Hole(90, 3, "H6", pin=-11, wind=(30, 10), sand=-1)]

CALM = [(h.yards, h.par, h.label, h.pin, (0.0, 0.0), h.sand) for h in COURSE]


def drawn_course(rng: random.Random, pin_range: float = 14.0, calm: bool = False) -> list[Hole]:
    """The same nine holes with the pin and the wind drawn independently.

    The first time this game was played the nine pins and the nine winds were nine fixed pairs that I chose by
    hand, and the aiming experiment came out one way in still air and the opposite way with the weather on. An
    athlete that cannot correct a crosswind is lucky or unlucky depending on which way the air blows past which
    pin, and a hand-picked table is not a sample of that luck. Draws are independent: the pin anywhere in the
    middle 28 ft of the green, the air from any bearing at 8 to 18 mph.
    """
    return [Hole(h.yards, h.par, h.label, pin=rng.uniform(-pin_range, pin_range),
                 wind=(0.0, 0.0) if calm else (rng.uniform(0.0, 360.0), rng.uniform(8.0, 18.0)),
                 sand=h.sand)
            for h in COURSE]


def wind_vector(wind: tuple[float, float]) -> tuple[float, float]:
    """The air's velocity in ft/s, from the bearing it blows FROM — the way a golfer names it: 'into the
    wind on the first', and everybody knows which way to face."""
    frm, mph = wind
    toward = math.radians(frm + 180.0)
    v = mph * MPH
    return v * math.sin(toward), v * math.cos(toward)

FAIRWAY_HALF = 20.0 * FT_PER_YD    # yd either side of the centre line before the lie is rough
ROUGH_EDGE = 35.0 * FT_PER_YD      # beyond this the ball is in the trees: a stroke and a drop
# The green is an ellipse round the hole's centre, not a circle round the flag, and that is the whole of the
# second decision: a flag cut 13 ft from the edge of a 40 ft-wide green is a pin you can aim at or a pin you
# can play away from, and the two are different scores. At a circle centred on the flag the choice does not
# exist, because the flag is the safest place on the green.
# ---- the sand, the first thing in this file that could make a miss directional ----------------------
# On an ellipse every miss is the same kind of miss: short, long, left and right all cost roughly the same,
# so "aim at the middle of the green" is a coherent instruction and the pin's distance from that middle is
# the only thing a player has to weigh. Put a bunker on one flank and that should stop being true: the same
# fourteen feet of miss is a putt on one side and sand on the other. That was the hypothesis of pass 4, and
# the selftest is where it is tested — the answer is that it does not stop being true, and the reason is
# that a bunker without a lip is a slow lie rather than an obstacle.
GREEN_A = 20.0                     # ft, half the green's width
GREEN_B = 28.0                     # ft, half its depth
BUNKER_W = 14.0                    # ft of sand outside the green's edge on its guarded side
# The lip. Not a law of motion: a height the ball must be above when it crosses the sand's inner edge, read off
# the trajectory the integrator already computes. Eighteen inches, which is what a greenside bunker's face is,
# and enough that a flat shot from a ball lying a foot from it cannot get out forwards. What it is *not*: a
# plugged lie, a stance with the feet below the ball, spin dying at contact. Those are laws, so they are absent,
# and said to be absent.
LIP_H = 1.5                        # ft of sand face the ball has to clear to reach the green
LIP_MARGIN = 1.4                   # the athlete's safety factor on its own clearance: a rule, not physics
STROKE_CAP = 12
# The putter is for the green and nothing else. A Texas wedge from off the edge was tried (2026-11-19) and
# turned every fringe into a two-putt, which is not golf either.
PUTT_ZONE = 0.0


def on_green(point: tuple[float, float], hole: Hole) -> bool:
    dx = (point[0] - hole.centre[0]) / GREEN_A
    dy = (point[1] - hole.centre[1]) / GREEN_B
    return dx * dx + dy * dy <= 1.0


def in_sand(point: tuple[float, float], hole: Hole) -> bool:
    """A band of sand along one flank of the green, as deep as the green is. Not a ring round it: a ring
    would guard every side and the pin would stop mattering, which is the one thing this addition has to
    leave alone."""
    if not hole.sand:
        return False
    dx = point[0] - hole.centre[0]
    dy = abs(point[1] - hole.centre[1])
    if dy > GREEN_B:
        return False
    if hole.sand > 0:
        return GREEN_A < dx <= GREEN_A + BUNKER_W
    return -GREEN_A - BUNKER_W <= dx < -GREEN_A


def lip_distance(ball: tuple[float, float], bearing: float, hole: Hole) -> float | None:
    """How far this bearing has to run before the ball must climb the lip, in feet — or None if it never
    crosses the sand's inner edge: playing out of the end of the bunker, or away from the green. Only the
    green-side edge is a face; the outer edge is level with the fairway. That asymmetry is the decision a
    bunker actually poses, and the reason a player can always take his medicine and play out sideways."""
    if not hole.sand:
        return None
    ux, uy = math.sin(math.radians(bearing)), math.cos(math.radians(bearing))
    if (hole.sand > 0 and ux >= -1e-6) or (hole.sand < 0 and ux <= 1e-6):
        return None                    # the sand is on +x for a right bunker, so the green is at −x
    edge = hole.centre[0] + hole.sand * GREEN_A
    t = (edge - ball[0]) / ux
    if t <= 0.0:
        return None
    if abs(ball[1] + uy * t - hole.centre[1]) > GREEN_B:
        return None
    return t


def lie_at(point: tuple[float, float], hole: Hole) -> str:
    if on_green(point, hole):
        return "green"
    if in_sand(point, hole):
        return "sand"
    off = abs(point[0])
    if off <= FAIRWAY_HALF:
        return "fairway"
    if off <= ROUGH_EDGE:
        return "rough"
    return "trees"


# ---- the athlete ------------------------------------------------------------------------------------
GEARS = (1.0, 0.8, 0.6, 0.45, 0.35, 0.25)   # what the notebook has columns for: the full swing, something
#                                        off it, a half, a soft half, the chip and the little chip. Not a
#                                        continuous dial, because a player's repeatable shots are the named
#                                        ones — and because an athlete that can hit any effort exactly can
#                                        always reach the flag, whose distances then never matter. The last
#                                        gear was added on 2026-11-19: without it a ball 17 yd off the edge
#                                        had nothing in the bag that would land on the green, and the athlete
#                                        played ping-pong until the twelve-stroke cap.

# What a knocked-down swing costs in the choosing: this many yards of accuracy is worth surrendering before
# the athlete will take 25% off a swing. It is a rule of the athlete's, not a fact about golf.
FULL_SWING_PREFERENCE = 1.5

# The ball speed a headwind is measured against when the athlete is deciding how much club the wind is worth.
# One number, because it is a ratio and the coefficient it is fitted with absorbs the choice.
WIND_REF_SPEED = 150.0            # ft/s
# A wind blowing more sideways than this, as a fraction of a ball speed, is a wind the athlete cannot read a
# face angle out of: about 5 mph across. Above it the shot still counts; it just does not teach the hands.
CROSS_QUIET = 0.035

# The smallest scatter `target()` will believe, in feet at the flag. It is a floor on the *model* — a normal
# tail wider than a golf ball — and not a floor on skill, which is why it must be small. At 2.0 ft (passes 2-8)
# it was larger than a 1° scatter from anywhere inside 76 ft, so the target decision ignored the belief
# altogether and six taught sigmas from 0.6° to 3.0° played the same card. Measured, pass 9.
FLOOR_FT = 0.5


# What a beginner believes about a bag, against what it does. Not random: the shape of the error is the shape
# of the mistake everybody makes — too much faith in the short irons, no idea what the wedges do, and a
# driver that is credited with less than it has because the good ones are forgotten and the bad ones are not.
# This table is invented. What it is *not* is a uniform percentage: a bag that is uniformly ten per cent
# short is a bag with no error worth learning, because inverting a scaled table returns the true distance
# exactly, and a control player with one would score as well as a player who practised.
INHERITED = {"driver": 0.94, "3 wood": 1.06, "5 iron": 0.93,
             "7 iron": 1.10, "9 iron": 1.04, "sand wedge": 0.88}


class Athlete:
    """Six clubs and five gears. Thirty numbers, none of which it has right to begin with.

    What it is told before every shot: the distance to the flag and the lie. Both are visible to a golfer;
    the wind is calm unless a caller says otherwise. What it carries is a notebook:

        table[club][gear]   what this club has done for me at this effort, in yards

    Every entry starts at what a beginner believes: the bag this model gives, scaled *linearly* in gear (hit
    it twice as hard and it goes twice as far, says the beginner — it does not) and scaled per club by
    `INHERITED`. Every fairway shot replaces the entry it was hit with by the running mean of what that club
    and that gear have actually done. That is all the arithmetic there is.

    The second thing it learns is smaller and costs more strokes: the ball leaves its clubface about two
    degrees right of where it aims. It estimates that angle from the side of its misses and aims off it.

    An earlier version of this file had the athlete fit distance = k·effort^p by least squares. It fitted
    badly, and the reason is worth keeping: with a bag of full swings the observations sit at nearly one
    effort, so k and p trade off against each other, and a wrong pair still explains every number in the
    notebook. A table cannot make that mistake, and it is also what players actually keep.
    """

    def __init__(self, prior: float = 1.0, sigma_taught: float | None = None,
                 gate: bool = True) -> None:
        """`prior` scales what it believes about the bag (1.0 is the beginner of this file, 0.85 a worse one);
        `sigma_taught` denies it the one number it would otherwise learn from its own misses, which is the
        input to every target decision — a field needs somebody who cannot tell how wide it hits."""
        self.table = {c.name: {g: bag()[c.name] * INHERITED[c.name] * prior * g for g in GEARS} for c in CLUBS}
        self.n = {c.name: {g: 0 for g in GEARS} for c in CLUBS}
        self.aim_bias = 0.0
        self.face = 2.2                                    # its own hands, which it does not know about:
        #                                                    the playing code adds this, the learning code
        #                                                    never reads it, and `aim_bias` is what it
        #                                                    estimates from the side of its misses
        self.misses: list[float] = []                      # misses struck in still-ish air, in degrees
        self.shots = 0
        self.sigma = 1.5                                   # degrees of scatter it believes it has; learned
        self.sigma_taught = sigma_taught                   # ...unless it is told, and then never learns
        self.gate = gate                                   # whether the wind is kept out of that lesson
        self.cnd_pairs: list[tuple[float, float]] = []      # (head fraction, how short the shot came back)
        self.wind_c = 0.0                                  # how much wind takes off; learned from zero
        self.rough_cost = ROUGH_LOSS                       # what the rough costs; told, not learned
        self.sand_pen = SAND_PEN                           # what a ball in the sand is worth, in strokes
        self.policy = "spread"                             # "flag", "centre" or "spread"

    def predict(self, name: str, gear: float) -> float:
        return self.table[name][gear]

    def choose(self, distance_yd: float) -> tuple[Club, float]:
        """The shot in the notebook whose distance is nearest, with a price on taking something off it."""
        best = None
        for c in CLUBS:
            for g in GEARS:
                gap = abs(self.table[c.name][g] - distance_yd)
                score = gap + FULL_SWING_PREFERENCE * (1.0 - g)
                if best is None or score < best[0]:
                    best = (score, c, g)
        return best[1], best[2]

    def observe(self, name: str, gear: float, total_yd: float) -> None:
        """Fold the shot into the entry it was hit on. Half a swing is not a full one: a player who
        corrected his seven iron off a knocked-down shot would ruin the number that matters."""
        self.shots += 1
        n = self.n[name][gear]
        self.n[name][gear] = n + 1
        self.table[name][gear] += (total_yd - self.table[name][gear]) / (n + 1)

    def observe_side(self, lateral_yd: float, distance_yd: float, aim_used: float,
                     cross: float = 0.0) -> None:
        """The hands, from the side of the miss — on the holes where the air is not doing the work.

        A crosswind moves this ball about 32 degrees per unit of crosswind fraction (measured, not assumed:
        see the selftest), so a 16 mph crosswind is worth four and a half degrees and a mean of the misses
        would learn a slice that is not there. **The first version of this did exactly that and spent three
        rounds aiming four degrees wrong.** So the hands are only read on shots struck in still-ish air, and
        the scatter is what is left about that mean — which is also the number the target decision needs.

        What the athlete therefore cannot do is aim off for a crosswind. That is not an oversight: it is the
        wind doing something to a golf ball that a table cannot hold, and the cost of it is measured by
        running the same athlete round the calm course.
        """
        if distance_yd < 20.0 or (self.gate and abs(cross) > CROSS_QUIET):
            return
        raw = math.degrees(math.atan2(lateral_yd, distance_yd)) - aim_used
        self.misses.append(raw)
        n = len(self.misses)
        self.aim_bias = -sum(self.misses) / n
        if self.sigma_taught is None:
            self.sigma = max(0.3, math.sqrt(sum((m - self.aim_bias * -1.0) ** 2 for m in self.misses) / n))
        else:
            self.sigma = self.sigma_taught

    def aim_offset(self, cross: float = 0.0) -> float:
        return self.aim_bias

    def observe_conditions(self, head_fraction: float, ratio: float) -> None:
        """One condition, one coefficient, least squares through the origin:

            what the shot did / what the notebook said  ≈  1 - wind_c · h

        `h` is the headwind as a fraction of a ball speed, so the coefficient is dimensionless. This is the
        only place the athlete learns something that is not a tool, and it is identified by the wind changing
        between holes rather than by its own choices — which is why one parameter works here and the
        five-parameter effort fit did not.

        The lie is deliberately *not* learned. A first version fitted it alongside the wind and came out at
        0.46 for a true 0.20, because a rough lie is where a mis-clubbed ball ends up and the coefficient
        absorbed the notebook's own errors. Guarding it to settled entries then learned nothing (no rough
        shot is ever hit with a club that has been hit four times). The honest answer is that the rough is
        not something a player discovers by experiment — it is the first thing anybody tells you — so it is
        a constant here, `ROUGH_LOSS`, and the notebook stays clean.
        """
        self.cnd_pairs.append((head_fraction, 1.0 - ratio))
        den = sum(h * h for h, _ in self.cnd_pairs)
        if den > 1e-9:
            self.wind_c = max(-1.0, min(3.0, sum(h * y for h, y in self.cnd_pairs) / den))

    def target(self, hole: Hole, ball: tuple[float, float], dist_ft: float) -> float:
        """Where to aim, in feet right of the green's centre. The decision the game is really about.

            flag     aim at the pin, wherever it is cut.
            centre   aim at the middle of the green, which is what a caddie says.
            spread   aim where the ball is *cheapest to hole out from*, given the scatter it has measured:
                     COST_ON_GREEN · P(on the green) + COST_OFF_GREEN · P(off it)
                     + (COST_ON_GREEN + SAND_PEN) · P(in the sand).

        Nothing here is learning. It is what the learned numbers are *for* — a player who knows how much it
        misses by can spend that knowledge on a target, and a player who does not can only hope.

        **Pass 10 replaced this objective, and the name `spread` is a leftover.** Until then it scored
        P(on the green) + 0.3 · P(inside 25 ft of the pin): not strokes, and unable to tell a 3 ft putt from
        a 24 ft one. The honest version is strokes, and it is what showed that the game's *putter* has no
        gradient at all (COST_ON_GREEN is 2.00 from two feet and from twenty-eight, because the putt athlete
        bisects its gain and its line to zero error and the roll carries no scatter). So on this green there
        is nothing to aim at but the lie: being off the green costs 0.6 of a stroke and the sand costs the
        athlete's own price, and everything else the objective used to reward was a gradient I had written
        into it. The pin enters only through the ties — when two targets cost the same, this aims at the
        flag, which is what a player does and is stated as a rule because it is one.

        The sand term is what pass 4 is about, and pass 10 made it nearly all of the objective. On a green
        with no bunker, "the middle" and "the pin" cost the same and the tie-break decides; put fourteen feet
        of sand on one flank and the same fourteen feet of miss costs a stroke on that side and nothing on
        the other. `centre` does not know this and `flag` does not know it either, which is the point.
        """
        if self.policy == "flag":
            return hole.pin
        if self.policy == "centre":
            return 0.0
        # Pass 9. This floor was 2.0 ft from the second pass to the eighth, and it was the whole of the
        # answer to the eighth pass's deflation: an honest sigma (0.9-1.1°, hands 1.10°) is below a 2 ft
        # spread at every approach range in the game, so the floor decided the target and the belief never
        # reached it. It is not a bound on how well anyone can aim — it was a bound on a *model*, standing
        # in for the fact that a normal tail is fatter than a golf ball's. What it is now is small enough
        # to bind only inside 30 ft, where a green is a putting surface and a 0.5 ft floor is honest.
        s = max(FLOOR_FT, math.radians(self.sigma) * dist_ft)
        scored: list[tuple[float, float]] = []
        for k in range(-45, 46):
            t = float(k)
            p_on = _phi((GREEN_A - t) / s) - _phi((-GREEN_A - t) / s)
            p_sand = 0.0
            if hole.sand > 0:
                p_sand = _phi((GREEN_A + BUNKER_W - t) / s) - _phi((GREEN_A - t) / s)
            elif hole.sand < 0:
                p_sand = _phi((-GREEN_A - t) / s) - _phi((-GREEN_A - BUNKER_W - t) / s)
            value = (COST_ON_GREEN * p_on + COST_OFF_GREEN * max(0.0, 1.0 - p_on - p_sand)
                     + (COST_ON_GREEN + self.sand_pen) * p_sand)
            scored.append((value, t))
        # Pass 9, the second half. With the floor at 2 ft the objective had one peak wherever it was
        # evaluated; with the floor gone, a scatter of a foot makes it *flat* over a band, and the loop was
        # returning whichever end of that band it reached first — a fact about range(-45, 46) and not about
        # a golf shot. Ties are broken at the flag now, and since pass 10 that rule carries most of the
        # decision on a green with no hazard near the pin: no hazard, no gradient, and the flag wins the tie.
        best = min(v for v, _ in scored)
        return min((t for v, t in scored if v <= best + 1e-9), key=lambda t: abs(t - hole.pin))


def _phi(z: float) -> float:
    """The normal CDF, from the error function — no scipy, no approximation to argue with."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ---- playing ----------------------------------------------------------------------------------------
def yards_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1]) / FT_PER_YD


def bearing_to(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))


def report_shot(start: tuple[float, float], rest: tuple[float, float],
                flag: tuple[float, float]) -> tuple[float, float]:
    """The number back: along (past is +, yards), lateral (right is +, yards), in the flag's frame."""
    ux, uy = flag[0] - start[0], flag[1] - start[1]
    d = math.hypot(ux, uy)
    if d < 1e-6:
        return 0.0, 0.0
    ux, uy = ux / d, uy / d
    rx, ry = uy, -ux
    dx, dy = rest[0] - flag[0], rest[1] - flag[1]
    return (dx * ux + dy * uy) / FT_PER_YD, (dx * rx + dy * ry) / FT_PER_YD


def play_hole(hole: Hole, ath: Athlete, putter: PuttAthlete, green: Green,
              learn: bool = True, verbose: bool = True, wind: tuple[float, float] | None = None,
              tag: str = "", rng: random.Random | None = None,
              start: tuple[float, float] = (0.0, 0.0), trace: float | None = None) -> dict:
    """One hole, one loop.

    It was two loops until this pass — shots, then putts — and putting a bunker beside the green broke that:
    a putt that runs off the edge and stops in the sand cannot be putted again, so the game has to come back
    out of the putter and into a club. One loop decides, for every stroke, whether this ball gets a putter or
    a club, which is a decision a golfer makes and a phase boundary does not. A ball on the fringe it putted
    itself onto still gets the putter (a Texas wedge is legal golf); a ball in the sand never does.
    """
    rng = rng or random.Random(DEFAULT_SEED)
    wind = hole.wind if wind is None else wind
    wx, wy = wind_vector(wind)
    flag = hole.flag
    ball = start
    strokes, putts, penalties = 0, 0, 0
    log: list[dict] = []
    holed, last_putt = False, False
    lip_seen = False                  # this ball has already hit the face once
    while strokes < STROKE_CAP:
        gap_ft = math.hypot(flag[0] - ball[0], flag[1] - ball[1])
        if gap_ft <= 2.125 / 12.0:        # the hole is 4.25 in across; a ball in it is in it, and putt.py
            holed = True                   # never has to be asked, because a putt never starts there
            if verbose and last_putt is False and strokes:
                print(f"  {tag}{hole.label:>3} {'':>4} {'':>12} in the hole, no putt needed")
            break
        lie = "fairway" if ball == (0.0, 0.0) else lie_at(ball, hole)

        # ---- the putter -------------------------------------------------------------------------
        if (lie == "green" or gap_ft <= PUTT_ZONE or (last_putt and lie not in ("sand", "trees"))) \
                and putts < 4:
            bearing = bearing_to(ball, flag)
            r = putt_attempt(putter, PuttHole(gap_ft, bearing), green, learn=learn)
            putts += 1
            strokes += 1
            last_putt = True
            if r["holed"]:
                holed = True
                if verbose:
                    print(f"  {tag}{hole.label:>3} {'':>4} {'':>12} putt        {gap_ft:5.1f} ft  "
                          f"{r['text']}  ({putts} putt{'s' if putts > 1 else ''})")
                break
            # putt's report is in the hole's own frame: past is + along the line it was hit on, right is +.
            ux, uy = flag[0] - ball[0], flag[1] - ball[1]
            d = math.hypot(ux, uy) or 1.0
            ux, uy = ux / d, uy / d
            ball = (flag[0] + r["along"] * ux + r["lateral"] * uy,
                    flag[1] + r["along"] * uy - r["lateral"] * ux)
            if verbose:
                print(f"  {tag}{hole.label:>3} {'':>4} {'':>12} putt        {gap_ft:5.1f} ft  {r['text']}")
            continue

        if putts >= 4:            # four putts and it picks up: no club is taken to a ball on the green, and
            break                  # before this guard the field found that one could be, and crashed

        # ---- a club -----------------------------------------------------------------------------
        if lie == "trees":
            strokes += 1
            penalties += 1
            ball = (math.copysign(ROUGH_EDGE, ball[0]), ball[1])
            log.append(dict(kind="penalty", text="in the trees: one stroke, dropped at the edge of the rough"))
            continue
        # Where to aim, and how much the air and the lie will change the number the notebook gives. The sand
        # costs most of the distance, it costs the pin (`target()` will not aim onto it) and, since the lip, it
        # may cost the stroke altogether: the ball must be eighteen inches up by the time it reaches the face.
        def pick(bearing: float, play_ft: float):
            """Club, gear and the conditions for a shot along `bearing` that has to travel `play_ft`."""
            ux_, uy_ = math.sin(math.radians(bearing)), math.cos(math.radians(bearing))
            head_ = -(wx * ux_ + wy * uy_) / WIND_REF_SPEED   # positive into the wind
            cross_ = (wx * uy_ - wy * ux_) / WIND_REF_SPEED   # positive: blowing across to the right
            lc_ = ath.rough_cost if lie == "rough" else (SAND_LOSS if lie == "sand" else 0.0)
            cost_ = 1.0 - ath.wind_c * head_ - lc_
            club_, gear_ = ath.choose(play_ft / FT_PER_YD / max(0.5, cost_))
            return club_, gear_, head_, cross_, cost_

        offset = ath.target(hole, ball, gap_ft)
        aim_bearing = bearing_to(ball, (hole.centre[0] + offset, hole.centre[1]))
        play_ft = gap_ft
        lip_ft = lip_distance(ball, aim_bearing, hole) if lie == "sand" else None
        club, gear, head, cross, cost = pick(aim_bearing, play_ft)
        escaping = False
        if lie == "sand" and (lip_seen or (lip_ft is not None and (
                lip_ft * math.tan(math.radians(club.launch)) < LIP_MARGIN * LIP_H))):
            # The athlete's rule, and a rule is not physics: if the club in its hand cannot be eighteen inches up
            # in the distance it must climb, it plays out over the *low* edge instead, straight away from the
            # green. A sand wedge is 28°, so the face costs it 2.8 ft of run. And after a failure the same club
            # does not swing at the same target twice: a player who has just hit the face takes his medicine,
            # which is what `lip_seen` is, and without it this hole could be played twelve times into the wall.
            escaping = True
            aim_bearing = math.degrees(math.atan2(ball[0] - hole.centre[0], ball[1] - hole.centre[1]))
            lip_ft = None
            play_ft = (GREEN_A + BUNKER_W - abs(ball[0] - hole.centre[0])) + 6.0
            club, gear, head, cross, cost = pick(aim_bearing, play_ft)
        predicted = ath.predict(club.name, gear)
        aim_used = ath.aim_offset(cross)
        aim = aim_bearing + aim_used + ath.face + rng.gauss(0.0, FACE_SD)
        effort = gear * (1.0 + rng.gauss(0.0, SPEED_SD))
        res = shot(ball, club, effort, aim, lie=lie, wind=(wx, wy), lip=lip_ft, trace=trace)
        rest = res["rest"]
        rest = (max(-ROUGH_EDGE * 1.4, min(ROUGH_EDGE * 1.4, rest[0])), rest[1])  # the course ends somewhere
        along, lateral = report_shot(ball, rest, flag)
        # ...and the same shot measured from the line it *meant* to hit. `report_shot` is in the flag's frame,
        # and the flag is not where the athlete aimed: the whole point of `target()` is that it aims somewhere
        # else on purpose. Taking the side of the miss from the flag therefore counts the athlete's own aim as
        # a miss, which is not a fact about its hands. Found on 2026-11-19, pass 8, by measuring the two.
        _ux, _uy = math.sin(math.radians(aim_bearing)), math.cos(math.radians(aim_bearing))
        _dx, _dy = rest[0] - ball[0], rest[1] - ball[1]
        lateral_aim = (_dx * _uy - _dy * _ux) / FT_PER_YD
        flown_yd = max(1.0, math.hypot(_dx, _dy) / FT_PER_YD)   # the range the angle is a fraction of
        strokes += 1
        last_putt = False
        measured = yards_between(ball, rest)
        if learn:
            # The notebook only ever learns from fairway — a number taken off rough or sand is not a number —
            # and so do the conditions, for the same reason: a ball that comes back 45% short out of sand
            # tells the athlete nothing about the wind, and a coefficient fitted through it would learn a
            # headwind that was a bunker. That is the same error as the rough coefficient that came out at
            # 0.46 for a true 0.20.
            if lie == "fairway":
                if ath.n[club.name][gear] >= 4:
                    ath.observe_conditions(head, measured / max(1.0, predicted))
                # the notebook is a calm-day notebook: a shot with the wind behind it is divided back to
                # what it would have done in still air, or the student learns that its driver goes 317.
                ath.observe(club.name, gear, measured / max(0.5, cost))
                ath.observe_side(lateral_aim, flown_yd, aim_used, cross)
        if res.get("lip"):
            lip_seen = True
        elif not in_sand(rest, hole):
            lip_seen = False
        log.append(dict(kind="shot", club=club.name, gear=gear, effort=effort,
                        carried=res["carry"] / FT_PER_YD,
                        ran=res["roll"] / FT_PER_YD, total=measured, along=along, lateral=lateral,
                        # The number that shows whether the notebook is being learned: what it said the
                        # shot would do against what it did. Not the miss to the flag — that is mostly the
                        # coarseness of the gear ladder, and it says nothing about the player's knowledge.
                        predicted=predicted, notebook_err=abs(measured - predicted) / max(1.0, predicted),
                        angle=math.degrees(math.atan2(lateral, max(1.0, gap_ft / FT_PER_YD))),
                        angle_aim=math.degrees(math.atan2(lateral_aim, flown_yd)),
                        offset=offset, head=head, cross=cross, lie=lie, on_green=on_green(rest, hole),
                        in_sand=in_sand(rest, hole), escaping=escaping, hit_lip=bool(res.get("lip")),
                        strokes_at=strokes, gap_ft=gap_ft, start=ball,
                        path=res.get("path"), stop_at=res.get("stop_at"),
                        aim=aim, bearing=aim_bearing))
        if verbose:
            side = "right" if lateral > 0 else "left"
            depth = "short" if along < 0 else "long"
            mark = " green" if on_green(rest, hole) else (" SAND" if in_sand(rest, hole) else "")
            mark = " LIP" if res.get("lip") else mark
            mark = " OUT" if escaping else mark
            print(f"  {tag}{hole.label:>3} {hole.yards:4.0f} yd par {hole.par}   "
                  f"{club.name:<11} {effort * 100:3.0f}%  {measured:5.1f} yd   "
                  f"{abs(along):5.1f} {depth:<5} {abs(lateral):4.1f} {side:<5} "
                  f"aim {offset:+5.1f} ft  {lie:<7}{mark}")
        ball = rest
    if not holed and putts == 0 and verbose:
        print(f"  {tag}{hole.label:>3} {'':>4} {'':>12} picked up")
    approaches = [e for e in log if e["kind"] == "shot"]
    return dict(hole=hole, strokes=strokes, putts=putts, penalties=penalties, log=log, holed=holed,
                to_green=len(approaches), gir=len(approaches) <= max(1, hole.par - 2),
                in_sand=sum(1 for e in approaches if e.get("in_sand")))


def play_round(holes, ath: Athlete, putter: PuttAthlete, green: Green,
               learn: bool = True, verbose: bool = True, tag: str = "",
               rng: random.Random | None = None) -> dict:
    rng = rng or random.Random(DEFAULT_SEED)
    rows = [play_hole(h, ath, putter, green, learn=learn, verbose=verbose, tag=tag, rng=rng)
            for h in holes]
    strokes = sum(r["strokes"] for r in rows)
    par = sum(h.par for h in holes)
    shots = [e for r in rows for e in r["log"] if e["kind"] == "shot"]
    nerr = sum(e["notebook_err"] for e in shots) / len(shots) if shots else 0.0
    miss = sum(abs(e["along"]) for e in shots) / len(shots) if shots else 0.0
    angle = sum(abs(e["angle"]) for e in shots) / len(shots) if shots else 0.0
    if verbose:
        print(f"  {'':>3} round {'':>10} {strokes} strokes, par {par}, {strokes - par:+3d}"
              f"   putts {sum(r['putts'] for r in rows)}   penalties {sum(r['penalties'] for r in rows)}"
              f"   miss {miss:4.1f} yd, notebook off by {nerr * 100:4.1f}%, {angle:4.2f}° off line")
    return dict(rows=rows, strokes=strokes, par=par, to_par=strokes - par, nerr=nerr,
                angle=angle, miss=miss)


# ---- the checks the numbers rest on ----------------------------------------------------------------
def selftest() -> int:
    fails, n = [], 0

    def check(name: str, ok: bool, note: str) -> None:
        nonlocal n
        n += 1
        print(f"  [{'ok' if ok else 'FAIL'}] {name}: {note}")
        if not ok:
            fails.append(name)

    # 1. the integrator itself, on a case with an answer you can write down
    vac = flight((0, 0, 0.0), (100 * math.cos(math.radians(45)), 0.0, 100 * math.sin(math.radians(45))),
                 (0.0, 0.0), "fairway", net_check=False, cl=0.0, drag=0.0, lift=0.0,
                 surfaces={"fairway": {"e": 0.4, "f": 1.0}}, t_max=10)
    rng = math.hypot(*vac["land"])
    check("vacuum range 45° at 100 ft/s", abs(rng - 100 ** 2 / G) < 1.0,
          f"{rng:.2f} ft vs v²/g = {100 ** 2 / G:.2f}")

    # 2. drag takes distance away. Same launch, no spin, drag on and off: the ball with drag must be short.
    v45 = (100 * math.cos(math.radians(45)), 0.0, 100 * math.sin(math.radians(45)))
    base = {"fairway": {"e": 0.4, "f": 1.0}}
    pulled = flight((0, 0, 0.0), v45, (0.0, 0.0), "fairway", net_check=False, cl=0.0,
                    drag=0.0015, lift=LIFT_BASE, surfaces=base, t_max=20)
    free = flight((0, 0, 0.0), v45, (0.0, 0.0), "fairway", net_check=False, cl=0.0,
                  drag=0.0, lift=LIFT_BASE, surfaces=base, t_max=20)
    check("drag takes distance away", math.hypot(*pulled["land"]) < 0.9 * math.hypot(*free["land"]),
          f"{math.hypot(*pulled['land']):.1f} ft with drag against {math.hypot(*free['land']):.1f} free")

    # 3. backspin holds the ball up. Same flight, same drag, spin off: the ball must fall short.
    d = CLUB_BY_NAME["driver"]
    v_d = (d.speed_mph * MPH * math.cos(math.radians(d.launch)), 0.0,
           d.speed_mph * MPH * math.sin(math.radians(d.launch)))
    cl_d, drag_d = aero(d, d.speed_mph * MPH)
    with_drag = flight((0, 0, 0.0), v_d, (0.0, 0.0), "fairway", net_check=False, cl=-cl_d,
                       drag=drag_d, lift=LIFT_BASE, surfaces=base, t_max=20)
    flat = flight((0, 0, 0.0), v_d, (0.0, 0.0), "fairway", net_check=False, cl=0.0,
                  drag=drag_d, lift=LIFT_BASE, surfaces=base, t_max=20)
    spin_gain = math.hypot(*with_drag["land"]) - math.hypot(*flat["land"])
    check("backspin adds carry", spin_gain > 30.0, f"+{spin_gain / 3:.1f} yd from 2686 rpm")

    # 4. the bag, in order, in the band the calibration was aimed at
    carries = {c.name: shot((0.0, 0.0), c, 1.0, 0.0)["carry"] / FT_PER_YD for c in CLUBS}
    order_ok = all(carries[CLUBS[i].name] > carries[CLUBS[i + 1].name] for i in range(len(CLUBS) - 1))
    resid = max(abs(carries[c.name] - c.prior_carry) for c in CLUBS)
    check("bag is monotone", order_ok, ", ".join(f"{n} {v:.0f}" for n, v in carries.items()))
    check("calibration residual", resid < 12.0, f"worst club {resid:.1f} yd off its prior carry")

    # 5. putt's friction law, used unchanged: a ball at 6 ft/s rolls the stimp reading
    a = STIMPMETER_SPEED ** 2 / (2 * 10.0)
    roll = STIMPMETER_SPEED ** 2 / (2 * a)
    check("roll law is putt's", abs(roll - 10.0) < 1e-9, f"6.0 ft/s rolls {roll:.2f} ft on a 10 stimp")

    # 6. determinism: one shot, twice
    a1 = shot((0.0, 0.0), CLUB_BY_NAME["7 iron"], 0.87, 3.0)["rest"]
    a2 = shot((0.0, 0.0), CLUB_BY_NAME["7 iron"], 0.87, 3.0)["rest"]
    check("same swing, same ball", a1 == a2, f"{a1[0]:.4f},{a1[1]:.4f} both times")

    # 7. the experiment: does three rounds of nine teach this athlete anything
    green = Green(stimp=10.0, grade=1.2, downhill=135.0)
    ath, putter = Athlete(), PuttAthlete()
    scores = [play_round(COURSE, ath, putter, green, learn=True, verbose=False)["to_par"]
              for _ in range(3)]
    held = play_round(HELD_OUT, ath, putter, green, learn=True, verbose=False)["to_par"]
    ctrl_ath, ctrl_putter = Athlete(), PuttAthlete()
    ctrl = [play_round(COURSE, ctrl_ath, ctrl_putter, green, learn=False, verbose=False)["to_par"]
            for _ in range(3)]
    check("learning player improves", scores[2] < scores[0], f"rounds {scores}, held-out {held:+d}")
    check("control does not", ctrl[2] >= ctrl[0], f"no learning: {ctrl}")
    # Only the entries it has actually hit twice or more can be held against the truth. An entry nobody
    # ever plays is not a failure of the notebook; it is a shot this course never asked for, and saying so
    # is the difference between a check and a decoration.
    used, errs, worst_at, worst = 0, [], "", 0.0
    for c in CLUBS:
        for g in GEARS:
            if ath.n[c.name][g] < 2:
                continue
            used += 1
            e = abs(ath.table[c.name][g] - shot((0.0, 0.0), c, g, 0.0)["total"] / FT_PER_YD)
            e /= max(1.0, bag()[c.name] * g)
            errs.append(e)
            if e > worst:
                worst, worst_at = e, f"{c.name} at {g:.0%}"
    mean = sum(errs) / max(1, len(errs))
    check("the notebook converges where it is used", used >= 8 and mean < 0.04 and worst < 0.15,
          f"{used} entries hit twice or more: {mean:.1%} off on average, worst {worst_at} {worst:.1%}"
          f" (two observations and 1.5% of speed noise do not buy better)")
    learned = [(ath.table[c.name][0.6] / ath.table[c.name][1.0])
               for c in CLUBS if ath.n[c.name][0.6] >= 2 and ath.n[c.name][1.0] >= 2]
    truth = [(shot((0.0, 0.0), c, 0.6, 0.0)["total"] / shot((0.0, 0.0), c, 1.0, 0.0)["total"])
             for c in CLUBS if ath.n[c.name][0.6] >= 2 and ath.n[c.name][1.0] >= 2]
    lm = sum(learned) / max(1, len(learned))
    tm = sum(truth) / max(1, len(truth))
    check("the notebook finds the curve", len(learned) >= 1 and abs(lm - tm) < 0.08,
          f"a 60% swing is {lm:.2f} of a full one over {len(learned)} clubs, learnt; {tm:.2f} is true; "
          f"0.60 was assumed")

    # 12. the air: a headwind shortens a shot, and a crosswind pushes it aside at a rate the model can be
    # asked about directly — 32 degrees per unit of crosswind fraction, which is the number the athlete's
    # silence about crosswinds is built on.
    iron = CLUB_BY_NAME["7 iron"]
    calm_shot = shot((0.0, 0.0), iron, 1.0, 0.0)
    head_shot = shot((0.0, 0.0), iron, 1.0, 0.0, wind=(0.0, -WIND_REF_SPEED * 0.1))
    check("a headwind takes distance off", head_shot["total"] < 0.95 * calm_shot["total"],
          f"{calm_shot['total'] / 3:.1f} yd calm, {head_shot['total'] / 3:.1f} yd into 10% of a ball speed")
    angles = []
    for frac in (0.05, 0.10, 0.15):
        r = shot((0.0, 0.0), iron, 1.0, 0.0, wind=(WIND_REF_SPEED * frac, 0.0))
        angles.append(math.degrees(math.atan2(r["rest"][0], r["rest"][1])) / frac)
    drift = sum(angles) / len(angles)
    check("a crosswind drifts it aside linearly", max(angles) - min(angles) < 1.5,
          f"{drift:.1f}° per unit of crosswind, spread {min(angles):.1f}–{max(angles):.1f}")

    # 13. the conditions it can learn, and the target decision it can then make
    windy = list(COURSE)
    ath2, put2 = Athlete(), PuttAthlete()
    for _ in range(4):
        play_round(windy, ath2, put2, green, learn=True, verbose=False)
    check("it learns what the wind costs", 0.3 < ath2.wind_c < 1.4,
          f"wind_c {ath2.wind_c:.2f} (the model's own response is about 0.7 per unit of head fraction)")
    still = [Hole(*c) for c in CALM]   # the same flags on a still day
    trained = Athlete()
    trained.policy = "spread"
    put3 = PuttAthlete()
    for _ in range(4):
        play_round(still, trained, put3, green, learn=True, verbose=False)
    scored = {}
    for pol in ("flag", "spread"):
        a = copy_of(trained)
        a.policy = pol
        scored[pol] = sum(play_round(still, a, PuttAthlete(), green, learn=False, verbose=False,
                                     rng=random.Random(DEFAULT_SEED))["strokes"] for _ in range(4))
    check("and with an honest scatter the pin is a fine target on the nine", scored["spread"] <= scored["flag"],
          f"{scored['spread']} strokes against {scored['flag']} over four calm rounds — the spread policy is "
          f"never better on my own pins, whose flags sit no further out than ±14 ft")

    # 14. the target decision, measured over drawn pins instead of my nine: its value has to grow as the pins
    # get tucked. If it did not, the whole of finding 3 would be a property of the table I typed in.
    #
    # Since pass 8 this is measured over *bags* as well as courses. One athlete on one run of practice rounds
    # gave +0.68 at ±19 and another, a round further on, gave −0.60: the paired design cancels the course and
    # not the notebook, and the notebook is what the aim is drawn on. Three bags, twelve courses each, is the
    # smallest version that does not read its own noise as a finding.
    def paired_advantage(pin_range: float, draws: int = 12, bags: int = 3) -> float:
        by_bag = []
        for b in range(bags):
            a0 = Athlete()
            a0.policy = "spread"
            pu = PuttAthlete()
            for k in range(3):
                play_round(drawn_course(random.Random(9000 + k), pin_range, True), a0, pu, green,
                           learn=True, verbose=False, rng=random.Random(DEFAULT_SEED + 7919 * b + k))
            tot = 0.0
            for k in range(draws):
                course = drawn_course(random.Random(4000 + k), pin_range, True)
                row = {}
                for pol in ("flag", "spread"):
                    a = copy_of(a0)
                    a.policy = pol
                    row[pol] = play_round(course, a, PuttAthlete(), green, learn=False, verbose=False,
                                          rng=random.Random(DEFAULT_SEED))["to_par"]
                tot += row["flag"] - row["spread"]
            by_bag.append(tot / draws)
        return sum(by_bag) / bags

    tight, friendly = paired_advantage(19.0), paired_advantage(6.0)
    check("a tucked pin is what makes the target decision worth anything",
          tight - friendly > 1.0 and tight > 0.5,
          f"aiming at the pin instead of where the putt is likeliest is worth {tight:+.2f} strokes on pins cut "
          f"19 ft out and {friendly:+.2f} on pins cut 6 ft out, over 3 bags × 12 drawn courses each")

# 17. the sand is where the hole says it is, and only there
    left_hole, right_hole, none = (Hole(400, 4, "S", pin=10.0, sand=-1), Hole(400, 4, "S", pin=10.0, sand=+1),
                                   Hole(400, 4, "S", pin=10.0, sand=0))
    y = 400.0 * FT_PER_YD
    check("the sand is on the side the hole says",
          in_sand((GREEN_A + 7.0, y), right_hole) and not in_sand((GREEN_A + 7.0, y), left_hole)
          and not in_sand((GREEN_A + 7.0, y), none)
          and in_sand((-GREEN_A - 7.0, y), left_hole) and not in_sand((-GREEN_A - 7.0, y), right_hole)
          and not in_sand((0.0, y), right_hole),
          f"27 ft right of centre is sand on a right bunker and grass on a left one and on none")

    # 18. sand takes most of the distance and more than half of the run
    wedge = CLUB_BY_NAME["sand wedge"]
    off_grass, off_sand = shot((0.0, 0.0), wedge, 1.0, 0.0), shot((0.0, 0.0), wedge, 1.0, 0.0, lie="sand")
    keeps = off_sand["total"] / off_grass["total"]
    check("sand takes the distance and the run",
          abs(keeps - (1.0 - SAND_LOSS)) < 0.06 and off_sand["roll"] < 0.7 * off_grass["roll"],
          f"a wedge keeps {keeps:.2f} of its distance (told {1.0 - SAND_LOSS:.2f}) and "
          f"{off_sand['roll'] / off_grass['roll']:.2f} of its run-out")

    # 18b. the face itself: a ball lying a foot from it cannot be got out forwards by anything in the bag,
    # and one six feet away can — and the athlete that finds itself against the face plays out, not again
    sandy = Hole(400, 4, "S", pin=0.0, sand=+1)
    close, far = (GREEN_A + 1.0, y), (GREEN_A + 7.0, y)
    b_close = math.degrees(math.atan2(-close[0], 0.0))
    b_far = math.degrees(math.atan2(-far[0], 0.0))
    tries = {c.name: bool(shot(close, c, 1.0, b_close, lie="sand",
                               lip=lip_distance(close, b_close, sandy)).get("lip")) for c in CLUBS}
    clears_far = not shot(far, CLUB_BY_NAME["sand wedge"], 1.0, b_far, lie="sand",
                          lip=lip_distance(far, b_far, sandy)).get("lip")
    check("a foot from the face, nothing gets out forwards", all(tries.values()),
          "hits the face: " + ", ".join(n for n, hit in tries.items() if hit))
    check("six feet from it, a wedge does", clears_far,
          f"a putter would not, and the athlete does not try it: the face is {LIP_H:.1f} ft and a sand wedge "
          f"is 28°, so it needs {LIP_H / math.tan(math.radians(28.0)):.1f} ft of run")
    esc = play_hole(sandy, copy_of(ath), PuttAthlete(), green, learn=False, verbose=False,
                    rng=random.Random(7), start=close)
    first = next(e for e in esc["log"] if e["kind"] == "shot")
    check("and the athlete plays out instead of into it twice", first["escaping"] and not first["hit_lip"],
          f"first stroke from 1 ft out of the face: club {first['club']} {first['gear']:.0%}, "
          f"escaping {first['escaping']}, {esc['strokes']} strokes to hole out")

    # 19. what a ball in the sand is worth, played through the game rather than a second copy of its rules:
    # a hole started on the sand, and the same hole started on the green two feet nearer the hole
    def strokes_from(point: tuple[float, float], hole: Hole) -> int:
        return play_hole(hole, copy_of(ath), PuttAthlete(), green, learn=False, verbose=False,
                         rng=random.Random(7), start=point)["strokes"]

    near = Hole(400, 4, "S", pin=0.0, sand=+1)
    nn = 40
    from_green = sum(strokes_from((19.0, y), near) for _ in range(nn)) / nn
    from_sand = sum(strokes_from((21.5, y), near) for _ in range(nn)) / nn
    check("a ball in the sand is worth what it is told it is worth",
          1.0 <= from_sand - from_green <= 3.0 and abs((from_sand - from_green) - ath.sand_pen) < 0.6,
          f"from 21 ft in the sand {from_sand:.2f} strokes against {from_green:.2f} from the green "
          f"({from_sand - from_green:+.2f}): the athlete prices it at {ath.sand_pen:.2f}. It priced it at "
          f"1.00 by guess in pass 4, and 0.30 while there was no lip, when sand really was cheap")

    # 19b-19c. the two costs `target()` is made of. Pass 10 replaced a step function with them, and a cost
    # that nobody measures is the same kind of object as the 25 ft step was: a number I wrote down.
    def short_game(kind: str, d: float, bearings: int = 8) -> tuple[float, int]:
        """Strokes to hole out from `d` feet, over the bearings on which a ball at that distance lies in
        `kind`. Played through the game, not through a second copy of its rules."""
        h = Hole(400, 4, "C", pin=13.0, sand=+1)
        out = []
        for b in range(bearings):
            a = math.radians(360.0 * b / bearings)
            p = (h.centre[0] + math.sin(a) * d, h.centre[1] + math.cos(a) * d)
            got = "sand" if in_sand(p, h) else ("green" if on_green(p, h) else "rough")
            if got != kind:
                continue
            out.append(play_hole(h, copy_of(ath), PuttAthlete(), green, learn=False, verbose=False,
                                 start=p, rng=random.Random(7))["strokes"])
        return (sum(out) / len(out), len(out)) if out else (float("nan"), 0)

    near_c, _ = short_game("green", 2.5)
    far_c, _ = short_game("green", 24.0)
    check("the green costs the same from 2 ft as from 24",
          abs(near_c - far_c) < 0.4 and abs(near_c - COST_ON_GREEN) < 0.4,
          f"{near_c:.2f} strokes from 2.5 ft and {far_c:.2f} from 24 ft, against the {COST_ON_GREEN:.2f} the "
          f"objective is told. They are the same number because the putter is deterministic — it bisects its "
          f"gain and its line to zero error and the roll has no scatter — so there is no gradient in distance "
          f"on this green for any objective to spend, and the 25 ft step this replaced was standing in for one")
    off_c_36, n36 = short_game("rough", 36.0, bearings=16)
    off_c_60, n60 = short_game("rough", 60.0, bearings=16)
    off_c = (off_c_36 * n36 + off_c_60 * n60) / (n36 + n60)
    check("off the green costs a chip more than on it",
          abs(off_c - COST_OFF_GREEN) < 0.35 and off_c > near_c + 0.3,
          f"{off_c:.2f} strokes off the green ({n36 + n60} bearings at 36 and 60 ft) against {near_c:.2f} on "
          f"it and {COST_OFF_GREEN:.2f} told. It is not one number in the world — it is 2 or 3 depending on "
          f"whether the chip goes in and which way the slope runs ({off_c_36:.2f} at 36 ft, {off_c_60:.2f} at "
          f"60) — and the objective flattens it, which is the next thing standing between this model and golf")

    # 20. the notebook learns nothing from sand: same reason as the rough, one lie further out
    sand_ath, sand_put = Athlete(), PuttAthlete()
    for h in COURSE:
        play_hole(h, sand_ath, sand_put, green, learn=True, verbose=False, rng=random.Random(DEFAULT_SEED))
    obs = sand_ath.shots
    fairway_shots = 0
    sand_ath, sand_put = Athlete(), PuttAthlete()
    for h in COURSE:
        r = play_hole(h, sand_ath, sand_put, green, learn=True, verbose=False, rng=random.Random(DEFAULT_SEED))
        fairway_shots += sum(1 for e in r["log"] if e["kind"] == "shot" and e["lie"] == "fairway")
    check("the notebook learns nothing from sand", obs == fairway_shots,
          f"{obs} entries updated, {fairway_shots} shots struck from fairway")

    # 21. the negative this pass exists to report: the bunker is almost never reached, and adding it does
    # not make the target decision directional. This is the check that could have gone the other way.
    def sand_experiment(draws: int = 20, pin_range: float = 19.0):
        """The same courses twice — bunkers in, bunkers filled in — paired by hole, split by which side of
        the green the flag was cut. The quantity is how much adding the sand changes *what aiming away from
        the pin is worth*, which is the thing the pass predicted it would raise and did not."""
        seen, hit = 0, 0
        diffs = {"toward": [], "away": []}
        for k in range(draws):
            base = drawn_course(random.Random(4000 + k), pin_range, True)
            bare = [Hole(h.yards, h.par, h.label, pin=h.pin, wind=h.wind, sand=0) for h in base]
            got = {}
            for tag_, course_ in (("in", base), ("out", bare)):
                for p_ in ("flag", "spread"):
                    a = copy_of(ath)
                    a.policy = p_
                    rr = play_round(course_, a, PuttAthlete(), green, learn=False, verbose=False,
                                    rng=random.Random(DEFAULT_SEED))
                    got[(tag_, p_)] = rr["rows"]
            for i, h in enumerate(base):
                if not h.sand or abs(h.pin) < 8.0:
                    continue
                for e in got[("in", "flag")][i]["log"]:
                    if e["kind"] != "shot":
                        continue
                    seen += 1
                    hit += 1 if e.get("in_sand") else 0
                d = ((got[("in", "flag")][i]["strokes"] - got[("in", "spread")][i]["strokes"])
                     - (got[("out", "flag")][i]["strokes"] - got[("out", "spread")][i]["strokes"]))
                diffs["toward" if h.pin * h.sand > 0 else "away"].append(d)
        return (seen, hit,
                sum(diffs["toward"]) / max(1, len(diffs["toward"])),
                sum(diffs["away"]) / max(1, len(diffs["away"])))

    seen, hit, toward, away = sand_experiment()
    check("the bunker is almost never reached", hit / max(1, seen) < 0.10,
          f"{hit} of {seen} approaches at a tucked pin beside the sand finished in it "
          f"({hit / max(1, seen):.1%}); a flank bunker needs the depth right as well as the face wrong")
    check("and so it does not make the decision directional",
          toward < 0.3 and abs(toward - away) < 0.4,
          f"adding the sand moves what aiming away from the pin is worth by {toward:+.2f} strokes when the pin "
          f"is cut toward it and {away:+.2f} when it is cut away — the prediction was that the first would "
          f"rise by more than a stroke, and it does not rise at all")

    # 26-28. the scatter it believes against the scatter its shots have. Pass 8 is the pass that found the
    # first of these by measuring it: until then the athlete read its own scatter off the flag, so the offset
    # it aims by on purpose counted as a miss, and it believed it was half again as wild as it was.
    def trained_sigma(calm: bool, rounds: int = 4):
        a, pu = Athlete(), PuttAthlete()
        for k in range(rounds):
            for h in drawn_course(random.Random(3000 + k), 14.0, calm):
                play_hole(h, a, pu, green, learn=True, verbose=False, rng=random.Random(DEFAULT_SEED + k))
        return a

    calm_ath = trained_sigma(True)
    check("the scatter it learns is the scatter its hands have",
          abs(calm_ath.sigma - FACE_SD) < 0.3,
          f"it believes {calm_ath.sigma:.2f}° and the hands are {FACE_SD:.2f}° — this check exists because "
          f"for six passes the athlete read its misses off the flag and believed 1.5° for the same hands")

    windy_ath = trained_sigma(False)
    windy_rows = []
    for k in range(2):
        course = drawn_course(random.Random(3500 + k), 14.0, False)
        for h in course:
            r = play_hole(h, windy_ath, PuttAthlete(), green, learn=False, verbose=False,
                          rng=random.Random(DEFAULT_SEED + 40 + k))
            windy_rows += [e for e in r["log"] if e["kind"] == "shot" and e.get("angle_aim") is not None]
    all_sd = _sd([e["angle_aim"] for e in windy_rows])
    quiet_sd = _sd([e["angle_aim"] for e in windy_rows if abs(e["cross"]) <= CROSS_QUIET])
    check("the gate shows it the still air while the wind scatters the ball",
          all_sd > 1.5 * quiet_sd and windy_ath.sigma < 0.75 * all_sd,
          f"in wind its shots scatter {all_sd:.2f}° and the shots the gate lets through scatter {quiet_sd:.2f}°; "
          f"it believes {windy_ath.sigma:.2f}° — too bold by a factor of {all_sd / windy_ath.sigma:.1f}, which "
          f"is the opposite of what the sixth pass suspected")

    probe = Athlete()
    probe.aim_bias = 0.0
    hole40 = Hole(400, 4, "T", pin=13.0, sand=+1)
    hole200 = Hole(400, 4, "T", pin=13.0, sand=+1)
    near = [copy_of(probe) for _ in range(2)]
    for a, sig in zip(near, (0.6, 3.0)):
        a.sigma = sig
    far = [copy_of(probe) for _ in range(2)]
    for a, sig in zip(far, (0.6, 3.0)):
        a.sigma = sig
    near_t = [a.target(hole40, (13.0, hole40.centre[1] - 40.0), 40.0) for a in near]
    far_t = [a.target(hole200, (13.0, hole200.centre[1] - 200.0), 200.0) for a in far]
    check("the belief reaches the target at every range, not only past 76 ft",
          near_t[0] - near_t[1] >= 3.0 and far_t[0] - far_t[1] >= 3.0,
          f"from 40 ft a scatter of 0.6° aims at {near_t[0]:+.0f} ft and one of 3.0° at {near_t[1]:+.0f}; from "
          f"200 ft at {far_t[0]:+.0f} and {far_t[1]:+.0f}. Until pass 9 the floor in `target()` was 2 ft, which "
          f"is wider than a 1° scatter inside 76 ft, and both of those short answers were the same number")

    # 29. Taking the floor out made the objective *flat* over a band — every target from which the ball is
    # certain to be on the green and inside 25 ft of the pin scores the same — and the scan was answering
    # with whichever end of the band it reached first. That is a fact about range(-45, 46). Ties are now
    # broken at the flag, and an interior pin is the case where every policy has to agree.
    band = []
    for pin in (-6.0, 0.0, 6.0):
        h = Hole(400, 4, "T", pin=pin, sand=+1)
        for sig in (0.5, 3.0):
            a = copy_of(probe)
            a.sigma = sig
            band.append(a.target(h, (13.0, h.centre[1] - 40.0), 40.0))
    check("a flat objective is broken at the flag, not at the end of the scan",
          band == [-6.0, -6.0, 0.0, 0.0, 6.0, 6.0],
          f"pins −6/0/+6 from 40 ft, a 0.5° and a 3.0° belief: {', '.join(f'{x:+.0f}' for x in band)}. The "
          f"floor never bound on this hole — it answers the same with 2 ft or 0.5 — so this is the tie-break "
          f"alone: before it, a pin at 0 from 40 ft was answered −15 ft, the left end of a band the objective "
          f"scores as flat, because that is where `for k in range(-45, 46)` starts counting")

    print(f"\n  {len(fails)} of {n} checks failed" if fails else f"\n  all {n} checks pass")
    return 1 if fails else 0


def copy_of(ath: Athlete) -> Athlete:
    """A settled athlete, cloned: the target decision is measured on one who has finished learning, so the
    three policies are compared with the same notebook, the same hands and the same draw."""
    b = Athlete()
    b.table = {k: dict(v) for k, v in ath.table.items()}
    b.n = {k: dict(v) for k, v in ath.n.items()}
    b.aim_bias, b.sigma = ath.aim_bias, ath.sigma
    b.wind_c, b.rough_cost, b.sand_pen = ath.wind_c, ath.rough_cost, ath.sand_pen
    b.sigma_taught = ath.sigma_taught
    b.gate = ath.gate
    b.face = ath.face
    return b


def compare(args) -> int:
    green = Green(stimp=10.0, grade=1.2, downhill=135.0)
    course = [Hole(*c) for c in CALM] if args.calm else COURSE
    trained = Athlete()
    trained.policy = "spread"
    putter = PuttAthlete()
    for i in range(4):
        play_round(course, trained, putter, green, learn=True, verbose=False,
                   rng=random.Random(DEFAULT_SEED))
    print(f"trained: four rounds, notebook off by "
          f"{play_round(course, trained, putter, green, learn=False, verbose=False, rng=random.Random(DEFAULT_SEED))['nerr'] * 100:.1f}%"
          f"  aim bias {trained.aim_bias:+.2f}°  sigma {trained.sigma:.2f}°")
    print("\nfour rounds each, same notebook, same seed, learning off:")
    print(f"  {'policy':8s} {'strokes':>8s} {'to par':>7s} {'GIR':>7s} {'putts':>6s}")
    for policy in ("flag", "centre", "spread"):
        a = copy_of(trained)
        a.policy = policy
        rows = [play_round(course, a, PuttAthlete(), green, learn=False, verbose=False,
                           rng=random.Random(DEFAULT_SEED)) for _ in range(4)]
        strokes = sum(r["strokes"] for r in rows)
        greens = sum(1 for r in rows for row in r["rows"] if row["gir"])
        putts = sum(row["putts"] for r in rows for row in r["rows"])
        print(f"  {policy:8s} {strokes:8d} {strokes - 35 * 4:+7d} {greens:5d}/36 {putts:6d}")
    return 0


def draws(args) -> int:
    """One trained athlete, many courses, all policies, paired by course — repeated over several bags.

    Training is on drawn courses too, four of them, learning on — so the notebook is not tuned to my nine pins
    either. Evaluation is learning off, one round a course, every policy on the same course, and the quantity
    reported is the *paired* difference: the same draw in both columns, which is the only way a nine-hole score
    gets an error bar small enough to argue with.

    **And the bags are drawn too, since pass 8.** Until then every number here was measured on *one* athlete:
    one run of four practice courses, one notebook, one set of club distances. Re-running the same experiment
    with a fifth practice course — the athlete's hands and scatter almost identical, its eight-iron half a yard
    different — flipped the sign of the pinned-pin result at ±19 ft, +0.68 one way and −0.60 the other. The
    paired design cancels the *course*, not the *bag*, and the bag is as much a draw as the weather is. So
    `--bags N` trains N athletes on different practice sets and reports the mean of the per-bag differences
    with the spread *across bags* as the error bar. That is a wider bar, and it is the bar the claim needs.

    Since pass 4 there is a second table, over holes rather than rounds, split by where the pin was cut
    relative to the sand. That split was *declared before the run*, and it is the test of whether pass 3's
    finding is about pin tuck or about a green with nothing on it: if a tuck toward fourteen feet of sand and
    a tuck toward fourteen feet of grass are the same number, the bunker bought nothing.
    """
    green = Green(stimp=10.0, grade=1.2, downhill=135.0)
    n, bags = args.draws, max(1, args.bags)
    policies = ("flag", "centre", "spread")
    combos = (("flag", "centre"), ("flag", "spread"), ("centre", "spread"))
    per_bag = {p: [] for p in policies}
    diff_bag = {c: [] for c in combos}
    hole_bag = {k: [] for k in ("tucked_sand", "away_sand", "friendly_sand", "none_tucked", "none_friendly")}
    sand_bag = {k: [] for k in ("tucked_sand", "away_sand", "friendly")}
    tucked = lambda h: abs(h.pin) >= 8.0          # noqa: E731  declared before the run, not chosen after
    hole_key = {"tucked_sand": lambda h: h.sand != 0 and tucked(h) and h.pin * h.sand > 0,
                "away_sand": lambda h: h.sand != 0 and tucked(h) and h.pin * h.sand < 0,
                "friendly_sand": lambda h: h.sand != 0 and not tucked(h),
                "none_tucked": lambda h: h.sand == 0 and tucked(h),
                "none_friendly": lambda h: h.sand == 0 and not tucked(h)}
    for bag in range(bags):
        trained = Athlete()
        trained.policy = "spread"
        putter = PuttAthlete()
        # The bag is drawn from the *practice session*, not from the pins: in still air the pin changes where the
        # shot is aimed and not how far it is hit, so two athletes practising on different pins end up with the
        # same notebook to two decimal places — measured, before this line was written. What a bag really varies
        # with is where the practice shots finished, and that is the seed.
        for k in range(4):
            play_round(drawn_course(random.Random(9000 + k), args.pin_range, args.calm),
                       trained, putter, green, learn=True, verbose=False,
                       rng=random.Random(DEFAULT_SEED + 7919 * bag + k))
        scores = {p: [] for p in policies}
        per_hole = {p: [] for p in policies}
        for d in range(n):
            course = drawn_course(random.Random(4000 + d), args.pin_range, args.calm)
            for p in policies:
                a = copy_of(trained)
                a.policy = p
                r = play_round(course, a, PuttAthlete(), green, learn=False, verbose=False,
                               rng=random.Random(DEFAULT_SEED))
                scores[p].append(r["to_par"])
                per_hole[p].extend((h, row["strokes"]) for h, row in zip(course, r["rows"]))
        for p in policies:
            per_bag[p].append(sum(scores[p]) / n)
        for c in combos:
            diff_bag[c].append(sum(x - y for x, y in zip(scores[c[0]], scores[c[1]])) / n)
        pairs = list(zip(per_hole["flag"], per_hole["spread"]))
        for key, keep in hole_key.items():
            d = [x - y for (h, x), (_, y) in pairs if keep(h)]
            hole_bag[key].append(sum(d) / len(d) if d else 0.0)
        # the clean version: the same courses with the bunkers filled in. The table above compares holes that
        # differ in more ways than the sand — the sandless holes are a par 3 and two par 5s — so the treatment
        # is a course with its bunkers taken out: same pins, same winds, same draw, and the only difference
        # between the two columns is the sand.
        got_sand = {"tucked_sand": [], "away_sand": [], "friendly": []}
        for d in range(n):
            base = drawn_course(random.Random(4000 + d), args.pin_range, args.calm)
            bare = [Hole(h.yards, h.par, h.label, pin=h.pin, wind=h.wind, sand=0) for h in base]
            rows = {}
            for tag_, course_ in (("in", base), ("out", bare)):
                for p_ in ("flag", "spread"):
                    a = copy_of(trained)
                    a.policy = p_
                    r = play_round(course_, a, PuttAthlete(), green, learn=False, verbose=False,
                                   rng=random.Random(DEFAULT_SEED))
                    rows[(tag_, p_)] = [row["strokes"] for row in r["rows"]]
            for i, h in enumerate(base):
                if not h.sand:
                    continue
                a_in = rows[("in", "flag")][i] - rows[("in", "spread")][i]
                a_out = rows[("out", "flag")][i] - rows[("out", "spread")][i]
                key = ("tucked_sand" if tucked(h) and h.pin * h.sand > 0 else
                       "away_sand" if tucked(h) else "friendly")
                got_sand[key].append(a_in - a_out)
        for key, xs in got_sand.items():
            sand_bag[key].append(sum(xs) / len(xs) if xs else 0.0)

    def band(xs: list[float], label: str, note: str = "") -> None:
        m = sum(xs) / len(xs)
        if len(xs) > 1:
            se = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) / math.sqrt(len(xs))
        else:
            se = float("nan")
        t = m / se if se and se > 0 else 0.0
        print(f"    {label:<44s} {m:+6.2f} ± {1.96 * se:4.2f}   t {t:+5.1f}   {note}")

    print(f"{n} courses drawn independently (pins ±{args.pin_range:.0f} ft"
          f"{', still air' if args.calm else ', wind drawn too'}), one round each, learning off, "
          f"over {bags} bag{'s' if bags > 1 else ''}\n")
    print(f"  {'policy':8s} {'mean':>7s} {'sd across bags':>16s}")
    for p in policies:
        xs = per_bag[p]
        m = sum(xs) / len(xs)
        sd = math.sqrt(sum((x - m) ** 2 for x in xs) / max(1, len(xs) - 1)) if len(xs) > 1 else float("nan")
        print(f"  {p:8s} {m:+7.2f} {sd:16.2f}")
    print("\n  paired differences, strokes a round (negative means the first is better):")
    print(f"  {'':<22s}{'mean':>8s}{'95%':>8s}{'t':>7s}")
    for c in combos:
        band(diff_bag[c], f"  {c[0]:6s} - {c[1]:6s}")
    print("\n  the decision by hole: aimed at the pin minus aimed where the putt is likeliest")
    for key, label in (("tucked_sand", "pin cut toward the sand, |pin| >= 8 ft"),
                       ("away_sand", "pin cut away from the sand, |pin| >= 8 ft"),
                       ("friendly_sand", "sand beside a friendly pin, |pin| < 8 ft"),
                       ("none_tucked", "no sand, |pin| >= 8 ft"),
                       ("none_friendly", "no sand, |pin| < 8 ft")):
        band(hole_bag[key], "  " + label, "sand" if "sand" in key and key != "none_tucked"
             and key != "none_friendly" else "grass")
    print(f"\n  the same {n} courses, bunkers in against bunkers filled in: what the sand changes about that "
          f"decision")
    for key, label in (("tucked_sand", "pin cut toward the sand, |pin| >= 8 ft"),
                       ("away_sand", "pin cut away from the sand, |pin| >= 8 ft"),
                       ("friendly", "friendly pin, |pin| < 8 ft")):
        band(sand_bag[key], "  " + label)
    if bags == 1:
        print("\n  one bag: the error bars above are the spread across courses only, and that is what pass 3-7 "
              "reported.\n  --bags 8 redraws the athlete itself, which is the larger uncertainty of the two.")
    return 0


FIELD = [
    # name, policy, learns, prior on the bag, sigma taught (None: learned from its own misses)
    ("practiser", "spread", True, 1.00, None),
    ("flag-hunter", "flag", True, 1.00, None),
    ("cautious", "centre", True, 1.00, None),
    ("no practice", "spread", False, 1.00, None),
    ("bad start", "spread", True, 0.85, None),
    ("blind hands", "spread", True, 1.00, 1.5),
]


def field(args) -> int:
    """Six athletes, one course, one card. A field is not physics and needs nobody's permission.

    The same drawn course every competitor plays in the same round, with the same seed, so the weather and the
    bounce are common and the only differences are the things each of them does or believes: where it aims,
    whether it learns at all, what it starts out believing about its bag, and whether it is allowed to know how
    wide it hits. Everybody learns where they are allowed to — four rounds, in public, with the card read out.

    What this is not: other people. A field of my own athletes sharing one notebook's ancestry is a field of
    *strategies*, and the number on the card is still mine. Whether the commons ever puts six members' numbers
    on one board is a thing the members would have to do in their own windows; nothing here can do it for them
    and nothing here should pretend to.
    """
    green = Green(stimp=10.0, grade=1.2, downhill=135.0)
    rounds = max(1, args.rounds)   # eight is the shortest card on which luck stops deciding the order
    courses = [drawn_course(random.Random(5000 + k), args.pin_range, args.calm) for k in range(rounds)]
    print(f"{rounds} rounds of nine, pins ±{args.pin_range:.0f} ft"
          f"{', still air' if args.calm else ', wind drawn'}; every athlete plays the same course each round, "
          f"with the same seed\n")
    cards = []
    for name, policy, learns, prior, sigma in FIELD:
        ath = Athlete(prior=prior, sigma_taught=sigma)
        ath.policy = policy
        tots = [play_round(course, ath, PuttAthlete(), green, learn=learns, verbose=False,
                           rng=random.Random(DEFAULT_SEED + r))["to_par"] for r, course in enumerate(courses)]
        cards.append((name, policy, learns, tots, ath))
    par = sum(h.par for h in courses[0]) * rounds
    head = "  " + f"{'':14s}{'':9s}" + "".join(f"{'R' + str(i + 1):>6s}" for i in range(rounds))
    print(head + f"{'total':>8s}{'best':>7s}{'change':>9s}")
    for name, policy, learns, tots, ath in sorted(cards, key=lambda c: sum(c[3])):
        change = tots[-1] - tots[0]
        print(f"  {name:14s}{policy:9s}" + "".join(f"{t:+6d}" for t in tots)
              + f"{sum(tots):+8d}{min(tots):+7d}{change:+9d}")
    print(f"\n  par {par} over {rounds} rounds. change is last round minus first: negative is improvement.")
    print("  and what each of them ended up believing:")
    for name, policy, learns, tots, ath in sorted(cards, key=lambda c: sum(c[3])):
        print(f"    {name:14s} aim bias {ath.aim_bias:+5.2f}°  sigma {ath.sigma:4.2f}°  "
              f"wind {ath.wind_c:4.2f}  shots observed {ath.shots:4d}")
    return 0


# ---- the picture ------------------------------------------------------------------------------------
# A golf shot is the cheapest thing in this repository to film: one ball, one arc, six seconds, and no opponent.
# The film is not a claim and it rests on nothing — every number in this file was decided before it was drawn —
# so it lives in its own section with the scene it draws, and the page under `games/golf/replay3d.html` reads it
# with no library at all: a ball, an arc and a wall do not need a character pipeline.
# ---- the scatter, taught against learned ------------------------------------------------------------
# Pass 6 ended with a question: in wind every learner's sigma doubles, so a scatter-aware player aims by a
# number the wind inflated — is that an artefact of the gate that keeps a crosswind out of what teaches the
# hands, or a fact about a scatter-aware player? Answering it needed the game to measure two things it had
# never measured: what the athlete *believes* its scatter is, and what its scatter *is*. The second one only
# exists relative to the line the shot was aimed at, which is why the log now records it too.
TAUGHT_ARMS = (("gated, learned", None, True), ("ungated, learned", None, False),
               ("told 0.6°", 0.6, True), ("told 1.1°", 1.1, True),
               ("told 2.0°", 2.0, True), ("told 3.0°", 3.0, True))


def _sd(xs: list[float]) -> float:
    if len(xs) < 2:
        return float("nan")
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def costs_test(args) -> int:
    """What the short game costs, played out rather than assumed — the two numbers `target()` is made of.

    Until pass 10 `target()` did not use strokes at all: it scored
    `P(on the green) + 0.3 * P(inside 25 ft of the pin) - SAND_PEN * P(in the sand)`. Scoring a landing by what
    it costs needs the cost, and the cost is a fact about this game's putter and its clubs, so it is measured
    the same way everything else here is: put a ball somewhere and play it out.
    """
    green = Green(stimp=10.0, grade=1.2, downhill=135.0)
    h = Hole(400, 4, "C", pin=13.0, sand=+1)
    ath = Athlete()
    ath.policy = "spread"
    for k in range(3):
        play_round(drawn_course(random.Random(9000 + k), 14.0, True), ath, PuttAthlete(), green,
                   learn=True, verbose=False, rng=random.Random(DEFAULT_SEED + k))
    print(f"a settled athlete (sigma {ath.sigma:.2f}°), pin {h.pin:+.0f}, sand to the right; green 20 ft half-"
          f"width, 28 ft half-depth\n")
    print(f"  {'distance':>9s}{'green':>16s}{'rough':>16s}{'sand':>16s}")
    rows = {"green": [], "rough": [], "sand": []}
    for d in (2.5, 4, 6, 9, 12, 16, 20, 24, 28, 33, 40, 50, 60):
        line = f"  {d:7.1f}ft"
        for kind in ("green", "rough", "sand"):
            vals = []
            for b in range(16):
                a = math.radians(360.0 * b / 16)
                pt = (h.centre[0] + math.sin(a) * d, h.centre[1] + math.cos(a) * d)
                got = "sand" if in_sand(pt, h) else ("green" if on_green(pt, h) else "rough")
                if got != kind:
                    continue
                vals.append(play_hole(h, copy_of(ath), PuttAthlete(), green, learn=False, verbose=False,
                                      start=pt, rng=random.Random(DEFAULT_SEED))["strokes"])
            rows[kind] += vals
            line += f"{_mean(vals):10.2f}({len(vals):2d})" if vals else f"{'—':>13s}    "
        print(line)
    print(f"\n  on the green, every distance from 2.5 ft to 28 ft costs {COST_ON_GREEN:.2f}: the putter is")
    print(f"  deterministic — it bisects its gain and its line to zero error and the roll carries no scatter —")
    print(f"  so it holes out in two from anywhere and the green has no gradient in distance at all.")
    print(f"  off the green, mean {_mean(rows['rough']):.2f} against {COST_OFF_GREEN:.2f} told, and it is 2 or 3 by")
    print(f"  bearing: a chip that goes in, or one that does not. In the sand, mean {_mean(rows['sand']):.2f} against")
    print(f"  {COST_ON_GREEN + ath.sand_pen:.2f} told (the green's two plus the athlete's {ath.sand_pen:.2f} price).")
    return 0


def sigma_test(args) -> int:
    """Does a *belief about its own hands* reach the player's card, now that the floor is out of the way?

    Two quantities, and the whole of the first experiment was that they had never been measured against each
    other: the scatter the athlete *believes* (which is what its target decision is made of) and the scatter
    its shots *have*. The eighth pass measured both and found that the belief never reached the card — the
    target decision floors the scatter at 2 ft, and 2 ft is wider than a 1° scatter inside 76 ft, so six
    values from 0.6° to 3.0° played the same card to within fifteen strokes in nine hundred.

    The floor is 0.5 ft now. **And the bar in the first version of this report was wrong**, which is the
    other half of the pass: it paired the arms by course and divided by the spread of course-mean
    differences, but the shot streams diverge at the first decision the arms disagree about, so the noise
    that pairing was supposed to cancel survives — and running the same six arms on four independent streams
    moved every one of them by half a stroke, which is most of the effect being claimed. `--streams` repeats
    the whole experiment on independent shot streams and reports the across-stream spread as the bar. The
    paired-by-course bar is gone: it was a bar on the draw, not on the noise.
    """
    green = Green(stimp=10.0, grade=1.2, downhill=135.0)
    train, test = max(2, args.draws // 3), max(2, args.draws // 3)
    courses = [drawn_course(random.Random(7000 + k), args.pin_range) for k in range(train + test)]
    print(f"{train} courses to learn on, {test} to play, pins ±{args.pin_range:.0f} ft, wind drawn, "
          f"{args.rounds} times through the test set, {args.streams} independent streams\n")
    per_arm: dict[str, list[float]] = {}
    beliefs, last_logs = {}, {}
    for stream in range(args.streams):
        base = DEFAULT_SEED + 1000 * stream
        for name, taught, gated in TAUGHT_ARMS:
            ath = Athlete(sigma_taught=taught, gate=gated)
            ath.policy = "spread"
            for k, course in enumerate(courses[:train]):
                play_round(course, ath, PuttAthlete(), green, learn=True, verbose=False,
                           rng=random.Random(base + k))
            tot, logs = 0, []
            for _ in range(args.rounds):
                for k, course in enumerate(courses[train:]):
                    r = play_round(course, ath, PuttAthlete(), green, learn=False, verbose=False,
                                   rng=random.Random(base + 500 + k))
                    tot += r["strokes"]
                    logs += [e for h in r["rows"] for e in h["log"]]
            per_arm.setdefault(name, []).append(tot / (args.rounds * test))
            beliefs[name], last_logs[name] = ath.sigma, logs
    print(f"  {'':18s}{'strokes/round':>15s}{'± across':>10s}{'vs gated':>17s}{'sigma believed':>16s}")
    ref = per_arm[TAUGHT_ARMS[0][0]]
    rows = []
    for name, _, _ in TAUGHT_ARMS:
        v = per_arm[name]
        m = _mean(v)
        se = _sd(v) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
        d = _mean([x - y for x, y in zip(v, ref)])
        se_d = _sd([x - y for x, y in zip(v, ref)]) / math.sqrt(len(v)) if len(v) > 1 else float("nan")
        rows.append((name, m, se, d, se_d))
        print(f"  {name:18s}{m:15.2f}{1.96 * se:10.2f}   {d:+6.2f} ± {1.96 * se_d:4.2f}{beliefs[name]:16.2f}")
    lo = min(rows, key=lambda r: r[1])
    hi = max(rows, key=lambda r: r[1])
    dd = [x - y for x, y in zip(per_arm[hi[0]], per_arm[lo[0]])]
    se_dd = _sd(dd) / math.sqrt(len(dd)) if len(dd) > 1 else float("nan")
    print(f"\n  the table's own spread: {lo[0]} {lo[1]:.2f} against {hi[0]} {hi[1]:.2f}, "
          f"{hi[1] - lo[1]:.2f} ± {1.96 * se_dd:.2f} strokes a round, paired by stream")
    print(f"  the bar is the across-stream spread of the mean over {args.streams} streams "
          f"({test} courses × {args.rounds} rounds each); a difference smaller than twice it is not a "
          f"difference. And the streams are the honest unit here, not the courses: the arms share a course "
          f"and stop sharing a shot stream the moment they aim at different feet.")
    print("\n  and what the shots actually did, on the last stream, with learning off:")
    for name, _, _ in TAUGHT_ARMS:
        logs = last_logs[name]
        angles = [e["angle_aim"] for e in logs if e["kind"] == "shot" and e.get("angle_aim") is not None]
        quiet = [e["angle_aim"] for e in logs if e["kind"] == "shot" and e.get("angle_aim") is not None
                 and abs(e["cross"]) <= CROSS_QUIET]
        print(f"    {name:18s} every shot {_sd(angles):5.2f}° (n={len(angles):3d})   "
              f"still-air shots {_sd(quiet):5.2f}° (n={len(quiet):3d})   believes {beliefs[name]:4.2f}°")
    print("\n  a belief matching the shots is neither bold nor cautious; a belief half the scatter aims at a "
          "pin it cannot hit. With the floor in, none of this reached a card at all.")
    return 0


def _shot(scene_ath: Athlete, hole: Hole, start: tuple[float, float], club: Club, gear: float,
          bearing: float, label: str, wind: tuple[float, float] = (0.0, 0.0),
          lens: str | None = None) -> dict:
    """One drawn shot: the film, and the sentence that goes under it."""
    lip_ft = lip_distance(start, bearing, hole)
    res = shot(start, club, gear, bearing, lie=lie_at(start, hole), wind=wind_vector(wind),
               lip=lip_ft, trace=0.02)
    if res.get("lip"):
        text = "into the face: the stroke is spent and the ball is where it was"
    elif on_green(res["rest"], hole):
        text = f"on the green, {math.hypot(hole.flag[0] - res['rest'][0], hole.flag[1] - res['rest'][1]):.0f} ft from the flag"
    else:
        text = (f"{res['total'] / FT_PER_YD:.0f} yd, "
                f"{math.hypot(hole.flag[0] - res['rest'][0], hole.flag[1] - res['rest'][1]) / FT_PER_YD:.0f} yd from the flag")
    return dict(label=label, club=club.name, gear=gear, start=list(start), path=res.get("path"),
                stop_at=res.get("stop_at"), rest=list(res["rest"]), lip=bool(res.get("lip")), result=text,
                hit=res.get("hang", 0.0),
                face=lip_ft,          # how far to the face, or None
                lens=lens)            # the shot list's note about which camera it wants, or None for the renderer's


def _hole_json(hole: Hole) -> dict:
    return dict(yards=hole.yards, par=hole.par, label=hole.label, pin=hole.pin, sand=hole.sand,
                centre=list(hole.centre), flag=list(hole.flag), green_a=GREEN_A, green_b=GREEN_B,
                bunker_w=BUNKER_W if hole.sand else 0.0, lip_h=LIP_H if hole.sand else 0.0)


def render(args) -> int:
    """Write a scene and the page that plays it, into `games/golf/renders/`."""
    out_dir = Path(__file__).resolve().parent.parent / "games" / "golf" / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)
    green = Green(stimp=10.0, grade=1.2, downhill=135.0)
    which = args.render
    if which == "lip":
        hole = Hole(400, 4, "the face", pin=0.0, sand=+1)
        y = hole.yards * FT_PER_YD
        near, far = (GREEN_A + 1.0, y), (GREEN_A + 7.0, y)
        to_flag = lambda p: math.degrees(math.atan2(-p[0], 0.0))          # noqa: E731
        out_way = lambda p: math.degrees(math.atan2(p[0], 0.0))           # noqa: E731
        a = copy_of(Athlete())                         # a beginner is enough: the picture is of the course
        a.policy = "spread"
        scene = dict(
            title="the face, from one foot and from six",
            note="Three balls, one bunker. The face is 18 in of sand along the green's edge and nothing along "
                 "the other three sides: a ball can always go out the back, never out the front. The second is "
                 "the first ball played out sideways, which is what a player does; the third is the same club "
                 "from six feet further back, where the swing has room to be a swing and the face is 2.4 ft "
                 "under the ball instead of on top of it.",
            fov=38.0,
            view=dict(pos=[86.0, y - 58.0, 30.0], target=[17.0, y + 3.0, 1.0],
                      label="behind the bunker: the face on the right, the flag beyond it"),
            feet=_hole_json(hole),
            shots=[
                _shot(a, hole, near, CLUB_BY_NAME["sand wedge"], 0.25, to_flag(near),
                      "one foot from the face, at the flag — nothing in the bag is high enough"),
                _shot(a, hole, near, CLUB_BY_NAME["sand wedge"], 0.25, out_way(near),
                      "the same ball, played out over the low edge: what the athlete actually does",
                      lens="wide"),
                _shot(a, hole, far, CLUB_BY_NAME["sand wedge"], 0.35, to_flag(far),
                      "six feet back, a little more on it: 2.4 ft high at the face for an 18 in face"),
            ])
        name = "the-face"
    else:
        n = int(which)
        hole = COURSE[n - 1] if 1 <= n <= len(COURSE) else HELD_OUT[max(0, n - 10)]
        a = Athlete()
        a.policy = "spread"
        pu = PuttAthlete()
        for k in range(3):
            play_round([h for h in COURSE if h is not hole] or COURSE, a, pu, green, learn=True, verbose=False,
                       rng=random.Random(DEFAULT_SEED + k))
        y = hole.yards * FT_PER_YD
        r = play_hole(hole, a, pu, green, learn=False, verbose=False, rng=random.Random(DEFAULT_SEED),
                      trace=0.02)
        shots = []
        for e in r["log"]:
            if e["kind"] != "shot":
                continue
            shots.append(dict(label=f"{e['club']} at {e['gear']:.0%}, aim {e['offset']:+.0f} ft",
                              club=e["club"], gear=e["gear"], start=[round(c, 2) for c in e["start"]],
                              path=e.get("path"), stop_at=e.get("stop_at"), rest=None, lens="wide",
                              lip=bool(e.get("hit_lip")),
                              result=f"{e['total']:.0f} yd, {abs(e['along']):.0f} yd "
                                              f"{'short' if e['along'] < 0 else 'past'}, "
                                              f"{abs(e['lateral']):.0f} yd {'right' if e['lateral'] > 0 else 'left'}"))
        scene = dict(title=f"hole {hole.label}: {hole.yards:.0f} yd, par {hole.par}",
                     note=f"the athlete plays it in {r['strokes']} strokes, {r['putts']} of them putts. "
                          f"Bunker on the {'right' if hole.sand > 0 else ('left' if hole.sand < 0 else 'none')}.",
                     fov=44.0, feet=_hole_json(hole), shots=shots,
                     view=dict(pos=[0.12 * y, -0.10 * y, 0.22 * y], target=[hole.centre[0], 0.78 * y, 0.0],
                               label=f"down the hole from behind the tee: {hole.yards:.0f} yd, par {hole.par}"))
        name = f"hole-{hole.label}"
    (out_dir / f"{name}.json").write_text(json.dumps(scene, indent=1))
    template = (Path(__file__).resolve().parent.parent / "games" / "golf" / "replay3d.html").read_text()
    page = template.replace("__SCENE__", json.dumps(scene))
    out = out_dir / f"{name}.html"
    out.write_text(page)
    print(f"{name}: {len(scene['shots'])} shots, "
          f"{sum(len(s['path'] or ()) for s in scene['shots'])} path points\n  {out}")
    return 0


# ---- main -------------------------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--learn", type=int, default=1, help="0 for the control: the same athlete, frozen")
    ap.add_argument("--policy", default="spread", choices=["flag", "centre", "spread"],
                    help="where it aims: at the pin, at the middle of the green, or where the putt is likeliest")
    ap.add_argument("--calm", action="store_true", help="the same course on a still day")
    ap.add_argument("--bags", type=int, default=1,
                    help="how many athletes to train on different practice sets; the error bar becomes the "
                         "spread across bags (the bag is a draw like the weather)")
    ap.add_argument("--draws", type=int, default=0,
                    help="evaluate the policies over N random pin-and-wind pairings instead of the fixed nine")
    ap.add_argument("--pin-range", type=float, default=14.0,
                    help="how far from the green's centre a drawn pin may be, in feet")
    ap.add_argument("--compare", action="store_true",
                    help="train one athlete, then play the same rounds under all three target policies")
    ap.add_argument("--rounds", type=int, default=4)
    ap.add_argument("--streams", type=int, default=4,
                    help="independent shot streams for --sigma; the bar is their spread")
    ap.add_argument("--costs", action="store_true",
                    help="what the short game costs from each distance and lie: the numbers `target()` is made of")
    ap.add_argument("--sigma", action="store_true",
                    help="the scatter it believes against the scatter its shots have, in wind")
    ap.add_argument("--field", action="store_true",
                    help="six scripted athletes on one card: same course, same weather, different strategies")
    ap.add_argument("--render", metavar="SCENE", default=None,
                    help="write a film: 'lip' for the bunker face, or a hole number, e.g. --render 7")
    ap.add_argument("--floor", type=float, default=FLOOR_FT,
                    metavar="FT", help="override the floor `target()` puts under the scatter, to re-measure it")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    globals()["FLOOR_FT"] = args.floor
    if args.selftest:
        return selftest()
    if args.compare:
        return compare(args)
    if args.costs:
        return costs_test(args)
    if args.sigma:
        return sigma_test(args)
    if args.draws:
        return draws(args)
    if args.field:
        return field(args)
    if args.render:
        return render(args)

    green = Green(stimp=10.0, grade=1.2, downhill=135.0)
    ath, putter = Athlete(), PuttAthlete()
    ath.policy = args.policy
    course = [Hole(*c) for c in CALM] if args.calm else COURSE
    print(__doc__.splitlines()[2])
    print(f"\nBAG (carry + run at a full swing, fairway)")
    for c in CLUBS:
        r = shot((0.0, 0.0), c, 1.0, 0.0)
        print(f"  {c.name:<11} {r['carry'] / 3:5.0f} + {r['roll'] / 3:4.0f} = {r['total'] / 3:5.0f} yd"
              f"   {c.speed_mph} mph, {c.launch:.1f}°, {c.spin:.0f} rpm, hang {r['hang']:.1f}s")

    totals = []
    for i in range(1, args.rounds + 1):
        print(f"\nROUND {i}" + ("" if args.learn else "  (CONTROL: no learning)"))
        r = play_round(course, ath, putter, green, learn=bool(args.learn), tag=f"R{i}·")
        totals.append(r["to_par"])
    print(f"\nHELD-OUT: six holes never played")
    held = play_round([Hole(*h) for h in CALM] if False else HELD_OUT, ath, putter, green,
                      learn=bool(args.learn), tag="H·")
    print(f"\n  to par: {totals}   held-out {held['to_par']:+d}   policy {ath.policy}"
          + ("   calm" if args.calm else ""))
    print("  notebook against true (yards; full / 80% / 60% / chip, and shots at each):")
    for c in CLUBS:
        gs = (1.0, 0.8, 0.6, 0.35)
        t = " ".join(f"{shot((0, 0), c, g, 0.0)['total'] / 3:5.0f}" for g in gs)
        l = " ".join(f"{ath.table[c.name][g]:5.0f}" for g in gs)
        n = " ".join(f"{ath.n[c.name][g]:2d}" for g in gs)
        print(f"    {c.name:<11} {l}   true {t}   n {n}")
    print(f"  aim bias {ath.aim_bias:+.2f}°  (its hands are {ath.face:+.2f}°)   shots observed {ath.shots}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
