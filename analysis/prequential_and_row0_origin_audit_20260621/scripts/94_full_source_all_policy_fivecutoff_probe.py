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
GATE93 = TEST_RESULTS / "93_full_source_all_policy_multicutoff_probe.json"

TEST_CUTOFFS = [10, 20, 35, 50, 60]
ALL_POLICIES = [
    "earliest_source",
    "latest_source",
    "prefer_previous_end_then_earliest",
]


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


def compact_book_rows(book_rows: list[dict[str, Any]]) -> dict[str, Any]:
    multi = [row for row in book_rows if int(row["cutoff_count"]) >= 2]
    unstable = [row for row in multi if not row["stable_exact_path"]]
    return {
        "multi_cutoff_book_count": len(multi),
        "multi_cutoff_stable_book_count": len(multi) - len(unstable),
        "multi_cutoff_unstable_book_count": len(unstable),
        "unstable_books": [int(row["book"]) for row in unstable],
        "max_signature_count": max(
            [int(row["signature_count"]) for row in multi] or [0]
        ),
    }


def make_result() -> dict[str, Any]:
    gate93 = load_json(GATE93)
    assert_boundary("full_source_all_policy_multicutoff_probe", gate93)
    if gate93["classification"] != "full_source_all_policy_multicutoff_stable":
        raise RuntimeError("gate93 is not stable")

    helper91 = load_module("gate91_for_gate94", GATE91_SCRIPT)
    helper92 = load_module("gate92_for_gate94", GATE92_SCRIPT)
    gate86 = helper91.load_module("gate86_for_gate94", helper91.GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_gate94", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate94", gate82.GATE77_SCRIPT)

    start = time.perf_counter()
    policy_summaries = []
    for policy in ALL_POLICIES:
        rows = []
        for cutoff in TEST_CUTOFFS:
            rows.extend(helper91.run_cutoff(cutoff, gate77, gate82, policy=policy))
        summary = helper92.summarize_rows(rows)
        summary["policy"] = policy
        summary["source"] = "computed_gate94"
        summary["five_cutoff_stability"] = compact_book_rows(summary["book_rows"])
        policy_summaries.append(summary)
    elapsed = time.perf_counter() - start

    all_roundtrip = all(
        row["roundtrip_book_evaluations"] == row["target_book_evaluations"]
        for row in policy_summaries
    )
    all_raw_positive = all(
        row["raw_positive_book_evaluations"] == row["target_book_evaluations"]
        for row in policy_summaries
    )
    all_five_cutoff_stable = all(
        row["five_cutoff_stability"]["multi_cutoff_stable_book_count"]
        == row["five_cutoff_stability"]["multi_cutoff_book_count"]
        for row in policy_summaries
    )
    any_non_earliest = any(
        row["total_non_earliest_source_count"] > 0 for row in policy_summaries
    )
    total_multi_cutoff_books = sum(
        row["five_cutoff_stability"]["multi_cutoff_book_count"]
        for row in policy_summaries
    )
    total_unstable_books = sum(
        row["five_cutoff_stability"]["multi_cutoff_unstable_book_count"]
        for row in policy_summaries
    )
    classification = (
        "full_source_all_policy_fivecutoff_stable"
        if all_roundtrip
        and all_raw_positive
        and all_five_cutoff_stable
        and any_non_earliest
        else "full_source_all_policy_fivecutoff_mixed"
    )

    return {
        "schema": "full_source_all_policy_fivecutoff_probe.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate93_all_policy_cutoffs_50_60": rel(GATE93),
            "gate91_script": rel(GATE91_SCRIPT),
            "gate92_script": rel(GATE92_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "tested_cutoffs": TEST_CUTOFFS,
            "all_same_length_sources_exposed": True,
            "policies": ALL_POLICIES,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "elapsed_seconds": elapsed,
            "all_roundtrip": all_roundtrip,
            "all_raw_positive": all_raw_positive,
            "all_five_cutoff_multi_book_stable": all_five_cutoff_stable,
            "any_non_earliest_sources_selected": any_non_earliest,
            "policy_count": len(policy_summaries),
            "total_multi_cutoff_books_across_policies": total_multi_cutoff_books,
            "total_unstable_books_across_policies": total_unstable_books,
            "interpretation": (
                "All three source tie policies are tested across the five "
                "prequential cutoffs with every same-length source candidate "
                "exposed. This checks whether the exposed-source parser "
                "robustness from cutoffs 50/60 survives the full cutoff grid."
            ),
        },
        "policy_summaries": policy_summaries,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "full_source_all_policy_fivecutoff_probe_only",
            "source_rule_status": classification,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "94_full_source_all_policy_fivecutoff_probe.json"
    md_path = TEST_RESULTS / "94_full_source_all_policy_fivecutoff_probe.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Full Source All-Policy Five-Cutoff Probe",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 93 compared all source tie policies only on cutoffs `50/60`.",
        "This probe repeats the exposed-source test across the five prequential",
        "cutoffs `10/20/35/50/60`, without changing the parser or cost model.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Multi-cutoff stable books | Roundtrip | Raw-positive | Non-earliest sources | Hidden candidates | Primary bits | Unstable books |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in result["policy_summaries"]:
        stability = row["five_cutoff_stability"]
        lines.append(
            "| {policy} | {stable}/{total} | {rt}/{target} | {raw}/{target} | {non_earliest} | {hidden} | {bits:.6f} | `{unstable}` |".format(
                policy=row["policy"],
                stable=stability["multi_cutoff_stable_book_count"],
                total=stability["multi_cutoff_book_count"],
                rt=row["roundtrip_book_evaluations"],
                raw=row["raw_positive_book_evaluations"],
                target=row["target_book_evaluations"],
                non_earliest=row["total_non_earliest_source_count"],
                hidden=row["hidden_candidate_count"],
                bits=row["total_primary_parser_bits"],
                unstable=stability["unstable_books"],
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- All policies roundtrip: `{s['all_roundtrip']}`.",
            f"- All policies raw-positive: `{s['all_raw_positive']}`.",
            f"- All policies five-cutoff stable: `{s['all_five_cutoff_multi_book_stable']}`.",
            f"- Unstable multi-cutoff books across policies: `{s['total_unstable_books_across_policies']}/{s['total_multi_cutoff_books_across_policies']}`.",
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
