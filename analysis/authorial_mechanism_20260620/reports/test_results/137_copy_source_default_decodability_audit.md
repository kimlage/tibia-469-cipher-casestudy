# 137. Copy Source Default Decodability Audit

Classification: `controlled_copy_source_default_exception_formula_improvement`
Translation delta: `NONE`

## Purpose

After copy length was remodeled as a decodable default/exception ledger,
copy source remains the largest declared component. This audit tests a
decodable source default: previous copy source plus previous copy length,
falling back to 0 when illegal, plus a global adaptive exception source.

## Result

- Active bits: `8206.178`
- Active copy-address bits: `3031.700`
- Candidate copy-address bits: `3002.838`
- Candidate total bits: `8177.317`
- Candidate gain: `28.862` bits
- Roundtrip: `70/70`
- Copy items: `261`
- Default source matches: `5/261`
- Exception sources: `256/261`
- Declaration delta charged: `12.0` bits

## Interpretation

The default source rule is weak in raw coverage (`5/261`), but it is
decodable and replaces a few expensive absolute addresses while the
exception source stream gains from a global adaptive prior. After charging
`12.0` extra declaration bits, the
copy-address ledger drops from `3031.700` to
`3002.838` bits and the total bound becomes
`8177.317` bits.

## Promoted Formula

- [sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json](../../sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json)

## Boundary

- A new mechanical compression bound is promoted for copy-source coding.
- Copy source is not removed; it is remodeled as a decodable default/exception ledger.
- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
