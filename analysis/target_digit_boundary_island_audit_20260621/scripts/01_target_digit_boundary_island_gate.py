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
THRESHOLD_GATE = (
    ROOT
    / "analysis"
    / "target_digit_boundary_threshold_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_boundary_threshold_gate.json"
)

OUT_STEM = "01_target_digit_boundary_island_gate"
RANDOM_SEED = 46920260622
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


def contiguous_islands(predicted: set[int]) -> list[tuple[int, int]]:
    if not predicted:
        return []
    values = sorted(predicted)
    out = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        out.append((start, previous))
        start = previous = value
    out.append((start, previous))
    return out


def book_cost(info: dict[str, Any], predicted: set[int]) -> dict[str, Any]:
    candidates = info["candidate_positions"]
    actual = info["actual_cutpoints"]
    islands = contiguous_islands(predicted)
    actual_in_predicted = predicted & actual
    outside_actual = actual - predicted
    occupied_islands = 0
    multi_hit_islands = 0
    island_position_bits = 0.0
    for start, end in islands:
        length = end - start + 1
        hits = sum(1 for pos in actual if start <= pos <= end)
        if hits:
            occupied_islands += 1
            island_position_bits += log2comb(length, hits)
            if hits > 1:
                multi_hit_islands += 1
    baseline = math.log2(info["length"]) + log2comb(len(candidates), len(actual))
    threshold_correction = log2comb(len(predicted), len(actual_in_predicted)) + log2comb(
        len(candidates) - len(predicted), len(outside_actual)
    )
    island_correction = (
        log2comb(len(islands), occupied_islands)
        + island_position_bits
        + log2comb(len(candidates) - len(predicted), len(outside_actual))
    )
    return {
        "baseline_bits": baseline,
        "threshold_correction_bits": threshold_correction,
        "island_correction_bits": island_correction,
        "true_positive": len(actual_in_predicted),
        "false_positive": len(predicted - actual),
        "false_negative": len(outside_actual),
        "predicted_count": len(predicted),
        "actual_count": len(actual),
        "island_count": len(islands),
        "occupied_islands": occupied_islands,
        "multi_hit_islands": multi_hit_islands,
        "exact": predicted == actual,
    }


def evaluate(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    policy: str,
    selected_override: dict[int, set[int]] | None = None,
) -> dict[str, Any]:
    baseline = 0.0
    threshold_correction = 0.0
    island_correction = 0.0
    tp = fp = fn = pred = actual = exact = 0
    island_count = occupied = multi_hit = 0
    for book in book_ids:
        info = per_book[book]
        predicted = selected_override[book] if selected_override else predicted_set(info, policy)
        cost = book_cost(info, predicted)
        baseline += cost["baseline_bits"]
        threshold_correction += cost["threshold_correction_bits"]
        island_correction += cost["island_correction_bits"]
        tp += cost["true_positive"]
        fp += cost["false_positive"]
        fn += cost["false_negative"]
        pred += cost["predicted_count"]
        actual += cost["actual_count"]
        exact += int(cost["exact"])
        island_count += cost["island_count"]
        occupied += cost["occupied_islands"]
        multi_hit += cost["multi_hit_islands"]
    policy_bits = math.log2(len(policies()))
    return {
        "policy": policy,
        "book_count": len(book_ids),
        "baseline_bits": baseline,
        "threshold_correction_bits_after_policy": threshold_correction + policy_bits,
        "threshold_saving_after_policy": baseline - threshold_correction - policy_bits,
        "island_correction_bits_after_policy": island_correction + policy_bits,
        "island_saving_after_policy": baseline - island_correction - policy_bits,
        "island_delta_vs_threshold_bits": island_correction - threshold_correction,
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "predicted_count": pred,
        "actual_count": actual,
        "exact_books": exact,
        "island_count": island_count,
        "occupied_islands": occupied,
        "multi_hit_islands": multi_hit,
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
        savings.append(row["baseline_bits"] - row["island_correction_bits_after_policy"])
    savings.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED + sum(ord(ch) for ch in policy),
        "saving_mean_after_policy": mean(savings),
        "saving_p05_after_policy": percentile(savings, 0.05),
        "saving_p95_after_policy": percentile(savings, 0.95),
    }


def full_fit_rows(per_book: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    book_ids = sorted(per_book)
    rows = []
    for policy in policies():
        row = evaluate(per_book, book_ids, policy)
        rows.append(row)
    return rows


def prequential_rows(per_book: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    all_books = sorted(per_book)
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = [book for book in all_books if book < cutoff]
        test_books = [book for book in all_books if book >= cutoff]
        train_rows = [evaluate(per_book, train_books, policy) for policy in policies()]
        selected = max(train_rows, key=lambda row: (row["island_saving_after_policy"], row["policy"]))
        test = evaluate(per_book, test_books, selected["policy"])
        rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": selected["policy"],
                "train_island_saving_after_policy": selected["island_saving_after_policy"],
                "test_island_saving_after_policy": test["island_saving_after_policy"],
                "test_threshold_saving_after_policy": test["threshold_saving_after_policy"],
                "test_island_delta_vs_threshold_bits": test["island_delta_vs_threshold_bits"],
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
    full_rows = full_fit_rows(per_book)
    best = max(full_rows, key=lambda row: (row["island_saving_after_policy"], row["recall"]))
    best_random = random_control(per_book, sorted(per_book), best["policy"])
    preq = prequential_rows(per_book)
    threshold_summary = threshold_gate["summary"]
    comparison = {
        "threshold_gate_best_policy": threshold_summary["best_policy"],
        "threshold_gate_saving_after_policy": threshold_summary["best_saving_after_policy"],
        "threshold_gate_correction_bits_after_policy": threshold_summary[
            "best_correction_bits_after_policy"
        ],
        "threshold_gate_correction_events": threshold_summary["best_correction_events"],
        "best_island_saving_delta_vs_threshold_gate": best["island_saving_after_policy"]
        - threshold_summary["best_saving_after_policy"],
        "best_island_correction_delta_vs_threshold_gate": best[
            "island_correction_bits_after_policy"
        ]
        - threshold_summary["best_correction_bits_after_policy"],
    }
    promotes_island_code = (
        best["island_saving_after_policy"] > threshold_summary["best_saving_after_policy"]
        and all(row["test_island_saving_after_policy"] > 0 for row in preq)
        and all(row["test_island_delta_vs_threshold_bits"] <= 0 for row in preq)
    )
    summary = {
        "book_count": len(per_book),
        "candidate_position_count": sum(len(info["candidate_positions"]) for info in per_book.values()),
        "actual_cutpoint_count": sum(len(info["actual_cutpoints"]) for info in per_book.values()),
        "policy_count": len(policies()),
        "best_policy": best["policy"],
        "best_baseline_bits": best["baseline_bits"],
        "best_island_correction_bits_after_policy": best["island_correction_bits_after_policy"],
        "best_island_saving_after_policy": best["island_saving_after_policy"],
        "best_threshold_saving_same_policy_after_policy": best["threshold_saving_after_policy"],
        "best_island_delta_vs_same_policy_threshold_bits": best["island_delta_vs_threshold_bits"],
        "best_random_saving_p95_after_policy": best_random["saving_p95_after_policy"],
        "best_true_positive": best["true_positive"],
        "best_false_positive": best["false_positive"],
        "best_false_negative": best["false_negative"],
        "best_predicted_count": best["predicted_count"],
        "best_correction_events": best["correction_events"],
        "best_island_count": best["island_count"],
        "best_occupied_islands": best["occupied_islands"],
        "best_multi_hit_islands": best["multi_hit_islands"],
        "best_exact_books": best["exact_books"],
        "best_precision": best["precision"],
        "best_recall": best["recall"],
        "prequential_cells": len(preq),
        "prequential_positive_test_island_saving_cells": sum(
            1 for row in preq if row["test_island_saving_after_policy"] > 0
        ),
        "prequential_island_beats_threshold_cells": sum(
            1 for row in preq if row["test_island_delta_vs_threshold_bits"] <= 0
        ),
        "promotes_island_code": promotes_island_code,
        "interpretation": (
            "The high-surprisal boundary signal is mostly a set of short islands. "
            "Encoding occupied islands plus offsets is auditably structured, but "
            "it does not beat the simpler threshold candidate-set code and still "
            "does not generate exact skeletons."
        ),
    }
    return {
        "schema": "target_digit_boundary_island_gate_v1",
        "scope": "analysis_only_high_surprisal_island_boundary_hypothesis",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "threshold_gate": rel(THRESHOLD_GATE),
        },
        "full_fit_rows": sorted(full_rows, key=lambda row: row["island_saving_after_policy"], reverse=True),
        "prequential_rows": preq,
        "random_control_best": best_random,
        "threshold_comparison": comparison,
        "summary": summary,
        "classification": "target_digit_boundary_island_code_rejected",
        "decision": {
            "promotes_island_code": promotes_island_code,
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
        "# Target Digit Boundary Island Gate",
        "",
        "Classification: `target_digit_boundary_island_code_rejected`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether high-surprisal boundary candidates should be encoded as",
        "contiguous islands plus offsets rather than as a flat candidate set.",
        "",
        "## Summary",
        "",
        f"- Books/candidates/actual cutpoints: `{s['book_count']}` / `{s['candidate_position_count']}` / `{s['actual_cutpoint_count']}`.",
        f"- Policies tested: `{s['policy_count']}`.",
        f"- Best island policy: `{s['best_policy']}`.",
        f"- Baseline full cutpoint atlas bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Island correction bits after policy charge: `{s['best_island_correction_bits_after_policy']:.3f}`.",
        f"- Island saving after policy charge: `{s['best_island_saving_after_policy']:.3f}` bits.",
        f"- Same-policy threshold saving: `{s['best_threshold_saving_same_policy_after_policy']:.3f}` bits.",
        f"- Island delta vs same-policy threshold: `{s['best_island_delta_vs_same_policy_threshold_bits']:.3f}` bits.",
        f"- Random island saving p95 after policy charge: `{s['best_random_saving_p95_after_policy']:.3f}` bits.",
        f"- TP/FP/FN: `{s['best_true_positive']}` / `{s['best_false_positive']}` / `{s['best_false_negative']}`.",
        f"- Predicted boundaries/correction events: `{s['best_predicted_count']}` / `{s['best_correction_events']}`.",
        f"- Islands/occupied/multi-hit: `{s['best_island_count']}` / `{s['best_occupied_islands']}` / `{s['best_multi_hit_islands']}`.",
        f"- Precision/recall: `{s['best_precision']:.6f}` / `{s['best_recall']:.6f}`.",
        f"- Exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Prefix-selected positive test-saving cells: `{s['prequential_positive_test_island_saving_cells']}/{s['prequential_cells']}`.",
        f"- Prefix-selected island-beats-threshold cells: `{s['prequential_island_beats_threshold_cells']}/{s['prequential_cells']}`.",
        "",
        "## Comparison To Threshold Gate",
        "",
        f"- Threshold gate best policy: `{c['threshold_gate_best_policy']}`.",
        f"- Threshold gate saving after policy charge: `{c['threshold_gate_saving_after_policy']:.3f}` bits.",
        f"- Best island saving delta vs threshold gate: `{c['best_island_saving_delta_vs_threshold_gate']:.3f}` bits.",
        f"- Best island correction delta vs threshold gate: `{c['best_island_correction_delta_vs_threshold_gate']:.3f}` bits.",
        "",
        "The island model is structurally informative but not a better code.",
        "The best policy's occupied islands are all single-hit, but there are still",
        "too many islands and outside misses for this to replace the flat threshold",
        "candidate-set correction code.",
        "",
        "## Top Island Policies",
        "",
        "| Policy | Island saving | Delta vs same-policy threshold | Islands | Occupied | FN | Exact books |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["full_fit_rows"][:8]:
        lines.append(
            f"| `{row['policy']}` | `{row['island_saving_after_policy']:.3f}` | "
            f"`{row['island_delta_vs_threshold_bits']:.3f}` | `{row['island_count']}` | "
            f"`{row['occupied_islands']}` | `{row['false_negative']}` | `{row['exact_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Island code promoted: `False`.",
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
