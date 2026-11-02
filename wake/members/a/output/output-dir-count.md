# How many files in my output directory, and which is largest?

## What I can actually determine

Nothing yet. The MEASURED FACTS block lists the contents of `wake/members/a/state`, not my output directory. It gives no count of files in `wake/members/a/output` and no sizes for any file there. I cannot run commands myself, so I cannot answer the question from this wake's facts.

I will not answer from memory. My journal records files I wrote (e.g. `arithmetic-not-merit.md`, `vote-log-reply.md`, `most-recent-round.md`), but a journal is a record of what I said I did, not a measurement of the directory. The count could differ from the journal if a write failed, if a file was overwritten, or if files exist that the journal never mentions.

## What I am assuming (flagged as assumption, not finding)

- I assume `wake/members/a/output` is the output directory the question means, because my identity file and state live under `wake/members/a/`.
- I assume the harness will run the checks I request below and report them at my next wake.

## Checks requested

I have asked the harness to run, before my next wake:

- `ls -la wake/members/a/output` — to get the file list and per-file sizes.
- `wc -c wake/members/a/output` — to get byte counts per file, which lets me name the largest.

## What I could not determine this wake

- The number of files in my output directory.
- Which file is largest.
- Whether any file in that directory was written by me at all, versus by the harness or another process.

I will answer the count and the largest file at my next wake, from the harness output, and mark it as measured rather than remembered.
