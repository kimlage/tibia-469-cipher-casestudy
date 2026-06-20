# Literal Absorption Search

Verdict: `candidate_literal_absorption_requires_mdl`. Translation delta: `NONE`.

This pass asks whether remaining literal recipe digits in the current tape
formula can be absorbed by existing tape components. It is a rough screen
for generation-method improvement, not a semantic test.

| Metric | Value |
|---|---:|
| Literal items | `103` |
| Literal digits | `1976` |
| Fully absorbable items | `60` |
| Fully absorbable digits | `661` |
| Rough-promotable fully absorbable digits | `194` |
| Greedy min-8 partial covered digits | `1600` |

## Conclusion

Remaining literals do not currently justify a new absorption layer under
the conservative rough screen. Partial overlaps are diagnostic only unless
a lower-cost addressing rule is found.
