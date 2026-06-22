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

OUT_STEM = "01_target_digit_boundary_miss_residual_gate"
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 1000
ALPHA = 0.5
DIGITS = "0123456789"
PRIMARY_POLICY = "right_ge:4"
PRIMARY_POLICY_COUNT = 23
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
        primary = {pos for pos in candidates if surprisal[pos] >= 4.0}
        out[book] = {
            "book": book,
            "length": len(target),
            "candidate_positions": candidates,
            "actual_cutpoints": set(actual),
            "primary_candidates": primary,
            "outside_candidates": set(candidates) - primary,
            "surprisal": surprisal,
            "rank_fraction": rank_fraction,
        }
    return out


def distance_to_primary(pos: int, primary: set[int], fallback: int) -> int:
    if not primary:
        return fallback
    return min(abs(pos - candidate) for candidate in primary)


def residual_policy_specs() -> list[tuple[str, PolicyFunc]]:
    specs: list[tuple[str, PolicyFunc]] = []
    for threshold in [0.5, 1, 1.5, 2, 2.5, 3, 3.25, 3.5, 3.75]:
        name = f"outside_right_ge:{threshold}"

        def func(info: dict[str, Any], threshold: float = threshold) -> set[int]:
            return {
                pos
                for pos in info["outside_candidates"]
                if info["surprisal"][pos] >= threshold
            }

        specs.append((name, func))
    for distance in [1, 2, 3, 4, 5, 8, 13, 21]:
        name = f"near_primary:{distance}"

        def func(info: dict[str, Any], distance: int = distance) -> set[int]:
            return {
                pos
                for pos in info["outside_candidates"]
                if distance_to_primary(pos, info["primary_candidates"], info["length"]) <= distance
            }

        specs.append((name, func))
    for lo, hi in [
        (0, 0.03),
        (0, 0.05),
        (0, 0.08),
        (0, 0.10),
        (0, 0.15),
        (0, 0.20),
        (0.03, 0.10),
        (0.05, 0.15),
        (0.10, 0.20),
        (0.10, 0.30),
        (0.20, 0.50),
    ]:
        name = f"outside_rank_band:{lo}_{hi}"

        def func(info: dict[str, Any], lo: float = lo, hi: float = hi) -> set[int]:
            return {
                pos
                for pos in info["outside_candidates"]
                if lo < info["rank_fraction"][pos] <= hi
            }

        specs.append((name, func))
    for bins in [5, 10, 20]:
        for bucket in range(bins):
            name = f"position_bucket:{bucket}_of_{bins}"

            def func(
                info: dict[str, Any],
                bucket: int = bucket,
                bins: int = bins,
            ) -> set[int]:
                return {
                    pos
                    for pos in info["outside_candidates"]
                    if int(pos * bins / info["length"]) == bucket
                }

            specs.append((name, func))
    for modulus in [2, 3, 5, 10]:
        for remainder in range(modulus):
            name = f"position_mod:{modulus}_{remainder}"

            def func(
                info: dict[str, Any],
                modulus: int = modulus,
                remainder: int = remainder,
            ) -> set[int]:
                return {
                    pos
                    for pos in info["outside_candidates"]
                    if pos % modulus == remainder
                }

            specs.append((name, func))
    for threshold in [0, 0.25, 0.5, 1, 1.5, 2]:
        name = f"outside_delta_ge:{threshold}"

        def func(info: dict[str, Any], threshold: float = threshold) -> set[int]:
            return {
                pos
                for pos in info["outside_candidates"]
                if info["surprisal"][pos] - info["surprisal"][pos - 1] >= threshold
            }

        specs.append((name, func))
    for threshold in [2, 2.5, 3, 3.5]:
        name = f"outside_local_peak_ge:{threshold}"

        def func(info: dict[str, Any], threshold: float = threshold) -> set[int]:
            out = set()
            for pos in info["outside_candidates"]:
                right = info["surprisal"][pos + 1] if pos + 1 < info["length"] else -math.inf
                if (
                    info["surprisal"][pos] >= threshold
                    and info["surprisal"][pos] >= info["surprisal"][pos - 1]
                    and info["surprisal"][pos] >= right
                ):
                    out.add(pos)
            return out

        specs.append((name, func))
    return specs


def threshold_cost(info: dict[str, Any]) -> dict[str, Any]:
    candidates = info["candidate_positions"]
    actual = info["actual_cutpoints"]
    primary = info["primary_candidates"]
    outside = info["outside_candidates"]
    inside_hits = primary & actual
    outside_hits = outside & actual
    baseline = math.log2(info["length"]) + log2comb(len(candidates), len(actual))
    correction = log2comb(len(primary), len(inside_hits)) + log2comb(
        len(outside), len(outside_hits)
    )
    return {
        "baseline_bits": baseline,
        "threshold_correction_bits": correction,
        "inside_true_positive": len(inside_hits),
        "inside_false_positive": len(primary - actual),
        "outside_actual": len(outside_hits),
    }


def residual_cost(info: dict[str, Any], selected: set[int]) -> dict[str, Any]:
    actual = info["actual_cutpoints"]
    primary = info["primary_candidates"]
    outside = info["outside_candidates"]
    inside_hits = primary & actual
    outside_hits = outside & actual
    selected_hits = selected & outside_hits
    unselected = outside - selected
    correction = (
        log2comb(len(primary), len(inside_hits))
        + log2comb(len(selected), len(selected_hits))
        + log2comb(len(unselected), len(outside_hits - selected_hits))
    )
    return {
        "residual_correction_bits": correction,
        "residual_selected_count": len(selected),
        "residual_true_positive": len(selected_hits),
        "residual_false_positive": len(selected - outside_hits),
        "residual_false_negative": len(outside_hits - selected_hits),
        "outside_actual": len(outside_hits),
    }


def evaluate(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    policy_name: str,
    policy_func: PolicyFunc,
    policy_count: int,
    selected_override: dict[int, set[int]] | None = None,
) -> dict[str, Any]:
    baseline = threshold_bits = residual_bits = 0.0
    inside_tp = inside_fp = outside_actual = 0
    selected_count = residual_tp = residual_fp = residual_fn = exact_outside_books = 0
    for book in book_ids:
        info = per_book[book]
        threshold = threshold_cost(info)
        selected = selected_override[book] if selected_override else policy_func(info)
        residual = residual_cost(info, selected)
        baseline += threshold["baseline_bits"]
        threshold_bits += threshold["threshold_correction_bits"]
        residual_bits += residual["residual_correction_bits"]
        inside_tp += threshold["inside_true_positive"]
        inside_fp += threshold["inside_false_positive"]
        outside_actual += threshold["outside_actual"]
        selected_count += residual["residual_selected_count"]
        residual_tp += residual["residual_true_positive"]
        residual_fp += residual["residual_false_positive"]
        residual_fn += residual["residual_false_negative"]
        exact_outside_books += int(
            selected == (info["outside_candidates"] & info["actual_cutpoints"])
        )
    threshold_policy_bits = math.log2(PRIMARY_POLICY_COUNT)
    residual_policy_bits = math.log2(policy_count)
    threshold_after = threshold_bits + threshold_policy_bits
    residual_after = residual_bits + threshold_policy_bits + residual_policy_bits
    return {
        "policy": policy_name,
        "book_count": len(book_ids),
        "baseline_bits": baseline,
        "threshold_correction_bits_after_policy": threshold_after,
        "threshold_saving_after_policy": baseline - threshold_after,
        "residual_correction_bits_after_policy": residual_after,
        "residual_saving_after_policy": baseline - residual_after,
        "delta_vs_threshold_bits": threshold_after - residual_after,
        "inside_true_positive": inside_tp,
        "inside_false_positive": inside_fp,
        "outside_actual": outside_actual,
        "residual_selected_count": selected_count,
        "residual_true_positive": residual_tp,
        "residual_false_positive": residual_fp,
        "residual_false_negative": residual_fn,
        "residual_precision": residual_tp / selected_count if selected_count else 0.0,
        "residual_recall": residual_tp / outside_actual if outside_actual else 0.0,
        "exact_outside_books": exact_outside_books,
    }


def random_control(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    policy_name: str,
    policy_func: PolicyFunc,
    policy_count: int,
) -> dict[str, Any]:
    selected_counts = {
        book: len(policy_func(per_book[book]))
        for book in book_ids
    }
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in policy_name))
    deltas = []
    savings = []
    for _ in range(RANDOM_TRIALS):
        selected = {}
        for book in book_ids:
            outside = sorted(per_book[book]["outside_candidates"])
            count = selected_counts[book]
            selected[book] = set(rng.sample(outside, count)) if count else set()
        row = evaluate(per_book, book_ids, policy_name, policy_func, policy_count, selected)
        deltas.append(row["delta_vs_threshold_bits"])
        savings.append(row["residual_saving_after_policy"])
    deltas.sort()
    savings.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED + sum(ord(ch) for ch in policy_name),
        "delta_mean_vs_threshold_bits": mean(deltas),
        "delta_p05_vs_threshold_bits": percentile(deltas, 0.05),
        "delta_p95_vs_threshold_bits": percentile(deltas, 0.95),
        "saving_mean_after_policy": mean(savings),
        "saving_p95_after_policy": percentile(savings, 0.95),
    }


def full_fit_rows(
    per_book: dict[int, dict[str, Any]],
    specs: list[tuple[str, PolicyFunc]],
) -> list[dict[str, Any]]:
    return [
        evaluate(per_book, sorted(per_book), name, func, len(specs))
        for name, func in specs
    ]


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
        selected = max(train_rows, key=lambda row: (row["delta_vs_threshold_bits"], row["policy"]))
        selected_name, selected_func = next(
            (name, func) for name, func in specs if name == selected["policy"]
        )
        test = evaluate(per_book, test_books, selected_name, selected_func, len(specs))
        rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": selected_name,
                "train_delta_vs_threshold_bits": selected["delta_vs_threshold_bits"],
                "test_delta_vs_threshold_bits": test["delta_vs_threshold_bits"],
                "test_residual_saving_after_policy": test["residual_saving_after_policy"],
                "test_threshold_saving_after_policy": test["threshold_saving_after_policy"],
                "test_residual_true_positive": test["residual_true_positive"],
                "test_residual_false_positive": test["residual_false_positive"],
                "test_residual_false_negative": test["residual_false_negative"],
                "test_exact_outside_books": test["exact_outside_books"],
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
    specs = residual_policy_specs()
    full_rows = full_fit_rows(per_book, specs)
    best = max(full_rows, key=lambda row: (row["delta_vs_threshold_bits"], row["residual_recall"]))
    best_name, best_func = next((name, func) for name, func in specs if name == best["policy"])
    random_best = random_control(per_book, sorted(per_book), best_name, best_func, len(specs))
    preq = prequential_rows(per_book, specs)
    threshold_summary = threshold_gate["summary"]
    promotes_dependency_reduction = (
        best["delta_vs_threshold_bits"] > 0
        and best["delta_vs_threshold_bits"] > random_best["delta_p95_vs_threshold_bits"]
        and all(row["test_delta_vs_threshold_bits"] > 0 for row in preq)
    )
    summary = {
        "book_count": len(per_book),
        "candidate_position_count": sum(len(info["candidate_positions"]) for info in per_book.values()),
        "actual_cutpoint_count": sum(len(info["actual_cutpoints"]) for info in per_book.values()),
        "primary_policy": PRIMARY_POLICY,
        "primary_policy_count": PRIMARY_POLICY_COUNT,
        "residual_policy_count": len(specs),
        "best_residual_policy": best["policy"],
        "best_baseline_bits": best["baseline_bits"],
        "threshold_gate_saving_after_policy": threshold_summary["best_saving_after_policy"],
        "threshold_gate_correction_bits_after_policy": threshold_summary[
            "best_correction_bits_after_policy"
        ],
        "best_threshold_saving_recomputed_after_policy": best["threshold_saving_after_policy"],
        "best_residual_saving_after_policy": best["residual_saving_after_policy"],
        "best_residual_correction_bits_after_policy": best[
            "residual_correction_bits_after_policy"
        ],
        "best_delta_vs_threshold_bits": best["delta_vs_threshold_bits"],
        "best_random_delta_p95_vs_threshold_bits": random_best["delta_p95_vs_threshold_bits"],
        "inside_true_positive": best["inside_true_positive"],
        "inside_false_positive": best["inside_false_positive"],
        "outside_actual": best["outside_actual"],
        "best_residual_selected_count": best["residual_selected_count"],
        "best_residual_true_positive": best["residual_true_positive"],
        "best_residual_false_positive": best["residual_false_positive"],
        "best_residual_false_negative": best["residual_false_negative"],
        "best_residual_precision": best["residual_precision"],
        "best_residual_recall": best["residual_recall"],
        "best_exact_outside_books": best["exact_outside_books"],
        "prequential_cells": len(preq),
        "prequential_positive_delta_cells": sum(
            1 for row in preq if row["test_delta_vs_threshold_bits"] > 0
        ),
        "promotes_dependency_reduction": promotes_dependency_reduction,
        "promotes_endpoint_generator": False,
        "interpretation": (
            "A second-stage residual candidate rule captures part of the 107 "
            "cutpoints missed by the primary high-surprisal threshold and reduces "
            "the paid cutpoint dependency. It remains a broad candidate-code "
            "improvement with low precision, not an endpoint generator."
        ),
    }
    return {
        "schema": "target_digit_boundary_miss_residual_gate_v1",
        "scope": "analysis_only_threshold_miss_residual_candidate_code",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "threshold_gate": rel(THRESHOLD_GATE),
        },
        "full_fit_rows": sorted(full_rows, key=lambda row: row["delta_vs_threshold_bits"], reverse=True),
        "prequential_rows": preq,
        "random_control_best": random_best,
        "summary": summary,
        "classification": "target_digit_boundary_miss_residual_weak_not_promoted",
        "decision": {
            "promotes_dependency_reduction": promotes_dependency_reduction,
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
    lines = [
        "# Target Digit Boundary Miss Residual Gate",
        "",
        "Classification: `target_digit_boundary_miss_residual_weak_not_promoted`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the `107` cutpoints missed by the promoted `right_ge:4`",
        "boundary threshold have a second-stage source-free candidate structure.",
        "",
        "## Summary",
        "",
        f"- Books/candidates/actual cutpoints: `{s['book_count']}` / `{s['candidate_position_count']}` / `{s['actual_cutpoint_count']}`.",
        f"- Primary policy: `{s['primary_policy']}`.",
        f"- Residual policies tested: `{s['residual_policy_count']}`.",
        f"- Best residual policy: `{s['best_residual_policy']}`.",
        f"- Threshold gate saving after policy charge: `{s['threshold_gate_saving_after_policy']:.3f}` bits.",
        f"- Residual saving after primary+residual policy charge: `{s['best_residual_saving_after_policy']:.3f}` bits.",
        f"- Delta vs threshold: `{s['best_delta_vs_threshold_bits']:.3f}` bits.",
        f"- Random residual delta p95: `{s['best_random_delta_p95_vs_threshold_bits']:.3f}` bits.",
        f"- Primary inside TP/FP: `{s['inside_true_positive']}` / `{s['inside_false_positive']}`.",
        f"- Outside actual cutpoints: `{s['outside_actual']}`.",
        f"- Residual selected/TP/FP/FN: `{s['best_residual_selected_count']}` / `{s['best_residual_true_positive']}` / `{s['best_residual_false_positive']}` / `{s['best_residual_false_negative']}`.",
        f"- Residual precision/recall: `{s['best_residual_precision']:.6f}` / `{s['best_residual_recall']:.6f}`.",
        f"- Exact outside books: `{s['best_exact_outside_books']}/{s['book_count']}`.",
        f"- Prefix-selected positive delta cells: `{s['prequential_positive_delta_cells']}/{s['prequential_cells']}`.",
        "",
        "The best rule is still broad: it selects many residual candidates and does",
        "not generate exact endpoints. Full-fit evidence is positive, but the",
        "prefix-selected validation fails one cell, so this is not promoted.",
        "",
        "## Top Residual Policies",
        "",
        "| Policy | Delta vs threshold | Residual TP | Residual FP | Residual FN | Selected |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["full_fit_rows"][:8]:
        lines.append(
            f"| `{row['policy']}` | `{row['delta_vs_threshold_bits']:.3f}` | "
            f"`{row['residual_true_positive']}` | `{row['residual_false_positive']}` | "
            f"`{row['residual_false_negative']}` | `{row['residual_selected_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes dependency reduction: `{s['promotes_dependency_reduction']}`.",
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
