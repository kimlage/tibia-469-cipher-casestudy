# Post-Midpoint Alpha1 Pair Frontier

Verdict: `post_midpoint_alpha1_pair_frontier_closed`. Translation delta: `NONE`.

This audit tests whether two compatible local recipe edits improve
together after the one-step midpoint alpha=1 frontier closed. It uses
the active midpoint context, alpha=1 copy-length ledger, payload model,
item-type model, forced rules, book-length ledger, and minaddr absolute
source addresses.

## Result

- Current formula bits: `8572.267`
- Valid single candidates: `189`
- Literal-to-copy candidates tested: `21`
- Copy-to-literal candidates tested: `283`
- Invalid singles: `115`
- Compatible pairs: `17762`
- Valid pairs: `17663`
- Invalid pairs: `99`

## Best Single

- Type: `literal_to_copy`
- Delta: `0.971` bits
- Book/op/text: `17` / `1` / `477090`

## Best Pair

- Delta: `2.501` bits
- Total bits: `8574.768`
- Repair 1: `literal_to_copy` book `3`, op `4`, text `60199`, length `5`
- Repair 2: `literal_to_copy` book `17`, op `1`, text `477090`, length `6`

## Interpretation

Compatible pairs are promoted only when exact rescoring remains cheaper
and 70/70 roundtrip plus forced-rule validation still pass. This is a
mechanical recipe audit only; it does not introduce plaintext, row0
meaning, or authorial intent.
