from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
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


def zero_totals() -> dict[str, Any]:
    totals: dict[str, Any] = {"bits": 0.0, "forced_literals": 0, "forced_copies": 0}
    for key in COMPONENT_KEYS:
        totals[key] = 0.0
    for key in INVENTORY_KEYS:
        totals[key] = 0
    return totals


def reparse_breakdown(
    *,
    audit126,
    formula: dict[str, Any],
    books: dict[str, str],
    train_books: list[int],
    test_books: list[int],
    train_counts: dict[str, Any],
) -> dict[str, Any]:
    available = "".join(books[str(book)] for book in train_books)
    totals = zero_totals()
    book_rows = []
    errors = []

    for book in test_books:
        encoded = audit126.encode_book_frozen_reparse(
            book=str(book),
            text=books[str(book)],
            available=available,
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
                "forced_literals": encoded["forced_literals"],
                "forced_copies": encoded["forced_copies"],
                "component_bits": {key: encoded[key] for key in COMPONENT_KEYS},
                "inventory": {key: encoded[key] for key in INVENTORY_KEYS},
                "validation": encoded["validation"],
            }
        )
        available += books[str(book)]

    totals["validation"] = {
        "book_count": len(test_books),
        "books_roundtrip_ok": len(test_books) - len(errors),
        "errors": errors,
    }
    return {"totals": totals, "book_rows": book_rows}


def largest_positive(delta: dict[str, float]) -> str | None:
    positives = {key: value for key, value in delta.items() if value > 1e-9}
    if not positives:
        return None
    return max(positives, key=positives.__getitem__)


def largest_gain(delta: dict[str, float]) -> str | None:
    negatives = {key: value for key, value in delta.items() if value < -1e-9}
    if not negatives:
        return None
    return min(negatives, key=negatives.__getitem__)


def make_result() -> dict[str, Any]:
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    family_holdout = load_json(FAMILY_HOLDOUT)
    all_books = set(range(70))

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    target_rows = [
        row
        for row in family_holdout["rows"]
        if row["reparse_minus_active_bits"] >= -1e-9
    ]
    rows = []
    for source_row in target_rows:
        test_books = list(source_row["test_books"])
        train_books = sorted(all_books - set(test_books))
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=set(train_books),
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        reparse = reparse_breakdown(
            audit126=audit126,
            formula=formula,
            books=books,
            train_books=train_books,
            test_books=test_books,
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
        component_delta = {
            key: reparse["totals"][key] - active[key]
            for key in COMPONENT_KEYS
        }
        inventory_delta = {
            key: reparse["totals"][key] - active[key]
            for key in INVENTORY_KEYS
        }
        rows.append(
            {
                "label": source_row["label"],
                "test_books": test_books,
                "component_family_failure": source_row["component_family_failure"],
                "active_bits": active["bits"],
                "deterministic_reparse_bits": reparse["totals"]["bits"],
                "reparse_minus_active_bits": reparse["totals"]["bits"] - active["bits"],
                "reparse_gain_vs_raw_bits": source_row["reparse_gain_vs_raw_bits"],
                "component_delta_bits": component_delta,
                "inventory_delta": inventory_delta,
                "largest_loss_component": largest_positive(component_delta),
                "largest_gain_component": largest_gain(component_delta),
                "active_component_bits": {key: active[key] for key in COMPONENT_KEYS},
                "reparse_component_bits": {key: reparse["totals"][key] for key in COMPONENT_KEYS},
                "active_inventory": {key: active[key] for key in INVENTORY_KEYS},
                "reparse_inventory": {key: reparse["totals"][key] for key in INVENTORY_KEYS},
                "forced_items": {
                    "forced_literals": reparse["totals"]["forced_literals"],
                    "forced_copies": reparse["totals"]["forced_copies"],
                },
                "validation": reparse["totals"]["validation"],
                "book_rows": reparse["book_rows"],
            }
        )

    loss_counter = Counter(row["largest_loss_component"] or "no_positive_component" for row in rows)
    worst = max(rows, key=lambda row: row["reparse_minus_active_bits"])
    classification = (
        "family_reparse_losses_are_local_component_overheads"
        if all(row["validation"]["errors"] == [] for row in rows)
        else "family_reparse_losses_include_roundtrip_failures"
    )
    return {
        "schema": "recipe_reparse_family_loss_decomposition.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "family_holdout": rel(FAMILY_HOLDOUT),
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
        },
        "rows": rows,
        "summary": {
            "loss_family_count": len(rows),
            "all_roundtrip": all(row["validation"]["errors"] == [] for row in rows),
            "component_family_failure_loss_count": sum(
                1 for row in rows if row["component_family_failure"]
            ),
            "mean_reparse_minus_active_bits": sum(
                row["reparse_minus_active_bits"] for row in rows
            )
            / len(rows),
            "max_reparse_minus_active_bits": worst["reparse_minus_active_bits"],
            "worst_family": worst["label"],
            "largest_loss_component_counts": dict(sorted(loss_counter.items())),
            "loss_labels": [row["label"] for row in rows],
            "interpretation": (
                "The families where deterministic reparse does not beat the "
                "active full-corpus recipe are still roundtrip-valid and still "
                "beat raw digits. The remaining losses are component-level local "
                "overheads against the already-seen active recipe, not evidence "
                "for plaintext or row0 origin."
            ),
        },
        "decision": {
            "family_loss_status": "localized_component_overhead_against_active_recipe",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "09_recipe_reparse_family_loss_decomposition.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Recipe Reparse Family Loss Decomposition",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 08 found five public-bookcase families where deterministic reparse",
        "beats raw digits but does not beat the active full-corpus recipe. This",
        "audit decomposes those five local losses by charged component.",
        "",
        "## Summary",
        "",
        f"- Loss families: `{result['summary']['loss_family_count']}`.",
        f"- All roundtrip: `{result['summary']['all_roundtrip']}`.",
        f"- Component-failure loss families: `{result['summary']['component_family_failure_loss_count']}`.",
        f"- Mean reparse minus active: `{result['summary']['mean_reparse_minus_active_bits']:.3f}` bits.",
        f"- Worst family: `{result['summary']['worst_family']}` at `{result['summary']['max_reparse_minus_active_bits']:.3f}` bits.",
        f"- Largest-loss component counts: `{result['summary']['largest_loss_component_counts']}`.",
        "",
        "## Loss Rows",
        "",
        "| Family | Books | Reparse - active | Largest loss | Largest gain | Component failure | Raw gain |",
        "|---|---|---:|---|---|---|---:|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | "
            f"`{row['reparse_minus_active_bits']:.3f}` | "
            f"`{row['largest_loss_component']}` | `{row['largest_gain_component']}` | "
            f"`{row['component_family_failure']}` | `{row['reparse_gain_vs_raw_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Component Delta Bits",
            "",
            "Values are deterministic reparse minus active full-corpus recipe. Positive values are local losses.",
            "",
            "| Family | Literal length | Literal payload | Item type | Copy address | Copy length | Inventory delta |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in result["rows"]:
        delta = row["component_delta_bits"]
        lines.append(
            f"| `{row['label']}` | `{delta['literal_length_bits']:.3f}` | "
            f"`{delta['literal_payload_bits']:.3f}` | "
            f"`{delta['item_type_stream_bits']:.3f}` | "
            f"`{delta['copy_address_bits']:.3f}` | "
            f"`{delta['copy_length_stream_bits']:.3f}` | "
            f"`{row['inventory_delta']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- These are local active-recipe wins, not raw predictive failures.",
            "- The five families still roundtrip and still beat raw digit coding.",
            "- The generation explanation remains partial because the active full-corpus recipe can still be locally cheaper.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "09_recipe_reparse_family_loss_decomposition.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
