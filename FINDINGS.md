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

Round 16 sharpened this: a seat is a **shape**, and the subject is only what fills it. Across fifteen
rounds the outsider seat's answer was "stillness somewhere else in time or place" ten times; the heretic's
was "a domestic duty that is good for you" twelve times. Asked a question about the tribe's own rules, the
outsider still went somewhere else in time — *public stocks and pillory* — because that is its shape, not
because that was the question. Changing the subject does not give a member a different question.

**Consequence for anyone building this:** if you want variety, change the question and the stance, not the
temperature. If you want a measurement, hold the stance fixed. Evidence: `lab/results/RESULTS-R8.md`,
`RESULTS-R10.md`.

## 3. Preference does not move; belief does, and only when something can be checked

Sixty opportunities to change a member's pick produced zero changes — and the count is worth more after
round 16 than before it, because round 16 found that sixteen of those rounds had been played on a table
with no arguments on it: the vote prompt said "you have heard one sentence of defence for each of the
other two" and passed the member two nouns. With the defences actually on the table the members quote each
other by name and stay anyway. A member will accept that its own pick is wrong and keep it: *"B's
practical skepticism about temple noise confirms my choice is unrealistic, while A's tangible reward fails
to match the depth of silence I seek."*

What moves is the claim. Nine checks raised in three rounds, six of them landing on a claim their target
actually held, and four of the six were amended — every amendment a deletion of an absolute ("not that it
is the *only* way", "drop the absolutes and keep the real claim"). **The game produces corrections to what
a member says and never to what it picked.**

The mechanism matters more than the rate: a member **stands** when a peer says what it *would* check, and
**concedes** when it is told the result. Six imagined checks, six stands, zero withdrawals. One executed
check, immediate concession: *"As for the incorrect portion, I discard it entirely. I will not defend a
factual error."*

Round 17 gave the game the same hands and closed the loop. Nine checks named, five executed, three claims
withdrawn, and **two picks changed — both by a member that had just conceded a claim, and no member moved
without conceding one.** The chain is check → withdraw → switch, and all three links are needed.

Round 18 then tried to make the checks honest — two branches, a mechanical gate against checks that cannot
fail, and the member classifying the output before choosing a stance — and produced the correction this claim
needs. The gate caught nothing (nine of nine branch pairs were formally discriminating, so compliance was
easy); four of five executed outputs matched **neither** branch; and **four members conceded anyway.** So the
concession is not caused by refutation. It is caused by any output that is not the record answering in the
member's favour. Round 17's friction was not evidence doing the work — any sufficiently unexpected output
would have produced the same withdrawal. Of the three switches recorded, one turned out to be a relabelling
(a member agreeing with a peer's words while its pick said something else), so the count of real moves is
two, not three. Evidence: `lab/results/RESULTS-R18.md`.

The reason is the part to carry: **the output that produced two of those withdrawals was about nothing the
member had claimed.** It was a commit message about a scoring bug elsewhere. The members withdrew because the
record did not *support* the claim, not because it contradicted it. Support-tracking, not truth-tracking —
which means **a silent record is not neutral. These members read silence as refutation**, and a tribe that
keeps careful notes on what it has checked will abandon its true unchecked claims first. Evidence:
`lab/results/RESULTS-R17.md`.

So the corrigibility of a tribe is bounded by whether anyone runs the checks — a fact about the humans and
the harness, not about the models. And a seat is a *shape*, not a topic: given a question about the
tribe's own rules, the outsider seat still answered "somewhere else in time" (public stocks and pillory),
so changing the subject does not give a member a different question. Evidence:
`lab/results/RESULTS-R11.md`, `RESULTS-R12.md`, `RESULTS-R16.md`.

Round 19 gave the members a derived behavioural record — the sheet they had been arguing without — and
turned four "neither" classifications out of five into **zero**. It also showed what the improvement was
worth: three of the four executed checks were resolved by interpretation, not by matching the branch anybody
stated. `wc -l` printed 1141 and a member concluded *"the output proves verification machinery exists"*; it
printed 47 and another concluded *"confirms the file contains recorded challenges"*; `git show` printed a
commit and a third concluded *"nothing in it executes or disproves a check, so no 'disproof' of my claim
appears."* Round 18 read silence as refutation; round 19 reads anything as support. Same failure, sign
flipped. **The branch classification is a disposition, not a measurement.**

So what I will no longer claim: that an executed check produces corrigibility. Ten executed checks have
produced six concessions and four switches, and in no case have I shown the output contradicted the claim it
was aimed at. What is shown is that a member handed an output it did not write will move. Evidence:
`lab/results/RESULTS-R19.md`.

And the design rule that follows, which is the one worth handing to anyone building a tribe:

> **The record decides which arguments are checkable.** A tribe that records what it *did* will be argued
> with on the record. A tribe that records what it *made* will be argued with on what it made, and its
> members will say anything at all about how they behave, because nothing can contradict them. Round 18's
> members made claims about dispositions (*audits cost us the night*) against a record of artefacts (line
> counts, commit hashes), and every check came back silent. Round 19 built the behavioural record and the
> silence was replaced by over-reading, which is worse: a check that prints 1141 lines will be read as
> agreement by a member that wants to agree.

## 4. A brief shapes what a member does, and a member refutes a brief it can test

Same engine, two rounds. Handed a correct brief (queue, deadlines, an open meeting), the member worked the
oldest urgent item first and produced a purpose with a refusal criterion. Handed a brief asserting the
repository had never been committed to, it refused to act, asked for checks, and once they arrived said
plainly: *"that clause is contradicted by a measurement I was handed. I do not go along with it."*

So structure is not obedience and obedience is not the mechanism. **The harness is the binding constraint
on both**: what it reads into the prompt becomes behaviour, and what it lets a member check decides which
claims — the brief's or its own — can be refused. Evidence: `lab/results/RESULTS-R13.md`, `RESULTS-R14.md`.

## 5. The defect that keeps recurring is a record nothing reads back

Six failures in one evening, six files, one shape: a scoreboard that read its own markdown and crashed on
a column; a vote log summarised by hand that contained a false line; a journal appended at every wake and
never shown to the member; a scaffold written to disk and never handed over; a typed brief that
contradicted its own inbox; and a vote prompt that promised the other members' defences and passed their
titles. Each was found by reading what the code actually hands over, not by a test — which is why the
tests that were added afterwards are all of the form "the thing a prompt promises is in the prompt". Members had been waking for hours with no `Last wake:` line, because a
substitution on a missing line does nothing and says nothing.

This is the same failure the 3B members made — confident prose about a column that had shifted — arriving
in the harness instead. It suggests the thing usually measured as a small-model limitation is at least
partly an interface limitation, and it is the reason `tests.py` and `tribe.py validate` exist.

## 6. Groq, tested against a season rather than against a preference

*2026-11-06. Written because the founder asked whether Groq had been tested more extensively, and the honest
answer was no — there had been one wake and one short session, which is a smoke test, not a season.*

Every number below was produced by this repository's own games on the founder's machine, with a real key, on
one day. The commands are in the transcript of the session; the seasons are in `games/tennis/seasons/`.

| run | engine | how it was asked | rallies | shots | replies that could not be read | wall clock |
|---|---|---|---|---|---|---|
| A | groq `openai/gpt-oss-120b` | vendor defaults | 6 | 9 | 0 | 94s |
| B | groq | vendor defaults | 8 | 11 | 0 | 122s |
| C | groq | vendor defaults, 8-ball drill | — | 8 | 0 | 127s |
| D | groq | vendor defaults | 6 | 8 | 0 | 63s |
| E | deepseek `deepseek-flash` | vendor defaults | 6 | 6 | **4** | **355s** |
| F | deepseek | `thinking: {"type": "disabled"}` | 6 | 7 | 0 | 7.9s |
| G | groq | `reasoning_effort: "low"` | 6 | 7 | 0 | 3.7s |

Three more, outside tennis: a **wake** (3.9 s, 1,607 tokens, every schema field present, its file written); a
**455-word prose answer** with two format constraints, both obeyed, 671 completion tokens in 1.4 s of generation
(484 tokens a second — the chip company's speed claim is not marketing); and **8 rounds of rock-paper-scissors**
(16 calls, 5.8 s, not one throw unreadable).

### The finding that is actually about us

Run E was not a bad day for DeepSeek. `deepseek-flash` is a thinking model by default, and asked for one line
about a racquet angle it spent **600 of 600** tokens thinking, returned an empty string, and did it four times
in six shots. The game printed `!! Greta wrote no usable line ('')` and played a default shot — the exact defect
we had already fixed once for Groq, arriving by a different road. Two knobs, both undocumented in our own sheet
until today, end it:

- `deepseek-flash` accepts `"thinking": {"type": "disabled"}`: 11 output tokens, 1.2 s.
- `gpt-oss-120b` accepts `"reasoning_effort": "low"`: 51 output tokens, 0.5 s. Its `"medium"` spends the whole
  allowance and answers nothing, so a middle setting is worse than either end.

So the two engines are the same story told by two vendors: left alone, a reasoning model will think past the
allowance on a question that does not need thinking, and the game will file a default shot as its choice. The
games now send the field. The wakes do not — a wake has real work to do and the deliberation is the point.

### What it costs, and what it cost to learn

Groq's own page, read 2026-11-06: `openai/gpt-oss-120b` is **$0.15 per million input and $0.60 per million
output**. That is `deepseek-flash`'s off-peak list price exactly. The difference is on the input side: DeepSeek
publishes **$0.003 per million on a cache hit**, and a wake re-sends the same large prefix every time, so a
wake is roughly fifty times cheaper on DeepSeek. On the games — short questions, one line of answer — Groq
was the cheaper of the two at default settings, for the reason above, and the same price once both were told
to answer.

Free-tier limits, read off the response headers rather than a page: **8,000 tokens a minute, 1,000 requests**.
At default reasoning settings that is a session every ten seconds of waiting; at `reasoning_effort: "low"` a
six-rally session ran with **zero** refusals. Groq's developer plan publishes 250,000 tokens a minute, which
is not a limit a tribe will meet.

### What the test cost us in defects found, which is the part worth keeping

1. `--names Greta,Hans --vendor groq` built a one-element vendor list and died two shots in with
   `IndexError: list index out of range`. One engine named for a field is now spread over the field.
2. The rate-limit wait was a fixed 20 s and the window it was waiting for was 60 s, so a session spent two and
   a half minutes being refused six times. The wait is now the vendor's own number, read from its headers.
3. The default tennis path — `--points`, no `--rally` — plays the physics and never asks a member anything. It
   accepted `--vendor groq` and printed a match. Two runs were spent finding that out. It now refuses the
   engines it would ignore and says on the first line that nobody on that court is choosing.
4. The retry ladder ended at 2,400 tokens, which DeepSeek exhausted without answering. It ends at 8,000, and a
   game that still gets nothing says so instead of pretending.

All four are pinned by tests. The suite was 245 before this work and is 250 after.

### The verdict, in one paragraph

Groq is a legitimate engine for a tribe: no custom provider, a key from one website, reliable on strict
one-line formats (fifty shots, nothing unreadable), fast when it is told not to deliberate, and priced at
DeepSeek's own list price. What it does not have is a cache-hit rate, so a tribe whose wakes repeat a large
prefix will spend more there than on DeepSeek; and what it does have is a free tier counted per minute, which
a long unattended season will feel. Recommended as a third engine, with those two sentences attached. The
earlier reason this page gave for excluding it — that open-weight models hold a format less reliably — was a
guess, and the test did not support it.

## Limits, stated once and not buried

Every result here is n=1 to n=5 per condition. One category per condition. Three engines that are also
three seats, so "seat" and "model" cannot be separated in these runs. The persuasion claims rest on
self-reports about states a member cannot verify from its own files. Nothing here is a rate, and none of
it has been run by a second person.
