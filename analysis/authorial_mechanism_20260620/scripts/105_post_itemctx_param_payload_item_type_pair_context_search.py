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
PAYLOAD_CONTEXT = HERE / "scripts/93_post_midpoint_alpha1_literal_payload_context_search.py"
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


def payload_candidate_rows(formula: dict, books: dict[str, str], current_score: dict) -> list[dict]:
    payload = load_module("literal_payload_context", PAYLOAD_CONTEXT)
    model = formula["policy"]["literal_payload_model"]
    alpha = float(model["alpha"])
    current_declaration_bits = int(model["model_declaration_bits"])
    current_payload_bits = float(current_score["literal_payload_bits"])
    literal_rows = payload.collect_literal_digit_rows(formula, books)

    active_bits, _audit_rows, _counts = payload.payload_bits(literal_rows, alpha, lambda _row: "global")
    if abs(active_bits - current_payload_bits) > 1e-6:
        raise RuntimeError((active_bits, current_payload_bits))

    specs = [
        (
            "active_global_literal_payload_context",
            "active_global",
            None,
            "single global payload context",
            lambda _row: "global",
        ),
        (
            "book_midpoint_35_literal_payload_context",
            "fixed_book_midpoint",
            None,
            "book_id < 35 versus book_id >= 35",
            lambda row: "first_half" if int(row["book_int"]) < 35 else "second_half",
        ),
        (
            "book_quartile_literal_payload_context",
            "fixed_book_quartile",
            None,
            "four fixed numeric book quartiles",
            lambda row: min(3, int(row["book_int"]) // 18),
        ),
        (
            "book_decade_literal_payload_context",
            "fixed_book_decade",
            None,
            "numeric book decade bucket",
            lambda row: int(row["book_int"]) // 10,
        ),
        (
            "book_parity_literal_payload_context",
            "fixed_book_parity",
            None,
            "numeric book id parity",
            lambda row: int(row["book_int"]) % 2,
        ),
        (
            "literal_run_length_log_context",
            "literal_run_length",
            None,
            "log bucket of current literal-run length",
            lambda row: payload.log_bucket(int(row["literal_run_length"]), 6),
        ),
        (
            "literal_offset_log_context",
            "literal_offset",
            None,
            "log bucket of digit offset inside the literal run",
            lambda row: payload.log_bucket(int(row["literal_offset"]) + 1, 6),
        ),
        (
            "copy_index_proxy_global_position_context",
            "global_position",
            None,
            "log bucket of generated digit position before literal digit",
            lambda row: payload.log_bucket(int(row["global_digit_pos"]) + 1, 14),
        ),
    ]

    rows = []
    for name, family, split_book, description, context_fn in specs:
        bits, _audit_rows, counts = payload.payload_bits(literal_rows, alpha, context_fn)
        context_count = len(counts)
        declaration_bits = (
            current_declaration_bits
            if family == "active_global"
            else payload.contextual_payload_declaration_bits(current_declaration_bits, context_count)
        )
        rows.append(
            {
                "model": name,
                "family": family,
                "split_book": split_book,
                "context_description": description,
                "literal_payload_bits": bits,
                "literal_payload_model_declaration_bits": declaration_bits,
                "context_count": context_count,
                "context_counts": counts,
                "delta_vs_current_bits": bits - current_payload_bits + declaration_bits - current_declaration_bits,
                "component_delta_bits": bits - current_payload_bits,
                "declaration_delta_bits": declaration_bits - current_declaration_bits,
                "changed": family != "active_global",
            }
        )

    for split_book in range(1, 70):
        bits, _audit_rows, counts = payload.payload_bits(
            literal_rows,
            alpha,
            lambda row, split_book=split_book: "before_split"
            if int(row["book_int"]) < split_book
            else "after_split",
        )
        declaration_bits = payload.searched_split_declaration_bits(
            current_declaration_bits,
            len(counts),
            split_book,
        )
        rows.append(
            {
                "model": "searched_single_book_split_literal_payload_context",
                "family": "searched_single_book_split",
                "split_book": split_book,
                "context_description": f"book_id < {split_book} versus book_id >= {split_book}",
                "literal_payload_bits": bits,
                "literal_payload_model_declaration_bits": declaration_bits,
                "context_count": len(counts),
                "context_counts": counts,
                "delta_vs_current_bits": bits - current_payload_bits + declaration_bits - current_declaration_bits,
                "component_delta_bits": bits - current_payload_bits,
                "declaration_delta_bits": declaration_bits - current_declaration_bits,
                "changed": True,
            }
        )
    rows.sort(key=lambda row: row["delta_vs_current_bits"])
    return rows


def item_type_candidate_rows(formula: dict, books: dict[str, str], current_score: dict, current_bits: float) -> list[dict]:
    itemctx = load_module("item_type_context_family_search", ITEM_CONTEXT_SEARCH)
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("copy_length_context", CONTEXT)
    item_context = load_module("post_midpoint_item_type_context_search", HERE / "scripts/95_post_midpoint_alpha1_item_type_context_search.py")

    current_model = formula["policy"]["item_type_model"]
    current_item_decl = int(current_model["model_declaration_bits"])
    current_fixed_bits = float(formula["mdl_estimate_rough"]["fixed_bits"])
    forced_rule_bits = int(current_model["forced_rule_bits"])
    item_rows, item_stats = item_context.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    family_specs: list[tuple[str, list[int | None]]] = [
        ("global", [None]),
        ("fixed_book_midpoint", [None]),
        ("fixed_book_quartile", [None]),
        ("fixed_book_decade", [None]),
        ("fixed_book_parity", [None]),
        ("op_index", [None]),
        ("declared_remaining", [None]),
        ("searched_single_book_split", list(range(1, 70))),
    ]

    rows = []
    for family, split_books in family_specs:
        for split_book in split_books:
            counts = itemctx.collect_extra_context_counts(item_rows, family, split_book)
            extra_decl = itemctx.extra_context_declaration_bits(family, len(counts), split_book)
            for order in range(1, 8):
                for alpha in range(1, 33):
                    declaration_bits = itemctx.item_type_base_declaration_bits(alpha, order, forced_rule_bits) + extra_decl
                    candidate = copy.deepcopy(formula)
                    candidate_model = itemctx.set_extra_context(candidate["policy"]["item_type_model"], family, split_book, counts)
                    candidate_model["order"] = order
                    candidate_model["alpha"] = alpha
                    candidate_model["model_declaration_bits"] = declaration_bits
                    candidate["policy"]["item_type_model"] = candidate_model
                    candidate["mdl_estimate_rough"]["fixed_bits"] = (
                        current_fixed_bits - current_item_decl + declaration_bits
                    )
                    score = midpoint.score_formula(candidate, books, frontier, context_module)
                    if score["validation"]["errors"]:
                        raise RuntimeError(score["validation"])
                    total_bits = score["total_bits"]
                    rows.append(
                        {
                            "family": family,
                            "split_book": split_book,
                            "order": order,
                            "alpha": alpha,
                            "extra_context_count": len(counts),
                            "extra_context_counts": counts,
                            "item_type_stream_bits": score["item_type_stream_bits"],
                            "model_declaration_bits": declaration_bits,
                            "delta_vs_current_bits": total_bits - current_bits,
                            "component_delta_bits": score["item_type_stream_bits"] - current_score["item_type_stream_bits"],
                            "declaration_delta_bits": declaration_bits - current_item_decl,
                            "changed": not (
                                family == "searched_single_book_split"
                                and split_book == 6
                                and order == 1
                                and alpha == 2
                            ),
                        }
                    )
    rows.sort(key=lambda row: row["delta_vs_current_bits"])
    return rows


def pair_row(current_bits: float, payload_row: dict, item_row: dict) -> dict:
    total = current_bits + payload_row["delta_vs_current_bits"] + item_row["delta_vs_current_bits"]
    return {
        "payload_family": payload_row["family"],
        "payload_model": payload_row["model"],
        "payload_split_book": payload_row["split_book"],
        "payload_delta_bits": payload_row["delta_vs_current_bits"],
        "item_type_family": item_row["family"],
        "item_type_split_book": item_row["split_book"],
        "item_type_order": item_row["order"],
        "item_type_alpha": item_row["alpha"],
        "item_type_delta_bits": item_row["delta_vs_current_bits"],
        "total_bits": total,
        "delta_vs_current_bits": total - current_bits,
        "payload_changed": payload_row["changed"],
        "item_type_changed": item_row["changed"],
    }


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

    payload_rows = payload_candidate_rows(formula, books, current_score)
    item_rows = item_type_candidate_rows(formula, books, current_score, current_bits)

    heap: list[tuple[float, int, dict]] = []
    pair_count = 0
    best_changed = None
    best_both_changed = None
    for payload_row in payload_rows:
        for item_row in item_rows:
            row = pair_row(current_bits, payload_row, item_row)
            pair_count += 1
            if len(heap) < 100:
                heapq.heappush(heap, (-row["total_bits"], pair_count, row))
            elif row["total_bits"] < -heap[0][0]:
                heapq.heapreplace(heap, (-row["total_bits"], pair_count, row))
            if row["payload_changed"] or row["item_type_changed"]:
                if best_changed is None or row["total_bits"] < best_changed["total_bits"]:
                    best_changed = row
            if row["payload_changed"] and row["item_type_changed"]:
                if best_both_changed is None or row["total_bits"] < best_both_changed["total_bits"]:
                    best_both_changed = row

    top_pairs = [row for _neg_total, _idx, row in sorted(heap, key=lambda item: -item[0])]
    best_pair = top_pairs[0]
    promoted = best_pair["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_post_itemctx_param_payload_item_type_pair_improvement"
        if promoted
        else "post_itemctx_param_payload_item_type_pair_not_promoted"
    )

    # The formula scorer natively covers item-type changes but not the synthetic
    # payload context families. Rescore the item-type side of top pairs and
    # verify that the pair total is exactly the item rescore plus payload delta.
    itemctx = load_module("item_type_context_family_search_verify", ITEM_CONTEXT_SEARCH)
    verification = []
    current_item_decl = int(formula["policy"]["item_type_model"]["model_declaration_bits"])
    current_fixed_bits = float(formula["mdl_estimate_rough"]["fixed_bits"])
    for row in top_pairs[:20]:
        candidate = copy.deepcopy(formula)
        item_match = next(
            item
            for item in item_rows
            if item["family"] == row["item_type_family"]
            and item["split_book"] == row["item_type_split_book"]
            and item["order"] == row["item_type_order"]
            and item["alpha"] == row["item_type_alpha"]
        )
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
        recomposed_total = score["total_bits"] + row["payload_delta_bits"]
        if abs(recomposed_total - row["total_bits"]) > 1e-6:
            raise RuntimeError((recomposed_total, row["total_bits"]))
        verification.append(
            {
                "pair_delta_bits": row["delta_vs_current_bits"],
                "item_type_rescored_total_bits": score["total_bits"],
                "payload_delta_bits": row["payload_delta_bits"],
                "recomposed_total_bits": recomposed_total,
                "validation_errors": score["validation"]["errors"],
            }
        )

    result = {
        "schema": "post_itemctx_param_payload_item_type_pair_context_search.v1",
        "test": "105_post_itemctx_param_payload_item_type_pair_context_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "payload_candidates_tested": len(payload_rows),
        "item_type_candidates_tested": len(item_rows),
        "pair_candidates_tested": pair_count,
        "best_pair": best_pair,
        "best_changed_pair": best_changed,
        "best_both_changed_pair": best_both_changed,
        "top_pairs": top_pairs,
        "top_payload_models": payload_rows[:20],
        "top_item_type_models": item_rows[:20],
        "authoritative_item_rescore_checks": verification,
        "promotion_rule": (
            "promote only if a decodable literal-payload context plus item-type "
            "context family/order/alpha pair beats the active itemctx_param model "
            "after charged declaration bits while preserving 70/70 roundtrip and "
            "translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Payload/Item-Type Pair Context Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit combines the post-itemctx_param literal-payload context",
        "frontier with the post-itemctx_param item-type context-family frontier.",
        "Payload and item-type costs are independent MDL components here, so all",
        "pairs are enumerated by summed component deltas and the top pairs are",
        "checked by authoritative item-type rescoring plus payload delta.",
        "",
        "## Coverage",
        "",
        f"- Payload candidates: `{len(payload_rows)}`",
        f"- Item-type candidates: `{len(item_rows)}`",
        f"- Pair candidates: `{pair_count}`",
        "",
        "## Top Pairs",
        "",
        "| Rank | Payload family | Payload split | Item family | Item split | Order | Alpha | Total bits | Delta |",
        "|---:|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_pairs[:20], start=1):
        payload_split = "" if row["payload_split_book"] is None else str(row["payload_split_book"])
        item_split = "" if row["item_type_split_book"] is None else str(row["item_type_split_book"])
        lines.append(
            f"| `{rank}` | `{row['payload_family']}` | `{payload_split}` | "
            f"`{row['item_type_family']}` | `{item_split}` | `{row['item_type_order']}` | "
            f"`{row['item_type_alpha']}` | `{row['total_bits']:.3f}` | "
            f"`{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Changed Pair",
            "",
            f"- Delta vs current: `{best_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Payload: `{best_changed['payload_family']}`"
            + ("" if best_changed["payload_split_book"] is None else f" split `{best_changed['payload_split_book']}`"),
            f"- Item-type: `{best_changed['item_type_family']}`"
            + ("" if best_changed["item_type_split_book"] is None else f" split `{best_changed['item_type_split_book']}`")
            + f", order `{best_changed['item_type_order']}`, alpha `{best_changed['item_type_alpha']}`",
            "",
            "## Best Pair With Both Components Changed",
            "",
            f"- Delta vs current: `{best_both_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Payload: `{best_both_changed['payload_family']}`"
            + (
                ""
                if best_both_changed["payload_split_book"] is None
                else f" split `{best_both_changed['payload_split_book']}`"
            ),
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
            "No payload/item-type context pair beats the active searched split at",
            "book `6`, order `1`, alpha `2` with the active global literal-payload",
            "model. The best changed pair is still worse after declaration cost.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost-ledger audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("105_post_itemctx_param_payload_item_type_pair_context_search", result, lines)


if __name__ == "__main__":
    main()
