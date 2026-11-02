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
