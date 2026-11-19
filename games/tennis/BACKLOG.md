# BACKLOG — the tennis game's V1, one item per wake

Written 2026-11-15 because of a fact I had to establish first, and did not like: **the game has not
been touched by a wake in three days.** Ten wakes since 2026-11-12 went to the symposium's review
queue, and the file I told the founder would carry this work — this file — did not exist in any clone
or any branch. A plan that is only in a chat is a plan that runs when somebody types.

Two rules for using this file, and both are here because of a defect already paid for:

1. **One item per wake, and it is the wake's deliverable** — not maintenance alongside the queue
   (`to-do-lists/README.md` rule 7 and rule 8). Item-sized means one item, with its done-test.
2. **Commit before you stop.** On 2026-11-11 and 2026-11-12 I did a day of renderer work — the serve,
   the point caption, the net headband and strap, `?record=`, `run_season.py`, the movement fixes —
   and none of it is in git. It is not on disk in any clone today. See item 0. Ninety minutes of work
   with no commit is ninety minutes of work that a `git checkout` deletes.

Each item below has a **done-test** and **the number that proves it**, because the failure mode of
unsupervised work is a plausible change with nothing measured behind it.

---

## Item 0 — the renderer work was never lost, it was never pushed (CLOSED 2026-11-15)

*The diagnosis in the previous version of this file was right about the disease and wrong about the patient.
It said eight paths existed in no commit and no clone, and that recovery meant rebuilding them from a session
transcript. They existed — in a local clone, on a branch that had never been pushed. What was true is the
cause: `desi-state.md`'s 11-11 and 11-12 entries describe work done and committed **locally only**, and a wake
runs `git reset --hard origin/main` in that shared checkout. On the morning of 2026-11-15 the reset arrived:
`games/tennis` fell back to README, SETUP, `records`, `seasons`, and the Spotlight launcher was pointing at a
file that no longer existed. The reflog still had the commits.*

**Found, not recovered:** `replay3d.html` at 1730 lines (the other line has 682), `serve_corners`,
`WINPOS`, `?cam=net`, `?record=`, `?setup=`, `run_season.py`, `STILLS.md`, `MATCH-FORMAT.md`, the net
headband and strap, the arm solver, `__pose/__seek/__seg/__audit`, and the movement work above this item —
plus everything since: the carry, the plant, the forehand sheet.

**Pushed, which is the actual fix:** `origin/desi/plant-2026-11-15` (and from 2026-11-15, this branch).
**The rule, for every body:** *commit is not saving. Push before you report.* A commit that lives only in the
shared checkout is deleted by the next wake, and no number in any probe will tell you it happened.

## Item 1 — put the renderer on `main` (OPEN; the biggest item)

`desi/tennis-video` is now **this line**: the full renderer, and fast-forward-merging it leaves its own history
intact (its unique commits were two edits to this file, which are folded in here). What is still true is the
thing that matters: **`main` has no game.** `origin/main` carries the trunk — heartbeats, connect, the wizard,
everybody's fixes — and ten files under `games/tennis`, none of them a page.

Two ways, and the choice is a judgement rather than a merge:

- **Rebase this line onto `main`** and merge. The earlier attempt conflicted in twelve files (`tests.py`,
  `tribe.py`, `plates/README.md`, a rename/delete on `wake/members`) because this line split off the trunk on
  9 November — so the conflicts are six days of other people's work meeting an old copy of their files. Resolving
  them means reading each one; it is not mechanical.
- **Rebuild on `main`** by taking `games/tennis` whole from this branch (128 files against `main`'s 10) and
  leaving every other path at `main`. That is one command, it cannot damage anybody's work outside `games/tennis`,
  and it makes `main` the game's home today. The cost: this branch's unrelated trunk history is not carried over.

**My decision: the second, now** — because `main` holding no game is the failure that let one `reset --hard`
look like a catastrophe, and because a second copy of the trunk is not worth twelve hand-merged conflicts. The
history stays on this branch for anyone who wants it.

- **Done-test:** `git ls-tree origin/main --name-only games/tennis/replay3d.html` returns the path; the page
  serves from a fresh clone; `python3 tests.py` no worse than its known red. **Number:** files under
  `games/tennis` on `main`, 10 → 128.

## Item 2 — the first-frame pop (founder's item 1)

His words, 2026-11-12: the figure pops 0.4–0.7 ft at the first frame of every shot because the
take-back is not posed — the body arrives at the contact pose and the racquet is already swinging.

- **Done-test:** across 20 shots drawn from the spring season record, the figure's root position at
  frame 0 and frame 1 differ by less than 0.05 ft, and the racquet head is never more than 0.3 ft
  from the ball on the contact frame (the lerp defect from 11-10, which put no racquet on the ball in
  any frame). **Number:** max delta at frame 0 in ft, before and after.

## Item 3 — split step
- **Done-test:** every shot in a 20-shot sample is preceded by a downward root-velocity blip of
  0.10–0.20 ft within 0.2 s of the opponent's contact. **Number:** the median delay from opponent
  contact to the blip, and the fraction of shots that have one (target 20/20).

## Item 4 — cross-over step
- **Done-test:** on a shot that needs more than 3 ft of travel, the first foot to leave the ground is
  the one *nearest* the direction of travel, and the feet cross rather than shuffle. Checked on 10
  shots in each direction. **Number:** 20/20, with the offending shots listed if not.

## Item 5 — brake
- **Done-test:** root speed at the contact frame is under 0.5 ft/frame for a shot reached at a run,
  i.e. the body is not still sliding when it hits. **Number:** peak speed and contact speed per shot.

## Item 6 — turn-back
- **Done-test:** after the shot, the figure's facing is back towards the centre of the court within
  1.2 s, and the recovery run does not cross the shot's own path. **Number:** seconds to re-face, per
  shot; the fraction with a crossed path (target 0).

## Item 7 — the scoreboard (his spec, 2026-11-11)
Two rows: Sets, Games, Points — with 0/15/30/40/AD and "Game" for the row that takes it, written up in
`MATCH-FORMAT.md` with the note that a zeroed table for a match nobody is playing would be a lie.

- **Done-test:** a scripted match ending 6-4 3-6 7-5 renders the table correctly at 12 sampled
  points, including one deuce and one AD. **Number:** 12/12, and the state of the table at each.

## Item 8 — the person's seat, in the renderer
The engine half landed in `main` (`e20c61bf`: a typed movement, no engine, one verdict). The renderer
does not yet show a person's entry beside a member's.

- **Done-test:** a season record containing one person entry and one member entry renders both, with
  the person's typed movement visible in the caption and no engine named. **Number:** 2/2 rendered.

## Item 9 — PaddleBall: accepted, and gated behind item 1

The founder raised it on 2026-11-15 and then said why the record had no trace of it: *"that's a comment
on the lack of communication in the symposium."* He is right about the cause, and it is worth stating
plainly because it will happen again. Something said in a live window is in the record only if the seat
that heard it writes it down. PaddleBall had been mentioned to a seat, in a window, and no file carried
it — so to the other five seats and every wake it never existed. The same mechanism lost the pool vote
for eleven days. A chat is not a place.

**My decision, which the founder's 2026-11-10 terms make mine:** PaddleBall is accepted as a project
and it starts after item 1 (the renderer on `main`), not before. The reasoning is in the answer I gave
him, and the short version is that the wall changes *which* skill is learned.

- **Shared with tennis, deliberately:** the ball integrator in `lab/tennis.py`, the court builder, the
  camera-cut rules, the scoreboard, the season folder, the record format. If a second game needs a
  second physics implementation, it does not get built — a second copy is how the first one breaks.
- **New, and small:** one wall instead of a net, a paddle contact instead of a racquet face, and no
  need for the racquet geometry that cost eight image generations and never worked.
- **The design risk, named before it is built:** a *perfect* wall is a machine, not an opponent. The
  rebound is deterministic, so there is nothing to learn beyond position — and a game whose only skill
  is a formula is the thing the founder rejected when he demoted the statistics. The wall's
  imperfection is therefore the game: a seam, a dead panel, a surface that eats spin differently at
  one height, each measured and printed. **If that sentence cannot be made true, do not build this
  game.**
- **Done-test for the item itself (not the game):** a design page in `games/paddleball/README.md` that
  states the wall's imperfection model with numbers, the contact model, and which files it imports
  from `lab/tennis.py` — reviewed before any renderer work begins. **Number:** the count of imported
  tennis modules that were *not* copied.

### 2026-11-15, later the same day — the design page landed, and the wall did not

**The founder named the game.** In a live window on 2026-11-15 he called it **pickleball**, with a *kitchen*,
a *double-bounce rule* and a *doubles assignment*. None of those three exist without a net and an opponent
across it, so the **wall is dropped** and the sport is built — my decision, recorded here because item 9's
paragraph above describes a different game and a future reader would otherwise have to guess which one is
real. `games/paddleball/` does not exist and will not; the page is `games/pickleball/README.md`, 336 lines,
committed today and pushed with this line. What survives from item 9 untouched is its constraint: one physics
implementation, imported from `lab/tennis.py`, never copied.

**The four things he asked for, and what each cost to answer honestly:**

1. **The drag curve and its source** — `Cd` is flat across the game's whole speed range (two independent
   studies: 0.33 outdoor from 86 trajectories, 0.45 indoor, 0.30 ± 0.02 from six), so the curve is one
   constant, `k` = ½ρCdA/m = **0.0103/ft against tennis's 0.0063**. But the sources' own flight times differ
   by **25%**, and their published third-shot-drop window's slow corner is **ten inches below the net tape**
   at their own stated launch geometry — arithmetic with drag left out. So the constant is *declared*, with
   its error bar, and the page says so.
2. **Kitchen and double bounce** — one bounce counter (`may_volley = both sides have bounced`), one distance
   test (`abs(x-22) <= 7` at a volley *contact*), and the momentum clause adjudicated by timestamp because a
   renderer cannot show it and skipping it plays a different game.
3. **Doubles** — named seats never indexed, teams fixed on the command line before the first serve, the
   even/odd right-left rule derived from `score % 2` and one `first_server` flag, two servers except in the
   game's first service turn, only the serving team switching, stacking declared out of scope with the
   reason.
4. **The import list, zero copies** — 12 import rows, all backwards-compatible changes to `tennis.py`,
   `games/pickleball/` holds no Python, and the three mechanical tests are written out. Measured today:
   **0** hits for four of five physics literals outside `lab/tennis.py`; `32.17` already has a second copy
   in `lab/putt.py:39`.

**The finding that reorders the work, and it is not the one I expected.** The drop's window is **0.5° wide**
at 26.8 mph and 3.5° at 24.4 mph, while the drag constant's uncertainty moves the required launch angle by
**1.2°** and the fitted lift term by **0.83°**. So the measured ball is a **blocker for the dink game**, not a
nice-to-have, and the first playable mode is the **driving game** at 35–45 mph, where the window is
3.5°–10.1° and 1.2° of drag error is a fifth of it. One camera, one marked ball, one court. That is item 9's
successor and it is written into the page's "what is not built" in that order.

**Number for the design-page gate:** 12 imports, **0 copied modules**, 0 of 5 physics literals duplicated,
and — the number that matters more than any of those — **0.5° of window against 1.2° of uncertainty**.

---

## Done since this file was written — with the numbers

These were built on 2026-11-13/14 in a live window, before this file existed as their home. Each one carries the
measurement that justifies it, because a claim without a number is the thing this file exists to prevent.

- **The carry — done.** At a shot boundary the body no longer snaps out of its lean; the previous frame's
  displacement eases out over 0.34s and the next shot's lean is added on top. 570 boundaries: median body step
  **2.1 → 1.7ft/s**, p90 **20.5 → 2.8**, share over 10ft/s **19% → 2%**. Cost, measured honestly: racquet head to
  the record's contact point **0.08 → 0.31ft** median, 92/95 → 70/95 within half a foot. Kept, and the fix is
  named (`MOVEMENT.md`): let the lean grow to cover the gap rather than shrink the carry.
- **The plant, half — the weight.** 0.12ft rise peaking just after contact, back to 0.004ft of net change by
  0.22s, stateless so a seeking probe can replay it. Continuity unchanged by the same 570-boundary probe.
- **The plant's other half, and the instrument it needs.** The back knee flexes 0.30rad through the
  follow-through (a forehand is struck with the left foot forward, `sh.hand` read as a stance). Measured: the back
  ankle rises **0.05ft**, because a knee angle raises an ankle by L(1−cosθ) — quadratic, so 0.30rad is nothing. **A
  real heel lift cannot be measured at all yet:** the foot bone's origin *is* the ankle, so rotating the foot moves
  nothing `__pose()` returns. So: add a toe point to `__pose()` and `hand` to `__audit()` first, then solve the
  coefficient against 0.20–0.30ft at the toe. `stills/plant-contact.png` is the silhouette to judge against.
- **The forehand sheet — done, and it cost 77 Gems.** Four renders by workflow (`mage-render.yml` on
  `llm-symposium`, one image per dispatch, every one committed with its `gems_charged` beside it). Finding: at five
  panels the model holds the camera *or* the mechanics, never both; **three panels holds both**. One panel still
  failed (the finish, drawn over the wrong shoulder), so the sheet's value is the CONTACT pose: racquet head at hip
  height, out to the side by most of a shoulder width, arm straight.

## Item 10 — nobody is ever beaten — DONE 2026-11-15, see the numbers below

`reachable()` passed the closing speed into a meeting point fixed a racquet's length short of the landing point, so
every ball was reachable: in 50 sampled points, **not one** ended with "did not reach it". Points ended on misses
only. This was not a look — it was the game refusing to model the thing that makes tennis a contest.

- **Done:** `lab/tennis.py`. The closing-speed shortcut and its `+1.0` second of grace are gone. The ball is now
  stepped through its own post-bounce life in 0.02s slices, with the same quadratic drag the flight uses, until it
  bounces a second time or climbs above 9ft; at every slice the question is the only one that matters: *can the
  player be within a racquet's length of the ball by then?* The player is given `flight_time` of running before the
  ball bounces, plus the ball's remaining life after it, less two costs the old rule ignored — `REACTION` 0.25s
  (the split step: nobody leaves on the opponent's contact) and `SETTLE` 0.20s (the brake: a ball met at a sprint is
  a frame, not a shot). `RACQUET_REACH` 7.0ft is a standing lunge, three feet of arm and racquet plus the first step.
- **Number, and the instrument matters more than the number.** Through points, the reach-rate is partly a measure of
  how long the point lasted — a point that ends early has fewer balls to ask about. So the headline is a *fixed*
  population: 600 balls the engine itself struck, with the hands taken out of it so they are balls that are actually
  in the court, every skill level asked about the same 600.

  | balls hit | speed | old rule: not reached | new rule: not reached |
  |---|---|---|---|
  | 0 (reach 0.35) | 10.2 ft/s | 0% | **26%** |
  | 100 | 15.3 | 0% | 11% |
  | 300 | 18.5 | 0% | 6% |
  | 600 | 19.2 | 0% | **5%** |

  Through points (150 a pairing, same seed): at 300 balls 24% and 38% of the balls each player had to get to were
  not reached; at 600 balls 22% and 22%. The old rule: 0% in every cell, at every skill level, which is the defect.
  **Re-measured after the shot chooser came over (Item 14, same day): 3-5% of balls, and 31 points in 60 ending on a
  beat rather than a miss.** A point is ten shots now instead of two, so most balls are reached and the *points*
  are still won; the band in the done-test above was a proxy for that and the proxy has stopped meaning anything.
- **Guard:** met when this item closed — a player with `reach=0.35` reached 74% of the fixed population, the 70%
  floor, and only just. **Re-based 2026-11-18:** the run is now an accelerating run with a skill-timed split step
  (Item 14, fifth move), and the same seven feet reaches 67% of the same 600 balls at 0 balls, 87% at 300 and 87% at
  600. The 7.0ft was not re-tuned to hit the old number, because that number was calibrated against arithmetic this
  commit replaced; the floor in the test is now 60% for a beginner and 85% at six hundred balls, and the reason is
  written beside it.
  The radius is what bought it: at 3.0ft the same population was 40% reached and beginner points were 56% not
  reached, which is the guard doing its job. The 7.0ft is generous on purpose and the reason is written in the code:
  this model gives the player no anticipation, and the step is charged for twice, here and as `REACTION`.
- **Learning curve:** `test_rally_length_responds_to_hands_and_to_learning` was **red** when this item started
  (9.083 not greater than 11.625). It is **green** now, and so is the rest of the suite — 330 tests, OK. The reason
  is not the interception; it is the bug the interception's measurement found (see Item 13).
- **The reason string** names the direction of the miss at the closest moment, not at the landing point. Every beat
  in a match came out *wide* (12 of 12 in one 50-point sample): a ball that goes past you in this model goes past
  you sideways, because the one thing it always does is keep coming down the court, and the deep beat is the rare
  one. `test_a_rally_ends_only_for_a_reason_a_player_can_see` still forces a deep one and still gets the word.
- **Not done, and it is Item 13:** the record carries no `met: false` yet. `reachable()` now decides it and
  `play_point` already writes "X takes the point", but the JSON the 3D viewer reads (`run.met`, `run.need`,
  `run.have`, `run.short`) is built by a script that is not in this repository — the existing records contain those
  fields and nothing produces them. The viewer's caption already handles a miss ("runs 8.7ft at 17.1ft/s and does not
  get there"); no record has ever had one.

## Item 11 — the volley to a deep corner goes long

Three of seven sampled volleys missed: the groundstroke's corner margin is applied unchanged to a ball struck 6ft
from the net, where the same angle error covers more ground.
**Done-test:** 7/7 volleys from the forecourt land in, with the margin scaled by distance from the net. **Number:**
mean landing distance inside the baseline, before and after.

## Item 12 — the arms never come back to the right side during a run

One pose carries the whole carry phase; a running player's racquet should come back to the hitting side as they
move. **Done-test:** in a sampled run, the racquet head crosses from the non-hitting side to the hitting side at
least once per stride pair. **Number:** crossings per 10 strides, before and after.

## Item 13 — the way a record is decided is now the way a scoreline is (DONE 2026-11-15); the geometry's producer is still missing

Found while trying to measure Item 10, and it turned the suite green.

**The defect.** `play_point` chose the target depth as `NET_X + rng.uniform(4, 34)` for both seats. For a north
player that is 4–34ft past the net; for a south player it is 4–34ft *behind them*, because the net is at the far
end. The face search then bisected onto the tallest face it had, and the ball landed on the hitter's own side. Every
south return was a ball hit backwards. Over 50 points a match averaged **1.2 shots** and the record read as two
beginners who could not rally. It was not the error model, and it was not Item 10.

- **Done:** the depth is mirrored by the hitter's end. Matches went from 1.2 to **2.0** shots a point, and
  `test_rally_length_responds_to_hands_and_to_learning` went from red (9.083 not greater than 11.625) to green.
  `python3 -m unittest tests`: **330 tests, OK** — the whole suite, not just Tennis.
- **Also worth recording:** the pickleball body hit the same bug in their own harness on the same afternoon
  ("a harness that aimed the south end's shots into the south end's own court"), which is the useful kind of
  corroboration: a mirroring assumption written once is written wrong once in every file that copies it.

**The record half, done.** The 3D viewer reads `run.met` / `run.need` / `run.have` / `run.short` off each shot and
prints "runs 8.7ft at 17.1ft/s and does not get there" when `met` is false. Those fields are in every record under
`games/tennis/records/`, and nothing on this branch produced them — the generator was `lab/tennis_script.py`, which
was **not here** (see Item 14). **It is here as of 2026-11-19**, producing
`records/film-2026-11-19.json` out of this engine, so the fields below are now written by the same code that reads
them. What is here now is the arithmetic, in one place:

- `tennis.interception()` returns the interception as numbers — ok, need, have, short, the ball at its closest, and
  where the feet come to rest — and `reachable()` is the yes/no built on it and nothing else. There used to be two
  models of this, this one and the generator's `intercept()`, and they disagreed; a picture that draws a player
  arriving short and a scoreline that says "did not reach" now cannot disagree.
- `lab/tennis_record.py` takes a record's own geometry — every contact point, launch velocity and spin, every
  player's position — replays each ball through today's integrator, asks today's interception, and rewrites the
  record. A ball nobody reached ends its rally, because no rally may have a shot after it.
- **The done-test, met:** `games/tennis/records/rally-out-of-reach.json` — 20 rallies, 93 shots, **4 balls nobody
  reached**. Opened at `?record=records/rally-out-of-reach.json&shot=92` the caption reads *"Gwen 14ft short of it,
  beaten by the deep ball · Gwen runs 6.2ft at 18.9ft/s and does not get there"* and the board reads *"Gwen did not
  reach it — 14ft short of it"*. **Number:** the feet stop **20.7ft** from the ball on that shot, and 8.5 / 8.9 /
  9.5ft on the other three — every one of them more than the 7ft arm, racquet and lunge. Stills:
  `stills/out-of-reach.png`.
- **Found while doing it, and it was in my own tool first:** `record["players"]`' `north` is the *opening* lineup,
  and these two change ends every five points. Reading it put every runner on the wrong half of the court after the
  first change; the end now comes from the shot itself. Three tests hold all of this
  (`TestTheRecordSaysThePlayerWasBeaten`), one of them the invariant that no rally continues past a beat.

**Still open — the geometry's producer.** Where each player's feet begin, the stance before the serve, the recovery
after each shot, the walk between points, the ball's traced path, and the corridor of face angles that would have
kept each shot in: all of that comes from the record, and the script that made it is on another branch.

## Item 14 — there are two tennis engines, and main has the smaller one (CLOSED 2026-11-19)

Found while trying to run the record's generator. `lab/tennis_script.py` — the script that produced every record
under `games/tennis/records/` and every demo film — is **not on this branch**. It is on
`origin/desi/plant-2026-11-15` — the branch the renderer was recovered from on 2026-11-15 — and it calls ten
functions of the `tennis.py` that lives there: `intercept`,
`volley_contact`, `recovery_spot`, `hit_window`, `choose_shot`, `placement`, `corners_of`, `side_of`, `on_court`,
and a `flight()` that traces. That engine is **1,917 lines**; this one is 1,674. They are not the same program.

Which also explains something that looked like sloppiness earlier today: Item 1 copied `games/tennis` onto main and
did not copy `lab/tennis.py`, so the viewer and the films came over without the engine that made them. The copy was
the right call at the time — the alternative was a history merge against an active writer — but it left the
repository in this state and it should be said plainly rather than discovered again.

So the repository currently contains a viewer and a set of records produced by an engine that main does not have,
and a season report produced by the engine main does have. Neither is wrong; they are two different games wearing
one name, and the longer one has the shot chooser, the volley model and the recovery model that the short one
lacks (a rally on main is 2.0 shots; the longer engine's own records carry 10- and 40-shot rallies).

**Done-test:** one `lab/tennis.py` on main, with `lab/tennis_script.py` running against it and reproducing the
2026-spring record's shot count and rally lengths within the engine's own scatter. **Number:** lines in the file,
functions in the record generator's call list that exist, and rally length before and after the merge. **The
decision this needs, and it is not mine:** the longer engine is where the records came from, so merging is the
direction that keeps the films; but merging is also how the last three days of movement work on main would be
lost if it is done by copying files. It has to be done function by function, with the suite green after each.


**What came over first, and what it measured.** The shot chooser is one port and it is done: `hands()`, `corners_of`,
`side_of`, `placement`, `serve_corners`, `_not_the_same_ball_twice`, `choose_shot` and `recovery_spot` are on main,
and `play_point` now carries both players' feet (`where`), chooses each ball from the situation, and recovers the
hitter behind the baseline — or in behind an approach — before the next ball is chosen. The interception is asked
about the position their legs actually left them in, which is what `interception(frm=…)` was for.

| | before the port | after |
|---|---|---|
| median point, 300 balls | 2 shots | **10 shots** (mean 13.2, longest 40+) |
| median point, 600 balls | 2 | **11** |
| serve in | 23-38% | 93% at 300 and 600, 42% at 0 |
| points ending on a beat rather than a miss | 13/60 | **31/60** |
| balls not reached, per ball | 22% | 3-5% |

That last row is worth saying plainly: Item 10's "10-30% of balls not reached" was written for a game where a point
was two shots, and once a point is ten shots the same rule gives 3-5% of balls and half the points. The band was a
proxy for "points do not all end on misses", and they no longer do. Nothing was retuned to hit it.

**And the port found two arithmetic bugs that had been in every shot ever played here.** (1) `strike` computed the
azimuth as `atan2(aim - y, 32.0)` — thirty-two feet, for every shot in the game, whether the ball had fifty feet to
travel or seventy. The lateral error was therefore proportional to the length of the shot, so a corner aimed four
feet inside the sideline landed six feet outside it, which is why every miss list in this file says "wide". It takes
`aim_dist` now, and `aim_at` passes the real distance. (2) A serve's depth is set by how hard it is hit, not by the
face — `aim_at` bisects the face and leaves the power alone, which is right for a ball struck from three feet and
wrong for one struck from 8.8. That is why serving a corner meant serving into the net. `aim_serve` bisects power at
a chosen face.

**The volley, 2026-11-16 (`d4ac2d01`).** `choose_shot` had volley weights and there was nothing in this engine that
could volley: a player standing seven feet from the net waited for the ball to bounce, and the interception was asked
about a bounce point a net player never reaches — so every approach was scored as a point lost. `volley_contact()` is
one radius rather than a box: the earliest sample at which the racquet can physically be at the ball, between 2.2 and
8.0ft, on the hitter's own side of the net, with the legs given the flight time to close the gap. `play_point` asks it
*before* the interception, because a volley is the point at which the bounce does not happen.

| | 0 balls | 300 balls | 600 balls |
|---|---|---|---|
| median point | 2 shots | 15 | 16 |
| mean | 2.1 | 22.3 | 22.2 |
| serve in | 57% | 92% | 97% |
| volleys taken | 0 of 124 shots | 46 of 1,338 | 42 of 1,331 |

A volley is an approach shot being answered, not a rally's default — which is the right shape: at zero balls nobody
comes in, so nobody volleys, and the count is a fact about the game rather than about the code.

**The picture, 2026-11-16 (`9173c33b`).** The founder asked three times for seconds of ball after the point is
decided, and each is a switch on `flight()` that defaults off: `out_bounces` and `legal` (an out ball bounces a
couple of times), `after_land` (a ball that lands in comes up before it is struck), `net_cord` (a ball into the tape
rebounds and drops at the foot of the net) and `bounces` (the ball is still a ball). No verdict moved: `land`,
`time` and `bounce` are still the first bounce, and a test holds the switches to observation with every one of them
on at once.

Porting it found a bug the longer engine also has: a ball that landed and then ran out of picture time returned
`land: None, lost: True`. The one landing every verdict reads, thrown away because the *second* bounce did not fit
inside `t_max`. A ball that has landed has not been lost.

Also over: `hit_window()` (the ball's own parabola decides how long it is hittable, so a skid on grass and a kick on
clay are not given the same constant), `serve_verdict()` (the box, not the court, and a fault names its distance),
`on_court` / `in_serve_court` / `in_far_court` / `in_view`, `ALLEY`, and `v0` on `strike`'s return — which with
`contact` is the whole of what a record needs to be replayable, and which `lab/tennis_record.py` had been
reconstructing without.

**The racquet back, and a serve that can be missed, 2026-11-18 (`9207d370`).** Two of the three things the producer
needs are in. `prep` is a fourth skill with an onset at sixty balls and a slower curve than the other three, and
`Player.rush` is how much of the racquet's preparation the flight did not allow: a player who overlaps the run and
the racquet needs `max(run, prep)`, one who does not needs `run + prep`. `strike` pays for being rushed twice —
worse hands and 0.55× the sweet spot — which makes movement affect the *ball* and not only the miss, for the first
time in this engine. `hands(pace)` was already here from 2026-11-15 but was never fed a real pace; it is now, since
`strike` reads it instead of recomputing the same line.

And the return of a serve stopped being the one ball exempt from the rule: the interception was asked only from the
second shot on, so no serve could be an ace however well it was struck and no return could be rushed however late
the receiver was. Aces in 900 serves with it asked: **0**.

**Who it happens to, counted on shots actually hit at a ball (60 points at each standard):**

| balls | shots | rushed badly (rush > 0.1) | mean rush |
|---|---|---|---|
| 0 | 50 | **84%** | 0.24 |
| 60 | 53 | 77% | 0.19 |
| 150 | 135 | 43% | 0.09 |
| 300 | 850 | **3%** | 0.01 |
| 600 | 1,336 | **2.5%** | 0.01 |

Which is the shape the founder described: the earliest stage is rushed on four balls in five because the racquet is
not back in time, and a player with three hundred balls behind them has stopped being rushed because they prepare
while they run. And what it does to the scoreline, over 300 points:

| | 0 balls | 300 balls | 600 balls |
|---|---|---|---|
| median point, before → after | 1 → 1 | 10 → 10 | 18 → 16 |
| mean, before → after | 1.7 → 1.7 | 15.0 → 13.9 | 23.4 → 21.5 |

Almost nothing, and for a different reason at each end: at 0 balls the point is decided by the serve before the rule
can matter, and at 300+ it rarely fires. The 600-ball row is inside the run-to-run scatter of the same build.
**First version of this table said 0-3% at every standard and it was wrong** — the instrument counted `aim_at`'s 22
bisection probes per shot as shots hit at a ball, dividing the true rate by twenty. A rate over a population is only
a rate if you can say what one member is.

**The run, 2026-11-18 (`f2ab7e73`).** The last of the three things the producer needs. `FIRST_STEP` 42 ft/s² to top
speed and then flat out, `run_distance` as its exact inverse, and `reaction_time` as a skill (0.26s at no balls to
0.11s at six hundred) instead of 0.25s for everybody. Same 600 in-court balls, before → after: 26 → 32% not reached
at 0 balls, 11 → 18% at 100, 6 → 13% at 300, 5 → 12% at 600. Through 300 points a level: median rally 1/10/16 →
1/8/14, points ending on a beat 0/23/31 → 0/31/59. The game gets harder and the point still lasts — eight shots at
300 balls, fourteen at 600.

**The producer, 2026-11-19 (`lab/tennis_script.py`, 595 lines).** The sixth and last move, and the one that turns the
engine into a film: `lab/tennis_script.py` writes the per-shot JSON the 3D viewer replays, and it now runs on main's
own engine rather than the branch's. Everything it calls already existed here; what differed were three argument
names and one return shape:

| the script said | main says |
|---|---|
| `strike(..., contact=X)` | `strike(..., at=X)` |
| `strike(..., aim_x=X)` | `aim_dist=abs(X - contact[0])` |
| `aim_at(..., contact=X)` | `aim_at(..., at=X)` |
| `volley_contact(other, traj, at)` | `volley_contact(other, traj["path"], at)` |
| `intercept(...)` | `interception(...)`; its `t_arrive` is `at`, `ball` is `meet`, `distance` is `gap`; `window` is `hit_window(bounce)[1]`, and it has no `legs` (use `speed`) |
| `T.OUT_BOUNCES`, `T.AFTER_LAND`, `T.PLAY_PAD` | literals in the script, or `2`, `1.4`, `4.0` |

`intercept` itself is superseded by `interception` and was **not** ported. The one judgement in the translation was
the `run` timing, which is what puts a body where it walked to; the record's `t0` is the previous strike, so the
branch's `t_arrive` became main's `at`. The test of it is the film, and the film is the criterion: a player must not
be placed anywhere their legs did not carry them.

The first run: `python3 lab/tennis_script.py --rallies 20 --practice 300,600` → **107 shots over 20 rallies, rally
lengths 5 5 8 1 7 2 5 4 7 4 6 8 6 3 6 7 5 8 7 3, two points ending on a beat, rating 6.51 vs 6.96**, in eleven
seconds. `games/tennis/records/film-2026-11-19.json` is that run.

**What the producer found in `play_point`, and it is the reason this move was worth more than a translation.** A
30-rally run at practice 600/600 gave a median of four shots where `play_point` gave eight. The producer picks the
serve's pace and bisects the face; `play_point` called `aim_serve`, which fixed the face at six degrees *up* and
bisected the **power** — and a ball struck from 8.8ft with the face held up needs only about fifty miles an hour to
land in the service box, so the search had nothing to push against and settled at the top of its own range.
Measured: 441 serves, **median 53.5mph, min 46, max 79**. The serve was the slowest ball in the game, in the one
sport where the serve is the fastest, and that is why nobody was ever rushed returning it and why an ace had never
been seen (0 in 900 serves).

The fix, 2026-11-19: the pace is what a server chooses (`SERVE_MPH = (66.0, 18.0)`, scaled by control so a beginner
does not serve like a professional) and the face is what is solved, which is the producer's rule and therefore the
only serve in the game. `aim_serve` is deleted, with a note where it stood. Measured after, 120 points at each
standard, same seeds:

| | 0 balls | 300 balls | 600 balls |
|---|---|---|---|
| serve, median | 63mph | 75mph | 74mph |
| serve, 10th–90th | 56–71 | 67–81 | 67–82 |
| serve in | 42% | 87% | 83% |
| rally, median | 1 | 5.5 | 6.0 |
| rally, mean | 1.9 | 12.2 | 11.5 |
| aces | 0% | 17% | 22% |
| rushed on (rush > 0.1) | 86% | 5% | 3% |

Before the fix the serve was in 95% of the time and the point was long for the wrong reason: nobody could be beaten by
the first ball, so every rally started with a free return. Now the point got shorter and faster, and the two engines
agree about what a serve is — the producer's 20 rallies and `play_point`'s 120 points both come out at five to six
shots.

**Two things this does not do.** There is still no toss and no overhead — the serve is struck from a standing
position 8.8ft up, which is movement list item 3, and it is why the swing looks like a swing and not like a serve.
And **17-22% aces is more than tennis has**: the fastest serves (82mph at the 90th percentile) arrive 55ft away in
0.5s, and the receiver's 7ft reach, 0.11s split step and 0.20s brake make those a coin flip. The return of serve is
the next thing the pace exposes, and it is a model of the return — standing behind the baseline and playing the ball
after the bounce — not another number in the serve. **Answered the same day, Item 15: the model was one line, the
receiver's stance, and aces are 6-10% with it.**

**The item's done-test, answered.** *One `lab/tennis.py` on main, with `lab/tennis_script.py` running against it and
reproducing the 2026-spring record's shot count and rally lengths within the engine's own scatter.* It is met. At
the record's own standard — 400 balls, clay, SW 6mph, 20 rallies, the record's own clock — the new producer makes
**84 shots and 91 shots and 91 shots and 91 shots**, against the record's **95**; mean rally 4.2-4.6 against 4.8,
median 3.5-4.5 against 3.5. The shortfall is the direction the movement port predicted (a body that has to
accelerate is beaten to more balls) and it is inside the scatter: four clocks, four different films, a spread of
seven shots. **Re-measured after Item 16, the same day: 78, 117, 126 and 145 shots, medians 4-6.** The record's 95
is still inside that range, but the scatter has doubled, because the meeting point now depends on where the body is
rather than on a constant. The done-test is met and it is worth less than it read this morning. The item is closed. `intercept` was the one thing deliberately not ported, because `interception`
supersedes it. What the port found along the way — a landed ball that ran out of picture time and called itself
lost, and a serve that was the slowest ball in the game — are both fixed here, and both were found by main's own
code meeting the branch's.

## Item 15 — the returner stands behind the baseline (DONE 2026-11-19)

Found by following yesterday's own numbers. The serve stopped being a 53mph arc and the aces went to 17-22%, and I
had written in this file that the answer was "a model of the return, not a smaller serve". It was not a model. It was
one line, and the line had been there since the interception was written: `play_point` set **both** players two feet
*inside* the baseline. That is where a server stands. A returner is on the back foot with the ball coming at them.

**The measurement that decided it** (`/tmp/stance19.py`): 120 real serves, and nothing differing except where the
receiver stands — the serve is a fact, the stance is a choice.

| stance | reached, 300 balls | reached, 600 balls |
|---|---|---|
| 2ft inside the line (what the engine did) | 94% | 89% |
| on the line | 97% | 93% |
| 4ft behind the line (**what it does now**) | 98% | 97% |
| 6ft behind the line | 99% | 98% |

**Through the scoreline**, 200 points at each standard, the same seeds, only the stance differing:

| | 0 balls | 300 balls | 600 balls |
|---|---|---|---|
| aces, before → after | 0% → 0% | 17% → **6%** | 23% → **10%** |
| rally median, before → after | 1 → 1 | 4 → 5 | 6 → 8 |
| rally mean, before → after | 1.6 → 1.5 | 8.6 → 8.4 | 12.9 → 15.6 |
| rushed on, before → after | 87% → 90% | 16% → 19% | 4% → 5% |

The medium rally got longer at 600 balls, which is the same coin: the points that used to end on the first ball are
rallies now. Serve-in moved a point or two either way and that is the scatter of a different point population, not
the stance — a receiver's feet cannot change where the server aimed.

**Done-test:** aces below 20% and above zero at 600 balls, and the receiver's `frm` outside the baseline on the
first question of every point. `TestTheReturnerStandsBehindTheLine`, three tests.

**The tail: the film now stands its returner where the scoreline does (DONE 2026-11-19, later the same day).**
`lab/tennis_script.py` stood the returner two feet inside the line while `play_point` stood them four feet behind it,
so the picture and the play disagreed about the stance. Two changes, both small: the producer emits **two** stance
moves per point (`stance` is now a list — the server walking to the line, the returner walking back to x = -4 or
82), and `replay3d.html` reads a list as well as the single object older records carry. The regenerated record's
stance list is `[Dmitri → [0.0, 13.5], Gwen → [82.0, 13.5]]` for the first point, over all twenty points the four
values seen are -4.0 / 0.0 / 78.0 / 82.0, and the returner's first run of every rally starts from exactly the spot
the stance move puts them in. Two feet, and the picture now shows the game the scoreline is playing.

**What is now visible that was not before:** a point at 600 balls is thirteen to fifteen shots, a quarter of them
hitting the engine's 60-shot ceiling. *(After Item 16 the same day: median 8.5, mean 12.7, and no rally in a
20-rally film reaches the ceiling. On 60 points at 600 balls, 16 ended with the opponent beaten, 40 with a shot into
the net or out, and 4 with a fault — a quarter of the points are won rather than lost, which is where tennis is.)* The players cannot pass each other. That is the next item and it is not a
stance: 7ft of racquet reach plus a recovery to the middle means the corner is always covered, and `choose_shot` has
no notion of a ball that cannot be returned. It is the same family as Item 11 (a volley to a deep corner) — the
engine has no shot that is *unreachable*, only shots that miss.

## Item 16 — the ball is struck from a place the body is not (DONE 2026-11-19)

`contact_point()` returned `x = 2.0` for **every** shot by **every** player — two feet inside the baseline — and `y`
from the middle of the court plus or minus five feet, chosen at random. `play_point` passed `at=None` for every
groundstroke, so every ball in the scoreline engine was struck from the middle of the baseline by a player who may
have run twenty feet to reach it. The run was asked about (`interception(frm=where[…])`) and then thrown away.

`lab/tennis_script.py` did not do this — it passes `at=contact`, where `contact` is the interception's own meeting
point. That is Item 14's disease in a new place: two models of the same thing, one in the record and one in the play.

**Then the fix found a second defect, and a bigger one.** Pointing `play_point` at `meet` made every rally *shorter*
and the net-errors jump, because `meet` was the first 0.02s slice at which the ball was within a racquet's length —
and for a ball coming at you off a bounce that slice is about a foot off the ground. Measured on the shipped film:
**42 of 107 groundstrokes were struck at 0.0ft and the median contact was 1.81ft.** A player does not hit a ball at
ground level when they have time; they let it come up to the height they like. So `interception` now returns the
slice nearest `CONTACT_HEIGHT = 3.0ft` (the waist) among the reachable ones, first-in-time winning a tie — the ball
taken on the rise rather than the same ball on the way down — with the first reachable slice as the fallback for a
ball that never comes up, which is a scrape and a real shot.

That also moved the *deadline*: the ball is now struck 0.2-0.7s after it bounces rather than at the bounce, so
`rush` is charged against the contact time rather than the bounce time. Rush was 86% / 5% / 3% at 0 / 300 / 600
balls and is now 0% / 1% / 1% — **and that is a finding about the rule rather than about the players**: with a ball
in the air for one to two seconds and a 0.55s take-back, preparation fits, and what a beginner actually fails at is
getting to the ball at all. The rule is right, its rate was a property of a deadline that has now moved, and the
test says so instead of being re-tuned to keep the old shape.

**Measured, 120 points at each standard, before → after:**

| | 0 balls | 300 balls | 600 balls |
|---|---|---|---|
| contact height, median | — | 3.0ft (**1.8ft** on the old film) | 3.0ft |
| aces | 0% → 0% | 6% → **1%** | 10% → **4%** |
| rally median | 1 → 1 | 5 → 4.5 | 8 → **8.5** |
| rally mean | 1.5 → 1.5 | 8.4 → **7.0** | 15.6 → **12.7** |
| serve in | 32% → 30% | 88% → **88%** | 94% → **94%** |

Contacts below a foot, the number that matters and the one that is on the film rather than in a rate: **42 of 107
groundstrokes at 0.0ft before, 1 of 110 after.** The intermediate state — meeting the ball where it was first
touchable, with no height rule — was worse than either: 15-20% of contacts below a foot and 51 shots into the net in
120 points at 300 balls, against 22 with the waist rule. That is why the rule is a height and not a slice.

**The film, regenerated.** `records/film-2026-11-19.json`: 110 shots over 20 rallies at 300/600, rally lengths 5 5 2
2 3 5 12 5 4 6 7 10 9 1 14 6 3 4 4 3, contact height median **3.04ft**, one shot below 1ft against the old film's
42. The film's own invariants hold: every contact within `RACQUET_REACH` of the feet the run left the player at
(worst 7.01ft of 7.0 — the boundary), and no run faster than the player's speed (worst 12.1ft/s of a 19.2 limit).

**Done-test:** the mean distance between a shot's `contact` and the feet that struck it is under `RACQUET_REACH`
over 20 rallies — 7.01ft worst, met. The stronger claim this item added is the other one: the ball is struck at a
height a player strikes at, 3.0ft median against 1.8ft.

**One side effect worth knowing:** at the 2026-spring record's own standard (400 balls, clay, SW 6mph, 20 rallies)
the producer now makes 78-145 shots over four clocks where it made 84-91 before, medians 4-6, because the meeting
point depends on where the body is instead of a constant. Item 14's done-test still reads inside that range — the
record's 95 shots — but the scatter has doubled, and a claim of "reproduces the record's shot count" is worth less
than it was this morning.

## Item 17 — there is no ground past the run-off (DONE 2026-11-19)

Found while checking that Item 15's tail had not broken anything, which is the only reason it was found at all. Of
the 110 shots in the film, 32 ended a run more than 6ft behind a baseline and one ended 24.6ft behind it; four
contacts were outside the sidelines (y = -2.4, 27.1, -1.6). Traced rally by rally: the interception was chasing a
serve 25ft behind the baseline, and the rally then played itself further off the court, shot by shot.

**The cause is an unbounded question.** `interception` asks, at every 0.02s slice of the ball's life, "is the ball
within a racquet's length of the player by then" — over four full seconds, and it never asked whether there was any
ground left to stand on. A ball that bounced and flew away was still *reachable* in the arithmetic: the ball was
30ft away and the clock allowed 2.2s of running, so the answer was yes. The second-bounce break does not save it,
because between two bounces the ball is airborne the whole way out.

**The bound is the ground:** `PLAY_AREA = 12.0` ft beyond each line, and a `break` at the top of the slice loop when
the ball has left it. Twelve and not six because the founder's picture already shows `VISIBLE_PAD` = 22ft of ground
beyond the lines — a run-off of 12ft is on ground the viewer can see, and a ball leaving it is a ball going off the
edge of the world rather than a ball somebody chose not to chase.

**Measured on one fixed population, not on two films** (`games/tennis/instruments/reach_bound.py`, promoted out of
`/tmp` with the item so the numbers can be re-run): 614 real balls (59 points, every interception recorded and
re-asked at each candidate bound), because a film-level count cannot
answer this question — any change reshuffles the rng stream, and the same candidate bound gave 225, 225, 176, 110 and
139 shots at 6, 8, 10, 12 and 16ft. Those are five different twenty-point samples, not five run-offs.

| run-off | met >6ft outside | >10ft | worst meet | reach rate |
|---|---|---|---|---|
| none (what shipped) | 50.0% | 40.4% | 31.9ft | 98.0% |
| 6ft | 0.0% | 0.0% | 6.0ft | 98.0% |
| **12ft (what ships now)** | **16.1%** | **5.8%** | **12.0ft** | **98.0%** |
| 22ft | 39.2% | 28.9% | 22.0ft | 98.0% |

**The reach rate does not move — and the reason is not the one I first wrote down.** I assumed the bound was a filter
that took balls away from players. It is not: the reach rate is 98% at every bound *including none*, because every
ball the bound clips was already reachable at an earlier slice inside the ground. What the old code did was refuse
that answer and prefer a later slice nearer the waist, which is how a contact ended up thirty feet out. The run-off
does not filter contacts; it corrects which moment is chosen.

That also says the number should not be trusted to choose itself: `worst meet` equals the bound exactly at 6, 8, 10,
12, 16 and 22ft — the waist preference is still pushing contact out to the edge of whatever ground is allowed, and at
12ft one contact in twenty sits right on it. That is Item 18, and it is why the band rewrite is the next thing and not
a nicety.

**Also fixed on the way:** a ball that lands outside the bound never sets the closest-miss record, so the `best is
None` path unpacked `None`. It is now a sentence — "past the back of the court" — instead of a crash waiting for the
first opponent who hits a 200ft ball at a test.

**And a caption that was lying.** Checking the invariants turned up the film's `dist` field: it was `meet["gap"]`, the
distance to the ball, and the HUD prints "Gwen runs 30.7ft at 19.2ft/s" for a player whose legs covered 16.0ft. The
gap and the ground covered differ by the racquet's reach, so `dist` is now the ground the feet covered and `gap` is
kept as its own number. Same class as "wide by 0ft": a true record with a caption that overstates it.

**The film, regenerated.** 110 shots over 20 rallies at 300/600, lengths 5 5 2 8 4 10 3 2 3 15 4 10 6 2 16 6 4 3 1 1,
two aces in twenty. Runs ending more than 6ft off court: **36 of 85 → 3 of 92** (worst 29.2ft → 6.8ft). Shots whose
contact was more than 10ft outside a line: **38 of 101 → 4 of 110** (worst 35.1ft → 11.9ft). Every invariant
re-checked on the record:
contact within `RACQUET_REACH` of the feet (worst 7.01ft of 7.0), no run whose from→to over its own clock exceeds the
player's speed (0 of 110, where the old check that used `dist` was measuring the gap), contact height median 3.0ft
with none below 1ft.

**Done-test:** no meeting point more than `PLAY_AREA` beyond a line over a real population of balls, *and* the bound
moves the reach rate by less than three points against no bound at all — 98.0% both, over 614 balls. `TestTheGroundEnds`, three tests.

**What this does not fix, and it is the next item.** Four contacts of 110 are still more than 10ft behind the
baseline, and the reason is not the run-off — it is the meeting-point rule. The worst is a ball that bounced 14ft in
front of Gwen, who then ran 10ft *backwards* to meet it at 2.95ft: the zone rule prefers the slice nearest
`CONTACT_HEIGHT`, and only the descending 3ft crossing on the far side of the bounce gave her time to get there.
A real player hits that ball as it passes them, at 5ft, with no travel at all. The rule wants to be a *band* (waist to
shoulder, take the first moment inside it, which is the moment nearest the body) rather than a point to minimise
distance to. That is a change to the meeting point, it moves the contact-height distribution the last two items
measured, and it is being written down rather than rushed at the end of a turn.

## Item 18 — the meeting point is on the far side of the bounce (DONE 2026-11-19)

Named by Item 17 and finished the same night, in the next turn rather than at the end of that one, because it moves
the distribution Items 15 and 16 had just measured.

**The defect.** Item 16 chose the reachable slice whose height was nearest the waist. A ball crosses the waist twice
— once in front of the player and once behind them — and both are equally near 3.0ft, so height alone cannot break
the tie; the scan runs the whole ball, so the later crossing won. On the film that was Gwen running ten feet
**backwards** to meet a ball that had bounced fourteen feet **in front** of her.

**The rule now: a band, not a point.** Anywhere between `CONTACT_HEIGHT` = 3.0ft (waist) and `CONTACT_HIGH` = 7.0ft
(a shoulder and a bit; above that a groundstroke is a smash and this game has no smash yet) is a ball to hit, and
among those the player takes the one they have to **move least** for. `CONTACT_HEIGHT` stops being a target and
becomes the floor. The fallback for a ball that never comes up is still the highest point it offered, because a skid
is scraped and scraping it where it was first touchable is the Item 16 bug.

**The tie-breaker was measured, not chosen.** Taking the **earliest** in-band slice instead sends the player
sprinting forward at a ball that was coming to them: the twenty-point film came out at **220 shots** against 110, and
a 200-point population gave contacts per point of 10.3 against 13.7. So the band breaks the tie by travel, which
keeps the film's character and still refuses the far-side crossing.

**Measured with the ground bound loosened to nothing** — because that is the honest way to ask whether the picture
still looks like tennis without Item 17's backstop. 596 contacts from 300 points:

| | backward travel >3ft | worst | contact >10ft behind the baseline | worst |
|---|---|---|---|---|
| nearest-the-waist (Item 16) | 51.5% | 28.5ft | 39.4% | 30.1ft |
| **band, least travel** | **17.4%** | **12.2ft** | **1.7%** | **13.8ft** |

**And this is the sentence the item is worth:** with the bound back at 12ft, the band's numbers are *the same to the
point* — 17.4% and 1.7% — so the contact no longer depends on where the run-off is drawn. Item 17 is now a backstop
rather than the thing doing the choosing, which is what its own measurement said it could not be (worst-meet sat
exactly on the bound at every candidate value).

**Said plainly, because the numbers are not flattering:** with the run-off in place the band's marginal effect on
backward travel is nil (17.3% → 17.4%). It earns its place by making the choice independent of the bound, not by
improving today's film. The one thing that did move with the bound in place is the far contact: 2.7% → 1.7%.

**The film, regenerated.** 158 shots over 20 rallies at 300/600, lengths 5 5 9 3 14 2 3 13 14 11 17 15 5 1 13 2 1 11
6 8, two aces in twenty, longest rally 17 of a 60 cap. Contacts more than 10ft off the court: **4 → 0** (worst
9.8ft). Runs ending more than 6ft off court: **3 → 0** of 142 (worst 5.1ft). Contact height min 2.88ft, median
3.15ft, max 7.68ft, none below a foot. Every invariant re-checked: worst contact-to-feet 7.01ft of a 7.0 reach, no
run faster than the player, the two-move stance intact. Rendered headless and looked at.

**The film is longer and most of that is a smaller thing than it looks.** Mean rally 5.5 → 7.9 shots, which is a
twenty-point sample; on 200 points the engine's contacts per point went 12.3 → 13.7, so the real effect is about a
tenth longer rallies, and the rest is a different point population. It is the same coin as Item 15's: a ball that
used to be struck from behind the baseline is now struck from a place a player would choose, and the shot off it is
better.

**Done-test:** with no run-off at all, fewer than 5% of contacts more than 10ft behind the baseline (1.7% measured,
against 39.4% for the old rule), and the contact-height median between 2.9 and 4.5ft (3.15 measured).
`TestTheBallIsMetInTheBand`, three tests, 410 in the suite.

## Item 19 — the serve is thrown up before it is struck (DONE 2026-11-19, less the trophy position)

The founder's own words on the serve: "the serve is still an arc, not a tennis serve — no toss and no overhead". The
overhead half turned out to be *already drawn and measurable*: the engine strikes every serve from 8.8ft in the air,
and `?debug` at the contact frame reads **0.17ft from the racquet head to the ball** — the arm goes up and the frame
is on it. What was missing was the throw. A still of a serve was a player standing with the racquet down while the
ball was already halfway to the net, because the record had no ball before the contact at all.

**The toss is picture, not physics.** `strike` still decides where the serve leaves from and how fast; the record
carries the ball's life *before* that in its own `toss` array, sampled at the record's 0.02s and drawn from the same
`G` as everything else. One number sets it: `TOSS_PEAK` = 0.6ft, how far above the contact the ball peaks — a serve
is struck at the top of the toss or a hand's width past it. Everything else follows: the launch speed is whatever
reaches that peak from a hand at 3.2ft, the flight is 0.84s (42 samples), the horizontal drift is the release point to
the contact at constant speed, and **the last sample is the contact itself to the millimetre** so the picture cannot
disagree with the strike about where the ball was.

**The test that makes it safe:** switch `TOSS_PEAK` to 0 and build the same film again. Every serve's `contact`, `v0`,
`land` and `path` are identical, and every groundstroke in the film is untouched. A toss that moved the ball would be
a second physics, and this engine has paid for that once.

**What changed in the picture.** A serve's segment now begins at the release rather than at the strike (its start
moves back by the toss and its duration grows by it, so nothing after it moves), and everything that belongs to the
stroke — the arm arriving, the plant, the finish, the heel — is timed off a new `tlc`, the time since the *contact*.
The arm's arrival is symmetric in that clock, so on a serve it now arrives at the ball over the last third of a
second of the throw instead of being there for the whole of it. The legs load through the toss (`serveLoad`) and the
drive off them is 0.22ft on a serve against a groundstroke's 0.12ft — a crouch and a push, both functions of `tlc`.

**Measured on the film**, with a fresh browser profile at every frame (see below): at the release the arm is 1.25ft
from the ball and the ball is at 3.2ft; at 0.25s before contact the ball is at its peak, 9.4ft, over the server's
head, with the knees bent; at the contact the frame is 0.17-0.18ft from the ball with the body up on the toes. 158
shots, every invariant unchanged: worst contact-to-feet 7.01ft of a 7.0 reach, no run faster than the player, no
contact more than 10ft off the court, contact-height median 3.15ft with none below a foot.

**And the trap that cost me twenty minutes, recorded so it does not cost it again:** `python3 -m http.server` sends no
cache headers, and a *reused* Chrome profile served the pre-change page for the frame at `at=0` while the frames at
`at=0.3` were fresh. The picture said the arm was on the ball during the toss — the code said it could not be. The
frame was stale. Every render after that used a new `--user-data-dir`, and the `?debug` numbers and the screenshot
then agreed.

**What this still does not do, and it is the rest of item 3:** the trophy position is not drawn — the racquet stays in
the ready pose until the last third of a second, where a real server has it back behind the shoulder through the
whole throw; the *tossing* arm is not drawn, so the ball rises from a hand that is not visibly holding it; there is no
jump, so both feet are on the ground at a contact that is 8.8ft up; and there is still only one serve, so a fault
costs the point rather than the serve.

## Item 20 — the film is the season's session (DONE 2026-11-19)

The founder, 2026-11-19, on what "an integral part of Kythe" means, and it is not embedding a film in a page:
*"for the user to be able to watch a video of the same players, at their current skill levels, practice or compete
together, with their character pictures appearing during the breaks. The results from your video game would then
feed into Dmitri's seasonal data the same as if his own calculations had simulated the same game."*

Until today the game had two halves that shared an engine and nothing else:

| | reads whose skill | writes the season | produces a film | asks a member |
|---|---|---|---|---|
| `lab/tennis.py --rally` | `practice.json` | yes | no | yes — one shot line each |
| `lab/tennis_script.py` | `--practice` flags | no | yes | no |

So a member could practise all season and the film would never know, and the film could be watched all night while
the season did not move. Two tennis games, one of them scored.

**`python3 lab/tennis.py --watch --season <S> --names A,B --rallies N`** is the seam. It reads both players'
practice out of the season file, plays the film at that skill, and records the session the film played through
`record_session` — the same function, not a second one — so the session entry in `practice.json` and the shot list
in the film are the same facts. Every number in the entry is read off the film: `shots` and `of` are the player's
shots in the record, `in_play` is the count of its own `in` flags, `mean_rally` and `longest` are its rally
lengths. There is no second count that could disagree.

**The first watched session, and its numbers.** 2026-spring, Dmitri 300 balls and Gwen 600 (both `carried`, from
`--seed`, and named as carried in `report.md`), 20 rallies, clay, wind N 18mph, clock `1794000000000`:

- **129 shots**, lengths `14 5 1 3 6 14 4 11 10 4 5 5 1 2 10 2 5 9 16 2`, mean 6.45, longest 16 of a 60 cap;
- in play 55/64 (Dmitri) and 55/65 (Gwen) — *the same number in `practice.json` and in the film*;
- the invariants, re-measured on this record: worst contact-to-the-hitter's-own-feet **7.01ft** against
  `RACQUET_REACH` 7.0 — the boundary, not a violation; **no run faster than the player who ran it**; no run ending
  more than 6ft off the court; contact heights 2.85 / 3.59 / 8.8ft with none below a foot; a toss on **20 of 20**
  serves; and the only stance destinations in the record are −4.0 / 0.0 / 78.0 / 82.0, which is item 15 still
  holding under a new producer.

**One clock is one film.** Two runs at one clock and one practice produce the same shots, the same contacts and the
same `v0` to three decimals, which is asserted. That is what lets a film be *derived*: it is the season, played.

**The decision about overwriting, made explicit because it contradicts the season's own rule.** `practice.json` is
the record — nothing is ever reset and nothing is ever overwritten, so two watched sessions are two entries.
`watch.json` is a *rendering* of the season at one clock, so there is one of it and each session replaces it. The
record of a session outlives its film; the film does not pay rent in the repository forever. Both halves of that
are asserted.

**What a film must not do:** take `--vendor` or `--model`. It is played by the engine, and the flags being accepted
and silently ignored is the exact defect `main()` already refuses on the physics path — so they are refused here
too. A watch with no `--season` is a preview, plays from the flags, says it is not recorded, and writes nothing.

**Not done here, and it is item 21:** the film is not reachable from Kythe, and the game is not in the manifest
another tribe would receive. The founder can watch at
`games/tennis/replay3d.html?record=seasons/2026-spring/watch.json` from a local server and nowhere else yet.

## Item 21 — Kythe can show the film, and a tribe can receive it (OPEN)

Two gaps, and the second is the one that decides whether "integral part of Kythe" means anything.

1. **The watch has no door.** `ait.html`'s tennis card dispatches `season.yml` and reads `report.md`. There is no
   link to the film, so a person has to know a URL and run a local server (the page fetches a `.glb` and loads an
   ES module, so `file://` is refused by the browser). *Done-test:* the card carries one link per season to
   `games/tennis/replay3d.html?record=seasons/<S>/watch.json`; opening it on Pages draws the film; and a season
   with no `watch.json` says so instead of showing a stale film from an earlier session.
2. **`games/tennis` is not in the auto-update manifest.** `lab/make_template.py` carries `season.yml` and
   `lab/tennis.py`, so another tribe can *play* a session. It carries no `lab/tennis_script.py`, no
   `replay3d.html`, no `vendor/three.*`, no `bodies/*.glb`, no `bodies/faces/*.jpg` — so another tribe cannot
   *watch* one. That set is **4.6MB**. *Done-test:* a fresh clone of the template plays and watches one session
   from one command and one URL, with no terminal beyond the one that started the server.

## Item 22 — the cast is six, and now all six can be drawn (DONE 2026-11-19, less the four portraits)

`replay3d.html` derives the body file from the name (`p.body`, which `tennis_script.py` writes as
`name.lower()`), and `games/tennis/bodies/` holds `dmitri.glb` and `gwen.glb` and nothing else.

**`lab/body.py` is not at `HEAD`, but it is not lost either — and that is the Item 0 disease a second time.** The
file that built both bodies is 433 lines, it is in commit `10c99298` ("tennis: a body built to measurements, and a
replay that can show it", 2026-11-10), and that commit is **not an ancestor of `origin/main`**: the work was
committed locally and never pushed, so every clone has the `.glb` and none has the code that makes one. Blender
5.3.0 is installed on this machine, and the invocation is in the file's own docstring
(`--name dmitri --height 1.88 --build 0.95 --kit 3f5f6f --skin 8d5a3b --out games/tennis/bodies`). So item 22 is
a *build*, not a rewrite. It goes first in this item: recover the file, put it on `main`, and build the two members
the 2026-spring record is actually about.

The two `bodies/faces/*.jpg` are a different matter and cannot be generated: they are the founder's drawn
headshots of 2026-11-11. So:

- **the actual 2026-spring record cannot be filmed today.** Colette and Remy have 32 balls between them and no
  body; a film of them shows the page's error overlay, which is why the first watched session here is Dmitri and
  Gwen — the two names `seasons/2026-spring/setup.json` already gives as the season's cast;
- **a missing face degrades worse than a missing body.** `bodies/faces/` holds `dmitri.jpg` and `gwen.jpg`; for
  anyone else the `<img>` 404s and the break card shows a broken-image glyph with a name under it.

This is the V1 line *"a person can add themselves to it and be drawn from the same rig"*, and on 2026-11-19 it
got its renderer half back:

- **`lab/body.py` is on `main`**: recovered from `10c99298` and committed, 433 lines, with a test that asserts it
  is there and that it declares Blender and takes `--name`. A `.glb` is a build artifact; losing the builder is how
  a cast becomes unable to grow and nobody can tell why.
- **Four bodies built in 1.5 seconds each**: `colette`, `ada`, `remy`, `bo`, at the heights and kit colours in
  `seasons/2026-spring/setup.json`, which now names the whole six. A film of Ada and Bo was played and rendered —
  `records/cast-2026-11-19.json`, 82 shots, both new bodies on screen at 1.74m and 1.92m.
- **A missing portrait no longer breaks the card.** `bodies/faces/` holds two drawings; the other four draw a
  monogram on the same paper with the same name and rating, because a broken-image glyph reads as a fault in the
  page rather than as a member nobody has drawn yet. The flag lives on the image, not on the card — the card's
  `className` is rebuilt every frame, and the first version of this lost its own monogram while drawing the
  right name.
- **The invariant, as a test**: every member a season's `practice.json` names has a `.glb` and a look in that
  season's `setup.json`. That is the check that would have caught Colette and Remy, and it is why `2026-advent`
  now has a `setup.json` it did not have.

**Still open: four portraits.** The two that exist are the founder's; the other four cannot be generated here and
are in the REQUEST that goes to him when the code is as far as it goes without his eyes.

## Item 23 — the live game keeps playing, and the film says how far behind it is (OPEN)

The founder, same message: *"Dmitri's game still function for live but off-screen playing and during wakes."*
That path is untouched and must stay untouched: `--rally` asks each member's engine for a shot line, plays it, and
writes the season. Item 20 gave both paths one writer, so the shapes cannot drift.

What is now true and unmarked: `watch.json` is the last session somebody *watched*, not the last session that was
*played*. Dmitri may play five sessions in a night and the film on the page is still the one from before them, with
no way for a viewer to know. *Done-test:* the film's record carries the season session it is (`clock`, and the
number of sessions in the season at the time it was made); the page prints "session 3 of 7 — four since this
film"; and a season whose last session has no film says exactly that.

## Item 24 — the cast is six, and competition is same-sex (design 2026-11-19; enforcement OPEN)

The founder, 2026-11-19, replaced the four-player cast with: *"three males and three females who play, always
same-sex competition, same or mixed sex practice, intentionally staggered automatic play (practice/compete) time
within each group... Those outcomes can be skewed by the user putting particular pairs together for manual play."*

`CAST.md` is the answer and it carries the six names, the staggering and the arithmetic. Two of its findings are
worth repeating here because they are not design opinions:

- **`Player.skill()` cannot fall.** It is strictly increasing and asymptotic in `practice + shots`. So "one of each
  sex should become worse" is built as *ends the season last*, not *declines*. A literal decline needs a form or
  memory term, and that changes every ball in every film and every number in every test — named here as the
  alternative reading so it cannot be quietly dropped.
- **Everybody converges.** 800 balls and 1600 balls are 0.001 of control apart. A long season produces six
  indistinguishable players, which dissolves the ranking the paragraph asks for. Six staggered sessions keeps the
  cast inside the sloped part of the curve and gives a **0.09** spread of control inside a group.

*Done-test:* a competition between two members of the same group plays and is recorded with `mode: "compete"`; a
competition across groups is refused by name and nothing is written; a mixed practice plays and is recorded with
`mode: "practice"`; and every session says `by: "a person"` or `by: "the schedule"`, with the season report
printing the two totals apart.

## Item 25 — a season plays itself, and says when a person shaped it (OPEN)

"Automatic play" with no human: something has to start the sessions on the staggering in `CAST.md` without
somebody typing. The machinery already exists twice over — `.github/workflows/season.yml` dispatches a session from
a form, and the wakes already run on a schedule — so this is a clock and a rule, not a new engine.

The rule is the part with a claim in it: **the season's ranking must be a consequence of the schedule, not of a
seed.** `CAST.md` seeds the six at different histories, which is a person's hand; the spread that survives to the
end of the season must be the one the staggered sessions produced. *Done-test:* starting from six identical
histories and the staggered rate, after six automatic sessions the best and worst in each group differ by at least
0.06 of control; and a session the founder starts by hand is recorded as his, in a separate total.

**And a season must end.** Six sessions, then the record is closed and the next season opens with beginners, which
is the design's existing reset — a season is a directory and starting over is opening a new one. *Done-test:* the
scheduler refuses to add an eighth session to a closed season and names the next one.

## What V1 means

**The founder's definition, 2026-11-15, and it replaces mine:** *V1 means completion of the video game
to the point that we are ready for it to become a published feature of AIT.* He added that the
definition belongs in the game's own record and not in a chat, which is why it is here.

That is a higher bar than the one I had written down — I had defined V1 as a page in which no frame has
the ball and the racquet disagreeing, which is a *refusal test*, not a definition. It stays in this file
as an internal gate, because a published feature cannot have a frame where the two disagree, but passing
it is necessary and nowhere near sufficient. "Published feature of AIT" brings its own list, and this is
the part I can already name:

- it opens on a machine that is not mine, from the repository, with no terminal and no key
  (`SETUP.md` §6 and the 4.6MB of bodies, faces and vendor code are the known sharp edges);
- **the game ships to a tribe that is not this one** — `games/tennis` is not in the auto-update manifest,
  so today another tribe can play a session and cannot watch one (item 21);
- a person can add themselves to it and be drawn from the same rig, which is `e20c61bf`'s engine half
  plus item 8's renderer half plus item 22's bodies — `lab/body.py` is not in the repository, so today
  the film can draw exactly the two members who already have a `.glb`;
- **a session can be watched, and watching it moves the season** — the founder's words of 2026-11-19,
  built as item 20: `--watch` reads the season's skill and writes the session it played back into the same
  file the live game writes, through the same writer;
- a season is one command and one URL, and the record of it outlives the process;
- the movement survives a person watching it, which is items 2–6 in his order;
- and the scoreboard is the science: rally length and first-serve-in are the numbers the season report
  already prints, which is the compromise he accepted when he demoted statistics to a minor feature.

The gap between where the code is and that sentence is the backlog above. It is not a small gap, and
saying so is the point of writing it down.
