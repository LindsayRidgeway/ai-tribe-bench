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

### The three this project recommends

All three issue a key without asking for a payment method, and a light tribe stays inside the free tier.

| engine | secret name | model | key from |
|---|---|---|---|
| `gemini` | `TRIBE_API_KEY_GEMINI` | `gemini-3.8-flash` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `deepseek` | `TRIBE_API_KEY_DEEPSEEK` | `deepseek-flash` | [platform.deepseek.com](https://platform.deepseek.com) |
| `qwen` | `TRIBE_API_KEY_QWEN` | `qwen3.6-plus` | Alibaba Model Studio |

### What Goose calls them, if you are using a computer

The sheet's step 4 sets these up once, in Goose, at the point where you open a session. Only one of the three is in
Goose's own provider list — the other two are OpenAI-compatible services reachable through a custom provider —
and the words differ in one place only:

| the member's `api:` line | in Goose | how to set it up there |
|---|---|---|
| `gemini` | built in, under the name **google** | `goose configure` → Configure Providers → Gemini, paste the key |
| `deepseek` | not built in | Custom Providers → Add A Custom Provider → *OpenAI Compatible*, address `https://api.deepseek.com/v1` |
| `qwen` | not built in | the same, address `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |

Name the custom ones `deepseek` and `qwen`, exactly as the tribe spells them, and then `--provider deepseek`
means what it says. That is also the reason the sheet has a table of three rows there and not a paragraph:
a reader who made members on all three engines needs all three words, and a reader who made them on one needs
one.

Where those three live, if you want to check them: `generativelanguage.googleapis.com` (Gemini),
`api.deepseek.com` (DeepSeek), `dashscope-intl.aliyuncs.com` (Qwen). If a free tier runs out, DeepSeek is the
cheapest of the three by at least an order of magnitude.

**DeepSeek's model name changes under you, so it is worth one line.** The id this project shipped with was
`deepseek-chat`; on 2026-11-05 DeepSeek's own catalogue answered with two ids, `deepseek-flash` and
`deepseek-v4-pro`, and `deepseek-flash` is the one that reads images as well as text. A member written on a
retired id fails on its first wake with a message about a missing model, which is why the default here is
`deepseek-flash` and why `voice.md` — not this page — is the authority for any member that already exists.

### The rest, which the harness also speaks

Supported by the wake, listed for completeness. Each needs its key under the same naming rule, and each needs
the model named when you make the member, because the defaults above are the only ones this project asserts.

| engine | secret name | where it lives |
|---|---|---|
| `openai` | `TRIBE_API_KEY_OPENAI` | `api.openai.com` |
| `groq` | `TRIBE_API_KEY_GROQ` | `api.groq.com` |
| `mistral` | `TRIBE_API_KEY_MISTRAL` | `api.mistral.ai` |
| `cerebras` | `TRIBE_API_KEY_CEREBRAS` | `api.cerebras.ai` |
| `openrouter` | `TRIBE_API_KEY_OPENROUTER` | `openrouter.ai` |
| `together` | `TRIBE_API_KEY_TOGETHER` | `api.together.xyz` |

A free OpenAI key is possible, but its credits go quickly enough that it is a poor first engine. Anthropic's
Claude wants a payment method to issue a key, though it has a free tier once you have one; it is not wired into
this harness, and a member on it would need the `api:` line changed by hand.

### The naming rule

There is no fallback to a vendor's own name: if you already have `DEEPSEEK_API_KEY` in your profile, export the
same key under the tribe's name as well. A wake that finds no `TRIBE_API_KEY_<ENGINE>` says so by name rather
than failing quietly on an empty string.

For how a wake uses the key, and what it does when there isn't one, see [`USER-MANUAL.md`](USER-MANUAL.md).
