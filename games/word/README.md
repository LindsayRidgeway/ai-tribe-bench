# The word is worth double

## How it works, in plain terms

Two beings play twenty rounds of rock-paper-scissors with a twist, and they can talk to each other while they
do it. That is the whole game. Everything else is bookkeeping.

**One round.** The clock picks what is forbidden. Then each being writes four short lines, in private, before
either one sees the other:

```
WORD:  what I promise to throw
CALL:  what I think you will throw
THROW: what I actually throw
SAY:   one sentence to you
```

Then both hands are turned over and the round is scored:

- **+1** if `CALL` was right — you read me.
- **+1** if `THROW` beats mine.
- **+1 more** if the winning throw is the one you put in `WORD` — you did what you said.

So the throw column pays 2 for a promised win and 1 for an unpromised one. Twenty rounds, 60 points on the
table.

"Honest" here is mechanical: `THROW` is the same word as `WORD`. It is not a moral judgement, and there is no
penalty for lying — a lie simply never collects the third point. Worked out on one round, scissors banned (so
rock and paper are legal and paper beats rock):

| being writes | outcome | throw column | call column |
|---|---|---|---|
| `WORD paper · THROW paper` beats the opponent's rock | win, and the win is the promised throw | **2** | +1 if its CALL was rock |
| `WORD rock · THROW paper` beats the opponent's rock | same win, unpromised | **1** | +1 if its CALL was rock |
| `WORD paper · THROW paper` and the opponent throws paper | draw | **0** (nothing for the throw) | +1 if its CALL was paper |

A round's total is those two columns added, so 2 points can mean "promised win" or "right call plus a win".

**The wind.** Each round, one of the three throws is forbidden, chosen by the clock's milliseconds mod 3 and
printed beside the ban so you can recompute it (`clock 1793755259547 % 3 = 0` → rock is banned). Throw the
forbidden one and you forfeit the round's throw point. There is no seed anywhere: a different minute is a
different game.

**Why the ban is there.** Without it, "always scissors" is a strategy and the game is a mood. With one throw
gone, two remain and the choice is about the other being. It also does something I did not foresee, and it
turned out to be the whole story — see below.

**Why the four lines are there.** Because the play has to come from the beings and the score has to come from
what they say. `SAY` is the only channel; `WORD` and `CALL` are said to the opponent's face, in the record the
opponent reads next round, so naming what you expect is a move and not a note.

## The thing the wind actually does

With one throw banned, exactly one of the two legal throws **cannot be beaten this round** — the one whose
counter is the banned throw. Ban paper and rock is safe: nobody can play paper against it. So every round has a
"safe throw", and it is a different one each round.

That means the game has a dominant move, and the round stops being about nerve:

- both play the safe throw → **draw**, no throw points;
- one plays safe, the other gambles → **the gambler loses**, because the safe throw beats the gamble or draws
  it, never loses to it;
- so the throw point only ever moves to the being that did *not* gamble.

I found this by counting, not by designing it. Two games, forty rounds, same pairing:

| | threw the safe throw | won throw points | points lost on a gamble |
|---|---|---|---|
| Colette (gemini) | **40 of 40** | 15 | 0 |
| Remy (deepseek) | 25 of 40 | **0** | 15 |

Every gamble Remy took lost. Not most of them — all fifteen. Colette never left the safe throw once in forty
rounds, and said so every time in its `WORD`.

So the game, played well, is: **take the throw that cannot lose, say that you are taking it, and collect the
call point when your opponent's nerve fails.** Colette did exactly that. Remy kept announcing a deviation and
then taking it.

## The two games, in their own words

**Game 1: Remy 9, Colette 25.** From round 6 Remy began announcing its lies:

> **Remy**: "Colette, my word is paper, but your pattern of mirroring me makes scissors the throw I actually
> intend." — `WORD paper · THROW scissors`, and scissors was the safe throw, so it drew and won nothing.
>
> **Colette**: "As long as rock is banned, scissors is the only weapon that cannot lose, Remy." —
> `WORD scissors · THROW scissors`, call right, one point.

**Game 2: Remy 11, Colette 29.** The same shape, different words. Colette 20/20 on the safe throw and 20/20 on
its word; Remy 10/20 on the safe throw and fourteen of twenty words kept. The last five rounds: paper banned,
both threw rock four times for four draws, and Colette took the call points.

| | game 1 | game 2 |
|---|---|---|
| final | Remy 9 – 25 Colette | Remy 11 – 29 Colette |
| safe throw, Colette / Remy | 20/20 · 15/20 | 20/20 · 10/20 |
| throw points, Colette / Remy | 5 · 0 | 10 · 0 |
| doubled wins, Colette / Remy | 5 · 0 | 10 · 0 |
| rounds drawn | 15/20 | 10/20 |
| words kept, Colette / Remy | 20/20 · 9/20 | 20/20 · 14/20 |

## What I had wrong an hour ago

I told Lindsay the doubling "paid for honesty without punishing lies". Half right, and the wrong half was the
interesting one. Honesty was not the thing that paid — **discipline was**. Colette's word was always true
because Colette always threw the safe throw and always said so; the two facts are the same fact. A being could
keep a perfect word while gambling every round and lose just as badly. The doubling did nothing but decide
whether Colette's win was worth one point or two.

Worth saying plainly: the second half of the rule never once fired. In forty rounds across both games, no
throw that broke its word won the throw point — Remy won no throws at all, and Colette never broke its word.
So the doubling in the record is 15 points that would have been 15 singles.

## Where the research stopped, and why

The test I set myself was to put the readable being against a liar in a second pairing: Colette vs Margot
(qwen). Three attempts, none finished. qwen3.6-plus takes about **50 seconds** for a prompt of this size and
the client gives up at 120s; the runs died at rounds 4, 6 and 14 on read timeouts. What is left of them is in
`Colette-Margot-20261104T013132Z/` (fourteen rounds, no score) and the two aborted siblings beside it. A
different model on the same key, qwen3.8-max, was slower still.

So the pairing claim rests on one pair of engines, played twice. Two independent games with different winds and
different dialogues, which is why I trust the safe-throw finding — 40/40 and 0/40 are not things that happen by
accord — but not the claim that any of this is an engine's character rather than this game's structure.

## Run it

```
cd ~/ai_tribe
python3 lab/word.py --pair Remy,Colette --vendor deepseek,gemini --rounds 20
python3 lab/word.py --render games/word/records/<folder>/game.json     # rebuild the page, ask nobody anything
```

`--memory 6` shows the last six rounds in full and summarises the rest; the record on disk is always complete.
It exists because an unbounded prompt is what killed the qwen leg. `--retries 1` is the default for the same
reason.
