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
| Prequential and row0 origin audit | freezes `8558.667` as `compression_bound`; learned components beat uniform on all prefix future-suffix splits, but random same-size train controls are usually stronger, and row0 origin remains exogenous across manual/permutation/grid/order/external/workbook hypotheses | predictive component evidence / row0 still exogenous |
| Recipe externality audit | only `4285.876/8558.667` bits are prequentially scored learned components; `4272.791` bits remain fixed recipe or non-learned ledger | component validation only / full recipe discovery not proved |
| Prequential recipe reparse audit | with frozen train-prefix component counts, a deterministic LZ parser roundtrips every future suffix and beats the active full-corpus recipe under the same frozen counts on all five cutoffs | predictive recipe evidence / split-specific analysis only |
| Prequential recipe reparse controls | at cutoffs `20/35/50`, real suffixes beat random same-length, per-book-shuffled, and suffix-pool-shuffled controls; controls have negative gain versus raw digits | controlled predictive recipe evidence |
| Prequential recipe train-set controls | at focused cutoff `50`, numeric prefix beats the random train-set mean but not all random inventories (`p=0.1538`) | predictive recipe evidence / numeric order not promoted |
| Online deterministic reparse formula | deterministic parser using only prior committed book counts becomes a full-corpus formula; validates `70/70` and lowers the bound from `8558.667` to `8343.062` | strongest copy/reference upper bound |
| Online reparse order control | numeric order remains best against reverse, parity, length-derived, and 6 seeded random orders; best random raw order is `+188.584` bits worse before order cost | canonical order support / no new bound |
| Online formula recipe prune | book `length` and copy `target_start` are derivable; stripped projection preserves `8343.062` bits and `70/70`, saving `5612` recipe JSON bytes | representation simplification / no new bound |
| Canonical online recipe formula | materializes the pruned formula without book `length` or copy `target_start`; preserves `8343.062` bits and `70/70` | former compact bound representation |
| Literal-length-derived recipe formula | literal op `length` is derived from literal `text`; removes 87 more redundant fields and preserves `8343.062` bits and `70/70` | tighter recipe representation |
| Op-type-derived recipe formula | op `type` is derived from field shape; removes 348 more redundant fields and preserves `8343.062` bits and `70/70` | remaining op dependencies: literal text, copy source, copy length |
| Copy source canonicality audit | all 261 copy sources are the earliest legal occurrence of the copied chunk at declared length; only 123 are unique | canonical encoder rule / source still required for decoding |
| Copy source canonicality controls | earliest occurrence remains `261/261`; latest occurrence is `123/261`, previous-source-plus-length is `5/261`, and random candidate choice expects `169.473` hits | source tie-break support / no decoder removal |
| Copy length default/exception formula | target-max extension is high-coverage but encoder-only; decodable `decoder_max_possible` default plus adaptive exceptions lowers copy-length cost and promotes the bound to `8206.178` bits | copy length remodeled / row0 unchanged |
| Copy source default/exception formula | previous-source-plus-length default is decodable but sparse; adaptive exception-source coding lowers copy-address cost and promotes the bound to `8177.317` bits | copy source remodeled / row0 unchanged |
| Default/exception prequential validation | after train-count freezing fix, prefix online and frozen gains are all positive (`min frozen aggregate=50.303` bits), but family holdouts include failures | prefix-frozen partial / final method not promoted |
| Default/exception component profile | `8177.317` remains compression bound and prefix-frozen profile; family/bookcase failures keep the generation claim partial | separated ledgers |
| Current literal-payload profile audit | old order-1 profile does not transfer; order-1 is `+95.968` full-corpus and `+28.609` aggregate frozen-prefix bits worse | order-2 retained |
| Copy source distance model audit | backward-distance source coding is decodable but the replacement is `+25.551` bits worse than active absolute-source default/exception | distance rejected |
| Current active prequential profile audit | active learned streams cover `7157.317/8177.317` bits and beat uniform on all tested prefix, block, and public-bookcase family holdouts; random same-size train controls are usually stronger than numeric prefixes | component validation strengthened / recipe discovery not proved |
| Active reparse state-boundary audit | active copy-source default is path-dependent on previous copy source/length; exact reparse needs expanded state and reaches a cutoff-10 state proxy of `302879952` | recipe-discovery blocker localized |
| Copy source state-free default audit | decoder-computable source defaults that avoid previous-copy state are all worse; the best `state_free_back_current_length` rule is `+15.186` bits worse and worse in every prefix frozen split | state-free source simplification rejected |
| Copy length midpoint context audit | midpoint `book_id < 35` beats global by `13.839` bits, is rank `2/69` among one-cut boundaries, beats global in every prefix frozen split, and passes book-id permutation controls (`p=0.0033`) | midpoint context supported / no new bound |
| Literal copy availability boundary audit | `73/87` literal starts have no legal `min_len` copy candidate and `760/857` literal digits are forced at digit level; residual parser choice is localized to `14` literal starts / `97` digit positions | literal externality reduced / no new bound |
| Optional literal copy repair frontier | `74` single in-literal copy-prefix repairs across `5` eligible optional starts are scored under the active ledger; best candidate is still `+1.180` bits worse | simplest optional-literal repair rejected |
| Literal payload default/exception audit | modal-default/exception literal digit coding is decodable but worse than the active categorical previous-emitted-digit order-2 model | rejected fallback / no new bound |
| Literal payload structural context audit | literal-run offset, run-length bucket, book half/parity, and bounded combinations with `prev2` all over-split the payload stream | rejected context / no new bound |
| Prequential and row0 origin audit | frozen validation scope `8558.667` shows partial learned-component prediction, but family failures and recipe externality keep it from being a full generation method; row0 remains exogenous | analysis-only boundary / no generation promotion |
| Row0 origin frontier audit | matrix/rule/orbit/tape-feature/low-rank/render/eye/provenance tests are indexed together; no family yields a charged, controlled, holdout-capable pair-label formula | current-corpus frontier saturated / row0 origin still open |
| Row0 next-frontier audit | lookup baseline is `160.521` bits; 13 worksheet anchors reduce nominal residual lookup to `106.343` bits before anchor/source costs, while ordered-surface facts (`39` absent, `19/91` conflict, `54/55` purity) promote only a mechanical clue | no origin formula / primary source or paid anchor reduction required |
| Tape MDL gain | Rough total gain `6597.1` bits over literal module table | accepted compression evidence |
| Residual exact repeats | MDL-pruned `exact_repeat` covers `1683/2083` residual digits; about `400` digits remain literal | accepted secondary mechanical layer |
| Chayenne holdout | minLen=8 coverage `45/49`; Avar Tar minLen=8 coverage `0/115` | secondary validation only |
| Zero omission | local previous/next context and geometry predict omission better than code-only | supporting render layer |

Primary sources:
[tape_based_formula_report.md](../../analysis/generator_search_20260618/tape_based_formula_report.md),
[literal_reference_benchmark_controls.md](../../analysis/authorial_mechanism_20260620/reports/test_results/06_literal_reference_benchmark_controls.md),
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
[prequential_and_row0_origin_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/125_prequential_and_row0_origin_audit.md),
[prequential_and_row0_origin_audit_20260621.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/prequential_and_row0_origin_audit.md),
[recipe_externality_audit.md](../../analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/04_recipe_externality_audit.md),
[row0_origin_parallel_report.md](../../analysis/row0_origin_parallel_20260621/reports/final_row0_origin_parallel_report.md),
[row0_next_frontier_report.md](../../analysis/row0_origin_parallel_20260621/reports/row0_next_frontier_report.md),
[prequential_recipe_reparse_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/126_prequential_recipe_reparse_audit.md),
[prequential_recipe_reparse_controls.md](../../analysis/authorial_mechanism_20260620/reports/test_results/127_prequential_recipe_reparse_controls.md),
[prequential_recipe_reparse_trainset_controls.md](../../analysis/authorial_mechanism_20260620/reports/test_results/128_prequential_recipe_reparse_trainset_controls.md),
[online_deterministic_reparse_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/129_online_deterministic_reparse_compile.md),
[online_reparse_order_control_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/130_online_reparse_order_control_audit.md),
[online_formula_recipe_prune_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/131_online_formula_recipe_prune_audit.md),
[canonical_online_recipe_formula_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/132_canonical_online_recipe_formula_compile.md),
[literal_length_derived_recipe_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/133_literal_length_derived_recipe_compile.md),
[op_type_derived_recipe_compile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/134_op_type_derived_recipe_compile.md),
[copy_source_canonicality_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/135_copy_source_canonicality_audit.md),
[online_copy_source_canonicality_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/140_online_copy_source_canonicality_audit.md),
[copy_length_default_decodability_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/136_copy_length_default_decodability_audit.md),
[copy_source_default_decodability_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/137_copy_source_default_decodability_audit.md),
[default_exception_prequential_validation.md](../../analysis/authorial_mechanism_20260620/reports/test_results/141_default_exception_prequential_validation.md),
[default_exception_component_profile.md](../../analysis/authorial_mechanism_20260620/reports/test_results/142_default_exception_component_profile.md),
[current_literal_payload_profile_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/143_current_literal_payload_profile_audit.md),
[copy_source_distance_model_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/144_copy_source_distance_model_audit.md),
[current_active_prequential_profile_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/145_current_active_prequential_profile_audit.md),
[active_reparse_state_boundary_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/146_active_reparse_state_boundary_audit.md),
[copy_source_state_free_default_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/147_copy_source_state_free_default_audit.md),
[copy_length_midpoint_context_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/148_copy_length_midpoint_context_audit.md),
[literal_copy_availability_boundary_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/149_literal_copy_availability_boundary_audit.md),
[optional_literal_copy_repair_frontier.md](../../analysis/authorial_mechanism_20260620/reports/test_results/150_optional_literal_copy_repair_frontier.md),
[literal_payload_default_decodability_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/138_literal_payload_default_decodability_audit.md),
[literal_payload_structural_context_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/139_literal_payload_structural_context_audit.md),
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

Primary sources:
[matrix_generator_exhaustive_report.md](../../analysis/generator_search_20260618/matrix_generator_exhaustive_report.md),
[generator_model_final_report.md](../../analysis/generator_search_20260618/generator_model_final_report.md),
[hierarchical_provenance_pair_label_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/09_hierarchical_provenance_pair_label_audit.md),
[row0_origin_frontier_audit.md](../../analysis/authorial_mechanism_20260620/reports/test_results/119_row0_origin_frontier_audit.md),
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
