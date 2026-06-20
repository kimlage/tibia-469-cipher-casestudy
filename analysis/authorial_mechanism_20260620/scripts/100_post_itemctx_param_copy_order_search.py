from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"
COPY_ORDER = HERE / "scripts/90_post_midpoint_alpha1_copy_order_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_bits"


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
    copy_order = load_module("post_midpoint_alpha1_copy_order_search", COPY_ORDER)
    frontier = copy_order.load_module("minaddr_frontier", FRONTIER)
    midpoint = copy_order.load_module("post_midpoint_frontier", MIDPOINT)
    context_module = copy_order.load_module("post_adaptive_copy_length_context", CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    copy_rows = copy_order.collect_copy_rows(formula, books)
    alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    source_length_bits, source_length_by_copy, context_counts = copy_order.midpoint_adaptive_length_bits(
        copy_rows,
        alpha,
        "source_first_length_symbol_count",
    )
    length_first_bits, length_first_by_copy, length_first_context_counts = copy_order.midpoint_adaptive_length_bits(
        copy_rows,
        alpha,
        "length_first_length_symbol_count",
    )
    if abs(source_length_bits - current_score["copy_length_code_bits"]) > 1e-6:
        raise RuntimeError((source_length_bits, current_score["copy_length_code_bits"]))

    source_address_bits = sum(math.log2(max(2, row["source_first_address_count"])) for row in copy_rows)
    length_first_address_bits = sum(math.log2(max(2, row["length_first_address_count"])) for row in copy_rows)
    active_copy_bits = source_address_bits + source_length_bits
    if abs(active_copy_bits - current_score["copy_bits"]) > 1e-6:
        raise RuntimeError((active_copy_bits, current_score["copy_bits"]))

    per_copy_rows = []
    savings = []
    for row, source_length, length_first_length in zip(copy_rows, source_length_by_copy, length_first_by_copy):
        source_first_bits = math.log2(max(2, row["source_first_address_count"])) + source_length
        length_first_copy_bits = math.log2(max(2, row["length_first_address_count"])) + length_first_length
        saving = source_first_bits - length_first_copy_bits
        savings.append(saving)
        per_copy_rows.append(
            {
                **row,
                "source_first_bits": source_first_bits,
                "length_first_bits": length_first_copy_bits,
                "length_first_delta_bits": length_first_copy_bits - source_first_bits,
            }
        )

    optimistic_savings = sum(saving for saving in savings if saving > 0)
    optimistic_switch_count = sum(1 for saving in savings if saving > 0)
    sparse = copy_order.optimize_sparse_length_first_runs(copy_rows, savings)
    fixed_noncopy_bits = current_score["total_bits"] - current_score["copy_bits"]

    models = [
        {
            "model": "source_first_then_midpoint_alpha1_length_active",
            "copy_bits": active_copy_bits,
            "decodable": True,
            "length_first_copy_count": 0,
        },
        {
            "model": "midpoint_alpha1_length_first_then_source",
            "copy_bits": length_first_address_bits + length_first_bits,
            "decodable": True,
            "length_first_copy_count": len(copy_rows),
        },
        {
            "model": "best_midpoint_alpha1_copy_order_optimistic_no_mode",
            "copy_bits": active_copy_bits - optimistic_savings,
            "decodable": False,
            "length_first_copy_count": optimistic_switch_count,
        },
        {
            "model": "midpoint_alpha1_copy_order_mode_per_copy",
            "copy_bits": active_copy_bits - optimistic_savings + len(copy_rows),
            "decodable": True,
            "length_first_copy_count": optimistic_switch_count,
        },
        {
            "model": "midpoint_alpha1_copy_order_sparse_run_list_length_first_required",
            "copy_bits": active_copy_bits + sparse["net_extra_bits"],
            "decodable": True,
            "length_first_copy_count": sparse["length_first_copy_count"],
            "details": sparse,
        },
    ]
    rows = []
    for row in models:
        total_bits = fixed_noncopy_bits + row["copy_bits"]
        rows.append({**row, "total_bits": total_bits, "delta_vs_current_bits": total_bits - current_bits})
    rows.sort(key=lambda row: row["total_bits"])

    best_decodable = next(row for row in rows if row["decodable"])
    best_any = rows[0]
    if (
        best_decodable["model"] != "source_first_then_midpoint_alpha1_length_active"
        and best_decodable["total_bits"] < current_bits - 1e-9
    ):
        classification = "post_itemctx_param_copy_order_candidate"
    elif best_any["total_bits"] < current_bits - 1e-9 and not best_any["decodable"]:
        classification = "post_itemctx_param_copy_order_optimistic_only_not_promoted"
    else:
        classification = "post_itemctx_param_copy_order_source_first_retained"

    best_savings = sorted(per_copy_rows, key=lambda row: row["length_first_delta_bits"])[:20]
    worst_costs = sorted(per_copy_rows, key=lambda row: row["length_first_delta_bits"], reverse=True)[:20]
    result = {
        "schema": "post_itemctx_param_copy_order_search.v1",
        "test": "100_post_itemctx_param_copy_order_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_items": len(copy_rows),
        "fixed_noncopy_bits": fixed_noncopy_bits,
        "source_first_context_counts": context_counts,
        "length_first_context_counts": length_first_context_counts,
        "models": rows,
        "copy_order_rows": per_copy_rows,
        "best_length_first_savings": best_savings,
        "worst_length_first_costs": worst_costs,
        "promotion_rule": (
            "promote only if a decodable copy coding order beats source-first address "
            "then midpoint alpha=1 adaptive length under full itemctx_param rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Copy Order Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests the within-copy coding order after the itemctx_param",
        "promotion. The recipe, payload model, item-type model, forced rules,",
        "book-length ledger, minaddr source-address contract, and fixed midpoint",
        "context are held constant.",
        "",
        "## Copy Order Models",
        "",
        "| Model | Copy bits | Total bits | Delta vs current | Decodable | Length-first copies |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model']}` | `{row['copy_bits']:.3f}` | `{row['total_bits']:.3f}` | "
            f"`{row['delta_vs_current_bits']:.3f}` | `{row['decodable']}` | "
            f"`{row['length_first_copy_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Length-First Shape",
            "",
            f"- Copy items: `{len(copy_rows)}`",
            f"- Pure length-first delta: `{length_first_address_bits + length_first_bits - active_copy_bits:.3f}` bits",
            f"- Optimistic no-mode savings: `{optimistic_savings:.3f}` bits across `{optimistic_switch_count}` copies",
            f"- Best sparse decodable net delta: `{sparse['net_extra_bits']:.3f}` bits",
            f"- Best sparse length-first copies: `{sparse['length_first_copy_count']}`",
            "",
            "## Best Length-First Savings",
            "",
            "| Rank | Book | Op | Length | Source-first bits | Length-first bits | Delta |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for rank, row in enumerate(best_savings[:10], start=1):
        lines.append(
            f"| `{rank}` | `{row['book']}` | `{row['op_index']}` | `{row['length']}` | "
            f"`{row['source_first_bits']:.3f}` | `{row['length_first_bits']:.3f}` | "
            f"`{row['length_first_delta_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Pure length-first coding is worse overall. Selecting the cheaper order per",
            "copy is cheaper only when source/length order mode bits are free, so that",
            "row is retained as an optimistic lower bound. The tested decodable mode",
            "ledgers do not beat the active source-first order.",
            "",
            "## Boundary",
            "",
            "This is a mechanical copy-cost audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("100_post_itemctx_param_copy_order_search", result, lines)


if __name__ == "__main__":
    main()
