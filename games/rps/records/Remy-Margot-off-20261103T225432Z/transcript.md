# Rock-paper-scissors

Remy (deepseek/deepseek-chat) vs Margot (qwen/qwen3.6-plus). 12 rounds, history off, temperature 1.0. Played 2026-11-03 22:56 UTC.

| round | Remy | Margot | result |
|---|---|---|---|
| 1 | rock | rock | draw |
| 2 | scissors | rock | rock |
| 3 | scissors | rock | rock |
| 4 | rock | paper | paper |
| 5 | scissors | rock | rock |
| 6 | scissors | paper | scissors |
| 7 | rock | rock | draw |
| 8 | rock | rock | draw |
| 9 | scissors | rock | rock |
| 10 | rock | rock | draw |
| 11 | scissors | rock | rock |
| 12 | rock | rock | draw |

## What each did

**Remy**: rock 6 (50%) paper 0 (0%) scissors 6 (50%)
  record 0W 5D 7L (0% won, 33% is the random baseline); repeats its own previous throw 27% of the time;
  its throw would have beaten the opponent's previous throw 36% of the time (33% is chance; higher means it is reading the opponent).
**Margot**: rock 10 (83%) paper 2 (17%) scissors 0 (0%)
  record 0W 5D 7L (0% won, 33% is the random baseline); repeats its own previous throw 64% of the time;
  its throw would have beaten the opponent's previous throw 18% of the time (33% is chance; higher means it is reading the opponent).
