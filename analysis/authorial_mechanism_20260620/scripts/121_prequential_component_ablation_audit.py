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


def split_rows(rows: list[dict[str, Any]], cutoff: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        [row for row in rows if int(row["book_int"]) < cutoff],
        [row for row in rows if int(row["book_int"]) >= cutoff],
    )


def copy_counts(rows: list[dict[str, Any]], context_key: Callable[[dict[str, Any]], Any]) -> dict[Any, dict[int, int]]:
    counts: dict[Any, dict[int, int]] = {}
    for row in rows:
        context = context_key(row)
        bucket = counts.setdefault(context, {})
        length_index = int(row["length_index"])
        bucket[length_index] = bucket.get(length_index, 0) + 1
    return counts


def score_copy_rows(
    rows: list[dict[str, Any]],
    counts: dict[Any, dict[int, int]],
    *,
    alpha: int,
    context_key: Callable[[dict[str, Any]], Any],
    update: bool,
) -> float:
    local_counts = {key: dict(value) for key, value in counts.items()}
    bits = 0.0
    for row in rows:
        context = context_key(row)
        bucket = local_counts.setdefault(context, {})
        symbol_count = int(row["symbol_count"])
        length_index = int(row["length_index"])
        legal_observations = sum(bucket.get(index, 0) for index in range(symbol_count))
        probability = (bucket.get(length_index, 0) + alpha) / (legal_observations + alpha * symbol_count)
        bits += -math.log2(probability)
        if update:
            bucket[length_index] = bucket.get(length_index, 0) + 1
    return bits


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
    counts: dict[Any, dict[str, float]],
    *,
    alpha: float,
    alphabet: list[str],
    context_key: Callable[[dict[str, Any]], Any],
    symbol_key: str,
    update: bool,
) -> float:
    local_counts = {key: dict(value) for key, value in counts.items()}
    bits = 0.0
    for row in rows:
        context = context_key(row)
        bucket = local_counts.setdefault(context, {symbol: 0.0 for symbol in alphabet})
        total = sum(bucket.get(symbol, 0.0) for symbol in alphabet)
        symbol = row[symbol_key]
        probability = (bucket.get(symbol, 0.0) + alpha) / (total + len(alphabet) * alpha)
        bits += -math.log2(probability)
        if update:
            bucket[symbol] = bucket.get(symbol, 0.0) + 1.0
    return bits


def summarize_variant(
    *,
    rows: list[dict[str, Any]],
    cutoffs: list[int],
    alphabet: list[str] | None,
    symbol_key: str,
    alpha: float,
    context_key: Callable[[dict[str, Any]], Any],
    score_kind: str,
) -> dict[str, Any]:
    cutoff_rows = []
    for cutoff in cutoffs:
        train_rows, holdout_rows = split_rows(rows, cutoff)
        if score_kind == "copy":
            counts = copy_counts(train_rows, context_key)
            online = score_copy_rows(holdout_rows, counts, alpha=int(alpha), context_key=context_key, update=True)
            frozen = score_copy_rows(holdout_rows, counts, alpha=int(alpha), context_key=context_key, update=False)
            uniform = sum(math.log2(int(row["symbol_count"])) for row in holdout_rows)
        else:
            if alphabet is None:
                raise ValueError("alphabet required for fixed scorer")
            counts = fixed_counts(train_rows, alphabet=alphabet, context_key=context_key, symbol_key=symbol_key)
            online = score_fixed_rows(
                holdout_rows,
                counts,
                alpha=alpha,
                alphabet=alphabet,
                context_key=context_key,
                symbol_key=symbol_key,
                update=True,
            )
            frozen = score_fixed_rows(
                holdout_rows,
                counts,
                alpha=alpha,
                alphabet=alphabet,
                context_key=context_key,
                symbol_key=symbol_key,
                update=False,
            )
            uniform = len(holdout_rows) * math.log2(len(alphabet))
        cutoff_rows.append(
            {
                "train_book_count": cutoff,
                "holdout_event_count": len(holdout_rows),
                "online_bits": online,
                "frozen_bits": frozen,
                "uniform_bits": uniform,
                "online_vs_uniform_bits": online - uniform,
                "frozen_vs_uniform_bits": frozen - uniform,
            }
        )
    return {
        "cutoffs": cutoff_rows,
        "total_online_vs_uniform_bits": sum(row["online_vs_uniform_bits"] for row in cutoff_rows),
        "total_frozen_vs_uniform_bits": sum(row["frozen_vs_uniform_bits"] for row in cutoff_rows),
    }


def main() -> None:
    audit118 = load_audit_118()
    frontier = audit118.load_module("minaddr_frontier", audit118.FRONTIER)
    midpoint = audit118.load_module("post_midpoint_frontier", audit118.MIDPOINT)
    context_module = audit118.load_module("copy_length_context", audit118.CONTEXT)
    payload_module = audit118.load_module("literal_payload_context", audit118.PAYLOAD_CONTEXT)
    item_module = audit118.load_module("item_type_context", audit118.ITEM_CONTEXT)

    formula = audit118.load_json(audit118.FORMULA)
    books = {str(key): value for key, value in audit118.load_json(audit118.BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][audit118.CURRENT_TOTAL_KEY])
    current_score = midpoint.score_formula(formula, books, frontier, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    copy_rows = context_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    item_model = formula["policy"]["item_type_model"]
    copy_alpha = int(formula["policy"]["copy_length_model"]["alpha"])
    payload_alpha = float(formula["policy"]["literal_payload_model"]["alpha"])
    item_alpha = float(item_model["alpha"])

    components = [
        {
            "component": "copy_length",
            "active_variant": "active_midpoint",
            "score_kind": "copy",
            "rows": copy_rows,
            "alphabet": None,
            "symbol_key": "length_index",
            "alpha": copy_alpha,
            "variants": [
                ("global", "single global bounded length-index distribution", lambda _row: "global"),
                ("active_midpoint", "book_id < 35 versus book_id >= 35", audit118.copy_context),
            ],
        },
        {
            "component": "literal_payload",
            "active_variant": "active_order2",
            "score_kind": "fixed",
            "rows": payload_rows,
            "alphabet": audit118.DIGITS,
            "symbol_key": "digit",
            "alpha": payload_alpha,
            "variants": [
                ("order0_global", "single global digit distribution", lambda _row: ("global", "")),
                ("order1_previous_digit", "previous one emitted digit", lambda row: ("global", row["previous_digit_context"][-1:])),
                ("active_order2", "previous two emitted digits", audit118.payload_context_key),
            ],
        },
        {
            "component": "item_type",
            "active_variant": "active_split6_prev1",
            "score_kind": "fixed",
            "rows": item_rows,
            "alphabet": audit118.ITEM_TYPES,
            "symbol_key": "item_type",
            "alpha": item_alpha,
            "variants": [
                ("order0_global", "single global item-type distribution", lambda _row: ("global", ())),
                ("prev1_global", "previous charged item type only", lambda row: ("global", tuple(row["previous_item_context"]))),
                (
                    "split6_only",
                    "book_id < 6 versus book_id >= 6 without previous item",
                    lambda row: (audit118.item_extra_context(item_model, row), ()),
                ),
                ("active_split6_prev1", "split at book 6 plus previous item", audit118.item_context_key(item_model)),
            ],
        },
    ]

    component_results = []
    for component in components:
        variants = []
        for name, description, context_key in component["variants"]:
            summary = summarize_variant(
                rows=component["rows"],
                cutoffs=audit118.TRAIN_CUTOFFS,
                alphabet=component["alphabet"],
                symbol_key=component["symbol_key"],
                alpha=component["alpha"],
                context_key=context_key,
                score_kind=component["score_kind"],
            )
            variants.append({"variant": name, "description": description, **summary})
        active = next(row for row in variants if row["variant"] == component["active_variant"])
        for row in variants:
            row["online_delta_vs_active_bits"] = (
                row["total_online_vs_uniform_bits"] - active["total_online_vs_uniform_bits"]
            )
            row["frozen_delta_vs_active_bits"] = (
                row["total_frozen_vs_uniform_bits"] - active["total_frozen_vs_uniform_bits"]
            )
        best_online = min(variants, key=lambda row: row["total_online_vs_uniform_bits"])
        best_frozen = min(variants, key=lambda row: row["total_frozen_vs_uniform_bits"])
        component_results.append(
            {
                "component": component["component"],
                "active_variant": component["active_variant"],
                "best_online_variant": best_online["variant"],
                "best_frozen_variant": best_frozen["variant"],
                "active_is_best_online": best_online["variant"] == component["active_variant"],
                "active_is_best_frozen": best_frozen["variant"] == component["active_variant"],
                "variants": variants,
            }
        )

    active_best_count = sum(
        1 for row in component_results if row["active_is_best_online"] and row["active_is_best_frozen"]
    )
    simpler_beats_active = [
        row["component"]
        for row in component_results
        if not (row["active_is_best_online"] and row["active_is_best_frozen"])
    ]
    classification = (
        "prequential_component_ablation_simplifies_generation_explanation"
        if simpler_beats_active
        else "prequential_component_ablation_supports_active_contexts"
    )

    result = {
        "schema": "prequential_component_ablation_audit.v1",
        "test": "121_prequential_component_ablation_audit",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(audit118.FORMULA.relative_to(ROOT)),
        "source_prequential_audit": str((REPORTS / "118_prequential_generation_model_audit.json").relative_to(ROOT)),
        "compression_bound_bits": current_bits,
        "train_cutoffs": audit118.TRAIN_CUTOFFS,
        "component_results": component_results,
        "summary": {
            "components_tested": len(component_results),
            "active_best_online_and_frozen_components": active_best_count,
            "components_where_simpler_variant_beats_active": simpler_beats_active,
            "interpretation": (
                "This audit tests generation-explanation simplicity only. It does "
                "not change the active compression bound, because the bound remains "
                "the fully charged best corpus code. Simpler holdout winners should "
                "be preferred when describing what mechanically generalizes."
            ),
        },
        "boundary": {
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# 121. Prequential Component Ablation Audit",
        "",
        f"Classification: `{classification}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This audit asks which learned components of the active book generator",
        "generalize under prefix holdout and which ones are better treated as",
        "compression-bound detail. It compares the active contexts against simpler",
        "variants on the same train cutoffs used by audit 118.",
        "",
        "Lower total `vs uniform` values are better because they save more bits",
        "across all five prefix holdouts.",
        "",
        "## Component Summary",
        "",
        "| Component | Active variant | Best online | Best frozen | Active online total | Best online total | Active frozen total | Best frozen total |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in component_results:
        active = next(item for item in row["variants"] if item["variant"] == row["active_variant"])
        best_online = next(item for item in row["variants"] if item["variant"] == row["best_online_variant"])
        best_frozen = next(item for item in row["variants"] if item["variant"] == row["best_frozen_variant"])
        lines.append(
            f"| `{row['component']}` | `{row['active_variant']}` | "
            f"`{row['best_online_variant']}` | `{row['best_frozen_variant']}` | "
            f"`{active['total_online_vs_uniform_bits']:.3f}` | "
            f"`{best_online['total_online_vs_uniform_bits']:.3f}` | "
            f"`{active['total_frozen_vs_uniform_bits']:.3f}` | "
            f"`{best_frozen['total_frozen_vs_uniform_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The active compression formula remains the `8561.792` bit bound. This",
            "audit does not lower that bound. Its job is to keep the generation",
            "explanation honest: if a simpler context predicts holdouts better than",
            "the active context, the active context should be described as a",
            "compression-bound refinement rather than a robust authorial mechanism.",
            "",
            "## Boundary",
            "",
            "- No row0/table origin formula is promoted.",
            "- No plaintext, glossary, or authorial-intent claim is introduced.",
            "- `translation_delta`: `NONE`.",
        ]
    )

    write_result("121_prequential_component_ablation_audit", result, lines)


if __name__ == "__main__":
    main()
