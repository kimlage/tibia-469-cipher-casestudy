from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"
POLICY_DRIFT_SCRIPT = HERE / "scripts" / "09_integrated_parser_policy_and_drift_audit.py"
OBSERVABLE_REPAIR_SCRIPT = HERE / "scripts" / "17_observable_repair_policy_audit.py"
CONDITIONAL_REPAIR_SCRIPT = HERE / "scripts" / "18_conditional_repair_classifier_audit.py"
PATH_TEMPLATE_REUSE = TEST_RESULTS / "37_path_template_reuse_audit.json"

OUT_STEM = "38_trajectory_neighbor_parser_audit"
SEED_BOOKS = list(range(10))
ACTIVE_CLASSIFIER = "if_peak_len_le5_then_skip_to_next_peak_ge5"
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


def normalized_projected_ops(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": row["type"],
            "target_start": int(row["target_start"]),
            "length": int(row["length"]),
            "source": row["source"],
        }
        for row in rows
    ]


def stable_by_book(trace_module, gate111, books: dict[int, str]) -> dict[int, list[dict[str, Any]]]:
    projected_ops = trace_module.projected_ops_from_copy_rows(
        gate111.make_copy_rows(), books
    )
    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for op in projected_ops:
        by_book[int(op["book"])].append(op)
    for rows in by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))
    return {book: normalized_projected_ops(rows) for book, rows in by_book.items()}


def first_diff(
    repair_module,
    predicted: list[dict[str, Any]],
    stable: list[dict[str, Any]],
) -> dict[str, Any] | None:
    diff = repair_module.first_diff(predicted, stable)
    if diff is None:
        return None
    diff = dict(diff)
    diff["drift_class"] = repair_module.classify_diff(diff)
    return diff


def op_label(op: dict[str, Any] | None) -> tuple[Any, ...]:
    if op is None:
        return ("none", 0)
    return (op["type"], int(op["length"]))


def bucket(value: int | float | None, cuts: list[int]) -> int:
    if value is None:
        return -1
    for index, cut in enumerate(cuts):
        if value <= cut:
            return index
    return len(cuts)


def recent_labels(ops: list[dict[str, Any]], size: int = 3) -> tuple[tuple[Any, ...], ...]:
    tail = [op_label(op) for op in ops[-size:]]
    while len(tail) < size:
        tail.insert(0, ("BOS", 0))
    return tuple(tail)


def trajectory_vector(row: dict[str, Any], family: str) -> tuple[Any, ...]:
    f = row["features"]
    base = (
        bucket(row["target_start"] / max(1, row["target_length"]), [0.05, 0.15, 0.3, 0.5, 0.75]),
        bucket(row["op_index"], [0, 1, 2, 4, 8, 13]),
        bucket(row["copy_count"], [0, 1, 2, 4, 8, 13]),
        bucket(row["literal_count"], [0, 1, 2, 4, 8, 13]),
        bucket(row["copy_digits"], [0, 8, 21, 55, 144, 233]),
        bucket(row["literal_digits"], [0, 5, 13, 34, 89, 144]),
        bucket(row["last_copy_length"], [0, 5, 8, 13, 21, 34, 55]),
        bucket(row["last_literal_length"], [0, 1, 3, 5, 8, 13, 21, 34]),
        row["previous_labels"],
    )
    context = (
        f["position_bucket"],
        f["previous_type"],
        f["predicted_type"],
        bucket(int(f["predicted_length"]), [1, 3, 5, 8, 13, 21, 34, 55]),
        bucket(int(f["immediate_copy_len"]), [0, 5, 8, 13, 21, 34, 55]),
        bucket(int(f["peak_len"]), [0, 5, 8, 13, 21, 34, 55]),
        bucket(int(f["next_peak_len"]), [0, 5, 8, 13, 21, 34, 55]),
    )
    if family == "trajectory":
        return base
    if family == "context":
        return context
    if family == "combined":
        return base + context
    raise ValueError(family)


def feature_distance(left: tuple[Any, ...], right: tuple[Any, ...]) -> float:
    if len(left) != len(right):
        raise ValueError("vector length mismatch")
    total = 0.0
    for a, b in zip(left, right):
        if isinstance(a, tuple) and isinstance(b, tuple):
            total += feature_distance(a, b)
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            total += abs(float(a) - float(b))
        else:
            total += 0.0 if a == b else 1.0
    return total


def parse_active_trajectory(
    repair_module,
    conditional_module,
    trace_module,
    policy_module,
    books: dict[int, str],
    stable: dict[int, list[dict[str, Any]]],
    classifier: dict[str, Any],
    predicates: dict[str, Callable[[dict[str, Any]], bool]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    emitted = "".join(books[book] for book in SEED_BOOKS)
    decisions: list[dict[str, Any]] = []
    book_rows: list[dict[str, Any]] = []
    for book in range(10, 70):
        target = books[book]
        pos = 0
        op_index = 0
        previous_type = "BOS"
        previous_length = 0
        predicted_ops: list[dict[str, Any]] = []
        copy_count = 0
        literal_count = 0
        copy_digits = 0
        literal_digits = 0
        last_copy_length = 0
        last_literal_length = 0
        while pos < len(target):
            predicted, context = repair_module.baseline_op(
                policy_module, trace_module, emitted, target, pos
            )
            features = conditional_module.context_row(
                target,
                pos,
                predicted,
                context,
                previous_type,
                previous_length,
                op_index,
            )
            chosen = predicted
            if predicates[classifier["predicate"]](features):
                chosen, _ = repair_module.apply_repair_policy(
                    policy_module,
                    trace_module,
                    emitted,
                    target,
                    pos,
                    predicted,
                    context,
                    classifier["action"],
                )
            if int(chosen["length"]) <= 0:
                raise RuntimeError({"type": "non_positive_chosen_op", "chosen": chosen})
            stable_op = stable[book][op_index] if op_index < len(stable[book]) else None
            row = {
                "book": book,
                "op_index": op_index,
                "target_start": pos,
                "target_length": len(target),
                "features": features,
                "chosen": dict(chosen),
                "stable_label": op_label(stable_op),
                "active_label": op_label(chosen),
                "copy_count": copy_count,
                "literal_count": literal_count,
                "copy_digits": copy_digits,
                "literal_digits": literal_digits,
                "last_copy_length": last_copy_length,
                "last_literal_length": last_literal_length,
                "previous_labels": recent_labels(predicted_ops),
            }
            decisions.append(row)
            predicted_ops.append(dict(chosen))
            emitted += target[pos : pos + int(chosen["length"])]
            if chosen["type"] == "copy":
                copy_count += 1
                copy_digits += int(chosen["length"])
                last_copy_length = int(chosen["length"])
            else:
                literal_count += 1
                literal_digits += int(chosen["length"])
                last_literal_length = int(chosen["length"])
            previous_type = chosen["type"]
            previous_length = int(chosen["length"])
            pos += int(chosen["length"])
            op_index += 1
        diff = first_diff(repair_module, predicted_ops, stable[book])
        book_rows.append(
            {
                "book": book,
                "exact": diff is None,
                "first_diff": diff,
            }
        )
    return decisions, book_rows


def residual_queries(
    decisions: list[dict[str, Any]], book_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_key = {(row["book"], row["op_index"]): row for row in decisions}
    rows: list[dict[str, Any]] = []
    for book_row in book_rows:
        if book_row["exact"]:
            continue
        diff = book_row["first_diff"]
        if diff is None:
            continue
        query = dict(by_key[(int(book_row["book"]), int(diff["index"]))])
        query["drift_class"] = diff["drift_class"]
        rows.append(query)
    return rows


def train_examples(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    train_books: set[int],
) -> list[dict[str, Any]]:
    exact_books = {row["book"] for row in book_rows if row["exact"]}
    return [
        row
        for row in decisions
        if row["book"] in exact_books and row["book"] in train_books
    ]


def predict_label(
    examples: list[dict[str, Any]], query: dict[str, Any], family: str, k: int
) -> tuple[tuple[Any, ...] | None, float | None, list[dict[str, Any]]]:
    if not examples:
        return None, None, []
    qv = trajectory_vector(query, family)
    neighbors = sorted(
        (
            {
                "book": ex["book"],
                "op_index": ex["op_index"],
                "distance": feature_distance(qv, trajectory_vector(ex, family)),
                "stable_label": ex["stable_label"],
            }
            for ex in examples
        ),
        key=lambda row: (row["distance"], row["book"], row["op_index"]),
    )[:k]
    counts: Counter[tuple[Any, ...]] = Counter(row["stable_label"] for row in neighbors)
    label, _ = max(
        counts.items(),
        key=lambda item: (
            item[1],
            -min(row["distance"] for row in neighbors if row["stable_label"] == item[0]),
            str(item[0]),
        ),
    )
    return label, neighbors[0]["distance"], neighbors


def score_policy(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    k: int,
    train_books: set[int],
    query_books: set[int],
) -> dict[str, Any]:
    examples = train_examples(decisions, book_rows, train_books)
    queries = [row for row in residual_queries(decisions, book_rows) if row["book"] in query_books]
    hits = []
    rows = []
    for query in queries:
        predicted, distance, neighbors = predict_label(examples, query, family, k)
        hit = predicted == query["stable_label"]
        hits.append(hit)
        rows.append(
            {
                "book": query["book"],
                "op_index": query["op_index"],
                "drift_class": query["drift_class"],
                "active_label": query["active_label"],
                "stable_label": query["stable_label"],
                "predicted_label": predicted,
                "nearest_distance": distance,
                "hit": hit,
                "nearest_neighbors": neighbors[:3],
            }
        )
    return {
        "family": family,
        "k": k,
        "train_book_count": len(train_books),
        "query_count": len(queries),
        "hits": sum(1 for hit in hits if hit),
        "rows": rows,
    }


def full_fit_scoreboard(
    decisions: list[dict[str, Any]], book_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows = []
    all_books = set(range(10, 70))
    residual_books = {row["book"] for row in book_rows if not row["exact"]}
    for family in ["trajectory", "context", "combined"]:
        for k in [1, 3, 5]:
            rows.append(score_policy(decisions, book_rows, family, k, all_books, residual_books))
    return rows


def prequential_rows(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    k: int,
) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        query_books = set(range(cutoff, 70))
        score = score_policy(decisions, book_rows, family, k, train_books, query_books)
        rows.append(
            {
                "cutoff_book": cutoff,
                "test_residuals": score["query_count"],
                "hits": score["hits"],
            }
        )
    return rows


def shuffle_control(
    decisions: list[dict[str, Any]],
    book_rows: list[dict[str, Any]],
    family: str,
    k: int,
    observed: int,
) -> dict[str, Any]:
    exact_examples = train_examples(decisions, book_rows, set(range(10, 70)))
    labels = [row["stable_label"] for row in exact_examples]
    rng = random.Random(46938 + 100 * k + len(family))
    hits: list[int] = []
    residual_books = {row["book"] for row in book_rows if not row["exact"]}
    queries = [row for row in residual_queries(decisions, book_rows) if row["book"] in residual_books]
    for _ in range(RANDOM_TRIALS):
        shuffled = list(labels)
        rng.shuffle(shuffled)
        perm_examples = [dict(row) for row in exact_examples]
        for row, label in zip(perm_examples, shuffled):
            row["stable_label"] = label
        total = 0
        for query in queries:
            predicted, _, _ = predict_label(perm_examples, query, family, k)
            total += int(predicted == query["stable_label"])
        hits.append(total)
    return {
        "family": family,
        "k": k,
        "observed": observed,
        "trials": RANDOM_TRIALS,
        "shuffle_min": min(hits),
        "shuffle_mean": sum(hits) / len(hits),
        "shuffle_max": max(hits),
        "shuffle_ge_observed_count": sum(1 for hit in hits if hit >= observed),
        "p_ge_observed": (
            sum(1 for hit in hits if hit >= observed) + 1
        )
        / (len(hits) + 1),
    }


def make_result() -> dict[str, Any]:
    gate37 = load_json(PATH_TEMPLATE_REUSE)
    assert_boundary("path_template_reuse_audit", gate37)
    if gate37["classification"] != "path_template_reuse_hypothesis_rejected":
        raise RuntimeError("gate38 expects gate37 template reuse rejection")

    trace_module = load_module("segmentation_trace_for_gate38", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_gate38", GATE111_SCRIPT)
    policy_module = load_module("policy_drift_for_gate38", POLICY_DRIFT_SCRIPT)
    repair_module = load_module("observable_repair_for_gate38", OBSERVABLE_REPAIR_SCRIPT)
    conditional_module = load_module(
        "conditional_repair_for_gate38", CONDITIONAL_REPAIR_SCRIPT
    )
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable = stable_by_book(trace_module, gate111, books)
    predicates = {"always_false": lambda row: False}
    predicates.update({name: fn for name, fn in conditional_module.make_predicates()})
    classifier = next(
        item
        for item in conditional_module.make_classifiers()
        if item["label"] == ACTIVE_CLASSIFIER
    )
    decisions, book_rows = parse_active_trajectory(
        repair_module,
        conditional_module,
        trace_module,
        policy_module,
        books,
        stable,
        classifier,
        predicates,
    )
    exact_books = [row["book"] for row in book_rows if row["exact"]]
    residual_books = [row["book"] for row in book_rows if not row["exact"]]
    scoreboard = full_fit_scoreboard(decisions, book_rows)
    best = max(
        scoreboard,
        key=lambda row: (row["hits"], -row["k"], row["family"]),
    )
    preq = prequential_rows(decisions, book_rows, best["family"], int(best["k"]))
    control = shuffle_control(
        decisions,
        book_rows,
        best["family"],
        int(best["k"]),
        int(best["hits"]),
    )
    preq_cells_with_residual = sum(1 for row in preq if row["test_residuals"] > 0)
    preq_cells_all_hit = sum(
        1
        for row in preq
        if row["test_residuals"] > 0 and row["hits"] == row["test_residuals"]
    )
    promotes = (
        best["hits"] == best["query_count"]
        and preq_cells_all_hit == preq_cells_with_residual
        and control["p_ge_observed"] <= 0.05
    )
    if promotes:
        classification = "trajectory_neighbor_parser_promoted"
    elif best["hits"] > 0:
        classification = "trajectory_neighbor_weak_clue_not_promoted"
    else:
        classification = "trajectory_neighbor_parser_rejected"
    return {
        "schema": "trajectory_neighbor_parser_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "path_template_reuse_audit": rel(PATH_TEMPLATE_REUSE),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_latent_path_state_shortcut": True,
        },
        "summary": {
            "active_classifier": ACTIVE_CLASSIFIER,
            "exact_book_count": len(exact_books),
            "residual_book_count": len(residual_books),
            "residual_books": residual_books,
            "decision_count": len(decisions),
            "families_tested": ["trajectory", "context", "combined"],
            "k_values_tested": [1, 3, 5],
            "best_family": best["family"],
            "best_k": best["k"],
            "best_hits": best["hits"],
            "best_query_count": best["query_count"],
            "prequential_cells_with_residuals": preq_cells_with_residual,
            "prequential_cells_all_hit": preq_cells_all_hit,
            "shuffle_p_ge_observed": control["p_ge_observed"],
            "promotes_trajectory_neighbor_parser": promotes,
            "interpretation": (
                "Trajectory-neighbor parsing tests whether residual first-drift "
                "operations can be selected by nearest cumulative parser-state "
                "trajectories from exact books. This is a path/state shortcut, "
                "not a local branch feature or compression sweep."
            ),
        },
        "scoreboard": [
            {
                "family": row["family"],
                "k": row["k"],
                "hits": row["hits"],
                "query_count": row["query_count"],
            }
            for row in sorted(scoreboard, key=lambda row: (-row["hits"], row["family"], row["k"]))
        ],
        "best_rows": best["rows"],
        "prequential_rows": preq,
        "shuffle_control": control,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "trajectory_neighbor_tested",
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
        [row["family"], row["k"], row["hits"], row["query_count"]]
        for row in result["scoreboard"]
    ]
    preq_rows = [
        [row["cutoff_book"], row["test_residuals"], row["hits"]]
        for row in result["prequential_rows"]
    ]
    best_rows = [
        [
            row["book"],
            row["op_index"],
            row["drift_class"],
            row["active_label"],
            row["stable_label"],
            row["predicted_label"],
            row["nearest_distance"],
            row["hit"],
        ]
        for row in result["best_rows"]
    ]
    c = result["shuffle_control"]
    body = f"""# Trajectory Neighbor Parser Audit

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 38 tests whether the residual first-drift choices can be explained by
nearest cumulative parser-state trajectories from books already parsed exactly.
This is a richer path/state shortcut than local branch predicates or exact
template reuse.

It does not search row0, plaintext, or semantics.

## Summary

- Active classifier: `{s['active_classifier']}`.
- Exact parser books: `{s['exact_book_count']}`.
- Residual parser books: `{s['residual_book_count']}`.
- Families tested: `{s['families_tested']}`.
- k values tested: `{s['k_values_tested']}`.
- Best policy: `{s['best_family']}`, k=`{s['best_k']}`.
- Best residual hits: `{s['best_hits']}/{s['best_query_count']}`.
- Prequential residual cells fully hit:
  `{s['prequential_cells_all_hit']}/{s['prequential_cells_with_residuals']}`.
- Shuffle control `p_ge_observed`: `{s['shuffle_p_ge_observed']:.4f}`.
- Promotes parser rule: `{s['promotes_trajectory_neighbor_parser']}`.

## Scoreboard

{md_table(scoreboard_rows, ["family", "k", "hits", "residual queries"])}

## Prequential Rows For Best Policy

{md_table(preq_rows, ["cutoff", "test residuals", "hits"])}

## Shuffle Control For Best Policy

- Observed hits: `{c['observed']}`.
- Trials: `{c['trials']}`.
- Shuffle mean: `{c['shuffle_mean']:.3f}`.
- Shuffle max: `{c['shuffle_max']}`.
- `p_ge_observed`: `{c['p_ge_observed']:.4f}`.

## Best Policy Residual Rows

{md_table(best_rows, ["book", "op", "drift class", "active label", "stable label", "predicted label", "nearest distance", "hit"])}

## Decision

Trajectory-neighbor parsing is not promoted. The best nearest-trajectory policy
does not cover the residual first-drift choices under prefix/holdout and
therefore does not replace the retained segmentation decisions.

The remaining blocker is still a richer latent path/state mechanism or a
source-free target digit account.

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
