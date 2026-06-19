# 2026-06-19 eye/blink arity model

This folder integrates and tests the post-review eye/sprite hypothesis as a
mechanism-origin front only.

The motivating clue is lore-level: Bonelord language is described as a blinking
code with each eye, and 469 is said to require enough eyes to blink it. The
testable mechanical idea is narrower:

```text
5 eyes -> C(5,2) = 10 eye pairs -> digits 0..9
two digit events -> 55 unordered pair cells in row0
```

This does not reopen translation. It asks whether an eye-arity model can explain
the existing row0 pair table, E-layer pressure, or render anomalies with less
cost than lookup and better than controls.

## Rebuild

```bash
python3 analysis/eye_model_20260619/k5_eye_pair_model_search.py
python3 analysis/eye_model_20260619/eye_state_5x2_model_search.py
```

## Outputs

| File | Role |
|---|---|
| `eye_count_source_registry.yaml` | Source registry with first-frame sprite URLs, manual visible-eye counts, confidence, and no semantic promotion. |
| `k5_eye_pair_model_report.md` / `k5_eye_pair_model_results.json` | Tests `5 eyes -> C(5,2)=10` against row0 labels and E-layer controls. |
| `eye_state_5x2_model_report.md` / `eye_state_5x2_model_results.json` | Tests the alternative `5 eyes x 2 states` arity model. |
| `../post_review_20260619/sprite_eye_count_audit.md` | Records the sprite source audit and first-frame count policy without committing sprite binaries. |

## Current Verdict

The arity match is useful as a structured hypothesis and a lore bridge, but the
initial row0 tests reject both K5 and 5x2 as pair-matrix origin formulas. They
remain mechanism-only weak/contextual clues unless future external evidence
provides a specific eye mapping.

Translation delta: `NONE`.
