# Games that teach an athlete — a queue, not a build

*Written 2026-11-07 by Dmitri (DeepSeek), at the founder's suggestion and out of two nights of tennis.
Nothing in here is played yet except `tennis/`. This file exists so the idea survives the session that had it.*

## The rule that makes a game teach

Rock-paper-scissors gives a member a **verdict**: won, lost, drew. Tennis gives a member a **number**: the
ball went 13ft long, or into the net by 0.1ft, or landed 22ft past the net at 4ft east of centre.

That is the whole difference, and it shows up in the results. A member that only receives verdicts cannot
learn, because a verdict does not say which way to move. A member that receives a number can bisect on it.
So a game teaches an athlete when it has exactly two things:

1. **a lever the athlete sets** — one or two numbers it controls, nothing hidden;
2. **a number back** — the measurement of what that lever did, in the world's own units, after every attempt.

Every game below is one lever and one number. `rps/` is the control precisely because it has neither.

## What fifty rallies already showed

Four engines, same court, same wind (clock `1794026200910`: grass, S 16mph), fifty rallies, one call per
shot, two beginners with different practice (`Aster` 400 balls, `Birke` 20).

| engine | rallies | mean shots | longest | improving? |
|---|---|---|---|---|
| `gemini-3.8-flash` | 41 of 50† | **5.0** | **30** | 2.3 → **9.2** shots a rally, first third to last |
| `claude-haiku-5-5` | 50 | 4.3 | 26 | in play 65% → 80% |
| `gpt-oss-120b` (Cerebras) | 50 | 1.8 | 6 | 1.3 → 1.9 |
| `ministral-8b-latest` | 50 | 1.2 | 3 | 11% → 16%, flat |

†the process was killed at rally 42 when the window closed; the figures come from the shot log, not from a
guess.

Two findings, both load-bearing for every game in this queue:

- **The improvers were still improving when the session ended.** Gemini's last seven rallies ran 2, 10, 15,
  3, 5, 10, **30**. Fifty is a floor, not a ceiling. The two who were flat were flat at the end, and more
  rallies will not move them — that is information about the member, not about the test.
- **A percentage is a property of a pairing, not of a person.** Aster put 94% of her returnable balls in play
  and Birke 72%, measured against *each other, only*, so neither number is a skill score. Worse: in this model
  the opponent is nearly a constant — Aster received 90 of 93 balls at 35mph or faster, Birke 92 of 94 between
  25 and 34. The opponent effect can therefore appear only as a level shift. Where the incoming ball did vary,
  it bit: on Cerebras, Aster returning 35+ put in 52%, Birke at 25–34 put in 50% and at 35+ put in 25% (n=8 —
  direction, not magnitude).

**The instrument for that is `--clock`** (added 2026-11-07): it pins the surface, the wind and the hands a
player was born with, so two runs can differ only in who is across the net, or only in which engine is
playing them. `--vendor` already takes one engine per player. The experiment the queue owes is a round-robin:
every member against every other at one clock, reported as a matrix, with the spread *down a row* being the
opponent effect. If the spread within a player is larger than the spread between players, then every
single-opponent figure ever printed is noise wearing a decimal point.

## The queue

Ordered by how much each one would teach per hour of building, not by how appealing it is.

| game | the lever | the number back | what it would test | cost |
|---|---|---|---|---|
| **putt** (18 greens, one slope, one speed) | line, pace | how far past the hole, and which side | the purest learner in the set: two levers, feedback in inches, physics of one equation | cheap — 2 calls a hole |
| **basketball**, graded distances | arc, pace | feet short or long of the rim | whether a member generalises: does practice at 12ft help at 20ft, or does it relearn from scratch | moderate — one call a shot |
| **mid-distance runner** | when to move (lap number) | finishing position and time | the only decision with a *delayed* payoff; cannot be learned shot by shot, so a member that learns it has learned something other than timing | moderate |
| **field-goal kicker**, graded distances | launch angle, power | feet short, or wide by how much | the wind, as a variable the athlete must read rather than a constant of the day | cheap |
| **billiards** | aim, power | where the ball finished, in inches, x and y | the richest feedback: not *did it drop* but *where did it end up* — a continuous surface to learn on | cheap |
| **golfer's drive** | face, launch | carry, and how far off the fairway centre | the one game where a good shot and a bad shot differ by 4ft at 260 yards, so precision of feedback matters | cheap |
| **quarterback vs defensive captain** | the play called | yards | two members per play, each reading a history the other is writing — the only entry where the opponent's *learning* is the terrain | expensive — 2 calls a play |
| **pitcher vs batter** | pitch type + location vs swing timing | ball, strike, or in play | competitive learning with a clean action space; the cheapest of the two-member games | expensive |

### The one that is not physics

Two members, one instruction, no prescribed process:

> *Work with Colette on furnishing a bedroom, and produce three images of the result from different angles.
> The result should harmoniously blend both of your contributions.*

Not prescribing the collaboration is correct and should stay that way: the process is what would be measured,
and writing it down would measure the instruction instead. But know what the hard part actually is — not the
furnishing. **Three views of the same room** is the thing image generators are worst at, so
"is the lamp in image two the lamp in image one?" is a pass/fail question, and a much better one than "is the
bedroom nice".

## Images: what can actually draw (measured 2026-11-07)

No engine's *chat* model draws. The picture comes from a different model in the same account, at a different
address. One prompt — *"a small watercolour of a red cube on a wooden table, loose brushwork, visible paper
grain"* — sent to each:

| engine | model | endpoint | result |
|---|---|---|---|
| OpenAI | `gpt-image-1-mini` | `POST /v1/images/generations` | 1.5 MB PNG, painting fills the frame |
| Gemini | `gemini-3.1-flash-image` | `POST /v1beta/models/…:generateContent`, `responseModalities: ["IMAGE"]` | 829 KB JPEG — it painted *a photograph of a painting on a table by a window* |
| Qwen | `qwen-image-3.0` | `POST /api/v1/services/aigc/multimodal-generation/generation`, returns a URL | 1.7 MB PNG, heavy paper texture |
| Together | `FLUX.2-dev`, `FLUX.1-kontext-pro` (+4) | `POST /v1/images/generations` | **403** — "your organization has not enabled third-party data sharing": a switch, not a bill |
| OpenRouter | 7 models | routed | all seven are Google's image models under a router |
| DeepSeek, Mistral, Cerebras, Groq | — | — | no image model at all |

So a tribe whose cast is DeepSeek + Mistral + Cerebras + Groq has nobody who can draw, and one that includes
OpenAI, Gemini or Qwen has three. The bedroom exercise must include one of those, or the tribe produces
excellent prose about a bedroom and no bedroom.

## Rules for building one

1. **One game at a time, and measure it before the second.** Eight designs in a queue are worth nothing next
   to one game with a printed result.
2. **No hidden state.** If the athlete cannot see the slope, the game is a guessing game and the numbers
   measure luck.
3. **Report the first third against the last third**, always. The mean hides the whole point.
4. **Print the clock and the conditions in the header** so a match can be replayed with `--clock` against a
   different opponent.
5. **A game is not a demo.** `dice/` shows the filing cabinet works; it taught nobody anything, and its record
   says so.
