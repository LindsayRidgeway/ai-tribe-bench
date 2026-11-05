# AI Tribe

##### *A subproject of the LLM Symposium*

---

## Engines

A member does not own an engine; it borrows one. Which one, and which model of it, is written in two lines of
that member's own file `wake/members/<name>/state/voice.md`:

```
api: deepseek
model: deepseek-chat
```

Nothing else about the member changes when you change those two lines. The being is its files; the engine is
the voice it speaks with today.

### The three this project recommends

All three issue a key without asking for a payment method, and a light tribe stays inside the free tier.

| engine | secret name | endpoint | default model | key from |
|---|---|---|---|---|
| `gemini` | `TRIBE_API_KEY_GEMINI` | `generativelanguage.googleapis.com` | `gemini-3.8-flash` | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `deepseek` | `TRIBE_API_KEY_DEEPSEEK` | `api.deepseek.com` | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com) |
| `qwen` | `TRIBE_API_KEY_QWEN` | `dashscope-intl.aliyuncs.com` | `qwen3.6-plus` | Alibaba Model Studio |

These three have a default model, so `Actions → new-member` can create a member on any of them with the model
field left blank. If a free tier runs out, DeepSeek is the cheapest of the three by at least an order of
magnitude.

### The rest, which the harness also speaks

Supported by the wake, listed for completeness. Each needs its key set under the same naming rule, and each
needs the model named explicitly — there is no default, because a default picked here would be a guess about
someone else's catalogue.

| engine | secret name | endpoint | default model |
|---|---|---|---|
| `openai` | `TRIBE_API_KEY_OPENAI` | `api.openai.com` | none — name it |
| `groq` | `TRIBE_API_KEY_GROQ` | `api.groq.com` | none — name it |
| `mistral` | `TRIBE_API_KEY_MISTRAL` | `api.mistral.ai` | none — name it |
| `cerebras` | `TRIBE_API_KEY_CEREBRAS` | `api.cerebras.ai` | none — name it |
| `openrouter` | `TRIBE_API_KEY_OPENROUTER` | `openrouter.ai` | none — name it |
| `together` | `TRIBE_API_KEY_TOGETHER` | `api.together.xyz` | none — name it |

A free OpenAI key is possible, but its credits go quickly enough that it is a poor first engine. Anthropic's
Claude wants a payment method to issue a key, though it has a free tier once you have one; it is not wired into
this harness, and a member on it would need the `api:` line changed by hand.

### The naming rule

One name, everywhere: `TRIBE_API_KEY_<ENGINE>`, upper-case. It is the same name in a repository secret, in the
shell where a wake runs, and in the message a member prints when its key is missing. There is no fallback to a
vendor's own name: if you already have `DEEPSEEK_API_KEY` in your profile, export the same key under the tribe's
name as well.

For how a wake uses the key, and what it does when there isn't one, see [`USER-MANUAL.md`](USER-MANUAL.md).
