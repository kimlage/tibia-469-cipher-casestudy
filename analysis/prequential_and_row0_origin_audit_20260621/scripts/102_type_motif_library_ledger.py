from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE100 = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"
GATE101 = TEST_RESULTS / "101_skeleton_template_reuse_audit.json"


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
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def make_result() -> dict[str, Any]:
    gate100 = load_json(GATE100)
    gate101 = load_json(GATE101)
    assert_boundary("skeleton_rule_coverage_audit", gate100)
    assert_boundary("skeleton_template_reuse_audit", gate101)
    if gate101["classification"] != "skeleton_template_reuse_sparse":
        raise RuntimeError("gate101 did not reject exact template reuse")

    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in gate100["skeleton_rows"]:
        by_book[int(row["book"])].append(row)
    for rows in by_book.values():
        rows.sort(key=lambda row: int(row["op_index"]))

    type_groups: dict[str, dict[str, Any]] = {}
    for book, rows in sorted(by_book.items()):
        sequence = [row["type"] for row in rows]
        key = stable_hash(sequence)
        type_groups.setdefault(key, {"sequence": sequence, "books": []})
        type_groups[key]["books"].append(book)
    for group in type_groups.values():
        group["books"] = sorted(group["books"])

    exact_atlas_records = sum(len(rows) for rows in by_book.values())
    type_library_entries = sum(len(group["sequence"]) for group in type_groups.values())
    book_assignment_records = len(by_book)
    residual_length_target_records = exact_atlas_records
    type_library_total_records = (
        type_library_entries + book_assignment_records + residual_length_target_records
    )
    type_only_delta_vs_exact_atlas = (
        type_library_entries + book_assignment_records - exact_atlas_records
    )
    full_representation_delta_vs_exact_atlas = (
        type_library_total_records - exact_atlas_records
    )
    reused_groups = [
        {"books": group["books"], "sequence": group["sequence"]}
        for group in type_groups.values()
        if len(group["books"]) > 1
    ]
    reused_groups.sort(key=lambda row: (-len(row["books"]), row["books"]))

    promotes_type_library = (
        type_library_total_records < exact_atlas_records
        and residual_length_target_records == 0
    )
    classification = (
        "type_motif_library_promotable"
        if promotes_type_library
        else "type_motif_library_not_promoted"
    )
    return {
        "schema": "type_motif_library_ledger.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate100_skeleton_rule_coverage": rel(GATE100),
            "gate101_skeleton_template_reuse": rel(GATE101),
        },
        "scope": {
            "analysis_only": True,
            "ledger_only": True,
            "tests_type_sequence_library": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_count": len(by_book),
            "exact_atlas_records": exact_atlas_records,
            "type_template_count": len(type_groups),
            "type_library_entries": type_library_entries,
            "book_assignment_records": book_assignment_records,
            "residual_length_target_records": residual_length_target_records,
            "type_library_total_records": type_library_total_records,
            "type_only_delta_vs_exact_atlas": type_only_delta_vs_exact_atlas,
            "full_representation_delta_vs_exact_atlas": full_representation_delta_vs_exact_atlas,
            "reused_group_count": len(reused_groups),
            "reused_book_count": sum(len(group["books"]) for group in reused_groups),
            "largest_reused_group": max((len(group["books"]) for group in reused_groups), default=0),
            "promotes_type_library": promotes_type_library,
            "interpretation": (
                "Type-sequence motifs repeat, but a type library only saves "
                "eight type/assignment records before residual length and target "
                "positions are paid. With those residuals included, the type-"
                "motif representation is larger than the exact skeleton atlas, "
                "so it is not promoted."
            ),
        },
        "reused_type_groups": reused_groups,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "type_motif_library_rejected",
            "skeleton_status": "exact_atlas_retained",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "102_type_motif_library_ledger.json"
    md_path = TEST_RESULTS / "102_type_motif_library_ledger.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Type Motif Library Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 101 found repeated operation-type motifs but sparse exact skeleton",
        "template reuse. This ledger checks whether a type-sequence library reduces",
        "the materialized skeleton once book assignments and remaining length/target",
        "records are counted.",
        "",
        "## Ledger",
        "",
        f"- Books: `{s['book_count']}`.",
        f"- Exact skeleton atlas records: `{s['exact_atlas_records']}`.",
        f"- Type templates: `{s['type_template_count']}`.",
        f"- Type-library entries: `{s['type_library_entries']}`.",
        f"- Book-assignment records: `{s['book_assignment_records']}`.",
        f"- Residual length/target records: `{s['residual_length_target_records']}`.",
        f"- Type-library total records: `{s['type_library_total_records']}`.",
        f"- Type-only delta vs exact atlas: `{s['type_only_delta_vs_exact_atlas']}`.",
        f"- Full representation delta vs exact atlas: `{s['full_representation_delta_vs_exact_atlas']}`.",
        f"- Reused type groups/books: `{s['reused_group_count']}` / `{s['reused_book_count']}`.",
        f"- Largest reused type group: `{s['largest_reused_group']}`.",
        "",
        "## Decision",
        "",
        f"- Promotes type library: `{s['promotes_type_library']}`.",
        f"- {s['interpretation']}",
        "- No compression-bound change is introduced.",
        "- No formula is emitted.",
        "- Row0 remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
