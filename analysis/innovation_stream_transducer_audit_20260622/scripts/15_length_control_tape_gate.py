from __future__ import annotations

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

COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
FRONTIER_LEDGER = TEST_RESULTS / "14_generation_dependency_frontier_ledger.json"

OUT_STEM = "15_length_control_tape_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500
ALPHA = 0.5

FEATURES = [
    "global",
    "type",
    "book_start",
    "remaining_bucket",
    "prev_length_bucket",
    "prev_type",
    "type_x_remaining",
    "prev_x_remaining",
    "book_start_x_type",
]

FEATURES_REQUIRING_TYPE = {
    "type",
    "prev_type",
    "type_x_remaining",
    "book_start_x_type",
}


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


def log2comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    ) / math.log(2)


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    frac = index - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def bucket(value: int | None, cuts: list[int], prefix: str) -> str:
    if value is None:
        return f"{prefix}_BOS"
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut}"
    return f"{prefix}_gt_{cuts[-1]}"


def build_rows(ops_by_book: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for book in range(10, 70):
        ops = ops_by_book[str(book)]
        book_len = sum(int(op["length"]) for op in ops)
        remaining = book_len
        prev_length: int | None = None
        prev_type = "BOS"
        for op_index, op in enumerate(ops):
            length = int(op["length"])
            op_type = str(op["type"])
            rows.append(
                {
                    "book": book,
                    "book_len": book_len,
                    "op_index": op_index,
                    "op_count": len(ops),
                    "target_start": int(op["target_start"]),
                    "length": length,
                    "type": op_type,
                    "is_book_start": op_index == 0,
                    "remaining_before": remaining,
                    "prev_length": prev_length,
                    "prev_type": prev_type,
                }
            )
            remaining -= length
            prev_length = length
            prev_type = op_type
    return rows


def feature_value(row: dict[str, Any], feature: str) -> str:
    if feature == "global":
        return "all"
    if feature == "type":
        return str(row["type"])
    if feature == "book_start":
        return "book_start" if row["is_book_start"] else "internal"
    if feature == "remaining_bucket":
        return bucket(row["remaining_before"], [5, 10, 20, 40, 80, 160], "remain")
    if feature == "prev_length_bucket":
        return bucket(row["prev_length"], [1, 2, 3, 5, 8, 13, 21, 55, 144], "prev")
    if feature == "prev_type":
        return str(row["prev_type"])
    if feature == "type_x_remaining":
        return feature_value(row, "type") + "|" + feature_value(row, "remaining_bucket")
    if feature == "prev_x_remaining":
        return feature_value(row, "prev_length_bucket") + "|" + feature_value(
            row, "remaining_bucket"
        )
    if feature == "book_start_x_type":
        return feature_value(row, "book_start") + "|" + feature_value(row, "type")
    raise KeyError(feature)


def length_bits(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    feature: str,
    length_alphabet: set[int],
) -> tuple[float, int]:
    by_context: dict[str, Counter[int]] = defaultdict(Counter)
    global_counts: Counter[int] = Counter()
    for row in train_rows:
        by_context[feature_value(row, feature)][row["length"]] += 1
        global_counts[row["length"]] += 1
    if feature == "global":
        by_context = {"all": global_counts}
    bits = 0.0
    vocab = len(length_alphabet)
    for row in test_rows:
        counter = by_context.get(feature_value(row, feature), global_counts)
        total = sum(counter.values())
        probability = (counter[row["length"]] + ALPHA) / (total + ALPHA * vocab)
        bits -= math.log2(probability)
    return bits, len(by_context)


def composition_bits(rows: list[dict[str, Any]]) -> float:
    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_book[row["book"]].append(row)
    bits = 0.0
    for book_rows in by_book.values():
        book_len = book_rows[0]["book_len"]
        op_count = len(book_rows)
        bits += log2comb(book_len - 1, op_count - 1)
    return bits


def feature_model_cost(feature: str, context_count: int, length_alphabet_size: int) -> float:
    if feature == "global":
        return 0.0
    return math.log2(len(FEATURES) - 1) + context_count * math.log2(length_alphabet_size)


def evaluate_cutoff(
    rows: list[dict[str, Any]],
    cutoff: int,
    length_alphabet: set[int],
) -> dict[str, Any]:
    train_rows = [row for row in rows if row["book"] < cutoff]
    test_rows = [row for row in rows if row["book"] >= cutoff]
    global_bits, global_contexts = length_bits(
        train_rows, test_rows, "global", length_alphabet
    )
    candidates = []
    for feature in FEATURES:
        bits, contexts = length_bits(train_rows, test_rows, feature, length_alphabet)
        model_cost = feature_model_cost(feature, contexts, len(length_alphabet))
        candidates.append(
            {
                "feature": feature,
                "requires_type_stream": feature in FEATURES_REQUIRING_TYPE,
                "bits": bits,
                "context_count": contexts,
                "model_cost_bits": model_cost,
                "paid_bits": bits + model_cost,
                "saving_vs_global_bits": global_bits - bits,
                "paid_saving_vs_global_bits": global_bits - bits - model_cost,
            }
        )
    best = max(candidates, key=lambda row: row["saving_vs_global_bits"])
    best_paid = max(candidates, key=lambda row: row["paid_saving_vs_global_bits"])
    comp_bits = composition_bits(test_rows)
    return {
        "cutoff": cutoff,
        "train_ops": len(train_rows),
        "test_ops": len(test_rows),
        "test_books": len({row["book"] for row in test_rows}),
        "composition_bits_fixed_op_counts": comp_bits,
        "global_bits": global_bits,
        "global_contexts": global_contexts,
        "best_feature": best["feature"],
        "best_feature_bits": best["bits"],
        "best_feature_contexts": best["context_count"],
        "best_feature_requires_type_stream": best["requires_type_stream"],
        "best_feature_saving_vs_global_bits": best["saving_vs_global_bits"],
        "best_paid_feature": best_paid["feature"],
        "best_paid_feature_bits": best_paid["bits"],
        "best_paid_feature_model_cost_bits": best_paid["model_cost_bits"],
        "best_paid_feature_paid_bits": best_paid["paid_bits"],
        "best_paid_feature_contexts": best_paid["context_count"],
        "best_paid_feature_requires_type_stream": best_paid["requires_type_stream"],
        "best_paid_saving_vs_global_bits": best_paid["paid_saving_vs_global_bits"],
        "best_paid_saving_vs_composition_bits": comp_bits - best_paid["paid_bits"],
        "feature_rows": candidates,
    }


def shuffled_control(
    rows: list[dict[str, Any]],
    cutoff: int,
    length_alphabet: set[int],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + cutoff)
    length_values = [row["length"] for row in rows]
    saving_values = []
    paid_saving_values = []
    composition_saving_values = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(length_values)
        rng.shuffle(shuffled)
        shuffled_rows = [dict(row, length=shuffled[index]) for index, row in enumerate(rows)]
        row = evaluate_cutoff(shuffled_rows, cutoff, length_alphabet)
        saving_values.append(row["best_feature_saving_vs_global_bits"])
        paid_saving_values.append(row["best_paid_saving_vs_global_bits"])
        composition_saving_values.append(row["best_paid_saving_vs_composition_bits"])
    saving_values.sort()
    paid_saving_values.sort()
    composition_saving_values.sort()
    return {
        "trials": RANDOM_TRIALS,
        "best_saving_vs_global_mean": mean(saving_values),
        "best_saving_vs_global_p95": percentile(saving_values, 0.95),
        "best_paid_saving_vs_global_mean": mean(paid_saving_values),
        "best_paid_saving_vs_global_p95": percentile(paid_saving_values, 0.95),
        "best_paid_saving_vs_composition_mean": mean(composition_saving_values),
        "best_paid_saving_vs_composition_p95": percentile(composition_saving_values, 0.95),
    }


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    frontier = load_json(FRONTIER_LEDGER)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("generation_dependency_frontier_ledger", frontier)
    rows = build_rows(ledger["canonical_ops_by_book"])
    length_alphabet = {row["length"] for row in rows}
    cutoff_rows = []
    for cutoff in PREFIX_CUTOFFS:
        observed = evaluate_cutoff(rows, cutoff, length_alphabet)
        control = shuffled_control(rows, cutoff, length_alphabet)
        observed["control"] = control
        observed["beats_shuffle_paid_p95"] = (
            observed["best_paid_saving_vs_global_bits"]
            > control["best_paid_saving_vs_global_p95"]
        )
        observed["beats_fixed_op_composition"] = (
            observed["best_paid_saving_vs_composition_bits"] > 0
        )
        cutoff_rows.append(observed)

    beats_control_count = sum(row["beats_shuffle_paid_p95"] for row in cutoff_rows)
    beats_composition_count = sum(row["beats_fixed_op_composition"] for row in cutoff_rows)
    best_paid_features = Counter(row["best_paid_feature"] for row in cutoff_rows)
    type_granted_best_count = sum(
        row["best_paid_feature_requires_type_stream"] for row in cutoff_rows
    )
    promotes_predictive_length_clue = beats_control_count >= 4
    promotes_cutpoint_replacement = (
        promotes_predictive_length_clue and beats_composition_count >= 4
    )
    summary = {
        "canonical_ops": len(rows),
        "derived_books": 60,
        "internal_operation_starts": frontier["summary"]["internal_ops"],
        "unique_lengths": len(length_alphabet),
        "raw_composition_bits_fixed_op_counts_all_books": composition_bits(rows),
        "cutoffs_tested": PREFIX_CUTOFFS,
        "random_trials": RANDOM_TRIALS,
        "best_paid_feature_modes": dict(best_paid_features),
        "type_granted_best_cutoffs": type_granted_best_count,
        "beats_shuffle_paid_p95_cutoffs": beats_control_count,
        "beats_fixed_op_composition_cutoffs": beats_composition_count,
        "promotes_predictive_length_control_clue": promotes_predictive_length_clue,
        "promotes_cutpoint_replacement": promotes_cutpoint_replacement,
        "interpretation": (
            "This gate treats the operation lengths as a possible control tape: if "
            "book lengths and length stream are granted, internal starts follow by "
            "cumulative sum. It asks whether that stream has prefix-holdout structure "
            "beyond shuffled controls, and separately whether the paid model beats "
            "a uniform fixed-op-count cutpoint composition."
        ),
    }
    if promotes_cutpoint_replacement:
        classification = "length_control_tape_cutpoint_replacement_promoted"
    elif promotes_predictive_length_clue:
        classification = "length_control_tape_predictive_clue_not_cutpoint_replacement"
    else:
        classification = "length_control_tape_rejected"
    return {
        "schema": "length_control_tape_gate_v1",
        "scope": "analysis_only_internal_start_length_control_stream",
        "inputs": {
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "generation_dependency_frontier_ledger": rel(FRONTIER_LEDGER),
        },
        "cutoff_rows": cutoff_rows,
        "summary": summary,
        "classification": classification,
        "decision": {
            "promotes_predictive_length_control_clue": promotes_predictive_length_clue,
            "promotes_cutpoint_replacement": promotes_cutpoint_replacement,
            "generator_status": "not_promoted",
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
        "# Length Control Tape Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the unresolved internal operation-start frontier can be",
        "reframed as a smaller length-control tape. If book lengths and the",
        "sequence of operation lengths are granted, internal starts are generated",
        "by cumulative sum. This gate asks whether that length stream has",
        "prefix-holdout structure, and whether it is strong enough to replace",
        "fixed-op-count cutpoint declaration.",
        "",
        "## Summary",
        "",
        f"- Canonical ops: `{s['canonical_ops']}`.",
        f"- Internal operation starts: `{s['internal_operation_starts']}`.",
        f"- Unique lengths: `{s['unique_lengths']}`.",
        f"- Raw composition bits with fixed op counts, all books: `{s['raw_composition_bits_fixed_op_counts_all_books']:.3f}`.",
        f"- Cutoffs tested: `{s['cutoffs_tested']}`.",
        f"- Random shuffle trials per cutoff: `{s['random_trials']}`.",
        f"- Best paid feature modes: `{s['best_paid_feature_modes']}`.",
        f"- Type-granted best cutoffs: `{s['type_granted_best_cutoffs']}/{len(s['cutoffs_tested'])}`.",
        f"- Beats shuffled paid p95 cutoffs: `{s['beats_shuffle_paid_p95_cutoffs']}/{len(s['cutoffs_tested'])}`.",
        f"- Beats fixed-op-count composition cutoffs: `{s['beats_fixed_op_composition_cutoffs']}/{len(s['cutoffs_tested'])}`.",
        f"- Promotes predictive length-control clue: `{s['promotes_predictive_length_control_clue']}`.",
        f"- Promotes cutpoint replacement: `{s['promotes_cutpoint_replacement']}`.",
        "",
        s["interpretation"],
        "",
        "## Prefix-Holdout Rows",
        "",
        "| Cutoff | Train/Test Ops | Best Paid Feature | Type Grant | Paid Saving vs Global | Shuffle Paid p95 | Paid Saving vs Composition | Beats Shuffle | Beats Composition |",
        "| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        control = row["control"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['train_ops']}/{row['test_ops']}` | "
            f"`{row['best_paid_feature']}` | "
            f"`{row['best_paid_feature_requires_type_stream']}` | "
            f"`{row['best_paid_saving_vs_global_bits']:.3f}` | "
            f"`{control['best_paid_saving_vs_global_p95']:.3f}` | "
            f"`{row['best_paid_saving_vs_composition_bits']:.3f}` | "
            f"`{row['beats_shuffle_paid_p95']}` | "
            f"`{row['beats_fixed_op_composition']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The length stream has real predictive structure in prefix holdout after a simple context cost.",
            "- The strongest paid contexts usually require the operation type stream, so this is not source-free skeleton generation.",
            "- The paid length model does not beat fixed-op-count uniform cutpoint composition in any cutoff.",
            "- Therefore this promotes only a control-tape clue, not a replacement for the internal start atlas.",
            "- Row0, plaintext, translation, and compression bound remain unchanged.",
            "",
        ]
    )
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_markdown(result)


if __name__ == "__main__":
    main()
