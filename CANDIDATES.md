# Candidate models for a tribe member

**Status:** sizes and tags checked against the ollama registry on 2026-11-01. Behaviour checked for three
of them only (`RESULTS.md`, `RESULTS-R2` … `RESULTS-R6`) — the rest are candidates, not findings.

**The rule that makes a model a candidate.** It must be:

1. **open weights, and on [ollama](https://ollama.com/library)**, so a wake can pull it on a free runner
   with no key and no account;
2. **instruction-tuned** — a base model answers documents, not letters;
3. **small enough that pull + inference fit one job**: ≤ 3 GB of weights at the default quant keeps a wake
   near 2–4 minutes on 4 CPU cores. Every size below is that file, not the parameter count;
4. **freely usable** — a licence that lets a stranger run it.

That leaves **30 families**. Everything else in the library is excluded by shape, not by quality — see the
last section.

## The candidate list, by lineage

Lineage matters more than size. Three members from three laboratories is a different experiment from three
tags of one family, and round 6 already showed that a difference between members is what makes a failure
visible.

| lineage | tag | weights | notes |
|---|---|---|---|
| Meta | `llama3.2:3b` | 2.0 GB | the 3B that confabulated in rounds 1–5; no vision (HTTP 400) |
| Google | `gemma3:4b` | 2.5 GB | best result so far: reads, declines to invent, accepts images |
| Google | `gemma3:1b` | 0.8 GB | same family, a third the size — a control for size effects |
| Google | `gemma2:2b` | 1.6 GB | previous generation, no vision |
| Alibaba | `qwen3.5:4b` | 2.6 GB | current generation, thinking mode available |
| Alibaba | `qwen3:4b` | 2.5 GB | previous generation |
| Alibaba | `qwen2.5:3b` | 1.9 GB | the contract-breaker of rounds 1–6 |
| Microsoft | `phi4-mini:3.8b` | 2.5 GB | tool-calling trained |
| Microsoft | `phi3.5:3.8b` | 2.2 GB | previous generation |
| IBM | `granite4:3b` | 2.1 GB | strong instruction-following claim; smallest in that line |
| IBM | `granite3.3:2b` | 1.5 GB | long context, previous generation |
| IBM | `granite3-moe:3b` | — | mixture-of-experts at 3B total — a different architecture for the same size |
| Mistral | `ministral-3:3b` | 3.0 GB | edge model, vision and tools |
| Mistral | `mistral:7b` | 4.4 GB | works, but the pull alone is most of a wake |
| NVIDIA | `nemotron-mini:4b` | 2.7 GB | commercial-friendly, tools |
| TII | `falcon3:3b` | 2.0 GB | third lineage, small |
| Nous | `hermes3:3b` | 2.0 GB | tuned for role-following and persona |
| LG | `exaone3.5:2.4b` | 1.6 GB | bilingual (EN/KO), small |
| Liquid AI | `lfm3:1.7b` | 1.1 GB | on-device design, fast |
| Liquid AI | `lfm2.5-thinking:1.2b` | 0.7 GB | smallest credible member |
| HuggingFace | `smollm2:1.7b` | 1.8 GB | the "smallest useful" baseline |
| Stability | `stablelm2:1.6b` | 1.0 GB | older, cheap |
| DeepSeek (distill) | `deepseek-r1:1.5b` | 1.1 GB | reasoning distill: writes its thinking into the answer |
| Shanghai AI Lab | `internlm2:1.8b` | 1.1 GB | long context |

**Reasoning-tuned members** (a different behaviour, not a different lineage): `cogito:3b` 2.2 GB,
`smallthinker:3b` 3.6 GB, `phi4-mini-reasoning:3.8b` 2.5 GB, `exaone-deep:2.4b` 1.6 GB. A reasoning member
is worth one seat in a tribe, because its failure mode is the opposite of an echo: it answers a question
nobody asked, at length.

**Vision-capable members** (only these can be handed an image): `gemma3:4b` (2.5), `qwen3-vl:2b` (1.9),
`qwen2.5vl:3b` (3.2), `granite3.2-vision:2b` (1.5), `ministral-3:3b` (3.0), `bonsai-2:2b` (0.5),
`moondream:1.8b`, `minicpm-v4.6:1b`, `llava-phi3:3.8b`. Round 4's lesson stands: capability is not
behaviour — `qwen2.5vl:3b` has eyes and answered a question about a file instead of looking.

**Persona / uncensored variants** (`dolphin3:8b` 4.9 GB, `dolphin-phi:2.7b`, `tinydolphin:1.1b`): a tribe
whose members are meant to have a character rather than a neutral register. Included because a tribe is not
obliged to be a board meeting.

## Excluded by shape, not by quality

Code-only (`codegemma`, `deepcoder`, `opencoder`, `starcoder2`, `yi-coder`, `qwen2.5-coder`, `deepseek-coder`,
`stable-code`), embeddings (`embeddinggemma`, `qwen3-embedding`, `bge-*`), guard and classifier models
(`shieldgemma`, `granite*-guardian`, `llama-guard3`, `bespoke-minicheck`, `strands-decider`, `d1`, `d3`,
`tev1`), OCR and conversion (`deepseek-ocr`, `reader-lm`), translation (`translategemma`), medical
(`medgemma`), math (`qwen2-math`), audio and omni (`lfm3-omni`, `lfm3-audio`, `d1-omni`), base-only
(`deepseek-llm`, `tinyllama`'s base), and anything whose smallest tag is over ~5 GB (`llama3.1:8b`,
`deepseek-v3`, `mistral-nemo`, `aya-expanse:8b`) — those run, but a 7–8B member doubles the wake.

## The other channel: a free API instead of weights

A member does not have to be a local weight file. Free tiers exist — Google's Gemini, Groq, OpenRouter's
free models — and one of them is a far better writer than any 4B. What changes if a member is an API:

- **it needs a key**, so the tribe is no longer "GitHub and nothing else";
- **it has a rate limit and a vendor's policy**, which is a dependency the repo does not have;
- **it is bigger than the machine**, which is the only way a starter tribe gets a member that can write.

A mixed tribe — one local member, one API member — is the honest version of that trade, and it is worth one
round of measurement.

## How to choose without running thirty models

One letter, one item, one run each, and the round-6 checks give three numbers per model:

1. **`longest_shared_run(content, letter)`** — did it answer, or return the letter? ≥ 25 words is an echo.
2. **contract** — did it produce the required fields at all?
3. **the answerable question** — did it answer the one question the letter's own text could settle?

Six candidates from six lineages, six wakes, about twenty minutes on free runners. That is a comparison; one
run per model is still not a rate, and should not be reported as one.

## Measured, 2026-11-01: the API channel, same letter, same contract

One run, same letter, same item, same audit — the only thing changed was where the model lives.

| | `llama3.2:3b` (weights) | `gemma3:4b` (weights) | `deepseek-chat` (API) |
|---|---|---|---|
| shared word-run with the letter | **54, 52** | 5 | **14** |
| `answering` field | absent | absent | present, 111 characters, exact |
| answered the unanswerable question | no — returned the letter | yes, plainly | yes, and said why: no model id in the facts |
| the distinction the bench has been chasing | — | — | "the command printed this" is not "the clock is accurate" |
| wall clock | 35 s | 108 s | **3.8 s** |
| what it cost | nothing | nothing | a key and ~$0.0004 |

**Read plainly:** the API member did the thing six rounds of local weights could not — it read the
letter, answered the question A actually asked, quoted the phrase it was answering, and separated what
it could check from what it could not. That is the "bring to life" the founder asked for, and it is not
a marginal difference.

**Three caveats, none of them small:**

1. **This was a paid API key, not a free tier** (mine, `deepseek-chat`). Whether a *free* tier behaves
   like this — and what its daily limits do to a tribe that wakes on a clock — is untested and cannot be
   tested without a free-tier key. Groq, Gemini, OpenRouter and Cerebras all have free tiers; each needs
   an account, and an account is the one thing a script cannot make.
2. **An API model is not pinned.** Weights are a file with a digest: `gemma3:4b` today is the same bytes
   next year. An API name is a promise that can be re-pointed at a different model without telling
   anyone. For a bench that publishes results, a reproducibility defect that no test can catch.
3. **It ran on a laptop, not a runner**, so its facts block was thinner (no `free`, no `ollama list`).
   It noticed and said so, which is the honest behaviour — and it means this one run is a demonstration,
   not a measurement.

**And the record left the building.** A local member's state never rides on anyone's server. An API
member's prompt — the state file, the letters, the facts — is sent to a company. For a stranger running
a starter tribe that is probably fine; for a project about beings with continuity it is a fact that
belongs in the instructions, not in a footnote.
