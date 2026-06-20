from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_pair_repair_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"
PAIR_FRONTIER = HERE / "scripts/88_post_midpoint_alpha1_pair_frontier.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_pair_repair_bits"


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
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    pair_frontier = load_module("post_midpoint_alpha1_pair_frontier", PAIR_FRONTIER)
    frontier = pair_frontier.load_module("minaddr_frontier", FRONTIER)
    midpoint = pair_frontier.load_module("post_midpoint_frontier", MIDPOINT)
    context_module = pair_frontier.load_module("post_adaptive_copy_length_context", CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = pair_frontier.score_formula(formula, books, frontier, midpoint, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    candidates, single_counts = pair_frontier.collect_single_candidates(
        formula,
        books,
        current_bits,
        frontier,
        midpoint,
        context_module,
    )
    best_single = min(candidates, key=lambda row: row["single_delta_bits"]) if candidates else None
    best_pair = None
    pair_counts = {
        "total_pairs_considered": 0,
        "compatible_pairs": 0,
        "overlapping_pairs_skipped": 0,
        "invalid_pairs": 0,
        "valid_pairs": 0,
    }

    import itertools

    for left, right in itertools.combinations(candidates, 2):
        pair_counts["total_pairs_considered"] += 1
        if not pair_frontier.repairs_compatible(left, right):
            pair_counts["overlapping_pairs_skipped"] += 1
            continue
        pair_counts["compatible_pairs"] += 1
        score = pair_frontier.score_formula(
            pair_frontier.apply_repair_pair(formula, (left, right)),
            books,
            frontier,
            midpoint,
            context_module,
        )
        if score["validation"]["errors"]:
            pair_counts["invalid_pairs"] += 1
            continue
        pair_counts["valid_pairs"] += 1
        row = {
            "total_bits": score["total_bits"],
            "delta_bits": score["total_bits"] - current_bits,
            "repairs": [left, right],
            "score": score,
        }
        if best_pair is None or row["total_bits"] < best_pair["total_bits"]:
            best_pair = row

    promoted = best_pair is not None and best_pair["delta_bits"] < -1e-9
    classification = (
        "controlled_post_itemctx_param_pair_repair_improvement"
        if promoted
        else "post_itemctx_param_pair_frontier_closed"
    )

    if promoted:
        out = pair_frontier.apply_repair_pair(formula, tuple(best_pair["repairs"]))
        score = best_pair["score"]
        out.update(
            {
                "schema": "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_pair_repair_formula.v1",
                "classification": classification,
                "translation_delta": "NONE",
                "source_baseline_formula": str(FORMULA.relative_to(ROOT)),
                "mdl_estimate_rough": {
                    **out["mdl_estimate_rough"],
                    OUT_TOTAL_KEY: score["total_bits"],
                    "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_bits": current_bits,
                    "gain_vs_previous_itemctx_param_bits": current_bits - score["total_bits"],
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
                "post_itemctx_param_pair_repair": {
                    "repairs": best_pair["repairs"],
                    "delta_bits": best_pair["delta_bits"],
                    "total_bits": best_pair["total_bits"],
                },
                "validation": {
                    **out["validation"],
                    "post_itemctx_param_pair_repair_roundtrip_audit": score["validation"],
                    "literal_payload_context_stats": score["literal_payload_context_stats"],
                    "item_type_context_stats": score["item_type_context_stats"],
                    "midpoint_copy_length_context_counts": score["midpoint_copy_length_context_counts"],
                },
            }
        )
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_itemctx_param_pair_frontier.v1",
        "test": "98_post_itemctx_param_pair_frontier",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "single_counts": single_counts,
        "valid_single_candidates": len(candidates),
        "best_single_repair": best_single,
        "pair_counts": pair_counts,
        "best_pair_repair": pair_frontier.strip_score(best_pair),
        "best_pair_score": best_pair["score"] if best_pair else None,
        "promotion_rule": (
            "promote only if two compatible local edits beat the active "
            "itemctx_param formula under full rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Pair Frontier",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether two compatible local recipe edits improve",
        "together after the post-itemctx_param one-step frontier closed. It uses",
        "the active item-type split context with order `1` / `alpha=2`, midpoint",
        "copy-length context, alpha=1 copy-length ledger, payload model, forced",
        "rules, book-length ledger, and minaddr absolute source addresses.",
        "",
        "## Result",
        "",
        f"- Current formula bits: `{current_bits:.3f}`",
        f"- Valid single candidates: `{len(candidates)}`",
        f"- Literal-to-copy candidates tested: `{single_counts['literal_to_copy_tested']}`",
        f"- Copy-to-literal candidates tested: `{single_counts['copy_to_literal_tested']}`",
        f"- Invalid singles: `{single_counts['invalid_singles']}`",
        f"- Compatible pairs: `{pair_counts['compatible_pairs']}`",
        f"- Valid pairs: `{pair_counts['valid_pairs']}`",
        f"- Invalid pairs: `{pair_counts['invalid_pairs']}`",
    ]
    if best_single:
        lines.extend(
            [
                "",
                "## Best Single",
                "",
                f"- Type: `{best_single['edit_type']}`",
                f"- Delta: `{best_single['single_delta_bits']:.3f}` bits",
                f"- Book/op/text: `{best_single['book']}` / `{best_single['op_index']}` / `{best_single['text']}`",
            ]
        )
    if best_pair:
        lines.extend(
            [
                "",
                "## Best Pair",
                "",
                f"- Delta: `{best_pair['delta_bits']:.3f}` bits",
                f"- Total bits: `{best_pair['total_bits']:.3f}`",
            ]
        )
        for index, repair in enumerate(best_pair["repairs"], start=1):
            lines.append(
                f"- Repair {index}: `{repair['edit_type']}` book `{repair['book']}`, "
                f"op `{repair['op_index']}`, text `{repair['text']}`, length `{repair['length']}`"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Compatible pairs are promoted only when exact rescoring remains cheaper",
            "and 70/70 roundtrip plus forced-rule validation still pass. This is a",
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
    write_result("98_post_itemctx_param_pair_frontier", result, lines)


if __name__ == "__main__":
    main()
