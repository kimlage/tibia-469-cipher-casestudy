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
PAIR_PAYLOAD_ITEM = HERE / "scripts/105_post_itemctx_param_payload_item_type_pair_context_search.py"
PAIR_COPY_ITEM = HERE / "scripts/106_post_itemctx_param_copy_length_item_type_pair_context_search.py"
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


def compact_payload(row: dict) -> dict:
    return {
        "model": row["model"],
        "family": row["family"],
        "split_book": row["split_book"],
        "delta_vs_current_bits": row["delta_vs_current_bits"],
        "component_delta_bits": row["component_delta_bits"],
        "declaration_delta_bits": row["declaration_delta_bits"],
        "changed": row["changed"],
    }


def compact_copy_length(row: dict) -> dict:
    return {
        "model": row["model"],
        "family": row["family"],
        "split_book": row["split_book"],
        "delta_vs_current_bits": row["delta_vs_current_bits"],
        "component_delta_bits": row["component_delta_bits"],
        "declaration_delta_bits": row["declaration_delta_bits"],
        "changed": row["changed"],
    }


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


def triple_row(current_bits: float, payload_row: dict, copy_row: dict, item_row: dict) -> dict:
    delta = (
        payload_row["delta_vs_current_bits"]
        + copy_row["delta_vs_current_bits"]
        + item_row["delta_vs_current_bits"]
    )
    return {
        "payload_family": payload_row["family"],
        "payload_model": payload_row["model"],
        "payload_split_book": payload_row["split_book"],
        "payload_delta_bits": payload_row["delta_vs_current_bits"],
        "payload_changed": payload_row["changed"],
        "copy_length_family": copy_row["family"],
        "copy_length_model": copy_row["model"],
        "copy_length_split_book": copy_row["split_book"],
        "copy_length_delta_bits": copy_row["delta_vs_current_bits"],
        "copy_length_changed": copy_row["changed"],
        "item_type_family": item_row["family"],
        "item_type_split_book": item_row["split_book"],
        "item_type_order": item_row["order"],
        "item_type_alpha": item_row["alpha"],
        "item_type_delta_bits": item_row["delta_vs_current_bits"],
        "item_type_changed": item_row["changed"],
        "total_bits": current_bits + delta,
        "delta_vs_current_bits": delta,
    }


def top_triples(current_bits: float, payload_rows: list[dict], copy_rows: list[dict], item_rows: list[dict], limit: int) -> list[dict]:
    heap: list[tuple[float, int, int, int]] = []
    seen = {(0, 0, 0)}
    heapq.heappush(
        heap,
        (
            payload_rows[0]["delta_vs_current_bits"]
            + copy_rows[0]["delta_vs_current_bits"]
            + item_rows[0]["delta_vs_current_bits"],
            0,
            0,
            0,
        ),
    )
    out = []
    while heap and len(out) < limit:
        _delta, payload_idx, copy_idx, item_idx = heapq.heappop(heap)
        out.append(triple_row(current_bits, payload_rows[payload_idx], copy_rows[copy_idx], item_rows[item_idx]))
        for next_idx in (
            (payload_idx + 1, copy_idx, item_idx),
            (payload_idx, copy_idx + 1, item_idx),
            (payload_idx, copy_idx, item_idx + 1),
        ):
            p_i, c_i, i_i = next_idx
            if p_i >= len(payload_rows) or c_i >= len(copy_rows) or i_i >= len(item_rows):
                continue
            if next_idx in seen:
                continue
            seen.add(next_idx)
            heapq.heappush(
                heap,
                (
                    payload_rows[p_i]["delta_vs_current_bits"]
                    + copy_rows[c_i]["delta_vs_current_bits"]
                    + item_rows[i_i]["delta_vs_current_bits"],
                    p_i,
                    c_i,
                    i_i,
                ),
            )
    return out


def best_changed_combo(current_bits: float, payload_rows: list[dict], copy_rows: list[dict], item_rows: list[dict]) -> dict:
    active_payload = next(row for row in payload_rows if not row["changed"])
    active_copy = next(row for row in copy_rows if not row["changed"])
    active_item = next(row for row in item_rows if not row["changed"])
    best_payload_changed = next(row for row in payload_rows if row["changed"])
    best_copy_changed = next(row for row in copy_rows if row["changed"])
    best_item_changed = next(row for row in item_rows if row["changed"])
    candidates = [
        triple_row(current_bits, best_payload_changed, active_copy, active_item),
        triple_row(current_bits, active_payload, best_copy_changed, active_item),
        triple_row(current_bits, active_payload, active_copy, best_item_changed),
    ]
    return min(candidates, key=lambda row: row["total_bits"])


def best_all_changed_combo(current_bits: float, payload_rows: list[dict], copy_rows: list[dict], item_rows: list[dict]) -> dict:
    return triple_row(
        current_bits,
        next(row for row in payload_rows if row["changed"]),
        next(row for row in copy_rows if row["changed"]),
        next(row for row in item_rows if row["changed"]),
    )


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("copy_length_context", CONTEXT)
    pair_payload_item = load_module("pair_payload_item", PAIR_PAYLOAD_ITEM)
    pair_copy_item = load_module("pair_copy_item", PAIR_COPY_ITEM)
    itemctx = load_module("item_type_context_family_search_verify", ITEM_CONTEXT_SEARCH)

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    payload_rows = [compact_payload(row) for row in pair_payload_item.payload_candidate_rows(formula, books, current_score)]
    copy_rows = [compact_copy_length(row) for row in pair_copy_item.copy_length_candidate_rows(formula, books, current_score, current_bits)]
    item_rows = [compact_item_type(row) for row in pair_payload_item.item_type_candidate_rows(formula, books, current_score, current_bits)]
    payload_rows.sort(key=lambda row: row["delta_vs_current_bits"])
    copy_rows.sort(key=lambda row: row["delta_vs_current_bits"])
    item_rows.sort(key=lambda row: row["delta_vs_current_bits"])

    for label, rows in (("payload", payload_rows), ("copy_length", copy_rows), ("item_type", item_rows)):
        if rows[0]["delta_vs_current_bits"] < -1e-9:
            raise RuntimeError((label, rows[0]))

    triple_count = len(payload_rows) * len(copy_rows) * len(item_rows)
    top = top_triples(current_bits, payload_rows, copy_rows, item_rows, 100)
    best = top[0]
    best_changed = best_changed_combo(current_bits, payload_rows, copy_rows, item_rows)
    best_all_changed = best_all_changed_combo(current_bits, payload_rows, copy_rows, item_rows)
    promoted = best["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_post_itemctx_param_payload_copy_length_item_type_triple_improvement"
        if promoted
        else "post_itemctx_param_payload_copy_length_item_type_triple_not_promoted"
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
        recomposed_total = score["total_bits"] + row["payload_delta_bits"] + row["copy_length_delta_bits"]
        if abs(recomposed_total - row["total_bits"]) > 1e-6:
            raise RuntimeError((recomposed_total, row["total_bits"]))
        verification.append(
            {
                "triple_delta_bits": row["delta_vs_current_bits"],
                "item_type_rescored_total_bits": score["total_bits"],
                "payload_delta_bits": row["payload_delta_bits"],
                "copy_length_delta_bits": row["copy_length_delta_bits"],
                "recomposed_total_bits": recomposed_total,
                "validation_errors": score["validation"]["errors"],
            }
        )

    result = {
        "schema": "post_itemctx_param_payload_copy_length_item_type_triple_context_search.v1",
        "test": "107_post_itemctx_param_payload_copy_length_item_type_triple_context_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "payload_candidates_tested": len(payload_rows),
        "copy_length_candidates_tested": len(copy_rows),
        "item_type_candidates_tested": len(item_rows),
        "triple_candidates_proven_by_component_minima": triple_count,
        "best_triple": best,
        "best_changed_triple": best_changed,
        "best_all_changed_triple": best_all_changed,
        "top_triples": top,
        "top_payload_models": payload_rows[:20],
        "top_copy_length_models": copy_rows[:20],
        "top_item_type_models": item_rows[:20],
        "authoritative_item_rescore_checks": verification,
        "promotion_rule": (
            "promote only if a decodable literal-payload context plus copy-length "
            "context plus item-type context family/order/alpha triple beats the "
            "active global payload, midpoint copy-length, and item-type split "
            "model after charged declaration bits while preserving 70/70 "
            "roundtrip and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Payload/Copy-Length/Item-Type Triple Context Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit combines the post-itemctx_param literal-payload, copy-length,",
        "and item-type context frontiers. These are independent MDL components in",
        "the current ledger, so the full triple space is proven by component",
        "minima and the top triples are generated with a sorted heap. The top",
        "triples are then checked by authoritative item-type rescoring plus",
        "payload and copy-length deltas.",
        "",
        "## Coverage",
        "",
        f"- Payload candidates: `{len(payload_rows)}`",
        f"- Copy-length candidates: `{len(copy_rows)}`",
        f"- Item-type candidates: `{len(item_rows)}`",
        f"- Triple candidates proven by component minima: `{triple_count}`",
        "",
        "## Top Triples",
        "",
        "| Rank | Payload | Copy | Copy split | Item | Item split | Order | Alpha | Total bits | Delta |",
        "|---:|---|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top[:20], start=1):
        copy_split = "" if row["copy_length_split_book"] is None else str(row["copy_length_split_book"])
        item_split = "" if row["item_type_split_book"] is None else str(row["item_type_split_book"])
        lines.append(
            f"| `{rank}` | `{row['payload_family']}` | `{row['copy_length_family']}` | `{copy_split}` | "
            f"`{row['item_type_family']}` | `{item_split}` | `{row['item_type_order']}` | "
            f"`{row['item_type_alpha']}` | `{row['total_bits']:.3f}` | "
            f"`{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Changed Triple",
            "",
            f"- Delta vs current: `{best_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Payload: `{best_changed['payload_family']}`",
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
            "## Best Triple With All Three Components Changed",
            "",
            f"- Delta vs current: `{best_all_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Payload: `{best_all_changed['payload_family']}`",
            f"- Copy-length: `{best_all_changed['copy_length_family']}`"
            + (
                ""
                if best_all_changed["copy_length_split_book"] is None
                else f" split `{best_all_changed['copy_length_split_book']}`"
            ),
            f"- Item-type: `{best_all_changed['item_type_family']}`"
            + (
                ""
                if best_all_changed["item_type_split_book"] is None
                else f" split `{best_all_changed['item_type_split_book']}`"
            )
            + f", order `{best_all_changed['item_type_order']}`, alpha `{best_all_changed['item_type_alpha']}`",
            "",
            "## Interpretation",
            "",
            "No payload/copy-length/item-type context triple beats the active global",
            "payload, book-midpoint copy-length context, and searched item-type split",
            "at book `6`, order `1`, alpha `2`. The full triple space is closed by",
            "the non-negative minima of the three complete component frontiers.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost-ledger audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("107_post_itemctx_param_payload_copy_length_item_type_triple_context_search", result, lines)


if __name__ == "__main__":
    main()
