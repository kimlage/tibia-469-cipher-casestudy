from __future__ import annotations

import itertools
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE41 = TEST_RESULTS / "41_latent_state_lookup_cost_gate.json"
OUT_STEM = "42_compact_latent_rule_frontier"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


Predicate = tuple[str, Callable[[dict[str, Any]], bool]]


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


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        raise ValueError((n, k))
    return math.log2(math.comb(n, k))


def log2_factorial(n: int) -> float:
    return math.lgamma(n + 1) / math.log(2)


def multiset_order_bits(labels: list[tuple[Any, ...]]) -> float:
    counts = Counter(labels)
    return log2_factorial(len(labels)) - sum(
        log2_factorial(count) for count in counts.values()
    )


def lookup_bits(decision_universe: int, rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    labels = [tuple(row["stable_label"]) for row in rows]
    return log2_comb(decision_universe, len(rows)) + multiset_order_bits(labels)


def length_bucket(value: int) -> str:
    for cut in [1, 3, 5, 8, 13, 21, 34, 55]:
        if value <= cut:
            return f"le{cut}"
    return "gt55"


def make_predicates(rows: list[dict[str, Any]]) -> list[Predicate]:
    books = sorted({int(row["book"]) for row in rows})
    ops = sorted({int(row["op_index"]) for row in rows})
    active_types = sorted({tuple(row["active_label"])[0] for row in rows})
    active_lengths = sorted({int(tuple(row["active_label"])[1]) for row in rows})
    active_buckets = sorted({length_bucket(length) for length in active_lengths})
    predicates: list[Predicate] = [
        ("all", lambda row: True),
        ("book_parity_0", lambda row: int(row["book"]) % 2 == 0),
        ("book_parity_1", lambda row: int(row["book"]) % 2 == 1),
        ("book_lt_30", lambda row: int(row["book"]) < 30),
        ("book_lt_40", lambda row: int(row["book"]) < 40),
        ("book_ge_40", lambda row: int(row["book"]) >= 40),
        ("book_ge_50", lambda row: int(row["book"]) >= 50),
        ("op_even", lambda row: int(row["op_index"]) % 2 == 0),
        ("op_odd", lambda row: int(row["op_index"]) % 2 == 1),
    ]
    for mod in [3, 5]:
        for value in range(mod):
            predicates.append(
                (
                    f"book_mod{mod}_{value}",
                    lambda row, mod=mod, value=value: int(row["book"]) % mod == value,
                )
            )
    for book in books:
        predicates.append((f"book_eq_{book}", lambda row, book=book: int(row["book"]) == book))
    for op in ops:
        predicates.append((f"op_eq_{op}", lambda row, op=op: int(row["op_index"]) == op))
    for active_type in active_types:
        predicates.append(
            (
                f"active_type_{active_type}",
                lambda row, active_type=active_type: tuple(row["active_label"])[0]
                == active_type,
            )
        )
    for length in active_lengths:
        predicates.append(
            (
                f"active_len_{length}",
                lambda row, length=length: int(tuple(row["active_label"])[1])
                == length,
            )
        )
    for bucket in active_buckets:
        predicates.append(
            (
                f"active_bucket_{bucket}",
                lambda row, bucket=bucket: length_bucket(
                    int(tuple(row["active_label"])[1])
                )
                == bucket,
            )
        )
    return predicates


def rule_cost_bits(predicate_count: int, label_count: int, rule_count: int) -> float:
    if rule_count == 0:
        return 0.0
    # One stop/use bit per rule plus predicate and label IDs.
    return rule_count * (1.0 + math.log2(predicate_count) + math.log2(label_count))


def score_rule_set(
    rows: list[dict[str, Any]],
    predicates: list[Predicate],
    label_set: list[tuple[Any, ...]],
    rule_specs: list[tuple[str, tuple[Any, ...]]],
    decision_universe: int,
) -> dict[str, Any]:
    pred_map = {name: fn for name, fn in predicates}
    assigned: set[int] = set()
    false_positive_rows: list[int] = []
    hit_rows: list[int] = []
    for pred_name, label in rule_specs:
        fn = pred_map[pred_name]
        for idx, row in enumerate(rows):
            if idx in assigned or not fn(row):
                continue
            if tuple(row["stable_label"]) == label:
                hit_rows.append(idx)
                assigned.add(idx)
            else:
                false_positive_rows.append(idx)
    unresolved = [
        row for idx, row in enumerate(rows) if idx not in set(hit_rows)
    ]
    cost = rule_cost_bits(len(predicates), len(label_set), len(rule_specs)) + lookup_bits(
        decision_universe, unresolved
    )
    return {
        "rules": [
            {"predicate": predicate, "label": label}
            for predicate, label in rule_specs
        ],
        "rule_count": len(rule_specs),
        "hit_count": len(set(hit_rows)),
        "false_positive_count": len(set(false_positive_rows)),
        "unresolved_count": len(unresolved),
        "total_bits": cost,
        "rule_bits": rule_cost_bits(len(predicates), len(label_set), len(rule_specs)),
        "remaining_lookup_bits": lookup_bits(decision_universe, unresolved),
        "hit_books": sorted({rows[idx]["book"] for idx in set(hit_rows)}),
    }


def generate_candidate_rule_sets(
    rows: list[dict[str, Any]],
    predicates: list[Predicate],
    label_set: list[tuple[Any, ...]],
) -> list[list[tuple[str, tuple[Any, ...]]]]:
    single_rules: list[tuple[str, tuple[Any, ...]]] = []
    for pred_name, fn in predicates:
        covered = [row for row in rows if fn(row)]
        if not covered:
            continue
        labels = sorted({tuple(row["stable_label"]) for row in covered})
        for label in labels:
            single_rules.append((pred_name, label))
    candidates = [[rule] for rule in single_rules]
    # Keep pair frontier bounded and interpretable.
    for left, right in itertools.combinations(single_rules, 2):
        if left[0] == right[0]:
            continue
        candidates.append([left, right])
    return candidates


def prequential_rows(
    rows: list[dict[str, Any]],
    predicates: list[Predicate],
    label_set: list[tuple[Any, ...]],
    decision_universe: int,
) -> list[dict[str, Any]]:
    out = []
    candidates = generate_candidate_rule_sets(rows, predicates, label_set)
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        if not test:
            out.append(
                {
                    "cutoff_book": cutoff,
                    "train_count": len(train),
                    "test_count": 0,
                    "selected_rules": [],
                    "test_hits": 0,
                    "test_false_positives": 0,
                    "selected_net_bits_vs_lookup": 0.0,
                }
            )
            continue
        train_lookup = lookup_bits(decision_universe, train)
        train_scores = []
        for rules in candidates:
            score = score_rule_set(train, predicates, label_set, rules, decision_universe)
            score["net_bits_vs_lookup"] = score["total_bits"] - train_lookup
            train_scores.append(score)
        selected = min(
            train_scores,
            key=lambda row: (
                row["net_bits_vs_lookup"],
                row["false_positive_count"],
                -row["hit_count"],
                row["rule_count"],
            ),
        )
        test_score = score_rule_set(
            test,
            predicates,
            label_set,
            [
                (rule["predicate"], tuple(rule["label"]))
                for rule in selected["rules"]
            ],
            decision_universe,
        )
        out.append(
            {
                "cutoff_book": cutoff,
                "train_count": len(train),
                "test_count": len(test),
                "selected_rules": selected["rules"],
                "selected_net_bits_vs_lookup": selected["net_bits_vs_lookup"],
                "test_hits": test_score["hit_count"],
                "test_false_positives": test_score["false_positive_count"],
            }
        )
    return out


def make_result() -> dict[str, Any]:
    gate41 = load_json(GATE41)
    assert_boundary("latent_state_lookup_cost_gate", gate41)
    if gate41["classification"] != "latent_state_lookup_cost_audit_only":
        raise RuntimeError("gate42 expects gate41 lookup cost audit")

    rows = gate41["residual_rows"]
    decision_universe = int(gate41["summary"]["decision_universe"])
    labels = sorted({tuple(row["stable_label"]) for row in rows})
    predicates = make_predicates(rows)
    baseline_lookup = lookup_bits(decision_universe, rows)
    candidates = generate_candidate_rule_sets(rows, predicates, labels)
    scores = []
    for rules in candidates:
        score = score_rule_set(rows, predicates, labels, rules, decision_universe)
        score["net_bits_vs_lookup"] = score["total_bits"] - baseline_lookup
        scores.append(score)
    best = min(
        scores,
        key=lambda row: (
            row["net_bits_vs_lookup"],
            row["false_positive_count"],
            -row["hit_count"],
            row["rule_count"],
        ),
    )
    zero_false_positive_scores = [
        row for row in scores if row["false_positive_count"] == 0
    ]
    best_zero_false_positive = min(
        zero_false_positive_scores,
        key=lambda row: (
            row["net_bits_vs_lookup"],
            -row["hit_count"],
            row["rule_count"],
        ),
    )
    preq = prequential_rows(rows, predicates, labels, decision_universe)
    preq_cells_with_test = sum(1 for row in preq if row["test_count"] > 0)
    preq_cells_with_hit = sum(1 for row in preq if row["test_hits"] > 0)
    promotes = (
        best_zero_false_positive["net_bits_vs_lookup"] < 0
        and preq_cells_with_hit == preq_cells_with_test
    )
    if promotes:
        classification = "compact_latent_rule_promoted"
    elif best["hit_count"] > 0:
        classification = "compact_latent_rule_rejected_cost_or_holdout"
    else:
        classification = "compact_latent_rule_frontier_rejected"
    return {
        "schema": "compact_latent_rule_frontier.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "latent_state_lookup_cost_gate": rel(GATE41),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_compact_latent_rule_against_lookup": True,
        },
        "summary": {
            "residual_count": len(rows),
            "decision_universe": decision_universe,
            "predicate_count": len(predicates),
            "label_count": len(labels),
            "candidate_rule_sets": len(candidates),
            "baseline_lookup_bits": baseline_lookup,
            "best_total_bits": best["total_bits"],
            "best_net_bits_vs_lookup": best["net_bits_vs_lookup"],
            "best_rule_count": best["rule_count"],
            "best_hit_count": best["hit_count"],
            "best_false_positive_count": best["false_positive_count"],
            "best_unresolved_count": best["unresolved_count"],
            "best_zero_false_positive_total_bits": best_zero_false_positive[
                "total_bits"
            ],
            "best_zero_false_positive_net_bits_vs_lookup": best_zero_false_positive[
                "net_bits_vs_lookup"
            ],
            "best_zero_false_positive_hit_count": best_zero_false_positive[
                "hit_count"
            ],
            "best_zero_false_positive_unresolved_count": best_zero_false_positive[
                "unresolved_count"
            ],
            "prequential_cells_with_test": preq_cells_with_test,
            "prequential_cells_with_hit": preq_cells_with_hit,
            "promotes_compact_latent_rule": promotes,
            "interpretation": (
                "Compact latent rules are scored only if they beat the residual "
                "lookup after paying predicate and label IDs. Hits without a net "
                "MDL gain or holdout stability are not generation progress."
            ),
        },
        "best_rule": best,
        "best_zero_false_positive_rule": best_zero_false_positive,
        "top_scoreboard": sorted(
            scores,
            key=lambda row: (
                row["net_bits_vs_lookup"],
                row["false_positive_count"],
                -row["hit_count"],
                row["rule_count"],
            ),
        )[:20],
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "compact_latent_rule_tested",
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


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    score_rows = [
        [
            item["rule_count"],
            item["hit_count"],
            item["false_positive_count"],
            item["unresolved_count"],
            f"{item['total_bits']:.3f}",
            f"{item['net_bits_vs_lookup']:.3f}",
            item["rules"],
        ]
        for item in result["top_scoreboard"][:10]
    ]
    preq_rows = [
        [
            row["cutoff_book"],
            row["train_count"],
            row["test_count"],
            row["test_hits"],
            row["test_false_positives"],
            f"{row['selected_net_bits_vs_lookup']:.3f}",
            row["selected_rules"],
        ]
        for row in result["prequential_rows"]
    ]
    body = f"""# Compact Latent Rule Frontier

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 42 tests whether a small observable latent rule can beat the explicit
residual lookup priced by gate 41. Candidate rules use residual-visible book,
operation, and active-operation features; each rule pays predicate and label
IDs before any remaining residual lookup is charged.

This is not a compression-bound update and not a row0/semantic claim.

## Summary

- Residual count: `{s['residual_count']}`.
- Predicate count: `{s['predicate_count']}`.
- Label count: `{s['label_count']}`.
- Candidate rule sets: `{s['candidate_rule_sets']}`.
- Baseline lookup bits: `{s['baseline_lookup_bits']:.3f}`.
- Best total bits: `{s['best_total_bits']:.3f}`.
- Best net bits vs lookup:
  `{s['best_net_bits_vs_lookup']:.3f}`.
- Best rule count: `{s['best_rule_count']}`.
- Best hits: `{s['best_hit_count']}`.
- Best false positives: `{s['best_false_positive_count']}`.
- Best zero-false-positive net bits vs lookup:
  `{s['best_zero_false_positive_net_bits_vs_lookup']:.3f}`.
- Best zero-false-positive hits:
  `{s['best_zero_false_positive_hit_count']}`.
- Prequential cells with held-out hit:
  `{s['prequential_cells_with_hit']}/{s['prequential_cells_with_test']}`.
- Promotes compact latent rule: `{s['promotes_compact_latent_rule']}`.

## Top Rule Sets

{md_table(score_rows, ["rules", "hits", "false positives", "unresolved", "total bits", "net bits", "rule spec"])}

## Prequential Rows

{md_table(preq_rows, ["cutoff", "train", "test", "test hits", "test false positives", "train net bits", "selected rules"])}

## Decision

No compact latent rule is promoted. The best apparent MDL gain has false
positives, and the best zero-false-positive rule does not provide stable
held-out coverage. Under current evidence, the latent state still needs a real
mechanism, not a small residual-visible rule patch.

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
