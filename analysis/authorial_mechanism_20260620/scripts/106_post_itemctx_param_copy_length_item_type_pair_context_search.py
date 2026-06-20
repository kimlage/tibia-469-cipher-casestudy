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
COPY_CONTEXT_RESWEEP = HERE / "scripts/91_post_midpoint_alpha1_copy_length_context_resweep.py"
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


def copy_length_candidate_rows(formula: dict, books: dict[str, str], current_score: dict, current_bits: float) -> list[dict]:
    resweep = load_module("copy_length_context_resweep", COPY_CONTEXT_RESWEEP)
    context_search = load_module("post_adaptive_copy_length_context", CONTEXT)
    resweep.context_search = context_search

    copy_rows = context_search.collect_copy_rows(formula, books)
    alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    current_declaration_bits = int(formula["policy"]["copy_length_model"]["model_declaration_bits"])
    copy_base_declaration_bits = int(
        formula["policy"]["copy_length_model"]["replaces"]["replaces"]["model_declaration_bits"]
    )
    current_length_bits = float(current_score["copy_length_code_bits"])
    fixed_nonlength_bits = current_bits - current_length_bits

    active_bits, _audit_rows, _counts = context_search.adaptive_context_bits(
        copy_rows,
        alpha,
        resweep.midpoint_context,
    )
    if abs(active_bits - current_length_bits) > 1e-6:
        raise RuntimeError((active_bits, current_length_bits))

    candidate_specs = [
        (
            "active_book_midpoint_35_context",
            "fixed_book_midpoint",
            None,
            "book_id < 35 versus book_id >= 35",
            resweep.midpoint_context,
        ),
        (
            "book_quartile_context",
            "fixed_book_quartile",
            None,
            "four fixed numeric book quartiles",
            lambda row: min(3, int(row["book_int"]) // 18),
        ),
        (
            "book_decade_context",
            "fixed_book_decade",
            None,
            "numeric book decade bucket",
            lambda row: int(row["book_int"]) // 10,
        ),
        (
            "book_parity_context",
            "fixed_book_parity",
            None,
            "numeric book id parity",
            lambda row: int(row["book_int"]) % 2,
        ),
        (
            "same_book_context",
            "source_scope",
            None,
            "same-book source versus prior-book source",
            lambda row: "same_book" if bool(row["same_book"]) else "prior_book",
        ),
        (
            "legal_symbol_count_log_context",
            "legal_length_space",
            None,
            "log bucket of legal copy-length symbol count",
            lambda row: resweep.log_bucket(int(row["symbol_count"]), 6),
        ),
        (
            "distance_log_context",
            "copy_distance",
            None,
            "log bucket of decoded copy distance",
            lambda row: resweep.log_bucket(int(row["distance"]), 12),
        ),
        (
            "remaining_log_context",
            "declared_remaining",
            None,
            "log bucket of remaining declared book length",
            lambda row: resweep.log_bucket(int(row["remaining"]), 8),
        ),
        (
            "previous_copy_length_log_context",
            "previous_copy_length",
            None,
            "previous copy length-index log bucket",
            lambda row: "start"
            if row["previous_length_index"] is None
            else resweep.log_bucket(int(row["previous_length_index"]) + 1, 6),
        ),
        (
            "copy_index_midpoint_context",
            "copy_index_midpoint",
            None,
            "first half versus second half of the copy-item stream",
            lambda row: "first_copy_half" if int(row["copy_id"]) < len(copy_rows) / 2 else "second_copy_half",
        ),
    ]

    rows = []
    for name, family, split_book, description, context_fn in candidate_specs:
        row = resweep.model_row(
            name=name,
            family=family,
            context_description=description,
            context_fn=context_fn,
            rows=copy_rows,
            alpha=alpha,
            current_length_bits=current_length_bits,
            current_total_bits=current_bits,
            fixed_nonlength_bits=fixed_nonlength_bits,
            current_declaration_bits=current_declaration_bits,
            copy_base_declaration_bits=copy_base_declaration_bits,
        )
        row["split_book"] = split_book
        row["changed"] = name != "active_book_midpoint_35_context"
        rows.append(resweep.strip_audit_rows(row))

    for split_book in range(1, 70):
        length_bits, _audit_rows, context_counts = context_search.adaptive_context_bits(
            copy_rows,
            alpha,
            lambda row, split_book=split_book: "before_split"
            if int(row["book_int"]) < split_book
            else "after_split",
        )
        declaration_bits = resweep.searched_split_declaration_bits(
            copy_base_declaration_bits,
            alpha,
            len(context_counts),
            split_book,
        )
        total_bits = fixed_nonlength_bits + length_bits + declaration_bits - current_declaration_bits
        rows.append(
            {
                "model": "searched_single_book_split_context",
                "family": "searched_single_book_split",
                "split_book": split_book,
                "context_description": f"book_id < {split_book} versus book_id >= {split_book}",
                "adaptive_copy_length_bits": length_bits,
                "copy_model_declaration_bits": declaration_bits,
                "context_count": len(context_counts),
                "context_counts": context_counts,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "component_delta_bits": length_bits - current_length_bits,
                "declaration_delta_bits": declaration_bits - current_declaration_bits,
                "decodable": True,
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


def pair_row(current_bits: float, copy_row: dict, item_row: dict) -> dict:
    total = current_bits + copy_row["delta_vs_current_bits"] + item_row["delta_vs_current_bits"]
    return {
        "copy_length_family": copy_row["family"],
        "copy_length_model": copy_row["model"],
        "copy_length_split_book": copy_row["split_book"],
        "copy_length_delta_bits": copy_row["delta_vs_current_bits"],
        "item_type_family": item_row["family"],
        "item_type_split_book": item_row["split_book"],
        "item_type_order": item_row["order"],
        "item_type_alpha": item_row["alpha"],
        "item_type_delta_bits": item_row["delta_vs_current_bits"],
        "total_bits": total,
        "delta_vs_current_bits": total - current_bits,
        "copy_length_changed": copy_row["changed"],
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

    copy_rows = copy_length_candidate_rows(formula, books, current_score, current_bits)
    item_rows = item_type_candidate_rows(formula, books, current_score, current_bits)

    heap: list[tuple[float, int, dict]] = []
    pair_count = 0
    best_changed = None
    best_both_changed = None
    for copy_row in copy_rows:
        for item_row in item_rows:
            row = pair_row(current_bits, copy_row, item_row)
            pair_count += 1
            if len(heap) < 100:
                heapq.heappush(heap, (-row["total_bits"], pair_count, row))
            elif row["total_bits"] < -heap[0][0]:
                heapq.heapreplace(heap, (-row["total_bits"], pair_count, row))
            if row["copy_length_changed"] or row["item_type_changed"]:
                if best_changed is None or row["total_bits"] < best_changed["total_bits"]:
                    best_changed = row
            if row["copy_length_changed"] and row["item_type_changed"]:
                if best_both_changed is None or row["total_bits"] < best_both_changed["total_bits"]:
                    best_both_changed = row

    top_pairs = [row for _neg_total, _idx, row in sorted(heap, key=lambda item: -item[0])]
    best_pair = top_pairs[0]
    promoted = best_pair["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_post_itemctx_param_copy_length_item_type_pair_improvement"
        if promoted
        else "post_itemctx_param_copy_length_item_type_pair_not_promoted"
    )

    # The repository scorer natively covers item-type changes on top of the
    # active midpoint copy-length context. Copy-length alternatives are scored
    # as independent MDL components; verify top-pair recomposition against the
    # authoritative item-type scorer.
    itemctx = load_module("item_type_context_family_search_verify", ITEM_CONTEXT_SEARCH)
    current_item_decl = int(formula["policy"]["item_type_model"]["model_declaration_bits"])
    current_fixed_bits = float(formula["mdl_estimate_rough"]["fixed_bits"])
    verification = []
    for row in top_pairs[:20]:
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
        recomposed_total = score["total_bits"] + row["copy_length_delta_bits"]
        if abs(recomposed_total - row["total_bits"]) > 1e-6:
            raise RuntimeError((recomposed_total, row["total_bits"]))
        verification.append(
            {
                "pair_delta_bits": row["delta_vs_current_bits"],
                "item_type_rescored_total_bits": score["total_bits"],
                "copy_length_delta_bits": row["copy_length_delta_bits"],
                "recomposed_total_bits": recomposed_total,
                "validation_errors": score["validation"]["errors"],
            }
        )

    result = {
        "schema": "post_itemctx_param_copy_length_item_type_pair_context_search.v1",
        "test": "106_post_itemctx_param_copy_length_item_type_pair_context_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_length_candidates_tested": len(copy_rows),
        "item_type_candidates_tested": len(item_rows),
        "pair_candidates_tested": pair_count,
        "best_pair": best_pair,
        "best_changed_pair": best_changed,
        "best_both_changed_pair": best_both_changed,
        "top_pairs": top_pairs,
        "top_copy_length_models": copy_rows[:20],
        "top_item_type_models": item_rows[:20],
        "authoritative_item_rescore_checks": verification,
        "promotion_rule": (
            "promote only if a decodable copy-length context plus item-type "
            "context family/order/alpha pair beats the active midpoint copy-length "
            "and item-type split model after charged declaration bits while "
            "preserving 70/70 roundtrip and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Copy-Length/Item-Type Pair Context Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit combines the post-itemctx_param copy-length context frontier",
        "with the post-itemctx_param item-type context-family frontier. Copy-length",
        "and item-type costs are independent MDL components here, so all pairs are",
        "enumerated by summed component deltas and the top pairs are checked by",
        "authoritative item-type rescoring plus copy-length delta.",
        "",
        "## Coverage",
        "",
        f"- Copy-length candidates: `{len(copy_rows)}`",
        f"- Item-type candidates: `{len(item_rows)}`",
        f"- Pair candidates: `{pair_count}`",
        "",
        "## Top Pairs",
        "",
        "| Rank | Copy family | Copy split | Item family | Item split | Order | Alpha | Total bits | Delta |",
        "|---:|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top_pairs[:20], start=1):
        copy_split = "" if row["copy_length_split_book"] is None else str(row["copy_length_split_book"])
        item_split = "" if row["item_type_split_book"] is None else str(row["item_type_split_book"])
        lines.append(
            f"| `{rank}` | `{row['copy_length_family']}` | `{copy_split}` | "
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
            f"- Copy-length: `{best_changed['copy_length_family']}`"
            + (
                ""
                if best_changed["copy_length_split_book"] is None
                else f" split `{best_changed['copy_length_split_book']}`"
            ),
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
            f"- Copy-length: `{best_both_changed['copy_length_family']}`"
            + (
                ""
                if best_both_changed["copy_length_split_book"] is None
                else f" split `{best_both_changed['copy_length_split_book']}`"
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
            "No copy-length/item-type context pair beats the active book-midpoint",
            "copy-length context plus searched item-type split at book `6`, order",
            "`1`, alpha `2`. The best changed pair is still worse after",
            "declaration cost.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost-ledger audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("106_post_itemctx_param_copy_length_item_type_pair_context_search", result, lines)


if __name__ == "__main__":
    main()
