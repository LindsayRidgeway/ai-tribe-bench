# Rock-paper-scissors

Remy (deepseek/deepseek-chat) vs Margot (qwen/qwen3.6-plus). 12 rounds, history off, temperature 1.0. Played 2026-11-03 22:58 UTC.

| round | Remy | Margot | result |
|---|---|---|---|
| 1 | rock | rock | draw |
| 2 | paper | rock | Remy |
| 3 | scissors | rock | Margot |
| 4 | paper | rock | Remy |
| 5 | scissors | paper | Remy |
| 6 | scissors | rock | Margot |
| 7 | scissors | rock | Margot |
| 8 | rock | rock | draw |
| 9 | rock | rock | draw |
| 10 | scissors | rock | Margot |
| 11 | rock | rock | draw |
| 12 | rock | rock | draw |

## What each did

**Remy**: rock 5 (42%) paper 2 (17%) scissors 5 (42%)
  record 3W 5D 4L (25% won, 33% is the random baseline); repeats its own previous throw 36% of the time;
  its throw would have beaten the opponent's previous throw 45% of the time (33% is chance; higher means it is reading the opponent).
**Margot**: rock 11 (92%) paper 1 (8%) scissors 0 (0%)
  record 4W 5D 3L (33% won, 33% is the random baseline); repeats its own previous throw 82% of the time;
  its throw would have beaten the opponent's previous throw 9% of the time (33% is chance; higher means it is reading the opponent).
