from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATES = [
    (
        "post_targetmax_source_frontier",
        TEST_RESULTS / "56_post_targetmax_source_substitution_frontier_gate.json",
    ),
    (
        "post_targetmax_source_second_pass",
        TEST_RESULTS / "57_post_targetmax_source_substitution_second_pass_gate.json",
    ),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def gate_row(name: str, path: Path, data: dict[str, Any]) -> dict[str, Any]:
    summary = data["summary"]
    pair_count = int(summary["pair_substitution_count"])
    gain = float(summary["candidate_gain_bits"])
    selector_floor_bits = math.log2(pair_count)
    return {
        "name": name,
        "source": rel(path),
        "classification": data["classification"],
        "active_total_bits": float(summary["active_total_bits"]),
        "candidate_total_bits": float(summary["candidate_total_bits"]),
        "candidate_gain_bits": gain,
        "copy_event_count": int(summary["copy_event_count"]),
        "single_substitution_count": int(summary["single_substitution_count"]),
        "positive_single_count": int(summary["positive_single_count"]),
        "pair_substitution_count": pair_count,
        "positive_pair_count": int(summary["positive_pair_count"]),
        "positive_pair_fraction": int(summary["positive_pair_count"]) / pair_count,
        "selector_floor_bits": selector_floor_bits,
        "selector_floor_minus_gain_bits": selector_floor_bits - gain,
        "pair_candidates_per_gain_bit": pair_count / gain if gain > 0 else math.inf,
        "best_arity": int(summary["best_arity"]),
        "best_substitutions": summary["best_substitutions"],
    }


def make_result() -> dict[str, Any]:
    rows = []
    for name, path in GATES:
        data = load_json(path)
        assert_boundary(name, data)
        rows.append(gate_row(name, path, data))

    gains = [row["candidate_gain_bits"] for row in rows]
    pair_counts = [row["pair_substitution_count"] for row in rows]
    positive_pair_counts = [row["positive_pair_count"] for row in rows]
    positive_single_counts = [row["positive_single_count"] for row in rows]
    cumulative_gain = sum(gains)
    selector_floor_total = sum(row["selector_floor_bits"] for row in rows)
    last = rows[-1]
    stop_rule = {
        "all_post_targetmax_source_passes_below_0_001_bits": all(
            gain < 0.001 for gain in gains
        ),
        "cumulative_post_targetmax_gain_below_0_0005_bits": cumulative_gain < 0.0005,
        "positive_pair_counts_nonincreasing": all(
            later <= earlier
            for earlier, later in zip(positive_pair_counts, positive_pair_counts[1:])
        ),
        "positive_single_counts_nonincreasing": all(
            later <= earlier
            for earlier, later in zip(positive_single_counts, positive_single_counts[1:])
        ),
        "same_pair_search_size_each_pass": len(set(pair_counts)) == 1,
        "last_gain_smaller_than_pair_selector_floor": (
            last["candidate_gain_bits"] < last["selector_floor_bits"]
        ),
        "cumulative_gain_smaller_than_selector_floor_total": (
            cumulative_gain < selector_floor_total
        ),
    }
    stop_mainline = all(stop_rule.values())
    return {
        "schema": "post_targetmax_source_substitution_stop_audit.v1",
        "classification": (
            "post_targetmax_source_substitution_micro_frontier_stop_mainline"
            if stop_mainline
            else "post_targetmax_source_substitution_frontier_continue"
        ),
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {name: rel(path) for name, path in GATES},
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "does_not_search_third_post_targetmax_source_pass": True,
            "fixed_segmentation": True,
            "fixed_copy_lengths": True,
            "same_chunk_source_choices_only": True,
            "source_substitution_passes_considered": [row["name"] for row in rows],
        },
        "rows": rows,
        "summary": {
            "current_compression_bound_bits": rows[-1]["candidate_total_bits"],
            "post_targetmax_pass_gains_bits": gains,
            "post_targetmax_cumulative_gain_bits": cumulative_gain,
            "last_pass_gain_bits": last["candidate_gain_bits"],
            "last_pass_positive_pair_fraction": last["positive_pair_fraction"],
            "last_pass_pair_candidates_per_gain_bit": last[
                "pair_candidates_per_gain_bit"
            ],
            "minimum_pair_selector_floor_bits": last["selector_floor_bits"],
            "minimum_pair_selector_floor_minus_last_gain_bits": last[
                "selector_floor_minus_gain_bits"
            ],
            "selector_floor_total_bits": selector_floor_total,
            "selector_floor_total_minus_cumulative_gain_bits": (
                selector_floor_total - cumulative_gain
            ),
            "stop_rule": stop_rule,
            "stop_mainline": stop_mainline,
            "interpretation": (
                "The post-target-max source frontier is positive only at a "
                "microscopic compression-bound scale. Under explicit selector-cost "
                "sanity checks, continuing same-chunk source passes is no longer "
                "a mainline mechanical-explanation path."
            ),
        },
        "decision": {
            "compression_bound_status": "8156_049986_retained_as_current_bound",
            "generation_explanation_status": (
                "post_targetmax_same_chunk_source_micro_sweeps_no_longer_mainline"
            ),
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "next_work": (
                "Return to structural source/length parser, holdout-predictive "
                "parser improvement, or row0-origin evidence instead of another "
                "unpriced same-chunk source-substitution pass."
            ),
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (
        TEST_RESULTS / "58_post_targetmax_source_substitution_stop_audit.json"
    ).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = result["summary"]
    lines = [
        "# Post-Target-Max Source Substitution Stop Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gates 56 and 57 found only microscopic post-target-max same-chunk",
        "source-substitution gains. This audit applies an explicit stop rule",
        "and does not run a third post-target-max source-substitution pass.",
        "",
        "## Pass Ledger",
        "",
        "| Gate | Active bits | Candidate bits | Gain bits | Positive singles | Positive pairs | Pair candidates | Selector floor bits |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['name']}` | `{row['active_total_bits']:.6f}` | "
            f"`{row['candidate_total_bits']:.6f}` | "
            f"`{row['candidate_gain_bits']:+.6f}` | "
            f"`{row['positive_single_count']}` | `{row['positive_pair_count']}` | "
            f"`{row['pair_substitution_count']}` | `{row['selector_floor_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Stop Rule",
            "",
            f"- Pass gains: `{summary['post_targetmax_pass_gains_bits']}`.",
            f"- Cumulative gain: `{summary['post_targetmax_cumulative_gain_bits']:.6f}` bits.",
            f"- Last pass positive-pair fraction: `{summary['last_pass_positive_pair_fraction']:.6f}`.",
            f"- Last pass pair candidates per gained bit: `{summary['last_pass_pair_candidates_per_gain_bit']:.3f}`.",
            f"- Minimum pair-selector floor for the last pass: `{summary['minimum_pair_selector_floor_bits']:.3f}` bits.",
            f"- Selector floor minus last gain: `{summary['minimum_pair_selector_floor_minus_last_gain_bits']:.3f}` bits.",
            f"- Total selector floor minus cumulative gain: `{summary['selector_floor_total_minus_cumulative_gain_bits']:.3f}` bits.",
            f"- Stop rule booleans: `{summary['stop_rule']}`.",
            "",
            "## Decision",
            "",
            f"- Current compression bound remains `{summary['current_compression_bound_bits']:.6f}` bits.",
            "- Do not treat further unpriced same-chunk source substitutions as a mainline generation search.",
            "- Future progress should require structural source/length derivation, holdout-predictive parser improvement, or row0-origin evidence.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- Segmentation and copy lengths remain fixed in all source-substitution passes considered.",
            "- This audit does not emit a new formula.",
        ]
    )
    (
        TEST_RESULTS / "58_post_targetmax_source_substitution_stop_audit.md"
    ).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
