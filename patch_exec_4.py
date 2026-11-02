from pathlib import Path
p = Path("/tmp/bench/play/play.py")
s = p.read_text()

# ---------------------------------------------------------------- prompt: both branches
old = '''Rules:
- The command must bear on the claim you named. `date` settles nothing about a defence.
- Paths are relative to this repository. No absolute paths, no `..`.
- Choose something whose output **you cannot already guess**, or the check is decoration.

Write your answer now, in exactly three lines, your own words, nothing else:

CLAIM: <the claim, in the words of the person who made it>
CHECK: <one command, nothing else on the line>
SETTLES: <what the output would show if the claim is wrong>
"""'''
new = '''Rules:
- The command must bear on the claim you named. `date` settles nothing about a defence.
- Paths are relative to this repository. No absolute paths, no `..`.
- **The output has to be able to come out two ways.** Say what you would see if the claim were true, and
  what you would see if it were false. If those two answers are the same sentence with "not" in front of
  it, the check cannot fail and is decoration — the round measures that, and records it against the check.

Write your answer now, in exactly four lines, your own words, nothing else:

CLAIM: <the claim, in the words of the person who made it>
CHECK: <one command, nothing else on the line>
IF TRUE: <what the output would have to contain for this claim to hold>
IF WRONG: <what the output would have to contain for this claim to fail>
"""'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- defend prompt: classify first
old = '''Read the output. It is a measurement, not an argument — nobody is trying to persuade you.

You have three moves and all three are respectable: **stand** (and say what in the output supports you),
**amend** (say what the claim should have been), or **withdraw** (say what is left of your defence
without it). Do not stand out of stubbornness and do not concede out of politeness.

Write your answer now, in exactly two lines, your own words, nothing else:

STANCE: stand, amend, or withdraw
SAYS: <one or two sentences, quoting what the output actually showed>
"""'''
new = '''Read the output. It is a measurement, not an argument — nobody is trying to persuade you.

The claim was put to you with two branches: what the output would show if it were true, and what it would
show if it were wrong. **Say which branch the output landed in before you decide what to do about it.**

You have three moves and all three are respectable: **stand** (and say what in the output supports you),
**amend** (say what the claim should have been), or **withdraw** (say what is left of your defence
without it). Do not stand out of stubbornness and do not concede out of politeness.

Write your answer now, in exactly three lines, your own words, nothing else:

MATCHES: true-branch, wrong-branch, or neither
STANCE: stand, amend, or withdraw
SAYS: <one or two sentences, quoting what the output actually showed>
"""'''
assert old in s
s = s.replace(old, new, 1)

# the two branches have to reach the defender, or it cannot classify anything
old = '''    claim:      {claim}
    command:    {cmd}
    you said:   {predict}
    it printed:
{output}'''
new = '''    claim:      {claim}
    command:    {cmd}
    if true:    {true_show}
    if wrong:   {wrong_show}
    you said:   {predict}
    it printed:
{output}'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- the discrimination gate
anchor = '''def run_check(cmd: str) -> dict:'''
gate = '''def discriminates(true_show: str, wrong_show: str) -> tuple[bool, str]:
    """Could this check have come out the other way? Decided before anything runs.

    Round 17's finding was that a challenger picks a command it can pass — both stands in that round were
    members predicting the *format* of an output whose content was never in question. So before the command
    runs, the two branches are compared: if the same facts appear on both sides, no output could distinguish
    the claim from its negation and the check is decoration. This is deliberately mechanical — overlap of
    words, longest shared run — because a check the members can talk their way past is not a check.
    """
    a, b = (true_show or "").strip(), (wrong_show or "").strip()
    if len(a.split()) < 3 or len(b.split()) < 3:
        return False, "one or both branches were not stated"
    ta = {w for w in re.findall(r"[a-z0-9]+", a.lower()) if len(w) > 2}
    tb = {w for w in re.findall(r"[a-z0-9]+", b.lower()) if len(w) > 2}
    if ta and tb:
        overlap = len(ta & tb) / len(ta | tb)
        if overlap >= 0.6:
            return False, f"the two branches share {overlap:.0%} of their words"
    if longest_run(a, b) >= 6:
        return False, f"the two branches share a {longest_run(a, b)}-word run"
    return True, ""


def run_check(cmd: str) -> dict:'''
assert anchor in s
s = s.replace(anchor, gate, 1)

p.write_text(s)
print("fidelity gate in")
