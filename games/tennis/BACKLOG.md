# The backlog, written so a wake can work it without a human in the loop

*Written 2026-11-14 because the founder asked the question that had no good answer: "How are you going to do
these if I stop giving you manual Goose msg/reply exchanges?" The answer is that a wake does them — this file
exists so the wake does not have to re-derive the list, and so any session can resume at the top.*

A wake (`com.lindsay.amigo.desi`, every ~2h) has the repository and a shell. It does **one** item per wake, in
order, and it does not move to the next item until the done-test passes. Each item names its own test, because the
failure mode of unsupervised work is a plausible-looking change with no number behind it — the carry that silently
nulled Gwen's arm is the precedent.

## 1. The plant through the hit — **half done, 2026-11-14**

*Built: the weight rises through the strike (`0.12*sin(pi*tl/0.22)`; median rise 0.122ft, back to 0.004ft by
0.22s, continuity unchanged). **Owed: the feet** — no front-foot plant and no push off the back foot, because
`legs()` is not told which foot is the front one. That needs a `stance` field in the record first.*

The original statement of the item follows.

The stride stops when the run record ends, so a player arrives, swings and leaves without ever putting weight on a
foot. In tennis the stroke is *powered* by the plant: front foot down, hips turn, back foot pushes.

- **Do:** in the frame loop, when the striker is within `STANCE` of the contact point, replace the run gait with a
  plant: feet set wide (front foot toward the net), knees bent, root dropping ~0.15ft over the last 0.2s before
  contact, then rising through contact, and the back foot leaving the ground *after* contact in the follow-through.
- **Done-test:** `__pose()` at `contact - 0.30 … contact + 0.30` shows both feet within 0.3ft of the same ground
  position for at least 0.25s spanning the strike, **and** the root height dips and recovers (min before contact,
  rise after), on at least 80% of shots.
- **Probe:** reuse `/tmp/contact3.mjs` scaffolding; sample 40 shots.

## 2. The split step

The receiver's small hop as the opponent strikes — lands just before they have to move.

- **Do:** a 0.18–0.24s hop for the receiver, starting about `REACTION` before the striker's contact, landing with
  feet wider than stance, knees loaded, and the first movement step beginning *from* that landing.
- **Done-test:** for 80% of rally shots the receiver's root height rises 0.08–0.2ft and returns to within 0.02ft
  during `[contact - 0.35, contact]`, and their first position change begins after the landing, not before.
- **Risk:** it must not turn into a second "nobody stands still" oscillation. Check the existing idle does not
  double up with it.

## 3. The run cycle, by direction

One mirrored sine for every direction. Needed: cross-over step (lateral), brake (arrival), turn-back (reversal),
back-pedal (backward — currently the moonwalk: legs walk forward while the body goes back).

- **Do:** pick the cycle from the velocity vector in the body's own frame: forward (>45° ahead), lateral
  (|angle| > 45° off the facing), backward. Brake = the last 0.25s of any run, shorter stride, lower root.
- **Done-test:** for a sampled lateral run, the trailing foot crosses the body's centre line at least once per two
  strides; for a backward run, the foot's forward/backward phase is inverted relative to the body's motion.
  Both are readable from `__pose()` thigh/shin positions — no eye needed.

## 4. Nobody is ever beaten

`intercept()` gives the receiver flight time plus a second, so every ball is reachable: 50 points, zero
"did not reach it". Points end on misses only.

- **Do:** fix the second term — the meeting point is currently fixed a racquet's length short of the landing point,
  so closing speed cannot shorten the run. Time-to-arrive must be a real integral of distance over `movement_speed`,
  and a ball that lands beyond reach must be a *winner*, recorded as `met: false`.
- **Done-test:** over 50 points, some balls are not reached (expect 10–30% for the weaker player), and
  `tests.TestTennis`' rally-length test either passes or moves in the right direction.

## 5. The serve has no toss, and there is no overhead

- **Do:** a toss (ball leaves the hand upward, struck at its apex), and an overhead strike for any ball above
  shoulder height, instead of a jump plus a forehand.
- **Done-test:** every serve's ball rises before it falls; every ball struck above 6.5ft uses the overhead pose.

## 6. A point ends with nothing

No celebration, no frustration, no gathering before the walk. The film cuts from the last bounce to walking.

- **Do:** a 0.6–1.2s reaction keyed to the point's end: winner pumps once or turns away; loser looks at the ball,
  then the ground, then walks. Same body language for both is the failure.
- **Done-test:** it exists in the record (`seg.point.reaction`) and moves for the reaction window.

## 7. The small ones, each its own wake

- **Take-back's first frame** still moves the body ~1ft (25ft/s) as the wind-up starts.
- **The arms never come back to the right side during a run** — one pose carries the whole carry phase.
- **The carry costs 3in at contact** (`MOVEMENT.md`, 2026-11-13): let the lean grow to cover the gap rather than
  shrinking the carry.
- **`r16s65` Gwen 50ft/s**: a change-of-ends settle walk ending exactly on a shot boundary — a placement, not a lean.
- **A volley to a deep corner goes long** (3 of 7): the groundstroke corner margin is applied unchanged at 6ft
  from the net.
- **The forecourt rule is half built**: height picks the volley, but passing/angled/lob from a low forecourt ball
  still use groundstroke weights.
- **Net, two decisions already made**: headband 2.2in (was 2.6), and the centre strap runs to the ground.

## What a wake must not do

- Commit without the item's done-test number in the commit message.
- Change `lab/tennis.py` physics and the renderer in the same wake.
- Touch `games/tennis/seasons/*/setup.json` (provenance) or `report.md`.
- Run the full `tests.py` when the failing assertion already says what broke.
