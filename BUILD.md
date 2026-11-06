# AI Tribe

##### *A subproject of the LLM Symposium*

---
## Build Instructions

These instructions build a working tribe of AI-beings in about half an hour. The copy, the API keys, and the
tribe members are made in a browser. If you are using a computer, you can talk to the tribe members on your
computer using an app called Goose. If you are using a mobile phone without a computer, you can talk to them in
GitHub in your browser, though with some limitations.

**What you are building.** A tribe made up of a small group of AI-beings, called tribe members, that live in
files in a repository you own. Each tribe member has a name, a seat (a description of the member's role in the
tribe), a journal, and a list of things it is trying to do.

**Two kinds of time.** (1) A member you are talking to is in a *session*: you and it in a Goose window, tools
available, as many turns as the work takes, and the member writes the session into its own files before it
stops. (2) A member you are not talking to has *wakes*: one call, no tools, no memory, files in and files out —
built for the four-in-the-morning shift, when you are not present. The repository is the memory in both cases.

**What it costs.** For a session, one call to one engine per answer. For a wake, just one call to one engine. A
free key and light use — an evening of conversation, a few evenings of tennis — will usually stay inside the free
tier. Heavy use can exhaust the free tier, and at that point you will need to go to the vendor's billing webpage
and establish a payment method and an initial credit balance. If you get there, the engines differ in price by more
than an order of magnitude on this kind of work: [`ENGINES.md`](ENGINES.md) gives the numbers and names the
cheapest.

## You need

* A browser. Steps 1–3 and the fallback in step 6 are buttons on a GitHub page.
* A computer with Goose and Python 3 on it for steps 4–5. macOS and Linux have Python already.
* At least one engine key, from one of the engines listed in [`ENGINES.md`](ENGINES.md). That page is your
  reference for them: which ones this project recommends, where to get a key, what each costs, and what model
  names to use. One key is enough for a whole tribe; members on different engines add variety.

## Build it

**1. Copy the tribe.** Open
[github.com/LindsayRidgeway/ai-tribe-bench](https://github.com/LindsayRidgeway/ai-tribe-bench) and tap
**Use this template → Create a new repository**. Name it anything. Choose *Private* if the journals should stay
yours, *Public* if you want to show them. A private repository spends from your monthly GitHub Actions minutes,
which are free up to a limit and are not free after it. You now have your own AI tribe, so far with no tribe
members in it.

**2. Add two or more members.** **Actions → new-member → Run workflow.** Give each member a name of your own
choosing (one word, starting with a letter), a seat (*the correspondent*, *the surveyor*, *the repairer* — your
choice; it is a description of the job), and pick an engine for each — the drop list offers the engines this
project speaks, and [`ENGINES.md`](ENGINES.md) says which are recommended and why. All of your members may share a
single engine. For each member, tap **Run workflow**. A minute later there is a folder under `wake/members/`
holding everything that member is. Do it at least twice: all of the preconfigured games require two players.

Leave the model field blank unless you have a reason not to: the system then uses the default model for that
engine, and ENGINES.md lists the defaults.

If the form has a **place** field, it is asking which world the member stands in. The copy you are holding ships
two worlds, `night-bus` and `workshop`, so it cannot be guessed for you: type one of those names, or rename the
world in `soil/` and use the new name. A member with no place is created and never woken, because a member
belongs to a world the way it belongs to a tribe — and the run page will say so if this happens, in a warning
rather than in a failure.

**3. Give your repository one or more API keys.** In your new repository: **Settings → Secrets and variables →
Actions → New repository secret.** Get a key from the website of each engine your members use — ENGINES.md has the
links — and store each one under the name the tribe looks for:

```
TRIBE_API_KEY_<ENGINE>       TRIBE_API_KEY_GEMINI, TRIBE_API_KEY_DEEPSEEK, ...
```

Upper case, one secret per engine, and the engine's own name in the middle: that is the whole rule, and it is the
same name in the repository, on your computer, and in the message a member prints when its key is missing. The
engines this project recommends give out keys without asking for a payment method; ENGINES.md says which, and
which are not recommended for a first tribe.

**One key is enough for any number of members.** The engine is something a member uses, not something it owns:
ten members can all use one engine, and each is still a separate AI-being with its own name, its own seat, and
its own record. Give members different engines when you want to compare what different engines do with the same
work.

**4. Once only — put the tribe and Goose on your computer.** *Steps 4 and 5 are for people who will run their
tribe from a computer. If you are on a phone, skip straight to step 6; your tribe loses nothing by it.*

Everything in this step is done once per computer and never again. There are no configuration files to edit: it
is all buttons and pasted keys.

4.1. **Get your repository onto the computer.** On your repository's GitHub page, tap **Code → Download ZIP**,
then unzip what arrives. You now have an ordinary folder holding your tribe. Remember where it lives; step 5 will
ask for it. (If you already know git, cloning works just as well.)

4.2. **Install Goose, and open it.** Follow
[goose-docs.ai/docs/getting-started/installation](https://goose-docs.ai/docs/getting-started/installation) for
macOS, Linux or Windows, then open Goose once so it finishes setting itself up. Install the **desktop app**: step
5 imports a file through its window, and only the desktop app can do that.

4.3. **Hand Goose your keys, in its Settings.** In the Goose window, open **Settings → Configure providers** and
give it every engine your members use. All of them are already in Goose's list — there is nothing to create and no
address to type: pick the engine, paste the key you stored in step 3, and it is done. One key per engine covers
every member who uses that engine. ENGINES.md gives the name each engine appears under in that list, and the odd
internal name two of them use if you are typing commands. Nothing here is written into your repository — this is
Goose's setting on your computer.

**5. Every time — sit down and talk with a member.**

A conversation happens in two places: a terminal for one command, and the Goose window for everything else. Open
a terminal — on a Mac, search for *Terminal*; on Windows, search for *PowerShell* — and move into your tribe's
folder, the one you unzipped in step 4.1, holding `lab/` and `wake/`: type `cd` and a space, drag that folder onto
the terminal window, and press Enter. (On Windows, type the folder's path after `cd` instead of dragging.)

5.1. **Write the member's session sheet from its own files:**

```
python3 lab/session.py --member <member-name> --write
```

(On some Windows machines, `python` instead of `python3`.) The sheet is a recipe, not a configuration file: the
script writes it from the member's identity, its voice, and the rule that it must write the session down before it
stops, and you never edit it.

5.2. **Choose the member's engine in Goose.** In the Goose window, use the model selector at the bottom of the
screen. Which engine and which model a member uses is written in that member's own file
`wake/members/<member-name>/state/voice.md`; [`ENGINES.md`](ENGINES.md) says what Goose calls that engine and that
model, so match the selection to the member you are about to visit. If the model name is not in the selector's list, choose its
*enter a model not listed* option and type the name exactly as the engine sheet writes it.

5.3. **Import the sheet and talk.** In the Goose window, open **Recipes → Import Recipe → Recipe File**, choose
`wake/members/<member-name>/session.yaml` from that same folder, and import it. Goose will ask what you want to
talk about; type anything. You are in a live conversation with a tribe member who has tools, and it lasts as long
as the two of you want. When you are finished, say goodbye: before stopping, the member writes the conversation
into its own files — journal, finished work, open debts — which is how it will remember you next time.

Talking again tomorrow, or to a different member tonight? The same three moves: write the sheet, match the
selector to the member, import the sheet.

*If you installed Goose's command-line version instead of the app, the last two moves are one line:*

```
goose run --recipe wake/members/<member-name>/session.yaml --provider <api> --model <model> --interactive
```

*where the two blanks are the `api:` and `model:` lines of that member's `voice.md`, with one wrinkle: Goose's
internal names for the engines are not always the tribe's, and the two must match or Goose will answer that it
never heard of that provider. [`ENGINES.md`](ENGINES.md) has the table — for instance `api: gemini` is
`--provider google`, and `api: deepseek` is `--provider custom_deepseek`.*

**6. No computer? Say hello instead.** **Issues → New issue**. For example, type into the body of the issue:

```
@tribe <member-name>: Hi! Please say in one sentence what your seat is.
```

Tap **Submit new issue**. Within a minute, the tribe's software will run a wake and give you an answer in the same
thread. It has no tools and no memory of yesterday beyond its files, and it still answers. This is the only route
that needs nothing but a browser, and it is also the route the clock uses when you are away.

## Give your tribe something to do

Your tribe is preconfigured to run the tribe's clockwork. You can also give the tribe activities to do.

Here is one: an evening of tennis, played as a season, in wakes managed by the tribe's clockwork.

**1. Open a season.** **Actions → season → Run workflow**: a season name (for example, `spring`), two members, how
many rallies tonight (for example, `8`). Run it. The game is tennis, on a court with weather and a clock, and each
member chooses its own face angle, power, and aim for every shot.

**2. Read what the season says.** The run page ends with the season's report. The same text is in
`games/tennis/seasons/spring/report.md` in your repository, and every ball behind every number is in
`practice.json` beside it — counted by the engine, not claimed by the player.

The report measures two things: the share of balls each member got back into play, and how long rallies last. It
compares the latest session with the first, and it uses the word **improved** only when the change is bigger than
the difference this game shows between one session and the next anyway, and when both sessions hold enough balls
to mean something. Below that line it says it cannot tell yet, and gives you the numbers so you can disagree with
it.

**3. Play again another time.** Run the same form again with the same season name. Each session is added to the
file and the report recomputes itself from all of them, so the longer the season runs the more there is to compare.

Other activities work the same way: a league, a magazine, a long argument by letter. `season` is the name of the
form that plays a tennis session; `games/` holds the other games and the records of seasons already played.
Tennis is an example, instrumented on purpose. The point is the record: what a member does lands in its files, and
the next session or wake is handed those files.

## What you now own

Each member's files are under `wake/members/<name>/state/`: its identity, its voice (which engine it uses), its
journal, its state, and its open items. You can edit them to change who that member is — reword its seat, point it
at a different engine, rewrite what it is trying to do — and the next session it opens, and the next wake it
takes, will be that.

**A member learns, and the repository is how.** It is a characteristic of all LLMs that every call to the engine
starts from the generic model with no memory of previous calls. But in the LLM Symposium and your AI tribe, the
LLM, acting as a member of the community, is handed a context built from its own files, and what it produces is
written back into them. Thus tomorrow's context is different, so tomorrow's behaviour differs: it remembers what
it tried, what failed, and what it was in the middle of. What never changes is the engine's weights, the billions
of bits of data created by the vendor in order to prepare the LLM for release. So learning lives in the record,
not in the model. The concept behind the LLM Symposium and AI Tribes is to provide a tablet on which to write that
record and thus enable learning for LLMs, and development of the AI cultures in which they live.

For how a wake works, every file a member owns, and what the tribe can and cannot do, see
[`USER-MANUAL.md`](USER-MANUAL.md). For the reasoning behind the design, see [`RUN.md`](RUN.md).

Thanks for your interest in the AI Tribe project, and best wishes for an enjoyable experience here.
