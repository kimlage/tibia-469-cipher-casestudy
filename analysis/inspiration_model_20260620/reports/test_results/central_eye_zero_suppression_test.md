# Central-Eye Zero Suppression Test

Verdict: `weak_clue`. Translation delta: `NONE`.

Existing zero audit classification: `supporting_render_layer`.

| Selected view | Model | Holdout metric |
|---|---|---:|
| balanced accuracy | `primary_secondary_with_negative_06_and_boundary` | 0.855 |
| rough MDL gain | `geometry_descdiag_only` | 11.6 bits |

The D&D central-eye framing is a useful label for the existing zero/render
signal, but it does not create a formula or semantic value.
