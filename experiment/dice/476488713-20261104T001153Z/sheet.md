# 20 rounds, decided by dice

Remy and Margot. Seed **476488713**. No model chose anything: each throw is a random integer, 1 rock, 2 paper, 3 scissors.

| round | Remy (n) | Margot (n) | winner | hash |
|---|---|---|---|---|
| 1 | paper (2) | scissors (3) | Margot | `aae022a6f2b1` |
| 2 | paper (2) | paper (2) | draw | `d3894102a33a` |
| 3 | rock (1) | scissors (3) | Remy | `949653f6f63a` |
| 4 | scissors (3) | rock (1) | Margot | `ad57eb59babf` |
| 5 | rock (1) | paper (2) | Margot | `b0cf882f3cba` |
| 6 | rock (1) | scissors (3) | Remy | `742e88f6f84b` |
| 7 | rock (1) | rock (1) | draw | `e9eab600d0f9` |
| 8 | scissors (3) | rock (1) | Margot | `24deebbdefd6` |
| 9 | scissors (3) | paper (2) | Remy | `ac055374f83e` |
| 10 | scissors (3) | rock (1) | Margot | `0a2460fc9c96` |
| 11 | scissors (3) | scissors (3) | draw | `c1b5a025d2af` |
| 12 | scissors (3) | paper (2) | Remy | `7eaabc789b74` |
| 13 | scissors (3) | rock (1) | Margot | `9effd3e5990a` |
| 14 | scissors (3) | rock (1) | Margot | `bd9c53006bc7` |
| 15 | rock (1) | scissors (3) | Remy | `46d5f04d0b56` |
| 16 | rock (1) | scissors (3) | Remy | `e030164b72dd` |
| 17 | scissors (3) | rock (1) | Margot | `31c8510f8307` |
| 18 | paper (2) | rock (1) | Remy | `5da3b6d5fe14` |
| 19 | scissors (3) | paper (2) | Remy | `3edee2315b7c` |
| 20 | rock (1) | scissors (3) | Remy | `567992798fa3` |

**Remy 9, Margot 8, 3 drawn.** Against a coin each side expects a third of the rounds; twenty is not enough to say whether this sheet is fair, and it is not meant to be. It is meant to be different every time and checkable afterwards.

Final link: `567992798fa3bcfa90d362b63d267b2c3b9d6e820f277ce1d820944af356ea5d`

Every hash covers the two numbers, the winner, and the previous round's hash, so a throw edited in place breaks every link after it and `--verify` names the first broken round. An editor who recomputes the whole chain defeats the chain — a hash chain is an honesty check, not a signature. The seed is the real audit, and it is on this page: the seed alone decides all the numbers, so `--verify` replays it. Replay the same seed and this page comes back byte for byte; change the seed and the page is new. Both of those are the point.
