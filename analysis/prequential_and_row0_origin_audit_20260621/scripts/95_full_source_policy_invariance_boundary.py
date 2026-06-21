from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE91_SCRIPT = HERE / "scripts" / "91_full_source_exposure_audit.py"
GATE94 = TEST_RESULTS / "94_full_source_all_policy_fivecutoff_probe.json"

TEST_CUTOFFS = [10, 20, 35, 50, 60]
ALL_POLICIES = [
    "earliest_source",
    "latest_source",
    "prefer_previous_end_then_earliest",
]
EPS = 1e-9


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def shape_key(row: dict[str, Any]) -> tuple[int, int, int, int, int]:
    return (
        int(row["op_count"]),
        int(row["copy_items"]),
        int(row["literal_runs"]),
        int(row["copied_digits"]),
        int(row["literal_digits"]),
    )


def summarize_case(cutoff: int, book: int, rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    signatures = {policy: rows[policy]["signature"] for policy in ALL_POLICIES}
    shapes = {policy: shape_key(rows[policy]) for policy in ALL_POLICIES}
    source_sums = {policy: int(rows[policy]["source_sum"]) for policy in ALL_POLICIES}
    parser_bits = {policy: float(rows[policy]["parser_bits"]) for policy in ALL_POLICIES}
    non_earliest = {
        policy: int(rows[policy]["non_earliest_source_count"]) for policy in ALL_POLICIES
    }
    signature_count = len(set(signatures.values()))
    shape_count = len(set(shapes.values()))
    source_sum_span = max(source_sums.values()) - min(source_sums.values())
    parser_bits_span = max(parser_bits.values()) - min(parser_bits.values())
    exact_signature_invariant = signature_count == 1
    shape_invariant = shape_count == 1
    source_sum_invariant = source_sum_span == 0
    return {
        "cutoff": cutoff,
        "book": book,
        "signature_count": signature_count,
        "shape_count": shape_count,
        "source_sum_span": source_sum_span,
        "parser_bits_span": parser_bits_span,
        "exact_signature_invariant": exact_signature_invariant,
        "shape_invariant": shape_invariant,
        "source_sum_invariant": source_sum_invariant,
        "pure_source_choice_variation": shape_invariant and source_sum_span > 0,
        "shape_variation": not shape_invariant,
        "parser_cost_tie": parser_bits_span <= EPS,
        "parser_cost_near_tie_lte_0_1": parser_bits_span <= 0.1 + EPS,
        "signatures": signatures,
        "shape_keys": {policy: list(shapes[policy]) for policy in ALL_POLICIES},
        "source_sums": source_sums,
        "parser_bits": parser_bits,
        "non_earliest_source_counts": non_earliest,
    }


def make_result() -> dict[str, Any]:
    gate94 = load_json(GATE94)
    assert_boundary("full_source_all_policy_fivecutoff_probe", gate94)
    if gate94["classification"] != "full_source_all_policy_fivecutoff_stable":
        raise RuntimeError("gate94 is not stable")

    helper91 = load_module("gate91_for_gate95", GATE91_SCRIPT)
    gate86 = helper91.load_module("gate86_for_gate95", helper91.GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_gate95", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate95", gate82.GATE77_SCRIPT)

    start = time.perf_counter()
    by_case: dict[tuple[int, int], dict[str, dict[str, Any]]] = {}
    for policy in ALL_POLICIES:
        for cutoff in TEST_CUTOFFS:
            for row in helper91.run_cutoff(cutoff, gate77, gate82, policy=policy):
                key = (int(row["cutoff"]), int(row["book"]))
                by_case.setdefault(key, {})[policy] = row

    cases = []
    for cutoff, book in sorted(by_case):
        rows = by_case[(cutoff, book)]
        missing = [policy for policy in ALL_POLICIES if policy not in rows]
        if missing:
            raise RuntimeError({"cutoff": cutoff, "book": book, "missing": missing})
        cases.append(summarize_case(cutoff, book, rows))
    elapsed = time.perf_counter() - start

    exact_invariant = [case for case in cases if case["exact_signature_invariant"]]
    shape_invariant = [case for case in cases if case["shape_invariant"]]
    source_invariant = [case for case in cases if case["source_sum_invariant"]]
    pure_source_variation = [case for case in cases if case["pure_source_choice_variation"]]
    shape_variation = [case for case in cases if case["shape_variation"]]
    cost_tie = [case for case in cases if case["parser_cost_tie"]]
    near_tie = [case for case in cases if case["parser_cost_near_tie_lte_0_1"]]
    max_source_span_case = max(cases, key=lambda case: int(case["source_sum_span"]))
    max_cost_span_case = max(cases, key=lambda case: float(case["parser_bits_span"]))

    source_dependency_removed = len(exact_invariant) == len(cases)
    classification = (
        "full_source_policy_invariant"
        if source_dependency_removed
        else "full_source_policy_stable_but_source_variant"
    )

    return {
        "schema": "full_source_policy_invariance_boundary.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate94_full_source_all_policy_fivecutoff": rel(GATE94),
            "gate91_script": rel(GATE91_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "tested_cutoffs": TEST_CUTOFFS,
            "all_same_length_sources_exposed": True,
            "policies": ALL_POLICIES,
            "compares_exact_policy_signatures": True,
            "compares_policy_operation_shapes": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "case_count": len(cases),
            "exact_signature_invariant_cases": len(exact_invariant),
            "exact_signature_variant_cases": len(cases) - len(exact_invariant),
            "shape_invariant_cases": len(shape_invariant),
            "shape_variant_cases": len(shape_variation),
            "source_sum_invariant_cases": len(source_invariant),
            "source_sum_variant_cases": len(cases) - len(source_invariant),
            "pure_source_choice_variation_cases": len(pure_source_variation),
            "parser_cost_tie_cases": len(cost_tie),
            "parser_cost_near_tie_lte_0_1_cases": len(near_tie),
            "max_source_sum_span": int(max_source_span_case["source_sum_span"]),
            "max_source_sum_span_case": {
                "cutoff": max_source_span_case["cutoff"],
                "book": max_source_span_case["book"],
                "source_sums": max_source_span_case["source_sums"],
            },
            "max_parser_bits_span": float(max_cost_span_case["parser_bits_span"]),
            "max_parser_bits_span_case": {
                "cutoff": max_cost_span_case["cutoff"],
                "book": max_cost_span_case["book"],
                "parser_bits": max_cost_span_case["parser_bits"],
            },
            "source_dependency_removed": source_dependency_removed,
            "interpretation": (
                "Gate 94 shows every policy is stable across five cutoffs. This "
                "boundary audit checks the stronger condition needed to demote "
                "source choice itself: exact source-bearing signatures must be "
                "policy-invariant. They are not."
            ),
        },
        "cases": cases,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "source_tie_policy_robust_but_source_dependency_retained",
            "source_dependency_status": (
                "retained_declared_dependency"
                if not source_dependency_removed
                else "policy_invariant_candidate"
            ),
            "source_rule_status": classification,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "95_full_source_policy_invariance_boundary.json"
    md_path = TEST_RESULTS / "95_full_source_policy_invariance_boundary.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Full Source Policy Invariance Boundary",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 94 showed that all three source tie policies are stable across the",
        "five prequential cutoffs when every same-length source candidate is",
        "exposed. This audit tests the stronger dependency question: whether the",
        "source-bearing exact signatures are invariant across policies.",
        "",
        "## Result",
        "",
        f"- Cases compared: `{s['case_count']}` `(cutoff, book)` pairs.",
        f"- Exact signature invariant cases: `{s['exact_signature_invariant_cases']}/{s['case_count']}`.",
        f"- Exact signature variant cases: `{s['exact_signature_variant_cases']}/{s['case_count']}`.",
        f"- Shape invariant cases: `{s['shape_invariant_cases']}/{s['case_count']}`.",
        f"- Shape variant cases: `{s['shape_variant_cases']}/{s['case_count']}`.",
        f"- Source-sum invariant cases: `{s['source_sum_invariant_cases']}/{s['case_count']}`.",
        f"- Pure source-choice variation cases: `{s['pure_source_choice_variation_cases']}/{s['case_count']}`.",
        f"- Parser-cost ties: `{s['parser_cost_tie_cases']}/{s['case_count']}`.",
        f"- Parser-cost near ties (`<=0.1` bit): `{s['parser_cost_near_tie_lte_0_1_cases']}/{s['case_count']}`.",
        f"- Max source-sum span: `{s['max_source_sum_span']}` at cutoff `{s['max_source_sum_span_case']['cutoff']}`, book `{s['max_source_sum_span_case']['book']}`.",
        f"- Max parser-bit span: `{s['max_parser_bits_span']:.6f}` at cutoff `{s['max_parser_bits_span_case']['cutoff']}`, book `{s['max_parser_bits_span_case']['book']}`.",
        "",
        "## Decision",
        "",
        f"- Source dependency removed: `{s['source_dependency_removed']}`.",
        f"- {s['interpretation']}",
        "- The gate 94 result is therefore parser robustness, not source-choice demotion.",
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
