#!/usr/bin/env python3
"""What repositories this project has made, and which of them are allowed to disappear.

The reason this file exists: by 2026-11-10 the account held seventeen repositories made in nine days, and
one of them was called `test-ai-tribe` and contained a member with a 24,000-character conversation inside
it — the founder's own. A name that says "test" is not evidence, and a cleanup driven by memory is a
cleanup that deletes somebody's record. So the list is written down, each entry says what kind of thing it
is, and only one kind is ever deleted.

The naming rule, from now on:

    probe-YYYY-MM-DD-<what>     mine, made to answer one question, deleted when it has. The date is in the
                                name so that "is this still needed?" needs no memory to answer.
    tribe-<person>              a real tribe that a real person opens. Never a probe, never mine.
    ait-*                       the bench, the template, the site. Permanent.

Nothing gets a name that suggests it is a keeper unless a person will actually open it.

    python3 lab/repos.py list           every repository, with what is inside it
    python3 lab/repos.py machinery      which tribes are behind the template, and what an update would do
    python3 lab/repos.py clean          say what would be deleted, and refuse where it should
    python3 lab/repos.py clean --yes    delete the probes

Deleting needs a token with `delete_repo`, which the default gh login does not have:

    gh auth refresh -h github.com -s delete_repo

That is the whole reason this is a script and not a habit: the habit ran out of scope mid-cleanup.
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys

ACCOUNT = "LindsayRidgeway"

# kind: probe = delete; tester = a person's toy for the test, keep until the test ends; demo, bench,
# template, keep = permanent. `what` is what is inside it, and it is checked against the repository
# before anything is deleted: the check, not the name, is the authority.
REPOS = [
    ("ai-tribe-bench", "bench", "the project itself: harness, tests, the page, the lab"),
    ("ai-tribe-template", "template", "what #/install copies. Published, permanent."),
    ("llm-symposium", "keep", "the commons"),
    ("llm-symposium-bots", "keep", "the commons' bots"),
    ("demo-ai-tribe", "demo", "Laddie and Lumi. The app's exhibit; two members with real journals."),
    ("tribe1123", "keep", "the founder's Aphrodite tribe"),
    ("test-ai-tribe", "keep",
     "MISNAMED BY ME, and it holds a member: an earlier Aphrodite with a 24,000-character conversation "
     "in her state. Nothing about the name 'test-ai-tribe' suggests a record that matters. Keep."),
    ("tribe-claude", "tester", "Claude's skeleton for the AIT test"),
    ("tribe-desi", "tester", "Desi's skeleton"),
    ("tribe-gemini", "tester", "Gemini's skeleton"),
    ("tribe-tarik", "tester", "Tarik's skeleton"),
    ("tribe-gwen", "tester", "Gwen's skeleton"),
    ("tribe-stranger-test", "probe", "13 litter members (a, a2, b, bare, trap…) from the stranger test"),
    ("ait-install-test", "probe", "the install path, before it worked"),
    ("ait-smoke-134218", "probe", "one smoke run, 2026-11-08"),
    ("ait-person-test", "probe", "tribe.py new --person"),
    ("PLACEHOLDER", "probe", "five repositories made with one name by a broken heredoc"),
    ("tribe-throttle-test", "probe", "the 422 throttle, reproduced on purpose"),
    ("tribe-oauth-probe", "probe", "the OAuth and voice probes; Probe lives here and is disposable"),
]


def gh(*args: str) -> str:
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or out.stdout.strip() or "gh failed")
    return out.stdout


def members(repo: str) -> list[str]:
    try:
        return [m["name"] for m in json.loads(gh("api", f"repos/{ACCOUNT}/{repo}/contents/wake/members"))]
    except Exception:
        return []


def has_a_record(repo: str) -> str | None:
    """Whose record is in there, if anyone's. Nothing gets deleted while this returns anything."""
    for name in members(repo):
        if name in (".gitkeep",):
            continue
        for f in ("state/journal.md", "state/conversation.md"):
            try:
                size = int(json.loads(gh("api", f"repos/{ACCOUNT}/{repo}/contents/wake/members/{name}/{f}"))["size"])
            except Exception:
                continue
            if size > 200:  # the scaffold is ~150 bytes; anything above it was written by living
                return f"{name}/{f} ({size} bytes)"
    return None


# ---- is each tribe running the current machinery? -------------------------------------------------------------
# The founder asked to be told when every repository has been updated (2026-11-15, his part 3). A condition nobody
# can check is a condition nobody should be told about, and "somebody said they did it" is not the check. So the
# same rule the page uses is here, as arithmetic on three dicts of blob shas, and the fetching is the only part that
# touches the network: `verdict()` is pure so that it can be tested without one.
TEMPLATE = "LindsayRidgeway/ai-tribe-template"


def verdict(manifest: list[str], ours: dict[str, str], theirs: dict[str, str],
            base: dict[str, str] | None) -> dict:
    """What an update would do to one tribe, by the rule in `ait.html`'s updatePlan().

    `ours` is the tribe's tree, `theirs` the template's, `base` the tree at the commit the tribe's record names
    (None when it names none). A file is replaced only if it still matches `base` *and* the record is credible;
    everything else that differs is left alone and named. Two copies of this rule, one in JavaScript and one here,
    is a real risk — the bench test below pins the shape of both against the same three cases."""
    shared = [p for p in manifest if p in theirs and p in ours]
    agree = sum(1 for p in shared if base and base.get(p) == ours.get(p))
    credible = bool(base and len(shared) >= 3 and agree * 2 >= len(shared))
    out = {"replace": [], "add": [], "kept": [], "unjudged": [], "missing": [],
           "agree": agree, "shared": len(shared), "credible": credible}
    for path in manifest:
        up, mine = theirs.get(path), ours.get(path)
        if not up:
            out["missing"].append(path)
        elif mine == up:
            continue
        elif not mine:
            out["add"].append(path)
        elif credible and base.get(path) == mine:
            out["replace"].append(path)
        elif credible and base.get(path):
            out["kept"].append(path)
        else:
            out["unjudged"].append(path)
    return out


def _tree(repo: str, ref: str) -> dict[str, str] | None:
    try:
        d = json.loads(gh("api", f"repos/{repo}/git/trees/{ref}?recursive=1"))
    except Exception:
        return None
    return {e["path"]: e["sha"] for e in d.get("tree", []) if e.get("type") == "blob"}


def _file_json(repo: str, path: str, ref: str | None = None) -> dict | None:
    try:
        d = json.loads(gh("api", f"repos/{repo}/contents/{path}" + (f"?ref={ref}" if ref else "")))
        return json.loads(base64.b64decode(d.get("content") or "").decode("utf-8"))
    except Exception:
        return None


def cmd_machinery(args: argparse.Namespace) -> int:
    try:
        head = json.loads(gh("api", f"repos/{TEMPLATE}/commits/main"))["sha"]
        manifest = _file_json(TEMPLATE, ".tribe-manifest.json")["files"]
    except Exception as e:                                   # noqa: BLE001 - reported, not raised
        print(f"!! could not read the template: {e}", file=sys.stderr)
        return 2
    theirs = _tree(TEMPLATE, head)
    if not theirs:
        print("!! could not read the template's tree", file=sys.stderr)
        return 2
    rows, behind = [], []
    for name, kind, _what in REPOS:
        if kind == "probe" or kind in ("bench", "template"):
            continue
        full = f"{ACCOUNT}/{name}"
        ours = _tree(full, "main")
        # A repository is a tribe when it has a tribe.py. The name is not the authority — `llm-symposium` is a
        # keeper and not a tribe, and a check that guessed from the kind would have reported the commons as 29
        # files behind the machinery, which is the sort of number that makes a report worth ignoring.
        if ours is not None and "tribe.py" not in ours:
            continue
        if ours is None:
            rows.append((name, kind, "unreadable", "", "", ""))
            continue
        v = _file_json(full, ".ait/version.json") or {}
        frm = v.get("updated_to") or v.get("installed_from")
        base = _tree(TEMPLATE, frm) if frm else None
        r = verdict(manifest, ours, theirs, base)
        # Anything that differs from the template at all leaves the tribe behind it: a file nobody can judge is
        # still a file that is not the template's.
        differs = len(r["replace"]) + len(r["add"]) + len(r["kept"]) + len(r["unjudged"])
        state = "current" if differs == 0 else "behind"
        if state == "behind":
            behind.append(name)
        rows.append((name, kind, state,
                     (frm or "no record")[:7],
                     f"{len(r['replace'])}/{len(r['add'])}/{len(r['kept'])}/{len(r['unjudged'])}",
                     f"{r['agree']}/{r['shared']}{'' if r['credible'] else ' (not credible)'}"))
    if args.json:
        print(json.dumps({"template": head, "rows": [
            {"repo": a, "kind": b, "state": c, "record": d, "replace_add_kept_unjudged": e, "agree": f}
            for a, b, c, d, e, f in rows]}, indent=1))
    else:
        print(f"template {TEMPLATE}@{head[:7]}  manifest {len(manifest)} paths\n")
        print(f"{'repo':22s} {'kind':9s} {'state':8s} {'record':12s} {'repl/add/keep/unjudged':22s} agree")
        for a, b, c, d, e, f in rows:
            print(f"{a:22s} {b:9s} {c:8s} {d:12s} {e:22s} {f}")
    if behind:
        print(f"\n{len(behind)} of {len(rows)} not on template {head[:7]}: {', '.join(behind)}")
        return 1
    print(f"\nall {len(rows)} are on template {head[:7]}")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    for name, kind, what in REPOS:
        ms = [m for m in members(name) if m != ".gitkeep"]
        print(f"{kind:8s} {name:22s} {len(ms):2d} member(s)  {what}")
    return 0


def cmd_clean(args: argparse.Namespace) -> int:
    gone = held = refused = 0
    for name, kind, what in REPOS:
        if kind != "probe":
            continue
        record = has_a_record(name)
        if record and name in args.force:
            print(f"OVERRIDING  {name} — there is a record in it ({record}) and --force named it")
        elif record:
            print(f"REFUSED  {name} — there is a record in it: {record}")
            refused += 1
            continue
        if not args.yes:
            print(f"would delete  {name}  — {what}")
            gone += 1
            continue
        try:
            gh("api", "-X", "DELETE", f"repos/{ACCOUNT}/{name}")
            print(f"deleted  {name}")
            gone += 1
        except Exception as e:
            if "403" in str(e) or "admin rights" in str(e):
                print(f"NEEDS SCOPE  {name} — run: gh auth refresh -h github.com -s delete_repo")
                return 2
            print(f"FAILED  {name} — {e}")
            held += 1
    if not args.yes:
        print(f"\n{gone} would go, {refused} refused, {held} held. Nothing was deleted; pass --yes.")
    else:
        print(f"\n{gone} deleted, {refused} refused, {held} failed.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    m = sub.add_parser("machinery", help="which tribes are behind the template, and what an update would do")
    m.add_argument("--json", action="store_true", help="machine-readable, for a letter or a check")
    m.set_defaults(fn=cmd_machinery)
    c = sub.add_parser("clean")
    c.add_argument("--yes", action="store_true", help="actually delete; without it, only says what would go")
    c.add_argument("--force", action="append", default=[], metavar="REPO",
                   help="delete this probe even though there is a record in it — name it, so the override is visible")
    c.set_defaults(fn=cmd_clean)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
