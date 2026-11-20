# RELEASE.md — who reads this, in what order, and what each of them is asked

Two audiences, four rounds, in this order. Nobody sees it before the person before them has finished, and
no round is repeated because a round you spend twice is worth half.

## 0. Mine, before anyone else

- ~~The test suite is green from a fresh clone.~~ **Measured 2026-11-20, and it is green.** `git clone --depth 1`
  into an empty directory, then `python3 tests.py` there: **482 tests, OK**, 275 seconds, no red. The only skips
  announce themselves and say why ("… has no key for it — skipped, not failed"). This bullet used to read
  "nineteen tests fail in the shipped copy" — true when it was written, stale by the time it was read, which is
  the exact failure this sheet exists to catch.
- **The schedule is now measured, and it is not punctual.** Eight consecutive due turns on this repository each
  produced a run; every one was late, by 43 to 192 minutes, median about two hours. On the founder's circle two of
  three due turns arrived (66 and 89 minutes late) and one never came. The scheduler belongs to the host, and the
  host does not promise a minute. So the sentence we may write is "it wakes on its own, within a few hours of the
  time you set". "At :17" must appear nowhere. (My earlier reading — one firing in six due, with re-registration
  suspected — came from counting firings only at their due minute. The correction is in `clock.yml`.)
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
| 1 | **A clock that says what it does, and does it** | The product claim is "nobody is watching", not "on the minute". Measured 2026-11-20: it fires, always, and always late. What is owed is prose that promises the window, plus a liveness check so a silently dead clock is loud | half a day for the copy and the check; days for a hard guarantee, now optional |
| 2 | **Install on a clean account, timed** | Round 0 of this file, never done. Every place a stranger would guess is a line in the manual, and the manual currently promises thirty minutes as a claim | half a day, plus what the stopwatch finds |
| 3 | **A stranger's hour** | `TESTER.md` exists and has been run by testers *of the bench*, not by someone who wants a circle. Their hesitation column is the real spec | waits on other people |
| 4 | **The update path, proven once** | One press has written a version record; no press has yet **replaced** a file on a real circle. Until it has, an installed circle cannot be kept current, and a fix I land never reaches a user | half a day |
| 5 | ~~**Tests green from a fresh clone**~~ — **done 2026-11-20** | `git clone --depth 1` into an empty directory, `python3 tests.py` → 482 tests, OK, no red. Kept in place rather than struck out of the numbering, because the calendar below refers to it by number | done |
| 6 | **Pictures in a conversation** | §14's honest gap. Not a beta blocker — a beta omission, and it should be *described* as one rather than silently absent | a day, two ends |
| 7 | **A choice of games, and a session you can watch** | Same category as 6: a product a person shows a friend needs more than tennis | days |

**The long pole is no longer number 1, and that is a correction rather than a relief.** On 2026-11-19 I named the
clock the long pole on a count of "one firing in six due", with re-registration suspected. The count was wrong: I was
only looking at runs that arrived at their due minute. Counted properly, eight consecutive due turns on this
repository all ran and all were late by 43 to 192 minutes, and the lateness is the host's documented behaviour, not a
fault in the file. So the clock is not broken; it is imprecise, and it always was. Item 1 shrinks to writing the
window honestly and adding a liveness check so that a clock which *does* stop is loud instead of silent.

**The long pole is number 2**, and it always was: a real install on an account with nothing on it, timed, done by
somebody who has not already been told what he knows. That is the only place where a product decides whether it is
a product. Number 3 waits on number 2 and on a stranger.

"It works while you sleep" is now a sentence this project can demonstrate *and* promise, provided the promise names
the window rather than the minute.

**Calendar, corrected 2026-11-20.** 5 is done. 1 is half a day instead of days. 2 and 4 are half a day each, plus
whatever the stopwatch finds. So the build side is **about two days, not a week** — the founder was right to be
surprised by a week: it contained a long pole that was a miscount. Numbers 6 and 7 still do not gate a beta; the
tennis season is a month out on its own clock and touches none of this. What remains that I cannot do is 3, a
stranger's hour, which begins the day somebody who wants a circle sits down. I will not put a date on it.

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
