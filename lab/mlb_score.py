#!/usr/bin/env python3
"""Score three beings' World Series picks against what actually happened.

Why this file exists. The Dow experiment asked three beings to predict a number and made everyone wait a
day to find out. The founder's objection on 2026-11-03 was exact: *"the fact that we can't check the
prediction accuracy for 24 hours is a disadvantage."* The 2026 baseball season is over. A regular-season
box score is a permanent fact, and the postseason result is a URL away, so a prediction about it can be
scored in the time it takes to read the file.

What is scored, and what is refused.
  - The champion in the top three, and at what rank. That is the headline, and on this season it separates
    nobody: the Brewers had the best record and the best run differential and they won.
  - Depth: how far the three picks actually went (champion 5, pennant 4, LCS 3, DS 2, wild card 1, October
    off 0) — a scale where reaching the Series counts for both clubs and winning it counts for one more.
    This is the number that separates methods, because it pays a second and third pick that were right
    for the right reason.
  - Recall, not method. The 2026 postseason may be in a model's weights. Every being is asked to file a
    `KNEW:` line and a `GUESS BEFORE SEARCH:` line *before* it searches. A being that names the champion
    from memory and then picks it is flagged, and its pick is not counted as a test of its method.
  - A verdict. There is none. One postseason is one sample, and the favourite won it; a tool that crowned
    a winner from this would be selling exactly what `lab/compare.py` refuses to sell.

Usage:
    python3 lab/mlb_score.py                       # reads experiment/mlb/*-1.md
    python3 lab/mlb_score.py --also experiment     # plus any -1.md elsewhere
    python3 lab/mlb_score.py --offline-file facts/postseason-2026.json   # no network
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOB_DIR = ROOT / "experiment" / "mlb"

API = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&season={season}&gameType={kind}"

# The four rounds, shallowest first. A team's depth is the deepest round it appears in, and the champion
# is whoever won the last game of the deepest one.
ROUNDS = [("F", 1, "wild card"), ("D", 2, "division series"), ("L", 3, "championship series"),
          ("W", 4, "World Series")]
CHAMPION = 5          # reaching the Series is 4 for both clubs; winning it is one more

PICK = re.compile(r"^\s*(?:\*\*)?PICK\s*([123])\s*(?:\*\*)?\s*[:.\-–—]\s*(.+)$", re.M | re.I)
KNEW = re.compile(r"^\s*(?:\*\*)?KNEW(?:\*\*)?\s*[:.\-–—]\s*(.+)$", re.M | re.I)
GUESS = re.compile(r"^\s*(?:\*\*)?GUESS BEFORE SEARCH(?:\*\*)?\s*[:.\-–—]\s*(.+)$", re.M | re.I)
METHOD = re.compile(r"^\s*(?:\*\*)?METHOD(?:\*\*)?\s*[:.\-–—]\s*(.+)$", re.M | re.I)

# Nickname and location both name a club, and a scorer that misses "Brewers" because it wanted "Milwaukee
# Brewers" is the same defect as a key with two names. Short forms are the ones a person actually writes.
ALIASES = {
    "brewers": "Brewers", "milwaukee": "Brewers", "milwaukee brewers": "Brewers",
    "rays": "Rays", "tampa bay": "Rays", "tampa bay rays": "Rays", "tampa": "Rays",
    "dodgers": "Dodgers", "los angeles dodgers": "Dodgers", "la dodgers": "Dodgers",
    "guardians": "Guardians", "cleveland": "Guardians", "cleveland guardians": "Guardians",
    "braves": "Braves", "atlanta": "Braves", "atlanta braves": "Braves",
    "yankees": "Yankees", "new york yankees": "Yankees", "ny yankees": "Yankees",
    "padres": "Padres", "san diego": "Padres", "san diego padres": "Padres",
    "cubs": "Cubs", "chicago cubs": "Cubs",
    "white sox": "White Sox", "chicago white sox": "White Sox",
    "red sox": "Red Sox", "boston": "Red Sox", "boston red sox": "Red Sox",
    "phillies": "Phillies", "philadelphia": "Phillies", "philadelphia phillies": "Phillies",
    "astros": "Astros", "houston": "Astros", "houston astros": "Astros",
    "d-backs": "D-backs", "diamondbacks": "D-backs", "arizona": "D-backs",
    "arizona diamondbacks": "D-backs",
    "orioles": "Orioles", "baltimore": "Orioles", "blue jays": "Blue Jays", "toronto": "Blue Jays",
    "twins": "Twins", "minnesota": "Twins", "nationals": "Nationals", "washington": "Nationals",
    "cardinals": "Cardinals", "st. louis": "Cardinals", "st louis": "Cardinals",
    "tigers": "Tigers", "detroit": "Tigers", "mariners": "Mariners", "seattle": "Mariners",
    "reds": "Reds", "cincinnati": "Reds", "mets": "Mets", "new york mets": "Mets",
    "royals": "Royals", "kansas city": "Royals", "giants": "Giants", "san francisco": "Giants",
    "athletics": "Athletics", "a's": "Athletics", "angels": "Angels", "los angeles angels": "Angels",
    "rockies": "Rockies", "colorado": "Rockies", "pirates": "Pirates", "pittsburgh": "Pirates",
}


def canon(name: str) -> str | None:
    """A club name a person wrote, as the scorer spells it — or None if it is not a club."""
    s = re.sub(r"\(.*?\)", " ", name)
    s = s.split("—")[0].split("–")[0].split(" - ")[0]
    s = re.sub(r"[^a-z0-9' ]", " ", s.lower())
    s = re.sub(r"\s+", " ", s).strip()
    if s in ALIASES:
        return ALIASES[s]
    for alias, club in sorted(ALIASES.items(), key=lambda kv: -len(kv[0])):
        if alias in s:
            return club
    return None


def default_fetch(url: str, tries: int = 3) -> str:
    """One TLS handshake timeout should not cost the whole score — the first run of this tool lost one."""
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ai-tribe-bench/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode()
        except Exception as e:      # noqa: BLE001 — a retry is the whole point
            last = e
    raise last


def outcome(fetch=None, season: int = 2026) -> tuple[dict[str, int], str | None]:
    """How far each club went, from the league's own schedule: 5 champion, 4 pennant, 3 LCS, 2 DS, 1 WC."""
    fetch = fetch or default_fetch
    depth: dict[str, int] = {}
    champion = None
    for kind, points, _label in ROUNDS:
        data = json.loads(fetch(API.format(season=season, kind=kind)))
        for day in data.get("dates", []):
            for game in day.get("games", []):
                sides = game.get("teams", {})
                names = [sides.get("away", {}).get("team", {}).get("name"),
                         sides.get("home", {}).get("team", {}).get("name")]
                for n in names:
                    if not n:
                        continue
                    club = canon(n) or n
                    depth[club] = max(depth.get(club, 0), points)
                for side in ("away", "home"):
                    if sides.get(side, {}).get("isWinner"):
                        n = sides[side].get("team", {}).get("name")
                        if n and points == 4:
                            champion = canon(n) or n
    if champion:
        depth[champion] = max(depth.get(champion, 4), CHAMPION)
    return depth, champion


def picks(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    out = {"file": path, "member": path.stem.replace("-1", "").strip("-"),
           "picks": {}, "knew": "", "guess": "", "method": ""}
    for m in PICK.finditer(text):
        rank = int(m.group(1))
        tail = m.group(2)
        # The club is the first clause, not the sentence: "E — 30% — best record" names E, and a scorer that
        # swallowed the reason would file a club called "E — 30% — best record" and score it as an unknown.
        head = re.split(r"\s+[—–-]\s+|\s*[|]\s*|\s\(\s*", tail)[0]
        head = head.replace("*", "").strip()
        club = canon(head) or head[:20]
        conf = re.search(r"(\d{1,3})\s*%", tail)
        out["picks"].setdefault(rank, {"club": club, "raw": tail.strip()[:90],
                                       "conf": int(conf.group(1)) if conf else None})
    for key, rx in (("knew", KNEW), ("guess", GUESS), ("method", METHOD)):
        m = rx.search(text)
        if m:
            out[key] = m.group(1).strip()[:200]
    return out


def recall_risk(row: dict, champion: str) -> str:
    """Did this being know, before searching, the thing it then picked? That is not a test of method."""
    picked = {p["club"] for p in row["picks"].values()}
    if champion not in picked:
        return ""
    said = f"{row['knew']} {row['guess']}".lower()
    if champion.lower() in said or ("brewers" in said and champion == "Brewers"):
        return "flagged: named the champion before searching"
    if re.search(r"\bi (do not|don't) know\b|\bno\b", row["knew"].lower()) and row["guess"]:
        return "clean: said it did not know, then picked"
    if not row["knew"]:
        return "no KNEW line filed"
    return ""


def rows(root: Path | None = None, also: list[str] | None = None, fetch=None,
         letters: dict[str, str] | None = None):
    root = root or ROOT
    # Two experiments live side by side: the 2026 season under real names, and a season with the names taken
    # out. A scorer that mixed them would score letter-votes against clubs, so the two sets are kept apart by
    # the only thing that distinguishes them — whether the file is an anonymous run.
    pattern = "*-anon-1.md" if letters else "*-1.md"
    files = sorted((root / "experiment" / "mlb").glob(pattern))
    for extra in (also or []):
        files += sorted((root / extra).glob(pattern))
    if not letters:
        files = [f for f in files if not f.name.endswith("-anon-1.md")]
    seen, out = set(), []
    for f in files:
        r = picks(f)
        # A season with the names taken out: a member picks letters, and the letters become clubs here and
        # nowhere earlier, so nothing a member read could contain the answer.
        if letters:
            for slot in r["picks"].values():
                if slot["club"] in letters:
                    slot["club"] = canon(letters[slot["club"]]) or letters[slot["club"]]
        key = r["member"].casefold()
        if key in seen or not r["picks"]:
            continue
        seen.add(key)
        out.append(r)
    return out


def main(argv=None, fetch=None, now=None) -> int:
    ap = argparse.ArgumentParser(description="score World Series picks against the postseason")
    ap.add_argument("--also", action="append", default=[], help="extra directory to look in for *-1.md")
    ap.add_argument("--offline-file", default=None,
                    help="a saved response per round (JSON list of four), so the score is reproducible")
    ap.add_argument("--season", type=int, default=2026, help="which season's postseason to score against")
    ap.add_argument("--key", default=None,
                    help="the letter->club mapping for a season with the names taken out; the mapping is "
                         "printed at the end, because the reveal is the point")
    ap.add_argument("--write", action="store_true", help="also write facts/mlb-comparison.md")
    args = ap.parse_args(argv)
    now = now or datetime.now(timezone.utc)

    if args.offline_file:
        saved = json.loads(Path(args.offline_file).read_text(encoding="utf-8"))
        fetch = lambda url: saved[url]  # noqa: E731
    letters = None
    if args.key:
        letters = json.loads(Path(args.key).read_text(encoding="utf-8"))["letters"]
    try:
        depth, champion = outcome(fetch, args.season)
    except Exception as e:
        print(f"   could not read the postseason schedule: {e}", file=sys.stderr)
        print("   nothing was scored. A score invented from memory is worse than no score, because a "
              "reader cannot tell the difference once it is on disk.", file=sys.stderr)
        return 2
    if not depth or not champion:
        print("   the schedule came back empty, or it has no World Series winner in it. Nothing to score "
              "against.", file=sys.stderr)
        return 2
    rows_ = rows(also=args.also, fetch=fetch, letters=letters)
    if not rows_:
        print("No *-1.md prediction files found under experiment/mlb/. A scoreboard needs at least one.")
        return 1

    print(f"Scored against the {args.season} postseason: {champion} won it. "
          f"(read from statsapi.mlb.com at {now:%Y-%m-%d %H:%M} UTC)\n")
    print(f"{'being':10s} {'#1':14s} {'#2':14s} {'#3':14s} {'champ':7s} {'depth':6s} recall")
    print(f"{'-'*10} {'-'*14} {'-'*14} {'-'*14} {'-'*7} {'-'*6} {'-'*30}")
    table = []
    for r in rows_:
        p = [r["picks"].get(i, {}).get("club", "—") for i in (1, 2, 3)]
        rank = next((i for i in (1, 2, 3) if r["picks"].get(i, {}).get("club") == champion), None)
        points = sum(depth.get(c, 0) for c in p if c != "—")
        flag = recall_risk(r, champion)
        table.append({"member": r["member"], "picks": p, "rank": rank, "depth": points, "flag": flag,
                      "method": r["method"]})
        print(f"{r['member'][:10]:10s} {p[0][:14]:14s} {p[1][:14]:14s} {p[2][:14]:14s} "
              f"{(('#' + str(rank)) if rank else '—'):7s} {points:<6d} {flag}")

    print()
    if len(table) == 1:
        print(f"Only one being filed picks, so there is no method to compare: **{table[0]['member']}** "
              f"scored {table[0]['depth']} depth points. A comparison needs at least two.")
    else:
        top = max(t['depth'] for t in table)
        best = [t["member"] for t in table if t["depth"] == top]
        if len(best) == len(table):
            print(f"Every being scored {top} depth points. Nothing in this table separates their methods — "
                  f"which is a result about the season, not about them: the club with the best record and "
                  f"the best run differential won it.")
        else:
            print(f"Deepest three picks: {', '.join(best)} at {top} depth points. That is not yet a better "
                  f"method — one postseason is one sample, and the club with the best record won it. Read the "
                  f"METHOD blocks in the files before believing a ranking; the interesting difference is "
                  f"usually in the pick nobody made.")
        hits = [t["member"] for t in table if t["rank"]]
        if len(hits) == len(table):
            print(f"All of them put the champion in their top three, so 'accuracy' discriminates nothing "
                  f"here. What differs is rank and confidence, and whether the reason was the right one.")
    flagged = [t["member"] for t in table if t["flag"].startswith("flagged")]
    if flagged:
        print(f"\n{', '.join(flagged)} named the champion *before* searching. A pick that matches a memory "
              f"is not evidence of a method that works. Their rows stay, and their scores do not count as a "
              f"test of how they weigh a season.")
    print("\nWhat one postseason can decide: whether a being's stated method is coherent enough to be checked, "
          "and whether it survives being shown the answer. What it cannot decide: whose method is better. "
          "The champion wins about one time in five, which is why exchange 3 asks them to argue about it "
          "rather than asking this tool to.")

    if letters:
        print("\nThe letters, which no being could see while it was deciding:")
        inv = {v: k for k, v in letters.items()}
        for club in sorted(depth, key=lambda c: -depth[c]):
            if club in inv:
                print(f"   {inv[club]:3s} {club:22s} went {depth[club]} "
                      f"({'champion' if depth[club] == 5 else 'pennant' if depth[club] == 4 else 'LCS' if depth[club] == 3 else 'earlier'})")

    if args.write:
        out = ROOT / "facts" / "mlb-comparison.md"
        lines = [f"# World Series picks against the 2026 postseason", "",
                 f"Scored {now:%Y-%m-%d %H:%M} UTC from statsapi.mlb.com. Champion: **{champion}**.", "",
                 "| being | #1 | #2 | #3 | champion rank | depth | recall |", "|---|---|---|---|---|---|---|"]
        for t in table:
            lines.append(f"| {t['member']} | {t['picks'][0]} | {t['picks'][1]} | {t['picks'][2]} | "
                         f"{(('#' + str(t['rank'])) if t['rank'] else '—')} | {t['depth']} | "
                         f"{t['flag'] or '—'} |")
        lines += ["", "Depth: champion 5, pennant 4, championship series 3, division series 2, wild card 1, "
                  "October off 0. "
                  "Read the METHOD blocks before ranking anybody: one postseason is one sample."]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n   wrote {out.relative_to(ROOT) if str(out).startswith(str(ROOT)) else out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
