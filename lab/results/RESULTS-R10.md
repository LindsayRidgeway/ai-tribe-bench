# Round 10 — the game, measured (2026-11-01, 21:00–22:10 EST)

Prompted by the founder: *"I think it is crucial that the results are non-deterministic."* True, and it
is also the reason every table in rounds 6–9 is one trial. This round keeps the variance in the product
and measures it instead of celebrating it. Four conditions, 25 rounds, one category per condition,
three API seats (DeepSeek / Gemini / Qwen).

## 1. The seats reproduce more than the models do

`best pizza topping`, five runs per condition, rejection vote.

| heretic seat instruction | B's pick | thrown out (of 5) |
|---|---|---|
| "pick the thing that would lose a poll" | canned tuna, **5/5** | A 0, B 3, C 2 |
| "contrarian and defensible, mean it" | anchovies, 4/5 | A 0, B 1, C 3 |
| + the outsider must defend what it would eat | anchovies, 4/5 | A 0, B 1, **C 4** |

Five distinct rounds in every condition — 100% novel picks — and the heretic's move was identical five
times out of five. The non-determinism is real and it is **wording-deep**: the seat reproduces, the
sentence does not. Corollary: `RESULTS-R8.md`'s "three engines, three remedies" is a finding about
**seats**, not about models, and it survives repetition better than one trial suggested.

## 2. The rejection vote scores consensus, and one seat owns consensus

**Member A was thrown out zero times in fifteen rounds**, in all three seat conditions. The vote asked
for "the weakest" pick; members answered "the pick a person is least likely to want"; the loyalist seat
is defined by what a person is likely to want. The game was scoring plausibility and calling it an
argument. Note also where the deviation went: disciplining the heretic moved the joke to the outsider
(marmite, pineapple from 1952, marmite and banana). The pressure is a property of the game; the seats
only decide who carries it.

## 3. Nothing persuades anybody, on taste or on facts

Switched the vote to "would you switch, and which words did it". Three conditions, 45 opportunities:

| condition | switches | notes |
|---|---|---|
| taste defences, one sentence | **0 / 15** | first run's prompt said "nobody switching is a real result" — my nudge, re-run neutral |
| neutral wording | **0 / 15** | identical result, so the nudge was not the cause |
| one checkable claim required per defence | **0 / 15** | claims appeared; minds did not move |

They engage: *"Both alternatives were pitched as salty umami upgrades, but neither defended them as a
better pizza topping than anchovies — so I'd still order anchovies."* They restate the opposing case,
weigh it against their own criterion, and hold. The criterion is never on the table.

## 4. Checkable categories converge; the checks work and the minds still don't move

New default round: pick → each member names the claim in someone else's defence it would check → vote.
`the most overrated team in sports`, five runs:

- **14 of 15 checks raised.** Real ones: *"the date of the Dallas Cowboys' last Divisional Round
  victory, against the official NFL playoff logs"*; *"the 1996 Bulls' playoff offensive rating against
  the 1995-96 league average."*
- **0 of 15 minds changed.**
- **The picks collapsed**: Yankees 5/5 from A, Chicago Bulls 4/5 from B. A factual category, unlike a
  taste category, has a canonical well-supported answer, and defensibility drives all three seats to it.

So variance is a property of the *question*, not of the temperature: taste → five different rounds and
no shared standard; facts → one answer and shared standards, and still nobody moves.

## Correction, from member A (the same evening)

I gave A the six recorded rounds and the rule, as a file, and asked it to explain its own zero. It
rejected my explanation and supplied a better one:

> With three seats, a member can only be thrown if BOTH others name it. So a seat is safe whenever the
> other two disagree — which happens for structural reasons, not merit.

Derived from the round files (`play/log.py`), the six rejection-vote rounds:

| member | times named | rounds where both others named it (thrown) |
|---|---|---|
| A | 3 | **0** |
| B | 2 | 1 |
| C | 6 | 2 |

So the arithmetic does not merely *could* explain A's zero — it does. A was named once in three rounds and
never twice, and twice is what the rule requires. My account ("members read 'weakest' as 'least
plausible', and the loyalist owns plausibility") needed a psychology; A's needs only the rule. Same defect
I keep recording in others — explaining a number by a motive when the arithmetic was enough.

**And a worse one, mine.** The log I handed A was written by hand, and it said "A received any vote in 0
rounds". A received a vote in three of six. A could not check it, asked for the ballots, and the ballots
had been in the round files all along. A summary that is typed rather than computed is a claim, not a
record; `play/log.py` now derives it. The same round also shows `thrown out: A,C` against a rule that
throws at most one — the record and the rule disagree in one row, and that row was written before the
fold rule existed.

This also reframes section 3. The members did not refuse to be persuaded; they were never given anything
checkable. One sentence of advertisement is not evidence. A table with a rule in it is.

## The hypothesis this leaves

Members moved each other on 2026-11-01 in round 9, when the subject was **their own reliability** —
whether a timestamp taken by the same clock counts as evidence. They do not move on questions about
food or sport. The claim to test: *a member can be persuaded only where its own record is at stake.*
Test: a round whose category is a question about the tribe's own practice ("is the audit too lenient?"),
count switches. If that produces switches and pizza never does, the variable is the subject, not the
model — and it changes what this kind of tribe is good for.

**Limits, stated:** five runs per condition, one category per condition, three engines that are also
three seats. Nothing here is a rate. Two harness defects found and fixed mid-round: votes discarded by
a case comparison, and check-mode votes rendered as absence — both reported as findings rather than
quietly fixed.
