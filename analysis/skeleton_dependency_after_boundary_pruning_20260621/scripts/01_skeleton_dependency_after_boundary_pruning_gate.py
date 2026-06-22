from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
PRUNING_GATE = (
    ROOT
    / "analysis"
    / "target_digit_boundary_pruning_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_boundary_pruning_gate.json"
)
TYPE_GATE = (
    ROOT
    / "analysis"
    / "target_digit_boundary_type_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_digit_boundary_type_gate.json"
)

OUT_STEM = "01_skeleton_dependency_after_boundary_pruning_gate"


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


def book_rows(books: dict[int, str], ops_by_book: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for book in range(10, 70):
        op_count = len(ops_by_book[str(book)])
        internal_cutpoints = op_count - 1
        rows.append(
            {
                "book": book,
                "book_length": len(books[book]),
                "candidate_cutpoint_positions": len(books[book]) - 1,
                "op_count": op_count,
                "internal_cutpoints": internal_cutpoints,
                "op_count_uniform_bits": math.log2(len(books[book])),
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    pruning = load_json(PRUNING_GATE)
    type_gate = load_json(TYPE_GATE)
    copy_ledger = load_json(COPY_SOURCE_LEDGER)
    assert_boundary("target_digit_boundary_pruning_gate", pruning)
    assert_boundary("target_digit_boundary_type_gate", type_gate)
    assert_boundary("copy_source_ledger", copy_ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    rows = book_rows(books, copy_ledger["canonical_ops_by_book"])
    pruning_summary = pruning["summary"]
    type_summary = type_gate["summary"]
    op_count_bits = sum(row["op_count_uniform_bits"] for row in rows)
    exact_conditional_cutpoint_bits = float(pruning_summary["best_baseline_bits"])
    pruned_conditional_cutpoint_bits = float(
        pruning_summary["best_model_bits_after_q_charge"]
    )
    exact_full_cutpoint_atlas_bits = op_count_bits + exact_conditional_cutpoint_bits
    pruned_full_cutpoint_atlas_bits = op_count_bits + pruned_conditional_cutpoint_bits
    cutpoint_saving = exact_full_cutpoint_atlas_bits - pruned_full_cutpoint_atlas_bits
    op_count_fraction_after_pruning = op_count_bits / pruned_full_cutpoint_atlas_bits
    type_transfer_rejected = not bool(
        type_gate["decision"]["promotes_boundary_type_rule"]
    )
    promotes_generator = False
    promotes_dependency_reduction = (
        bool(pruning["decision"]["promotes_boundary_pruning_clue"])
        and cutpoint_saving > 0
        and type_transfer_rejected
    )
    op_count_histogram = Counter(str(row["op_count"]) for row in rows)
    summary = {
        "book_count": len(rows),
        "internal_cutpoint_count": sum(row["internal_cutpoints"] for row in rows),
        "candidate_cutpoint_positions": sum(
            row["candidate_cutpoint_positions"] for row in rows
        ),
        "op_count_uniform_bits": op_count_bits,
        "exact_conditional_cutpoint_bits": exact_conditional_cutpoint_bits,
        "pruned_conditional_cutpoint_bits": pruned_conditional_cutpoint_bits,
        "exact_full_cutpoint_atlas_bits": exact_full_cutpoint_atlas_bits,
        "pruned_full_cutpoint_atlas_bits": pruned_full_cutpoint_atlas_bits,
        "full_cutpoint_atlas_saving_bits": cutpoint_saving,
        "op_count_fraction_after_pruning": op_count_fraction_after_pruning,
        "pruning_q": pruning_summary["best_q"],
        "pruning_hits": pruning_summary["best_hit_count"],
        "pruning_misses": pruning_summary["best_miss_count"],
        "type_transfer_status": "rejected",
        "type_majority_hits": type_summary["majority_hits"],
        "type_best_predicate_hits": type_summary["best_predicate"]["hits"],
        "op_count_histogram": dict(sorted(op_count_histogram.items(), key=lambda item: int(item[0]))),
        "promotes_dependency_reduction": promotes_dependency_reduction,
        "promotes_generator": promotes_generator,
        "interpretation": (
            "Boundary pruning reduces the conditional cutpoint atlas even after "
            "charging q, but the number of cutpoints per book remains external "
            "and operation type transfer is rejected. This is a dependency "
            "reduction ledger, not a source-free skeleton generator."
        ),
    }
    return {
        "schema": "skeleton_dependency_after_boundary_pruning_gate_v1",
        "scope": "analysis_only_skeleton_dependency_ledger",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "target_digit_boundary_pruning_gate": rel(PRUNING_GATE),
            "target_digit_boundary_type_gate": rel(TYPE_GATE),
        },
        "book_rows": rows,
        "summary": summary,
        "classification": "skeleton_dependency_reduced_not_generated",
        "decision": {
            "promotes_dependency_reduction": promotes_dependency_reduction,
            "promotes_generator": promotes_generator,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Skeleton Dependency After Boundary Pruning Gate",
        "",
        "Classification: `skeleton_dependency_reduced_not_generated`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Consolidate how much the promoted `prev2` boundary-pruning clue",
        "reduces skeleton dependency once the number of cutpoints per book is",
        "also charged.",
        "",
        "## Summary",
        "",
        f"- Books/internal cutpoints/candidates: `{s['book_count']}` / `{s['internal_cutpoint_count']}` / `{s['candidate_cutpoint_positions']}`.",
        f"- Op-count uniform bits: `{s['op_count_uniform_bits']:.3f}`.",
        f"- Exact conditional cutpoint bits: `{s['exact_conditional_cutpoint_bits']:.3f}`.",
        f"- Pruned conditional cutpoint bits: `{s['pruned_conditional_cutpoint_bits']:.3f}`.",
        f"- Exact full cutpoint atlas bits: `{s['exact_full_cutpoint_atlas_bits']:.3f}`.",
        f"- Pruned full cutpoint atlas bits: `{s['pruned_full_cutpoint_atlas_bits']:.3f}`.",
        f"- Full cutpoint atlas saving: `{s['full_cutpoint_atlas_saving_bits']:.3f}` bits.",
        f"- Op-count share after pruning: `{s['op_count_fraction_after_pruning']:.6f}`.",
        f"- Pruning hits/misses: `{s['pruning_hits']}` / `{s['pruning_misses']}`.",
        f"- Type transfer: `{s['type_transfer_status']}`.",
        "",
        "## Decision",
        "",
        "- Promotes dependency reduction: `True`.",
        "- Promotes skeleton generator: `False`.",
        "- The `prev2` boundary clue reduces the cutpoint atlas but still grants op counts and residual endpoint selection.",
        "- Operation type is not explained by the boundary clue.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
