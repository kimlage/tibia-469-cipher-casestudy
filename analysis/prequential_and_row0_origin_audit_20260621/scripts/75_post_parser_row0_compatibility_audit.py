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

ROW0_BRIDGE = TEST_RESULTS / "47_row0_parallel_provenance_bridge_audit.json"
RECENT_FORMULA_ROW0 = TEST_RESULTS / "70_recent_formula_row0_compatibility_audit.json"
FINAL_DEPENDENCY = TEST_RESULTS / "71_final_formula_dependency_refresh_gate.json"
PARSER_FEASIBILITY = TEST_RESULTS / "72_final_source_length_parser_feasibility_audit.json"
BOOK_LOCAL_PARSER = TEST_RESULTS / "73_book_local_source_length_parser_probe.json"
SPARSE_HARD_BOOK = TEST_RESULTS / "74_sparse_hard_book_source_length_parser_gate.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_no_semantics(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")


def require_row0_unchanged(name: str, data: dict[str, Any]) -> None:
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} does not preserve row0 exogenous status")


def make_result() -> dict[str, Any]:
    deep = load_json(ROW0_DEEP_PROVENANCE)
    scoreboard = load_json(ROW0_SCOREBOARD)
    worksheet = load_json(ROW0_PARTIAL_WORKSHEET)
    surface = load_json(ROW0_SURFACE)
    paid = load_json(ROW0_PAID_ANCHOR)
    bridge = load_json(ROW0_BRIDGE)
    recent = load_json(RECENT_FORMULA_ROW0)
    final_dependency = load_json(FINAL_DEPENDENCY)
    parser_feasibility = load_json(PARSER_FEASIBILITY)
    book_local = load_json(BOOK_LOCAL_PARSER)
    sparse = load_json(SPARSE_HARD_BOOK)

    row0_inputs = {
        "row0_final_report": rel(ROW0_FINAL_REPORT),
        "row0_next_frontier_report": rel(ROW0_NEXT_FRONTIER_REPORT),
        "row0_deep_provenance": rel(ROW0_DEEP_PROVENANCE),
        "row0_scoreboard": rel(ROW0_SCOREBOARD),
        "row0_partial_worksheet": rel(ROW0_PARTIAL_WORKSHEET),
        "row0_surface_exception": rel(ROW0_SURFACE),
        "row0_paid_anchor": rel(ROW0_PAID_ANCHOR),
    }
    main_inputs = {
        "row0_parallel_bridge": rel(ROW0_BRIDGE),
        "recent_formula_row0_compatibility": rel(RECENT_FORMULA_ROW0),
        "final_formula_dependency": rel(FINAL_DEPENDENCY),
        "parser_feasibility": rel(PARSER_FEASIBILITY),
        "book_local_parser": rel(BOOK_LOCAL_PARSER),
        "sparse_hard_book_parser": rel(SPARSE_HARD_BOOK),
    }

    for name, data in [
        ("row0_deep_provenance", deep),
        ("row0_scoreboard", scoreboard),
        ("row0_partial_worksheet", worksheet),
        ("row0_surface_exception", surface),
        ("row0_paid_anchor", paid),
        ("row0_parallel_bridge", bridge),
        ("recent_formula_row0_compatibility", recent),
        ("final_formula_dependency", final_dependency),
        ("parser_feasibility", parser_feasibility),
        ("book_local_parser", book_local),
        ("sparse_hard_book_parser", sparse),
    ]:
        assert_no_semantics(name, data)

    for name, data in [
        ("row0_parallel_bridge", bridge),
        ("recent_formula_row0_compatibility", recent),
        ("final_formula_dependency", final_dependency),
        ("parser_feasibility", parser_feasibility),
        ("book_local_parser", book_local),
        ("sparse_hard_book_parser", sparse),
    ]:
        require_row0_unchanged(name, data)

    if recent["summary"]["row0_changed"]:
        raise RuntimeError("recent formula compatibility changed row0")
    if recent["summary"]["predicts_row0_labels_under_holdout"]:
        raise RuntimeError("recent formula unexpectedly predicts row0 labels")
    if recent["summary"]["beats_row0_lookup_after_cost"]:
        raise RuntimeError("recent formula unexpectedly beats row0 lookup")
    if paid["summary"]["full_explicit_pair_label_model_promoted"]:
        raise RuntimeError("paid worksheet anchors promoted unexpectedly")
    if paid["summary"]["controlled_paid_subset_promoted"]:
        raise RuntimeError("paid controlled subset promoted unexpectedly")
    if final_dependency["summary"]["declared_operation_dependency_fields"] != 609:
        raise RuntimeError("final dependency count changed")
    if sparse["summary"]["book_row"]["roundtrip_ok"] is not True:
        raise RuntimeError("sparse hard-book parser did not roundtrip")

    parser_gates = [
        {
            "source": rel(FINAL_DEPENDENCY),
            "classification": final_dependency["classification"],
            "result": "dependency_boundary_unchanged",
            "metric": "609 retained operation dependency fields",
            "row0_origin_status": final_dependency["decision"]["row0_origin_status"],
        },
        {
            "source": rel(PARSER_FEASIBILITY),
            "classification": parser_feasibility["classification"],
            "result": "parser_scoped_not_promoted",
            "metric": "1,966,897,365 transition proxy",
            "row0_origin_status": parser_feasibility["decision"]["row0_origin_status"],
        },
        {
            "source": rel(BOOK_LOCAL_PARSER),
            "classification": book_local["classification"],
            "result": "two_book_subset_roundtrips",
            "metric": "2/2 books, 125.866 parser bits",
            "row0_origin_status": book_local["decision"]["row0_origin_status"],
        },
        {
            "source": rel(SPARSE_HARD_BOOK),
            "classification": sparse["classification"],
            "result": "hard_book_sparse_roundtrip",
            "metric": "book 66, 41,832 transitions, 623.9x proxy reduction",
            "row0_origin_status": sparse["decision"]["row0_origin_status"],
        },
    ]

    return {
        "schema": "post_parser_row0_compatibility_audit.v1",
        "classification": "post_parser_advances_row0_unchanged",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "row0_inputs": row0_inputs,
            "main_formula_and_parser_inputs": main_inputs,
        },
        "summary": {
            "current_compression_bound_bits": recent["summary"][
                "current_compression_bound_bits"
            ],
            "row0_status": "row0_origin_exogenous_under_current_evidence",
            "row0_changed": False,
            "advances_checked": "post_partial_boundary_dependency_and_parser_gates_71_74",
            "advances_are_row0_integration": False,
            "advances_are_book_formula_or_parser_only": True,
            "predicts_row0_labels_under_holdout": False,
            "beats_row0_lookup_after_cost": False,
            "explains_39_93_19_91": False,
            "new_cipsoft_or_authorial_provenance": False,
            "promoted_origin_formula_count": 0,
            "lookup_baseline_bits": paid["baseline_lookup_bits"],
            "paid_anchor_full_pair_label_net_bits": paid["summary"][
                "all_anchors_explicit_pair_label_net_bits"
            ],
            "rare_singletons_explicit_pair_label_net_bits": paid["summary"][
                "rare_singletons_explicit_pair_label_net_bits"
            ],
            "surface_clue_status": surface["decision"],
            "deep_provenance_decision": deep["decision"],
            "row0_scoreboard_decision": scoreboard["decision"],
            "partial_worksheet_decision": worksheet["promotion_decision"],
            "paid_anchor_decision": paid["decision"],
            "parser_gates_checked": parser_gates,
        },
        "taxonomy": {
            "PROMOTED_ORIGIN_FORMULA": [],
            "PROMOTED_MECHANICAL_CLUE": [
                {
                    "name": "ordered_surface_render_layer",
                    "evidence": "39 absent, 93 present, and 19/91 directed conflict",
                    "boundary": "surface clue only; not a row0 label generator",
                }
            ],
            "WEAK_CLUE": [
                {
                    "name": "partial_worksheet_model",
                    "evidence": "13 anchors reduce lookup only before anchor/source costs",
                    "boundary": "plausible worksheet shape, not promoted",
                }
            ],
            "REJECTED_CONTROL": [
                {
                    "name": "paid_anchor_reduction_gate",
                    "evidence": "explicit pair+label anchor cost is worse than lookup",
                    "net_bits": paid["summary"][
                        "all_anchors_explicit_pair_label_net_bits"
                    ],
                }
            ],
            "BLOCKED_NEEDS_EXTERNAL_SOURCE": [
                {
                    "name": "cipsoft_or_authorial_row0_origin",
                    "evidence": "project provenance traced locally, but primary origin remains untraced",
                }
            ],
            "AUDIT_ONLY": [
                {
                    "name": "source_length_parser_gates_71_74",
                    "evidence": "dependency/parser implementation progress downstream from row0",
                    "boundary": "row0 unchanged; no origin formula or provenance added",
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
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "75_post_parser_row0_compatibility_audit.json"
    md_path = TEST_RESULTS / "75_post_parser_row0_compatibility_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Post-Parser Row0 Compatibility Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This gate checks whether the post-row0-bridge formula/dependency/parser",
        "advances in gates 71-74 change the independent row0-origin conclusion.",
        "They do not. The advances are downstream book-formula or source/length",
        "parser progress while row0 remains an assumed substrate.",
        "",
        "## Result",
        "",
        f"- Current compression bound checked: `{s['current_compression_bound_bits']:.6f}` bits.",
        f"- Row0 status: `{s['row0_status']}`.",
        "- `row0 changed`: `False`.",
        "- Advances are row0 integration: `False`.",
        "- Advances are book formula or parser only: `True`.",
        f"- Predicts row0 labels under holdout: `{s['predicts_row0_labels_under_holdout']}`.",
        f"- Beats row0 lookup after cost: `{s['beats_row0_lookup_after_cost']}`.",
        f"- Explains `39`, `93`, `19/91`: `{s['explains_39_93_19_91']}`.",
        f"- New CipSoft/authorial provenance: `{s['new_cipsoft_or_authorial_provenance']}`.",
        f"- Promoted origin formulas: `{s['promoted_origin_formula_count']}`.",
        "",
        "## Gates Checked",
        "",
        "| Source | Classification | Result | Metric | Row0 status |",
        "|---|---|---|---:|---|",
    ]
    for row in s["parser_gates_checked"]:
        lines.append(
            "| `{source}` | `{classification}` | `{result}` | `{metric}` | `{row0_origin_status}` |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Row0 Compatibility Checks",
            "",
            "| Check | Outcome | Interpretation |",
            "|---|---|---|",
            "| Row0 label holdout prediction | `False` | Gates 71-74 model copy source/length and parser execution, not row0 pair labels. |",
            "| Lookup reduction after rule/anchor cost | `False` | Paid worksheet anchors remain negative after explicit pair+label cost. |",
            "| `39` / `93` / `19/91` explanation | `False` | The ordered-surface facts remain a promoted mechanical clue only. |",
            "| New provenance | `False` | Local provenance is partially traced; CipSoft/authorial origin remains untraced. |",
            "| Formula assumes row0 | `True` | The book-generation/parser gates operate downstream from row0. |",
            "",
            "## Taxonomy",
            "",
            "- `PROMOTED_ORIGIN_FORMULA`: `0`",
            "- `PROMOTED_MECHANICAL_CLUE`: ordered-surface/render layer only",
            "- `WEAK_CLUE`: partial worksheet shape only",
            "- `REJECTED_CONTROL`: paid anchor reduction gate",
            "- `BLOCKED_NEEDS_EXTERNAL_SOURCE`: CipSoft/authorial row0 origin",
            "- `AUDIT_ONLY`: gates 71-74 dependency/parser progress",
            "",
            "## Decision",
            "",
            "- `row0 unchanged`.",
            "- The post-bridge advances are book-formula/parser progress, not row0-origin integration.",
            "- No row0-origin formula is promoted.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
