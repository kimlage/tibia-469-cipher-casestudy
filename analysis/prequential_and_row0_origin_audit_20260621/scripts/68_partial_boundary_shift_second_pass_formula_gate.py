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

CURRENT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_formula_469.json"
)
OUT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE67 = TEST_RESULTS / "67_partial_boundary_shift_second_pass_gate.json"
GATE65_SCRIPT = HERE / "scripts" / "65_active_exception_partial_boundary_shift_gate.py"

CURRENT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_partial_boundary_shift_second_pass_bits"
)


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


def annotate_formula(
    *,
    formula: dict[str, Any],
    current_score: dict[str, Any],
    candidate_score: dict[str, Any],
    current_total: float,
    candidate_total: float,
    best: dict[str, Any],
) -> dict[str, Any]:
    gain = current_total - candidate_total
    component_delta = {
        key: float(candidate_score[key]) - float(current_score[key])
        for key in [
            "literal_bits_no_payload",
            "literal_payload_bits",
            "item_type_bits",
            "copy_source_bits",
            "copy_length_bits",
        ]
    }
    return {
        **formula,
        "classification": "partial_boundary_shift_second_pass_formula_improves_bound",
        "source_formula": rel(CURRENT_FORMULA),
        "partial_boundary_shift_second_pass_compile": {
            "source": "68_partial_boundary_shift_second_pass_formula_gate",
            "candidate_gate": rel(GATE67),
            "book": best["book"],
            "op_index": best["op_index"],
            "mode": best["mode"],
            "delta": best["delta"],
            "target_max_slack": best["target_max_slack"],
            "previous_total_bits": current_total,
            "candidate_total_bits": candidate_total,
            "candidate_gain_bits": gain,
            "component_delta_bits": component_delta,
        },
        "policy": {
            **formula["policy"],
            "partial_boundary_shift_second_pass": {
                "source": "68_partial_boundary_shift_second_pass_formula_gate",
                "scope": "single exact-scored second-pass partial shift inside an active residual target-max two-op window",
                "exact_component_rescore": True,
                "promoted": True,
            },
        },
        "mdl_estimate_rough": {
            **formula["mdl_estimate_rough"],
            OUT_TOTAL_KEY: candidate_total,
            f"previous_{CURRENT_TOTAL_KEY}": current_total,
            "gain_vs_previous_partial_boundary_shift_bits": gain,
            "literal_bits_no_payload": candidate_score["literal_bits_no_payload"],
            "adaptive_context_order_literal_payload_bits": candidate_score[
                "literal_payload_bits"
            ],
            "item_type_split_only_stream_bits": candidate_score["item_type_bits"],
            "copy_source_default_exception_bits": candidate_score["copy_source_bits"],
            "copy_source_substitution_frontier_bits": candidate_score["copy_source_bits"],
            "copy_source_default_exception_stream_bits": candidate_score[
                "source_model"
            ]["stream_bits"],
            "copy_source_default_exception_flag_bits": candidate_score[
                "source_model"
            ]["flag_bits"],
            "copy_source_default_exception_source_bits": candidate_score[
                "source_model"
            ]["exception_source_bits"],
            "copy_length_default_exception_bits": candidate_score["copy_length_bits"],
            "copy_length_code_bits": candidate_score["copy_length_bits"],
            "bounded_adaptive_copy_length_bits": candidate_score["copy_length_bits"],
            "copy_length_default_exception_stream_bits": candidate_score[
                "length_model"
            ]["stream_bits"],
            "copy_length_default_exception_flag_bits": candidate_score[
                "length_model"
            ]["flag_bits"],
            "copy_length_default_exception_length_bits": candidate_score[
                "length_model"
            ]["exception_length_bits"],
            "copy_bits": candidate_score["copy_source_bits"]
            + candidate_score["copy_length_bits"],
            "literal_runs": candidate_score["literal_runs"],
            "literal_digits": candidate_score["literal_digits"],
            "copy_items": candidate_score["copy_items"],
            "copied_digits": candidate_score["copied_digits"],
        },
        "boundary": {
            **formula["boundary"],
            "compression_bound_changed": True,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "translation_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }


def make_result() -> dict[str, Any]:
    gate67 = load_json(GATE67)
    assert_boundary("partial_boundary_shift_second_pass_gate", gate67)
    if gate67["classification"] != "partial_boundary_shift_second_pass_candidate_found":
        raise RuntimeError("gate67 did not find a candidate")
    helper = load_module("gate65_partial_boundary_shift", GATE65_SCRIPT)
    gate52_helper = helper.load_module(
        "gate52_targetmax_resegmentation",
        helper.GATE52_SCRIPT,
    )
    compile129, audit136, audit137, modules = helper.build_modules(gate52_helper)

    formula = load_json(CURRENT_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    current_total = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
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

    best = gate67["summary"]["best_valid_candidate"]
    exception = next(
        row
        for row in gate67["candidates"]
        if int(row["book"]) == int(best["book"])
        and int(row["op_index"]) == int(best["op_index"])
        and int(row["delta"]) == int(best["delta"])
        and row["mode"] == best["mode"]
    )
    candidate_formula = helper.apply_partial_shift(
        helper=gate52_helper,
        formula=formula,
        books=books,
        exception=exception,
        delta=int(best["delta"]),
        mode=best["mode"],
    )
    roundtrip_errors = gate52_helper.roundtrip_errors(candidate_formula, books)
    candidate_score = helper.score_formula(
        helper=gate52_helper,
        formula=candidate_formula,
        books=books,
        compile129=compile129,
        audit136=audit136,
        audit137=audit137,
        modules=modules,
    )
    candidate_errors = list(roundtrip_errors) + list(candidate_score["errors"])
    candidate_total = float(candidate_score["exact_total_bits"])
    candidate_gain = current_total - candidate_total
    classification = (
        "partial_boundary_shift_second_pass_formula_improves_bound"
        if not candidate_errors and candidate_gain > 0
        else "partial_boundary_shift_second_pass_formula_not_promoted"
    )
    output_formula = None
    if classification == "partial_boundary_shift_second_pass_formula_improves_bound":
        output = annotate_formula(
            formula=candidate_formula,
            current_score=current_score,
            candidate_score=candidate_score,
            current_total=current_total,
            candidate_total=candidate_total,
            best=best,
        )
        output["validation"] = {
            **candidate_formula["validation"],
            "partial_boundary_shift_second_pass_roundtrip_audit": {
                "book_count": 70,
                "books_roundtrip_ok": 70 if not roundtrip_errors else 0,
                "errors": roundtrip_errors,
            },
        }
        OUT_FORMULA.write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        output_formula = rel(OUT_FORMULA)

    return {
        "schema": "partial_boundary_shift_second_pass_formula_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "current_formula": rel(CURRENT_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "candidate_gate": rel(GATE67),
        },
        "scope": {
            "analysis_only": True,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "candidate_source": "best exact-scored partial boundary second-pass shift from gate 67",
        },
        "summary": {
            "current_total_bits": current_total,
            "current_exact_total_bits": float(current_score["exact_total_bits"]),
            "candidate_total_bits": candidate_total,
            "candidate_gain_bits": candidate_gain,
            "candidate": {
                "book": best["book"],
                "op_index": best["op_index"],
                "mode": best["mode"],
                "delta": best["delta"],
                "target_max_slack": best["target_max_slack"],
            },
            "roundtrip_error_count": len(roundtrip_errors),
            "score_error_count": len(candidate_score["errors"]),
            "errors": candidate_errors[:5],
            "component_delta_bits": {
                key: float(candidate_score[key]) - float(current_score[key])
                for key in [
                    "literal_bits_no_payload",
                    "literal_payload_bits",
                    "item_type_bits",
                    "copy_source_bits",
                    "copy_length_bits",
                ]
            },
            "output_formula": output_formula,
        },
        "decision": {
            "compression_bound_status": (
                "promoted_8154_676268"
                if classification
                == "partial_boundary_shift_second_pass_formula_improves_bound"
                else "unchanged_8155_261037"
            ),
            "partial_boundary_shift_status": classification,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    s = result["summary"]
    c = s["candidate"]
    return "\n".join(
        [
            "# Partial Boundary Shift Second-Pass Formula Gate",
            "",
            f"Classification: `{result['classification']}`",
            "Translation delta: `NONE`",
            "",
            "## Purpose",
            "",
            "Gate 67 found one further exact-scored partial shift candidate after",
            "the first partial-boundary promotion. This gate reapplies it and",
            "materializes a new formula only if exact scoring improves.",
            "",
            "## Summary",
            "",
            f"- Current total bits: `{s['current_total_bits']:.6f}`.",
            f"- Exact scorer reproduction: `{s['current_exact_total_bits']:.6f}`.",
            f"- Candidate total bits: `{s['candidate_total_bits']:.6f}`.",
            f"- Candidate gain bits: `{s['candidate_gain_bits']:+.6f}`.",
            f"- Candidate: book `{c['book']}`, op `{c['op_index']}`, mode `{c['mode']}`, delta `{c['delta']}` of slack `{c['target_max_slack']}`.",
            f"- Roundtrip errors: `{s['roundtrip_error_count']}`.",
            f"- Score errors: `{s['score_error_count']}`.",
            f"- Component deltas: `{s['component_delta_bits']}`.",
            f"- Output formula: `{s['output_formula']}`.",
            "",
            "## Decision",
            "",
            f"- Compression-bound status: `{result['decision']['compression_bound_status']}`.",
            "- This is a mechanical formula update only.",
            "- Row0 origin remains exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )


def main() -> None:
    result = make_result()
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "68_partial_boundary_shift_second_pass_formula_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (TEST_RESULTS / "68_partial_boundary_shift_second_pass_formula_gate.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
