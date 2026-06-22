# Literal Payload Reference Subcodec Gate

Classification: `literal_payload_reference_subcodec_rejected`
Translation delta: `NONE`

## Purpose

Test whether literal payload chunks that already occurred in emitted text
can be replaced by declared prior references after paying mode/source cost.

## Summary

- Literal chunks/digits: `53` / `266`.
- Chunks with prior occurrence: `38`.
- Prior-occurrence digits: `103`.
- Raw uniform payload bits: `883.633`.
- Beneficial references before mode cost: `11` chunks / `48` digits.
- No-mode reference delta: `-30.001` bits.
- Charged reference delta: `22.999` bits.
- Charged selected references: `11` chunks / `48` digits.

## Random Controls

- Trials: `500`.
- Charged delta mean/min/p05/p50/p95/max: `51.370` / `39.856` / `47.916` / `53.000` / `53.000` / `53.000`.
- Reference count mean/max: `0.618` / `4`.
- Reference digit mean/max: `2.504` / `17`.

## Decision

- Promotes literal payload reference subcodec: `False`.
- Prior whole-chunk recurrence is diagnostic only unless it beats raw payload after mode/source cost and controls.
- Literal payload remains a declared dependency.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
