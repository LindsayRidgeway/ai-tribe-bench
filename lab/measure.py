#!/usr/bin/env python3
"""Measure a standing figure from a photograph or a render, and print its width profile.

The same code runs on the reference and on the model's own render, so what is compared is two numbers
produced identically, not a number and an opinion. A pixel belongs to the subject when it differs from the
background (taken from the top-left corner) in any channel. Per row, the subject's width is the longest
contiguous run of such pixels — not the row's total extent, which would swallow a cast shadow on one side.
Rows whose run is implausibly wide to be a person are dropped: that is how the floor plane in a render
gets excluded without a separate rule for floors.

    python3 lab/measure.py <image> [more images]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BAND = 0.05
WIDEST = 0.60        # no human is 60% of their height wide; anything wider is a floor or a shadow


def row_widths(mask):
    """Horizontal extent of the subject in each row: outermost subject pixel to outermost.

    Extent rather than longest run, because a figure with its arms at its sides has daylight between arm
    and waist at some heights and not others, and longest-run jumps between 'torso' and 'torso plus arm'
    from row to row. Extent is stable; the cost is that a shadow touching the figure would widen it, which
    is why the per-row background is measured at the row's own edges.
    """
    out = np.zeros(mask.shape[0])
    for y in range(mask.shape[0]):
        xs = np.flatnonzero(mask[y])
        if len(xs) > 1:
            out[y] = xs[-1] - xs[0]
    return out


def silhouette(path):
    """Background per row, taken from that row's two ends.

    A single corner colour fails on both of these images: the studio backdrop is a gradient, so a global
    threshold marks the backdrop itself as subject and every torso row is discarded as 'too wide to be a
    person'. Per-row edges follow the gradient and leave the subject as the only thing that differs.
    """
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    edge = np.concatenate([a[:, :12, :], a[:, -12:, :]], axis=1)
    bg = np.median(edge, axis=1)[:, None, :]              # one colour per row
    return np.abs(a - bg).max(axis=2) > 30


def profile(path):
    mask = silhouette(path)
    w = row_widths(mask)
    valid = (w > 0) & (w < mask.shape[1] * WIDEST)
    rows = np.flatnonzero(valid)
    if not len(rows):
        raise SystemExit(f"{path}: no figure found")
    top, bot = rows[0], rows[-1]
    h = bot - top
    prof = {}
    for i in range(int(1 / BAND)):
        y = int(top + h * (i * BAND + BAND / 2))
        prof[round(1 - (i * BAND + BAND / 2), 2)] = w[y] / h if 0 <= y < len(w) and valid[y] else 0.0
    return h, prof


def main(paths):
    data = [profile(p) for p in paths]
    print(f"{'height':>7}  " + "  ".join(f"{Path(p).stem[:16]:>16}" for p in paths))
    for k in sorted(data[0][1], reverse=True):
        print(f"{k:7.2f}  " + "  ".join(f"{d[1].get(k, 0):16.3f}" for d in data))
    for p, (h, _) in zip(paths, data):
        print(f"  {Path(p).name}: {h}px tall")
    print("\nwidths are fractions of the figure's own height — the only scale that compares across images")


if __name__ == "__main__":
    main(sys.argv[1:])
