from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

SKELETON_SCRIPT = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "scripts"
    / "02_source_free_skeleton_grammar_gate.py"
)
BOUNDARY_CLOSURE = (
    ROOT
    / "analysis"
    / "generation_boundary_closure_audit_20260621"
    / "reports"
    / "test_results"
    / "01_generation_boundary_closure_audit.json"
)

OUT_STEM = "01_operation_length_markov_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
MAX_OPS = 200


State = dict[str, Any]
ContextFn = Callable[[State], str]


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


def bucket(value: int) -> str:
    if value <= 1:
        return "le1"
    if value <= 3:
        return "le3"
    if value <= 5:
        return "le5"
    if value <= 8:
        return "le8"
    if value <= 13:
        return "le13"
    if value <= 21:
        return "le21"
    if value <= 34:
        return "le34"
    if value <= 55:
        return "le55"
    if value <= 89:
        return "le89"
    return "gt89"


def reconstruct() -> dict[int, list[dict[str, Any]]]:
    module = load_module("source_free_skeleton_for_length_markov", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def rowize(by_book: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for book in sorted(by_book):
        book_length = sum(int(op["length"]) for op in by_book[book])
        previous_length = 0
        previous_type = "BOS"
        target_start = 0
        for op_index, op in enumerate(by_book[book]):
            length = int(op["length"])
            rows.append(
                {
                    "book": book,
                    "book_length": book_length,
                    "op_index": op_index,
                    "target_start": target_start,
                    "remaining": book_length - target_start,
                    "type": op["type"],
                    "previous_type": previous_type,
                    "previous_length": previous_length,
                    "length": length,
                }
            )
            previous_type = op["type"]
            previous_length = length
            target_start += length
    return rows


def context_families() -> dict[str, ContextFn]:
    return {
        "global": lambda s: "global",
        "type": lambda s: f"type={s['type']}",
        "op_index": lambda s: f"op={s['op_index']}",
        "op_index_x_type": lambda s: f"op={s['op_index']}|type={s['type']}",
        "previous_length": lambda s: f"prev_len={s['previous_length']}",
        "previous_type": lambda s: f"prev_type={s['previous_type']}",
        "previous_type_x_type": lambda s: (
            f"prev_type={s['previous_type']}|type={s['type']}"
        ),
        "previous_length_bucket_x_type": lambda s: (
            f"prev_lenb={bucket(int(s['previous_length']))}|type={s['type']}"
        ),
        "remaining_bucket_x_type": lambda s: (
            f"remb={bucket(int(s['remaining']))}|type={s['type']}"
        ),
        "book_length_bucket_x_op": lambda s: (
            f"booklenb={bucket(int(s['book_length']))}|op={s['op_index']}"
        ),
        "book_mod10_x_op_index": lambda s: (
            f"bookmod10={int(s['book']) % 10}|op={s['op_index']}"
        ),
    }


def majority_length(rows: list[dict[str, Any]]) -> int:
    counts = Counter(int(row["length"]) for row in rows)
    return min(counts, key=lambda length: (-counts[length], length))


def train_model(rows: list[dict[str, Any]], name: str, fn: ContextFn) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[fn(row)].append(row)
    return {
        "context_name": name,
        "fallback_length": majority_length(rows),
        "mapping": {key: majority_length(values) for key, values in groups.items()},
        "context_count": len(groups),
    }


def predict(model: dict[str, Any], fn: ContextFn, state: State) -> int:
    return int(model["mapping"].get(fn(state), model["fallback_length"]))


def row_score(rows: list[dict[str, Any]], model: dict[str, Any], fn: ContextFn) -> dict[str, Any]:
    exact = 0
    abs_error = 0
    for row in rows:
        p = predict(model, fn, row)
        err = int(row["length"]) - p
        exact += 1 if err == 0 else 0
        abs_error += abs(err)
    return {
        "context_name": model["context_name"],
        "context_count": model["context_count"],
        "row_count": len(rows),
        "exact_lengths": exact,
        "mean_abs_error": abs_error / len(rows) if rows else 0.0,
    }


def generate_book(
    truth_ops: list[dict[str, Any]],
    *,
    book: int,
    model: dict[str, Any],
    fn: ContextFn,
) -> dict[str, Any]:
    book_length = sum(int(op["length"]) for op in truth_ops)
    generated_lengths = []
    target_start = 0
    previous_type = "BOS"
    previous_length = 0
    for op_index in range(MAX_OPS):
        remaining = book_length - target_start
        if remaining <= 0:
            break
        granted_type = truth_ops[op_index]["type"] if op_index < len(truth_ops) else "copy"
        state = {
            "book": book,
            "book_length": book_length,
            "op_index": op_index,
            "target_start": target_start,
            "remaining": remaining,
            "type": granted_type,
            "previous_type": previous_type,
            "previous_length": previous_length,
        }
        length = max(1, predict(model, fn, state))
        if length > remaining:
            length = remaining
        generated_lengths.append(length)
        target_start += length
        previous_type = granted_type
        previous_length = length
    truth_lengths = [int(op["length"]) for op in truth_ops]
    aligned = list(zip(generated_lengths, truth_lengths))
    exact_prefix = 0
    for left, right in aligned:
        if left != right:
            break
        exact_prefix += 1
    return {
        "book": book,
        "truth_op_count": len(truth_lengths),
        "generated_op_count": len(generated_lengths),
        "truth_book_length": book_length,
        "generated_book_length": sum(generated_lengths),
        "exact_sequence": generated_lengths == truth_lengths,
        "exact_prefix_ops": exact_prefix,
        "row_hits": sum(1 for left, right in aligned if left == right),
        "generated_lengths": generated_lengths,
    }


def generation_score(
    by_book: dict[int, list[dict[str, Any]]],
    model: dict[str, Any],
    fn: ContextFn,
    books: list[int],
) -> dict[str, Any]:
    rows = [generate_book(by_book[book], book=book, model=model, fn=fn) for book in books]
    return {
        "context_name": model["context_name"],
        "book_count": len(rows),
        "exact_books": sum(1 for row in rows if row["exact_sequence"]),
        "row_hits": sum(row["row_hits"] for row in rows),
        "truth_ops": sum(row["truth_op_count"] for row in rows),
        "mean_exact_prefix_ops": (
            sum(row["exact_prefix_ops"] for row in rows) / len(rows) if rows else 0.0
        ),
        "rows": rows,
    }


def prequential(
    by_book: dict[int, list[dict[str, Any]]],
    rows: list[dict[str, Any]],
    contexts: dict[str, ContextFn],
) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train_rows = [row for row in rows if int(row["book"]) < cutoff]
        test_books = [book for book in sorted(by_book) if book >= cutoff]
        trained = []
        for name, fn in contexts.items():
            model = train_model(train_rows, name, fn)
            score = generation_score(by_book, model, fn, [book for book in sorted(by_book) if book < cutoff])
            trained.append((name, fn, model, score))
        selected_name, selected_fn, selected_model, selected_train = max(
            trained,
            key=lambda item: (
                item[3]["exact_books"],
                item[3]["row_hits"],
                -item[2]["context_count"],
                item[0],
            ),
        )
        test_score = generation_score(by_book, selected_model, selected_fn, test_books)
        oracle = max(
            [generation_score(by_book, model, fn, test_books) for _name, fn, model, _score in trained],
            key=lambda score: (score["exact_books"], score["row_hits"], score["context_name"]),
        )
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_context": selected_name,
                "train_exact_books": selected_train["exact_books"],
                "train_book_count": selected_train["book_count"],
                "test_exact_books": test_score["exact_books"],
                "test_book_count": test_score["book_count"],
                "test_row_hits": test_score["row_hits"],
                "test_truth_ops": test_score["truth_ops"],
                "oracle_context": oracle["context_name"],
                "oracle_test_exact_books": oracle["exact_books"],
                "oracle_test_row_hits": oracle["row_hits"],
                "selected_matches_oracle": (
                    test_score["exact_books"] == oracle["exact_books"]
                    and test_score["row_hits"] == oracle["row_hits"]
                ),
            }
        )
    return result


def make_result() -> dict[str, Any]:
    boundary = load_json(BOUNDARY_CLOSURE)
    assert_boundary("generation_boundary_closure", boundary)
    by_book = reconstruct()
    rows = rowize(by_book)
    contexts = context_families()
    full_scores = []
    for name, fn in contexts.items():
        model = train_model(rows, name, fn)
        rscore = row_score(rows, model, fn)
        gscore = generation_score(by_book, model, fn, sorted(by_book))
        full_scores.append(
            {
                **rscore,
                "exact_books": gscore["exact_books"],
                "book_count": gscore["book_count"],
                "generation_row_hits": gscore["row_hits"],
                "truth_ops": gscore["truth_ops"],
                "mean_exact_prefix_ops": gscore["mean_exact_prefix_ops"],
            }
        )
    full_scores.sort(
        key=lambda row: (
            row["exact_books"],
            row["generation_row_hits"],
            row["exact_lengths"],
            -row["context_count"],
            row["context_name"],
        ),
        reverse=True,
    )
    preq = prequential(by_book, rows, contexts)
    best = full_scores[0]
    promoted = (
        best["exact_books"] == best["book_count"]
        and all(row["test_exact_books"] == row["test_book_count"] for row in preq)
    )
    classification = (
        "operation_length_markov_generator_promoted"
        if promoted
        else "operation_length_markov_generator_rejected"
    )
    return {
        "schema": "operation_length_markov_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "generation_boundary_closure": rel(BOUNDARY_CLOSURE),
        },
        "scope": {
            "analysis_only": True,
            "book_lengths_granted": True,
            "operation_types_granted_for_generation": True,
            "tests_markov_context_length_generation": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_count": len(by_book),
            "operation_count": len(rows),
            "context_family_count": len(contexts),
            "best_context": best["context_name"],
            "best_context_count": best["context_count"],
            "best_full_exact_books": best["exact_books"],
            "best_full_generation_row_hits": best["generation_row_hits"],
            "best_full_truth_ops": best["truth_ops"],
            "best_rowwise_exact_lengths": best["exact_lengths"],
            "best_mean_exact_prefix_ops": best["mean_exact_prefix_ops"],
            "prequential_cells": len(preq),
            "prequential_cover_all_cells": sum(
                1 for row in preq if row["test_exact_books"] == row["test_book_count"]
            ),
            "prequential_any_exact_book_cells": sum(
                1 for row in preq if row["test_exact_books"] > 0
            ),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "promotes_operation_length_generator": promoted,
            "interpretation": (
                "Even with book lengths and operation types granted, simple "
                "Markov/context grammars do not generate the operation-length "
                "sequence. The length atlas remains the skeleton blocker."
            ),
        },
        "full_fit_scoreboard": full_scores,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "operation_length_status": "atlas_retained_after_markov_gate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Operation Length Markov Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the operation-length atlas can be generated by simple",
        "Markov/context grammars after granting book lengths and operation types.",
        "",
        "## Summary",
        "",
        f"- Books/operations: `{s['book_count']}` / `{s['operation_count']}`.",
        f"- Context families: `{s['context_family_count']}`.",
        f"- Best context: `{s['best_context']}`.",
        f"- Best full-fit exact books: `{s['best_full_exact_books']}/{s['book_count']}`.",
        f"- Best full-fit generated row hits: `{s['best_full_generation_row_hits']}/{s['best_full_truth_ops']}`.",
        f"- Best rowwise exact lengths: `{s['best_rowwise_exact_lengths']}/{s['operation_count']}`.",
        f"- Best mean exact prefix ops: `{s['best_mean_exact_prefix_ops']:.3f}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout any-exact-book cells: `{s['prequential_any_exact_book_cells']}/{s['prequential_cells']}`.",
        "",
        "## Full-Fit Scoreboard",
        "",
        "| Context | Exact books | Generated row hits | Rowwise hits | Contexts |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result["full_fit_scoreboard"]:
        lines.append(
            f"| `{row['context_name']}` | `{row['exact_books']}/{row['book_count']}` | "
            f"`{row['generation_row_hits']}/{row['truth_ops']}` | "
            f"`{row['exact_lengths']}/{row['row_count']}` | `{row['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Context | Test exact books | Test row hits | Oracle context |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_context']}` | "
            f"`{row['test_exact_books']}/{row['test_book_count']}` | "
            f"`{row['test_row_hits']}/{row['test_truth_ops']}` | "
            f"`{row['oracle_context']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes operation-length generator: `{s['promotes_operation_length_generator']}`.",
            f"- {s['interpretation']}",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
