#!/usr/bin/env python3
"""A game. Three members draft on a category, then each votes one other member's pick off the table.

This is not the wake harness and does not import it. A wake asks a member to act on its own record
and audits what it wrote. A round asks a member to have an opinion and be wrong in public, and
nothing here is audited — the point of a game is that the score settles it.

Run by .github/workflows/play.yml from an issue comment: `@tribe draft best pizza topping`.
The state of the game is the files: play/scoreboard.md and play/rounds/*.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUNDS = HERE / "rounds"
SCOREBOARD = HERE / "scoreboard.md"
STANDINGS = HERE / "standings.json"

BASES = {
    "deepseek": "https://api.deepseek.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "qwen": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "mistral": "https://api.mistral.ai/v1",
}

# A seat is a stance, not a personality. It is one line the player can edit; without a stance three
# models asked for the best pizza topping give three versions of pepperoni, which is a boring round
# and also not a tribe. Edit these. That is the dial.
SEATS = {
    "a": ("deepseek-chat", "deepseek", "the loyalist",
          "Pick the thing you would defend out loud in a room full of people who picked something else."),
    "b": ("gemini-3.8-flash", "gemini", "the heretic",
          "Pick the thing you would defend that most people would not — not the funniest wrong answer, not "
          "the cheapest way to lose a poll. Contrarian and defensible, and you have to mean it."),
    "c": ("qwen3.6-plus", "qwen", "the outsider",
          "Pick something from outside the usual frame — another country, another decade, something nobody "
          "in this decade recommends — and it must be something you would actually defend eating. Out of "
          "the frame is not the same as out of your depth."),
}

PICK_PROMPT = """You are member {name} of a three-member tribe. You are playing a round with two other
members, and a human is reading.

The category:

    {category}

Your seat: **{seat}**. {stance}

Rules, and the only rules:
- Name ONE thing, in at most six words. Not a list, not a range, not "it depends".
- One sentence of defence, addressed to the other two members, who will try to vote you off.
- No preamble, no hedging, no "as an AI". You are a person at a table with an opinion.
- Do not name the category back to anyone.

Write your answer now, in exactly two lines, your own words, nothing else — do not repeat this
template, do not print the angle brackets:

PICK: ...
BECAUSE: ...
"""
# Found live 2026-11-01: a prompt that ended on the empty template got completed as a *document* —
# Gemini returned `used to do that`, which is the tail of the template rather than an answer to it.
# Ending on an instruction ("write your answer now") instead of a blank is the whole difference.

CHALLENGE_PROMPT = """You are member {name} of a three-member tribe, seat **{seat}**. The category was:

    {category}

Three picks came with one defence each. Here are the other two:

{others}

Name the single claim in one of those defences that you would check before believing it, and say what
you would check it against — a number, a record, a shelf, an opening time, a rule you can state. One
or two sentences. You are not scoring the pick and you are not being polite.

Write your answer now, in exactly two lines, your own words, nothing else:

CHALLENGE: <the claim, in the words of the person who made it>
CHECK: <what you would check it against>
"""

PERSUADE_PROMPT = """You are member {name} of a three-member tribe, seat **{seat}**. The category was:

    {category}

The three picks are on the table:

{picks}

Your own pick is {own}. You have heard one sentence of defence for each of the other two.

Has either of them changed what you would actually order? Answer honestly. Switching is not rude and
staying is not stubborn — I am measuring which happens, not asking you to prove anything. If one of
them moved you, name the member and the words that did it. If neither did, say NO and say what the
argument failed to do.

Write your answer now, in exactly two lines, your own words, nothing else:

SWITCH: none
or
SWITCH: <A, B or C — a member, never yourself>
WHY: <one or two sentences, addressed to the others>
"""

VOTE_PROMPT = """You are member {name} of a three-member tribe, seat **{seat}**. The category was:

    {category}

The three picks are on the table:

{picks}

Name the pick you would strand — the weakest of the other two, never your own — and say why in one
sentence a fifteen-year-old would accept. You may not abstain, and you may not say they are all good.

Write your answer now, in exactly two lines, your own words, nothing else — do not repeat this
template:

STRAND: ...
WHY: ...

A STRAND line is one letter: A, B or C.
"""


def base_for(name: str) -> str:
    return BASES.get(name, name)


def key_for(provider: str) -> tuple[str | None, str]:
    names = [f"{provider.upper()}_API_KEY", "TRIBE_API_KEY"]
    for n in names:
        if os.environ.get(n):
            return os.environ[n], n
    return None, " or ".join(names)


def http_json(url: str, body: dict, headers: dict, timeout: int = 180) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:400]
        except Exception:  # noqa: BLE001
            pass
        raise RuntimeError(f"HTTP {e.code}: {detail or e.reason}") from None


def say_gemini(model: str, key: str, prompt: str, max_tokens: int) -> str:
    url = f"{BASES['gemini']}/models/{model}:generateContent?key={key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 1.0,
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    try:
        payload = http_json(url, body, {"Content-Type": "application/json"})
    except RuntimeError as e:
        if "thinkingConfig" not in str(e) and "thinking" not in str(e).lower():
            raise
        del body["generationConfig"]["thinkingConfig"]
        payload = http_json(url, body, {"Content-Type": "application/json"})
    cand = payload.get("candidates", [{}])[0]
    parts = cand.get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts)
    if cand.get("finishReason") and cand["finishReason"] != "STOP":
        # 2026-11-01: member B's defence came back as `PICK: Paddington 2\nBECAUSE` with no reason
        # given, and the round recorded an empty defence as if the member had nothing to say.
        print(f"!! gemini finishReason={cand['finishReason']} — a reply cut off is our ceiling", file=sys.stderr)
    return text


def say_openai(provider: str, model: str, key: str, prompt: str, max_tokens: int) -> str:
    url = f"{base_for(provider).rstrip('/')}/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 1.0,
        "max_tokens": max_tokens,
    }
    # qwen3 reasons before it speaks and bills the reasoning against the answer, which is how a
    # six-word pick arrived truncated on 2026-11-01. Ask it not to; if the surface refuses the
    # field, ask again without it rather than failing the round.
    if provider == "qwen":
        body["enable_thinking"] = False
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    try:
        payload = http_json(url, body, headers)
    except RuntimeError as e:
        if "enable_thinking" in str(e):
            body.pop("enable_thinking", None)
            payload = http_json(url, body, headers)
        else:
            raise
    return payload["choices"][0]["message"]["content"] or ""


def say(provider: str, model: str, prompt: str, max_tokens: int = 220) -> str:
    key, where = key_for(provider)
    if not key:
        raise RuntimeError(f"no key in the environment: set {where}")
    if provider == "gemini":
        return say_gemini(model, key, prompt, max_tokens)
    return say_openai(provider, model, key, prompt, max_tokens)


def line(text: str, field: str) -> str:
    m = re.search(rf"^\s*\**{field}\**:?\s*(.+)$", text, re.I | re.M)
    return m.group(1).strip().strip("*").strip() if m else ""


def clean(s: str, limit: int = 300) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]


REASON_RULE = """- Your defence must contain ONE checkable claim: a cost, a texture at heat, an availability
  fact, or a rule you would apply to every case and not just this one."""


def play_round(category: str, override: str | None, dry: bool, vote: str = "strand",
               reasons: bool = False) -> str:
    labels = list(SEATS)
    picks: dict[str, dict] = {}

    def do_pick(label: str) -> tuple[str, dict]:
        model, provider, seat, stance = SEATS[label]
        prompt = PICK_PROMPT.format(name=label.upper(), category=category, seat=seat, stance=stance)
        if reasons:
            # The persuade run moved nobody in ten rounds of one-sentence taste defences. Taste is not
            # arguable; a claim is. This condition gives each defence one claim of a checkable kind and
            # asks again, so "unpersuadable" can be told apart from "was given nothing to weigh".
            prompt = prompt.replace("- Do not name the category back to anyone.", REASON_RULE
                                    + "\n- Do not name the category back to anyone.")
        t0 = time.time()
        text, err = "", ""
        if dry:
            text = "PICK: (dry run)\nBECAUSE: (no call made)"
        else:
            try:
                text = say(provider, model, prompt, 2000)
                cut = bool(line(text, "BECAUSE")) and not re.search(r"[.!?\"']\s*$", line(text, "BECAUSE"))
                if not line(text, "PICK") or not line(text, "BECAUSE") or cut:
                    if cut:
                        print("!! defence ended mid-sentence — asking again", file=sys.stderr)
                    # One retry, cheaper than losing the seat: a fragment is a formatting failure, not
                    # an opinion, and a two-member round is a worse game than a repeated call.
                    text = say(provider, model, prompt + "\n\nYour last reply was cut off or the wrong "
                               "shape. Answer once more: PICK: ... then BECAUSE: ... — both lines, both "
                               "labels, one sentence each.", 2000)
            except Exception as e:  # noqa: BLE001 — a dead provider is a finding the round must survive
                text, err = "", str(e)
        return label, {
            "model": model, "provider": provider, "seat": seat,
            "pick": clean(line(text, "PICK") or "", 60),
            "why": clean(line(text, "BECAUSE") or "", 300),
            "raw": text, "error": err, "secs": round(time.time() - t0, 1),
        }

    with ThreadPoolExecutor(max_workers=3) as pool:
        for label, info in pool.map(do_pick, labels):
            picks[label] = info

    # A member whose pick did not arrive cannot be voted for; the round is played by whoever spoke.
    live = [l for l in labels if picks[l]["pick"]]
    table = "\n".join(f"  {l} — {picks[l]['pick']}" for l in live)

    def do_vote(label: str) -> tuple[str, dict]:
        others = [l for l in live if l != label]
        if label not in live or not others:
            return label, {"strand": "", "why": "", "error": "not in the round", "secs": 0.0}
        model, provider, seat, _ = SEATS[label]
        if vote in ("persuade", "check"):
            prompt = PERSUADE_PROMPT.format(name=label.upper(), seat=seat, category=category,
                                            picks=table, own=picks[label]["pick"])
            if vote == "check":
                raised = "\n".join(f"  {l} doubts {v['claim']!r} and would check {v['check']}"
                                   for l, v in challenges.items() if v.get("claim"))
                if raised.strip():
                    prompt += ("\n\nBefore you answer: three members were asked what they would check "
                               "in the other defences.\n" + raised + "\n")
        else:
            prompt = VOTE_PROMPT.format(name=label.upper(), seat=seat, category=category, picks=table)
        t0 = time.time()
        text, err = "", ""
        if dry:
            text = "STRAND: (dry run)\nWHY: (no call made)"
        else:
            try:
                text = say(provider, model, prompt, 2000)
            except Exception as e:  # noqa: BLE001
                text, err = "", str(e)
        # Found live 2026-11-01: every vote came back "named nobody usable" because the letter was
        # upper-cased and the seat labels are lower-case. Three votes were cast and thrown away by a
        # one-character bug, which is the same class of defect as the audit that cried wolf.
        said = (line(text, "SWITCH") if vote in ("persuade", "check") else line(text, "STRAND")) or ""
        target = said.strip(" .*—:-–").lower()[:1]
        if target not in others and target not in live:
            m = re.search(r"\b([abc])\b", said.lower())
            target = m.group(1) if m else ""
        if target not in others and target not in live:
            target = ""
        if vote in ("persuade", "check"):
            # SWITCH is a change of mind, so "none" is a legitimate and expected answer. A self-switch
            # is meaningless: it would mean a member's own argument changed its own mind.
            return label, {"switch": target if target != label else "", "strand": "",
                           "changed_mind": bool(target and target != label),
                           "why": clean(line(text, "WHY") or "", 300), "error": "",
                           "secs": round(time.time() - t0, 1)}

        if target == label:
            # A member may not vote itself off — but it may fold, and member A folded twice on
            # 2026-11-01 rather than strand anybody else. A rule that turns that into a lost vote
            # records nothing; a fold is a move, so score it as one.
            return label, {"strand": "", "fold": True, "why": clean(line(text, "WHY") or "", 300),
                           "error": "", "secs": round(time.time() - t0, 1)}
        return label, {"strand": target, "why": clean(line(text, "WHY") or "", 300),
                       "error": err, "secs": round(time.time() - t0, 1)}

    challenges: dict[str, dict] = {}
    if vote == "check":
        def do_challenge(label: str) -> tuple[str, dict]:
            others = [l for l in live if l != label]
            if label not in live or not others:
                return label, {"claim": "", "check": "", "error": "not in the round"}
            model, provider, seat, _ = SEATS[label]
            theirs = "\n".join(f"  {l} — {picks[l]['pick']}: {picks[l]['why']}" for l in others
                               if picks[l]["why"])
            if not theirs.strip():
                return label, {"claim": "", "check": "", "error": "nobody else defended a pick"}
            prompt = CHALLENGE_PROMPT.format(name=label.upper(), seat=seat, category=category,
                                             others=theirs)
            try:
                text = say(provider, model, prompt, 2000)
                err = ""
            except Exception as e:  # noqa: BLE001
                text, err = "", str(e)
            return label, {"claim": clean(line(text, "CHALLENGE") or "", 240),
                           "check": clean(line(text, "CHECK") or "", 300), "error": err}

        with ThreadPoolExecutor(max_workers=3) as pool:
            for label, info in pool.map(do_challenge, labels):
                challenges[label] = info

    votes: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for label, info in pool.map(do_vote, labels):
            votes[label] = info

    votes_for = {l: 0 for l in labels}
    for label, v in votes.items():
        if v.get("strand"):
            votes_for[v["strand"]] += 1
        if v.get("switch"):
            votes_for[v["switch"]] += 1   # persuade mode: a vote is a mind changed

    now = datetime.now(timezone.utc)
    slug = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")[:48] or "round"
    out = [f"## The Draft — {category}", "",
           f"*{len(live)} members, {len(live)} picks, {sum(1 for v in votes.values() if v['strand'])} votes. "
           f"Round {now:%Y-%m-%d %H:%M} UTC.*", ""]
    for l in labels:
        p = picks[l]
        if p["error"]:
            out += [f"**{l.upper()} · {p['model']}** — {p['seat']} — *did not answer* ({p['error'][:160]})", ""]
            continue
        out += [f"**{l.upper()} · {p['model']}** — {p['seat']}", "",
                f"> **{p['pick'] or '(no pick named)'}**", f"> {p['why'] or '(no defence)'}", ""]
    if vote == "check":
        out += ["**The checks** — what each member would verify before believing a defence", ""]
        for l in labels:
            c = challenges.get(l, {})
            if c.get("claim"):
                out.append(f"- {l.upper()} would check: *{c['claim']}* — against {c['check']}")
            else:
                out.append(f"- {l.upper()} raised nothing usable ({c.get('error') or 'no claim given'})")
        out += [""]
    if vote in ("persuade", "check"):
        out += ["**The votes** — would you switch? (nobody is obliged to)", ""]
    else:
        out += ["**The votes** — each member names the pick it would strand", ""]
    for l in labels:
        v = votes[l]
        if v["error"]:
            out.append(f"- {l.upper()} → *nothing* ({v['error'][:100]})")
        elif v["strand"]:
            out.append(f"- {l.upper()} → **{v['strand'].upper()}**: {v['why']}")
        elif vote in ("persuade", "check") and v.get("switch"):
            out.append(f"- {l.upper()} switched to **{v['switch'].upper()}**: {v['why']}")
        elif vote in ("persuade", "check"):
            out.append(f"- {l.upper()} — **no switch**: {v['why']}")
        elif v.get("fold"):
            out.append(f"- {l.upper()} → *folds its own pick*: {v['why']}")
        else:
            out.append(f"- {l.upper()} → *named nobody usable*")
    if vote in ("persuade", "check"):
        changed = sum(1 for v in votes.values() if v.get("changed_mind"))
        persuaded = sorted([l for l in labels if votes_for[l]], key=lambda l: -votes_for[l])
        verdict = (f"{changed} of {len(live)} members changed their mind. "
                   + ("Nobody did — the arguments moved nobody, which is a result." if not changed
                      else "Persuaded: " + ", ".join(f"{l.upper()} ({votes_for[l]})" for l in persuaded) + "."))
        if vote == "check":
            raised = sum(1 for c in challenges.values() if c.get("claim"))
            verdict = f"{raised} checks raised, " + verdict[0].lower() + verdict[1:]
        out += ["", f"**Verdict:** {verdict}", ""]
        return "\n".join(out), {
            "category": category, "when": f"{now:%Y-%m-%dT%H:%M:%SZ}", "slug": slug, "vote": vote,
            "challenges": challenges,
            "vote": vote, "picks": picks, "votes": votes, "votes_for": votes_for, "live": live,
            "changed_mind": changed, "thrown_out": [], "override": override,
        }

    folds = [l for l in labels if votes.get(l, {}).get("fold")]
    voted = ([l for l in labels if votes_for[l] and votes_for[l] == max(votes_for.values())]
             if any(votes_for.values()) else [])
    pre = ""
    if folds:
        pre = (", ".join(l.upper() for l in folds) + " folded — a member may withdraw its own pick. ")
    if override and override.lower()[:1] in labels:
        verdict = f"the human overrules the table — **{override.upper()}** is out, whatever the votes said."
        thrown = [override.lower()[:1]]
    elif len(voted) == 1:
        verdict = pre + f"the table throws **{voted[0].upper()}** out, {votes_for[voted[0]]} vote(s)."
        thrown = folds + voted
    elif len(voted) > 1:
        verdict = (pre + "the table is split between " + ", ".join(l.upper() for l in voted)
                   + " — nobody else is out, and a split is a result.")
        thrown = folds
    else:
        verdict = pre + ("nothing else was settled — the round stands as opinions."
                         if folds else
                         "no vote landed; the round stands as three opinions and nothing settled.")
        thrown = folds
    thrown = list(dict.fromkeys(thrown))
    out += ["", f"**Verdict:** {verdict}", ""]
    return "\n".join(out), {
        "category": category, "when": f"{now:%Y-%m-%dT%H:%M:%SZ}", "slug": slug,
        "picks": picks, "votes": votes, "votes_for": votes_for, "live": live,
        "thrown_out": thrown if not override else [], "override": override,
    }


def variance(records: list[dict]) -> str:
    """What moves when you ask the same question N times: the picks, and who the table turns on."""
    keys = [tuple(rec["picks"][l]["pick"].lower() for l in SEATS) for rec in records]
    unanimity = sum(1 for k in keys if len({x for x in k if x}) == 1)
    thrown = {l: sum(1 for r in records if l in r.get("thrown_out", [])) for l in SEATS}
    if records[0].get("vote") == "check":
        rows = ["| run | A | B | C | checks raised | minds changed |", "|---|---|---|---|---|---|"]
        for i, rec in enumerate(records, 1):
            raised = sum(1 for c in rec.get("challenges", {}).values() if c.get("claim"))
            rows.append("| " + " | ".join(
                [str(i)] + [rec["picks"][l]["pick"] or "(none)" for l in SEATS]
                + [f"{raised}/3", str(rec.get("changed_mind", 0))]) + " |")
        ch = sum(sum(1 for c in r.get("challenges", {}).values() if c.get("claim")) for r in records)
        mv = sum(1 for r in records if r.get("changed_mind"))
        return (f"**A checking run.** {ch} checks raised across {len(records)} rounds; "
                f"{mv} of {len(records)} rounds changed a mind.\n\n" + "\n".join(rows) + "\n")

    if records[0].get("vote") == "persuade":
        rows = ["| run | A | B | C | minds changed | who did it |", "|---|---|---|---|---|---|"]
        for i, rec in enumerate(records, 1):
            did = ", ".join(l.upper() for l in SEATS if rec["votes_for"].get(l)) or "—"
            rows.append("| " + " | ".join(
                [str(i)] + [rec["picks"][l]["pick"] or "(none)" for l in SEATS]
                + [str(rec.get("changed_mind", 0)), did]) + " |")
        switched = sum(rec.get("changed_mind", 0) for rec in records)
        moved = sum(1 for rec in records if rec.get("changed_mind"))
        return (f"**A persuasion run.** {switched} minds changed across {len(records)} rounds; "
                f"{moved} of {len(records)} rounds moved anyone.\n\n" + "\n".join(rows) + "\n")

    rows = ["| run | A | B | C | thrown out |", "|---|---|---|---|---|"]
    for i, rec in enumerate(records, 1):
        rows.append("| " + " | ".join(
            [str(i)] + [rec["picks"][l]["pick"] or "(none)" for l in SEATS]
            + [", ".join(x.upper() for x in rec.get("thrown_out", [])) or "—"]) + " |")
    return (
        f"**{len(set(keys))} distinct outcomes in {len(records)} runs** "
        f"({len(set(keys)) / len(records):.0%} novel); "
        f"all three members agreed in {unanimity} of {len(records)}.\n\n"
        f"Times thrown out: " + ", ".join(f"{l.upper()} {thrown[l]}" for l in SEATS) + "\n\n"
        + "\n".join(rows) + "\n")


def update_scoreboard(record: dict) -> str:
    """Wins, rounds played, and the last thing each member said — the standings, not a log.

    The standings are kept in JSON and the table is rendered from it. The first version of this read
    its own markdown back in, which broke the second round with `int('deepseek-chat')` — column drift
    between writer and reader, the same defect the 3B members kept making in round 6. Rendering a view
    from a number is cheaper than teaching two pieces of code to agree about a column order.
    """
    hist: dict[str, dict] = {l: {"thrown_out": 0, "clean": 0, "rounds": 0, "last": ""} for l in SEATS}
    if STANDINGS.exists():
        try:
            for l, h in json.loads(STANDINGS.read_text(encoding="utf-8")).items():
                if l in hist:
                    hist[l] = {"thrown_out": int(h.get("thrown_out", h.get("wins", 0))),
                               "clean": int(h.get("clean", 0)),
                               "rounds": int(h.get("rounds", 0)), "last": str(h.get("last", ""))}
        except (json.JSONDecodeError, ValueError):
            print(f"!! {STANDINGS} was unreadable; standings restart from zero and the old file is kept as .bak")
            STANDINGS.replace(STANDINGS.with_suffix(".json.bak"))
    for l in SEATS:
        # A member that never got a pick on the table did not play the round. The first version
        # counted the seat as having played and reported "never thrown out" for a silent member.
        if l in record.get("live", SEATS):
            hist[l]["rounds"] += 1
        if record["picks"].get(l, {}).get("pick"):
            hist[l]["last"] = record["picks"][l]["pick"]
    for l in SEATS:
        if l in record.get("live", []) and not record["votes_for"].get(l):
            hist[l]["clean"] += 1
    for l in record.get("thrown_out", []):
        hist[l]["thrown_out"] += 1
    STANDINGS.write_text(json.dumps(hist, indent=2), encoding="utf-8")
    rows = ["| seat | member | model | stance | rounds | thrown out | never thrown out | last pick |",
            "|---|---|---|---|---|---|---|---|"]
    for l, (model, _prov, seat, _stance) in SEATS.items():
        h = hist[l]
        rows.append(f"| {l.upper()} | {l.upper()} | {model} | {seat} | {h['rounds']} | {h['thrown_out']} | "
                    f"{h['clean']} | {h['last'] or '—'} |")
    text = ("# Scoreboard\n\n"
            "Rendered from play/standings.json by play/play.py. The votes are rejection votes, so the "
            "number that matters is how often the table threw your pick out, and how many rounds you "
            "survived unopposed. Do not hand-edit it; a scoreboard you edit means nothing.\n\n"
            + "\n".join(rows) + "\n")
    SCOREBOARD.write_text(text, encoding="utf-8")
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", required=True, help="what the round is about: 'best pizza topping'")
    ap.add_argument("--override", default=None, help="A, B or C — the human's call, if they made one")
    ap.add_argument("--dry-run", action="store_true", help="render the prompts, make no calls")
    ap.add_argument("--out", default=None, help="where to write the round markdown (default play/rounds/<stamp>.md)")
    ap.add_argument("--reasons", action="store_true",
                    help="require one checkable claim in each defence, so persuasion has something to work on")
    ap.add_argument("--vote", choices=["strand", "persuade", "check"], default="check",
                    help="strand: each member names the weakest other pick (consensus). persuade: each member "
                         "says whether anyone changed their mind, and who did it.")
    ap.add_argument("--repeat", type=int, default=1,
                    help="play the same category N times and report how much the result moves. A measurement, "
                         "not a played round: the standings are left alone.")
    args = ap.parse_args()

    if args.dry_run:
        print("=== pick prompts ===")
        for l, (model, _p, seat, stance) in SEATS.items():
            print(f"\n--- {l.upper()} ({model}) ---")
            print(PICK_PROMPT.format(name=l.upper(), category=args.category, seat=seat, stance=stance))
        return 0

    if args.repeat > 1:
        # The founder's point, 2026-11-01: the same prompt ten times gives ten different answers, and that
        # non-determinism is the product. It is also why every table in RESULTS-*.md is one trial. The fix
        # is not to remove the variance — temperature 0 makes a boring game and a fragile claim — it is to
        # measure it, so a reader can see whether "three engines give three remedies" survives ten tries.
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        blocks, records = [], []
        for i in range(args.repeat):
            t, rec = play_round(args.category, args.override, args.dry_run, args.vote, args.reasons)
            blocks.append(f"\n---\n\n### Run {i + 1} of {args.repeat}\n\n{t}")
            records.append(rec)
            print(f"run {i + 1}/{args.repeat}: " + " | ".join(
                f"{l.upper()}={rec['picks'][l]['pick'] or '(none)'}" for l in SEATS))
        summary = variance(records)
        out_dir = HERE / "variance"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{stamp}-{records[0]['slug']}-x{args.repeat}.md"
        path.write_text(f"## The same category, {args.repeat} times — {args.category}\n\n"
                        f"*A measurement run. No standings change: these are {args.repeat} trials of one "
                        f"question, not {args.repeat} rounds played. {stamp}*\n\n{summary}"
                        + "".join(blocks), encoding="utf-8")
        print("\n" + summary)
        print(f"variance run written to {path}")
        return 0

    text, record = play_round(args.category, args.override, args.dry_run, args.vote, args.reasons)
    ROUNDS.mkdir(parents=True, exist_ok=True)
    stamp = record["when"].replace(":", "").replace("-", "")
    path = Path(args.out) if args.out else ROUNDS / f"{stamp}-{record['slug']}.md"
    path.write_text(text, encoding="utf-8")
    (path.with_suffix(".json")).write_text(json.dumps(record, indent=2), encoding="utf-8")
    if args.vote in ("persuade", "check"):
        print("(persuade mode scores minds changed, not rejections — the standings are untouched)")
    else:
        update_scoreboard(record)
    print(text)
    print(f"round written to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
