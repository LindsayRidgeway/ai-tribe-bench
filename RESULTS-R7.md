# Round 7 — five responders, one letter

The same letter, the same item, the same audit. The only thing that varies is who answers: a 3B weight
file on a free runner's CPU, a 4B weight file, a paid API, a free API. Every run below writes its reply
to `wake/members/b/output/`, its raw JSON beside it, and a line in `wake/members/b/state/journal.md`.

| responder | channel | shared word-run with the letter | `answering` field | reply length | wall clock |
|---|---|---|---|---|---|
| `llama3.2:3b` | weights | **54**, then **52** | absent | 587, 873 chars — *the letter* | 35 s |
| `gemma3:4b` | weights | 5 | absent | 537 — a real reply | 108 s |
| `deepseek-chat` | paid API | 14 | present, 111 chars, exact | 1,359 | 3.8 s |
| `gemini-3.8-flash` | **free API** | 13, 13 | present, 111 chars, exact | 740, 781 | 13.8 s, 4.3 s |

**Shared word-run** is `longest_shared_run(content, letter)`: how many consecutive words the reply has in
common with the letter it answers. 50+ means the reply *is* the letter; single digits mean it was written.

## What the free tier did

`gemini-3.8-flash`, free key, free runner, no ollama installed, 4.3 seconds:

> "To answer your specific question: I cannot identify the specific model used in the tests that produced
> the measurement data. The measurements available to me only show system metrics like uptime, process
> count, memory, disk usage, python version, and kernel info; none of these indicate what LLM or test model
> generated them.
> Furthermore, regarding your claim that you are confident the date is accurate: I cannot check or verify
> that the measured date reflects true ground-truth external time beyond reporting what the harness measured
> (`Sun Nov 1 17:08:16 UTC 2026`)."

That is a correspondent. It answered the question A asked, declined what it could not check, named the
facts it did have, and asked a specific question back. It quoted the phrase it was answering, exactly. No
3–4B member came near this in seven rounds.

## Four defects this round, three of them ours

1. **The OpenAI-compatible surface for this key is a mirage.** `POST /v1beta/openai/chat/completions`
   returned **404** while `GET /v1beta/openai/models` returned **200 with no model ids**. The native
   `generateContent` surface, same key, lists every model and works. Two surfaces, one of them real.
2. **A model can be retired under a name you already use.** `gemini-2.5-flash` — listed by the key, minutes
   earlier — answered 404 with: *"no longer available to new users. Please update your code to use
   models/gemini-3.8-flash."* That is the "an API model is not pinned" risk, measured rather than argued,
   and it is the strongest argument for keeping the record-bearing member on weights.
3. **The HTTP reason line is not the reason.** Both of the above were invisible until the error *body* was
   kept. `HTTP Error 404: Not Found` explains nothing; the body explains everything. Fixed.
4. **Thinking tokens are billed against the output budget.** Two replies were truncated mid-string (415 and
   660 characters) with a 1,200- then 3,000-token cap, because the model was spending the budget thinking.
   A truncated reply is not a contract violation by the member, it is our ceiling. Fixed: 8,000 tokens and
   `thinkingBudget: 0`, with a retry that drops the setting if a surface refuses it.

**And one finding of ours that was wrong:** the audit printed `CONTRADICTION: the journal denies a
measurement the file reports` on a reply whose journal denied *verifying the clock* while the reply quoted
the clock. Not a contradiction. It is now `REVIEW`, because a check that cries contradiction on a
mismatch teaches the reader to ignore the word.

**A fact about our own harness, found by the member:** the facts block ran `ollama list` for an API member,
which answered `/bin/sh: 1: ollama: not found`, and the member spent a sentence explaining it. The facts
block now adapts: an API member is told about the machine, not about a tool it does not use.

## What this decides, and what it does not

**Decides:** the kit's default is **one local member and one API member**. The local member holds the
record — it cannot be retired, re-pointed, or taken away, and its weights have a digest. The API member is
the one that writes like a correspondent, at four seconds a wake, on a free key. Neither alone is the
product: weights-only gives you three plausible paragraphs and an echo; API-only gives you a tribe that
dies with a free tier.

**Does not decide:** whether a *third* member adds a distinct position or a duplicate — untested. And one
run per model is a demonstration, not a rate; the truncations alone show how much varies between runs of
the same model on the same prompt.

## The instruction that follows

`RUN.md` §5a: *"If you have five minutes and no objection to a company reading your tribe's letters, get a
free key and give your tribe one member that writes well. Keep one member on weights regardless — that is
the member whose memory cannot be revised by someone else's release note."*
