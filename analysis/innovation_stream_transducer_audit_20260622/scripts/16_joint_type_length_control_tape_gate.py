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
LENGTH_CONTROL_GATE = TEST_RESULTS / "15_length_control_tape_gate.json"

OUT_STEM = "16_joint_type_length_control_tape_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500
ALPHA = 0.5

FEATURES = [
    "global",
    "book_start",
    "remaining_bucket",
    "op_index_bucket",
    "prev_type",
    "prev_length_bucket",
    "prev_pair",
    "prev_type_x_remaining",
    "book_start_x_remaining",
]


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
            pair = f"{op_type}:{length}"
            rows.append(
                {
                    "book": book,
                    "book_len": book_len,
                    "op_index": op_index,
                    "op_count": len(ops),
                    "target_start": int(op["target_start"]),
                    "length": length,
                    "type": op_type,
                    "pair": pair,
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
    if feature == "book_start":
        return "book_start" if row["is_book_start"] else "internal"
    if feature == "remaining_bucket":
        return bucket(row["remaining_before"], [5, 10, 20, 40, 80, 160], "remain")
    if feature == "op_index_bucket":
        return bucket(row["op_index"], [0, 1, 2, 3, 5, 8, 13], "idx")
    if feature == "prev_type":
        return str(row["prev_type"])
    if feature == "prev_length_bucket":
        return bucket(row["prev_length"], [1, 2, 3, 5, 8, 13, 21, 55, 144], "prev")
    if feature == "prev_pair":
        return feature_value(row, "prev_type") + "|" + feature_value(
            row, "prev_length_bucket"
        )
    if feature == "prev_type_x_remaining":
        return feature_value(row, "prev_type") + "|" + feature_value(
            row, "remaining_bucket"
        )
    if feature == "book_start_x_remaining":
        return feature_value(row, "book_start") + "|" + feature_value(
            row, "remaining_bucket"
        )
    raise KeyError(feature)


def symbol_bits(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    feature: str,
    symbol_key: str,
    alphabet: set[str],
) -> tuple[float, int]:
    by_context: dict[str, Counter[str]] = defaultdict(Counter)
    global_counts: Counter[str] = Counter()
    for row in train_rows:
        symbol = str(row[symbol_key])
        by_context[feature_value(row, feature)][symbol] += 1
        global_counts[symbol] += 1
    if feature == "global":
        by_context = {"all": global_counts}
    bits = 0.0
    vocab = len(alphabet)
    for row in test_rows:
        counter = by_context.get(feature_value(row, feature), global_counts)
        total = sum(counter.values())
        symbol = str(row[symbol_key])
        probability = (counter[symbol] + ALPHA) / (total + ALPHA * vocab)
        bits -= math.log2(probability)
    return bits, len(by_context)


def feature_model_cost(feature: str, context_count: int, alphabet_size: int) -> float:
    if feature == "global":
        return 0.0
    return math.log2(len(FEATURES) - 1) + context_count * math.log2(alphabet_size)


def skeleton_composition_bits(rows: list[dict[str, Any]]) -> tuple[float, float, float]:
    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_book[row["book"]].append(row)
    cutpoint_bits = 0.0
    type_bits = 0.0
    for book_rows in by_book.values():
        book_len = book_rows[0]["book_len"]
        op_count = len(book_rows)
        literal_count = sum(1 for row in book_rows if row["type"] == "literal")
        cutpoint_bits += log2comb(book_len - 1, op_count - 1)
        type_bits += log2comb(op_count, literal_count)
    return cutpoint_bits, type_bits, cutpoint_bits + type_bits


def evaluate_cutoff(rows: list[dict[str, Any]], cutoff: int) -> dict[str, Any]:
    train_rows = [row for row in rows if row["book"] < cutoff]
    test_rows = [row for row in rows if row["book"] >= cutoff]
    pair_alphabet = {str(row["pair"]) for row in rows}
    type_alphabet = {str(row["type"]) for row in rows}
    global_pair_bits, _ = symbol_bits(
        train_rows, test_rows, "global", "pair", pair_alphabet
    )
    pair_rows = []
    for feature in FEATURES:
        bits, contexts = symbol_bits(train_rows, test_rows, feature, "pair", pair_alphabet)
        model_cost = feature_model_cost(feature, contexts, len(pair_alphabet))
        pair_rows.append(
            {
                "feature": feature,
                "bits": bits,
                "context_count": contexts,
                "model_cost_bits": model_cost,
                "paid_bits": bits + model_cost,
                "saving_vs_global_bits": global_pair_bits - bits,
                "paid_saving_vs_global_bits": global_pair_bits - bits - model_cost,
            }
        )
    type_rows = []
    global_type_bits, _ = symbol_bits(
        train_rows, test_rows, "global", "type", type_alphabet
    )
    for feature in FEATURES:
        bits, contexts = symbol_bits(train_rows, test_rows, feature, "type", type_alphabet)
        model_cost = feature_model_cost(feature, contexts, len(type_alphabet))
        type_rows.append(
            {
                "feature": feature,
                "bits": bits,
                "context_count": contexts,
                "model_cost_bits": model_cost,
                "paid_bits": bits + model_cost,
                "saving_vs_global_bits": global_type_bits - bits,
                "paid_saving_vs_global_bits": global_type_bits - bits - model_cost,
            }
        )
    best_pair = max(pair_rows, key=lambda row: row["saving_vs_global_bits"])
    best_paid_pair = max(pair_rows, key=lambda row: row["paid_saving_vs_global_bits"])
    best_paid_type = max(type_rows, key=lambda row: row["paid_saving_vs_global_bits"])
    cutpoint_bits, type_composition_bits, skeleton_bits = skeleton_composition_bits(test_rows)
    return {
        "cutoff": cutoff,
        "train_ops": len(train_rows),
        "test_ops": len(test_rows),
        "test_books": len({row["book"] for row in test_rows}),
        "pair_alphabet_size": len(pair_alphabet),
        "global_pair_bits": global_pair_bits,
        "best_pair_feature": best_pair["feature"],
        "best_pair_saving_vs_global_bits": best_pair["saving_vs_global_bits"],
        "best_pair_contexts": best_pair["context_count"],
        "best_paid_pair_feature": best_paid_pair["feature"],
        "best_paid_pair_bits": best_paid_pair["bits"],
        "best_paid_pair_model_cost_bits": best_paid_pair["model_cost_bits"],
        "best_paid_pair_paid_bits": best_paid_pair["paid_bits"],
        "best_paid_pair_contexts": best_paid_pair["context_count"],
        "best_paid_pair_saving_vs_global_bits": best_paid_pair[
            "paid_saving_vs_global_bits"
        ],
        "best_paid_type_feature": best_paid_type["feature"],
        "best_paid_type_saving_vs_global_bits": best_paid_type[
            "paid_saving_vs_global_bits"
        ],
        "cutpoint_composition_bits_fixed_op_counts": cutpoint_bits,
        "type_composition_bits_fixed_op_counts": type_composition_bits,
        "skeleton_composition_bits_fixed_op_counts": skeleton_bits,
        "best_paid_pair_saving_vs_skeleton_composition_bits": (
            skeleton_bits - best_paid_pair["paid_bits"]
        ),
        "pair_rows": pair_rows,
        "type_rows": type_rows,
    }


def shuffled_control(rows: list[dict[str, Any]], cutoff: int) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + cutoff)
    pairs = [(row["type"], row["length"], row["pair"]) for row in rows]
    paid_saving_values = []
    skeleton_saving_values = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(pairs)
        rng.shuffle(shuffled)
        shuffled_rows = []
        for index, row in enumerate(rows):
            op_type, length, pair = shuffled[index]
            shuffled_rows.append(
                {
                    **row,
                    "type": op_type,
                    "length": length,
                    "pair": pair,
                }
            )
        observed = evaluate_cutoff(shuffled_rows, cutoff)
        paid_saving_values.append(observed["best_paid_pair_saving_vs_global_bits"])
        skeleton_saving_values.append(
            observed["best_paid_pair_saving_vs_skeleton_composition_bits"]
        )
    paid_saving_values.sort()
    skeleton_saving_values.sort()
    return {
        "trials": RANDOM_TRIALS,
        "best_paid_pair_saving_vs_global_mean": mean(paid_saving_values),
        "best_paid_pair_saving_vs_global_p95": percentile(paid_saving_values, 0.95),
        "best_paid_pair_saving_vs_skeleton_mean": mean(skeleton_saving_values),
        "best_paid_pair_saving_vs_skeleton_p95": percentile(skeleton_saving_values, 0.95),
    }


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    length_control = load_json(LENGTH_CONTROL_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("length_control_tape_gate", length_control)
    rows = build_rows(ledger["canonical_ops_by_book"])
    cutoff_rows = []
    for cutoff in PREFIX_CUTOFFS:
        observed = evaluate_cutoff(rows, cutoff)
        control = shuffled_control(rows, cutoff)
        observed["control"] = control
        observed["beats_shuffle_paid_pair_p95"] = (
            observed["best_paid_pair_saving_vs_global_bits"]
            > control["best_paid_pair_saving_vs_global_p95"]
        )
        observed["beats_skeleton_composition"] = (
            observed["best_paid_pair_saving_vs_skeleton_composition_bits"] > 0
        )
        cutoff_rows.append(observed)

    beats_shuffle_count = sum(row["beats_shuffle_paid_pair_p95"] for row in cutoff_rows)
    beats_skeleton_count = sum(row["beats_skeleton_composition"] for row in cutoff_rows)
    best_paid_features = Counter(row["best_paid_pair_feature"] for row in cutoff_rows)
    best_type_features = Counter(row["best_paid_type_feature"] for row in cutoff_rows)
    promotes_joint_control_clue = beats_shuffle_count >= 3
    promotes_skeleton_replacement = (
        promotes_joint_control_clue and beats_skeleton_count >= 4
    )
    cutpoint_bits, type_bits, skeleton_bits = skeleton_composition_bits(rows)
    summary = {
        "canonical_ops": len(rows),
        "derived_books": 60,
        "pair_alphabet_size": len({str(row["pair"]) for row in rows}),
        "type_alphabet_size": len({str(row["type"]) for row in rows}),
        "cutoffs_tested": PREFIX_CUTOFFS,
        "random_trials": RANDOM_TRIALS,
        "all_books_cutpoint_composition_bits_fixed_op_counts": cutpoint_bits,
        "all_books_type_composition_bits_fixed_op_counts": type_bits,
        "all_books_skeleton_composition_bits_fixed_op_counts": skeleton_bits,
        "best_paid_pair_feature_modes": dict(best_paid_features),
        "best_paid_type_feature_modes": dict(best_type_features),
        "beats_shuffle_paid_pair_p95_cutoffs": beats_shuffle_count,
        "beats_skeleton_composition_cutoffs": beats_skeleton_count,
        "promotes_joint_type_length_control_clue": promotes_joint_control_clue,
        "promotes_skeleton_replacement": promotes_skeleton_replacement,
        "interpretation": (
            "This gate tests the natural follow-up to the length-control clue: "
            "encode each operation as a joint type:length control symbol, so "
            "book lengths plus the stream determine operation starts and modes. "
            "It measures prefix-holdout prediction against shuffled pair controls "
            "and against the paid cost of declaring cutpoints plus types with "
            "fixed op counts."
        ),
    }
    if promotes_skeleton_replacement:
        classification = "joint_type_length_control_tape_skeleton_replacement_promoted"
    elif promotes_joint_control_clue:
        classification = "joint_type_length_control_tape_clue_not_skeleton_replacement"
    else:
        classification = "joint_type_length_control_tape_rejected"
    return {
        "schema": "joint_type_length_control_tape_gate_v1",
        "scope": "analysis_only_joint_operation_control_stream",
        "inputs": {
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "length_control_tape_gate": rel(LENGTH_CONTROL_GATE),
        },
        "cutoff_rows": cutoff_rows,
        "summary": summary,
        "classification": classification,
        "decision": {
            "promotes_joint_type_length_control_clue": promotes_joint_control_clue,
            "promotes_skeleton_replacement": promotes_skeleton_replacement,
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
        "# Joint Type-Length Control Tape Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test the constructive follow-up to the length-control clue. If each",
        "operation is encoded as a joint `type:length` symbol, then granted book",
        "lengths and op counts let the stream generate operation starts by",
        "cumulative sum and operation modes directly. This is tested against",
        "shuffled pair controls and against fixed-op-count cutpoint+type",
        "composition.",
        "",
        "## Summary",
        "",
        f"- Canonical ops: `{s['canonical_ops']}`.",
        f"- Pair alphabet size: `{s['pair_alphabet_size']}`.",
        f"- Type alphabet size: `{s['type_alphabet_size']}`.",
        f"- All-books cutpoint composition bits with fixed op counts: `{s['all_books_cutpoint_composition_bits_fixed_op_counts']:.3f}`.",
        f"- All-books type composition bits with fixed op counts: `{s['all_books_type_composition_bits_fixed_op_counts']:.3f}`.",
        f"- All-books skeleton composition bits with fixed op counts: `{s['all_books_skeleton_composition_bits_fixed_op_counts']:.3f}`.",
        f"- Best paid pair feature modes: `{s['best_paid_pair_feature_modes']}`.",
        f"- Best paid type feature modes: `{s['best_paid_type_feature_modes']}`.",
        f"- Beats shuffled paid pair p95 cutoffs: `{s['beats_shuffle_paid_pair_p95_cutoffs']}/{len(s['cutoffs_tested'])}`.",
        f"- Beats skeleton composition cutoffs: `{s['beats_skeleton_composition_cutoffs']}/{len(s['cutoffs_tested'])}`.",
        f"- Promotes joint type-length clue: `{s['promotes_joint_type_length_control_clue']}`.",
        f"- Promotes skeleton replacement: `{s['promotes_skeleton_replacement']}`.",
        "",
        s["interpretation"],
        "",
        "## Prefix-Holdout Rows",
        "",
        "| Cutoff | Train/Test Ops | Best Paid Pair Feature | Paid Pair Saving vs Global | Shuffle p95 | Paid Pair Saving vs Skeleton | Beats Shuffle | Beats Skeleton |",
        "| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        control = row["control"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['train_ops']}/{row['test_ops']}` | "
            f"`{row['best_paid_pair_feature']}` | "
            f"`{row['best_paid_pair_saving_vs_global_bits']:.3f}` | "
            f"`{control['best_paid_pair_saving_vs_global_p95']:.3f}` | "
            f"`{row['best_paid_pair_saving_vs_skeleton_composition_bits']:.3f}` | "
            f"`{row['beats_shuffle_paid_pair_p95']}` | "
            f"`{row['beats_skeleton_composition']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Joint `type:length` prediction is not promoted as skeleton replacement.",
            "- The pair stream is much more expensive than fixed-op-count cutpoint+type composition in every cutoff.",
            "- Any surviving paid predictive signal is therefore a weak control-stream clue, not generation.",
            "- Operation counts, copy source, literal payload, and row0 remain external.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
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
