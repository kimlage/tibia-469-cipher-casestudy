from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

GATE = TEST_RESULTS / "01_book_order_dependency_gate.json"
OUT = REPORTS / "final_book_order_generation_audit.md"


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
    assert_boundary("book_order_dependency_gate", gate)
    s = gate["summary"]
    classification = (
        "BOOK_ORDER_GENERATOR_PROMOTED"
        if s["numeric_order_promoted_as_generator"]
        else "BOOK_ORDER_CANONICAL_RETAINED_NOT_GENERATED"
    )
    lines = [
        "# Final Book Order Generation Audit",
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
        "Is numeric book order a generated mechanical rule, a compact canonical",
        "order retained by the formula, or replaceable by a searched non-numeric",
        "order?",
        "",
        "## Consolidated Evidence",
        "",
        f"- Prefix-trained components beat uniform in `{s['preq_prefix_online_beats_uniform_cutoffs']}` cutoffs.",
        f"- Numeric prefixes are order-specific in `0` online/frozen cutoffs at p<=0.05.",
        f"- Numeric online frontier has `{s['frontier_numeric_after_bootstrap_raw_wins']}/{s['frontier_after_bootstrap_book_count']}` after-bootstrap raw wins.",
        f"- The same frontier criterion is not unique: `{s['frontier_orders_with_perfect_after_bootstrap']}` tested orders and `{s['frontier_random_orders_with_perfect_after_bootstrap']}` random orders are also perfect after bootstrap.",
        f"- The frontier best order is `{s['frontier_best_total_gain_order']}` at `{s['frontier_best_total_gain_delta_vs_numeric_bits']:+.3f}` bits versus numeric on that local metric.",
        f"- Under the full formula, best raw and charged order are both `{s['promotion_full_formula_best_charged_order']}`.",
        f"- Promotable non-numeric orders: `{s['promotion_promotable_order_count']}`.",
        f"- `random_04` is `+{s['random_04_full_formula_charged_delta_vs_numeric_bits']:.3f}` bits worse than numeric after full-formula and descriptor costs.",
        f"- Online reparse random raw/charged orders <= numeric: `{s['online_reparse_random_raw_le_numeric_count']}` / `{s['online_reparse_random_charged_le_numeric_count']}`.",
        "",
        "## Decision",
        "",
        "- Numeric order remains the compact canonical order used by the formula.",
        "- Numeric order is not promoted as a generated mechanical rule.",
        "- Arbitrary searched non-numeric order is not promoted.",
        "- Order-dependent parser evidence remains predictive/diagnostic, not authorial-origin evidence.",
        "- This does not change the compression bound.",
        "- Row0 remains exogenous and unchanged.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        "",
        "## Sources",
        "",
        "- [Book order dependency gate](test_results/01_book_order_dependency_gate.md)",
        "- [Prequential order control audit](../../authorial_mechanism_20260620/reports/test_results/120_prequential_order_control_audit.md)",
        "- [Online order frontier controls](../../prequential_and_row0_origin_audit_20260621/reports/test_results/22_online_order_frontier_controls.md)",
        "- [Order frontier promotion gate](../../prequential_and_row0_origin_audit_20260621/reports/test_results/23_order_frontier_promotion_gate.md)",
        "- [Online reparse order control audit](../../authorial_mechanism_20260620/reports/test_results/130_online_reparse_order_control_audit.md)",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"classification": classification, "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
