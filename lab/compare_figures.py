#!/usr/bin/env python3
"""Put a reference photograph and a build of the body side by side, at the same scale, cropped to the figure.

    python3 lab/compare_figures.py --out games/tennis/stills/reference-compare.png \
        --panel "reference, front:games/tennis/bodies/reference/woman-front-open-1.jpg" \
        --panel "model, front:games/tennis/bodies/gwen-measure-front.png" ...

Why: the only way I have ever caught a bad body in this project is by looking at it beside the thing it is
supposed to resemble. Two numbers matched and the legs were still half a person's width; the picture caught
it, the table did not. So the picture is the deliverable and the numbers are the footnote.

Each panel is cropped to the subject's own bounding box and scaled so every figure is the same height on the
sheet, which is the only way a comparison of proportions can be seen rather than trusted.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reference import Figure                                    # noqa: E402

PAD = 18
LABEL_H = 44


def crop_to_figure(path, height):
    f = Figure(path)
    m = f.m
    cols = [i for i in range(m.shape[1]) if m[:, i].any()]
    box = (max(cols[0] - PAD, 0), max(f.top - PAD, 0),
           min(cols[-1] + PAD, m.shape[1]), min(f.bottom + PAD, m.shape[0]))
    im = Image.open(path).convert("RGB").crop(box)
    scale = height / im.height
    return im.resize((max(1, int(im.width * scale)), height), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--height", type=int, default=820)
    ap.add_argument("--panel", action="append", default=[])
    args = ap.parse_args()

    panels = []
    for spec in args.panel:
        label, path = spec.rsplit(":", 1)
        panels.append((label, crop_to_figure(path, args.height)))

    gap = 26
    width = sum(p.width for _, p in panels) + gap * (len(panels) + 1)
    height = args.height + LABEL_H + gap * 2
    sheet = Image.new("RGB", (width, height), (22, 23, 26))
    draw = ImageDraw.Draw(sheet)
    x = gap
    for label, im in panels:
        sheet.paste(im, (x, gap))
        draw.text((x + 4, gap + args.height + 12), label, fill=(196, 200, 205))
        x += im.width + gap
    sheet.save(args.out)
    print(f"wrote {args.out}  {sheet.width}x{sheet.height}  {len(panels)} panels")


if __name__ == "__main__":
    main()
