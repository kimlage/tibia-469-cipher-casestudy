# Final Seed Primacy Audit

Date: 2026-06-21

Classification: `AUDIT_ONLY_COMPRESSION`
Translation delta: `NONE`
Case reopened: `False`
Plaintext claim: `False`

## Question

This front tests whether a small subset of books behaves like a mechanical seed
for the remaining 469 corpus. It does not test translation, plaintext, fan
glosses, or authorial intent.

The tested mechanism is deliberately narrow: declare a seed set, then cover
non-seed books by exact copies of length at least 5 from the seed books, plus
literal residual digits. Copying from a target book, copying from derived books,
and copying across seed-book boundaries are disabled.

## Inputs

- Seed coverage audit: [analysis/seed_primacy_audit_20260621/reports/test_results/01_seed_coverage_audit.md](test_results/01_seed_coverage_audit.md).
- Books: `analysis/audit_20260609/books_digits.json`.
- Existing source-free skeleton ledger: `analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/99_exact_skeleton_dependency_ledger.json`.

## Main Result

| Test | Seed books | Copied digits | Literal digits | Copies | Coverage | Random percentile |
|---|---|---:|---:|---:|---:|---:|
| Operational 0-9 | `[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]` | 8664 | 903 | 397 | 90.56% | 0.21 |
| Best k=10 posthoc greedy | `[7, 8, 9, 13, 17, 20, 25, 39, 54, 67]` | 9734 | 247 | 388 | 97.53% | 1.00 |
| Random k=10 median | `100 sampled sets` | 9005 | n/a | n/a | 93.40% | n/a |
| Permuted-prefix k=10 median | `100 sampled orders` | 8978 | n/a | n/a | 93.35% | n/a |

The operational seed `0-9` covers fewer copied digits than the sampled random
k=10 median (`8664` vs `9005`)
and sits at random percentile `0.21`.
That is not evidence that `0-9` are mechanically special as seeds.

The best k=10 candidate found by posthoc greedy coverage is much stronger,
but it is selected after seeing the corpus: `[7, 8, 9, 13, 17, 20, 25, 39, 54, 67]`.
It is therefore an audit-only compression result, not a primary-origin claim.

## Prequential Seed Selection

- Prequential seed selection audit: [analysis/seed_primacy_audit_20260621/reports/test_results/03_prequential_seed_selection_audit.md](test_results/03_prequential_seed_selection_audit.md).
- Evaluated prefix/k cells: `7`.
- Train-greedy beats random median cells: `7`.
- Train-greedy beats random p95 cells: `6`.
- Operational prefix beats random median cells: `1`.
- Mean train-greedy vs suffix-oracle coverage gap: `0.016640`.
- Max train-greedy vs suffix-oracle coverage gap: `0.028849`.
- Promotes prequential seed generator: `False`.

Prefix-trained seeds show partial predictive signal, but they do not close
the posthoc gap: they fail the random-p95 condition in one evaluated cell
and remain behind suffix-oracle seeds selected after seeing the future books.

## Seed Size Sweep

| k | Best label | Seed books | Copied | Literal | Copies | Coverage | Gain vs random median after declaration |
|---:|---|---|---:|---:|---:|---:|---:|
| 5 | `greedy_coverage` | `[8, 9, 13, 17, 25]` | 10011 | 353 | 459 | 96.59% | 5172.242 |
| 10 | `greedy_coverage` | `[7, 8, 9, 13, 17, 20, 25, 39, 54, 67]` | 9734 | 247 | 388 | 97.53% | 2421.686 |
| 15 | `greedy_coverage` | `[1, 7, 8, 9, 12, 13, 17, 18, 20, 25, 39, 49, 54, 55, 67]` | 9328 | 100 | 279 | 98.94% | 2728.964 |
| 20 | `greedy_coverage` | `[1, 7, 8, 9, 12, 13, 14, 17, 18, 20, 24, 25, 27, 34, 39, 49, 54, 55, 63, 67]` | 8721 | 82 | 252 | 99.07% | 2913.331 |

The sweep finds small high-coverage subsets, especially greedy sets containing
books such as `7`, `8`, `9`, `13`, `17`, and `25`. This is a mechanical
coverage clue about redundancy in the corpus, but it is not evidence that
those books are authorial seeds. The selected sets are posthoc and still
leave copy-source choices and literal payload external.

## Required Controls

- Random same-size seeds: run for k = `[5, 10, 15, 20]`.
- Permuted order prefixes: run for k = `[5, 10, 15, 20]`.
- Seed declaration cost: charged as `log2(C(70,k))` in the payload-gain ledger.
- Copy-source dependency: retained as `copy_items_required`; not treated as solved.
- Public bookcase metadata: tested as a prefix control where available; it did not beat the posthoc greedy sets.
- Leave-one-family/bookcase controls: emitted as `family_holdout_controls` in the JSON, classified control-only.

## Categories

- `PROMOTED_MECHANICAL_SEED_CLUE`: not reached.
- `WEAK_SEED_CLUE`: not reached for `0-9` under this seed-only control.
- `REJECTED_SEED_HYPOTHESIS`: not used as the global label because posthoc high-coverage cores do exist.
- `AUDIT_ONLY_COMPRESSION`: reached; this is the final classification.
- `BLOCKED_NEEDS_EXTERNAL_SOURCE`: applies to any authorial seed claim.

## Answers

1. Books `0-9` special as seed: `False`.
2. Alternative k=10 seed better: `True`; best found is `[7, 8, 9, 13, 17, 20, 25, 39, 54, 67]`.
3. Gain over random after declaration for operational `0-9`: `False`.
4. Mechanical primary-core signal: `not_promoted_posthoc_alternatives_exist`.
5. Authorial seed claim: `BLOCKED_NEEDS_EXTERNAL_SOURCE`.
6. Translation/plaintext impact: `NONE`.

## Boundary

- No plaintext, translation, semantic reading, or fan gloss is introduced.
- `row0` remains exogenous and unchanged.
- Better coverage is not treated as origin.
- Seed mechanical, authorial seed, compressibility, and generative explanation remain separate.
- Any wiki update must keep this as an audit-only compression boundary, not a promoted validated origin/generation claim.
