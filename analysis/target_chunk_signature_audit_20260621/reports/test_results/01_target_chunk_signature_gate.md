# Target Chunk Signature Gate

Classification: `target_chunk_signature_generator_rejected`
Translation delta: `NONE`

## Purpose

Test whether a coarse signature layer can replace exact target chunks
without becoming payload lookup or a target-text oracle.

## Summary

- Operation chunks: `261` (`208` copy, `53` literal).
- Target-stream digits: `9567`.
- Exact unique chunks from prior audit: `256/261` (`0.981`).
- Best non-payload family: `kind_x_book_mod10_x_length_bucket`.
- Best non-payload signatures/singletons/selector bits: `85` / `22` / `495.649`.
- Least-unique payload family: `kind_x_length_bucket_x_digit_sum_mod10`.
- Least-unique payload signatures/selector bits: `90` / `489.978`.
- Most-exact payload family: `kind_x_length_bucket_x_first2_last2`.
- Most-exact payload singletons/signatures: `251` / `256`.

## Signature Families

| Family | Class | Signatures | Singleton rows | Max bucket | Exact selector bits | Random selector mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `kind` | `non_payload` | `2` | `0` | `208` | `1905.271` | `n/a` |
| `kind_x_length` | `non_payload` | `97` | `52` | `11` | `515.723` | `n/a` |
| `kind_x_length_bucket` | `non_payload` | `12` | `0` | `48` | `1281.181` | `n/a` |
| `kind_x_length_bucket_x_op_phase` | `non_payload` | `41` | `8` | `28` | `844.945` | `n/a` |
| `kind_x_book_mod10_x_length_bucket` | `non_payload` | `85` | `22` | `10` | `495.649` | `n/a` |
| `kind_x_length_bucket_x_first_last` | `payload_edge` | `217` | `180` | `4` | `94.265` | `86.589` |
| `kind_x_length_bucket_x_first2_last2` | `payload_edge` | `256` | `251` | `2` | `10.000` | `6.897` |
| `kind_x_length_bucket_x_digit_support` | `payload_histogram` | `143` | `120` | `33` | `518.045` | `506.124` |
| `kind_x_length_bucket_x_digit_sum_mod10` | `payload_checksum` | `90` | `32` | `10` | `489.978` | `497.372` |
| `kind_x_length_bucket_x_histogram_shape` | `payload_histogram` | `255` | `249` | `2` | `12.000` | `7.323` |

## Decision

- Promotes target-chunk signature generator: `False`.
- Non-payload signatures leave the exact target digits unresolved.
- Payload signatures mostly measure edge/checksum/histogram content already inside the target stream.
- Random same-length controls do not support a promoted source-free signature rule.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
