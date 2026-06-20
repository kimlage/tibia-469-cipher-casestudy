from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_literal_repair_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_type_coded_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

ITEM_TYPES = ["literal", "copy"]


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


def adaptive_type_bits(stream: list[str], alpha: int) -> float:
    counts = {item_type: 0 for item_type in ITEM_TYPES}
    total = 0
    bits = 0.0
    for item_type in stream:
        probability = (counts[item_type] + alpha) / (total + len(ITEM_TYPES) * alpha)
        bits += -math.log2(probability)
        counts[item_type] += 1
        total += 1
    return bits


def render_formula_and_item_stream(formula: dict, books: dict[str, str]) -> tuple[dict, list[str]]:
    emitted_digits = ""
    item_stream = []
    errors = []

    for book in map(str, formula["policy"]["book_order"]):
        parts = []
        for op in formula["book_recipes"][book]["ops"]:
            item_type = op["type"]
            item_stream.append(item_type)
            if item_type == "literal":
                chunk = op["text"]
                if len(chunk) != int(op["length"]):
                    errors.append({"book": book, "type": "literal_length_mismatch", "op": op})
            elif item_type == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                length = int(op["length"])
                chunk = emitted_digits[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op": op})
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op": op})
            parts.append(chunk)
            emitted_digits += chunk
        if "".join(parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})

    validation = {
        "book_count": len(formula["policy"]["book_order"]),
        "books_roundtrip_ok": 0 if errors else len(formula["policy"]["book_order"]),
        "errors": errors,
    }
    return validation, item_stream


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    validation, item_stream = render_formula_and_item_stream(formula, books)
    if validation["errors"]:
        raise RuntimeError(validation["errors"])

    current_bits = formula["mdl_estimate_rough"]["sequential_lz_digit_address_literal_repair_bits"]
    literal_runs = int(formula["mdl_estimate_rough"]["literal_runs"])
    copy_items = int(formula["mdl_estimate_rough"]["copy_items"])
    current_item_type_bits = literal_runs + copy_items
    if current_item_type_bits != len(item_stream):
        raise RuntimeError((current_item_type_bits, len(item_stream)))

    literal_length_bits = formula["mdl_estimate_rough"]["literal_bits_no_payload"] - literal_runs
    copy_bits_without_type = formula["mdl_estimate_rough"]["copy_bits"] - copy_items
    fixed_bits = formula["mdl_estimate_rough"]["fixed_bits"]
    literal_payload_bits = formula["mdl_estimate_rough"]["adaptive_literal_payload_bits"]

    measured_current = (
        fixed_bits
        + literal_length_bits
        + literal_payload_bits
        + copy_bits_without_type
        + current_item_type_bits
    )
    if abs(measured_current - current_bits) > 1e-6:
        raise RuntimeError((measured_current, current_bits))

    rows = []
    for alpha in range(1, 129):
        stream_bits = adaptive_type_bits(item_stream, alpha)
        declaration_bits = gamma_bits(alpha + 1)
        type_bits = stream_bits + declaration_bits
        total_bits = (
            fixed_bits
            + declaration_bits
            + literal_length_bits
            + literal_payload_bits
            + copy_bits_without_type
            + stream_bits
        )
        rows.append(
            {
                "alpha": alpha,
                "item_type_stream_bits": stream_bits,
                "model_declaration_bits": declaration_bits,
                "item_type_bits": type_bits,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
            }
        )
    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    promoted = best["total_bits"] < current_bits
    classification = "controlled_item_type_ledger_improvement" if promoted else "item_type_ledger_not_promoted"

    histogram = dict(sorted(Counter(item_stream).items()))

    if promoted:
        out = json.loads(json.dumps(formula))
        out["schema"] = "sequential_lz_digit_address_type_coded_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["item_type_model"] = {
            "family": "adaptive_dirichlet_integer_alpha",
            "alphabet": ITEM_TYPES,
            "alpha": best["alpha"],
            "model_declaration_bits": best["model_declaration_bits"],
        }
        out["policy"]["cost_model"] = (
            "gamma(book_count)+declared_book_length_ledger+adaptive_item_type_ledger+"
            "copy_length_model_declaration+literal_length_model_declaration+"
            "literal_payload_model_declaration+literal_run_lengths+absolute_digit_source_copy_ops"
        )
        out["mdl_estimate_rough"] = {
            **formula["mdl_estimate_rough"],
            "sequential_lz_digit_address_type_coded_bits": best["total_bits"],
            "previous_sequential_lz_digit_address_literal_repair_bits": current_bits,
            "gain_vs_previous_digit_address_literal_repair_bits": current_bits - best["total_bits"],
            "fixed_bits": fixed_bits + best["model_declaration_bits"],
            "literal_bits": literal_length_bits + literal_payload_bits,
            "literal_bits_no_payload": literal_length_bits,
            "copy_bits": copy_bits_without_type,
            "previous_item_type_bits": current_item_type_bits,
            "item_type_bits": best["item_type_bits"],
            "item_type_stream_bits": best["item_type_stream_bits"],
            "item_type_model_declaration_bits": best["model_declaration_bits"],
            "item_type_gain_bits": current_item_type_bits - best["item_type_bits"],
            "item_type_histogram": histogram,
        }
        out["validation"]["item_type_ledger_roundtrip_audit"] = validation
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "item_type_ledger_compile.v1",
        "test": "40_item_type_ledger_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_item_type_bits": current_item_type_bits,
        "literal_runs": literal_runs,
        "copy_items": copy_items,
        "item_type_histogram": histogram,
        "literal_length_bits": literal_length_bits,
        "copy_bits_without_type": copy_bits_without_type,
        "best_model": best,
        "top_models": rows[:20],
        "validation": validation,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Item-Type Ledger Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit keeps the current repaired sequential LZ recipe fixed and",
        "retells only the literal/copy item-type ledger. The active formula",
        "charges one type bit per item. Candidate ledgers encode the same item",
        "stream with a two-symbol adaptive Dirichlet model and charge the",
        "declared integer `alpha`.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.1f}` |",
        f"| Best type-coded formula bits | `{best['total_bits']:.1f}` |",
        f"| Delta vs current | `{best['delta_vs_current_bits']:.1f}` |",
        f"| Current item-type bits | `{current_item_type_bits:.1f}` |",
        f"| Best item-type bits | `{best['item_type_bits']:.1f}` |",
        f"| Literal runs | `{literal_runs}` |",
        f"| Copy items | `{copy_items}` |",
        f"| Best alpha | `{best['alpha']}` |",
        "",
        "## Best Alpha Values",
        "",
        "| Rank | Alpha | Stream bits | Model bits | Type bits | Total bits | Delta |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:16], start=1):
        lines.append(
            f"| `{rank}` | `{row['alpha']}` | `{row['item_type_stream_bits']:.1f}` | "
            f"`{row['model_declaration_bits']}` | `{row['item_type_bits']:.1f}` | "
            f"`{row['total_bits']:.1f}` | `{row['delta_vs_current_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The item stream is strongly imbalanced toward copies. Charging a fixed",
            "one-bit tag per item is decodable but not the tightest ledger for the",
            "already-fixed recipe. The adaptive two-symbol ledger is also decodable",
            "because the decoder reads item types sequentially until each declared",
            "book length is exhausted.",
            "",
            "## Boundary",
            "",
            "This is a mechanical ledger/cost improvement only. It does not alter",
            "row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("40_item_type_ledger_compile", result, lines)


if __name__ == "__main__":
    main()
