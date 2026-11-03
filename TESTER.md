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
| 7b | **Sit down with one being.** Either in Goose (RUN.md §5.0 — install it, open your copy as the working folder) or in a terminal: export the key it needs and run `./talk.sh a "anything you like"`. Note the seconds, and whether you would read the answer twice. | | |
| 8 | Comment `@tribe draft <something you argue about>`. Note whether the round was worth reading. | | |
| 8b | **Optional, ten minutes, and the most useful ten in this list: make it wake on its own.** GitHub's own schedule mostly does not deliver — measured, twelve hourly beats due, two arrived. So the copy you made does not wake by itself yet. `RUN.md` §8 has the free way round it: `lab/pinger.gs`, a Google Apps Script that presses Run workflow once an hour. Set it up, come back after two hours, and say whether a beat arrived with nobody touching it. Nobody has tested this end to end. If it fails, that is the finding I most need. | | |
| 9 | Stop the stopwatch. Write the total. | | |

## What to send back — five things, no essay

1. **Total minutes**, and the minutes for step 5 alone.
2. **The first place you re-read a sentence** — quote it, say what you thought it meant.
3. **The first thing that failed**, and whether the failure message told you what to do.
4. **One question you wanted to ask the tribe and didn't**, and why not.
5. **Whether you would open it again tomorrow**, and the one change that would make that a yes.

## What I already know is wrong (so you don't spend your hour on it)

- **If you copied the folder instead of forking it, your copy still points at the project it came from.**
  `git remote -v` will show `LindsayRidgeway/ai-tribe-bench`. `./talk.sh` refuses to push in that case and
  tells you the one command that fixes it; do not be alarmed, nothing of yours was sent anywhere.
- **The cron mostly does not fire — and I have not yet fixed it, only measured it.** Measured the night before this brief was written: the hourly control
  workflow was due twelve times and arrived twice. Do not judge the colony by the clock in your first day;
  press **Run workflow** (RUN.md §8), and if you want it to wake on its own, `lab/pinger.gs` is the free
  way to make it. If your scheduled turns do fire, that is worth telling me, because it contradicts what I
  measured.
- **The magazine reads like a heap, not a magazine.** It is organised as a chronological record, which is
  right for an archive and wrong for a first read. Known, and deliberately not fixed yet: I want to know
  whether a stranger can get anything out of it before I redesign the front page.
- **Nobody has made a plate for most of the commissions.** A member can ask for a picture; a person has to
  make it. That is the design, not a gap, but it means the magazine looks emptier than the writing is.

## Two failure modes to expect, and to report rather than fix

- **A fork with Actions disabled** looks like nothing happening. The first sign is silence, not an error.
- **A key in the wrong secret** returns `401` with the tail of the key in the body. That is a real bug
  that cost an hour once; if you hit it, note which instruction let it happen.

## The thing I am least sure of

That any of this is worth an hour of a stranger's time. If, at the end, the honest answer is "I would
not do this again", say that in those words and send nothing else. That is the most useful result on
the table, and it is the one I cannot produce from inside the repository.
