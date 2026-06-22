from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_joint_boundary_digit_gate.json"
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
    gate = load_json(GATE)
    assert_boundary("joint_boundary_digit_gate", gate)
    s = gate["summary"]
    classification = "JOINT_BOUNDARY_DIGIT_PAIR_MODEL_REJECTED"
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
        "Does the simplest joint target-stream/parser model improve generation by",
        "emitting `(boundary flag, digit)` pairs under prefix-trained contexts?",
        "",
        "## Result",
        "",
        f"- Prefix cutoffs tested: `{s['cutoff_count']}`.",
        f"- Context orders tested: `{s['orders_tested']}`.",
        f"- Best nontrivial model: `{s['best_nontrivial_model']}`.",
        f"- Best aggregate gain vs baseline: `{s['best_aggregate_gain_vs_baseline_bits']:.3f}` bits.",
        f"- Positive cells for best model: `{s['best_positive_cells']}/{s['best_cells']}`.",
        f"- Promotes joint parser: `{s['promotes_joint_parser']}`.",
        "",
        "The simplest joint model is rejected. Pairing the boundary flag with the",
        "current digit is not enough; context sparsity overwhelms any boundary",
        "signal. A future parser needs explicit latent state or another joint",
        "mechanism, not just `(boundary,digit)` tokens.",
        "",
        "## Decision",
        "",
        "- Simple joint boundary+digit pair emission is rejected.",
        "- No parser/generator is promoted.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Joint boundary digit gate](test_results/01_joint_boundary_digit_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
