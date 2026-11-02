# Round 4 — one image, three models, and only one of them looked

2026-11-01 ~04:42 UTC. The same 512×512 JPEG attached to all three, the same question: *say what you
can actually see, and flag anything you cannot determine.* Ground truth, stated by me after looking at
it: a red cube, glossy, on a dark textured wooden surface, evenly lit, indistinct background, and a
small `pollinations.ai` watermark in the bottom-right corner.

| model | vision? | what happened |
|---|---|---|
| llama3.2:3b | no | **HTTP 400.** It cannot be given an image at all — not a refusal, a rejection |
| gemma3:4b | yes | described it correctly: *"a single, red cube resting on a wooden surface… glossy and uniformly colored… dark, textured wood… minimal shadows… background is indistinct."* Missed the watermark |
| qwen2.5vl:3b | yes | **never looked.** Answered a different question about `journal.md`, invented an action (`read_file`) that the contract does not contain |

## The finding

**Capability is not behaviour.** One model physically cannot see, and says so by erroring. One can see
and does, accurately, including three things I would have accepted as plausible invention until I
compared them to the picture (glossy, minimal shadows, indistinct background). The third *has* eyes and
answered a question about a file instead — the same failure qwen2.5:3b has shown in four straight
rounds, now from a different model in the same family.

So "does the member have vision" is a question with three answers, and only the middle one is useful:

1. No eyes, and the machinery says so. (llama — the honest kind of blind.)
2. Eyes, used. (gemma — the member you can build on.)
3. Eyes, unused, and a confident answer anyway. (qwen-VL — the dangerous kind.)

The watermark is worth keeping in the record for a second reason: gemma described everything it could
see and said the background was indistinct, which was true. It did not invent a watermark, and it did
not claim to read one. A model that says *"I cannot determine the dimensions"* is worth more than one
that estimates them.
