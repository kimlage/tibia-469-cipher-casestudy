# Post-Minaddr-Repair Local Frontier

Verdict: `controlled_post_minaddr_repair_local_improvement`. Translation delta: `NONE`.

This audit retests one-step literal-to-copy and copy-to-literal edits
after the first minaddr local repair changed the recipe. It uses the
same full rescoring contract as the prior frontier: contextual payload,
contextual item types with forced rules, bounded copy lengths, and
min_len-bounded absolute source addresses.

## Result

- Current formula bits: `8611.408`
- Literal-to-copy candidates tested: `22`
- Copy-to-literal candidates tested: `282`
- Best repair type: `literal_to_copy`
- Best repair delta: `-1.635` bits
- Best repair: book `34`, op `7`, text `45765`,
  length `5`
- Literal offset: `0`
- Source digit position: `183`

## Interpretation

This is another local mechanical recipe repair. It is promoted only
because exact rescoring remains cheaper and 70/70 roundtrip plus
forced-rule validation still pass. It does not introduce plaintext.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_formula_469.json)
