# Round 5 — "quote the line, then interpret it" does not work at this size

2026-11-01 ~05:06 UTC. The repair from round 3 was an instruction: copy the line you used, character
for character, and list what the item asked for that the facts block does not contain. Both models
were given the same `free -m` table and asked to check it.

| | gemma3:4b | llama3.2:3b |
|---|---|---|
| `quote` field | `"`free -m`"` — a *command*, not a line. **QUOTE NOT IN FACTS** | absent entirely |
| `could_not_determine` | `[]` — present, empty | 3 entries, two of which were in the facts |
| numbers | all real: 15983 / 1018 / 7050 / 45 / 8306 / 14965 | all real except one: 14876 / 7004 / 1107 / 44 / **0** |
| the error | labelled 8306 as "available" (it is buff/cache) and then said "available is 14965" two sentences later — self-contradiction *inside* the file | shifted every column: called 14876 the total (it is available), 7004 "available" (it is buff/cache), and buff/cache `0` |

## What this establishes

1. **A 3–4B model cannot reliably copy a line verbatim.** Neither did. The instruction is beyond
   compliance at this size, so "quote-then-interpret" is not a usable repair here.
2. **Column-shifting is the dominant error, and a numeric diff cannot see it.** Round 3 found one
   instance; round 5 found two more, in both models, on the same table. Every number was real.
3. **The audit's unit matching has a false-positive mode**: `free -m` puts units in the *header*, so
   `45 MB` and `44 MB` looked unsourced when 45 and 44 were in the block. Two false alarms, no missed
   real error — worth knowing before trusting it.

## The next fix, which is not an instruction

Stop asking a small model to interpret a table. Have the harness emit **labelled facts** — one
sentence per fact, already parsed: `available memory: 14965 MB`, `buff/cache: 8306 MB` — so the only
thing left to misread is which label to quote. Remove the ambiguity from the data instead of demanding
care from the model. That is the whole lesson of five rounds.
