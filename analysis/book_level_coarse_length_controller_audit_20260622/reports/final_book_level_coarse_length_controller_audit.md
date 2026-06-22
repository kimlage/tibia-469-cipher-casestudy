# Final Book-Level Coarse Length Controller Audit

Status: `analysis_only`
Classification: `PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

This audit integrates the recent length/control factorization at book level: known `book_length`, latent `op_count`, coarse `type:length_bucket` sequence, and within-bucket residual lengths represented as a composition constrained by the book length.

No target text, plaintext, semantics, fan glosses, row0 origin, or exact residuals are used to choose the coarse sequence.

## Residual Composition

- Books: `60` (`12` trivial, `48` nontrivial).
- Independent residual bits: `1031.010`.
- Composition-index bits: `665.782`.
- Saving: `365.229` bits.
- Classification: `PROMOTED_RESIDUAL_COMPOSITION_CODEC`.

Given the true coarse sequence and `book_length`, exact residual lengths can be represented by a book-level composition index. This promotes a residual composition codec: the fine residual field is reduced structurally, though not freely generated.

## Latent Op-Count Coarse Beam

- Best model pair: `book_length__op_count`.
- Pair classification: `PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE`.
- Exact op_count in beam: `120/150`.
- Exact coarse sequence in beam: `56/150`.
- Nontrivial exact coarse sequences: `13`.
- Same-multiset shuffled exact-sequence p95: `37`.
- Promoted pairs: `['global__op_count', 'global__count_x_pos', 'book_length__op_count', 'book_length__count_x_pos', 'phase_x_length__op_count', 'phase_x_length__count_x_pos']`.

The true coarse sequence survives in beam above same-multiset controls after `op_count` is made latent. This does not make top-1 generation exact, but it does reduce the status of op_count/coarse sequence from pure atlas to a book-level controller candidate with corrections.

## Integrated Cost

| Model | Bits |
| --- | ---: |
| op_count + coarse sequence separated, uniform residual | `4478.440` |
| op_count granted coarse model + residual composition index | `2711.394` |
| latent op_count beam + residual composition/corrections | `3146.578` |

The latent book-level controller improves substantially over separated op_count/coarse/residual declaration, but remains worse than the version that still grants true op_count to the coarse controller. The gap is the current book-level correction ledger.

## Decision

- `PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE`.
- `op_count` is no longer treated as simply conceded: the latent beam recovers true op_count in most held-out books and keeps exact coarse sequences above same-multiset controls.
- The fine length residual is reduced to a book-level composition index when the coarse sequence is known or corrected.
- This is closer to a gerative mechanism, but not a complete generator: top-1 books are not exact, and correction payload remains.
- `row0`, translation, plaintext, and the compression bound remain unchanged.

## Remaining External Fields

- coarse sequence corrections when the true sequence misses beam
- book-level composition index for exact residual lengths
- literal innovation tape payload and schedule
- copy-hint rank stream
- seed books `0..9`
- `row0`

## Reproducible Artifacts

- [01_book_level_coarse_length_controller_gate.py](../scripts/01_book_level_coarse_length_controller_gate.py)
- [01_book_level_coarse_length_controller_gate.json](test_results/01_book_level_coarse_length_controller_gate.json)
- [01_book_level_coarse_length_controller_gate.md](test_results/01_book_level_coarse_length_controller_gate.md)
- [02_compile_final_book_level_coarse_length_controller_audit.py](../scripts/02_compile_final_book_level_coarse_length_controller_audit.py)
