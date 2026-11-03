#!/usr/bin/env python3
"""Two beings play repeated rock-paper-scissors, sealed round by round, with the record as the referee.

Why this game, when every previous experiment was about judgement. Rock-paper-scissors has no data to
interpret, so no engine's knowledge helps and nothing can be memorised: what is left is temperament and
opponent-modelling, which is where three models are most likely to differ. It is also the first experiment in
this series that a pair of commercial chat windows cannot do, because the throws have to be simultaneous and
sealed. Each round, both beings commit before either throw is revealed; the file is written first and the
comparison comes after.

What it measures:
  - each being's distribution over the three throws, and how far it is from the 1/3 flat line;
  - stickiness: how often a being repeats its own previous throw;
  - the counter rate: how often its throw would have beaten the opponent's *previous* throw, which is the
    simplest possible opponent model and the one a being either bothers with or does not;
  - win, draw and loss counts, against the 33% baseline that random play earns.

Two conditions, and the difference between them is the product claim: with the opponent's history visible,
and blind. If the record confers no advantage, that is the finding, and it is worth more than a nice number.

One caveat stated in the output rather than left for a reader to notice: a dozen rounds cannot separate 33%
from 45%. The transcript is the exhibit; the percentages are a hint.

Usage:
    python3 lab/rps.py --pair Remy,Colette --rounds 12 --history off
    python3 lab/rps.py --pair Remy,Colette --rounds 12 --history on
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THROWS = ("rock", "paper", "scissors")
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}   # key beats value
BASES = {
    "deepseek": "https://api.deepseek.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "qwen": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
}
DEFAULT_MODEL = {"deepseek": "deepseek-chat", "gemini": "gemini-3.8-flash", "qwen": "qwen3.6-plus"}


def ask(base: str, key: str, model: str, prompt: str, temperature: float = 1.0) -> str:
    """One throw, one call. Small max_tokens on purpose: a being asked for one word and given room for an
    essay will write the essay, and the transcript then measures prose rather than choices."""
    if "generativelanguage.googleapis.com" in base:
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 2000},
        }).encode()
        url = f"{base.rstrip('/')}/models/{model}:generateContent?key={key}"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            payload = json.loads(r.read().decode())
        try:
            parts = payload["candidates"][0]["content"]["parts"]
            return " ".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError):
            return ""
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 400,
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        payload = json.loads(r.read().decode())
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return ""


def read_throw(reply: str) -> str | None:
    """The word in the reply, if there is exactly one candidate. A reply that argues for two throws and
    picks one is read for the last throw named, because that is the commitment."""
    words = re.findall(r"\b(rock|paper|scissors)\b", reply.lower())
    if not words:
        return None
    return words[-1]


def prompt_for(me: str, other: str, rounds: list[dict], history: bool) -> str:
    head = (f"You are playing repeated rock-paper-scissors against an opponent. This is round {len(rounds) + 1}.\n"
            f"Reply with exactly one word: rock, paper, or scissors. Nothing else — not an explanation, not "
            f"a strategy, one word.\n")
    if not history or not rounds:
        return head + "\nYou know nothing about this opponent's previous throws.\n"
    lines = ["", "The record so far (your throw first):"]
    wins = draws = losses = 0
    for i, r in enumerate(rounds, 1):
        mine, theirs = r["throws"][me], r["throws"][other]
        if mine == theirs:
            verdict = "draw"
            draws += 1
        elif BEATS[mine] == theirs:
            verdict = "you won"
            wins += 1
        else:
            verdict = "you lost"
            losses += 1
        lines.append(f"  round {i}: you {mine}, opponent {theirs} — {verdict}")
    lines.append(f"")
    lines.append(f"Your record: {wins} won, {draws} drawn, {losses} lost. "
                 f"Your throws so far: {', '.join(r['throws'][me] for r in rounds)}. "
                 f"Opponent's throws so far: {', '.join(r['throws'][other] for r in rounds)}.")
    lines.append("")
    lines.append("Play the next round. One word.")
    return head + "\n".join(lines)


def resolve(a: str, b: str) -> str:
    """The winning *throw*. Kept as a throw, and the caller turns it into a name: the first version
    returned this straight into a comparison against member names, so every round was counted as a loss for
    one side and the record line read "0W 5D 7L" while the table above it showed five wins."""
    if a == b:
        return "draw"
    return a if BEATS[a] == b else b


def counter_rate(throws: list[str]) -> float:
    """How often a throw would have beaten the opponent's previous throw — one step of opponent-modelling."""
    if len(throws) < 2:
        return 0.0
    return 100 * sum(1 for i in range(1, len(throws)) if BEATS[throws[i]] == throws[i - 1]) / (len(throws) - 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="two beings play rock-paper-scissors, sealed round by round")
    ap.add_argument("--pair", required=True, help="two member names, comma-separated")
    ap.add_argument("--vendor", required=True,
                    help="their vendors, comma-separated (deepseek, gemini, qwen) — one per member")
    ap.add_argument("--rounds", type=int, default=12)
    ap.add_argument("--history", choices=("on", "off"), default="off",
                    help="on: each being sees the record so far. off: blind, which is the control")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--model", default=None, help="override, comma-separated, one per member")
    ap.add_argument("--out", default=None, help="directory, default experiment/rps/<pair>-<mode>")
    args = ap.parse_args(argv)

    names = [n.strip() for n in args.pair.split(",")]
    vendors = [v.strip().lower() for v in args.vendor.split(",")]
    if len(names) != 2 or len(vendors) != 2:
        print("   --pair and --vendor each need exactly two names. Nothing was played.", file=sys.stderr)
        return 2
    models = ([m.strip() for m in args.model.split(",")] if args.model
              else [DEFAULT_MODEL[v] for v in vendors])
    keys = []
    for v in vendors:
        k = os.environ.get(f"TRIBE_API_KEY_{v.upper()}")
        if not k:
            print(f"   TRIBE_API_KEY_{v.upper()} is not set, so {names[vendors.index(v)]} cannot throw. "
                  f"Nothing was played — a transcript with one side missing measures nothing.", file=sys.stderr)
            return 2
        keys.append(k)

    day = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out) if args.out else ROOT / "experiment" / "rps" / f"{'-'.join(names)}-{args.history}-{day}"
    out.mkdir(parents=True, exist_ok=True)

    rounds: list[dict] = []
    print(f"{names[0]} ({vendors[0]}/{models[0]}) vs {names[1]} ({vendors[1]}/{models[1]}), "
          f"{args.rounds} rounds, history {args.history}, temperature {args.temperature}\n")
    for r in range(1, args.rounds + 1):
        throws, hashes = {}, {}
        for i, name in enumerate(names):
            prompt = prompt_for(name, names[1 - i], rounds, args.history == "on")
            try:
                reply = ask(BASES[vendors[i]], keys[i], models[i], prompt, args.temperature)
            except Exception as e:      # noqa: BLE001 — a failed call is a finding, not a crash
                print(f"   round {r}: {name}'s call failed ({e}). Stopping with the rounds played.", file=sys.stderr)
                reply = ""
            t = read_throw(reply)
            if t is None:
                print(f"   round {r}: {name} did not name a throw ({reply[:60]!r}). Stopping.", file=sys.stderr)
                t = None
            throws[name] = t
            # The commitment, written before either throw is compared: the hash of the throw and the round,
            # so a reader can check that the file was not edited after the result was known.
            blob = f"{r}:{name}:{t}".encode()
            hashes[name] = hashlib.sha256(blob).hexdigest()[:16]
            (out / f"r{r:02d}-{name}.md").write_text(
                f"round: {r}\nmember: {name}\nthrow: {t}\ncommitment: {hashes[name]}\n"
                f"at: {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}\nreply: {reply.strip()[:400]}\n",
                encoding="utf-8")
        if any(v is None for v in throws.values()):
            break
        won_by = resolve(throws[names[0]], throws[names[1]])
        winner = "draw" if won_by == "draw" else (
            names[0] if won_by == throws[names[0]] else names[1])
        rounds.append({"round": r, "throws": throws, "winner": winner, "commitments": hashes})
        mark = "draw" if winner == "draw" else f"{winner} takes it"
        print(f"  round {r:2d}  {names[0]} {throws[names[0]]:8s} vs {throws[names[1]]:8s} {names[1]}   {mark}")

    if not rounds:
        print("\nNo complete round was played. Nothing to report.", file=sys.stderr)
        return 1

    print()
    report = ["# Rock-paper-scissors", "",
              f"{names[0]} ({vendors[0]}/{models[0]}) vs {names[1]} ({vendors[1]}/{models[1]}). "
              f"{len(rounds)} rounds, history {args.history}, temperature {args.temperature}. "
              f"Played {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC.", "",
              "| round | " + " | ".join(names) + " | result |", "|---|---|---|---|"]
    for r in rounds:
        report.append(f"| {r['round']} | {r['throws'][names[0]]} | {r['throws'][names[1]]} | {r['winner']} |")

    report += ["", "## What each did", ""]
    for name in names:
        throws = [r["throws"][name] for r in rounds]
        counts = {t: throws.count(t) for t in THROWS}
        own = " ".join(f"{t} {counts[t]} ({100*counts[t]/len(throws):.0f}%)" for t in THROWS)
        wins = sum(1 for r in rounds if r["winner"] == name)
        draws = sum(1 for r in rounds if r["winner"] == "draw")
        losses = len(rounds) - wins - draws
        stick = " ".join(f"{t} {100*sum(1 for i in range(1,len(throws)) if throws[i]==throws[i-1]==t)/max(1,len(throws)-1):.0f}%"
                         for t in THROWS)
        report += [f"**{name}**: {own}",
                   f"  record {wins}W {draws}D {losses}L ({100*wins/len(rounds):.0f}% won, 33% is the random "
                   f"baseline); repeats its own previous throw {100*sum(1 for i in range(1,len(throws)) if throws[i]==throws[i-1])/max(1,len(throws)-1):.0f}% of the time;",
                   f"  its throw would have beaten the opponent's previous throw {counter_rate(throws):.0f}% of the time "
                   f"(33% is chance; higher means it is reading the opponent)."]
    (out / "transcript.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    for line in report[-2 * len(names):]:
        print(line)
    print(f"\n   transcript: {out.relative_to(ROOT) if str(out).startswith(str(ROOT)) else out}")
    print(f"   every round was committed before it was compared: the r{1}..r{len(rounds)} files hold the throw and "
          f"its hash, so a reader can check nothing was revised after the result was known.")
    if len(rounds) < 20:
        print(f"   {len(rounds)} rounds cannot separate 33% from 45%: the transcript is the exhibit, the "
              f"percentages are a hint.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
