# Source Blocker Structural Context Gate

Classification: `simple_source_contexts_do_not_rescue_cross_op_near_tie`
Translation delta: `NONE`

## Purpose

Audits 153-154 isolate a tight source-cost blocker: the best cross-op
optional literal repair would improve under a source-free oracle, but
source-free coding is not decodable and the active source ledger remains
slightly above break-even. This gate checks whether the follow-up
structural source contexts actually rescue that blocker.

## Summary

- Cross-op candidate delta: `+0.027` bits.
- Source margin over break-even: `+0.027` bits.
- Source-free oracle delta: `-11.209` bits.
- Active copy-source delta: `+11.237` bits.
- Best non-global source context: `book_half`.
- Best non-global context delta vs global: `+5.872` bits.
- Prefix-frozen losses for best context: `5/5`.
- Min/max prefix-frozen delta: `+0.063` / `+6.274` bits.

## Interpretation

The near tie is real but not promotable. The source-free oracle would
save enough bits, but it removes a required decodable source choice.
The tested mechanical context split that comes closest, `book_half`,
is still `+5.872` bits worse on the full source stream and worse in
all `5/5` prefix-frozen checks. That rejects simple structural context
splitting as the next source fix.

## Boundary

- No compression bound is promoted.
- No plaintext, translation, semantic reading, or case reopening is introduced.
- Row0/table origin remains exogenous.
