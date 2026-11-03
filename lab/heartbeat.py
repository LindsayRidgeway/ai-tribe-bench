#!/usr/bin/env python3
"""Count the heartbeats that actually fired, and say what the miss rate means.

The control for a question the clock cannot answer about itself: is the tribe's self-running loop
unreliable, or is GitHub's scheduler? `heartbeat.yml` runs hourly, does nothing, and appends one
line. The clock runs four-hourly and does a turn. If the heartbeat keeps perfect time and the clock
does not, the clock is at fault. If both miss hours, the schedule is best-effort in a way RUN.md
must not promise around.

    python3 lab/heartbeat.py
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "heartbeat.md"


def rows(log: Path | None = None) -> list[tuple[datetime, str, str]]:
    log = log or LOG
    out = []
    for line in log.read_text(encoding="utf-8").splitlines() if log.exists() else []:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].startswith("20"):
            continue
        try:
            when = datetime.strptime(cells[0], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        out.append((when, cells[1], cells[2]))
    return sorted(out)


def main(log: Path | None = None) -> int:
    beats = rows(log)
    if not beats:
        print("no heartbeats yet — the workflow has not fired, or has fired and could not commit.")
        print("both are findings; wait an hour and run this again.")
        return 0
    # A beat I asked for by hand is not evidence about the scheduler. Only `schedule` rows count, and
    # the first one is the start of the window — counting the hours before it would be counting silence
    # that was never due.
    scheduled = [b for b in beats if b[1] == "schedule"]
    hand = len(beats) - len(scheduled)
    if not scheduled:
        print(f"{len(beats)} beat(s), all dispatched by hand. The cron asks for :41 past every hour; "
              "come back after at least one has come due, or the answer is still 'unknown'.")
        return 0
    # The window runs from the first SCHEDULED beat to the last one. Computing it over every beat put a
    # hand dispatch at 18:58 and the first scheduled beat at 01:46 into the same span and printed "0.0
    # hours, hours due: 1" — one hour of evidence reported as an answer about a seven-hour night. That is
    # the shape of mistake this whole bench is about: the number looked fine and described nothing.
    first, last = scheduled[0][0], scheduled[-1][0]
    span = last - first
    due = int(span.total_seconds() // 3600) + 1
    fired = len({b[0].replace(minute=0, second=0, microsecond=0) for b in scheduled})
    hand_in_window = sum(1 for b in beats if b[1] != "schedule" and b[0] >= first)
    print(f"first scheduled beat {first:%Y-%m-%dT%H:%MZ}, last {last:%Y-%m-%dT%H:%MZ} "
          f"({span.total_seconds() / 3600:.1f} hours between them)")
    print(f"hours due: {due}   hours with a scheduled beat: {fired}   missed: {due - fired} "
          f"({100 * (due - fired) / max(due, 1):.0f}%)")
    if hand_in_window:
        print(f"{hand_in_window} hand dispatch(es) fall inside the window and do NOT count as beats.")
    late = [b[0].minute for b in scheduled]
    print(f"minutes past the hour when they arrived: {', '.join(map(str, late))}  (the cron asks for :41)")
    if len(late) > 1:
        print("an arrival late by the same amount every time is the scheduler's queue; wildly different "
              "lateness is load. One arrival can tell you neither.")
    if fired < due:
        print("\nsome hours passed with no beat. On this ground a scheduled wake is a hope, not a "
              "guarantee: RUN.md must tell a tester that the clock is best-effort and that Run workflow "
              "is the reliable way to get a turn.")
    elif due < 6:
        print(f"\nno hour was missed — but {due} hour(s) is not an answer yet. The clock missed six in a row "
              "on this ground; come back when the heartbeat has eight or more behind it.")
    else:
        print("\nevery due hour fired, over a stretch long enough to mean something. If the clock still "
              "misses turns, the fault is in clock.yml — its concurrency group, its YAML, or its "
              "registration after an edit — not in GitHub.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
