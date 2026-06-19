# Sprite Eye Count Audit

This closes the review checklist item for sprite capture/counting without
turning sprite art into semantic evidence.

Sprite files were resolved through the public TibiaWiki/Fandom MediaWiki API,
downloaded locally for visual inspection, and reduced to source metadata in
[`sprite_source_manifest.json`](sprite_sources/sprite_source_manifest.json).
The raw sprite binaries are not intended for publication in this repository.

## Manual First-Frame Counts

| Source | File title | First-frame visual count | Confidence | Notes |
|---|---|---:|---|---|
| `bonelord_current` | `File:Bonelord.gif` | 5 peripheral/stalk eyes visible | medium | Current sprite supports a five-channel visual reading if central mouth/face is not counted as an eye. |
| `bonelord_nostalgia` | `File:Bonelord (Nostalgia).gif` | 5 visible eyes if central eye plus four peripheral eyes are counted | medium | Old Beholder/Nostalgia sprite supports a five-eye reading under a different anatomical convention. |
| `elder_bonelord` | `File:Elder Bonelord.gif` | 5 peripheral/stalk eyes visible | medium | Same visual family as current Bonelord; source page records Elder speech strings but this is not a gloss. |
| `evil_eye` | `File:The Evil Eye.gif` | 5 peripheral/stalk eyes visible | medium | Boss sprite appears visually identical/similar to Elder Bonelord in the first frame inspected. |
| `gazer` | `File:Gazer.gif` | 1 central eye visible | high | Useful arity contrast: Gazer/Eye-of-Seven style is not a five-eye K5 source. |
| `eye_of_the_seven` | `File:Eye of the Seven.gif` | 1 central eye visible | high | Page notes it looks like a Gazer; treated as one-eye trap/creature class. |
| `braindeath` | `File:Braindeath.gif` | ambiguous: sealed/central plus appendage eyes | low | Lore says the central eye is sealed and normally used for Bonelord communication; do not use as K5 support. |

## Interpretation

The visual audit is compatible with the arity hypothesis for
Bonelord/Elder/Evil Eye sprites and gives useful negative contrasts for
Gazer/Eye of the Seven. It does not prove the K5 model. The actual row0 tests
still reject K5 and `5x2` as pair-cell label formulas.

Translation delta: `NONE`.
