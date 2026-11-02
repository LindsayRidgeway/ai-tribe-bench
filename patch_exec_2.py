from pathlib import Path
p = Path("/tmp/bench/play/play.py")
s = p.read_text()

# ---------------------------------------------------------------- challenge prompt: exec variant
old = '''            prompt = CHALLENGE_PROMPT.format(name=label.upper(), seat=seat, category=category,
                                             others=theirs)
            try:
                text = say(provider, model, prompt, 2000)
                err = ""
            except Exception as e:  # noqa: BLE001
                text, err = "", str(e)
            return label, {"claim": clean(line(text, "CHALLENGE") or "", 240),
                           "check": clean(line(text, "CHECK") or "", 300), "error": err}'''
new = '''            if vote == "exec":
                prompt = EXEC_PROMPT.format(name=label.upper(), seat=seat, category=category,
                                            facts=facts_sheet(), others=theirs,
                                            whitelist=WHITELIST_LINE)
            else:
                prompt = CHALLENGE_PROMPT.format(name=label.upper(), seat=seat, category=category,
                                                 others=theirs)
            try:
                text = say(provider, model, prompt, 2000)
                err = ""
            except Exception as e:  # noqa: BLE001
                text, err = "", str(e)
            return label, {"claim": clean(line(text, "CHALLENGE") or line(text, "CLAIM") or "", 240),
                           "check": clean(line(text, "CHECK") or "", 160),
                           "settles": clean(line(text, "SETTLES") or "", 300), "error": err}'''
assert old in s
s = s.replace(old, new, 1)

# a settled claim is a claim the round will actually run, so it is worth a full round's challenges
s = s.replace('''    challenges: dict[str, dict] = {}
    if vote == "check":''', '''    challenges: dict[str, dict] = {}
    if vote in ("check", "exec"):''', 1)

# ---------------------------------------------------------------- predict, run, defend
old = '''    answers: dict[str, dict] = {}
    if vote == "check":'''
new = '''    answers: dict[str, dict] = {}
    if vote == "exec":
        # Round 12 put the finding on the table: six imagined checks produced six stands, and one executed
        # check produced an immediate concession. The wake harness got hands (check.py) and stopped taking
        # the member's word for what a command would print. The game never did — a round could raise nine
        # checks and run none of them. This is the game with the same hands.
        aimed: dict[str, list] = {}
        for asker, c in challenges.items():
            if not c.get("claim"):
                continue
            target = owner_of(c["claim"], c.get("check", ""), picks, live, asker)
            if target:
                aimed.setdefault(target, []).append((asker, c))

        def do_exec(label: str) -> tuple[str, dict]:
            mine = aimed.get(label, [])
            if not mine:
                return label, {"challenged": False, "stance": "", "says": "", "error": ""}
            asker, c = mine[0]   # one executed check per member per round: three is a conversation
            model, provider, seat, _ = SEATS[label]
            pred, perr = "", ""
            try:
                pred = say(provider, model, PREDICT_PROMPT.format(
                    name=label.upper(), seat=seat, own_pick=picks[label]["pick"],
                    own_why=picks[label].get("why", ""), asker=asker.upper(),
                    claim=c["claim"], cmd=c["check"]), 2000)
            except Exception as e:  # noqa: BLE001 — a member that will not predict can still be shown
                perr = str(e)
            # The prediction is made before the run and recorded before the run. A member that sees the
            # output first can always claim it expected it.
            result = run_check(c["check"])
            shown = result["output"] or f"(not run — {result['refused']})"
            body = "\\n".join("      " + ln for ln in shown.splitlines()[:25]) or "      (no output)"
            try:
                text, err = say(provider, model, EXECUTED_DEFEND_PROMPT.format(
                    name=label.upper(), seat=seat, own_pick=picks[label]["pick"],
                    own_why=picks[label].get("why", ""), claim=c["claim"],
                    cmd=result["cmd"] or c["check"],
                    predict=clean(line(pred, "PREDICT") or "", 200) or "(did not predict)",
                    output=body), 2000), ""
            except Exception as e:  # noqa: BLE001
                text, err = "", str(e)
            stance = (line(text, "STANCE") or "").strip().strip(".*").lower()
            stance = next((w for w in ("stand", "amend", "withdraw") if stance.startswith(w)), "")
            return label, {"challenged": True, "asker": asker, "claim": c["claim"],
                           "settles": c.get("settles", ""), "cmd": result["cmd"],
                           "refused": result["refused"], "output": shown[:1200],
                           "predict": clean(line(pred, "PREDICT") or "", 240),
                           "expecting": clean(line(pred, "IF WRONG") or "", 240),
                           "stance": stance, "says": clean(line(text, "SAYS") or "", 400),
                           "error": err or perr}

        with ThreadPoolExecutor(max_workers=3) as pool:
            for label, info in pool.map(do_exec, labels):
                answers[label] = info
    if vote == "check":'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- votes: exec counts switches
s = s.replace('''        if vote in ("persuade", "check"):
            prompt = PERSUADE_PROMPT.format(''', '''        if vote in ("persuade", "check", "exec"):
            prompt = PERSUADE_PROMPT.format(''', 1)

s = s.replace('''                if raised.strip():
                    prompt += ("\\n\\nBefore you answer: three members were asked what they would check "
                               "in the other defences.\\n" + raised + "\\n")''',
'''                if raised.strip():
                    prompt += ("\\n\\nBefore you answer: three members were asked what they would check "
                               "in the other defences.\\n" + raised + "\\n")
            if vote == "exec":
                done = [f"  {l.upper()}: `{a['cmd']}` printed {a['output'][:240]!r} — {l.upper()} "
                        f"{a['stance'] + 's' if a.get('stance') else 'did not answer'}"
                        for l, a in answers.items() if a.get("challenged")]
                if done:
                    prompt += ("\\n\\nBefore you answer: these checks were RUN in this round, not imagined.\\n"
                               + "\\n".join(done) + "\\n")''', 1)

s = s.replace('''        said = (line(text, "SWITCH") if vote in ("persuade", "check") else line(text, "STRAND")) or ""''',
'''        said = (line(text, "SWITCH") if vote in ("persuade", "check", "exec") else line(text, "STRAND")) or ""''', 1)
s = s.replace('''        if vote in ("persuade", "check"):
            # SWITCH is a change of mind''', '''        if vote in ("persuade", "check", "exec"):
            # SWITCH is a change of mind''', 1)

p.write_text(s)
print("exec flow wired")
