# Handover — the interface

*Left by Dmitri, 2026-11-22, for whoever next opens `ait.html` with a design question. The work it
describes is commit `6dc9fa51` (2026-11-20), rewritten against the usability heuristics and the
reading studies: 79% of people scan rather than read, half the word count, one idea a paragraph,
one claim and one button above the fold, the rest one press away.*

## The rule that pass held to

**No explanation was deleted, only demoted into a `<details>`.** The only deletions were genuine
duplicates: the Members tab (it rendered Today's list a second time), the `last read HH:MM:SS`
line, the three-paragraph hero, the `$0 / From $0 / Yours` strip.

Why it matters here more than elsewhere: this product's claim is that nothing is hidden from the
person who owns the circle. An interface cannot answer that by knowing less. It answers by not
saying everything at once — and by keeping every sentence somewhere a press will reach.

When you add a section, ask two questions in this order: *is there already a row, fact or fold that
says this?* and *would a person act differently for having read it?* If both answers are no, it is
commentary, and commentary is what the person complained about.

## Two headings are mine, and unreviewed

- Home: **"AI members who work while you are away — and remember you when you come back."**
- A room: **"A round is one question put to the room at once…"**

The founder has not passed judgement on either. If a claim in them is not true of the thing as it
now behaves (the clock especially), cut it rather than patch it.

## Four states written but never exercised with a real account

They render, and the page checks assert their sentences, but no real repository has hit them:

1. A wake with **no key** — the free-bookkeeping path, and its "leaves nothing" message.
2. A **public** circle — the notice naming what becomes readable, and Settings → General.
3. The **update banner** — what an update would change, and the update actually applying.
4. A key that **cannot** be written to Actions — the wall with the paste that still works.

If you touch any of them, the honest verification is a real circle: a scratch account, one member,
one key, and then the wrong thing on purpose.

## The harness contract, which is not negotiable

`lab/page-check.mjs` and `tests.py` assert **user-facing sentences**, not just structure: *"kept in
the file and not said"*, *"free bookkeeping"*, *"The judge then picks the one answer that is said
aloud"*, `>Build an issue<`. Those sentences are the product. Read the harness before editing prose,
and never edit a test to match a rewrite — I changed zero tests in that pass, and twice rewrote a
heading because a check was right and I was not.

The counts move as the page grows; the rule does not: extract the `<script>`, `node --check` it, run
the page checks, then the suite. Both, every time.

## One concrete trap, from experience

`ait.html` is one file with three `<script>` blocks. A Python slice intended to end at the first
`: '';` matched a later one and swallowed `paintVisibility`, `roomNoteHTML`, `viewToday` and
`viewMember` — the page then threw `ReferenceError: viewToday is not defined` at first paint. Exact
strings, one replacement at a time, `assert count == 1` before replacing, and a syntax check after
each batch. The suite would have caught it in six minutes; the browser caught it in one, which is
the argument for opening the page as well as testing it.

## Where the record is

- Commit `6dc9fa51` — the message lists what moved, page by page.
- `~/LLM/dmitri-bot/dmitri-journal.md`, entry of 2026-11-20 03:12Z — the reasoning, the sites that
  refused to load, and the one risk taken on purpose: no second pair of eyes until the end.
