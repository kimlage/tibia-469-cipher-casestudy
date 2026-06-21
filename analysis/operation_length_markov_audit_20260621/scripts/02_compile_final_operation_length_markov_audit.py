from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_operation_length_markov_gate.json"
OUT = REPORTS / "final_operation_length_markov_audit.md"


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
    assert_boundary("operation_length_markov_gate", gate)
    s = gate["summary"]
    classification = (
        "OPERATION_LENGTH_MARKOV_GENERATOR_PROMOTED"
        if s["promotes_operation_length_generator"]
        else "OPERATION_LENGTH_MARKOV_GENERATOR_REJECTED"
    )
    lines = [
        "# Final Operation Length Markov Audit",
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
        "If book lengths and operation types are granted, can simple Markov or",
        "context grammars generate the `261` operation lengths?",
        "",
        "## Result",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Context families tested: `{s['context_family_count']}`.",
        f"- Best context: `{s['best_context']}`.",
        f"- Best full-fit exact books: `{s['best_full_exact_books']}/{s['book_count']}`.",
        f"- Best full-fit generated row hits: `{s['best_full_generation_row_hits']}/{s['best_full_truth_ops']}`.",
        f"- Best rowwise exact lengths: `{s['best_rowwise_exact_lengths']}/{s['operation_count']}`.",
        f"- Best mean exact prefix ops: `{s['best_mean_exact_prefix_ops']:.3f}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout any-exact-book cells: `{s['prequential_any_exact_book_cells']}/{s['prequential_cells']}`.",
        "",
        "## Decision",
        "",
        "- No operation-length Markov/context generator is promoted.",
        "- The operation-length atlas remains the operation-skeleton blocker.",
        "- The negative result is generous: book lengths and operation types are granted.",
        "- This does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Operation length Markov gate](test_results/01_operation_length_markov_gate.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
