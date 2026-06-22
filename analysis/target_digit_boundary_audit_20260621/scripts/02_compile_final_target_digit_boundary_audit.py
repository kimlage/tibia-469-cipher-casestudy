from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_target_digit_boundary_gate.json"
OUT = REPORTS / "final_target_digit_boundary_audit.md"


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
    assert_boundary("target_digit_boundary_gate", gate)
    s = gate["summary"]
    classification = "TARGET_DIGIT_BOUNDARY_MARKOV_CLUE_PROMOTED_NOT_GENERATOR"
    lines = [
        "# Final Target Digit Boundary Audit",
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
        "Does the promoted `prev2_digits` clue help explain operation endpoints,",
        "or does it only compress target payload after endpoints are declared?",
        "",
        "## Result",
        "",
        f"- Books tested: `{s['book_count']}`.",
        f"- Internal operation cutpoints: `{s['internal_cutpoint_count']}`.",
        f"- Candidate boundary positions: `{s['candidate_position_count']}`.",
        f"- Mean right-surprisal at real cutpoints: `{s['right_surprisal_mean']:.6f}`.",
        f"- Random right-surprisal mean/p95: `{s['right_surprisal_random_mean']:.6f}` / `{s['right_surprisal_random_p95']:.6f}`.",
        f"- Right-surprisal top10 hits: `{s['right_top10_hits']}/{s['internal_cutpoint_count']}` (`{s['right_top10_fraction']:.6f}`), above random p95 `{s['right_top10_random_p95']:.6f}`.",
        f"- Right-surprisal top-k selector hits: `{s['right_topk_hits']}/{s['internal_cutpoint_count']}` (`{s['right_topk_fraction']:.6f}`), exact nontrivial books `{s['right_topk_exact_nontrivial_books']}/{s['right_topk_nontrivial_books']}`.",
        f"- Zero-cutpoint books: `{s['zero_cutpoint_books']}`.",
        f"- Delta right-left mean vs p95 control: `{s['delta_mean']:.6f}` / `{s['delta_random_p95']:.6f}`.",
        "",
        "The result links the digit-process clue to segmentation: internal",
        "operation cutpoints are strongly enriched immediately before high",
        "surprisal digits under a prequential second-order digit model. This",
        "is a real mechanical clue, not a compression micro-sweep. It is not a",
        "generator: selecting the top-k surprisal positions recovers only a",
        "minority of cutpoints and does not reconstruct full book skeletons.",
        "",
        "## Decision",
        "",
        "- A target-digit boundary Markov clue is promoted.",
        "- No endpoint generator is promoted.",
        "- The skeleton remains an atlas/dependency, but now with a stronger structural diagnostic.",
        "- Compression bound is unchanged.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Target digit boundary gate](test_results/01_target_digit_boundary_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
