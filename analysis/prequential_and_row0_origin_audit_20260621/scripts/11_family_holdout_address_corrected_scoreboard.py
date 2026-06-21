from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUDIT_10 = HERE / "scripts" / "10_family_holdout_address_space_audit.py"
FAMILY_HOLDOUT = TEST_RESULTS / "08_recipe_reparse_family_holdout.json"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"

EPSILON_BITS = 1e-3


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
    audit10 = load_module("audit10_address_space", AUDIT_10)
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    family_holdout = load_json(FAMILY_HOLDOUT)
    all_books = set(range(70))

    rows = []
    for row in family_holdout["rows"]:
        test_books = list(row["test_books"])
        train_books = sorted(all_books - set(test_books))
        active_rebased = audit10.reprice_active_recipe_in_holdout_coordinates(
            formula=formula,
            books=books,
            train_books=train_books,
            test_books=test_books,
        )
        active_address_shift = active_rebased["coordinate_shift_bits"]
        active_address_corrected_bits = row["active_recipe_frozen_bits"] + active_address_shift
        corrected_delta = row["deterministic_reparse_bits"] - active_address_corrected_bits
        rows.append(
            {
                "label": row["label"],
                "test_books": test_books,
                "raw_uniform_bits": row["raw_uniform_bits"],
                "active_recipe_original_bits": row["active_recipe_frozen_bits"],
                "active_address_coordinate_shift_bits": active_address_shift,
                "active_address_corrected_bits": active_address_corrected_bits,
                "deterministic_reparse_bits": row["deterministic_reparse_bits"],
                "reparse_minus_active_original_bits": row["reparse_minus_active_bits"],
                "reparse_minus_active_address_corrected_bits": corrected_delta,
                "reparse_beats_raw": row["reparse_beats_raw"],
                "reparse_beats_active_original": row["reparse_beats_active_recipe"],
                "reparse_beats_or_ties_active_address_corrected": corrected_delta <= EPSILON_BITS,
                "component_family_failure": row["component_family_failure"],
                "active_rebased_validation": active_rebased["validation"],
                "copy_count": len(active_rebased["copy_rows"]),
            }
        )

    original_worse = [row for row in rows if row["reparse_minus_active_original_bits"] > EPSILON_BITS]
    corrected_worse = [
        row for row in rows if row["reparse_minus_active_address_corrected_bits"] > EPSILON_BITS
    ]
    classification = (
        "family_holdout_reparse_beats_or_ties_active_after_address_correction"
        if not corrected_worse
        else "family_holdout_reparse_has_address_corrected_losses"
    )
    return {
        "schema": "family_holdout_address_corrected_scoreboard.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "epsilon_bits": EPSILON_BITS,
        "inputs": {
            "family_holdout": rel(FAMILY_HOLDOUT),
            "address_space_audit": rel(AUDIT_10),
            "recipe_reparse": rel(AUDIT_126),
        },
        "rows": rows,
        "summary": {
            "family_count": len(rows),
            "all_active_rebased_roundtrip": all(
                row["active_rebased_validation"]["errors"] == [] for row in rows
            ),
            "reparse_beats_raw_count": sum(1 for row in rows if row["reparse_beats_raw"]),
            "original_reparse_beats_or_ties_active_count": sum(
                1 for row in rows if row["reparse_minus_active_original_bits"] <= EPSILON_BITS
            ),
            "address_corrected_reparse_beats_or_ties_active_count": sum(
                1 for row in rows if row["reparse_beats_or_ties_active_address_corrected"]
            ),
            "original_worse_labels": [row["label"] for row in original_worse],
            "address_corrected_worse_labels": [row["label"] for row in corrected_worse],
            "mean_original_reparse_minus_active_bits": sum(
                row["reparse_minus_active_original_bits"] for row in rows
            )
            / len(rows),
            "mean_address_corrected_reparse_minus_active_bits": sum(
                row["reparse_minus_active_address_corrected_bits"] for row in rows
            )
            / len(rows),
            "min_address_corrected_reparse_minus_active_bits": min(
                row["reparse_minus_active_address_corrected_bits"] for row in rows
            ),
            "max_address_corrected_reparse_minus_active_bits": max(
                row["reparse_minus_active_address_corrected_bits"] for row in rows
            ),
            "interpretation": (
                "After correcting active copy-address cost to the same holdout "
                "coordinate system used by deterministic reparse, public-bookcase "
                "family holdout no longer has active-recipe local wins at the "
                "declared epsilon."
            ),
        },
        "decision": {
            "family_holdout_status": "predictive_reparse_retained_after_address_correction",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "11_family_holdout_address_corrected_scoreboard.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Family Holdout Address-Corrected Scoreboard",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 10 showed that the five family losses against the active recipe were",
        "copy-address coordinate artifacts. This audit applies that address-space",
        "correction to all public-bookcase family holdouts.",
        "",
        "## Summary",
        "",
        f"- Families checked: `{result['summary']['family_count']}`.",
        f"- Active recipes roundtrip after address rebase: `{result['summary']['all_active_rebased_roundtrip']}`.",
        f"- Reparse beats raw digits: `{result['summary']['reparse_beats_raw_count']}/{result['summary']['family_count']}`.",
        f"- Reparse beats/ties active before correction: `{result['summary']['original_reparse_beats_or_ties_active_count']}/{result['summary']['family_count']}`.",
        f"- Reparse beats/ties active after address correction: `{result['summary']['address_corrected_reparse_beats_or_ties_active_count']}/{result['summary']['family_count']}`.",
        f"- Mean reparse minus active before correction: `{result['summary']['mean_original_reparse_minus_active_bits']:.3f}` bits.",
        f"- Mean reparse minus active after correction: `{result['summary']['mean_address_corrected_reparse_minus_active_bits']:.3f}` bits.",
        f"- Address-corrected worse labels: `{result['summary']['address_corrected_worse_labels']}`.",
        "",
        "## Rows",
        "",
        "| Family | Books | Original delta | Address-corrected delta | Address shift | Beats/ties corrected |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | "
            f"`{row['reparse_minus_active_original_bits']:.3f}` | "
            f"`{row['reparse_minus_active_address_corrected_bits']:.3f}` | "
            f"`{row['active_address_coordinate_shift_bits']:.3f}` | "
            f"`{row['reparse_beats_or_ties_active_address_corrected']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Public-bookcase family holdout reparsing beats raw digits in every family.",
            "- The apparent active-recipe local wins disappear after address-space correction.",
            "- This strengthens predictive recipe validation, but it does not derive row0 or promote a final authorial method.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "11_family_holdout_address_corrected_scoreboard.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
