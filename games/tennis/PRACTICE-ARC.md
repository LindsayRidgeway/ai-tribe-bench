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
| 0 | 1.00 | 2.42 shots | 5 | 91% | 11.9ft | 54mph | 16 of 40 |
| 25 | 2.13 | 2.58 shots | 5 | 93% | 12.1ft | 58mph | 9 of 40 |
| 60 | 3.36 | 2.33 shots | 4 | 89% | 12.8ft | 59mph | 10 of 40 |
| 120 | 4.79 | 2.75 shots | 9 | 85% | 12.7ft | 64mph | 4 of 40 |
| 250 | 6.25 | 2.60 shots | 7 | 80% | 13.7ft | 69mph | 1 of 40 |
| 400 | 6.79 | 3.55 shots | 9 | 89% | 13.0ft | 72mph | 0 of 40 |
| 700 | 6.98 | 4.70 shots | 14 | 88% | 12.5ft | 73mph | 0 of 40 |

Three things move monotonically and are visible in the picture without a single number on screen: the serve gets
faster and stops missing, rallies get longer, and the *reason* a point ends changes completely — a beginner nets the
ball or double-faults, a practised pair loses the point to a ball they cannot reach.

## The three films

| file | balls | rating | what you are watching |
|---|---|---|---|
| `demo3d-000.html` | 0 | 1.0 | half the points are double faults; slow serves; the return goes into the net |
| `demo3d-120.html` | 120 | 4.8 | rallies exist — the serve lands, the ball comes back three times |
| `demo3d.html` | 400 | 6.8 | 72mph serves, no double faults, and the point is won by hitting where the other is not |

Two films would have been the obvious choice and the wrong one: the two ends of a career are not a comparison,
because at zero practice there is no tennis in the film at all. The middle one is what a month of Sundays buys.

## What "better" means, mechanically

None of this is a curve drawn on the table. Each column falls out of `Player.skill()`, which is
`1 − exp(−(practice + shots)/120)` for `control`, `reach` and `sweet`, and a slower curve with a sixty-ball onset
for `prep`:

- **serve pace and placement** — `SERVE_MPH`, scaled by `control`, so a beginner serves 54mph at the corner they
  cannot hit and double-faults 40% of the time;
- **movement** — `5 + 15·reach` ft/s, which is what the renderer walks the legs at, so the beginner crosses the
  court at 10ft/s and the practised player at 19;
- **reaction** — `0.26 − 0.15·reach` seconds, which is the difference between being beaten to a ball and reaching it;
- **the racquet** — `prep` decides whether it comes back while running, and the renderer uses it.

The one column that does *not* improve and is not supposed to is "balls reached": a practised pair misses more balls
than a beginner because they hit the ball where the other player cannot get to it. At zero practice nobody is
beaten to a ball — the points are lost by the beginner, not won against them. That inversion is the whole difference
between the two levels, and it is the reason the table is worth looking at.
