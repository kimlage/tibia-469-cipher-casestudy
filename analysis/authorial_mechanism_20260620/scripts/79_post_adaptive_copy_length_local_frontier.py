from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair3_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair3_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_frontier_module():
    spec = importlib.util.spec_from_file_location("minaddr_frontier", FRONTIER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frontier module: {FRONTIER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def adaptive_copy_length_bits(formula: dict, scorer) -> tuple[float, list[dict], list[dict]]:
    min_len = int(formula["policy"]["min_len"])
    alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    counts: dict[int, int] = {}
    emitted = ""
    total_bits = 0.0
    errors = []
    rows = []
    copy_id = 0

    for book in map(str, formula["policy"]["book_order"]):
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        parts = []
        position = 0
        for op_index, op in enumerate(ops):
            length = int(op["length"])
            remaining = book_length - position
            if op["type"] == "literal":
                chunk = op["text"]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "literal_length_mismatch", "op_index": op_index})
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                max_length = min(remaining, len(emitted) - source_digit_pos)
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
                legal = range(symbol_count)
                legal_observations = sum(counts.get(index, 0) for index in legal)
                denominator = legal_observations + alpha * symbol_count
                numerator = counts.get(length_index, 0) + alpha
                bits = -math.log2(numerator / denominator)
                truncated_bits = scorer.truncated_binary_bits(symbol_count, length_index)
                total_bits += bits
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op_index": op_index})
                rows.append(
                    {
                        "copy_id": copy_id,
                        "book": book,
                        "op_index": op_index,
                        "source_digit_pos": source_digit_pos,
                        "length": length,
                        "max_length": max_length,
                        "symbol_count": symbol_count,
                        "length_index": length_index,
                        "adaptive_bits": bits,
                        "truncated_binary_bits": truncated_bits,
                        "previous_legal_observations": legal_observations,
                        "previous_same_length_observations": counts.get(length_index, 0),
                    }
                )
                counts[length_index] = counts.get(length_index, 0) + 1
                copy_id += 1
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op_index": op_index, "op": op})
            parts.append(chunk)
            emitted += chunk
            position += length
        if "".join(parts) != formula.get("book_digits", {}).get(book, ""):
            pass

    return total_bits, rows, errors


def score_formula(formula: dict, books: dict[str, str], frontier) -> dict:
    base = frontier.score_formula(formula, books)
    adaptive_bits, adaptive_rows, adaptive_errors = adaptive_copy_length_bits(formula, frontier)
    errors = list(base["validation"]["errors"]) + adaptive_errors
    current_copy_length = float(base["copy_length_code_bits"])
    copy_bits = float(base["copy_address_bits"]) + adaptive_bits
    total_bits = float(base["total_bits"]) - current_copy_length + adaptive_bits
    return {
        **base,
        "total_bits": total_bits,
        "copy_bits": copy_bits,
        "copy_length_code_bits": adaptive_bits,
        "adaptive_copy_length_rows": adaptive_rows,
        "truncated_copy_length_bits": current_copy_length,
        "validation": {
            **base["validation"],
            "books_roundtrip_ok": 0 if errors else base["validation"]["books_roundtrip_ok"],
            "errors": errors,
        },
    }


def find_best_repair(formula: dict, books: dict[str, str], current_bits: float, frontier) -> tuple[dict | None, dict]:
    min_len = int(formula["policy"]["min_len"])
    best = None
    counts = {"literal_to_copy_tested": 0, "copy_to_literal_tested": 0, "invalid_candidates": 0}
    for context in frontier.iter_contexts(formula):
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
                    score = score_formula(frontier.apply_literal_to_copy(formula, repair), books, frontier)
                    counts["literal_to_copy_tested"] += 1
                    if score["validation"]["errors"]:
                        counts["invalid_candidates"] += 1
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
            score = score_formula(frontier.apply_copy_to_literal(formula, repair), books, frontier)
            counts["copy_to_literal_tested"] += 1
            if score["validation"]["errors"]:
                counts["invalid_candidates"] += 1
                continue
            delta = score["total_bits"] - current_bits
            if best is None or delta < best["delta_bits"]:
                best = {**repair, "delta_bits": delta, "score": score}
    return best, counts


def strip_score(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {key: value for key, value in row.items() if key != "score"}


def main() -> None:
    frontier = load_frontier_module()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = score_formula(formula, books, frontier)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    best, counts = find_best_repair(formula, books, current_bits, frontier)
    promoted = best is not None and best["delta_bits"] < -1e-9
    classification = (
        "controlled_post_adaptive_copy_length_local_repair_improvement"
        if promoted
        else "post_adaptive_copy_length_local_frontier_closed"
    )

    if promoted:
        out = (
            frontier.apply_literal_to_copy(formula, best)
            if best["edit_type"] == "literal_to_copy"
            else frontier.apply_copy_to_literal(formula, best)
        )
        score = best["score"]
        out.update(
            {
                "schema": "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair3_formula.v1",
                "classification": classification,
                "translation_delta": "NONE",
                "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
                "mdl_estimate_rough": {
                    **out["mdl_estimate_rough"],
                    OUT_TOTAL_KEY: score["total_bits"],
                    "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_bits": current_bits,
                    "gain_vs_previous_adaptive_repair2_bits": current_bits - score["total_bits"],
                    "literal_bits_no_payload": score["literal_bits_no_payload"],
                    "adaptive_context_order_literal_payload_bits": score["literal_payload_bits"],
                    "copy_bits": score["copy_bits"],
                    "copy_address_bits": score["copy_address_bits"],
                    "copy_length_code_bits": score["copy_length_code_bits"],
                    "bounded_adaptive_copy_length_bits": score["copy_length_code_bits"],
                    "item_type_context_order_stream_bits": score["item_type_stream_bits"],
                    "literal_runs": score["literal_runs"],
                    "literal_digits": score["literal_digits"],
                    "copy_items": score["copy_items"],
                    "copied_digits": score["copied_digits"],
                    "forced_literal_length_count": score["forced_literal_length_count"],
                    "forced_literal_length_saved_bits": score["forced_literal_length_saved_bits"],
                },
                "post_adaptive_copy_length_local_repair": strip_score(best),
                "validation": {
                    **out["validation"],
                    "post_adaptive_copy_length_local_repair_roundtrip_audit": score["validation"],
                    "literal_payload_context_stats": score["literal_payload_context_stats"],
                    "item_type_context_stats": score["item_type_context_stats"],
                },
            }
        )
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_adaptive_copy_length_local_frontier.v1",
        "test": "79_post_adaptive_copy_length_local_frontier",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "candidate_counts": counts,
        "best_repair": strip_score(best),
        "best_repair_score": best["score"] if best else None,
        "promotion_rule": (
            "promote only if one exact literal-to-copy or copy-to-literal local edit "
            "beats the active adaptive copy-length formula under full rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Adaptive-Copy-Length Local Frontier",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests the immediate one-edit local recipe frontier after",
        "adaptive bounded copy-length coding became the active formula. It scores",
        "single literal-to-copy and copy-to-literal edits under the same payload,",
        "item-type, forced-rule, minaddr, and adaptive copy-length contracts.",
        "",
        "## Result",
        "",
        f"- Current formula bits: `{current_bits:.3f}`",
        f"- Literal-to-copy candidates tested: `{counts['literal_to_copy_tested']}`",
        f"- Copy-to-literal candidates tested: `{counts['copy_to_literal_tested']}`",
        f"- Invalid candidates: `{counts['invalid_candidates']}`",
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
                f"- Best repair total bits: `{best['score']['total_bits']:.3f}`",
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
            "mechanical recipe audit only; it does not introduce plaintext, row0",
            "meaning, or authorial intent.",
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
    write_result("79_post_adaptive_copy_length_local_frontier", result, lines)


if __name__ == "__main__":
    main()
