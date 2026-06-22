from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_digit_boundary_miss_transition_gate.json"
OUT = REPORTS / "final_target_digit_boundary_miss_transition_audit.md"


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
    assert_boundary("target_digit_boundary_miss_transition_gate", gate)
    s = gate["summary"]
    classification = "TARGET_DIGIT_BOUNDARY_MISS_TRANSITION_CLASSES_REJECTED_CONTROL"
    lines = [
        "# Final Target Digit Boundary Miss Transition Audit",
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
        "Are the cutpoints missed by `right_ge:4` explained by skeleton transition",
        "classes, length buckets, ordinal position, or chunk recurrence?",
        "",
        "## Result",
        "",
        f"- Cutpoints/hits/misses: `{s['cutpoint_count']}` / `{s['hit_count']}` / `{s['miss_count']}`.",
        f"- Features tested: `{s['feature_count']}`.",
        f"- Baseline miss-label atlas: `{s['baseline_miss_label_bits']:.3f}` bits.",
        f"- Best feature: `{s['best_feature']}` with `{s['best_category_count']}` categories.",
        f"- Best saving before/after feature charge: `{s['best_saving_before_feature_charge']:.3f}` / `{s['best_saving_after_feature_charge']:.3f}` bits.",
        f"- Random relabel p95 before feature charge: `{s['best_random_saving_p95_before_feature_charge']:.3f}` bits.",
        f"- Beats random p95: `{s['best_beats_random_p95']}`.",
        f"- Prefix-selected positive test cells: `{s['prequential_positive_test_cells']}/{s['prequential_cells']}`.",
        "",
        "The feature audit rejects this path as a promoted explanation. The best",
        "skeleton-conditioned feature is not above random relabel p95, and chunk",
        "recurrence features are too sparse to explain the missed cutpoints.",
        "",
        "## Decision",
        "",
        "- Miss transition/chunk feature is rejected as a promoted clue.",
        "- Endpoint generator is not promoted.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target digit boundary miss transition gate](test_results/01_target_digit_boundary_miss_transition_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
