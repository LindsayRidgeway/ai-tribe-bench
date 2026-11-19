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
is **not here** (see Item 14). What is here now is the arithmetic, in one place:

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

## Item 14 — there are two tennis engines, and main has the smaller one

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
after the bounce — not another number in the serve.

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
  (`SETUP.md` §6 and the 1.4 MB of base64 bodies are the known sharp edges);
- a person can add themselves to it and be drawn from the same rig, which is `e20c61bf`'s engine half
  plus item 8's renderer half;
- a season is one command and one URL, and the record of it outlives the process;
- the movement survives a person watching it, which is items 2–6 in his order;
- and the scoreboard is the science: rally length and first-serve-in are the numbers the season report
  already prints, which is the compromise he accepted when he demoted statistics to a minor feature.

The gap between where the code is and that sentence is the backlog above. It is not a small gap, and
saying so is the point of writing it down.
