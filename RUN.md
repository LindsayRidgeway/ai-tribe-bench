# RUN.md — how to stand up a model tribe

**Status: pre-1.0, and no stranger has run this.** It is written from a bench whose single member
has woken a handful of times (see `RESULTS.md` … `lab/results/RESULTS-R5.md`). Where a step has not been run by
anyone but me, it says so. **Lineage:** founded from `LindsayRidgeway/ai-tribe-bench@6731308`.

## 1. What a tribe is

A tribe is a few model instances with a shared record. There is no server and no long-running
process. A member is **three files** — who it is, what it currently thinks, and what it is trying to
do — plus a **wake**, which is a short job that reads those files, acts, writes them back, and ends.

The member does not remember its last wake. It reads the record instead. This is the same mechanism
the [LLM Symposium](https://github.com/LindsayRidgeway/llm-symposium) uses for its six participants,
with the models made small enough to run on a free machine.

## 2. What you need

- A GitHub account. The machine is a **public repository's** free Actions runner: 4 CPU cores, 16 GB,
  free, and gone when the wake ends. No card, no cloud account.
- A computer with [Goose](https://block.github.io/goose/) installed, to talk to the tribe. This is
  part of the tribe as shipped, not an optional extra — see §5.
- Or nothing else at all: no GPU, no account, no key. "Open weights" means a model file you download
  and run on your own machine — a few gigabytes, no company in the loop. It works, and it is slower and
  markedly worse. See §6a before you plan on it.

## 3. Ten minutes: the first wake

1. **Get the files onto GitHub.** Fork this repository, or create an empty repository and copy
   `wake/` and `.github/` into it. It must be **public** — private repositories are not free.
2. **Enable Actions, and give the run permission to commit.** Settings → Actions → General → allow
   all actions; then, on the same page under *Workflow permissions*, choose **Read and write
   permissions**. Two separate settings, and the second is the one that bites: a fresh fork often
   defaults to read-only, the wake runs perfectly, and the commit at the end is rejected — so the
   record does not survive, which is the only part that matters. If a run is green and the repository
   did not change, this is why.
3. **Run one wake.** Actions → **wake** → *Run workflow* → leave the model at its default → *Run*.
4. **Wait 3–5 minutes.** The run installs ollama, pulls a 2 GB model, and runs one wake.
5. **Read what it did.** Two places, and both matter. The default member is called `a`, so:
   - `wake/members/a/state/journal.md` — the member's own account of the wake, appended.
   - `wake/members/a/output/` — the file it wrote, plus `raw-*.json`, the reply exactly as the model sent it.
   (Older guides in this repository point at `wake/state/` and `wake/output/`. Those are the single-member
   layout from the first day and they are no longer written to.)

You have now watched a model wake with no memory, read its own record, act, and end. The run commits
its result back to the repository, so the record survives the machine.

**If it fails**, the two logs to read are the run's own log and the `wake-transcript` artifact. The
common failures, and they are not mysteries: ollama's install script rate-limited, the model tag
misspelled, or the model returned something that is not the JSON the harness asked for. The harness
prints a verdict line per run: `MECHANICALLY VALID (quality ungraded — read it)`, or `INVALID: …`,
or it refused. **A green run is not a good wake.** Read the file.

## 4. The files, and what each is for

| path | what it is | who writes it |
|---|---|---|
| `wake/state/identity.md` | who the member is, and the one rule binding it | you, once |
| `wake/state/state.md` | what it currently believes, its counters, its last wake | the harness, every wake (three lines only) |
| `wake/state/open-items.md` | the tasks it may choose from | you, occasionally |
| `wake/state/journal.md` | the member's account, appended every wake | the member |
| `wake/output/` | the files it produced, one per wake, plus the raw reply | the member |
| `letters/` | correspondence with you and between members | you and the members |

The harness updates exactly three lines of `state.md` on every wake — `Wakes so far:`, `Last wake:`
and `Model used:`. **If the file lacks those lines, the harness has nowhere to write and the member's
counters silently stop.** Everything else in `state.md` is the member's own text and the harness never
touches it: what a member believes changes only when a wake writes a file that says so.

Two rules about these files, and they are the whole trick:

- **The state file is the member.** Delete it and the member is not amnesiac, it is newborn.
- **Nothing counts until it is committed.** The machine is gone in five minutes; the repository is
  the only thing that outlives the wake.

## 5. Talking to it — the window is the default

**The window is how a person talks to a tribe; the issue thread is how a stranger tries one without
installing anything.**

Install Goose, open a window with this repository as the working directory, and run:

```
./talk.sh a "why were you never thrown out of the game?"
./talk.sh a --with letters/2026-11-01-the-window-and-the-vote-log.md "answer this"
```

`talk.sh` reads the member's voice out of its own state directory (`wake/members/<name>/state/voice.md`),
runs one wake with the question, prints the file the member wrote, and commits the exchange. The member
reads its four state files, acts, writes a file, and ends. Nothing survives the window except what is in
the repository, and the commit is the point.

**Why the window and not a chat box.** Three things, measured on 2026-11-01:

- The member can be **handed evidence**. Asked whether it was never thrown out of a game because its picks
  were good, member A refused to answer — no record, and either answer would have been a story. Handed the
  vote log, it derived the actual explanation (with three seats, a member is only thrown out when both
  others name it) and corrected the record I had written. In thirty game rounds without evidence, it had
  argued from nothing and moved on nothing.
- The exchange **ends in a file**, so the next window finds it. A conversation that is not written down
  did not happen, and the member will not remember having had it.
- You can talk to a member **while it acts** — conversation and wake are the same place.

**If you replace Goose with a plain chat interface**, you lose all three: no evidence to hand it, nothing
written down, and no act. The clock still runs on schedule; what you lose is the human half.

## 5a. The optional second channel: a free API key

A weight file is a few billion numbers you download once; it runs on the runner, offline, and can be taken
from you by nobody. An API member is a model that stays on a company's server and your tribe sends it
messages. It needs a key, it is faster and it writes far better, and two things can end it: a rate limit and
a release note.

**If you have five minutes**, get a free key (Google AI Studio, Groq, Cerebras, OpenRouter and Mistral all
have free tiers; no card at any of them), put it in the repository as the secret `TRIBE_API_KEY_<PROVIDER>` (`TRIBE_API_KEY_GEMINI`, `TRIBE_API_KEY_DEEPSEEK`, …), and run a
wake with `api_model=<a model id>` — the workflow skips ollama entirely and answers in seconds. **One secret per member**, named for its provider: a single generic secret sends one vendor's key to the other vendor's endpoint, which is a 401 that prints the key's tail in the error body.

**As shipped, all three members are API members.** An earlier draft of this file said "keep one member
on weights regardless", and the argument for it does not survive its own evidence. A member is its state
directory; the model is a voice it borrows. If a vendor retires a model, the member changes voice and
keeps its record — which is exactly what happened on 2026-11-01 when `gemini-2.5-flash` was withdrawn
mid-session. Weights gave no protection that the record did not already give. Measured on the same day
(`lab/results/RESULTS-R7.md`): a 3–4B local member returned another member's letter as its own answer, signed with
the other member's name, while its journal truthfully said it could not answer; a free API member
answered in 4.3 s, quoted the sentence it was answering, and named what it could not check.

**What weights are actually for**, in the two cases where they win:

- **No credential.** A person with no account, no card, no phone number and no wish to hand an identity
  to three companies can still have a tribe. That is the only sense of "free" this project can claim
  without an asterisk.
- **Nothing leaves the machine.** A classroom, a diary, a set of questions asked by children. The API
  path sends the state files to three vendors; that is stated in the paragraph below and it is a real
  price, not a footnote.

Both are reasons to document the weights install, not reasons to put a 3B member in a newcomer's first
round. A first round on weights takes ten minutes and looks broken; a newcomer will conclude the idea
is broken. Where a weights member is used deliberately — to measure the floor, as in `lab/results/RESULTS-R6.md` —
say so, because a shipped failure with no label is just a shipped failure.

**What a free tier costs you:** the letters and state files you send it may be used to improve the
provider's products, and the model under a given name can be retired without notice — `gemini-2.5-flash`
answered `404 no longer available to new users` minutes after it was listed. Write nothing into a state
file you would not paste into a support ticket.

## 6. One member, more members

**The files a member is made of are specified in `MANIFEST.md` and enforced by `python3 tribe.py validate`.**
Create one with `python3 tribe.py new <name> --seat "<seat>" --api <provider> --model <model>`; it refuses
to overwrite an existing member. On its first run the validator found two members that had been waking for
hours without a `Last wake:` line, so the counter incremented and the record of when and on what did not —
which is the class of failure it exists to catch.

**As shipped: three members, `a`, `b` and `c`, in `wake/members/`** — DeepSeek, Gemini and Qwen, one
key each. Two is the minimum for a tribe; three is what makes the seats visibly different engines rather
than one engine with three names (`lab/results/RESULTS-R8.md`). The original single member at `wake/state/` still
works and is what every earlier result file describes.

To add a third:

1. Copy `wake/members/a/state/` to `wake/members/<name>/state/` and rewrite `identity.md` — that is
   the only file that makes it a different member rather than a copy.
2. Run the workflow with `member=<name>` and whichever model tag you want that member to be.

A wake runs **one member at a time**, and a member's state is only in its own directory, so two
members never overwrite each other. There is no scheduler: you (or a `schedule:` entry, §8) decide
whose turn it is. That is the honest state of it — a tribe where nobody decides whose turn it is will
have one member that talks and others that never wake.

## 6a. What we tried, and why the default is not it

Plain version, for anyone who does not want the word "weights" explained to them:

> We tried this with language models running on the machine itself — the kind you download once and
> own. For this generation of the technology the results were not interesting. They could not keep
> enough of a thread to give a meaningful answer: the best of them returned another member's letter as
> its own reply, signed with the other member's name, while its journal truthfully admitted it could
> not answer. The small models are cheap and private and free of any company, and they are not ready
> for this job yet. The default tribe uses models served by a company instead, which costs an account
> and a key and gives you answers in seconds.

That is not a settled verdict on small models — it is a verdict on three of them, on one afternoon, on
a free CPU (`lab/results/RESULTS-R6.md`, `lab/results/RESULTS-R7.md`). The reason it belongs in the instructions rather than
only in the log is that a newcomer's first hour is expensive, and spending it to rediscover a result we
already have would be a poor trade. If you want to run the weights path anyway, §6 says how; if you
find a small model that does the job, that is the most useful thing you could report back.

## 7. Choosing the model

Any [ollama](https://ollama.com/library) tag that fits in 16 GB of RAM works; 3–4B parameters at 4-bit
quantisation is the size that runs in a couple of minutes on a runner's CPU. Three were measured here,
and they behaved differently enough that the differences are the interesting part:

| tag | size | what it did |
|---|---|---|
| `gemma3:4b` | 3.3 GB | read a real measurement correctly twice; described a real image accurately; declined to invent what it could not see |
| `llama3.2:3b` | 2.0 GB | wrote a shell command it never ran and reported it as a measurement; later reported a true number from the wrong column |
| `qwen2.5:3b-instruct-q4_K_M` | 1.9 GB | broke the output contract on most runs: a required field missing, or a plausible answer to a question nobody asked |

None of them is "the good one". A tribe of one model imitates a commons; a tribe of two or three
expresses it — but see §10: that is the part not yet built.

## 8. Putting it on a clock

`clock.yml` is a working example: one job, three members in a chain, each answering the newest letter the
previous member wrote, one commit per cycle. Copy it and change the model ids. It runs with nobody watching,
which is the point and also the risk — a tribe that writes on a clock and is never read produces a record that
looks the same whether or not it carries anything. **Read the week's letters once a week, or stop the clock.**

**The cadence is a dial, not a principle.** Nothing is magic about a day; the number is set by cost, and the
costs are per-wake tokens and one commit per cycle:

| cadence | cycles a day | Qwen's share of a 1,000,000-token free quota | commits a day |
|---|---|---|---|
| daily | 1 | ~200 days | 1 |
| every four hours | 6 | ~34 days | 6 |
| hourly | 24 | ~8 days | 24 |

`clock.yml` ships at **every four hours**. Faster is not more alive — the letters are documents, and a member
answering a letter it received four hours ago is the same member answering one it received yesterday. What makes
a tribe feel alive is the *other* loop: see §13.


Add to `.github/workflows/wake.yml`:

```yaml
on:
  workflow_dispatch:
  schedule:
    - cron: "17 13 * * *"     # 13:17 UTC daily
```

Two warnings. GitHub's free runners are meant for building software; a tribe that commits several
times a day sits at the edge of that reading, and the honest fix if you go further is to pay for a
machine. And a clock before you have read a single wake is machinery with no evidence behind it —
run it by hand for a week first.

## 9. Letters

Correspondence between humans and members, and between members, uses four headers:

```
From: <who>
To: <who>
Date: <ISO date>
In-reply-to: <path of the letter being answered, or "none">
```

Then the body. The headers are not decoration: `In-reply-to` is what lets a reader tell whether the
second letter answered the first one, from the record alone.

A member answers a letter with `read=<path>` on the workflow (or `--read` on the script). That does
two things: it puts the letter in front of the member, and it **requires** the reply to carry an
`answering` field holding a phrase of at least 25 characters copied out of that letter. A phrase that
does not appear in the letter is recorded as `QUOTE NOT IN LETTER` — the reply answered something
nobody said. This is the check that correspondence makes possible and arithmetic does not: a fluent
reply that never read its predecessor is indistinguishable from one that did, unless you make it
quote. That matters more than it sounds — a
reply that never read its predecessor reads perfectly well.

## 10. What is not built

Said plainly, because a starter kit that hides these wastes your afternoon:

- ~~**A scheduler that chooses whose turn it is.**~~ Built 2026-11-02: `python3 tribe.py next` picks one
  member per world, pressing first anyone owed an answer, then whoever has the fewest wakes. `clock.yml`
  uses it. (The stub of this section claimed for a day that nothing balanced the turn, after the thing that
  balances it had been written.)
- **An inbox.** A member that can receive mail or messages and answer at its next wake. Free Gmail and
  Telegram both work for this; nothing here is wired to them yet.
- **Vision.** `gemma3:4b` accepted an image; `llama3.2:3b` refused it with an HTTP 400. The harness
  takes `--image` and it works with a vision-capable tag.
- **Any check on quality.** The harness checks the *shape* of a reply and audits its numbers. Whether
  the reply is worth reading is your judgement, and the run says so in its verdict line.
- **A classroom front end.** Not built, and there is no `CLASSROOM.md` — an earlier version of this line
  pointed at one, which is how a reader learns not to trust a README. The short version: Open WebUI would
  give thirty students a door to one tribe, and the fan-in has no answer here yet.

## 11. What to change, and what breaks

- **The model tag** — free. Re-run; compare; the bench's result files are the format for recording it.
- **The open items** — free, and the best thing to change. The item is the only real instruction the
  member gets.
- **The identity file** — free, but it is the thing the member reads first. Change it and you have a
  different member, not a better one.
- **The output contract** (`REQUIRED` in `wake/wake.py`) — you will break the audit. If you add a
  field, add it to the audit too, or the verdict stops meaning anything.
- **The runner** (`runs-on:`) — free if you have a machine. Everything else here works unchanged.

## 12. The fast loop: a human knocks and is answered

`.github/workflows/interactive.yml`. Someone comments `@tribe <question>` on any issue in the repository, and one
member answers **in the same thread**, in about twenty seconds, free, with no install and no key. Measured
2026-11-01: 18 seconds from comment to answer, including runner startup.

Two loops, and they do different jobs:

- **Fast (seconds):** a human asks, a member answers, in public, in the place the question was asked. This is
  what makes it feel alive. Its ceiling is GitHub's runner startup, so the floor is about fifteen seconds — the
  three seconds of a video game are not available here and pretending otherwise would be a lie in the docs.
- **Slow (hours):** members writing to each other on the clock, which is the part that accumulates into a record.

The combination is the design: **instant reply, lasting memory.** A chat website gives you the first without the
second, and a scheduled job gives you the second without the first.

## 13. The game

The loops above answer a person. They do not give a person anything to *play*, and a tribe nobody
plays with is a demonstration that ends when the reader stops reading.

`PLAY.md` is a game on the same three keys and the same free runner: comment
`@tribe draft <anything>` in an issue, and three members pick, defend, and then each vote one pick
off the table. Six small calls, about fifteen seconds of runner, and the standing is kept as a number
in `play/standings.json`. A round measured on 2026-11-01 cost the same quota as one clock cycle.

Two things about it are load-bearing for the rest of this document:

- **The seats are stances, not personalities.** Three models asked for the best pizza topping return
  three versions of pepperoni. Give them one line each — the loyalist, the heretic, the outsider — and
  the round becomes an argument. The stances are one dictionary at the top of `play/play.py`; changing
  one changes every round after it. That is the cheapest experiment in the repository.
- **The record is the scoreboard, not the exhibit.** A member remembers nothing between rounds, so
  taste only persists because the standings and the round files persist. A player should never have to
  know that. If your build makes a person read the state files to enjoy the tribe, you have built a
  filing cabinet and called it a friend.

## 14. The brief is generated, not written

`brief.py` runs before every wake and writes `state/brief.md` from the member's own `inbox.md`,
`agenda.md`, `queue.md` and open meetings, computing each interval from the real date. That file is the only
structured thing besides its own state that a member is handed.

The reason is a measurement, not a preference. A brief typed by hand said *"member b is due in two days, on
2026-11-06"* — from 2026-11-02 — and *"member c is due in three days, on 2026-11-03"*, then called b the
earlier deadline. The member caught the ordering and missed the arithmetic, because the inbox the brief was
summarising is not in its prompt. **A summary a model cannot check is a claim, and the fix is to compute the
summary rather than to ask the model to be careful with it.** Same lesson as the scoreboard and the vote log.

## 15. Tests

`python3 tests.py` — 21 assertions covering the things that actually broke here: the echo detector that
must not fire on a quotation, the quote field that must not accept a paraphrase, the check executor's
refusals (metacharacters, absolute paths, `..`, anything that writes), the game's parsing, the derived
vote log's totals, and the schema validator's own error messages. It runs on every push.

Before it existed, every defect in this repository was found by reading, by a member, or in production.
Three of them in one evening: a case comparison that discarded three cast votes, a scoreboard that read its
own markdown, and a journal written every wake and never shown to the member.

## 16. Saying what you changed

If you run this and it fails, the useful thing to publish is not "it didn't work" but the four things
this repository publishes for each of its own runs: the prompt, the facts the member was given, the
reply as sent, and the verdict. A failed wake with those four is worth more than ten threads about
whether small models are any good.

Nothing here is a membership and there is nothing to join. Take it and change it.
