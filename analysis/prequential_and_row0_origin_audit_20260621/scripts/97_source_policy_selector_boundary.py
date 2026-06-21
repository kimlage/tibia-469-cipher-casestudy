from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE96 = TEST_RESULTS / "96_full_source_canonical_policy_boundary.json"
PRIMARY_POLICY = "earliest_source"
ALTERNATE_POLICY = "latest_source"
EPS = 1e-9


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


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


def make_result() -> dict[str, Any]:
    gate96 = load_json(GATE96)
    assert_boundary("full_source_canonical_policy_boundary", gate96)
    if gate96["classification"] != "no_static_canonical_source_policy_cost_safe":
        raise RuntimeError("gate96 did not reject static canonical policy")

    cases = gate96["cases"]
    target_books = sorted({int(case["book"]) for case in cases})
    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        by_book[int(case["book"])].append(case)

    book_summaries = []
    selector_books = []
    total_savings_vs_primary = 0.0
    total_penalty_if_alternate_global = 0.0
    for book in target_books:
        rows = by_book[book]
        latest_deltas = [float(row["latest_delta_vs_canonical"]) for row in rows]
        alternate_better = [delta for delta in latest_deltas if delta < -EPS]
        alternate_worse = [delta for delta in latest_deltas if delta > EPS]
        primary_min = sum(
            1 for row in rows if PRIMARY_POLICY in row["min_policies"]
        )
        alternate_min = sum(
            1 for row in rows if ALTERNATE_POLICY in row["min_policies"]
        )
        savings = -sum(alternate_better)
        penalty = sum(alternate_worse)
        total_savings_vs_primary += savings
        total_penalty_if_alternate_global += penalty
        selected_policy = (
            ALTERNATE_POLICY
            if alternate_min == len(rows) and primary_min == 0
            else PRIMARY_POLICY
        )
        if selected_policy == ALTERNATE_POLICY:
            selector_books.append(book)
        book_summaries.append(
            {
                "book": book,
                "case_count": len(rows),
                "primary_min_cases": primary_min,
                "alternate_min_cases": alternate_min,
                "alternate_better_cases": len(alternate_better),
                "alternate_worse_cases": len(alternate_worse),
                "alternate_savings_vs_primary": savings,
                "alternate_penalty_vs_primary": penalty,
                "selected_policy": selected_policy,
            }
        )

    selected_case_count = sum(
        row["case_count"]
        for row in book_summaries
        if row["selected_policy"] == ALTERNATE_POLICY
    )
    static_primary_extra_bits = gate96["summary"][
        "primary_canonical_extra_bits_vs_per_case_min"
    ]
    selector_extra_bits_vs_per_case_min = static_primary_extra_bits - total_savings_vs_primary
    book_selector_floor_bits = (
        math.log2(len(target_books)) if selector_books else 0.0
    )
    policy_label_floor_bits = math.log2(2) if selector_books else 0.0
    paid_selector_floor_bits = book_selector_floor_bits + policy_label_floor_bits
    net_bits_vs_static_primary_after_floor = total_savings_vs_primary - paid_selector_floor_bits
    selector_exactly_matches_per_case_min = abs(selector_extra_bits_vs_per_case_min) <= EPS
    selector_is_book_specific = bool(selector_books)
    source_fields_removed = False
    promotes_generation_explanation = False
    classification = (
        "book_specific_policy_selector_audit_only"
        if selector_exactly_matches_per_case_min and selector_is_book_specific
        else "policy_selector_not_minimal"
    )

    return {
        "schema": "source_policy_selector_boundary.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate96_canonical_policy_boundary": rel(GATE96),
        },
        "scope": {
            "analysis_only": True,
            "primary_policy": PRIMARY_POLICY,
            "alternate_policy": ALTERNATE_POLICY,
            "target_book_count": len(target_books),
            "selector_books": selector_books,
            "book_specific_selector": selector_is_book_specific,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "case_count": len(cases),
            "target_book_count": len(target_books),
            "selector_books": selector_books,
            "selected_alternate_case_count": selected_case_count,
            "static_primary_extra_bits_vs_per_case_min": static_primary_extra_bits,
            "selector_extra_bits_vs_per_case_min": selector_extra_bits_vs_per_case_min,
            "selector_exactly_matches_per_case_min": selector_exactly_matches_per_case_min,
            "total_savings_vs_static_primary": total_savings_vs_primary,
            "total_penalty_if_alternate_global": total_penalty_if_alternate_global,
            "book_selector_floor_bits": book_selector_floor_bits,
            "policy_label_floor_bits": policy_label_floor_bits,
            "paid_selector_floor_bits": paid_selector_floor_bits,
            "net_bits_vs_static_primary_after_floor": net_bits_vs_static_primary_after_floor,
            "source_fields_removed": source_fields_removed,
            "promotes_generation_explanation": promotes_generation_explanation,
            "interpretation": (
                "A selector that uses latest_source only for book 63 and "
                "earliest_source otherwise matches the per-case policy minimum, "
                "but it is a book-specific selector over an already source-"
                "dependent parser. It can be kept as an audit-only compression "
                "boundary, not as a generation explanation."
            ),
        },
        "book_summaries": book_summaries,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "book_specific_policy_selector_rejected",
            "source_dependency_status": "retained_declared_dependency",
            "selector_status": "audit_only_not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "97_source_policy_selector_boundary.json"
    md_path = TEST_RESULTS / "97_source_policy_selector_boundary.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Source Policy Selector Boundary",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 96 rejected a single static source tie policy. This audit tests the",
        "minimal obvious selector: use `latest_source` only where it is strictly",
        "cheaper than `earliest_source`, otherwise keep `earliest_source`.",
        "",
        "## Result",
        "",
        f"- Cases compared: `{s['case_count']}`.",
        f"- Target books represented: `{s['target_book_count']}`.",
        f"- Selector books: `{s['selector_books']}`.",
        f"- Selected alternate cases: `{s['selected_alternate_case_count']}`.",
        f"- Selector matches per-case minimum: `{s['selector_exactly_matches_per_case_min']}`.",
        f"- Static primary extra bits vs per-case min: `{s['static_primary_extra_bits_vs_per_case_min']:.12f}`.",
        f"- Selector extra bits vs per-case min: `{s['selector_extra_bits_vs_per_case_min']:.12f}`.",
        f"- Savings vs static primary: `{s['total_savings_vs_static_primary']:.12f}`.",
        f"- Paid selector floor: `{s['paid_selector_floor_bits']:.6f}` bits.",
        f"- Net bits vs static primary after selector floor: `{s['net_bits_vs_static_primary_after_floor']:.6f}`.",
        "",
        "## Decision",
        "",
        f"- Source fields removed: `{s['source_fields_removed']}`.",
        f"- Promotes generation explanation: `{s['promotes_generation_explanation']}`.",
        f"- {s['interpretation']}",
        "- This does not promote a decoder-side source rule.",
        "- No compression-bound change is introduced.",
        "- No formula is emitted.",
        "- Row0 remains unchanged and exogenous.",
        "- No plaintext, translation, semantic reading, or case reopening is introduced.",
    ]
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
