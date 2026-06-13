---
page_id: phrase-codebook
page_type: finding
context: bonelord-469
visibility: public_candidate
status: closed
updated_at: 2026-06-13
moc_parent: README.md
source_refs: [rosetta_digit_word_anchors, phrase_level_gt_gate_items]
---

# 4. The Phrase Codebook (Accepted Deliverable)

[← The Two-Cipher Finding](03-two-cipher-systems.md) · [Wiki home](README.md) · Next: [The Book Layer is Non-Linguistic →](05-book-layer-non-linguistic.md)

---

> This is the project's **accepted, frozen deliverable** — the part of 469 that is genuinely (if partially) cracked. It is the NPC **phrase** word-code (Layer B). Full frozen artifact: [docs/469_frozen_deliverable_2026-06-01.md](../469_frozen_deliverable_2026-06-01.md).

## The verified word-codes

Sources: `rosetta_digit_word_anchors`, `rosetta_wordcode_occurrences`. **Zero internal contradictions** (no code maps to two different words).

| Code (digits) | Word | Origin phrase |
|---|---|---|
| 3478 | be | Knightmare — "be a wit than be a fool" |
| 3466 | be | Knightmare (homophone of 3478) |
| 67 | a | Knightmare |
| 0 | a | Knightmare (homophone of 67) |
| 90871 | wit | Knightmare |
| 97664 | than | Knightmare |
| 345 | fool | Knightmare |
| 653 | look | The Evil Eye — "look at you" |
| 768 | at | The Evil Eye |
| 764 | you | The Evil Eye / Elder Bonelord |
| 659 | let | Elder Bonelord — "let me see you" |
| 978 | me | Elder Bonelord |
| 54 | see | Elder Bonelord |

13 code→word entries over **10 distinct words** — **6 attested as rows in the rosetta tables** (`653` look, `768` at, `764` you, `659` let, `978` me, `54` see) and **7 doc-level reconstructions** from the Knightmare segmentation (`3478`/`3466` be, `67`/`0` a, `90871` wit, `97664` than, `345` fool). The earlier `054` "see" variant does **not** exist in the DB and is dropped (see the [final report](../469_final_report.md) §7, correction 3).

## Verified properties

- **Homophony (many codes → one word):** be = {3478, 3466}; a = {67, 0}.
- **Only one code generalizes across phrases:** `764` = "you" is the **only** code that recurs in more than one phrase (The Evil Eye *and* Elder). Every other code appears in exactly one phrase.
- The phrases that segment cleanly: Knightmare (24/24 digits), "look at you" (9/9), "let me see you" (12/12).

## ⚠️ The circularity caveat (important — do not over-read)

The database's "ground-truth gate" (`phrase_level_gt_gate_items`, `gt_pass=1`) is **weaker than it looks**:

- The two passing phrases validate against the **project's own DP-decoder output**, not against any CipSoft-attested English.
- Both are flagged `component_gloss_allowed = 0` and `book_decode_promotable = 0` — **the project itself forbids** deriving word-codes or book semantics from these passes.
- The Knightmare gate masks the "a" slot as `<*>` (decoded_norm = "be a wit than be fool"), so the "a" mapping is weaker than the table implies.
- `Poll2014_C` is **mis-dated** (the primary source is the **2020** poll); its "expected" text is the decoder's self-output; the validation note states "no official translation known."
- The reading "be a wit than be a fool" is **community analysis** (TibiaSecrets / forums), **not** an official translation.

**Net:** the codebook is internally consistent and useful as a *holdout / validation* set, but it is **not externally-attested ground truth at the word level.** This caveat is why the project's honest scoreboard still records the puzzle as unsolved.

## The generalization ceiling

A leave-one-phrase-out test (build the codebook on all phrases but one, predict the held-out phrase): it recovers exactly **one** word — `764` = you. Every other code is confined to a single phrase. So the codebook **cannot bootstrap new translations**; it validates the phrases it was built from and little more. A 2026-06-01 web sweep for additional attested phrase↔English pairs found **none** ([page 7](07-external-sources.md)), so this ceiling is currently unbroken.

---

[← The Two-Cipher Finding](03-two-cipher-systems.md) · [Wiki home](README.md) · Next: [The Book Layer is Non-Linguistic →](05-book-layer-non-linguistic.md)
