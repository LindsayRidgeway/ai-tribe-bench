#!/usr/bin/env python3
"""Write the README for one lever experiment.

Two questions, and the first version of this file could not tell them apart:

1. **Was the change in front of the member?** A lever that never reaches the prompt measures nothing.
   On 2026-11-02 the workflow kept the first 4,000 characters of the run log, which ended before THE SOIL
   block began — so "the member ignored the drop" and "the drop never arrived" produced identical
   artifacts, and I read one as the other. The soil block is now cut out of the prompt itself.
2. **Did the wake use it?** Word-by-word against the piece it wrote. Crude on purpose: it is a question a
   machine can answer, and it is not the same question as "is this piece different in kind", which is a
   human's judgement and is left to one.

    python3 lab/analyse_lever.py --out lab/experiments/<dir> --lever drop --member a --place workshop \
        --value "..." --work work.md --soil soil-as-it-saw-it.md --model deepseek-chat --stamp ...
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path


def flat(text: str) -> str:
    return " ".join(text.split()).lower()


def analyse(value: str, work: str, soil: str) -> tuple[bool, list[str]]:
    """Did the change arrive, and did the piece use any of it."""
    value, work, soil = value.strip(), work.strip(), soil.strip()
    arrived = bool(value) and flat(value) in flat(soil)
    words = re.findall(r"[A-Za-z]{5,}", value)[:8]
    used = [w for w in words if re.search(rf"\b{re.escape(w)}\b", work, re.I)]
    return arrived, used


def build(value: str, work: str, soil: str | None, lever: str, member: str, place: str,
          model: str, stamp: str, changed: str) -> str:
    # soil is None when the block could not be cut out of the log at all, which is not the same as "the
    # member was given no ground" — so it says which it is rather than reporting a silent no.
    arrived, used = analyse(value, work, soil or "")
    if soil is None:
        verdict = ("I could not find THE SOIL block in the run log, so I cannot say whether the change "
                   "reached the member. This experiment answers nothing until that is fixed.")
    elif arrived:
        verdict = "yes — the change is in THE SOIL block of its prompt"
    else:
        verdict = "NO — the change is not in the prompt the member was given"
    lines = [
        f"# Lever: {lever}, on member {member} in {place}",
        "",
        f"**What was changed** — `{changed}`:",
        "",
        "```",
        value.strip(),
        "```",
        "",
        f"**Run at** {stamp}, voice {model}.",
        "",
        f"**Did it reach the member?** {verdict}",
        "",
        f"**Did the wake use it?** {', '.join(used) if used else 'no word from the change appears in what it wrote'}",
        "",
    ]
    if soil is not None and not arrived:
        lines += [
            "This experiment measured nothing about the member: the lever was not connected to the prompt. "
            "Fix that before reading the piece.",
            "",
        ]
    lines += [
        "The prompt's soil block is in `soil-as-it-saw-it.md` and the piece is in `work.md`. Whether the "
        "piece is different *in kind* from what it writes at home is a human's judgement, and this file "
        "does not pretend to make it.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("out", "lever", "member", "place", "value", "model", "stamp", "changed"):
        ap.add_argument(f"--{name}", required=True)
    ap.add_argument("--work", default="")
    ap.add_argument("--soil", default="")
    a = ap.parse_args()

    out = Path(a.out)
    work = Path(a.work).read_text(encoding="utf-8", errors="replace") if a.work and Path(a.work).exists() else ""
    soil_path = Path(a.soil) if a.soil else out / "soil-as-it-saw-it.md"
    soil = soil_path.read_text(encoding="utf-8", errors="replace") if soil_path.exists() else None

    text = build(a.value, work, soil, a.lever, a.member, a.place, a.model, a.stamp, a.changed)
    (out / "README.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
