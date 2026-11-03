#!/usr/bin/env python3
"""Write the facts a member cannot look up: what the index has actually done, as of now.

A wake is one model call with no tools. It cannot fetch a price, and a member asked to predict an index
close will otherwise produce a confident number from training data that stopped months ago. The design's
answer is the one §5 gives for every other missing fact: hand it the evidence in a file and say where the
file came from. This writes that file.

    python3 lab/dow.py                       # today's session, written to facts/dow-<today>.md
    python3 lab/dow.py --date 2026-11-04     # tomorrow, after the close, for the scoring round

Source: the public Yahoo Finance chart endpoint, no key. The file records the URL, the moment it was
fetched, and whether the last bar is a closed session or a session still running — because "the Dow is
51,716" means something different at 10:33 in the morning than it does at 4:01 in the afternoon, and a
member that is not told the difference will treat a moving number as a settled one.
"""
from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EDJI?range=10d&interval=1d"


def fetch(url: str = URL) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "ai-tribe-bench/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def sessions(payload: dict) -> list[dict]:
    result = payload["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    out = []
    for t, o, h, l, c in zip(result["timestamp"], quote["open"], quote["high"], quote["low"], quote["close"]):
        if c is None:
            continue
        out.append({"when": datetime.fromtimestamp(t, timezone.utc),
                    "open": o, "high": h, "low": l, "close": c})
    return out


def render(rows: list[dict], meta: dict, target: str, url: str = URL) -> str:
    now = datetime.now(timezone.utc)
    last = rows[-1]
    live = meta.get("regularMarketTime") and meta.get("regularMarketPrice") is not None
    last_day = last["when"].date()
    today = now.date()
    running = live and last_day == today and now.hour < 21      # 21:00Z is the US close in winter
    out = [
        f"# The index, as of {now:%Y-%m-%d %H:%M} UTC",
        "",
        f"Written by `lab/dow.py` from {url} — the public Yahoo Finance chart endpoint, no key, not a "
        "trading feed. Nothing here is a forecast. If a number below disagrees with your memory, the "
        "number is what the endpoint returned and your memory is training data.",
        "",
        "## The last sessions (close, in points)",
        "",
        "| session | open | high | low | close |",
        "|---|---|---|---|---|",
    ]
    for r in rows[-6:]:
        out.append(f"| {r['when']:%Y-%m-%d} | {r['open']:,.1f} | {r['high']:,.1f} | {r['low']:,.1f} "
                   f"| {r['close']:,.1f} |")
    out.append("")
    if running:
        out += [f"**The {last_day} session is still running.** As of {now:%H:%M} UTC the index stood at "
                f"{meta['regularMarketPrice']:,.2f}, which is not a close and may not become one. The "
                f"figures in the table for {last_day} are the same moving numbers, not a settled result.", ""]
    else:
        out += [f"**The {last_day} session has closed** at {last['close']:,.1f}.", ""]
    changes = [rows[i]["close"] - rows[i - 1]["close"] for i in range(1, len(rows))]
    if changes:
        out += ["## How much this index moves in a day, measured over the same window", "",
                f"- daily changes: min {min(changes):+,.1f}, max {max(changes):+,.1f}, "
                f"mean {sum(changes) / len(changes):+,.1f} points",
                f"- mean absolute daily change: {sum(abs(c) for c in changes) / len(changes):,.1f} points",
                "",
                "That last figure is the useful one: it is roughly the size of error you should expect "
                "from any honest guess about a single session, including your own.", ""]
    out += [f"## The question this file is for: the close on {target}", "",
            "- You have no tools this wake and no way to look anything up. This file is the whole of what "
            "you know about the market.",
            "- Begin the file you write with a line of exactly this shape, so it can be compared without "
            "anyone interpreting your prose: `PREDICTION: <a number, points, no commas>`",
            "- Then give: a confidence (a percentage, honestly — 100% is a claim about the world, not a "
            "mood), the two facts from this file you actually relied on, and the thing that would prove "
            "you wrong if it happened before the close.",
            "- You may decline to predict. If you do, say what you would need in order to answer, and let "
            "the comparison below record a refusal rather than a coin flip dressed as a forecast.", ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="write the market facts a wake cannot fetch")
    ap.add_argument("--date", default="", help="the session whose close is being predicted (default: tomorrow)")
    ap.add_argument("--out", default="", help="where to write (default: facts/dow-<today>.md)")
    ap.add_argument("--url", default=URL)
    a = ap.parse_args(argv)
    try:
        payload = fetch(a.url)
    except Exception as e:                                   # noqa: BLE001 — say it, do not fake it
        print(f"!! could not fetch the index: {e}")
        print("   nothing was written. A facts file invented from memory is worse than no facts file, "
              "because a member cannot tell the difference once it is on disk.")
        return 2
    result = payload["chart"]["result"][0]
    rows = sessions(payload)
    if not rows:
        print("!! the endpoint answered but had no closes in it — nothing written")
        return 2
    target = a.date or (date.fromordinal(rows[-1]["when"].date().toordinal() + 1)).isoformat()
    out = Path(a.out) if a.out else ROOT / "facts" / f"dow-{rows[-1]['when']:%Y-%m-%d}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(rows, result["meta"], target, a.url), encoding="utf-8")
    try:
        shown = out.relative_to(ROOT)
    except ValueError:                       # --out outside the repository: say the path, not a traceback
        shown = out
    print(f"wrote {shown}")
    print(f"   last session {rows[-1]['when']:%Y-%m-%d} close {rows[-1]['close']:,.1f}; "
          f"question is the close on {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
