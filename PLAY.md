# PLAY

You do not read this project. You play it.

Open any issue — the one called *Knock on the door* will do — and comment:

```
@tribe draft best pizza topping
```

In about forty seconds three members answer: three picks, three defences, and then each member names
the pick it would strand. A round is six small model calls. Then:

```
@tribe override b      # the table got it wrong; you decide
@tribe score           # the standings
```

That is the whole game. Two verbs and a standings command.

## The rules, in full

1. Name one thing, in at most six words, and defend it in one sentence.
2. Each member then names the pick it would **strand** — one of the *other* two, with a reason a
   fifteen-year-old would accept. No abstaining, no "they're all good".
3. If a member names its own pick, that is a **fold**, and it counts: the pick is off the table and
   the member takes the hit. Members fold more often than you would think, and it is usually funnier
   than the vote.
4. The most-stranded pick is thrown out. A tie throws nobody out, and a split is a result, not a
   failure of the round.
5. You can overrule all of it with `@tribe override b`.

The standings count what the votes actually are — rejection votes. So the numbers are **thrown out**
and **never thrown out**, not "wins". A round where nothing is settled does not retroactively become
a win for anyone.

## Why three members

Because a draft needs disagreement. One model asked for the best pizza topping gives you the answer
a search engine would give you, and there is nothing to watch. Three members with three stances give
you a table with an argument on it, and the argument is the entertainment — the picks are just how it
starts.

The stances live at the top of `play/play.py` in one dictionary: **the loyalist**, **the heretic**,
**the outsider**. Edit them. Swapping `the heretic` for `the traditionalist` changes every round that
follows, which is the cheapest way to find out how much of the argument is the model and how much is
the seat.

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
