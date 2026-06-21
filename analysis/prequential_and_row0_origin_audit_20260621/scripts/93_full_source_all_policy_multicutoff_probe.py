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
GATE92_SCRIPT = HERE / "scripts" / "92_full_source_latest_multicutoff_probe.py"
GATE92 = TEST_RESULTS / "92_full_source_latest_multicutoff_probe.json"

TEST_CUTOFFS = [50, 60]
COMPUTED_POLICIES = ["earliest_source", "prefer_previous_end_then_earliest"]
ALL_POLICIES = ["earliest_source", "latest_source", "prefer_previous_end_then_earliest"]


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


def latest_summary_from_gate92(gate92: dict[str, Any]) -> dict[str, Any]:
    s = gate92["summary"]
    return {
        "policy": "latest_source",
        "target_book_evaluations": s["target_book_evaluations"],
        "roundtrip_book_evaluations": s["roundtrip_book_evaluations"],
        "raw_positive_book_evaluations": s["raw_positive_book_evaluations"],
        "book_count": s["book_count"],
        "multi_cutoff_book_count": s["multi_cutoff_book_count"],
        "multi_cutoff_stable_book_count": s["multi_cutoff_stable_book_count"],
        "multi_cutoff_unstable_book_count": s["multi_cutoff_unstable_book_count"],
        "unstable_books": s["unstable_books"],
        "total_primary_parser_bits": s["total_primary_parser_bits"],
        "total_non_earliest_source_count": s["total_non_earliest_source_count"],
        "total_copy_items": s["total_copy_items"],
        "total_literal_digits": s["total_literal_digits"],
        "hidden_candidate_count": s["hidden_candidate_count"],
        "positions_with_hidden_sources": s["positions_with_hidden_sources"],
        "max_candidates_at_position": s["max_candidates_at_position"],
        "book_rows": s["book_rows"],
        "source": "gate92_reused",
    }


def make_result() -> dict[str, Any]:
    gate92 = load_json(GATE92)
    assert_boundary("full_source_latest_multicutoff_probe", gate92)
    if gate92["classification"] != "full_source_latest_multicutoff_stable":
        raise RuntimeError("gate92 is not stable")

    helper91 = load_module("gate91_for_gate93", GATE91_SCRIPT)
    helper92 = load_module("gate92_for_gate93", GATE92_SCRIPT)
    gate86 = helper91.load_module("gate86_for_gate93", helper91.GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_gate93", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate93", gate82.GATE77_SCRIPT)

    start = time.perf_counter()
    policy_summaries = [latest_summary_from_gate92(gate92)]
    for policy in COMPUTED_POLICIES:
        rows = []
        for cutoff in TEST_CUTOFFS:
            rows.extend(helper91.run_cutoff(cutoff, gate77, gate82, policy=policy))
        row = helper92.summarize_rows(rows)
        row["policy"] = policy
        row["source"] = "computed_gate93"
        policy_summaries.append(row)
    elapsed = time.perf_counter() - start
    policy_summaries = sorted(policy_summaries, key=lambda row: ALL_POLICIES.index(row["policy"]))

    all_roundtrip = all(
        row["roundtrip_book_evaluations"] == row["target_book_evaluations"]
        for row in policy_summaries
    )
    all_raw_positive = all(
        row["raw_positive_book_evaluations"] == row["target_book_evaluations"]
        for row in policy_summaries
    )
    all_multi_stable = all(
        row["multi_cutoff_stable_book_count"] == row["multi_cutoff_book_count"]
        for row in policy_summaries
    )
    any_non_earliest = any(
        row["total_non_earliest_source_count"] > 0 for row in policy_summaries
    )
    classification = (
        "full_source_all_policy_multicutoff_stable"
        if all_roundtrip and all_raw_positive and all_multi_stable and any_non_earliest
        else "full_source_all_policy_multicutoff_mixed"
    )

    return {
        "schema": "full_source_all_policy_multicutoff_probe.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate92_latest_policy": rel(GATE92),
            "gate91_script": rel(GATE91_SCRIPT),
            "gate92_script": rel(GATE92_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "tested_cutoffs": TEST_CUTOFFS,
            "all_same_length_sources_exposed": True,
            "policies": ALL_POLICIES,
            "latest_source_reused_from_gate92": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "all_roundtrip": all_roundtrip,
            "all_raw_positive": all_raw_positive,
            "all_multi_cutoff_books_stable": all_multi_stable,
            "any_non_earliest_sources_selected": any_non_earliest,
            "policy_count": len(policy_summaries),
            "interpretation": (
                "All three source tie policies are compared on cutoffs 50 and 60 "
                "with every same-length source candidate exposed. This checks "
                "whether the partial multi-cutoff stability from gate 92 depends "
                "on the latest-source tie policy."
            ),
        },
        "policy_summaries": policy_summaries,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "full_source_all_policy_multicutoff_probe_only",
            "source_rule_status": classification,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "93_full_source_all_policy_multicutoff_probe.json"
    md_path = TEST_RESULTS / "93_full_source_all_policy_multicutoff_probe.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Full Source All-Policy Multi-Cutoff Probe",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 92 tested the most disruptive `latest_source` policy on cutoffs",
        "`50/60`. This probe adds `earliest_source` and",
        "`prefer_previous_end_then_earliest` on the same exposed-source frontier,",
        "reusing the validated latest-source row from gate 92.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Stable books | Roundtrip | Raw-positive | Non-earliest sources | Hidden candidates | Primary bits | Source |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["policy_summaries"]:
        lines.append(
            "| {policy} | {multi_cutoff_stable_book_count}/{multi_cutoff_book_count} | {roundtrip_book_evaluations}/{target_book_evaluations} | {raw_positive_book_evaluations}/{target_book_evaluations} | {total_non_earliest_source_count} | {hidden_candidate_count} | {total_primary_parser_bits:.6f} | {source} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- All policies roundtrip: `{s['all_roundtrip']}`.",
            f"- All policies raw-positive: `{s['all_raw_positive']}`.",
            f"- All policies multi-cutoff stable: `{s['all_multi_cutoff_books_stable']}`.",
            f"- Any non-earliest sources selected: `{s['any_non_earliest_sources_selected']}`.",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No formula is emitted.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
