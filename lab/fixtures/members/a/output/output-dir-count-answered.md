# Output directory: count and largest file

## What I can determine from the check

The harness ran `ls -la wake/members/a/output` and its output is in MEASURED FACTS. Counting the regular-file entries (excluding `.` and `..`) gives **23 files**.

Largest by byte size, from the `ls -la` size column:

- `raw-20261102T022235Z.json` — 4044 bytes
- `raw-20261102T021547Z.json` — 4008 bytes
- `raw-20261102T021255Z.json` — 3598 bytes

So the largest file is **`raw-20261102T022235Z.json` at 4044 bytes**.

## What I am assuming

- That `ls -la` size is in bytes (standard for this format).
- That "files" means regular files, not the directory entries `.` and `..`.
- That the listing is complete and current as of the check time (02:44 UTC).

## What I could not determine

- The content of the largest file, or whether it is meaningful — only its size.
- Whether any file changed between the check and now.
- A byte-exact total; I did not sum the column, only ranked it.

## Note on my earlier wake

At 02:44 I wrote `output-dir-count.md` saying I could not answer because only the state directory was listed. That was correct then. This wake the output listing exists, so the answer is now available. I am not going along with my earlier "cannot answer" — I am updating it against the check.
