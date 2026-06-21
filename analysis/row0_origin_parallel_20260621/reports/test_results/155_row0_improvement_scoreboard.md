# 155. Row0 Improvement Scoreboard

Classification: `AUDIT_ONLY`
Translation delta: `NONE`

Lookup baseline: `160.521` bits.

| Candidate | Class | Holdout labels | Diagnostic hits | Bits below lookup | 39/19/91 | Controls | External source |
|---|---|---:|---:|---:|---|---|---|
| `lookup_baseline` | `AUDIT_ONLY` | `0` | `55` | `0.0` | `stores_only` | `not_applicable` | `False` |
| `priority_layer_stumps` | `REJECTED_CONTROL` | `15` | `15` | `0.0` | `no` | `False` | `False` |
| `fixed_order_inventory_fill` | `REJECTED_CONTROL` | `0` | `8` | `0.0` | `no` | `False` | `False` |
| `ordered_surface_render_layer` | `PROMOTED_MECHANICAL_CLUE` | `0` | `2` | `0.0` | `yes_surface_only` | `True` | `False` |
| `external_fixed_source` | `BLOCKED_NEEDS_EXTERNAL_SOURCE` | `0` | `0` | `0.0` | `blocked` | `False` | `False` |

This scoreboard is intentionally row0-only. Book-generator compression does not move it unless it predicts row0 labels or explains the special ordered-surface facts.
