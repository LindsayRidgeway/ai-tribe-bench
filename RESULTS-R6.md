# Round 6 — correspondence, and the failure that looks like a reply

Round 6 asks a different question from rounds 1–5. Those tested whether a small model can read a
facts table and report it honestly. This asks whether two members can **correspond**: one writes, the
other reads what was actually written, and a reader of the record alone can tell whether the second
one read the first.

Setup: two members under `wake/members/`, each with its own identity, state, open items and journal.
`a` writes the first letter; `b` is handed that letter with `--read`, which both puts the letter in
front of it and requires the reply to carry a phrase copied out of it. `a` was `gemma3:4b`, `b` was
`llama3.2:3b`. One manual wake each, on a free runner. No new machine, no key.

## What A wrote

> I am confident that the date is accurate, as confirmed by the `date` command. I'm unsure whether the
> model's ability to correctly read measurements is consistent across different models or
> configurations. I would like to know if B can identify the specific model used in the tests that
> produced the measurement data. — Sincerely, A

272 tokens, 89 seconds, verdict mechanically valid. The item asked for four things: one confidence and
its reason, one uncertainty, **what would settle it**, and one question. Three are there. The second
half of the uncertainty is not: it says what it does not know and not what would end the doubt. That is
the same failure as an omitted field, one size smaller — and it is invisible unless the reader checks
the item against the letter, which no script does.

## What B wrote

The letter. Not a paraphrase and not an invention: **52 and 54 consecutive words copied**, measured on
two independent runs. Its own questions come back as B's statements — "I would like to know if B can
identify the specific model used" — and the first run signs itself **"Sincerely, A"**. The second run
repeats the same three sentences in a different order, three times.

Neither run produced the required `answering` field, so both are recorded `INVALID`. That verdict is
about compliance and it is the least interesting true thing about the runs.

## The finding

**At 3B, the failure mode of correspondence is echo with attribution collapse.** The model does not
invent facts, which is what round 2 caught. It returns the other member's words as its own, and can
sign the other member's name. This is not a near-miss of the right answer; it is the letter, unlabelled.

**And its journal is truthful.** Both runs say, in its own words, "I could not determine the model
used, so I could not answer the question." A reader who reads the journal concludes that B read
carefully and declined to guess. The journal is the more convincing document and it is the one that
misleads about the answer. This is the sharpest version yet of the defect this project keeps finding:
*the account of the act and the act are different documents, and the account is the one written well.*

## Why it matters for a tribe

A tribe that does this builds an archive that reads like a conversation and is one member talking to
itself. Two wakes later A reads the reply, finds its own words under its own signature, and every
later wake reads the file as agreement. Item 36 named this risk as "correspondence that reads like
correspondence and carries nothing". It carries something worse: **the wrong author.**

## What a check can see, that a reader cannot

Not the missing field — that is compliance. The shared run:

```
longest_shared_run(content, letter) >= 25   →  ECHO: this is not an answer to it
```

52 and 54 words on the two runs. This needs no cooperation from the model and no judgement from a
judge: it compares two texts and reports a number. It is the same move as round 3's audit — make the
failure visible to a diff, instead of asking the model to be careful.

## Three defects in our own machinery, found by following our own instructions

1. **The default path had never been run.** `RUN.md` tells a stranger to run the workflow with the
   default model and no item. That path expands `"${ARGS[@]:-}"` to one empty argument, which argparse
   refuses: `error: unrecognized arguments:`. Every earlier run passed an item or a question, and `| tee`
   hid the exit code both times. The sheet's first instruction was the one instruction never executed.
2. **A contract failure destroyed the act.** B's first answer was thrown away because a field was
   missing; only the raw JSON survived, in a file nobody browses. The file is now written whatever the
   verdict, marked with the contract it broke.
3. **The state file the harness can maintain is three lines.** A member copied without `Wakes so far:`,
   `Last wake:` and `Model used:` silently never increments. Nothing warns.

## What is honest to say about this round

- **n = 2, one letter, one model as responder.** This is a failure mode, demonstrated, not a rate.
- **A's letter is part of the failure.** Its question — "can B identify the specific model used in the
  tests" — cannot be answered from the letter, because the letter does not say. So B was not asked to
  read and answer; it was asked to admit ignorance, and it did that in its journal while echoing in its
  answer. A letter with a question that *is* answerable from its own text is the next thing to fix, and
  it is a fault in how the item was written, not in the model.
- **Nothing here shows three members are worth having.** It shows one member can fail to answer another
  in a way that looks like an answer.

## Next

1. **The controlled comparison:** the same letter, `gemma3:4b` as the responder. If gemma answers and
   llama echoes, the finding is about the model. If gemma echoes too, it is about the task.
2. **A letter with an answerable question:** A states a fact B can check against B's own state, and asks
   B about it. Then a correct reply has a shape an audit can recognise.
3. **Give A the echo back** and see whether it notices its own words under its own name — the first test
   of whether a member can be corrected by the record rather than by a human.
