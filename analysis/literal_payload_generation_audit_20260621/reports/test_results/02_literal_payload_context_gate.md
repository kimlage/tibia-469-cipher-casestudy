# Literal Payload Context Gate

Classification: `literal_payload_context_rejected`
Translation delta: `NONE`

## Purpose

Test whether literal payload chunks can be predicted from source-free
contexts once the exact skeleton is granted.

## Summary

- Chunks/digits: `53` / `266`.
- Payload labels: `49`.
- Best context: `op_index_x_length`.
- Best exact chunks: `39/53`.
- Best exact digits: `222/266`.
- Best net vs raw uniform bits: `44.588` bits.
- Prefix/holdout any-exact-chunk cells: `0/5`.
- Prefix/holdout cover-all chunks cells: `0/5`.

## Full-Fit Scoreboard

| Context | Exact chunks | Exact digits | Contexts | Net vs raw |
| --- | ---: | ---: | ---: | ---: |
| `op_index_x_length` | `39/53` | `222/266` | `39` | `44.588` |
| `phase10_x_length` | `39/53` | `219/266` | `38` | `41.266` |
| `book_mod10_x_length` | `37/53` | `219/266` | `37` | `47.214` |
| `target_phase_16` | `15/53` | `41/266` | `15` | `45.967` |
| `length` | `14/53` | `130/266` | `12` | `34.622` |
| `op_index` | `13/53` | `43/266` | `13` | `43.073` |
| `target_phase_10` | `11/53` | `29/266` | `10` | `36.287` |
| `book_mod10` | `10/53` | `37/266` | `10` | `37.642` |
| `length_bucket` | `8/53` | `57/266` | `6` | `23.217` |
| `forced` | `3/53` | `6/266` | `2` | `11.331` |
| `global` | `2/53` | `4/266` | `1` | `7.244` |

## Prefix/Holdout

| Cutoff | Context | Test exact chunks | Test exact digits | Oracle context |
| ---: | --- | ---: | ---: | --- |
| `20` | `op_index_x_length` | `0/27` | `0/126` | `length` |
| `30` | `op_index_x_length` | `0/21` | `0/97` | `length` |
| `40` | `phase10_x_length` | `0/15` | `0/82` | `length` |
| `50` | `op_index_x_length` | `0/7` | `0/45` | `global` |
| `60` | `op_index_x_length` | `0/2` | `0/4` | `global` |

## Decision

- Promotes literal payload generator: `False`.
- Weak context clue: `False`.
- Simple source-free context tables over the granted skeleton do not generate literal payload. Full-fit exact hits come from a payload-bearing lookup table; prefix/holdout gets no exact chunks and the paid table does not beat raw literal digits.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
