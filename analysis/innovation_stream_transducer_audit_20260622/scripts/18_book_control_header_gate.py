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
JOINT_CONTROL_GATE = TEST_RESULTS / "16_joint_type_length_control_tape_gate.json"
HYBRID_TAPE_SUBCODEC_GATE = TEST_RESULTS / "17_hybrid_innovation_tape_subcodec_gate.json"

OUT_STEM = "18_book_control_header_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500
ALPHA = 0.5

FIELDS = ["op_count", "literal_ops", "literal_digits"]
FEATURES = [
    "global",
    "book_mod5",
    "book_mod10",
    "book_decade",
    "book_length_bucket",
    "prev_header",
    "prev_op_count_bucket",
    "book_mod10_x_length_bucket",
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


def bucket(value: int | None, cuts: list[int], prefix: str) -> str:
    if value is None:
        return f"{prefix}_BOS"
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut}"
    return f"{prefix}_gt_{cuts[-1]}"


def feature_value(row: dict[str, Any], feature: str) -> str:
    if feature == "global":
        return "all"
    if feature == "book_mod5":
        return f"mod5_{row['book'] % 5}"
    if feature == "book_mod10":
        return f"mod10_{row['book'] % 10}"
    if feature == "book_decade":
        return f"decade_{row['book'] // 10}"
    if feature == "book_length_bucket":
        return bucket(row["book_length"], [60, 100, 140, 180, 240], "len")
    if feature == "prev_header":
        return str(row["prev_header"] or "BOS")
    if feature == "prev_op_count_bucket":
        return bucket(row["prev_op_count"], [1, 2, 3, 5, 8, 13], "prev_ops")
    if feature == "book_mod10_x_length_bucket":
        return feature_value(row, "book_mod10") + "|" + feature_value(
            row, "book_length_bucket"
        )
    raise KeyError(feature)


def build_rows(ops_by_book: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    previous_header = None
    previous_op_count = None
    for book in range(10, 70):
        ops = ops_by_book[str(book)]
        op_count = len(ops)
        literal_ops = sum(1 for op in ops if op["type"] == "literal")
        literal_digits = sum(
            int(op["length"]) for op in ops if op["type"] == "literal"
        )
        book_length = sum(int(op["length"]) for op in ops)
        header = f"{op_count}:{literal_ops}:{literal_digits}"
        row = {
            "book": book,
            "book_length": book_length,
            "op_count": op_count,
            "literal_ops": literal_ops,
            "literal_digits": literal_digits,
            "header": header,
            "prev_header": previous_header,
            "prev_op_count": previous_op_count,
        }
        rows.append(row)
        previous_header = header
        previous_op_count = op_count
    return rows


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
        symbol = str(row[symbol_key])
        counter = by_context.get(feature_value(row, feature), global_counts)
        total = sum(counter.values())
        probability = (counter[symbol] + ALPHA) / (total + ALPHA * vocab)
        bits -= math.log2(probability)
    return bits, len(by_context)


def feature_model_cost(feature: str, context_count: int, alphabet_size: int) -> float:
    if feature == "global":
        return 0.0
    return math.log2(len(FEATURES) - 1) + context_count * math.log2(alphabet_size)


def best_symbol_model(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    symbol_key: str,
    alphabet: set[str],
) -> dict[str, Any]:
    global_bits, _ = symbol_bits(train_rows, test_rows, "global", symbol_key, alphabet)
    candidates = []
    for feature in FEATURES:
        bits, contexts = symbol_bits(train_rows, test_rows, feature, symbol_key, alphabet)
        model_cost = feature_model_cost(feature, contexts, len(alphabet))
        candidates.append(
            {
                "feature": feature,
                "bits": bits,
                "context_count": contexts,
                "model_cost_bits": model_cost,
                "paid_bits": bits + model_cost,
                "saving_vs_global_bits": global_bits - bits,
                "paid_saving_vs_global_bits": global_bits - bits - model_cost,
            }
        )
    best_paid = max(candidates, key=lambda row: row["paid_saving_vs_global_bits"])
    return {
        "global_bits": global_bits,
        "best_paid_feature": best_paid["feature"],
        "best_paid_bits": best_paid["bits"],
        "best_paid_model_cost_bits": best_paid["model_cost_bits"],
        "best_paid_total_bits": best_paid["paid_bits"],
        "best_paid_saving_vs_global_bits": best_paid["paid_saving_vs_global_bits"],
        "best_paid_contexts": best_paid["context_count"],
        "feature_rows": candidates,
    }


def evaluate_cutoff(rows: list[dict[str, Any]], cutoff: int) -> dict[str, Any]:
    train_rows = [row for row in rows if row["book"] < cutoff]
    test_rows = [row for row in rows if row["book"] >= cutoff]
    header_alphabet = {str(row["header"]) for row in rows}
    header_model = best_symbol_model(train_rows, test_rows, "header", header_alphabet)
    field_models = {}
    separate_total = 0.0
    separate_global = 0.0
    for field in FIELDS:
        alphabet = {str(row[field]) for row in rows}
        field_model = best_symbol_model(train_rows, test_rows, field, alphabet)
        field_models[field] = field_model
        separate_total += field_model["best_paid_total_bits"]
        separate_global += field_model["global_bits"]
    return {
        "cutoff": cutoff,
        "train_books": len(train_rows),
        "test_books": len(test_rows),
        "header_alphabet_size": len(header_alphabet),
        "header_global_bits": header_model["global_bits"],
        "header_best_feature": header_model["best_paid_feature"],
        "header_best_paid_total_bits": header_model["best_paid_total_bits"],
        "header_best_paid_saving_vs_global_bits": header_model[
            "best_paid_saving_vs_global_bits"
        ],
        "separate_field_global_bits": separate_global,
        "separate_field_best_paid_total_bits": separate_total,
        "header_saving_vs_separate_paid_bits": separate_total
        - header_model["best_paid_total_bits"],
        "field_models": field_models,
        "header_feature_rows": header_model["feature_rows"],
    }


def shuffled_control(rows: list[dict[str, Any]], cutoff: int) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + cutoff)
    headers = [
        (row["header"], row["op_count"], row["literal_ops"], row["literal_digits"])
        for row in rows
    ]
    header_savings = []
    separate_savings = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(headers)
        rng.shuffle(shuffled)
        shuffled_rows = []
        for index, row in enumerate(rows):
            header, op_count, literal_ops, literal_digits = shuffled[index]
            shuffled_rows.append(
                {
                    **row,
                    "header": header,
                    "op_count": op_count,
                    "literal_ops": literal_ops,
                    "literal_digits": literal_digits,
                }
            )
        observed = evaluate_cutoff(shuffled_rows, cutoff)
        header_savings.append(observed["header_best_paid_saving_vs_global_bits"])
        separate_savings.append(observed["header_saving_vs_separate_paid_bits"])
    header_savings.sort()
    separate_savings.sort()
    return {
        "trials": RANDOM_TRIALS,
        "header_paid_saving_vs_global_mean": mean(header_savings),
        "header_paid_saving_vs_global_p95": percentile(header_savings, 0.95),
        "header_saving_vs_separate_mean": mean(separate_savings),
        "header_saving_vs_separate_p95": percentile(separate_savings, 0.95),
    }


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


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    joint_control = load_json(JOINT_CONTROL_GATE)
    hybrid_tape = load_json(HYBRID_TAPE_SUBCODEC_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("joint_type_length_control_tape_gate", joint_control)
    assert_boundary("hybrid_innovation_tape_subcodec_gate", hybrid_tape)
    rows = build_rows(ledger["canonical_ops_by_book"])
    cutoff_rows = []
    for cutoff in PREFIX_CUTOFFS:
        observed = evaluate_cutoff(rows, cutoff)
        control = shuffled_control(rows, cutoff)
        observed["control"] = control
        observed["beats_shuffle_header_p95"] = (
            observed["header_best_paid_saving_vs_global_bits"]
            > control["header_paid_saving_vs_global_p95"]
        )
        observed["beats_separate_paid_fields"] = (
            observed["header_saving_vs_separate_paid_bits"] > 0
        )
        cutoff_rows.append(observed)
    beats_shuffle = sum(row["beats_shuffle_header_p95"] for row in cutoff_rows)
    beats_separate = sum(row["beats_separate_paid_fields"] for row in cutoff_rows)
    best_features = Counter(row["header_best_feature"] for row in cutoff_rows)
    promotes_header_clue = beats_shuffle >= 4
    promotes_joint_header = promotes_header_clue and beats_separate >= 4
    summary = {
        "book_count": len(rows),
        "header_alphabet_size": len({str(row["header"]) for row in rows}),
        "op_count_alphabet_size": len({str(row["op_count"]) for row in rows}),
        "literal_ops_alphabet_size": len({str(row["literal_ops"]) for row in rows}),
        "literal_digits_alphabet_size": len(
            {str(row["literal_digits"]) for row in rows}
        ),
        "cutoffs_tested": PREFIX_CUTOFFS,
        "random_trials": RANDOM_TRIALS,
        "best_header_feature_modes": dict(best_features),
        "beats_shuffle_header_p95_cutoffs": beats_shuffle,
        "beats_separate_paid_fields_cutoffs": beats_separate,
        "promotes_book_control_header_clue": promotes_header_clue,
        "promotes_joint_header_replacement": promotes_joint_header,
        "interpretation": (
            "This gate tests whether per-book control fields form one useful "
            "header for the transducer: op_count, literal_op_count, and "
            "literal_tape_digits. It compares a joint header predictor against "
            "shuffled controls and against separately coded field predictors."
        ),
    }
    if promotes_joint_header:
        classification = "book_control_header_replacement_promoted"
    elif promotes_header_clue:
        classification = "book_control_header_clue_not_replacement"
    else:
        classification = "book_control_header_rejected"
    return {
        "schema": "book_control_header_gate_v1",
        "scope": "analysis_only_joint_book_level_control_header",
        "inputs": {
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "joint_type_length_control_tape_gate": rel(JOINT_CONTROL_GATE),
            "hybrid_innovation_tape_subcodec_gate": rel(HYBRID_TAPE_SUBCODEC_GATE),
        },
        "cutoff_rows": cutoff_rows,
        "summary": summary,
        "classification": classification,
        "decision": {
            "promotes_book_control_header_clue": promotes_header_clue,
            "promotes_joint_header_replacement": promotes_joint_header,
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
        "# Book Control Header Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the transducer's remaining book-level control fields",
        "form one useful header: operation count, literal operation count,",
        "and innovation-tape digit consumption. A promoted result would reduce",
        "declared book-level control before the operation-level parser runs.",
        "",
        "## Summary",
        "",
        f"- Books: `{s['book_count']}`.",
        f"- Header alphabet size: `{s['header_alphabet_size']}`.",
        f"- Component alphabets op/literal_ops/literal_digits: `{s['op_count_alphabet_size']}` / `{s['literal_ops_alphabet_size']}` / `{s['literal_digits_alphabet_size']}`.",
        f"- Cutoffs tested: `{s['cutoffs_tested']}`.",
        f"- Random shuffle trials per cutoff: `{s['random_trials']}`.",
        f"- Best header feature modes: `{s['best_header_feature_modes']}`.",
        f"- Beats shuffled header p95 cutoffs: `{s['beats_shuffle_header_p95_cutoffs']}/{len(s['cutoffs_tested'])}`.",
        f"- Beats separately coded field predictors: `{s['beats_separate_paid_fields_cutoffs']}/{len(s['cutoffs_tested'])}`.",
        f"- Promotes book-control header clue: `{s['promotes_book_control_header_clue']}`.",
        f"- Promotes joint header replacement: `{s['promotes_joint_header_replacement']}`.",
        "",
        s["interpretation"],
        "",
        "## Prefix-Holdout Rows",
        "",
        "| Cutoff | Train/Test Books | Best Header Feature | Header Saving vs Global | Shuffle p95 | Header Saving vs Separate | Beats Shuffle | Beats Separate |",
        "| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        control = row["control"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['train_books']}/{row['test_books']}` | "
            f"`{row['header_best_feature']}` | "
            f"`{row['header_best_paid_saving_vs_global_bits']:.3f}` | "
            f"`{control['header_paid_saving_vs_global_p95']:.3f}` | "
            f"`{row['header_saving_vs_separate_paid_bits']:.3f}` | "
            f"`{row['beats_shuffle_header_p95']}` | "
            f"`{row['beats_separate_paid_fields']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- A joint book-control header is promoted only if it beats shuffled controls and separately coded fields.",
            "- If it only beats shuffled controls, it is a clue about book-level control structure, not a replacement.",
            "- This gate does not generate operation starts, copy sources, literal payload, or row0.",
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
