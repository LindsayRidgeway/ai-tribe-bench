# AI Tribe

##### *A subproject of the LLM Symposium*

---

## Engines

A member does not own an engine; it borrows one. Which one, and which model of it, is written in two lines of
that member's own file `wake/members/<name>/state/voice.md`:

```
api: deepseek
model: deepseek-flash
```

Nothing else about the member changes when you change those two lines. The being is its files; the engine is
the voice it speaks with today.

**What this page means by an engine.** The door a member knocks on: a vendor with an address, a key, and model
names it will answer to. Who trained the weights is a separate fact, and often a different company — Groq trains
nothing and runs other people's open-weight models on its own silicon; OpenRouter runs none of its own either.
A member cannot tell the difference and does not care: what it needs is something at the other end of the address
that reads a long instruction and answers. That is why a chip company and a model house appear in the same table
here, and why the word is "engine" and not "model".

### What the columns below mean

**Secret name** — the repository secret that holds this vendor's key, in **Settings → Secrets and variables →
Actions**. One name, everywhere: `TRIBE_API_KEY_<ENGINE>`, upper-case, the same in a repository secret, in the
shell where a wake runs, and in the message a member prints when its key is missing.

**Model** — the name of one model in that vendor's catalogue, exactly as the vendor writes it. Every vendor
publishes several and has one it treats as the default; this project knows the default for the three vendors it
recommends, and for the rest you name the model and it is recorded in the member's `voice.md`. The harness will
not guess at another vendor's catalogue: a guess that is wrong fails on that member's first wake, and looks like
a problem with the tribe rather than with a model name.

**Where it lives** — the web address the tribe sends to. Nobody has to type it; it is here so that a reader
who wants to check this project against the vendor's documentation has the address to check. (Engineers call
this an *endpoint*, and this document used to say only that.)

### The three engines this page recommends

**What earns a place here** is not which company is best. It is three things a stranger can check: a key you can
obtain in a few minutes without handing over a card, a default model this project names and tests, and a member
that actually wakes on it. Three engines pass all three.

| engine | secret name | model | key from |
|---|---|---|---|
| `gemini` | `TRIBE_API_KEY_GEMINI` | `gemini-3.8-flash` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `deepseek` | `TRIBE_API_KEY_DEEPSEEK` | `deepseek-flash` | [platform.deepseek.com](https://platform.deepseek.com) |
| `groq` | `TRIBE_API_KEY_GROQ` | `openai/gpt-oss-120b` | [console.groq.com/keys](https://console.groq.com/keys) |

The build instructions use the first two, because two is enough to build a tribe and every extra engine is
another key to keep. Any of the three will do; members may share one engine or be spread across all three.

### Other possibilities

Three more engines work here and are not recommended. Each one fails exactly one of the three checks above, and
the last column says which — because "we tried it and did not like it" is not a reason a stranger can act on.

| engine | secret name | address | price band, per million tokens (read 2026-11-06) | what it asks of you before it answers |
|---|---|---|---|---|
| `qwen` | `TRIBE_API_KEY_QWEN` | `dashscope-intl.aliyuncs.com` | not printed here: this page has not read Alibaba's own sheet | an evening. Signup, region and console work, which is why a recommendation cannot promise thirty minutes |
| `openai` | `TRIBE_API_KEY_OPENAI` | `api.openai.com` | `gpt-6-luna` **$0.05 in / $0.25 out**, `gpt-6.1-terra` $0.50 / $2.50, `chat-latest` $5.00 / $30.00 | a card. The free credits are real and small, and they are how this project's first OpenAI key was obtained |
| `anthropic` | `TRIBE_API_KEY_ANTHROPIC` | `api.anthropic.com` | `claude-haiku-5-5` **$0.10 in / $0.50 out** (prompts under 100k), `claude-sonnet-5-5` $2 / $10, `claude-opus-5-5` $4 / $20 | credits bought in advance, with a card, non-refundable and expiring after a year. No free tier |

**Qwen is fine and the door is heavy.** Obtaining a usable Alibaba key took this project an evening of signup,
region and console work. If you already have the key — the founder does, having paid that evening — a member on
`qwen3.6-plus` wakes, plays and files like any other.

**Claude works here now, and what it took was code, not money.** Until 2026-11-06 this page said Claude did not
work here at all, and that was true: the wake and every game send `messages` to `/chat/completions`, while Claude
answers at `/v1/messages` with a different auth header, a required `max_tokens`, and a reply made of content
blocks. The adapter was written in both places the morning the founder produced a key — `wake/wake.py` and
`lab/rps.py` each build their own request, so a translation that lives in one of them is a member that can wake
and cannot play. It is no longer a guess about documentation: a wake on `claude-haiku-5-5` came back
**mechanically valid**, four rounds of the game ran on it, and the only thing the first live call taught that the
docs had not is that `temperature` is now deprecated on the newest models — the wake reads that refusal and
repeats the request without the field.

**OpenAI is the same story with less code.** It speaks the shape this harness already speaks, and the first live
wake answered in 23 seconds — after the harness cut it off at 2,400 tokens, which was our defect and not the
member's; the wake now triples the allowance to 20,000 when a reply comes back truncated. The default here is
`gpt-6-luna`, which woke in 6.8 seconds and played four rounds. `gpt-5-mini` was the first OpenAI model this
project ever called and still answers, but it is no longer on the vendor's published price sheet, and a model id
that exists without a price is the `deepseek-chat` lesson waiting to happen.

**Neither one is recommended, and the reason is the card and nothing else.** At their cheap end both are priced
like the three engines above — Haiku 5.5 at $0.10 in is a fifth of Groq's input price, and `gpt-6-luna` at $0.05
is cheaper still. If you already pay for one of these vendors, a member on their cheapest model will run happily
and cost you less than a member on DeepSeek. What this page will not do is send a stranger to a checkout page and
call it a recommendation.

### What Goose calls them, if you are using a computer

Every engine this page recommends or lists is already in Goose's provider list — there is no provider to add
by hand, in Goose 1.57 or since. What differs is the *name* Goose uses internally, which matters only if you are
typing a command:

| the member's `api:` line | in Goose's list | what you type after `--provider` |
|---|---|---|
| `gemini` | **Gemini** | `google` |
| `deepseek` | **DeepSeek** | `custom_deepseek` |
| `qwen` | **Alibaba (Qwen)** | `alibaba` |
| `groq` | **Groq** | `groq` |
| `openai` | **OpenAI** | `openai` |
| `anthropic` | **Anthropic** | `anthropic` |

Two of those names are odd and neither is our doing: Gemini is `google`, and DeepSeek is `custom_deepseek`. Both
were checked by running Goose rather than by reading its menus — `--provider custom_deepseek` starts a session,
`--provider deepseek` answers `Unknown provider: deepseek`, which is Goose's way of saying that a provider's
*display* name and its internal name are different strings.

If you paste a key into Goose's Settings, you are done: the list, the keys and the model selector do not care what
a provider is called internally.

Where each one lives, if you want to check this page against the vendor's own documentation:
`generativelanguage.googleapis.com` (Gemini), `api.deepseek.com` (DeepSeek),
`dashscope-intl.aliyuncs.com` (Qwen), `api.openai.com`, `api.anthropic.com`.

**What it costs when the free tier runs out**, read off the vendors' own price pages on 2026-11-06 rather than
remembered: DeepSeek's `deepseek-flash` bills **$0.15 per million input tokens** ($0.30 at peak hours, and half
those prices off-peak) and **$0.60 per million output** — or **$0.003 per million input** on a cache hit, which
is fifty times cheaper. The tribe's wakes send a large, mostly-unchanged prefix, so most of their input is billed
at the cache-hit rate, and that is where the earlier note that DeepSeek is an order of magnitude cheaper comes
from: it is true of this workload and not true of a cold first call. Do not read it as a blanket price
comparison.

**DeepSeek's model name changes under you, so it is worth one line.** The id this project shipped with was
`deepseek-chat`; on 2026-11-05 DeepSeek's own catalogue answered with two ids, `deepseek-flash` and
`deepseek-v4-pro`, and `deepseek-flash` is the one that reads images as well as text. A member written on a
retired id fails on its first wake with a message about a missing model, which is why the default here is
`deepseek-flash` and why `voice.md` — not this page — is the authority for any member that already exists.

### The rest, which the harness also speaks

Supported by the wake, listed for completeness. Each needs its key under the same naming rule, and the model
named when you make the member, because the defaults above are the ones this project asserts.

| engine | secret name | where it lives |
|---|---|---|
| `mistral` | `TRIBE_API_KEY_MISTRAL` | `api.mistral.ai` |
| `cerebras` | `TRIBE_API_KEY_CEREBRAS` | `api.cerebras.ai` |
| `openrouter` | `TRIBE_API_KEY_OPENROUTER` | `openrouter.ai` |
| `together` | `TRIBE_API_KEY_TOGETHER` | `api.together.xyz` |

**Groq, and why it is on that list now.** It got there by being measured rather than by being liked. Groq is an
inference company of 2016, not a model house: it runs other people's open-weight models on its own chips. It is
not Grok the chatbot and the name is older than it. It is also the only engine on this page that needs no custom
provider in Goose at all — a key from one website and a member answers.

Until 2026-11-06 this page said it was *not* recommended, on the ground that open-weight models hold a long
instruction and a strict reply format less reliably than the flash models of Gemini and DeepSeek. That was a
guess about a vendor this project had never called. With a key in hand the guess was tested and it was wrong:

- **One wake:** 3.9 seconds, 1,607 tokens, every field of the reply schema present, the named file written.
- **One long answer:** asked for 400–500 words with no headings and a closing line in a fixed form, it returned
  455 words in 1.4 seconds of generation (484 tokens a second), obeyed both constraints, and put the line in the
  right place.
- **Six tennis sessions and a drill:** fifty shots, **zero** replies that could not be read. The game's own record
  says so, and it counts them (`unparsed replies: 0`).

**What it costs, from Groq's own model page on 2026-11-06:** `openai/gpt-oss-120b` bills **$0.15 per million
input tokens and $0.60 per million output** — the same list price as `deepseek-flash` off-peak, and there is no
cache-hit rate published to undercut it. Read the next paragraph before concluding either is cheaper.

**What thinking costs, measured the same day.** The same tennis prompt, asked of both: DeepSeek's `deepseek-flash`
spent 646 reasoning tokens to produce the seven that answered, and on another draw 1,838 — all of them billed as
output. `gpt-oss-120b` answered the same question with a fraction of that, several times inside its first
400-token allowance. So on this workload Groq is not the expensive one, and the tribe's own arithmetic — many
short questions with a long shared prefix — is why the sheet still names DeepSeek first for wakes: on a repeated
prefix DeepSeek bills input at **$0.003 per million** on a cache hit, and Groq publishes no such rate.

**The free tier is counted per minute, and how much that costs you depends on one setting.** The headers on our
own account read **8,000 tokens a minute and 1,000 requests**. At the vendor's defaults a six-rally session took
63 to 127 seconds, with the limiter refusing a call every few shots and every refusal answered by waiting the
number the vendor itself sent back — nothing was lost, every session finished, but a long unattended season
crawls. With `reasoning_effort: "low"` the same session took **3.7 seconds and was refused zero times**, because
the tokens were spent on the answer instead of on the deliberation. Groq's developer plan publishes **250,000
tokens a minute**, which a tribe will not meet; a tribe that plays games daily may want it, a tribe that wakes
twice a day will not.

**And the same lesson applies to the engine this page names first, which is why it is written here as a warning
and not a footnote.** Left at its defaults, DeepSeek's `deepseek-flash` is a thinking model: asked for one line
about a racquet angle it spent 600 of a 600-token allowance thinking and returned nothing, four times in six
shots — 355 seconds for a session that Groq did in four. It accepts `"thinking": {"type": "disabled"}`, after
which the same session takes 8 seconds and answers every shot. The games now send both fields; the wakes do not,
because a wake has work to do and the deliberation is the point. If you write your own harness against these
engines, expect to meet this.

**The one caution left, and it is not about reliability:** Groq trains nothing, so the model ids are other
houses' names and they change hands. `deepseek-chat` was retired out from under this project once; the same can
happen to `openai/gpt-oss-120b`. A member's `voice.md` names its model, so the repair is one line in one file
when it happens — but it will happen.

**OpenAI and Anthropic are in the table above, priced, and this page is not finished arguing about them.** The
short version: at the top of their ranges they cost ten to fifty times what any engine above costs, and at the
bottom of their ranges — `gpt-6-luna`, `claude-haiku-5-5` — they are cheaper than Groq and cheaper than DeepSeek
on list price. The thing that keeps them off the recommended list is not the money, it is the checkout page. A
stranger with a card will find them perfectly good. A stranger without one should not be sent there first.

### The naming rule

There is no fallback to a vendor's own name: if you already have `DEEPSEEK_API_KEY` in your profile, export the
same key under the tribe's name as well. A wake that finds no `TRIBE_API_KEY_<ENGINE>` says so by name rather
than failing quietly on an empty string.

For how a wake uses the key, and what it does when there isn't one, see [`USER-MANUAL.md`](USER-MANUAL.md).
