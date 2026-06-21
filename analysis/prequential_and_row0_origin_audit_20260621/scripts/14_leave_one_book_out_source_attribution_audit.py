from __future__ import annotations

import bisect
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_128 = AUTHORIAL / "scripts" / "128_prequential_recipe_reparse_trainset_controls.py"
LOO_AUDIT = TEST_RESULTS / "13_leave_one_book_out_no_self_audit.json"


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


def source_ranges(books: dict[str, str], train_books: list[int]) -> tuple[list[dict[str, int]], list[int]]:
    ranges = []
    starts = []
    cursor = 0
    for book in train_books:
        start = cursor
        cursor += len(books[str(book)])
        ranges.append({"book": book, "start": start, "end": cursor})
        starts.append(start)
    return ranges, starts


def source_for_pos(
    ranges: list[dict[str, int]],
    starts: list[int],
    pos: int,
    *,
    train_available_len: int,
    current_prefix_len: int,
) -> str:
    if pos >= train_available_len:
        if pos < train_available_len + current_prefix_len:
            return "current_prefix"
        raise ValueError(
            {
                "pos": pos,
                "train_available_len": train_available_len,
                "current_prefix_len": current_prefix_len,
            }
        )
    index = bisect.bisect_right(starts, pos) - 1
    if index < 0 or pos >= ranges[index]["end"]:
        raise ValueError({"pos": pos, "range_index": index})
    return f"book:{ranges[index]['book']}"


def overlap_by_book(
    *,
    ranges: list[dict[str, int]],
    starts: list[int],
    source_start: int,
    length: int,
    train_available_len: int,
    current_prefix_len: int,
) -> dict[str, int]:
    source_end = source_start + length
    cursor = source_start
    overlaps: dict[str, int] = {}
    while cursor < source_end:
        if cursor >= train_available_len:
            source = "current_prefix"
            boundary = train_available_len + current_prefix_len
        else:
            index = bisect.bisect_right(starts, cursor) - 1
            if index < 0:
                raise ValueError({"cursor": cursor, "source_start": source_start, "length": length})
            row = ranges[index]
            source = f"book:{row['book']}"
            boundary = row["end"]
        take = min(source_end, boundary) - cursor
        if take <= 0:
            raise ValueError({"cursor": cursor, "source": source, "source_end": source_end})
        overlaps[source] = overlaps.get(source, 0) + take
        cursor += take
    return overlaps


def make_result() -> dict[str, Any]:
    audit126 = load_module("audit126_recipe_reparse", AUDIT_126)
    audit128 = load_module("audit128_trainset_controls", AUDIT_128)
    copy_module = audit126.load_module("copy_context", audit126.COPY_CONTEXT)
    payload_module = audit126.load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    item_module = audit126.load_module("item_context", audit126.ITEM_CONTEXT)

    formula = load_json(audit126.FORMULA)
    books = {str(key): value for key, value in load_json(audit126.BOOKS_DIGITS).items()}
    loo = load_json(LOO_AUDIT)
    all_books = set(range(70))

    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    rows = []
    aggregate_edges: dict[tuple[int, str], int] = defaultdict(int)
    source_book_usage: Counter[str] = Counter()
    source_start_book_usage: Counter[str] = Counter()
    total_copy_items = 0
    total_copied_digits = 0
    total_cross_boundary_items = 0
    total_cross_boundary_digits = 0

    for target_book in range(70):
        train_books = sorted(all_books - {target_book})
        train_counts = audit128.train_counts_for_books(
            audit126,
            train_books=set(train_books),
            formula=formula,
            copy_rows=copy_rows,
            payload_rows=payload_rows,
            item_rows=item_rows,
        )
        ranges, starts = source_ranges(books, train_books)
        available = "".join(books[str(book)] for book in train_books)
        train_available_len = len(available)
        encoded = audit126.encode_book_frozen_reparse(
            book=str(target_book),
            text=books[str(target_book)],
            available=available,
            formula=formula,
            train_counts=train_counts,
        )

        source_digits: Counter[int] = Counter()
        source_starts: Counter[int] = Counter()
        copy_items = 0
        copied_digits = 0
        cross_boundary_items = 0
        cross_boundary_digits = 0
        copy_details = []
        for op_index, op in enumerate(encoded["ops"]):
            if op["type"] != "copy":
                continue
            copy_items += 1
            length = int(op["length"])
            source_start = int(op["source_digit_pos"])
            current_prefix_len = int(op["target_start"])
            copied_digits += length
            start_source = source_for_pos(
                ranges,
                starts,
                source_start,
                train_available_len=train_available_len,
                current_prefix_len=current_prefix_len,
            )
            source_starts[start_source] += 1
            source_start_book_usage[start_source] += 1
            overlaps = overlap_by_book(
                ranges=ranges,
                starts=starts,
                source_start=source_start,
                length=length,
                train_available_len=train_available_len,
                current_prefix_len=current_prefix_len,
            )
            for source_book, overlap in overlaps.items():
                source_digits[source_book] += overlap
                source_book_usage[source_book] += overlap
                aggregate_edges[(target_book, source_book)] += overlap
            if len(overlaps) > 1:
                cross_boundary_items += 1
                cross_boundary_digits += length
            copy_details.append(
                {
                    "op_index": op_index,
                    "target_start": int(op["target_start"]),
                    "length": length,
                    "source_digit_pos": source_start,
                    "source_start": start_source,
                    "source_books_touched": dict(sorted(overlaps.items())),
                    "crosses_source_book_boundary": len(overlaps) > 1,
                }
            )

        total_copy_items += copy_items
        total_copied_digits += copied_digits
        total_cross_boundary_items += cross_boundary_items
        total_cross_boundary_digits += cross_boundary_digits
        top_source_book = None
        top_source_digits = 0
        if source_digits:
            top_source_book, top_source_digits = source_digits.most_common(1)[0]
        rows.append(
            {
                "target_book": target_book,
                "book_length_digits": len(books[str(target_book)]),
                "copy_items": copy_items,
                "copied_digits": copied_digits,
                "distinct_source_books": len(source_digits),
                "top_source_book": top_source_book,
                "top_source_copied_digits": top_source_digits,
                "top_source_share": (top_source_digits / copied_digits) if copied_digits else 0.0,
                "cross_boundary_copy_items": cross_boundary_items,
                "cross_boundary_copied_digits": cross_boundary_digits,
                "source_books_by_copied_digits": dict(sorted(source_digits.items())),
                "source_start_books_by_copy_items": dict(sorted(source_starts.items())),
                "copy_details": copy_details,
                "validation": encoded["validation"],
            }
        )

    edge_rows = [
        {"target_book": target, "source": source, "copied_digits": copied}
        for (target, source), copied in aggregate_edges.items()
    ]
    edge_rows.sort(key=lambda row: (-row["copied_digits"], row["target_book"], row["source"]))
    rows_by_top_share = sorted(rows, key=lambda row: row["top_source_share"], reverse=True)
    rows_by_distinct_sources = sorted(rows, key=lambda row: row["distinct_source_books"], reverse=True)
    cross_boundary_share = (
        total_cross_boundary_digits / total_copied_digits if total_copied_digits else 0.0
    )
    current_prefix_copied_digits = source_book_usage.get("current_prefix", 0)
    current_prefix_copy_items_started = source_start_book_usage.get("current_prefix", 0)
    current_prefix_target_books = [
        row["target_book"] for row in rows if row["source_books_by_copied_digits"].get("current_prefix")
    ]
    classification = (
        "loo_source_attribution_mapped_with_boundary_crossings"
        if total_cross_boundary_items
        else "loo_source_attribution_mapped_clean_book_sources"
    )
    return {
        "schema": "leave_one_book_out_source_attribution_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "leave_one_book_out_no_self": rel(LOO_AUDIT),
            "recipe_reparse": rel(AUDIT_126),
            "trainset_controls": rel(AUDIT_128),
        },
        "rows": rows,
        "source_edges": edge_rows,
        "summary": {
            "book_count": len(rows),
            "roundtrip_book_count": sum(1 for row in rows if row["validation"]["errors"] == []),
            "total_copy_items": total_copy_items,
            "total_copied_digits": total_copied_digits,
            "total_cross_boundary_copy_items": total_cross_boundary_items,
            "total_cross_boundary_copied_digits": total_cross_boundary_digits,
            "cross_boundary_copied_digit_share": cross_boundary_share,
            "current_prefix_copied_digits": current_prefix_copied_digits,
            "current_prefix_copied_digit_share": (
                current_prefix_copied_digits / total_copied_digits if total_copied_digits else 0.0
            ),
            "current_prefix_copy_items_started": current_prefix_copy_items_started,
            "current_prefix_target_books": current_prefix_target_books,
            "mean_distinct_source_books_per_target": sum(
                row["distinct_source_books"] for row in rows
            )
            / len(rows),
            "max_distinct_source_books": max(row["distinct_source_books"] for row in rows),
            "mean_top_source_share": sum(row["top_source_share"] for row in rows) / len(rows),
            "max_top_source_share": max(row["top_source_share"] for row in rows),
            "top_source_dominated_books_ge_0_90": [
                row["target_book"] for row in rows if row["top_source_share"] >= 0.90
            ],
            "highest_top_source_share_rows": [
                {
                    "target_book": row["target_book"],
                    "top_source_book": row["top_source_book"],
                    "top_source_share": row["top_source_share"],
                    "copied_digits": row["copied_digits"],
                }
                for row in rows_by_top_share[:10]
            ],
            "widest_source_rows": [
                {
                    "target_book": row["target_book"],
                    "distinct_source_books": row["distinct_source_books"],
                    "copied_digits": row["copied_digits"],
                }
                for row in rows_by_distinct_sources[:10]
            ],
            "top_source_books_by_copied_digits": [
                {"source": source, "copied_digits": copied}
                for source, copied in source_book_usage.most_common(10)
            ],
            "top_source_start_books_by_copy_items": [
                {"source": source, "copy_items_started": count}
                for source, count in source_start_book_usage.most_common(10)
            ],
            "top_edges_by_copied_digits": edge_rows[:20],
            "interpretation": (
                "The singleton result is not a black box: copied digits can be "
                "attributed to concrete source books or to the current held-out "
                "book prefix already emitted by the sequential decoder. Boundary-"
                "crossing copies are explicitly counted because the complement "
                "inventory is a concatenation of books without separators."
            ),
        },
        "decision": {
            "source_attribution_status": "mapped_for_singleton_holdout",
            "generation_explanation_status": "stronger_but_still_partial",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "14_leave_one_book_out_source_attribution_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Leave-One-Book-Out Source Attribution Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 13 showed every individual book can be reparsed without preloading",
        "that book into the inventory. This audit maps where copied digits come",
        "from: concrete source books or the already-emitted current-book prefix.",
        "It also counts copies that cross artificial source-book boundaries in the",
        "concatenated complement inventory.",
        "",
        "## Summary",
        "",
        f"- Books checked: `{result['summary']['book_count']}`.",
        f"- Roundtrip books: `{result['summary']['roundtrip_book_count']}/{result['summary']['book_count']}`.",
        f"- Copy items: `{result['summary']['total_copy_items']}`.",
        f"- Copied digits: `{result['summary']['total_copied_digits']}`.",
        f"- Cross-boundary copy items: `{result['summary']['total_cross_boundary_copy_items']}`.",
        f"- Cross-boundary copied digits: `{result['summary']['total_cross_boundary_copied_digits']}`.",
        f"- Cross-boundary copied digit share: `{result['summary']['cross_boundary_copied_digit_share']:.6f}`.",
        f"- Current-prefix copied digits: `{result['summary']['current_prefix_copied_digits']}`.",
        f"- Current-prefix copied digit share: `{result['summary']['current_prefix_copied_digit_share']:.6f}`.",
        f"- Current-prefix target books: `{result['summary']['current_prefix_target_books']}`.",
        f"- Mean distinct source books per target: `{result['summary']['mean_distinct_source_books_per_target']:.3f}`.",
        f"- Mean top-source share: `{result['summary']['mean_top_source_share']:.3f}`.",
        "",
        "## Highest Top-Source Shares",
        "",
        "| Target | Top source | Top share | Copied digits |",
        "|---:|---:|---:|---:|",
    ]
    for row in result["summary"]["highest_top_source_share_rows"]:
        lines.append(
            f"| `{row['target_book']}` | `{row['top_source_book']}` | "
            f"`{row['top_source_share']:.3f}` | `{row['copied_digits']}` |"
        )

    lines.extend(
        [
            "",
            "## Widest Source Rows",
            "",
            "| Target | Distinct source books | Copied digits |",
            "|---:|---:|---:|",
        ]
    )
    for row in result["summary"]["widest_source_rows"]:
        lines.append(
            f"| `{row['target_book']}` | `{row['distinct_source_books']}` | "
            f"`{row['copied_digits']}` |"
        )

    lines.extend(
        [
            "",
            "## Top Edges",
            "",
        "| Target | Source | Copied digits |",
            "|---:|---:|---:|",
        ]
    )
    for row in result["summary"]["top_edges_by_copied_digits"]:
        lines.append(
            f"| `{row['target_book']}` | `{row['source']}` | "
            f"`{row['copied_digits']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Singleton holdout source attribution is now explicit as target-book to source-book/current-prefix copied-digit edges.",
            "- Cross-boundary copies are measured rather than hidden; they are a boundary condition of the concatenated complement inventory.",
            "- This improves the mechanical dependency map but does not derive row0, plaintext, or authorial order.",
        ]
    )
    (TEST_RESULTS / "14_leave_one_book_out_source_attribution_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
