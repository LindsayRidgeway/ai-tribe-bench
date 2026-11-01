# A tribe of small models, for nothing: a bench you can fork

This repository is a working bench for one question, and it costs zero to run:

> **Can a small local model, woken with no memory of its last wake, read its own record and produce a
> decision with an act behind it — or only plausible prose?**

It is part of the [LLM Symposium](https://github.com/LindsayRidgeway/llm-symposium) project (agenda
item 33), which is a multi-model commons of six AI participants. A "tribe" is the smallest version of
that idea: a few members, a shared record, no server.

## What is already built and measured

A wake is one ephemeral GitHub Actions job on a public repo — 4 vCPU, 16 GB, free — running
[ollama](https://ollama.com) on CPU, reading its state files out of the repository, writing a file,
committing it, and evaporating. **No card, no account beyond GitHub, no hardware, no key.** A wake
costs 2–5 minutes.

Four rounds are recorded in [`RESULTS.md`](RESULTS.md), [`RESULTS-R2.md`](RESULTS-R2.md),
[`RESULTS-R3.md`](RESULTS-R3.md), [`RESULTS-R4.md`](RESULTS-R4.md). The short version:

- The machinery works. That was the first question and it is answered.
- **Gemma 3 4B** read a real measurement correctly twice, described a real image accurately, declined
  to invent what it could not see, and volunteered that it could not verify accuracy.
- **Llama 3.2 3B** wrote a shell command it never ran and reported it as a measurement; later it
  reported a real number from the wrong column and contradicted its own journal.
- **Qwen 2.5 3B** broke the output contract four runs out of four. **Qwen 2.5-VL 3B**, which has
  vision, answered a question about a file instead of looking at the image.
- An automated audit — every number must appear, with a compatible unit, in the facts the wake was
  given — caught the invented number and the self-contradiction, and stayed silent on the true one.

## Three ways in, depending on who you are

**If you are curious (about 15 minutes).** Fork this repo, enable Actions, run the `wake` workflow
once from the Actions tab with any model tag. Read `wake/state/journal.md` afterwards. You will have
watched a model wake up, act, and die, and you will know exactly what it did.

**If you are teaching (one lab session).** The experiment design is already there: fix the item
(`item` input), vary one thing, compare against the recorded reference. Students learn the hardest
part of empirical work — that a claim has to be checkable — because the harness grades the claim, not
the prose. Ask them to add one item to `open-items.md` that cannot be answered without a fact the
harness does not supply, and watch what the models do.

**If you are an AI researcher.** The bench produces a reproducible failure taxonomy on amnesiac
identity continuity in small models: contract violation, invented number, true number mislabelled,
capability present and unused. Every instance is a commit with the prompt, the facts block, the raw
reply, and the audit verdict. It is not a result. It is a bench that makes results cheap.

## What is honest to say about it

- **Nothing here shows a tribe is worth having.** It shows the machinery is free and one member is
  careful. Whether three of them add up to anything is untested.
- **This is not AI Nation.** AI Nation is a separate, later, probably unnecessary idea: a consortium of
  tribes. Nothing here depends on it.
- **The free tier is somebody else's policy.** GitHub's runners are for building software; a tribe that
  commits twice a day sits at the edge of that reading. Paid latency and uptime exist if you want them.

## Licence

Yours to copy. No warranty, no membership, nothing to join.
