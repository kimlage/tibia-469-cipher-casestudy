from __future__ import annotations

import copy
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def min_len_bounded_copy_address_bits(formula: dict, books: dict[str, str]) -> dict:
    min_len = int(formula["policy"]["min_len"])
    order = [str(book) for book in formula["policy"]["book_order"]]
    emitted = ""
    errors = []
    rows = []
    total_bits = 0.0
    previous_total_bits = 0.0

    for book in order:
        ops = formula["book_recipes"][book]["ops"]
        book_parts = []
        for op_index, op in enumerate(ops):
            length = int(op["length"])
            if op["type"] == "literal":
                chunk = op["text"]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "literal_length_mismatch", "op_index": op_index})
            elif op["type"] == "copy":
                emitted_len = len(emitted)
                source_digit_pos = int(op["source_digit_pos"])
                legal_source_count = max(1, emitted_len - min_len + 1)
                if source_digit_pos >= legal_source_count:
                    errors.append(
                        {
                            "book": book,
                            "type": "source_outside_min_len_bound",
                            "op_index": op_index,
                            "source_digit_pos": source_digit_pos,
                            "legal_source_count": legal_source_count,
                            "emitted_len": emitted_len,
                            "min_len": min_len,
                        }
                    )
                previous_bits = math.log2(max(2, emitted_len))
                bounded_bits = math.log2(max(2, legal_source_count))
                previous_total_bits += previous_bits
                total_bits += bounded_bits
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op_index": op_index})
                rows.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "emitted_len": emitted_len,
                        "source_digit_pos": source_digit_pos,
                        "length": length,
                        "legal_source_count": legal_source_count,
                        "previous_address_bits": previous_bits,
                        "bounded_address_bits": bounded_bits,
                        "saved_bits": previous_bits - bounded_bits,
                    }
                )
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op_index": op_index, "op": op})
            book_parts.append(chunk)
            emitted += chunk
        if "".join(book_parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})

    return {
        "previous_copy_address_bits": previous_total_bits,
        "bounded_copy_address_bits": total_bits,
        "gain_bits": previous_total_bits - total_bits,
        "copy_items": len(rows),
        "rows": rows,
        "validation": {
            "book_count": len(order),
            "books_roundtrip_ok": 0 if errors else len(order),
            "errors": errors,
        },
    }


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])

    address_audit = min_len_bounded_copy_address_bits(formula, books)
    if address_audit["validation"]["errors"]:
        raise RuntimeError(address_audit["validation"])

    previous_address_bits = float(formula["mdl_estimate_rough"]["copy_address_bits"])
    if abs(address_audit["previous_copy_address_bits"] - previous_address_bits) > 1e-6:
        raise RuntimeError((address_audit["previous_copy_address_bits"], previous_address_bits))
    bounded_address_bits = address_audit["bounded_copy_address_bits"]
    bounded_total_bits = current_bits - previous_address_bits + bounded_address_bits
    gain_bits = current_bits - bounded_total_bits
    classification = (
        "controlled_min_len_bounded_copy_address_improvement"
        if gain_bits > 1e-9
        else "min_len_bounded_copy_address_not_promoted"
    )

    promoted = classification == "controlled_min_len_bounded_copy_address_improvement"
    if promoted:
        out = copy.deepcopy(formula)
        out["schema"] = "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["copy_address_model"] = {
            "address_space": "previously_emitted_digits_excluding_book_separators_and_impossible_last_min_len_minus_one_sources",
            "family": "absolute_digit_only_source_pos_min_len_bounded",
            "legal_source_count": "max(1, emitted_digit_count - min_len + 1)",
            "replaces": formula["policy"]["copy_address_model"],
        }
        out["policy"]["cost_model"] = (
            out["policy"]["cost_model"]
            + "+min_len_bounded_absolute_digit_source_addresses"
        )
        out["mdl_estimate_rough"] = {
            **out["mdl_estimate_rough"],
            OUT_TOTAL_KEY: bounded_total_bits,
            "previous_sequential_lz_digit_address_contextual_bounded_copy_length_bits": current_bits,
            "gain_vs_previous_contextual_bounded_copy_length_bits": gain_bits,
            "previous_copy_address_bits": previous_address_bits,
            "min_len_bounded_copy_address_bits": bounded_address_bits,
            "copy_address_bits": bounded_address_bits,
            "copy_bits": bounded_address_bits + float(formula["mdl_estimate_rough"]["copy_length_code_bits"]),
        }
        out["validation"] = {
            **out["validation"],
            "min_len_bounded_copy_address_roundtrip_audit": address_audit["validation"],
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    top_savings = sorted(address_audit["rows"], key=lambda row: row["saved_bits"], reverse=True)[:20]
    result = {
        "schema": "min_len_bounded_copy_address_compile.v1",
        "test": "70_min_len_bounded_copy_address_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "bounded_formula_bits": bounded_total_bits,
        "gain_bits": gain_bits,
        "previous_copy_address_bits": previous_address_bits,
        "min_len_bounded_copy_address_bits": bounded_address_bits,
        "address_audit": address_audit,
        "top_savings": top_savings,
        "promotion_rule": (
            "promote only if excluding impossible last min_len-1 source positions preserves "
            "70/70 roundtrip and lowers the active bounded-copy-length formula"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Min-Length-Bounded Copy Address Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tightens the absolute digit-only source address space in the",
        "active bounded-copy-length formula. A legal copy source must have at",
        "least `min_len` emitted digits available after it, so the last",
        "`min_len - 1` emitted positions cannot be valid source starts.",
        "",
        "The candidate keeps the recipe, copy lengths, literal payload model,",
        "item-type model, and book-length ledger unchanged. It replaces the",
        "address space size `emitted_digit_count` with",
        "`max(1, emitted_digit_count - min_len + 1)`.",
        "",
        "## Result",
        "",
        f"- Current formula bits: `{current_bits:.3f}`",
        f"- Min-length-bounded formula bits: `{bounded_total_bits:.3f}`",
        f"- Gain: `{gain_bits:.3f}` bits",
        f"- Previous copy-address bits: `{previous_address_bits:.3f}`",
        f"- Min-length-bounded copy-address bits: `{bounded_address_bits:.3f}`",
        f"- Copy items: `{address_audit['copy_items']}`",
        "",
        "## Top Per-Copy Savings",
        "",
        "| Rank | Book | Op | Emitted digits | Legal sources | Saved bits |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_savings, start=1):
        lines.append(
            f"| `{rank}` | `{row['book']}` | `{row['op_index']}` | "
            f"`{row['emitted_len']}` | `{row['legal_source_count']}` | "
            f"`{row['saved_bits']:.6f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a marginal address-space refinement only. It is decodable",
            "because `min_len` and the emitted digit count are known before every",
            "copy source address. It does not introduce plaintext, row0 meaning,",
            "or authorial intent.",
        ]
    )
    if promoted:
        lines.extend(
            [
                "",
                "## Promoted Formula",
                "",
                f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
            ]
        )
    write_result("70_min_len_bounded_copy_address_compile", result, lines)


if __name__ == "__main__":
    main()
