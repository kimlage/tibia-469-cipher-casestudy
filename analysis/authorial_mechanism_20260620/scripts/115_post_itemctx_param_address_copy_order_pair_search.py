from __future__ import annotations

import heapq
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
ADDRESS_SEARCH = HERE / "scripts/89_post_midpoint_alpha1_address_model_search.py"
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


def address_candidate_rows(formula: dict, books: dict[str, str], current_score: dict, current_bits: float) -> list[dict]:
    address = load_module("post_midpoint_alpha1_address_model_search", ADDRESS_SEARCH)
    _spans, literal_rows, copy_rows = address.build_rows(formula, books, current_score)
    active_copy_bits = address.current_copy_bits(copy_rows)
    if abs(active_copy_bits - current_score["copy_bits"]) > 1e-6:
        raise RuntimeError((active_copy_bits, current_score["copy_bits"]))
    fixed_noncopy_bits = current_score["total_bits"] - current_score["copy_bits"]
    standard = address.standard_address_models(copy_rows)
    seed_models, seed_stats = address.literal_seed_models(copy_rows, literal_rows, active_copy_bits)

    rows = []
    for row in [*standard, *seed_models]:
        total_bits = fixed_noncopy_bits + row["copy_bits"]
        changed = row["model"] != "absolute_digit_source_pos_min_len_bounded"
        rows.append(
            {
                "model": row["model"],
                "copy_bits": row["copy_bits"],
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "decodable": bool(row["decodable"]),
                "changed": changed,
                "seed_copy_count": row.get("seed_copy_count", 0),
            }
        )
    rows.sort(key=lambda row: row["delta_vs_current_bits"])
    return rows, seed_stats


def copy_order_candidate_rows(formula: dict, books: dict[str, str], current_score: dict, current_bits: float) -> list[dict]:
    copy_order = load_module("post_midpoint_alpha1_copy_order_search", COPY_ORDER)
    copy_rows = copy_order.collect_copy_rows(formula, books)
    alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    source_length_bits, source_length_by_copy, _context_counts = copy_order.midpoint_adaptive_length_bits(
        copy_rows,
        alpha,
        "source_first_length_symbol_count",
    )
    length_first_bits, length_first_by_copy, _length_first_context_counts = copy_order.midpoint_adaptive_length_bits(
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

    savings = []
    for row, source_length, length_first_length in zip(copy_rows, source_length_by_copy, length_first_by_copy):
        source_first_bits = math.log2(max(2, row["source_first_address_count"])) + source_length
        length_first_copy_bits = math.log2(max(2, row["length_first_address_count"])) + length_first_length
        savings.append(source_first_bits - length_first_copy_bits)

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
        },
    ]
    rows = []
    for row in models:
        total_bits = fixed_noncopy_bits + row["copy_bits"]
        changed = row["model"] != "source_first_then_midpoint_alpha1_length_active"
        rows.append(
            {
                **row,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "changed": changed,
            }
        )
    rows.sort(key=lambda row: row["delta_vs_current_bits"])
    return rows


def pair_row(current_bits: float, address_row: dict, order_row: dict) -> dict:
    delta = address_row["delta_vs_current_bits"] + order_row["delta_vs_current_bits"]
    decodable = bool(address_row["decodable"] and order_row["decodable"])
    return {
        "address_model": address_row["model"],
        "address_delta_bits": address_row["delta_vs_current_bits"],
        "address_decodable": address_row["decodable"],
        "address_changed": address_row["changed"],
        "copy_order_model": order_row["model"],
        "copy_order_delta_bits": order_row["delta_vs_current_bits"],
        "copy_order_decodable": order_row["decodable"],
        "copy_order_changed": order_row["changed"],
        "decodable": decodable,
        "changed": address_row["changed"] or order_row["changed"],
        "total_bits": current_bits + delta,
        "delta_vs_current_bits": delta,
    }


def top_pairs(current_bits: float, address_rows: list[dict], order_rows: list[dict], limit: int) -> list[dict]:
    heap: list[tuple[float, int, int]] = []
    seen = {(0, 0)}
    heapq.heappush(
        heap,
        (address_rows[0]["delta_vs_current_bits"] + order_rows[0]["delta_vs_current_bits"], 0, 0),
    )
    out = []
    while heap and len(out) < limit:
        _delta, address_idx, order_idx = heapq.heappop(heap)
        out.append(pair_row(current_bits, address_rows[address_idx], order_rows[order_idx]))
        for next_idx in ((address_idx + 1, order_idx), (address_idx, order_idx + 1)):
            a_i, o_i = next_idx
            if a_i >= len(address_rows) or o_i >= len(order_rows):
                continue
            if next_idx in seen:
                continue
            seen.add(next_idx)
            heapq.heappush(
                heap,
                (address_rows[a_i]["delta_vs_current_bits"] + order_rows[o_i]["delta_vs_current_bits"], a_i, o_i),
            )
    return out


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("copy_length_context", CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    address_rows, seed_stats = address_candidate_rows(formula, books, current_score, current_bits)
    order_rows = copy_order_candidate_rows(formula, books, current_score, current_bits)
    pair_count = len(address_rows) * len(order_rows)
    top = top_pairs(current_bits, address_rows, order_rows, 100)
    best_any = top[0]
    best_decodable = next(row for row in top if row["decodable"])
    active_address = next(row for row in address_rows if not row["changed"])
    active_order = next(row for row in order_rows if not row["changed"])
    best_changed_decodable = next(row for row in top if row["decodable"] and row["changed"])
    best_both_changed_decodable = min(
        (
            pair_row(current_bits, address, order)
            for address in address_rows
            for order in order_rows
            if address["changed"] and order["changed"] and address["decodable"] and order["decodable"]
        ),
        key=lambda row: row["total_bits"],
    )
    best_changed = min(
        [
            pair_row(current_bits, next(row for row in address_rows if row["changed"]), active_order),
            pair_row(current_bits, active_address, next(row for row in order_rows if row["changed"])),
        ],
        key=lambda row: row["total_bits"],
    )
    promoted = (
        best_decodable["changed"]
        and best_decodable["total_bits"] < current_bits - 1e-9
    )
    if promoted:
        classification = "controlled_post_itemctx_param_address_copy_order_pair_improvement"
    elif best_any["total_bits"] < current_bits - 1e-9 and not best_any["decodable"]:
        classification = "post_itemctx_param_address_copy_order_pair_optimistic_only_not_promoted"
    else:
        classification = "post_itemctx_param_address_copy_order_pair_not_promoted"

    result = {
        "schema": "post_itemctx_param_address_copy_order_pair_search.v1",
        "test": "115_post_itemctx_param_address_copy_order_pair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "address_candidates_tested": len(address_rows),
        "copy_order_candidates_tested": len(order_rows),
        "pair_candidates_proven_by_component_minima": pair_count,
        "best_pair_any": best_any,
        "best_pair_decodable": best_decodable,
        "best_changed_pair": best_changed,
        "best_changed_pair_decodable": best_changed_decodable,
        "best_both_changed_pair_decodable": best_both_changed_decodable,
        "top_pairs": top,
        "address_models": address_rows,
        "copy_order_models": order_rows,
        "seed_stats": seed_stats,
        "promotion_rule": (
            "promote only if a decodable address-model and copy-order pair beats "
            "the active min_len-bounded absolute source address plus source-first "
            "copy order ledger after charged mode/declaration bits while preserving "
            "70/70 roundtrip and translation_delta NONE; nondecodable no-mode rows "
            "are lower bounds only"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Address/Copy-Order Pair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit combines the post-itemctx_param address-model frontier with",
        "the copy-order frontier. A pair can promote only if both sides are",
        "decodable. Rows that rely on literal-seed source-mode bits or per-copy",
        "copy-order mode bits being free remain optimistic lower bounds.",
        "",
        "## Coverage",
        "",
        f"- Address candidates: `{len(address_rows)}`",
        f"- Copy-order candidates: `{len(order_rows)}`",
        f"- Pair candidates proven by component minima: `{pair_count}`",
        "",
        "## Top Pairs",
        "",
        "| Rank | Address model | Order model | Decodable | Total bits | Delta |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for rank, row in enumerate(top[:20], start=1):
        lines.append(
            f"| `{rank}` | `{row['address_model']}` | `{row['copy_order_model']}` | "
            f"`{row['decodable']}` | `{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Decodable Pair",
            "",
            f"- Delta vs current: `{best_decodable['delta_vs_current_bits']:.3f}` bits",
            f"- Address: `{best_decodable['address_model']}`",
            f"- Copy order: `{best_decodable['copy_order_model']}`",
            "",
            "## Best Changed Decodable Pair",
            "",
            f"- Delta vs current: `{best_changed_decodable['delta_vs_current_bits']:.3f}` bits",
            f"- Address: `{best_changed_decodable['address_model']}`",
            f"- Copy order: `{best_changed_decodable['copy_order_model']}`",
            "",
            "## Best Decodable Pair With Both Components Changed",
            "",
            f"- Delta vs current: `{best_both_changed_decodable['delta_vs_current_bits']:.3f}` bits",
            f"- Address: `{best_both_changed_decodable['address_model']}`",
            f"- Copy order: `{best_both_changed_decodable['copy_order_model']}`",
            "",
            "## Interpretation",
            "",
            "The best overall pair is an optimistic lower bound because it combines",
            "no-mode address and no-mode copy-order rows. The best decodable pair is",
            "the active ledger, and every changed decodable pair is worse after mode",
            "and declaration costs.",
            "",
            "## Boundary",
            "",
            "This is a mechanical copy-cost audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("115_post_itemctx_param_address_copy_order_pair_search", result, lines)


if __name__ == "__main__":
    main()
