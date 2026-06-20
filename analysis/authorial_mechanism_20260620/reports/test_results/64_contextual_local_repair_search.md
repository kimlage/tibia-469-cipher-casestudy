# Contextual Local Repair Search

Verdict: `contextual_local_repair_not_promoted`. Translation delta: `NONE`.

This audit retests single literal-to-copy repairs after the payload and
item-type contextual ledgers changed the exact cost model. The search
keeps the same generation recipe family and validates each candidate by
full rescoring: literal lengths, contextual literal payload, copy bits,
and contextual item-type bits with deterministic forced rules.

## Result

- Current formula bits: `8803.5`
- Candidate repairs tested: `22`
- Best repair delta: `1.0` bits
- Best repair: book `17`, text `477090`,
  literal offset `1`, length `6`,
  source digit position `208`

## Interpretation

A repair is promoted only when exact rescoring remains cheaper and
70/70 roundtrip plus forced-rule validation still pass. This is a
mechanical recipe audit only; it does not introduce plaintext.
