# Post-Forced-Repair High-Order Exhaustion

Verdict: `post_forced_repair_high_order_not_promoted`. Translation delta: `NONE`.

This audit closes the remaining high-order local frontier after the
forced-length local repair. It exactly rescores compatible sets of
13 through 19 literal-to-copy repairs, and confirms that no compatible
sets exist for sizes 20 through 22. The full active cost model is used:
adaptive literal payload, forced literal lengths, digit-only absolute
copy addresses, copy length coding, and the book-start Markov item-type
stream with deterministic type rules.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `8922.8` |
| Single repair candidates | `22` |
| Compatible sets tested | `180892` |
| Incompatible sets skipped | `916898` |
| Total sets considered | `1097790` |
| Best set size | `13` |
| Best set total bits | `8946.5` |
| Best set delta vs current | `23.7` |

## Results by Size

| Size | Compatible | Incompatible | Best total bits | Best delta |
|---:|---:|---:|---:|---:|
| `13` | `107576` | `389844` | `8946.5` | `23.7` |
| `14` | `49708` | `270062` | `8949.8` | `27.0` |
| `15` | `17816` | `152728` | `8954.1` | `31.3` |
| `16` | `4777` | `69836` | `8957.6` | `34.8` |
| `17` | `902` | `25432` | `8963.3` | `40.5` |
| `18` | `107` | `7208` | `8969.8` | `47.0` |
| `19` | `6` | `1534` | `8977.5` | `54.6` |
| `20` | `0` | `231` | - | - |
| `21` | `0` | `22` | - | - |
| `22` | `0` | `1` | - | - |

## Best High-Order Set

| Book | Op | Book pos | Literal offset | Chunk | Source digit pos | Length | Single delta |
|---:|---:|---:|---:|---|---:|---:|---:|
| `0` | `2` | `60` | `56` | `11800` | `57` | `5` | `1.3` |
| `1` | `4` | `34` | `6` | `57651` | `92` | `5` | `1.8` |
| `2` | `7` | `36` | `2` | `65128` | `50` | `5` | `1.6` |
| `2` | `9` | `71` | `2` | `18003` | `58` | `5` | `0.7` |
| `2` | `9` | `71` | `16` | `72611` | `68` | `5` | `2.1` |
| `2` | `11` | `137` | `19` | `14519` | `164` | `5` | `3.0` |
| `2` | `11` | `137` | `30` | `11216` | `225` | `5` | `1.9` |
| `3` | `4` | `29` | `12` | `60199` | `22` | `5` | `1.1` |
| `3` | `7` | `73` | `5` | `04648` | `374` | `5` | `2.3` |
| `3` | `12` | `107` | `2` | `45765` | `183` | `5` | `3.1` |
| `17` | `1` | `7` | `1` | `477090` | `208` | `6` | `1.0` |
| `57` | `2` | `69` | `18` | `91186` | `46` | `5` | `7.0` |
| `57` | `2` | `69` | `23` | `74519` | `3292` | `5` | `1.8` |

## Interpretation

A high-order set is promoted only if exact rescoring beats the active
forced-length repaired formula. Since the best remaining high-order
set remains worse, the local literal-to-copy frontier is exhausted
for all compatible set sizes above twelve under this cost model.

## Boundary

This is a mechanical recipe audit only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
