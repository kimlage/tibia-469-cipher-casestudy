# Chayenne Spacing Audit

Status: `analysis_only`

Translation delta: `NONE`

Plaintext claim: `false`

Case reopened: `false`

## Primary Surface

Source surface:

```text
114514519485611451908304576512282177 [visible emoticon/image separator] 6612527570584 xD
```

The primary-source answer has two numeric blocks separated by a visible
emoticon/image marker and whitespace. This audit tests that visible boundary
as a mechanical boundary only.

## Result

- Joined numeric string occurrence count: `0`
- Valid full split boundaries where both sides are attested book substrings:
  `[36]`
- Source boundary: `36`
- Source boundary is unique full split: `True`

| chunk | length | occurrences | book:start hits |
| --- | --- | --- | --- |
| block_1 | 36 | 11 | 1:16, 8:6, 10:165, 19:48, 27:13, 31:143, 35:172, 37:55, 41:72, 63:53, 66:165 |
| block_2 | 13 | 9 | 2:111, 5:72, 9:70, 22:73, 28:21, 46:207, 48:44, 51:217, 53:188 |

## Repetition Rank

| target | length | target count | max count | unique substrings | count >= target | top fraction |
| --- | --- | --- | --- | --- | --- | --- |
| block_1 | 36 | 11 | 13 | 3628 | 63 | 0.017365 |
| block_2 | 13 | 9 | 18 | 2592 | 452 | 0.174383 |
| joined | 49 | 0 | 11 | 3751 | n/a | n/a |

## Negative Controls

| control | trials | hits | hit rate |
| --- | --- | --- | --- |
| block_1 | 2000 | 0 | 0.000000 |
| block_2 | 2000 | 0 | 0.000000 |
| joined | 2000 | 0 | 0.000000 |
| joined_valid_full_split | 1000 | 0 | 0.000000 |

## Selection Logic

| chunk | earliest book:start | common left | common right | common extended len | extended hits | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| block_1 | 1:16 | 2 | 0 | 38 | 11 | recurring stem with variable continuations |
| block_2 | 2:111 | 21 | 33 | 67 | 9 | internal slice of a stable repeated template |

The two selected chunks are not a contiguous book quote. Their first attested
occurrences are in consecutive early books (`1` and `2`), and the source answer
joins them with emoticons. Block 1 behaves like a recurring stem with variable
continuations; Block 2 is an internal slice of a larger stable repeated
template.

## Pair And Binary Alignment

- Block 1 pairs from start: `['11', '45', '14', '51', '94', '85', '61', '14', '51', '90', '83', '04', '57', '65', '12', '28', '21', '77']`
- Block 2 pairs from start: `['66', '12', '52', '75', '70', '58', '4']`
- Block 2 pairs with leading zero: `['06', '61', '25', '27', '57', '05', '84']`
- Block 2 pairs with trailing zero: `['66', '12', '52', '75', '70', '58', '40']`
- Joined pairs from start: `['11', '45', '14', '51', '94', '85', '61', '14', '51', '90', '83', '04', '57', '65', '12', '28', '21', '77', '66', '12', '52', '75', '70', '58', '4']`

Binary/integer profiles are included in the JSON. The relevant finding is that
the second block and the joined string are not naturally 2-digit aligned, and
the integer bit lengths do not produce a clean 5-bit eye grouping.

## Decision

Classification: `PROMOTED_MECHANICAL_CLUE`

Narrow claim:
`chayenne_primary_separator_marks_unique_join_between_two_attested_book_substrings`

This does not promote word spacing, plaintext, translation, row0 origin, or an
authorial origin formula. It supports a narrower provenance/mechanical clue:
Chayenne's public numeric answer appears to have been assembled from two
existing 469-corpus numeric modules, with the visible source separator preserving
their join.

Row0 status: `unchanged_exogenous`

Translation/plaintext status: `NONE`
