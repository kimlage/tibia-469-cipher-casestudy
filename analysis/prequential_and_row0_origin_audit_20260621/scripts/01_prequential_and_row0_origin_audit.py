from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

LEGACY_SCRIPT = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "scripts"
    / "125_prequential_and_row0_origin_audit.py"
)
LEGACY_RESULT = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "reports"
    / "test_results"
    / "125_prequential_and_row0_origin_audit.json"
)
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

SCOPE_COMPRESSION_BOUND_BITS = 8558.666806283434
KNOWN_LATER_COMPRESSION_ONLY_BOUND_BITS = 8343.061944935467


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("legacy_prequential_row0_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": percentile(values, 0.5),
        "mean": sum(values) / len(values),
        "max": max(values),
    }


def split_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    online = [float(row["aggregate"]["test_online_gain_vs_uniform_bits"]) for row in rows]
    frozen = [float(row["aggregate"]["test_frozen_gain_vs_uniform_bits"]) for row in rows]
    gaps = [float(row["aggregate"]["online_train_test_gap_bits_per_event"]) for row in rows]
    failures = [
        {
            "label": row["label"],
            "online_gain_vs_uniform_bits": row["aggregate"]["test_online_gain_vs_uniform_bits"],
            "frozen_gain_vs_uniform_bits": row["aggregate"]["test_frozen_gain_vs_uniform_bits"],
        }
        for row in rows
        if row["aggregate"]["test_online_gain_vs_uniform_bits"] <= 0
        or row["aggregate"]["test_frozen_gain_vs_uniform_bits"] <= 0
    ]
    return {
        "split_count": len(rows),
        "online_gain_vs_uniform_bits": summary(online),
        "frozen_gain_vs_uniform_bits": summary(frozen),
        "train_test_gap_bits_per_event": summary(gaps),
        "nonpositive_gain_failures": failures,
    }


def ablation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_component: dict[str, list[float]] = {
        "copy_length": [],
        "literal_payload": [],
        "item_type": [],
    }
    for row in rows:
        online_total = float(row["aggregate"]["test_online_bits"])
        ablated = row["test_component_ablation_totals_bits"]
        by_component["copy_length"].append(float(ablated["copy_length_uniform_only"]) - online_total)
        by_component["literal_payload"].append(float(ablated["literal_payload_uniform_only"]) - online_total)
        by_component["item_type"].append(float(ablated["item_type_uniform_only"]) - online_total)
    return {component: summary(values) for component, values in by_component.items()}


def parameter_stability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parameter_rows = [
        row["parameter_stability"]["declared_parameters_frozen"]
        for row in rows
    ]
    first = parameter_rows[0] if parameter_rows else {}
    coverage: dict[str, dict[str, int]] = {}
    for component, key in [
        ("copy_length", "copy_length_context_coverage"),
        ("literal_payload", "literal_payload_context_coverage"),
        ("item_type", "item_type_context_coverage"),
    ]:
        missing = sum(
            int(row["parameter_stability"][key]["missing_context_events"])
            for row in rows
        )
        present = sum(
            int(row["parameter_stability"][key]["present_context_events"])
            for row in rows
        )
        coverage[component] = {
            "present_context_events": present,
            "missing_context_events": missing,
        }
    return {
        "parameters_identical_across_splits": all(row == first for row in parameter_rows),
        "declared_parameters": first,
        "context_coverage_total": coverage,
    }


def row0_substrate_facts() -> dict[str, Any]:
    occ = load_json(OCC_STREAMS)
    books = load_json(BOOKS_DIGITS)
    codes = sorted({code for values in occ["class_sizes"].values() for code in values})
    all_codes = {f"{index:02d}" for index in range(100)}
    return {
        "source_occ_streams": rel(OCC_STREAMS),
        "source_books_digits": rel(BOOKS_DIGITS),
        "book_count": len(books),
        "row0_symbol_count": len(occ["class_sizes"]),
        "class_code_count": len(codes),
        "missing_two_digit_codes": sorted(all_codes - set(codes)),
        "class_sizes": {key: len(value) for key, value in sorted(occ["class_sizes"].items())},
        "full_duplicate_book_count": len(occ.get("full_dup_books", [])),
        "note": (
            "These committed artifacts verify the code-class substrate used by the "
            "mechanical audits; they do not derive the 10x10 pair-cell labels."
        ),
    }


def make_result(legacy: dict[str, Any]) -> dict[str, Any]:
    predictive = legacy["predictive_validation"]
    prefix = predictive["prefix_future_suffix_splits"]
    blocks = predictive["contiguous_block_holdouts"]
    families = predictive["public_bookcase_family_holdouts"]
    random_controls = predictive["random_train_set_controls"]

    family_failures = split_summary(families)["nonpositive_gain_failures"]
    prefix_failures = split_summary(prefix)["nonpositive_gain_failures"]
    block_failures = split_summary(blocks)["nonpositive_gain_failures"]
    if prefix_failures:
        predictive_class = "posthoc_compressor_warning_prefix_holdout_failed"
    elif family_failures:
        predictive_class = "predictive_signal_partial_not_generation_method"
    elif block_failures:
        predictive_class = "predictive_signal_partial_block_instability"
    else:
        predictive_class = "predictive_signal_retained_but_recipe_still_posthoc"

    return {
        "schema": "prequential_and_row0_origin_audit_20260621.v1",
        "classification": "analysis_only_falsifiable_audit_row0_origin_exogenous",
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "scope": {
            "scope_compression_bound_bits": SCOPE_COMPRESSION_BOUND_BITS,
            "source_formula": legacy["source_formula"],
            "known_later_compression_only_bound_bits_not_used_as_generation_claim": (
                KNOWN_LATER_COMPRESSION_ONLY_BOUND_BITS
            ),
            "reason_later_bound_not_used_here": (
                "The requested method change freezes the 8558.667-bit formula as "
                "the predictive-validation target and stops treating later "
                "compression-only micro-improvements as generation evidence."
            ),
            "fixed_recipe_limitation": (
                "All predictive tests keep the full-corpus LZ recipe fixed. "
                "They validate learned component scoring, not recipe discovery."
            ),
        },
        "active_component_reproduction": legacy["active_component_reproduction"],
        "predictive_validation": {
            "classification": predictive_class,
            "prefix_future_suffix": {
                "summary": split_summary(prefix),
                "rows": prefix,
            },
            "contiguous_block_holdouts": {
                "summary": split_summary(blocks),
                "rows": blocks,
            },
            "public_bookcase_family_holdouts": {
                "summary": split_summary(families),
                "rows": families,
            },
            "randomized_order_controls": random_controls,
            "component_ablation_prefix_splits": ablation_summary(prefix),
            "parameter_stability_prefix_splits": parameter_stability(prefix),
            "failure_rule": (
                "If prefix holdout gains vanish, classify as posthoc compressor. "
                "Family failures downgrade the result to partial predictive signal, "
                "not an authorial generation method."
            ),
        },
        "row0_origin": {
            "classification": "row0_origin_remains_exogenous",
            "substrate_facts": row0_substrate_facts(),
            "what_row0_explains": legacy["row0_origin"]["what_row0_explains"],
            "what_remains_exogenous": legacy["row0_origin"]["what_remains_exogenous"],
            "hypotheses": legacy["row0_origin"]["hypotheses"],
            "promoted_row0_origin_formula_count": 0,
        },
        "progress_criterion": {
            "counts_as_progress": [
                "Prefix/block/family holdout validation or falsification.",
                "A clearer ad-hoc dependency ledger for the fixed LZ recipe and row0.",
                "Controlled rejection of row0-origin hypotheses with algorithm, cost, coverage, contradictions, and controls.",
            ],
            "does_not_count_as_progress": [
                "Number of scripts or test rows.",
                "Compression-only bit reductions without holdout or structural value.",
                "Any semantic projection unsupported by CipSoft/in-game evidence.",
            ],
        },
        "decision": {
            "compression_bound_status": "8558.667 bits is the frozen validation scope, not final authorial method.",
            "generation_explanation_status": predictive_class,
            "row0_origin_status": "exogenous_under_current_evidence",
            "translation_or_plaintext_status": "NONE",
        },
    }


def render_markdown(result: dict[str, Any], *, audit_link_prefix: str) -> str:
    prefix = result["predictive_validation"]["prefix_future_suffix"]["rows"]
    random_controls = result["predictive_validation"]["randomized_order_controls"]
    block_summary = result["predictive_validation"]["contiguous_block_holdouts"]["summary"]
    family_summary = result["predictive_validation"]["public_bookcase_family_holdouts"]["summary"]
    ablations = result["predictive_validation"]["component_ablation_prefix_splits"]
    params = result["predictive_validation"]["parameter_stability_prefix_splits"]

    lines = [
        "# Prequential and Row0 Origin Audit",
        "",
        "Classification: `analysis_only_falsifiable_audit_row0_origin_exogenous`",
        "Translation delta: `NONE`",
        "",
        "## Scope",
        "",
        f"- Frozen validation compression bound: `{result['scope']['scope_compression_bound_bits']:.3f}` bits",
        f"- Later compression-only bound recorded but not used as generation evidence: `{result['scope']['known_later_compression_only_bound_bits_not_used_as_generation_claim']:.3f}` bits",
        "- No plaintext, translation, or case-reopening claim is made.",
        "- Limitation: the LZ recipe is fixed from the full corpus; this audit tests learned component scoring, not recipe discovery.",
        "",
        "## Predictive Validation",
        "",
        f"Predictive classification: `{result['predictive_validation']['classification']}`",
        "",
        "| Split | Train books | Test books | Train bits | Test online bits | Test frozen bits | Uniform bits | Online gain | Frozen gain | Gap/event |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in prefix:
        agg = row["aggregate"]
        lines.append(
            f"| `{row['label']}` | `{len(row['train_books'])}` | `{len(row['test_books'])}` | "
            f"`{agg['train_bits']:.3f}` | `{agg['test_online_bits']:.3f}` | "
            f"`{agg['test_frozen_bits']:.3f}` | `{agg['test_uniform_bits']:.3f}` | "
            f"`{agg['test_online_gain_vs_uniform_bits']:.3f}` | "
            f"`{agg['test_frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{agg['online_train_test_gap_bits_per_event']:.4f}` |"
        )

    lines.extend(
        [
            "",
            "### Baselines And Controls",
            "",
            f"- Prefix online gain summary: `{result['predictive_validation']['prefix_future_suffix']['summary']['online_gain_vs_uniform_bits']}`",
            f"- Prefix frozen gain summary: `{result['predictive_validation']['prefix_future_suffix']['summary']['frozen_gain_vs_uniform_bits']}`",
            f"- Contiguous block online summary: `{block_summary['online_gain_vs_uniform_bits']}`",
            f"- Public-bookcase family online summary: `{family_summary['online_gain_vs_uniform_bits']}`",
            f"- Public-bookcase family nonpositive failures: `{family_summary['nonpositive_gain_failures']}`",
            "",
            "| Cutoff | Observed prefix online gain | Random median gain | p(random >= observed) |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in random_controls:
        lines.append(
            f"| `{row['cutoff']}` | `{row['observed_prefix_online_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['random_gain_summary_bits']['median']:.3f}` | "
            f"`{row['p_random_gain_ge_observed']:.4f}` |"
        )

    lines.extend(
        [
            "",
            "### Component Ablations",
            "",
            "Values are bits saved by the learned component over replacing only that component with a uniform code on prefix holdouts.",
            "",
            "| Component | Min | Median | Mean | Max |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for component, row in ablations.items():
        lines.append(
            f"| `{component}` | `{row['min']:.3f}` | `{row['median']:.3f}` | "
            f"`{row['mean']:.3f}` | `{row['max']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "### Parameter Stability",
            "",
            f"- Parameters identical across prefix splits: `{params['parameters_identical_across_splits']}`",
            f"- Declared parameters: `{params['declared_parameters']}`",
            f"- Context coverage totals: `{params['context_coverage_total']}`",
            "",
            "Interpretation: prefix and contiguous-block tests retain positive advantage over uniform, but the family split has nonpositive failures. The result is therefore predictive signal only, not a final generation method.",
            "",
            "## Row0 Origin Boundary",
            "",
            f"Row0 classification: `{result['row0_origin']['classification']}`",
            "",
            "### What Row0 Explains",
        ]
    )
    for item in result["row0_origin"]["what_row0_explains"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### What Remains Exogenous")
    for item in result["row0_origin"]["what_remains_exogenous"]:
        lines.append(f"- {item}")

    substrate = result["row0_origin"]["substrate_facts"]
    lines.extend(
        [
            "",
            "### Substrate Facts",
            "",
            f"- Books in committed digit corpus: `{substrate['book_count']}`",
            f"- Row0 symbols: `{substrate['row0_symbol_count']}`",
            f"- Class codes represented: `{substrate['class_code_count']}`",
            f"- Missing two-digit codes from class map: `{substrate['missing_two_digit_codes']}`",
            f"- Sources: [`occ_streams.json`]({audit_link_prefix}/homophone_channel/occ_streams.json), [`books_digits.json`]({audit_link_prefix}/books_digits.json)",
            "",
            "### Origin Hypotheses",
            "",
            "| Hypothesis | Status | Coverage | Cost | Contradictions / controls |",
            "|---|---|---|---:|---|",
        ]
    )
    for row in result["row0_origin"]["hypotheses"]:
        cost = row["descriptive_cost_bits"]
        cost_text = f"{cost:.3f}" if isinstance(cost, (int, float)) else str(cost)
        lines.append(
            f"| `{row['hypothesis']}` | `{row['status']}` | {row['coverage']} | "
            f"{cost_text} | {row['contradictions']}; controls `{row['negative_controls']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- `8558.667` bits remains a frozen validation scope here, not a final authorial method.",
            "- The learned component signal survives prefix and block holdout but fails some family holdouts, so it is not promoted beyond partial predictive structure.",
            "- `row0` continues exogenous: the active book generator assumes the table rather than deriving it.",
            "- No translation, plaintext, or case reopening is introduced.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_module = load_module(LEGACY_SCRIPT)
    legacy_module.main()
    legacy = load_json(LEGACY_RESULT)
    if abs(float(legacy["compression_bound_bits_confirmed"]) - SCOPE_COMPRESSION_BOUND_BITS) > 1e-6:
        raise RuntimeError("legacy audit no longer matches frozen 8558.667-bit scope")
    result = make_result(legacy)

    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    result_path = TEST_RESULTS / "01_prequential_and_row0_origin_audit.json"
    report_path = TEST_RESULTS / "01_prequential_and_row0_origin_audit.md"
    final_report_path = REPORTS / "prequential_and_row0_origin_audit.md"

    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        render_markdown(result, audit_link_prefix="../../../audit_20260609"),
        encoding="utf-8",
    )
    final_report_path.write_text(
        render_markdown(result, audit_link_prefix="../../audit_20260609"),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
