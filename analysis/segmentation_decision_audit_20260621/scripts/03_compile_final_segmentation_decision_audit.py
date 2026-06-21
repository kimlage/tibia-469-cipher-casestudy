from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

TRACE = TEST_RESULTS / "01_segmentation_decision_trace.json"
STRUCTURAL = TEST_RESULTS / "02_structural_segmentation_hypothesis_audit.json"
FINAL = REPORTS / "final_segmentation_decision_audit.md"


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
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def main() -> None:
    trace = load_json(TRACE)
    structural = load_json(STRUCTURAL)
    assert_boundary("segmentation_decision_trace", trace)
    assert_boundary("structural_segmentation_hypothesis", structural)

    ts = trace["summary"]
    ss = structural["summary"]
    exception_rows = structural["exception_rows"]

    lines = [
        "# Final Segmentation Decision Audit",
        "",
        "Status: `analysis_only`",
        "Classification: `PROMOTED_MECHANICAL_SEGMENTATION_CLUE` for parser segmentation; `AUDIT_ONLY` for source-free generation.",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Row0 origin: `unchanged_exogenous`",
        "Compression bound: `unchanged_8154_676268`",
        "",
        "## Question",
        "",
        "Can the retained `(source,length)` decisions be explained as a",
        "mechanical segmentation/parser rule rather than another local bit",
        "sweep?",
        "",
        "## Main Result",
        "",
        "On the stable copy projection used by the recent length gates, the rule",
        "`choose the longest previous target match; break source ties by earliest source`",
        f"recovers `{ss['target_text_global_longest_pair_hits']}/{ss['target_text_global_longest_pair_total']}`",
        "copy pairs.",
        "",
        "This is a real mechanical parser clue: it sharply reduces the declared",
        "`(source,length)` dependency for copy segmentation when the target book",
        "text is being parsed. It is not a source-free generator for the 70 books,",
        "because it still requires the target suffix as input and has one",
        "exception.",
        "",
        "## Trace Coverage",
        "",
        f"- Reference skeleton operations: `{ts['reference_skeleton_operation_count']}`.",
        f"- Stable-projection operations traced: `{ts['stable_projection_operation_count']}`.",
        f"- Copy decisions traced: `{ts['copy_count']}`.",
        f"- Candidate pair median: `{ts['candidate_pair_count_summary']['median']:.3f}`.",
        f"- Candidate pair max: `{ts['candidate_pair_count_summary']['max']}`.",
        f"- Declared copy equals source-local target max: `{ts['declared_is_max_count']}/{ts['copy_count']}`.",
        f"- Stable-projection literal gaps: `{ts['stable_projection_literal_gap_count']}` "
        f"with `{ts['stable_projection_literal_digit_count']}` literal digits.",
        "",
        "The stable projection has one more literal gap than the reference",
        "skeleton ledger (`54` vs `53`) and one fewer literal digit (`265` vs",
        "`266`). This report therefore treats the finding as a copy-segmentation",
        "parser clue, not a replacement for the full skeleton ledger.",
        "",
        "## Structural Hypotheses",
        "",
        "| Hypothesis | Result | Boundary |",
        "|---|---:|---|",
        f"| Longest previous target match + earliest source | `{ss['best_source_tie_policy_hits']}/{ss['copy_count']}` | parser clue, target-text-aware |",
        f"| Random source among global-max matches | expected `{ss['random_global_max_source_expected_hits']:.3f}/{ss['copy_count']}` | negative control |",
        f"| Unique global-max source forcing | `{ss['unique_global_max_source_rows']}/{ss['copy_count']}` rows | partial only |",
        f"| Recurrent next boundary preserved | `{ss['recurrent_boundary_hits']}/{ss['copy_count']}` | weak clue, not sufficient |",
        f"| Stop before max protects literal payload | `{ss['literal_payload_protection_hits']}/{ss['copy_count']}` | rejected |",
        "",
        "## Exception",
        "",
        "| Book | Op | Projection copy | Declared length | Max length | Candidate pairs | Declared boundary pairs | Max boundary pairs |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in exception_rows:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['projection_copy_index']}` | "
            f"`{row['declared_length']}` | `{row['all_source_max_length']}` | "
            f"`{row['candidate_pair_count']}` | "
            f"`{row['declared_boundary_candidate_pair_count']}` | "
            f"`{row['max_boundary_candidate_pair_count']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Found a strong target-text-aware parser rule for copy segmentation.",
            "- Did not find a source-free generation rule for the book digits.",
            "- Reduced the practical copy `(source,length)` blocker to: target text must be available, stable projection must be accepted, and one exception remains.",
            "- Rejected the literal-payload-protection shortcut and weakened recurrent-boundary explanations.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, fan gloss, semantic reading, or case reopening is introduced.",
            "",
            "## Next Blocker",
            "",
            "The next real blocker is not another local length policy. It is a",
            "source-free account of why the target digit stream exists, or a",
            "controlled parser integration that proves the stable projection can",
            "replace the retained `(source,length)` ledger without smuggling in",
            "target text or changing the skeleton/literal accounting.",
            "",
            "## Sources",
            "",
            "- [Segmentation decision trace](test_results/01_segmentation_decision_trace.md)",
            "- [Structural segmentation hypothesis audit](test_results/02_structural_segmentation_hypothesis_audit.md)",
            "",
        ]
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    FINAL.write_text("\n".join(lines), encoding="utf-8")
    print(FINAL)


if __name__ == "__main__":
    main()
