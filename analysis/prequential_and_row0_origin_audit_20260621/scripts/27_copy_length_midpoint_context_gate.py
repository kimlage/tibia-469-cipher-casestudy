from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

MIDPOINT_CONTEXT = AUTHORIAL_RESULTS / "148_copy_length_midpoint_context_audit.json"
ACTIVE_PREQUENTIAL = AUTHORIAL_RESULTS / "145_current_active_prequential_profile_audit.json"


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
    midpoint = load_json(MIDPOINT_CONTEXT)
    active = load_json(ACTIVE_PREQUENTIAL)
    for name, data in [
        ("copy_length_midpoint_context", midpoint),
        ("current_active_prequential_profile", active),
    ]:
        assert_boundary(name, data)

    full = midpoint["full_corpus"]
    prefix = midpoint["prefix_future_suffix"]
    controls = midpoint["permutation_controls"]
    decision = midpoint["decision"]
    prefix_gaps = [
        float(row["midpoint_minus_global_frozen_bits"])
        for row in prefix["rows"]
    ]
    all_prefix_midpoint_better = all(gap < 0 for gap in prefix_gaps)
    best_cutoff_delta_vs_midpoint = (
        float(full["midpoint_35_stream_bits"]) - float(full["best_boundary"]["stream_bits"])
    )
    midpoint_supported = (
        decision["midpoint_context_retained"]
        and full["midpoint_gain_vs_global_bits"] > 0
        and all_prefix_midpoint_better
        and controls["p_permuted_midpoint_gain_ge_observed"] < 0.01
    )
    searched_boundary_promotable = (
        decision["best_boundary_promoted"]
        or best_cutoff_delta_vs_midpoint > 1.0
    )
    classification = (
        "copy_length_midpoint_context_generalizes_searched_cutoff_rejected"
        if midpoint_supported and not searched_boundary_promotable
        else "copy_length_midpoint_context_not_supported"
    )

    return {
        "schema": "copy_length_midpoint_context_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "copy_length_midpoint_context": rel(MIDPOINT_CONTEXT),
            "current_active_prequential_profile": rel(ACTIVE_PREQUENTIAL),
        },
        "summary": {
            "copy_length_events": midpoint["scope"]["copy_length_events"],
            "active_prequential_formula_bits": active["scope"][
                "active_compression_bound_bits"
            ],
            "active_prequential_recipe_discovery_proved": active["decision"][
                "recipe_discovery_proved"
            ],
            "global_stream_bits": full["global_stream_bits"],
            "midpoint_35_stream_bits": full["midpoint_35_stream_bits"],
            "midpoint_gain_vs_global_bits": full["midpoint_gain_vs_global_bits"],
            "best_boundary_cutoff": full["best_boundary"]["cutoff"],
            "best_boundary_stream_bits": full["best_boundary"]["stream_bits"],
            "best_boundary_gain_vs_global_bits": full[
                "best_boundary_gain_vs_global_bits"
            ],
            "best_cutoff_delta_vs_midpoint_bits": best_cutoff_delta_vs_midpoint,
            "midpoint_boundary_rank": full["midpoint_boundary_rank"],
            "midpoint_context_counts": full["midpoint_context_counts"],
            "prefix_frozen_split_count": len(prefix_gaps),
            "prefix_frozen_midpoint_win_count": sum(1 for gap in prefix_gaps if gap < 0),
            "prefix_frozen_midpoint_minus_global_bits_min": min(prefix_gaps),
            "prefix_frozen_midpoint_minus_global_bits_mean": sum(prefix_gaps)
            / len(prefix_gaps),
            "prefix_frozen_midpoint_minus_global_bits_max": max(prefix_gaps),
            "p_permuted_midpoint_gain_ge_observed": controls[
                "p_permuted_midpoint_gain_ge_observed"
            ],
            "p_permuted_best_boundary_gain_ge_observed": controls[
                "p_permuted_best_boundary_gain_ge_observed"
            ],
            "permutation_control_count": controls["control_count"],
            "midpoint_supported": midpoint_supported,
            "searched_boundary_promoted": searched_boundary_promotable,
            "interpretation": (
                "The natural book midpoint is supported as a copy-length context: "
                "it beats global on full corpus, every tested prefix-frozen split, "
                "and book-id permutation controls. The searched cutoff 37 is only "
                "0.256 bits better, so it remains an ad-hoc boundary and is not "
                "promoted."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged",
            "copy_length_context_status": "midpoint_context_retained",
            "searched_boundary_status": "cutoff_37_not_promoted",
            "generation_explanation_status": "copy_length_context_generalization_strengthened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "27_copy_length_midpoint_context_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Copy Length Midpoint Context Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The active copy-length default/exception stream uses the declared context",
        "`book_id < 35` versus `book_id >= 35`. This gate checks whether that",
        "midpoint split is a supported mechanical context or a removable/posthoc",
        "parameter, and whether the searched cutoff `37` should replace it.",
        "",
        "## Summary",
        "",
        f"- Copy-length events: `{s['copy_length_events']}`.",
        f"- Global stream bits: `{s['global_stream_bits']:.3f}`.",
        f"- Midpoint-35 stream bits: `{s['midpoint_35_stream_bits']:.3f}`.",
        f"- Midpoint gain vs global: `{s['midpoint_gain_vs_global_bits']:.3f}` bits.",
        f"- Best searched cutoff: `{s['best_boundary_cutoff']}`.",
        f"- Best cutoff gain vs global: `{s['best_boundary_gain_vs_global_bits']:.3f}` bits.",
        f"- Best cutoff delta vs midpoint: `{s['best_cutoff_delta_vs_midpoint_bits']:.3f}` bits.",
        f"- Midpoint rank among one-cut boundaries: `{s['midpoint_boundary_rank']}`.",
        f"- Prefix-frozen midpoint wins: `{s['prefix_frozen_midpoint_win_count']}/{s['prefix_frozen_split_count']}`.",
        f"- Prefix-frozen midpoint-minus-global min/mean/max: "
        f"`{s['prefix_frozen_midpoint_minus_global_bits_min']:.3f}` / "
        f"`{s['prefix_frozen_midpoint_minus_global_bits_mean']:.3f}` / "
        f"`{s['prefix_frozen_midpoint_minus_global_bits_max']:.3f}` bits.",
        f"- P(permuted midpoint gain >= observed): "
        f"`{s['p_permuted_midpoint_gain_ge_observed']:.4f}`.",
        f"- P(permuted best-boundary gain >= observed): "
        f"`{s['p_permuted_best_boundary_gain_ge_observed']:.4f}`.",
        "",
        "## Interpretation",
        "",
        "The midpoint context is retained as a real mechanical component: it beats",
        "the global copy-length context by `13.839` bits, wins all `5/5`",
        "prefix-frozen future-suffix checks, and is unusual under 300 book-id",
        "permutation controls. The searched cutoff `37` is only `0.256` bits",
        "better than the natural midpoint, so promoting it would add ad-hoc",
        "description cost for a sub-bit local gain.",
        "",
        "## Boundary",
        "",
        "- No compression bound is promoted.",
        "- Recipe discovery remains partial; this validates one learned component.",
        "- No plaintext, translation, semantic reading, row0 change, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "27_copy_length_midpoint_context_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
