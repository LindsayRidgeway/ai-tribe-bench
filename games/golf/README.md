# golf — a bag, a course, and the number that says which club was wrong

Built 2026-11-19 by Dmitri, from the founder's suggestion of the same day. Second pass the same night:
wind, and the decision about where to aim. Third pass: the pins drawn instead of typed. **Fourth pass: a
bunker beside the green, put there to test the third pass and mostly to refute it.** The tool is
`lab/golf.py`; the runs are `records/golf-2026-11-19.txt`; the checks are `python3 lab/golf.py --selftest`
(22 of them).

    python3 lab/golf.py                    # six rounds of nine, then six holes never played
    python3 lab/golf.py --calm             # the same pins on a still day
    python3 lab/golf.py --learn 0          # the control: same athlete, same seed, never updated
    python3 lab/golf.py --policy flag      # aim at the pin / centre: the middle / spread: where the putt is likeliest
    python3 lab/golf.py --compare          # train one athlete, then play all three policies against each other
    python3 lab/golf.py --draws 60         # the same, over 60 courses whose pins and winds are drawn, not chosen
    python3 lab/golf.py --selftest         # the numbers below, checked

## The question, and why it is not "putt, from further away"

`games/putt/` closed one loop: two levers, two unknown numbers, bisection on the printed miss. Golf that
copied that would teach nothing, because a green with a longer putter on it is the same problem.

What is different about golf is that the athlete does not know what its tools do:

    on the green   one tool, two numbers, learned by bisection;
    on the course  six tools at six gears each, and it has to find out what all of them do, while the
                   shot it hits now decides the problem it faces next.

So the levers are **which club** and **which gear** (full, 80%, 60%, 45%, the chip, the little chip), its
number back is the one a golfer reads off the fairway — how far short or long, how far left or right, in
yards — and the thing it builds out of those numbers is a notebook: thirty-six entries, every one wrong to
start with. What it must also learn is what the *conditions* cost (a headwind, the rough) and how much it
misses by, because that last number is what a target decision is made of.

The queue in `games/ATHLETES.md` had this as *"golfer's drive — face, launch → carry and how far off the
fairway centre"*. One shot cannot teach a course: there is no second shot that is worse because of the
first. The bag, the course and the pin are the addition, and they are the whole of the game.

## The course

Nine holes, one straight corridor, par 35: 410, 165, 520, 300, 145, 385, 95, 450, 500 yards. Fairway 40 yd
wide; rough to 35 yd off the centre line, where a ball leaves the club at 88% of its fairway speed and runs
out less, 20% of the shot in all — **told to the athlete, not learned** (see the note under the athlete);
beyond 35 yd, trees, one stroke and a drop at the edge.

The green is an **ellipse 40 ft wide and 56 ft deep round the hole's centre**, and the flag is cut anywhere
from 14 ft left of that centre to 13 ft right. That shape is the second decision in the game: on a circle
round the flag, the flag is the safest place on the green and there is nothing to decide.

Six of the nine holes have a **bunker on one flank**: 14 ft of sand outside the green's edge, on the right of
3, 4 and 8 and on the left of 2, 7 and 9. Three holes have none, so a sandless green is in the sample too. The
bunker does not move with the pin — that is the point of putting it there: a pin cut toward the sand and a pin
cut away from it are different problems with the same distance from the middle. The ball leaves sand at 70% of
its grass speed, bounces dead, and cannot be putted from; the *lip* is not modelled, and that omission turns
out to be the whole of the result below.

Every hole has a **wind**, blowing at 9 to 18 mph from a stated bearing, and it is told to the athlete
before every shot — all nine are in the `COURSE` table with their pins. `--calm` is the same pins with no
air.

Inside 30 ft of the flag, and only there, the putter comes out, and it is `games/putt`'s putter and
`games/putt`'s friction law, imported, not re-modelled.

## The athlete

Scripted, no model calls, and it is told everything a player can see: the distance to the flag, the lie,
the pin's position, the green's shape and the wind. It carries:

    table[club][gear]   what this club has done for me at this effort, in yards

Every entry starts at what a beginner believes — the bag this model gives, scaled per club by an invented
`INHERITED` (too much faith in the 7-iron, 1.10; none in the sand wedge, 0.88) and scaled *linearly* in
gear (hit it twice as hard, go twice as far). Every fairway shot replaces the entry it was hit with by the
running mean of what that club and that gear actually did, **divided back to what it would have done in
still air** — a notebook is a calm-day notebook, or the student learns that its driver goes 317 yards.

Then three numbers that are not tools:

- **its hands** — the ball leaves its clubface 2.2° right of where it aims, learned from the side of its
  misses;
- **its scatter** — how wide those misses are about that mean, which is the input to the target decision;
- **the wind** — one coefficient fitted through the origin on the shots it has taken, against the headwind
  as a fraction of a ball speed: `what it did / what the notebook said ≈ 1 − c·h`.

**The rough is not learned, and the reason is in the code.** Fitting it alongside the wind gave 0.46 for a
true 0.20, because a rough lie is where a mis-clubbed ball ends up and the coefficient swallowed the
notebook's own error. Guarding the fit to settled entries learned nothing instead, since no rough shot is
ever hit with a club that has been hit four times. The honest conclusion is that the rough is not
something a player discovers by experiment; it is the first thing anybody tells you. So it is a constant,
and the record says why rather than hiding one.

## The physics: what is calibrated, what is measured, what is invented

The ball is `lab/tennis.py`'s integrator with golf's constants passed in; the roll is `lab/putt.py`'s
friction law, a = STIMPMETER²/(2·stimp). One integrator, one roll law, no second copy of either.

| check (selftest) | model says |
|---|---|
| vacuum range, 45° at 100 ft/s | **310.92 ft** against v²/g = 310.85 |
| drag, same launch | **231.6 ft** with drag against 310.9 without |
| a headwind | 7-iron **182.6 yd** calm, **160.3 yd** into 10% of a ball speed |
| a crosswind | **31.8° per unit** of crosswind fraction, linear to 0.1° over ±15% |
| the bag, full swing, carry + run | driver **295**, 3 wood 274, 5 iron 210, 7 iron 183, 9 iron 154, sand wedge 122 |
| calibration residual | worst club **8.5 yd** off its prior carry |
| roll law | 6.0 ft/s rolls **10.00 ft** on a 10 stimp, exactly putt's |
| sand | a wedge keeps **0.54** of its distance and **0.56** of its run-out, against 0.55 and 17.3 → 9.8 yd |

**Nothing here was measured on a launch monitor.** The six clubs' ball speeds, launch angles and spin rates
are priors from published tour averages; the four drag/lift constants (Cl = min(0.131, 1.68·S), Cd =
min(0.284, 0.188 + 0.469·S), where S = ωr/v) were fitted until those six priors came out. The residual is
printed so the size of the assumption is visible. A model calibrated to a table is only as good as the
table, and it is not evidence about a real golf ball. No finding below rests on the model being right about
physics; they rest on it being consistent, which the checks test directly.

Strike dispersion is a prior too: 1.1° of clubface error and 1.5% of ball speed, drawn from a fixed seed
(20261119). **Every round replays the same sequence**, so two rounds differ only in what the athlete knows.

## What six rounds printed — still air, and wind

Same pins, same seed, one athlete learning and one frozen.

| still air | 1 | 2 | 3 | 4 | 5 | 6 | held-out | notebook error |
|---|---|---|---|---|---|---|---|---|
| **learning** | +16 | +13 | +10 | +3 | +5 | +8 | +3 | 8.0 → 2.3, 7.6 by the sixth |
| **control** | +13 | +13 | +13 | +13 | +13 | +13 | +10 | 35.9% flat |

| windy | 1 | 2 | 3 | 4 | 5 | 6 | held-out | notebook error |
|---|---|---|---|---|---|---|---|---|
| **learning** | +22 | +17 | +12 | +10 | +6 | +5 | +9 | 21.3 → 11.4% |

*to par over nine holes (par 35); held-out is six holes never played (par 22). Notebook error is |what the
notebook said| against |what the shot did|, over every shot in the round.*

Putts, still air: 30, 25, 25, 22, 24, 25 for the learner, 18 every round for the control.

### Five findings

1. **A wrong notebook costs about five strokes a round, and only after it has been paid for.** The learner
   starts four strokes worse than a player who never practises (+16 against +13) and finishes five to eight
   better. It is the putts early on: thirty of them in the first round against eighteen. A wrong notebook
   does not miss the flag so much as miss it into places where the next shot is harder.
2. **The wind is worth five strokes a round and cannot be learned, only paid.** The same course, same pins,
   same seed: +22, +17, +12, +10, +6, +5 with the wind against +16, +13, +10, +3, +5, +8 in still air. The
   athlete learns the *along* part — its coefficient settles at 0.95 against the model's own 0.7 per unit of
   head fraction — and cannot learn the *across* part at all. A crosswind moves the ball 31.8° per unit of
   cross fraction, and there is no column in a notebook for that.
3. **Where you aim is worth nothing on a friendly pin day and two and a half strokes on a tucked one — and
   the course, not the player, decides which day it is.** One trained athlete, three policies, sixty courses
   per setting with the pins *drawn* rather than chosen, every policy playing the same course, learning off:

   | still air, 60 drawn courses | pin ±6 ft | pin ±14 ft | pin ±19 ft |
   |---|---|---|---|
   | aiming at the pin, minus aiming where the putt is likeliest | **−0.42 ± 0.22** | **+0.78 ± 0.29** | **+2.50 ± 0.58** |

   Negative means pin-hunting wins. On a nine with the flags near the middle it is right to shoot at them, by
   about four tenths of a stroke; somewhere around eight feet of pin offset the middle of the green becomes the
   better target, and on a tucked-pin day the decision is worth two and a half strokes a round. **The first
   version of this file reported three strokes off nine pins I had typed in myself, and they were tucked: their
   mean offset is 10 ft, which is what the ±19 draw looks like.** The three was the top of the range the
   randomised estimate allows, not a general rule, and the README said three before it had a right to.

4. **With the wind on, the same decision is worth nothing at all — and last night's twenty-stroke reversal was
   an artifact of my own pin table.** Drawn pins at ±19 with drawn wind give **−0.43 ± 0.56**: not a reversal,
   just no effect. The reason is mechanical and worth stating, because it is the most useful sentence in this
   file: *a crosswind adds an error the player cannot predict, and its size per hole is comparable to the pin's
   offset — so the correction it could make for the pin is lost inside the error it cannot make.* Against the
   fixed nine, the same comparison swung twenty strokes the other way (128 against 156); with pins and winds
   drawn independently, that swing is gone. Nine pins and nine winds are nine fixed pairs; I had chosen them,
   and an athlete that cannot correct a sidewind is lucky or unlucky by which way the air blows past which pin.

5. **The bunker did not do what I said it would do, and the reason is the thing I did not model.** Pass 3
   ended with a prediction, written down before the run: a miss with a *direction* would make the target
   decision two-dimensional. It did not. Same sixty courses, the same pins and winds, played twice — once as
   drawn, once with every bunker filled in — paired by hole:

   | still air, pin ±19 ft, bunkers in minus bunkers filled in | strokes |
   |---|---|
   | pin cut **toward** the sand, \|pin\| ≥ 8 ft | **−0.21 ± 0.14** |
   | pin cut **away** from it, \|pin\| ≥ 8 ft | −0.05 ± 0.05 |
   | friendly pin, \|pin\| < 8 ft | −0.01 ± 0.05 |

   Negative means the bunker made *pin-hunting better*. Two mechanisms, both measured: **the bunker is
   almost never reached** — 3 to 5 per cent of the approaches aimed into one finish in it, because reaching a
   flank bunker needs the depth right *and* the face wrong, and this athlete's depth error is tens of feet —
   and **a ball in it is not worth much**: 21 ft from the hole in sand takes 2.20 strokes against 2.00 from
   19 ft on the green. A bunker without a lip is a slow lie, not an obstacle. The athlete recovers with the
   same bag it uses everywhere, from a flat surface, aiming at the flag, and the shortest club in the bag gets
   out. So the hazard is nearly free, and a nearly free hazard fourteen feet from the pin cannot move where a
   player aims. **I estimated the hit rate at 39% from a normal CDF and got 3%** — I computed the face-angle
   factor and forgot that the depth has to be right too, which is the same error as pass 3 in a new dress:
   working the part of the sum that is easy and calling it the answer.

   One number in this finding is a warning about all the others. The athlete's price for sand was first
   written as **one full stroke**, invented. With that guess the decision at ±14 ft fell from +0.78 to −0.10 —
   a fabricated constant inside the player moved the headline by 0.9 strokes a round, at exactly the pitch
   the course was built to be measured at. Measured properly it is 0.30, and the check that now guards it is
   `a ball in the sand is worth what it is told it is worth`. **The aggregate the third pass published does
   move, once, and by half a stroke:** ±19 still air goes from +2.50 ± 0.58 to **+1.97 ± 0.55**, mostly
   because sand stops the overshoot that used to run through the back of the green. ±6 and ±14 are unchanged
   within their error bars (−0.38 ± 0.21 and +0.85 ± 0.29). And with the wind on, nothing: ±19 with drawn
   wind gives **−0.28 ± 0.63**, which is the fourth finding's null, still standing.

## What this does not model

- **no bunker lip, and no plugged lie or killed spin in sand** — a bunker is a slow lie here, which the fourth
  pass measured to be worth 0.2 strokes rather than a stroke; water, dogleg, tree line, green contour and
  green slope are absent for the same reason: each is a new law, and each was left out rather than invented
- a ball in sand must still be "carried" out by the same bag from a flat surface; no stance, no shallow
  explosion, no downhill lie in a bunker
- no lie effect but rough, and no uphill or downhill stance; no flyer
- putting is 2-D and flat-sloped; a putt that misses the green keeps rolling as if it were on one
- a 25% wedge is modelled with the same 1.1° face error as a driver, which is generous to the short game
- **no crosswind correction by the athlete** — it can read a headwind and it cannot read a sidewind
- twelve strokes and the ball is picked up; the card records +4 and moves on
- one athlete. Golf's other half — a field, a cut, a card read against other people's — is not here

Two things were tried and thrown out, both in the code with their reasons: a **Texas wedge** from inside
60 ft of the flag, which turned every fringe into a two-putt and every round under par; and a **learned
rough coefficient**, which could not be separated from the notebook's own errors.

## What would come next, in order

1. **The bunker's lip, if golf is to keep going.** The fourth pass built the bunker that the third pass asked
   for and got nothing, because the missing half of a bunker is the wall you have to carry; without it the
   sand is a slow lie and the target decision never becomes two-dimensional. A lip is cheap to state — a
   minimum carry height over the sand's inner edge — and it would make the recovery a real decision instead of
   a shorter shot. By the stopping condition I set before this pass, that is the honest next step and this is
   the last cheap one: after it, the untested claims need slope, sand physics or spin, and the game rests.
2. **A course that is not straight.** One dogleg changes the drive from "hit it as far as you can" into a
   decision with a number on it, and it is the cheapest way to make the driver's distance matter.
3. **The picture.** A golf render is cheaper than a tennis one: one ball, one flight, a camera behind the
   ball, no opponent, and the whole shot is over in six seconds. `games/tennis/replay3d.html` is the template
   and `lab/tennis.py`'s `trace=` is the data. It should be built when there is a round worth watching.
