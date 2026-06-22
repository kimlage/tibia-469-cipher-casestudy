# GitHub Exact Book Source Hunt

Classification: `exact_book_github_hits_are_corpus_only_no_object_surface_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Summary

Ran `5` exact-string GitHub code searches for representative 469 book prefixes. Found `60` exact text hits across `5` repositories.

The hits are corpus mirrors or community analysis repositories. None exposes the object/container/slot/order layer required to reduce v9.

## Repository Classification

| Repository | Classification | Known Role | Sample Paths |
| --- | --- | --- | --- |
| `s2ward/469` | `TEXT_CORPUS_OR_COMMUNITY_ANALYSIS` | community corpus/alignment repository | 01-books.md, 05-rearrange.txt, 02-align.txt, 04-align.txt |
| `elkolorado/tibia-469-bacca-averages` | `TEXT_CORPUS_OR_COMMUNITY_ANALYSIS` | community corpus/statistics repository | 2grams.py, words.txt, ciphers/tibia/469books.txt, books.txt |
| `caiocrm/469` | `TEXT_CORPUS_OR_COMMUNITY_ANALYSIS` | community analysis repository | data/sequences.txt, data/sequences.txt, data/sequences.txt, bruteforce_matrix_pos.py |
| `elkolorado/tibia-corpus` | `TEXT_CORPUS_OR_COMMUNITY_ANALYSIS` | community text corpus mirror | tibiacorpus.txt, tibiacorpus.txt, tibiacorpus.txt, tibiacorpus.txt |
| `elkolorado/tibialibraries` | `TEXT_CORPUS_OR_COMMUNITY_ANALYSIS` | community library text mirror | 469/index.html, 469/index.html |

## Decision

No `PROMOTED_EXTERNAL_CONTROL_SOURCE` and no v9 reduction.

This closes the easy public-code route: exact book strings are discoverable, but only as text/corpus copies. The needed source remains object-layer or versioned authoring provenance.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
