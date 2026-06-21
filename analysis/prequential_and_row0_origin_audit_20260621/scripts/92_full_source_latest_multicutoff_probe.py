from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE91_SCRIPT = HERE / "scripts" / "91_full_source_exposure_audit.py"
GATE91 = TEST_RESULTS / "91_full_source_exposure_audit.json"

POLICY = "latest_source"
TEST_CUTOFFS = [50, 60]


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


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_book: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_book.setdefault(int(row["book"]), []).append(row)
    book_rows = []
    for book in sorted(by_book):
        book_rows_for_book = sorted(by_book[book], key=lambda row: int(row["cutoff"]))
        signatures = sorted({row["signature"] for row in book_rows_for_book})
        book_rows.append(
            {
                "book": book,
                "cutoffs": [int(row["cutoff"]) for row in book_rows_for_book],
                "cutoff_count": len(book_rows_for_book),
                "signature_count": len(signatures),
                "stable_exact_path": len(signatures) == 1,
                "non_earliest_source_count": sum(
                    int(row["non_earliest_source_count"]) for row in book_rows_for_book
                ),
            }
        )
    multi = [row for row in book_rows if row["cutoff_count"] >= 2]
    unstable = [row for row in multi if not row["stable_exact_path"]]
    return {
        "target_book_evaluations": len(rows),
        "roundtrip_book_evaluations": sum(1 for row in rows if row["roundtrip_ok"]),
        "raw_positive_book_evaluations": sum(
            1 for row in rows if row["parser_bits"] < row["raw_digit_uniform_bits"]
        ),
        "book_count": len(book_rows),
        "multi_cutoff_book_count": len(multi),
        "multi_cutoff_stable_book_count": len(multi) - len(unstable),
        "multi_cutoff_unstable_book_count": len(unstable),
        "unstable_books": [row["book"] for row in unstable],
        "total_primary_parser_bits": sum(float(row["parser_bits"]) for row in rows),
        "total_non_earliest_source_count": sum(
            int(row["non_earliest_source_count"]) for row in rows
        ),
        "total_copy_items": sum(int(row["copy_items"]) for row in rows),
        "total_literal_digits": sum(int(row["literal_digits"]) for row in rows),
        "hidden_candidate_count": sum(
            int(row["candidate_stats"]["hidden_candidate_count"]) for row in rows
        ),
        "positions_with_hidden_sources": sum(
            int(row["candidate_stats"]["positions_with_hidden_sources"]) for row in rows
        ),
        "max_candidates_at_position": max(
            int(row["candidate_stats"]["max_candidates_at_position"]) for row in rows
        ),
        "book_rows": book_rows,
    }


def make_result() -> dict[str, Any]:
    gate91 = load_json(GATE91)
    assert_boundary("full_source_exposure_audit", gate91)
    helper = load_module("gate91_for_gate92", GATE91_SCRIPT)
    gate86 = helper.load_module("gate86_for_gate92", helper.GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_gate92", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate92", gate82.GATE77_SCRIPT)

    start = time.perf_counter()
    rows = []
    for cutoff in TEST_CUTOFFS:
        rows.extend(helper.run_cutoff(cutoff, gate77, gate82, policy=POLICY))
    elapsed = time.perf_counter() - start
    summary = summarize_rows(rows)
    all_roundtrip = summary["roundtrip_book_evaluations"] == summary["target_book_evaluations"]
    all_raw_positive = (
        summary["raw_positive_book_evaluations"] == summary["target_book_evaluations"]
    )
    all_multi_stable = (
        summary["multi_cutoff_stable_book_count"] == summary["multi_cutoff_book_count"]
    )
    classification = (
        "full_source_latest_multicutoff_stable"
        if all_roundtrip and all_raw_positive and all_multi_stable
        else "full_source_latest_multicutoff_mixed"
    )
    return {
        "schema": "full_source_latest_multicutoff_probe.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate91_full_source_exposure": rel(GATE91),
            "gate91_script": rel(GATE91_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "policy": POLICY,
            "tested_cutoffs": TEST_CUTOFFS,
            "all_same_length_sources_exposed": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            **summary,
            "elapsed_seconds": elapsed,
            "all_roundtrip": all_roundtrip,
            "all_raw_positive": all_raw_positive,
            "all_multi_cutoff_books_stable": all_multi_stable,
            "interpretation": (
                "The most disruptive full-source tie policy from gate 91 is "
                "tested over cutoffs 50 and 60, giving books 60-69 two "
                "observations for exact-path stability under exposed sources."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "full_source_latest_multicutoff_probe_only",
            "source_rule_status": classification,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "92_full_source_latest_multicutoff_probe.json"
    md_path = TEST_RESULTS / "92_full_source_latest_multicutoff_probe.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Full Source Latest Multi-Cutoff Probe",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 91 exposed every same-length source only on cutoff 60. This probe",
        "runs the most disruptive tie policy, `latest_source`, on cutoffs 50 and",
        "60 so books 60-69 receive two exact-path observations.",
        "",
        "## Result",
        "",
        f"- Tested cutoffs: `{result['scope']['tested_cutoffs']}`.",
        f"- Book evaluations: `{s['target_book_evaluations']}`.",
        f"- Roundtrip evaluations: `{s['roundtrip_book_evaluations']}/{s['target_book_evaluations']}`.",
        f"- Raw-positive evaluations: `{s['raw_positive_book_evaluations']}/{s['target_book_evaluations']}`.",
        f"- Multi-cutoff stable books: `{s['multi_cutoff_stable_book_count']}/{s['multi_cutoff_book_count']}`.",
        f"- Unstable multi-cutoff books: `{s['unstable_books']}`.",
        f"- Non-earliest source selections: `{s['total_non_earliest_source_count']}`.",
        f"- Hidden candidates exposed: `{s['hidden_candidate_count']}`.",
        f"- Total primary parser bits: `{s['total_primary_parser_bits']:.6f}`.",
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
