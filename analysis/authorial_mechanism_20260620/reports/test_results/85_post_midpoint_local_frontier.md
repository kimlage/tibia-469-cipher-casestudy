# Post-Midpoint Local Frontier

Verdict: `post_midpoint_local_frontier_closed`. Translation delta: `NONE`.

This audit retests the immediate one-edit local recipe frontier after
the fixed book-midpoint adaptive copy-length context became the active
formula. It scores single literal-to-copy and copy-to-literal edits under
the same payload, item-type, forced-rule, minaddr, and midpoint copy-length
contracts.

## Result

- Current formula bits: `8574.407`
- Literal-to-copy candidates tested: `21`
- Copy-to-literal candidates tested: `283`
- Invalid candidates: `115`
- Best repair type: `literal_to_copy`
- Best repair delta: `1.537` bits
- Best repair: book `17`, op `1`, text `477090`,
  length `6`
- Best repair total bits: `8575.944`
- Literal offset: `1`
- Source digit position: `208`

## Interpretation

A local edit is promoted only when exact rescoring remains cheaper and
70/70 roundtrip plus forced-rule validation still pass. This is a
mechanical recipe audit only; it does not introduce plaintext, row0
meaning, or authorial intent.
