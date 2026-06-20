from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_markov_type_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_book_start_type_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

ITEM_TYPES = ["literal", "copy"]
BOS = "BOS"


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


def render_formula_and_book_streams(formula: dict, books: dict[str, str]) -> tuple[dict, list[dict], list[str]]:
    emitted_digits = ""
    book_streams = []
    flat_stream = []
    errors = []

    for book in map(str, formula["policy"]["book_order"]):
        parts = []
        item_stream = []
        for op in formula["book_recipes"][book]["ops"]:
            item_type = op["type"]
            item_stream.append(item_type)
            flat_stream.append(item_type)
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
        book_streams.append({"book": book, "item_stream": item_stream})

    validation = {
        "book_count": len(formula["policy"]["book_order"]),
        "books_roundtrip_ok": 0 if errors else len(formula["policy"]["book_order"]),
        "errors": errors,
    }
    return validation, book_streams, flat_stream


def book_start_markov_bits(book_streams: list[dict], alpha: int) -> tuple[float, dict[str, int]]:
    counts = defaultdict(lambda: {item_type: 0 for item_type in ITEM_TYPES})
    totals = defaultdict(int)
    transitions = Counter()
    bits = 0.0
    for row in book_streams:
        previous = BOS
        for item_type in row["item_stream"]:
            probability = (counts[previous][item_type] + alpha) / (totals[previous] + len(ITEM_TYPES) * alpha)
            bits += -math.log2(probability)
            counts[previous][item_type] += 1
            totals[previous] += 1
            transitions[f"{previous}->{item_type}"] += 1
            previous = item_type
    return bits, dict(sorted(transitions.items()))


def global_markov_bits(flat_stream: list[str], alpha: int) -> float:
    if not flat_stream:
        return 0.0
    counts = {previous: {item_type: 0 for item_type in ITEM_TYPES} for previous in ITEM_TYPES}
    totals = {item_type: 0 for item_type in ITEM_TYPES}
    bits = 1.0
    previous = flat_stream[0]
    for item_type in flat_stream[1:]:
        probability = (counts[previous][item_type] + alpha) / (totals[previous] + len(ITEM_TYPES) * alpha)
        bits += -math.log2(probability)
        counts[previous][item_type] += 1
        totals[previous] += 1
        previous = item_type
    return bits


def order2_book_start_diagnostic(book_streams: list[dict], alpha: int) -> float:
    counts = defaultdict(lambda: {item_type: 0 for item_type in ITEM_TYPES})
    totals = defaultdict(int)
    bits = 0.0
    for row in book_streams:
        history = [BOS, BOS]
        for item_type in row["item_stream"]:
            context = tuple(history[-2:])
            probability = (counts[context][item_type] + alpha) / (totals[context] + len(ITEM_TYPES) * alpha)
            bits += -math.log2(probability)
            counts[context][item_type] += 1
            totals[context] += 1
            history.append(item_type)
    return bits


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    validation, book_streams, flat_stream = render_formula_and_book_streams(formula, books)
    if validation["errors"]:
        raise RuntimeError(validation["errors"])

    mdl = formula["mdl_estimate_rough"]
    current_bits = mdl["sequential_lz_digit_address_markov_type_bits"]
    current_item_type_bits = mdl["item_type_bits"]
    current_item_type_stream_bits = mdl["item_type_stream_bits"]
    current_item_type_declaration_bits = mdl["item_type_model_declaration_bits"]
    fixed_without_item_type_model = mdl["fixed_bits"] - current_item_type_declaration_bits

    measured_current = (
        mdl["fixed_bits"]
        + mdl["literal_bits_no_payload"]
        + mdl["adaptive_literal_payload_bits"]
        + mdl["copy_bits"]
        + current_item_type_stream_bits
    )
    if abs(measured_current - current_bits) > 1e-6:
        raise RuntimeError((measured_current, current_bits))

    rows = []
    for alpha in range(1, 129):
        stream_bits, transitions = book_start_markov_bits(book_streams, alpha)
        declaration_bits = gamma_bits(alpha + 1)
        type_bits = stream_bits + declaration_bits
        total_bits = (
            fixed_without_item_type_model
            + declaration_bits
            + mdl["literal_bits_no_payload"]
            + mdl["adaptive_literal_payload_bits"]
            + mdl["copy_bits"]
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
                "transition_histogram": transitions,
            }
        )
    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    promoted = best["total_bits"] < current_bits
    classification = (
        "controlled_book_start_item_type_ledger_improvement"
        if promoted
        else "book_start_item_type_ledger_not_promoted"
    )

    histogram = dict(sorted(Counter(flat_stream).items()))
    book_start_histogram = dict(sorted(Counter(row["item_stream"][0] for row in book_streams if row["item_stream"]).items()))
    diagnostic_rows = []
    for alpha in range(1, 17):
        diagnostic_rows.append(
            {
                "alpha": alpha,
                "global_markov_type_bits": global_markov_bits(flat_stream, alpha) + gamma_bits(alpha + 1),
                "book_start_markov_type_bits": book_start_markov_bits(book_streams, alpha)[0] + gamma_bits(alpha + 1),
                "book_start_order2_type_bits": order2_book_start_diagnostic(book_streams, alpha) + gamma_bits(alpha + 1),
            }
        )

    if promoted:
        out = json.loads(json.dumps(formula))
        out["schema"] = "sequential_lz_digit_address_book_start_type_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["item_type_model"] = {
            "family": "adaptive_book_start_markov_dirichlet_integer_alpha",
            "alphabet": ITEM_TYPES,
            "alpha": best["alpha"],
            "model_declaration_bits": best["model_declaration_bits"],
            "conditioning": "BOS_at_each_declared_book_start_else_previous_item_type",
        }
        out["policy"]["cost_model"] = (
            "gamma(book_count)+declared_book_length_ledger+adaptive_book_start_markov_item_type_ledger+"
            "copy_length_model_declaration+literal_length_model_declaration+"
            "literal_payload_model_declaration+literal_run_lengths+absolute_digit_source_copy_ops"
        )
        out["mdl_estimate_rough"] = {
            **mdl,
            "sequential_lz_digit_address_book_start_type_bits": best["total_bits"],
            "previous_sequential_lz_digit_address_markov_type_bits": current_bits,
            "gain_vs_previous_digit_address_markov_type_bits": current_bits - best["total_bits"],
            "fixed_bits": fixed_without_item_type_model + best["model_declaration_bits"],
            "previous_item_type_bits": current_item_type_bits,
            "previous_item_type_stream_bits": current_item_type_stream_bits,
            "item_type_bits": best["item_type_bits"],
            "item_type_stream_bits": best["item_type_stream_bits"],
            "item_type_model_declaration_bits": best["model_declaration_bits"],
            "item_type_gain_bits": current_item_type_bits - best["item_type_bits"],
            "item_type_histogram": histogram,
            "item_type_book_start_histogram": book_start_histogram,
            "item_type_transition_histogram": best["transition_histogram"],
        }
        out["validation"]["book_start_item_type_ledger_roundtrip_audit"] = validation
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "book_start_item_type_ledger_compile.v1",
        "test": "42_book_start_item_type_ledger_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_item_type_bits": current_item_type_bits,
        "current_item_type_stream_bits": current_item_type_stream_bits,
        "item_count": len(flat_stream),
        "book_count": len(book_streams),
        "item_type_histogram": histogram,
        "book_start_histogram": book_start_histogram,
        "best_model": best,
        "top_models": rows[:20],
        "diagnostic_models": diagnostic_rows,
        "validation": validation,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Book-Start Item-Type Ledger Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit keeps the current Markov item-type sequential LZ recipe fixed",
        "and retells only the literal/copy item-type ledger. The current ledger",
        "conditions on the previous item globally. The tested ledger uses a",
        "`BOS` context at each declared book start, then conditions on the",
        "previous item type inside the book.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.1f}` |",
        f"| Best book-start type formula bits | `{best['total_bits']:.1f}` |",
        f"| Delta vs current | `{best['delta_vs_current_bits']:.1f}` |",
        f"| Current item-type bits | `{current_item_type_bits:.1f}` |",
        f"| Best book-start item-type bits | `{best['item_type_bits']:.1f}` |",
        f"| Books | `{len(book_streams)}` |",
        f"| Item count | `{len(flat_stream)}` |",
        f"| Book starts with literal | `{book_start_histogram.get('literal', 0)}` |",
        f"| Book starts with copy | `{book_start_histogram.get('copy', 0)}` |",
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
            "## Transition Counts",
            "",
            "| Transition | Count |",
            "|---|---:|",
        ]
    )
    for key, value in best["transition_histogram"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Diagnostics",
            "",
            "The gain comes from using already-declared book boundaries as item-type",
            "context. It does not add a new order, source, or plaintext channel.",
            "Higher-order book-start diagnostics are recorded in JSON but not",
            "promoted unless they beat this ledger under the same declaration cost.",
            "",
            "## Boundary",
            "",
            "This is a mechanical ledger/cost improvement only. It does not alter",
            "row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("42_book_start_item_type_ledger_compile", result, lines)


if __name__ == "__main__":
    main()
