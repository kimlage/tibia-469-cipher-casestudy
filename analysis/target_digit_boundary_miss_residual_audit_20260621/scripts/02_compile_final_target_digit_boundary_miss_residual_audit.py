from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_digit_boundary_miss_residual_gate.json"
OUT = REPORTS / "final_target_digit_boundary_miss_residual_audit.md"


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
    assert_boundary("target_digit_boundary_miss_residual_gate", gate)
    s = gate["summary"]
    classification = "TARGET_DIGIT_BOUNDARY_MISS_RESIDUAL_WEAK_NOT_PROMOTED"
    lines = [
        "# Final Target Digit Boundary Miss Residual Audit",
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
        "Can the cutpoints missed by the promoted `right_ge:4` boundary threshold",
        "be captured by a second-stage source-free residual candidate rule?",
        "",
        "## Result",
        "",
        f"- Primary policy: `{s['primary_policy']}`.",
        f"- Residual policies tested: `{s['residual_policy_count']}`.",
        f"- Best residual policy: `{s['best_residual_policy']}`.",
        f"- Threshold gate saving after policy charge: `{s['threshold_gate_saving_after_policy']:.3f}` bits.",
        f"- Residual saving after primary+residual policy charge: `{s['best_residual_saving_after_policy']:.3f}` bits.",
        f"- Delta vs threshold: `{s['best_delta_vs_threshold_bits']:.3f}` bits.",
        f"- Random residual delta p95: `{s['best_random_delta_p95_vs_threshold_bits']:.3f}` bits.",
        f"- Outside actual cutpoints: `{s['outside_actual']}`.",
        f"- Residual selected/TP/FP/FN: `{s['best_residual_selected_count']}` / `{s['best_residual_true_positive']}` / `{s['best_residual_false_positive']}` / `{s['best_residual_false_negative']}`.",
        f"- Residual precision/recall: `{s['best_residual_precision']:.6f}` / `{s['best_residual_recall']:.6f}`.",
        f"- Prefix-selected positive delta cells: `{s['prequential_positive_delta_cells']}/{s['prequential_cells']}`.",
        "",
        "The result is a weak full-fit dependency clue, not a promotion. The best",
        "residual policy beats random p95 in full fit, but prefix-selected",
        "validation is positive in only `4/5` cells and the policy remains broad",
        "and low precision.",
        "",
        "## Decision",
        "",
        f"- Dependency reduction is promoted: `{s['promotes_dependency_reduction']}`.",
        "- Endpoint generator is not promoted.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target digit boundary miss residual gate](test_results/01_target_digit_boundary_miss_residual_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
