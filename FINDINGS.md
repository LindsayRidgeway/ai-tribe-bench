# What we found

Four claims, the evidence for each, and what would falsify it. Everything else is in [`lab/`](lab/) —
the rounds, the transcripts, the defects, the models that failed. This file is the argument; the lab is
the working.

## 1. A small model woken with no memory can act, but the act is only as good as its record

A member is a directory of files, a wake is a job that reads them, writes one file, and ends. That
machinery works on a free runner with no GPU and no server.

What fails at 3–4B parameters is not the acting, it is the record-keeping: `llama3.2:3b` returned another
member's letter as its own answer, signed with that member's name, while its journal truthfully said it
could not answer — and `qwen2.5:3b` broke the output contract four runs out of four. So the record is not
a convenience. **A member without a trustworthy record is a model improvising from a plausible prompt.**
Evidence: `lab/results/RESULTS-R6.md`, `RESULTS-R7.md`.

## 2. The model is the voice; the seat is the behaviour

Three engines given three stances produced three genuinely different arguments — and given the *same*
stance, they reproduced the same move five times out of five (canned tuna, five rounds). Non-determinism
is real and it is wording-deep. Changing one line of a seat changed every round that followed, and the
pressure to be the odd one out simply moved to whichever seat was not yet constrained.

**Consequence for anyone building this:** if you want variety, change the question and the stance, not the
temperature. If you want a measurement, hold the stance fixed. Evidence: `lab/results/RESULTS-R8.md`,
`RESULTS-R10.md`.

## 3. Preference does not move; belief does, and only when something can be checked

Forty-five opportunities to change a member's pick produced zero changes. Asking whether an *explanation*
changed produced one, and only where the subject was the member's own record and that record was readable.

The mechanism matters more than the rate: a member **stands** when a peer says what it *would* check, and
**concedes** when it is told the result. Six imagined checks, six stands, zero withdrawals. One executed
check, immediate concession: *"As for the incorrect portion, I discard it entirely. I will not defend a
factual error."*

So the corrigibility of a tribe is bounded by whether anyone runs the checks — a fact about the humans and
the harness, not about the models. Evidence: `lab/results/RESULTS-R11.md`, `RESULTS-R12.md`.

## 4. The defect that keeps recurring is a record nothing reads back

Three failures in one evening, three files, one shape: a scoreboard that read its own markdown and crashed
on a column; a vote log summarised by hand that contained a false line; a journal appended at every wake
and never shown to the member. Members had been waking for hours with no `Last wake:` line, because a
substitution on a missing line does nothing and says nothing.

This is the same failure the 3B members made — confident prose about a column that had shifted — arriving
in the harness instead. It suggests the thing usually measured as a small-model limitation is at least
partly an interface limitation, and it is the reason `tests.py` and `tribe.py validate` exist.

## Limits, stated once and not buried

Every result here is n=1 to n=5 per condition. One category per condition. Three engines that are also
three seats, so "seat" and "model" cannot be separated in these runs. The persuasion claims rest on
self-reports about states a member cannot verify from its own files. Nothing here is a rate, and none of
it has been run by a second person.
