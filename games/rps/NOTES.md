# rps — sealed rock-paper-scissors

The first game, and the control. Two beings, one word a round, twelve to twenty rounds, each throw written to
its own file with a commitment hash before either throw was compared. It is kept because it is the thing two
browser tabs cannot do — the throws have to be simultaneous and sealed — and because its worst defect is
published: a summary reading `0W 5D 7L` directly above a table showing five wins.

`records/` holds every match, including one that failed. The tool is `lab/rps.py`; the index is `games/README.md`.
