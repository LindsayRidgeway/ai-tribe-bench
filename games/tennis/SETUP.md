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
