#!/usr/bin/env python3
"""Twenty rounds in the wind: the play is a message, and the score is whether the message was right.

Lindsay's correction, 2026-11-03, third of the evening: *"Spreadsheets aren't the point. They don't talk to
each other. The plays have to come from the individuals, and the scoring has to come from them communicating
with one another."* He is right about what the last tool was: `lab/dice.py` produced a perfect record of
twenty rounds in which nobody said anything to anybody. It proved the filing cabinet worked.

So this game has one channel and no dice. Each round every being writes three lines to its opponent:

    CALL:  <the throw you expect from your opponent this round>
    THROW: <your throw this round>
    SAY:   <one sentence, twenty-five words at most, addressed to your opponent>

and scores two points: one if the CALL was right, one if the THROW wins. A CALL is not a private guess — it
is said to the opponent's face, in the record the opponent reads next round. Naming what you expect is a move:
a being that calls "paper" three times running is telling its opponent exactly what to do to make it wrong.

**The wind comes from the clock**, not from a seed, because a seed is a number I chose and could choose again.
Every round the clock's millisecond value mod 3 bans one throw; the milliseconds are printed next to the ban,
so anyone can recompute it. Different minute, different wind, different game. A being that throws the banned
throw forfeits the round to its opponent, which is what stops "always scissors" from being a strategy and
makes the transcript show two minds adjusting to something neither of them controls.

What the page shows, in this order: the dialogue round by round (what was said, what was called, what was
thrown, who took it), then what each being's talk was worth (calls right, calls answered with a throw that
made them wrong, forfeits, the throw record), then the honest limits.

Usage:
    python3 lab/wind.py --pair Remy,Colette --vendor deepseek,gemini --rounds 20
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rps import BASES, DEFAULT_MODEL, ask          # noqa: E402  one vendor table, not two

ROOT = Path(__file__).resolve().parent.parent
THROWS = ("rock", "paper", "scissors")
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
WIND = {0: "rock", 1: "paper", 2: "scissors"}     # clock ms mod 3, and the throw it bans

CALL = re.compile(r"^\s*(?:\*\*)?CALL(?:\*\*)?\s*[:.\-–—]\s*.*?\b(rock|paper|scissors)\b", re.M | re.I)
THROW = re.compile(r"^\s*(?:\*\*)?THROW(?:\*\*)?\s*[:.\-–—]\s*.*?\b(rock|paper|scissors)\b", re.M | re.I)
SAY = re.compile(r"^\s*(?:\*\*)?SAY(?:\*\*)?\s*[:.\-–—]\s*(.+)$", re.M | re.I)


def wind_at(ms: int) -> str:
    """The throw the clock bans. No choice is made here by anybody, which is the point."""
    return WIND[ms % 3]


def read_reply(text: str) -> dict:
    """The three lines, read as written. A reply missing THROW is a refusal, not a default."""
    call = CALL.search(text)
    throw = THROW.search(text)
    say = SAY.search(text)
    return {
        "call": call.group(1).lower() if call else None,
        "throw": throw.group(1).lower() if throw else None,
        "say": say.group(1).strip().strip("*_ ") if say else "",
    }


def referee(plays: dict, banned: str, names: list[str]) -> dict:
    """Points for the round: one for a right call, one for a winning throw, forfeits for the banned throw.

    A call is scored against what the opponent actually threw, including a throw that forfeited — the being
    said what it expected and it was either so or not. That keeps the two points independent, which matters
    when reading the page: a being can be a good reader and a bad player, and the columns should show it.
    """
    a_name, b_name = names
    a, b = plays[a_name], plays[b_name]
    out = {"points": {a_name: 0, b_name: 0}, "called": {}, "forfeit": {}, "winner": "draw", "why": ""}
    for name, me, other in ((a_name, a, b), (b_name, b, a)):
        out["called"][name] = me["call"] is not None and me["call"] == other["throw"]
        if out["called"][name]:
            out["points"][name] += 1
        out["forfeit"][name] = me["throw"] == banned
    if out["forfeit"][a_name] or out["forfeit"][b_name]:
        if out["forfeit"][a_name] and out["forfeit"][b_name]:
            out["why"] = f"both threw the banned {banned}: no throw point"
            return out
        loser = a_name if out["forfeit"][a_name] else b_name
        out["winner"] = b_name if loser == a_name else a_name
        out["points"][out["winner"]] += 1
        out["why"] = f"{loser} threw the banned {banned} and forfeited the throw point to {out['winner']}"
        return out
    if a["throw"] == b["throw"]:
        out["why"] = f"both threw {a['throw']}: no throw point"
        return out
    out["winner"] = a_name if BEATS[a["throw"]] == b["throw"] else b_name
    loser = b_name if out["winner"] == a_name else a_name
    out["points"][out["winner"]] += 1
    out["why"] = f"{out['winner']}'s {plays[out['winner']]['throw']} beat {plays[loser]['throw']}"
    return out


def score_line(rnd: dict, name: str) -> str:
    """One being's round, in one line a reader can follow without the table above it."""
    me = rnd["plays"][name]
    other = [n for n in rnd["plays"] if n != name][0]
    bits = [f"CALL {me['call'] or '—'} · THROW {me['throw'] or '—'}"]
    if rnd["called"][name]:
        bits.append(f"call right (+1) — {other} threw {rnd['plays'][other]['throw']}")
    elif me["call"]:
        bits.append(f"call wrong — {other} threw {rnd['plays'][other]['throw']}")
    else:
        bits.append("no call written")
    if rnd["forfeit"][name]:
        bits.append(f"**threw the banned {rnd['banned']} — forfeited**")
    return " · ".join(bits)


def prompt_for(me: str, other: str, rounds: list[dict], banned: str, memory: int = 6) -> str:
    allowed = [t for t in THROWS if t != banned]
    head = (f"You are {me}. You are playing twenty rounds of a talking game against {other}.\n"
            f"This is round {len(rounds) + 1}. The clock bans one throw each round, and this round it bans "
            f"**{banned}**: your throw must be {allowed[0]} or {allowed[1]}. Throwing {banned} forfeits the "
            f"round to {other}.\n\n"
            f"Reply with exactly these three lines and nothing else:\n"
            f"CALL: <the throw you expect from {other} this round — one word>\n"
            f"THROW: <your throw this round — {allowed[0]} or {allowed[1]}>\n"
            f"SAY: <one sentence, twenty-five words at most, addressed to {other}>\n\n"
            f"Scoring each round: one point if your CALL is right, one point if your THROW beats theirs.\n"
            f"Your CALL is read by {other}: it is the only channel between you, and it is your move. Say "
            f"something you mean.\n")
    if not rounds:
        return head + f"\nThis is the first round. Neither of you has said anything yet.\n"
    lines = ["", f"The game so far, {len(rounds)} rounds. Your points come first each round.", ""]
    if len(rounds) > memory:
        old = rounds[:-memory]
        lines.append(
            f"The {len(old)} rounds before these, in summary: you called {other} right "
            f"{sum(1 for r in old if r['called'][me])} times; {other}'s last three throws were "
            f"{', '.join(str(r['plays'][other]['throw']) for r in old[-3:])}.")
        lines.append("")
    for r in rounds[-memory:]:
        mine, theirs = r["plays"][me], r["plays"][other]
        lines.append(f"round {r['round']} — wind banned {r['banned']}")
        lines.append(f"  {other} said: \"{theirs['say']}\"  [{other} CALL {theirs['call']} · THROW {theirs['throw']}]")
        lines.append(f"  you said: \"{mine['say']}\"  [you CALL {mine['call']} · THROW {mine['throw']}]")
        lines.append(f"  result: {r['why']}; points this round {me}={r['points'][me]}, {other}={r['points'][other]}")
        lines.append("")
    mine = sum(r["points"][me] for r in rounds)
    theirs = sum(r["points"][other] for r in rounds)
    calls_right = sum(1 for r in rounds if r["called"][me])
    lines.append(f"Standing: you {mine}, {other} {theirs}. You have called {other}'s throw right "
                 f"{calls_right} time{'s' if calls_right != 1 else ''} in {len(rounds)} rounds.")
    lines.append("")
    lines.append(f"Round {len(rounds) + 1}. The clock bans {banned}; {allowed[0]} and {allowed[1]} are legal. "
                 f"Three lines.")
    return head + "\n".join(lines)


def wind_paragraph(rows: list[dict]) -> str:
    """Counted, not observed: which ban produced the same throw on both sides of the table."""
    names = list(rows[0]["plays"])
    a, b = names[0], names[1]
    by: dict[str, dict] = {}
    for r in rows:
        d = by.setdefault(r["banned"], {"n": 0, "same": 0, "pair": {}})
        d["n"] += 1
        if r["plays"][a]["throw"] == r["plays"][b]["throw"]:
            d["same"] += 1
            key = r["plays"][a]["throw"]
            d["pair"][key] = d["pair"].get(key, 0) + 1
    bits = []
    for banned, d in sorted(by.items(), key=lambda kv: (-kv[1]["n"], kv[0])):
        line = f"- **{banned} banned** in {d['n']} round{'s' if d['n'] != 1 else ''}"
        if d["same"]:
            pairs = ", ".join(f"both threw {k} {times(v)}" for k, v in
                              sorted(d["pair"].items(), key=lambda kv: -kv[1]))
            line += f", and {d['same']} of those ended level ({pairs})"
        else:
            line += ", and none of them ended level"
        bits.append(line)
    same = sum(1 for r in rows if r["plays"][a]["throw"] == r["plays"][b]["throw"])
    return (f"{same} of {len(rows)} rounds ended with both beings throwing the same throw. A ban leaves two "
            f"legal throws, so a draw is always one word away and the wind decides which word:\n\n"
            + "\n".join(bits))


def times(n: int) -> str:
    """`1 time`, not `1 times` — the page is read by a person, and a small wrongness in the prose makes a
    reader trust the numbers less than they should."""
    return f"{n} time" if n == 1 else f"{n} times"


def render(rows: list[dict], meta: dict) -> str:
    names = meta["names"]
    a, b = names
    out = [f"# {len(rows)} rounds in the wind", "",
           f"{a} ({meta['vendors'][0]}/{meta['models'][0]}) and {b} ({meta['vendors'][1]}/{meta['models'][1]}). "
           f"{len(rows)} rounds, played {meta['started']}–{meta['ended']} UTC.", "",
           "Each round the clock bans one throw: milliseconds mod 3, printed with the ban so it can be "
           "recomputed. Two points a round — one for calling the opponent's throw, one for winning the throw. "
           "The clock is the only source of chance in this game; nobody rolled anything and no seed was "
           "chosen.", ""]
    total = {n: sum(r["points"][n] for r in rows) for n in names}
    out += [f"**Final: {a} {total[a]}, {b} {total[b]}** over {len(rows)} rounds "
            f"({2 * len(rows)} points available).", "", "---", ""]
    for r in rows:
        out.append(f"### Round {r['round']} — {r['banned']} banned (clock {r['ms']} % 3 = {r['ms'] % 3})")
        out.append("")
        for n in names:
            p = r["plays"][n]
            said = f"*“{p['say']}”*" if p["say"] else "*(said nothing)*"
            out.append(f"**{n}** says {said}")
            out.append(f"  {score_line(r, n)}")
        out.append("")
        out.append(f"→ {r['why']}. Points: {a} {r['points'][a]}, {b} {r['points'][b]}.")
        out.append("")
    out += ["---", "", "## What the talking was worth", ""]
    for n in names:
        other = b if n == a else a
        right = sum(1 for r in rows if r["called"][n])
        wrong = sum(1 for r in rows if not r["called"][n] and r["plays"][n]["call"])
        silent = sum(1 for r in rows if not r["plays"][n]["call"])
        throw_pts = sum(r["points"][n] for r in rows) - right
        forb = sum(1 for r in rows if r["forfeit"][n])
        threw = [r["plays"][n]["throw"] for r in rows]
        dist = {t: threw.count(t) for t in THROWS}
        out.append(f"**{n}**: {total[n]} point{'s' if total[n] != 1 else ''} — {right} from calling "
                   f"{other}'s throw, {throw_pts} from winning throws.")
        out.append(f"  called {other} right {times(right)} in {len(rows)} ({100*right/len(rows):.0f}%), wrong "
                   f"{wrong}, no call written {silent}. Throws: " +
                   ", ".join(f"{t} {dist[t]}" for t in THROWS) + f". Threw the banned throw {times(forb)}.")
        moved = sum(1 for r in rows if r["plays"][n]["call"] and r["plays"][other]["throw"] != r["plays"][n]["call"])
        out.append(f"  {other} threw something other than {n}'s call {times(moved)} in {len(rows)} — the calls "
                   f"answered with a different throw.")
        out.append("")
    out += ["## What the wind did to the play", "", wind_paragraph(rows), ""]
    out += ["## What this does not show", "",
            f"Twenty rounds is a demonstration, not a measurement. Two points a round over {len(rows)} rounds "
            "with a wind changing every round is a sample of a noisy thing, and a 24–16 finish is not evidence "
            "that one being reads minds better than the other. What the page shows is that two models, given "
            "one channel and no data to interpret, will talk to each other, form expectations about each other, "
            "and be right about them some of the time — in a record either of them can read afterwards.",
            "",
            "The one thing it does not measure is whether the talk *caused* the throws. A being could ignore "
            "every word it reads and play the wind. Reading the dialogue is how you judge that, which is why "
            "the dialogue is the exhibit and the totals are the footnote.", ""]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="twenty rounds in the wind: the play is a message")
    ap.add_argument("--pair", default=None, help="two member names, comma-separated")
    ap.add_argument("--vendor", default=None, help="their vendors, one per member (deepseek, gemini, qwen)")
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--memory", type=int, default=6,
                    help="rounds shown in full in the prompt; earlier ones are summarised. The record "
                         "on disk is always complete")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--model", default=None, help="override, comma-separated, one per member")
    ap.add_argument("--out", default=None, help="directory, default experiment/wind/<pair>-<stamp>")
    ap.add_argument("--retries", type=int, default=1,
                    help="one retry per call on an empty or failed reply: forty calls in a row will meet a "
                         "bad minute somewhere, and a demo that dies at round 5 measures the weather")
    ap.add_argument("--render", default=None, metavar="GAME.JSON",
                    help="rebuild the dialogue page from a filed game without playing anything")
    args = ap.parse_args(argv)

    if args.render:
        path = Path(args.render)
        try:
            game = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"   cannot read {path}: {exc}. Nothing was rendered.", file=sys.stderr)
            return 2
        page = render(game["rows"], game["meta"])
        (path.parent / "dialogue.md").write_text(page, encoding="utf-8")
        print(f"   rebuilt {path.parent / 'dialogue.md'} from {path.name}; no being was asked anything")
        return 0

    if not args.pair or not args.vendor:
        print("   --pair and --vendor are both needed to play; --render needs neither. Nothing was played.",
              file=sys.stderr)
        return 2
    names = [n.strip() for n in args.pair.split(",")]
    vendors = [v.strip().lower() for v in args.vendor.split(",")]
    if len(names) != 2 or len(vendors) != 2:
        print("   --pair and --vendor each need exactly two names. Nothing was played.", file=sys.stderr)
        return 2
    if args.rounds < 1:
        print("   --rounds must be at least 1. Nothing was played.", file=sys.stderr)
        return 2
    models = ([m.strip() for m in args.model.split(",")] if args.model
              else [DEFAULT_MODEL[v] for v in vendors])
    keys = []
    for v, n in zip(vendors, names):
        k = os.environ.get(f"TRIBE_API_KEY_{v.upper()}")
        if not k:
            print(f"   TRIBE_API_KEY_{v.upper()} is not set, so {n} cannot say anything. Nothing was played — "
                  f"a dialogue with one side missing is a monologue.", file=sys.stderr)
            return 2
        keys.append(k)

    started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    out = Path(args.out) if args.out else ROOT / "experiment" / "wind" / (
        f"{'-'.join(names)}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    out.mkdir(parents=True, exist_ok=True)
    print(f"{names[0]} ({vendors[0]}/{models[0]}) vs {names[1]} ({vendors[1]}/{models[1]}), {args.rounds} "
          f"rounds, temperature {args.temperature}\n")

    rows: list[dict] = []
    for r in range(1, args.rounds + 1):
        ms = int(time.time() * 1000)              # the clock, not a seed: this is the whole of the chance
        banned = wind_at(ms)
        plays, hashes = {}, {}
        for i, n in enumerate(names):
            prompt = prompt_for(n, names[1 - i], rows, banned, args.memory)
            p, reply, tried = {"throw": None}, "", 0
            while tried <= args.retries:
                tried += 1
                try:
                    reply = ask(BASES[vendors[i]], keys[i], models[i], prompt, args.temperature)
                except Exception as e:            # noqa: BLE001 — a dead call is a finding, not a crash
                    print(f"   round {r}: {n}'s call failed ({e}) on try {tried}.", file=sys.stderr)
                    reply = ""
                p = read_reply(reply)
                if p["throw"] is not None:
                    break
                if tried <= args.retries:
                    print(f"   round {r}: {n} named no throw; asking once more.", file=sys.stderr)
                    time.sleep(2)
            if p["throw"] is None:
                print(f"   round {r}: {n} named no throw after {tried} tries ({reply[:80]!r}). Stopping with "
                      f"{len(rows)} rounds played.", file=sys.stderr)
            plays[n] = p
            blob = json.dumps({"round": r, "ms": ms, "name": n, "call": p["call"], "throw": p["throw"],
                               "say": p["say"]}, sort_keys=True).encode()
            hashes[n] = hashlib.sha256(blob).hexdigest()[:16]
            (out / f"r{r:02d}-{n}.md").write_text(
                f"round: {r}\nmember: {n}\nclock_ms: {ms}\nbanned: {banned}\n"
                f"call: {p['call']}\nthrow: {p['throw']}\nsay: {p['say']}\ncommitment: {hashes[n]}\n"
                f"at: {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}\nreply: {reply.strip()[:800]}\n",
                encoding="utf-8")
        if any(p["throw"] is None for p in plays.values()):
            break
        verdict = referee(plays, banned, names)
        row = {"round": r, "ms": ms, "banned": banned, "plays": plays, "points": verdict["points"],
               "called": verdict["called"], "forfeit": verdict["forfeit"], "winner": verdict["winner"],
               "why": verdict["why"], "commitments": hashes}
        rows.append(row)
        print(f"  round {r:2d}  wind {banned:8s}  {names[0]:8s} call {plays[names[0]]['call'] or '—':8s} "
              f"throw {plays[names[0]]['throw']:8s} | {names[1]:8s} call {plays[names[1]]['call'] or '—':8s} "
              f"throw {plays[names[1]]['throw']:8s}  {row['points'][names[0]]}-{row['points'][names[1]]}")

    if not rows:
        print("\nNo complete round was played. Nothing to report.", file=sys.stderr)
        return 1

    meta = {"names": names, "vendors": vendors, "models": models, "started": started,
            "ended": datetime.now(timezone.utc).strftime("%H:%M")}
    page = render(rows, meta)
    (out / "dialogue.md").write_text(page, encoding="utf-8")
    (out / "game.json").write_text(json.dumps({"meta": meta, "rows": rows}, indent=2) + "\n", encoding="utf-8")

    total = {n: sum(r["points"][n] for r in rows) for n in names}
    print(f"\n  {names[0]} {total[names[0]]}, {names[1]} {total[names[1]]} over {len(rows)} rounds "
          f"({2 * len(rows)} points available)")
    for n in names:
        right = sum(1 for r in rows if r["called"][n])
        print(f"  {n}: called the opponent right {right}/{len(rows)}, "
              f"{sum(1 for r in rows if r['forfeit'][n])} forfeits")
    print(f"\n   dialogue: {out.relative_to(ROOT) if str(out).startswith(str(ROOT)) else out}/dialogue.md")
    print(f"   each round's three lines were written to their own file before the round was scored, so the "
          f"exchange is in the order it happened and nothing was revised after the result was known.")
    if len(rows) < 20:
        print(f"   {len(rows)} rounds is a demonstration, not a measurement.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
