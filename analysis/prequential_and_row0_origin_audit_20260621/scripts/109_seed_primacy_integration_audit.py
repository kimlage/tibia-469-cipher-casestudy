from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

SEED_FRONT = ROOT / "analysis" / "seed_primacy_audit_20260621"
SEED_REPORT = SEED_FRONT / "reports" / "final_seed_primacy_audit.md"
SEED_COVERAGE = SEED_FRONT / "reports" / "test_results" / "01_seed_coverage_audit.json"
SEED_PREQUENTIAL = (
    SEED_FRONT / "reports" / "test_results" / "03_prequential_seed_selection_audit.json"
)
ROW0_REFRESH = TEST_RESULTS / "108_recent_gates_row0_compatibility_refresh.json"
OUT_STEM = "109_seed_primacy_integration_audit"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_no_semantics(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("decision", {}).get("translation_or_plaintext_status") != "NONE":
        raise RuntimeError(f"{name} changed translation/plaintext status")


def make_result() -> dict[str, Any]:
    coverage = load_json(SEED_COVERAGE)
    prequential = load_json(SEED_PREQUENTIAL)
    row0_refresh = load_json(ROW0_REFRESH)
    final_report = SEED_REPORT.read_text(encoding="utf-8")

    for name, data in [
        ("seed_coverage", coverage),
        ("seed_prequential", prequential),
        ("row0_refresh", row0_refresh),
    ]:
        assert_no_semantics(name, data)

    if "Classification: `AUDIT_ONLY_COMPRESSION`" not in final_report:
        raise RuntimeError("final seed report classification changed")
    if "Translation delta: `NONE`" not in final_report:
        raise RuntimeError("final seed report translation boundary changed")
    if coverage["classification"] != "AUDIT_ONLY_COMPRESSION":
        raise RuntimeError("seed coverage classification changed")
    if prequential["classification"] != "prequential_seed_selection_not_promoted":
        raise RuntimeError("prequential seed classification changed")
    if coverage["decision"]["books_0_9_special_as_seed"] is not False:
        raise RuntimeError("operational books 0-9 became promoted seeds")
    if coverage["decision"]["gain_over_random_survives_declaration_cost"] is not False:
        raise RuntimeError("operational seed gain unexpectedly survived controls")
    if prequential["summary"]["promotes_prequential_seed_generator"] is not False:
        raise RuntimeError("prequential seed generator promoted unexpectedly")
    if coverage["decision"]["row0_origin_status"] != "unchanged_exogenous":
        raise RuntimeError("seed coverage changed row0 status")
    if prequential["decision"]["row0_origin_status"] != "unchanged_exogenous":
        raise RuntimeError("prequential seed changed row0 status")
    if row0_refresh["summary"]["row0_changed"] is not False:
        raise RuntimeError("row0 refresh changed row0")

    operational = coverage["summary"]["operational_0_9"]
    best_k10 = coverage["summary"]["best_k10_candidate"]
    preq_summary = prequential["summary"]

    return {
        "schema": "seed_primacy_integration_audit.v1",
        "classification": "seed_primacy_integrated_audit_only_compression",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "final_seed_report": rel(SEED_REPORT),
            "seed_coverage_audit": rel(SEED_COVERAGE),
            "prequential_seed_selection_audit": rel(SEED_PREQUENTIAL),
            "row0_refresh": rel(ROW0_REFRESH),
        },
        "summary": {
            "seed_front_classification": coverage["classification"],
            "final_report_classification": "AUDIT_ONLY_COMPRESSION",
            "current_compression_bound_bits": 8154.676268216349,
            "row0_changed": False,
            "row0_origin_status": "unchanged_exogenous",
            "operational_0_9": {
                "seed_books": operational["seed_books"],
                "copied_digits_explained": operational["copied_digits_explained"],
                "target_digits": operational["target_digits"],
                "coverage_rate": operational["coverage_rate"],
                "random_control_percentile_copied_digits": operational[
                    "random_control_percentile_copied_digits"
                ],
                "gain_vs_random_median_after_declaration_bits": operational[
                    "gain_vs_random_median_after_declaration_bits"
                ],
                "special_as_seed": coverage["decision"]["books_0_9_special_as_seed"],
            },
            "best_k10_posthoc": {
                "seed_books": best_k10["seed_books"],
                "copied_digits_explained": best_k10["copied_digits_explained"],
                "target_digits": best_k10["target_digits"],
                "coverage_rate": best_k10["coverage_rate"],
                "search_class": best_k10["search_class"],
                "random_control_percentile_copied_digits": best_k10[
                    "random_control_percentile_copied_digits"
                ],
            },
            "prequential_seed_selection": {
                "evaluated_cells": preq_summary["evaluated_cells"],
                "train_greedy_beats_random_median_cells": preq_summary[
                    "train_greedy_beats_random_median_cells"
                ],
                "train_greedy_beats_random_p95_cells": preq_summary[
                    "train_greedy_beats_random_p95_cells"
                ],
                "operational_beats_random_median_cells": preq_summary[
                    "operational_beats_random_median_cells"
                ],
                "mean_train_greedy_oracle_gap_coverage": preq_summary[
                    "mean_train_greedy_oracle_gap_coverage"
                ],
                "max_train_greedy_oracle_gap_coverage": preq_summary[
                    "max_train_greedy_oracle_gap_coverage"
                ],
                "promotes_prequential_seed_generator": preq_summary[
                    "promotes_prequential_seed_generator"
                ],
            },
            "criteria": {
                "promotes_authorial_seed_claim": False,
                "promotes_generation_formula": False,
                "changes_compression_bound": False,
                "predicts_or_derives_row0": False,
                "adds_plaintext_or_translation": False,
                "identifies_compression_core_posthoc": True,
            },
            "decision_links": {
                "coverage_generation_explanation_status": coverage["decision"][
                    "generation_explanation_status"
                ],
                "prequential_generation_explanation_status": prequential["decision"][
                    "generation_explanation_status"
                ],
                "authorial_seed_claim": coverage["decision"]["authorial_seed_claim"],
                "mechanical_primary_core_signal": coverage["decision"][
                    "mechanical_primary_core_signal"
                ],
            },
        },
        "taxonomy": {
            "PROMOTED_MECHANICAL_SEED_CLUE": [],
            "WEAK_SEED_CLUE": [],
            "REJECTED_SEED_HYPOTHESIS": [
                {
                    "name": "operational_books_0_9_seed_primacy",
                    "evidence": "8664 copied digits is below the random k=10 median 9005 and percentile 0.21",
                }
            ],
            "AUDIT_ONLY_COMPRESSION": [
                {
                    "name": "posthoc_high_coverage_seed_sets",
                    "evidence": "best k=10 posthoc greedy seed covers 9734 digits but is selected after seeing the corpus",
                },
                {
                    "name": "prequential_train_greedy_seed_selection",
                    "evidence": "prefix-trained seeds beat random median in 7/7 cells and p95 in 6/7, but do not close suffix-oracle gap",
                },
            ],
            "BLOCKED_NEEDS_EXTERNAL_SOURCE": [
                {
                    "name": "authorial_seed_claim",
                    "evidence": "no external CipSoft/in-game source identifies a seed set",
                }
            ],
        },
        "decision": {
            "seed_primacy_status": "audit_only_compression",
            "operational_0_9_status": "not_mechanically_privileged_seed",
            "prequential_seed_status": "partial_predictive_signal_not_promoted",
            "row0_origin_status": "unchanged_exogenous",
            "compression_bound_status": "unchanged_8154_676268",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    s = result["summary"]
    operational = s["operational_0_9"]
    best_k10 = s["best_k10_posthoc"]
    preq = s["prequential_seed_selection"]
    lines = [
        "# Seed Primacy Integration Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This bridge integrates the final seed-primacy front into the main",
        "prequential/row0 audit. It treats the seed work as a narrow exact-copy",
        "coverage test, not as translation, plaintext, authorial intent, or row0",
        "origin evidence.",
        "",
        "## Decision",
        "",
        "- Seed front status: `AUDIT_ONLY_COMPRESSION`.",
        "- Operational books `0..9` are not mechanically privileged seeds under the tested controls.",
        "- Posthoc high-coverage seed sets are compression clues only.",
        "- Prefix-trained seed selection has partial predictive signal, but is not promoted.",
        "- `row0 unchanged`; compression bound remains `8154.676268` bits.",
        "",
        "## Operational Seed Check",
        "",
        "| Seed set | Copied digits | Target digits | Coverage | Random percentile | Gain vs random median after declaration | Status |",
        "|---|---:|---:|---:|---:|---:|---|",
        f"| `0..9` | `{operational['copied_digits_explained']}` | `{operational['target_digits']}` | `{operational['coverage_rate']:.6f}` | `{operational['random_control_percentile_copied_digits']:.2f}` | `{operational['gain_vs_random_median_after_declaration_bits']:.3f}` | `not_promoted` |",
        "",
        "## Posthoc Core",
        "",
        f"- Best k=10 posthoc greedy seed: `{best_k10['seed_books']}`.",
        f"- Copied digits: `{best_k10['copied_digits_explained']}` / `{best_k10['target_digits']}`.",
        f"- Coverage: `{best_k10['coverage_rate']:.6f}`.",
        f"- Search class: `{best_k10['search_class']}`.",
        "- Boundary: selected after seeing the corpus, so it is not an authorial seed claim.",
        "",
        "## Prequential Check",
        "",
        f"- Evaluated prefix/k cells: `{preq['evaluated_cells']}`.",
        f"- Train-greedy beats random median: `{preq['train_greedy_beats_random_median_cells']}/{preq['evaluated_cells']}`.",
        f"- Train-greedy beats random p95: `{preq['train_greedy_beats_random_p95_cells']}/{preq['evaluated_cells']}`.",
        f"- Operational prefix beats random median: `{preq['operational_beats_random_median_cells']}/{preq['evaluated_cells']}`.",
        f"- Mean train-greedy vs suffix-oracle gap: `{preq['mean_train_greedy_oracle_gap_coverage']:.6f}`.",
        f"- Max train-greedy vs suffix-oracle gap: `{preq['max_train_greedy_oracle_gap_coverage']:.6f}`.",
        f"- Promotes prequential seed generator: `{preq['promotes_prequential_seed_generator']}`.",
        "",
        "## Taxonomy",
        "",
        "| Bucket | Result |",
        "|---|---|",
        "| `PROMOTED_MECHANICAL_SEED_CLUE` | none |",
        "| `WEAK_SEED_CLUE` | none |",
        "| `REJECTED_SEED_HYPOTHESIS` | operational `0..9` seed primacy |",
        "| `AUDIT_ONLY_COMPRESSION` | posthoc high-coverage cores; partial prequential seed-selection signal |",
        "| `BLOCKED_NEEDS_EXTERNAL_SOURCE` | authorial seed claim |",
        "",
        "## Boundary",
        "",
        "This integration adds no plaintext, translation, semantic reading, row0",
        "origin formula, or new compression bound. Better exact-copy seed coverage",
        "is recorded as corpus redundancy evidence only.",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
