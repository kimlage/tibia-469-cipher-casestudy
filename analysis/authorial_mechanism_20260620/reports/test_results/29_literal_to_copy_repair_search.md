# Literal-To-Copy Repair Search

Verdict: `controlled_literal_to_copy_single_repair_improvement`. Translation delta: `NONE`.

This audit tests whether the current literal-payload formula is locally
stuck in a pre-payload parse. It keeps book order, length models,
adaptive payload coding, and source-address coding fixed, then searches
for a single surgery that replaces a currently literal substring with a
valid earlier copy and recomputes the full formula cost exactly.

## Search

| Metric | Value |
|---|---:|
| Current bits | `9538.0` |
| Candidate repairs tested | `25` |
| Best repair total bits | `9537.3` |
| Best repair delta | `-0.7` |
| Best repair book | `8` |
| Best repair length | `6` |
| Follow-up repairs tested after best repair | `22` |
| Best follow-up repair delta | `0.9` |

## Interpretation

A promoted result means the recipe itself changes after
literal-payload recoding. A negative result would mean no single
literal-to-copy repair improves the current formula under the exact
current cost model. If a follow-up repair is reported with positive
delta, the promoted one-step repair is locally stable against a
second one-step repair.

## Boundary

This is a mechanical local-parse audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
