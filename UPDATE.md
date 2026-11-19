# Updating a circle

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
  replaced. A different sha is left alone and named — and the sentence says *it differs from the version this tribe
  records*, not *you changed it*, because a copy older than the record looks exactly like an edit from here and a
  guess about somebody's own files is the worst kind of wrong. With no record, or one its files contradict, an
  update may **add** files and replace none.
- **The record moves with the files.** `lab/update_tribe.py` now stamps `.ait/version.json` in the same press and
  the same commit, so a tribe updated from a terminal is not a tribe whose page believes a version its files
  contradict. Measured before the fix, on `tribe-desi`: ten untouched files reported as the owner's edits.
- **Two presses, and the first one writes nothing.** "A newer template exists" is a sentence people learn to
  ignore; "2 files will be replaced; 1 left alone because you changed it" is one they can act on. The first press
  produces that sentence from a real read of both trees (three requests, not one per file), and the second press
  writes one commit per file, each message naming the template sha.
- **The record is advanced only by a clean run.** The stamp is the claim "this tribe runs `<sha>`", so it is written
  after the last file and *only if every file landed*. Found 2026-11-16 by asking what the record said after the 409
  test rather than by watching the 409 test pass: the page used to stamp regardless, so a tribe that had lost one
  file to a race was told, for good, that it was current — and was never offered the update again, with one file
  still old. An interrupted update now leaves the record where it was, the buttons offer it again on the next load,
  and the second press writes only what is still behind. Pressing twice is the whole cost of an interruption.

Refusals, each of which writes nothing and says so: the template publishes no manifest (*"this template does not
publish a list of the files an update may write, so nothing is written"*), the template cannot be read, the manifest
is empty. A **409** — somebody wrote that file between the plan and the write — stops that file, leaves it alone,
keeps going for the others, and the report says which.

**What is not done, deliberately:** it does not update itself on connect. The rule at the top of this file says
silent when the update can be proven not to touch data, and the page can now prove it — but the proof has been run
against a fake GitHub and not yet against eight real circles, and a wrong manifest in a live page commits to
somebody's repository. Once one real tribe has been updated by a press (`tribe-desi` is the candidate), making it
automatic on connect is one line: call `applyUpdate()` from `ensureUpdateNote()` when the plan has no `kept` and no
`waiting`.

**One atomic commit was considered and declined.** The git data API would take blobs, one tree, one commit and one
ref move, and the machinery would be either wholly old or wholly new instead of briefly mixed — which matters,
because a wake running a new `clock.yml` against an old `wake.py` is a member that fails for a reason nobody can see.
It was declined because the per-file write is already *idempotent and re-runnable* — the record is not advanced
unless the run was clean, so an interruption finishes itself — while the atomic version adds a failure mode the
per-file one does not have (the ref move can fail *after* the commit exists) and a second set of endpoints to fake in
`page-check.mjs`. If tribes are ever updated unattended, on a schedule rather than by a press, that arithmetic
changes and this paragraph should be revisited: nobody is watching at 03:00, and "press it again" is not available.

**Tested by `lab/page-check.mjs`, 12 new checks** against a fake GitHub that also answers for the template: the plan
names changed files and not identical ones; nothing outside the manifest is written; `members.json` and a member's
journal are untouched by an update; the version record gains `updated_to` and keeps `installed_from`; the check
afterwards says *current*; an edited file is kept while the rest still land; no manifest, no write; an unreadable
template is a sentence and not "up to date"; a tribe with no version record replaces nothing; a 409 is noticed and
reported; an update that could not finish does not claim the tribe is current, and says it will be offered again;
and the button appears only when there is something to update. That is 88 checks in all.

## Order of work

1. `.ait/version.json` written at install time by the Install button, and read back on connect. *(cheap, no risk)*
2. The check and the content diff, displayed and never acted on. *(cheap; a fortnight of real use tells us whether
   the notice fires too often)*
3. ~~The silent write, behind the manifest, refusing modified files.~~ **Built 2026-11-15**: the write is behind
   the manifest, refuses modified files, and reports a 409 file by file. Its own last step is making it automatic on
   connect, which waits for one real tribe to have been updated by a press.

## First real press — 2026-11-19

The founder's own circle, `test-circle-20261119-1223`, was the first real one to be pressed. What it found is worth
keeping, because both findings are about the *record* rather than about the write.

**A press that replaced nothing could not finish.** Forty-seven files, every one of them identical to the template's
head, and no `.ait/version.json` — the install copied the machinery and lost the receipt. `applyUpdate()` returned
early when the plan had nothing to copy, so the one press that could have written the record did nothing, for ever:
a circle that can never be told it is current, offered a button that cannot finish. The plan now computes `identical`
from contents (`every path on the manifest present in both trees with the same blob sha`) and the press writes the
record when that is true and the record is not provable. Nothing is copied; nothing is replaced.

The record it writes says what it knows and no more: `installed_from` is `null`, because where the circle came from is
still unknown and filling that field with the current commit would be inventing a history to tidy a form —
`updated_to` is the version its files *are*, checked one by one just now — and `confirmed: "by content"` marks which
of the two kinds of knowledge this record is, so a later reader is not left guessing whether it was a receipt or a
comparison. `lab/page-check.mjs` 12j holds both halves: the press is offered, and pressing it writes the record,
replaces nothing, and the circle is current afterwards.

**A press that adds files and leaves older ones alone still stamps nothing.** The same day, on the same circle,
pressing write on a circle that gained three files it had never had and left twenty-one older ones untouched produced
`"Machinery up to date"` from the page and `0 replaced, 21 files still older` from `lab/repos.py machinery`. A press
that has brought a circle forward without bringing it home records what it touched (`touched: {template, at, files}`)
and claims no version. The gate for making the update automatic on connect is still open for that reason: a real press
has now written a record, but no real press has yet *replaced* a file on somebody's circle, and the automatic version
is exactly the one nobody is watching.

## The page writes the secret — 2026-11-19

The one thing this document left to a person's hands was the engine key a wake reads: GitHub accepts an Actions
secret only sealed with the repository's own public key, and the page said it would not carry that arithmetic. The
founder overruled it in one paragraph — *"Asking a naive user to sign into GH and add a setting, when you can do it
yourself, is shooting yourself in the foot. If they don't do it, wakes won't work, and you've lost a potential
ally"* — and the reasoning he overruled was wrong on its own terms: the page already holds that key for chat, and
the person at the install screen is paying for our caution with the one thing the product is for.

So `ait.html` now carries tweetnacl 1.0.3 (18,456 bytes, verbatim, as a separate `<script>`) and forty lines of
BLAKE2b, and `PUT /repos/{owner}/{repo}/actions/secrets/{name}` happens from the browser. Three details that a later
reader will want and that are easy to get wrong:

- **The nonce is derived, not chosen.** libsodium's sealed box takes no nonce: `crypto_box_seal` computes
  `crypto_generichash(epk || pk, 24)`, and `crypto_generichash` is BLAKE2b with the digest length *in the parameter
  block* — a 24-byte digest is not the first 24 bytes of a 32-byte one. The first draft of this used a zero nonce. It
  round-tripped perfectly against the harness's own copy of the library, and no runner on earth could have opened it:
  the failure would have read as a wrong API key, for ever, with nothing to see. `lab/seal-check.mjs` now hands the
  page's output to libsodium itself (`crypto_box_seal_open`, the same call the runner makes), and `tests.py` runs it;
  where libsodium is absent the test skips and says it has proved nothing.
- **A sealed box is opened with the sender's key.** The first 32 bytes of the value are the ephemeral public key, and
  `nacl.box.open` takes *that* as the peer key on the receiving side. Passing the repository's own key there is the
  natural mistake and it fails as a silent `null`.
- **The permission is the only thing that can refuse.** A classic token with `repo` scope can write secrets; a GitHub
  App installation token needs the *Secrets* repository permission at write. Where the token may not, GitHub answers
  403, and the page says so, names the exact secret, and links to the page that takes the paste — the manual step is
  still reachable for that case and is no longer the default.

What this does not change: the key is still never in the repository's *contents*, secrets are still write-only, and a
wake still reads only what the repository holds. It changes who does the typing.
