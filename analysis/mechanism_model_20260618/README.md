# 2026-06-18 mechanism/origin model addendum

This folder extends the closed 469 case study with an explicit model of how the
70-book layer appears to have been produced. It does not reopen translation.

## Files

| File | Role |
|---|---|
| `01_mechanism_model.py` | Dependency-free mechanism/origin consolidation script. |
| `02_compile_mechanical_formula.py` | Compiles the lossless mechanical formula, book recipes, and consistency register. |
| `03_mechanical_generator.py` | Syntax-only CLI for code lookup, internal-symbol encoding, and book reconstruction. |
| `04_residual_coverage_mdl.py` | Builds the residual atlas, maximum-coverage register, Chayenne/Avar controls, and MDL pruning report. |
| `mechanism_model_results.json` | Generated machine-readable model summary. |
| `mechanism_model_report.md` | Human-readable report. |
| `code_symbol_grid.md` | Generated 10x10 code-to-symbol grid. |
| `mechanical_formula_469.json` | Lossless mechanical generator: code table, homophones, modules, and per-book recipes. |
| `mechanical_formula_report.md` | Human-readable formula plus inconsistency register. |
| `residual_atlas.json` / `residual_atlas_table.md` | The 2,083 literal residual digits by book, offset, symbols, and neighboring modules. |
| `residual_coverage_candidates.json` | Full phase-1 permissive candidate register. |
| `residual_coverage_mdl_results.json` / `residual_coverage_mdl_report.md` | Maximum residual coverage, Chayenne validation, Avar Tar control, and MDL-pruned residual model. |

## Rebuild

```bash
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/01_mechanism_model.py
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/02_compile_mechanical_formula.py
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/04_residual_coverage_mdl.py
```

## Use

```bash
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/03_mechanical_generator.py lookup-code 19
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/03_mechanical_generator.py encode-symbols ITELBENNA --policy top
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/03_mechanical_generator.py generate-book 1
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/03_mechanical_generator.py decode-codes 196151354351464614
```

## Mechanical formula

The compiled formula is intentionally syntax-only:

```text
D = {00..99} \ {39}
T(code) = internal symbol
H(symbol) = {codes mapped to that symbol}
GenerateBook(k) = concat(module_ref(Mi) or literal_digit_string from recipe[k])
```

It roundtrips all 70 raw digit books. It can generate table-consistent
pseudo-469 strings, but it does not generate meanings or translations.

## Residual pass

The 2,083 literal digits left by the minL=20 formula now have a complete atlas
and a two-phase audit:

- Phase 1 allows overlapping broad operators and reaches 100.0% residual
  coverage as an upper bound.
- Phase 2 prunes by MDL and controls. Only `exact_repeat` survives; it explains
  1,683 residual digits and leaves an estimated 400 literal digits.
- Chayenne is secondary validation only; Avar Tar is a negative control.

## Verdict

Best current production model:

```text
handmade 10x10 numeric index table
-> mostly mirror-symmetric unordered-pair symbol lookup
-> fixed homophone classes over a 14-symbol internal alphabet
-> pre-encoded digit chunks / modules
-> copied and spliced book assembly
-> leading-zero omission render pass
```

Translation delta remains `NONE`.
