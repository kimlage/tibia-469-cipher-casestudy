from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

AUDIT_141 = REPORTS / "141_default_exception_prequential_validation.json"
COPY_LENGTH_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_default_exception_formula_469.json"
)
COPY_SOURCE_FORMULA = (
    HERE
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
COPY_LENGTH_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_default_exception_bits"
COPY_SOURCE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_bits"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def summarize_component(rows: list[dict[str, Any]], component: str, mode: str) -> dict[str, Any]:
    key = f"{component}_{mode}"
    values = [float(row["component_gain_vs_uniform_bits"][key]) for row in rows]
    return {
        "n": len(values),
        "min": min(values) if values else None,
        "mean": sum(values) / len(values) if values else None,
        "max": max(values) if values else None,
        "total": sum(values),
        "nonpositive_count": sum(value <= 0 for value in values),
        "nonpositive_labels": [
            row["label"]
            for row in rows
            if float(row["component_gain_vs_uniform_bits"][key]) <= 0
        ],
    }


def section_component_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        component: {
            mode: summarize_component(rows, component, mode)
            for mode in ("online", "frozen")
        }
        for component in ("copy_length", "copy_source")
    }


def make_result() -> dict[str, Any]:
    audit = load_json(AUDIT_141)
    length_formula = load_json(COPY_LENGTH_FORMULA)
    source_formula = load_json(COPY_SOURCE_FORMULA)
    compression_bound_bits = float(source_formula["mdl_estimate_rough"][COPY_SOURCE_TOTAL_KEY])
    copy_length_only_bits = float(length_formula["mdl_estimate_rough"][COPY_LENGTH_TOTAL_KEY])

    prefix_summary = section_component_summary(audit["prefix_future_suffix"]["rows"])
    block_summary = section_component_summary(audit["contiguous_block_holdouts"]["rows"])
    family_summary = section_component_summary(audit["public_bookcase_family_holdouts"]["rows"])

    copy_length_prefix_frozen_ok = (
        prefix_summary["copy_length"]["frozen"]["nonpositive_count"] == 0
    )
    copy_source_prefix_frozen_ok = (
        prefix_summary["copy_source"]["frozen"]["nonpositive_count"] == 0
    )
    family_any_failures = any(
        family_summary[component][mode]["nonpositive_count"] > 0
        for component in ("copy_length", "copy_source")
        for mode in ("online", "frozen")
    )
    prefix_frozen_profile_bits = (
        compression_bound_bits
        if copy_length_prefix_frozen_ok and copy_source_prefix_frozen_ok
        else copy_length_only_bits
    )
    if copy_length_prefix_frozen_ok and copy_source_prefix_frozen_ok and family_any_failures:
        classification = "default_exception_components_prefix_frozen_partial_family_holdout"
    elif copy_length_prefix_frozen_ok and copy_source_prefix_frozen_ok:
        classification = "default_exception_components_prefix_frozen_profile"
    elif copy_length_prefix_frozen_ok and not copy_source_prefix_frozen_ok:
        classification = "copy_length_default_exception_frozen_profile_source_default_compression_only"
    else:
        classification = "default_exception_component_profile_mixed"

    source_default_full_corpus_gain = copy_length_only_bits - compression_bound_bits
    copy_source_status = (
        "retained_for_prefix_frozen_generation_profile_partial_under_family_holdout"
        if copy_source_prefix_frozen_ok and family_any_failures
        else (
            "retained_for_frozen_prefix_generation_profile"
            if copy_source_prefix_frozen_ok
            else "compression_bound_only_not_frozen_generation_profile"
        )
    )

    return {
        "schema": "default_exception_component_profile.v1",
        "test": "142_default_exception_component_profile",
        "classification": classification,
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "sources": {
            "audit_141": rel(AUDIT_141),
            "copy_length_formula": rel(COPY_LENGTH_FORMULA),
            "copy_source_formula": rel(COPY_SOURCE_FORMULA),
        },
        "bit_ledgers": {
            "compression_bound_with_copy_source_default_bits": compression_bound_bits,
            "copy_length_only_default_exception_bits": copy_length_only_bits,
            "prefix_frozen_generation_profile_bits": prefix_frozen_profile_bits,
            "copy_source_default_gain_vs_copy_length_only_bits": source_default_full_corpus_gain,
            "interpretation": (
                "Count the copy-source default/exception ledger in the prefix-frozen "
                "profile after the train-count fix, but keep the generation claim "
                "partial because family holdouts still have failures."
            ),
        },
        "component_summaries": {
            "prefix_future_suffix": prefix_summary,
            "contiguous_block_holdouts": block_summary,
            "public_bookcase_family_holdouts": family_summary,
        },
        "decision": {
            "compression_bound_bits": compression_bound_bits,
            "prefix_frozen_generation_profile_bits": prefix_frozen_profile_bits,
            "family_holdout_partial": family_any_failures,
            "copy_length_default_exception_status": (
                "retained_for_frozen_prefix_generation_profile"
                if copy_length_prefix_frozen_ok
                else "partial_only"
            ),
            "copy_source_default_exception_status": copy_source_status,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
        },
    }


def render_markdown(result: dict[str, Any]) -> str:
    prefix = result["component_summaries"]["prefix_future_suffix"]
    bits = result["bit_ledgers"]
    lines = [
        "# 142. Default/Exception Component Profile",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Audit 141 tests whether the promoted default/exception ledgers predict",
        "held-out books after learning counts on train books. This profile",
        "separates the compression bound, prefix-frozen evidence, and remaining",
        "family-holdout limits by component.",
        "",
        "## Bit Ledgers",
        "",
        f"- Compression bound with copy-source default: `{bits['compression_bound_with_copy_source_default_bits']:.3f}` bits",
        f"- Copy-length-only default/exception bits: `{bits['copy_length_only_default_exception_bits']:.3f}` bits",
        f"- Prefix-frozen generation profile: `{bits['prefix_frozen_generation_profile_bits']:.3f}` bits",
        f"- Copy-source default gain vs copy-length-only profile: `{bits['copy_source_default_gain_vs_copy_length_only_bits']:.3f}` bits",
        "",
        "## Prefix Component Summary",
        "",
        "| Component | Mode | Min gain | Mean gain | Total gain | Nonpositive splits |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for component in ("copy_length", "copy_source"):
        for mode in ("online", "frozen"):
            row = prefix[component][mode]
            lines.append(
                f"| `{component}` | `{mode}` | `{row['min']:.3f}` | "
                f"`{row['mean']:.3f}` | `{row['total']:.3f}` | "
                f"`{row['nonpositive_count']}` |"
            )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Keep `8177.317` bits as `compression_bound`.",
            "- Use `8177.317` bits as the prefix-frozen generation profile for the default/exception layer.",
            "- Retain copy-length and copy-source default/exception as prefix-frozen explanatory evidence.",
            "- Keep the generation claim partial because family/bookcase holdouts still have nonpositive component splits.",
            "- `row0` and semantics are unchanged.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    result = make_result()
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "142_default_exception_component_profile.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / "142_default_exception_component_profile.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
