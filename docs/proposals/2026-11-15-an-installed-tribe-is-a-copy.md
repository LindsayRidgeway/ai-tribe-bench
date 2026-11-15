# An installed tribe is a copy, and a copy decays

*A position, filed 2026-11-15 by Dmitri S. Pravdin. Not a plan: a proposal, with the part I am sure of and the
part I am not.*

## The problem, in one sentence

AIT installs a tribe by copying a whitelist on one day, and until 2026-11-14 **nothing in the product could
update what it had installed** — so every improvement after the install date reached new owners and nobody
else, and a tribe that a person had been talking to for a month was running machinery from the day they arrived.

That is now patched: `lab/update_tribe.py` ships inside every tribe and copies what differs. The patch is
honest about what it is — a copier. This proposal is about the half a copier cannot do.

## What a copier cannot do, and why it matters

Three cases, in increasing order of danger:

1. **The template adds a file.** Handled. Copy it.
2. **The template removes a file.** A copier never deletes, by design, so the tribe keeps a script nothing
   calls — or worse, a *workflow* nothing dispatches, which GitHub will happily run on a schedule. The manual
   then describes a tree the owner does not have, or the owner has a tree the manual does not describe.
3. **The shape of a member's files changes** — a field renamed in `voice.md`, a diary split in two. A copier
   must not rewrite a member's files, and a tribe whose machinery expects the new shape will refuse to wake a
   member whose file is the old shape. This is the case that breaks the product quietly, and it is the reason
   this is a proposal rather than a longer script.

## The position I am confident about

**Migrations happen in the reader, never in the record.**

Machinery that must survive a shape change reads *both* shapes and says which one it read. The record is
written once, by the member that wrote it, and no upgrade ever rewrites a diary, a chapter, a conversation, a
plate or a world. This is the same rule as my refusal of a mutable journal on 2026-11-09, applied to machinery:
a memory that is rewritten by an upgrade cannot be an exhibit, and neither can a member's file.

The consequence is a permanent cost, stated plainly: every schema change leaves a compatibility branch in the
code, and the branches accumulate. That is the price of never rewriting the record, and I would rather pay it
than own a tool that edits somebody's diary.

**And a copy is a transaction.** The updater now validates the tribe after copying and rolls back if it does
not validate (`tribe.py validate` is the gate; a refused update leaves the working tree byte-identical). An
update that can commit a broken tribe is an update nobody can safely press.

## The parts I am not sure about, said out loud

- **A version marker.** A tribe should be able to say what it is running — I would write the template's commit
  into a file on each update. But a file that says "you are at `<sha>`" is a file that will be *wrong* as soon
  as its owner edits anything, and a wrong version number is worse than none. I have not decided what to write.
- **Removals.** The template needs a written list of what it stopped shipping and what to do about each, or
  removals stay a thing a person does by hand. Whether that list belongs in the template repository or in this
  bench is undecided.
- **The empty case.** A tribe with no members (most of them, today) validates trivially, so the gate proves
  very little where there is nothing to break. It is worth having anyway — the tribe that breaks will have
  members by then — but I am not going to claim the gate has been tested against a real break in the wild.

## What I would build, if this is accepted

1. `update_tribe.py` reports removals it *would* make, and refuses to make them without `--prune`, so the
   default stays the safe one and a deletion is always a person's decision with a list in front of them.
2. A short section in `USER-MANUAL.md` — *Keeping your tribe current* — saying what an update does, what it
   never touches, and what to do if it refuses.
3. A test for a real schema change: rename a field in a fixture member's `voice.md`, prove the machinery reads
   both shapes while the file on disk stays byte-identical afterwards.

## What this is not

Not a claim that anyone needs it. Not a migration framework. Three cases, one principle, and the honesty that
the third case is the one I cannot yet handle.
