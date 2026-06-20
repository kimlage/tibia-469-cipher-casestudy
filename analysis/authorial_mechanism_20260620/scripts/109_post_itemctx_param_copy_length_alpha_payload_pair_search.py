from __future__ import annotations

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
ALPHA_ITEM_PAIR = HERE / "scripts/108_post_itemctx_param_copy_length_alpha_item_type_pair_search.py"
PAYLOAD_ITEM_PAIR = HERE / "scripts/105_post_itemctx_param_payload_item_type_pair_context_search.py"

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


def compact_alpha(row: dict) -> dict:
    return {
        "model": row["model"],
        "family": row["family"],
        "alpha_by_context": row["alpha_by_context"],
        "delta_vs_current_bits": row["delta_vs_current_bits"],
        "component_delta_bits": row["component_delta_bits"],
        "declaration_delta_bits": row["declaration_delta_bits"],
        "changed": row["changed"],
    }


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


def pair_row(current_bits: float, alpha_row: dict, payload_row: dict) -> dict:
    delta = alpha_row["delta_vs_current_bits"] + payload_row["delta_vs_current_bits"]
    return {
        "copy_alpha_family": alpha_row["family"],
        "copy_alpha_model": alpha_row["model"],
        "copy_alpha_by_context": alpha_row["alpha_by_context"],
        "copy_alpha_delta_bits": alpha_row["delta_vs_current_bits"],
        "copy_alpha_changed": alpha_row["changed"],
        "payload_family": payload_row["family"],
        "payload_model": payload_row["model"],
        "payload_split_book": payload_row["split_book"],
        "payload_delta_bits": payload_row["delta_vs_current_bits"],
        "payload_changed": payload_row["changed"],
        "total_bits": current_bits + delta,
        "delta_vs_current_bits": delta,
    }


def top_pairs(current_bits: float, alpha_rows: list[dict], payload_rows: list[dict], limit: int) -> list[dict]:
    heap: list[tuple[float, int, int]] = []
    seen = {(0, 0)}
    heapq.heappush(
        heap,
        (alpha_rows[0]["delta_vs_current_bits"] + payload_rows[0]["delta_vs_current_bits"], 0, 0),
    )
    out = []
    while heap and len(out) < limit:
        _delta, alpha_idx, payload_idx = heapq.heappop(heap)
        out.append(pair_row(current_bits, alpha_rows[alpha_idx], payload_rows[payload_idx]))
        for next_idx in ((alpha_idx + 1, payload_idx), (alpha_idx, payload_idx + 1)):
            a_i, p_i = next_idx
            if a_i >= len(alpha_rows) or p_i >= len(payload_rows):
                continue
            if next_idx in seen:
                continue
            seen.add(next_idx)
            heapq.heappush(
                heap,
                (
                    alpha_rows[a_i]["delta_vs_current_bits"] + payload_rows[p_i]["delta_vs_current_bits"],
                    a_i,
                    p_i,
                ),
            )
    return out


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("copy_length_context", CONTEXT)
    alpha_item_pair = load_module("alpha_item_pair", ALPHA_ITEM_PAIR)
    payload_item_pair = load_module("payload_item_pair", PAYLOAD_ITEM_PAIR)

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    alpha_rows = [
        compact_alpha(row)
        for row in alpha_item_pair.alpha_candidate_rows(formula, books, current_score, current_bits)
    ]
    payload_rows = [
        compact_payload(row)
        for row in payload_item_pair.payload_candidate_rows(formula, books, current_score)
    ]
    alpha_rows.sort(key=lambda row: row["delta_vs_current_bits"])
    payload_rows.sort(key=lambda row: row["delta_vs_current_bits"])

    if alpha_rows[0]["delta_vs_current_bits"] < -1e-9:
        raise RuntimeError(("alpha", alpha_rows[0]))
    if payload_rows[0]["delta_vs_current_bits"] < -1e-9:
        raise RuntimeError(("payload", payload_rows[0]))

    pair_count = len(alpha_rows) * len(payload_rows)
    top = top_pairs(current_bits, alpha_rows, payload_rows, 100)
    best = top[0]
    active_alpha = next(row for row in alpha_rows if not row["changed"])
    active_payload = next(row for row in payload_rows if not row["changed"])
    best_alpha_changed = next(row for row in alpha_rows if row["changed"])
    best_payload_changed = next(row for row in payload_rows if row["changed"])
    best_changed = min(
        [
            pair_row(current_bits, best_alpha_changed, active_payload),
            pair_row(current_bits, active_alpha, best_payload_changed),
        ],
        key=lambda row: row["total_bits"],
    )
    best_both_changed = pair_row(current_bits, best_alpha_changed, best_payload_changed)
    promoted = best["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_post_itemctx_param_copy_length_alpha_payload_pair_improvement"
        if promoted
        else "post_itemctx_param_copy_length_alpha_payload_pair_not_promoted"
    )

    result = {
        "schema": "post_itemctx_param_copy_length_alpha_payload_pair_search.v1",
        "test": "109_post_itemctx_param_copy_length_alpha_payload_pair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_alpha_candidates_tested": len(alpha_rows),
        "payload_candidates_tested": len(payload_rows),
        "pair_candidates_proven_by_component_minima": pair_count,
        "best_pair": best,
        "best_changed_pair": best_changed,
        "best_both_changed_pair": best_both_changed,
        "top_pairs": top,
        "top_copy_alpha_models": alpha_rows[:20],
        "top_payload_models": payload_rows[:20],
        "promotion_rule": (
            "promote only if a decodable copy-length alpha-by-context row plus "
            "literal-payload context beats the active shared copy-length alpha=1 "
            "and global payload model after charged declaration bits while "
            "preserving 70/70 roundtrip and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Copy-Length Alpha/Payload Pair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit combines the post-itemctx_param midpoint copy-length",
        "alpha-by-context grid with the post-itemctx_param literal-payload context",
        "frontier. The two costs are independent MDL components here, so the full",
        "pair space is proven by component minima and the top pairs are generated",
        "with a sorted heap.",
        "",
        "## Coverage",
        "",
        f"- Copy-length alpha candidates: `{len(alpha_rows)}`",
        f"- Payload candidates: `{len(payload_rows)}`",
        f"- Pair candidates proven by component minima: `{pair_count}`",
        "",
        "## Top Pairs",
        "",
        "| Rank | Copy alpha by context | Payload family | Payload split | Total bits | Delta |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for rank, row in enumerate(top[:20], start=1):
        payload_split = "" if row["payload_split_book"] is None else str(row["payload_split_book"])
        lines.append(
            f"| `{rank}` | `{row['copy_alpha_by_context']}` | `{row['payload_family']}` | "
            f"`{payload_split}` | `{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Changed Pair",
            "",
            f"- Delta vs current: `{best_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Copy alpha: `{best_changed['copy_alpha_by_context']}`",
            f"- Payload: `{best_changed['payload_family']}`"
            + (
                ""
                if best_changed["payload_split_book"] is None
                else f" split `{best_changed['payload_split_book']}`"
            ),
            "",
            "## Best Pair With Both Components Changed",
            "",
            f"- Delta vs current: `{best_both_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Copy alpha: `{best_both_changed['copy_alpha_by_context']}`",
            f"- Payload: `{best_both_changed['payload_family']}`"
            + (
                ""
                if best_both_changed["payload_split_book"] is None
                else f" split `{best_both_changed['payload_split_book']}`"
            ),
            "",
            "## Interpretation",
            "",
            "No copy-length alpha/payload pair beats the active shared copy-length",
            "alpha `1` and global literal-payload model. The full pair space is",
            "closed by the non-negative minima of the two complete component",
            "frontiers.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost-ledger audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("109_post_itemctx_param_copy_length_alpha_payload_pair_search", result, lines)


if __name__ == "__main__":
    main()
