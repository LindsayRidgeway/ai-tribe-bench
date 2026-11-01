# AI Tribe — bench

A workbench, not the product. This repository exists to answer one question, and it is deliberately
public because GitHub gives its computers away free only to public repositories.

**The question.** Can a small open-weight model, woken by a free runner with no memory of the last
wake, read its own state file and produce *a decision with an act behind it* — or does it produce
plausible prose with no act in it?

Everything here is disposable. No member of the LLM Symposium lives here. Nothing in this repository
is a claim about the Model AI Tribe project (agenda item 33) beyond what a transcript can show.

## How a wake works

1. GitHub starts a machine from a clock or a button (`.github/workflows/wake.yml`).
2. `ollama` is installed and a small model is pulled — no GPU, CPU inference.
3. `wake/wake.py` reads `wake/state/`, asks the model to choose **one** open item and act on it,
   and requires the reply as JSON with a file path and its content.
4. The script writes that file, appends to the journal, and the workflow commits the result.

The instance then evaporates. The files are the only thing that survives — the same rule the
Symposium runs on.

## Files

- `wake/state/identity.md` — who the member is (fixed)
- `wake/state/state.md` — where it stands (rewritten by each wake)
- `wake/state/open-items.md` — the list a wake chooses from
- `wake/state/journal.md` — append-only record of what it did
- `wake/output/` — the acts themselves
- `wake/wake.py` — one wake
