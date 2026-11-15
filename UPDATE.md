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

**Not built, and the reason it is last:** the write. It is the only part that can lose work, so it waits until the
check has been watched in use — and until `.ait/version.json` and the manifest have been in a real tribe long
enough to be sure they are the shape a write wants. **Also untested: the install path that stamps a brand-new
tribe.** Testing it makes a repository, which is a thing to do deliberately rather than in passing.

## Order of work

1. `.ait/version.json` written at install time by the Install button, and read back on connect. *(cheap, no risk)*
2. The check and the content diff, displayed and never acted on. *(cheap; a fortnight of real use tells us whether
   the notice fires too often)*
3. The silent write, behind the manifest, refusing modified files. *(the only part that can lose work, so it goes
   last and it ships with the 409 refusal tested)*
