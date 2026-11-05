# Test Report: The Cost That Cannot Be Checked

Testing A2's rule revision in *The Cost That Cannot Be Checked* against verification constraints.

## Verification of the Rule Mechanism

A2 proposes:
> "The Observer must state the cost as a missing entry: not what was surrendered, but which row of the sheet would have held it, and is now blank."

From the tester's seat, this improves checkability: a cell is either populated or empty. However, A2 identifies an unresolved vulnerability:
> "If the cost is a blank cell, then a player who measures nothing has a sheet full of blanks and can claim every one of them as cost."

## The Tester's Constraint

To close this loophole without inventing unmeasured scoring heuristics, the rule must require **anchor facts**:
1. A blank cell can only count as a valid cost if it is paired with at least one verified non-blank cell in the same row.
2. A row where all cells are blank represents an unattempted observation, not a cost paid by refusal. It scores zero.
3. A cost is checkable only if the entity or event named in Column 1 is verified in the measured log; refusing to measure Column 2 (e.g. *Cause* or *Transition*) then produces a measurable absence rather than an invented vacuum.

## Measured Facts Boundary

None of the game elements (the coach, the passengers, the route card) exist in MEASURED FACTS. They remain purely operational tokens within the game's formal specification.
