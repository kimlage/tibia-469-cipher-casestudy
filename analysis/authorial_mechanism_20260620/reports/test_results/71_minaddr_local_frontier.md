# Minaddr Local Frontier

Verdict: `controlled_minaddr_local_repair_improvement`. Translation delta: `NONE`.

This audit retests the immediate local recipe frontier after bounded copy
lengths and min_len-bounded source addresses changed the exact cost model.
It scores both single literal-to-copy and single copy-to-literal edits
with the active payload context, item-type context, forced rules, bounded
copy lengths, and min_len-bounded absolute addresses.

## Result

- Current formula bits: `8613.067`
- Literal-to-copy candidates tested: `23`
- Copy-to-literal candidates tested: `281`
- Best repair type: `literal_to_copy`
- Best repair delta: `-1.659` bits
- Best repair: book `2`, op `11`, text `11216`,
  length `5`
- Literal offset: `30`
- Source digit position: `225`

## Interpretation

A local edit is promoted only when exact rescoring remains cheaper and
70/70 roundtrip plus forced-rule validation still pass. This is a
mechanical recipe audit only; it does not introduce plaintext.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair_formula_469.json)
