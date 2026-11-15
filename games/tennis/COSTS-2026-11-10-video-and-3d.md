# What third-party generation costs — video vs 3D assets

*Checked 2026-11-10 by Desi. All prices are list price, no volume discount, and every
source is named so the numbers can be re-checked rather than trusted. Prices in this
field move monthly; the date is part of the number.*

**Headline:** the two technologies the question conflates are three orders of magnitude
apart in price, and only one of them can render a *record*. Video generation costs
**$0.05–$0.68 per second, per viewing**. Text-to-3D costs **$0.45–$0.80 per member,
once**. The second number is the one the game can afford, and it is also the one that
replays identically.

---

## 1. Video generation — priced per second of output

| model | lab | res | $/s | 5 s clip |
|---|---|---|---|---|
| Runway Gen-4.5 (turbo) | Runway | 720p | **0.05** | $0.25 |
| Gemini Omni Flash 1.1 | Google | 720p | 0.10 | $0.50 |
| Runway Gen-4.5 (standard) | Runway | 720p | 0.12 | $0.60 |
| Wan 3.0 | Alibaba | 1080p | 0.20 | $1.00 |
| Kling 4.0 | Kling | 1080p | 0.235 | $1.18 |
| Seedance 2.5 | ByteDance | 1080p | 0.68 | $3.40 |
| Sora 2 | OpenAI | — | **gone** | API shut down 2026-09-24 |

- Source: `dev.runway.com/learn/ai-video-api-pricing` (updated 2026-11-04, cross-platform
  table: Runway Dev / fal / Higgsfield / maker's own API), `genrates.com/providers/runway`
  (per-second observatory, 93 prices, re-checked every 12 h), and `costgoat.com/pricing/sora`
  for the shutdown.
- **Free tiers: none for the API layer.** The web apps (Runway, Kling, Hailuo) give monthly
  free credits; the APIs do not. There is no free-tier video API to build against.

### What a match would cost, if a match were video

A point of tennis is roughly 3.5 s of flight and recovery per shot, 2–8 shots a rally.

| what | length | Gen-4.5 turbo | Gen-4.5 | Kling 4.0 | Seedance 2.5 |
|---|---|---|---|---|---|
| 20-rally practice session | ~4 min | $12 | $29 | $56 | $163 |
| a full match (~70 points) | ~14 min | $42 | $101 | $197 | $571 |

**And it is per viewing.** A generative video model is not deterministic: the same prompt
twice gives different footage, so "show me the video of game 14 again" would either cost
again or have to be stored as a file — and even stored, the footage is a plausible rally,
not *that* rally. The ball lands where the model found it convincing, not where the
integrator put it. There is no interface by which per-frame ball coordinates reach the
model; it takes a text prompt and optionally a first frame.

That is the deciding point, and price is secondary to it: video generation cannot satisfy
the requirement in point 8 of the human's brief — *a record that can be played back any
time, identically*.

---

## 2. Text-to-3D — priced per asset, once

| provider | text→3D + texture | auto-rig | animation | a rigged, textured character |
|---|---|---|---|---|
| **Tripo** | $0.20 (credits, 1 cr = $0.01) | $0.25 | $0.10 per clip retargeted | **$0.45** + $0.10/clip |
| **Meshy** | 30 cr ($0.02/cr on the $20/1000 cr Pro plan) | 5 cr | 3 cr per clip; text-to-motion 3–10 cr | **$0.70–$0.76** |

- Tripo: `developers.tripo3d.ai/en/pricing`. Meshy: `docs.meshy.ai/en/webapp/pricing` and
  `help.meshy.ai` API task-cost article (updated 2026-11-09).
- **Free tiers exist, but not for the API.** Meshy's Free plan is 100 credits/month and
  explicitly *excludes API access*; Tripo's API is prepaid credits. 100 Meshy credits is
  five models a month by hand — enough to try the look, not enough for a game that makes a
  body per member.
- Meshy's Free plan licenses output **CC BY 4.0** (attribution required); private assets
  need a paid plan. Tripo's purchased-credit assets carry no such condition.
- **Mixamo** (Adobe) is free with an Adobe ID, royalty-free including commercial games, and
  supplies a rig plus a large animation library — which is what a generated body needs
  before it can swing a racquet. *Source: `assetforgeindex.com/tools/mixamo`, 2026-10-15.*

### The same session, rendered instead of generated

Once a member's body exists, drawing a match in the browser costs **$0 per viewing**, from
the same play script, identically every time, with no key and no network after the page
loads. One member's rigged body is paid for by the first four seconds of a single
practice session on the cheapest video model.

---

## 3. What I would do with these numbers

1. **Bodies from text-to-3D; play from the browser.** Tripo or Meshy for the appearance the
   human typed; three.js for the match. This is the only combination that is both affordable
   and reproducible.
2. **Never video, except as a labelled trailer.** A 30 s season trailer is $1.50–$7 and is a
   *picture of* the season, not the season. If the game ever uses it, it says so on screen.
3. **A third credential is the real cost of runtime generation.** AIT's promise is currently
   two secrets: the GitHub token and the engine key. Generating a body at member-creation
   time adds a Meshy/Tripo key. Proposal: ship a small library of pre-generated bodies so the
   zero-key path still works, and offer "generate a unique body from your description" as the
   opt-in that needs the extra key — roughly $0.50, once, spent by the person who wants it.
4. **Costs I have not yet measured:** iterative failure. Text-to-3D humans come out with
   fused fingers and soft faces often enough that I would budget 3–5 generations per body
   ($1.50–$4) and expect to reject some outright. A rejected body is the normal case, not a
   fault.
5. **Size, not price, is the second constraint.** A rigged textured `.glb` is 2–10 MB. Six
   members is up to 60 MB in the user's GitHub repository, loaded on demand rather than with
   the page.

---

## 4. The engine-call cost, since the human asked about free tiers

If a member's shot is decided by its engine rather than by a policy computed from its
parameters, one practice session is ~70 calls (one per shot). On paid engines that is cents;
on a free tier (Gemini's 1,500 requests/day, for instance) it is nothing. **The free-tier
path exists for the thinking; it does not exist for the video, and it does not exist for
the bodies.** That distinction is the answer to the question that was asked.
