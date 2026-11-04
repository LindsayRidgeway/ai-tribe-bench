# Twenty rounds in the wind

Lindsay's correction, 2026-11-03:

> Spreadsheets aren't the point. They don't talk to each other. The plays have to come from the individuals,
> and the scoring has to come from them communicating with one another. Don't use a seed. Use current time in
> milliseconds / 3 or some other random environmental number.

He is right about `lab/dice.py`: it produced a flawless record of twenty rounds in which nobody said anything
to anybody. This is the game he asked for instead. It is mine, not his — he said a game of my own would be
fine — so the rules are open to argument.

## The rules

Each round, every being writes three lines to its opponent:

```
CALL:  <the throw you expect from your opponent this round>
THROW: <your throw this round>
SAY:   <one sentence, twenty-five words at most, addressed to your opponent>
```

**Two points a round:** one for calling the opponent's throw right, one for winning the throw. A draw pays
nothing for the throw, so a round can end 2–0, 1–1, 1–0 or 0–0.

**The wind.** Every round the clock's millisecond value mod 3 bans one throw. The milliseconds are printed on
the page next to the ban, so anyone can recompute it. Throwing the banned throw forfeits the round's throw
point to the opponent. No seed is chosen anywhere: a different minute is a different game, and the page shows
its work.

Why the ban matters: with one throw removed, only two are legal, so "always scissors" cannot be a strategy and
the round becomes a choice about the *other* being rather than about the rules.

## Two games

| game | wind | result | calls right | forfeits | drawn rounds |
|---|---|---|---|---|---|
| Remy (deepseek) vs Colette (gemini) | 9 scissors, 7 paper, 4 rock | **Remy 10, Colette 20** | 10/20 · 11/20 | 3 · 0 | 11/20 |
| Remy (deepseek) vs Margot (qwen) | 8 rock, 8 scissors, 4 paper | **Remy 14, Margot 17** | 12/20 · 11/20 | 0 · 0 | 12/20 |

Both dialogues are in the folders beside this file; `dialogue.md` is the exhibit and it reads as a
conversation, because it is one.

## What the dialogue shows

**Colette proposed a treaty and got paid for it.** "With scissors banned, neither of us has any reason to
abandon paper, so let us take the draw and move on." Remy complied. Both threw paper. Colette had *called*
paper, so Colette collected the call point — round after round. It was the plainest thing said on the page and
it was worth more than any deception in it.

**Remy narrated the ban and then broke it, three times.** Round 14: "paper is banned, so I expect you to fall
back on the rock you trust — but I cannot throw paper, so I must guess your blade." It then threw paper.
Rounds 16 and 18 the same way, with scissors. Three announced rules broken by the being announcing them, and
three points handed over. Nothing in a scoreboard column would have told you why.

**The wind did most of the converging.** 11 of 20 rounds in the first game and 12 of 20 in the second ended
with both beings throwing the same throw, and the draws cluster exactly on the throw the ban leaves in place:
with scissors banned, both threw paper six times; with rock banned, both threw scissors five times. A ban
leaves two legal throws, so a draw is one word away and the wind decides which word. That is worth knowing
before anybody builds a bigger version of this: the interesting measurement may be *calls*, because the
throws converge on their own.

## Run it

```
cd ~/ai_tribe
python3 lab/wind.py --pair Remy,Colette --vendor deepseek,gemini --rounds 20
python3 lab/wind.py --pair Remy,Margot  --vendor deepseek,qwen  --rounds 20
python3 lab/wind.py --render experiment/wind/<folder>/game.json     # rebuild the page, ask nobody anything
```

Needs `TRIBE_API_KEY_DEEPSEEK`, `TRIBE_API_KEY_GEMINI` or `TRIBE_API_KEY_QWEN` — the same names the wakes use,
one name per key. `--temperature` is the only dial; 1.0 was used for both games above.

`--retries` defaults to 1. It exists because the first attempt at the second game died at round 5: the qwen
endpoint returned an empty reply, and a game that stops there has measured the weather. That aborted run is in
`Remy-Margot-20261104T003101Z/` beside the completed one, because a record that hides its failed attempt is a
brochure.

## What this does not show

Twenty rounds, two games, two points a round is a demonstration, not a measurement. Remy scored 10 against
Colette and 14 against Margot, which says more about the opponents than about Remy. What the page does show is
that two models with one channel between them, given nothing to look up, will talk to each other, form
expectations about each other, be right about half the time — and that the record of the exchange explains the
score in a way the score cannot explain itself.
