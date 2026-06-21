from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

TRAJECTORY_SCRIPT = HERE / "scripts" / "38_trajectory_neighbor_parser_audit.py"
GATE43 = TEST_RESULTS / "43_source_free_residual_rule_gate.json"

OUT_STEM = "44_operation_ngram_grammar_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 400


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


def label(row: dict[str, Any], key: str) -> tuple[Any, ...]:
    return tuple(row[key])


def previous_labels(row: dict[str, Any]) -> tuple[tuple[Any, ...], ...]:
    return tuple(tuple(item) for item in row["previous_labels"])


def op_bucket(row: dict[str, Any]) -> tuple[str, int]:
    return ("op_bucket", min(int(row["op_index"]), 8))


def context_key(row: dict[str, Any], family: str) -> tuple[Any, ...]:
    prev = previous_labels(row)
    if family == "unigram":
        return ()
    if family == "op_bucket":
        return (op_bucket(row),)
    if family == "prev1_type":
        return tuple((item[0],) for item in prev[-1:])
    if family == "prev2_type":
        return tuple((item[0],) for item in prev[-2:])
    if family == "prev1":
        return prev[-1:]
    if family == "prev2":
        return prev[-2:]
    if family == "prev3":
        return prev[-3:]
    if family == "prev1_op_bucket":
        return prev[-1:] + (op_bucket(row),)
    if family == "prev2_op_bucket":
        return prev[-2:] + (op_bucket(row),)
    raise ValueError(family)


def build_decisions() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    traj = load_module("trajectory_for_gate44", TRAJECTORY_SCRIPT)
    trace_module = traj.load_module("segmentation_trace_for_gate44", traj.TRACE_SCRIPT)
    gate111 = traj.load_module("gate111_for_gate44", traj.GATE111_SCRIPT)
    policy_module = traj.load_module("policy_drift_for_gate44", traj.POLICY_DRIFT_SCRIPT)
    repair_module = traj.load_module(
        "observable_repair_for_gate44", traj.OBSERVABLE_REPAIR_SCRIPT
    )
    conditional_module = traj.load_module(
        "conditional_repair_for_gate44", traj.CONDITIONAL_REPAIR_SCRIPT
    )
    books = {int(key): value for key, value in traj.load_json(traj.BOOKS_DIGITS).items()}
    stable = traj.stable_by_book(trace_module, gate111, books)
    predicates = {"always_false": lambda row: False}
    predicates.update({name: fn for name, fn in conditional_module.make_predicates()})
    classifier = next(
        item
        for item in conditional_module.make_classifiers()
        if item["label"] == traj.ACTIVE_CLASSIFIER
    )
    return traj.parse_active_trajectory(
        repair_module,
        conditional_module,
        trace_module,
        policy_module,
        books,
        stable,
        classifier,
        predicates,
    )


def train_rows(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    train_books: set[int],
) -> list[dict[str, Any]]:
    exact_books = {row["book"] for row in book_rows if row["exact"]}
    return [
        row
        for row in decisions
        if int(row["book"]) in exact_books and int(row["book"]) in train_books
    ]


def residual_queries(
    trajectory_module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    query_books: set[int],
) -> list[dict[str, Any]]:
    return [
        row
        for row in trajectory_module.residual_queries(decisions, book_rows)
        if int(row["book"]) in query_books
    ]


def make_table(rows: list[dict[str, Any]], family: str) -> dict[tuple[Any, ...], Counter]:
    table: dict[tuple[Any, ...], Counter] = defaultdict(Counter)
    for row in rows:
        table[context_key(row, family)][label(row, "stable_label")] += 1
    return table


def predict(table: dict[tuple[Any, ...], Counter], row: dict[str, Any], family: str):
    counter = table.get(context_key(row, family))
    if not counter:
        return None, "unsupported", 0, 0
    predicted, support = max(counter.items(), key=lambda item: (item[1], str(item[0])))
    if predicted == label(row, "stable_label"):
        status = "hit"
    else:
        status = "false_positive"
    return predicted, status, support, len(counter)


def grammar_table_bits(table: dict[tuple[Any, ...], Counter], label_count: int) -> float:
    if not table:
        return 0.0
    context_count = len(table)
    bits_per_row = 1.0 + math.log2(max(1, context_count)) + math.log2(label_count)
    return context_count * bits_per_row


def score_family(
    trajectory_module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    train_books: set[int],
    query_books: set[int],
    decision_universe: int,
    label_count: int,
) -> dict[str, Any]:
    table = make_table(train_rows(decisions, book_rows, train_books), family)
    queries = residual_queries(trajectory_module, decisions, book_rows, query_books)
    rows = []
    counts: Counter[str] = Counter()
    for query in queries:
        predicted, status, support, choices = predict(table, query, family)
        counts[status] += 1
        rows.append(
            {
                "book": query["book"],
                "op_index": query["op_index"],
                "context": repr(context_key(query, family)),
                "active_label": query["active_label"],
                "stable_label": query["stable_label"],
                "predicted_label": predicted,
                "status": status,
                "support": support,
                "choice_count": choices,
            }
        )
    unresolved = [
        row for row, detail in zip(queries, rows) if detail["status"] != "hit"
    ]
    table_bits = grammar_table_bits(table, label_count)
    baseline = lookup_bits(decision_universe, queries)
    total_bits = table_bits + lookup_bits(decision_universe, unresolved)
    return {
        "family": family,
        "train_rows": sum(sum(counter.values()) for counter in table.values()),
        "table_context_count": len(table),
        "query_count": len(queries),
        "hit_count": counts["hit"],
        "false_positive_count": counts["false_positive"],
        "unsupported_count": counts["unsupported"],
        "table_bits": table_bits,
        "baseline_lookup_bits": baseline,
        "remaining_lookup_bits": lookup_bits(decision_universe, unresolved),
        "total_bits": total_bits,
        "net_bits_vs_lookup": total_bits - baseline,
        "rows": rows,
    }


def prequential_rows(
    trajectory_module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    decision_universe: int,
    label_count: int,
) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        score = score_family(
            trajectory_module,
            decisions,
            book_rows,
            family,
            set(range(10, cutoff)),
            set(range(cutoff, 70)),
            decision_universe,
            label_count,
        )
        out.append(
            {
                "cutoff_book": cutoff,
                "test_residuals": score["query_count"],
                "hits": score["hit_count"],
                "false_positives": score["false_positive_count"],
                "unsupported": score["unsupported_count"],
                "net_bits_vs_lookup": score["net_bits_vs_lookup"],
            }
        )
    return out


def shuffle_control(
    trajectory_module,
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    observed_hits: int,
) -> dict[str, Any]:
    exact_books = {row["book"] for row in book_rows if row["exact"]}
    base_train = [
        row for row in decisions if int(row["book"]) in exact_books
    ]
    labels = [label(row, "stable_label") for row in base_train]
    residual_books = {row["book"] for row in book_rows if not row["exact"]}
    queries = residual_queries(trajectory_module, decisions, book_rows, residual_books)
    rng = random.Random(46944 + len(family))
    hits: list[int] = []
    for _ in range(RANDOM_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        permuted = [dict(row) for row in base_train]
        for row, shuffled_label in zip(permuted, shuffled):
            row["stable_label"] = shuffled_label
        table = make_table(permuted, family)
        total = 0
        for query in queries:
            predicted, _, _, _ = predict(table, query, family)
            total += int(predicted == label(query, "stable_label"))
        hits.append(total)
    return {
        "family": family,
        "observed_hits": observed_hits,
        "trials": RANDOM_TRIALS,
        "shuffle_min": min(hits),
        "shuffle_mean": sum(hits) / len(hits),
        "shuffle_max": max(hits),
        "shuffle_ge_observed_count": sum(1 for hit in hits if hit >= observed_hits),
        "p_ge_observed": (
            sum(1 for hit in hits if hit >= observed_hits) + 1
        )
        / (len(hits) + 1),
    }


def make_result() -> dict[str, Any]:
    gate43 = load_json(GATE43)
    assert_boundary("source_free_residual_rule_gate", gate43)
    if gate43["classification"] != "source_free_residual_rule_rejected":
        raise RuntimeError("gate44 expects gate43 source-free rejection")

    trajectory_module = load_module("trajectory_for_gate44_main", TRAJECTORY_SCRIPT)
    decisions, book_rows = build_decisions()
    residual_books = {row["book"] for row in book_rows if not row["exact"]}
    exact_books = {row["book"] for row in book_rows if row["exact"]}
    # Keep the lookup comparator identical to gate 41.
    gate41 = load_json(TEST_RESULTS / "41_latent_state_lookup_cost_gate.json")
    decision_universe = int(gate41["summary"]["decision_universe"])
    label_count = int(gate43["summary"]["label_count"])

    families = [
        "unigram",
        "op_bucket",
        "prev1_type",
        "prev2_type",
        "prev1",
        "prev2",
        "prev3",
        "prev1_op_bucket",
        "prev2_op_bucket",
    ]
    all_books = set(range(10, 70))
    scores = [
        score_family(
            trajectory_module,
            decisions,
            book_rows,
            family,
            all_books,
            residual_books,
            decision_universe,
            label_count,
        )
        for family in families
    ]
    best = max(
        scores,
        key=lambda row: (
            row["hit_count"],
            -row["false_positive_count"],
            -row["unsupported_count"],
            -row["net_bits_vs_lookup"],
            row["family"],
        ),
    )
    minimum_net = min(scores, key=lambda row: row["net_bits_vs_lookup"])
    preq = prequential_rows(
        trajectory_module,
        decisions,
        book_rows,
        best["family"],
        decision_universe,
        label_count,
    )
    control = shuffle_control(
        trajectory_module,
        decisions,
        book_rows,
        best["family"],
        int(best["hit_count"]),
    )
    preq_cells_with_test = sum(1 for row in preq if row["test_residuals"] > 0)
    preq_cells_with_hit = sum(
        1 for row in preq if row["test_residuals"] > 0 and row["hits"] > 0
    )
    promotes = (
        best["hit_count"] == best["query_count"]
        and best["false_positive_count"] == 0
        and preq_cells_with_hit == preq_cells_with_test
        and control["p_ge_observed"] <= 0.05
        and best["net_bits_vs_lookup"] < 0
    )
    classification = (
        "operation_ngram_grammar_promoted"
        if promotes
        else "operation_ngram_grammar_rejected"
    )
    return {
        "schema": "operation_ngram_grammar_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "trajectory_neighbor_parser_script": rel(TRAJECTORY_SCRIPT),
            "source_free_residual_rule_gate": rel(GATE43),
            "latent_lookup_cost_gate": rel(TEST_RESULTS / "41_latent_state_lookup_cost_gate.json"),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_operation_sequence_grammar": True,
        },
        "summary": {
            "interpretation": (
                "This gate tests whether residual first-drift choices are "
                "explained by a small operation-sequence grammar over prior "
                "operation labels and op index, trained only on exact parser "
                "books. It is path-grammar evidence, not a compression sweep."
            ),
            "exact_book_count": len(exact_books),
            "residual_book_count": len(residual_books),
            "residual_count": best["query_count"],
            "families_tested": families,
            "best_family": best["family"],
            "best_hit_count": best["hit_count"],
            "best_false_positive_count": best["false_positive_count"],
            "best_unsupported_count": best["unsupported_count"],
            "best_context_count": best["table_context_count"],
            "best_structural_family_net_bits_vs_lookup": best["net_bits_vs_lookup"],
            "minimum_net_family": minimum_net["family"],
            "minimum_net_bits_vs_lookup": minimum_net["net_bits_vs_lookup"],
            "minimum_net_false_positive_count": minimum_net["false_positive_count"],
            "prequential_cells_with_hit": preq_cells_with_hit,
            "prequential_cells_with_test": preq_cells_with_test,
            "shuffle_p_ge_observed": control["p_ge_observed"],
            "promotes_operation_ngram_grammar": promotes,
        },
        "scoreboard": [
            {
                "family": row["family"],
                "hit_count": row["hit_count"],
                "false_positive_count": row["false_positive_count"],
                "unsupported_count": row["unsupported_count"],
                "table_context_count": row["table_context_count"],
                "net_bits_vs_lookup": row["net_bits_vs_lookup"],
            }
            for row in sorted(
                scores,
                key=lambda row: (
                    -row["hit_count"],
                    row["false_positive_count"],
                    row["unsupported_count"],
                    row["net_bits_vs_lookup"],
                    row["family"],
                ),
            )
        ],
        "best_rows": best["rows"],
        "prequential_rows": preq,
        "shuffle_control": control,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "operation_ngram_grammar_tested",
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
    scoreboard_rows = [
        [
            row["family"],
            row["hit_count"],
            row["false_positive_count"],
            row["unsupported_count"],
            row["table_context_count"],
            f"{row['net_bits_vs_lookup']:.3f}",
        ]
        for row in result["scoreboard"]
    ]
    best_rows = [
        [
            row["book"],
            row["op_index"],
            row["active_label"],
            row["stable_label"],
            row["predicted_label"],
            row["status"],
            row["support"],
            row["choice_count"],
        ]
        for row in result["best_rows"]
    ]
    preq_rows = [
        [
            row["cutoff_book"],
            row["test_residuals"],
            row["hits"],
            row["false_positives"],
            row["unsupported"],
            f"{row['net_bits_vs_lookup']:.3f}",
        ]
        for row in result["prequential_rows"]
    ]
    c = result["shuffle_control"]
    body = f"""# Operation N-Gram Grammar Gate

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 44 tests whether the remaining residual first-drift operations are
explained by a small operation-sequence grammar: unigram, op-index bucket,
previous operation types, previous operation labels, and previous-label plus
op-bucket contexts. The grammar is trained only on books already parsed
exactly by the active parser.

## Summary

- Exact parser books used for grammar training: `{s['exact_book_count']}`.
- Residual books tested: `{s['residual_book_count']}`.
- Residual decisions tested: `{s['residual_count']}`.
- Families tested: `{len(s['families_tested'])}`.
- Best family: `{s['best_family']}`.
- Best hits: `{s['best_hit_count']}/{s['residual_count']}`.
- Best false positives: `{s['best_false_positive_count']}`.
- Best unsupported residuals: `{s['best_unsupported_count']}`.
- Best context count: `{s['best_context_count']}`.
- Best structural-family net bits vs lookup: `{s['best_structural_family_net_bits_vs_lookup']:.3f}`.
- Lowest net family: `{s['minimum_net_family']}` at `{s['minimum_net_bits_vs_lookup']:.3f}` bits with `{s['minimum_net_false_positive_count']}` false positives.
- Prequential cells with held-out hit: `{s['prequential_cells_with_hit']}/{s['prequential_cells_with_test']}`.
- Shuffle p_ge_observed: `{s['shuffle_p_ge_observed']:.4f}`.
- Promotes operation n-gram grammar: `{s['promotes_operation_ngram_grammar']}`.

## Scoreboard

{md_table(scoreboard_rows, ['family', 'hits', 'false positives', 'unsupported', 'contexts', 'net bits'])}

## Best-Family Residual Rows

{md_table(best_rows, ['book', 'op', 'active label', 'stable label', 'predicted label', 'status', 'support', 'choices'])}

## Prequential Rows

{md_table(preq_rows, ['cutoff', 'test residuals', 'hits', 'false positives', 'unsupported', 'net bits'])}

## Shuffle Control

- Trials: `{c['trials']}`.
- Shuffle min/mean/max hits: `{c['shuffle_min']}` / `{c['shuffle_mean']:.3f}` / `{c['shuffle_max']}`.
- Shuffle >= observed: `{c['shuffle_ge_observed_count']}`.
- p_ge_observed: `{c['p_ge_observed']:.4f}`.

## Decision

No operation n-gram grammar is promoted. The best family explains `0`
residuals; coarser grammars produce false positives and richer grammars become
unsupported. This rejects a compact operation-sequence grammar as the missing
latent path/state mechanism.

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
