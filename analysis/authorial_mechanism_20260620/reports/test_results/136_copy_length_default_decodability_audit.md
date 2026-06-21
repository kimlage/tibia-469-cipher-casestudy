# 136. Copy Length Default Decodability Audit

Classification: `controlled_copy_length_default_exception_formula_improvement`
Translation delta: `NONE`

## Purpose

Audit 135 found that most copy lengths equal the maximum extension
against the target book. This audit checks whether that can become a
decoder-side default rule, or whether it depends on future target digits
only known to the encoder.

## Result

- Active bits: `8343.062`
- Active copy-length bits: `1485.689`
- Candidate copy-length bits: `1348.806`
- Candidate total bits: `8206.178`
- Candidate gain: `136.884` bits
- Recomputed bits: `8343.062`
- Roundtrip: `70/70`
- Copy items: `261`

| Rule | Decodable | Matches | Exceptions | Coverage | Optimistic exception lower bound |
|---|---:|---:|---:|---:|---:|
| `min_len_default` | `True` | `11` | `250` | `0.042` | `1582.498` |
| `previous_copy_length_default` | `True` | `11` | `250` | `0.042` | `1556.367` |
| `decoder_max_possible_after_source` | `True` | `60` | `201` | `0.230` | `1431.610` |
| `encoder_target_max_extension` | `False` | `238` | `23` | `0.912` | `251.639` |

## Interpretation

The high-coverage default is `encoder_target_max_extension`: it matches
`238/261` copies. But that rule compares the source chunk against future
target digits, which the decoder does not know before decoding the copy.
The best decoder-side default tested here, `decoder_max_possible_after_source`,
matches only `60/261` copies as a pure default. However, a decodable
default/exception ledger can use that default and encode a flag plus
adaptive exception length. With an explicit `8` bit declaration delta,
that remaps copy-length cost from `1485.689` to
`1348.806` bits, lowering the formula to
`8206.178` bits.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_default_exception_formula_469.json](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_default_exception_formula_469.json)

## Boundary

- A new mechanical compression bound is promoted for copy-length coding.
- Copy length is not removed entirely; it is remodeled as a decodable default/exception ledger.
- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
