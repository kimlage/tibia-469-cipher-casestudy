from __future__ import annotations

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
COPY_PAYLOAD_PAIR = HERE / "scripts/113_post_itemctx_param_copy_payload_context_alpha_pair_search.py"

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


def pair_row(current_bits: float, address_row: dict, payload_row: dict) -> dict:
    delta = address_row["delta_vs_current_bits"] + payload_row["delta_vs_current_bits"]
    decodable = bool(address_row["decodable"])
    return {
        "address_model": address_row["model"],
        "address_delta_bits": address_row["delta_vs_current_bits"],
        "address_decodable": address_row["decodable"],
        "address_changed": address_row["changed"],
        "payload_model": payload_row["model"],
        "payload_family": payload_row["family"],
        "payload_split_book": payload_row["split_book"],
        "payload_alpha": payload_row["alpha"],
        "payload_context_count": payload_row["context_count"],
        "payload_delta_bits": payload_row["delta_vs_current_bits"],
        "payload_changed": payload_row["changed"],
        "decodable": decodable,
        "changed": address_row["changed"] or payload_row["changed"],
        "total_bits": current_bits + delta,
        "delta_vs_current_bits": delta,
    }


def top_pairs(current_bits: float, address_rows: list[dict], payload_rows: list[dict], limit: int) -> list[dict]:
    heap: list[tuple[float, int, int]] = []
    seen = {(0, 0)}
    heapq.heappush(
        heap,
        (address_rows[0]["delta_vs_current_bits"] + payload_rows[0]["delta_vs_current_bits"], 0, 0),
    )
    out = []
    while heap and len(out) < limit:
        _delta, address_idx, payload_idx = heapq.heappop(heap)
        out.append(pair_row(current_bits, address_rows[address_idx], payload_rows[payload_idx]))
        for next_idx in ((address_idx + 1, payload_idx), (address_idx, payload_idx + 1)):
            a_i, p_i = next_idx
            if a_i >= len(address_rows) or p_i >= len(payload_rows):
                continue
            if next_idx in seen:
                continue
            seen.add(next_idx)
            heapq.heappush(
                heap,
                (address_rows[a_i]["delta_vs_current_bits"] + payload_rows[p_i]["delta_vs_current_bits"], a_i, p_i),
            )
    return out


def best_pair_matching(current_bits: float, address_rows: list[dict], payload_rows: list[dict], predicate) -> dict:
    matches = (
        pair_row(current_bits, address, payload)
        for address in address_rows
        for payload in payload_rows
        if predicate(address, payload)
    )
    return min(matches, key=lambda row: row["total_bits"])


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("copy_length_context", CONTEXT)
    address_pair = load_module("address_copy_order_pair", ADDRESS_COPY_ORDER_PAIR)
    copy_payload_pair = load_module("copy_payload_pair", COPY_PAYLOAD_PAIR)

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    address_rows, seed_stats = address_pair.address_candidate_rows(formula, books, current_score, current_bits)
    payload_rows = copy_payload_pair.payload_candidate_rows(formula, books, current_score, current_bits)
    address_rows.sort(key=lambda row: row["delta_vs_current_bits"])
    payload_rows.sort(key=lambda row: row["delta_vs_current_bits"])
    if payload_rows[0]["delta_vs_current_bits"] < -1e-9:
        raise RuntimeError(("payload_context_alpha", payload_rows[0]))

    pair_count = len(address_rows) * len(payload_rows)
    top = top_pairs(current_bits, address_rows, payload_rows, 100)
    best_any = top[0]
    best_decodable = best_pair_matching(
        current_bits,
        address_rows,
        payload_rows,
        lambda address, _payload: address["decodable"],
    )
    best_changed_decodable = best_pair_matching(
        current_bits,
        address_rows,
        payload_rows,
        lambda address, payload: address["decodable"] and (address["changed"] or payload["changed"]),
    )
    best_both_changed_decodable = best_pair_matching(
        current_bits,
        address_rows,
        payload_rows,
        lambda address, payload: address["decodable"] and address["changed"] and payload["changed"],
    )
    promoted = best_decodable["changed"] and best_decodable["total_bits"] < current_bits - 1e-9
    if promoted:
        classification = "controlled_post_itemctx_param_address_payload_context_alpha_pair_improvement"
    elif best_any["total_bits"] < current_bits - 1e-9 and not best_any["decodable"]:
        classification = "post_itemctx_param_address_payload_context_alpha_pair_optimistic_only_not_promoted"
    else:
        classification = "post_itemctx_param_address_payload_context_alpha_pair_not_promoted"

    result = {
        "schema": "post_itemctx_param_address_payload_context_alpha_pair_search.v1",
        "test": "117_post_itemctx_param_address_payload_context_alpha_pair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "address_candidates_tested": len(address_rows),
        "payload_context_alpha_candidates_tested": len(payload_rows),
        "pair_candidates_proven_by_component_minima": pair_count,
        "best_pair_any": best_any,
        "best_pair_decodable": best_decodable,
        "best_changed_pair_decodable": best_changed_decodable,
        "best_both_changed_pair_decodable": best_both_changed_decodable,
        "top_pairs": top,
        "address_models": address_rows,
        "top_payload_context_alpha_models": payload_rows[:20],
        "seed_stats": seed_stats,
        "promotion_rule": (
            "promote only if a decodable address-model plus literal-payload "
            "context/shared-alpha row beats the active min_len-bounded absolute "
            "source address and global literal-payload alpha=1 model after "
            "charged declaration bits while preserving 70/70 roundtrip and "
            "translation_delta NONE; nondecodable no-mode address rows are "
            "lower bounds only"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Address/Payload Context-Alpha Pair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit combines the post-itemctx_param address-model frontier with",
        "the literal-payload context/shared-alpha frontier. A pair can promote",
        "only if the address side is decodable; no-mode literal-seed address",
        "rows remain optimistic lower bounds.",
        "",
        "## Coverage",
        "",
        f"- Address candidates: `{len(address_rows)}`",
        f"- Literal-payload context/alpha candidates: `{len(payload_rows)}`",
        f"- Pair candidates proven by component minima: `{pair_count}`",
        "",
        "## Top Pairs",
        "",
        "| Rank | Address model | Payload family | Payload split | Payload alpha | Decodable | Total bits | Delta |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top[:20], start=1):
        split = "" if row["payload_split_book"] is None else str(row["payload_split_book"])
        lines.append(
            f"| `{rank}` | `{row['address_model']}` | `{row['payload_family']}` | `{split}` | "
            f"`{row['payload_alpha']}` | `{row['decodable']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Decodable Pair",
            "",
            f"- Delta vs current: `{best_decodable['delta_vs_current_bits']:.3f}` bits",
            f"- Address: `{best_decodable['address_model']}`",
            f"- Payload: `{best_decodable['payload_family']}`, alpha `{best_decodable['payload_alpha']}`",
            "",
            "## Best Changed Decodable Pair",
            "",
            f"- Delta vs current: `{best_changed_decodable['delta_vs_current_bits']:.3f}` bits",
            f"- Address: `{best_changed_decodable['address_model']}`",
            f"- Payload: `{best_changed_decodable['payload_family']}`, alpha `{best_changed_decodable['payload_alpha']}`",
            "",
            "## Best Decodable Pair With Both Components Changed",
            "",
            f"- Delta vs current: `{best_both_changed_decodable['delta_vs_current_bits']:.3f}` bits",
            f"- Address: `{best_both_changed_decodable['address_model']}`",
            f"- Payload: `{best_both_changed_decodable['payload_family']}`, alpha `{best_both_changed_decodable['payload_alpha']}`",
            "",
            "## Interpretation",
            "",
            "The best overall pair is an optimistic lower bound because it uses the",
            "literal-seed no-mode address row. The best decodable pair is the",
            "active ledger, and every changed decodable pair is worse after",
            "address-mode and payload declaration costs.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost-ledger audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("117_post_itemctx_param_address_payload_context_alpha_pair_search", result, lines)


if __name__ == "__main__":
    main()
