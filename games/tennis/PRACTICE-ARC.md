# Watching a player learn — `lab/practice_arc.py`

The founder, 2026-11-12: *"Think how cool it will be to see players get better with practice."*

Everything in this engine was already a function of balls hit — `skill()` is asymptotic in practice, movement speed
is built on it, the serve's pace, its placement and its fault rate are built on it, the racquet goes back earlier,
the errors shrink. What was missing was a way to *look*. `lab/practice_arc.py` plays the same forty points at seven
career lengths and writes three films of the same twenty points, so the claim is something to flip between rather
than a paragraph in a design note.

Same court, same wind, same clock, same pair. The only thing that differs is how many balls they have hit before
today.

| balls before today | rating | mean rally | longest | balls reached | mean run | first serve | double faults |
|---|---|---|---|---|---|---|---|
| 0 | 1.00 | 1.48 shots | 4 | 90% | 10.6ft | 55mph | 24 of 40 |
| 25 | 2.13 | 1.85 shots | 5 | 89% | 12.4ft | 58mph | 15 of 40 |
| 60 | 3.36 | 1.85 shots | 6 | 87% | 12.4ft | 64mph | 21 of 40 |
| 120 | 4.79 | 2.08 shots | 6 | 98% | 12.2ft | 69mph | 16 of 40 |
| 250 | 6.25 | 3.00 shots | 10 | 94% | 11.8ft | 72mph | 7 of 40 |
| 400 | 6.79 | 4.08 shots | 12 | 95% | 11.9ft | 75mph | 4 of 40 |
| 700 | 6.98 | 5.38 shots | 19 | 96% | 12.6ft | 74mph | 0 of 40 |

Two columns move for the whole length of the table and are visible in the picture without a single number on
screen: the serve gets faster (55 → 74mph) and the double faults go from most of their points to none. Rally length
rises across the career but not in a straight line, and the old version of this table overstated the smoothness of
it. Forty points is a small sample, the random stream is not the same at each level, and since the one-serve rule
(2026-11-12) a fault is a lost point — so one bad serving day at level 60 reads as a short rally. What is not noise
is the ends: at zero practice there is no rally to watch, and at seven hundred there is a nineteen-shot one.

The *reason* a point ends changes species, which is the part a table cannot show and the film can.

## The three films

| file | balls | rating | what you are watching |
|---|---|---|---|
| `demo3d-000.html` | 0 | 1.0 | 29 shots in 20 points, 12 double faults; slow serves; the return goes into the net |
| `demo3d-120.html` | 120 | 4.8 | 41 shots, rallies exist — the serve lands, the ball comes back three times |
| `demo3d.html` | 400 | 6.8 | 95 shots, 75mph serves, 2 double faults, one rally of 12 |

Two films would have been the obvious choice and the wrong one: the two ends of a career are not a comparison,
because at zero practice there is no tennis in the film at all. The middle one is what a month of Sundays buys.

## What "better" means, mechanically

None of this is a curve drawn on the table. Each column falls out of `Player.skill()`, which is
`1 − exp(−(practice + shots)/120)` for `control`, `reach` and `sweet`, and a slower curve with a sixty-ball onset
for `prep`:

- **serve pace and placement** — `SERVE_MPH`, scaled by `control`, so a beginner serves 55mph and misses the box
  more often than not: with one serve per point, 24 of their 40 points are a double fault;
- **movement** — `5 + 15·reach` ft/s, which is what the renderer walks the legs at, so the beginner crosses the
  court at 10ft/s and the practised player at 19;
- **reaction** — `0.26 − 0.15·reach` seconds, which is the difference between being beaten to a ball and reaching it;
- **the racquet** — `prep` decides whether it comes back while running, and the renderer uses it.

Every column moves in the direction a coach would want, and the *reason a point ends* changes species, which is the
part a table cannot show and the film can. At zero practice the point is lost by the beginner: double fault, or the
ball in the net, and nobody has to win it. At four hundred balls the points are lost to a ball that could not be
reached, or to an aim that came off the side of the court. A beginner has the point taken off their own racquet;
a practised player has it taken off them.

One caveat worth keeping, because it is the honest half of the "better players miss more" argument: past a certain
point placement shortens rallies as fast as fitness lengthens them, and the table can then go either way. This run
has 5.38 shots at seven hundred balls against 4.08 at four hundred; the run before the one-serve rule had 4.25
against 5.05, the other way round, on the same code path and a different random stream. Forty points does not
settle a question that size. The claim the arc supports is the one the founder made — that a player visibly improves
— and not the finer claim that every column improves monotonically, which it does not.
