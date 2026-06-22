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

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
INTERNAL_BOUNDARY_CANDIDATE_TRIGGER_GATE = (
    TEST_RESULTS / "12_internal_boundary_candidate_trigger_decomposition_gate.json"
)

OUT_STEM = "13_book_start_mode_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 1000


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


def bucket(value: int, cuts: list[int], prefix: str) -> str:
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut}"
    return f"{prefix}_gt_{cuts[-1]}"


def build_rows(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    tape_pos = 0
    emitted_len = sum(len(books[book]) for book in range(10))
    for book in range(10, 70):
        first = ops_by_book[str(book)][0]
        label = "literal" if first["type"] == "literal" else "copy"
        rows.append(
            {
                "book": book,
                "book_length": len(books[book]),
                "label": label,
                "first_op_length": int(first["length"]),
                "tape_pos": tape_pos,
                "emitted_len": emitted_len,
            }
        )
        for op in ops_by_book[str(book)]:
            if op["type"] == "literal":
                tape_pos += len(op.get("payload", ""))
        emitted_len += len(books[book])
    return rows


def feature_value(row: dict[str, Any], feature: str) -> str:
    if feature == "global_majority":
        return "all"
    if feature == "book_decade":
        return f"decade_{row['book'] // 10}"
    if feature == "book_mod10":
        return f"mod10_{row['book'] % 10}"
    if feature == "book_length_bucket":
        return bucket(row["book_length"], [80, 120, 160, 220], "len")
    if feature == "tape_pos_bucket":
        return bucket(row["tape_pos"], [0, 5, 20, 60, 120, 200], "tpos")
    if feature == "emitted_len_bucket":
        return bucket(row["emitted_len"], [2000, 4000, 6000, 8000, 10000], "emit")
    if feature == "mod10_x_length":
        return (
            feature_value(row, "book_mod10")
            + "|"
            + feature_value(row, "book_length_bucket")
        )
    if feature == "decade_x_length":
        return (
            feature_value(row, "book_decade")
            + "|"
            + feature_value(row, "book_length_bucket")
        )
    raise KeyError(feature)


FEATURES = [
    "global_majority",
    "book_decade",
    "book_mod10",
    "book_length_bucket",
    "tape_pos_bucket",
    "emitted_len_bucket",
    "mod10_x_length",
    "decade_x_length",
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


def evaluate_feature(
    rows: list[dict[str, Any]],
    cutoff: int,
    feature: str,
    feature_count: int,
) -> dict[str, Any]:
    train_rows = [row for row in rows if 10 <= row["book"] < cutoff]
    test_rows = [row for row in rows if cutoff <= row["book"] < 70]
    table, default = train_table(train_rows, feature)
    predictions = [
        default if feature == "global_majority" else table.get(feature_value(row, feature), default)
        for row in test_rows
    ]
    labels = [row["label"] for row in test_rows]
    literal_count = sum(1 for label in labels if label == "literal")
    errors = sum(1 for pred, label in zip(predictions, labels) if pred != label)
    literal_hits = sum(
        1
        for pred, label in zip(predictions, labels)
        if pred == "literal" and label == "literal"
    )
    lookup_bits = log2comb(len(test_rows), literal_count)
    correction_bits = log2comb(len(test_rows), errors)
    table_bits = len(table) if feature != "global_majority" else 0.0
    feature_id_bits = math.log2(feature_count) if feature != "global_majority" else 0.0
    total_bits = correction_bits + table_bits + feature_id_bits
    return {
        "cutoff": cutoff,
        "feature": feature,
        "train_books": len(train_rows),
        "test_books": len(test_rows),
        "test_literals": literal_count,
        "test_copies": len(test_rows) - literal_count,
        "literal_hits": literal_hits,
        "copy_hits": sum(
            1
            for pred, label in zip(predictions, labels)
            if pred == "copy" and label == "copy"
        ),
        "context_count": len(table),
        "errors": errors,
        "exact_books": len(test_rows) - errors,
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
        row["delta_exact_vs_global"] = row["exact_books"] - baseline["exact_books"]


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
    best_delta_exact = []
    positive_cell_counts = []
    for _ in range(RANDOM_TRIALS):
        shuffled_labels = labels[:]
        rng.shuffle(shuffled_labels)
        shuffled_rows = [dict(row, label=label) for row, label in zip(rows, shuffled_labels)]
        eval_rows = evaluate_all(shuffled_rows)
        feature_rows = [row for row in eval_rows if row["feature"] != "global_majority"]
        best = max(
            feature_rows,
            key=lambda row: (row["delta_bits_vs_global"], row["delta_exact_vs_global"]),
        )
        best_delta_bits.append(best["delta_bits_vs_global"])
        best_delta_exact.append(best["delta_exact_vs_global"])
        positive_cell_counts.append(
            sum(1 for row in feature_rows if row["delta_bits_vs_global"] > 0)
        )
    best_delta_bits.sort()
    best_delta_exact.sort()
    positive_cell_counts.sort()
    return {
        "trials": RANDOM_TRIALS,
        "best_delta_bits_mean": mean(best_delta_bits),
        "best_delta_bits_p95": percentile(best_delta_bits, 0.95),
        "best_delta_exact_mean": mean(best_delta_exact),
        "best_delta_exact_p95": percentile(best_delta_exact, 0.95),
        "positive_cells_mean": mean(positive_cell_counts),
        "positive_cells_p95": percentile(positive_cell_counts, 0.95),
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
    internal_gate = load_json(INTERNAL_BOUNDARY_CANDIDATE_TRIGGER_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("internal_boundary_candidate_trigger_decomposition_gate", internal_gate)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    rows = build_rows(books, ledger["canonical_ops_by_book"])
    eval_rows = evaluate_all(rows)
    global_rows = [row for row in eval_rows if row["feature"] == "global_majority"]
    feature_rows = [row for row in eval_rows if row["feature"] != "global_majority"]
    best_global = max(global_rows, key=lambda row: row["saving_vs_lookup_bits"])
    best_feature = max(
        feature_rows,
        key=lambda row: (row["delta_bits_vs_global"], row["delta_exact_vs_global"]),
    )
    positive_cells = sum(1 for row in feature_rows if row["delta_bits_vs_global"] > 0)
    stable_positive_cells = sum(
        1
        for row in feature_rows
        if row["cutoff"] >= 30 and row["delta_bits_vs_global"] > 0
    )
    control = random_control(rows)
    promotes = (
        best_feature["delta_bits_vs_global"] > control["best_delta_bits_p95"]
        and best_feature["delta_exact_vs_global"] > control["best_delta_exact_p95"]
        and stable_positive_cells >= 3
    )
    weak = (
        not promotes
        and best_feature["delta_bits_vs_global"] > 0
        and best_feature["delta_exact_vs_global"] > 0
    )
    mode_counts = Counter(row["label"] for row in rows)
    summary = {
        "book_start_count": len(rows),
        "book_start_literals": mode_counts["literal"],
        "book_start_copies": mode_counts["copy"],
        "best_global_cutoff": best_global["cutoff"],
        "best_global_exact_books": best_global["exact_books"],
        "best_global_test_books": best_global["test_books"],
        "best_global_saving_vs_lookup_bits": best_global["saving_vs_lookup_bits"],
        "best_feature": best_feature["feature"],
        "best_feature_cutoff": best_feature["cutoff"],
        "best_feature_exact_books": best_feature["exact_books"],
        "best_feature_test_books": best_feature["test_books"],
        "best_feature_literal_hits": best_feature["literal_hits"],
        "best_feature_copy_hits": best_feature["copy_hits"],
        "best_feature_saving_vs_lookup_bits": best_feature["saving_vs_lookup_bits"],
        "best_feature_delta_bits_vs_global": best_feature["delta_bits_vs_global"],
        "best_feature_delta_exact_vs_global": best_feature["delta_exact_vs_global"],
        "positive_feature_cells": positive_cells,
        "stable_positive_feature_cells": stable_positive_cells,
        "random_delta_bits_p95": control["best_delta_bits_p95"],
        "random_delta_exact_p95": control["best_delta_exact_p95"],
        "random_positive_cells_p95": control["positive_cells_p95"],
        "promotes_book_start_mode": promotes,
        "weak_book_start_mode": weak,
        "interpretation": (
            "This gate tests whether the promoted book-start clue can be refined "
            "into a target-free first-operation mode parser. A promotion requires "
            "a non-global feature to beat shuffled controls and remain positive "
            "beyond the unstable earliest split."
        ),
    }
    return {
        "schema": "book_start_mode_gate_v1",
        "scope": "analysis_only_target_free_book_start_mode_policy",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "internal_boundary_candidate_trigger_gate": rel(
                INTERNAL_BOUNDARY_CANDIDATE_TRIGGER_GATE
            ),
        },
        "rows": eval_rows,
        "random_control": control,
        "summary": summary,
        "classification": (
            "book_start_mode_policy_promoted"
            if promotes
            else (
                "book_start_mode_policy_weak_prefix_artifact"
                if weak
                else "book_start_mode_policy_rejected"
            )
        ),
        "decision": {
            "promotes_book_start_mode": promotes,
            "weak_book_start_mode": weak,
            "generator_status": "not_promoted",
            "book_start_mode_status": "not_promoted" if not promotes else "promoted",
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
        "# Book Start Mode Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether book-start operation mode (`literal` vs `copy`) has a",
        "target-free rule beyond global majority.",
        "",
        "## Summary",
        "",
        f"- Book starts: `{s['book_start_count']}`.",
        f"- Literal/copy starts: `{s['book_start_literals']}` / `{s['book_start_copies']}`.",
        f"- Best global exact books: `{s['best_global_exact_books']}/{s['best_global_test_books']}` at cutoff `{s['best_global_cutoff']}`.",
        f"- Best global saving vs mode lookup: `{s['best_global_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best feature: `{s['best_feature']}`.",
        f"- Best feature cutoff: `{s['best_feature_cutoff']}`.",
        f"- Best feature exact books: `{s['best_feature_exact_books']}/{s['best_feature_test_books']}`.",
        f"- Best feature literal/copy hits: `{s['best_feature_literal_hits']}` / `{s['best_feature_copy_hits']}`.",
        f"- Best feature saving vs lookup: `{s['best_feature_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best feature delta vs global: `{s['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Best feature exact delta vs global: `{s['best_feature_delta_exact_vs_global']}`.",
        f"- Positive feature cells: `{s['positive_feature_cells']}`.",
        f"- Stable positive feature cells: `{s['stable_positive_feature_cells']}`.",
        f"- Random delta bits p95: `{s['random_delta_bits_p95']:.3f}`.",
        f"- Random exact delta p95: `{s['random_delta_exact_p95']:.3f}`.",
        f"- Random positive cells p95: `{s['random_positive_cells_p95']:.3f}`.",
        f"- Promotes book-start mode: `{s['promotes_book_start_mode']}`.",
        f"- Weak book-start mode: `{s['weak_book_start_mode']}`.",
        "",
        s["interpretation"],
        "",
        "## Best Rows",
        "",
        "| Cutoff | Feature | Exact | Lit/Copy hits | Errors | Saving | Delta bits | Delta exact | Contexts |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(
        result["rows"],
        key=lambda item: (item["delta_bits_vs_global"], item["delta_exact_vs_global"]),
        reverse=True,
    )[:12]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['feature']}` | "
            f"`{row['exact_books']}/{row['test_books']}` | "
            f"`{row['literal_hits']}/{row['copy_hits']}` | "
            f"`{row['errors']}` | `{row['saving_vs_lookup_bits']:.3f}` | "
            f"`{row['delta_bits_vs_global']:.3f}` | "
            f"`{row['delta_exact_vs_global']}` | `{row['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- A book-start mode policy is promoted only if it beats shuffled controls and remains positive beyond the earliest unstable split.",
            "- Under current features, the apparent `book_mod10` improvement is not promoted as a stable mode parser.",
            "- The book-start clue remains structural: every derived book has a first operation, but its literal/copy mode remains externally declared.",
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
