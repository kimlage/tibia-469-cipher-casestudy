# 131. Online Formula Recipe Prune Audit

Classification: `lossless_recipe_representation_simplification`
Translation delta: `NONE`

## Purpose

Audit 129 promoted an online reparse formula. This audit checks whether
that formula's committed recipe still carries fields that are derivable
from the recipe itself rather than required to generate the books.

## Result

- Active recomputed bound: `8343.062` bits
- Stripped projection bound: `8343.062` bits
- Score delta: `+0.000000000000` bits
- Active roundtrip: `70/70`
- Stripped roundtrip: `70/70`
- Removed book `length` fields: `70`
- Removed copy `target_start` fields: `261`
- Recipe JSON byte reduction: `5612` bytes

## Remaining Declared Recipe Dependency

| Field family | Count | Digits covered |
|---|---:|---:|
| Literal runs | `87` | `857` |
| Copy ops | `261` | `10406` |
| Copy source fields | `261` | `10406` |
| Copy length fields | `261` | `10406` |

## Interpretation

The per-book `length` field and copy `target_start` field are
representation artifacts for the active online formula. Removing
them in-memory preserves the exact cost and `70/70` roundtrip.
The bound is unchanged, but the canonical recipe can be documented
more tightly: book length is recovered from operation lengths, and
copy target start is recovered from cumulative position.

## Boundary

- No plaintext or translation is introduced.
- Row0/table origin is unchanged.
- The active formula file is not rewritten by this audit.
- Remaining literal payload and copy source/length fields are still
  required declared recipe dependencies.
