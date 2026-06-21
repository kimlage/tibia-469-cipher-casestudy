# Operation Length Dependency Ledger

Classification: `operation_length_dependency_retained`
Translation delta: `NONE`

## Purpose

This ledger consolidates the length side of the current skeleton
frontier. It asks whether recent derivations remove the operation
length atlas or merely make other fields downstream of that atlas.

## Ledger

- Operations: `261`.
- Copies/literals: `208` / `53`.
- Current compression bound: `8154.676268` bits.
- Declared operation dependency fields: `609`.
- Target-start fields derived from lengths: `261`.
- Op-type residual after availability/exception rule: `3`.
- Length atlas records retained: `261`.
- Length records removed by current rules: `0`.
- Type+length records after type rule: `264`.
- Length share of type+length ledger: `0.988636`.

## Rule Coverage

- Best source-free length rule: `length_gte_20` = `116/261`.
- Best source-free copy-length rule: `copy_length_is_remaining_book` = `55/208`.
- Best source-free literal-length rule: `literal_length_is_remaining_book` = `5/53`.

## Copy-Length Boundary

- Decoder max-possible defaults/exceptions: `60` / `201`.
- Copy-length fields retained in compact recipe: `261`.
- Encoder target-max decodable: `False`.
- Dependency retained: `True`.

## Final Source/Length Refresh

- Copy events: `261`.
- Encoder target-max rule improved after partial shifts: `False`.
- Decoder-valid joint rule improved after partial shifts: `False`.
- Declared-source + decoder-max delta: `0`.
- Unique-source + decoder-max delta: `0`.
- Previous-end + decoder-max delta: `0`.
- Structural blocker: `source_length_parser_still_required`.

## Decision

- Promotes length generator: `False`.
- Target positions are derived once the length sequence is known, and operation type is mostly derivable if target copy availability and the length atlas are allowed. The remaining blocker is the length sequence itself: current source-free length rules cover at most 116/261 operation lengths, copy-specific source-free rules cover only 55/208 copy lengths, literal length rules cover only 5/53 literal lengths, and the compact recipe still retains all 261 copy-length fields. The current model therefore explains positions and most type decisions downstream of length, but it does not yet generate the operation-length atlas.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
