# Inspiration Model Leaderboard

Generated: 2026-06-20  
Translation delta: `NONE`

| Rank | Hypothesis / test | Test type | Classification | Evidence | Stop rule outcome |
|---:|---|---|---|---|---|
| 1 | Subjective viewer / render transform | `wrapper_existing_result` | `accepted_mechanical` | Directed surface + orientation holdout reports | Accepted only as render/orientation layer. |
| 2 | Great Calculator / assembly | `wrapper_existing_result` | `accepted_mechanical` | Tape formula: 70/70 books, 62 slices, 16 components, rough gain 6597 bits | Already accepted; no semantic movement. |
| 3 | Authorial source classifier | `manual_classifier` | `accepted_mechanical` | Deterministic routing of Chayenne, YTC, Secret Library, Honeminas, Avar Tar | Process guard accepted. |
| 4 | Boundary-safe anchor audit | `original_statistical` | `rejected_control` | `3478` has 24 per-book hits and 0 cross-book false hits; several lore anchors are absent from books | Substring presence is not a formula. |
| 5 | Aligned numeric anchor audit | `original_statistical` | `rejected_control` | `3478` hits split 12/12 across 2-digit phase; `486486`, `74032`, `45331`, `43153`, `34784` are absent | No boundary-aligned lower-cost formula. |
| 6 | Assembly path inference audit | `original_statistical` | `rejected_control` | Holdout transition accuracy 0.0000; control p_ge 1.0000 | Tape path remains reconstruction mechanics only. |
| 7 | Central-eye zero suppression | `wrapper_existing_result` | `weak_clue` | Zero context signal exists but does not become final formula under rough MDL | Keep as support only. |
| 8 | D&D central-eye formal model | `manual_classifier` | `weak_clue` | Zero/render reports present; analogy formalized but not predictive semantics | Mechanism inspiration only. |
| 9 | D&D eye-ray d10 channels | `wrapper_existing_result` | `weak_clue` | K5/5x2 eye models fail as row0 label generators | Reject as origin formula. |
| 10 | D&D fixed ray-order model | `blocked_watchlist` | `blocked_waiting_for_fixed_external_order` | No committed external fixed ray-order source | Do not fit source order from row0. |
| 11 | NPC keyword trigger model | `wrapper_existing_result` | `weak_clue` | Phrase/source classes separate from book layer | No sentence/book plaintext. |
| 12 | Quest mechanism feature matrix | `manual_classifier` | `watchlist_only` | Corpus files contain feature vocabulary but no book-level feature target | Ontology only until alignment target exists. |
| 13 | Library entity ontology | `wrapper_existing_result` | `weak_clue` | 70-book object model + Secret Library anchor | Ontology only. |
| 14 | Numeric identity seeds | `wrapper_existing_result` | `watchlist_only` | `3478`, `486486`, Honeminas, Secret Library anchors | No controlled seed improvement. |
| 15 | Numeric identity graph motif audit | `original_statistical` | `rejected_control` | Code-graph motif controls do not promote any seed into a formula | No word-code mapping. |
| 16 | Yalahar quarter blocks | `wrapper_existing_result` | `watchlist_only` | No predictive quarter metadata | No-go until fixed order target appears. |
| 17 | Dreamer duality split | `wrapper_existing_result` | `watchlist_only` | Existing source-class split already covers it | No independent prediction. |
| 18 | PoI throne order motif | `wrapper_existing_result` | `watchlist_only` | 7/14 analogy only | No controlled order model. |
| 19 | Physical library topology audit | `blocked_watchlist` | `blocked_waiting_for_physical_metadata` | No committed per-book physical topology/order manifest | Cannot infer topology from lore or ids. |
| 20 | Excalibug route | `blocked_watchlist` | `blocked_waiting_for_official_source` | Keyword-gate clue but no official GT pair | Wait for source. |
| 21 | Official source snapshot audit | `source_registry` | `source_registry` | 18/18 sources now carry text presence, officiality, interpretation risk, semantic authority | Registry hygiene only. |
| 22 | Expanded negative-control suite | `original_statistical` | `partial_negative_control_suite` | Available numeric controls tested; lore-only controls blocked without numeric source | Control overlap is not positive evidence. |
| 23 | Tridiag / Donina E-render clues | `wrapper_existing_result` | `weak_clue` | Local E/zero/render anomaly statistics only | Not a formula. |
| 24 | Paradox / Spirit Grounds / Evil Mastermind | `manual_classifier` | `rejected_control` | Negative controls and anti-dictionary guardrails | Keep as false-positive calibration. |
| 25 | Dreadeye / First Dragon | `blocked_watchlist` | `watchlist_only` | Future/alien-communication hooks only | Official-source gate. |
| 26 | Avar Tar / fan glosses / German-MHG claims | `manual_classifier` | `rejected_control` | Leaky, unsupported, or contradicted by controls | Keep as negative examples. |
| 27 | Deep Statistical Closure for Current Source-Inspiration Families | `original_statistical` | `source_family_closed_negative` | 2000-control probes for seeds, external strings, row0 models, book phases, E/render anomalies, co-occurrence | No formula or official GT. |
| 28 | Plan exhaustion audit | `completion_audit` | `source_family_closed_negative` | Current-state audit verifies artifacts, tests, lanes, H19-H24, semantic gates, and fronts | Execution complete as negative closure. |

## What Counts As Future Promotion

Only these would move the leaderboard:

1. CipSoft/in-game number-to-text, book-to-text, or symbol-to-meaning evidence.
2. A lower-cost mechanical formula that beats current tape/module/render
   baselines under controls.
3. A fixed source-family closure that removes future search space.

No item in this pass satisfies item 1 or 2. Several lanes satisfy item 3.
