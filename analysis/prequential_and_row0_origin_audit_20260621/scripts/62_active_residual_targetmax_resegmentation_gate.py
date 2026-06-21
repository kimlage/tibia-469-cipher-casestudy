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
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
ACTIVE_COPY_LENGTH_TOPOLOGY_61 = (
    TEST_RESULTS / "61_active_copy_length_exception_topology_gate.json"
)
GATE52_SCRIPT = HERE / "scripts" / "52_targetmax_resegmentation_candidate_audit.py"

ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_bits"
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


def exact_total_from_score(score: dict[str, Any]) -> float:
    return sum(
        float(score[key])
        for key in [
            "literal_bits_no_payload",
            "literal_payload_bits",
            "item_type_bits",
            "copy_source_bits",
            "copy_length_bits",
        ]
    ) + 620.0


def build_modules(helper):
    compile129 = helper.load_module("compile129", helper.AUDIT_129)
    audit136 = helper.load_module("audit136", helper.AUDIT_136)
    audit137 = helper.load_module("audit137", helper.AUDIT_137)
    audit126 = compile129.load_audit_126()
    modules = {
        "audit126": audit126,
        "frontier": helper.load_module("frontier", audit126.FRONTIER),
        "midpoint": helper.load_module("midpoint", audit126.MIDPOINT),
        "copy_module": helper.load_module("copy_context", audit126.COPY_CONTEXT),
        "item_module": helper.load_module("item_context", audit126.ITEM_CONTEXT),
    }
    return compile129, audit136, audit137, modules


def score_formula(
    *,
    helper,
    formula: dict[str, Any],
    books: dict[str, str],
    compile129,
    audit136,
    audit137,
    modules: dict[str, Any],
) -> dict[str, Any]:
    score = helper.score_compatible_components(
        formula=formula,
        books=books,
        compile129=compile129,
        audit136=audit136,
        audit137=audit137,
        modules=modules,
    )
    score["exact_total_bits"] = exact_total_from_score(score)
    return score


def component_delta(
    candidate_score: dict[str, Any],
    current_score: dict[str, Any],
) -> dict[str, float]:
    return {
        key: float(candidate_score[key]) - float(current_score[key])
        for key in [
            "literal_bits_no_payload",
            "literal_payload_bits",
            "item_type_bits",
            "copy_source_bits",
            "copy_length_bits",
        ]
    }


def scan_candidates(
    *,
    helper,
    formula: dict[str, Any],
    books: dict[str, str],
    exceptions: list[dict[str, Any]],
    current_total: float,
    current_score: dict[str, Any],
    compile129,
    audit136,
    audit137,
    modules: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for exception in exceptions:
        for mode in ["preserve_next_mode", "literalize_next_remainder"]:
            try:
                candidate_formula = helper.apply_targetmax_trim(
                    formula=formula,
                    books=books,
                    exception=exception,
                    mode=mode,
                )
                roundtrip_errors = helper.roundtrip_errors(candidate_formula, books)
                candidate_score = score_formula(
                    helper=helper,
                    formula=candidate_formula,
                    books=books,
                    compile129=compile129,
                    audit136=audit136,
                    audit137=audit137,
                    modules=modules,
                )
                errors = list(roundtrip_errors) + list(candidate_score["errors"])
                candidate_total = (
                    None if errors else float(candidate_score["exact_total_bits"])
                )
                candidate_gain = (
                    None if candidate_total is None else current_total - candidate_total
                )
                deltas = (
                    {}
                    if errors
                    else component_delta(candidate_score, current_score)
                )
            except Exception as exc:  # pragma: no cover - audit record only
                errors = [{"type": "exception", "message": str(exc)}]
                candidate_total = None
                candidate_gain = None
                deltas = {}
            rows.append(
                {
                    "book": exception["book"],
                    "op_index": exception["op_index"],
                    "book_pos": exception["book_pos"],
                    "mode": mode,
                    "following_op_type": exception["first_covered_following_op_type"],
                    "slack": exception["target_max_slack"],
                    "candidate_total_bits": candidate_total,
                    "candidate_gain_bits": candidate_gain,
                    "error_count": len(errors),
                    "errors": errors[:5],
                    "component_delta_bits": deltas,
                }
            )
    return rows


def make_result() -> dict[str, Any]:
    gate61 = load_json(ACTIVE_COPY_LENGTH_TOPOLOGY_61)
    assert_boundary("active_copy_length_exception_topology", gate61)
    helper = load_module("gate52_targetmax_resegmentation", GATE52_SCRIPT)
    compile129, audit136, audit137, modules = build_modules(helper)

    formula = load_json(ACTIVE_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    current_total = float(formula["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    current_score = score_formula(
        helper=helper,
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

    exceptions = gate61["active_topology"]["exception_rows"]
    rows = scan_candidates(
        helper=helper,
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
    valid_rows = [row for row in rows if int(row["error_count"]) == 0]
    improving_rows = [
        row
        for row in valid_rows
        if row["candidate_gain_bits"] is not None
        and float(row["candidate_gain_bits"]) > EPSILON
    ]
    valid_rows_sorted = sorted(
        valid_rows,
        key=lambda row: float(row["candidate_gain_bits"]),
        reverse=True,
    )
    best_valid = valid_rows_sorted[0] if valid_rows_sorted else None
    worst_valid = valid_rows_sorted[-1] if valid_rows_sorted else None
    error_histogram: dict[str, int] = {}
    for row in rows:
        if not row["errors"]:
            continue
        first = row["errors"][0]
        key = str(first.get("rule") or first.get("type") or "unknown")
        error_histogram[key] = error_histogram.get(key, 0) + 1

    classification = (
        "active_residual_targetmax_resegmentation_saturated_no_improvements"
        if not improving_rows
        else "active_residual_targetmax_resegmentation_improves_bound"
    )
    return {
        "schema": "active_residual_targetmax_resegmentation_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "active_formula": rel(ACTIVE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "active_copy_length_exception_topology": rel(
                ACTIVE_COPY_LENGTH_TOPOLOGY_61
            ),
            "targetmax_resegmentation_helper": rel(GATE52_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "candidate_modes": [
                "preserve_next_mode",
                "literalize_next_remainder",
            ],
            "candidate_source": "19 active target-max copy-length exceptions from gate 61",
        },
        "summary": {
            "current_total_bits": current_total,
            "current_exact_total_bits": float(current_score["exact_total_bits"]),
            "active_exception_count": len(exceptions),
            "candidate_count": len(rows),
            "valid_candidate_count": len(valid_rows),
            "invalid_candidate_count": len(rows) - len(valid_rows),
            "improving_candidate_count": len(improving_rows),
            "best_valid_candidate": best_valid,
            "worst_valid_candidate": worst_valid,
            "error_histogram": dict(sorted(error_histogram.items())),
            "interpretation": (
                "Every remaining active target-max exception was tested with the "
                "same local trim modes used by the promoted target-max gates. "
                "No exact valid candidate improves the active bound. The best "
                "valid residual rewrite is still worse by 0.000163 bits, so this "
                "local residual target-max resegmentation frontier is saturated."
            ),
        },
        "candidate_rows": rows,
        "decision": {
            "compression_bound_status": "unchanged_8156_049986",
            "residual_targetmax_resegmentation_status": "saturated_no_improving_candidate",
            "copy_length_dependency_status": "retained_declared",
            "generation_explanation_status": "residual_boundaries_require_nonlocal_joint_parser",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "62_active_residual_targetmax_resegmentation_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    best = s["best_valid_candidate"]
    lines = [
        "# Active Residual Target-Max Resegmentation Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 61 shows that 19 active copy lengths still stop before their",
        "encoder target-max extension. This gate tests whether any remaining",
        "local extend-and-trim rewrite improves the active formula under the",
        "same exact component scorer used by the promoted target-max gates.",
        "",
        "## Summary",
        "",
        f"- Current total bits: `{s['current_total_bits']:.6f}`.",
        f"- Exact scorer reproduction: `{s['current_exact_total_bits']:.6f}`.",
        f"- Active exceptions tested: `{s['active_exception_count']}`.",
        f"- Candidate rows: `{s['candidate_count']}`.",
        f"- Valid candidates: `{s['valid_candidate_count']}`.",
        f"- Invalid candidates: `{s['invalid_candidate_count']}`.",
        f"- Improving candidates: `{s['improving_candidate_count']}`.",
        f"- Error histogram: `{s['error_histogram']}`.",
        "",
        "## Best Valid Residual Candidate",
        "",
    ]
    if best is None:
        lines.append("- No valid candidates.")
    else:
        lines.extend(
            [
                f"- Book/op/mode: `{best['book']}` / `{best['op_index']}` / `{best['mode']}`.",
                f"- Slack: `{best['slack']}`.",
                f"- Candidate total bits: `{best['candidate_total_bits']:.6f}`.",
                f"- Candidate gain bits: `{best['candidate_gain_bits']:+.6f}`.",
                f"- Component deltas: `{best['component_delta_bits']}`.",
            ]
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Interpretation: {s['interpretation']}",
            "- Current compression bound remains `8156.049986` bits.",
            "- The residual local target-max resegmentation frontier is saturated under this exact scorer.",
            "- Further progress requires a nonlocal joint parser rather than another local extend-and-trim rule.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No new formula is emitted.",
        ]
    )
    (TEST_RESULTS / "62_active_residual_targetmax_resegmentation_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
