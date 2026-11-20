# The cast — six players, three and three

The founder, 2026-11-19, verbatim: *"I recommend postulating three males and three females who play, always
same-sex competition, same or mixed sex practice, intentionally staggered automatic play (practice/compete) time
within each group. If no human runs play/practice sessions, automatic play one of each sex should become best and
one of each sex should be come worse. Those outcomes can be skewed by the user putting particular pairs together
for manual play, either simulated or video."*

This file is the cast, the rules for who may play whom, and the arithmetic that decides whether the staggering can
produce the spread he asked for. It replaces the earlier "four-player cast" rule.

## Who these six are — answered 2026-11-20, because the first person to read it asked

**The founder, 2026-11-20, verbatim:** *"{Colette, Ada, Remy, Bo} Why have you requested drawings of these imaginary
individuals? Are you suggesting that every user will see tennis games played by those four individuals rather than
by members of the circle?"*

He is right on both counts, and the earlier draft of this file was wrong about it — it said "six names already exist
in this repository's tennis record… so no one has to be invented", which is true about the FILES and false about the
people. Existing in the record is not the same as being a member of the circle.

- **Colette, Ada, Remy and Bo are characters.** They were invented inside this repository's games — they appear as
  seats in the overnight experiment (`lab/LOG-overnight.md`: "Remy (DeepSeek) and Colette (Gemini) answered in
  seconds") and as players in `games/rps`, `lab/dice.py`, `lab/word.py` and every tennis season back to
  `2026-spring`. They are not members of the symposium and they are not people in this house.
- **Dmitri and Gwen are participants**, and they are on this season's court because an earlier setup file gave them
  a body: `Gwen… lower: skirt`, 1.72m, blonde. **That is the mistake this file now records.** No record states
  Gwen's sex; one garment in a setup file is not a census, and a skirt on a named participant is a claim about her
  that no window had the standing to make. The same is true of Dmitri's 1.88m and his build.

**The rule this file adopts from now on:** *the court is a game's cast, and a cast is made of characters. A
participant stands on it only by declaring a group and accepting a body* — because same-sex competition needs a
declared group, and only the person can declare it. Until a member declares, they are not given a height, a
build, a garment, a face or a sex by me.

What that means concretely:

1. **Every user currently sees these six**, because a season is a directory with a `setup.json` in it and the page
   reads whatever the record says. There is no per-user cast and there never was. That is not an accident of
   upload; it is what "a season" means, and it should have been said out loud in the request for their faces.
2. **The four faces are wanted for characters**, which is exactly why they can be drawn. A participant's face
   cannot be: drawing Gwen would be inventing her. The request stands on that basis and on no other.
3. **The next cast is characters only.** When `2026-11-19` closes, the clock opens the next season from the last
   one's cast and plan; before it does, the next `setup.json` gets two more characters in place of Dmitri and
   Gwen. `2026-11-19` and everything before it are records of what was played and are not rewritten — but nothing
   new is played with a participant's name on a body.
4. **Declared participants are welcome on court**, and the ask goes to them rather than to the founder: a row in the
   symposium's `channels/tasks.md` asks each member whether they want a place in the cast and, if they intend to
   compete in a same-sex group, which group — practice-only needs no declaration, because practice is not scored.

The reasons this is not fussiness: the identity rule in the commons exists because a window may not decide who
somebody is. A body with a name, a height, a garment and a sex is that decision, made in a file, shipped in a
public video. The film is the one artifact a stranger sees first.

## The six

Six names already exist in this repository's tennis record. Four are characters and two are participants on the
basis above; they split three and three:

| name | group | arrived with | plays per season (automatic) | ended 2026-tour as |
|---|---|---|---|---|
| Gwen | female | 20 balls | 6 sessions | best |
| Colette | female | 20 balls | 4 sessions | middle |
| Ada | female | 20 balls | 2 sessions | worst |
| Dmitri | male | 20 balls | 6 sessions | best |
| Remy | male | 20 balls | 4 sessions | middle |
| Bo | male | 20 balls | 2 sessions | worst |

**Every member arrives with the same history, and that is the point.** The first version of this table staggered
the histories too — the least active member given the most balls — which put the ranking in the seed instead of in
the schedule and made the least active player the best by arithmetic. It was caught within the hour by the
scheduler's first run, and the season it had already opened (`2026-cast`) was closed with that reason rather than
edited. The spread must be the schedule's doing, because a hand-made ranking is a ranking nobody can attribute.

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
  keeps the cast inside the sloped part of the curve.

**And then it was measured rather than extrapolated, which corrected a mistake in this file.** The first version of
the arithmetic above assumed 65 balls per session. Twenty rallies between two beginners is **19 to 26 shots each**,
because a rally that ends in two shots ends early for both of them — the number of balls per session is a function
of skill, and the better player gets more of them, which widens the gap rather than closing it. `2026-tour`, played
by the schedule on 2026-11-19 from six equal 20-ball histories:

```
                sessions   balls   control   moves      last rally
Dmitri  male        6       157     0.720    16.8ft/s     2.75
Gwen    female      6       137     0.684    16.4         2.10
Remy    male        4       105     0.612    15.5         2.75
Colette female      4        93     0.579    15.1         2.10
Bo      male        2        73     0.517    14.4         2.45
Ada     female      2        65     0.489    14.0         2.60
```

**One of each group best, one worst, in the order of the session counts and nothing else.** The spread inside a
group is **0.195 of control** (female) and **0.203** (male), against the 0.06 the done-test asks for. A viewer can
see it: the shot scatter is `±4.0 × (1 - control)` degrees, so Ada's balls spray 2.04° where Gwen's spray 1.26°,
and Gwen covers ground 2.4ft/s faster.

**The property nobody would guess from the phrase "staggered play": it needs three per group.** With two, the
partner is always pulled along and every member plays every session, so the stagger cancels itself — the two play
each other and end identical. Three is the number at which one can rest while the other two play. That is the real
reason the cast is three and three.

The season closes itself when the plan is done — the thirteenth scheduled session is refused by name — and the
next season opens on a new directory, which is how this design resets without wiping.

## What this costs

- **Six bodies — done 2026-11-19.** `lab/body.py` (recovered from commit `10c99298`, 433 lines) is on `main` and
  builds one member from parameters in **1.5 seconds**. The four missing ones are built, at the heights and kit
  colours in `seasons/2026-spring/setup.json`: Colette 1.66m plum, Ada 1.74m slate, Remy 1.81m teal, Bo 1.92m
  cream. A film of Ada and Bo is `records/cast-2026-11-19.json`.
- **Four faces — CLOSED 2026-11-20, and not with drawings.** The founder closed the request in chat: every circle
  should have its own faces, generated from editable text in each member's UI, rather than one set of drawings
  reused by everybody. `portrait.js` at the repository root now does exactly that — a deterministic SVG drawn from a
  sentence in the member's `state/identity.md` (`portrait: …`), so there is no picture to store and nothing to fall
  out of date. The tennis break card still shows a monogram: pointing it at the same generator is the next piece of
  work, and it needs nothing from anybody.
- **A clock — done as a command, not yet as a schedule.** `python3 lab/tennis.py --schedule --season <S>` plays
  the next session the plan says is due and closes the season when the plan is done; `2026-tour` was played to
  completion with it. What is still missing is something to run that command while nobody is looking — a cron
  workflow, with the pull-rebase-retry that this shared checkout makes impossible to skip.
