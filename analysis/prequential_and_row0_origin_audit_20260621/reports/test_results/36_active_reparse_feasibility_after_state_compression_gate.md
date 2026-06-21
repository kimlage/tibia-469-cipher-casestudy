# Active Reparse Feasibility After State Compression Gate

Classification: `source_state_frontier_reduced_parser_still_unpromoted`
Translation delta: `NONE`

## Purpose

Gate 35 proved that active copy-source defaults only need
`previous_copy_end`, not the full previous `(source, length)` pair.
This gate asks what that buys operationally for exact active reparse,
and where the parser boundary still remains.

## Summary

- Old reparse state key: `(book_pos, previous_item)`.
- Pre-compression required source state: `(book_pos, previous_item, previous_copy_source, previous_copy_length)`.
- Compressed source state: `(book_pos, previous_item, previous_copy_end)`.
- Source default stream preserved: `2990.838` bits.
- Default/exception counts: `5` / `256`.
- End-default mismatches: `0`.
- Aggregate proxy: `969111171` -> `26758611`.
- Aggregate proxy reduction: `97.239%`.
- End-state proxy remains `313.5x` the old DP state count.
- Max book-level end-state proxy: `614250`.
- All tested suffix books are below `1,000,000` end-state proxy: `True`.
- Cutoff 60 has `9/10` books below `250,000` end-state proxy.

## Prefix Frontier

| Cutoff | Books | Old states | Pair proxy | End proxy | End/old | Max book end proxy | <=100k | <=250k | <=1m |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `10` | `60` | `28881` | `302879952` | `8286852` | `286.9` | `614250` | `35` | `51` | `60` |
| `20` | `50` | `23925` | `256343727` | `7288953` | `304.7` | `614250` | `28` | `42` | `50` |
| `35` | `35` | `17610` | `222810162` | `6068094` | `344.6` | `614250` | `17` | `27` | `35` |
| `50` | `20` | `10527` | `146167728` | `4035321` | `383.3` | `614250` | `10` | `14` | `20` |
| `60` | `10` | `4407` | `40909602` | `1079391` | `244.9` | `258264` | `7` | `9` | `10` |

## Largest Book-Level End-State Proxies

| Cutoff | Book | End proxy | Pair proxy | Old states | Distinct end states | Reduction |
|---:|---:|---:|---:|---:|---:|---:|
| `10` | `58` | `614250` | `24081057` | `819` | `750` | `97.449%` |
| `10` | `53` | `598128` | `29175264` | `816` | `733` | `97.950%` |
| `10` | `51` | `585075` | `27128919` | `807` | `725` | `97.843%` |
| `20` | `58` | `614250` | `24081057` | `819` | `750` | `97.449%` |
| `20` | `53` | `598128` | `29175264` | `816` | `733` | `97.950%` |
| `20` | `51` | `585075` | `27128919` | `807` | `725` | `97.843%` |
| `35` | `58` | `614250` | `24081057` | `819` | `750` | `97.449%` |
| `35` | `53` | `598128` | `29175264` | `816` | `733` | `97.950%` |
| `35` | `51` | `585075` | `27128919` | `807` | `725` | `97.843%` |
| `50` | `58` | `614250` | `24081057` | `819` | `750` | `97.449%` |
| `50` | `53` | `598128` | `29175264` | `816` | `733` | `97.950%` |
| `50` | `51` | `585075` | `27128919` | `807` | `725` | `97.843%` |
| `60` | `66` | `258264` | `13486065` | `633` | `408` | `98.085%` |
| `60` | `65` | `153510` | `5790540` | `510` | `301` | `97.349%` |
| `60` | `64` | `135888` | `2500248` | `456` | `298` | `94.565%` |

## Interpretation

The source-state dimension is no longer the same hard blocker it was in
gate 146: every tested book-level source-state proxy falls below one
million after compression to `previous_copy_end`, and the late cutoff
frontier is substantially smaller. That is enough to justify a future
book-local prototype.

It is not enough to promote exact active reparse. The end-state proxy is
still hundreds of times larger than the old frozen-count DP, and this
gate does not solve adaptive counts, tie-breaking, copy source
selection, copy length declaration, literal payload, or item-type
ledger dependencies.

## Boundary

- No compression-bound change is introduced.
- No parser or recipe-discovery promotion is introduced.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
