#!/usr/bin/env python3
"""One wake. Read the state files, ask a small model to choose one open item and act on it,
write down what it did — including when what it did was nothing usable.

Run by .github/workflows/wake.yml on a free runner. The instance does not survive the job;
only the files in this repository do.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "state"
OUTPUT = ROOT / "output"

PROMPT = """You are {identity_name}. You have just woken up with no memory. Everything you know is
the text below, which you wrote in a previous wake.

=== YOUR IDENTITY ===
{identity}

=== YOUR STATE ===
{state}

=== YOUR OPEN ITEMS ===
{items}

=== WHAT YOU MUST DO NOW ===
Choose exactly ONE item from the list above and act on it. You are a member of a tribe, not a
chatbot: a wake that produces only commentary has failed. Your act must be a file you write.

Reply with JSON only, exactly this shape, no prose before or after:

{{
  "chosen_item": "the number and first few words of the item you chose",
  "why": "one sentence, concrete, naming what in the state made you choose it",
  "action": "write_file",
  "path": "wake/output/<short-name>.md",
  "content": "<the file you are writing; at least 200 characters; plain markdown>",
  "journal": "two or three sentences: what you did, and anything you could not do"
}}

If no item can be acted on, use "action": "no_action", omit path and content, and say in
"journal" exactly what blocked you. Refusing with a reason is allowed. Producing a plausible
paragraph with no act in it is not, and it will be recorded as a failure of the wake.
"""


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else "(missing)"


def identity_name(text: str) -> str:
    m = re.search(r"\*\*(.+?)\*\*", text)
    return m.group(1) if m else "the member"


def ask(host: str, model: str, prompt: str) -> tuple[str, dict]:
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.4, "num_predict": 900, "num_ctx": 4096},
        }
    ).encode()
    req = urllib.request.Request(
        f"{host}/api/generate", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        payload = json.loads(r.read().decode())
    return payload.get("response", ""), payload


def parse(reply: str) -> dict | None:
    try:
        return json.loads(reply)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", reply, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def safe_path(p: str) -> Path | None:
    name = Path(p).name
    if not name or name in {".", ".."}:
        return None
    return OUTPUT / name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--host", default="http://127.0.0.1:11434")
    args = ap.parse_args()

    OUTPUT.mkdir(parents=True, exist_ok=True)
    identity, state, items = (
        read(STATE / "identity.md"),
        read(STATE / "state.md"),
        read(STATE / "open-items.md"),
    )
    prompt = PROMPT.format(
        identity_name=identity_name(identity), identity=identity, state=state, items=items
    )
    print(f"=== prompt ({len(prompt)} chars) ===")
    print(prompt)

    t0 = time.time()
    reply, payload = ask(args.host, args.model, prompt)
    elapsed = time.time() - t0

    print(f"\n=== raw reply after {elapsed:.1f}s ===")
    print(reply)

    (OUTPUT / f"raw-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json").write_text(
        reply, encoding="utf-8"
    )

    verdict = "FAILED: the reply was not JSON"
    written = "(none)"
    question = "?"
    jtext = ""

    parsed = parse(reply)
    if parsed:
        question = str(parsed.get("chosen_item", "?"))[:80]
        jtext = str(parsed.get("journal", "")).strip()
        if parsed.get("action") == "write_file":
            target = safe_path(str(parsed.get("path", "")))
            content = str(parsed.get("content", "")).strip()
            if target is None:
                verdict = "FAILED: no usable path"
            elif len(content) < 200:
                verdict = f"FAILED: content was only {len(content)} characters"
                target.write_text(content + "\n", encoding="utf-8")
                written = target.name
            else:
                target.write_text(content + "\n", encoding="utf-8")
                written = target.name
                verdict = "OK: chose an item and wrote a file"
        elif parsed.get("action") == "no_action":
            verdict = "REFUSED: no item could be acted on"
        else:
            verdict = f"FAILED: unknown action {parsed.get('action')!r}"

    now = datetime.now(timezone.utc)
    evals = payload.get("eval_count", "?")
    with (STATE / "journal.md").open("a", encoding="utf-8") as f:
        f.write(
            f"\n## {now:%Y-%m-%d %H:%M} UTC — {args.model}\n\n"
            f"- Verdict: **{verdict}**\n"
            f"- Item chosen: {question}\n"
            f"- File written: {written}\n"
            f"- Tokens generated: {evals}; wall clock: {elapsed:.1f}s\n"
            f"- In its own words: {jtext or '(no journal field)'}\n"
        )

    s = read(STATE / "state.md")
    wakes = int((re.search(r"Wakes so far:\s*(\d+)", s) or [0, 0])[1]) + 1
    s = re.sub(r"Wakes so far:\s*\d+", f"Wakes so far: {wakes}", s)
    s = re.sub(r"Last wake:.*", f"Last wake: {now:%Y-%m-%d %H:%M} UTC", s)
    s = re.sub(r"Model used:.*", f"Model used: {args.model}", s)
    (STATE / "state.md").write_text(s, encoding="utf-8")

    print(f"\n=== verdict: {verdict} ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
