# Recipe Externality Audit

Classification: `prequential_validation_is_conditional_on_full_recipe`
Translation delta: `NONE`

## Purpose

This audit quantifies the limitation already declared by the
prequential/row0-origin report: the recipe of literal/copy operations is
fixed from the full-corpus formula. The test is whether the current
prequential evidence proves a full generation method. It does not.

## Bit Accounting

| Bucket | Bits | Share |
|---|---:|---:|
| Active 8558.667-bit formula | `8558.667` | `100.000%` |
| Prequentially scored components | `4285.876` | `50.076%` |
| Fixed recipe / non-learned ledger | `4272.791` | `49.924%` |

Scored components:

| Component | Bits | Events |
|---|---:|---:|
| Copy length | `1631.494` | `283` |
| Literal payload | `2434.095` | `773` |
| Item type | `220.287` | `287` |

Fixed/non-learned ledger:

| Component | Bits |
|---|---:|
| Fixed bits ledger | `620.000` |
| Literal structure without payload | `368.000` |
| Copy address bits | `3284.791` |

## Recipe Inventory

| Measure | Count |
|---|---:|
| Books | `70` |
| Digits | `11263` |
| Recipe ops | `368` |
| Literal runs | `85` |
| Literal payload digits | `773` |
| Copy ops / source addresses | `283` |
| Copied digits | `10490` |

## Holdout Disclosure

Every prefix holdout still receives the held-out recipe structure from the
full formula before scoring the learned components.

| Split | Test books | Test digits | Known ops | Known copy addresses | Known literal runs | Known copied digits | Online gain | Frozen gain |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `prefix_10_future_suffix` | `60` | `9567` | `268` | `221` | `47` | `9329` | `157.027` | `121.828` |
| `prefix_20_future_suffix` | `50` | `7925` | `187` | `162` | `25` | `7808` | `87.175` | `63.548` |
| `prefix_35_future_suffix` | `35` | `5835` | `118` | `101` | `17` | `5752` | `48.465` | `37.014` |
| `prefix_50_future_suffix` | `20` | `3489` | `60` | `53` | `7` | `3443` | `37.628` | `35.170` |
| `prefix_60_future_suffix` | `10` | `1459` | `21` | `19` | `2` | `1455` | `10.399` | `11.078` |

Family holdout failures under the same disclosure:

| Family | Books | Known ops | Known copy addresses | Known literal runs | Known copied digits | Online gain | Frozen gain |
|---|---|---:|---:|---:|---:|---:|---:|
| `hellgate_public_bookcase_33` | `[18, 19]` | `5` | `5` | `0` | `222` | `-2.966` | `-2.940` |
| `hellgate_public_bookcase_6` | `[38, 39]` | `8` | `5` | `3` | `188` | `0.161` | `-0.395` |
| `hellgate_public_bookcase_8` | `[68, 69]` | `2` | `2` | `0` | `283` | `-0.166` | `-0.167` |

## Source Control

- Predictive split accepts precomputed rows: `True`
- Predictive split searches recipe ops: `False`
- Main collects rows from the full formula before splitting: `True`

## Decision

- The current prequential audit is retained as conditional component validation.
- It is not promoted to a full generation method because recipe discovery is external to the test.
- `row0` origin is unchanged and remains exogenous.
- `translation_delta: NONE`; no plaintext or reopening claim is introduced.
