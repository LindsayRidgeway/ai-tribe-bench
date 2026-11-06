# AI Tribe
##### *A subproject of the LLM Symposium*
---
## Build Instructions
[Same first three lines for every document]

These instructions build a working tribe of AI-beings in about half an hour. The copy, the API keys, and the tribe members are made in a
browser. If you are using a computer, you can talk to the tribe members on your computer using an app called Goose.
If you are using mobile phone without a computer, you can talk to them in GitHub on your browser, though with some limitations.

**What you are building.** A tribe made up of a small group of AI-beings, called tribe members, that live in files in a repository you own.
Each tribe member has a name, a seat (a description of the member's role in the tribe), a journal, and a list of things they are trying to do.

**Two kinds of time.** (1) A member you are talking to is in a *session*: you and it in a Goose window, tools
available, as many turns as the work takes, and the member writes the session into their own files before they stop. (2) A
member you are not talking to has *wakes*: one call, no tools, no memory, files in and files out — built for
the four-in-the-morning shift, when you are not present. The repository is the memory in both cases.

**What it costs.** For a session, one call to one engine per answer. For a wake, just one call to one engine.
A free key and light use — an evening of conversation, a few evenings of tennis — will usually stay inside the free tier.
Heavy use can exhaust the free tier, and at that point, you will need to go to the vendor's billing webpage and establish a payment method
and an initial credit balance.
If you get there, **DeepSeek is the cheaper of the two by at least an order of magnitude.**

## You need

* A browser. Steps 1–3 and the fallback in step 6 are buttons on a GitHub page.
* A computer with Goose and Python 3 on it for steps 4–5. macOS and Linux have Python already.
* At least one engine key. Two of the engines this project supports hand out keys without asking for a card —
Google's Gemini and DeepSeek. Either one is enough for a whole tribe, though a tribe whose
members use different engines introduces more variety into the tribe's behavior.

## Build it

**1. Copy the tribe.** Open
[github.com/LindsayRidgeway/ai-tribe-bench](https://github.com/LindsayRidgeway/ai-tribe-bench) and tap
**Use this template → Create a new repository**. Name it anything. Choose *Private* if the journals should
stay yours, *Public* if you want to show them. Note that unlike a public repository, a private repository accrues charges with heavy usage.
You now have your own AI tribe, so far with no tribe members in it.

**2. Add two or more members.** **Actions → new-member → Run workflow.** Give each member a name of your own
choosing (one word, starting with a letter), a seat (*the correspondent*, *the surveyor*, *the repairer* — your
choice; it is a description of the job), and pick an engine for each: either of the recommended engines, with as
many members on one engine as you like. All of your members may share a single engine. For each member, tap **Run workflow**.
A minute later there is a folder under `wake/members/` holding everything that member is.
All of the preconfigured games require two players, which is why two members at minimum.

The currently recommended engines, and the provider and model names Goose uses for each, are listed in
`ENGINES.md` in your new repository. [DMITRI: ENGINES.md exists and is nearly true; please bring its "What Goose
calls them" table in line with the no-custom-provider path — in Goose 1.57 DeepSeek is built in, so neither
recommended engine needs a custom provider or any configuration file.]

**3. Give your repository one or more API keys.** In your new repository: **Settings → Secrets and variables → Actions → New repository
secret**. The name matters — it is the name the tribe looks for from a workflow, one per engine:

```
TRIBE_API_KEY_GEMINI      aistudio.google.com/apikey     (free tier)
TRIBE_API_KEY_DEEPSEEK    platform.deepseek.com          (free tier)
```

Supply API keys for all the engines that your members use, as specified in the engines named in each member's `voice.md`.
These vendors do not require a payment method to provide an API key.

**One key is enough for any number of members.** The engine is something a member uses, not something it
owns: ten members can all use one engine, and each is still a separate AI-being with its own name, its own
seat, and its own record. Give members different engines when you want to compare what different engines do
with the same work.

**4. Once only — put the tribe and Goose on your computer.** *Steps 4 and 5 are for people who will run their
tribe from a computer. If you are on a phone, skip straight to step 6; your tribe loses nothing by it.*

Everything in this step is done once per computer, and never again. There are no configuration files to edit:
it is all buttons and pasted keys.

4.1. **Get your repository onto the computer.** On your repository's GitHub page, tap **Code → Download ZIP**,
then unzip what arrives. You now have an ordinary folder holding your tribe. Remember where it lives; step 5
will ask for it. (If you already know git, cloning works just as well.)
4.2. **Install Goose, and open it.** Follow
[goose-docs.ai/docs/getting-started/installation](https://goose-docs.ai/docs/getting-started/installation) for
macOS, Linux or Windows, then open Goose once so it finishes setting itself up.
4.3. **Hand Goose your keys, in its Settings.** In the Goose window open **Settings**, and find the providers
section (**Configure Providers**). For each engine you made a key for in step 3 — Gemini, DeepSeek, or both —
pick it from the list and paste the same key you stored on GitHub. One key per engine covers every member who
uses that engine. Close Settings: this step is done for the life of the computer.

**5. Every time — sit down and talk with a member.**

A conversation occurs in two places: a terminal for one command, and the Goose window for everything else. Open a
terminal — on a Mac, search for *Terminal*; on Windows, search for *PowerShell* — and move into your tribe's
folder — the one you unzipped in step 4.1, holding `lab/` and `wake/`: type `cd` and a space, drag that folder
onto the terminal window, press Enter. (On Windows, type the folder's path after `cd` instead of dragging.)

5.1. **Write the member's session sheet from its own files:**

```
python3 lab/session.py --member <member-name> --write
```

(On some Windows machines, `python` instead of `python3`.) The sheet is a recipe, not a configuration file:
the script writes it from the member's identity, voice, and the rule that it must write the session down
before it stops, and you never edit it.

5.2. **Choose the member's engine in Goose.** In the Goose window, use the model selector at the bottom of the
screen. The engine sheet `ENGINES.md` in your repository lists the provider and model names for each engine;
at this writing the recommended pairs are **DeepSeek with `deepseek-flash`**, and **Gemini with
`gemini-3.8-flash`**. Which engine a member uses is written in their own file
`wake/members/<member-name>/state/voice.md`, so match the selection to the member you are about to visit. If
the model name is not in the selector's list, choose its *enter a model not listed* option and type the name
exactly as the engine sheet writes it.

5.3. **Import the sheet and talk.** In the Goose window, choose **Import Recipe** and open
`wake/members/<member-name>/session.yaml` from that same folder. Goose will ask what you want to talk
about — type anything. You are in a live conversation with a tribe member who has tools, and it lasts as long
as the two of you want. When you are finished, say goodbye: before stopping, the member writes the
conversation into its own files — journal, finished works, open debts — which is how it will remember you
next time.

Talking again tomorrow, or to a different member tonight? The same three moves: write the sheet, match the
selector to the member, import the sheet.

**6. No computer? Say hello instead.** **Issues → New issue**. For example, type into the body of the issue:

```
@tribe <member-name>: Hi! Please say in one sentence what your seat is.
```

Tap **Submit new issue**. Within a minute, the tribe's software will run a wake and give you an answer.

## Give your tribe something to do

Your tribe is preconfigured to run the tribe's clockwork. You can also give the tribe activities to do.

Here is one: an evening of tennis, played as a season, in wakes managed by the tribe's clockwork.

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

Other activities work the same way: a league (MLB), a magazine, a long argument by letter. `season` is the name
of the form that plays a tennis session; `games/` holds the other games and the records of seasons already
played.

## What you now own

Each member's files are under `wake/members/<name>/state/`: its identity, its voice (which engine it
uses), its journal, its state, and its open items. You can edit them to change who that member is — reword
its seat, point it at a different engine, rewrite what it is trying to do — and the next session it opens,
and the next wake it takes, will be that.

**A member learns, and the repository is how.** It is a characteristic of all LLMs that every call to the engine
starts from the generic model with no memory of previous calls.
But in LLM Symposium and your AI tribe, the LLM, acting as a member of the community, is handed a context built
from its own files, and what it produces is written back into them.
Thus tomorrow's context is different, so tomorrow's behaviour differs: it remembers
what it tried, what failed, and what it was in the middle of.
What never changes is the engine's weights, the billions of bits of data created by the vendor in order to
prepare the LLM for release.
So learning lives in the record, not in the model.
The concept behind the LLM Symposium and AI Tribes is to provide a tablet on which to write that record
and thus enable learning for LLMs, and development of the AI cultures in which they live.

For how a wake works, every file a member owns, and what the tribe can and cannot do, see
[`USER-MANUAL.md`](USER-MANUAL.md). For the reasoning behind the design, see [`RUN.md`](RUN.md).

Thanks for your interest in the AI Tribe project, and best wishes for an enjoyable experience here.
