#!/usr/bin/env python3
"""Regenerate the demo pages from replay3d.html / replay.html without replaying the physics: each demo already
carries its own record in <script id="script">, so the template only has to be re-stamped with it."""
import re, pathlib, sys

G = pathlib.Path(__file__).resolve().parent  # .../games/tennis
REPO = G.parents[1]
re3 = (REPO / "games" / "tennis" / "replay3d.html").read_text()
re2 = (REPO / "games" / "tennis" / "replay.html").read_text()
pat = re.compile(r'id="script">(.*?)</script>', re.S)

for name in sys.argv[2:] or ["demo3d.html", "demo3d-000.html", "demo3d-120.html"]:
    p = G / name
    m = pat.search(p.read_text())
    p.write_text(re3.replace("__SCRIPT__", m.group(1)))
    print(f"{name}: {len(m.group(1))} bytes of record re-stamped")

p = G / "demo.html"
m = pat.search(p.read_text())
p.write_text(re2.replace("__SCRIPT__", m.group(1)))
print("demo.html: re-stamped")
