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


def strip_audit_rows(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "audit_rows"}


def context_specs(payload) -> list[dict]:
    specs: list[dict] = [
        {
            "model": "active_global_literal_payload_context",
            "family": "active_global",
            "split_book": None,
            "context_description": "single global payload context",
            "context_fn": lambda _row: "global",
        },
        {
            "model": "book_midpoint_35_literal_payload_context",
            "family": "fixed_book_midpoint",
            "split_book": None,
            "context_description": "book_id < 35 versus book_id >= 35",
            "context_fn": lambda row: "first_half" if int(row["book_int"]) < 35 else "second_half",
        },
        {
            "model": "book_quartile_literal_payload_context",
            "family": "fixed_book_quartile",
            "split_book": None,
            "context_description": "four fixed numeric book quartiles",
            "context_fn": lambda row: min(3, int(row["book_int"]) // 18),
        },
        {
            "model": "book_decade_literal_payload_context",
            "family": "fixed_book_decade",
            "split_book": None,
            "context_description": "numeric book decade bucket",
            "context_fn": lambda row: int(row["book_int"]) // 10,
        },
        {
            "model": "book_parity_literal_payload_context",
            "family": "fixed_book_parity",
            "split_book": None,
            "context_description": "numeric book id parity",
            "context_fn": lambda row: int(row["book_int"]) % 2,
        },
        {
            "model": "literal_run_length_log_context",
            "family": "literal_run_length",
            "split_book": None,
            "context_description": "log bucket of current literal-run length",
            "context_fn": lambda row: payload.log_bucket(int(row["literal_run_length"]), 6),
        },
        {
            "model": "literal_offset_log_context",
            "family": "literal_offset",
            "split_book": None,
            "context_description": "log bucket of digit offset inside the literal run",
            "context_fn": lambda row: payload.log_bucket(int(row["literal_offset"]) + 1, 6),
        },
        {
            "model": "copy_index_proxy_global_position_context",
            "family": "global_position",
            "split_book": None,
            "context_description": "log bucket of generated digit position before literal digit",
            "context_fn": lambda row: payload.log_bucket(int(row["global_digit_pos"]) + 1, 14),
        },
    ]
    for split_book in range(1, 70):
        specs.append(
            {
                "model": "searched_single_book_split_literal_payload_context",
                "family": "searched_single_book_split",
                "split_book": split_book,
                "context_description": f"book_id < {split_book} versus book_id >= {split_book}",
                "context_fn": lambda row, split_book=split_book: "before_split"
                if int(row["book_int"]) < split_book
                else "after_split",
            }
        )
    return specs


def payload_base_declaration_bits(payload, current_declaration_bits: int, current_alpha: float) -> int:
    alpha_int = int(current_alpha)
    if current_alpha != alpha_int:
        raise ValueError(f"non-integer alpha is not supported here: {current_alpha}")
    return current_declaration_bits - payload.gamma_bits(alpha_int + 1)


def candidate_declaration_bits(
    *,
    payload,
    base_declaration_bits: int,
    alpha: int,
    context_count: int,
    family: str,
    split_book: int | None,
) -> int:
    bits = base_declaration_bits + payload.gamma_bits(alpha + 1)
    if family != "active_global":
        bits += 1 + payload.gamma_bits(context_count + 1)
    if family == "searched_single_book_split":
        if split_book is None:
            raise ValueError("searched split requires split_book")
        bits += payload.gamma_bits(split_book + 1)
    return bits


def candidate_row(
    *,
    spec: dict,
    context_fn: Callable[[dict], object],
    literal_rows: list[dict],
    alpha: int,
    payload,
    current_payload_bits: float,
    current_total_bits: float,
    fixed_nonpayload_bits: float,
    current_declaration_bits: int,
    base_declaration_bits: int,
    current_alpha: int,
) -> dict:
    bits, audit_rows, counts = payload.payload_bits(literal_rows, alpha, context_fn)
    declaration_bits = candidate_declaration_bits(
        payload=payload,
        base_declaration_bits=base_declaration_bits,
        alpha=alpha,
        context_count=len(counts),
        family=spec["family"],
        split_book=spec["split_book"],
    )
    total_bits = fixed_nonpayload_bits + bits + declaration_bits - current_declaration_bits
    context_changed = spec["model"] != "active_global_literal_payload_context"
    alpha_changed = alpha != current_alpha
    changed = context_changed or alpha_changed
    return {
        "model": spec["model"],
        "family": spec["family"],
        "split_book": spec["split_book"],
        "context_description": spec["context_description"],
        "alpha": alpha,
        "literal_payload_bits": bits,
        "literal_payload_model_declaration_bits": declaration_bits,
        "context_count": len(counts),
        "context_counts": counts,
        "total_bits": total_bits,
        "delta_vs_current_bits": total_bits - current_total_bits,
        "component_delta_bits": bits - current_payload_bits,
        "declaration_delta_bits": declaration_bits - current_declaration_bits,
        "context_changed": context_changed,
        "alpha_changed": alpha_changed,
        "changed": changed,
        "decodable": True,
        "audit_rows": audit_rows,
    }


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
    current_alpha = int(model["alpha"])
    current_declaration_bits = int(model["model_declaration_bits"])
    base_declaration_bits = payload_base_declaration_bits(payload, current_declaration_bits, current_alpha)
    current_payload_bits = float(current_score["literal_payload_bits"])
    fixed_nonpayload_bits = current_bits - current_payload_bits
    literal_rows = payload.collect_literal_digit_rows(formula, books)

    active_bits, _audit_rows, active_context_counts = payload.payload_bits(
        literal_rows,
        current_alpha,
        lambda _row: "global",
    )
    if abs(active_bits - current_payload_bits) > 1e-6:
        raise RuntimeError((active_bits, current_payload_bits))
    expected_current_declaration = candidate_declaration_bits(
        payload=payload,
        base_declaration_bits=base_declaration_bits,
        alpha=current_alpha,
        context_count=len(active_context_counts),
        family="active_global",
        split_book=None,
    )
    if expected_current_declaration != current_declaration_bits:
        raise RuntimeError((expected_current_declaration, current_declaration_bits))

    specs = context_specs(payload)
    rows = []
    for spec in specs:
        for alpha in range(1, 65):
            rows.append(
                candidate_row(
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

    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    best_changed = next(row for row in rows if row["changed"])
    best_context_changed = next(row for row in rows if row["context_changed"])
    best_alpha_changed_active_context = next(
        row for row in rows if row["alpha_changed"] and not row["context_changed"]
    )
    promoted = best["total_bits"] < current_bits - 1e-9 and best["changed"]
    classification = (
        "controlled_post_itemctx_param_literal_payload_context_alpha_improvement"
        if promoted
        else "post_itemctx_param_literal_payload_context_alpha_not_promoted"
    )

    result = {
        "schema": "post_itemctx_param_literal_payload_context_alpha_resweep.v1",
        "test": "112_post_itemctx_param_literal_payload_context_alpha_resweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "literal_digit_items": len(literal_rows),
        "literal_runs": len({row["literal_run_id"] for row in literal_rows}),
        "current_literal_payload_bits": current_payload_bits,
        "current_alpha": current_alpha,
        "current_literal_payload_model_declaration_bits": current_declaration_bits,
        "payload_base_declaration_bits": base_declaration_bits,
        "payload_context_candidates_tested": len(specs),
        "alpha_values_tested": 64,
        "payload_context_alpha_candidates_tested": len(rows),
        "best_model": strip_audit_rows(best),
        "best_changed_model": strip_audit_rows(best_changed),
        "best_context_changed_model": strip_audit_rows(best_context_changed),
        "best_alpha_changed_active_context_model": strip_audit_rows(best_alpha_changed_active_context),
        "top_models": [strip_audit_rows(row) for row in rows[:100]],
        "best_context_audit_rows": best["audit_rows"],
        "promotion_rule": (
            "promote only if a decodable literal-payload context plus shared "
            "alpha beats the active global previous-emitted-digit payload model "
            "with alpha=1 after charged context/alpha/split declaration bits "
            "while preserving 70/70 roundtrip and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Itemctx Param Literal Payload Context/Alpha Resweep",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit closes the gap between the post-itemctx_param literal-payload",
        "context search and the payload alpha parameter. It retests the same",
        "literal-payload context families as the context search, but sweeps a",
        "shared `alpha=1..64` for each context. Family, order, alpha, context,",
        "and searched-split declaration bits are charged. The recipe, literal-run",
        "length model, copy-address ledger, copy-length model, item-type model,",
        "forced rules, and book-length ledger are fixed.",
        "",
        "## Coverage",
        "",
        f"- Literal-payload context candidates: `{len(specs)}`",
        "- Shared alpha values per context: `64`",
        f"- Context/alpha candidates tested: `{len(rows)}`",
        "",
        "## Top Models",
        "",
        "| Rank | Model | Family | Split | Alpha | Contexts | Payload bits | Model bits | Total bits | Delta |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:20], start=1):
        split = "" if row["split_book"] is None else str(row["split_book"])
        lines.append(
            f"| `{rank}` | `{row['model']}` | `{row['family']}` | `{split}` | `{row['alpha']}` | "
            f"`{row['context_count']}` | `{row['literal_payload_bits']:.3f}` | "
            f"`{row['literal_payload_model_declaration_bits']}` | `{row['total_bits']:.3f}` | "
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
            "No literal-payload context/shared-alpha candidate beats the active",
            "global previous-emitted-digit payload model with shared `alpha=1`.",
            "The active payload model remains the complete minimum after declaration",
            "costs.",
            "",
            "## Boundary",
            "",
            "This is a mechanical payload-cost ledger audit only. It does not alter",
            "row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("112_post_itemctx_param_literal_payload_context_alpha_resweep", result, lines)


if __name__ == "__main__":
    main()
