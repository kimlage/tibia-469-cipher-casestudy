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
ADDRESS_SEARCH = HERE / "scripts/89_post_midpoint_alpha1_address_model_search.py"

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
    address = load_module("post_midpoint_alpha1_address_model_search", ADDRESS_SEARCH)
    frontier = address.load_module("minaddr_frontier", FRONTIER)
    midpoint = address.load_module("post_midpoint_frontier", MIDPOINT)
    context_module = address.load_module("post_adaptive_copy_length_context", CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    _spans, literal_rows, copy_rows = address.build_rows(formula, books, current_score)
    absolute_bits = address.current_copy_bits(copy_rows)
    if abs(absolute_bits - current_score["copy_bits"]) > 1e-6:
        raise RuntimeError((absolute_bits, current_score["copy_bits"]))

    fixed_noncopy_bits = current_score["total_bits"] - current_score["copy_bits"]
    standard = address.standard_address_models(copy_rows)
    seed_models, seed_stats = address.literal_seed_models(copy_rows, literal_rows, absolute_bits)
    rows = []
    for row in [*standard, *seed_models]:
        total_bits = fixed_noncopy_bits + row["copy_bits"]
        rows.append(
            {
                **row,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_score["total_bits"],
            }
        )
    rows.sort(key=lambda row: row["total_bits"])
    best_decodable = next(row for row in rows if row["decodable"])
    best_any = rows[0]

    if (
        best_decodable["model"] != "absolute_digit_source_pos_min_len_bounded"
        and best_decodable["total_bits"] < current_bits - 1e-9
    ):
        classification = "post_itemctx_param_address_model_candidate"
    elif best_any["total_bits"] < current_bits - 1e-9 and not best_any["decodable"]:
        classification = "post_itemctx_param_address_optimistic_only_not_promoted"
    else:
        classification = "post_itemctx_param_address_absolute_minaddr_retained"

    result = {
        "schema": "post_itemctx_param_address_model_search.v1",
        "test": "99_post_itemctx_param_address_model_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "fixed_noncopy_bits": fixed_noncopy_bits,
        "copy_items": len(copy_rows),
        "same_book_copy_items": sum(1 for row in copy_rows if row["same_book"]),
        "models": rows,
        "seed_stats": seed_stats,
        "promotion_rule": (
            "promote only if a decodable copy-source address ledger beats the active "
            "itemctx_param min_len-bounded absolute digit source positions under full rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Address Model Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests copy-source address ledgers after the itemctx_param",
        "promotion. The recipe, copy lengths, book lengths, literal payload model,",
        "item-type model, forced rules, midpoint context, and alpha=1 copy-length",
        "model are fixed; only the copy source-address ledger changes.",
        "",
        "## Address Models",
        "",
        "| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model']}` | `{row['copy_bits']:.1f}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_current_bits']:.1f}` | `{row['decodable']}` | "
            f"`{row.get('seed_copy_count', 0)}` |"
        )
    lines.extend(
        [
            "",
            "## Seed Address Shape",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Copy items | `{len(copy_rows)}` |",
            f"| Same-book copy items | `{sum(1 for row in copy_rows if row['same_book'])}` |",
            f"| Copy items with any prior literal-seed address | `{seed_stats['seed_usable_copy_items']}` |",
            f"| Copy items with positive optimistic seed saving | `{seed_stats['seed_positive_saving_copy_items']}` |",
            f"| Optimistic seed address savings | `{seed_stats['optimistic_seed_address_savings_bits']:.1f}` bits |",
            f"| Best sparse seed extra cost | `{seed_stats['best_sparse_seed_extra_bits']:.1f}` bits |",
            "",
            "## Interpretation",
            "",
            "The active min_len-bounded absolute digit source position ledger remains",
            "promoted unless another decodable row beats it under full rescoring.",
            "Literal-seed addressing is still recorded as an optimistic lower bound",
            "when source-mode bits are not declared.",
            "",
            "## Boundary",
            "",
            "This is a mechanical address-cost audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("99_post_itemctx_param_address_model_search", result, lines)


if __name__ == "__main__":
    main()
