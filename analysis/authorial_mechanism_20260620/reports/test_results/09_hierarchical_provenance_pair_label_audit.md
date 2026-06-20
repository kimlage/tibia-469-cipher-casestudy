# Hierarchical Provenance Pair-Label Audit

Verdict: `hierarchical_provenance_not_pair_table_formula`. Translation delta: `NONE`.

This audit asks whether the new hierarchical generation provenance
explains the unresolved 55-cell unordered pair table. It derives
per-pair features from book recipe operations, tape inventory
self-reference operations, component usage, omitted-zero rendering,
and canonical `occ_streams.json` token positions.

## Best Stump

| Feature | Threshold | Hits | Accuracy | Rough gain vs lookup | Control p(hit) | Control p(gain>=0) |
|---|---:|---:|---:|---:|---:|---:|
| `diff` | `4.5000` | `16/55` | `0.291` | `-196.1` | `0.4194` | `0.0014` |

## Best Inventory-Preserving Order Fill

| Feature | Reverse | Hits | Accuracy | Control p(hit) |
|---|---:|---:|---:|---:|
| `top_source_component_frac` | `True` | `11/55` | `0.200` | `0.8816` |

## Control Summary

| Control metric | Runs | Mean | Max | p(>= observed) |
|---|---:|---:|---:|---:|
| `best_stump_hits` | `700` | `15.38` | `18` | `0.4194` |
| `best_order_fill_hits` | `700` | `12.03` | `19` | `0.8816` |

## Boundary

The hierarchical formula improves book generation, but these provenance
features do not promote a pair-table origin formula unless they beat
inventory-preserving controls and rough lookup cost. No plaintext or
semantic claim is introduced.
