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
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tennis import flight  # noqa: E402  the one integrator, not a second copy of the loop
from putt import (  # noqa: E402  the short game is already a game
    STIMPMETER_SPEED, Athlete as PuttAthlete, Green, Hole as PuttHole, attempt as putt_attempt,
)

G = 32.17                 # ft/s²
MPH = 1.46667             # mph to ft/s
FT_PER_YD = 3.0
RHO = 0.002377            # slugs/ft³, sea level

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
ROUGH_SPEED = 0.88

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


# ---- one shot ---------------------------------------------------------------------------------------
def shot(start: tuple[float, float], club: Club, effort: float, aim: float,
         lie: str = "fairway", wind: tuple[float, float] = (0.0, 0.0),
         surface: dict | None = None) -> dict:
    """Strike, fly, bounce, run out. Every length is in feet, every angle in degrees clockwise from north.

    `effort` is the fraction of the club's nominal ball speed, which is the one thing an athlete controls
    that a launch monitor cannot argue with. `aim` is the bearing the ball leaves on. The rest point is
    where a spectator would walk to.
    """
    surf = surface or {"fairway": {"e": 0.4, "f": 1.0}, "rough": {"e": 0.3, "f": 1.0}}
    speed = club.speed_mph * MPH * effort * (ROUGH_SPEED if lie == "rough" else 1.0)
    cl, drag = aero(club, speed)
    a = math.radians(aim)
    v0 = (speed * math.cos(math.radians(club.launch)) * math.sin(a),
          speed * math.cos(math.radians(club.launch)) * math.cos(a),
          speed * math.sin(math.radians(club.launch)))
    out = flight((start[0], start[1], 0.0), v0, wind, lie, net_check=False,
                 cl=-cl, drag=drag, lift=LIFT_BASE, surfaces=surf, t_max=20.0)
    land = out.get("land")
    if not land:                                    # cannot happen with these constants; if it does, say so
        return dict(land=start, rest=start, carry=0.0, roll=0.0, total=0.0, lost=True,
                    hang=out.get("time", 0.0), cl=cl, drag=drag, speed=speed)
    bx, by, _ = out["bounce"]["v"]
    vh = math.hypot(bx, by)
    ux, uy = (bx / vh, by / vh) if vh > 1e-9 else (math.sin(a), math.cos(a))
    stimp = STIMP_FAIRWAY if lie != "rough" else STIMP_ROUGH
    a_roll = STIMPMETER_SPEED ** 2 / (2.0 * stimp)
    roll = (ROLL_RETAIN * vh) ** 2 / (2.0 * a_roll)
    carry = math.hypot(land[0] - start[0], land[1] - start[1])
    rest = (land[0] + ux * roll, land[1] + uy * roll)
    return dict(land=land, rest=rest, carry=carry, roll=roll, total=carry + roll, lost=False,
                hang=out.get("time", 0.0), cl=cl, drag=drag, speed=speed,
                descent=math.degrees(math.atan2(-out["bounce"]["v"][2], vh)))


# ---- the course -------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Hole:
    yards: float
    par: int
    label: str = ""

    @property
    def flag(self) -> tuple[float, float]:
        return 0.0, self.yards * FT_PER_YD


COURSE = [Hole(410, 4, "1"), Hole(165, 3, "2"), Hole(520, 5, "3"), Hole(300, 4, "4"),
          Hole(145, 3, "5"), Hole(385, 4, "6"), Hole(95, 3, "7"), Hole(450, 4, "8"),
          Hole(500, 5, "9")]
HELD_OUT = [Hole(130, 3, "H1"), Hole(375, 4, "H2"), Hole(480, 5, "H3"),
            Hole(190, 3, "H4"), Hole(340, 4, "H5"), Hole(90, 3, "H6")]

FAIRWAY_HALF = 20.0 * FT_PER_YD    # yd either side of the centre line before the lie is rough
ROUGH_EDGE = 35.0 * FT_PER_YD      # beyond this the ball is in the trees: a stroke and a drop
GREEN_R = 30.0                     # ft from the flag: inside it, the putter; outside, a club. A 60 ft
#                                    green is a real green, and the number is load-bearing: at 90 ft the
#                                    athlete never misses one, and a game whose green cannot be missed
#                                    scores par with a bag it has never checked.
STROKE_CAP = 12


def lie_at(point: tuple[float, float]) -> str:
    off = abs(point[0])
    if off <= FAIRWAY_HALF:
        return "fairway"
    if off <= ROUGH_EDGE:
        return "rough"
    return "trees"


# ---- the athlete ------------------------------------------------------------------------------------
GEARS = (1.0, 0.8, 0.6, 0.45, 0.35)     # what the notebook has columns for: the full swing, something off
#                                        it, a half, a soft half and the chip. Five, not a continuous dial,
#                                        because a player's repeatable shots are the named ones — and because
#                                        an athlete that can hit any effort exactly is an athlete that can
#                                        always reach the flag, whose distances then never matter.

# What a knocked-down swing costs in the choosing: this many yards of accuracy is worth surrendering before
# the athlete will take 25% off a swing. It is a rule of the athlete's, not a fact about golf.
FULL_SWING_PREFERENCE = 1.5


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

    def __init__(self) -> None:
        self.table = {c.name: {g: bag()[c.name] * INHERITED[c.name] * g for g in GEARS} for c in CLUBS}
        self.n = {c.name: {g: 0 for g in GEARS} for c in CLUBS}
        self.aim_bias = 0.0
        self.face = 2.2                                    # its own hands, which it does not know about:
        #                                                    the playing code adds this, the learning code
        #                                                    never reads it, and `aim_bias` is what it
        #                                                    estimates from the side of its misses
        self.misses: list[float] = []                      # the part of each miss that was not the aim
        self.shots = 0

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

    def observe_side(self, lateral_yd: float, distance_yd: float, aim_used: float) -> None:
        """The hands, from the side of the miss. What it learns is *its own* face angle: the miss angle
        less the aim it chose. Then it aims that much the other way. Two numbers, not one, because a
        player who only learned "I finish right" could not tell a slice from a mis-aimed club."""
        if distance_yd < 20.0:
            return
        self.misses.append(math.degrees(math.atan2(lateral_yd, distance_yd)) - aim_used)
        self.aim_bias = -sum(self.misses) / len(self.misses)


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
              learn: bool = True, verbose: bool = True, wind: tuple[float, float] = (0.0, 0.0),
              tag: str = "", rng: random.Random | None = None) -> dict:
    rng = rng or random.Random(DEFAULT_SEED)
    flag = hole.flag
    ball = (0.0, 0.0)
    strokes, log = 0, []
    penalties = 0
    while True:
        dist_ft = math.hypot(flag[0] - ball[0], flag[1] - ball[1])
        if dist_ft <= GREEN_R or strokes >= STROKE_CAP:
            break
        lie = "fairway" if ball == (0.0, 0.0) else lie_at(ball)
        if lie == "trees":
            strokes += 1
            penalties += 1
            ball = (math.copysign(ROUGH_EDGE, ball[0]), ball[1])
            log.append(dict(kind="penalty", text="in the trees: one stroke, dropped at the edge of the rough"))
            lie = "rough"
            continue
        club, gear = ath.choose(dist_ft / FT_PER_YD)
        predicted = ath.predict(club.name, gear)
        aim_used = ath.aim_bias
        aim = bearing_to(ball, flag) + aim_used + ath.face + rng.gauss(0.0, FACE_SD)
        effort = gear * (1.0 + rng.gauss(0.0, SPEED_SD))
        res = shot(ball, club, effort, aim, lie=lie, wind=wind)
        rest = res["rest"]
        rest = (max(-ROUGH_EDGE * 1.4, min(ROUGH_EDGE * 1.4, rest[0])), rest[1])  # the course ends somewhere
        along, lateral = report_shot(ball, rest, flag)
        strokes += 1
        measured = yards_between(ball, rest)
        if learn and lie == "fairway":
            ath.observe(club.name, gear, measured)
            ath.observe_side(lateral, max(1.0, dist_ft / FT_PER_YD), aim_used)
        log.append(dict(kind="shot", club=club.name, gear=gear, effort=effort,
                        carried=res["carry"] / FT_PER_YD,
                        ran=res["roll"] / FT_PER_YD, total=measured, along=along, lateral=lateral,
                        # The number that shows whether the notebook is being learned: what it said the
                        # shot would do against what it did. Not the miss to the flag — that is mostly the
                        # coarseness of the gear ladder, and it says nothing about the player's knowledge.
                        predicted=predicted, notebook_err=abs(measured - predicted) / max(1.0, predicted),
                        angle=math.degrees(math.atan2(lateral, max(1.0, dist_ft / FT_PER_YD))),
                        lie=lie))
        if verbose:
            side = "right" if lateral > 0 else "left"
            depth = "short" if along < 0 else "long"
            print(f"  {tag}{hole.label:>3} {hole.yards:4.0f} yd par {hole.par}   "
                  f"{club.name:<11} {effort * 100:3.0f}%  {measured:5.1f} yd   "
                  f"{abs(along):5.1f} {depth:<5} {abs(lateral):4.1f} {side:<5} {lie}")
        ball = rest
    # ---- the green: games/putt, not a second model of it
    putts = 0
    if math.hypot(flag[0] - ball[0], flag[1] - ball[1]) <= 2.125 / 12.0:
        ball = flag          # it is in the cup; putt.py never has to ask, because a putt never starts there
    while putts < 4 and strokes < STROKE_CAP:
        d_ft = math.hypot(flag[0] - ball[0], flag[1] - ball[1])
        if d_ft > GREEN_R and putts == 0:
            break
        bearing = bearing_to(ball, flag) if d_ft > 0 else 0.0
        r = putt_attempt(putter, PuttHole(d_ft, bearing), green, learn=learn)
        putts += 1
        strokes += 1
        if r["holed"]:
            if verbose:
                print(f"  {tag}{hole.label:>3} {'':>4} {'':>12} putt        {d_ft:5.1f} ft  "
                      f"{r['text']}  ({putts} putt{'s' if putts > 1 else ''})")
            break
        # putt's report is in the hole's own frame: past is + along the line it was hit on, right is +.
        ux, uy = flag[0] - ball[0], flag[1] - ball[1]
        d = math.hypot(ux, uy) or 1.0
        ux, uy = ux / d, uy / d
        ball = (flag[0] + r["along"] * ux + r["lateral"] * uy,
                flag[1] + r["along"] * uy - r["lateral"] * ux)
        if verbose:
            print(f"  {tag}{hole.label:>3} {'':>4} {'':>12} putt        {d_ft:5.1f} ft  {r['text']}")
    if putts == 0 and verbose:
        print(f"  {tag}{hole.label:>3} {'':>4} {'':>12} picked up")
    return dict(hole=hole, strokes=strokes, putts=putts, penalties=penalties, log=log)


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

    print(f"\n  {len(fails)} of {n} checks failed" if fails else f"\n  all {n} checks pass")
    return 1 if fails else 0


# ---- main -------------------------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--learn", type=int, default=1, help="0 for the control: the same athlete, frozen")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    green = Green(stimp=10.0, grade=1.2, downhill=135.0)
    ath, putter = Athlete(), PuttAthlete()
    print(__doc__.splitlines()[2])
    print(f"\nBAG (carry + run at a full swing, fairway)")
    for c in CLUBS:
        r = shot((0.0, 0.0), c, 1.0, 0.0)
        print(f"  {c.name:<11} {r['carry'] / 3:5.0f} + {r['roll'] / 3:4.0f} = {r['total'] / 3:5.0f} yd"
              f"   {c.speed_mph} mph, {c.launch:.1f}°, {c.spin:.0f} rpm, hang {r['hang']:.1f}s")

    totals = []
    for i in range(1, args.rounds + 1):
        print(f"\nROUND {i}" + ("" if args.learn else "  (CONTROL: no learning)"))
        r = play_round(COURSE, ath, putter, green, learn=bool(args.learn), tag=f"R{i}·")
        totals.append(r["to_par"])
    print(f"\nHELD-OUT: six holes never played")
    held = play_round(HELD_OUT, ath, putter, green, learn=bool(args.learn), tag="H·")
    print(f"\n  to par: {totals}   held-out {held['to_par']:+d}")
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
