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
   Rallies are currently played with no serve at all; the engine's serve exists (`shot="serve"`,
   contact at 8.8ft) but the script plays `shot="rally"`. A match needs an order: one player serves a whole game,
   service alternates each game, and within a game the server alternates ends of the court each point. This is a
   change to `lab/tennis_script.py`, not to the renderer.
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
