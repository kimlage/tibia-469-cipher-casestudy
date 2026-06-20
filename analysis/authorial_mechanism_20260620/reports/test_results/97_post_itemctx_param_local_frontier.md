# Post-Itemctx Param Local Frontier

Verdict: `post_itemctx_param_local_frontier_closed`. Translation delta: `NONE`.

This audit retests the immediate one-edit local recipe frontier after
the item-type extra-context parameter changed to order `1` / `alpha=2`.
It scores single literal-to-copy and copy-to-literal edits under the
same payload, forced-rule, minaddr, midpoint context, alpha=1
copy-length, and itemctx_param contracts.

## Result

- Current formula bits: `8561.792`
- Literal-to-copy candidates tested: `21`
- Copy-to-literal candidates tested: `283`
- Invalid candidates: `115`
- Best repair type: `literal_to_copy`
- Best repair delta: `0.957` bits
- Best repair: book `3`, op `4`, text `60199`,
  length `5`
- Best repair total bits: `8562.749`
- Literal offset: `12`
- Source digit position: `22`

## Interpretation

A local edit is promoted only when exact rescoring remains cheaper and
70/70 roundtrip plus forced-rule validation still pass. This is a
mechanical recipe audit only; it does not introduce plaintext, row0
meaning, or authorial intent.
