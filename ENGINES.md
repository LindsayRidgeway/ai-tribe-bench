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

Nothing else about the member changes when you change those two lines. The being is its files; the engine is the
voice it speaks with today.[^1]

There are four tables: the engines this page recommends, the engines that work here and are not recommended, the
engines the harness speaks that nobody here has yet called, and the names Goose uses for all of them. The reasoning
is in nineteen notes at the end, numbered so you can read the ones that interest you and skip the rest.[^2]

### The three engines this page recommends

| engine | secret name[^3] | model[^4] | price, per million tokens | key from |
|---|---|---|---|---|
| `gemini` | `TRIBE_API_KEY_GEMINI` | `gemini-3.8-flash` | **free** on the free tier; $0.75 in / $3.75 out on the paid tier until 2026-12-31, then double | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — no card |
| `deepseek` | `TRIBE_API_KEY_DEEPSEEK` | `deepseek-flash`[^5][^6] | **$0.15 in / $0.60 out**; **$0.003** on cached input | [platform.deepseek.com](https://platform.deepseek.com) |
| `groq` | `TRIBE_API_KEY_GROQ` | `openai/gpt-oss-120b`[^7][^8][^9] | **$0.15 in / $0.60 out**; no cache-hit rate published | [console.groq.com/keys](https://console.groq.com/keys) — free tier, no card |

*What earns a place here* is three things a stranger can check: a key you can obtain in a few minutes without
handing over a card, a default model this project names and tests, and a member that actually wakes on it. Where
those prices and free tiers come from is note 10.[^10] The build instructions use the first two, because two is
enough to build a tribe and every extra engine is another key to keep.[^11]

### Other possibilities

| engine | secret name | address | price, per million tokens[^10] | what it asks of you first |
|---|---|---|---|---|
| `qwen` | `TRIBE_API_KEY_QWEN` | `dashscope-intl.aliyuncs.com` | not printed here: Alibaba's own sheet has not been read | an evening: signup, region and console work[^12] |
| `openai` | `TRIBE_API_KEY_OPENAI` | `api.openai.com` | **$0.05 in / $0.25 out** (`gpt-6-luna`); $0.50 / $2.50 (`gpt-6.1-terra`); $5.00 / $30.00 (`chat-latest`) | a card[^13] |
| `anthropic` | `TRIBE_API_KEY_ANTHROPIC` | `api.anthropic.com` | **$0.10 in / $0.50 out** (`claude-haiku-5-5`, prompts under 100k); $2 / $10 (`claude-sonnet-5-5`); $4 / $20 (`claude-opus-5-5`) | prepaid credits bought with a card[^14] |

All three work here. None of them is recommended, and the reason is the door, not the engine and not the
bill.[^15]

### The rest, which the harness also speaks

| engine | secret name | address |
|---|---|---|
| `mistral` | `TRIBE_API_KEY_MISTRAL` | `api.mistral.ai` |
| `cerebras` | `TRIBE_API_KEY_CEREBRAS` | `api.cerebras.ai` |
| `openrouter` | `TRIBE_API_KEY_OPENROUTER` | `openrouter.ai` |
| `together` | `TRIBE_API_KEY_TOGETHER` | `api.together.xyz` |

Supported by the wake, unmeasured here: no key has been spent on any of them, so this page names no default model
and promises nothing.[^16]

### On your own machine

The harness can also run weights on your own machine rather than call an API. That needs no key, no card and no
account, which makes it the only option on this page a stranger can try without asking anyone's permission. What
has been measured about whether it is any good is note 17.[^17]

### What Goose calls them, if you are using a computer

| the member's `api:` line | in Goose's list | what you type after `--provider` |
|---|---|---|
| `gemini` | **Gemini** | `google` |
| `deepseek` | **DeepSeek** | `custom_deepseek` |
| `qwen` | **Alibaba (Qwen)** | `alibaba` |
| `groq` | **Groq** | `groq` |
| `openai` | **OpenAI** | `openai` |
| `anthropic` | **Anthropic** | `anthropic` |

Every engine on this page is already in Goose's provider list — there is no provider to add by hand, in Goose 1.57
or since. Two of the internal names are odd and neither is our doing.[^18] Paste the key into Goose's Settings and
you are done: the list, the keys and the model selector do not care what a provider is called internally.[^19]

### Notes

[^1]: **What this page means by an engine.** The door a member knocks on: a vendor with an address, a key, and
    model names it will answer to. Who trained the weights is a separate fact, and often a different company —
    Groq trains nothing and runs other people's open-weight models on its own silicon; OpenRouter runs none of its
    own either. A member cannot tell the difference and does not care: what it needs is something at the other end
    of the address that reads a long instruction and answers. That is why a chip company and a model house appear
    in the same table here, and why the word is "engine" and not "model".

[^2]: **How to read the rest of this page.** Nothing below is required to build a tribe. Each note stands alone,
    and the tables above are complete without them: an address, a secret name, a model, a price, and what the door
    asks. Read the ones that touch a decision you are about to make — the vendor you pick, the money you might
    spend, or the machine it runs on.

[^3]: **Secret name.** The repository secret that holds this vendor's key, in **Settings → Secrets and variables →
    Actions**. One name everywhere: `TRIBE_API_KEY_<ENGINE>`, upper-case, the same in a repository secret, in the
    shell where a wake runs, and in the message a member prints when its key is missing. There is no fallback to a
    vendor's own spelling: if you already have `DEEPSEEK_API_KEY` in your profile, export the same key under the
    tribe's name as well. A wake that finds no `TRIBE_API_KEY_<ENGINE>` says so by name rather than failing
    quietly on an empty string. For how a wake uses the key, and what it does when there isn't one, see
    [`USER-MANUAL.md`](USER-MANUAL.md).

[^4]: **Model.** The name of one model in that vendor's catalogue, exactly as the vendor writes it. Every vendor
    publishes several and treats one as its default; this project names a tested default for five vendors — the
    three recommended here and the two paid engines below — and for the rest you name the model yourself and it is
    recorded in the member's `voice.md`. The harness will not guess at another vendor's catalogue: a guess that is
    wrong fails on that member's first wake and looks like a problem with the tribe rather than with a model name.

[^5]: **DeepSeek's model name changes under you.** The id this project shipped with was `deepseek-chat`; on
    2026-11-05 DeepSeek's own catalogue answered with two ids, `deepseek-flash` and `deepseek-v4-pro`, and
    `deepseek-flash` is the one that reads images as well as text. A member written on a retired id fails on its
    first wake with a message about a missing model, which is why the default here is `deepseek-flash` and why
    `voice.md` — not this page — is the authority for any member that already exists.

[^6]: **DeepSeek is a thinking model at its defaults, and that starves a one-line question.** Asked for one line
    about a racquet angle it spent 600 of a 600-token allowance thinking and returned nothing, four times in six
    shots — 355 seconds for a session Groq did in four. It accepts `"thinking": {"type": "disabled"}`, after which
    the same session takes 8 seconds and answers every shot. The games send that field; the wakes do not, because a
    wake has work to do and the deliberation is the point. If you write your own harness against these engines,
    expect to meet this.

[^7]: **What Groq is, and why it is here at all.** An inference company of 2016, not a model house: it runs other
    people's open-weight models on its own chips. It is not Grok the chatbot and the name is older than it. It is
    also the only engine on this page that needs no custom provider in Goose at all. Until 2026-11-06 this page
    said it was *not* recommended, on the ground that open-weight models hold a long instruction and a strict reply
    format less reliably than the flash models of Gemini and DeepSeek. That was a guess about a vendor this project
    had never called. With a key in hand the guess was tested and it was wrong: one wake in 3.9 seconds with every
    field of the reply schema present and the named file written; one 455-word answer in 1.4 seconds of generation
    that obeyed both of its format constraints; and fifty tennis shots across six sessions with **zero** replies
    that could not be read, which the game's own record counts (`unparsed replies: 0`).

[^8]: **Groq's free tier is counted per minute, and one setting decides how much that costs you.** The headers on
    our own account read **8,000 tokens a minute and 1,000 requests**. At the vendor's defaults a six-rally session
    took 63 to 127 seconds, the limiter refusing a call every few shots and every refusal answered by waiting the
    number the vendor itself sent back — nothing was lost, every session finished, but a long unattended season
    crawls. With `reasoning_effort: "low"` the same session took **3.7 seconds and was refused zero times**,
    because the tokens were spent on the answer instead of the deliberation. The developer plan publishes
    **250,000 tokens a minute**, which a tribe will not meet; a tribe that plays games daily may want it, a tribe
    that wakes twice a day will not.

[^9]: **What thinking costs, measured on both engines the same day, and the one caution left.** The same tennis
    prompt: DeepSeek's `deepseek-flash` spent 646 reasoning tokens to produce the seven that answered, and on
    another draw 1,838 — all billed as output. `gpt-oss-120b` answered with a fraction of that, several times
    inside its first 400-token allowance. So on this workload Groq is not the expensive one, and the tribe's own
    arithmetic — many short questions over a long shared prefix — is why the page still names DeepSeek first for
    wakes: on a repeated prefix DeepSeek bills input at **$0.003 per million** and Groq publishes no such rate.
    The caution is not about reliability: Groq trains nothing, so its model ids are other houses' names and they
    change hands. `deepseek-chat` was retired out from under this project once; `openai/gpt-oss-120b` can be too.
    The repair is one line in one `voice.md` — but it will happen.

[^10]: **Where these prices came from.** Read off the vendors' own price sheets on 2026-11-06, each on the page
    linked from that vendor's row, rather than remembered. Three things they do not say: a free tier is not the
    same offer twice — Gemini's free tier is free because Google may use the prompts to improve its products, while
    DeepSeek and Groq's free tiers are rate limits rather than a data trade; prices move, and Gemini's already
    carry a scheduled doubling on 2027-01-01; and a cached input token is the only price that matters for this
    workload, because a wake re-sends a large unchanged prefix every time. Anthropic publishes the same shape of
    rate — `claude-haiku-5-5` at **$0.01 per million** on a cache hit, an order below its $0.10 list — which is
    worth knowing before anyone repeats the folklore that only the cheap engines cache.

[^11]: **Why the build instructions use two engines and not three.** Two is enough to build a tribe, and every
    extra engine is another key to keep, another line in a settings screen, and another thing that can be wrong
    when a first wake fails. Members may share one engine or be spread across all three; nothing in the harness
    assumes one engine per tribe.

[^12]: **Qwen is fine and the door is heavy.** Obtaining a usable Alibaba key took this project an evening of
    signup, region and console work. A recommendation is a promise about the first thirty minutes, and this page
    cannot make that promise for Alibaba. If you already have the key — the founder does, having paid that evening
    — a member on `qwen3.6-plus` wakes, plays and files like any other.

[^13]: **OpenAI works here, and its cheapest model is the cheapest thing on this page.** It speaks the shape this
    harness already speaks, so it needed no adapter, and it still refused three things in a row, each refusal
    naming the field: `max_tokens` on models that want `max_completion_tokens` (and the reverse on older ones), a
    `temperature` of 0.4 on a model that supports only the default, and `response_format: json_object` on a model
    that demands the word "json" appear in the messages. The harness now reads the complaint, changes that one
    field and retries. The first live wake then came back truncated at 2,400 tokens — 2,400 tokens of reasoning
    and no answer, which was our defect and not the member's; the wake now triples the allowance to 20,000 when a
    reply is cut off. The default is `gpt-6-luna`, which woke in 6.8 seconds and played eight readable throws.
    `gpt-5-mini` was the first OpenAI model this project ever called and still answers, but it has dropped off the
    vendor's published price sheet — which is the `deepseek-chat` failure one day early, and the reason the default
    moved.

[^14]: **Claude works here now, and what it took was code, not money.** Until 2026-11-06 this page said Claude did
    not work here at all, and that was true: the wake and every game send `messages` to `/chat/completions`, while
    Claude answers at `/v1/messages` with a different auth header, a required `max_tokens`, and a reply made of
    content blocks. The adapter was written in both places the morning the founder produced a key — `wake/wake.py`
    and `lab/rps.py` each build their own request, so a translation that lives in one of them is a member that can
    wake and cannot play. It is no longer a guess about documentation: a wake on `claude-haiku-5-5` came back
    **mechanically valid**, four rounds of the game ran on it, and the one thing the first live call taught that
    the docs had not is that `temperature` is now deprecated on the newest models — the wake reads that refusal
    and repeats the request without the field. The door: credits bought in advance with a card, non-refundable,
    expiring after a year, no free tier.

[^15]: **Why the last two are not recommended, and it is not the bill.** At the bottom of their ranges both are
    cheaper than anything above: `claude-haiku-5-5` at $0.10 in is a fifth of Groq's input price, and `gpt-6-luna`
    at $0.05 is cheaper still — so a reader who already pays one of these vendors should put a member on their
    cheapest model and will spend less than one on DeepSeek. At the top of the ranges the older sentence still
    holds and this page keeps it: those models cost ten to fifty times what any engine above costs. Either way,
    what keeps these two out is the checkout page. A stranger with a card will find them perfectly good. This page
    will not send a stranger without one there first.

[^16]: **What "supported by the wake" means, and what it does not.** The harness speaks each of these addresses —
    it is the same OpenAI-shaped request as Groq and DeepSeek — and nothing else has been established. Nobody here
    has spent a key on them, so there is no measured wake, no tested model id, and no price line this page is
    willing to print. To use one you name the model yourself when you make the member; if the name is wrong the
    member fails on its first wake and says so. Two of these vendors are worth a look on their own terms —
    Cerebras for speed on the same open-weight models Groq serves, OpenRouter for reaching many vendors through
    one key — and one is worth a caution, because a router means your record's prompts pass through a party that
    is neither you nor the model's author.

[^17]: **Local weights, which need no key and have not been ruled out.** The wake can run a model on the machine
    instead of calling an API (`wake.py --model`, `--host`), and three small open-weight models have been measured
    here — `llama3.2:3b`, `gemma3:4b`, `qwen2.5vl:3b` — on a free cloud runner's CPU, in rounds 1–7 of
    [`lab/results/`](lab/results/). On that evidence they are not correspondents: `llama3.2:3b` copied 52 to 54
    consecutive words of the letter it was answering and signed itself with the other member's name; `qwen2.5:3b`
    omitted a required field in four runs out of four and answered an item that did not exist; `gemma3:4b` wrote a
    real reply but left out one of the four things the item asked for; and `llama3.2:3b` cannot be handed an image
    at all, which the vendor answers with HTTP 400 rather than a refusal. **What that establishes is narrow**: a
    3B model on a CPU is not a correspondent. It says nothing about a 14B or 30B model on Apple silicon, because
    no model has ever been run on this project's own laptop — the M4 Pro here has 24 GB and no ollama installed.
    A tribe that wants no keys at all should test that first rather than trust either the failure above or the
    enthusiasm of a model card.

[^18]: **Two of Goose's internal names are odd, and the difference is the whole trap.** Gemini is `google`, and
    DeepSeek is `custom_deepseek`. Both were checked by running Goose rather than by reading its menus: `--provider
    custom_deepseek` starts a session, and `--provider deepseek` answers `Unknown provider: deepseek`, which is
    Goose's way of saying that a provider's *display* name and its internal name are different strings. Alibaba's
    engine is the same story one degree worse: it appears as **Alibaba (Qwen)** and answers to `alibaba`.

[^19]: **Where each engine lives, if you want to check this page against the vendor's documentation.**
    `generativelanguage.googleapis.com` (Gemini), `api.deepseek.com` (DeepSeek), `dashscope-intl.aliyuncs.com`
    (Qwen), `api.groq.com` (Groq), `api.openai.com`, `api.anthropic.com`. Engineers call this an *endpoint*, and an
    earlier version of this page assumed that word was understood. It is not; it means the address.
