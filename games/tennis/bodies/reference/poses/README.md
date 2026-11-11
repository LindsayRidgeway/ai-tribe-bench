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

## The outfit block

The founder's suggestion, 2026-11-11: name the kit in numbers, not adjectives. He is right, and for a reason
beyond tidiness — the sheets came back with the top sometimes a tee and sometimes a tee-dress, and a hem that
moves changes the silhouette the instrument reads. Two of the thirteen landmarks in `lab/reference.py` are
"hip / skirt" at 0.50 of height and "under the skirt" at 0.44; if the hem is in a different place in panel 2 than
in panel 4, those two rows are measuring different garments.

Revision 2, after the first sheet made with it (`f1-e.jpg`). His corrections, all four taken:

- **No shorts.** The inner shorts clause — "white inner shorts ending 1 inch below the skirt hem" — came back as
  visible white briefs below the hem in four of six panels, which is underwear drawn by a machine that read the
  words and not the intent. The skirt is a single layer and nothing shows under it. Deleted.
- **Not "her hair tied back off her face".** Deleted outright. It is the character reference's job: `@kirsten`
  already fixes the hair, and instructing it again in words is a second opinion that competes with the first.
- **"jewelry"**, his spelling, not "jewellery".
- **"extra arms" goes back in the negative.** He is right and my reasoning last turn did not cover it: "extra
  arms" is a count correction and it works; "two hands" was a penalty on a body part the positive was asking
  for, and it damaged the hands. Different mechanisms. Keep count terms, drop part penalties.

The paragraph, verbatim in every set from here — f, b, s and m:

> Her outfit is identical in every frame: a fitted white athletic T-shirt with a plain crew neck, short sleeves
> ending about 6 inches above the elbow, and a hem ending 3 inches above her navel, so exactly 3 inches of bare
> midriff shows; a white tennis skirt with the waistband on her hips and the hem 4 inches above the knee, a single
> layer with no shorts, no briefs and nothing visible below the hem; white ankle socks and white tennis shoes. No
> logos, no wristbands, no headband, no watch, no jewelry, nothing on her wrists or hands.

Nothing on the wrists is measurement, not taste: the wrist is one of the landmarks and a sweatband moves it.

Negative, revision 2:

> tennis racquet, ball, shadow, extra arms, extra hands, text, watermark, logo, side view, back view, motion
> blur, different woman, different outfit, cropped head, cropped shoes.

`f1-e.jpg` also failed the framing instruction in two panels — panel 2 has no shoes in frame and panel 5 stops at
the ankles — and put a horizon line behind her in one panel and not the next. So the wording now says there is
empty background above her head and below her shoes in every frame, and the backdrop is flat mid-grey with no
floor line. The costume is fixed; the framing is not yet.


## f1-f — framing fixed, and the swing lost with it

`f1-f.jpg` is the first sheet that passes the framing instruction: head to shoes inside every frame with margin,
flat backdrop, no shorts, midriff consistent. And it is the worst sheet for the thing the sheet exists to
measure. Panels 4, 5 and 6 are a wave, folded arms and a catalogue stance — not a forehand. Take the racquet out
and the model loses the verb: "forehand" without an implement is a woman standing with her arms out.

So the founder's two corrections, 2026-11-11, both taken:

- **"invisible racquet".** Tell the model she is swinging a racquet that cannot be seen, rather than that she is
  holding nothing. The motion survives and nothing is drawn. It also fixes something I got wrong: a forehand hand
  is *closed* around a grip, not open. The flat open palm I asked for, to keep the model from mangling fingers,
  was a worse landmark than a fist — and it read as waving.
- **hair in a ponytail, back in.** Without the line, six panels of long hair falling over the shoulders, which is
  the neck and the shoulder-line landmarks gone. Not a taste note: a ponytail keeps two of the thirteen rows
  readable.

Negative gains `visible tennis racquet`. The count terms (extra arms, extra hands) stay; `two hands` stays out.

## f1-g, and the end of the swing sheet

`f1-g.jpg` is the invisible racquet. It bought the verb back — the arms swing, the turn is there — and it paid
for it with a fist closed around a black stub drawn in every panel, because "invisible racquet" is a contradiction
a rendering model resolves by drawing a small piece of one. Panels 4 and 5 are punches. Nothing in the sheet is a
forehand.

Eight grids, four prompts, no forehand. The conclusion is not that the prompt needs a ninth revision. It is that
a photograph cannot tell me eight joint angles per moment, and the model has a strong prior about what a tennis
portrait looks like which no wording has moved. The swing becomes a rule in `replay3d.html`, written against the
geometry the engine already knows — contact point, contact height, the ball's exit direction, the stance the run
record produced — and checked by looking at the render, which takes seconds instead of a generation round-trip.

The founder's hair correction stands for any future sheet: **"face-framing loose pony-tail"**. Loose and framing
the face is the character; clear of the shoulders is the measurement (the neck and shoulder-line rows of the tape
need a silhouette without hair across them), and a loose ponytail is the only wording that has produced both.
