# Digit-Address Literal Repair Search

Verdict: `controlled_digit_address_literal_repair_improvement`. Translation delta: `NONE`.

This audit retests one-step literal-to-copy repairs after the formula
moved to digit-only copy addresses. The current recipe is used as the
baseline, and each candidate is rescored with adaptive literal payload
coding and digit-only absolute copy-address cost.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `9070.8` |
| Candidates tested | `24` |
| Best candidate bits | `9070.1` |
| Best candidate delta | `-0.8` |

## Best Candidate

| Book | Literal offset | Chunk | Source digit pos | Length | Delta |
|---:|---:|---|---:|---:|---:|
| `13` | `6` | `57928` | `1976` | `5` | `-0.8` |

## Follow-Up Check

After applying the best repair, `23` further one-step
candidates were tested. The best follow-up candidate is not cheaper:

| Book | Chunk | Delta vs repaired |
|---:|---|---:|
| `12` | `65128` | `0.9` |

## Interpretation

A candidate is promoted only if exact rescoring beats the active
digit-address formula. A non-promoted best candidate remains useful
as a local frontier audit, not as progress.

## Boundary

This is a mechanical recipe audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
