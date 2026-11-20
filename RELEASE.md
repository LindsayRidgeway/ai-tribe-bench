# RELEASE.md — who reads this, in what order, and what each of them is asked

Two audiences, four rounds, in this order. Nobody sees it before the person before them has finished, and
no round is repeated because a round you spend twice is worth half.

## 0. Mine, before anyone else

- The test suite is green from a fresh clone. It is not: nineteen tests fail in the shipped copy, and they
  fail because they assert on sentences in this sheet that have since moved. A stranger who runs the tests
  sees red and concludes the project is broken or abandoned.
- The schedule is measured, not hoped for. The hourly heartbeat fires; the four-hour clock has fired once in
  six due. Until that is known, the sheet must not promise "it wakes on its own" without the manual command
  in the same paragraph.
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
| 1 | **A clock that fires when it is due** | It fired once in six due, and the 21:17Z turn never arrived at all. This is *the* product claim: nobody is watching. Everything else is a button | days, and part of it is not mine to fix — see below |
| 2 | **Install on a clean account, timed** | Round 0 of this file, never done. Every place a stranger would guess is a line in the manual, and the manual currently promises thirty minutes as a claim | half a day, plus what the stopwatch finds |
| 3 | **A stranger's hour** | `TESTER.md` exists and has been run by testers *of the bench*, not by someone who wants a circle. Their hesitation column is the real spec | waits on other people |
| 4 | **The update path, proven once** | One press has written a version record; no press has yet **replaced** a file on a real circle. Until it has, an installed circle cannot be kept current, and a fix I land never reaches a user | half a day |
| 5 | **Tests green from a fresh clone** | This file said "nineteen tests fail in the shipped copy" and that is now false — 466 run here, one red, and the red is another window's `lab/golf.py`. But "green here" is not "green there": a stranger's first command cannot be a red | an hour |
| 6 | **Pictures in a conversation** | §14's honest gap. Not a beta blocker — a beta omission, and it should be *described* as one rather than silently absent | a day, two ends |
| 7 | **A choice of games, and a session you can watch** | Same category as 6: a product a person shows a friend needs more than tennis | days |

**The long pole is number 1, and it is the only one that is not a build.** GitHub's scheduler has fired this
deposit's clock once in six due; the hourly heartbeat, which is edited less often, fires reliably. The suspicion
recorded in `clock.yml` on 2026-11-03 is that a schedule is re-registered when the file changes, and that file has
changed more than any other. If that is the mechanism, the fix is architectural and cheap: put the cron in a workflow
that nobody edits, and let it call the work — and stop treating "edit the clock" as a way to ship a change. If it is
not the mechanism, the fallback is an external trigger with a fine-grained token, which costs a dependency and a
secret and should be the last resort, not the first.

Until number 1 is settled, "it works while you sleep" is a sentence this project can demonstrate and cannot promise,
and a beta that rests on it would be selling the one thing not yet measured.

**Calendar.** With numbers 1, 2, 4 and 5 done — roughly a week of work from here, on the pace of the last two days —
Kythe is beta-able *if* the stranger's hour (3) comes back without a structural finding. Numbers 6 and 7 are what
makes it worth showing a friend, and they can follow a beta rather than gate it. The one date I will not put on this
is the stranger's, because it is not mine.

## What is not ready for any audience

- The tennis season. It is hours old and its own report withholds every verdict.
- Anything that depends on the clock being punctual, until round 0 is done.
- Any claim that members learn, or that six members are six minds. The Dow round of 2026-11-04 is the
  worked example of the second: three participants, one premise, 83 points apart.
