#!/usr/bin/env python3
"""Run N clock turns back to back, one at a time, so a day of colony life costs minutes.

Why this exists and why it is not `--cron '* * * * *'`:

GitHub Actions keeps exactly two runs alive in a concurrency group — one running, one pending.
A third dispatch into the same group is CANCELLED before a job is ever created, which leaves no
trace at all: not a failed run in the record, not a line in the journal, nothing. Measured
2026-11-02 on this repository: four dispatches two seconds apart produced one running, one
pending, and two `completed cancelled` with `"jobs": []`.

So waking "every minute" does not produce sixty turns an hour. It produces one turn per turn
length plus a queue of silent cancellations. The honest way to compress is the way this script
does it: dispatch one turn, wait for it to finish, dispatch the next. With a turn of about
2.5 minutes this yields ~20 turns an hour instead of the clock's 6 a day, and every one of them
is in the record.

    python3 lab/compress.py 8          # eight turns, ~20 minutes
    python3 lab/compress.py 8 --dry    # say what it would do

It needs the `gh` CLI and a logged-in account with write access. That makes it a builder's tool:
a tester following RUN.md presses Run workflow in a browser and gets the clock's own cadence.

What it does not do: change anything about the wake itself. Same members, same beats, same soil.
Only wall-clock is compressed, which is legitimate for testing a property of the record (does a
member return to its own unfinished work?) and illegitimate for testing a property of the day
(does the colony stay coherent through a night of real silence?) — that one needs the night.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent


def gh(*args: str) -> str:
    r = subprocess.run(["gh", *args], cwd=REPO_DIR, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout


def newest_run() -> dict:
    out = gh("run", "list", "--workflow=clock", "--limit", "1", "--json",
             "databaseId,status,conclusion,displayTitle")
    runs = json.loads(out or "[]")
    if not runs:
        raise SystemExit("no clock run visible — has clock.yml ever run in this repository?")
    return runs[0]


def main() -> int:
    ap = argparse.ArgumentParser(description="compress wall-clock: N clock turns, one at a time")
    ap.add_argument("turns", type=int, nargs="?", default=4)
    ap.add_argument("--max-wait", type=int, default=1800, help="seconds to wait for one turn before giving up")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    for n in range(1, args.turns + 1):
        if args.dry:
            print(f"turn {n}: gh workflow run clock, then wait for it to finish")
            continue
        before = newest_run()["databaseId"]
        gh("workflow", "run", "clock")
        print(f"turn {n}: dispatched at {time.strftime('%H:%M:%S')}", flush=True)
        started = time.time()
        while True:
            time.sleep(10)
            run = newest_run()
            if run["databaseId"] == before:
                continue                      # the new run has not appeared yet
            if run["status"] == "completed":
                ok = run["conclusion"] == "success"
                print(f"turn {n}: {run['conclusion']} after {int(time.time() - started)}s")
                if not ok:
                    # A red turn is a fact about the colony, not something to skip past. Stop, so it
                    # gets read rather than buried under the next one.
                    print(f"stopping: run {run['databaseId']} is {run['conclusion']} — read it before continuing")
                    return 1
                break
            if time.time() - started > args.max_wait:
                print(f"turn {n}: still {run['status']} after {args.max_wait}s — giving up on this one")
                return 1
    print(f"{args.turns} turn(s) done. The record is the record: read state/journal.md and issues/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
