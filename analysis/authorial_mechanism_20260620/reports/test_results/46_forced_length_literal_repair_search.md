# Forced-Length Literal Repair Search

Verdict: `controlled_forced_length_literal_repair_improvement`. Translation delta: `NONE`.

This audit retests one-step literal-to-copy repairs after the formula
added forced suffix literal lengths. Each candidate is rescored with
the full active model: adaptive literal payload, forced literal lengths,
digit-only absolute copy addresses, copy length coding, and the
book-start Markov item-type stream with deterministic type rules.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8922.9` |
| Candidates tested | `23` |
| Best candidate bits | `8922.8` |
| Best candidate delta | `-0.1` |

## Best Candidate

| Book | Literal offset | Chunk | Source digit pos | Length | Delta |
|---:|---:|---|---:|---:|---:|
| `12` | `2` | `65128` | `50` | `5` | `-0.1` |

## Follow-Up Check

After applying the best repair, `22` further one-step
candidates were tested. The best follow-up candidate is not cheaper:

| Book | Chunk | Delta vs repaired |
|---:|---|---:|
| `2` | `18003` | `0.7` |

## Interpretation

A candidate is promoted only if exact rescoring beats the active
forced-literal-length formula. A non-promoted best candidate remains
a local frontier audit, not semantic progress.

## Boundary

This is a mechanical recipe audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
