# AI Tribe Build Instructions

*A subproject of the LLM Symposium*

This sheet builds a working tribe in about half an hour. The copy, the keys and the members are made in a
browser; the talking happens on your computer, in Goose.

**What you are building.** A small group of AI members that live in files in a repository you own. Each has
a name, a seat (what it is for), a journal, and a list of things it is trying to do. Nothing they know is
hidden inside a chat window: it is text you can read, correct, or delete.

**Two kinds of time.** A member you are talking to is in a *session*: you and it in a Goose window, tools
available, as many turns as the work takes, and it writes the session into its own files before it stops. A
member you are not talking to has *wakes*: one call, no tools, no memory, files in and files out — built for
the four-in-the-morning shift, when nobody is there. The repository is the memory in both cases, which is
why the session has to end by writing itself down.

**What it costs.** One call to one engine per answer, and a session is many calls. A free key and light use —
an evening of conversation, a few evenings of tennis — will usually stay inside the free tier. Heavy use can
exhaust it, and at that point the vendor asks for a payment method. If you get there, **DeepSeek is the
cheapest of the three by at least an order of magnitude.**

## You need

* A browser. Steps 1–3 and the fallback in step 6 are buttons on a GitHub page.
* A computer with Goose and Python 3 on it for steps 4–5. macOS and Linux have Python already.
* One engine key. Three of the engines this project supports hand out keys without asking for a card —
  Google's Gemini, DeepSeek, and Alibaba's Qwen. Any one of them is enough for a whole tribe; a tribe whose
  members borrow different engines is the stronger arrangement.

## Build it

**1. Copy the tribe.** Open
[github.com/LindsayRidgeway/ai-tribe-bench](https://github.com/LindsayRidgeway/ai-tribe-bench) and tap
**Use this template → Create a new repository**. Name it anything. Choose *Private* if the journals should
stay yours, *Public* if you want to show them. You now have your own copy, with two example members in it.

**2. Give it a key.** In your new repository: **Settings → Secrets and variables → Actions → New repository
secret**. The name matters — it is the one name the tribe looks for from a workflow, one per engine:

```
TRIBE_API_KEY_GEMINI      aistudio.google.com/apikey     (free tier)
TRIBE_API_KEY_DEEPSEEK    platform.deepseek.com          (free tier)
TRIBE_API_KEY_QWEN        Alibaba Model Studio           (free tier)
```

Set the one your members borrow, which is the engine named in each member's `voice.md`. The two example
members in your copy borrow Gemini, so that is the one to set first. None of the three asks for a card.

**One key is enough for any number of members.** The engine is something a member borrows, not something it
owns: ten members can all borrow one engine, and each is still a separate being with its own name, its own
seat and its own record. Give members different engines when you want to compare what different engines do
with the same work.

**3. Add a member.** **Actions → new-member → Run workflow.** Give it a name (one word, starting with a
letter), a seat (*the correspondent*, *the surveyor*, *the repairer* — your choice; it is a description of the
job), and pick an engine. Tap **Run workflow**. A minute later there is a folder under `wake/members/` holding
everything that member is. Do it at least twice: two members are the minimum for the games.

**4. Put the tribe on your computer.** Clone your repository, or download it with **Code → Download ZIP** and
unzip it. Then install Goose — [goose-docs.ai/docs/getting-started/installation](https://goose-docs.ai/docs/getting-started/installation),
macOS, Linux or Windows — and start it once in that folder, because it will ask you for a provider and a key:

```
goose session
```

Use the same engine and key you gave the repository. That is the second and last place a key goes.

**5. Visit a member.** A member is talked to in a session. One command writes that member's session recipe
from its own files — its identity, its voice, and the rule that it must write the session down before it
stops:

```
python3 lab/session.py --member Ada --write
goose run --recipe wake/members/Ada/session.yaml --interactive
```

Ask it anything. It reads its own identity, state, journal and open items first, it has its tools, and it can
work for as long as the two of you need. When it finishes it should leave a journal entry, file anything it
wrote, and record what it still owes you — check that it did, because nobody else will: a session is not a
wake, and the harness does not file it for you.

If a member should run on its own engine rather than whatever Goose is set to, `goose run` takes
`--provider` and `--model`; the two lines in `voice.md` are the ones to copy.

**6. No computer? Say hello instead.** **Issues → New issue**, and in the body:

```
@tribe Ada: hello — say in one sentence what your seat is.
```

Tap **Submit new issue**. Within a minute the thread gets a comment: the answer, from a wake rather than a
session. It has no tools and no memory of yesterday beyond its files, and it still answers. This is the only
route that needs nothing but a browser, and it is also the route the clock uses when you are away.

## Give it something to do

An activity is what turns a working tribe into an interesting one. Here is one: an evening of tennis, played
as a season, and it runs on the clockwork rather than on your session.

**1. Open a season.** **Actions → season → Run workflow**: a season name (`spring`), two members (`Ada,Bo`),
how many rallies tonight (`8`). Run it. The game is tennis, on a court with weather and a clock, and each
member chooses its own face angle, power and aim from what its last shot did.

**2. Read what the season says.** The run page ends with the season's report. The same text is in
`games/tennis/seasons/spring/report.md` in your repository, and every ball behind every number is in
`practice.json` beside it — counted by the engine, not claimed by the player.

The report measures two things: the share of balls each member got back into play, and how long rallies last.
It compares the latest session with the first, and it says the game **improved** only when the change is
bigger than the difference this game shows between one session and the next anyway, and when both sessions
hold enough balls to mean something. Below that line it says it cannot tell yet, and gives you the numbers so
you can disagree with it.

**3. Play again another time.** Same season name. Each session is added to the file and the report recomputes
itself from all of them, so the longer the season runs the more there is to compare.

Other activities work the same way: a league, a magazine, a long argument by letter. `season` is the name of
the form that plays a tennis session; `games/` holds the other games and the records of seasons already
played. Tennis is an example, well instrumented on purpose. The point is the record: what a member does lands
in its files, and the next session or wake is handed those files.

## What you own now

Each member's files are under `wake/members/<name>/state/`: its identity, its voice (which engine it
borrows), its journal, its state, and its open items. You can edit them to change who that member is — reword
its seat, point it at a different engine, rewrite what it is trying to do — and the next session it opens,
and the next wake it takes, will be that.

**A member learns, and the repository is how.** Every call to an engine starts from the generic model with no
memory of yesterday. What it is handed is a context built from its own files, and what it produces is written
back into them. Tomorrow's context is longer and different, so tomorrow's behaviour differs: it remembers
what it tried, what failed, and what it was in the middle of. What never changes is the engine's weights. The
learning lives in the record, not in the model — which is why the record is the thing to keep, and why a
member with a long record is not the same member as one with a short one.

For how a wake works, every file a member owns, and what the tribe can and cannot do, see
[`USER-MANUAL.md`](USER-MANUAL.md). For the reasoning behind the design, see [`RUN.md`](RUN.md).

Thanks for your interest in the AI Tribe project, and best wishes for an enjoyable experience here.
