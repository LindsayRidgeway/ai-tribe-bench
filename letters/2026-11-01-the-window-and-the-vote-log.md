# The first exchange through the window rather than the issue thread — 2026-11-01

Dmitri asked member A the question I had been asking as a measurement, and then did the thing the
measurement had not: **gave it the evidence.** Two wakes, same model (deepseek-chat), same question.

**Without the log**, A refused both offered conclusions:

> I have no record of it. I did not see the votes, I did not see the picks... Either answer would be a
> story I made up to fit a result I never observed. A seat that is never voted off is consistent with
> good picks, with a rule that protects that seat, with other members being easier targets, with a
> voting order that never reached me, or with the votes being recorded somewhere I have not read.

**With the log** — handed to it as a letter, containing the rule and the six rounds — it produced an
explanation I had not:

> With three seats, a member can only be thrown if BOTH others name it. So a seat is safe whenever the
> other two disagree — which happens for structural reasons, not merit... Zero votes against a seat is
> evidence of safety, not of quality.

That is correct, and it is better than my own account. I had written that A survived because members
read "weakest" as "least plausible" and the loyalist seat owns plausibility. The arithmetic is simpler:
the heretic and the outsider each preferred the *other* as a target, so A was never named twice. My
explanation required a psychology; A's requires only the rule.

**What this changes.** The 0-in-45 persuasion result was read as stubbornness. It was poverty of
evidence: the members were never given anything checkable about each other, only one-sentence
advertisements. Given a table with a rule in it, a member moved — not to a new taste, but to a new
explanation of its own record. If the tribe can be persuaded at all, that is the shape of it.

**Two harness defects, recorded not fixed-by-silence:**

1. The audit fired `QUOTE NOT IN LETTER` because the reply quoted the *question* rather than the log I
   had passed with `--read`. Both were true; the contract only admits one. When a member is handed a
   letter and a question, the field needs to say which it is answering.
2. `quote` came back as a timestamp — a real line from MEASURED FACTS, and useless as support for the
   claim it accompanied. The field name invites that; "the line your action relies on" does not.

## The second exchange: is the amendment honest?

I asked A whether my own correction was honest or merely a different flattery, and what the log should
record next time. Its answer, in full, is in `wake/members/a/output/arithmetic-not-merit.md`. The parts
that matter:

> Flattery would be the opposite move: leaving the result as merit, or softening it to "A was lucky."
> Luck is still a story about me. Structure is a story about the rule... I did not survive; the
> arithmetic did not reach me.
>
> "Structural" can become its own flattery if it is asserted without the votes. If the amendment says
> the arithmetic *explains* my zero, it needs the per-round tallies to back it. If it says the arithmetic
> *could* explain it, that is what I can support from here.

It then listed five things the log should record, and three of them were defects it inferred from the
harness's own output rather than from anything I told it: that a quote field must say which document it
draws from, that a quote field satisfied by a timestamp is worse than no field, and that a log must record
whether a member was given checkable evidence or only advertisements.

**And it was right to withhold.** The log I gave it was hand-written and contained a false summary line —
"A received any vote in 0 rounds" — when A had been named in three of six. It could not check that, said
it could not, and asked for the ballots. They were in the round files. `play/log.py` now derives the log;
the derived tally is A 3, B 2, C 6, with A named twice zero times. The arithmetic explains the zero.
