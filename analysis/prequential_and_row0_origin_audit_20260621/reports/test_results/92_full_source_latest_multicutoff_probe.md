# Full Source Latest Multi-Cutoff Probe

Classification: `full_source_latest_multicutoff_stable`
Translation delta: `NONE`

## Purpose

Gate 91 exposed every same-length source only on cutoff 60. This probe
runs the most disruptive tie policy, `latest_source`, on cutoffs 50 and
60 so books 60-69 receive two exact-path observations.

## Result

- Tested cutoffs: `[50, 60]`.
- Book evaluations: `30`.
- Roundtrip evaluations: `30/30`.
- Raw-positive evaluations: `30/30`.
- Multi-cutoff stable books: `10/10`.
- Unstable multi-cutoff books: `[]`.
- Non-earliest source selections: `35`.
- Hidden candidates exposed: `1246561`.
- Total primary parser bits: `1460.629276`.

## Decision

- The most disruptive full-source tie policy from gate 91 is tested over cutoffs 50 and 60, giving books 60-69 two observations for exact-path stability under exposed sources.
- No compression-bound change is introduced.
- No formula is emitted.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
