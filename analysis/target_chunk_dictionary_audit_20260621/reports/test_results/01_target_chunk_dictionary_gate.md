# Target Chunk Dictionary Gate

Classification: `target_chunk_dictionary_rejected`
Translation delta: `NONE`

## Purpose

Test whether the missing target-stream can be represented as a compact
dictionary of exact operation chunks after the exact skeleton is granted.

## Summary

- Operation chunks: `261` (`208` copy, `53` literal).
- Copy/literal digits: `9301` / `266`.
- Unique chunks overall: `256/261` (`0.981`).
- Unique copy chunks: `207/208` (`0.995`).
- Unique literal chunks: `49/53` (`0.925`).
- Repeated chunks/rows/digits overall: `5` / `10` / `292`.
- Target-conditioned baseline bits: `941.718`.
- All-chunk dictionary bits: `33383.885`.
- Dictionary delta vs baseline: `32442.167` bits.
- Repeated-only chunk dictionary delta vs raw stream: `-461.782` bits.

## Repeated Chunk Examples

| Chunk | Length | Count |
| --- | ---: | ---: |
| `819537243485625108114636467243554600361451912112888304646797278316013451586042158577445451904504215956151353478019288952160199364672431427894` | `141` | `2` |
| `19` | `2` | `2` |
| `6` | `1` | `2` |
| `7` | `1` | `2` |
| `9` | `1` | `2` |

## Decision

- Promotes target-chunk dictionary: `False`.
- Exact target chunks are too close to unique payload declarations to serve as a compact generator.
- This rejects the simplest target-stream dictionary account; it does not reject richer latent/state mechanisms.
- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
