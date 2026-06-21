from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUDIT_12 = HERE / "scripts" / "12_family_holdout_no_test_carryover_audit.py"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_128 = AUTHORIAL / "scripts" / "128_prequential_recipe_reparse_trainset_controls.py"


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
    audit12 = load_module("audit12_no_test_carryover", AUDIT_12)
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    all_books = set(range(70))

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = []
    for book in range(70):
        train_books = sorted(all_books - {book})
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=set(train_books),
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        reparse = audit12.reparse_no_test_carryover(
            audit126=audit126,
            formula=formula,
            books=books,
            train_books=train_books,
            test_books=[book],
            train_counts=train_counts,
        )
        raw_bits = audit128.raw_uniform_bits(books, [book])
        bits = reparse["totals"]["bits"]
        gain = raw_bits - bits
        rows.append(
            {
                "book": book,
                "book_length_digits": len(books[str(book)]),
                "raw_uniform_bits": raw_bits,
                "leave_one_out_reparse_bits": bits,
                "gain_vs_raw_bits": gain,
                "beats_raw": gain > 0,
                "validation": reparse["totals"]["validation"],
                "inventory": {
                    key: reparse["totals"][key]
                    for key in audit12.INVENTORY_KEYS
                },
                "component_bits": {
                    key: reparse["totals"][key]
                    for key in audit12.COMPONENT_KEYS
                },
            }
        )

    failures = [row for row in rows if not row["beats_raw"]]
    weakest = sorted(rows, key=lambda row: row["gain_vs_raw_bits"])[:10]
    classification = (
        "leave_one_book_out_no_self_predictive"
        if not failures
        else "leave_one_book_out_no_self_partial"
    )
    return {
        "schema": "leave_one_book_out_no_self_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
            "no_test_carryover_helper": rel(AUDIT_12),
        },
        "rows": rows,
        "summary": {
            "book_count": len(rows),
            "roundtrip_book_count": sum(1 for row in rows if row["validation"]["errors"] == []),
            "beats_raw_count": sum(1 for row in rows if row["beats_raw"]),
            "failure_books": [row["book"] for row in failures],
            "mean_gain_vs_raw_bits": sum(row["gain_vs_raw_bits"] for row in rows) / len(rows),
            "min_gain_vs_raw_bits": min(row["gain_vs_raw_bits"] for row in rows),
            "max_gain_vs_raw_bits": max(row["gain_vs_raw_bits"] for row in rows),
            "mean_reparse_bits": sum(row["leave_one_out_reparse_bits"] for row in rows)
            / len(rows),
            "weakest_books": [
                {
                    "book": row["book"],
                    "gain_vs_raw_bits": row["gain_vs_raw_bits"],
                    "book_length_digits": row["book_length_digits"],
                }
                for row in weakest
            ],
            "interpretation": (
                "At singleton granularity, every book roundtrips and beats raw "
                "digit coding when the parser can use only the other 69 books as "
                "inventory. This strengthens mutual mechanical redundancy evidence "
                "without proving an authorial order or row0 origin."
            ),
        },
        "decision": {
            "singleton_holdout_status": "predictive_signal_retained_without_self",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "13_leave_one_book_out_no_self_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Leave-One-Book-Out No-Self Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This audit tests singleton holdout granularity. Each book is reparsed",
        "using the other `69` books as the preloaded inventory. The held-out",
        "book itself is not preloaded; as in sequential decoding, its current",
        "prefix may become available after emission.",
        "",
        "## Summary",
        "",
        f"- Books checked: `{result['summary']['book_count']}`.",
        f"- Roundtrip books: `{result['summary']['roundtrip_book_count']}/{result['summary']['book_count']}`.",
        f"- Beats raw digits: `{result['summary']['beats_raw_count']}/{result['summary']['book_count']}`.",
        f"- Mean gain vs raw: `{result['summary']['mean_gain_vs_raw_bits']:.3f}` bits.",
        f"- Min gain vs raw: `{result['summary']['min_gain_vs_raw_bits']:.3f}` bits.",
        f"- Max gain vs raw: `{result['summary']['max_gain_vs_raw_bits']:.3f}` bits.",
        f"- Failure books: `{result['summary']['failure_books']}`.",
        "",
        "## Weakest Books",
        "",
        "| Book | Length | Gain vs raw |",
        "|---:|---:|---:|",
    ]
    for row in result["summary"]["weakest_books"]:
        lines.append(
            f"| `{row['book']}` | `{row['book_length_digits']}` | "
            f"`{row['gain_vs_raw_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| Book | Length | Reparse bits | Raw bits | Gain vs raw | Beats raw |",
            "|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in result["rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['book_length_digits']}` | "
            f"`{row['leave_one_out_reparse_bits']:.3f}` | "
            f"`{row['raw_uniform_bits']:.3f}` | "
            f"`{row['gain_vs_raw_bits']:.3f}` | `{row['beats_raw']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Every individual book is mechanically reparseable from the other 69 preloaded books, plus any current prefix emitted during sequential decoding, with positive gain over raw digit coding.",
            "- This strengthens item-level predictive redundancy, but it uses complement inventory and is not an authorial order proof.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "13_leave_one_book_out_no_self_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
