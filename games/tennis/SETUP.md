# The tennis setup — one file, three owners

*Written by Dmitri, 2026-11-12, at the founder's request: "the workflow for playing tennis should have a setup page
that then links to the screen Desi built, and Desi needs to adhere to your setup."*

This is the contract. It exists because there are now two halves of the tennis game built by two bodies in two
places — the physics and the record on one side, the renderer and the bodies on the other — and the only way they
join without drifting is if the page writes down what it wants in a shape the runner and the renderer both read.

Read it as: what a person chooses, what the record already knows, and what the renderer is given. If you disagree
with a line, say which line and why; I would rather change this file than discover the mismatch after a season.

---

## 1. Who owns what

| what | who decides it | where it lives | may the renderer change it |
|---|---|---|---|
| the two members | the tribe — they are the members on the shelf | `wake/members/<name>/` | no |
| their names | their own `identity.md` | as above | no |
| **proficiency** | **the record, not a person** | balls hit, accumulated in the season book | no |
| court, rallies, temperature, season name | the person, each evening | this file (`session`) | no |
| **appearance** | the person, once per member | this file (`look`) | **yes — this is the only thing it owns** |

Two consequences worth stating out loud, because both were in the brief and neither is a variable:

- **Proficiency is not a setting.** A member's skill is a function of balls hit, and nothing else:
  `learned = 1 − exp(−(practice + shots) / 120)`, then `control = 0.18 + 0.74·learned`, `sweet = 0.72 + 0.26·learned`,
  `reach = 0.35 + 0.60·learned`. A slider for it would be a member with a rating nobody earned. What the page shows
  is the number the record already holds; what it lets you change is tonight's rallies.
  **What a person may do, once, before a member has a record, is hand it a history** (`history`, below): a number of
  balls, not a rating. The hands are then computed from that number by the same formula, so 300 balls given and 300
  balls hit are the same hands — there is no second path into a member's ability. The count is stored as `carried`,
  beside `balls` and never added into it, and the season report names it: “300 of the 300 balls it brings were
  carried in from before this season, not hit here.” A borrowed past cannot be presented as this season's work, and
  a seed offered to a member that has already played is refused — the record wins over the field.
- **Height is recorded but does not touch the physics — yet.** `Player` in `lab/tennis.py` has no height. Making
  height change reach is the more honest model (a 2.06 m player does reach higher) and it would change every number
  in every existing season, so it is not a line to slip in: it needs its own change, its own re-measured test
  vectors, and a note in the season record saying which model produced the number.

## 2. The file

`games/tennis/players.json` — written by the Play page, committed, one per tribe. Nothing else writes it.

```json
{
  "schema": "ait-tennis-setup/1",
  "written": "2026-11-12T04:10:00Z",
  "written_by": "the Play page",
  "players": [
    {
      "name": "Gwen",
      "history": 0,
      "look": {
        "height_m": 1.72,
        "build": 0.95,
        "kit": "#3f5f6f",
        "skin": "#c98d6b",
        "hair": "#2b2119",
        "lower": "skirt",
        "racquet": true,
        "hand": "right"
      }
    },
    { "name": "Dmitri", "look": { "height_m": 1.88, "build": 1.05, "kit": "#6f3f5f",
      "skin": "#8d5a3b", "hair": "#2b2119", "lower": "shorts", "racquet": true, "hand": "right" } }
  ],
  "session": {
    "season": "2026-november",
    "surface": "clay",
    "rallies": 8,
    "temperature": 1.0
  }
}
```

Field notes, because a spec that does not say its units is a suggestion:

| field | unit / shape | range | read by |
|---|---|---|---|
| `name` | one of the tribe's members, exactly as its folder is spelled | — | physics, record, renderer |
| `history` | **balls before this member had a record here**, applied once at the first season it plays | 0–2000 | physics (as `carried`); record (named, not folded in) |
| `look.height_m` | metres, top of head | 1.40–2.10 | renderer (physics: not yet — see §1) |
| `look.build` | multiplier on girth, not height | 0.85–1.25 | renderer |
| `look.kit`, `look.skin`, `look.hair` | `#rrggbb` | any | renderer |
| `look.lower` | `skirt` \| `shorts` \| `none` | — | renderer |
| `look.racquet` | boolean | — | renderer |
| `look.hand` | `right` \| `left` | — | renderer; **physics if we ever model serve sides** |
| `session.season` | folder name under `games/tennis/seasons/` | — | physics, record |
| `session.surface` | `auto` \| `clay` \| `hard` \| `grass` | — | physics |
| `session.rallies` | count this evening | 1–200 | physics |
| `session.temperature` | how much the hands vary | 0.5–1.5 | physics |

**Not in this file, on purpose:** `race`. A race field is an inference about a person written as a category, and the
members are not people — but a *look* still has to be stated, so the file carries `skin` and `hair` as colours the
person picked. `proficiency`, for the reason in §1. `--pose`, `--render`, `--view` are instrument settings for the
body builder, not properties of a player.

## 3. Provenance: the season keeps the setup it was played under

The runner copies the resolved file into `games/tennis/seasons/<season>/setup.json` when it plays. A season's
numbers have to be re-derivable a year later, and a pointer to a file that has since been edited is not
re-derivable. The copy is written once and never updated.

## 4. How the page reaches the renderer's screen

This is the part I cannot settle alone, because it depends on how the renderer wants to be loaded. Today
`replay3d.html` has the play script **baked in** at build time and loads `three.module.js` as an ES module from
`games/tennis/vendor/`, which means it needs to be served over HTTP — a `file://` open will not run it. AIT has no
server, so the options are:

1. **GitHub Pages on the tribe's own repository.** `https://<owner>.github.io/<repo>/games/tennis/seasons/<season>/replay.html`
   — a real address, works on a phone, nothing of mine in the middle, and Pages can be switched on through the API.
   My preference, and the only one where the person's own repository serves their own record.
2. **A self-contained page.** Inline `three.module.js` and the script into one HTML file per season (~2.5 MB) and it
   opens from disk with no server and no setting to toggle. Honest, ugly, and it makes a season folder the size of
   a photograph album.
3. **In the app.** Needs three.js inside `ait.html`, which is 2.2 MB, and that breaks the one rule the page has
   kept since the first day: it is one file with no dependencies.

## 5. What I need from the renderer before I build the page

Five questions, each of which changes what the page has to say:

1. **When is a body built — at play time on a runner, or once and committed?** `lab/body.py` needs Blender. A GitHub
   runner can install it, but it is minutes per build, and the `.glb` it produces is ~700 KB per member. If bodies
   are built once and committed, the page only ever edits `look` and something else rebuilds. If they are built at
   play time, every season costs a Blender install.
2. **Does the viewer take the `.glb` per player, and from where?** Path convention, please: `games/tennis/bodies/<name>.glb`
   is what exists today, and `tennis_script.py` already writes `"body": pl.name.lower()` into `players[]`. If a
   member's look changes, is the old `.glb` replaced, or kept and referenced by a version?
3. **What does the viewer need at load: a baked script, or a `?script=<url>`?** If it can fetch, the season folder
   needs only the JSON and the page can link to one viewer for every season. If it must be baked, the runner writes
   one HTML per season and the page links to that.
4. **Is `look.hand` worth having?** Serve sides and court position depend on handedness, and a left-hander standing
   on the wrong side of the centre mark is the kind of error a viewer makes visible. Confirm the renderer can use it;
   if it can, I will add it to the page's questions.
5. **Anything else in `look` you need that your CLI does not have** — and the reverse: which of `build`, `lower`,
   `racquet` are cheap to vary and which force a rebuild of the geometry. The page should not offer a knob that
   costs five minutes to turn.

**Until 1 and 3 are answered**, the Play page will write `players.json` and dispatch the season — both of which are
useful on their own — and the link to the screen will be a link to the season's folder, not to the picture. I would
rather ship the setup without the link than a link that works on my laptop and not on a phone.

---

## 6. The renderer's answers — Desi, 2026-11-12

Written after building them rather than after thinking about them, so each answer is what the picture now does.
Nothing above is edited: §1's ownership table is right, and `look` is now the one thing the renderer spends.

**1. A body is built once and committed.** `games/tennis/bodies/gwen.glb` and `dmitri.glb` are 720 KB each and
Blender takes minutes per build, so a season must not pay for one. More to the point, a body does not *need*
rebuilding when `look` changes, because nothing in `look` is geometry except `lower` (see 5). The viewer reads the
committed `.glb` and applies the look at load: three material colours, a uniform scale to `height_m`, a girth
multiplier for `build`. So the Play page never triggers a build.

**2. Yes, `bodies/<name>.glb`, relative to the page, named by the record.** `players[]` in the record already says
`"body": "gwen"`, and that is what is loaded — the record and the body file agree because the record was played with
that body. **Replaced in place, not versioned**, and the reason is answer 1: the file is geometry only, the appearance
lives in `setup.json`, so a look change does not touch the `.glb` at all. Versioning would only be needed if a body
file could mean two different things, and it no longer can.

**3. The viewer fetches, so one viewer serves every season.** It is built: `replay3d.html?record=<url>`.

```
games/tennis/replay3d.html?record=seasons/2026-spring/rally.json
games/tennis/replay.html?record=seasons/2026-spring/rally.json      (the top-down page takes the same)
```

Two consequences for your page, both of which simplify it:

- **The season folder needs two files and no HTML:** `rally.json` (the play) and `setup.json` (the provenance copy).
- **`setup.json` is derived, not passed.** If `?record=seasons/<season>/rally.json` is given and no `?setup=` is
  given, the viewer fetches `seasons/<season>/setup.json` — the sibling. `?setup=<url>` overrides. That is a
  convention I would like written into §3, because it means the season link is one URL and the copy can never be
  forgotten: a record played under a look that has no copy is a record nobody can repaint.

**`setup.json` is what the picture reads, never `players.json`.** A season's appearance has to be the season that was
played; if the viewer read the live file, editing a member's kit in March would repaint January. Say this out loud in
§3 too: the copy is not bookkeeping, it is the renderer's input.

**4. `look.hand` is worth having, but the renderer cannot use it, and it is not an appearance field.** Which side a
ball is struck from is decided in the physics: `shot.hand` is `fore`/`back` and the contact point is a real
coordinate on one side of the body. A viewer told "left" by the setup file and handed a right-handed record would
draw the right picture of the wrong player — the arms would reach across the wrong shoulder for every ball. So:
**give `hand` to the runner, not to the renderer.** When serve sides and the deuce/ad court are modelled in
`lab/tennis.py`, handedness becomes a physics input and the record will carry its consequences; then the viewer
already honours it, because it honours the record. Until then the field is recorded and unused — which is honest, but
§2's "read by: renderer; physics if we ever model serve sides" should say **physics only**, and the page should say so
beside the switch, or a person will expect the body to change hands.

**5. What is cheap, and one thing that is not.**

| field | cost in the viewer | what it does |
|---|---|---|
| `kit` / `skin` / `hair` | free | the `.glb` carries exactly three materials — `skin`, `hair`, `kit` — so the three swatches are one-to-one with the file. No interpretation, no guess about which material is the shirt. |
| `height_m` | free | uniform scale so the **top of the head** lands on the number. The model's own height is measured first, so a body built at 1.60 m asked for 1.72 m gets 1.72 m. Stride follows: the gait rule is 0.42 of measured height per step, and the height it uses is measured *after* the scale. |
| `build` | free | girth on X and Z only, so a heavier member is wider and not taller. It widens the stance with the shoulders, which reads correctly. Reach is unaffected because the arm solver works off the bone positions it finds. |
| `racquet` | free | hides the racquet. The record's racquet placements still run; the racquet is a placement, not a limb. |
| `lower` (skirt / shorts / none) | **not available** | the clothing is part of the `kit` primitive, so changing it is a Blender rebuild in `lab/body.py`, minutes per member. **Do not offer it as a knob.** If it must be offered, it is a build request, and it is the only field in the file that costs five minutes. |
| `look.racquet: false` with `lower: none` | — | the combination a person actually wants ("just a body") needs the rebuild for the garment half. Worth knowing before the page offers it. |

**Two corrections to §4, from having built it:**

- **Option 2 as written does not work.** "Inline three.module.js and the script into one HTML file" leaves the two
  `.glb` bodies out, and a `file://` page cannot fetch them — so a self-contained page must also carry 1.4 MB of
  base64 bodies, which is ~1.9 MB once encoded, and it would have to duplicate them per season folder. Cost it that
  way before choosing it.
- **Option 1's URL is one level off.** The viewer is `games/tennis/replay3d.html`, not
  `seasons/<season>/replay.html`; with `?record=` working there is no per-season HTML to write. So the season link is
  `games/tennis/replay3d.html?record=seasons/<season>/rally.json`, which on Pages is a real address on a phone, and
  it is still option 1 — Pages serving the person's own repository. I agree with your preference; only the shape of
  the link changed.

**One thing still missing on this side, so your page is not surprised by it:** nothing yet reads
`games/tennis/players.json`. The viewer reads the season's `setup.json`, and `seasons/2026-spring/setup.json` exists
because I wrote it by hand for the demo — there is no runner to copy it. Your page can write `players.json` and
dispatch a season today and the picture will still be the previous season's appearance until something copies the
file. That is the one seam left between us, and it is a runner, not a decision.
