# Content-Addressed Event Program Gate

Classification: `content_addressed_event_program_not_promoted`
Translation delta: `NONE`
Plaintext claim: `False`
Case reopened: `False`

## Question

Given the promoted online x64 coarse-control stream, can copy events choose prior content chunks so exact length and source derive from the selected chunk, replacing `composition_index + copy_hint/source`?

## Cost Comparison

- Selected content policy: `long_freq_recent`.
- V2 residual being replaced: `3423.183` bits.
- Content-event residual: `3686.781` bits.
- Delta vs v2 residual: `263.598` bits.
- V2 total with online x64 excluding seed: `4299.595` bits.
- New total with online x64 excluding seed: `4563.193` bits.
- Copy content-rank bits: `2649.756`.
- Literal event bits: `1037.025` (`883.633` payload + `153.392` length delimiters).

## Source/Length Derivation

- Copy ops: `208`.
- Source derived from selected content: `208/208`.
- Canonical source equals raw source: `200/208`.
- Candidate count median/mean/max: `31983` / `103813.981` / `1275643`.
- Top-80 content-rank hits: `5/208`.

## Controls

| Control | Metric | Result |
| --- | --- | ---: |
| `random_rank` | observed/p05/p50/p95 | `2649.756` / `2816.392` / `2858.728` / `2891.246` |
| `same_multiset_shuffled_chunks` | observed/p05/p50/p95 | `2649.756` / `2583.502` / `2652.153` / `2723.410` |
| `previous_material_reversed_order` | content available | `196/208` |
| `previous_material_shuffled_digits` | content available | `1/208` |
| `book_order_permuted` | content available | `181/208` |
| `literal_tape_shuffled` | exact chunks after shuffle | `2/53` |

## Prefix Holdout

| Cutoff | Policy | Test copy ops | Content bits | V2 bits | Delta | Top80 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| `20` | `long_freq_recent` | `155` | `2520.403` | `2303.166` | `217.237` | `3` |
| `30` | `long_freq_recent` | `119` | `1953.932` | `1786.763` | `167.170` | `2` |
| `40` | `freq_recent_long` | `80` | `1420.145` | `1274.354` | `145.791` | `0` |
| `50` | `freq_recent_long` | `49` | `870.886` | `774.007` | `96.879` | `0` |
| `60` | `freq_recent_long` | `18` | `282.738` | `234.951` | `47.786` | `0` |

## Decision

`content_addressed_event_program_not_promoted` as a full program. It removes raw source as a field only by replacing it with a larger content-rank tape, so the residual burden moves to chunk content rather than becoming a small generator.

`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.
