# Integrated Online Literal Parser Audit

Classification: `integrated_online_literal_parser_partial_improvement_not_promoted`
Translation delta: `NONE`

## Purpose

Gate 06 scored an online literal-stop rule inside known literal gaps.
This gate freezes that rule and lets it parse each non-seed book
end-to-end, without granting declared literal windows or declared copy
starts.

## Parser

- Literal stop policy: `first_confirmed_max_copy_length_peak`.
- Confirm window: `6`.
- Copy policy: `longest_previous_target_match_earliest_source_tie`.
- Book order: `canonical_10_to_69_after_seed_books_0_to_9`.

## Result

- Exact books vs stable projection: `46/60`.
- Full greedy exact books: `39/60`.
- Delta vs full greedy: `7`.
- Predicted operations: `268` vs stable `262`.
- Predicted copy ops: `199` vs stable `208`.
- Predicted literal gaps: `69` vs stable `54`.
- Predicted literal digits: `329` vs stable `265`.

## Mismatch Sample

| Book | Predicted ops | Stable ops | First diff |
|---:|---:|---:|---|
| `14` | `12` | `8` | `{"index": 0, "predicted": {"length": 18, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 39, "source": null, "target_start": 0, "type": "literal"}}` |
| `16` | `10` | `12` | `{"index": 6, "predicted": {"length": 7, "source": null, "target_start": 144, "type": "literal"}, "stable_projection": {"length": 6, "source": 274, "target_start": 144, "type": "copy"}}` |
| `20` | `6` | `7` | `{"index": 1, "predicted": {"length": 9, "source": null, "target_start": 15, "type": "literal"}, "stable_projection": {"length": 6, "source": 190, "target_start": 15, "type": "copy"}}` |
| `21` | `3` | `3` | `{"index": 0, "predicted": {"length": 7, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 9, "source": 197, "target_start": 0, "type": "copy"}}` |
| `26` | `5` | `4` | `{"index": 0, "predicted": {"length": 1, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 11, "source": 3054, "target_start": 0, "type": "copy"}}` |
| `28` | `5` | `5` | `{"index": 1, "predicted": {"length": 6, "source": null, "target_start": 89, "type": "literal"}, "stable_projection": {"length": 7, "source": 2778, "target_start": 89, "type": "copy"}}` |
| `30` | `6` | `6` | `{"index": 1, "predicted": {"length": 6, "source": null, "target_start": 17, "type": "literal"}, "stable_projection": {"length": 6, "source": 255, "target_start": 17, "type": "copy"}}` |
| `34` | `8` | `9` | `{"index": 0, "predicted": {"length": 10, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 4, "source": null, "target_start": 0, "type": "literal"}}` |
| `36` | `6` | `6` | `{"index": 4, "predicted": {"length": 6, "source": null, "target_start": 78, "type": "literal"}, "stable_projection": {"length": 7, "source": 2327, "target_start": 78, "type": "copy"}}` |
| `39` | `2` | `3` | `{"index": 0, "predicted": {"length": 7, "source": null, "target_start": 0, "type": "literal"}, "stable_projection": {"length": 5, "source": 2520, "target_start": 0, "type": "copy"}}` |
| `45` | `4` | `3` | `{"index": 1, "predicted": {"length": 1, "source": null, "target_start": 62, "type": "literal"}, "stable_projection": {"length": 8, "source": 2850, "target_start": 62, "type": "copy"}}` |
| `55` | `4` | `4` | `{"index": 2, "predicted": {"length": 45, "source": 2757, "target_start": 67, "type": "copy"}, "stable_projection": {"length": 44, "source": 2757, "target_start": 67, "type": "copy"}}` |

## Decision

- The frozen online literal stop rule is tested as an executable parser rather than inside declared literal windows. Any mismatch means the local stop rule drifts when it must choose subsequent operation starts itself.
- Integrated parser status: `integrated_online_literal_parser_partial_improvement_not_promoted`.
- The result remains target-text-aware and analysis-only.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
