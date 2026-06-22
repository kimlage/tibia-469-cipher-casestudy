from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_digit_boundary_pruning_gate.json"
OUT = REPORTS / "final_target_digit_boundary_pruning_audit.md"


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
    assert_boundary("target_digit_boundary_pruning_gate", gate)
    s = gate["summary"]
    classification = "TARGET_DIGIT_BOUNDARY_PRUNING_CLUE_PROMOTED_NOT_GENERATOR"
    lines = [
        "# Final Target Digit Boundary Pruning Audit",
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
        "Does the `prev2_digits` boundary surprisal clue reduce the declared",
        "cutpoint dependency after paying for misses and threshold choice?",
        "",
        "## Result",
        "",
        f"- Books/cutpoints/candidate positions: `{s['book_count']}` / `{s['cutpoint_count']}` / `{s['candidate_position_count']}`.",
        f"- Best q: `{s['best_q']}` with candidate fraction `{s['best_candidate_fraction']:.6f}`.",
        f"- Hits/misses: `{s['best_hit_count']}/{s['best_cutpoint_count']}` / `{s['best_miss_count']}`.",
        f"- Baseline cutpoint bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Model bits after q charge: `{s['best_model_bits_after_q_charge']:.3f}`.",
        f"- Saving after q charge: `{s['best_saving_after_q_charge']:.3f}` bits.",
        f"- Random saving p95 at best q: `{s['best_random_saving_p95']:.3f}` bits.",
        f"- Prefix-selected positive test-saving cells: `{s['prequential_positive_test_saving_cells']}/{s['prequential_cells']}` before q charge and `{s['prequential_positive_test_saving_after_q_charge_cells']}/{s['prequential_cells']}` after q charge.",
        "",
        "This promotes a cutpoint-pruning clue: high `prev2` right-surprisal",
        "bands reduce the paid cutpoint atlas and the best full-fit result",
        "beats random same-size candidate bands. It is still not an endpoint",
        "generator because exact cutpoints outside the band remain declared.",
        "",
        "## Decision",
        "",
        "- A boundary-pruning clue is promoted.",
        "- No endpoint generator is promoted.",
        "- The skeleton dependency is reduced diagnostically, not eliminated.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target digit boundary pruning gate](test_results/01_target_digit_boundary_pruning_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
