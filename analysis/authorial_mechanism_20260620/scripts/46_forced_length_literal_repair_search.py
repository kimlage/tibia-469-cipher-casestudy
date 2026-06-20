from __future__ import annotations

import copy
import json
import math
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_forced_literal_length_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_forced_length_literal_repair_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_forced_literal_length_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_forced_length_literal_repair_bits"
ITEM_TYPES = ["literal", "copy"]
BOS = "BOS"
DIGITS = [str(i) for i in range(10)]


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


def adaptive_payload_bits(stream: str, alpha: int) -> float:
    counts = {digit: 0 for digit in DIGITS}
    total = 0
    bits = 0.0
    for digit in stream:
        probability = (counts[digit] + alpha) / (total + len(DIGITS) * alpha)
        bits += -math.log2(probability)
        counts[digit] += 1
        total += 1
    return bits


def item_type_stream_bits(book_streams: list[dict], min_len: int, alpha: int) -> tuple[float, dict]:
    counts = defaultdict(lambda: {item_type: 0 for item_type in ITEM_TYPES})
    totals = defaultdict(int)
    bits = 0.0
    forced_literal_to_copy = 0
    forced_remaining_short_to_literal = 0
    violations = []

    for row in book_streams:
        previous = BOS
        position = 0
        for index, item_type in enumerate(row["item_stream"]):
            remaining = row["book_length"] - position
            if previous == "literal":
                forced_literal_to_copy += 1
                if item_type != "copy":
                    violations.append({"rule": "literal_forces_copy", "book": row["book"], "item_index": index})
            elif remaining < min_len:
                forced_remaining_short_to_literal += 1
                if item_type != "literal":
                    violations.append(
                        {
                            "rule": "remaining_short_forces_literal",
                            "book": row["book"],
                            "item_index": index,
                            "remaining": remaining,
                        }
                    )
            else:
                probability = (counts[previous][item_type] + alpha) / (totals[previous] + len(ITEM_TYPES) * alpha)
                bits += -math.log2(probability)
                counts[previous][item_type] += 1
                totals[previous] += 1

            position += row["item_lengths"][index]
            previous = item_type

    return bits, {
        "forced_literal_to_copy": forced_literal_to_copy,
        "forced_remaining_short_to_literal": forced_remaining_short_to_literal,
        "forced_rule_violations": violations,
    }


def score_formula(formula: dict, books: dict[str, str]) -> dict:
    order = [str(book) for book in formula["policy"]["book_order"]]
    min_len = int(formula["policy"]["min_len"])
    copy_k = int(formula["policy"]["copy_length_model"]["k"])
    literal_k = int(formula["policy"]["literal_run_length_model"]["k"])
    payload_alpha = int(formula["policy"]["literal_payload_model"]["alpha"])
    item_type_alpha = int(formula["policy"]["item_type_model"]["alpha"])
    fixed_bits = float(formula["mdl_estimate_rough"]["fixed_bits"])

    emitted_digits = ""
    literal_payload = []
    literal_bits_no_payload = 0.0
    copy_bits = 0.0
    copy_address_bits = 0.0
    copy_length_code_bits = 0
    literal_runs = 0
    literal_digits = 0
    copy_items = 0
    copied_digits = 0
    forced_literal_length_count = 0
    forced_literal_length_saved_bits = 0
    book_streams = []
    errors = []

    for book in order:
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        parts = []
        item_stream = []
        item_lengths = []
        position = 0
        for op in ops:
            item_type = op["type"]
            length = int(op["length"])
            remaining = book_length - position
            item_stream.append(item_type)
            item_lengths.append(length)
            if item_type == "literal":
                text = op["text"]
                if len(text) != length:
                    errors.append({"book": book, "type": "literal_length_mismatch", "op": op})
                if remaining < min_len:
                    forced_literal_length_count += 1
                    saved_bits = rice_bits(length + 1, literal_k)
                    forced_literal_length_saved_bits += saved_bits
                    if length != remaining:
                        errors.append(
                            {
                                "book": book,
                                "type": "forced_literal_does_not_consume_remaining",
                                "remaining": remaining,
                                "length": length,
                            }
                        )
                else:
                    literal_bits_no_payload += rice_bits(length + 1, literal_k)
                literal_payload.append(text)
                literal_runs += 1
                literal_digits += length
                chunk = text
            elif item_type == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                chunk = emitted_digits[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op": op})
                address_bits = math.log2(max(2, len(emitted_digits)))
                length_bits = rice_bits(length - min_len + 1, copy_k)
                copy_bits += address_bits + length_bits
                copy_address_bits += address_bits
                copy_length_code_bits += length_bits
                copy_items += 1
                copied_digits += length
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op": op})
            parts.append(chunk)
            emitted_digits += chunk
            position += length
        if "".join(parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})
        book_streams.append(
            {
                "book": book,
                "book_length": book_length,
                "item_stream": item_stream,
                "item_lengths": item_lengths,
            }
        )

    payload_stream = "".join(literal_payload)
    payload_bits = adaptive_payload_bits(payload_stream, payload_alpha)
    item_bits, item_stats = item_type_stream_bits(book_streams, min_len, item_type_alpha)
    errors.extend(item_stats["forced_rule_violations"])
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
        **item_stats,
        "validation": {
            "book_count": len(order),
            "books_roundtrip_ok": 0 if errors else len(order),
            "errors": errors,
        },
    }


def iter_literal_contexts(formula: dict):
    emitted_digits = ""
    for book in map(str, formula["policy"]["book_order"]):
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            length = int(op["length"])
            if op["type"] == "literal":
                yield {
                    "book": book,
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "emitted_before_op": emitted_digits,
                    "text": op["text"],
                }
                emitted_digits += op["text"]
            elif op["type"] == "copy":
                chunk = emitted_digits[int(op["source_digit_pos"]) : int(op["source_digit_pos"]) + length]
                emitted_digits += chunk
            else:
                raise ValueError(op)
            book_pos += length


def apply_repair(formula: dict, repair: dict) -> dict:
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


def find_best_single_repair(formula: dict, books: dict[str, str], current_bits: float) -> tuple[dict | None, int]:
    min_len = int(formula["policy"]["min_len"])
    best = None
    tested = 0
    for ctx in iter_literal_contexts(formula):
        text = ctx["text"]
        for start in range(len(text)):
            available = ctx["emitted_before_op"] + text[:start]
            max_len = len(text) - start
            for length in range(min_len, max_len + 1):
                chunk = text[start : start + length]
                source_digit_pos = available.find(chunk)
                if source_digit_pos < 0:
                    continue
                tested += 1
                repair = {
                    "book": ctx["book"],
                    "op_index": ctx["op_index"],
                    "book_pos": ctx["book_pos"],
                    "literal_offset": start,
                    "source_digit_pos": source_digit_pos,
                    "length": length,
                    "chunk": chunk,
                }
                score = score_formula(apply_repair(formula, repair), books)
                if score["validation"]["errors"]:
                    continue
                delta = score["total_bits"] - current_bits
                row = {**repair, "total_bits": score["total_bits"], "delta_vs_current_bits": delta}
                if best is None or row["total_bits"] < best["total_bits"]:
                    best = row
    return best, tested


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_score = score_formula(formula, books)
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"]["errors"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    best, candidates_tested = find_best_single_repair(formula, books, current_bits)
    promoted = best is not None and best["total_bits"] < current_bits
    classification = (
        "controlled_forced_length_literal_repair_improvement"
        if promoted
        else "forced_length_literal_repair_none_promoted"
    )

    followup_best = None
    followup_tested = 0
    output_score = None
    if promoted:
        out = apply_repair(formula, best)
        output_score = score_formula(out, books)
        followup_best, followup_tested = find_best_single_repair(out, books, output_score["total_bits"])
        out["schema"] = "sequential_lz_digit_address_forced_length_literal_repair_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["mdl_estimate_rough"] = {
            **formula["mdl_estimate_rough"],
            OUT_TOTAL_KEY: output_score["total_bits"],
            "previous_sequential_lz_digit_address_forced_literal_length_bits": current_bits,
            "gain_vs_previous_digit_address_forced_literal_length_bits": current_bits - output_score["total_bits"],
            "literal_bits": output_score["literal_bits_no_payload"] + output_score["literal_payload_bits"],
            "literal_bits_no_payload": output_score["literal_bits_no_payload"],
            "adaptive_literal_payload_bits": output_score["literal_payload_bits"],
            "copy_bits": output_score["copy_bits"],
            "copy_address_bits": output_score["copy_address_bits"],
            "copy_length_code_bits": output_score["copy_length_code_bits"],
            "item_type_stream_bits": output_score["item_type_stream_bits"],
            "item_type_bits": output_score["item_type_stream_bits"]
            + formula["mdl_estimate_rough"]["item_type_model_declaration_bits"],
            "literal_runs": output_score["literal_runs"],
            "literal_digits": output_score["literal_digits"],
            "copy_items": output_score["copy_items"],
            "copied_digits": output_score["copied_digits"],
            "forced_literal_length_count": output_score["forced_literal_length_count"],
            "forced_literal_length_saved_bits": output_score["forced_literal_length_saved_bits"],
        }
        out["validation"]["forced_length_literal_repair_roundtrip_audit"] = output_score["validation"]
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "forced_length_literal_repair_search.v1",
        "test": "46_forced_length_literal_repair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score": current_score,
        "candidates_tested": candidates_tested,
        "best_single_repair": best,
        "followup_candidates_tested_after_best_repair": followup_tested,
        "followup_best_after_best_repair": followup_best,
        "output_score": output_score,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Forced-Length Literal Repair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests one-step literal-to-copy repairs after the formula",
        "added forced suffix literal lengths. Each candidate is rescored with",
        "the full active model: adaptive literal payload, forced literal lengths,",
        "digit-only absolute copy addresses, copy length coding, and the",
        "book-start Markov item-type stream with deterministic type rules.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.1f}` |",
        f"| Candidates tested | `{candidates_tested}` |",
    ]
    if best is not None:
        lines.extend(
            [
                f"| Best candidate bits | `{best['total_bits']:.1f}` |",
                f"| Best candidate delta | `{best['delta_vs_current_bits']:.1f}` |",
            ]
        )
    lines.extend(
        [
            "",
            "## Best Candidate",
            "",
            "| Book | Literal offset | Chunk | Source digit pos | Length | Delta |",
            "|---:|---:|---|---:|---:|---:|",
        ]
    )
    if best is not None:
        lines.append(
            f"| `{best['book']}` | `{best['literal_offset']}` | `{best['chunk']}` | "
            f"`{best['source_digit_pos']}` | `{best['length']}` | "
            f"`{best['delta_vs_current_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Follow-Up Check",
            "",
        ]
    )
    if followup_best is None:
        lines.append("No promoted repair was applied, so no follow-up repair search was needed.")
    else:
        lines.extend(
            [
                f"After applying the best repair, `{followup_tested}` further one-step",
                "candidates were tested. The best follow-up candidate is not cheaper:",
                "",
                "| Book | Chunk | Delta vs repaired |",
                "|---:|---|---:|",
                f"| `{followup_best['book']}` | `{followup_best['chunk']}` | "
                f"`{followup_best['delta_vs_current_bits']:.1f}` |",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "A candidate is promoted only if exact rescoring beats the active",
            "forced-literal-length formula. A non-promoted best candidate remains",
            "a local frontier audit, not semantic progress.",
            "",
            "## Boundary",
            "",
            "This is a mechanical recipe audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("46_forced_length_literal_repair_search", result, lines)


if __name__ == "__main__":
    main()
