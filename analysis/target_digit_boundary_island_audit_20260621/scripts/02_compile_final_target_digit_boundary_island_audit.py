from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_digit_boundary_island_gate.json"
OUT = REPORTS / "final_target_digit_boundary_island_audit.md"


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
    assert_boundary("target_digit_boundary_island_gate", gate)
    s = gate["summary"]
    c = gate["threshold_comparison"]
    classification = "TARGET_DIGIT_BOUNDARY_ISLAND_CODE_REJECTED"
    lines = [
        "# Final Target Digit Boundary Island Audit",
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
        "Can high-surprisal boundary candidates be described as contiguous islands",
        "plus offsets, rather than a flat candidate set, without granting op-count?",
        "",
        "## Result",
        "",
        f"- Books/candidates/actual cutpoints: `{s['book_count']}` / `{s['candidate_position_count']}` / `{s['actual_cutpoint_count']}`.",
        f"- Policies tested: `{s['policy_count']}`.",
        f"- Best island policy: `{s['best_policy']}`.",
        f"- Baseline full cutpoint atlas bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Island correction bits after policy charge: `{s['best_island_correction_bits_after_policy']:.3f}`.",
        f"- Island saving after policy charge: `{s['best_island_saving_after_policy']:.3f}` bits.",
        f"- Same-policy threshold saving: `{s['best_threshold_saving_same_policy_after_policy']:.3f}` bits.",
        f"- Island delta vs same-policy threshold: `{s['best_island_delta_vs_same_policy_threshold_bits']:.3f}` bits.",
        f"- TP/FP/FN: `{s['best_true_positive']}` / `{s['best_false_positive']}` / `{s['best_false_negative']}`.",
        f"- Islands/occupied/multi-hit: `{s['best_island_count']}` / `{s['best_occupied_islands']}` / `{s['best_multi_hit_islands']}`.",
        f"- Exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Prefix-selected island-beats-threshold cells: `{s['prequential_island_beats_threshold_cells']}/{s['prequential_cells']}`.",
        "",
        "## Comparison To Threshold Gate",
        "",
        f"- Threshold gate best policy: `{c['threshold_gate_best_policy']}`.",
        f"- Threshold gate saving after policy charge: `{c['threshold_gate_saving_after_policy']:.3f}` bits.",
        f"- Best island saving delta vs threshold gate: `{c['best_island_saving_delta_vs_threshold_gate']:.3f}` bits.",
        f"- Best island correction delta vs threshold gate: `{c['best_island_correction_delta_vs_threshold_gate']:.3f}` bits.",
        "",
        "The island view is structurally informative: the best policy's occupied",
        "islands are single-hit. But it does not improve the paid code, does not",
        "win prequentially against same-policy threshold coding, and does not",
        "generate any exact book skeletons.",
        "",
        "## Decision",
        "",
        "- Island code is rejected as a replacement for the threshold gate.",
        "- Endpoint generator is not promoted.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target digit boundary island gate](test_results/01_target_digit_boundary_island_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
