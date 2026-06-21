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
AUDIT_15 = HERE / "scripts" / "15_leave_one_book_out_book_bounded_source_audit.py"
BOOK_BOUNDED = TEST_RESULTS / "15_leave_one_book_out_book_bounded_source_audit.json"

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


def book_family_index(families: dict[str, set[int]]) -> dict[int, list[str]]:
    by_book: dict[int, list[str]] = {}
    for label, books in sorted(families.items()):
        for book in sorted(books):
            by_book.setdefault(book, []).append(label)
    return by_book


def make_result() -> dict[str, Any]:
    audit125 = load_module("audit125_prequential_row0", AUDIT_125)
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    audit15 = load_module("audit15_book_bounded", AUDIT_15)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    book_bounded = load_json(BOOK_BOUNDED)
    book_bounded_by_book = {row["book"]: row for row in book_bounded["rows"]}
    families = audit125.load_bookcase_families()
    family_by_book = book_family_index(families)
    all_books = set(range(70))

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = []
    for book in range(70):
        labels = family_by_book.get(book, [])
        excluded_books = {book}
        for label in labels:
            excluded_books.update(families[label])
        train_books = sorted(all_books - excluded_books)
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=set(train_books),
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        available = "".join(books[str(train_book)] for train_book in train_books)
        encoded = audit15.encode_book_book_bounded_reparse(
            audit126=audit126,
            book=str(book),
            text=books[str(book)],
            available=available,
            source_boundaries=audit15.source_ranges(books, train_books),
            formula=formula,
            train_counts=train_counts,
        )
        raw_bits = audit128.raw_uniform_bits(books, [book])
        gain = raw_bits - encoded["bits"]
        baseline = book_bounded_by_book[book]
        rows.append(
            {
                "book": book,
                "book_length_digits": len(books[str(book)]),
                "family_labels": labels,
                "excluded_books": sorted(excluded_books),
                "excluded_peer_books": sorted(set(excluded_books) - {book}),
                "train_book_count": len(train_books),
                "raw_uniform_bits": raw_bits,
                "family_excluded_reparse_bits": encoded["bits"],
                "book_bounded_reparse_bits": baseline["book_bounded_reparse_bits"],
                "family_excluded_gain_vs_raw_bits": gain,
                "book_bounded_gain_vs_raw_bits": baseline["book_bounded_gain_vs_raw_bits"],
                "family_excluded_minus_book_bounded_bits": encoded["bits"]
                - baseline["book_bounded_reparse_bits"],
                "beats_raw": gain > 0,
                "validation": encoded["validation"],
                "inventory": {key: encoded[key] for key in INVENTORY_KEYS},
                "component_bits": {key: encoded[key] for key in COMPONENT_KEYS},
            }
        )

    failures = [row for row in rows if not row["beats_raw"]]
    family_rows = [row for row in rows if row["family_labels"]]
    family_failures = [row for row in family_rows if not row["beats_raw"]]
    weakest = sorted(rows, key=lambda row: row["family_excluded_gain_vs_raw_bits"])[:10]
    highest_penalty = sorted(
        rows, key=lambda row: row["family_excluded_minus_book_bounded_bits"], reverse=True
    )[:10]
    classification = (
        "family_excluded_singleton_holdout_predictive"
        if not failures
        else "family_excluded_singleton_holdout_partial"
    )
    return {
        "schema": "leave_one_book_out_family_excluded_source_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "families": rel(AUDIT_125),
            "book_bounded_singleton": rel(BOOK_BOUNDED),
            "book_bounded_parser": rel(AUDIT_15),
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
        },
        "rows": rows,
        "summary": {
            "book_count": len(rows),
            "family_labeled_book_count": len(family_rows),
            "roundtrip_book_count": sum(1 for row in rows if row["validation"]["errors"] == []),
            "beats_raw_count": sum(1 for row in rows if row["beats_raw"]),
            "family_labeled_beats_raw_count": sum(1 for row in family_rows if row["beats_raw"]),
            "failure_books": [row["book"] for row in failures],
            "family_labeled_failure_books": [row["book"] for row in family_failures],
            "mean_family_excluded_gain_vs_raw_bits": sum(
                row["family_excluded_gain_vs_raw_bits"] for row in rows
            )
            / len(rows),
            "min_family_excluded_gain_vs_raw_bits": min(
                row["family_excluded_gain_vs_raw_bits"] for row in rows
            ),
            "mean_family_excluded_minus_book_bounded_bits": sum(
                row["family_excluded_minus_book_bounded_bits"] for row in rows
            )
            / len(rows),
            "max_family_excluded_minus_book_bounded_bits": max(
                row["family_excluded_minus_book_bounded_bits"] for row in rows
            ),
            "mean_family_labeled_gain_vs_raw_bits": (
                sum(row["family_excluded_gain_vs_raw_bits"] for row in family_rows)
                / len(family_rows)
                if family_rows
                else None
            ),
            "min_family_labeled_gain_vs_raw_bits": (
                min(row["family_excluded_gain_vs_raw_bits"] for row in family_rows)
                if family_rows
                else None
            ),
            "weakest_books": [
                {
                    "book": row["book"],
                    "family_labels": row["family_labels"],
                    "excluded_peer_books": row["excluded_peer_books"],
                    "gain_vs_raw_bits": row["family_excluded_gain_vs_raw_bits"],
                    "book_length_digits": row["book_length_digits"],
                }
                for row in weakest
            ],
            "highest_family_exclusion_penalty_books": [
                {
                    "book": row["book"],
                    "family_labels": row["family_labels"],
                    "excluded_peer_books": row["excluded_peer_books"],
                    "family_excluded_minus_book_bounded_bits": row[
                        "family_excluded_minus_book_bounded_bits"
                    ],
                    "family_excluded_gain_vs_raw_bits": row[
                        "family_excluded_gain_vs_raw_bits"
                    ],
                }
                for row in highest_penalty
            ],
            "interpretation": (
                "Each book is reparsed independently from a book-bounded source "
                "inventory. For books with a public-bookcase family label, every "
                "book from that same family is removed from both frozen train "
                "counts and copy sources. Positive gains test whether singleton "
                "prediction depends on same-family memorization."
            ),
        },
        "decision": {
            "same_family_source_status": "predictive_signal_retained_without_same_family_sources"
            if not failures
            else "predictive_signal_partial_without_same_family_sources",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "16_leave_one_book_out_family_excluded_source_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Leave-One-Book-Out Family-Excluded Source Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 15 showed that singleton reparsing does not depend on copy sources",
        "crossing artificial source-book boundaries. This audit asks a harder",
        "source question: when a target book belongs to a known public-bookcase",
        "family, remove that entire family from both frozen train counts and copy",
        "sources before reparsing the target book.",
        "",
        "Current-prefix copies remain legal if they stay inside the already-emitted",
        "target prefix; the tested leakage is same-family source inventory.",
        "",
        "## Summary",
        "",
        f"- Books checked: `{result['summary']['book_count']}`.",
        f"- Family-labeled books: `{result['summary']['family_labeled_book_count']}`.",
        f"- Roundtrip books: `{result['summary']['roundtrip_book_count']}/{result['summary']['book_count']}`.",
        f"- Beats raw digits: `{result['summary']['beats_raw_count']}/{result['summary']['book_count']}`.",
        f"- Family-labeled beats raw: `{result['summary']['family_labeled_beats_raw_count']}/{result['summary']['family_labeled_book_count']}`.",
        f"- Mean family-excluded gain vs raw: `{result['summary']['mean_family_excluded_gain_vs_raw_bits']:.3f}` bits.",
        f"- Min family-excluded gain vs raw: `{result['summary']['min_family_excluded_gain_vs_raw_bits']:.3f}` bits.",
        f"- Mean family-excluded minus book-bounded: `{result['summary']['mean_family_excluded_minus_book_bounded_bits']:.3f}` bits.",
        f"- Max family-excluded minus book-bounded: `{result['summary']['max_family_excluded_minus_book_bounded_bits']:.3f}` bits.",
        f"- Failure books: `{result['summary']['failure_books']}`.",
        "",
        "## Weakest Books",
        "",
        "| Book | Families | Excluded peers | Length | Family-excluded gain vs raw |",
        "|---:|---|---|---:|---:|",
    ]
    for row in result["summary"]["weakest_books"]:
        lines.append(
            f"| `{row['book']}` | `{row['family_labels']}` | `{row['excluded_peer_books']}` | "
            f"`{row['book_length_digits']}` | `{row['gain_vs_raw_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Highest Family-Exclusion Penalties",
            "",
            "| Book | Families | Excluded peers | Penalty vs book-bounded | Family-excluded gain vs raw |",
            "|---:|---|---|---:|---:|",
        ]
    )
    for row in result["summary"]["highest_family_exclusion_penalty_books"]:
        lines.append(
            f"| `{row['book']}` | `{row['family_labels']}` | `{row['excluded_peer_books']}` | "
            f"`{row['family_excluded_minus_book_bounded_bits']:.3f}` | "
            f"`{row['family_excluded_gain_vs_raw_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The singleton holdout is retested after removing same-family books from train counts and copy sources.",
            "- The result is evidence about source dependency only; it does not derive row0 or promote a final authorial method.",
            "- No plaintext, translation, row0-origin change, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "16_leave_one_book_out_family_excluded_source_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
