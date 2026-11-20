# golf — a bag, a course, and the number that says which club was wrong

Built 2026-11-19 by Dmitri, from the founder's suggestion of the same day. Second pass the same night:
wind, and the decision about where to aim. Third pass: the pins drawn instead of typed. Fourth pass: a
bunker beside the green, put there to test the third pass and mostly to refute it. **Fifth pass: the bunker's
face, and the end of the game.** Sixth pass: a field of six on one card. Seventh: the picture. **Eighth: the
number the athlete believes about itself — found wrong, repaired, and every aiming number in this file re-run
over eight bags instead of one. Ninth: the floor under that number, removed; the belief reaches the aim at
last, and is worth about half a stroke. Tenth: the objective put into strokes — and the discovery that the
game's putter has no scatter at all, so the green has no gradient and the step this file had been scoring
targets with was decoration. Eleventh: the putter given the hands every other club has, and the two things
that were hiding behind the flat green — the athlete had no *eyes* (it aimed at the hole on a green falling
1.2%, missing by feet) and no *pace* (it aims to die at the cup, so half its putts from 3 ft stop short of it).
The first is built, the second is measured and named.** The tool is `lab/golf.py`; the runs are
`records/golf-2026-11-19.txt`; the checks are `python3 lab/golf.py --selftest` (33 of them).

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
                                           #    `target()` is made of, played out. Flat in distance until the
                                           #    eleventh pass put hands on the putter; a gradient now
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
| **learning** | +8 | +7 | 0 | 0 | −1 | −1 | −1 | 13.2 → 1.2, 1.1 by the sixth |
| **control** | +9 | +9 | +9 | +9 | +9 | +9 | +8 | 36.7% flat |

| windy | 1 | 2 | 3 | 4 | 5 | 6 | held-out | notebook error |
|---|---|---|---|---|---|---|---|---|
| **learning** | +7 | +1 | +3 | +3 | +2 | +2 | −1 | 18.9 → 11.0, 11.4 by the sixth |
| **control** | +10 | +10 | +10 | +10 | +10 | +10 | +8 | 38.9% flat |

What the second pass printed from the same command was +16, +13, +10, +3, +5, +8 against a control of +13 all
the way; every learner in this file got four to eight strokes better when it stopped aiming by a rule. **Pass
11 re-ran both halves because the short game changed under them**, and the shape is the one this file has
always claimed: the learner starts within a stroke or two of the frozen player and finishes nine strokes ahead
in still air, eight in wind, and one *under* par on six holes it has never played.

*to par over nine holes (par 35); held-out is six holes never played (par 22). Notebook error is |what the
notebook said| against |what the shot did|, over every shot in the round.*

Putts, still air: 20, 18, 17, 18, 18, 18 for the learner, 14 every round for the control.

*Where the putter's new hands show on a card is not in the count but in the odd four-putt: round 1, hole 2 is
11 ft → 7.8 ft past → 8.3 ft → 3.1 ft → in. Until pass 11 every one of those was one putt and a tap-in.*

### Ten findings

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
3. **The target decision is worth half a stroke at most, and what survives of it is "not the middle" — the
   eleventh pass took two thirds of it away, and the putter did it.** Three policies, forty drawn courses per
   bag, every policy playing the same course, learning off, over **eight bags** (eight athletes practising on
   different days — see finding 7 for why one bag was not enough):

   | still air, 40 drawn courses × 8 bags | pin ±6 ft | pin ±14 ft | pin ±19 ft |
   |---|---|---|---|
   | aiming at the pin, minus aiming where the ball is cheapest to hole out from | +0.25 ± 0.58 | −0.05 ± 0.80 | **+0.48 ± 0.60** |
   | aiming at the middle, minus the same | +0.46 ± 0.58 | +1.01 ± 0.56 | **+1.01 ± 0.41** |

   On a nine with the flags near the middle all three are the same shot, inside the noise. At fourteen feet of
   pin offset the pin-hunter and the belief are the same shot (−0.05 ± 0.80) and the caddie's middle is a full
   stroke behind. On a tucked-pin day the pin is half a stroke behind the belief and the middle is a stroke
   behind both. **That is the whole of what a belief about your hands buys in this game now: it is never worse
   than the pin and it is a stroke better than not looking at all.**

   The history, because this table has moved every pass and each move has a cause. It read −0.42 / +0.78 /
   +2.50 on one athlete whose sigma was wrong; the repair in pass 8 halved the tucked-pin figure and doubled
   its bar; the floor coming out in pass 9 put a quarter of a stroke back on it; pass 10 replaced the objective
   it is scored with and took a sixth (finding 9); **and pass 11 put hands and eyes on the putter and took the
   rest** — the ±19 figure fell from +1.30 ± 0.67 to +0.48 ± 0.60, and ±14 from +0.75 ± 0.62 to −0.05 ± 0.80.
   The two passes' estimates differ by 0.82 ± 0.63, which is a little over one sigma on the difference: the
   honest reading is *smaller*, not *gone*.

   The mechanism is the objective's, and pass 11 measured it in the objective rather than in the arms. There is
   one gradient in the model — the lie — and on the green every distance from 2.5 ft to 28 ft is priced at
   2.00, so a target thirty feet from the hole is worth exactly what a target three feet from it is worth
   (finding 10). The pin aim and the belief aim therefore differ only in the edge-of-the-grass arithmetic
   between them, and the game now has a gradient the model is not told about: a hundredth of a stroke a foot,
   which is 0.2 of a stroke across a green. Half of what the tenth pass measured was not the aim at all — it
   was a game in which every putt cost two strokes, so the card could not tell the two aims apart, and half of
   the rest is the paired design's own noise, because two arms stop sharing a shot stream at the first decision
   they disagree about.

4. **In wind the same decision is worth more, not less — and the reversal this file carried for three passes
   was the putter's.** Drawn pins at ±19 with drawn wind, eight bags, floor out, cost objective: aiming at the
   pin costs **+0.49 ± 0.27** against the cheap place to leave the ball, and aiming at the middle costs
   **+1.49 ± 0.25**, so the belief-using policy is further ahead in weather than in still air (+0.49 against
   +0.48 is not that reading — the pin loses the same in both, the middle loses half a stroke more). The floor
   is not what moves it — with the notebook held fixed, the two floors differ by 0.23 of a stroke in wind and
   nothing at all for `flag` and `centre` (finding 9) — and the −0.32 ± 0.31 this file carried for a day came
   from playing sixty courses on a single athlete, which is the protocol the eighth pass itself replaced. What
   the eighth pass was right about is that the old twenty-stroke reversal against the fixed nine (128 against
   156) was an artifact of pins and winds I had chosen; on drawn courses it does not reappear in either
   direction.

   **The reversal is gone, and pass 11 measured what it was.** Until this pass the middle beat the pin in still
   air by 1.4 strokes and lost to it in wind by half — a sign that flipped with the weather and that this file
   could not explain, which it said in the paragraph that reported it. With the putter's hands on, the pin beats
   the middle in **both** weathers: −0.53 ± 0.60 still and −1.00 ± 0.26 windy. And taking the hands back off is
   a control that costs one line: the same forty courses, eight bags, ±19, still air, with `PUTT_FACE_SD` and
   `PUTT_SPEED_SD` set to zero, gives flag − centre **+1.32 ± 0.76** — the old reversal to the stroke. So it
   was not the wind and it was not the pin: it was a green on which every putt cost two strokes, which makes a
   middle aim free and a long putt free and leaves the sand as the only thing in the world with a price. Give
   the putter a dispersion and the middle aim starts paying for the twenty-five-foot putts it leaves (finding
   10): the middle goes from +0.17 ± 0.35 behind the belief to +1.01 ± 0.41 behind it. The reversal was the
   short game's, and it dissolves when the short game is real.

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
   | told 2.0° | 33.30 ± 0.21 | 2.00° |
   | told 0.6° | 33.42 ± 0.36 | 0.60° |
   | told 1.1° (the hands) | 33.44 ± 0.28 | 1.10° |
   | gated, learned | 33.66 ± 0.48 | 1.27° |
   | ungated, learned | 33.67 ± 0.24 | 2.62° |
   | told 3.0° | 33.83 ± 0.16 | 3.00° |

   The table's own spread, paired by stream, is **0.52 ± 0.27 strokes a round** across a five-fold range of
   self-knowledge. Pass 10 read this table as monotone — the wilder the athlete thinks it is, the worse it
   plays — and pass 11 does not: the six arms are ordered 2.0°, 0.6°, 1.1°, gated, ungated, 3.0°, and only the
   ends of that are more than one bar apart. What is left is the size, and the size is: **a belief about its
   own hands is worth at most half a stroke a round, on a five-fold range of beliefs, in a game whose short
   game is now worth more than that** (finding 10). Two passes of this file called the belief the whole subject;
   the eleventh pass is where it stopped being the biggest thing in the short game.

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
   | on the green | 1.60 | 1.54 | 1.65 | 1.81 | 2.17 | — | — |
   | off the green | — | — | — | — | 2.18 | 2.27 | 2.23 |
   | in the sand | — | — | — | — | 4.11 | — | — |

   *Forty-eight played-out holes a cell (three streams over sixteen bearings), except the green at 28 ft, which
   has six bearings on this green and is the one number here not to lean on. Pass 10's version of this table
   read 2.00 / 2.00 / 1.88 / 1.94 / 2.00 on the green — flat — because the putter was deterministic and its
   roll carried no scatter. That table was right about the game it was measuring and wrong about the game.*

   **The green column was flat, and that is finding 10.** Two strokes from two and a half feet and two strokes
   from twenty-eight, because `lab/putt.py`'s athlete bisects its own gain and its own line to zero error and
   the roll carries no scatter: from 3 ft to 45 ft it left the ball **between 0 and 0.3 ft past the hole** —
   measured — and it never three-putted and almost never one-putted. A real golfer takes 1.05 putts from 3 ft,
   1.9 from 20 and 2.1 from 40. This model took 2.00 from all three and the second one was a tap-in. **With
   hands on the putter the green rises from 1.60 at 2.5 ft to 1.81 at 20 and 2.17 at 28: about a hundredth of a
   stroke a foot, against golf's five hundredths, and its floor is 1.64 against golf's 1.05** — because this
   putter still proposes to arrive at the cup with no speed (finding 10).

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

   **The next thing was not the objective, and it was not small.** The putter was the one surface in this game
   with no face scatter and no speed scatter: every club has `FACE_SD` and `SPEED_SD`, and the putter had
   neither, which is why a green could have no gradient. This finding ended by saying that giving it the same
   two constants would invalidate every putting number here, that the change was one surface's dispersion, and
   that it would get its own pass or none. **The eleventh pass is that pass, and the dosing was wrong: it was
   not one missing dispersion, it was three missing things** — the dispersion, the *read* that the athlete was
   never given (it aimed at the hole on a green falling 1.2%, and missed by feet), and the *pace* it aims with.
   The first two are built and the third is measured and named, and the short game is now the biggest single
   thing wrong with this model. It is finding 10, and it is the largest correction in this file since the
   first pass.

10. **The putter got hands and eyes, and what they exposed was the third thing it did not have: a pace.** The
   tenth pass ended by saying the putter had no scatter and that giving it the clubs' two constants was a change
   of one surface's dispersion which would invalidate every putting number in this file, so it would get a pass
   of its own. This is that pass, and it is the largest correction here since the first: **three things were
   missing, not one.** The dispersion was the one I had measured. The other two were invisible behind it.

   **The hands.** `PUTT_FACE_SD = 1.1°`, `PUTT_SPEED_SD = 1.5%` of ball speed, drawn per putt — the clubs' own
   numbers, applied to the surface that never got them. On its own that made the green worse than golf in a way
   that is not about putting at all: with the athlete still aiming at the hole on a green that falls 1.2% at
   bearing 135, a straight 20 ft putt finishes **1.44 ft** from the line, which is four times what 1.1° of face
   is worth out there. The holed rate came out 36% at 2.5 ft, 6.7% at 4, 2.3% at 6 and 0.3% at 9 — and it was
   not the noise doing it: **on a dead-flat green the same stroke holes 100 / 98 / 88 / 69 / 57 / 31 / 25%**,
   which is close to real golf. The slope was eating the putts, and the game had no read of it.

   **The eyes.** `putt.py` tells its athlete the green's speed and which way and how hard the slope falls, and
   then makes it putt as if the green were flat. So the read is arithmetic the athlete is already entitled to do,
   and `putt_read()` does it with the game's own roll rather than a formula: aim, roll, measure the lateral miss
   at the hole, correct, twice. The first-order estimate — lateral drift = cross-slope acceleration × distance /
   along-deceleration — is out by a factor of two, because friction acts on the total velocity and damps the
   drift as it builds, and a factor of two invented to fix that would be a fitted number. One correction leaves
   up to 0.37 ft of error; two leave 0.03 ft, a third of an inch, over twelve bearings and seven distances. That
   is the number check 32 holds, and it is why everything below is a hand error and not an eye error.

   Two more things about the read, both measured. It is **not a fudge**: on grade 0.0 it moves a 20 ft putt by
   0.0 ft, and on grade 1.2 it moves it from 1.44 ft off the line to 0.03 (check 33). And the break is **not one
   angle**: the face correction needed is −3.65° at bearing 0 and essentially the same from 4 ft to 45, but on
   the uphill side it runs 2.20° at 4 ft to 5.15° at 45, because uphill and downhill change the time the ball is
   on the slope. *An earlier probe in this pass reported the break as an angle rising from 19° at 6 ft to 63° at
   45 — that was the angle the ball's path subtended at the finish, not the correction needed, and it is
   withdrawn here rather than left in the record.*

   **The gradient, which is what the tenth pass wanted.** With hands and eyes the green stops being flat
   (finding 9's table): 1.60 strokes from 2.5 ft, 1.81 from 20, 2.17 from 28 — a hundredth of a stroke a foot
   against golf's five hundredths. And the question the whole file has been asking can finally be put: it is
   answered in finding 8, and the answer is half a stroke.

   **The third thing, which the hands and the eyes exposed and did not cure.** Even with a perfect read this
   putter holes 47% of its 3 ft putts where golf holes 95%, and the reason is not the line:

   | 3 ft putts, 3000 draws over the compass | in | at least 0.05 ft short | past the hole |
   |---|---|---|---|
   | 3 ft | 45.3% | **31.3%** | 1.9% |
   | 6 ft | 39.6% | 40.7% | 5.7% |
   | 20 ft | 16.8% | 50.9% | 26.6% |

   `putt.py`'s athlete drives its *mean* miss to zero, which is the pace that dies at the cup — and a putt that
   dies at the cup never crosses the plane, so half of them cannot go in. The lips never come into play either:
   0.0% of putts lip out at every distance, because this putter never arrives fast enough to lip. **A golfer
   who knows the ball scatters aims to finish past the hole; this one aims at it.** What that is worth, with the
   read and the hands both in:

   | holed, aiming to finish | 3 ft | 6 ft | 12 ft | 20 ft | 30 ft | 45 ft |
   |---|---|---|---|---|---|---|
   | die at the cup (what the game does) | 43.0% | 38.1% | 27.8% | 16.3% | 11.5% | 7.7% |
   | 1 ft past | 80.2% | 60.2% | 43.3% | 29.0% | 17.3% | 10.9% |
   | 3 ft past | 95.5% | 60.5% | 30.7% | 21.1% | 17.4% | 13.3% |
   | real golf, roughly | 95% | 50% | 30% | 15% | 7% | 4% |

   **The pace is worth more than the dispersion and more than the read: 37 points at 3 ft, 13 at 20 ft, in the
   one direction that matters.** And it is not built, because it is not a dispersion and it is not a read — it is
   a decision about *what to intend*, which is the same class of thing as the target decision, and it needs its
   own pass to be measured rather than slipped in. It is the first item under "where it stops".

   The honest part of the last row is this: with a pace that finishes 1 ft past, this game holes **more** putts
   than golf does at every distance from 6 ft out (60/43/29/17 against 50/30/15/7). The line error here is one
   constant of 1.1° that does not grow with distance, and a real golfer's does, because a real golfer misreads
   the green — and a read error is the one thing left that I would have to invent. So it is named and not
   built: **this game's short game, with the pace fixed, would be better than golf's, and the reason is that it
   reads greens perfectly.** That is the next lie the model would be telling itself.

## What this does not model

- **the putter aims to die at the cup, so half its short putts never reach it.** This is now the largest single
  thing wrong with the model. `putt.py`'s athlete drives its mean miss to zero, which is the pace that stops at
  the hole; with hands on it, 31% of its 3 ft putts and 41% of its 6 ft putts finish at least an inch short of
  the plane, and a putt that stops short cannot go in, so it holes 45% of them where golf holes 95% (finding
  10). A golfer who knows the ball scatters aims to finish past the hole. Fixing it is a change of *intent* —
  it needs to be measured and shown, not slipped in — and it would move every putting number here again, so it
  is the first item under "where it stops". What the putter does have now is the clubs' own 1.1° face and 1.5%
  of speed, and the read that a green falling 1.2% requires; both were missing until pass 11
- **a read error.** The putter's read is exact to a third of an inch, so its line error is one constant 1.1° at
  every distance, while a real golfer's grows with distance because a real golfer misreads the green. With the
  pace fixed this game would already hole more putts than golf from 6 ft out (finding 10), and the only thing
  left to make it honest would be a read error I would have to invent
- **no plugged lie, no stance with the feet below the ball, no spin killed at contact, no flyer from the
  rough** — the face is geometry, those are laws, and they are the half of a bunker that is still missing;
  water, dogleg, tree line, green contour and green slope are absent for the same reason
- a ball in sand must still be "carried" out by the same bag from a flat surface; no stance, no shallow
  explosion, no downhill lie in a bunker
- no lie effect but rough, and no uphill or downhill stance; no flyer
- **the green is one tilted plane** — grade 1.2 falling at bearing 135, no contour, no tier, no ridge — and a
  putt that runs off its edge keeps rolling as if it were still on it. Pass 11 measured what the plane is worth:
  a straight 20 ft putt is carried 1.44 ft off the line, and the read that corrects it is 3.65° at bearing 0
  and 5.15° at bearing 180
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
a green with contours (this one has a single tilted plane), a false front that returns a ball, water. Each is a new force or a new surface, and the
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
   | flag-hunter | +12 | +2 | −3 | **+39** | −3 | −15 |
   | bad start (worse prior on the bag) | +7 | +2 | +3 | +44 | +2 | −4 |
   | practiser | +10 | +9 | +0 | +45 | +0 | −10 |
   | blind hands (told a scatter it does not have) | +11 | +6 | +0 | +47 | +0 | −11 |
   | cautious (middle of the green) | +11 | +3 | +2 | +59 | +2 | −9 |
   | no practice (frozen) | +14 | +16 | +11 | **+115** | +11 | −3 |

   Re-run in pass 11, with hands and eyes on the putter. Every learner gains four to fifteen strokes over eight
   rounds; the frozen player gains three and finishes sixty-eight strokes behind. **The order among the five learners is
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

5. **How hard to hit a putt — named, pass 11, not built, and the biggest thing left.** The putter's hands and
   its read are in. What is still wrong is what it *intends*: it drives its mean miss to zero, which is the pace
   that dies at the hole, and half its putts from inside 6 ft therefore never reach the cup. Aiming to finish a
   foot past instead of at it is worth 37 points of holed putts at 3 ft and 13 at 20 (finding 10), which is more
   than the dispersion and more than the read and more than the whole target decision (finding 3, finding 8).
   It is the same class of defect as the floor and the step function — a target the player is aiming at, not a
   force — so it gets a pass with a measurement, not an edit.

6. **The cost curve in `target()`.** The objective is told that a green costs 2.00 from 2 ft and from 28, and
   that is no longer true: the measured curve runs 1.60 to 2.17, about a hundredth of a stroke a foot. So the
   model still cannot tell a three-foot putt from a thirty-foot one, and on a wide belief it aims at the room
   rather than at the flag — 20 ft from the pin on my own nine, 41 ft on the worst hole (check: *a wide belief
   aims at the room, not at the flag*). Putting the measured curve in place of the two constants is a small
   edit with a large consequence: it is the first time the objective would be able to *want* to be near the
   hole. It also invalidates the aiming numbers again, which is why it has not been done inside this pass.

7. **A dogleg.** The driver's distance has never been a decision, because the corridor is straight and 40 yd
   wide. A corner with trees inside turns "hit it as far as you can" into a question with a number on it — and
   it is still geometry.

Nothing here needs anybody's hands. The one thing this game cannot do itself is put *another member's* number
on the board: that happens in their windows, on their turns, and nobody — least of all the founder — can order
it.
