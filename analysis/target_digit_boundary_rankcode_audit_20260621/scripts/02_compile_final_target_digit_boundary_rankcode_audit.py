from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_digit_boundary_rankcode_gate.json"
OUT = REPORTS / "final_target_digit_boundary_rankcode_audit.md"


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
    assert_boundary("target_digit_boundary_rankcode_gate", gate)
    s = gate["summary"]
    classification = "TARGET_DIGIT_BOUNDARY_RANKCODE_WEAK_NOT_PROMOTED"
    lines = [
        "# Final Target Digit Boundary Rank-Code Audit",
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
        "Does the whole `prev2_digits` boundary rank distribution reduce the",
        "declared cutpoint atlas beyond a single high-surprisal band?",
        "",
        "## Result",
        "",
        f"- Books/cutpoints/candidate positions: `{s['book_count']}` / `{s['cutpoint_count']}` / `{s['candidate_position_count']}`.",
        f"- Best scheme: `{s['best_scheme']}`.",
        f"- Best bin totals: `{s['best_bin_totals']}`.",
        f"- Baseline cutpoint bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Model bits after scheme charge: `{s['best_model_bits_after_scheme_charge']:.3f}`.",
        f"- Saving after scheme charge: `{s['best_saving_after_scheme_charge']:.3f}` bits.",
        f"- Random saving p95 for best scheme: `{s['best_random_saving_p95']:.3f}` bits.",
        f"- Prefix-selected positive test-saving cells after scheme charge: `{s['prequential_positive_test_saving_after_scheme_charge_cells']}/{s['prequential_cells']}`.",
        "",
        "The rank-code view is useful but does not pass the stricter promotion",
        "gate. It improves the full-fit paid atlas relative to the one-band",
        "pruning code, but prefix-selected suffix validation fails in the last",
        "cell. The prior boundary-pruning clue remains the promoted result.",
        "",
        "## Decision",
        "",
        "- No boundary rank-code clue is promoted.",
        "- No endpoint generator is promoted.",
        "- This records a weak diagnostic and a promotion boundary.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target digit boundary rank-code gate](test_results/01_target_digit_boundary_rankcode_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
