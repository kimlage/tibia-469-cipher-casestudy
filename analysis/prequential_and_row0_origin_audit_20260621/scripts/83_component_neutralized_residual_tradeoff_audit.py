from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE82_SCRIPT = HERE / "scripts" / "82_component_neutralized_path_stability_gate.py"
GATE82 = TEST_RESULTS / "82_component_neutralized_path_stability_gate.json"

ACTIVE_MODE = "active_learned"
BEST_MODE = "uniform_copy_length_and_source_exception"
FULL_SOURCE_MODE = "uniform_copy_length_and_full_source"


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


def mode_summary(gate82: dict[str, Any], mode: str) -> dict[str, Any]:
    return next(row for row in gate82["summary"]["mode_summaries"] if row["cost_mode"] == mode)


def unstable_set(summary: dict[str, Any]) -> set[int]:
    return {int(row["book"]) for row in summary["unstable_books"]}


def op_profile(ops: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type_sequence": "".join("C" if op["type"] == "copy" else "L" for op in ops),
        "length_sequence": [int(op["length"]) for op in ops],
        "copy_sources": [int(op["source"]) for op in ops if op["type"] == "copy"],
        "literal_digits": sum(int(op["length"]) for op in ops if op["type"] == "literal"),
        "copied_digits": sum(int(op["length"]) for op in ops if op["type"] == "copy"),
    }


def rerun_modes_for_books(
    gate82_module,
    modes: list[str],
    books_of_interest: set[int],
) -> dict[str, dict[int, list[dict[str, Any]]]]:
    gate77_module = gate82_module.load_module(
        "gate77_multi_cutoff_validation_for_gate83",
        gate82_module.GATE77_SCRIPT,
    )
    result: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for mode in modes:
        rows_by_book: dict[int, list[dict[str, Any]]] = {book: [] for book in books_of_interest}
        for cutoff in gate77_module.CUTOFFS:
            for row in gate82_module.run_cutoff(cutoff, gate77_module, cost_mode=mode):
                book = int(row["book"])
                if book in books_of_interest:
                    rows_by_book[book].append(row)
        result[mode] = rows_by_book
    return result


def summarize_book_mode(rows: list[dict[str, Any]]) -> dict[str, Any]:
    signatures: dict[str, dict[str, Any]] = {}
    for row in rows:
        signature = row["signature"]
        signatures.setdefault(
            signature,
            {
                "signature": signature,
                "cutoffs": [],
                "parser_bits_by_cutoff": {},
                "op_profile": op_profile(row["signature_ops"]),
            },
        )
        signatures[signature]["cutoffs"].append(int(row["cutoff"]))
        signatures[signature]["parser_bits_by_cutoff"][str(row["cutoff"])] = float(
            row["parser_bits"]
        )
    variants = sorted(
        signatures.values(),
        key=lambda item: (-len(item["cutoffs"]), item["cutoffs"][0], item["signature"]),
    )
    return {
        "cutoffs": sorted(int(row["cutoff"]) for row in rows),
        "signature_count": len(variants),
        "stable_exact_path": len(variants) == 1,
        "variants": variants,
    }


def make_result() -> dict[str, Any]:
    gate82 = load_json(GATE82)
    assert_boundary("component_neutralized_path_stability", gate82)
    if gate82["summary"]["best_stability_mode"] != BEST_MODE:
        raise RuntimeError(gate82["summary"]["best_stability_mode"])

    active = mode_summary(gate82, ACTIVE_MODE)
    best = mode_summary(gate82, BEST_MODE)
    full_source = mode_summary(gate82, FULL_SOURCE_MODE)
    active_unstable = unstable_set(active)
    best_unstable = unstable_set(best)
    full_source_unstable = unstable_set(full_source)
    resolved_by_best = sorted(active_unstable - best_unstable)
    persistent_in_best = sorted(active_unstable & best_unstable)
    introduced_by_best = sorted(best_unstable - active_unstable)
    full_source_replaced_residuals = sorted(best_unstable ^ full_source_unstable)
    books_of_interest = set(resolved_by_best) | set(persistent_in_best) | set(introduced_by_best) | full_source_unstable

    gate82_module = load_module("gate82_component_neutralized", GATE82_SCRIPT)
    detailed_rows = rerun_modes_for_books(
        gate82_module,
        [ACTIVE_MODE, BEST_MODE, FULL_SOURCE_MODE],
        books_of_interest,
    )
    book_rows = []
    for book in sorted(books_of_interest):
        status = (
            "resolved_by_best"
            if book in resolved_by_best
            else (
                "persistent_in_best"
                if book in persistent_in_best
                else (
                    "introduced_by_best"
                    if book in introduced_by_best
                    else "full_source_only_residual"
                )
            )
        )
        book_rows.append(
            {
                "book": book,
                "status": status,
                "active": summarize_book_mode(detailed_rows[ACTIVE_MODE][book]),
                "best": summarize_book_mode(detailed_rows[BEST_MODE][book]),
                "full_source": summarize_book_mode(detailed_rows[FULL_SOURCE_MODE][book]),
            }
        )

    classification = "component_neutralization_tradeoff_localized"
    return {
        "schema": "component_neutralized_residual_tradeoff_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate82_component_neutralized_path_stability": rel(GATE82),
            "gate82_replay_script": rel(GATE82_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "mode_compared_to_active": BEST_MODE,
            "full_source_control_mode": FULL_SOURCE_MODE,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "active_unstable_books": sorted(active_unstable),
            "best_unstable_books": sorted(best_unstable),
            "full_source_unstable_books": sorted(full_source_unstable),
            "resolved_by_best_count": len(resolved_by_best),
            "resolved_by_best_books": resolved_by_best,
            "persistent_in_best_books": persistent_in_best,
            "introduced_by_best_books": introduced_by_best,
            "full_source_replaced_residual_books": full_source_replaced_residuals,
            "best_stable_delta_vs_active": best["stable_book_delta_vs_active"],
            "best_parser_bits_delta_vs_active": best["total_parser_bits_delta_vs_active"],
            "full_source_parser_bits_delta_vs_active": full_source["total_parser_bits_delta_vs_active"],
            "full_source_extra_cost_vs_best": (
                full_source["total_parser_bits_delta_vs_active"]
                - best["total_parser_bits_delta_vs_active"]
            ),
            "book_rows": book_rows,
            "interpretation": (
                "Uniform copy-length/source-exception scoring resolves most "
                "active learned-path instabilities, but the gain is not a full "
                "mechanism closure: book 34 remains unstable and book 26 becomes "
                "newly unstable. Full source uniformization changes the residual "
                "pair but costs far more, so the source flag is not promoted as "
                "the next simplification."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "component_neutralized_tradeoff_not_final",
            "generation_explanation_status": "simplification_candidate_with_two_residual_books",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "83_component_neutralized_residual_tradeoff_audit.json"
    md_path = TEST_RESULTS / "83_component_neutralized_residual_tradeoff_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Component-Neutralized Residual Tradeoff Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 82 improved exact multi-cutoff path stability from `38/50` to",
        "`48/50`. This audit identifies which books were resolved, which remain",
        "unstable, and which instability was introduced by the structural",
        "simplification.",
        "",
        "## Summary",
        "",
        f"- Active unstable books: `{s['active_unstable_books']}`.",
        f"- Best-mode unstable books: `{s['best_unstable_books']}`.",
        f"- Resolved by best mode: `{s['resolved_by_best_count']}` books.",
        f"- Persistent in best mode: `{s['persistent_in_best_books']}`.",
        f"- Introduced by best mode: `{s['introduced_by_best_books']}`.",
        f"- Best-mode parser-bit delta vs active: `{s['best_parser_bits_delta_vs_active']:.6f}`.",
        f"- Full-source extra cost vs best: `{s['full_source_extra_cost_vs_best']:.6f}`.",
        "",
        "## Affected Books",
        "",
        "| Book | Status | Active signatures | Best signatures | Full-source signatures |",
        "|---:|---|---:|---:|---:|",
    ]
    for row in s["book_rows"]:
        lines.append(
            "| {book} | `{status}` | {active} | {best} | {full_source} |".format(
                book=row["book"],
                status=row["status"],
                active=row["active"]["signature_count"],
                best=row["best"]["signature_count"],
                full_source=row["full_source"]["signature_count"],
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
