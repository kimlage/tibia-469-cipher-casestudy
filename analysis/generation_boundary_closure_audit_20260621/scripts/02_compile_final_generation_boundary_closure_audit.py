from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_generation_boundary_closure_audit.json"
OUT = REPORTS / "final_generation_boundary_closure_audit.md"


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
    assert_boundary("generation_boundary_closure_audit", gate)
    s = gate["summary"]
    lines = [
        "# Final Generation Boundary Closure Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{gate['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Row0 origin: `unchanged_exogenous`",
        "Compression bound: `unchanged_8154_676268`",
        "",
        "## Current Boundary",
        "",
        f"- Promoted generators across consolidated dependencies: `{s['promoted_generator_count']}/{s['dependency_count']}`.",
        f"- Materialized unit floor: `{s['total_materialized_units_floor']}`.",
        f"- Unit definition: {s['materialized_unit_definition']}.",
        f"- Next blocker: `{s['next_blocker']}`.",
        "",
        "## Dependency Status",
        "",
        "| Dependency | Status | Count |",
        "| --- | --- | ---: |",
    ]
    for row in gate["dependency_rows"]:
        lines.append(f"| `{row['dependency']}` | `{row['status']}` | `{row['count']}` |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The current model is a robust parser/atlas boundary, not a source-free",
            "generator. The exact operation skeleton remains the first blocker.",
            "Book lengths, literal payload, and copy sources remain declared",
            "dependencies; numeric book order is retained as canonical but not",
            "generated. Further work should not count as progress unless it",
            "removes one of these dependencies or generalizes under holdout.",
            "",
            "Row0 remains exogenous. The compression bound remains unchanged.",
            "No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
            "## Sources",
            "",
            "- [Generation boundary closure audit](test_results/01_generation_boundary_closure_audit.md)",
        ]
    )
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": gate["classification"], "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
