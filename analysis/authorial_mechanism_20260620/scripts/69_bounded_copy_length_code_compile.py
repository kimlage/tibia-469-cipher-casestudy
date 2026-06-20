from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_copy_to_literal_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
SCORER = HERE / "scripts/64_contextual_local_repair_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_copy_to_literal_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_scorer():
    spec = importlib.util.spec_from_file_location("contextual_scorer", SCORER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scorer: {SCORER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def truncated_binary_bits(symbol_count: int, index: int) -> int:
    """Code length for index in a canonical truncated-binary code."""
    if symbol_count <= 0:
        raise ValueError(symbol_count)
    if not 0 <= index < symbol_count:
        raise ValueError((symbol_count, index))
    if symbol_count == 1:
        return 0
    floor_bits = int(math.floor(math.log2(symbol_count)))
    short_count = (1 << (floor_bits + 1)) - symbol_count
    return floor_bits if index < short_count else floor_bits + 1


def bounded_copy_length_bits(formula: dict, books: dict[str, str]) -> dict:
    min_len = int(formula["policy"]["min_len"])
    order = [str(book) for book in formula["policy"]["book_order"]]
    emitted = ""
    errors = []
    rows = []
    total_bits = 0
    copy_items = 0
    forced_singleton_lengths = 0
    singleton_saved_rice_bits = 0

    rice_k = int(formula["policy"]["copy_length_model"]["k"])

    for book in order:
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        book_parts = []
        book_pos = 0
        for op_index, op in enumerate(ops):
            length = int(op["length"])
            remaining = book_length - book_pos
            if op["type"] == "literal":
                chunk = op["text"]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "literal_length_mismatch", "op_index": op_index})
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                available_after_source = len(emitted) - source_digit_pos
                max_length = min(remaining, available_after_source)
                symbol_count = max_length - min_len + 1
                length_index = length - min_len
                if symbol_count <= 0:
                    errors.append(
                        {
                            "book": book,
                            "type": "no_legal_copy_length",
                            "op_index": op_index,
                            "remaining": remaining,
                            "available_after_source": available_after_source,
                        }
                    )
                    symbol_count = 1
                    length_index = 0
                elif not 0 <= length_index < symbol_count:
                    errors.append(
                        {
                            "book": book,
                            "type": "copy_length_outside_bounds",
                            "op_index": op_index,
                            "length": length,
                            "max_length": max_length,
                            "min_len": min_len,
                        }
                    )
                    length_index = max(0, min(length_index, symbol_count - 1))
                bits = truncated_binary_bits(symbol_count, length_index)
                total_bits += bits
                copy_items += 1
                rice_bits = ((length - min_len) >> rice_k) + 1 + rice_k
                if symbol_count == 1:
                    forced_singleton_lengths += 1
                    singleton_saved_rice_bits += rice_bits
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op_index": op_index})
                rows.append(
                    {
                        "book": book,
                        "op_index": op_index,
                        "book_pos": book_pos,
                        "source_digit_pos": source_digit_pos,
                        "length": length,
                        "max_length": max_length,
                        "symbol_count": symbol_count,
                        "length_index": length_index,
                        "bounded_bits": bits,
                        "rice_bits": rice_bits,
                        "saved_bits": rice_bits - bits,
                    }
                )
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op_index": op_index, "op": op})
            book_parts.append(chunk)
            emitted += chunk
            book_pos += length
        if "".join(book_parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})

    return {
        "bounded_copy_length_bits": total_bits,
        "copy_items": copy_items,
        "forced_singleton_lengths": forced_singleton_lengths,
        "singleton_saved_rice_bits": singleton_saved_rice_bits,
        "rows": rows,
        "validation": {
            "book_count": len(order),
            "books_roundtrip_ok": 0 if errors else len(order),
            "errors": errors,
        },
    }


def main() -> None:
    scorer = load_scorer()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = scorer.score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    bounded = bounded_copy_length_bits(formula, books)
    if bounded["validation"]["errors"]:
        raise RuntimeError(bounded["validation"])

    previous_copy_length_bits = float(current_score["copy_length_code_bits"])
    bounded_copy_length_code_bits = float(bounded["bounded_copy_length_bits"])
    current_copy_model_declaration_bits = int(formula["mdl_estimate_rough"]["copy_model_declaration_bits"])
    bounded_model_declaration_bits = current_copy_model_declaration_bits
    declaration_delta_bits = bounded_model_declaration_bits - current_copy_model_declaration_bits
    bounded_total_bits = current_bits - previous_copy_length_bits + bounded_copy_length_code_bits + declaration_delta_bits
    gain_bits = current_bits - bounded_total_bits
    classification = (
        "controlled_bounded_copy_length_improvement"
        if gain_bits > 1e-9
        else "bounded_copy_length_not_promoted"
    )

    promoted = classification == "controlled_bounded_copy_length_improvement"
    output_formula = None
    if promoted:
        output_formula = copy.deepcopy(formula)
        output_formula["schema"] = "sequential_lz_digit_address_contextual_bounded_copy_length_formula.v1"
        output_formula["classification"] = classification
        output_formula["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        output_formula["policy"]["copy_length_model"] = {
            "family": "bounded_truncated_binary_after_source_address",
            "max_length_bound": (
                "min(declared_book_remaining_digits, emitted_digit_count_after_source_address)"
            ),
            "model_declaration_bits": bounded_model_declaration_bits,
            "replaces": formula["policy"]["copy_length_model"],
        }
        output_formula["policy"]["cost_model"] = (
            output_formula["policy"]["cost_model"]
            + "+bounded_truncated_binary_copy_lengths_after_source_address"
        )
        output_formula["mdl_estimate_rough"] = {
            **output_formula["mdl_estimate_rough"],
            OUT_TOTAL_KEY: bounded_total_bits,
            "previous_sequential_lz_digit_address_contextual_copy_to_literal_bits": current_bits,
            "gain_vs_previous_contextual_copy_to_literal_bits": gain_bits,
            "previous_copy_length_code_bits": previous_copy_length_bits,
            "bounded_copy_length_code_bits": bounded_copy_length_code_bits,
            "copy_length_code_bits": bounded_copy_length_code_bits,
            "copy_model_declaration_bits": bounded_model_declaration_bits,
            "copy_bits": current_score["copy_address_bits"] + bounded_copy_length_code_bits,
            "copy_address_bits": current_score["copy_address_bits"],
            "forced_singleton_copy_lengths": bounded["forced_singleton_lengths"],
            "forced_singleton_copy_length_saved_bits": bounded["singleton_saved_rice_bits"],
        }
        output_formula["validation"] = {
            **output_formula["validation"],
            "bounded_copy_length_roundtrip_audit": bounded["validation"],
            "bounded_copy_length_copy_items": bounded["copy_items"],
        }
        OUT_FORMULA.write_text(
            json.dumps(output_formula, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    top_savings = sorted(bounded["rows"], key=lambda row: row["saved_bits"], reverse=True)[:20]
    result = {
        "schema": "bounded_copy_length_code_compile.v1",
        "test": "69_bounded_copy_length_code_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "bounded_formula_bits": bounded_total_bits,
        "gain_bits": gain_bits,
        "previous_copy_length_code_bits": previous_copy_length_bits,
        "bounded_copy_length_code_bits": bounded_copy_length_code_bits,
        "copy_model_declaration_bits": bounded_model_declaration_bits,
        "current_score_audit": current_score,
        "bounded_copy_length_audit": bounded,
        "top_savings": top_savings,
        "promotion_rule": (
            "promote only if the bounded code is decodable after source-address decoding, "
            "preserves 70/70 roundtrip, and beats Rice k=4 after declaration bits"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Bounded Copy-Length Code Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests a decodable copy-length refinement for the active",
        "contextual formula. After a copy source address is decoded, the decoder",
        "knows both the declared remaining book length and how many emitted digits",
        "exist after that source position. Therefore the legal copy length range is",
        "`min_len..min(remaining_book_digits, emitted_digits_after_source)`.",
        "",
        "The candidate replaces unbounded Rice `k=4` copy lengths with a canonical",
        "truncated-binary code over that bounded range. The copy recipe, addresses,",
        "book lengths, literal payload model, and item-type model are unchanged.",
        "",
        "## Result",
        "",
        f"- Current formula bits: `{current_bits:.1f}`",
        f"- Bounded formula bits: `{bounded_total_bits:.1f}`",
        f"- Gain: `{gain_bits:.1f}` bits",
        f"- Previous Rice copy-length bits: `{previous_copy_length_bits:.1f}`",
        f"- Bounded copy-length bits: `{bounded_copy_length_code_bits:.1f}`",
        f"- Copy items: `{bounded['copy_items']}`",
        f"- Forced singleton copy lengths: `{bounded['forced_singleton_lengths']}`",
        f"- Singleton saved Rice bits: `{bounded['singleton_saved_rice_bits']}`",
        "",
        "## Top Per-Copy Savings",
        "",
        "| Rank | Book | Op | Length | Max length | Rice bits | Bounded bits | Saved bits |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_savings, start=1):
        lines.append(
            f"| `{rank}` | `{row['book']}` | `{row['op_index']}` | `{row['length']}` | "
            f"`{row['max_length']}` | `{row['rice_bits']}` | `{row['bounded_bits']}` | "
            f"`{row['saved_bits']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The improvement is a coding-bound refinement, not a new parse or text",
            "claim. It is decodable because the bound is known before the copy length",
            "is decoded once the source address has been read. It does not introduce",
            "plaintext, row0 meaning, or authorial intent.",
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
    write_result("69_bounded_copy_length_code_compile", result, lines)


if __name__ == "__main__":
    main()
