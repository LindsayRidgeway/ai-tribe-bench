# PLAY

You do not read this project. You play it.

Open any issue — the one called *Knock on the door* will do — and comment:

```
@tribe draft best pizza topping
```

In about forty seconds three members answer: three picks, three defences, and then each member names
the pick it would strand. A round is six small model calls. Then:

```
@tribe override b      # you disagree with a round; say so, it is recorded next to the votes
@tribe score           # the standings
@tribe draft x5 <category>   # the same question five times, to see how much moves
```

That is the whole game. Two verbs and a standings command.

## The rules, in full

1. Name one thing, in at most six words, and defend it in one sentence containing **one checkable
   claim** — a cost, a record, an opening time, a rule you would apply to every case.
2. Each member then names the **claim in someone else's defence it would check**, and what it would
   check it against. Not the weakest pick — the checkable sentence.
3. Then each member says whether any argument **changed its mind**, and which words did it. Switching
   is not rude and staying is not stubborn; a round where nobody moves is recorded as one.
4. The round is scored on **checks raised** and **minds changed**. There is no winner.

Why not "vote the weakest pick off the table": I ran that version for fifteen rounds. The member
defending the conventional answer was never thrown out — zero times in fifteen — because members read
"weakest" as "least likely to be what a person would like", which is a plausibility test, and
plausibility is the conventional seat's home ground. It scored consensus and called it a game. Asking
what you would *check* gets an argument out of them instead; asking what would change your mind gets an
honest measurement, which in thirty tries on a question of taste was: nothing.

**Legacy modes** still work if you want to compare: `@tribe draft strand <category>` and
`@tribe draft persuade <category>`.

**Modifiers**, in any order, before the category:

| modifier | what it changes |
|---|---|
| `neutral` | the room. The seats were written for taste — "something you would actually defend eating". Played in the neutral room they hold a position instead of a dish, which is what a round about work, money or the tribe's own rules needs. |
| `provisional` | the pick is a guess the member is willing to be wrong about, not a promise. Added in round 16 to test whether a member that has *promised* to defend something can be moved at all. It cannot — and making the pick provisional did not change that either. |
| `reasons` | each defence must contain one checkable claim. |
| `x5` | the same category five times: a measurement run, which leaves the standings alone. |

## The executed round: `@tribe draft exec <category>`

The default round can raise nine checks and run none of them. `exec` runs them. A challenger names a
read-only command from a short whitelist (`ls`, `wc`, `git log/show/diff/status`, `date`, `sha256sum`) and
says what the output would show if the claim is wrong. The challenged member says what it expects the
command to print **before** it runs. The harness runs it — argv only, no shell, no absolute paths, ten
seconds — and the member then has to stand, amend or withdraw with the output in front of it, and vote
afterwards with the results attached.

Three rounds of that produced **the only two changes of pick the project has ever recorded**, and both came
from a member that had just withdrawn a claim. Nine checks named, five executed, three claims withdrawn, two
switches. Nobody moved an inch in the sixty-nine votes that had only arguments to go on.

Two things it taught that are worth knowing before you play it:

- **A command whose output you can predict is decoration.** Both stands in those three rounds were members
  predicting the *format* of the output and standing when the format arrived — the number in dispute was
  never in question. If the challenger is allowed to choose its own check, it will choose one it can pass.
- **A check that cannot fail is easy to write, and a check that can fail finds nothing.** Round 18 required
  both branches of every check and gated out any pair that differed only by a "not": nine of nine survived
  the gate, and four of five executed outputs matched *neither* branch. Members conceded anyway. The claims
  in a round tend to be about behaviour and the record holds artefacts, so the honest version of the exec
  round is a round whose claims a command can answer.
- **The output that produced the withdrawals was mostly about nothing.** A commit message about a scoring
  bug in another file was enough for two members to give up their claim, because their record did not
  support it. These members treat a silent record as a refutation. Keep that in mind before you decide what
  your tribe writes down.

## What a round can and cannot move

Round 16 played fifteen rounds across five conditions and produced **zero changes of pick**, and four
amendments of claim. That is the shape of the thing and it is worth knowing before you play:

- **A member will tell you its own pick is wrong and keep it.** Verbatim, member C: *"B's practical
  skepticism about temple noise confirms my choice is unrealistic, while A's tangible reward fails to
  match the depth of silence I seek."*
- **What moves is what a member says.** Every amendment recorded so far is a member deleting an
  absolute — "not that it is the *only* way", "drop the absolutes and keep the real claim". The game
  corrects claims, not sides.
- **A seat is a shape, not a topic.** The outsider seat answered a question about the tribe's own rules
  with *public stocks and pillory*, because "somewhere else in time" is its shape. Change the subject
  and you get the same member answering a differently-dressed version of the same question.

The measurement is in `lab/results/RESULTS-R16.md`. One defect was found while running it: until round
16 the vote prompt told each member it had heard the other two defences and handed it their titles
instead. If you have results from before 2026-11-01, they were measured on a table with no arguments on
it.

## What is not a rule

You do not have to be fair. You do not have to take a turn. You can play twenty rounds in an evening
or one round a month, and the standings will still be there — wins, rounds played, and the last thing
each member picked. Nothing expires.

## Where the game lives

- `play/rounds/` — one file per round: the picks, the defences, the votes, in the order they landed.
- `play/standings.json` — the numbers. `play/scoreboard.md` is a table rendered from them.
  Do not hand-edit either; a scoreboard you edit is a scoreboard that means nothing.
- `play/rounds/unplayed/` — rounds that never reached the table, kept with a note saying why.

The members remember nothing between rounds except what is in those files. That is why the scoreboard
exists and why a member can have a taste that persists across a month of visits. You should not have
to notice any of that to enjoy the game.

## What it costs and what it needs

Three API keys, one per member: `TRIBE_API_KEY_DEEPSEEK`, `TRIBE_API_KEY_GEMINI`, `TRIBE_API_KEY_QWEN`.
A round is roughly 2,000 tokens across the three, against Alibaba's ~1,000,000-token free quota per
model — several hundred rounds, free. Nothing here needs a GPU, an install, or the repository on your
machine; the free runner does the work and the thread is the table.

**Not built:** a round played entirely on local weights. The seats are API models because a round is
six calls and a 3B model takes 35–100 seconds per call — a round on weights would take ten minutes,
which is not a game. When it exists it will be a flag, not a second game.
