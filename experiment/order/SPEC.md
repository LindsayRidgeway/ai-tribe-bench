# The Hidden Order — a game whose strategy can only be learned by playing

Design note, 2026-11-04. Lindsay's brief:

> one of them practices and learns strategies that can only be learned with practice... Can you devise a game
> where winning strategy has to be learned with practice?

## Why the previous games fail this test

Rock-paper-scissors cannot test learning, because the table is in the model's weights. Ask a being to play it
and it already knows rock beats scissors; twenty rounds teach it nothing, and "practice" would have to mean
something the model cannot do. That is the trap in every game in `experiment/wind`, `experiment/word` and
`experiment/favour`: they measure temperament, reading and nerve, never learning.

**A game can only require learning if the strategy is not derivable.** So the rules must be hidden, arbitrary,
and different every match.

## The rules

Four signs, `A B C D`. At the start of a match the clock draws a hidden **order**: for each of the six pairs,
which sign beats which. There are 2⁶ = 64 possible orders. Nothing about the letters hints at the structure,
there is no cycle rule to remember, and a model's knowledge of rock-paper-scissors is worth nothing.

Each round the clock offers one pair — say `B` and `D` — and both players choose one sign blind. The winner
takes a point. The result is revealed, so **each round teaches exactly one relation**: this time `D` beat `B`.

Twenty rounds, six relations. A player who has never seen this order can only guess; a player who has played
it before knows the table and cannot be beaten on an even score.

**Practice** is the part that makes it a demonstration rather than a puzzle: before the match, one player plays
a practice match on the same hidden order, and its record — what it learned — is carried into the real match.
The other arrives empty. Same engine, same prompt, same clock. The only difference between them is what they
have learned.

## The three arms

| | players | what it shows |
|---|---|---|
| 1 | two beginners, even | the control: neither knows the table, the result is noise |
| 2 | practised vs beginner, even | the practised player should win nearly always, because it knows and the other guesses |
| 3 | practised vs beginner, handicapped | the beginner gets points at the start, and has a chance again |

**The handicap is the measured differential**, golf's rule: play arm 2 first, take the median margin, hand it to
the beginner in arm 3. Go's stones and a golfer's handicap are the same idea — you move the score, not the play.

**The metric that keeps it honest is skill, not score.** Count, for each player, the fraction of rounds in
which it chose the sign that actually wins the offered pair. The handicap moves points; it cannot move this
number. If the practised player is still choosing right on 100% of rounds while losing on points, the handicap
is doing what a handicap does.

## The arithmetic, simulated

`lab/order.py` prices the handicap with scripted players — a learner that starts empty and updates one relation
per round, against the same learner handed the table. Two thousand matches of twenty rounds, 64 orders:

| | |
|---|---|
| arm 2, even terms | practised wins **100%** of matches, median margin **+5 points** |
| skill, before any handicap | practised right on **100%** of rounds, beginner **75%** |
| arm 3, handicap 5 | beginner wins 28%, draws 43%, practised wins 29% |
| arm 3, handicap 4 | beginner 5%, practised 72% |
| arm 3, handicap 6 | beginner 71%, practised 0% |

So the dial is one point wide, which is why the handicap wants **half points** (or drawn matches split): the
interesting setting is between 5 and 6, where the beginner has a real chance and the practised player still
wins most scored matches. The beginner's 75% is not zero because pairs repeat and it learns during the match
too — which is the point: learning is happening, just too late to matter over twenty rounds.

## What this does not show

The two players in that simulation are not minds. One is a table lookup and the other is a one-bit-per-round
learner, and they were built to make the handicap arithmetic checkable before anybody spends a key. What the
numbers establish is the shape: a hidden table makes practice decisive, and points are the right currency for
evening it.

Whether a real model can learn the table in twenty rounds is the experiment, and it may go either way. A model
that reasons well might infer more from six observations than my toy learner does; a model that reasons well
and is shown the practice record may simply be told the table and stop learning anything. Both outcomes are
findings, which is the reason to run it.

The other design Lindsay named — pick a stronger model by reasoning rating and give the weaker one bonus
points — measures **reasoning**, not learning, and should be run as a separate arm rather than mixed into this
one. The two questions are different: one is whether practice pays, the other is whether a better reasoner
wins. Mixing them would leave neither answered.
