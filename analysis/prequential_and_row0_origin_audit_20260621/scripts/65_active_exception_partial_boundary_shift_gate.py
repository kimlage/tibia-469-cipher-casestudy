from __future__ import annotations

import copy
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


def component_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, float]:
    return {
        key: float(candidate[key]) - float(baseline[key])
        for key in [
            "literal_bits_no_payload",
            "literal_payload_bits",
            "item_type_bits",
            "copy_source_bits",
            "copy_length_bits",
        ]
    }


def apply_partial_shift(
    *,
    helper,
    formula: dict[str, Any],
    books: dict[str, str],
    exception: dict[str, Any],
    delta: int,
    mode: str,
) -> dict[str, Any]:
    out = copy.deepcopy(formula)
    book = str(exception["book"])
    op_index = int(exception["op_index"])
    ops = out["book_recipes"][book]["ops"]
    if op_index + 1 >= len(ops):
        raise RuntimeError({"type": "missing_next_op", "exception": exception})
    current = ops[op_index]
    following = ops[op_index + 1]
    rows = helper.reconstruct_book(formula, books, book)
    following_text = rows[op_index + 1]["text"]
    if delta <= 0 or delta > int(exception["target_max_slack"]):
        raise RuntimeError({"type": "bad_delta", "delta": delta, "exception": exception})
    if delta > len(following_text):
        raise RuntimeError(
            {"type": "delta_exceeds_following_text", "delta": delta, "exception": exception}
        )
    remaining_text = following_text[delta:]
    current["length"] = int(current["length"]) + delta
    if following["type"] == "literal":
        following["text"] = following["text"][delta:]
        following["length"] = len(following["text"])
    elif mode == "preserve_next_mode":
        following["source_digit_pos"] = int(following["source_digit_pos"]) + delta
        following["length"] = int(following["length"]) - delta
    elif mode == "literalize_next_remainder":
        following.clear()
        following.update(
            {
                "type": "literal",
                "text": remaining_text,
                "length": len(remaining_text),
            }
        )
    else:
        raise RuntimeError(f"unknown mode: {mode}")
    if following.get("length") == 0:
        del ops[op_index + 1]
    return out


def candidate_modes(exception: dict[str, Any]) -> list[str]:
    if exception["first_covered_following_op_type"] == "literal":
        return ["trim_literal"]
    return ["preserve_next_mode", "literalize_next_remainder"]


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
        for delta in range(1, int(exception["target_max_slack"]) + 1):
            for mode in candidate_modes(exception):
                try:
                    candidate_formula = apply_partial_shift(
                        helper=helper,
                        formula=formula,
                        books=books,
                        exception=exception,
                        delta=delta,
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
                        "delta": delta,
                        "target_max_slack": exception["target_max_slack"],
                        "following_op_type": exception["first_covered_following_op_type"],
                        "candidate_total_bits": candidate_total,
                        "candidate_gain_bits": candidate_gain,
                        "error_count": len(errors),
                        "errors": errors[:5],
                        "component_delta_bits": deltas,
                    }
                )
    return rows


def render_markdown(result: dict[str, Any]) -> str:
    s = result["summary"]
    best = s["best_valid_candidate"]
    lines = [
        "# Active Exception Partial Boundary Shift Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 62 exact-scored only the full shift to target-max for each residual",
        "copy-length exception. This gate exact-scores every positive partial",
        "boundary shift up to target-max inside the same two-operation local window.",
        "",
        "## Summary",
        "",
        f"- Current total bits: `{s['current_total_bits']:.6f}`.",
        f"- Exact scorer reproduction: `{s['current_exact_total_bits']:.6f}`.",
        f"- Exceptions tested: `{s['exception_count']}`.",
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
            "- Current compression bound remains `8156.049986` bits.",
            "- Copy length remains a declared dependency.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No new formula is emitted.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
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
    candidates = scan_candidates(
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
        "active_exception_partial_boundary_shift_candidate_found"
        if improving
        else "active_exception_partial_boundary_shift_saturated"
    )
    interpretation = (
        "At least one partial boundary shift improves the exact active scorer. "
        "This is a candidate for formula promotion only after a separate "
        "promotion gate writes and validates a new formula."
        if improving
        else "Every positive partial shift inside the residual two-operation "
        "windows is non-improving under the exact active scorer. The residual "
        "boundary is not solved by choosing a smaller-than-target-max local shift."
    )
    result = {
        "schema": "active_exception_partial_boundary_shift_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "active_formula": rel(ACTIVE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "active_copy_length_exception_topology": rel(ACTIVE_COPY_LENGTH_TOPOLOGY_61),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "copy_event_count": 261,
            "exception_count": len(exceptions),
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "window_family": "two-operation positive partial boundary shifts up to target-max",
        },
        "summary": {
            "current_total_bits": current_total,
            "current_exact_total_bits": float(current_score["exact_total_bits"]),
            "exception_count": len(exceptions),
            "candidate_count": len(candidates),
            "valid_candidate_count": len(valid),
            "improving_candidate_count": len(improving),
            "candidate_count_by_mode": {
                mode: sum(1 for row in candidates if row["mode"] == mode)
                for mode in modes
            },
            "valid_count_by_mode": {
                mode: sum(1 for row in valid if row["mode"] == mode)
                for mode in modes
            },
            "improving_count_by_mode": {
                mode: sum(1 for row in improving if row["mode"] == mode)
                for mode in modes
            },
            "best_valid_candidate": best,
            "top_valid_candidates": valid_sorted[:12],
            "interpretation": interpretation,
        },
        "candidates": candidates,
        "decision": {
            "compression_bound_status": "unchanged_8156_049986",
            "copy_length_dependency_status": "retained_declared",
            "generation_explanation_status": (
                "partial_boundary_shift_candidate_found"
                if improving
                else "partial_boundary_shift_does_not_explain_residual_boundaries"
            ),
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }

    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "65_active_exception_partial_boundary_shift_gate.json"
    md_path = TEST_RESULTS / "65_active_exception_partial_boundary_shift_gate.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
