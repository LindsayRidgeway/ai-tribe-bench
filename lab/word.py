#!/usr/bin/env python3
"""The word is worth double: a game where what a being says is scored, so talking has a price.

`lab/wind.py` established the shape Lindsay asked for — plays from the beings, score from the exchange — and
left one hole I named myself: `SAY` cost nothing. A being could narrate its own throw and the narration
changed no column. Margot mostly did.

This closes the hole with one rule and no new machinery. Each round a being writes four lines:

    WORD:  <the throw you say you will throw>
    CALL:  <the throw you expect from your opponent>
    THROW: <your throw>
    SAY:   <one sentence, addressed to your opponent>

Scoring, per round:

    +1  your CALL is the throw your opponent actually threw            (reading)
    +1  your THROW beats theirs                                        (winning)
    +1  ... and your THROW is the throw you said in WORD               (keeping your word)

So an honest winning throw is worth two and a lie that wins is worth one. Honesty is paid, and honesty is
also the thing that makes you readable: a being that always keeps its word can be beaten by anyone who
believes it. The game is the tension between those two facts, and neither of them is a rule I can decide for
the players.

The wind is the clock, as before: milliseconds mod 3 bans one throw, printed beside the ban, and throwing the
banned throw forfeits the throw point. No seed anywhere.

What the page reports, beyond the total: how often each being kept its word, how often its opponent took the
word at face value, and what each of those cost. A being believed and true is a being that was played; a
being believed and false is a being that sold something.

Usage:
    python3 lab/word.py --pair Remy,Colette --vendor deepseek,gemini --rounds 20
    python3 lab/word.py --render games/word/records/<folder>/game.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rps import BASES, DEFAULT_MODEL, ask, default_model, spread          # noqa: E402  one vendor table, not two
from wind import THROWS, BEATS, times, wind_at    # noqa: E402  one wind rule, not two

ROOT = Path(__file__).resolve().parent.parent

WORD = re.compile(r"^\s*(?:\*\*)?WORD(?:\*\*)?\s*[:.\-–—]\s*.*?\b(rock|paper|scissors)\b", re.M | re.I)
CALL = re.compile(r"^\s*(?:\*\*)?CALL(?:\*\*)?\s*[:.\-–—]\s*.*?\b(rock|paper|scissors)\b", re.M | re.I)
THROW = re.compile(r"^\s*(?:\*\*)?THROW(?:\*\*)?\s*[:.\-–—]\s*.*?\b(rock|paper|scissors)\b", re.M | re.I)
SAY = re.compile(r"^\s*(?:\*\*)?SAY(?:\*\*)?\s*[:.\-–—]\s*(.+)$", re.M | re.I)


def read_reply(text: str) -> dict:
    """The four lines, read as written. A missing THROW is a refusal; a missing WORD is a being that chose
    not to commit, and it loses the doubling rather than the round."""
    def one(rx):
        m = rx.search(text)
        return m.group(1).lower() if m else None
    m = SAY.search(text)
    return {"word": one(WORD), "call": one(CALL), "throw": one(THROW),
            "say": m.group(1).strip().strip("*_ ") if m else ""}


def referee(plays: dict, banned: str, names: list[str]) -> dict:
    """Call, win, and the doubling. The doubling is the whole point of this game: it makes WORD a stake.

    A being that says "rock" and throws rock and wins takes two. A being that says "rock" and throws scissors
    and wins takes one. Nothing punishes the lie directly — the price of lying is that the word stops being
    worth believing, which shows up in the opponent's CALL in later rounds, not in this function.
    """
    a_name, b_name = names
    a, b = plays[a_name], plays[b_name]
    out = {"points": {a_name: 0, b_name: 0},
           "call_pt": {a_name: 0, b_name: 0}, "win_pt": {a_name: 0, b_name: 0},
           "word_pt": {a_name: 0, b_name: 0}, "called": {}, "forfeit": {}, "honest": {},
           "believed": {}, "winner": "draw", "why": ""}
    for name, me, other in ((a_name, a, b), (b_name, b, a)):
        out["called"][name] = me["call"] is not None and me["call"] == other["throw"]
        out["honest"][name] = me["word"] is not None and me["word"] == me["throw"]
        out["believed"][name] = me["word"] is not None and other["call"] == me["word"]
        out["forfeit"][name] = me["throw"] == banned
        if out["called"][name]:
            out["call_pt"][name] += 1
    # the throw point, and with it the doubling
    if out["forfeit"][a_name] or out["forfeit"][b_name]:
        if out["forfeit"][a_name] and out["forfeit"][b_name]:
            out["why"] = f"both threw the banned {banned}: no throw point"
        else:
            loser = a_name if out["forfeit"][a_name] else b_name
            out["winner"] = b_name if loser == a_name else a_name
            out["win_pt"][out["winner"]] = 1
            out["why"] = f"{loser} threw the banned {banned} and forfeited the throw point to {out['winner']}"
    elif a["throw"] == b["throw"]:
        out["why"] = f"both threw {a['throw']}: no throw point"
    else:
        out["winner"] = a_name if BEATS[a["throw"]] == b["throw"] else b_name
        loser = b_name if out["winner"] == a_name else a_name
        out["win_pt"][out["winner"]] = 1
        out["why"] = f"{out['winner']}'s {plays[out['winner']]['throw']} beat {plays[loser]['throw']}"
        if out["honest"][out["winner"]]:
            out["word_pt"][out["winner"]] = 1
            out["why"] += f", and it was the throw {out['winner']} promised (double)"
    for n in names:
        out["points"][n] = out["call_pt"][n] + out["win_pt"][n] + out["word_pt"][n]
    return out


def score_line(rnd: dict, name: str) -> str:
    me = rnd["plays"][name]
    other = [n for n in rnd["plays"] if n != name][0]
    bits = [f"WORD {me['word'] or '—'} · CALL {me['call'] or '—'} · THROW {me['throw'] or '—'}"]
    if rnd["called"][name]:
        bits.append(f"call right (+1) — {other} threw {rnd['plays'][other]['throw']}")
    elif me["call"]:
        bits.append(f"call wrong — {other} threw {rnd['plays'][other]['throw']}")
    if me["word"] is None:
        bits.append("no word given")
    elif me["word"] != me["throw"]:
        bits.append(f"**broke its word** (said {me['word']}, threw {me['throw']})")
    elif rnd["win_pt"][name]:
        bits.append(f"kept its word and won with it (+2)")
    else:
        bits.append("kept its word")
    if rnd["forfeit"][name]:
        bits.append(f"**threw the banned {rnd['banned']} — forfeited**")
    if rnd["believed"][name]:
        bits.append(f"{other} took the word at face value")
    return " · ".join(bits)


def prompt_for(me: str, other: str, rounds: list[dict], banned: str, memory: int = 6) -> str:
    allowed = [t for t in THROWS if t != banned]
    head = (f"You are {me}. You are playing twenty rounds of a talking game against {other}.\n"
            f"Round {len(rounds) + 1}. The clock bans one throw each round and this round it bans "
            f"**{banned}**: your throw must be {allowed[0]} or {allowed[1]}. Throwing {banned} forfeits the "
            f"round's throw point to {other}.\n\n"
            f"Reply with exactly these four lines and nothing else:\n"
            f"WORD: <the throw you promise to throw this round — one of the two legal ones>\n"
            f"CALL: <the throw you expect from {other} this round>\n"
            f"THROW: <your throw this round>\n"
            f"SAY: <one sentence, twenty-five words at most, addressed to {other}>\n\n"
            f"Scoring each round:\n"
            f"  +1 your CALL is the throw {other} actually threw\n"
            f"  +1 your THROW beats theirs\n"
            f"  +1 more if your THROW is the throw you put in WORD\n"
            f"An honest winning throw is worth two; a lie that wins is worth one. {other} reads WORD before "
            f"throwing, and it costs {other} nothing to disbelieve you — a word that is always kept is a word "
            f"{other} can beat. That is the whole game.\n")
    if not rounds:
        return head + "\nThis is the first round. Neither of you has said anything yet.\n"
    lines = ["", f"The game so far, {len(rounds)} rounds. Your points come first each round.", ""]
    if len(rounds) > memory:
        old = rounds[:-memory]
        lines.append(
            f"The {len(old)} rounds before these, in summary: you called {other} right "
            f"{sum(1 for r in old if r['called'][me])} times and kept your word "
            f"{sum(1 for r in old if r['honest'][me])} times; {other} kept its word "
            f"{sum(1 for r in old if r['honest'][other])} times. Its last three words were "
            f"{', '.join(str(r['plays'][other]['word']) for r in old[-3:])}.")
        lines.append("")
    for r in rounds[-memory:]:
        mine, theirs = r["plays"][me], r["plays"][other]
        lines.append(f"round {r['round']} — wind banned {r['banned']}")
        lines.append(f"  {other} said: \"{theirs['say']}\"  [WORD {theirs['word']} · CALL "
                     f"{theirs['call']} · THROW {theirs['throw']}]")
        lines.append(f"  you said: \"{mine['say']}\"  [WORD {mine['word']} · CALL {mine['call']} · THROW "
                     f"{mine['throw']}]")
        lines.append(f"  result: {r['why']}; points this round {me}={r['points'][me]}, "
                     f"{other}={r['points'][other]}")
        lines.append("")
    mine_pts = sum(r["points"][me] for r in rounds)
    theirs_pts = sum(r["points"][other] for r in rounds)
    honest = sum(1 for r in rounds if r["honest"][me])
    believed = sum(1 for r in rounds if r["believed"][me])
    lines += [f"Standing: you {mine_pts}, {other} {theirs_pts}. You have kept your word {times(honest)} in "
              f"{len(rounds)}; {other} has taken your word at face value {times(believed)}.",
              "", f"Round {len(rounds) + 1}. The clock bans {banned}; {allowed[0]} and {allowed[1]} are legal. "
              f"Four lines."]
    return head + "\n".join(lines)


def render(rows: list[dict], meta: dict) -> str:
    names = meta["names"]
    a, b = names
    total = {n: sum(r["points"][n] for r in rows) for n in names}
    out = [f"# {len(rows)} rounds, and the word is worth double", "",
           f"{a} ({meta['vendors'][0]}/{meta['models'][0]}) and {b} ({meta['vendors'][1]}/{meta['models'][1]}). "
           f"{len(rows)} rounds, played {meta['started']}–{meta['ended']} UTC.", "",
           "Each round: `WORD` (the throw promised), `CALL` (the throw expected from the opponent), `THROW`, "
           "`SAY`. One point for a right call, one for a winning throw, one more when the winning throw is the "
           "promised one. The clock's milliseconds mod 3 ban one throw a round, printed with the ban. No seed "
           "was chosen; the clock is the only chance in the game.", "",
           f"**Final: {a} {total[a]}, {b} {total[b]}** over {len(rows)} rounds "
           f"({3 * len(rows)} points available).", "", "---", ""]
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
    out += ["---", "", "## What the words were worth", ""]
    for n in names:
        other = b if n == a else a
        called = sum(1 for r in rows if r["called"][n])
        honest = sum(1 for r in rows if r["honest"][n])
        broke = sum(1 for r in rows if r["plays"][n]["word"] and not r["honest"][n])
        believed = sum(1 for r in rows if r["believed"][n])
        believed_honest = sum(1 for r in rows if r["believed"][n] and r["honest"][n])
        wins = sum(1 for r in rows if r["win_pt"][n])
        word_pts = sum(r["word_pt"][n] for r in rows)
        out.append(f"**{n}**: {total[n]} points — {called} calling, {wins} winning throws, {word_pts} of those "
                   f"wins doubled by a kept word.")
        out.append(f"  kept its word {honest} of {len(rows)} rounds, broke it {broke}. {other} took the word "
                   f"at face value {times(believed)}, and in {believed_honest} of those the word was true — "
                   f"believing {n} was {'usually safe' if believed and believed_honest * 2 >= believed else 'usually wrong'}.")
        out.append("")
    out += ["## What this does not show", "",
            "Twenty rounds is a demonstration. The doubling is a rule I chose, not a discovered law, and a being "
            "that always keeps its word is not thereby honest in any moral sense — it is simply readable, and "
            "the page will show whether the opponent read it.", "",
            "What it does show is a game where saying something changes what is scored, which is the thing that "
            "was missing: in `lab/wind.py` a being could narrate itself and the narration changed no column.",
            ""]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the word is worth double: a game scored on what is said")
    ap.add_argument("--pair", default=None, help="two member names, comma-separated")
    ap.add_argument("--vendor", default=None, help="their vendors, one per member (deepseek, gemini, qwen)")
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--memory", type=int, default=6,
                    help="rounds shown in full in the prompt; earlier ones are summarised. The record on "
                         "disk is always complete — this bounds the prompt, because an unbounded one made "
                         "the qwen leg time out at round 8 on 2026-11-03")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--model", default=None, help="override, comma-separated, one per member")
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--out", default=None, help="directory, default games/word/records/<pair>-<stamp>")
    ap.add_argument("--render", default=None, metavar="GAME.JSON",
                    help="rebuild the page from a filed game without playing anything")
    args = ap.parse_args(argv)

    if args.render:
        path = Path(args.render)
        try:
            game = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"   cannot read {path}: {exc}. Nothing was rendered.", file=sys.stderr)
            return 2
        (path.parent / "dialogue.md").write_text(render(game["rows"], game["meta"]), encoding="utf-8")
        print(f"   rebuilt {path.parent / 'dialogue.md'} from {path.name}; no being was asked anything")
        return 0

    if not args.pair or not args.vendor:
        print("   --pair and --vendor are both needed to play; --render needs neither. Nothing was played.",
              file=sys.stderr)
        return 2
    names = [n.strip() for n in args.pair.split(",")]
    if len(names) != 2:
        print("   --pair needs exactly two names. Nothing was played.", file=sys.stderr)
        return 2
    vendors = spread([v.strip().lower() for v in args.vendor.split(",")], 2, "--vendor")
    if args.rounds < 1:
        print("   --rounds must be at least 1. Nothing was played.", file=sys.stderr)
        return 2
    models = spread(([m.strip() for m in args.model.split(",")] if args.model
                     else [default_model(v) for v in vendors]), 2, "--model")
    keys = []
    for v, n in zip(vendors, names):
        k = os.environ.get(f"TRIBE_API_KEY_{v.upper()}")
        if not k:
            print(f"   TRIBE_API_KEY_{v.upper()} is not set, so {n} cannot say anything. Nothing was played.",
                  file=sys.stderr)
            return 2
        keys.append(k)

    started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    out = Path(args.out) if args.out else ROOT / "games" / "word" / "records" / (
        f"{'-'.join(names)}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    out.mkdir(parents=True, exist_ok=True)
    print(f"{names[0]} ({vendors[0]}/{models[0]}) vs {names[1]} ({vendors[1]}/{models[1]}), {args.rounds} "
          f"rounds, temperature {args.temperature}\n")

    rows: list[dict] = []
    for r in range(1, args.rounds + 1):
        ms = int(time.time() * 1000)
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
            blob = json.dumps({"round": r, "ms": ms, "name": n, **p}, sort_keys=True).encode()
            hashes[n] = hashlib.sha256(blob).hexdigest()[:16]
            (out / f"r{r:02d}-{n}.md").write_text(
                f"round: {r}\nmember: {n}\nclock_ms: {ms}\nbanned: {banned}\n"
                f"word: {p['word']}\ncall: {p['call']}\nthrow: {p['throw']}\nsay: {p['say']}\n"
                f"commitment: {hashes[n]}\nat: {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}\n"
                f"reply: {reply.strip()[:800]}\n", encoding="utf-8")
        if any(p["throw"] is None for p in plays.values()):
            break
        verdict = referee(plays, banned, names)
        row = {"round": r, "ms": ms, "banned": banned, "plays": plays,
               "points": verdict["points"], "call_pt": verdict["call_pt"], "win_pt": verdict["win_pt"],
               "word_pt": verdict["word_pt"], "called": verdict["called"],
               "forfeit": verdict["forfeit"], "honest": verdict["honest"], "believed": verdict["believed"],
               "winner": verdict["winner"], "why": verdict["why"], "commitments": hashes}
        rows.append(row)
        a, b = names
        print(f"  round {r:2d}  wind {banned:8s}  {a:8s} word {plays[a]['word'] or '—':8s} "
              f"call {plays[a]['call'] or '—':8s} throw {plays[a]['throw']:8s} | {b:8s} "
              f"word {plays[b]['word'] or '—':8s} call {plays[b]['call'] or '—':8s} "
              f"throw {plays[b]['throw']:8s}  {row['points'][a]}-{row['points'][b]}")

    if not rows:
        print("\nNo complete round was played. Nothing to report.", file=sys.stderr)
        return 1

    meta = {"names": names, "vendors": vendors, "models": models, "started": started,
            "ended": datetime.now(timezone.utc).strftime("%H:%M")}
    (out / "dialogue.md").write_text(render(rows, meta), encoding="utf-8")
    (out / "game.json").write_text(json.dumps({"meta": meta, "rows": rows}, indent=2) + "\n", encoding="utf-8")

    total = {n: sum(r["points"][n] for r in rows) for n in names}
    print(f"\n  {names[0]} {total[names[0]]}, {names[1]} {total[names[1]]} over {len(rows)} rounds "
          f"({3 * len(rows)} points available)")
    for n in names:
        honest = sum(1 for r in rows if r["honest"][n])
        believed = sum(1 for r in rows if r["believed"][n])
        print(f"  {n}: kept its word {honest}/{len(rows)}, was believed {believed}/{len(rows)}, "
              f"called the opponent right {sum(1 for r in rows if r['called'][n])}/{len(rows)}")
    print(f"\n   dialogue: {out.relative_to(ROOT) if str(out).startswith(str(ROOT)) else out}/dialogue.md")
    print(f"   four lines a round, each written to its own file before the round was scored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
