# Recent Gates Row0 Compatibility Refresh

Classification: `recent_formula_gates_76_107_row0_unchanged`
Translation delta: `NONE`

## Purpose

This refresh checks gates `76..107` against the independent row0
provenance front. The interval covers multi-cutoff parser validation,
path-stability controls, decoder/source-policy controls, skeleton
dependency ledgers, and the operation-type dependency ledger.

## Decision

- `row0 unchanged`.
- Row0 status: `row0_origin_exogenous_under_current_evidence`.
- Recent advances are book-formula/parser improvements, not row0-origin integration.
- Current compression bound remains `8154.676268` bits.
- No plaintext, translation, fan gloss, or case reopening is introduced.

## Criteria Check

| Criterion | Result |
|---|---|
| `predicts_row0_labels_under_holdout` | `False` |
| `reduces_bits_below_row0_lookup_after_rule_or_anchor_cost` | `False` |
| `explains_39_93_19_91_beyond_existing_surface_clue` | `False` |
| `adds_new_cipsoft_or_authorial_provenance` | `False` |
| `only_improves_book_formula_assuming_row0` | `True` |

## Row0 Evidence Retained

- Lookup baseline: `160.521` bits.
- Full 13-anchor explicit pair+label net: `-11.852` bits.
- Rare-singleton explicit pair+label net: `0.000` bits.
- Provenance decision: `project_row0_provenance_partially_traced_but_cipsoft_origin_untraced`.
- Surface clue decision: `surface_ordered_asymmetry_is_real_but_label_origin_unresolved`.
- Partial worksheet decision: `not_promoted_as_origin_formula_anchor_cost_and_externality_not_paid`.
- Paid anchor decision: `explicit_paid_anchor_model_does_not_beat_lookup`.

## Recent Formula Evidence

- Gates checked: `32` (`76..107`).
- Multi-cutoff parser: `175/175` roundtrip and `175/175` raw-positive suffix evaluations.
- Path stability: `38` stable vs `12` unstable multi-cutoff books before later controls.
- Global item/literal control stable books: `50`, promoted: `True`.
- Skeleton simple-rule coverage promoted: `False`.
- Operation-type residual after availability/exception rule: `3` of `261` fields.
- Length atlas records retained: `261`.

## Taxonomy

| Bucket | Result |
|---|---|
| `PROMOTED_ORIGIN_FORMULA` | none |
| `PROMOTED_MECHANICAL_CLUE` | ordered-surface clue only (`39`, `93`, `19/91`) |
| `WEAK_CLUE` | partial worksheet shape only |
| `REJECTED_CONTROL` | paid anchor reduction; skeleton simple-rule coverage |
| `BLOCKED_NEEDS_EXTERNAL_SOURCE` | CipSoft/authorial row0 origin |
| `AUDIT_ONLY` | gates `76..107`, book formula/parser only |

## Gate Families

| Family | Count |
|---|---:|
| `decoder_rule_and_source_policy_controls` | `10` |
| `parser_validation_and_stability` | `12` |
| `skeleton_dependency_and_type_ledger` | `10` |

## Boundary

The recent formula/parser work remains compatible with row0 being an
accepted mechanical substrate. It does not derive row0, does not
predict pair labels under holdout, does not beat the paid row0 lookup
baseline, and does not add CipSoft/authorial provenance.
