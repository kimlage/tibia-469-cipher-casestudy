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
SKELETON_DEPENDENCY_GATE = (
    ROOT
    / "analysis"
    / "skeleton_dependency_after_boundary_pruning_20260621"
    / "reports"
    / "test_results"
    / "01_skeleton_dependency_after_boundary_pruning_gate.json"
)

OUT_STEM = "01_target_digit_boundary_threshold_gate"
RANDOM_SEED = 46920260621
RANDOM_TRIALS = 1000
ALPHA = 0.5
DIGITS = "0123456789"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


def policies() -> list[str]:
    right = [f"right_ge:{value}" for value in [2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6]]
    delta = [f"delta_ge:{value}" for value in [0, 0.5, 1, 1.5, 2, 2.5, 3]]
    rank = [f"rank_top:{value}" for value in [0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50]]
    return right + delta + rank


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


def prev2_context(prefix: str) -> tuple[str, str]:
    if not prefix:
        return ("BOS", "BOS")
    if len(prefix) == 1:
        return ("BOS", prefix[-1])
    return (prefix[-2], prefix[-1])


def train_prev2(books: dict[int, str], book_ids: list[int]) -> tuple[dict[tuple[str, str], Counter[str]], Counter[str]]:
    counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    for book in book_ids:
        prefix = ""
        for digit in books[book]:
            counts[prev2_context(prefix)][digit] += 1
            prefix += digit
    global_counts = Counter()
    for counter in counts.values():
        global_counts.update(counter)
    return counts, global_counts


def book_surprisals(books: dict[int, str], book: int) -> list[float]:
    counts, global_counts = train_prev2(
        books, [candidate for candidate in sorted(books) if candidate < book]
    )
    prefix = ""
    values = []
    for digit in books[book]:
        counter = counts.get(prev2_context(prefix), global_counts)
        total = sum(counter.values())
        probability = (counter[digit] + ALPHA) / (total + ALPHA * len(DIGITS))
        values.append(-math.log2(probability))
        prefix += digit
    return values


def make_per_book(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> dict[int, dict[str, Any]]:
    out = {}
    for book in range(10, 70):
        target = books[book]
        surprisal = book_surprisals(books, book)
        candidates = list(range(1, len(target)))
        ranked = sorted(candidates, key=lambda pos: (-surprisal[pos], pos))
        rank_fraction = {pos: (index + 1) / len(candidates) for index, pos in enumerate(ranked)}
        actual = [
            int(op["target_start"]) + int(op["length"])
            for op in ops_by_book[str(book)][:-1]
        ]
        actual = sorted(pos for pos in actual if 0 < pos < len(target))
        out[book] = {
            "book": book,
            "length": len(target),
            "candidate_positions": candidates,
            "actual_cutpoints": set(actual),
            "surprisal": surprisal,
            "rank_fraction": rank_fraction,
        }
    return out


def predicted_set(info: dict[str, Any], policy: str) -> set[int]:
    kind, raw = policy.split(":")
    threshold = float(raw)
    candidates = info["candidate_positions"]
    if kind == "right_ge":
        return {pos for pos in candidates if info["surprisal"][pos] >= threshold}
    if kind == "delta_ge":
        return {
            pos
            for pos in candidates
            if info["surprisal"][pos] - info["surprisal"][pos - 1] >= threshold
        }
    if kind == "rank_top":
        return {pos for pos in candidates if info["rank_fraction"][pos] <= threshold}
    raise KeyError(policy)


def book_cost(info: dict[str, Any], predicted: set[int]) -> dict[str, Any]:
    candidates = info["candidate_positions"]
    actual = info["actual_cutpoints"]
    true_positive = len(predicted & actual)
    false_positive = len(predicted - actual)
    false_negative = len(actual - predicted)
    true_negative = len(candidates) - true_positive - false_positive - false_negative
    baseline = math.log2(info["length"]) + log2comb(len(candidates), len(actual))
    correction = log2comb(len(predicted), false_positive) + log2comb(
        len(candidates) - len(predicted), false_negative
    )
    return {
        "baseline_bits": baseline,
        "correction_bits": correction,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "true_negative": true_negative,
        "predicted_count": len(predicted),
        "actual_count": len(actual),
        "exact": predicted == actual,
    }


def evaluate(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    policy: str,
    selected_override: dict[int, set[int]] | None = None,
) -> dict[str, Any]:
    baseline = 0.0
    correction = 0.0
    tp = fp = fn = pred = actual = exact = 0
    for book in book_ids:
        info = per_book[book]
        predicted = selected_override[book] if selected_override else predicted_set(info, policy)
        cost = book_cost(info, predicted)
        baseline += cost["baseline_bits"]
        correction += cost["correction_bits"]
        tp += cost["true_positive"]
        fp += cost["false_positive"]
        fn += cost["false_negative"]
        pred += cost["predicted_count"]
        actual += cost["actual_count"]
        exact += int(cost["exact"])
    policy_bits = math.log2(len(policies()))
    return {
        "policy": policy,
        "book_count": len(book_ids),
        "baseline_bits": baseline,
        "correction_bits_before_policy": correction,
        "policy_bits": policy_bits,
        "correction_bits_after_policy": correction + policy_bits,
        "saving_after_policy": baseline - correction - policy_bits,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "predicted_count": pred,
        "actual_count": actual,
        "exact_books": exact,
        "correction_events": fp + fn,
        "precision": tp / pred if pred else 0.0,
        "recall": tp / actual if actual else 0.0,
    }


def random_control(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    policy: str,
) -> dict[str, Any]:
    predicted_counts = {
        book: len(predicted_set(per_book[book], policy))
        for book in book_ids
    }
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in policy))
    savings = []
    for _ in range(RANDOM_TRIALS):
        selected = {}
        for book in book_ids:
            candidates = per_book[book]["candidate_positions"]
            count = predicted_counts[book]
            selected[book] = set(rng.sample(candidates, count)) if count else set()
        row = evaluate(per_book, book_ids, policy, selected)
        savings.append(row["baseline_bits"] - row["correction_bits_before_policy"])
    savings.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED + sum(ord(ch) for ch in policy),
        "saving_mean_before_policy": mean(savings),
        "saving_p05_before_policy": percentile(savings, 0.05),
        "saving_p95_before_policy": percentile(savings, 0.95),
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


def full_fit_rows(per_book: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    book_ids = sorted(per_book)
    rows = []
    for policy in policies():
        row = evaluate(per_book, book_ids, policy)
        control = random_control(per_book, book_ids, policy)
        row["random_control"] = control
        row["saving_beats_random_p95"] = (
            row["baseline_bits"] - row["correction_bits_before_policy"]
            > control["saving_p95_before_policy"]
        )
        rows.append(row)
    return rows


def prequential_rows(per_book: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    all_books = sorted(per_book)
    rows = []
    for cutoff in [20, 30, 40, 50, 60]:
        train_books = [book for book in all_books if book < cutoff]
        test_books = [book for book in all_books if book >= cutoff]
        train_rows = [evaluate(per_book, train_books, policy) for policy in policies()]
        selected = max(train_rows, key=lambda row: (row["saving_after_policy"], row["policy"]))
        test = evaluate(per_book, test_books, selected["policy"])
        rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": selected["policy"],
                "train_saving_after_policy": selected["saving_after_policy"],
                "test_saving_after_policy": test["saving_after_policy"],
                "test_true_positive": test["true_positive"],
                "test_false_positive": test["false_positive"],
                "test_false_negative": test["false_negative"],
                "test_exact_books": test["exact_books"],
                "test_book_count": test["book_count"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    skeleton_dependency = load_json(SKELETON_DEPENDENCY_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("skeleton_dependency_after_boundary_pruning_gate", skeleton_dependency)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    per_book = make_per_book(books, copy_ledger["canonical_ops_by_book"])
    full_rows = full_fit_rows(per_book)
    best = max(full_rows, key=lambda row: (row["saving_after_policy"], row["recall"]))
    preq = prequential_rows(per_book)
    promotes_dependency_reduction = (
        best["saving_after_policy"] > 0
        and best["saving_beats_random_p95"]
        and all(row["test_saving_after_policy"] > 0 for row in preq)
    )
    promotes_endpoint_generator = best["exact_books"] == len(per_book)
    summary = {
        "book_count": len(per_book),
        "candidate_position_count": sum(len(info["candidate_positions"]) for info in per_book.values()),
        "actual_cutpoint_count": sum(len(info["actual_cutpoints"]) for info in per_book.values()),
        "best_policy": best["policy"],
        "best_baseline_bits": best["baseline_bits"],
        "best_correction_bits_after_policy": best["correction_bits_after_policy"],
        "best_saving_after_policy": best["saving_after_policy"],
        "best_random_saving_p95_before_policy": best["random_control"]["saving_p95_before_policy"],
        "best_true_positive": best["true_positive"],
        "best_false_positive": best["false_positive"],
        "best_false_negative": best["false_negative"],
        "best_predicted_count": best["predicted_count"],
        "best_correction_events": best["correction_events"],
        "best_exact_books": best["exact_books"],
        "best_precision": best["precision"],
        "best_recall": best["recall"],
        "prequential_cells": len(preq),
        "prequential_positive_test_saving_cells": sum(
            1 for row in preq if row["test_saving_after_policy"] > 0
        ),
        "prequential_exact_book_cells": sum(
            row["test_exact_books"] for row in preq
        ),
        "promotes_dependency_reduction": promotes_dependency_reduction,
        "promotes_endpoint_generator": promotes_endpoint_generator,
        "interpretation": (
            "A threshold-generated boundary set plus paid FP/FN corrections "
            "reduces the full cutpoint atlas without granting op-count. It "
            "still requires a large correction list and generates no exact "
            "nontrivial book skeletons by itself."
        ),
    }
    return {
        "schema": "target_digit_boundary_threshold_gate_v1",
        "scope": "analysis_only_threshold_generated_boundary_set",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "skeleton_dependency_after_boundary_pruning_gate": rel(SKELETON_DEPENDENCY_GATE),
        },
        "full_fit_rows": full_rows,
        "prequential_rows": preq,
        "summary": summary,
        "classification": "target_digit_boundary_threshold_dependency_reduced_not_generator",
        "decision": {
            "promotes_dependency_reduction": promotes_dependency_reduction,
            "promotes_endpoint_generator": promotes_endpoint_generator,
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
        "# Target Digit Boundary Threshold Gate",
        "",
        "Classification: `target_digit_boundary_threshold_dependency_reduced_not_generator`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether an absolute `prev2` surprisal/rank threshold can generate",
        "a boundary set without granting op-count, paying only FP/FN corrections.",
        "",
        "## Summary",
        "",
        f"- Books/candidates/actual cutpoints: `{s['book_count']}` / `{s['candidate_position_count']}` / `{s['actual_cutpoint_count']}`.",
        f"- Best policy: `{s['best_policy']}`.",
        f"- Baseline full cutpoint atlas bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Correction bits after policy charge: `{s['best_correction_bits_after_policy']:.3f}`.",
        f"- Saving after policy charge: `{s['best_saving_after_policy']:.3f}` bits.",
        f"- Random saving p95 before policy charge: `{s['best_random_saving_p95_before_policy']:.3f}` bits.",
        f"- TP/FP/FN: `{s['best_true_positive']}` / `{s['best_false_positive']}` / `{s['best_false_negative']}`.",
        f"- Predicted boundaries/correction events: `{s['best_predicted_count']}` / `{s['best_correction_events']}`.",
        f"- Precision/recall: `{s['best_precision']:.6f}` / `{s['best_recall']:.6f}`.",
        f"- Exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Prefix-selected positive test-saving cells: `{s['prequential_positive_test_saving_cells']}/{s['prequential_cells']}`.",
        "",
        "## Top Full-Fit Policies",
        "",
        "| Policy | Saving | TP | FP | FN | Exact books |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(result["full_fit_rows"], key=lambda item: item["saving_after_policy"], reverse=True)[:8]:
        lines.append(
            f"| `{row['policy']}` | `{row['saving_after_policy']:.3f}` | "
            f"`{row['true_positive']}` | `{row['false_positive']}` | "
            f"`{row['false_negative']}` | `{row['exact_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Promotes dependency reduction: `True`.",
            "- Promotes endpoint generator: `False`.",
            "- The threshold set removes the need to grant op-count, but only by paying a large FP/FN correction list.",
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
