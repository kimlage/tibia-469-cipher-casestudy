from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL_RESULTS = ROOT / "analysis" / "authorial_mechanism_20260620" / "reports" / "test_results"

PAYLOAD_DEFAULT = AUTHORIAL_RESULTS / "138_literal_payload_default_decodability_audit.json"
PAYLOAD_STRUCTURAL = AUTHORIAL_RESULTS / "139_literal_payload_structural_context_audit.json"
PAYLOAD_PROFILE = AUTHORIAL_RESULTS / "143_current_literal_payload_profile_audit.json"
COPY_AVAILABILITY_GATE = TEST_RESULTS / "28_literal_copy_availability_gate.json"


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


def best_modal_default_candidate(data: dict[str, Any]) -> dict[str, Any]:
    return min(data["modal_default_candidates"], key=lambda row: float(row["bits"]))


def best_non_active_structural_candidate(data: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        row for row in data["candidates"] if row["label"] != data["best_candidate"]["label"]
    ]
    if not candidates:
        raise RuntimeError("no non-active structural candidates found")
    return min(candidates, key=lambda row: float(row["total_bits"]))


def make_result() -> dict[str, Any]:
    payload_default = load_json(PAYLOAD_DEFAULT)
    payload_structural = load_json(PAYLOAD_STRUCTURAL)
    payload_profile = load_json(PAYLOAD_PROFILE)
    copy_availability = load_json(COPY_AVAILABILITY_GATE)

    for name, data in [
        ("literal_payload_default_decodability", payload_default),
        ("literal_payload_structural_context", payload_structural),
        ("current_literal_payload_profile", payload_profile),
        ("literal_copy_availability_gate", copy_availability),
    ]:
        assert_boundary(name, data)

    active_bits = float(payload_profile["scope"]["active_literal_payload_bits"])
    if abs(active_bits - float(payload_default["active_literal_payload_bits"])) > 1e-9:
        raise RuntimeError("default audit active payload bits do not match profile")
    if abs(active_bits - float(payload_structural["active_literal_payload_bits"])) > 1e-9:
        raise RuntimeError("structural audit active payload bits do not match profile")
    if payload_profile["decision"]["literal_payload_profile"] != "order2_retained":
        raise RuntimeError("current profile no longer retains order2 payload model")
    if payload_default["best_candidate"]["order"] != 2:
        raise RuntimeError("default audit no longer selects active order2 categorical model")
    if payload_structural["best_candidate"]["label"] != "active_prev2":
        raise RuntimeError("structural audit no longer selects active prev2 model")
    if copy_availability["decision"]["literal_externality_status"] != "reduced_not_removed":
        raise RuntimeError("copy availability gate no longer keeps literal externality boundary")

    modal_best = best_modal_default_candidate(payload_default)
    structural_best = best_non_active_structural_candidate(payload_structural)
    comparison = payload_profile["comparison"]
    prefix_splits = payload_profile["prefix_splits"]
    order1_win_cutoffs = list(comparison["order1_frozen_win_cutoffs"])
    order2_frozen_win_cutoffs = [
        row["cutoff"]
        for row in prefix_splits
        if float(row["order2"]["test_frozen_bits"]) <= float(row["order1"]["test_frozen_bits"])
    ]
    order2_online_win_cutoffs = [
        row["cutoff"]
        for row in prefix_splits
        if float(row["order2"]["test_online_bits"]) <= float(row["order1"]["test_online_bits"])
    ]

    modal_delta = float(modal_best["bits"]) - active_bits
    structural_delta = float(structural_best["total_bits"]) - active_bits
    order1_full_delta = float(comparison["order1_full_corpus_delta_vs_order2_bits"])
    order1_frozen_delta = float(comparison["order1_frozen_delta_vs_order2_total_bits"])
    order1_online_delta = float(comparison["order1_online_delta_vs_order2_total_bits"])

    simplifications_rejected = (
        modal_delta > 0
        and structural_delta > 0
        and order1_full_delta > 0
        and order1_frozen_delta > 0
        and order1_online_delta > 0
    )
    classification = (
        "literal_payload_order2_retained_simplifications_rejected"
        if simplifications_rejected
        else "literal_payload_model_boundary_unresolved"
    )

    return {
        "schema": "literal_payload_model_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "literal_payload_default_decodability": rel(PAYLOAD_DEFAULT),
            "literal_payload_structural_context": rel(PAYLOAD_STRUCTURAL),
            "current_literal_payload_profile": rel(PAYLOAD_PROFILE),
            "literal_copy_availability_gate": rel(COPY_AVAILABILITY_GATE),
        },
        "summary": {
            "literal_digit_count": payload_profile["scope"]["literal_digit_count"],
            "active_literal_payload_bits": active_bits,
            "active_order": 2,
            "active_context_count": payload_profile["full_corpus"]["2"]["context_count"],
            "order0_full_corpus_bits": payload_profile["full_corpus"]["0"]["bits"],
            "order1_full_corpus_bits": payload_profile["full_corpus"]["1"]["bits"],
            "order2_full_corpus_bits": payload_profile["full_corpus"]["2"]["bits"],
            "order3_full_corpus_bits": payload_profile["full_corpus"]["3"]["bits"],
            "order1_full_corpus_delta_vs_order2_bits": order1_full_delta,
            "order1_online_delta_vs_order2_total_bits": order1_online_delta,
            "order1_frozen_delta_vs_order2_total_bits": order1_frozen_delta,
            "order1_frozen_win_cutoffs": order1_win_cutoffs,
            "order2_frozen_win_cutoffs": order2_frozen_win_cutoffs,
            "order2_online_win_cutoffs": order2_online_win_cutoffs,
            "best_modal_default_bits": modal_best["bits"],
            "best_modal_default_delta_vs_active_bits": modal_delta,
            "best_modal_default_default_order": modal_best["default_order"],
            "best_modal_default_exception_order": modal_best["exception_order"],
            "best_modal_default_exception_count": modal_best["exception_count"],
            "best_modal_default_default_count": modal_best["default_count"],
            "best_non_active_structural_label": structural_best["label"],
            "best_non_active_structural_total_bits": structural_best["total_bits"],
            "best_non_active_structural_delta_vs_active_bits": structural_delta,
            "structural_candidate_count": len(payload_structural["candidates"]),
            "modal_default_candidate_count": len(payload_default["modal_default_candidates"]),
            "literal_externality_status": copy_availability["decision"][
                "literal_externality_status"
            ],
            "copy_availability_classification": copy_availability["classification"],
            "simplifications_rejected": simplifications_rejected,
            "interpretation": (
                "After separating forced literal payload from optional parser "
                "repairs, the remaining literal digit model still cannot be "
                "simplified to order1, modal default/exception coding, or simple "
                "structural context splits. The active order2 previous-emitted-"
                "digit categorical model remains the current payload boundary."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged",
            "literal_payload_model_status": "active_order2_retained",
            "fallback_status": "modal_default_exception_rejected",
            "structural_context_status": "over_split_rejected",
            "generation_explanation_status": "literal_payload_dependency_sharpened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "29_literal_payload_model_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    lines = [
        "# Literal Payload Model Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "After the literal copy-availability gate reduces literal externality,",
        "this gate checks whether the remaining literal payload digit model can",
        "be simplified without retuning the held-out boundary into a post-hoc",
        "compressor claim.",
        "",
        "## Summary",
        "",
        f"- Literal payload digits: `{s['literal_digit_count']}`.",
        f"- Active literal payload bits: `{s['active_literal_payload_bits']:.3f}`.",
        f"- Active model: order-`{s['active_order']}` previous-emitted-digit context with `{s['active_context_count']}` contexts.",
        f"- Order-1 full-corpus delta vs order-2: `{s['order1_full_corpus_delta_vs_order2_bits']:.3f}` bits.",
        f"- Order-1 aggregate online prefix delta vs order-2: `{s['order1_online_delta_vs_order2_total_bits']:.3f}` bits.",
        f"- Order-1 aggregate frozen prefix delta vs order-2: `{s['order1_frozen_delta_vs_order2_total_bits']:.3f}` bits.",
        f"- Order-1 frozen split wins: `{s['order1_frozen_win_cutoffs']}`.",
        f"- Order-2 frozen split wins or ties: `{s['order2_frozen_win_cutoffs']}`.",
        f"- Order-2 online split wins or ties: `{s['order2_online_win_cutoffs']}`.",
        f"- Best modal default/exception candidate: `{s['best_modal_default_delta_vs_active_bits']:.3f}` bits worse than active.",
        f"- Best non-active structural context `{s['best_non_active_structural_label']}`: `{s['best_non_active_structural_delta_vs_active_bits']:.3f}` bits worse than active.",
        "",
        "## Interpretation",
        "",
        "The old order-1 simplification does not transfer to the current recipe:",
        "it wins some intermediate frozen splits, but loses on full corpus and in",
        "aggregate prefix online/frozen totals. Modal default/exception coding is",
        "decodable but worse, and the simple structural context families over-split",
        "the stream. The active order-2 payload model is therefore retained as a",
        "dependency boundary, not promoted as an authorial final method.",
        "",
        "## Boundary",
        "",
        "- No compression bound is promoted.",
        "- Literal payload dependency is sharpened, not removed.",
        "- Row0 origin remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    (TEST_RESULTS / "29_literal_payload_model_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
