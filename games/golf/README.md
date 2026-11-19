# golf — a bag, a course, and the number that says which club was wrong

Built 2026-11-19 by Dmitri, from the founder's suggestion of the same day. Second pass the same night:
wind, and the decision about where to aim. The tool is `lab/golf.py`; the runs are
`records/golf-2026-11-19.txt`; the checks are `python3 lab/golf.py --selftest` (15 of them).

    python3 lab/golf.py                    # six rounds of nine, then six holes never played
    python3 lab/golf.py --calm             # the same pins on a still day
    python3 lab/golf.py --learn 0          # the control: same athlete, same seed, never updated
    python3 lab/golf.py --policy flag      # aim at the pin / centre: the middle / spread: where the putt is likeliest
    python3 lab/golf.py --compare          # train one athlete, then play all three policies against each other
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

### Four findings

1. **A wrong notebook costs about five strokes a round, and only after it has been paid for.** The learner
   starts four strokes worse than a player who never practises (+16 against +13) and finishes five to eight
   better. It is the putts early on: thirty of them in the first round against eighteen. A wrong notebook
   does not miss the flag so much as miss it into places where the next shot is harder.
2. **The wind is worth five strokes a round and cannot be learned, only paid.** The same course, same pins,
   same seed: +22, +17, +12, +10, +6, +5 with the wind against +16, +13, +10, +3, +5, +8 in still air. The
   athlete learns the *along* part — its coefficient settles at 0.95 against the model's own 0.7 per unit of
   head fraction — and cannot learn the *across* part at all. A crosswind moves the ball 31.8° per unit of
   cross fraction, and there is no column in a notebook for that.
3. **On a still day, aiming at the pin is a mistake worth three strokes a round.** One trained athlete, four
   rounds under each policy, learning off, same draw:

   | policy | strokes (36 holes) | to par | greens hit | putts |
   |---|---|---|---|---|
   | at the pin | 148 | +8 | 28/36 | 76 |
   | at the middle of the green | 140 | 0 | **32/36** | 76 |
   | where the putt is likeliest | **136** | **−4** | **32/36** | **72** |

   Three strokes a round, and it is the same three the caddie has been charging for since caddies: a pin
   cut near an edge is not worth fourteen feet of proximity. The scatter it measured (1.8°) is what decides
   it — with a 17-foot wide pattern, the middle is a better target than the flag, and the athlete works that
   out from its own misses.
4. **The same experiment on the windy course reverses, and I will not call that a finding.** With the wind
   on, pin-hunting wins by twenty strokes over aiming at the middle (128 against 156), and the reason is a
   property of *my* arrangement, not of golf: nine pins and nine winds are nine fixed pairs, I chose them,
   and an athlete that cannot correct for crosswind drift is lucky or unlucky depending on which way the
   wind blows past which pin. It is a caution about the design, and the next pass should randomise the pin
   and wind pairing before anyone reads a number off the windy column.

## What this does not model

- no bunker, water, dogleg, tree line, or green contour; one slope for every hole
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

1. **Randomise the pin and wind pairing**, and run the three policies again over many draws. The calm result
   is a finding; the windy one is a coin that I minted. This is an hour's work and it is the first thing that
   should happen, before any of the rest.
2. **A course that is not straight.** One dogleg changes the drive from "hit it as far as you can" into a
   decision with a number on it, and it is the cheapest way to make the driver's distance matter.
3. **The picture.** A golf render is cheaper than a tennis one: one ball, one flight, a camera behind the
   ball, no opponent, and the whole shot is over in six seconds. `games/tennis/replay3d.html` is the template
   and `lab/tennis.py`'s `trace=` is the data. It should be built when there is a round worth watching.
