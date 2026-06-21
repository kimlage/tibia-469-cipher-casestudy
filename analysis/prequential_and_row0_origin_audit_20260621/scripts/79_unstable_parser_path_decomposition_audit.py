from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE77_SCRIPT = HERE / "scripts" / "77_multi_cutoff_sparse_suffix_parser_validation.py"
GATE78_SCRIPT = HERE / "scripts" / "78_multi_cutoff_parser_path_stability_audit.py"
GATE78 = TEST_RESULTS / "78_multi_cutoff_parser_path_stability_audit.json"


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


def target_profile(ops: list[dict[str, Any]]) -> tuple[tuple[Any, ...], ...]:
    return tuple((op["type"], op["target_start"], op["length"]) for op in ops)


def type_length_profile(ops: list[dict[str, Any]]) -> tuple[tuple[Any, ...], ...]:
    return tuple((op["type"], op["length"]) for op in ops)


def type_profile(ops: list[dict[str, Any]]) -> tuple[str, ...]:
    return tuple(op["type"] for op in ops)


def source_profile(ops: list[dict[str, Any]]) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            op["target_start"],
            op.get("source"),
            op.get("source_default"),
        )
        for op in ops
        if op["type"] == "copy"
    )


def classify_variants(variants: list[dict[str, Any]]) -> str:
    target_profiles = {target_profile(variant["ops"]) for variant in variants}
    source_profiles = {source_profile(variant["ops"]) for variant in variants}
    type_length_profiles = {
        type_length_profile(variant["ops"]) for variant in variants
    }
    type_profiles = {type_profile(variant["ops"]) for variant in variants}
    op_counts = {len(variant["ops"]) for variant in variants}

    if len(target_profiles) == 1 and len(source_profiles) > 1:
        return "source_selection_only"
    if len(type_length_profiles) == 1 and len(source_profiles) > 1:
        return "source_selection_same_lengths"
    if len(type_profiles) == 1 and len(op_counts) == 1:
        return "boundary_shift_same_shape"
    if len(type_profiles) == 1:
        return "same_type_sequence_length_or_count_change"
    return "segmentation_shape_change"


def summarize_variant(variant: dict[str, Any]) -> dict[str, Any]:
    ops = variant["ops"]
    return {
        "signature": variant["signature"],
        "cutoffs": variant["cutoffs"],
        "op_count": len(ops),
        "type_sequence": "".join("C" if op["type"] == "copy" else "L" for op in ops),
        "length_sequence": [op["length"] for op in ops],
        "copy_sources": [op.get("source") for op in ops if op["type"] == "copy"],
        "copy_default_flags": [
            op.get("source_default") for op in ops if op["type"] == "copy"
        ],
        "literal_digits": sum(op["length"] for op in ops if op["type"] == "literal"),
        "copied_digits": sum(op["length"] for op in ops if op["type"] == "copy"),
        "parser_bits_by_cutoff": variant["parser_bits_by_cutoff"],
    }


def collect_unstable_variants() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    gate78 = load_json(GATE78)
    assert_boundary("multi_cutoff_parser_path_stability", gate78)
    unstable_books = [
        row["book"]
        for row in gate78["summary"]["book_rows"]
        if row["cutoff_count"] >= 2 and not row["stable_exact_path"]
    ]
    gate77_module = load_module("gate77_multi_cutoff_validation", GATE77_SCRIPT)
    gate78_module = load_module("gate78_path_stability", GATE78_SCRIPT)

    rows_by_book: dict[int, list[dict[str, Any]]] = {book: [] for book in unstable_books}
    for cutoff in gate77_module.CUTOFFS:
        for row in gate78_module.run_cutoff(cutoff, gate77_module):
            if row["book"] in rows_by_book:
                rows_by_book[row["book"]].append(row)

    book_rows = []
    for book in sorted(rows_by_book):
        rows = rows_by_book[book]
        signatures: dict[str, dict[str, Any]] = {}
        for row in rows:
            sig = row["signature"]
            signatures.setdefault(
                sig,
                {
                    "signature": sig,
                    "cutoffs": [],
                    "ops": row["signature_ops"],
                    "parser_bits_by_cutoff": {},
                    "transition_evaluations_by_cutoff": {},
                },
            )
            signatures[sig]["cutoffs"].append(row["cutoff"])
            signatures[sig]["parser_bits_by_cutoff"][str(row["cutoff"])] = row[
                "parser_bits"
            ]
            signatures[sig]["transition_evaluations_by_cutoff"][str(row["cutoff"])] = row[
                "transition_evaluations"
            ]
        variants = sorted(
            signatures.values(),
            key=lambda item: (-len(item["cutoffs"]), item["cutoffs"][0], item["signature"]),
        )
        classification = classify_variants(variants)
        book_rows.append(
            {
                "book": book,
                "cutoffs_tested": sorted(row["cutoff"] for row in rows),
                "variant_count": len(variants),
                "instability_class": classification,
                "dominant_cutoffs": variants[0]["cutoffs"],
                "variant_summaries": [summarize_variant(variant) for variant in variants],
            }
        )
    return gate78, book_rows


def make_result() -> dict[str, Any]:
    gate78, book_rows = collect_unstable_variants()
    class_counts: dict[str, int] = {}
    for row in book_rows:
        class_counts[row["instability_class"]] = (
            class_counts.get(row["instability_class"], 0) + 1
        )
    worst = sorted(
        book_rows,
        key=lambda row: (-row["variant_count"], row["book"]),
    )[:10]
    return {
        "schema": "unstable_parser_path_decomposition_audit.v1",
        "classification": "unstable_parser_paths_decomposed",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate78_path_stability": rel(GATE78),
            "gate78_path_replay": rel(GATE78_SCRIPT),
            "gate77_context_loader": rel(GATE77_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "unstable_books_from_gate78": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "unstable_book_count": len(book_rows),
            "class_counts": class_counts,
            "max_variant_count": max(row["variant_count"] for row in book_rows),
            "worst_books": [
                {
                    "book": row["book"],
                    "variant_count": row["variant_count"],
                    "instability_class": row["instability_class"],
                    "variant_cutoffs": [
                        variant["cutoffs"] for variant in row["variant_summaries"]
                    ],
                }
                for row in worst
            ],
            "book_rows": book_rows,
            "interpretation": (
                "The unstable parser paths are primarily boundary/segmentation "
                "choice problems rather than pure source-address swaps. This "
                "narrows the next structural task: stabilize copy boundary "
                "selection under frozen prefixes, especially book 65, instead "
                "of searching for another compression-only parameter."
            ),
            "upstream_gate78_summary": {
                "stable_exact_path_book_count": gate78["summary"][
                    "stable_exact_path_book_count"
                ],
                "unstable_exact_path_book_count": gate78["summary"][
                    "unstable_exact_path_book_count"
                ],
                "stable_exact_path_fraction": gate78["summary"][
                    "stable_exact_path_fraction"
                ],
            },
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "unstable_paths_localized_to_boundary_selection",
            "generation_explanation_status": "next_work_is_boundary_stability_not_micro_sweep",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "79_unstable_parser_path_decomposition_audit.json"
    md_path = TEST_RESULTS / "79_unstable_parser_path_decomposition_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Unstable Parser Path Decomposition Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 78 found `12` books whose exact parser paths change across frozen",
        "cutoffs. This gate decomposes those unstable paths into source-only",
        "changes, same-shape boundary shifts, or larger segmentation changes.",
        "",
        "## Summary",
        "",
        f"- Unstable books decomposed: `{s['unstable_book_count']}`.",
        f"- Class counts: `{s['class_counts']}`.",
        f"- Max variants in one book: `{s['max_variant_count']}`.",
        "",
        "## Worst Books",
        "",
        "| Book | Variants | Class | Variant cutoffs |",
        "|---:|---:|---|---|",
    ]
    for row in s["worst_books"]:
        lines.append(
            "| {book} | {variant_count} | `{instability_class}` | `{variant_cutoffs}` |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No corpus-wide formula promotion is introduced.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
