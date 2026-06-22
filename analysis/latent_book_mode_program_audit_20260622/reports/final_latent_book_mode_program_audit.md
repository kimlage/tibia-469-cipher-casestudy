# Final Latent Book Mode Program Audit

Status: `analysis_only`
Classification: `LATENT_BOOK_MODE_PROGRAM_NOT_PROMOTED`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Can the promoted residual book mode be predicted by a small decoder-visible program, rather than merely paid as a compact joint label?

## Result

The selected book-mode program costs `945.479` bits versus `891.772` global mode bits (`-53.707`). It has `2/20` positive splits and beats shuffled p95: `False` (p95 `-26.211`).

Top1/Beam5/Beam10 recovery is `11` / `64` / `83` over `186` repeated held-out books.

## Decision

The simple latent book-mode program is not promoted. The previous residual coupling clue remains real, but under these features the mode must still be paid as a compact external label rather than generated. It still does not derive exact type:length streams, literal payload, copy hints, row0, plaintext, translation, or compression_bound.

## Reproducible Artifacts

- [01_latent_book_mode_program_gate.py](../scripts/01_latent_book_mode_program_gate.py)
- [01_latent_book_mode_program_gate.json](test_results/01_latent_book_mode_program_gate.json)
- [01_latent_book_mode_program_gate.md](test_results/01_latent_book_mode_program_gate.md)
