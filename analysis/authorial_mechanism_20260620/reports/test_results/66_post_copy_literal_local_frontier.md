# Post Copy-to-Literal Local Frontier

Verdict: `post_copy_literal_local_frontier_closed`. Translation delta: `NONE`.

This audit retests the local one-edit frontier after the promoted
copy-to-literal repair. It checks both directions under the current exact
contextual cost model: literal-to-copy and copy-to-literal.

## Results

- Current formula bits: `8803.1`
- Literal-to-copy candidates tested: `23`
- Best literal-to-copy delta: `0.4` bits
- Copy-to-literal candidates tested: `281`
- Invalid copy-to-literal candidates: `116`
- Best copy-to-literal delta: `1.5` bits
- Copy-to-literal pairs tested: `13530`
- Invalid copy-to-literal pairs/singles: `212`
- Best copy-to-literal pair delta: `3.5` bits

## Interpretation

No additional local repair is promoted if all best deltas are positive.
This closes the immediate one-edit frontier and the copy-to-literal pair
frontier for the current contextual formula, without changing the
semantic verdict.
