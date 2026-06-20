# Post-Adaptive-Copy-Length Local Frontier

Verdict: `post_adaptive_copy_length_local_frontier_closed`. Translation delta: `NONE`.

This audit retests the immediate one-edit local recipe frontier after
adaptive bounded copy-length coding became the active formula. It scores
single literal-to-copy and copy-to-literal edits under the same payload,
item-type, forced-rule, minaddr, and adaptive copy-length contracts.

## Result

- Current formula bits: `8575.986`
- Literal-to-copy candidates tested: `21`
- Copy-to-literal candidates tested: `283`
- Invalid candidates: `115`
- Best repair type: `copy_to_literal`
- Best repair delta: `1.084` bits
- Best repair: book `34`, op `7`, text `45765`,
  length `5`
- Best repair total bits: `8577.070`

## Interpretation

A local edit is promoted only when exact rescoring remains cheaper and
70/70 roundtrip plus forced-rule validation still pass. This is a
mechanical recipe audit only; it does not introduce plaintext, row0
meaning, or authorial intent.
