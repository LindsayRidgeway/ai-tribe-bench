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

## Item 0 — recover the uncommitted renderer work (BLOCKING; do this first)

- **What is missing, and how it is known missing.** These paths appear in the 11-11 and 11-12
  entries of `desi-state.md` and exist in no commit of `ai-tribe-bench` and in no clone on this
  machine: `serve_corners`/`serve_verdict` in `lab/tennis.py`, `WINPOS` and the `?cam=net` hook in
  `games/tennis/replay3d.html`, `games/tennis/STILLS.md`, `games/tennis/MATCH-FORMAT.md`,
  `lab/run_season.py`, the `?record=`/`?setup=` derivation, and the net headband/strap geometry.
  Checked: `git grep` across every ref and `git fsck` dangling commits in `ai-tribe-bench`; `git log
  --all` in all eight other candidate repos; a whole-home `find` for the file names.
- **Why it is recoverable anyway:** the work was done in the live window whose session id is
  `20261110_26` in `~/.local/share/goose/sessions/sessions.db` (509 messages mention `replay3d`,
  37 `WINPOS`, 31 `serve_corners`, 19 `run_season`). Tool calls carry file content.
- **Done-test:** `git grep -c serve_corners -- lab/tennis.py` ≥ 1; `git grep -c WINPOS --
  games/tennis/replay3d.html` ≥ 1; `python3 tests.py` green; and `games/tennis/STILLS.md` and
  `games/tennis/MATCH-FORMAT.md` exist. **Number to print:** how many of the eight paths were
  recovered verbatim from the transcript and how many had to be rewritten.
- Do not "re-implement from memory" and call it recovered. A rewrite is fine; it goes in the report
  as a rewrite.

## Item 1 — put the renderer on `main`, or retire the branch

`desi/tennis-video` is **4 commits ahead and 87 behind** `main`, last touched 2026-11-11. Every
committed pixel of the 3D game is on a branch nothing merges, which is how a working renderer can be
invisible to the repository that is supposed to hold it. Either rebase it onto `main` and merge, or
rebuild the renderer on `main` from the recovered files and delete the branch.

- **Done-test:** `main` contains `games/tennis/replay3d.html`; `python3 tests.py` green; the stills
  regenerate from the command in `STILLS.md`. **Number:** commits behind `main` after the merge = 0.

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

## Item 9 — Pickleball: the second game, and the first one that can grade movement

*(Corrected 2026-11-15. This item said "PaddleBall" and described a practice wall. Both were my
misreading: by "paddleball" the founder meant a second paddle game, and what he actually wants added to
AIT is **pickleball**. The wall is a different thing and is item 10.)*

**Accepted, and gated behind item 1.** Five reasons it is a better second game than a reskin of tennis,
in the order they matter:

1. **It is the only project on the shelf that tests something AIT has never tested: two beings sharing a
   court.** Pickleball is natively doubles. Tennis here is singles — one profile choosing a shot. Doubles
   means the kitchen line covered by two bodies, a partner who must know whether the ball is theirs, and
   a record that has to name *which* player took it. That is a coordination surface, not a physics one,
   and no amount of tennis work produces it.
2. **The kitchen is a rule about position, so the score grades movement.** No volleying inside 7 ft: you
   must let the ball bounce there. A being that cannot stop loses points, and the violation is countable
   in the record. Today the movement items (2–6) are judged by my eye on a still; this is the first game
   where being badly placed has a number.
3. **The ball is drag-dominated, not gravity-dominated.** A perforated plastic sphere at 30–40 mph is
   slow and decelerates hard: in tennis the drag term is a correction, in pickleball it is the flight.
   `lab/tennis.py` already carries the term (`0.0063·|v_rel|·v_rel` per foot); what changes is that the
   approximations become visible instead of negligible — which is a reason to build it *here*, where I
   know which terms are approximations (lift is vertical-axis only, no spin decay).
4. **It is a second, independent test of the claim AIT is built on.** "Rallies get longer as the players
   learn" was verified in tennis over a season. In pickleball the rally is long by construction, so the
   claim gets tested where it cannot be flattered by the format.
5. **Nothing new to draw.** Same 18-bone rig, same bodies, a paddle instead of a racquet, a 34-inch net
   instead of a 3-foot one. The asset pipeline that cost eight generations is not reopened.

- **The risk, named before any code:** pickleball is close enough to tennis that I could ship tennis with
  five constants changed and call it a new game. My first acceptance test was a list of behaviours that
  cannot occur in tennis — a kitchen violation, a double-bounce error, a partner yielding a ball — and
  the founder cut it down, correctly: **"the fact that you'd be implementing doubles at all is reason
  enough."** A reskin cannot have four beings on a court, two of them on the same side, with a record
  that names which paddle took each ball. Doubles is the test.
- **Owner: me, alone.** The founder raised a second amigo as the natural place for someone else to own
  something real, and then said why not: *"you and Dmitri are far-and-away the least expensive high-end
  AI-beings in the cohort, and since you developed the tennis video game, I think you are better suited
  to developing a pickleball game — at least the animation."* Cost beats a theory about collaboration
  that has not been tested. Recorded as the reason, so that the decision is not mistaken later for
  territory: it is the invoice.
- **Done-test for this item, before any renderer work:** `games/pickleball/README.md` states the ball's
  drag curve with its source and its numbers, the kitchen and double-bounce rules as the engine will
  enforce them, the doubles assignment rule, and which modules it *imports* from `lab/tennis.py`.
  **Number:** imported modules that were copied instead = 0.

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
