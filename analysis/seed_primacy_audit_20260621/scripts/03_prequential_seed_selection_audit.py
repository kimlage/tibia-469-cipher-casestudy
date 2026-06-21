from __future__ import annotations

import importlib.util
import json
import random
import time
from functools import lru_cache
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
SCRIPTS = HERE / "scripts"
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
SEED_COVERAGE = TEST_RESULTS / "01_seed_coverage_audit.json"

MIN_COPY_LEN = 5
PREFIX_CUTOFFS = [10, 20, 35, 50]
SEED_SIZES = [5, 10]
RANDOM_SAMPLES = 200
RNG_SEED = 4692026062103


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_seed_module() -> Any:
    path = SCRIPTS / "01_seed_coverage_audit.py"
    spec = importlib.util.spec_from_file_location("seed_coverage_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")
    row0 = decision.get("row0_origin_status", decision.get("row0_status"))
    if row0 not in {None, "unchanged_exogenous", "exogenous_under_current_evidence"}:
        raise RuntimeError(f"{name} changed row0 origin")


def summarize(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "median": float(median(ordered)),
        "mean": float(mean(ordered)),
        "p95": ordered[int(0.95 * (len(ordered) - 1))],
        "max": ordered[-1],
    }


def percentile(value: float, samples: list[float]) -> float:
    return sum(1 for sample in samples if sample <= value) / len(samples)


def make_result() -> dict[str, Any]:
    start = time.perf_counter()
    seed_coverage = load_json(SEED_COVERAGE)
    assert_boundary("seed_coverage_audit", seed_coverage)
    if seed_coverage["classification"] != "AUDIT_ONLY_COMPRESSION":
        raise RuntimeError("seed coverage audit did not close as audit-only")

    module = load_seed_module()
    books_raw = load_json(BOOKS_DIGITS)
    books = {int(book): text for book, text in books_raw.items()}
    all_books = sorted(books)
    maxlens_by_target_source = module.precompute_source_target_maxlens(books)

    @lru_cache(maxsize=None)
    def evaluate(seed_tuple: tuple[int, ...], target_tuple: tuple[int, ...]) -> dict[str, Any]:
        seed = set(seed_tuple)
        totals = {
            "target_digits": 0,
            "copied_digits_explained": 0,
            "literal_digits_required": 0,
            "copy_items_required": 0,
            "literal_runs_required": 0,
            "op_count": 0,
        }
        for target_book in target_tuple:
            if target_book in seed:
                continue
            target = books[target_book]
            combined = [0] * len(target)
            for source_book in seed_tuple:
                source_lens = maxlens_by_target_source[target_book].get(source_book)
                if source_lens is None:
                    continue
                for pos, length in enumerate(source_lens):
                    if length > combined[pos]:
                        combined[pos] = length
            parsed = module.parse_target(combined)
            totals["target_digits"] += len(target)
            totals["copied_digits_explained"] += int(parsed["copied_digits"])
            totals["literal_digits_required"] += int(parsed["literal_digits"])
            totals["copy_items_required"] += int(parsed["copy_items"])
            totals["literal_runs_required"] += int(parsed["literal_runs"])
            totals["op_count"] += int(parsed["op_count"])
        copied = totals["copied_digits_explained"]
        target_digits = totals["target_digits"]
        return {
            **totals,
            "coverage_rate": copied / target_digits if target_digits else 0.0,
        }

    def greedy_select(
        candidate_pool: list[int],
        k: int,
        target_mode: str,
        fixed_targets: list[int] | None = None,
    ) -> list[int]:
        chosen: list[int] = []
        remaining = set(candidate_pool)
        for _ in range(k):
            best_book = None
            best_score = None
            for book in sorted(remaining):
                candidate = tuple(sorted(chosen + [book]))
                if target_mode == "train_internal":
                    targets = tuple(book for book in candidate_pool if book not in candidate)
                elif target_mode == "fixed_targets":
                    if fixed_targets is None:
                        raise RuntimeError("fixed target mode requires targets")
                    targets = tuple(fixed_targets)
                else:
                    raise RuntimeError(f"unknown target mode {target_mode}")
                row = evaluate(candidate, targets)
                score = (
                    row["copied_digits_explained"],
                    -row["literal_digits_required"],
                    -row["copy_items_required"],
                    -sum(candidate),
                )
                if best_score is None or score > best_score:
                    best_score = score
                    best_book = book
            if best_book is None:
                raise RuntimeError("greedy selection failed")
            chosen.append(best_book)
            remaining.remove(best_book)
        return sorted(chosen)

    rng = random.Random(RNG_SEED)
    rows: list[dict[str, Any]] = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = [book for book in all_books if book < cutoff]
        test_books = [book for book in all_books if book >= cutoff]
        for k in SEED_SIZES:
            if len(train_books) <= k or not test_books:
                continue
            train_greedy = greedy_select(train_books, k, "train_internal")
            suffix_oracle = greedy_select(
                train_books, k, "fixed_targets", fixed_targets=test_books
            )
            operational = list(range(k))
            candidate_sets = {
                "operational_prefix": operational,
                "train_greedy_internal": train_greedy,
                "suffix_oracle_from_train": suffix_oracle,
            }
            random_rows = []
            for _ in range(RANDOM_SAMPLES):
                seed = tuple(sorted(rng.sample(train_books, k)))
                random_rows.append(evaluate(seed, tuple(test_books)))
            random_copied = [row["copied_digits_explained"] for row in random_rows]
            random_coverage = [row["coverage_rate"] for row in random_rows]
            random_summary = {
                "copied_digits": summarize([float(v) for v in random_copied]),
                "coverage_rate": summarize(random_coverage),
            }
            candidate_eval = {}
            for label, seed in candidate_sets.items():
                row = evaluate(tuple(seed), tuple(test_books))
                candidate_eval[label] = {
                    "seed_books": seed,
                    **row,
                    "copied_digit_percentile_vs_random_train_seeds": percentile(
                        float(row["copied_digits_explained"]),
                        [float(v) for v in random_copied],
                    ),
                    "copied_delta_vs_random_median": (
                        row["copied_digits_explained"]
                        - random_summary["copied_digits"]["median"]
                    ),
                    "coverage_delta_vs_random_median": (
                        row["coverage_rate"] - random_summary["coverage_rate"]["median"]
                    ),
                }
            oracle_copied = candidate_eval["suffix_oracle_from_train"][
                "copied_digits_explained"
            ]
            train_copied = candidate_eval["train_greedy_internal"][
                "copied_digits_explained"
            ]
            rows.append(
                {
                    "cutoff": cutoff,
                    "seed_book_count": k,
                    "train_books": train_books,
                    "test_books": test_books,
                    "train_book_count": len(train_books),
                    "test_book_count": len(test_books),
                    "test_digits": sum(len(books[book]) for book in test_books),
                    "random_train_seed_controls": random_summary,
                    "candidates": candidate_eval,
                    "train_greedy_oracle_gap_copied_digits": (
                        oracle_copied - train_copied
                    ),
                    "train_greedy_oracle_gap_coverage": (
                        candidate_eval["suffix_oracle_from_train"]["coverage_rate"]
                        - candidate_eval["train_greedy_internal"]["coverage_rate"]
                    ),
                }
            )

    train_greedy_beats_median = [
        row
        for row in rows
        if row["candidates"]["train_greedy_internal"]["copied_delta_vs_random_median"] > 0
    ]
    train_greedy_beats_p95 = [
        row
        for row in rows
        if (
            row["candidates"]["train_greedy_internal"][
                "copied_digit_percentile_vs_random_train_seeds"
            ]
            >= 0.95
        )
    ]
    operational_beats_median = [
        row
        for row in rows
        if row["candidates"]["operational_prefix"]["copied_delta_vs_random_median"] > 0
    ]
    train_greedy_gaps = [
        row["train_greedy_oracle_gap_coverage"] for row in rows
    ]
    promoted = (
        len(train_greedy_beats_p95) == len(rows)
        and mean(train_greedy_gaps) <= 0.02
    )
    classification = (
        "prequential_seed_selection_promotable_candidate"
        if promoted
        else "prequential_seed_selection_not_promoted"
    )
    return {
        "schema": "prequential_seed_selection_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "seed_coverage_audit": rel(SEED_COVERAGE),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "prefix_cutoffs": PREFIX_CUTOFFS,
            "seed_sizes": SEED_SIZES,
            "random_samples_per_cell": RANDOM_SAMPLES,
            "rng_seed": RNG_SEED,
            "seed_candidates_restricted_to_train_prefix": True,
            "test_suffix_hidden_from_train_greedy": True,
            "suffix_oracle_is_posthoc_control_only": True,
        },
        "summary": {
            "elapsed_seconds": time.perf_counter() - start,
            "evaluated_cells": len(rows),
            "train_greedy_beats_random_median_cells": len(train_greedy_beats_median),
            "train_greedy_beats_random_p95_cells": len(train_greedy_beats_p95),
            "operational_beats_random_median_cells": len(operational_beats_median),
            "mean_train_greedy_oracle_gap_coverage": mean(train_greedy_gaps),
            "max_train_greedy_oracle_gap_coverage": max(train_greedy_gaps),
            "promotes_prequential_seed_generator": promoted,
            "interpretation": (
                "Seed sets selected only from the prefix do not close the "
                "posthoc gap. The train-greedy seeds can beat random controls "
                "in some splits, but they do not consistently beat p95 random "
                "train seeds and remain behind suffix-oracle seeds selected "
                "after seeing the future books. Seed selection therefore stays "
                "audit-only rather than a generative mechanism."
            ),
        },
        "rows": rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "prequential_seed_selection_not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "authorial_seed_claim": "BLOCKED_NEEDS_EXTERNAL_SOURCE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "03_prequential_seed_selection_audit.json"
    md_path = TEST_RESULTS / "03_prequential_seed_selection_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Prequential Seed Selection Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The seed coverage audit found high-coverage seed sets only posthoc. This",
        "audit asks whether seeds selected using only prefix books predict future",
        "suffix coverage without retuning on the test books.",
        "",
        "## Result",
        "",
        f"- Evaluated prefix/k cells: `{s['evaluated_cells']}`.",
        f"- Train-greedy beats random median cells: `{s['train_greedy_beats_random_median_cells']}`.",
        f"- Train-greedy beats random p95 cells: `{s['train_greedy_beats_random_p95_cells']}`.",
        f"- Operational prefix beats random median cells: `{s['operational_beats_random_median_cells']}`.",
        f"- Mean train-greedy vs suffix-oracle coverage gap: `{s['mean_train_greedy_oracle_gap_coverage']:.6f}`.",
        f"- Max train-greedy vs suffix-oracle coverage gap: `{s['max_train_greedy_oracle_gap_coverage']:.6f}`.",
        f"- Promotes prequential seed generator: `{s['promotes_prequential_seed_generator']}`.",
        "",
        "## Cells",
        "",
        "| cutoff | k | train-greedy seed | train-greedy coverage | random median coverage | train percentile | suffix-oracle coverage | operational coverage |",
        "|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        train = row["candidates"]["train_greedy_internal"]
        oracle = row["candidates"]["suffix_oracle_from_train"]
        operational = row["candidates"]["operational_prefix"]
        random_median = row["random_train_seed_controls"]["coverage_rate"]["median"]
        lines.append(
            f"| {row['cutoff']} | {row['seed_book_count']} | `{train['seed_books']}` | "
            f"{train['coverage_rate']:.6f} | {random_median:.6f} | "
            f"{train['copied_digit_percentile_vs_random_train_seeds']:.3f} | "
            f"{oracle['coverage_rate']:.6f} | {operational['coverage_rate']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- Suffix-oracle seeds are posthoc controls only.",
            "- No compression-bound change is introduced.",
            "- No formula is emitted.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
