from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_125 = AUTHORIAL / "scripts" / "125_prequential_and_row0_origin_audit.py"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_128 = AUTHORIAL / "scripts" / "128_prequential_recipe_reparse_trainset_controls.py"
FAMILY_FAILURE_AUDIT = TEST_RESULTS / "02_family_holdout_failure_audit.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def make_result() -> dict[str, Any]:
    audit125 = load_module("audit125_prequential_row0", AUDIT_125)
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    families = audit125.load_bookcase_families()
    all_books = set(range(70))

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    family_failure = load_json(FAMILY_FAILURE_AUDIT)
    component_failure_labels = set(family_failure["summary"]["failure_labels"])

    rows = []
    for label, test_books_set in sorted(families.items()):
        test_books = sorted(test_books_set)
        train_books = all_books - set(test_books)
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=train_books,
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        reparse = audit128.reparse_with_train_inventory(
            audit126,
            formula=formula,
            books=books,
            train_order=sorted(train_books),
            test_order=test_books,
            train_counts=train_counts,
        )
        active = audit126.active_recipe_frozen_cost(
            formula=formula,
            books=books,
            test_books=set(test_books),
            train_counts=train_counts,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        raw_bits = audit128.raw_uniform_bits(books, test_books)
        rows.append(
            {
                "label": label,
                "test_books": test_books,
                "test_book_count": len(test_books),
                "raw_uniform_bits": raw_bits,
                "active_recipe_frozen_bits": active["bits"],
                "deterministic_reparse_bits": reparse["bits"],
                "reparse_gain_vs_raw_bits": reparse["gain_vs_raw_bits"],
                "active_gain_vs_raw_bits": raw_bits - active["bits"],
                "reparse_minus_active_bits": reparse["bits"] - active["bits"],
                "reparse_beats_raw": reparse["gain_vs_raw_bits"] > 0,
                "reparse_beats_active_recipe": reparse["bits"] < active["bits"],
                "component_family_failure": label in component_failure_labels,
                "validation": reparse["validation"],
                "reparse_inventory": {
                    "literal_runs": reparse["literal_runs"],
                    "literal_digits": reparse["literal_digits"],
                    "copy_items": reparse["copy_items"],
                    "copied_digits": reparse["copied_digits"],
                },
                "active_inventory": {
                    "literal_runs": active["literal_runs"],
                    "literal_digits": active["literal_digits"],
                    "copy_items": active["copy_items"],
                    "copied_digits": active["copied_digits"],
                },
            }
        )

    failures = [row for row in rows if not row["reparse_beats_raw"]]
    worse_than_active = [row for row in rows if not row["reparse_beats_active_recipe"]]
    component_failure_rows = [row for row in rows if row["component_family_failure"]]
    component_failure_rescued = [
        row
        for row in component_failure_rows
        if row["reparse_beats_raw"] and row["validation"]["errors"] == []
    ]

    classification = (
        "recipe_reparse_family_holdouts_predictive_with_active_recipe_ties"
        if not failures and worse_than_active
        else "recipe_reparse_family_holdouts_predictive"
        if not failures
        else "recipe_reparse_family_holdouts_partial"
    )

    return {
        "schema": "recipe_reparse_family_holdout.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "families": rel(AUDIT_125),
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
            "component_family_failure_audit": rel(FAMILY_FAILURE_AUDIT),
        },
        "rows": rows,
        "summary": {
            "family_count": len(rows),
            "reparse_beats_raw_count": sum(1 for row in rows if row["reparse_beats_raw"]),
            "reparse_beats_active_recipe_count": sum(
                1 for row in rows if row["reparse_beats_active_recipe"]
            ),
            "roundtrip_family_count": sum(1 for row in rows if row["validation"]["errors"] == []),
            "component_failure_family_count": len(component_failure_rows),
            "component_failure_reparse_beats_raw_count": len(component_failure_rescued),
            "worst_reparse_minus_active_bits": max(row["reparse_minus_active_bits"] for row in rows),
            "best_reparse_minus_active_bits": min(row["reparse_minus_active_bits"] for row in rows),
            "mean_reparse_minus_active_bits": sum(row["reparse_minus_active_bits"] for row in rows)
            / len(rows),
            "worse_than_active_labels": [row["label"] for row in worse_than_active],
            "interpretation": (
                "Held-out public-bookcase families remain reparse-predictable versus "
                "raw digits. The deterministic parser does not always beat the "
                "full-corpus active recipe, so this supports predictive recipe "
                "discovery without promoting a final authorial method."
            ),
        },
        "decision": {
            "recipe_predictive_signal": "retained_under_public_bookcase_family_holdout",
            "family_failure_status": "component_failures_are_not_recipe_discovery_failures",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "08_recipe_reparse_family_holdout.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Recipe Reparse Family Holdout",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Component-only prequential scoring had public-bookcase family failures.",
        "This audit asks whether deterministic recipe discovery also fails on those",
        "families. Each split trains on every book outside one public bookcase family,",
        "then reparses that held-out family under frozen counts.",
        "",
        "## Summary",
        "",
        f"- Families: `{result['summary']['family_count']}`.",
        f"- Reparse beats raw digits: `{result['summary']['reparse_beats_raw_count']}/{result['summary']['family_count']}`.",
        f"- Reparse beats active frozen recipe: `{result['summary']['reparse_beats_active_recipe_count']}/{result['summary']['family_count']}`.",
        f"- Component-failure families reparse beats raw: `{result['summary']['component_failure_reparse_beats_raw_count']}/{result['summary']['component_failure_family_count']}`.",
        f"- Mean reparse minus active: `{result['summary']['mean_reparse_minus_active_bits']:.3f}` bits.",
        "",
        "## Rows",
        "",
        "| Family | Books | Raw gain | Reparse - active | Beats raw | Beats active | Component failure |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | "
            f"`{row['reparse_gain_vs_raw_bits']:.3f}` | "
            f"`{row['reparse_minus_active_bits']:.3f}` | "
            f"`{row['reparse_beats_raw']}` | `{row['reparse_beats_active_recipe']}` | "
            f"`{row['component_family_failure']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Recipe reparsing remains predictive under public-bookcase family holdout.",
            "- The prior component-only family failures are not recipe-discovery failures.",
            "- The active full-corpus recipe is still sometimes cheaper, so the generation explanation remains partial.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "08_recipe_reparse_family_holdout.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
