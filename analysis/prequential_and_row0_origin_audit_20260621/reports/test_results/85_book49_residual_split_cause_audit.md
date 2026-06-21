# Book 49 Residual Split Cause Audit

Classification: `book49_residual_split_explained_by_fixed_control`
Translation delta: `NONE`

## Purpose

Gate 84 leaves a single residual, book `49`. This audit compares the
two observed prefix variants under fixed local controls to determine
whether item-type or literal-length charges alone close the residual.

## Observed Variants

| Variant | Cutoffs | Type sequence | Length sequence |
|---|---|---|---|
| `coalesced_prefix` | `[35]` | `LCCLCCCLCC` | `[25, 17, 18, 1, 8, 18, 9, 6, 8, 5]` |
| `split_prefix` | `[10, 20]` | `LCLCCLCCCLCC` | `[11, 7, 7, 17, 18, 1, 8, 18, 9, 6, 8, 5]` |

## Control Winners

| Control | Stable winner | Winners by cutoff |
|---|---:|---|
| `observed_payload_mode` | `False` | `{'10': 'split_prefix', '20': 'split_prefix', '35': 'coalesced_prefix'}` |
| `no_literal_length_charge` | `True` | `{'10': 'split_prefix', '20': 'split_prefix', '35': 'split_prefix'}` |
| `no_item_type_charge` | `True` | `{'10': 'split_prefix', '20': 'split_prefix', '35': 'split_prefix'}` |
| `no_item_or_literal_length_charge` | `True` | `{'10': 'split_prefix', '20': 'split_prefix', '35': 'split_prefix'}` |

## Decision

- The sole payload-neutralized residual is a local prefix split in book 49: cutoffs 10/20 choose literal-copy-literal at the start, while cutoff 35 chooses the coalesced 25-digit literal. The fixed local item/literal-length controls are audit-only; they do not emit a corpus formula.
- No compression-bound change is introduced.
- No corpus-wide formula promotion is introduced.
- Row0 remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
