from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

ACTIVE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE66 = TEST_RESULTS / "66_partial_boundary_shift_formula_gate.json"
GATE65_SCRIPT = HERE / "scripts" / "65_active_exception_partial_boundary_shift_gate.py"
TOPOLOGY_SCRIPT = HERE / "scripts" / "61_active_copy_length_exception_topology_gate.py"

ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_bits"
)
EPSILON = 1e-12


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def mode_counts(rows: list[dict[str, Any]], modes: list[str]) -> dict[str, int]:
    return {mode: sum(1 for row in rows if row["mode"] == mode) for mode in modes}


def render_markdown(result: dict[str, Any]) -> str:
    s = result["summary"]
    best = s["best_valid_candidate"]
    lines = [
        "# Partial Boundary Shift Second-Pass Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "After gate 66 promotes one partial boundary shift, this gate recomputes",
        "the active target-max exception topology on the promoted formula and",
        "exact-scores every remaining positive partial local shift.",
        "",
        "## Summary",
        "",
        f"- Current total bits: `{s['current_total_bits']:.6f}`.",
        f"- Exact scorer reproduction: `{s['current_exact_total_bits']:.6f}`.",
        f"- Active copy events: `{s['copy_event_count']}`.",
        f"- Active target-max exceptions: `{s['exception_count']}`.",
        f"- Active slack digits: `{s['target_max_slack_digits_total']}`.",
        f"- Shift candidates tested: `{s['candidate_count']}`.",
        f"- Valid candidates: `{s['valid_candidate_count']}`.",
        f"- Improving candidates: `{s['improving_candidate_count']}`.",
        f"- Candidate count by mode: `{s['candidate_count_by_mode']}`.",
        f"- Valid count by mode: `{s['valid_count_by_mode']}`.",
        f"- Improving count by mode: `{s['improving_count_by_mode']}`.",
    ]
    if best:
        lines.extend(
            [
                "",
                "## Best Valid Candidate",
                "",
                f"- Book/op: `{best['book']}` / `{best['op_index']}`.",
                f"- Mode: `{best['mode']}`.",
                f"- Delta/slack: `{best['delta']}` / `{best['target_max_slack']}`.",
                f"- Candidate total bits: `{best['candidate_total_bits']:.6f}`.",
                f"- Candidate gain bits: `{best['candidate_gain_bits']:+.6f}`.",
                f"- Component deltas: `{best['component_delta_bits']}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Top Valid Candidates",
            "",
            "| Book | Op | Mode | Delta | Slack | Gain bits | Total bits |",
            "|---:|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in s["top_valid_candidates"]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['mode']}` | "
            f"`{row['delta']}` | `{row['target_max_slack']}` | "
            f"`{row['candidate_gain_bits']:+.6f}` | "
            f"`{row['candidate_total_bits']:.6f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Interpretation: {s['interpretation']}",
            "- Row0 origin remains exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    gate66 = load_json(GATE66)
    assert_boundary("partial_boundary_shift_formula_gate", gate66)
    helper = load_module("gate65_partial_boundary_shift", GATE65_SCRIPT)
    gate52_helper = helper.load_module(
        "gate52_targetmax_resegmentation",
        helper.GATE52_SCRIPT,
    )
    topology = load_module("active_exception_topology", TOPOLOGY_SCRIPT)
    compile129, audit136, audit137, modules = helper.build_modules(gate52_helper)

    formula = load_json(ACTIVE_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    current_total = float(formula["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    current_score = helper.score_formula(
        helper=gate52_helper,
        formula=formula,
        books=books,
        compile129=compile129,
        audit136=audit136,
        audit137=audit137,
        modules=modules,
    )
    if current_score["errors"]:
        raise RuntimeError(
            {"type": "current_score_errors", "errors": current_score["errors"][:5]}
        )
    if not math.isclose(
        float(current_score["exact_total_bits"]),
        current_total,
        abs_tol=1e-9,
    ):
        raise RuntimeError(
            {
                "type": "current_exact_scorer_mismatch",
                "formula_total": current_total,
                "exact_total": current_score["exact_total_bits"],
            }
        )

    active_topology = topology.exception_topology(formula, books)
    exceptions = active_topology["exception_rows"]
    candidates = helper.scan_candidates(
        helper=gate52_helper,
        formula=formula,
        books=books,
        exceptions=exceptions,
        current_total=current_total,
        current_score=current_score,
        compile129=compile129,
        audit136=audit136,
        audit137=audit137,
        modules=modules,
    )
    valid = [row for row in candidates if row["error_count"] == 0]
    improving = [
        row
        for row in valid
        if row["candidate_gain_bits"] is not None
        and float(row["candidate_gain_bits"]) > EPSILON
    ]
    valid_sorted = sorted(
        valid,
        key=lambda row: float(row["candidate_gain_bits"]),
        reverse=True,
    )
    best = valid_sorted[0] if valid_sorted else None
    modes = sorted({row["mode"] for row in candidates})
    classification = (
        "partial_boundary_shift_second_pass_candidate_found"
        if improving
        else "partial_boundary_shift_second_pass_saturated"
    )
    interpretation = (
        "A further exact-scored partial boundary shift remains after the first "
        "promotion. A separate formula gate is required before changing the bound."
        if improving
        else "No further positive partial local boundary shift improves the "
        "exact active scorer after the first promotion."
    )
    result = {
        "schema": "partial_boundary_shift_second_pass_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "active_formula": rel(ACTIVE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "previous_formula_gate": rel(GATE66),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "window_family": "second-pass two-operation positive partial boundary shifts up to target-max",
        },
        "summary": {
            "current_total_bits": current_total,
            "current_exact_total_bits": float(current_score["exact_total_bits"]),
            "copy_event_count": active_topology["copy_event_count"],
            "exception_count": active_topology["target_max_exception_count"],
            "target_max_slack_digits_total": active_topology[
                "target_max_slack_digits_total"
            ],
            "candidate_count": len(candidates),
            "valid_candidate_count": len(valid),
            "improving_candidate_count": len(improving),
            "candidate_count_by_mode": mode_counts(candidates, modes),
            "valid_count_by_mode": mode_counts(valid, modes),
            "improving_count_by_mode": mode_counts(improving, modes),
            "best_valid_candidate": best,
            "top_valid_candidates": valid_sorted[:12],
            "interpretation": interpretation,
        },
        "active_topology": active_topology,
        "candidates": candidates,
        "decision": {
            "compression_bound_status": "unchanged_8155_261037",
            "copy_length_dependency_status": "retained_declared",
            "partial_boundary_shift_status": (
                "second_pass_candidate_found" if improving else "second_pass_saturated"
            ),
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }

    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "67_partial_boundary_shift_second_pass_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (TEST_RESULTS / "67_partial_boundary_shift_second_pass_gate.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
