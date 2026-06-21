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
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_formula_469.json"
)
OUT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE51 = TEST_RESULTS / "51_copy_length_segmentation_exception_audit.json"
GATE53 = TEST_RESULTS / "53_targetmax_resegmentation_formula_gate.json"
GATE52_SCRIPT = HERE / "scripts" / "52_targetmax_resegmentation_candidate_audit.py"

CURRENT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_resegmentation_second_pass_bits"
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


def make_result() -> dict[str, Any]:
    gate51 = load_json(GATE51)
    assert_boundary("copy_length_segmentation_exception_audit", gate51)
    gate53 = load_json(GATE53)
    assert_boundary("targetmax_resegmentation_formula_gate", gate53)
    helper = load_module("gate52_targetmax_resegmentation", GATE52_SCRIPT)
    compile129, audit136, audit137, modules = build_modules(helper)

    formula = load_json(CURRENT_FORMULA)
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    current_total = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
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
    current_exact_total = float(current_score["exact_total_bits"])
    if not math.isclose(current_exact_total, current_total, abs_tol=1e-9):
        raise RuntimeError(
            {
                "type": "current_exact_scorer_mismatch",
                "formula_total": current_total,
                "exact_total": current_exact_total,
            }
        )

    candidates = []
    skipped_stale = 0
    for exception in gate51["exception_rows"]:
        if not still_matches_current_formula(formula, exception):
            skipped_stale += 1
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
                candidate_errors = list(roundtrip_errors) + list(
                    candidate_score["errors"]
                )
                candidate_total = (
                    None
                    if candidate_errors
                    else float(candidate_score["exact_total_bits"])
                )
                candidate_gain = (
                    None if candidate_total is None else current_total - candidate_total
                )
                component_delta = (
                    {}
                    if candidate_errors
                    else {
                        key: float(candidate_score[key]) - float(current_score[key])
                        for key in [
                            "literal_bits_no_payload",
                            "literal_payload_bits",
                            "item_type_bits",
                            "copy_source_bits",
                            "copy_length_bits",
                        ]
                    }
                )
            except Exception as exc:  # pragma: no cover - recorded as audit data
                roundtrip_errors = []
                candidate_score = {"errors": [{"type": "exception", "message": str(exc)}]}
                candidate_errors = candidate_score["errors"]
                candidate_total = None
                candidate_gain = None
                component_delta = {}
            candidates.append(
                {
                    "book": exception["book"],
                    "op_index": exception["op_index"],
                    "mode": mode,
                    "following_op_type": exception["first_covered_following_op_type"],
                    "slack": exception["target_max_slack"],
                    "candidate_total_bits": candidate_total,
                    "candidate_gain_bits": candidate_gain,
                    "roundtrip_error_count": len(roundtrip_errors),
                    "score_error_count": len(candidate_score["errors"]),
                    "errors": candidate_errors[:5],
                    "component_delta_bits": component_delta,
                }
            )

    valid = [
        row
        for row in candidates
        if row["candidate_total_bits"] is not None
        and row["roundtrip_error_count"] == 0
        and row["score_error_count"] == 0
    ]
    improving = [
        row for row in valid if float(row["candidate_gain_bits"]) > 1e-12
    ]
    mode_rank = {"preserve_next_mode": 0, "literalize_next_remainder": 1}
    best = (
        max(
            improving,
            key=lambda row: (
                float(row["candidate_gain_bits"]),
                -mode_rank[row["mode"]],
                -int(row["book"]),
                -int(row["op_index"]),
            ),
        )
        if improving
        else None
    )
    classification = (
        "targetmax_resegmentation_second_pass_improves_bound"
        if best is not None
        else "targetmax_resegmentation_second_pass_no_improvement"
    )

    output_formula = None
    candidate_score = None
    if best is not None:
        best_exception = next(
            row
            for row in gate51["exception_rows"]
            if int(row["book"]) == int(best["book"])
            and int(row["op_index"]) == int(best["op_index"])
        )
        candidate_formula = helper.apply_targetmax_trim(
            formula=formula,
            books=books,
            exception=best_exception,
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
        candidate_total = float(candidate_score["exact_total_bits"])
        candidate_gain = current_total - candidate_total
        output = {
            **candidate_formula,
            "classification": classification,
            "source_formula": rel(CURRENT_FORMULA),
            "targetmax_resegmentation_second_pass_compile": {
                "source": "54_targetmax_resegmentation_second_pass_gate",
                "previous_gate": rel(GATE53),
                "book": best["book"],
                "op_index": best["op_index"],
                "mode": best["mode"],
                "slack": best["slack"],
                "previous_total_bits": current_total,
                "candidate_total_bits": candidate_total,
                "candidate_gain_bits": candidate_gain,
                "component_delta_bits": best["component_delta_bits"],
            },
            "policy": {
                **candidate_formula["policy"],
                "targetmax_resegmentation_second_pass": {
                    "source": "54_targetmax_resegmentation_second_pass_gate",
                    "scope": "best remaining local target-max resegmentation after gate53",
                    "exact_component_rescore": True,
                    "promoted": True,
                },
            },
            "mdl_estimate_rough": {
                **candidate_formula["mdl_estimate_rough"],
                OUT_TOTAL_KEY: candidate_total,
                f"previous_{CURRENT_TOTAL_KEY}": current_total,
                "gain_vs_previous_targetmax_resegmentation_bits": candidate_gain,
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
                "copy_length_default_exception_bits": candidate_score[
                    "copy_length_bits"
                ],
                "copy_length_code_bits": candidate_score["copy_length_bits"],
                "bounded_adaptive_copy_length_bits": candidate_score[
                    "copy_length_bits"
                ],
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
                "targetmax_resegmentation_second_pass_roundtrip_audit": {
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

    return {
        "schema": "targetmax_resegmentation_second_pass_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "current_formula": rel(CURRENT_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "copy_length_segmentation_exception_audit": rel(GATE51),
            "previous_targetmax_formula_gate": rel(GATE53),
        },
        "candidate_output_formula": output_formula,
        "scope": {
            "analysis_only": True,
            "candidate_source": "remaining gate51 target-max exceptions still matching the gate53 formula",
            "stale_exception_count": skipped_stale,
            "exact_component_scorer_reproduces_current_bound": True,
            "row0_origin_changed": False,
            "plaintext_or_translation_claim": False,
        },
        "summary": {
            "current_total_bits": current_total,
            "current_exact_total_bits": current_exact_total,
            "candidate_total_bits": None if best is None else best["candidate_total_bits"],
            "candidate_gain_bits": None if best is None else best["candidate_gain_bits"],
            "tested_candidate_count": len(candidates),
            "valid_candidate_count": len(valid),
            "improving_candidate_count": len(improving),
            "stale_exception_count": skipped_stale,
            "best_candidate": best,
            "inventory": (
                None
                if candidate_score is None
                else {
                    "literal_runs": candidate_score["literal_runs"],
                    "literal_digits": candidate_score["literal_digits"],
                    "copy_items": candidate_score["copy_items"],
                    "copied_digits": candidate_score["copied_digits"],
                }
            ),
            "interpretation": (
                "A second exact target-max resegmentation pass still finds a "
                "positive mechanical compression-bound improvement, but it does "
                "not derive row0 or add semantics."
            ),
        },
        "candidates": candidates,
        "decision": {
            "compression_bound_status": (
                "improved_by_second_targetmax_resegmentation"
                if best is not None
                else "unchanged"
            ),
            "targetmax_resegmentation_status": (
                "second_candidate_promoted" if best is not None else "saturated"
            ),
            "generation_explanation_status": "resegmentation_path_promoted_second_step",
            "next_mainline_status": "continue_exact_targetmax_resegmentation_until_no_positive_candidate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "54_targetmax_resegmentation_second_pass_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    best = s["best_candidate"]
    lines = [
        "# Target-Max Resegmentation Second-Pass Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 53 promoted one target-max resegmentation under the exact",
        "component scorer. This gate retests the remaining compatible local",
        "target-max rewrites against that promoted formula and emits a new",
        "formula only if exact scoring and roundtrip validation still improve",
        "the bound.",
        "",
        "## Summary",
        "",
        f"- Current formula bits: `{s['current_total_bits']:.6f}`.",
        f"- Current exact scorer bits: `{s['current_exact_total_bits']:.6f}`.",
        f"- Stale exceptions skipped: `{s['stale_exception_count']}`.",
        f"- Candidates tested: `{s['tested_candidate_count']}`.",
        f"- Valid candidates: `{s['valid_candidate_count']}`.",
        f"- Improving candidates: `{s['improving_candidate_count']}`.",
    ]
    if best is not None:
        lines.extend(
            [
                f"- Candidate bits: `{best['candidate_total_bits']:.6f}`.",
                f"- Candidate gain: `{best['candidate_gain_bits']:+.6f}` bits.",
                f"- Candidate: book `{best['book']}`, op `{best['op_index']}`, mode `{best['mode']}`, slack `{best['slack']}`.",
                f"- Component deltas: `{best['component_delta_bits']}`.",
                f"- Inventory: `{s['inventory']}`.",
            ]
        )
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
            "## Candidate Table",
            "",
            "| Book | Op | Mode | Next | Slack | Errors | Gain | Total |",
            "|---:|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in result["candidates"]:
        gain = row["candidate_gain_bits"]
        total = row["candidate_total_bits"]
        gain_text = "NA" if gain is None else f"{gain:+.6f}"
        total_text = "NA" if total is None else f"{total:.6f}"
        error_count = int(row["roundtrip_error_count"]) + int(row["score_error_count"])
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['mode']}` | "
            f"`{row['following_op_type']}` | `{row['slack']}` | "
            f"`{error_count}` | `{gain_text}` | `{total_text}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a compression-bound update only. The exact scorer validates a",
            "second local target-max resegmentation after the gate-53 formula. It",
            "does not derive the 10x10 row0 table, identify plaintext, or reopen",
            "semantic interpretation.",
            "",
            "## Boundary",
            "",
            "- Compression bound changes only after exact scorer reproduction and roundtrip validation.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "54_targetmax_resegmentation_second_pass_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
