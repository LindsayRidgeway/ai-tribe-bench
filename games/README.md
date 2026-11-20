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
| `pickleball/` | `lab/pickleball.py` (not yet written) | **design page, 2026-11-15** | the sport with a kitchen, a double-bounce rule and doubles: the player moves, the paddle contacts, the engine computes the ball — one integrator, imported from `lab/tennis.py`, never copied | the ball's `Cd` is flat over the whole range (0.33 outdoor, 0.45 indoor), `k` = 0.0103/ft against tennis's 0.0063; below 22 mph no ball reaches the backcourt; the third-shot drop's window is 0.5°–3.5°, which is smaller than the 1.2° the drag constant is uncertain by — so the measured ball comes before the dink game |

The four sport games (`tennis/`, `pickleball/`, `putt/`, `golf/`) are not in the table above because their
subject is a moving ball rather than a choice; each is indexed in its own `README.md`. Two of them now carry a
renderer, and both are self-contained pages with the scene baked in: `tennis/replay3d.html` and, since
2026-11-19, `golf/renders/the-face.html` — three shots at a bunker's face, which is the first thing in either
game that a still frame could not say. `golf/` (2026-11-19) is the first of them whose subject is a *bag*: six clubs whose
distances the athlete has wrong, five gears each, and a nine-hole course that only ever asks for some of them.
It is also the first that has been argued *against* by its own author, twice: a fourth pass built the bunker its
third pass asked for and got nothing, and a fifth pass built the bunker's face, made sand five times dearer, and
got nothing again. It rests there, on the condition it set for itself in advance: what is left needs a law
invented rather than a measurement taken. What it does while it rests is not physics: a field of six on one
card, a film of the face, and — on 2026-11-19's eighth pass — the demolition and repair of a number it had
been getting wrong about itself since the second pass, which halved its best aiming result and doubled the bar
on it. The game is the only one of these that has audited its own athlete rather than its own physics, and it
found more that way — and a ninth pass took the floor out from under that number and found that what had been
hiding behind it was not the athlete at all but a step function in the objective, which is the first time any
of these games has found a defect in *its own scoring rule* rather than in its physics or its player. The
tenth pass then wrote that rule in the game's own units and the defect turned out to be one surface deeper: the
putter has no scatter, so every putt costs two strokes from any distance, so the green has no gradient and the
objective that replaced the step function is nearly flat too. It is the most specific thing any of these games
has found — not a missing force but a missing *dispersion*, on the one surface nobody thought to check. And the
eleventh pass put the dispersion in and found that the count was wrong: giving the putter hands exposed an
athlete that had never been given *eyes* (it aimed at the hole on a green falling 1.2%, and missed by a foot and
a half from twenty feet) and, behind that, a putter that aims to die at the cup and therefore cannot hole half
its three-footers. Three missing things, one of them built, one built, one measured and named — and the short
game is now the biggest single thing wrong with any game in this directory. The twelfth pass built the third:
the putter now decides how far past the cup to aim from what it has learned about its own scatter, and the green
starts costing what golf's greens cost (1.00 at 2 ft, 1.93 at 20). It also found that two of the game's own
instruments had been reading the wrong thing — a cost table whose "distance" was distance from the green's
centre, and a price check that ran forty trials on one seed — which is the third time this game has caught a
defect in the measuring rather than in the physics. The thirteenth pass put that curve into the objective, and it
found four things at once: a fourth instrument reading the wrong thing (the same cost table, now read as a curve
when the number of positions it samples was falling with distance), a bug in its own first version that made every
ball in the rough aim at the widest target it could find, the first target decision the short game has ever had
(three quarters of a stroke at 30 ft, because a chip is all distance and the objective could not see distance), and
the reason four passes of bunkers have failed to change the aim — the objective's landing always arrives at the
pin's distance, so it thinks the sand is reachable 42% of the time where the game makes it 11.6%. What is left of
golf is that: one dimension, and a scatter that is a number instead of a vector. The fourteenth pass is the first
one with something to look at: `python3 lab/golf.py --season` writes `golf/renders/season.html`, six athletes over
eight rounds with each one's belief about itself drawn beside its card, and a band across four practice sessions —
a page that opens from disk with no script in it at all. The fifteenth pass is the film: `--render 7` no longer
films a hole from one mount behind the tee. Two tracking cameras were built and photographed and thrown away — a pan
that centres the ball cannot hold the hole, and a telephoto turned the picture into a green screen — and what
replaced them solves the frame instead: the camera stands off the shot far enough to hold the flight and the green,
the horizon stays in shot, and the shot tracer is what the eye follows, because a 1.6-inch ball a hundred feet away
is a pixel and no framing can make it more. `--render round` plays the athlete's own nine holes as one film,
`--render worst` and `--render best` play the hole the card says went worst and best, and the ball now finishes where
the game says it stopped rolling instead of where it stopped flying — a twenty-five-yard disagreement between the
caption and the dot that had been on the same page for nine passes. The sixteenth pass puts the putts in the film:
`putt.roll()` traces its own line, each putt is photographed from above because a putt is a line on a surface and
nothing else, and the cup stops being a three-pixel symbol. Two checks now guard the picture rather than the golf —
that the film's line ends where the card says the ball stopped (it failed at two inches, and the two inches were a
bearing taken off the bounce), and that the line is the green's rather than a ruler (0.56 ft of bow on the 1.2%
green, zero on it flattened). The seventeenth pass is the door: `--start` writes `renders/start.html`, which reads
`season.json` and cannot print a mean without its standard error, and `FOR-BETA.md` holds what is known wrong, dated,
one click below the product rather than on its face.

## Which to keep, and why

`favour/` is the game. `order/` is the next one, and the only one whose subject is learning rather than
temperament. `word/` and `wind/` are kept because their records are the evidence for findings cited elsewhere —
deleting them would leave the conclusions standing on nothing. `rps/` and `dice/` are kept as the control and
the apparatus: what a game looks like before anyone is talking, and what a record looks like before anything is
at stake.

`ATHLETES.md` is the queue of games not yet built: one lever, one number back, and the reason tennis
teaches while rock-paper-scissors cannot. It is a design file, not a game.

The baseball and football experiments (`experiment/mlb/`, `experiment/rank/`) are not games and stay in
`experiment/`, with the task files that run them.
