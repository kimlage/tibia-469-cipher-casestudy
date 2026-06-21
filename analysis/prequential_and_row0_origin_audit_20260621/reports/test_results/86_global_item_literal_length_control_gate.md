# Global Item/Literal-Length Control Gate

Classification: `global_item_literal_control_closes_path_stability`
Translation delta: `NONE`

## Purpose

Gate 85 showed that local item-type or literal-length controls stabilize
the sole book `49` residual. This gate applies those controls globally
on top of the payload-neutralized parser.

## Mode Scoreboard

| Mode | Stable books | Unstable books | Stable delta | Raw-positive evals | Parser bits delta |
|---|---:|---:|---:|---:|---:|
| payload_uniform | 49/50 | 1/50 | +0 | 175/175 | +0.000000 |
| payload_uniform_no_literal_length | 49/50 | 1/50 | +0 | 175/175 | -371.996343 |
| payload_uniform_no_item_type | 50/50 | 0/50 | +1 | 175/175 | -390.466744 |
| payload_uniform_no_item_or_literal_length | 50/50 | 0/50 | +1 | 175/175 | -770.657134 |

## Best Mode

- Best mode: `payload_uniform_no_item_or_literal_length`.
- Best stable exact-path books: `50/50`.
- Best parser-bit delta vs payload baseline: `-770.657134`.
- Best-mode unstable books: `[]`.

## Decision

- The local book 49 controls are applied globally to test whether they close the residual without side effects. A global control is promotable only if it preserves roundtrip/raw-positive coverage and closes exact path stability across all multi-cutoff books.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
