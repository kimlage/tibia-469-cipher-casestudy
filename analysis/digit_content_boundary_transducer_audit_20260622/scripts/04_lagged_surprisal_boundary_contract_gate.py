#!/usr/bin/env python3
"""Lagged-surprisal boundary contract gate.

Gate 03 showed a sharp asymmetry: decoder-visible surprisal does not pass
controls, while right-surprisal does. This gate tests whether that stronger
signal can be reinterpreted as a one-digit-lag boundary annotation contract:
the program emits the first digit of a new segment, then marks the operation
start after seeing that digit.

That timing is weaker than an online copy/literal decoder. For copy operations,
recognizing the start one digit late externalizes the first copied digit into
the innovation stream before the copy can begin. This gate therefore charges an
explicit one-digit lag tax for each copy start recovered by the lagged policy.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "digit_content_boundary_transducer_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

SCRIPT03 = FRONT / "scripts" / "03_surprisal_start_candidate_gate.py"
GATE03 = TEST_RESULTS / "03_surprisal_start_candidate_gate.json"
CONTROL_LEDGER = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

JSON_OUT = TEST_RESULTS / "04_lagged_surprisal_boundary_contract_gate.json"
MD_OUT = TEST_RESULTS / "04_lagged_surprisal_boundary_contract_gate.md"
FINAL_OUT = FRONT / "reports" / "final_digit_content_boundary_transducer_audit.md"

RANDOM_SEED = 46920260622 + 4
RANDOM_TRIALS = 500
UNIFORM_DIGIT_BITS = math.log2(10)


def load_gate03_module() -> Any:
    spec = importlib.util.spec_from_file_location("surprisal_start_candidate_gate", SCRIPT03)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCRIPT03}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def op_lookup(ledger: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    out = {}
    for row in ledger["ledger_rows"]:
        book = int(row["book"])
        start = int(row["target_start"])
        if start:
            out[(book, start)] = row
    return out


def candidate_positions_for_book(module: Any, rows: list[dict[str, Any]], family: str, rate: float) -> set[int]:
    ranked = module.rank_book(rows, family)
    k = min(len(ranked), max(1, int(round(len(ranked) * rate))))
    return {int(row["pos"]) for row in ranked[:k]}


def evaluate_book(
    rows: list[dict[str, Any]],
    candidates: set[int],
    ops_by_start: dict[tuple[int, int], dict[str, Any]],
) -> dict[str, Any]:
    if not rows:
        return {}
    book = int(rows[0]["book"])
    starts = {int(row["pos"]) for row in rows if row["is_start"]}
    hits = starts & candidates
    misses = starts - candidates
    false_positives = candidates - starts
    copy_hits = 0
    literal_hits = 0
    invalid_copy_lag = 0
    copy_misses = 0
    literal_misses = 0
    for pos in hits:
        op = ops_by_start[(book, pos)]
        if op["op_type"] == "copy":
            copy_hits += 1
            invalid_copy_lag += int(int(op["length"]) <= 1)
        else:
            literal_hits += 1
    for pos in misses:
        op = ops_by_start[(book, pos)]
        if op["op_type"] == "copy":
            copy_misses += 1
        else:
            literal_misses += 1
    n = len(rows)
    k = len(candidates)
    baseline_bits = log2_choose(n, len(starts))
    candidate_bits = log2_choose(k, len(hits)) + log2_choose(n - k, len(misses))
    lag_tax_bits = copy_hits * UNIFORM_DIGIT_BITS
    return {
        "baseline_bits": baseline_bits,
        "candidate_bits": candidate_bits,
        "copy_hits": copy_hits,
        "copy_misses": copy_misses,
        "false_positives": len(false_positives),
        "hits": len(hits),
        "invalid_copy_lag": invalid_copy_lag,
        "k": k,
        "lag_tax_bits": lag_tax_bits,
        "lagged_total_bits": candidate_bits + lag_tax_bits,
        "literal_hits": literal_hits,
        "literal_misses": literal_misses,
        "misses": len(misses),
        "positions": n,
        "starts": len(starts),
    }


def random_controls(
    rows_by_book: dict[int, list[dict[str, Any]]],
    test_books: list[int],
    rate: float,
    baseline_bits: float,
    ops_by_start: dict[tuple[int, int], dict[str, Any]],
    seed_offset: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    deltas = []
    for _ in range(RANDOM_TRIALS):
        total = 0.0
        for book in test_books:
            rows = rows_by_book[book]
            k = min(len(rows), max(1, int(round(len(rows) * rate))))
            candidates = set(rng.sample([int(row["pos"]) for row in rows], k))
            total += evaluate_book(rows, candidates, ops_by_start)["lagged_total_bits"]
        deltas.append(total - baseline_bits)
    return {
        "delta_mean": sum(deltas) / len(deltas),
        "delta_p05": percentile(deltas, 5),
        "delta_p50": percentile(deltas, 50),
        "delta_p95": percentile(deltas, 95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = Counter()
    floats = defaultdict(float)
    for row in rows:
        for key, value in row.items():
            if key.endswith("_bits"):
                floats[key] += float(value)
            elif isinstance(value, int):
                totals[key] += value
    return {**dict(totals), **dict(floats)}


def cutoff_gate(
    module: Any,
    cutoff_row: dict[str, Any],
    books: dict[int, str],
    starts: dict[int, set[int]],
    ops_by_start: dict[tuple[int, int], dict[str, Any]],
    seed_offset: int,
) -> dict[str, Any]:
    cutoff = int(cutoff_row["cutoff"])
    selected = cutoff_row["selected"]
    family = selected["family"]
    rate = float(selected["rate"])
    train_books = [int(book) for book in cutoff_row["train_books"]]
    test_books = [int(book) for book in cutoff_row["test_books"]]
    rows_by_book = module.build_rows(books, starts, train_books, test_books)
    book_rows = []
    for book in test_books:
        candidates = candidate_positions_for_book(module, rows_by_book[book], family, rate)
        book_rows.append(evaluate_book(rows_by_book[book], candidates, ops_by_start))
    summary = aggregate(book_rows)
    summary["delta_vs_baseline_after_lag_tax"] = (
        summary["lagged_total_bits"] - summary["baseline_bits"]
    )
    controls = random_controls(
        rows_by_book,
        test_books,
        rate,
        summary["baseline_bits"],
        ops_by_start,
        seed_offset,
    )
    summary.update(
        {
            "beats_random_p05_after_lag_tax": summary["delta_vs_baseline_after_lag_tax"]
            < controls["delta_p05"],
            "family": family,
            "random_lagged_controls": controls,
            "rate": rate,
        }
    )
    return {
        "cutoff": cutoff,
        "selected": summary,
        "test_books": test_books,
        "train_books": train_books,
    }


def make_result() -> dict[str, Any]:
    module = load_gate03_module()
    gate03 = load_json(GATE03)
    ledger = load_json(CONTROL_LEDGER)
    assert_boundary("surprisal_start_candidate_gate", gate03)
    assert_boundary("unified_residual_control_ledger", ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    starts = module.build_start_labels(ledger)
    ops_by_start = op_lookup(ledger)
    diagnostic_rows = gate03["cutoff_rows"]["diagnostic_target_conditioned"]
    cutoff_rows = [
        cutoff_gate(module, row, books, starts, ops_by_start, seed_offset=index)
        for index, row in enumerate(diagnostic_rows)
    ]
    selected_rows = [row["selected"] for row in cutoff_rows]
    policy_bits = gate03["summary"]["diagnostic_target_conditioned"]["policy_bits"]
    total_baseline = sum(row["baseline_bits"] for row in selected_rows)
    total_candidate = sum(row["candidate_bits"] for row in selected_rows)
    total_lag_tax = sum(row["lag_tax_bits"] for row in selected_rows)
    total_lagged = total_candidate + total_lag_tax + policy_bits
    total_delta = total_lagged - total_baseline
    beats_random = sum(row["beats_random_p05_after_lag_tax"] for row in selected_rows)
    total_copy_hits = sum(row["copy_hits"] for row in selected_rows)
    total_copy_misses = sum(row["copy_misses"] for row in selected_rows)
    total_hits = sum(row["hits"] for row in selected_rows)
    total_starts = sum(row["starts"] for row in selected_rows)
    weak = total_delta < 0 and beats_random >= 4
    classification = (
        "WEAK_LAGGED_SURPRISAL_BOUNDARY_ANNOTATION_CLUE"
        if weak
        else "LAGGED_SURPRISAL_BOUNDARY_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "cutoff_rows": cutoff_rows,
        "decision": {
            "executable_copy_literal_decoder_promoted": False,
            "generator_promoted": False,
            "lagged_annotation_promoted": weak,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "surprisal_start_candidate_gate": rel(GATE03),
            "unified_residual_control_ledger": rel(CONTROL_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "lagged_surprisal_boundary_contract_gate.v1",
        "scope": "analysis_only_one_digit_lag_boundary_contract",
        "summary": {
            "beats_random_p05_after_lag_tax_cells": beats_random,
            "policy_bits": policy_bits,
            "total_baseline_bits": total_baseline,
            "total_candidate_bits_before_policy": total_candidate,
            "total_copy_hits_requiring_lag_tax": total_copy_hits,
            "total_copy_misses": total_copy_misses,
            "total_delta_vs_baseline_after_lag_tax": total_delta,
            "total_hits": total_hits,
            "total_lag_tax_bits": total_lag_tax,
            "total_lagged_bits": total_lagged,
            "total_starts": total_starts,
            "uniform_digit_bits": UNIFORM_DIGIT_BITS,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Lagged Surprisal Boundary Contract Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether the strong right-surprisal start-candidate signal can be "
        "reinterpreted as a one-digit-lag boundary annotation program after paying "
        "the first copied digit as external innovation.",
        "",
        "## Summary",
        "",
        f"- Lagged bits after policy and copy lag tax: `{s['total_lagged_bits']:.3f}`.",
        f"- Exact start composition baseline bits: `{s['total_baseline_bits']:.3f}`.",
        f"- Delta after lag tax: `{s['total_delta_vs_baseline_after_lag_tax']:.3f}` bits.",
        f"- Candidate bits before policy/tax: `{s['total_candidate_bits_before_policy']:.3f}`.",
        f"- Copy-hit lag tax: `{s['total_lag_tax_bits']:.3f}` bits "
        f"(`{s['total_copy_hits_requiring_lag_tax']}` copy starts at `{s['uniform_digit_bits']:.3f}` bits each).",
        f"- Start hits: `{s['total_hits']}/{s['total_starts']}`.",
        f"- Copy misses still requiring exact correction: `{s['total_copy_misses']}`.",
        f"- Cells beating random top-K p05 after lag tax: `{s['beats_random_p05_after_lag_tax_cells']}/5`.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | Family | Rate | Hits | Copy hits | Copy misses | Lagged bits | Baseline bits | Delta | Random p05 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["cutoff_rows"]:
        selected = row["selected"]
        lines.append(
            f"| `{row['cutoff']}` | `{selected['family']}` | `{selected['rate']:.3f}` | "
            f"`{selected['hits']}` | `{selected['copy_hits']}` | `{selected['copy_misses']}` | "
            f"`{selected['lagged_total_bits']:.3f}` | `{selected['baseline_bits']:.3f}` | "
            f"`{selected['delta_vs_baseline_after_lag_tax']:.3f}` | "
            f"`{selected['beats_random_p05_after_lag_tax']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "A one-digit-lag annotation can keep the right-surprisal clue in play "
            "only as a weak segmentation annotation. It is not a promoted copy/literal "
            "decoder, because copy starts recognized late must externalize copied "
            "digits and missed copy starts still require exact correction.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
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
        "Can the strong right-surprisal boundary signal be made less oracle-like by "
        "treating it as a one-digit-lag boundary annotation program?",
        "",
        "## Result",
        "",
        f"The one-digit-lag contract costs `{s['total_lagged_bits']:.3f}` bits versus "
        f"`{s['total_baseline_bits']:.3f}` exact start-composition bits "
        f"(`{s['total_delta_vs_baseline_after_lag_tax']:.3f}`). The lag tax alone is "
        f"`{s['total_lag_tax_bits']:.3f}` bits for "
        f"`{s['total_copy_hits_requiring_lag_tax']}` recovered copy starts. It still "
        f"beats random top-K p05 in `{s['beats_random_p05_after_lag_tax_cells']}/5` cells.",
        "",
        "## Decision",
        "",
        "This preserves a weak boundary-annotation clue, but it does not produce an "
        "executable copy/literal decoder. The next blocker remains deriving starts "
        "and copy/literal mode before target-conditioned source availability or "
        "paying the remaining correction tape explicitly. Row0, plaintext, "
        "translation, and compression_bound remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_all_position_boundary_transducer_gate.py](../scripts/01_all_position_boundary_transducer_gate.py)",
        "- [02_start_candidate_ranking_gate.py](../scripts/02_start_candidate_ranking_gate.py)",
        "- [03_surprisal_start_candidate_gate.py](../scripts/03_surprisal_start_candidate_gate.py)",
        "- [04_lagged_surprisal_boundary_contract_gate.py](../scripts/04_lagged_surprisal_boundary_contract_gate.py)",
        "- [01_all_position_boundary_transducer_gate.json](test_results/01_all_position_boundary_transducer_gate.json)",
        "- [02_start_candidate_ranking_gate.json](test_results/02_start_candidate_ranking_gate.json)",
        "- [03_surprisal_start_candidate_gate.json](test_results/03_surprisal_start_candidate_gate.json)",
        "- [04_lagged_surprisal_boundary_contract_gate.json](test_results/04_lagged_surprisal_boundary_contract_gate.json)",
        "- [04_lagged_surprisal_boundary_contract_gate.md](test_results/04_lagged_surprisal_boundary_contract_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
