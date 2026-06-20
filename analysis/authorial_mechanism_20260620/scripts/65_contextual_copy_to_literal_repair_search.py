from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_context_order_type_context_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_copy_to_literal_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
SCORER = HERE / "scripts/64_contextual_local_repair_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_forced_length_literal_context_order_type_context_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_copy_to_literal_bits"


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


def replace_copy_with_literal(formula: dict, repair: dict) -> dict:
    out = copy.deepcopy(formula)
    out["book_recipes"][repair["book"]]["ops"][repair["op_index"]] = {
        "type": "literal",
        "text": repair["text"],
        "length": repair["length"],
    }
    return out


def find_best_copy_to_literal(formula: dict, books: dict[str, str], current_bits: float, scorer) -> tuple[dict | None, int, int]:
    emitted = ""
    tested = 0
    invalid = 0
    best = None
    for book in map(str, formula["policy"]["book_order"]):
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            length = int(op["length"])
            if op["type"] == "literal":
                chunk = op["text"]
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                repair = {
                    "book": book,
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "length": length,
                    "source_digit_pos": source_digit_pos,
                    "text": chunk,
                }
                tested += 1
                candidate = replace_copy_with_literal(formula, repair)
                score = scorer.score_formula(candidate, books)
                if score["validation"]["errors"]:
                    invalid += 1
                else:
                    delta = score["total_bits"] - current_bits
                    if best is None or delta < best["delta_bits"]:
                        best = {**repair, "delta_bits": delta, "score": score}
            else:
                raise ValueError(op)
            emitted += chunk
            book_pos += length
    return best, tested, invalid


def main() -> None:
    scorer = load_scorer()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = scorer.score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])

    best, tested, invalid = find_best_copy_to_literal(formula, books, current_bits, scorer)
    promoted = best is not None and best["delta_bits"] < -1e-9
    classification = (
        "controlled_contextual_copy_to_literal_improvement"
        if promoted
        else "contextual_copy_to_literal_not_promoted"
    )

    if promoted:
        out = replace_copy_with_literal(formula, best)
        score = best["score"]
        out.update(
            {
                "schema": "sequential_lz_digit_address_contextual_copy_to_literal_formula.v1",
                "classification": classification,
                "translation_delta": "NONE",
                "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
                "mdl_estimate_rough": {
                    **out["mdl_estimate_rough"],
                    OUT_TOTAL_KEY: score["total_bits"],
                    "previous_sequential_lz_digit_address_forced_length_literal_context_order_type_context_bits": current_bits,
                    "gain_vs_previous_context_order_type_context_bits": current_bits - score["total_bits"],
                    "literal_bits_no_payload": score["literal_bits_no_payload"],
                    "adaptive_context_order_literal_payload_bits": score["literal_payload_bits"],
                    "copy_bits": score["copy_bits"],
                    "copy_address_bits": score["copy_address_bits"],
                    "copy_length_code_bits": score["copy_length_code_bits"],
                    "item_type_context_order_stream_bits": score["item_type_stream_bits"],
                    "literal_runs": score["literal_runs"],
                    "literal_digits": score["literal_digits"],
                    "copy_items": score["copy_items"],
                    "copied_digits": score["copied_digits"],
                    "forced_literal_length_count": score["forced_literal_length_count"],
                    "forced_literal_length_saved_bits": score["forced_literal_length_saved_bits"],
                },
                "contextual_copy_to_literal_repair": {
                    key: value for key, value in best.items() if key not in {"score"}
                },
                "validation": {
                    **out["validation"],
                    "contextual_copy_to_literal_roundtrip_audit": score["validation"],
                    "literal_payload_context_stats": score["literal_payload_context_stats"],
                    "item_type_context_stats": score["item_type_context_stats"],
                },
                "boundary": out["boundary"],
            }
        )
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "contextual_copy_to_literal_repair_search.v1",
        "test": "65_contextual_copy_to_literal_repair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "tested_copy_to_literal_repairs": tested,
        "invalid_copy_to_literal_repairs": invalid,
        "best_repair": best,
        "promotion_rule": (
            "promote only if replacing one existing copy item with an explicit literal "
            "beats the active contextual formula under exact rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Contextual Copy-to-Literal Repair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests the reverse of the usual literal-to-copy repair. After",
        "contextual payload coding, a short copy can become more expensive than",
        "spelling the same digits as a literal. Every candidate is exactly rescored",
        "with literal lengths, contextual literal payload, copy bits, and contextual",
        "item-type bits with deterministic forced rules.",
        "",
        "## Result",
        "",
        f"- Current formula bits: `{current_bits:.1f}`",
        f"- Copy-to-literal repairs tested: `{tested}`",
        f"- Invalid under forced-rule/roundtrip checks: `{invalid}`",
    ]
    if best is None:
        lines.append("- Best repair: none found")
    else:
        lines.extend(
            [
                f"- Best repair delta: `{best['delta_bits']:.1f}` bits",
                f"- Best repair: book `{best['book']}`, copy op `{best['op_index']}`,",
                f"  book position `{best['book_pos']}`, length `{best['length']}`,",
                f"  text `{best['text']}`, source digit position `{best['source_digit_pos']}`",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a mechanical recipe audit only. It preserves exact book",
            "roundtrip and does not introduce plaintext, row0 meaning, or authorial",
            "intent.",
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
    write_result("65_contextual_copy_to_literal_repair_search", result, lines)


if __name__ == "__main__":
    main()
