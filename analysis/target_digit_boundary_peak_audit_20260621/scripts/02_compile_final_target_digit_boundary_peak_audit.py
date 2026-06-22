from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_digit_boundary_peak_gate.json"
OUT = REPORTS / "final_target_digit_boundary_peak_audit.md"


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
    assert_boundary("target_digit_boundary_peak_gate", gate)
    s = gate["summary"]
    c = gate["threshold_comparison"]
    classification = "TARGET_DIGIT_BOUNDARY_PEAK_SUPPRESSION_WEAK_NOT_PROMOTED"
    lines = [
        "# Final Target Digit Boundary Peak Audit",
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
        "Can the `prev2` boundary signal be sharpened into local peaks or",
        "non-maximum-suppressed rank peaks, without granting op-count?",
        "",
        "## Result",
        "",
        f"- Books/candidates/actual cutpoints: `{s['book_count']}` / `{s['candidate_position_count']}` / `{s['actual_cutpoint_count']}`.",
        f"- Policies tested: `{s['policy_count']}`.",
        f"- Best peak policy: `{s['best_policy']}`.",
        f"- Baseline full cutpoint atlas bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Correction bits after policy charge: `{s['best_correction_bits_after_policy']:.3f}`.",
        f"- Saving after policy charge: `{s['best_saving_after_policy']:.3f}` bits.",
        f"- TP/FP/FN: `{s['best_true_positive']}` / `{s['best_false_positive']}` / `{s['best_false_negative']}`.",
        f"- Predicted boundaries/correction events: `{s['best_predicted_count']}` / `{s['best_correction_events']}`.",
        f"- Precision/recall: `{s['best_precision']:.6f}` / `{s['best_recall']:.6f}`.",
        f"- Exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Prefix-selected positive test-saving cells: `{s['prequential_positive_test_saving_cells']}/{s['prequential_cells']}`.",
        "",
        "## Comparison To Threshold Gate",
        "",
        f"- Prior threshold policy: `{c['threshold_policy']}`.",
        f"- Saving delta vs threshold: `{c['saving_delta_vs_threshold']:.3f}` bits.",
        f"- Correction-event delta vs threshold: `{c['correction_event_delta_vs_threshold']}`.",
        f"- False-positive delta vs threshold: `{c['false_positive_delta_vs_threshold']}`.",
        f"- False-negative delta vs threshold: `{c['false_negative_delta_vs_threshold']}`.",
        "",
        "Peak suppression is a meaningful diagnostic because it cuts the correction",
        "event count almost in half, but it is worse as a paid code: it discards too",
        "many true cutpoints and still generates no exact book skeletons.",
        "",
        "## Decision",
        "",
        "- Local peak / non-maximum suppression replacement is not promoted.",
        "- Endpoint generator is not promoted.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target digit boundary peak gate](test_results/01_target_digit_boundary_peak_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
