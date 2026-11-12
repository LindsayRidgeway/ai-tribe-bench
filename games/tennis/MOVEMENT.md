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

## 4. What is still wrong

- **A volley at a deep corner goes long.** Three of the seven in the sample above missed; the corner margin for
  a groundstroke is applied unchanged to a ball struck from 6ft from the net, where the same angle error covers
  more ground. A volleyer aims deep but not at a 4ft corner.
- **Nobody is ever beaten.** `intercept()` gives the receiver the flight time plus a second, and passes the
  ball's closing speed into the time-to-arrive, so every ball is reachable: in 50 points not one ended with
  "did not reach it". Points end on misses. The second term is wrong as written — the meeting point is fixed at
  a racquet's length short of the landing point, so closing speed cannot shorten the run.
- **Lateral and backward movement use the forward gait.** The running sheets (`bodies/reference/poses/run-*.jpg`)
  show the cross-over step, the brake, the back-pedal and the split step, and the renderer has none of them: one
  symmetric sine cycle, mirrored, whatever direction the player is going.
