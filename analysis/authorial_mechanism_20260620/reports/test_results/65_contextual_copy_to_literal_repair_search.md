# Contextual Copy-to-Literal Repair Search

Verdict: `controlled_contextual_copy_to_literal_improvement`. Translation delta: `NONE`.

This audit tests the reverse of the usual literal-to-copy repair. After
contextual payload coding, a short copy can become more expensive than
spelling the same digits as a literal. Every candidate is exactly rescored
with literal lengths, contextual literal payload, copy bits, and contextual
item-type bits with deterministic forced rules.

## Result

- Current formula bits: `8803.5`
- Copy-to-literal repairs tested: `282`
- Invalid under forced-rule/roundtrip checks: `114`
- Best repair delta: `-0.4` bits
- Best repair: book `34`, copy op `7`,
  book position `105`, length `5`,
  text `45765`, source digit position `183`

## Interpretation

This is a mechanical recipe audit only. It preserves exact book
roundtrip and does not introduce plaintext, row0 meaning, or authorial
intent.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_copy_to_literal_formula_469.json`](../../sequential_lz_digit_address_contextual_copy_to_literal_formula_469.json)
