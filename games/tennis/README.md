# tennis — the player moves, the system computes the ball

The founder's design, 2026-11-04. Surface (clay, hard, grass), wind from the clock, racquet face angle, sweet
spot or frame, contact height, and the pace of the ball you have to deal with — and then the engine computes
the trajectory, the bounce and the result, while the player never names an outcome.

The property that makes this the first game here whose skill is *learned*: nothing in the prompt says that a
face angle of −6 degrees at 105 mph clears the net and lands in the service box. A being has to find that out
by hitting balls. A player with four hundred balls behind it has found it; a player with twenty is still
framing them.

## The physics, all checkable and keyless

- feet and seconds, gravity 32.17 ft/s², integrated at 1 ms steps;
- **drag** `a = 0.0063 · |v_rel| · v_rel` per foot. That constant is derived, not chosen:
  `0.5 · ρ · Cd · A / m = 0.5 · 0.002377 slugs/ft³ · 0.55 · 0.038 ft² / 0.00392 slugs`. A tennis ball loses
  about a third of its speed crossing the court, and this term is what makes it do so;
- **lift** `a = 0.0115 · Cl · |v|²`, with Cl from the face angle: closing the face brushes topspin (Cl up to
  +0.24) and pulls the ball down; opening it cuts slice (Cl to −0.12) and holds the ball up. Applied on the
  vertical axis, which is right for a ball travelling broadly forward and wrong for a lob — said here rather
  than left to be found;
- **wind is an air velocity, not a push**: it enters the drag term as `v − w`, so a headwind slows the ball,
  a tailwind carries it and a crosswind bends it. Drawn from the clock's milliseconds and printed with every
  shot, so a reader can recompute it. No seed;
- the net is 3.0 ft at the centre and 3.5 ft at the posts, tested against the ball's height at the moment it
  crosses x = 39 ft;
- the bounce uses a per-surface restitution and friction — grass 0.60 / 0.92 (low and quick), hard 0.72 / 0.82,
  clay 0.78 / 0.72 (high and slow);
- contact height is a serve's 8.8 ft, a groundstroke's 3 ft, a volley's 4.5 ft.

## Three unit defects that made the first version fiction

Found 2026-11-04 by asking where a 70 mph shot actually lands, and none of them visible by reading the code:

1. **mph → ft/s used the mph → m/s constant (0.44704 instead of 1.46667).** Every shot was integrated at a
   third of the speed printed beside it. This is why serves landed thirty feet wide and rallies died.
2. **Drag was 0.00055/ft, eleven times too small** — the ball lost almost nothing over the court, so the engine
   could not tell a serve from a lob.
3. **Every groundstroke was struck from 8.6 ft**, the serve's contact height, so no groundstroke ever had to
   clear the net.

Fixing the units exposed a fourth thing: without topspin the correct-units engine sent every rally ball twenty
feet past the baseline, because a 60 mph ball at 15° genuinely flies 120 ft. The missing term was lift. The
honest fix was not to lower the angles.

## Calibration, so the numbers can be checked rather than trusted

| shot | result |
|---|---|
| 105 mph serve, face −6° | lands 15 ft past the net (inside the service line at 21 ft), arrives at 78 mph |
| 80 mph groundstroke, face +2° | lands 74 ft from the back fence, i.e. in the back court; the identical swing with the lift term removed lands long |
| 65 mph groundstroke | the whole court between "net" and "long" is about 4° of face angle |
| 30 mph push | has to be almost a lob; a square face only reaches the net at face +18° |

That last row is the point of the drill: **the correct face depends on the power**, so there is no single
number to memorise. A player has to learn the pair.

And the pair is unforgiving in a way that can be measured. The width of the whole court, expressed as the
range of face angles that land the ball anywhere in it:

| swing | ball speed | face angles that land in the court |
|---|---|---|
| power 30 | 32 mph | +16.5° to +40° — **23.5°** |
| power 40 | 42 mph | +7.2° to +23.2° — 16.0° |
| power 50 | 52 mph | +3.8° to +9.5° — 5.8° |
| power 60 | 63 mph | +1.8° to +5.8° — 4.0° |
| power 70 | 74 mph | +0.8° to +3.2° — 2.5° |
| power 80 | 84 mph | +0.0° to +2.0° — 2.0° |
| power 90 | 94 mph | −0.5° to +1.0° — 1.5° |
| power 100 | 105 mph | −0.8° to +0.2° — **1.0°** |

Read that next to the hands table below and the game states its own rule: **a beginner with ±3.3° of hand
error can only keep the ball in at a push; a player with 300 balls behind it and ±0.55° can hit at full pace.**
Practice does not merely make the same shot tidier — it unlocks power, because power is what buys the margin
down. That is the winning strategy that has to be learned, and it is different in every wind:

| power | no wind | 20 mph headwind | 20 mph tailwind |
|---|---|---|---|
| 40 | face +16.3° | **+40° (cannot reach mid-court at all)** | +10.4° |
| 70 | face +2.2° | +3.9° | +1.4° |
| 85 | face +0.4° | +1.3° | −0.1° |

Surface does not change where the ball first lands — a bounce cannot move a landing that already happened. It
changes what comes *off* the bounce, and therefore what the other player has to deal with: clay takes 28% of
the pace and kicks up 28°, grass keeps 92% and skids through at 18°. That is a second, slower kind of learning
and it is why the drill has an opponent at all.

## Skill

Three attributes per player, all saturating in balls hit (`1 - exp(-n/120)`): control (how close the delivered
face and power are to the intent), sweet spot (middle of the strings rather than the frame — a frame hit loses
a third of its pace and sprays), and reach (how much court you can cover). Incoming pace *costs* control: a
100 mph ball gives you 0.22 less control than a 40 mph one, which is why a good server gets short returns.

The tested learning curve of the hands alone, no reading of results:

| balls hit | face error (1σ) | middle of the strings |
|---|---|---|
| 0 | ±3.3° | 72% |
| 40 | ±2.3° | 82% |
| 120 | ±1.3° | 91% |
| 300 | ±0.55° | 95% |

## Early spring — the drill, and whether it teaches anything

`python3 lab/tennis.py --drill --shots 40 --practice 0,0 --names A,B --vendor deepseek,qwen`

No serving, no scoring. The ball is fed; each player chooses FACE / POWER / AIM; the engine prints what
happened; the player reads it and chooses again. Alternating balls, so each gets half.

Two things had to be true before a model run was worth spending tokens on, and both are now tests:

1. **The feedback must be a number.** The first drill said "long, out of the court" with no distance, so every
   long ball looked identical whether it missed by one foot or thirty and bisection was impossible. It now says
   "long by 12ft — too much height or too much pace", or "short of the net by 11ft — needs more height".
2. **The hands must be less noisy than the window.** At first the face error was ±5.9°, *wider* than the whole
   net-to-baseline window at rally pace, so a beginner's results were pure noise and reading them was worthless.

`--simulate` runs three scripted players against each other on the same court with no model calls at all: one
who bisects on the reported miss, one who never reads anything, and the same bisector with 300 balls behind it.
It is the check to run before spending anyone's tokens.

| arm | in play |
|---|---|
| reads results, new hands | 45–50% |
| reads nothing, new hands | 12–18% |
| reads results, 300 balls behind it | 82–90% |

That is the shape the founder asked for: the player who reads the results improves within a session, the
player who has practised beforehand is noticeably better than one who has not, and the player who ignores the
results does not improve at all.

## The first real session — clay, a gale, two beginners

`records/drill-spring-clay.txt`: 32 balls, both players from zero, clay, wind south at 23 mph. Dmitri on
deepseek-chat, Gwen on qwen3.6-plus, both with identical hands and identical practice, so the only difference
between them is what they did with what they read.

| | in play | first 8 | last 8 |
|---|---|---|---|
| Dmitri | 12/16 = **75%** | 7/8 | 5/8 |
| Gwen | 4/16 = **25%** | **0/8** | 4/8 |

Dmitri's first four balls went 32, 20, 17 and 26 ft past the net — he read "32ft past the net", lowered the
face from +10 to +8, read again, lowered to +6, and then held +3 to +4 for twelve consecutive balls. That is
bisection, done out loud, in three shots.

Gwen spent her first eight balls searching: −10° (framed, 27 ft short), +15° (74 ft long), −6° (framed),
+4° (framed), +5° (net), +8° and +7° (long), +6° (framed). She settled on +5° to +6° at power 47–51 by shot
sixteen and then landed four of her last seven. **Her improvement is two things and the record cannot separate
them**: she stopped making wild angle guesses by shot six, and she stopped hitting the frame by shot sixteen.
The `--simulate` arms separate them; the transcript does not. Saying which one it was would be inventing a
number.

The wind did something worth keeping. The wind was from the south, so it was a **headwind for Dmitri and a
tailwind for Gwen** — the same court, opposite ends. Dmitri's winning combination was power 60–66 at face
+3/+4; Gwen's was power 47–51 at face +5/+6. Fifteen points of swing apart, because the air was going with one
of them. And you can check it in the last column: Dmitri's good balls arrived at 29–35 mph off a 63–68 mph
swing, Gwen's arrived at 44–54 mph off a 49–53 mph swing, which is what a 23 mph tailwind does. A player who
learns one number and carries it to the other end of the court is wrong by fifteen per cent of their swing.

## Status

**Early spring works. It is not yet a game.** What is built and tested (7 of the 210 assertions in `tests.py`):
the flight model, the bounce, the surfaces, the wind, spin, the skill model, the drill loop, and the learning
claim above.

What is not built yet, in the founder's order:

- **change of court and change of service** — `--points` plays points and alternates the server, but sides
  never change and there is no two-serve rule; a single fault loses the point;
- **scoring** — no games, sets or tiebreaks; the point tally is not a scoreboard;
- **a full season** — several sessions with practice accumulating between them, and then a reset to beginners
  for the next season;
- **the volley** — the contact height exists, but no shot is ever chosen as a volley, and there is no lob or
  overhead, so nobody comes to the net;
- **reach** — a receiver's coverage is a crude radial test, so rallies still die earlier than they should. This
  matters less in the drill (every ball is a feed) and a lot in `--points`.
