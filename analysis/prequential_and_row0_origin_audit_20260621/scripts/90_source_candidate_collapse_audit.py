from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE88_SCRIPT = HERE / "scripts" / "88_decoder_side_rule_coverage_audit.py"
GATE88 = TEST_RESULTS / "88_decoder_side_rule_coverage_audit.json"
GATE89 = TEST_RESULTS / "89_source_tiebreak_artifact_audit.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"


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


def source_collapse_detected(audit126) -> dict[str, Any]:
    source = inspect.getsource(audit126.match_candidates)
    return {
        "stores_one_source_per_length": "by_length: dict[int, int]" in source,
        "prefers_lower_source_on_same_length": "source_pos < current" in source,
        "returns_collapsed_length_source_pairs": "sorted(by_length.items())" in source,
        "source_excerpt": "\n".join(source.splitlines()[10:25]),
    }


def make_result() -> dict[str, Any]:
    gate88 = load_json(GATE88)
    gate89 = load_json(GATE89)
    assert_boundary("decoder_side_rule_coverage_audit", gate88)
    assert_boundary("source_tiebreak_artifact_audit", gate89)
    gate88_module = load_module("gate88_for_gate90", GATE88_SCRIPT)
    gate86_module = gate88_module.load_module(
        "gate86_for_gate90",
        gate88_module.GATE86_SCRIPT,
    )
    gate82_module = gate86_module.load_module(
        "gate82_for_gate90",
        gate86_module.GATE82_SCRIPT,
    )
    gate77_module = gate82_module.load_module(
        "gate77_for_gate90",
        gate82_module.GATE77_SCRIPT,
    )
    context = gate77_module.load_parser_context_for_cutoff(10)
    audit126 = context["audit126"]
    min_len = int(context["formula"]["policy"]["min_len"])
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}

    canonical_rows = gate88_module.stable_projection_rows(
        gate86_module,
        gate82_module,
        gate77_module,
    )
    copy_rows = gate88_module.collect_copy_rule_rows(
        canonical_rows=canonical_rows,
        books=books,
        min_len=min_len,
    )
    collapse = source_collapse_detected(audit126)
    collapse_confirmed = (
        collapse["stores_one_source_per_length"]
        and collapse["prefers_lower_source_on_same_length"]
        and collapse["returns_collapsed_length_source_pairs"]
    )
    copy_event_count = len(copy_rows)
    earliest_count = sum(1 for row in copy_rows if row["source_is_earliest_target_match"])
    unique_count = sum(1 for row in copy_rows if row["source_is_unique_target_match"])
    hidden_alternative_count = sum(
        1 for row in copy_rows if int(row["target_match_source_count"]) > 1
    )
    max_hidden_alternatives = max(
        int(row["target_match_source_count"]) - 1 for row in copy_rows
    )
    hidden_rows = [
        {
            "book": row["book"],
            "op_index": row["op_index"],
            "book_pos": row["book_pos"],
            "source": row["source"],
            "length": row["length"],
            "target_match_source_count": row["target_match_source_count"],
            "decoder_max_possible_after_declared_source": row[
                "decoder_max_possible_after_declared_source"
            ],
        }
        for row in copy_rows
        if int(row["target_match_source_count"]) > 1
    ][:25]
    gate89_superseded = (
        collapse_confirmed
        and gate89["classification"] == "source_canonicality_tiebreak_not_resolved"
    )
    classification = (
        "source_canonicality_candidate_collapse_artifact"
        if collapse_confirmed and earliest_count == copy_event_count
        else "source_candidate_collapse_unresolved"
    )

    return {
        "schema": "source_candidate_collapse_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate88": rel(GATE88),
            "gate89": rel(GATE89),
            "gate88_script": rel(GATE88_SCRIPT),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "collapse_confirmed_in_precompute_matches": collapse_confirmed,
            "copy_event_count": copy_event_count,
            "source_is_earliest_target_match_count": earliest_count,
            "source_is_unique_target_match_count": unique_count,
            "hidden_alternative_source_event_count": hidden_alternative_count,
            "max_hidden_alternatives_for_one_event": max_hidden_alternatives,
            "gate89_superseded": gate89_superseded,
            "interpretation": (
                "The parser helper exposes only the earliest source for each "
                "copy length. Therefore the 208/208 earliest-target-match result "
                "is induced by candidate generation, not independent source "
                "evidence. Gate 89 could not change sources because alternate "
                "same-length sources were never exposed to the heap."
            ),
        },
        "precompute_match_source_collapse": collapse,
        "hidden_alternative_examples": hidden_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "source_canonicality_demoted_to_candidate_generation_artifact",
            "source_rule_status": "earliest_target_match_not_independent_evidence",
            "gate89_status": "superseded_by_candidate_collapse_audit"
            if gate89_superseded
            else "not_superseded",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "90_source_candidate_collapse_audit.json"
    md_path = TEST_RESULTS / "90_source_candidate_collapse_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Source Candidate Collapse Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 89 tested source tie policies, but `precompute_matches` may already",
        "collapse candidate sources before the parser sees them. This audit checks",
        "the helper implementation and recounts hidden same-length alternatives.",
        "",
        "## Findings",
        "",
        f"- Candidate collapse confirmed in `precompute_matches`: `{s['collapse_confirmed_in_precompute_matches']}`.",
        f"- Projection copy events: `{s['copy_event_count']}`.",
        f"- Earliest-target-match count: `{s['source_is_earliest_target_match_count']}/{s['copy_event_count']}`.",
        f"- Unique-target-match count: `{s['source_is_unique_target_match_count']}/{s['copy_event_count']}`.",
        f"- Events with hidden alternate sources: `{s['hidden_alternative_source_event_count']}/{s['copy_event_count']}`.",
        f"- Max hidden alternates for one event: `{s['max_hidden_alternatives_for_one_event']}`.",
        f"- Gate 89 superseded: `{s['gate89_superseded']}`.",
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
