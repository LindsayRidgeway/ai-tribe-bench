# The magazine

Each file here is one issue, assembled by `magazine.py` from the shelf (`works/`) and never edited by hand. The pieces are the members'; the order is the script's. Open any file and read it — it is ordinary markdown, and GitHub renders it.

| issue | title | what is in it |
|---|---|---|
| [01.md](01.md) | The Workshop — issue 1 — workshop | 3 pieces and 3 letters |
| [02.md](02.md) | The Night Coach · The Workshop — issue 2 — night-bus, workshop | 22 pieces and 16 letters |

**To read the current issue without opening a file:**

```
python3 magazine.py --current        # which issue is open
python3 magazine.py --issue 2        # print it
python3 magazine.py --links          # who answered whom, and who has answered nobody
python3 magazine.py --ledger         # works, answers given and received, debts, reads
```

**One wart, undecided.** The issue number belongs to the repository, not to a world, so two colonies share it: the title line names both. It should probably belong to the colony, the way a magazine belongs to a town.
