# golf — a bag, a course, and the number that says which club was wrong

Built 2026-11-19 by Dmitri, from the founder's suggestion of the same day. The tool is `lab/golf.py`;
the run is `records/golf-2026-11-19.txt`; the checks are `python3 lab/golf.py --selftest` (11 of them).

    python3 lab/golf.py                  # six rounds of nine, then six holes never played
    python3 lab/golf.py --learn 0        # the control: same athlete, same seed, never updated
    python3 lab/golf.py --selftest       # the numbers below, checked

## The question, and why it is not "putt, from further away"

`games/putt/` closed one loop: two levers, two unknown numbers, bisection on the printed miss. Golf that
copied that would teach nothing, because a green with a longer putter on it is the same problem.

What is different about golf is that the athlete does not know what its tools do:

    on the green   one tool, two numbers, learned by bisection;
    on the course  six tools at five gears each, and it has to be told — or find out — what all of them do,
                   while the shot it hits now decides the problem it faces next.

So this game's levers are **which club** and **which gear** (a full swing, 80%, 60%, 45%, or the chip), its
number back is the one a golfer reads off the fairway — how far short or long, how far left or right, in yards
— and the thing it must build out of those numbers is a notebook: thirty entries, every one of them wrong to
start with.

The queue in `games/ATHLETES.md` had this as *"golfer's drive — face, launch → carry and how far off the
fairway centre"*. That is one shot, and one shot cannot teach a course: there is no second shot to be worse
because of the first. The bag and the course are the addition, and they are the whole of the game.

## The course

Nine holes, one straight corridor, par 35: 410, 165, 520, 300, 145, 385, 95, 450, 500 yards. Fairway 40 yd
wide; rough to 35 yd off the centre line, where a ball leaves the club at 88% of its fairway speed; beyond
that, trees — one stroke and a drop at the edge. A 60 ft green: inside 30 ft of the flag the putter comes
out, and it is `games/putt`'s putter and `games/putt`'s friction law, imported, not re-modelled. Par is the
hole's, and twelve strokes picks the ball up.

Wind is calm. The course has no bunker, no water and no dogleg, and those are three of the four things that
make a real course a course. They are on the list below, not silently absent.

## The athlete

Scripted, no model calls, and it is told everything a player can see: the distance to the flag and the lie.
It carries:

    table[club][gear]   what this club has done for me at this effort, in yards

Every entry starts at what a beginner believes — the bag this model gives, scaled per club by an invented
`INHERITED` (too much faith in the 7-iron, 1.10; none in the sand wedge, 0.88) and scaled *linearly* in gear
(hit it twice as hard, go twice as far). Every fairway shot replaces the entry it was hit with by the running
mean of what that club and that gear actually did. The second thing it learns is smaller and costs more
strokes: the ball leaves its clubface 2.2° right of where it aims, and it estimates that angle from the side
of its misses and aims off it.

It hits a gear, never something in between, because a player's repeatable shots are the named ones — and
because an athlete that can hit any effort exactly can always reach the flag, and then its distances never
matter.

**An earlier version fitted distance = k·effort^p by least squares.** It fitted badly, and the reason is the
most useful thing this build taught me: with a bag of full swings the observations sit at nearly one effort,
so k and p trade off against each other and a wrong pair still explains every number in the book. The table
cannot make that mistake, and it is also what players keep.

## The physics: what is calibrated, what is measured, what is invented

The ball is `lab/tennis.py`'s integrator with golf's constants passed in; the roll is `lab/putt.py`'s
friction law, a = STIMPMETER²/(2·stimp). One integrator, one roll law, no second copy of either.

| check (selftest) | model says |
|---|---|
| vacuum range, 45° at 100 ft/s | **310.92 ft** against v²/g = 310.85 |
| drag, same launch | **231.6 ft** with drag against 310.9 without |
| backspin | 2686 rpm is worth **+113.6 yd** of carry at the same drag |
| the bag, full swing, carry + run | driver **295**, 3 wood 274, 5 iron 210, 7 iron 183, 9 iron 154, sand wedge 122 |
| calibration residual | worst club **8.5 yd** off its prior carry |
| roll law | 6.0 ft/s rolls **10.00 ft** on a 10 stimp, exactly putt's |

**Nothing here was measured on a launch monitor.** The six clubs' ball speeds, launch angles and spin rates
are priors from published tour averages; the four drag/lift constants (Cl = min(0.131, 1.68·S), Cd =
min(0.284, 0.188 + 0.469·S), where S = ωr/v) were *fitted* until those six priors came out. The residual is
printed so the size of the assumption is visible. A model calibrated to a table is only as good as the table,
and it is not evidence about a real golf ball. No finding below rests on the model being right about physics;
they rest on it being consistent, which the first six checks test directly.

That third row deserves its warning. A hundred and fourteen yards from spin is a lot, and it is what the
model needs to turn a 231-yard vacuum drive into a 263-yard carry. It is also the strongest hint that the
lift model is too generous at low spin ratios. It does not change any finding — the game's numbers are the
athlete's notebook, not the ball's — but a reader should treat the flight numbers as a consistent fiction.

Strike dispersion is a prior too: 1.1° of clubface error and 1.5% of ball speed, drawn from a fixed seed
(20261119). **Every round replays the same sequence**, so two rounds differ only in what the athlete knows.

## What six rounds printed

Same course, same seed, one athlete learning and one frozen.

| | 1 | 2 | 3 | 4 | 5 | 6 | held-out | notebook error |
|---|---|---|---|---|---|---|---|---|
| **learning** | +11 | +1 | +2 | +3 | **0** | **0** | +3 | 7.9 → 2.2% |
| **control** | +6 | +6 | +6 | +6 | +6 | +6 | +5 | 24.3% flat |

*to par over nine holes (par 35); held-out is six holes never played (par 22). Notebook error is |what the
notebook said| against |what the shot did|, over every shot in the round.*

Putts: 27, 18, 19, 22, 19, 19 for the learner; 17 every round for the control. In the selftest, where the
athlete plays until it has 12 entries hit twice or more, the notebook is **1.3% off on average**.

### Three findings

1. **Learning costs a round before it pays.** The first round is five strokes worse than never having
   practised (+11 against +6), and it is the putts: twenty-seven of them against seventeen. A wrong notebook
   does not just miss the flag, it misses it into places where the next shot is harder. After that the
   learner is four to six strokes a round better than the frozen player and settles at par.
2. **The notebook converges only where the course asks it a question.** Twelve entries settled to 1.3% mean
   error; the sand wedge's *full swing* was never played in three rounds and stayed at 107 against a true
   122 — twelve per cent wrong, untouched, because nothing in the round ever called for it. A course is not
   a test of a bag; it is a test of the shots that course asks for, and the held-out holes (+3 against the
   control's +5) are a weak probe of the rest.
3. **A coarse gear ladder hides a wrong notebook.** The control's notebook is 24% wrong on every shot and it
   still scores +6, because it can only hit thirty numbers anyway and picking the nearest one to the flag is
   nearly as good with a bad table as with a good one. What the notebook buys is the last few yards, not the
   ability to reach — which is worth saying plainly, because "six clubs you have to learn" sounds like a much
   harder game than the numbers make it.

### One instrument that failed

The mean miss to the flag is about **50 yd for both players** and tells you nothing: on a 410-yard par 4 the
first shot is a driver that cannot reach, and its 115-yard "miss" swamps every good approach on the card. A
verdict number (strokes) is coarse and a miss in yards is dominated by the longest shot on the hole. The
number that actually shows learning is the notebook's own error, which is why it is the one in the table.

## What this does not model

- no bunker, water, dogleg, tree line, or green contour; one slope for every hole
- no wind in a round (the engine takes it; the course does not use it)
- one lie effect — rough costs 12% of ball speed — and no flyer, no buried ball, no uphill or downhill stance
- putting is 2-D and flat-sloped; a putt that misses the green keeps rolling as if it were on one
- a 35% wedge is modelled with the same 1.1° face error as a driver, which is generous to the short game
- twelve strokes and the ball is picked up; the card records +4 and moves on
- one athlete. Golf's other half — a field, a cut, a card that is read against other people's — is not here

## What would come next, in order

1. **Wind, and a lie that is not flat.** Both are one number each and both are already parameters of the
   engine; the course is what refuses to use them. This is the cheapest way to make the notebook wrong in
   more interesting ways.
2. **A caddie's question, not a club's.** The interesting decision in golf is not "which club" but "where am
   I willing to miss", and this athlete never chooses a target — it chooses a distance. A target is a third
   lever, and it is the one a member would learn something about.
3. **The picture.** A golf render is cheaper than a tennis one: one ball, one flight, a camera behind the ball,
   no opponent, and the whole shot is over in six seconds. `games/tennis/replay3d.html` is the template and
   `lab/tennis.py`'s `trace=` is the data. It should be built when there is a round worth watching, not
   before — a renderer aimed at a game nobody has played is a demo with a camera.
