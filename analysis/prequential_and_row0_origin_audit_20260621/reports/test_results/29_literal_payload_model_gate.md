# Literal Payload Model Gate

Classification: `literal_payload_order2_retained_simplifications_rejected`
Translation delta: `NONE`

## Purpose

After the literal copy-availability gate reduces literal externality,
this gate checks whether the remaining literal payload digit model can
be simplified without retuning the held-out boundary into a post-hoc
compressor claim.

## Summary

- Literal payload digits: `857`.
- Active literal payload bits: `2613.661`.
- Active model: order-`2` previous-emitted-digit context with `98` contexts.
- Order-1 full-corpus delta vs order-2: `95.968` bits.
- Order-1 aggregate online prefix delta vs order-2: `47.346` bits.
- Order-1 aggregate frozen prefix delta vs order-2: `28.609` bits.
- Order-1 frozen split wins: `[20, 35, 50]`.
- Order-2 frozen split wins or ties: `[10, 60]`.
- Order-2 online split wins or ties: `[10, 20, 50, 60]`.
- Best modal default/exception candidate: `38.049` bits worse than active.
- Best non-active structural context `prev2_plus_book_half`: `19.159` bits worse than active.

## Interpretation

The old order-1 simplification does not transfer to the current recipe:
it wins some intermediate frozen splits, but loses on full corpus and in
aggregate prefix online/frozen totals. Modal default/exception coding is
decodable but worse, and the simple structural context families over-split
the stream. The active order-2 payload model is therefore retained as a
dependency boundary, not promoted as an authorial final method.

## Boundary

- No compression bound is promoted.
- Literal payload dependency is sharpened, not removed.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
