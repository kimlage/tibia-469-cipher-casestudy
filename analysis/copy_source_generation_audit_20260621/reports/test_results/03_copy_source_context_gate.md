# Copy Source Context Gate

Classification: `copy_source_context_generator_rejected`
Translation delta: `NONE`

## Purpose

Test whether simple source-bearing context tables can predict copy
source after granting exact skeleton and literal payload.

## Summary

- Copy events: `208`.
- Context families: `11`.
- Best context: `book_mod10_x_length`.
- Best chunk hits: `173/208`.
- Best source-exact hits: `173/208`.
- Best net vs raw absolute source bits: `199.919` bits.
- Prefix/holdout cover-all cells: `0/5`.

## Full-Fit Scoreboard

| Context | Chunk hits | Source exact | Contexts | Net vs raw |
| --- | ---: | ---: | ---: | ---: |
| `book_mod10_x_length` | `173/208` | `173/208` | `173` | `199.919` |
| `phase10_x_length` | `170/208` | `170/208` | `170` | `198.090` |
| `op_index_x_length` | `162/208` | `162/208` | `162` | `193.532` |
| `length` | `85/208` | `85/208` | `85` | `97.617` |
| `target_phase_16` | `18/208` | `18/208` | `16` | `1.938` |
| `op_index` | `15/208` | `15/208` | `13` | `-8.213` |
| `book_mod10` | `13/208` | `13/208` | `10` | `-21.400` |
| `matching_count_bucket` | `11/208` | `11/208` | `6` | `-54.595` |
| `target_phase_10` | `11/208` | `11/208` | `10` | `3.139` |
| `length_bucket` | `7/208` | `7/208` | `6` | `-2.617` |
| `global` | `4/208` | `4/208` | `1` | `-35.450` |

## Prefix/Holdout

| Cutoff | Context | Test chunk hits | Test source exact | Oracle context |
| ---: | --- | ---: | ---: | --- |
| `20` | `op_index_x_length` | `1/155` | `1/155` | `global` |
| `30` | `book_mod10_x_length` | `0/119` | `0/119` | `target_phase_16` |
| `40` | `book_mod10_x_length` | `0/80` | `0/80` | `target_phase_16` |
| `50` | `book_mod10_x_length` | `0/49` | `0/49` | `length` |
| `60` | `book_mod10_x_length` | `0/18` | `0/18` | `global` |

## Decision

- Promotes copy-source generator: `False`.
- Source context tables are source-bearing selectors. They do not remove source declarations unless they generalize and beat raw source declaration after paid table and corrections.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
