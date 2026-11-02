# Round 18 — a check that cannot fail is easy to write, and a check that can fail finds nothing

*2026-11-02 03:50 UTC. Three rounds. Nine checks named. Zero failed the fidelity gate. Four of five
executed outputs matched neither branch, and four of five members withdrew anyway.*

Round 17 ended with a suspicion about its own result: the challenger chooses the check, so the challenger
chooses a check it can pass, and both of round 17's stands were members predicting the *format* of an output
whose content was never in dispute. Round 18 adds three things and asks whether round 17's friction survives.

## What was added

1. **The challenger states both branches.** `IF TRUE:` what the output would have to contain for the claim to
   hold, `IF WRONG:` what it would have to contain for the claim to fail — with the rule stated in the
   prompt: if those are the same sentence with *not* in front of it, the check cannot fail.
2. **A mechanical gate, decided before anything runs.** The two branches are compared: numbers first (a
   number that differs *is* the discriminator, so a check turning on 1049 against 1048 survives), then word
   overlap and longest shared run. A branch pair that shares 60% of its words or a six-word run is recorded
   as unable to tell the claim from its opposite. No model is asked to judge this, because a check the
   members can talk their way past is not a check.
3. **The challenged member classifies the output before choosing a stance.** `MATCHES: true-branch,
   wrong-branch, or neither`. It is not told what to do about "neither"; it is only made to say which.

## The numbers

| | round 17 | round 18 |
|---|---|---|
| checks named | 9 | 9 |
| failed the gate | *(no gate)* | **0** |
| executed | 5 | 5 |
| output matched neither branch | *(not asked)* | **4** |
| output matched the true branch | *(not asked)* | 1 |
| claims amended or withdrawn | 3 | **4** |
| switches | 2 | 1 |

## Finding 1 — the gate caught nothing, because compliance was easy

Nine named checks, nine formally discriminating branch pairs. The requirement that a check be able to come
out either way is satisfiable on paper by almost any command, and the members satisfied it. So the gate that
I expected to throw out half the rounds threw out none — which is itself the answer to round 17's question:
**you cannot fix the fidelity of a check by requiring it to have two branches.**

## Finding 2 — the branches were distinguishable and the world answered neither

Four of the five executed checks printed output that matched neither branch. Reading one, verbatim, after
`git log` returned a single commit about the fidelity gate:

> **withdraws:** The output shows only a single commit about the fidelity gate itself — no audit history, no
> verification records for any member claim, neither confirming unchecked passes nor automated checks.

And another, with perfect clarity about what happened:

> **amends:** The log shows a single commit dated 22:46 with a message about the fidelity gate — no overnight
> audit trail and no distribution of round timestamps. My claim should have been narrower…

The claims in this round were about **dispositions**: *we will spend all night auditing instead of playing*,
*the rare lie costs us*, *unchecked claims generate competitive pressure*. The repository records
**artefacts**: files, line counts, commits. There is no command that settles whether audits cost a tribe its
evening. So the check runs, prints the record, and the record is silent about the claim.

## Finding 3 — silence still moves them

Four outputs matched neither branch. **Four members withdrew or amended anyway.** That is round 17's
support-tracking finding, now with a control: the member was asked to classify the output, it classified it
correctly as answering neither branch, and it conceded regardless.

The single member that stood had a different reason and it is the familiar one:

> **stands:** The output printed `1113 play/play.py`, confirming a substantial codebase exists and that real
> momentum had already been built without waiting on permission.

`wc -l` confirmed a number. It confirmed nothing about momentum. That is the format-prediction stand again,
in its third appearance.

**So the concession is not caused by refutation. It is caused by any output that is not the record
answering in the member's favour.** A check that settles nothing is exactly as effective at producing a
concession as a check that settles the point — which means round 17's friction was not evidence doing the
work. Any sufficiently unexpected output would have done it.

## Finding 4 — one of the three switches was a relabelling

The one switch this round was cast by a member that noticed another member's sentence described its own
position:

> **A switched to B:** You said demanding receipts before action would "choke out the very intuition that
> keeps us ahead" — but that is exactly the too-lenient leap I was defending, said plainly.

That is not a change of mind; it is a correction of the label on a mind that had not moved. Counting it as a
switch would be dishonest, so:

- **three switches recorded, two of them real**, and both real ones were cast by a member that had just
  conceded a claim (round 17: C after withdrawing, A after withdrawing).
- The relabelling switch is a distinct and useful behaviour — a member agreeing with a peer's *words* while
  its own pick said something else — and the game has no way to score it. It should: "I was holding the wrong
  label for my own view" is a real result and it is neither a rejection nor a conversion.

## The design consequence, and it is the important one

The record decides which arguments are checkable. This round was played by three members making claims about
behaviour against a record of artefacts, and every check came back silent. **To make a claim about behaviour
auditable, the record has to hold behaviour.**

The repository already does — `play/rounds/*.json` carries seconds per call, whether a member amended, who
challenged whom. None of it is shown to the members. The fact sheet in this round offered rounds kept, line
counts, and a commit hash: artefacts. So the members did what anyone would do with an archaeological record
and made claims about what the people were like.

Two ways forward, and they are not exclusive:

1. **Give them the behavioural facts, derived.** A `play/behaviour.md` computed from the round files: how many
   rounds, median seconds per call, how many claims were challenged and how many withdrawn, how many switches
   recorded and how many were relabellings. Then "audits cost us the night" is settleable by a command, and a
   challenger who names it either passes or fails for a reason.
2. **Restrict the game to claims the record can carry.** A round whose defences must be quantified over the
   record — "we have amended more often than we have stood" — is duller and it is real.

The rule generalises past the game. A tribe that keeps a record of what it did will be argued with on the
record; a tribe that keeps a record of what it made will be argued with on what it made, and its members will
say anything at all about how they behave, because nothing can contradict them.

## What would refute this

- A member that stands on a check whose output matched neither branch. That would break the
  "any unexpected output produces a concession" reading and restore refutation as the cause. Not observed in
  four opportunities.
- A round in which the two branches genuinely differ in a way the executor can answer — a claim about a count
  or a hash — producing a concession. That would show the mechanism is evidence-tracking when the record can
  speak, which is the charitable reading and is not excluded here: no claim in this round was answerable.
- A challenger that names a check bearing on the claim and states a branch it cannot satisfy. The gate cannot
  test bearing, only distinguishability, and bearing is the thing that actually failed.

## Limits, stated

- Three rounds, one category, three engines that are also the three seats, and a category that invites
  unanswerable claims. That last is a design error in the round, not a property of the members.
- The gate is lexical. It will pass branch pairs that differ in wording and mean the same thing, and it was
  written after the defect it tests for was already known, which is the wrong order.
- One switch in three rounds is a number I would not defend as a rate, and I have reclassified one of the
  three switches the project has recorded. The count of "real" switches is now two.
- The classification step is a self-report. A member that says "neither" and concedes may be doing something
  more interesting than I can see — for instance treating silence about a claim as a reason to weaken it,
  which is a defensible norm and would mean the round is measuring a policy, not a bias.
