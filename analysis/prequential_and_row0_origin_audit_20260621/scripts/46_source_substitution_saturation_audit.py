from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATES = [
    ("source_path_formula", TEST_RESULTS / "41_full_corpus_source_path_formula_gate.json"),
    (
        "source_substitution_frontier",
        TEST_RESULTS / "42_full_corpus_source_substitution_frontier_gate.json",
    ),
    (
        "source_substitution_second_pass",
        TEST_RESULTS / "43_full_corpus_source_substitution_second_pass_gate.json",
    ),
    (
        "source_substitution_third_pass",
        TEST_RESULTS / "44_full_corpus_source_substitution_third_pass_gate.json",
    ),
    (
        "source_substitution_fourth_pass",
        TEST_RESULTS / "45_full_corpus_source_substitution_fourth_pass_gate.json",
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
    if decision.get("row0_origin_status") != "unchanged_exogenous":
        raise RuntimeError(f"{name} changed row0 origin status")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext status")


def gate_row(name: str, path: Path, data: dict[str, Any]) -> dict[str, Any]:
    summary = data["summary"]
    row = {
        "name": name,
        "source": rel(path),
        "classification": data["classification"],
        "active_total_bits": float(summary["active_total_bits"]),
        "candidate_total_bits": float(summary["candidate_total_bits"]),
        "candidate_gain_bits": float(summary["candidate_gain_bits"]),
        "copy_event_count": int(summary["copy_event_count"]),
        "active_copy_source_bits": float(summary["active_copy_source_bits"]),
        "candidate_copy_source_bits": float(summary["candidate_copy_source_bits"]),
    }
    for key in [
        "single_substitution_count",
        "positive_single_count",
        "pair_substitution_count",
        "positive_pair_count",
        "best_arity",
    ]:
        if key in summary:
            row[key] = int(summary[key])
    if "pair_substitution_count" in row:
        row["positive_pair_fraction"] = (
            row["positive_pair_count"] / row["pair_substitution_count"]
        )
        row["selector_floor_bits"] = math.log2(row["pair_substitution_count"])
        row["selector_floor_minus_gain_bits"] = (
            row["selector_floor_bits"] - row["candidate_gain_bits"]
        )
        row["pair_candidates_per_gain_bit"] = (
            row["pair_substitution_count"] / row["candidate_gain_bits"]
            if row["candidate_gain_bits"] > 0
            else math.inf
        )
    return row


def make_result() -> dict[str, Any]:
    rows = []
    for name, path in GATES:
        data = load_json(path)
        assert_boundary(name, data)
        rows.append(gate_row(name, path, data))

    substitution_rows = rows[1:]
    microscopic_tail = substitution_rows[1:]
    gains = [row["candidate_gain_bits"] for row in substitution_rows]
    tail_gains = [row["candidate_gain_bits"] for row in microscopic_tail]
    pair_counts = [row["pair_substitution_count"] for row in substitution_rows]
    positive_pair_counts = [row["positive_pair_count"] for row in substitution_rows]
    positive_single_counts = [row["positive_single_count"] for row in substitution_rows]
    last = substitution_rows[-1]

    selector_floor_cumulative_tail = sum(row["selector_floor_bits"] for row in microscopic_tail)
    cumulative_tail_gain = sum(tail_gains)
    stop_rule = {
        "last_three_passes_all_below_0_001_bits": all(gain < 0.001 for gain in tail_gains),
        "last_three_cumulative_gain_below_0_002_bits": cumulative_tail_gain < 0.002,
        "positive_pair_counts_strictly_decrease": all(
            later < earlier
            for earlier, later in zip(positive_pair_counts, positive_pair_counts[1:])
        ),
        "positive_single_counts_strictly_decrease_after_second_pass": all(
            later < earlier
            for earlier, later in zip(positive_single_counts[1:], positive_single_counts[2:])
        ),
        "same_pair_search_size_each_pass": len(set(pair_counts)) == 1,
        "last_gain_smaller_than_minimum_pair_selector_floor": (
            last["candidate_gain_bits"] < last["selector_floor_bits"]
        ),
        "tail_gain_smaller_than_minimum_tail_selector_floor": (
            cumulative_tail_gain < selector_floor_cumulative_tail
        ),
    }
    frontier_saturated = all(stop_rule.values())

    return {
        "schema": "source_substitution_saturation_audit.v1",
        "classification": (
            "local_source_substitution_frontier_saturated_stop_mainline"
            if frontier_saturated
            else "local_source_substitution_frontier_not_saturated"
        ),
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {name: rel(path) for name, path in GATES},
        "scope": {
            "analysis_only": True,
            "new_formula_emitted": False,
            "source_substitution_passes_considered": [row["name"] for row in substitution_rows],
            "fixed_segmentation": True,
            "fixed_copy_lengths": True,
            "same_chunk_source_choices_only": True,
            "does_not_search_fifth_pass": True,
        },
        "rows": rows,
        "summary": {
            "active_bound_before_source_path_bits": rows[0]["active_total_bits"],
            "current_compression_bound_bits": last["candidate_total_bits"],
            "source_path_gain_bits": rows[0]["candidate_gain_bits"],
            "first_substitution_frontier_gain_bits": substitution_rows[0][
                "candidate_gain_bits"
            ],
            "tail_pass_gains_bits": tail_gains,
            "tail_cumulative_gain_bits": cumulative_tail_gain,
            "last_pass_gain_bits": last["candidate_gain_bits"],
            "last_pass_positive_pair_fraction": last["positive_pair_fraction"],
            "last_pass_pair_candidates_per_gain_bit": last[
                "pair_candidates_per_gain_bit"
            ],
            "minimum_pair_selector_floor_bits": last["selector_floor_bits"],
            "minimum_pair_selector_floor_minus_last_gain_bits": last[
                "selector_floor_minus_gain_bits"
            ],
            "tail_selector_floor_bits": selector_floor_cumulative_tail,
            "tail_selector_floor_minus_tail_gain_bits": (
                selector_floor_cumulative_tail - cumulative_tail_gain
            ),
            "stop_rule": stop_rule,
            "frontier_saturated": frontier_saturated,
        },
        "decision": {
            "compression_bound_status": "8160_825608_retained_as_current_local_source_bound",
            "generation_explanation_status": (
                "local_same_chunk_source_substitution_no_longer_mainline"
            ),
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "next_work": (
                "Future progress should require a structural source/length "
                "derivation, holdout-predictive parser improvement, or row0-origin "
                "evidence rather than repeated unpriced local source edits."
            ),
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "46_source_substitution_saturation_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = result["summary"]
    lines = [
        "# Source Substitution Saturation Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This audit stops treating repeated same-chunk source substitutions as a",
        "mainline generation search. It reads gates 41-45 and applies an explicit",
        "stop rule to the local fixed-recipe source frontier. No fifth pass is run.",
        "",
        "## Pass Ledger",
        "",
        "| Gate | Active bits | Candidate bits | Gain bits | Positive singles | Positive pairs | Pair candidates | Selector floor bits |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["rows"]:
        positive_singles = row.get("positive_single_count", "")
        positive_pairs = row.get("positive_pair_count", "")
        pair_count = row.get("pair_substitution_count", "")
        selector = row.get("selector_floor_bits")
        selector_text = f"`{selector:.3f}`" if selector is not None else ""
        lines.append(
            f"| `{row['name']}` | `{row['active_total_bits']:.6f}` | "
            f"`{row['candidate_total_bits']:.6f}` | "
            f"`{row['candidate_gain_bits']:+.6f}` | `{positive_singles}` | "
            f"`{positive_pairs}` | `{pair_count}` | {selector_text} |"
        )

    lines.extend(
        [
            "",
            "## Stop Rule",
            "",
            f"- Last three pass gains: `{summary['tail_pass_gains_bits']}`.",
            f"- Last three cumulative gain: `{summary['tail_cumulative_gain_bits']:.6f}` bits.",
            f"- Last pass positive-pair fraction: `{summary['last_pass_positive_pair_fraction']:.6f}`.",
            f"- Last pass pair candidates per gained bit: `{summary['last_pass_pair_candidates_per_gain_bit']:.3f}`.",
            f"- Minimum pair-selector floor for the last pass: `{summary['minimum_pair_selector_floor_bits']:.3f}` bits.",
            f"- Selector floor minus last gain: `{summary['minimum_pair_selector_floor_minus_last_gain_bits']:.3f}` bits.",
            f"- Tail selector floor minus tail gain: `{summary['tail_selector_floor_minus_tail_gain_bits']:.3f}` bits.",
            f"- Stop rule booleans: `{summary['stop_rule']}`.",
            "",
            "## Decision",
            "",
            f"- Current local-source compression bound: `{summary['current_compression_bound_bits']:.6f}` bits.",
            "- The local same-chunk single/pair source frontier is saturated as a mainline path.",
            "- This is a falsification of continued unpriced local-source micro-sweeps as generation evidence, not a new formula claim.",
            "- Future progress should require structural source/length derivation, holdout-predictive parser improvement, or row0-origin evidence.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- Segmentation and copy lengths remain fixed in all source-substitution passes considered.",
            "- This audit does not search a fifth pass or emit a new formula.",
        ]
    )
    (TEST_RESULTS / "46_source_substitution_saturation_audit.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
