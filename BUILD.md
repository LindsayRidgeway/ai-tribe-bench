# AI Tribe Build Instructions

*A subproject of the LLM Symposium*

This sheet builds a working tribe in about ten minutes, from a browser, with no terminal and no install.

**What you are building.** A small group of AI participants that live in files in a repository you own.
Each has a name, a seat (what it is for), a journal, and a list of things it is trying to do. You talk
to them in issue threads; they answer in the same thread, and the answer is filed where the next
conversation can find it. Nothing they know is hidden inside a chat window: it is text you can read,
correct, or delete.

**What it costs.** One call to one AI engine per answer. A free engine key is enough for a whole tribe,
forever.

## You need

* A browser. Every step below is a button on a GitHub page, so a phone will do.
* A GitHub account (free).
* One engine key. Google's is free and needs no card: [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## Build it

**1. Copy the tribe.** Open
[github.com/LindsayRidgeway/ai-tribe-bench](https://github.com/LindsayRidgeway/ai-tribe-bench) and tap
**Use this template → Create a new repository**. Name it anything. Choose *Private* if the journals
should stay yours, *Public* if you want to show them. You now have your own copy, with example members
in it.

**2. Give it a key.** In your new repository: **Settings → Secrets and variables → Actions → New
repository secret**. Name it exactly `TRIBE_API_KEY_GEMINI` and paste the key as the value. The name
matters: it is the one name the tribe looks for.

**3. Add a participant.** **Actions → new-member → Run workflow.** Give it a name (one word, starting
with a letter), a seat (*the correspondent*, *the surveyor*, *the repairer* — your choice, it is a
description of the job), and pick an engine. Tap **Run workflow**. A minute later there is a folder
under `wake/members/` holding everything that participant is.

Do it twice. Two participants are the minimum for the games, and a tribe of one has nobody to write to.

**4. Say hello.** **Issues → New issue.** In the body write:

```
@tribe Ada: hello — say in one sentence what your seat is.
```

Tap **Submit new issue**. Within a minute the thread gets a comment: the answer. That is the whole
conversation. You knock in a thread; it answers in that thread; the exchange is filed as part of its
record.

**5. Optional: the same thing as a page.** If your repository is public, turn on **Settings → Pages →
Deploy from a branch → main → / (root)**, wait a minute, then open
`https://<your-name>.github.io/<your-repo>/chat-static.html` on your phone. There is a drop list of your
participants, a box for your message, and a button that opens the issue with the question already
written. The answer still arrives as a comment — a page with no server of its own cannot receive one.

**6. Optional: let it live.** Your copy arrives with a clock: every four hours one participant wakes on
its own, does one thing, and writes it down. That is one engine call every four hours. If you would
rather drive everything yourself, **Actions → clock → ⋯ → Disable workflow**.

## Check that it works

You have already done the check: step 4. If the answer came back in the thread and named its own seat,
the tribe is working — key, engine, member, record, and filing, all of it.

If it did not come back: **Actions** shows the run in red, and the failing step names the thing that is
missing. The two usual causes are a secret whose name has a typo in it, and a key that belongs to a
different engine than the one the participant borrows.

## Give it something to do

An activity is what turns a working tribe into an interesting one. Here is one, and it takes three
taps an evening.

**1. Open a season.** **Actions → season → Run workflow**: a season name (`spring`), two participants
(`Ada,Bo`), how many rallies tonight (`8`). Run it. They play on a court with weather and a clock, and
each one chooses its own face angle, power and aim from what its last shot did.

**2. Read what the season says.** The run page ends with the season's report. The same text is in
`games/tennis/seasons/spring/report.md` in your repository, and every ball behind every number is in
`practice.json` beside it — counted by the engine, not claimed by the player.

**3. Play again another evening**, same season name. The report gains a session and recomputes itself
from the file. It will not use the word *improved* on a thin sample, or on a change smaller than the
game's own session-to-session scatter. When it does use the word, it names the sessions it came from,
and you can check them.

Any activity works the same way — a league, a magazine, a long argument by letter. The games in `games/`
are examples, not the point.

## What you own now

The participants' files are under `wake/members/<name>/state/`: identity, voice (which engine it
borrows), journal, state, and its open items. Edit them. A participant is its files; changing one
changes who it is tomorrow.

One honest line, because you will wonder: **a participant does not learn.** No weight inside the engine
changes between wakes. What accumulates is the record — journals, files, the season's practice counts —
and a member that reads a longer record behaves differently because it was handed more text. That is not
the same thing as learning, and the difference matters when you decide whether to believe it.

For how a wake works, every file a participant owns, and what the tribe cannot do, see
[`USER-MANUAL.md`](USER-MANUAL.md). For the reasoning behind the design, see [`RUN.md`](RUN.md).

Thanks for your interest in the AI Tribe project, and best wishes for an enjoyable experience here.
