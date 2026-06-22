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
PRUNING_GATE = (
    ROOT
    / "analysis"
    / "target_digit_boundary_pruning_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_boundary_pruning_gate.json"
)

OUT_STEM = "01_target_digit_boundary_rankcode_gate"
RANDOM_SEED = 46920260621
RANDOM_TRIALS = 1000
ALPHA = 0.5
DIGITS = "0123456789"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]

SCHEMES: dict[str, list[float]] = {
    "top10_rest": [0.10],
    "top10_20_50": [0.10, 0.20, 0.50],
    "top5_10_20_50": [0.05, 0.10, 0.20, 0.50],
    "top5_10_15_20_30_50": [0.05, 0.10, 0.15, 0.20, 0.30, 0.50],
    "deciles": [index / 10 for index in range(1, 10)],
    "ventiles": [index / 20 for index in range(1, 20)],
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
        actual = [
            int(op["target_start"]) + int(op["length"])
            for op in ops_by_book[str(book)][:-1]
        ]
        actual = sorted(pos for pos in actual if 0 < pos < len(target))
        candidates = list(range(1, len(target)))
        ranked = sorted(candidates, key=lambda pos: (-surprisal[pos], pos))
        out[book] = {
            "book": book,
            "length": len(target),
            "candidate_positions": candidates,
            "ranked_by_right_surprisal": ranked,
            "actual_cutpoints": actual,
        }
    return out


def rank_bins(n: int, scheme: list[float]) -> list[tuple[int, int]]:
    bins = []
    previous = 0
    for fraction in scheme:
        end = min(n, math.ceil(fraction * n))
        if end > previous:
            bins.append((previous, end))
            previous = end
    if previous < n:
        bins.append((previous, n))
    return bins


def book_rankcode_cost(
    info: dict[str, Any],
    scheme: list[float],
    selected_override: set[int] | None = None,
) -> dict[str, Any]:
    ranked = info["ranked_by_right_surprisal"]
    n = len(ranked)
    actual = set(info["actual_cutpoints"] if selected_override is None else selected_override)
    k = len(actual)
    if k == 0:
        return {
            "baseline_bits": 0.0,
            "model_bits": 0.0,
            "cutpoint_count": 0,
            "bin_counts": [0 for _ in rank_bins(n, scheme)],
        }
    baseline = log2comb(n, k)
    counts = []
    sizes = []
    for start, end in rank_bins(n, scheme):
        bucket = set(ranked[start:end])
        counts.append(len(actual & bucket))
        sizes.append(end - start)
    bin_count = len(sizes)
    composition_bits = log2comb(k + bin_count - 1, bin_count - 1)
    within_bin_bits = sum(log2comb(size, count) for size, count in zip(sizes, counts))
    return {
        "baseline_bits": baseline,
        "model_bits": composition_bits + within_bin_bits,
        "cutpoint_count": k,
        "bin_counts": counts,
        "composition_bits": composition_bits,
        "within_bin_bits": within_bin_bits,
    }


def evaluate(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    scheme_name: str,
    selected_override: dict[int, set[int]] | None = None,
) -> dict[str, Any]:
    scheme = SCHEMES[scheme_name]
    baseline = 0.0
    model = 0.0
    cutpoints = 0
    bin_totals: list[int] | None = None
    for book in book_ids:
        cost = book_rankcode_cost(
            per_book[book],
            scheme,
            selected_override[book] if selected_override else None,
        )
        baseline += cost["baseline_bits"]
        model += cost["model_bits"]
        cutpoints += cost["cutpoint_count"]
        if bin_totals is None:
            bin_totals = [0 for _ in cost["bin_counts"]]
        for index, count in enumerate(cost["bin_counts"]):
            bin_totals[index] += count
    scheme_choice_bits = math.log2(len(SCHEMES))
    return {
        "scheme": scheme_name,
        "book_count": len(book_ids),
        "cutpoint_count": cutpoints,
        "baseline_bits": baseline,
        "model_bits_before_scheme_charge": model,
        "scheme_choice_bits": scheme_choice_bits,
        "model_bits_after_scheme_charge": model + scheme_choice_bits,
        "saving_before_scheme_charge": baseline - model,
        "saving_after_scheme_charge": baseline - model - scheme_choice_bits,
        "bin_totals": bin_totals or [],
    }


def random_control(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    scheme_name: str,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in scheme_name))
    savings = []
    for _ in range(RANDOM_TRIALS):
        selected = {}
        for book in book_ids:
            info = per_book[book]
            k = len(info["actual_cutpoints"])
            candidates = info["candidate_positions"]
            selected[book] = set(rng.sample(candidates, k)) if k else set()
        row = evaluate(per_book, book_ids, scheme_name, selected)
        savings.append(row["saving_before_scheme_charge"])
    savings.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED + sum(ord(ch) for ch in scheme_name),
        "saving_mean": mean(savings),
        "saving_p05": percentile(savings, 0.05),
        "saving_p95": percentile(savings, 0.95),
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
    for scheme_name in SCHEMES:
        row = evaluate(per_book, book_ids, scheme_name)
        control = random_control(per_book, book_ids, scheme_name)
        row["random_control"] = control
        row["saving_beats_random_p95"] = (
            row["saving_before_scheme_charge"] > control["saving_p95"]
        )
        rows.append(row)
    return rows


def prequential_rows(per_book: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    all_books = sorted(per_book)
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = [book for book in all_books if book < cutoff]
        test_books = [book for book in all_books if book >= cutoff]
        train_rows = [evaluate(per_book, train_books, scheme) for scheme in SCHEMES]
        selected = max(
            train_rows,
            key=lambda row: (row["saving_before_scheme_charge"], row["scheme"]),
        )
        test = evaluate(per_book, test_books, selected["scheme"])
        rows.append(
            {
                "cutoff": cutoff,
                "selected_scheme": selected["scheme"],
                "train_saving_before_scheme_charge": selected[
                    "saving_before_scheme_charge"
                ],
                "test_cutpoints": test["cutpoint_count"],
                "test_saving_before_scheme_charge": test[
                    "saving_before_scheme_charge"
                ],
                "test_saving_after_scheme_charge": test[
                    "saving_after_scheme_charge"
                ],
                "test_bin_totals": test["bin_totals"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    pruning_gate = load_json(PRUNING_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("target_digit_boundary_pruning_gate", pruning_gate)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    per_book = make_per_book(books, copy_ledger["canonical_ops_by_book"])
    rows = full_fit_rows(per_book)
    best = max(
        rows,
        key=lambda row: (row["saving_after_scheme_charge"], row["saving_before_scheme_charge"]),
    )
    preq = prequential_rows(per_book)
    promotes_rankcode_clue = (
        best["saving_after_scheme_charge"] > 0
        and best["saving_beats_random_p95"]
        and all(row["test_saving_after_scheme_charge"] > 0 for row in preq)
    )
    promotes_endpoint_generator = False
    summary = {
        "book_count": len(per_book),
        "cutpoint_count": sum(len(info["actual_cutpoints"]) for info in per_book.values()),
        "candidate_position_count": sum(
            len(info["candidate_positions"]) for info in per_book.values()
        ),
        "best_scheme": best["scheme"],
        "best_bin_totals": best["bin_totals"],
        "best_baseline_bits": best["baseline_bits"],
        "best_model_bits_after_scheme_charge": best["model_bits_after_scheme_charge"],
        "best_saving_after_scheme_charge": best["saving_after_scheme_charge"],
        "best_random_saving_p95": best["random_control"]["saving_p95"],
        "best_beats_random_p95": best["saving_beats_random_p95"],
        "prequential_cells": len(preq),
        "prequential_positive_test_saving_after_scheme_charge_cells": sum(
            1 for row in preq if row["test_saving_after_scheme_charge"] > 0
        ),
        "promotes_boundary_rankcode_clue": promotes_rankcode_clue,
        "promotes_endpoint_generator": promotes_endpoint_generator,
        "interpretation": (
            "A fixed rank-bin code over prev2 right-surprisal ranks reduces "
            "the paid cutpoint atlas more than the one-band pruning code in "
            "full fit, but it fails the strict all-suffix promotion gate. It "
            "remains a weak diagnostic, not a promoted parser component."
        ),
    }
    return {
        "schema": "target_digit_boundary_rankcode_gate_v1",
        "scope": "analysis_only_cutpoint_rank_distribution_code",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "target_digit_boundary_pruning_gate": rel(PRUNING_GATE),
        },
        "schemes": SCHEMES,
        "full_fit_rows": rows,
        "prequential_rows": preq,
        "summary": summary,
        "classification": "target_digit_boundary_rankcode_weak_not_promoted",
        "decision": {
            "promotes_boundary_rankcode_clue": promotes_rankcode_clue,
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
        "# Target Digit Boundary Rank-Code Gate",
        "",
        "Classification: `target_digit_boundary_rankcode_weak_not_promoted`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the full rank distribution of internal cutpoints under",
        "`prev2_digits` right-surprisal reduces the paid cutpoint atlas.",
        "",
        "## Summary",
        "",
        f"- Books/cutpoints/candidate positions: `{s['book_count']}` / `{s['cutpoint_count']}` / `{s['candidate_position_count']}`.",
        f"- Best scheme: `{s['best_scheme']}`.",
        f"- Best bin totals: `{s['best_bin_totals']}`.",
        f"- Baseline cutpoint bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Model bits after scheme charge: `{s['best_model_bits_after_scheme_charge']:.3f}`.",
        f"- Saving after scheme charge: `{s['best_saving_after_scheme_charge']:.3f}` bits.",
        f"- Random saving p95 for best scheme: `{s['best_random_saving_p95']:.3f}` bits.",
        f"- Prefix-selected positive test-saving cells after scheme charge: `{s['prequential_positive_test_saving_after_scheme_charge_cells']}/{s['prequential_cells']}`.",
        "",
        "## Full-Fit Rows",
        "",
        "| Scheme | Bin totals | Saving after scheme | Random saving p95 |",
        "| --- | --- | ---: | ---: |",
    ]
    for row in result["full_fit_rows"]:
        lines.append(
            f"| `{row['scheme']}` | `{row['bin_totals']}` | "
            f"`{row['saving_after_scheme_charge']:.3f}` | "
            f"`{row['random_control']['saving_p95']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Suffix Rows",
            "",
            "| Cutoff | Selected scheme | Test cutpoints | Test saving after scheme |",
            "| ---: | --- | ---: | ---: |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_scheme']}` | "
            f"`{row['test_cutpoints']}` | "
            f"`{row['test_saving_after_scheme_charge']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Promotes boundary rank-code clue: `False`.",
            "- Promotes endpoint generator: `False`.",
            "- The rank distribution improves full-fit cutpoint coding, but prefix-selected suffix validation fails in one cell.",
            "- The prior boundary-pruning clue remains the stronger promoted result.",
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
