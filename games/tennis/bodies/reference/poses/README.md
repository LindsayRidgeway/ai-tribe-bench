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

Also present and harmless: a soft floor shadow. The silhouette instrument separates her from it without help
(checked on panel 1 of f1-c: mask rows 236–1136, shadow below threshold), so the ask is not "no shadow" but
"the racquet clear of her body", which is the overlap that does obscure a measurement.
