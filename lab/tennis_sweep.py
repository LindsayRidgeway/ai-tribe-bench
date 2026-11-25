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
  the toe  the biggest one-frame rise of either toe, which is the standing-to-stride switch

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


def main(argv):
    path = argv[1] if len(argv) > 1 else "/tmp/log.txt"
    rows, segs, plan = read(path)
    names = [p[0] for p in plan] or ["A", "B"]
    idx = {n: i for i, n in enumerate(names)}
    traj = {k: [] for k in idx.values()}
    for r in rows:
        for k in idx.values():
            p = r[3 + k]
            if p and len(p) > 7 and p[7]:
                traj[k].append({"T": r[0], "x": p[7][0], "z": p[7][1], "yaw": p[2],
                                "rl": p[3], "rr": p[4], "tl": p[6][0], "tr": p[6][1]})
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


if __name__ == "__main__":
    main(sys.argv)
