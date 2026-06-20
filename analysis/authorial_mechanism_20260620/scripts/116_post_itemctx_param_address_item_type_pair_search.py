from __future__ import annotations

import copy
import heapq
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
ADDRESS_COPY_ORDER_PAIR = HERE / "scripts/115_post_itemctx_param_address_copy_order_pair_search.py"
PAYLOAD_ITEM_PAIR = HERE / "scripts/105_post_itemctx_param_payload_item_type_pair_context_search.py"
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
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def pair_row(current_bits: float, address_row: dict, item_row: dict) -> dict:
    delta = address_row["delta_vs_current_bits"] + item_row["delta_vs_current_bits"]
    decodable = bool(address_row["decodable"])
    return {
        "address_model": address_row["model"],
        "address_delta_bits": address_row["delta_vs_current_bits"],
        "address_decodable": address_row["decodable"],
        "address_changed": address_row["changed"],
        "item_type_family": item_row["family"],
        "item_type_split_book": item_row["split_book"],
        "item_type_order": item_row["order"],
        "item_type_alpha": item_row["alpha"],
        "item_type_delta_bits": item_row["delta_vs_current_bits"],
        "item_type_changed": item_row["changed"],
        "decodable": decodable,
        "changed": address_row["changed"] or item_row["changed"],
        "total_bits": current_bits + delta,
        "delta_vs_current_bits": delta,
    }


def top_pairs(current_bits: float, address_rows: list[dict], item_rows: list[dict], limit: int) -> list[dict]:
    heap: list[tuple[float, int, int]] = []
    seen = {(0, 0)}
    heapq.heappush(
        heap,
        (address_rows[0]["delta_vs_current_bits"] + item_rows[0]["delta_vs_current_bits"], 0, 0),
    )
    out = []
    while heap and len(out) < limit:
        _delta, address_idx, item_idx = heapq.heappop(heap)
        out.append(pair_row(current_bits, address_rows[address_idx], item_rows[item_idx]))
        for next_idx in ((address_idx + 1, item_idx), (address_idx, item_idx + 1)):
            a_i, i_i = next_idx
            if a_i >= len(address_rows) or i_i >= len(item_rows):
                continue
            if next_idx in seen:
                continue
            seen.add(next_idx)
            heapq.heappush(
                heap,
                (address_rows[a_i]["delta_vs_current_bits"] + item_rows[i_i]["delta_vs_current_bits"], a_i, i_i),
            )
    return out


def best_pair_matching(current_bits: float, address_rows: list[dict], item_rows: list[dict], predicate) -> dict:
    matches = (
        pair_row(current_bits, address, item)
        for address in address_rows
        for item in item_rows
        if predicate(address, item)
    )
    return min(matches, key=lambda row: row["total_bits"])


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("copy_length_context", CONTEXT)
    address_pair = load_module("address_copy_order_pair", ADDRESS_COPY_ORDER_PAIR)
    payload_item_pair = load_module("payload_item_pair", PAYLOAD_ITEM_PAIR)
    itemctx = load_module("item_type_context_family_search_verify", ITEM_CONTEXT_SEARCH)

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    address_rows, seed_stats = address_pair.address_candidate_rows(formula, books, current_score, current_bits)
    item_rows = [
        compact_item_type(row)
        for row in payload_item_pair.item_type_candidate_rows(formula, books, current_score, current_bits)
    ]
    address_rows.sort(key=lambda row: row["delta_vs_current_bits"])
    item_rows.sort(key=lambda row: row["delta_vs_current_bits"])

    pair_count = len(address_rows) * len(item_rows)
    top = top_pairs(current_bits, address_rows, item_rows, 100)
    best_any = top[0]
    best_decodable = best_pair_matching(
        current_bits,
        address_rows,
        item_rows,
        lambda address, _item: address["decodable"],
    )
    best_changed_decodable = best_pair_matching(
        current_bits,
        address_rows,
        item_rows,
        lambda address, item: address["decodable"] and (address["changed"] or item["changed"]),
    )
    best_both_changed_decodable = best_pair_matching(
        current_bits,
        address_rows,
        item_rows,
        lambda address, item: address["decodable"] and address["changed"] and item["changed"],
    )
    promoted = best_decodable["changed"] and best_decodable["total_bits"] < current_bits - 1e-9
    if promoted:
        classification = "controlled_post_itemctx_param_address_item_type_pair_improvement"
    elif best_any["total_bits"] < current_bits - 1e-9 and not best_any["decodable"]:
        classification = "post_itemctx_param_address_item_type_pair_optimistic_only_not_promoted"
    else:
        classification = "post_itemctx_param_address_item_type_pair_not_promoted"

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
        recomposed_total = score["total_bits"] + row["address_delta_bits"]
        if abs(recomposed_total - row["total_bits"]) > 1e-6:
            raise RuntimeError((recomposed_total, row["total_bits"]))
        verification.append(
            {
                "pair_delta_bits": row["delta_vs_current_bits"],
                "item_type_rescored_total_bits": score["total_bits"],
                "address_delta_bits": row["address_delta_bits"],
                "recomposed_total_bits": recomposed_total,
                "validation_errors": score["validation"]["errors"],
            }
        )

    result = {
        "schema": "post_itemctx_param_address_item_type_pair_search.v1",
        "test": "116_post_itemctx_param_address_item_type_pair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "address_candidates_tested": len(address_rows),
        "item_type_candidates_tested": len(item_rows),
        "pair_candidates_proven_by_component_minima": pair_count,
        "best_pair_any": best_any,
        "best_pair_decodable": best_decodable,
        "best_changed_pair_decodable": best_changed_decodable,
        "best_both_changed_pair_decodable": best_both_changed_decodable,
        "top_pairs": top,
        "address_models": address_rows,
        "top_item_type_models": item_rows[:20],
        "seed_stats": seed_stats,
        "authoritative_item_rescore_checks": verification,
        "promotion_rule": (
            "promote only if a decodable address-model plus item-type "
            "context/order/alpha pair beats the active min_len-bounded absolute "
            "source address and item-type split model after charged declaration "
            "bits while preserving 70/70 roundtrip and translation_delta NONE; "
            "nondecodable no-mode address rows are lower bounds only"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Address/Item-Type Pair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit combines the post-itemctx_param address-model frontier with",
        "the item-type context/order/alpha frontier. A pair can promote only if",
        "the address side is decodable; no-mode literal-seed address rows remain",
        "optimistic lower bounds.",
        "",
        "## Coverage",
        "",
        f"- Address candidates: `{len(address_rows)}`",
        f"- Item-type candidates: `{len(item_rows)}`",
        f"- Pair candidates proven by component minima: `{pair_count}`",
        "",
        "## Top Pairs",
        "",
        "| Rank | Address model | Item family | Item split | Order | Alpha | Decodable | Total bits | Delta |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top[:20], start=1):
        split = "" if row["item_type_split_book"] is None else str(row["item_type_split_book"])
        lines.append(
            f"| `{rank}` | `{row['address_model']}` | `{row['item_type_family']}` | `{split}` | "
            f"`{row['item_type_order']}` | `{row['item_type_alpha']}` | `{row['decodable']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Decodable Pair",
            "",
            f"- Delta vs current: `{best_decodable['delta_vs_current_bits']:.3f}` bits",
            f"- Address: `{best_decodable['address_model']}`",
            f"- Item-type: `{best_decodable['item_type_family']}`, order `{best_decodable['item_type_order']}`, alpha `{best_decodable['item_type_alpha']}`",
            "",
            "## Best Changed Decodable Pair",
            "",
            f"- Delta vs current: `{best_changed_decodable['delta_vs_current_bits']:.3f}` bits",
            f"- Address: `{best_changed_decodable['address_model']}`",
            f"- Item-type: `{best_changed_decodable['item_type_family']}`, order `{best_changed_decodable['item_type_order']}`, alpha `{best_changed_decodable['item_type_alpha']}`",
            "",
            "## Best Decodable Pair With Both Components Changed",
            "",
            f"- Delta vs current: `{best_both_changed_decodable['delta_vs_current_bits']:.3f}` bits",
            f"- Address: `{best_both_changed_decodable['address_model']}`",
            f"- Item-type: `{best_both_changed_decodable['item_type_family']}`, order `{best_both_changed_decodable['item_type_order']}`, alpha `{best_both_changed_decodable['item_type_alpha']}`",
            "",
            "## Interpretation",
            "",
            "The best overall pairs are optimistic lower bounds because they use the",
            "literal-seed no-mode address row. The best decodable pair is the active",
            "ledger, and every changed decodable pair is worse after declaration and",
            "mode costs.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost-ledger audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("116_post_itemctx_param_address_item_type_pair_search", result, lines)


if __name__ == "__main__":
    main()
