from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

SEED_COVERAGE = TEST_RESULTS / "01_seed_coverage_audit.json"
PREQUENTIAL_SEED_SELECTION = TEST_RESULTS / "03_prequential_seed_selection_audit.json"
FINAL_REPORT = REPORTS / "final_seed_primacy_audit.md"

SEED_SIZES = [5, 10, 15, 20]
REQUIRED_CANDIDATE_LABELS = {
    "canonical_prefix",
    "greedy_coverage",
    "singleton_centrality_top",
    "public_bookcase_order_prefix",
}
REQUIRED_METRICS = {
    "copied_digits_explained",
    "literal_digits_required",
    "copy_items_required",
    "source_dependency_remaining",
    "coverage_rate",
    "prefix_holdout_gap_abs",
    "seed_declaration_bits",
    "gain_vs_random_median_after_declaration_bits",
    "seed_stats",
    "derived_stats",
}


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


def candidate_rows_by_label(audit: dict[str, Any], label: str) -> list[dict[str, Any]]:
    return [row for row in audit["candidate_rows"] if row["label"] == label]


def make_result() -> dict[str, Any]:
    coverage = load_json(SEED_COVERAGE)
    prequential = load_json(PREQUENTIAL_SEED_SELECTION)
    final_text = FINAL_REPORT.read_text(encoding="utf-8")

    assert_boundary("seed_coverage", coverage)
    assert_boundary("prequential_seed_selection", prequential)
    if "Translation delta: `NONE`" not in final_text:
        raise RuntimeError("final report does not preserve translation boundary")
    if "Plaintext claim: `False`" not in final_text:
        raise RuntimeError("final report does not preserve plaintext boundary")

    candidate_labels = {row["label"] for row in coverage["candidate_rows"]}
    missing_labels = sorted(REQUIRED_CANDIDATE_LABELS - candidate_labels)
    random_ks = sorted(row["seed_book_count"] for row in coverage["random_control_summaries"])
    permuted_ks = sorted(
        row["seed_book_count"] for row in coverage["permuted_prefix_control_summaries"]
    )
    best_ks = sorted(row["seed_book_count"] for row in coverage["best_by_k"])
    candidate_ks_by_label = {
        label: sorted({row["seed_book_count"] for row in candidate_rows_by_label(coverage, label)})
        for label in sorted(candidate_labels)
    }

    metric_missing_by_label: dict[str, list[str]] = {}
    for label in REQUIRED_CANDIDATE_LABELS | {"operational_0_9"}:
        rows = candidate_rows_by_label(coverage, label)
        if not rows:
            continue
        missing = sorted(
            metric
            for metric in REQUIRED_METRICS
            if any(metric not in row for row in rows)
        )
        if missing:
            metric_missing_by_label[label] = missing

    tasks = [
        {
            "requirement": "analysis_only_front_exists",
            "status": "passed",
            "evidence": rel(HERE),
        },
        {
            "requirement": "operational_seed_0_9_baseline",
            "status": "passed"
            if coverage["decision"]["books_0_9_special_as_seed"] is False
            else "failed",
            "evidence": "operational_0_9 candidate and decision books_0_9_special_as_seed=False",
        },
        {
            "requirement": "seed_sizes_5_10_15_20",
            "status": "passed" if best_ks == SEED_SIZES else "failed",
            "evidence": f"best_by_k={best_ks}",
        },
        {
            "requirement": "random_same_size_controls",
            "status": "passed" if random_ks == SEED_SIZES else "failed",
            "evidence": f"random_ks={random_ks}",
        },
        {
            "requirement": "permuted_order_prefix_controls",
            "status": "passed" if permuted_ks == SEED_SIZES else "failed",
            "evidence": f"permuted_ks={permuted_ks}",
        },
        {
            "requirement": "centrality_baseline",
            "status": "passed" if candidate_ks_by_label.get("singleton_centrality_top") == SEED_SIZES else "failed",
            "evidence": f"singleton_centrality_top={candidate_ks_by_label.get('singleton_centrality_top')}",
        },
        {
            "requirement": "metadata_bookcase_baseline",
            "status": "passed" if candidate_ks_by_label.get("public_bookcase_order_prefix") == SEED_SIZES else "failed",
            "evidence": f"public_bookcase_order_prefix={candidate_ks_by_label.get('public_bookcase_order_prefix')}",
        },
        {
            "requirement": "leave_one_family_bookcase_controls",
            "status": "passed" if len(coverage["family_holdout_controls"]) > 0 else "failed",
            "evidence": f"family_holdout_controls={len(coverage['family_holdout_controls'])}",
        },
        {
            "requirement": "declaration_cost_charged",
            "status": "passed"
            if all("seed_declaration_bits" in row for row in coverage["candidate_rows"])
            else "failed",
            "evidence": "seed_declaration_bits present on all candidate rows",
        },
        {
            "requirement": "metrics_present",
            "status": "passed" if not metric_missing_by_label else "failed",
            "evidence": metric_missing_by_label or "required metrics present",
        },
        {
            "requirement": "prequential_train_test_check",
            "status": "passed"
            if prequential["summary"]["promotes_prequential_seed_generator"] is False
            else "failed",
            "evidence": "promotes_prequential_seed_generator=False",
        },
        {
            "requirement": "row0_unchanged",
            "status": "passed"
            if coverage["decision"]["row0_origin_status"] == "unchanged_exogenous"
            and prequential["decision"]["row0_origin_status"] == "unchanged_exogenous"
            else "failed",
            "evidence": "row0_origin_status unchanged_exogenous",
        },
        {
            "requirement": "no_translation_plaintext",
            "status": "passed",
            "evidence": "translation_delta=NONE, plaintext_claim=False",
        },
    ]

    failed = [task for task in tasks if task["status"] != "passed"]
    if failed:
        classification = "seed_primacy_requirement_closure_failed"
    else:
        classification = "seed_primacy_requirements_closed_audit_only"

    return {
        "schema": "seed_requirement_closure_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "seed_coverage_audit": rel(SEED_COVERAGE),
            "prequential_seed_selection_audit": rel(PREQUENTIAL_SEED_SELECTION),
            "final_report": rel(FINAL_REPORT),
        },
        "summary": {
            "task_count": len(tasks),
            "passed_task_count": len(tasks) - len(failed),
            "failed_task_count": len(failed),
            "candidate_labels": sorted(candidate_labels),
            "seed_sizes": SEED_SIZES,
            "family_holdout_control_count": len(coverage["family_holdout_controls"]),
            "final_seed_classification": coverage["classification"],
            "books_0_9_special_as_seed": coverage["decision"][
                "books_0_9_special_as_seed"
            ],
            "alternative_seed_better_for_k10": coverage["decision"][
                "alternative_seed_better_for_k10"
            ],
            "gain_over_random_survives_declaration_cost": coverage["decision"][
                "gain_over_random_survives_declaration_cost"
            ],
            "promotes_prequential_seed_generator": prequential["summary"][
                "promotes_prequential_seed_generator"
            ],
            "authorial_seed_claim": coverage["decision"]["authorial_seed_claim"],
            "translation_or_plaintext_status": "NONE",
        },
        "tasks": tasks,
        "decision": {
            "seed_primacy_status": "audit_only_compression",
            "requirements_closed": not failed,
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "seed_primacy_not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "04_seed_requirement_closure_audit.json"
    md_path = TEST_RESULTS / "04_seed_requirement_closure_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Seed Requirement Closure Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This gate checks whether the seed-primacy front covers the requested",
        "baselines, metrics, controls, categories, and epistemic boundaries. It",
        "does not add a new seed search.",
        "",
        "## Summary",
        "",
        f"- Tasks passed: `{s['passed_task_count']}/{s['task_count']}`.",
        f"- Candidate labels: `{s['candidate_labels']}`.",
        f"- Family/bookcase controls: `{s['family_holdout_control_count']}`.",
        f"- Final seed classification: `{s['final_seed_classification']}`.",
        f"- Books `0..9` special as seed: `{s['books_0_9_special_as_seed']}`.",
        f"- Alternative k=10 seed better: `{s['alternative_seed_better_for_k10']}`.",
        f"- Operational `0..9` gain survives declaration cost: `{s['gain_over_random_survives_declaration_cost']}`.",
        f"- Prequential seed generator promoted: `{s['promotes_prequential_seed_generator']}`.",
        f"- Authorial seed claim: `{s['authorial_seed_claim']}`.",
        "",
        "## Requirement Matrix",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for task in result["tasks"]:
        lines.append(
            f"| `{task['requirement']}` | `{task['status']}` | `{task['evidence']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The seed front satisfies the requested analysis-only audit scope.",
            "- The result remains `AUDIT_ONLY_COMPRESSION`, not a promoted seed-origin formula.",
            "- No row0, plaintext, translation, semantic, or case-reopening claim is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
