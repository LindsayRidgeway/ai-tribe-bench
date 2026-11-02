#!/usr/bin/env python3
"""Who has taken a copy — the part of the traction question that the beacon cannot answer.

The beacon counts trials: it fires when a repository actually wakes somebody, and it carries the repo's
name. It cannot fire for a repository that was cloned and never run, and it says nothing about the person
behind the name. That second gap is what this closes, with public data only.

Two things are public and durable, and neither needs anybody's email address:

  forks    every copy GitHub has recorded, with the owner's login and when they took it;
  clones   the upstream repository's own clone count, last 14 days, which needs push access and is
           therefore only available to the owner.

A GitHub login is a public identity. An email address is not public — the API returns one only if the
person chose to publish it — and a beacon that collected addresses would be surveilling private
individuals to measure a strawman. So: logins, dates, and whether the copy has been touched since.

    python3 lab/traction.py            # writes lab/traction.md

The token comes from GITHUB_TOKEN in Actions, or GH_TOKEN / --token locally. Without one it still lists
what an anonymous request can see, and says which numbers are missing rather than printing zero.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Which repository this is about. In a fork this must be the fork, not the upstream it came from — the
# whole point is to see whether anybody took a copy, and a file that reports the origin's numbers from
# inside somebody else's copy reports the wrong thing.
REPO = (os.environ.get("TRACTION_REPO")
        or os.environ.get("GITHUB_REPOSITORY")
        or "LindsayRidgeway/ai-tribe-bench")


def get(path: str, token: str = "") -> tuple[object, str]:
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "ai-tribe-bench-traction")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r), ""
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return None, type(e).__name__


def build(repo: str = REPO, token: str = "") -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    forks, ferr = get(f"/repos/{repo}/forks?per_page=100&sort=newest", token)
    clones, cerr = get(f"/repos/{repo}/traffic/clones", token)
    stars = get(f"/repos/{repo}", token)[0]

    out = [f"# Traction — {repo}", "",
           f"*Rebuilt {now} by `lab/traction.py`. Public data only: logins and dates, never addresses.*", ""]

    if isinstance(stars, dict):
        out += [f"**Stars** {stars.get('stargazers_count', '?')} · **Forks** {stars.get('forks_count', '?')} · "
                f"**Watchers** {stars.get('subscribers_count', '?')}", ""]

    out += ["## Copies taken", ""]
    if isinstance(forks, list) and forks:
        out += ["| who | took a copy | last touched it |", "|---|---|---|"]
        for f in forks:
            out.append(f"| [{f['owner']['login']}]({f['html_url']}) | {str(f.get('created_at',''))[:10]} | "
                       f"{str(f.get('pushed_at',''))[:10]} |")
        out += ["", f"*{len(forks)} fork(s). A fork that has never been pushed to took a copy and did nothing "
                    "with it — which is the abandonment this cannot measure and will not pretend to.*"]
    elif ferr:
        out.append(f"(forks could not be read: {ferr})")
    else:
        out.append("No forks. Nobody has taken a copy through GitHub.")

    out += ["", "## Clones of this repository (last 14 days, owner only)", ""]
    if isinstance(clones, dict):
        out += [f"{clones.get('count', '?')} clones from {clones.get('uniques', '?')} distinct sources.", "",
                "*This number is not a count of people.* Every wake and every clock turn clones this "
                "repository on a runner, and those clones are in here. On 2026-11-02 the total was 356 "
                "while the star and fork counts were 0 — which is what a machine reading its own work looks "
                "like. Read the daily rows for a shape, not the total for a number.", ""]
        for day in (clones.get("clones") or [])[-14:]:
            out.append(f"- {day['timestamp'][:10]}: {day['count']} ({day['uniques']} unique)")
    else:
        out += [f"Not available ({cerr or 'no answer'}). This needs push access to the repository; the "
                "Actions token has it, an anonymous request does not. **This is not zero** — it is unread."]

    out += ["", "## What the beacon adds", "",
            "The beacon reports the moment a repository **runs** the tribe for the first time, and names it. "
            "That is the only signal for a copy made without forking — a download, a template, a zip — because "
            "those leave no trace here. Trials, not intentions; and the two lists answer different questions, "
            "so neither is a substitute for the other.", ""]
    return "\n".join(out)


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if "--token" in sys.argv:
        token = sys.argv[sys.argv.index("--token") + 1]
    text = build(token=token)
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lab", "traction.md")
    with open(os.path.normpath(here), "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
