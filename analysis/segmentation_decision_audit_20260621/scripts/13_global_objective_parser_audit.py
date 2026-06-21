from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
GATE111_SCRIPT = PREQ / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TRACE_SCRIPT = HERE / "scripts" / "01_segmentation_decision_trace.py"
RESIDUAL_CONTEXT = TEST_RESULTS / "12_integrated_parser_residual_context_audit.json"

OUT_STEM = "13_global_objective_parser_audit"
SEED_BOOKS = list(range(10))
MIN_COPY_LEN = 5
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]


OBJECTIVES = [
    "min_ops",
    "min_literal_digits",
    "min_literal_runs",
    "min_copies",
    "max_copy_digits",
    "balanced_ops_literals",
]


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


def normalize_ops(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": row["type"],
            "target_start": int(row["target_start"]),
            "length": int(row["length"]),
            "source": row["source"],
        }
        for row in rows
    ]


def copy_candidates(trace_module, emitted_base: str, target: str, pos: int) -> list[dict[str, int]]:
    emitted = emitted_base + target[:pos]
    rows = trace_module.candidate_sources_with_max(emitted, target, pos)
    by_length: dict[int, int] = {}
    for row in rows:
        for length in range(MIN_COPY_LEN, row["max_length"] + 1):
            source = by_length.get(length)
            if source is None or row["source"] < source:
                by_length[length] = row["source"]
    return [
        {"type": "copy", "target_start": pos, "length": length, "source": source}
        for length, source in sorted(by_length.items())
    ]


def edge_delta(op: dict[str, Any], objective: str) -> tuple[int, ...]:
    is_lit = op["type"] == "literal"
    is_copy = op["type"] == "copy"
    length = int(op["length"])
    if objective == "min_ops":
        return (1, length if is_lit else 0, -length if is_copy else 0)
    if objective == "min_literal_digits":
        return (length if is_lit else 0, 1, -length if is_copy else 0)
    if objective == "min_literal_runs":
        return (1 if is_lit else 0, length if is_lit else 0, 1)
    if objective == "min_copies":
        return (1 if is_copy else 0, length if is_lit else 0, 1)
    if objective == "max_copy_digits":
        return (-length if is_copy else 0, 1, length if is_lit else 0)
    if objective == "balanced_ops_literals":
        return (1 + (length if is_lit else 0), 1, -length if is_copy else 0)
    raise ValueError(objective)


def add_cost(left: tuple[int, ...], right: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(a + b for a, b in zip(left, right))


def better_path(candidate: tuple[int, ...], incumbent: tuple[int, ...] | None) -> bool:
    return incumbent is None or candidate < incumbent


def dp_parse_book(
    trace_module,
    emitted_base: str,
    target: str,
    objective: str,
) -> list[dict[str, Any]]:
    n = len(target)
    width = len(edge_delta({"type": "literal", "length": 1}, objective))
    best: list[tuple[int, ...] | None] = [None] * (n + 1)
    prev: list[tuple[int, dict[str, Any]] | None] = [None] * (n + 1)
    best[0] = tuple(0 for _ in range(width))
    for pos in range(n):
        if best[pos] is None:
            continue
        # Literal edges may run to any later position. This is intentionally a
        # broad path-state control: if a simple objective can derive segmentation,
        # it should be allowed to choose non-local literal spans.
        for end in range(pos + 1, n + 1):
            op = {
                "type": "literal",
                "target_start": pos,
                "length": end - pos,
                "source": None,
            }
            cand = add_cost(best[pos], edge_delta(op, objective))
            if better_path(cand, best[end]):
                best[end] = cand
                prev[end] = (pos, op)
        for op in copy_candidates(trace_module, emitted_base, target, pos):
            end = pos + int(op["length"])
            cand = add_cost(best[pos], edge_delta(op, objective))
            if better_path(cand, best[end]):
                best[end] = cand
                prev[end] = (pos, op)
    if best[n] is None:
        raise RuntimeError("no parser path")
    ops: list[dict[str, Any]] = []
    cursor = n
    while cursor > 0:
        item = prev[cursor]
        if item is None:
            raise RuntimeError({"type": "missing_prev", "cursor": cursor})
        pos, op = item
        ops.append(op)
        cursor = pos
    return list(reversed(ops))


def first_diff(predicted: list[dict[str, Any]], stable: list[dict[str, Any]]) -> dict[str, Any] | None:
    if predicted == stable:
        return None
    for index, (left, right) in enumerate(zip(predicted, stable)):
        if left != right:
            return {"index": index, "predicted": left, "stable_projection": right}
    index = min(len(predicted), len(stable))
    return {
        "index": index,
        "predicted": None if index >= len(predicted) else predicted[index],
        "stable_projection": None if index >= len(stable) else stable[index],
    }


def score_objective(
    trace_module,
    books: dict[int, str],
    stable_by_book: dict[int, list[dict[str, Any]]],
    objective: str,
) -> dict[str, Any]:
    emitted_base = "".join(books[book] for book in SEED_BOOKS)
    exact_books: list[int] = []
    mismatch_rows: list[dict[str, Any]] = []
    predicted_ops = predicted_copies = predicted_literal_runs = predicted_literal_digits = 0
    stable_ops = stable_copies = stable_literal_runs = stable_literal_digits = 0
    for book in range(10, 70):
        target = books[book]
        predicted = dp_parse_book(trace_module, emitted_base, target, objective)
        stable = normalize_ops(stable_by_book.get(book, []))
        predicted_ops += len(predicted)
        predicted_copies += sum(1 for row in predicted if row["type"] == "copy")
        predicted_literal_runs += sum(1 for row in predicted if row["type"] == "literal")
        predicted_literal_digits += sum(
            int(row["length"]) for row in predicted if row["type"] == "literal"
        )
        stable_ops += len(stable)
        stable_copies += sum(1 for row in stable if row["type"] == "copy")
        stable_literal_runs += sum(1 for row in stable if row["type"] == "literal")
        stable_literal_digits += sum(
            int(row["length"]) for row in stable if row["type"] == "literal"
        )
        diff = first_diff(predicted, stable)
        if diff is None:
            exact_books.append(book)
        else:
            mismatch_rows.append(
                {
                    "book": book,
                    "predicted_op_count": len(predicted),
                    "stable_projection_op_count": len(stable),
                    "first_diff": diff,
                }
            )
        emitted_base += target
    return {
        "objective": objective,
        "tested_books": 60,
        "exact_book_count": len(exact_books),
        "mismatch_book_count": len(mismatch_rows),
        "exact_books": exact_books,
        "mismatch_books": [row["book"] for row in mismatch_rows],
        "predicted_operation_count": predicted_ops,
        "stable_projection_operation_count": stable_ops,
        "predicted_copy_count": predicted_copies,
        "stable_copy_count": stable_copies,
        "predicted_literal_gap_count": predicted_literal_runs,
        "stable_literal_gap_count": stable_literal_runs,
        "predicted_literal_digit_count": predicted_literal_digits,
        "stable_literal_digit_count": stable_literal_digits,
        "sample_mismatches": mismatch_rows[:12],
    }


def prequential_selection(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        test_books = set(range(cutoff, 70))
        scored = []
        for score in scores:
            exact = set(score["exact_books"])
            train_hits = len(exact & train_books)
            test_hits = len(exact & test_books)
            scored.append(
                {
                    "objective": score["objective"],
                    "train_hits": train_hits,
                    "train_total": len(train_books),
                    "test_hits": test_hits,
                    "test_total": len(test_books),
                    "exact_book_count": score["exact_book_count"],
                }
            )
        selected = max(
            scored,
            key=lambda row: (
                row["train_hits"],
                row["test_hits"],
                row["exact_book_count"],
                row["objective"],
            ),
        )
        oracle = max(scored, key=lambda row: (row["test_hits"], row["train_hits"]))
        rows.append(
            {
                "cutoff_book": cutoff,
                "selected_objective": selected["objective"],
                "train_hits": selected["train_hits"],
                "train_total": selected["train_total"],
                "test_hits": selected["test_hits"],
                "test_total": selected["test_total"],
                "oracle_objective": oracle["objective"],
                "oracle_test_hits": oracle["test_hits"],
                "selected_matches_oracle": selected["test_hits"] == oracle["test_hits"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    residual = load_json(RESIDUAL_CONTEXT)
    assert_boundary("integrated_parser_residual_context_audit", residual)
    if residual["summary"]["exact_books"] != 48:
        raise RuntimeError("gate12 exact coverage changed")

    trace_module = load_module("segmentation_trace_for_gate13", TRACE_SCRIPT)
    gate111 = load_module("gate111_for_segmentation_gate13", GATE111_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stable_ops = trace_module.projected_ops_from_copy_rows(gate111.make_copy_rows(), books)
    stable_by_book: dict[int, list[dict[str, Any]]] = {}
    for op in stable_ops:
        stable_by_book.setdefault(int(op["book"]), []).append(op)
    for rows in stable_by_book.values():
        rows.sort(key=lambda row: int(row["target_start"]))

    scores = [score_objective(trace_module, books, stable_by_book, obj) for obj in OBJECTIVES]
    best = max(
        scores,
        key=lambda row: (
            row["exact_book_count"],
            -abs(row["predicted_operation_count"] - row["stable_projection_operation_count"]),
            -abs(row["predicted_literal_digit_count"] - row["stable_literal_digit_count"]),
            row["objective"],
        ),
    )
    baseline_exact = int(residual["summary"]["exact_books"])
    preq = prequential_selection(scores)
    preq_stable = all(row["selected_matches_oracle"] for row in preq)
    improvement = best["exact_book_count"] - baseline_exact
    promotes_global_objective = best["exact_book_count"] == 60 and preq_stable
    if promotes_global_objective:
        classification = "global_objective_parser_promoted_target_text_parser"
    elif improvement > 0 and preq_stable:
        classification = "global_objective_parser_prequential_partial_not_promoted"
    elif improvement > 0:
        classification = "global_objective_parser_posthoc_partial_not_promoted"
    else:
        classification = "global_objective_parser_rejected"

    return {
        "schema": "global_objective_parser_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "integrated_parser_residual_context_audit": rel(RESIDUAL_CONTEXT),
            "books_digits": rel(BOOKS_DIGITS),
        },
        "scope": {
            "analysis_only": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "target_text_required": True,
            "declared_literal_windows_granted": False,
            "declared_copy_starts_granted": False,
            "source_free_digit_generator_emitted": False,
        },
        "summary": {
            "objective_count": len(scores),
            "baseline_window5_exact_books": baseline_exact,
            "best_objective": best["objective"],
            "best_exact_books": best["exact_book_count"],
            "exact_improvement_vs_window5": improvement,
            "prequential_cells": len(preq),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "prequential_stable": preq_stable,
            "promotes_global_objective_parser": promotes_global_objective,
            "interpretation": (
                "Book-local dynamic programming tests whether a simple global "
                "objective over operations, literal mass, and copy mass can replace "
                "the greedy local peak parser. It remains target-text-aware and "
                "does not emit source-free digits."
            ),
        },
        "objective_scoreboard": sorted(
            [
                {
                    "objective": row["objective"],
                    "exact_book_count": row["exact_book_count"],
                    "mismatch_book_count": row["mismatch_book_count"],
                    "predicted_operation_count": row["predicted_operation_count"],
                    "predicted_literal_gap_count": row["predicted_literal_gap_count"],
                    "predicted_literal_digit_count": row["predicted_literal_digit_count"],
                    "predicted_copy_count": row["predicted_copy_count"],
                    "sample_mismatches": row["sample_mismatches"],
                }
                for row in scores
            ],
            key=lambda row: (-row["exact_book_count"], row["objective"]),
        ),
        "best_mismatches": best["sample_mismatches"],
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "global_objective_parser_status": "not_promoted",
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
        "# Global Objective Parser Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Local threshold and context predicates did not close the residual drift.",
        "This gate tests a richer path/state hypothesis: parse each book with",
        "dynamic programming under simple global objectives, without granting",
        "declared operation starts.",
        "",
        "## Scoreboard",
        "",
        f"- Objectives tested: `{s['objective_count']}`.",
        f"- Window5 baseline exact books: `{s['baseline_window5_exact_books']}/60`.",
        f"- Best objective: `{s['best_objective']}`.",
        f"- Best exact books: `{s['best_exact_books']}/60`.",
        f"- Exact-book improvement vs window5: `{s['exact_improvement_vs_window5']}`.",
        "",
        "| Objective | Exact books | Ops | Literal gaps | Literal digits | Copies |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["objective_scoreboard"]:
        lines.append(
            f"| `{row['objective']}` | `{row['exact_book_count']}/60` | "
            f"`{row['predicted_operation_count']}` | "
            f"`{row['predicted_literal_gap_count']}` | "
            f"`{row['predicted_literal_digit_count']}` | "
            f"`{row['predicted_copy_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Prequential Objective Selection",
            "",
            "| Cutoff | Selected | Train hits | Test hits | Oracle | Oracle test hits |",
            "|---:|---|---:|---:|---|---:|",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_objective']}` | "
            f"`{row['train_hits']}/{row['train_total']}` | "
            f"`{row['test_hits']}/{row['test_total']}` | "
            f"`{row['oracle_objective']}` | `{row['oracle_test_hits']}/{row['test_total']}` |"
        )
    lines.extend(
        [
            "",
            "## Mismatch Sample",
            "",
            "| Book | Predicted ops | Stable ops | First diff |",
            "|---:|---:|---:|---|",
        ]
    )
    for row in result["best_mismatches"]:
        lines.append(
            f"| `{row['book']}` | `{row['predicted_op_count']}` | "
            f"`{row['stable_projection_op_count']}` | "
            f"`{json.dumps(row['first_diff'], sort_keys=True)}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes global objective parser: `{s['promotes_global_objective_parser']}`.",
            f"- {s['interpretation']}",
            "- The result remains target-text-aware and analysis-only.",
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
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
