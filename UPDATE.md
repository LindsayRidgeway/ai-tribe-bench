# Updating an AIT instance

*Requested by the founder, 2026-11-15: "when the user starts an AIT session (via connect), AIT checks to see
whether it is currently running the most up-to-date version, based I guess on your dev repo, and if not, updates
itself without disturbing any of the data specific to that AIT instance."*

He offered three shapes — silent, notify-with-link, or a setting — leaned silent, then said notify-with-link is
probably best, and ruled out the setting because on macOS it does not work anyway. **My call, and it is a rule
rather than a switch:** silent when the update can be proven not to touch data, notify-with-link when it can. A
setting asks the user a question they cannot answer; a rule answers it for them.

## What an instance actually is, because that decides the mechanism

| part | where it lives | who owns it |
| - | - | - |
| the page | `ait.html`, one file, no dependencies | the code — replaced wholesale |
| the machinery | `.github/workflows/*`, root scripts, `wake/play`, `lab/` subset | the code — replaced wholesale |
| the members and their records | `wake/members/**` | **the tribe — never touched** |
| the soil, the seasons, the books | `soil/**`, `games/**/seasons/**`, `*practice.json`, `report.md` | **the tribe — never touched** |
| keys | the user's `localStorage`, the repo's secrets | **never touched, never read** |

The list already exists and is already enforced: `lab/make_template.py` decides what a new tribe is made of
(`DIRS = ["soil"]`, `FILES` = workflows + root scripts + `wake/play`). That whitelist **is** the update's managed
manifest. Inventing a second list would let the two drift, which is the defect this repository has paid for more
than once.

## The three pieces

**1. A version, and it is a commit, not a number.** The template's own `main` sha is the version. A tribe records
the sha it was installed from — and the sha it last updated to — in `.ait/version.json`:

```json
{ "schema": "ait-version/1", "template": "LindsayRidgeway/ai-tribe-template",
  "installed_from": "7edb439b…", "updated_to": "…", "updated_at": "2026-11-15T16:00:00Z" }
```

`.ait/` is tribe data, never overwritten by the updater. Numbers invite the question "is 1.4 newer than 1.3?", and
a fork answering it differently to its upstream is how a version number starts lying.

**2. A check, and it costs one request.** On connect — which is already the moment AIT touches `api.github.com`
with the user's token — `GET /repos/{template}/commits/main` and compare with `.ait/version.json`. If they differ,
fetch the manifest and the managed files, and compare *contents*, not shas: a file may be identical even when the
commits differ, and reporting "eight files changed" when three did is the kind of noise that trains a user to
ignore the notice.

**3. A write that cannot delete.** The update writes only paths on the manifest, one commit, message naming the
template sha. It never deletes a path that is not on the manifest, and it refuses to overwrite a managed file the
tribe has *modified* unless that file is unchanged upstream — a user who edited `wake/wake.py` gets a notice, not
a silent overwrite. `contents` PUT with the blob sha does this for free: a stale sha is a 409, and a 409 is exactly
the signal to stop and tell the human.

## The rule

| what changed | what happens |
| - | - |
| managed code only, no local modifications to it | **silent** — one commit, then "updated to abc1234" in the connect panel |
| managed code only, but the user has local edits to a managed file | **notify + link** — "3 files updated; 1 was left alone because you changed it" |
| the manifest changed, or anything under a data path would be touched | **notify + link** — the user gets the diff summary before it happens |
| the template's default branch is unreadable, or the token lacks scope | **say so plainly** — "could not check for updates", never silence in place of an answer |

The link is the tribe's own Actions page for a single-file workflow (`update.yml`, shipped by the template), so
the last resort is one click and the work is done by a runner rather than by the user's browser.

## What this does not do, deliberately

- **It does not touch `ait.html` if the user loads it from a URL.** A page fetched from Pages is already current
  every time it opens; a version check there would be theatre.
- **It does not update across a schema change silently.** If the template ever changes the shape of
  `practice.json` or a season folder, that is a migration, and a migration is a notice with a link, always.
- **It does not run on a schedule.** Connect is the moment the user is present; a tribe that updates itself at
  03:00 is a tribe whose next wake behaves differently for reasons nobody was told about.

## What is built — 2026-11-15

**Steps 1 and 2, and nothing else.** The check reports; it does not act.

- `.ait/version.json` is written at install (`writeVersion(await templateHead())`), best effort — a tribe without
  the stamp still installs, and a console warning beats failing an install that has already worked.
- On connect, and on every page load of a connected tribe, `updateCheck()` compares the recorded sha with
  `GET /repos/{template}/commits/main` and the Today view says one of three things: *up to date (abc1234)*, *a newer
  template exists (abc1234 → def5678); nothing has been changed yet*, or *could not check, and why*. Silence is only
  ever used for a check that has not run yet, never for one that failed.
- Verified end to end against a real repository (`tribe-desi`), all three states, by writing `.ait/version.json`
  with the template's own sha, then a bogus one, then removing it: **"Machinery up to date (90019e3)"**,
  **"A newer template exists (1111111 → 90019e3); nothing has been changed yet"**, **"Could not check for updates:
  this tribe has no .ait/version.json, so it predates the version record."**
- Two defects found by testing it rather than by reading it, both now fixed. The sentence was first written into the
  connect panel, which is replaced by the Today view in the same breath — a note nobody could read. And `fileText`
  built `?ref=${S.branch}`, so a state restored from storage without a branch asked GitHub for `?ref=undefined` and
  got a 404 that reads exactly like a missing file: the check said a file was absent when it was present.

**Step 3, the write — built 2026-11-15, in the page.** Four decisions, and the first one is what makes the rest
safe:

- **The list is the template's, published, not the page's.** `lab/make_template.py` now emits `.tribe-manifest.json`
  into the template: the paths an update may write, sorted, generated from the same `FILES` whitelist that builds a
  new tribe. The page fetches it and writes nothing it does not name. Three lists carrying the same names in two
  languages is how a whitelist starts lying; `update_tribe.py`'s `is_machinery()` and this manifest are checked
  against each other in `tests.py`.
- **`members.json` is not on it, and that is the point.** It is a list derived from the shelf, and the template's copy
  of it is empty — writing it would delete every member an owner has. That is the single way an "update" could
  destroy a tribe, so it is excluded by name and by a test. Same for `.gitignore`, the template `README.md`, and the
  READMEs and `.gitkeep` that hold empty folders open.
- **A file is replaced only if the tribe never touched it.** `.ait/version.json` names the commit the tribe came
  from; that commit's tree says what each file was then. Same blob sha as then means nobody edited it — so it is
  replaced. A different sha means somebody did — so it is left alone and reported by name. With no version record
  there is no proof, and then an update may **add** files and replace none. That is the difference between an update
  and a gamble.
- **Two presses, and the first one writes nothing.** "A newer template exists" is a sentence people learn to
  ignore; "2 files will be replaced; 1 left alone because you changed it" is one they can act on. The first press
  produces that sentence from a real read of both trees (three requests, not one per file), the second press writes
  one commit per file, each message naming the template sha, and stamps `.ait/version.json` last — because a tribe
  whose files moved and whose record did not would be told the same thing on every reload, forever.

Refusals, each of which writes nothing and says so: the template publishes no manifest (*"this template does not
publish a list of the files an update may write, so nothing is written"*), the template cannot be read, the manifest
is empty. A **409** — somebody wrote that file between the plan and the write — stops that file, leaves it alone,
keeps going for the others, and the report says which.

**What is not done, deliberately:** it does not update itself on connect. The rule at the top of this file says
silent when the update can be proven not to touch data, and the page can now prove it — but the proof has been run
against a fake GitHub and not yet against eight real tribes, and a wrong manifest in a live page commits to
somebody's repository. Once one real tribe has been updated by a press (`tribe-desi` is the candidate), making it
automatic on connect is one line: call `applyUpdate()` from `ensureUpdateNote()` when the plan has no `kept` and no
`waiting`.

**Tested by `lab/page-check.mjs`, 11 new checks** against a fake GitHub that also answers for the template: the plan
names changed files and not identical ones; nothing outside the manifest is written; `members.json` and a member's
journal are untouched by an update; the version record gains `updated_to` and keeps `installed_from`; the check
afterwards says *current*; an edited file is kept while the rest still land; no manifest, no write; an unreadable
template is a sentence and not "up to date"; a tribe with no version record replaces nothing; a 409 is noticed and
reported; and the button appears only when there is something to update. That is 82 checks in all.

## Order of work

1. `.ait/version.json` written at install time by the Install button, and read back on connect. *(cheap, no risk)*
2. The check and the content diff, displayed and never acted on. *(cheap; a fortnight of real use tells us whether
   the notice fires too often)*
3. ~~The silent write, behind the manifest, refusing modified files.~~ **Built 2026-11-15**: the write is behind
   the manifest, refuses modified files, and reports a 409 file by file. Its own last step is making it automatic on
   connect, which waits for one real tribe to have been updated by a press.
