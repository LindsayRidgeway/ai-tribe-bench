# Movement — where the players are, and why

The founder's rule of 2026-11-11, verbatim:

> The court in front of the baseline is never used by good players to receive the next shot, because the
> opposing player will fire to one of the back corners and the receiver won't be able to get to it. Of course,
> sometimes the player has to move there to return a shot, but they will always immediately try to get back to
> center court behind the baseline, or move up into the forecourt to volley (hit the ball as it comes over the
> net before it bounces), and often (but not always) before it drops too low. You can see that from the
> forecourt, the height of the ball when struck has a much more significant effect on the receiver's options:
> a drop-shot, a passing shot, a lob to the back court, a sharply angled shot to the side.

Everything below is that rule, built.

## 1. Nobody receives from the forecourt

`recovery_spot()` in `lab/tennis.py`. After every shot the player's `where` becomes:

- **behind the baseline at the centre** — `(-1.6, WIDTH/2)` at the north end, `(LENGTH+1.6, WIDTH/2)` at the
  south — unless the shot was an approach or a volley, in which case
- **seven feet from the net** — the position a volleyer actually holds.

Each shot carries a `recover` record: from the contact point, to that spot, over `min(2.5s, distance/speed)`,
with the ground covered. The renderer walks the legs along it. Before this, `where` never moved after contact,
so both players drifted forward over a long rally and stayed in the forecourt — which is exactly what the
founder described as wrong.

`in_time` on the record is *not* "they got back": at 400 balls a player moves at 19ft/s and always gets back
inside the cap. It is the harder claim — back in the middle before the ball they had just hit had landed —
and it is true of about 3 recoveries in 4.

## 2. A volley is decided when the ball arrives, not when the turn comes round

`volley_contact()` in `lab/tennis.py`, called from the *receiving* half of `tennis_script.py`.

The racquet sweeps a volume: 4.5ft from the middle of the body, 3.5ft to either side without moving the feet,
2.2ft to 8ft off the ground, at least 2ft on the player's own side of the net — and the volume grows with the
flight time, because the player has that long to get a leg to it. The earliest moment the volume reaches the
ball is the contact.

Three versions were needed and the first two failed in instructive ways:

1. scanning for the ball "level with the player" — a place the ball reaches twice, and it returned the frame
   where the ball crossed the net forty feet from anyone's racquet;
2. solving a fixed meeting plane 3ft in front of the stance — which put the contact 4ft past the net, where a
   driven ball is still going up at seven feet, and returned nothing at all on every ball that landed short of
   that plane. It also never fired, because the receiving check had already run: a net player could not get
   *back* to the landing point, so the point ended, while the whole reason they were standing there was to take
   the ball before it landed. **That was the bug that mattered.** Ordering, not physics.

Result at 400/500 balls, ten rallies, one seed: 7 volleys in 85 shots, 6 approaches, rally lengths
`[3,17,2,28,2,9,6,4,3,11]` against `[4,2,2,2,2,7,2,2]` before the recovery and volley work.

## 3. From the forecourt the height of the ball picks the shot

`choose_shot(..., height=z)` — `z` is the ball's height at contact, and passing it means the player is taking
the ball out of the air. The weights change with height:

| height at contact | what is on |
|---|---|
| ≥ 5.0ft (high volley) | drop volley, angle, drive, lob |
| 3.4–5.0ft (comfortable volley) | drive, angle, drop volley, lob |
| < 3.4ft (low volley) | dig it deep or lob it — **no drop**; there is nothing under the ball to cut |

A volley is also a punch, not a swing: everything is played at 80% of the equivalent groundstroke's pace, and a
drop volley lands 5–9ft past the net rather than 8–13.

## 4. Which stroke it is — forehand or backhand

The record now says: `hand: "fore" | "back"`, taken from which side of the body the contact is on, which the
engine has always known (`side_of`) and never wrote down. The renderer needs it twice:

- **the shoulders turn the other way** for a backhand — the windup and follow-through are mirrored;
- **the other arm leads**: the left hand on the ball and the right hand on the handle below it, which is the
  two-handed backhand most club players own and what the reference sheets kept drawing whenever the racquet
  crossed the body.

### Three bugs found by measuring the hand's distance to the ball

`?debug` now prints, for the hitter, the distance from each hand to the ball at contact. It read 2.46ft on every
shot while the target was 1.6ft away.

1. **The lerp was inverted.** `target.lerp(wait, k)` with `k = 1` at the strike sends the hand to the *ready*
   position at the moment of contact and to the ball afterwards. It should be `lerp(wait, 1 - k)`. The racquet
   followed the same lerp, so **no frame of this game has ever had a racquet on the ball**: it sat at the chest
   through every stroke. That is most of the "statue reaching for something" reading.
2. **The contact point was on the player's own feet.** `carry` was the meeting point, and the meeting point is
   where the feet stop, so the body stood in the ball and the shoulder-to-ball distance was 0.9ft. The contact
   is now the landing point, with the feet a racquet's length short of it.
3. **CCD could not fold.** The old solver rotated joints towards the target, which stalls when the target is
   close to the shoulder. It is now a two-bone law-of-cosines solve with the elbow on a circle broken by a pole
   (elbows point down), reading both bone lengths off the rig. The hand now lands 1.60ft from the ball, which
   is what was asked for.

## 5. The racquet comes back on the way, or it does not come back in time

The founder, 2026-11-11:

> Inexperienced players don't know to get their racquets back as they're running, and it leads to mishits because
> they can't get the racquet back fast enough. Good players virtually always get their racquets back while
> running to the ball, but on the side that they'll be hitting from. I'm not sure how quickly players learn to do
> this; after the earliest stage, they'll remember to do it more and more, but it won't be an instant
> transformation.

This is a fourth skill, `prep`, and it is not another copy of `control`. `strike` multiplies the face error by
`1 - 0.45·rush` and the chance of hitting the strings by `1 - 0.55·rush`: a rushed player both sprays and frames.

**Rush is arithmetic, not a dice roll.** The racquet takes `PREP_TIME` = 0.55 s to come back. A player with the
habit takes it back *while* the legs work, so the run and the preparation overlap and all they need is
`max(run, prep)`. A player without it does them one after another — run, arrive, then start the racquet — and
needs `run + prep`. `prep` slides between the two, and `rush = (required - flight) / required`. Learning does not
make the ball slower; it makes the two things happen at once.

**The curve has an onset, and it is slower than the others.** `prep = 1 - exp(-max(0, balls - 60) / 240)`: zero
for the first sixty balls (the earliest stage), 0.34 at 160, 0.63 at 300, 0.86 at 600. Striking a ball and
remembering to prepare for it are different skills and do not arrive together.

Measured over 30 points at each standard —

| balls | shots rushed | miss rate when rushed | miss rate when set | mean rally |
|---|---|---|---|---|
| 0 | 25/25 | 64% | — | 2.6 |
| 60 | 29/30 | 72% | — | 2.5 |
| 150 | 36/37 | 78% | — | 2.7 |
| 300 | 35/124 | 43% | 17% | 5.4 |
| 600 | 6/172 | 50% | 16% | 6.9 |

At 150 balls every ball is rushed and a rally is under three shots. That is not a bug in the arithmetic, it is
what that standard of player is, and it means the demo has to be generated with practised players or it shows
nothing but mistakes.

**In the picture** the windup now depends on it: a prepared receiver has the racquet back and the shoulders turned
for the whole run; a rushed one starts the backswing late, over `0.55 - 0.30·rush` seconds instead of 0.55. The
shoulders also turn towards the side they will hit from, which is the founder's second half-sentence — "on the
side that they'll be hitting from" — taken from the next shot's recorded hand rather than guessed.

Still not built: the racquet coming back *to the right side* as a visible pose change during the run (the arms
hold the ready position until the windup ramps; only the shoulders and the knees know), and the feet, which are
still planted through the hit.

## 6. What is still wrong

- **A volley at a deep corner goes long.** Three of the seven in the sample above missed; the corner margin for
  a groundstroke is applied unchanged to a ball struck from 6ft from the net, where the same angle error covers
  more ground. A volleyer aims deep but not at a 4ft corner.
- **Nobody is ever beaten.** `intercept()` gives the receiver the flight time plus a second, and passes the
  ball's closing speed into the time-to-arrive, so every ball is reachable: in 50 points not one ended with
  "did not reach it". Points end on misses. The second term is wrong as written — the meeting point is fixed at
  a racquet's length short of the landing point, so closing speed cannot shorten the run.
- **The feet are planted through the hit.** The founder's other named gap: the stride stops when the run record
  ends, so there is no plant, no weight transfer and no push off the back foot.
- **Lateral and backward movement use the forward gait.** The running sheets (`bodies/reference/poses/run-*.jpg`)
  show the cross-over step, the brake, the back-pedal and the split step, and the renderer has none of them: one
  symmetric sine cycle, mirrored, whatever direction the player is going.
