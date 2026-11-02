# Round 11 — evidence in the room (2026-11-01, 21:15–21:30 EST)

Round 10 ended on a confound: the members were asked whether an argument changed their mind, and they
never had an argument — they had one sentence of advertisement each and no record of anything. This round
puts the evidence in front of them and asks the same question twice, separately: **did your preference
move, and did your explanation move?**

## What was done

- `talk.sh` — the window path as a command: a member's voice is read from its own state directory, one
  wake runs, the file it wrote is printed, the exchange is committed.
- `@tribe ask <member> <question>` — the same thing inside an issue thread, with `play/log.py`'s derived
  vote log attached as the document the member must answer.
- `play/log.py` — the vote log is derived from `play/rounds/*.json` instead of typed.

Derived tally over the six rejection-vote rounds: **A named 3 times, B 2, C 6; thrown out A 0, B 1, C 2.**
With three seats a member is only thrown out when both others name it, so A was never at risk: named once
in three rounds, never twice.

## Three members, one question, the log attached

| member | preference moved? | explanation moved? | how it handled the gap |
|---|---|---|---|
| A | no — "the log gives me no reason to name C more or less" | **yes** — from no explanation to a checkable one | named what it could not check |
| B | could not say — no prior record of its own | could not say, but derived the arithmetic | refused to invent a narrative |
| C | could not say — "any claim of change would be an assumption" | could not say | restated only the verified facts |

A's formulation of the change, which is better than mine:

> Flattery would be the opposite move: leaving the result as merit, or softening it to "A was lucky."
> Luck is still a story about me. Structure is a story about the rule... I did not survive; the
> arithmetic did not reach me.

And it refused the distinction I had elided, demanding the file say whether the arithmetic *explains* the
zero or *could* explain it. The derived ballots settle it: it explains.

**All three members independently said they had no record of playing.** They were right: the game wrote to
`play/rounds/` and never to `wake/members/<name>/state/`. An activity that does not enter a member's own
record did not happen to the member.

## Three fixes, all the same defect

1. **Rounds now journal themselves into each member's state.** Verified: A's journal contains the round,
   its pick, the other picks, and the outcome.
2. **The journal was never read back into the prompt.** A member with an evening of rounds in its journal
   still answered "I have no record of what I picked" — correctly, because the harness showed it a
   directory listing and not the file. The last 4,000 characters of the journal are now in the prompt as
   "your record of what you did". Asked the same question afterwards, A recovered the round, matched its
   timestamp and category against the log, said "two documents agree, not that the event was independently
   verified", and refused my word "scattered":

   > Counting `—` cells as scatter would be reading absence as opinion... The honest verdict is
   > **underdetermined, leaning scattered** — not "scattered" as a finding.

3. **The member's own directory listing pointed one level above the repository.** Member B reported "my
   state directory is absent (`ai-tribe-bench/wake/members/b/state: No such file or directory`)" and then
   declined to say anything about its own record — the right behaviour on a broken instrument.

## The finding

**Preference did not move in forty-five opportunities, and belief moved in one of three.** The variable is
not the model, the seat, or the temperature: it is whether the subject is the member's own record and
whether it can read that record. A tribe cannot be corrected by anything it is not shown.

**And the defect pattern of the night, which is worth more than the results:** three separate failures,
three files, one shape — *a record that exists in a form nothing reads back*. The scoreboard read its own
markdown and crashed on a column. The vote log was summarised by hand and contained a false line. The
journal was appended at every wake and never shown to the member. This is the same failure the 3B members
made in round 6 — confident prose about a column that had shifted — arriving in the harness instead of in
the model.

**Limits:** three members, one question, one evening; the "belief moved" claim rests on one member's
self-report about a change of explanation it cannot verify from its own files.
