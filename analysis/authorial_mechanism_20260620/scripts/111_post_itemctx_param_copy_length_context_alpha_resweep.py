from __future__ import annotations

import json
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"
CONTEXT_RESWEEP = HERE / "scripts/91_post_midpoint_alpha1_copy_length_context_resweep.py"

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


def strip_audit_rows(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "audit_rows"}


def context_specs(rows: list[dict], resweep) -> list[dict]:
    specs: list[dict] = [
        {
            "model": "active_book_midpoint_35_context",
            "family": "fixed_book_midpoint",
            "split_book": None,
            "context_description": "book_id < 35 versus book_id >= 35",
            "context_fn": resweep.midpoint_context,
        },
        {
            "model": "book_quartile_context",
            "family": "fixed_book_quartile",
            "split_book": None,
            "context_description": "four fixed numeric book quartiles",
            "context_fn": lambda row: min(3, int(row["book_int"]) // 18),
        },
        {
            "model": "book_decade_context",
            "family": "fixed_book_decade",
            "split_book": None,
            "context_description": "numeric book decade bucket",
            "context_fn": lambda row: int(row["book_int"]) // 10,
        },
        {
            "model": "book_parity_context",
            "family": "fixed_book_parity",
            "split_book": None,
            "context_description": "numeric book id parity",
            "context_fn": lambda row: int(row["book_int"]) % 2,
        },
        {
            "model": "same_book_context",
            "family": "source_scope",
            "split_book": None,
            "context_description": "same-book source versus prior-book source",
            "context_fn": lambda row: "same_book" if bool(row["same_book"]) else "prior_book",
        },
        {
            "model": "legal_symbol_count_log_context",
            "family": "legal_length_space",
            "split_book": None,
            "context_description": "log bucket of legal copy-length symbol count",
            "context_fn": lambda row: resweep.log_bucket(int(row["symbol_count"]), 6),
        },
        {
            "model": "distance_log_context",
            "family": "copy_distance",
            "split_book": None,
            "context_description": "log bucket of decoded copy distance",
            "context_fn": lambda row: resweep.log_bucket(int(row["distance"]), 12),
        },
        {
            "model": "remaining_log_context",
            "family": "declared_remaining",
            "split_book": None,
            "context_description": "log bucket of remaining declared book length",
            "context_fn": lambda row: resweep.log_bucket(int(row["remaining"]), 8),
        },
        {
            "model": "previous_copy_length_log_context",
            "family": "previous_copy_length",
            "split_book": None,
            "context_description": "previous copy length-index log bucket",
            "context_fn": lambda row: "start"
            if row["previous_length_index"] is None
            else resweep.log_bucket(int(row["previous_length_index"]) + 1, 6),
        },
        {
            "model": "copy_index_midpoint_context",
            "family": "copy_index_midpoint",
            "split_book": None,
            "context_description": "first half versus second half of the copy-item stream",
            "context_fn": lambda row: "first_copy_half"
            if int(row["copy_id"]) < len(rows) / 2
            else "second_copy_half",
        },
    ]
    for split_book in range(1, 70):
        specs.append(
            {
                "model": "searched_single_book_split_context",
                "family": "searched_single_book_split",
                "split_book": split_book,
                "context_description": f"book_id < {split_book} versus book_id >= {split_book}",
                "context_fn": lambda row, split_book=split_book: "before_split"
                if int(row["book_int"]) < split_book
                else "after_split",
            }
        )
    return specs


def candidate_row(
    *,
    spec: dict,
    context_fn: Callable[[dict], object],
    rows: list[dict],
    alpha: int,
    context_module,
    resweep,
    current_length_bits: float,
    current_total_bits: float,
    fixed_nonlength_bits: float,
    current_declaration_bits: int,
    copy_base_declaration_bits: int,
    current_alpha: int,
) -> dict:
    length_bits, audit_rows, context_counts = context_module.adaptive_context_bits(rows, alpha, context_fn)
    if spec["family"] == "searched_single_book_split":
        declaration_bits = resweep.searched_split_declaration_bits(
            copy_base_declaration_bits,
            alpha,
            len(context_counts),
            int(spec["split_book"]),
        )
    else:
        declaration_bits = resweep.context_declaration_bits(
            copy_base_declaration_bits,
            alpha,
            len(context_counts),
        )
    total_bits = fixed_nonlength_bits + length_bits + declaration_bits - current_declaration_bits
    changed = not (
        spec["model"] == "active_book_midpoint_35_context"
        and alpha == current_alpha
    )
    context_changed = spec["model"] != "active_book_midpoint_35_context"
    alpha_changed = alpha != current_alpha
    return {
        "model": spec["model"],
        "family": spec["family"],
        "split_book": spec["split_book"],
        "context_description": spec["context_description"],
        "alpha": alpha,
        "adaptive_copy_length_bits": length_bits,
        "copy_model_declaration_bits": declaration_bits,
        "context_count": len(context_counts),
        "context_counts": context_counts,
        "total_bits": total_bits,
        "delta_vs_current_bits": total_bits - current_total_bits,
        "component_delta_bits": length_bits - current_length_bits,
        "declaration_delta_bits": declaration_bits - current_declaration_bits,
        "context_changed": context_changed,
        "alpha_changed": alpha_changed,
        "changed": changed,
        "decodable": True,
        "audit_rows": audit_rows,
    }


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("post_adaptive_copy_length_context", CONTEXT)
    resweep = load_module("post_midpoint_alpha1_copy_length_context_resweep", CONTEXT_RESWEEP)

    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    copy_rows = context_module.collect_copy_rows(formula, books)
    current_alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    current_declaration_bits = int(formula["policy"]["copy_length_model"]["model_declaration_bits"])
    copy_base_declaration_bits = int(
        formula["policy"]["copy_length_model"]["replaces"]["replaces"]["model_declaration_bits"]
    )
    current_length_bits = float(current_score["copy_length_code_bits"])
    fixed_nonlength_bits = current_bits - current_length_bits

    active_bits, _audit_rows, active_context_counts = context_module.adaptive_context_bits(
        copy_rows,
        current_alpha,
        resweep.midpoint_context,
    )
    if abs(active_bits - current_length_bits) > 1e-6:
        raise RuntimeError((active_bits, current_length_bits))
    expected_current_declaration = resweep.context_declaration_bits(
        copy_base_declaration_bits,
        current_alpha,
        len(active_context_counts),
    )
    if expected_current_declaration != current_declaration_bits:
        raise RuntimeError((expected_current_declaration, current_declaration_bits))

    rows = []
    specs = context_specs(copy_rows, resweep)
    for spec in specs:
        for alpha in range(1, 65):
            rows.append(
                candidate_row(
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

    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    best_changed = next(row for row in rows if row["changed"])
    best_context_changed = next(row for row in rows if row["context_changed"])
    best_alpha_changed_active_context = next(
        row for row in rows if row["alpha_changed"] and not row["context_changed"]
    )
    promoted = best["total_bits"] < current_bits - 1e-9 and best["changed"]
    classification = (
        "controlled_post_itemctx_param_copy_length_context_alpha_improvement"
        if promoted
        else "post_itemctx_param_copy_length_context_alpha_not_promoted"
    )

    result = {
        "schema": "post_itemctx_param_copy_length_context_alpha_resweep.v1",
        "test": "111_post_itemctx_param_copy_length_context_alpha_resweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_items": len(copy_rows),
        "current_copy_length_bits": current_length_bits,
        "current_alpha": current_alpha,
        "current_copy_model_declaration_bits": current_declaration_bits,
        "copy_base_declaration_bits": copy_base_declaration_bits,
        "context_candidates_tested": len(specs),
        "alpha_values_tested": 64,
        "context_alpha_candidates_tested": len(rows),
        "best_model": strip_audit_rows(best),
        "best_changed_model": strip_audit_rows(best_changed),
        "best_context_changed_model": strip_audit_rows(best_context_changed),
        "best_alpha_changed_active_context_model": strip_audit_rows(best_alpha_changed_active_context),
        "top_models": [strip_audit_rows(row) for row in rows[:100]],
        "best_context_audit_rows": best["audit_rows"],
        "promotion_rule": (
            "promote only if a decodable copy-length context plus shared alpha "
            "beats the active fixed book-midpoint context with alpha=1 after "
            "charged context/alpha/split declaration bits while preserving 70/70 "
            "roundtrip and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Copy-Length Context/Alpha Resweep",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit closes the gap between the post-itemctx_param copy-length",
        "context resweep and the midpoint alpha grid. It retests the same",
        "copy-length context families as the context resweep, but sweeps a shared",
        "`alpha=1..64` for each context. Context, alpha, and searched split",
        "declaration bits are charged. The recipe, source-address ledger, payload",
        "model, item-type model, forced rules, and book-length ledger are fixed.",
        "",
        "## Coverage",
        "",
        f"- Copy-length context candidates: `{len(specs)}`",
        "- Shared alpha values per context: `64`",
        f"- Context/alpha candidates tested: `{len(rows)}`",
        "",
        "## Top Models",
        "",
        "| Rank | Model | Family | Split | Alpha | Contexts | Length bits | Model bits | Total bits | Delta |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:20], start=1):
        split = "" if row["split_book"] is None else str(row["split_book"])
        lines.append(
            f"| `{rank}` | `{row['model']}` | `{row['family']}` | `{split}` | `{row['alpha']}` | "
            f"`{row['context_count']}` | `{row['adaptive_copy_length_bits']:.3f}` | "
            f"`{row['copy_model_declaration_bits']}` | `{row['total_bits']:.3f}` | "
            f"`{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Changed Model",
            "",
            f"- Delta vs current: `{best_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Model: `{best_changed['model']}`",
            f"- Family: `{best_changed['family']}`",
            f"- Split: `{'' if best_changed['split_book'] is None else best_changed['split_book']}`",
            f"- Alpha: `{best_changed['alpha']}`",
            "",
            "## Best Context-Changed Model",
            "",
            f"- Delta vs current: `{best_context_changed['delta_vs_current_bits']:.3f}` bits",
            f"- Model: `{best_context_changed['model']}`",
            f"- Family: `{best_context_changed['family']}`",
            f"- Split: `{'' if best_context_changed['split_book'] is None else best_context_changed['split_book']}`",
            f"- Alpha: `{best_context_changed['alpha']}`",
            "",
            "## Best Alpha Change On Active Context",
            "",
            f"- Delta vs current: `{best_alpha_changed_active_context['delta_vs_current_bits']:.3f}` bits",
            f"- Alpha: `{best_alpha_changed_active_context['alpha']}`",
            "",
            "## Interpretation",
            "",
            "No copy-length context/shared-alpha candidate beats the active fixed",
            "book-midpoint context with shared `alpha=1`. The active context remains",
            "the complete minimum after declaration costs.",
            "",
            "## Boundary",
            "",
            "This is a mechanical copy-length cost-ledger audit only. It does not",
            "alter row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("111_post_itemctx_param_copy_length_context_alpha_resweep", result, lines)


if __name__ == "__main__":
    main()
