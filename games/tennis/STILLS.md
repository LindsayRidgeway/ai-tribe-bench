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
