from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE100 = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"


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


def group_books(
    by_book: dict[int, list[dict[str, Any]]],
    fn: Callable[[list[dict[str, Any]]], Any],
) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for book, rows in by_book.items():
        value = fn(rows)
        key = stable_hash(value)
        groups.setdefault(key, {"books": [], "value": value})
        groups[key]["books"].append(book)
    for row in groups.values():
        row["books"] = sorted(row["books"])
    return groups


def summarize_groups(groups: dict[str, dict[str, Any]]) -> dict[str, Any]:
    clusters = sorted(
        [row["books"] for row in groups.values() if len(row["books"]) > 1],
        key=lambda books: (-len(books), books),
    )
    size_histogram = Counter(len(row["books"]) for row in groups.values())
    return {
        "unique_template_count": len(groups),
        "reused_cluster_count": len(clusters),
        "reused_book_count": sum(len(cluster) for cluster in clusters),
        "largest_cluster_size": max((len(row["books"]) for row in groups.values()), default=0),
        "cluster_size_histogram": {
            str(size): count for size, count in sorted(size_histogram.items())
        },
        "reused_clusters": clusters,
    }


def make_result() -> dict[str, Any]:
    gate100 = load_json(GATE100)
    assert_boundary("skeleton_rule_coverage_audit", gate100)
    if gate100["classification"] != "skeleton_simple_rule_coverage_insufficient":
        raise RuntimeError("gate100 did not reject simple skeleton rules")

    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in gate100["skeleton_rows"]:
        by_book[int(row["book"])].append(row)
    for rows in by_book.values():
        rows.sort(key=lambda row: int(row["op_index"]))

    extractors = {
        "exact_skeleton": lambda rows: [
            {
                "type": row["type"],
                "target_start": int(row["target_start"]),
                "length": int(row["length"]),
            }
            for row in rows
        ],
        "type_sequence": lambda rows: [row["type"] for row in rows],
        "length_sequence": lambda rows: [int(row["length"]) for row in rows],
        "aggregate_profile": lambda rows: {
            "op_count": len(rows),
            "copy_count": sum(1 for row in rows if row["type"] == "copy"),
            "literal_count": sum(1 for row in rows if row["type"] == "literal"),
            "copied_digits": sum(
                int(row["length"]) for row in rows if row["type"] == "copy"
            ),
            "literal_digits": sum(
                int(row["length"]) for row in rows if row["type"] == "literal"
            ),
        },
    }
    group_summaries = {}
    group_examples = {}
    for name, extractor in extractors.items():
        groups = group_books(by_book, extractor)
        group_summaries[name] = summarize_groups(groups)
        group_examples[name] = {
            key: {"books": value["books"], "value": value["value"]}
            for key, value in groups.items()
            if len(value["books"]) > 1
        }

    exact = group_summaries["exact_skeleton"]
    type_seq = group_summaries["type_sequence"]
    template_reuse_promotable = (
        exact["unique_template_count"] <= 10
        and exact["reused_book_count"] >= 30
    )
    classification = (
        "skeleton_template_reuse_promotable_candidate"
        if template_reuse_promotable
        else "skeleton_template_reuse_sparse"
    )

    return {
        "schema": "skeleton_template_reuse_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate100_skeleton_rule_coverage": rel(GATE100),
        },
        "scope": {
            "analysis_only": True,
            "book_count": len(by_book),
            "tests_exact_template_reuse": True,
            "tests_type_motif_reuse": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_count": len(by_book),
            "exact_unique_template_count": exact["unique_template_count"],
            "exact_reused_cluster_count": exact["reused_cluster_count"],
            "exact_reused_book_count": exact["reused_book_count"],
            "exact_largest_cluster_size": exact["largest_cluster_size"],
            "type_sequence_unique_count": type_seq["unique_template_count"],
            "type_sequence_reused_book_count": type_seq["reused_book_count"],
            "type_sequence_largest_cluster_size": type_seq["largest_cluster_size"],
            "template_reuse_promotable": template_reuse_promotable,
            "interpretation": (
                "Exact skeleton template reuse is sparse: most books still need "
                "their own length/target skeleton. Type-sequence motifs repeat, "
                "but length-bearing templates do not repeat enough to replace "
                "the skeleton atlas with a small template library."
            ),
        },
        "group_summaries": group_summaries,
        "group_examples": group_examples,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "template_reuse_insufficient_atlas_retained",
            "skeleton_status": "stable_atlas_not_template_generator",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "101_skeleton_template_reuse_audit.json"
    md_path = TEST_RESULTS / "101_skeleton_template_reuse_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    exact = result["group_summaries"]["exact_skeleton"]
    types = result["group_summaries"]["type_sequence"]
    lines = [
        "# Skeleton Template Reuse Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 100 rejected simple rules for generating the skeleton. This audit",
        "checks whether the remaining skeleton atlas can be reduced by exact",
        "template reuse or type-sequence motif reuse across books.",
        "",
        "## Result",
        "",
        f"- Books: `{s['book_count']}`.",
        f"- Exact skeleton unique templates: `{s['exact_unique_template_count']}`.",
        f"- Exact reused clusters/books: `{s['exact_reused_cluster_count']}` / `{s['exact_reused_book_count']}`.",
        f"- Exact largest cluster: `{s['exact_largest_cluster_size']}`.",
        f"- Type-sequence unique templates: `{s['type_sequence_unique_count']}`.",
        f"- Type-sequence reused books: `{s['type_sequence_reused_book_count']}`.",
        f"- Type-sequence largest cluster: `{s['type_sequence_largest_cluster_size']}`.",
        f"- Exact reused clusters: `{exact['reused_clusters']}`.",
        f"- Type-sequence reused clusters: `{types['reused_clusters']}`.",
        "",
        "## Decision",
        "",
        f"- Template reuse promotable: `{s['template_reuse_promotable']}`.",
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
