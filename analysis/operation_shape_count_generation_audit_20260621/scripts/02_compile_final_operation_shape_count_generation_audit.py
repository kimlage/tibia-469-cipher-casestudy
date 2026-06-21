from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_operation_shape_count_generation_gate.json"
OUT = REPORTS / "final_operation_shape_count_generation_audit.md"


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
    assert_boundary("operation_shape_count_generation_gate", gate)
    s = gate["summary"]
    classification = (
        "OPERATION_SHAPE_COUNT_GENERATOR_PROMOTED"
        if s["promotes_operation_shape_count_generator"]
        else "OPERATION_SHAPE_COUNT_GENERATOR_REJECTED_WITH_AUDIT_ONLY_CONTEXT_CLUE"
    )
    lines = [
        "# Final Operation Shape Count Generation Audit",
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
        "Can each book's coarse operation shape `(op_count, literal_count)`",
        "be generated from book id and book length before exact type sequence,",
        "cutpoints, or sources?",
        "",
        "## Result",
        "",
        f"- Books tested: `{s['book_count']}`.",
        f"- Operation total: `{s['operation_count']}`.",
        f"- Literal/copy operation totals: `{s['literal_operation_count']}` / `{s['copy_operation_count']}`.",
        f"- Model candidates: `{s['model_count']}`.",
        f"- Best model: `{s['best_model']}`.",
        f"- Best exact shape books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Best op-count exact books: `{s['best_op_count_exact_books']}/{s['book_count']}`.",
        f"- Best literal-count exact books: `{s['best_literal_count_exact_books']}/{s['book_count']}`.",
        f"- Best total shape error: `{s['best_total_shape_error']}`.",
        f"- Best paid records: `{s['best_paid_records']}` vs exact shape atlas `{s['exact_shape_atlas_records']}`.",
        f"- Paid-record delta vs exact atlas: `{s['paid_record_delta_vs_exact_atlas']:+d}`.",
        f"- Random mean/p95/max exact books: `{s['random_mean_exact_books']:.3f}` / `{s['random_p95_exact_books']}` / `{s['random_max_exact_books']}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout beats-random-p95 exact cells: `{s['prequential_beats_random_p95_exact_cells']}/{s['prequential_cells']}`.",
        "",
        "The same context that helped `op_count` also gives a small full-fit",
        "shape-count reduction, but it is weaker: only `-2` paid records",
        "versus exact shape lookup, with `23` missed books and no promoting",
        "holdout cells.",
        "",
        "## Decision",
        "",
        "- No operation-shape-count generator is promoted.",
        "- Coarse `(op_count, literal_count)` shape remains a retained skeleton dependency.",
        "- The `-2` paid-record full-fit reduction is audit-only and does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Operation shape count generation gate](test_results/01_operation_shape_count_generation_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
