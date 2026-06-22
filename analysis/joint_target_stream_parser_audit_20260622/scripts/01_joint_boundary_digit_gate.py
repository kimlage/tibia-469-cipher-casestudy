from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
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
ROUTE_REVIEW = (
    ROOT
    / "analysis"
    / "skeleton_generation_route_review_20260622"
    / "reports"
    / "test_results"
    / "01_skeleton_generation_route_review.json"
)

OUT_STEM = "01_joint_boundary_digit_gate"
ALPHA = 0.5
DIGITS = "0123456789"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
ORDERS = [0, 1, 2, 3]


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


def context(prefix: str, order: int) -> tuple[str, ...]:
    if order == 0:
        return ("GLOBAL",)
    if len(prefix) < order:
        return tuple(["BOS"] * (order - len(prefix)) + list(prefix))
    return tuple(prefix[-order:])


def train_counts(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
    book_ids: list[int],
    order: int,
) -> dict[str, Any]:
    digit_counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    boundary_counts: dict[tuple[str, ...], Counter[int]] = defaultdict(Counter)
    pair_counts: dict[tuple[str, ...], Counter[tuple[int, str]]] = defaultdict(Counter)
    global_digit = Counter()
    global_boundary = Counter()
    global_pair = Counter()
    for book in book_ids:
        digits = books[book]
        flags = boundary_flags(book, len(digits), ops_by_book)
        prefix = ""
        for index, digit in enumerate(digits):
            flag = flags[index]
            ctx = context(prefix, order)
            digit_counts[ctx][digit] += 1
            boundary_counts[ctx][flag] += 1
            pair_counts[ctx][(flag, digit)] += 1
            global_digit[digit] += 1
            global_boundary[flag] += 1
            global_pair[(flag, digit)] += 1
            prefix += digit
    return {
        "digit_counts": digit_counts,
        "boundary_counts": boundary_counts,
        "pair_counts": pair_counts,
        "global_digit": global_digit,
        "global_boundary": global_boundary,
        "global_pair": global_pair,
    }


def nll(counter: Counter[Any], symbol: Any, alpha: float, alphabet_size: int) -> float:
    return -math.log2(
        (counter[symbol] + alpha) / (sum(counter.values()) + alpha * alphabet_size)
    )


def score_model(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
    train_ids: list[int],
    test_ids: list[int],
    order: int,
    model: str,
) -> dict[str, Any]:
    counts = train_counts(books, ops_by_book, train_ids, order)
    bits = 0.0
    digit_count = 0
    boundary_count = 0
    for book in test_ids:
        digits = books[book]
        flags = boundary_flags(book, len(digits), ops_by_book)
        prefix = ""
        for index, digit in enumerate(digits):
            flag = flags[index]
            ctx = context(prefix, order)
            if model == "separate_global_boundary":
                bits += nll(
                    counts["digit_counts"].get(ctx, counts["global_digit"]),
                    digit,
                    ALPHA,
                    len(DIGITS),
                )
                bits += nll(counts["global_boundary"], flag, ALPHA, 2)
            elif model == "separate_context_boundary":
                bits += nll(
                    counts["digit_counts"].get(ctx, counts["global_digit"]),
                    digit,
                    ALPHA,
                    len(DIGITS),
                )
                bits += nll(
                    counts["boundary_counts"].get(ctx, counts["global_boundary"]),
                    flag,
                    ALPHA,
                    2,
                )
            elif model == "joint_pair_context":
                bits += nll(
                    counts["pair_counts"].get(ctx, counts["global_pair"]),
                    (flag, digit),
                    ALPHA,
                    len(DIGITS) * 2,
                )
            else:
                raise KeyError(model)
            digit_count += 1
            boundary_count += flag
            prefix += digit
    return {
        "order": order,
        "model": model,
        "bits": bits,
        "digit_count": digit_count,
        "boundary_count": boundary_count,
    }


def cutoff_rows(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    for order in ORDERS:
        for cutoff in PREFIX_CUTOFFS:
            train_ids = [book for book in sorted(books) if book < cutoff]
            test_ids = [book for book in range(cutoff, 70)]
            baseline = score_model(
                books,
                ops_by_book,
                train_ids,
                test_ids,
                order,
                "separate_global_boundary",
            )
            for model in ["separate_context_boundary", "joint_pair_context"]:
                scored = score_model(books, ops_by_book, train_ids, test_ids, order, model)
                rows.append(
                    {
                        "cutoff": cutoff,
                        "order": order,
                        "model": model,
                        "test_digit_count": scored["digit_count"],
                        "test_boundary_count": scored["boundary_count"],
                        "baseline_bits": baseline["bits"],
                        "model_bits": scored["bits"],
                        "gain_vs_baseline_bits": baseline["bits"] - scored["bits"],
                    }
                )
    return rows


def aggregate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for order in ORDERS:
        for model in ["separate_context_boundary", "joint_pair_context"]:
            subset = [row for row in rows if row["order"] == order and row["model"] == model]
            out.append(
                {
                    "order": order,
                    "model": model,
                    "aggregate_gain_vs_baseline_bits": sum(
                        row["gain_vs_baseline_bits"] for row in subset
                    ),
                    "positive_cells": sum(
                        1 for row in subset if row["gain_vs_baseline_bits"] > 0
                    ),
                    "cells": len(subset),
                    "aggregate_model_bits": sum(row["model_bits"] for row in subset),
                    "aggregate_baseline_bits": sum(row["baseline_bits"] for row in subset),
                }
            )
    return out


def make_result() -> dict[str, Any]:
    route_review = load_json(ROUTE_REVIEW)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("skeleton_generation_route_review", route_review)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    rows = cutoff_rows(books, copy_ledger["canonical_ops_by_book"])
    aggregates = aggregate_rows(rows)
    nontrivial = [
        row
        for row in aggregates
        if not (row["model"] == "separate_context_boundary" and row["order"] == 0)
    ]
    best = max(nontrivial, key=lambda row: row["aggregate_gain_vs_baseline_bits"])
    promotes_joint_parser = (
        best["aggregate_gain_vs_baseline_bits"] > 0
        and best["positive_cells"] == best["cells"]
    )
    summary = {
        "cutoff_count": len(PREFIX_CUTOFFS),
        "orders_tested": ORDERS,
        "model_count": 2,
        "best_nontrivial_model": f"{best['model']}_order{best['order']}",
        "best_aggregate_gain_vs_baseline_bits": best["aggregate_gain_vs_baseline_bits"],
        "best_positive_cells": best["positive_cells"],
        "best_cells": best["cells"],
        "promotes_joint_parser": promotes_joint_parser,
        "interpretation": (
            "A simple joint emission of boundary flag and digit does not beat "
            "a factorized prevN digit model plus global boundary-rate baseline "
            "under prefix holdout. This falsifies the simplest joint target-stream "
            "parser route; a future latent-state parser must add real state, not "
            "just pair the current boundary flag with the current digit."
        ),
    }
    return {
        "schema": "joint_boundary_digit_gate_v1",
        "scope": "analysis_only_joint_target_stream_parser_first_gate",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "route_review": rel(ROUTE_REVIEW),
        },
        "cutoff_rows": rows,
        "aggregate_rows": aggregates,
        "summary": summary,
        "classification": "joint_boundary_digit_pair_model_rejected",
        "decision": {
            "promotes_joint_parser": promotes_joint_parser,
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
        "# Joint Boundary Digit Gate",
        "",
        "Classification: `joint_boundary_digit_pair_model_rejected`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test the simplest joint target-stream/parser route: emit a boundary flag",
        "and the next digit together under prefix-trained contexts, instead of",
        "choosing boundaries after the target text is known.",
        "",
        "## Summary",
        "",
        f"- Prefix cutoffs tested: `{s['cutoff_count']}`.",
        f"- Context orders tested: `{s['orders_tested']}`.",
        f"- Models tested per order: `{s['model_count']}`.",
        f"- Best nontrivial model: `{s['best_nontrivial_model']}`.",
        f"- Best aggregate gain vs factorized global-boundary baseline: `{s['best_aggregate_gain_vs_baseline_bits']:.3f}` bits.",
        f"- Positive cells for best model: `{s['best_positive_cells']}/{s['best_cells']}`.",
        f"- Promotes joint parser: `{s['promotes_joint_parser']}`.",
        "",
        s["interpretation"],
        "",
        "## Aggregate Scoreboard",
        "",
        "| Model | Order | Aggregate gain | Positive cells |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in sorted(
        result["aggregate_rows"],
        key=lambda item: item["aggregate_gain_vs_baseline_bits"],
        reverse=True,
    ):
        lines.append(
            f"| `{row['model']}` | `{row['order']}` | "
            f"`{row['aggregate_gain_vs_baseline_bits']:.3f}` | "
            f"`{row['positive_cells']}/{row['cells']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Simple joint boundary+digit pair emission is rejected.",
            "- No parser/generator is promoted.",
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
