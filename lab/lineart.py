#!/usr/bin/env python3
"""Measure a line drawing: silhouette widths as fractions of the figure's own height.

`lab/reference.py` measures photographs, where the figure is a solid dark mass on a light background and the
instrument can find islands. Line art is the opposite: almost everything is background and the ink is a thin
outline, so the island method finds nothing and the flood fill walks the whole page. What a line drawing gives
instead is an exact *outermost* ink pixel per scan line — the silhouette is the envelope of the drawing, and it is
crisper than any photograph's, because there is no shading gradient to move the edge by half a pixel.

    python3 lab/lineart.py games/tennis/bodies/reference/poses/look-gwen.jpg --cols 4 --rows 2

A grid sheet is split into equal panels; the panel borders and the hand-lettered title above the figure are
excluded before anything is measured.

STATUS 2026-11-11: **not trustworthy yet.** The first version measured the drawn panel border as the figure and
reported a shoulder width of 0.40 of body height for a woman; the second removed continuous lines and still reads
0.46 on the panels where an arm reaches the edge. It needs the border found and cut properly, not masked, and it
needs to be checked against a figure whose proportions are known — which is what its two predecessors each needed
before they could be believed. Nothing has been taken from these numbers.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# The same tape as `reference.py`, so the two instruments can be compared without conversion.
TAPE = [("crown", 0.97), ("head widest", 0.92), ("shoulder line", 0.78), ("upper chest", 0.70),
        ("waist", 0.56), ("hip", 0.50), ("mid thigh", 0.36), ("knee", 0.26), ("calf", 0.20)]

BORDER = 6          # px: the drawn rectangle around each panel
TITLE = 0.10        # the top tenth of a panel is the hand-lettered title, not the figure


def ink(path: str) -> np.ndarray:
    a = np.asarray(Image.open(path).convert("L"), dtype=float)
    return a < 150           # ink is anything clearly darker than paper


def panels(mask: np.ndarray, cols: int, rows: int):
    h, w = mask.shape
    ph, pw = h // rows, w // cols
    for r in range(rows):
        for c in range(cols):
            yield r, c, mask[r * ph:(r + 1) * ph, c * pw:(c + 1) * pw]


def measure(panel: np.ndarray) -> dict:
    """Silhouette of one panel, in fractions of the figure's own height."""
    h, w = panel.shape
    inner = panel[int(h * TITLE):h - BORDER, BORDER:w - BORDER]
    # The first version of this measured the panel border as if it were the figure: a drawn rectangle is a
    # continuous line down both sides of every panel, so every row read 0.40 and every landmark agreed with every
    # other. A border is a line that runs the whole length of the panel; a limb is not. Remove those first.
    keep_c = inner.mean(axis=0) < 0.85
    keep_r = inner.mean(axis=1) < 0.85
    inner = inner[np.ix_(keep_r, keep_c)]
    # A row belongs to the figure if it carries more ink than a stray fleck; a column likewise.
    rowink = inner.sum(axis=1)
    colink = inner.sum(axis=0)
    rlim = max(3, int(0.004 * w))
    rows = np.where(rowink > rlim)[0]
    cols = np.where(colink > rlim)[0]
    if len(rows) < 10 or len(cols) < 10:
        return {}
    top, bot = rows[0], rows[-1]
    H = bot - top
    out = {"height_px": float(H), "width_px": float(cols[-1] - cols[0])}
    for name, z in TAPE:
        row = int(top + (1.0 - z) * H)
        xs = np.where(inner[row])[0]
        out[name] = float(xs[-1] - xs[0]) / H if len(xs) > 1 else 0.0
    out["shoulder/hip"] = out["shoulder line"] / out["hip"] if out["hip"] else 0.0
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--rows", type=int, default=2)
    a = ap.parse_args(argv)

    mask = ink(a.path)
    print(f"\n=== {Path(a.path).name}  ({a.cols} x {a.rows} panels)")
    head = "panel      " + "".join(f"{n:>13}" for n, _ in TAPE)
    print(head)
    for r, c, panel in panels(mask, a.cols, a.rows):
        m = measure(panel)
        if not m:
            print(f"row {r + 1} col {c + 1}    — (no figure found)")
            continue
        line = f"row {r + 1} col {c + 1}  "
        line += "".join(f"{m[n]:>13.3f}" for n, _ in TAPE)
        print(line + f"   h={m['height_px']:.0f}px  w/h={m['width_px'] / m['height_px']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
