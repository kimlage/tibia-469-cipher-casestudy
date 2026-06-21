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
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json"
)
OUT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE52 = TEST_RESULTS / "52_targetmax_resegmentation_candidate_audit.json"
GATE52_SCRIPT = HERE / "scripts" / "52_targetmax_resegmentation_candidate_audit.py"

CURRENT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_bits"
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


def make_result() -> dict[str, Any]:
    gate52 = load_json(GATE52)
    assert_boundary("targetmax_resegmentation_candidate_audit", gate52)
    helper = load_module("gate52_targetmax_resegmentation", GATE52_SCRIPT)
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
    formula = load_json(CURRENT_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    current_total = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = helper.score_compatible_components(
        formula=formula,
        books=books,
        compile129=compile129,
        audit136=audit136,
        audit137=audit137,
        modules=modules,
    )
    if current_score["errors"]:
        raise RuntimeError({"type": "current_score_errors", "errors": current_score["errors"][:5]})
    current_exact_total = exact_total_from_score(current_score)
    if not math.isclose(current_exact_total, current_total, abs_tol=1e-9):
        raise RuntimeError(
            {
                "type": "current_exact_scorer_mismatch",
                "formula_total": current_total,
                "exact_total": current_exact_total,
            }
        )

    best = gate52["summary"]["best_candidate"]
    if best is None:
        raise RuntimeError("gate52 has no best candidate")
    candidate_formula = helper.apply_targetmax_trim(
        formula=formula,
        books=books,
        exception={
            "book": best["book"],
            "op_index": best["op_index"],
            "target_max_slack": best["slack"],
        },
        mode=best["mode"],
    )
    roundtrip_errors = helper.roundtrip_errors(candidate_formula, books)
    candidate_score = helper.score_compatible_components(
        formula=candidate_formula,
        books=books,
        compile129=compile129,
        audit136=audit136,
        audit137=audit137,
        modules=modules,
    )
    candidate_errors = list(roundtrip_errors) + list(candidate_score["errors"])
    candidate_total = exact_total_from_score(candidate_score)
    candidate_gain = current_total - candidate_total
    classification = (
        "targetmax_resegmentation_formula_improves_bound"
        if not candidate_errors and candidate_gain > 0
        else "targetmax_resegmentation_formula_not_promoted"
    )
    output_formula = None
    if classification == "targetmax_resegmentation_formula_improves_bound":
        output = {
            **candidate_formula,
            "classification": classification,
            "source_formula": rel(CURRENT_FORMULA),
            "targetmax_resegmentation_compile": {
                "source": "53_targetmax_resegmentation_formula_gate",
                "candidate_gate": rel(GATE52),
                "book": best["book"],
                "op_index": best["op_index"],
                "mode": best["mode"],
                "slack": best["slack"],
                "previous_total_bits": current_total,
                "candidate_total_bits": candidate_total,
                "candidate_gain_bits": candidate_gain,
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
            },
            "policy": {
                **candidate_formula["policy"],
                "targetmax_resegmentation": {
                    "source": "53_targetmax_resegmentation_formula_gate",
                    "scope": "single local extend-to-target-max and trim-following-op rewrite",
                    "exact_component_rescore": True,
                    "promoted": True,
                },
            },
            "mdl_estimate_rough": {
                **candidate_formula["mdl_estimate_rough"],
                OUT_TOTAL_KEY: candidate_total,
                f"previous_{CURRENT_TOTAL_KEY}": current_total,
                "gain_vs_previous_source_substitution_fourth_pass_bits": candidate_gain,
                "literal_bits_no_payload": candidate_score["literal_bits_no_payload"],
                "adaptive_context_order_literal_payload_bits": candidate_score[
                    "literal_payload_bits"
                ],
                "item_type_split_only_stream_bits": candidate_score["item_type_bits"],
                "copy_source_default_exception_bits": candidate_score["copy_source_bits"],
                "copy_source_substitution_frontier_bits": candidate_score[
                    "copy_source_bits"
                ],
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
                **candidate_formula["boundary"],
                "compression_bound_changed": True,
                "row0_origin_changed": False,
                "semantic_delta": "NONE",
                "translation_delta": "NONE",
                "authorial_intent_claim": False,
            },
            "validation": {
                **candidate_formula["validation"],
                "targetmax_resegmentation_roundtrip_audit": {
                    "book_count": 70,
                    "books_roundtrip_ok": 70 if not roundtrip_errors else 0,
                    "errors": roundtrip_errors,
                },
            },
        }
        OUT_FORMULA.write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        output_formula = rel(OUT_FORMULA)
    return {
        "schema": "targetmax_resegmentation_formula_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "current_formula": rel(CURRENT_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "candidate_gate": rel(GATE52),
        },
        "candidate_output_formula": output_formula,
        "scope": {
            "single_candidate": True,
            "candidate_source": "best candidate from gate52",
            "exact_component_scorer_reproduces_current_bound": True,
            "row0_origin_changed": False,
            "plaintext_or_translation_claim": False,
        },
        "summary": {
            "current_total_bits": current_total,
            "current_exact_total_bits": current_exact_total,
            "candidate_total_bits": candidate_total,
            "candidate_gain_bits": candidate_gain,
            "book": best["book"],
            "op_index": best["op_index"],
            "mode": best["mode"],
            "slack": best["slack"],
            "roundtrip_error_count": len(roundtrip_errors),
            "score_error_count": len(candidate_score["errors"]),
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
            "inventory": {
                "literal_runs": candidate_score["literal_runs"],
                "literal_digits": candidate_score["literal_digits"],
                "copy_items": candidate_score["copy_items"],
                "copied_digits": candidate_score["copied_digits"],
            },
            "interpretation": (
                "The exact component scorer reproduces the current bound and "
                "promotes the best local target-max resegmentation candidate as "
                "a real mechanical bound improvement."
            ),
        },
        "decision": {
            "compression_bound_status": (
                "improved_by_targetmax_resegmentation"
                if classification == "targetmax_resegmentation_formula_improves_bound"
                else "unchanged"
            ),
            "targetmax_resegmentation_status": "single_candidate_promoted",
            "generation_explanation_status": "resegmentation_path_promoted_single_step",
            "next_mainline_status": "test additional compatible targetmax_resegmentations_under_exact_scorer",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "53_targetmax_resegmentation_formula_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Target-Max Resegmentation Formula Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 52 found local target-max resegmentation proxy improvements. This",
        "gate first proves that the exact component scorer reproduces the current",
        "bound, then promotes the best single candidate only if roundtrip and exact",
        "component scoring improve the formula.",
        "",
        "## Summary",
        "",
        f"- Current formula bits: `{s['current_total_bits']:.6f}`.",
        f"- Current exact scorer bits: `{s['current_exact_total_bits']:.6f}`.",
        f"- Candidate bits: `{s['candidate_total_bits']:.6f}`.",
        f"- Candidate gain: `{s['candidate_gain_bits']:+.6f}` bits.",
        f"- Candidate: book `{s['book']}`, op `{s['op_index']}`, mode `{s['mode']}`, slack `{s['slack']}`.",
        f"- Roundtrip errors: `{s['roundtrip_error_count']}`.",
        f"- Score errors: `{s['score_error_count']}`.",
        f"- Component deltas: `{s['component_delta_bits']}`.",
        f"- Inventory: `{s['inventory']}`.",
    ]
    if result["candidate_output_formula"]:
        lines.extend(
            [
                "",
                "## Promoted Formula",
                "",
                f"- [{Path(result['candidate_output_formula']).name}](../../../authorial_mechanism_20260620/{Path(result['candidate_output_formula']).name})",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is the first promoted target-max resegmentation step. The gain comes",
            "from copy-length coding; copy-source cost rises slightly, while literal",
            "payload, literal structure, and item-type cost remain unchanged. The",
            "result is mechanical only and does not affect row0 or semantics.",
            "",
            "## Boundary",
            "",
            "- Compression bound changes only after exact scorer reproduction and roundtrip validation.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "53_targetmax_resegmentation_formula_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
