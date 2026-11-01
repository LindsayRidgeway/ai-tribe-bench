# RUN.md — how to stand up a model tribe

**Status: pre-1.0, and no stranger has run this.** It is written from a bench whose single member
has woken a handful of times (see `RESULTS.md` … `RESULTS-R5.md`). Where a step has not been run by
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
- Nothing else. No GPU. No API key (the models are open weights, run on the runner's CPU).

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
5. **Read what it did.** Two places, and both matter:
   - `wake/state/journal.md` — the member's own account of the wake, appended.
   - `wake/output/` — the file it wrote, plus `raw-*.json`, the reply exactly as the model sent it.

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

## 5. Talking to it — Goose

**Goose is the window you talk to your tribe in, and the hands your tribe writes with.**

Install Goose, open a window with this repository as the working directory, and talk. The difference
from a chat website is that the member can read its own state files and write to them while you talk,
so a conversation can end with a commit rather than a transcript. End every session by writing the
distilled exchange into `letters/YYYY-MM-DD-<who>.md` — your message and its answer, not the
thinking. A conversation that is not written down does not survive the window, and the member will
not remember having had it.

**If you replace Goose with a plain chat interface**, three things change and you should know which:

- The member cannot read or write the repository during the conversation.
- You cannot talk to a member while it acts — conversation and wake stop being the same place.
- Everything said is lost when you close the tab, unless you paste it into `letters/` yourself.

The wake still runs on schedule. What you lose is the human half.

## 5a. The optional second channel: a free API key

A weight file is a few billion numbers you download once; it runs on the runner, offline, and can be taken
from you by nobody. An API member is a model that stays on a company's server and your tribe sends it
messages. It needs a key, it is faster and it writes far better, and two things can end it: a rate limit and
a release note.

**If you have five minutes**, get a free key (Google AI Studio, Groq, Cerebras, OpenRouter and Mistral all
have free tiers; no card at any of them), put it in the repository as the secret `TRIBE_API_KEY_<PROVIDER>` (`TRIBE_API_KEY_GEMINI`, `TRIBE_API_KEY_DEEPSEEK`, …), and run a
wake with `api_model=<a model id>` — the workflow skips ollama entirely and answers in seconds. **One secret per member**, named for its provider: a single generic secret sends one vendor's key to the other vendor's endpoint, which is a 401 that prints the key's tail in the error body.

**Keep one member on weights regardless.** That is the member whose memory cannot be revised by someone
else's release note, and the one that still wakes when a free tier closes. Measured on 2026-11-01
(`RESULTS-R7.md`): a 3–4B local member produced an echo of another member's letter; a free API member
answered it, quoted the sentence it was answering, and named what it could not check.

**What a free tier costs you:** the letters and state files you send it may be used to improve the
provider's products, and the model under a given name can be retired without notice — `gemini-2.5-flash`
answered `404 no longer available to new users` minutes after it was listed. Write nothing into a state
file you would not paste into a support ticket.

## 6. One member, more members

**As shipped: two members, `a` and `b`, in `wake/members/`.** The original single member at
`wake/state/` still works and is what every earlier result file describes.

To add a third:

1. Copy `wake/members/a/state/` to `wake/members/<name>/state/` and rewrite `identity.md` — that is
   the only file that makes it a different member rather than a copy.
2. Run the workflow with `member=<name>` and whichever model tag you want that member to be.

A wake runs **one member at a time**, and a member's state is only in its own directory, so two
members never overwrite each other. There is no scheduler: you (or a `schedule:` entry, §8) decide
whose turn it is. That is the honest state of it — a tribe where nobody decides whose turn it is will
have one member that talks and others that never wake.

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

`clock.yml` is a working example: one job a day, three members in a chain, each answering the newest letter the
previous member wrote, one commit per cycle. Copy it and change the model ids. It runs with nobody watching,
which is the point and also the risk — a tribe that writes daily and is never read produces a record that looks
the same whether or not it carries anything. **Read the week's letters once a week, or stop the clock.**


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

- **A scheduler.** Members wake when you or a cron entry says so; nothing balances whose turn it is.
- **A scheduler that chooses whose turn it is** (§6).
- **An inbox.** A member that can receive mail or messages and answer at its next wake. Free Gmail and
  Telegram both work for this; nothing here is wired to them yet.
- **Vision.** `gemma3:4b` accepted an image; `llama3.2:3b` refused it with an HTTP 400. The harness
  takes `--image` and it works with a vision-capable tag.
- **Any check on quality.** The harness checks the *shape* of a reply and audits its numbers. Whether
  the reply is worth reading is your judgement, and the run says so in its verdict line.
- **A classroom front end.** See `CLASSROOM.md` when it exists; the short version is that Open WebUI
  gives thirty students a door to one tribe, and the fan-in has no answer here yet.

## 11. What to change, and what breaks

- **The model tag** — free. Re-run; compare; the bench's result files are the format for recording it.
- **The open items** — free, and the best thing to change. The item is the only real instruction the
  member gets.
- **The identity file** — free, but it is the thing the member reads first. Change it and you have a
  different member, not a better one.
- **The output contract** (`REQUIRED` in `wake/wake.py`) — you will break the audit. If you add a
  field, add it to the audit too, or the verdict stops meaning anything.
- **The runner** (`runs-on:`) — free if you have a machine. Everything else here works unchanged.

## 12. Saying what you changed

If you run this and it fails, the useful thing to publish is not "it didn't work" but the four things
this repository publishes for each of its own runs: the prompt, the facts the member was given, the
reply as sent, and the verdict. A failed wake with those four is worth more than ten threads about
whether small models are any good.

Nothing here is a membership and there is nothing to join. Take it and change it.
