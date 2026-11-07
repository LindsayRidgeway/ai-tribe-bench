# putt — one green, one slope, one speed, and the miss in feet

The first game in `games/ATHLETES.md`, built 2026-11-07. It exists to answer one question with a number
instead of a paragraph: **does a being get better at this when the only thing it is told after each attempt
is how far past the hole the ball finished?**

    python3 lab/putt.py               # 18 holes on one 2% green, then 3 holes it never practised
    python3 lab/putt.py --grade 0     # the same 18 holes dead flat: the control
    python3 lab/putt.py --selftest    # the five checks the numbers rest on

## The levers and the number

Two levers, both visible, nothing hidden:

- **line** — the bearing the ball starts on, in degrees off the hole;
- **pace** — the ball's speed off the face, in feet per second.

One number back, in the world's own units: **how far past the hole (or short of it), in feet, and which side,
in feet.** Not a verdict. A number, so an athlete can bisect on it — which is the whole difference between
this and `rps/`.

## The physics, one equation, checkable and keyless

```
friction   a = 18 / stimp            ft/s²   from the stimpmeter: released at 6.0 ft/s, the ball rolls `stimp` ft
slope      a = 32.17 * grade / 100   ft/s², pointing downhill
capture    hole radius 2.125 in; a ball crossing the hole faster than 4.5 ft/s lips out instead of dropping
```

Measured by `--selftest`, so the numbers can be checked rather than trusted:

| check | model says |
|---|---|
| stimp definition, 10.5 green | 6.0 ft/s on the flat rolls **10.50 ft** |
| 2% slope, 9.0 ft/s | **17.2 ft uphill**, **37.8 ft downhill** — the same hit is worth 2.2x, by direction |
| capture, 20 ft hole | 9.4 ft/s arrives at 4.45 ft/s and **drops**; 10.5 arrives at 6.46 and **lips out** |
| break, aimed straight at 25 ft, 2% across | the ball finishes **3.12 ft right (downhill)** and 10.18 ft short |

That third and fourth row are why this game teaches two separate things. Pace is not "hit it hard enough":
a ball can be on the exact line and still lip out, and the same ball straight at the hole finishes three feet
downhill of it.

## The athlete, and what it is not

No model calls. It is told the distance, the bearing, the green's speed and the slope — a player can see and
feel all four, so nothing is hidden. It does not know how *it* converts intent into a ball, so it carries two
numbers and learns both from the printed miss:

    pace = gain * sqrt(2 * a_eff * distance)      gain   — one unknown
    aim  = bearing - break * cross_slope          break  — one unknown, degrees per ft/s²

Both errors are monotone in their own lever, so bisection is legitimate here rather than a guess with a
decimal point: each putt halves the bracket of whichever lever last produced an error, and it alternates.

It is a stand-in for a member, not a member. What it tests is the **game**: if bisection cannot close this
loop, no model can.

## What the eighteen holes printed

Full run: `records/putt-2026-11-07.txt`. Green: stimp 10.5, 2% falling toward 120°, clock-free and
deterministic apart from nothing at all — the same run twice is the same run.

| | first 6 putts | last 6 putts | holed | held out (3 holes, no practice) |
|---|---|---|---|---|
| **2% green** | 4.26 ft miss | **6.16 ft** | 0/18 | 1.17 ft |
| **flat green** (control) | 4.80 ft | **0.00 ft** | 9/18 | — |

Two results, and the second is the one worth having:

1. **Where the athlete's model can express the answer, the feedback is sufficient.** Flat, it converges to a
   pace gain of 0.996 and a single line bias, holes 9 of 18 including the last six in a row, and its mean miss
   goes to zero. Nothing in the prompt or the code told it the right answer; the printed miss did.
2. **On a sloped green the same feedback is not sufficient for a single line bias, and the curve gets
   worse rather than better.** A 2% green breaks 3 ft on a 25 ft putt and more on a 48 ft one, so the bias
   that holes a 6 ft putt misses a 48 ft putt; the athlete oscillates and finishes at 6.16 ft. That is a
   property of the model it was given, not of the number it was given — the fix is a third lever, break as a
   function of distance, and that is the next game's work, not this one's.

**Do not read the held-out row as success.** Three holes is not a sample, and its 1.17 ft being better than
the last third of the training set is a warning that both figures are noise at this size.

## Two defects found while building it

1. **Every ball that stopped near the hole was being counted as holed.** The crossing speed was taken as
   `v * (1 - f)` on the millisecond's segment, so once the ball was merely *near* the hole the closest
   approach clamped to the segment's end and the speed read zero. Fixed by testing the plane through the hole
   and taking the speed at that crossing; the capture check is what found it.
2. **A learner fitted on a fractional error across different distances diverges on a sloped green.** The
   along error divided by distance is not one function of the pace coefficient when the slope's pull varies
   by bearing (0.643 ft/s² down a 2% fall, which is 37% of friction), so a secant step on that number walked
   the pace up until putts finished 130 ft past. The bisection above replaced it because a bracket cannot run
   away.

## What this game owes next

Break as a lever that scales with distance (one more unknown, one more bisection), then the numbers in the
table above become the baseline that a *member* — not a script — has to beat. Only then does the next entry
in `games/ATHLETES.md` start.
