# Bounded Copy-Length Code Compile

Verdict: `controlled_bounded_copy_length_improvement`. Translation delta: `NONE`.

This audit tests a decodable copy-length refinement for the active
contextual formula. After a copy source address is decoded, the decoder
knows both the declared remaining book length and how many emitted digits
exist after that source position. Therefore the legal copy length range is
`min_len..min(remaining_book_digits, emitted_digits_after_source)`.

The candidate replaces unbounded Rice `k=4` copy lengths with a canonical
truncated-binary code over that bounded range. The copy recipe, addresses,
book lengths, literal payload model, and item-type model are unchanged.

## Result

- Current formula bits: `8803.1`
- Bounded formula bits: `8614.1`
- Gain: `189.0` bits
- Previous Rice copy-length bits: `1860.0`
- Bounded copy-length bits: `1671.0`
- Copy items: `281`
- Forced singleton copy lengths: `3`
- Singleton saved Rice bits: `15`

## Top Per-Copy Savings

| Rank | Book | Op | Length | Max length | Rice bits | Bounded bits | Saved bits |
|---:|---:|---:|---:|---:|---:|---:|---:|
| `1` | `35` | `1` | `276` | `276` | `21` | `9` | `12` |
| `2` | `9` | `0` | `204` | `294` | `17` | `8` | `9` |
| `3` | `66` | `0` | `210` | `210` | `17` | `8` | `9` |
| `4` | `53` | `1` | `155` | `155` | `14` | `8` | `6` |
| `5` | `8` | `9` | `5` | `5` | `5` | `0` | `5` |
| `6` | `12` | `13` | `5` | `5` | `5` | `0` | `5` |
| `7` | `17` | `2` | `133` | `258` | `13` | `8` | `5` |
| `8` | `22` | `0` | `137` | `137` | `13` | `8` | `5` |
| `9` | `26` | `3` | `144` | `144` | `13` | `8` | `5` |
| `10` | `27` | `0` | `124` | `124` | `12` | `7` | `5` |
| `11` | `32` | `2` | `123` | `123` | `12` | `7` | `5` |
| `12` | `33` | `0` | `134` | `134` | `13` | `8` | `5` |
| `13` | `46` | `0` | `117` | `124` | `12` | `7` | `5` |
| `14` | `47` | `0` | `126` | `126` | `12` | `7` | `5` |
| `15` | `48` | `1` | `146` | `146` | `13` | `8` | `5` |
| `16` | `49` | `11` | `5` | `5` | `5` | `0` | `5` |
| `17` | `50` | `0` | `141` | `141` | `13` | `8` | `5` |
| `18` | `52` | `1` | `129` | `129` | `12` | `7` | `5` |
| `19` | `58` | `3` | `132` | `132` | `12` | `7` | `5` |
| `20` | `59` | `0` | `141` | `272` | `13` | `8` | `5` |

## Interpretation

The improvement is a coding-bound refinement, not a new parse or text
claim. It is decodable because the bound is known before the copy length
is decoded once the source address has been read. It does not introduce
plaintext, row0 meaning, or authorial intent.

## Promoted Formula

- [`sequential_lz_digit_address_contextual_bounded_copy_length_formula_469.json`](../../sequential_lz_digit_address_contextual_bounded_copy_length_formula_469.json)
