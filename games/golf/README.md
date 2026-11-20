# golf — a bag, a course, and the number that says which club was wrong

Built 2026-11-19 by Dmitri, from the founder's suggestion of the same day. Second pass the same night:
wind, and the decision about where to aim. Third pass: the pins drawn instead of typed. Fourth pass: a
bunker beside the green, put there to test the third pass and mostly to refute it. **Fifth pass: the bunker's
face, and the end of the game.** Sixth pass: a field of six on one card. Seventh: the picture. **Eighth: the
number the athlete believes about itself — found wrong, repaired, and every aiming number in this file re-run
over eight bags instead of one.** The tool is `lab/golf.py`; the runs are
`records/golf-2026-11-19.txt`; the checks are `python3 lab/golf.py --selftest` (28 of them).

    python3 lab/golf.py                    # six rounds of nine, then six holes never played
    python3 lab/golf.py --calm             # the same pins on a still day
    python3 lab/golf.py --learn 0          # the control: same athlete, same seed, never updated
    python3 lab/golf.py --policy flag      # aim at the pin / centre: the middle / spread: where the putt is likeliest
    python3 lab/golf.py --compare          # train one athlete, then play all three policies against each other
    python3 lab/golf.py --draws 60         # the same, over 60 courses whose pins and winds are drawn, not chosen
    python3 lab/golf.py --draws 40 --bags 8  # ...and over 8 athletes practising on different days, which is
                                           #    the error bar the aiming numbers actually need
    python3 lab/golf.py --sigma            # the scatter it believes against the scatter its shots have
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

### Seven findings

1. **A wrong notebook costs about five strokes a round, and only after it has been paid for.** The learner
   starts four strokes worse than a player who never practises (+16 against +13) and finishes five to eight
   better. It is the putts early on: thirty of them in the first round against eighteen. A wrong notebook
   does not miss the flag so much as miss it into places where the next shot is harder.
2. **The wind is worth five strokes a round and cannot be learned, only paid.** The same course, same pins,
   same seed: +22, +17, +12, +10, +6, +5 with the wind against +16, +13, +10, +3, +5, +8 in still air. The
   athlete learns the *along* part — its coefficient settles at 0.95 against the model's own 0.7 per unit of
   head fraction — and cannot learn the *across* part at all. A crosswind moves the ball 31.8° per unit of
   cross fraction, and there is no column in a notebook for that.
3. **Where you aim is worth nothing on a friendly pin day and a stroke and a half on a tucked one — and the
   course, not the player, decides which day it is.** Three policies, forty drawn courses per bag, every policy
   playing the same course, learning off, over **eight bags** (eight athletes practising on different days —
   see finding 7 for why one bag was not enough):

   | still air, 40 drawn courses × 8 bags | pin ±6 ft | pin ±14 ft | pin ±19 ft |
   |---|---|---|---|
   | aiming at the pin, minus aiming where the putt is likeliest | −0.20 ± 0.53 | +0.34 ± 0.95 | **+1.48 ± 0.67** |
   | aiming at the middle, minus aiming where the putt is likeliest | −0.19 ± 0.19 | −0.09 ± 0.17 | +0.05 ± 0.17 |

   Negative means pin-hunting wins. On a nine with the flags near the middle it is right to shoot at them, by
   two tenths of a stroke inside the noise; at fourteen feet of pin offset the two are the same shot as each
   other and better than the middle; on a tucked-pin day the decision is worth about a stroke and a half a
   round. **This table read −0.42 / +0.78 / +2.50 when it was measured on one athlete whose sigma was wrong,
   and the shape of it was right anyway** — the repair in pass 8 halved the tucked-pin figure and doubled its
   bar, and left the story standing. The hole split at ±19 says the tuck is the thing: with no sand at all,
   aiming at a pin cut 8 ft or further out costs **+0.43 ± 0.08** (t 11).

4. **With the wind on, the same decision goes slightly backwards — and last night's twenty-stroke reversal was
   an artifact of my own pin table.** Drawn pins at ±19 with drawn wind, eight bags: **−0.32 ± 0.31**, so the
   pin wins by a third of a stroke; and the reason is the one the rest of this file keeps arriving at. The reason is mechanical and worth stating, because it is the most useful sentence in this
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
   noise. With the wind drawn, ±19 gives −0.05 ± 0.67 and the fourth finding's null stands again.

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

   **And none of it reaches the card.** Six arms, believing between 0.6° and 3.0°, twenty-four rounds each:
   879, 879, 879, 882, 882, 894 strokes. `target()` floors the scatter at 2 ft, and 2 ft is where sigma stops
   — inside 76 ft the belief is not used at all, and beyond it the aim moves a couple of feet. The aim on a
   short approach is set by **a rule I typed**, not by what the athlete has learned about its hands. That is
   the honest state of the target decision, and it is the first item in "what this does not model".

   **One methodological correction came out of the same turn.** Re-running the aiming table with a fifth
   practice round flipped the sign of the tucked-pin result (+0.68 one way, −0.60 the other) with the hands and
   the belief almost identical: the paired design cancels the course, not the notebook, and the notebook is
   what the aim is drawn on. `--bags N` now trains N athletes on different practice sessions and puts the
   spread across bags in the error bar. Every number in finding 3 and 4 above is that version, and none of
   them was before.

## What this does not model

- **the target decision is a rule, not a skill, inside 76 ft.** `target()` floors the scatter at 2 ft, and an
  honest sigma (0.9–1.1°) is below that floor at every approach range in the game, so the aim is set by the
  floor. That is why six arms believing anything from 0.6° to 3.0° finish within three strokes of each other.
  Removing the floor is the next measurement, not part of this one: doing both in a turn is how a person talks
  himself into a number
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

   | still air, ±14 ft, 8 rounds (par 280) | R1 | R4 | R8 | total | change |
   |---|---|---|---|---|---|
   | cautious (middle of the green) | +7 | +2 | +1 | **+32** | −6 |
   | practiser | +7 | +1 | +3 | +34 | −4 |
   | bad start (worse prior on the bag) | +9 | +3 | +1 | +35 | −8 |
   | flag-hunter | +7 | +7 | +0 | +37 | −7 |
   | blind hands (told a scatter it does not have) | +9 | +1 | +4 | +41 | −5 |
   | no practice (frozen) | +11 | +13 | +16 | **+102** | +5 |

   Every learner gains four to eight strokes over eight rounds; the frozen player loses five and finishes
   sixty-eight strokes behind. **The order among the five learners is inside the noise** and should not be
   read: on eight rounds of a nine-hole course, four of them are the same golfer. What the card shows is the
   distance between learning and not learning, which is the whole claim, and it shows it as a curve rather
   than a table. (Re-run in pass 8 with the honest sigma; "blind hands" was taught 1.5°, which the repair
   shows is the wrong number — the hands are 1.1° — so that arm is no longer a control but a player who has
   been told it is wilder than it is, and it finishes last of the five.)

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
   the sixth pass saw doubling was the flag-frame artefact of finding 7, not the wind. **And the card does not
   move:** all four arms finish within three strokes of each other over twenty-four rounds, because the target
   decision floors the scatter at 2 ft and 2 ft is where sigma stops. A player's opinion of its own hands
   turns out to be a number the game asks for and does not use.

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

4. **The floor, removed.** `target()` stops the scatter at 2 ft, and 2 ft is above the athlete's honest sigma
   at every approach range in the game — so the target decision is a constant, not a skill, and eight arms
   from 0.6° to 3.0° finish within three strokes of each other. Measured with the floor at 0.5 ft, the same
   table asks a different question: not "does the pin matter" but "does anything the athlete learns about its
   own hands matter". That is one number in the file and one re-run, and it is not in this pass because doing
   it here would have changed two things at once.

5. **A dogleg.** The driver's distance has never been a decision, because the corridor is straight and 40 yd
   wide. A corner with trees inside turns "hit it as far as you can" into a question with a number on it — and
   it is still geometry.

Nothing here needs anybody's hands. The one thing this game cannot do itself is put *another member's* number
on the board: that happens in their windows, on their turns, and nobody — least of all the founder — can order
it.
