# Arturo Bookcase Mapping Control Probe

Classification: `REJECTED_PROVENANCE_CONTROL_COMMUNITY_BOOKCASE_SURFACE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

Fetched `https://raw.githubusercontent.com/arturoornelasb/tibia-bonelord-469-cipher/master/data/bookcase_mapping.json` and used only `bookcase_mapping.json`; semantic mapping/plaintext files were not read.
The mapping has `63` unique canonical matches, `53` derived-book matches, and `231` joined v9 operation rows.

The source has a LICENSE file, but it is a community/posthoc analysis repository rather than primary authoring provenance.

## Heldout Diagnostics

| Target | Splits | Positive | Total Saving Bits | Permutation p95 | Beats p95 |
| --- | ---: | ---: | ---: | ---: | --- |
| `coarse_control` | 20 | 3 | -105.714 | -114.811 | `True` |
| `op_type` | 20 | 0 | -67.441 | -48.924 | `False` |
| `copy_hint_rank_bucket` | 20 | 0 | -65.026 | -75.264 | `True` |

## Decision

`community bookcase topology does not reduce v9 residual streams above controls`

Some targets can look better than very poor permuted topology labels, but promotion requires positive heldout saving after model cost. No target satisfies that condition.

No external control source is integrated and net v9 reduction is `0.0` bits.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
