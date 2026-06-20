from __future__ import annotations

import json
import math
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


def signed_delta_bits(delta: int) -> int:
    return gamma_bits(abs(delta) + 1) + (0 if delta == 0 else 1)


def build_copy_rows(formula: dict, books: dict[str, str]) -> tuple[list[dict], dict]:
    order = [str(book) for book in formula["policy"]["book_order"]]
    min_len = int(formula["policy"]["min_len"])
    emitted_len = 0
    copy_rows: list[dict] = []
    spans: list[dict] = []
    literal_bits = 0.0
    book_header_bits = sum(gamma_bits(len(books[str(book)]) + 1) for book in order)
    stream_header_bits = gamma_bits(len(order) + 1)
    copy_id = 0

    for book_index, book in enumerate(order):
        book_start_global = emitted_len
        for op in formula["book_recipes"][str(book)]["ops"]:
            if op["type"] == "literal":
                length = int(op["length"])
                literal_bits += 1 + gamma_bits(length + 1) + length * LOG2_10
                emitted_len += length
            elif op["type"] == "copy":
                length = int(op["length"])
                source_pos = int(op["source_pos"])
                copy_rows.append(
                    {
                        "copy_id": copy_id,
                        "target_book": str(book),
                        "target_book_index": book_index,
                        "target_offset": int(op["target_start"]),
                        "target_global": emitted_len,
                        "source_pos": source_pos,
                        "length": length,
                        "back_distance": emitted_len - source_pos,
                    }
                )
                emitted_len += length
                copy_id += 1
            else:
                raise ValueError(op)
        spans.append(
            {
                "book": str(book),
                "book_index": book_index,
                "start_global": book_start_global,
                "end_global": emitted_len,
            }
        )
        emitted_len += 1

    for row in copy_rows:
        source_span = next(
            span
            for span in spans
            if span["start_global"] <= row["source_pos"] < span["end_global"]
        )
        row["source_book"] = source_span["book"]
        row["source_book_index"] = source_span["book_index"]
        row["source_offset"] = row["source_pos"] - source_span["start_global"]
        row["source_book_delta"] = row["target_book_index"] - row["source_book_index"]
        row["same_book"] = row["source_book"] == row["target_book"]

    fixed_bits = stream_header_bits + book_header_bits + literal_bits
    metadata = {
        "order": order,
        "min_len": min_len,
        "stream_header_bits": stream_header_bits,
        "book_header_bits": book_header_bits,
        "literal_bits": literal_bits,
        "fixed_noncopy_bits": fixed_bits,
    }
    return copy_rows, metadata


def copy_len_bits(row: dict, min_len: int) -> int:
    return gamma_bits(row["length"] - min_len + 1)


def cost_models(copy_rows: list[dict], min_len: int) -> dict[str, float]:
    models: dict[str, float] = {}

    models["absolute_flat_source_pos"] = sum(
        1 + math.log2(max(2, row["target_global"])) + copy_len_bits(row, min_len)
        for row in copy_rows
    )
    models["back_distance_gamma"] = sum(
        1 + gamma_bits(row["back_distance"]) + copy_len_bits(row, min_len)
        for row in copy_rows
    )
    models["book_delta_offset_gamma"] = sum(
        1
        + gamma_bits(row["source_book_delta"] + 1)
        + gamma_bits(row["source_offset"] + 1)
        + copy_len_bits(row, min_len)
        for row in copy_rows
    )

    for model_name, field in [
        ("source_pos_delta_gamma", "source_pos"),
        ("back_distance_delta_gamma", "back_distance"),
    ]:
        previous = None
        total = 0.0
        for row in copy_rows:
            value = row[field]
            if previous is None:
                address_bits = gamma_bits(value + 1) if field == "source_pos" else gamma_bits(value)
            else:
                address_bits = signed_delta_bits(value - previous)
            total += 1 + address_bits + copy_len_bits(row, min_len)
            previous = value
        models[model_name] = total

    previous_delta = None
    previous_offset = None
    total = 0.0
    for row in copy_rows:
        book_delta = row["source_book_delta"]
        source_offset = row["source_offset"]
        if previous_delta is None:
            address_bits = gamma_bits(book_delta + 1) + gamma_bits(source_offset + 1)
        else:
            address_bits = signed_delta_bits(book_delta - previous_delta) + signed_delta_bits(
                source_offset - previous_offset
            )
        total += 1 + address_bits + copy_len_bits(row, min_len)
        previous_delta = book_delta
        previous_offset = source_offset
    models["book_delta_offset_delta_gamma"] = total

    models["mixed_same_book_distance_else_book_offset"] = sum(
        1
        + 1
        + (
            gamma_bits(row["back_distance"])
            if row["same_book"]
            else gamma_bits(row["source_book_delta"] + 1) + gamma_bits(row["source_offset"] + 1)
        )
        + copy_len_bits(row, min_len)
        for row in copy_rows
    )
    return models


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    copy_rows, metadata = build_copy_rows(formula, books)
    observed_bits = formula["mdl_estimate_rough"]["sequential_lz_dp_parse_bits"]
    models = cost_models(copy_rows, metadata["min_len"])
    rows = []
    for name, copy_bits in sorted(models.items(), key=lambda item: item[1]):
        total_bits = metadata["fixed_noncopy_bits"] + copy_bits
        rows.append(
            {
                "model": name,
                "copy_bits": copy_bits,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - observed_bits,
            }
        )

    best = rows[0]
    classification = (
        "copy_source_address_absolute_retained"
        if best["model"] == "absolute_flat_source_pos"
        else "copy_source_address_model_candidate"
    )
    result = {
        "schema": "copy_source_address_model_search.v1",
        "test": "14_copy_source_address_model_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "copy_items": len(copy_rows),
        "same_book_copy_items": sum(1 for row in copy_rows if row["same_book"]),
        "fixed_noncopy_bits": metadata["fixed_noncopy_bits"],
        "current_formula_bits": observed_bits,
        "models": rows,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Copy Source Address Model Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether the DP sequential LZ formula can be improved by",
        "charging copy source addresses differently. The parse and emitted books",
        "are held fixed; only the address ledger changes.",
        "",
        "## Address Models",
        "",
        "| Model | Copy bits | Total bits | Delta vs current |",
        "|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model']}` | `{row['copy_bits']:.1f}` | "
            f"`{row['total_bits']:.1f}` | `{row['delta_vs_current_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The current absolute `source_pos` ledger remains cheapest. Back-distance,",
            "source-delta, and book-relative source models all add cost under this",
            "fixed parse. Therefore no new address model is promoted in this cycle.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost audit only. It does not alter the book text,",
            "explain row0, or introduce plaintext.",
        ]
    )
    write_result("14_copy_source_address_model_search", result, lines)


if __name__ == "__main__":
    main()
