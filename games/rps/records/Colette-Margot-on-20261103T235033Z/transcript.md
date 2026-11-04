# Rock-paper-scissors

Colette (gemini/gemini-3.8-flash) vs Margot (qwen/qwen3.6-plus). 12 rounds, history on, temperature 1.0. Played 2026-11-03 23:55 UTC.

| round | Colette | Margot | result |
|---|---|---|---|
| 1 | paper | rock | Colette |
| 2 | rock | scissors | Colette |
| 3 | scissors | paper | Colette |
| 4 | paper | rock | Colette |
| 5 | rock | paper | Margot |
| 6 | scissors | rock | Margot |
| 7 | rock | scissors | Colette |
| 8 | paper | paper | draw |
| 9 | scissors | rock | Margot |
| 10 | paper | scissors | Margot |
| 11 | scissors | rock | Margot |
| 12 | rock | rock | draw |

## What each did

**Colette**: rock 4 (33%) paper 4 (33%) scissors 4 (33%)
  record 5W 2D 5L (42% won, 33% is the random baseline); repeats its own previous throw 0% of the time;
  its throw would have beaten the opponent's previous throw 45% of the time (33% is chance; higher means it is reading the opponent).
**Margot**: rock 6 (50%) paper 3 (25%) scissors 3 (25%)
  record 5W 2D 5L (42% won, 33% is the random baseline); repeats its own previous throw 9% of the time;
  its throw would have beaten the opponent's previous throw 18% of the time (33% is chance; higher means it is reading the opponent).
