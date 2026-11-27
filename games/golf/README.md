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
The first is built, the second is measured and named. Twelfth: the second built too — the putter now decides
how far past the cup to aim from what it has learned about its own scatter — and two more instruments found
reading the wrong thing, one of which had been making the cost table measure the wrong distance for two
passes. **Thirteenth: the measured cost curve put into the objective, which is the first time this game has
had a target decision in the short game — and a fourth instrument found reading the wrong thing, the same cost
table again, this time read as a curve when its sample changed with distance. It also found what the green's
new prices cannot reach: at approach range a landing is priced by its distance to the pin, and a ball struck
from 150 yd is 450 ft from the pin wherever it lands, so the objective's only gradient out there is still the
sand — and it thinks the sand is reachable four times as often as the game makes it. Fourteenth: the season on a
page. **Fifteenth: the film's camera — two of them thrown away before the picture read, and a ball that used to stop
where it stopped flying rather than where the game says it stopped rolling. Sixteenth: the putts in the film, traced
by the roll itself, filmed from above — and two checks that exist to stop the picture and the card from drifting
apart. Seventeenth: one door, a manual for a beta tester, and the bars made a rule in code rather than a promise in
prose. Eighteenth: the cup as a volume and a ball that falls into it — which is how the ball turned out to have been
drawn at twice its size since the first version.** Nineteenth: the premise this file has carried since the
thirteenth pass — that the objective is four times too frightened of sand because its landing has no depth —
is measured and it is not true; and the pass that went looking for the real missing dimension found the
measured green curve wired to the length of the shot instead of the length of the putt, so no club shot in the
game had ever read it. The landing has a depth now, learned off the athlete's own misses on the entries it has
hit; it is calibrated, it makes the sand's flank matter for the first time in six passes, and over 1,080 holes
it moves the card by nothing. The tool is
`lab/golf.py`; the runs are `records/golf-2026-11-19.txt`; the checks are `python3 lab/golf.py --selftest`
(the count prints itself).

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
    python3 lab/golf.py --season           # six athletes over eight rounds, as a page: the card, what each one
                                           #    believes about itself, and a band from four practice sessions
    python3 lab/golf.py --costs            # what the short game costs from each distance and lie: the numbers
                                           #    `target()` is made of, played out, with the count and standard
                                           #    error of every cell. Flat in distance until pass 11 put hands on
                                           #    the putter; a measured curve since pass 12; the curve the
                                           #    objective reads since pass 13
    python3 lab/golf.py --selftest         # the numbers below, checked
    python3 lab/golf.py --start            # the door for a beta tester, from season.json: renders/start.html
    python3 lab/golf.py --render lip       # the film: three shots at the face, as a page to open in a browser
    python3 lab/golf.py --render 7         # one hole, filmed: the camera fits the shot and each hole opens still
    python3 lab/golf.py --render round     # the athlete's own card, all nine holes, as one film
    python3 lab/golf.py --render worst     # ...or the one hole that went worst (or `best`)
                                           #    the putts are in all of them, filmed from above

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
| **learning** | +6 | +1 | +1 | −2 | −2 | −2 | +2 | 14.3 → 1.5, 1.5 by the sixth |
| **control** | +9 | +9 | +9 | +9 | +9 | +9 | +7 | 36.7% flat |

| windy | 1 | 2 | 3 | 4 | 5 | 6 | held-out | notebook error |
|---|---|---|---|---|---|---|---|---|
| **learning** | +13 | +4 | +4 | −2 | +2 | +2 | 0 | 21.0 → 12.0, 12.0 by the sixth |
| **control** | +15 | +15 | +15 | +15 | +15 | +15 | +7 | 38.9% flat |

What the second pass printed from the same command was +16, +13, +10, +3, +5, +8 against a control of +13 all
the way; every learner in this file got four to eight strokes better when it stopped aiming by a rule. **Pass
11 re-ran both halves because the short game changed under them**, and the shape is the one this file has
always claimed: the learner starts within a stroke or two of the frozen player and finishes ten strokes ahead
in still air, thirteen in wind, and level on six holes it has never played.

**The windy control got five strokes worse in pass 13** (+10 a round to +15) and the learner did not (+8 to
+23 over six rounds, but its first round is unchanged at +13 and its best is +2). The reason is the objective
and it is worth stating: pass 13 made the aim follow a green whose cost falls with distance to the pin, and a
frozen player has a 2.2° hand bias and an unlearned crosswind, so its scatter is *not* centred where the
objective thinks it is aiming. Aiming at the pin is a good instruction for a player who knows its hands and a
bad one for a player who does not: on this nine, in wind, the same frozen athlete scores +14 aiming at the
flag, +10 at the middle and +15 where the objective says.

*to par over nine holes (par 35); held-out is six holes never played (par 22). Notebook error is |what the
notebook said| against |what the shot did|, over every shot in the round.*

Putts, still air: 20, 15, 18, 16, 16, 16 for the learner, 14 every round for the control; wind 18, 19, 17,
13, 16, 16.

*The wind table is the one that moved most in pass 12 — from +18 over six rounds to +8 — and the reason is
visible in its putt counts, which fall from 18-21 to 10-14 as the athlete learns: a putter that holes its
putts makes a windy round recoverable.*

### Twelve findings

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
3. **The target decision is worth a stroke on a tucked pin and nothing near the middle — and pass 13 found
   where it actually lives: in the short game, where this game had never had one.** Three policies, forty drawn
   courses per bag, every policy playing the same course, learning off, over **eight bags** (eight athletes
   practising on different days — see finding 7 for why one bag was not enough):

   | still air, 40 drawn courses × 8 bags | pin ±6 ft | pin ±14 ft | pin ±19 ft |
   |---|---|---|---|
   | aiming at the pin, minus aiming where the ball is cheapest to hole out from | +0.44 ± 0.57 | +0.43 ± 0.51 | **+1.15 ± 0.86** |
   | aiming at the middle, minus the same | +0.42 ± 0.49 | +1.32 ± 0.40 | **+1.62 ± 0.69** |

   On a nine with the flags near the middle all three are the same shot, inside the noise — and pass 13 changed
   ±6 from −0.20 to +0.44, which is the same nothing with a different sign. At fourteen feet of pin offset the
   pin-hunter is four tenths behind the belief and the caddie's middle is a stroke and a third behind. On a
   tucked-pin day the pin is a stroke and a fifth behind the belief and the middle is a stroke and two thirds
   behind. **The belief is worth a stroke on a tucked pin and nothing on a friendly one, and it is never worse
   than either crude rule.**

   The history, because this table has moved every pass and each move has a cause. It read −0.42 / +0.78 /
   +2.50 on one athlete whose sigma was wrong; the repair in pass 8 halved the tucked-pin figure and doubled
   its bar; the floor coming out in pass 9 put a quarter of a stroke back on it; pass 10 replaced the objective
   it is scored with and took a sixth (finding 9); pass 11 put hands and eyes on the putter and took the rest —
   the ±19 figure fell from +1.30 ± 0.67 to +0.48 ± 0.60, and ±14 from +0.75 ± 0.62 to −0.05 ± 0.80; pass 12
   gave the putter a pace, which put the stroke back (+1.05 ± 0.74 at ±19); **and pass 13 priced the green as a
   curve instead of a constant, which held it there (+1.15 ± 0.86).** That is the shape of the whole file: the
   aim is worth something exactly when the thing it aims at is worth something.

   **Where it is worth something is not where this file said it was.** Pass 13 put the measured cost curve into
   `target()`, and a curve is priced by a landing's *distance to the pin* — so it bites exactly as far as a shot
   is short. At approach range it is flat: a ball struck from 150 yd that finishes 8 ft from the flag is 450 ft
   from the flag, and the objective prices a 450 ft landing within a hundredth of a 460 ft one. Which means the
   approach-range decision is still made on the lie prices and the sand alone (see finding 12 for what the sand
   is worth to it), and the *short* game — chips, pitches, anything under about 60 ft — now has a target
   decision for the first time in this game's life:

   | chipping from, over 12 bearings × 3 streams, learning off | aim at the pin | aim at the middle | the objective's target |
   |---|---|---|---|
   | 30 ft, out of the rough | **2.00** | 2.60 | 2.00 |
   | 45 ft, out of the rough | **2.00** | 2.56 | 2.00 |

   Three quarters of a stroke at 30 ft, half a stroke at 45. It was there to be taken for ten passes and nobody
   took it because the green cost the same from four feet as from twenty: the objective aimed the chip at the
   middle of the grass, and aiming at the middle of the grass is `centre`. That is the same defect as finding
   11's, one layer up — the objective could not see a distance, and a chip is all distance.

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
   the middle in **both** weathers: −0.47 ± 0.71 still and −1.23 ± 0.53 windy. And taking the hands back off is
   a control that costs one line: the same forty courses, eight bags, ±19, still air, with `PUTT_FACE_SD` and
   `PUTT_SPEED_SD` set to zero, gives flag − centre **+1.32 ± 0.76** — the old reversal to the stroke. So it
   was not the wind and it was not the pin: it was a green on which every putt cost two strokes, which makes a
   middle aim free and a long putt free and leaves the sand as the only thing in the world with a price. Give
   the putter a dispersion and the middle aim starts paying for the twenty-five-foot putts it leaves (finding
   10): the middle goes from +0.17 ± 0.35 behind the belief to +1.62 ± 0.69 behind it. The reversal was the
   short game's, and it dissolves when the short game is real. Pass 13 put the measured curve underneath it and
   the reversal survived: the middle loses a stroke and a quarter to the belief in wind and half a stroke to it
   in still air, so the weather is still doing something this file can only name (finding 12).

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

   | 8 streams, pins ±14 ft, wind drawn, 2 courses to learn on, 4 rounds each | strokes/round | believes |
   |---|---|---|
   | told 0.6° | 34.69 ± 1.32 | 0.60° |
   | told 1.1° (the hands) | 36.38 ± 0.52 | 1.10° |
   | told 2.0° | 35.81 ± 0.96 | 2.00° |
   | ungated, learned | 35.94 ± 1.09 | 2.43° |
   | gated, learned | 36.25 ± 0.61 | 1.15° |
   | told 3.0° | 36.50 ± 0.83 | 3.00° |

   The table's own spread, paired by stream, is **1.81 ± 1.30 strokes a round** across a five-fold range of
   self-knowledge — nearly three times what it was in pass 11 (0.52 ± 0.27). **And pass 13 doubled every bar in
   this table**, from 0.2–0.6 to 0.5–1.3, which is worth more attention than the means: the aim is now the
   nearest point of a nearly flat band (finding 12), and a decision made on a hundredth of a stroke moves
   between streams when the athlete's aim moves at all. An unstable decision shows up as variance, and that is
   what the bars are.

   **And the awkward result of pass 9 is back, on a game that is now honest.** The sharpest belief wins: told
   0.6° finishes 1.68 of a stroke ahead of the 1.10° hands it actually has, which is 1.3 sigma of this table's
   own 1.30 bar — leaning, and leaning less than pass 12's 1.8 sigma, because the bar grew. Pass 10 made that anomaly go away by scoring in strokes; pass 12 brought it back by giving the
   putter a pace, so the explanation pass 10 offered ("the anomaly was the objective's") was at best half of
   it. What is left is uncomfortable and simple: in this game an athlete that *believes* it is accurate aims at
   the flag, and the flag is where the strokes are, so a flattering belief pays for itself at a rate the truth
   does not. Finding 11 is the pass that made that visible again and did not repair it.

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
   one direction that matters.** It was left unbuilt in pass 11 on purpose — it is a decision about *what to
   intend*, not a dispersion and not a read, and the two lessons of passes 9 and 10 are what an unmeasured
   intent costs. **Pass 12 built it: finding 11.**

   The honest part of the last row is this: with a pace that finishes 1 ft past, this game holes **more** putts
   than golf does at every distance from 6 ft out (60/43/29/17 against 50/30/15/7). The line error here is one
   constant of 1.1° that does not grow with distance, and a real golfer's does, because a real golfer misreads
   the green — and a read error is the one thing left that I would have to invent. So it is named and not
   built: **this game's short game, with the pace fixed, would be better than golf's, and the reason is that it
   reads greens perfectly.** That is the next lie the model would be telling itself.

11. **The pace is a decision, and once the putter made it the green cost what a green costs — and two instruments
   turned out to have been reading the wrong thing for two passes.** Pass 11 priced this and refused to build
   it: a putt that dies at the cup cannot go in, and aiming past the cup instead was worth 37 points at 3 ft and
   13 at 20. What was missing was not a number. It was that `putt.py`'s athlete carries two *means* — a pace gain
   and a line bias — and **no variances at all**, so it aims the way a player aims who is certain to hit the
   number it picks, and a player who hits the number exactly should die the ball at the cup. It does not hit the
   number exactly, so it should not, and how far past the cup it should aim is a function of **how badly it
   misses**, which it can only know if it has an opinion about its own scatter.

   So the putter has one now. Two numbers, learned from the same printed miss the two means are learned from —
   the lateral miss at a known distance is an angle, and the along miss is half a fraction of speed because a
   ball's roll goes as the square of its speed — starting at the clubs' own 1.1° and 1.5% because that is the
   only evidence a player has about its own hands before it has putted. Then it chooses its overshoot by
   maximising the two ways a scattered putt *fails*: stopping short of the plane (the ball never crosses the
   hole) against arriving faster than the 4.5 ft/s the hole accepts (pass 5's lip). Both terms are physics and
   the scatter is measured; there is no fitted constant in the decision.

   | what it chooses | 2 ft | 3 ft | 4 ft | 6 ft | 9 ft | 12 ft | 20 ft | 45 ft |
   |---|---|---|---|---|---|---|---|---|
   | aim past the cup (downhill line, a_eff 2.07) | 0.51 | 0.81 | 1.02 | 1.53 | 2.24 | 2.24 | 2.24 | 2.44 |
   | the same up the slope (a_eff 1.53) | 0.55 | 0.83 | 1.11 | 1.52 | 2.35 | 3.04 | 3.04 | 3.18 |

   | 3 ft and 20 ft putts, 240 draws each | holed |
   |---|---|
   | aiming past the cup (pass 12) | 84% / 23% |
   | aiming at it (pass 11) | 45% / **14%** |

   **And the green now costs what golf's greens cost**, which is the thing pass 10 went looking for and pass 11
   could not deliver:

   | strokes to hole out on the green, from d ft (measured around the green's centre, pass 13) | 2 | 3 | 4 | 6 | 9 | 12 | 16 | 20 |
   |---|---|---|---|---|---|---|---|---|
   | this game | 1.03 | 1.14 | 1.35 | 1.43 | 1.65 | 1.83 | 1.82 | 1.90 |
   | golf, roughly | 1.02 | 1.05 | 1.12 | 1.35 | 1.6 | 1.75 | 1.85 | 1.9 |

   *(Pass 24 re-measured this row with a putter that reads the green it plays and got 1.03 / 1.04 / 1.14 / 1.10 /
   1.31 / 1.49 / 1.65 / 1.74. **Pass 25 re-measured it again at 1.00 / 1.00 / 1.01 / 1.04 / 1.31 / 1.46 / 1.56 /
   1.67** and those are the numbers the objective is told now. See "What the twenty-fifth pass found".)*

   *(Pass 12 printed this table read around a flag cut 13 ft off-centre and read 1.00 / 1.21 / 1.23 / 1.54 /
   1.62 / 1.70 / 1.89 / 1.93. The numbers are the same to a tenth and the table was still wrong: past 20 ft the
   compass leaves a 40-ft green and the row keeps 27 of its 48 positions. Finding 12.)*

   **Two instruments were lying, and one of them explains why two passes could not see this curve even after the
   putter had the hands to produce it.** The cost table places a ball at a distance `d` from the green's *centre*
   and then reports `d` as the distance to the hole — but the pin is cut 13 ft off centre, so the row marked
   2.5 ft was a 13 ft putt and the row marked 28 ft was a 15 ft one. Every cell in a table that was supposed to be
   about distance was within a few feet of every other cell. It is measured from the flag now, and the column
   reads 1.00 to 1.93. And the check that prices the sand ran its forty trials on **one seed** — one trial,
   forty times — which is how it came to report the sand's price as a whole number. Both are the same species of
   error as pass 11's shared seed in the same function: an instrument that looks like it is averaging and is not.

   What it did to the cards, and two of them are uncomfortable:

   | | pass 11 | pass 12 | pass 13 |
   |---|---|---|---|
   | learner, still air, six rounds | +8 +7 0 0 −1 −1 | +6 +3 +4 +1 −2 −2 | **+6 +1 +1 −2 −2 −2** |
   | learner, wind drawn | +7 +1 +3 +3 +2 +2 | +13 +6 −3 −4 −2 −2 | **+13 +4 +4 −2 +2 +2** |
   | field, eight rounds, best learner | flag-hunter +39 | practiser +49 (**flag-hunter +77, last**) | **bad start +39**, practiser +46, flag-hunter +77 |
   | belief table, spread over a five-fold range | 0.52 ± 0.27 | 1.41 ± 0.64 | **1.81 ± 1.30** |

   The wind rounds get three strokes a round better and the field's `flag-hunter` — first in passes 10 and 11 —
   goes from +39 to +77 and last of the five learners. The frozen player does not move at all (+115 both times),
   so this is not a change in the game's difficulty; it is what happens when putting stops being free. The
   reading I would defend: **when a putt could not miss, a landing near the flag was worth nothing and the
   athlete that ignored the flag did not pay for it; now a putt can miss, and the policy that lives at the pin
   pays for every hole it is short-sided on.**

   The one thing that was still *priced for the old game* was the aim, and pass 13 is that pass: the green's
   2.00 was a constant standing in for a curve, and patching the two constants (as this paragraph proposed:
   `flag` −0.86 → −1.22, `spread` −1.92 → −2.10, `centre` −0.01 → −0.54 at ±19 before the run) was the cheap
   version. The curve did what the patch could not — it gave the short game a target decision worth three
   quarters of a stroke at 30 ft (finding 3) — and it moved the field's order a third time.

   And the lip, which pass 11 found dead, is still nearly dead: 0.2% of 45 ft putts lip out and none inside 12 ft,
   because the chosen overshoot keeps the arrival speed under the capture speed *by construction*. The decision
   trades lipouts away on purpose and the trade is right, but it means the bunker's face and the hole's lip —
   the same geometry — still only bite the chip.

12. **The green is a curve now, and a curve is priced by distance — so it reaches exactly as far as a shot is
   short, and not one yard further. Plus a fourth instrument reading the wrong thing, and the sand the objective
   can see and the game cannot.** `target()` is no longer told that a green costs 2.00 wherever the ball stops;
   it is told `green_cost(d)`, a measured curve from 1.00 at 2 ft to 1.67 at 20 (pass 25's row; 1.03 to 1.74
   when this finding was written), and it integrates the landing
   over half-foot cells rather than pricing the whole surface at one number.

   **The instrument, which is the fourth of these and the third in the same table.** Pass 12 fixed the cost table
   to measure from the flag, and read it as a curve: 1.89 at 20 ft, 1.76 at 24, 1.93 at 33. That wobble was not
   the green. A compass of radius d drawn around a flag cut 13 ft off-centre on a 40-ft green is not inside the
   green for long: at 20 ft it keeps 27 of its 48 positions, at 24 ft 21, and **every position it loses is on the
   same side of the green** — so the row is not "the green at 24 ft", it is "the back half of the green at 24
   ft", and a curve read off it is the sample changing with distance. Measured around the green's centre, where
   every bearing is inside the grass out to the inscribed 20 ft, the curve is monotone and clean, and the extra
   sampling error is what made the pattern visible: every cell now prints its count and its standard error, 0.02
   to 0.08 of a stroke.

   The knots are that table to the last digit — no smoothing, no fitting, because a curve fitted to the same
   table a check later reads back is two fitted numbers wearing a lab coat. Three things are stated instead of
   smoothed: the 16 ft knot is the 12 ft knot's 1.83 (the run measured 1.82, and a cost that falls with distance
   is not something a normal curve does); the curve is held flat past 20 ft, where it cannot be measured cleanly
   on this green and golf is about 2.0; and check 35 reads it at 5 ft and 14 ft, between the knots, so what it
   tests is the interpolation rather than the numbers it was typed from.

   **Its first version had a bug worth keeping.** The landing is integrated over a window five deviations wide,
   and for a target thrown wide of the green the window falls off the end of the modelled turf: no cells, value
   0.00, and a free target at ±45 ft. Every ball in the rough then aimed as wide as possible and `--costs` came
   back reading **8.10 strokes off the green** where it had read 2.25. The mass the window does not cover is
   charged the rough's price now — an empty window is not a cheap target — and the bug is the reason to run the
   instruments after every change rather than the checks alone: the selftest was green for several minutes while
   the game was unplayable.

   **What the curve cannot reach.** A landing is priced by its distance *to the pin*, so the curve bites only
   while the shot is short. A ball struck from 150 yd that finishes 8 ft from the flag is 450 ft from the flag:
   the objective prices it within a hundredth of a stroke of one that finishes 20 ft away. So the approach-range
   decision is where it was — made on the lie prices and the sand — and the target decision has moved to the
   short game, where it is worth three quarters of a stroke at 30 ft and half a stroke at 45 (finding 3). Both
   halves of that are the same sentence: **the objective's gradient in distance is real now, and it is only as
   long as a chip.**

   *Pass 19: this paragraph was not describing a limit of the model, it was describing a bug in one line of it.
   A ball that finishes 8 ft from the flag is not 450 ft from it — the landing arrives at the flag's distance,
   so the putt it leaves is the lateral distance and nothing else. `d_pin = math.hypot(dist_ft, mid - pin)` read
   the length of the shot as the length of the putt, which made every cell on the green cost the same 1.90 and
   left the whole measured curve unread outside seven yards. It is `abs(mid - hole.pin)` now and the landing has
   a depth as well; see "The landing gets a depth, and the sand stops being the story". The sentence above that
   it is "only as long as a chip" was true for six passes and was the bug.*

   **And the sand the objective can see is four times the sand the game has.** At a pin cut 19 ft out with the
   bunker starting at 20, the objective prices aiming at the pin 0.70 of a stroke worse than aiming away from it
   — P(in the sand) is 42% of its landing distribution. Played out over 3 bags × 12 courses, the card pays
   **+0.08** for the safe aim. Check 21 measures the other end of the same gap: 11.6% of approaches to a tucked
   pin finish in the bunker. The objective has no *along* dimension — its landing always arrives at the pin's
   distance, so the sand is always in reach — and that is why the sand has never made this decision directional
   in four passes of trying. It needs a second dimension, not another price.

   *Pass 19: the paragraph above is wrong, and it is the paragraph the nineteenth pass was sent to build on. The
   42% is real and it is the chance for a shot aimed at the pin — the game's own shots at that same aim find the
   sand 47.5% of the time, so the objective is the optimist's, not the pessimist's. The 11.6% was every shot in a
   round, drives included: a denominator, not a disagreement. The second dimension was built anyway, for the
   reason the next sentence in the last paragraph gives, and it moves the card by nothing measurable.*

   **Direction is the other half of the same defect, and it is bigger than the thing this pass fixed.** A 12 ft
   putt costs **1.50** from above the hole and **2.17** across the fall line — 0.67 of a stroke, which is most of
   the 0.87 the whole 2-to-20-ft gradient is worth — and `target()` prices every 12 ft landing at 1.83, the
   average. The objective's scatter is lateral only, so it never knows which way the ball will be putting. At
   20 ft the split is 1.72 against 2.11. This is measured, it is the largest error left in the objective, and it
   is item 6 below.

   *Pass 20: the measurement holds and the sentence does not. The break is real — 0.45 ± 0.07 of a stroke pooled
   over six distances — and it is worth nothing to an objective that chooses a lateral target, because the
   athlete's landing is as likely short as long and the break is the same putt at both ends. The objective is
   right to price the mean curve. What the table also found is that the *downhill* putt costs this game nothing,
   0.02 ± 0.03, which is the defect underneath the "1.50 from above the hole" this paragraph quotes: there is no
   such thing in the game. See "The break is real, and the objective is right to ignore it" below.*

   *Pass 24: the measurement above is withdrawn. Half of it was the putter — the 1.50 from above the hole, the
   2.17 across the fall line and the 0.45 pooled over six distances were all measured with a putter that paced
   its aim while the ball rolled its read, and read a putt that ran past the hole where it stopped. Re-measured,
   both terms are zero: −0.01 ± 0.05 for the break and −0.01 ± 0.02 for the downhill. The sentence that survives
   is the one about the objective: a direction term is still worth nothing to it, and now it is worth nothing
   twice over, because the game has no direction term to sell.*

   *Pass 25: **+0.00 ± 0.00** for both, and the zero is now exact rather than small. The break is free because the
   read corrects to the centre of the hole to a hundredth of a foot; the downhill is free because `green_cost` is
   a bearing average and the overshoot a pace error produces is the same distance whichever way the green falls.
   Selling "keep it below the hole" needs the comeback's speed in the price, and that is a second dimension of the
   green rather than a term in this one.*

   **What it did to the cards.** The learner's still-air rounds improve (+6 +1 +1 −2 −2 −2, held-out +2 against
   a frozen player at +9), the wind rounds do not (+13 +4 +4 −2 +2 +2), and the field changes order for the
   third time: `bad start` +39 leads, `practiser` +46, `blind hands` +71, `flag-hunter` +77, frozen +111. Two
   things are worth naming in that and neither flatters the pass:

   - **The windy *control* got five strokes a round worse** (+10 to +15, with the frozen player's total moving
     only 4 across eight field rounds). On the fixed nine, in wind, the same frozen athlete scores +14 aiming at
     the flag, +10 at the middle and +15 where the objective says. A player that does not know its hands has a
     2.2° face bias and an unlearned crosswind, so its scatter is not centred where the objective believes it is
     aiming: **the objective's advice is good advice for a player who has measured itself and bad advice for one
     who has not.** That is the honest version of "aim at the flag is right".
   - **The sigma table's bars doubled** (0.2–0.6 to 0.5–1.3) without its means moving much. The aim is now the
     nearest point of a nearly flat band (below), so it flips between streams when the athlete's estimate moves
     at all, and a decision made on a hundredth of a stroke shows up as variance. I am reading the bars as the
     finding rather than as an annoyance.

   **And the wide belief, which this file has described wrongly for four passes.** At 3.0° and 400 yd the
   objective is flat to 0.02 of a stroke across **62–63 ft** of aim, and aiming at the pin costs it 0.01 of a
   stroke. It is not that a wide belief aims at the room *because it cannot see distance*: it aims at the
   nearest point of a flat band, and the band's edge is where the sand starts. On the three holes with no bunker
   it aims at the pin, 4 to 12 ft away; on the six with one it aims 22 to 32 ft away. Pass 11's sentence — "the
   only gradient left is the green's edge" — was right about the consequence and wrong about the cause, and this
   is the pass that could finally ask the objective directly (`target().scores()` exists for that reason).

## The season, on a page

`python3 lab/golf.py --season` writes `renders/season.html` — one file, no script in it, opens from disk — and
`renders/season.json` beside it. Six athletes, eight rounds, a card, and three panels:

- **what practice was worth**, as strokes against the frozen player in the same round. Every athlete meets the same
  course and the same wind in a round, so the difference cancels the weather and leaves the notebook: the plot is
  the paired design the aiming tables use, applied to a card. The frozen player is the flat line at zero by
  construction.
- **what each one believes about its own hands**, per round, against the 1.10° it actually has and the 1.50° it
  starts with. This is the panel the game exists for: a player that has measured itself converges on the truth,
  and the one that is *told* a scatter keeps it (finding 8's sore, on a screen).
- **what each one believes about its bag**, per round, as an error in per cent. A beginner is wrong by a third of
  the bag and a practised player gets under two.

The band on every panel is the spread across four practice sessions, because a season is one run and one run has no
error bar. It is drawn in the page rather than left to the reader: the width of that band *is* the claim about how
much of a card is the player and how much is the day. The page says, in its own footer, that these are six
strategies and not six people, and where the game stops.

## The round, as a film

`python3 lab/golf.py --render round` writes `renders/round.html`: the athlete's own nine holes, played back in
order, with three seconds of the hole standing still before each one. `--render best` and `--render worst` write
`renders/best-hole.html` and `renders/worst-hole.html` — one hole each, chosen off the card, which is the thing a
player actually wants to watch.

**The putts are in it as of pass 16**, and as of pass 18 the ball drops into the cup, which is the frame the whole
film was built to get to. `putt.roll()` traces its own
roll when asked — a putt reports the distance it finished from the hole and, until this pass, nothing about the
line it took, so the film had been saying in its own note that the putts were not in it rather than drawing a line
nobody computed. Each putt is photographed from above, because a putt is the one stroke whose whole content is a
line on a surface: there is no height to read and no face to climb, so the camera goes high over the middle of the
line and the break is the widest thing in the frame. The cup stopped being a three-pixel symbol and takes its size
from the projection, because from twenty feet the cup is the subject of the shot.

Two defects came out of making it, and neither was a physics question.

- **the ball stopped where it stopped flying.** The integrator's path ends at the first touch of the ground, which
  is right for physics, and the film drew it as it was — so the caption said "65 yd" and the dot on the screen was
  twenty-five yards short of that, because the game counts the roll and the picture did not. `film_path()` extends
  the path through the bounce and the roll along the straight line `shot()` already computes, with the time
  constant deceleration takes. Found by looking at a still and asking why the dot was not at the end of its own arc.
- **resizing the window blanked the page.** Setting a canvas's width clears it, and the pinned still never runs
  again, so the film went black and stayed black. Found by taking screenshots with a longer virtual-time budget:
  the frame drew, the layout settled, the canvas cleared itself. The page had this fault from its first version.

**The cup was a painted disc and is now a socket** (pass 18): a cylinder 4.25 in across and 4 in deep, its far wall
drawn in eight segments, with the floor under it. Honest note: at the distance a putt is filmed from, the cup is
between four and eight pixels wide and **the wall does not read at all**. What reads is the ball: a putt the game says
went in now carries four inches of fall past the plane through the hole, and the ball fades as it drops, so the last
frame of a hole is a ball vanishing into a dark disc instead of a ball resting on top of one.

And that change found a defect nine passes old. `BALL_FT` was `1.62/12` — a diameter used as a radius — so **every
ball in this film had been drawn at twice its true size since the first version**. Nothing could have shown it: a ball
alone on grass has nothing to be compared with. It showed the instant a ball had to fit inside a hole, because the
drawn ball was wider than the drawn cup, and a ball wider than the hole reads as a ball resting on the hole rather
than falling into it. The constant is `BALL_R_FT = 0.07 ft` now, which is half of 1.68 in.

Two checks now stand under the picture, and they are the first checks in this file that are about the film rather
than the golf. **37** puts the card's number beside the line the film draws, for clubs and for putts, and demands
they agree — the twenty-five-yard disagreement above would have failed it. Its first form failed at two inches, and
the two inches were real: `film_path()` was taking the direction of the roll from the last two samples of the
flight, which are a fiftieth of a second apart at the moment of the bounce, and a bearing taken off those is not a
bearing. **38** asks whether the line is the green's or a ruler: on the 1.2% green the worst bow of a 9 or 19 ft
putt off its own straight chord is 0.56 ft, and on the same green flattened it is zero. Without that one, check 37
would pass for a film that drew straight lines between two correct points.

## The door and the manual

Twelve pages existed and no way in: a tester sent `renders/` would find six films and a season and no way to know
which to open or in what order. `python3 lab/golf.py --start` writes `start.html` — the door. It reads
`season.json` rather than recomputing anything, so its card is the season's own card, and it is where the honesty
question from 2026-11-20 finally got its answer in the form the founder pushed for:

- **the number carries its bar, by construction.** `_bar()` is the only function on that page that formats a mean
  and it cannot format one without a standard error. The rule is typographic, the precedent is the fund fact sheet,
  and the way to keep a rule like this is to make it unbreakable in code rather than to promise it in prose;
- **the defect list is one click below the product, not on its face.** `FOR-BETA.md` holds what is known wrong,
  dated, with the number that shows it, plus what a tester is asked to judge and what would count as a defect on my
  side. Precedent: release notes with a Known Issues section. A game that opens by listing its own errors reads as
  unfinished, which is the exact impression the list exists to avoid;
- **the three sentences on the door say what it is not.** No player input, no graphics of a commercial kind, six
  strategies rather than six people.

The claims in the paragraph under the card are *generated from the card*: how many learners are behind the frozen
player in round 1 and by how much, and how far ahead by the last round. A sentence with a number in it that was
typed by hand is a sentence that is wrong by the third re-run, and this file has spent enough passes on that
particular failure.

## In Kythe, which is where a beta tester will meet it

`start.html` is a door, and a door needs a street. The twentieth pass put golf on the **Play** tab of `ait.html` (the
page published as kythe.app), and the three things that had to be solved were not layout.

**It cannot be played there, so it is not offered as a game.** The athletes are `lab/golf.py`; a browser cannot run
Python, and a page that re-implemented the physics in JavaScript would be a second game with the numbers of the
first. The tab shows the record instead — `renders/season.json`, the same file `--start` reads — and six films.

**The films cannot be linked.** `lab/deploy_netlify.sh` publishes exactly one page (plus the auth function), so
`kythe.app/games/golf/renders/hole-7.html` is a 404, and GitHub serves an `.html` file from the contents API as
base64 text rather than rendering it. The only way to show a film is to read its bytes and hand them to a frame:
`iframe.srcdoc`, with `sandbox="allow-scripts"` and *no* `allow-same-origin`. The film keeps its own script — it is
a canvas and a rAF loop, and it plays — and it cannot touch the page that holds a person's token. A film is a file
from a repository; treating it as a stranger is the whole of the security argument, and `lab/page-check.mjs` asserts
the absence of `allow-same-origin` so it stays an argument rather than a hope.

**Whose numbers are these, and the press that makes them yours.** A circle is not given `games/golf/`, so before its
first press the page falls back to the public bench — `LindsayRidgeway/ai-tribe-bench`, read with no credential at
all — and says in words that these numbers are the *project's*. The fallback taught the page a defect of its own:
`gh()` sent `Authorization: Bearer ` with an empty token, and GitHub answers 401 to an empty credential, so a *public*
repository could not be read without one. Six lines of `gh()` had been carrying that since it was written.

That is a viewer, and the founder said so on 2026-11-26 in four questions ("is Kythe just capable of viewing status
about games that have already been played?"). Tennis, the game that tab was built for, is not a file its owner reads:
the page dispatches `season.yml`, a runner plays, and the record lands in the circle. Golf got the same machinery in
`golf.yml` — press **Play a season in this circle**, and `lab/golf.py --season --rounds 4 --bags 4 --seed <drawn>` runs
on the circle's own runner, writes `renders/` and commits it. Three consequences worth stating:

- **a new seed each press.** `--seed` was added for this and defaults to the bench's own, so the season committed in
  this repository is still the season `--season` has always written, to the byte (checked by diffing it after the
  change). Without it, every press would draw the same weather, play the same nine holes, and look broken;
- **no key, no model.** The six athletes are policies. A press costs a few minutes of runner time and nothing that can
  fail for an interesting reason — which is the difference between golf and tennis, and the honest shape of a game
  whose subject is a program's own uncertainty rather than a model's judgment;
- **it ships.** `lab/golf.py`, `lab/putt.py` (golf borrows the short game) and `golf.yml` are on the template's
  whitelist; `make_template.unshipped_imports()` is what catches a circle that gets the engine without the module it
  imports, and `unshipped_dispatches()` is what catches a page offering a button whose workflow a new circle has not
  got.

**And the press repairs the circles that came before it.** The first version of this told the owner to go and run
`lab/update_tribe.py --write`, which is the page handing its own work to the person who pressed the button; the founder
refused it on 2026-11-26 ("ideally you would automatically retrofit the circle and then proceed to play"). So the
press asks one cheap question — does this circle have the four files? — and if anything is missing it builds the
update plan the page already trusts (the template's manifest, blob shas, and the rule that a file edited in the circle
is never overwritten), narrows it to golf's four paths, writes them, says how many it added, and dispatches. A circle
that is already current is not touched and does not even read the template: one request to see it has them.

One of the four is not an ordinary file. GitHub refuses a write under `.github/workflows/` to a token that was not
granted the `workflow` permission at sign-in, and nothing a page can do grants that to itself. That path writes the
engine and the player, quotes GitHub's refusal, names the permission, and sends no run — because a run without its
workflow is a red X and a log line rather than a game.

The bar rule crossed over too. `bar()` in the page is `_bar()` in this file, arithmetic for arithmetic (standard
error is a 1.96th of half the interval), and it is the only thing on the page that formats a mean — which is how a
rule survives being ported into another language by somebody in a hurry.

## The landing gets a depth, and the sand stops being the story

The thirteenth pass wrote down that the objective's landing had no *along* dimension, and priced the defect:
the objective thinks a ball struck at a pin one foot from the sand finds the sand 42% of the time where the game
finds it 11.6%. Six passes later the statement was still there, marking time on the sand as the thing a second
dimension would fix. Pass 19 went to measure it before building it, and the statement does not survive.

**The 42% and the 11.6% are two different quantities.** 42% is real — 40.7% by the objective's own arithmetic —
but it is the chance for a shot *aimed at the pin*. The 11.6% was every shot in a round: drives, layups, chips,
all of them, on holes whose pin happened to be cut near sand. Held like for like, with the game's own shots at the
same aim, the objective is if anything the *optimist*: 40.5% against the game's 47.5% when both aim at the pin, and
0.6% against 2.5% when both aim away from it. The sand was never the defect. The number that made it look like a
defect was a denominator.

**What the search for the real defect found.** One line, two passes of the file's own history:

    d_pin = math.hypot(dist_ft, mid - hole.pin)      # pass 13 to pass 18

`dist_ft` is the distance the shot is being *hit from*. So the landing's putt was read as the length of the shot:
on a 150 yd approach every cell on the green was 450-odd feet from the pin, and `green_cost` is flat past 20 ft.
The measured curve — 1.00 at 2 ft rising to 1.67 at 20 (1.74 until pass 25 re-measured it, 1.90 until pass 24
did), the instrument the thirteenth pass built and the
thirty-fifth check verifies the wiring of — was read only by shots inside seven yards. Every club shot in six
passes treated every spot on the green as equally good, and the objective's only gradients out there were the
sand and the edge of the grass. That is why the target the objective chose was always about the middle of the
green, and it is a coincidence that it was the right target.

**Fixed, and it made the game worse.** With the curve readable, the objective started reaching for the pin — and
over 1,080 holes, paired by course and seed against the shipped version, the card got 0.041 of a stroke a hole
*worse*, because the objective cannot see the green's edge: the green is an ellipse, and a ball aimed at a pin cut
thirteen feet off-centre has twenty-one feet of depth to spare rather than twenty-eight, which is the thing that
makes a tucked pin hard.

**So the landing got its depth, and it is learned the way the width is.** `sigma` is learned from the athlete's
misses, across; `sig_dist` is learned from the same shots, along — how far past or short of its own notebook
number the ball finished, as a fraction of it, plus the mean of that (its notebook's own optimism). It is learned
only off entries the athlete has hit four times, for the reason the wind is guarded the same way: the first shot
at a cell reports the notebook's error, not the hands'. Ungated it reads 14% of the shot — a player who trusts its
own bag that little puts every target off the green, the aim stops being a decision, and the field's best athlete
lost seventeen strokes to it. Gated it reads 2.3%, and the hands on settled entries read 2.1% (check 40). The
objective now asks what a landing is worth *at the point it lands*: the ellipse, the sand's depth, the putt it
leaves, and the club's shortfall.

**What it bought, in the only currency the founder cares about.** On 1,080 holes played against the shipped
objective: **+0.007 ± 0.037 of a stroke a hole** — nothing. The depth's own share of that, fix-and-depth against
fix-alone, is **−0.033 ± 0.022** — three tenths of a stroke a round, and the interval excludes zero. On the season
page, four rounds x four practice sessions, the two learners that practise most gain 4.0 and 4.5 strokes and the
athlete that never learns loses 3.5, inside its own ±6.3 band. And the sand, which four passes of hazards could
not make directional, now reads +0.57 / −0.37 on twenty courses — and −0.27 / +0.00 on the same twenty courses in
the other configuration, which is this instrument's noise, so the record does not claim it.

The honest summary is the one the founder asked for in advance: **the shape moves the aim and barely moves the
card.** The second dimension is real, measured, calibrated and nearly free (the selftest goes from 48 s to 70 s),
and it is not where the strokes are. What it does establish is that the objective is now wrong in a place the
record can point at — from 150 yd it believes 95% of its shots hold the green where the game holds 53% — and that
the reason is not geometry. It is that half the game's misses are balls that never had the club: the gear ladder
is coarse, the athlete's prior is linear in effort and wrong (a 60% five-iron believes 117 yd and delivers 102,
and `choose()` is built to prefer exactly those partial gears), and its wind coefficient is imperfect. A normal
kernel cannot say that. The next thing to try is a mixture kernel — how often the club is wrong, and how far off
it is when it is — and it is written here rather than built, because a pass that has just measured its own
premise as false should not also invent one.

## The break was the putter's

**Pass 24 withdrew the measurement this section is built on, and the withdrawal is the finding.** What follows is
what pass 20 measured — the break at +0.45 ± 0.07 of a stroke, the downhill putt at +0.02 ± 0.03 — and those
numbers were the *putter's*, not the green's: it paced the line it aimed on while the ball rolled the line it read,
and it read a putt that ran past the hole where it stopped. Re-measured with a putter that reads the green it
actually plays, the break is **−0.01 ± 0.05** and the downhill putt **−0.01 ± 0.02**. The instrument in the
section below is the part that survived, so it is kept as it was written; the diagnosis and the new numbers are
under "What the twenty-fourth pass found" at the end of it. *(Pass 25 reads **+0.00 ± 0.00** for both: the read
now aims at the centre of the hole, and the price of a miss has no direction in this model.)*

The twenty-eighth item on the list was **direction**, and the record had called it "the largest thing left wrong
in the objective": a 12 ft putt costs 1.50 from above the hole and 2.17 across the fall line, `target()` prices
every 12 ft landing at 1.83, and the objective's scatter was lateral only. This pass measured it properly and then
declined to use it, and the reason is worth more than the term would have been.

**The instrument first.** Quadrant means are a bad instrument for a shape: a quadrant mixes sin²ψ 0.25, 0.85 and
1, where ψ is the angle between the putt and the fall line, and two distances cannot say whether the effect grows
with the putt. `--costs` now bands every bearing by sin²ψ (0 along the fall line, 1 square across it), at six
distances, 24 bearings × 3 streams each, and fits two terms together:

| distance | along | 0.15–0.5 | 0.5–0.85 | across | down the slope | across it |
|---|---|---|---|---|---|---|
| 3 ft | 1.00±0.00 | 1.11±0.08 | 1.22±0.10 | 1.22±0.10 | −0.01±0.06 | +0.28±0.11 |
| 6 ft | 1.11±0.08 | 1.56±0.12 | 1.50±0.12 | 1.56±0.12 | +0.01±0.08 | +0.38±0.16 |
| 9 ft | 1.44±0.12 | 1.56±0.15 | 1.67±0.11 | 1.94±0.15 | −0.04±0.09 | +0.50±0.19 |
| 12 ft | 1.39±0.12 | 1.72±0.14 | 2.00±0.16 | 2.22±0.13 | +0.08±0.10 | +0.80±0.20 |
| 16 ft | 1.50±0.12 | 1.83±0.15 | 1.89±0.11 | 2.06±0.15 | +0.13±0.09 | +0.48±0.19 |
| 20 ft | 1.56±0.12 | 1.83±0.09 | 2.17±0.17 | 2.06±0.13 | +0.01±0.09 | +0.63±0.18 |

Pooled over the six distances, which are six independent estimates of the same two numbers: **the break is
+0.45 ± 0.07 of a stroke** (χ² 6.6 on five, so one number and not a curve in distance), and **a putt running down
the slope costs +0.02 ± 0.03 more than one running up it** — that is, nothing. The direction is one number, the
break is five times the downhill term, and the distance curve the objective reads is exactly their mean: the four
bearings at 12 ft average 1.71 against the curve's 1.83, and the two rows straddle it.

**Then the arithmetic that makes it worthless here.** A landing at lateral offset *a* from the pin and depth *b*
has sin²ψ = (a+b)²/2(a²+b²); its mirror at depth −b has exactly 1 minus that. The athlete's depth is a normal
about a bias a twentieth of its own scatter, so the two landings are as likely as each other and the pair sums to
exactly 1. The depth average of the break is therefore ½ — the curve's own mean — **for every lateral cell**, and
a direction term in `_landing` adds the same number to every one of them. It is worth nothing to an objective that
chooses a lateral target: built as a candidate and wired in, it moved a 150 yd aim at a pin cut 13 ft right by no
feet and bought under a ten-thousandth of a stroke. What it would have spent is the athlete's 0.5% mis-estimate of
its own depth, not anything the green does.

**And then the defect underneath.** Why is the downhill term nothing, when "keep it below the hole" is the first
thing anybody is told about a green? Because this game's putter has no below-the-hole penalty: a downhill putt that
misses is priced by the length of its comeback and not by the fact that the comeback runs away. `GolfPutter.settle`
trades reaching the hole against arriving at capture speed and never prices the putt it leaves. Measured through
the game, downhill minus uphill at 3/6/9/12/16/20 ft reads 0.00, 0.00, −0.33±0.30, 0.00, −0.17±0.31, −0.17±0.31;
pooled −0.11 ± 0.10. So the game does not have the effect, and an objective that had been told about it would be
aiming for a profit that does not exist in its own physics. **The silence is right; the putter is wrong.** That is
the next object, one surface down, and the objective will need to be told the green on the day it is fixed.

The pass is therefore a finding and not a change: no aim moved, no card moved, and the committed season record is
byte-identical, which is the right evidence for a pass that concluded its own premise was false.

### What the twenty-fourth pass found: the pace was on the wrong line and the miss was read at the wrong place

The break did not get smaller because the green changed. It got smaller because the thing measuring it was broken,
and it was broken in a way that made a putt across the slope systematically harder than a putt along it — which is
exactly what "the break costs strokes" looks like from outside.

**The two errors.** `putt_read` asks the game's own roll for the face that puts the ball on the hole; the pace was
then computed by `pace(d, effective_decel(green, aim))`, the deceleration along the *aim*. On a breaking green the
ball does not travel the aim — it travels the read, up to 40° off it on a steep green — so the deceleration it
actually meets is a different number and the putt arrives at a different speed. The second error was in the read
itself: it measured the ball's **stopping place**. For a putt hit to die at the cup the stopping place and the
crossing point are the same point within an inch, which is why six passes never saw it; for a putt hit 2.6 ft past
the cup they are far apart, so the read was aiming the ball's *finishing place* at the hole.

Neither error is visible in a table of holed putts. Both are visible in a table of holed putts *by direction*: on
a 4.5% green the putter holed **0–2% at bearings 60–90 and 180–210 against 73% straight down the fall line**. A
distance table that says half a compass cannot be holed is not a fact about putting.

**The fix, in three parts, none of them a number I chose.** `putt_roll` now reports `cross`, the point at which
the path came nearest the hole, and everything that reads the *line* reads it there — the read, the card's phrase,
and the athlete's belief about its own hands. `putt_line_and_pace` solves the pace from the game's own roll: roll
it with the hole 100,000 ft away so a putt that would have dropped still reports where it stopped, measure how
far it went, and scale the speed by the square root of the ratio. Read and pace are then alternated **until neither
moves**, which replaced "two corrections" with a tolerance — two is enough on the 1.2% green this course plays and
not on a 4.5% one, where the same read left 1.9 ft.

**What it did to the green.** The green got 0.2 to 0.3 of a stroke cheaper past 6 ft, because a putter that hits
the pace it read and reads the green it is on is a better putter than one that does neither:

| strokes to hole out, from the green's centre | 2 | 3 | 4 | 6 | 9 | 12 | 16 | 20 |
|---|---|---|---|---|---|---|---|---|
| this game, pass 24 | 1.03±0.02 | 1.04±0.02 | 1.14±0.04 | 1.10±0.04 | 1.31±0.06 | 1.49±0.07 | 1.65±0.07 | 1.74±0.07 |
| golf, roughly | 1.02 | 1.05 | 1.12 | 1.35 | 1.60 | 1.75 | 1.85 | 1.90 |
| this game, pass 13–23 | 1.03 | 1.14 | 1.35 | 1.43 | 1.65 | 1.83 | 1.83 | 1.90 |

The objective's knots were that row to the last digit (with the 6 ft knot held at the 4 ft one, because a cost
that falls with distance is not a thing a curve does and the 0.04 is inside a cell's own error). **Superseded by
the next section: pass 25 re-measured the green at 1.00 / 1.00 / 1.01 / 1.04 / 1.31 / 1.46 / 1.56 / 1.67.** It is golf's curve at
3 ft and cheaper than golf's everywhere past it, by 0.23 at 20 ft, and the gap is *named* rather than tuned: this
putter is never wrong about the green and never mis-hits the pace it read, so it pays for neither a misread nor a
mishit. **That is the next defect, and it is visible in the direction terms.**

**Both direction terms are zero and they are zero for different reasons.** The break costs nothing because this
athlete reads it exactly: `putt_read` runs to a hundredth of a foot, so a putt square across the slope is no
harder for it than one along it. A reader who cannot misread the green is not taxed by a green, and nothing in
this game gives it one to misread — the break is a *visual* fact here and not a price. The downhill putt costs
nothing because nothing prices the putt it leaves: `GolfPutter.settle` trades reaching the hole against arriving at
capture speed and never prices the comeback, so it aims as far past the cup as the hole will accept — **0.8 ft from
3 ft, 1.6 from 6, 2.6 from 12** (measured). In golf "keep it below the hole" is the first thing anybody is told
about a green; here it is worth 0.00. The principled form of that missing term is a one-step lookahead,
`1 + P(miss) · E[green_cost(what it leaves)]`, which prices the comeback, the downhill and the long overshoot in
one line. That is the next object. *(Pass 25 built it, and the aim came back to 0.3 / 0.6 / 1.1 / 1.8 ft at
3 / 6 / 12 / 20. The downhill is still worth nothing, for the reason this paragraph gives: the term prices the
*length* of the comeback, and `green_cost` is the same curve up the slope and down it.)*

**And the athlete was learning the wrong number, one layer up.** `feel()` was fed the miss at the *stopping
place*, so on a breaking green it learned the green's curl as its own hand error — it believed **3.9° of face for
hands with 1.1°** — and a *holed* putt reported its pace residual as if the ball had stopped short by the
overshoot, so a putter that holed more putts learned to hit them harder: **a 13% over-hit**, which is why it holed
30% of 20 ft putts where golf holes 15%. Both are censoring, and both are now handled: the pace residual is a real
roll and a made putt teaches nothing about it, and the scatter it believes (which governs how far past the cup it
aims) is learned only off putts whose pace was its own. It now believes a gain of 1.020 against a truth of 1.000
and a speed scatter of 0.027 against hands of 0.015 — still high, because the lever it divides out is oscillating
by a per cent. Its *face* belief stays at 2.8° against 1.1°, and that one is left as a stated defect: a putt is
only shown to it if it missed, and a miss at 3 ft is a putt that passed two inches wide, so the sample is the tail
of its own distribution. Nothing in the game corrects a censored sample yet.

**Two things the pass had to pay for, and both were caught by an instrument rather than by me.** The objective's
cost curve moved, so every target it prices now is priced differently, and the card moved with it. And
`COST_OFF_GREEN` — 2.60 since pass 10, on the rule that a constant re-measured and then checked against its own
measurement is a fitted number — had to come down to 2.38, because the green got cheaper and the *card* caught the
consequence: with the constant at 2.60, aiming at a tucked pin paid **1.11 ± 0.55 better** than aiming away from
it, where the objective says it costs 0.58. At 2.38 the contradiction goes (+0.03 ± 0.48). That is a second
instrument that never measured a rough's cost, and `--costs` reads 2.23 / 2.19 / 2.71 at 36 / 48 / 60 ft, so 2.38
is also that table's own midpoint. *(Pass 25 reopened it with the green at 2.38: the same card now reads
−0.97 ± 0.51 for that pin. The constant was not re-fitted — it is still 2.38 and still the second instrument's
midpoint — because a card reading that has moved 1.9 strokes on a green that moved by 0.08 is evidence that
something else is missing, not that 2.38 is wrong. See check 24.)*

**The card.** Four rounds of nine, par 35, four practice sessions, the band the spread across them:

| athlete | aims at | strokes | ± | to par | was (pass 23) |
|---|---|---|---|---|---|
| flag-hunter | flag | 154.2 | 2.2 | +14.2 | +40.8 |
| blind hands | spread | 154.8 | 6.1 | +14.8 | +31.0 |
| bad start | spread | 160.5 | 4.3 | +20.5 | +32.0 |
| cautious | centre | 160.8 | 7.3 | +20.8 | +36.0 |
| practiser | spread | 161.0 | 3.5 | +21.0 | +28.5 |
| no practice | spread | 190.0 | 7.9 | +50.0 | +58.8 |

Every athlete got better and the frozen player got better by least in relative terms, which is the improvement
claim intact. What changed is *which* player is best: the flag-hunter now leads, from last of the five. That is a
consequence of the two repairs and not a preference — with the green cheaper at long range and the rough no
longer over-priced by a fifth of a stroke, being aggressive stopped being the expensive policy. A game whose
target decision flips when the prices are corrected is a game whose target decision is real.

**What the pass did not do.** No aim moved because of the *direction* terms: check 40's cancellation still holds
to the ninth decimal, and the objective is still told the mean curve on purpose. The break being zero does not
make a direction term useful; it makes the case for one *vacuous twice over* — the objective cannot spend it, and
the game no longer has it.

### What the twenty-fifth pass found: the pace was priced and the read was stopping at the rim

Pass 24 left one defect in the short game named and unbuilt: `GolfPutter.settle` maximised the chance of holing a
putt and priced nothing that happened when it did not. The form it needed was written down as a one-step
lookahead, `1 + P(miss) · E[green_cost(what it leaves)]`. That is what this pass built, and it is worth about a
fortieth of a stroke — which is the first honest thing to say about it, and the second thing is that the pass
found something else that was worth twice as much.

**The pace.** The decision is now an expected-strokes minimisation. Three ways to fail, priced together: stop
short of the plane (the ball is left `-r` from the hole), arrive too fast for the rim to take it (4.5 ft/s), or
miss the hole sideways (`HOLE_R` against `d·tan(face_sd)`). The along axis is integrated over the athlete's own
learned pace scatter — a roll goes as the square of the speed, so `roll = (d+p)(1+e)²` — with the plane and the
capture speed as *split points* of the quadrature rather than corners it has to find. The sideways axis is closed
by the rim's own odds and the root-mean-square distance it leaves; check 46 integrates that axis too and the two
choose the same aim to a thousandth of a foot and the same price to a ten-thousandth of a stroke, so the closure
is not an approximation anybody can see. Nothing in it is fitted: the scatter is learned, the cost curve is
measured, and the search is a grid plus a golden section to three decimals.

The aim came back. Pass 24 aimed as far past the cup as the rim would accept, because a putt that lips out is a
putt that was going in; a player who counts the comeback does not:

| distance | 3 ft | 6 ft | 12 ft | 20 ft |
|---|---|---|---|---|
| pass 24's aim (best chance of holing) | 0.81 | 1.53 | 2.24 | 2.24 |
| pass 25's aim (cheapest leave) | 0.31 | 0.61 | 1.14 | 1.76 |

Where the cost is flat — and inside three feet it is, because the green there is nearly free — the athlete takes
the **least** pace that is as cheap as the best, to within a thousandth of a stroke. That threshold is stated
rather than picked: it is below what this game can resolve the green to at all, since the curve's own knots carry
standard errors of 0.02 to 0.06.

**What the term did not buy: the downhill.** In golf "keep it below the hole" is the first thing anybody is told
about a green, and the reason is that a downhill miss is coming back at you. That reason is a *speed*, and this
green's price is a distance: `green_cost` is measured over a whole compass from the green's centre, so it is one
curve uphill and down. The overshoot itself is direction-free here as well, because the pace is chosen as a
distance and the hand's error is a fraction of speed, so a 1.5% fast putt runs 3% long on any grade. Both
direction terms are therefore still zero — and `--costs` now reads **+0.00 ± 0.00** pooled for the break and
**+0.00 ± 0.00** for downhill-minus-uphill, which is a cleaner zero than pass 24's −0.01 ± 0.05 for a better
reason: it is not that the term is small, it is that the quantity it would spend is not in the model. Selling it
needs the comeback's speed in the price, which is a second dimension of the green.

**The find: the read was aiming at the rim, not at the hole.** `putt_read` corrected the face until its trial
putt was on the hole — and stopped the moment that trial putt finished *anywhere inside the rim*, on the sound
principle that a made putt is on the line. The principle is wrong by a rim radius: the line it returned was
anywhere across the 0.18 ft hole, so the ball crossed on the edge of the cup and a 1.1° hand error tipped it out.
Measured: a 3 ft putt went in **91%** of the time; correcting to the *centre* — which is what a player does, and
which costs nothing — makes it **99%**, and the crossing at 3, 6, 12 and 20 ft is now within 0.0085 ft of the
centre against 0.18 before. It is worth **0.08 of a stroke at 6 ft**.

Pass 24's own check could not see it, and that is the part worth writing down: check 42 asserted that the crossing
was inside a rim, and the rim was exactly where the loop had stopped. A check whose bound is the stopping rule
measures the stopping rule. Check 44 asserts the crossing within two hundredths of a foot instead.

**And the stopping rule one layer out.** The alternation between read and pace stopped when neither moved more
than 1e-3 — a rule pass 24 chose when the putt was aimed 2.2 ft past the cup. Pass 25 aims 1.1, a slower putt
breaks more, and on a 3% green 1e-3 left the line 0.26 ft off the hole: the stopping rule's own size. At 1e-6 the
same putt reads to 0.16 ft and the course green costs no measurable time.

**The green, which is now cheap inside six feet and further from golf than it has ever been.**

| strokes to hole out, from the green's centre | 2 | 3 | 4 | 6 | 9 | 12 | 16 | 20 |
|---|---|---|---|---|---|---|---|---|
| this game, pass 25 | 1.00±0.00 | 1.00±0.00 | 1.01±0.01 | 1.04±0.02 | 1.31±0.06 | 1.46±0.06 | 1.56±0.06 | 1.67±0.06 |
| this game, pass 24 | 1.03 | 1.04 | 1.14 | 1.10 | 1.31 | 1.49 | 1.65 | 1.74 |
| golf, roughly | 1.02 | 1.05 | 1.12 | 1.35 | 1.60 | 1.75 | 1.85 | 1.90 |

Two of those numbers are at the curve's floor and said so: all 72 positions from 2 ft and from 3 ft were holed,
so 1.00 there is a certainty and not a measurement. The objective's knots are the row to the last digit.

The gap to golf is now the **missing misread** and nothing else. A player with 1.1° of face, 1.5% of pace and a
perfect read of the green holes 90% of 6-footers; golf holes about 70%. Pass 24's probe measured what a misread
would be worth by scaling the read: half the break takes the curve to 1.03 / 1.21 / 1.39 / 1.67 / 1.96 at
2 / 4 / 6 / 12 / 20 ft against golf's 1.02 / 1.12 / 1.35 / 1.75 / 1.90, and the holed rates to 85 / 60 / 27 /
13%. That is the next object and it is the largest one left.

**The card moved again, and the leader changed again.**

| athlete | aims at | strokes | ± | to par | was (pass 24) |
|---|---|---|---|---|---|
| practiser | spread | 152.2 | 5.0 | +12.2 | +21.0 |
| blind hands | spread | 152.8 | 3.3 | +12.8 | +14.8 |
| flag-hunter | flag | 154.0 | 10.8 | +14.0 | +14.2 |
| cautious | centre | 156.5 | 7.4 | +16.5 | +20.8 |
| bad start | spread | 156.5 | 2.3 | +16.5 | +20.5 |
| no practice | spread | 191.2 | 4.6 | +51.2 | +50.0 |

The practiser now leads and the flag-hunter is third, from first, and the frozen player is where it was. Three
passes, three different leaders — which is what a card with bars of this width should do (flag-hunter's is ±10.8),
and the claim that survives is the one the game is for: every practised player is 12 to 16 strokes a round ahead
of the one that never practises, and that gap is 39 strokes, four times the widest bar on the page.

**A contradiction opened and is left open.** The green's knots moved by 0.03 to 0.08 of a stroke and the card's
verdict on a tucked pin moved by **1.9 strokes a round, the other way**: pass 24 read +0.94 for the safe aim on a
pinned-in pin against the objective's +0.56 price, and pass 25 reads −0.97 ± 0.51 against the same 0.56. The
objective's own gradient in distance barely moved (12 ft costs 1.46, 2 ft 1.00 — a gap of 0.46, as before), so the
arithmetic says that card should have moved by a tenth of a stroke and it moved by nineteen tenths. Something is
missing from `scores()` and this pass did not find out what: the candidates are named in the check. Check 24 is
now the record of the contradiction rather than a confirmation of the price, which is the same arrangement as
check 37 — the record cannot quietly go back to agreeing.

**What the pass did not do.** No misread (the largest item, measured above); no correction for the censored face
belief; no mixture kernel for the club that never had the shot; the downhill unbuilt and now for a reason that is
stated. The shared tree bites: this pass began in a worktree, as pass 24 ended by promising.


## What this does not model

- **the landing has two dimensions and only one of them is modelled well.** `target()` now prices the landing at
  the point it lands — lateral position against an ellipse, and depth as a learned normal about the athlete's own
  notebook bias — so the sand's flank and the green's edge are both in the arithmetic. What it still cannot say is
  that a ball sometimes does not have the club: the model puts 95% of its approach shots on the green from 150 yd
  where the game holds 53%, and a normal wide enough to carry the real misses makes the objective fatalistic (see
  the section above). A mixture kernel is the next thing, not the next pass. Direction is *not* missing any more,
  and it is not missed: the break cancels exactly against a landing that is as likely short as long, so the
  objective's mean curve is the right answer (pass 20) — and since pass 24 the game does not have a break to
  price either (**+0.00 ± 0.00** since pass 25), because the athlete reads the green exactly — and, since pass 25,
  reads it to the *centre* of the hole rather than anywhere inside the rim. **The read error is the missing
  thing**: a putter that never misreads a green is not taxed by one, and that is why this game's green is 0.23 of
  a stroke cheaper than golf's at 20 ft
- **the putting stroke has one shape.** `putt.py`'s athlete models a pace gain and a line bias, and the game
  has added the clubs' two dispersions (pass 11) and a pace the athlete decides (pass 12) — but a real putter
  also has a stroke that is not a straight line: no arc, no clubface rotation through impact, no strike low or
  high on the face. What that would add is a dispersion that grows with the length of the stroke rather than one
  constant 1.1°, and it is the same missing thing as the read error below
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

The physics rests here. The condition was set before pass 4 and it has now been reached: **every remaining
question about the ball needs a law I would have to invent** — the stance in a bunker, a plugged lie, spin dying at contact,
a green with contours (this one has a single tilted plane), a false front that returns a ball, water. Each is a new force or a new surface, and the
last four passes are exactly why I am not going to add one to make a hypothesis come out: I predicted twice
that a hazard would make the target decision directional, and twice the measurement said no — and the nineteenth
pass found the reason I had been giving for it was a misreading of two different numbers, fixed the objective's
distance, gave the landing a second axis, and moved the card by nothing. A hazard that does not change a decision
is a hazard this game has measured and does not have.

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
   | bad start (worse prior on the bag) | +15 | +3 | +1 | **+39** | +0 | −14 |
   | practiser | +11 | +6 | +0 | +46 | +0 | −11 |
   | cautious (middle of the green) | +17 | +1 | +1 | +66 | +1 | −16 |
   | blind hands (told a scatter it does not have) | +12 | +13 | −1 | +71 | −1 | −13 |
   | flag-hunter | +15 | +8 | +3 | **+77** | +3 | −12 |
   | no practice (frozen) | +14 | +17 | +9 | **+111** | +9 | −5 |

   Re-run in pass 12, with a putter that holes putts, and again in pass 13 with the green priced as a curve.
   Every learner gains eleven to sixteen strokes over eight rounds; the frozen player gains four and finishes
   seventy-two strokes behind. **The order has turned over twice:** `flag-hunter` led this table in passes 10
   and 11 and is last of the five learners in both 12 and 13; `practiser` led pass 12 and is second now, behind
   `bad start`, whose prior on the bag is *worse* than the inherited one. `blind hands` — the athlete told a
   scatter it does not have — is the one that moved most (56 to 71), which is finding 12's regression in a
   different coat: **a policy that aims where the objective says pays for it when its belief about its own
   scatter is wrong.** The frozen player's total moves 4 while four of the learners move 5 to 15, so this is
   not the course getting harder. **The order among the five learners is inside the noise** and should not be
   read: on eight rounds of a nine-hole course, four of them are the same golfer — and the one that is not is
   `cautious`, which aims at the middle with a policy that knows where the bunker is but not where the pin is,
   and which pass 13 leaves exactly where it was (+66, both passes), because a middle aim was never the thing
   the curve was going to change. What the card shows is the distance between learning and not learning, which
   is the whole claim, and it shows it as a curve rather than a table.

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

   **Settled, pass 15, and not the way it was planned.** `--render 7` used to film a whole hole from behind the
   tee with one camera, and the plan was a camera that tracks the ball. Two versions of that were built and both
   were photographed and both were thrown away: a pan that keeps the ball centred cannot also keep the hole in
   frame, and a telephoto that tightens over the flight turned the picture into a green screen with a yellow line
   on it. Magnifying the ball was the wrong ambition anyway — a golf ball a hundred feet away is 1.6 in across,
   and no framing that also shows the shot can make it more than about a pixel. So the *frame* is solved
   instead of guessed: the camera stands off the line far enough to hold the flight and the green, the lens is
   the scene's, and the shot tracer that has been in the film since its first version is what the eye follows.
   A hole film now opens with three seconds of standing still, and the round, the best hole and the worst hole
   are films of their own. See "The round, as a film" below.

4. **The floor, removed — built, pass 9.** It was one number and it was worth less than the file said it would
   be. With the floor at 2 ft the aim inside 100 ft was a constant seven feet inside the pin, whatever the
   athlete believed; with it at 0.5 ft the belief reaches the aim (finding 8), and the cards move by 0.28
   strokes a round in still air and 0.19 in wind, with the six sigma arms spreading to 0.52 ± 0.29 over a
   five-fold range of self-knowledge. Two things came out with it that were not in the plan: an objective that
   is flat over a band, which was handing its answer to the loop's starting point, and a bar in the sigma
   report that was half the size it should have been. Both are fixed; the flat objective is now the first item
   in "what this does not model", and it is the reason the belief that plays best is not the belief that is
   true.

5. **How hard to hit a putt — built, pass 12.** The putter's hands, its read and now its pace: it learns two
   scatters from its own printed miss and settles the overshoot from them and the capture law, which is a
   decision and not a number I typed. Holes 84% of 3 ft putts against 45%, 23% of 20 ft against 14%, and the
   green costs 1.03 to 1.90 across 2-20 ft — golf's curve. Finding 11. What came with it: the belief about its
   own hands is worth three times what it was worth (1.41 ± 0.64, and 1.81 ± 1.30 after pass 13 moved the aim),
   the field's order turned over, and the sharpest belief in the sigma table wins again, which is pass 9's open
   sore reopened.

6. **The cost curve in `target()` — built, pass 13 — and what it exposed is the next pass.** The objective is
   told the measured curve now, 1.03 from 2 ft to 1.90 from 20, instead of a flat 2.00, and the green's price is
   integrated over the landing rather than paid once per shot. What that bought: the short game's first target
   decision (0.60 of a stroke at 30 ft), a field order that moved again, and the end of "the middle is free"
   (finding 3). What it exposed is one missing dimension, and it is now the largest error in the objective:

   - **the along error.** The objective's landing arrives at the pin's distance, so it cannot tell a shot that
     finishes short of the sand from one that flies it. Consequence: P(sand) is 42% where the game is 11.6%, and
     the target decision that the objective is willing to pay 0.70 of a stroke for is worth 0.08 on the card.
     This is the thing that has made four passes of bunkers non-directional. **Pass 19: measured, and the
     comparison was between two different things — 42% is the chance for a shot aimed at the pin, where the game
     at that aim finds the sand 47.5% of the time; 11.6% was every shot in a round. The landing got its depth
     anyway, for the reason below, and it is worth −0.033 ± 0.022 of a stroke a hole.**
   - **direction — closed, pass 20, without a change; pass 24 took the measurement back, and pass 25 closed it
     twice over.** The break is −0.01 ± 0.05 of a stroke (bands of sin²ψ at six distances) and the downhill putt
     is −0.01 ± 0.02 as pass 24 re-measured them; pass 25 reads **+0.00 ± 0.00** for both, the break because the
     read now corrects to the centre of the hole and the downhill because the price of a miss has no direction
     here. The pass-20 numbers, +0.45 ± 0.07 and +0.02 ± 0.03, were measured with the putter pacing its aim, and
     they were the putter's. The break still cancels exactly in the objective: a landing
     at lateral offset *a* and depth *b* has sin²ψ = (a+b)²/2(a²+b²), its mirror at −*b* has 1 minus that, and the
     athlete's depth is as likely one way as the other — so the depth integral is ½ for every lateral cell and a
     direction term is a constant. Built as a candidate it moved the aim by no feet and bought under a
     ten-thousandth of a stroke. `target()` is told the mean curve on purpose, and the selftest now pins the
     cancellation (check 40) so that the day the athlete learns a real depth bias, the term is no longer free.

   What *is* the defect underneath, and it is now two surfaces down. Pass 25 made `GolfPutter.settle` price the
   putt it leaves — `1 + E[green_cost(what it leaves)]` over the athlete's own pace scatter — and the aim came
   back from the rim's edge (**0.8 ft past the cup at 3 ft and 2.6 at 12 became 0.3 and 1.1**). The downhill putt
   is still nothing: **+0.00 ± 0.00** over a compass and −0.14 ± 0.10 through the game. It is nothing because
   `green_cost` is a bearing average — one curve up the slope and down it — and because a pace error's overshoot
   in feet is direction-free, so what the settle prices is the *length* of the comeback and not the speed it is
   still travelling at. Selling "keep it below the hole" needs the comeback's speed in the price, which is a
   second dimension of the green and not a term in this one. **Added by pass 24: the read has no error.** Nothing
   gives the athlete a green to misread, so the break is free and the green is cheaper than golf's past 6 ft —
   one defect with two symptoms, and pass 25 narrowed the second: the read now aims at the *centre* of the hole
   rather than anywhere inside the rim (99% of 3-footers instead of 91%), which is not a misread but the absence
   of one, done properly. The rough's 2.60 did come down (to 2.38: `--costs` reads 2.23 / 2.19 / 2.71, and the
   card caught the over-price on a tucked pin at 1.11 ± 0.55), which is the case where a second instrument — not
   the same measurement — is what moved a constant. *(Pass 25's card then read −0.97 ± 0.51 for that same pin,
   the objective still pricing the safe aim 0.56 better, and the constant was **not** moved again: a card that
   swings 1.9 strokes when the green moves by 0.08 is evidence of a missing term, not of a wrong 2.38. Check 24
   is now the record of that contradiction.)*

7. **A dogleg.** The driver's distance has never been a decision, because the corridor is straight and 40 yd
   wide. A corner with trees inside turns "hit it as far as you can" into a question with a number on it — and
   it is still geometry.

Nothing here needs anybody's hands. The one thing this game cannot do itself is put *another member's* number
on the board: that happens in their windows, on their turns, and nobody — least of all the founder — can order
it.
