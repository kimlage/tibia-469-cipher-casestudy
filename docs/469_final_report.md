# The Tibia "469" Bonelord Cipher — Final Report

**Date:** 2026-06-10 • **Status:** FINAL. This document supersedes and consolidates all prior status documents (`docs/469_frozen_deliverable_2026-06-01.md`, `docs/plans/iter791_status_reset_2026-06-01.md`, `docs/wiki/`). It records the complete history of the decode effort, the full evidence stack that **definitively falsifies a natural-language translation of the 70-book corpus**, every attack executed (including the final channel closures of 2026-06-10), the honest corrections made along the way, and exact reproduction paths for every number.

*Not affiliated with or endorsed by CipSoft GmbH; Tibia and Bonelord are trademarks of CipSoft GmbH.*

---

## 0. Executive verdict

1. **The 469 corpus contains two unrelated cipher systems.** The NPC/poll *phrases* are a variable-length digit-group word-code (small codebook recovered, validation-only). The 70 *books* are a fixed 2-digit-code → 14-symbol system, mechanically solved end-to-end (99 codes, zero ambiguity, byte-exact reconstruction 70/70).
2. **The book layer does not encode natural language.** This is a positive, adversarially-verified result resting on five statistical disqualifiers — which span **three independent axes** (frequency profile, map geometry, sequential structure), all holding on the deduplicated corpus — a powered pre-registered language test (real language would score z ≈ +9; the corpus scores +1.3 to +3.0), and a complete null sweep of every standard cryptanalytic attack class — each re-derived at least twice by independent implementations, every positive control-tested against shuffle/permutation nulls.
3. **The corpus is provably reproducible without a message.** A two-part generative code (module inventory + assembly) describes the corpus more cheaply than every competing model tested — by ~5,130 bits (~17%) over the strongest tokenization (the LEARNED unigram-lexicon, 29,757 bits) and by 10,149 bits (29%) over the weaker insertion-free MIXA1 lexicon — while the same test *loses* on genuine language controls; the books were assembled by copying pre-encoded digit strings from a fixed text→code lexicon (§6.4, §6.1). What is not copy-paste (~995 symbols) independently fails every language gate.
4. **Every internal attack surface is closed**, including the last two channels (homophone-selection keying: **per-occurrence capacity 0 bits**, with a one-shot residual of ≤~1,460 bits that is unreadable as language; and the residual "German-like" order signal: repeated-motif structure, not language), both closed 2026-06-10 — see §6.
5. **The only thing that could overturn this verdict is external CipSoft-attested ground truth** (an official book→plaintext pair or symbol table). As of 2026-06-09 no such material exists publicly, and the community consensus remains "unsolved."

---

## 1. The puzzle and the corpus

In *Tibia* (CipSoft GmbH, era ~2005–2007 for the relevant content), Bonelords speak a numeric "language" the community calls **469**. It appears in:

- **70 in-game books** (Hellgate / Isle of Kings libraries) — the main corpus: digit strings totaling **11,263 digits**;
- **NPC dialogue** (The Evil Eye, Elder Bonelord, A Wrinkled Bonelord, Avar Tar) and **official poll/event text** (2014/2020 polls, "Your True Colour" 2012);
- in-lore clues: A Wrinkled Bonelord gives its name as `486486`, says `1` = "Tibia", treats `0` as taboo, and ties the language to "mathemagic"; the Honeminas formula contains `3478`.

| Corpus fact | Value | Verification |
|---|---|---|
| Books | 70 (140 DB rows = clean double-export, deduped) | `sheet__books`, sha256-identical export pair |
| Total digits | 11,263 | re-summed from raw strings |
| Decoded symbols | 5,729 | `len(digits) + insertedzeros == 2*baselen` holds **70/70** (195 omitted leading zeros) |
| Symbol alphabet | 14: `ABCEFILNORSTV` + `*` mask | re-derived from digits+map; matches tibiasecrets/article160 independently |
| 2-digit codes used | 99/100 (only `39` absent); 98 ever appear *written* (`07`'s zero is always omitted) | `row0_code_symbol_probe_books` |
| Corpus provenance | byte-exact vs community-canonical s2ward/469 | integrity audit, 2026-06-09 |

The mechanical model ("row0"): re-insert omitted leading zeros at recorded per-book positions, split into fixed 2-digit codes, map through one global 99-entry code→symbol table. This reproduces every book's `decodedbase` **exactly (5,729/5,729 positions, 70/70 books)** and is the verified substrate for everything below.

---

## 2. Timeline of the effort

| When | Phase | What happened | Outcome |
|---|---|---|---|
| ~2005–2012 | (community era) | Books discovered in-game; Kharos library sequence (2006); Chayenne joke reply (2009); "Your True Colour" string (2012); 2014/2020 poll options | Community cracks isolated phrases ("be a wit than be a fool", "look at you", "let me see you" — fan analysis, never CipSoft-confirmed); books resist all attempts |
| 2024 | First attempts (`archive/old_attempts_2024`) | Manual frequency analyses over the s2ward/469 public corpus | No decode; groundwork |
| 2026-02-04 → 2026-03-07 | The spreadsheet flow era (iterations ~137–784; **48,718 logged flow-runs** in `sheet__flowrunlog`; plans `iter159`–`iter477`) | Automated candidate-promotion pipeline: segmentation/base-bucket search, reverse-phrase mining, English-layer ladders, sestina methodology, seqmatch/hint ladders, German-candidate audits, BENNA/anchor families | Built the row0 substrate (the lasting structural asset). Semantically: a long series of `PROMOTED_NO_PROSE` and pareidolia-prone "semi-English"; first plateau admissions (`iter217`, `iter266`) |
| 2026-03 → 2026-05 | Probe/gate era (~554 `sqlite_*` scripts, 1,592 DB tables) | Hundreds of structural probes: contig overlap, slot grammar, formula families (BENNA/NAESE/C68/C86/VINVIN…), external-anchor audits (`human_q1`–`q96`), falsification packages pkg1–pkg8 | All structural-only; promotion gates (`GT bad_enforced=0`, holdout, negative controls) correctly block every semantic promotion |
| 2026-05-08 | External sweep | s2ward corpus audit; Kharos 137-digit sequence catalogued as `NEW_OR_REARRANGED_SEQUENCE_AUDIT_ONLY` | No external ground truth found |
| 2026-05-11 | `iter786`/`iter787` | SQLite consolidation; "human translation routes" | Infrastructure + honest status |
| 2026-05-31 | Fork A decision + project assessment | Two-cipher separation verified with nulls; external German "solution" falsified against GT cribs; activity-over-outcome failure mode diagnosed | Phrase codebook accepted (validation-only); books confirmed a *different* system |
| 2026-06-01 | **Freeze + book-layer verdict** (`iter791`, workflow `book-symbol-layer-469`) | Map invertibility resolved (99→14, zero ambiguity); five non-linguistic disqualifiers established; mathemagic exhausted (56 tables, all NULL); substitution solve = NO_CREDIBLE_SOLVE; Outcome Ledger reform adopted | **NO-GO on book decoding; phrase codebook FROZEN; project wiki + frozen deliverable written** |
| 2026-06-09/10 | **Full adversarial re-audit** (workflow `audit-469-translation-verdict`: 30 agents, 6 lanes, 10 executed attacks, 12 refuter votes, completeness critic) | Every frozen claim re-derived from raw data; methodology coverage audited vs the standard attack tree; blind fresh-eyes attack; external recency sweep; 10 missed/under-tested attacks actually executed with controls | **NO-GO confirmed.** 2 new verified findings (copy-paste generative origin; homophone-rotation scribe behavior); 4 frozen-doc claims corrected; 2 over-claimed "promising" results refuted by the audit's own verifiers |
| 2026-06-10 | **Final channel closures** (this report, §6) | The homophone-selection channel attacked as a key/message carrier; the language-residual contradiction resolved by pre-registered split-half test; 2012 string sourcing; disqualifiers restated on deduplicated corpus; generative MDL contest closed | See §6 — final state of each |

---

## 3. What was actually solved (the accepted positives)

### 3.1 The two-cipher separation (CONFIRMED, with corrected framing)

The phrase layer and the book layer are different systems:

- Decisive long word-codes `90871` (=wit) and `97664` (=than) appear **0/70** as raw substrings of book digits; cross-phrase codes `653` (=look) and `768` (=at) appear **0 times in 11,263 digits** vs a uniform-null expectation of ~11.1 occurrences each (P(0) ≈ e⁻¹¹ ≈ 1.5×10⁻⁵).
- **Corrected framing (2026-06-09 audit):** the absence of `653`/`768` is *itself* a digit-distribution effect, and several other codebook codes DO occur in books — `67`: 189 occurrences in 64 books, `54`: 48 occ / 38 books, `345`: 40 occ / 37 books, `3478`: 24 books — all explained at the book-code level (e.g. `3478` aligned = codes `34|78` = letters B,E; `67` = letter A). Under a code-shuffle null there is **no enrichment of word-codes in books**. The honest statement is *"the books show no use of the word-code system"*, not *"word-codes are absent below chance."* The conclusion (two systems) stands.

### 3.2 The phrase codebook (FROZEN, validation-only — with attestation status)

| Code | Word | Attestation |
|---|---|---|
| 653 / 768 / 764 | look / at / you | **in-DB** (`rosetta_digit_word_anchors`), Evil Eye phrase |
| 659 / 978 / 54 | let / me / see | **in-DB**, Elder Bonelord phrase |
| 3478, 3466 / 67, 0 / 90871 / 97664 / 345 | be (×2) / a (×2) / wit / than / fool | **doc-level reconstruction** from the Knightmare segmentation `3478\|67\|90871\|97664\|3466\|0\|345` (concatenates exactly to the attested 24-digit string); NOT rows in the rosetta tables. The `054` variant does not exist in the DB. |

Internally contradiction-free (no code → two words; homophony be={3478,3466}, a={67,0} is by design). **Hard caveats (verified):** the gt-gate passes validate against the project's *own* decoder output (`component_gloss_allowed=0`, `book_decode_promotable=0` for all passes); the readings are community analysis, never CipSoft-confirmed; only `764`=you generalizes across phrases. Status: **6 entries attested in-DB + 7 reconstructed; useful as holdout, NOT external ground truth.**

### 3.3 The mechanical book model (row0)

Fully solved as *mechanics*: 99 codes → 14 symbols, zero ambiguous codes, deterministic reconstruction 70/70 (the 2026-06-01 structural fix resolved the last 12 books). Two real structural anchors survive: `34`=B, `78`=E, `67`=A (triangulated via book-map + word-gloss + article160 — agreeing only on the "BE A" prefix), and the reversal-invariance property (§4.4).

---

## 4. The falsification stack: why the books provably do not translate

Every item below was re-derived from raw per-book data by at least two independent implementations (2026-06-01 workflow, then again 2026-06-09 audit), with scripts preserved under `analysis/audit_20260609/`. These five disqualifiers span **three statistically independent axes**: the unigram-frequency profile (§4.1–4.3 are three views of the *same* frequency vector — strong, but one observation, not three independent ones), the code→symbol map geometry (§4.4), and the sequential/templating structure (§4.5). The frequency, map, and sequence axes cannot all fail by a single mechanism; together they are conclusive.

### 4.1 Disqualifier 1 — The frequency profile fits *nothing*, and flat-random fits better than any language

Symbol frequencies over all 5,729 symbols (recomputed exactly): I 20.20%, E 17.28%, N 12.36%, T 10.39%, F 9.86%, A 8.52%, V 6.46%, S 4.26%, L 3.70%, B 3.33%, `*` 2.09%, C 0.82%, R 0.56%, O 0.17%.

Chi-square distance vs 13-symbol-restricted renormalized references: **UNIFORM 3691 < English 4296 < German 4850 < Spanish 9408** (recomputed exactly; orderings stable across multiple published frequency tables). A flat-random profile fits the books *better than every natural language tested* — and all four values are astronomically significant at df=12: the profile fits nothing; uniform is merely least-bad.

### 4.2 Disqualifier 2 — Individual symbol rates are language-impossible

F = 9.86% (English 2.2%, German 1.7%, Spanish 0.7%); V = 6.46% (≈5.7× English); I = 20.6% (no natural language exceeds ~15%); while R = 0.56% (every reference language 6–9%) and O = 0.17% (15–50× below every language). No known orthography combines high-F/high-V with near-zero R/O.

### 4.3 Disqualifier 3 — The reduced-alphabet / abjad / syllabary escape is closed

A *meaningless random* 13-class merge of English fits the books' rank-shape (cosine 0.980) better than any structured reduction (0.947); the corpus is more peaked (Gini 0.45) than any merge can produce; the top-3 symbols are vowel-labeled (I, E, A), so it is not a consonant skeleton. (13 symbols alone is not disqualifying — Hawaiian has 13; the profile + structure is.)

### 4.4 Disqualifier 4 — The code→symbol map is a lookup table, not a letter cipher

Swapping the two digits of a code yields the **same symbol for 86/89 non-palindromic codes**; 54/55 unordered digit-pair classes are pure (sole exception {1,9}→{I,N}). A letter cipher has no reason to be reversal-invariant — this is a constructed-table property. Symbol is **not** a function of digit-sum (ds=8 → {E,I,L,N,V}; ds=9 → {F,I,S,T,V}), refuting checksum/digit-root number systems. Dead cells `32/33/38` (≤2 occurrences, deduped z ≈ −5.2/−4.3) plus hyper-enriched `19` (z = +17.7) are a fingerprint of *how the table was built*, not of a message.

### 4.5 Disqualifier 5 — The only sequential structure is verbatim copy-paste, and the corpus is provably a recombination of modules (2026-06-09, survived 3/3 adversarial refuters)

- Identical fragments across books: a 19-char fragment in **12/70** books, 29-char in 9, 49-char in 7 — and stronger: a 106-char fragment identical in 2 books, `ASTFN` in 25.
- **20/70 books are exact digit substrings of other books** (31 containment pairs). A greedy tiling with **62 modules covers 81.5% of all 11,263 digits**; exact LZ dedup leaves only **995/5,729 novel symbols (17.4%)** / 1,305 novel digits (11.6%). Every corpus statistic was therefore ~5× pseudo-replicated (full-corpus numbers remain directionally valid; canonical deduped numbers in §6.4).
- A RePair grammar compresses the symbol corpus to **13,125 bits vs 21,812 baseline (ratio 0.602)**, beating order-2 Markov surrogates by **z = −47.5**; 86.0% of symbols sit in 10-grams shared verbatim across ≥2 books (order-2 Markov control: 2.86%, z = 84; shuffles: ~0%, z = 2475). 80.7% of the corpus is emitted by grammar rules reused across books.
- This is **copy-paste generation, not syntax**: `*`-delimited "tokens" average 30 chars (max 117) with no Zipfian distribution; conditional entropy gains come from long fixed strings, not grammar.

### 4.6 The substitution-solve null (anti-pareidolia gate)

Fixing the corroborated anchors B/E/A and searching all symbol→letter remaps for maximal English-likeness yields **NO_CREDIBLE_SOLVE**: every decode is gibberish (`qjewbezzaqxqq…`) at shuffled-English score level; the best remap forces the most frequent symbol (I, 20.6%) onto a rare letter. The corpus-aggregate self-anagram beat (z = +9.70) reproduces exactly — and is fully explained by templating: a leave-one-out *corpus-trained* bigram model scores 3–5× higher (z mean +6.5) than the English model, and de-templating (the 18 books sharing no 19-char fragment) drops the aggregate to z = +3.38, bottom of the random-subset range. Per-book, no single book beats its own anagram robustly (z range −0.10…+2.29).

### 4.7 The mathemagic / number-system alternative is exhausted

All ≈56 `mathemagic_*` tables: **zero** accepted plaintext/gloss (`NO_PLAINTEXT`, `DIES_AFTER_PAIR_CONTROL`, `FAILS_RANK13_HOLDOUT`, `STRUCTURAL_ONLY`). Independent re-tests: codes show no arithmetic progressions (+13 at 0.4%, +49 at 0.2% — *below* common deltas), no mod-N concentration; the consecutive-code diff-mod-10 anomaly (z = +14.5 vs shuffle) is reproduced *exactly* by code bigram statistics (obs 126.8 vs order-1 Markov 135.6 ± 23.2) — pure production structure, no modular arithmetic.

### 4.8 The 2026-06-09 audit: ten further attack classes executed, with controls

A 30-agent adversarial audit (3 re-derivation lanes, methodology-coverage audit vs the standard cryptanalytic attack tree, a *blind* fresh-eyes attack with no access to project conclusions, external recency sweep, then 10 merged attacks actually executed, each "promising" result attacked by 3 independent refuters):

| # | Attack | Result |
|---|---|---|
| 1 | Module decomposition + generative proof | **PROMISING → SURVIVED 3/3 refuters** (now §4.5) |
| 2 | Code-table dead-cell geometry (straddling-checkerboard / 10×10 generator) | **NULL** — straddle premise refuted; no generator found |
| 3 | Kharos 71st-sequence holdout decode | PROMISING → **REFUTED 2/3** (circular: the sequence is a paste-up of book 2/13 digit material + ~19 novel digits, already catalogued 2026-05-08 as audit-only; shuffle null cannot distinguish copying from mechanics) |
| 4 | Zero-omission side channel (~576 bits hypothesized) | PROMISING → **REFUTED 2/3 as an encoder fact** (the omit/retain choice is predictable from local context at 99.7% in-sample / 92.8% honest LOBO — a real internal regularity, but validated against project-derived labels; honest residual capacity bound ~140 bits not ~10; no readable content either way) |
| 5 | Internal homophonic solve, 99 codes → 26 letters, split-half validated | **NULL — definitive**: held-out transfer fails for English AND German |
| 6 | Book metadata channels (lengths, ordering, clusterid) | **NULL** |
| 7 | Digit-level re-pairing closure (reverse, interleave, columnar w2–40, boustrophedon) | **NULL** |
| 8 | Ottendorf / index-cipher over 33 local Tibia-era lore texts | **NULL** |
| 9 | Markov generator-constraint hunt | **PROMISING → SURVIVED 3/3**: lag-repulsion/run-ceiling close as code-statistics-derivative; residual identified as **proximity-conditioned homophone rotation** (§5.2) |
| 10 | Insertion-free / mixed-length segmentation MDL contest | **NULL** — canonical 2-digit + zero-insertion model wins |

External sweep (EN/PT/DE/ES, to 2026-06-09): no CipSoft-attested pair exists; TibiaSecrets ceased (2024-11); the 2026-03 GitHub "first candidate solution" repo is unverified German-overfit of the same class as the falsified arturoornelasb attempt; no new official Bonelord content.

---

## 5. Verified discoveries about *how* the corpus was made (structure, not meaning)

These survived full adversarial verification and are the project's genuinely novel contributions beyond the negative result:

### 5.1 The books are recombinations from a module inventory (§4.5)
The corpus is generated by copying and splicing ~62 reusable digit modules (plus ~1k novel symbols of joins/filler). This explains the templating, the pseudo-replication, and the cross-book "families" that consumed months of structural probing.

### 5.2 Homophone selection is a fixed text→code lexicon (refined 2026-06-10)
The 2026-06-09 finding: when the same symbol recurs at distance 2–3, the encoder avoids reusing the same homophone code (z = −6.27/−6.51 vs 1,000 within-(book,symbol) permutations); adjacent doubles *reuse* it (z = +2.60); symbol-specific habits (E/I/S/V/F rotate, N/B repeat). The 2026-06-10 channel attack (§6.1) **subsumed this**: the rotation/recency behavior is an epiphenomenon of a *deterministic segment→code-sequence lexicon* — identical text positions get identical codes even in non-copied contexts (95.9% agreement, z = +16.4; one variant cell corpus-wide), and a lexicon+order-2-Markov model predicts 89.8% of all choices held-out. Combined with the reversal-invariant table (§4.4), the dead-cell fingerprint, and the digit-level copying proof (§6.4): **the corpus was produced by composing pre-encoded chunks from a fixed lexicon built once over a hand-made homophone table — not by enciphering fresh text per book.**

### 5.3 Zero-omission is rule-governed (internal regularity)
The omitted-leading-zero placements are predictable from local written context (code, prev-2-digits, next-digit) at 98.2% on clean held-out slots — an internal consistency property of the recorded parses (see caveat in §4.8 row 4). One irreducible exception (book 18, code position 26) looks like an encoder slip.

---

## 6. The final channel closures (2026-06-10)

### 6.1 The homophone-selection channel — CHANNEL_CLOSED: zero per-occurrence capacity; no key; no message

This was the audit critic's "only place a key could still hide": for each symbol with 2–17 homophone codes (5,609 multi-class tokens), *which* code the encoder chose could in principle carry a hidden message. Attacked with a pre-registered decision rule (positives need z ≥ 3 vs matched controls AND must survive dedupe). Three independent legs close it:

1. **The selection is text-keyed and deterministic — there is no per-occurrence freedom.** Across occurrence pairs with identical (segment, index-in-segment) but *non-identical* surrounding digit context (i.e., not verbatim copies), code agreement is **47/49 = 95.9%** vs shuffle control 12.7% ± 5.1% (**z = +16.4**). Exactly **one variant cell exists in the whole corpus** (segment "I" index 0: code `65` in book 1 vs `18` in books 13/57). The choices are a function of the text — a **word/segment → code-sequence lexicon** — so a per-occurrence message channel has **capacity 0 bits**.
2. **Rule competition (leave-one-book-out, 70 folds):** a lexicon lookup with order-2 code-Markov backoff predicts **89.8% of choices (0.547 bits/choice)**; even plain previous-token Markov gets 78.2%. The previously verified rotation/recency behavior (§5.2) is an **epiphenomenon** of this lexicon process (fitted recency weights add only ~2 bits over the whole novel corpus); Gronsfeld-style position keys k=2..26 never beat null. Honest out-of-sample bound on everything a one-shot key could occupy: **≤ ~1,460 bits** (≤1,170 on the strictest leak-free subset) — and that residual is demonstrably *bursty and text-novelty-aligned* (predictability burstiness, normalizing to null under the lexicon model on cross-book-unique material), the opposite of an embedded message's independent residuals.
3. **Readability battery: 0/28 dedupe-surviving positives.** Binary streams of class-2 symbols, per-symbol streams, Baconian 5-bit (both bit orders), ASCII 7/8-bit, IoC, letter-frequency fits (EN+DE), digit re-expansion, residual-rank streams — 5 full-corpus hits all **die on dedupe** (0/28 at |z| ≥ 3 on novel material); residual-rank letter stats are nowhere near language (χ²_EN ≈ 7,414 on 1,116 letters vs ~30–50 for English).

The `19` enrichment and dead cells `32/33/38` also close: in novel material code 19's share drops toward uniform with cross-book homogeneity at z = +0.20, and the dead cells are 1-occurrence lexicon cells — all part of the same extreme frequency skew of the lexicon-generation process, with no extra structure.

**Verdict: CHANNEL_CLOSED.** The homophone "choices" were made **once**, when the lexicon was built — not per occurrence. No key. No message. Scripts: `analysis/audit_20260609/homophone_channel/step1`–`step6` (+ `.out`).

### 6.2 The language-residual contradiction — RESOLVED: no language signal survives a powered, pre-registered test

Three lanes had reported language-residual signals on different objects (EN letter-identity z=+9.70 corpus-wide; German bigram-order z=+4.45 on novel-only text; vs a definitive NULL from the 99-code homophonic split-half solve). A single pre-registered split-half protocol settled it (decision rule fixed before computing: a signal is REAL only if z ≥ +3.00 in **both** halves; object = the deduplicated novel-content segments, 1,743 symbols / 1,625 bigrams, split even/odd by extraction order; 1,000 nulls per statistic):

| Statistic | Half A | Half B | Combined | Verdict |
|---|---|---|---|---|
| EN-identity (vs 1,000 random relabelings) | +1.44 | +1.31 | +1.34 | FAIL |
| EN-order (bigram, vs within-segment shuffles) | +1.87 | +1.68 | +2.52 | FAIL |
| DE-order (bigram, same null) | +2.93 | +2.99 | +3.94 | FAIL (both halves < 3) |
| DE−EN contrast | +1.14 | +1.44 | +1.75 | FAIL |

**Power analysis (the decisive part):** genuine German or English prose pushed through the actual 13-symbol merge at the same sample size yields **z ≈ +9 to +10** on the order tests. The observed DE-order signal (+2.93/+2.99) is **~3.3× weaker than real language** — quantitatively too weak to be language even though it replicates. Moreover, after the 13-symbol merge the DE and EN bigram tables score *real German* about equally (injected-German contrast ≈ 0), so "German-like" was never even identifiable by this instrument.

**Where the signal actually lives:** repeated 4–11-symbol motifs (below the 12-symbol dedup threshold) cover 78% of the "novel" corpus. Under a motif-preserving token-shuffle null, the DE-order signal collapses (combined z +3.94 → **+0.97**; half B −0.47). The "German-like order structure" is generic repeated-motif structure misread through a German bigram table. This also reconciles the homophonic-solve NULL: there is no letter-level language; symbol-level scores persisted only because repeated motifs carry above-average DE-table bigram mass. (Caveat, stated plainly: a motif-preserving null by construction retains the very motifs that produce the signal, so this leg establishes that the signal is *motif-localized*, not that the corpus is independently "not language." The load-bearing argument is therefore the **power gap** — genuine language scores z ≈ +9–10 on this instrument while the corpus scores +1.3 to +3.0 — not the split-half threshold, which the DE-order statistic in fact *replicates* across both halves at z ≈ +2.9.)

**Verdicts:** EN-identity = NOT_REPLICABLE (the +9.70 needed the 5× pseudo-replicated corpus to exist). DE-order = REAL_BUT_NOT_LANGUAGE (motif structure). The NO-GO is *strengthened*: it now rests on a **powered** test — real language would have shown z ≈ +9 here and showed +1.3 to +3.0. Scripts: `analysis/audit_20260609/lang_residual/preregistered_splithalf.py` (+ `.out`).

### 6.3 The 2012 "Your True Colour" string — SOURCED with primary provenance; genuinely novel but too short to inform

The last untested out-of-corpus 469-style string was located and verified at its **primary source**: the 2012-02-24 Wayback snapshot of CipSoft's official news page ([web.archive.org/web/20120224031702/tibia.com news id=1975](https://web.archive.org/web/20120224031702/http://www.tibia.com:80/news/?subtopic=latestnews&id=1975)), where it is **question 10 of the official "Your True Colour" personality quiz**: `78567 34334 989 135 65142` (21 digits; the quiz's own answer options joke about hidden meanings — a Rorschach item, but CipSoft-authored).

Test results (script `analysis/audit_20260609/ytc_2012/ytc_test.py`):
- **Not a paste-up** (unlike Kharos): greedy chunk cover vs all 70 books = **0.000 at every length**; 0 shared 5-grams; longest shared substring 4 = exactly the shuffle-control mean. The entire string is novel.
- **Mechanically compatible but non-discriminative:** parses under the 99-code inventory with the length identity holding (21+1 = 2×11) and zero omission-consistency flags — but shuffle controls parse equally well (z ≈ +0.5–0.6). Group-boundary parse decodes to `IEA VBB TT NL IEL` via the B/E/A anchors — not language. The only hint: ML logprob/token beats controls at z = +1.4–1.65 (P ≈ 0.05–0.07), weakly consistent with same-inventory generation, not significant.

**Verdict: GENUINELY_NOVEL_MATERIAL — novel ≠ informative.** At 21 digits it cannot discriminate cipher mechanics from chance and carries no gloss. It is the only fully out-of-corpus CipSoft-authored 469 string and is preserved as audit material; it changes nothing.

### 6.4 Canonical deduped disqualifiers + the generative proof — CLOSED: the corpus is provably better described as message-free recombination

**Task 1 — disqualifiers restated on the deduplicated corpus** (LZ first-occurrence residual: **995 novel symbols in 162 segments**; pseudo-replication factor of the published numbers = 5.76×). **Nothing weakened — all five disqualifiers HELD:**

| Disqualifier | Full corpus | Deduped (canonical) | Status |
|---|---|---|---|
| Frequency profile | I 20.6, E 17.7, N 12.6, F 10.1, V 6.6, R 0.57, O 0.18 | E 18.8, I 18.8, N 13.2, F 10.5, V 7.1, R 0.51, O 0.41 | HELD (same shape; E/I swap top-2 only) |
| χ² ordering (per-N, scale-free) | UNIFORM 0.658 < EN 0.766 < DE 0.865 < ES 1.677 | **UNIFORM 0.654 < EN 0.806 < DE 0.908 < ES 1.778** | HELD — flat-random margin *widens* |
| Per-symbol anomalies | F/V high, R/O near-absent | F 10.54 (EN-renorm max 2.97), V 7.06 (EN 1.30), R 0.51 (EN 7.99), O 0.41 | HELD at full strength |
| Vowel fraction / Gini | 47.2% / 0.452 | 47.1% / 0.451 | HELD |
| Dictionary coverage (19,322-word lexicon, DP over segments) | — | 36.7% vs random control 34.3% ± 2.2% → **z = +1.09** | HELD — no lexical structure above chance |
| Reversal invariance | 86/88 reverse-pairs same-symbol; 54/55 pure classes | map-level, unaffected | HELD by construction |

**Task 2 — the generative MDL contest, run to a verdict.** A conservative two-part code (62-module inventory fully charged as model cost + per-book assembly description + literals at flat log₂10) describes all 11,263 digits in **24,627.8 bits**, beating the strongest competing description the segmentation contest could produce — the LEARNED unigram-lexicon (29,757.1 bits, the lowest any tokenizer reached) — by **+5,129 bits (~17%)**, and the weaker insertion-free MIXA1 lexicon (34,777.3 bits) by **+10,149 bits (29%)**; an LZ77-style self-referential two-part code reaches **10,678.9 bits (0.95 bits/digit)**, margin +24,098 vs MIXA1. Raw-digit baseline 37,414.9; CANON tokenization 36,736.0. (Neither MIXA1 nor LEARNED is a *language* model — both are alternative tokenizations of the digit stream, and LEARNED ignores the canonical 2-digit boundaries, respecting them in only 5.8% of tokens. They are the toughest non-recombination *descriptions* available, not message hypotheses; the disqualifying fact is that the recombination code G beats them on the real corpus and **loses to them on every control**.)

**The test discriminates** (controls run through the identical pipeline): on genuine English pushed through the actual 14-symbol merge and homophonic code table, on shuffled symbols, and on re-encoded real symbols — the generative code **never wins** (margins −3,040 to −19,347 bits). It wins only on the real corpus. Bonus mechanical proof: the real corpus combines near-uniform homophone usage with massive digit-verbatim repeats — impossible under fresh re-enciphering of repeated text (random homophone choice yields zero digit-verbatim modules in controls). **The books were assembled by copying digit strings, not by re-enciphering repeated text through the table.**

**Verdict: GENERATIVE_PROOF_CLOSED.** The book layer is *provably* more economically described as message-free digit-level recombination than by any message-bearing model tested, and the residual payload that could in principle carry a message (995 symbols ≈ ≤3.8 kbit) independently fails every language gate (Task 1 + §6.2). The NO-GO upgrades from "no solution found" to **"the corpus is reproducible without a message, and what isn't copy-paste isn't language."** Scripts: `analysis/audit_20260609/dedup_canonical/c1_dedup_disqualifiers.py`, `c2_generative_mdl.py` (+ `.out`).

---

## 7. Corrections & honesty ledger

Recorded so no future reader over-trusts the intermediate documents:

1. **"Ground truth" phrase framing (corrected 2026-06-01):** the gt-gate passes are circular (validate against the project's own decoder); "be a wit than be a fool" is community analysis, not CipSoft text.
2. **"Self-anagram beat is near-noise (z=2.3)" (corrected 2026-06-01):** the beat is robust (z 8–15) — but driven by templating, not language; the verdict is unchanged, the *reason* was wrong.
3. **13-entry codebook attestation (corrected 2026-06-09):** only 6 entries exist in the rosetta tables; 7 are doc-level reconstructions; `054` does not exist.
4. **"Word-codes absent 0/70" (corrected 2026-06-09):** true only for 4 codes; others occur but without enrichment (§3.1).
5. **"Digits/codes roughly uniform" (corrected 2026-06-09):** false — digit χ²=938 (df 9; digit `1` is 2.9× digit `3`); aligned code counts range 1–192 (χ²=3911, df 99). The "98/100" figure refers to *written* 2-digit forms.
6. **"12-book reconstruction off-by-one" (resolved 2026-06-01):** a wrong-alignment artifact, as was the older "code 11 → 7 letters" ambiguity claim. Clean 70/70 under the canonical stream.
7. **Kharos "holdout validation" and the zero-omission "side-channel refutation" (refuted 2026-06-09/10):** both over-claimed; retained only in their weakened forms (§4.8).
8. **Frequency-profile χ² exact values** are frequency-table-dependent (German 4656 vs 4850, Spanish 9817 vs 9408 across published tables); the *ordering* is what is claimed and it is stable. The recomputed 2026-06-09 values (UNIFORM 3691 < English 4296 < German 4850 < Spanish 9408) are canonical and supersede the earlier 4292/4656/9817 figures still quoted in the historical wiki and frozen snapshots.
9. **Process failure mode (diagnosed 2026-05-31):** activity-over-outcome — 48,718 flow-runs and 1,592 tables with 0 accepted translations; fixed by the Outcome Ledger (progress = cribs reproduced under holdout / externally-confirmed codes / books crossing to accepted / externally-attested phrase passes — all still 0).
10. **`probe_runs` registry is empty** — probe history must be reconstructed from per-probe `*_runs` tables and script names; a documentation gap noted for any successor.
11. **"Five independent disqualifiers" (refined 2026-06-13, public-release pass):** the five disqualifiers reduce to **three** independent axes — §4.1–4.3 are three views of one frequency vector, not three independent observations (§4). The verdict is unchanged; the independence count was overstated.
12. **Generative-MDL margin comparator (refined 2026-06-13):** the headline +10,149-bit (29%) margin was measured against the weaker MIXA1 lexicon; against the strongest competing tokenization (LEARNED, 29,757 bits) the margin is **+5,129 bits (~17%)** (§6.4, §0.3). The directional result — G wins on the real corpus and loses on every control — is unchanged.
13. **Homophone-channel "capacity 0 bits" (clarified 2026-06-13):** 0 bits is the *per-occurrence* capacity; the **one-shot residual** a key could occupy is bounded at ≤~1,460 bits and is demonstrably unreadable as language (§6.1).

## 8. External claims register

| Claim | Verdict |
|---|---|
| arturoornelasb German/MHG full solution | **FALSIFIED**: decodes the English GT cribs to garbage (Knightmare → `LTENWEETLAED`); self-disclaimed overfit |
| tibiasecrets article160 "decoded book" ("YE FAST. BE YET…") | **NOT a crib**: non-canonical cross-boundary stitch (all of Book 39 + a 27-digit mid-stream fragment of Books 15/16); forced English. Independently corroborates the 13-symbol alphabet and B/E/A anchors |
| NARCISSIST string `62792068657272657261` | absent from all 70 books; also reads as ASCII hex "by herrera" (DNS-hijack red herring) — textbook pareidolia |
| Chayenne 2009 reply | genuine book substrings, joke non-answer |
| Avar Tar poem | attested, but in-lore flagged as lies/"not true 469" |
| 2026-03 GitHub "first candidate solution" (German, 94.6% coverage) | unverified; same overfit class as arturoornelasb; not cited by any source as accepted |
| BENNA / TELBENNA / ENNAI | internal decode artifacts; zero external attestation; closest real lore handle is HONEMINAS |

## 9. What would overturn this verdict

Exactly one thing: **CipSoft-attested numeric↔plaintext ground truth** — an official translation of any book, an official code/symbol table, or a new officially-glossed phrase long enough to test the book map. Watch official channels (anniversary events, new Bonelord NPCs/items); community sources are exhausted. Should such material appear, the row0 mechanical model (§3.3) is the correct, validated substrate to test it against — that part of the work is solid and reusable.

## 10. Reproduction guide

- **Data:** `data/bonelord_operational.sqlite` (1 GB, 1,592 tables; open read-only: `file:...?mode=ro`). Key tables: `sheet__books` (dedupe `GROUP BY bookid`), `row0_code_symbol_probe_books` (canonical code stream + omitted-zero positions, 1-based), `row0_code_symbol_counts` (map), `rosetta_digit_word_anchors` / `rosetta_wordcode_occurrences` (phrase codebook), `phrase_level_gt_gate_items` (gate caveats).
- **Audit scripts (2026-06-09/10):** committed mirror at **`analysis/audit_20260609/`** — re-derivation (`main_audit.py`, `claim7_*.py`), fresh-eyes battery (`s1`–`s11`), module/grammar proof (`m1_modules.py`, `m2_grammar.py`), attacks (`markov_generator_constraint.py`, `homophone_rotation_test.py`, holdout/Kharos pipeline, refuter re-implementations under `refute/`), final closures under `homophone_channel/`, `lang_residual/`, `ytc_2012/`, `dedup_canonical/`.
- **Known pitfall:** SQL queries in this environment can silently return 0 rows — always print row counts.
- **Historical documents:** the project wiki [`wiki/README.md`](wiki/README.md) (9 pages + glossary), the iteration plans [`plans/`](plans/README.md) (67 files, indexed), the earlier snapshot [`469_frozen_deliverable_2026-06-01.md`](469_frozen_deliverable_2026-06-01.md), and [`../AGENTS.md`](../AGENTS.md) (the Outcome Ledger). All are superseded by this report where figures differ.

---

*This report was produced by multi-agent adversarial verification: every quantitative claim was independently re-implemented from the read-only database; every "promising" finding was attacked by three independent refuters before acceptance; honest NULL results and corrections are recorded rather than discarded.*
