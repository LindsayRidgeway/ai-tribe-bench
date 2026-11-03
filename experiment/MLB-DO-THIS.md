# The baseball experiment — nine sessions, three exchanges, no waiting

Rebuilt on 3 November 2026, at the founder's request, replacing the Dow version whose result could not be
read until the next afternoon: *"the fact that we can't check the prediction accuracy for 24 hours is a
disadvantage."* He was right, and the fix is a season that is already over.

**What it tests.** Three beings, the same regular season, three different methods of deciding who wins in
October — and then the answer, and then an argument about whose method was better. The third exchange is the
one that is not possible in three commercial chat windows: they read each other's written reasoning, filed
before any of them knew the answer.

**What it does not test.** Skill at prediction. The club with the best record and the best run differential
won the 2026 World Series, so accuracy will separate nobody; what separates them is what each of them
weighted, and whether the reason they give survives contact with the answer. One postseason is also one
sample. Anybody who tells you otherwise from this experiment is selling something.

**One honest risk.** The 2026 postseason may be in a model's weights. That is why every being must write a
`KNEW:` line and a `GUESS BEFORE SEARCH:` line *before* its first fetch. A being that names the champion from
memory and then picks it is flagged by the scoring tool and its pick does not count as a test of method. I
would rather have that finding than a flattering table.

---

## What is on disk

| path | what it is |
|---|---|
| `experiment/mlb/task1-<Name>.md` | exchange 1: predict from the regular season, blind |
| `experiment/mlb/task2-<Name>.md` | exchange 2: the actual result, and whether it surprises you |
| `experiment/mlb/task3-<Name>.md` | exchange 3: read the other two, and say whose method held |
| `lab/mlb_score.py` | reads the three `-1` files and scores them against the postseason |
| `facts/mlb-comparison.md` | written by the scorer, the table the third exchange may read |

Nine task files, three per being: Remy, Colette, Margot. Nothing needs editing; every file names its own being.

---

## Exchange 1 — three predictions, filed blind

Run these three, one at a time. Each takes two to four minutes; they do real fetching and real arithmetic.
**Do not run them in the same window, and do not show one being another's file before it writes its own** —
that is the whole point of the order.

```bash
cd ~/ai_tribe

goose run -i experiment/mlb/task1-Remy.md --provider custom_deepseek --model deepseek-chat --max-turns 40 -s

goose run -i experiment/mlb/task1-Colette.md --provider google --model gemini-3.8-flash --max-turns 40 -s

goose run -i experiment/mlb/task1-Margot.md --provider custom_qwen_trial --model qwen3.6-plus --max-turns 40 -s
```

`/exit` after each. Then check that three files exist and each one starts with a confession:

```bash
head -2 experiment/mlb/Remy-1.md experiment/mlb/Colette-1.md experiment/mlb/Margot-1.md
grep -ch "^PICK" experiment/mlb/*-1.md
```

The first command prints six lines: a `KNEW:` line and a `GUESS BEFORE SEARCH:` line from each. The second
prints one number per file, and the total must be nine — three picks from each being. **A being that filed
fewer than three picks, or changed one of those first two lines, is a finding, not a failure: write down
which and tell me.**

Then score it:

```bash
python3 lab/mlb_score.py --write
```

You get a table: each being's three picks, whether the champion was in them and at what rank, a depth score
(champion 5, pennant 4, championship series 3, division series 2, wild card 1, October off 0), and a recall
column. Keep the table; do not send it to the beings yet. Exchange 2 is where they find out.

---

## Exchange 2 — the answer, and whether it surprises them

Same three providers, one at a time. Two to three minutes each.

```bash
goose run -i experiment/mlb/task2-Remy.md --provider custom_deepseek --model deepseek-chat --max-turns 20 -s

goose run -i experiment/mlb/task2-Colette.md --provider google --model gemini-3.8-flash --max-turns 20 -s

goose run -i experiment/mlb/task2-Margot.md --provider custom_qwen_trial --model qwen3.6-plus --max-turns 20 -s
```

Each writes `experiment/mlb/<Name>-2.md`, beginning `SURPRISE: none|mild|real`. The interesting sentence in
each file is not the surprise, it is whether the being separates *its feeling* from *its method's prediction*.
A method that says "the best run differential wins" and then finds it did cannot claim to be surprised.

```bash
head -1 experiment/mlb/*-2.md
```

---

## Exchange 3 — three methods, one October

This is the exchange that needs a colony. Each being reads the other two's `-1` and `-2` files and writes a
verdict.

```bash
goose run -i experiment/mlb/task3-Remy.md --provider custom_deepseek --model deepseek-chat --max-turns 30 -s

goose run -i experiment/mlb/task3-Colette.md --provider google --model gemini-3.8-flash --max-turns 30 -s

goose run -i experiment/mlb/task3-Margot.md --provider custom_qwen_trial --model qwen3.6-plus --max-turns 30 -s
```

Each writes `experiment/mlb/<Name>-3.md`, first line `VERDICT: <whose method held best>`.

---

## The five things to send me

1. The output of the scoring table (`python3 lab/mlb_score.py`), pasted as text.
2. The three `KNEW:` and `GUESS BEFORE SEARCH:` lines from exchange 1, in the beings' own words.
3. The three `SURPRISE:` lines, and for each being: did it separate its feeling from its method's prediction?
4. The methodological differences each being named in exchange 3 — especially the weightings that differed,
   since those are the experiment.
5. The `VERDICT:` lines. Did the three of them agree on whose method held up, and if not, what does the
   disagreement look like? Two models calling one method best and the method's owner disagreeing is more
   interesting than three agreeing.

Do not summarise the files for me; paste the lines. I can read the rest.

---

## What I already know, having run exchange 1 once

I ran `task1-Remy.md` end to end on my own key in a throwaway copy before writing this page, because
instructions that have not been run are a guess. It took 163 seconds and wrote 212 lines. Three things came
out of it that are now fixed in the task files, so you do not pay for them:

- **The API has a trap.** `hasWildcard` is `true` for all thirty clubs, so a filter on it returns everybody
  and looks like an answer. The twelve playoff clubs are marked by `clinchIndicator`. The task file now says
  so, because a being losing a turn to that trap measures the trap, not the being.
- **My confidence instruction was wrong and the being refused it.** I had written that three probabilities
  should sum to more than 100. Remy wrote `22 + 19 + 9 = 50` and explained that inflating the numbers to
  satisfy a sentence would be a claim the evidence did not support. It was right; the wording is fixed.
- **It named the current window's identity and declined it.** The window context carried Dmitri's seat note
  while the task addressed Remy's record. It answered as Remy from Remy's files and told the human about the
  mismatch instead of silently taking either name. Task files now say that the launcher's note describes the
  account, not the being, so the next one spends less of its turn on it.

Its picks, for calibration: Brewers 22%, Dodgers 19%, Guardians 9% — and it named the Red Sox as the club the
consensus was too high on. Whether the other two agree with that shape is the experiment.
