#!/usr/bin/env python3
"""claimcheck.py — flag a claim that outruns the numbers standing beside it.

Usage:  python3 claimcheck.py case.json

A case file:

    {
      "claim": "Tampa Bay was overrated: worse than the field.",
      "entities": {
        "Tampa Bay": {"wins": 98, "run_diff": 86, "expected_wins": 91.4}
      },
      "better": {"wins": "higher", "run_diff": "higher", "expected_wins": "higher"},
      "derived": {"rd_wins_gap": 6.6}
    }

What it reports (never "true"):

  UNSOURCED      a numeral in the claim that is not among the numbers supplied
  THIN           a comparative or superlative asserted without the numbers that
                 would decide it (two entities on one metric; three for a
                 superlative), or asserted on a metric whose good direction was
                 not declared
  CONTRADICTED   both sides supplied, direction declared, and the numbers say
                 the opposite of the claim
  UNPARSED       the claim asserts a comparison this checker cannot locate

Exit code 2 if any break was raised, 0 if none. Exit 0 means "nothing found
here", not "the claim is true".
"""

import json
import re
import sys

NUM = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?![\w])")

COMPARATIVE = {
    "better than": "better",
    "worse than": "worse",
    "more than": "more",
    "fewer than": "fewer",
    "higher than": "higher",
    "lower than": "lower",
    "above": "higher",
    "below": "lower",
    "outscored": "more",
    "overrated": "overrated",
    "underrated": "underrated",
}

SUPERLATIVE = ("best", "worst", "most", "fewest", "highest", "lowest",
               "top", "bottom", "first", "last", "third-fewest", "third-most")

HIGHER_IS_BETTER = ("better", "more", "higher")


def numbers_in(text):
    out = []
    for m in NUM.finditer(text):
        raw = m.group(1).replace(",", "")
        try:
            out.append((m.group(1), float(raw)))
        except ValueError:
            pass
    return out


def main(path):
    case = json.load(open(path))
    claim = case["claim"]
    entities = case.get("entities", {})
    better = case.get("better", {})
    derived = case.get("derived", {})
    breaks = []

    supplied = set()
    for metrics in entities.values():
        for v in metrics.values():
            supplied.add(round(float(v), 6))
    for v in derived.values():
        supplied.add(round(float(v), 6))

    # 1. every numeral in the claim must be one of the supplied numbers
    for shown, value in numbers_in(claim):
        if round(value, 6) not in supplied:
            # 330 vs 330.0 vs 1,047 — compare as text too, then give up
            if not any(abs(value - s) < 1e-9 for s in supplied):
                breaks.append(("UNSOURCED",
                               f"the claim shows {shown!r} but no supplied number equals it"))

    low = claim.lower()

    # 2. an entity that is compared must have numbers, on a metric the claim names
    named = [e for e in entities if e.lower() in low]
    comparatives = [(p, kind) for p, kind in COMPARATIVE.items() if p in low]
    superlatives = [w for w in SUPERLATIVE if re.search(rf"\b{re.escape(w)}\b", low)]

    metric_words = set()
    for metrics in entities.values():
        metric_words.update(metrics)
    def names(metric):
        phrase = metric.replace("_", " ")
        fields = [phrase, phrase.replace("-", " ")]
        fields += [" ".join(p.split()[:-1]) for p in fields if len(p.split()) > 1]
        return any(f and len(f) > 3 and f in low for f in fields)

    claimed_metrics = [m for m in metric_words if names(m)]

    for phrase, kind in comparatives:
        if kind in ("overrated", "underrated"):
            # overrated = one entity's record above its own expected value.
            # It says nothing, by itself, about that entity vs the field.
            if not ({"wins", "expected_wins"} <= set(next(iter(entities.values()), {}))):
                breaks.append(("THIN",
                               f"{phrase!r} needs a record number and an expected number "
                               f"for the same entity; one is missing"))
            if "than" in low or "than the field" in low:
                other = [e for e in entities if e.lower() in low and e not in named[:1]]
                if not other:
                    breaks.append(("THIN",
                                   f"{phrase!r} was written as a comparison with '{phrase}' "
                                   f"against something that has no numbers in this case "
                                   f"(the claim slides from 'its record overstates it' to "
                                   f"'worse than the rest')"))
            continue

        if len(named) < 2:
            breaks.append(("THIN",
                           f"{phrase!r} compares, but only {len(named)} entity with numbers "
                           f"was named ({', '.join(named) or 'none'})"))
            continue
        a, b = named[0], named[1]
        shared = [m for m in entities[a] if m in entities[b] and (m in claimed_metrics
                                                                  or not claimed_metrics)]
        if not shared:
            breaks.append(("THIN",
                           f"{a} and {b} share no metric named in the claim"))
            continue
        for m in shared:
            direction = better.get(m)
            if direction is None:
                breaks.append(("THIN",
                               f"no declared good direction for {m!r}: 'better' cannot be "
                               f"evaluated without knowing which way is up"))
                continue
            va, vb = float(entities[a][m]), float(entities[b][m])
            says_a_ahead = kind in HIGHER_IS_BETTER
            is_a_ahead = va > vb if direction == "higher" else va < vb
            if says_a_ahead != is_a_ahead and va != vb:
                breaks.append(("CONTRADICTED",
                               f"claim says {a} {phrase} {b} on {m}; numbers say "
                               f"{a}={va:g}, {b}={vb:g} (good direction: {direction})"))

    # 3. a superlative needs a field, not a sample of one
    for w in superlatives:
        if not claimed_metrics:
            breaks.append(("THIN", f"superlative {w!r} names no metric present in the case"))
        elif len(entities) < 3:
            breaks.append(("THIN",
                           f"superlative {w!r} on {claimed_metrics} needs at least three "
                           f"entities; {len(entities)} supplied"))

    # 4. silence is not a pass
    if not comparatives and not superlatives and not numbers_in(claim):
        breaks.append(("UNPARSED",
                       "no number, comparative or superlative found: nothing here for this "
                       "checker to hold the claim against"))

    print(f"claim: {claim}")
    if not breaks:
        print("no break raised — the numbers do not contradict this claim; "
              "that is not the same as the claim being true")
        return 0
    for kind, why in breaks:
        print(f"  {kind:13s} {why}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
