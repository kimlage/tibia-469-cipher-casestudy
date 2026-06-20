# Source Attribution Confidence

Translation delta: `NONE`.

| Level | Use | Can move semantic verdict? |
|---|---|---|
| `CONFIRMED_SOURCE` | Primary/in-game/transcript/wiki source with direct text. | Only if it contains official number-to-text, book-to-text, or symbol-to-meaning ground truth. |
| `AUTHORIAL_DIRECT` | Knightmare or CipSoft source speaks directly about their own work. | No, unless it supplies official ground truth. |
| `AUTHORIAL_DIRECT_NPC` | Direct in-game Knightmare/NPC text; useful as source context but not real-world author self-attestation by itself. | No. |
| `AUTHORIAL_ASSOCIATED` | Quest/area/theme associated with Knightmare/design style. | No. |
| `MECHANISM_CORPUS` | Quest/lore used as mechanical comparandum. | No. |
| `DND_PARALLEL` | Public D&D Beholder mechanism used as candidate inspiration. | No. |
| `PAREIDOLIA_RISK` | Numerology/similarity without source/control. | No; reject or use only as negative calibration. |

## Normalized Registry Fields

`CONFIRMED_SOURCE` means the registry has a usable source/string reference. It
does not mean official semantic authority. The registry therefore also tracks:

- `text_presence`: whether the cited text/string is present.
- `officiality`: official CipSoft, in-game reported, promoted fansite,
  community wiki, fan claim, external reference, or local reproducible report.
- `interpretation_risk`: low, medium, high, or severe.
- `semantic_authority`: `none` or `official_gt`.

Every current source has `semantic_authority: none`.

## Contradiction Policy

Existing repo baselines override new lore interpretations unless the new source
is official ground truth. A new source can be useful when it closes a source
family negatively, adds a reliable unglossed numeric anchor, or supplies a
mechanical hypothesis with controls that is not already covered.

Current contradiction locks:

- Avar Tar remains a negative control, not validation.
- Chayenne remains secondary copy/module compatibility, not plaintext.
- Secret Library `74032 45331` remains an external numeric anchor, not 469
  book plaintext.
- D&D/Beholder parallels cannot prove intent or semantics.
- German/MHG and other fan readings remain rejected unless official ground
  truth appears.
