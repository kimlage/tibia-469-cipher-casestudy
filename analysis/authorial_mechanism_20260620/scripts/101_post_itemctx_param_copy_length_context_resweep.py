from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_itemctx_param_context2_alpha1_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"
CONTEXT_RESWEEP = HERE / "scripts/91_post_midpoint_alpha1_copy_length_context_resweep.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_itemctx_param_context2_alpha1_minaddr_repair2_bits"


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
    resweep = load_module("post_midpoint_alpha1_copy_length_context_resweep", CONTEXT_RESWEEP)
    frontier = resweep.load_module("minaddr_frontier", FRONTIER)
    midpoint = resweep.load_module("post_midpoint_frontier", MIDPOINT)
    context_search = resweep.load_module("post_adaptive_copy_length_context", CONTEXT)
    resweep.context_search = context_search

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_search)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    rows = context_search.collect_copy_rows(formula, books)
    alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    current_declaration_bits = int(formula["policy"]["copy_length_model"]["model_declaration_bits"])
    copy_base_declaration_bits = int(
        formula["policy"]["copy_length_model"]["replaces"]["replaces"]["model_declaration_bits"]
    )
    current_length_bits = float(current_score["copy_length_code_bits"])
    fixed_nonlength_bits = current_bits - current_length_bits

    active_bits, active_audit_rows, active_context_counts = context_search.adaptive_context_bits(
        rows,
        alpha,
        resweep.midpoint_context,
    )
    if abs(active_bits - current_length_bits) > 1e-6:
        raise RuntimeError((active_bits, current_length_bits))

    candidate_specs = [
        (
            "active_book_midpoint_35_context",
            "fixed_book_midpoint",
            "book_id < 35 versus book_id >= 35",
            resweep.midpoint_context,
        ),
        (
            "book_quartile_context",
            "fixed_book_quartile",
            "four fixed numeric book quartiles",
            lambda row: min(3, int(row["book_int"]) // 18),
        ),
        (
            "book_decade_context",
            "fixed_book_decade",
            "numeric book decade bucket",
            lambda row: int(row["book_int"]) // 10,
        ),
        (
            "book_parity_context",
            "fixed_book_parity",
            "numeric book id parity",
            lambda row: int(row["book_int"]) % 2,
        ),
        (
            "same_book_context",
            "source_scope",
            "same-book source versus prior-book source",
            lambda row: "same_book" if bool(row["same_book"]) else "prior_book",
        ),
        (
            "legal_symbol_count_log_context",
            "legal_length_space",
            "log bucket of legal copy-length symbol count",
            lambda row: resweep.log_bucket(int(row["symbol_count"]), 6),
        ),
        (
            "distance_log_context",
            "copy_distance",
            "log bucket of decoded copy distance",
            lambda row: resweep.log_bucket(int(row["distance"]), 12),
        ),
        (
            "remaining_log_context",
            "declared_remaining",
            "log bucket of remaining declared book length",
            lambda row: resweep.log_bucket(int(row["remaining"]), 8),
        ),
        (
            "previous_copy_length_log_context",
            "previous_copy_length",
            "previous copy length-index log bucket",
            lambda row: "start"
            if row["previous_length_index"] is None
            else resweep.log_bucket(int(row["previous_length_index"]) + 1, 6),
        ),
        (
            "copy_index_midpoint_context",
            "copy_index_midpoint",
            "first half versus second half of the copy-item stream",
            lambda row: "first_copy_half" if int(row["copy_id"]) < len(rows) / 2 else "second_copy_half",
        ),
    ]

    models = []
    for name, family, description, context_fn in candidate_specs:
        models.append(
            resweep.model_row(
                name=name,
                family=family,
                context_description=description,
                context_fn=context_fn,
                rows=rows,
                alpha=alpha,
                current_length_bits=current_length_bits,
                current_total_bits=current_bits,
                fixed_nonlength_bits=fixed_nonlength_bits,
                current_declaration_bits=current_declaration_bits,
                copy_base_declaration_bits=copy_base_declaration_bits,
            )
        )

    searched_split_rows = []
    for split_book in range(1, 70):
        length_bits, audit_rows, context_counts = context_search.adaptive_context_bits(
            rows,
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
        searched_split_rows.append(
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
                "audit_rows": audit_rows,
            }
        )
    models.extend(searched_split_rows)
    models.sort(key=lambda row: row["total_bits"])
    best_decodable = next(row for row in models if row["decodable"])
    promoted = (
        best_decodable["model"] != "active_book_midpoint_35_context"
        and best_decodable["total_bits"] < current_bits - 1e-9
    )
    classification = (
        "controlled_post_itemctx_param_copy_length_context_improvement"
        if promoted
        else "post_itemctx_param_copy_length_context_retains_midpoint"
    )

    if promoted:
        out = copy.deepcopy(formula)
        out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_itemctx_param_context2_alpha1_minaddr_repair2_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["copy_length_model"] = {
            **out["policy"]["copy_length_model"],
            "context_family": best_decodable["family"],
            "context_description": best_decodable["context_description"],
            "context_count": int(best_decodable["context_count"]),
            "model_declaration_bits": int(best_decodable["copy_model_declaration_bits"]),
        }
        if "split_book" in best_decodable:
            out["policy"]["copy_length_model"]["split_book"] = int(best_decodable["split_book"])
        out["policy"]["cost_model"] = out["policy"]["cost_model"] + "+copy_length_context2"
        out["mdl_estimate_rough"] = {
            **out["mdl_estimate_rough"],
            OUT_TOTAL_KEY: best_decodable["total_bits"],
            "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_bits": current_bits,
            "gain_vs_previous_itemctx_param_bits": current_bits - best_decodable["total_bits"],
            "bounded_adaptive_copy_length_bits": best_decodable["adaptive_copy_length_bits"],
            "copy_length_code_bits": best_decodable["adaptive_copy_length_bits"],
            "copy_model_declaration_bits": int(best_decodable["copy_model_declaration_bits"]),
            "copy_bits": current_score["copy_address_bits"] + best_decodable["adaptive_copy_length_bits"],
            "fixed_bits": float(formula["mdl_estimate_rough"]["fixed_bits"])
            - current_declaration_bits
            + int(best_decodable["copy_model_declaration_bits"]),
        }
        out["validation"] = {
            **out["validation"],
            "post_itemctx_param_copy_length_context_roundtrip_audit": current_score["validation"],
            "post_itemctx_param_copy_length_context_copy_items": len(rows),
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_itemctx_param_copy_length_context_resweep.v1",
        "test": "101_post_itemctx_param_copy_length_context_resweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_items": len(rows),
        "current_alpha": alpha,
        "current_copy_length_bits": current_length_bits,
        "current_copy_model_declaration_bits": current_declaration_bits,
        "copy_base_declaration_bits": copy_base_declaration_bits,
        "active_context_counts": active_context_counts,
        "best_model": resweep.strip_audit_rows(best_decodable),
        "models": [resweep.strip_audit_rows(row) for row in models],
        "best_context_audit_rows": best_decodable["audit_rows"],
        "promotion_rule": (
            "promote only if a decodable copy-length context beats the active "
            "fixed book-midpoint context after charged declaration bits with alpha=1, "
            "70/70 roundtrip, and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Copy-Length Context Resweep",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests copy-length contexts after the itemctx_param",
        "promotion. The recipe, source-address ledger, copy order, payload model,",
        "item-type model, forced rules, book-length ledger, and alpha=1 are fixed.",
        "",
        "## Top Context Models",
        "",
        "| Rank | Model | Family | Total bits | Delta | Component delta | Declaration delta | Contexts |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(models[:12], start=1):
        label = row["model"]
        if "split_book" in row:
            label = f"{label}@{row['split_book']}"
        lines.append(
            f"| `{rank}` | `{label}` | `{row['family']}` | `{row['total_bits']:.3f}` | "
            f"`{row['delta_vs_current_bits']:.3f}` | `{row['component_delta_bits']:.3f}` | "
            f"`{row['declaration_delta_bits']}` | `{row['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The active fixed book-midpoint context remains promoted unless another",
            "declared, decodable context beats it after declaration bits. This is a",
            "mechanical copy-length context audit only; it does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    if promoted:
        lines.extend(["", "## Promoted Formula", "", f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})"])
    write_result("101_post_itemctx_param_copy_length_context_resweep", result, lines)


if __name__ == "__main__":
    main()
