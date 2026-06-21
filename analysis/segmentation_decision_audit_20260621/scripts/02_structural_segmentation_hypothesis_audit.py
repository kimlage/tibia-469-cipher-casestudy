from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

TRACE = TEST_RESULTS / "01_segmentation_decision_trace.json"
OUT_STEM = "02_structural_segmentation_hypothesis_audit"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


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
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def score_boolean(rows: list[dict[str, Any]], name: str, predicate: Callable[[dict[str, Any]], bool], boundary: str) -> dict[str, Any]:
    hits = [row for row in rows if predicate(row)]
    failures = [row for row in rows if not predicate(row)]
    return {
        "hypothesis": name,
        "hits": len(hits),
        "total": len(rows),
        "coverage": len(hits) / len(rows),
        "misses": len(failures),
        "boundary": boundary,
        "promoted": len(hits) == len(rows) and boundary == "source_free",
        "sample_failures": [
            {
                "book": row["book"],
                "op_index": row["op_index"],
                "projection_copy_index": row["projection_copy_index"],
                "declared_source": row["declared_source"],
                "declared_length": row["declared_length"],
                "decoder_max": row["decoder_max"],
                "candidate_pair_count": row["candidate_pair_count"],
            }
            for row in failures[:10]
        ],
    }


def score_source_policy(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    hits = 0
    failures = []
    for row in rows:
        if row["declared_length"] != row["all_source_max_length"]:
            ok = False
            predicted = None
        elif policy == "earliest_global_max_source":
            predicted = row["global_max_earliest_source"]
            ok = row["declared_source"] == predicted
        elif policy == "latest_global_max_source":
            predicted = row["global_max_latest_source"]
            ok = row["declared_source"] == predicted
        else:
            raise ValueError(policy)
        if ok:
            hits += 1
        elif len(failures) < 10:
            failures.append(
                {
                    "book": row["book"],
                    "op_index": row["op_index"],
                    "projection_copy_index": row["projection_copy_index"],
                    "declared_source": row["declared_source"],
                    "predicted_source": predicted,
                    "declared_length": row["declared_length"],
                    "all_source_max_length": row["all_source_max_length"],
                    "global_max_length_source_count": row[
                        "global_max_length_source_count"
                    ],
                }
            )
    return {
        "hypothesis": policy,
        "hits": hits,
        "total": len(rows),
        "coverage": hits / len(rows),
        "misses": len(rows) - hits,
        "boundary": "target_text_dependent_source_tie_policy",
        "promoted": False,
        "sample_failures": failures,
    }


def score_unique_global_max(rows: list[dict[str, Any]]) -> dict[str, Any]:
    covered = [
        row
        for row in rows
        if row["declared_length"] == row["all_source_max_length"]
        and row["global_max_length_source_count"] == 1
    ]
    hits = [row for row in covered if row["declared_source_is_unique_global_max"]]
    return {
        "hypothesis": "unique_global_max_source_forces_joint_pair",
        "covered_rows": len(covered),
        "hits_on_covered_rows": len(hits),
        "total": len(rows),
        "coverage_of_all_rows": len(hits) / len(rows),
        "covered_accuracy": None if not covered else len(hits) / len(covered),
        "boundary": "partial_target_text_dependent_forcing",
        "promoted": False,
    }


def prequential_tie_policy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    policies = {
        "earliest_global_max_source": lambda row: row["declared_source"]
        == row["global_max_earliest_source"]
        and row["declared_length"] == row["all_source_max_length"],
        "latest_global_max_source": lambda row: row["declared_source"]
        == row["global_max_latest_source"]
        and row["declared_length"] == row["all_source_max_length"],
    }
    results = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        if not train or not test:
            continue
        train_scores = {
            name: sum(1 for row in train if fn(row)) / len(train)
            for name, fn in policies.items()
        }
        selected = max(train_scores, key=lambda name: (train_scores[name], name))
        test_hits = sum(1 for row in test if policies[selected](row))
        oracle_test_hits = max(sum(1 for row in test if fn(row)) for fn in policies.values())
        results.append(
            {
                "cutoff_book": cutoff,
                "train_rows": len(train),
                "test_rows": len(test),
                "selected_policy": selected,
                "train_coverage": train_scores[selected],
                "test_hits": test_hits,
                "test_coverage": test_hits / len(test),
                "oracle_test_hits": oracle_test_hits,
                "oracle_test_coverage": oracle_test_hits / len(test),
                "selected_matches_oracle": test_hits == oracle_test_hits,
            }
        )
    return results


def make_result() -> dict[str, Any]:
    trace = load_json(TRACE)
    assert_boundary("segmentation_decision_trace", trace)
    rows = trace["copy_trace_rows"]

    hypothesis_rows = [
        score_boolean(
            rows,
            "declared_source_target_match_max_length",
            lambda row: row["declared_is_max"],
            "declared_source_and_target_text_dependent",
        ),
        score_boolean(
            rows,
            "global_longest_target_match_pair",
            lambda row: row["declared_pair_is_global_max_length"],
            "target_text_dependent_pair_oracle",
        ),
        score_source_policy(rows, "earliest_global_max_source"),
        score_source_policy(rows, "latest_global_max_source"),
        score_boolean(
            rows,
            "copy_preserves_recurrent_next_boundary",
            lambda row: row["preserves_recurrent_boundary"],
            "target_text_dependent_boundary_clue",
        ),
        score_boolean(
            rows,
            "stop_before_max_protects_literal_payload",
            lambda row: row["extend_to_max_changes_literal_payload"],
            "rejected_control",
        ),
        score_boolean(
            rows,
            "declared_boundary_has_more_future_copy_options_than_max_boundary",
            lambda row: row["declared_boundary_candidate_pair_count"]
            > row["max_boundary_candidate_pair_count"],
            "target_text_dependent_boundary_clue",
        ),
    ]
    unique = score_unique_global_max(rows)
    preq = prequential_tie_policy(rows)

    target_text_max = next(
        row for row in hypothesis_rows if row["hypothesis"] == "global_longest_target_match_pair"
    )
    best_source_policy = max(
        [
            row
            for row in hypothesis_rows
            if row["hypothesis"]
            in {"earliest_global_max_source", "latest_global_max_source"}
        ],
        key=lambda row: row["hits"],
    )
    promotes_source_free_rule = False
    promotes_target_text_parser_clue = (
        target_text_max["hits"] >= 0.99 * target_text_max["total"]
        and best_source_policy["hits"] == target_text_max["hits"]
    )
    classification = "target_text_longest_earliest_parser_clue_not_source_free_generator"
    hard_failures = target_text_max["sample_failures"]
    exception_rows = [
        {
            "book": row["book"],
            "op_index": row["op_index"],
            "projection_copy_index": row["projection_copy_index"],
            "target_start": row["target_start"],
            "declared_source": row["declared_source"],
            "declared_length": row["declared_length"],
            "decoder_max": row["decoder_max"],
            "all_source_max_length": row["all_source_max_length"],
            "candidate_pair_count": row["candidate_pair_count"],
            "extend_to_max_extra_digits": row["extend_to_max_extra_digits"],
            "declared_boundary_candidate_pair_count": row[
                "declared_boundary_candidate_pair_count"
            ],
            "max_boundary_candidate_pair_count": row[
                "max_boundary_candidate_pair_count"
            ],
        }
        for row in rows
        if not row["declared_pair_is_global_max_length"]
    ]
    random_global_max_source_expected_hits = sum(
        1.0 / row["global_max_length_source_count"]
        for row in rows
        if row["declared_pair_is_global_max_length"]
    )

    return {
        "schema": "structural_segmentation_hypothesis_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {"segmentation_decision_trace": rel(TRACE)},
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "tests_target_text_dependent_structural_rules": True,
            "does_not_emit_formula": True,
        },
        "summary": {
            "copy_count": len(rows),
            "target_text_global_longest_pair_hits": target_text_max["hits"],
            "target_text_global_longest_pair_total": target_text_max["total"],
            "target_text_global_longest_pair_coverage": target_text_max["coverage"],
            "best_source_tie_policy": best_source_policy["hypothesis"],
            "best_source_tie_policy_hits": best_source_policy["hits"],
            "best_source_tie_policy_coverage": best_source_policy["coverage"],
            "random_global_max_source_expected_hits": random_global_max_source_expected_hits,
            "random_global_max_source_expected_coverage": random_global_max_source_expected_hits
            / len(rows),
            "unique_global_max_source_rows": unique["covered_rows"],
            "unique_global_max_source_coverage": unique["coverage_of_all_rows"],
            "recurrent_boundary_hits": next(
                row
                for row in hypothesis_rows
                if row["hypothesis"] == "copy_preserves_recurrent_next_boundary"
            )["hits"],
            "literal_payload_protection_hits": next(
                row
                for row in hypothesis_rows
                if row["hypothesis"] == "stop_before_max_protects_literal_payload"
            )["hits"],
            "prequential_tie_policy_cells": len(preq),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "promotes_target_text_parser_clue": promotes_target_text_parser_clue,
            "promotes_source_free_segmentation_rule": promotes_source_free_rule,
            "interpretation": (
                "The strongest structural finding is that target-text-aware "
                "longest-copy segmentation with earliest-source tie recovers "
                "nearly every copy pair in the stable projection. This is a "
                "real parser clue for segmentation, but not a source-free "
                "generator: it requires the target suffix being parsed and "
                "still has one exception. Literal-protection and recurrent-"
                "boundary shortcuts do not explain the decision trace."
            ),
        },
        "hypothesis_rows": hypothesis_rows,
        "unique_global_max_source": unique,
        "prequential_tie_policy_rows": preq,
        "exception_rows": exception_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "target_text_max_boundary_clue_not_generator",
            "source_length_dependency_status": "copy_pairs_mostly_reduced_if_target_text_is_granted_source_free_dependency_retained",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Structural Segmentation Hypothesis Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "This gate tests structural segmentation hypotheses against the",
        "decision trace. It is not a bit sweep and it does not search",
        "plaintext.",
        "",
        "## Hypothesis Scoreboard",
        "",
        "| Hypothesis | Hits | Coverage | Boundary | Source-free promoted |",
        "|---|---:|---:|---|---|",
    ]
    for row in result["hypothesis_rows"]:
        lines.append(
            f"| `{row['hypothesis']}` | `{row['hits']}/{row['total']}` | "
            f"`{row['coverage']:.3f}` | `{row['boundary']}` | "
            f"`{row['promoted']}` |"
        )
    unique = result["unique_global_max_source"]
    lines.extend(
        [
            "",
            "## Source Tie Boundary",
            "",
            f"- Unique global-max source rows: `{unique['covered_rows']}/{unique['total']}`.",
            f"- Best source tie policy: `{s['best_source_tie_policy']}` = "
            f"`{s['best_source_tie_policy_hits']}/{s['copy_count']}`.",
            f"- Random global-max source expected hits: "
            f"`{s['random_global_max_source_expected_hits']:.3f}/{s['copy_count']}`.",
            f"- Prequential tie-policy cells matching suffix oracle: "
            f"`{s['prequential_selected_matches_oracle_cells']}/{s['prequential_tie_policy_cells']}`.",
            "",
            "## Exception Rows",
            "",
            "| Book | Op | Projection copy | Declared length | Max length | Candidate pairs | Declared boundary pairs | Max boundary pairs |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["exception_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['projection_copy_index']}` | "
            f"`{row['declared_length']}` | `{row['all_source_max_length']}` | "
            f"`{row['candidate_pair_count']}` | "
            f"`{row['declared_boundary_candidate_pair_count']}` | "
            f"`{row['max_boundary_candidate_pair_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes target-text parser clue: `{s['promotes_target_text_parser_clue']}`.",
            f"- Promotes source-free segmentation rule: `{s['promotes_source_free_segmentation_rule']}`.",
            f"- {s['interpretation']}",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
