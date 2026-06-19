---
page_id: mechanism-origin-model
page_type: finding
context: bonelord-469
visibility: public_candidate
status: closed
updated_at: 2026-06-19
moc_parent: README.md
source_refs: [analysis/mechanism_model_20260618, analysis/lore_audit_20260618]
---

# 11. Mechanism & Origin Model

[<- Lore Source Audit](10-lore-source-audit.md) . [Wiki home](README.md) . Next: [Generator-Origin Search ->](12-generator-origin-search.md)

---

> Post-final mechanism addendum. This page records the best current explanation
> of how the 70-book layer was made. It is **not** a new translation.

## Verdict

The strongest production model is:

```text
handmade 10x10 numeric index table
-> mostly mirror-symmetric unordered-pair symbol lookup
-> fixed homophone classes over a 14-symbol internal alphabet
-> pre-encoded digit chunks / modules
-> copied and spliced book assembly
-> leading-zero omission render pass
```

This model explains the verified structure of the books. It does not assign
meaning to the books, and it does not move any Outcome Ledger translation
metric.

Full generated report:
[`analysis/mechanism_model_20260618/mechanism_model_report.md`](../../analysis/mechanism_model_20260618/mechanism_model_report.md).
Mechanical formula:
[`analysis/mechanism_model_20260618/mechanical_formula_report.md`](../../analysis/mechanism_model_20260618/mechanical_formula_report.md)
and
[`analysis/mechanism_model_20260618/mechanical_formula_469.json`](../../analysis/mechanism_model_20260618/mechanical_formula_469.json).
Syntax-only helper:
[`analysis/mechanism_model_20260618/03_mechanical_generator.py`](../../analysis/mechanism_model_20260618/03_mechanical_generator.py).
Residual coverage/MDL pass:
[`analysis/mechanism_model_20260618/residual_coverage_mdl_report.md`](../../analysis/mechanism_model_20260618/residual_coverage_mdl_report.md).

## What we can say about the language

Accepted facts:

- **469 is not one solved language in the evidence.** The phrase layer and the
  70-book layer are different systems.
- **The phrase/NPC layer is a small word-code.** It has validation-only entries
  such as `653` = look, `768` = at, `764` = you, `659` = let, `978` = me,
  `54` = see, plus doc-level Knightmare reconstructions such as `3478`/`3466`
  = be and `67`/`0` = a.
- **The book layer is a numeric script over 14 internal symbols.** It uses 99 of
  the 100 possible 2-digit cells and reconstructs 70/70 books mechanically.
- **The book table is mirror/pair-driven.** It is not a simple digit-sum or
  arithmetic plaintext channel.
- **The book text was assembled from pre-encoded chunks.** It was not freshly
  encrypted sentence by sentence.

## Numeric index / pair table

The code-symbol grid is generated at
[`analysis/mechanism_model_20260618/code_symbol_grid.md`](../../analysis/mechanism_model_20260618/code_symbol_grid.md).

Key facts:

| Fact | Value |
|---|---:|
| Present 2-digit cells | 99/100 |
| Missing cell | `39` |
| Unordered pair classes | 55 |
| Pure unordered pair classes | 54/55 |
| Non-palindromic present codes | 89 |
| Reverse-available codes | 88 |
| Same-symbol reversals where reverse exists | 86/88 |

The only unordered-pair conflict is `{1,9}`: `19` maps to `I`, while `91` maps
to `N`. Code `93` is present, but its reverse `39` is the missing cell.

Simple feature checks confirm that the table is not explained by a normal
arithmetic formula:

| Feature | Majority accuracy | Errors |
|---|---:|---:|
| unordered pair | 0.990 | 1 |
| digit product | 0.727 | 27 |
| digit sum | 0.444 | 55 |
| digit difference | 0.404 | 59 |
| row/column | 0.273 / 0.263 | 72 / 73 |

That is the core mechanism: a 2-digit index, folded through reversal into
unordered-pair classes.

## Homophone classes

The internal alphabet is `*ABCEFILNORSTV`. Most symbols have multiple numeric
cells:

| Symbol | Code count | Occurrences | Top code |
|---|---:|---:|---:|
| `E` | 17 | 990 | `51` |
| `I` | 15 | 1157 | `19` |
| `N` | 15 | 708 | `46` |
| `T` | 12 | 595 | `61` |
| `A` | 10 | 488 | `14` |
| `V` | 9 | 370 | `36` |
| `F` | 6 | 565 | `21` |
| `L` | 4 | 212 | `35` |
| `B`, `C`, `O`, `R`, `S` | 2 each | variable | variable |
| `*` | 1 | 120 | `00` |

This is a homophone table. The code choices are not a free per-occurrence
message channel; the prior homophone-channel audit showed they are largely
predictable from the fixed text/chunk process.

## Mechanical formula

The reproducible generator is:

```text
D = {00..99} \ {39}
Sigma = *ABCEFILNORSTV
T: D -> Sigma
H(s) = {c in D | T(c)=s}

DecodeCode(c) = T(c)
DecodePair(a,b) = T(ab)
  where T(ab)=T(ba) for every unordered pair except {1,9}
  T(19)=I, T(91)=N, and T(39) is undefined

EncodeSymbols(s1..sn, policy) = concat(select_code(si, policy))

GenerateBook(k) = concat(item_1..item_m)
  item_j = module_ref(Mi) or literal_digit_string
```

The compiled artifact roundtrips all 70 raw digit books exactly. Its canonical
min-length-20 closure has 62 modules, 4,464 module-inventory digits, 127 module
uses, 2,083 literal digits, and 81.5% digit coverage. This is enough to explain
consistent mechanical generation of the book layer. It is not enough to assign
meaning to any generated string.

The generator-origin addendum refines this book-layer formula without changing
the semantic verdict: the 62 literal modules are now representable as 62 slices
of 16 overlap-tape components. The compiled tape-based formula roundtrips
70/70 books, absorbs 107 literal residual digits as exact same-component tape
gaps, and leaves 1,976 literal digits. See
[`tape_based_formula_report.md`](../../analysis/generator_search_20260618/tape_based_formula_report.md)
and [`tape_based_formula_469.json`](../../analysis/generator_search_20260618/tape_based_formula_469.json).
Projected back to the internal code stream, those tapes cover 2,150/2,157 tape
digits with zero code/symbol conflicts; 51/62 module slices align to token
boundaries. The exceptions are real: some module edges cut rendered tokens, and
pair cells `33`/`66` appear only outside the reusable tape layer. This supports
a code-token tape generator with raw-digit edge exceptions, not a semantic
decoder.

The later no-hard-gate matrix search does not recover the exact original
pair-cell placement formula: 294,528 candidates top out at 21/55 hits and
classify as lookup-disguise. So the tape formula explains book manufacture,
not the authorial rule for the 55-cell pair table.

Useful syntax-only commands:

```bash
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/03_mechanical_generator.py lookup-code 19
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/03_mechanical_generator.py encode-symbols ITELBENNA --policy top
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/03_mechanical_generator.py generate-book 1
/opt/anaconda3/bin/python analysis/mechanism_model_20260618/03_mechanical_generator.py decode-codes 196151354351464614
```

The formula also resolves two reporting inconsistencies:

- **86/89 vs 86/88:** 89 non-palindromic present codes exist; 88 have their
  reverse present; 86 of those 88 preserve the symbol. Code `93` has no reverse
  because `39` is the missing cell.
- **m1 vs c2 modules:** exploratory `m1_out.txt` differs slightly from the MDL
  closure. The formula follows the canonical `c2_out.txt` closure: 62 modules,
  4,464 inventory digits, 2,083 literal digits, and 24,627.8 bits.

## Residual coverage / MDL pruning

The follow-up residual audit treats the 2,083 literal digits as a separate
mechanical problem. It produces:

- [`residual_atlas_table.md`](../../analysis/mechanism_model_20260618/residual_atlas_table.md):
  every literal segment with book, offset, raw digits, internal symbols, and
  neighboring modules.
- [`residual_coverage_candidates.json`](../../analysis/mechanism_model_20260618/residual_coverage_candidates.json):
  the full permissive candidate register.
- [`residual_coverage_mdl_report.md`](../../analysis/mechanism_model_20260618/residual_coverage_mdl_report.md):
  Chayenne secondary validation, Avar Tar negative control, and MDL pruning.

Results:

| Layer | Result |
|---|---:|
| Residual digits | 2,083 |
| Residual segments | 115 |
| Phase-1 permissive coverage | 2,083/2,083 |
| MDL-selected residual digits | 1,683 |
| Estimated literal digits remaining | 400 |
| Baseline c2 bits | 24,627.8 |
| Estimated pruned bits | 21,844.3 |

Only `exact_repeat` survives the MDL/control pruning. Short repeats, boundary
glue, zero variants, pair-reverse variants, homophone variants, near matches,
and Chayenne-like overlaps remain recorded as diagnostics or rejected/control
classes. This means the residuals are mostly explainable as additional
digit-copying below the old 20-digit module threshold, not as semantic payload.

Chayenne behaves like secondary validation: 45/49 digits are covered by
minLen=8 book substrings without training on Chayenne. Avar Tar behaves as the
negative control: 0/115 digits are covered by minLen=8 book substrings. Broad
minLen=3 coverage is explicitly rejected because it also covers controls.

## Chunk assembly

The raw digit strings are heavily copied and spliced:

| Model | Modules | Coverage | Literal/novel digits | Unique content | Fully covered books |
|---|---:|---:|---:|---:|---:|
| repeated modules, min length 20 | 62 | 81.5% | 2083 | 6547 | 11 |
| repeated modules, min length 10 | 90 | 88.3% | 1317 | 6164 | 13 |

There are 31 exact raw containment pairs: some whole books are digit substrings
of other books. A same-length shuffle control over the minL=20 extractor gives
0.0% median coverage, so this is not a generic short-string artifact.

The previous MDL audit supplies the decisive compression comparison:

| Model | Bits |
|---|---:|
| two-part module inventory + assembly | 24,627.8 |
| strongest learned tokenizer benchmark | 29,757.1 |
| MIXA1 benchmark | 34,777.3 |
| LZ77-style generative upper bound | 10,678.9 |

The books are cheaper to describe as copied modules/tape spans plus joins than
as any tested message-bearing tokenization. The LZ77-style bound is still lower
because it is a generic compressor, not an auditable human-plausible generator
with named modules, slices, and book recipes.

The tape-based addendum uses its own rough accounting rather than the older
MDL table above: literal module formula `24,350.7` bits, tape-based formula
`17,753.5` bits, rough gain `6,597.1` bits.

## Lore fit

The mechanism model fits the verified lore better than a plaintext-decoder
model:

- `Beware of the Bonelords` says the native tongue is blink-code plus
  mathematics, and that the books contain only numbers.
- `You Cannot Even Imagine` explicitly uses an assembly framing for the
  Bonelord language.
- `The Honeminas Formula` frames Magic Web/gate coordinates with paired numeric
  vectors.
- `74032 45331` is confirmed as an external unglossed Secret Library numeric
  book, but is absent from the 70-book raw corpus.

Correct interpretation: the lore may describe the **manufacturing style** of
the numeric language, not a hidden readable plaintext in the 70 books.

## Remaining useful work

Only mechanism/origin work remains productive without official ground truth:

1. Fit explicit symmetric-table construction hypotheses to the 10x10 grid and
   penalize complexity.
2. Treat future official 469 strings as generator-classification cases: same
   table, same modules, same omission rules, or only same numeric style?
3. Maintain the official-source watchlist for book glosses, symbol tables, or
   First Dragon-style memoir material.
4. Keep weird-language and numerology material as negative controls.

## Verdict

We advanced the explanation of **how it was probably made**:

- indexed numeric table;
- mirror/unordered pair geometry;
- homophone classes;
- fixed pre-encoded chunks;
- copy/splice assembly.

We did **not** find a new translation, new accepted word, or new book meaning.

---

[<- Lore Source Audit](10-lore-source-audit.md) . [Wiki home](README.md) . Next: [Generator-Origin Search ->](12-generator-origin-search.md)
