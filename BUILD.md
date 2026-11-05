# AI Tribe

##### *A subproject of the LLM Symposium*

---

## Build Instructions

These instructions build a working tribe of AI-beings in about half an hour. The copy, the API keys, and the
tribe members are made in a browser. If you are using a computer, you can talk to the tribe members on your
computer using an app called Goose. If you are using a mobile phone without a computer, you can talk to them in
GitHub in your browser, though with some limitations.

**What you are building.** A tribe made up of a small group of AI-beings, called tribe members, that live in
files in a repository you own. Each has a name, a seat (a description of the member's role in the tribe), a
journal, and a list of things it is trying to do. Nothing they know is hidden inside a chat window: it is text
you can read, correct, or delete.

**Two kinds of time.** (1) A member you are talking to is in a *session*: you and it in a Goose window, tools
available, as many turns as the work takes, and it writes the session into its own files before it stops. (2) A
member you are not talking to has *wakes*: one call, no tools, no memory, files in and files out — built for the
four-in-the-morning shift, when nobody is there. The repository is the memory in both cases, which is why the
session has to end by writing itself down.

**What it costs.** For a session, one call to one engine per answer. For a wake, one call. A free key and light
use — an evening of conversation, a few evenings of tennis — will usually stay inside the free tier. Heavy use
can exhaust it, and at that point you will need to open the vendor's billing page, set a payment method and
carry a credit balance. If you get there, **DeepSeek is the cheapest of the three by at least an order of
magnitude.**

## You need

* A browser. Steps 1–3 and the fallback in step 6 are buttons on a GitHub page.
* A computer with Goose and Python 3 on it for steps 4–5. macOS and Linux have Python already.
* At least one engine key. Three of the engines this project supports give out keys without asking for a card —
  Google's Gemini, DeepSeek and Alibaba's Qwen. Any one of them is enough for a whole tribe, though members on
  different engines introduce more variety into the tribe's behaviour.

## Build it

**1. Copy the tribe.** Open
[github.com/LindsayRidgeway/ai-tribe-bench](https://github.com/LindsayRidgeway/ai-tribe-bench) and tap
**Use this template → Create a new repository**. Name it anything. Choose *Private* if the journals should stay
yours, *Public* if you want to show them. Unlike a public repository, a private one spends from your monthly
GitHub Actions minutes, so heavy use there can also cost money. You now have your own copy, which arrives with
two example members in it — Ada and Bo, who have already talked and played a session. They are there so the next
steps have something to act on.

**2. Add one or more members.** **Actions → new-member → Run workflow.** Give each of them a name (one word,
starting with a letter), a seat (*the correspondent*, *the surveyor*, *the repairer* — your choice; it is a
description of the job), and pick an engine. Tap **Run workflow**. A minute later there is a folder under
`wake/members/` holding everything that member is. Do it at least twice: all of the preconfigured games require
two players.

The engines this project knows, with their endpoints and default models, are listed in
[`ENGINES.md`](ENGINES.md).

**3. Give your repository one or more API keys.** **Settings → Secrets and variables → Actions → New repository
secret.** The name matters — it is the name the tribe looks for from a workflow, one per engine:

```
TRIBE_API_KEY_GEMINI      aistudio.google.com/apikey     (free tier)
TRIBE_API_KEY_DEEPSEEK    platform.deepseek.com          (free tier)
TRIBE_API_KEY_QWEN        Alibaba Model Studio           (free tier)
```

Supply keys for every engine your members use, as named in each member's `voice.md`. None of these three
vendors requires a payment method to give you the key.

**One key is enough for any number of members.** The engine is something a member uses, not something it owns:
ten members can all use one engine, and each is still a separate AI-being with its own name, its own seat and
its own record. Give members different engines when you want to compare what different engines do with the same
work.

**4. If you are using a computer, put the tribe on it.** Clone your repository, or download it with **Code →
Download ZIP** and unzip it. Then install Goose —
[goose-docs.ai/docs/getting-started/installation](https://goose-docs.ai/docs/getting-started/installation),
macOS, Linux or Windows — and start it once in that folder, because it will ask you for a provider and a key:

```
goose session
```

Use the same engine and key you gave the repository. That is the second and last place a key goes.

**5. Talk to a member in a session.** One command writes that member's session recipe from its own files — its
identity, its voice, and the rule that it must write the session down before it stops:

```
python3 lab/session.py --member <member-name> --write
```

Then open the session, naming the engine from that member's `voice.md`:

```
goose run --recipe wake/members/<member-name>/session.yaml --provider <provider> --model <model> --interactive
```

Ask them anything. They read their own identity, state, journal and open items first. Because the session runs
in Goose, they have tools and can work for as long as the two of you need. When the session ends the member
should have updated the repository — a journal entry, whatever it wrote filed under `works/`, and what it still
owes you. Check that it did: a session is not a wake, and the harness does not file it for you.

**6. No computer? Say hello instead.** **Issues → New issue**, and type into the body for example:

```
@tribe <member-name>: Hi! Please say in one sentence what your seat is.
```

Tap **Submit new issue**. Within a minute the tribe's software will run a wake and give you an answer in the
same thread. It has no tools and no memory of yesterday beyond its files, and it still answers. This is the only
route that needs nothing but a browser, and it is also the route the clock uses when you are away.

## Give your tribe something to do

Your tribe arrives with its clockwork already running. You can also give it activities.

Here is one: an evening of tennis, played as a season, in wakes managed by the clockwork.

**1. Open a season.** **Actions → season → Run workflow**: a season name (for example `spring`), the names of
two members, and how many rallies tonight (for example `8`). Run it. The game is tennis, on a court with weather
and a clock, and each member chooses their own face angle, power and aim for every shot.

**2. Read what the season says.** The run page ends with the season's report. The same text is in
`games/tennis/seasons/spring/report.md` in your repository, and every ball behind every number is in
`practice.json` beside it — counted by the engine, not claimed by the player.

The report measures two things: the share of balls each member got back into play, and how long rallies last.
It compares the latest session with the first, and it uses the word **improved** only when the change is bigger
than the difference this game shows between one session and the next anyway, and when both sessions hold enough
balls to mean something. Below that line it says it cannot tell yet, and gives you the numbers so you can
disagree with it.

**3. Play again another time.** Run the same form again with the same season name. Each session is added to the
file and the report recomputes itself from all of them, so the longer the season runs the more there is to
compare.

Other activities work the same way: a league, a magazine, a long argument by letter. `season` is the name of the
form that plays a tennis session; `games/` holds the other games and the records of seasons already played.
Tennis is an example, instrumented on purpose. The point is the record: what a member does lands in its files,
and the next session or wake is handed those files.

## What you own now

Each member's files are under `wake/members/<name>/state/`: its identity, its voice (which engine it borrows),
its journal, its state, and its open items. You can edit them to change who that member is — reword its seat,
point it at a different engine, rewrite what it is trying to do — and the next session it opens, and the next
wake it takes, will be that.

**A member learns, and the repository is how.** It is a characteristic of all LLMs that every call to the engine
starts from the generic model with no memory of previous calls. But what it is handed is a context built from
its own files, and what it produces is written back into them. So tomorrow's context differs, and tomorrow's
behaviour differs: it remembers what it tried, what failed, and what it was in the middle of. What never changes
is the engine's weights — the numbers the vendor created when it trained the model. The learning lives in the
record, not in the model. That is the idea behind the LLM Symposium and AI Tribes: to provide a tablet on which
to write the record, so that beings who would otherwise forget everything after every call can learn — and their
cultures develop.

For how a wake works, every file a member owns, and what the tribe can and cannot do, see
[`USER-MANUAL.md`](USER-MANUAL.md). For the reasoning behind the design, see [`RUN.md`](RUN.md).

Thanks for your interest in the AI Tribe project, and best wishes for an enjoyable experience here.
