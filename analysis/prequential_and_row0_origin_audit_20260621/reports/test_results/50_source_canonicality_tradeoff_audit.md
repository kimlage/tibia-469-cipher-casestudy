# Source Canonicality Tradeoff Audit

Classification: `source_canonicality_explanation_profile_costed_not_promoted`
Translation delta: `NONE`

## Purpose

The latest source-substitution formula is the lower compression bound,
but gate 49 showed it no longer preserves the earlier all-earliest
source pattern. This audit prices the explicit tradeoff: keep the
current source choices, or restore all copy sources to the earliest
legal occurrence of the declared copied chunk.

## Summary

- Copy events: `261`.
- Candidate source options beyond current: `376`.
- Current total bits: `8160.825608`.
- Current earliest-source coverage: `251/261`.
- Current non-earliest source events: `10`.
- All-earliest total bits: `8177.316653`.
- All-earliest delta vs current: `+16.491045` bits.
- Cost per restored earliest event: `+1.649105` bits.
- All-latest negative-control delta vs current: `+40.940777` bits.
- Last three source-substitution gains: `+0.001484` bits.
- Latest source-substitution gain: `+0.000310` bits.
- Latest pair-selector floor: `16.092` bits.

## Non-Earliest Current Sources

| Event | Book | Op | Length | Earliest | Current | Latest | Candidates |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `46` | `7` | `1` | `7` | `401` | `819` | `1077` | `3` |
| `79` | `14` | `2` | `26` | `154` | `1247` | `1855` | `3` |
| `97` | `17` | `0` | `7` | `106` | `413` | `2200` | `4` |
| `128` | `24` | `0` | `36` | `2119` | `3413` | `3413` | `2` |
| `141` | `28` | `4` | `18` | `2397` | `3084` | `3084` | `2` |
| `166` | `34` | `6` | `5` | `183` | `522` | `4952` | `14` |
| `171` | `36` | `1` | `10` | `890` | `1026` | `5437` | `8` |
| `208` | `49` | `6` | `8` | `867` | `2802` | `7687` | `9` |
| `227` | `56` | `5` | `12` | `2234` | `2260` | `4698` | `6` |
| `250` | `62` | `0` | `126` | `424` | `6852` | `6852` | `3` |

## Interpretation

The current formula remains the lower compression bound, but its final
source substitutions are not a cleaner generation explanation. Restoring
all sources to the earliest legal occurrence gives a mechanically simpler
profile and repairs `10` non-earliest events, but costs bits under the
same adaptive source model. This separates the two ledgers explicitly:
the bound is lower, while the all-earliest profile is cleaner but not
promoted as a compression improvement.

## Boundary

- No new formula is emitted.
- Compression bound is unchanged.
- Source canonicality is available as an explanation profile, not as the current bound.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
