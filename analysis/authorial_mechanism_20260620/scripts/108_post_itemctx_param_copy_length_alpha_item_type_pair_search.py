from __future__ import annotations

import copy
import heapq
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"
ALPHA_GRID = HERE / "scripts/92_post_midpoint_alpha1_context_alpha_grid.py"
PAIR_PAYLOAD_ITEM = HERE / "scripts/105_post_itemctx_param_payload_item_type_pair_context_search.py"
ITEM_CONTEXT_SEARCH = HERE / "scripts/104_post_itemctx_param_item_type_context_family_search.py"

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
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def alpha_candidate_rows(formula: dict, books: dict[str, str], current_score: dict, current_bits: float) -> list[dict]:
    alpha_grid = load_module("copy_length_alpha_grid", ALPHA_GRID)
    context_search = load_module("post_adaptive_copy_length_context", CONTEXT)

    copy_rows = context_search.collect_copy_rows(formula, books)
    current_alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    current_declaration_bits = int(formula["policy"]["copy_length_model"]["model_declaration_bits"])
    copy_base_declaration_bits = int(
        formula["policy"]["copy_length_model"]["replaces"]["replaces"]["model_declaration_bits"]
    )
    current_length_bits = float(current_score["copy_length_code_bits"])
    fixed_nonlength_bits = current_bits - current_length_bits

    active_alpha_by_context = {"first_half": current_alpha, "second_half": current_alpha}
    active_bits, _audit_rows, context_counts = alpha_grid.midpoint_length_bits_with_alpha_by_context(
        copy_rows,
        active_alpha_by_context,
    )
    if abs(active_bits - current_length_bits) > 1e-6:
        raise RuntimeError((active_bits, current_length_bits))
    expected_current_declaration = alpha_grid.shared_alpha_declaration_bits(
        copy_base_declaration_bits,
        current_alpha,
        len(active_alpha_by_context),
    )
    if expected_current_declaration != current_declaration_bits:
        raise RuntimeError((expected_current_declaration, current_declaration_bits))

    rows = [
        {
            "model": "active_shared_alpha1_midpoint_context",
            "family": "shared_alpha",
            "alpha_by_context": active_alpha_by_context,
            "adaptive_copy_length_bits": active_bits,
            "copy_model_declaration_bits": current_declaration_bits,
            "context_counts": context_counts,
            "total_bits": current_bits,
            "delta_vs_current_bits": 0.0,
            "component_delta_bits": 0.0,
            "declaration_delta_bits": 0,
            "changed": False,
        }
    ]

    for first_alpha in range(1, 65):
        for second_alpha in range(1, 65):
            alpha_by_context = {"first_half": first_alpha, "second_half": second_alpha}
            length_bits, _audit_rows, counts = alpha_grid.midpoint_length_bits_with_alpha_by_context(
                copy_rows,
                alpha_by_context,
            )
            declaration_bits = alpha_grid.alpha_by_context_declaration_bits(
                copy_base_declaration_bits,
                alpha_by_context,
            )
            total_bits = fixed_nonlength_bits + length_bits + declaration_bits - current_declaration_bits
            rows.append(
                {
                    "model": "midpoint_alpha_by_context_grid",
                    "family": "alpha_by_context",
                    "alpha_by_context": alpha_by_context,
                    "adaptive_copy_length_bits": length_bits,
                    "copy_model_declaration_bits": declaration_bits,
                    "context_counts": counts,
                    "total_bits": total_bits,
                    "delta_vs_current_bits": total_bits - current_bits,
                    "component_delta_bits": length_bits - current_length_bits,
                    "declaration_delta_bits": declaration_bits - current_declaration_bits,
                    "changed": True,
                }
            )

    rows.sort(key=lambda row: row["delta_vs_current_bits"])
    return rows


def compact_item_type(row: dict) -> dict:
    return {
        "family": row["family"],
        "split_book": row["split_book"],
        "order": row["order"],
        "alpha": row["alpha"],
        "delta_vs_current_bits": row["delta_vs_current_bits"],
        "component_delta_bits": row["component_delta_bits"],
        "declaration_delta_bits": row["declaration_delta_bits"],
        "changed": row["changed"],
        "extra_context_counts": row["extra_context_counts"],
        "model_declaration_bits": row["model_declaration_bits"],
    }


def pair_row(current_bits: float, alpha_row: dict, item_row: dict) -> dict:
    delta = alpha_row["delta_vs_current_bits"] + item_row["delta_vs_current_bits"]
    return {
        "copy_alpha_family": alpha_row["family"],
        "copy_alpha_model": alpha_row["model"],
        "copy_alpha_by_context": alpha_row["alpha_by_context"],
        "copy_alpha_delta_bits": alpha_row["delta_vs_current_bits"],
        "copy_alpha_changed": alpha_row["changed"],
        "item_type_family": item_row["family"],
        "item_type_split_book": item_row["split_book"],
        "item_type_order": item_row["order"],
        "item_type_alpha": item_row["alpha"],
        "item_type_delta_bits": item_row["delta_vs_current_bits"],
        "item_type_changed": item_row["changed"],
        "total_bits": current_bits + delta,
        "delta_vs_current_bits": delta,
    }


def top_pairs(current_bits: float, alpha_rows: list[dict], item_rows: list[dict], limit: int) -> list[dict]:
    heap: list[tuple[float, int, int]] = []
    seen = {(0, 0)}
    heapq.heappush(
        heap,
        (alpha_rows[0]["delta_vs_current_bits"] + item_rows[0]["delta_vs_current_bits"], 0, 0),
    )
    out = []
    while heap and len(out) < limit:
        _delta, alpha_idx, item_idx = heapq.heappop(heap)
        out.append(pair_row(current_bits, alpha_rows[alpha_idx], item_rows[item_idx]))
        for next_idx in ((alpha_idx + 1, item_idx), (alpha_idx, item_idx + 1)):
            a_i, i_i = next_idx
            if a_i >= len(alpha_rows) or i_i >= len(item_rows):
                continue
            if next_idx in seen:
                continue
            seen.add(next_idx)
            heapq.heappush(
                heap,
                (alpha_rows[a_i]["delta_vs_current_bits"] + item_rows[i_i]["delta_vs_current_bits"], a_i, i_i),
            )
    return out


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("copy_length_context", CONTEXT)
    pair_payload_item = load_module("pair_payload_item", PAIR_PAYLOAD_ITEM)
    itemctx = load_module("item_type_context_family_search_verify", ITEM_CONTEXT_SEARCH)

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    alpha_rows = alpha_candidate_rows(formula, books, current_score, current_bits)
    item_rows = [
        compact_item_type(row)
        for row in pair_payload_item.item_type_candidate_rows(formula, books, current_score, current_bits)
    ]
    item_rows.sort(key=lambda row: row["delta_vs_current_bits"])

    if alpha_rows[0]["delta_vs_current_bits"] < -1e-9:
        raise RuntimeError(("alpha", alpha_rows[0]))
    if item_rows[0]["delta_vs_current_bits"] < -1e-9:
        raise RuntimeError(("item_type", item_rows[0]))

    pair_count = len(alpha_rows) * len(item_rows)
    top = top_pairs(current_bits, alpha_rows, item_rows, 100)
    best = top[0]
    active_alpha = next(row for row in alpha_rows if not row["changed"])
    active_item = next(row for row in item_rows if not row["changed"])
    best_alpha_changed = next(row for row in alpha_rows if row["changed"])
    best_item_changed = next(row for row in item_rows if row["changed"])
    best_changed = min(
        [
            pair_row(current_bits, best_alpha_changed, active_item),
            pair_row(current_bits, active_alpha, best_item_changed),
        ],
        key=lambda row: row["total_bits"],
    )
    best_both_changed = pair_row(current_bits, best_alpha_changed, best_item_changed)
    promoted = best["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_post_itemctx_param_copy_length_alpha_item_type_pair_improvement"
        if promoted
        else "post_itemctx_param_copy_length_alpha_item_type_pair_not_promoted"
    )

    current_item_decl = int(formula["policy"]["item_type_model"]["model_declaration_bits"])
    current_fixed_bits = float(formula["mdl_estimate_rough"]["fixed_bits"])
    verification = []
    for row in top[:20]:
        item_match = next(
            item
            for item in item_rows
            if item["family"] == row["item_type_family"]
            and item["split_book"] == row["item_type_split_book"]
            and item["order"] == row["item_type_order"]
            and item["alpha"] == row["item_type_alpha"]
        )
        candidate = copy.deepcopy(formula)
        candidate_model = itemctx.set_extra_context(
            candidate["policy"]["item_type_model"],
            item_match["family"],
            item_match["split_book"],
            item_match["extra_context_counts"],
        )
        candidate_model["order"] = int(item_match["order"])
        candidate_model["alpha"] = int(item_match["alpha"])
        candidate_model["model_declaration_bits"] = int(item_match["model_declaration_bits"])
        candidate["policy"]["item_type_model"] = candidate_model
        candidate["mdl_estimate_rough"]["fixed_bits"] = (
            current_fixed_bits - current_item_decl + int(item_match["model_declaration_bits"])
        )
        score = midpoint.score_formula(candidate, books, frontier, context_module)
        if score["validation"]["errors"]:
            raise RuntimeError(score["validation"])
        expected_item_total = current_bits + item_match["delta_vs_current_bits"]
        if abs(score["total_bits"] - expected_item_total) > 1e-6:
            raise RuntimeError((score["total_bits"], expected_item_total))
        recomposed_total = score["total_bits"] + row["copy_alpha_delta_bits"]
        if abs(recomposed_total - row["total_bits"]) > 1e-6:
            raise RuntimeError((recomposed_total, row["total_bits"]))
        verification.append(
            {
                "pair_delta_bits": row["delta_vs_current_bits"],
                "item_type_rescored_total_bits": score["total_bits"],
                "copy_alpha_delta_bits": row["copy_alpha_delta_bits"],
                "recomposed_total_bits": recomposed_total,
                "validation_errors": score["validation"]["errors"],
            }
        )

    result = {
        "schema": "post_itemctx_param_copy_length_alpha_item_type_pair_search.v1",
        "test": "108_post_itemctx_param_copy_length_alpha_item_type_pair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_alpha_candidates_tested": len(alpha_rows),
        "item_type_candidates_tested": len(item_rows),
        "pair_candidates_proven_by_component_minima": pair_count,
        "best_pair": best,
        "best_changed_pair": best_changed,
        "best_both_changed_pair": best_both_changed,
        "top_pairs": top,
        "top_copy_alpha_models": alpha_rows[:20],
        "top_item_type_models": item_rows[:20],
        "authoritative_item_rescore_checks": verification,
        "promotion_rule": (
            "promote only if a decodable copy-length alpha-by-context row plus "
            "item-type context family/order/alpha pair beats the active shared "
            "copy-length alpha=1 and item-type split model after charged "
            "declaration bits while preserving 70/70 roundtrip and "
            "translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Copy-Length Alpha/Item-Type Pair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit combines the post-itemctx_param midpoint copy-length",
        "alpha-by-context grid with the post-itemctx_param item-type context-family",
        "frontier. The two costs are independent MDL components here, so the full",
        "pair space is proven by component minima and the top pairs are generated",
        "with a sorted heap. The top pairs are then checked by authoritative",
        "item-type rescoring plus copy-length alpha delta.",
        "",
        "## Coverage",
        "",
        f"- Copy-length alpha candidates: `{len(alpha_rows)}`",
        f"- Item-type candidates: `{len(item_rows)}`",
        f"- Pair candidates proven by component minima: `{pair_count}`",
        "",
        "## Top Pairs",
        "",
        "| Rank | Copy alpha by context | Item family | Item split | Order | Alpha | Total bits | Delta |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top[:20], start=1):
        item_split = "" if row["item_type_split_book"] is None else str(row["item_type_split_book"])
        lines.append(
            f"| `{rank}` | `{row['copy_alpha_by_context']}` | `{row['item_type_family']}` | "
            f"`{item_split}` | `{row['item_type_order']}` | `{row['item_type_alpha']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Changed Pair",
            "",
            f"- Delta vs current: `{best_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Copy alpha: `{best_changed['copy_alpha_by_context']}`",
            f"- Item-type: `{best_changed['item_type_family']}`"
            + (
                ""
                if best_changed["item_type_split_book"] is None
                else f" split `{best_changed['item_type_split_book']}`"
            )
            + f", order `{best_changed['item_type_order']}`, alpha `{best_changed['item_type_alpha']}`",
            "",
            "## Best Pair With Both Components Changed",
            "",
            f"- Delta vs current: `{best_both_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Copy alpha: `{best_both_changed['copy_alpha_by_context']}`",
            f"- Item-type: `{best_both_changed['item_type_family']}`"
            + (
                ""
                if best_both_changed["item_type_split_book"] is None
                else f" split `{best_both_changed['item_type_split_book']}`"
            )
            + f", order `{best_both_changed['item_type_order']}`, alpha `{best_both_changed['item_type_alpha']}`",
            "",
            "## Interpretation",
            "",
            "No copy-length alpha/item-type pair beats the active shared copy-length",
            "alpha `1` and searched item-type split at book `6`, order `1`, alpha",
            "`2`. The full pair space is closed by the non-negative minima of the",
            "two complete component frontiers.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost-ledger audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("108_post_itemctx_param_copy_length_alpha_item_type_pair_search", result, lines)


if __name__ == "__main__":
    main()
