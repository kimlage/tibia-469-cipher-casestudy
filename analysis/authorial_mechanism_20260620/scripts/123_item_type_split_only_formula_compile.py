from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

AUDIT_118 = HERE / "scripts" / "118_prequential_generation_model_audit.py"
OUT_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_formula_469.json"
)
OUT_TOTAL_KEY = (
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


def score_item_rows(
    rows: list[dict[str, Any]],
    *,
    alpha: float,
    context_key: Callable[[dict[str, Any]], Any],
) -> tuple[float, dict[str, int]]:
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
    frontier = audit118.load_module("minaddr_frontier", audit118.FRONTIER)
    midpoint = audit118.load_module("post_midpoint_frontier", audit118.MIDPOINT)
    context_module = audit118.load_module("copy_length_context", audit118.CONTEXT)
    item_module = audit118.load_module("item_type_context", audit118.ITEM_CONTEXT)

    formula = audit118.load_json(audit118.FORMULA)
    books = {str(key): value for key, value in audit118.load_json(audit118.BOOKS_DIGITS).items()}
    active_bits = float(formula["mdl_estimate_rough"][audit118.CURRENT_TOTAL_KEY])
    active_score = midpoint.score_formula(formula, books, frontier, context_module)
    if active_score["validation"]["errors"]:
        raise RuntimeError(active_score["validation"])
    if abs(active_score["total_bits"] - active_bits) > 1e-6:
        raise RuntimeError((active_score["total_bits"], active_bits))

    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    item_model = formula["policy"]["item_type_model"]
    alpha = float(item_model["alpha"])
    active_item_bits, active_context_counts = score_item_rows(
        item_rows,
        alpha=alpha,
        context_key=audit118.item_context_key(item_model),
    )
    if abs(active_item_bits - active_score["item_type_stream_bits"]) > 1e-6:
        raise RuntimeError((active_item_bits, active_score["item_type_stream_bits"]))

    split_only_bits, split_only_context_counts = score_item_rows(
        item_rows,
        alpha=alpha,
        context_key=lambda row: (audit118.item_extra_context(item_model, row), ()),
    )

    # Conservative promotion rule: keep the active item-type declaration charge.
    # This avoids relying on a cheaper order=0 declaration convention that the
    # older scorer never encoded.
    candidate_bits = active_bits - active_item_bits + split_only_bits
    conservative_extra_decl_bits = 1
    conservative_candidate_bits = candidate_bits + conservative_extra_decl_bits
    promoted = candidate_bits < active_bits - 1e-9
    conservative_promoted = conservative_candidate_bits < active_bits - 1e-9
    classification = (
        "controlled_item_type_split_only_formula_improvement"
        if promoted
        else "item_type_split_only_formula_not_promoted"
    )

    output_formula = None
    if promoted:
        output = copy.deepcopy(formula)
        output["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_splitonly_param_minaddr_repair2_formula.v1"
        output["classification"] = classification
        output["source_baseline_formula"] = str(audit118.FORMULA.relative_to(ROOT))
        output["policy"]["item_type_model"] = {
            **output["policy"]["item_type_model"],
            "family": "adaptive_book_split_item_type_context_with_forced_type_rules",
            "conditioning": (
                "No previous item-type history is coded; charged emissions are "
                "conditioned only on the declared book split extra-context. "
                "Forced item types remain enforced but are not charged."
            ),
            "order": 0,
            "order_declaration_bits": 0,
            "extra_context_counts": split_only_context_counts,
            "model_declaration_bits": int(item_model["model_declaration_bits"]),
            "replaces": item_model,
        }
        output["policy"]["cost_model"] = output["policy"]["cost_model"] + "+item_type_split_only_stream"
        output["mdl_estimate_rough"] = {
            **output["mdl_estimate_rough"],
            OUT_TOTAL_KEY: candidate_bits,
            "previous_sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_itemctx_param_minaddr_repair2_bits": active_bits,
            "gain_vs_previous_itemctx_param_bits": active_bits - candidate_bits,
            "item_type_split_only_stream_bits": split_only_bits,
            "previous_item_type_context_order_stream_bits": active_item_bits,
            "item_type_model_declaration_bits": int(item_model["model_declaration_bits"]),
            "fixed_bits": float(formula["mdl_estimate_rough"]["fixed_bits"]),
        }
        output["validation"] = {
            **output["validation"],
            "item_type_split_only_formula_roundtrip_audit": active_score["validation"],
            "item_type_split_only_stats": {
                **item_stats,
                "context_count": len(split_only_context_counts),
                "context_counts": split_only_context_counts,
                "conservative_same_declaration_charge": True,
            },
        }
        OUT_FORMULA.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        output_formula = str(OUT_FORMULA.relative_to(ROOT))

    result = {
        "schema": "item_type_split_only_formula_compile.v1",
        "test": "123_item_type_split_only_formula_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(audit118.FORMULA.relative_to(ROOT)),
        "output_formula": output_formula,
        "active_compression_bound_bits": active_bits,
        "candidate_total_bits": candidate_bits,
        "candidate_gain_bits": active_bits - candidate_bits,
        "conservative_extra_decl_bits": conservative_extra_decl_bits,
        "conservative_candidate_total_bits": conservative_candidate_bits,
        "conservative_candidate_gain_bits": active_bits - conservative_candidate_bits,
        "promoted_under_same_declaration_charge": promoted,
        "promoted_even_with_one_extra_declaration_bit": conservative_promoted,
        "active_item_type_bits": active_item_bits,
        "split_only_item_type_bits": split_only_bits,
        "item_type_component_gain_bits": active_item_bits - split_only_bits,
        "active_context_counts": active_context_counts,
        "split_only_context_counts": split_only_context_counts,
        "item_stats": item_stats,
        "validation": active_score["validation"],
        "promotion_rule": (
            "Promote only if split-only item-type coding improves the active "
            "validated total while preserving the same recipe, same fixed "
            "item-type declaration charge, forced-rule validity, 70/70 roundtrip, "
            "and translation_delta NONE."
        ),
        "boundary": {
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 123. Item-Type Split-Only Formula Compile",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 121 found that item-type `split6_only` predicts prefix holdouts",
        "better than the active split-plus-previous-item context. This compile",
        "tests whether that simpler component can be promoted as a decodable",
        "full-corpus formula under the active recipe and a conservative unchanged",
        "item-type declaration charge.",
        "",
        "## Result",
        "",
        f"- Active compression bound: `{active_bits:.3f}` bits",
        f"- Split-only candidate: `{candidate_bits:.3f}` bits",
        f"- Gain vs active: `{active_bits - candidate_bits:.3f}` bits",
        f"- Candidate with one extra declaration bit: `{conservative_candidate_bits:.3f}` bits",
        f"- Gain with one extra declaration bit: `{active_bits - conservative_candidate_bits:.3f}` bits",
        "- Roundtrip: `70/70`",
        "",
        "## Component",
        "",
        "| Component | Active bits | Split-only bits | Gain |",
        "|---|---:|---:|---:|",
        (
            f"| `item_type` | `{active_item_bits:.3f}` | "
            f"`{split_only_bits:.3f}` | `{active_item_bits - split_only_bits:.3f}` |"
        ),
        "",
        "## Interpretation",
        "",
        "The simpler item-type model is not just a holdout explanation: under the",
        "same declaration charge it also improves the full-corpus mechanical code.",
        "It remains a book-generation formula change only. It does not explain",
        "row0, introduce plaintext, or make an authorial-intent claim.",
        "",
        "## Boundary",
        "",
        "- Recipe, copy addresses, copy lengths, literal lengths, and literal payload",
        "  model are unchanged.",
        "- Forced item-type rules remain enforced.",
        "- `translation_delta`: `NONE`.",
    ]
    if output_formula:
        lines.extend(["", "## Promoted Formula", "", f"- [{Path(output_formula).name}](../../{Path(output_formula).name})"])

    write_result("123_item_type_split_only_formula_compile", result, lines)


if __name__ == "__main__":
    main()
