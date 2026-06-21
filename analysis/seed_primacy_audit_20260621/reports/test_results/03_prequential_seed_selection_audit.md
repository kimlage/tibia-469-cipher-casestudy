# Prequential Seed Selection Audit

Classification: `prequential_seed_selection_not_promoted`
Translation delta: `NONE`

## Purpose

The seed coverage audit found high-coverage seed sets only posthoc. This
audit asks whether seeds selected using only prefix books predict future
suffix coverage without retuning on the test books.

## Result

- Evaluated prefix/k cells: `7`.
- Train-greedy beats random median cells: `7`.
- Train-greedy beats random p95 cells: `6`.
- Operational prefix beats random median cells: `1`.
- Mean train-greedy vs suffix-oracle coverage gap: `0.016640`.
- Max train-greedy vs suffix-oracle coverage gap: `0.028849`.
- Promotes prequential seed generator: `False`.

## Cells

| cutoff | k | train-greedy seed | train-greedy coverage | random median coverage | train percentile | suffix-oracle coverage | operational coverage |
|---:|---:|---|---:|---:|---:|---:|---:|
| 10 | 5 | `[1, 3, 7, 8, 9]` | 0.871224 | 0.811853 | 0.965 | 0.900073 | 0.812794 |
| 20 | 5 | `[7, 8, 9, 17, 18]` | 0.958233 | 0.814259 | 1.000 | 0.975016 | 0.805804 |
| 20 | 10 | `[1, 4, 7, 8, 9, 13, 14, 17, 18, 19]` | 0.975268 | 0.942587 | 0.920 | 0.987003 | 0.902965 |
| 35 | 5 | `[8, 9, 17, 20, 25]` | 0.959040 | 0.801028 | 0.995 | 0.978578 | 0.775835 |
| 35 | 10 | `[1, 7, 8, 9, 12, 13, 17, 18, 20, 25]` | 0.978749 | 0.907284 | 0.975 | 0.989374 | 0.889289 |
| 50 | 5 | `[8, 9, 17, 20, 25]` | 0.962740 | 0.791201 | 1.000 | 0.980224 | 0.778447 |
| 50 | 10 | `[7, 8, 9, 17, 18, 20, 25, 38, 39, 49]` | 0.979650 | 0.909860 | 0.980 | 0.991115 | 0.880768 |

## Decision

- Seed sets selected only from the prefix do not close the posthoc gap. The train-greedy seeds can beat random controls in some splits, but they do not consistently beat p95 random train seeds and remain behind suffix-oracle seeds selected after seeing the future books. Seed selection therefore stays audit-only rather than a generative mechanism.
- Suffix-oracle seeds are posthoc controls only.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
