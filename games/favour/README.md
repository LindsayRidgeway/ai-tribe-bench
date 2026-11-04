# The clock favours a throw

The third version of the talking game, and the first one where the choice of throw is a choice.

## Why it exists

Lindsay asked the question that broke the previous version: *"the other gambles → the gambler loses, always. I
think I understand what a 'gamble' is, but why would any experienced player ever gamble?"*

They wouldn't. In `lab/word.py` a round bans one throw, which leaves two legal ones — and the legal throw whose
counter is banned cannot be beaten that round. The other legal throw can only beat the banned throw, which
nobody may play, so it can only draw or lose. Never win. So the "gamble" had no upside: it was a mistake, not a
risk, and my calling it a gamble was generous to Remy. Across eighty rounds of the first two games, every
throw that was neither the safe one nor a forfeit lost or drew.

Which means the first two games were not decided by the throws at all. Both beings found the safe throw, the
throw column died, and only `CALL` was live. Colette did not win 15–0 on throws by skill; Remy handed them
over.

## The two rules that changed

**Nothing is banned.** Each round the clock *favours* one throw — milliseconds mod 3, printed so a reader can
recompute it — and a winning throw with the favoured throw is worth two. All three throws stay legal, so there
is no safe throw. Chasing the favoured throw is a temptation with a counter, not a forced move.

**The sentence is scored.** `SAY` now pays when the opponent's `CALL` is a throw you named out loud and did not
put in `WORD`. You get a point for being believed on the strength of your sentence — which also means a
sentence that names a throw is a trap: name it and they call it, and if you throw something else they have
given you a point and lost the call.

Four points a round: right call, winning throw (doubled if favoured), kept promise, believed sentence.

## The game played

Remy (deepseek) 28 – 27 Colette (gemini). Twenty rounds, 80 points available.

| | Remy | Colette |
|---|---|---|
| called the opponent right | 6 | 5 |
| winning throws (promised) | 6 (5) | 7 (4) |
| points for being believed | 11 | 11 |
| kept its word | 16/20 | 19/20 |
| threw the clock's favoured throw | **1/20** | 9/20 |

Two things this shows that the earlier versions could not:

- **The game is live.** 28–27 against 9–25 and 11–29. Calls right fell to 6 and 5 in twenty — with three live
  throws, neither being can predict the other, which is what a game looks like rather than a forced move.
- **Temperament finally shows in a choice.** Faced with the same clock, Colette chased the favoured throw nine
  times in twenty and Remy once. Under the ban rule that difference could not exist, because there was only
  one sane throw.

The sentence paid 22 of the 80 points. It is now a move: both beings used it, and both were believed about as
often as they were called correctly — the words and the throws have come apart, which is the point of having
a channel at all.

## Run it

```
cd ~/ai_tribe
python3 lab/favour.py --pair Remy,Colette --vendor deepseek,gemini --rounds 20
python3 lab/favour.py --render games/favour/records/<folder>/game.json
```

## What "contest" means here

I used the word loosely last night, so I will define it and then check the game against the definition. A game
is a contest when **no action guarantees its player a non-loss** — when every move you can make can be beaten
by some move the other player can make. If one move cannot lose, the round stops being a decision: a rational
player takes it every time and the game is decided somewhere else.

Checked mechanically, for one round, printing the result of each throw against every legal opponent throw:

```
ban rule, scissors banned:        favour rule, rock favoured:
  rock     draw, loss               rock      draw, loss, win
  paper    win, draw   <- never loses
```

Under the ban, paper cannot lose, so rock is never worth playing and the round is over before it starts. Under
the favour rule every throw can be beaten, and each is the best answer to exactly one opponent throw: rock to
scissors (doubled, because it is favoured), paper to rock, scissors to paper. Nothing is dominant, so the
choice depends on what the other player does — which is what a contest is.

Two things that are *not* the definition, and that I leaned on too hard:

- **A close score.** Two beings throwing at random produce 28–27 as easily as 40–15. The margin was the
  weakest evidence of the three I gave and I should have led with the dominance check.
- **Unpredictability.** Calls right fell to 6 and 5 of 20, at chance — but a game can be a contest between two
  players who read each other perfectly. Chance-level calls say there is no forced pattern to exploit, not
  that the play is good.

What the close score does show, given the other two checks, is that neither being found a strategy the other
could not answer: Colette chased the favoured throw nine times, Remy once, and neither run of nine or one was
punished consistently. That is the state a contest is supposed to be in.

## What this does not show

One pairing, twenty rounds, and four points a round is a scorecard I invented — not a discovered law. The
useful comparison is against the two games filed in `games/word/records/`, which used the same engines, the same
four lines and the same clock: the only differences are the ban and the fourth line's price, and the score went
from 16 points apart to one.
