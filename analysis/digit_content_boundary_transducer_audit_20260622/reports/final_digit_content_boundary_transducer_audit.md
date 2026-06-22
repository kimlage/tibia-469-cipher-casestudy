# Final Digit Content Boundary Transducer Audit

Status: `analysis_only`
Classification: `START_CANDIDATE_RANKING_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can decoder-visible digit-prefix/content features rank a small candidate set for internal starts and reduce the paid start-position dependency?

## Result

The candidate ranking codec costs `1941.433` bits versus `2063.661` exact start-composition bits (`-122.227`). It beats random top-K p05 in `2/5` cells and captures `37/343` starts, leaving `306` missed-start corrections.

## Decision

This gate is a candidate-set test, not a complete parser. It is promoted only if the candidate set plus corrections reduces the start ledger under controls. Row0, plaintext, translation, and compression_bound remain unchanged.

## Reproducible Artifacts

- [01_all_position_boundary_transducer_gate.py](../scripts/01_all_position_boundary_transducer_gate.py)
- [02_start_candidate_ranking_gate.py](../scripts/02_start_candidate_ranking_gate.py)
- [01_all_position_boundary_transducer_gate.json](test_results/01_all_position_boundary_transducer_gate.json)
- [02_start_candidate_ranking_gate.json](test_results/02_start_candidate_ranking_gate.json)
- [02_start_candidate_ranking_gate.md](test_results/02_start_candidate_ranking_gate.md)
