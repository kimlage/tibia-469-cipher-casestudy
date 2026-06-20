# Post-Itemctx Param Pair Frontier

Verdict: `post_itemctx_param_pair_frontier_closed`. Translation delta: `NONE`.

This audit tests whether two compatible local recipe edits improve
together after the post-itemctx_param one-step frontier closed. It uses
the active item-type split context with order `1` / `alpha=2`, midpoint
copy-length context, alpha=1 copy-length ledger, payload model, forced
rules, book-length ledger, and minaddr absolute source addresses.

## Result

- Current formula bits: `8561.792`
- Valid single candidates: `189`
- Literal-to-copy candidates tested: `21`
- Copy-to-literal candidates tested: `283`
- Invalid singles: `115`
- Compatible pairs: `17762`
- Valid pairs: `17663`
- Invalid pairs: `99`

## Best Single

- Type: `literal_to_copy`
- Delta: `0.957` bits
- Book/op/text: `3` / `4` / `60199`

## Best Pair

- Delta: `1.809` bits
- Total bits: `8563.601`
- Repair 1: `literal_to_copy` book `2`, op `11`, text `14519`, length `5`
- Repair 2: `literal_to_copy` book `3`, op `4`, text `60199`, length `5`

## Interpretation

Compatible pairs are promoted only when exact rescoring remains cheaper
and 70/70 roundtrip plus forced-rule validation still pass. This is a
mechanical recipe audit only; it does not introduce plaintext, row0
meaning, or authorial intent.
