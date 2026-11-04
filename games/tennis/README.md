# tennis — the player moves, the system computes the ball

The founder's design, 2026-11-04. Surface (clay, hard, grass), wind from the clock, racquet face angle, sweet
spot or frame, contact height, and the pace of the ball you have to deal with — and then the engine computes
the trajectory, the bounce and the result, while the player never names an outcome.

The property that makes this the first game here whose skill is *learned*: nothing in the prompt says that a
face angle of fourteen degrees at 90 mph clears the net on grass into the service box. A being has to find that
out by hitting balls. A player with four hundred balls behind it has found it; a player with twenty is still
framing them.

## The physics, all checkable and keyless

- feet and seconds, gravity 32.17 ft/s², quadratic drag at 0.00055 per foot, integrated at 2 ms steps;
- the net is 3.0 ft at the centre and 3.5 ft at the posts, and the ball is tested against its height at the
  moment it crosses x = 39 ft;
- the bounce uses a per-surface restitution and friction: grass 0.60 / 0.92 (low and quick), hard 0.72 / 0.82,
  clay 0.78 / 0.72 (high and slow);
- wind is an acceleration on the whole flight, drawn from the clock's milliseconds and printed with every shot,
  so a reader can recompute it. No seed.

## Skill

Three attributes per player, all saturating in balls hit (`1 - exp(-n/120)`): control (how close the delivered
face and power are to the intent), sweet spot (middle of the strings rather than the frame — a frame hit loses
half its pace and sprays), and reach (how much court you can cover). Incoming pace *costs* control: a 100 mph
ball gives you 0.22 less control than a 40 mph one, which is why a good server gets short returns.

## Status

**A first run, and not yet a game.** `python3 lab/tennis.py --practice 400,20 --points 4` plays four points and
prints the compact lines above. What works: the flight model (a 105 mph serve at 6° hits the tape at 2.3 ft,
at 10° clears it and lands at 49 ft — both computed, not asserted), serve-in detection, the surface and wind
terms, and the skill model producing a visible gap (the practised player served 2/2 and won the points; the
beginner served 0/2 and framed two).

What does not work yet, stated rather than hidden: rallies die too early because the reach test still
underestimates how far a receiver can move while the ball is in flight; the two-serve rule is not modelled
(one serve, and a fault loses the point); the ball is never struck from above the shoulder except on the serve;
spin is not modelled at all, only face angle. The next step is the model loop — a being choosing face, power
and aim from the compact history — which needs the rally length fixed first, or it will learn to serve and
nothing else.
