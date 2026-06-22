---
page_id: mechanical-origin-model-v1
page_type: finding
context: bonelord-469
visibility: public_candidate
status: frozen
updated_at: 2026-06-21
moc_parent: README.md
source_refs:
  - analysis/mechanism_model_20260618
  - analysis/generator_search_20260618
  - analysis/ml_formula_probe_20260618
  - analysis/prequential_and_row0_origin_audit_20260621
  - analysis/row0_origin_parallel_20260621
  - analysis/row0_real_origin_search_20260621
  - analysis/authorial_provenance_audit_20260621
  - analysis/segmentation_decision_audit_20260621
---

# 13. Mechanical Origin Model v1

[<- Generator-Origin Search](12-generator-origin-search.md) . [Wiki home](README.md)

---

## Verdict

The strongest current result is a partial mechanical fabrication model for the
70-book layer. It improves the explanation of how the numeric material was
assembled, but it does not find a translation, a new glossary, a plaintext
channel, or the original compact formula for the 10x10 pair matrix.

This page freezes that state as `mechanical_origin_model_v1`.

## Model Stack

`mechanical_origin_model_v1` is:

```text
row0 code table
+ unordered pair / mirror geometry
+ directed render exceptions ({19,91}, missing 39)
+ homophone classes
+ 16 numeric tape components
+ 62 module slices
+ merged same-component spans
+ exact residual repeats
+ remaining literals
+ zero-rendering support layer
```

The model is mechanical only. It is not a semantic decoder.

## Accepted Mechanical Layers

| Layer | Current evidence | Status |
|---|---|---|
| `row0` code table | 99-entry code->symbol substrate; byte-exact 70/70 reconstruction | accepted mechanical substrate |
| Pair/mirror geometry | 54/55 unordered pairs pure; one conflict `{19,91}`; ordered surface has only missing `39` | accepted render/geometry layer |
| Tape formula | 16 tape components, 62 module slices, 12 tape spans, 70/70 book roundtrip | accepted mechanical formula |
| Literal-reference formula | 36 remaining literal items are replaced by references into existing tape components, saving roughly `1167.4` bits with 70/70 book roundtrip; component-shuffle and random-literal controls save `0.0` bits in 400 runs | controlled mechanical improvement |
| Hierarchical reference formula | 16 tape components are themselves reconstructed by literal runs plus self-references, then the improved book recipes reconstruct 70/70 books at roughly `13858.5` bits | strongest structured tape/module generator |
| Sequential LZ book formula | 70 books are emitted in numeric order as literal runs plus earlier/current-prefix digit references; `10190.0` rough bits, 70/70 roundtrip, digit-shuffle/random controls fail | strong copy/reference upper bound |
| Non-numeric LZ order search | best sampled order saves `186.0` gross bits but costs `332.5` bits to describe as a permutation | rejected unless externally supplied |
| Sequential LZ literal-run cost formula | the same sequential generator is charged by literal runs instead of per-digit literal flags; `9944.0` rough bits, 70/70 roundtrip, and digit-shuffle/random/book-order controls are worse (`p=0.0062`) | strong copy/reference upper bound |
| Sequential LZ dynamic-parse formula | the same run-literal vocabulary is parsed by dynamic programming at fixed `min_len=6`; `9823.3` rough bits, 70/70 roundtrip, digit-shuffle/random controls fail, and book-order support is only moderate (`p=0.0396`) | previous strongest copy/reference upper bound |
| Copy address model search | back-distance, source-delta, and book-relative source addresses all cost more than absolute `source_pos`; next-best tested address model is `11507.9` bits | rejected refinement |
| Copy graph / literal seed atlas | DP LZ edges and literal runs are materialized; `32` source books, `5` same-book copies, and `52/84` literal runs reused later | diagnostic provenance atlas |
| Structured public physical order | partial Hellgate/bookcase orders under DP LZ cost at least `9993.1` bits, worse than numeric `9823.3`; manifest ambiguity blocks authorial-order promotion | rejected refinement |
| Literal seed address model | prior literal-run addressing can reach `9752.8` only without mode bits; decodable mixed ledger costs `10033.8`, worse than numeric `9823.3` | rejected refinement / optimistic clue |
| Literal seed grouped-mode model | grouped mode coding reduces the seed-address penalty, but the best decodable seed-using sparse-run ledger is still `9830.0` bits versus the previous `9823.3` gamma-length DP formula | rejected refinement |
| Copy hub macro model | source-book hubs and target-default source macros cost at least `10326.9` bits even in the optimistic lower bound, worse than the previous `9823.3` gamma-length DP formula | rejected refinement |
| Restricted hybrid vocabulary reparse | declared repeated digit motifs plus LZ references roundtrip 70/70, but the best dictionary-using model is `9840.7` bits, worse than the previous `9823.3` gamma-length DP formula | rejected refinement |
| DP min_len sweep | `min_len=6` remains best in the modern DP sequential LZ sweep; `min_len=5` is nearest at `9827.7` bits, `+4.4` worse | retained parameter |
| Sequential LZ Rice-length formula | copy lengths are encoded with Rice `k=4` after reparsing at `min_len=5`; `9596.5` rough bits, 70/70 roundtrip, `226.8` bits better than gamma-length DP | strongest copy/reference upper bound |
| Copy length grid sweep | broader `min_len=3..12` and Rice `k=0..10` grid retains Rice `k=4`, `min_len=5`; nearest alternate is `9600.0` bits | retained parameter |
| Rice parse copy address models | absolute `source_pos` remains best decodable at `9596.5`; literal-seed no-mode reaches `9549.5` but sparse decodable seed-run costs `9607.1` | rejected refinement / optimistic clue |
| Sequential LZ Rice literal-length formula | literal-run lengths are encoded with Rice `k=3` while copy lengths remain Rice `k=4`; `9545.5` rough bits, 70/70 roundtrip, `51.0` bits better than the prior Rice-length formula | strongest copy/reference upper bound |
| Joint length code grid | `605` joint DP reparses keep copy Rice `k=4`, literal Rice `k=3`, `min_len=5`; nearest alternate is `9552.2` bits | retained parameter set |
| Sequential LZ literal-payload formula | literal digits use an adaptive Dirichlet payload model with `alpha=14`; `9538.0` rough bits, `7.5` bits better than uniform decimal payload cost | strongest copy/reference upper bound |
| Current formula copy address models | absolute `source_pos` remains best decodable at `9538.0`; literal-seed no-mode reaches `9478.6` but sparse decodable seed-run costs `9548.7` | rejected refinement / optimistic clue |
| Sequential LZ literal-to-copy repair formula | one local replacement turns literal `972783` in book `8` into a valid prior copy; `9537.3` rough bits, `0.7` bits better than the literal-payload formula | strongest copy/reference upper bound |
| Post-repair payload alpha sweep | adaptive literal-payload `alpha=14` remains best after the local repair; nearest alternate `alpha=13` is slightly worse | retained parameter |
| Post-repair copy address models | absolute `source_pos` remains best decodable at `9537.3`; literal-seed no-mode reaches `9472.4` but the best sparse decodable seed-run costs `9548.0` | rejected refinement / optimistic clue |
| Literal-to-copy pair repair search | `293` compatible two-repair recipes are tested; the best costs `9538.2`, worse than the one-step repaired formula | rejected refinement |
| Sequential LZ book-length ledger formula | independent gamma-coded book lengths are replaced by signed Rice residuals from declared `anchor=151`, `k=5`; total bound drops to `9073.3` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Multi-anchor book-length ledger search | best decodable multi-anchor length mixture costs `581.0` length bits, `+15.0` worse than the single-anchor ledger | rejected refinement |
| Sequential LZ digit-address formula | book separators are removed from the absolute copy-address space after lengths make them reconstructable; total bound drops to `9070.8` bits | strongest copy/reference upper bound |
| Digit-only copy address models | absolute `source_digit_pos` remains best decodable at `9070.8`; literal-seed no-mode reaches `9006.2` but sparse decodable seed-run costs `9081.5` | rejected refinement / optimistic clue |
| Sequential LZ digit-address literal-repair formula | one local replacement turns literal `57928` in book `13` into a valid prior copy; total bound drops to `9070.1` bits and follow-up one-step repair is worse | strongest copy/reference upper bound |
| Post digit-address repair payload alpha sweep | adaptive literal-payload `alpha=14` remains best after the latest repair; nearest alternate `alpha=13` is slightly worse | retained parameter |
| Post digit-address repair address models | absolute `source_digit_pos` remains best decodable at `9070.1`; literal-seed no-mode reaches `9005.5` but sparse decodable seed-run costs `9080.8` | rejected refinement / optimistic clue |
| Sequential LZ item-type ledger formula | fixed one-bit literal/copy tags are replaced by a declared adaptive two-symbol item-type ledger; total bound drops to `8996.2` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Sequential LZ Markov item-type ledger formula | the literal/copy tag stream is conditioned on the previous item type; total bound drops to `8977.6` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Sequential LZ book-start item-type ledger formula | declared book starts are used as `BOS` context in the item-type ledger; total bound drops to `8972.2` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Sequential LZ literal-force item-type ledger formula | a charged deterministic rule makes literal items force the next in-book item to copy; total bound drops to `8966.7` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Sequential LZ remaining-short item-type ledger formula | a charged deterministic rule makes book suffixes shorter than `min_len=5` force literal item type; total bound drops to `8953.9` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Sequential LZ forced short-suffix literal-length formula | the 8 forced short-suffix literals consume the remaining declared book length, removing redundant length bits; total bound drops to `8922.9` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Sequential LZ forced-length literal-repair formula | one additional local repair turns `65128` in book `12` into a valid prior copy; total bound drops to `8922.8` bits and follow-up one-step repair is worse | strongest copy/reference upper bound |
| Post forced-length repair payload alpha sweep | adaptive literal-payload `alpha=14` remains best after the latest repair; nearest alternate `alpha=13` is `+0.1` bit worse | retained parameter |
| Post forced-length repair copy address models | absolute `source_digit_pos` remains best decodable at `8922.8`; literal-seed no-mode reaches `8855.5` but sparse decodable seed-run costs `8933.5` | rejected refinement / optimistic clue |
| Post forced-length repair pair search | `22` single literal-to-copy candidates produce `227` compatible pairs, but the best pair is `+1.6` bits worse than the active formula | rejected refinement |
| Post forced-length repair triple search | the same `22` candidates produce `1462` compatible triples, but the best triple is `+2.7` bits worse than the active formula | rejected refinement |
| Post forced-length repair quad search | the same `22` candidates produce `6596` compatible quartets, but the best quartet is `+3.9` bits worse than the active formula | rejected refinement |
| Post forced-length repair quint search | the same `22` candidates produce `22168` compatible quintets, but the best quintet is `+5.5` bits worse than the active formula | rejected refinement |
| Post forced-length repair sext search | the same `22` candidates produce `57596` compatible sextets, but the best sextet is `+7.3` bits worse than the active formula | rejected refinement |
| Post forced-length repair sept search | the same `22` candidates produce `118456` compatible septets, but the best septet is `+9.0` bits worse than the active formula | rejected refinement |
| Post forced-length repair oct search | the same `22` candidates produce `195806` compatible octets, but the best octet is `+11.0` bits worse than the active formula | rejected refinement |
| Post forced-length repair nonet search | the same `22` candidates produce `262548` compatible nonets, but the best nonet is `+12.9` bits worse than the active formula | rejected refinement |
| Post forced-length repair decet search | the same `22` candidates produce `286858` compatible decets, but the best decet is `+15.1` bits worse than the active formula | rejected refinement |
| Post forced-length repair eleven-repair search | the same `22` candidates produce `255476` compatible eleven-repair sets, but the best set is `+17.8` bits worse than the active formula | rejected refinement |
| Post forced-length repair twelve-repair search | the same `22` candidates produce `184756` compatible twelve-repair sets, but the best set is `+20.6` bits worse than the active formula | rejected refinement |
| Post forced-length repair high-order exhaustion | compatible set sizes `13..19` are exactly rescored and sizes `20..22` checked; the best remaining set is size `13` at `+23.7` bits and sizes `20..22` have no compatible sets | rejected refinement / frontier closed |
| Sequential LZ literal-payload context formula | final literal payload digits are coded by an adaptive previous-emitted-digit context; total bound drops from `8922.8` to `8842.0` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Sequential LZ literal-payload context-order formula | final literal payload digits are coded by a declared order-2 previous-emitted-digit context; total bound drops from `8842.0` to `8805.7` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Sequential LZ item-type context-order formula | the literal/copy item-type ledger uses a declared order-3 previous item-type context while retaining forced rules; total bound drops from `8805.7` to `8803.5` bits with 70/70 roundtrip | strongest copy/reference upper bound |
| Sequential LZ contextual copy-to-literal repair formula | one short copy of `45765` in book `34` is cheaper as an explicit literal under contextual payload coding; total bound drops from `8803.5` to `8803.1` bits | strongest copy/reference upper bound |
| Post copy-to-literal local frontier | after the contextual copy-to-literal repair, single literal-to-copy, single copy-to-literal, and `13530` copy-to-literal pair edits are all worse | rejected refinement / local frontier closed |
| Contextual copy-address model search | absolute `source_digit_pos` remains best decodable at `8803.1`; literal-seed no-mode reaches `8739.3` but sparse decodable seed-run costs `8813.8` | rejected refinement / optimistic clue |
| Post-contextual parameter resweep | current declared parameters remain best after the copy-to-literal repair: copy Rice `k=4`, literal Rice `k=3`, payload order `2` / `alpha=1`, item-type order `3` / `alpha=2` | retained parameter frontier |
| Sequential LZ bounded copy-length formula | copy lengths are coded with truncated binary over the legal range known after the source address is decoded; total bound drops from `8803.1` to `8614.1` bits | strongest copy/reference upper bound |
| Sequential LZ min_len-bounded address formula | absolute copy source addresses exclude impossible last `min_len - 1` emitted positions; total bound drops from `8614.133` to `8613.067` bits | strongest copy/reference upper bound |
| Sequential LZ minaddr local-repair formula | one literal `11216` in book `2` becomes a valid prior copy from source digit position `225`; total bound drops from `8613.067` to `8611.408` bits | strongest copy/reference upper bound |
| Sequential LZ post-minaddr local-repair formula | after the `11216` repair, literal `45765` in book `34` again becomes a valid prior copy from source digit position `183`; total bound drops from `8611.408` to `8609.773` bits | strongest copy/reference upper bound |
| Post-minaddr repair2 local frontier | after the two minaddr repairs, the best one-step local edit is `+0.121` bits worse | rejected refinement / local frontier closed |
| Post-repair2 parameter resweep | literal Rice `k=3`, payload order `2` / `alpha=1`, and item-type order `3` / `alpha=2` remain best | retained parameter frontier |
| Post-repair2 pair frontier | `17663` valid compatible local-edit pairs are rescored; the best pair is `+0.692` bits worse | rejected refinement / pair frontier closed |
| Post-repair2 address model search | min_len-bounded absolute addresses remain best decodable at `8609.8`; literal-seed no-mode reaches `8540.4` but is not decodable without source-mode bits | rejected refinement / optimistic clue |
| Post-repair2 copy order search | source-address-then-length remains best decodable; pure length-first is `+18.295` bits worse and best-order no-mode is `-3.539` bits optimistic only | rejected refinement / optimistic clue |
| Sequential LZ adaptive copy-length formula | bounded adaptive copy-length index coding with `alpha=2` lowers the active bound from `8609.773` to `8575.986` bits | strongest copy/reference upper bound |
| Post-adaptive-copy-length local frontier | after adaptive copy lengths, the best one-edit repair is copy-to-literal `45765` in book `34`, still `+1.084` bits worse | rejected refinement / local frontier closed |
| Post-adaptive parameter resweep | copy-length `alpha=2`, literal Rice `k=3`, payload order `2` / `alpha=1`, and item-type order `3` / `alpha=2` remain best | retained parameter frontier |
| Post-adaptive pair frontier | `17663` valid compatible pairs are rescored; the best pair, copy-to-literal `71288` plus `45765`, is `+2.516` bits worse | rejected refinement / pair frontier closed |
| Post-adaptive address model search | min_len-bounded absolute addresses remain best decodable at `8576.0`; literal-seed no-mode reaches `8506.6` but is not decodable without source-mode bits | rejected refinement / optimistic clue |
| Post-adaptive copy order search | source-address-then-adaptive-length remains best decodable; pure length-first is `+13.664` bits worse and best-order no-mode is `-3.539` bits optimistic only | rejected refinement / optimistic clue |
| Post-adaptive copy-length context formula | a fixed book-midpoint context for the adaptive copy-length prior lowers the bound from `8575.986` to `8574.407` bits after charged context declaration bits | strongest copy/reference upper bound |
| Post-midpoint local frontier | after the midpoint context, the best one-edit local repair is literal-to-copy `477090` in book `17`, still `+1.537` bits worse | rejected refinement / local frontier closed |
| Post-midpoint parameter resweep | after the midpoint context, copy-length `alpha=1` lowers the bound from `8574.407` to `8572.267` bits while literal length, payload, and item-type parameters stay fixed | strongest copy/reference upper bound |
| Post-midpoint alpha1 local frontier | after `alpha=1`, the best one-edit local repair remains literal-to-copy `477090` in book `17`, still `+0.971` bits worse | rejected refinement / local frontier closed |
| Post-midpoint alpha1 pair frontier | `17663` valid compatible pairs are rescored after the alpha1 local frontier closes; the best pair is still `+2.501` bits worse | rejected refinement / pair frontier closed |
| Post-midpoint alpha1 address model search | min_len-bounded absolute addresses remain best decodable at `8572.267`; literal-seed no-mode reaches `8502.9` but is not decodable without source-mode bits | rejected refinement / optimistic clue |
| Post-midpoint alpha1 copy order search | source-address-then-length remains best decodable; pure length-first is `+12.194` bits worse and best-order no-mode is `-3.539` bits optimistic only | rejected refinement / optimistic clue |
| Post-midpoint alpha1 copy-length context resweep | fixed book-midpoint context remains best at `8572.267`; book quartiles are `+1.941` bits worse and the best searched split is `+2.296` bits worse | retained context frontier |
| Post-midpoint alpha1 context alpha grid | first-half `alpha=1` plus second-half `alpha=2` saves `1.611` length bits but is `+1.389` bits worse after per-context alpha declarations | rejected refinement / retained shared alpha |
| Post-midpoint alpha1 literal payload context search | book-midpoint payload context saves `2.251` bits but is `+1.749` bits worse after declaration; searched split book `39` is `+11.613` bits worse | rejected refinement / retained global payload model |
| Post-midpoint alpha1 top60 triple probe | among the top `60` local single-edit candidates, `33588` valid compatible triples are rescored and the best is still `+3.914` bits worse | bounded negative probe / not exhaustive closure |
| Post-midpoint alpha1 item-type context search | a declared item-type split at book `6` lowers the bound from `8572.267` to `8569.652`; current-item-length context is cheaper but non-decodable | strongest copy/reference upper bound |
| Post-itemctx parameter resweep | after the item-type split context is active, item-type extra-context order `1` / `alpha=2` lowers the bound from `8569.652` to `8561.792`; literal-run length, literal payload, and midpoint copy-length parameters stay fixed | strongest copy/reference upper bound |
| Post-itemctx_param local frontier | after the itemctx_param promotion, the best one-step edit is literal-to-copy `60199` in book `3`, still `+0.957` bits worse | rejected refinement / local frontier closed |
| Post-itemctx_param pair frontier | `17663` valid compatible pairs are rescored after the itemctx_param local frontier closes; the best pair is still `+1.809` bits worse | rejected refinement / pair frontier closed |
| Post-itemctx_param address model search | min_len-bounded absolute addresses remain best decodable at `8561.792`; literal-seed no-mode reaches `8492.396` but is not decodable without source-mode bits | rejected refinement / optimistic clue |
| Post-itemctx_param copy order search | source-address-then-length remains best decodable; pure length-first is `+12.194` bits worse and best-order no-mode is `-3.539` bits optimistic only | rejected refinement / optimistic clue |
| Post-itemctx_param copy-length context resweep | fixed book-midpoint context remains best at `8561.792`; book quartiles are `+1.941` bits worse and the best searched split is `+2.296` bits worse | retained context frontier |
| Post-itemctx_param context alpha grid | first-half `alpha=1` plus second-half `alpha=2` saves `1.611` length bits but is `+1.389` bits worse after per-context alpha declarations | rejected refinement / retained shared alpha |
| Post-itemctx_param literal payload context search | book-midpoint payload context saves `2.251` bits but is `+1.749` bits worse after declaration; searched split book `39` is `+11.613` bits worse | rejected refinement / retained global payload model |
| Post-itemctx_param item-type context family search | `17024` family/order/alpha candidates are rescored; active split `6`, order `1`, alpha `2` remains best and nearest alternate split `9` is `+1.335` bits worse | retained item-type context frontier |
| Post-itemctx_param payload/item-type pair context search | `77` payload contexts and `17024` item-type candidates form `1310848` pairs; active pair remains best, best changed pair is `+0.415` bits worse, and best pair with both components changed is `+2.164` bits worse | rejected refinement / joint context frontier closed |
| Post-itemctx_param copy-length/item-type pair context search | `79` copy-length contexts and `17024` item-type candidates form `1344896` pairs; active pair remains best, best changed pair is `+0.415` bits worse, and best pair with both components changed is `+2.357` bits worse | rejected refinement / joint context frontier closed |
| Post-itemctx_param payload/copy-length/item-type triple context search | `77` payload contexts, `79` copy-length contexts, and `17024` item-type candidates imply `103556992` triples; active triple remains best, best changed triple is `+0.415` bits worse, and best triple with all three components changed is `+4.106` bits worse | rejected refinement / triple context frontier closed |
| Post-itemctx_param copy-length alpha/item-type pair search | `4097` copy-length alpha rows and `17024` item-type candidates imply `69747328` pairs; active pair remains best, best changed pair is `+0.415` bits worse, and best pair with both components changed is `+1.804` bits worse | rejected refinement / joint alpha frontier closed |
| Post-itemctx_param copy-length alpha/payload pair search | `4097` copy-length alpha rows and `77` literal-payload contexts imply `315469` pairs; active pair remains best, best changed pair is `+1.389` bits worse, and best pair with both components changed is `+3.138` bits worse | rejected refinement / joint alpha frontier closed |
| Post-itemctx_param copy-alpha/payload/item-type triple search | `4097` copy-length alpha rows, `77` literal-payload contexts, and `17024` item-type candidates imply `5370544256` triples; active triple remains best, best changed triple is `+0.415` bits worse, and best triple with all three components changed is `+3.553` bits worse | rejected refinement / triple alpha frontier closed |
| Post-itemctx_param copy-length context/shared-alpha resweep | `79` copy-length contexts times `64` shared alpha values test `5056` rows; active book-midpoint context with `alpha=1` remains best, best context change is `+1.941` bits worse, and best active-context alpha change is `+2.140` bits worse | rejected refinement / context-alpha frontier closed |
| Post-itemctx_param literal-payload context/shared-alpha resweep | `77` literal-payload contexts times `64` shared alpha values test `4928` rows; active global payload model with `alpha=1` remains best, best context change is `+1.749` bits worse, and best active-context alpha change is `+17.859` bits worse | rejected refinement / payload context-alpha frontier closed |
| Post-itemctx_param copy/payload context-alpha pair search | `5056` copy-length context-alpha rows and `4928` literal-payload context-alpha rows imply `24915968` pairs; active pair remains best, best changed pair is `+1.749` bits worse, and best pair with both components changed is `+3.690` bits worse | rejected refinement / context-alpha pair frontier closed |
| Post-itemctx_param copy/payload/item context-alpha triple search | `5056` copy-length context-alpha rows, `4928` literal-payload context-alpha rows, and `17024` item-type candidates imply `424169439232` triples; active triple remains best, best changed triple is `+0.415` bits worse, and best triple with all three components changed is `+4.106` bits worse | rejected refinement / context-alpha triple frontier closed |
| Post-itemctx_param address/copy-order pair search | `10` address rows and `5` copy-order rows form `50` pairs; best overall pair is `-72.935` bits but nondecodable, active pair remains best decodable, and best changed decodable pair is `+8.979` bits worse | rejected refinement / optimistic lower bound only |
| Post-itemctx_param address/item-type pair search | `10` address rows and `17024` item-type candidates form `170240` pairs; best overall pair is nondecodable via literal-seed no-mode addressing, active pair remains best decodable, and best changed decodable pair is `+0.415` bits worse | rejected refinement / optimistic lower bound only |
| Post-itemctx_param address/payload context-alpha pair search | `10` address rows and `4928` literal-payload context/alpha rows form `49280` pairs; best overall pair is nondecodable via literal-seed no-mode addressing, active pair remains best decodable, and best changed decodable pair is `+1.749` bits worse | rejected refinement / optimistic lower bound only |
| Prequential generation model audit | prefix-online and prefix-frozen learned-component scoring beat uniform on all train cutoffs `10/20/35/50/60`; the then-active `8561.792` formula is retained as a prior `compression_bound`, not final authorial method | partial predictive validation / generation explanation not final |
| Prequential order control audit | numeric prefixes still beat uniform, but random same-size train-book sets usually save more bits; the learned-component signal is not numeric-order-specific | predictive distribution only / numeric authorial order not promoted |
| Prequential component ablation audit | copy-length midpoint generalizes; literal payload order-1 beats active order-2 and item-type split-only beats active split+previous item on prefix holdout | generation explanation simplified / compression bound unchanged |
| Simplified generation profile compile | holdout-preferred component profile roundtrips `70/70` at `8613.581` bits, `+51.789` versus the active bound | explanatory profile / not lower MDL code |
| Item-type split-only formula compile | split-only item-type coding keeps the same recipe and forced rules, validates `70/70`, and lowers the bound from `8561.792` to `8558.667` | strongest copy/reference upper bound |
| Item-type split-only alpha resweep | after the split-only promotion, `alpha=2` remains best at `8558.667`; nearest alternate `alpha=1` is `+0.309` bits worse | retained parameter frontier |
| Item-type op-shape boundary gate | split-only item-type sequence modeling remains retained, but compact-recipe op `type` fields are derivable from operation shape; `348` explicit fields are removed with `+0.000` bit delta and `70/70` roundtrip | item sequence retained / recipe type field derived |
| Prequential and row0 origin audit | freezes `8558.667` as `compression_bound`; learned components beat uniform on all prefix future-suffix splits, but random same-size train controls are usually stronger, and row0 origin remains exogenous across manual/permutation/grid/order/external/workbook hypotheses | predictive component evidence / row0 still exogenous |
| Recipe externality audit | only `4285.876/8558.667` bits are prequentially scored learned components; `4272.791` bits remain fixed recipe or non-learned ledger | component validation only / full recipe discovery not proved |
| Row0 hypothesis requirement audit | all six requested row0-origin families are forced through algorithm, cost, coverage, contradiction, negative-control, and random/permuted comparison fields; promoted origin formulas remain `0` | row0 origin checklist closed negative |
| Recipe reparse evidence matrix | deterministic reparse roundtrips all prefix-held-out suffixes and beats active suffix recipes/content controls, but random same-size train inventories can match or exceed numeric prefix at cutoff `50` (`p=0.1538`) | fixed-recipe externality partly reduced / generation claim still partial |
| Recipe reparse train-set multi-cutoff | random same-size train-set controls at cutoffs `35/50/60` show numeric prefix beats random mean/max at `2/3` cutoffs but loses at cutoff `60` | numeric order not promoted as authorial proof |
| Recipe reparse family holdout | public-bookcase family holdout reparsing beats raw digits in `19/19` families and `3/3` component-failure families, but beats the active frozen recipe in only `14/19` families | recipe discovery signal strengthened / still partial |
| Recipe reparse family loss decomposition | the five active-recipe local wins all roundtrip and still beat raw digits; four are dominated by copy-address overhead with no literal/copy inventory change, and one is an exact tie | local losses explained / no generation promotion |
| Family holdout address-space audit | after rebasing the active recipe into the same heldout-after-train coordinate system, the five copy-address losses drop from mean `4.667` bits to approximately `0.000` bits | active local wins were coordinate artifacts |
| Address-corrected family scoreboard | applying the address-space correction to all public-bookcase families changes reparse-vs-active beat/tie coverage from `15/19` to `19/19`, while raw-digit coverage remains `19/19` | predictive recipe validation strengthened |
| No-test-carryover family holdout | parsing each held-out book from the training-complement inventory alone still roundtrips `19/19` families and beats raw digits in `19/19`, with mean gain `1054.570` bits | family signal does not require heldout self-feeding |
| Leave-one-book-out no-self audit | each individual book is reparsed from the other `69` books only; `70/70` roundtrip and `70/70` beat raw digits, with minimum gain `96.055` bits | item-level redundancy validated / no order proof |
| Leave-one-book-out source attribution | singleton reparses use `189` copy items and `11062` copied digits attributed to source books/current prefix; `3001` copied digits cross artificial source-book boundaries | source dependency atlas / boundary caveat exposed |
| Book-bounded singleton source audit | forbidding source copies from crossing source-book boundaries still gives `70/70` roundtrip and `70/70` raw wins; mean gain `464.898` bits | boundary caveat not required for singleton signal |
| Family-excluded singleton source audit | removing same-family books from frozen train counts and copy sources still gives `70/70` roundtrip, `70/70` raw wins, and `46/46` family-labeled raw wins; mean gain `460.251` bits | same-family source memorization not required |
| Online prefix book frontier audit | previous-books-only online reparsing with book-bounded sources roundtrips `70/70`, beats raw in `69/70`, and beats raw in `69/69` after the bootstrap book `0`; mean gain `419.761` bits | sequential generation frontier / bootstrap caveat |
| Online bootstrap seed policy audit | charging book `0` as an explicit raw seed closes the online cold-start failure: `70/70` wins-or-ties, `69/70` strict wins, and `10.499` bits saved versus parsing book `0` online | bootstrap policy clarified / no new bound |
| Seeded online formula rescore audit | converting the book-0 seed policy back into formula recipes fails complete scoring: seeded online is `+0.979` bits worse and book-bounded seeded is `+305.198` bits worse than `8343.062` | seed policy rejected as formula promotion |
| Seeded rescore loss decomposition | the seeded formula saves `36.842` non-payload bits but adds `37.821` literal-payload bits, explaining the `+0.979` net loss | local seed saving outweighed by payload cost |
| Seed exception signal cost audit | even zero-cost deterministic fallback is `+0.979` bits worse; a one-book index exception is `+7.108`, so promotion would require negative descriptor cost `< -0.979` | seed exception promotion closed |
| Online order frontier controls | numeric order keeps `69/69` after-bootstrap raw wins, but `10/11` tested orders also do, including `6/6` seeded random orders; `random_04` is `+0.549` bits better in mean after-bootstrap gain and `+61.452` bits better in total gain | online frontier predictive / numeric order not proved |
| Order frontier promotion gate | the local frontier winner `random_04` is `+188.584` bits worse than numeric under the complete online formula before order cost and `+521.038` bits worse after descriptor cost; no tested non-numeric order promotes | frontier metric demoted from promotion score |
| Prequential recipe reparse audit | with frozen train-prefix component counts, a deterministic LZ parser roundtrips every future suffix and beats the active full-corpus recipe under the same frozen counts on all five cutoffs | predictive recipe evidence / split-specific analysis only |
| Prequential recipe reparse controls | at cutoffs `20/35/50`, real suffixes beat random same-length, per-book-shuffled, and suffix-pool-shuffled controls; controls have negative gain versus raw digits | controlled predictive recipe evidence |
| Prequential recipe train-set controls | at focused cutoff `50`, numeric prefix beats the random train-set mean but not all random inventories (`p=0.1538`) | predictive recipe evidence / numeric order not promoted |
| Online deterministic reparse formula | deterministic parser using only prior committed book counts becomes a full-corpus formula; validates `70/70` and lowers the bound from `8558.667` to `8343.062` | strongest copy/reference upper bound |
| Online reparse order control | numeric order remains best against reverse, parity, length-derived, and 6 seeded random orders; best random raw order is `+188.584` bits worse before order cost | canonical order support / no new bound |
| Online formula recipe prune | book `length` and copy `target_start` are derivable; stripped projection preserves `8343.062` bits and `70/70`, saving `5612` recipe JSON bytes | representation simplification / no new bound |
| Canonical online recipe formula | materializes the pruned formula without book `length` or copy `target_start`; preserves `8343.062` bits and `70/70` | former compact bound representation |
| Literal-length-derived recipe formula | literal op `length` is derived from literal `text`; removes 87 more redundant fields and preserves `8343.062` bits and `70/70` | tighter recipe representation |
| Op-type-derived recipe formula | op `type` is derived from field shape; removes 348 more redundant fields and preserves `8343.062` bits and `70/70` | remaining op dependencies: literal text, copy source, copy length |
| Recipe representation dependency gate | consolidates the compact recipe compiles: `766` independent fields are derivable and removed with `+0.000` bit delta and `70/70`, while literal text, copy source, and copy length remain declared | derivable recipe fields closed / dependencies retained |
| Copy source canonicality audit | all 261 copy sources are the earliest legal occurrence of the copied chunk at declared length; only 123 are unique | canonical encoder rule / source still required for decoding |
| Source canonicality decodability gate | earliest-source canonicality is `261/261`, but the rule depends on future target chunk, `138/261` choices are ambiguous at declared length, and source dependency is not removed | encoder regularity / decoder source retained |
| Copy source canonicality controls | earliest occurrence remains `261/261`; latest occurrence is `123/261`, previous-source-plus-length is `5/261`, and random candidate choice expects `169.473` hits | source tie-break support / no decoder removal |
| Copy length default/exception formula | target-max extension is high-coverage but encoder-only; decodable `decoder_max_possible` default plus adaptive exceptions lowers copy-length cost and promotes the bound to `8206.178` bits | copy length remodeled / row0 unchanged |
| Copy length derivation boundary gate | target-max matches `238/261` copy lengths but is encoder-only; decoder max-possible gives `60` defaults / `201` exceptions, midpoint generalizes, and compact recipes still declare `261` copy lengths | copy length partly modeled / dependency retained |
| Copy source default/exception formula | previous-source-plus-length default is decodable but sparse; adaptive exception-source coding lowers copy-address cost and promotes the bound to `8177.317` bits | copy source remodeled / row0 unchanged |
| Default/exception prequential validation | after train-count freezing fix, prefix online and frozen gains are all positive (`min frozen aggregate=50.303` bits), but family holdouts include failures | prefix-frozen partial / final method not promoted |
| Default/exception component profile | `8177.317` remains compression bound and prefix-frozen profile; family/bookcase failures keep the generation claim partial | separated ledgers |
| Current literal-payload profile audit | old order-1 profile does not transfer; order-1 is `+95.968` full-corpus and `+28.609` aggregate frozen-prefix bits worse | order-2 retained |
| Copy source distance model audit | backward-distance source coding is decodable but the replacement is `+25.551` bits worse than active absolute-source default/exception | distance rejected |
| Current active prequential profile audit | active learned streams cover `7157.317/8177.317` bits and beat uniform on all tested prefix, block, and public-bookcase family holdouts; random same-size train controls are usually stronger than numeric prefixes | component validation strengthened / recipe discovery not proved |
| Current active profile boundary gate | consolidates `8177.317` as active bound with positive frozen gain across all tested prefix/block/family splits, while exact active reparse remains blocked by previous-copy source/length state | active profile validated / recipe discovery blocked |
| Copy source state compression gate | active source default only needs `previous_copy_end`, not full previous `(source, length)`; default/exception ledger is preserved and aggregate candidate-state proxy drops by `97.239%` | source state simplified / parser not promoted |
| Active reparse feasibility after state compression | every tested book-level `previous_copy_end` source-state proxy is below `1,000,000`, and cutoff `60` has `9/10` books below `250,000`; the full active objective and remaining recipe dependencies are still unresolved | prototype frontier improved / parser not promoted |
| Cutoff-60 source-state reparse prototype | deterministic reparse recipes for cutoff `60` are repriced with the active `previous_copy_end` source ledger; `10/10` roundtrip, `10/10` raw wins, and aggregate `-10.241` bits versus uniform-address reparse, with only `4/10` individual wins | source ledger executable / recipe not reoptimized |
| Multi-cutoff source-state reparse reprice | the same repricing is repeated at cutoffs `10/20/35/50/60`; `5/5` cutoffs beat uniform-address reparse in aggregate, totaling `-112.968` bits, while recipes are still not source-state reoptimized | source ledger generalizes / parser not promoted |
| Multi-cutoff source-choice optimizer | greedy alternate-source choice over fixed deterministic reparse chunks changes `0/514` sources and gives `+0.000` bits versus repricing | source-only local frontier closed |
| Multi-cutoff global source-path optimizer | exact DP over source choices with fixed deterministic segmentation and copy lengths changes `10/514` sources, improves the repriced ledger by `-42.359` bits, and uses max state count `14` | path-state value confirmed / parser not promoted |
| Full-corpus source-path formula gate | same-chunk source substitutions proposed by global path DP survive exact adaptive source-stream rescore; changing `2/261` sources lowers the active bound from `8177.317` to `8162.412` bits | strongest fixed-recipe copy/reference bound |
| Full-corpus source-substitution frontier | exhaustive single/pair same-chunk source substitution search tests `376` singles and `69849` pairs; the best pair lowers the active bound from `8162.412` to `8160.827` bits | strongest fixed-recipe copy/reference bound |
| Full-corpus source-substitution second pass | rerunning the same single/pair frontier on the `8160.827` bit formula finds only a microscopic `+0.000671` bit gain, lowering the active bound to `8160.826421` | compression-bound update / generation evidence unchanged |
| Full-corpus source-substitution third pass | a third single/pair frontier pass finds another microscopic `+0.000503` bit gain, lowering the active bound to `8160.825917` | local source frontier saturating |
| Full-corpus source-substitution fourth pass | a fourth single/pair frontier pass finds another microscopic `+0.000310` bit gain, lowering the active bound to `8160.825608` | local source frontier saturating |
| Source-substitution saturation audit | last three same-chunk source-substitution passes total only `0.001484` bits, and a minimum pair-selector floor dwarfs the latest gain | local source micro-sweeps frozen as non-mainline |
| Active reparse state-boundary audit | active copy-source default is path-dependent on previous copy source/length; exact reparse needs expanded state and reaches a cutoff-10 state proxy of `302879952` | recipe-discovery blocker localized |
| Copy source state-free default audit | decoder-computable source defaults that avoid previous-copy state are all worse; the best `state_free_back_current_length` rule is `+15.186` bits worse and worse in every prefix frozen split | state-free source simplification rejected |
| Source state dependency gate | canonicality does not remove source dependency and state-free defaults do not remove previous-copy source/length state; best state-free default is `+15.186` bits and loses `5/5` prefix-frozen checks | path-dependent source state retained |
| Source selection derivation boundary gate | source selection is `261/261` earliest-source canonical, but earliest depends on future target text; backward distance is `+25.551` bits worse and state-free default is `+15.186` bits worse | encoder canonicality retained / decoder derivation rejected |
| Copy length midpoint context audit | midpoint `book_id < 35` beats global by `13.839` bits, is rank `2/69` among one-cut boundaries, beats global in every prefix frozen split, and passes book-id permutation controls (`p=0.0033`) | midpoint context supported / no new bound |
| Copy length midpoint context gate | natural midpoint context is retained as generalizing component; searched cutoff `37` is only `0.256` bits better and is rejected as ad-hoc | component validation strengthened / no bound promotion |
| Literal copy availability boundary audit | `73/87` literal starts have no legal `min_len` copy candidate and `760/857` literal digits are forced at digit level; residual parser choice is localized to `14` literal starts / `97` digit positions | literal externality reduced / no new bound |
| Literal copy availability gate | forced literals dominate (`73/87` starts, `760/857` digits); `74` in-literal and `465` cross-op repair candidates are all worse, with best deltas `+1.180` and `+0.027` bits | literal externality reduced / local repairs rejected |
| Optional literal copy repair frontier | `74` single in-literal copy-prefix repairs across `5` eligible optional starts are scored under the active ledger; best candidate is still `+1.180` bits worse | simplest optional-literal repair rejected |
| Cross-op optional literal copy frontier | allowing replacement copies to cross literal boundaries yields `465` valid candidates; none improves, and the best is only `+0.027` bits worse than active | cross-op optional-literal repair rejected |
| Cross-op near-tie decomposition | best near miss saves literal/item bits but pays `+11.237` copy-source and `+1.639` copy-length bits, yielding a real `+0.027` bit loss | near tie explained / no promotion |
| Cross-op source break-even audit | best near miss uses earliest of two full-length sources and would improve under a source-free oracle, but the active source ledger is `0.027` bits above break-even | source-free oracle rejected |
| Copy source structural context audit | book-half, length-bucket, exact-length, position-bucket, and combined contexts all worsen the source exception stream; best non-global is `+5.872` bits and loses every prefix-frozen split | global source prior retained |
| Source blocker structural context gate | the cross-op near tie is only `+0.027` bits worse and a source-free oracle would be `-11.209`, but the best decodable context `book_half` is `+5.872` bits worse and loses `5/5` prefix-frozen checks | simple source-context rescue rejected |
| Literal payload default/exception audit | modal-default/exception literal digit coding is decodable but worse than the active categorical previous-emitted-digit order-2 model | rejected fallback / no new bound |
| Literal payload structural context audit | literal-run offset, run-length bucket, book half/parity, and bounded combinations with `prev2` all over-split the payload stream | rejected context / no new bound |
| Literal payload model gate | after forced literal availability is separated, order-1 remains worse on full corpus and aggregate prefix totals; modal default/exception and simple structural contexts are also worse | active order-2 payload dependency retained |
| Prequential and row0 origin audit | frozen validation scope `8558.667` shows partial learned-component prediction, but family failures and recipe externality keep it from being a full generation method; row0 remains exogenous | analysis-only boundary / no generation promotion |
| Row0 origin frontier audit | matrix/rule/orbit/tape-feature/low-rank/render/eye/provenance tests are indexed together; no family yields a charged, controlled, holdout-capable pair-label formula | current-corpus frontier saturated / row0 origin still open |
| Row0 parallel provenance bridge | independent provenance front traces local workbook/import/reconstruction/audit layers, but CipSoft origin is untraced and paid worksheet anchors do not beat lookup after pair+label costs | row0 remains exogenous |
| Current formula dependency scoreboard | latest source-substitution formula roundtrips `70/70` with `348` ops; `87` literal payload fields, `261` copy-source fields, and `261` copy-length fields remain declared | next mainline is structural source/length parser |
| Source-length joint derivability audit | latest source substitutions reduce the prior all-earliest source pattern from `261/261` to `251/261`; joint earliest+target-max covers `230/261` but is encoder-oracle only, while decoder-valid declared-source+decoder-max covers only `60/261` | source and length remain declared dependencies |
| Source canonicality tradeoff audit | restoring the all-earliest source profile repairs `10` non-earliest current events but raises the total from `8160.825608` to `8177.316653` bits (`+16.491045`) | compression bound and explanation profile separated |
| Copy length segmentation exception audit | all `23` target-max length exceptions enter exactly one following op and stop inside it, absorbing `0` complete following ops | copy length is a resegmentation problem |
| Target-max resegmentation candidate audit | local extend-and-trim rewrites produce `42/46` valid candidates and `5` proxy improvements; best proxy is book `9` op `0` at `-2.059513` bits | candidate path opened / exact scorer required |
| Target-max resegmentation formula gate | exact component scorer reproduces the current bound and promotes book `9` op `0` resegmentation, lowering the bound from `8160.825608` to `8158.766094` (`+2.059513`) | strongest mechanical bound / row0 unchanged |
| Target-max resegmentation second-pass gate | after the first rewrite, exact scorer tests `44` remaining candidates, finds `4` improvements, and promotes book `2` op `9`, lowering the bound to `8157.065654` (`+1.700440`) | strongest mechanical bound / row0 unchanged |
| Target-max resegmentation saturation gate | greedy exact continuation promotes two final positive passes, lowers the bound to `8156.050355`, and leaves `0` exact improving candidates in the local target-max frontier | local resegmentation family saturated / row0 unchanged |
| Post-target-max source-substitution frontier | rerunning exact same-chunk source substitution after target-max saturation finds one microscopic pair gain, lowering the bound to `8156.050167` (`+0.000188`) | compression-bound bookkeeping / row0 unchanged |
| Post-target-max source-substitution second pass | rerunning the same frontier on the post-target-max source-substituted formula finds another microscopic pair gain, lowering the bound to `8156.049986` (`+0.000181`) | compression-bound bookkeeping / row0 unchanged |
| Post-target-max source-substitution stop audit | the two post-target-max source passes sum to only `0.000369` bits and selector-cost sanity checks dominate by `32.244` bits, so no third pass is run | micro-frontier frozen / return to structural tests |
| Active formula dependency refresh | comparing the gate-48 formula to the active post-target-max formula shows a `4.775621`-bit bound gain but `+0` declared recipe dependency fields; the active formula still declares `609` fields | better bound / no structural dependency reduction |
| Active source-length joint refresh | active target-max length hits improve `238 -> 242`, but joint decoder-valid rules remain unchanged: declared-source+decoder-max `60/261`, unique-source+decoder-max `28/261`, previous-end+decoder-max `1/261` | encoder regularity sharpened / decoder dependency retained |
| Active copy-length exception topology | active target-max exceptions drop `23 -> 19` and slack drops `128 -> 115` digits, but all `19` remaining exceptions still partially enter exactly one following op | residual length problem remains joint segmentation |
| Active residual target-max resegmentation | exact-scoring the `38` local extend-and-trim rewrites for the `19` active exceptions finds `34` valid and `0` improving candidates; best valid rewrite is `-0.000163` bits worse | local residual target-max frontier saturated |
| Active exception stop-rule separability | simple single-feature and pairwise stop rules over `261` copy events find `0` exact separators for the `19` residual boundaries; best F1 is `0.265060`, with many false positives and no decoder-valid promotion | simple stop-rule explanation rejected |
| Active exception finite-state model | `231` compact online context models are tested for the `19` residual boundaries; the best costs `112.749463` bits, `+17.943077` worse than an explicit exception list, with permutation `p=0.638000` | finite-state exception model rejected |
| Active exception partial-boundary shift | every positive partial shift up to target-max is exact-scored for the `19` residual boundaries; `2/229` candidates improve, led by book `10` op `0` delta `3` | candidate path reopened locally |
| Partial-boundary shift formula | the best partial shift is promoted with `70/70` roundtrip and lowers the mechanical bound from `8156.049986` to `8155.261037` bits | strongest fixed-recipe copy/reference bound |
| Partial-boundary shift second pass | after the first promotion, `1/223` second-pass candidates improves: book `46` op `1` delta `1` | candidate path continued locally |
| Partial-boundary shift second-pass formula | the second partial shift is promoted with `70/70` roundtrip and lowers the mechanical bound from `8155.261037` to `8154.676268` bits | strongest fixed-recipe copy/reference bound |
| Partial-boundary shift saturation | after two promotions, `0/221` remaining partial-shift candidates improve; best valid remaining shift is `-0.000163` bits worse | local partial-shift frontier closed |
| Branch-choice frontier closure | gates `16-35` in the segmentation-decision front are compiled together; `20` gates are audited, `0` complete parser rules promote, and simple weak-signal branch-choice combinations are closed as audit-only | richer path/state parser still required |
| Path-template reuse audit | exact source-free operation-length templates of width `1..3` from the `50` exact parser books explain `0/10` residual first-drift corrections under the observable state key | simple template reuse rejected |
| Trajectory-neighbor parser audit | nearest cumulative parser-state trajectories over trajectory/context/combined vectors with `k=1/3/5` explain `0/10` residual first-drift corrections; shuffle control mean is `0.190` | nearest trajectory reuse rejected |
| Observable state support audit | best exposed state family supports only `4/10` residuals and gives `0/10` deterministic exact-label matches; `6/10` residual states are out of support | latent state or source-free target stream still required |
| Latent state requirement audit | `33` simple observable split tests still give `0/10` deterministic residual matches; all `10` residuals and `9` distinct stable labels need latent/source-free explanation | simple latent splits rejected |
| Latent state lookup cost gate | pricing the fallback latent lookup gives a first-drift lower bound of `79.361` bits and a per-site dictionary variant of `90.269` bits; full oracle needs at least `11` correction events | latent state must provide a compact rule |
| Compact latent rule frontier | `6276` single/two-rule residual-visible rule sets are charged against the `79.361`-bit lookup; the only apparent MDL win has a false positive, and the best zero-false-positive rule is `+1.773` bits worse | compact residual rule rejected |
| Source-free residual rule gate | `4495` strict book/op ordinal rule sets are tested after removing active parser features; the apparent structural win has `1` false positive, the best clean rule hits only `1/10` and is `+1.651` bits worse than lookup, and held-out hits are `0/4` | source-free ordinal selector rejected |
| Operation n-gram grammar gate | `9` operation-sequence grammar families are trained on the `50` exact parser books; every family gets `0/10` residual hits, the safest richer context has `4` false positives and `6` unsupported residuals, and the lowest-net unigram still has `10` false positives | compact operation grammar rejected |
| Residual exception transfer gate | `6` observable residual feature families and `k=1/3/5` nearest-residual transfer are tested leave-one-residual-out; best result is `0/10` hits and `0/4` held-out cells with a hit | reusable residual-exception class rejected |
| Branch rank position audit | `14` observable branch orderings are tested; best top-1 ranker gets `6/10` residuals but changes `20` clean controls, and best top-3 coverage is `8/10` | weak rank signal / no parser rule |
| Branch rank exception cost gate | pricing `balanced_ops_literals` against the `79.361`-bit residual lookup shows global ranker+corrections is `+96.497` bits worse; residual-gated ranker is `-4.684` bits only after granting residual-site lookup | rank signal audit-only / not source-free |
| Residual site detector gate | `1196` observable branch-ambiguity predicates and `4356` single/pair rules are tested; best rule is `6/10` with `6` false positives, best zero-FP rule covers `3/10`, and prefix/holdout covers all residuals in `0/4` cells | residual-gated ranker remains lookup-dependent |
| Book skeleton alignment gate | `27` whole-book skeleton alignment configs over `50` exact books are tested; best config gets `0/10` residual unique-branch hits, `0/10` residual type/length hits, and `211` clean false changes | book-level skeleton parser rejected |
| Source interval context gate | `12` source/payload context policies are tested; best source-target start-distance policy gets `5/10` residuals with random-control `p=0.002`, but causes `189` clean false changes and `0/4` cover-all holdout cells | weak source-context clue / no parser rule |
| Source interval precision gate | `1780` observable predicates and `30720` rules test whether source-interval repairs can fire safely; best rule gets `5/10` residuals with `4` clean false changes, and best zero-FP rule gets `3/10` | precision improves but parser not promoted |
| Source interval observable precision gate | gate 51's zero-FP rule is corrected by removing diagnostic `drift_class`; `1762` observable predicates leave the best zero-FP rule at only `2/10` residuals, while the best full-fit observable rule remains `5/10` with `4` clean false changes | safe observable source-interval rule not promoted |
| Source interval cost gate | pricing the observable source-interval signal against the `79.361`-bit residual lookup makes the full-fit rule `+3.410` bits worse; the zero-FP rule is only `-0.131` bits better before holdout and covers `2/10` residuals | cost clue audit-only / no parser rule |
| Book-start copy subclass gate | isolating the tempting book-start copy residual subclass without `drift_class` catches all `3/3` subclass residuals only with `6` clean false changes; the best zero-FP rule catches `1/3`, is `+8.670` bits worse than lookup, and gets `0/4` clean oracle-cover holdout cells | weak clue audit-only / no parser rule |
| Observable signature support gate | `6` observable decision/candidate signature families and `3` label modes are tested; the best full-fit signature gives `0/10` deterministic residual matches, with `7/10` out of support and `0/4` holdout cells with any deterministic match | exposed candidate state rejected / latent path-state still required |
| Sequential signature support gate | adding previous one/two operation shapes and prior copy/literal counts to candidate signatures tests `10` sequential families and `3` label modes; every residual query is out of support, so the best result is `0/10` deterministic matches and `0/10` supported residuals | short observable path memory rejected |
| Latent path-state budget gate | after support failures, a valid latent-state account still pays `58.570` site bits plus `20.791` label-order bits; the best valid model is exactly the `79.361`-bit residual lookup, while cheaper rows require a residual-site oracle | latent-state naming rejected as lookup repackaging |
| Beam survival budget gate | after direct branch selection fails, the stable branch survives inside width `5` under `max_suffix_copy_digits` in `5/5` prefix/holdout cells, but top-1 gets only `5/10` residuals and the fixed-width paid model is `+4.750` bits worse than lookup | weak path-state clue / no selector promoted |
| Beam rank selector gate | inside that width-5 beam, `beam_context_combo` resolves `10/10` residuals full-fit but changes `4` clean controls; prefix/holdout has `0/5` cover-all cells and the paid context table is `+129.872` bits worse than lookup | full-fit selector clue / not promoted |
| Beam selector stability gate | support-pruning and stability tests keep the best full-fit threshold at support `1`; leave-one-book drops to `4/10`, leave-context-out to `5/10`, and prefix/holdout still has `0/5` cover-all cells | selector table unstable / not promoted |
| Beam hierarchical backoff gate | six observable context hierarchies are tested; best `global_to_beam_combo` ties `230/234` and `10/10` residuals only at support `1`, grows to `88` contexts, costs `+166.286` bits, and keeps `0/5` cover-all holdout cells | backoff selector rejected |
| Residual patch program gate | the ten residual choices compress to five macro patch classes, but site selection still costs `56.631` bits, the cheapest paid patch program is `+2.490` bits worse than lookup, the best zero-FP detector hits `1/10`, and prefix/holdout exact detector cells are `0/5` | weak macro clue / site lookup not removed |
| Beam Markov state selector gate | a free-run Markov selector over beam ranks reaches `230/234` and `9/10` residuals with `3` clean false changes, but its paid table is `+159.472` bits worse than lookup and prefix/holdout cover-all remains `0/5` | sequential state clue / not promoted |
| Row0 next-frontier audit | lookup baseline is `160.521` bits; 13 worksheet anchors reduce nominal residual lookup to `106.343` bits before anchor/source costs, while ordered-surface facts (`39` absent, `19/91` conflict, `54/55` purity) promote only a mechanical clue | no origin formula / primary source or paid anchor reduction required |
| Row0 paid anchor reduction gate | all 13 worksheet anchors save `54.178` bits only before costs; after explicit pair+label cost the net is `-11.852` bits, and rare-singleton anchors only break even despite strong nominal controls | partial worksheet remains descriptive / no origin formula |
| Recent formula row0 compatibility audit | partial-boundary book-formula improvements lower the downstream bound to `8154.676268`, but no gate predicts row0 labels under holdout, beats row0 lookup after costs, explains `39`/`93`/`19/91`, or adds CipSoft/authorial provenance | row0 unchanged / book formula only |
| Row0 real-origin search | row0-only scoreboard retests paid anchors, external order, workbook/script provenance, manual worksheet shape, ordered-surface exceptions, 6/9 quotient, diagonal/E pressure, grid coordinates, inventory/frequency, and recent book-formula dependency; no origin formula is promoted, and the only moved axis is strong falsification of important hypotheses | negative row0-origin search / no constructive improvement |
| Final formula dependency refresh | the `8154.676268` formula still has `609` retained operation dependency fields; target-max coverage stays `242/261`, declared-source+decoder-max `60/261`, unique-source+decoder-max `28/261`, and previous-end+decoder-max `1/261` | source/length parser still required |
| Final source/length parser feasibility | previous-end state compression keeps every tested book-level end-state proxy below `1,000,000`, but the copy-transition proxy totals `1,966,897,365` transitions (`23045.1x` old DP), with hardest books `53`, `51`, `35`, and `58` | parser needs pruning/caching before promotion |
| Book-local source/length parser probe | active source/length DP executes on cutoff-60 books `67` and `60`, both roundtrip and beat raw digits at `125.866` total parser bits, but ties the same-policy reprice and leaves hard book `66` unresolved | parser path executable / no bound promotion |
| Sparse hard-book source/length parser | sparse Dijkstra over reachable states roundtrips cutoff-60 hard book `66` in `0.033s`, with `41,832` transitions versus the `26,096,904` transition proxy (`623.9x` reduction) | hard local parser blocker removed / no bound promotion |
| Post-parser row0 compatibility audit | gates 71-74 are checked against the row0 front; none predicts row0 labels under holdout, beats paid lookup, explains `39`/`93`/`19/91`, or adds CipSoft/authorial provenance | row0 unchanged / parser-only progress |
| Recent-gates row0 compatibility refresh | gates `76..107` are checked against the row0 front; multi-cutoff parser validation, path-stability controls, decoder/source-policy controls, skeleton ledgers, and operation-type derivation all remain downstream from row0 | row0 unchanged / book formula only |
| Cutoff-60 sparse suffix parser | sparse Dijkstra parses books `60..69` sequentially with `previous_copy_end` carried between books; `10/10` roundtrip, `10/10` raw-positive, `368.531807` parser bits, and `383,548` transitions | suffix parser executable / no bound promotion |
| Multi-cutoff sparse suffix validation | cutoffs `10/20/35/50/60` all execute with frozen prefix counts; `175/175` suffix book evaluations roundtrip and beat raw, with parser better/tie/worse than same-policy reprice in `12/163/0` cells | predictive parser evidence strengthened / no bound promotion |
| Multi-cutoff parser path stability | exact operation signatures are replayed for the same book across frozen cutoffs; `38/50` multi-cutoff books keep one exact path, while `12/50` vary and book `65` has `4` signatures | parser mechanism supported / path instability remains |
| Unstable parser path decomposition | the `12` prefix-sensitive books split into `9` same-shape boundary shifts and `3` segmentation-shape changes; none is pure source-address drift | next blocker is boundary stabilization |
| Boundary policy stability gate | fixed simple boundary policies are repriced over the `12` unstable books and `37` cutoff observations; the best structural policy reaches only `16/37` exact matches with `8.984788` regret bits, and even the audit-only oracle reaches only `18/37` | rejected boundary-rule shortcut / blocker remains |
| Boundary instability cost decomposition | `47` losing observed variants are compared against their per-cutoff parser winners; dominant positive components are `copy_length` in `30`, `copy_source_exception` in `12`, `literal_payload` in `4`, and `copy_source_flag` in `1` | blocker localized to learned length/source-exception costs |
| Component-neutralized path stability | uniform decodable copy-length and source-exception costs improve exact multi-cutoff path stability from `38/50` to `48/50` with `175/175` roundtrip/raw-positive evaluations, at `+67.605622` parser bits and residual instability in books `26` and `34` | structural simplification candidate / no bound promotion |
| Component-neutralized residual tradeoff | the best neutralized mode resolves `11/12` active unstable books, keeps book `34` unstable, and introduces book `26`; full-source uniformization changes the residuals to `35`/`45` but costs another `+367.448154` bits | candidate not final / source flag not promoted |
| Residual literal-payload neutralization | uniform literal-payload cost on top of the copy-length/source-exception neutralized parser resolves books `26` and `34`, improves stability to `49/50`, and leaves only book `49` unstable, at `+170.606311` parser bits over the previous neutralized mode | narrower simplification candidate / not final |
| Book 49 residual split cause audit | the sole `49/50` residual is a prefix split: cutoffs `10/20` choose `literal-copy-literal` lengths `11+7+7`, while cutoff `35` chooses one `25`-digit literal; removing local `literal_length` or `item_type` charge stabilizes the split locally | local cause localized / audit-only |
| Global item/literal-length control gate | applying the book `49` controls corpus-wide shows that removing `item_type` charge closes exact path stability at `50/50`, while removing both `item_type` and `literal_length` also reaches `50/50` with best parser-bit delta `-770.657134` versus payload-uniform baseline and `175/175` roundtrip/raw-positive evaluations | parser-stability simplification / row0 unchanged |
| Stable path projection boundary audit | the best stable no-item/no-literal-length projection covers `11263/11263` digits with `208` copy items and `54` literal runs after 10 seed books, reducing materialized operation dependency fields by `139` versus active formula, but it still requires target text for copy candidates, literal payload, and endpoints | encoder-side projection only / no generator promotion |
| Decoder-side rule coverage audit | simple decoder-side rules do not promote the stable projection: best source rule `source_is_previous_copy_end` covers `6/208`, best length rule `length_is_decoder_max` covers `58/208`, best joint rule covers `2/208`, and `265` literal payload digits remain materialized | target-text dependency not removed |
| Source tie-break artifact audit | alternate source tie policies keep identical primary cost and `50/50` stability, but do not change selected source sums (`source_sum_span=0`), so the `208/208` earliest-target-match signal is not explained as simple parser tie-break; it still depends on target chunks | target-dependent source clue retained / not promoted |
| Source candidate collapse audit | `precompute_matches` keeps only one source per length and chooses the lower `source_pos`; `130/208` projected copy events have hidden alternate sources, so the `208/208` earliest-target-match signal is a candidate-generation artifact and gate 89 is superseded | source canonicality demoted / target-text dependency remains |
| Full source exposure audit | on cutoff `60`, exposing all same-length sources preserves `10/10` stability and roundtrip; `latest_source` selects `10` non-earliest sources at only `+0.017676` primary bits, while earliest and previous-end-preferred policies match collapsed cost | local robustness / no source-rule promotion |
| Full-source latest multi-cutoff probe | with all same-length sources exposed and `latest_source` tie policy, cutoffs `50/60` roundtrip and beat raw in `30/30` evaluations; books `60..69` remain exact-path stable across both cutoffs (`10/10`) while `35` non-earliest sources are selected | partial multi-cutoff robustness / no formula promotion |
| Full-source all-policy multi-cutoff probe | with every same-length source exposed, `earliest_source`, `latest_source`, and `prefer_previous_end_then_earliest` all roundtrip and beat raw in `30/30` evaluations per policy on cutoffs `50/60`; each keeps books `60..69` stable across both cutoffs (`10/10`) | partial all-policy robustness / row0 unchanged |
| Full-source all-policy five-cutoff probe | extending the exposed-source all-policy check to cutoffs `10/20/35/50/60` gives `175/175` roundtrip/raw-positive evaluations per policy and `50/50` multi-cutoff-stable books per policy, with `0/150` unstable policy-book cases | five-cutoff parser robustness / still no source rule |
| Full-source policy invariance boundary | all policies share operation shape in `175/175` cases, but exact source-bearing signatures match in only `48/175`; `127/175` cases are pure source-choice variants | source dependency retained |
| Full-source canonical policy boundary | no static source tie policy is cost-safe: earliest and previous-end-preferred are min-cost in `170/175`, but latest-source is cheaper in five book-`63` cases | static tie-policy rejected |
| Source-policy selector boundary | the book-`63` latest-source selector matches per-case policy minima and has positive lower-bound bit balance, but it is book-specific and source fields remain materialized | audit-only selector / not generation |
| Full-source exact skeleton invariance | removing source addresses leaves an exact operation skeleton invariant in `175/175` policy-cutoff cases and `60/60` books; canonical skeleton has `261` ops, `208` copies, `53` literal runs, and `266` literal digits | source-free segmentation atlas / not generator |
| Exact skeleton dependency ledger | the stable skeleton leaves `208` copy-source fields and `53` literal payload chunks external; residual external fields drop from `609` to `261`, but atlas+external records still total `522` | dependency ledger improvement / not generator |
| Skeleton decoder ambiguity audit | grants the exact skeleton and measures decoder-side ambiguity without source/payload declarations; legal source branching alone is `2550.594` bits, literal payload branching is `883.633` bits, and the combined lower bound is `3434.227` bits (`10^1033.805` choices) | skeleton decoder generator blocked |
| Generation boundary closure audit | consolidates book order, book lengths, operation skeleton, copy sources, and literal payload after the recent gates; `0/5` dependencies have promoted generators, materialized-unit floor is `593` (`1+70+261+208+53`), and the next blocker is deriving the operation skeleton or a stronger target-stream account | current boundary: parser/atlas, not generator |
| Operation count generation audit | tests `229` source-free models for the per-book skeleton op count from book id and book length; best `context_book_mod10_x_length_bucket` hits `40/60` books and reduces full-fit paid records from `60` to `55`, but misses `20` books and has `0/5` cover-all or random-p95-beating holdout cells | audit-only context clue / op count retained |
| Operation shape-count generation audit | tests `2416` source-free models for `(op_count, literal_count)` from book id and book length; best `context_book_mod10_x_length_bucket` hits `37/60` exact shapes and reduces full-fit paid records from `60` to `58`, but misses `23` books and has `0/5` cover-all or random-p95-beating holdout cells | weaker audit-only context clue / shape count retained |
| Operation type-sequence generation audit | after granting `(op_count, literal_count)`, deterministic literal-placement rules and paid type templates are tested; best `template_book_mod5_x_shape` is exact full-fit (`60/60`, `261/261`) but carries `235` template records, is only `-26` vs type-field lookup, and has `0/5` holdout cells beating random p95 | exact template rejected as posthoc |
| Operation type-weighted length audit | after granting book length and literal/copy sequence, tests source-free weighted allocation by type, position, op index, and coarse shape; best `learned_by_shape_x_type_x_position` reaches only `14/60` exact books and `74/261` row hits, costs `363` paid records vs `261` exact length fields, and has `0/5` cover-all holdout cells | type-weighted length generator rejected |
| Operation length Markov audit | grants book lengths and operation types, then tests `11` Markov/context grammars for the `261` operation lengths; best full-fit context (`op_index_x_type`) generates only `9/60` exact books, `43/261` generated row hits, and `52/261` rowwise length hits, with `0/5` cover-all holdout cells | operation-length atlas retained |
| Operation length motif audit | tests reusable sub-book length motifs as an alternative to the one-row-per-operation atlas; best full-fit library has `2` motifs and only `-2` records while leaving `249` residual singleton lengths, and prefix/holdout motif libraries cover `0` future books without residuals | motif library not promoted |
| Operation cutpoint scaling audit | grants book lengths and tests normalized cutpoint templates scaled to each length; best full-fit `book_mod10_x_op_count` reaches `42/60` exact books and `206/261` row hits, but carries `45` templates plus `181` payload records, is `+35` records worse than the exact atlas, and has `0/5` cover-all holdout cells | cutpoint-scaling generator rejected |
| Operation cutpoint lattice audit | tests whether the `201` internal operation boundaries lie on small proportional grids after granting book length and op count; best denominator `128` gives `41/60` exact books and `159/201` hits, below same-shape random mean `161.357`, with `0/5` holdout cells beating random p95 | proportional lattice rejected |
| Operation recursive partition audit | tests `108` source-free interval-splitting policies over bisection, thirds, fourths, fifths, and golden-ratio cuts; best `latest:half` has only `2/48` exact nontrivial books and `11/201` cutpoint hits, below random p95 `14`, with `0/5` holdout cells beating random p95 | recursive partition rejected |
| Book order generation audit | existing order controls are consolidated against the current boundary: prefix evidence is not numeric-order-specific (`0` order-specific cutoffs), frontier metric is not unique (`10` perfect orders, `6` random), no non-numeric order promotes under full formula and descriptor costs, and online reparse random controls never beat numeric | canonical numeric order retained / not generated |
| Book length generation audit | the active signed-Rice book-length ledger reproduces the prior `1030 -> 566` bit compression (`anchor=151`, `k=5`) but still declares residuals; simple source-free length policies top out at `14/70` exact lengths, while exact `70/70` requires a book-index lookup carrying `70` length payloads and prefix/holdout has `0/6` cover-all cells | book-length generator rejected |
| Source-free skeleton grammar gate | `13` grammar families over operation index, prior op, book length, remaining length, phase, and book-mod/order features are tested as a generator for the exact `261`-op skeleton; best full-fit context gets only `3/60` books and `14/261` ops, is `+660.028` bits worse than a label-atlas lower bound, and has `0/5` cover-all holdout cells | simple skeleton generator rejected |
| Literal payload generation audit | after granting the exact skeleton, the remaining `53` chunks / `266` literal digits are tested against `11` source-free context families; best full-fit context carries `222` payload digits, is `+44.588` bits worse than raw uniform literal payload after paid costs, and has `0/5` holdout cells with any exact chunk | literal payload generator rejected |
| Copy source generation audit | after granting exact skeleton and literal payload, the remaining `208` source fields are tested directly; target-aware matching controls hit `208/208`, but the best decoder-visible policy hits only `8/208` chunks and `1/60` exact books, while the best source-bearing context hits `173/208` full-fit, is `+199.919` bits worse than raw source declaration, and has `0/5` cover-all holdout cells | copy-source generator rejected |
| Skeleton rule coverage audit | simple decoder-visible rules do not generate the skeleton: best op-type rule is `always_copy` at `208/261`, best length rule is `116/261`, and target-dependent availability is only `208/261` | simple generator rejected |
| Skeleton template reuse audit | exact skeleton reuse is sparse (`58` unique templates across `60` books; only pairs `43/50` and `47/62` repeat), while type-sequence motifs repeat without length-template reuse | template-library promotion rejected |
| Type motif library ledger | type motifs repeat, but a type library has `193` entries plus `60` assignments and still leaves `261` length/target residual records; full representation is `514` records, `+253` vs exact atlas | type motif library rejected |
| Copy availability type exception ledger | target-dependent copy availability contains every copy (`208/208`) and forces `36` literals, leaving `17` optional literal exceptions, but the conditioned ledger is `278` records (`+17` vs exact atlas) and depends on target text | `AUDIT_ONLY` mechanical clue |
| Target position derivation ledger | `target_start`, `remaining`, and op index are derived in `261/261` rows from cumulative lengths/book length, so target position is not an independent skeleton dependency | ledger sharpened / atlas retained |
| Optional literal exception rule audit | within available-copy rows, `length <= 5 and remaining >= 10` catches all `17` optional literal exceptions with `3` false-positive copies; shuffled controls have best-error min `12` | partial target-dependent type clue / not promoted |
| Prequential optional literal rule validation | prefix-selected exception rules beat the no-exception baseline in `4/4` suffix splits, but train-selected rules trail suffix oracle by up to `1` error and keep target/length-atlas dependencies | predictive support / not promoted |
| Operation type dependency ledger | allowing target copy availability plus the retained length atlas reduces explicit op-type dependency from `261` fields to `3` residual errors, but type+length records are still `264` (`+3` vs exact atlas) | op-type mostly derived / generator not promoted |
| Operation length dependency ledger | target positions derive from the length sequence and op-type is mostly downstream from length/copy availability, but source-free length rules cover only `116/261`, copy-length rules `55/208`, literal-length rules `5/53`, and all `261` copy-length fields remain retained | length atlas retained / generator not promoted |
| Decoder length candidate ambiguity | even granting op type and copy source, only `5/261` operation lengths are syntactically forced; `256/261` remain ambiguous with median `89` candidate lengths and `1555.548` log2 candidate-space bits | length selection remains generator blocker |
| Decoder length policy audit | fixed min/max/quartile/median/previous-length policies over candidate sets fail; the best, `max_candidate`, reaches only `63/261` (`58/208` copy lengths, `5/53` literal lengths) | simple length policy rejected |
| Segmentation decision trace | stable copy projection exposes candidate `(source,length)` spaces directly: median `80` candidate pairs, max `1248`, and `207/208` declared copies equal the source-local target max | parser trace built / row0 unchanged |
| Structural segmentation hypothesis audit | `choose the longest previous target match; break source ties by earliest source` recovers `207/208` copy pairs, versus random global-max source expectation `119.739/208`; this is target-text-aware parser evidence, not a source-free generator | promoted mechanical segmentation clue / generator not promoted |
| Parser dependency reduction ledger | conditional target-text parser projection reduces materialized records from `522` to `318` and removes `414` copy `(source,length)` fields, but full greedy source-free parsing is exact for only `39/60` non-seed books | dependency reduced conditionally / op-start atlas retained |
| Literal gap boundary audit | inside each declared literal window, stopping at best literal+copy advance matches `54/54` gaps, but first-available-match gets only `23/54` and full-suffix best-advance only `11/49` followed-by-copy gaps | local boundary clue / literal window retained |
| Online literal stop rule audit | first confirmed max-copy local peak with confirmation window `6` predicts `45/49` followed-by-copy literal stops and `50/54` gaps with book-end default; prefix selection chooses the same policy/window in `5/5` cells | partial online stop rule / four exceptions retained |
| Literal stop exception topology audit | the four online-stop misses split into four classes; best source-free flag has recall `0.750` with `9` false positives, so no exception rule is promoted | residual exceptions mapped / retained |
| Integrated online literal parser audit | freezing the online stop rule and running it end-to-end without declared literal windows or copy starts improves exact books from `39/60` greedy to `46/60`, but still drifts in `14` books and over-literalizes `329` vs stable `265` digits | partial parser improvement / not promoted |
| Integrated parser policy and drift audit | retuning the same local-peak family selects `max_copy_length:window5` in `5/5` prefix cells and improves exact books to `48/60`, but leaves `12` mixed drift books | prefix-stable partial parser / not promoted |
| Integrated parser override audit | book-start/internal/any-position immediate-copy overrides over thresholds `5..20` fail to improve on `window5:no_override`; train-selected book-start overrides lose suffix books in `2/5` prefix cells | immediate-copy rescue rejected |
| Integrated parser peak-strength audit | requiring stronger accepted local peaks (`min_peak_len 5..30`) does not improve on `48/60`; `min_peak_len6` ties but trades understops for missed-copy/overstop failures | weak-peak rescue rejected |
| Integrated parser residual context audit | `64` observable parser-state predicates are tested against the `12` residual drifts; best `peak_len_le5` reaches only TP/FP/FN `4/3/8`, precision `0.571`, recall `0.333` | simple context rule rejected |
| Global objective parser audit | book-local DP under six simple global objectives is stable but wrong: best `balanced_ops_literals` reaches only `23/60`, below the `48/60` window5 parser | crude global objective rejected |
| Feature-weighted global parser audit | `16` linear cost profiles over literal mass, copy base cost, copy reward, short-copy penalty, and book-start-copy penalty top out at `26/60`, below `48/60` | small feature cost rejected |
| Source boundary alignment audit | source-side operation/book chunk reuse fails: starts on prior operation boundaries `28/208`, ends `29/208`, single-prior-chunk copies `0/208`, and the best boundary-aware tie policy gets `206/208` vs `207/208` for earliest source | block-copy segmentation hypothesis rejected |
| Single drift repair oracle audit | replacing the first divergent operation with the stable projection repairs `11/12` residual parser books; allowing two such oracle repairs reaches `60/60`, with histogram `{1: 11, 2: 1}` | blocker localized to first-drift classifier / no rule promoted |
| Observable repair policy audit | `36` non-oracle repair templates are tested against the gate-16 oracle map; best remains baseline `window5` at `48/60`, and prequential selection matches oracle in only `3/5` cells | simple repair classifier rejected |
| Conditional repair classifier audit | a restricted predicate-action classifier finds `if_peak_len_le5_then_skip_to_next_peak_ge5`, improving the integrated parser from `48/60` to `50/60` with `5/5` prequential stability, but leaving `10` mixed drift books | prefix-stable partial repair / not promoted |
| Two-stage conditional repair audit | adding a second observable predicate-action rule after the gate-18 classifier gives `0` exact-book gain; best remains the single-stage `50/60` parser and second-stage train selection matches oracle in only `3/5` cells | second simple repair layer rejected |
| Post-repair residual oracle audit | with the `50/60` parser active, one stable-projection correction repairs `9/10` residual books and two corrections reach `60/60`; only book `20` still needs two oracle corrections | residual localized / oracle-only |
| Post-repair residual feature audit | the best observable residual predicate catches `6/10` residuals but also fires on `13` clean controls; the best zero-false-positive predicate catches only `1/10` | single residual feature flag rejected |
| Residual branch continuation audit | all `10/10` stable residual operations are available as observable branches, but the best non-oracle continuation objective catches only `6/10` and changes `20` clean controls | simple path objective rejected |
| Branch ranker prequential audit | the active baseline is `224/234` with `0/10` residual hits; best full-fit ranker is `223/234` with `0/10`; residual-only reaches `7/10` but changes `221` clean controls | learned branch ranker rejected |
| Contextual mode selector audit | best full-fit context table reaches `229/234`, resolving `5/10` residuals with `0` clean-control changes, but prefix/holdout has only `1/5` zero-false-control cells and `1/5` all-residual-covered cells | weak full-fit clue / not promoted |
| Contextual mode stability audit | the `context_combo` full-fit `5/10` residual gain drops to `1/10` under leave-one-book and `0/10` under leave-context-out; support pruning collapses most of the gain | weak post-hoc clue / not parser |
| Hierarchical context backoff audit | context hierarchies preserve the full-fit `5/10` residual ceiling, but prequential selection has only `1/5` zero-false-control cells and residual gains require false clean-control changes | hierarchical backoff rejected |
| Observable decision tree policy audit | a small observable tree improves full-fit to `228/234` and `4/10` residuals with `0` clean-control changes, but prefix/holdout recovers `0` held-out residuals in every split that contains residuals | small finite-state parser rejected |
| Target boundary recurrence audit | scoring branches by recurrence of target-side boundary context performs poorly: best recurrence policy reaches only `31/234`, `1/10` residuals, and `194` clean false changes; random boundary controls do better on total hits | recurrent-boundary segmentation rejected |
| Future copy opportunity audit | scoring branches by near-future copy availability reaches only `96/234`, `2/10` residuals, and `130` clean false changes; randomized feature controls are stronger on total hits | copy-opportunity lookahead rejected |
| Source state continuity audit | book-local previous-copy continuity is stronger than shuffled controls and best `min_source_delta` catches `6/10` residuals, but it changes `13` clean controls and has `0/5` zero-clean-false-change holdout cells | source-state continuity rejected |
| Global source state continuity audit | even granting stable-projection history as global carried source state, best `min_source_delta` still catches only `6/10` residuals, changes `13` clean controls, and has `0/5` zero-clean-false-change holdout cells | carryover source-state upper bound rejected |
| Phase/grid segmentation audit | simple cycles `2/3/4/5/8/10/16/20` over target boundaries, lengths, source, source end, and source-target phase produce only a weak `source_mod0_10/20` full-fit clue: `1/10` residual, `0` clean false changes, and no held-out residual recovery | phase/grid parser rejected |
| Context nearest-branch audit | nearest-neighbor recurrence over raw target digit context is worse than the active baseline: best leave-one-book policy gets `216/234`, `0/10` residuals, and `8` clean false changes; shuffled labels match or exceed it | raw-context recurrence rejected |
| Structural signal consensus audit | combining source-state, phase/grid, future-copy, and boundary-recurrence votes preserves clean controls only by staying at the active baseline: best consensus is `224/234`, `0/10` residuals, `0` clean false changes | weak-signal consensus rejected |
| Structural vote residual decomposition | residual support and clean-control risk overlap: threshold `3` catches only books `16/39` but also moves `18` clean controls; threshold `4` leaves book `39` plus `1` clean false move | weak-signal frontier decomposed / no rule |
| Seed primacy audit | treating books `0..9` as declared seeds covers `8664/9567` non-seed digits, below random k=10 median `9005`, while the best k=10 posthoc seed covers `9734` digits; seed-set choice remains external | `AUDIT_ONLY_COMPRESSION` / no seed-origin promotion |
| Prequential seed selection audit | prefix-trained greedy seeds beat random median in `7/7` cells and p95 in `6/7`, but still trail suffix-oracle posthoc seeds; operational prefixes beat random median in only `1/7` | partial predictive seed signal / not promoted |
| Seed primacy integration audit | the final seed report is integrated into the main prequential/row0 boundary; operational `0..9` is rejected, posthoc high-coverage cores stay compression-only, and prequential seed selection is partial but not promotable | seed front incorporated / no origin or row0 change |
| Seed requirement closure audit | final seed front is checked against the requested baselines, metrics, and controls: operational, random, permuted, centrality, metadata/bookcase, family holdout, declaration cost, and prequential checks all close `13/13` | requirements closed / still audit-only |
| Chayenne spacing/provenance audit | the PortalTibia primary-source answer has two numeric blocks separated by a visible marker; the joined 49-digit string has `0` corpus occurrences, while the source split at boundary `36` is the unique full split whose two sides are both attested book substrings; shuffle controls are `0/2000` for block/join hits and `0/1000` for joined full-split hits | `PROMOTED_MECHANICAL_CLUE` / row0 and plaintext unchanged |
| Tape MDL gain | Rough total gain `6597.1` bits over literal module table | accepted compression evidence |
| Residual exact repeats | MDL-pruned `exact_repeat` covers `1683/2083` residual digits; about `400` digits remain literal | accepted secondary mechanical layer |
| Chayenne holdout | minLen=8 coverage `45/49`; Avar Tar minLen=8 coverage `0/115` | secondary validation only |
| Zero omission | local previous/next context and geometry predict omission better than code-only | supporting render layer |

Primary sources:
[tape_based_formula_report.md](../../analysis/generator_search_20260618/tape_based_formula_report.md),
[literal_reference_benchmark_controls.md](../../analysis/authorial_mechanism_20260620/reports/test_results/06_literal_reference_benchmark_controls.md),
[authorial_provenance_source_notes.md](../../analysis/authorial_provenance_audit_20260621/reports/authorial_provenance_source_notes.md),
[chayenne_spacing_audit.md](../../analysis/authorial_provenance_audit_20260621/reports/test_results/01_chayenne_spacing_audit.md),
[tape_inventory_self_reference_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/07_tape_inventory_self_reference_search.md),
[hierarchical_reference_formula_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/08_hierarchical_reference_formula_compile.md),
[sequential_lz_book_formula_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/10_sequential_lz_book_formula_compile.md),
[sequential_lz_order_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/11_sequential_lz_order_search.md),
[sequential_lz_literal_run_cost_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/12_sequential_lz_literal_run_cost_compile.md),
[sequential_lz_dp_parse_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/13_sequential_lz_dp_parse_compile.md),
[copy_source_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/14_copy_source_address_model_search.md),
[copy_graph_provenance_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/15_copy_graph_provenance_audit.md),
[structured_physical_order_lz_test.md](../../analysis/authorial_mechanism_20260620/reports/test_results/16_structured_physical_order_lz_test.md),
[literal_seed_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/17_literal_seed_address_model_search.md),
[literal_seed_grouped_mode_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/18_literal_seed_grouped_mode_search.md),
[copy_hub_macro_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/19_copy_hub_macro_model_search.md),
[restricted_hybrid_vocabulary_reparse.md](../../analysis/authorial_mechanism_20260620/reports/test_results/20_restricted_hybrid_vocabulary_reparse.md),
[dp_min_len_sweep_control.md](../../analysis/authorial_mechanism_20260620/reports/test_results/21_dp_min_len_sweep_control.md),
[copy_length_code_reparse.md](../../analysis/authorial_mechanism_20260620/reports/test_results/22_copy_length_code_reparse.md),
[copy_length_grid_sweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/23_copy_length_grid_sweep.md),
[rice_copy_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/24_rice_copy_address_model_search.md),
[literal_run_length_code_reparse.md](../../analysis/authorial_mechanism_20260620/reports/test_results/25_literal_run_length_code_reparse.md),
[joint_length_code_grid_sweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/26_joint_length_code_grid_sweep.md),
[literal_payload_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/27_literal_payload_model_search.md),
[current_formula_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/28_current_formula_address_model_search.md),
[literal_to_copy_repair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/29_literal_to_copy_repair_search.md),
[post_repair_payload_alpha_sweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/30_post_repair_payload_alpha_sweep.md),
[post_repair_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/31_post_repair_address_model_search.md),
[literal_to_copy_pair_repair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/32_literal_to_copy_pair_repair_search.md),
[book_length_ledger_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/33_book_length_ledger_search.md),
[book_length_multi_anchor_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/34_book_length_multi_anchor_search.md),
[digit_only_copy_address_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/35_digit_only_copy_address_compile.md),
[digit_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/36_digit_address_model_search.md),
[digit_address_literal_repair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/37_digit_address_literal_repair_search.md),
[post_digit_repair_payload_alpha_sweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/38_post_digit_repair_payload_alpha_sweep.md),
[post_digit_repair_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/39_post_digit_repair_address_model_search.md),
[item_type_ledger_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/40_item_type_ledger_compile.md),
[markov_item_type_ledger_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/41_markov_item_type_ledger_compile.md),
[book_start_item_type_ledger_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/42_book_start_item_type_ledger_compile.md),
[literal_forces_copy_type_ledger_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/43_literal_forces_copy_type_ledger_compile.md),
[remaining_short_forces_literal_type_ledger_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/44_remaining_short_forces_literal_type_ledger_compile.md),
[remaining_short_literal_length_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/45_remaining_short_literal_length_compile.md),
[forced_length_literal_repair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/46_forced_length_literal_repair_search.md),
[post_forced_repair_payload_alpha_sweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/47_post_forced_repair_payload_alpha_sweep.md),
[post_forced_repair_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/48_post_forced_repair_address_model_search.md),
[post_forced_repair_pair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/49_post_forced_repair_pair_search.md),
[post_forced_repair_triple_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/50_post_forced_repair_triple_search.md),
[post_forced_repair_quad_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/51_post_forced_repair_quad_search.md),
[post_forced_repair_quint_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/52_post_forced_repair_quint_search.md),
[post_forced_repair_sext_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/53_post_forced_repair_sext_search.md),
[post_forced_repair_sept_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/54_post_forced_repair_sept_search.md),
[post_forced_repair_oct_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/55_post_forced_repair_oct_search.md),
[post_forced_repair_nonet_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/56_post_forced_repair_nonet_search.md),
[post_forced_repair_decet_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/57_post_forced_repair_decet_search.md),
[post_forced_repair_eleven_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/58_post_forced_repair_eleven_search.md),
[post_forced_repair_twelve_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/59_post_forced_repair_twelve_search.md),
[post_forced_repair_high_order_exhaustion.md](../../analysis/authorial_mechanism_20260620/reports/test_results/60_post_forced_repair_high_order_exhaustion.md),
[post_contextual_parameter_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/68_post_contextual_parameter_resweep.md),
[bounded_copy_length_code_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/69_bounded_copy_length_code_compile.md),
[min_len_bounded_copy_address_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/70_min_len_bounded_copy_address_compile.md),
[minaddr_local_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/71_minaddr_local_frontier.md),
[post_minaddr_repair_local_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/72_post_minaddr_repair_local_frontier.md),
[post_minaddr_repair2_local_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/73_post_minaddr_repair2_local_frontier.md),
[post_repair2_parameter_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/74_post_repair2_parameter_resweep.md),
[post_repair2_pair_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/75_post_repair2_pair_frontier.md),
[post_repair2_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/76_post_repair2_address_model_search.md),
[post_repair2_copy_order_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/77_post_repair2_copy_order_search.md),
[post_repair2_adaptive_copy_length_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/78_post_repair2_adaptive_copy_length_compile.md),
[post_adaptive_copy_length_local_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/79_post_adaptive_copy_length_local_frontier.md),
[post_adaptive_parameter_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/80_post_adaptive_parameter_resweep.md),
[post_adaptive_pair_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/81_post_adaptive_pair_frontier.md),
[post_adaptive_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/82_post_adaptive_address_model_search.md),
[post_adaptive_copy_order_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/83_post_adaptive_copy_order_search.md),
[post_adaptive_copy_length_context_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/84_post_adaptive_copy_length_context_search.md),
[post_midpoint_local_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/85_post_midpoint_local_frontier.md),
[post_midpoint_parameter_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/86_post_midpoint_parameter_resweep.md),
[post_midpoint_alpha1_local_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/87_post_midpoint_alpha1_local_frontier.md),
[post_midpoint_alpha1_pair_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/88_post_midpoint_alpha1_pair_frontier.md),
[post_midpoint_alpha1_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/89_post_midpoint_alpha1_address_model_search.md),
[post_midpoint_alpha1_copy_order_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/90_post_midpoint_alpha1_copy_order_search.md),
[post_midpoint_alpha1_copy_length_context_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/91_post_midpoint_alpha1_copy_length_context_resweep.md),
[post_midpoint_alpha1_context_alpha_grid.md](../../analysis/authorial_mechanism_20260620/reports/test_results/92_post_midpoint_alpha1_context_alpha_grid.md),
[post_midpoint_alpha1_literal_payload_context_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/93_post_midpoint_alpha1_literal_payload_context_search.md),
[post_midpoint_alpha1_top60_triple_probe.md](../../analysis/authorial_mechanism_20260620/reports/test_results/94_post_midpoint_alpha1_top60_triple_probe.md),
[post_midpoint_alpha1_item_type_context_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/95_post_midpoint_alpha1_item_type_context_search.md),
[post_itemctx_parameter_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/96_post_itemctx_parameter_resweep.md),
[post_itemctx_param_local_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/97_post_itemctx_param_local_frontier.md),
[post_itemctx_param_pair_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/98_post_itemctx_param_pair_frontier.md),
[post_itemctx_param_address_model_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/99_post_itemctx_param_address_model_search.md),
[post_itemctx_param_copy_order_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/100_post_itemctx_param_copy_order_search.md),
[post_itemctx_param_copy_length_context_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/101_post_itemctx_param_copy_length_context_resweep.md),
[post_itemctx_param_context_alpha_grid.md](../../analysis/authorial_mechanism_20260620/reports/test_results/102_post_itemctx_param_context_alpha_grid.md),
[post_itemctx_param_literal_payload_context_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/103_post_itemctx_param_literal_payload_context_search.md),
[post_itemctx_param_item_type_context_family_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/104_post_itemctx_param_item_type_context_family_search.md),
[post_itemctx_param_payload_item_type_pair_context_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/105_post_itemctx_param_payload_item_type_pair_context_search.md),
[post_itemctx_param_copy_length_item_type_pair_context_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/106_post_itemctx_param_copy_length_item_type_pair_context_search.md),
[post_itemctx_param_payload_copy_length_item_type_triple_context_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/107_post_itemctx_param_payload_copy_length_item_type_triple_context_search.md),
[post_itemctx_param_copy_length_alpha_item_type_pair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/108_post_itemctx_param_copy_length_alpha_item_type_pair_search.md),
[post_itemctx_param_copy_length_alpha_payload_pair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/109_post_itemctx_param_copy_length_alpha_payload_pair_search.md),
[post_itemctx_param_copy_alpha_payload_item_type_triple_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/110_post_itemctx_param_copy_alpha_payload_item_type_triple_search.md),
[post_itemctx_param_copy_length_context_alpha_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/111_post_itemctx_param_copy_length_context_alpha_resweep.md),
[post_itemctx_param_literal_payload_context_alpha_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/112_post_itemctx_param_literal_payload_context_alpha_resweep.md),
[post_itemctx_param_copy_payload_context_alpha_pair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/113_post_itemctx_param_copy_payload_context_alpha_pair_search.md),
[post_itemctx_param_copy_payload_item_context_alpha_triple_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/114_post_itemctx_param_copy_payload_item_context_alpha_triple_search.md),
[post_itemctx_param_address_copy_order_pair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/115_post_itemctx_param_address_copy_order_pair_search.md),
[post_itemctx_param_address_item_type_pair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/116_post_itemctx_param_address_item_type_pair_search.md),
[post_itemctx_param_address_payload_context_alpha_pair_search.md](../../analysis/authorial_mechanism_20260620/reports/test_results/117_post_itemctx_param_address_payload_context_alpha_pair_search.md),
[prequential_generation_model_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/118_prequential_generation_model_audit.md),
[row0_origin_frontier_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/119_row0_origin_frontier_audit.md),
[prequential_order_control_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/120_prequential_order_control_audit.md),
[prequential_component_ablation_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/121_prequential_component_ablation_audit.md),
[simplified_generation_profile_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/122_simplified_generation_profile_compile.md),
[item_type_split_only_formula_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/123_item_type_split_only_formula_compile.md),
[item_type_split_only_alpha_resweep.md](../../analysis/authorial_mechanism_20260620/reports/test_results/124_item_type_split_only_alpha_resweep.md),
[item_type_op_shape_boundary_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/33_item_type_op_shape_boundary_gate.md),
[prequential_and_row0_origin_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/125_prequential_and_row0_origin_audit.md),
[prequential_and_row0_origin_audit_20260621.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/prequential_and_row0_origin_audit.md),
[recipe_externality_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/04_recipe_externality_audit.md),
[row0_hypothesis_requirement_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/05_row0_hypothesis_requirement_audit.md),
[recipe_reparse_evidence_matrix.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/06_recipe_reparse_evidence_matrix.md),
[recipe_reparse_trainset_multicutoff.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/07_recipe_reparse_trainset_multicutoff.md),
[recipe_reparse_family_holdout.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/08_recipe_reparse_family_holdout.md),
[leave_one_book_out_family_excluded_source_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/16_leave_one_book_out_family_excluded_source_audit.md),
[online_prefix_book_frontier_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/17_online_prefix_book_frontier_audit.md),
[online_bootstrap_seed_policy_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/18_online_bootstrap_seed_policy_audit.md),
[seeded_online_formula_rescore_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/19_seeded_online_formula_rescore_audit.md),
[seeded_rescore_loss_decomposition.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/20_seeded_rescore_loss_decomposition.md),
[seed_exception_signal_cost_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/21_seed_exception_signal_cost_audit.md),
[online_order_frontier_controls.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/22_online_order_frontier_controls.md),
[order_frontier_promotion_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/23_order_frontier_promotion_gate.md),
[row0_origin_parallel_report.md](../../analysis/row0_origin_parallel_20260621/reports/final_row0_origin_parallel_report.md),
[row0_next_frontier_report.md](../../analysis/row0_origin_parallel_20260621/reports/row0_next_frontier_report.md),
[row0_paid_anchor_reduction_gate.md](../../analysis/row0_origin_parallel_20260621/reports/test_results/159_row0_paid_anchor_reduction_gate.md),
[recent_formula_row0_compatibility_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/70_recent_formula_row0_compatibility_audit.md),
[row0_real_origin_search_report.md](../../analysis/row0_real_origin_search_20260621/reports/row0_real_origin_search_report.md),
[final_formula_dependency_refresh_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/71_final_formula_dependency_refresh_gate.md),
[final_source_length_parser_feasibility_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/72_final_source_length_parser_feasibility_audit.md),
[book_local_source_length_parser_probe.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/73_book_local_source_length_parser_probe.md),
[sparse_hard_book_source_length_parser_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/74_sparse_hard_book_source_length_parser_gate.md),
[post_parser_row0_compatibility_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/75_post_parser_row0_compatibility_audit.md),
[cutoff60_sparse_suffix_parser_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/76_cutoff60_sparse_suffix_parser_gate.md),
[multi_cutoff_sparse_suffix_parser_validation.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/77_multi_cutoff_sparse_suffix_parser_validation.md),
[multi_cutoff_parser_path_stability_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/78_multi_cutoff_parser_path_stability_audit.md),
[unstable_parser_path_decomposition_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/79_unstable_parser_path_decomposition_audit.md),
[boundary_policy_stability_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/80_boundary_policy_stability_gate.md),
[boundary_instability_cost_decomposition_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/81_boundary_instability_cost_decomposition_gate.md),
[component_neutralized_path_stability_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/82_component_neutralized_path_stability_gate.md),
[component_neutralized_residual_tradeoff_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/83_component_neutralized_residual_tradeoff_audit.md),
[residual_literal_payload_neutralization_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/84_residual_literal_payload_neutralization_gate.md),
[book49_residual_split_cause_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/85_book49_residual_split_cause_audit.md),
[global_item_literal_length_control_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/86_global_item_literal_length_control_gate.md),
[stable_path_projection_boundary_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/87_stable_path_projection_boundary_audit.md),
[decoder_side_rule_coverage_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/88_decoder_side_rule_coverage_audit.md),
[source_tiebreak_artifact_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/89_source_tiebreak_artifact_audit.md),
[source_candidate_collapse_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/90_source_candidate_collapse_audit.md),
[full_source_exposure_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/91_full_source_exposure_audit.md),
[full_source_latest_multicutoff_probe.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/92_full_source_latest_multicutoff_probe.md),
[full_source_all_policy_multicutoff_probe.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/93_full_source_all_policy_multicutoff_probe.md),
[full_source_all_policy_fivecutoff_probe.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/94_full_source_all_policy_fivecutoff_probe.md),
[full_source_policy_invariance_boundary.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/95_full_source_policy_invariance_boundary.md),
[full_source_canonical_policy_boundary.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/96_full_source_canonical_policy_boundary.md),
[source_policy_selector_boundary.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/97_source_policy_selector_boundary.md),
[full_source_exact_skeleton_invariance.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/98_full_source_exact_skeleton_invariance.md),
[exact_skeleton_dependency_ledger.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/99_exact_skeleton_dependency_ledger.md),
[final_generation_boundary_closure_audit.md](../../analysis/generation_boundary_closure_audit_20260621/reports/final_generation_boundary_closure_audit.md),
[generation_boundary_closure_audit.md](../../analysis/generation_boundary_closure_audit_20260621/reports/test_results/01_generation_boundary_closure_audit.md),
[final_operation_count_generation_audit.md](../../analysis/operation_count_generation_audit_20260621/reports/final_operation_count_generation_audit.md),
[operation_count_generation_gate.md](../../analysis/operation_count_generation_audit_20260621/reports/test_results/01_operation_count_generation_gate.md),
[final_operation_shape_count_generation_audit.md](../../analysis/operation_shape_count_generation_audit_20260621/reports/final_operation_shape_count_generation_audit.md),
[operation_shape_count_generation_gate.md](../../analysis/operation_shape_count_generation_audit_20260621/reports/test_results/01_operation_shape_count_generation_gate.md),
[final_operation_type_sequence_generation_audit.md](../../analysis/operation_type_sequence_generation_audit_20260621/reports/final_operation_type_sequence_generation_audit.md),
[operation_type_sequence_generation_gate.md](../../analysis/operation_type_sequence_generation_audit_20260621/reports/test_results/01_operation_type_sequence_generation_gate.md),
[final_operation_length_markov_audit.md](../../analysis/operation_length_markov_audit_20260621/reports/final_operation_length_markov_audit.md),
[operation_length_markov_gate.md](../../analysis/operation_length_markov_audit_20260621/reports/test_results/01_operation_length_markov_gate.md),
[final_operation_length_motif_audit.md](../../analysis/operation_length_motif_audit_20260621/reports/final_operation_length_motif_audit.md),
[operation_length_motif_library_gate.md](../../analysis/operation_length_motif_audit_20260621/reports/test_results/01_operation_length_motif_library_gate.md),
[final_operation_cutpoint_scaling_audit.md](../../analysis/operation_cutpoint_scaling_audit_20260621/reports/final_operation_cutpoint_scaling_audit.md),
[operation_cutpoint_scaling_gate.md](../../analysis/operation_cutpoint_scaling_audit_20260621/reports/test_results/01_operation_cutpoint_scaling_gate.md),
[final_operation_cutpoint_lattice_audit.md](../../analysis/operation_cutpoint_lattice_audit_20260621/reports/final_operation_cutpoint_lattice_audit.md),
[operation_cutpoint_lattice_gate.md](../../analysis/operation_cutpoint_lattice_audit_20260621/reports/test_results/01_operation_cutpoint_lattice_gate.md),
[final_operation_recursive_partition_audit.md](../../analysis/operation_recursive_partition_audit_20260621/reports/final_operation_recursive_partition_audit.md),
[operation_recursive_partition_gate.md](../../analysis/operation_recursive_partition_audit_20260621/reports/test_results/01_operation_recursive_partition_gate.md),
[final_book_order_generation_audit.md](../../analysis/book_order_generation_audit_20260621/reports/final_book_order_generation_audit.md),
[book_order_dependency_gate.md](../../analysis/book_order_generation_audit_20260621/reports/test_results/01_book_order_dependency_gate.md),
[final_book_length_generation_audit.md](../../analysis/book_length_generation_audit_20260621/reports/final_book_length_generation_audit.md),
[book_length_generation_gate.md](../../analysis/book_length_generation_audit_20260621/reports/test_results/02_book_length_generation_gate.md),
[final_source_free_skeleton_generation_audit.md](../../analysis/source_free_skeleton_generation_audit_20260621/reports/final_source_free_skeleton_generation_audit.md),
[source_free_skeleton_grammar_gate.md](../../analysis/source_free_skeleton_generation_audit_20260621/reports/test_results/02_source_free_skeleton_grammar_gate.md),
[final_literal_payload_generation_audit.md](../../analysis/literal_payload_generation_audit_20260621/reports/final_literal_payload_generation_audit.md),
[literal_payload_context_gate.md](../../analysis/literal_payload_generation_audit_20260621/reports/test_results/02_literal_payload_context_gate.md),
[final_copy_source_generation_audit.md](../../analysis/copy_source_generation_audit_20260621/reports/final_copy_source_generation_audit.md),
[copy_source_context_gate.md](../../analysis/copy_source_generation_audit_20260621/reports/test_results/03_copy_source_context_gate.md),
[skeleton_rule_coverage_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/100_skeleton_rule_coverage_audit.md),
[skeleton_template_reuse_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/101_skeleton_template_reuse_audit.md),
[type_motif_library_ledger.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/102_type_motif_library_ledger.md),
[copy_availability_type_exception_ledger.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/103_copy_availability_type_exception_ledger.md),
[target_position_derivation_ledger.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/104_target_position_derivation_ledger.md),
[optional_literal_exception_rule_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/105_optional_literal_exception_rule_audit.md),
[prequential_optional_literal_rule_validation.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/106_prequential_optional_literal_rule_validation.md),
[operation_type_dependency_ledger.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/107_operation_type_dependency_ledger.md),
[recent_gates_row0_compatibility_refresh.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/108_recent_gates_row0_compatibility_refresh.md),
[operation_length_dependency_ledger.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/110_operation_length_dependency_ledger.md),
[decoder_length_candidate_ambiguity_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/111_decoder_length_candidate_ambiguity_audit.md),
[decoder_length_policy_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/112_decoder_length_policy_audit.md),
[final_segmentation_decision_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/final_segmentation_decision_audit.md),
[segmentation_decision_trace.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/01_segmentation_decision_trace.md),
[structural_segmentation_hypothesis_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/02_structural_segmentation_hypothesis_audit.md),
[parser_dependency_reduction_ledger.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/04_parser_dependency_reduction_ledger.md),
[literal_gap_boundary_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/05_literal_gap_boundary_audit.md),
[online_literal_stop_rule_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/06_online_literal_stop_rule_audit.md),
[literal_stop_exception_topology_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/07_literal_stop_exception_topology_audit.md),
[integrated_online_literal_parser_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/08_integrated_online_literal_parser_audit.md),
[integrated_parser_policy_and_drift_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/09_integrated_parser_policy_and_drift_audit.md),
[integrated_parser_override_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/10_integrated_parser_override_audit.md),
[integrated_parser_peak_strength_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/11_integrated_parser_peak_strength_audit.md),
[integrated_parser_residual_context_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/12_integrated_parser_residual_context_audit.md),
[global_objective_parser_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/13_global_objective_parser_audit.md),
[feature_weighted_global_parser_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/14_feature_weighted_global_parser_audit.md),
[source_boundary_alignment_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/15_source_boundary_alignment_audit.md),
[single_drift_repair_oracle_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/16_single_drift_repair_oracle_audit.md),
[observable_repair_policy_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/17_observable_repair_policy_audit.md),
[conditional_repair_classifier_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/18_conditional_repair_classifier_audit.md),
[two_stage_conditional_repair_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/19_two_stage_conditional_repair_audit.md),
[post_repair_residual_oracle_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/20_post_repair_residual_oracle_audit.md),
[post_repair_residual_feature_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/21_post_repair_residual_feature_audit.md),
[residual_branch_continuation_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/22_residual_branch_continuation_audit.md),
[branch_ranker_prequential_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/23_branch_ranker_prequential_audit.md),
[contextual_mode_selector_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/24_contextual_mode_selector_audit.md),
[contextual_mode_stability_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/25_contextual_mode_stability_audit.md),
[hierarchical_context_backoff_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/26_hierarchical_context_backoff_audit.md),
[observable_decision_tree_policy_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/27_observable_decision_tree_policy_audit.md),
[target_boundary_recurrence_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/28_target_boundary_recurrence_audit.md),
[future_copy_opportunity_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/29_future_copy_opportunity_audit.md),
[source_state_continuity_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/30_source_state_continuity_audit.md),
[global_source_state_continuity_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/31_global_source_state_continuity_audit.md),
[phase_grid_segmentation_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/32_phase_grid_segmentation_audit.md),
[context_nearest_branch_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/33_context_nearest_branch_audit.md),
[structural_signal_consensus_audit.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/34_structural_signal_consensus_audit.md),
[structural_vote_residual_decomposition.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/35_structural_vote_residual_decomposition.md),
[book_skeleton_alignment_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/49_book_skeleton_alignment_gate.md),
[source_interval_context_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/50_source_interval_context_gate.md),
[source_interval_precision_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/51_source_interval_precision_gate.md),
[source_interval_observable_precision_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/52_source_interval_observable_precision_gate.md),
[source_interval_cost_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/53_source_interval_cost_gate.md),
[book_start_copy_subclass_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/54_book_start_copy_subclass_gate.md),
[observable_signature_support_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/55_observable_signature_support_gate.md),
[sequential_signature_support_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/56_sequential_signature_support_gate.md),
[latent_path_state_budget_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/57_latent_path_state_budget_gate.md),
[beam_survival_budget_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/58_beam_survival_budget_gate.md),
[beam_rank_selector_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/59_beam_rank_selector_gate.md),
[beam_selector_stability_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/60_beam_selector_stability_gate.md),
[beam_hierarchical_backoff_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/61_beam_hierarchical_backoff_gate.md),
[residual_patch_program_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/62_residual_patch_program_gate.md),
[beam_markov_state_selector_gate.md](../../analysis/segmentation_decision_audit_20260621/reports/test_results/63_beam_markov_state_selector_gate.md),
[final_seed_primacy_audit.md](../../analysis/seed_primacy_audit_20260621/reports/final_seed_primacy_audit.md),
[prequential_seed_selection_audit.md](../../analysis/seed_primacy_audit_20260621/reports/test_results/03_prequential_seed_selection_audit.md),
[seed_requirement_closure_audit.md](../../analysis/seed_primacy_audit_20260621/reports/test_results/04_seed_requirement_closure_audit.md),
[seed_primacy_integration_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/109_seed_primacy_integration_audit.md),
[prequential_recipe_reparse_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/126_prequential_recipe_reparse_audit.md),
[prequential_recipe_reparse_controls.md](../../analysis/authorial_mechanism_20260620/reports/test_results/127_prequential_recipe_reparse_controls.md),
[prequential_recipe_reparse_trainset_controls.md](../../analysis/authorial_mechanism_20260620/reports/test_results/128_prequential_recipe_reparse_trainset_controls.md),
[online_deterministic_reparse_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/129_online_deterministic_reparse_compile.md),
[online_reparse_order_control_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/130_online_reparse_order_control_audit.md),
[online_formula_recipe_prune_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/131_online_formula_recipe_prune_audit.md),
[canonical_online_recipe_formula_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/132_canonical_online_recipe_formula_compile.md),
[literal_length_derived_recipe_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/133_literal_length_derived_recipe_compile.md),
[op_type_derived_recipe_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/134_op_type_derived_recipe_compile.md),
[recipe_representation_dependency_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/30_recipe_representation_dependency_gate.md),
[copy_source_canonicality_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/135_copy_source_canonicality_audit.md),
[source_canonicality_decodability_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/25_source_canonicality_decodability_gate.md),
[online_copy_source_canonicality_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/140_online_copy_source_canonicality_audit.md),
[copy_length_default_decodability_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/136_copy_length_default_decodability_audit.md),
[copy_length_derivation_boundary_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/32_copy_length_derivation_boundary_gate.md),
[copy_source_default_decodability_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/137_copy_source_default_decodability_audit.md),
[default_exception_prequential_validation.md](../../analysis/authorial_mechanism_20260620/reports/test_results/141_default_exception_prequential_validation.md),
[default_exception_component_profile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/142_default_exception_component_profile.md),
[current_literal_payload_profile_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/143_current_literal_payload_profile_audit.md),
[copy_source_distance_model_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/144_copy_source_distance_model_audit.md),
[current_active_prequential_profile_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/145_current_active_prequential_profile_audit.md),
[current_active_profile_boundary_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/34_current_active_profile_boundary_gate.md),
[copy_source_state_compression_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/35_copy_source_state_compression_gate.md),
[active_reparse_state_boundary_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/146_active_reparse_state_boundary_audit.md),
[copy_source_state_free_default_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/147_copy_source_state_free_default_audit.md),
[source_selection_derivation_boundary_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/31_source_selection_derivation_boundary_gate.md),
[source_length_joint_derivability_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/49_source_length_joint_derivability_audit.md),
[source_canonicality_tradeoff_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/50_source_canonicality_tradeoff_audit.md),
[copy_length_segmentation_exception_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/51_copy_length_segmentation_exception_audit.md),
[targetmax_resegmentation_candidate_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/52_targetmax_resegmentation_candidate_audit.md),
[targetmax_resegmentation_formula_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/53_targetmax_resegmentation_formula_gate.md),
[targetmax_resegmentation_second_pass_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/54_targetmax_resegmentation_second_pass_gate.md),
[targetmax_resegmentation_saturation_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/55_targetmax_resegmentation_saturation_gate.md),
[post_targetmax_source_substitution_frontier_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/56_post_targetmax_source_substitution_frontier_gate.md),
[post_targetmax_source_substitution_second_pass_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/57_post_targetmax_source_substitution_second_pass_gate.md),
[post_targetmax_source_substitution_stop_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/58_post_targetmax_source_substitution_stop_audit.md),
[copy_length_midpoint_context_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/148_copy_length_midpoint_context_audit.md),
[copy_length_midpoint_context_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/27_copy_length_midpoint_context_gate.md),
[literal_copy_availability_boundary_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/149_literal_copy_availability_boundary_audit.md),
[literal_copy_availability_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/28_literal_copy_availability_gate.md),
[optional_literal_copy_repair_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/150_optional_literal_copy_repair_frontier.md),
[cross_op_optional_literal_copy_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/151_cross_op_optional_literal_copy_frontier.md),
[cross_op_near_tie_decomposition.md](../../analysis/authorial_mechanism_20260620/reports/test_results/152_cross_op_near_tie_decomposition.md),
[cross_op_source_break_even_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/153_cross_op_source_break_even_audit.md),
[copy_source_structural_context_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/154_copy_source_structural_context_audit.md),
[source_blocker_structural_context_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/24_source_blocker_structural_context_gate.md),
[literal_payload_default_decodability_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/138_literal_payload_default_decodability_audit.md),
[literal_payload_structural_context_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/139_literal_payload_structural_context_audit.md),
[literal_payload_model_gate.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/29_literal_payload_model_gate.md),
[residual_coverage_mdl_report.md](../../analysis/mechanism_model_20260618/residual_coverage_mdl_report.md),
[external_holdout_chayenne_ytc_report.md](../../analysis/generator_search_20260618/external_holdout_chayenne_ytc_report.md),
[zero_compact_rule_report.md](../../analysis/generator_search_20260618/zero_compact_rule_report.md).

## Weak Clues

These are real or suggestive mechanical signals, but they are not promoted as
the origin formula.

| Clue | Why it remains weak |
|---|---|
| `6<->9` orbit | compresses/structures a small part of the pair table, but mixed-orbit overhead and controls prevent promotion |
| E layer | diagonal/high-block E pressure is real locally, but blockers, residuals, and render-origin probes fail controls |
| Orientation/render | ordered `ab` vs `ba` has strong context signal, but does not generalize as a grid formula |
| Chayenne | compatible with 469 module/copy layer, but not an attested plaintext or training source |
| ML zero signal | confirms local render predictability; does not discover a matrix formula |
| Eye/blink arity | `5 eyes -> C(5,2)=10 -> 55 cells` matches the row0 scale, but K5/5x2 tests reject it as the pair-cell formula |
| Hierarchical provenance | book/tape/inventory provenance improves generation, but does not predict pair labels (`16/55`, control `p=0.4194`) |

## Rejected As Origin Formula

The following remain documented but not promoted:

- 10x10 matrix formula searches, including the no-hard-gate ledger of
  `294528` candidates. Best coverage is only `21/55`, classified
  `lookup_disguise`.
- PRNG/seeds, Magic Web/Honeminas numbers, `1 = Tibia`, and lore-number masks.
- Short repeats and permissive residual operators that also cover controls.
- Avar Tar as 469: it is a negative control, not validation.
- ML pair-cell formula: it does not beat the simple/mechanical baselines.
- High-block blocker drawing/stroke and render-origin E-priority probes:
  both explain local patterns descriptively but fail controls.
- Eye/blink K5 and `5x2` arity models as row0 label generators: both are
  useful lore bridges but cost more than lookup and are ordinary under
  controls.
- Hierarchical provenance as row0 pair-label generator: the best feature stump
  costs more than lookup and is ordinary under inventory-preserving controls.
- Consolidated row0 origin frontier: existing matrix, rule-cover, orbit,
  tape-feature, low-rank, render, eye/blink, and provenance tests are now
  indexed together as `row0_origin_frontier_saturated_current_corpus`; this is
  a frontier statement, not a solved-origin claim.
- Row0 real-origin search: the paid-anchor, diagonal/E, grid-coordinate, and
  inventory/frequency origin families are rejected under row0-only controls;
  the external-order source is blocked, and workbook/script provenance remains
  audit-only rather than CipSoft/authorial evidence.

Primary sources:
[matrix_generator_exhaustive_report.md](../../analysis/generator_search_20260618/matrix_generator_exhaustive_report.md),
[generator_model_final_report.md](../../analysis/generator_search_20260618/generator_model_final_report.md),
[hierarchical_provenance_pair_label_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/09_hierarchical_provenance_pair_label_audit.md),
[row0_origin_frontier_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/119_row0_origin_frontier_audit.md),
[row0_real_origin_search_report.md](../../analysis/row0_real_origin_search_20260621/reports/row0_real_origin_search_report.md),
[accepted_rejected_hypotheses.json](../../analysis/generator_search_20260618/accepted_rejected_hypotheses.json),
[k5_eye_pair_model_report.md](../../analysis/eye_model_20260619/k5_eye_pair_model_report.md),
[eye_state_5x2_model_report.md](../../analysis/eye_model_20260619/eye_state_5x2_model_report.md).

## What Counts As Future Progress

Further work should not count progress by the number of new fronts or scripts.
It should count only if it improves one of these axes:

1. Matrix origin: a compact rule that predicts pair-cell labels under MDL and
   controls.
2. Assembly origin: a smaller or better-validated tape/module/literal formula.
3. External truth: CipSoft-attested number->plaintext, book->plaintext, or a
   symbol table.

Without external truth, new semantic translations, glossaries, or plaintext
claims remain inadmissible.

## Reproduction Pointers

- Main consolidated leaderboard:
  [generator_mdl_leaderboard.md](../../analysis/generator_search_20260618/generator_mdl_leaderboard.md)
- Final generator verdict:
  [generator_model_final_report.md](../../analysis/generator_search_20260618/generator_model_final_report.md)
- Self-contained tape formula:
  [tape_based_formula_469.json](../../analysis/generator_search_20260618/tape_based_formula_469.json)
- Base mechanism formula:
  [mechanical_formula_469.json](../../analysis/mechanism_model_20260618/mechanical_formula_469.json)
- Literal-reference follow-up:
  [literal_reference_formula_469.json](../../analysis/authorial_mechanism_20260620/literal_reference_formula_469.json)
- Hierarchical reference follow-up:
  [hierarchical_reference_formula_469.json](../../analysis/authorial_mechanism_20260620/hierarchical_reference_formula_469.json)
- Sequential LZ book formula:
  [sequential_lz_book_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_book_formula_469.json)
- Sequential LZ literal-run cost formula:
  [sequential_lz_run_literal_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_run_literal_formula_469.json)
- Sequential LZ dynamic-parse formula:
  [sequential_lz_dp_parse_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_dp_parse_formula_469.json)
- Sequential LZ Rice-length formula:
  [sequential_lz_rice_length_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_rice_length_formula_469.json)
- Sequential LZ Rice literal-length formula:
  [sequential_lz_rice_literal_length_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_rice_literal_length_formula_469.json)
- Sequential LZ literal-payload formula:
  [sequential_lz_literal_payload_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_literal_payload_formula_469.json)
- Sequential LZ literal-to-copy repair formula:
  [sequential_lz_literal_copy_repair_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_literal_copy_repair_formula_469.json)
- Sequential LZ book-length ledger formula:
  [sequential_lz_length_ledger_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_length_ledger_formula_469.json)
- Sequential LZ digit-address formula:
  [sequential_lz_digit_address_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_formula_469.json)
- Sequential LZ digit-address literal-repair formula:
  [sequential_lz_digit_address_literal_repair_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_literal_repair_formula_469.json)
- Sequential LZ forced-length literal-context formula:
  [sequential_lz_digit_address_forced_length_literal_context_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_forced_length_literal_context_formula_469.json)
- Sequential LZ forced-length literal-context-order formula:
  [sequential_lz_digit_address_forced_length_literal_context_order_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_forced_length_literal_context_order_formula_469.json)
- Sequential LZ forced-length literal-context-order plus type-context formula:
  [sequential_lz_digit_address_forced_length_literal_context_order_type_context_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_forced_length_literal_context_order_type_context_formula_469.json)
- Sequential LZ contextual copy-to-literal repair formula:
  [sequential_lz_digit_address_contextual_copy_to_literal_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_contextual_copy_to_literal_formula_469.json)
- Sequential LZ bounded copy-length formula:
  [sequential_lz_digit_address_contextual_bounded_copy_length_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_copy_length_formula_469.json)
- Sequential LZ min_len-bounded address formula:
  [sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_formula_469.json)
- Sequential LZ minaddr local-repair formula:
  [sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair_formula_469.json)
- Sequential LZ post-minaddr local-repair formula:
  [sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_formula_469.json](../../analysis/authorial_mechanism_20260620/sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_formula_469.json)
- DP LZ copy graph:
  [dp_lz_copy_graph_edges.csv](../../analysis/authorial_mechanism_20260620/tables/dp_lz_copy_graph_edges.csv)
- DP LZ literal seed atlas:
  [dp_lz_literal_seed_atlas.md](../../analysis/authorial_mechanism_20260620/tables/dp_lz_literal_seed_atlas.md)

Translation delta: `NONE`.
