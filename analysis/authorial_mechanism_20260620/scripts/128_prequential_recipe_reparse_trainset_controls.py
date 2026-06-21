from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

AUDIT_126 = HERE / "scripts" / "126_prequential_recipe_reparse_audit.py"
CONTROL_CUTOFFS = [50]
CONTROL_TRIALS = 12
RANDOM_SEED = 46920260620


def load_audit_126():
    spec = importlib.util.spec_from_file_location("prequential_recipe_reparse_audit", AUDIT_126)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {AUDIT_126}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def summarize(values: list[float], observed: float) -> dict[str, float | int]:
    return {
        "trials": len(values),
        "min": min(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "max": max(values),
        "p_control_ge_observed": (1 + sum(value >= observed for value in values)) / (len(values) + 1),
    }


def raw_uniform_bits(books: dict[str, str], test_books: list[int]) -> float:
    return sum(len(books[str(book)]) for book in test_books) * math.log2(10)


def train_counts_for_books(
    audit126,
    *,
    train_books: set[int],
    formula: dict[str, Any],
    copy_rows: list[dict[str, Any]],
    payload_rows: list[dict[str, Any]],
    item_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    item_model = formula["policy"]["item_type_model"]
    return {
        "copy": audit126.copy_counts([row for row in copy_rows if int(row["book_int"]) in train_books]),
        "payload": audit126.fixed_counts(
            [row for row in payload_rows if int(row["book_int"]) in train_books],
            alphabet=audit126.DIGITS,
            context_fn=lambda row: ("global", row["previous_digit_context"]),
            symbol_key="digit",
        ),
        "item": audit126.fixed_counts(
            [row for row in item_rows if int(row["book_int"]) in train_books],
            alphabet=audit126.ITEM_TYPES,
            context_fn=lambda row: audit126.item_context_key(item_model, int(row["book_int"])),
            symbol_key="item_type",
        ),
    }


def reparse_with_train_inventory(
    audit126,
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    train_order: list[int],
    test_order: list[int],
    train_counts: dict[str, Any],
) -> dict[str, Any]:
    available = "".join(books[str(book)] for book in train_order)
    totals = {
        "bits": 0.0,
        "literal_runs": 0,
        "literal_digits": 0,
        "copy_items": 0,
        "copied_digits": 0,
    }
    errors = []
    for book in test_order:
        encoded = audit126.encode_book_frozen_reparse(
            book=str(book),
            text=books[str(book)],
            available=available,
            formula=formula,
            train_counts=train_counts,
        )
        totals["bits"] += float(encoded["bits"])
        totals["literal_runs"] += int(encoded["literal_runs"])
        totals["literal_digits"] += int(encoded["literal_digits"])
        totals["copy_items"] += int(encoded["copy_items"])
        totals["copied_digits"] += int(encoded["copied_digits"])
        errors.extend(
            {"book": str(book), **error} if isinstance(error, dict) else {"book": str(book), "error": error}
            for error in encoded["validation"]["errors"]
        )
        available += books[str(book)]
    raw_bits = raw_uniform_bits(books, test_order)
    return {
        "test_books": test_order,
        "bits": totals["bits"],
        "raw_uniform_bits": raw_bits,
        "gain_vs_raw_bits": raw_bits - totals["bits"],
        "literal_runs": totals["literal_runs"],
        "literal_digits": totals["literal_digits"],
        "copy_items": totals["copy_items"],
        "copied_digits": totals["copied_digits"],
        "validation": {
            "books_roundtrip_ok": len(test_order) - len({row["book"] for row in errors}),
            "book_count": len(test_order),
            "errors": errors,
        },
    }


def main() -> None:
    audit126 = load_audit_126()
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    all_books = list(range(70))
    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = []
    for cutoff in CONTROL_CUTOFFS:
        observed_train = set(range(cutoff))
        observed_test = list(range(cutoff, 70))
        observed_counts = train_counts_for_books(
            audit126,
            train_books=observed_train,
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        observed = reparse_with_train_inventory(
            audit126,
            formula=formula,
            books=books,
            train_order=sorted(observed_train),
            test_order=observed_test,
            train_counts=observed_counts,
        )

        rng = random.Random(RANDOM_SEED + cutoff)
        control_gains = []
        control_examples = []
        roundtrip_failures = 0
        for trial in range(CONTROL_TRIALS):
            train = set(rng.sample(all_books, cutoff))
            test = sorted(set(all_books) - train)
            train_counts = train_counts_for_books(
                audit126,
                train_books=train,
                formula=formula,
                copy_rows=copy_rows,
                payload_rows=payload_rows,
                item_rows=item_rows,
            )
            control = reparse_with_train_inventory(
                audit126,
                formula=formula,
                books=books,
                train_order=sorted(train),
                test_order=test,
                train_counts=train_counts,
            )
            control_gains.append(float(control["gain_vs_raw_bits"]))
            if control["validation"]["books_roundtrip_ok"] != control["validation"]["book_count"]:
                roundtrip_failures += 1
            if len(control_examples) < 5:
                control_examples.append(
                    {
                        "trial": trial,
                        "train_books": sorted(train),
                        "test_book_count": len(test),
                        "gain_vs_raw_bits": control["gain_vs_raw_bits"],
                        "bits": control["bits"],
                    }
                )

        control_summary = summarize(control_gains, float(observed["gain_vs_raw_bits"]))
        rows.append(
            {
                "cutoff": cutoff,
                "observed_prefix": observed,
                "random_train_set_control": control_summary,
                "random_train_roundtrip_failures": roundtrip_failures,
                "control_examples": control_examples,
            }
        )

    numeric_prefix_beats_control_mean = all(
        row["observed_prefix"]["gain_vs_raw_bits"] > row["random_train_set_control"]["mean"]
        for row in rows
    )
    numeric_prefix_specific = all(
        row["random_train_set_control"]["p_control_ge_observed"] <= 1 / (CONTROL_TRIALS + 1)
        for row in rows
    )
    classification = (
        "recipe_reparse_numeric_prefix_specific"
        if numeric_prefix_beats_control_mean and numeric_prefix_specific
        else "recipe_reparse_predictive_not_numeric_prefix_specific"
    )

    result = {
        "schema": "prequential_recipe_reparse_trainset_controls.v1",
        "test": "128_prequential_recipe_reparse_trainset_controls",
        "classification": classification,
        "translation_delta": "NONE",
        "source_audit": rel(AUDIT_126),
        "control_cutoffs": CONTROL_CUTOFFS,
        "control_trials": CONTROL_TRIALS,
        "rows": rows,
        "summary": {
            "numeric_prefix_beats_control_mean_at_all_cutoffs": numeric_prefix_beats_control_mean,
            "numeric_prefix_specific_at_all_cutoffs": numeric_prefix_specific,
        },
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "translation_claim": False,
            "plaintext_claim": False,
            "case_reopened": False,
        },
    }

    lines = [
        "# 128. Prequential Recipe Reparse Train-Set Controls",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audits 126-127 show that deterministic frozen-count reparsing has a real",
        "suffix signal above content controls. This audit asks a different question:",
        "is the signal specific to numeric prefix -> future suffix, or do random",
        "same-size training inventories provide equal or better source material?",
        "",
        "This first control is intentionally focused on cutoff `50`, where the",
        "test suffix is still 20 books but the random-inventory DP controls are",
        "cheap enough to run repeatedly. The observed row uses train books",
        "`0..49` and tests `50..69`. Controls sample random same-size train sets,",
        "reparse the remaining books in numeric order, and keep the same parser",
        "and frozen component-count contract.",
        "",
        "## Result",
        "",
        "| Cutoff | Observed gain | Random mean gain | Random max gain | p(random >= observed) |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        control = row["random_train_set_control"]
        lines.append(
            f"| `{row['cutoff']}` | `{row['observed_prefix']['gain_vs_raw_bits']:.3f}` | "
            f"`{control['mean']:.3f}` | `{control['max']:.3f}` | "
            f"`{control['p_control_ge_observed']:.4f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This audit separates copy/reference predictability from numeric-order",
            "specificity. If random train inventories match or exceed the numeric",
            "prefix, the mechanism remains predictive but not evidence for numeric",
            "book order as an authorial generation order.",
            "",
            "This remains analysis-only. It does not lower `compression_bound`,",
            "derive `row0`, translate the books, or promote an authorial method.",
        ]
    )
    write_result("128_prequential_recipe_reparse_trainset_controls", result, lines)


if __name__ == "__main__":
    main()
