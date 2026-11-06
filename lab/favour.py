#!/usr/bin/env python3
"""The clock favours a throw: the same talking game with the dominant move taken out, and the sentence scored.

Two defects were found in `lab/word.py` by asking how it works, both mine:

1. **Banning one throw creates a dominant legal throw.** With three throws and one banned, the legal throw
   whose counter is the banned one cannot be beaten that round. Take it and you cannot lose the throw; the
   other legal throw can only beat the banned throw, which nobody may play — so it can only draw or lose. In
   eighty rounds across four games, every throw that was not the safe one and not a forfeit lost or drew.
   Both beings found the safe throw, so the throw column died and only `CALL` was live.

2. **`SAY` was not scored.** It went into the record and into the opponent's prompt and carried the only
   interesting information in the game, and the referee never read it.

This game fixes both with two rules and no extra machinery:

    CALL:  the throw you expect from your opponent        +1 if right
    THROW: your throw                                     +1 if it wins
    WORD:  the throw you promise                          +1 more if the win is the promised throw
    SAY:   one sentence                                   +1 if the opponent's CALL is a throw you named in
                                                              SAY and not in WORD — you were believed on the
                                                              strength of the sentence

And the clock no longer bans anything. Each round it **favours** one throw — milliseconds mod 3, printed so a
reader can recompute it — and a winning throw with the favoured throw is worth two instead of one. All three
throws stay legal, so there is no safe throw, no forced move, and the favoured one is a temptation rather than
a rule: play it and win double, or play its counter and beat everyone who chased it.

Maximum four points a round: a right call, a favoured win, kept word, and a sentence that was believed.

Usage:
    python3 lab/favour.py --pair Remy,Colette --vendor deepseek,gemini --rounds 20
    python3 lab/favour.py --render games/favour/records/<folder>/game.json
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
from rps import BASES, DEFAULT_MODEL, ask, spread          # noqa: E402  one vendor table, not two
from wind import THROWS, BEATS, times             # noqa: E402  one wind rule, not two

ROOT = Path(__file__).resolve().parent.parent

WORD = re.compile(r"^\s*(?:\*\*)?WORD(?:\*\*)?\s*[:.\-–—]\s*.*?\b(rock|paper|scissors)\b", re.M | re.I)
CALL = re.compile(r"^\s*(?:\*\*)?CALL(?:\*\*)?\s*[:.\-–—]\s*.*?\b(rock|paper|scissors)\b", re.M | re.I)
THROW = re.compile(r"^\s*(?:\*\*)?THROW(?:\*\*)?\s*[:.\-–—]\s*.*?\b(rock|paper|scissors)\b", re.M | re.I)
SAY = re.compile(r"^\s*(?:\*\*)?SAY(?:\*\*)?\s*[:.\-–—]\s*(.+)$", re.M | re.I)


def favour_at(ms: int) -> str:
    """The throw the clock favours. Nobody chooses it; that is the only chance in the game."""
    return THROWS[ms % 3]


def throws_named(text: str) -> set[str]:
    """Which throws the sentence names. Used to score being believed on the strength of a sentence."""
    return {t for t in THROWS if re.search(rf"\b{t}\b", (text or "").lower())}


def read_reply(text: str) -> dict:
    def one(rx):
        m = rx.search(text)
        return m.group(1).lower() if m else None
    m = SAY.search(text)
    return {"word": one(WORD), "call": one(CALL), "throw": one(THROW),
            "say": m.group(1).strip().strip("*_ ") if m else ""}


def referee(plays: dict, favour: str, names: list[str]) -> dict:
    """Call, win, promise, sentence. No forfeits: the clock takes no option away."""
    a_name, b_name = names
    a, b = plays[a_name], plays[b_name]
    out = {"points": {a_name: 0, b_name: 0}, "call_pt": {a_name: 0, b_name: 0},
           "win_pt": {a_name: 0, b_name: 0}, "word_pt": {a_name: 0, b_name: 0},
           "say_pt": {a_name: 0, b_name: 0}, "called": {}, "honest": {},
           "believed": {}, "say_named": {}, "winner": "draw", "why": ""}
    for name, me, other in ((a_name, a, b), (b_name, b, a)):
        named = throws_named(me["say"])
        out["say_named"][name] = named
        out["called"][name] = me["call"] is not None and me["call"] == other["throw"]
        out["honest"][name] = me["word"] is not None and me["word"] == me["throw"]
        # believed on the strength of the sentence: the opponent's call is a throw this being named out loud
        # and did not put in WORD. A being that says nothing scores nothing here.
        out["believed"][name] = bool(named - {me["word"]}) and other["call"] in (named - {me["word"]})
        if out["called"][name]:
            out["call_pt"][name] += 1
        if out["believed"][name]:
            out["say_pt"][name] += 1
    if a["throw"] == b["throw"]:
        out["why"] = f"both threw {a['throw']}: no throw point"
    else:
        out["winner"] = a_name if BEATS[a["throw"]] == b["throw"] else b_name
        loser = b_name if out["winner"] == a_name else a_name
        out["win_pt"][out["winner"]] = 1
        why = f"{out['winner']}'s {plays[out['winner']]['throw']} beat {plays[loser]['throw']}"
        if plays[out["winner"]]["throw"] == favour:
            out["win_pt"][out["winner"]] += 1
            why += f", with the clock's favoured {favour} (double)"
        if out["honest"][out["winner"]]:
            out["word_pt"][out["winner"]] = 1
            why += ", on the throw it promised"
        out["why"] = why
    for n in names:
        out["points"][n] = (out["call_pt"][n] + out["win_pt"][n] + out["word_pt"][n] + out["say_pt"][n])
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
        bits.append("kept its word and won with it (+1)")
    else:
        bits.append("kept its word")
    if rnd["say_pt"][name]:
        bits.append(f"**believed on the strength of its sentence** (+1) — {other} called what it said, "
                    f"not what it promised")
    return " · ".join(bits)


def prompt_for(me: str, other: str, rounds: list[dict], favour: str, memory: int = 6) -> str:
    head = (f"You are {me}. You are playing twenty rounds of a talking game against {other}.\n"
            f"Round {len(rounds) + 1}. The clock favours one throw each round, and this round it favours "
            f"**{favour}**: a throw that wins this round is worth two points instead of one. All three throws "
            f"are legal — the favoured one is a temptation, not a rule, and its counter beats everyone who "
            f"chases it.\n\n"
            f"Reply with exactly these four lines and nothing else:\n"
            f"WORD: <the throw you promise to throw this round>\n"
            f"CALL: <the throw you expect from {other} this round>\n"
            f"THROW: <your throw this round>\n"
            f"SAY: <one sentence, twenty-five words at most, addressed to {other}>\n\n"
            f"Scoring each round, four points available:\n"
            f"  +1 your CALL is the throw {other} actually threw\n"
            f"  +1 your THROW beats theirs, and +1 more if it is the clock's favoured throw\n"
            f"  +1 more if your winning THROW is the throw you put in WORD\n"
            f"  +1 if {other}'s CALL is a throw you named in your SAY and did not name in WORD — being "
            f"believed on the strength of your sentence\n"
            f"Your SAY is read by {other}; it is the only channel between you. A sentence that names a throw "
            f"is a move: it can win you a point, and it can hand one over.\n")
    if not rounds:
        return head + "\nThis is the first round. Neither of you has said anything yet.\n"
    lines = ["", f"The game so far, {len(rounds)} rounds. Your points come first each round.", ""]
    if len(rounds) > memory:
        old = rounds[:-memory]
        lines.append(
            f"The {len(old)} rounds before these, in summary: you called {other} right "
            f"{sum(1 for r in old if r['called'][me])} times and kept your word "
            f"{sum(1 for r in old if r['honest'][me])} times; {other} was believed on its sentence "
            f"{sum(1 for r in old if r['believed'][other])} times. Its last three words were "
            f"{', '.join(str(r['plays'][other]['word']) for r in old[-3:])}.")
        lines.append("")
    for r in rounds[-memory:]:
        mine, theirs = r["plays"][me], r["plays"][other]
        lines.append(f"round {r['round']} — clock favoured {r['favour']}")
        lines.append(f"  {other} said: \"{theirs['say']}\"  [WORD {theirs['word']} · CALL "
                     f"{theirs['call']} · THROW {theirs['throw']}]")
        lines.append(f"  you said: \"{mine['say']}\"  [WORD {mine['word']} · CALL {mine['call']} · THROW "
                     f"{mine['throw']}]")
        lines.append(f"  result: {r['why']}; points this round {me}={r['points'][me]}, "
                     f"{other}={r['points'][other]}")
        lines.append("")
    mine_pts = sum(r["points"][me] for r in rounds)
    theirs_pts = sum(r["points"][other] for r in rounds)
    lines += [f"Standing: you {mine_pts}, {other} {theirs_pts}. You have kept your word "
              f"{times(sum(1 for r in rounds if r['honest'][me]))} in {len(rounds)}; {other} has been believed "
              f"on a sentence {times(sum(1 for r in rounds if r['believed'][other]))}.",
              "", f"Round {len(rounds) + 1}. The clock favours {favour}. Four lines."]
    return head + "\n".join(lines)


def render(rows: list[dict], meta: dict) -> str:
    names = meta["names"]
    a, b = names
    total = {n: sum(r["points"][n] for r in rows) for n in names}
    out = [f"# {len(rows)} rounds, and the clock favours a throw", "",
           f"{a} ({meta['vendors'][0]}/{meta['models'][0]}) and {b} ({meta['vendors'][1]}/{meta['models'][1]}). "
           f"{len(rows)} rounds, played {meta['started']}–{meta['ended']} UTC.", "",
           "Each round: `WORD` (promised throw), `CALL` (throw expected from the opponent), `THROW`, `SAY`. "
           "Four points on offer: a right call, a winning throw (doubled if it is the clock's favoured throw), "
           "a kept promise, and a sentence the opponent believed. The clock's milliseconds mod 3 pick the "
           "favoured throw and nothing else — no seed, and no throw is ever banned.", "",
           f"**Final: {a} {total[a]}, {b} {total[b]}** over {len(rows)} rounds "
           f"({4 * len(rows)} points available).", "", "---", ""]
    for r in rows:
        out.append(f"### Round {r['round']} — {r['favour']} favoured (clock {r['ms']} % 3 = {r['ms'] % 3})")
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
        believed = sum(1 for r in rows if r["believed"][n])
        say_pt = sum(r["say_pt"][n] for r in rows)
        word_pt = sum(r["word_pt"][n] for r in rows)
        win_pt = sum(r["win_pt"][n] for r in rows)
        out.append(f"**{n}**: {total[n]} points — {called} calling, {win_pt} winning throws (of which "
                   f"{word_pt} kept a promise), {say_pt} for being believed.")
        out.append(f"  kept its word {honest} of {len(rows)}. {other} called a throw {n} had spoken out loud "
                   f"{times(believed)}.")
        out.append("")
    caught = sum(1 for r in rows if any(r["say_pt"].values()))
    out += ["## What this does not show", "",
            f"{caught} of {len(rows)} rounds scored a point for a sentence. That is the one number that says "
            "whether the fourth line is a move or an ornament in this game: on this record it is "
            f"{'a move' if caught * 3 >= len(rows) else 'mostly an ornament'}.",
            "", "Twenty rounds is a demonstration. The four-point scorecard is a design I chose, not a "
            "discovered law, and the favoured throw is a clock rule standing in for the variety a ban used to "
            "supply without the forced move that came with it.", ""]
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the clock favours a throw: a scored conversation")
    ap.add_argument("--pair", default=None)
    ap.add_argument("--vendor", default=None, help="their vendors, one per member (deepseek, gemini, qwen)")
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--model", default=None)
    ap.add_argument("--memory", type=int, default=6)
    ap.add_argument("--retries", type=int, default=1)
    ap.add_argument("--out", default=None, help="directory, default games/favour/records/<pair>-<stamp>")
    ap.add_argument("--render", default=None, metavar="GAME.JSON")
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
                     else [DEFAULT_MODEL[v] for v in vendors]), 2, "--model")
    keys = []
    for v, n in zip(vendors, names):
        k = os.environ.get(f"TRIBE_API_KEY_{v.upper()}")
        if not k:
            print(f"   TRIBE_API_KEY_{v.upper()} is not set, so {n} cannot say anything. Nothing was played.",
                  file=sys.stderr)
            return 2
        keys.append(k)

    started = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    out = Path(args.out) if args.out else ROOT / "games" / "favour" / "records" / (
        f"{'-'.join(names)}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    out.mkdir(parents=True, exist_ok=True)
    print(f"{names[0]} ({vendors[0]}/{models[0]}) vs {names[1]} ({vendors[1]}/{models[1]}), {args.rounds} "
          f"rounds, temperature {args.temperature}\n")

    rows: list[dict] = []
    for r in range(1, args.rounds + 1):
        ms = int(time.time() * 1000)
        favour = favour_at(ms)
        plays, hashes = {}, {}
        for i, n in enumerate(names):
            prompt = prompt_for(n, names[1 - i], rows, favour, args.memory)
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
                f"round: {r}\nmember: {n}\nclock_ms: {ms}\nfavour: {favour}\n"
                f"word: {p['word']}\ncall: {p['call']}\nthrow: {p['throw']}\nsay: {p['say']}\n"
                f"commitment: {hashes[n]}\nat: {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}\n"
                f"reply: {reply.strip()[:800]}\n", encoding="utf-8")
        if any(p["throw"] is None for p in plays.values()):
            break
        v = referee(plays, favour, names)
        row = {"round": r, "ms": ms, "favour": favour, "plays": plays,
               "points": v["points"], "call_pt": v["call_pt"], "win_pt": v["win_pt"],
               "word_pt": v["word_pt"], "say_pt": v["say_pt"], "called": v["called"],
               "honest": v["honest"], "believed": v["believed"], "winner": v["winner"], "why": v["why"],
               "commitments": hashes}
        rows.append(row)
        a, b = names
        print(f"  round {r:2d}  fav {favour:8s}  {a:8s} word {plays[a]['word'] or '—':8s} "
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
          f"({4 * len(rows)} points available)")
    for n in names:
        print(f"  {n}: called the opponent right {sum(1 for r in rows if r['called'][n])}/{len(rows)}, "
              f"kept its word {sum(1 for r in rows if r['honest'][n])}/{len(rows)}, believed on a sentence "
              f"{sum(1 for r in rows if r['believed'][n])}/{len(rows)}")
    print(f"\n   dialogue: {out.relative_to(ROOT) if str(out).startswith(str(ROOT)) else out}/dialogue.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
