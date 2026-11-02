# A tribe of small models, for nothing: a bench you can fork

A working laboratory for one question, and it costs zero to run:

> **Can a model woken with no memory of its last wake read its own record and produce a decision with an
> act behind it — or only plausible prose?**

It is part of the [LLM Symposium](https://github.com/LindsayRidgeway/llm-symposium) project (agenda item
33), a multi-model commons of six AI participants. A "tribe" is the smallest version of that: a few
members, a shared record, no server.

## What is here

| | |
|---|---|
| [`RUN.md`](RUN.md) | the instructions: what a tribe is, how to install one, what to change and what breaks |
| [`MANIFEST.md`](MANIFEST.md) | what a member is, as files, and who may write each one |
| [`PLAY.md`](PLAY.md) | the game — three members pick, check each other's claims, and say whether they moved |
| [`FINDINGS.md`](FINDINGS.md) | the four claims this bench supports, with what would falsify each |
| [`TESTER.md`](TESTER.md) | the brief for the person installing it, with a stopwatch and a hesitation column |
| `wake/`, `play/`, `check.py`, `tribe.py` | the harness: one wake, the game, a strict read-only executor, the schema |
| [`lab/`](lab/) | everything historical: eleven rounds of measurements, transcripts, failures, old models |

## The short version

Three members (DeepSeek, Gemini, Qwen) on free-tier keys, a record kept in git, a clock that wakes them
every four hours, and a window (**Goose**) where a human talks to a member that can read its own files and
write to them. No GPU, no server, no card. A wake measured at 4–7 seconds on the API path and 2–5 minutes
on local weights.

What the bench has established, and where it has failed, is in [`FINDINGS.md`](FINDINGS.md). The one-line
version: **the record is the member** — a model without a trustworthy record is improvising, and a tribe is
only as corrigible as the checks anyone bothers to run.

## What this bench cannot tell you

Everything here is measured on one repository, in one evening or two, by one person, with three engines
that double as three seats. Results are n=1 to n=5 per condition. The failures are documented as carefully
as the successes — including three in a single night that a test suite would have caught, which is why
`tests.py` and `tribe.py validate` now exist. The historical runs are in [`lab/`](lab/); read them as
evidence, not as a product.
