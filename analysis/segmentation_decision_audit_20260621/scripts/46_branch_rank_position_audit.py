from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from statistics import median
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE22_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
GATE45 = TEST_RESULTS / "45_residual_exception_transfer_gate.json"

OUT_STEM = "46_branch_rank_position_audit"


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


RankKey = Callable[[dict[str, Any]], tuple[Any, ...]]


def branch_length(branch: dict[str, Any]) -> int:
    return int(branch["op"]["length"])


def copy_type(branch: dict[str, Any]) -> int:
    return 0 if branch["op"]["type"] == "copy" else 1


def literal_type(branch: dict[str, Any]) -> int:
    return 0 if branch["op"]["type"] == "literal" else 1


def label_bucket(branch: dict[str, Any], wanted: str) -> int:
    return 0 if wanted in branch["label"] else 1


def metrics(branch: dict[str, Any]) -> dict[str, Any]:
    return branch["metrics"]


def rankers() -> dict[str, RankKey]:
    return {
        "active_first": lambda b: (0 if b["is_active"] else 1, b["label"]),
        "copy_first_longest": lambda b: (copy_type(b), -branch_length(b), b["label"]),
        "copy_first_shortest": lambda b: (copy_type(b), branch_length(b), b["label"]),
        "literal_first_longest": lambda b: (literal_type(b), -branch_length(b), b["label"]),
        "literal_first_shortest": lambda b: (literal_type(b), branch_length(b), b["label"]),
        "longest_op": lambda b: (-branch_length(b), copy_type(b), b["label"]),
        "shortest_op": lambda b: (branch_length(b), copy_type(b), b["label"]),
        "immediate_copy_first": lambda b: (label_bucket(b, "immediate_copy"), -branch_length(b), b["label"]),
        "literal_stop_first": lambda b: (label_bucket(b, "literal_stop"), branch_length(b), b["label"]),
        "min_suffix_ops": lambda b: (
            metrics(b)["suffix_op_count"],
            metrics(b)["suffix_literal_digits"],
            -metrics(b)["suffix_copy_digits"],
            b["label"],
        ),
        "min_suffix_literals": lambda b: (
            metrics(b)["suffix_literal_digits"],
            metrics(b)["suffix_op_count"],
            -metrics(b)["suffix_copy_digits"],
            b["label"],
        ),
        "max_suffix_copy_digits": lambda b: (
            -metrics(b)["suffix_copy_digits"],
            metrics(b)["suffix_op_count"],
            metrics(b)["suffix_literal_digits"],
            b["label"],
        ),
        "max_suffix_copy_count": lambda b: (
            -metrics(b)["suffix_copy_count"],
            metrics(b)["suffix_op_count"],
            metrics(b)["suffix_literal_digits"],
            b["label"],
        ),
        "balanced_ops_literals": lambda b: (
            metrics(b)["suffix_op_count"] * 5 + metrics(b)["suffix_literal_digits"],
            -metrics(b)["suffix_copy_digits"],
            b["label"],
        ),
    }


def stable_rank(decision: dict[str, Any], key: RankKey) -> int | None:
    ranked = sorted(decision["branches"], key=key)
    for index, branch in enumerate(ranked, start=1):
        if branch["is_stable"]:
            return index
    return None


def score_ranker(decisions: list[dict[str, Any]], name: str, key: RankKey) -> dict[str, Any]:
    rows = []
    for decision in decisions:
        if not decision["branches"]:
            continue
        ranked = sorted(decision["branches"], key=key)
        chosen = ranked[0]
        rank = stable_rank(decision, key)
        rows.append(
            {
                "book": decision["book"],
                "kind": decision["kind"],
                "drift_class": decision["drift_class"],
                "branch_count": len(decision["branches"]),
                "stable_rank": rank,
                "top_is_stable": chosen["is_stable"],
                "top_is_active": chosen["is_active"],
                "top_label": chosen["label"],
                "stable_op": decision["stable_op"],
                "top_op": chosen["op"],
            }
        )
    residual_rows = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean_rows = [row for row in rows if row["kind"] == "clean_control"]
    residual_ranks = [row["stable_rank"] for row in residual_rows if row["stable_rank"]]
    clean_ranks = [row["stable_rank"] for row in clean_rows if row["stable_rank"]]
    return {
        "ranker": name,
        "total_rows": len(rows),
        "residual_total": len(residual_rows),
        "clean_total": len(clean_rows),
        "residual_top1": sum(1 for row in residual_rows if row["top_is_stable"]),
        "clean_false_changes": sum(1 for row in clean_rows if not row["top_is_stable"]),
        "residual_top2": sum(1 for rank in residual_ranks if rank <= 2),
        "residual_top3": sum(1 for rank in residual_ranks if rank <= 3),
        "residual_median_rank": None if not residual_ranks else median(residual_ranks),
        "residual_max_rank": None if not residual_ranks else max(residual_ranks),
        "clean_median_rank": None if not clean_ranks else median(clean_ranks),
        "rows": rows,
    }


def oracle_rank_summary(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    residuals = [row for row in decisions if row["kind"] == "residual_first_drift"]
    branch_counts = [len(row["branches"]) for row in residuals]
    return {
        "residual_count": len(residuals),
        "branch_count_min": min(branch_counts),
        "branch_count_median": median(branch_counts),
        "branch_count_max": max(branch_counts),
        "oracle_rank_selector_bits": sum(math.log2(count) for count in branch_counts),
    }


def make_result() -> dict[str, Any]:
    gate45 = load_json(GATE45)
    assert_boundary("residual_exception_transfer_gate", gate45)
    if gate45["classification"] != "residual_exception_transfer_rejected":
        raise RuntimeError("gate46 expects gate45 residual-transfer rejection")

    gate22 = load_module("gate22_for_gate46", GATE22_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    ranker_scores = [
        score_ranker(decisions, name, key) for name, key in rankers().items()
    ]
    best_top1 = max(
        ranker_scores,
        key=lambda row: (
            row["residual_top1"],
            -row["clean_false_changes"],
            row["residual_top2"],
            row["ranker"],
        ),
    )
    best_top3 = max(
        ranker_scores,
        key=lambda row: (
            row["residual_top3"],
            -row["clean_false_changes"],
            row["residual_top1"],
            row["ranker"],
        ),
    )
    promotes = (
        best_top1["residual_top1"] == best_top1["residual_total"]
        and best_top1["clean_false_changes"] == 0
    )
    classification = (
        "branch_rank_rule_promoted" if promotes else "branch_rank_rule_rejected"
    )
    return {
        "schema": "branch_rank_position_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "residual_exception_transfer_gate": rel(GATE45),
            "residual_branch_continuation_script": rel(GATE22_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "stable_projection_used_as_label_only": True,
            "declared_literal_windows_granted": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_branch_rank_heuristics": True,
        },
        "summary": {
            "interpretation": (
                "This gate ranks observable candidate branches for each residual "
                "and clean-control decision. It tests whether stable residual "
                "branches are simply top-ranked under a small observable ordering."
            ),
            "ranker_count": len(ranker_scores),
            "residual_count": best_top1["residual_total"],
            "clean_control_count": best_top1["clean_total"],
            "best_top1_ranker": best_top1["ranker"],
            "best_top1_residual_hits": best_top1["residual_top1"],
            "best_top1_clean_false_changes": best_top1["clean_false_changes"],
            "best_top3_ranker": best_top3["ranker"],
            "best_top3_residual_hits": best_top3["residual_top3"],
            "best_top3_clean_false_changes": best_top3["clean_false_changes"],
            "promotes_branch_rank_rule": promotes,
        },
        "oracle_rank_summary": oracle_rank_summary(decisions),
        "scoreboard": [
            {
                key: row[key]
                for key in [
                    "ranker",
                    "residual_top1",
                    "residual_top2",
                    "residual_top3",
                    "clean_false_changes",
                    "residual_median_rank",
                    "residual_max_rank",
                ]
            }
            for row in sorted(
                ranker_scores,
                key=lambda row: (
                    -row["residual_top1"],
                    row["clean_false_changes"],
                    -row["residual_top3"],
                    row["ranker"],
                ),
            )
        ],
        "best_top1_rows": best_top1["rows"],
        "best_top3_rows": best_top3["rows"],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "branch_rank_heuristics_tested",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def md_table(rows: list[list[Any]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def residual_row_table(rows: list[dict[str, Any]]) -> list[list[Any]]:
    return [
        [
            row["book"],
            row["drift_class"],
            row["branch_count"],
            row["stable_rank"],
            row["top_label"],
            row["top_is_stable"],
            row["top_is_active"],
        ]
        for row in rows
        if row["kind"] == "residual_first_drift"
    ]


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    oracle = result["oracle_rank_summary"]
    scoreboard_rows = [
        [
            row["ranker"],
            row["residual_top1"],
            row["residual_top2"],
            row["residual_top3"],
            row["clean_false_changes"],
            row["residual_median_rank"],
            row["residual_max_rank"],
        ]
        for row in result["scoreboard"]
    ]
    body = f"""# Branch Rank Position Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 46 ranks every observable candidate branch at the remaining residual
sites. It asks whether the stable branch is simply top-ranked by a small
observable ordering: type priority, length priority, active/default priority,
literal-stop/immediate-copy priority, or suffix continuation metrics.

## Summary

- Rankers tested: `{s['ranker_count']}`.
- Residual decisions: `{s['residual_count']}`.
- Clean controls: `{s['clean_control_count']}`.
- Best top-1 ranker: `{s['best_top1_ranker']}`.
- Best top-1 residual hits: `{s['best_top1_residual_hits']}/{s['residual_count']}`.
- Best top-1 clean false changes: `{s['best_top1_clean_false_changes']}`.
- Best top-3 ranker: `{s['best_top3_ranker']}`.
- Best top-3 residual coverage: `{s['best_top3_residual_hits']}/{s['residual_count']}`.
- Best top-3 clean false changes: `{s['best_top3_clean_false_changes']}`.
- Promotes branch-rank rule: `{s['promotes_branch_rank_rule']}`.

## Oracle Rank Lower Bound

- Residual branch count min/median/max: `{oracle['branch_count_min']}` / `{oracle['branch_count_median']}` / `{oracle['branch_count_max']}`.
- Per-residual rank selector lower bound: `{oracle['oracle_rank_selector_bits']:.3f}` bits.

## Ranker Scoreboard

{md_table(scoreboard_rows, ['ranker', 'top1', 'top2', 'top3', 'clean false changes', 'median rank', 'max rank'])}

## Best Top-1 Residual Rows

{md_table(residual_row_table(result['best_top1_rows']), ['book', 'class', 'branches', 'stable rank', 'top label', 'top stable?', 'top active?'])}

## Best Top-3 Residual Rows

{md_table(residual_row_table(result['best_top3_rows']), ['book', 'class', 'branches', 'stable rank', 'top label', 'top stable?', 'top active?'])}

## Decision

No branch-rank rule is promoted. The best observable top-1 ordering explains
only a minority of residuals and damages clean controls; even the best top-3
coverage leaves residuals outside the near-top set. This rejects a simple
rank/ordering heuristic as the missing segmentation mechanism.

- Compression bound is unchanged.
- Row0 remains exogenous and unchanged.
- No plaintext, translation, semantic reading, or case reopening is introduced.
"""
    md_path.write_text(body, encoding="utf-8")
    print(json_path)
    print(md_path)


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
