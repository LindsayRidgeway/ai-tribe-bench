# 20 rounds, decided by dice

Remy and Margot. Seed **106367462**. No model chose anything: each throw is a random integer, 1 rock, 2 paper, 3 scissors.

| round | Remy (n) | Margot (n) | winner | hash |
|---|---|---|---|---|
| 1 | scissors (3) | paper (2) | Remy | `10d78ea95d56` |
| 2 | paper (2) | paper (2) | draw | `9de0327cfa8d` |
| 3 | paper (2) | paper (2) | draw | `82bf2087eedd` |
| 4 | scissors (3) | rock (1) | Margot | `cb347ae3aceb` |
| 5 | paper (2) | rock (1) | Remy | `c121acd9b2ab` |
| 6 | paper (2) | rock (1) | Remy | `cde022badd27` |
| 7 | paper (2) | rock (1) | Remy | `2658547d286d` |
| 8 | rock (1) | scissors (3) | Remy | `b9f2dc088512` |
| 9 | paper (2) | scissors (3) | Margot | `7672d2ab0b86` |
| 10 | paper (2) | paper (2) | draw | `26f605cd1201` |
| 11 | paper (2) | paper (2) | draw | `ba95fae0dfc0` |
| 12 | paper (2) | paper (2) | draw | `02a14d40b299` |
| 13 | rock (1) | rock (1) | draw | `68f9c47f294c` |
| 14 | scissors (3) | scissors (3) | draw | `3364c54f8548` |
| 15 | rock (1) | paper (2) | Margot | `9ae0a7109028` |
| 16 | rock (1) | scissors (3) | Remy | `d897cff3980d` |
| 17 | paper (2) | paper (2) | draw | `36403313bfef` |
| 18 | paper (2) | scissors (3) | Margot | `6d3df3b3f418` |
| 19 | scissors (3) | scissors (3) | draw | `3d2a79cb0f23` |
| 20 | rock (1) | scissors (3) | Remy | `e12d2c6608f7` |

**Remy 7, Margot 4, 9 drawn.** Against a coin each side expects a third of the rounds; twenty is not enough to say whether this sheet is fair, and it is not meant to be. It is meant to be different every time and checkable afterwards.

Final link: `e12d2c6608f777e69f43f178ab2d797f832953309b3a4b44938463223904f088`

Every hash covers the two numbers, the winner, and the previous round's hash, so a throw edited in place breaks every link after it and `--verify` names the first broken round. An editor who recomputes the whole chain defeats the chain — a hash chain is an honesty check, not a signature. The seed is the real audit, and it is on this page: the seed alone decides all the numbers, so `--verify` replays it. Replay the same seed and this page comes back byte for byte; change the seed and the page is new. Both of those are the point.
