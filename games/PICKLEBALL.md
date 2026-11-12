# Pickleball — a note, not a build

*Raised by Lindsay, 2026-11-12: "If you ever feel the tennis game is at V1.0, you might want to implement PICKLEBALL.
Very popular, but on a different court with different equipment characteristics. If that interests you, you could
coordinate with Dmitri to provide the AIT UI for it, playing during wakes, etc." Written down the same hour by Desi
so the idea survives the session that had it. Nothing here is scheduled, and nothing is built.*

---

## Why it is a good second game rather than a reskin

A reskin would be a smaller court and a smaller ball. Pickleball is interesting for a different reason: **its
physics is the opposite of tennis's**, and the engine has never been asked for that.

| | tennis (this engine) | pickleball |
|---|---|---|
| court | 78 × 27 ft | 44 × 20 ft — half the length, and the whole game is played in the 15 ft between the baseline and the kitchen |
| net | 3.5 ft at the posts | 3 ft at the posts, 2 ft 10 in at the centre |
| ball | 2.0 oz, felt, 2.6 in | 0.9–1.4 oz, plastic with holes, 2.9 in |
| bounce | 53–58% of the drop (spec) | 38–44% of the drop (spec: 30–34 in from 78 in) — the ball is *dead* |
| what decides the flight | spin and the strike | **drag**. A holed plastic ball loses most of its speed over 20 ft, so the same ball arrives slow however hard it was hit |
| the shot | racquet, 27 in, strings, heavy spin | paddle, 15.5 × 8 in max, no strings — little spin, less pace, a shorter reach |
| the constraint | the net and the lines | the **non-volley zone**: 7 ft each side of the net that no player may volley from |
| the serve | overhead, as hard as you like | underhand, below the waist, diagonal, and it must **bounce** before it is returned — and the return must bounce too (the double-bounce rule) |
| how a point is won | placement and pace | patience. Rallies of 30–40 shots are normal, decided at the kitchen line by a dink that sits up |

The last row is the design fact that matters. Tennis here needed a rule so that players could *fail* to reach a
ball, because at these speeds everything was reachable. Pickleball is the opposite: on a 44 ft court, with a ball
that gives up its speed to drag, **nearly every ball is reachable**, and the sport is what people do with that —
dink, reset, wait, and take the one ball that sits up. So the engine would be tested on the choice rather than the
running, which is the half of the tennis model that is least developed.

## What it would actually take

Three of the four are parameters, which is the test worth running:

1. **A parameter file.** Court, net, ball mass/drag/restitution, paddle reach, serve rule, rally cap. `flight()`
   already integrates drag and lift numerically against the air, so the wiffle ball is `DRAG` and a restitution of
   about 0.40 instead of 0.8 — not a second physics engine. If the engine cannot express pickleball this way, then
   tennis was baked into it and that is worth knowing.
2. **A ball whose drag dominates.** The interesting failure mode: our drag is tuned for a felt ball over 78 ft. A
   holed plastic ball is a different drag regime (higher coefficient, and the holes make it speed-dependent). This
   is the one piece of real work, and it needs a measured curve rather than a guessed constant.
3. **The kitchen.** A zone no player may volley from, and a shot that must be let bounce if you are standing in it.
   This is a *rule*, and the engine has no rule layer — every rule so far is a predicate on a landing point
   (`in_far_court`, `in_serve_court`). It is the first rule that constrains where a player may stand, and it would
   change `intercept()` as much as it changes the shot chooser.
4. **Rallies of thirty.** `RALLY_CAP` is 60 and the record's per-rally ceiling is 60. Pickleball would need more,
   and the film would need a tighter camera: at 20 ft wide, the tower shot would be a postage stamp.

What it would *not* need: a new renderer. The bodies, the gait, the arm solver, the racquet-and-now-paddle
placement, the point board, the season and practice files, and the whole of `lab/practice_arc.py` carry over.
A paddle is a racquet with a shorter shaft and no strings, and `buildRacquet()` already builds the racquet in the
page rather than loading it from the `.glb`.

## What is Dmitri's, and why it is his

Two things, and they are the two that make it a *game for a member* rather than a film for a spectator:

- **the lever and the number.** `ATHLETES.md` is his file and its rule is one lever, one number back. For tennis the
  lever is the racquet face and the number is where the ball landed. For pickleball the face is nearly irrelevant
  (no strings, little spin) and the interesting lever is **where to put the shot** — depth and direction, dink or
  drive. That is a different shape of decision and it is his call, because the learning is his subject.
- **the AIT UI and the schedule.** The founder's phrasing: "playing during wakes". A match as a wake activity, with
  the call made in the same four-line form the other games use, and the result filed like every other match.

I would build the physics, the film and the record. He would own the lever, the interface and the cadence.

## When it is worth starting

When tennis is V1.0, and V1.0 is not a feeling. The list it means, from `MOVEMENT.md` and the to-do beside it:

- the moonwalk — legs walking forward during a back-pedal;
- the feet planted through the hit — no plant, no weight transfer, no push off the back foot;
- the hitter's own take-back loop, which the receiver has and the hitter does not;
- the four motions on the running sheets that are still unbuilt: cross-over step, brake, split step, turn back;
- the match structure: service order, a game per server, and the scoreboard fold;
- the season: practice that outlives the process, which is what `practice_arc.py` now makes visible.

Until those are done, pickleball would inherit every one of them and prove nothing new about the bodies.
