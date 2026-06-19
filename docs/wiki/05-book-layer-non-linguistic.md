---
page_id: book-layer-non-linguistic
page_type: finding
context: bonelord-469
visibility: public_candidate
status: closed
updated_at: 2026-06-18
moc_parent: README.md
source_refs: [audit_20260609/main_audit.out, audit_20260609/dedup_canonical]
---

# 5. The Book Layer is Non-Linguistic

[← The Phrase Codebook](04-phrase-codebook.md) · [Wiki home](README.md) · Next: [Attempts & Dead Ends →](06-attempts-and-dead-ends.md)

---

> **Core result.** The 70-book 14-symbol layer (Layer A) is **not decodable to natural language.** This is a positive, adversarially-verified finding — not merely "we failed to solve it." Five disqualifiers — spanning **three independent axes** (frequency profile, map geometry, sequential structure) — converge, and the number/formula alternative is exhausted. **Verdict: NO-GO on further book decoding.**

## The 14-symbol alphabet and its frequency profile

The book layer outputs 13 real symbols + 1 mask (`*`). Occurrence frequencies across all 5,729 symbols:

| Symbol | Freq | | Symbol | Freq |
|---|---|---|---|---|
| I | 20.2% | | L | 3.7% |
| E | 17.3% | | B | 3.3% |
| N | 12.4% | | `*` (mask) | 2.1% |
| T | 10.4% | | C | 0.8% |
| F | **9.9%** | | R | 0.6% |
| A | 8.5% | | O | 0.2% |
| V | **6.5%** | | | |
| S | 4.3% | | | |

Missing from English entirely: D, G, H, J, K, M, P, Q, U, W, X, Y, Z.

## The five disqualifiers (all independently re-derived)

1. **Profile is closer to flat-random than to any language.** Restricting each reference to the 13 real symbols and renormalizing, chi-square distance: **UNIFORM 3691 < English 4296 < German 4850 < Spanish 9408** (recomputed exactly in the 2026-06-09 audit; these supersede the earlier 4292/4656/9817 figures). The flat-random control fits *better* than every natural language tested.
2. **Per-symbol frequencies are language-disqualifying.** F = 10% (English ~3%, German ~2%), V = 6.6% (English ~1%), I = 20.6% (no language exceeds ~15%), while R = 0.6% and O = 0.2% are near-absent (every language has R 6–9%, O 3–9%). This high-F/high-V, near-zero-R/O signature matches **no** natural language.
3. **The reduced-alphabet / abjad / syllabary escape is closed.** A *meaningless random* 13-class merge of English fits the book's rank-shape (cosine 0.980) *better* than any structured reduction (0.947). The book is also far more peaked (Gini 0.45) than any merge can produce, and its top-3 symbols are vowel-labeled (I, E, A) — so it is not a consonant skeleton. (Note: 13 symbols alone is *not* disqualifying — Hawaiian has 13. The disqualifier is the profile + structure, not the count.)
4. **The only sequential structure is verbatim cross-book templating.** A 19-char fragment appears identically in **12 of 70** books; a 29-char fragment in **9**; a 49-char fragment in **7**; plus tandem repeats (`AIFAIF…`) in 10 books. Conditional entropy sits 0.32 bits below the unigram baseline — but that "structure" is copy-paste of long fixed strings, **not** Markov word/grammar syntax. The `*`-delimited "tokens" average 30 chars (longest 117), with no Zipfian word distribution.
5. **Code→symbol is a reversal-invariant lookup on the *unordered* digit pair.** 89 non-palindrome codes are present; 88 have their digit-reverse present; 86 of those 88 map to the *same* symbol. Also, 54 of 55 unordered-pair classes are pure. A letter cipher has no reason to be reversal-invariant — this is a lookup-table property. And symbol is **not** a function of digit-sum (ds=8 → {E,I,L,N,V}; ds=9 → {F,I,S,T,V}), which refutes a checksum/digit-root number system.

## The substitution-solve attempt (and the anti-pareidolia gate)

We fixed the corroborated anchors B/E/A and searched symbol→letter remaps to maximize English-likeness, under the discipline that any "solve" **must beat a self-anagram control** (shuffle each book's own symbols).

- Result: **NO_CREDIBLE_SOLVE.** Every decode is unreadable gibberish (e.g. `qjewbezzaqxqq…`), at the *shuffled-English* score level, far from real English. The best remap forces the most-frequent symbol I (20.6%) to a rare letter — an anti-English profile. The Knightmare phrase still does not read past "BE A".
- **Honesty correction (recorded):** the self-anagram beat is actually **robust (z ≈ 8–15)**, not marginal — an earlier "z = 2.3 / near-noise" framing was *understated*. But the adversarial verifier proved the beat is driven by the **verbatim templating + extreme skew** (any frequency-aware scorer rewards these), **not** by language. So the verdict is unchanged; we just don't cite "near-noise" as the reason. See [page 8](08-lessons-and-process.md).

## The mathemagic / number-system alternative is exhausted

The in-lore framing ("the language relies on numbers/mathemagic"; the Honeminas formula contains 3478) was tested:

- The project's **≈56 `mathemagic_*` tables** all report **zero** accepted plaintext/gloss. Decisions are uniformly `NO_PLAINTEXT`, `DIES_AFTER_PAIR_CONTROL`, `FAILS_RANK13_HOLDOUT`, `MATHEMAGIC_LOCAL_OPERATORS_ONLY_NO_GLOSS`, `SELECTOR_DEMOTED`.
- Independent tests confirm: codes use 98/100 of the 2-digit space uniformly across decades; within-book deltas show no arithmetic progression (+13 = 0.4%, +49 = 0.2%, *below* the commonest deltas); no mod-N concentration. The only real numeric property is the reversal-invariance lookup (disqualifier #5) — a property of the *alphabet*, not a message-bearing formula.

The 2026-06-18 [Lore Source Audit](10-lore-source-audit.md) keeps this closure:
Honeminas/Tridiag/Donina/Magic Web material may be preserved as
generator/indexer/selector lore only, never as a renewed plaintext-decoder path.
The deeper follow-up also found zero exact hits for the confirmed Secret Library
external pair (`74032`, `45331`, `7403245331`) and for the primary Honeminas
vector strings (`43153`, `34784`, `4315334784`) in the 70-book raw digit corpus.
The [Mechanism & Origin Model](11-mechanism-origin-model.md) formalizes the
surviving generator/index/pair explanation without changing the no-translation
verdict.

## What survives as real (structure, not meaning)

Two genuine positives, preserved as descriptions of the cipher's *mechanics*:

1. The anchors **34=B, 78=E, 67=A**, corroborated by three independent sources, re-unifying the phrase/book layers at the "BE A" prefix.
2. The **reversal-invariant unordered-digit-pair lookup** (54/55 pair-classes pure).

Neither is a path to plaintext.

---

[← The Phrase Codebook](04-phrase-codebook.md) · [Wiki home](README.md) · Next: [Attempts & Dead Ends →](06-attempts-and-dead-ends.md)
