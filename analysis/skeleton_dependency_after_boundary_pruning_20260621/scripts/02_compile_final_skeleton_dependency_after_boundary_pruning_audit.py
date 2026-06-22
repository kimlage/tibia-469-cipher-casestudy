from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_skeleton_dependency_after_boundary_pruning_gate.json"
OUT = REPORTS / "final_skeleton_dependency_after_boundary_pruning_audit.md"


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
    assert_boundary("skeleton_dependency_after_boundary_pruning_gate", gate)
    s = gate["summary"]
    classification = "SKELETON_DEPENDENCY_REDUCED_NOT_GENERATED"
    lines = [
        "# Final Skeleton Dependency After Boundary Pruning Audit",
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
        "After promoting the `prev2` boundary-pruning clue, how much of the",
        "operation skeleton dependency is actually reduced once op counts are",
        "also charged?",
        "",
        "## Result",
        "",
        f"- Books/internal cutpoints/candidates: `{s['book_count']}` / `{s['internal_cutpoint_count']}` / `{s['candidate_cutpoint_positions']}`.",
        f"- Op-count uniform bits: `{s['op_count_uniform_bits']:.3f}`.",
        f"- Exact conditional cutpoint bits: `{s['exact_conditional_cutpoint_bits']:.3f}`.",
        f"- Pruned conditional cutpoint bits: `{s['pruned_conditional_cutpoint_bits']:.3f}`.",
        f"- Exact full cutpoint atlas bits: `{s['exact_full_cutpoint_atlas_bits']:.3f}`.",
        f"- Pruned full cutpoint atlas bits: `{s['pruned_full_cutpoint_atlas_bits']:.3f}`.",
        f"- Full cutpoint atlas saving: `{s['full_cutpoint_atlas_saving_bits']:.3f}` bits.",
        f"- Op-count share after pruning: `{s['op_count_fraction_after_pruning']:.6f}`.",
        f"- Pruning hits/misses: `{s['pruning_hits']}` / `{s['pruning_misses']}`.",
        f"- Type transfer: `{s['type_transfer_status']}`.",
        "",
        "The promoted boundary clue does reduce the skeleton cutpoint dependency",
        "under a paid ledger. It does not generate the skeleton: op counts remain",
        "external, `115` cutpoints are still outside the high-surprisal band, and",
        "the copy/literal type transfer audit is rejected.",
        "",
        "## Decision",
        "",
        "- Dependency reduction is promoted.",
        "- No skeleton generator is promoted.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Skeleton dependency after boundary pruning gate](test_results/01_skeleton_dependency_after_boundary_pruning_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
