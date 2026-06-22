# Book-Level Coarse Length Controller Gate

Classification: `PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Purpose

Test a book-level controller that links known `book_length`, latent `op_count`, coarse `type:length_bucket` sequence, and within-bucket residual composition. No target text, plaintext, semantics, row0 origin, or exact residuals are used to choose the coarse sequence.

## A. Book-Length Constrained Residual Composition

- Books: `60` (`12` trivial, `48` nontrivial).
- Independent uniform residual bits: `1031.010`.
- Composition-index bits after true coarse sequence and book_length: `665.782`.
- Saving: `365.229` bits.
- Classification: `PROMOTED_RESIDUAL_COMPOSITION_CODEC`.

## B. Latent Op-Count Coarse Beam

- Best pair: `book_length__op_count`.
- Best pair classification: `PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE`.
- Exact op_count in beam: `120/150`.
- Exact coarse sequence in beam: `56/150`.
- Nontrivial exact coarse sequences: `13`.
- Same-multiset shuffled exact-sequence p95: `37`.
- Promoted pairs: `['global__op_count', 'global__count_x_pos', 'book_length__op_count', 'book_length__count_x_pos', 'phase_x_length__op_count', 'phase_x_length__count_x_pos']`.

| Cutoff | Test Books | OpCount In Beam | Sequence In Beam | Nontrivial Sequence | Top1 OpCount | Top1 Sequence |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `20` | `50` | `38` | `15` | `3` | `11` | `0` |
| `30` | `40` | `31` | `13` | `3` | `11` | `0` |
| `40` | `30` | `24` | `12` | `3` | `10` | `0` |
| `50` | `20` | `17` | `9` | `2` | `8` | `0` |
| `60` | `10` | `10` | `7` | `2` | `5` | `0` |

## C. Integrated Book-Level Cost

| Model | Bits |
| --- | ---: |
| op_count + coarse sequence separated, uniform residual | `4478.440` |
| op_count granted coarse model + residual composition index | `2711.394` |
| latent op_count beam + residual composition/corrections | `3146.578` |

## Decision

A book-level controller candidate is promoted: book-length constrained residual composition reduces the residual dependency, and the latent op_count coarse beam keeps true coarse sequences above same-multiset controls.

`row0`, translation, plaintext, and the compression bound remain unchanged.

## Remaining External Fields

- per-book op_count if latent beam is not enough to remove it
- coarse sequence corrections when the true sequence misses beam
- literal innovation tape payload and schedule
- copy-hint rank stream
- seed books `0..9`
- `row0`
