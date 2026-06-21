from __future__ import annotations

import importlib.util
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE22_SCRIPT = HERE / "scripts" / "22_residual_branch_continuation_audit.py"
GATE48 = TEST_RESULTS / "48_residual_site_detector_gate.json"

OUT_STEM = "49_book_skeleton_alignment_gate"
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


def length_bucket(value: int) -> str:
    for cut in [1, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]:
        if value <= cut:
            return f"le{cut}"
    return "gt233"


def op_label(op: dict[str, Any]) -> tuple[str, int]:
    return (op["type"], int(op["length"]))


def token(label: tuple[str, int], family: str) -> tuple[Any, ...]:
    op_type, length = label
    if family.endswith("type_only"):
        return (op_type,)
    if family.endswith("type_len_bucket"):
        return (op_type, length_bucket(length))
    if family.endswith("exact_len"):
        return (op_type, length)
    raise ValueError(family)


def edit_distance(left: list[tuple[Any, ...]], right: list[tuple[Any, ...]]) -> int:
    if not left:
        return len(right)
    if not right:
        return len(left)
    prev = list(range(len(right) + 1))
    for i, a in enumerate(left, start=1):
        cur = [i]
        for j, b in enumerate(right, start=1):
            cur.append(
                min(
                    prev[j] + 1,
                    cur[j - 1] + 1,
                    prev[j - 1] + (0 if a == b else 1),
                )
            )
        prev = cur
    return prev[-1]


def prefix_distance(
    query_prefix: list[tuple[str, int]],
    example_prefix: list[tuple[str, int]],
    family: str,
) -> float:
    q_tokens = [token(label, family) for label in query_prefix]
    e_tokens = [token(label, family) for label in example_prefix]
    if family.startswith("tail3"):
        q_tokens = q_tokens[-3:]
        e_tokens = e_tokens[-3:]
        width = 3
        while len(q_tokens) < width:
            q_tokens.insert(0, ("BOS",))
        while len(e_tokens) < width:
            e_tokens.insert(0, ("BOS",))
        return sum(0 if a == b else 1 for a, b in zip(q_tokens, e_tokens))
    if family.startswith("tail5"):
        q_tokens = q_tokens[-5:]
        e_tokens = e_tokens[-5:]
        width = 5
        while len(q_tokens) < width:
            q_tokens.insert(0, ("BOS",))
        while len(e_tokens) < width:
            e_tokens.insert(0, ("BOS",))
        return sum(0 if a == b else 1 for a, b in zip(q_tokens, e_tokens))
    distance = edit_distance(q_tokens, e_tokens)
    return distance / max(1, len(q_tokens), len(e_tokens))


def branch_label(branch: dict[str, Any]) -> tuple[str, int]:
    return op_label(branch["op"])


def build_rows() -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    gate22 = load_module("gate22_for_gate49", GATE22_SCRIPT)
    decisions = gate22.collect_decisions()["decisions"]
    by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in decisions:
        by_book[int(row["book"])].append(row)
    for rows in by_book.values():
        rows.sort(key=lambda item: int(item["stable_index"]))

    enriched: list[dict[str, Any]] = []
    for book, rows in sorted(by_book.items()):
        prefix: list[tuple[str, int]] = []
        for row in rows:
            item = dict(row)
            item["book"] = book
            item["prefix_labels"] = list(prefix)
            item["stable_label"] = op_label(row["stable_op"])
            item["active_label"] = op_label(row["active_op"])
            item["branch_labels"] = [branch_label(branch) for branch in row["branches"]]
            item["stable_branch_match_count"] = sum(
                1
                for branch in row["branches"]
                if branch_label(branch) == item["stable_label"]
            )
            enriched.append(item)
            prefix.append(item["active_label"])
    return enriched, by_book


def exact_books(by_book: dict[int, list[dict[str, Any]]]) -> set[int]:
    return {
        book
        for book, rows in by_book.items()
        if rows and all(row["kind"] == "clean_control" for row in rows)
    }


def choose_label(
    examples: list[dict[str, Any]],
    query: dict[str, Any],
    family: str,
    k: int,
) -> tuple[tuple[str, int] | None, list[dict[str, Any]]]:
    if not examples:
        return None, []
    ranked = sorted(
        (
            {
                "book": row["book"],
                "stable_index": row["stable_index"],
                "distance": prefix_distance(
                    query["prefix_labels"], row["prefix_labels"], family
                ),
                "stable_label": row["stable_label"],
            }
            for row in examples
            if row["book"] != query["book"]
        ),
        key=lambda row: (
            row["distance"],
            abs(int(row["stable_index"]) - int(query["stable_index"])),
            row["book"],
            row["stable_index"],
        ),
    )[:k]
    if not ranked:
        return None, []
    counts: Counter[tuple[str, int]] = Counter(row["stable_label"] for row in ranked)
    predicted, _count = max(
        counts.items(),
        key=lambda item: (
            item[1],
            -min(row["distance"] for row in ranked if row["stable_label"] == item[0]),
            str(item[0]),
        ),
    )
    return predicted, ranked[:5]


def evaluate_prediction(
    query: dict[str, Any],
    predicted: tuple[str, int] | None,
    neighbors: list[dict[str, Any]],
) -> dict[str, Any]:
    matching = [
        branch for branch in query["branches"] if branch_label(branch) == predicted
    ]
    unique_branch = matching[0] if len(matching) == 1 else None
    label_hit = predicted == query["stable_label"]
    unique_branch_hit = bool(unique_branch and unique_branch["is_stable"])
    predicted_changes_clean = (
        query["kind"] == "clean_control"
        and predicted is not None
        and predicted != query["stable_label"]
    )
    return {
        "book": query["book"],
        "stable_index": query["stable_index"],
        "target_start": query["target_start"],
        "kind": query["kind"],
        "drift_class": query["drift_class"],
        "active_label": query["active_label"],
        "stable_label": query["stable_label"],
        "predicted_label": predicted,
        "label_hit": label_hit,
        "matching_branch_count": len(matching),
        "unique_branch_hit": unique_branch_hit,
        "predicted_changes_clean": predicted_changes_clean,
        "neighbor_sample": neighbors,
    }


def score_config(
    rows: list[dict[str, Any]],
    exact_book_set: set[int],
    family: str,
    k: int,
    example_books: set[int],
    query_books: set[int],
) -> dict[str, Any]:
    examples = [
        row
        for row in rows
        if row["book"] in exact_book_set and row["book"] in example_books
    ]
    queries = [row for row in rows if row["book"] in query_books]
    detail_rows = []
    for query in queries:
        predicted, neighbors = choose_label(examples, query, family, k)
        detail_rows.append(evaluate_prediction(query, predicted, neighbors))
    residual_rows = [row for row in detail_rows if row["kind"] == "residual_first_drift"]
    clean_rows = [row for row in detail_rows if row["kind"] == "clean_control"]
    return {
        "family": family,
        "k": k,
        "example_book_count": len(example_books),
        "query_count": len(detail_rows),
        "residual_total": len(residual_rows),
        "residual_label_hits": sum(row["label_hit"] for row in residual_rows),
        "residual_unique_branch_hits": sum(
            row["unique_branch_hit"] for row in residual_rows
        ),
        "clean_total": len(clean_rows),
        "clean_false_changes": sum(row["predicted_changes_clean"] for row in clean_rows),
        "unsupported_predictions": sum(
            1 for row in detail_rows if row["predicted_label"] is None
        ),
        "non_unique_branch_predictions": sum(
            1
            for row in detail_rows
            if row["predicted_label"] is not None and row["matching_branch_count"] != 1
        ),
        "rows": detail_rows,
    }


def configs() -> list[tuple[str, int]]:
    families = [
        "full_edit_type_only",
        "full_edit_type_len_bucket",
        "full_edit_exact_len",
        "tail3_type_only",
        "tail3_type_len_bucket",
        "tail3_exact_len",
        "tail5_type_only",
        "tail5_type_len_bucket",
        "tail5_exact_len",
    ]
    return [(family, k) for family in families for k in [1, 3, 5]]


def full_fit_scoreboard(
    rows: list[dict[str, Any]], exact_book_set: set[int]
) -> list[dict[str, Any]]:
    all_books = {int(row["book"]) for row in rows}
    return [
        score_config(rows, exact_book_set, family, k, all_books, all_books)
        for family, k in configs()
    ]


def select_score(score: dict[str, Any]) -> tuple[Any, ...]:
    return (
        score["residual_unique_branch_hits"],
        score["residual_label_hits"],
        -score["clean_false_changes"],
        -score["unsupported_predictions"],
        -score["non_unique_branch_predictions"],
        score["family"],
        -score["k"],
    )


def prequential_rows(
    rows: list[dict[str, Any]], exact_book_set: set[int]
) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        test_books = set(range(cutoff, 70))
        train_scores = [
            score_config(rows, exact_book_set, family, k, train_books, train_books)
            for family, k in configs()
        ]
        selected = max(train_scores, key=select_score)
        test = score_config(
            rows,
            exact_book_set,
            selected["family"],
            int(selected["k"]),
            train_books,
            test_books,
        )
        out.append(
            {
                "cutoff_book": cutoff,
                "selected_family": selected["family"],
                "selected_k": selected["k"],
                "train_residual_unique_branch_hits": selected[
                    "residual_unique_branch_hits"
                ],
                "train_residual_total": selected["residual_total"],
                "test_residual_unique_branch_hits": test[
                    "residual_unique_branch_hits"
                ],
                "test_residual_label_hits": test["residual_label_hits"],
                "test_residual_total": test["residual_total"],
                "test_clean_false_changes": test["clean_false_changes"],
                "test_unsupported_predictions": test["unsupported_predictions"],
                "test_non_unique_branch_predictions": test[
                    "non_unique_branch_predictions"
                ],
            }
        )
    return out


def shuffle_control(
    rows: list[dict[str, Any]],
    exact_book_set: set[int],
    best: dict[str, Any],
) -> dict[str, Any]:
    family = best["family"]
    k = int(best["k"])
    all_books = {int(row["book"]) for row in rows}
    examples = [
        row
        for row in rows
        if row["book"] in exact_book_set and row["book"] in all_books
    ]
    labels = [row["stable_label"] for row in examples]
    residual_queries = [
        row for row in rows if row["kind"] == "residual_first_drift"
    ]
    rng = random.Random(46949 + k + len(family))
    hits = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(labels)
        rng.shuffle(shuffled)
        perm_examples = [dict(row) for row in examples]
        for row, label in zip(perm_examples, shuffled):
            row["stable_label"] = label
        total = 0
        for query in residual_queries:
            predicted, neighbors = choose_label(perm_examples, query, family, k)
            total += int(evaluate_prediction(query, predicted, neighbors)["unique_branch_hit"])
        hits.append(total)
    observed = int(best["residual_unique_branch_hits"])
    return {
        "family": family,
        "k": k,
        "observed_unique_branch_hits": observed,
        "trials": RANDOM_TRIALS,
        "shuffle_min": min(hits),
        "shuffle_mean": sum(hits) / len(hits),
        "shuffle_max": max(hits),
        "shuffle_ge_observed_count": sum(1 for hit in hits if hit >= observed),
        "p_ge_observed": (sum(1 for hit in hits if hit >= observed) + 1)
        / (len(hits) + 1),
    }


def make_result() -> dict[str, Any]:
    gate48 = load_json(GATE48)
    assert_boundary("residual_site_detector_gate", gate48)
    if gate48["classification"] != "residual_site_detector_rejected":
        raise RuntimeError("gate49 expects gate48 residual-site detector rejection")

    rows, by_book = build_rows()
    exact_book_set = exact_books(by_book)
    residual_books = sorted(
        {row["book"] for row in rows if row["kind"] == "residual_first_drift"}
    )
    scoreboard = full_fit_scoreboard(rows, exact_book_set)
    best = max(scoreboard, key=select_score)
    preq = prequential_rows(rows, exact_book_set)
    control = shuffle_control(rows, exact_book_set, best)
    cells_with_residuals = sum(1 for row in preq if row["test_residual_total"] > 0)
    cells_all_residuals = sum(
        1
        for row in preq
        if row["test_residual_total"] > 0
        and row["test_residual_unique_branch_hits"] == row["test_residual_total"]
    )
    cells_clean = sum(
        1 for row in preq if row["test_clean_false_changes"] == 0
    )
    promotes = (
        best["residual_unique_branch_hits"] == best["residual_total"]
        and best["clean_false_changes"] == 0
        and best["unsupported_predictions"] == 0
        and best["non_unique_branch_predictions"] == 0
        and cells_all_residuals == cells_with_residuals
        and cells_clean == len(preq)
        and control["p_ge_observed"] <= 0.05
    )
    if promotes:
        classification = "book_skeleton_alignment_parser_promoted"
    elif best["residual_unique_branch_hits"] > 0:
        classification = "book_skeleton_alignment_weak_clue_not_promoted"
    else:
        classification = "book_skeleton_alignment_rejected"
    best_rows = [
        row
        for row in best["rows"]
        if row["kind"] == "residual_first_drift"
    ]
    return {
        "schema": "book_skeleton_alignment_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "residual_branch_continuation_audit": rel(GATE22_SCRIPT),
            "residual_site_detector_gate": rel(GATE48),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "source_free_digit_generator_emitted": False,
            "stable_projection_used_as_evaluation_label_only": True,
            "promotes_parser_rule": promotes,
            "tests_book_level_skeleton_alignment": True,
            "requires_unique_observable_branch_for_source_length_credit": True,
        },
        "summary": {
            "exact_book_count": len(exact_book_set),
            "residual_book_count": len(residual_books),
            "residual_books": residual_books,
            "decision_count": len(rows),
            "config_count": len(configs()),
            "best_family": best["family"],
            "best_k": best["k"],
            "best_residual_unique_branch_hits": best[
                "residual_unique_branch_hits"
            ],
            "best_residual_label_hits": best["residual_label_hits"],
            "best_residual_total": best["residual_total"],
            "best_clean_false_changes": best["clean_false_changes"],
            "best_unsupported_predictions": best["unsupported_predictions"],
            "best_non_unique_branch_predictions": best[
                "non_unique_branch_predictions"
            ],
            "prequential_cells": len(preq),
            "prequential_cells_with_residuals": cells_with_residuals,
            "prequential_cover_all_residual_cells": cells_all_residuals,
            "prequential_zero_clean_false_change_cells": cells_clean,
            "shuffle_p_ge_observed": control["p_ge_observed"],
            "promotes_book_skeleton_alignment_parser": promotes,
            "interpretation": (
                "Gate 49 tests whether the remaining residual branch choices "
                "are recoverable from book-level operation skeleton alignment "
                "against exact books. Credit for source/length reduction is "
                "granted only when the predicted type/length maps to a unique "
                "observable branch at the decision site."
            ),
        },
        "scoreboard": [
            {
                "family": row["family"],
                "k": row["k"],
                "residual_unique_branch_hits": row["residual_unique_branch_hits"],
                "residual_label_hits": row["residual_label_hits"],
                "residual_total": row["residual_total"],
                "clean_false_changes": row["clean_false_changes"],
                "unsupported_predictions": row["unsupported_predictions"],
                "non_unique_branch_predictions": row[
                    "non_unique_branch_predictions"
                ],
            }
            for row in sorted(scoreboard, key=select_score, reverse=True)
        ],
        "prequential_rows": preq,
        "shuffle_control": control,
        "best_residual_rows": best_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "source_length_dependency_status": "book_skeleton_alignment_tested",
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
        "# Book Skeleton Alignment Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 49 tests a book-level parser hypothesis: perhaps the",
        "remaining residual `(source,length)` decisions are selected",
        "by alignment to operation skeletons from books already parsed",
        "exactly, not by a local branch feature.",
        "",
        "Credit is stricter than type/length label matching. A residual",
        "hit counts only when the predicted type/length maps to one",
        "unique observable branch at the site, so source choice is not",
        "silently granted by the stable projection.",
        "",
        "## Summary",
        "",
        f"- Exact books used as skeleton source: `{s['exact_book_count']}`.",
        f"- Residual books: `{s['residual_book_count']}`.",
        f"- Decisions: `{s['decision_count']}`.",
        f"- Configurations tested: `{s['config_count']}`.",
        f"- Best family: `{s['best_family']}`.",
        f"- Best k: `{s['best_k']}`.",
        f"- Best residual unique-branch hits: `{s['best_residual_unique_branch_hits']}/{s['best_residual_total']}`.",
        f"- Best residual label hits: `{s['best_residual_label_hits']}/{s['best_residual_total']}`.",
        f"- Best clean false changes: `{s['best_clean_false_changes']}`.",
        f"- Unsupported predictions: `{s['best_unsupported_predictions']}`.",
        f"- Non-unique branch predictions: `{s['best_non_unique_branch_predictions']}`.",
        f"- Shuffle p(>= observed): `{s['shuffle_p_ge_observed']:.3f}`.",
        "",
        "## Scoreboard",
        "",
        "| Family | k | Residual unique branch hits | Residual label hits | Clean false changes | Unsupported | Non-unique |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["scoreboard"][:12]:
        lines.append(
            f"| `{row['family']}` | `{row['k']}` | "
            f"`{row['residual_unique_branch_hits']}/{row['residual_total']}` | "
            f"`{row['residual_label_hits']}/{row['residual_total']}` | "
            f"`{row['clean_false_changes']}` | "
            f"`{row['unsupported_predictions']}` | "
            f"`{row['non_unique_branch_predictions']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected family | k | Test residual unique hits | Test residual label hits | Test clean false changes | Unsupported | Non-unique |",
            "|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_family']}` | "
            f"`{row['selected_k']}` | "
            f"`{row['test_residual_unique_branch_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_residual_label_hits']}/{row['test_residual_total']}` | "
            f"`{row['test_clean_false_changes']}` | "
            f"`{row['test_unsupported_predictions']}` | "
            f"`{row['test_non_unique_branch_predictions']}` |"
        )
    lines.extend(
        [
            "",
            "## Residual Rows Under Best Config",
            "",
            "| Book | Op | Class | Active | Stable | Predicted | Label hit | Unique branch hit | Branch matches |",
            "|---:|---:|---|---|---|---|---:|---:|---:|",
        ]
    )
    for row in result["best_residual_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['stable_index']}` | "
            f"`{row['drift_class']}` | `{row['active_label']}` | "
            f"`{row['stable_label']}` | `{row['predicted_label']}` | "
            f"`{row['label_hit']}` | `{row['unique_branch_hit']}` | "
            f"`{row['matching_branch_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes book-skeleton alignment parser: `{s['promotes_book_skeleton_alignment_parser']}`.",
            f"- Prequential cover-all-residual cells: `{s['prequential_cover_all_residual_cells']}/{s['prequential_cells_with_residuals']}`.",
            f"- Prequential zero-clean-false-change cells: `{s['prequential_zero_clean_false_change_cells']}/{s['prequential_cells']}`.",
            f"- {s['interpretation']}",
            "- Book-level skeleton alignment does not remove the remaining source/length dependency.",
            "- The result is analysis-only and does not change the compression bound.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
