from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

ROW0_PARALLEL = ROOT / "analysis" / "row0_origin_parallel_20260621"
ROW0_REPORTS = ROW0_PARALLEL / "reports"
ROW0_TEST_RESULTS = ROW0_REPORTS / "test_results"

ROW0_FINAL_REPORT = ROW0_REPORTS / "final_row0_origin_parallel_report.md"
ROW0_NEXT_FRONTIER_REPORT = ROW0_REPORTS / "row0_next_frontier_report.md"
ROW0_DEEP_PROVENANCE = ROW0_TEST_RESULTS / "154_row0_deep_provenance_audit.json"
ROW0_SCOREBOARD = ROW0_TEST_RESULTS / "155_row0_improvement_scoreboard.json"
ROW0_PARTIAL_WORKSHEET = ROW0_TEST_RESULTS / "156_row0_partial_worksheet_model.json"
ROW0_SURFACE = ROW0_TEST_RESULTS / "157_row0_surface_exception_focus.json"
ROW0_PAID_ANCHOR = ROW0_TEST_RESULTS / "159_row0_paid_anchor_reduction_gate.json"

GATE_START = 76
GATE_END = 107
OUT_STEM = "108_recent_gates_row0_compatibility_refresh"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def gate_json_path(number: int) -> Path:
    matches = sorted(TEST_RESULTS.glob(f"{number}_*.json"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one gate {number} JSON, found {len(matches)}")
    return matches[0]


def assert_no_semantics(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")


def require_row0_unchanged(name: str, data: dict[str, Any]) -> None:
    decision = data.get("decision", {})
    status = decision.get("row0_origin_status")
    if status not in {"unchanged_exogenous", "exogenous_under_current_evidence"}:
        raise RuntimeError(f"{name} does not preserve row0 exogenous status: {status}")
    scope = data.get("scope", {})
    if isinstance(scope, dict) and scope.get("row0_origin_changed") is not False:
        raise RuntimeError(f"{name} scope does not freeze row0 origin")


def family_for_gate(number: int) -> str:
    if 76 <= number <= 87:
        return "parser_validation_and_stability"
    if 88 <= number <= 97:
        return "decoder_rule_and_source_policy_controls"
    return "skeleton_dependency_and_type_ledger"


def extract_gate_row(number: int, path: Path, data: dict[str, Any]) -> dict[str, Any]:
    decision = data.get("decision", {})
    summary = data.get("summary", {})
    row: dict[str, Any] = {
        "gate": number,
        "source": rel(path),
        "family": family_for_gate(number),
        "classification": data["classification"],
        "compression_bound_status": decision.get("compression_bound_status"),
        "generation_explanation_status": decision.get("generation_explanation_status"),
        "row0_origin_status": decision.get("row0_origin_status"),
    }
    for key in [
        "total_suffix_book_evaluations",
        "total_roundtrip_book_evaluations",
        "total_raw_positive_book_evaluations",
        "stable_exact_path_book_count",
        "unstable_exact_path_book_count",
        "best_stable_exact_path_book_count",
        "promotes_generator",
        "simple_rule_covers_skeleton",
        "copy_count",
        "literal_count",
        "operation_count",
        "explicit_op_type_residual_after_rule",
        "length_atlas_records_retained",
        "promotes_type_generator",
    ]:
        if key in summary:
            row[key] = summary[key]
    return row


def make_result() -> dict[str, Any]:
    row0_deep = load_json(ROW0_DEEP_PROVENANCE)
    row0_scoreboard = load_json(ROW0_SCOREBOARD)
    row0_worksheet = load_json(ROW0_PARTIAL_WORKSHEET)
    row0_surface = load_json(ROW0_SURFACE)
    row0_paid = load_json(ROW0_PAID_ANCHOR)

    for name, data in [
        ("row0_deep_provenance", row0_deep),
        ("row0_scoreboard", row0_scoreboard),
        ("row0_partial_worksheet", row0_worksheet),
        ("row0_surface_exception", row0_surface),
        ("row0_paid_anchor", row0_paid),
    ]:
        assert_no_semantics(name, data)

    if row0_deep["decision"] != "project_row0_provenance_partially_traced_but_cipsoft_origin_untraced":
        raise RuntimeError("row0 provenance decision changed")
    if row0_surface["decision"] != "surface_ordered_asymmetry_is_real_but_label_origin_unresolved":
        raise RuntimeError("row0 surface clue decision changed")
    if row0_worksheet["promotion_decision"] != "not_promoted_as_origin_formula_anchor_cost_and_externality_not_paid":
        raise RuntimeError("row0 worksheet promotion decision changed")
    if row0_paid["decision"] != "explicit_paid_anchor_model_does_not_beat_lookup":
        raise RuntimeError("row0 paid-anchor decision changed")
    if row0_paid["summary"]["full_explicit_pair_label_model_promoted"]:
        raise RuntimeError("full paid worksheet anchor model promoted unexpectedly")
    if row0_paid["summary"]["controlled_paid_subset_promoted"]:
        raise RuntimeError("controlled paid worksheet subset promoted unexpectedly")

    promoted_origin_rows = [
        row
        for row in row0_scoreboard["scoreboard"]
        if row.get("Class") == "PROMOTED_ORIGIN_FORMULA"
    ]
    if promoted_origin_rows:
        raise RuntimeError("row0 scoreboard contains a promoted origin formula")

    gates: list[dict[str, Any]] = []
    for number in range(GATE_START, GATE_END + 1):
        path = gate_json_path(number)
        data = load_json(path)
        assert_no_semantics(path.name, data)
        require_row0_unchanged(path.name, data)
        if data.get("decision", {}).get("translation_or_plaintext_status") != "NONE":
            raise RuntimeError(f"{path.name} changed translation/plaintext status")
        gates.append(extract_gate_row(number, path, data))

    gate_by_number = {row["gate"]: row for row in gates}
    gate107 = load_json(gate_json_path(107))
    gate77 = load_json(gate_json_path(77))
    gate78 = load_json(gate_json_path(78))
    gate86 = load_json(gate_json_path(86))
    gate100 = load_json(gate_json_path(100))

    family_counts: dict[str, int] = {}
    for row in gates:
        family_counts[row["family"]] = family_counts.get(row["family"], 0) + 1

    criteria = {
        "predicts_row0_labels_under_holdout": False,
        "reduces_bits_below_row0_lookup_after_rule_or_anchor_cost": False,
        "explains_39_93_19_91_beyond_existing_surface_clue": False,
        "adds_new_cipsoft_or_authorial_provenance": False,
        "only_improves_book_formula_assuming_row0": True,
    }

    return {
        "schema": "recent_gates_row0_compatibility_refresh.v1",
        "classification": "recent_formula_gates_76_107_row0_unchanged",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "row0_final_report": rel(ROW0_FINAL_REPORT),
            "row0_next_frontier_report": rel(ROW0_NEXT_FRONTIER_REPORT),
            "row0_deep_provenance": rel(ROW0_DEEP_PROVENANCE),
            "row0_scoreboard": rel(ROW0_SCOREBOARD),
            "row0_partial_worksheet": rel(ROW0_PARTIAL_WORKSHEET),
            "row0_surface_exception": rel(ROW0_SURFACE),
            "row0_paid_anchor": rel(ROW0_PAID_ANCHOR),
            "recent_formula_gates": [row["source"] for row in gates],
        },
        "summary": {
            "gate_range_checked": [GATE_START, GATE_END],
            "gate_count_checked": len(gates),
            "gate_family_counts": family_counts,
            "current_compression_bound_bits": 8154.676268216349,
            "row0_changed": False,
            "row0_origin_status": "row0_origin_exogenous_under_current_evidence",
            "recent_advances_are_row0_integration": False,
            "recent_advances_are_book_formula_or_parser_only": True,
            "criteria": criteria,
            "lookup_baseline_bits": row0_paid["baseline_lookup_bits"],
            "paid_anchor_full_pair_label_net_bits": row0_paid["summary"][
                "all_anchors_explicit_pair_label_net_bits"
            ],
            "rare_singletons_explicit_pair_label_net_bits": row0_paid["summary"][
                "rare_singletons_explicit_pair_label_net_bits"
            ],
            "surface_clue_status": row0_surface["decision"],
            "deep_provenance_decision": row0_deep["decision"],
            "partial_worksheet_decision": row0_worksheet["promotion_decision"],
            "paid_anchor_decision": row0_paid["decision"],
            "multi_cutoff_parser_validation": {
                "total_suffix_book_evaluations": gate77["summary"][
                    "total_suffix_book_evaluations"
                ],
                "total_roundtrip_book_evaluations": gate77["summary"][
                    "total_roundtrip_book_evaluations"
                ],
                "total_raw_positive_book_evaluations": gate77["summary"][
                    "total_raw_positive_book_evaluations"
                ],
                "parser_minus_same_policy_reprice_bits": gate77["summary"][
                    "total_parser_minus_same_policy_reprice_bits"
                ],
            },
            "path_stability_boundary": {
                "stable_exact_path_book_count": gate78["summary"][
                    "stable_exact_path_book_count"
                ],
                "unstable_exact_path_book_count": gate78["summary"][
                    "unstable_exact_path_book_count"
                ],
            },
            "global_item_literal_control": {
                "best_stable_exact_path_book_count": gate86["summary"][
                    "best_stable_exact_path_book_count"
                ],
                "promotes_global_control": gate86["summary"]["promotes_global_control"],
            },
            "skeleton_rule_boundary": {
                "simple_rule_covers_skeleton": gate100["summary"][
                    "simple_rule_covers_skeleton"
                ],
                "best_op_type_rule": gate100["summary"]["best_op_type_rule"],
                "best_length_rule": gate100["summary"]["best_length_rule"],
                "best_copy_length_rule": gate100["summary"]["best_copy_length_rule"],
                "best_literal_length_rule": gate100["summary"][
                    "best_literal_length_rule"
                ],
            },
            "operation_type_boundary": {
                "operation_count": gate107["summary"]["operation_count"],
                "explicit_op_type_fields_before_rule": gate107["summary"][
                    "explicit_op_type_fields_before_rule"
                ],
                "explicit_op_type_residual_after_rule": gate107["summary"][
                    "explicit_op_type_residual_after_rule"
                ],
                "length_atlas_records_retained": gate107["summary"][
                    "length_atlas_records_retained"
                ],
                "promotes_type_generator": gate107["summary"][
                    "promotes_type_generator"
                ],
            },
            "gates_checked": gates,
            "key_gate_sources": {
                "multi_cutoff_parser_validation": gate_by_number[77]["source"],
                "path_stability": gate_by_number[78]["source"],
                "global_item_literal_control": gate_by_number[86]["source"],
                "skeleton_rule_coverage": gate_by_number[100]["source"],
                "operation_type_dependency": gate_by_number[107]["source"],
            },
        },
        "taxonomy": {
            "PROMOTED_ORIGIN_FORMULA": [],
            "PROMOTED_MECHANICAL_CLUE": [
                {
                    "name": "ordered_surface_render_layer",
                    "evidence": "39 absent, 93 present, and 19/91 directed conflict",
                    "boundary": "surface clue only; no row0 pair-label origin",
                }
            ],
            "WEAK_CLUE": [
                {
                    "name": "partial_worksheet_model",
                    "evidence": "13 anchors reduce lookup before paying source/anchor cost",
                    "boundary": "plausible worksheet shape, not promoted",
                }
            ],
            "REJECTED_CONTROL": [
                {
                    "name": "paid_anchor_reduction_gate",
                    "evidence": "explicit pair+label anchor data is worse than lookup",
                    "net_bits": row0_paid["summary"][
                        "all_anchors_explicit_pair_label_net_bits"
                    ],
                },
                {
                    "name": "skeleton_simple_rule_coverage",
                    "evidence": "source-free simple rules do not cover operation lengths or skeleton",
                    "best_length_rule": gate100["summary"]["best_length_rule"],
                },
            ],
            "BLOCKED_NEEDS_EXTERNAL_SOURCE": [
                {
                    "name": "cipsoft_or_authorial_row0_origin",
                    "evidence": "local project provenance is partially traced, but primary origin remains untraced",
                }
            ],
            "AUDIT_ONLY": [
                {
                    "name": "recent_formula_gates_76_107",
                    "evidence": "parser/skeleton/type evidence strengthens the book-generation method while assuming row0",
                    "boundary": "row0 unchanged",
                }
            ],
        },
        "decision": {
            "row0_origin_status": "unchanged_exogenous",
            "recent_advances_status": "book_formula_and_parser_only",
            "row0_scoreboard_status": "unchanged_no_origin_formula_promoted",
            "compression_bound_status": "unchanged_8154_676268",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    criteria = s["criteria"]
    lines = [
        "# Recent Gates Row0 Compatibility Refresh",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This refresh checks gates `76..107` against the independent row0",
        "provenance front. The interval covers multi-cutoff parser validation,",
        "path-stability controls, decoder/source-policy controls, skeleton",
        "dependency ledgers, and the operation-type dependency ledger.",
        "",
        "## Decision",
        "",
        "- `row0 unchanged`.",
        f"- Row0 status: `{s['row0_origin_status']}`.",
        "- Recent advances are book-formula/parser improvements, not row0-origin integration.",
        f"- Current compression bound remains `{s['current_compression_bound_bits']:.6f}` bits.",
        "- No plaintext, translation, fan gloss, or case reopening is introduced.",
        "",
        "## Criteria Check",
        "",
        "| Criterion | Result |",
        "|---|---|",
    ]
    for key, value in criteria.items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(
        [
            "",
            "## Row0 Evidence Retained",
            "",
            f"- Lookup baseline: `{s['lookup_baseline_bits']:.3f}` bits.",
            f"- Full 13-anchor explicit pair+label net: `{s['paid_anchor_full_pair_label_net_bits']:.3f}` bits.",
            f"- Rare-singleton explicit pair+label net: `{s['rare_singletons_explicit_pair_label_net_bits']:.3f}` bits.",
            f"- Provenance decision: `{s['deep_provenance_decision']}`.",
            f"- Surface clue decision: `{s['surface_clue_status']}`.",
            f"- Partial worksheet decision: `{s['partial_worksheet_decision']}`.",
            f"- Paid anchor decision: `{s['paid_anchor_decision']}`.",
            "",
            "## Recent Formula Evidence",
            "",
            f"- Gates checked: `{s['gate_count_checked']}` (`{GATE_START}..{GATE_END}`).",
            f"- Multi-cutoff parser: `{s['multi_cutoff_parser_validation']['total_roundtrip_book_evaluations']}/{s['multi_cutoff_parser_validation']['total_suffix_book_evaluations']}` roundtrip and `{s['multi_cutoff_parser_validation']['total_raw_positive_book_evaluations']}/{s['multi_cutoff_parser_validation']['total_suffix_book_evaluations']}` raw-positive suffix evaluations.",
            f"- Path stability: `{s['path_stability_boundary']['stable_exact_path_book_count']}` stable vs `{s['path_stability_boundary']['unstable_exact_path_book_count']}` unstable multi-cutoff books before later controls.",
            f"- Global item/literal control stable books: `{s['global_item_literal_control']['best_stable_exact_path_book_count']}`, promoted: `{s['global_item_literal_control']['promotes_global_control']}`.",
            f"- Skeleton simple-rule coverage promoted: `{s['skeleton_rule_boundary']['simple_rule_covers_skeleton']}`.",
            f"- Operation-type residual after availability/exception rule: `{s['operation_type_boundary']['explicit_op_type_residual_after_rule']}` of `{s['operation_type_boundary']['explicit_op_type_fields_before_rule']}` fields.",
            f"- Length atlas records retained: `{s['operation_type_boundary']['length_atlas_records_retained']}`.",
            "",
            "## Taxonomy",
            "",
            "| Bucket | Result |",
            "|---|---|",
            "| `PROMOTED_ORIGIN_FORMULA` | none |",
            "| `PROMOTED_MECHANICAL_CLUE` | ordered-surface clue only (`39`, `93`, `19/91`) |",
            "| `WEAK_CLUE` | partial worksheet shape only |",
            "| `REJECTED_CONTROL` | paid anchor reduction; skeleton simple-rule coverage |",
            "| `BLOCKED_NEEDS_EXTERNAL_SOURCE` | CipSoft/authorial row0 origin |",
            "| `AUDIT_ONLY` | gates `76..107`, book formula/parser only |",
            "",
            "## Gate Families",
            "",
            "| Family | Count |",
            "|---|---:|",
        ]
    )
    for family, count in sorted(s["gate_family_counts"].items()):
        lines.append(f"| `{family}` | `{count}` |")

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The recent formula/parser work remains compatible with row0 being an",
            "accepted mechanical substrate. It does not derive row0, does not",
            "predict pair labels under holdout, does not beat the paid row0 lookup",
            "baseline, and does not add CipSoft/authorial provenance.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
