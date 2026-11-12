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
| 0 | 1.00 | 2.62 shots | 7 | 84% | 11.3ft | 51mph | 15 of 40 |
| 25 | 2.13 | 2.58 shots | 7 | 89% | 11.7ft | 56mph | 19 of 40 |
| 60 | 3.36 | 2.38 shots | 5 | 89% | 13.3ft | 58mph | 11 of 40 |
| 120 | 4.79 | 2.90 shots | 7 | 90% | 13.1ft | 63mph | 7 of 40 |
| 250 | 6.25 | 3.83 shots | 15 | 89% | 12.4ft | 70mph | 0 of 40 |
| 400 | 6.79 | 5.05 shots | 18 | 92% | 12.0ft | 72mph | 0 of 40 |
| 700 | 6.98 | 4.25 shots | 14 | 91% | 11.9ft | 74mph | 1 of 40 |

Three things move monotonically and are visible in the picture without a single number on screen: the serve gets
faster and stops missing, rallies get longer, and the *reason* a point ends changes completely — a beginner nets the
ball or double-faults, a practised pair loses the point to a ball they cannot reach.

## The three films

| file | balls | rating | what you are watching |
|---|---|---|---|
| `demo3d-000.html` | 0 | 1.0 | 44 shots in 20 points, 12 double faults; slow serves; the return goes into the net |
| `demo3d-120.html` | 120 | 4.8 | 49 shots, rallies exist — the serve lands, the ball comes back three times |
| `demo3d.html` | 400 | 6.8 | 109 shots, 72mph serves, no double faults, one rally of 18 |

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

Every column moves in the direction a coach would want, and the *reason a point ends* changes species, which is the
part a table cannot show and the film can. At zero practice the point is lost by the beginner: double fault, or the
ball in the net, and nobody has to win it. At four hundred balls fourteen points in forty are lost to a ball that could not
be reached, or to an aim that came off the side of the court. A beginner has the point taken off their own racquet;
a practised player has it taken off them.

One caveat worth keeping, because it is the honest half of the "better players miss more" argument: at the very top
the effect is real and only just outweighed. By seven hundred balls the rally length has stopped climbing — 4.25
against 5.05 at four hundred — because better hands win points that better legs would only have kept alive. The curve
is not a straight line up, and it should not be: past a certain point, placement shortens rallies as much as fitness
lengthens them.
