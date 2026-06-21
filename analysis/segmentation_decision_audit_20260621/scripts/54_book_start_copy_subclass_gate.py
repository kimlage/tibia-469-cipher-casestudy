from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE41 = TEST_RESULTS / "41_latent_state_lookup_cost_gate.json"
GATE50_SCRIPT = HERE / "scripts" / "50_source_interval_context_gate.py"
GATE50 = TEST_RESULTS / "50_source_interval_context_gate.json"
GATE53 = TEST_RESULTS / "53_source_interval_cost_gate.json"

OUT_STEM = "54_book_start_copy_subclass_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 1000
RANDOM_SEED = 46954
BIG = 10**9


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


def op_key(op: dict[str, Any]) -> tuple[Any, ...]:
    return (op["type"], int(op["target_start"]), int(op["length"]), op.get("source"))


def copy_branches(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        branch
        for branch in row["branches"]
        if branch["branch"]["op"]["type"] == "copy"
        and branch["features"]["source"] is not None
    ]


def literal_active(row: dict[str, Any]) -> bool:
    return row["active_op"]["type"] == "literal"


def choose_copy(row: dict[str, Any], policy: str) -> dict[str, Any] | None:
    candidates = copy_branches(row)
    if not candidates:
        return None
    if policy == "max_copy_length":
        return max(
            candidates,
            key=lambda item: (
                item["features"]["length"],
                item["features"]["payload_occurrences"],
                -item["features"]["source_target_interval_distance"],
                item["branch"]["label"],
            ),
        )
    if policy == "min_interval_distance":
        return max(
            candidates,
            key=lambda item: (
                -item["features"]["source_target_interval_distance"],
                item["features"]["payload_occurrences"],
                item["features"]["length"],
                item["branch"]["label"],
            ),
        )
    if policy == "max_payload_occurrences":
        return max(
            candidates,
            key=lambda item: (
                item["features"]["payload_occurrences"],
                item["features"]["length"],
                -item["features"]["source_target_interval_distance"],
                item["branch"]["label"],
            ),
        )
    if policy == "min_start_distance":
        return max(
            candidates,
            key=lambda item: (
                -item["features"]["source_target_start_distance"],
                item["features"]["payload_occurrences"],
                item["features"]["length"],
                item["branch"]["label"],
            ),
        )
    if policy == "min_end_distance":
        return max(
            candidates,
            key=lambda item: (
                -item["features"]["source_target_end_distance"],
                item["features"]["payload_occurrences"],
                item["features"]["length"],
                item["branch"]["label"],
            ),
        )
    if policy == "max_context_recurrence":
        return max(
            candidates,
            key=lambda item: (
                item["features"]["max_source_context_recurrence"],
                item["features"]["payload_occurrences"],
                item["features"]["length"],
                item["branch"]["label"],
            ),
        )
    raise ValueError(policy)


def flatten_rows(source_module) -> list[dict[str, Any]]:
    rows = []
    for row in source_module.build_choice_rows():
        candidates = copy_branches(row)
        copy_lengths = [item["features"]["length"] for item in candidates]
        payloads = [item["features"]["payload_occurrences"] for item in candidates]
        intervals = [
            item["features"]["source_target_interval_distance"] for item in candidates
        ]
        rows.append(
            {
                "book": int(row["book"]),
                "target_start": int(row["target_start"]),
                "stable_index": int(row["stable_index"]),
                "kind": row["kind"],
                "drift_class": row["drift_class"],
                "active_op": row["active_op"],
                "stable_op": row["stable_op"],
                "active_is_stable": op_key(row["active_op"]) == op_key(row["stable_op"]),
                "active_type": row["active_op"]["type"],
                "stable_type": row["stable_op"]["type"],
                "active_length": int(row["active_op"]["length"]),
                "copy_branch_count": len(candidates),
                "max_copy_length": max(copy_lengths, default=0),
                "max_payload_occurrences": max(payloads, default=0),
                "min_interval_distance": min(intervals, default=BIG),
                "source": row,
            }
        )
    return rows


def policy_names() -> list[str]:
    return [
        "max_copy_length",
        "min_interval_distance",
        "max_payload_occurrences",
        "min_start_distance",
        "min_end_distance",
        "max_context_recurrence",
    ]


def threshold_values(rows: list[dict[str, Any]], key: str) -> list[int]:
    values = sorted({int(row[key]) for row in rows if int(row[key]) < BIG})
    return values or [0]


def make_rules(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    min_lengths = threshold_values(rows, "max_copy_length")
    min_payloads = threshold_values(rows, "max_payload_occurrences")
    max_intervals = threshold_values(rows, "min_interval_distance")
    active_lengths = threshold_values(rows, "active_length")
    rules = []
    for policy in policy_names():
        for min_len in min_lengths:
            for min_payload in min_payloads:
                for max_interval in max_intervals:
                    rules.append(
                        {
                            "policy": policy,
                            "min_copy_length": min_len,
                            "min_payload_occurrences": min_payload,
                            "max_interval_distance": max_interval,
                            "max_active_literal_length": None,
                        }
                    )
        for max_active in active_lengths:
            rules.append(
                {
                    "policy": policy,
                    "min_copy_length": 5,
                    "min_payload_occurrences": 1,
                    "max_interval_distance": max(max_intervals),
                    "max_active_literal_length": max_active,
                }
            )
    return rules


def rule_label(rule: dict[str, Any]) -> str:
    parts = [
        rule["policy"],
        f"len_ge_{rule['min_copy_length']}",
        f"payload_ge_{rule['min_payload_occurrences']}",
        f"interval_le_{rule['max_interval_distance']}",
    ]
    if rule["max_active_literal_length"] is not None:
        parts.append(f"active_literal_len_le_{rule['max_active_literal_length']}")
    return "__".join(parts)


def fires(row: dict[str, Any], rule: dict[str, Any]) -> bool:
    if int(row["target_start"]) != 0:
        return False
    if not literal_active(row):
        return False
    if row["copy_branch_count"] <= 0:
        return False
    if int(row["max_copy_length"]) < int(rule["min_copy_length"]):
        return False
    if int(row["max_payload_occurrences"]) < int(rule["min_payload_occurrences"]):
        return False
    if int(row["min_interval_distance"]) > int(rule["max_interval_distance"]):
        return False
    max_active = rule["max_active_literal_length"]
    if max_active is not None and int(row["active_length"]) > int(max_active):
        return False
    return True


def selected_branch(row: dict[str, Any], rule: dict[str, Any]) -> dict[str, Any] | None:
    if not fires(row, rule):
        return None
    return choose_copy(row["source"], rule["policy"])


def score_rule(rows: list[dict[str, Any]], rule: dict[str, Any]) -> dict[str, Any]:
    selected = []
    residual = [row for row in rows if row["kind"] == "residual_first_drift"]
    clean = [row for row in rows if row["kind"] == "clean_control"]
    for row in rows:
        branch = selected_branch(row, rule)
        if branch is None:
            continue
        selected.append((row, branch))
    residual_hits = [
        row
        for row, branch in selected
        if row["kind"] == "residual_first_drift" and branch["branch"]["is_stable"]
    ]
    residual_false = [
        row
        for row, branch in selected
        if row["kind"] == "residual_first_drift" and not branch["branch"]["is_stable"]
    ]
    clean_false = [
        row
        for row, branch in selected
        if row["kind"] == "clean_control" and not branch["branch"]["is_stable"]
    ]
    clean_safe = [
        row
        for row, branch in selected
        if row["kind"] == "clean_control" and branch["branch"]["is_stable"]
    ]
    return {
        "rule": rule,
        "predicate": rule_label(rule),
        "policy": rule["policy"],
        "selected_count": len(selected),
        "selected_books": [int(row["book"]) for row, _branch in selected],
        "residual_hits": len(residual_hits),
        "residual_hit_books": [int(row["book"]) for row in residual_hits],
        "residual_false": len(residual_false),
        "residual_false_books": [int(row["book"]) for row in residual_false],
        "residual_total": len(residual),
        "residual_miss_books": [
            int(row["book"])
            for row in residual
            if int(row["book"]) not in {int(hit["book"]) for hit in residual_hits}
        ],
        "book_start_copy_residual_total": sum(
            row["drift_class"] == "book_start_copy_missed_as_literal"
            for row in residual
        ),
        "book_start_copy_residual_hits": sum(
            row["drift_class"] == "book_start_copy_missed_as_literal"
            for row in residual_hits
        ),
        "clean_false_changes": len(clean_false),
        "clean_false_books": [int(row["book"]) for row in clean_false],
        "clean_safe_selected": len(clean_safe),
        "clean_total": len(clean),
        "selected_rows": [
            {
                "book": int(row["book"]),
                "stable_index": int(row["stable_index"]),
                "kind": row["kind"],
                "drift_class": row["drift_class"],
                "active_op": row["active_op"],
                "stable_op": row["stable_op"],
                "chosen_op": branch["branch"]["op"],
                "chosen_is_stable": branch["branch"]["is_stable"],
                "chosen_features": branch["features"],
            }
            for row, branch in selected
        ],
    }


def score_key(score: dict[str, Any]) -> tuple[Any, ...]:
    return (
        score["book_start_copy_residual_hits"],
        score["residual_hits"],
        -score["clean_false_changes"],
        -score["residual_false"],
        -score["selected_count"],
        score["predicate"],
    )


def prequential(rows: list[dict[str, Any]], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if row["book"] < cutoff]
        test = [row for row in rows if row["book"] >= cutoff]
        train_scores = [score_rule(train, rule) for rule in rules]
        selected = max(train_scores, key=score_key)
        test_score = score_rule(test, selected["rule"])
        oracle = max([score_rule(test, rule) for rule in rules], key=score_key)
        out.append(
            {
                "cutoff_book": cutoff,
                "selected_predicate": selected["predicate"],
                "train_book_start_copy_hits": selected[
                    "book_start_copy_residual_hits"
                ],
                "train_residual_hits": selected["residual_hits"],
                "train_residual_total": selected["residual_total"],
                "train_clean_false_changes": selected["clean_false_changes"],
                "test_book_start_copy_hits": test_score[
                    "book_start_copy_residual_hits"
                ],
                "test_residual_hits": test_score["residual_hits"],
                "test_residual_total": test_score["residual_total"],
                "test_clean_false_changes": test_score["clean_false_changes"],
                "test_residual_false": test_score["residual_false"],
                "oracle_test_book_start_copy_hits": oracle[
                    "book_start_copy_residual_hits"
                ],
                "oracle_test_residual_hits": oracle["residual_hits"],
                "selected_matches_oracle": (
                    test_score["book_start_copy_residual_hits"],
                    test_score["residual_hits"],
                    -test_score["clean_false_changes"],
                )
                == (
                    oracle["book_start_copy_residual_hits"],
                    oracle["residual_hits"],
                    -oracle["clean_false_changes"],
                ),
            }
        )
    return out


def random_site_control(rows: list[dict[str, Any]], best: dict[str, Any]) -> dict[str, Any]:
    candidate_rows = [
        row
        for row in rows
        if int(row["target_start"]) == 0
        and literal_active(row)
        and int(row["copy_branch_count"]) > 0
    ]
    hit_books = {
        int(row["book"])
        for row in rows
        if row["kind"] == "residual_first_drift"
        and row["drift_class"] == "book_start_copy_missed_as_literal"
    }
    draw_count = min(best["selected_count"], len(candidate_rows))
    rng = random.Random(RANDOM_SEED)
    hits = []
    for _ in range(RANDOM_TRIALS):
        sample = rng.sample(candidate_rows, draw_count)
        hits.append(sum(int(row["book"]) in hit_books for row in sample))
    observed = best["book_start_copy_residual_hits"]
    return {
        "candidate_site_count": len(candidate_rows),
        "draw_count": draw_count,
        "observed_book_start_copy_hits": observed,
        "trials": RANDOM_TRIALS,
        "random_min": min(hits),
        "random_mean": sum(hits) / len(hits),
        "random_max": max(hits),
        "random_ge_observed_count": sum(hit >= observed for hit in hits),
        "p_ge_observed": (sum(hit >= observed for hit in hits) + 1)
        / (len(hits) + 1),
    }


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return math.inf
    return math.log2(math.comb(n, k))


def log2_factorial(n: int) -> float:
    return math.lgamma(n + 1) / math.log(2)


def multiset_order_bits(labels: list[tuple[Any, ...]]) -> float:
    counts = Counter(labels)
    return log2_factorial(len(labels)) - sum(
        log2_factorial(count) for count in counts.values()
    )


def cost_for_rule(
    score: dict[str, Any],
    rule_count: int,
    decision_universe: int,
    baseline_lookup_bits: float,
    residual_label_by_book: dict[int, tuple[Any, ...]],
) -> dict[str, Any]:
    clean_false = int(score["clean_false_changes"])
    residual_misses = int(score["residual_total"]) - int(score["residual_hits"])
    missed_labels = [
        residual_label_by_book[int(book)] for book in score["residual_miss_books"]
    ]
    rule_id_bits = math.log2(rule_count)
    clean_rollback_bits = log2_comb(decision_universe, clean_false)
    residual_miss_site_bits = log2_comb(decision_universe, residual_misses)
    residual_miss_label_bits = multiset_order_bits(missed_labels)
    total = (
        rule_id_bits
        + clean_rollback_bits
        + residual_miss_site_bits
        + residual_miss_label_bits
    )
    return {
        "predicate": score["predicate"],
        "residual_hits": score["residual_hits"],
        "residual_misses": residual_misses,
        "book_start_copy_residual_hits": score["book_start_copy_residual_hits"],
        "clean_false_changes": clean_false,
        "rule_id_bits": rule_id_bits,
        "clean_rollback_bits": clean_rollback_bits,
        "residual_miss_site_bits": residual_miss_site_bits,
        "residual_miss_label_bits": residual_miss_label_bits,
        "total_bits": total,
        "net_vs_lookup_bits": total - baseline_lookup_bits,
    }


def make_result() -> dict[str, Any]:
    gate41 = load_json(GATE41)
    gate50 = load_json(GATE50)
    gate53 = load_json(GATE53)
    for name, data in [
        ("latent_state_lookup_cost_gate", gate41),
        ("source_interval_context_gate", gate50),
        ("source_interval_cost_gate", gate53),
    ]:
        assert_boundary(name, data)
    if gate53["classification"] != "source_interval_cost_weak_clue_not_promoted":
        raise RuntimeError("gate54 expects gate53 weak-clue state")

    source_module = load_module("source_interval_for_gate54", GATE50_SCRIPT)
    rows = flatten_rows(source_module)
    rules = make_rules(rows)
    scores = [score_rule(rows, rule) for rule in rules]
    scores.sort(key=score_key, reverse=True)
    best = scores[0]
    zero_fp = [row for row in scores if row["clean_false_changes"] == 0]
    best_zero_fp = zero_fp[0] if zero_fp else None
    preq = prequential(rows, rules)
    control = random_site_control(rows, best)
    baseline_lookup_bits = float(
        gate41["summary"]["first_drift_lookup_lower_bound_bits"]
    )
    decision_universe = max(
        int(gate41["summary"]["decision_universe"]),
        int(gate50["summary"]["decision_count"]),
    )
    residual_label_by_book = {}
    for row in gate50["best_residual_rows"]:
        stable = row["stable_op"]
        residual_label_by_book[int(row["book"])] = (
            stable["type"],
            int(stable["length"]),
        )
    best_cost = cost_for_rule(
        best,
        len(rules),
        decision_universe,
        baseline_lookup_bits,
        residual_label_by_book,
    )
    zero_cost = (
        None
        if best_zero_fp is None
        else cost_for_rule(
            best_zero_fp,
            len(rules),
            decision_universe,
            baseline_lookup_bits,
            residual_label_by_book,
        )
    )
    candidate_costs = [best_cost] + ([] if zero_cost is None else [zero_cost])
    best_priced = min(candidate_costs, key=lambda row: row["total_bits"])
    cells_with_test_residuals = sum(1 for row in preq if row["test_residual_total"] > 0)
    cells_cover_all_book_start = sum(
        1
        for row in preq
        if row["test_residual_total"] > 0
        and row["test_book_start_copy_hits"]
        == row["oracle_test_book_start_copy_hits"]
        and row["test_clean_false_changes"] == 0
    )
    promotes = (
        best["book_start_copy_residual_hits"]
        == best["book_start_copy_residual_total"]
        and best["clean_false_changes"] == 0
        and cells_cover_all_book_start == cells_with_test_residuals
        and best_priced["total_bits"] < baseline_lookup_bits
        and control["p_ge_observed"] <= 0.05
    )
    if promotes:
        classification = "book_start_copy_subclass_rule_promoted"
    elif best["book_start_copy_residual_hits"] > 0:
        classification = "book_start_copy_subclass_weak_clue_not_promoted"
    else:
        classification = "book_start_copy_subclass_rejected"
    return {
        "schema": "book_start_copy_subclass_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "latent_state_lookup_cost_gate": rel(GATE41),
            "source_interval_context_gate": rel(GATE50),
            "source_interval_cost_gate": rel(GATE53),
            "source_interval_context_script": rel(GATE50_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "tests_book_start_copy_subclass": True,
            "excludes_drift_class_predicates": True,
            "promotes_parser_rule": promotes,
        },
        "summary": {
            "decision_count": len(rows),
            "rule_count": len(rules),
            "residual_total": best["residual_total"],
            "book_start_copy_residual_total": best[
                "book_start_copy_residual_total"
            ],
            "best_predicate": best["predicate"],
            "best_book_start_copy_residual_hits": best[
                "book_start_copy_residual_hits"
            ],
            "best_residual_hits": best["residual_hits"],
            "best_clean_false_changes": best["clean_false_changes"],
            "best_selected_count": best["selected_count"],
            "best_zero_fp_predicate": None if best_zero_fp is None else best_zero_fp["predicate"],
            "best_zero_fp_book_start_copy_residual_hits": 0
            if best_zero_fp is None
            else best_zero_fp["book_start_copy_residual_hits"],
            "best_zero_fp_residual_hits": 0
            if best_zero_fp is None
            else best_zero_fp["residual_hits"],
            "best_zero_fp_selected_count": 0
            if best_zero_fp is None
            else best_zero_fp["selected_count"],
            "baseline_lookup_bits": baseline_lookup_bits,
            "best_priced_bits": best_priced["total_bits"],
            "best_priced_net_vs_lookup_bits": best_priced["net_vs_lookup_bits"],
            "random_p_ge_observed": control["p_ge_observed"],
            "prequential_cells": len(preq),
            "prequential_cells_with_test_residuals": cells_with_test_residuals,
            "prequential_cover_oracle_book_start_zero_fp_cells": cells_cover_all_book_start,
            "promotes_book_start_copy_parser_rule": promotes,
            "interpretation": (
                "Gate 54 isolates the diagnostic-looking book-start copy "
                "residual subclass without using drift_class in the predicate. "
                "A rule must fire from observable book-start copy availability, "
                "avoid clean false changes, beat residual lookup after rule cost, "
                "and remain stable under prefix/holdout."
            ),
        },
        "best_score": {
            key: value
            for key, value in best.items()
            if key not in {"rule", "selected_rows"}
        },
        "best_zero_fp_score": None
        if best_zero_fp is None
        else {
            key: value
            for key, value in best_zero_fp.items()
            if key not in {"rule", "selected_rows"}
        },
        "cost_rows": candidate_costs,
        "random_site_control": control,
        "prequential_rows": preq,
        "selected_rows_under_best": best["selected_rows"],
        "scoreboard_top": [
            {
                key: value
                for key, value in row.items()
                if key not in {"rule", "selected_rows"}
            }
            for row in scores[:25]
        ],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "book_start_copy_subclass_tested",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    s = result["summary"]
    lines = [
        "# Book-Start Copy Subclass Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 54 tests whether the residual subclass where an active",
        "literal at book start should instead be a copy has an observable",
        "subrule. It does not use `drift_class` as a predicate; the firing",
        "condition is limited to book-start literal state plus observable",
        "copy-candidate features.",
        "",
        "## Summary",
        "",
        f"- Decisions: `{s['decision_count']}`.",
        f"- Rules tested: `{s['rule_count']}`.",
        f"- Residual decisions: `{s['residual_total']}`.",
        f"- Book-start copy residuals: `{s['book_start_copy_residual_total']}`.",
        f"- Best predicate: `{s['best_predicate']}`.",
        f"- Best book-start copy hits: `{s['best_book_start_copy_residual_hits']}/{s['book_start_copy_residual_total']}`.",
        f"- Best residual hits overall: `{s['best_residual_hits']}/{s['residual_total']}`.",
        f"- Best clean false changes: `{s['best_clean_false_changes']}`.",
        f"- Best zero-FP predicate: `{s['best_zero_fp_predicate']}`.",
        f"- Best zero-FP book-start copy hits: `{s['best_zero_fp_book_start_copy_residual_hits']}/{s['book_start_copy_residual_total']}`.",
        f"- Best priced bits: `{s['best_priced_bits']:.3f}`.",
        f"- Best priced net vs lookup: `{s['best_priced_net_vs_lookup_bits']:.3f}`.",
        f"- Random p(>= observed): `{s['random_p_ge_observed']:.3f}`.",
        f"- Promotes parser rule: `{s['promotes_book_start_copy_parser_rule']}`.",
        "",
        "## Cost Rows",
        "",
        "| Predicate | Book-start hits | Residual hits | Clean false changes | Total bits | Net vs lookup |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["cost_rows"]:
        lines.append(
            f"| `{row['predicate']}` | "
            f"`{row['book_start_copy_residual_hits']}` | "
            f"`{row['residual_hits']}` | "
            f"`{row['clean_false_changes']}` | "
            f"`{row['total_bits']:.3f}` | "
            f"`{row['net_vs_lookup_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected predicate | Train residual hits | Test residual hits | Test clean false changes | Oracle test book-start hits | Matches oracle |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_predicate']}` | "
            f"`{row['train_residual_hits']}/{row['train_residual_total']}` | "
            f"`{row['test_residual_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` | "
            f"`{row['oracle_test_book_start_copy_hits']}` | "
            f"`{row['selected_matches_oracle']}` |"
        )
    lines.extend(
        [
            "",
            "## Selected Rows Under Best Predicate",
            "",
            "| Book | Op | Kind | Class | Active | Stable | Chosen | Hit | Payload occ. | Interval distance |",
            "|---:|---:|---|---|---|---|---|---:|---:|---:|",
        ]
    )
    for row in result["selected_rows_under_best"]:
        features = row["chosen_features"]
        lines.append(
            f"| `{row['book']}` | `{row['stable_index']}` | "
            f"`{row['kind']}` | `{row['drift_class']}` | "
            f"`{row['active_op']}` | `{row['stable_op']}` | "
            f"`{row['chosen_op']}` | `{row['chosen_is_stable']}` | "
            f"`{features['payload_occurrences']}` | "
            f"`{features['source_target_interval_distance']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The subclass has visible signal, but it is still not a promoted",
            "segmentation rule unless it clears all gates at once: no clean",
            "false changes, lower paid description than residual lookup, and",
            "stable prefix/holdout behavior. This gate therefore keeps the",
            "result as weak/audit-only when the signal is local or post-hoc.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
