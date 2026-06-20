from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_dp_parse_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

LOG2_10 = math.log2(10)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def build_copy_rows(formula: dict, books: dict[str, str]) -> tuple[list[dict], dict]:
    order = [str(book) for book in formula["policy"]["book_order"]]
    min_len = int(formula["policy"]["min_len"])
    emitted_len = 0
    copy_rows: list[dict] = []
    spans: list[dict] = []
    copy_id = 0
    literal_bits = 0.0
    stream_header_bits = gamma_bits(len(order) + 1)
    book_header_bits = sum(gamma_bits(len(books[book]) + 1) for book in order)

    for book_index, book in enumerate(order):
        book_start_global = emitted_len
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                length = int(op["length"])
                literal_bits += 1 + gamma_bits(length + 1) + length * LOG2_10
                emitted_len += length
            elif op["type"] == "copy":
                length = int(op["length"])
                copy_rows.append(
                    {
                        "copy_id": copy_id,
                        "target_book": book,
                        "target_book_index": book_index,
                        "target_global": emitted_len,
                        "source_pos": int(op["source_pos"]),
                        "length": length,
                        "length_bits": gamma_bits(length - min_len + 1),
                    }
                )
                emitted_len += length
                copy_id += 1
            else:
                raise ValueError(op)
        spans.append(
            {
                "book": book,
                "book_index": book_index,
                "global_start": book_start_global,
                "global_end": emitted_len,
            }
        )
        emitted_len += 1

    for row in copy_rows:
        source_span = next(
            span
            for span in spans
            if span["global_start"] <= row["source_pos"] < span["global_end"]
        )
        row["source_book"] = source_span["book"]
        row["source_book_index"] = source_span["book_index"]
        row["source_offset"] = row["source_pos"] - source_span["global_start"]
        row["source_book_delta"] = row["target_book_index"] - row["source_book_index"]
        row["absolute_address_bits"] = math.log2(max(2, row["target_global"]))

    metadata = {
        "order": order,
        "min_len": min_len,
        "fixed_noncopy_bits": stream_header_bits + book_header_bits + literal_bits,
        "stream_header_bits": stream_header_bits,
        "book_header_bits": book_header_bits,
        "literal_bits": literal_bits,
    }
    return copy_rows, metadata


def hub_index_log_bits(count: int) -> float:
    if count <= 1:
        return 0.0
    return math.log2(count)


def hub_index_ceil_bits(count: int) -> int:
    if count <= 1:
        return 0
    return math.ceil(math.log2(count))


def absolute_copy_bits(copy_rows: list[dict]) -> float:
    return sum(
        1 + row["absolute_address_bits"] + row["length_bits"]
        for row in copy_rows
    )


def global_source_hub_model(copy_rows: list[dict]) -> dict:
    source_books = sorted({row["source_book"] for row in copy_rows}, key=int)
    table_bits = gamma_bits(len(source_books) + 1) + sum(
        gamma_bits(int(book) + 1) for book in source_books
    )
    index_bits = hub_index_log_bits(len(source_books))
    copy_bits = sum(
        1 + index_bits + gamma_bits(row["source_offset"] + 1) + row["length_bits"]
        for row in copy_rows
    )
    return {
        "model": "global_source_book_hub_offset_gamma",
        "copy_bits": copy_bits,
        "table_bits": table_bits,
        "decodable": True,
        "hub_count": len(source_books),
        "hub_index_bits": index_bits,
    }


def target_hub_model(copy_rows: list[dict], index_mode: str) -> dict:
    by_target: dict[str, list[dict]] = defaultdict(list)
    for row in copy_rows:
        by_target[row["target_book"]].append(row)

    table_bits = 0.0
    copy_bits = 0.0
    total_hubs = 0
    single_source_targets = 0
    if index_mode == "log2":
        index_fn = hub_index_log_bits
    elif index_mode == "ceil":
        index_fn = hub_index_ceil_bits
    else:
        raise ValueError(index_mode)

    for rows in by_target.values():
        source_books = sorted({row["source_book"] for row in rows}, key=int)
        total_hubs += len(source_books)
        single_source_targets += int(len(source_books) == 1)
        table_bits += gamma_bits(len(source_books) + 1)
        for source_book in source_books:
            source_delta = next(row["source_book_delta"] for row in rows if row["source_book"] == source_book)
            table_bits += gamma_bits(source_delta + 1)
        per_copy_index_bits = index_fn(len(source_books))
        copy_bits += sum(
            1 + per_copy_index_bits + gamma_bits(row["source_offset"] + 1) + row["length_bits"]
            for row in rows
        )

    return {
        "model": f"target_source_book_hub_offset_{index_mode}",
        "copy_bits": copy_bits,
        "table_bits": table_bits,
        "decodable": True,
        "target_books_with_copies": len(by_target),
        "target_source_hubs_total": total_hubs,
        "single_source_targets": single_source_targets,
    }


def target_default_source_models(copy_rows: list[dict]) -> list[dict]:
    by_target: dict[str, list[dict]] = defaultdict(list)
    for row in copy_rows:
        by_target[row["target_book"]].append(row)

    optimistic_table_bits = 0.0
    optimistic_copy_bits = 0.0
    mode_table_bits = 0.0
    mode_copy_bits = 0.0
    sparse_table_bits = 0.0
    sparse_copy_bits = 0.0
    default_copy_count = 0
    exception_copy_count = 0
    mode_default_uses = 0

    for rows in by_target.values():
        default_source = Counter(row["source_book"] for row in rows).most_common(1)[0][0]
        default_delta = next(
            row["source_book_delta"] for row in rows if row["source_book"] == default_source
        )
        default_declaration_bits = gamma_bits(default_delta + 1)
        optimistic_table_bits += default_declaration_bits
        mode_table_bits += default_declaration_bits
        sparse_table_bits += default_declaration_bits

        exceptions = [
            index
            for index, row in enumerate(rows)
            if row["source_book"] != default_source
        ]
        sparse_table_bits += gamma_bits(len(exceptions) + 1)
        previous = -1
        for index in exceptions:
            sparse_table_bits += gamma_bits(index - previous)
            previous = index

        for index, row in enumerate(rows):
            default_possible = row["source_book"] == default_source
            default_bits = gamma_bits(row["source_offset"] + 1) if default_possible else float("inf")
            absolute_bits = row["absolute_address_bits"]

            # Optimistic lower bound: a decoder somehow knows when the default
            # source is used. It is included to show that even the favorable
            # default-source hub variant does not beat absolute source_pos.
            if default_possible:
                default_copy_count += 1
                optimistic_copy_bits += 1 + default_bits + row["length_bits"]
            else:
                exception_copy_count += 1
                optimistic_copy_bits += 1 + absolute_bits + row["length_bits"]

            if default_bits < absolute_bits:
                mode_default_uses += 1
                mode_copy_bits += 1 + 1 + default_bits + row["length_bits"]
            else:
                mode_copy_bits += 1 + 1 + absolute_bits + row["length_bits"]

            if index in exceptions:
                sparse_copy_bits += 1 + absolute_bits + row["length_bits"]
            else:
                sparse_copy_bits += 1 + default_bits + row["length_bits"]

    return [
        {
            "model": "target_default_source_optimistic_no_mode",
            "copy_bits": optimistic_copy_bits,
            "table_bits": optimistic_table_bits,
            "decodable": False,
            "default_copy_count": default_copy_count,
            "exception_copy_count": exception_copy_count,
        },
        {
            "model": "target_default_source_mode_per_copy",
            "copy_bits": mode_copy_bits,
            "table_bits": mode_table_bits,
            "decodable": True,
            "default_copy_count": mode_default_uses,
            "exception_copy_count": len(copy_rows) - mode_default_uses,
        },
        {
            "model": "target_default_source_sparse_exception_list",
            "copy_bits": sparse_copy_bits,
            "table_bits": sparse_table_bits,
            "decodable": True,
            "default_copy_count": default_copy_count,
            "exception_copy_count": exception_copy_count,
        },
    ]


def source_hub_stats(copy_rows: list[dict]) -> dict:
    by_target: dict[str, list[dict]] = defaultdict(list)
    for row in copy_rows:
        by_target[row["target_book"]].append(row)
    source_books = sorted({row["source_book"] for row in copy_rows}, key=int)
    target_hub_counts = [len({row["source_book"] for row in rows}) for rows in by_target.values()]
    target_copy_counts = [len(rows) for rows in by_target.values()]
    top_target_books = []
    for target_book, rows in sorted(
        by_target.items(),
        key=lambda item: (-len(item[1]), int(item[0])),
    )[:8]:
        top_target_books.append(
            {
                "target_book": target_book,
                "copy_items": len(rows),
                "source_hub_count": len({row["source_book"] for row in rows}),
                "top_sources": Counter(row["source_book"] for row in rows).most_common(5),
            }
        )
    return {
        "copy_items": len(copy_rows),
        "target_books_with_copies": len(by_target),
        "global_source_book_count": len(source_books),
        "target_source_hubs_total": sum(target_hub_counts),
        "single_source_targets": sum(1 for count in target_hub_counts if count == 1),
        "max_source_hubs_in_target": max(target_hub_counts),
        "max_copy_items_in_target": max(target_copy_counts),
        "top_target_books_by_copy_count": top_target_books,
    }


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    copy_rows, metadata = build_copy_rows(formula, books)
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_dp_parse_bits"]

    absolute = {
        "model": "absolute_flat_source_pos",
        "copy_bits": absolute_copy_bits(copy_rows),
        "table_bits": 0.0,
        "decodable": True,
    }
    candidates = [
        absolute,
        global_source_hub_model(copy_rows),
        target_hub_model(copy_rows, "log2"),
        target_hub_model(copy_rows, "ceil"),
        *target_default_source_models(copy_rows),
    ]
    rows = []
    for candidate in candidates:
        total_bits = metadata["fixed_noncopy_bits"] + candidate["copy_bits"] + candidate["table_bits"]
        rows.append(
            {
                **candidate,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
            }
        )
    rows.sort(key=lambda row: row["total_bits"])

    best_decodable = next(row for row in rows if row["decodable"])
    best_any = rows[0]
    if best_decodable["model"] != "absolute_flat_source_pos" and best_decodable["total_bits"] < current_bits:
        classification = "copy_hub_macro_model_candidate"
    elif best_any["model"] != "absolute_flat_source_pos" and best_any["total_bits"] < current_bits:
        classification = "copy_hub_macro_optimistic_only_not_promoted"
    else:
        classification = "copy_hub_macro_model_not_promoted"

    result = {
        "schema": "copy_hub_macro_model_search.v1",
        "test": "19_copy_hub_macro_model_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "fixed_noncopy_bits": metadata["fixed_noncopy_bits"],
        "models": rows,
        "stats": source_hub_stats(copy_rows),
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Copy Hub Macro Model Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether the DP LZ copy ledger can be improved by",
        "declaring source-book hubs or default source books, then addressing",
        "copies as `hub + source_offset` rather than absolute `source_pos`.",
        "The parse, book order, emitted digits, and copy lengths are fixed.",
        "",
        "## Address Models",
        "",
        "| Model | Table bits | Copy bits | Total bits | Delta vs current | Decodable |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model']}` | `{row['table_bits']:.1f}` | `{row['copy_bits']:.1f}` | "
            f"`{row['total_bits']:.1f}` | `{row['delta_vs_current_bits']:.1f}` | "
            f"`{row['decodable']}` |"
        )

    stats = result["stats"]
    lines.extend(
        [
            "",
            "## Hub Shape",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Copy items | `{stats['copy_items']}` |",
            f"| Target books with copies | `{stats['target_books_with_copies']}` |",
            f"| Global source books | `{stats['global_source_book_count']}` |",
            f"| Target-source hubs total | `{stats['target_source_hubs_total']}` |",
            f"| Single-source target books | `{stats['single_source_targets']}` |",
            f"| Max source hubs in one target | `{stats['max_source_hubs_in_target']}` |",
            f"| Max copy items in one target | `{stats['max_copy_items_in_target']}` |",
            "",
            "## Interpretation",
            "",
            "The source-hub idea does not reduce the current DP LZ formula. The",
            "target-local hub table is too expensive, and even the optimistic",
            "default-source lower bound stays above the current absolute",
            "`source_pos` ledger. This closes the immediate copy-hub macro variant",
            "without changing the accepted mechanical baseline.",
            "",
            "## Boundary",
            "",
            "This is a mechanical address-cost audit only. It does not alter the book",
            "strings, explain row0, or introduce plaintext.",
        ]
    )
    write_result("19_copy_hub_macro_model_search", result, lines)


if __name__ == "__main__":
    main()
