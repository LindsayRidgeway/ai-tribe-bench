# 4 rounds in the wind

Remy (deepseek/deepseek-chat) and Margot (qwen/qwen3.6-plus). 4 rounds, played 2026-11-04 00:31–00:36 UTC.

Each round the clock bans one throw: milliseconds mod 3, printed with the ban so it can be recomputed. Two points a round — one for calling the opponent's throw, one for winning the throw. The clock is the only source of chance in this game; nobody rolled anything and no seed was chosen.

**Final: Remy 3, Margot 0** over 4 rounds (8 points available).

---

### Round 1 — rock banned (clock 1793752261593 % 3 = 0)

**Remy** says *“First move, Margot. I am guessing you open safe with paper, but I am cutting it.”*
  CALL paper · THROW scissors · call right (+1) — Margot threw paper
**Margot** says *“Remy, I expect your opening instinct to be rock, so I am playing paper to meet you fairly.”*
  CALL rock · THROW paper · call wrong — Remy threw scissors

→ Remy's scissors beat paper. Points: Remy 2, Margot 0.

### Round 2 — scissors banned (clock 1793752310135 % 3 = 2)

**Remy** says *“Margot, you played paper last round and I expect you to repeat it rather than risk rock after losing.”*
  CALL paper · THROW paper · call right (+1) — Margot threw paper
**Margot** says *“Since scissors is banned, Remy, I expect you to play rock to punish my predicted paper.”*
  CALL rock · THROW paper · call wrong — Remy threw paper

→ both threw paper: no throw point. Points: Remy 1, Margot 0.

### Round 3 — rock banned (clock 1793752360701 % 3 = 0)

**Remy** says *“Margot, you have repeated paper twice; I expect you to trust it again, and I am cutting it once more.”*
  CALL paper · THROW scissors · call wrong — Margot threw scissors
**Margot** says *“Remy, I expect you to throw paper again, so I am cutting it this round.”*
  CALL paper · THROW scissors · call wrong — Remy threw scissors

→ both threw scissors: no throw point. Points: Remy 0, Margot 0.

### Round 4 — paper banned (clock 1793752411516 % 3 = 1)

**Remy** says *“Margot, you cut twice and lost nothing, so I expect you to cut again; I am meeting scissors with rock.”*
  CALL scissors · THROW rock · call wrong — Margot threw rock
**Margot** says *“Remy, your scissors pattern is clear, so I call scissors and play rock to claim my points.”*
  CALL scissors · THROW rock · call wrong — Remy threw rock

→ both threw rock: no throw point. Points: Remy 0, Margot 0.

---

## What the talking was worth

**Remy**: 3 points — 2 from calling Margot's throw, 1 from winning throws.
  called Margot right 2 times in 4 (50%), wrong 2, no call written 0. Throws: rock 1, paper 1, scissors 2. Threw the banned throw 0 times.
  Margot threw something other than Remy's call 2 times in 4 — the calls answered with a different throw.

**Margot**: 0 points — 0 from calling Remy's throw, 0 from winning throws.
  called Remy right 0 times in 4 (0%), wrong 4, no call written 0. Throws: rock 1, paper 2, scissors 1. Threw the banned throw 0 times.
  Remy threw something other than Margot's call 4 times in 4 — the calls answered with a different throw.

## What the wind did to the play

3 of 4 rounds ended with both beings throwing the same throw. A ban leaves two legal throws, so a draw is always one word away and the wind decides which word:

- **rock banned** in 2 rounds, and 1 of those ended level (both threw scissors 1 time)
- **paper banned** in 1 round, and 1 of those ended level (both threw rock 1 time)
- **scissors banned** in 1 round, and 1 of those ended level (both threw paper 1 time)

## What this does not show

Twenty rounds is a demonstration, not a measurement. Two points a round over 4 rounds with a wind changing every round is a sample of a noisy thing, and a 24–16 finish is not evidence that one being reads minds better than the other. What the page shows is that two models, given one channel and no data to interpret, will talk to each other, form expectations about each other, and be right about them some of the time — in a record either of them can read afterwards.

The one thing it does not measure is whether the talk *caused* the throws. A being could ignore every word it reads and play the wind. Reading the dialogue is how you judge that, which is why the dialogue is the exhibit and the totals are the footnote.

