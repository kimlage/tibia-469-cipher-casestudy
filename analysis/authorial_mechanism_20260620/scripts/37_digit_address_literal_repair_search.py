from __future__ import annotations

import copy
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_literal_repair_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

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


def score_formula(formula: dict, books: dict[str, str]) -> dict:
    order = [str(book) for book in formula["policy"]["book_order"]]
    min_len = int(formula["policy"]["min_len"])
    copy_k = int(formula["policy"]["copy_length_model"]["k"])
    literal_k = int(formula["policy"]["literal_run_length_model"]["k"])
    payload_alpha = int(formula["policy"]["literal_payload_model"]["alpha"])
    fixed_bits = (
        formula["mdl_estimate_rough"]["fixed_bits"]
        if "mdl_estimate_rough" in formula and "fixed_bits" in formula["mdl_estimate_rough"]
        else 0
    )

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
    errors = []

    for book in order:
        parts = []
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                text = op["text"]
                length = int(op["length"])
                if len(text) != length:
                    errors.append({"book": book, "type": "literal_length_mismatch", "op": op})
                literal_bits_no_payload += 1 + rice_bits(length + 1, literal_k)
                literal_payload.append(text)
                literal_runs += 1
                literal_digits += length
                chunk = text
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                length = int(op["length"])
                chunk = emitted_digits[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op": op})
                address_bits = math.log2(max(2, len(emitted_digits)))
                length_bits = rice_bits(length - min_len + 1, copy_k)
                copy_bits += 1 + address_bits + length_bits
                copy_address_bits += address_bits
                copy_length_code_bits += length_bits
                copy_items += 1
                copied_digits += length
            else:
                errors.append({"book": book, "type": "bad_op", "op": op})
                chunk = ""
            parts.append(chunk)
            emitted_digits += chunk
        if "".join(parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})

    payload_stream = "".join(literal_payload)
    payload_bits = adaptive_payload_bits(payload_stream, payload_alpha)
    total_bits = fixed_bits + literal_bits_no_payload + payload_bits + copy_bits
    return {
        "total_bits": total_bits,
        "fixed_bits": fixed_bits,
        "literal_bits_no_payload": literal_bits_no_payload,
        "literal_payload_bits": payload_bits,
        "copy_bits": copy_bits,
        "copy_address_bits": copy_address_bits,
        "copy_length_code_bits": copy_length_code_bits,
        "literal_runs": literal_runs,
        "literal_digits": literal_digits,
        "copy_items": copy_items,
        "copied_digits": copied_digits,
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
            if op["type"] == "literal":
                yield {
                    "book": book,
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "emitted_before_op": emitted_digits,
                    "text": op["text"],
                }
                emitted_digits += op["text"]
                book_pos += int(op["length"])
            elif op["type"] == "copy":
                chunk = emitted_digits[int(op["source_digit_pos"]) : int(op["source_digit_pos"]) + int(op["length"])]
                emitted_digits += chunk
                book_pos += int(op["length"])
            else:
                raise ValueError(op)


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
                candidate = apply_repair(formula, repair)
                score = score_formula(candidate, books)
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
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_digit_address_bits"]
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    best, candidates_tested = find_best_single_repair(formula, books, current_bits)
    promoted = best is not None and best["total_bits"] < current_bits
    classification = (
        "controlled_digit_address_literal_repair_improvement"
        if promoted
        else "digit_address_literal_repair_none_promoted"
    )

    followup_best = None
    followup_tested = 0
    if promoted:
        out = apply_repair(formula, best)
        score = score_formula(out, books)
        followup_best, followup_tested = find_best_single_repair(out, books, score["total_bits"])
        out["schema"] = "sequential_lz_digit_address_literal_repair_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["mdl_estimate_rough"] = {
            **formula["mdl_estimate_rough"],
            "sequential_lz_digit_address_literal_repair_bits": score["total_bits"],
            "previous_sequential_lz_digit_address_bits": current_bits,
            "gain_vs_previous_digit_address_bits": current_bits - score["total_bits"],
            "literal_bits": score["literal_bits_no_payload"] + score["literal_payload_bits"],
            "literal_bits_no_payload": score["literal_bits_no_payload"],
            "adaptive_literal_payload_bits": score["literal_payload_bits"],
            "copy_bits": score["copy_bits"],
            "copy_address_bits": score["copy_address_bits"],
            "copy_length_code_bits": score["copy_length_code_bits"],
            "literal_runs": score["literal_runs"],
            "literal_digits": score["literal_digits"],
            "copy_items": score["copy_items"],
            "copied_digits": score["copied_digits"],
        }
        out["validation"]["digit_address_literal_repair_roundtrip_audit"] = score["validation"]
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "digit_address_literal_repair_search.v1",
        "test": "37_digit_address_literal_repair_search",
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
        "boundary": formula["boundary"],
    }

    lines = [
        "# Digit-Address Literal Repair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests one-step literal-to-copy repairs after the formula",
        "moved to digit-only copy addresses. The current recipe is used as the",
        "baseline, and each candidate is rescored with adaptive literal payload",
        "coding and digit-only absolute copy-address cost.",
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
            "digit-address formula. A non-promoted best candidate remains useful",
            "as a local frontier audit, not as progress.",
            "",
            "## Boundary",
            "",
            "This is a mechanical recipe audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("37_digit_address_literal_repair_search", result, lines)


if __name__ == "__main__":
    main()
