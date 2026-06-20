# Literal Reference Formula Compile

Verdict: `candidate_literal_reference_formula`. Translation delta: `NONE`.

This pass compiles a candidate improvement over the tape formula by
replacing remaining literal strings with references into existing tape
components when the reference address is cheaper than storing digits.

| Metric | Value |
|---|---:|
| Per-reference bits | `21` |
| Reference items | `36` |
| Referenced literal digits | `579` |
| Kept literal items | `67` |
| Kept literal digits | `1397` |
| Rough saved bits | `1167.4` |
| Book roundtrip | `70/70` |

## Boundary

This is a mechanical reference-layer improvement only. It does not explain
the pair table, does not add source authority, and does not translate any
book.
