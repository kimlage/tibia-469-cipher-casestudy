from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
TABLES = HERE / "tables"

FORMULA = HERE / "sequential_lz_dp_parse_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
MECHANICAL_FORMULA = ROOT / "analysis/mechanism_model_20260618/mechanical_formula_469.json"
SQLITE_DB = ROOT / "data/bonelord_operational.sqlite"

COPY_GRAPH_CSV = TABLES / "dp_lz_copy_graph_edges.csv"
LITERAL_ATLAS_CSV = TABLES / "dp_lz_literal_seed_atlas.csv"
LITERAL_ATLAS_MD = TABLES / "dp_lz_literal_seed_atlas.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_decodedbase() -> dict[str, str]:
    if not SQLITE_DB.exists():
        return {}
    uri = f"file:{SQLITE_DB}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    con.row_factory = sqlite3.Row
    try:
        return {
            str(row["bookid"]): str(row["decodedbase"])
            for row in con.execute("select bookid, decodedbase from sheet__books")
        }
    finally:
        con.close()


def align_decoded_symbols(raw_digits: str, decodedbase: str, code_to_symbol: dict[str, str]) -> list[dict]:
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def solve(pos: int, sym_pos: int) -> tuple[tuple[int, int, str, bool, str], ...] | None:
        if pos == len(raw_digits) and sym_pos == len(decodedbase):
            return ()
        if pos > len(raw_digits) or sym_pos >= len(decodedbase):
            return None
        symbol = decodedbase[sym_pos]
        options = []
        if pos + 2 <= len(raw_digits):
            code = raw_digits[pos : pos + 2]
            if code_to_symbol.get(code) == symbol:
                rest = solve(pos + 2, sym_pos + 1)
                if rest is not None:
                    options.append(((pos, pos + 2, code, False, symbol),) + rest)
        if pos + 1 <= len(raw_digits):
            code = "0" + raw_digits[pos]
            if code_to_symbol.get(code) == symbol:
                rest = solve(pos + 1, sym_pos + 1)
                if rest is not None:
                    options.append(((pos, pos + 1, code, True, symbol),) + rest)
        if not options:
            return None
        options.sort(key=lambda items: sum(1 for item in items if item[3]))
        return options[0]

    aligned = solve(0, 0)
    if aligned is None:
        return []
    return [
        {
            "digit_start": start,
            "digit_end": end,
            "code": code,
            "omitted_leading_zero": omitted,
            "symbol": symbol,
        }
        for start, end, code, omitted, symbol in aligned
    ]


def symbol_overlap(alignment: list[dict], start: int, end: int) -> dict:
    overlaps = [
        item
        for item in alignment
        if item["digit_start"] < end and item["digit_end"] > start
    ]
    return {
        "row0_symbols_overlap": "".join(item["symbol"] for item in overlaps),
        "row0_codes_overlap": " ".join(item["code"] for item in overlaps),
        "omitted_zero_overlap_count": sum(1 for item in overlaps if item["omitted_leading_zero"]),
    }


def build_stream(formula: dict) -> tuple[list[dict], list[dict], list[dict]]:
    order = [str(book) for book in formula["policy"]["book_order"]]
    spans = []
    copy_rows = []
    literal_rows = []
    emitted_len = 0
    copy_id = 0
    literal_id = 0

    for book_index, book in enumerate(order):
        book_start_global = emitted_len
        previous_op_type = ""
        ops = formula["book_recipes"][str(book)]["ops"]
        for op_index, op in enumerate(ops):
            if op["type"] == "literal":
                length = int(op["length"])
                literal_rows.append(
                    {
                        "literal_run_id": literal_id,
                        "book": str(book),
                        "book_index": book_index,
                        "op_index": op_index,
                        "offset": int(sum(int(item["length"]) for item in ops[:op_index])),
                        "global_start": emitted_len,
                        "global_end": emitted_len + length,
                        "length": length,
                        "digits": op["text"],
                        "previous_op_type": previous_op_type,
                        "next_op_type": ops[op_index + 1]["type"] if op_index + 1 < len(ops) else "",
                    }
                )
                emitted_len += length
                literal_id += 1
                previous_op_type = "literal"
            elif op["type"] == "copy":
                length = int(op["length"])
                copy_rows.append(
                    {
                        "copy_id": copy_id,
                        "target_book": str(book),
                        "target_book_index": book_index,
                        "target_offset": int(op["target_start"]),
                        "target_global_start": emitted_len,
                        "target_global_end": emitted_len + length,
                        "source_global_start": int(op["source_pos"]),
                        "source_global_end": int(op["source_pos"]) + length,
                        "length": length,
                        "back_distance": emitted_len - int(op["source_pos"]),
                    }
                )
                emitted_len += length
                copy_id += 1
                previous_op_type = "copy"
            else:
                raise ValueError(op)
        spans.append(
            {
                "book": str(book),
                "book_index": book_index,
                "global_start": book_start_global,
                "global_end": emitted_len,
            }
        )
        emitted_len += 1
    return spans, copy_rows, literal_rows


def annotate_copy_sources(spans: list[dict], copy_rows: list[dict]) -> None:
    for row in copy_rows:
        source_span = next(
            span
            for span in spans
            if span["global_start"] <= row["source_global_start"] < span["global_end"]
        )
        row["source_book"] = source_span["book"]
        row["source_book_index"] = source_span["book_index"]
        row["source_offset"] = row["source_global_start"] - source_span["global_start"]
        row["source_end_offset"] = row["source_global_end"] - source_span["global_start"]
        row["target_end_offset"] = row["target_offset"] + row["length"]
        row["book_delta"] = row["target_book_index"] - row["source_book_index"]
        row["same_book"] = row["source_book"] == row["target_book"]


def annotate_literal_reuse(literal_rows: list[dict], copy_rows: list[dict]) -> None:
    for literal in literal_rows:
        users = [
            row
            for row in copy_rows
            if row["source_global_start"] < literal["global_end"]
            and row["source_global_end"] > literal["global_start"]
            and row["target_global_start"] >= literal["global_end"]
        ]
        literal["reused_later_as_source"] = bool(users)
        literal["later_copy_user_count"] = len(users)
        literal["later_copy_user_ids"] = "|".join(str(row["copy_id"]) for row in users[:12])
        literal["later_copy_user_books"] = "|".join(sorted({row["target_book"] for row in users}, key=int))


def write_tables(copy_rows: list[dict], literal_rows: list[dict]) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    copy_fields = [
        "copy_id",
        "source_book",
        "source_offset",
        "source_end_offset",
        "target_book",
        "target_offset",
        "target_end_offset",
        "length",
        "book_delta",
        "same_book",
        "back_distance",
    ]
    with COPY_GRAPH_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=copy_fields, lineterminator="\n")
        writer.writeheader()
        for row in copy_rows:
            writer.writerow({field: row[field] for field in copy_fields})

    literal_fields = [
        "literal_run_id",
        "book",
        "offset",
        "length",
        "digits",
        "row0_symbols_overlap",
        "row0_codes_overlap",
        "omitted_zero_overlap_count",
        "previous_op_type",
        "next_op_type",
        "reused_later_as_source",
        "later_copy_user_count",
        "later_copy_user_ids",
        "later_copy_user_books",
    ]
    with LITERAL_ATLAS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=literal_fields, lineterminator="\n")
        writer.writeheader()
        for row in literal_rows:
            writer.writerow({field: row.get(field, "") for field in literal_fields})

    lines = [
        "# DP LZ Literal Seed Atlas",
        "",
        "Diagnostic atlas of literal runs in `sequential_lz_dp_parse_formula_469.json`.",
        "`row0_symbols_overlap` is mechanical row0 overlap, not plaintext.",
        "",
        "| Run | Book | Offset | Len | Digits | Row0 overlap | Reused later |",
        "|---:|---:|---:|---:|---|---|---:|",
    ]
    for row in literal_rows:
        digits = row["digits"]
        digits_preview = digits if len(digits) <= 24 else digits[:24] + "..."
        symbols = row.get("row0_symbols_overlap", "")
        symbols_preview = symbols if len(symbols) <= 24 else symbols[:24] + "..."
        lines.append(
            f"| `{row['literal_run_id']}` | `{row['book']}` | `{row['offset']}` | "
            f"`{row['length']}` | `{digits_preview}` | `{symbols_preview}` | "
            f"`{row['later_copy_user_count']}` |"
        )
    LITERAL_ATLAS_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    code_to_symbol = load_json(MECHANICAL_FORMULA)["code_to_symbol"]
    decodedbase = load_decodedbase()

    spans, copy_rows, literal_rows = build_stream(formula)
    annotate_copy_sources(spans, copy_rows)
    annotate_literal_reuse(literal_rows, copy_rows)

    alignments = {}
    alignment_failures = []
    for book, digits in books.items():
        decoded = decodedbase.get(str(book), "")
        if not decoded:
            alignment_failures.append(str(book))
            alignments[str(book)] = []
            continue
        alignment = align_decoded_symbols(digits, decoded, code_to_symbol)
        if not alignment:
            alignment_failures.append(str(book))
        alignments[str(book)] = alignment

    for row in literal_rows:
        row.update(symbol_overlap(alignments.get(str(row["book"]), []), row["offset"], row["offset"] + row["length"]))

    write_tables(copy_rows, literal_rows)

    source_book_counts = Counter(row["source_book"] for row in copy_rows)
    source_book_digits = Counter()
    target_book_digits = Counter()
    for row in copy_rows:
        source_book_digits[row["source_book"]] += row["length"]
        target_book_digits[row["target_book"]] += row["length"]

    book_delta_counts = Counter(row["book_delta"] for row in copy_rows)
    literal_reused_count = sum(1 for row in literal_rows if row["reused_later_as_source"])
    literal_reused_digits = sum(row["length"] for row in literal_rows if row["reused_later_as_source"])
    same_book_count = sum(1 for row in copy_rows if row["same_book"])
    immediate_previous_count = sum(1 for row in copy_rows if row["book_delta"] == 1)

    classification = "copy_graph_literal_seed_atlas_compiled_no_formula_promotion"
    result = {
        "schema": "copy_graph_provenance_audit.v1",
        "test": "15_copy_graph_provenance_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "outputs": {
            "copy_graph_csv": str(COPY_GRAPH_CSV.relative_to(ROOT)),
            "literal_seed_atlas_csv": str(LITERAL_ATLAS_CSV.relative_to(ROOT)),
            "literal_seed_atlas_md": str(LITERAL_ATLAS_MD.relative_to(ROOT)),
        },
        "copy_items": len(copy_rows),
        "copied_digits": sum(row["length"] for row in copy_rows),
        "same_book_copy_items": same_book_count,
        "immediate_previous_book_copy_items": immediate_previous_count,
        "source_book_count": len(source_book_counts),
        "top_source_books_by_copy_digits": source_book_digits.most_common(10),
        "top_target_books_by_copied_digits": target_book_digits.most_common(10),
        "book_delta_counts": sorted(book_delta_counts.items()),
        "literal_runs": len(literal_rows),
        "literal_digits": sum(row["length"] for row in literal_rows),
        "literal_runs_reused_later": literal_reused_count,
        "literal_digits_reused_later": literal_reused_digits,
        "row0_alignment_failures": alignment_failures,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Copy Graph Provenance Audit",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit materializes the DP LZ formula as copy edges and literal seed",
        "runs. It is diagnostic: it explains where the current generator copies",
        "from, which literal runs become later source material, and which books are",
        "source hubs. It does not introduce a new lower-cost formula.",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Copy items | `{len(copy_rows)}` |",
        f"| Copied digits | `{sum(row['length'] for row in copy_rows)}` |",
        f"| Same-book copy items | `{same_book_count}` |",
        f"| Immediate-previous-book copy items | `{immediate_previous_count}` |",
        f"| Source books used | `{len(source_book_counts)}` |",
        f"| Literal runs | `{len(literal_rows)}` |",
        f"| Literal digits | `{sum(row['length'] for row in literal_rows)}` |",
        f"| Literal runs reused later | `{literal_reused_count}` |",
        f"| Literal digits reused later | `{literal_reused_digits}` |",
        f"| Row0 alignment failures | `{len(alignment_failures)}` |",
        "",
        "## Top Source Books By Copied Digits",
        "",
        "| Book | Copied-out digits |",
        "|---:|---:|",
    ]
    for book, copied in source_book_digits.most_common(10):
        lines.append(f"| `{book}` | `{copied}` |")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- [Copy graph CSV](../../tables/{COPY_GRAPH_CSV.name})",
            f"- [Literal seed atlas CSV](../../tables/{LITERAL_ATLAS_CSV.name})",
            f"- [Literal seed atlas Markdown](../../tables/{LITERAL_ATLAS_MD.name})",
            "",
            "## Boundary",
            "",
            "The atlas uses row0 symbols as mechanical overlap labels only. It does",
            "not promote plaintext, authorial intent, or a row0 pair-table origin.",
        ]
    )
    write_result("15_copy_graph_provenance_audit", result, lines)


if __name__ == "__main__":
    main()
