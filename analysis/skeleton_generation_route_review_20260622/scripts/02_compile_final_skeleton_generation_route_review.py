from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_skeleton_generation_route_review.json"
OUT = REPORTS / "final_skeleton_generation_route_review.md"


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
    assert_boundary("skeleton_generation_route_review", gate)
    s = gate["summary"]
    classification = "SKELETON_GENERATION_ROUTE_REVIEW_BOUNDARY_FRONTIER_SATURATED"
    lines = [
        "# Final Skeleton Generation Route Review",
        "",
        "Status: `analysis_only`",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Row0 origin: `unchanged_exogenous`",
        "Compression bound: `unchanged_8154_676268`",
        "",
        "## Result",
        "",
        f"- Routes reviewed: `{s['route_count']}`.",
        f"- Promoted generator routes: `{s['promoted_generator_routes']}`.",
        f"- Promoted clue/dependency routes: `{s['promoted_dependency_or_clue_routes']}`.",
        f"- Rejected/weak/deferred routes: `{s['rejected_or_weak_routes']}`.",
        f"- Open blocker: `{s['open_blocker']}`.",
        f"- Recommended next route: `{s['continue_route']}`.",
        "",
        s["decision"],
        "",
        "## Decision",
        "",
        "- Boundary-frontier work is saturated as a main route.",
        "- Simple source-free skeleton grammar, local length contexts, proportional cutpoint geometry, and boundary-miss label classification should not be continued without a new latent state.",
        "- The next aligned route is a joint target-stream/parser or explicit latent-state account that emits digits and boundaries together.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Skeleton generation route review](test_results/01_skeleton_generation_route_review.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
