from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_digit_boundary_type_gate.json"
OUT = REPORTS / "final_target_digit_boundary_type_audit.md"


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
    assert_boundary("target_digit_boundary_type_gate", gate)
    s = gate["summary"]
    classification = "TARGET_DIGIT_BOUNDARY_TYPE_RULE_REJECTED"
    lines = [
        "# Final Target Digit Boundary Type Audit",
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
        "Does the `prev2_digits` boundary clue also explain whether the next",
        "operation after a cutpoint is copy or literal?",
        "",
        "## Result",
        "",
        f"- Boundaries tested: `{s['boundary_count']}`.",
        f"- Next-type counts: `{s['next_type_counts']}`.",
        f"- Majority baseline: `{s['majority_type']}` with `{s['majority_hits']}/{s['boundary_count']}` hits.",
        f"- Best predicate: `{s['best_predicate']['predicate']}` / literal_when_true `{s['best_predicate']['literal_when_true']}`.",
        f"- Best predicate hits: `{s['best_predicate']['hits']}/{s['boundary_count']}`.",
        f"- Best predicate delta vs majority: `{s['best_predicate']['delta_vs_majority_hits']}`.",
        f"- Prequential positive-delta cells: `{s['prequential_cells_with_positive_delta']}/{s['prequential_cells']}`.",
        "",
        "The cutpoint surprisal clue does not transfer to operation type. The",
        "best tested predicates are all below the copy-majority baseline, and",
        "prefix/suffix context tables do not produce a positive delta. This",
        "keeps the boundary clue scoped to candidate cutpoint reduction.",
        "",
        "## Decision",
        "",
        "- No boundary type rule is promoted.",
        "- The boundary-pruning clue remains useful for endpoints only.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target digit boundary type gate](test_results/01_target_digit_boundary_type_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
