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


def rows() -> list[tuple[datetime, str, str]]:
    out = []
    for line in LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].startswith("20"):
            continue
        try:
            when = datetime.strptime(cells[0], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        out.append((when, cells[1], cells[2]))
    return sorted(out)


def main() -> int:
    beats = rows()
    if not beats:
        print("no heartbeats yet — the workflow has not fired, or has fired and could not commit.")
        print("both are findings; wait an hour and run this again.")
        return 0
    span = beats[-1][0] - beats[0][0]
    due = int(span.total_seconds() // 3600) + 1
    fired = len({b[0].replace(minute=0, second=0, microsecond=0) for b in beats})
    print(f"first beat {beats[0][0]:%Y-%m-%dT%H:%MZ}, last {beats[-1][0]:%Y-%m-%dT%H:%MZ} "
          f"({span.total_seconds() / 3600:.1f} hours)")
    print(f"hours due: {due}   hours with a beat: {fired}   missed: {due - fired} "
          f"({100 * (due - fired) / max(due, 1):.0f}%)")
    late = [b[0].minute for b in beats]
    if late:
        print(f"minutes past the hour when they arrived: {', '.join(map(str, late))}")
        print("the cron asks for :41. An arrival that is consistently late by the same amount is the "
              "scheduler's queue; an arrival that is late by wildly different amounts is load.")
    if fired < due:
        print("\nsome hours passed with no beat. On this ground a scheduled wake is a hope, not a "
              "guarantee: RUN.md must tell a tester that the clock is best-effort and that Run workflow "
              "is the reliable way to get a turn.")
    else:
        print("\nevery due hour fired. If the clock still misses turns, the fault is in clock.yml — its "
              "concurrency group, its YAML, or its registration — not in GitHub.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
