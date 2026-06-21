from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

CANONICALITY = AUTHORIAL_RESULTS / "135_copy_source_canonicality_audit.json"
DEFAULT_EXCEPTION = AUTHORIAL_RESULTS / "137_copy_source_default_decodability_audit.json"
SOURCE_BREAK_EVEN = AUTHORIAL_RESULTS / "153_cross_op_source_break_even_audit.json"
SOURCE_CONTEXT = AUTHORIAL_RESULTS / "154_copy_source_structural_context_audit.json"
SOURCE_BLOCKER_GATE = TEST_RESULTS / "24_source_blocker_structural_context_gate.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened") not in (None, False):
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim") not in (None, False):
        raise RuntimeError(f"{name} introduced plaintext")


def make_result() -> dict[str, Any]:
    canonicality = load_json(CANONICALITY)
    default_exception = load_json(DEFAULT_EXCEPTION)
    break_even = load_json(SOURCE_BREAK_EVEN)
    source_context = load_json(SOURCE_CONTEXT)
    blocker_gate = load_json(SOURCE_BLOCKER_GATE)
    for name, data in [
        ("copy_source_canonicality", canonicality),
        ("copy_source_default_exception", default_exception),
        ("cross_op_source_break_even", break_even),
        ("copy_source_structural_context", source_context),
        ("source_blocker_gate", blocker_gate),
    ]:
        assert_boundary(name, data)

    summary = canonicality["summary"]
    copy_items = int(summary["copy_items"])
    earliest = int(summary["earliest_source_count"])
    unique = int(summary["unique_source_count"])
    ambiguous = copy_items - unique
    dependency_removed = bool(
        canonicality.get("boundary", {}).get("copy_source_dependency_removed", False)
    )
    default_matches = int(default_exception["model"]["default_count"])
    exceptions = int(default_exception["model"]["exception_count"])
    source_context_promoted = bool(source_context["decision"]["structural_context_promoted"])
    blocker_closed = (
        blocker_gate["classification"]
        == "simple_source_contexts_do_not_rescue_cross_op_near_tie"
    )
    earliest_rule_decoder_computable = False
    promoted = (
        earliest == copy_items
        and earliest_rule_decoder_computable
        and dependency_removed
        and exceptions == 0
    )
    classification = (
        "copy_source_canonicality_removes_decoder_dependency"
        if promoted
        else "earliest_source_canonicality_encoder_side_only"
    )

    return {
        "schema": "source_canonicality_decodability_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "copy_source_canonicality": rel(CANONICALITY),
            "copy_source_default_exception": rel(DEFAULT_EXCEPTION),
            "cross_op_source_break_even": rel(SOURCE_BREAK_EVEN),
            "copy_source_structural_context": rel(SOURCE_CONTEXT),
            "source_blocker_gate": rel(SOURCE_BLOCKER_GATE),
        },
        "summary": {
            "copy_items": copy_items,
            "earliest_source_count": earliest,
            "unique_source_count": unique,
            "ambiguous_source_count": ambiguous,
            "candidate_count_mean": summary["candidate_count_mean"],
            "candidate_count_max": summary["candidate_count_max"],
            "earliest_exact_chunk_rule_decoder_computable": earliest_rule_decoder_computable,
            "copy_source_dependency_removed_by_canonicality": dependency_removed,
            "default_exception_default_matches": default_matches,
            "default_exception_exceptions": exceptions,
            "default_exception_candidate_gain_bits": default_exception["candidate_gain_bits"],
            "source_free_oracle_delta_bits": break_even["break_even"][
                "no_source_oracle_delta_bits"
            ],
            "simple_source_context_promoted": source_context_promoted,
            "source_blocker_gate_closed": blocker_closed,
            "interpretation": (
                "The declared source is fully canonical relative to the copied "
                "chunk, but that chunk is future target information from the "
                "decoder's perspective. Earliest-source canonicality therefore "
                "audits encoder regularity; it does not remove the source ledger."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged",
            "source_canonicality_status": "complete_encoder_regularization",
            "decoder_source_dependency_status": "not_removed",
            "source_default_exception_status": "retained_decodable_representation",
            "generation_explanation_status": "source_rule_boundary_sharpened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "25_source_canonicality_decodability_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Source Canonicality Decodability Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 135 found that every declared copy source is the earliest legal",
        "occurrence of the copied chunk at the declared length. This gate checks",
        "whether that canonicality actually removes source from the decoder, or",
        "whether it only regularizes the encoder's choice after the target chunk",
        "is already known.",
        "",
        "## Summary",
        "",
        f"- Copy items: `{s['copy_items']}`.",
        f"- Earliest exact-chunk sources: `{s['earliest_source_count']}/{s['copy_items']}`.",
        f"- Unique source choices at declared length: `{s['unique_source_count']}/{s['copy_items']}`.",
        f"- Ambiguous source choices at declared length: `{s['ambiguous_source_count']}/{s['copy_items']}`.",
        f"- Candidate count mean/max: `{s['candidate_count_mean']:.3f}` / "
        f"`{s['candidate_count_max']}`.",
        f"- Earliest exact-chunk rule decoder-computable: "
        f"`{s['earliest_exact_chunk_rule_decoder_computable']}`.",
        f"- Source dependency removed by canonicality: "
        f"`{s['copy_source_dependency_removed_by_canonicality']}`.",
        f"- Decodable default/exception source model: "
        f"`{s['default_exception_default_matches']}` defaults and "
        f"`{s['default_exception_exceptions']}` exceptions.",
        f"- Default/exception gain already promoted upstream: "
        f"`{s['default_exception_candidate_gain_bits']:.3f}` bits.",
        f"- Source-free oracle delta at the cross-op near tie: "
        f"`{s['source_free_oracle_delta_bits']:+.3f}` bits.",
        f"- Simple source context promoted: `{s['simple_source_context_promoted']}`.",
        "",
        "## Interpretation",
        "",
        "Earliest-source canonicality is real, but it is not a decoder rule. The",
        "rule asks for the earliest prior occurrence of the chunk that will be",
        "copied; the decoder does not know that future chunk until the source and",
        "length have already been resolved. The current valid representation",
        "therefore remains the decodable default/exception source ledger, not a",
        "source-free earliest-occurrence rule.",
        "",
        "## Boundary",
        "",
        "- No compression bound is promoted.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "- Row0/table origin remains exogenous.",
    ]
    (TEST_RESULTS / "25_source_canonicality_decodability_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
