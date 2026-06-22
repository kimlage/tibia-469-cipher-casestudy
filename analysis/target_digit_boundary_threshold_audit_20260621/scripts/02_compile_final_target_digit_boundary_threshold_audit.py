from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_digit_boundary_threshold_gate.json"
OUT = REPORTS / "final_target_digit_boundary_threshold_audit.md"


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
    assert_boundary("target_digit_boundary_threshold_gate", gate)
    s = gate["summary"]
    classification = "TARGET_DIGIT_BOUNDARY_THRESHOLD_DEPENDENCY_REDUCED_NOT_GENERATOR"
    lines = [
        "# Final Target Digit Boundary Threshold Audit",
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
        "Can a `prev2` surprisal/rank threshold generate a boundary set directly,",
        "without granting op-count, if FP/FN corrections are paid?",
        "",
        "## Result",
        "",
        f"- Books/candidates/actual cutpoints: `{s['book_count']}` / `{s['candidate_position_count']}` / `{s['actual_cutpoint_count']}`.",
        f"- Best policy: `{s['best_policy']}`.",
        f"- Baseline full cutpoint atlas bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Correction bits after policy charge: `{s['best_correction_bits_after_policy']:.3f}`.",
        f"- Saving after policy charge: `{s['best_saving_after_policy']:.3f}` bits.",
        f"- Random saving p95 before policy charge: `{s['best_random_saving_p95_before_policy']:.3f}` bits.",
        f"- TP/FP/FN: `{s['best_true_positive']}` / `{s['best_false_positive']}` / `{s['best_false_negative']}`.",
        f"- Predicted boundaries/correction events: `{s['best_predicted_count']}` / `{s['best_correction_events']}`.",
        f"- Precision/recall: `{s['best_precision']:.6f}` / `{s['best_recall']:.6f}`.",
        f"- Exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Prefix-selected positive test-saving cells: `{s['prequential_positive_test_saving_cells']}/{s['prequential_cells']}`.",
        "",
        "This is a stronger dependency reduction than the op-count-conditioned",
        "pruning ledger because the policy generates a candidate boundary set",
        "without first declaring op-count. It is not a generator: the best policy",
        "requires a large correction list and produces no exact full book skeletons.",
        "",
        "## Decision",
        "",
        "- Dependency reduction is promoted.",
        "- No endpoint or skeleton generator is promoted.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target digit boundary threshold gate](test_results/01_target_digit_boundary_threshold_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
