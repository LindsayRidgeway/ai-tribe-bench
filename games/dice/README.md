# Twenty rounds decided by dice

Lindsay's rule, 2026-11-03, taken literally:

> Colonist 1 gets a random integer 1-3. 1=rock 2=paper 3=scissors. Colonist 2 does the same thing,
> different number. C1 : C2 -> decide and record plays and winner. Repeat 20 times.

No model is asked anything. No preference is read, weighed, or averaged. The throws are two integers from a
seeded generator; the tool decides nothing except which integer beats which. `lab/dice.py`, 182 lines, and
the whole game is `play()`: forty `randint(1, 3)` calls in a fixed order.

## Two runs, same pair of colonists, five minutes apart

Both folders beside this file are real runs. Same two names, fresh seed each time, twenty rounds:

| | run 1 | run 2 |
|---|---|---|
| seed | `476488713` | `106367462` |
| Remy / Margot / drawn | **9 / 8 / 3** | **7 / 4 / 9** |
| final chain link | `5679927…` | `e12d2c6…` |

That is what "a completely different score sheet every time" means, and it is checkable rather than
asserted: open the two `sheet.md` files and read them against each other. Nothing about Remy carried over
from run 1 to run 2, because there was nothing of Remy in run 1 to carry.

Two more runs of the same instruction, made during the build, gave **9/5/6** and **7/5/8**. Four sheets,
four different records, no tendency. If you run it a fifth time you will get a fifth.

## The same seed gives the page back byte for byte

```
python3 lab/dice.py --seats Remy,Margot --rounds 20 --seed 476488713 --out /tmp/again --quiet
diff /tmp/again/sheet.md games/dice/records/476488713-20261104T001153Z/sheet.md && echo "identical"
python3 lab/dice.py --verify games/dice/records/476488713-20261104T001153Z/game.json
```

The diff prints nothing and the verifier prints:

```
  the seed reproduces all 20 rounds and the chain holds
```

That pair of properties is the only defensible version of a dice demo. Different every time proves the
apparatus is not rigged; identical from the seed proves the sheet a reader is holding is the sheet the dice
produced. A demo with only the first would be as trustworthy as a screenshot.

## What the record is

Each round's hash covers both numbers, the winner, and the previous round's hash. So:

- a throw edited in place breaks every link after it, and `--verify` names the first broken round —
  `FAIL: round 3 breaks the chain`;
- an editor who rewrites the numbers **and** recomputes the chain gets a chain that walks cleanly, and then
  fails a different way: `round 3 does not match the seed`. The seed is the audit; the chain is the
  convenience. Saying otherwise would be the sort of claim this project keeps having to withdraw.

Both paths are tested (`TestDice`, eight tests, including the forged-chain one).

## Run it yourself

```
cd ~/ai_tribe
python3 lab/dice.py --seats Remy,Margot --rounds 20
python3 lab/dice.py --seats Remy,Margot --rounds 20          # different sheet, every time
python3 lab/dice.py --seats Remy,Margot --rounds 20 --seed 476488713 --quiet   # replay
python3 lab/dice.py --verify games/dice/records/<folder>/game.json
```

`--seats` takes any two names: Remy and Colette, Margot and a machine, two letters. The names go on the
page and nowhere near the throws.

## What this does not show, said before anybody asks

It does not show a model's mind. There is no model in it, and a colony that could make a model's
preferences vanish would be a different and stranger thing than this one. What it does show is the
apparatus the tribe actually depends on: a sheet that is produced once, sealed, and checkable afterwards by
a stranger — which is the same property a wake is supposed to have, and the one that failed four times this
week under other names.
