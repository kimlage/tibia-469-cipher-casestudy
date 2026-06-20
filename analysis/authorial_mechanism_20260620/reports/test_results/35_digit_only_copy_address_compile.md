# Digit-Only Copy Address Compile

Verdict: `controlled_digit_only_copy_address_improvement`. Translation delta: `NONE`.

This audit keeps the current recipe fixed and changes only the absolute
copy-source address coordinate. Since the formula now declares the 70
book lengths, book separators are reconstructable. Copy addresses can
therefore point into the previously emitted digit stream rather than the
previously emitted digit-plus-separator stream.

## Search Summary

| Metric | Value |
|---|---:|
| Current formula bits | `9073.3` |
| Digit-only address formula bits | `9070.8` |
| Delta vs current | `-2.4` |
| Copy items | `280` |
| Previous copy address bits | `3257.3` |
| Digit-only address bits | `3254.9` |
| Address gain | `2.4` |

## Interpretation

The gain is small but decodable: separators no longer need to expand the
absolute address space once book lengths are declared. This tightens the
mechanical generation bound without changing any emitted book digits.

## Boundary

This is a coordinate/cost improvement only. It does not alter row0,
introduce plaintext, or make an authorial-intent claim.
