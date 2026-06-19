# 2026-06-18 lore-source audit addendum

This folder incorporates the 2026-06-18 lore audit into the closed 469 case
study without reopening the decoder.

## Scope

The source report is archived as `source_report_pt.md`. It reviews Great
Calculator, Demona formula/Magic Web material, pair/mirror sources, Secret
Library, Paradox Tower, Spirit Grounds, minotaur mages, Serpentine Tower,
Hellgate matrix material, fake dictionaries, Dreadeye, First Dragon, Imortus,
Robson, and Braindeath/Bonelord-threat lore.

The operational conclusion is narrow:

- no new CipSoft-attested number<->plaintext pair;
- no new book plaintext;
- no new word-level code confirmed externally;
- no Outcome Ledger metric changes;
- several sources are worth preserving as mechanism-lore, controls, or watchlist
  items.

The exhaustive follow-up changed one source status: `74032 45331` is confirmed
as an external untranslated Secret Library Ice Section book, not merely a
secondary note. It still has no translation value and has zero exact hits in the
70-book raw digit corpus.

## Files

| File | Role |
|---|---|
| `source_report_pt.md` | Original Portuguese audit report supplied for incorporation. |
| `00_source_registry.yaml` | JSON-compatible YAML registry of all 16 lore fronts and their gates. |
| `01_source_inventory.py` | Dependency-free validator and inventory generator. |
| `source_inventory.json` | Generated machine-readable inventory. |
| `source_inventory_table.md` | Generated review table. |
| `02_deep_verification.py` | Source/corpus verifier for new numeric fronts. |
| `deep_verification_results.json` | Generated numeric occurrence and control results. |
| `deep_verification_report.md` | Human-readable deep verification addendum. |

## Rebuild

```bash
/opt/anaconda3/bin/python analysis/lore_audit_20260618/01_source_inventory.py
/opt/anaconda3/bin/python analysis/lore_audit_20260618/02_deep_verification.py
```

The first script validates that every entry is classified, has a promotion gate,
and keeps `translation_value` at `NONE`. The second script checks registered
numeric fronts against `analysis/audit_20260609/books_digits.json` and fixed-seed
same-length random controls.

## Verdict

This addendum strengthens a mechanism interpretation: 469 lore is more
compatible with assembled/calculated/formulaic/pair-geometry production than
with hidden human plaintext in the 70 books. It found a confirmed external
unglossed numeric book, but it does not translate anything.
