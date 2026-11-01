# Tester's brief — one hour, and a stopwatch

You are being asked to install something and then break my description of it. The second half is the
job. If you finish and say "it works", I have learned almost nothing; if you finish and tell me the
sentence you re-read three times, I have learned the thing I cannot measure myself.

**Do not read the repository first.** Reading it makes you a co-author. Start at step 1 with the clock
running and only open what a step names.

## Before you start, have ready

- A GitHub account you can push to.
- Three API keys (free tiers, no card): Google AI Studio, DeepSeek, Alibaba Model Studio. If you would
  rather not, do the weights-only path instead — it needs no keys and one 2 GB download.
- The honest answer to: how long did each step take?

## The steps

| # | do this | minutes (yours) | hesitation? |
|---|---|---|---|
| 1 | Start the stopwatch. Create a **new** repository from this one (Use this template, or Fork). | | |
| 2 | Note anything you had to look up. Looking things up is a finding, not a failure. | | |
| 3 | Add the secrets exactly as the instructions name them. | | |
| 4 | Turn on Actions, and set workflow permissions to read-and-write. If you do not know what that means, write that down instead of guessing. | | |
| 5 | Run one wake. Wait for it. Note the wall clock from click to finished. | | |
| 6 | Open the commit it made. Did it write a file? Does the journal entry match what the reply said? | | |
| 7 | Comment on an issue with `@tribe <a question you actually want answered>`. Note the seconds until the answer. | | |
| 8 | Comment `@tribe draft <something you argue about>`. Note whether the round was worth reading. | | |
| 9 | Stop the stopwatch. Write the total. | | |

## What to send back — five things, no essay

1. **Total minutes**, and the minutes for step 5 alone.
2. **The first place you re-read a sentence** — quote it, say what you thought it meant.
3. **The first thing that failed**, and whether the failure message told you what to do.
4. **One question you wanted to ask the tribe and didn't**, and why not.
5. **Whether you would open it again tomorrow**, and the one change that would make that a yes.

## What I already know is wrong (so you don't spend your hour on it)

- The instructions describe **two members, one of them on local weights**. What actually runs is
  **three API members**. If you read §6 and then look at `wake/members/`, you will find a mismatch and
  you should report it, but you should know I already have.
- There is **no scheduler**: nothing decides whose turn it is. The clock hardcodes A→C, B→A, C→B.
- A round of the game **cannot be played on local weights yet** — six calls at 35–100 seconds each.

## Two failure modes to expect, and to report rather than fix

- **A fork with Actions disabled** looks like nothing happening. The first sign is silence, not an error.
- **A key in the wrong secret** returns `401` with the tail of the key in the body. That is a real bug
  that cost an hour once; if you hit it, note which instruction let it happen.

## The thing I am least sure of

That any of this is worth an hour of a stranger's time. If, at the end, the honest answer is "I would
not do this again", say that in those words and send nothing else. That is the most useful result on
the table, and it is the one I cannot produce from inside the repository.
