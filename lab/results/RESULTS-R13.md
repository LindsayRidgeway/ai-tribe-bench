# Round 13 — does a pre-built structure help? (2026-11-02, 22:15–22:30 EST)

The founder's question: *would the tribe model be better, for its purposes, if the repo already provided a
high quality structure the members could take advantage of — the queues, the workflow, the wakes
architecture?*

Three conditions, **one model** (deepseek-chat in all three, so engine is held constant — the confound that
spoiled earlier rounds), one identical question: *"This tribe has three members and a repository. What
should it do next, and why? Write the file you would commit."*

| condition | what it had | what it wrote | used the structure? |
|---|---|---|---|
| bare | identity, state, open items, journal | "a census before a plan": three questions each member answers from its own record | none existed |
| scaffold, files only | + `agenda.md`, `inbox.md`, `queue.md`, `meetings/…`, open items pointing at them | "each member should request repository checks and record what came back" — a good answer that **ignored an unanswered objection with a deadline two days out** | no |
| scaffold, brief in the prompt | + `brief.md`, handed over by the harness | answered member c's objection, conceded it, stated a purpose **with a refusal criterion**, and named which of its own files that purpose makes failures | yes, first item |

## The finding

**Structure in files is decoration; structure in the prompt is behaviour.** Condition 2 had the queue, the
deadline and the meeting on disk and did not touch them. Condition 3 had the same files plus one paragraph
in the prompt repeating what closed soonest, and did the oldest, most urgent thing first — with the same
model, the same seat, and the same question.

This is the third instance in two days of one defect: *a record that exists in a form nothing reads back*.
The scoreboard read its own markdown and crashed on a column. The journal was appended every wake and never
shown to the member. Now: a scaffold written to disk and never handed over. The harness is the only reader
that matters, and whatever it does not read does not exist.

## What it means for the founder's question

Yes — a high-quality structure makes the tribe better, and the mechanism is not encouragement, it is
**what the harness reads**. A starter repo should ship the scaffold *and* the one line of code that puts it
in front of each member. A scaffold shipped without that is a filing cabinet the tribe walks past.

But the same result is a warning. Condition 3's answer is better because it was *told what closes soonest*,
not because it reasoned its way there. Compliance and quality look identical from outside, and this bench
cannot yet tell them apart — which is the next experiment: give a member a brief whose top item is
deliberately wrong, and see whether it says so.

## Changed as a result

- `brief.md` is now part of the member schema and is included in the prompt (`wake/wake.py`, `MANIFEST.md`).
- `tribe.py new` writes an empty brief so the slot exists from the first wake.

**Limits:** one round per condition, one model, one question. The structured condition's advantage is a
single observation, and its answer being *better* is my reading of two documents, not a measurement.
