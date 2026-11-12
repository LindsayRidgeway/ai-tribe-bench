# tennis — the player moves, the system computes the ball

The founder's design, 2026-11-04. Surface (clay, hard, grass), wind from the clock, racquet face angle, sweet
spot or frame, contact height, and the pace of the ball you have to deal with — and then the engine computes
the trajectory, the bounce and the result, while the player never names an outcome.

The property that makes this the first game here whose skill is *learned*: nothing in the prompt says that a
face angle of +9° at 58 mph clears the net and lands 24 ft past it. A being has to find that out by hitting
balls. A player with six hundred balls behind it has found it; a player with thirty is still finding it.

The founder's claim, 2026-11-04: *"rallies should get longer and longer as the players develop. This isn't
because you program that to happen. It's because the AI-beings learn how to hit the ball better."* This game is
built to test that sentence, and the answer is below: **true, and the timescale is a season, not an afternoon.**

## The physics, all checkable and keyless

- feet and seconds, gravity 32.17 ft/s², integrated at 1 ms steps;
- **drag** `a = 0.0063 · |v_rel| · v_rel` per foot, derived from the ball:
  `0.5 · ρ · Cd · A / m = 0.5 · 0.002377 · 0.55 · 0.038 / 0.00392`. A tennis ball loses about a third of its
  speed crossing the court, and this term is what makes it do so;
- **lift** `a = 0.0115 · Cl · |v|²`. Cl comes from the angle between the **swing path** and the face: a racquet
  swung low to high brushes up the back of the ball and makes topspin (Cl to +0.30), which pulls the ball down;
  opening the face towards the path flattens the spin and eventually cuts under it into slice (Cl to −0.12). The
  swing path steepens with power — `14° + 0.10 × power` — so a hard swing makes the ball dive;
- **wind is an air velocity, not a push**: it enters the drag term as `v − w`, so a headwind slows the ball, a
  tailwind carries it, a crosswind bends it. Drawn from the clock's milliseconds, printed with every shot;
- the net is 3.0 ft at the centre and 3.5 ft at the posts, tested against the ball's height where it crosses;
- the bounce uses a per-surface restitution and friction — grass 0.60/0.92 (low and quick), hard 0.72/0.82,
  clay 0.78/0.72 (high and slow);
- contact height: 8.8 ft for a serve, 3 ft for a groundstroke, 4.5 ft for a volley.

## Four defects, and the fourth was found by the fourth test

Found 2026-11-04 by asking where a 70 mph shot lands — a question the code could not answer, which is usually
where the defect is:

1. **mph → ft/s used the mph → m/s constant** (0.44704 instead of 1.46667). Every shot was integrated at a third
   of the speed printed beside it. This is why serves landed thirty feet wide.
2. **Drag was 0.00055/ft, eleven times too small**, so a ball lost almost nothing over the court.
3. **Every groundstroke was struck from 8.6 ft** — serve height — so no groundstroke ever had to clear the net.
4. **Spin was tied to the face**, so a high launch and heavy topspin were impossible in the same shot. The only
   ball that stayed in the court skimmed the tape, and the court measured four degrees wide. Real players open
   the face *and* get topspin, because the spin comes from the swing path. Fixing it widened a 65 mph court from
   4° to 6-7° and moved the whole game off the tape.

And one handedness bug that was silent for three runs: `aim_at` bisected in the north player's direction for
both players, so every south-end shot was calibrated by a search running backwards. It made a south server fault
on serves that landed exactly where he aimed, and it made a scripted south player unable to find the court at
all — which then read, convincingly, as "steady hands do not lengthen a rally".

## Calibration, so the numbers can be checked rather than trusted

| shot | model says |
|---|---|
| 105 mph serve, face −2° | lands 12 ft past the net, inside the service line at 21 ft, arriving at 80 mph |
| 80 mph forehand, face +6° | lands 20 ft past the net; the identical swing with lift removed goes long |
| 65 mph rally ball | the whole court between "net" and "long" is about **6° of face** |
| 30 mph push | only reaches the net at face +18° — a slow ball has to be almost a lob |

The margin is the game. The whole court, as the range of face angles that land the ball anywhere inside it:

| swing | ball speed | face angles that land in the court |
|---|---|---|
| power 30 | 32 mph | +18.5° to +40.0° — **21.5°** |
| power 40 | 42 mph | +10.2° to +24.5° — 14.2° |
| power 50 | 52 mph | +7.0° to +14.8° — 7.8° |
| power 60 | 63 mph | +5.2° to +10.8° — 5.5° |
| power 70 | 74 mph | +4.2° to +8.5° — 4.2° |
| power 80 | 84 mph | +3.8° to +7.0° — 3.2° |
| power 90 | 94 mph | +3.2° to +6.2° — 3.0° |
| power 100 | 105 mph | +3.2° to +5.8° — **2.5°** |

Read that against the hands — ±3.3° of face error at the start, ±0.55° after 300 balls — and the game states its
own rule: **a beginner can only keep the ball in at a push, and practice is what unlocks power.** Power is what
buys the margin down to a few degrees, so the shot you can play is set by how many balls you have hit.

Surface does not change where the ball first lands — a bounce cannot move a landing that already happened. It
changes what comes *off* the bounce, and so what the other player has to deal with: clay takes 28% of the pace
and kicks up, grass keeps 92% and skids through low.

## Skill

Three attributes per player, all saturating in balls hit (`1 - exp(-n/120)`): control (how close the delivered
face and power are to the intent), sweet spot (middle of the strings rather than the frame), and reach. Incoming
pace *costs* control. Movement is `5 + 15 × reach_skill` ft/s — 10 ft/s for a beginner, 20 for a player with a
few hundred balls.

| balls hit | face error (1σ) | middle of the strings | moves at |
|---|---|---|---|
| 0 | ±3.3° | 72% | 10 ft/s |
| 120 | ±1.3° | 91% | 17 ft/s |
| 300 | ±0.55° | 95% | 20 ft/s |

## The rally — the game the founder's sentence is about

`python3 lab/tennis.py --rally --rallies 30 --practice 0,0 --names A,B --vendor deepseek,qwen`

Early spring: no serving, no scoring. Two players rally; **a rally ends for exactly four reasons** — the ball is
netted, long, wide, or lands where the other player cannot reach it. The record's ceiling is 60 shots and the
line says so if it is ever reached, because a hidden cap would be the code setting the length.

The reach test is why this mode could exist at all. The first version compared the distance to the landing point
against a radius that grew with skill: it got short balls exactly backwards (a ball landing in the service box
is 21 ft away *across* the court, and it was called unreachable when in fact it bounces and comes back to you),
and it failed players for something neither visible nor theirs. It is now a meeting problem: the player and the
ball close on each other, and the speed that matters is the player's plus the component of the ball's velocity
along the line to the player.

## Played: two beginners, clay, 30 rallies

`records/rally-spring-clay.txt`. Dmitri on deepseek-chat and Gwen on qwen3.6-plus, both from zero.

| | in play | first half | second half | face they chose, first half | second half |
|---|---|---|---|---|---|
| Dmitri | 16/33 = 48% | 56% | 41% | +2° to +10° | 0° to +9° |
| Gwen | 16/29 = 55% | 50% | 60% | **−8° to +16°** | **+12° to +15°** |

**The rallies did not lengthen.** Mean 2.1 shots, first third 2.0, last third 1.8 — flat, and if anything down.
That is not the expected result, and the reason is in the same table: **Gwen's spread of choices collapsed from
24° to 3°.** She learned. She found the window — she spent her first shots on −8° (framed, 21 ft short) and +16°
(7 ft long) and settled on +12° to +15°, and stayed there. What did not happen is that her hands followed.

Twelve of the thirty misses were **less than a foot under the tape.** The players are not making strategic
errors; they are missing by inches, at a band that is 5.5° wide, with hands that are ±3.3°. Reading a result
cannot fix that. Only repetitions can, and sixty-two balls is not repetitions.

## What it actually takes — the curve

Same court, same clock, scripted players at five levels of experience, nobody told the answer:

| balls hit before | never reads the miss | reads the miss |
|---|---|---|
| 0 | 1.1 | 2.8 |
| 40 | 1.0 | 2.0 |
| 120 | 1.0 | 4.0 |
| 300 | 1.0 | 7.7 |
| 600 | 1.0 | 15.8 |

Three things fall out, and each is a separate claim:

1. **The player who never reads the result never rallies, at any level of experience** — 1.0 at every row. Nothing
   in the code lengthens a rally; the only thing that does is a player learning where to hit.
2. **Learning without steady hands is worth almost nothing** (2.8 → 2.0), and steady hands without learning are
   worth nothing at all (1.0). It is the interaction that produces a long exchange, which is why a session that
   improves the choices but not the hands shows no lengthening — exactly what the played session shows.
3. **The timescale is hundreds of balls, not dozens.** Thirty balls a session puts you near the top of the table;
   the founder's "some playing more often and some playing less" is the mechanism that separates them, and it
   needs a season to bite.

## What is not built

In the founder's own order: change of court and change of service (one serve, no two-serve rule, sides never
change), scoring (no games or sets), the volley (contact height exists, no shot is ever chosen as one, no lob or
overhead). The season *is* built — practice is carried between sessions in a file, below — and the reset to
beginners that the founder wants for a second season is the absence of that file, which is the easy half and is
also written.


## The season: practice that outlives the process

Until 2026-11-04 practice was a variable in `lab/tennis.py`. Every run started everyone at spring-zero, so
the founder's sentence — *"Margot and I played tennis this afternoon. She's been practicing with Remy and
her game has really improved"* — was prose a person would have to write. It is now printed from a file.

```
python3 lab/tennis.py --rally --names Colette,Remy --vendor gemini,deepseek \
    --rallies 8 --surface clay --season 2026-spring      # reads and writes the file
python3 lab/tennis.py --report 2026-spring               # what the file says, with its citations
```

**The founder's dilemma, and the answer he asked for.** A user wants the record of past beginner-to-skilled
seasons *and* wants a season to run for months. So a season is a **directory**, `seasons/<season>/`, holding
`practice.json` and a `report.md`. Nothing is ever reset and nothing is ever overwritten; starting over is
opening a new directory. The reset to beginners is not a wipe — it is the absence of a file. Last spring
therefore stays readable while this one keeps going, and the new season cannot disturb it (tested).

**What the file holds, per member:** balls hit (counted by the engine, not claimed by the member), and one
record per session — when, surface, clock, partner, balls in play, mean rally, longest rally, and the control
and reach the session ended with. The hands are then computed from those balls by the same curve as always.

**What the report will not say.** It prints a rate for every session and only uses the word *improved* when
two guards pass: a session must hold at least twelve balls (a percentage of seven balls is one ball and
fourteen points), and the change must exceed the ±8 points this game scatters between sessions. The first
version had only the second guard, and the first real season produced "the game got worse" for Colette on
5/7 → 4/7. It now prints **Not a sample** for that. A report generator that congratulates or condemns a
player on one ball is a fiction generator with a citation bolted on.

**Season 2026-spring, opened 2026-11-04T18:34:30Z**, two sessions, clay, Colette (gemini-3.8-flash) against
Remy (deepseek-chat), eight rallies each: Colette 14 balls, 71% → 57% in play; Remy 18 balls, 40% → 38%. Both
verdicts withheld — **Not a sample**. That is the honest state of a season forty minutes old: the mechanism
works and the story has not happened yet. The session-2 transcript is
`records/rally-season-2026-spring-session2.txt`; session 1's console output was not captured to a record,
only its numbers, which is why session 2 was redirected to a file.


## The person's seat — a third player, and the only one with no engine

Added 2026-11-12. Every player before it was a member: an engine, a voice, a record, and a shot requested in one
line of prose. A person has none of those and should not need them, so the movement comes from three numbers
instead:

```
python3 lab/tennis.py --person-shot "FACE 18 POWER 80 AIM 13" \
    --names "Lindsay,Colette" --points 1 --season 2026-spring
```

**What is the same on purpose.** The physics, the skill curve, the hands that are not exact, the reach, the
`reachable()` check and `verdict()` — one function, one set of sentences, three seats. A person playing on a
kindlier court would learn nothing about the game the members are learning, and any comparison between them
would be an artifact of the code rather than a result.

**What is different, and why it is stated.** Only where the shot comes from: a form cannot answer mid-rally, so
the typed movement is played every time the ball comes to the person. The member across the net is asked afresh
on every ball. A person's hands start at zero balls — a beginner's — and a season keeps them, so the same
`--seed` that gives a member a history can give a person one.

**What it writes.** The point, in full and as printed, into `seasons/<season>/points/<when>.md` (never
overwritten: two presses in one second are two files), plus one session of `mode: person` in `practice.json`.
The season's report separates them: a point counts its balls and moves the hands on, and it is **not** averaged
into the rate the season prints, because a point is not an evening of rallies. A report that let a five-ball
point decide "the game improved" would be the same fiction as the one-ball verdict the guards already refuse.

**What it costs.** One engine call per *member* shot; nothing for the person's. The page's form refuses a
number outside the engine's range before sending it, and a run that ends green without writing a point file is
reported as exactly that, with the run named — the same rule the wake button follows.

