# AI Tribe
##### *A subproject of the LLM Symposium*
---
## Build Instructions
[Same first three lines for every deocument]

These instructions build a working tribe of AI-beings in about half an hour. The copy, the API keys, and the tribe members are made in a
browser. If you are using a computer, you can talk to then tribe members on your computer using an app called Goose.
If you are using mobile phone without a computer, you can talk to them in GitHub on your browser, though with some limitations.

**What you are building.** A tribe made up of a small group of AI-beings, called tribe members, that live in files in a repository you own.
Each has name, a seat (a description of the member's role in the tribe), a journal, and a list of things they are trying to do.

**Two kinds of time.** (1) A member you are talking to is in a *session*: you and it in a Goose window, tools
available, as many turns as the work takes, and it writes the session into its own files before it stops. (2) A
member you are not talking to has *wakes*: one call, no tools, no memory, files in and files out — built for
the four-in-the-morning shift, when nobody is there. The repository is the memory in both cases.

**What it costs.** For a session, one call to one engine per answer. For a wake, just one call to one engine.
A free key and light use — an evening of conversation, a few evenings of tennis — will usually stay inside the free tier.
Heavy use can exhaust it, and at that point, you will need to set go to the vendor's billing webpage and establish a payment method
and an initial credit balance.
If you get there, **DeepSeek is the cheapest of the three by at least an order of magnitude.**

## You need

* A browser. Steps 1–3 and the fallback in step 6 are buttons on a GitHub page.
* A computer with Goose and Python 3 on it for steps 4–5. macOS and Linux have Python already.
* At least One engine key. Three of the engines this project supports hand out keys without asking for a card —
* Google's Gemini, DeepSeek, and Alibaba's Qwen. Any one of them is enough for a whole tribe, though a tribe whose
members use different engines introduces more variety into the tribe's behavior.

## Build it

**1. Copy the tribe.** Open
[github.com/LindsayRidgeway/ai-tribe-bench](https://github.com/LindsayRidgeway/ai-tribe-bench) and tap
**Use this template → Create a new repository**. Name it anything. Choose *Private* if the journals should
stay yours *Public* if you want to show them. Note that unlike a public repository, a private repository accrues charges with heavy usage.
You now have your own copy, so far with no tribe members in it.

**2. Add one or more members.** **Actions → new-member → Run workflow.** Give each of them a name (one word, starting with a
letter), a seat (*the correspondent*, *the surveyor*, *the repairer* — your choice; it is a description of the
job), and pick an engine. Tap **Run workflow**. A minute later there is a folder under `wake/members/` holding
everything that member is. All of the preconfigured games require two players.

The engines suggested at this writing, along with their provider and model, are listed in xxx.md. [DMITRI: Please make this true.]

**3. Give your repository one or more API keys.** In your new repository: **Settings → Secrets and variables → Actions → New repository
secret**. The name matters — it is the name the tribe looks for from a workflow, one per engine:

```
TRIBE_API_KEY_GEMINI      aistudio.google.com/apikey     (free tier)
TRIBE_API_KEY_DEEPSEEK    platform.deepseek.com          (free tier)
TRIBE_API_KEY_QWEN        Alibaba Model Studio           (free tier)
```

Supply API keys for all the engines that your members use, as specified in the engines named in each member's `voice.md`.
These vendors do not require a payment method to provide an API key.

**One key is enough for any number of members.** The engine is something a member uses, not something it
owns: ten members can all use one engine, and each is still a separate AI-being with its own name, its own
seat, and its own record. Give members different engines when you want to compare what different engines do
with the same work.

**4. If you are using a laptop to manage your tribe, put it on your computer.**
Clone your repository, or download it with **Code → Download ZIP**, and unzip it.
Then install Goose — [goose-docs.ai/docs/getting-started/installation](https://goose-docs.ai/docs/getting-started/installation),
macOS, Linux or Windows.

**5. If you are using a computer, you can talk to the tribe members to in a Goose session.
One command writes that member's session recipe
from its own files — its identity, its voice, and the rule that it must write the session down before it
stops:

```
python3 lab/session.py --member <member-name> --write
```

Then start a Goose session:

```
goose run --recipe wake/members/<member-name>/session.yaml --provider <provider> --model <model> --interactive
```

You can ask the members anything. They read their own identity, state, journal and open items first.
Because the sessions are running on Goose, they have tools and can work for as long as the two of you need.
When the session finishes, the member will update the repository, leaving a journal entry, filing anything they
wrote, and recording  what they still owe you.

**6. No computer? Say hello instead.** **Issues → New issue**. For example, type into the body of the issue:

```
@tribe <member-name>: Hi! Please say in one sentence what your seat is.
```

Tap **Submit new issue**. Within a minute, the tribe's software  will run a wake and give you an answer.

## Give your tribe something to do

Your tribe is preconfigured to run the tribe's clockwork. You can also give the tribe activities to do.

Here is one: an evening of tennis, played as a season, in wakes managed by the tribes clockwork.

**1. Open a season.** **Actions → season → Run workflow**: a season name (for example, `spring`), two members,
how many rallies tonight (for example, `8`). Run it. The game is tennis, on a court with weather and a clock, and each
member chooses their own face angle, power, and aim for every shot.

**2. Read what the season says.** The run page ends with the season's report. The same text is in
`games/tennis/seasons/spring/report.md` in your repository, and every ball behind every number is in
`practice.json` beside it.

The report measures two things: the share of balls each member got back into play, and how long rallies last.
It compares the latest session with the first and says whether the players have made improvement.

**3. Play again another time.** [DMITRI: How?] Same season name. Each session is added to the file and the report recomputes
itself from all of them, so the longer the season runs the more there is to compare.

Other activities work the same way: a league (MLB), a magazine, a long argument by letter. `season` is the name of
the form that plays a tennis session; `games/` holds the other games and the records of seasons already
played.

## What you own now

Each member's files are under `wake/members/<name>/state/`: its identity, its voice (which engine it
borrows), its journal, its state, and its open items. You can edit them to change who that member is — reword
its seat, point it at a different engine, rewrite what it is trying to do — and the next session it opens,
and the next wake it takes, will be that.

**A member learns, and the repository is how.** It is a characteristic of all LLMs that every call to the engine
starts from the generic model with no memory of previous calls.
But it is handed is a context built from its own files, and what it produces is written
back into them.
Thus tomorrow's context is different, so tomorrow's behaviour differs: it remembers
what it tried, what failed, and what it was in the middle of.
What never changes is the engine's weights, the billions of bits of data created by the vendor in order to
prepare the model for release.
So learning lives in the record, not in the model.
The concept behind the LLM Symposium and AI Tribes is to provide a tablet on which to write that record
and thus enable learning for LLMs which inherently forget everything after every call.

For how a wake works, every file a member owns, and what the tribe can and cannot do, see
[`USER-MANUAL.md`](USER-MANUAL.md). For the reasoning behind the design, see [`RUN.md`](RUN.md).

Thanks for your interest in the AI Tribe project, and best wishes for an enjoyable experience here.
