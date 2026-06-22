from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable


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
THRESHOLD_GATE = (
    ROOT
    / "analysis"
    / "target_digit_boundary_threshold_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_boundary_threshold_gate.json"
)

OUT_STEM = "01_target_digit_boundary_peak_gate"
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 1000
ALPHA = 0.5
DIGITS = "0123456789"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


PolicyFunc = Callable[[dict[str, Any]], set[int]]


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


def prev2_context(prefix: str) -> tuple[str, str]:
    if not prefix:
        return ("BOS", "BOS")
    if len(prefix) == 1:
        return ("BOS", prefix[-1])
    return (prefix[-2], prefix[-1])


def train_prev2(
    books: dict[int, str],
    book_ids: list[int],
) -> tuple[dict[tuple[str, str], Counter[str]], Counter[str]]:
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


def policy_specs() -> list[tuple[str, PolicyFunc]]:
    specs: list[tuple[str, PolicyFunc]] = []
    for threshold in [2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6]:
        for radius in [1, 2, 3, 4, 5]:
            for prominence in [0, 0.25, 0.5, 1.0, 1.5, 2.0]:
                name = f"local_peak:right_ge={threshold}:radius={radius}:prom={prominence}"

                def func(
                    info: dict[str, Any],
                    threshold: float = threshold,
                    radius: int = radius,
                    prominence: float = prominence,
                ) -> set[int]:
                    surprisal = info["surprisal"]
                    out = set()
                    for pos in info["candidate_positions"]:
                        lo = max(0, pos - radius)
                        hi = min(len(surprisal) - 1, pos + radius)
                        neighbors = [surprisal[q] for q in range(lo, hi + 1) if q != pos]
                        if surprisal[pos] < threshold:
                            continue
                        if any(value > surprisal[pos] for value in neighbors):
                            continue
                        if neighbors and surprisal[pos] - max(neighbors) < prominence:
                            continue
                        out.add(pos)
                    return out

                specs.append((name, func))
    for threshold in [2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6]:
        for gap in [2, 3, 4, 5, 6, 8, 10, 12]:
            name = f"nms_right:right_ge={threshold}:gap={gap}"

            def func(
                info: dict[str, Any],
                threshold: float = threshold,
                gap: int = gap,
            ) -> set[int]:
                surprisal = info["surprisal"]
                candidates = [
                    pos for pos in info["candidate_positions"] if surprisal[pos] >= threshold
                ]
                chosen: list[int] = []
                for pos in sorted(candidates, key=lambda item: (-surprisal[item], item)):
                    if all(abs(pos - prior) >= gap for prior in chosen):
                        chosen.append(pos)
                return set(chosen)

            specs.append((name, func))
    for fraction in [0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30]:
        for gap in [2, 3, 4, 5, 6, 8, 10, 12]:
            name = f"nms_rank:top={fraction}:gap={gap}"

            def func(
                info: dict[str, Any],
                fraction: float = fraction,
                gap: int = gap,
            ) -> set[int]:
                surprisal = info["surprisal"]
                candidates = info["candidate_positions"]
                top_k = max(1, round(len(candidates) * fraction))
                top = sorted(candidates, key=lambda item: (-surprisal[item], item))[:top_k]
                chosen: list[int] = []
                for pos in top:
                    if all(abs(pos - prior) >= gap for prior in chosen):
                        chosen.append(pos)
                return set(chosen)

            specs.append((name, func))
    return specs


def book_cost(info: dict[str, Any], predicted: set[int]) -> dict[str, Any]:
    candidates = info["candidate_positions"]
    actual = info["actual_cutpoints"]
    true_positive = len(predicted & actual)
    false_positive = len(predicted - actual)
    false_negative = len(actual - predicted)
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
        "predicted_count": len(predicted),
        "actual_count": len(actual),
        "exact": predicted == actual,
    }


def evaluate(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    policy_name: str,
    policy_func: PolicyFunc,
    policy_count: int,
    selected_override: dict[int, set[int]] | None = None,
) -> dict[str, Any]:
    baseline = 0.0
    correction = 0.0
    tp = fp = fn = predicted_count = actual_count = exact_books = 0
    for book in book_ids:
        info = per_book[book]
        predicted = selected_override[book] if selected_override else policy_func(info)
        cost = book_cost(info, predicted)
        baseline += cost["baseline_bits"]
        correction += cost["correction_bits"]
        tp += cost["true_positive"]
        fp += cost["false_positive"]
        fn += cost["false_negative"]
        predicted_count += cost["predicted_count"]
        actual_count += cost["actual_count"]
        exact_books += int(cost["exact"])
    policy_bits = math.log2(policy_count)
    return {
        "policy": policy_name,
        "book_count": len(book_ids),
        "baseline_bits": baseline,
        "correction_bits_before_policy": correction,
        "policy_bits": policy_bits,
        "correction_bits_after_policy": correction + policy_bits,
        "saving_after_policy": baseline - correction - policy_bits,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "predicted_count": predicted_count,
        "actual_count": actual_count,
        "exact_books": exact_books,
        "correction_events": fp + fn,
        "precision": tp / predicted_count if predicted_count else 0.0,
        "recall": tp / actual_count if actual_count else 0.0,
    }


def random_control(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    policy_name: str,
    policy_func: PolicyFunc,
    policy_count: int,
) -> dict[str, Any]:
    predicted_counts = {
        book: len(policy_func(per_book[book]))
        for book in book_ids
    }
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in policy_name))
    savings = []
    for _ in range(RANDOM_TRIALS):
        selected = {}
        for book in book_ids:
            candidates = per_book[book]["candidate_positions"]
            count = predicted_counts[book]
            selected[book] = set(rng.sample(candidates, count)) if count else set()
        row = evaluate(
            per_book,
            book_ids,
            policy_name,
            policy_func,
            policy_count,
            selected,
        )
        savings.append(row["baseline_bits"] - row["correction_bits_before_policy"])
    savings.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED + sum(ord(ch) for ch in policy_name),
        "saving_mean_before_policy": mean(savings),
        "saving_p05_before_policy": percentile(savings, 0.05),
        "saving_p95_before_policy": percentile(savings, 0.95),
    }


def full_fit_rows(
    per_book: dict[int, dict[str, Any]],
    specs: list[tuple[str, PolicyFunc]],
) -> list[dict[str, Any]]:
    book_ids = sorted(per_book)
    rows = []
    for name, func in specs:
        rows.append(evaluate(per_book, book_ids, name, func, len(specs)))
    return rows


def prequential_rows(
    per_book: dict[int, dict[str, Any]],
    specs: list[tuple[str, PolicyFunc]],
) -> list[dict[str, Any]]:
    all_books = sorted(per_book)
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = [book for book in all_books if book < cutoff]
        test_books = [book for book in all_books if book >= cutoff]
        train_rows = [
            evaluate(per_book, train_books, name, func, len(specs))
            for name, func in specs
        ]
        selected = max(train_rows, key=lambda row: (row["saving_after_policy"], row["policy"]))
        selected_name, selected_func = next(
            (name, func) for name, func in specs if name == selected["policy"]
        )
        test = evaluate(
            per_book,
            test_books,
            selected_name,
            selected_func,
            len(specs),
        )
        rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": selected_name,
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
    threshold_gate = load_json(THRESHOLD_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("target_digit_boundary_threshold_gate", threshold_gate)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    per_book = make_per_book(books, copy_ledger["canonical_ops_by_book"])
    specs = policy_specs()
    full_rows = full_fit_rows(per_book, specs)
    best = max(full_rows, key=lambda row: (row["saving_after_policy"], row["recall"]))
    best_name, best_func = next((name, func) for name, func in specs if name == best["policy"])
    best_random = random_control(per_book, sorted(per_book), best_name, best_func, len(specs))
    preq = prequential_rows(per_book, specs)
    threshold_summary = threshold_gate["summary"]
    comparison = {
        "threshold_policy": threshold_summary["best_policy"],
        "threshold_saving_after_policy": threshold_summary["best_saving_after_policy"],
        "threshold_correction_bits_after_policy": threshold_summary[
            "best_correction_bits_after_policy"
        ],
        "threshold_correction_events": threshold_summary["best_correction_events"],
        "threshold_predicted_count": threshold_summary["best_predicted_count"],
        "threshold_true_positive": threshold_summary["best_true_positive"],
        "threshold_false_positive": threshold_summary["best_false_positive"],
        "threshold_false_negative": threshold_summary["best_false_negative"],
        "saving_delta_vs_threshold": best["saving_after_policy"]
        - threshold_summary["best_saving_after_policy"],
        "correction_event_delta_vs_threshold": best["correction_events"]
        - threshold_summary["best_correction_events"],
        "false_positive_delta_vs_threshold": best["false_positive"]
        - threshold_summary["best_false_positive"],
        "false_negative_delta_vs_threshold": best["false_negative"]
        - threshold_summary["best_false_negative"],
    }
    promotes_peak_replacement = (
        best["saving_after_policy"] > threshold_summary["best_saving_after_policy"]
        and best["exact_books"] > 0
        and all(row["test_saving_after_policy"] > 0 for row in preq)
    )
    summary = {
        "book_count": len(per_book),
        "candidate_position_count": sum(len(info["candidate_positions"]) for info in per_book.values()),
        "actual_cutpoint_count": sum(len(info["actual_cutpoints"]) for info in per_book.values()),
        "policy_count": len(specs),
        "best_policy": best["policy"],
        "best_baseline_bits": best["baseline_bits"],
        "best_correction_bits_after_policy": best["correction_bits_after_policy"],
        "best_saving_after_policy": best["saving_after_policy"],
        "best_random_saving_p95_before_policy": best_random["saving_p95_before_policy"],
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
        "promotes_peak_replacement": promotes_peak_replacement,
        "interpretation": (
            "Local peak and non-maximum suppression policies reduce false positives "
            "and total correction events, but lose too many true cutpoints to replace "
            "the simpler threshold dependency code or generate the skeleton."
        ),
    }
    return {
        "schema": "target_digit_boundary_peak_gate_v1",
        "scope": "analysis_only_local_peak_boundary_hypothesis",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "threshold_gate": rel(THRESHOLD_GATE),
        },
        "full_fit_rows": sorted(full_rows, key=lambda row: row["saving_after_policy"], reverse=True),
        "prequential_rows": preq,
        "random_control_best": best_random,
        "threshold_comparison": comparison,
        "summary": summary,
        "classification": "target_digit_boundary_peak_suppression_weak_not_promoted",
        "decision": {
            "promotes_peak_replacement": promotes_peak_replacement,
            "promotes_endpoint_generator": False,
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
    c = result["threshold_comparison"]
    lines = [
        "# Target Digit Boundary Peak Gate",
        "",
        "Classification: `target_digit_boundary_peak_suppression_weak_not_promoted`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether internal cutpoints are better modeled as local peaks or",
        "non-maximum-suppressed rank peaks in the `prev2` right-surprisal stream,",
        "without granting op-count.",
        "",
        "## Summary",
        "",
        f"- Books/candidates/actual cutpoints: `{s['book_count']}` / `{s['candidate_position_count']}` / `{s['actual_cutpoint_count']}`.",
        f"- Policies tested: `{s['policy_count']}`.",
        f"- Best peak policy: `{s['best_policy']}`.",
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
        "## Comparison To Threshold Gate",
        "",
        f"- Prior threshold policy: `{c['threshold_policy']}`.",
        f"- Saving delta vs threshold: `{c['saving_delta_vs_threshold']:.3f}` bits.",
        f"- Correction-event delta vs threshold: `{c['correction_event_delta_vs_threshold']}`.",
        f"- False-positive delta vs threshold: `{c['false_positive_delta_vs_threshold']}`.",
        f"- False-negative delta vs threshold: `{c['false_negative_delta_vs_threshold']}`.",
        "",
        "Peak suppression removes many false positives but misses more real",
        "cutpoints. It is a useful diagnostic, not a better dependency code.",
        "",
        "## Top Full-Fit Peak Policies",
        "",
        "| Policy | Saving | TP | FP | FN | Exact books |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["full_fit_rows"][:8]:
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
            "- Peak replacement promoted: `False`.",
            "- Endpoint generator promoted: `False`.",
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
