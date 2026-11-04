# The games

One folder per game that is kept. Each holds its rules in `README.md` and every match ever played in
`records/<match>/`, with the per-round files exactly as they were written: for the talking games, both beings'
four lines filed separately before the round was scored, so the exchange is in the order it happened.

The tools are not in these folders. They live in `lab/` because they share one vendor table and one clock rule
(`lab/rps.py` and `lab/wind.py`), and a second copy of a thing is how this repository has been broken before.
Each game below names the tool that plays it.

| game | tool | status | what it is | what it found |
|---|---|---|---|---|
| `favour/` | `lab/favour.py` | **current** | four lines a round (`WORD CALL THROW SAY`), the clock *favours* a throw, four points: right call, winning throw (doubled if favoured), kept promise, sentence believed | Remy 28–27 Colette. No dominant move, so the throw is a decision; temperament shows in a choice (Colette chased the favoured throw 9/20, Remy 1/20) |
| `word/` | `lab/word.py` | superseded by `favour/` | the same four lines, but the clock *bans* a throw and a promise kept is worth double | Remy 9–25 and 11–29 Colette. The ban left a safe throw nobody could beat, so the throw column was a forced move; the defect is the reason `favour/` exists |
| `wind/` | `lab/wind.py` | superseded by `word/` | three lines a round (`CALL THROW SAY`), ban, points for a right call and a winning throw | Remy 10–20 Colette, Remy 14–17 Margot. 11/20 and 12/20 rounds were draws on the throw the ban left standing: the first evidence that the wind, not the beings, was deciding |
| `rps/` | `lab/rps.py` | retained as the control | sealed rock-paper-scissors, one word a round, twelve to twenty rounds | the first experiment two browser tabs cannot run: throws must be simultaneous. Also the sharpest published correction — the summary said 0W 5D 7L above a table showing five wins |
| `dice/` | `lab/dice.py` | retained as the apparatus, not a game | twenty rounds decided by a seeded generator: no model, no preferences | different sheet every run, identical from the same seed, hash-chained. It shows the filing cabinet works — which is why a demo made of it showed nothing |
| `order/` | `lab/order.py` | **spec, not yet played** | four signs, a hidden order drawn per match, so the winning strategy can only be learned by playing; a handicap priced from the even-play margin | simulated: a practised player wins 100% on even terms and is right on 100% of choices against 75%; a five-point handicap gives the beginner about a third of the matches and moves no skill |

## Which to keep, and why

`favour/` is the game. `order/` is the next one, and the only one whose subject is learning rather than
temperament. `word/` and `wind/` are kept because their records are the evidence for findings cited elsewhere —
deleting them would leave the conclusions standing on nothing. `rps/` and `dice/` are kept as the control and
the apparatus: what a game looks like before anyone is talking, and what a record looks like before anything is
at stake.

The baseball and football experiments (`experiment/mlb/`, `experiment/rank/`) are not games and stay in
`experiment/`, with the task files that run them.
