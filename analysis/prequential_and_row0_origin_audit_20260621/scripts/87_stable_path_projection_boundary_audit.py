from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE86_SCRIPT = HERE / "scripts" / "86_global_item_literal_length_control_gate.py"
GATE86 = TEST_RESULTS / "86_global_item_literal_length_control_gate.json"
GATE71 = TEST_RESULTS / "71_final_formula_dependency_refresh_gate.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

BEST_MODE = "payload_uniform_no_item_or_literal_length"


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


def stable_mode_names(gate86: dict[str, Any]) -> list[str]:
    return [
        row["cost_mode"]
        for row in gate86["summary"]["mode_summaries"]
        if row["stable_exact_path_book_count"] == 50
        and row["raw_positive_book_evaluations"] == 175
        and row["roundtrip_book_evaluations"] == 175
    ]


def summarize_projection(rows: list[dict[str, Any]], books: dict[str, str]) -> dict[str, Any]:
    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_book.setdefault(int(row["book"]), []).append(row)

    book_summaries = []
    canonical_totals = {
        "parsed_book_count": 0,
        "canonical_op_count": 0,
        "canonical_literal_runs": 0,
        "canonical_literal_digits": 0,
        "canonical_copy_items": 0,
        "canonical_copied_digits": 0,
        "canonical_transition_evaluations": 0,
        "canonical_visited_states": 0,
    }
    for book in sorted(by_book):
        book_rows = sorted(by_book[book], key=lambda row: int(row["cutoff"]))
        signatures = sorted({row["signature"] for row in book_rows})
        canonical = book_rows[0]
        stable = len(signatures) == 1
        if stable:
            canonical_totals["parsed_book_count"] += 1
            canonical_totals["canonical_op_count"] += int(canonical["op_count"])
            canonical_totals["canonical_literal_runs"] += int(canonical["literal_runs"])
            canonical_totals["canonical_literal_digits"] += int(canonical["literal_digits"])
            canonical_totals["canonical_copy_items"] += int(canonical["copy_items"])
            canonical_totals["canonical_copied_digits"] += int(canonical["copied_digits"])
            canonical_totals["canonical_transition_evaluations"] += int(
                canonical["transition_evaluations"]
            )
            canonical_totals["canonical_visited_states"] += int(canonical["visited_state_count"])
        book_summaries.append(
            {
                "book": book,
                "cutoffs": [int(row["cutoff"]) for row in book_rows],
                "cutoff_count": len(book_rows),
                "signature_count": len(signatures),
                "stable_exact_path": stable,
                "canonical_cutoff": int(canonical["cutoff"]),
                "canonical_op_count": int(canonical["op_count"]),
                "canonical_literal_runs": int(canonical["literal_runs"]),
                "canonical_literal_digits": int(canonical["literal_digits"]),
                "canonical_copy_items": int(canonical["copy_items"]),
                "canonical_copied_digits": int(canonical["copied_digits"]),
                "canonical_parser_bits": float(canonical["parser_bits"]),
            }
        )

    seed_books = list(range(10))
    single_cutoff_books = [
        row["book"] for row in book_summaries if row["cutoff_count"] == 1
    ]
    multi_cutoff_books = [
        row["book"] for row in book_summaries if row["cutoff_count"] >= 2
    ]
    unstable_books = [row["book"] for row in book_summaries if not row["stable_exact_path"]]
    seed_digits = sum(len(books[str(book)]) for book in seed_books)
    total_digits = sum(len(text) for text in books.values())

    return {
        **canonical_totals,
        "target_book_count": len(books),
        "seed_books": seed_books,
        "seed_book_count": len(seed_books),
        "seed_digits": seed_digits,
        "parsed_books": sorted(by_book),
        "single_cutoff_only_books": single_cutoff_books,
        "single_cutoff_only_book_count": len(single_cutoff_books),
        "multi_cutoff_books": multi_cutoff_books,
        "multi_cutoff_book_count": len(multi_cutoff_books),
        "multi_cutoff_stable_book_count": sum(
            1 for row in book_summaries if row["cutoff_count"] >= 2 and row["stable_exact_path"]
        ),
        "unstable_books": unstable_books,
        "stable_book_count": sum(1 for row in book_summaries if row["stable_exact_path"]),
        "total_digit_count": total_digits,
        "coverage_digit_count": seed_digits
        + canonical_totals["canonical_literal_digits"]
        + canonical_totals["canonical_copied_digits"],
        "book_summaries": book_summaries,
    }


def make_result() -> dict[str, Any]:
    gate86 = load_json(GATE86)
    gate71 = load_json(GATE71)
    assert_boundary("global_item_literal_length_control_gate", gate86)
    assert_boundary("final_formula_dependency_refresh_gate", gate71)
    if gate86["classification"] != "global_item_literal_control_closes_path_stability":
        raise RuntimeError("gate86 did not close path stability")
    stable_modes = stable_mode_names(gate86)
    if BEST_MODE not in stable_modes:
        raise RuntimeError({"best_mode": BEST_MODE, "stable_modes": stable_modes})

    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    gate86_module = load_module("gate86_for_gate87", GATE86_SCRIPT)
    gate82_module = gate86_module.load_module(
        "gate82_for_gate87",
        gate86_module.GATE82_SCRIPT,
    )
    gate77_module = gate82_module.load_module(
        "gate77_for_gate87",
        gate82_module.GATE77_SCRIPT,
    )

    start = time.perf_counter()
    rows = []
    for cutoff in gate77_module.CUTOFFS:
        rows.extend(
            gate86_module.run_cutoff(
                cutoff,
                gate77_module,
                gate82_module,
                mode=BEST_MODE,
            )
        )
    elapsed = time.perf_counter() - start
    projection = summarize_projection(rows, books)

    dependency_counts = {
        "materialized_seed_payload_digit_fields": projection["seed_digits"],
        "materialized_literal_payload_digit_fields": projection[
            "canonical_literal_digits"
        ],
        "materialized_copy_source_fields": projection["canonical_copy_items"],
        "materialized_copy_length_fields": projection["canonical_copy_items"],
        "materialized_operation_dependency_fields": projection["canonical_literal_runs"]
        + 2 * projection["canonical_copy_items"],
        "item_type_charge_removed_from_projection": True,
        "literal_length_charge_removed_from_projection": True,
    }
    active_deps = gate71["declared_dependency_counts"]
    comparison = {
        "active_declared_literal_payload_fields": active_deps[
            "declared_literal_payload_fields"
        ],
        "active_declared_copy_source_fields": active_deps["declared_copy_source_fields"],
        "active_declared_copy_length_fields": active_deps["declared_copy_length_fields"],
        "active_declared_operation_dependency_fields": active_deps[
            "declared_operation_dependency_fields"
        ],
        "projection_materialized_copy_source_field_delta": dependency_counts[
            "materialized_copy_source_fields"
        ]
        - active_deps["declared_copy_source_fields"],
        "projection_materialized_copy_length_field_delta": dependency_counts[
            "materialized_copy_length_fields"
        ]
        - active_deps["declared_copy_length_fields"],
        "projection_materialized_operation_dependency_field_delta": dependency_counts[
            "materialized_operation_dependency_fields"
        ]
        - active_deps["declared_operation_dependency_fields"],
    }
    target_text_blocker = {
        "target_text_required_for_copy_candidate_search": True,
        "target_text_required_for_literal_payload": True,
        "target_text_required_for_literal_endpoint_set": True,
        "decoder_can_choose_projection_without_target_text": False,
        "seed_books_external": projection["seed_books"],
        "single_cutoff_books_not_holdout_stability_proven": projection[
            "single_cutoff_only_books"
        ],
    }
    promotes_generator = (
        projection["multi_cutoff_stable_book_count"] == projection["multi_cutoff_book_count"]
        and not target_text_blocker["target_text_required_for_copy_candidate_search"]
        and not target_text_blocker["target_text_required_for_literal_payload"]
        and not projection["single_cutoff_only_books"]
    )
    classification = (
        "stable_path_projection_promoted_to_generator"
        if promotes_generator
        else "stable_path_projection_boundary_only"
    )

    return {
        "schema": "stable_path_projection_boundary_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate86": rel(GATE86),
            "gate86_script": rel(GATE86_SCRIPT),
            "gate71_dependency_refresh": rel(GATE71),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "projection_mode": BEST_MODE,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "stable_modes_from_gate86": stable_modes,
            "projection_mode": BEST_MODE,
            "parsed_book_count": projection["parsed_book_count"],
            "seed_book_count": projection["seed_book_count"],
            "single_cutoff_only_book_count": projection["single_cutoff_only_book_count"],
            "multi_cutoff_stable_book_count": projection["multi_cutoff_stable_book_count"],
            "multi_cutoff_book_count": projection["multi_cutoff_book_count"],
            "unstable_book_count": len(projection["unstable_books"]),
            "coverage_digit_count": projection["coverage_digit_count"],
            "total_digit_count": projection["total_digit_count"],
            "canonical_copy_items": projection["canonical_copy_items"],
            "canonical_literal_runs": projection["canonical_literal_runs"],
            "canonical_literal_digits": projection["canonical_literal_digits"],
            "canonical_copied_digits": projection["canonical_copied_digits"],
            "promotes_generator": promotes_generator,
            "interpretation": (
                "Gate 86 gives a stable encoder-side path projection under the "
                "no-item/no-literal-length control, but the projection is still "
                "chosen with the target book text available. It therefore bounds "
                "the path-stability problem without proving a decoder-side book "
                "generator."
            ),
        },
        "projection": projection,
        "dependency_counts": dependency_counts,
        "comparison_to_active_formula_dependencies": comparison,
        "target_text_blocker": target_text_blocker,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "stable_encoder_path_projection_only",
            "source_length_parser_status": "target_text_dependency_blocks_generator_promotion",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "87_stable_path_projection_boundary_audit.json"
    md_path = TEST_RESULTS / "87_stable_path_projection_boundary_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    deps = result["dependency_counts"]
    blocker = result["target_text_blocker"]
    comparison = result["comparison_to_active_formula_dependencies"]
    lines = [
        "# Stable Path Projection Boundary Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 86 closes multi-cutoff exact path stability under global",
        "item/literal-length controls. This audit asks whether that stable path",
        "can be promoted as a generator, or whether it remains an encoder-side",
        "projection that still needs target text and declared payload/source/length",
        "material.",
        "",
        "## Result",
        "",
        f"- Projection mode: `{s['projection_mode']}`.",
        f"- Multi-cutoff stable books: `{s['multi_cutoff_stable_book_count']}/{s['multi_cutoff_book_count']}`.",
        f"- Single-cutoff-only parsed books: `{s['single_cutoff_only_book_count']}`.",
        f"- Seed books still external: `{result['projection']['seed_books']}`.",
        f"- Unstable projected books: `{result['projection']['unstable_books']}`.",
        f"- Coverage digits: `{s['coverage_digit_count']}/{s['total_digit_count']}`.",
        f"- Canonical parsed copy items: `{s['canonical_copy_items']}`.",
        f"- Canonical parsed literal runs/digits: `{s['canonical_literal_runs']}` / `{s['canonical_literal_digits']}`.",
        f"- Promotes generator: `{s['promotes_generator']}`.",
        "",
        "## Dependency Boundary",
        "",
        f"- Materialized seed payload digits: `{deps['materialized_seed_payload_digit_fields']}`.",
        f"- Materialized parsed literal payload digits: `{deps['materialized_literal_payload_digit_fields']}`.",
        f"- Materialized copy source fields: `{deps['materialized_copy_source_fields']}`.",
        f"- Materialized copy length fields: `{deps['materialized_copy_length_fields']}`.",
        f"- Operation dependency-field delta vs active formula: `{comparison['projection_materialized_operation_dependency_field_delta']}`.",
        f"- Target text required for copy candidate search: `{blocker['target_text_required_for_copy_candidate_search']}`.",
        f"- Target text required for literal payload/endpoints: `{blocker['target_text_required_for_literal_payload']}` / `{blocker['target_text_required_for_literal_endpoint_set']}`.",
        f"- Decoder can choose projection without target text: `{blocker['decoder_can_choose_projection_without_target_text']}`.",
        "",
        "## Decision",
        "",
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
