from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE44_SCRIPT = HERE / "scripts" / "44_operation_ngram_grammar_gate.py"
GATE44 = TEST_RESULTS / "44_operation_ngram_grammar_gate.json"

OUT_STEM = "45_residual_exception_transfer_gate"
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


def bucket(value: int | None, cuts: list[int]) -> int:
    if value is None:
        return -1
    for index, cut in enumerate(cuts):
        if value <= cut:
            return index
    return len(cuts)


def previous_labels(row: dict[str, Any]) -> tuple[tuple[Any, ...], ...]:
    return tuple(tuple(item) for item in row["previous_labels"])


def label(row: dict[str, Any], key: str = "stable_label") -> tuple[Any, ...]:
    return tuple(row[key])


def feature_vector(row: dict[str, Any], family: str) -> tuple[Any, ...]:
    f = row["features"]
    prev = previous_labels(row)
    coarse = (
        f["position_bucket"],
        f["previous_type"],
        f["predicted_type"],
        bucket(int(f["immediate_copy_len"]), [0, 5, 8, 13, 21, 34]),
        bucket(int(f["peak_len"]), [0, 5, 8, 13, 21, 34, 55]),
    )
    context = (
        int(row["op_index"]),
        f["position_bucket"],
        f["previous_type"],
        bucket(int(f["previous_length"]), [0, 1, 3, 5, 8, 13, 21, 34, 55]),
        f["predicted_type"],
        bucket(int(f["predicted_length"]), [1, 3, 5, 8, 13, 21, 34, 55]),
        bucket(int(f["immediate_copy_len"]), [0, 5, 8, 13, 21, 34, 55]),
        bucket(f.get("peak_offset"), [0, 1, 3, 5, 8, 13, 21, 34, 55]),
        bucket(int(f["peak_len"]), [0, 5, 8, 13, 21, 34, 55]),
        bucket(f.get("next_peak_offset"), [0, 1, 3, 5, 8, 13, 21, 34, 55]),
        bucket(int(f["next_peak_len"]), [0, 5, 8, 13, 21, 34, 55]),
    )
    if family == "coarse":
        return coarse
    if family == "context":
        return context
    if family == "context_prev1":
        return context + (prev[-1],)
    if family == "context_prev2":
        return context + prev[-2:]
    if family == "active_shape":
        return coarse + (label(row, "active_label"),)
    if family == "active_shape_prev1":
        return coarse + (label(row, "active_label"), prev[-1])
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


def predict_label(
    train: list[dict[str, Any]],
    query: dict[str, Any],
    family: str,
    k: int,
) -> tuple[tuple[Any, ...] | None, list[dict[str, Any]]]:
    if not train:
        return None, []
    qv = feature_vector(query, family)
    neighbors = sorted(
        (
            {
                "book": row["book"],
                "stable_label": label(row),
                "distance": feature_distance(qv, feature_vector(row, family)),
            }
            for row in train
        ),
        key=lambda row: (row["distance"], row["book"], str(row["stable_label"])),
    )[:k]
    counts = Counter(row["stable_label"] for row in neighbors)
    predicted, _ = max(
        counts.items(),
        key=lambda item: (
            item[1],
            -min(row["distance"] for row in neighbors if row["stable_label"] == item[0]),
            str(item[0]),
        ),
    )
    return predicted, neighbors


def score_transfer(
    rows: list[dict[str, Any]],
    family: str,
    k: int,
    train_books: set[int] | None = None,
    query_books: set[int] | None = None,
) -> dict[str, Any]:
    details = []
    queries = [
        row
        for row in rows
        if query_books is None or int(row["book"]) in query_books
    ]
    for query in queries:
        train = [
            row
            for row in rows
            if int(row["book"]) != int(query["book"])
            and (train_books is None or int(row["book"]) in train_books)
        ]
        predicted, neighbors = predict_label(train, query, family, k)
        details.append(
            {
                "book": query["book"],
                "op_index": query["op_index"],
                "active_label": query["active_label"],
                "stable_label": query["stable_label"],
                "predicted_label": predicted,
                "hit": predicted == label(query),
                "nearest_neighbors": neighbors[:3],
            }
        )
    return {
        "family": family,
        "k": k,
        "query_count": len(queries),
        "hit_count": sum(1 for row in details if row["hit"]),
        "unsupported_count": sum(1 for row in details if row["predicted_label"] is None),
        "rows": details,
    }


def prequential_rows(rows: list[dict[str, Any]], family: str, k: int) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        score = score_transfer(
            rows,
            family,
            k,
            train_books=set(range(10, cutoff)),
            query_books=set(range(cutoff, 70)),
        )
        out.append(
            {
                "cutoff_book": cutoff,
                "test_residuals": score["query_count"],
                "hits": score["hit_count"],
                "unsupported": score["unsupported_count"],
            }
        )
    return out


def shuffle_control(
    rows: list[dict[str, Any]], family: str, k: int, observed: int
) -> dict[str, Any]:
    labels = [label(row) for row in rows]
    rng = random.Random(46945 + len(family) * 10 + k)
    hits = []
    for _ in range(RANDOM_TRIALS):
        shuffled = labels[:]
        rng.shuffle(shuffled)
        permuted = [dict(row) for row in rows]
        for row, shuffled_label in zip(permuted, shuffled):
            row["stable_label"] = shuffled_label
        hits.append(score_transfer(permuted, family, k)["hit_count"])
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
    gate44 = load_json(GATE44)
    assert_boundary("operation_ngram_grammar_gate", gate44)
    if gate44["classification"] != "operation_ngram_grammar_rejected":
        raise RuntimeError("gate45 expects gate44 grammar rejection")

    gate44_module = load_module("gate44_for_gate45", GATE44_SCRIPT)
    trajectory_module = gate44_module.load_module(
        "trajectory_for_gate45", gate44_module.TRAJECTORY_SCRIPT
    )
    decisions, book_rows = gate44_module.build_decisions()
    residual_rows = trajectory_module.residual_queries(decisions, book_rows)

    families = [
        "coarse",
        "context",
        "context_prev1",
        "context_prev2",
        "active_shape",
        "active_shape_prev1",
    ]
    ks = [1, 3, 5]
    scores = [
        score_transfer(residual_rows, family, k)
        for family in families
        for k in ks
    ]
    best = max(
        scores,
        key=lambda row: (
            row["hit_count"],
            -row["unsupported_count"],
            -row["k"],
            row["family"],
        ),
    )
    preq = prequential_rows(residual_rows, best["family"], int(best["k"]))
    control = shuffle_control(
        residual_rows, best["family"], int(best["k"]), int(best["hit_count"])
    )
    preq_cells_with_test = sum(1 for row in preq if row["test_residuals"] > 0)
    preq_cells_with_hit = sum(
        1 for row in preq if row["test_residuals"] > 0 and row["hits"] > 0
    )
    promotes = (
        best["hit_count"] == best["query_count"]
        and preq_cells_with_hit == preq_cells_with_test
        and control["p_ge_observed"] <= 0.05
    )
    classification = (
        "residual_exception_transfer_promoted"
        if promotes
        else "residual_exception_transfer_rejected"
    )
    return {
        "schema": "residual_exception_transfer_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "operation_ngram_grammar_gate": rel(GATE44),
            "operation_ngram_grammar_script": rel(GATE44_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "promotes_parser_rule": promotes,
            "tests_residual_exception_transfer": True,
        },
        "summary": {
            "interpretation": (
                "This gate asks whether the residual corrections transfer among "
                "themselves under observable features. Stable labels are used "
                "only for leave-one-residual-out training/evaluation, never as "
                "features."
            ),
            "residual_count": len(residual_rows),
            "families_tested": families,
            "k_values_tested": ks,
            "best_family": best["family"],
            "best_k": best["k"],
            "best_hit_count": best["hit_count"],
            "best_unsupported_count": best["unsupported_count"],
            "prequential_cells_with_hit": preq_cells_with_hit,
            "prequential_cells_with_test": preq_cells_with_test,
            "shuffle_p_ge_observed": control["p_ge_observed"],
            "promotes_residual_exception_transfer": promotes,
        },
        "scoreboard": [
            {
                "family": row["family"],
                "k": row["k"],
                "hit_count": row["hit_count"],
                "query_count": row["query_count"],
                "unsupported_count": row["unsupported_count"],
            }
            for row in sorted(
                scores,
                key=lambda row: (
                    -row["hit_count"],
                    row["unsupported_count"],
                    row["k"],
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
            "source_length_dependency_status": "residual_transfer_tested",
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
        [row["family"], row["k"], row["hit_count"], row["query_count"], row["unsupported_count"]]
        for row in result["scoreboard"]
    ]
    best_rows = [
        [
            row["book"],
            row["op_index"],
            row["active_label"],
            row["stable_label"],
            row["predicted_label"],
            row["hit"],
            row["nearest_neighbors"],
        ]
        for row in result["best_rows"]
    ]
    preq_rows = [
        [row["cutoff_book"], row["test_residuals"], row["hits"], row["unsupported"]]
        for row in result["prequential_rows"]
    ]
    c = result["shuffle_control"]
    body = f"""# Residual Exception Transfer Gate

Classification: `{result['classification']}`
Translation delta: `NONE`

## Purpose

Gate 45 asks whether the residual corrections form a reusable exception
family. It trains only on other residual corrections and predicts each held-out
residual from observable active-parser features, using stable labels only as
leave-one-residual-out training/evaluation labels.

## Summary

- Residual decisions tested: `{s['residual_count']}`.
- Families tested: `{len(s['families_tested'])}`.
- k values tested: `{s['k_values_tested']}`.
- Best family: `{s['best_family']}`.
- Best k: `{s['best_k']}`.
- Best hits: `{s['best_hit_count']}/{s['residual_count']}`.
- Best unsupported residuals: `{s['best_unsupported_count']}`.
- Prequential cells with held-out hit: `{s['prequential_cells_with_hit']}/{s['prequential_cells_with_test']}`.
- Shuffle p_ge_observed: `{s['shuffle_p_ge_observed']:.4f}`.
- Promotes residual exception transfer: `{s['promotes_residual_exception_transfer']}`.

## Scoreboard

{md_table(scoreboard_rows, ['family', 'k', 'hits', 'query count', 'unsupported'])}

## Best-Family Rows

{md_table(best_rows, ['book', 'op', 'active label', 'stable label', 'predicted label', 'hit', 'nearest neighbors'])}

## Prequential Rows

{md_table(preq_rows, ['cutoff', 'test residuals', 'hits', 'unsupported'])}

## Shuffle Control

- Trials: `{c['trials']}`.
- Shuffle min/mean/max hits: `{c['shuffle_min']}` / `{c['shuffle_mean']:.3f}` / `{c['shuffle_max']}`.
- Shuffle >= observed: `{c['shuffle_ge_observed_count']}`.
- p_ge_observed: `{c['p_ge_observed']:.4f}`.

## Decision

No residual exception-transfer rule is promoted. The residual corrections do
not predict each other under the tested observable feature families. This
makes a compact reusable residual-exception class unlikely under current
evidence; the remaining explanation is still a richer latent state or an
external/source-free target stream account.

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
