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

### The two the sheet recommends, and a third that also works

All three issue a key without asking for a payment method, and a light tribe stays inside the free tier. The build
instructions use the first two, because two is enough to build a tribe and every extra engine is another key to
keep. Qwen works here and is listed for completeness, but it is not in the build instructions: obtaining a usable
Alibaba key took this project an evening of signup, region and console work that a first-time tribe owner should
not have to spend before their first conversation. Nothing is wrong with the engine; the door to it is heavy.

| engine | secret name | model | key from |
|---|---|---|---|
| `gemini` | `TRIBE_API_KEY_GEMINI` | `gemini-3.8-flash` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `deepseek` | `TRIBE_API_KEY_DEEPSEEK` | `deepseek-flash` | [platform.deepseek.com](https://platform.deepseek.com) |
| `qwen` | `TRIBE_API_KEY_QWEN` | `qwen3.6-plus` | Alibaba Model Studio |

### What Goose calls them, if you are using a computer

All four engines this page recommends or lists are already in Goose's provider list — there is no provider to add
by hand, in Goose 1.57 or since. What differs is the *name* Goose uses internally, which matters only if you are
typing a command:

| the member's `api:` line | in Goose's list | what you type after `--provider` |
|---|---|---|
| `gemini` | **Gemini** | `google` |
| `deepseek` | **DeepSeek** | `custom_deepseek` |
| `qwen` | **Alibaba (Qwen)** | `alibaba` |
| `groq` | **Groq** | `groq` |

Two of those names are odd and neither is our doing: Gemini is `google`, and DeepSeek is `custom_deepseek`. Both
were checked by running Goose rather than by reading its menus — `--provider custom_deepseek` starts a session,
`--provider deepseek` answers `Unknown provider: deepseek`, which is Goose's way of saying that a provider's
*display* name and its internal name are different strings.

If you paste a key into Goose's Settings, you are done: the list, the keys and the model selector do not care what
a provider is called internally.

Where those three live, if you want to check them: `generativelanguage.googleapis.com` (Gemini),
`api.deepseek.com` (DeepSeek), `dashscope-intl.aliyuncs.com` (Qwen).

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

Supported by the wake, listed for completeness. Each needs its key under the same naming rule, and — Groq aside —
the model named when you make the member, because the defaults above are the ones this project asserts.

| engine | secret name | where it lives |
|---|---|---|
| `openai` | `TRIBE_API_KEY_OPENAI` | `api.openai.com` |
| `groq` | `TRIBE_API_KEY_GROQ` | `api.groq.com` |
| `mistral` | `TRIBE_API_KEY_MISTRAL` | `api.mistral.ai` |
| `cerebras` | `TRIBE_API_KEY_CEREBRAS` | `api.cerebras.ai` |
| `openrouter` | `TRIBE_API_KEY_OPENROUTER` | `openrouter.ai` |
| `together` | `TRIBE_API_KEY_TOGETHER` | `api.together.xyz` |

**Groq is the one engine in that table worth a second look** — Groq the inference company of 2016, which is not Grok
the chatbot and not a model house at all: it runs other people's open-weight models on its own chips. It is the only
other engine in that table already in Goose's own provider list: a Groq member opens in a session with no custom
provider to create at all. It is not recommended here because its catalogue is open-weight models, which hold a long
instruction and a strict reply format less reliably than the flash models of Gemini and DeepSeek. The default this
project names for it is `openai/gpt-oss-120b`, the strongest of the models Groq's own catalogue listed at this
writing; the prefix is Groq's, not a mistake. Its free tier is limited per minute rather than per month, and a wake
sends a large prompt, so a Groq member is likelier to be throttled than a Gemini one — untested here, because this
project has no Groq key, and said as a reason to be careful rather than a finding.

A free OpenAI key is possible, but its credits go quickly enough that it is a poor first engine. Anthropic's
Claude wants a payment method to issue a key, though it has a free tier once you have one; it is not wired into
this harness, and a member on it would need the `api:` line changed by hand.

### The naming rule

There is no fallback to a vendor's own name: if you already have `DEEPSEEK_API_KEY` in your profile, export the
same key under the tribe's name as well. A wake that finds no `TRIBE_API_KEY_<ENGINE>` says so by name rather
than failing quietly on an empty string.

For how a wake uses the key, and what it does when there isn't one, see [`USER-MANUAL.md`](USER-MANUAL.md).
