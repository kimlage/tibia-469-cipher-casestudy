from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE80_SCRIPT = HERE / "scripts" / "80_boundary_policy_stability_gate.py"
GATE80 = TEST_RESULTS / "80_boundary_policy_stability_gate.json"

COMPONENTS = [
    "item_type",
    "copy_source_flag",
    "copy_source_exception",
    "copy_length",
    "literal_payload",
    "literal_length",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def zero_components() -> dict[str, float]:
    return {component: 0.0 for component in COMPONENTS}


def score_fixed_ops_with_components(
    *,
    context: dict[str, Any],
    book: int,
    available: str,
    initial_previous_copy_end: int | None,
    ops: list[dict[str, Any]],
) -> dict[str, Any]:
    gate37 = context["gate37"]
    audit126 = context["audit126"]
    formula = context["formula"]
    train_counts = context["train_counts"]
    source_train_counts = context["source_train_counts"]
    copy_prefixes = context["copy_prefixes"]
    text = context["books"][str(book)]
    min_len = int(formula["policy"]["min_len"])
    literal_length_model = formula["policy"]["literal_run_length_model"]
    payload_model = formula["policy"]["literal_payload_model"]
    copy_model = formula["policy"]["copy_length_model"]
    item_model = formula["policy"]["item_type_model"]
    copy_context = audit126.copy_context_key(book)
    payload_prefix = audit126.literal_payload_prefix_costs(
        text=text,
        emitted_before_book=available,
        payload_counts=train_counts["payload"],
        order=int(payload_model["order"]),
        alpha=float(payload_model["alpha"]),
    )

    components = zero_components()
    position = 0
    previous_item = "BOS"
    previous_end = initial_previous_copy_end
    local_emitted = available
    for op in ops:
        length = int(op["length"])
        if length <= 0 or int(op["target_start"]) != position:
            return {
                "valid": False,
                "bits": float("inf"),
                "reason": "bad_target_or_length",
                "components": components,
            }
        remaining = len(text) - position
        if length > remaining:
            return {
                "valid": False,
                "bits": float("inf"),
                "reason": "over_book_end",
                "components": components,
            }

        if op["type"] == "literal":
            if previous_item == "literal":
                return {
                    "valid": False,
                    "bits": float("inf"),
                    "reason": "adjacent_literal",
                    "components": components,
                }
            literal_forced = remaining < min_len
            if literal_forced and length != remaining:
                return {
                    "valid": False,
                    "bits": float("inf"),
                    "reason": "bad_forced_literal_length",
                    "components": components,
                }
            next_position = position + length
            components["literal_payload"] += (
                payload_prefix[next_position] - payload_prefix[position]
            )
            if not literal_forced:
                components["item_type"] += audit126.item_bits_for_choice(
                    forced=False,
                    item_type="literal",
                    book_int=book,
                    item_model=item_model,
                    item_counts=train_counts["item"],
                )
                components["literal_length"] += audit126.length_bits(
                    length + 1,
                    literal_length_model,
                )
            local_emitted += text[position:next_position]
            position = next_position
            previous_item = "literal"
            continue

        if op["type"] != "copy":
            return {
                "valid": False,
                "bits": float("inf"),
                "reason": "unknown_op",
                "components": components,
            }

        if remaining < min_len or length < min_len:
            return {
                "valid": False,
                "bits": float("inf"),
                "reason": "short_copy",
                "components": components,
            }
        source = int(op["source"])
        target_digit_global = len(available) + position
        legal_source_count = max(1, target_digit_global - min_len + 1)
        max_length = min(remaining, target_digit_global - source)
        symbol_count = max_length - min_len + 1
        length_index = length - min_len
        if (
            source < 0
            or source >= legal_source_count
            or symbol_count <= 0
            or length_index < 0
            or length_index >= symbol_count
        ):
            return {
                "valid": False,
                "bits": float("inf"),
                "reason": "illegal_copy",
                "components": components,
            }
        copied = local_emitted[source : source + length]
        target = text[position : position + length]
        if copied != target:
            return {
                "valid": False,
                "bits": float("inf"),
                "reason": "copy_mismatch",
                "components": components,
            }
        source_bits, _is_default, flag_bits, exception_bits = (
            gate37.source_default_exception_bits(
                source=source,
                legal_source_count=legal_source_count,
                previous_copy_end=previous_end,
                counts=source_train_counts,
            )
        )
        if not math.isfinite(source_bits):
            return {
                "valid": False,
                "bits": float("inf"),
                "reason": "source_inf",
                "components": components,
            }
        forced = previous_item == "literal"
        components["item_type"] += audit126.item_bits_for_choice(
            forced=forced,
            item_type="copy",
            book_int=book,
            item_model=item_model,
            item_counts=train_counts["item"],
        )
        components["copy_source_flag"] += flag_bits
        components["copy_source_exception"] += exception_bits
        components["copy_length"] += gate37.fast_copy_length_bits(
            counts=train_counts["copy"],
            prefixes=copy_prefixes,
            context=copy_context,
            length_index=length_index,
            symbol_count=symbol_count,
            alpha=int(copy_model["alpha"]),
        )
        local_emitted += copied
        position += length
        previous_item = "copy"
        previous_end = source + length

    total = sum(components.values())
    return {
        "valid": position == len(text) and local_emitted.endswith(text),
        "bits": total if position == len(text) else float("inf"),
        "reason": "ok" if position == len(text) else "incomplete",
        "components": components,
        "final_previous_copy_end": previous_end,
    }


def dominant_positive_component(delta: dict[str, float]) -> str:
    positives = {
        component: value
        for component, value in delta.items()
        if value > 1e-9
    }
    if not positives:
        return "none"
    return max(positives.items(), key=lambda item: (item[1], item[0]))[0]


def make_result() -> dict[str, Any]:
    gate80_result = load_json(GATE80)
    assert_boundary("boundary_policy_stability", gate80_result)
    gate80 = load_module("gate80_boundary_policy", GATE80_SCRIPT)
    rows = gate80.replay_rows_with_initials()
    unstable_books = {
        int(row["book"]) for row in gate80_result["summary"]["book_rows"]
    }
    variants_by_book, rows_by_cutoff_book = gate80.collect_variants(
        rows,
        unstable_books,
    )

    dominant_counts: dict[str, int] = {}
    positive_delta_totals = zero_components()
    signed_delta_totals = zero_components()
    comparison_rows = []
    book_rows = []
    comparison_count = 0
    total_regret_bits = 0.0

    for book in sorted(unstable_books):
        variants = variants_by_book[book]
        cutoff_rows = sorted(
            (
                row
                for (_cutoff, row_book), row in rows_by_cutoff_book.items()
                if row_book == book
            ),
            key=lambda row: int(row["cutoff"]),
        )
        book_dominant_counts: dict[str, int] = {}
        book_total_regret = 0.0
        for row in cutoff_rows:
            cutoff = int(row["cutoff"])
            scored_by_signature = {}
            for variant in variants:
                scored_by_signature[variant["signature"]] = score_fixed_ops_with_components(
                    context=row["context"],
                    book=book,
                    available=row["available"],
                    initial_previous_copy_end=row["initial_previous_copy_end"],
                    ops=variant["ops"],
                )
            winner_signature = row["signature"]
            winner = scored_by_signature[winner_signature]
            if not winner["valid"]:
                raise RuntimeError(
                    {
                        "book": book,
                        "cutoff": cutoff,
                        "type": "winner_invalid",
                        "reason": winner["reason"],
                    }
                )
            for variant in variants:
                signature = variant["signature"]
                if signature == winner_signature:
                    continue
                scored = scored_by_signature[signature]
                if not scored["valid"]:
                    raise RuntimeError(
                        {
                            "book": book,
                            "cutoff": cutoff,
                            "signature": signature,
                            "type": "variant_invalid",
                            "reason": scored["reason"],
                        }
                    )
                delta = {
                    component: scored["components"][component]
                    - winner["components"][component]
                    for component in COMPONENTS
                }
                regret = scored["bits"] - winner["bits"]
                dominant = dominant_positive_component(delta)
                comparison_count += 1
                total_regret_bits += regret
                book_total_regret += regret
                dominant_counts[dominant] = dominant_counts.get(dominant, 0) + 1
                book_dominant_counts[dominant] = book_dominant_counts.get(dominant, 0) + 1
                for component in COMPONENTS:
                    signed_delta_totals[component] += delta[component]
                    if delta[component] > 0:
                        positive_delta_totals[component] += delta[component]
                comparison_rows.append(
                    {
                        "book": book,
                        "cutoff": cutoff,
                        "winner_signature": winner_signature,
                        "variant_signature": signature,
                        "regret_bits": regret,
                        "dominant_positive_component": dominant,
                        "component_delta_bits": delta,
                        "winner_component_bits": winner["components"],
                        "variant_component_bits": scored["components"],
                    }
                )
        book_rows.append(
            {
                "book": book,
                "variant_count": len(variants),
                "cutoff_count": len(cutoff_rows),
                "comparison_count": sum(book_dominant_counts.values()),
                "dominant_component_counts": book_dominant_counts,
                "total_regret_bits": book_total_regret,
            }
        )

    top_positive_components = sorted(
        positive_delta_totals.items(),
        key=lambda item: (-item[1], item[0]),
    )
    top_signed_components = sorted(
        signed_delta_totals.items(),
        key=lambda item: (-abs(item[1]), item[0]),
    )
    classification = "boundary_instability_driven_by_learned_cost_components"
    return {
        "schema": "boundary_instability_cost_decomposition_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate80_boundary_policy": rel(GATE80),
            "gate80_boundary_policy_script": rel(GATE80_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "unstable_books_only": True,
            "observed_variants_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "unstable_book_count": len(unstable_books),
            "variant_against_winner_comparison_count": comparison_count,
            "total_regret_bits": total_regret_bits,
            "mean_regret_bits": total_regret_bits / comparison_count,
            "dominant_component_counts": dominant_counts,
            "positive_delta_totals_by_component": positive_delta_totals,
            "signed_delta_totals_by_component": signed_delta_totals,
            "top_positive_components": [
                {"component": component, "bits": bits}
                for component, bits in top_positive_components
            ],
            "top_signed_components": [
                {"component": component, "bits": bits}
                for component, bits in top_signed_components
            ],
            "book_rows": book_rows,
            "largest_regret_comparisons": sorted(
                comparison_rows,
                key=lambda row: (-row["regret_bits"], row["book"], row["cutoff"]),
            )[:20],
            "interpretation": (
                "The remaining boundary choices are being selected by the "
                "learned coding streams rather than by a simple invariant "
                "boundary rule. Component deltas localize which streams most "
                "often make the losing observed variants more expensive than "
                "the per-cutoff parser winner."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "boundary_instability_costs_decomposed",
            "generation_explanation_status": "boundary_selection_still_cost_driven_not_rule_driven",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "81_boundary_instability_cost_decomposition_gate.json"
    md_path = TEST_RESULTS / "81_boundary_instability_cost_decomposition_gate.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Boundary Instability Cost Decomposition Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 80 rejected simple invariant boundary policies. This gate asks",
        "which learned cost components actually separate each per-cutoff parser",
        "winner from the other observed variants of the same unstable book.",
        "",
        "## Summary",
        "",
        f"- Unstable books tested: `{s['unstable_book_count']}`.",
        f"- Variant-vs-winner comparisons: `{s['variant_against_winner_comparison_count']}`.",
        f"- Total regret bits across comparisons: `{s['total_regret_bits']:.6f}`.",
        f"- Mean regret bits: `{s['mean_regret_bits']:.6f}`.",
        f"- Dominant component counts: `{s['dominant_component_counts']}`.",
        "",
        "## Positive Delta Totals",
        "",
        "| Component | Positive delta bits | Signed delta bits |",
        "|---|---:|---:|",
    ]
    for component in COMPONENTS:
        lines.append(
            "| {component} | {positive:.6f} | {signed:.6f} |".format(
                component=component,
                positive=s["positive_delta_totals_by_component"][component],
                signed=s["signed_delta_totals_by_component"][component],
            )
        )
    lines.extend(
        [
            "",
            "## Largest Regret Comparisons",
            "",
            "| Book | Cutoff | Regret bits | Dominant component |",
            "|---:|---:|---:|---|",
        ]
    )
    for row in s["largest_regret_comparisons"][:10]:
        lines.append(
            "| {book} | {cutoff} | {regret_bits:.6f} | `{dominant_positive_component}` |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No corpus-wide formula promotion is introduced.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
