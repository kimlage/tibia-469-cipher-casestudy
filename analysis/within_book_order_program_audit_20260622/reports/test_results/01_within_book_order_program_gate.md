# Within-Book Order Program Gate

Classification: `WITHIN_BOOK_ORDER_PROGRAM_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Given the true per-book multiset of joint operation tokens, test whether a prefix-trained no-replacement sequential policy can reduce the exact within-book order index.

## Summary

- Uniform order bits: `587.378`.
- Policy order bits: `606.765`.
- Saving vs uniform order: `-19.387` bits.
- Cells beating shuffled-train p95: `1/5`.
- Cells beating shuffled-test p95: `0/5`.
- Greedy exact books: `57`.
- Greedy nontrivial exact books: `4`.
- True sequence in beam20: `118`.
- Nontrivial true sequence in beam20: `37`.

## Prefix Holdouts

| Cutoff | Family | Test ops | Uniform bits | Policy bits | Saving | Train p95 | Test p95 | Beam hits |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| `20` | `prev_control` | `182` | `228.267` | `229.228` | `-0.961` | `False` | `False` | `38` |
| `30` | `prev_control` | `140` | `170.470` | `175.956` | `-5.486` | `False` | `False` | `30` |
| `40` | `prev_op_type` | `95` | `112.227` | `120.654` | `-8.427` | `True` | `False` | `25` |
| `50` | `prev_control` | `56` | `61.337` | `64.993` | `-3.656` | `False` | `False` | `16` |
| `60` | `prev_op_type` | `20` | `15.077` | `15.933` | `-0.857` | `False` | `False` | `9` |

## Decision

This can only become a generator component if it reduces the granted order index under holdout and survives shuffled-order controls. The book multiset is still granted in this gate.
