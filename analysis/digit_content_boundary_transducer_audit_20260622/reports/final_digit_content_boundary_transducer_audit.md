# Final Digit Content Boundary Transducer Audit

Status: `analysis_only`
Classification: `WEAK_DIGIT_BOUNDARY_CLUE_NOT_GENERATOR`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can decoder-visible digit-prefix/content features derive internal operation starts and literal/copy modes without granting the operation-token sequence or target-conditioned copy availability?

## Result

The all-position model costs `3075.566` bits versus `2160.605` true-count composition bits (`914.961` bits worse). It beats composition in `0/5` cells and shuffled-label p05 in `4/5` cells. Across held-out scoring it has `343` true start labels and predicts `0` start labels.

## Decision

This is the first strict pilot of the selected digit/content-boundary route. It is promoted only if it reduces the internal-start/mode dependency after controls. Row0, plaintext, translation, and compression_bound remain unchanged.

## Reproducible Artifacts

- [01_all_position_boundary_transducer_gate.py](../scripts/01_all_position_boundary_transducer_gate.py)
- [01_all_position_boundary_transducer_gate.json](test_results/01_all_position_boundary_transducer_gate.json)
- [01_all_position_boundary_transducer_gate.md](test_results/01_all_position_boundary_transducer_gate.md)
