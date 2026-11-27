# Taking a still

Every picture in `stills/` comes from one command. It lives here because it was asked where it is kept, and the
answer was "in a chat" — which is not a place.

```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --use-angle=metal --run-all-compositor-stages-before-draw --hide-scrollbars \
  --window-size=1440,810 --virtual-time-budget=12000 \
  --screenshot=games/tennis/stills/NAME.png \
  "http://localhost:8778/games/tennis/demo3d.html?point=1"
```

Three of those flags are not decoration:

- `--use-angle=metal` — without it WebGL cannot create a context on this Mac (`VENDOR = 0xffff, GL_VENDOR =
  Disabled`) and the screenshot is a black rectangle.
- `--headless=new` — the old `--headless` gives the same black rectangle even with Metal, and the page's own
  readouts stay at their `—` placeholders because the script never runs.
- `--run-all-compositor-stages-before-draw` — otherwise the canvas is captured before the first frame lands, and
  every still is byte-identical to every other still.

The server is already up at `http://localhost:8778` from `~/ai_tribe` (`python3 -m http.server 8778`). A `file://`
URL will not load the `.glb` bodies, so the page needs the server.

## Jumping to a moment

The page takes three query parameters, all of which pause the film so the still is repeatable:

- `?point=5` — the end of rally 5: the point board, and the clock stopped.
- `?shot=12` — shot 12, with `&at=0.8` to choose how far through it (0 to 1).
- `?t=41.2` — an absolute time in seconds of film.

`?at=` is a **fraction** of the shot (0 to 1), not a number of seconds — a distinction worth writing down
because I lost twenty minutes to it on 2026-11-19 reading `at=2.6` as "2.6 seconds into the shot" and getting a
frame from the next rally. `?at=2.6` is 2.6× past the end of the segment, i.e. the film simply plays on.

**The break is `?point=N` and nothing else.** `?shot=13&at=0.95` looks like it lands on the walk between points and
does not reliably: the settle lives in the segment's `hold`, and a fraction of `dur` cannot address it. `?point=`
sets the clock to `start + dur + 0.02`, holds it there (`playing = false`) and forces the caption up
(`signAlways = true`), which is the only repeatable way to photograph the point board, the face card, or the
monogram that stands in for a member with no portrait. Every still of a break in this folder was taken that way.

`?cam=near` puts the camera beside the near baseline for looking at feet. `?cam=hit` goes over the striker's own
shoulder, and `?cam=net` stands square on to the net from the side — which is the only way to see whether the
headband follows the sag and whether the centre strap reaches the ground.

## A record the page has to fetch

`?record=` is the other half of that: the page fetches a season's `rally.json` instead of the copy baked into the
demo films, and `?setup=` beside it says which body and which look each player has.

```sh
"…/Google Chrome" --headless=new … --screenshot=games/tennis/stills/out-of-reach.png \
  "http://localhost:8778/games/tennis/replay3d.html?record=records/rally-out-of-reach.json&shot=92&at=0.55"
```

`stills/out-of-reach.png` is the first still of a point that is *lost* rather than missed: the ball is past the
player and the caption says how far short of it they were. It took a record rebuilt by `lab/tennis_record.py`,
because no record on this branch had ever had a ball nobody reached.

## Measuring the reach invariant: `run`, not `watch`

The gate this project holds itself to — *no frame where the ball and the racquet disagree* — is checkable from a
record without rendering anything, and the check is one line per shot: the distance from a shot's `contact` to the
hitter's feet must be inside `RACQUET_REACH` (7.0ft), and the contact's height inside `RACQUET_HIGH` (9.0ft).

**The feet are in `run`, not in `watch`, and the difference cost me a false alarm on 2026-11-19.** `run` is the
receiver's movement to the ball that is coming at them: `run.player`, `run.from`, `run.to`, plus `dist` (ground the
feet covered), `gap` (how far the ball was) and `met`. It is attached to the shot that was hit *to* them. `watch`
is something else entirely — a ball going *out*, where the receiver takes one step, reads the length and lets it
go (`watch_out`), so it carries a 0.35s step and not a run to contact.

Walking a record with `watch` put the hitter's feet at their stance from the last serve and reported five
"violations" up to 22.8ft in a film whose true worst contact was **7.005ft against a 7.0ft reach**. The engine was
right and the instrument was wrong, which is the failure mode this file exists to catch. Serve shots are the other
half: a serve's feet come from the `stance` entry on the first shot of the point, because nobody ran to a ball they
are holding.

```python
feet = {}
for s in shots:
    for st in s.get("stance") or []:           # a serve: the stance walked into before the first ball
        feet[st["player"]] = st.get("to") or st["from"]
    f = feet.get(s["player"])
    if f:
        d = math.dist(s["contact"][:2], f[:2])  # must be <= 7.0
    if s.get("run"):                            # the ball in play: this is where the next hitter's feet came to
        feet[s["run"]["player"]] = s["run"]["to"]
```

## The instrument the movement items need: `?sweep`

A headless browser draws about one frame a second of wall clock, so a per-frame log samples the film at random —
which is fine for "where is the toe" and useless for "is there a dip within 0.2s of the contact". Items 3–6 are all
questions about ORDER, so the frames have to be produced in order:

    "…/replay3d.html?record=seasons/<S>/watch.json&debug&sweep=0:130:0.04"

`?sweep=t0:t1:dt` steps the film in fixed steps of RECORD time, calls `tick()` directly instead of waiting for the
compositor, and prints two kinds of line to the console (captured with `--enable-logging=stderr --v=0`):

- `debug segs` — one JSON array: every segment's `[shot n, start, dur, toss, hitter]`. **The contact is
  `start + toss`**, which is not `start`: a serve's segment begins at the throw.
- `debug sweep` — one JSON row per step: `[T, shot n, tlc, [rootY, isHitter], [rootY, isHitter]]`.

Two traps, both paid for on 2026-11-19. **`tlc` is attributed to the segment that owns the time**, and a segment
owns its hold as well as its shot, so the samples during the NEXT shot's toss come back labelled with the previous
shot. The fix is to analyse in absolute time off `start + toss` rather than trusting `tlc` for the baseline. And
**the sweep's range is not the film's length**: a session's film can run 125 s, and a sweep to 60 s will resolve
eleven shots and quietly look like the whole match.

The first measurement of the split step with this instrument: 0.000–0.021 ft of dip over eleven shots. After the
change: 20 of 20 shots inside the founder's 0.10–0.20 ft band, 0.11–0.19 s after contact.

### Three traps, all paid for on 2026-11-20

**1. Without `--screenshot=`, a headless sweep may never run at all.** `window.__sweep` is started from two nested
`requestAnimationFrame` callbacks. `--headless=new` with no screenshot produces no compositor frames often enough for
those callbacks to fire, so the sweep printed `debug setup` and `debug bones` and then nothing — the page loads and the
bodies load, and the run comes back empty, which reads exactly like a broken sweep. Adding `--screenshot=/tmp/x.png`
(any path) makes the compositor run the stages, and the sweep prints. `--run-all-compositor-stages-before-draw` alone
did not. The check that tells the two apart: `?debug&t=5&toe` prints `debug toe` lines per frame only if rAF is
running at all.

**2. `rel()` measures the toe from the ROOT, so it is invariant to anything that moves the root.** Reporting that
column across `&ground=0` and `&ground=1` said "the clamp changes nothing" — the same numbers to three decimals on
both sides — on a build where the median toe went from 0.254ft to 0.020ft. The height above the COURT is
`rootY + rel[1]`, and the sweep row now carries it directly as `[toeL, toeR]` in world feet, because the court *is*
`y = 0`.

**3. A sweep row's player entries are `[rootY, isHitter, yaw, relL, relR, rq, [toeL, toeR], [rootX, rootZ]]`** —
**eight** fields per player, not five and not seven. A script written against the older shape reads `rel[3]` as the toe and silently gets the left foot's
3-vector instead of its height, or reads `rel[5]` and gets `undefined`.

**4. A sweep row is not a plan, and until 2026-11-20 there was no way to ask where a body came from.** `debug plan`
prints every move the page knows about, per player, as `[t0, t1, from, to]`, once, before the rows. It is the line
that found item 2b: a segment pushes its RUN before its STANCE, the stance happens first, and `whereAt` stops the
walk at the first move that has not begun — so the stance never happened and the body was PLACED. Two sweeps, one
number each: **24 frames of the film moved a body more than 25ft/s before the sort, 0 after; the worst single frame
went from 18.91ft to 0.42ft.** A row tells you where a body is; the plan tells you which move put it there.

**5. A sweep log needs a READER, and the reader is `lab/tennis_sweep.py`.** Every number in items 2b, 4 and 5 since
2026-11-25 comes out of

    python3 lab/tennis_sweep.py /tmp/log.txt

which reports the biggest one-frame move any body makes, the frames over 25ft/s, the biggest one-frame rise of either
toe, the per-shot contact speed, and — per run of more than 3ft — which foot is on the side the body is going and
which foot came across first. Three notes it carries in its own comments because they cost a pass each: Chrome echoes
the first rows after the sweep ends (the log is otherwise in time order, so the first row that does not advance is
where the reader stops); `run` in the record belongs to the RECEIVER, not the hitter; and the toe HEIGHTS are a bad
probe for which foot swings (the grounding clamp keeps them within 0.03ft of each other) while the toe's FORWARD
offset separates them by up to 2.6ft.

**6. `?probe=<T>&who=<name>`** prints one `debug grow` line per frame within 0.12s of a film time: `moving`, the move's
window, the distance into the move, `grow`, the phase and the near-side sign. It is how item 2b's remainder was found,
and it is the only instrument here that can say why a body is where it is in the frame it stops.

**7. `debug plan`'s KEY ORDER IS NOT THE ROW'S COLUMN ORDER, and mapping one to the other silently renames the
players.** The plan is filled as the settle moves are pushed, in whatever order they are pushed; `D.players` order is
the film's. On `seasons/2026-11-19` the plan is `[Colette, Gwen]` and the columns are `[Gwen, Colette]`. With two
players, anything that reports "the other one" survives the swap — which is why item 4's answer stood — and anything
that reports the NAMED player does not: item 5's "the striker's root speed at contact, median 0.50ft/s" was the
RECEIVER's, and the striker's own is 1.82ft/s. The mapping is now read off the log's own `isHitter` flag
(`tennis_sweep.order()`), and every column must claim exactly one name or the reader refuses.

**8. A segment's `hold` is the room it was given, not a claim on the next segment's frames.** `shotAt` used to return
the first segment whose `[start, start+dur+hold)` contained the time, and a serve's segment starts a toss (0.84s)
before its contact — inside the break of the point before it. So the break won and **16 of 26 serves in the film never
drew their toss**: the ball appeared at the contact, from nothing. The later start wins now. `debug segs` carries each
segment's window end as a seventh field and `debug film` carries the film's end, so the overlap can be recomputed from
one log instead of being inferred from where a body was.

The measurement this produced, `?sweep=0:18:0.02&ground=0|1` over `seasons/2026-11-19/watch.json` (901 frames):

| | both toes > 0.10ft | samples within 0.05ft | median toe | max |
|---|---|---|---|---|
| `&ground=0` | 823 of 901 | 43 of 1,802 | 0.254ft | 1.080ft |
| `&ground=1` | 60 of 901 | 958 of 1,802 | 0.020ft | 0.898ft |

**9. A SWEEP FINDS ONLY WHAT THE FILM REACHES, AND A DEFECT LIVES IN THE PATH NO FILM TAKES.** Item 2b's biggest
one-frame move was 0.86ft on `seasons/2026-11-19` — and 6.00ft (300ft/s) on the first film a sweep ever had with a
**change of ends** in it, made for a different item entirely. A twenty-rally session does not change ends; a
forty-rally one does. So a number measured on one film is a claim about that film, and the honest form of it is
"the worst move in a film that changes ends: 0.40ft", not "the worst move in the game".

**10. A WALK IS NOT A RUN, AND 58% OF THE FIRST ITEM-12 MEASURE WAS A WALK.** Item 12's question is what the arms
do during a run. The reader counted a frame as "running" when the root moved more than 3ft/s — and the stroll
between points moves at 6-7ft/s, which is *above* that gate. The walk already carried the frame (the racquet goes
down by the thigh and `stroll()` swings the arms), so the population reported the walk's crossings as the carry's
and the fix that followed looked like it barely worked. The line was then read off the film's own speed histogram
— `5:1427, 6:2130, 7:2241, 8:158, 9:140, 10:86, 11:112` — where the bins at 5-7 are walks and the bins at 9-20 are
runs, so 9ft/s is a gap in the record rather than a threshold chosen to make the answer come out.

The lesson is the general one: **a population defined by a speed gate has to be checked against what is actually
moving at each speed**, or a fix gets measured on the frames it does not touch.
