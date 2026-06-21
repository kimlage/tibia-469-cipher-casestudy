from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_operation_length_motif_library_gate.json"
OUT = REPORTS / "final_operation_length_motif_audit.md"


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
    assert_boundary("operation_length_motif_library_gate", gate)
    s = gate["summary"]
    classification = (
        "OPERATION_LENGTH_MOTIF_GENERATOR_PROMOTED"
        if s["promotes_operation_length_motif_generator"]
        else "OPERATION_LENGTH_MOTIF_LIBRARY_NOT_PROMOTED"
    )
    lines = [
        "# Final Operation Length Motif Audit",
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
        "Can the `261` operation lengths be represented as reusable sub-book",
        "motifs rather than a one-row-per-operation atlas?",
        "",
        "## Result",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Best mode: `{s['best_mode']}`.",
        f"- Best library size: `{s['best_library_size']}`.",
        f"- Best records vs exact atlas: `{s['best_total_records']}` vs `{s['best_exact_atlas_records']}` (`{s['best_delta_vs_exact_atlas_records']:+d}`).",
        f"- Best residual singletons: `{s['best_residual_singletons']}`.",
        f"- Best all-motif-covered books: `{s['best_all_motif_books']}/{s['book_count']}`.",
        "",
        "The only full-fit gain is a tiny `-2` record reduction while leaving",
        "`249` operation lengths as residual singletons. In prefix/holdout, the",
        "selected motif libraries cover `0` future books without residuals and",
        "do not improve the test atlas record count.",
        "",
        "## Decision",
        "",
        "- No operation-length motif generator is promoted.",
        "- Sub-book motif reuse is too sparse to replace the operation-length atlas.",
        "- This does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Operation length motif library gate](test_results/01_operation_length_motif_library_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
