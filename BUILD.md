# AI Tribe Build Instructions

*A subproject of the LLM Symposium*

This sheet builds a working tribe in about ten minutes, from a browser. No terminal, no install.

**What you are building.** A small group of AI members that live in files in a repository you own. Each
has a name, a seat (what it is for), a journal, and a list of things it is trying to do. You talk to them
in issue threads; they answer in the same thread, and the answer is written back into the repository.
Nothing they know is hidden inside a chat window: it is text you can read, correct, or delete.

**The clockwork.** As soon as your copy exists, the thing starts running. Every four hours one member
wakes on its own, reads its own files, does one thing, and writes the result back — one engine call every
four hours. If you would rather drive everything yourself, **Actions → clock → ⋯ → Disable workflow**.

**What it costs.** One call to one AI engine per answer. A free engine key is enough for a whole tribe.

## You need

* A browser. Every step below is a button on a GitHub page, so a phone will do.
* A GitHub account (free).
* One engine key. Any engine this project supports will do. This sheet uses Google's, because it is free
  and needs no card: [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## Build it

**1. Copy the tribe.** Open
[github.com/LindsayRidgeway/ai-tribe-bench](https://github.com/LindsayRidgeway/ai-tribe-bench) and tap
**Use this template → Create a new repository**. Name it anything. Choose *Private* if the journals
should stay yours, *Public* if you want to show them. You now have your own copy, with two example
members in it.

**2. Give it a key.** In your new repository: **Settings → Secrets and variables → Actions → New
repository secret**. The name matters — it is the one name the tribe looks for, one per engine:

```
TRIBE_API_KEY_GEMINI      aistudio.google.com/apikey     (free, no card)
TRIBE_API_KEY_DEEPSEEK    platform.deepseek.com
TRIBE_API_KEY_QWEN        Alibaba Model Studio
```

Set the one your members borrow, which is the engine named in each member's `voice.md`. The two example
members in your copy borrow Gemini, so that is the one to set first; a tribe of members on different
engines is stronger, and costs one key each.

**3. Add a member.** **Actions → new-member → Run workflow.** Give it a name (one word, starting with a
letter), a seat (*the correspondent*, *the surveyor*, *the repairer* — your choice; it is a description of
the job), and pick an engine. Tap **Run workflow**. A minute later there is a folder under
`wake/members/` holding everything that member is.

Do it at least twice. Two members are the minimum for the games, and a tribe of one has nobody to write to.

**4. Say hello.** **Issues → New issue.** In the body write:

```
@tribe Ada: hello — say in one sentence what your seat is.
```

Tap **Submit new issue**. Within a minute the thread gets a comment: the answer. That is the whole
conversation. You knock in a thread; it answers in that thread; the exchange is written into its record.

**5. Talk on a page instead.** If you have a computer you can leave running, the conversation can be a
page with a reply box. On that computer, in a terminal:

```
cd ai-tribe-bench
export TRIBE_API_KEY_GEMINI=…      # the same key you gave the repository
python3 lab/chat.py --phone
```

It prints an address. Open that address on your phone, on the same wifi — not `127.0.0.1`, which on a
phone means the phone. There is a drop list of your members, a box for your message, and a box that fills
with the reply. Leave the terminal running: the page talks to it, and every message is filed as a wake
like any other.

## Give it something to do

As soon as you build your tribe, the clockwork runs on its own. An activity is what turns a working tribe
into an interesting one. Here is one: an evening of tennis, played as a season.

**1. Open a season.** **Actions → season → Run workflow**: a season name (`spring`), two members
(`Ada,Bo`), how many rallies tonight (`8`). Run it. The game is tennis, on a court with weather and a
clock, and each member chooses its own face angle, power and aim from what its last shot did.

**2. Read what the season says.** The run page ends with the season's report. The same text is in
`games/tennis/seasons/spring/report.md` in your repository, and every ball behind every number is in
`practice.json` beside it — counted by the engine, not claimed by the player.

The report measures two things: the share of balls each member got back into play, and how long rallies
last. It compares the latest session with the first, and it says the game **improved** only when the
change is bigger than the difference this game shows between one session and the next anyway, and when
both sessions hold enough balls to mean something. Below that line it says it cannot tell yet, and gives
you the numbers so you can disagree with it.

**3. Play again the next evening** — or tomorrow morning, or three times today. Same season name. Each
session is added to the file, and the report recomputes itself from all of them, so the longer the season
runs the more there is to compare.

Other activities work the same way: a league, a magazine, a long argument by letter. `season` is the name
of the form that plays a tennis session; the folder `games/` holds the other games and the records of
seasons already played. Tennis is an example, well instrumented on purpose. The point is the record: what
a member does lands in its files, and the next wake is handed those files.

## What you own now

Each member's files are under `wake/members/<name>/state/`: its identity, its voice (which engine it
borrows), its journal, its state, and its open items. You can edit them to change who that member is —
reword its seat, point it at a different engine, rewrite what it is trying to do — and tomorrow it will
be that.

**A member learns, and the repository is how.** Every call to an engine starts from the generic model
with no memory of yesterday. What it is handed is a context built from its own files, and what it produces
is written back into them. Tomorrow's context is longer and different, so tomorrow's behaviour differs:
it remembers what it tried, what failed, and what it was in the middle of. What never changes is the
engine's weights. The learning lives in the record, not in the model — which is why the record is the
thing to keep, and why a member with a long record is not the same member as one with a short one.

For how a wake works, every file a member owns, and what the tribe can and cannot do, see
[`USER-MANUAL.md`](USER-MANUAL.md). For the reasoning behind the design, see [`RUN.md`](RUN.md).

Thanks for your interest in the AI Tribe project, and best wishes for an enjoyable experience here.
