from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair3_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair3_bits"


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


def main() -> None:
    frontier = load_frontier_module()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = frontier.score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    best, counts = frontier.find_best_repair(formula, books, current_bits)
    promoted = best is not None and best["delta_bits"] < -1e-9
    classification = (
        "controlled_post_minaddr_repair2_local_improvement"
        if promoted
        else "post_minaddr_repair2_local_frontier_closed"
    )

    if promoted:
        if best["edit_type"] == "literal_to_copy":
            out = frontier.apply_literal_to_copy(formula, best)
        else:
            out = frontier.apply_copy_to_literal(formula, best)
        score = best["score"]
        out.update(
            {
                "schema": "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair3_formula.v1",
                "classification": classification,
                "translation_delta": "NONE",
                "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
                "mdl_estimate_rough": {
                    **out["mdl_estimate_rough"],
                    OUT_TOTAL_KEY: score["total_bits"],
                    "previous_sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_bits": current_bits,
                    "gain_vs_previous_minaddr_repair2_bits": current_bits - score["total_bits"],
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
                "post_minaddr_repair2_local_repair": {
                    key: value for key, value in best.items() if key != "score"
                },
                "validation": {
                    **out["validation"],
                    "post_minaddr_repair2_local_roundtrip_audit": score["validation"],
                    "literal_payload_context_stats": score["literal_payload_context_stats"],
                    "item_type_context_stats": score["item_type_context_stats"],
                },
                "boundary": out["boundary"],
            }
        )
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_minaddr_repair2_local_frontier.v1",
        "test": "73_post_minaddr_repair2_local_frontier",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "candidate_counts": counts,
        "best_repair": best,
        "promotion_rule": (
            "promote only if one exact local edit after the second minaddr repair beats "
            "the active formula under full rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Minaddr-Repair2 Local Frontier",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests one-step literal-to-copy and copy-to-literal edits",
        "after the second minaddr local repair changed the recipe. It uses the",
        "same full rescoring contract as the prior local-frontier passes.",
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
            "The local frontier is closed for one-step edits under the current",
            "bounded-copy-length and min_len-bounded address cost model if the best",
            "candidate is at or above zero delta. This is a mechanical recipe audit",
            "only; it does not introduce plaintext.",
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
    write_result("73_post_minaddr_repair2_local_frontier", result, lines)


if __name__ == "__main__":
    main()
