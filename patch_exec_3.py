from pathlib import Path
p = Path("/tmp/bench/play/play.py")
s = p.read_text()

# ---------------------------------------------------------------- rendering
s = s.replace('''    if vote == "check":
        out += ["**The checks** — what each member would verify before believing a defence", ""]
        for l in labels:
            c = challenges.get(l, {})
            if c.get("claim"):
                out.append(f"- {l.upper()} would check: *{c['claim']}* — against {c['check']}")''',
'''    if vote in ("check", "exec"):
        head = ("**The checks** — what each member would verify before believing a defence"
                if vote == "check" else
                "**The checks** — one command each, chosen to settle a claim in someone else's defence")
        out += [head, ""]
        for l in labels:
            c = challenges.get(l, {})
            if c.get("claim"):
                tail = f" — against {c['check']}" + (f" (settles it if: {c['settles']})"
                                                     if c.get("settles") else "")
                out.append(f"- {l.upper()} would check: *{c['claim']}*{tail}")''', 1)

old = '''    if vote == "check" and answers:
        out += ["**The answers** — a claim was challenged, so the member holding it has to say what would "
                "happen", ""]'''
new = '''    if vote == "exec" and answers:
        out += ["**The executed checks** — predicted, then run, then answered. The prediction is made "
                "before the output, so a member cannot claim it expected what it did not", ""]
        for l in labels:
            a = answers.get(l, {})
            if not a.get("challenged"):
                out.append(f"- {l.upper()} — nothing of its own was aimed at with a command")
                continue
            verdict = a.get("refused") or "ran"
            out += [f"- **{l.upper()}**, checked by {a.get('asker', '?').upper()} on *\\"{a['claim']}\\"*",
                    f"  - command: `{a['cmd'] or '(none)'}` — {verdict}",
                    f"  - predicted: {a.get('predict') or '(did not predict)'}",
                    "  - printed:",
                    "    ```",
                    ] + ["    " + ln for ln in (a.get("output") or "(nothing)").splitlines()[:12]] + [
                    "    ```",
                    f"  - then **{a.get('stance') or 'did not answer'}s**: {a.get('says', '')}"]
        out += [""]
    if vote == "check" and answers:
        out += ["**The answers** — a claim was challenged, so the member holding it has to say what would "
                "happen", ""]'''
assert old in s
s = s.replace(old, new, 1)

# verdict line for exec
s = s.replace('''        if vote == "check":
            raised = sum(1 for c in challenges.values() if c.get("claim"))''',
'''        if vote == "exec":
            raised = sum(1 for c in challenges.values() if c.get("claim"))
            ran = sum(1 for a in answers.values() if a.get("challenged") and not a.get("refused"))
            refused = sum(1 for a in answers.values() if a.get("challenged") and a.get("refused"))
            held = sum(1 for a in answers.values() if a.get("stance") == "stand")
            moved = sum(1 for a in answers.values() if a.get("stance") in ("amend", "withdraw"))
            verdict = (f"{raised} checks named, {ran} run and {refused} refused by the executor; of the "
                       f"members checked with a real result, {held} stood and {moved} amended or withdrew. "
                       + verdict[0].lower() + verdict[1:])
        elif vote == "check":
            raised = sum(1 for c in challenges.values() if c.get("claim"))''', 1)

# record
s = s.replace('''            "changed_mind": changed, "thrown_out": [], "override": override,''',
'''            "changed_mind": changed, "thrown_out": [], "override": override,
            "executed": {l: a for l, a in answers.items() if a.get("challenged")},''', 1)

# CLI
s = s.replace('''    ap.add_argument("--vote", choices=["strand", "persuade", "check"], default="check",''',
'''    ap.add_argument("--vote", choices=["strand", "persuade", "check", "exec"], default="check",''', 1)
s = s.replace('''    ap.add_argument("--reasons", action="store_true",''',
'''    ap.add_argument("--reasons", action="store_true",''', 1)

s = s.replace('''    if args.vote in ("persuade", "check"):
        print("(persuade mode scores minds changed, not rejections — the standings are untouched)")''',
'''    if args.vote in ("persuade", "check", "exec"):
        print("(persuade mode scores minds changed, not rejections — the standings are untouched)")''', 1)
p.write_text(s)
print("rendered")
