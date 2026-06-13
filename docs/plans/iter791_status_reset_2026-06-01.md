# iter791 — Status Reset & Honest Re-baseline (2026-06-01)

Records the outcome of the Fork A follow-through round (book-crib hunt, BENNA gloss, GT-phrase growth, alignment fix) and the resulting status changes. Companion to `docs/469_frozen_deliverable_2026-06-01.md`.

## Round result: NEGATIVE / plateau confirmed
No net-new **semantic** ground truth. Verified independently (read-only, re-derived in /tmp):
- **Book-crib search → CLOSED-NEGATIVE.** No public source ties a plaintext to a canonical book digit string. Every primary source (tibia.fandom, tibiawiki.com.br, tibiasecrets, s2ward/469, Portuguese community) states the puzzle is **unsolved**. The one published "decoded book" (tibiasecrets/article160) is a non-canonical cross-boundary stitch (Book 39 + a 15/16 fragment) and forced English.
- **BENNA/TELBENNA/ENNAI → no external gloss; internal artifacts only.** Confirmed not Tibia vocabulary. Closest real handle: HONEMINAS + the 3478 token. Matches the project's own `benna_external_bridge_audit_v1_runs` (exact_external_bridge_count=0).
- **GT-phrase corpus → not extended.** No new attested digit↔English pair. The `764`=you cross-phrase generalization ceiling is intact.

## Net-new POSITIVE (structural, not semantic)
- **12-book off-by-one reconstruction → RESOLVED 70/70.** `row0_code_symbol_probe_books` shows `valid=1`, `consumed_digits == digitslen` for all 70; independent reconstruction (insert leading zero at each `omitidxs_1based` position, consume 1 digit there / 2 elsewhere) matches the canonical code stream for the formerly-failing books (2,10,13,14,18,19,27,35,55,57,…). This is a STRUCTURAL fix only — it produces no translation.

## Correction logged
Earlier in-session framing called the phrase codebook / "be a wit than be a fool" **ground truth**. Corrected: the phrase gates validate against the project's OWN decoder output (circular), and the reading is community analysis, not a CipSoft translation. The codebook is internally consistent and holdout-useful, but is NOT externally-attested at the word level.

## Status changes (recorded here; DB scoreboard NOT mutated)
- `EXTERNAL_BOOK_CRIB` = **CLOSED-NEGATIVE**
- `BOOK_PROSE_GLOSS` = **STOPPED-PAREIDOLIA** (generation halted under the current letter pipeline)
- Open-problems list: **remove** the 12-book reconstruction failure (resolved 70/70)
- Phrase codebook = **FROZEN / ACCEPTED** (validation-only; see frozen deliverable §2–§3)

> Note: these statuses are recorded in versioned docs (reversible via git) rather than by INSERT/UPDATE into the 1 GB operational SQLite, to avoid mutating core operational state outside the project's own scripts. A DB write can be done as a separate, explicit step if desired.

## Go-forward plan (prioritized)
1. **STOP** mining external sources for a book crib (exhausted) and **STOP** book-prose generation under the letter pipeline (confirmed pareidolia).
2. **FREEZE** the phrase codebook as the accepted artifact; treat GT phrases as holdout/validation only.
3. Treat BENNA/TELBENNA/ENNAI strictly as **internal structural operators**; pursue HONEMINAS-formula structure only as math, never as a gloss.
4. If any further book work is attempted: focus on the now-clean 70/70 code stream + the weak letter-IDENTITY signal (z=+3.67), investigating whether a corrected alignment turns the ambiguous `2-digit→letter` relation (`11`→{A,E,F,I,N,T,V}) into a cleaner function. This is the one open internal question with plausible payoff.
5. The ONLY needle-mover is genuinely new **CipSoft-attested** numeric↔English ground truth — watch official channels (anniversary events, new Bonelord NPCs/items) rather than re-reading exhausted community pages.

## Internal front #1 result (map invertibility → book-layer verdict)
Ran 2026-06-01 (workflow `book-symbol-layer-469`, 5 agents, adversarially verified). Re-derived every number from the canonical DB tables (`row0_code_symbol_counts`, `row0_code_symbol_probe_books`).

**Map invertibility: RESOLVED — and the book layer is VERIFIED NON-LINGUISTIC.**
- Under the canonical code stream the 2-digit→symbol map is perfectly functional: **99 codes → 14 symbols, 0 ambiguous, 5729/5729 positions consistent** (the old "11→7 letters" was wrong alignment). Partly tautological (decodedbase was generated from the counts table) — flagged, not leaned on.
- **Partial two-layer re-unification (real):** book-map on the Knightmare phrase gives `34=B, 78=E, 67=A` — so word-code `3478`="be" = B+E; corroborated by 3 independent sources (book-map, word-gloss, tibiasecrets/article160). But agreement is ONLY on the "BE A" prefix; continuation diverges and adds zero readability.
- **Five independent disqualifiers of natural-language decodability (all re-verified):**
  1. Unigram profile closer to flat-random than any language: UNIFORM χ²=3691 **<** English 4292 < German 4656 < Spanish 9817.
  2. Language-disqualifying per-symbol freqs: F=10.1%, V=6.6%, I=20.6% (no language >~15%), R=0.6%, O=0.2% near-absent.
  3. Reduced-alphabet/abjad/syllabary escape CLOSED: a meaningless random 13-class merge of English fits the book shape (cos 0.980) better than any structured reduction (0.947); top-3 symbols are vowel-labeled.
  4. Only sequential structure = verbatim cross-book templating (a 19-char fragment identical in 12/70 books, 29-char in 9, 49-char in 7) — copy-paste, not Markov syntax.
  5. Code→symbol is a **reversal-invariant function of the unordered digit pair** (86/89 codes; 54/55 pair-classes pure) — a lookup property, not a letter cipher; and NOT a function of digit-sum (refutes checksum/number system).
- **Mathemagic alternative: exhausted.** All 56 `mathemagic_*` tables show 0 accepted plaintext/gloss; decisions uniformly NO_PLAINTEXT / DIES_AFTER_PAIR_CONTROL / FAILS_RANK13_HOLDOUT / STRUCTURAL_ONLY.
- **Honesty corrections logged:** (a) the substitution solve's self-anagram beat is **robust (z=8–15), NOT marginal** (a lane's z=2.3 was understated) — but the beat is driven by templating + skew, NOT language (every decode is gibberish at shuffled-English score level), so the NO_CREDIBLE_SOLVE verdict stands. (b) 13 symbols alone do not prove non-language (Hawaiian has 13); the verdict rests on the profile + templating + lookup structure.

**GO/NO-GO: NO-GO on further book-layer decoding.** Substitution-annealing, more reference languages, and more mathemagic operators are ground already covered and NULL; continuing risks pareidolia. Preserve two real positives as structural findings (not meaning): the B/E/A anchors, and the reversal-invariant digit-pair lookup. The only thing that could overturn the verdict is **external CipSoft ground truth** (an attested book→plaintext pair or the official symbol/meaning table).

## Working-agreement change (see AGENTS.md "Outcome Ledger")
Progress is measured by OUTCOME, not cadence. A round counts as progress only if one of these strictly increases under an honest, reproducible check: (1) cribs reproduced under holdout; (2) codes confirmed by a CipSoft/in-game source (not the project's own decoder, not a fan guess); (3) books crossing NO_PROSE→accepted; (4) GT phrases passing against attested external English. All four are currently **0**. A round that moves none is logged as "NEGATIVE / plateau" — a valid outcome, not a failure to paper over.
