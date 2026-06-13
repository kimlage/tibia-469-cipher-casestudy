---
page_id: lessons-and-process
page_type: retrospective
context: bonelord-469
visibility: public_candidate
status: closed
updated_at: 2026-06-13
moc_parent: README.md
source_refs: [AGENTS.md]
---

# 8. Lessons & Process

[← External Sources](07-external-sources.md) · [Wiki home](README.md) · Next: [Open Questions →](09-open-questions.md)

---

> The methodological story: what went wrong at the *process* level, what was done genuinely well, and the reform now in place. This page matters as much as the technical results — it is *why* a decade of effort plateaued.

## The core critique: activity over outcome

The project accumulated extraordinary machinery:

- **1,592 SQLite tables**, ~**553** Python scripts (overwhelmingly `*_probe` / `*_gate` / `*_audit`), **48,718** flow-runs, **318,276** "candidate promotions", ~96 numbered `human_qNN` research tables.
- Yet the honest scoreboard records **0 accepted human-readable book translations** (`convergence_honest_progress_rollup_v1`: `BOOK_PROSE_GLOSS = ZERO_ACCEPTED`; `goal_completion_audit_v1`: `NOT_COMPLETE`, C2 & C4 FAIL).

The failure mode was **goal-substitution**: the system optimized *activity* (run another iteration, build another probe table) instead of *outcome* (a decoded segment). A strict promotion gate prevented false positives but had **no positive exit path**, so rigor itself became a plateau — endless null iterations that *looked* like progress.

## What was done genuinely well (credit where due)

1. **Scientific integrity of the first order.** Rejecting the German "solution" with 100% mechanical coverage because it failed two ground-truth phrases ([page 7](07-external-sources.md)) is exactly the discipline that separates real decipherment from wishful pattern-matching.
2. **Institutionalized anti-overfit controls** — holdout, negative controls, shadow-vs-canonical, the rule that honestly marking `<SUSPECT>`/`<UNK>` is *progress*.
3. **Total auditability** — every claim traces to a table and a run.
4. **Honest self-diagnosis** — the project's own tables admit `ZERO_ACCEPTED` / `NOT_COMPLETE`. It did not lie to itself about results, only mis-prioritized effort.

## Two honesty corrections made during this work

Recorded transparently because the project's value rests on not fooling itself:

1. **An early data read was corrupted and discarded.** The first analysis in this engagement was built on a non-existent database path whose queries failed *silently*; it produced fabricated-looking counts ("33k segments already in English", "21k iterations"). It was thrown out entirely once the real 1 GB operational DB was opened. (Lesson now in the operating notes: verify a query returned real rows; route output to files.)
2. **The phrase "ground truth" is weaker than first stated.** The `gt_pass=1` phrases validate against the project's *own decoder output*, not against CipSoft-attested English; "be a wit than be a fool" is community analysis. The codebook is holdout-useful but not externally attested. (Full caveat on [page 4](04-phrase-codebook.md).)
3. *(also)* **The substitution-solve's anagram beat was understated, then corrected** — it is robust (z ≈ 8–15) but driven by templating + skew, not language ([page 5](05-book-layer-non-linguistic.md)).

Adversarial verification — a separate agent instructed to refute — caught corrections #2 and #3. Building the refutation step in was decisive.

## The reform: the Outcome Ledger

Added to [`AGENTS.md`](../../AGENTS.md). Progress is now measured by **outcome, not cadence.** Activity (session count, iteration number, scripts/tables created) is explicitly **not** progress. A round counts only if one of these strictly increases under an honest, reproducible check:

| Metric | Current value |
|---|---|
| `CRIBS_REPRODUCED_UNDER_HOLDOUT` | **0** books |
| `CODES_CONFIRMED_EXTERNALLY` (CipSoft-attested, not own decoder) | **0** at word level |
| `BOOKS_NO_PROSE_TO_ACCEPTED` | **0 / 70** |
| `GT_PHRASES_PASSING_EXTERNALLY` | **0** (4 pass only vs own decoder) |

Rules: no metric may rise without a cited, reproducible source; decoder self-output and fan guesses are inadmissible; a round that moves nothing is logged as **"NEGATIVE / plateau confirmed"** — a valid outcome, not a failure to paper over; structural fixes are logged separately and do not count as semantic progress.

## The meta-lesson

The puzzle's hardness was **data-starvation**, not insufficient cleverness or tooling. Once that is true, *more internal iteration cannot help* — and a process that rewards iteration will run forever producing nulls dressed as activity. The fix is to (a) measure outcome, (b) accept a robust negative as a real result, and (c) redirect effort to the only thing that could change the inputs: external ground truth ([page 9](09-open-questions.md)).

---

[← External Sources](07-external-sources.md) · [Wiki home](README.md) · Next: [Open Questions →](09-open-questions.md)
