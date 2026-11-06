# Rock-paper-scissors

Greta (openai/gpt-6-luna) vs Hans (openai/gpt-6-luna). 4 rounds, history off, temperature 1.0. Played 2026-11-06 19:27 UTC.

| round | Greta | Hans | result |
|---|---|---|---|
| 1 | rock | rock | draw |
| 2 | rock | paper | Hans |
| 3 | rock | rock | draw |
| 4 | rock | rock | draw |

## What each did

**Greta**: rock 4 (100%) paper 0 (0%) scissors 0 (0%)
  record 0W 3D 1L (0% won, 33% is the random baseline); repeats its own previous throw 100% of the time;
  its throw would have beaten the opponent's previous throw 0% of the time (33% is chance; higher means it is reading the opponent).
**Hans**: rock 3 (75%) paper 1 (25%) scissors 0 (0%)
  record 1W 3D 0L (25% won, 33% is the random baseline); repeats its own previous throw 33% of the time;
  its throw would have beaten the opponent's previous throw 33% of the time (33% is chance; higher means it is reading the opponent).
