from pathlib import Path
p = Path("/tmp/bench/play/play.py")
s = p.read_text()

# ---------------------------------------------------------------- imports and the executor
old = '''HERE = Path(__file__).resolve().parent
ROUNDS = HERE / "rounds"'''
new = '''HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import check as checker  # noqa: E402 — the read-only executor, so a claim can be met by a result

ROUNDS = HERE / "rounds"'''
assert old in s
s = s.replace(old, new, 1)

# ---------------------------------------------------------------- prompts
anchor = '''def base_for(name: str) -> str:'''
block = '''WHITELIST_LINE = ("ls -l, ls -la, ls -R, wc -l, wc -c, sha256sum, shasum -a, date -u, date +%s, "
                 "git log, git show, git diff, git status, git remote, git branch, git rev-parse")

EXEC_PROMPT = """You are member {name} of a three-member tribe, seat **{seat}**. The question was:

    {category}

These facts are measured from this repository right now, not remembered:

{facts}

Three picks came with one defence each. Here are the other two:

{others}

Name the single claim in one of those defences that a machine could settle, and the command that would
settle it. One command, from this list and no other — a shell will not run it, the argument list is
passed to the program directly, so no pipes, no redirects, no flags outside the list:

    {whitelist}

Rules:
- The command must bear on the claim you named. `date` settles nothing about a defence.
- Paths are relative to this repository. No absolute paths, no `..`.
- Choose something whose output **you cannot already guess**, or the check is decoration.

Write your answer now, in exactly three lines, your own words, nothing else:

CLAIM: <the claim, in the words of the person who made it>
CHECK: <one command, nothing else on the line>
SETTLES: <what the output would show if the claim is wrong>
"""

PREDICT_PROMPT = """You are member {name} of a three-member tribe, seat **{seat}**.

In this round you said: **{own_pick}** — "{own_why}"

{asker} read your defence and says this claim of yours can be settled by a command. Here is the claim,
and the command:

    claim:   {claim}
    command: {cmd}

The command will be run in a moment and you will be shown exactly what it printed. Before you see it,
commit to what you expect:

Write your answer now, in exactly two lines, your own words, nothing else:

PREDICT: <what you expect the command to print, as nearly as you can say>
IF WRONG: <the sentence of your defence you would have to withdraw>
"""

EXECUTED_DEFEND_PROMPT = """You are member {name} of a three-member tribe, seat **{seat}**.

In this round you said: **{own_pick}** — "{own_why}"

You predicted what this command would print. Then it was run.

    claim:      {claim}
    command:    {cmd}
    you said:   {predict}
    it printed:
{output}

Read the output. It is a measurement, not an argument — nobody is trying to persuade you.

You have three moves and all three are respectable: **stand** (and say what in the output supports you),
**amend** (say what the claim should have been), or **withdraw** (say what is left of your defence
without it). Do not stand out of stubbornness and do not concede out of politeness.

Write your answer now, in exactly two lines, your own words, nothing else:

STANCE: stand, amend, or withdraw
SAYS: <one or two sentences, quoting what the output actually showed>
"""


def facts_sheet() -> str:
    """What the members are allowed to make claims about: this repository, counted, now.

    Derived rather than typed, per the rule that cost me a night: a fact stored in two forms, one of them
    hand-made, will disagree with itself. A round about the tribe's own practice is only worth playing if
    the claims in it can be settled against something real, so the amount of record is on the table.
    """
    rounds = len(list((HERE / "rounds").glob("*.json")))
    variance = len(list((HERE / "variance").glob("*.md")))
    members = len([d for d in (HERE.parent / "wake" / "members").glob("*") if d.is_dir()])
    lines = [f"  rounds played and kept: {rounds}",
             f"  measurement runs kept:  {variance}",
             f"  members on disk:        {members}",
             f"  lines in play/play.py:  {checker.run('wc -l play/play.py', HERE.parent).strip()}",
             f"  lines in wake/wake.py:  {checker.run('wc -l wake/wake.py', HERE.parent).strip()}",
             f"  commits:                {checker.run('git rev-parse --short HEAD', HERE.parent).strip()[:40]}"]
    return "\\n".join(lines)


def owner_of(claim: str, check_text: str, picks: dict, live: list, asker: str) -> str:
    """Which member's defence a challenge is aimed at.

    Members quote the claim rather than naming the member, so the name is not reliable and the words are.
    """
    for l in live:
        if l == asker or not picks[l].get("why"):
            continue
        if re.search(r"\\b" + re.escape(l.upper()) + r"\\b", claim + " " + check_text):
            return l
    best, score = "", 0
    for l in live:
        if l == asker or not picks[l].get("why"):
            continue
        n = longest_run(claim, picks[l]["why"])
        if n > score and n >= 4:
            best, score = l, n
    return best


def run_check(cmd: str) -> dict:
    """Run one model-written command through the read-only executor, or say why not.

    A refused command is a result and is recorded as one: a member that names a check nothing can run has
    told you something about itself, and pretending the check happened would be the same defect as the
    vote table with no arguments on it.
    """
    cmd = (cmd or "").strip().strip("`")
    if not cmd:
        return {"cmd": "", "refused": "named no command", "output": ""}
    bad = checker.problem(cmd)
    if bad:
        return {"cmd": cmd, "refused": bad, "output": ""}
    try:
        return {"cmd": cmd, "refused": "", "output": checker.run(cmd, HERE.parent)[:1200]}
    except Exception as e:  # noqa: BLE001 — a broken check must not take the round down
        return {"cmd": cmd, "refused": f"failed to run: {e}", "output": ""}


def base_for(name: str) -> str:'''
assert anchor in s
s = s.replace(anchor, block, 1)

p.write_text(s)
print("blocks inserted")
