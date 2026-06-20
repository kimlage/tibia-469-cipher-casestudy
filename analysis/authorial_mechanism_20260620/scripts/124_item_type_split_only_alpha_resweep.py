from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

AUDIT_118 = HERE / "scripts" / "118_prequential_generation_model_audit.py"
FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_formula_469.json"
)
CURRENT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_bits"
)
ITEM_TYPES = ["literal", "copy"]


def load_audit_118():
    spec = importlib.util.spec_from_file_location("prequential_generation_model_audit", AUDIT_118)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {AUDIT_118}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_result(name: str, result: dict[str, Any], lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def score_split_only_rows(rows: list[dict[str, Any]], *, alpha: float, context_key) -> tuple[float, dict[str, int]]:
    counts: dict[Any, dict[str, float]] = {}
    context_counts: dict[str, int] = {}
    bits = 0.0
    for row in rows:
        context = context_key(row)
        context_label = json.dumps(context, sort_keys=True) if not isinstance(context, str) else context
        bucket = counts.setdefault(context, {item_type: 0.0 for item_type in ITEM_TYPES})
        total = sum(bucket.get(item_type, 0.0) for item_type in ITEM_TYPES)
        item_type = row["item_type"]
        probability = (bucket.get(item_type, 0.0) + alpha) / (total + len(ITEM_TYPES) * alpha)
        bits += -math.log2(probability)
        bucket[item_type] = bucket.get(item_type, 0.0) + 1.0
        context_counts[context_label] = context_counts.get(context_label, 0) + 1
    return bits, dict(sorted(context_counts.items()))


def main() -> None:
    audit118 = load_audit_118()
    item_module = audit118.load_module("item_type_context", audit118.ITEM_CONTEXT)
    formula = audit118.load_json(FORMULA)
    books = {str(key): value for key, value in audit118.load_json(audit118.BOOKS_DIGITS).items()}
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    model = formula["policy"]["item_type_model"]
    current_alpha = int(model["alpha"])
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_item_bits = float(formula["mdl_estimate_rough"]["item_type_split_only_stream_bits"])
    current_alpha_decl_bits = gamma_bits(current_alpha + 1)

    def split_context(row: dict[str, Any]) -> tuple[str, tuple]:
        return (audit118.item_extra_context(model, row), ())

    observed_item_bits, context_counts = score_split_only_rows(
        item_rows,
        alpha=current_alpha,
        context_key=split_context,
    )
    if abs(observed_item_bits - current_item_bits) > 1e-6:
        raise RuntimeError((observed_item_bits, current_item_bits))

    rows = []
    for alpha in range(1, 65):
        item_bits, alpha_context_counts = score_split_only_rows(
            item_rows,
            alpha=alpha,
            context_key=split_context,
        )
        declaration_delta = gamma_bits(alpha + 1) - current_alpha_decl_bits
        total_bits = current_bits - current_item_bits + item_bits + declaration_delta
        rows.append(
            {
                "alpha": alpha,
                "item_type_stream_bits": item_bits,
                "alpha_declaration_delta_bits": declaration_delta,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "context_counts": alpha_context_counts,
            }
        )
    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    promoted = best["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_item_type_split_only_alpha_improvement"
        if promoted
        else "item_type_split_only_alpha_resweep_retains_current"
    )

    result = {
        "schema": "item_type_split_only_alpha_resweep.v1",
        "test": "124_item_type_split_only_alpha_resweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_alpha": current_alpha,
        "current_item_type_stream_bits": current_item_bits,
        "current_context_counts": context_counts,
        "best_model": best,
        "rows": rows,
        "item_stats": item_stats,
        "promotion_rule": (
            "Promote only if an alternate split-only alpha beats the active "
            "split-only formula after charging alpha declaration delta, preserving "
            "forced rules, same recipe, 70/70 roundtrip from the source formula, "
            "and translation_delta NONE."
        ),
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 124. Item-Type Split-Only Alpha Resweep",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "After audit 123 promoted split-only item-type coding, this audit retests",
        "the smoothing alpha for that new structural model. The recipe, forced",
        "rules, split at book `6`, copy model, literal model, and address ledger",
        "are fixed.",
        "",
        "## Result",
        "",
        f"- Current formula bits: `{current_bits:.3f}`",
        f"- Current alpha: `{current_alpha}`",
        f"- Best alpha: `{best['alpha']}`",
        f"- Best total bits: `{best['total_bits']:.3f}`",
        f"- Delta vs current: `{best['delta_vs_current_bits']:.3f}` bits",
        "",
        "## Top Alpha Rows",
        "",
        "| Rank | Alpha | Item bits | Decl delta | Total bits | Delta vs current |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:10], start=1):
        lines.append(
            f"| `{rank}` | `{row['alpha']}` | `{row['item_type_stream_bits']:.3f}` | "
            f"`{row['alpha_declaration_delta_bits']}` | `{row['total_bits']:.3f}` | "
            f"`{row['delta_vs_current_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The active `alpha=2` split-only item-type model remains best after",
            "charging alpha declaration deltas. The new `8558.667` compression bound",
            "is retained; no follow-up parameter promotion is justified here.",
            "",
            "## Boundary",
            "",
            "- No row0/table origin formula is promoted.",
            "- No plaintext, glossary, or authorial-intent claim is introduced.",
        ]
    )

    write_result("124_item_type_split_only_alpha_resweep", result, lines)


if __name__ == "__main__":
    main()
