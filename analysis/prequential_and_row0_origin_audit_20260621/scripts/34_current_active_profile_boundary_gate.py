from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

COPY_LENGTH_DEFAULT = AUTHORIAL_RESULTS / "136_copy_length_default_decodability_audit.json"
COPY_SOURCE_DEFAULT = AUTHORIAL_RESULTS / "137_copy_source_default_decodability_audit.json"
DEFAULT_EXCEPTION_VALIDATION = AUTHORIAL_RESULTS / "141_default_exception_prequential_validation.json"
DEFAULT_EXCEPTION_PROFILE = AUTHORIAL_RESULTS / "142_default_exception_component_profile.json"
CURRENT_ACTIVE_PROFILE = AUTHORIAL_RESULTS / "145_current_active_prequential_profile_audit.json"
ACTIVE_REPARSE_STATE = AUTHORIAL_RESULTS / "146_active_reparse_state_boundary_audit.json"
STATE_FREE_DEFAULT = AUTHORIAL_RESULTS / "147_copy_source_state_free_default_audit.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any], *, allow_bound_change: bool = False) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    boundary = data.get("boundary", {})
    decision = data.get("decision", {})
    if boundary.get("semantic_delta", decision.get("semantic_delta", "NONE")) != "NONE":
        raise RuntimeError(f"{name} introduced semantic delta")
    if (
        boundary.get("row0_origin_changed", decision.get("row0_origin_changed", False))
        is not False
    ):
        raise RuntimeError(f"{name} changed row0 origin")
    compression_changed = boundary.get(
        "compression_bound_changed",
        decision.get("compression_bound_changed", False),
    )
    if compression_changed is not False and not allow_bound_change:
        raise RuntimeError(f"{name} changed compression bound")
    if boundary.get("authorial_intent_claim", False) is not False:
        raise RuntimeError(f"{name} introduced authorial intent claim")


def split_gain_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    online = [float(row["aggregate"]["online_gain_vs_uniform_bits"]) for row in rows]
    frozen = [float(row["aggregate"]["frozen_gain_vs_uniform_bits"]) for row in rows]
    return {
        "split_count": len(rows),
        "online_min_gain_bits": min(online),
        "online_mean_gain_bits": sum(online) / len(online),
        "online_nonpositive_count": sum(value <= 0 for value in online),
        "frozen_min_gain_bits": min(frozen),
        "frozen_mean_gain_bits": sum(frozen) / len(frozen),
        "frozen_nonpositive_count": sum(value <= 0 for value in frozen),
    }


def make_result() -> dict[str, Any]:
    copy_length = load_json(COPY_LENGTH_DEFAULT)
    copy_source = load_json(COPY_SOURCE_DEFAULT)
    validation = load_json(DEFAULT_EXCEPTION_VALIDATION)
    profile = load_json(DEFAULT_EXCEPTION_PROFILE)
    active = load_json(CURRENT_ACTIVE_PROFILE)
    state = load_json(ACTIVE_REPARSE_STATE)
    state_free = load_json(STATE_FREE_DEFAULT)

    for name, data, allow in [
        ("copy_length_default_decodability", copy_length, True),
        ("copy_source_default_decodability", copy_source, True),
        ("default_exception_prequential_validation", validation, False),
        ("default_exception_component_profile", profile, False),
        ("current_active_prequential_profile", active, False),
        ("active_reparse_state_boundary", state, False),
        ("copy_source_state_free_default", state_free, False),
    ]:
        assert_boundary(name, data, allow_bound_change=allow)

    active_prefix = split_gain_summary(active["prefix_future_suffix"]["rows"])
    active_blocks = split_gain_summary(active["contiguous_block_holdouts"]["rows"])
    active_families = split_gain_summary(active["public_bookcase_family_holdouts"]["rows"])
    validation_families = split_gain_summary(validation["public_bookcase_family_holdouts"]["rows"])

    active_bound = float(active["scope"]["active_compression_bound_bits"])
    active_validated = (
        active["classification"]
        == "current_active_components_predictive_under_tested_holdouts_recipe_fixed"
        and active_prefix["frozen_nonpositive_count"] == 0
        and active_blocks["frozen_nonpositive_count"] == 0
        and active_families["frozen_nonpositive_count"] == 0
        and active["decision"]["recipe_discovery_proved"] is False
    )
    default_exception_bound_promoted = (
        copy_length["classification"]
        == "controlled_copy_length_default_exception_formula_improvement"
        and copy_source["classification"]
        == "controlled_copy_source_default_exception_formula_improvement"
        and profile["decision"]["compression_bound_bits"] == active_bound
    )
    state_blocker_retained = (
        state["classification"] == "active_reparse_requires_path_dependent_copy_source_state"
        and state["decision"]["recipe_externality_removed"] is False
        and state_free["classification"]
        == "state_free_copy_source_defaults_rejected_active_path_state_retained"
        and state_free["decision"]["state_free_default_promoted"] is False
    )
    classification = (
        "active_8177_profile_validated_recipe_discovery_blocked"
        if active_validated and default_exception_bound_promoted and state_blocker_retained
        else "active_profile_boundary_unresolved"
    )

    return {
        "schema": "current_active_profile_boundary_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "copy_length_default_decodability": rel(COPY_LENGTH_DEFAULT),
            "copy_source_default_decodability": rel(COPY_SOURCE_DEFAULT),
            "default_exception_prequential_validation": rel(DEFAULT_EXCEPTION_VALIDATION),
            "default_exception_component_profile": rel(DEFAULT_EXCEPTION_PROFILE),
            "current_active_prequential_profile": rel(CURRENT_ACTIVE_PROFILE),
            "active_reparse_state_boundary": rel(ACTIVE_REPARSE_STATE),
            "copy_source_state_free_default": rel(STATE_FREE_DEFAULT),
        },
        "summary": {
            "active_compression_bound_bits": active_bound,
            "copy_length_default_exception_bits": copy_length["candidate_total_bits"],
            "copy_length_gain_bits": copy_length["candidate_gain_bits"],
            "copy_source_default_exception_bits": copy_source["candidate_total_bits"],
            "copy_source_gain_bits": copy_source["candidate_gain_bits"],
            "learned_component_stream_bits": active["full_corpus_accounting"][
                "learned_component_stream_bits"
            ],
            "learned_component_stream_share_pct": active["full_corpus_accounting"][
                "learned_component_stream_share_pct"
            ],
            "fixed_recipe_or_declaration_bits": active["full_corpus_accounting"][
                "fixed_recipe_or_declaration_bits"
            ],
            "fixed_recipe_or_declaration_share_pct": active["full_corpus_accounting"][
                "fixed_recipe_or_declaration_share_pct"
            ],
            "component_stream_bits": active["full_corpus_accounting"][
                "component_stream_bits"
            ],
            "event_counts": active["full_corpus_accounting"]["event_counts"],
            "default_exception_validation_family_nonpositive_frozen_count": (
                validation_families["frozen_nonpositive_count"]
            ),
            "default_exception_validation_family_nonpositive_online_count": (
                validation_families["online_nonpositive_count"]
            ),
            "active_prefix_gain_summary": active_prefix,
            "active_block_gain_summary": active_blocks,
            "active_family_gain_summary": active_families,
            "random_train_control_cutoffs": [
                {
                    "cutoff": row["cutoff"],
                    "observed_numeric_prefix_online_gain_bits": row[
                        "observed_numeric_prefix_online_gain_bits"
                    ],
                    "random_median_online_gain_bits": row[
                        "random_online_gain_summary_bits"
                    ]["median"],
                    "p_random_ge_observed": row["p_random_ge_observed"],
                }
                for row in active["random_same_size_train_controls"]
            ],
            "recipe_discovery_proved": active["decision"]["recipe_discovery_proved"],
            "active_reparse_state_key_required": state["scope"][
                "active_reparse_state_key_required"
            ],
            "old_reparse_state_key": state["scope"]["old_reparse_state_key"],
            "exact_active_reparse_implemented": state["summary"][
                "exact_active_reparse_implemented"
            ],
            "cutoff10_state_proxy": state["prefix_rows"][0]["candidate_graph_summary"][
                "active_path_dependent_state_proxy"
            ],
            "cutoff10_old_reparse_state_count": state["prefix_rows"][0][
                "candidate_graph_summary"
            ]["old_reparse_state_count"],
            "max_book_state_proxy_multiplier": state["summary"][
                "max_book_state_proxy_multiplier"
            ],
            "best_state_free_default": state_free["decision"]["best_state_free_name"],
            "best_state_free_worse_than_active_total_bits": state_free["decision"][
                "best_state_free_worse_than_active_total_bits"
            ],
            "default_exception_bound_promoted": default_exception_bound_promoted,
            "active_validated": active_validated,
            "state_blocker_retained": state_blocker_retained,
        },
        "decision": {
            "compression_bound_status": "8177.317_bits_active_bound_retained",
            "generation_explanation_status": (
                "active_learned_components_predictive_under_tested_holdouts"
            ),
            "recipe_discovery_status": "not_proved_path_dependent_state_boundary_retained",
            "numeric_order_status": "not_unique_against_random_same_size_train_controls",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "34_current_active_profile_boundary_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Current Active Profile Boundary Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This gate consolidates the default/exception layer into the current",
        "mechanical ledger. It distinguishes the active compression bound and",
        "component-level holdout validation from the still-open recipe-discovery",
        "problem caused by path-dependent copy-source state.",
        "",
        "## Summary",
        "",
        f"- Active compression bound: `{s['active_compression_bound_bits']:.3f}` bits.",
        f"- Copy-length default/exception formula: `{s['copy_length_default_exception_bits']:.3f}` bits, gain `{s['copy_length_gain_bits']:.3f}`.",
        f"- Copy-source default/exception formula: `{s['copy_source_default_exception_bits']:.3f}` bits, gain `{s['copy_source_gain_bits']:.3f}`.",
        f"- Learned component streams: `{s['learned_component_stream_bits']:.3f}` bits (`{s['learned_component_stream_share_pct']:.3f}%`).",
        f"- Fixed recipe/declaration remainder: `{s['fixed_recipe_or_declaration_bits']:.3f}` bits (`{s['fixed_recipe_or_declaration_share_pct']:.3f}%`).",
        f"- Active prefix frozen min gain: `{s['active_prefix_gain_summary']['frozen_min_gain_bits']:.3f}` bits.",
        f"- Active block frozen min gain: `{s['active_block_gain_summary']['frozen_min_gain_bits']:.3f}` bits.",
        f"- Active family frozen min gain: `{s['active_family_gain_summary']['frozen_min_gain_bits']:.3f}` bits.",
        f"- Active family frozen nonpositive failures: `{s['active_family_gain_summary']['frozen_nonpositive_count']}`.",
        f"- Default/exception-only family frozen nonpositive failures before full active profile: `{s['default_exception_validation_family_nonpositive_frozen_count']}`.",
        f"- Recipe discovery proved: `{s['recipe_discovery_proved']}`.",
        f"- Required active reparse state: `{s['active_reparse_state_key_required']}`.",
        f"- Old reparse state: `{s['old_reparse_state_key']}`.",
        f"- Cutoff-10 state proxy: `{s['cutoff10_state_proxy']}` versus old state count `{s['cutoff10_old_reparse_state_count']}`.",
        f"- Best state-free source default: `{s['best_state_free_default']}`, `{s['best_state_free_worse_than_active_total_bits']:.3f}` bits worse.",
        "",
        "## Interpretation",
        "",
        "`8177.317` bits is retained as the current active mechanical",
        "compression bound. Unlike the default/exception-only validation, the",
        "full active learned stream profile has positive frozen gain in every",
        "tested prefix, block, and public-bookcase family holdout. That",
        "strengthens component-level predictive validation, but it still does",
        "not prove recipe discovery: the active recipe rows are extracted before",
        "splitting, and exact active reparsing requires previous-copy source and",
        "length state. The best state-free replacement is worse, so this boundary",
        "remains a real blocker rather than a solved generator.",
        "",
        "## Boundary",
        "",
        "- No new compression bound is introduced by this gate.",
        "- The current active bound is consolidated as `8177.317` bits.",
        "- Recipe discovery remains unproved and path-state-bound.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "34_current_active_profile_boundary_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
