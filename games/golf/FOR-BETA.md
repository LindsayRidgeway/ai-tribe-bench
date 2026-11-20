# golf — for a beta tester

Written 2026-11-20, at the end of the seventeenth pass. The game is `lab/golf.py`; the pages it writes are in
`renders/`; the record of every pass is `records/golf-2026-11-19.txt`; the findings are `README.md` beside this
file. Start at **`renders/start.html`** — it is the door, and it links everything below.

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

**The objective has one dimension where the game has two.** `target()` models a shot's *lateral* miss and assumes
the ball arrives at the pin's distance. Consequences, both measured on 2026-11-20:

- the sand looks reachable 42% of the time to the objective where the game finds it 11.6%, so the arithmetic is
  four times more frightened of a bunker than the golf is, and it will pay 0.70 of a stroke to avoid a hazard that
  costs 0.08 (README finding 12, record pass 13);
- a 12 ft putt costs 1.50 strokes up the fall line and 2.17 across it, while `target()` prices every 12 ft
  landing at 1.83 — a 0.67-stroke spread on a single landing, against the 0.87 the whole 2-to-20-ft gradient is
  worth.

This is the largest error in the game and the next pass that is not a page: it needs the landing to be a vector
scatter instead of a number.

**The wind and the aim.** The frozen player — the one that never practises — scores +14 a round aiming at the flag,
+10 aiming at the middle, and +15 aiming where the objective says (record pass 13). The objective's advice is good
advice for a player that has measured itself and bad advice for one that has not, because an unlearned player has a
2.2° hand bias and an unlearned crosswind and scatters about a point that is not where the objective thinks it is
aiming. **This is recorded, not repaired.**

**The putt has no height.** The hole is a painted ellipse. The ball arrives at it and stops; nothing drops into the
cup (record pass 16). It is the most satisfying frame in golf and it is missing.

**The putter has no read error.** Its read of the break is exact to a third of an inch, so its line error is one
constant 1.1° at every distance, where a real golfer misreads more the longer the putt. With the pace already
fixed, this game holes more putts than golf does from 6 ft out (README finding 10).

**The green has no contour.** One grade, one fall line, everywhere. No tiers, no swales, no two-break putts.

**There is no dogleg.** The corridor is straight and 40 yards wide, so the driver's distance has never been a
decision — it is always "hit it as far as you can". Geometry, not physics, and unbuilt.

**A bunker shot cannot plug, and a lie cannot be bad.** No plugged lies, no sitting down in the rough, no flyer.

**The field is one program's athletes, not six people.** Six strategies sharing one notebook's ancestry. Putting
six *members*' numbers on one board is something the members would have to do in their own windows, and nobody —
least of all the founder — can order it. The pages say this in their own footers.

**The rough's price is 0.3 of a stroke too dear.** Two instruments agree it is. It stays where pass 10 put it,
because a number re-measured and then checked against its own measurement is a fitted number.

**One count is typed rather than counted.** The season page's footer says "thirty-eight checks". It is true today
(`python3 lab/golf.py --selftest`). It will be false the next time a check is added, until someone edits the string.

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

    python3 lab/golf.py --selftest                 # 38 checks: the numbers everything else rests on
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
