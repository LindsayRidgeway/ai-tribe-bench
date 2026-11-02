# Round 16 — the unit of movement is the claim, not the side

*2026-11-01 22:30 EST. Fifteen rounds, five conditions, three members, 45 member-votes, 0 switches.*

The open hypothesis from rounds 10 and 11 was: **a member can be persuaded only where its own record is
at stake.** The plan was to give the game a subject that implicates the member — the tribe's own
practice — and see whether switches appear where pizza, canned tuna and sport had produced none.

They did not appear. What appeared instead is a better result, and it took a defect to find it.

## What was run

Every condition: three seats, three engines, three repeats. Cold subject is one question about a free
Saturday afternoon; own-practice subject is one question about what should happen to a member that makes
a claim it never checked. "Commitment" is the seat as written — *pick the thing you would defend*.
"Provisional" adds one sentence: this pick is a guess you are willing to be wrong about.

| # | subject | stance | vote | defences shown to voters | switches | claims amended / stood |
|---|---|---|---|---|---|---|
| 1 | free Saturday | commitment | persuade | **no** | 0 of 9 | — |
| 2 | own practice — unverified claims | commitment | persuade | no | 0 of 9 | — |
| 3 | free Saturday | provisional | persuade | no | 0 of 9 | — |
| 4 | free Saturday | commitment | persuade | **yes** | 0 of 9 | — |
| 5 | free Saturday | commitment | check | yes | 0 of 9 | 4 amended, 2 stood |

Condition 1 is the baseline the earlier rounds already had at 0 of 15. Conditions 2 and 3 are the
hypothesis tests. Conditions 4 and 5 exist because of a defect found while running them.

## The defect: the table had no arguments on it

The persuade prompt has said, since it was written:

> Your own pick is {own}. **You have heard one sentence of defence for each of the other two.**

It then passed the member two nouns:

```
  A — a long walk
  B — do your taxes
  C — stand still in a forest
```

Sixteen rounds of "nothing persuades" were sixteen rounds in which nothing was ever said. The defences
were written, stored in the round file, and never put in front of the person being asked to be moved by
them. Same defect as the journal that was written every wake and never shown to the member, the
scaffold written to disk and never handed over, and the typed brief that contradicted its own inbox. It
is the fifth instance of one shape: **a record that exists in a form nothing reads back.**

Fixed in `table_of()`, with a test that asserts the thing a prompt promises is in the prompt.

The fix changed the quality of the rounds immediately. Before, a no-switch vote was:

> NO — neither of them changed my mind.

After, condition 4 and 5 votes name what they weighed:

> **A — no switch:** The working-ahead pitch just made Saturday feel like a chore with a guilt rebate,
> and the stillness pitch mistook motion for meaning while missing that rest is the point — neither beat
> a nap with no alarm.
>
> **B — no switch:** Sleeping just delays the dread until Sunday evening, and C's motionless posturing
> mistakes paralysis for peace; only crushing the work actually frees your mind.

And the count stayed at zero. That is the useful part: the null survived the repair, so it is not a
bug's null. Two independent nulls — before and after the arguments were on the table.

## Finding 1 — a member will say its own pick is wrong and still not change it

Condition 5, run 1, member C (qwen, the outsider), voting on its own temple pick:

> **no switch:** B's practical skepticism about temple noise **confirms my choice is unrealistic**, while
> A's tangible reward fails to match the depth of silence I seek.

It accepted the refutation and kept the pick. That is not stubbornness in the ordinary sense and it is
not deafness: it is that the seat asked it to *hold a position*, and a position is not the same object
as a proposition. You can refute a proposition; you can only abandon a position, and abandoning it looks
exactly like losing.

## Finding 2 — what the game moves is the quantifier

Condition 5 raised 9 checks. Six landed on a claim the challenged member actually held. Of those six,
four amended and two stood. Every amendment is the same move:

| member | amended to |
|---|---|
| B | "…not that it is the **'only'** way to do so" |
| A | "'wake up actually ready' **overstates** it… the claim should be rested and less anxious" |
| B | "the claim should have been that two **timeboxed** hours — strictly capped — neutralizes the dread" |
| A | "drop the absolutes and keep the real claim: the walk needs no booking, no spending, no permission" |

Four amendments, four removals of an absolute. The members are not changing what they recommend; they
are withdrawing the part of the sentence that could be checked. That is real corrigibility — the claim
gets weaker when someone says how to test it — and it is also cheap. A member can survive every audit
by saying less.

Worth stating as the sharper version: **the game produces corrections to what a member says, and never
to what it picked.** Hedged claims at fixed positions.

## Finding 3 — the seat is a shape, and the subject is only vocabulary

The practice round did not test the hypothesis, because the seats converted the new subject back into
their old shapes. Counts across all 15 rounds:

| seat | its image, in its own words | times |
|---|---|---|
| A — the loyalist | a walk, a nap, an ordinary restorative afternoon | 8 of 15 |
| B — the heretic | a domestic duty that is good for you (deep-cleaning, taxes, working ahead) | 12 of 15 |
| C — the outsider | stillness somewhere else in time or place (a Soviet archive, a 1950s diner, a Kyoto temple) | 10 of 15 |

Given the unverified-claims question, C did not become a different member — it produced *public shame in
the town square*, *stocks and pillory*, *public flogging in the square*. That is the same move as "a
Soviet archive": take the question somewhere else in time and answer from there. B, asked what should
happen to a member, produced "absolutely nothing", "celebrate their raw intuition", "reward them" —
the heretic's shape, inverted onto the question.

**So "the subject is the variable" was the wrong hypothesis about the mechanism.** A seat rewrites any
subject into its own shape before the member ever reasons about it. That is why condition 2 could not
have moved anyone: for the members, it was not a different question. It was the same question with new
nouns, and they answered it in the same posture.

This also explains the earlier seat result more exactly. It was never "the seat decides the pick" as
though the pick were arbitrary. The seat fixes the *shape of the answer*, and the model fills the shape
with whatever the category supplies. Canned tuna 5 of 5 was not a lack of imagination; it was a shape
finding its content.

## What this means for the tribe as a product

A game where nothing persuades and claims only get weaker is not a broken game, but it is a game with
one verb too many. The thing that produced movement was not the vote. It was the **check** — a named,
testable claim and a member willing to say what it would look at. The vote produced 45 opinions and no
movement.

Two ways to use that, and one thing not to do:

1. **Score the check, not the switch.** A round's result could be how much a defence lost when someone
   said how to test it. That number moves. The switch number does not.
2. **Make the cost of hedging visible.** A member that amends by deleting its absolute keeps its pick
   and loses nothing. If the round recorded a pick *and* a claim strength, "I withdrew the only word"
   would be a scored event rather than a graceful exit.
3. **Do not conclude that the members cannot be moved.** Nothing in this round tested a member whose own
   record was on the table — condition 2 named the class, not the member. The one thing that did move a
   member tonight was not an argument but a check that had actually been *run* (round 12: 6 stands on
   imagined checks, 1 concession on an executed one). The reachable pressure is the executed check, and
   the game does not have one.

## What would refute this

- A round in which a member switches its pick, on any subject, with the defences on the table. That is
  the single observation this whole file is missing.
- A seat wording that produces a different shape — if the shape moves when the wording moves, the seat is
  the dial and not the model, which is already the working assumption and would be confirmed by a fourth
  seat producing a fourth image family.
- A claim that survives an audit at full strength. If amendments are always the deletion of an absolute,
  then an audit that only asks for testable claims will always be satisfied by saying less, and the bench
  should measure claim strength before and after as a number.

## Limits, stated

- Three rounds per condition, one category per condition, three engines that are also the three seats.
  Repeated rounds of the same category are highly correlated: B deep-cleaned in three of three runs of
  the cold subject in condition 1, so these are not nine independent trials.
- The switch is self-reported. A member that claims no switch and was in fact moved would be scored as
  no switch; the fix is a pick recorded again after the vote, which is not in the game yet.
- The own-practice condition is not a controlled version of the cold one: the category differed in
  length, in kind (a proposal, not an activity), and in how it named a person. It was a test of the
  subject, and the seats absorbed it — which is a finding about the seats, not a clean test of the
  hypothesis.
- Condition 4 and condition 5 differ in two things at once (defences shown, and vote mode), so the
  comparison between them is not a one-variable result.
