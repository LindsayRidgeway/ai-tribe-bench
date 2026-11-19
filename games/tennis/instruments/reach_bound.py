"""The run-off: does PLAY_AREA change how many balls a player reaches? Item 17, 2026-11-19.

    python3 games/tennis/instruments/reach_bound.py 300

Promoted out of /tmp when the item was written, because the numbers in BACKLOG.md Item 17 are the whole
argument for the bound and a reference to a file that no longer exists is not evidence. It captures a
population of real interceptions (every ball `play_point` asks about), then re-asks each one with the
module-global PLAY_AREA set to each candidate, so every candidate sees the same balls. That is the point:
a film-level count cannot answer this question — any change reshuffles the rng stream, and 6/8/10/12/16ft
gave 225/225/176/110/139 shots on the film, five different samples rather than five run-offs.

The columns are `reached` and the share of meetings that happen more than 6ft and 10ft outside the court.
Two findings, and the second is the one that matters:

  * `reached` does not move — 98% at every bound, including none at all. The bound is therefore NOT a
    filter that takes balls away from players. Every ball it clips was already reachable at an earlier
    slice, inside the ground; the old code simply preferred a later slice nearer the waist and put the
    contact thirty feet out. So the run-off is a correction to WHICH moment is chosen.
  * `worst meet` equals the bound exactly at 6/8/10/12/16/22ft. The waist preference is still pushing
    contact to the edge of whatever ground is allowed, which is why the number is not trusted to choose
    itself and why Item 18 rewrites the preference as a band.
"""
import sys
import collections

sys.path.insert(0, "/Users/lindsayridgeway/ai_tribe/lab")
import tennis as T

CALLS = []
_orig = T.interception


def recording(p, land, flight_time, bounce, surface, *a, **kw):
    out = _orig(p, land, flight_time, bounce, surface, *a, **kw)
    CALLS.append((p, land, flight_time, dict(bounce), surface, a, dict(kw)))
    return out


T.interception = recording
want = int(sys.argv[1]) if len(sys.argv) > 1 else 300
pts = 0
seed = 0
while len(CALLS) < want:
    seed += 1
    import random
    rng = random.Random(seed)
    a = T.Player("Dmitri", True, 300)
    b = T.Player("Gwen", False, 600)
    T.play_point(a, b, "clay", (-6.22, -6.22), 6.0, rng)
    pts += 1
T.interception = _orig

print(f"{len(CALLS)} balls asked of interception over {pts} points\n")
def outside(x, y):
    return max(-x, x - T.LENGTH, -y, y - T.WIDTH, 0.0)


print(f"{'run-off':>8} {'reached':>9} {'>6ft out':>9} {'>10ft out':>10} {'worst meet':>11}"
      f" {'mean short (ft)':>16}")
for pa in (6.0, 8.0, 10.0, 12.0, 16.0, 22.0, 1e9):
    T.PLAY_AREA = pa
    ok = 0
    shorts, outs, worst_off = [], [], 0.0
    for p, land, ft, bounce, surface, a, kw in CALLS:
        m = _orig(p, land, ft, bounce, surface, *a, **kw)
        if m["ok"]:
            ok += 1
            off = outside(m["meet"][0], m["meet"][1])
            outs.append(off)
            worst_off = max(worst_off, off)
        else:
            shorts.append(m["short_ft"])
    print(f"{pa if pa < 1e6 else 'none':>8} {ok/len(CALLS):9.1%} {sum(o > 6 for o in outs)/max(1,len(outs)):9.1%}"
          f" {sum(o > 10 for o in outs)/max(1,len(outs)):10.1%} {worst_off:11.1f}"
          f" {sum(shorts)/max(1,len(shorts)):16.1f}")
