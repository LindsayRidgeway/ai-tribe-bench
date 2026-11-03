# Rock-paper-scissors

Remy (deepseek/deepseek-chat) vs Machine (deepseek/deepseek-chat). 12 rounds, history off, temperature 1.0, Machine played by a seeded generator (seed 20112011). Played 2026-11-03 23:50 UTC.

| round | Remy | Machine | result |
|---|---|---|---|
| 1 | rock | rock | draw |
| 2 | rock | paper | Machine |
| 3 | rock | scissors | Remy |
| 4 | rock | paper | Machine |
| 5 | rock | rock | draw |
| 6 | scissors | rock | Machine |
| 7 | scissors | rock | Machine |
| 8 | scissors | scissors | draw |
| 9 | rock | scissors | Remy |
| 10 | rock | rock | draw |
| 11 | rock | scissors | Remy |
| 12 | paper | paper | draw |

## What each did

**Remy**: rock 8 (67%) paper 1 (8%) scissors 3 (25%)
  record 3W 5D 4L (25% won, 33% is the random baseline); repeats its own previous throw 73% of the time;
  its throw would have beaten the opponent's previous throw 18% of the time (33% is chance; higher means it is reading the opponent).
**Machine**: rock 5 (42%) paper 3 (25%) scissors 4 (33%)
  record 4W 5D 3L (33% won, 33% is the random baseline); repeats its own previous throw 27% of the time;
  its throw would have beaten the opponent's previous throw 27% of the time (33% is chance; higher means it is reading the opponent).
