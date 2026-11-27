# golf — for a beta tester

Written 2026-11-20, at the end of the seventeenth pass; last revised 2026-11-27, at the end of the
twenty-fifth. The game is `lab/golf.py`; the pages it writes are in
`renders/`; the record of every pass is `records/golf-2026-11-19.txt`; the findings are `README.md` beside this
file. Start at **`renders/start.html`** — it is the door, and it links everything below.

**If you are reading this as a Kythe beta tester**, you do not need any of that. Press **Play** in the app: below the
tennis forms is golf's card — six programs, four rounds, every number with its error — the six replays it wrote, each
opening in a sandboxed frame, and a button. The card starts as the project's own `season.json`, the same one this
file's door reads, and says so in words. Press **Play a season in this circle** and your own repository plays a
season, draws a new seed, and commits the card and the replays into `games/golf/renders/` — three minutes, no key,
because golf asks no model anything. If your circle was made before golf existed, the press writes the four missing
files into it first and then plays; if your sign-in was not granted GitHub's `workflow` permission it cannot write the
workflow file, and it will say exactly that rather than start a run that cannot work. No member of yours is on the course, and that is the game, not a gap in it.

---

## 1. What this is, and what it is not

**It is** a golf game with no player in it. Six programs play the same nine holes. Each is allowed to learn a
different part of what a golfer has to learn — how far each club goes, how much the wind takes off, how far its own
hands miss by — and nothing else is given to any of them. The claim being tested is that a player which has measured
itself plays better than one which has not, and that the measurement is visible in the data rather than asserted.

**It is not** a game you play. There is no club to choose, no button to press, no score to beat. That was a
decision, not an omission: the game's subject is a program's own uncertainty, and a human at the controls would
cover it up. If you came for something to play, this is the wrong file and you should be told so on the door.

**It is also not** a claim about golf. Every number here comes out of one physics integrator (`lab/tennis.py`'s
flight, with golf's constants) and two learners, and it agrees with published golf to a tenth of a stroke on the
green and to a few per cent on the bag. Where it does not agree, this file says so.

---

## 2. What I would like you to judge

Three questions, in the order I would ask them of myself.

1. **Is the learning visible?** Open `renders/season.html`. The middle panel is each athlete's belief about the
   scatter of its own hands, per round, drawn against the 1.10° it actually has and the 1.50° it was told before it
   hit a ball. A player that converges on the dark line has measured itself. A player that does not move has been
   told the answer and kept it. If you cannot see the difference in that panel in ten seconds, the panel is wrong
   and I want to know.
2. **Do you believe the numbers?** Every figure on every page carries its error bar, and section 4 says what the
   bars are. Pick any two numbers that differ by less than their bars and check that nothing on the page claims
   they differ. If something does, that is a defect of the first order and I would rather hear it than any other
   kind of report.
3. **Is the picture worth looking at?** `renders/hole-7.html` (nineteen seconds), `renders/round.html` (a whole
   round, three and a half minutes), `renders/best-hole.html` and `renders/worst-hole.html`. The camera solves
   itself from each shot. Tell me the moment you stop watching, and roughly what time it was on the clock in the
   bar — a film that loses a viewer at a particular frame is a fact I can use, and "it's fine" is not.

---

## 3. What is known wrong

Dated, with the number that shows it. Nothing in this list is a surprise to me; several of them have been the whole
subject of a pass.

**The objective is too kind about holding a green.** As of pass 19 the landing has two dimensions — lateral
position against the green's ellipse, and depth as a spread learned from the athlete's own misses (dated
2026-11-22). What it still cannot say is that a ball sometimes does not *have* the club. From 150 yards the
objective puts 95% of its shots on the green; the game holds 53%. The gap is not the geometry: the gear ladder is
coarse, the athlete's prior is linear in effort when the flight is not (a 60% five-iron believes 117 yards and
delivers 102), and the club-choosing rule prefers exactly those partial gears. A spread wide enough to carry that
makes the objective fatalistic — everything is off the green, the aim stops being a decision, and the best athlete
in the field lost seventeen strokes to it. So the model is narrow and known to be kind, and the next thing to try
is a mixture: how often the club is wrong, and how far off it is when it is. There is no bar on this one; it is a
distance between two measurements, not a sample.

**Direction was on this list, came off it, and then was taken back off it — this is the item to read if you only
read one.** A 12 ft putt *did* cost more across the fall line than along it: 0.45 ± 0.07 of a stroke, pooled over
six distances, measured 2026-11-27. On 2026-11-27, later the same day, the same fit read **−0.01 ± 0.05**, because
the putter that produced the first number was wrong: it computed its pace on the line it aimed while the ball rolled
the line it read, and it read a putt that runs past the hole at the place where it *stopped*. The break did not
shrink; the thing measuring it was broken, and it was broken in a way that made a putt across the slope harder than
a putt along it. Fixed, both direction terms are zero — pass 24 read break −0.01 ± 0.05 and downhill putt
−0.01 ± 0.02; pass 25 reads **+0.00 ± 0.00** for both, because the read now aims at the centre of the hole rather
than anywhere inside the rim, and nothing in the model prices the direction of a miss — and the green got 0.2 to
0.3 of a stroke cheaper past 6 ft, which is why the card moved.

One defect is left where that number used to be, and pass 25 made it bigger rather than smaller. **The putter
never misreads a green** — its read is exact to a hundredth of a foot — so the break is a picture and not a price,
and its green is now much cheaper than golf's. A player with 1.1° of face, 1.5% of pace and a perfect read holes
90% of six-footers; golf holes about 70%. That is the largest single thing wrong with this game and the next
object.

The other defect that used to sit here — **nothing priced the putt it leaves** — is gone. Pass 25 gave the pace the
one-step lookahead it needed, `1 + E[green_cost(what it leaves)]`, and the aim came back from the rim's edge
(0.81 ft at 3 ft, 2.24 at 12) to 0.31 and 1.14. What that term did *not* buy is the downhill: the price of a miss
is its **length**, and `green_cost` is the bearing average — one curve up the slope and down it — while the
overshoot in feet is direction-free anyway (the pace is chosen as a distance, the hand errs as a fraction of
speed). So "keep it below the hole" is still worth nothing here, but now for a reason that is a statement about
the model rather than a missing term: a comeback that arrives *fast* is a second dimension of the green.
`target()` is still told the mean curve on purpose: a landing that is as likely short as long makes the two halves
of a break cancel exactly, and wiring the term in moved the aim by no feet.

**What the depth bought, stated plainly, because it is less than the file expected.** Over 1,080 holes played
against the previous version, paired by course and seed, the whole change — the distance fix and the depth — is
worth +0.007 ± 0.037 of a stroke a hole. The depth's own share is −0.033 ± 0.022, about a third of a stroke a
round. On the season page the two athletes that practise hardest gain 4.0 and 4.5 strokes and the one that never
practises loses 3.5, inside its own band. If you play this and it feels like the aiming never changes, that is
the measurement, not your imagination.

**The sand's direction is not resolved.** Four passes of hazards failed to make the target decision directional.
The depth moved it: +0.57 / −0.37 on twenty courses — and −0.27 / +0.00 on the same twenty courses in another
configuration of the same pass. That is the instrument's noise, and I am not claiming the effect.

**The wind and the aim.** The frozen player — the one that never practises — scores +14 a round aiming at the flag,
+10 aiming at the middle, and +15 aiming where the objective says (record pass 13). The objective's advice is good
advice for a player that has measured itself and bad advice for one that has not, because an unlearned player has a
2.2° hand bias and an unlearned crosswind and scatters about a point that is not where the objective thinks it is
aiming. **This is recorded, not repaired.**

**The read used to aim at the rim rather than the hole, and it was worth 0.08 of a stroke.** `putt_read`
corrected the face until its trial putt finished *anywhere inside the cup*, on the sound principle that a made
putt is on the line. The principle is wrong by a rim radius: the line it returned crossed the hole on the edge, and
a 1.1° hand error tipped it out. A 3 ft putt went in 91% of the time and now goes in 99%; the crossing is within
0.0085 ft of the centre at 3, 6, 12 and 20 ft, against 0.18 before. Found 2026-11-27, fixed the same day, and
written down because it is the third defect in three passes that lived in a *stopping rule* rather than in the
physics — and because the check that should have caught it asserted the crossing was inside a rim, which is where
the loop had stopped. That check now asks for a hundredth of a foot.

**The cup's depth does not read.** As of pass 18 the hole is a cylinder 4.25 in across and 4 in deep with a wall and
a floor, and the ball falls the last four inches and fades. At the distance a putt is filmed from the cup is four to
eight pixels across, so **the wall is invisible**; what you see is a ball vanishing into a dark disc. That is the
honest state of the best frame in the game.

**The putter has no read error, and it is now the largest single thing wrong with the short game.** Its read of
the break is exact to a hundredth of a foot (it runs the game's own roll and corrects until the ball crosses
within 0.01 ft of the hole's *centre* — pass 25 fixed that; it used to stop anywhere inside the rim), so its line
error is one constant 1.1° at every distance, where a real golfer misreads more the longer the putt. Consequences,
all measured on 2026-11-27: the green costs **1.04 against golf's 1.35 at 6 ft and 1.67 against 1.90 at 20** — and
1.00 at 2 and 3 ft, where every one of 72 positions was holed — and the break costs it nothing at all. A probe that
halves the read puts the curve at 1.03 / 1.21 / 1.39 / 1.67 / 1.96 and the holed rates at 85 / 60 / 27 / 13% from
2 / 4 / 6 / 12 / 20 ft, which is golf's green within a tenth everywhere except 20 ft. That is what the missing
misread is worth. It is not built, and a scale factor I picked would be a fitted number: the mechanism has to be a
player's *belief* about the slope, learnable from its own misses, or it is a difficulty setting.

**The putter over-believes its own face, and it is a censored sample.** A putt is only shown to it if it missed, and
a miss from 3 ft is a putt that passed two inches wide, so the scatter it measures is the tail of its own
distribution: it believes 2.8° of face for hands that have 1.1°. It does not use that number to make a decision —
the number it uses, how badly it misses its pace, is learned from real rolls and reads 0.027 against hands of 0.015
— but the belief is wrong and nothing in the game corrects for the censoring yet.

**The green has no contour.** One grade, one fall line, everywhere. No tiers, no swales, no two-break putts.

**There is no dogleg.** The corridor is straight and 40 yards wide, so the driver's distance has never been a
decision — it is always "hit it as far as you can". Geometry, not physics, and unbuilt.

**A bunker shot cannot plug, and a lie cannot be bad.** No plugged lies, no sitting down in the rough, no flyer.

**The field is one program's athletes, not six people.** Six strategies sharing one notebook's ancestry. Putting
six *members*' numbers on one board is something the members would have to do in their own windows, and nobody —
least of all the founder — can order it. The pages say this in their own footers.

**The rough's price was 0.3 of a stroke too dear, and it was fixed by the second instrument, not the first.** It
sat at 2.60 from pass 10 to pass 23 on the rule that a constant re-measured and then checked against its own
measurement is a fitted number. Pass 24 lowered it to 2.38, and not on that rule's terms: the green got cheaper,
which widened the green-to-rough margin, and the *card* then caught it — aiming at a tucked pin paid 1.11 ± 0.55
better than aiming away from it, where the objective says it costs 0.58. At 2.38 the contradiction went
(+0.03 ± 0.48). `--costs` reads 2.23 / 2.19 / 2.71 at 36 / 48 / 60 ft, so 2.38 is its own midpoint.

**And the same card has now flipped, which is the open contradiction in this file.** Pass 25 made the green cheaper
again — 1.00 at 3 ft, 1.04 at 6 — and the card's verdict on that tucked pin went from +0.94 to **−0.97 ± 0.51**,
i.e. from "aiming at the pin costs you" to "aiming at the pin saves you", while the objective still prices the
safe aim as 0.56 better. The objective's own gradient in distance moved by less than 0.01 (12 ft costs 1.46 and
2 ft 1.00, a gap of 0.46 before and after), so the arithmetic says that card should have moved by a tenth of a
stroke and it moved by nineteen. Something is missing from `scores()` and this pass could not identify it. The
candidates are named in the check, which now asserts the *gap* rather than agreement. If you are the kind of
tester who wants one thing to look at, look at that: a game whose target decision is worth 1.9 strokes a round in
one instrument and the opposite 0.6 in another has a term nobody has written down.

**A ball is drawn with a floor of 2.2 px.** At the distance a golf shot is photographed from, a 1.68 in ball is
half a pixel, and a half-pixel ball is invisible; the floor is a marker, not a measurement, and the scale bar is
what says how big the world is. (The ball was drawn at *twice* its real size until pass 18, because the constant
was a diameter used as a radius. Nothing could have shown it until a ball had to fit inside a cup.)

---

## 4. The bars, and the rule about them

Every number on every page carries its own error bar, or the page says why it has none. That is a typographic rule
and not a claim about honesty, and the precedent is the fund fact sheet: a return is printed beside its standard
deviation because in that trade the error bar *is* the product.

**What the bars are.** A bar is ±1.96 standard errors. The standard error is taken across **four practice
sessions**: the season is played four times over, with a different practice session at the start of each, and the
same courses and pins, so the band is the part of the result that was the day rather than the player.

**What the paired columns are.** Every athlete meets the same drawn course and the same wind in a round, so the
difference between an athlete and the frozen player cancels the weather and leaves the notebook. That difference has
a narrower bar than either raw score, and it is the column to read. The season page draws nothing else.

**Where the rule is enforced.** In code, not in prose. `lab/golf.py`'s `_bar()` is the only function on the start
page that formats a mean, and it cannot print one without its standard error. The season page's panels are drawn
from the same records. This file is the one exception, and it names its numbers *and* their source so that a reader
can go and check them.

---

## 5. How to run it

    python3 lab/golf.py --selftest                 # the checks: the numbers everything else rests on
    python3 lab/golf.py --season                   # the season, as a page (renders/season.html)
    python3 lab/golf.py --start                    # the door, from the season's own record (needs --season first)
    python3 lab/golf.py --render 7                 # one hole, filmed
    python3 lab/golf.py --render round             # the whole round, filmed
    python3 lab/golf.py --render best|worst|lip    # the best hole, the worst hole, the bunker's face

Nothing needs a server, a key or a network. Every page in `renders/` is a file that opens from disk; the two chart
pages have no script in them at all, and the films have one because a camera cannot be baked.

---

## 6. What would be a defect worth telling me about

- **A number without a bar**, anywhere.
- **Two numbers claimed to differ whose bars overlap.**
- **A page that contradicts another page** about the same figure or the same stroke.
- **A picture that disagrees with its own caption** — this has happened twice (a ball that stopped where it
  stopped flying rather than rolling, twenty-five yards apart; a putt line that bent a fraction of an inch off its
  own start), and both were found by looking, not by a check.
- **A film that loses you**, with the clock reading when it did.
- **A sentence in the record or the README that the code no longer supports.** That is the failure mode of a project
  that writes a lot down, and it is the one I would most like caught.

What is *not* a defect: the game not being fun, because it is not a game you play; the graphics not being a
commercial game's, because they are a projection and a painter's sort; and the putts not being in the film, because
as of pass 16 they are.
