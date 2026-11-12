# Taking a still

Every picture in `stills/` comes from one command. It lives here because it was asked where it is kept, and the
answer was "in a chat" — which is not a place.

```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --use-angle=metal --run-all-compositor-stages-before-draw --hide-scrollbars \
  --window-size=1440,810 --virtual-time-budget=12000 \
  --screenshot=games/tennis/stills/NAME.png \
  "http://localhost:8778/games/tennis/demo3d.html?point=1"
```

Three of those flags are not decoration:

- `--use-angle=metal` — without it WebGL cannot create a context on this Mac (`VENDOR = 0xffff, GL_VENDOR =
  Disabled`) and the screenshot is a black rectangle.
- `--headless=new` — the old `--headless` gives the same black rectangle even with Metal, and the page's own
  readouts stay at their `—` placeholders because the script never runs.
- `--run-all-compositor-stages-before-draw` — otherwise the canvas is captured before the first frame lands, and
  every still is byte-identical to every other still.

The server is already up at `http://localhost:8778` from `~/ai_tribe` (`python3 -m http.server 8778`). A `file://`
URL will not load the `.glb` bodies, so the page needs the server.

## Jumping to a moment

The page takes three query parameters, all of which pause the film so the still is repeatable:

- `?point=5` — the end of rally 5: the point board, and the clock stopped.
- `?shot=12` — shot 12, with `&at=0.8` to choose how far through it (0 to 1).
- `?t=41.2` — an absolute time in seconds of film.

`?cam=near` puts the camera beside the near baseline for looking at feet. `?cam=hit` goes over the striker's own
shoulder, and `?cam=net` stands square on to the net from the side — which is the only way to see whether the
headband follows the sag and whether the centre strap reaches the ground.
