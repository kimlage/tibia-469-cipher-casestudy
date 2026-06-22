from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
BOUNDARY_CANDIDATE_TRIGGER_GATE = TEST_RESULTS / "10_boundary_candidate_trigger_gate.json"
GATE10_SCRIPT = HERE / "scripts" / "10_boundary_candidate_trigger_gate.py"

OUT_STEM = "11_decoder_visible_boundary_candidate_trigger_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500
POLICY = "right_ge:4"
LABELS = ("nonstart", "literal", "copy")


def load_gate10():
    spec = importlib.util.spec_from_file_location("boundary_candidate_trigger_gate", GATE10_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GATE10_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate10 = load_gate10()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def build_rows(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for book in range(10, 70):
        target = books[book]
        surprisal = gate10.book_surprisals(books, book)
        candidates = {0} | gate10.predicted_boundaries(surprisal, len(target))
        actual_by_start = {
            int(op["target_start"]): ("literal" if op["type"] == "literal" else "copy")
            for op in ops_by_book[str(book)]
        }
        ranked = sorted(range(1, len(target)), key=lambda pos: (-surprisal[pos], pos))
        rank_fraction = {pos: (index + 1) / max(1, len(ranked)) for index, pos in enumerate(ranked)}
        previous_candidate = None
        for pos in sorted(candidates):
            label = actual_by_start.get(pos, "nonstart")
            rows.append(
                {
                    "book": book,
                    "target_start": pos,
                    "remaining": len(target) - pos,
                    "label": label,
                    "is_book_start": pos == 0,
                    "surprisal": surprisal[pos],
                    "rank_fraction": rank_fraction.get(pos, 0.0),
                    "distance_from_previous_candidate": (
                        pos - previous_candidate if previous_candidate is not None else 999
                    ),
                }
            )
            previous_candidate = pos
    return rows


def bucket(value: float, cuts: list[float], prefix: str) -> str:
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut:g}"
    return f"{prefix}_gt_{cuts[-1]:g}"


def feature_value(row: dict[str, Any], feature: str) -> str:
    if feature == "global_majority":
        return "all"
    if feature == "book_start":
        return f"book_start_{row['is_book_start']}"
    if feature == "target_start_bucket":
        return bucket(row["target_start"], [0, 5, 20, 60, 120], "start")
    if feature == "remaining_bucket":
        return bucket(row["remaining"], [5, 20, 60, 120], "remain")
    if feature == "surprisal_bucket":
        return bucket(row["surprisal"], [4, 4.5, 5, 6, 8], "surp")
    if feature == "rank_bucket":
        return bucket(row["rank_fraction"], [0.03, 0.05, 0.08, 0.10, 0.15, 0.20], "rank")
    if feature == "candidate_gap_bucket":
        return bucket(row["distance_from_previous_candidate"], [1, 2, 4, 8, 16, 32], "gap")
    if feature == "book_start_x_surprisal":
        return feature_value(row, "book_start") + "|" + feature_value(row, "surprisal_bucket")
    if feature == "book_start_x_rank":
        return feature_value(row, "book_start") + "|" + feature_value(row, "rank_bucket")
    if feature == "surprisal_x_gap":
        return feature_value(row, "surprisal_bucket") + "|" + feature_value(row, "candidate_gap_bucket")
    if feature == "rank_x_gap":
        return feature_value(row, "rank_bucket") + "|" + feature_value(row, "candidate_gap_bucket")
    raise KeyError(feature)


FEATURES = [
    "global_majority",
    "book_start",
    "target_start_bucket",
    "remaining_bucket",
    "surprisal_bucket",
    "rank_bucket",
    "candidate_gap_bucket",
    "book_start_x_surprisal",
    "book_start_x_rank",
    "surprisal_x_gap",
    "rank_x_gap",
]


def train_table(train_rows: list[dict[str, Any]], feature: str) -> tuple[dict[str, str], str]:
    global_counts = Counter(row["label"] for row in train_rows)
    default = global_counts.most_common(1)[0][0]
    if feature == "global_majority":
        return {}, default
    by_context: dict[str, Counter[str]] = defaultdict(Counter)
    for row in train_rows:
        by_context[feature_value(row, feature)][row["label"]] += 1
    table = {
        context: counts.most_common(1)[0][0]
        for context, counts in by_context.items()
    }
    return table, default


def predict(row: dict[str, Any], feature: str, table: dict[str, str], default: str) -> str:
    if feature == "global_majority":
        return default
    return table.get(feature_value(row, feature), default)


def evaluate_feature(
    rows: list[dict[str, Any]],
    cutoff: int,
    feature: str,
    feature_count: int,
) -> dict[str, Any]:
    train_rows = [row for row in rows if 10 <= row["book"] < cutoff]
    test_rows = [row for row in rows if cutoff <= row["book"] < 70]
    table, default = train_table(train_rows, feature)
    predictions = [predict(row, feature, table, default) for row in test_rows]
    labels = [row["label"] for row in test_rows]
    counts = Counter(labels)
    errors = sum(1 for pred, label in zip(predictions, labels) if pred != label)
    start_labels = {"literal", "copy"}
    actual_starts = sum(1 for label in labels if label in start_labels)
    predicted_starts = sum(1 for pred in predictions if pred in start_labels)
    start_hits = sum(
        1
        for pred, label in zip(predictions, labels)
        if pred == label and label in start_labels
    )
    literal_hits = sum(
        1
        for pred, label in zip(predictions, labels)
        if pred == "literal" and label == "literal"
    )
    copy_hits = sum(
        1
        for pred, label in zip(predictions, labels)
        if pred == "copy" and label == "copy"
    )
    lookup_bits = gate10.log2multinomial([counts[label] for label in LABELS])
    correction_bits = gate10.log2comb(len(test_rows), errors) + errors * math.log2(len(LABELS) - 1)
    table_bits = len(table) * math.log2(len(LABELS)) if feature != "global_majority" else 0.0
    feature_id_bits = math.log2(feature_count) if feature != "global_majority" else 0.0
    total_bits = correction_bits + table_bits + feature_id_bits
    return {
        "cutoff": cutoff,
        "feature": feature,
        "train_candidates": len(train_rows),
        "test_candidates": len(test_rows),
        "test_nonstarts": counts["nonstart"],
        "test_literal_starts": counts["literal"],
        "test_copy_starts": counts["copy"],
        "actual_starts": actual_starts,
        "predicted_starts": predicted_starts,
        "start_hits": start_hits,
        "literal_hits": literal_hits,
        "copy_hits": copy_hits,
        "context_count": len(table),
        "errors": errors,
        "exact_candidates": len(test_rows) - errors,
        "lookup_bits": lookup_bits,
        "correction_bits": correction_bits,
        "table_bits": table_bits,
        "feature_id_bits": feature_id_bits,
        "total_bits": total_bits,
        "saving_vs_lookup_bits": lookup_bits - total_bits,
    }


def add_global_deltas(rows: list[dict[str, Any]]) -> None:
    global_by_cutoff = {
        row["cutoff"]: row
        for row in rows
        if row["feature"] == "global_majority"
    }
    for row in rows:
        baseline = global_by_cutoff[row["cutoff"]]
        row["delta_bits_vs_global"] = (
            row["saving_vs_lookup_bits"] - baseline["saving_vs_lookup_bits"]
        )
        row["delta_exact_vs_global"] = row["exact_candidates"] - baseline["exact_candidates"]
        row["delta_start_hits_vs_global"] = row["start_hits"] - baseline["start_hits"]


def evaluate_all(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        for feature in FEATURES:
            out.append(evaluate_feature(rows, cutoff, feature, len(FEATURES)))
    add_global_deltas(out)
    return out


def random_control(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    labels = [row["label"] for row in rows]
    best_delta_bits = []
    best_start_hits = []
    for _ in range(RANDOM_TRIALS):
        shuffled_labels = labels[:]
        rng.shuffle(shuffled_labels)
        shuffled_rows = [dict(row, label=label) for row, label in zip(rows, shuffled_labels)]
        eval_rows = evaluate_all(shuffled_rows)
        feature_rows = [row for row in eval_rows if row["feature"] != "global_majority"]
        best = max(
            feature_rows,
            key=lambda row: (
                row["delta_bits_vs_global"],
                row["delta_start_hits_vs_global"],
            ),
        )
        best_delta_bits.append(best["delta_bits_vs_global"])
        best_start_hits.append(best["delta_start_hits_vs_global"])
    best_delta_bits.sort()
    best_start_hits.sort()
    return {
        "trials": RANDOM_TRIALS,
        "best_delta_bits_mean": mean(best_delta_bits),
        "best_delta_bits_p95": gate10.percentile(best_delta_bits, 0.95),
        "best_start_hits_mean": mean(best_start_hits),
        "best_start_hits_p95": gate10.percentile(best_start_hits, 0.95),
    }


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    gate10_result = load_json(BOUNDARY_CANDIDATE_TRIGGER_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("boundary_candidate_trigger_gate", gate10_result)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    candidate_rows = build_rows(books, ledger["canonical_ops_by_book"])
    eval_rows = evaluate_all(candidate_rows)
    internal_candidate_rows = [row for row in candidate_rows if not row["is_book_start"]]
    internal_eval_rows = evaluate_all(internal_candidate_rows)
    global_rows = [row for row in eval_rows if row["feature"] == "global_majority"]
    feature_rows = [row for row in eval_rows if row["feature"] != "global_majority"]
    internal_global_rows = [
        row for row in internal_eval_rows if row["feature"] == "global_majority"
    ]
    internal_feature_rows = [
        row for row in internal_eval_rows if row["feature"] != "global_majority"
    ]
    best_global = max(global_rows, key=lambda row: row["saving_vs_lookup_bits"])
    best_feature = max(
        feature_rows,
        key=lambda row: (
            row["delta_bits_vs_global"],
            row["delta_start_hits_vs_global"],
        ),
    )
    best_overall = max(eval_rows, key=lambda row: row["saving_vs_lookup_bits"])
    best_internal_global = max(
        internal_global_rows, key=lambda row: row["saving_vs_lookup_bits"]
    )
    best_internal_feature = max(
        internal_feature_rows,
        key=lambda row: (
            row["delta_bits_vs_global"],
            row["delta_start_hits_vs_global"],
        ),
    )
    global_at_best_feature_cutoff = next(
        row for row in global_rows if row["cutoff"] == best_feature["cutoff"]
    )
    control = random_control(candidate_rows)
    internal_control = random_control(internal_candidate_rows)
    promotes = (
        best_feature["delta_bits_vs_global"] > control["best_delta_bits_p95"]
        and best_feature["delta_start_hits_vs_global"] > control["best_start_hits_p95"]
        and best_feature["saving_vs_lookup_bits"] > 0
    )
    weak = (
        not promotes
        and best_feature["delta_bits_vs_global"] > 0
        and best_feature["delta_start_hits_vs_global"] > 0
    )
    label_counts = Counter(row["label"] for row in candidate_rows)
    target_conditioned_delta = gate10_result["summary"]["best_feature_delta_bits_vs_global"]
    target_conditioning_gap = target_conditioned_delta - max(0.0, best_feature["delta_bits_vs_global"])
    promotes_internal = (
        best_internal_feature["delta_bits_vs_global"] > internal_control["best_delta_bits_p95"]
        and best_internal_feature["delta_start_hits_vs_global"] > internal_control["best_start_hits_p95"]
        and best_internal_feature["saving_vs_lookup_bits"] > 0
    )
    weak_internal = (
        not promotes_internal
        and best_internal_feature["delta_bits_vs_global"] > 0
        and best_internal_feature["delta_start_hits_vs_global"] > 0
    )
    summary = {
        "candidate_policy": POLICY,
        "candidate_count": len(candidate_rows),
        "candidate_nonstarts": label_counts["nonstart"],
        "candidate_literal_starts": label_counts["literal"],
        "candidate_copy_starts": label_counts["copy"],
        "candidate_actual_starts": label_counts["literal"] + label_counts["copy"],
        "best_overall_feature": best_overall["feature"],
        "best_overall_cutoff": best_overall["cutoff"],
        "best_overall_exact_candidates": best_overall["exact_candidates"],
        "best_overall_test_candidates": best_overall["test_candidates"],
        "best_overall_start_hits": best_overall["start_hits"],
        "best_overall_actual_starts": best_overall["actual_starts"],
        "best_overall_saving_vs_lookup_bits": best_overall["saving_vs_lookup_bits"],
        "best_global_cutoff": best_global["cutoff"],
        "best_global_exact_candidates": best_global["exact_candidates"],
        "best_global_test_candidates": best_global["test_candidates"],
        "best_global_start_hits": best_global["start_hits"],
        "best_global_saving_vs_lookup_bits": best_global["saving_vs_lookup_bits"],
        "best_feature": best_feature["feature"],
        "best_feature_cutoff": best_feature["cutoff"],
        "best_feature_exact_candidates": best_feature["exact_candidates"],
        "best_feature_test_candidates": best_feature["test_candidates"],
        "best_feature_start_hits": best_feature["start_hits"],
        "best_feature_actual_starts": best_feature["actual_starts"],
        "best_feature_literal_hits": best_feature["literal_hits"],
        "best_feature_copy_hits": best_feature["copy_hits"],
        "best_feature_predicted_starts": best_feature["predicted_starts"],
        "best_feature_errors": best_feature["errors"],
        "best_feature_saving_vs_lookup_bits": best_feature["saving_vs_lookup_bits"],
        "best_feature_global_exact_candidates": global_at_best_feature_cutoff["exact_candidates"],
        "best_feature_global_start_hits": global_at_best_feature_cutoff["start_hits"],
        "best_feature_global_saving_vs_lookup_bits": global_at_best_feature_cutoff["saving_vs_lookup_bits"],
        "best_feature_delta_bits_vs_global": best_feature["delta_bits_vs_global"],
        "best_feature_delta_exact_vs_global": best_feature["delta_exact_vs_global"],
        "best_feature_delta_start_hits_vs_global": best_feature["delta_start_hits_vs_global"],
        "target_conditioned_boundary_candidate_delta_bits": target_conditioned_delta,
        "target_conditioning_gap_bits": target_conditioning_gap,
        "internal_candidate_count": len(internal_candidate_rows),
        "internal_best_feature": best_internal_feature["feature"],
        "internal_best_feature_cutoff": best_internal_feature["cutoff"],
        "internal_best_feature_exact_candidates": best_internal_feature["exact_candidates"],
        "internal_best_feature_test_candidates": best_internal_feature["test_candidates"],
        "internal_best_feature_start_hits": best_internal_feature["start_hits"],
        "internal_best_feature_actual_starts": best_internal_feature["actual_starts"],
        "internal_best_feature_literal_hits": best_internal_feature["literal_hits"],
        "internal_best_feature_copy_hits": best_internal_feature["copy_hits"],
        "internal_best_feature_saving_vs_lookup_bits": best_internal_feature["saving_vs_lookup_bits"],
        "internal_best_feature_delta_bits_vs_global": best_internal_feature["delta_bits_vs_global"],
        "internal_best_feature_delta_start_hits_vs_global": best_internal_feature["delta_start_hits_vs_global"],
        "internal_best_global_saving_vs_lookup_bits": best_internal_global["saving_vs_lookup_bits"],
        "internal_random_delta_bits_p95": internal_control["best_delta_bits_p95"],
        "internal_random_start_hits_p95": internal_control["best_start_hits_p95"],
        "promotes_internal_decoder_visible_boundary_candidate_trigger": promotes_internal,
        "weak_internal_decoder_visible_boundary_candidate_trigger": weak_internal,
        "random_delta_bits_p95": control["best_delta_bits_p95"],
        "random_start_hits_p95": control["best_start_hits_p95"],
        "promotes_decoder_visible_boundary_candidate_trigger": promotes,
        "weak_decoder_visible_boundary_candidate_trigger": weak,
        "interpretation": (
            "This gate repeats the boundary-candidate trigger test after removing "
            "target-conditioned copy availability. It keeps the right_ge:4 "
            "candidate set and asks whether decoder-visible boundary features can "
            "separate nonstarts, literal starts, and copy starts under prefix holdout."
        ),
    }
    return {
        "schema": "decoder_visible_boundary_candidate_trigger_gate_v1",
        "scope": "analysis_only_target_free_three_way_trigger_on_threshold_boundary_candidates",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "boundary_candidate_trigger_gate": rel(BOUNDARY_CANDIDATE_TRIGGER_GATE),
        },
        "rows": eval_rows,
        "internal_rows": internal_eval_rows,
        "random_control": control,
        "internal_random_control": internal_control,
        "summary": summary,
        "classification": (
            "decoder_visible_boundary_candidate_trigger_clue_promoted"
            if promotes
            else (
                "decoder_visible_boundary_candidate_trigger_clue_weak"
                if weak
                else "decoder_visible_boundary_candidate_trigger_rejected"
            )
        ),
        "decision": {
            "promotes_decoder_visible_boundary_candidate_trigger": promotes,
            "weak_decoder_visible_boundary_candidate_trigger": weak,
            "generator_status": "not_promoted",
            "target_conditioned_copy_availability_status": "removed_for_this_gate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Decoder Visible Boundary Candidate Trigger Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the `right_ge:4` boundary candidate trigger clue survives",
        "after removing target-conditioned copy availability.",
        "",
        "## Summary",
        "",
        f"- Candidate policy: `{s['candidate_policy']}`.",
        f"- Candidate positions: `{s['candidate_count']}`.",
        f"- Candidate nonstarts/literal/copy: `{s['candidate_nonstarts']}` / `{s['candidate_literal_starts']}` / `{s['candidate_copy_starts']}`.",
        f"- Best overall feature: `{s['best_overall_feature']}`.",
        f"- Best overall cutoff: `{s['best_overall_cutoff']}`.",
        f"- Best overall exact candidates: `{s['best_overall_exact_candidates']}/{s['best_overall_test_candidates']}`.",
        f"- Best overall start hits: `{s['best_overall_start_hits']}/{s['best_overall_actual_starts']}`.",
        f"- Best overall saving vs three-way lookup: `{s['best_overall_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best global exact/start hits: `{s['best_global_exact_candidates']}/{s['best_global_test_candidates']}` / `{s['best_global_start_hits']}`.",
        f"- Best global saving vs three-way lookup: `{s['best_global_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best feature over global: `{s['best_feature']}`.",
        f"- Best feature cutoff: `{s['best_feature_cutoff']}`.",
        f"- Best feature exact candidates: `{s['best_feature_exact_candidates']}/{s['best_feature_test_candidates']}`.",
        f"- Best feature start hits: `{s['best_feature_start_hits']}/{s['best_feature_actual_starts']}`.",
        f"- Best feature literal/copy hits: `{s['best_feature_literal_hits']}` / `{s['best_feature_copy_hits']}`.",
        f"- Best feature predicted starts: `{s['best_feature_predicted_starts']}`.",
        f"- Best feature errors: `{s['best_feature_errors']}`.",
        f"- Best feature saving vs lookup: `{s['best_feature_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Same-cutoff global exact/start hits: `{s['best_feature_global_exact_candidates']}` / `{s['best_feature_global_start_hits']}`.",
        f"- Same-cutoff global saving vs lookup: `{s['best_feature_global_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best feature delta vs global: `{s['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Best feature start-hit delta vs global: `{s['best_feature_delta_start_hits_vs_global']}`.",
        f"- Target-conditioned candidate delta bits: `{s['target_conditioned_boundary_candidate_delta_bits']:.3f}`.",
        f"- Target-conditioning gap bits: `{s['target_conditioning_gap_bits']:.3f}`.",
        f"- Internal candidate positions: `{s['internal_candidate_count']}`.",
        f"- Internal best feature: `{s['internal_best_feature']}`.",
        f"- Internal best feature exact candidates: `{s['internal_best_feature_exact_candidates']}/{s['internal_best_feature_test_candidates']}`.",
        f"- Internal best feature start hits: `{s['internal_best_feature_start_hits']}/{s['internal_best_feature_actual_starts']}`.",
        f"- Internal best feature literal/copy hits: `{s['internal_best_feature_literal_hits']}` / `{s['internal_best_feature_copy_hits']}`.",
        f"- Internal best feature saving vs lookup: `{s['internal_best_feature_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Internal best feature delta vs global: `{s['internal_best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Internal random delta bits p95: `{s['internal_random_delta_bits_p95']:.3f}`.",
        f"- Promotes internal decoder-visible trigger: `{s['promotes_internal_decoder_visible_boundary_candidate_trigger']}`.",
        f"- Random delta bits p95: `{s['random_delta_bits_p95']:.3f}`.",
        f"- Random start-hit delta p95: `{s['random_start_hits_p95']:.3f}`.",
        f"- Promotes decoder-visible boundary candidate trigger: `{s['promotes_decoder_visible_boundary_candidate_trigger']}`.",
        f"- Weak decoder-visible boundary candidate trigger: `{s['weak_decoder_visible_boundary_candidate_trigger']}`.",
        "",
        s["interpretation"],
        "",
        "## Best Rows",
        "",
        "| Cutoff | Feature | Exact | Start hits | Lit/Copy hits | Pred starts | Errors | Saving | Delta bits | Delta starts | Contexts |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(
        result["rows"],
        key=lambda item: (
            item["delta_bits_vs_global"],
            item["delta_start_hits_vs_global"],
        ),
        reverse=True,
    )[:12]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['feature']}` | "
            f"`{row['exact_candidates']}/{row['test_candidates']}` | "
            f"`{row['start_hits']}/{row['actual_starts']}` | "
            f"`{row['literal_hits']}/{row['copy_hits']}` | "
            f"`{row['predicted_starts']}` | `{row['errors']}` | "
            f"`{row['saving_vs_lookup_bits']:.3f}` | "
            f"`{row['delta_bits_vs_global']:.3f}` | "
            f"`{row['delta_start_hits_vs_global']}` | `{row['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- This gate removes target-conditioned copy availability from the boundary-candidate trigger policy.",
            "- Any promoted clue here is a target-free candidate-label dependency reducer, not a closed-loop generator.",
            "- The internal-only decomposition is reported separately so book-start invariance is not overclaimed as internal skeleton generation.",
            "- The `right_ge:4` candidate set still depends on the target digit stream and still misses canonical starts.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
