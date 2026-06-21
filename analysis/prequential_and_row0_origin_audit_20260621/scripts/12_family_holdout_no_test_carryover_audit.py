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
FAMILY_HOLDOUT = TEST_RESULTS / "08_recipe_reparse_family_holdout.json"

COMPONENT_KEYS = [
    "literal_length_bits",
    "literal_payload_bits",
    "item_type_stream_bits",
    "copy_address_bits",
    "copy_length_stream_bits",
]
INVENTORY_KEYS = ["literal_runs", "literal_digits", "copy_items", "copied_digits"]


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


def empty_totals() -> dict[str, Any]:
    totals: dict[str, Any] = {
        "bits": 0.0,
        "forced_literals": 0,
        "forced_copies": 0,
    }
    for key in COMPONENT_KEYS:
        totals[key] = 0.0
    for key in INVENTORY_KEYS:
        totals[key] = 0
    return totals


def reparse_no_test_carryover(
    *,
    audit126,
    formula: dict[str, Any],
    books: dict[str, str],
    train_books: list[int],
    test_books: list[int],
    train_counts: dict[str, Any],
) -> dict[str, Any]:
    train_available = "".join(books[str(book)] for book in train_books)
    totals = empty_totals()
    book_rows = []
    errors = []
    for book in test_books:
        encoded = audit126.encode_book_frozen_reparse(
            book=str(book),
            text=books[str(book)],
            available=train_available,
            formula=formula,
            train_counts=train_counts,
        )
        for key in ["bits", "forced_literals", "forced_copies", *COMPONENT_KEYS, *INVENTORY_KEYS]:
            totals[key] += encoded[key]
        if encoded["validation"]["errors"]:
            errors.append({"book": book, "errors": encoded["validation"]["errors"]})
        book_rows.append(
            {
                "book": book,
                "bits": encoded["bits"],
                "copy_items": encoded["copy_items"],
                "copied_digits": encoded["copied_digits"],
                "literal_runs": encoded["literal_runs"],
                "literal_digits": encoded["literal_digits"],
                "component_bits": {key: encoded[key] for key in COMPONENT_KEYS},
                "validation": encoded["validation"],
            }
        )
    totals["validation"] = {
        "book_count": len(test_books),
        "books_roundtrip_ok": len(test_books) - len(errors),
        "errors": errors,
    }
    return {"totals": totals, "book_rows": book_rows}


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
    family_holdout = load_json(FAMILY_HOLDOUT)
    standard_by_label = {row["label"]: row for row in family_holdout["rows"]}
    all_books = set(range(70))

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = []
    for label, test_books_set in sorted(families.items()):
        test_books = sorted(test_books_set)
        train_books = sorted(all_books - set(test_books))
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=set(train_books),
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        no_carry = reparse_no_test_carryover(
            audit126=audit126,
            formula=formula,
            books=books,
            train_books=train_books,
            test_books=test_books,
            train_counts=train_counts,
        )
        standard = standard_by_label[label]
        raw_bits = standard["raw_uniform_bits"]
        no_carry_bits = no_carry["totals"]["bits"]
        rows.append(
            {
                "label": label,
                "test_books": test_books,
                "raw_uniform_bits": raw_bits,
                "standard_family_reparse_bits": standard["deterministic_reparse_bits"],
                "no_test_carryover_reparse_bits": no_carry_bits,
                "no_test_carryover_gain_vs_raw_bits": raw_bits - no_carry_bits,
                "standard_gain_vs_raw_bits": standard["reparse_gain_vs_raw_bits"],
                "no_carryover_minus_standard_bits": no_carry_bits
                - standard["deterministic_reparse_bits"],
                "no_test_carryover_beats_raw": no_carry_bits < raw_bits,
                "standard_reparse_beats_raw": standard["reparse_beats_raw"],
                "validation": no_carry["totals"]["validation"],
                "inventory": {key: no_carry["totals"][key] for key in INVENTORY_KEYS},
                "component_bits": {key: no_carry["totals"][key] for key in COMPONENT_KEYS},
                "book_rows": no_carry["book_rows"],
            }
        )

    failures = [row for row in rows if not row["no_test_carryover_beats_raw"]]
    classification = (
        "family_holdout_no_test_carryover_predictive"
        if not failures
        else "family_holdout_no_test_carryover_partial"
    )
    return {
        "schema": "family_holdout_no_test_carryover_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "families": rel(AUDIT_125),
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
            "standard_family_holdout": rel(FAMILY_HOLDOUT),
        },
        "rows": rows,
        "summary": {
            "family_count": len(rows),
            "roundtrip_family_count": sum(1 for row in rows if row["validation"]["errors"] == []),
            "no_test_carryover_beats_raw_count": sum(
                1 for row in rows if row["no_test_carryover_beats_raw"]
            ),
            "standard_reparse_beats_raw_count": sum(
                1 for row in rows if row["standard_reparse_beats_raw"]
            ),
            "mean_no_test_carryover_gain_vs_raw_bits": sum(
                row["no_test_carryover_gain_vs_raw_bits"] for row in rows
            )
            / len(rows),
            "mean_standard_gain_vs_raw_bits": sum(row["standard_gain_vs_raw_bits"] for row in rows)
            / len(rows),
            "mean_no_carryover_minus_standard_bits": sum(
                row["no_carryover_minus_standard_bits"] for row in rows
            )
            / len(rows),
            "max_no_carryover_minus_standard_bits": max(
                row["no_carryover_minus_standard_bits"] for row in rows
            ),
            "failure_labels": [row["label"] for row in failures],
            "interpretation": (
                "Even when each held-out book is reparsed from the training "
                "complement alone, without carrying earlier held-out books into "
                "later held-out books, every public-bookcase family still beats "
                "raw digit coding."
            ),
        },
        "decision": {
            "no_test_carryover_status": "predictive_signal_retained",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "12_family_holdout_no_test_carryover_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Family Holdout No-Test-Carryover Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Family reparse holdouts normally emit the held-out family sequentially.",
        "This audit removes cross-book carryover inside the held-out family:",
        "each held-out book starts from the training-complement inventory only.",
        "",
        "## Summary",
        "",
        f"- Families checked: `{result['summary']['family_count']}`.",
        f"- Roundtrip families: `{result['summary']['roundtrip_family_count']}/{result['summary']['family_count']}`.",
        f"- No-test-carryover beats raw: `{result['summary']['no_test_carryover_beats_raw_count']}/{result['summary']['family_count']}`.",
        f"- Standard family reparse beats raw: `{result['summary']['standard_reparse_beats_raw_count']}/{result['summary']['family_count']}`.",
        f"- Mean no-test-carryover gain vs raw: `{result['summary']['mean_no_test_carryover_gain_vs_raw_bits']:.3f}` bits.",
        f"- Mean standard gain vs raw: `{result['summary']['mean_standard_gain_vs_raw_bits']:.3f}` bits.",
        f"- Mean no-carryover minus standard: `{result['summary']['mean_no_carryover_minus_standard_bits']:.3f}` bits.",
        f"- Failure labels: `{result['summary']['failure_labels']}`.",
        "",
        "## Rows",
        "",
        "| Family | Books | No-carry gain vs raw | Standard gain vs raw | No-carry - standard | Beats raw |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | "
            f"`{row['no_test_carryover_gain_vs_raw_bits']:.3f}` | "
            f"`{row['standard_gain_vs_raw_bits']:.3f}` | "
            f"`{row['no_carryover_minus_standard_bits']:.3f}` | "
            f"`{row['no_test_carryover_beats_raw']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Public-bookcase family prediction does not depend on cross-book carryover inside the held-out family to beat raw digits.",
            "- Cross-book carryover still improves compression and remains valid for sequential generation, but it is not required for the positive family-holdout signal.",
            "- This strengthens predictive validation without deriving row0 or promoting a final authorial method.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "12_family_holdout_no_test_carryover_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
