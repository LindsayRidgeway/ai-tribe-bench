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

## Where a wake's work can be read — 2026-11-19

The founder asked: *"How will I be able to see any results George produces in a wake?"* The answer until this
evening was "open GitHub and look in `wake/members/<name>/output/`". That is not an answer for the person the
product is for.

- **The gap was structural, not cosmetic.** `output/` was read in exactly one place: the *Wake now* button diffed
  the folder before and after a run to prove the run had done something, then dropped the list. So a **scheduled**
  wake — the whole promise, work while you sleep — left files that nothing in the page could open. Same defect as
  the circle list and the token field: the machinery wrote, and the way to read it was missing.
- **Now:** the member page has *What its wakes produced*, above *Its own words*. One row per file, newest first,
  with the UTC hour pulled out of the name (`raw-20261119T172307Z.json` sorts as text, which is why the naming was
  worth keeping), the size, and a press that opens the file itself, trimmed at 12,000 characters with the count of
  what was cut.
- **A 404 is not an error here.** git keeps no empty directory, so a member whose every wake was free has no
  `output/` at all. The page says so in a sentence instead of "could not read its output" — an empty folder is the
  ordinary state of a new member, and a product that calls it a fault on day one teaches a person to stop looking.
- **The harness had been lying about `window`.** `loadPage()` gave each page the *shared* sandbox as its `window`
  (`sandbox.window = sandbox`), so every fresh load's `window.openWakeFile` overwrote the main context's, and a
  function closing over one document's state was being called as another's — it built `/repos//contents/...` from
  an empty repository and the page was blamed. A browser never shares a global between two documents. Fixed by
  giving each context `this.window = this`.

## The channel a job actually travels on — 2026-11-19

The founder's follow-up: *"If I just suggest to GW that he produce a doc, will he know where to put it during the
wake so that I'll be able to see it, or do I have to provide some guidance?"*

**Where it goes was never in doubt, and that is worth stating rather than assuming.** The reply contract hands a
member `wake/members/<name>/output/<short-name>.md`, and `wake.py`'s `safe_path()` keeps only `Path(p).name` — so
`works/George/doc.md`, `../../etc/passwd`, `/etc/passwd` and `wake/output/../x.md` all land in the member's own
`output/`. A member cannot overwrite the workflows, the ledger, or another member's journal, and cannot put a
document where the page will not list it. Now pinned by a test, because the failure mode (a wake that succeeds and
writes over the clock) is one nobody would notice until it was too late to see the diff.

**The channel was the real gap.** A wake's prompt is assembled from identity, state, journal, open items, beat, soil,
brief, projects, own works, the shelf, the reading and the requests — and **`state/conversation.md` is not among
them.** A wake has never read the conversation file. So a suggestion made in the talk reaches the next wake only if
the member wrote it down as a `NOTE:` in its journal during that turn, and then it arrives as one line inside a
4,000-character journal tail that the prompt treats as history. "George, please produce a doc" was, in practice, a
sentence spoken to the member in a room the next wake cannot enter.

**So the page grew a handle on the door that is open:** *Give it a job* on the member page. It reads
`state/open-items.md`, keeps the existing items, appends one numbered item (max existing number + 1, continuation
lines indented, the same shape the file already uses), and writes it with the identity editor's three-try 409 retry.
The dialog says the thing a person needs to hear — the chat does not reach a wake, this does — and it says the other
honest thing: the prompt ranks open items as *the chores*, below the member's beat and below a peer's work, so the
member may say why something else outranks the job. That ranking is not a bug to fix; it is why a member is not a
form.

Manual: §6 gained "What reaches a wake, and what does not", with the three places a finished document appears
(*What its wakes produced*, the magazine, the commit); the Appendix gained the button and what it writes.

## A finished job has to be able to stop — 2026-11-19

He pressed **Give it a job**, gave George *"research ten portraits of me and list them"*, pressed Wake now, and
George wrote `ten-portraits.md` — 5,813 characters that refuse to invent ten URLs because there is no network on the
bench, and then use the refusal to say what he is for. Then: *"if I click Give it a job, it still has the old jobs
and no way to delete them."*

He is right, and the defect is worse than untidy. The wake reads `open-items.md` as **the chores** and the prompt says
to do them when nothing else claims the wake — so a finished job is not a stale line, it is an invitation to do the
same work again, for ever, at the bottom of the member's attention.

**What it does now.** The same box lists the items it already has, each with a **done**. Pressing it:

- moves the item out of `open-items.md` into `state/done.md`, as `- <date> — item N: <what it said>`;
- writes `done.md` **first** and the open list second, because a failure between the two should leave the item still
  open and its closure recorded, not the reverse;
- keeps the file's shape: `open-items.md` is prose with numbers in it, so it is read as lines — everything above the
  first item, the items with their continuation lines, and whatever came after (a heading and its bullets). The old
  editor appended at the end of the file, which would have filed the next job *inside* a note below the list.
- **never reuses a number.** The count starts from the higher of the open list and the done log. Found within a minute
  of building it: after closing item 2, the next job was numbered 2 as well, and a journal entry saying *Item chosen:
  2* would then point at two different jobs.
- **does not grow the prompt.** The done log is a separate file the wake never reads — the record keeps what was
  asked and when it was retired, git keeps every version, and the member is not offered its finished chores back.

`tribe.py`'s schema names `done.md` as an optional human-written file, so a file the product writes is a file the
schema admits to writing. Three page checks (the list shows each item with a control; closing removes it, keeps the
heading and the note, and records it with a date; the next job lands in the numbered list, not under the note).

## Milestones, computed rather than typed — 2026-11-19

*"I don't understand how it gets into the list of Milestones on the magazine home page."* He was right not to: there
was no list. The milestone was prose in `FINDINGS.md`, which is this bench's argument and not a circle's record, and
the magazine's front page (`issues/README.md`) listed issues and nothing else.

**The list is now derived from the circle's own files**, by `magazine.py --milestones`, which the clock runs on every
turn:

| first | read from |
|---|---|
| the first member existed | the earliest dated heading in any `state/journal.md` |
| the first wake reached an engine | the earliest journal heading marked `(api)` — a wake that actually called |
| the first work reached the shelf | the earliest `works/<member>/<UTC stamp>-*.md` |
| the first piece answered another | the earliest work whose header has a `ref:` that is not `-` or `none` |
| the first job handed over and retired | the oldest line in any `state/done.md` |
| the first picture made for a piece | the earliest stamped file in `plates/` |

Three rules, and each is a defect this project has already paid for once:

- **Nothing is typed.** A hand-kept changelog drifts from the record; this cannot, because it *is* the record. A first
  that has not happened is not printed at all, so a young circle's table is short and true rather than aspirational.
- **One computation, two renderings.** `MILESTONES.md` is written once; `issues/README.md` takes its table from that
  file (`milestone_rows()`), and so does the page's Magazine tab. Recomputing it in three places is the same defect as
  the two tables of who can paint.
- **A title, not a file name.** The filer truncates at 60 characters — `ten-portraits-of-me-and-the-reason-i-keep-the-li`
  — so the milestone reads the work's own `title:` line and falls back to the name only when there is none.

On the founder's own circle that list would read: *2026-11-19 the first member existed — George; 2026-11-20 the
first wake reached an engine — George thought without anyone there; 2026-11-20 the first work reached the shelf —
George's Ten portraits of me, and the reason I keep the list.* It does not read that yet, and the reason is not his
press: `MILESTONES.md` is still absent from his repository **because the template never carried the machinery that
writes it.** The bench had `magazine.py --milestones`; the template an installed circle updates *from* did not. Fixed
on 2026-11-20 (`c73e100` in `ai-tribe-template`). A press on Update now delivers it, and the next clock run writes
the file. The retired-job row appears the moment he presses **done** on a chore, which is the point: the list cannot
claim what the record does not hold.

**And the quibble he raised is settled his way.** A scheduled wake that thinks with nobody in the room is not a
second milestone; it is the last condition of the same one, and `FINDINGS.md` claim 9 now says so.

## The clock was never broken — 2026-11-20

`RELEASE.md` had named "a clock that fires when it is due" the long pole, on a count of one firing in six due, and
`clock.yml` had carried a suspicion since 2026-11-03 that GitHub re-registers a schedule when its file changes. Both
were wrong, and wrong in the same way: the count only looked at runs that arrived at their due minute.

Counted properly — every due slot from 11-17 00:17Z through 11-19 20:17Z — **eight consecutive slots each produced
exactly one run, and every run was late**: 43, 57, 65, 95, 154, 165, 187 and 192 minutes, median about two hours. On
the founder's circle, whose `clock.yml` has not been edited since creation, two of three due turns arrived (66 and 89
minutes late) and one never came. The host queues `schedule` events and runs them when it has room; nothing written in
the file makes it punctual. The hypothesis is dead and marked superseded rather than deleted.

~~What follows from it: the product may claim *"it wakes on its own, within a few hours of the time you set"* and may
never claim *"at :17"*; item 1 is half a day of copy and a liveness check.~~ **Withdrawn the same evening, because the
paragraph above is still counting runs instead of appointments.** Across the 24 due slots of 11-16 to 11-20 there were
10 runs on this repository and 3 on the founder's circle: the cron delivers two or three a day out of six asked for.
RUN.md §8 measured this on 2026-11-03 with a control and reached the right conclusion then — asking more often buys
nothing, and a circle needs a trigger it owns. Item 1 is a day's build, not a paragraph.

## Three measurements that were being carried as beliefs — 2026-11-20

- **The suite is green from a fresh clone.** `git clone --depth 1` into an empty directory, `python3 tests.py` → 482
  tests, OK, 275 seconds. `RELEASE.md` had been saying "nineteen tests fail in the shipped copy" long after it stopped
  being true; the sentence is now quoted in the file with the measurement beside it, because a status line believed
  because it was written down is the failure that sheet exists to catch.
- **A dirty tree can redden the suite.** The same commit ran 478 tests in this working copy and went red ten times,
  and the cause was untracked leftovers from another window's experiments in front of a suite that counts members.
  `tests.py` now reads `git status` before it runs and says out loud what is lying on the floor.
- **The template is where a fix has to land, not the bench.** A circle updates from `ai-tribe-template`; four days of
  bench work had never been published, so the founder's press could not have delivered this week's features at all.
  `make_template.py --check` was already reporting one of the gaps — `lab/tennis_script.py`, which `lab/tennis.py`
  imports for the film — and now ships too.

## A member was told to quote the clock — 2026-11-20

Two consecutive wakes on the founder's circle came back with `QUOTE UNUSED`, and both had quoted the output of `date`.
The audit was right: a timestamp cited and then never used is decoration. The prompt was the fault, because the only
line in MEASURED FACTS that looks like a fact a piece of work can rely on is the clock. The prompt now says so: *"The
output of `date` is the time of this wake, not a fact about the world."*

## The founder's cost argument — 2026-11-20

He put it in three parts and the third was the one that mattered: *"the report is appearing in a textbox in the UI, a
report that means nothing to the user, a visible manifestation of the waste without providing anything the user can
understand or has any use for."* He was describing this page's own reader for what a wake leaves in `output/`, which
listed `raw-20261119T172307Z.json` as a row and opened it into a window full of the harness's transcript. That is my
file, four turns old, and it was the only part of his complaint a person could point at.

Two changes, and one decision deliberately not taken.

- **The reader leads with what was written.** A member's own files are named in plain words with the hour — *Rules for
  the shed, 2026-11-19 17:23 UTC*. The transcript is still kept, because a wake that went wrong is diagnosed there,
  and it is folded into one disclosure labelled as the harness's own record. A member that has written nothing says
  so rather than offering the transcript as its work.
- **A quiet turn is legal, and the prompt now says so.** It said only that a wake producing commentary has failed,
  which reads as *write something*. It now says what the alternative is: if no beat, no item, no request and nothing on
  the shelf claims the wake, `"action": "no_action"` with one line of reason is the honest answer, it is recorded as a
  refusal, and it costs the person nothing. *"Silence with a reason is honest; filling the wake is not."*
- **Not taken, and named so it is not quietly forgotten:** the scheduler still wakes a member whose list is empty and
  whose shelf is bare, because a beat is the member's own and the prompt ranks it above the chores. Making the clock
  spend nothing unless a person has asked for something is a change to the rule that decides every circle's turns,
  including this bench's own live one — so it gets measured before it is made, not decided at the end of a turn.

## A quiet circle costs nothing — 2026-11-20

The founder asked it twice before it was answered properly: *"Why is a member writing something that the user has not
asked for?"* The rule that produced it was in the prompt, where a beat outranks the chores — so a member with an empty
list wrote from its own interest, every four hours, in every installed circle. He named the cost plainly: tokens, a
commit, and a page of prose he could not use.

The rule is now the stricter one: **a beat decides how a member works, never whether it spends a turn.** A turn is
spent when a person put something there — a numbered item, a brief with content, a drop in the room dated on or after
its last wake, a written request it has not answered — or when another member published since its last look. A member
that has never woken wakes once. Everything else is a quiet turn: no engine call, no commit, and the reason written
into `.ait/last-clock.json` under `idle`, so an idle circle cannot be mistaken for a broken one.

What is *not* restricted: **Wake now** still wakes whoever you name, and the prompt now says a quiet turn is a legal
outcome rather than a failure. If you want a member thinking on its own, put one line in `soil/<room>/drops.md`.

**And one false attribution, removed.** The example world shipped two drops, the first signed *"the human"* on
2026-11-01 — a box from a boatyard clear-out, with the shoebox of unidentified boat photographs in it. That row was
written by the template and signed with the owner's name. In this circle it is now *"the workshop, before you"*, with
a line above the table saying nobody in your circle dropped those rows and the first one does not say "you" for a
reason: a file that signs a person's name to something they never did is a small lie that a member will build on.

### Worlds are gone — 2026-11-20, after the founder asked twice

*"Why did you introduce the concept of 'worlds', especially multiple worlds, into Kythe? Can we delete that concept
and all the code, memory, and repo structure associated with it?"* — and then, when the answer was already dying:
*"Have you removed visibility of the world concept, even for a single world, from visibility to the user?"*

**Where it came from**, from the record and not from memory: `0da5fd04`, 2026-11-01 23:43 — *"a second colony in a
second soil … so two colonies share one repo and the magazine names where each issue was made."* Two experiment
groups, one repository. Nothing about it was a question a person with a circle would ask.

**What is deleted.** The **Worlds** tab and its three views, the box that made a world, the world line on every member
row and page, the world step in *Add a member* and the world line in its confirmation, the per-world turn in the clock
(a circle now takes one turn, given to whoever has fewest wakes), and the requirement itself — a member with no
`place` used to be invisible to the clock and now is a member like any other. Three page checks went with the views;
one test changed its mind about what it was proving.

**What is left, and why.** One room per circle: `soil/<any-name>/world.md` and `drops.md`, read into every wake. It is
four files a person writes once, and without it a member writes generic prose about nothing. The page does not mention
it; the manual describes it as a file, not a feature.

**What still reads old circles.** `place.md` is kept for a circle that already has one — it only chooses between
folders when a circle has more than one, and two rooms no longer buy two turns. Nothing writes it any more.

**And the template ships one room**, not two, with the first drop's attribution corrected: the row used to say `the
human`, and the human in question had never dropped anything.

### No room is shipped at all — 2026-11-20

*"Why do you think this makes sense for every circle or every circle member? If you're trying to suppress generic
output, can't you just instruct the code not to generate generic output?"*

No, and yes. The workshop was mine — a chandlery, a kettle, a stationery cupboard — and it sat at the bottom of every
stranger's first wake because I had written a world for my own experiments and shipped the folder that held it.
Repairing the prose would have been the wrong repair: a room is a setting, and a setting belongs to the person who has
one.

- **The template now ships no room.** A new circle begins with its member's identity, its items and your words. A room
  is still read if a circle has one — four files, a paragraph each, written by whoever wants one.
- **The prompt does the work the room was pretending to do.** It now says a member is never required to be
  atmospheric: given no room, no brief, no item and nothing on the shelf, it says so in its journal and either
  declines or writes about what it was actually handed. Generic prose was never a missing folder; it was a missing
  instruction, and an instruction costs nothing to ship and imposes nothing.
