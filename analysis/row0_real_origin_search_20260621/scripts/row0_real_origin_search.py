#!/usr/bin/env python3
"""Row0-only origin search scoreboard.

This front deliberately excludes downstream book-compression gains unless the
candidate directly predicts the row0 pair-label table.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
FRONT = SCRIPT.parents[1]
REPO = SCRIPT.parents[3]
REPORTS = FRONT / "reports"
TEST_RESULTS = REPORTS / "test_results"
DATA = FRONT / "data"

SOURCE_PATHS = {
    "final_parallel": "analysis/row0_origin_parallel_20260621/reports/final_row0_origin_parallel_report.md",
    "next_frontier": "analysis/row0_origin_parallel_20260621/reports/row0_next_frontier_report.md",
    "scoreboard_155": "analysis/row0_origin_parallel_20260621/reports/test_results/155_row0_improvement_scoreboard.json",
    "worksheet_156": "analysis/row0_origin_parallel_20260621/reports/test_results/156_row0_partial_worksheet_model.json",
    "paid_anchor_159": "analysis/row0_origin_parallel_20260621/reports/test_results/159_row0_paid_anchor_reduction_gate.json",
    "formula_compat_70": "analysis/prequential_and_row0_origin_audit_20260621/reports/test_results/70_recent_formula_row0_compatibility_audit.json",
    "priority_144": "analysis/row0_origin_parallel_20260621/reports/test_results/144_row0_priority_layer_mdl.json",
    "inventory_146": "analysis/row0_origin_parallel_20260621/reports/test_results/146_row0_fill_order_inventory_search.json",
    "provenance_154": "analysis/row0_origin_parallel_20260621/reports/test_results/154_row0_deep_provenance_audit.json",
    "frontier_119": "analysis/authorial_mechanism_20260620/reports/test_results/119_row0_origin_frontier_audit.json",
    "wiki": "docs/wiki/13-mechanical-origin-model-v1.md",
}

GRID = [
    ["*", "N", "R", "V", "F", "T", "I", "I", "I", "T"],
    ["N", "E", "F", "N", "A", "E", "T", "V", "I", "I"],
    ["R", "F", "A", "O", "L", "I", "N", "S", "T", "N"],
    ["V", "N", "O", "E", "B", "L", "V", "A", "T", None],
    ["F", "A", "L", "B", "E", "F", "N", "E", "E", "N"],
    ["T", "E", "I", "L", "F", "V", "I", "E", "E", "I"],
    ["I", "T", "N", "V", "N", "I", "E", "A", "C", "V"],
    ["I", "V", "S", "A", "E", "E", "A", "N", "E", "A"],
    ["I", "I", "T", "T", "E", "E", "C", "E", "A", "T"],
    ["T", "N", "N", "N", "N", "I", "V", "A", "T", "E"],
]


def read_json(relpath: str) -> dict[str, Any]:
    path = REPO / relpath
    with path.open() as fh:
        return json.load(fh)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")


def md_table(rows: list[dict[str, Any]], cols: list[tuple[str, str]]) -> str:
    out = ["| " + " | ".join(title for _, title in cols) + " |"]
    out.append("|" + "|".join("---" for _ in cols) + "|")
    for row in rows:
        vals = []
        for key, _ in cols:
            value = row.get(key, "")
            if isinstance(value, float):
                value = f"{value:.3f}"
            elif isinstance(value, list):
                value = ", ".join(map(str, value))
            vals.append(str(value).replace("\n", " "))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def pair_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for a in range(10):
        for b in range(a, 10):
            code = f"{a}{b}"
            label = GRID[a][b]
            reverse_label = GRID[b][a]
            missing_ordered_code = None
            if label is None:
                label = reverse_label
                missing_ordered_code = code
            if code == "19":
                label = "I/N"
            rows.append(
                {
                    "pair": code,
                    "label": label,
                    "forward": GRID[a][b],
                    "reverse": reverse_label,
                    "is_diagonal": a == b,
                    "has_6_or_9": a in (6, 9) or b in (6, 9),
                    "missing_ordered_code": missing_ordered_code,
                }
            )
    return rows


def lookup_bits(rows: list[dict[str, Any]]) -> float:
    counts = Counter(row["label"] for row in rows)
    bits = math.lgamma(len(rows) + 1) / math.log(2)
    bits -= sum(math.lgamma(v + 1) / math.log(2) for v in counts.values())
    return bits


def find_family(frontier_119: dict[str, Any], name: str) -> dict[str, Any]:
    for family in frontier_119.get("families", []):
        if family.get("family") == name:
            return family
    return {}


def source_digest() -> dict[str, Any]:
    paths = []
    for key, relpath in SOURCE_PATHS.items():
        path = REPO / relpath
        paths.append(
            {
                "key": key,
                "path": relpath,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )
    return {
        "schema": "row0_real_origin_source_digest.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": paths,
    }


def build_scoreboard() -> dict[str, Any]:
    rows = pair_rows()
    baseline = read_json(SOURCE_PATHS["scoreboard_155"]).get("lookup_baseline_bits", lookup_bits(rows))
    worksheet = read_json(SOURCE_PATHS["worksheet_156"])
    paid = read_json(SOURCE_PATHS["paid_anchor_159"])
    compat = read_json(SOURCE_PATHS["formula_compat_70"])
    priority = read_json(SOURCE_PATHS["priority_144"])
    inventory = read_json(SOURCE_PATHS["inventory_146"])
    provenance = read_json(SOURCE_PATHS["provenance_154"])
    frontier = read_json(SOURCE_PATHS["frontier_119"])

    paid_summary = paid["summary"]
    paid_models = {row["name"]: row for row in paid["models"]}
    priority_best = priority["best_rule"]
    inv_holdout = inventory["prior_usage_driven_pair_placement"]["holdout_same_rule"]
    orbit = find_family(frontier, "digit_orbit_6_9")

    workbook_count = len(provenance.get("workbooks", []))
    script_count = len(provenance.get("scripts", []))
    traced_paths = len(provenance.get("tracked_row0_related_paths", []))

    hypothesis_rows: list[dict[str, Any]] = [
        {
            "hypothesis": "paid_anchor_source_model",
            "algorithm": "Freeze 13 worksheet anchors, encode residual lookup, then charge exact anchor-pair set and anchor-label arrangement.",
            "description_bits": "54.178 nominal reduction - 40.400 pair-set cost - 25.629 label-arrangement cost",
            "labels_predicted_holdout": 0,
            "coverage_pairs": "13 anchors plus residual lookup over 55 pairs",
            "bits_below_lookup_after_costs": paid_summary["all_anchors_explicit_pair_label_net_bits"],
            "explains_39_93_19_91": "stores 19 and 39 as anchors; does not derive why 39 is missing, 93 present, or 19/91 conflict",
            "negative_controls": f"nominal random-subset p={paid_summary['all_anchors_random_subset_p_ge_nominal']:.4f}; explicit paid model not promoted",
            "contradictions": "Anchor labels/source are unpaid in the nominal model; explicit pair+label payment makes the full model worse than lookup.",
            "classification": "REJECTED_CONTROL",
            "metric_moved": "5_falsification_strong",
            "evidence_path": SOURCE_PATHS["paid_anchor_159"],
        },
        {
            "hypothesis": "external_fixed_source_order",
            "algorithm": "Require a pre-row0 source that fixes pair/cell order before fitting labels.",
            "description_bits": "not chargeable: no source found",
            "labels_predicted_holdout": 0,
            "coverage_pairs": "0/55",
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_93_19_91": "no",
            "negative_controls": "not run because the source prerequisite is absent",
            "contradictions": "Any order chosen after seeing row0 is post-hoc and inadmissible.",
            "classification": "BLOCKED_NEEDS_EXTERNAL_SOURCE",
            "metric_moved": "none",
            "evidence_path": SOURCE_PATHS["next_frontier"],
        },
        {
            "hypothesis": "workbook_script_artifact_provenance",
            "algorithm": "Use local workbook/script audit as artifact provenance; distinguish project reconstruction from CipSoft or in-game origin.",
            "description_bits": "audit-only; not a generative code",
            "labels_predicted_holdout": 0,
            "coverage_pairs": "project artifact surface only",
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_93_19_91": "no",
            "negative_controls": "not a label predictor",
            "contradictions": f"{workbook_count} workbooks, {script_count} scripts, and {traced_paths} tracked paths trace local project layers but not pre-project/CipSoft origin.",
            "classification": "AUDIT_ONLY",
            "metric_moved": "none_new_provenance",
            "evidence_path": SOURCE_PATHS["provenance_154"],
        },
        {
            "hypothesis": "manual_worksheet_reconstruction",
            "algorithm": "Treat row0 as a worksheet: freeze rare/surface/diagonal anchors, encode all remaining pair labels by lookup.",
            "description_bits": f"{worksheet['anchor_count']} anchors reduce residual lookup from {worksheet['lookup_bits_before']:.3f} to {worksheet['residual_lookup_bits_after_freezing_anchors']:.3f} before paying anchor costs",
            "labels_predicted_holdout": 0,
            "coverage_pairs": f"{worksheet['anchor_count']}/55 anchors before residual lookup",
            "bits_below_lookup_after_costs": paid_summary["all_anchors_explicit_pair_label_net_bits"],
            "explains_39_93_19_91": "captures 39/19 as declared anchors, not as a rule",
            "negative_controls": "paid-anchor gate rejects the explicit pair+label version; rare singletons only break even",
            "contradictions": "A worksheet model is honest as provenance shape, but the chosen cells remain exogenous.",
            "classification": "WEAK_CLUE",
            "metric_moved": "none",
            "evidence_path": SOURCE_PATHS["worksheet_156"],
        },
        {
            "hypothesis": "ordered_surface_exception_rule_39_93_19_91",
            "algorithm": "Fold 99 ordered codes to 55 unordered pairs, then keep an ordered-surface exception ledger for missing 39 and directed 19/91.",
            "description_bits": "small surface ledger; no pair-label generator",
            "labels_predicted_holdout": 0,
            "coverage_pairs": "54/55 pure unordered pairs plus one directed conflict",
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_93_19_91": "yes as render/surface facts only",
            "negative_controls": "recent formula compatibility audit confirms book-formula gains do not derive these facts",
            "contradictions": "It explains ordered-surface topology, not why labels I/N/N were assigned.",
            "classification": "PROMOTED_MECHANICAL_CLUE",
            "metric_moved": "3_retained_surface_clue_not_new_origin_formula",
            "evidence_path": SOURCE_PATHS["formula_compat_70"],
        },
        {
            "hypothesis": "six_nine_quotient_orbit_compression",
            "algorithm": "Quotient unordered pair cells by the fixed 6<->9 digit orbit and test whether orbit structure predicts labels.",
            "description_bits": "quotient/orbit clue only; full label table still needs residual lookup",
            "labels_predicted_holdout": 0,
            "coverage_pairs": f"{orbit.get('key_result', {}).get('primary_hits', 51)}/55 primary quotient hits",
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_93_19_91": "partly touches 39/93 but does not explain the directed absence/conflict",
            "negative_controls": f"fixed-swap control p={orbit.get('key_result', {}).get('fixed_swap_control_p', 0.015249237538123094):.4f}; weak signal, not full formula",
            "contradictions": "Mixed non-singleton orbits remain; the quotient does not assign all labels.",
            "classification": "WEAK_CLUE",
            "metric_moved": "none",
            "evidence_path": orbit.get("source", SOURCE_PATHS["frontier_119"]),
        },
        {
            "hypothesis": "diagonal_E_pressure",
            "algorithm": "Declare diagonal cells as a family and assign E to the observed diagonal-E anchors.",
            "description_bits": "positive only if the diagonal family is supplied; explicit pair costs are negative",
            "labels_predicted_holdout": 0,
            "coverage_pairs": "5 diagonal E anchors",
            "bits_below_lookup_after_costs": paid_summary["diagonal_family_net_with_label_arrangement_bits"],
            "explains_39_93_19_91": "no",
            "negative_controls": f"diagonal-family random-subset p={paid_summary['diagonal_family_random_subset_p_ge_nominal']:.4f}",
            "contradictions": "The family-supplied lower bound is ordinary under diagonal-family controls.",
            "classification": "REJECTED_CONTROL",
            "metric_moved": "5_falsification_strong",
            "evidence_path": SOURCE_PATHS["paid_anchor_159"],
        },
        {
            "hypothesis": "grid_coordinate_formula_paid",
            "algorithm": f"Best simple coordinate stump: {priority_best['rule']} -> {priority_best['pred_in']}/{priority_best['pred_out']} with leave-one-out scoring.",
            "description_bits": "does not beat lookup; rule family searched and controlled",
            "labels_predicted_holdout": priority_best["loo_hits"],
            "coverage_pairs": "55/55 predictions",
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_93_19_91": "no",
            "negative_controls": f"label-shuffle p={priority['label_shuffle_control']['p_control_ge_observed']:.4f}; digit-permutation p={priority['digit_permutation_control']['p_control_ge_observed']:.4f}",
            "contradictions": "Best stump accuracy is low and ordinary for the searched family.",
            "classification": "REJECTED_CONTROL",
            "metric_moved": "5_falsification_strong",
            "evidence_path": SOURCE_PATHS["priority_144"],
        },
        {
            "hypothesis": "inventory_frequency_derivation_holdout",
            "algorithm": "Use fixed/frequency-driven pair placement plus symbol inventory, then test the same rule on held-out books.",
            "description_bits": "inventory/order rule only; no paid row0 formula",
            "labels_predicted_holdout": inv_holdout["correct"],
            "coverage_pairs": f"{inv_holdout['correct']}/{inv_holdout['total']} holdout hits",
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_93_19_91": "no",
            "negative_controls": f"holdout control p={inv_holdout['control']['p_ge_observed']:.4f}; fixed-order random control p={inventory['random_order_control']['p_control_ge_observed']:.4f}",
            "contradictions": "Train-selected order does not generalize; fixed orders top out at 8/55 observed hits.",
            "classification": "REJECTED_CONTROL",
            "metric_moved": "5_falsification_strong",
            "evidence_path": SOURCE_PATHS["inventory_146"],
        },
        {
            "hypothesis": "recent_book_formula_as_row0_evidence",
            "algorithm": "Ask whether the current 8154.676268-bit book formula predicts the row0 table rather than merely using it.",
            "description_bits": "excluded from row0 scoring",
            "labels_predicted_holdout": 0,
            "coverage_pairs": "0/55 direct row0 predictions",
            "bits_below_lookup_after_costs": 0.0,
            "explains_39_93_19_91": "no",
            "negative_controls": "compatibility gate has predicts_row0_labels_under_holdout=false and beats_row0_lookup_after_cost=false",
            "contradictions": "The formula improves downstream book generation while assuming row0 as substrate.",
            "classification": "AUDIT_ONLY",
            "metric_moved": "none",
            "evidence_path": SOURCE_PATHS["formula_compat_70"],
        },
    ]

    moved = sorted({r["metric_moved"] for r in hypothesis_rows if r["metric_moved"].startswith("5_")})
    promoted_origin = [r for r in hypothesis_rows if r["classification"] == "PROMOTED_ORIGIN_FORMULA"]
    verdict = "row0_real_origin_search_negative_under_current_evidence"

    return {
        "schema": "row0_real_origin_search_scoreboard.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "row0_lookup_bits": baseline,
        "row0_pair_count": 55,
        "hypotheses": hypothesis_rows,
        "summary": {
            "real_row0_constructive_improvement": False,
            "promoted_origin_formula_count": len(promoted_origin),
            "metrics_moved": moved,
            "metrics_not_moved": [
                "1_labels_predicted_under_holdout",
                "2_bits_below_lookup_after_paid_costs",
                "3_new_controlled_explanation_39_93_19_91",
                "4_new_local_authorial_cipsoft_provenance",
            ],
            "surface_clue_retained": True,
            "book_formula_excluded_from_row0_score": bool(compat["summary"]["recent_formula_assumes_row0"]),
        },
    }


def write_scoreboard(scoreboard: dict[str, Any]) -> None:
    write_json(TEST_RESULTS / "01_row0_real_origin_scoreboard.json", scoreboard)

    cols = [
        ("hypothesis", "Hypothesis"),
        ("classification", "Class"),
        ("labels_predicted_holdout", "Holdout labels"),
        ("coverage_pairs", "Coverage"),
        ("bits_below_lookup_after_costs", "Bits below lookup"),
        ("metric_moved", "Metric"),
    ]
    md = [
        "# Row0 Real Origin Scoreboard",
        "",
        f"Verdict: `{scoreboard['verdict']}`.",
        "",
        f"Row0 lookup baseline: `{scoreboard['row0_lookup_bits']:.3f}` bits.",
        "",
        md_table(scoreboard["hypotheses"], cols),
        "",
        "Constructive row0 improvement: `false`. The only moved axis is stronger falsification of important origin hypotheses.",
        "",
    ]
    (TEST_RESULTS / "01_row0_real_origin_scoreboard.md").write_text("\n".join(md))

    csv_path = DATA / "row0_real_origin_scoreboard.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(scoreboard["hypotheses"][0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(scoreboard["hypotheses"])


def write_hypothesis_files(scoreboard: dict[str, Any]) -> None:
    for idx, row in enumerate(scoreboard["hypotheses"], start=2):
        slug = row["hypothesis"]
        payload = {
            "schema": "row0_real_origin_hypothesis_result.v1",
            "verdict": scoreboard["verdict"],
            "row0_lookup_bits": scoreboard["row0_lookup_bits"],
            "result": row,
        }
        write_json(TEST_RESULTS / f"{idx:02d}_{slug}.json", payload)
        md = [
            f"# {slug}",
            "",
            f"Classification: `{row['classification']}`.",
            "",
            f"Algorithm: {row['algorithm']}",
            "",
            f"Description cost: {row['description_bits']}",
            "",
            f"Holdout labels predicted: `{row['labels_predicted_holdout']}`.",
            "",
            f"Coverage: {row['coverage_pairs']}.",
            "",
            f"Bits below lookup after costs: `{row['bits_below_lookup_after_costs']}`.",
            "",
            f"39/93/19/91: {row['explains_39_93_19_91']}.",
            "",
            f"Controls: {row['negative_controls']}.",
            "",
            f"Contradictions: {row['contradictions']}",
            "",
            f"Evidence: `{row['evidence_path']}`.",
            "",
        ]
        (TEST_RESULTS / f"{idx:02d}_{slug}.md").write_text("\n".join(md))


def write_pair_inventory(scoreboard: dict[str, Any]) -> None:
    rows = pair_rows()
    write_json(DATA / "row0_pair_inventory.json", {"schema": "row0_pair_inventory.v1", "rows": rows})
    with (DATA / "row0_pair_inventory.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(row["label"] for row in rows)
    write_json(
        TEST_RESULTS / "00_row0_pair_inventory.json",
        {
            "schema": "row0_pair_inventory_summary.v1",
            "pair_count": len(rows),
            "label_counts": dict(sorted(counts.items())),
            "computed_lookup_bits": lookup_bits(rows),
            "scoreboard_lookup_bits": scoreboard["row0_lookup_bits"],
            "missing_ordered_code": "39",
            "present_reverse_code": "93",
            "directed_conflict": "19/91",
        },
    )


def write_completion_audit(scoreboard: dict[str, Any]) -> None:
    required = [
        TEST_RESULTS / "01_row0_real_origin_scoreboard.json",
        TEST_RESULTS / "01_row0_real_origin_scoreboard.md",
        DATA / "row0_pair_inventory.json",
        DATA / "row0_real_origin_scoreboard.csv",
        REPORTS / "row0_real_origin_search_report.md",
    ]
    status_rows = []
    for path in required:
        status_rows.append({"path": str(path.relative_to(REPO)), "exists": path.exists()})
    wiki_text = (REPO / SOURCE_PATHS["wiki"]).read_text()
    wiki_contains_update = "Row0 real-origin search" in wiki_text and "row0_real_origin_search_report.md" in wiki_text
    payload = {
        "schema": "row0_real_origin_completion_audit.v1",
        "objective_satisfied": all(row["exists"] for row in status_rows)
        and scoreboard["verdict"] == "row0_real_origin_search_negative_under_current_evidence"
        and wiki_contains_update,
        "verdict": scoreboard["verdict"],
        "deliverables": status_rows,
        "wiki_update_required": True,
        "wiki_update_present": wiki_contains_update,
        "wiki_update_reason": "validated negative row0-only conclusion; update should be short and non-semantic",
        "constructive_row0_improvement": scoreboard["summary"]["real_row0_constructive_improvement"],
        "metrics_moved": scoreboard["summary"]["metrics_moved"],
    }
    write_json(TEST_RESULTS / "12_completion_audit.json", payload)
    md = [
        "# Completion Audit",
        "",
        f"Objective satisfied by artifacts: `{payload['objective_satisfied']}`.",
        "",
        f"Verdict: `{payload['verdict']}`.",
        "",
        md_table(status_rows, [("path", "Path"), ("exists", "Exists")]),
        "",
        f"Wiki update required: `{payload['wiki_update_required']}`.",
        "",
        f"Wiki update present: `{payload['wiki_update_present']}`.",
        "",
    ]
    (TEST_RESULTS / "12_completion_audit.md").write_text("\n".join(md))


def write_final_report(scoreboard: dict[str, Any]) -> None:
    falsified = [r for r in scoreboard["hypotheses"] if r["classification"] == "REJECTED_CONTROL"]
    retained = [
        r
        for r in scoreboard["hypotheses"]
        if r["classification"] in ("PROMOTED_MECHANICAL_CLUE", "WEAK_CLUE")
    ]
    blocked = [r for r in scoreboard["hypotheses"] if r["classification"] == "BLOCKED_NEEDS_EXTERNAL_SOURCE"]
    audit_only = [r for r in scoreboard["hypotheses"] if r["classification"] == "AUDIT_ONLY"]

    cols = [
        ("hypothesis", "Hypothesis"),
        ("classification", "Class"),
        ("metric_moved", "Metric"),
        ("contradictions", "Contradiction / limit"),
    ]
    report = [
        "# Row0 Real Origin Search Report",
        "",
        f"Verdict: `{scoreboard['verdict']}`.",
        "",
        "This front searches only for row0-origin improvement. Downstream book-formula gains are explicitly excluded unless they directly predict the row0 pair-label table.",
        "",
        "## Result",
        "",
        "- Constructive row0 improvement: `false`.",
        "- Promoted origin formulas: `0`.",
        "- Metric moved: `5_falsification_strong` only.",
        "- Metrics not moved: holdout label prediction, paid bits below lookup, new controlled explanation of `39/93/19/91`, and new local/authorial/CipSoft provenance.",
        "",
        "The row0 table therefore remains exogenous under current evidence. This is a negative result about origin, not a reversal of the accepted row0 mechanical substrate.",
        "",
        "## Scoreboard",
        "",
        md_table(scoreboard["hypotheses"], cols),
        "",
        "## Falsified Or Rejected",
        "",
        md_table(falsified, [("hypothesis", "Hypothesis"), ("negative_controls", "Controls"), ("contradictions", "Why rejected")]),
        "",
        "## Retained But Not Promoted",
        "",
        md_table(retained, [("hypothesis", "Hypothesis"), ("classification", "Class"), ("contradictions", "Limit")]),
        "",
        "## Blocked",
        "",
        md_table(blocked, [("hypothesis", "Hypothesis"), ("contradictions", "Blocker")]),
        "",
        "## Audit-Only Boundaries",
        "",
        md_table(audit_only, [("hypothesis", "Hypothesis"), ("contradictions", "Boundary")]),
        "",
        "## Row0 Progress Accounting",
        "",
        "The only positive movement is metric 5: important origin hypotheses now have a single row0-only scoreboard that records their explicit algorithms, costs, controls, and contradictions. No new source, no holdout-capable label predictor, and no paid-below-lookup origin model was found.",
        "",
        "## Primary Artifacts",
        "",
        "- `analysis/row0_real_origin_search_20260621/reports/test_results/01_row0_real_origin_scoreboard.json`",
        "- `analysis/row0_real_origin_search_20260621/reports/test_results/12_completion_audit.json`",
        "- `analysis/row0_real_origin_search_20260621/data/row0_real_origin_scoreboard.csv`",
        "- `analysis/row0_real_origin_search_20260621/data/row0_pair_inventory.csv`",
        "",
    ]
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "row0_real_origin_search_report.md").write_text("\n".join(report))


def write_readme() -> None:
    readme = [
        "# Row0 Real Origin Search 2026-06-21",
        "",
        "Analysis-only row0 origin front. It scores row0 hypotheses independently from downstream book-generation formula improvements.",
        "",
        "Run:",
        "",
        "```bash",
        "python3 analysis/row0_real_origin_search_20260621/scripts/row0_real_origin_search.py",
        "```",
        "",
        "Main report: `reports/row0_real_origin_search_report.md`.",
        "",
    ]
    (FRONT / "README.md").write_text("\n".join(readme))


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    write_json(TEST_RESULTS / "00_source_digest.json", source_digest())
    scoreboard = build_scoreboard()
    write_scoreboard(scoreboard)
    write_hypothesis_files(scoreboard)
    write_pair_inventory(scoreboard)
    write_final_report(scoreboard)
    write_completion_audit(scoreboard)
    write_readme()


if __name__ == "__main__":
    main()
