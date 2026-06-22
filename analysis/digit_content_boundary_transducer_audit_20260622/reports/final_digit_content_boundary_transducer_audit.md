# Final Digit Content Boundary Transducer Audit

Status: `analysis_only`
Classification: `SURPRISAL_START_CANDIDATE_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can decoder-visible digit/content signals rank candidate internal starts well enough to reduce the paid start-position dependency?

## Result

The decoder-visible surprisal candidate codec costs `1922.243` bits versus `2063.661` exact start-composition bits (`-141.417`). It beats random top-K p05 in `0/5` cells and captures `71/343` starts, leaving `272` missed-start corrections.

The target-conditioned diagnostic right/sum surprisal route costs `1665.114` bits versus `2063.661` (`-398.547`), with `4/5` random-control cells. It is not promotable because it looks at the next digit.

## Decision

The digit-boundary surprisal clue remains useful diagnostically, but it does not become an executable decoder-visible start program. Row0, plaintext, translation, and compression_bound remain unchanged.

## Reproducible Artifacts

- [01_all_position_boundary_transducer_gate.py](../scripts/01_all_position_boundary_transducer_gate.py)
- [02_start_candidate_ranking_gate.py](../scripts/02_start_candidate_ranking_gate.py)
- [03_surprisal_start_candidate_gate.py](../scripts/03_surprisal_start_candidate_gate.py)
- [01_all_position_boundary_transducer_gate.json](test_results/01_all_position_boundary_transducer_gate.json)
- [02_start_candidate_ranking_gate.json](test_results/02_start_candidate_ranking_gate.json)
- [02_start_candidate_ranking_gate.md](test_results/02_start_candidate_ranking_gate.md)
- [03_surprisal_start_candidate_gate.json](test_results/03_surprisal_start_candidate_gate.json)
- [03_surprisal_start_candidate_gate.md](test_results/03_surprisal_start_candidate_gate.md)
