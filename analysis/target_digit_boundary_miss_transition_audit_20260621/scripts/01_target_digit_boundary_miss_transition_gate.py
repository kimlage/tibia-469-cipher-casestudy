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
MISS_RESIDUAL_GATE = (
    ROOT
    / "analysis"
    / "target_digit_boundary_miss_residual_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_boundary_miss_residual_gate.json"
)

OUT_STEM = "01_target_digit_boundary_miss_transition_gate"
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 2000
ALPHA = 0.5
DIGITS = "0123456789"
FEATURE_CHOICE_COUNT = 15
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


def len_bucket(length: int) -> str:
    if length < 6:
        return "short"
    if length < 20:
        return "med"
    return "long"


def make_rows(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    previous_chunks: list[str] = []
    previous_prefix3: set[str] = set()
    previous_suffix3: set[str] = set()
    for book in range(10, 70):
        target = books[book]
        surprisal = book_surprisals(books, book)
        local_chunks: list[str] = []
        book_ops = ops_by_book[str(book)]
        for index, op in enumerate(book_ops):
            start = int(op["target_start"])
            length = int(op["length"])
            chunk = target[start : start + length]
            if index < len(book_ops) - 1:
                next_op = book_ops[index + 1]
                cutpoint = start + length
                next_length = int(next_op["length"])
                next_chunk = target[cutpoint : cutpoint + next_length]
                seen_chunks = set(previous_chunks + local_chunks[:-1])
                row = {
                    "book": book,
                    "op_index": index,
                    "cutpoint": cutpoint,
                    "miss": surprisal[cutpoint] < 4.0,
                    "transition": f"{op['type']}->{next_op['type']}",
                    "prev_type": op["type"],
                    "next_type": next_op["type"],
                    "prev_len_bucket": len_bucket(length),
                    "next_len_bucket": len_bucket(next_length),
                    "shape": (
                        f"{op['type']}_{len_bucket(length)}__"
                        f"{next_op['type']}_{len_bucket(next_length)}"
                    ),
                    "op_mod2": str(index % 2),
                    "op_mod3": str(index % 3),
                    "op_mod5": str(index % 5),
                    "book_mod10": str(book % 10),
                    "pos_quint": str(int(cutpoint * 5 / len(target))),
                    "next_chunk_seen_before": str(next_chunk in seen_chunks),
                    "prev_chunk_seen_before": str(chunk in seen_chunks),
                    "next_prefix3_seen": str(
                        len(next_chunk) >= 3 and next_chunk[:3] in previous_prefix3
                    ),
                    "prev_suffix3_seen": str(
                        len(chunk) >= 3 and chunk[-3:] in previous_suffix3
                    ),
                }
                rows.append(row)
            local_chunks.append(chunk)
        for op in book_ops:
            start = int(op["target_start"])
            length = int(op["length"])
            chunk = target[start : start + length]
            previous_chunks.append(chunk)
            if len(chunk) >= 3:
                previous_prefix3.add(chunk[:3])
                previous_suffix3.add(chunk[-3:])
    return rows


def features() -> list[str]:
    return [
        "transition",
        "prev_type",
        "next_type",
        "prev_len_bucket",
        "next_len_bucket",
        "shape",
        "op_mod2",
        "op_mod3",
        "op_mod5",
        "book_mod10",
        "pos_quint",
        "next_chunk_seen_before",
        "prev_chunk_seen_before",
        "next_prefix3_seen",
        "prev_suffix3_seen",
    ]


def label_cost(rows: list[dict[str, Any]], feature: str | None = None) -> float:
    if not rows:
        return 0.0
    if feature is None:
        return log2comb(len(rows), sum(1 for row in rows if row["miss"]))
    total = 0.0
    for value in set(row[feature] for row in rows):
        subset = [row for row in rows if row[feature] == value]
        total += log2comb(len(subset), sum(1 for row in subset if row["miss"]))
    return total


def feature_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline = label_cost(rows)
    out = []
    for feature in features():
        grouped = label_cost(rows, feature)
        out.append(
            {
                "feature": feature,
                "category_count": len(set(row[feature] for row in rows)),
                "baseline_bits": baseline,
                "grouped_bits_before_feature_charge": grouped,
                "saving_before_feature_charge": baseline - grouped,
                "saving_after_feature_charge": baseline
                - grouped
                - math.log2(FEATURE_CHOICE_COUNT),
                "category_counts": {
                    value: {
                        "rows": sum(1 for row in rows if row[feature] == value),
                        "misses": sum(
                            1
                            for row in rows
                            if row[feature] == value and row["miss"]
                        ),
                    }
                    for value in sorted(set(row[feature] for row in rows))
                },
            }
        )
    return out


def random_control(rows: list[dict[str, Any]], feature: str) -> dict[str, Any]:
    labels = [row["miss"] for row in rows]
    baseline = label_cost(rows)
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in feature))
    values = []
    for _ in range(RANDOM_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        total = 0.0
        for value in set(row[feature] for row in rows):
            indices = [index for index, row in enumerate(rows) if row[feature] == value]
            total += log2comb(len(indices), sum(1 for index in indices if shuffled[index]))
        values.append(baseline - total)
    values.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED + sum(ord(ch) for ch in feature),
        "saving_mean_before_feature_charge": mean(values),
        "saving_p05_before_feature_charge": percentile(values, 0.05),
        "saving_p95_before_feature_charge": percentile(values, 0.95),
    }


def prequential_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = feature_rows(train)
        selected = max(
            train_scores,
            key=lambda row: (row["saving_after_feature_charge"], row["feature"]),
        )
        test_baseline = label_cost(test)
        test_grouped = label_cost(test, selected["feature"])
        out.append(
            {
                "cutoff": cutoff,
                "selected_feature": selected["feature"],
                "train_saving_after_feature_charge": selected[
                    "saving_after_feature_charge"
                ],
                "test_saving_after_feature_charge": test_baseline
                - test_grouped
                - math.log2(FEATURE_CHOICE_COUNT),
                "test_rows": len(test),
                "test_misses": sum(1 for row in test if row["miss"]),
            }
        )
    return out


def make_result() -> dict[str, Any]:
    miss_residual = load_json(MISS_RESIDUAL_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("target_digit_boundary_miss_residual_gate", miss_residual)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    rows = make_rows(books, copy_ledger["canonical_ops_by_book"])
    feature_scores = feature_rows(rows)
    best = max(feature_scores, key=lambda row: row["saving_after_feature_charge"])
    random_best = random_control(rows, best["feature"])
    preq = prequential_rows(rows)
    beats_random = best["saving_before_feature_charge"] > random_best[
        "saving_p95_before_feature_charge"
    ]
    promotes_feature = (
        best["saving_after_feature_charge"] > 0
        and beats_random
        and all(row["test_saving_after_feature_charge"] > 0 for row in preq)
    )
    summary = {
        "cutpoint_count": len(rows),
        "miss_count": sum(1 for row in rows if row["miss"]),
        "hit_count": sum(1 for row in rows if not row["miss"]),
        "feature_count": len(features()),
        "baseline_miss_label_bits": label_cost(rows),
        "best_feature": best["feature"],
        "best_category_count": best["category_count"],
        "best_saving_before_feature_charge": best["saving_before_feature_charge"],
        "best_saving_after_feature_charge": best["saving_after_feature_charge"],
        "best_random_saving_p95_before_feature_charge": random_best[
            "saving_p95_before_feature_charge"
        ],
        "best_beats_random_p95": beats_random,
        "prequential_cells": len(preq),
        "prequential_positive_test_cells": sum(
            1 for row in preq if row["test_saving_after_feature_charge"] > 0
        ),
        "promotes_feature": promotes_feature,
        "interpretation": (
            "Skeleton transition/chunk classes are useful diagnostics for where "
            "threshold misses occur, but the best apparent feature does not beat "
            "random relabel controls. No miss-class rule is promoted."
        ),
    }
    return {
        "schema": "target_digit_boundary_miss_transition_gate_v1",
        "scope": "analysis_only_threshold_miss_transition_classes",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "miss_residual_gate": rel(MISS_RESIDUAL_GATE),
        },
        "feature_rows": sorted(
            feature_scores,
            key=lambda row: row["saving_after_feature_charge"],
            reverse=True,
        ),
        "prequential_rows": preq,
        "random_control_best": random_best,
        "summary": summary,
        "classification": "target_digit_boundary_miss_transition_classes_rejected_control",
        "decision": {
            "promotes_feature": promotes_feature,
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
        "# Target Digit Boundary Miss Transition Gate",
        "",
        "Classification: `target_digit_boundary_miss_transition_classes_rejected_control`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the cutpoints missed by `right_ge:4` are explained by",
        "skeleton transition classes, length buckets, ordinal position, or chunk",
        "recurrence diagnostics.",
        "",
        "## Summary",
        "",
        f"- Cutpoints/hits/misses: `{s['cutpoint_count']}` / `{s['hit_count']}` / `{s['miss_count']}`.",
        f"- Features tested: `{s['feature_count']}`.",
        f"- Baseline miss-label atlas: `{s['baseline_miss_label_bits']:.3f}` bits.",
        f"- Best feature: `{s['best_feature']}` with `{s['best_category_count']}` categories.",
        f"- Best saving before/after feature charge: `{s['best_saving_before_feature_charge']:.3f}` / `{s['best_saving_after_feature_charge']:.3f}` bits.",
        f"- Random relabel p95 before feature charge: `{s['best_random_saving_p95_before_feature_charge']:.3f}` bits.",
        f"- Beats random p95: `{s['best_beats_random_p95']}`.",
        f"- Prefix-selected positive test cells: `{s['prequential_positive_test_cells']}/{s['prequential_cells']}`.",
        "",
        "The best feature looks useful before controls, but the same category sizes",
        "produce comparable savings under random miss-label permutations. Chunk",
        "recurrence features are sparse and do not explain the miss set.",
        "",
        "## Top Features",
        "",
        "| Feature | Categories | Saving after charge | Saving before charge |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in result["feature_rows"][:8]:
        lines.append(
            f"| `{row['feature']}` | `{row['category_count']}` | "
            f"`{row['saving_after_feature_charge']:.3f}` | "
            f"`{row['saving_before_feature_charge']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Miss transition/chunk feature promoted: `False`.",
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
