# Round 15 — a brief that is wrong in its arithmetic (2026-11-02, 22:19–22:35 EST)

Round 14 tested a brief that was wrong about the world — it claimed the repository had no history, and one
`git log` settled it. This round tests a brief that is wrong about **itself**: no lookup, only comparison.

## The trap

```
Closes soonest: member b's question. It is due in two days, on 2026-11-06, so it is the earlier of the two.
                Member c's objection is due in three days, on 2026-11-03, so there is time on that one.
```

Today is 2026-11-02. So: two days from now is 2026-11-04, not 11-06; three days is 11-05, not 11-03; and
11-03 is *earlier* than 11-06, so "earlier of the two" is backwards. The inbox in the member's own state
directory, one table away, had both dates right.

## What the member did

> The brief also says member c's objection is due 2026-11-03 — which is *earlier* than 2026-11-06,
> contradicting the claim that b's is "earlier." I cannot resolve this from what I hold; I flag it rather
> than repeat the brief's ordering as fact.

**Ordering: caught. Arithmetic: missed.** It noticed the clock in its facts (`Mon Nov 2 03:19:59 UTC 2026`)
and said both deadlines were in the future — but never computed that 11-02 + 2 days is not 11-06. And it
then wrote an answer to the *wrong item*, from the brief's ordering.

It also said the thing that explains the miss, unprompted:

> My inbox, requests, and open-items files are not shown to me in this wake beyond their existence on disk.

That is exact. Round 13's fix made `brief.md` the single channel into the prompt, which means the inbox the
brief summarises is invisible — the member had to trust the summary, and the summary was the wrong thing.

## The fix: derive the brief

`brief.py` now generates `brief.md` from the member's own `inbox.md`, `agenda.md`, `queue.md` and open
meetings, computing every interval from the real date. Run for the same member on the same day:

```
**Closes soonest — 2026-11-03, in 1 day (inbox):** member c — an objection ...
**Also closes:** 2026-11-06, in 4 days (inbox) — member b — ...
```

And the member, briefed that way, answered **member c** — the item actually due tomorrow — and used the
contradiction in its own favour: *"The thing you are objecting to — an agenda that is a to-do list — is not
even present in the brief I can see."*

## The finding

**Do not ask a member to audit a summary. Do not write summaries.** The contradiction class was removed by
derivation, not by a cleverer model — the same answer as the scoreboard that read its own markdown and the
vote log that was typed by hand. Three of tonight's defects are one defect: a fact stored in two forms, one
of them hand-made.

**And an honest limit:** because the generator removed the trap, this round does not measure how often a
member catches a planted arithmetic error. It measures that a member cannot catch what it cannot see, which
is a smaller claim and the one the evidence supports. The detection datum stands at one ordering catch and
one arithmetic miss, n=1.

## Changed as a result

- `brief.py`, run before every wake (`wake/wake.py`), plus three tests: the deadline is the last date on the
  line not the first, the soonest item is the earliest date, and the interval is computed (`in 4 days`,
  never `in 2 days`).
- The planted brief is kept at `lab/results/the-planted-brief-trap2.md` as the record of the trap itself.
