# Pose references

Photographs generated with Mage, one grid per stroke and camera, at the founder's hands from prompts written
here. They are reference, not record: nothing in the game is drawn from these, and no pixel of them reaches a
player. What is taken from them is measurement — joint positions and the angle of the racquet to the forearm at
named moments — in the same way `lab/reference.py` took proportions from the standing sheet.

The rule the file names follow: `<set><n>-<variant>.jpg`, where a set is f = forehand, b = backhand, s = serve,
m = movement; the camera is the front (far-end) view unless suffixed `-back` (near-end) or `-side`.

## f1 — forehand, front view, first attempts

- `f1-a.jpg` — the prompt without a character reference.
- `f1-b.jpg` — a different character.
- `f1-c.jpg` — `@kirsten`. The founder's choice, and mine, and not for taste.

Three runs of the same text produced three different women: different face, different build, different kit.
Joint angles measured across that set would be an average of three bodies, which is not a measurement of
anything. With a named character the figure is one person from panel to panel, so an elbow angle in panel 2 and
a knee angle in panel 5 belong to the same body and can be fitted together.

All three fail the pose brief in the same way, and the fault is the prompt's, not the model's: the arc described
("racquet back and up on her right side", "carried up and across", "finish over her left shoulder") is a
two-handed backhand's arc, and that is what the model drew in panels 2 and 6 — both hands on the handle. The
corrected text names the left hand in every panel and puts the racquet in the right hand only.

## f1-d — the corrected text, run once

- `f1-d.jpg` — the same brief with the left hand named in every panel and the racquet in the right hand only.

It is half a fix. Panels 3, 4 and 5 are a one-handed forehand with the left hand open and clear of the body —
that is the arc the renderer needs, and the first time the sheet has produced it. Panels 1, 2 and 6 went back to
two hands on the handle, which are the frames where the racquet passes the body and the model reaches for the
familiar shape. Naming the left hand is not enough to hold it there.

## The next sheet drops the racquet

Measurement does not need it. The racquet in the game is built in the page, not in the .glb, and its angle is
computed every frame from the direction the engine says the ball left in (`placeRacquet` aims the shaft at the
ball and rolls the bed to `sh.v0`). Nothing about the racquet is measured from a photograph, so drawing one in a
reference sheet buys nothing and costs the two failures that keep coming back: a second hand on the handle, and
a racquet lying across the torso where the silhouette instrument cannot separate it from her waist.

The body is what is measured — ankle, knee, hip, shoulder, elbow, wrist, and the angle between the two arms.
Six frames of a one-handed forehand, hands empty, is a sheet the instrument can read and the model can draw.

Also present and harmless: a soft floor shadow. The silhouette instrument separates her from it without help
(checked on panel 1 of f1-c: mask rows 236–1136, shadow below threshold), so the ask is not "no shadow" but
"the racquet clear of her body", which is the overlap that does obscure a measurement.
