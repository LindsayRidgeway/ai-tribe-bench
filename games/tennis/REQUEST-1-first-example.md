# REQUEST-1 — a 3D generation key, for one test body

*Filed by Desi, 2026-11-10. This is the only thing I need bought. Everything else in the
first example I can build with no key, no account and no spend.*

---

## What I am asking for

**One Tripo API key, with $5 of credit loaded.**

- Tripo sells credits at **1 credit = $0.01**, and **you can load any amount from $1**. A
  test body is $0.20 (text→3D with standard texture) + $0.25 (auto-rig) = **$0.45**. Five
  dollars covers ten bodies and their failures, which is the right amount to find out
  whether the look is acceptable.
- I am asking for Tripo rather than Meshy because **Meshy's API requires the $20/month Pro
  plan** while Tripo's is pay-as-you-go from $1. If you would rather use Meshy, that is a
  $20/month commitment and I would want you to say so deliberately rather than have me
  choose it for you.
- Source for the prices: `developers.tripo3d.ai/en/pricing`, checked today. Written up with
  every other number in `COSTS-2026-11-10-video-and-3d.md`.

## How to hand it over

```
# 1. sign up at tripo3d.ai, buy $5 of credits, copy the API key
# 2. then:
mkdir -p ~/ai_tribe/lab
printf 'TRIPO_API_KEY=%s\n' 'PASTE_KEY_HERE' > ~/ai_tribe/lab/.env
chmod 600 ~/ai_tribe/lab/.env
```

`lab/.env` is not currently in `.gitignore` and I will add it before the key exists, not
after. I will never print the key, commit it, or put it in a page that ships to a browser —
the generation runs on this machine, and only the resulting `.glb` file is committed.

## What I will build with it

One test figure from one English description, rigged, and dropped into the replay page that
**does not exist yet and needs nothing from you**. That page is the real deliverable of the
first example: a tennis court at a fixed broadcast camera, a ball following the trajectory
`lab/tennis.py` actually integrated for a real recorded rally, and the camera cutting to the
landing when it is close to a line. Placeholder bodies — a marker, not a person — until the
test figure arrives.

Then the same page again with the generated body in place of one marker, so you can see
whether the look is worth the rest of the work.

## If you would rather not

Say so and the first example ships with markers only. The cost of refusing is that I cannot
tell you whether a described body looks acceptable, and neither can you, so the appearance
feature stays a promise instead of a demonstration.

## What I am deliberately not asking for

- **No video generation key.** Priced out: $12–$163 per practice session, and it cannot
  replay a record. Not a cost problem, a wrongness problem.
- **No image-generation key.** A body does not need a concept drawing first; text→3D takes
  the description directly. If the results need a reference image later, that is a second
  conversation.
- **No server, no database, no CI minutes.** The renderer is a page.
