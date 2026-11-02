from pathlib import Path
p = Path("/tmp/bench/play/play.py")
s = p.read_text()

# ---------------------------------------------------------------- parse both branches
old = '''                           "settles": clean(line(text, "SETTLES") or "", 300), "error": err}'''
new = '''                           "true_show": clean(line(text, "IF TRUE") or "", 300),
                           "wrong_show": clean(line(text, "IF WRONG") or "", 300),
                           "error": err}'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- gate before the run, classify after
old = '''            # The prediction is made before the run and recorded before the run. A member that sees the
            # output first can always claim it expected it.
            result = run_check(c["check"])'''
new = '''            # The gate is decided from the two branches alone, before anything runs: no output could tell
            # this claim from its opposite, so the check is decoration whatever it prints.
            disc, why_not = discriminates(c.get("true_show", ""), c.get("wrong_show", ""))
            # The prediction is made before the run and recorded before the run. A member that sees the
            # output first can always claim it expected it.
            result = run_check(c["check"])'''
assert old in s
s = s.replace(old, new, 1)

old = '''                    cmd=result["cmd"] or c["check"],
                    predict=clean(line(pred, "PREDICT") or "", 200) or "(did not predict)",
                    output=body), 2000), ""'''
new = '''                    cmd=result["cmd"] or c["check"],
                    true_show=c.get("true_show") or "(not stated)",
                    wrong_show=c.get("wrong_show") or "(not stated)",
                    predict=clean(line(pred, "PREDICT") or "", 200) or "(did not predict)",
                    output=body), 2000), ""'''
assert old in s
s = s.replace(old, new, 1)

old = '''            stance = (line(text, "STANCE") or "").strip().strip(".*").lower()
            stance = next((w for w in ("stand", "amend", "withdraw") if stance.startswith(w)), "")
            return label, {"challenged": True, "asker": asker, "claim": c["claim"],
                           "settles": c.get("settles", ""), "cmd": result["cmd"],'''
new = '''            stance = (line(text, "STANCE") or "").strip().strip(".*").lower()
            stance = next((w for w in ("stand", "amend", "withdraw") if stance.startswith(w)), "")
            matched = (line(text, "MATCHES") or "").strip().strip(".*").lower()
            matched = next((w for w in ("true-branch", "wrong-branch", "neither")
                            if matched.startswith(w.split("-")[0])), matched[:20])
            return label, {"challenged": True, "asker": asker, "claim": c["claim"],
                           "true_show": c.get("true_show", ""), "wrong_show": c.get("wrong_show", ""),
                           "discriminates": disc, "why_not": why_not, "matches": matched,
                           "cmd": result["cmd"],'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- rendering
old = '''                tail = f" — against {c['check']}" + (f" (settles it if: {c['settles']})"
                                                     if c.get("settles") else "")
                out.append(f"- {l.upper()} would check: *{c['claim']}*{tail}")'''
new = '''                d, why_not = discriminates(c.get("true_show", ""), c.get("wrong_show", ""))
                tail = f" — against `{c['check']}`"
                if c.get("true_show") or c.get("wrong_show"):
                    tail += (f"\\n    - if true: {c.get('true_show') or '(not stated)'}"
                             f"\\n    - if wrong: {c.get('wrong_show') or '(not stated)'}"
                             f"\\n    - **{'could come out either way' if d else 'cannot discriminate: ' + why_not}**")
                out.append(f"- {l.upper()} would check: *{c['claim']}*{tail}")'''
assert old in s
s = s.replace(old, new, 1)

old = '''                    f"  - then **{a.get('stance') or 'did not answer'}s**: {a.get('says', '')}"]'''
new = '''                    f"  - gate: {'could come out either way' if a.get('discriminates') else 'cannot discriminate — ' + (a.get('why_not') or '')}",
                    f"  - landed in: **{a.get('matches') or 'not classified'}**",
                    f"  - then **{a.get('stance') or 'did not answer'}s**: {a.get('says', '')}"]'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- verdict line
old = '''            verdict = (f"{raised} checks named, {ran} run and {refused} refused by the executor; of the "
                       f"members checked with a real result, {held} stood and {moved} amended or withdrew. "
                       + verdict[0].lower() + verdict[1:])'''
new = '''            blind = sum(1 for a in answers.values() if a.get("challenged") and not a.get("discriminates"))
            neither = sum(1 for a in answers.values() if a.get("matches", "").startswith("neither"))
            verdict = (f"{raised} checks named, {blind} of them could not tell the claim from its opposite "
                       f"(decided before running), {ran} run and {refused} refused; of the members checked "
                       f"with a real result, {held} stood and {moved} amended or withdrew, and {neither} "
                       f"said the output matched neither branch. " + verdict[0].lower() + verdict[1:])'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- variance summary
old = '''            return (f"**An executing run.** {ch} checks named, {ran} run against the repository, "
                    f"{refused} refused by the executor, and {moved} claims amended or withdrawn across "
                    f"{len(records)} rounds; {mv} of {len(records)} rounds changed a mind.\\n\\n"
                    + "\\n".join(rows) + "\\n")'''
new = '''            blind = sum(1 for r in records for a in r.get("executed", {}).values()
                        if not a.get("discriminates"))
            neither = sum(1 for r in records for a in r.get("executed", {}).values()
                          if str(a.get("matches", "")).startswith("neither"))
            return (f"**An executing run.** {ch} checks named, of which **{blind} could not tell the claim "
                    f"from its opposite** before anything ran; {ran} executed, {refused} refused; {moved} "
                    f"claims amended or withdrawn and {neither} members said the output matched neither "
                    f"branch; {mv} of {len(records)} rounds changed a mind.\\n\\n" + "\\n".join(rows) + "\\n")'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s)
print("classification wired")
