# Post-Minaddr-Repair2 Local Frontier

Verdict: `post_minaddr_repair2_local_frontier_closed`. Translation delta: `NONE`.

This audit retests one-step literal-to-copy and copy-to-literal edits
after the second minaddr local repair changed the recipe. It uses the
same full rescoring contract as the prior local-frontier passes.

## Result

- Current formula bits: `8609.773`
- Literal-to-copy candidates tested: `21`
- Copy-to-literal candidates tested: `283`
- Best repair type: `copy_to_literal`
- Best repair delta: `0.121` bits
- Best repair: book `26`, op `2`, text `94343`,
  length `5`

## Interpretation

The local frontier is closed for one-step edits under the current
bounded-copy-length and min_len-bounded address cost model if the best
candidate is at or above zero delta. This is a mechanical recipe audit
only; it does not introduce plaintext.
