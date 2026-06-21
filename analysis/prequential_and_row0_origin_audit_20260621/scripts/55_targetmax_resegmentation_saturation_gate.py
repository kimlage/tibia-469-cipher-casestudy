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
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_second_pass_formula_469.json"
)
OUT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_saturated_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE51 = TEST_RESULTS / "51_copy_length_segmentation_exception_audit.json"
GATE54 = TEST_RESULTS / "54_targetmax_resegmentation_second_pass_gate.json"
GATE52_SCRIPT = HERE / "scripts" / "52_targetmax_resegmentation_candidate_audit.py"

CURRENT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_second_pass_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_saturated_bits"
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


def still_matches_current_formula(
    formula: dict[str, Any],
    exception: dict[str, Any],
) -> bool:
    book = str(exception["book"])
    op_index = int(exception["op_index"])
    ops = formula["book_recipes"][book]["ops"]
    if op_index + 1 >= len(ops):
        return False
    op = ops[op_index]
    return (
        op.get("type") == "copy"
        and int(op.get("length", -1)) == int(exception["length"])
        and int(op.get("source_digit_pos", -1)) == int(exception["source_digit_pos"])
    )


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
) -> tuple[list[dict[str, Any]], int]:
    candidates = []
    stale_exception_count = 0
    for exception in exceptions:
        if not still_matches_current_formula(formula, exception):
            stale_exception_count += 1
            continue
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
                deltas = {} if errors else component_delta(candidate_score, current_score)
            except Exception as exc:  # pragma: no cover - audit record only
                errors = [{"type": "exception", "message": str(exc)}]
                candidate_total = None
                candidate_gain = None
                deltas = {}
            candidates.append(
                {
                    "book": exception["book"],
                    "op_index": exception["op_index"],
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
    return candidates, stale_exception_count


def choose_best(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    improving = [
        row
        for row in candidates
        if row["candidate_gain_bits"] is not None
        and float(row["candidate_gain_bits"]) > EPSILON
        and int(row["error_count"]) == 0
    ]
    if not improving:
        return None
    mode_rank = {"preserve_next_mode": 0, "literalize_next_remainder": 1}
    return max(
        improving,
        key=lambda row: (
            float(row["candidate_gain_bits"]),
            -mode_rank[row["mode"]],
            -int(row["book"]),
            -int(row["op_index"]),
        ),
    )


def find_exception(
    exceptions: list[dict[str, Any]],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    return next(
        row
        for row in exceptions
        if int(row["book"]) == int(candidate["book"])
        and int(row["op_index"]) == int(candidate["op_index"])
    )


def make_result() -> dict[str, Any]:
    gate51 = load_json(GATE51)
    assert_boundary("copy_length_segmentation_exception_audit", gate51)
    gate54 = load_json(GATE54)
    assert_boundary("targetmax_resegmentation_second_pass_gate", gate54)
    helper = load_module("gate52_targetmax_resegmentation", GATE52_SCRIPT)
    compile129, audit136, audit137, modules = build_modules(helper)

    exceptions = gate51["exception_rows"]
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    initial_formula = load_json(CURRENT_FORMULA)
    formula = initial_formula
    initial_total = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_total = initial_total
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

    pass_rows = []
    final_candidates = []
    final_stale_exception_count = 0
    while True:
        candidates, stale_exception_count = scan_candidates(
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
        valid_count = sum(
            1
            for row in candidates
            if row["candidate_total_bits"] is not None and int(row["error_count"]) == 0
        )
        improving_count = sum(
            1
            for row in candidates
            if row["candidate_gain_bits"] is not None
            and float(row["candidate_gain_bits"]) > EPSILON
            and int(row["error_count"]) == 0
        )
        best = choose_best(candidates)
        if best is None:
            final_candidates = candidates
            final_stale_exception_count = stale_exception_count
            break
        exception = find_exception(exceptions, best)
        candidate_formula = helper.apply_targetmax_trim(
            formula=formula,
            books=books,
            exception=exception,
            mode=best["mode"],
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
        if roundtrip_errors or candidate_score["errors"]:
            raise RuntimeError(
                {
                    "type": "best_candidate_revalidation_failed",
                    "roundtrip_errors": roundtrip_errors[:5],
                    "score_errors": candidate_score["errors"][:5],
                }
            )
        next_total = float(candidate_score["exact_total_bits"])
        pass_rows.append(
            {
                "pass_index": len(pass_rows) + 1,
                "book": best["book"],
                "op_index": best["op_index"],
                "mode": best["mode"],
                "following_op_type": best["following_op_type"],
                "slack": best["slack"],
                "input_total_bits": current_total,
                "output_total_bits": next_total,
                "gain_bits": current_total - next_total,
                "tested_candidate_count": len(candidates),
                "valid_candidate_count": valid_count,
                "improving_candidate_count": improving_count,
                "stale_exception_count": stale_exception_count,
                "component_delta_bits": best["component_delta_bits"],
            }
        )
        formula = candidate_formula
        current_total = next_total
        current_score = candidate_score

    classification = (
        "targetmax_resegmentation_saturated_with_improvements"
        if pass_rows
        else "targetmax_resegmentation_already_saturated"
    )
    output_formula = None
    if pass_rows:
        output = {
            **formula,
            "classification": classification,
            "source_formula": rel(CURRENT_FORMULA),
            "targetmax_resegmentation_saturation_compile": {
                "source": "55_targetmax_resegmentation_saturation_gate",
                "previous_gate": rel(GATE54),
                "initial_total_bits": initial_total,
                "final_total_bits": current_total,
                "total_gain_bits": initial_total - current_total,
                "passes": pass_rows,
                "final_improving_candidate_count": 0,
            },
            "policy": {
                **formula["policy"],
                "targetmax_resegmentation_saturation": {
                    "source": "55_targetmax_resegmentation_saturation_gate",
                    "scope": "greedy exact target-max resegmentation until no positive candidate remains",
                    "exact_component_rescore": True,
                    "promoted": True,
                },
            },
            "mdl_estimate_rough": {
                **formula["mdl_estimate_rough"],
                OUT_TOTAL_KEY: current_total,
                f"previous_{CURRENT_TOTAL_KEY}": initial_total,
                "gain_vs_previous_targetmax_resegmentation_second_pass_bits": (
                    initial_total - current_total
                ),
                "literal_bits_no_payload": current_score["literal_bits_no_payload"],
                "adaptive_context_order_literal_payload_bits": current_score[
                    "literal_payload_bits"
                ],
                "item_type_split_only_stream_bits": current_score["item_type_bits"],
                "copy_source_default_exception_bits": current_score["copy_source_bits"],
                "copy_source_substitution_frontier_bits": current_score[
                    "copy_source_bits"
                ],
                "copy_source_default_exception_stream_bits": current_score[
                    "source_model"
                ]["stream_bits"],
                "copy_source_default_exception_flag_bits": current_score[
                    "source_model"
                ]["flag_bits"],
                "copy_source_default_exception_source_bits": current_score[
                    "source_model"
                ]["exception_source_bits"],
                "copy_length_default_exception_bits": current_score[
                    "copy_length_bits"
                ],
                "copy_length_code_bits": current_score["copy_length_bits"],
                "bounded_adaptive_copy_length_bits": current_score[
                    "copy_length_bits"
                ],
                "copy_length_default_exception_stream_bits": current_score[
                    "length_model"
                ]["stream_bits"],
                "copy_length_default_exception_flag_bits": current_score[
                    "length_model"
                ]["flag_bits"],
                "copy_length_default_exception_length_bits": current_score[
                    "length_model"
                ]["exception_length_bits"],
                "copy_bits": current_score["copy_source_bits"]
                + current_score["copy_length_bits"],
                "literal_runs": current_score["literal_runs"],
                "literal_digits": current_score["literal_digits"],
                "copy_items": current_score["copy_items"],
                "copied_digits": current_score["copied_digits"],
            },
            "boundary": {
                **formula["boundary"],
                "compression_bound_changed": True,
                "row0_origin_changed": False,
                "semantic_delta": "NONE",
                "translation_delta": "NONE",
                "authorial_intent_claim": False,
            },
            "validation": {
                **formula["validation"],
                "targetmax_resegmentation_saturation_roundtrip_audit": {
                    "book_count": 70,
                    "books_roundtrip_ok": 70,
                    "errors": [],
                },
            },
        }
        OUT_FORMULA.write_text(
            json.dumps(output, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        output_formula = rel(OUT_FORMULA)

    final_valid_count = sum(
        1
        for row in final_candidates
        if row["candidate_total_bits"] is not None and int(row["error_count"]) == 0
    )
    return {
        "schema": "targetmax_resegmentation_saturation_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "current_formula": rel(CURRENT_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "copy_length_segmentation_exception_audit": rel(GATE51),
            "previous_targetmax_second_pass_gate": rel(GATE54),
        },
        "candidate_output_formula": output_formula,
        "scope": {
            "analysis_only": True,
            "search_policy": "greedy_best_exact_gain_per_pass",
            "exact_component_scorer_reproduces_current_bound": True,
            "row0_origin_changed": False,
            "plaintext_or_translation_claim": False,
        },
        "summary": {
            "initial_total_bits": initial_total,
            "final_total_bits": current_total,
            "total_gain_bits": initial_total - current_total,
            "promoted_pass_count": len(pass_rows),
            "final_tested_candidate_count": len(final_candidates),
            "final_valid_candidate_count": final_valid_count,
            "final_improving_candidate_count": 0,
            "final_stale_exception_count": final_stale_exception_count,
            "inventory": {
                "literal_runs": current_score["literal_runs"],
                "literal_digits": current_score["literal_digits"],
                "copy_items": current_score["copy_items"],
                "copied_digits": current_score["copied_digits"],
            },
            "interpretation": (
                "The exact target-max resegmentation family is saturated under "
                "the greedy scorer: positive candidates are promoted, then the "
                "final frontier has no exact positive candidate."
            ),
        },
        "passes": pass_rows,
        "final_candidates": final_candidates,
        "decision": {
            "compression_bound_status": (
                "improved_to_targetmax_resegmentation_saturated_bound"
                if pass_rows
                else "unchanged"
            ),
            "targetmax_resegmentation_status": "saturated_under_exact_greedy_frontier",
            "generation_explanation_status": "resegmentation_family_saturated_no_row0_change",
            "next_mainline_status": "return_to_structural_source_length_parser_or_holdout_predictive_parser",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "55_targetmax_resegmentation_saturation_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Target-Max Resegmentation Saturation Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 54 left the exact target-max resegmentation frontier open. This",
        "gate greedily promotes the best exact positive candidate, rescoring",
        "after each promotion, until no positive candidate remains.",
        "",
        "## Summary",
        "",
        f"- Initial formula bits: `{s['initial_total_bits']:.6f}`.",
        f"- Final formula bits: `{s['final_total_bits']:.6f}`.",
        f"- Total gain: `{s['total_gain_bits']:+.6f}` bits.",
        f"- Promoted passes: `{s['promoted_pass_count']}`.",
        f"- Final candidates tested: `{s['final_tested_candidate_count']}`.",
        f"- Final valid candidates: `{s['final_valid_candidate_count']}`.",
        f"- Final improving candidates: `{s['final_improving_candidate_count']}`.",
        f"- Final stale exceptions: `{s['final_stale_exception_count']}`.",
        f"- Final inventory: `{s['inventory']}`.",
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
            "## Promoted Passes",
            "",
            "| Pass | Book | Op | Mode | Next | Slack | Input bits | Output bits | Gain | Valid | Improving |",
            "|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["passes"]:
        lines.append(
            f"| `{row['pass_index']}` | `{row['book']}` | `{row['op_index']}` | "
            f"`{row['mode']}` | `{row['following_op_type']}` | `{row['slack']}` | "
            f"`{row['input_total_bits']:.6f}` | `{row['output_total_bits']:.6f}` | "
            f"`{row['gain_bits']:+.6f}` | `{row['valid_candidate_count']}` | "
            f"`{row['improving_candidate_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Final Frontier",
            "",
            "| Book | Op | Mode | Next | Slack | Errors | Gain | Total |",
            "|---:|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in result["final_candidates"]:
        gain = row["candidate_gain_bits"]
        total = row["candidate_total_bits"]
        gain_text = "NA" if gain is None else f"{gain:+.6f}"
        total_text = "NA" if total is None else f"{total:.6f}"
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['mode']}` | "
            f"`{row['following_op_type']}` | `{row['slack']}` | "
            f"`{row['error_count']}` | `{gain_text}` | `{total_text}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This closes the local target-max resegmentation family under the exact",
            "greedy frontier: all positive candidates reachable by this gate are",
            "promoted, and the final candidate table has zero positive exact gains.",
            "The result is still a mechanical compression-bound update only.",
            "",
            "## Boundary",
            "",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Saturation is local to the greedy target-max resegmentation frontier, not proof of a final authorial method.",
        ]
    )
    (TEST_RESULTS / "55_targetmax_resegmentation_saturation_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
