# Component-Neutralized Path Stability Gate

Classification: `component_neutralization_improves_path_stability`
Translation delta: `NONE`

## Purpose

Gate 81 localized boundary instability mainly to learned copy-length
and source-exception costs. This gate neutralizes those components
with uniform decodable costs and reruns multi-cutoff path stability.

## Summary

- Active stable exact-path books: `38`.
- Best stability mode: `uniform_copy_length_and_source_exception`.
- Best stable exact-path books: `48`.
- Best stability delta vs active: `10`.

## Mode Scoreboard

| Mode | Stable books | Unstable books | Stable delta | Raw-positive evals | Parser bits delta |
|---|---:|---:|---:|---:|---:|
| active_learned | 38/50 | 12/50 | +0 | 175/175 | +0.000000 |
| uniform_copy_length | 43/50 | 7/50 | +5 | 175/175 | +29.266234 |
| uniform_source_exception | 40/50 | 10/50 | +2 | 175/175 | +37.865814 |
| uniform_copy_length_and_source_exception | 48/50 | 2/50 | +10 | 175/175 | +67.605622 |
| uniform_copy_length_and_full_source | 48/50 | 2/50 | +10 | 175/175 | +435.053776 |

## Best-Mode Residual Instability

- Best mode parser-bit delta vs active: `67.605622`.
- Remaining unstable books: `[26, 34]`.

## Decision

- Uniformizing the learned copy-length/source-exception cost components tests whether path instability is an artifact of overfit component priors. A mode can be structurally interesting only if it improves exact multi-cutoff path stability without being treated as a compression-bound promotion.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
