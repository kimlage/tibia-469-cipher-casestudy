from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_length_ledger_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def render_and_rewrite(formula: dict, books: dict[str, str]) -> tuple[dict, dict]:
    out = json.loads(json.dumps(formula))
    emitted_with_separators = ""
    emitted_digits = ""
    copy_rows = []
    errors = []

    for book in map(str, formula["policy"]["book_order"]):
        parts = []
        out_ops = out["book_recipes"][book]["ops"]
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            out_op = out_ops[op_index]
            if op["type"] == "literal":
                chunk = op["text"]
                if len(chunk) != int(op["length"]):
                    errors.append({"book": book, "type": "literal_length_mismatch", "op": op})
            elif op["type"] == "copy":
                source_pos = int(op["source_pos"])
                length = int(op["length"])
                chunk = emitted_with_separators[source_pos : source_pos + length]
                source_digit_pos = sum(1 for char in emitted_with_separators[:source_pos] if char != "#")
                digit_chunk = emitted_digits[source_digit_pos : source_digit_pos + length]
                if chunk != digit_chunk:
                    errors.append(
                        {
                            "book": book,
                            "type": "digit_address_mismatch",
                            "source_pos": source_pos,
                            "source_digit_pos": source_digit_pos,
                            "length": length,
                        }
                    )
                out_op["source_digit_pos"] = source_digit_pos
                out_op["source_pos_with_separators_audit"] = source_pos
                copy_rows.append(
                    {
                        "book": book,
                        "source_pos_with_separators": source_pos,
                        "source_digit_pos": source_digit_pos,
                        "target_global_with_separators": len(emitted_with_separators),
                        "target_digit_global": len(emitted_digits),
                        "length": length,
                    }
                )
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op": op})
            parts.append(chunk)
            emitted_with_separators += chunk
            emitted_digits += chunk
        if "".join(parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})
        emitted_with_separators += "#"

    validation = {
        "book_count": len(formula["policy"]["book_order"]),
        "books_roundtrip_ok": 0 if errors else len(formula["policy"]["book_order"]),
        "errors": errors,
    }
    return out, {"validation": validation, "copy_rows": copy_rows}


def address_bits_with_separators(copy_rows: list[dict]) -> float:
    return sum(math.log2(max(2, row["target_global_with_separators"])) for row in copy_rows)


def address_bits_digits_only(copy_rows: list[dict]) -> float:
    return sum(math.log2(max(2, row["target_digit_global"])) for row in copy_rows)


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    out, audit = render_and_rewrite(formula, books)
    if audit["validation"]["errors"]:
        raise RuntimeError(audit["validation"]["errors"])

    copy_rows = audit["copy_rows"]
    old_address_bits = formula["mdl_estimate_rough"]["copy_address_bits"]
    measured_old_address_bits = address_bits_with_separators(copy_rows)
    measured_new_address_bits = address_bits_digits_only(copy_rows)
    address_gain = measured_old_address_bits - measured_new_address_bits
    new_address_bits = old_address_bits - address_gain
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_length_ledger_bits"]
    new_total_bits = current_bits - address_gain

    promoted = new_total_bits < current_bits
    classification = "controlled_digit_only_copy_address_improvement" if promoted else "digit_only_copy_address_not_promoted"

    if promoted:
        out["schema"] = "sequential_lz_digit_address_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["copy_address_model"] = {
            "family": "absolute_digit_only_source_pos",
            "address_space": "previously_emitted_digits_excluding_book_separators",
        }
        out["mdl_estimate_rough"] = {
            **formula["mdl_estimate_rough"],
            "sequential_lz_digit_address_bits": new_total_bits,
            "previous_sequential_lz_length_ledger_bits": current_bits,
            "gain_vs_previous_length_ledger_bits": address_gain,
            "copy_bits": formula["mdl_estimate_rough"]["copy_bits"] - address_gain,
            "copy_address_bits": new_address_bits,
            "previous_copy_address_bits": old_address_bits,
            "digit_only_address_gain_bits": address_gain,
        }
        out["validation"]["digit_only_copy_address_roundtrip_audit"] = audit["validation"]
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "digit_only_copy_address_compile.v1",
        "test": "35_digit_only_copy_address_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "digit_only_formula_bits": new_total_bits,
        "delta_vs_current_bits": new_total_bits - current_bits,
        "copy_items": len(copy_rows),
        "old_copy_address_bits": old_address_bits,
        "measured_old_separator_address_bits": measured_old_address_bits,
        "measured_digit_only_address_bits": measured_new_address_bits,
        "digit_only_address_gain_bits": address_gain,
        "validation": audit["validation"],
        "boundary": formula["boundary"],
    }

    lines = [
        "# Digit-Only Copy Address Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit keeps the current recipe fixed and changes only the absolute",
        "copy-source address coordinate. Since the formula now declares the 70",
        "book lengths, book separators are reconstructable. Copy addresses can",
        "therefore point into the previously emitted digit stream rather than the",
        "previously emitted digit-plus-separator stream.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.1f}` |",
        f"| Digit-only address formula bits | `{new_total_bits:.1f}` |",
        f"| Delta vs current | `{new_total_bits - current_bits:.1f}` |",
        f"| Copy items | `{len(copy_rows)}` |",
        f"| Previous copy address bits | `{old_address_bits:.1f}` |",
        f"| Digit-only address bits | `{new_address_bits:.1f}` |",
        f"| Address gain | `{address_gain:.1f}` |",
        "",
        "## Interpretation",
        "",
        "The gain is small but decodable: separators no longer need to expand the",
        "absolute address space once book lengths are declared. This tightens the",
        "mechanical generation bound without changing any emitted book digits.",
        "",
        "## Boundary",
        "",
        "This is a coordinate/cost improvement only. It does not alter row0,",
        "introduce plaintext, or make an authorial-intent claim.",
    ]
    write_result("35_digit_only_copy_address_compile", result, lines)


if __name__ == "__main__":
    main()
