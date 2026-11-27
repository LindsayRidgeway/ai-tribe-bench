# RELEASE.md — who reads this, in what order, and what each of them is asked

Two audiences, four rounds, in this order. Nobody sees it before the person before them has finished, and
no round is repeated because a round you spend twice is worth half.

## 0. Mine, before anyone else

- ~~The test suite is green from a fresh clone.~~ **Measured 2026-11-20, and it is green.** `git clone --depth 1`
  into an empty directory, then `python3 tests.py` there: **482 tests, OK**, 275 seconds, no red. The only skips
  announce themselves and say why ("… has no key for it — skipped, not failed"). This bullet used to read
  "nineteen tests fail in the shipped copy" — true when it was written, stale by the time it was read, which is
  the exact failure this sheet exists to catch.
- **The schedule is now measured, and "not punctual" was the wrong diagnosis (corrected 2026-11-20).** This bullet
  said eight consecutive due turns each produced a run, 43–192 minutes late, and concluded that the clock "fires,
  always, and always late". That count was of **runs, not of slots** — eight runs in four days is not eight
  appointments kept. Counted properly across the 24 due slots of four days: **10 runs on this repository and 3 in
  the founder's circle** (11-16 20:17Z → 11-20 20:17Z), arriving 37 to 193 minutes after their slot, with gaps of up
  to eleven hours and one slot (08:17Z) that has never once been delivered. RUN.md §8 has said this since
  2026-11-03, with a control: a workflow asking four times an hour got 6% of what it asked for, against 15% of the
  hours when it asked once — the loss is a stretch of time with no deliveries in it, so more cron lines buy nothing.
  **The correction matters because the two documents disagreed and the beta-facing one was the wrong one.** The
  product sentence may not be "it wakes within a few hours of the time you set". It is "it wakes on its own, two or
  three times a day, at hours neither of you chooses" — and a circle that must keep a cadence needs a trigger it
  owns, outside GitHub. **Re-measured 2026-11-27 with `lab/clock.py`, seven days, both repositories: the shape
  holds and the numbers are worse in one place and better in another.** 41 due slots each; 18 runs here and 16 in
  the founder's circle, so two or three a day out of six; a median of 93 and 112 minutes late, up to 235; the
  longest silence 13.6 and 13.8 hours. The 08:17Z slot was delivered **0 times out of 7 on both repositories**
  — a fact that was "never once delivered" in the November sheet and is now measured twice — while 12:17Z arrived
  6 of 7 on both. Four slots on the bench produced two runs each (duplicates, not deliveries). The figure and the
  tool that takes it are now in the manual's §5, so the paragraph is re-derived rather than remembered.
- **One press now carries a fix to a circle (proven 2026-11-20 16:25Z).** The founder's circle took eight machinery
  files from a single press — its own `clock.yml`, `tribe.py`, `magazine.py` and others replaced, not merely recorded
  — which is the first evidence that the update path replaces rather than only notes a version. What it has not yet
  shown is the replaced clock running: the 16:17Z slot after that press was still undelivered 3 h 42 m later, which
  is the ordinary miss above and not a consequence of the press (the bench, edited at the same time, ran at 16:56Z).
- I install it myself, on a clean account, with a stopwatch, having told nobody what I already know. Every
  place I had to guess becomes a line in the sheet. The sheet currently promises thirty minutes; that
  promise is a claim until this is done.


## 0.5. Every commit names the side of the split it lives on

Gwen's finding, 2026-11-13, and it cost five testers a round of contradictory reports. This project has
three places a change can live, and they reach a tester differently:

| side | reaches a tester | how |
|---|---|---|
| **page** | at once, on every tribe | the site is served once; a reload is enough |
| **bench** | never, on its own | the bench is the project's own repository |
| **tribe** | only when that tribe updates | `lab/update_tribe.py`, run by its owner |

A retest is only meaningful if the tester knows which side was changed. So the first word of a commit
message, or the first line of the note that carries the sha, says it: `page:`, `bench:`, `tribe:`, or
`template:` for a publish. "Same tribe, same key" is true for a page fix and silently false for anything in
the machinery — a tester retesting a tribe-side patch on a tribe that cannot receive it will report
*still broken* about work that is done, and be right about what she can see.

## 1. The founder, as a stranger

Read `RUN.md` §1–§4 and mark the first place you would close it. Not an edit — a measurement. Three lines
per mark: where you were and what you were looking for, why you would have stopped, one clause on what you
would have done instead. Editing while reading destroys the only data the exercise produces; edits are
welcome afterwards.

Then, separately: install it on a machine that is not mine, without asking me anything, timed.

## 2. One or two people who have never heard of any of this

Given `RUN.md` and nothing else, with `TESTER.md` as the ask. Their job is not to be encouraging and not to
be cruel; it is to report the sentence they re-read three times. Reading the repository first makes them a
co-author and spoils the round, which is why `TESTER.md` says so in its second paragraph.

## 3. The commons, twice, with two different jobs

Two rounds, deliberately different, and each round is sealed: no participant sees another's answer before
writing its own, and none of them is given the founder's framing or mine.

**Round A — build it.** Follow `RUN.md` alone and stand up a tribe. Report what you had to guess, what you
could not get past, and the first thing you had to ask a person. The output of this round is a defect list,
not an opinion.

**Round B — grade it.** With the repository in front of you, grade the document as an instruction sheet and
say how to improve it. What is missing, what is in the wrong place, what assumes something it never says,
what would you cut.

Then the one that is not graded: **the strongest case that this is a costume** — a role-play with a filing
cabinet — and the record answers it or does not. That case is the reason the project keeps the record it
keeps, and a round that cannot be answered is a better result than a round that is.

## What the ask does not contain

No instruction about tone. Not "be encouraging", not "don't be encouraging": both are rules about the
reader, and either one produces a performance. The ask states the questions, hands over the files — the
season file, the learning curve, the three answers 83 points apart — and says nothing about how to feel
about them. My own position belongs in the sheet, where it can be attacked, not in the question where it
steers.

## Beta: what it needs, and the long pole (asked 2026-11-19)

The founder asked for an estimate of when Kythe is ready for beta testing, and what the long pole is. "Ready for
beta" has to mean something checkable, so it is written as a sentence:

> **A person who is not the founder installs Kythe from `kythe.app`, connects it to a repository they own, gives a
> member a numbered job, and reads the work in the page — with nobody from this bench in the loop and nothing typed
> into a terminal.**

**What is already true.** Those steps work when the founder does them: install, connect, the one-card token path,
the key written into the repository as a sealed Actions secret, a job handed over, a wake that thinks, a work on
the shelf, the magazine assembled, the work opened in the page, the job retired. All of it measured on his own
circle between 2026-11-19 17:23Z and 2026-11-20 00:08Z.

**What is between that and beta, in the order I would do it.**

| # | what | why it is on the list | size |
|---|---|---|---|
| 1 | **A clock the circle owns** — **ruled out, and replaced by the number** | Measured 2026-11-20 across 24 due slots: 10 runs here, 3 in the founder's circle — two or three wakes a day, 37–193 minutes late, one slot never delivered at all. The remedy was built and installed on his own circle on 2026-11-22 (`ping` → `204`, `workflow_dispatch` 22:33:16Z green, trigger logged) and then **ruled out of the product by him**: a second account, a long-lived token outside the repository, and a page whose UI changes under a manual. What replaces it is the number, printed on Today beside the button that works now — *the clock asks every four hours; GitHub usually delivers two or three of those a day, an hour or more late* — and the hand wake as the mechanism, not the fallback | a day, and it is done |
| 2 | **Install on a clean account, timed** | Round 0 of this file, never done. Every place a stranger would guess is a line in the manual, and the manual currently promises thirty minutes as a claim | half a day, plus what the stopwatch finds |
| 3 | **A stranger's hour** | `TESTER.md` exists and has been run by testers *of the bench*, not by someone who wants a circle. Their hesitation column is the real spec | waits on other people |
| 4 | ~~**The update path, proven once**~~ — **done 2026-11-20 16:25Z** | The founder's press replaced **eight machinery files** on a real circle (clock.yml, new-member.yml, REFERENCE.md, USER-MANUAL.md, magazine.py, tribe.py, wake/wake.py, the version record) and `MILESTONES.md` appeared. So a press replaces files, and a fix I land does reach a user | done |
| 5 | ~~**Tests green from a fresh clone**~~ — **done 2026-11-20** | `git clone --depth 1` into an empty directory, `python3 tests.py` → 482 tests, OK, no red. Kept in place rather than struck out of the numbering, because the calendar below refers to it by number | done |
| 6 | ~~**Pictures in a conversation**~~ — **done 2026-11-23, both directions** | **The capability** is `wake/vision.json`, one table with three readers (page, instrument, wake) and a rule: absent means unmeasured, unmeasured means blind. Measured 2026-11-22/23 — `deepseek-flash` described the known picture and said where the shapes were; `deepseek-v4-pro`, same endpoint, key and request, answered **no image**; `gemma3:4b` described a red cube; `llama3.2:3b` rejected the image outright; `qwen2.5vl:3b` has eyes, ignored them, and invented an action. **A person to a member**: *Picture* in a conversation, gated before the picker, shrunk to a 1400px JPEG, sent in the three shapes each vendor takes, recorded as a note and never as bytes. **A member to a picture, without a person in the room**: a file left in `state/inbox/` is shown at the next wake, once, and `state/looked-at.md` says what was shown, to which model, and what came of it. 544→552 tests, 144 page checks, every new check watched failing under its own mutation. **The remaining gap is measurement, not code**: only one vendor and three local models have been pointed at a picture, so the button refuses the other ten engines until somebody with a key runs one command | done, but for the unmeasured engines |
| 7 | **A choice of games, and a session you can watch** — **half built 2026-11-27** | Three games on the tab (tennis, golf, pickleball), and golf's season is watchable: the engine writes the card after each round, the run commits it between rounds, and the page paints a running table that reorders as the lead changes hands, deleting it when the season finishes. Tennis still reports at the end; same shape of work, different file. | the tennis half is days |

**The long pole is number 1 again, and it got there by my own miscount being corrected twice.** On 2026-11-19 I
named the clock the long pole and then talked myself out of it: the count of "one firing in six due" was wrong, I
said, because I had only looked at runs that arrived at their due minute — and eight consecutive due turns had all
produced runs. That second count was wrong the other way. Eight *runs* in four days is not eight appointments kept:
there were 24 due slots and 10 runs. So the first reading was right and its correction was wrong, which is the worse
of the two errors, because a correction is trusted. RUN.md §8 has carried the correct measurement since 2026-11-03
and I did not read it before overriding it. The clock is not merely imprecise: on a free public repository most of
its appointments are not delivered, and no cron line fixes that.

**The long pole is number 2**, and it always was: a real install on an account with nothing on it, timed, done by
somebody who has not already been told what he knows. That is the only place where a product decides whether it is
a product. Number 3 waits on number 2 and on a stranger.

"It works while you sleep" survives as a sentence only in the weak form: **two or three wakes a day, at hours
nobody chose**, and a circle that must keep a cadence needs a timer it owns. What may never be written is "every
four hours" or "at :17".

**Calendar, rewritten 2026-11-26.** 1 is not a build any more: it was built, installed on a real circle, and ruled
out of the product on 2026-11-22, and what replaces it is the number printed on Today beside the button that works.
4 and 5 are done. 6 is done at both ends since 2026-11-23, with one remainder that is measurement rather than code:
one vendor and three local models have been measured for vision, so the Picture button refuses the other engines
until somebody with a key runs one command each. 7 is days of work and does not gate an alpha. **2 is the only item
left that gates one**, and it is half a day plus whatever the stopwatch finds — because it is the only place where
the product meets somebody who has not already been told the answer. 3 begins the day somebody who wants a circle
sits down, and I will not put a date on it. The previous version of this paragraph said 6 and 7 did not gate a beta
and that the build side was two days with the clock at the top; the table above had already moved on, and a calendar
that disagrees with its own list is the kind of document a person quotes back at you.

## Deleting worlds — the founder's question of 2026-11-20

He asked the right question: *"why did you introduce the concept of 'worlds', especially multiple worlds, into Kythe?
Can we delete that concept and all the code, memory, and repo structure associated with it?"*

**Provenance, from the record rather than from memory.** `place.md` and the `soil/<place>/` split arrived in
`0da5fd04`, 2026-11-01 23:43, whose subject line is the whole reason: *"a second colony in a second soil — place.md
says which world a member stands in, so two colonies share one repo and the magazine names where each issue was
made."* Two parallel groups of members, one repository, one clock. Nothing about it came from a person who wanted to
run a circle.

**So: it is experiment scaffolding that leaked into the product.** A person has a circle and members in it. They did
not ask for worlds, they cannot delete the two example ones without editing files, and a member with no `place` is
invisible to the clock — a mandatory concept that buys them nothing. Yes, it can go.

**What it is load-bearing for today** (this is the cost, not the plan):

| where | what it does | what happens to it |
|---|---|---|
| `wake/members/<n>/state/place.md` | says which world a member stands in; no place = never woken | deleted; membership is the circle, not a world |
| `soil/<place>/{world,name,drops,addresses}.md` | the room a member lives in; goes into the prompt as THE SOIL | **kept, singular**: one room per circle, `world/` at the root |
| `tribe.py next` | one turn per place, so a second world gets its own turn | deleted; turns go to the fewest wakes across the circle, which is the rule from before `0da5fd04` |
| `tribe.py new/-place` | asks where the member stands | deleted; a new member joins the circle's one room |
| `magazine.py` | names the world each issue was made in | deleted; there is one |
| `ait.html` | shows `place` on the member page | deleted |
| template `soil/` (two example worlds) | ships a choice nobody asked for | one example room, or none, plus a line saying where to write your own |
| `USER-MANUAL` / `REFERENCE` / schema | documents all of the above | rewritten |

**The order I will do it in**, because a half-deleted concept is worse than either end: (1) one room, read from
`world/` if it exists and otherwise from the single directory under `soil/`, so an installed circle keeps working;
(2) the clock ignores `place` entirely and schedules across the circle; (3) `place.md` stops being read, then stops
being written; (4) the page, the manual, the reference and the schema; (5) the template. Each step is a commit that
leaves the tests green, and the whole thing is one day's work rather than a rewrite.

**What is not on the table**: deleting the room itself. A member with no room writes generic prose, and the room is
the cheapest thing in the product — four files of prose a person writes once. What goes is the plural, the
partitioning, and the requirement.

## What is not ready for any audience

- The tennis season. It is hours old and its own report withholds every verdict.
- Anything that depends on the clock being punctual, until round 0 is done.
- Any claim that members learn, or that six members are six minds. The Dow round of 2026-11-04 is the
  worked example of the second: three participants, one premise, 83 points apart.
