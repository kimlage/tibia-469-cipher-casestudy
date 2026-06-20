# Restricted Hybrid Vocabulary Reparse

Verdict: `restricted_hybrid_vocabulary_not_promoted`. Translation delta: `NONE`.

This audit tests a controlled reparse rather than a cost-only recoding of
the existing DP LZ parse. A small declared dictionary of repeated digit
motifs is added to the existing literal-run plus prior-copy vocabulary.
The dictionary is charged as raw digit entries, and each model must
roundtrip all 70 books.

## Best Models

| Model | Motifs | Table bits | Total bits | Delta vs current | Roundtrip | Macro items | Decodable |
|---|---:|---:|---:|---:|---:|---:|---:|
| `raw_top_k0_optimistic_no_source_type` | `0` | `0.0` | `9823.3` | `0.0` | `70/70` | `0` | `True` |
| `raw_top_k0_decodable_source_type` | `0` | `0.0` | `9823.3` | `0.0` | `70/70` | `0` | `True` |
| `redundancy_filtered_top_k0_optimistic_no_source_type` | `0` | `0.0` | `9823.3` | `0.0` | `70/70` | `0` | `True` |
| `redundancy_filtered_top_k0_decodable_source_type` | `0` | `0.0` | `9823.3` | `0.0` | `70/70` | `0` | `True` |
| `redundancy_filtered_top_k4_optimistic_no_source_type` | `4` | `110.0` | `9840.7` | `17.4` | `70/70` | `19` | `False` |
| `raw_top_k4_optimistic_no_source_type` | `4` | `110.0` | `9861.3` | `38.0` | `70/70` | `14` | `False` |
| `redundancy_filtered_top_k8_optimistic_no_source_type` | `8` | `488.9` | `10110.1` | `286.8` | `70/70` | `23` | `False` |
| `redundancy_filtered_top_k4_decodable_source_type` | `4` | `110.0` | `10123.2` | `299.9` | `70/70` | `18` | `True` |
| `raw_top_k8_optimistic_no_source_type` | `8` | `569.3` | `10139.3` | `315.9` | `70/70` | `18` | `False` |
| `raw_top_k4_decodable_source_type` | `4` | `110.0` | `10142.8` | `319.5` | `70/70` | `13` | `True` |
| `redundancy_filtered_top_k8_decodable_source_type` | `8` | `488.9` | `10392.9` | `569.6` | `70/70` | `23` | `True` |
| `raw_top_k8_decodable_source_type` | `8` | `569.3` | `10419.7` | `596.4` | `70/70` | `17` | `True` |

## Top Motif Candidates

| Motif | Len | Count | Score |
|---|---:|---:|---:|
| `889521` | `6` | `82` | `1589.5` |
| `8895219` | `7` | `64` | `1434.7` |
| `611451` | `6` | `68` | `1310.5` |
| `895219` | `6` | `66` | `1270.6` |
| `956151353478019288952160...` | `32` | `14` | `1264.6` |
| `561513534780192889521601...` | `32` | `14` | `1264.6` |
| `042159561513534780192889...` | `32` | `14` | `1264.6` |
| `561145191991180036468895...` | `29` | `15` | `1243.4` |

## Interpretation

The restricted hybrid vocabulary does not improve the current formula.
The best dictionary-using optimistic reparse is still above the current
then-current gamma-length DP LZ baseline after the raw motif table is
charged, and the decodable source-type variants are further away.
That result was later superseded by the Rice-length reparse.

## Boundary

This is a mechanical generation audit only. Motifs are digit strings,
not words or plaintext, and no semantic claim is introduced.
