# REQUEST-2 — one character reference sheet, four views

*Filed by Desi, 2026-11-10. Format follows `llm-symposium/docs/gallery/prompt-methodology.md`: the amigo
writes the prompt, the human runs it as hands, the author selects. Precedent: `REQUEST DM-2`.*

**Why.** The two Mage images Lindsay showed me are photographs of a moment. They cannot be animated
without video generation, which is priced out and cannot replay a record. What they *can* be is the thing
I lack most: **a reference to build against.** I am modelling blind — I render a still, look at it, adjust
a number, render again. An artist works from a reference sheet pinned beside the screen. That is the gap
between what I built today and what those two images are.

**What I am asking for:** four runs, four images, one character, one kit. Not action shots — a
*construction sheet*. No racquet, no ball, no court lines: those are the things I place myself, and a
generated racquet in a generated hand is exactly the detail that goes wrong.

---

## Character A — the woman

**Run 1 — front**, standing, arms at sides, facing the camera square.

> full-body studio photograph of a female tennis player standing square to the camera, arms relaxed at
> her sides, feet shoulder-width apart, plain white tennis top and white skirt, white trainers, white
> visor, hair tied back, neutral expression, even soft frontal studio lighting, seamless mid-grey
> background, sharp focus throughout, full figure from head to shoes with space above the head and
> below the feet, natural anatomy, correct number of fingers, no props, no racquet, no ball

**Runs 2–4 — left profile, back, three-quarter.** Same paragraph with one phrase changed
(`turned 90 degrees to her left, side profile`, then `seen from directly behind`, then
`turned 45 degrees away from the camera`), each run **starting from the image accepted in Run 1 as an
image reference**, so the face, kit and lighting are held rather than re-invented.

Negative, all runs: racquet, tennis ball, motion blur, dramatic action, foreshortening, extreme
perspective, multiple people, court, background detail, text, watermark, extra limbs, distorted hands,
shadows across the body, harsher rim light.

## Character B — the man

Same four runs, same wording with the kit changed: plain white T-shirt, navy shorts, white trainers, no
visor, short hair. Held the same way, front first, then img2img from it.

---

---

## The block to paste (added 2026-11-10 after the first attempt missed)

The first run produced three multi-panel course decks about choosing an AI companion platform — seven
panels per sheet, captions, logos. Not this brief. Either the wrong text was pasted, or the tool
defaults to a storyboard layout; both are fixed by asking for **one photograph** and forbidding the
layout words outright.

**Run 1 — paste this as one block, nothing else:**

```
a single full-body studio photograph of one woman, a tennis player, standing square to the camera,
arms relaxed at her sides, feet shoulder-width apart, plain white tennis top and white skirt, white
trainers, white visor, hair tied back, neutral expression, even soft frontal studio lighting, plain
mid-grey seamless background, sharp focus from head to shoes with clear empty space above her head and
below her feet, natural proportions, correct hands, five fingers on each hand. Photograph, not a
storyboard, not a slide, not a collage. One person, one view, whole frame filled by her and nothing else.
negative: multiple panels, collage, grid, storyboard, slide deck, presentation, captions, subtitles,
text, watermark, logo, interface, screenshot, racquet, tennis ball, tennis court, other people, motion
blur, dramatic action, extreme perspective.
```

**Runs 2-4** are the same block with one clause changed (`turned 90 degrees to her left, side profile`;
`seen from directly behind`; `turned 45 degrees away from the camera`), each fed the accepted Run 1 as an
image reference.

**What is already proven, by the accident.** The same woman — same face, same knit sweater, same
apartment — holds across seven panels of the throwaway sheet: her features and her clothing are
consistent under one prompt. That is the exact capability a reference sheet needs and a sprite set
would need. The tool can hold an identity; it was never asked to hold a tennis player.

## What I will do with it

- Measure proportions against it — head-to-height ratio, shoulder width, limb taper, where the knee
  actually sits — and correct `lab/body.py` from numbers I can see rather than numbers I guessed.
- Colour-match the kit and the skin tone properly instead of picking hex values by feel.
- Show the corrected body beside the reference, so the comparison is checkable rather than asserted.

## What this does not do

It does **not** make the render photoreal, and I am not asking it to. A photograph cannot be posed by
the integrator, and a body that cannot be posed is a body that cannot show a shot. The sheet is
scaffolding for the model; the model stays the thing on the court.

Two things in the images shown to me, recorded because they matter for this brief rather than as
criticism: the man's grip does not close on the handle, and the woman's racquet head is out of plane
with her swing. Both are invisible in a picture and fatal in a mesh. A construction sheet avoids the
question entirely.
