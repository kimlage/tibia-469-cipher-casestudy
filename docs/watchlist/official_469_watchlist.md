---
page_id: official-469-watchlist
page_type: reference
context: bonelord-469
visibility: public_candidate
status: frozen
updated_at: 2026-06-19
source_refs:
  - docs/wiki/09-open-questions.md
  - docs/wiki/10-lore-source-audit.md
---

# Official 469 Watchlist

This watchlist exists only for future official evidence. It is not an invitation
to restart internal decoding work.

## Reopening Triggers

Only these evidence classes can reopen the semantic verdict:

| Trigger | Required evidence | Effect |
|---|---|---|
| Official number-to-plaintext pair | CipSoft/in-game source ties digits to meaning | can move `CODES_CONFIRMED_EXTERNALLY` |
| Official book plaintext | one of the 70 books tied to plaintext | can move `CRIBS_REPRODUCED_UNDER_HOLDOUT` |
| Official symbol table | CipSoft/in-game source maps row0 symbols or numbers | can test book-layer meaning directly |
| Official long glossed phrase | long enough to validate beyond phrase-code circularity | can test phrase/book split |

## Sources To Watch

| Source class | Examples | Current status |
|---|---|---|
| First Dragon / memoir hooks | future official memoir/event text mentioning Bonelord language | watchlist only |
| New Bonelord NPCs or sounds | Elder, Evil Eye, Wrinkled Bonelord, new creature variants | watchlist only |
| Official polls/news/events | new anniversary or 469-related strings | watchlist only |
| Secret Library updates | new numeric books or newly glossed existing numeric books | watchlist only |
| Hellgate/Demona/Paradox updates | new in-game text near known mechanism-lore sources | watchlist only |

## Non-Triggers

- Unglossed numbers alone.
- Fan dictionaries or external translations without CipSoft/in-game proof.
- Short digit overlaps such as two-, three-, or four-digit hits.
- More internal row0/model searches without a new external official clue.

Translation delta: `NONE`.
