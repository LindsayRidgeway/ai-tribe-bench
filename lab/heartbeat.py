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

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE / "heartbeat.md"
CONTROL = HERE.parent / ".github" / "workflows" / "heartbeat.yml"

# The control asked for one beat an hour (:41) until 2026-11-03T14:00Z, when it began asking four
# times (:11 :26 :41 :56) to test one question: are scheduled runs dropped *per event* or for whole
# periods? This constant is the one thing in this file that is a claim rather than a reading — the log
# records "schedule", not which of the four cron lines fired — so it is named as a claim and dated.
FOUR_SINCE = datetime(2026, 11, 3, 14, 0, tzinfo=timezone.utc)
BASELINE = [41]   # what the control asked for before FOUR_SINCE, and the only honest yardstick for
                  # beats that arrived before it. Reading yesterday's arrivals against today's four
                  # offsets made the 10:01 beat look six minutes late for a slot (:56) nobody had
                  # asked for yet — the tool inventing a schedule it never kept.


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


def offsets(control: Path | None = None) -> list[int]:
    """The minutes past the hour the control asks for, READ from the workflow.

    Not restated here: a tool holding its own copy of the schedule is the same defect as a sheet and a
    shell spelling one key two ways. If the workflow gains a cron line, this follows it.
    """
    control = control or CONTROL
    out, text = [], control.read_text(encoding="utf-8") if control.exists() else ""
    for line in text.splitlines():
        m = re.match(r"\s*-\s*cron:\s*[\"'](\d+)\s", line)
        if m:
            out.append(int(m.group(1)))
    return sorted(set(out)) or [41]


def minutes_late(beat: datetime, offs: list[int]) -> float:
    """How late, against the most recent slot that was already due when this beat arrived.

    The first version printed `beat.minute` and called it lateness, which read the 10:01 beat as
    arriving one minute past the hour and therefore *early*, when it was the 09:41 slot arriving
    twenty minutes late. A one-number summary of lateness has to know which slot it belongs to.
    """
    hour = beat.replace(minute=0, second=0, microsecond=0)
    best = None
    for back in range(0, 7):
        for o in offs:
            slot = hour - timedelta(hours=back) + timedelta(minutes=o)
            if slot <= beat:
                d = (beat - slot).total_seconds() / 60
                best = d if best is None else min(best, d)
    return best if best is not None else 0.0


def main(log: Path | None = None, now: datetime | None = None) -> int:
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
    # ...and it ends at NOW, not at the last beat. A window that closes on the last observation cannot
    # contain a silence, and a silence is the thing being measured: on the morning of 2026-11-03 this
    # printed "hours due: 9, missed: 7 (78%)" when three further hours had already passed with nothing at
    # all — the quiet hours at the end of a window are exactly what a stalled scheduler produces, and
    # closing the window on the last beat hid them. The current hour counts only once its :41 has passed.
    now = now or datetime.now(timezone.utc)
    first, last = scheduled[0][0], scheduled[-1][0]
    span = last - first
    end = now.replace(minute=0, second=0, microsecond=0)
    if now.minute < 41:
        end -= timedelta(hours=1)
    due = int((end - first.replace(minute=0, second=0, microsecond=0)).total_seconds() // 3600) + 1
    fired = len({b[0].replace(minute=0, second=0, microsecond=0) for b in scheduled})
    hand_in_window = sum(1 for b in beats if b[1] != "schedule" and b[0] >= first)
    print(f"first scheduled beat {first:%Y-%m-%dT%H:%MZ}, last {last:%Y-%m-%dT%H:%MZ} "
          f"({span.total_seconds() / 3600:.1f} hours between them; the window is closed at "
          f"{end:%Y-%m-%dT%H:%MZ}, not at the last beat)")
    print(f"hours due: {due}   hours with a scheduled beat: {fired}   missed: {due - fired} "
          f"({100 * (due - fired) / max(due, 1):.0f}%)")
    if hand_in_window:
        print(f"{hand_in_window} hand dispatch(es) fall inside the window and do NOT count as beats.")
    offs = offsets()
    asked = ":" + " :".join(f"{o:02d}" for o in offs)
    late = [minutes_late(b[0], offs if b[0] >= FOUR_SINCE else BASELINE) for b in scheduled]
    print(f"minutes late, against the slot already due when each arrived: "
          f"{', '.join(f'{d:.0f}' for d in late)}  (the control asks for {asked} now, for :41 then)")
    if len(late) > 1:
        print("the same lateness every time is a queue; wildly different lateness is load. One arrival "
              "can tell you neither.")
    # The four-offset hour tests a narrower question than "does the scheduler work": whether a lost beat
    # is one event lost or a stretch of time lost. Four independent asks per hour distinguish them.
    per_hour = len(offs)
    since = max(first, FOUR_SINCE)
    if now > FOUR_SINCE:
        hours_since = int((end - since.replace(minute=0, second=0, microsecond=0))
                          .total_seconds() // 3600) + 1
        events_due = max(hours_since, 0) * per_hour
        arrived = sum(1 for b in scheduled if b[0] >= since)
        print(f"\nsince the control asked {per_hour}x an hour: events due {events_due}, arrived {arrived}. "
              f"(The hours-due figure above asks for {per_hour}x that many events.)")
        if events_due and arrived:
            share = 100 * arrived / events_due
            # The number worth comparing is not "a fifth" — that was hardcoded, and the share it described
            # was 6% the first time this printed. It is the per-event share now against the per-hour share
            # over the stretch when the control still asked once an hour. If four asks buy four times the
            # wakes, the loss is per-event; if they buy the same, the loss is a stretch of time, and no
            # number of cron lines will fill it.
            base_hours = int((since.replace(minute=0, second=0, microsecond=0)
                              - first.replace(minute=0, second=0, microsecond=0)).total_seconds() // 3600)
            before_arrived = sum(1 for b in scheduled if b[0] < since)
            before = 100 * before_arrived / base_hours if base_hours > 0 else None
            if before is None:
                print(f"a wake arrived for {share:.0f}% of the {events_due} events asked for since the control "
                      f"went to {per_hour} an hour, and there is no earlier hourly stretch in this window to "
                      "compare it with. A remedy is still named rather than waiting: a lost stretch of time is "
                      "filled by a timer this colony owns (RUN.md §8, lab/pinger.gs), not by a louder cron.")
            elif share <= before * 1.5:
                print(f"a wake arrived for {share:.0f}% of the {events_due} events asked for, against "
                      f"{before:.0f}% of the {base_hours} hours asked for when the control asked once an hour. "
                      f"{per_hour} asks did not buy {per_hour} times the wakes: the loss is a stretch of time "
                      "with no deliveries in it, not single events dropped, and asking more often will not fix "
                      "it. An hourly timer outside GitHub (RUN.md §8, lab/pinger.gs) is the fix.")
            elif share > 75:
                print(f"most events arriving ({share:.0f}%) although hours went missing when the control "
                      "asked once: the loss is per-event, so redundant cron lines are a floor — and still a "
                      "floor, not a guarantee. lab/pinger.gs is what makes it certain.")
            else:
                print(f"between a half again as many and three quarters of the events arrive ({share:.0f}%): "
                      "partial loss, so neither redundant crons nor a single external timer is enough on its "
                      "own. Keep both.")
    if fired < due:
        print("\nsome hours passed with no beat. On this ground a scheduled wake is a hope, not a "
              "guarantee. The remedy is a timer this colony owns rather than a louder cron: RUN.md §8 "
              "ranks Run workflow, a hand wake, @tribe and then the cron, and lab/pinger.gs is the free "
              "hourly pulse outside GitHub.")
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
