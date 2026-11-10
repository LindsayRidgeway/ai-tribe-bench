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
    python3 lab/repos.py clean          say what would be deleted, and refuse where it should
    python3 lab/repos.py clean --yes    delete the probes

Deleting needs a token with `delete_repo`, which the default gh login does not have:

    gh auth refresh -h github.com -s delete_repo

That is the whole reason this is a script and not a habit: the habit ran out of scope mid-cleanup.
"""
from __future__ import annotations

import argparse
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
    c = sub.add_parser("clean")
    c.add_argument("--yes", action="store_true", help="actually delete; without it, only says what would go")
    c.add_argument("--force", action="append", default=[], metavar="REPO",
                   help="delete this probe even though there is a record in it — name it, so the override is visible")
    c.set_defaults(fn=cmd_clean)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
