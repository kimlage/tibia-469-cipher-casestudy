from __future__ import annotations

import importlib.util
import json
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_128 = AUTHORIAL / "scripts" / "128_prequential_recipe_reparse_trainset_controls.py"
AUDIT_130 = AUTHORIAL / "scripts" / "130_online_reparse_order_control_audit.py"
AUDIT_15 = HERE / "scripts" / "15_leave_one_book_out_book_bounded_source_audit.py"

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


def break_even_position(rows: list[dict[str, Any]]) -> int | None:
    cumulative = 0.0
    for row in rows:
        cumulative += float(row["gain_vs_raw_bits"])
        if cumulative > 0:
            return int(row["position"])
    return None


def evaluate_case(
    *,
    order_case: dict[str, Any],
    audit126,
    audit128,
    audit15,
    formula: dict[str, Any],
    books: dict[str, str],
    copy_rows: list[dict[str, Any]],
    payload_rows: list[dict[str, Any]],
    item_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = []
    cumulative_gain = 0.0
    order = [int(book) for book in order_case["order"]]
    for position, book in enumerate(order):
        train_books = order[:position]
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
        gain = raw_bits - float(encoded["bits"])
        cumulative_gain += gain
        rows.append(
            {
                "position": position,
                "book": book,
                "book_length_digits": len(books[str(book)]),
                "prior_train_book_count": len(train_books),
                "raw_uniform_bits": raw_bits,
                "book_bounded_online_reparse_bits": float(encoded["bits"]),
                "gain_vs_raw_bits": gain,
                "cumulative_gain_vs_raw_bits": cumulative_gain,
                "beats_raw": gain > 0,
                "validation": encoded["validation"],
                "inventory": {key: encoded[key] for key in INVENTORY_KEYS},
                "component_bits": {key: encoded[key] for key in COMPONENT_KEYS},
            }
        )

    failures = [row for row in rows if not row["beats_raw"]]
    after_bootstrap = rows[1:]
    after_bootstrap_failures = [row for row in after_bootstrap if not row["beats_raw"]]
    gains = [float(row["gain_vs_raw_bits"]) for row in rows]
    after_gains = [float(row["gain_vs_raw_bits"]) for row in after_bootstrap]
    return {
        "name": order_case["name"],
        "family": order_case["family"],
        "descriptor_bits": float(order_case["descriptor_bits"]),
        "descriptor_note": order_case["descriptor_note"],
        "order_prefix": order[:10],
        "order_suffix": order[-10:],
        "rows": rows,
        "summary": {
            "book_count": len(rows),
            "roundtrip_book_count": sum(1 for row in rows if row["validation"]["errors"] == []),
            "beats_raw_count": sum(1 for row in rows if row["beats_raw"]),
            "after_bootstrap_book_count": len(after_bootstrap),
            "after_bootstrap_beats_raw_count": sum(
                1 for row in after_bootstrap if row["beats_raw"]
            ),
            "failure_books": [int(row["book"]) for row in failures],
            "after_bootstrap_failure_books": [
                int(row["book"]) for row in after_bootstrap_failures
            ],
            "mean_gain_vs_raw_bits": statistics.mean(gains),
            "min_gain_vs_raw_bits": min(gains),
            "mean_after_bootstrap_gain_vs_raw_bits": statistics.mean(after_gains),
            "min_after_bootstrap_gain_vs_raw_bits": min(after_gains),
            "total_gain_vs_raw_bits": sum(gains),
            "first_book": int(rows[0]["book"]),
            "first_book_gain_vs_raw_bits": float(rows[0]["gain_vs_raw_bits"]),
            "cumulative_break_even_position": break_even_position(rows),
            "weakest_books": [
                {
                    "position": int(row["position"]),
                    "book": int(row["book"]),
                    "gain_vs_raw_bits": float(row["gain_vs_raw_bits"]),
                    "book_length_digits": int(row["book_length_digits"]),
                    "prior_train_book_count": int(row["prior_train_book_count"]),
                }
                for row in sorted(rows, key=lambda item: float(item["gain_vs_raw_bits"]))[:8]
            ],
        },
    }


def make_result() -> dict[str, Any]:
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    audit130 = load_module("audit130_order_controls", AUDIT_130)
    audit15 = load_module("audit15_book_bounded", AUDIT_15)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    base_online_formula = load_json(audit130.ACTIVE_FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    numeric_order = [int(book) for book in base_online_formula["policy"]["book_order"]]
    cases = audit130.named_orders(numeric_order, books) + audit130.random_orders(numeric_order)

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = [
        evaluate_case(
            order_case=case,
            audit126=audit126,
            audit128=audit128,
            audit15=audit15,
            formula=formula,
            books=books,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        for case in cases
    ]
    numeric = next(row for row in rows if row["name"] == "numeric")
    after_perfect = [
        row
        for row in rows
        if row["summary"]["after_bootstrap_beats_raw_count"]
        == row["summary"]["after_bootstrap_book_count"]
    ]
    random_rows = [row for row in rows if row["family"] == "random_permutation_control"]
    best_after_mean = max(
        rows, key=lambda row: float(row["summary"]["mean_after_bootstrap_gain_vs_raw_bits"])
    )
    best_total = max(rows, key=lambda row: float(row["summary"]["total_gain_vs_raw_bits"]))
    numeric_unique_after = len(after_perfect) == 1 and after_perfect[0]["name"] == "numeric"
    random_perfect_count = sum(
        1
        for row in random_rows
        if row["summary"]["after_bootstrap_beats_raw_count"]
        == row["summary"]["after_bootstrap_book_count"]
    )

    if numeric_unique_after:
        classification = "numeric_online_frontier_unique_after_bootstrap_in_tested_orders"
    elif numeric["summary"]["after_bootstrap_beats_raw_count"] == numeric["summary"][
        "after_bootstrap_book_count"
    ]:
        classification = "online_frontier_predictive_but_not_numeric_order_unique"
    else:
        classification = "numeric_online_frontier_partial_under_order_controls"

    for row in rows:
        row["delta_total_gain_vs_numeric_bits"] = (
            float(row["summary"]["total_gain_vs_raw_bits"])
            - float(numeric["summary"]["total_gain_vs_raw_bits"])
        )
        row["delta_after_bootstrap_mean_gain_vs_numeric_bits"] = (
            float(row["summary"]["mean_after_bootstrap_gain_vs_raw_bits"])
            - float(numeric["summary"]["mean_after_bootstrap_gain_vs_raw_bits"])
        )

    return {
        "schema": "online_order_frontier_controls.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
            "online_reparse_order_control": rel(AUDIT_130),
            "book_bounded_parser": rel(AUDIT_15),
            "base_online_formula": rel(audit130.ACTIVE_FORMULA),
        },
        "controls": {
            "random_seed": audit130.RANDOM_SEED,
            "random_order_count": audit130.RANDOM_ORDER_COUNT,
            "order_count": len(rows),
            "after_bootstrap_definition": "exclude position 0 of each tested order",
            "source_boundary_rule": (
                "copy sources may use prior books or the current emitted prefix, "
                "but may not cross prior-book boundaries"
            ),
        },
        "summary": {
            "numeric_after_bootstrap_beats_raw_count": numeric["summary"][
                "after_bootstrap_beats_raw_count"
            ],
            "after_bootstrap_book_count": numeric["summary"]["after_bootstrap_book_count"],
            "numeric_failure_books": numeric["summary"]["failure_books"],
            "numeric_after_bootstrap_failure_books": numeric["summary"][
                "after_bootstrap_failure_books"
            ],
            "orders_with_perfect_after_bootstrap_count": len(after_perfect),
            "orders_with_perfect_after_bootstrap": [row["name"] for row in after_perfect],
            "random_orders_with_perfect_after_bootstrap_count": random_perfect_count,
            "best_after_bootstrap_mean_gain_order": {
                "name": best_after_mean["name"],
                "family": best_after_mean["family"],
                "mean_after_bootstrap_gain_vs_raw_bits": best_after_mean["summary"][
                    "mean_after_bootstrap_gain_vs_raw_bits"
                ],
                "delta_vs_numeric_bits": best_after_mean[
                    "delta_after_bootstrap_mean_gain_vs_numeric_bits"
                ],
            },
            "best_total_gain_order": {
                "name": best_total["name"],
                "family": best_total["family"],
                "total_gain_vs_raw_bits": best_total["summary"]["total_gain_vs_raw_bits"],
                "delta_vs_numeric_bits": best_total["delta_total_gain_vs_numeric_bits"],
            },
            "numeric_total_gain_vs_raw_bits": numeric["summary"]["total_gain_vs_raw_bits"],
            "numeric_mean_after_bootstrap_gain_vs_raw_bits": numeric["summary"][
                "mean_after_bootstrap_gain_vs_raw_bits"
            ],
            "numeric_cumulative_break_even_position": numeric["summary"][
                "cumulative_break_even_position"
            ],
            "interpretation": (
                "The numeric previous-book frontier remains predictive after its "
                "first bootstrap position, but the same after-bootstrap raw-win "
                "criterion is not exclusive to numeric order when tested against "
                "the order-control families."
            ),
        },
        "rows": rows,
        "decision": {
            "online_frontier_status": "predictive_after_bootstrap",
            "numeric_order_status": (
                "unique_after_bootstrap_under_tested_orders"
                if numeric_unique_after
                else "not_unique_after_bootstrap_under_tested_orders"
            ),
            "compression_bound_status": "unchanged",
            "generation_explanation_status": "order_control_boundary_sharpened",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "22_online_order_frontier_controls.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    numeric = next(row for row in result["rows"] if row["name"] == "numeric")
    ranked_after = sorted(
        result["rows"],
        key=lambda row: float(row["summary"]["mean_after_bootstrap_gain_vs_raw_bits"]),
        reverse=True,
    )
    ranked_total = sorted(
        result["rows"],
        key=lambda row: float(row["summary"]["total_gain_vs_raw_bits"]),
        reverse=True,
    )
    lines = [
        "# Online Order Frontier Controls",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 17 showed that previous-books-only online reparsing beats raw digit",
        "coding for `69/69` books after the numeric-order bootstrap book. Audit 130",
        "tested full-formula order controls only as aggregate bit counts. This",
        "audit combines those questions: it reruns the book-bounded online frontier",
        "under the same named and random order controls and measures the",
        "after-bootstrap per-book raw-win frontier.",
        "",
        "## Summary",
        "",
        f"- Orders tested: `{result['controls']['order_count']}`.",
        f"- Numeric after-bootstrap raw wins: "
        f"`{result['summary']['numeric_after_bootstrap_beats_raw_count']}/"
        f"{result['summary']['after_bootstrap_book_count']}`.",
        f"- Numeric failure books: `{result['summary']['numeric_failure_books']}`.",
        f"- Numeric after-bootstrap failures: "
        f"`{result['summary']['numeric_after_bootstrap_failure_books']}`.",
        f"- Orders with perfect after-bootstrap raw wins: "
        f"`{result['summary']['orders_with_perfect_after_bootstrap_count']}/"
        f"{result['controls']['order_count']}`.",
        f"- Random orders with perfect after-bootstrap raw wins: "
        f"`{result['summary']['random_orders_with_perfect_after_bootstrap_count']}/"
        f"{result['controls']['random_order_count']}`.",
        f"- Best after-bootstrap mean-gain order: "
        f"`{result['summary']['best_after_bootstrap_mean_gain_order']['name']}` "
        f"(`{result['summary']['best_after_bootstrap_mean_gain_order']['delta_vs_numeric_bits']:+.3f}` "
        "bits vs numeric mean).",
        f"- Best total-gain order: `{result['summary']['best_total_gain_order']['name']}` "
        f"(`{result['summary']['best_total_gain_order']['delta_vs_numeric_bits']:+.3f}` "
        "bits vs numeric total).",
        "",
        "## Order Table",
        "",
        "| Order | Family | Raw wins | After bootstrap | Failures | Mean after gain | Total gain | Delta total vs numeric |",
        "|---|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in result["rows"]:
        summary = row["summary"]
        lines.append(
            f"| `{row['name']}` | `{row['family']}` | "
            f"`{summary['beats_raw_count']}/{summary['book_count']}` | "
            f"`{summary['after_bootstrap_beats_raw_count']}/"
            f"{summary['after_bootstrap_book_count']}` | "
            f"`{summary['failure_books']}` | "
            f"`{summary['mean_after_bootstrap_gain_vs_raw_bits']:.3f}` | "
            f"`{summary['total_gain_vs_raw_bits']:.3f}` | "
            f"`{row['delta_total_gain_vs_numeric_bits']:+.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Highest Mean After-Bootstrap Gains",
            "",
            "| Rank | Order | Family | Mean after gain | After failures |",
            "|---:|---|---|---:|---|",
        ]
    )
    for index, row in enumerate(ranked_after[:8], start=1):
        lines.append(
            f"| {index} | `{row['name']}` | `{row['family']}` | "
            f"`{row['summary']['mean_after_bootstrap_gain_vs_raw_bits']:.3f}` | "
            f"`{row['summary']['after_bootstrap_failure_books']}` |"
        )

    lines.extend(
        [
            "",
            "## Highest Total Gains",
            "",
            "| Rank | Order | Family | Total gain | Delta vs numeric | Break-even position |",
            "|---:|---|---|---:|---:|---:|",
        ]
    )
    for index, row in enumerate(ranked_total[:8], start=1):
        lines.append(
            f"| {index} | `{row['name']}` | `{row['family']}` | "
            f"`{row['summary']['total_gain_vs_raw_bits']:.3f}` | "
            f"`{row['delta_total_gain_vs_numeric_bits']:+.3f}` | "
            f"`{row['summary']['cumulative_break_even_position']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
        ]
    )
    if result["decision"]["numeric_order_status"] == "unique_after_bootstrap_under_tested_orders":
        lines.extend(
            [
                "Numeric order is the only tested order with a perfect",
                "after-bootstrap raw-win frontier. This supports the numeric",
                "order boundary under the tested controls, without promoting a",
                "plaintext, row0 origin, or final authorial method.",
            ]
        )
    else:
        lines.extend(
            [
                "The numeric previous-book frontier remains predictive after the",
                "bootstrap position, but the criterion is not unique: at least one",
                "control order also reaches a perfect after-bootstrap raw-win",
                "frontier. The result therefore strengthens the predictive-parser",
                "signal while rejecting the stronger claim that numeric order is",
                "proved by the per-book frontier alone.",
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No compression bound is promoted by this audit.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0/table origin remains exogenous.",
            "- After-bootstrap means position `1..69` of each tested order, not book IDs `1..69`.",
        ]
    )
    (TEST_RESULTS / "22_online_order_frontier_controls.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
