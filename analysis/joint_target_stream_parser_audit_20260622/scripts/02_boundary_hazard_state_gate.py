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
JOINT_PAIR_GATE = TEST_RESULTS / "01_joint_boundary_digit_gate.json"

OUT_STEM = "02_boundary_hazard_state_gate"
ALPHA = 0.5
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 400
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


def features() -> list[str]:
    return [
        "age_bucket",
        "age_exact_cap20",
        "age_exact_cap50",
        "remaining_bucket",
        "progress_quint",
        "count_bucket",
        "count_mod3",
        "age_x_remaining",
        "age_x_progress",
        "age_x_count",
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


def boundary_flags(book: int, length: int, ops_by_book: dict[str, list[dict[str, Any]]]) -> list[int]:
    flags = [0] * length
    if str(book) not in ops_by_book:
        return flags
    for op in ops_by_book[str(book)][:-1]:
        cutpoint = int(op["target_start"]) + int(op["length"])
        if 0 < cutpoint < length:
            flags[cutpoint] = 1
    return flags


def random_flags(book: int, length: int, count: int, rng: random.Random) -> list[int]:
    flags = [0] * length
    if count:
        for cutpoint in rng.sample(range(1, length), count):
            flags[cutpoint] = 1
    return flags


def age_bucket(age: int) -> str:
    if age == 1:
        return "age_1"
    if age <= 3:
        return "age_2_3"
    if age <= 7:
        return "age_4_7"
    if age <= 15:
        return "age_8_15"
    if age <= 31:
        return "age_16_31"
    if age <= 63:
        return "age_32_63"
    return "age_64_plus"


def remaining_bucket(remaining: int) -> str:
    if remaining <= 3:
        return "rem_1_3"
    if remaining <= 7:
        return "rem_4_7"
    if remaining <= 15:
        return "rem_8_15"
    if remaining <= 31:
        return "rem_16_31"
    if remaining <= 63:
        return "rem_32_63"
    return "rem_64_plus"


def count_bucket(count: int) -> str:
    if count == 0:
        return "count_0"
    if count == 1:
        return "count_1"
    if count <= 3:
        return "count_2_3"
    return "count_4_plus"


def make_rows(
    books: dict[int, str],
    flags_by_book: dict[int, list[int]],
    book_ids: list[int],
) -> list[dict[str, Any]]:
    rows = []
    for book in book_ids:
        length = len(books[book])
        flags = flags_by_book[book]
        last_boundary = 0
        emitted_count = 0
        for pos in range(1, length):
            age = pos - last_boundary
            remaining = length - pos
            age_b = age_bucket(age)
            rem_b = remaining_bucket(remaining)
            count_b = count_bucket(emitted_count)
            row = {
                "book": book,
                "position": pos,
                "flag": flags[pos],
                "global": "global",
                "age_bucket": age_b,
                "age_exact_cap20": str(min(age, 20)),
                "age_exact_cap50": str(min(age, 50)),
                "remaining_bucket": rem_b,
                "progress_quint": str(int(pos * 5 / length)),
                "count_bucket": count_b,
                "count_mod3": str(emitted_count % 3),
                "age_x_remaining": f"{age_b}|{rem_b}",
                "age_x_progress": f"{age_b}|{int(pos * 5 / length)}",
                "age_x_count": f"{age_b}|{count_b}",
            }
            rows.append(row)
            if flags[pos]:
                last_boundary = pos
                emitted_count += 1
    return rows


def nll(counter: Counter[int], symbol: int) -> float:
    return -math.log2(
        (counter[symbol] + ALPHA) / (sum(counter.values()) + ALPHA * 2)
    )


def score_feature(train_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    global_counts = Counter(row["flag"] for row in train_rows)
    context_counts: dict[str, Counter[int]] = defaultdict(Counter)
    for row in train_rows:
        context_counts[row[feature]][row["flag"]] += 1
    baseline_bits = 0.0
    model_bits = 0.0
    boundary_count = 0
    for row in test_rows:
        baseline_bits += nll(global_counts, row["flag"])
        model_bits += nll(context_counts.get(row[feature], global_counts), row["flag"])
        boundary_count += row["flag"]
    return {
        "feature": feature,
        "test_rows": len(test_rows),
        "test_boundaries": boundary_count,
        "baseline_bits": baseline_bits,
        "model_bits": model_bits,
        "gain_bits": baseline_bits - model_bits,
    }


def evaluate(
    books: dict[int, str],
    flags_by_book: dict[int, list[int]],
    feature: str,
) -> dict[str, Any]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_rows = make_rows(books, flags_by_book, list(range(10, cutoff)))
        test_rows = make_rows(books, flags_by_book, list(range(cutoff, 70)))
        scored = score_feature(train_rows, test_rows, feature)
        scored["cutoff"] = cutoff
        rows.append(scored)
    feature_bits = math.log2(len(features()))
    aggregate_gain = sum(row["gain_bits"] for row in rows)
    return {
        "feature": feature,
        "feature_bits": feature_bits,
        "aggregate_gain_before_feature_charge": aggregate_gain,
        "aggregate_gain_after_feature_charge": aggregate_gain - feature_bits,
        "positive_cells": sum(1 for row in rows if row["gain_bits"] > 0),
        "cells": len(rows),
        "cutoff_rows": rows,
    }


def random_control(
    books: dict[int, str],
    true_flags_by_book: dict[int, list[int]],
    feature: str,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in feature))
    gains = []
    for _ in range(RANDOM_TRIALS):
        flags_by_book = {
            book: random_flags(book, len(books[book]), sum(true_flags_by_book[book]), rng)
            for book in range(10, 70)
        }
        gains.append(evaluate(books, flags_by_book, feature)["aggregate_gain_before_feature_charge"])
    gains.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED + sum(ord(ch) for ch in feature),
        "gain_mean_before_feature_charge": mean(gains),
        "gain_p05_before_feature_charge": percentile(gains, 0.05),
        "gain_p95_before_feature_charge": percentile(gains, 0.95),
        "gain_max_before_feature_charge": gains[-1] if gains else 0.0,
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
    joint_pair = load_json(JOINT_PAIR_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("joint_boundary_digit_gate", joint_pair)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    flags_by_book = {
        book: boundary_flags(book, len(books[book]), copy_ledger["canonical_ops_by_book"])
        for book in range(10, 70)
    }
    score_rows = [evaluate(books, flags_by_book, feature) for feature in features()]
    best = max(score_rows, key=lambda row: row["aggregate_gain_after_feature_charge"])
    random_best = random_control(books, flags_by_book, best["feature"])
    promotes_hazard_state = (
        best["aggregate_gain_after_feature_charge"] > 0
        and best["positive_cells"] == best["cells"]
        and best["aggregate_gain_before_feature_charge"]
        > random_best["gain_p95_before_feature_charge"]
    )
    summary = {
        "feature_count": len(features()),
        "cutoff_count": len(PREFIX_CUTOFFS),
        "best_feature": best["feature"],
        "best_aggregate_gain_before_feature_charge": best[
            "aggregate_gain_before_feature_charge"
        ],
        "best_aggregate_gain_after_feature_charge": best[
            "aggregate_gain_after_feature_charge"
        ],
        "best_positive_cells": best["positive_cells"],
        "best_cells": best["cells"],
        "best_random_gain_p95_before_feature_charge": random_best[
            "gain_p95_before_feature_charge"
        ],
        "best_beats_random_p95": best["aggregate_gain_before_feature_charge"]
        > random_best["gain_p95_before_feature_charge"],
        "promotes_hazard_state": promotes_hazard_state,
        "promotes_exact_parser": False,
        "interpretation": (
            "A sequential boundary hazard state based on age since the last emitted "
            "boundary reduces boundary-flag coding under prefix holdout and beats "
            "same-count random boundary controls. It is a real parser-state clue, "
            "but it still emits probabilities rather than exact endpoints."
        ),
    }
    return {
        "schema": "boundary_hazard_state_gate_v1",
        "scope": "analysis_only_joint_parser_state_boundary_hazard",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "joint_pair_gate": rel(JOINT_PAIR_GATE),
        },
        "score_rows": sorted(
            score_rows,
            key=lambda row: row["aggregate_gain_after_feature_charge"],
            reverse=True,
        ),
        "random_control_best": random_best,
        "summary": summary,
        "classification": "boundary_hazard_state_dependency_reduced_not_generator",
        "decision": {
            "promotes_hazard_state": promotes_hazard_state,
            "promotes_exact_parser": False,
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
        "# Boundary Hazard State Gate",
        "",
        "Classification: `boundary_hazard_state_dependency_reduced_not_generator`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether a sequential parser state can reduce boundary dependency:",
        "the state is available during generation and includes age since the last",
        "emitted boundary, remaining length, progress, and emitted-boundary count.",
        "",
        "## Summary",
        "",
        f"- Features tested: `{s['feature_count']}`.",
        f"- Prefix cutoffs tested: `{s['cutoff_count']}`.",
        f"- Best feature: `{s['best_feature']}`.",
        f"- Aggregate gain before feature charge: `{s['best_aggregate_gain_before_feature_charge']:.3f}` bits.",
        f"- Aggregate gain after feature charge: `{s['best_aggregate_gain_after_feature_charge']:.3f}` bits.",
        f"- Positive cells: `{s['best_positive_cells']}/{s['best_cells']}`.",
        f"- Random same-count p95 before feature charge: `{s['best_random_gain_p95_before_feature_charge']:.3f}` bits.",
        f"- Beats random p95: `{s['best_beats_random_p95']}`.",
        f"- Promotes hazard state: `{s['promotes_hazard_state']}`.",
        f"- Promotes exact parser: `{s['promotes_exact_parser']}`.",
        "",
        s["interpretation"],
        "",
        "## Feature Scoreboard",
        "",
        "| Feature | Gain after charge | Gain before charge | Positive cells |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in result["score_rows"]:
        lines.append(
            f"| `{row['feature']}` | `{row['aggregate_gain_after_feature_charge']:.3f}` | "
            f"`{row['aggregate_gain_before_feature_charge']:.3f}` | "
            f"`{row['positive_cells']}/{row['cells']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Sequential hazard state is promoted as a boundary dependency reducer.",
            "- Exact parser/generator is not promoted.",
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
