from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

AUDIT_118 = HERE / "scripts" / "118_prequential_generation_model_audit.py"


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


def fixed_counts(
    rows: list[dict[str, Any]],
    *,
    alphabet: list[str],
    context_key: Callable[[dict[str, Any]], Any],
    symbol_key: str,
) -> dict[Any, dict[str, float]]:
    counts: dict[Any, dict[str, float]] = {}
    for row in rows:
        context = context_key(row)
        bucket = counts.setdefault(context, {symbol: 0.0 for symbol in alphabet})
        symbol = row[symbol_key]
        bucket[symbol] = bucket.get(symbol, 0.0) + 1.0
    return counts


def score_fixed_rows(
    rows: list[dict[str, Any]],
    *,
    alpha: float,
    alphabet: list[str],
    context_key: Callable[[dict[str, Any]], Any],
    symbol_key: str,
) -> float:
    counts: dict[Any, dict[str, float]] = {}
    bits = 0.0
    for row in rows:
        context = context_key(row)
        bucket = counts.setdefault(context, {symbol: 0.0 for symbol in alphabet})
        total = sum(bucket.get(symbol, 0.0) for symbol in alphabet)
        symbol = row[symbol_key]
        probability = (bucket.get(symbol, 0.0) + alpha) / (total + len(alphabet) * alpha)
        bits += -math.log2(probability)
        bucket[symbol] = bucket.get(symbol, 0.0) + 1.0
    return bits


def main() -> None:
    audit118 = load_audit_118()
    frontier = audit118.load_module("minaddr_frontier", audit118.FRONTIER)
    midpoint = audit118.load_module("post_midpoint_frontier", audit118.MIDPOINT)
    context_module = audit118.load_module("copy_length_context", audit118.CONTEXT)
    payload_module = audit118.load_module("literal_payload_context", audit118.PAYLOAD_CONTEXT)
    item_module = audit118.load_module("item_type_context", audit118.ITEM_CONTEXT)

    formula = audit118.load_json(audit118.FORMULA)
    books = {str(key): value for key, value in audit118.load_json(audit118.BOOKS_DIGITS).items()}
    active_score = midpoint.score_formula(formula, books, frontier, context_module)
    if active_score["validation"]["errors"]:
        raise RuntimeError(active_score["validation"])
    active_bits = float(formula["mdl_estimate_rough"][audit118.CURRENT_TOTAL_KEY])
    if abs(active_score["total_bits"] - active_bits) > 1e-6:
        raise RuntimeError((active_score["total_bits"], active_bits))

    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    item_model = formula["policy"]["item_type_model"]
    payload_alpha = float(formula["policy"]["literal_payload_model"]["alpha"])
    item_alpha = float(item_model["alpha"])

    active_payload_bits = score_fixed_rows(
        payload_rows,
        alpha=payload_alpha,
        alphabet=audit118.DIGITS,
        context_key=audit118.payload_context_key,
        symbol_key="digit",
    )
    simplified_payload_bits = score_fixed_rows(
        payload_rows,
        alpha=payload_alpha,
        alphabet=audit118.DIGITS,
        context_key=lambda row: ("global", row["previous_digit_context"][-1:]),
        symbol_key="digit",
    )
    active_item_bits = score_fixed_rows(
        item_rows,
        alpha=item_alpha,
        alphabet=audit118.ITEM_TYPES,
        context_key=audit118.item_context_key(item_model),
        symbol_key="item_type",
    )
    simplified_item_bits = score_fixed_rows(
        item_rows,
        alpha=item_alpha,
        alphabet=audit118.ITEM_TYPES,
        context_key=lambda row: (audit118.item_extra_context(item_model, row), ()),
        symbol_key="item_type",
    )
    if abs(active_payload_bits - active_score["literal_payload_bits"]) > 1e-6:
        raise RuntimeError(("payload", active_payload_bits, active_score["literal_payload_bits"]))
    if abs(active_item_bits - active_score["item_type_stream_bits"]) > 1e-6:
        raise RuntimeError(("item", active_item_bits, active_score["item_type_stream_bits"]))

    simplified_profile_bits = (
        active_bits
        - active_payload_bits
        - active_item_bits
        + simplified_payload_bits
        + simplified_item_bits
    )
    component_deltas = {
        "literal_payload_order1_minus_active_order2_bits": simplified_payload_bits - active_payload_bits,
        "item_type_split_only_minus_active_split_prev1_bits": simplified_item_bits - active_item_bits,
    }
    classification = (
        "simplified_generation_profile_costs_more_than_compression_bound"
        if simplified_profile_bits > active_bits
        else "simplified_generation_profile_beats_compression_bound"
    )

    result = {
        "schema": "simplified_generation_profile_compile.v1",
        "test": "122_simplified_generation_profile_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(audit118.FORMULA.relative_to(ROOT)),
        "source_ablation_audit": str((REPORTS / "121_prequential_component_ablation_audit.json").relative_to(ROOT)),
        "validation": active_score["validation"],
        "active_compression_bound_bits": active_bits,
        "simplified_generation_profile_bits": simplified_profile_bits,
        "delta_vs_compression_bound_bits": simplified_profile_bits - active_bits,
        "cost_basis": (
            "Stream-substitution profile using the active validated recipe and "
            "active fixed declaration ledger. This is intentionally not promoted "
            "as a fully re-declared compression formula."
        ),
        "components": {
            "copy_length": {
                "profile": "active_midpoint",
                "bits": active_score["copy_length_code_bits"],
                "reason": "Best online and frozen holdout component in audit 121.",
            },
            "literal_payload": {
                "active_profile": "active_order2",
                "simplified_profile": "order1_previous_digit",
                "active_bits": active_payload_bits,
                "simplified_bits": simplified_payload_bits,
                "delta_bits": component_deltas["literal_payload_order1_minus_active_order2_bits"],
                "reason": "Order-1 wins prefix holdout in audit 121, despite costing more on the full corpus.",
            },
            "item_type": {
                "active_profile": "active_split6_prev1",
                "simplified_profile": "split6_only",
                "active_bits": active_item_bits,
                "simplified_bits": simplified_item_bits,
                "delta_bits": component_deltas["item_type_split_only_minus_active_split_prev1_bits"],
                "reason": "Split-only wins prefix holdout in audit 121, despite costing more on the full corpus.",
            },
        },
        "boundary": {
            "compression_bound_changed": False,
            "generation_explanation_profile_compiled": True,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 122. Simplified Generation Profile Compile",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 121 found that some simpler component contexts predict prefix",
        "holdouts better than the active compression-bound contexts. This compile",
        "measures that simplified generation profile on the full 70-book corpus",
        "while preserving the same recipe and 70/70 roundtrip validation.",
        "",
        "## Result",
        "",
        f"- Active compression bound: `{active_bits:.3f}` bits",
        f"- Simplified generation profile: `{simplified_profile_bits:.3f}` bits",
        f"- Delta vs compression bound: `{simplified_profile_bits - active_bits:.3f}` bits",
        "- Roundtrip: `70/70`",
        "- Cost basis: stream-substitution profile over the active validated",
        "  recipe and fixed declaration ledger; not a promoted re-declared",
        "  compression formula.",
        "",
        "## Component Deltas",
        "",
        "| Component | Active | Simplified profile | Active bits | Simplified bits | Delta |",
        "|---|---|---|---:|---:|---:|",
        (
            "| `literal_payload` | `active_order2` | `order1_previous_digit` | "
            f"`{active_payload_bits:.3f}` | `{simplified_payload_bits:.3f}` | "
            f"`{simplified_payload_bits - active_payload_bits:.3f}` |"
        ),
        (
            "| `item_type` | `active_split6_prev1` | `split6_only` | "
            f"`{active_item_bits:.3f}` | `{simplified_item_bits:.3f}` | "
            f"`{simplified_item_bits - active_item_bits:.3f}` |"
        ),
        "",
        "## Interpretation",
        "",
        "The simplified profile is not promoted as a new lower MDL bound. It costs",
        "more on the full corpus because the active formula is still the best",
        "charged post-hoc code. Its value is explanatory: it records the simpler",
        "component choices that generalize better under prefix holdout.",
        "",
        "## Boundary",
        "",
        "- `compression_bound` remains the active `8561.792` bit formula.",
        "- `generation_explanation_profile` is compiled but not a stronger code.",
        "- No row0/table origin formula is promoted.",
        "- No plaintext, glossary, or authorial-intent claim is introduced.",
    ]

    write_result("122_simplified_generation_profile_compile", result, lines)


if __name__ == "__main__":
    main()
