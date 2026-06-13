---
page_id: glossary
page_type: reference
context: bonelord-469
visibility: public_candidate
status: closed
updated_at: 2026-06-13
moc_parent: README.md
---

# Glossary

Coined terms and shorthand used across this wiki and the
[final report](../469_final_report.md).

| Term | Meaning |
|---|---|
| **469** | The community name for the numeric "language" spoken/written by Bonelords in *Tibia*, after the in-game item that started it. |
| **Layer A / books** | The 70 in-game "books": long digit strings decoded via a fixed **2-digit code → 14-symbol** map. The non-linguistic layer. |
| **Layer B / phrases** | The NPC dialogue and poll lines: **variable-length digit groups → whole words** (a word-code). The partially-cracked layer. |
| **row0** | The canonical mechanical model of the books: re-insert omitted leading zeros, split into 2-digit codes, map through one 99-entry table. Reconstructs all 70 books byte-exact (5,729/5,729 symbols). |
| **decodedbase** | The 14-symbol string a book decodes to under `row0` (e.g. `ITELBENNAIFIININS…`). |
| **disqualifier** | One of the independent statistical reasons the book layer cannot be natural language (frequency profile, per-symbol rates, reduced-alphabet escape, templating, map geometry). |
| **self-anagram control** | The decisive anti-pareidolia test: shuffle a book's own symbols (keep the multiset) and re-score. If a "readable" decode does not beat an anagram of itself, the method is rewarding letter *frequencies*, not *order* — i.e. it is not finding language. |
| **null control** | A baseline that should contain no signal (random/uniform data of the same shape). A finding must beat the control's **max**, not its average. |
| **holdout** | Keeping some ground truth back, fitting on the rest, and testing prediction on the held-out part. |
| **homophone** | More than one code mapping to the same word (Layer B) or letter (Layer A) — e.g. `be = {3478, 3466}`. |
| **pareidolia** | Seeing meaning (here, language) in noise. The failure mode the whole method is built to refuse. |
| **Outcome Ledger** | The reform that measures progress by *outcome* (cribs reproduced under holdout, externally-confirmed codes), explicitly **not** by activity (iterations, scripts, tables). See [page 8](08-lessons-and-process.md). |
| **NO-GO** | The verdict that no internal method can decode the books to language; only external CipSoft ground truth could reopen it. |
| **reversal-invariant lookup** | A map property: swapping a code's two digits yields the same symbol (86/89 non-palindromic codes). A constructed-table fingerprint, not a letter-cipher behaviour. |
| **generative / MDL proof** | The result that a two-part recombination code (module inventory + assembly) describes the corpus more cheaply than any competing model — and only on the real corpus, never on language controls. |
| **BENNA / TELBENNA / ENNAI** | Strings that dominate the books' `decodedbase` but have **no** external attestation — internal decode artifacts, not Bonelord vocabulary. |
| **HONEMINAS** | The closest *real* lore handle (the Honeminas formula contains `3478`); the likely true origin of the project's "BENNA_FORMULA_FRAME" label. |
| **Bonelord** | An in-game *Tibia* race (floating, many-eyed; called *Beholders* before a 2010 rename) that "speaks" 469. Trademark of [CipSoft GmbH](entities/cipsoft.md). |
| **Hellgate / Isle of Kings / Kharos** | In-game areas whose libraries hold the 70 books. |
| **Knightmare / The Evil Eye / Elder Bonelord / A Wrinkled Bonelord / Avar Tar** | NPCs whose 469 utterances make up the phrase corpus (Layer B). |
| **CipSoft** | The studio behind *Tibia*; the only holder of the ground truth that could overturn the verdict. See [entities/cipsoft](entities/cipsoft.md). |
