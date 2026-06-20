from __future__ import annotations

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
    payload = load_module("post_midpoint_alpha1_literal_payload_context_search", PAYLOAD_CONTEXT)
    frontier = payload.load_module("minaddr_frontier", FRONTIER)
    midpoint = payload.load_module("post_midpoint_frontier", MIDPOINT)
    context_module = payload.load_module("post_adaptive_copy_length_context", CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    model = formula["policy"]["literal_payload_model"]
    alpha = float(model["alpha"])
    current_declaration_bits = int(model["model_declaration_bits"])
    current_payload_bits = float(current_score["literal_payload_bits"])
    fixed_nonpayload_bits = current_bits - current_payload_bits
    literal_rows = payload.collect_literal_digit_rows(formula, books)

    active_bits, active_audit_rows, active_context_counts = payload.payload_bits(
        literal_rows,
        alpha,
        lambda _row: "global",
    )
    if abs(active_bits - current_payload_bits) > 1e-6:
        raise RuntimeError((active_bits, current_payload_bits))

    candidate_specs = [
        (
            "active_global_literal_payload_context",
            "active_global",
            "single global payload context",
            lambda _row: "global",
        ),
        (
            "book_midpoint_35_literal_payload_context",
            "fixed_book_midpoint",
            "book_id < 35 versus book_id >= 35",
            lambda row: "first_half" if int(row["book_int"]) < 35 else "second_half",
        ),
        (
            "book_quartile_literal_payload_context",
            "fixed_book_quartile",
            "four fixed numeric book quartiles",
            lambda row: min(3, int(row["book_int"]) // 18),
        ),
        (
            "book_decade_literal_payload_context",
            "fixed_book_decade",
            "numeric book decade bucket",
            lambda row: int(row["book_int"]) // 10,
        ),
        (
            "book_parity_literal_payload_context",
            "fixed_book_parity",
            "numeric book id parity",
            lambda row: int(row["book_int"]) % 2,
        ),
        (
            "literal_run_length_log_context",
            "literal_run_length",
            "log bucket of current literal-run length",
            lambda row: payload.log_bucket(int(row["literal_run_length"]), 6),
        ),
        (
            "literal_offset_log_context",
            "literal_offset",
            "log bucket of digit offset inside the literal run",
            lambda row: payload.log_bucket(int(row["literal_offset"]) + 1, 6),
        ),
        (
            "copy_index_proxy_global_position_context",
            "global_position",
            "log bucket of generated digit position before literal digit",
            lambda row: payload.log_bucket(int(row["global_digit_pos"]) + 1, 14),
        ),
    ]

    models = []
    for name, family, description, context_fn in candidate_specs:
        bits, audit_rows, counts = payload.payload_bits(literal_rows, alpha, context_fn)
        context_count = len(counts)
        declaration_bits = (
            current_declaration_bits
            if name == "active_global_literal_payload_context"
            else payload.contextual_payload_declaration_bits(current_declaration_bits, context_count)
        )
        total_bits = fixed_nonpayload_bits + bits + declaration_bits - current_declaration_bits
        models.append(
            {
                "model": name,
                "family": family,
                "context_description": description,
                "literal_payload_bits": bits,
                "literal_payload_model_declaration_bits": declaration_bits,
                "context_count": context_count,
                "context_counts": counts,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "component_delta_bits": bits - current_payload_bits,
                "declaration_delta_bits": declaration_bits - current_declaration_bits,
                "decodable": True,
                "audit_rows": audit_rows,
            }
        )

    searched_split_rows = []
    for split_book in range(1, 70):
        bits, audit_rows, counts = payload.payload_bits(
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
        total_bits = fixed_nonpayload_bits + bits + declaration_bits - current_declaration_bits
        searched_split_rows.append(
            {
                "model": "searched_single_book_split_literal_payload_context",
                "family": "searched_single_book_split",
                "split_book": split_book,
                "context_description": f"book_id < {split_book} versus book_id >= {split_book}",
                "literal_payload_bits": bits,
                "literal_payload_model_declaration_bits": declaration_bits,
                "context_count": len(counts),
                "context_counts": counts,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "component_delta_bits": bits - current_payload_bits,
                "declaration_delta_bits": declaration_bits - current_declaration_bits,
                "decodable": True,
                "audit_rows": audit_rows,
            }
        )
    best_searched_split = min(searched_split_rows, key=lambda row: row["total_bits"])
    models.append(best_searched_split)
    models.sort(key=lambda row: row["total_bits"])
    best_decodable = next(row for row in models if row["decodable"])
    promoted = (
        best_decodable["model"] != "active_global_literal_payload_context"
        and best_decodable["total_bits"] < current_bits - 1e-9
    )
    classification = (
        "controlled_post_itemctx_param_literal_payload_context_improvement"
        if promoted
        else "post_itemctx_param_literal_payload_context_not_promoted"
    )

    result = {
        "schema": "post_itemctx_param_literal_payload_context_search.v1",
        "test": "103_post_itemctx_param_literal_payload_context_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "literal_digit_items": len(literal_rows),
        "literal_runs": len({row["literal_run_id"] for row in literal_rows}),
        "current_literal_payload_bits": current_payload_bits,
        "current_literal_payload_model_declaration_bits": current_declaration_bits,
        "best_model": payload.strip_audit_rows(best_decodable),
        "models": [payload.strip_audit_rows(row) for row in models],
        "searched_single_split_models": [
            payload.strip_audit_rows(row)
            for row in sorted(searched_split_rows, key=lambda row: row["total_bits"])
        ],
        "best_context_audit_rows": best_decodable["audit_rows"],
        "promotion_rule": (
            "promote only if a decodable literal-payload context beats the active "
            "global previous-emitted-digit payload model after charged declaration "
            "bits while preserving 70/70 roundtrip and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Literal Payload Context Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests whether the adaptive literal payload model should be",
        "split by a simple context after the itemctx_param promotion. The recipe,",
        "literal-run length model, copy-address ledger, copy-length model,",
        "item-type model, forced rules, and book-length ledger are fixed.",
        "",
        "## Payload Context Models",
        "",
        "| Rank | Model | Contexts | Payload bits | Model bits | Total bits | Delta vs current | Component delta |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(models, start=1):
        lines.append(
            f"| `{rank}` | `{row['model']}` | `{row['context_count']}` | "
            f"`{row['literal_payload_bits']:.3f}` | `{row['literal_payload_model_declaration_bits']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` | "
            f"`{row['component_delta_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Searched Split",
            "",
            f"- Split book: `{best_searched_split['split_book']}`",
            f"- Total bits: `{best_searched_split['total_bits']:.3f}`",
            f"- Delta vs current: `{best_searched_split['delta_vs_current_bits']:.3f}`",
            f"- Component delta: `{best_searched_split['component_delta_bits']:.3f}`",
            f"- Declaration delta: `{best_searched_split['declaration_delta_bits']}`",
            "",
            "## Interpretation",
            "",
            "A literal-payload context is promoted only if its component savings",
            "survive the extra declaration cost. Otherwise the active global",
            "previous-emitted-digit payload model remains the current formula.",
            "",
            "## Boundary",
            "",
            "This is a mechanical payload-cost audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("103_post_itemctx_param_literal_payload_context_search", result, lines)


if __name__ == "__main__":
    main()
