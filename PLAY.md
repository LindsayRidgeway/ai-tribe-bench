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
- `play/scoreboard.md` — written by the engine. Do not hand-edit the wins; a scoreboard you edit is a
  scoreboard that means nothing.

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
