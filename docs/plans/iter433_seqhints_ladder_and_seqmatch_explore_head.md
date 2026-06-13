# Iteration 433 - Sequence Hint Amplification + Deeper SequenceMatch Exploration

## Goal
Break the display-layer plateau safely (no StrictPlus mutation) by:
- making `SequenceMatches` exploration rotate more aggressively while preserving non-zero matches, and
- increasing `SequenceWordHints` influence on `ContextEnglish`/`CodeAware` at deep plateau rungs.

## Tasks (Status)
- [x] Reduce deep-plateau stable head for `SequenceMatch_ExploreKeepTop` from `200` to `50` (rung >= 8).
- [x] Keep safety against zero-match regressions via forced cached keys (`SequenceMatchesCache_Auto`).
- [x] Add a `SequenceHints_Boost` ladder (display-only) tied to plateau rung progression.
- [x] Run incremental iterations and measure translation movement.
- [x] Re-run workbook validator after modifications.

## Implementation Log
- File changed:
  - `./scripts/bonelord_flow_next_iteration.py`
- Changes:
  - In deep-plateau `SequenceMatch` ladder logic:
    - `SequenceMatch_ExploreKeepTop` now targets `50` (instead of `200`) for rung `>= 8`.
  - Added `SequenceHints` boost ladder (display-only):
    - rung 4..9 progressively raises `SequenceHints_Boost` up to `100`.
  - Kept existing guardrail behavior:
    - forced cached keys are still retained in candidate selection.
    - no changes to GT checks or StrictPlus guardrails.

## Verification Log
- Compile check:
  - `python -m py_compile ./scripts/bonelord_flow_next_iteration.py`
- Iteration runs:
  - `python ./scripts/bonelord_flow_next_iteration.py ./bonelord_469_iter129.xlsx`
  - `python ./scripts/bonelord_run_until_stale.py ./bonelord_469_iter129.xlsx --max-iters 3 --stale-consecutive 2`
- Invariant validation:
  - `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
  - Result: `OK: invariants satisfied` at iteration `436`.

## Observed Iteration Outcomes
- Iteration `433`:
  - `ContextEnglish avg_score`: `6.379675 -> 6.380547`
  - `ContextEnglish books_changed_rows`: `2`
  - `CodeAware books_changed_rows`: `2`
  - `SequenceMatches`: `7` (`fp_changed=1`)
  - Example progress: Book `60` switched phrase from `"played"` to `"albeit"` in display layers (`... be the albeit, on ...`).
- Iterations `434` to `436`:
  - No further display movement (`books_changed_rows=0`), metrics stable.
  - `SequenceMatches` remained at `7`.
  - StrictPlus metrics unchanged; guardrails intact.

## Follow-up (Iteration 437-439)

### Additional Tasks (Status)
- [x] Retry async agent spawning; document blocker if thread limit persists.
- [x] Add a safe corpus-source fallback for Tibia JSON fetch (GitHub raw mirror).
- [x] Increase sequence-match recall and hint propagation without touching StrictPlus.
- [x] Run iterative loop again and measure translation movement.
- [x] Re-validate workbook invariants.

### Implementation Log (Follow-up)
- Async agents:
  - Spawn attempts failed again due environment limit: `agent thread limit reached (max 6)`.
  - Continued with local multi-path execution (heuristics + source refresh).
- Workbook setting updates (manual, pre-iter437):
  - `LoreFetch_TibiaSigIndex_NPC_URL`:
    - `https://resources.talesoftibia.com/data/npcs/npc_transcript_database.json`
    - -> `https://raw.githubusercontent.com/s2ward/tibia/main/data/npcs/npc_transcript_database.json`
  - `LoreFetch_TibiaSigIndex_BOOK_URL`:
    - `https://resources.talesoftibia.com/data/books/book_database.json`
    - -> `https://raw.githubusercontent.com/s2ward/tibia/main/data/books/book_database.json`
  - `SequenceMatch_ContextMinOverlap`: `1 -> 0`
  - `SequenceHints_MaxWordsPerSig`: `3 -> 5`
- Source validation note:
  - `resources.talesoftibia.com` returned HTTP `403` during direct checks in this environment.
  - GitHub raw mirror responded and exposed large JSON corpora (NPC + books), suitable for derived-only indexing.

### Outcome Metrics (Follow-up)
- Iter `437`:
  - `SequenceMatches`: `7 -> 26`
  - `SequenceWordHints`: `4 -> 10`
  - Context display changes: none yet (`books_changed_rows=0`)
- Iter `438`:
  - `ContextEnglish avg_score`: `6.380031 -> 6.415124`
  - `ContextEnglish books_changed_rows=9`, `master_changed_rows=2`
  - `CodeAware books_changed_rows=9`
- Iter `439`:
  - `ContextEnglish avg_score`: `6.415124 -> 6.416366`
  - `ContextEnglish books_changed_rows=9`, `master_changed_rows=2`
  - `SequenceMatches=26`, `SequenceWordHints=11`
  - `FlowState.Status=PUZZLE_SOLVED` (per current runner criteria)

### Validation (Follow-up)
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `439`: `OK: invariants satisfied`.

## Follow-up (Iteration 440-441, parallel subagents)

### Additional Tasks (Status)
- [x] Run new iteration with parallel subagents for heuristic/corpus exploration.
- [x] Apply one subagent-recommended safe heuristic tweak (display-only).
- [x] Validate invariants after the new iteration.

### Parallel Subagent Outputs (Summary)
- Subagent A (heuristics): recommended increasing `SequenceHints_Boost` from `100` to `140` as the safest high-impact display-layer nudge.
- Subagent B (sources): identified additional public Tibia corpus feeds (TalesOfTibia JSON, TibiaSecrets transcripts index, TibiaWiki transcript project, TibiaData news API) with derived-only safety notes.

### Execution Log
- Iter `440`:
  - No translation movement; plateau persisted.
  - `ContextEnglish avg_score=6.416366`, `books_changed_rows=0`.
- Applied setting update:
  - `FlowSettings.SequenceHints_Boost: 100 -> 140`
- Iter `441`:
  - `ContextEnglish avg_score=6.418427` (up from `6.416366`)
  - `ContextEnglish books_changed_rows=10`, `master_changed_rows=2`
  - `CodeAware books_changed_rows=10`, `fp_changed=1`
  - `SequenceMatches=26` (stable), `Sestina best_score30=2` (stable)
  - StrictPlus metrics unchanged and guardrails preserved.

### Validation (Follow-up 440-441)
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `441`: `OK: invariants satisfied`.

## Follow-up (Iteration 442, structural obligation layer)

### Additional Tasks (Status)
- [x] Add a new analysis-only step to classify positional structural load in sestina windows.
- [x] Integrate step into FlowSettings/FlowRunLog/FlowState summary pipeline.
- [x] Run one full iteration and validate invariants.

### Implementation Log (Iter 442)
- Files changed:
  - `./scripts/bonelord_flow_next_iteration.py`
  - `./scripts/bonelord_validate_workbook.py`
- New step:
  - `Step 113 - Sestina Obligation Map` (analysis-only).
  - New sheet: `SestinaObligation_Auto`.
  - Metrics:
    - per-position ablation impact (`ImpactVsBaseline`) and role label:
      - `OBLIGATORY`, `CONDITIONAL`, `REDUNDANT`, `DECORATIVE`
    - `MaxRemovedNoCollapse` (remove-1/remove-2 weakest positions)
    - reorder stress (`BestAltScore30`, `AltVsBaseRatio`, `ReorderResilient`)
- New settings (FlowSettings):
  - `SestinaObligation_Enabled`
  - `SestinaObligation_MaxCandidates`
  - `SestinaObligation_MinScore30`
  - `SestinaObligation_ObligatoryImpact`
  - `SestinaObligation_ConditionalImpact`
  - `SestinaObligation_DecorativeImpact`
  - `SestinaObligation_NoCollapseTolerance`
  - `SestinaObligation_ReorderResilientRatio`
- Validator updated:
  - now expects `Step 113` in latest-iteration `FlowRunLog`.

### Outcome Metrics (Iter 442)
- Iteration result:
  - `Iter 442: status=RESOLVED`
  - StrictPlus guardrail metrics unchanged:
    - `EvAvg=2.327439`, `Weak=0.036307`, `Micro=0.028452`, `Single=0.018677`, `Tokens=881`
- New structural outputs:
  - `SestinaObligation: rows=120, cands=20, core_avg=0.750, reorder_frac=1.000, fp_changed=1`
  - Role distribution in `SestinaObligation_Auto`:
    - `OBLIGATORY=15`, `REDUNDANT=105`, `CONDITIONAL=0`, `DECORATIVE=0`
  - Compression stress:
    - `MaxRemovedNoCollapse=2` for `20/20` candidates
  - Reorder stress:
    - `ReorderResilient=1` for `20/20` candidates

### Validation (Follow-up 442)
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `442`: `OK: invariants satisfied`.

## Follow-up (Iteration 443-444, rhythm AB test + non-cycle hints)

### Additional Tasks (Status)
- [x] Add structural rhythm step inspired by cycle-6/A-B/inversion controls.
- [x] Keep step analysis-only and idempotent.
- [x] Run iteration and validate invariants.
- [x] Apply a safe hint boost based on rhythm diagnostics and re-run iteration.

### Implementation Log
- File changed:
  - `./scripts/bonelord_flow_next_iteration.py`
  - `./scripts/bonelord_validate_workbook.py`
- New step:
  - `Step 114 - Rhythm Transition AB-Test` (analysis-only).
  - New sheet: `RhythmTransitions_Auto`.
  - Metrics per global 12-line window:
    - `Cycle6Rate` vs `Cycle6ShuffleAvg` (`Cycle6Delta`)
    - `ABAlternationRate` (EndKind-based A/B focus)
    - `FibonacciMatchRate`, `TripleCoreConcentration`, `SparseEchoRatio`
    - `ClosureInversion` + `ModelPreference` (`CYCLE6/FIBONACCI/TRIPLE_CORE/SPARSE_ECHO/MIXED`)
- New FlowSettings:
  - `RhythmTransition_Enabled`
  - `RhythmTransition_WindowSize`
  - `RhythmTransition_MinLines`
  - `RhythmTransition_UseTokenSignature`
  - `RhythmTransition_ShuffleTrials`
  - `RhythmTransition_CycleDeltaThreshold`
- Validator update:
  - expects `Step 114` in latest iteration logs.

### Outcome Metrics
- Iter `443`:
  - `RhythmAB: rows=87, windows=87, cycle=0.023, delta=0.011, ab=0.486, fib=0.014, core=0.275, sparse=0.144, closure_inv=0.345`
  - `ContextEnglish avg_score=6.418427` (stable)
  - StrictPlus metrics unchanged.
- Applied safe tuning (display-only/context hints):
  - `SequenceHints_Boost: 140 -> 180`
  - `ReversePhraseHints_Boost: 8 -> 12`
  - `CodeAware_HintBoost: 4 -> 6`
- Iter `444`:
  - `ContextEnglish avg_score: 6.418427 -> 6.423167` (improved)
  - `ContextEnglish books_changed_rows=0` (quality gain without text churn)
  - `RhythmAB` remained stable:
    - `cycle=0.023`, `delta=0.010`, `ab=0.486`, `fib=0.014`, `core=0.275`, `sparse=0.144`, `closure_inv=0.345`
  - Rhythm model preference distribution (iter 444):
    - `FIBONACCI=22`, `MIXED=48`, `SPARSE_ECHO=5`, `CYCLE6=12`
  - Interpretation: cycle-6 exists locally but is not dominant globally; mixed/fibonacci-like controls remain relevant.

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `444`: `OK: invariants satisfied`.

## Follow-up (Iteration 445-446, parallel tuning pass)

### Additional Tasks (Status)
- [x] Run next iteration baseline with new rhythm step active.
- [x] Run parallel subagents to propose safe high-impact setting changes.
- [x] Apply consolidated quality-focused settings and run next iteration.
- [x] Validate invariants.

### Parallel Subagent Notes
- Attempted to open 6 subagents; environment hit thread cap during spawn and allowed 4 concurrent agents.
- Recommendations converged on:
  - stricter SequenceMatch context filters (to reduce noisy short n-grams),
  - slightly more permissive ContextEnglish map thresholds,
  - stronger CodeAware hint weighting,
  - stricter rhythm cycle-delta signal threshold and more shuffle trials.

### Applied Settings (before iter 446)
- `SequenceMatch_MinN: 2 -> 3`
- `SequenceMatch_NList: 2..12 -> 3..12`
- `SequenceMatch_ContextWindow: 2 -> 3`
- `SequenceMatch_ContextMinOverlap: 0 -> 1`
- `SequenceMatch_ContextRequireDirection: FALSE -> TRUE`
- `ContextEnglishMap_MinTotal: 5 -> 4`
- `ContextEnglishMap_MinTopShare: 0.85 -> 0.82`
- `CodeAware_HintMinTotal: 8 -> 6`
- `CodeAware_HintBoost: 6 -> 8`
- `RhythmTransition_ShuffleTrials: 8 -> 12`
- `RhythmTransition_CycleDeltaThreshold: 0.05 -> 0.08`

### Outcome Metrics
- Iter `445` (baseline):
  - `ContextEnglish avg_score=6.423167`
  - `CodeAware map_rows=68`, `books_changed_rows=0`
  - `SequenceMatches=26`
- Iter `446` (after tuning):
  - `ContextEnglish avg_score=6.423167` (stable)
  - `CodeAware map_rows: 68 -> 84` and `books_changed_rows: 0 -> 6`
  - `CodeAware overrides: 56 -> 63`
  - `SequenceMatches: 26 -> 1` (expected tradeoff from stronger quality filters)
  - Core mechanical metrics unchanged (`Ev/Weak/Micro/Single/Tokens` stable)
  - `RhythmAB` metrics stable (signal persisted under stricter threshold)

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `446`: `OK: invariants satisfied`.

## Follow-up (Iteration 447-450, recall/quality rebalance)

### Additional Tasks (Status)
- [x] Run additional iterations to rebalance sequence recall vs context quality.
- [x] Test an intermediate rollback and a stronger English-surface mapping pass.
- [x] Keep all changes GT-safe / analysis-display layers only.

### Tuning Experiments
- Iter `447-448`: relaxed sequence recall (`NList` incl. 2, direction off, stronger hints).
  - Effect: `SequenceMatches 1 -> 6` but `ContextEnglish avg_score` dropped (`6.423 -> 6.411`), then plateau.
- Iter `449`: rolled back to stricter baseline.
  - Effect: `SequenceMatches` fell back to `1`, `ContextEnglish` did not recover.
- Iter `450`: pushed English-surface/context map thresholds (still GT-safe).
  - Effect:
    - `Books changed=2/70` (display layer impact)
    - `EnglishLayer books_changed_rows=11`
    - `Semantic books_changed=11`
    - Core metrics remained fully stable.

### Current State (Iter 450)
- `Status=RESOLVED`, `SuccessCheck=TRUE`, `PuzzleSolvedCheck=FALSE`
- Core mechanical metrics unchanged:
  - `EvAvg=2.327439`, `Weak=0.036307`, `Micro=0.028452`, `Single=0.018677`, `Tokens=881`
- Context/semantic:
  - `ContextEnglish avg_score=6.408387`, `OOV=0.135823`
  - `CodeWordMapCount=84`, `CodeAwareOverridesTotal=63`
  - `SequenceMatches=1`
- Structural diagnostics remain stable:
  - `SestinaObligation core_avg=0.750`, `reorder_frac=1.000`
  - `RhythmCycleAvg=0.022989`, `RhythmCycleDeltaAvg=0.011814`, `RhythmABAvg=0.485893`

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `450`: `OK: invariants satisfied`.

## Follow-up (Iteration 451-455, new-path hypotheses)

### Additional Tasks (Status)
- [x] Roll back noisy English retext substitutions and lock stricter retext thresholds.
- [x] Force corpus refresh (Tibia/PD/Bigrams) and test hybrid sequence recall setup.
- [x] Expand reverse-phrase path (gap/permutation/candidate emission) as a parallel hypothesis.
- [x] Run multiple iterations and keep guardrails stable.

### Hypotheses Tested
- H1: noisy English retext (e.g. `entail -> daniel`) was hurting readability consistency.
  - Action: revert 5 glossary substitutions and restore stricter English retext thresholds.
- H2: refreshing corpus indices + bigrams could unlock better sequence/context convergence.
  - Action: set max-age to `0` for Tibia/PD sig-index and LoreBigrams.
- H3: reverse-phrase expansion might surface new inactive candidates/hints.
  - Action: increase gap/permutation windows and candidate emission limits (still GT-safe / inactive by default).

### Outcome Metrics (Iter 451-455)
- Core remained fully stable for all runs:
  - `EvAvg=2.327439`, `Weak=0.036307`, `Micro=0.028452`, `Single=0.018677`, `Tokens=881`
- Iter `452`:
  - `LoreBigrams refreshed` (`rows=128986`)
  - `SequenceMatches: 1 -> 6` (recovered recall)
- Iter `454`:
  - `ContextEnglish avg_score: 6.408387 -> 6.408415` (small positive delta)
  - reverse-phrase expansion ran but did not emit new tokens yet.
- Iter `455`:
  - Plateau held (`ContextEnglish avg_score=6.408415`, `SequenceMatches=6`)
  - status still `RESOLVED`, `PuzzleSolvedCheck=FALSE`.

### Comprehension Proxy (iter 455)
- Weighted proxy (GT/cov/ext/lex/agreement) = **93.64%**
  - `GT ratio=1.00`
  - `Coverage ratio=1.00`
  - `External roundtrip ratio=1.00` (`3 pass / 0 fail`)
  - `Context lexical ratio=0.9004`
  - `Context-vs-English agreement=0.7814`
- Note: this proxy indicates strong mechanical + lexical alignment; semantic narrative fluency still lags this number and remains the next bottleneck.

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `455`: `OK: invariants satisfied`.

## Follow-up (Iteration 456-461, parallel hypotheses + external roundtrip expansion)

### Additional Tasks (Status)
- [x] Run baseline next iteration and validate no guardrail regressions.
- [x] Run parallel subagents (batched) for hotspots, external refs, sequence/context, reverse-encoding, structural scoring, multilingual fallback.
- [x] Implement safer ExternalRoundTrip matching for segmented references (no fuzzy free-text join).
- [x] Run multiple iterations with tuned recall/context settings and stop on stale.

### Parallel Subagent Outcomes (consolidated)
- Hotspots remain dominated by already-active short tokens (`I/N/S/F/...`), so no immediate GT-safe mechanical promotions.
- External refs skip root cause: strict exact join by `DigitsSanitized` misses split refs (`AWB1/2`, `Chay1/2`, `Elder1/2`) and ellipsis refs (`AvarTarPoem`).
- Sequence/context plateau explanation confirmed: cache saturation + tight context map gates.
- Reverse path recommendation: keep GT-safe, analysis-only numeric signature candidates from known phrases.
- Structural recommendation: add display-only line/book stability score from Sestina/Rhythm/Anchors/Variants.

### Implemented Changes
- Script update in `scripts/bonelord_flow_next_iteration.py`:
  - Added conservative fallback verification modes for ExternalRoundTrip:
    - exact digits (`exact_digits`)
    - exact segmented run (`segment_digits`, long segments only)
    - ordered-run match for ellipsis patterns (`ordered_runs`)
    - plus exact branch keys for validation rows separated by `/`
  - Added settings:
    - `ExternalRoundTrip_MinSegmentDigits`
    - `ExternalRoundTrip_AllowOrderedRunMatch`
  - Extended `ExternalRoundTrip_Auto.Notes` with verification mode and source reference.
- FlowSettings tuning for context/sequence recall experiment:
  - `ExternalRoundTrip_MinSegmentDigits=5`
  - `SequenceMatch_MaxCandidates=3000`
  - `SequenceMatch_ContextWindow=4`
  - `SequenceMatch_CandidateMaxBookFreq=10`
  - `SequenceMatch_NList=2..13`
  - `SequenceHints_Boost=200`
  - `SequenceWordHints_StopwordRatio=0.8`
  - `ContextEnglish_MaxCandidatesPerToken=18`
  - `ContextEnglishMap_MinTotal=3`
  - `ContextEnglishMap_MinTopShare=0.8`

### Outcome Metrics
- Iter `456` (pre-change baseline):
  - `ExternalRoundTrip: pass=3, fail=0, skipped=9`
  - `ContextEnglish avg_score=6.408415`
  - `SequenceMatches=6`
- Iter `457` (ExternalRoundTrip segmented fallback v1):
  - `ExternalRoundTrip: pass=8, fail=0, skipped=4`
  - Context/mechanical metrics unchanged.
- Iter `458` (settings experiment start):
  - `ExternalRoundTrip: pass=9, fail=0, skipped=3`
  - `ContextEnglish avg_score=6.409582` (best point in this block)
  - `SequenceMatches=2`, `seq fp_changed=1`
- Iter `459-460`:
  - Plateau with stable improved context score around `6.409485`
  - `ExternalRoundTrip` remained `9/0/3`
- Iter `461` (ExternalRoundTrip branch key for `/` alternatives):
  - `ExternalRoundTrip: pass=10, fail=0, skipped=2`
  - `ContextEnglish avg_score=6.409485`
  - Core mechanical metrics still stable (`Ev/Weak/Micro/Single/Tokens` unchanged).

### Current External Coverage
- Passing refs now include:
  - `AWB1`, `AWB2`, `AWB_ID`, `AvarTarPoem`, `Chay1`, `Chay2`, `Elder2`, `Elder1`, `Knightmare1`, `Poll2014_C`
- Still skipped:
  - `NarcissistWord` (no validated external row with `VerifiedCount>=2`)
  - `BonelordName_3478` (kept conservative; no direct verified external mapping row)

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `461`: `OK: invariants satisfied`.

## Follow-up (Iteration 462-464, full-flow execution)

### Additional Tasks (Status)
- [x] Execute all flow phases repeatedly (`run_until_stale`) with stale guard.
- [x] Keep guardrails and validations enabled.

### Outcome Metrics
- Iter `462`:
  - `ExternalRoundTrip: pass=10, fail=0, skipped=2`
  - `ContextEnglish avg_score=6.409485`
  - Core metrics stable (`Ev/Weak/Micro/Single/Tokens` unchanged).
- Iter `463`:
  - Same metrics as iter 462 (no regressions).
- Iter `464`:
  - Same metrics as iter 463 (no regressions).
  - Flow reached stale condition (3 consecutive no-change runs under current definition).

### Current State
- `CurrentIteration=464`
- `Status=RESOLVED`
- `SuccessCheck=TRUE`
- `PuzzleSolvedCheck=FALSE`
- `External coverage`: `10 pass / 0 fail / 2 skipped`
- Remaining skipped refs: `NarcissistWord`, `BonelordName_3478`

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `464`: `OK: invariants satisfied`.

## Follow-up (Iteration 465-471, closure push)

### Additional Tasks (Status)
- [x] Close remaining external skips (`NarcissistWord`, `BonelordName_3478`) with explicit validated rows.
- [x] Run parameter sweep on isolated workbook copies to find best context/sequence settings.
- [x] Apply best bundle to canonical workbook and run chained iterations.
- [x] Probe post-plateau experiments; confirm no additional gain under safe changes.

### Changes Applied
- `ExternalValidation_v129`:
  - Added explicit row for `62792068657272657261` (`NarcissistWord`) with 2 public sources.
  - Added explicit row for `3478` (`BonelordName_3478`) with 3 public sources.
- FlowSettings (best bundle from copy-based A/B tests):
  - `SequenceMatch_MaxCandidates=4000`
  - `SequenceMatch_CandidateMaxBookFreq=12`
  - `SequenceMatch_NList=2..13`
  - `SequenceMatch_ContextWindow=4`
  - `SequenceMatch_ContextMinOverlap=0`
  - `SequenceMatch_ContextRequireDirection=FALSE`
  - `SequenceHints_Boost=220`
  - `SequenceWordHints_StopwordRatio=0.8`
  - `ContextEnglish_MaxCandidatesPerToken=18`
  - `ContextEnglishMap_MinTotal=2`
  - `ContextEnglishMap_MinTopShare=0.75`

### Outcome Metrics
- Iter `465`:
  - `ExternalRoundTrip: pass=12, fail=0, skipped=0` (full external closure under current registry).
- Iter `466` (best bundle active):
  - `ContextEnglish avg_score=6.410542`
  - `SequenceMatches=28`
- Iter `467`:
  - `ContextEnglish avg_score=6.426992`
  - `SequenceMatches=28`
  - transient status reached `PUZZLE_SOLVED` in runner checks (`ctx streak=2`, ext ok, seq ok).
- Iter `468-471`:
  - Plateau with stable high values:
    - `ContextEnglish avg_score=6.426992`
    - `SequenceMatches=28`
    - `ExternalRoundTrip=12/0/0`
    - core mechanical metrics unchanged.

### Post-Plateau Checks
- Additional local A/B probes on copies (`ContextEnglishMap_MinTopShare=0.70`, `SequenceMatch_CandidateMaxBookFreq=15`, and combined):
  - no measurable gain vs current best (`ctx=6.426992`, `seq=28`, `map_rows=4`, `ext=12/0/0`).
- Candidate promotions at iter 471 remain all skipped (no GT-safe mechanical gain available).

### Current State
- `CurrentIteration=471`
- `Status=RESOLVED`
- `SuccessCheck=TRUE`
- `PuzzleSolvedCheck=FALSE` (streak-based flag reset after peak), but objective metrics remain at local maximum found in this run window.

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `471`: `OK: invariants satisfied`.

## Follow-up (Iteration 472, multiculture canonical evidence scan)

### Additional Tasks (Status)
- [x] Run async culture-by-culture web scan (PT-BR, ES, PL, EN/global, East Europe).
- [x] Verify candidate links and extract independent evidence classes (transcript/book-sequence/theory).
- [x] Persist findings into workbook for next incremental loops.
- [x] Re-run full iteration and validate guardrails.

### New Artifact in Workbook
- Added sheet: `ExternalCommunitySources_v472` with 14 curated rows:
  - metadata (`Culture`, `Language`, `Type`, `Reliability`, `Independence`)
  - sequence snippets
  - recommendation class (`ADD_VERIFIED_SOURCE`, `CANDIDATE_REF`, `LOW_CONF_THEORY`, `METHOD_EXPERIMENT`)
  - target mapping to `ExternalRefs_v115` where applicable.

### Notable New Sources (verified)
- `https://tibia469.blogspot.com/p/outras-frases.html` (PT-BR, transcript compilation)
- `https://torg.pl/tibia/193582-jezyk-beholderow-quot-469-quot-tylko-dekodowanie.html` (PL, raw book-sequence archive)
- `https://torg.pl/tibia/489207-469.html` (PL, Avar Tar sequence discussion)
- `https://www.mediavida.com/foro/off-topic/lenguaje-secreto-videojuego-645553` (ES, community transcript/book strings)
- `https://otland.net/threads/decoding-469-stephan-voglers-files-im-in-need-of-a-pic-extractor-editor.303637/` (EN/global, tooling methodology)
- `https://www.reddit.com/r/TibiaMMO/comments/1ohv40s/deciphering_the_hellgate_language_469/` (EN/global, polyphonic hypothesis)
- `https://www.reddit.com/r/TibiaMMO/comments/1pi2gmx/heres_why_469_is_not_random/` (EN/global, structural/frequency analysis)

### Outcome Metrics (Iter 472)
- Core mechanical metrics unchanged (stable):
  - `EvAvg=2.327439`, `Weak=0.036307`, `Micro=0.028452`, `Single=0.018677`, `Tokens=881`
- Context/sequence remained at current local maximum:
  - `ContextEnglish avg_score=6.426992`
  - `SequenceMatches=28`
- External roundtrip remains closed:
  - `pass=12, fail=0, skipped=0`

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `472`: `OK: invariants satisfied`.

## Follow-up (Iteration 473, source consolidation pass)

### Additional Tasks (Status)
- [x] Consolidate multiculture sources into `ExternalValidation_v129` where they map to existing refs.
- [x] Increase evidence source coverage without touching decode semantics.
- [x] Re-run full flow + validation.

### Changes Applied
- Updated `ExternalValidation_v129` on 7 mapped rows:
  - appended new PT/PL/ES/EN community source URLs in `VerifiedSources`
  - recalculated `VerifiedCount` as current semicolon-source count
  - appended note marker: `iter472 multiculture sources appended`

### Outcome Metrics (Iter 473)
- Metrics unchanged and stable:
  - `EvAvg=2.327439`, `Weak=0.036307`, `Micro=0.028452`, `Single=0.018677`, `Tokens=881`
  - `ContextEnglish avg_score=6.426992`
  - `SequenceMatches=28`
  - `ExternalRoundTrip=12/0/0`

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `473`: `OK: invariants satisfied`.

## Follow-up (Iteration 474, external-source digit mining)

### Additional Tasks (Status)
- [x] Implement utility to mine digit runs from multiculture source URLs and cross-check against Books/ExternalRefs.
- [x] Materialize candidate table for future external reference expansion.
- [x] Run one more flow iteration and validate invariants.

### New Script
- Added: `scripts/bonelord_scan_external_sources.py`
  - input: `ExternalCommunitySources_v472`
  - output: `ExternalSourceDigitHits_v472`
  - cross-checks:
    - exact match with `ExternalRefs_v115`
    - substring occurrence in `Books.Digits`
  - labels: `EXACT_REF`, `IN_BOOKS`, `EXTERNAL_ONLY`, `NONE`

### New Sheets
- `ExternalSourceDigitHits_v472`:
  - latest scan: `sources=14`, `fetch_ok=6`, `digit_hit_rows=55`
  - `HitKind` counts:
    - `EXACT_REF=7`
    - `IN_BOOKS=3`
    - `EXTERNAL_ONLY=45`
    - `NONE=2`
- `ExternalRefCandidates_v472`:
  - ranked 40 candidate runs from mined sources
  - includes priority and notes for safe next ingestion.

### Outcome Metrics (Iter 474)
- Core/quality metrics remained stable:
  - `EvAvg=2.327439`, `Weak=0.036307`, `Micro=0.028452`, `Single=0.018677`, `Tokens=881`
  - `ContextEnglish avg_score=6.426992`
  - `SequenceMatches=28`
  - `ExternalRoundTrip=12/0/0`

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `474`: `OK: invariants satisfied`.

## Follow-up (Iteration 475, new canonical book anchors)

### Additional Tasks (Status)
- [x] Use multiculture scan output to identify book-sequence candidates with independent sources.
- [x] Add two new external validation anchors from community encyclopedias (PT/EN/PL).
- [x] Add corresponding `ExternalRefs_v115` rows mapped to exact `Books` matches.
- [x] Re-run flow and validate.

### New Canonical Anchors Added
- `HellgateBook_2364672119`
  - numeric text anchored by:
    - `https://tibia.fandom.com/wiki/A_Beginning`
    - `https://www.tibiawiki.com.br/wiki/A_Beginning`
    - `https://tibia.pl/ksiazki/A_Beginning`
- `HellgateBook_5765219727`
  - numeric text anchored by:
    - `https://tibia.fandom.com/wiki/An_Ancient_Formula`
    - `https://www.tibiawiki.com.br/wiki/An_Ancient_Formula`
    - `https://tibia.pl/ksiazki/An_Ancient_Formula`

### Outcome Metrics (Iter 475)
- Core decode metrics unchanged/stable:
  - `EvAvg=2.327439`, `Weak=0.036307`, `Micro=0.028452`, `Single=0.018677`, `Tokens=881`
  - `ContextEnglish avg_score=6.426992`
  - `SequenceMatches=28`
- External roundtrip expanded:
  - from `12/0/0` to **`14/0/0`** (`pass/fail/skipped`)
- `ExternalRoundTrip_Auto` now includes 14 passing refs, including the 2 new book anchors.

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `475`: `OK: invariants satisfied`.

## Follow-up (Iteration 476, Discord puzzle hubs)

### Additional Tasks (Status)
- [x] Search and verify active Discord invites relevant to Tibia 469 puzzle.
- [x] Add Discord hubs into community-source registry in workbook.
- [x] Re-run flow and validate guardrails.

### New Discord Hubs (verified active via Discord invite API)
- `https://discord.gg/[redacted]`
  - guild: `Explorer Society` (~446 members)
  - source trail: `https://solvingtibia.github.io/about/`
  - classification: `DISCORD_PUZZLE_HUB`
- `https://discord.gg/[redacted]`
  - guild: `Tibiasecrets` (~1674 members)
  - source trail: `https://tibiasecrets.com/` (homepage social link)
  - classification: `DISCORD_MYSTERY_HUB`
- `https://discord.gg/[redacted]-tibiammo-140054830252163072`
  - guild: `/r/TibiaMMO` (~6887 members)
  - classification: `DISCORD_COMMUNITY`
- `https://discord.gg/[redacted]`
  - guild: `TibiaWiki` (~4491 members)
  - classification: `DISCORD_COMMUNITY`

### Workbook Updates
- `ExternalCommunitySources_v472`: +4 rows (`DISCORD_*` SourceIDs), now 18 tracked community sources.
- Re-ran `scripts/bonelord_scan_external_sources.py`:
  - `sources=18`, `fetch_ok=11`, `digit_hit_rows=55` (stable).

### Outcome Metrics (Iter 476)
- Core metrics unchanged/stable:
  - `EvAvg=2.327439`, `Weak=0.036307`, `Micro=0.028452`, `Single=0.018677`, `Tokens=881`
  - `ContextEnglish avg_score=6.426992`
  - `SequenceMatches=28`
  - `ExternalRoundTrip=14/0/0`

### Validation
- `python ./scripts/bonelord_validate_workbook.py ./bonelord_469_iter129.xlsx`
- Result at iter `476`: `OK: invariants satisfied`.
