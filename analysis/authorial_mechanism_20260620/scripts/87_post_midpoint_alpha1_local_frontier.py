from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair3_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair3_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def score_formula(formula: dict, books: dict[str, str], frontier, midpoint, context_module) -> dict:
    return midpoint.score_formula(formula, books, frontier, context_module)


def find_best_repair(formula: dict, books: dict[str, str], current_bits: float, frontier, midpoint, context_module) -> tuple[dict | None, dict]:
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
                    score = score_formula(
                        frontier.apply_literal_to_copy(formula, repair),
                        books,
                        frontier,
                        midpoint,
                        context_module,
                    )
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
            score = score_formula(
                frontier.apply_copy_to_literal(formula, repair),
                books,
                frontier,
                midpoint,
                context_module,
            )
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
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("post_adaptive_copy_length_context", CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = score_formula(formula, books, frontier, midpoint, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    best, counts = find_best_repair(formula, books, current_bits, frontier, midpoint, context_module)
    promoted = best is not None and best["delta_bits"] < -1e-9
    classification = (
        "controlled_post_midpoint_alpha1_local_repair_improvement"
        if promoted
        else "post_midpoint_alpha1_local_frontier_closed"
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
                "schema": "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair3_formula.v1",
                "classification": classification,
                "translation_delta": "NONE",
                "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
                "mdl_estimate_rough": {
                    **out["mdl_estimate_rough"],
                    OUT_TOTAL_KEY: score["total_bits"],
                    "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_bits": current_bits,
                    "gain_vs_previous_midpoint_alpha1_bits": current_bits - score["total_bits"],
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
                "post_midpoint_alpha1_local_repair": strip_score(best),
                "validation": {
                    **out["validation"],
                    "post_midpoint_alpha1_local_repair_roundtrip_audit": score["validation"],
                    "literal_payload_context_stats": score["literal_payload_context_stats"],
                    "item_type_context_stats": score["item_type_context_stats"],
                    "midpoint_copy_length_context_counts": score["midpoint_copy_length_context_counts"],
                },
            }
        )
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_midpoint_alpha1_local_frontier.v1",
        "test": "87_post_midpoint_alpha1_local_frontier",
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
            "beats the active midpoint alpha=1 formula under full rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Midpoint Alpha1 Local Frontier",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests the immediate one-edit local recipe frontier after",
        "the midpoint copy-length alpha was changed from `2` to `1`. It scores",
        "single literal-to-copy and copy-to-literal edits under the same payload,",
        "item-type, forced-rule, minaddr, midpoint context, and alpha=1",
        "copy-length contracts.",
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
    write_result("87_post_midpoint_alpha1_local_frontier", result, lines)


if __name__ == "__main__":
    main()
