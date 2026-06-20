from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_copy_to_literal_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
SCORER = HERE / "scripts/64_contextual_local_repair_search.py"
CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_copy_to_literal_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_scorer():
    spec = importlib.util.spec_from_file_location("contextual_scorer", SCORER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scorer: {SCORER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def payload_declaration_bits(alpha: int, order: int) -> int:
    return gamma_bits(alpha + 1) + 3 + (0 if order == 1 else gamma_bits(order))


def item_type_declaration_bits(alpha: int, order: int, forced_rule_bits: int) -> int:
    return gamma_bits(alpha + 1) + forced_rule_bits + (0 if order == 1 else 1 + gamma_bits(order))


def clone_formula(formula: dict) -> dict:
    return copy.deepcopy(formula)


def main() -> None:
    scorer = load_scorer()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = scorer.score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    fixed_bits = float(formula["mdl_estimate_rough"]["fixed_bits"])
    current_copy_decl = int(formula["mdl_estimate_rough"]["copy_model_declaration_bits"])
    current_literal_decl = int(formula["mdl_estimate_rough"]["literal_model_declaration_bits"])
    current_payload_decl = int(formula["policy"]["literal_payload_model"]["model_declaration_bits"])
    current_item_decl = int(formula["policy"]["item_type_model"]["model_declaration_bits"])
    forced_rule_bits = int(formula["policy"]["item_type_model"]["forced_rule_bits"])

    rows = []
    for copy_k in range(0, 11):
        candidate = clone_formula(formula)
        candidate["policy"]["copy_length_model"]["k"] = copy_k
        candidate["mdl_estimate_rough"]["fixed_bits"] = fixed_bits - current_copy_decl + gamma_bits(copy_k + 1)
        score = scorer.score_formula(candidate, books)
        rows.append(
            {
                "family": "copy_length_rice_k",
                "parameter": copy_k,
                "total_bits": score["total_bits"],
                "delta_vs_current_bits": score["total_bits"] - current_bits,
                "component_bits": score["copy_length_code_bits"],
                "model_declaration_bits": gamma_bits(copy_k + 1),
            }
        )

    for literal_k in range(0, 11):
        candidate = clone_formula(formula)
        candidate["policy"]["literal_run_length_model"]["k"] = literal_k
        candidate["mdl_estimate_rough"]["fixed_bits"] = fixed_bits - current_literal_decl + gamma_bits(literal_k + 1)
        score = scorer.score_formula(candidate, books)
        rows.append(
            {
                "family": "literal_run_length_rice_k",
                "parameter": literal_k,
                "total_bits": score["total_bits"],
                "delta_vs_current_bits": score["total_bits"] - current_bits,
                "component_bits": score["literal_bits_no_payload"],
                "model_declaration_bits": gamma_bits(literal_k + 1),
            }
        )

    for order in range(1, 7):
        for alpha in range(1, 33):
            declaration_bits = payload_declaration_bits(alpha, order)
            candidate = clone_formula(formula)
            candidate["policy"]["literal_payload_model"]["order"] = order
            candidate["policy"]["literal_payload_model"]["alpha"] = alpha
            candidate["policy"]["literal_payload_model"]["model_declaration_bits"] = declaration_bits
            candidate["mdl_estimate_rough"]["fixed_bits"] = fixed_bits - current_payload_decl + declaration_bits
            score = scorer.score_formula(candidate, books)
            rows.append(
                {
                    "family": "literal_payload_context_order_alpha",
                    "parameter": {"order": order, "alpha": alpha},
                    "total_bits": score["total_bits"],
                    "delta_vs_current_bits": score["total_bits"] - current_bits,
                    "component_bits": score["literal_payload_bits"],
                    "model_declaration_bits": declaration_bits,
                }
            )

    for order in range(1, 8):
        for alpha in range(1, 33):
            declaration_bits = item_type_declaration_bits(alpha, order, forced_rule_bits)
            candidate = clone_formula(formula)
            candidate["policy"]["item_type_model"]["order"] = order
            candidate["policy"]["item_type_model"]["alpha"] = alpha
            candidate["policy"]["item_type_model"]["model_declaration_bits"] = declaration_bits
            candidate["mdl_estimate_rough"]["fixed_bits"] = fixed_bits - current_item_decl + declaration_bits
            score = scorer.score_formula(candidate, books)
            rows.append(
                {
                    "family": "item_type_context_order_alpha",
                    "parameter": {"order": order, "alpha": alpha},
                    "total_bits": score["total_bits"],
                    "delta_vs_current_bits": score["total_bits"] - current_bits,
                    "component_bits": score["item_type_stream_bits"],
                    "model_declaration_bits": declaration_bits,
                }
            )

    rows.sort(key=lambda row: row["total_bits"])
    best_by_family = {}
    for row in rows:
        best_by_family.setdefault(row["family"], row)
    best = rows[0]
    classification = (
        "post_contextual_parameter_resweep_candidate"
        if best["total_bits"] < current_bits - 1e-9
        else "post_contextual_parameter_resweep_retains_current"
    )

    result = {
        "schema": "post_contextual_parameter_resweep.v1",
        "test": "68_post_contextual_parameter_resweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "best_model": best,
        "best_by_family": best_by_family,
        "models": rows,
        "promotion_rule": (
            "promote only if a declared parameter value for copy length, literal length, "
            "literal payload context, or item-type context beats the active contextual formula"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Contextual Parameter Resweep",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests declared parameters after the contextual copy-to-literal",
        "repair changed the recipe. It keeps the recipe fixed and sweeps copy",
        "length Rice `k`, literal-run length Rice `k`, literal-payload context",
        "order/alpha, and item-type context order/alpha.",
        "",
        "## Best By Family",
        "",
        "| Family | Parameter | Total bits | Delta vs current | Component bits | Model bits |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for family in sorted(best_by_family):
        row = best_by_family[family]
        lines.append(
            f"| `{family}` | `{row['parameter']}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_current_bits']:.1f}` | `{row['component_bits']:.1f}` | "
            f"`{row['model_declaration_bits']}` |"
        )
    lines.extend(
        [
            "",
            "## Top Candidates",
            "",
            "| Rank | Family | Parameter | Total bits | Delta vs current |",
            "|---:|---|---|---:|---:|",
        ]
    )
    for rank, row in enumerate(rows[:20], start=1):
        lines.append(
            f"| `{rank}` | `{row['family']}` | `{row['parameter']}` | "
            f"`{row['total_bits']:.1f}` | `{row['delta_vs_current_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The current parameters remain active if every family minimum is at or",
            "above the current formula cost. This is a mechanical parameter audit",
            "only; it does not introduce plaintext, row0 meaning, or authorial",
            "intent.",
        ]
    )
    write_result("68_post_contextual_parameter_resweep", result, lines)


if __name__ == "__main__":
    main()
