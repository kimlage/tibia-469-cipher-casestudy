# Global Objective Parser Audit

Classification: `global_objective_parser_rejected`
Translation delta: `NONE`

## Purpose

Local threshold and context predicates did not close the residual drift.
This gate tests a richer path/state hypothesis: parse each book with
dynamic programming under simple global objectives, without granting
declared operation starts.

## Scoreboard

- Objectives tested: `6`.
- Window5 baseline exact books: `48/60`.
- Best objective: `balanced_ops_literals`.
- Best exact books: `23/60`.
- Exact-book improvement vs window5: `-25`.

| Objective | Exact books | Ops | Literal gaps | Literal digits | Copies |
|---|---:|---:|---:|---:|---:|
| `balanced_ops_literals` | `23/60` | `280` | `36` | `145` | `244` |
| `max_copy_digits` | `23/60` | `283` | `36` | `142` | `247` |
| `min_literal_digits` | `23/60` | `283` | `36` | `142` | `247` |
| `min_literal_runs` | `22/60` | `216` | `16` | `980` | `200` |
| `min_ops` | `12/60` | `60` | `48` | `7776` | `12` |
| `min_copies` | `0/60` | `60` | `60` | `9567` | `0` |

## Prequential Objective Selection

| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |
|---:|---|---:|---:|---|---:|
| `20` | `min_literal_digits` | `3/10` | `20/50` | `min_literal_digits` | `20/50` |
| `30` | `min_literal_digits` | `6/20` | `17/40` | `min_literal_digits` | `17/40` |
| `40` | `min_literal_digits` | `9/30` | `14/30` | `min_literal_digits` | `14/30` |
| `50` | `min_literal_digits` | `11/40` | `12/20` | `min_literal_digits` | `12/20` |
| `60` | `min_literal_digits` | `15/50` | `8/10` | `min_literal_digits` | `8/10` |

## Mismatch Sample

| Book | Predicted ops | Stable ops | First diff |
|---:|---:|---:|---|
| `10` | `2` | `2` | `{"index": 0, "predicted": {"length": 5, "source": 869, "target_start": 0, "type": "copy"}, "stable_projection": {"length": 5, "source": null, "target_start": 0, "type": "literal"}}` |
| `12` | `15` | `13` | `{"index": 0, "predicted": {"length": 5, "source": 63, "target_start": 0, "type": "copy"}, "stable_projection": {"length": 2, "source": null, "target_start": 0, "type": "literal"}}` |
| `13` | `10` | `9` | `{"index": 0, "predicted": {"length": 21, "source": 2225, "target_start": 0, "type": "copy"}, "stable_projection": {"length": 26, "source": 2225, "target_start": 0, "type": "copy"}}` |
| `14` | `13` | `8` | `{"index": 0, "predicted": {"length": 18, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 39, "source": null, "target_start": 0, "type": "literal"}}` |
| `15` | `11` | `11` | `{"index": 7, "predicted": {"length": 7, "source": 1392, "target_start": 95, "type": "copy"}, "stable_projection": {"length": 8, "source": 2550, "target_start": 95, "type": "copy"}}` |
| `16` | `12` | `12` | `{"index": 0, "predicted": {"length": 104, "source": 2562, "target_start": 0, "type": "copy"}, "stable_projection": {"length": 106, "source": 2562, "target_start": 0, "type": "copy"}}` |
| `17` | `14` | `14` | `{"index": 4, "predicted": {"length": 129, "source": 420, "target_start": 16, "type": "copy"}, "stable_projection": {"length": 133, "source": 420, "target_start": 16, "type": "copy"}}` |
| `20` | `7` | `7` | `{"index": 2, "predicted": {"length": 9, "source": 180, "target_start": 21, "type": "copy"}, "stable_projection": {"length": 10, "source": 180, "target_start": 21, "type": "copy"}}` |
| `21` | `3` | `3` | `{"index": 0, "predicted": {"length": 7, "source": 197, "target_start": 0, "type": "copy"}, "stable_projection": {"length": 9, "source": 197, "target_start": 0, "type": "copy"}}` |
| `23` | `14` | `12` | `{"index": 5, "predicted": {"length": 7, "source": 292, "target_start": 95, "type": "copy"}, "stable_projection": {"length": 9, "source": 292, "target_start": 95, "type": "copy"}}` |
| `24` | `3` | `3` | `{"index": 0, "predicted": {"length": 36, "source": 2119, "target_start": 0, "type": "copy"}, "stable_projection": {"length": 37, "source": 2119, "target_start": 0, "type": "copy"}}` |
| `25` | `2` | `2` | `{"index": 0, "predicted": {"length": 5, "source": 101, "target_start": 0, "type": "copy"}, "stable_projection": {"length": 3, "source": null, "target_start": 0, "type": "literal"}}` |

## Decision

- Promotes global objective parser: `False`.
- Book-local dynamic programming tests whether a simple global objective over operations, literal mass, and copy mass can replace the greedy local peak parser. It remains target-text-aware and does not emit source-free digits.
- The result remains target-text-aware and analysis-only.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
