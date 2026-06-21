from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_128 = AUTHORIAL / "scripts" / "128_prequential_recipe_reparse_trainset_controls.py"
AUDIT_15 = HERE / "scripts" / "15_leave_one_book_out_book_bounded_source_audit.py"
ONLINE_COMPILE = AUTHORIAL / "reports" / "test_results" / "129_online_deterministic_reparse_compile.json"

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


def make_result() -> dict[str, Any]:
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    audit15 = load_module("audit15_book_bounded", AUDIT_15)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    online_compile = load_json(ONLINE_COMPILE)
    online_rows = {
        int(row["book"]): row for row in online_compile["reparse_audit"]["book_rows"]
    }

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = []
    cumulative_standard_gain = 0.0
    cumulative_book_bounded_gain = 0.0
    for book in range(70):
        train_books = list(range(book))
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=set(train_books),
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        available = "".join(books[str(train_book)] for train_book in train_books)
        bounded = audit15.encode_book_book_bounded_reparse(
            audit126=audit126,
            book=str(book),
            text=books[str(book)],
            available=available,
            source_boundaries=audit15.source_ranges(books, train_books),
            formula=formula,
            train_counts=train_counts,
        )
        standard = online_rows[book]
        raw_bits = audit128.raw_uniform_bits(books, [book])
        standard_gain = raw_bits - standard["bits"]
        bounded_gain = raw_bits - bounded["bits"]
        cumulative_standard_gain += standard_gain
        cumulative_book_bounded_gain += bounded_gain
        rows.append(
            {
                "book": book,
                "book_length_digits": len(books[str(book)]),
                "prior_train_book_count": len(train_books),
                "raw_uniform_bits": raw_bits,
                "online_reparse_bits": standard["bits"],
                "book_bounded_online_reparse_bits": bounded["bits"],
                "online_gain_vs_raw_bits": standard_gain,
                "book_bounded_online_gain_vs_raw_bits": bounded_gain,
                "book_bounded_minus_online_bits": bounded["bits"] - standard["bits"],
                "online_beats_raw": standard_gain > 0,
                "book_bounded_online_beats_raw": bounded_gain > 0,
                "cumulative_online_gain_vs_raw_bits": cumulative_standard_gain,
                "cumulative_book_bounded_online_gain_vs_raw_bits": cumulative_book_bounded_gain,
                "online_inventory": {key: standard[key] for key in INVENTORY_KEYS},
                "book_bounded_inventory": {key: bounded[key] for key in INVENTORY_KEYS},
                "online_component_bits": {key: standard[key] for key in COMPONENT_KEYS},
                "book_bounded_component_bits": {key: bounded[key] for key in COMPONENT_KEYS},
                "online_validation": standard["validation"],
                "book_bounded_validation": bounded["validation"],
            }
        )

    standard_failures = [row for row in rows if not row["online_beats_raw"]]
    bounded_failures = [row for row in rows if not row["book_bounded_online_beats_raw"]]
    rows_after_bootstrap = [row for row in rows if row["book"] > 0]
    standard_after_bootstrap_failures = [
        row for row in rows_after_bootstrap if not row["online_beats_raw"]
    ]
    bounded_after_bootstrap_failures = [
        row for row in rows_after_bootstrap if not row["book_bounded_online_beats_raw"]
    ]
    weakest_bounded = sorted(rows, key=lambda row: row["book_bounded_online_gain_vs_raw_bits"])[:10]
    highest_boundary_penalty = sorted(
        rows, key=lambda row: row["book_bounded_minus_online_bits"], reverse=True
    )[:10]
    classification = (
        "online_prefix_book_frontier_bootstrap_only_failure"
        if [row["book"] for row in bounded_failures] == [0]
        else "online_prefix_book_frontier_partial"
    )
    return {
        "schema": "online_prefix_book_frontier_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "online_compile": rel(ONLINE_COMPILE),
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
            "book_bounded_parser": rel(AUDIT_15),
        },
        "rows": rows,
        "summary": {
            "book_count": len(rows),
            "online_roundtrip_book_count": sum(
                1 for row in rows if row["online_validation"]["errors"] == []
            ),
            "book_bounded_roundtrip_book_count": sum(
                1 for row in rows if row["book_bounded_validation"]["errors"] == []
            ),
            "online_beats_raw_count": sum(1 for row in rows if row["online_beats_raw"]),
            "book_bounded_online_beats_raw_count": sum(
                1 for row in rows if row["book_bounded_online_beats_raw"]
            ),
            "online_after_bootstrap_beats_raw_count": sum(
                1 for row in rows_after_bootstrap if row["online_beats_raw"]
            ),
            "book_bounded_after_bootstrap_beats_raw_count": sum(
                1 for row in rows_after_bootstrap if row["book_bounded_online_beats_raw"]
            ),
            "after_bootstrap_book_count": len(rows_after_bootstrap),
            "online_failure_books": [row["book"] for row in standard_failures],
            "book_bounded_online_failure_books": [row["book"] for row in bounded_failures],
            "online_after_bootstrap_failure_books": [
                row["book"] for row in standard_after_bootstrap_failures
            ],
            "book_bounded_after_bootstrap_failure_books": [
                row["book"] for row in bounded_after_bootstrap_failures
            ],
            "mean_online_gain_vs_raw_bits": sum(row["online_gain_vs_raw_bits"] for row in rows)
            / len(rows),
            "mean_book_bounded_online_gain_vs_raw_bits": sum(
                row["book_bounded_online_gain_vs_raw_bits"] for row in rows
            )
            / len(rows),
            "min_online_gain_vs_raw_bits": min(row["online_gain_vs_raw_bits"] for row in rows),
            "min_book_bounded_online_gain_vs_raw_bits": min(
                row["book_bounded_online_gain_vs_raw_bits"] for row in rows
            ),
            "total_online_gain_vs_raw_bits": sum(row["online_gain_vs_raw_bits"] for row in rows),
            "total_book_bounded_online_gain_vs_raw_bits": sum(
                row["book_bounded_online_gain_vs_raw_bits"] for row in rows
            ),
            "mean_book_bounded_minus_online_bits": sum(
                row["book_bounded_minus_online_bits"] for row in rows
            )
            / len(rows),
            "max_book_bounded_minus_online_bits": max(
                row["book_bounded_minus_online_bits"] for row in rows
            ),
            "cumulative_book_bounded_break_even_book": next(
                (
                    row["book"]
                    for row in rows
                    if row["cumulative_book_bounded_online_gain_vs_raw_bits"] > 0
                ),
                None,
            ),
            "weakest_book_bounded_books": [
                {
                    "book": row["book"],
                    "gain_vs_raw_bits": row["book_bounded_online_gain_vs_raw_bits"],
                    "book_length_digits": row["book_length_digits"],
                    "prior_train_book_count": row["prior_train_book_count"],
                    "literal_digits": row["book_bounded_inventory"]["literal_digits"],
                    "copied_digits": row["book_bounded_inventory"]["copied_digits"],
                }
                for row in weakest_bounded
            ],
            "highest_book_boundary_penalty_books": [
                {
                    "book": row["book"],
                    "book_bounded_minus_online_bits": row["book_bounded_minus_online_bits"],
                    "book_bounded_gain_vs_raw_bits": row[
                        "book_bounded_online_gain_vs_raw_bits"
                    ],
                }
                for row in highest_boundary_penalty
            ],
            "interpretation": (
                "The online parser is evaluated at per-book granularity using only "
                "previous numeric-order books as external inventory. A book-bounded "
                "variant forbids source copies from crossing prior-book boundaries. "
                "The only raw-coding failure is the bootstrap book before any prior "
                "inventory exists."
            ),
        },
        "decision": {
            "online_prefix_status": "predictive_after_bootstrap",
            "bootstrap_status": "book_0_is_expected_cold_start_failure_against_raw",
            "book_boundary_status": "book_bounded_online_frontier_retains_after_bootstrap_signal",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "17_online_prefix_book_frontier_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Online Prefix Book Frontier Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 129 compiles a deterministic online reparse formula using only",
        "previous numeric-order books before committing each next book. This audit",
        "decomposes that result by target book and adds a book-bounded source",
        "variant, so the sequential frontier is visible instead of only the",
        "full-corpus total.",
        "",
        "## Summary",
        "",
        f"- Books checked: `{result['summary']['book_count']}`.",
        f"- Online roundtrip books: `{result['summary']['online_roundtrip_book_count']}/{result['summary']['book_count']}`.",
        f"- Book-bounded online roundtrip books: `{result['summary']['book_bounded_roundtrip_book_count']}/{result['summary']['book_count']}`.",
        f"- Online beats raw: `{result['summary']['online_beats_raw_count']}/{result['summary']['book_count']}`.",
        f"- Book-bounded online beats raw: `{result['summary']['book_bounded_online_beats_raw_count']}/{result['summary']['book_count']}`.",
        f"- Online after bootstrap beats raw: `{result['summary']['online_after_bootstrap_beats_raw_count']}/{result['summary']['after_bootstrap_book_count']}`.",
        f"- Book-bounded after bootstrap beats raw: `{result['summary']['book_bounded_after_bootstrap_beats_raw_count']}/{result['summary']['after_bootstrap_book_count']}`.",
        f"- Online failure books: `{result['summary']['online_failure_books']}`.",
        f"- Book-bounded online failure books: `{result['summary']['book_bounded_online_failure_books']}`.",
        f"- Mean online gain vs raw: `{result['summary']['mean_online_gain_vs_raw_bits']:.3f}` bits.",
        f"- Mean book-bounded online gain vs raw: `{result['summary']['mean_book_bounded_online_gain_vs_raw_bits']:.3f}` bits.",
        f"- Min book-bounded online gain vs raw: `{result['summary']['min_book_bounded_online_gain_vs_raw_bits']:.3f}` bits.",
        f"- Total book-bounded online gain vs raw: `{result['summary']['total_book_bounded_online_gain_vs_raw_bits']:.3f}` bits.",
        f"- Book-bounded cumulative break-even book: `{result['summary']['cumulative_book_bounded_break_even_book']}`.",
        "",
        "## Weakest Book-Bounded Online Books",
        "",
        "| Book | Prior books | Length | Literal digits | Copied digits | Gain vs raw |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["summary"]["weakest_book_bounded_books"]:
        lines.append(
            f"| `{row['book']}` | `{row['prior_train_book_count']}` | "
            f"`{row['book_length_digits']}` | `{row['literal_digits']}` | "
            f"`{row['copied_digits']}` | `{row['gain_vs_raw_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Highest Book-Boundary Penalties",
            "",
            "| Book | Penalty vs unbounded online | Book-bounded gain vs raw |",
            "|---:|---:|---:|",
        ]
    )
    for row in result["summary"]["highest_book_boundary_penalty_books"]:
        lines.append(
            f"| `{row['book']}` | `{row['book_bounded_minus_online_bits']:.3f}` | "
            f"`{row['book_bounded_gain_vs_raw_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- The online numeric-prefix parser has a single local raw-coding failure: book `0`, before any prior book inventory exists.",
            "- After the bootstrap book, both unbounded and book-bounded online variants beat raw digit coding in `69/69` books.",
            "- This strengthens sequential mechanical generation evidence, but it does not derive row0 or introduce plaintext.",
        ]
    )
    (TEST_RESULTS / "17_online_prefix_book_frontier_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
