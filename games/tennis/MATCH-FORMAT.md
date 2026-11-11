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
