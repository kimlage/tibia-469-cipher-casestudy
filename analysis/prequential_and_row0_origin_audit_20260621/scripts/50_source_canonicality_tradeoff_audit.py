from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

CURRENT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
GATE42_SCRIPT = HERE / "scripts" / "42_full_corpus_source_substitution_frontier_gate.py"
GATE39_SCRIPT = HERE / "scripts" / "39_multicutoff_source_choice_optimizer_gate.py"
GATE45 = TEST_RESULTS / "45_full_corpus_source_substitution_fourth_pass_gate.json"
GATE46 = TEST_RESULTS / "46_source_substitution_saturation_audit.json"
GATE49 = TEST_RESULTS / "49_source_length_joint_derivability_audit.json"

CURRENT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_fourth_pass_bits"
)
CURRENT_SOURCE_BITS_KEY = "copy_source_substitution_frontier_bits"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
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


def profile(
    *,
    label: str,
    events: list[dict[str, Any]],
    sources: list[int],
    current_total_bits: float,
    current_source_bits: float,
    gate42,
) -> dict[str, Any]:
    score = gate42.score_sources(events, sources, include_rows=True)
    total_bits = current_total_bits - current_source_bits + score["copy_source_bits"]
    source_is_earliest = sum(
        1 for event, source in zip(events, sources) if source == min(event["candidates"])
    )
    source_is_latest = sum(
        1 for event, source in zip(events, sources) if source == max(event["candidates"])
    )
    source_is_unique = sum(1 for event in events if len(event["candidates"]) == 1)
    changed_vs_current = sum(
        1 for event, source in zip(events, sources) if source != event["source_digit_pos"]
    )
    return {
        "label": label,
        "total_bits": total_bits,
        "copy_source_bits": score["copy_source_bits"],
        "copy_source_stream_bits": score["model"]["stream_bits"],
        "copy_source_flag_bits": score["model"]["flag_bits"],
        "copy_source_exception_bits": score["model"]["exception_source_bits"],
        "default_count": score["model"]["default_count"],
        "exception_count": score["model"]["exception_count"],
        "source_is_earliest_count": source_is_earliest,
        "source_is_latest_count": source_is_latest,
        "source_is_unique_count": source_is_unique,
        "changed_vs_current_count": changed_vs_current,
        "delta_total_vs_current_bits": total_bits - current_total_bits,
        "delta_source_vs_current_bits": score["copy_source_bits"] - current_source_bits,
        "rows": score["rows"],
    }


def noncanonical_rows(
    events: list[dict[str, Any]],
    current_sources: list[int],
    earliest_sources: list[int],
) -> list[dict[str, Any]]:
    rows = []
    for event, current, earliest in zip(events, current_sources, earliest_sources):
        if current == earliest:
            continue
        rows.append(
            {
                "event_index": event["event_index"],
                "book": event["book"],
                "op_index": event["op_index"],
                "book_pos": event["book_pos"],
                "length": event["length"],
                "candidate_count": len(event["candidates"]),
                "earliest_source": earliest,
                "current_source": current,
                "latest_source": max(event["candidates"]),
                "candidate_sources": event["candidates"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    gate45 = load_json(GATE45)
    gate46 = load_json(GATE46)
    gate49 = load_json(GATE49)
    for name, data in [
        ("gate45", gate45),
        ("gate46", gate46),
        ("gate49", gate49),
    ]:
        assert_boundary(name, data)

    gate42 = load_module("gate42_source_substitution_frontier", GATE42_SCRIPT)
    gate39 = load_module("gate39_source_choice", GATE39_SCRIPT)
    formula = gate42.normalize_ops_flexible(load_json(CURRENT_FORMULA))
    books = {str(k): v for k, v in load_json(BOOKS_DIGITS).items()}
    event_data = gate42.build_source_events(
        formula=formula,
        books=books,
        gate39=gate39,
    )
    if event_data["errors"]:
        raise RuntimeError(event_data["errors"])
    events = event_data["events"]

    current_total_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_source_bits = float(formula["mdl_estimate_rough"][CURRENT_SOURCE_BITS_KEY])
    current_sources = [int(event["source_digit_pos"]) for event in events]
    earliest_sources = [min(event["candidates"]) for event in events]
    latest_sources = [max(event["candidates"]) for event in events]
    first_candidate_sources = [event["candidates"][0] for event in events]
    if earliest_sources != first_candidate_sources:
        raise RuntimeError("candidate ordering is not earliest-first")

    current = profile(
        label="current_source_substitution_fourth_pass",
        events=events,
        sources=current_sources,
        current_total_bits=current_total_bits,
        current_source_bits=current_source_bits,
        gate42=gate42,
    )
    if not math.isclose(
        current["copy_source_bits"],
        current_source_bits,
        abs_tol=1e-9,
    ):
        raise RuntimeError(
            {
                "type": "current_source_rescore_mismatch",
                "formula": current_source_bits,
                "rescored": current["copy_source_bits"],
            }
        )
    all_earliest = profile(
        label="all_earliest_source_explanation_profile",
        events=events,
        sources=earliest_sources,
        current_total_bits=current_total_bits,
        current_source_bits=current_source_bits,
        gate42=gate42,
    )
    all_latest = profile(
        label="all_latest_source_negative_control",
        events=events,
        sources=latest_sources,
        current_total_bits=current_total_bits,
        current_source_bits=current_source_bits,
        gate42=gate42,
    )
    noncanonical = noncanonical_rows(events, current_sources, earliest_sources)
    restored_count = len(noncanonical)
    cost_per_restored_event = (
        all_earliest["delta_total_vs_current_bits"] / restored_count
        if restored_count
        else 0.0
    )

    classification = (
        "source_canonicality_explanation_profile_costed_not_promoted"
        if restored_count > 0 and all_earliest["delta_total_vs_current_bits"] > 0
        else "source_canonicality_tradeoff_unresolved"
    )
    return {
        "schema": "source_canonicality_tradeoff_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "current_formula": rel(CURRENT_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "source_substitution_fourth_pass_gate": rel(GATE45),
            "source_substitution_saturation_audit": rel(GATE46),
            "source_length_joint_derivability_audit": rel(GATE49),
        },
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "plaintext_or_translation_claim": False,
            "tested_question": (
                "How many bits the current source-substituted compression bound "
                "buys by giving up the earlier all-earliest source canonicality."
            ),
        },
        "summary": {
            "copy_event_count": len(events),
            "candidate_source_option_count": sum(
                max(0, len(event["candidates"]) - 1) for event in events
            ),
            "current_total_bits": current_total_bits,
            "current_copy_source_bits": current_source_bits,
            "current_earliest_count": current["source_is_earliest_count"],
            "current_non_earliest_count": restored_count,
            "all_earliest_total_bits": all_earliest["total_bits"],
            "all_earliest_copy_source_bits": all_earliest["copy_source_bits"],
            "all_earliest_delta_vs_current_bits": all_earliest[
                "delta_total_vs_current_bits"
            ],
            "all_earliest_restored_events": restored_count,
            "all_earliest_cost_per_restored_event_bits": cost_per_restored_event,
            "all_latest_total_bits": all_latest["total_bits"],
            "all_latest_delta_vs_current_bits": all_latest[
                "delta_total_vs_current_bits"
            ],
            "source_substitution_tail_gain_bits": gate46["summary"][
                "tail_cumulative_gain_bits"
            ],
            "latest_pass_gain_bits": gate46["summary"]["last_pass_gain_bits"],
            "latest_pass_selector_floor_bits": gate46["summary"][
                "minimum_pair_selector_floor_bits"
            ],
            "all_earliest_profile": {
                key: value
                for key, value in all_earliest.items()
                if key != "rows"
            },
            "current_profile": {
                key: value for key, value in current.items() if key != "rows"
            },
            "all_latest_negative_control_profile": {
                key: value for key, value in all_latest.items() if key != "rows"
            },
            "interpretation": (
                "Restoring the all-earliest source rule recovers source "
                "canonicality for the 10 non-earliest current events but costs "
                "bits under the active adaptive source stream. The current lower "
                "compression bound is therefore slightly less regular than the "
                "better generation-explanation profile."
            ),
        },
        "noncanonical_current_sources": noncanonical,
        "decision": {
            "compression_bound_status": "unchanged_current_source_substitution_bound_retained",
            "source_canonicality_status": "all_earliest_available_as_explanation_profile_not_bound",
            "generation_explanation_status": "compression_vs_canonicality_tradeoff_quantified",
            "next_mainline_status": "structural_source_length_parser_should_choose_bound_or_canonical_profile_explicitly",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "50_source_canonicality_tradeoff_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Source Canonicality Tradeoff Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "The latest source-substitution formula is the lower compression bound,",
        "but gate 49 showed it no longer preserves the earlier all-earliest",
        "source pattern. This audit prices the explicit tradeoff: keep the",
        "current source choices, or restore all copy sources to the earliest",
        "legal occurrence of the declared copied chunk.",
        "",
        "## Summary",
        "",
        f"- Copy events: `{s['copy_event_count']}`.",
        f"- Candidate source options beyond current: `{s['candidate_source_option_count']}`.",
        f"- Current total bits: `{s['current_total_bits']:.6f}`.",
        f"- Current earliest-source coverage: `{s['current_earliest_count']}/{s['copy_event_count']}`.",
        f"- Current non-earliest source events: `{s['current_non_earliest_count']}`.",
        f"- All-earliest total bits: `{s['all_earliest_total_bits']:.6f}`.",
        f"- All-earliest delta vs current: `{s['all_earliest_delta_vs_current_bits']:+.6f}` bits.",
        f"- Cost per restored earliest event: `{s['all_earliest_cost_per_restored_event_bits']:+.6f}` bits.",
        f"- All-latest negative-control delta vs current: `{s['all_latest_delta_vs_current_bits']:+.6f}` bits.",
        f"- Last three source-substitution gains: `{s['source_substitution_tail_gain_bits']:+.6f}` bits.",
        f"- Latest source-substitution gain: `{s['latest_pass_gain_bits']:+.6f}` bits.",
        f"- Latest pair-selector floor: `{s['latest_pass_selector_floor_bits']:.3f}` bits.",
        "",
        "## Non-Earliest Current Sources",
        "",
        "| Event | Book | Op | Length | Earliest | Current | Latest | Candidates |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["noncanonical_current_sources"]:
        lines.append(
            f"| `{row['event_index']}` | `{row['book']}` | `{row['op_index']}` | "
            f"`{row['length']}` | `{row['earliest_source']}` | "
            f"`{row['current_source']}` | `{row['latest_source']}` | "
            f"`{row['candidate_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The current formula remains the lower compression bound, but its final",
            "source substitutions are not a cleaner generation explanation. Restoring",
            "all sources to the earliest legal occurrence gives a mechanically simpler",
            "profile and repairs `10` non-earliest events, but costs bits under the",
            "same adaptive source model. This separates the two ledgers explicitly:",
            "the bound is lower, while the all-earliest profile is cleaner but not",
            "promoted as a compression improvement.",
            "",
            "## Boundary",
            "",
            "- No new formula is emitted.",
            "- Compression bound is unchanged.",
            "- Source canonicality is available as an explanation profile, not as the current bound.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "50_source_canonicality_tradeoff_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
