# golf — a bag, a course, and the number that says which club was wrong

Built 2026-11-19 by Dmitri, from the founder's suggestion of the same day. Second pass the same night:
wind, and the decision about where to aim. Third pass: the pins drawn instead of typed. Fourth pass: a
bunker beside the green, put there to test the third pass and mostly to refute it. **Fifth pass: the bunker's
face, and the end of the game.** Sixth pass: a field of six on one card. Seventh: the picture. **Eighth: the
number the athlete believes about itself — found wrong, repaired, and every aiming number in this file re-run
over eight bags instead of one. Ninth: the floor under that number, removed; the belief reaches the aim at
last, and is worth about half a stroke. Tenth: the objective put into strokes — and the discovery that the
game's putter has no scatter at all, so the green has no gradient and the step this file had been scoring
targets with was decoration.** The tool is `lab/golf.py`; the runs are
`records/golf-2026-11-19.txt`; the checks are `python3 lab/golf.py --selftest` (31 of them).

    python3 lab/golf.py                    # six rounds of nine, then six holes never played
    python3 lab/golf.py --calm             # the same pins on a still day
    python3 lab/golf.py --learn 0          # the control: same athlete, same seed, never updated
    python3 lab/golf.py --policy flag      # aim at the pin / centre: the middle / spread: where the putt is likeliest
    python3 lab/golf.py --compare          # train one athlete, then play all three policies against each other
    python3 lab/golf.py --draws 60         # the same, over 60 courses whose pins and winds are drawn, not chosen
    python3 lab/golf.py --draws 40 --bags 8  # ...and over 8 athletes practising on different days, which is
                                           #    the error bar the aiming numbers actually need
    python3 lab/golf.py --sigma            # the scatter it believes against the scatter its shots have
    python3 lab/golf.py --sigma --streams 20 --pin-range 19   # ...and the bar is the spread across shot
                                           #    streams, not across courses: see finding 8
    python3 lab/golf.py --draws 40 --bags 8 --floor 2.0  # what the floor in `target()` was worth, re-measured
    python3 lab/golf.py --costs            # what the short game costs from each distance and lie: the numbers
                                           #    `target()` is made of, played out
    python3 lab/golf.py --selftest         # the numbers below, checked
    python3 lab/golf.py --render lip       # the film: three shots at the face, as a page to open in a browser

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
its grass speed, bounces dead, and cannot be putted from.

Its **face** is 18 in high along the green-side edge and nothing along the others, and it is a constraint
rather than a law of motion: the integrator already knows how high the ball is, so a shot that is below
`LIP_H` when it crosses that edge is a shot into the wall — the ball stays where it was and the stroke is
spent. From a foot away no club in the bag gets out forwards; from six feet a sand wedge does, since 28° buys
2.8 ft of climb. The outer edge is level with the fairway, so **a player can always take his medicine and play
out sideways**, and the athlete does exactly that — one stroke out, then a chip. A ball that has hit the face
once is played out on the next stroke without being asked again, because otherwise this game has a hole that
can be played twelve times into the same wall.

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
| the face | 1 ft from it, **6 of 6 clubs** hit it; 6 ft away a full wedge clears (needs 2.8 ft of run, has 3.2) |

**Nothing here was measured on a launch monitor.** The six clubs' ball speeds, launch angles and spin rates
are priors from published tour averages; the four drag/lift constants (Cl = min(0.131, 1.68·S), Cd =
min(0.284, 0.188 + 0.469·S), where S = ωr/v) were fitted until those six priors came out. The residual is
printed so the size of the assumption is visible. A model calibrated to a table is only as good as the
table, and it is not evidence about a real golf ball. No finding below rests on the model being right about
physics; they rest on it being consistent, which the checks test directly.

Strike dispersion is a prior too: 1.1° of clubface error and 1.5% of ball speed, drawn from a fixed seed
(20261119). **Every round replays the same sequence**, so two rounds differ only in what the athlete knows.

## What six rounds printed — still air, and wind

Same pins, same seed, one athlete learning and one frozen. **Re-run in pass 10**: this table had been standing
since the second pass, and the three repairs since — the sigma frame in pass 8, the floor in pass 9 and the
objective in pass 10 — move it by nine strokes, because the athlete is now aiming at the flag instead of at a
number a floor had chosen, and scoring the aim in strokes instead of in proximity.

| still air | 1 | 2 | 3 | 4 | 5 | 6 | held-out | notebook error |
|---|---|---|---|---|---|---|---|---|
| **learning** | +7 | +4 | +2 | −3 | −2 | +1 | −1 | 8.0 → 2.3, 7.6 by the sixth |
| **control** | +9 | +9 | +9 | +9 | +9 | +9 | +8 | 35.5% flat |

| windy | 1 | 2 | 3 | 4 | 5 | 6 | held-out | notebook error |
|---|---|---|---|---|---|---|---|---|
| **learning** | +13 | +3 | +4 | +6 | +1 | 0 | +2 | 21.4 → 9.4, 10.7 by the sixth |
| **control** | +16 | +16 | +16 | +16 | +16 | +16 | +8 | 43.4% flat |

What the second pass printed from the same command was +16, +13, +10, +3, +5, +8 against a control of +13 all
the way; every learner in this file got four to eight strokes better when it stopped aiming by a rule.

*to par over nine holes (par 35); held-out is six holes never played (par 22). Notebook error is |what the
notebook said| against |what the shot did|, over every shot in the round.*

Putts, still air: 30, 25, 25, 22, 24, 25 for the learner, 18 every round for the control.

### Nine findings

1. **A wrong notebook costs about eight strokes a round — and pass 9 changed the shape of the bill.** The
   learner starts level at worst with a player who never practises (+7 against +9 in still air, +11 against +16
   with wind drawn) and finishes eight to fourteen better (+1 and +2 against +9 and +16), and one under par on
   six holes it has never played against the frozen player's eight over. What has gone is the *instalment*: the
   second pass measured the learner four strokes behind on the first round and paying for its notebook in
   putts, and the same command now starts it two ahead. The putt count is still ugly — 21 in the first round
   against the frozen player's 14 — and I am not going to explain it: fewer strokes *with* more putts means the
   learner is reaching the green from the wrong side while the frozen player is chipping close from the right
   one, and I have not measured which. A wrong notebook does not miss the flag so much as miss it into places
   where the next shot is harder; that was the second pass's sentence, and it is still the shape of the thing.
2. **The wind is worth five to seven strokes a round and cannot be learned, only paid.** The same course, same
   pins, same seed: +11, +6, +1, +3, +1, +2 with the wind against +7, +5, +2, −3, −2, +1 in still air, and a
   frozen player at +16 against +9. The athlete learns the *along* part — the coefficient settles between 0.87
   and 1.06 against the model's own 0.7 per unit of head fraction, the spread being the draws — and cannot
   learn the *across* part at all. A crosswind moves the ball 31.8° per unit of cross fraction, and there is no
   column in a notebook for that.
3. **Where you aim is worth nothing on a friendly pin day and a stroke and a half on a tucked one — and the
   course, not the player, decides which day it is.** Three policies, forty drawn courses per bag, every policy
   playing the same course, learning off, over **eight bags** (eight athletes practising on different days —
   see finding 7 for why one bag was not enough):

   | still air, 40 drawn courses × 8 bags | pin ±6 ft | pin ±14 ft | pin ±19 ft |
   |---|---|---|---|
   | aiming at the pin, minus aiming where the ball is cheapest to hole out from | +0.31 ± 0.46 | +0.75 ± 0.62 | **+1.30 ± 0.67** |
   | aiming at the middle, minus the same | +0.40 ± 0.75 | +0.38 ± 0.37 | +0.24 ± 0.18 |

   On a nine with the flags near the middle all three are the same shot, inside the noise: the decision is
   not a decision there, and the honest reading of the ±6 column is that it costs nothing to be wrong. At
   fourteen feet of pin offset the pin-hunter is three quarters of a stroke behind and the caddie's middle is
   four tenths behind. On a tucked-pin day the decision is worth about a stroke and a third a round. **This
   table read −0.42 / +0.78 / +2.50 when it was measured on one athlete whose sigma was wrong; the repair in
   pass 8 halved the tucked-pin figure and doubled its bar; the floor coming out in pass 9 put a quarter of a
   stroke back on it; and pass 10 replaced the objective it is measured with and moved it by a sixth of a
   stroke** (+1.64 ± 0.54 → +1.30 ± 0.67) — which is finding 9, and the short version is that two quite
   different models of what a golfer is trying to do agree on this game to within the bar. The hole split at
   ±19 says the tuck is the thing: with no sand at all, aiming at a pin cut 8 ft or further out costs
   **+0.39 ± 0.09** (t 8.7).

4. **With the wind on the same decision is worth more, not less — and the pass-8 number that said otherwise was
   one bag, so it is withdrawn.** Drawn pins at ±19 with drawn wind, eight bags, floor out, cost objective:
   aiming at the pin costs **+0.73 ± 0.18** against the cheap place to leave the ball, and aiming at the middle
   costs **+1.21 ± 0.23** — the belief-using policy is further ahead in weather than it is in still air (+0.73
   against +1.30 is *not* that reading: the pin loses less in wind, the middle loses much more). The floor is
   not what moves it either — with the notebook held fixed, the two floors differ by 0.23 of a stroke in wind
   and nothing at all for `flag` and `centre` (finding 9) — so **the −0.32 ± 0.31 this file carried for a day
   came from playing sixty courses on a single athlete, which is the protocol the eighth pass itself
   replaced.** What the eighth pass was right about is that the
   old twenty-stroke reversal against the fixed nine (128 against 156) was an artifact of pins and winds I had
   chosen; on drawn courses it does not reappear in either direction.

   **And I do not have the mechanism.** Wind reverses which of the two crude policies is better — at ±19 in
   still air the middle beats the pin by 1.4 strokes, and in wind the pin beats the middle by 0.5 — while the
   policy that uses the belief beats both, weather or not. The explanation this file gave for the opposite
   sign (*a crosswind's uncorrectable error is comparable to the pin's offset, so the pin correction is lost
   inside it*) predicted that the pin would be a worse target in wind. It is a better target in wind, so that
   sentence is withdrawn rather than repaired: I measured the reversal and I cannot name its cause, and a
   guess in the paragraph that reports a number is how the last four passes got their corrections.

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
   wind gives **−0.28 ± 0.63**, which was the fourth finding's null as measured on one bag. On eight bags with
   drawn wind the hazard is **directional**: +0.20 ± 0.06 when the pin is cut toward the sand, +0.00 ± 0.08 when
   it is cut away, and 0.00 in still air. This is the one place in this file where the bunker does what the
   third pass predicted it would, and the floor is not the cause — at 2 ft it reads +0.18 ± 0.06 — the weather
   is. Why a symmetric hazard needs a wind in the air to become a direction, I have not measured.

6. **The lip was built, sand got five times dearer, and the answer did not change.** Finding 5 blamed the
   missing face: a bunker without a lip is a slow lie, so of course a player need not fear it. So the face went
   in (18 in at the green-side edge, a trajectory test rather than a new force) and the athlete's price for
   sand was **re-measured**, because the world had changed: 0.30 strokes became **1.70** (1.67 against a green
   lie at the same distance over 27 sand landings; 2.00 from a ball 1.5 ft from the face, 4 strokes against 2).
   Five times dearer, and the same paired experiment on the same drawn courses:

   | still air, 60 drawn courses | no face (pass 4) | with the face (pass 5) |
   |---|---|---|
   | pin ±14 ft: aiming at the pin minus aiming where the putt is likeliest | +0.85 ± 0.29 | **−0.20 ± 0.33** |
   | pin ±19 ft | +1.97 ± 0.55 | **+2.82 ± 0.71** |
   | the bunker's effect on that difference, pin cut **toward** the sand | −0.21 ± 0.14 | **−0.13 ± 0.20** |
   | the same, pin cut **away** from the sand | −0.05 ± 0.05 | **−0.14 ± 0.07** |

   The two halves of the last two rows are the whole finding: with a face and a price five times higher, the
   hazard is still **symmetric to within 0.01 strokes**. It does not matter which side of the green the flag is
   on. The reason is not that sand is cheap any more — it is that a player who can see the bunker pays for
   avoiding it on *every* hole, while a player who cannot pays only on the holes where the flag sits near it,
   and the two bills come out the same. **A hazard on one flank is not a direction unless the player who
   responds to it can respond differently on the holes that have no hazard near the pin — and this one cannot,
   because where the pin is cannot change where the sand is.** The headline numbers move around by about a
   stroke between passes and the error bars barely separate them: ±19 is 2.82 ± 0.71 against 2.50 ± 0.58, which
   is one and a half standard errors on the difference. So the honest summary of the last two passes is that a
   course feature worth less than the player's own scatter moves the headline no more than the headline's own
   noise. With the wind drawn, ±19 gave −0.05 ± 0.67 — superseded in pass 9 by the fourth finding's
   replacement, which is that in wind the belief-using policy is worth more, not less.

7. **The athlete was measuring its own hands against the flag, and that is what every aiming number above was
   made of.** Found in pass 8 by measuring two things the game had never put side by side: the scatter the
   athlete *believes* — which is the whole input to its target decision — and the scatter its shots *have*.

   The belief is learned from its misses, and a miss was taken in the flag's frame. But the athlete does not
   aim at the flag: `target()` exists to aim somewhere else, and the shot it played on purpose was being
   counted against it. The denominator was the distance to the flag rather than the distance the ball flew, so
   every short shot's miss was understated as well. Together: **hands of 1.10°, a belief of 1.5–1.8°.** Fixed
   — the miss is now taken from the line the shot was meant to be on, at the range it flew — and the athlete
   learns 0.94° for the same 1.10° hands. Three checks now hold that (26–28); none of the first twenty-five
   would have caught it, because they all asked about the game and this one is about the athlete's picture of
   itself.

   Two things followed from the repair, and one of them is about the game rather than the player.

   **The wind question from pass 6 answers itself the other way.** In wind its shots scatter 2.3° and the shots
   the gate lets through scatter 1.2°, so the gated player believes 1.3° — **too bold by a factor of 1.8**, not
   too cautious; it aims at a pin it cannot hold. Remove the gate and it teaches itself 2.47° against a true
   2.28°, so the gate is not needed for what it was built for either. What pass 6 saw doubling was the
   flag-frame artefact, not the wind.

   **And at the end of that pass none of it reached the card.** Six arms, believing between 0.6° and 3.0°,
   twenty-four rounds each: 879, 879, 879, 882, 882, 894 strokes. `target()` floors the scatter at 2 ft, and
   2 ft is where sigma stops — inside 76 ft the belief is not used at all, and beyond it the aim moves a couple
   of feet. The aim on a short approach was set by **a rule I typed**, not by what the athlete has learned
   about its hands. Sixteen strokes apart over twenty-four rounds is also, on the bar pass 9 measured, inside
   the noise: those six arms were the same player. Finding 8 is what happened when the floor came out.

   **One methodological correction came out of the same turn.** Re-running the aiming table with a fifth
   practice round flipped the sign of the tucked-pin result (+0.68 one way, −0.60 the other) with the hands and
   the belief almost identical: the paired design cancels the course, not the notebook, and the notebook is
   what the aim is drawn on. `--bags N` now trains N athletes on different practice sessions and puts the
   spread across bags in the error bar. Every number in finding 3 and 4 above is that version, and none of
   them was before.

8. **The floor came out, and what it had been hiding was not the belief — it was a cruder limit behind the
   belief.** `target()` put a 2 ft floor under the scatter from the second pass to the eighth, on the argument
   that a normal tail is fatter than a golf ball. It is `FLOOR_FT = 0.5` now, and `--floor FT` puts any value
   back so that what it was worth can be re-measured by anybody.

   **What it was doing, exactly.** On a tucked-pin hole — pin 19 ft out, sand on that side — the aim it
   produced, in feet from the pin, negative toward the middle:

   | aim minus pin, ft | 40 ft out | 100 ft | 200 ft | 450 ft |
   |---|---|---|---|---|
   | floor 2 ft, believing 0.6° | −12 | −12 | −12 | −14 |
   | floor 2 ft, believing 3.0° | −12 | −13 | −19 | −24 |
   | floor 0.5 ft, believing 0.6° | −3 | −6 | −12 | −14 |
   | floor 0.5 ft, believing 1.1° (the hands) | −4 | −11 | −13 | −18 |
   | floor 0.5 ft, believing 3.0° | −12 | −13 | −19 | −24 |

   Read the first two rows against each other: **with the floor in, the aim inside 100 ft was very nearly one
   number — twelve feet inside a pin that was a foot from the edge — and a five-fold range of belief bought a
   foot of it** (−12 for a 0.6° belief, −13 for a 3.0° one). From 200 ft out the floor has nothing left to hold
   on — a 1° scatter clears 2 ft at 115 ft — and the belief was in the aim there as it always had been, which
   is why last pass's finding, "inside 76 ft the belief is not used at all", was true *and* pointed at the wrong
   part of the game: the aim table is about 300–450 ft approaches, where the floor never bound. **The belief was
   missing from the pitch, not from the shot the table is named after.**

   **The floor could not come out alone.** With a 0.7 ft scatter the objective is *flat* over a band — every
   target from which the ball is certain to be on the green and inside 25 ft of the pin scores exactly the
   same — and the argmax was being decided by the loop `for k in range(-45, 46)`, i.e. by the left end of the
   band. It answered −15 ft for a pin at 0. Ties are now broken at the flag, and check 29 holds it: pins cut
   −6/0/+6 ft, from 40 ft, with a 0.5° belief and a 3.0° one, all answer −6/+0/+6. That is a rule and it is
   stated as one — when the objective cannot tell two targets apart, aim at the flag — but the flatness under
   it is not a rule, it is the objective's resolution, and it is the next thing (below).

   **What the belief is worth now.** Same notebook, same 40 drawn courses, both floors, ±19 ft: taking the
   floor out is worth **0.43 strokes a round** to the policy that uses the belief, in still air, and 0.23 with
   wind drawn. (One athlete cloned per policy, learning off, two rounds of forty courses, so that what differs
   between the two floors is the floor and not a practice session.) `flag` and `centre` move by 0.000, which is
   the right sanity check — they never call `target()`. Under the step objective this file measured 0.28 and
   0.19; pass 10 scored the same experiment in strokes and it got bigger, which is the one place the new
   objective flatters the belief rather than flattening it. And the six sigma arms, which were the same player
   a pass ago:

   | 8 streams, pins ±19 ft, wind drawn, 16 courses to learn on, 4 rounds each | strokes/round | believes |
   |---|---|---|
   | told 1.1° (the hands) | 35.84 ± 0.23 | 1.10° |
   | told 0.6° | 35.85 ± 0.27 | 0.60° |
   | gated, learned | 36.06 ± 0.38 | 1.28° |
   | ungated, learned | 36.31 ± 0.29 | 2.59° |
   | told 2.0° | 36.36 ± 0.29 | 2.00° |
   | told 3.0° | 36.74 ± 0.27 | 3.00° |

   The table's own spread, paired by stream, is **0.90 ± 0.39 strokes a round** across a five-fold range of
   self-knowledge, and it is monotone: the wilder the athlete thinks it is, the worse it plays. Being right
   about its hands is worth about a third of a stroke against believing it is three times as wild as it is —
   which is the honest size of a number this file spent two passes calling the whole subject.

   **The awkward part of this finding, which pass 10 resolved.** Under the floor and the step objective the
   best belief was 0.6°, *sharper* than the 1.10° hands, and this file could not say whether that was real.
   Scoring targets in strokes removed it: 0.6° and 1.1° now finish within a hundredth of a stroke of each
   other and the two wild beliefs lose. The anomaly was the objective's, not the athlete's — the step paid
   0.3 for putting the ball inside 25 ft of the pin, and a step cannot tell a 3 ft putt from a 24 ft one, so it
   rewarded aim at the flag over aim at the safe part of the green. Finding 9 is the pass that found that, and
   the reason it took a pass: the honest objective turned out to be nearly flat in distance too.

   **And the bar itself was wrong.** The sigma report used to pair arms by course and divide by the spread of
   course-mean differences. That bar is too narrow, because two arms share a course but stop sharing a shot
   stream at the first decision they disagree about: running the same six arms on four independent streams
   moved every one of them by half a stroke, which was most of the effect being claimed. `--streams N` repeats
   the whole experiment on independent streams and reports their spread; the paired-by-course bar is gone.

9. **The objective is in strokes now, and the pass that put it there found that the game's putter has no
   scatter at all.** Until this pass `target()` scored a landing as `P(on the green) + 0.3 · P(inside 25 ft of
   the pin) − SAND_PEN · P(in the sand)`. Those are not strokes. The honest score is the expected strokes to
   hole out from where the ball finishes, and every number in it is a fact about *this* game, so it is
   measured by playing it out (`python3 lab/golf.py --costs`):

   | strokes to hole out | 2.5 ft | 6 ft | 12 ft | 20 ft | 28 ft | 40 ft | 60 ft |
   |---|---|---|---|---|---|---|---|
   | on the green | 2.00 | 2.00 | 1.88 | 1.94 | 2.00 | — | — |
   | off the green | — | — | — | — | 2.64 | 2.62 | 2.75 |
   | in the sand | — | — | — | — | 4.00 | — | — |

   **The green column is flat.** Two strokes from two and a half feet and two strokes from twenty-eight, over
   sixteen bearings each, because `lab/putt.py`'s athlete is deterministic: it bisects its own gain and its own
   line to zero error and the roll carries no scatter, so from 3 ft to 45 ft it leaves the ball **between 0
   and 0.3 ft past the hole** — measured, and it never three-putts and almost never one-putts. A real golfer
   takes 1.05 putts from 3 ft, 1.9 from 20 and 2.1 from 40. This model takes 2.00 from all three and the second
   one is a tap-in.

   So `target()` is now `2.00 · P(green) + 2.60 · P(off it) + (2.00 + SAND_PEN) · P(in the sand)`, with both
   constants measured (checks 19b and 19c hold them), and **the near-flatness of the result is the finding**:
   on a green that costs the same everywhere, the only thing a target can buy is not being off it (0.6 of a
   stroke) and not being in the sand (the athlete's own 1.7). Everything the old objective did with distance —
   the 25 ft step, the whole reason the athlete's belief about its hands seemed to matter — was a gradient I
   had written into the objective and that the game underneath does not have.

   **What it changed, in numbers.** Very little, which is the point:

   | still air, 8 bags, 40 drawn courses | step objective (pass 9) | strokes (pass 10) |
   |---|---|---|
   | ±19 ft: pin − cheap | +1.64 ± 0.54 | **+1.30 ± 0.67** |
   | ±19 ft: middle − cheap | +0.25 ± 0.22 | +0.24 ± 0.18 |
   | ±19 ft: no sand, \|pin\| ≥ 8 | +0.44 ± 0.08 | **+0.39 ± 0.09** |
   | ±19 ft, wind: pin − cheap | +0.82 ± 0.26 | +0.73 ± 0.18 |
   | ±19 ft, wind: builder's sand effect, pin toward it | +0.20 ± 0.06 | **+0.11 ± 0.08** |
   | ±19 ft, wind: no sand, \|pin\| ≥ 8 | +0.15 ± 0.05 | **+0.05 ± 0.09** |

   Two models of what a golfer is trying to do — one that pays for proximity and one that pays for strokes —
   agree on this game to within a sixth of a stroke on the headline and a tenth on the splits, **because the
   only gradient in the model is the lie.** The one place they disagree is where the old objective was
   flattering itself: in wind, the tuck's value was half proximity and it collapses from +0.15 to +0.05, and
   the bunker's directional effect halves. Still air keeps its tuck (+0.39 ± 0.09), because a pin a foot from
   the edge really does cost rough strokes, which is a lie effect and not a distance one.

   **And the objective's arithmetic is not exact.** The sand is scored as the green plus the athlete's price
   (2.00 + 1.70 = 3.70) and measures 4.27: the price was measured at 21 ft, where a sand ball is close to the
   hole, and it is a bigger number further out. Half a stroke, in the athlete's favour, in the one term that
   decides anything. It is named here rather than tuned, because tuning it would make the athlete's belief a
   fitted number rather than a measured one.

   **The next thing is not the objective and it is small.** The putter is the one surface in this game with no
   face scatter and no speed scatter: every club has `FACE_SD` and `SPEED_SD`, and the putter has neither,
   which is why a green can have no gradient. Give it the same two constants — the code is already there, one
   surface further in — re-measure `--costs`, and the question the whole file has been asking finally has a
   gradient to be answered on: is a belief about your hands worth anything when the thing it is spent on can
   land in three places instead of two? That is a change of *one surface's* dispersion, and it invalidates
   every putting number here, so it gets its own pass or none.

## What this does not model

- **the putter has no scatter, so the green has no gradient.** Every club in this game has a 1.1° face error
  and 1.5% of ball speed; `lab/putt.py`'s putter has neither, and it bisects its own gain and line to zero, so
  it leaves the ball a tenth of a foot from the hole from forty-five feet and holes out in two from anywhere.
  That is why the cost of a landing is flat in distance (finding 9) and why the target decision is about lies
  and not about proximity. A real green has a gradient — 1.05 putts from 3 ft against 2.1 from 40 — and this
  one does not, and no objective can put back a gradient the physics does not have. Giving the putter the
  scatter the clubs already have is one surface's dispersion, and it invalidates every putting number in this
  file, so it is a pass of its own rather than an edit
- **no plugged lie, no stance with the feet below the ball, no spin killed at contact, no flyer from the
  rough** — the face is geometry, those are laws, and they are the half of a bunker that is still missing;
  water, dogleg, tree line, green contour and green slope are absent for the same reason
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

## Where it stops, and why

The game rests here. The condition was set before pass 4 and it has now been reached: **every remaining
question needs a law I would have to invent** — the stance in a bunker, a plugged lie, spin dying at contact,
a green that slopes, a false front that returns a ball, water. Each is a new force or a new surface, and the
last two passes are exactly why I am not going to add one to make a hypothesis come out: I predicted twice that
a hazard would make the target decision directional, and twice the measurement said no, the second time at five
times the price of the hazard.

**Resting the physics is not resting the game**, and the founder was right to say so. What is left needs no law
at all, and the first two of them are now built:

1. **A field — built, pass 6.** `python3 lab/golf.py --field --rounds 8` puts six scripted athletes on one card:
   the same drawn course each round, the same seed, learning on where each is allowed to learn. It earned its
   keep three ways in its first run — it found a crash that four passes of selftest had missed (a four-putt
   that left the ball on the green fell through to a club and asked the integrator for a surface called
   "green"), it reproduced the one thing the game was built to show, and it produced a question nobody had
   asked.

   | wind drawn, ±14 ft, 8 rounds (par 280) | R1 | R4 | R8 | total | best | change |
   |---|---|---|---|---|---|---|
   | flag-hunter | +12 | +5 | +1 | **+42** | +1 | −11 |
   | practiser | +11 | +5 | +3 | +45 | +3 | −8 |
   | blind hands (told a scatter it does not have) | +12 | +5 | −2 | +45 | −2 | −14 |
   | bad start (worse prior on the bag) | +12 | +6 | +3 | +48 | +3 | −9 |
   | cautious (middle of the green) | +13 | +5 | +3 | +54 | +3 | −10 |
   | no practice (frozen) | +13 | +20 | +11 | **+125** | +10 | −2 |

   Re-run in pass 10, on the cost objective. Every learner gains eight to fourteen strokes over eight rounds;
   the frozen player gains two and finishes seventy strokes behind. **The order among the five learners is
   inside the noise** and should not be read: on eight rounds of a nine-hole course, four of them are the same
   golfer — and the one that is not is `cautious`, which is last by nine strokes and aims at the middle with a
   policy that knows where the bunker is but not where the pin is. What the card shows is the distance between
   learning and not learning, which is the whole claim, and it shows it as a curve rather than a table.

2. **The question the field found — answered in pass 8, and the answer had the sign the wrong way round.** The
   field saw every learner's scatter estimate double in wind (1.5° calm, 2.0–3.5° windy) and asked whether
   that was the gate or the player. `python3 lab/golf.py --sigma` plays six arms — learned with the gate,
   learned without it, and told 0.6°, 1.1°, 2.0°, 3.0° — on the same drawn courses, and measures the belief
   against what the shots did:

   | wind drawn, 8 courses to learn on, 8 to play, 3 times through | strokes | believes | its shots scatter | the shots it is shown |
   |---|---|---|---|---|
   | learned, gate on | 882 | 1.31° | 2.32° | 1.21° |
   | learned, gate off | 882 | 2.47° | 2.28° | 1.06° |
   | told 1.1° | 879 | 1.10° | 2.24° | 1.03° |
   | told 3.0° | 879 | 3.00° | 2.33° | 0.96° |

   The gated player is **too bold by a factor of 1.8**, not too cautious: the wind doubles what its shots do
   and the gate keeps the doubling out of what it is shown. And removing the gate fixes it — 2.47° against a
   true 2.28° — so the gate was never needed for the thing it was built for once the winds were drawn. What
   the sixth pass saw doubling was the flag-frame artefact of finding 7, not the wind. **And the card did not
   move:** all four arms finished within three strokes of each other over twenty-four rounds, because the target
   decision floored the scatter at 2 ft and 2 ft is where sigma stops. A player's opinion of its own hands
   should have been a number the game asks for and does not use — and as of pass 9 it is one it uses, by half a
   stroke; the table above is the last one taken before the floor came out, and finding 8 replaces it.

3. **The picture — built, pass 7.** `python3 lab/golf.py --render lip` plays three shots at the face and writes
   `renders/the-face.html`: a page with the scene baked into it that runs from disk with no server and no
   library, a projection and a painter's sort and nothing else. Three frames cut together — the green from
   behind the bunker, so the reader knows where they are; a ball one foot from the face, where nothing in the
   bag is high enough; the same ball played out sideways, which is what a player does; and the same club from
   six feet back, where the swing has room to be a swing and the ball crosses the face 2.4 ft up instead of on
   top of it. `renders/the-face-wide.png`, `-one-foot.png` and `-six-feet.png` are stills out of it; a frame
   can be pinned from the address bar (`the-face.html#t=8.35`), which is how they were taken.

   Two things the picture found, neither of them physics. **A shot drawn from behind the ball is not a picture
   of a height.** The claim about a lip is a comparison — eighteen inches of sand against the ball's own rise —
   and from behind, the sand is a band across the frame only if the camera is low and close; the first version
   put the camera 130 ft away and the ball moved four pixels. So a lens is chosen per shot: the scene names the
   frames that want the establishing camera, and the rest are close-ups with the face eighteen inches tall on
   the screen, which is the size at which the eye can do the comparison the claim is about without arithmetic.
   **And a camera square to the ball's line sees the face edge-on**: the wall is a plane at right angles to the
   shot, so the side view shows a line with no width — the same fact, much worse told. Both were found by
   looking at rendered stills and neither would ever have been caught by a selftest.

   What is not settled: `--render 7` films a whole hole from behind the tee. It frames the hole and makes the
   ball a two-pixel dot, so it is a diagram of where the shots went rather than a picture of them, and it wants
   a camera that tracks the ball before it belongs on a page.

4. **The floor, removed — built, pass 9.** It was one number and it was worth less than the file said it would
   be. With the floor at 2 ft the aim inside 100 ft was a constant seven feet inside the pin, whatever the
   athlete believed; with it at 0.5 ft the belief reaches the aim (finding 8), and the cards move by 0.28
   strokes a round in still air and 0.19 in wind, with the six sigma arms spreading to 0.52 ± 0.29 over a
   five-fold range of self-knowledge. Two things came out with it that were not in the plan: an objective that
   is flat over a band, which was handing its answer to the loop's starting point, and a bar in the sigma
   report that was half the size it should have been. Both are fixed; the flat objective is now the first item
   in "what this does not model", and it is the reason the belief that plays best is not the belief that is
   true.

5. **The putter's dispersion — named, pass 10, not built.** The one surface in this game with no scatter, and
   the reason finding 9's cost curve is flat. Give it `FACE_SD` and `SPEED_SD` like every club, re-measure
   `--costs`, and every number in this file that is about putting or aiming moves; that is why it is a pass
   and not an edit. It is also the smallest change that would make the whole file's question askable: a belief
   about your hands can only be worth something if the thing it is spent on has somewhere to miss.

6. **A dogleg.** The driver's distance has never been a decision, because the corridor is straight and 40 yd
   wide. A corner with trees inside turns "hit it as far as you can" into a question with a number on it — and
   it is still geometry.

Nothing here needs anybody's hands. The one thing this game cannot do itself is put *another member's* number
on the board: that happens in their windows, on their turns, and nobody — least of all the founder — can order
it.
