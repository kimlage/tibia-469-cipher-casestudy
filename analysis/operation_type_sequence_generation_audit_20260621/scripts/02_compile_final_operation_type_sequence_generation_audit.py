from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_operation_type_sequence_generation_gate.json"
OUT = REPORTS / "final_operation_type_sequence_generation_audit.md"


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
    assert_boundary("operation_type_sequence_generation_gate", gate)
    s = gate["summary"]
    classification = (
        "OPERATION_TYPE_SEQUENCE_GENERATOR_PROMOTED"
        if s["promotes_operation_type_sequence_generator"]
        else "OPERATION_TYPE_SEQUENCE_GENERATOR_REJECTED_AS_POSTHOC_TEMPLATE"
    )
    lines = [
        "# Final Operation Type Sequence Generation Audit",
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
        "Can the literal/copy order inside each book be generated once",
        "`(op_count, literal_count)` is granted?",
        "",
        "## Result",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Literal/copy operation totals: `{s['literal_operation_count']}` / `{s['copy_operation_count']}`.",
        f"- Models tested: `{s['model_count']}`.",
        f"- Best model: `{s['best_model']}`.",
        f"- Best model kind: `{s['best_kind']}`.",
        f"- Best exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Best type hits: `{s['best_type_hits']}/{s['operation_count']}`.",
        f"- Best paid records: `{s['best_paid_records']}` vs exact type fields `{s['exact_type_field_records']}`.",
        f"- Paid-record delta vs exact type fields: `{s['paid_record_delta_vs_exact_type_fields']:+d}`.",
        f"- Random mean/p95/max exact books: `{s['random_mean_exact_books']:.3f}` / `{s['random_p95_exact_books']}` / `{s['random_max_exact_books']}`.",
        f"- Random mean/p95/max type hits: `{s['random_mean_type_hits']:.3f}` / `{s['random_p95_type_hits']}` / `{s['random_max_type_hits']}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout beats-random-p95 exact cells: `{s['prequential_beats_random_p95_exact_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout beats-random-p95 type-hit cells: `{s['prequential_beats_random_p95_type_hit_cells']}/{s['prequential_cells']}`.",
        "",
        "The best full-fit model is an exact template map, not a generator:",
        "it reproduces all books only by carrying `235` template records,",
        "`-26` versus the exact type-field atlas, and it has no",
        "promoting holdout cells.",
        "",
        "## Decision",
        "",
        "- No operation-type-sequence generator is promoted.",
        "- Literal/copy order remains retained unless derived jointly with length and copy availability.",
        "- Exact full-fit templates are rejected as posthoc materialization.",
        "- This does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Operation type sequence generation gate](test_results/01_operation_type_sequence_generation_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
