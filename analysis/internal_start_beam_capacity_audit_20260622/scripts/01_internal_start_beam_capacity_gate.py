#!/usr/bin/env python3
"""Internal-start beam capacity gate.

The previous target-free internal-start program kept the true coarse sequence in
beam for 56/150 prefix-held-out books, but produced only 13/343 internal starts
before corrections and cost more than explicit opcount+cutpoint+type
declaration.

This gate asks whether that failure is merely a beam-capacity/ranking problem.
It reuses the same book-level controller and varies sequence/book beam widths,
charging rank bits, composition-index bits, and explicit corrections for misses.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "internal_start_beam_capacity_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

TARGET_FREE_GATE_SCRIPT = (
    ROOT
    / "analysis"
    / "target_free_internal_start_program_audit_20260622"
    / "scripts"
    / "01_target_free_internal_start_program_gate.py"
)
TARGET_FREE_GATE = (
    ROOT
    / "analysis"
    / "target_free_internal_start_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_target_free_internal_start_program_gate.json"
)
BOOK_LEVEL_SCRIPT = (
    ROOT
    / "analysis"
    / "book_level_coarse_length_controller_audit_20260622"
    / "scripts"
    / "01_book_level_coarse_length_controller_gate.py"
)
BOOK_LEVEL_GATE = (
    ROOT
    / "analysis"
    / "book_level_coarse_length_controller_audit_20260622"
    / "reports"
    / "test_results"
    / "01_book_level_coarse_length_controller_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_internal_start_beam_capacity_gate.json"
MD_OUT = TEST_RESULTS / "01_internal_start_beam_capacity_gate.md"
FINAL_OUT = FRONT / "reports" / "final_internal_start_beam_capacity_audit.md"

WIDTHS = [
    {"label": "baseline", "seq_beam": 12, "book_beam": 30},
    {"label": "x2", "seq_beam": 24, "book_beam": 60},
    {"label": "x4", "seq_beam": 48, "book_beam": 120},
    {"label": "x8", "seq_beam": 96, "book_beam": 240},
    {"label": "x16", "seq_beam": 192, "book_beam": 480},
    {"label": "x32", "seq_beam": 384, "book_beam": 960},
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    decision = data.get("decision", {})
    row0 = decision.get("row0_status") or decision.get("row0_origin_status")
    if row0 not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status: {row0}")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def evaluate_width(tf, bl, width: dict[str, Any], best_pair: str) -> dict[str, Any]:
    old_seq = bl.SEQ_BEAM_WIDTH
    old_book = bl.BOOK_BEAM_WIDTH
    bl.SEQ_BEAM_WIDTH = int(width["seq_beam"])
    bl.BOOK_BEAM_WIDTH = int(width["book_beam"])
    try:
        books = bl.load_books()
        count_name, coarse_name = best_pair.split("__", 1)
        cutoff_rows = [
            tf.evaluate_cutoff(bl, books, cutoff, count_name, coarse_name)
            for cutoff in bl.CUTOFFS
        ]
    finally:
        bl.SEQ_BEAM_WIDTH = old_seq
        bl.BOOK_BEAM_WIDTH = old_book

    totals: Counter[str] = Counter()
    for row in cutoff_rows:
        for key, value in row["summary"].items():
            if isinstance(value, (int, float)):
                totals[key] += value

    out = {
        **width,
        **dict(totals),
        "generated_internal_start_fraction": (
            totals["generated_internal_starts_before_correction"]
            / max(1, totals["test_internal_starts"])
        ),
        "saving_vs_explicit_opcount_cutpoint_bits": (
            totals["explicit_opcount_cutpoint_bits"] - totals["program_bits"]
        ),
        "saving_vs_explicit_opcount_cutpoint_type_bits": (
            totals["explicit_opcount_cutpoint_type_bits"] - totals["program_bits"]
        ),
        "sequence_hit_rate": totals["sequence_hit_books"] / max(1, totals["test_books"]),
    }
    out["width_id_bits"] = math.log2(len(WIDTHS))
    out["program_bits_with_width_id"] = out["program_bits"] + out["width_id_bits"]
    out["saving_vs_explicit_opcount_cutpoint_type_bits_with_width_id"] = (
        out["explicit_opcount_cutpoint_type_bits"] - out["program_bits_with_width_id"]
    )
    return out


def make_result() -> dict[str, Any]:
    target_free = load_json(TARGET_FREE_GATE)
    book_level = load_json(BOOK_LEVEL_GATE)
    assert_boundary("target_free_internal_start_program_gate", target_free)
    assert_boundary("book_level_controller_gate", book_level)
    tf = load_module("target_free_internal_start_program", TARGET_FREE_GATE_SCRIPT)
    bl = load_module("book_level_controller_for_capacity", BOOK_LEVEL_SCRIPT)
    best_pair = target_free["decision"]["best_pair"]
    rows = [evaluate_width(tf, bl, width, best_pair) for width in WIDTHS]
    best_by_paid = max(
        rows,
        key=lambda row: (
            row["saving_vs_explicit_opcount_cutpoint_type_bits_with_width_id"],
            row["generated_internal_starts_before_correction"],
            row["sequence_hit_books"],
        ),
    )
    best_by_hits = max(
        rows,
        key=lambda row: (
            row["sequence_hit_books"],
            row["generated_internal_starts_before_correction"],
            -row["program_bits"],
        ),
    )
    baseline = rows[0]
    coverage_improved = best_by_hits["sequence_hit_books"] > baseline["sequence_hit_books"]
    paid_reduction = (
        best_by_paid["saving_vs_explicit_opcount_cutpoint_type_bits_with_width_id"] > 0
    )
    exact_coverage = best_by_hits["sequence_hit_books"] == best_by_hits["test_books"]
    classification = (
        "PROMOTED_INTERNAL_START_BEAM_CAPACITY_PROGRAM"
        if paid_reduction and exact_coverage
        else "WEAK_BEAM_CAPACITY_ROUTE_RETAINED"
        if coverage_improved and not paid_reduction
        else "INTERNAL_START_BEAM_CAPACITY_ROUTE_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "best_by_hits": best_by_hits["label"],
            "best_by_paid_cost": best_by_paid["label"],
            "coverage_improved": coverage_improved,
            "paid_reduction": paid_reduction,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "book_level_controller_gate": rel(BOOK_LEVEL_GATE),
            "book_level_controller_script": rel(BOOK_LEVEL_SCRIPT),
            "target_free_internal_start_gate": rel(TARGET_FREE_GATE),
            "target_free_internal_start_script": rel(TARGET_FREE_GATE_SCRIPT),
        },
        "plaintext_claim": False,
        "rows": rows,
        "schema": "internal_start_beam_capacity_gate.v1",
        "scope": "analysis_only_beam_capacity_curve_for_target_free_internal_starts",
        "summary": {
            "best_pair": best_pair,
            "best_width_by_hits": best_by_hits["label"],
            "best_width_by_paid_cost": best_by_paid["label"],
            "classification": classification,
            "coverage_improved": coverage_improved,
            "max_generated_internal_starts": best_by_hits[
                "generated_internal_starts_before_correction"
            ],
            "max_sequence_hits": best_by_hits["sequence_hit_books"],
            "paid_reduction": paid_reduction,
            "route_boundary": (
                "larger beams test capacity only; promotion still requires paid "
                "ledger reduction, not more covered examples"
            ),
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    s = result["summary"]
    lines = [
        "# Internal Start Beam Capacity Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Did the target-free internal-start program fail because the book-level "
        "controller beam was too narrow, or because the controller still lacks the "
        "right generative ranking/state?",
        "",
        "## Summary",
        "",
        f"- Best controller pair: `{s['best_pair']}`.",
        f"- Best width by hits: `{s['best_width_by_hits']}`.",
        f"- Best width by paid cost: `{s['best_width_by_paid_cost']}`.",
        f"- Max sequence hits: `{int(s['max_sequence_hits'])}`.",
        f"- Max generated internal starts before correction: `{int(s['max_generated_internal_starts'])}`.",
        f"- Coverage improved over baseline: `{s['coverage_improved']}`.",
        f"- Paid reduction vs explicit opcount+cutpoint+type: `{s['paid_reduction']}`.",
        "",
        "## Capacity Curve",
        "",
        "| Width | Seq beam | Book beam | Sequence hits | Generated starts | Program bits | Correction bits | Saving vs start+type |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['seq_beam']}` | `{row['book_beam']}` | "
            f"`{int(row['sequence_hit_books'])}/{int(row['test_books'])}` | "
            f"`{int(row['generated_internal_starts_before_correction'])}/{int(row['test_internal_starts'])}` | "
            f"`{row['program_bits_with_width_id']:.3f}` | `{row['correction_bits']:.3f}` | "
            f"`{row['saving_vs_explicit_opcount_cutpoint_type_bits_with_width_id']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
        ]
    )
    if result["decision"]["paid_reduction"]:
        lines.append(
            "A wider beam reduces the paid ledger and should be promoted as a real "
            "program candidate."
        )
    elif result["decision"]["coverage_improved"]:
        lines.append(
            "Wider beams increase coverage, but not enough to reduce the paid ledger. "
            "This keeps the route alive only as a weak capacity clue; the missing "
            "piece is ranking/state, not just beam width."
        )
    else:
        lines.append(
            "Wider beams do not materially improve the route. The failure is not a "
            "capacity artifact under these widths."
        )
    lines.extend(
        [
            "",
            f"Boundary: {s['route_boundary']}.",
            "",
            "`row0`, plaintext, translation, and `compression_bound` remain unchanged.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result, MD_OUT)
    write_markdown(result, FINAL_OUT)
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "best_width_by_hits": result["summary"]["best_width_by_hits"],
                "max_sequence_hits": result["summary"]["max_sequence_hits"],
                "max_generated_internal_starts": result["summary"][
                    "max_generated_internal_starts"
                ],
                "paid_reduction": result["summary"]["paid_reduction"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
