# The cast — six players, three and three

The founder, 2026-11-19, verbatim: *"I recommend postulating three males and three females who play, always
same-sex competition, same or mixed sex practice, intentionally staggered automatic play (practice/compete) time
within each group. If no human runs play/practice sessions, automatic play one of each sex should become best and
one of each sex should be come worse. Those outcomes can be skewed by the user putting particular pairs together
for manual play, either simulated or video."*

This file is the cast, the rules for who may play whom, and the arithmetic that decides whether the staggering can
produce the spread he asked for. It replaces the earlier "four-player cast" rule.

## The six

Six names already exist in this repository's tennis record. They split three and three, so no one has to be
invented:

| name | group | arrived with | plays per season (automatic) | ends the season as |
|---|---|---|---|---|
| Gwen | female | 30 balls | 6 sessions | best |
| Colette | female | 70 balls | 4 sessions | middle |
| Ada | female | 140 balls | 2 sessions | worst |
| Dmitri | male | 30 balls | 6 sessions | best |
| Remy | male | 70 balls | 4 sessions | middle |
| Bo | male | 140 balls | 2 sessions | worst |

**The `group` column is my reading of the names and nothing more.** No record in this repository states anyone's
sex. The field exists so that a person can change it in one place instead of arguing with a rule, and so that
`same-sex competition` is enforced by data rather than by a default. Gwen's `lower: skirt` in
`seasons/2026-spring/setup.json` is the only sex-adjacent fact in the files, and one garment is not a census.

**`plays per season` is what "intentionally staggered" means mechanically**: not a different amount of play per
session, but a different NUMBER of sessions. Ada and Bo are on court a third as often as Gwen and Dmitri. That is
the whole mechanism, and it is why the spread below is measurable instead of wished for.

## The rules

1. **Competition is same-sex.** A session that competes across the two groups is refused by name, not silently
   re-paired. `--watch` and `--rally` both refuse it, because a rule enforced in one producer is a rule the other
   producer breaks.
2. **Practice may be any pairing**, including mixed. Practice is not scored, so there is nothing for a mixed pair
   to be unfair at. The record already distinguishes them: `mode` is `practice` or `compete`, and a session
   carries `with: [...]` either way.
3. **A manual pairing is recorded and is not automatic.** The founder's last sentence — "those outcomes can be
   skewed by the user putting particular pairs together for manual play" — is a fact about the record, not a
   feature to add later: a session a person started carries `by: "a person"`, an automatic one carries
   `by: "the schedule"`. The season report prints the two totals separately, so nobody can mistake a season a
   human hand-shaped for a season that played itself.
4. **A season is short and then it ends.** A season is about six automatic sessions, after which the record is
   closed and the next season opens with beginners. This is not a preference; see the arithmetic below.

## The arithmetic — why the season must be short, and why "worse" cannot mean "declines"

`Player.skill()` is *strictly increasing* in `practice + shots` and asymptotic:

```
balls    0     10     50    100    200    400    800    1600
control  0.180 0.239  0.432 0.598  0.780  0.894  0.919  0.920
reach    0.350 0.398  0.555 0.689  0.837  0.929  0.949  0.950
ft/s     10.2  11.0   13.3  15.3   17.6   18.9   19.2   19.3
```

Two consequences, both measured rather than assumed:

- **Nobody can get worse.** There is no term in the formula that can fall. So "one of each sex should become
  worse" cannot mean a player whose skill declines; it is read here as a player who ends the season *last*. If a
  literal decline is wanted, it needs a new term in the skill law — recent form, or a memory that fades — and that
  changes every ball in every film and every number in every test. It is not in this cast, and it is named in
  `BACKLOG.md` as the alternative reading so it cannot be lost.
- **Everybody converges.** 800 balls and 1600 balls are 0.001 of control and 0.01ft/s apart. So a season long
  enough for a hundred sessions produces six players who cannot be told apart on the court, and the ranking he
  asked for dissolves at exactly the point the season gets interesting. Six automatic sessions at a 3x/2x/1x rate
  keeps the cast inside the sloped part of the curve:

```
        opened    after 6 sessions    control
Gwen     30         30 + 6x65 = 420    0.894
Colette  70         70 + 4x65 = 330    0.855
Ada     140        140 + 2x65 = 270    0.801
```

A spread of **0.09 of control** inside one group is a difference a viewer can see: the shot scatter is
`±4.0 × (1 - control)` degrees, so Ada's balls spray 0.80° where Gwen's spray 0.42°, and Gwen covers ground at
18.9ft/s against Ada's 16.9. The season ends while that is still true, and the next season opens on a new
directory with everybody at zero — which is how the existing design already resets without wiping.

## What this costs

- **Six bodies.** `lab/body.py` (recoverable from commit `10c99298`, 433 lines, Blender 5.3.0 installed here)
  builds one member from parameters. Four of these six have no `.glb` today, so four builds.
- **Four faces.** `bodies/faces/` holds `dmitri.jpg` and `gwen.jpg`, both drawn by the founder. The other four
  cannot be generated here; until they exist the break card must draw a named placeholder rather than a
  broken-image glyph.
- **A clock.** Something has to start a session on the staggering above without a person, and it has to be a
  workflow rather than a habit.
