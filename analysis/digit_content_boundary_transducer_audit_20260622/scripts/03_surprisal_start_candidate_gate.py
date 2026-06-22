#!/usr/bin/env python3
"""Surprisal start-candidate gate.

The previous candidate-ranking gate found a small net bit reduction, but weak
controls. This gate asks whether the already documented digit-boundary
surprisal clue improves the internal-start candidate set.

Two classes are kept separate:

- decoder-visible scores: use only digits that have already been emitted at the
  candidate boundary;
- diagnostic scores: look at the next digit and are therefore not promotable as
  a standalone generator.

The codec is the same candidate+correction ledger as gate 02:

    log2(C(K, hits)) + log2(C(N-K, misses))

against the exact-count composition baseline log2(C(N, starts)).
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "digit_content_boundary_transducer_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
CONTROL_LEDGER = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
START_CANDIDATE_GATE = TEST_RESULTS / "02_start_candidate_ranking_gate.json"

JSON_OUT = TEST_RESULTS / "03_surprisal_start_candidate_gate.json"
MD_OUT = TEST_RESULTS / "03_surprisal_start_candidate_gate.md"
FINAL_OUT = FRONT / "reports" / "final_digit_content_boundary_transducer_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
RATE_POLICIES = [0.02, 0.04, 0.08, 0.12, 0.16]
RANDOM_SEED = 46920260622 + 3
RANDOM_TRIALS = 500
ALPHA = 0.5
DIGITS = "0123456789"

DECODER_VISIBLE_FAMILIES = [
    "left_surprisal",
    "left_peak2",
    "left_peak3",
    "left_ge4_then_suffix4",
    "suffix4_then_left_surprisal",
    "left_surprisal_then_pos",
]
DIAGNOSTIC_FAMILIES = [
    "right_surprisal_diagnostic",
    "right_ge4_diagnostic",
    "sum2_surprisal_diagnostic",
    "delta_right_left_diagnostic",
]
FAMILIES = DECODER_VISIBLE_FAMILIES + DIAGNOSTIC_FAMILIES


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def log2_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    if k == 0 or k == n:
        return 0.0
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / math.log(2)


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


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


def digit_surprisal(
    digit: str,
    prefix: str,
    counts: dict[tuple[str, str], Counter[str]],
    global_counts: Counter[str],
) -> float:
    counter = counts.get(prev2_context(prefix), global_counts)
    total = sum(counter.values())
    probability = (counter[digit] + ALPHA) / (total + ALPHA * len(DIGITS))
    return -math.log2(probability)


def book_surprisals(
    books: dict[int, str],
    book: int,
    counts: dict[tuple[str, str], Counter[str]],
    global_counts: Counter[str],
) -> list[float]:
    prefix = ""
    values = []
    for digit in books[book]:
        values.append(digit_surprisal(digit, prefix, counts, global_counts))
        prefix += digit
    return values


def build_start_labels(ledger: dict[str, Any]) -> dict[int, set[int]]:
    starts: dict[int, set[int]] = defaultdict(set)
    for row in ledger["ledger_rows"]:
        book = int(row["book"])
        start = int(row["target_start"])
        if start:
            starts[book].add(start)
    return starts


def prior_material_for(books: dict[int, str], book: int, pos: int) -> str:
    return "".join(books[idx] for idx in range(book)) + books[book][:pos]


def pos_fraction(pos: int, length: int) -> float:
    return pos / max(1, length)


def build_rows(
    books: dict[int, str],
    starts: dict[int, set[int]],
    train_books: list[int],
    eval_books: list[int],
) -> dict[int, list[dict[str, Any]]]:
    counts, global_counts = train_prev2(books, train_books)
    rows_by_book: dict[int, list[dict[str, Any]]] = {}
    for book in eval_books:
        text = books[book]
        surprisals = book_surprisals(books, book, counts, global_counts)
        rows = []
        for pos in range(1, len(text)):
            prior = prior_material_for(books, book, pos)
            prefix = text[:pos]
            suffix4 = prefix[-4:] if len(prefix) >= 4 else ""
            left_window = surprisals[max(0, pos - 3) : pos]
            rows.append(
                {
                    "book": book,
                    "is_start": pos in starts.get(book, set()),
                    "left_peak2": max(surprisals[max(0, pos - 2) : pos]),
                    "left_peak3": max(left_window),
                    "left_surprisal": surprisals[pos - 1],
                    "pos": pos,
                    "pos_fraction": pos_fraction(pos, len(text)),
                    "right_surprisal": surprisals[pos],
                    "suffix4_seen": bool(suffix4 and suffix4 in prior[:-1]),
                }
            )
        rows_by_book[book] = rows
    return rows_by_book


def score(row: dict[str, Any], family: str) -> float:
    if family == "left_surprisal":
        return row["left_surprisal"]
    if family == "left_peak2":
        return row["left_peak2"]
    if family == "left_peak3":
        return row["left_peak3"]
    if family == "left_ge4_then_suffix4":
        return float(row["left_surprisal"] >= 4.0) * 10.0 + float(row["suffix4_seen"])
    if family == "suffix4_then_left_surprisal":
        return float(row["suffix4_seen"]) * 10.0 + row["left_surprisal"]
    if family == "left_surprisal_then_pos":
        return row["left_surprisal"] - 0.1 * row["pos_fraction"]
    if family == "right_surprisal_diagnostic":
        return row["right_surprisal"]
    if family == "right_ge4_diagnostic":
        return float(row["right_surprisal"] >= 4.0) * 10.0 + row["right_surprisal"]
    if family == "sum2_surprisal_diagnostic":
        return row["left_surprisal"] + row["right_surprisal"]
    if family == "delta_right_left_diagnostic":
        return row["right_surprisal"] - row["left_surprisal"]
    raise KeyError(family)


def rank_book(rows: list[dict[str, Any]], family: str) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (-score(row, family), row["pos"]))


def candidate_cost_for_book(ranked: list[dict[str, Any]], rate: float) -> dict[str, Any]:
    n = len(ranked)
    starts = {row["pos"] for row in ranked if row["is_start"]}
    start_count = len(starts)
    k = min(n, max(1, int(round(n * rate))))
    candidates = {row["pos"] for row in ranked[:k]}
    hits = len(starts & candidates)
    misses = start_count - hits
    baseline_bits = log2_choose(n, start_count)
    candidate_bits = log2_choose(k, hits) + log2_choose(n - k, misses)
    return {
        "baseline_bits": baseline_bits,
        "candidate_bits": candidate_bits,
        "hits": hits,
        "k": k,
        "misses": misses,
        "positions": n,
        "starts": start_count,
    }


def candidate_cost(rows_by_book: dict[int, list[dict[str, Any]]], books: list[int], family: str, rate: float) -> dict[str, Any]:
    total = Counter()
    candidate_bits = 0.0
    baseline_bits = 0.0
    for book in books:
        cost = candidate_cost_for_book(rank_book(rows_by_book[book], family), rate)
        candidate_bits += cost["candidate_bits"]
        baseline_bits += cost["baseline_bits"]
        total.update(
            {
                "hits": cost["hits"],
                "k": cost["k"],
                "misses": cost["misses"],
                "positions": cost["positions"],
                "starts": cost["starts"],
            }
        )
    return {
        **dict(total),
        "baseline_bits": baseline_bits,
        "candidate_bits": candidate_bits,
        "delta_vs_baseline": candidate_bits - baseline_bits,
        "recall": total["hits"] / max(1, total["starts"]),
    }


def selection_penalty(families: list[str]) -> float:
    return math.log2(len(families) * len(RATE_POLICIES))


def select_policy(
    rows_by_book: dict[int, list[dict[str, Any]]],
    train_books: list[int],
    families: list[str],
) -> dict[str, Any]:
    candidates = []
    for family in families:
        for rate in RATE_POLICIES:
            result = candidate_cost(rows_by_book, train_books, family, rate)
            candidates.append(
                {
                    "family": family,
                    "rate": rate,
                    "train_bits_with_policy": result["candidate_bits"] + selection_penalty(families),
                    "train_delta_vs_baseline": result["delta_vs_baseline"],
                }
            )
    return min(candidates, key=lambda row: (row["train_bits_with_policy"], row["family"], row["rate"]))


def random_candidate_controls(
    rows_by_book: dict[int, list[dict[str, Any]]],
    books: list[int],
    rate: float,
    real_baseline_bits: float,
    seed_offset: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    deltas = []
    for _ in range(RANDOM_TRIALS):
        candidate_bits = 0.0
        for book in books:
            rows = rows_by_book[book]
            n = len(rows)
            starts = {row["pos"] for row in rows if row["is_start"]}
            start_count = len(starts)
            k = min(n, max(1, int(round(n * rate))))
            candidates = set(rng.sample([row["pos"] for row in rows], k))
            hits = len(starts & candidates)
            misses = start_count - hits
            candidate_bits += log2_choose(k, hits) + log2_choose(n - k, misses)
        deltas.append(candidate_bits - real_baseline_bits)
    return {
        "delta_mean": sum(deltas) / len(deltas),
        "delta_p05": percentile(deltas, 5),
        "delta_p50": percentile(deltas, 50),
        "delta_p95": percentile(deltas, 95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def cutoff_gate(
    cutoff: int,
    books: dict[int, str],
    starts: dict[int, set[int]],
    seed_offset: int,
    families: list[str],
) -> dict[str, Any]:
    train_books = [book for book in range(10, cutoff)]
    test_books = [book for book in range(cutoff, 70)]
    train_rows = build_rows(books, starts, train_books, train_books)
    selected = select_policy(train_rows, train_books, families)
    test_rows = build_rows(books, starts, train_books, test_books)
    result = candidate_cost(test_rows, test_books, selected["family"], selected["rate"])
    controls = random_candidate_controls(
        test_rows,
        test_books,
        selected["rate"],
        result["baseline_bits"],
        seed_offset,
    )
    result.update(
        {
            "beats_random_p05": result["delta_vs_baseline"] < controls["delta_p05"],
            "family": selected["family"],
            "rate": selected["rate"],
            "random_candidate_controls": controls,
            "train_bits_with_policy": selected["train_bits_with_policy"],
            "train_delta_vs_baseline": selected["train_delta_vs_baseline"],
        }
    )
    return {
        "cutoff": cutoff,
        "selected": result,
        "test_books": test_books,
        "train_books": train_books,
    }


def summarize(rows: list[dict[str, Any]], policy_bits: float) -> dict[str, Any]:
    selected = [row["selected"] for row in rows]
    total_candidate_before_policy = sum(row["candidate_bits"] for row in selected)
    total_candidate = total_candidate_before_policy + policy_bits
    total_baseline = sum(row["baseline_bits"] for row in selected)
    total_hits = sum(row["hits"] for row in selected)
    total_starts = sum(row["starts"] for row in selected)
    total_misses = sum(row["misses"] for row in selected)
    total_k = sum(row["k"] for row in selected)
    return {
        "beats_random_p05_cells": sum(row["beats_random_p05"] for row in selected),
        "policy_bits": policy_bits,
        "total_baseline_bits": total_baseline,
        "total_candidate_bits": total_candidate,
        "total_candidate_bits_before_policy": total_candidate_before_policy,
        "total_candidate_positions": total_k,
        "total_delta_vs_baseline": total_candidate - total_baseline,
        "total_hits": total_hits,
        "total_misses": total_misses,
        "total_recall": total_hits / max(1, total_starts),
        "total_starts": total_starts,
    }


def make_result() -> dict[str, Any]:
    previous = load_json(START_CANDIDATE_GATE)
    ledger = load_json(CONTROL_LEDGER)
    assert_boundary("start_candidate_gate", previous)
    assert_boundary("unified_residual_control_ledger", ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    starts = build_start_labels(ledger)
    visible_rows = [
        cutoff_gate(cutoff, books, starts, seed_offset=index, families=DECODER_VISIBLE_FAMILIES)
        for index, cutoff in enumerate(CUTOFFS)
    ]
    diagnostic_rows = [
        cutoff_gate(cutoff, books, starts, seed_offset=100 + index, families=DIAGNOSTIC_FAMILIES)
        for index, cutoff in enumerate(CUTOFFS)
    ]
    visible_summary = summarize(visible_rows, selection_penalty(DECODER_VISIBLE_FAMILIES))
    diagnostic_summary = summarize(diagnostic_rows, selection_penalty(DIAGNOSTIC_FAMILIES))
    visible_promoted = (
        visible_summary["total_delta_vs_baseline"] < 0
        and visible_summary["beats_random_p05_cells"] >= 4
        and visible_summary["total_hits"] > 0
    )
    visible_weak = (
        visible_summary["total_delta_vs_baseline"] < 0
        and visible_summary["beats_random_p05_cells"] >= 3
    )
    classification = (
        "PROMOTED_DECODER_VISIBLE_SURPRISAL_START_CANDIDATE"
        if visible_promoted
        else "WEAK_DECODER_VISIBLE_SURPRISAL_START_CANDIDATE"
        if visible_weak
        else "SURPRISAL_START_CANDIDATE_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "cutoff_rows": {
            "decoder_visible": visible_rows,
            "diagnostic_target_conditioned": diagnostic_rows,
        },
        "decision": {
            "diagnostic_scores_promotable": False,
            "generator_promoted": False,
            "grants_exact_internal_starts": False,
            "grants_operation_token_sequence": False,
            "grants_target_conditioned_copy_availability": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "start_candidate_gate": rel(START_CANDIDATE_GATE),
            "unified_residual_control_ledger": rel(CONTROL_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "surprisal_start_candidate_gate.v1",
        "scope": "analysis_only_digit_surprisal_start_candidate_ranking",
        "summary": {
            "decoder_visible": visible_summary,
            "diagnostic_target_conditioned": diagnostic_summary,
            "interpretation": (
                "Decoder-visible surprisal does not pass promotion controls. "
                "Target-conditioned right-surprisal remains a diagnostic clue only."
            ),
        },
        "translation_delta": "NONE",
    }


def append_table(lines: list[str], rows: list[dict[str, Any]]) -> None:
    lines.extend(
        [
            "| Cutoff | Family | Rate | K | Hits | Misses | Candidate bits | Baseline bits | Delta | Random p05 |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in rows:
        selected = row["selected"]
        lines.append(
            f"| `{row['cutoff']}` | `{selected['family']}` | `{selected['rate']:.3f}` | "
            f"`{selected['k']}` | `{selected['hits']}` | `{selected['misses']}` | "
            f"`{selected['candidate_bits']:.3f}` | `{selected['baseline_bits']:.3f}` | "
            f"`{selected['delta_vs_baseline']:.3f}` | `{selected['beats_random_p05']}` |"
        )


def write_markdown(result: dict[str, Any]) -> None:
    visible = result["summary"]["decoder_visible"]
    diagnostic = result["summary"]["diagnostic_target_conditioned"]
    lines = [
        "# Surprisal Start Candidate Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether the digit-boundary surprisal clue improves the internal-start "
        "candidate ledger. Decoder-visible scores are separated from target-conditioned "
        "right-surprisal diagnostics.",
        "",
        "## Decoder-Visible Summary",
        "",
        f"- Candidate bits after policy: `{visible['total_candidate_bits']:.3f}`.",
        f"- Exact start composition baseline bits: `{visible['total_baseline_bits']:.3f}`.",
        f"- Delta vs baseline: `{visible['total_delta_vs_baseline']:.3f}` bits.",
        f"- Cells beating random top-K p05: `{visible['beats_random_p05_cells']}/5`.",
        f"- Candidate positions selected: `{visible['total_candidate_positions']}`.",
        f"- Start hits: `{visible['total_hits']}/{visible['total_starts']}`.",
        f"- Misses requiring correction: `{visible['total_misses']}`.",
        f"- Recall: `{visible['total_recall']:.3f}`.",
        "",
        "## Diagnostic Target-Conditioned Summary",
        "",
        f"- Candidate bits after policy: `{diagnostic['total_candidate_bits']:.3f}`.",
        f"- Exact start composition baseline bits: `{diagnostic['total_baseline_bits']:.3f}`.",
        f"- Delta vs baseline: `{diagnostic['total_delta_vs_baseline']:.3f}` bits.",
        f"- Cells beating random top-K p05: `{diagnostic['beats_random_p05_cells']}/5`.",
        f"- Start hits: `{diagnostic['total_hits']}/{diagnostic['total_starts']}`.",
        "",
        "## Decoder-Visible Prefix Holdouts",
        "",
    ]
    append_table(lines, result["cutoff_rows"]["decoder_visible"])
    lines.extend(["", "## Diagnostic Prefix Holdouts", ""])
    append_table(lines, result["cutoff_rows"]["diagnostic_target_conditioned"])
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Only decoder-visible scores can be promoted. Right-surprisal and sum2 "
            "diagnostics look at the next digit and therefore remain target-conditioned "
            "candidate diagnostics, not an executable start generator.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    visible = result["summary"]["decoder_visible"]
    diagnostic = result["summary"]["diagnostic_target_conditioned"]
    lines = [
        "# Final Digit Content Boundary Transducer Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can decoder-visible digit/content signals rank candidate internal starts "
        "well enough to reduce the paid start-position dependency?",
        "",
        "## Result",
        "",
        f"The decoder-visible surprisal candidate codec costs `{visible['total_candidate_bits']:.3f}` bits "
        f"versus `{visible['total_baseline_bits']:.3f}` exact start-composition bits "
        f"(`{visible['total_delta_vs_baseline']:.3f}`). It beats random top-K p05 in "
        f"`{visible['beats_random_p05_cells']}/5` cells and captures "
        f"`{visible['total_hits']}/{visible['total_starts']}` starts, leaving "
        f"`{visible['total_misses']}` missed-start corrections.",
        "",
        f"The target-conditioned diagnostic right/sum surprisal route costs "
        f"`{diagnostic['total_candidate_bits']:.3f}` bits versus "
        f"`{diagnostic['total_baseline_bits']:.3f}` (`{diagnostic['total_delta_vs_baseline']:.3f}`), "
        f"with `{diagnostic['beats_random_p05_cells']}/5` random-control cells. "
        "It is not promotable because it looks at the next digit.",
        "",
        "## Decision",
        "",
        "The digit-boundary surprisal clue remains useful diagnostically, but it "
        "does not become an executable decoder-visible start program. Row0, "
        "plaintext, translation, and compression_bound remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_all_position_boundary_transducer_gate.py](../scripts/01_all_position_boundary_transducer_gate.py)",
        "- [02_start_candidate_ranking_gate.py](../scripts/02_start_candidate_ranking_gate.py)",
        "- [03_surprisal_start_candidate_gate.py](../scripts/03_surprisal_start_candidate_gate.py)",
        "- [01_all_position_boundary_transducer_gate.json](test_results/01_all_position_boundary_transducer_gate.json)",
        "- [02_start_candidate_ranking_gate.json](test_results/02_start_candidate_ranking_gate.json)",
        "- [02_start_candidate_ranking_gate.md](test_results/02_start_candidate_ranking_gate.md)",
        "- [03_surprisal_start_candidate_gate.json](test_results/03_surprisal_start_candidate_gate.json)",
        "- [03_surprisal_start_candidate_gate.md](test_results/03_surprisal_start_candidate_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
