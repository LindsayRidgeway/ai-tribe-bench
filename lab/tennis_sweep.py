"""Read a captured `?sweep` log and answer the movement items' questions with numbers.

The log is the stderr of a headless Chrome run of

    ".../Google Chrome" --headless=new --use-angle=metal --run-all-compositor-stages-before-draw \
      --hide-scrollbars --window-size=400,300 --user-data-dir=/tmp/cp-X --virtual-time-budget=60000 \
      --enable-logging=stderr --v=0 --screenshot=/tmp/x.png \
      "http://127.0.0.1:8778/games/tennis/replay3d.html?record=seasons/<S>/watch.json&debug&sweep=0:125:0.02"

and the `--screenshot=` is not decoration: without it the compositor may never run a frame, `window.__sweep`
never starts, and the run comes back empty (STILLS.md, trap 1).

What it prints, and why each number is here rather than in a chat:

  item 2b  the biggest one-frame move any body makes, and how many frames move a body over 25ft/s
  item 4   on every run of more than 3ft, which foot is on the side the body is going (the NEAR foot) and which
           one actually swings first. `near` is measured in the body's own frame: the travel direction is dotted
           with the lateral axis the sweep already reports, so a player running sideways while facing the net is
           read correctly and a player running straight ahead has no near side at all.
  item 5   the hitter's root speed at the contact frame
  item 12  whether the racquet head crosses the body's own centre line while the player runs, in crossings per
           stride pair — with the walk and the run split apart, because a walk already carried the frame and a
           population that mixes them reports the walk's crossings as the carry's (STILLS.md trap 10)
  the toe  the biggest one-frame rise of either toe, which is the standing-to-stride switch
  the toss a serve is drawn from its toss only if some frame during that toss is drawn as ITS OWN segment; the
           row's second field is the segment `shotAt` picked, so a previous point's break that swallowed the
           toss shows up here as a serve with no frame in its own window (STILLS.md, trap 8)

Usage:  python3 lab/tennis_sweep.py /tmp/log.txt [--segs]
"""
import json
import math
import sys

DEC = json.JSONDecoder()


def read(path):
    rows, segs, plan = [], None, None
    for line in open(path, encoding="utf-8", errors="ignore"):
        for tag, key in (("debug segs ", "segs"), ("debug plan ", "plan")):
            i = line.find(tag)
            if i >= 0:
                try:
                    v, _ = DEC.raw_decode(line[i + len(tag):].lstrip())
                except ValueError:
                    continue
                if key == "segs":
                    segs = v
                else:
                    plan = v
        i = line.find("debug sweep ")
        if i >= 0:
            try:
                v, _ = DEC.raw_decode(line[i + 12:].lstrip())
            except ValueError:
                continue
            rows.extend(v if (v and isinstance(v[0], list)) else [v])
    # Chrome echoes the first rows after the sweep ends; the log is otherwise in time order, so the first row
    # that does not advance is where the sweep stopped and the echo began.
    out = []
    for r in rows:
        if out and r[0] <= out[-1][0]:
            break
        out.append(r)
    return out, segs or [], plan or []


def heights(path):
    """Each player's figure height in feet, from the log's own `debug bones <name> ... height 5.44` line.

    The stride pair is `0.84 * height` in the page, so a crossings-per-stride-pair number needs the height, and a
    table of heights written into this file would be a second place for it to be wrong."""
    out = {}
    for line in open(path, encoding="utf-8", errors="ignore"):
        i = line.find("debug bones ")
        if i < 0:
            continue
        rest = line[i + 12:]
        name = rest.split(" ", 1)[0]
        j = rest.find("height ")
        if j >= 0:
            try:
                out[name] = float(rest[j + 7:].split(" ")[0])
            except ValueError:
                pass
    return out


def contacts_at_the_contact(path):
    """`debug contact` rows: one per shot, ticked at exactly the contact clock. The right way to read `rq`.

    Row: `[t, player, shot n, rally, rq, rootY, [rootX, rootZ], contactX, contactLateral, contactHeight, hand]`.

    This exists because every other contact number in this file came from a row on the sweep's own grid, and the
    record's ball trace is sampled every 0.02s: a row six thousandths of a second after a contact read the ball at
    the NEXT trace sample, which on a 113ft/s shot is 2.26ft further down the road. The defect was in the
    instrument, not the frame — measured 2026-11-27, shot 44 of `records/item31-after`: 2.58ft on the grid, 0.24ft
    at the contact. A grid row is not a strike and must not be averaged as one."""
    out = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        i = line.find("debug contact ")
        if i < 0:
            continue
        try:
            v, _ = DEC.raw_decode(line[i + len("debug contact "):].lstrip())
        except ValueError:
            continue
        if not isinstance(v, list) or len(v) < 7 or v[4] is None:
            continue
        out.append({"n": v[2], "rally": v[3], "who": v[1], "rq": v[4], "t": v[0], "rootY": v[5], "feet": v[6],
                    "contact": v[7:10] if len(v) >= 10 else None, "hand": v[10] if len(v) > 10 else None,
                    # the page's own account of whether the tick landed in the shot it is named for
                    "own": v[11] if len(v) > 11 else None})
    return out


def order(rows, segs, fallback):
    """Which column of a sweep row is which player — MEASURED from the log, not assumed from `debug plan`.

    The obvious mapping is `debug plan`'s key order, and it is WRONG: `PLAN` is filled as the settle moves are
    pushed, which is not the order of `D.players`, so on `seasons/2026-11-19` the plan is `[Colette, Gwen]` while
    the row's columns are `[Gwen, Colette]`. With exactly two players a swapped map still picks "the other one"
    correctly, so every number that reported the OTHER player survived it — and the two that reported the NAMED
    player did not. Measured 2026-11-26: item 5's "the striker's root speed at contact, median 0.50ft/s" was the
    RECEIVER's speed; the striker's own is 1.82ft/s. `isHitter` in the row is the log's own account of who is
    striking, so the mapping is read off that and checked: every shot must have exactly one column claiming it."""
    by_n = {s[0]: s for s in segs}
    votes = {}
    for r in rows:
        s = by_n.get(r[1])
        if not s:
            continue
        for i, p in enumerate(r[3:]):
            if p and p[1] == 1:
                votes.setdefault(i, set()).add(s[4])
    out = {}
    for i, who in votes.items():
        assert len(who) == 1, f"column {i} claims to be hitting for {sorted(who)}"
        out[next(iter(who))] = i
    if not out:
        out = {n: i for i, n in enumerate(fallback)}
    return out


def main(argv):
    path = argv[1] if len(argv) > 1 else "/tmp/log.txt"
    rows, segs, plan = read(path)
    if not rows:
        # A LOG WITH NO ROWS IS NOT A BROKEN INSTRUMENT, AND IT MUST NOT READ LIKE ONE. Two traps in STILLS.md say
        # the same thing from the other side: a page-side exception produces no `debug sweep` rows, and a headless
        # run without `--screenshot=` never starts the sweep at all — both look exactly like "the sweep did not run".
        # This used to fall through to `jumps[0]` and die with `IndexError: list index out of range`, which says
        # nothing about which of the three it was. Measured 2026-11-27: a `ReferenceError` in an edited page cost a
        # 15,001-row run and this traceback before the log was read by hand.
        print(f"  no `debug sweep` rows in {path}: {len(segs)} shot rows, so the page parsed the record and the film"
              f" was built, but no frame was sampled. Check, in this order: an `Uncaught` in the log (a page-side"
              f" exception reads exactly like a broken sweep), `--screenshot=` on the command line (without it the"
              f" compositor may never run a frame), and that `?sweep=t0:t1:dt` is inside the film's own clock.")
        return
    names = [p[0] for p in plan] or ["A", "B"]
    idx = order(rows, segs, names)
    names = [None] * len(idx)
    for n, i in idx.items():
        names[i] = n
    traj = {k: [] for k in idx.values()}
    for r in rows:
        for k in idx.values():
            p = r[3 + k]
            if p and len(p) > 7 and p[7]:
                traj[k].append({"T": r[0], "x": p[7][0], "z": p[7][1], "yaw": p[2],
                                "rl": p[3], "rr": p[4], "tl": p[6][0], "tr": p[6][1],
                                # the frame's lateral offset in the body's own frame (9th field, 2026-11-27)
                                "rh": (p[8][0] if len(p) > 8 and p[8] else None),
                                # which shot this row is in, and how far from its contact — the two numbers that
                                # say whether a running player is carrying the frame or winding up to strike
                                "n": r[1], "tlc": r[2]})
    print(f"{len(rows)} frames, {len(segs)} shots, players {', '.join(names)}")

    # ---- item 2b: a body placed rather than walked
    print("\n== item 2b — the biggest one-frame move, and how many frames are over 25ft/s ==")
    for n, k in idx.items():
        jumps = sorted(((math.hypot(b["x"] - a["x"], b["z"] - a["z"]), b["T"])
                        for a, b in zip(traj[k], traj[k][1:])), reverse=True)
        fast = [j for j in jumps if j[0] > 0.5]
        print(f"  {n:8s} {jumps[0][0]:6.2f}ft at T={jumps[0][1]:7.2f}   over 25ft/s: {len(fast)}"
              f"   next {[(round(d, 2), round(t, 2)) for d, t in jumps[1:4]]}")

    # ---- the toe: the standing-to-stride switch
    print("\n== the toe — biggest one-frame rise of either toe ==")
    for n, k in idx.items():
        rises = sorted(((abs(b[j] - a[j]), b["T"]) for a, b in zip(traj[k], traj[k][1:])
                        for j in ("tl", "tr") if a[j] is not None and b[j] is not None), reverse=True)
        over = sum(1 for d, _ in rises if d > 0.10)
        print(f"  {n:8s} {rises[0][0]:.3f}ft at T={rises[0][1]:7.2f}   over 0.10ft in a frame: {over}")

    # ---- item 12: does the frame come back across the body while the player runs?
    print("\n== item 12 — the frame's side of the body while moving ==")
    print("   the racquet head's lateral offset is the 9th field of each player entry (appended 2026-11-27), in the")
    print("   BODY's frame, so a sign change is the frame crossing the body's own centre line. A stride pair is")
    print("   `0.84 * height` ft, the page's own gait cycle, and the heights come out of the log's `debug bones` line")
    print("   rather than a table. The carry phase is the part of a move with no stroke in it: for the striker, more")
    print("   than 0.47s after contact (the finish is over); for anybody else, more than 0.55s before the take-back.")
    hts = heights(path)
    seg_by_n = {s[0]: s for s in segs}

    def speeds(t):
        out = []
        for a, b in zip(t, t[1:]):
            if a.get("rh") is None or "x" not in a:
                continue
            out.append(math.hypot(b["x"] - a["x"], b["z"] - a["z"]) / 0.02)
        return out

    # THE WALK/RUN LINE, MEASURED. The engine walks at 4.6ft/s and runs at 8ft/s and up, and a line picked by hand
    # would decide the answer, so it is read off this film's own histogram: the speed bin with the fewest frames
    # between 7 and 9ft/s is the gap the two populations are separated by.
    buckets = {}
    for k in idx.values():
        for v in speeds(traj[k]):
            if v >= 3.0:
                buckets[round(v)] = buckets.get(round(v), 0) + 1
    gap = min((b for b in buckets if 7 <= b <= 9), key=lambda b: buckets[b], default=8)
    print(f"   the walk/run line is {gap}ft/s, the emptiest bin between 7 and 9 in this film's speeds ("
          + ", ".join(f"{b}:{buckets[b]}" for b in sorted(buckets) if 5 <= b <= 11) + ")")

    def measure(t, name, carry_only):
        crossings, moved, last = 0, 0.0, None
        for a, b in zip(t, t[1:]):
            if a.get("rh") is None or "x" not in a:
                continue
            step = math.hypot(b["x"] - a["x"], b["z"] - a["z"])
            if step / 0.02 < gap:                   # a walk is not a run, and the walk already carried the frame
                continue
            if carry_only:
                sg = seg_by_n.get(a.get("n"))
                if sg and len(sg) > 4:
                    dur, toss, hitter = sg[2], sg[3] or 0.0, sg[4]
                    busy = a["tlc"] <= 0.47 if hitter == name else (a["tlc"] + toss) >= dur - 0.55
                    if busy:
                        continue
            moved += step
            sign = 1 if a["rh"] >= 0 else -1
            if last is not None and sign != last:
                crossings += 1
            last = sign
        return crossings, moved

    for n, k in idx.items():
        stride = 0.84 * hts.get(n, 5.5)
        cells = [(lab, measure(traj[k], n, carry)) for lab, carry in
                 (("run, carry", True), ("run, stroke", False))]
        cells = [(lab, c, ft) for lab, (c, ft) in cells]
        if not any(ft >= 1.0 for _, _, ft in cells):
            print(f"  {n:8s} no run in this log")
            continue
        for lab, c, ft in cells:
            if ft < 1.0:
                continue
            print(f"  {n:8s} stride pair {stride:4.2f}ft | {lab:11s} {c:3d} crossings in {ft:6.1f}ft"
                  f" = {c / ft * 10:4.2f} per 10ft = {c / (ft / stride):4.2f} per stride pair")

    # ---- item 16's remainder: is the frame on the ball at the contact?
    print("\n== the contact — how far the racquet head is from the ball when the ball is struck ==")
    exact = contacts_at_the_contact(path)
    if exact:
        print("   read from `debug contact`, which the page ticks at exactly `start + tossDur` — the contact by")
        print("   construction. A sweep row is on a 0.02s grid and the record's trace is 0.02s apart, so a row that")
        print("   lands a few thousandths after a contact reads half a trace hop: measured 2026-11-27, shot 44 read")
        print("   2.58ft on the grid and 0.24ft at the contact, at 113ft/s. The grid row is not a strike.")
    else:
        print("   read at the row nearest each contact (no `debug contact` lines in this log): a 0.02s grid against")
        print("   a 0.02s trace, so a fast shot's gap is overstated by up to half a hop.")
    if exact:
        off = [c for c in exact if c.get("own") == 0]
        print(f"   each row ticked its own segment: {len(exact) - len(off)} of {len(exact)}"
              + (f"  ({len(off)} did not — their numbers belong to the shot BEFORE them)" if off else ""))
    contacts = list(exact)
    for sg in ([] if exact else segs):
        n, hitter = sg[0], sg[4]
        k = idx.get(hitter)
        if k is None:
            continue
        # THE SHOT NUMBER IS NOT UNIQUE. A film of forty rallies restarts its shot numbers at 1 on every point, so
        # keying a contact on `n` silently mixed one rally's strike into another's: on `records/item31-after` it put
        # 116 "serves" through a film of 108 shots, and the rq it read was whichever rally's row sorted first. The
        # contact TIME is unique in a film, so a row belongs to a segment by its clock or not at all.
        when = sg[1] + (sg[3] or 0.0)
        best = None
        for r in rows:
            off = abs(r[0] - when)
            if off > 0.25:
                continue
            p = r[3 + k]
            if not p or len(p) < 9 or p[5] is None:
                continue
            if best is None or off < best[3]:
                best = (p[5], r[0], r[2], off, p[7], sg[7] if len(sg) > 7 else None)
        if best:
            contacts.append({"n": n, "who": hitter, "rq": best[0], "t": best[1], "tlc": best[2],
                             "feet": best[4], "contact": best[5]})
    # ...and the same contact against the FEET, from the record's own contact point (the eighth field of `debug
    # segs`, appended 2026-11-27) and the row's root position. This is the number the engine's reach decides.
    feet = []
    for c in contacts:
        if not c["contact"] or not c["feet"]:
            continue
        feet.append(math.hypot(c["feet"][0] - c["contact"][0], c["feet"][1] - c["contact"][1]))
    if contacts:
        d = sorted(c["rq"] for c in contacts)
        w = max(contacts, key=lambda c: c["rq"])
        print(f"  {len(d)} contacts this log reaches: head to ball median {d[len(d) // 2]:.2f}ft,"
              f" p90 {d[int(len(d) * 0.9)]:.2f}ft, worst {d[-1]:.2f}ft"
              f" (r{w.get('rally', '?')} shot {w['n']}, {w['who']}, T={w['t']})")
        print(f"  over 0.5ft: {sum(1 for x in d if x > 0.5)} of {len(d)}"
              f"   over 1ft: {sum(1 for x in d if x > 1.0)} of {len(d)}")
        # A SERVE AND A GROUNDSTROKE ARE TWO DIFFERENT QUESTIONS. A serve is struck 8.8ft up, and the stride cannot
        # reach that: `rise` in the page is capped at 0.95ft, so a serve's contact is short by the jump that is not
        # drawn (item 19). One median over both hides which of the two is still wrong, and they are 40% of this film.
        # THE HEIGHT IS THE THIRD FIELD, NOT THE SECOND. A record's contact is `[x, lateral, height]` — the page builds
        # its vector as `(contact[0], contact[2], contact[1])` — and the first version of this split read `contact[1]`,
        # i.e. the lateral coordinate, and called 98 of 108 contacts "serves struck 6ft up". A wrong index does not
        # fail: it produces a plausible population and a number that means nothing.
        tall = [c["rq"] for c in contacts if c["contact"] and c["contact"][2] > 6.0]
        flat = [c["rq"] for c in contacts if not (c["contact"] and c["contact"][2] > 6.0)]
        for label, v in (("serves, struck 6ft up or more", tall), ("groundstrokes", flat)):
            if not v:
                continue
            v = sorted(v)
            print(f"  {label}: n={len(v)} median {v[len(v) // 2]:.2f}ft, p90 {v[int(len(v) * 0.9)]:.2f}ft,"
                  f" worst {v[-1]:.2f}ft, over 1ft {sum(1 for x in v if x > 1.0)}")
        if feet:
            f = sorted(feet)
            print(f"  feet to contact, same {len(f)} contacts: median {f[len(f) // 2]:.2f}ft, p90"
                  f" {f[int(len(f) * 0.9)]:.2f}ft, worst {f[-1]:.2f}ft")
        print("  the page's own line for a contact no arm can make is `shoulder-B more than 3.9ft` (?debug's `debug")
        print("  geo`), and the record only promises the contact is inside RACQUET_REACH = 7.0ft of the feet — so a")
        print("  film can satisfy its own done-test and still be a contact the picture cannot draw.")

    # ---- the toss: does a serve's own segment own any frame during its own toss?
    print("\n== the toss — a serve is drawn from its toss only if a frame during that toss is drawn as its segment ==")
    serves = [s for s in segs if len(s) > 3 and (s[3] or 0) > 0.10]
    # A serve whose window the log does not REACH has not been measured, and counting it as a miss is how one
    # wrong number gets quoted twice: a 108-shot film swept 0:300 reported "27 of 65 never drawn" because its
    # last serves are past the end of the sweep. Only a window with both ends inside the logged range can be
    # called drawn or not drawn.
    tmin, tmax = rows[0][0], rows[-1][0]
    covered = [s for s in serves if s[1] >= tmin and s[1] + s[3] <= tmax]
    never = []
    for s in covered:
        n, start, toss = s[0], s[1], s[3]
        if not any(r[1] == n and start <= r[0] < start + toss for r in rows):
            never.append(n)
    print(f"  serves whose toss is never drawn: {len(never)} of {len(covered)}"
          + (f" ({len(serves) - len(covered)} of {len(serves)} serves are past the end of the log, unmeasured)"
             if len(covered) < len(serves) else "")
          + (f": {never}" if never else ""))
    cover = []
    for s in covered:
        n, start, toss = s[0], s[1], s[3]
        got = [r[0] for r in rows if r[1] == n and start <= r[0] < start + toss]
        if got:
            cover.append(((got[-1] - got[0]), toss, n))
    if cover:
        shortest = min(cover)
        print(f"  the shortest toss drawn covers {shortest[0]:.2f}s of its {shortest[1]:.2f}s (shot {shortest[2]})")

    # ---- item 4 + 5, shot by shot
    def near(k, t):
        return min(range(len(traj[k])), key=lambda i: abs(traj[k][i]["T"] - t))

    print("\n== item 4 — on a run of more than 3ft, which foot swings first ==")
    print("   the run is the RECEIVER's: `run` in the record belongs to the player the ball is going to, not the one")
    print("   who hit it. The swing foot is read from the toes 0.25-0.75s after the run begins: the clamp keeps the")
    print("   lower toe on the ground, so the toe that is off it is the one the gait is swinging.")
    led = tot = 0
    for s in segs:
        n, start, dur, toss, hitter, run = s[0], s[1], s[2], s[3], s[4], s[5] if len(s) > 5 else None
        if not run or run[0] < 3.0:
            continue
        dist, fx, fz, tx, tz = run
        k = 1 - idx[hitter]
        a = near(k, start + toss)
        row = traj[k][a]
        cy, sy = math.cos(row["yaw"]), math.sin(row["yaw"])
        dx, dz = tx - fx, tz - fz
        dd = math.hypot(dx, dz) or 1
        dx, dz = dx / dd, dz / dd
        # the body's own lateral axis, the same convention the sweep's rel[] uses: l = dx*cos(yaw) - dz*sin(yaw)
        side = dx * cy - dz * sy
        nearfoot = "L" if side > 0 else "R"
        # WHICH FOOT SWINGS FIRST IS READ FROM WHERE THE TOES ARE, NOT HOW HIGH THEY ARE. Toe height after the
        # grounding clamp is a poor probe — the clamp keeps the lower toe on the floor, so both heights sit within
        # 0.03ft of each other and the sign is noise (measured 2026-11-25: +/-0.003 to 0.05ft). The toe's FORWARD
        # offset is a stride's actual product and separates the two feet by 0.1 to 2.6ft over the same window.
        # TWO QUESTIONS, TWO METRICS, AND THEY ARE NOT THE SAME ONE. "Which foot leaves the ground first" is a
        # question about the START of the run; "which foot ends up in front" is a question about the step, and a
        # cross-over deliberately puts the FAR foot in front (the far leg swings across the body, which is what
        # crossing is). A metric that reads only the forward offsets therefore answers the second question and is
        # then scored against the first — which is what an earlier version of this script did.
        lift = {}
        for sd, key in (("L", "tl"), ("R", "tr")):
            base = sum(traj[k][i][key] for i in range(max(0, a - 5), a + 1)) / min(6, a + 1)
            lift[sd] = next((round(r["T"] - row["T"], 2) for r in traj[k][a:]
                               if r[key] is not None and r[key] > base + 0.06), None)
        window = [r for r in traj[k][a:] if 0.05 <= r["T"] - row["T"] <= 0.45]
        if not window or any(r["rl"] is None or r["rr"] is None for r in window):
            continue
        diff = sum(r["rl"][2] - r["rr"][2] for r in window) / len(window)
        across = "L" if diff > 0 else "R"
        first = "-"
        if lift["L"] is not None and (lift["R"] is None or lift["L"] < lift["R"]):
            first = "L"
        elif lift["R"] is not None:
            first = "R"
        # a tie to the frame is not a lead: both feet leave the ground in a split step, and the honest answer then
        # is "the same frame", counted as neither
        tie = lift["L"] is not None and lift["R"] is not None and abs(lift["L"] - lift["R"]) < 0.03
        tot += 1
        led += (first == nearfoot and not tie)
        print(f"  shot {n:2d} {names[k]:8s} travel {dist:5.1f}ft lateral {side:+.2f} near={nearfoot}"
              f" | off first: L+{lift['L']} R+{lift['R']} -> {first}{' (tie)' if tie else ''}"
              f" | across: {across} (L-R {diff:+.2f}ft)")
    print(f"  the near foot left the ground first on {led} of {tot}")

    print("\n== item 5 — the hitter's root speed at the contact frame ==")
    vals = []
    for s in segs:
        n, start, toss, hitter = s[0], s[1], s[3], s[4]
        k = idx[hitter]
        i = near(k, start + toss)
        if i < 1 or i + 1 >= len(traj[k]):
            continue
        a, b = traj[k][i - 1], traj[k][i + 1]
        vals.append((math.hypot(b["x"] - a["x"], b["z"] - a["z"]) / max(1e-6, b["T"] - a["T"]), n))
    vals.sort(reverse=True)
    mid = sorted(v for v, _ in vals)[len(vals) // 2]
    print(f"  median {mid:.2f}ft/s  max {vals[0][0]:.2f}ft/s (shot {vals[0][1]})"
          f"  over 30ft/s: {sum(1 for v, _ in vals if v > 30)} of {len(vals)}")

    # ---- item 6: the turn-back
    print("\n== item 6, the turn-back — how long until the striker is facing the middle of the court,")
    print("   and where the recovery run goes ==")
    print("   The facing is read against the line from the body to the CENTRE of the court (39, 13.5), which is what")
    print("   'back towards the centre' means when the body is standing anywhere but the middle of the baseline.")
    print("   `err@c` is the error ON the contact frame — it is the chase's facing, and the body has to turn from it")
    print("   to the net, so a large number here is the size of the snap the eye sees at the strike.")
    CEN = (39.0, 13.5)
    NET = 39.0

    def to_centre(p):
        return math.atan2(CEN[0] - p["x"], CEN[1] - p["z"])

    def err(p):
        return math.degrees((p["yaw"] - to_centre(p) + math.pi * 3) % (math.pi * 2) - math.pi)

    def err_net(p):
        # Square to the net is what the restated done-test asks, and it is the measure that does not move when a
        # player meets the ball four feet past the net: from there "the middle of the court" is behind her.
        net = math.pi / 2 if p["x"] < NET else -math.pi / 2
        return math.degrees((p["yaw"] - net + math.pi * 3) % (math.pi * 2) - math.pi)

    rows6 = []
    for s in segs:
        n, start, toss, hitter = s[0], s[1], s[3], s[4]
        k = idx[hitter]
        t = traj[k]
        i = near(k, start + toss)
        p = t[i]
        j = near(k, start + toss - 1.2)
        ax, az = p["x"] - t[j]["x"], p["z"] - t[j]["z"]
        app = math.hypot(ax, az)
        hit = next((q["T"] - (start + toss) for q in t[i:] if abs(err(q)) <= 20), None)
        r = near(k, start + toss + 1.2)
        rx, rz = t[r]["x"] - p["x"], t[r]["z"] - p["z"]
        rec = math.hypot(rx, rz)
        ang = None
        if app > 0.5 and rec > 0.5:
            ang = math.degrees(math.acos(max(-1.0, min(1.0, (ax * rx + az * rz) / (app * rec)))))
        rows6.append({"n": n, "who": hitter, "err0": err(p), "hit": hit, "err12": err(t[r]),
                      "errn0": err_net(p), "errn12": err_net(t[r]),
                      "rec": rec, "ang": ang, "x": p["x"], "z": p["z"]})
        print(f"  shot {n:2d} {hitter:8s} at {p['x']:6.1f},{p['z']:5.1f} err@contact {err(p):+6.0f}deg"
              f" ({err_net(p):+4.0f} to the net)"
              f" | within 20deg after {('%5.2fs' % hit) if hit is not None else '  never'}"
              f" | err at +1.2s {err(t[r]):+6.0f}deg | recovery {rec:5.2f}ft"
              f" {('at %3.0fdeg to the way in' % ang) if ang is not None else ''}")
    if not rows6:
        return
    worst = max(rows6, key=lambda w: abs(w["err0"]))
    late = max((w["hit"] for w in rows6 if w["hit"] is not None), default=0.0)
    moved = [w for w in rows6 if w["rec"] > 1.0]
    print(f"\n  the facing at contact is off the middle by {worst['err0']:+.0f}deg at worst (shot {worst['n']}),"
          f" and within 20deg {late:.2f}s after it at worst")
    wn = max(rows6, key=lambda w: abs(w["errn0"]))
    print(f"  SQUARE TO THE NET, which is the restated done-test: {wn['errn0']:+.0f}deg at worst (shot {wn['n']}),"
          f" median {sorted(abs(w['errn0']) for w in rows6)[len(rows6) // 2]:.1f}deg,"
          f" over 5deg on {sum(1 for w in rows6 if abs(w['errn0']) > 5)} of {len(rows6)},"
          f" over 20deg on {sum(1 for w in rows6 if abs(w['errn0']) > 20)}")
    print(f"  on the {len(moved)} shots that end in a recovery of more than 1ft: over 20deg off the middle 1.2s later"
          f" on {sum(1 for w in moved if abs(w['err12']) > 20)} of them,"
          f" worst {max(abs(w['err12']) for w in moved):.0f}deg"
          f" — those are the ones whose body is still facing the way it is running")
    retrace = [w for w in moved if w["ang"] is not None and w["ang"] < 30]
    print(f"  and the recovery retraces the way in (under 30deg between the two) on {len(retrace)} of them:"
          f" {[w['n'] for w in retrace]}")
    app_wide = [w for w in rows6 if abs(w["z"] - CEN[1]) >= 3.0]
    print(f"  of the {len(app_wide)} shots struck from more than 3ft off the centre line, the facing at contact is"
          f" off the middle by a median of"
          f" {sorted(abs(w['err0']) for w in app_wide)[len(app_wide) // 2]:.0f}deg")


if __name__ == "__main__":
    main(sys.argv)
