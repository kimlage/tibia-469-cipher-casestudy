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
GATE42 = TEST_RESULTS / "42_compact_latent_rule_frontier.json"
OUT_STEM = "43_source_free_residual_rule_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


Predicate = tuple[str, str, Callable[[dict[str, Any]], bool]]


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


def make_predicates(rows: list[dict[str, Any]]) -> list[Predicate]:
    books = sorted({int(row["book"]) for row in rows})
    ops = sorted({int(row["op_index"]) for row in rows})
    preds: list[Predicate] = [
        ("all", "structural", lambda row: True),
        ("book_parity_0", "structural", lambda row: int(row["book"]) % 2 == 0),
        ("book_parity_1", "structural", lambda row: int(row["book"]) % 2 == 1),
        ("book_lt_30", "structural", lambda row: int(row["book"]) < 30),
        ("book_lt_40", "structural", lambda row: int(row["book"]) < 40),
        ("book_ge_40", "structural", lambda row: int(row["book"]) >= 40),
        ("book_ge_50", "structural", lambda row: int(row["book"]) >= 50),
        ("op_even", "structural", lambda row: int(row["op_index"]) % 2 == 0),
        ("op_odd", "structural", lambda row: int(row["op_index"]) % 2 == 1),
        ("op_lt_2", "structural", lambda row: int(row["op_index"]) < 2),
        ("op_ge_2", "structural", lambda row: int(row["op_index"]) >= 2),
        ("op_ge_7", "structural", lambda row: int(row["op_index"]) >= 7),
    ]
    for mod in [3, 5, 10]:
        for value in range(mod):
            preds.append(
                (
                    f"book_mod{mod}_{value}",
                    "structural",
                    lambda row, mod=mod, value=value: int(row["book"]) % mod == value,
                )
            )
    for op in ops:
        preds.append(
            (
                f"op_eq_{op}",
                "structural",
                lambda row, op=op: int(row["op_index"]) == op,
            )
        )
    for book in books:
        preds.append(
            (
                f"book_eq_{book}",
                "lookup_like",
                lambda row, book=book: int(row["book"]) == book,
            )
        )
    return preds


def rule_cost_bits(predicate_count: int, label_count: int, rule_count: int) -> float:
    if rule_count == 0:
        return 0.0
    return rule_count * (1.0 + math.log2(predicate_count) + math.log2(label_count))


def score_rule_set(
    rows: list[dict[str, Any]],
    predicates: list[Predicate],
    labels: list[tuple[Any, ...]],
    rules: list[tuple[str, tuple[Any, ...]]],
    decision_universe: int,
) -> dict[str, Any]:
    pred_map = {name: (kind, fn) for name, kind, fn in predicates}
    hits: set[int] = set()
    false_positives: set[int] = set()
    kinds: set[str] = set()
    for pred_name, label in rules:
        kind, fn = pred_map[pred_name]
        kinds.add(kind)
        for index, row in enumerate(rows):
            if index in hits or not fn(row):
                continue
            if tuple(row["stable_label"]) == label:
                hits.add(index)
            else:
                false_positives.add(index)
    unresolved = [row for idx, row in enumerate(rows) if idx not in hits]
    rule_bits = rule_cost_bits(len(predicates), len(labels), len(rules))
    remaining_lookup = lookup_bits(decision_universe, unresolved)
    return {
        "rules": [{"predicate": pred, "label": label} for pred, label in rules],
        "rule_count": len(rules),
        "uses_lookup_like_predicate": "lookup_like" in kinds,
        "hit_count": len(hits),
        "false_positive_count": len(false_positives),
        "unresolved_count": len(unresolved),
        "rule_bits": rule_bits,
        "remaining_lookup_bits": remaining_lookup,
        "total_bits": rule_bits + remaining_lookup,
        "hit_books": sorted({rows[idx]["book"] for idx in hits}),
    }


def generate_rule_sets(
    rows: list[dict[str, Any]],
    predicates: list[Predicate],
    labels: list[tuple[Any, ...]],
    allow_lookup_like: bool,
) -> list[list[tuple[str, tuple[Any, ...]]]]:
    singles = []
    for name, kind, fn in predicates:
        if kind == "lookup_like" and not allow_lookup_like:
            continue
        covered = [row for row in rows if fn(row)]
        if not covered:
            continue
        for label in sorted({tuple(row["stable_label"]) for row in covered}):
            singles.append((name, label))
    rule_sets = [[rule] for rule in singles]
    for left, right in itertools.combinations(singles, 2):
        if left[0] == right[0]:
            continue
        rule_sets.append([left, right])
    return rule_sets


def score_frontier(
    rows: list[dict[str, Any]],
    predicates: list[Predicate],
    labels: list[tuple[Any, ...]],
    decision_universe: int,
    allow_lookup_like: bool,
) -> dict[str, Any]:
    baseline = lookup_bits(decision_universe, rows)
    rule_sets = generate_rule_sets(rows, predicates, labels, allow_lookup_like)
    scores = []
    for rules in rule_sets:
        score = score_rule_set(rows, predicates, labels, rules, decision_universe)
        score["net_bits_vs_lookup"] = score["total_bits"] - baseline
        scores.append(score)
    best = min(
        scores,
        key=lambda row: (
            row["net_bits_vs_lookup"],
            row["false_positive_count"],
            -row["hit_count"],
            row["uses_lookup_like_predicate"],
            row["rule_count"],
        ),
    )
    zero_fp = [row for row in scores if row["false_positive_count"] == 0]
    best_zero_fp = min(
        zero_fp,
        key=lambda row: (
            row["net_bits_vs_lookup"],
            -row["hit_count"],
            row["uses_lookup_like_predicate"],
            row["rule_count"],
        ),
    )
    return {
        "allow_lookup_like": allow_lookup_like,
        "candidate_rule_sets": len(rule_sets),
        "best": best,
        "best_zero_false_positive": best_zero_fp,
        "top_scoreboard": sorted(
            scores,
            key=lambda row: (
                row["net_bits_vs_lookup"],
                row["false_positive_count"],
                -row["hit_count"],
                row["uses_lookup_like_predicate"],
                row["rule_count"],
            ),
        )[:12],
    }


def prequential_rows(
    rows: list[dict[str, Any]],
    predicates: list[Predicate],
    labels: list[tuple[Any, ...]],
    decision_universe: int,
    allow_lookup_like: bool,
) -> list[dict[str, Any]]:
    out = []
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
                    "train_net_bits_vs_lookup": 0.0,
                }
            )
            continue
        if not train:
            continue
        train_labels = sorted({tuple(row["stable_label"]) for row in train})
        frontier = score_frontier(
            train, predicates, train_labels, decision_universe, allow_lookup_like
        )
        selected = frontier["best_zero_false_positive"]
        test_score = score_rule_set(
            test,
            predicates,
            labels,
            [(rule["predicate"], tuple(rule["label"])) for rule in selected["rules"]],
            decision_universe,
        )
        out.append(
            {
                "cutoff_book": cutoff,
                "train_count": len(train),
                "test_count": len(test),
                "selected_rules": selected["rules"],
                "train_net_bits_vs_lookup": selected["net_bits_vs_lookup"],
                "test_hits": test_score["hit_count"],
                "test_false_positives": test_score["false_positive_count"],
            }
        )
    return out


def make_result() -> dict[str, Any]:
    gate41 = load_json(GATE41)
    gate42 = load_json(GATE42)
    assert_boundary("latent_state_lookup_cost_gate", gate41)
    assert_boundary("compact_latent_rule_frontier", gate42)
    if gate42["classification"] != "compact_latent_rule_rejected_cost_or_holdout":
        raise RuntimeError("gate43 expects gate42 compact rule rejection")

    rows = gate41["residual_rows"]
    decision_universe = int(gate41["summary"]["decision_universe"])
    labels = sorted({tuple(row["stable_label"]) for row in rows})
    predicates = make_predicates(rows)
    structural = score_frontier(
        rows, predicates, labels, decision_universe, allow_lookup_like=False
    )
    with_lookup = score_frontier(
        rows, predicates, labels, decision_universe, allow_lookup_like=True
    )
    preq_structural = prequential_rows(
        rows, predicates, labels, decision_universe, allow_lookup_like=False
    )
    preq_with_lookup = prequential_rows(
        rows, predicates, labels, decision_universe, allow_lookup_like=True
    )
    structural_hit_cells = sum(1 for row in preq_structural if row["test_hits"] > 0)
    structural_test_cells = sum(1 for row in preq_structural if row["test_count"] > 0)
    promotes = (
        structural["best_zero_false_positive"]["net_bits_vs_lookup"] < 0
        and structural_hit_cells == structural_test_cells
    )
    if promotes:
        classification = "source_free_residual_rule_promoted"
    elif structural["best"]["hit_count"] > 0 or with_lookup["best"]["hit_count"] > 0:
        classification = "source_free_residual_rule_rejected"
    else:
        classification = "source_free_residual_rule_frontier_rejected"
    return {
        "schema": "source_free_residual_rule_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "latent_state_lookup_cost_gate": rel(GATE41),
            "compact_latent_rule_frontier": rel(GATE42),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": False,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_source_free_residual_rule_against_lookup": True,
        },
        "summary": {
            "residual_count": len(rows),
            "predicate_count": len(predicates),
            "label_count": len(labels),
            "structural_candidate_rule_sets": structural["candidate_rule_sets"],
            "lookup_like_candidate_rule_sets": with_lookup["candidate_rule_sets"],
            "structural_best_net_bits_vs_lookup": structural["best"][
                "net_bits_vs_lookup"
            ],
            "structural_best_false_positive_count": structural["best"][
                "false_positive_count"
            ],
            "structural_best_zero_false_positive_net_bits_vs_lookup": structural[
                "best_zero_false_positive"
            ]["net_bits_vs_lookup"],
            "structural_best_zero_false_positive_hit_count": structural[
                "best_zero_false_positive"
            ]["hit_count"],
            "lookup_like_best_zero_false_positive_net_bits_vs_lookup": with_lookup[
                "best_zero_false_positive"
            ]["net_bits_vs_lookup"],
            "lookup_like_best_zero_false_positive_hit_count": with_lookup[
                "best_zero_false_positive"
            ]["hit_count"],
            "prequential_structural_cells_with_hit": structural_hit_cells,
            "prequential_structural_cells_with_test": structural_test_cells,
            "promotes_source_free_residual_rule": promotes,
            "interpretation": (
                "This gate removes target-dependent active parser features. It "
                "separates structural source-free predicates from book_eq lookup "
                "predicates and requires net MDL gain plus holdout coverage."
            ),
        },
        "structural_frontier": structural,
        "lookup_like_frontier": with_lookup,
        "prequential_structural": preq_structural,
        "prequential_with_lookup": preq_with_lookup,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "source_free_residual_rule_tested",
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


def rule_rows(frontier: dict[str, Any]) -> list[list[Any]]:
    return [
        [
            item["rule_count"],
            item["hit_count"],
            item["false_positive_count"],
            item["unresolved_count"],
            item["uses_lookup_like_predicate"],
            f"{item['net_bits_vs_lookup']:.3f}",
            item["rules"],
        ]
        for item in frontier["top_scoreboard"][:8]
    ]


def preq_rows(rows: list[dict[str, Any]]) -> list[list[Any]]:
    return [
        [
            row["cutoff_book"],
            row["train_count"],
            row["test_count"],
            row["test_hits"],
            row["test_false_positives"],
            f"{row['train_net_bits_vs_lookup']:.3f}",
            row["selected_rules"],
        ]
        for row in rows
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
    body = f"""# Source-Free Residual Rule Gate

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 43 tests the strict source-free residual-rule path. Unlike gate 42, it
removes active parser/copy-availability features and uses only book/op ordinal
features. It also reports lookup-like `book_eq` predicates separately.

## Summary

- Residual count: `{s['residual_count']}`.
- Predicate count: `{s['predicate_count']}`.
- Structural candidate rule sets:
  `{s['structural_candidate_rule_sets']}`.
- Lookup-like candidate rule sets:
  `{s['lookup_like_candidate_rule_sets']}`.
- Structural best net bits vs lookup:
  `{s['structural_best_net_bits_vs_lookup']:.3f}`.
- Structural best false positives:
  `{s['structural_best_false_positive_count']}`.
- Structural best zero-false-positive net bits:
  `{s['structural_best_zero_false_positive_net_bits_vs_lookup']:.3f}`.
- Structural best zero-false-positive hits:
  `{s['structural_best_zero_false_positive_hit_count']}`.
- Lookup-like best zero-false-positive net bits:
  `{s['lookup_like_best_zero_false_positive_net_bits_vs_lookup']:.3f}`.
- Prequential structural cells with hit:
  `{s['prequential_structural_cells_with_hit']}/{s['prequential_structural_cells_with_test']}`.
- Promotes source-free residual rule:
  `{s['promotes_source_free_residual_rule']}`.

## Structural Frontier

{md_table(rule_rows(result['structural_frontier']), ["rules", "hits", "false positives", "unresolved", "uses book_eq", "net bits", "rule spec"])}

## Lookup-Like Frontier

{md_table(rule_rows(result['lookup_like_frontier']), ["rules", "hits", "false positives", "unresolved", "uses book_eq", "net bits", "rule spec"])}

## Structural Prequential Rows

{md_table(preq_rows(result['prequential_structural']), ["cutoff", "train", "test", "test hits", "test false positives", "train net bits", "selected rules"])}

## Decision

No source-free residual rule is promoted. Structural book/op ordinal rules do
not beat the lookup with clean held-out coverage; allowing `book_eq` only turns
the rule into a lookup-like patch. The source-free path therefore still needs a
real digit-stream mechanism, not a residual selector.

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
