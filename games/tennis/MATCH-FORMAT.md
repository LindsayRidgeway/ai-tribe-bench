# The match: format, score, and what is not built yet

Recorded 2026-11-11 from the founder's instruction. Nothing here is implemented; this is the specification the
competition layer will be built against, kept in the repository so it is not remembered in a chat.

## The scoreboard, in his words

> Show the match score in a two-row table. The three columns represent Sets, Games, and Points, read from left to
> right. Sets (Left Column): This shows how many full sets each player or team has won. Most matches are played as
> the best of three sets, meaning the first player to win two sets wins the match. Games (Middle Column): This
> displays the number of games won in the current set. A player generally needs to win six games by a margin of
> at least two to win the set. Points (Right Column): This tracks the live score of the game currently being
> played. It progresses as 0 (Love), 15, 30, 40, and Game (with "AD" appearing if a player holds the advantage
> after a 40–40 deuce).

So the table is two rows — one per player — and three columns:

    player      Sets   Games   Points
    Dmitri        1       4        30
    Gwen          0       3        AD

## What that fixes

- Two rows, always both players, no score for a third party.
- Sets: count of completed sets. Best of three; first to two wins the match.
- Games: games won in the current set. Six games with a two-game margin wins the set.
- Points: 0 / 15 / 30 / 40 / AD, with "Game" as the terminal value for the row that takes it.

## What it leaves open, and what I will do

These are my decisions unless he overrules them, because he does not direct the commons and a match has to have
an answer before it can be played.

1. **6–6.** He says six games by two. A set that reaches 6–6 needs an ending: a tiebreak to seven, or two clear
   games. I will use a tiebreak to seven points, two clear, because that is what "best of three sets" implies in
   every club and professional format, and without it a set can run forever.
2. **Deuce.** 40–40 is deuce; the next point gives AD to that player; if the other player wins the next point it
   returns to deuce. No "golden point" — his wording assumes advantage scoring.
3. **Serving, and where it goes.** A first serve is aimed at one of the two far corners of the service box,
   chosen at random for now (his instruction, 2026-11-11) — random because nothing yet knows which side a player
   returns badly from, and a corner is a corner. Once returns are recorded by side the same history the rally
   placement uses will choose between the two. Second serves will go to the same target with the pace off and the
   height on, which is what a second serve is.
   **Built 2026-11-11** (below, "The serve"). A match still needs an order: one player serves a whole game,
   service alternates each game, and within a game the server alternates ends each point. That is a change to
   `lab/tennis_script.py`, not to the renderer.
4. **Ends.** Players change ends at the end of the first game of each set and at the end of every set (odd games).
   Both players' `north` flips; the fixed broadcast camera does not move, which is the point of a fixed camera.
5. **Who serves first.** The lower rating serves first — a small handicap rather than a coin toss, and it keeps
   the record reproducible.
6. **A match is one file.** The record already carries a point verdict per rally. A match is that list plus the
   score folded over it; the scoreboard is displayed, not decided, and `Show me game 14 again` replays the same
   numbers because nothing is random that was not seeded.

## Where the score will be displayed

Top-right, above or beside the player list, always visible during a match — his two-row table, monospaced so the
columns do not shift as the numbers change. During practice rallies (which is all that exists today) the table is
absent rather than zeroed: there is no match to score.

## Not built yet, in order

1. Serving and a service order in the engine's play script.
2. The point list → (sets, games, points) fold, with tests, including deuce and a tiebreak.
3. The two-row table in `replay3d.html`, driven by that fold.
4. Ends changing; the camera staying where it is.
5. Then: a club, fixtures, a season — where a rating moves.

## The serve — built 2026-11-11

His instruction turned into code, and the first ball of every point is now a serve.

- `T.serve_corners(north, control)` returns the two deep corners of the service box, three feet inside the line
  for reliable hands and up to eight for a beginner — the same control-scaled margin as the groundstroke corners,
  for the same reason.
- The corner is chosen once per point with the run's seeded RNG, and both serves go to it: a second serve is the
  same intention with less pace, not a change of plan. Pace is 66-84% on the first ball, 85% of that on the
  second, and the second ball is aimed four feet shorter so it crosses the tape higher.
- A serve is judged by `T.serve_verdict`, not by `T.verdict`. To `verdict` a ball ten feet past the service line
  is inside the court and therefore good — true of every other shot, false of this one.
- A fault is not a lost point: the record keeps the faulted ball, the server keeps the ball, and a second fault
  is a double fault with the point to the receiver. The reason string says which.

Checked before it was believed: with a clean swing, 12 of 12 serves from both ends at 0, 200 and 400 balls landed
in the box, within 0.4ft of the corner aimed at, and the margin inside the service line closed from 7.8ft at 0
balls to 3.3ft at 400 — practice walking the target out to the line, now true of serving as well as of rallies.

Not built, and it matters: the **diagonal rule**. A real serve must cross to the opposite box (deuce court to
deuce court). Nothing here enforces it, because the service position is the middle of the baseline and both boxes
are equally diagonal from it. It belongs with the scoreboard, where a player stands on the correct half.

## A point that ends on the tape — built 2026-11-11

> When the ball hits the net, show it bouncing off and onto the court for a bounce or two before ending the point.

A point that ends in the net used to end when the ball reached the net: it stopped, and the point board came up
over a ball frozen in mid-air. That is not what a net cord is. In tennis the ball hits the tape, most of its speed
is eaten, and it drops at the foot of the net on the hitter's own side and bounces — a second and a half of ball
still to watch, and the reason the umpire waits before calling.

- `flight()` now takes a bounce count, `bounces=1`, and keeps integrating after the first bounce until it has
  that many. Every existing caller still asks for one bounce and gets exactly what it got before.
- A net cord recurses instead of stopping. `NET_ABSORBS = 0.08` of the speed survives, `NET_DROP = 0.25` of the
  vertical speed, and the horizontal velocity is **negated** — the ball comes back towards the hitter, not
  through the net. `land` stays `None`, so every caller that reads "did not reach the court" for the verdict is
  unchanged, and the point is still lost; the ball merely keeps existing for another half-second.
- The dribble is returned under `after_net` (`bounces`, `time`) and appended to the traced `path`, so the
  renderer draws it from the same integration that judged the shot. Nothing in the page needed changing: the
  shot is longer, so the film is longer.

Measured on the current demo (59 shots, 6 of them into the tape):

| shot | player | bounce 1 | bounce 2 | between | ball after the tape |
|---|---|---|---|---|---|
| 15 | Dmitri | 2.3 ft | 5.3 ft | 0.64 s | 0.66 s |
| 20 | Gwen | 1.0 ft | 2.1 ft | 0.64 s | 0.66 s |
| 23 | Dmitri | 0.6 ft | 1.6 ft | 0.42 s | 0.44 s |
| 25 | Dmitri | 3.6 ft | 7.5 ft | 0.66 s | 0.68 s |
| 54 | Gwen | 2.7 ft | 5.3 ft | 0.66 s | 0.68 s |
| 58 | Dmitri | 2.8 ft | 5.9 ft | 0.70 s | 0.72 s |

Distance is measured from the tape towards the hitter, and the direction is checked, not assumed: every one of
the six is on the side of the net the shot was struck from. Two bounces, between 0.6 and 7.5 ft in front of the
net, 0.4 to 0.7 seconds apart. The still is `stills/net-dribble.png` — rally 4, shot 5, "into the net at 2.5ft,
0.8ft under the tape", ball on the clay at the foot of the net with its trail leading back to the striker.

The first version of this kept the forward velocity: at `NET_ABSORBS = 0.20` the ball sailed six feet past the
net and at `0.06` it landed at x=40.6, still the wrong side. The bug was not the size of the damping, it was the
sign — and it looked perfectly plausible on a still until the landing points were printed.

Not built, and it is fine: nothing rolls along the tape. A ball that clips the cord and climbs over is still a
ball that clears the net here, with no loss of speed, because the contact is a plane and not a rope. It matters
for a lucky let; it does not matter for a point that ends.

## A point that ends out of court — built 2026-11-11

> When the ball is out, I suggest you show it bouncing (if it's in view) a couple of bounces, similar to netting a
> shot (which looks great).

The same fault as the net cord, one bounce further out: a ball that missed was integrated up to its landing point
and stopped. On screen the ball fell to the line and **froze there** — the one thing a ball never does — and the
point board came up over it. The verdict was right and the picture was a lie.

- `flight()` takes `out_bounces` (default **0**, so nothing that judges a shot pays for it), a `legal` test that
  decides what "out" means, and a `t_max` for how long the picture may watch. The ball that lands out recurses
  from its bounce with the post-bounce velocity — the same integration, not a second copy of the physics — and
  `land` is still the **first** bounce, so no caller can mistake a ball that bounced twice for one that was in.
- `OUT_BOUNCES = 2`, `OUT_SECONDS = 1.5`, `VISIBLE_PAD = 22`. The pad is the point: a ball leaving the lines is
  still travelling at 30-40 ft/s, so its second bounce is twenty to fifty feet outside the court, off the edge of
  any fixed camera. The film follows the ball while it is over the drawn court plane (the court is drawn 22 ft
  larger than itself on every side) and then stops, rather than walking it into the dark and stretching the shot.
- What "out" means is per stroke, because it is not one question: a serve is out against the **service court**
  (`in_serve_court`), a groundstroke against the lines on the **far side of the net** (`in_far_court`). The first
  version tested the court rectangle only, which froze a ball dumped three feet short of the net at its bounce —
  the one ball in the film that most obviously bounced on, since it stays in the middle of the picture.

Measured on the shipped film, 80 shots, 22 of them lost:

| | shots | duration |
|---|---|---|
| in, and net balls | 58 | 0.50 - 1.40 s |
| out, ball bounces on and leaves frame | 14 | 0.90 - 2.38 s |
| out, and slow enough to bounce twice or three times in frame | 8 | 1.18 - 1.98 s |

`stills/out-bounce.png` is shot 53, "short of the net by 3ft": at 0.26 of the shot the ball is 0.4 ft off the clay
with its trail leading back over the net, which is the ball doing the thing the founder asked for. The ball rises
0.02 -> 0.37 -> 0.72 ft in the three samples after every out bounce, so it is a bounce and not a teleport.

## The frame, and the ground behind the near baseline — built 2026-11-11

> I hope it won't distort your layout, but you need to show a couple of yards of court behind the closer court so
> that long balls, or missed shots to the closest player, have a place to bounce.

It does not distort anything, because the clay was already there — the court plane is drawn 22ft larger than the
court on every side — and only the camera was cropping it. `tower()` put the near baseline on the bottom edge of
the picture, so a ball that landed behind it bounced out of frame: six of the twenty-two lost balls in the film,
including every ball the far player hit long past the near player.

The camera is now solved rather than guessed, because it is fixed for the whole match and its frame is a decision
made once. Measured from the eye at (-56ft, 29ft) in the plane the court's length lies in:

- the **bottom edge** passes through a point 8ft behind the near baseline at ground level;
- the **top edge** passes through the far baseline at 6ft — a tall player's head, and where a ball long over the
  far baseline comes down;
- the lens is whatever spans those two, plus 10 per cent.

`aNear = 31.1°`, `aFar = 9.7°` below the horizontal, so **fov 23.5°** about an axis 20.4° down, where the old
camera used 26° about an axis 14.7° down. The court is a little smaller in the frame and a little lower, the near
player stands rather than sits on the bottom edge, and the strip behind the near baseline is about a sixth of the
frame height — which is what television shows, because it is where the ball goes.

The ball is followed to 22ft past every line (`in_view` in the engine, the same 22ft the court is drawn by), so the
bounce behind the near baseline is drawn, and so is the second one if it is slow enough to be in frame. Still:
`stills/out-behind-baseline.png` — rally 1 shot 3, "long by 8ft", the ball's trail coming down past the near
player and landing on the clay two and a half yards behind him, inside the picture.

## Ends, and which player is in the foreground — built 2026-11-11

> even for rallies, it would be more interesting if half the time the male was in the foreground, and half the
> time the female was... You don't want them changing after every point, but maybe after ten points.

The camera is nailed to one end — that is the whole point of it — so whoever stands at that end is a quarter of
the frame tall and whoever stands at the other end is a smudge. Until now that was always the same person, for
the whole film. In a match the ends change on their own schedule (the end of every odd game); practice rallies
have no games, so the count here is points, and the default is ten.

- `lab/tennis_script.py --swap-every N` (default **5** since 2026-11-11 — "every 5 rallies rather than every 10";
  `0` never flips). One line of engine: at the boundary,
  `pl.north = not pl.north` for both players. Nothing else needed changing, because every rule downstream already
  asks the player which end they are on rather than assuming: the serve corner, which side of the body is the
  forehand, the recovery spot behind *their* baseline, and which corner is "far" all read `pl.north`.
- The record now carries `ends` per rally and `changed_ends`, so the page can see the change instead of
  inferring it.
- The page had one real piece of work: `pl.north` meant the end a player *started* at, and it was read in nine
  places for posture — the body's facing, which way the legs go, the ready pose, the racquet face. Those now read
  `northIn(seg, name)`, which takes the end off the record: the striker's `sh.north`, the runner's
  `sh.run.north`, and otherwise the opposite, because within a rally the two players are always at opposite ends.
- Nobody walks seventy-eight feet during a break. The change is a cut: each player appears at the other end at
  the instant the next rally begins, under the point board, and the body's yaw is set rather than turned so
  there is no pirouette at the start of the next point.

Verified in the film as it now stands (20 points, `demo3d.html`): Dmitri is the near player in points 1-10 and
Gwen in 11-20, and 95 of the 116 shots were good balls landing inside the court — **every one of them on the
opponent's side of the net**. The two that landed on the hitter's own side are `in: false`, short of the net,
which is what they are.

For the record on the other question: the male figure is no less finished than the female one. Both are built by
the same script into the same eighteen-bone rig (`?debug` prints the same bone list for both), the same two-bone
solver poses both, and `?debug` reports 0.00ft of error against the prepared hand position for each. The gait is
a rule scaled by the figure's own measured height — 6.16ft for Dmitri, 5.64ft for Gwen, so his stride cycle is
5.17ft against her 4.74 — and movement speed comes from skill alone, so the two differ only in proportion. The
one number that is not proportional is the preparation offset, which is absolute feet from the chest: about 9%
smaller, in proportion, on the taller body. Nothing in the renderer names a player.

## How a point ends — 2026-11-11

Every point now ends on one of four things, and the fourth one only became possible tonight: netted, long or wide
(the hitter's error), or **out of reach** (a ball the receiver could not get to). Before this, only the first three
existed: `intercept()` answered yes to every ball in fifty points, so the record never once said a player had been
beaten to one. The rule, the four numbers that decide it and the measurements behind them are in `MOVEMENT.md`
("Nobody was ever beaten to a ball").

In the 20-point film as it now stands: 70 shots, rallies `[3,4,9,3,6,2,2,1,4,2,2,4,2,2,6,2,1,3,7,5]`, four points
end on a ball out of reach, six on a mishit, four on an aim that came off the side of the court, and six in the net. A beaten player runs as far as the clock allowed and stops short — nobody is teleported onto a contact — and
the record carries `need`, `have`, `short` and `legs` for the run, so a season report can say how many feet short
the losing player was, in which direction, and how tired they were when it happened.
