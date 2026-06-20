from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha_by_context_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha_by_context_minaddr_repair2_bits"


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


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def midpoint_context(row: dict) -> str:
    return "first_half" if int(row["book_int"]) < 35 else "second_half"


def shared_alpha_declaration_bits(base_declaration_bits: int, alpha: int, context_count: int) -> int:
    return base_declaration_bits + gamma_bits(alpha + 1) + 1 + gamma_bits(context_count + 1)


def alpha_by_context_declaration_bits(base_declaration_bits: int, alpha_by_context: dict[str, int]) -> int:
    return (
        base_declaration_bits
        + 1
        + gamma_bits(len(alpha_by_context) + 1)
        + sum(gamma_bits(alpha + 1) for alpha in alpha_by_context.values())
    )


def midpoint_length_bits_with_alpha_by_context(
    rows: list[dict],
    alpha_by_context: dict[str, int],
) -> tuple[float, list[dict], dict[str, int]]:
    context_counts: dict[str, dict[int, int]] = {}
    context_totals: dict[str, int] = {}
    total_bits = 0.0
    audit_rows = []

    for row in rows:
        context = midpoint_context(row)
        alpha = int(alpha_by_context[context])
        counts = context_counts.setdefault(context, {})
        symbol_count = int(row["symbol_count"])
        length_index = int(row["length_index"])
        legal_observations = sum(counts.get(index, 0) for index in range(symbol_count))
        denominator = legal_observations + alpha * symbol_count
        numerator = counts.get(length_index, 0) + alpha
        bits = -math.log2(numerator / denominator)
        total_bits += bits
        context_totals[context] = context_totals.get(context, 0) + 1
        audit_rows.append(
            {
                **row,
                "context": context,
                "alpha": alpha,
                "adaptive_context_bits": bits,
                "previous_context_legal_observations": legal_observations,
                "previous_context_same_length_observations": counts.get(length_index, 0),
            }
        )
        counts[length_index] = counts.get(length_index, 0) + 1

    return total_bits, audit_rows, context_totals


def strip_audit_rows(row: dict) -> dict:
    return {key: value for key, value in row.items() if key != "audit_rows"}


def main() -> None:
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_search = load_module("post_adaptive_copy_length_context", CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_search)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    rows = context_search.collect_copy_rows(formula, books)
    current_alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    current_declaration_bits = int(formula["policy"]["copy_length_model"]["model_declaration_bits"])
    copy_base_declaration_bits = int(
        formula["policy"]["copy_length_model"]["replaces"]["replaces"]["model_declaration_bits"]
    )
    current_length_bits = float(current_score["copy_length_code_bits"])
    fixed_nonlength_bits = current_bits - current_length_bits

    active_alpha_by_context = {"first_half": current_alpha, "second_half": current_alpha}
    active_bits, active_audit_rows, context_counts = midpoint_length_bits_with_alpha_by_context(
        rows,
        active_alpha_by_context,
    )
    if abs(active_bits - current_length_bits) > 1e-6:
        raise RuntimeError((active_bits, current_length_bits))
    expected_current_declaration = shared_alpha_declaration_bits(
        copy_base_declaration_bits,
        current_alpha,
        len(active_alpha_by_context),
    )
    if expected_current_declaration != current_declaration_bits:
        raise RuntimeError((expected_current_declaration, current_declaration_bits))

    models = [
        {
            "model": "active_shared_alpha1_midpoint_context",
            "family": "shared_alpha",
            "alpha_by_context": active_alpha_by_context,
            "adaptive_copy_length_bits": active_bits,
            "copy_model_declaration_bits": current_declaration_bits,
            "context_counts": context_counts,
            "total_bits": current_bits,
            "delta_vs_current_bits": 0.0,
            "component_delta_bits": 0.0,
            "declaration_delta_bits": 0,
            "decodable": True,
            "audit_rows": active_audit_rows,
        }
    ]

    for first_alpha in range(1, 65):
        for second_alpha in range(1, 65):
            alpha_by_context = {
                "first_half": first_alpha,
                "second_half": second_alpha,
            }
            length_bits, audit_rows, counts = midpoint_length_bits_with_alpha_by_context(
                rows,
                alpha_by_context,
            )
            declaration_bits = alpha_by_context_declaration_bits(copy_base_declaration_bits, alpha_by_context)
            total_bits = fixed_nonlength_bits + length_bits + declaration_bits - current_declaration_bits
            models.append(
                {
                    "model": "midpoint_alpha_by_context_grid",
                    "family": "alpha_by_context",
                    "alpha_by_context": alpha_by_context,
                    "adaptive_copy_length_bits": length_bits,
                    "copy_model_declaration_bits": declaration_bits,
                    "context_counts": counts,
                    "total_bits": total_bits,
                    "delta_vs_current_bits": total_bits - current_bits,
                    "component_delta_bits": length_bits - current_length_bits,
                    "declaration_delta_bits": declaration_bits - current_declaration_bits,
                    "decodable": True,
                    "audit_rows": audit_rows,
                }
            )

    models.sort(key=lambda row: row["total_bits"])
    best_decodable = next(row for row in models if row["decodable"])
    promoted = (
        best_decodable["model"] != "active_shared_alpha1_midpoint_context"
        and best_decodable["total_bits"] < current_bits - 1e-9
    )
    classification = (
        "controlled_post_midpoint_alpha_by_context_improvement"
        if promoted
        else "post_midpoint_alpha_by_context_not_promoted"
    )

    if promoted:
        out = copy.deepcopy(formula)
        out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha_by_context_minaddr_repair2_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["copy_length_model"] = {
            **out["policy"]["copy_length_model"],
            "alpha": None,
            "alpha_by_context": best_decodable["alpha_by_context"],
            "model_declaration_bits": int(best_decodable["copy_model_declaration_bits"]),
        }
        out["policy"]["cost_model"] = out["policy"]["cost_model"] + "+midpoint_alpha_by_context"
        out["mdl_estimate_rough"] = {
            **out["mdl_estimate_rough"],
            OUT_TOTAL_KEY: best_decodable["total_bits"],
            "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_bits": current_bits,
            "gain_vs_previous_midpoint_alpha1_bits": current_bits - best_decodable["total_bits"],
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
            "post_midpoint_alpha_by_context_roundtrip_audit": current_score["validation"],
            "post_midpoint_alpha_by_context_copy_items": len(rows),
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    best_grid = next(row for row in models if row["family"] == "alpha_by_context")
    result = {
        "schema": "post_midpoint_alpha1_context_alpha_grid.v1",
        "test": "92_post_midpoint_alpha1_context_alpha_grid",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_items": len(rows),
        "current_alpha": current_alpha,
        "current_copy_length_bits": current_length_bits,
        "current_copy_model_declaration_bits": current_declaration_bits,
        "copy_base_declaration_bits": copy_base_declaration_bits,
        "best_model": strip_audit_rows(best_decodable),
        "best_alpha_by_context_model": strip_audit_rows(best_grid),
        "models": [strip_audit_rows(row) for row in models],
        "best_context_audit_rows": best_decodable["audit_rows"],
        "promotion_rule": (
            "promote only if context-specific midpoint alphas beat the active shared "
            "alpha=1 midpoint context after charged declaration bits, with 70/70 "
            "roundtrip and translation_delta NONE"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Midpoint Alpha1 Context Alpha Grid",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether the fixed book-midpoint copy-length context",
        "needs separate smoothing parameters for `first_half` and `second_half`.",
        "The recipe, source-address ledger, copy order, payload model, item-type",
        "model, forced rules, book-length ledger, and midpoint context are fixed.",
        "",
        "## Top Alpha Models",
        "",
        "| Rank | Model | First alpha | Second alpha | Length bits | Model bits | Total bits | Delta vs current | Component delta |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(models[:20], start=1):
        alphas = row["alpha_by_context"]
        lines.append(
            f"| `{rank}` | `{row['model']}` | `{alphas['first_half']}` | `{alphas['second_half']}` | "
            f"`{row['adaptive_copy_length_bits']:.3f}` | `{row['copy_model_declaration_bits']}` | "
            f"`{row['total_bits']:.3f}` | `{row['delta_vs_current_bits']:.3f}` | "
            f"`{row['component_delta_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Best Context-Specific Alpha Row",
            "",
            f"- First-half alpha: `{best_grid['alpha_by_context']['first_half']}`",
            f"- Second-half alpha: `{best_grid['alpha_by_context']['second_half']}`",
            f"- Total bits: `{best_grid['total_bits']:.3f}`",
            f"- Delta vs current: `{best_grid['delta_vs_current_bits']:.3f}`",
            f"- Component delta: `{best_grid['component_delta_bits']:.3f}`",
            f"- Declaration delta: `{best_grid['declaration_delta_bits']}`",
            "",
            "## Interpretation",
            "",
            "Context-specific alphas are promoted only if their component savings",
            "survive the extra declaration cost. Otherwise the active shared",
            "`alpha=1` midpoint context remains the current formula.",
            "",
            "## Boundary",
            "",
            "This is a mechanical smoothing-parameter audit only. It does not alter",
            "row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    if promoted:
        lines.extend(
            [
                "",
                "## Promoted Formula",
                "",
                f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
            ]
        )
    write_result("92_post_midpoint_alpha1_context_alpha_grid", result, lines)


if __name__ == "__main__":
    main()
