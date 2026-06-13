# Iteration 386 - Add Open-Licensed "Sestina" Corpus Source (Wiki Raw) for Plateau Escape

## Goal
Increase semantic/context coverage around the in-corpus anchor `SESTIEN -> "sestine"` by adding a high-signal external source:
- Wikipedia `Sestina` page (raw wikitext) includes **Arnaut Daniel**, **Provence**, **envoi/envoy**, historical notes, etc.
- We only persist **derived** indices/snippets in the workbook (counts/signatures/bigrams), never full text.

This should improve:
- `LoreSigIndex_PD_Auto` coverage for rare-but-relevant words
- `LoreBigrams_Auto` context model quality
- downstream `SemanticMap_Auto`, `ContextEnglish`, and `SequenceMatches`

## Constraints / Safety
- No leaks / non-public sources.
- No full copyrighted text stored in XLSX.
- StrictPlus DP guardrails unchanged (GT live check + coverage).

## Tasks (Status)
- [x] Add `DEFAULT_WIKI_SESTINA_RAW_URL` and seed it into the plateau corpus ladder (via `_default_pd_sources()`).
- [x] Reorder `_default_pd_sources()` so Wikipedia is scanned first by `AutoPhraseCribs` within its time budget.
- [x] Run `next iteration` (iter386) to trigger:
  - plateau corpus ladder auto-appending this URL into `FlowSettings.LoreFetch_PDSigIndex_ExtraURLs`
  - forced refresh of PD sig-index + bigrams due to fingerprint change
- [x] Validate workbook invariants.
- [x] Report iteration stats with deltas, plus `LoreSigIndex`/`LoreBigrams` row counts and ContextEnglish delta.

## Implementation Notes
- File: `./scripts/bonelord_flow_next_iteration.py`
- Added constant:
  - `DEFAULT_WIKI_SESTINA_RAW_URL = https://en.wikipedia.org/w/index.php?title=Sestina&action=raw`
- Seeded as an extra corpus source (derived-only):
  - `("WIKIPEDIA_SESTINA_RAW", DEFAULT_WIKI_SESTINA_RAW_URL)`

## Implementation Log
- 2026-02-09: Added Wikipedia Sestina raw source to the default PD-style source list (derived-only) to strengthen the semantic/context pipeline.
- 2026-02-09: Iter `386` results:
  - `LoreBigrams_Auto` refreshed: `128,986` rows
  - Display layers changed: `Semantic books_changed=13`, `EnglishLayer books_changed=13`
  - `ContextEnglish avg_score` improved slightly (`6.377957 -> 6.378755`, streak=1)
  - StrictPlus metrics unchanged; validator OK
