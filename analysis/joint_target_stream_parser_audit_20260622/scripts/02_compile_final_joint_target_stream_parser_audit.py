from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PAIR_GATE = TEST_RESULTS / "01_joint_boundary_digit_gate.json"
HAZARD_GATE = TEST_RESULTS / "02_boundary_hazard_state_gate.json"
ENDPOINT_GATE = TEST_RESULTS / "03_boundary_hazard_endpoint_decoder_gate.json"
OUT = REPORTS / "final_joint_target_stream_parser_audit.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") != "unchanged_exogenous":
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def main() -> None:
    pair_gate = load_json(PAIR_GATE)
    hazard_gate = load_json(HAZARD_GATE)
    endpoint_gate = load_json(ENDPOINT_GATE)
    assert_boundary("joint_boundary_digit_gate", pair_gate)
    assert_boundary("boundary_hazard_state_gate", hazard_gate)
    assert_boundary("boundary_hazard_endpoint_decoder_gate", endpoint_gate)
    pair = pair_gate["summary"]
    hazard = hazard_gate["summary"]
    endpoint = endpoint_gate["summary"]
    classification = "JOINT_TARGET_STREAM_PARSER_FIRST_GATES_MIXED"
    lines = [
        "# Final Joint Target Stream Parser Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Row0 origin: `unchanged_exogenous`",
        "Compression bound: `unchanged_8154_676268`",
        "",
        "## Question",
        "",
        "Do first-pass joint target-stream/parser models reduce dependency by",
        "emitting boundary state along with the digit stream under prefix holdout?",
        "",
        "## Result",
        "",
        f"- Pair-token best model: `{pair['best_nontrivial_model']}`.",
        f"- Pair-token aggregate gain vs baseline: `{pair['best_aggregate_gain_vs_baseline_bits']:.3f}` bits.",
        f"- Pair-token positive cells: `{pair['best_positive_cells']}/{pair['best_cells']}`.",
        f"- Hazard-state best feature: `{hazard['best_feature']}`.",
        f"- Hazard-state gain after feature charge: `{hazard['best_aggregate_gain_after_feature_charge']:.3f}` bits.",
        f"- Hazard-state positive cells: `{hazard['best_positive_cells']}/{hazard['best_cells']}`.",
        f"- Hazard-state random p95 before feature charge: `{hazard['best_random_gain_p95_before_feature_charge']:.3f}` bits.",
        f"- Hazard endpoint decoder hits: `{endpoint['aggregate_hazard_hits']}/{endpoint['aggregate_boundaries']}`.",
        f"- Hazard endpoint cells beating random p95: `{endpoint['cells_beating_random_p95']}/{endpoint['cutoff_count']}`.",
        "",
        "The pair-token model is rejected: pairing the boundary flag with the",
        "current digit is not enough. A simple sequential hazard state is promoted",
        "as a boundary dependency reducer: age since the last emitted boundary",
        "beats same-count random boundary controls under prefix holdout. It is not",
        "an exact parser: when decoded into exact endpoints with true op-count",
        "granted, it does not beat same-count random endpoint controls.",
        "",
        "## Decision",
        "",
        "- Simple joint boundary+digit pair emission is rejected.",
        "- Sequential boundary hazard state is promoted as a dependency reducer.",
        "- Hazard endpoint decoding is rejected.",
        "- No exact parser/generator is promoted.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Joint boundary digit gate](test_results/01_joint_boundary_digit_gate.md)",
        "- [Boundary hazard state gate](test_results/02_boundary_hazard_state_gate.md)",
        "- [Boundary hazard endpoint decoder gate](test_results/03_boundary_hazard_endpoint_decoder_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
