# Seed Primacy Integration Audit

Classification: `seed_primacy_integrated_audit_only_compression`
Translation delta: `NONE`

## Purpose

This bridge integrates the final seed-primacy front into the main
prequential/row0 audit. It treats the seed work as a narrow exact-copy
coverage test, not as translation, plaintext, authorial intent, or row0
origin evidence.

## Decision

- Seed front status: `AUDIT_ONLY_COMPRESSION`.
- Operational books `0..9` are not mechanically privileged seeds under the tested controls.
- Posthoc high-coverage seed sets are compression clues only.
- Prefix-trained seed selection has partial predictive signal, but is not promoted.
- `row0 unchanged`; compression bound remains `8154.676268` bits.

## Operational Seed Check

| Seed set | Copied digits | Target digits | Coverage | Random percentile | Gain vs random median after declaration | Status |
|---|---:|---:|---:|---:|---:|---|
| `0..9` | `8664` | `9567` | `0.905613` | `0.21` | `-1132.777` | `not_promoted` |

## Posthoc Core

- Best k=10 posthoc greedy seed: `[7, 8, 9, 13, 17, 20, 25, 39, 54, 67]`.
- Copied digits: `9734` / `9981`.
- Coverage: `0.975253`.
- Search class: `posthoc_greedy_coverage`.
- Boundary: selected after seeing the corpus, so it is not an authorial seed claim.

## Prequential Check

- Evaluated prefix/k cells: `7`.
- Train-greedy beats random median: `7/7`.
- Train-greedy beats random p95: `6/7`.
- Operational prefix beats random median: `1/7`.
- Mean train-greedy vs suffix-oracle gap: `0.016640`.
- Max train-greedy vs suffix-oracle gap: `0.028849`.
- Promotes prequential seed generator: `False`.

## Taxonomy

| Bucket | Result |
|---|---|
| `PROMOTED_MECHANICAL_SEED_CLUE` | none |
| `WEAK_SEED_CLUE` | none |
| `REJECTED_SEED_HYPOTHESIS` | operational `0..9` seed primacy |
| `AUDIT_ONLY_COMPRESSION` | posthoc high-coverage cores; partial prequential seed-selection signal |
| `BLOCKED_NEEDS_EXTERNAL_SOURCE` | authorial seed claim |

## Boundary

This integration adds no plaintext, translation, semantic reading, row0
origin formula, or new compression bound. Better exact-copy seed coverage
is recorded as corpus redundancy evidence only.
