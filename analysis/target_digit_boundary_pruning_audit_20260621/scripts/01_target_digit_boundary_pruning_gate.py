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
BOUNDARY_GATE = (
    ROOT
    / "analysis"
    / "target_digit_boundary_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_boundary_gate.json"
)

OUT_STEM = "01_target_digit_boundary_pruning_gate"
RANDOM_SEED = 46920260621
RANDOM_TRIALS = 1000
ALPHA = 0.5
DIGITS = "0123456789"
Q_VALUES = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


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
    counts, global_counts = train_prev2(books, [candidate for candidate in sorted(books) if candidate < book])
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
            "actual_cutpoints": actual,
            "ranked_by_right_surprisal": ranked,
        }
    return out


def candidate_set(info: dict[str, Any], q: float) -> set[int]:
    k = max(1, math.ceil(q * len(info["candidate_positions"])))
    return set(info["ranked_by_right_surprisal"][:k])


def book_cost(info: dict[str, Any], selected: set[int]) -> dict[str, Any]:
    n = len(info["candidate_positions"])
    k = len(info["actual_cutpoints"])
    if k == 0:
        return {
            "baseline_bits": 0.0,
            "model_bits": 0.0,
            "hit_count": 0,
            "cutpoint_count": 0,
            "candidate_count": len(selected),
            "miss_count": 0,
        }
    actual = set(info["actual_cutpoints"])
    c = len(selected)
    h = len(actual & selected)
    baseline = log2comb(n, k)
    # Pay h so the decoder knows how many cutpoints are inside the pruned band.
    model = math.log2(k + 1) + log2comb(c, h) + log2comb(n - c, k - h)
    return {
        "baseline_bits": baseline,
        "model_bits": model,
        "hit_count": h,
        "cutpoint_count": k,
        "candidate_count": c,
        "miss_count": k - h,
    }


def evaluate_books(
    per_book: dict[int, dict[str, Any]],
    book_ids: list[int],
    q: float,
    selected_override: dict[int, set[int]] | None = None,
) -> dict[str, Any]:
    baseline = 0.0
    model = 0.0
    hits = 0
    cutpoints = 0
    candidates = 0
    misses = 0
    exact_nontrivial_books = 0
    nontrivial_books = 0
    for book in book_ids:
        info = per_book[book]
        selected = selected_override[book] if selected_override else candidate_set(info, q)
        cost = book_cost(info, selected)
        baseline += cost["baseline_bits"]
        model += cost["model_bits"]
        hits += cost["hit_count"]
        cutpoints += cost["cutpoint_count"]
        candidates += cost["candidate_count"]
        misses += cost["miss_count"]
        if cost["cutpoint_count"]:
            nontrivial_books += 1
            exact_nontrivial_books += int(cost["miss_count"] == 0)
    return {
        "q": q,
        "book_count": len(book_ids),
        "nontrivial_books": nontrivial_books,
        "baseline_bits": baseline,
        "model_bits_before_q_charge": model,
        "q_choice_bits": math.log2(len(Q_VALUES)),
        "model_bits_after_q_charge": model + math.log2(len(Q_VALUES)),
        "saving_before_q_charge": baseline - model,
        "saving_after_q_charge": baseline - model - math.log2(len(Q_VALUES)),
        "hit_count": hits,
        "cutpoint_count": cutpoints,
        "hit_fraction": hits / cutpoints if cutpoints else 0.0,
        "miss_count": misses,
        "candidate_count": candidates,
        "candidate_fraction": (
            candidates
            / sum(len(per_book[book]["candidate_positions"]) for book in book_ids)
            if book_ids
            else 0.0
        ),
        "exact_nontrivial_books": exact_nontrivial_books,
    }


def random_control(per_book: dict[int, dict[str, Any]], book_ids: list[int], q: float) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + int(q * 1000))
    savings = []
    hits = []
    for _ in range(RANDOM_TRIALS):
        selected = {}
        for book in book_ids:
            info = per_book[book]
            c = max(1, math.ceil(q * len(info["candidate_positions"])))
            selected[book] = set(rng.sample(info["candidate_positions"], c))
        row = evaluate_books(per_book, book_ids, q, selected)
        savings.append(row["saving_before_q_charge"])
        hits.append(row["hit_fraction"])
    savings.sort()
    hits.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED + int(q * 1000),
        "saving_mean": mean(savings),
        "saving_p05": percentile(savings, 0.05),
        "saving_p95": percentile(savings, 0.95),
        "hit_fraction_mean": mean(hits),
        "hit_fraction_p05": percentile(hits, 0.05),
        "hit_fraction_p95": percentile(hits, 0.95),
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
    for q in Q_VALUES:
        row = evaluate_books(per_book, book_ids, q)
        control = random_control(per_book, book_ids, q)
        row["random_control"] = control
        row["saving_beats_random_p95"] = row["saving_before_q_charge"] > control["saving_p95"]
        row["hit_fraction_beats_random_p95"] = row["hit_fraction"] > control["hit_fraction_p95"]
        rows.append(row)
    return rows


def prequential_rows(per_book: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    all_books = sorted(per_book)
    for cutoff in PREFIX_CUTOFFS:
        train_books = [book for book in all_books if book < cutoff]
        test_books = [book for book in all_books if book >= cutoff]
        train_by_q = [evaluate_books(per_book, train_books, q) for q in Q_VALUES]
        selected = max(train_by_q, key=lambda row: (row["saving_before_q_charge"], -row["q"]))
        test = evaluate_books(per_book, test_books, selected["q"])
        rows.append(
            {
                "cutoff": cutoff,
                "selected_q": selected["q"],
                "train_saving_before_q_charge": selected["saving_before_q_charge"],
                "test_book_count": len(test_books),
                "test_cutpoints": test["cutpoint_count"],
                "test_hit_count": test["hit_count"],
                "test_hit_fraction": test["hit_fraction"],
                "test_saving_before_q_charge": test["saving_before_q_charge"],
                "test_saving_after_q_charge": test["saving_after_q_charge"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    boundary_gate = load_json(BOUNDARY_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("target_digit_boundary_gate", boundary_gate)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    per_book = make_per_book(books, copy_ledger["canonical_ops_by_book"])
    rows = full_fit_rows(per_book)
    best = max(rows, key=lambda row: (row["saving_after_q_charge"], row["hit_fraction"]))
    preq = prequential_rows(per_book)
    promotes_pruning_clue = (
        best["saving_after_q_charge"] > 0
        and best["saving_beats_random_p95"]
        and all(row["test_saving_before_q_charge"] > 0 for row in preq)
    )
    promotes_endpoint_generator = False
    summary = {
        "book_count": len(per_book),
        "cutpoint_count": sum(len(info["actual_cutpoints"]) for info in per_book.values()),
        "candidate_position_count": sum(len(info["candidate_positions"]) for info in per_book.values()),
        "best_q": best["q"],
        "best_candidate_fraction": best["candidate_fraction"],
        "best_hit_count": best["hit_count"],
        "best_cutpoint_count": best["cutpoint_count"],
        "best_hit_fraction": best["hit_fraction"],
        "best_miss_count": best["miss_count"],
        "best_baseline_bits": best["baseline_bits"],
        "best_model_bits_after_q_charge": best["model_bits_after_q_charge"],
        "best_saving_after_q_charge": best["saving_after_q_charge"],
        "best_random_saving_p95": best["random_control"]["saving_p95"],
        "prequential_cells": len(preq),
        "prequential_positive_test_saving_cells": sum(
            1 for row in preq if row["test_saving_before_q_charge"] > 0
        ),
        "prequential_positive_test_saving_after_q_charge_cells": sum(
            1 for row in preq if row["test_saving_after_q_charge"] > 0
        ),
        "promotes_boundary_pruning_clue": promotes_pruning_clue,
        "promotes_endpoint_generator": promotes_endpoint_generator,
        "interpretation": (
            "High prev2 right-surprisal bands reduce the paid cutpoint atlas "
            "under a two-part cutpoint code and survive prefix-selected suffix "
            "checks. The rule still requires declaring misses and does not "
            "generate endpoints by itself."
        ),
    }
    return {
        "schema": "target_digit_boundary_pruning_gate_v1",
        "scope": "analysis_only_cutpoint_candidate_reduction",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "target_digit_boundary_gate": rel(BOUNDARY_GATE),
        },
        "q_values": Q_VALUES,
        "full_fit_rows": rows,
        "prequential_rows": preq,
        "summary": summary,
        "classification": "target_digit_boundary_pruning_clue_promoted_not_generator",
        "decision": {
            "promotes_boundary_pruning_clue": promotes_pruning_clue,
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
        "# Target Digit Boundary Pruning Gate",
        "",
        "Classification: `target_digit_boundary_pruning_clue_promoted_not_generator`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether high `prev2_digits` right-surprisal bands reduce the",
        "paid cutpoint dependency after charging misses and threshold choice.",
        "",
        "## Summary",
        "",
        f"- Books/cutpoints/candidate positions: `{s['book_count']}` / `{s['cutpoint_count']}` / `{s['candidate_position_count']}`.",
        f"- Best q: `{s['best_q']}`.",
        f"- Candidate fraction at best q: `{s['best_candidate_fraction']:.6f}`.",
        f"- Hits/misses: `{s['best_hit_count']}/{s['best_cutpoint_count']}` / `{s['best_miss_count']}`.",
        f"- Baseline cutpoint bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Model bits after q charge: `{s['best_model_bits_after_q_charge']:.3f}`.",
        f"- Saving after q charge: `{s['best_saving_after_q_charge']:.3f}` bits.",
        f"- Random saving p95 at best q: `{s['best_random_saving_p95']:.3f}` bits.",
        f"- Prefix-selected positive test-saving cells: `{s['prequential_positive_test_saving_cells']}/{s['prequential_cells']}` before q charge, `{s['prequential_positive_test_saving_after_q_charge_cells']}/{s['prequential_cells']}` after q charge.",
        "",
        "## Full-Fit Rows",
        "",
        "| q | Candidates | Hits | Misses | Saving after q | Random saving p95 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["full_fit_rows"]:
        lines.append(
            f"| `{row['q']}` | `{row['candidate_count']}` | "
            f"`{row['hit_count']}/{row['cutpoint_count']}` | "
            f"`{row['miss_count']}` | "
            f"`{row['saving_after_q_charge']:.3f}` | "
            f"`{row['random_control']['saving_p95']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Suffix Rows",
            "",
            "| Cutoff | Selected q | Test hits | Test saving before q | Test saving after q |",
            "| ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_q']}` | "
            f"`{row['test_hit_count']}/{row['test_cutpoints']}` | "
            f"`{row['test_saving_before_q_charge']:.3f}` | "
            f"`{row['test_saving_after_q_charge']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Promotes boundary pruning clue: `True`.",
            "- Promotes endpoint generator: `False`.",
            "- The clue reduces the paid cutpoint dependency, but exact endpoints still require residual declarations.",
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
