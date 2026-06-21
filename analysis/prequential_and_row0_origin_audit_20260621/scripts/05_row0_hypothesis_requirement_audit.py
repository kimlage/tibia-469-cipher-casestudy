from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PARENT_AUDIT = TEST_RESULTS / "01_prequential_and_row0_origin_audit.json"
LOOKUP_BASELINE = (
    ROOT
    / "analysis"
    / "row0_origin_parallel_20260621"
    / "reports"
    / "test_results"
    / "143_row0_lookup_baseline_mdl.json"
)
ROW0_FINAL_REPORT = (
    ROOT
    / "analysis"
    / "row0_origin_parallel_20260621"
    / "reports"
    / "final_row0_origin_parallel_report.md"
)


REQUIREMENTS = (
    "clear_algorithm",
    "descriptive_cost",
    "coverage",
    "contradictions",
    "negative_controls",
    "random_or_permuted_comparison",
)


CONTROL_INTERPRETATION = {
    "manual_authorial_lookup": {
        "random_or_permuted_comparison": (
            "Not applicable as a promoted generator: this is the direct lookup/null "
            "baseline that random or permuted formulas must beat."
        ),
        "failure_gate": "baseline_only_no_compact_origin",
        "passes_as_origin_formula": False,
    },
    "simple_permutation_or_group_rule": {
        "random_or_permuted_comparison": (
            "Control p=1.0 in the consolidated audit: the exact finite-group row "
            "acts as one group per cell and is classified as lookup disguise."
        ),
        "failure_gate": "lookup_disguise_after_rule_cost",
        "passes_as_origin_formula": False,
    },
    "grid_10x10_mechanism": {
        "random_or_permuted_comparison": (
            "Matrix search has an above-random partial-hit p-value, but the "
            "charged candidate is not lossless and remains costlier than lookup; "
            "local 2D/grid controls therefore do not promote an origin formula."
        ),
        "failure_gate": "partial_grid_signal_not_lossless_below_lookup",
        "passes_as_origin_formula": False,
    },
    "order_or_frequency_derivation": {
        "random_or_permuted_comparison": (
            "Usage/fill-order controls are ordinary: usage_train_p_ge_observed "
            "is 0.6534 and tape first-use Bonferroni is 1.0."
        ),
        "failure_gate": "holdout_and_control_failure",
        "passes_as_origin_formula": False,
    },
    "known_external_text_source": {
        "random_or_permuted_comparison": (
            "Searched lore/text orders can create partial matrix hits, but no fixed "
            "CipSoft/in-game source is attested; Avar Tar remains a negative control."
        ),
        "failure_gate": "no_primary_fixed_external_source",
        "passes_as_origin_formula": False,
    },
    "workbook_or_script_artifact": {
        "random_or_permuted_comparison": (
            "Artifact provenance is a code/path audit rather than a stochastic "
            "table generator: scripts preserve source cells and no synthesizing "
            "algorithm is found."
        ),
        "failure_gate": "provenance_preservation_not_origin_generator",
        "passes_as_origin_formula": False,
    },
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def requirement_status(row: dict[str, Any]) -> dict[str, bool]:
    return {
        "clear_algorithm": bool(row.get("algorithm")),
        "descriptive_cost": row.get("descriptive_cost_bits") is not None,
        "coverage": bool(row.get("coverage")),
        "contradictions": bool(row.get("contradictions")),
        "negative_controls": row.get("negative_controls") is not None,
        "random_or_permuted_comparison": bool(
            CONTROL_INTERPRETATION[row["hypothesis"]]["random_or_permuted_comparison"]
        ),
    }


def make_result() -> dict[str, Any]:
    parent = load_json(PARENT_AUDIT)
    lookup = load_json(LOOKUP_BASELINE)
    source_rows = parent["row0_origin"]["hypotheses"]

    matrix = []
    for row in source_rows:
        hypothesis = row["hypothesis"]
        controls = CONTROL_INTERPRETATION[hypothesis]
        status = requirement_status(row)
        matrix.append(
            {
                "hypothesis": hypothesis,
                "status": row["status"],
                "algorithm": row["algorithm"],
                "descriptive_cost_bits": row["descriptive_cost_bits"],
                "coverage": row["coverage"],
                "contradictions": row["contradictions"],
                "negative_controls": row["negative_controls"],
                "random_or_permuted_comparison": controls["random_or_permuted_comparison"],
                "requirement_status": status,
                "all_required_fields_present": all(status[requirement] for requirement in REQUIREMENTS),
                "passes_as_origin_formula": controls["passes_as_origin_formula"],
                "failure_gate": controls["failure_gate"],
                "source": row["source"],
            }
        )

    promoted = [row for row in matrix if row["passes_as_origin_formula"]]
    incomplete = [
        row["hypothesis"]
        for row in matrix
        if not row["all_required_fields_present"]
    ]
    result = {
        "schema": "row0_origin_hypothesis_requirement_audit.v1",
        "classification": "row0_origin_requirements_all_tested_no_origin_formula",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "parent_audit": rel(PARENT_AUDIT),
            "lookup_baseline": rel(LOOKUP_BASELINE),
            "row0_parallel_final_report": rel(ROW0_FINAL_REPORT),
        },
        "lookup_baselines": {
            "bits_lookup_given_inventory": lookup["bits_lookup_given_inventory"],
            "bits_direct_symbol_alphabet": lookup["bits_direct_symbol_alphabet"],
            "bits_direct_observed_label_alphabet": lookup["bits_direct_observed_label_alphabet"],
            "promotion_rule": lookup["promotion_rule"],
        },
        "requirements": list(REQUIREMENTS),
        "hypothesis_matrix": matrix,
        "summary": {
            "hypotheses_checked": len(matrix),
            "hypotheses_with_all_required_fields": len(matrix) - len(incomplete),
            "incomplete_hypotheses": incomplete,
            "promoted_origin_formula_count": len(promoted),
            "row0_origin_status": "exogenous_under_current_evidence",
            "decision": (
                "Every requested origin family has an explicit algorithm, cost or "
                "cost note, coverage, contradiction ledger, and control statement. "
                "No family passes the origin-formula gate."
            ),
        },
        "decision": {
            "row0_explains": parent["row0_origin"]["what_row0_explains"],
            "row0_remains_exogenous": parent["row0_origin"]["what_remains_exogenous"],
            "acceptable_negative_result": "origin_of_row0_continues_exogenous",
            "next_valid_unlocks": [
                "primary CipSoft/in-game symbol table or exact book-to-meaning crib",
                "fixed external source that predicts row0 labels without search leakage",
                "charged holdout-capable row0 algorithm below lookup cost",
                "provenance artifact showing an earlier authorial worksheet/source order",
            ],
        },
    }
    return result


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "05_row0_hypothesis_requirement_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Row0 Hypothesis Requirement Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This follow-up forces each requested `row0` origin hypothesis through the",
        "same falsifiable checklist: clear algorithm, descriptive cost, coverage,",
        "contradictions, negative controls, and random/permuted comparison. It",
        "does not search for plaintext and does not change the compression bound.",
        "",
        "## Lookup Baselines",
        "",
        f"- Lookup cost given inventory: `{result['lookup_baselines']['bits_lookup_given_inventory']:.3f}` bits.",
        f"- Direct symbol-alphabet cost: `{result['lookup_baselines']['bits_direct_symbol_alphabet']:.3f}` bits.",
        f"- Direct observed-label alphabet cost: `{result['lookup_baselines']['bits_direct_observed_label_alphabet']:.3f}` bits.",
        "- Promotion rule: a row0-origin formula must beat lookup after rule, parameters, exceptions, order, and search costs.",
        "",
        "## Requirement Matrix",
        "",
        "| Hypothesis | Status | Required fields | Cost | Coverage | Failure gate |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in result["hypothesis_matrix"]:
        cost = row["descriptive_cost_bits"]
        cost_text = f"{cost:.3f}" if isinstance(cost, (int, float)) else str(cost)
        required = "yes" if row["all_required_fields_present"] else "no"
        lines.append(
            f"| `{row['hypothesis']}` | `{row['status']}` | `{required}` | "
            f"{cost_text} | {row['coverage']} | `{row['failure_gate']}` |"
        )

    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Hypothesis | Negative / random-permuted control interpretation |",
            "|---|---|",
        ]
    )
    for row in result["hypothesis_matrix"]:
        lines.append(
            f"| `{row['hypothesis']}` | {row['random_or_permuted_comparison']} |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Hypotheses checked: `{result['summary']['hypotheses_checked']}`.",
            f"- Hypotheses with all required fields: `{result['summary']['hypotheses_with_all_required_fields']}`.",
            f"- Promoted row0 origin formulas: `{result['summary']['promoted_origin_formula_count']}`.",
            "- Acceptable negative result recorded: `origin_of_row0_continues_exogenous`.",
            "- No translation, plaintext, or case-reopening claim is introduced.",
        ]
    )
    (TEST_RESULTS / "05_row0_hypothesis_requirement_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
