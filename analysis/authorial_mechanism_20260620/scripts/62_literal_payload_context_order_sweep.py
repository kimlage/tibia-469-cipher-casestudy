from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_context_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_context_order_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

DIGITS = [str(i) for i in range(10)]
BOS = "^"
ALPHA_RANGE = range(1, 65)
ORDER_RANGE = range(1, 6)
ACTIVE_TOTAL_KEY = "sequential_lz_digit_address_forced_length_literal_context_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_forced_length_literal_context_order_bits"


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


def context_order_bits(order: int) -> int:
    if order == 1:
        return 0
    return gamma_bits(order)


def model_declaration_bits(alpha: int, order: int) -> int:
    # Current order-1 previous-emitted-digit model charges 3 family bits.
    return gamma_bits(alpha + 1) + 3 + context_order_bits(order)


def iter_literal_context_pairs(formula: dict, order: int) -> list[tuple[str, str]]:
    emitted = ""
    pairs = []
    for book in map(str, formula["policy"]["book_order"]):
        for op in formula["book_recipes"][book]["ops"]:
            length = int(op["length"])
            if op["type"] == "literal":
                for digit in op["text"]:
                    context = (BOS * order + emitted)[-order:]
                    pairs.append((context, digit))
                    emitted += digit
            elif op["type"] == "copy":
                start = int(op["source_digit_pos"])
                chunk = emitted[start : start + length]
                if len(chunk) != length:
                    raise ValueError({"book": book, "op": op, "type": "short_copy"})
                emitted += chunk
            else:
                raise ValueError(op)
    return pairs


def adaptive_context_bits(pairs: list[tuple[str, str]], alpha: int) -> float:
    counts = defaultdict(lambda: {digit: 0 for digit in DIGITS})
    totals = defaultdict(int)
    bits = 0.0
    for context, digit in pairs:
        probability = (counts[context][digit] + alpha) / (totals[context] + len(DIGITS) * alpha)
        bits += -math.log2(probability)
        counts[context][digit] += 1
        totals[context] += 1
    return bits


def context_summary(pairs: list[tuple[str, str]]) -> dict:
    counts = Counter(context for context, _digit in pairs)
    return {
        "context_count": len(counts),
        "min_context_uses": min(counts.values()) if counts else 0,
        "max_context_uses": max(counts.values()) if counts else 0,
        "context_histogram_top20": dict(counts.most_common(20)),
    }


def literal_payload_stream(formula: dict) -> str:
    return "".join(
        op["text"]
        for book in map(str, formula["policy"]["book_order"])
        for op in formula["book_recipes"][book]["ops"]
        if op["type"] == "literal"
    )


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


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    audit = validate_roundtrip(formula, books)
    if audit["errors"]:
        raise RuntimeError(audit)

    current_bits = float(formula["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    current_model = formula["policy"]["literal_payload_model"]
    current_payload_bits = float(formula["mdl_estimate_rough"]["adaptive_context_literal_payload_bits"])
    current_model_bits = int(current_model["model_declaration_bits"])
    current_payload_plus_model = current_payload_bits + current_model_bits
    current_without_payload_model = current_bits - current_payload_plus_model
    stream = literal_payload_stream(formula)

    models = [
        {
            "model": "adaptive_prev_emitted_digit_order_1_current",
            "order": 1,
            "alpha": int(current_model["alpha"]),
            "payload_bits": current_payload_bits,
            "model_declaration_bits": current_model_bits,
            "payload_plus_model_bits": current_payload_plus_model,
            "total_bits_if_replacing_payload_model": current_bits,
            "context_summary": context_summary(iter_literal_context_pairs(formula, 1)),
            "decodable": True,
        }
    ]

    for order in ORDER_RANGE:
        pairs = iter_literal_context_pairs(formula, order)
        rows = []
        for alpha in ALPHA_RANGE:
            payload_bits = adaptive_context_bits(pairs, alpha)
            declaration_bits = model_declaration_bits(alpha, order)
            rows.append(
                {
                    "model": f"adaptive_prev_emitted_digit_order_{order}",
                    "order": order,
                    "alpha": alpha,
                    "payload_bits": payload_bits,
                    "model_declaration_bits": declaration_bits,
                    "payload_plus_model_bits": payload_bits + declaration_bits,
                    "total_bits_if_replacing_payload_model": (
                        current_without_payload_model + payload_bits + declaration_bits
                    ),
                    "context_summary": context_summary(pairs),
                    "decodable": True,
                }
            )
        rows.sort(key=lambda row: row["payload_plus_model_bits"])
        best = dict(rows[0])
        best["sweep_top16"] = [dict(row) for row in rows[:16]]
        if order != 1:
            models.append(best)
        else:
            models[0]["sweep_top16"] = [dict(row) for row in rows[:16]]

    models.sort(key=lambda row: row["total_bits_if_replacing_payload_model"])
    best = models[0]
    promoted = best["total_bits_if_replacing_payload_model"] < current_bits - 1e-9
    classification = (
        "controlled_literal_payload_context_order_improvement"
        if promoted
        else "literal_payload_context_order_retains_order_1"
    )

    if promoted:
        out = {
            "schema": "sequential_lz_digit_address_forced_length_literal_context_order_formula.v1",
            "classification": classification,
            "translation_delta": "NONE",
            "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
            "scope": "70 raw digit books in numeric order",
            "policy": {
                **formula["policy"],
                "literal_payload_model": {
                    "family": "adaptive_prev_emitted_digit_context_order",
                    "order": best["order"],
                    "alpha": best["alpha"],
                    "alphabet": DIGITS,
                    "bos_symbol": BOS,
                    "context_source": (
                        "previous N emitted digits in the already generated digit stream, "
                        "left-padded with BOS before enough digits exist"
                    ),
                    "model_declaration_bits": best["model_declaration_bits"],
                    "family_bits_charged": 3,
                    "context_order_bits_charged": context_order_bits(best["order"]),
                    "decodable": True,
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
                OUT_TOTAL_KEY: best["total_bits_if_replacing_payload_model"],
                "previous_sequential_lz_digit_address_forced_length_literal_context_bits": current_bits,
                "gain_vs_previous_literal_context_bits": (
                    current_bits - best["total_bits_if_replacing_payload_model"]
                ),
                "previous_context_literal_payload_bits": current_payload_bits,
                "adaptive_context_order_literal_payload_bits": best["payload_bits"],
                "literal_payload_model_declaration_bits": best["model_declaration_bits"],
                "literal_payload_context_order": best["order"],
                "literal_payload_context_alpha": best["alpha"],
            },
            "literal_payload_digit_histogram": dict(sorted(Counter(stream).items())),
            "literal_payload_context_summary": best["context_summary"],
            "validation": {
                **formula["validation"],
                "literal_payload_context_order_roundtrip_audit": audit,
            },
            "boundary": formula["boundary"],
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "literal_payload_context_order_sweep.v1",
        "test": "62_literal_payload_context_order_sweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_payload_plus_model_bits": current_payload_plus_model,
        "current_without_payload_model_bits": current_without_payload_model,
        "literal_digits": len(stream),
        "literal_digit_histogram": dict(sorted(Counter(stream).items())),
        "best_model": best,
        "models": models,
        "promotion_rule": (
            "promote only if a decodable previous-emitted-digit context order beats "
            "the active order-1 context model after charged alpha, family, and order bits"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Literal Payload Context Order Sweep",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit keeps the full book recipe and every non-payload ledger fixed",
        "after the promoted previous-emitted-digit literal payload model. It tests",
        "whether longer deterministic contexts over the already emitted digit stream",
        "reduce the final literal payload cost.",
        "",
        "The active order-1 context is included as the baseline. Higher orders are",
        "charged for alpha, the context family, and a declared context-order cost.",
        "",
        "## Model Ranking",
        "",
        "| Rank | Order | Alpha | Payload bits | Model bits | Total bits | Delta vs active | Contexts |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(models, start=1):
        lines.append(
            f"| `{rank}` | `{row['order']}` | `{row['alpha']}` | "
            f"`{row['payload_bits']:.1f}` | `{row['model_declaration_bits']}` | "
            f"`{row['total_bits_if_replacing_payload_model']:.1f}` | "
            f"`{row['total_bits_if_replacing_payload_model'] - current_bits:.1f}` | "
            f"`{row['context_summary']['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The active contextual formula remains `{current_bits:.1f}` bits before",
            "this sweep. A higher-order model is promoted only if it beats that",
            "active order-1 context after all declaration bits are charged.",
            "",
            "This is a mechanical payload-coding audit only. It does not change row0,",
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
    write_result("62_literal_payload_context_order_sweep", result, lines)


if __name__ == "__main__":
    main()
