#!/usr/bin/env python3
"""Read a standing figure's landmarks out of a photograph or a render, with the same code for both.

    python3 lab/reference.py games/tennis/bodies/reference/woman-front-open-1.jpg \
                            games/tennis/bodies/stills/model-rest.png

Why a second instrument. `measure.py` answered one question — how wide is this figure at each height —
and it answered it well enough to catch short arms and a wide head. What it could not answer is *which
part* is wide: an arm held against the waist and a waist as wide as an arm are the same total width. So
this one splits each scan line into islands (torso, left arm, right arm are three), anchors on the body's
centre column and reports the *core* width (the island containing the centre) separately from the limbs.
With the arms held away from the body and the legs apart, that turns one number per height into a
part-by-part table: head, neck, shoulder, chest, waist, hip, each thigh, each knee, each calf.

Everything is a fraction of the figure's own height, so a 1152-pixel photograph and a 900-pixel render
are comparable, and nothing depends on how far away the camera was.

Caveats, stated rather than discovered later: a visor or a ponytail is part of the silhouette and
inflates the head band; a skirt is not a hip; a cast shadow under the feet is not a foot; a shoe is not
an ankle. Where a landmark cannot be trusted the table prints `--` rather than guessing.
"""
import sys

import numpy as np
from PIL import Image

GAP = 4          # pixels of background that separate two islands
EDGE = 12        # pixels of background sampled at each row's left and right edge


def mask_of(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    edge = np.concatenate([a[:, :EDGE, :], a[:, -EDGE:, :]], axis=1)
    bg = np.median(edge, axis=1)[:, None, :]          # this row's own background, not the whole image's
    m = np.abs(a - bg).max(axis=2) > 30
    # A floor plane, a gradient or a shadow can survive the threshold. Keep rows that are at most 0.75 of
    # the frame wide; a person never is, a background artefact usually is.
    m[m.sum(axis=1) > m.shape[1] * 0.75] = False
    return m


def islands(row):
    """Each contiguous run of subject pixels on this scan line, as (left, right, width)."""
    xs = np.flatnonzero(row)
    if len(xs) == 0:
        return []
    cuts = np.flatnonzero(np.diff(xs) > GAP)
    starts = np.concatenate(([xs[0]], xs[cuts + 1]))
    ends = np.concatenate((xs[cuts], [xs[-1]]))
    return [(int(s), int(e), int(e - s + 1)) for s, e in zip(starts, ends)]


class Figure:
    def __init__(self, path):
        self.path = path
        self.m = mask_of(path)
        rows = [i for i in range(self.m.shape[0]) if islands(self.m[i])]
        if not rows:
            raise SystemExit(f"{path}: no figure found — is it cropped too tight to see the background?")
        self.top, self.bottom = rows[0], rows[-1]
        self.H = self.bottom - self.top + 1
        self.cx = int(np.median([np.flatnonzero(self.m[i]).mean() for i in rows]))
        self.rows = np.arange(self.top, self.bottom + 1)
        self.isl = {y: islands(self.m[y]) for y in self.rows}
        self.z = (self.bottom - self.rows) / self.H            # height fraction, 0 at the feet
        self.core = np.array([self._core(y) for y in self.rows], float)
        self.total = np.array([(i[-1][1] - i[0][0] + 1) / self.H if i else 0 for i in self.isl.values()])
        self.n = np.array([len(i) for i in self.isl.values()])
        self.core /= self.H
        # Smooth over seven scan lines (0.7 % of a figure) before looking for structure. A one-row notch —
        # the antialiased top edge of a visor, a highlight the colour of the backdrop — otherwise reads as a
        # neck: it is what made the first version declare a 955-pixel figure to be 1.0 heads tall.
        k = 7
        pad = k // 2
        self.smooth = np.median(
            np.lib.stride_tricks.sliding_window_view(np.pad(self.core, pad, mode="edge"), k), axis=-1)

    def _core(self, y):
        for s, e, w in self.isl[y]:
            if s <= self.cx <= e:
                return w
        return 0.0            # the centre column is in the gap: two legs, nothing between them

    def at(self, z):
        y = int(round(self.bottom - z * self.H))
        y = min(max(y, self.top), self.bottom)
        return self.isl[y]

    def peak(self, z0, z1, series=None):
        series = self.core if series is None else series
        sel = (self.z >= z0) & (self.z <= z1)
        if not sel.any():
            return None
        i = np.flatnonzero(sel)[np.argmax(series[sel])]
        return float(self.z[i]), float(series[i])

    def trough(self, z0, z1, series=None):
        series = self.core if series is None else series
        sel = (self.z >= z0) & (self.z <= z1)
        if not sel.any():
            return None
        i = np.flatnonzero(sel)[np.argmin(series[sel])]
        return float(self.z[i]), float(series[i])

    def legs(self, z, reach=0.18, thin=0.15):
        """The two limb islands nearest the centre line, as (width, centre x) each, left to right.
        The reach and thin filters keep a hand hanging beside a skirt out of the leg count."""
        isl = [t for t in self.at(z)
               if abs((t[0] + t[1]) / 2 - self.cx) < reach * self.H and t[2] / self.H < thin]
        if len(isl) < 2:
            return []
        pair = sorted(isl, key=lambda t: -t[2])[:2]
        return sorted(((w / self.H, (s + e) / 2) for s, e, w in pair), key=lambda t: t[1])

    def colours(self, z=0.60, pad=6):
        """Median colour of the core at a height, for colour-matching the kit and the skin."""
        y = int(round(self.bottom - z * self.H))
        isl = [t for t in self.isl[y] if t[0] <= self.cx <= t[1]]
        if not isl:
            return None
        s, e, _ = isl[0]
        a = np.asarray(Image.open(self.path).convert("RGB"))
        patch = a[y - 2:y + 3, s + pad:e - pad + 1].reshape(-1, 3)
        return tuple(int(v) for v in np.median(patch, axis=0))


TAPE = [                      # the measuring tape: heights every body has, in units of figure height
    ("crown", 0.97), ("head widest", 0.92), ("jaw / neck", 0.87), ("shoulder line", 0.78),
    ("upper chest", 0.70), ("chest", 0.62), ("waist", 0.56), ("hip / skirt", 0.50),
    ("under the skirt", 0.44), ("mid thigh", 0.36), ("knee", 0.26), ("calf", 0.20),
    ("ankle / shoe", 0.08),
]


def segments(f):
    """Head, neck and shoulder from the figure itself, by walking down from the crown: the head is wide,
    the neck is a pinch, the shoulders are the next rise. Cheap and stable on the shapes we have —
    a person — and it fails visibly (`--`) on a shape that is not one."""
    core, total, z = f.smooth, f.total, f.z
    n = len(core)
    i, head_max, head_i = 0, 0.0, 0
    while i < n and (head_max == 0 or core[i] > 0.72 * head_max):
        if core[i] > head_max:
            head_max, head_i = core[i], i
        i += 1
    chin = min(i, n - 1)
    j = chin
    neck, neck_i = core[chin], chin
    while j < n and core[j] <= max(1.5 * neck, 0.02):
        if core[j] < neck:
            neck, neck_i = core[j], j
        j += 1
    sh_lo = j
    sh_end = min(n - 1, j + int(0.10 * f.H))
    sh_i = sh_lo + int(np.argmax(total[sh_lo:sh_end + 1])) if sh_end > sh_lo else sh_lo
    bad = not (0.045 < neck < 0.14 and head_max > 1.3 * neck and total[sh_i] > 1.4 * neck)
    return {"head": (z[head_i], head_max), "neck": (z[neck_i], neck), "chin": (z[chin], core[chin]),
            "shoulder": (z[sh_i], total[sh_i]), "ok": not bad}


def report(path, fine=False):
    f = Figure(path)
    print(f"\n=== {path}")
    print(f"figure height {f.H} px   centre column {f.cx}   frame {f.m.shape[1]}x{f.m.shape[0]}")

    seg = segments(f)
    if seg["ok"]:
        print(f"head widest {seg['head'][1]:.3f} at z={seg['head'][0]:.3f}   "
              f"neck {seg['neck'][1]:.3f} at z={seg['neck'][0]:.3f}   "
              f"shoulder line {seg['shoulder'][1]:.3f} at z={seg['shoulder'][0]:.3f}")
        head_h = 1.0 - seg["chin"][0]           # crown to jaw, not crown to the neck's pinch
        print(f"head height (crown to jaw) {head_h:.3f} h  ->  {1 / head_h:.1f} heads tall")
    else:
        print("head / neck / shoulder: -- (this silhouette does not segment as a lone standing figure)")

    print("\nmeasuring tape (width / figure height; core = the island at the centre column)")
    print(f"  {'landmark':16s} {'z':>5} {'core':>6} {'total':>6}  islands")
    for label, z in TAPE:
        isl = f.at(z)
        if not isl:
            print(f"  {label:16s} {z:5.2f}    ---")
            continue
        core = next((w / f.H for s_, e_, w in isl if s_ <= f.cx <= e_), 0.0)
        tot = (isl[-1][1] - isl[0][0] + 1) / f.H
        print(f"  {label:16s} {z:5.2f} {core:6.3f} {tot:6.3f}  {len(isl)}  " +
              " ".join(f"{w / f.H:.3f}" for _, _, w in isl))

    print("\nlegs and stance (two lowest islands on the scan line)")
    for label, z in (("under the skirt", 0.44), ("mid thigh", 0.36), ("knee", 0.26),
                     ("calf", 0.20), ("ankle", 0.08)):
        pair = f.legs(z)
        if not pair:
            print(f"  {label:16s} z={z:.2f}   merged")
            continue
        gap = (pair[1][1] - pair[0][1]) / f.H
        print(f"  {label:16s} z={z:.2f}   widths {pair[0][0]:.3f} {pair[1][0]:.3f}   "
              f"centres {pair[0][1]:.0f} {pair[1][1]:.0f} px, stance {gap:.3f}")

    if fine:
        print("\nprofile  z:  core  total  islands")
        for z in np.arange(0.02, 1.0, 0.01):
            isl = f.at(z)
            if not isl:
                continue
            core = next((w / f.H for s_, e_, w in isl if s_ <= f.cx <= e_), 0.0)
            tot = (isl[-1][1] - isl[0][0] + 1) / f.H
            print(f"  {z:4.2f}  {core:5.3f} {tot:5.3f}  {len(isl)}  " +
                  " ".join(f"{w / f.H:.3f}" for _, _, w in isl))
    return f


if __name__ == "__main__":
    fine = "--fine" in sys.argv
    for p in [a for a in sys.argv[1:] if not a.startswith("--")]:
        report(p, fine=fine)
