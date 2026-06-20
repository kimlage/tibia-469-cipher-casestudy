# Min-Length-Bounded Copy Address Compile

Verdict: `controlled_min_len_bounded_copy_address_improvement`. Translation delta: `NONE`.

This audit tightens the absolute digit-only source address space in the
active bounded-copy-length formula. A legal copy source must have at
least `min_len` emitted digits available after it, so the last
`min_len - 1` emitted positions cannot be valid source starts.

The candidate keeps the recipe, copy lengths, literal payload model,
item-type model, and book-length ledger unchanged. It replaces the
address space size `emitted_digit_count` with
`max(1, emitted_digit_count - min_len + 1)`.

## Result

- Current formula bits: `8614.133`
- Min-length-bounded formula bits: `8613.067`
- Gain: `1.066` bits
- Previous copy-address bits: `3264.817`
- Min-length-bounded copy-address bits: `3263.751`
- Copy items: `281`

## Top Per-Copy Savings

| Rank | Book | Op | Emitted digits | Legal sources | Saved bits |
|---:|---:|---:|---:|---:|---:|
| `1` | `0` | `1` | `55` | `51` | `0.108934` |
| `2` | `0` | `3` | `131` | `127` | `0.044738` |
| `3` | `1` | `1` | `156` | `152` | `0.037475` |
| `4` | `1` | `3` | `172` | `168` | `0.033947` |
| `5` | `1` | `5` | `214` | `210` | `0.027221` |
| `6` | `1` | `6` | `219` | `215` | `0.026594` |
| `7` | `2` | `1` | `242` | `238` | `0.024045` |
| `8` | `2` | `3` | `252` | `248` | `0.023084` |
| `9` | `2` | `5` | `262` | `258` | `0.022196` |
| `10` | `2` | `6` | `267` | `263` | `0.021777` |
| `11` | `2` | `8` | `300` | `296` | `0.019365` |
| `12` | `2` | `10` | `366` | `362` | `0.015854` |
| `13` | `3` | `0` | `413` | `409` | `0.014041` |
| `14` | `3` | `1` | `420` | `416` | `0.013806` |
| `15` | `3` | `3` | `436` | `432` | `0.013297` |
| `16` | `3` | `5` | `474` | `470` | `0.012226` |
| `17` | `3` | `6` | `481` | `477` | `0.012048` |
| `18` | `3` | `8` | `497` | `493` | `0.011658` |
| `19` | `3` | `9` | `502` | `498` | `0.011542` |
| `20` | `3` | `11` | `511` | `507` | `0.011338` |

## Interpretation

This is a marginal address-space refinement only. It is decodable
because `min_len` and the emitted digit count are known before every
copy source address. It does not introduce plaintext, row0 meaning,
or authorial intent.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_formula_469.json)
