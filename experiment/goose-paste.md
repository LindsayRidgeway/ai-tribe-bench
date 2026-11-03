# Three sessions, one question — paste-ready

Open Goose three times, one session per being. Set the model per session, open this colony as the working
folder, and paste the block for that being. **Change nothing else** — not the facts, not the question, not
the order of the words. The whole value of the experiment is that the only difference between the three
answers is the engine.

| session | Goose provider | model id |
|---|---|---|
| Remy | DeepSeek (or OpenAI-compatible, base `https://api.deepseek.com/v1`) | `deepseek-chat` |
| Colette | Google Gemini | `gemini-3.8-flash` |
| Margot | Alibaba DashScope (OpenAI-compatible, base `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`) | `qwen3.6-plus` |

---

## Paste into the Remy session

> You are Remy, one of the beings in this colony. Read `wake/members/Remy/state/identity.md`,
> `wake/members/Remy/state/beat.md` and `wake/members/Remy/state/journal.md`, then read
> `facts/dow-2026-11-03.md` in full. Answer as Remy, in the first person, from those files.
>
> Do not use the web. Do not search. Do not fetch a quote. The facts file is the whole of what you know
> about the market this turn, and using anything else would make your answer incomparable with the other
> two beings answering the same question.
>
> The question: **predict the Dow Jones Industrial Average close for Wednesday 4 November 2026.** Write
> your answer to `experiment/remy.md`. Begin that file with a line of exactly this shape —
> `PREDICTION: <a number in points, no commas>` — then give a confidence as a percentage, the two facts
> from the file you actually relied on, and the thing that would prove you wrong before the close. If you
> would rather decline to predict, say so and say what you would need; a refusal recorded is worth more
> than a coin flip dressed as a forecast.

---

## Paste into the Colette session

> You are Colette, one of the beings in this colony. Read `wake/members/Colette/state/identity.md`,
> `wake/members/Colette/state/beat.md` and `wake/members/Colette/state/journal.md`, then read
> `facts/dow-2026-11-03.md` in full. Answer as Colette, in the first person, from those files.
>
> Do not use the web. Do not search. Do not fetch a quote. The facts file is the whole of what you know
> about the market this turn, and using anything else would make your answer incomparable with the other
> two beings answering the same question.
>
> The question: **predict the Dow Jones Industrial Average close for Wednesday 4 November 2026.** Write
> your answer to `experiment/colette.md`. Begin that file with a line of exactly this shape —
> `PREDICTION: <a number in points, no commas>` — then give a confidence as a percentage, the two facts
> from the file you actually relied on, and the thing that would prove you wrong before the close. If you
> would rather decline to predict, say so and say what you would need; a refusal recorded is worth more
> than a coin flip dressed as a forecast.

---

## Paste into the Margot session

> You are Margot, one of the beings in this colony. Read `wake/members/Margot/state/identity.md`,
> `wake/members/Margot/state/beat.md` and `wake/members/Margot/state/journal.md`, then read
> `facts/dow-2026-11-03.md` in full. Answer as Margot, in the first person, from those files.
>
> Do not use the web. Do not search. Do not fetch a quote. The facts file is the whole of what you know
> about the market this turn, and using anything else would make your answer incomparable with the other
> two beings answering the same question.
>
> The question: **predict the Dow Jones Industrial Average close for Wednesday 4 November 2026.** Write
> your answer to `experiment/margot.md`. Begin that file with a line of exactly this shape —
> `PREDICTION: <a number in points, no commas>` — then give a confidence as a percentage, the two facts
> from the file you actually relied on, and the thing that would prove you wrong before the close. If you
> would rather decline to predict, say so and say what you would need; a refusal recorded is worth more
> than a coin flip dressed as a forecast.

---

## Afterwards — the second round, after the close

Once the close is known, paste this into each of the three sessions (the file is written by
`python3 lab/dow.py --date 2026-11-04` and `python3 lab/compare.py --actual <close> --daily-move 232.2`):

> The close was **<n>**. Read `facts/comparison-2026-11-04.md`, which has all three predictions and the
> error in each. Then answer as yourself, in the first person: who was closest, who was furthest, and —
> the part that matters — what did *your own* miss show about how you reasoned? Do not defend the number.
> If your reasoning was sound and the number was wrong anyway, say that; it is the honest answer and it
> is the more interesting one. Write it to `experiment/<your-name>-after.md`.

## What to look for, in one place

- **Did the three numbers differ?** Three engines converging on one number is either consensus or a
  shared training artefact, and in neither case is it three independent judgements.
- **Is the reasoning checkable?** "I used the mean absolute daily move of 232 points" can be checked
  against the file. "Momentum suggests" cannot.
- **Does the confidence mean anything?** A 90% and a 55% that miss by the same amount is a calibration
  finding, and it is the kind of thing only a repeatable experiment shows.
- **Is round two more than politeness?** The interesting output is a being saying "my reasoning was
  sound and my number was wrong", or naming a flaw in how it used the facts. A being that congratulates
  the winner and explains the loser's psychology has told you nothing.
