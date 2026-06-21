from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

CANONICALITY = AUTHORIAL_RESULTS / "135_copy_source_canonicality_audit.json"
CANONICALITY_CONTROLS = AUTHORIAL_RESULTS / "140_online_copy_source_canonicality_audit.json"
DISTANCE_MODEL = AUTHORIAL_RESULTS / "144_copy_source_distance_model_audit.json"
CANONICALITY_GATE = TEST_RESULTS / "25_source_canonicality_decodability_gate.json"
STATE_GATE = TEST_RESULTS / "26_source_state_dependency_gate.json"


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
    boundary = data.get("boundary", {})
    if boundary.get("semantic_delta", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced semantic delta")
    if boundary.get("row0_origin_changed", False) is not False:
        raise RuntimeError(f"{name} changed row0 origin")
    if boundary.get("compression_bound_changed", False) is not False:
        raise RuntimeError(f"{name} changed compression bound")
    if boundary.get("authorial_intent_claim", False) is not False:
        raise RuntimeError(f"{name} introduced authorial intent claim")


def prefix_distance_gaps(distance: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in distance["prefix_future_suffix"]["rows"]:
        absolute = row["models"]["absolute_source"]["default_exception"]
        backward = row["models"]["backward_distance"]["default_exception"]
        rows.append(
            {
                "label": row["label"],
                "frozen_backward_minus_absolute_bits": (
                    float(backward["test_frozen_bits"])
                    - float(absolute["test_frozen_bits"])
                ),
                "online_backward_minus_absolute_bits": (
                    float(backward["test_online_bits"])
                    - float(absolute["test_online_bits"])
                ),
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    canonicality = load_json(CANONICALITY)
    controls = load_json(CANONICALITY_CONTROLS)
    distance = load_json(DISTANCE_MODEL)
    canonicality_gate = load_json(CANONICALITY_GATE)
    state_gate = load_json(STATE_GATE)

    for name, data in [
        ("copy_source_canonicality", canonicality),
        ("copy_source_canonicality_controls", controls),
        ("copy_source_distance_model", distance),
        ("source_canonicality_decodability_gate", canonicality_gate),
        ("source_state_dependency_gate", state_gate),
    ]:
        assert_boundary(name, data)

    canonical_summary = canonicality["summary"]
    control_summary = controls["summary"]
    negative_controls = controls["negative_controls"]
    distance_decision = distance["decision"]
    state_summary = state_gate["summary"]
    canonicality_summary = canonicality_gate["summary"]
    prefix_gaps = prefix_distance_gaps(distance)
    distance_frozen_loss_count = sum(
        1 for row in prefix_gaps if row["frozen_backward_minus_absolute_bits"] > 0
    )
    distance_online_loss_count = sum(
        1 for row in prefix_gaps if row["online_backward_minus_absolute_bits"] > 0
    )

    copy_items = int(canonical_summary["copy_items"])
    earliest_hits = int(control_summary["earliest_source_hits"])
    latest_hits = int(control_summary["latest_source_hits"])
    previous_hits = int(control_summary["previous_source_hits"])
    previous_plus_length_hits = int(control_summary["previous_source_plus_length_hits"])
    unique_ops = int(control_summary["unique_source_candidate_ops"])
    ambiguous_ops = int(control_summary["ambiguous_source_candidate_ops"])
    canonicality_confirmed = (
        earliest_hits == copy_items
        and int(canonical_summary["earliest_source_count"]) == copy_items
        and int(negative_controls["latest_occurrence_hits"]) == latest_hits
    )
    decoder_dependency_retained = (
        canonicality_gate["decision"]["decoder_source_dependency_status"]
        == "not_removed"
        and state_gate["decision"]["source_state_status"]
        == "path_dependent_previous_copy_state_retained"
        and not bool(canonicality_summary["copy_source_dependency_removed_by_canonicality"])
        and not bool(canonicality_summary["earliest_exact_chunk_rule_decoder_computable"])
    )
    distance_rejected = (
        bool(distance_decision["active_copy_source_model_retained"])
        and not bool(distance_decision["backward_distance_promoted"])
        and float(distance_decision["distance_replacement_total_worse_than_active_bits"])
        > 0
        and distance_frozen_loss_count == len(prefix_gaps)
        and distance_online_loss_count == len(prefix_gaps)
    )
    classification = (
        "source_selection_encoder_canonical_decoder_dependency_retained"
        if canonicality_confirmed and decoder_dependency_retained and distance_rejected
        else "source_selection_derivation_boundary_unresolved"
    )

    return {
        "schema": "source_selection_derivation_boundary_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "copy_source_canonicality": rel(CANONICALITY),
            "copy_source_canonicality_controls": rel(CANONICALITY_CONTROLS),
            "copy_source_distance_model": rel(DISTANCE_MODEL),
            "source_canonicality_decodability_gate": rel(CANONICALITY_GATE),
            "source_state_dependency_gate": rel(STATE_GATE),
        },
        "summary": {
            "copy_items": copy_items,
            "earliest_source_hits": earliest_hits,
            "latest_source_hits": latest_hits,
            "previous_source_hits": previous_hits,
            "previous_source_plus_length_hits": previous_plus_length_hits,
            "unique_source_candidate_ops": unique_ops,
            "ambiguous_source_candidate_ops": ambiguous_ops,
            "candidate_source_count_mean": control_summary["candidate_source_count"][
                "mean"
            ],
            "candidate_source_count_max": control_summary["candidate_source_count"][
                "max"
            ],
            "random_candidate_expected_hits": negative_controls[
                "random_candidate_expected_hits"
            ],
            "probability_all_earliest_if_uniform_candidate_choice": negative_controls[
                "probability_all_earliest_if_uniform_candidate_choice"
            ],
            "log2_probability_all_earliest_if_uniform_candidate_choice": negative_controls[
                "log2_probability_all_earliest_if_uniform_candidate_choice"
            ],
            "distance_replacement_total_worse_than_active_bits": distance_decision[
                "distance_replacement_total_worse_than_active_bits"
            ],
            "distance_stream_worse_than_active_bits": distance_decision[
                "distance_stream_worse_than_active_default_exception_bits"
            ],
            "distance_prefix_frozen_loss_count": distance_frozen_loss_count,
            "distance_prefix_online_loss_count": distance_online_loss_count,
            "prefix_split_count": len(prefix_gaps),
            "prefix_distance_gaps": prefix_gaps,
            "earliest_exact_chunk_rule_decoder_computable": canonicality_summary[
                "earliest_exact_chunk_rule_decoder_computable"
            ],
            "copy_source_dependency_removed_by_canonicality": canonicality_summary[
                "copy_source_dependency_removed_by_canonicality"
            ],
            "active_reparse_state_key_required": state_summary[
                "active_reparse_state_key_required"
            ],
            "best_state_free_default": state_summary["best_state_free_default"],
            "best_state_free_total_penalty_bits": state_summary[
                "best_state_free_total_penalty_bits"
            ],
            "state_free_prefix_loss_count": state_summary["prefix_frozen_loss_count"],
            "state_free_prefix_split_count": state_summary["prefix_frozen_split_count"],
            "canonicality_confirmed": canonicality_confirmed,
            "decoder_dependency_retained": decoder_dependency_retained,
            "distance_rejected": distance_rejected,
            "interpretation": (
                "Copy source selection is highly regular on the encoder side: "
                "every declared source is the earliest legal exact-chunk source. "
                "The rule still depends on future target text and does not remove "
                "the decoder source ledger; backward-distance and state-free "
                "replacements also fail."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged",
            "source_selection_status": "encoder_canonicality_confirmed",
            "decoder_source_dependency_status": "retained",
            "distance_source_model_status": "rejected",
            "state_free_source_model_status": "rejected",
            "generation_explanation_status": "source_origin_boundary_sharpened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "31_source_selection_derivation_boundary_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Source Selection Derivation Boundary Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Copy source is one of the remaining declared recipe dependencies. This",
        "gate consolidates source canonicality, negative controls, the distance",
        "model, and the source-state gates to decide whether source selection has",
        "become a decoder-computable derivation or remains a declared ledger.",
        "",
        "## Summary",
        "",
        f"- Copy items: `{s['copy_items']}`.",
        f"- Earliest-source hits: `{s['earliest_source_hits']}/{s['copy_items']}`.",
        f"- Latest-source hits: `{s['latest_source_hits']}/{s['copy_items']}`.",
        f"- Previous-source hits: `{s['previous_source_hits']}/{s['copy_items']}`.",
        f"- Previous-source-plus-length hits: `{s['previous_source_plus_length_hits']}/{s['copy_items']}`.",
        f"- Unique / ambiguous source-candidate ops: `{s['unique_source_candidate_ops']}` / `{s['ambiguous_source_candidate_ops']}`.",
        f"- Random candidate expected hits: `{s['random_candidate_expected_hits']:.3f}`.",
        f"- Probability all sources are earliest under uniform candidate choice: `{s['probability_all_earliest_if_uniform_candidate_choice']:.3e}`.",
        f"- Backward-distance replacement penalty: `{s['distance_replacement_total_worse_than_active_bits']:.3f}` bits.",
        f"- Backward-distance prefix losses: frozen `{s['distance_prefix_frozen_loss_count']}/{s['prefix_split_count']}`, online `{s['distance_prefix_online_loss_count']}/{s['prefix_split_count']}`.",
        f"- Earliest exact-chunk rule decoder-computable: `{s['earliest_exact_chunk_rule_decoder_computable']}`.",
        f"- Source dependency removed by canonicality: `{s['copy_source_dependency_removed_by_canonicality']}`.",
        f"- Required active source state: `{s['active_reparse_state_key_required']}`.",
        f"- Best state-free default: `{s['best_state_free_default']}` (`+{s['best_state_free_total_penalty_bits']:.3f}` bits).",
        "",
        "## Interpretation",
        "",
        "The source choice has a strong encoder-side rule: it is always the",
        "earliest legal source for the copied target chunk. That is not enough to",
        "derive the source during decoding, because the copied target chunk is not",
        "known until source and length are resolved. Controls also reject simple",
        "alternatives: latest/previous source rules do not match, backward",
        "distance is worse on full corpus and all prefix splits, and state-free",
        "defaults lose to the active previous-source-plus-length model.",
        "",
        "## Boundary",
        "",
        "- Source selection is canonical but still declared.",
        "- No compression bound is promoted.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "31_source_selection_derivation_boundary_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
