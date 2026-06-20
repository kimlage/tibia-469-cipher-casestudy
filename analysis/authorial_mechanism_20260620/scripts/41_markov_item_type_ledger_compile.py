from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_type_coded_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_markov_type_formula_469.json"
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


def rice_bits(value: int, k: int) -> int:
    if value <= 0:
        raise ValueError(value)
    offset = value - 1
    return (offset >> k) + 1 + k


def markov_type_stream_bits(stream: list[str], alpha: int) -> float:
    if not stream:
        return 0.0
    counts = {previous: {item_type: 0 for item_type in ITEM_TYPES} for previous in ITEM_TYPES}
    totals = {item_type: 0 for item_type in ITEM_TYPES}
    bits = 1.0  # first literal/copy item tag
    previous = stream[0]
    for item_type in stream[1:]:
        probability = (counts[previous][item_type] + alpha) / (totals[previous] + len(ITEM_TYPES) * alpha)
        bits += -math.log2(probability)
        counts[previous][item_type] += 1
        totals[previous] += 1
        previous = item_type
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


def type_runs(stream: list[str]) -> list[dict]:
    runs = []
    for item_type in stream:
        if not runs or runs[-1]["item_type"] != item_type:
            runs.append({"item_type": item_type, "length": 1})
        else:
            runs[-1]["length"] += 1
    return runs


def transition_histogram(stream: list[str]) -> dict[str, int]:
    transitions = Counter()
    for previous, current in zip(stream, stream[1:]):
        transitions[f"{previous}->{current}"] += 1
    return dict(sorted(transitions.items()))


def rle_diagnostics(stream: list[str]) -> dict:
    runs = type_runs(stream)
    gamma_cost = 1 + sum(gamma_bits(run["length"]) for run in runs)
    rice_rows = []
    for k in range(0, 8):
        rice_rows.append(
            {
                "k": k,
                "bits": 1 + gamma_bits(k + 1) + sum(rice_bits(run["length"], k) for run in runs),
            }
        )
    return {
        "run_count": len(runs),
        "run_type_histogram": dict(sorted(Counter(run["item_type"] for run in runs).items())),
        "run_length_histogram": dict(sorted(Counter(run["length"] for run in runs).items())),
        "rle_gamma_bits": gamma_cost,
        "rle_rice_models": rice_rows,
    }


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    validation, item_stream = render_formula_and_item_stream(formula, books)
    if validation["errors"]:
        raise RuntimeError(validation["errors"])

    mdl = formula["mdl_estimate_rough"]
    current_bits = mdl["sequential_lz_digit_address_type_coded_bits"]
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
        stream_bits = markov_type_stream_bits(item_stream, alpha)
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
            }
        )
    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    promoted = best["total_bits"] < current_bits
    classification = "controlled_markov_item_type_ledger_improvement" if promoted else "markov_item_type_ledger_not_promoted"

    histogram = dict(sorted(Counter(item_stream).items()))
    transitions = transition_histogram(item_stream)

    if promoted:
        out = json.loads(json.dumps(formula))
        out["schema"] = "sequential_lz_digit_address_markov_type_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["item_type_model"] = {
            "family": "adaptive_markov_dirichlet_integer_alpha",
            "alphabet": ITEM_TYPES,
            "alpha": best["alpha"],
            "first_symbol_bits": 1,
            "model_declaration_bits": best["model_declaration_bits"],
            "conditioning": "previous_item_type",
        }
        out["policy"]["cost_model"] = (
            "gamma(book_count)+declared_book_length_ledger+adaptive_markov_item_type_ledger+"
            "copy_length_model_declaration+literal_length_model_declaration+"
            "literal_payload_model_declaration+literal_run_lengths+absolute_digit_source_copy_ops"
        )
        out["mdl_estimate_rough"] = {
            **mdl,
            "sequential_lz_digit_address_markov_type_bits": best["total_bits"],
            "previous_sequential_lz_digit_address_type_coded_bits": current_bits,
            "gain_vs_previous_digit_address_type_coded_bits": current_bits - best["total_bits"],
            "fixed_bits": fixed_without_item_type_model + best["model_declaration_bits"],
            "previous_item_type_bits": current_item_type_bits,
            "previous_item_type_stream_bits": current_item_type_stream_bits,
            "item_type_bits": best["item_type_bits"],
            "item_type_stream_bits": best["item_type_stream_bits"],
            "item_type_model_declaration_bits": best["model_declaration_bits"],
            "item_type_gain_bits": current_item_type_bits - best["item_type_bits"],
            "item_type_histogram": histogram,
            "item_type_transition_histogram": transitions,
            "item_type_markov_first_symbol_bits": 1,
        }
        out["validation"]["markov_item_type_ledger_roundtrip_audit"] = validation
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "markov_item_type_ledger_compile.v1",
        "test": "41_markov_item_type_ledger_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_item_type_bits": current_item_type_bits,
        "current_item_type_stream_bits": current_item_type_stream_bits,
        "item_count": len(item_stream),
        "item_type_histogram": histogram,
        "item_type_transition_histogram": transitions,
        "best_model": best,
        "top_models": rows[:20],
        "rle_diagnostics": rle_diagnostics(item_stream),
        "validation": validation,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Markov Item-Type Ledger Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit keeps the current item-type-coded sequential LZ recipe fixed",
        "and retells only the literal/copy item-type ledger. The previous ledger",
        "uses an adaptive two-symbol iid model. Candidate ledgers condition the",
        "next item type on the previous item type, charge the declared integer",
        "`alpha`, and charge one bit for the first item type.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.1f}` |",
        f"| Best Markov type formula bits | `{best['total_bits']:.1f}` |",
        f"| Delta vs current | `{best['delta_vs_current_bits']:.1f}` |",
        f"| Current item-type bits | `{current_item_type_bits:.1f}` |",
        f"| Best Markov item-type bits | `{best['item_type_bits']:.1f}` |",
        f"| Item count | `{len(item_stream)}` |",
        f"| Literal items | `{histogram.get('literal', 0)}` |",
        f"| Copy items | `{histogram.get('copy', 0)}` |",
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
    for key, value in transitions.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Diagnostics",
            "",
            f"RLE over the same stream has `{rle_diagnostics(item_stream)['run_count']}`",
            "runs and is not promoted by this audit; the best tested Markov ledger",
            "is the only cheaper decodable replacement for the current iid ledger.",
            "",
            "## Boundary",
            "",
            "This is a mechanical ledger/cost improvement only. It does not alter",
            "row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("41_markov_item_type_ledger_compile", result, lines)


if __name__ == "__main__":
    main()
