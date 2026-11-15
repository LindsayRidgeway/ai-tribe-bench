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

## Item 10 — nobody is ever beaten

`reachable()` passes the closing speed into a meeting point fixed a racquet's length short of the landing point, so
every ball is reachable: in 50 sampled points, **not one** ended with "did not reach it". Points end on misses only.
This is not a look — it is the game refusing to model the thing that makes tennis a contest.

- **Do:** replace the closing-speed shortcut with a real interception: step the ball's plan position after the
  bounce (0.02s steps, until the second bounce), and call it reachable only if the player could arrive by then at
  `movement_speed` plus a racquet's length. A ball that crosses away from the player becomes a winner, recorded as
  `met: false`.
- **Done-test:** over 50 points, 10–30% of balls are *not* reached by the weaker player, and the reason string names
  the wide vs deep ball correctly. **Number:** reach-rate before and after, per player; and the effect on the
  learning curve (`test_rally_length_responds_to_hands_and_to_learning` must not get worse).
- **Guard:** a beginner must still be able to play a rally. If the reach-rate for `reach=0.35` drops below 70%, the
  model is too harsh and the racquet radius is wrong, not the idea.

## Item 11 — the volley to a deep corner goes long

Three of seven sampled volleys missed: the groundstroke's corner margin is applied unchanged to a ball struck 6ft
from the net, where the same angle error covers more ground.
**Done-test:** 7/7 volleys from the forecourt land in, with the margin scaled by distance from the net. **Number:**
mean landing distance inside the baseline, before and after.

## Item 12 — the arms never come back to the right side during a run

One pose carries the whole carry phase; a running player's racquet should come back to the hitting side as they
move. **Done-test:** in a sampled run, the racquet head crosses from the non-hitting side to the hitting side at
least once per stride pair. **Number:** crossings per 10 strides, before and after.

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
