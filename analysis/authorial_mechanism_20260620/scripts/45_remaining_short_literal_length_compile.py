from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_remaining_force_type_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_forced_literal_length_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

FORCED_LENGTH_RULE_BITS = 1


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def rice_bits(value: int, k: int) -> int:
    if value <= 0:
        raise ValueError(value)
    offset = value - 1
    return (offset >> k) + 1 + k


def render_formula_and_forced_literals(formula: dict, books: dict[str, str]) -> tuple[dict, list[dict], int]:
    emitted_digits = ""
    min_len = int(formula["policy"]["min_len"])
    literal_k = int(formula["policy"]["literal_run_length_model"]["k"])
    forced = []
    literal_length_bits = 0
    errors = []

    for book in map(str, formula["policy"]["book_order"]):
        parts = []
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        position = 0
        previous = "BOS"
        for op_index, op in enumerate(ops):
            item_type = op["type"]
            length = int(op["length"])
            remaining = book_length - position
            if item_type == "literal":
                chunk = op["text"]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "literal_length_mismatch", "op": op})
                length_bits = rice_bits(length + 1, literal_k)
                literal_length_bits += length_bits
                if remaining < min_len:
                    forced.append(
                        {
                            "book": book,
                            "op_index": op_index,
                            "previous_item_type": previous,
                            "remaining": remaining,
                            "length": length,
                            "saved_length_bits": length_bits,
                        }
                    )
                    if length != remaining:
                        errors.append(
                            {
                                "book": book,
                                "type": "forced_literal_does_not_consume_remaining",
                                "op_index": op_index,
                                "remaining": remaining,
                                "length": length,
                            }
                        )
            elif item_type == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                chunk = emitted_digits[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op": op})
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op": op})
            parts.append(chunk)
            emitted_digits += chunk
            position += length
            previous = item_type
        if "".join(parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})

    validation = {
        "book_count": len(formula["policy"]["book_order"]),
        "books_roundtrip_ok": 0 if errors else len(formula["policy"]["book_order"]),
        "errors": errors,
    }
    return validation, forced, literal_length_bits


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    validation, forced_literals, measured_literal_length_bits = render_formula_and_forced_literals(formula, books)
    if validation["errors"]:
        raise RuntimeError(validation["errors"])

    mdl = formula["mdl_estimate_rough"]
    current_bits = mdl["sequential_lz_digit_address_remaining_force_type_bits"]
    current_literal_length_bits = mdl["literal_bits_no_payload"]
    if measured_literal_length_bits != current_literal_length_bits:
        raise RuntimeError((measured_literal_length_bits, current_literal_length_bits))

    forced_saved_bits = sum(row["saved_length_bits"] for row in forced_literals)
    new_literal_length_bits = current_literal_length_bits - forced_saved_bits
    new_total_bits = current_bits - forced_saved_bits + FORCED_LENGTH_RULE_BITS
    delta = new_total_bits - current_bits
    promoted = delta < 0
    classification = (
        "controlled_remaining_short_literal_length_improvement"
        if promoted
        else "remaining_short_literal_length_not_promoted"
    )

    if promoted:
        out = json.loads(json.dumps(formula))
        out["schema"] = "sequential_lz_digit_address_forced_literal_length_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["literal_run_length_model"] = {
            **out["policy"]["literal_run_length_model"],
            "forced_length_rule_bits": FORCED_LENGTH_RULE_BITS,
            "deterministic_rule": "remaining_book_digits_less_than_min_len_forced_literal_consumes_remaining_book_digits",
        }
        out["policy"]["cost_model"] = (
            "gamma(book_count)+declared_book_length_ledger+adaptive_book_start_markov_item_type_ledger+"
            "forced_type_rules+forced_suffix_literal_lengths+copy_length_model_declaration+"
            "literal_length_model_declaration+literal_payload_model_declaration+literal_run_lengths+"
            "absolute_digit_source_copy_ops"
        )
        out["mdl_estimate_rough"] = {
            **mdl,
            "sequential_lz_digit_address_forced_literal_length_bits": new_total_bits,
            "previous_sequential_lz_digit_address_remaining_force_type_bits": current_bits,
            "gain_vs_previous_digit_address_remaining_force_type_bits": current_bits - new_total_bits,
            "fixed_bits": mdl["fixed_bits"] + FORCED_LENGTH_RULE_BITS,
            "literal_bits": new_literal_length_bits + mdl["adaptive_literal_payload_bits"],
            "literal_bits_no_payload": new_literal_length_bits,
            "previous_literal_bits_no_payload": current_literal_length_bits,
            "forced_literal_length_rule_bits": FORCED_LENGTH_RULE_BITS,
            "forced_literal_length_saved_bits": forced_saved_bits,
            "forced_literal_length_count": len(forced_literals),
        }
        out["validation"]["remaining_short_literal_length_roundtrip_audit"] = validation
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "remaining_short_literal_length_compile.v1",
        "test": "45_remaining_short_literal_length_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "new_formula_bits": new_total_bits,
        "delta_vs_current_bits": delta,
        "current_literal_length_bits": current_literal_length_bits,
        "new_literal_length_bits": new_literal_length_bits,
        "forced_literal_length_rule_bits": FORCED_LENGTH_RULE_BITS,
        "forced_literal_length_saved_bits": forced_saved_bits,
        "forced_literal_length_count": len(forced_literals),
        "forced_literals": forced_literals,
        "validation": validation,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Remaining-Short Literal-Length Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit keeps the current remaining-force item-type sequential LZ",
        "recipe fixed and retells only literal-run length costs. When fewer than",
        "`min_len` digits remain in a declared book, the item type is already",
        "forced to literal; that literal must consume the remaining book suffix.",
        "The audit charges an explicit one-bit rule for that deterministic",
        "literal length.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.1f}` |",
        f"| Forced-length formula bits | `{new_total_bits:.1f}` |",
        f"| Delta vs current | `{delta:.1f}` |",
        f"| Current literal length bits | `{current_literal_length_bits:.1f}` |",
        f"| New literal length bits | `{new_literal_length_bits:.1f}` |",
        f"| Forced suffix literals | `{len(forced_literals)}` |",
        f"| Saved length bits before rule | `{forced_saved_bits:.1f}` |",
        f"| Rule bits | `{FORCED_LENGTH_RULE_BITS}` |",
        "",
        "## Forced Literal Lengths",
        "",
        "| Book | Op | Remaining | Length | Saved bits |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in forced_literals:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['remaining']}` | "
            f"`{row['length']}` | `{row['saved_length_bits']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The rule is decodable because book lengths and `min_len` are already",
            "declared. A shorter-than-`min_len` remaining suffix cannot be encoded",
            "as a copy, and the existing type rules leave only one legal literal",
            "length: the full remaining suffix.",
            "",
            "## Boundary",
            "",
            "This is a mechanical length-ledger improvement only. It does not alter",
            "row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("45_remaining_short_literal_length_compile", result, lines)


if __name__ == "__main__":
    main()
