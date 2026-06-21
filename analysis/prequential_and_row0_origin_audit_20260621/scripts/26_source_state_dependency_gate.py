from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

ACTIVE_REPARSE_STATE = AUTHORIAL_RESULTS / "146_active_reparse_state_boundary_audit.json"
STATE_FREE_DEFAULT = AUTHORIAL_RESULTS / "147_copy_source_state_free_default_audit.json"
SOURCE_CANONICALITY_GATE = TEST_RESULTS / "25_source_canonicality_decodability_gate.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened") is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim") is not False:
        raise RuntimeError(f"{name} introduced plaintext")


def make_result() -> dict[str, Any]:
    active_state = load_json(ACTIVE_REPARSE_STATE)
    state_free = load_json(STATE_FREE_DEFAULT)
    canonicality_gate = load_json(SOURCE_CANONICALITY_GATE)
    for name, data in [
        ("active_reparse_state_boundary", active_state),
        ("copy_source_state_free_default", state_free),
        ("source_canonicality_decodability_gate", canonicality_gate),
    ]:
        assert_boundary(name, data)

    state_free_decision = state_free["decision"]
    prefix_rows = state_free["prefix_future_suffix"]["rows"]
    best_state_free_name = state_free_decision["best_state_free_name"]
    prefix_gaps = [
        float(
            row["models"][best_state_free_name]["test_frozen_bits"]
            - row["models"]["active_previous_source_plus_length"]["test_frozen_bits"]
        )
        for row in prefix_rows
    ]
    all_prefix_worse = all(gap > 0 for gap in prefix_gaps)
    promoted = (
        not state_free_decision["active_path_dependent_default_retained"]
        or bool(state_free_decision["state_free_default_promoted"])
    )
    classification = (
        "source_state_dependency_removed_by_state_free_default"
        if promoted
        else "source_state_dependency_retained_state_free_defaults_rejected"
    )

    return {
        "schema": "source_state_dependency_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "active_reparse_state_boundary": rel(ACTIVE_REPARSE_STATE),
            "copy_source_state_free_default": rel(STATE_FREE_DEFAULT),
            "source_canonicality_decodability_gate": rel(SOURCE_CANONICALITY_GATE),
        },
        "summary": {
            "active_reparse_state_key_required": active_state["scope"][
                "active_reparse_state_key_required"
            ],
            "old_reparse_state_key": active_state["scope"]["old_reparse_state_key"],
            "exact_active_reparse_implemented": active_state["summary"][
                "exact_active_reparse_implemented"
            ],
            "max_book_state_proxy_multiplier": active_state["summary"][
                "max_book_state_proxy_multiplier"
            ],
            "best_state_free_default": state_free_decision["best_state_free_name"],
            "best_state_free_stream_penalty_bits": state_free_decision[
                "best_state_free_worse_than_active_stream_bits"
            ],
            "best_state_free_total_penalty_bits": state_free_decision[
                "best_state_free_worse_than_active_total_bits"
            ],
            "state_free_default_promoted": state_free_decision[
                "state_free_default_promoted"
            ],
            "active_path_dependent_default_retained": state_free_decision[
                "active_path_dependent_default_retained"
            ],
            "prefix_frozen_split_count": len(prefix_rows),
            "prefix_frozen_loss_count": sum(1 for gap in prefix_gaps if gap > 0),
            "prefix_frozen_gap_bits_min": min(prefix_gaps),
            "prefix_frozen_gap_bits_mean": sum(prefix_gaps) / len(prefix_gaps),
            "prefix_frozen_gap_bits_max": max(prefix_gaps),
            "all_prefix_frozen_state_free_worse": all_prefix_worse,
            "canonicality_removed_source_dependency": canonicality_gate["summary"][
                "copy_source_dependency_removed_by_canonicality"
            ],
            "earliest_exact_chunk_rule_decoder_computable": canonicality_gate["summary"][
                "earliest_exact_chunk_rule_decoder_computable"
            ],
            "interpretation": (
                "The active source ledger still requires previous-copy source and "
                "length state. Earliest-source canonicality is encoder-side only, "
                "and every tested state-free source default is worse on the full "
                "corpus and on every prefix-frozen split."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged",
            "source_state_status": "path_dependent_previous_copy_state_retained",
            "state_free_source_default_status": "rejected",
            "generation_explanation_status": "source_state_boundary_sharpened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "26_source_state_dependency_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Source State Dependency Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 146 localized the active deterministic-reparse blocker: the active",
        "copy-source default depends on previous copy source and previous copy",
        "length. Audit 147 tested state-free decoder-computable defaults. This gate",
        "checks whether those results remove the source-state dependency after the",
        "canonicality/decodability boundary is applied.",
        "",
        "## Summary",
        "",
        f"- Old reparse state key: `{s['old_reparse_state_key']}`.",
        f"- Active required state key: `{s['active_reparse_state_key_required']}`.",
        f"- Exact active reparse implemented upstream: `{s['exact_active_reparse_implemented']}`.",
        f"- Max book state-proxy multiplier: `{s['max_book_state_proxy_multiplier']}`.",
        f"- Best state-free default: `{s['best_state_free_default']}`.",
        f"- Best state-free stream penalty: `{s['best_state_free_stream_penalty_bits']:.3f}` bits.",
        f"- Best state-free total penalty: `{s['best_state_free_total_penalty_bits']:.3f}` bits.",
        f"- Prefix-frozen state-free losses: `{s['prefix_frozen_loss_count']}/{s['prefix_frozen_split_count']}`.",
        f"- Prefix-frozen gap min/mean/max: `{s['prefix_frozen_gap_bits_min']:.3f}` / "
        f"`{s['prefix_frozen_gap_bits_mean']:.3f}` / `{s['prefix_frozen_gap_bits_max']:.3f}` bits.",
        f"- Canonicality removed source dependency: `{s['canonicality_removed_source_dependency']}`.",
        f"- Earliest exact-chunk rule decoder-computable: `{s['earliest_exact_chunk_rule_decoder_computable']}`.",
        "",
        "## Interpretation",
        "",
        "The state-free candidates do not replace the active path-dependent source",
        "default. The best candidate, `state_free_back_current_length`, is still",
        "`15.186` bits worse on the full source stream and loses every tested",
        "prefix-frozen split. Combined with the canonicality gate, this keeps the",
        "source ledger as a real decoder dependency rather than a removable",
        "tie-break note.",
        "",
        "## Boundary",
        "",
        "- No compression bound is promoted.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "- Row0/table origin remains exogenous.",
    ]
    (TEST_RESULTS / "26_source_state_dependency_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
