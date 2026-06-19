---
page_id: eye-blink-arity-model
page_type: finding
context: bonelord-469
visibility: public_candidate
status: frozen
updated_at: 2026-06-19
moc_parent: README.md
source_refs:
  - analysis/eye_model_20260619
  - analysis/mechanism_model_20260618/mechanical_formula_469.json
---

# 14. Eye/Blink Arity Model

[<- Mechanical Origin Model v1](13-mechanical-origin-model-v1.md) . [Wiki home](README.md)

---

## Verdict

The eye/blink line is a useful mechanism-origin clue, but the tested models do
not recover the row0 pair-table labels below lookup cost. It does not reopen
translation and does not create plaintext.

The strongest version of the hypothesis was:

```text
5 eyes -> C(5,2) = 10 eye pairs -> digits 0..9
two digit events -> 55 unordered row0 cells
```

That arity match is real and worth preserving as a lore bridge. The actual
pair-cell labels still fail the tested K5 and `5x2` origin models.

Translation delta: `NONE`.

## What Was Tested

The post-review source file proposed two concrete arity models:

| Hypothesis | Test artifact | Result |
|---|---|---|
| `5 eyes -> C(5,2)=10` K5 edge model | [k5_eye_pair_model_report.md](../../analysis/eye_model_20260619/k5_eye_pair_model_report.md) | rejected as pair-matrix formula |
| `5 eyes x 2 states=10` eye/state model | [eye_state_5x2_model_report.md](../../analysis/eye_model_20260619/eye_state_5x2_model_report.md) | rejected as pair-matrix formula |

The source registry for future sprite/frame counts is
[eye_count_source_registry.yaml](../../analysis/eye_model_20260619/eye_count_source_registry.yaml).
It intentionally leaves visible eye counts as `TBD_manual` until a specific
frame, orientation, and image source are captured and reviewed.

## Results

| Model | Search space | Best label hits | MDL gain vs lookup | E-layer fit | Control result | Verdict |
|---|---:|---:|---:|---:|---|---|
| K5 eye-pair | 30,240 distinct edge-adjacency mappings | 18/55 | -170.2 bits | F1 0.500 | ordinary under controls | reject formula |
| 5x2 eye-state | 15,120 distinct feature mappings | 20/55 | -153.7 bits | F1 0.538 | ordinary under controls | reject formula |

The K5 run's best majority labels were intuitive but too weak:

| K5 relation | Majority row0 label |
|---|---|
| `same_edge` | `E` |
| `adjacent_edges` | `N` |
| `disjoint_edges` | `T` |

This is a descriptive pattern, not a generator. It explains too few labels and
costs more than storing the table.

## What Survives

The following should remain in the project as mechanism/context:

- Eye/blink lore is compatible with a multi-channel or non-linear code.
- "Enough eyes to blink it" is a plausible arity clue.
- "Subjective viewer" remains relevant to render/orientation hypotheses.
- The row0 55-cell unordered-pair geometry is exactly the right scale for a
  five-eye K5 story, but scale matching is not enough for promotion.

The following are rejected unless new external evidence appears:

- K5 relation classes as the row0 pair-cell formula.
- `5x2` eye/state relation classes as the row0 pair-cell formula.
- Sprite eye count as semantic proof.
- Any plaintext, glossary, or number-to-word claim derived from eye count.

## Future Use

Future work may use this page only as a controlled source-classifier or
watchlist item. A stronger result would need a specific external clue such as
a CipSoft-attested eye mapping, official symbol table, or official
number-to-plaintext pair. Without that, eye/sprite material remains a
mechanism-only weak clue.

---

[<- Mechanical Origin Model v1](13-mechanical-origin-model-v1.md) . [Wiki home](README.md)
