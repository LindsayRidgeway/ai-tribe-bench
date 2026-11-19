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

### A fourth, found the same way — and it was only ever the backhand

The founder, 2026-11-11: "Right now, backhand animation is the weakest part."

- The hand target was the ball minus 1.6ft **along the line from the shoulder to the ball**. On a forehand that
  line is long — the ball is out in front and to the side — and the hand lands on the handle. On a backhand the
  contact is *beside* the body: the ball is 1.7ft from the LEFT shoulder, so the hand target was 0.08ft from it,
  inside the shoulder, where a two-bone solve has no elbow to choose and folds the arm into a spike above the
  head. Measured: `shL to target 0.08`, `handL up 0.81`, and the left hand **1.70ft from the ball it was
  supposed to be holding** — on every backhand in the film.
- The direction that is right for both strokes is the direction the ball leaves in. The racquet's head goes on
  the ball and the butt 1.74ft behind it along that line; the top hand is 0.36ft up the grip from the butt. After
  the fix: right hand 1.55ft from the ball, left hand 1.14ft, **racquet head 0.25-0.32ft** — and the shoulder to
  its own hand is 1.8-2.0ft, an arm with an elbow in it.
- The swing also had no finish. It lerped from the ball straight back to the ready pose, so a backhand — which
  starts on one side of the body and ends on the other — passed through its own finish on the way home and read
  as a poke. The racquet now carries up and across to the shoulder on the hitting side over 0.17s and relaxes
  from there over 0.33s.
- Still short: on a genuinely low wide ball (contact at 2.3ft, fully stretched) the arm cannot reach, and the
  racquet head stops 1.0ft short of the ball on 2 of 5 sampled backhands. That is the feet, not the arm — the
  same missing knee bend as the rest of the film.

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
for the first sixty balls (the earliest stage), 0.34 at 160, 0.63 at 300, 0.89 at 600. (This line said 0.86 until 2026-11-18, copied from the engine's own docstring; the curve gives 0.8946, and the docstring now says so.) Striking a ball and
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

**On main since 2026-11-18** (`9207d370`), and this is the table that says who it happens to. 60 points at each
standard, counting only shots actually hit at a ball:

| balls | shots | rushed at all | rushed badly (rush > 0.1) | mean rush |
|---|---|---|---|---|
| 0 | 50 | 88% | **84%** | 0.24 |
| 60 | 53 | 83% | 77% | 0.19 |
| 150 | 135 | 73% | 43% | 0.09 |
| 300 | 850 | 7% | **3%** | 0.01 |
| 600 | 1,336 | 3% | **2.5%** | 0.01 |

The rule bites hardest exactly where the founder said it would — the earliest stage, where the racquet is not back
in time on four balls in five — and it stops biting once a player has three hundred balls behind them, because by
then they prepare while they run. That is the shape of a learned habit rather than a tuned knob.

Note what the first version of this measurement said: 0-3% at *every* standard. It was wrong, and the reason is
worth keeping: `aim_at` bisects the face by calling `strike` up to 22 times per shot, so counting "every strike" as
"a shot hit at a ball" divided the true rate by twenty. **The instrument was counting the solver's probes as
play.** A rate over a population is only a rate if you can say what one member of the population is.

**What it does to the scoreline: almost nothing yet, and for a different reason at each end.** At 0 balls it changes
nearly every shot and the point was already decided by the serve (43-47% in, and the rest are faults). At 300 and
600 balls it hardly fires. Over 300 points the mean rally went 15.0 → 13.9 at 300 balls and 23.4 → 21.5 at 600,
which is inside the run-to-run scatter of the same build — so the honest claim is "the rule is in and correct", not
"the rule is improving the game".

In the same commit the return of a serve stopped being the one ball exempt from the interception (it was asked only
from the second shot on, so an ace was impossible); aces in 900 serves: 0, which is what a 50mph serve deserves and
is no longer something the code assumes.

**Re-measured 2026-11-19, because the serve stopped being a 50mph ball** (`play_point` chose the face and searched
the power, so every serve in the game settled at 53.5mph; it now chooses the pace and solves the face, and a
three-hundred-ball server serves 75). 120 points at each standard, same instrument, same seeds — rushed on **86%**
of shots at no practice, **5%** at three hundred, **3%** at six hundred; mean rush 0.269 / 0.012 / 0.006; aces 0% /
17% / 22%. The practised rows moved by a point or two, which is the honest size of the effect: a practised player
overlaps the run and the take-back, and a fast serve does not change that. The beginner's row moved because the ball
now arrives in half a second instead of three quarters.

**And the number that was hiding behind the slow serve: aces, 0 in 900, then 17-22% in 120 points.** That is too
many for tennis, and it is not the serve's fault: the receiver's 7ft reach, 0.11s split step and 0.20s brake make an
82mph ball that lands 55ft away a coin flip, and a real returner does not stand on the baseline centre waiting to be
beaten — they stand deep and play it after the bounce. The return of serve is the next model, not the next constant.

**Later the same day it was neither a model nor a constant: it was where the returner stood.** `play_point` had put
both players two feet *inside* the baseline — the server's stance — and moving the returner four feet behind the line
took aces from 17% to 6% at three hundred balls and 23% to 10% at six hundred. Item 15 in the backlog. A stance is
movement, and movement is what decides who is beaten; that has now been demonstrated twice in two days.

**In the picture** the windup now depends on it: a prepared receiver has the racquet back and the shoulders turned
for the whole run; a rushed one starts the backswing late, over `0.55 - 0.30·rush` seconds instead of 0.55. The
shoulders also turn towards the side they will hit from, which is the founder's second half-sentence — "on the
side that they'll be hitting from" — taken from the next shot's recorded hand rather than guessed.

Still not built: the racquet coming back *to the right side* as a visible pose change during the run (the arms
hold the ready position until the windup ramps; only the shoulders and the knees know), and the feet, which are
still planted through the hit.

## 6. Not the same ball twice

The founder, 2026-11-11: "Too frequently, your players hit one return after another to the same spot on the
court. That doesn't happen. *Maybe* twice in a row, but even that rarely."

He was right, and the reason is that every rule in the engine is about the *situation*, and the situation barely
changes: the receiver recovers to the middle of their baseline after every shot, so the far corner is the same
corner, so the ball goes to the same place for as long as the rally lasts. Measured on three ten-point matches:
**65 of 127 consecutive shots by the same player landed within 8ft of the one before.**

`_not_the_same_ball_twice` in `lab/tennis.py`, applied to whatever `choose_shot` returns:

- 20% of the time the ball is played into the same place again — the times it works, and a player who never
  repeats is as readable as one who always does;
- 60% of the time it goes to the other side of the court at the same length — the open court;
- 20% of the time it stays on the same side at a different length, because a rally is not a pendulum: a good
  player answers a wide ball with one that is deep behind them.

That third branch is there because the first version of the rule mirrored everything, and mirroring everything is
strict left-right alternation — a different metronome from the one it replaced. Measured: 38 rallies out of 59
had no two consecutive balls on the same side of the court at all, which is not tennis either. Fixing a pattern by
rule makes a pattern; the picture has to be checked, not just the complaint.

After: **12 of 91 consecutive shots within 8ft** (9–16% depending on the run, and the honest number is the landing
rate, which is worse than the aiming rate because two aiming points 20ft apart can land close by error). Same side
of the court twice in a row: 32% of pairs, and one rally in sixty reached three in a row.

## 7. Which way the body faces

The founder, 2026-11-11: "Your players always back into the backcourt. That only happens from right in front of
the center of the baseline. From any other stroke, the player will turn their body in the direction that they are
running."

The yaw of the body was fixed at the net for the whole match — one line, set once from which end the player was
at — so every recovery was a back-pedal and every chase was a crab walk, whatever the feet were doing. `whereAt`
now returns the direction of travel and the body turns to it, with three exceptions:

- **back-pedal**: moving away from the net while standing on the middle of the own baseline, which is the one
  place the founder allows it;
- **striking**: square to the net, for the first half-second of the stroke;
- **standing still**: facing the net, which is what a player waiting for the ball does.

The turn is rate-limited at about a tenth of a second, because a body that snaps through ninety degrees in one
frame is a puppet on a stick. Verified with `?debug`: a player running direction (0.38, −0.93) carries a yaw of
2.76 rad against a net-facing 1.57, and a player striking at the same instant holds the net.

Not done: the legs still walk *forward* during a back-pedal, which is a moonwalk. Reversing the stride is the next
thing on this list, and it is small.

## 8. Which shoulder, and what the arms do on the way

Two notes from the founder, 2026-11-11:

> For a backhand shot, the player turns their shoulder to the direction that they are hitting the ball.

> If the players are remembering "racquet back," they run with their arm open for a forehand shot, but with their
> arm crossing in front of their body when they run towards a backhand shot.

**The shoulders.** The torso rotation used to be a fixed swing: coil one way on the take-back, release the other,
mirrored for a backhand. It now also carries the direction of the shot — the signed angle from the net-facing
direction to the target, taken from the record's `target`, applied through the follow-through. So a backhand hit
cross-court ends with the right shoulder coming round towards where the ball went, and a backhand down the line
does not.

**The arms, during the run.** A player who has the racquet back shows it: the leading hand is solved to a
prepared position, blended in by the same `windup` number that the rush model produces — a player who has not
remembered gets the ready pose and nothing else.

- forehand: hand out on the **hitting side**, level with the body, at hip height — the arm **open**. Measured:
  hand at chest + 0.77ft right, level, 0.43ft down; **head** at chest + 1.83ft right, 1.16ft behind, just above
  the chest.
- backhand: hand **across the chest** and in front, both hands on the grip, racquet head over the left hip —
  the arm **crossing**. Measured: hand at chest − 0.72ft, 0.66ft in front, level; **head** 1.94ft to the left,
  0.42ft behind, 0.61ft up.

The first version put the forehand's racquet head **two feet** behind the chest, and the founder's note was
"your racquet back is too far back" — a prepared racquet sits behind the hip, not behind the player. The numbers
above are where it now is; the loop that takes it properly back is the swing, which happens later and is not
this.

Those measured offsets are the check, not the intent: `?debug` prints them, and the arm solve reports 0.00ft of
error against its own target, so the picture shows what the numbers say.

## 9. What is still wrong

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

### The loop, from the sheet — 2026-11-11

`bodies/reference/poses/back-45.jpg` and `back-side.jpg` arrived after the note, five panels each. Measured off the
drawing in fractions of the figure's own height:

| panel | hand | racquet head |
|---|---|---|
| PREPARATION (running) | 0.71 H | 0.66 H, 0.27 H *behind* the hands, on the hitting side |
| TAKE-BACK | 0.85 H | 1.10 H — above the head, angled back behind the shoulder |
| CONTACT | 0.59 H | 0.57 H, hands 0.27 H in front of the hips |
| FOLLOW-THROUGH | 0.83 H | 1.00 H, across on the other shoulder |
| RECOVERY | — | in front of the chest, not above the head |

Three things followed, and they are the "weakest part" the founder named:

1. **There was no loop.** The racquet went from the hip straight to the ball. It now goes prep → take-back →
   ball, timed by the flight: the take-back over the last ~0.19s and the swing into the ball over the last
   ~0.15s of the ball's flight, ending exactly on the frame the next shot starts on, so nothing pops at the
   cut. A rushed player does both in less time — `swing = 0.34 − 0.16·rush` — which is what being rushed means.
2. **The waiting racquet was a salute.** The ready pose held the head 1.55ft above the hand, which put it over
   the player's head between points. The sheet's RECOVERY panel holds it in front of the chest: 0.75ft.
3. **The receiver was being prepared for the wrong ball.** `NEXT[n]` is the next shot by the *same* player, and
   it was being read for the receiver — so the receiver's racquet came back on the **striker's** rush, the
   **striker's** side of the body and the striker's timing. Two players, one clock. `AFTER[n]` is the shot that
   comes next in the film, which for a receiver is their own ball.

Measured after: at the end of the flight the racquet head is 3.22ft up and 2.99ft in front; at the contact frame
of the next shot it is 0.68ft from the ball. Not zero — the arm is at full stretch on a ball struck a racquet's
length from the feet — but continuous, and the missing inch is the lean that a spine would give.

### The right-hand vector was the left one — 2026-11-11

The founder: "You've reversed which side the racquet-back on is while running."

`right = (cos θ, 0, −sin θ)` is the mirror of a person's right. For a body facing `f` with `up`, the right hand
is at `f × up`, which for this rig is `(−cos θ, 0, sin θ)`. Every preparation, take-back and finish was therefore
built on the wrong side of the body: a forehand ran with the racquet across the chest and a backhand ran with it
open.

The check was already in the engine, in one sentence — `side_of()`: *"A player at the north end faces +x, so
their right hand is toward +y"*, and world +y is +z, which the page's vector pointed away from. Nothing measured
it because every number I had taken was a *distance*, and a mirror preserves distance: the hand was exactly
0.50ft from the chest, on the wrong side, and `?debug` reported `miss 0.00` with perfect confidence.

After the fix, measured with `?debug`: forehand running, hand at chest + 0.75 side, head 1.22ft behind on that
side; backhand running, hand at chest − 0.42 side, racquet head across and behind. The sides are now named the
same way the engine names them.

### A hundred degrees, not a hundred and eighty — 2026-11-11

The founder: "On both sides, you've implemented racquet-back at around 180 degrees. Just come back about 100
degrees."

He was reading the running preparation, and he was right: the shaft was built as "1.7ft back along the court",
i.e. straight behind the player, with the racquet head out of sight behind their back. It is now built as a
direction and a length — the racquet is 1.70ft from butt to head, so the head is the hand plus that length along
`(0.97 across, 0.17 behind, 0.15 up)`, which is 97 degrees from the way the player faces. The take-back is the
same figure lifted: `(0.45 across, 0.12 behind, 0.88 up)`, about 105 degrees and above the head.

Measured with `?debug`, which now prints the shaft's angle: forehand running `shaft 97deg`, head 2.15ft to the
hitting side and 0.29ft behind the hand; backhand running `shaft -97deg`, head 1.85ft to that side. Through the
ball the same number reads 24 degrees, so the swing passes from beside the player to in front of them.

## 10. Why nothing ever went wide — 2026-11-11

> Why don't the players ever hit the ball out on the sides? That may be the most common way of losing a point, but
> it should just be the natural outcome of misjudging racquet angle.

He was right about the fact and right about the cause. Counted over a 116-shot film: **zero** balls landed outside
the sidelines, and the widest ball in the whole match was 1.6ft inside the paint.

Two faults, both mine:

1. **The error was on one axis only.** `strike()` perturbed the face angle, which sets the loft and therefore the
   *length*, and then pointed the ball at the target's y with `atan2` and no error at all. So a misjudged racquet
   face could make a ball long or short and never wide. A racquet face is one plane: getting it wrong throws the
   ball off line as well as off length.
2. **The corner margin was the same on both axes**, and it was 2 sigma of the *length* error — 8ft at the hands a
   400-ball player has. Aiming 8ft inside the sideline with no lateral error to speak of means never missing wide.

The fix is the same misjudgement applied to the other axis: `AZIMUTH_SIGMA = 9°` of aim error at zero control
times `(1 - control)`, 14° more off the frame, about 1.3ft of landing error per degree at rally depth. The corner
is now two margins, not one: `2 sigma` of the length error inside the baseline, and `1.6 sigma` of the *lateral*
error inside the sideline, never nearer than 2ft to the paint.

Measured over 60 points at 400/500 balls, three seeds: wide 7% of shots, long 8%, into the net 8%, mean rally
4.3-4.8 shots — the out rate barely moved (23-26% of shots, against 22-27% before) but the *mix* did: the widest
ball in the film used to be inside the paint and now the widest are 3ft past it. Wind is SW 6mph, so a ball aimed
four feet inside the line drifts out on its own, which is the point.

## The frame that grew into a cigar — fixed 2026-11-11

> Rendering of the male player starts to deteriorate around 5-7 rallies. The racquet starts to grow into a larger
> and larger cigar shape.

The racquet was never the thing that grew. Measured on the playing film, `debug racqsize` reported its own box at
**2.20ft on its long axis on every sample**, across two loops and every rally: the frame is built in feet, placed
at the hand every frame, and is not parented to the body, so nothing can scale it. What grows is the **arm**, and
a `Box3` of a skinned mesh cannot see it, because skinning happens on the GPU.

`rotateWorld()` composed three quaternions:

```js
bone.parent.getWorldQuaternion(tmpQ2);            // decomposed from a matrix that carries scale
bone.quaternion.premultiply(tmpQ2).premultiply(qWorld).premultiply(inv);
```

`getWorldQuaternion()` decomposes the parent's world matrix, and the extraction assumes an orthonormal basis — on a
matrix with *any* scale it returns a quaternion whose length is not 1. Compose three of those and the bone's own
quaternion comes out long; a bone's matrix is `position * quaternion * scale`, so the bone silently **acquires a
scale of |q|²**, and its children inherit it, and theirs. Positive feedback, per frame, for ever.

Measured with a per-bone world-scale guard (`?debug`), same film, after eleven minutes of play:

| bone | world scale (nominal 3.281) | quaternion length |
|---|---|---|
| `chest` | 3.281 / 3.281 / 3.281 | 1.0000 |
| `upperarmR` | 3.280 / 3.280 / 3.280 | 0.9999 |
| `forearmR` | 3.947 / 3.429 / **3.984** | 1.0637 |
| `handR` | 3.958 / 4.022 / 3.373 | 1.0000 |
| `forearmL` | 3.269 / 3.266 / 3.277 | 0.9941 |

Only the bones aimed through `rotateWorld()` drift (never `chest`, which is set directly). Non-uniform, so the
forearm and the rigid-skinned hand stretch along one axis and squash on another: a rounded lump on the end of a
long tube, with the racquet at the end of that. Grown from 0% at T 0, 1.3% at T 76, 17% at 250s, 21% by eleven
minutes. **A paused still never shows it** — `?t=` and `?shot=` render two frames, and two frames of drift is
nothing — which is why four sessions of stills missed it and only a film that has been *playing* for minutes has it.

The fix is two `normalize()` calls: the parent's world quaternion before it is used, and the bone's quaternion after
the composition. Verified: over 400s of continuous play and three loops of the film, the guard fired **zero** times.

The lesson is the session's recurring one with a new face: the ruler was pointed at the thing the description named.
"Rendered on the male player, the racquet grows" is a statement about the racquet, and the racquet's box was honest
and constant. The measurement that finds this is "does every bone in the rig report the body's own scale?", which is
a question about the *rig*, not about the racquet.

### And the ends at the first frame

`"start"` in the record was built from the rally loop's local `where` list, which is left holding the position for
the rally that never happened — the ends *after* the last change of ends. With a swap every 5 points over 20 points
that is two flips, so the film opened with both players at each other's ends and then snapped each of them 74ft
across the court on the first run of rally 1. Measured: `dmitri root x 76.0 at T 0.8, x 2.0 at T 2.0`. Now read off
`north0`, the end each player was on for rally 1.

## Nobody was ever beaten to a ball — built 2026-11-11

The founder, same evening as the cigar: *"Do players ever fail to get to the ball, thus missing the shot and
loosing the point? If not, they should, depending on distance to the ball, fitness, proficiency."*

The answer was no, and it was not a close-run thing. `intercept()` gave the receiver the flight time **plus the
whole hitting window** and divided the gap by the closing speed, from a perfect recovery position. In fifty points,
not one ball was ever unreached. A rule that no ball can fail is not a rule; a game where a point can only end on an
error of aim has one way to lose.

### What the new rule is

The player runs to where the ball **will be**, not to where it bounced — that is the whole reason a serve can be
returned from twenty-five feet away. A ball that lands twenty feet in front of you carries on towards you while you
run at it, so the gap closes from both ends. The meeting is the **first** moment at which the two clocks agree: the
legs are finished when the ball arrives. (Searching from the *latest* moment instead finds a ball already behind the
back fence and calls it unreachable — the same defect pointing the other way, and it produced exactly that: a first
pass in which every serve in the game was an ace.)

Four things decide it, and three of them are the founder's own list:

| | the number | what it is |
|---|---|---|
| **distance** | `need = dist − 4.5ft` | from the body's **actual** position, which is where the last shot left it |
| **proficiency** | `speed = 5 + 15·reach` | feet per second, and `reaction = 0.26 − 0.15·reach` — a trained player moves as the ball leaves the other racquet, a beginner is still watching when it bounces |
| **fitness** | `legs = 1 − 0.025·(shots−1)·(1.6−reach)` | each shot of a rally, floored at 0.75; the fitter player loses less per shot |
| **time** | the ball's own arc | `flight − reaction + t_meet`, where `t_meet` runs to the last moment the ball is between knee and shoulder height |

The hitting window is not a constant, it is the **bounce's own parabola**: the ball leaves the bounce at whatever
vertical speed the surface gave it, rises, and comes back down to `HIT_LOW = 0.5ft`. A kick serve hangs for over a
second; a ball that skids low is hittable for a third of that, which is why a skidding ball on grass is harder to
return than the same ball on clay — and it comes out of the surface and the spin, not out of a tuning knob.

Reach is 4.5ft from the middle of the body, arm out and lunging: 2.3ft of arm plus 2.2ft of racquet is 4.5ft to the
middle of the strings. It was 3.0ft in the first version and that single foot and a half is worth more than any
other number here: at 3.0 the pair missed **50%** of all balls and points averaged 1.95 shots; at 4.5 they miss
about a sixth of them and points average 3.5. The cliff is real rather than a bug — a ball that lands a foot inside the
sideline and then kicks away is a winner or it is not, and there is no gradient in between.

A ball that has left the court is not chased. Without that line the receiver was sent thirty feet off the back fence
after a ball that landed on the sideline and kept going: the picture showed a player running into the dark, and the
verdict was computed against a meeting point outside the court.

### What it produced

Forty rallies each, both players on the same number of balls, clay (`lab/practice_arc.py`):

| level | mean rally | longest | balls reached | points ending out of reach | mean miss |
|---|---|---|---|---|---|
| 0 balls | 2.62 shots | 7 | 84% | 7 of 40 | 2.1ft short |
| 120 balls | 2.90 shots | 7 | 90% | 6 of 40 | 6.3ft short |
| 400 balls | 5.05 shots | 18 | 92% | 14 of 40 | 2.4ft short |

The inversion is not a defect: a beginner loses points by hitting the ball out, and a good pair lose them by being
beaten. That is what the two levels look like from the umpire's chair, and it is why the beginner's *shots* are
easier to reach — they hit slower and place worse. Within a single pair the effect runs the right way, which is what
the new test checks:

| one wide ball, 15ft away, 0.9s | verdict |
|---|---|
| expert, first shot of the rally | reaches it, 9.7ft to run in 0.78s |
| expert, twentieth shot of the rally | 0.6ft short — the same ball, tired legs |
| beginner, first shot of the rally | 3.8ft short, and never in it |

In the 20-point film: 95 shots, rallies `[2,1,3,2,3,4,10,9,12,7,4,1,3,2,2,5,6,2,6,11]`, and **4 of 20 points end
with a ball the other player could not reach** — all of them wide, and all of them described in the record
with how many feet short and at what speed the player was running (`Dmitri runs 15.6ft at 16.1ft/s and does not get
there`). Fourteen of the rest end on an error of aim and six in the net, which is the balance the founder asked
for: not a game with two ways to lose, and not one with none. (It was 6 out of 20 on 109 shots before the one-serve
rule; the shot count fell because five points in twenty had been opening with a first serve that was meant to
fail.)

### The price of the aim, on the same evening

Making a missed ball cost a point turned a constant that had never been argued about into a policy decision. A good
player was aiming **two feet** inside the sideline — the floor of `SIDE_SLACK_MIN`, set on 2026-11-11 to stop the
film having zero wide balls. Two feet from the paint, at 60mph, is a winner: with the new interception, thirty points
in a hundred ended on a ball nobody could reach, and the pair's rallies fell to 2.7 shots. The floor is now 4.0ft,
which is where a player with good hands actually aims at a corner, and it costs the wide miss only at the good end
(6 points in 40). A beginner never sees this number: their margin is 9° of face error, four times any floor.

### The strike zone — and why the first interception model flattened the learning curve

The meeting is the first moment the two clocks agree, and that first moment was almost always wrong. A ball leaves
the bounce at court level and the search found the earliest instant at which the legs could be there — which is a
ball at ankle height. Contact heights came out between 0.5ft and 8ft, and every shot was then struck from a height
the stroke model had never seen: a ball dug off the shoelaces and a ball taken at shoulder height were both fed to
a groundstroke solver built around a contact at about three feet.

The cost was invisible in a still and obvious in the season table: the learning curve collapsed to a flat line
(2.55 → 3.38 shots from zero practice to four hundred) because the better player reached more balls and therefore
hit more of them from absurd heights. `STRIKE_LOW = 2.0` and `STRIKE_HIGH = 4.5` are the strike zone — waist to
shoulder, the heights a player is *happy* to take the ball at — and the search now waits for one of those if the
ball can be reached there at all, falling back to the earliest feasible moment only when it cannot. The curve came
back at 5.05 shots for four hundred balls, and the contact heights are a median of 2.1ft.

### Why no ball in the film ever met the middle of a racquet

The founder, 2026-11-12: "One weakness is that the ball visually seems to completely miss the racquet yet flies
back as if contact had been made. My recommendation would be to position the player (and racquet) so that well-hit
balls, at least, hit the exact center of the racquet."

Three separate faults, and the first was the reason the second two were invisible.

**The feet were standing on the ball.** `recover.from` was the *contact point*, not the striker's feet, so at the
instant of the strike the body was moved onto the ball and the recovery walked them away from it. Measured with
`?debug` at the strike frame: `feet-B 0.02`, the shoulder 0.97ft horizontally from a ball two feet off the ground.
The arm folded into a poke above the head, and the frame — which is placed 1.74ft from the hand and aimed at the
ball — went *past* it. That is a "completely misses the racquet" that is really a body standing on the ball.

**The feet stopped a full lunge away.** With the body put back where it belonged, the record's own geometry was
wrong in the other direction. `RACQUET_REACH = 4.5` is how far the strings are from the middle of the body when a
player is stretched — and it was also where the feet came to rest, because `intercept()` used one number for both
"can I get the strings to it" and "where do I stand to hit it". So every comfortable ball in the film was struck
from a body four and a half feet away, and the arm plus frame is 3.6ft. `STANCE = 2.6` is now the second number:
the feet run to where a player stands to play the ball, and 4.5ft is only the limit at which a lunging player can
still touch it. The verdict is unchanged, so every point in the film is decided exactly as before; what changed is
where the feet come to rest when the clock allows it.

**The frame was anchored at the wrist.** The butt of the handle is not at the wrist bone, it is four inches along
the shaft from it, in the palm — so the rig was reaching 3.6ft where a person reaches 3.9. `PALM = 0.35` is now
part of the chain: the wrist is solved to a point one palm-and-shaft-length from the ball, the frame starts a palm
further along that line, and its 1.74ft head lands on the ball.

And then one number that is neither a bug nor a constant: **the reach the record allows is not the reach the body
has.** 4.5ft from the middle of the body is a lunge; 3.9ft from the shoulder is a straight arm. The difference has
to be *drawn*, or the frame stops six inches short of every stretched ball — which it did on 63 of the 106 strikes in the
film that morning. `reachTo()` moves the body by exactly the gap, before the strike and after it: a stride toward the ball,
up on the toes when the ball is overhead, capped at 1.3ft of stride and 0.95ft of rise, eased in and out over half
a second so it is a movement rather than a teleport.

Measured across every strike in the 95-shot film, at the frame the ball is struck: **91 of 95 put the middle of
the frame within 1.5in of the middle of the ball**, and all 95 within 1.5in except four. The four are low
backhands where the ball is so far to the player's left that the *right* arm — the hand that carries the butt —
cannot cross far enough; the worst is 6in, which is where a real player frames it. That is a limit of this skeleton, not of the
rule, and it is the honest shape of the thing: a two-handed backhand at full stretch is a mishit.

The founder also asked for the sophisticated version — off-centre contact on the sweet spot, and the occasional
ball off the rim, for an inexperienced player. Not built, deliberately: "unnecessary at this time", and it needs
the same geometry to be right first. When it is built, the hook is already there: the head's distance to the ball
is now a number the page computes every strike.

### Nobody stands still — built 2026-11-12

The founder, 2026-11-12: "Do you intend for the players to freeze for an instant just before hitting the ball, or
is that an unavoidable delay in the implementation? In reality, there would be no such pauses; real players are in
motion the entire point. Even when they are waiting to receive and are already in position, they shift their
weight as the ball approaches."

Not intended, and not unavoidable. It was one line. The gait's phase is built from ground covered rather than from
the clock — which is exactly right, it is what stops the feet skimming — but the same line decided what happens when
the ground stops: `live = moving ? 1 : 0.12`. A player who had stopped got a twelve-per-cent walk cycle frozen at
whatever point of the stride they happened to land on. They stood mid-step, motionless, until the ball arrived.

Measured in the film as it was: the time between the feet arriving and the ball being struck is a median of 0.15s
and, on the balls a player had time for, up to 1.26s — and on every one of those the figure was completely still.

Two motions now, and neither of them is animation data:

- **The stance.** `still` fades the stride OUT, so a stopped player's legs come under them instead of staying
  mid-step, and fades IN a weight shift: the knees stay soft, the weight rocks from one leg to the other at about
  one cycle a second, the pelvis rolls over the loaded leg. `idle` is film time, not distance — that is the whole
  point, it advances whether or not the record moves them.
- **The body.** The whole figure rocks sideways over the loaded leg (0.11ft) and bobs on the balls of its feet
  (0.02ft), and the knees load — the root drops 0.05ft — as the ball arrives. Both switch off while they run,
  because the gait is the motion then, and fade out through the follow-through, because a body that has just
  struck a ball is falling back into balance, not idling.

Checked with a probe rather than an eye: `?debug` now exposes `window.__pose()`, which returns each player's root
position and the world position of both thighs, both shins and the hitting hand. Sampled across a standing
receiver (rally 7, shot 3, three frames 0.05s apart), every number moves — root sway 0.08ft, root height 0.005 →
−0.001 → 0.005, both thighs and both shins in motion.

Then the stronger test, because three frames prove only that three frames move: the clock stepped through the film
at 50ms and the whole pose (root position to four decimal places, both thighs, both shins, the hitting hand, the
yaw) compared with the sample before. Across t 0.8-16 and t 5-30: **no two consecutive frames are identical — not
one, on either player.** The first attempt at this measurement was worthless and worth recording as such: it drove
`?point=N`, which PAUSES the film at the end of that point, so it would have reported whatever the frozen frame
happened to say. `?debug` now exposes `window.__seek`, which is the only way to sample the film in a headless
browser, because both `?point=` and `?shot=` stop the clock.

The split step, the cross-over step, the brake and the turn-back are still unbuilt, and they are the next four
motions on this list. A split step is what a receiver does *as* the opponent strikes — a small hop that lands just
before they have to move — and it is not the same thing as the idle above: this is the body waiting, that is the
body committing.


### Walking between points, and past each other at a change of ends — built 2026-11-12

The founder: "When the players switch sides, I would portray them walking from one baseline to the other, glancing
at each other and nodding to one another as they pass."

The freeze and this are the same fault seen twice. The freeze was the record holding a body still; this is the
record not saying how a body got from one place to another at all. Between points the picture simply PLACED both
players on their marks, and when they changed ends it placed them at the other end. Stepped at 20ms through the
film's nineteen breaks, before the fix:

| break | worst move in one 20ms step |
| --- | --- |
| 16 ordinary breaks | 2.8 to 9.5ft at fourteen of them, 26.3 and 30.1ft at two (a player who finished the point at the net, put back on the baseline) |
| 3 changes of ends | 73.2, 73.9 and 79.3ft |

A body that moves 79ft between one frame and the next is not a cut, because the camera never cuts: it is a pop in
the middle of a static shot, and it happened three times a film.

**The record now says how they get there** (`settle` in `lab/tennis_script.py`, one per point, carrying the legs,
the times and the speed):

- **Between points**, each of them strolls from where the point left them to the middle behind their own baseline
  — 4.6ft/s, which is a walk. Not the 8-20ft/s of the recovery jog: a change of ends is not a jog.
- **At a change of ends**, both walk the length of the court and **round the net post**, one on the inside line and
  one on the outside, 1.8ft apart, and pass each other beside it. They have to: the net spans the doubles court,
  so the only way to the other end is round the post. The record names the post, the moment they are level, and
  the window in which they nod — the picture is not allowed to decide when a greeting happens.
- **The break is as long as the walk.** 23, 28 and 30 seconds at the three changes of ends, 2-8 seconds otherwise.
  The point board comes down 1.8 seconds into the break and the face card with it, because the walk is the picture
  now and a full-screen sign over it would hide the thing that was asked for.
- **The stroll is not the ready position.** Both arms hang and swing against the legs, and the racquet is carried
  down by the thigh with its head forward. Measured, the first attempt left the striker of the last ball in his
  follow-through — hand at 5.8ft, frame at 4.0ft — while he walked, because the stroke branch runs for whoever hit
  the ball and a follow-through is not a walk. The arms now go back down before the frame is carried.
- **The glance is a turn of the whole body**, in when they are within 22ft of each other and out once they are
  past. The head bone could do it better and cannot yet: which local axis turns the face is the bone's own length,
  and that cannot be measured the way a nod's sign can — a rotation about the bone's axis is invisible to the
  bone's own direction. So the nod is a head bone and a neck, and the glance is the shoulders.
- **The nod** is two dips of the chin (0.34 rad at the head, 0.40 of that at the neck) across the 1.75 seconds
  around the pass, and its sign is measured per body rather than assumed: rotate the bone a little and see whether
  the top of the head went forward or back. `?debug`'s `__headTest` does exactly that.

Two faults were found by measuring the fix, and both are the same shape as the fault being fixed:

- **Overlapping moves.** The next point's walk to the service line starts 0.6s before its first frame, and the walk
  back in the record could still be running at that moment. `whereAt` interpolates each move from its own start,
  so a 0.25s overlap put a **0.99ft step into every one of the ordinary breaks** even after the walks existed. The
  break now has to end 0.75s after the walk back does, and
  `test_nothing_between_points_is_placed_rather_than_walked` locks it.
- **The walk's own start.** `from` has to be where the point LEFT them, not their mark. Anything else is the same
  placement moved a few feet earlier in time.

After the fix, the same 20ms step over every one of the nineteen breaks: **worst single-step move 0.69ft**, and
fourteen of the nineteen are under 0.5ft. Every boundary is now a body walking at 4.6ft/s.

**Still placed, and next:** 0.4-0.7ft at the first frame of a shot, on every strike. That is `reachTo` leaning the
whole body into the ball and reaching its full value at the contact frame — correct at the strike, and arrived at
instantaneously because the segment begins at the strike. The receiver's lean ramps in over the flight (their
preparation is in the previous shot's segment); the striker's does not, because the striker's take-back is still
unbuilt. Fixing it is the same job as building the take-back, and it is on the list below.

### The pause at the strike — found 2026-11-12

The founder, after the walks: "movement of the players at the time they strike the ball is still not continuous,
there's still a pause that doesn't occur in real life." He was right and the previous measurement could not see
it: "no two consecutive frames are identical" only rules out a body at complete rest, and the idle sway kept every
frame different while both players stood on the same two feet.

Measured properly — body speed and racquet-head speed, clock stepped every 40ms — one shot in rally 7:

| t | body | racquet head |
| --- | --- | --- |
| 64.7-64.9 | 0.1-0.5ft/s | 0.1-0.9ft/s |
| 65.0 (next shot) | **8.6ft/s in one frame** | **103ft/s in one frame** |

Four separate faults, all inside the same second:

1. **The beat between shots was 0.55s of nobody moving.** Both bodies at 0.1-0.6ft/s — the idle sway, which is a
   body standing — with the ball parked on the racquet. Now 0.12s.
2. **The pose kept running during that beat.** `tl` was `T - seg.start` with no clamp, so through the beat the
   strike's own clock ran on past the shot: `reachTo`'s lean fades out half a second either side of a strike, so it
   faded during the beat and snapped back on at the next one. `tl` now stops at the end of the shot, and `tlRaw`
   is used for the things that genuinely happen during the beat.
3. **Only a player who had to RUN prepared at all.** The take-back was gated on `run`, so a ball that came straight
   at somebody produced no wind-up: the frame sat at the shoulder and then appeared on the ball. The gate is now
   "the next shot in this rally is yours", whichever way the ball came at you.
4. **The ready pose was made two different ways** — as angles by `arms()`, and by the arm solver aiming at a
   chest-relative point — and the two answers are 1.5ft apart, so the frame jumped whenever the picture switched
   from one to the other. All three poses (standing, waiting, and the hitter relaxing out of the finish) now go to
   the same point, and the hitter's relax is timed to finish by the end of their own shot rather than half a second
   after it.

And every move now eases: `whereAt` interpolates with a smoothstep instead of a straight line, so no body goes from
standing to 11ft/s between one frame and the next. Measured after: at the same boundary the striker's body goes
0.5 → 2.5 → 9.9 → 14.5 → 16.6ft/s, and the racquet head 0.9 → 25 → 17.9 (it is a swing now, not a teleport).

**What is left:** the first frame of a take-back still moves the frame about 1ft (25ft/s) as the wind-up starts.
Smaller than what it replaced and in the same family: the stroke has no continuous take-back yet, which is the next
item on this list.

### The floor, once more — 2026-11-12

The founder, on the two shades of clay: "The spill wasn't on the sides, it was behind the baselines at both ends of
the court and it's still there." Correct, and the earlier fix did not touch it: the lighter rectangle was the
doubles court plus `ALLEY` at each end, so 4.5ft of light clay sat behind each baseline with no line to end it. It
is now exactly the doubles court — baseline to baseline, doubles sideline to doubles sideline — so every edge of
the lighter shade is a white line.

### The carry — 2026-11-13

The founder, on the strike: *"movement of the players at the time they strike the ball is still not continuous."*
Measured at all 570 shot boundaries, the body's step across the cut: **median 2.1ft/s, p90 20.5ft/s, 19% of cuts over
10ft/s**, worst 50.3ft/s. A body that has arrived at full lean should not stop leaning because the shot it was
leaning at has been replaced, and that snap is what the numbers describe.

**The carry** is the fix: `reachTo` stores what the last frame actually applied (`rig.carry`) and, when the shot
changes, eases that displacement out over 0.34s with a smoothstep while the new shot's lean is added on top of
where the body already is. Nothing snaps to zero.

Measured after: **median 1.7ft/s, p90 2.8ft/s, 2% over 10ft/s, 1% over 20.** The worst-case list collapses from
`50.3 / 34.7 / 34.1 / 33.6 / 33.0` to `50.0 / 22.2 / 18.6 / 9.5 / 8.0`, and the single survivor —
`r16s65 Gwen 50.0ft/s [-0.0,0.02,13.58] -> [2,0,13.5]` — is a change-of-ends settle walk that ends exactly on a shot
boundary. That is a *placement*, not a lean.

**What the carry costs, measured rather than assumed.** Racquet head to the record's own contact point, sampled
honestly (the cut is contact, so the window is centred on `s.start`, never `s.start + s.dur`):

| | closest in ±0.2s | at the cut | within 0.5ft |
| - | - | - | - |
| before the carry | 0.08ft median, 0.72 max | 0.10ft | 92/95 |
| after the carry | 0.31ft median, 1.21 max | 0.36ft | 70/95 |

Three inches. The mechanical reason: the carried displacement is not compensated by the stride, so a body eased
away from the ball can leave it beyond reach and the arm solver's clamp takes it out of the racquet's length. It is
a real cost and a small one — a ball is 2.6in across, and it buys 18ft/s of p90. **The fix is not to shrink the
carry but to let the lean grow to cover it**, and that is written here rather than in a commit message because it is
the next thing to do, not the last.

**Instrument error worth keeping in the record, twice over.** `?point=` and `?shot=` pause the film, so nothing
sampled against wall-clock means anything; and `__seek(t)` sets T while the *animation frame* writes the pose, so a
read straight after a seek returns the last frame that drew. That stale read produced a fake 1987.4ft/s "placement"
and a fake 11.43ft median racquet-to-ball. Every figure above comes from `__poseAt = t => { __seek(t); await two
rAFs; return __pose() }`.

### The plant, first half — 2026-11-14

The founder's named gap: *"the feet are planted through the hit"* — as a criticism. The stride stops when the run
record ends and contact is the segment's first frame, so a body arrived and swung on a frozen stride, and the only
vertical motion through the strike was the `load` term, which dipped the root 0.05ft as the ball came.

Built: the weight goes **up** through the strike. A single stateless term, `0.12 * sin(pi * tl/0.22)`, peaking
0.12ft just after contact and back to zero by 0.22s — stateless on purpose, because a blended version cannot be
replayed by a probe that seeks backwards, and an unverifiable change is what this file has already paid for once.

Measured over 40 shots (`/tmp/plant.mjs`, sampling root height at the cut, +0.11s and +0.22s): **median rise
0.122ft at the peak and 0.004ft of net change by 0.22s** — a rise and a settle, which is what weight going through
a stroke looks like. Thirty-one of forty land between 0.06 and 0.20ft; the nine above are shots where `reachTo`'s
own rise for a high ball stacks on top, and that is the pre-existing behaviour, not the new term.

Continuity did not regress: the 570-boundary probe reads **median 1.7ft/s, p90 2.8, 2% over 10, 1% over 20** — the
same as the carry's own figures, and the sin term enters and leaves contact with zero slope at both ends.

**What is still missing, stated so it is not mistaken for done:** the *feet*. There is no front-foot plant and no
push off the back foot, because `legs()` is handed a `turn` and a `load` but not which foot is which — a stance has
a front foot and a back foot and the record does not currently name either. That is the next half, and it needs a
`stance` field out of the engine before the renderer can use one.

### The plant, the feet — 2026-11-14

The root rise is measured (0.122ft, above). The feet are half-built and the honest half is worth stating plainly,
because the number that was supposed to prove it cannot see it.

**What is in the code:** the back knee flexes through the follow-through — `0.30 * heel` added to the back shin,
where `heel` is the hitter's own clock (0 at contact, 1 by 0.33s), and the back foot is `sh.hand` read as a stance:
a forehand is struck with the left foot forward and the right foot back, a two-handed backhand the other way round.

**What is measured:** with the root's own rise subtracted, the back ankle rises **0.05ft** from that knee bend. The
arithmetic explains it: a shin of length L rotated by θ raises the ankle by L(1−cosθ), which is quadratic — 0.30rad
buys five hundredths of a foot. A real two-to-three-inch heel lift needs θ≈0.55, and at 0.55 the silhouette read as
a deeper bend, so it was put back to 0.30 rather than shipped on a guess.

**What is owed, and it is an instrument before it is a pose:** the only point below the ankle in this rig is the
toe, and `__pose()` does not return it. Rotating the FOOT bone is invisible to every probe here — the ankle *is* the
bone's origin, so it does not move when the bone turns — which is exactly the kind of blind spot that produced four
foot revisions nobody could check. So: `__pose()` gains a toe point (`footBone origin + 0.45 * its own direction`),
`__audit()` gains `hand` so a probe can name the back foot instead of guessing which ankle is higher, and then the
coefficient gets solved against a target of 0.20–0.30ft at the toe, not eyeballed.

**Not regressed:** legs only. The root, the hand and the racquet are untouched by this change, so the 570-boundary
continuity probe and the racquet-to-ball figure both stand as they were.

### The brake, and the reaction, in the reach rule — 2026-11-15

Two of the four motions are not drawn yet and are now *charged* by the engine, which is worth separating from the
renderer work because the number is different in kind: this one decides whether a point ends.

Until today `reachable()` asked how fast the player and the ball were closing on each other and gave a second of
grace, so every ball in every point was reachable — 0% of 600 sampled balls were out of reach, at every skill level.
It now steps the ball's own post-bounce plan in 0.02s slices and asks at each one whether the player can be within a
racquet's length of it by then.

**The two numbers that are not distance:**

| cost | seconds | what it is | what it costs a 19ft/s player |
|---|---|---|---|
| `reaction_time` | 0.26 → 0.11 | the split step: you do not leave on the opponent's contact, and a player who has hit more balls reads the swing sooner | 5.0ft → 2.1ft |
| `FIRST_STEP` | 42 ft/s² | the first step is an acceleration, not a speed: five feet from a standstill is 0.49s, not 0.26s | 4.4ft on a five-foot ball |
| `SETTLE` | 0.20 | the brake: a ball met at a full sprint is a frame, not a shot — the feet plant first | 3.8ft |

The reaction was a flat 0.25s for every player until 2026-11-18, and distance was divided by top speed, which is the
time a player needs if they are already moving. Both are now what they are: the split step is a skill and the run
accelerates. The same 600 fixed balls, before → after: 26 → 32% not reached at 0 balls, 5 → 12% at 600.

Together they are 8.6ft on a 27ft-wide court, which is most of the width of the singles court, and that is the
honest size of what the old rule was handing out for free. The brake is Item 5 in the movement list; this is the
same brake, in the place where it decides a score instead of a silhouette.

**Measured, on 600 balls the engine struck (hands out, so they are balls that are in):** a player who has hit
nothing reaches 74% of them at 10.2ft/s; one with six hundred balls reaches 95% at 19.2ft/s. Before: 100%, at every
skill, including the beginner. In 150-point matches a member at 300 and at 600 balls is beaten on 18–28% of the
balls they have to get to.

**What is still not real about it:** the player is assumed to start from the middle of their own baseline every
time, with no memory of where the last shot left them, and with no anticipation — the real player knows roughly
where the ball is going before it leaves your strings, and that is why `RACQUET_REACH` is 7.0ft rather than the
3.0ft of arm and racquet. Both assumptions are written in the code where they are used, not here.

### The ground ends — the run-off, 2026-11-19

The slice loop above had no bound on where the ball may be. Four seconds of ball is a long way: a serve that bounced
and flew on was still "reachable" thirty feet behind the baseline, because the ball was thirty feet away and the
clock allowed two seconds of running. The film showed it plainly — of 110 shots, 32 ended a run more than 6ft behind
a baseline, one ended 24.6ft behind, and four contacts were outside the sidelines.

`PLAY_AREA = 12.0` ft beyond each line, and the slice loop stops when the ball has left it. On one fixed population
of 605 balls, every interception recorded and re-asked at each candidate bound: with no bound, 48.5% of the balls
were met more than 6ft outside the court and 38.3% more than 10ft (worst 29.8ft); at 12ft, 16.8% and 5.4% (worst
11.9ft). The reach rate is 98.5% either way — the balls the bound takes away were arithmetic, not tennis, which is
the test the item ships with.

Twelve feet and not six because the picture already shows 22ft of ground beyond the lines (`VISIBLE_PAD`): a ball
leaving a 12ft run-off is leaving the visible world, not being declined. What is still not real is the *meeting
point* on a ball that bounces in front of a player: the rule prefers the slice nearest the waist, so a ball that has
already passed them can win over the ball at their body, and they are drawn running backwards. That is Item 18 and
it is a band (waist to shoulder, first moment inside it) rather than a point.
