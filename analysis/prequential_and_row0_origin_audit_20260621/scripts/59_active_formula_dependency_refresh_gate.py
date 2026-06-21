from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

PREVIOUS_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json"
)
ACTIVE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
DEPENDENCY_SCOREBOARD_48 = TEST_RESULTS / "48_current_formula_dependency_scoreboard.json"
POST_TARGETMAX_SECOND_PASS = (
    TEST_RESULTS / "57_post_targetmax_source_substitution_second_pass_gate.json"
)
POST_TARGETMAX_STOP = (
    TEST_RESULTS / "58_post_targetmax_source_substitution_stop_audit.json"
)

PREVIOUS_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_bits"
)
ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_targetmax_saturated_source_substitution_second_pass_bits"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        raise RuntimeError(f"{name} changed row0 origin status")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def roundtrip_formula(formula: dict[str, Any], books: dict[str, str]) -> list[str]:
    emitted = ""
    errors: list[str] = []
    for book in map(str, formula["policy"]["book_order"]):
        rendered = []
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                chunk = op["text"]
            elif op["type"] == "copy":
                source = int(op["source_digit_pos"])
                length = int(op["length"])
                chunk = emitted[source : source + length]
            else:
                raise RuntimeError(f"unknown op type: {op['type']}")
            rendered.append(chunk)
            emitted += chunk
        if "".join(rendered) != books[book]:
            errors.append(book)
    return errors


def formula_counts(formula: dict[str, Any], books: dict[str, str]) -> dict[str, Any]:
    errors = roundtrip_formula(formula, books)
    literal_ops = 0
    copy_ops = 0
    literal_digits = 0
    copied_digits = 0
    for book in map(str, formula["policy"]["book_order"]):
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                length = len(op["text"])
                literal_ops += 1
                literal_digits += length
            elif op["type"] == "copy":
                length = int(op["length"])
                copy_ops += 1
                copied_digits += length
            else:
                raise RuntimeError(f"unknown op type: {op['type']}")
    total_digits = literal_digits + copied_digits
    return {
        "roundtrip_book_count": len(books) - len(errors),
        "roundtrip_errors": errors,
        "book_count": len(formula["book_recipes"]),
        "op_count": literal_ops + copy_ops,
        "literal_op_count": literal_ops,
        "copy_op_count": copy_ops,
        "literal_digits": literal_digits,
        "copied_digits": copied_digits,
        "total_digits": total_digits,
        "literal_digit_fraction": literal_digits / total_digits,
        "copied_digit_fraction": copied_digits / total_digits,
        "declared_literal_payload_fields": literal_ops,
        "declared_copy_source_fields": copy_ops,
        "declared_copy_length_fields": copy_ops,
        "declared_recipe_dependency_fields": literal_ops + copy_ops + copy_ops,
    }


def diff_counts(previous: dict[str, Any], active: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "op_count",
        "literal_op_count",
        "copy_op_count",
        "literal_digits",
        "copied_digits",
        "total_digits",
        "declared_literal_payload_fields",
        "declared_copy_source_fields",
        "declared_copy_length_fields",
        "declared_recipe_dependency_fields",
    ]
    return {key: active[key] - previous[key] for key in keys}


def dependency_rows(previous: dict[str, Any], active: dict[str, Any]) -> list[dict[str, Any]]:
    specs = [
        ("literal_payload", "declared_literal_payload_fields", "literal text fields"),
        ("copy_source", "declared_copy_source_fields", "copy source fields"),
        ("copy_length", "declared_copy_length_fields", "copy length fields"),
    ]
    rows = []
    for dependency, key, unit in specs:
        rows.append(
            {
                "dependency": dependency,
                "unit": unit,
                "previous_declared_units": previous[key],
                "active_declared_units": active[key],
                "delta_declared_units": active[key] - previous[key],
                "status": (
                    "unchanged_declared_dependency"
                    if active[key] == previous[key]
                    else "declared_dependency_count_changed"
                ),
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    dependency48 = load_json(DEPENDENCY_SCOREBOARD_48)
    gate57 = load_json(POST_TARGETMAX_SECOND_PASS)
    stop58 = load_json(POST_TARGETMAX_STOP)
    for name, data in [
        ("dependency_scoreboard_48", dependency48),
        ("post_targetmax_source_second_pass_gate", gate57),
        ("post_targetmax_stop_audit", stop58),
    ]:
        assert_boundary(name, data)

    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    previous_formula = load_json(PREVIOUS_FORMULA)
    active_formula = load_json(ACTIVE_FORMULA)
    previous_counts = formula_counts(previous_formula, books)
    active_counts = formula_counts(active_formula, books)
    if previous_counts["roundtrip_errors"] or active_counts["roundtrip_errors"]:
        raise RuntimeError(
            {
                "previous_roundtrip_errors": previous_counts["roundtrip_errors"],
                "active_roundtrip_errors": active_counts["roundtrip_errors"],
            }
        )

    previous_bits = float(previous_formula["mdl_estimate_rough"][PREVIOUS_TOTAL_KEY])
    active_bits = float(active_formula["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    gate57_bits = float(gate57["summary"]["candidate_total_bits"])
    stop_bits = float(stop58["summary"]["current_compression_bound_bits"])
    if abs(active_bits - gate57_bits) > 1e-9 or abs(active_bits - stop_bits) > 1e-9:
        raise RuntimeError(
            {
                "active_bits": active_bits,
                "gate57_bits": gate57_bits,
                "stop_bits": stop_bits,
            }
        )

    deltas = diff_counts(previous_counts, active_counts)
    structural_dependency_delta = deltas["declared_recipe_dependency_fields"]
    classification = (
        "active_formula_dependency_refresh_no_structural_dependency_reduction"
        if structural_dependency_delta == 0
        else "active_formula_dependency_refresh_dependency_count_changed"
    )
    return {
        "schema": "active_formula_dependency_refresh_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "previous_formula": rel(PREVIOUS_FORMULA),
            "active_formula": rel(ACTIVE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "dependency_scoreboard_48": rel(DEPENDENCY_SCOREBOARD_48),
            "post_targetmax_source_second_pass_gate": rel(POST_TARGETMAX_SECOND_PASS),
            "post_targetmax_stop_audit": rel(POST_TARGETMAX_STOP),
        },
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "compression_bound_changed": False,
            "tests_active_formula_after_targetmax_and_stop_audit": True,
            "does_not_search_plaintext": True,
            "does_not_search_additional_source_substitutions": True,
        },
        "previous_formula": {
            "classification": previous_formula["classification"],
            "total_bits": previous_bits,
            "counts": previous_counts,
        },
        "active_formula": {
            "classification": active_formula["classification"],
            "total_bits": active_bits,
            "counts": active_counts,
        },
        "dependency_rows": dependency_rows(previous_counts, active_counts),
        "summary": {
            "previous_bound_bits": previous_bits,
            "active_bound_bits": active_bits,
            "bound_delta_bits": active_bits - previous_bits,
            "bound_gain_bits": previous_bits - active_bits,
            "count_deltas": deltas,
            "declared_recipe_dependency_delta": structural_dependency_delta,
            "literal_digits_delta": deltas["literal_digits"],
            "copied_digits_delta": deltas["copied_digits"],
            "digit_shift_interpretation": (
                "Target-max resegmentation and post-target-max source substitutions "
                "move one digit from literal payload into copied payload, but they do "
                "not reduce the number of declared literal, source, or length fields."
            ),
            "mainline_implication": (
                "The active bound improves, but the structural explanation gap is "
                "unchanged at the dependency-count level. A future improvement must "
                "derive source/length fields or row0 rather than only reprice them."
            ),
        },
        "decision": {
            "compression_bound_status": "retained_8156_049986",
            "generation_explanation_status": (
                "active_formula_still_declares_same_recipe_dependency_count"
            ),
            "next_mainline_status": (
                "structural_source_length_parser_or_row0_origin_evidence_required"
            ),
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "59_active_formula_dependency_refresh_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    previous = result["previous_formula"]
    active = result["active_formula"]
    summary = result["summary"]
    lines = [
        "# Active Formula Dependency Refresh Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 48 mapped dependencies on the source-substitution fourth-pass",
        "formula. This refresh repeats the dependency count on the active",
        "post-target-max formula frozen by the stop audit. It does not search",
        "for another compression improvement.",
        "",
        "## Formula Comparison",
        "",
        "| Formula | Total bits | Literal ops | Copy ops | Literal digits | Copied digits | Declared recipe dependency fields | Roundtrip |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        f"| previous source-substitution fourth pass | `{previous['total_bits']:.6f}` | "
        f"`{previous['counts']['literal_op_count']}` | "
        f"`{previous['counts']['copy_op_count']}` | "
        f"`{previous['counts']['literal_digits']}` | "
        f"`{previous['counts']['copied_digits']}` | "
        f"`{previous['counts']['declared_recipe_dependency_fields']}` | "
        f"`{previous['counts']['roundtrip_book_count']}/70` |",
        f"| active post-target-max second-pass formula | `{active['total_bits']:.6f}` | "
        f"`{active['counts']['literal_op_count']}` | "
        f"`{active['counts']['copy_op_count']}` | "
        f"`{active['counts']['literal_digits']}` | "
        f"`{active['counts']['copied_digits']}` | "
        f"`{active['counts']['declared_recipe_dependency_fields']}` | "
        f"`{active['counts']['roundtrip_book_count']}/70` |",
        "",
        "## Dependency Rows",
        "",
        "| Dependency | Previous units | Active units | Delta | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for row in result["dependency_rows"]:
        lines.append(
            f"| `{row['dependency']}` | `{row['previous_declared_units']}` | "
            f"`{row['active_declared_units']}` | "
            f"`{row['delta_declared_units']:+d}` | `{row['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Result",
            "",
            f"- Bound gain versus the gate-48 formula: `{summary['bound_gain_bits']:.6f}` bits.",
            f"- Declared recipe dependency delta: `{summary['declared_recipe_dependency_delta']:+d}` fields.",
            f"- Literal digit delta: `{summary['literal_digits_delta']:+d}`.",
            f"- Copied digit delta: `{summary['copied_digits_delta']:+d}`.",
            f"- Interpretation: {summary['digit_shift_interpretation']}",
            f"- Mainline implication: {summary['mainline_implication']}",
            "",
            "## Decision",
            "",
            "- Current compression bound remains `8156.049986` bits.",
            "- The target-max/source-substitution path improves the bound but does not reduce declared recipe dependency fields.",
            "- The next mainline test remains structural source/length derivation or row0-origin evidence.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No new book-generation formula is emitted.",
            "- No additional source-substitution pass is searched.",
        ]
    )
    (TEST_RESULTS / "59_active_formula_dependency_refresh_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
