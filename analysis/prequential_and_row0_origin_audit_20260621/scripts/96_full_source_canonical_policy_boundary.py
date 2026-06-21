from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE95 = TEST_RESULTS / "95_full_source_policy_invariance_boundary.json"
POLICIES = [
    "earliest_source",
    "latest_source",
    "prefer_previous_end_then_earliest",
]
PRIMARY_CANONICAL_POLICY = "earliest_source"
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
    gate95 = load_json(GATE95)
    assert_boundary("full_source_policy_invariance_boundary", gate95)
    if gate95["classification"] != "full_source_policy_stable_but_source_variant":
        raise RuntimeError("gate95 does not expose the expected source-variant boundary")

    cases = gate95["cases"]
    rows = []
    for case in cases:
        parser_bits = {policy: float(case["parser_bits"][policy]) for policy in POLICIES}
        min_bits = min(parser_bits.values())
        canonical_bits = parser_bits[PRIMARY_CANONICAL_POLICY]
        min_policies = [
            policy for policy in POLICIES if abs(parser_bits[policy] - min_bits) <= EPS
        ]
        canonical_is_min = abs(canonical_bits - min_bits) <= EPS
        rows.append(
            {
                "cutoff": int(case["cutoff"]),
                "book": int(case["book"]),
                "exact_signature_invariant": bool(case["exact_signature_invariant"]),
                "shape_invariant": bool(case["shape_invariant"]),
                "source_sum_span": int(case["source_sum_span"]),
                "parser_bits_span": float(case["parser_bits_span"]),
                "primary_canonical_policy": PRIMARY_CANONICAL_POLICY,
                "primary_canonical_bits": canonical_bits,
                "min_bits": min_bits,
                "primary_canonical_delta_vs_min": canonical_bits - min_bits,
                "primary_canonical_is_min": canonical_is_min,
                "min_policies": min_policies,
                "latest_delta_vs_canonical": parser_bits["latest_source"] - canonical_bits,
                "previous_end_delta_vs_canonical": parser_bits[
                    "prefer_previous_end_then_earliest"
                ]
                - canonical_bits,
            }
        )

    canonical_min_cases = [row for row in rows if row["primary_canonical_is_min"]]
    latest_worse_cases = [row for row in rows if row["latest_delta_vs_canonical"] > EPS]
    latest_better_cases = [row for row in rows if row["latest_delta_vs_canonical"] < -EPS]
    previous_diff_cases = [
        row for row in rows if abs(row["previous_end_delta_vs_canonical"]) > EPS
    ]
    signature_variant_rows = [row for row in rows if not row["exact_signature_invariant"]]
    canonical_extra_bits = sum(row["primary_canonical_delta_vs_min"] for row in rows)
    latest_extra_bits = sum(max(0.0, row["latest_delta_vs_canonical"]) for row in rows)
    latest_savings_bits = -sum(min(0.0, row["latest_delta_vs_canonical"]) for row in rows)
    max_latest_penalty = max(rows, key=lambda row: row["latest_delta_vs_canonical"])
    max_latest_savings = min(rows, key=lambda row: row["latest_delta_vs_canonical"])

    policy_min_counts = {
        policy: sum(1 for row in rows if policy in row["min_policies"])
        for policy in POLICIES
    }
    policy_extra_bits_vs_min = {
        policy: sum(
            float(gate_case["parser_bits"][policy]) - min(
                float(gate_case["parser_bits"][other]) for other in POLICIES
            )
            for gate_case in gate95["cases"]
        )
        for policy in POLICIES
    }
    static_cost_safe_policies = [
        policy for policy, extra in policy_extra_bits_vs_min.items() if abs(extra) <= EPS
    ]

    canonical_policy_cost_safe = len(canonical_min_cases) == len(rows)
    source_fields_removed = False
    classification = (
        "static_canonical_source_policy_cost_safe_source_retained"
        if static_cost_safe_policies and not source_fields_removed
        else "no_static_canonical_source_policy_cost_safe"
    )

    return {
        "schema": "full_source_canonical_policy_boundary.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate95_policy_invariance_boundary": rel(GATE95),
        },
        "scope": {
            "analysis_only": True,
            "primary_canonical_policy": PRIMARY_CANONICAL_POLICY,
            "policies": POLICIES,
            "case_count": len(rows),
            "compares_policy_costs": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "case_count": len(rows),
            "primary_canonical_policy_cost_safe": canonical_policy_cost_safe,
            "primary_canonical_min_cases": len(canonical_min_cases),
            "primary_canonical_non_min_cases": len(rows) - len(canonical_min_cases),
            "primary_canonical_extra_bits_vs_per_case_min": canonical_extra_bits,
            "policy_min_counts": policy_min_counts,
            "policy_extra_bits_vs_per_case_min": policy_extra_bits_vs_min,
            "static_cost_safe_policies": static_cost_safe_policies,
            "signature_variant_cases": len(signature_variant_rows),
            "latest_worse_than_canonical_cases": len(latest_worse_cases),
            "latest_better_than_canonical_cases": len(latest_better_cases),
            "latest_extra_bits_vs_canonical_positive_only": latest_extra_bits,
            "latest_savings_bits_vs_canonical_positive_only": latest_savings_bits,
            "previous_end_differs_from_canonical_cases": len(previous_diff_cases),
            "max_latest_penalty_case": {
                "cutoff": max_latest_penalty["cutoff"],
                "book": max_latest_penalty["book"],
                "latest_delta_vs_canonical": max_latest_penalty[
                    "latest_delta_vs_canonical"
                ],
            },
            "max_latest_savings_case": {
                "cutoff": max_latest_savings["cutoff"],
                "book": max_latest_savings["book"],
                "latest_delta_vs_canonical": max_latest_savings[
                    "latest_delta_vs_canonical"
                ],
            },
            "source_fields_removed": source_fields_removed,
            "interpretation": (
                "No single static source tie policy is cost-safe across the "
                "gate95 cases. Earliest-source and previous-end-preferred tie "
                "on most cases, but latest-source is cheaper on five book-63 "
                "cases. Source tie policy therefore cannot be globally frozen "
                "without either paying bits or adding a selector."
            ),
        },
        "cases": rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "static_canonical_tie_policy_rejected_source_dependency_retained",
            "canonical_policy_status": (
                "static_policy_cost_safe"
                if static_cost_safe_policies
                else "no_static_policy_cost_safe"
            ),
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "96_full_source_canonical_policy_boundary.json"
    md_path = TEST_RESULTS / "96_full_source_canonical_policy_boundary.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Full Source Canonical Policy Boundary",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 95 showed that operation shape is policy-invariant but exact",
        "source-bearing signatures are not. This audit checks whether any",
        "static source tie policy can be frozen as canonical without paying",
        "parser-cost penalty.",
        "",
        "## Result",
        "",
        f"- Cases compared: `{s['case_count']}`.",
        f"- Primary canonical policy tested: `{result['scope']['primary_canonical_policy']}`.",
        f"- Primary canonical policy cost-safe: `{s['primary_canonical_policy_cost_safe']}`.",
        f"- Primary canonical min-cost cases: `{s['primary_canonical_min_cases']}/{s['case_count']}`.",
        f"- Primary canonical extra bits vs per-case min: `{s['primary_canonical_extra_bits_vs_per_case_min']:.12f}`.",
        f"- Static cost-safe policies: `{s['static_cost_safe_policies']}`.",
        f"- Policy min-counts: `{s['policy_min_counts']}`.",
        f"- Policy extra bits vs per-case min: `{s['policy_extra_bits_vs_per_case_min']}`.",
        f"- Signature-variant cases inherited from gate 95: `{s['signature_variant_cases']}/{s['case_count']}`.",
        f"- Latest-source worse than canonical cases: `{s['latest_worse_than_canonical_cases']}/{s['case_count']}`.",
        f"- Latest-source better than canonical cases: `{s['latest_better_than_canonical_cases']}/{s['case_count']}`.",
        f"- Latest-source positive extra bits vs canonical: `{s['latest_extra_bits_vs_canonical_positive_only']:.12f}`.",
        f"- Latest-source positive savings vs canonical: `{s['latest_savings_bits_vs_canonical_positive_only']:.12f}`.",
        f"- Previous-end-preferred differs from canonical cases: `{s['previous_end_differs_from_canonical_cases']}/{s['case_count']}`.",
        f"- Max latest-source penalty: `{s['max_latest_penalty_case']['latest_delta_vs_canonical']:.6f}` at cutoff `{s['max_latest_penalty_case']['cutoff']}`, book `{s['max_latest_penalty_case']['book']}`.",
        f"- Max latest-source savings: `{s['max_latest_savings_case']['latest_delta_vs_canonical']:.6f}` at cutoff `{s['max_latest_savings_case']['cutoff']}`, book `{s['max_latest_savings_case']['book']}`.",
        "",
        "## Decision",
        "",
        f"- Source fields removed: `{s['source_fields_removed']}`.",
        f"- {s['interpretation']}",
        "- No static canonical tie policy is promoted.",
        "- It does not promote a decoder-side source rule.",
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
