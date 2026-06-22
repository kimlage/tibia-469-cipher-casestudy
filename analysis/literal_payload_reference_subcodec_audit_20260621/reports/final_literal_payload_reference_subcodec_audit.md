# Final Literal Payload Reference Subcodec Audit

Status: `analysis_only`
Classification: `LITERAL_PAYLOAD_REFERENCE_SUBCODEC_REJECTED`
Translation delta: `NONE`
Plaintext claim: `False`
Row0 origin: `unchanged_exogenous`
Compression bound: `unchanged_8154_676268`

## Question

Can literal payload chunks that already occurred in emitted text be
replaced by a declared-reference subcodec after paying mode/source cost?

## Result

- Literal chunks/digits: `53` / `266`.
- Chunks with prior occurrence: `38`.
- Prior-occurrence digits: `103`.
- Raw uniform payload bits: `883.633`.
- Beneficial references before mode cost: `11` chunks / `48` digits.
- No-mode reference delta: `-30.001` bits.
- Charged reference delta: `22.999` bits.
- Charged selected references: `11` chunks / `48` digits.
- Random charged delta mean/p05/p95: `51.370` / `47.916` / `53.000`.

The recurrence is real but not usable as a promoted subcodec under this
paid model: the apparent no-mode saving disappears once literal chunks
need mode decisions and source addresses.

## Decision

- No literal-payload reference subcodec is promoted.
- Whole-chunk recurrence remains a diagnostic clue only.
- Literal payload remains a declared dependency.
- This does not change the compression bound.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.

## Sources

- [Literal payload reference subcodec gate](test_results/01_literal_payload_reference_subcodec_gate.md)
