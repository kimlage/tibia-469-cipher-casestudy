# Bonelord "469" — Frozen Deliverable (Accepted Artifact)

> ⚠️ **Historical snapshot — superseded by [docs/469_final_report.md](469_final_report.md) (2026-06-10).** Retained for provenance. Some figures here predate the 2026-06-09 audit corrections — e.g. the χ² values 4292/4656/9817 were recomputed to **4296/4850/9408**, the "13-entry codebook" is more precisely **6 attested in-DB + 7 reconstructed**, and the `054` "see" variant does **not** exist in the DB. **Trust the final report wherever they differ.**

**Date:** 2026-06-01  •  **Status:** FROZEN. The 2026-06-01 follow-through round produced **NO net-new semantic ground truth** (no book-crib, no new attested phrase pair, no external BENNA gloss). The result is a confirmed **NEGATIVE / plateau**, plus one structural fix (12-book reconstruction now clean 70/70). What follows is the accepted, **verified-only** content; everything the adversarial verifier rejected is excluded.

---

## 1. The two-cipher finding (CONFIRMED, high confidence)

The puzzle uses **two different, unrelated cipher systems**.

- **Layer B — PHRASES** = variable-length digit-GROUP word-codes. These pass the project's phrase gate. Homophonic (many codes → one word).
- **Layer A — BOOKS** = fixed 2-digit-code → 1-letter homophonic substitution, after re-inserting omitted leading zeros. The books do **NOT** use the word-code system: decisive long codes `90871`=wit, `97664`=than appear **0/70**; cross-phrase codes `653`=look, `768`=at appear **0/70** — far below the ~11/70 chance expectation (Monte Carlo null, independently re-derived). Verdict: **BOOKS_USE_DIFFERENT_SYSTEM.**

---

## 2. ACCEPTED PHRASE CODEBOOK (Layer B) — the frozen deliverable

Sources: `rosetta_digit_word_anchors`, `rosetta_wordcode_occurrences` (170 rows, 8 distinct codes). Internally contradiction-free (no code maps to >1 word).

### 2.1 The verified word-codes

| Code (digits) | Word | Phrase of origin |
|---|---|---|
| 3478 | be | Knightmare "be a wit than be a fool" |
| 3466 | be | Knightmare (homophone of 3478) |
| 67 | a | Knightmare |
| 0 | a | Knightmare (homophone of 67) |
| 90871 | wit | Knightmare |
| 97664 | than | Knightmare |
| 345 | fool | Knightmare |
| 653 | look | The Evil Eye "look at you" |
| 768 | at | The Evil Eye |
| 764 | you | The Evil Eye / Elder Bonelord |
| 659 | let | Elder Bonelord "let me see you" |
| 978 | me | Elder Bonelord |
| 54 / 054 | see | Elder Bonelord |

(13 code→word rows over 10 distinct word-meanings; `be` and `a` are each homophonic with two codes.)

### 2.2 Verified properties
- **Homophony:** be = {3478, 3466}; a = {67, 0}.
- **Only one code generalizes across phrases:** `764` = you is the ONLY code recurring across more than one phrase reference (`rosetta_wordcode_occurrences`: refnames AWB2, Elder1, Elder2). Every other code appears in exactly ONE phrase.
- **Generalization ceiling NOT broken** this round — no new phrase carries an attested English gloss.

### 2.3 GT / anchor phrases
- **Knightmare**: `3478 67 90871 97664 3466 0 345` → "be a wit than be a fool" (24/24 segments).
- **Evil Eye**: `653 768 764` → "look at you" (9/9).
- **Elder Bonelord**: `659 978 54 764` → "let me see you" (12/12).
- **Poll 2020 Option C**: `663 902073 7223 67538 467 80097` — passes roundtrip ONLY against the decoder's own output (see §3).

---

## 3. CAVEAT on the phrase gates (verified circularity — do not over-read)

`phrase_level_gt_gate_items` shows the two `gt_pass=1` phrases validate against the **project's own DP-decoder output**, not against any CipSoft-attested English:
- `component_gloss_allowed = 0` and `book_decode_promotable = 0` for BOTH — the project itself forbids deriving word-codes or book semantics from these passes.
- Knightmare's gate output masks the `a` slot as `<*>` (decoded_norm = "be a wit than be fool"), so the `a` (67/0) mapping is weaker than an unqualified listing implies.
- Poll2014_C is mis-dated in the DB (primary source = 2020 poll); its "expected" text is the decoder's self-output; validation note: "no official translation known."
- The "be a wit than be a fool" reading is community analysis (TibiaSecrets / forums), **NOT** an official CipSoft translation.

**Net:** the codebook is internally consistent and useful as a holdout, but it is **NOT externally-attested ground truth at the word level.**

---

## 4. BOOKS status — 0/70 accepted prose (pareidolia); generation STOPPED

- **13-letter alphabet:** ABCEFILNORSTV (U absent), re-verified across all 70 books' `decodedbase`. Independently matches tibiasecrets/article160's grid alphabet exactly.
- **Letter IDENTITIES** carry weak real signal (beats relabel-control, z=+3.67); **letter ORDER does NOT** (does not beat an anagram of its own letters). Strict (len≥4) dictionary coverage only ~0.18; vowel fraction 0.472.
- **BENNA / TELBENNA / ENNAI are INTERNAL decode artifacts, not Tibia vocabulary.** Book 0 `decodedbase` begins `ITELBENNAIFIININS...`; BENNA appears in 17 books' decodedbase. No external Tibia source attests them. The project's own `benna_external_bridge_audit_v1_runs` agrees (exact_external_bridge_count=0). Closest real lore handle: **HONEMINAS** (a Demona Bonelord whose "Honeminas formula" contains the digits 3478) — likely the real origin of the "BENNA_FORMULA_FRAME" label, but the attested name is HONEMINAS, not Benna.

**DECISION:** book-prose generation under the current letter pipeline is **STOPPED** — its readable English is confirmed forced-reading (pareidolia at sentence level).

---

## 5. Data facts (authoritative, re-verified)
- 70 books, 11,263 digits, 5,729 letters, 37/70 odd-length. Source = `sheet__books.digits` (dedupe 140→70 rows).
- Identity `len(digits) + insertedzeros == 2*baselen` holds **70/70**.
- **Reconstruction now clean 70/70** (the prior "12-book off-by-one" open problem is RESOLVED): `row0_code_symbol_probe_books` shows `valid=1` and `consumed_digits == digitslen` for all 70; independent reconstruction matches the canonical code stream for the formerly-failing books.
- Book 0: digits len 144, decodedbase len 74, insertedzeros 4, omitidxs 15,22,51,72.

---

## 6. What is explicitly NOT claimed
- NOT claimed: any decoded book passage / book plaintext. (The only published "decoded book," tibiasecrets/article160's "YE FAST. BE YET…", is tied to a **non-canonical cross-boundary stitch** = the whole of Book 39 + a 27-digit fragment living mid-stream in Books 15 & 16. Re-verified: `art.startswith(Book39)=True`; the 86-digit string is not equal to / a prefix of / a substring of any of the 70 canonical books.)
- NOT claimed: word-level semantics from the phrase GT passes (forbidden by gate flags).
- NOT claimed: any external gloss for BENNA/TELBENNA/ENNAI (none exists).
- NOT claimed: a clean invertible 2-digit code→letter function (still ambiguous: `11`→{A,E,F,I,N,T,V}).
- NOT claimed: the NARCISSIST string (`62792068657272657261`) as a book — verified absent from all 70; it also reads as ASCII hex "by herrera" (a confirmed DNS-hijack red herring) → two unrelated readings of one string = direct evidence of pareidolia.
- NOT claimed: the arturoornelasb German homophonic decode (self-disclaimed, falsified).

---

## 7. The binding constraint
The plateau is **data-starvation, not effort or tooling.** The only thing that moves the needle is a **CipSoft-attested numeric↔English pair** (anniversary event, new Bonelord NPC/item). Public/community sources are exhausted and universally describe the puzzle as unsolved. See `docs/plans/iter791_status_reset_2026-06-01.md` for the status reset and go-forward plan.
