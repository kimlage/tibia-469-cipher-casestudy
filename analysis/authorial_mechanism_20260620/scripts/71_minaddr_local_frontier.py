from __future__ import annotations

import copy
import json
import math
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair_bits"

DIGITS = [str(i) for i in range(10)]
ITEM_TYPES = ["literal", "copy"]
BOS_DIGIT = "^"
BOS_ITEM = "BOS"


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
    return ((value - 1) >> k) + 1 + k


def truncated_binary_bits(symbol_count: int, index: int) -> int:
    if symbol_count <= 0:
        raise ValueError(symbol_count)
    if not 0 <= index < symbol_count:
        raise ValueError((symbol_count, index))
    if symbol_count == 1:
        return 0
    floor_bits = int(math.floor(math.log2(symbol_count)))
    short_count = (1 << (floor_bits + 1)) - symbol_count
    return floor_bits if index < short_count else floor_bits + 1


def payload_context_bits(formula: dict) -> tuple[float, dict]:
    model = formula["policy"]["literal_payload_model"]
    order = int(model["order"])
    alpha = float(model["alpha"])
    counts = defaultdict(lambda: {digit: 0.0 for digit in DIGITS})
    totals = defaultdict(float)
    context_uses = defaultdict(int)
    emitted = ""
    bits = 0.0

    for book in map(str, formula["policy"]["book_order"]):
        for op in formula["book_recipes"][book]["ops"]:
            length = int(op["length"])
            if op["type"] == "literal":
                for digit in op["text"]:
                    context = (BOS_DIGIT * order + emitted)[-order:]
                    probability = (counts[context][digit] + alpha) / (totals[context] + len(DIGITS) * alpha)
                    bits += -math.log2(probability)
                    counts[context][digit] += 1.0
                    totals[context] += 1.0
                    context_uses[context] += 1
                    emitted += digit
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    raise ValueError({"book": book, "type": "short_copy", "op": op})
                emitted += chunk
            else:
                raise ValueError(op)

    return bits, {
        "context_count": len(context_uses),
        "context_histogram": dict(sorted(context_uses.items())),
    }


def item_type_context_bits(formula: dict) -> tuple[float, dict]:
    model = formula["policy"]["item_type_model"]
    order = int(model["order"])
    alpha = float(model["alpha"])
    min_len = int(formula["policy"]["min_len"])
    counts = defaultdict(lambda: {item_type: 0.0 for item_type in ITEM_TYPES})
    totals = defaultdict(float)
    context_uses = defaultdict(int)
    bits = 0.0
    coded_items = 0
    forced_literal_to_copy = 0
    forced_remaining_short_to_literal = 0
    violations = []

    for book in map(str, formula["policy"]["book_order"]):
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        position = 0
        history = []
        for op_index, op in enumerate(ops):
            item_type = op["type"]
            remaining = book_length - position
            previous = history[-1] if history else BOS_ITEM
            if previous == "literal":
                forced_literal_to_copy += 1
                if item_type != "copy":
                    violations.append({"rule": "literal_forces_copy", "book": book, "item_index": op_index})
            elif remaining < min_len:
                forced_remaining_short_to_literal += 1
                if item_type != "literal":
                    violations.append(
                        {
                            "rule": "remaining_short_forces_literal",
                            "book": book,
                            "item_index": op_index,
                            "remaining": remaining,
                        }
                    )
            else:
                context = tuple(([BOS_ITEM] * order + history)[-order:])
                probability = (counts[context][item_type] + alpha) / (totals[context] + len(ITEM_TYPES) * alpha)
                bits += -math.log2(probability)
                counts[context][item_type] += 1.0
                totals[context] += 1.0
                context_uses["|".join(context)] += 1
                coded_items += 1
            history.append(item_type)
            position += int(op["length"])

    return bits, {
        "coded_items": coded_items,
        "context_count": len(context_uses),
        "context_histogram": dict(sorted(context_uses.items())),
        "forced_literal_to_copy": forced_literal_to_copy,
        "forced_remaining_short_to_literal": forced_remaining_short_to_literal,
        "forced_rule_violations": violations,
    }


def score_formula(formula: dict, books: dict[str, str]) -> dict:
    order = [str(book) for book in formula["policy"]["book_order"]]
    min_len = int(formula["policy"]["min_len"])
    literal_k = int(formula["policy"]["literal_run_length_model"]["k"])
    fixed_bits = float(formula["mdl_estimate_rough"]["fixed_bits"])

    emitted = ""
    literal_bits_no_payload = 0.0
    copy_address_bits = 0.0
    copy_length_code_bits = 0
    literal_runs = 0
    literal_digits = 0
    copy_items = 0
    copied_digits = 0
    forced_literal_length_count = 0
    forced_literal_length_saved_bits = 0
    errors = []

    for book in order:
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        parts = []
        position = 0
        for op_index, op in enumerate(ops):
            item_type = op["type"]
            length = int(op["length"])
            remaining = book_length - position
            if item_type == "literal":
                text = op["text"]
                if len(text) != length:
                    errors.append({"book": book, "type": "literal_length_mismatch", "op_index": op_index})
                if remaining < min_len:
                    forced_literal_length_count += 1
                    forced_literal_length_saved_bits += rice_bits(length + 1, literal_k)
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
                else:
                    literal_bits_no_payload += rice_bits(length + 1, literal_k)
                literal_runs += 1
                literal_digits += length
                chunk = text
            elif item_type == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                emitted_len = len(emitted)
                legal_source_count = max(1, emitted_len - min_len + 1)
                if source_digit_pos >= legal_source_count:
                    errors.append(
                        {
                            "book": book,
                            "type": "source_outside_min_len_bound",
                            "op_index": op_index,
                            "source_digit_pos": source_digit_pos,
                            "legal_source_count": legal_source_count,
                        }
                    )
                copy_address_bits += math.log2(max(2, legal_source_count))
                max_length = min(remaining, emitted_len - source_digit_pos)
                symbol_count = max_length - min_len + 1
                length_index = length - min_len
                if symbol_count <= 0 or not 0 <= length_index < symbol_count:
                    errors.append(
                        {
                            "book": book,
                            "type": "copy_length_outside_bounds",
                            "op_index": op_index,
                            "length": length,
                            "max_length": max_length,
                            "symbol_count": symbol_count,
                        }
                    )
                    symbol_count = max(1, symbol_count)
                    length_index = max(0, min(length_index, symbol_count - 1))
                copy_length_code_bits += truncated_binary_bits(symbol_count, length_index)
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op_index": op_index})
                copy_items += 1
                copied_digits += length
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op_index": op_index, "op": op})
            parts.append(chunk)
            emitted += chunk
            position += length
        if "".join(parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})

    payload_bits, payload_stats = payload_context_bits(formula)
    item_bits, item_stats = item_type_context_bits(formula)
    errors.extend(item_stats["forced_rule_violations"])
    copy_bits = copy_address_bits + copy_length_code_bits
    total_bits = fixed_bits + literal_bits_no_payload + payload_bits + copy_bits + item_bits
    return {
        "total_bits": total_bits,
        "fixed_bits": fixed_bits,
        "literal_bits_no_payload": literal_bits_no_payload,
        "literal_payload_bits": payload_bits,
        "copy_bits": copy_bits,
        "copy_address_bits": copy_address_bits,
        "copy_length_code_bits": copy_length_code_bits,
        "item_type_stream_bits": item_bits,
        "literal_runs": literal_runs,
        "literal_digits": literal_digits,
        "copy_items": copy_items,
        "copied_digits": copied_digits,
        "forced_literal_length_count": forced_literal_length_count,
        "forced_literal_length_saved_bits": forced_literal_length_saved_bits,
        "literal_payload_context_stats": payload_stats,
        "item_type_context_stats": item_stats,
        "validation": {
            "book_count": len(order),
            "books_roundtrip_ok": 0 if errors else len(order),
            "errors": errors,
        },
    }


def iter_contexts(formula: dict):
    emitted = ""
    for book in map(str, formula["policy"]["book_order"]):
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            length = int(op["length"])
            if op["type"] == "literal":
                yield {
                    "kind": "literal",
                    "book": book,
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "emitted_before_op": emitted,
                    "text": op["text"],
                }
                emitted += op["text"]
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                yield {
                    "kind": "copy",
                    "book": book,
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "emitted_before_op": emitted,
                    "text": chunk,
                    "op": op,
                }
                emitted += chunk
            else:
                raise ValueError(op)
            book_pos += length


def apply_literal_to_copy(formula: dict, repair: dict) -> dict:
    out = copy.deepcopy(formula)
    ops = out["book_recipes"][repair["book"]]["ops"]
    original = ops[repair["op_index"]]
    text = original["text"]
    start = repair["literal_offset"]
    length = repair["length"]
    replacement = []
    if start:
        replacement.append({"type": "literal", "text": text[:start], "length": start})
    replacement.append(
        {
            "type": "copy",
            "source_digit_pos": repair["source_digit_pos"],
            "length": length,
            "target_start": repair["book_pos"] + start,
        }
    )
    suffix = text[start + length :]
    if suffix:
        replacement.append({"type": "literal", "text": suffix, "length": len(suffix)})
    ops[repair["op_index"] : repair["op_index"] + 1] = replacement
    return out


def apply_copy_to_literal(formula: dict, repair: dict) -> dict:
    out = copy.deepcopy(formula)
    ops = out["book_recipes"][repair["book"]]["ops"]
    ops[repair["op_index"]] = {
        "type": "literal",
        "text": repair["text"],
        "length": len(repair["text"]),
    }
    return out


def find_best_repair(formula: dict, books: dict[str, str], current_bits: float) -> tuple[dict | None, dict]:
    min_len = int(formula["policy"]["min_len"])
    best = None
    counts = {"literal_to_copy_tested": 0, "copy_to_literal_tested": 0}
    for context in iter_contexts(formula):
        if context["kind"] == "literal":
            text = context["text"]
            for start in range(len(text)):
                available = context["emitted_before_op"] + text[:start]
                for length in range(min_len, len(text) - start + 1):
                    chunk = text[start : start + length]
                    source_digit_pos = available.find(chunk)
                    if source_digit_pos < 0:
                        continue
                    repair = {
                        "edit_type": "literal_to_copy",
                        "book": context["book"],
                        "op_index": context["op_index"],
                        "book_pos": context["book_pos"],
                        "literal_offset": start,
                        "length": length,
                        "source_digit_pos": source_digit_pos,
                        "text": chunk,
                    }
                    score = score_formula(apply_literal_to_copy(formula, repair), books)
                    counts["literal_to_copy_tested"] += 1
                    if score["validation"]["errors"]:
                        continue
                    delta = score["total_bits"] - current_bits
                    if best is None or delta < best["delta_bits"]:
                        best = {**repair, "delta_bits": delta, "score": score}
        elif context["kind"] == "copy":
            repair = {
                "edit_type": "copy_to_literal",
                "book": context["book"],
                "op_index": context["op_index"],
                "book_pos": context["book_pos"],
                "length": len(context["text"]),
                "text": context["text"],
            }
            score = score_formula(apply_copy_to_literal(formula, repair), books)
            counts["copy_to_literal_tested"] += 1
            if score["validation"]["errors"]:
                continue
            delta = score["total_bits"] - current_bits
            if best is None or delta < best["delta_bits"]:
                best = {**repair, "delta_bits": delta, "score": score}
    return best, counts


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    best, counts = find_best_repair(formula, books, current_bits)
    promoted = best is not None and best["delta_bits"] < -1e-9
    classification = "controlled_minaddr_local_repair_improvement" if promoted else "minaddr_local_frontier_closed"

    if promoted:
        if best["edit_type"] == "literal_to_copy":
            out = apply_literal_to_copy(formula, best)
        else:
            out = apply_copy_to_literal(formula, best)
        score = best["score"]
        out.update(
            {
                "schema": "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair_formula.v1",
                "classification": classification,
                "translation_delta": "NONE",
                "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
                "mdl_estimate_rough": {
                    **out["mdl_estimate_rough"],
                    OUT_TOTAL_KEY: score["total_bits"],
                    "previous_sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_bits": current_bits,
                    "gain_vs_previous_minaddr_bits": current_bits - score["total_bits"],
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
                "minaddr_local_repair": {key: value for key, value in best.items() if key != "score"},
                "validation": {
                    **out["validation"],
                    "minaddr_local_repair_roundtrip_audit": score["validation"],
                    "literal_payload_context_stats": score["literal_payload_context_stats"],
                    "item_type_context_stats": score["item_type_context_stats"],
                },
                "boundary": out["boundary"],
            }
        )
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "minaddr_local_frontier.v1",
        "test": "71_minaddr_local_frontier",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "candidate_counts": counts,
        "best_repair": best,
        "promotion_rule": (
            "promote only if one exact literal-to-copy or copy-to-literal local edit beats "
            "the active min_len-bounded address formula under full rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Minaddr Local Frontier",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests the immediate local recipe frontier after bounded copy",
        "lengths and min_len-bounded source addresses changed the exact cost model.",
        "It scores both single literal-to-copy and single copy-to-literal edits",
        "with the active payload context, item-type context, forced rules, bounded",
        "copy lengths, and min_len-bounded absolute addresses.",
        "",
        "## Result",
        "",
        f"- Current formula bits: `{current_bits:.3f}`",
        f"- Literal-to-copy candidates tested: `{counts['literal_to_copy_tested']}`",
        f"- Copy-to-literal candidates tested: `{counts['copy_to_literal_tested']}`",
    ]
    if best is None:
        lines.append("- Best repair: none found")
    else:
        lines.extend(
            [
                f"- Best repair type: `{best['edit_type']}`",
                f"- Best repair delta: `{best['delta_bits']:.3f}` bits",
                f"- Best repair: book `{best['book']}`, op `{best['op_index']}`, text `{best['text']}`,",
                f"  length `{best['length']}`",
            ]
        )
        if best["edit_type"] == "literal_to_copy":
            lines.extend(
                [
                    f"- Literal offset: `{best['literal_offset']}`",
                    f"- Source digit position: `{best['source_digit_pos']}`",
                ]
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A local edit is promoted only when exact rescoring remains cheaper and",
            "70/70 roundtrip plus forced-rule validation still pass. This is a",
            "mechanical recipe audit only; it does not introduce plaintext.",
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
    write_result("71_minaddr_local_frontier", result, lines)


if __name__ == "__main__":
    main()
