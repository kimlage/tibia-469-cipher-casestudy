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
COPY_CONTEXT_ALPHA = HERE / "scripts/111_post_itemctx_param_copy_length_context_alpha_resweep.py"
PAYLOAD_CONTEXT_ALPHA = HERE / "scripts/112_post_itemctx_param_literal_payload_context_alpha_resweep.py"
PAYLOAD_CONTEXT = HERE / "scripts/93_post_midpoint_alpha1_literal_payload_context_search.py"
COPY_CONTEXT_RESWEEP = HERE / "scripts/91_post_midpoint_alpha1_copy_length_context_resweep.py"

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


def compact_copy(row: dict) -> dict:
    return {
        "model": row["model"],
        "family": row["family"],
        "split_book": row["split_book"],
        "alpha": row["alpha"],
        "context_count": row["context_count"],
        "delta_vs_current_bits": row["delta_vs_current_bits"],
        "component_delta_bits": row["component_delta_bits"],
        "declaration_delta_bits": row["declaration_delta_bits"],
        "context_changed": row["context_changed"],
        "alpha_changed": row["alpha_changed"],
        "changed": row["changed"],
    }


def compact_payload(row: dict) -> dict:
    return {
        "model": row["model"],
        "family": row["family"],
        "split_book": row["split_book"],
        "alpha": row["alpha"],
        "context_count": row["context_count"],
        "delta_vs_current_bits": row["delta_vs_current_bits"],
        "component_delta_bits": row["component_delta_bits"],
        "declaration_delta_bits": row["declaration_delta_bits"],
        "context_changed": row["context_changed"],
        "alpha_changed": row["alpha_changed"],
        "changed": row["changed"],
    }


def pair_row(current_bits: float, copy_row: dict, payload_row: dict) -> dict:
    delta = copy_row["delta_vs_current_bits"] + payload_row["delta_vs_current_bits"]
    return {
        "copy_model": copy_row["model"],
        "copy_family": copy_row["family"],
        "copy_split_book": copy_row["split_book"],
        "copy_alpha": copy_row["alpha"],
        "copy_context_count": copy_row["context_count"],
        "copy_delta_bits": copy_row["delta_vs_current_bits"],
        "copy_changed": copy_row["changed"],
        "payload_model": payload_row["model"],
        "payload_family": payload_row["family"],
        "payload_split_book": payload_row["split_book"],
        "payload_alpha": payload_row["alpha"],
        "payload_context_count": payload_row["context_count"],
        "payload_delta_bits": payload_row["delta_vs_current_bits"],
        "payload_changed": payload_row["changed"],
        "total_bits": current_bits + delta,
        "delta_vs_current_bits": delta,
    }


def top_pairs(current_bits: float, copy_rows: list[dict], payload_rows: list[dict], limit: int) -> list[dict]:
    heap: list[tuple[float, int, int]] = []
    seen = {(0, 0)}
    heapq.heappush(
        heap,
        (copy_rows[0]["delta_vs_current_bits"] + payload_rows[0]["delta_vs_current_bits"], 0, 0),
    )
    out = []
    while heap and len(out) < limit:
        _delta, copy_idx, payload_idx = heapq.heappop(heap)
        out.append(pair_row(current_bits, copy_rows[copy_idx], payload_rows[payload_idx]))
        for next_idx in ((copy_idx + 1, payload_idx), (copy_idx, payload_idx + 1)):
            c_i, p_i = next_idx
            if c_i >= len(copy_rows) or p_i >= len(payload_rows):
                continue
            if next_idx in seen:
                continue
            seen.add(next_idx)
            heapq.heappush(
                heap,
                (copy_rows[c_i]["delta_vs_current_bits"] + payload_rows[p_i]["delta_vs_current_bits"], c_i, p_i),
            )
    return out


def copy_candidate_rows(formula: dict, books: dict[str, str], current_score: dict, current_bits: float) -> list[dict]:
    copy_alpha = load_module("copy_context_alpha", COPY_CONTEXT_ALPHA)
    context_module = load_module("post_adaptive_copy_length_context", CONTEXT)
    resweep = load_module("post_midpoint_alpha1_copy_length_context_resweep", COPY_CONTEXT_RESWEEP)

    copy_rows = context_module.collect_copy_rows(formula, books)
    current_alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    current_declaration_bits = int(formula["policy"]["copy_length_model"]["model_declaration_bits"])
    copy_base_declaration_bits = int(
        formula["policy"]["copy_length_model"]["replaces"]["replaces"]["model_declaration_bits"]
    )
    current_length_bits = float(current_score["copy_length_code_bits"])
    fixed_nonlength_bits = current_bits - current_length_bits

    rows = []
    for spec in copy_alpha.context_specs(copy_rows, resweep):
        for alpha in range(1, 65):
            rows.append(
                compact_copy(
                    copy_alpha.candidate_row(
                        spec=spec,
                        context_fn=spec["context_fn"],
                        rows=copy_rows,
                        alpha=alpha,
                        context_module=context_module,
                        resweep=resweep,
                        current_length_bits=current_length_bits,
                        current_total_bits=current_bits,
                        fixed_nonlength_bits=fixed_nonlength_bits,
                        current_declaration_bits=current_declaration_bits,
                        copy_base_declaration_bits=copy_base_declaration_bits,
                        current_alpha=current_alpha,
                    )
                )
            )
    rows.sort(key=lambda row: row["delta_vs_current_bits"])
    return rows


def payload_candidate_rows(formula: dict, books: dict[str, str], current_score: dict, current_bits: float) -> list[dict]:
    payload_alpha = load_module("payload_context_alpha", PAYLOAD_CONTEXT_ALPHA)
    payload = load_module("post_midpoint_alpha1_literal_payload_context_search", PAYLOAD_CONTEXT)

    model = formula["policy"]["literal_payload_model"]
    current_alpha = int(model["alpha"])
    current_declaration_bits = int(model["model_declaration_bits"])
    base_declaration_bits = payload_alpha.payload_base_declaration_bits(
        payload,
        current_declaration_bits,
        current_alpha,
    )
    current_payload_bits = float(current_score["literal_payload_bits"])
    fixed_nonpayload_bits = current_bits - current_payload_bits
    literal_rows = payload.collect_literal_digit_rows(formula, books)

    rows = []
    for spec in payload_alpha.context_specs(payload):
        for alpha in range(1, 65):
            rows.append(
                compact_payload(
                    payload_alpha.candidate_row(
                        spec=spec,
                        context_fn=spec["context_fn"],
                        literal_rows=literal_rows,
                        alpha=alpha,
                        payload=payload,
                        current_payload_bits=current_payload_bits,
                        current_total_bits=current_bits,
                        fixed_nonpayload_bits=fixed_nonpayload_bits,
                        current_declaration_bits=current_declaration_bits,
                        base_declaration_bits=base_declaration_bits,
                        current_alpha=current_alpha,
                    )
                )
            )
    rows.sort(key=lambda row: row["delta_vs_current_bits"])
    return rows


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

    copy_rows = copy_candidate_rows(formula, books, current_score, current_bits)
    payload_rows = payload_candidate_rows(formula, books, current_score, current_bits)

    for label, rows in (("copy_context_alpha", copy_rows), ("payload_context_alpha", payload_rows)):
        if rows[0]["delta_vs_current_bits"] < -1e-9:
            raise RuntimeError((label, rows[0]))

    pair_count = len(copy_rows) * len(payload_rows)
    top = top_pairs(current_bits, copy_rows, payload_rows, 100)
    best = top[0]
    active_copy = next(row for row in copy_rows if not row["changed"])
    active_payload = next(row for row in payload_rows if not row["changed"])
    best_copy_changed = next(row for row in copy_rows if row["changed"])
    best_payload_changed = next(row for row in payload_rows if row["changed"])
    best_changed = min(
        [
            pair_row(current_bits, best_copy_changed, active_payload),
            pair_row(current_bits, active_copy, best_payload_changed),
        ],
        key=lambda row: row["total_bits"],
    )
    best_both_changed = pair_row(current_bits, best_copy_changed, best_payload_changed)
    promoted = best["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_post_itemctx_param_copy_payload_context_alpha_pair_improvement"
        if promoted
        else "post_itemctx_param_copy_payload_context_alpha_pair_not_promoted"
    )

    result = {
        "schema": "post_itemctx_param_copy_payload_context_alpha_pair_search.v1",
        "test": "113_post_itemctx_param_copy_payload_context_alpha_pair_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_context_alpha_candidates_tested": len(copy_rows),
        "payload_context_alpha_candidates_tested": len(payload_rows),
        "pair_candidates_proven_by_component_minima": pair_count,
        "best_pair": best,
        "best_changed_pair": best_changed,
        "best_both_changed_pair": best_both_changed,
        "top_pairs": top,
        "top_copy_context_alpha_models": copy_rows[:20],
        "top_payload_context_alpha_models": payload_rows[:20],
        "promotion_rule": (
            "promote only if a decodable copy-length context/shared-alpha row "
            "plus a literal-payload context/shared-alpha row beats the active "
            "book-midpoint copy-length alpha=1 and global payload alpha=1 models "
            "after charged declaration bits while preserving 70/70 roundtrip and "
            "translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Copy/Payload Context-Alpha Pair Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit combines the post-itemctx_param copy-length context/shared-alpha",
        "frontier with the literal-payload context/shared-alpha frontier. These",
        "are independent MDL components in the current ledger, so the full pair",
        "space is proven by component minima and the top pairs are generated with",
        "a sorted heap.",
        "",
        "## Coverage",
        "",
        f"- Copy-length context/alpha candidates: `{len(copy_rows)}`",
        f"- Literal-payload context/alpha candidates: `{len(payload_rows)}`",
        f"- Pair candidates proven by component minima: `{pair_count}`",
        "",
        "## Top Pairs",
        "",
        "| Rank | Copy family | Copy split | Copy alpha | Payload family | Payload split | Payload alpha | Total bits | Delta |",
        "|---:|---|---:|---:|---|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(top[:20], start=1):
        copy_split = "" if row["copy_split_book"] is None else str(row["copy_split_book"])
        payload_split = "" if row["payload_split_book"] is None else str(row["payload_split_book"])
        lines.append(
            f"| `{rank}` | `{row['copy_family']}` | `{copy_split}` | `{row['copy_alpha']}` | "
            f"`{row['payload_family']}` | `{payload_split}` | `{row['payload_alpha']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Changed Pair",
            "",
            f"- Delta vs current: `{best_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Copy: `{best_changed['copy_family']}`, alpha `{best_changed['copy_alpha']}`",
            f"- Payload: `{best_changed['payload_family']}`, alpha `{best_changed['payload_alpha']}`",
            "",
            "## Best Pair With Both Components Changed",
            "",
            f"- Delta vs current: `{best_both_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Copy: `{best_both_changed['copy_family']}`, alpha `{best_both_changed['copy_alpha']}`",
            f"- Payload: `{best_both_changed['payload_family']}`, alpha `{best_both_changed['payload_alpha']}`",
            "",
            "## Interpretation",
            "",
            "No copy-length context-alpha / literal-payload context-alpha pair beats",
            "the active book-midpoint copy-length `alpha=1` model and global",
            "literal-payload `alpha=1` model. The full pair space is closed by the",
            "non-negative minima of the two complete component frontiers.",
            "",
            "## Boundary",
            "",
            "This is a mechanical cost-ledger audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("113_post_itemctx_param_copy_payload_context_alpha_pair_search", result, lines)


if __name__ == "__main__":
    main()
