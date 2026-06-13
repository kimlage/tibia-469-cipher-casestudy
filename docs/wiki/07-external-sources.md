---
page_id: external-sources
page_type: log
context: bonelord-469
visibility: public_candidate
status: closed
updated_at: 2026-06-13
moc_parent: README.md
source_refs: [web-sources-cited-in-page]
---

# 7. External Sources & Falsified Solutions

[← Attempts & Dead Ends](06-attempts-and-dead-ends.md) · [Wiki home](README.md) · Next: [Lessons & Process →](08-lessons-and-process.md)

---

> What the wider community has produced, what we could verify, and the one "solution" that looked complete but was correctly rejected.

## The puzzle is publicly unsolved

Every primary source consulted states 469 is unsolved:

- **TibiaWiki (fandom / tibiawiki.com.br):** "still not solved", "none have supplied solid proof".
- **tibiasecrets.com** (the most-developed community analysis): "closer than ever … remains a mystery".
- **s2ward/469** (research repo, the most authoritative public collection): timeline states "No verified complete translations exist"; the author abandoned the decryption hypothesis. Its `books.json` holds 41 raw digit strings with **no titles and no translation fields**.
- **Portuguese community** (linguagem469.wordpress.com, tibiadown): vocabulary *guesses* only; all call it unsolved.

## The German "solution" (arturoornelasb) — FALSIFIED

A GitHub repo (`arturoornelasb/tibia-bonelord-469-cipher`) claims a complete solution: a homophonic **2-digit → German/MHG** map (98 codes → 22 letters), decoding all 70 books to German with names like *Salzberg*, *Weichstein*, *Orangenstrasse*. It looks authoritative (100% mechanical coverage). It is **wrong**, and the project correctly rejected it:

- Applied to the **English** ground-truth cribs, it decodes to **garbage** (Knightmare → `LTENWEETLAED`, 0% overlap with "be a wit than be a fool").
- Its decoded proper names have **no primary Tibia support**.
- Its **own README** disclaims: *"I cannot confirm that the decoded content is the actual intended plaintext"* and admits an "overfitting concern."
- The project's blind validation logged `FAILS_OR_WEAK_INITIAL_BLIND_BASELINES`.

> **Why this matters:** rejecting a tempting 100%-coverage "solution" because it fails two independent ground-truth phrases is the single best methodological decision in the project's history. It is what separates real decipherment from plausible-looking output.

## The one "decoded book" (tibiasecrets/article160) — NOT a usable crib

article160 publishes a decoded book passage ("YE FAST. BE YET YEY EEN FREE…") tied to a digit string. We verified it mechanically against the canonical books:

- The 86-digit source string is **the entirety of Book 39 + a 27-digit fragment** that appears mid-stream inside Books 15 and 16. It is a **cross-boundary stitch**, not a canonical book.
- The readable English is **forced** (the same pareidolia documented on [page 5](05-book-layer-non-linguistic.md)).

So it is **not** a book-crib. It does, however, **independently corroborate** our findings: article160 derives the *same* 13-symbol alphabet (ABCEFILNORSTV) and the *same* anchors (34=B, 78=E, 67=A). Independent convergence on the structure, not the meaning.

## Other external strings (verified, all unglossed)

| String / source | Status |
|---|---|
| **Chayenne** content-designer 2009 reply (`114514519485…`) | genuine book substrings, but a joke non-answer (`:)` `xD`); embeds the meme number 114514. No translation. |
| **Avar Tar** numeric poem | attested utterance, but the source itself says Avar Tar "is known for bragging and telling lies … not true 469." |
| **NARCISSIST** claim (`62792068657272657261`) | absent from all 70 books; also reads as ASCII hex **"by herrera"** — a confirmed DNS-hijack red herring. Two unrelated readings of one string = textbook pareidolia. |
| **2020 poll Option C** (`663 902073…`) | the official source marks it literally `???` — no attested meaning. (Options A and B *do* have meanings; the 469 line C does not.) |
| **"Your True Colour" 2012** (`78567 34334…`) | a genuinely new, uncatalogued digit string — but unglossed. |

## Net external result

**No new usable ground truth exists publicly** — no book-crib, no new attested phrase pair, no external gloss for BENNA. The community has the same digit strings we do and the same wall. This is why the only remaining unlock is *new* CipSoft-attested ground truth ([page 9](09-open-questions.md)).

---

[← Attempts & Dead Ends](06-attempts-and-dead-ends.md) · [Wiki home](README.md) · Next: [Lessons & Process →](08-lessons-and-process.md)
