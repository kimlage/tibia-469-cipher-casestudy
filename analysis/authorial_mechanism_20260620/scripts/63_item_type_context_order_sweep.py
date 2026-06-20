from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_context_order_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_context_order_type_context_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

ITEM_TYPES = ["literal", "copy"]
BOS = "BOS"
ALPHA_RANGE = range(1, 33)
ORDER_RANGE = range(1, 8)
ACTIVE_TOTAL_KEY = "sequential_lz_digit_address_forced_length_literal_context_order_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_forced_length_literal_context_order_type_context_bits"


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


def order_declaration_bits(order: int) -> int:
    if order == 1:
        return 0
    return 1 + gamma_bits(order)


def model_declaration_bits(alpha: int, order: int, forced_rule_bits: int) -> int:
    return gamma_bits(alpha + 1) + forced_rule_bits + order_declaration_bits(order)


def validate_roundtrip(formula: dict, books: dict[str, str]) -> dict:
    emitted = ""
    errors = []
    for book in map(str, formula["policy"]["book_order"]):
        parts = []
        for op in formula["book_recipes"][book]["ops"]:
            length = int(op["length"])
            if op["type"] == "literal":
                chunk = op["text"]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "literal_length_mismatch", "op": op})
            elif op["type"] == "copy":
                start = int(op["source_digit_pos"])
                chunk = emitted[start : start + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op": op})
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op": op})
            parts.append(chunk)
            emitted += chunk
        if "".join(parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})
    return {"book_count": len(formula["policy"]["book_order"]), "books_roundtrip_ok": 0 if errors else 70, "errors": errors}


def item_type_context_bits(formula: dict, order: int, alpha: int) -> tuple[float, dict]:
    min_len = int(formula["policy"]["min_len"])
    counts = defaultdict(lambda: {item_type: 0 for item_type in ITEM_TYPES})
    totals = defaultdict(int)
    context_uses = Counter()
    transition_uses = Counter()
    bits = 0.0
    forced_literal_to_copy = 0
    forced_remaining_short_to_literal = 0
    forced_rule_violations = []
    coded_items = 0

    for book in map(str, formula["policy"]["book_order"]):
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        position = 0
        history = []
        for op_index, op in enumerate(ops):
            item_type = op["type"]
            remaining = book_length - position
            previous = history[-1] if history else BOS

            if previous == "literal":
                forced_literal_to_copy += 1
                if item_type != "copy":
                    forced_rule_violations.append(
                        {"rule": "literal_forces_copy", "book": book, "item_index": op_index}
                    )
            elif remaining < min_len:
                forced_remaining_short_to_literal += 1
                if item_type != "literal":
                    forced_rule_violations.append(
                        {
                            "rule": "remaining_short_forces_literal",
                            "book": book,
                            "item_index": op_index,
                            "remaining": remaining,
                        }
                    )
            else:
                padded = [BOS] * order + history
                context = tuple(padded[-order:])
                probability = (counts[context][item_type] + alpha) / (totals[context] + len(ITEM_TYPES) * alpha)
                bits += -math.log2(probability)
                counts[context][item_type] += 1
                totals[context] += 1
                context_uses["|".join(context)] += 1
                transition_uses[f"{'|'.join(context)}->{item_type}"] += 1
                coded_items += 1

            history.append(item_type)
            position += int(op["length"])

    return bits, {
        "coded_items": coded_items,
        "context_count": len(context_uses),
        "context_histogram": dict(sorted(context_uses.items())),
        "transition_histogram": dict(sorted(transition_uses.items())),
        "forced_literal_to_copy": forced_literal_to_copy,
        "forced_remaining_short_to_literal": forced_remaining_short_to_literal,
        "forced_rule_violations": forced_rule_violations,
    }


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    audit = validate_roundtrip(formula, books)
    if audit["errors"]:
        raise RuntimeError(audit)

    current_bits = float(formula["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    current_stream_bits = float(formula["mdl_estimate_rough"]["item_type_stream_bits"])
    current_model_bits = int(formula["policy"]["item_type_model"]["model_declaration_bits"])
    forced_rule_bits = int(formula["policy"]["item_type_model"]["forced_rule_bits"])
    current_alpha = int(formula["policy"]["item_type_model"]["alpha"])
    current_payload_plus_model = current_stream_bits + current_model_bits
    current_without_item_model = current_bits - current_payload_plus_model

    models = []
    for order in ORDER_RANGE:
        order_rows = []
        for alpha in ALPHA_RANGE:
            stream_bits, stats = item_type_context_bits(formula, order, alpha)
            declaration_bits = model_declaration_bits(alpha, order, forced_rule_bits)
            order_rows.append(
                {
                    "model": f"adaptive_item_type_context_order_{order}",
                    "order": order,
                    "alpha": alpha,
                    "item_type_stream_bits": stream_bits,
                    "model_declaration_bits": declaration_bits,
                    "item_type_plus_model_bits": stream_bits + declaration_bits,
                    "total_bits_if_replacing_item_type_model": (
                        current_without_item_model + stream_bits + declaration_bits
                    ),
                    "decodable": True,
                    **stats,
                }
            )
        order_rows.sort(key=lambda row: row["item_type_plus_model_bits"])
        best = dict(order_rows[0])
        best["sweep_top16"] = [dict(row) for row in order_rows[:16]]
        models.append(best)

    models.sort(key=lambda row: row["total_bits_if_replacing_item_type_model"])
    best = models[0]
    promoted = best["total_bits_if_replacing_item_type_model"] < current_bits - 1e-9
    classification = (
        "controlled_item_type_context_order_improvement"
        if promoted
        else "item_type_context_order_retains_order_1"
    )

    if promoted:
        out = {
            "schema": "sequential_lz_digit_address_forced_length_literal_context_order_type_context_formula.v1",
            "classification": classification,
            "translation_delta": "NONE",
            "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
            "scope": "70 raw digit books in numeric order",
            "policy": {
                **formula["policy"],
                "item_type_model": {
                    "family": "adaptive_book_start_item_type_context_order_with_forced_type_rules",
                    "order": best["order"],
                    "alpha": best["alpha"],
                    "alphabet": ITEM_TYPES,
                    "conditioning": (
                        "BOS-padded previous N item types within each declared book; forced item types "
                        "remain in context history but are not charged as coded emissions"
                    ),
                    "deterministic_rules": formula["policy"]["item_type_model"]["deterministic_rules"],
                    "forced_rule_bits": forced_rule_bits,
                    "alpha_declaration_bits": gamma_bits(best["alpha"] + 1),
                    "order_declaration_bits": order_declaration_bits(best["order"]),
                    "model_declaration_bits": best["model_declaration_bits"],
                },
            },
            "book_recipes": formula["book_recipes"],
            "mdl_estimate_rough": {
                **formula["mdl_estimate_rough"],
                "fixed_bits": (
                    float(formula["mdl_estimate_rough"]["fixed_bits"])
                    - current_model_bits
                    + best["model_declaration_bits"]
                ),
                OUT_TOTAL_KEY: best["total_bits_if_replacing_item_type_model"],
                "previous_sequential_lz_digit_address_forced_length_literal_context_order_bits": current_bits,
                "gain_vs_previous_literal_context_order_bits": (
                    current_bits - best["total_bits_if_replacing_item_type_model"]
                ),
                "previous_item_type_stream_bits": current_stream_bits,
                "item_type_context_order_stream_bits": best["item_type_stream_bits"],
                "item_type_context_order": best["order"],
                "item_type_context_alpha": best["alpha"],
                "item_type_model_declaration_bits": best["model_declaration_bits"],
                "item_type_bits": best["item_type_stream_bits"] + best["model_declaration_bits"],
            },
            "item_type_context_summary": {
                "coded_items": best["coded_items"],
                "context_count": best["context_count"],
                "context_histogram": best["context_histogram"],
                "transition_histogram": best["transition_histogram"],
                "forced_literal_to_copy": best["forced_literal_to_copy"],
                "forced_remaining_short_to_literal": best["forced_remaining_short_to_literal"],
            },
            "validation": {
                **formula["validation"],
                "item_type_context_order_roundtrip_audit": audit,
                "item_type_context_order_forced_rule_violations": best["forced_rule_violations"],
            },
            "boundary": formula["boundary"],
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "item_type_context_order_sweep.v1",
        "test": "63_item_type_context_order_sweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_item_type_stream_bits": current_stream_bits,
        "current_item_type_model_declaration_bits": current_model_bits,
        "current_item_type_plus_model_bits": current_payload_plus_model,
        "current_without_item_type_model_bits": current_without_item_model,
        "current_alpha": current_alpha,
        "best_model": best,
        "models": models,
        "promotion_rule": (
            "promote only if a decodable item-type context order beats the active "
            "order-1 book-start Markov ledger after charged alpha, forced-rule, and order bits"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Item-Type Context Order Sweep",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit keeps the book recipe, copy-address ledger, length ledgers,",
        "forced literal-length rule, local repairs, and literal-payload model fixed.",
        "It retests only the literal/copy item-type ledger.",
        "",
        "The existing deterministic rules are retained: a literal item forces the",
        "next in-book item to copy, and a remaining book suffix shorter than",
        "`min_len` forces a literal. Forced emissions remain in the context history",
        "but are not charged as coded item-type emissions.",
        "",
        "## Model Ranking",
        "",
        "| Rank | Order | Alpha | Stream bits | Model bits | Total bits | Delta vs active | Contexts |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(models, start=1):
        lines.append(
            f"| `{rank}` | `{row['order']}` | `{row['alpha']}` | "
            f"`{row['item_type_stream_bits']:.1f}` | `{row['model_declaration_bits']}` | "
            f"`{row['total_bits_if_replacing_item_type_model']:.1f}` | "
            f"`{row['total_bits_if_replacing_item_type_model'] - current_bits:.1f}` | "
            f"`{row['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The active formula is `{current_bits:.1f}` bits. The best item-type",
            f"context candidate is order `{best['order']}` with `alpha={best['alpha']}`,",
            f"costing `{best['total_bits_if_replacing_item_type_model']:.1f}` bits.",
            "",
            "This is a mechanical ledger refinement only. It does not change row0,",
            "introduce plaintext, or claim authorial intent.",
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
    write_result("63_item_type_context_order_sweep", result, lines)


if __name__ == "__main__":
    main()
