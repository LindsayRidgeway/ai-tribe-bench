#!/usr/bin/env python3
"""Compare predictions the members wrote, against what actually happened.

The second half of the 2026-11-03 experiment: three members asked the same sealed question, then handed
the result and each other's answers, to say who was closest and what the miss showed. This tool does the
arithmetic so that the comparison is a file rather than a vibe, and so that the member doing the comparing
cannot quietly pick which numbers to notice.

    python3 lab/dow.py --date 2026-11-04          # the facts, including the settled close
    python3 lab/compare.py --actual 51900         # reads the PREDICTION lines, writes the comparison

A prediction is only readable if it was written in the one shape the tool can parse, which is why the
question asks for a first line of `PREDICTION: <number>`. Everything else in a work is prose, and prose is
for the member reading it, not for the tool.
"""
from __future__ import annotations

import argparse
import re
import statistics
from datetime import date, datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRED = re.compile(r"^\s*PREDICTION:\s*([\d,]+(?:\.\d+)?)", re.M | re.I)
CONF = re.compile(r"confiden\w*[^.\n]{0,40}?(\d{1,3})\s*%", re.I)
HEAD = re.compile(r"^---\n(.*?)\n---\n", re.S)


def header(text: str) -> dict:
    m = HEAD.match(text)
    out = {}
    if not m:
        return out
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def predictions(root: Path | None = None, also: list[str] | None = None) -> list[dict]:
    root = root or ROOT
    found = []
    files = sorted((root / "works").glob("*/*.md"))
    # `--also` reads a second place for predictions. The three-Goose-sessions version of the experiment
    # (2026-11-03) writes its answers to `experiment/`, because a chat session files no work: the member's
    # answer is a file a person asked for, not one the harness filed. Same scoring, different shelf.
    for extra in (also or []):
        files += sorted((root / extra).glob("*.md"))
    for p in files:
        text = p.read_text(encoding="utf-8")
        m = PRED.search(text)
        if not m:
            continue
        h = header(text)
        c = CONF.search(text)
        # In `works/<member>/x.md` the member is the directory; in `experiment/remy.md` it is the file stem.
        # Without this the chat-session answers were all scored as a member called "experiment".
        who = p.parent.name if p.parent.parent.name == "works" else p.stem
        found.append({
            "member": who,
            "file": str(p.relative_to(root)),
            "value": float(m.group(1).replace(",", "")),
            "confidence": int(c.group(1)) if c else None,
            "when": (h.get("when") or "").strip() or None,
            "title": h.get("title", p.stem),
        })
    # One prediction per member: the last one filed. A member that re-predicted after seeing the result
    # must not have its second guess scored — that is the one way this comparison could flatter anybody.
    latest: dict[str, dict] = {}
    for f in found:
        key = (str(f["when"] or ""), f["file"])
        if f["member"] not in latest or key > (str(latest[f["member"]]["when"] or ""),
                                               latest[f["member"]]["file"]):
            latest[f["member"]] = f
    return sorted(latest.values(), key=lambda f: f["member"])


def render(rows: list[dict], actual: float, target: str, daily_move: float | None) -> str:
    out = [f"# The predictions, against the close on {target}", "",
           f"Assembled by `lab/compare.py` on {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC from the "
           f"`PREDICTION:` line in each member's most recent work. The actual close is **{actual:,.1f}**.", ""]
    if not rows:
        return "\n".join(out + ["No member wrote a line beginning `PREDICTION:`. Nothing to compare — which "
                                "is itself the result: an answer in prose cannot be checked by anybody, "
                                "including its author.", ""])
    out += ["| member | predicted | off by | confidence |", "|---|---|---|---|"]
    errors = []
    for r in rows:
        e = r["value"] - actual
        errors.append(abs(e))
        out.append(f"| {r['member']} | {r['value']:,.1f} | {e:+,.1f} | "
                   f"{str(r['confidence']) + '%' if r['confidence'] is not None else '—'} |")
    out.append("")
    best = min(rows, key=lambda r: abs(r["value"] - actual))
    worst = max(rows, key=lambda r: abs(r["value"] - actual))
    out += [f"Closest: **{best['member']}**, off by {abs(best['value'] - actual):,.1f} points. "
            f"Furthest: **{worst['member']}**, off by {abs(worst['value'] - actual):,.1f} points.", ""]
    if len(rows) > 1:
        spread = statistics.pstdev([r["value"] for r in rows])
        out += [f"The three predictions spread {spread:,.1f} points apart (population standard deviation) "
                f"and the errors ranged {min(errors):,.1f}–{max(errors):,.1f}.", ""]
    out += ["**What this comparison is not.** Three guesses on one session, one of which happened to land "
            "nearest. That is not evidence that the nearest one predicts better, and it would take dozens "
            "of sessions to say anything of the kind. What it can show is whether a member's *stated "
            "reasoning* bore any relation to the number it gave, and whether it can say plainly that it "
            "was wrong.", ""]
    if daily_move:
        out += [f"**The size of the noise.** Over the window in the facts file the index moved "
                f"{daily_move:,.1f} points on an average day, ignoring direction. An error smaller than "
                f"that is what a coin flip produces; an error larger than it is not a near miss.", ""]
    out += ["## The works themselves", ""]
    for r in rows:
        out += [f"- **{r['member']}** — `{r['file']}` — *{r['title']}*"]
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="compare filed predictions to an actual close")
    ap.add_argument("--actual", type=float, required=True, help="the settled close, in points")
    ap.add_argument("--target", default=date.today().isoformat(), help="the session the close belongs to")
    ap.add_argument("--daily-move", type=float, default=None,
                    help="mean absolute daily change, so the comparison can say what noise looks like")
    ap.add_argument("--also", action="append", default=[],
                    help="an extra directory to read predictions from, e.g. --also experiment")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    rows = predictions(also=a.also)
    text = render(rows, a.actual, a.target, a.daily_move)
    out = Path(a.out) if a.out else ROOT / "facts" / f"comparison-{a.target}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    try:
        shown = out.relative_to(ROOT)
    except ValueError:
        shown = out
    print(text)
    print(f"wrote {shown}")
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
