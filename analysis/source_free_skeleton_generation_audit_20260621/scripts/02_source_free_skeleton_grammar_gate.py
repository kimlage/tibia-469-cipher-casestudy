from __future__ import annotations

import hashlib
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

PREQ = ROOT / "analysis" / "prequential_and_row0_origin_audit_20260621"
PREQ_RESULTS = PREQ / "reports" / "test_results"
GATE91_SCRIPT = PREQ / "scripts" / "91_full_source_exposure_audit.py"
GATE98 = PREQ_RESULTS / "98_full_source_exact_skeleton_invariance.json"
GATE99 = PREQ_RESULTS / "99_exact_skeleton_dependency_ledger.json"
HARD_LEDGER = TEST_RESULTS / "01_hard_boundary_ledger.json"

OUT_STEM = "02_source_free_skeleton_grammar_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
CANONICAL_CUTOFF = 10
CANONICAL_POLICY = "earliest_source"
MAX_GENERATED_OPS_PER_BOOK = 200


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


def stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


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


def source_free_skeleton(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    skeleton = []
    for op in ops:
        skeleton.append(
            {
                "type": op["type"],
                "target_start": int(op["target_start"]),
                "length": int(op["length"]),
                "forced": bool(op["forced"]),
            }
        )
    return skeleton


def reconstruct_canonical_skeleton() -> dict[int, list[dict[str, Any]]]:
    gate91 = load_module("gate91_for_source_free_skeleton_grammar", GATE91_SCRIPT)
    captured_ops: dict[str, list[dict[str, Any]]] = {}
    original_compact_signature = gate91.compact_signature

    def capture_compact_signature(ops: list[dict[str, Any]]) -> str:
        signature = original_compact_signature(ops)
        previous = captured_ops.get(signature)
        if previous is not None and previous != ops:
            raise RuntimeError({"type": "signature_collision", "signature": signature})
        captured_ops[signature] = json.loads(json.dumps(ops))
        return signature

    gate91.compact_signature = capture_compact_signature
    gate86 = gate91.load_module("gate86_for_skeleton_grammar", gate91.GATE86_SCRIPT)
    gate82 = gate86.load_module("gate82_for_skeleton_grammar", gate86.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_skeleton_grammar", gate82.GATE77_SCRIPT)
    rows = gate91.run_cutoff(
        CANONICAL_CUTOFF,
        gate77,
        gate82,
        policy=CANONICAL_POLICY,
    )
    result: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        result[int(row["book"])] = source_free_skeleton(captured_ops[row["signature"]])
    return result


def rowize_skeleton(by_book: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for book in sorted(by_book):
        book_length = sum(int(op["length"]) for op in by_book[book])
        previous_type = "BOS"
        previous_length = 0
        for op_index, op in enumerate(by_book[book]):
            target_start = int(op["target_start"])
            remaining = book_length - target_start
            rows.append(
                {
                    "book": book,
                    "book_length": book_length,
                    "op_index": op_index,
                    "target_start": target_start,
                    "remaining": remaining,
                    "previous_type": previous_type,
                    "previous_length": previous_length,
                    "label": f"{op['type']}:{int(op['length'])}",
                    "type": op["type"],
                    "length": int(op["length"]),
                    "forced": bool(op["forced"]),
                }
            )
            previous_type = op["type"]
            previous_length = int(op["length"])
    return rows


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
    return "gt55"


def phase(value: int, modulus: int) -> str:
    return str(value % modulus)


State = dict[str, Any]
ContextFn = Callable[[State], str]


def context_families() -> dict[str, ContextFn]:
    return {
        "global": lambda s: "global",
        "op_index": lambda s: f"op={s['op_index']}",
        "op_index_bucket": lambda s: f"opb={bucket(int(s['op_index']) + 1)}",
        "previous_type": lambda s: f"prev_type={s['previous_type']}",
        "previous_label": lambda s: (
            f"prev={s['previous_type']}:{int(s['previous_length'])}"
        ),
        "remaining_bucket": lambda s: f"rem={bucket(int(s['remaining']))}",
        "book_length_bucket": lambda s: f"booklen={bucket(int(s['book_length']))}",
        "target_phase_10": lambda s: f"phase10={phase(int(s['target_start']), 10)}",
        "target_phase_16": lambda s: f"phase16={phase(int(s['target_start']), 16)}",
        "op_x_remaining_bucket": lambda s: (
            f"op={s['op_index']}|rem={bucket(int(s['remaining']))}"
        ),
        "prev_label_x_remaining_bucket": lambda s: (
            f"prev={s['previous_type']}:{int(s['previous_length'])}|"
            f"rem={bucket(int(s['remaining']))}"
        ),
        "previous_type_x_phase10": lambda s: (
            f"prev_type={s['previous_type']}|phase10={phase(int(s['target_start']), 10)}"
        ),
        "book_mod10_x_op_index": lambda s: (
            f"bookmod10={int(s['book']) % 10}|op={s['op_index']}"
        ),
    }


def majority_label(rows: list[dict[str, Any]]) -> str:
    counts = Counter(row["label"] for row in rows)
    return min(counts, key=lambda label: (-counts[label], label))


def train_grammar(
    rows: list[dict[str, Any]],
    context_name: str,
    context_fn: ContextFn,
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[context_fn(row)].append(row)
    mapping = {context: majority_label(values) for context, values in grouped.items()}
    return {
        "context_name": context_name,
        "fallback_label": majority_label(rows),
        "mapping": mapping,
        "context_count": len(mapping),
    }


def parse_label(label: str) -> tuple[str, int]:
    op_type, length_text = label.split(":", 1)
    return op_type, int(length_text)


def predict_label(
    grammar: dict[str, Any],
    context_fn: ContextFn,
    state: State,
) -> str:
    return grammar["mapping"].get(context_fn(state), grammar["fallback_label"])


def generate_book(
    grammar: dict[str, Any],
    context_fn: ContextFn,
    *,
    book: int,
    book_length: int,
) -> list[dict[str, Any]]:
    generated = []
    target_start = 0
    previous_type = "BOS"
    previous_length = 0
    for op_index in range(MAX_GENERATED_OPS_PER_BOOK):
        remaining = book_length - target_start
        if remaining <= 0:
            break
        state = {
            "book": book,
            "book_length": book_length,
            "op_index": op_index,
            "target_start": target_start,
            "remaining": remaining,
            "previous_type": previous_type,
            "previous_length": previous_length,
        }
        label = predict_label(grammar, context_fn, state)
        op_type, length = parse_label(label)
        if length <= 0 or length > remaining:
            generated.append(
                {
                    "type": "invalid",
                    "target_start": target_start,
                    "length": length,
                    "label": label,
                }
            )
            break
        forced = remaining < 5 and op_type == "literal"
        generated.append(
            {
                "type": op_type,
                "target_start": target_start,
                "length": length,
                "forced": forced,
            }
        )
        target_start += length
        previous_type = op_type
        previous_length = length
    return generated


def skeleton_signature(ops: list[dict[str, Any]]) -> str:
    return stable_hash(
        [
            {
                "type": op["type"],
                "target_start": int(op["target_start"]),
                "length": int(op["length"]),
            }
            for op in ops
        ]
    )


def evaluate_grammar(
    by_book: dict[int, list[dict[str, Any]]],
    grammar: dict[str, Any],
    context_fn: ContextFn,
    books: list[int],
) -> dict[str, Any]:
    book_rows = []
    op_hits = 0
    op_total = 0
    generated_op_total = 0
    for book in books:
        truth = by_book[book]
        book_length = sum(int(op["length"]) for op in truth)
        generated = generate_book(
            grammar,
            context_fn,
            book=book,
            book_length=book_length,
        )
        truth_pairs = [
            (op["type"], int(op["target_start"]), int(op["length"])) for op in truth
        ]
        generated_pairs = [
            (op["type"], int(op["target_start"]), int(op["length"]))
            for op in generated
        ]
        for index, expected in enumerate(truth_pairs):
            if index < len(generated_pairs) and generated_pairs[index] == expected:
                op_hits += 1
        op_total += len(truth_pairs)
        generated_op_total += len(generated_pairs)
        exact = truth_pairs == generated_pairs
        book_rows.append(
            {
                "book": book,
                "book_length": book_length,
                "exact": exact,
                "truth_ops": len(truth_pairs),
                "generated_ops": len(generated_pairs),
                "op_hits": sum(
                    1
                    for index, expected in enumerate(truth_pairs)
                    if index < len(generated_pairs)
                    and generated_pairs[index] == expected
                ),
                "truth_signature": skeleton_signature(truth),
                "generated_signature": skeleton_signature(generated),
            }
        )
    return {
        "context_name": grammar["context_name"],
        "context_count": grammar["context_count"],
        "book_exact_count": sum(1 for row in book_rows if row["exact"]),
        "book_total": len(book_rows),
        "op_hits": op_hits,
        "op_total": op_total,
        "generated_op_total": generated_op_total,
        "book_rows": book_rows,
    }


def score_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["book_exact_count"],
        row["op_hits"],
        -abs(row["generated_op_total"] - row["op_total"]),
        -row["context_count"],
        row["context_name"],
    )


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return math.inf
    return math.log2(math.comb(n, k))


def price_score(row: dict[str, Any], label_count: int, family_count: int) -> dict[str, Any]:
    misses = row["op_total"] - row["op_hits"]
    grammar_bits = math.log2(family_count) + row["context_count"] * math.log2(label_count)
    correction_bits = log2_comb(row["op_total"], misses) + misses * math.log2(label_count)
    total = grammar_bits + correction_bits
    return {
        "grammar_bits": grammar_bits,
        "correction_bits": correction_bits,
        "misses": misses,
        "total_bits_with_corrections": total,
    }


def prequential_rows(
    by_book: dict[int, list[dict[str, Any]]],
    rows: list[dict[str, Any]],
    contexts: dict[str, ContextFn],
) -> list[dict[str, Any]]:
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = [book for book in sorted(by_book) if book < cutoff]
        test_books = [book for book in sorted(by_book) if book >= cutoff]
        train_rows = [row for row in rows if int(row["book"]) < cutoff]
        trained = []
        for name, fn in contexts.items():
            grammar = train_grammar(train_rows, name, fn)
            train_score = evaluate_grammar(by_book, grammar, fn, train_books)
            trained.append((name, fn, grammar, train_score))
        selected_name, selected_fn, selected_grammar, selected_train_score = max(
            trained, key=lambda item: score_key(item[3])
        )
        test_score = evaluate_grammar(by_book, selected_grammar, selected_fn, test_books)
        oracle_scores = [
            evaluate_grammar(by_book, grammar, fn, test_books)
            for _name, fn, grammar, _train_score in trained
        ]
        oracle = max(oracle_scores, key=score_key)
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_context": selected_name,
                "train_exact_books": selected_train_score["book_exact_count"],
                "train_total_books": selected_train_score["book_total"],
                "train_op_hits": selected_train_score["op_hits"],
                "train_op_total": selected_train_score["op_total"],
                "test_exact_books": test_score["book_exact_count"],
                "test_total_books": test_score["book_total"],
                "test_op_hits": test_score["op_hits"],
                "test_op_total": test_score["op_total"],
                "oracle_context": oracle["context_name"],
                "oracle_test_exact_books": oracle["book_exact_count"],
                "oracle_test_op_hits": oracle["op_hits"],
                "selected_matches_oracle": (
                    test_score["book_exact_count"] == oracle["book_exact_count"]
                    and test_score["op_hits"] == oracle["op_hits"]
                ),
            }
        )
    return result


def make_result() -> dict[str, Any]:
    gate98 = load_json(GATE98)
    gate99 = load_json(GATE99)
    hard = load_json(HARD_LEDGER)
    assert_boundary("full_source_exact_skeleton_invariance", gate98)
    assert_boundary("exact_skeleton_dependency_ledger", gate99)
    assert_boundary("hard_boundary_ledger", hard)
    by_book = reconstruct_canonical_skeleton()
    rows = rowize_skeleton(by_book)
    expected = gate99["summary"]
    if len(rows) != int(expected["skeleton_atlas_records"]):
        raise RuntimeError({"expected_ops": expected["skeleton_atlas_records"], "got": len(rows)})
    if sum(1 for row in rows if row["type"] == "copy") != int(expected["copy_items"]):
        raise RuntimeError("copy count mismatch against gate99")
    if sum(1 for row in rows if row["type"] == "literal") != int(expected["literal_runs"]):
        raise RuntimeError("literal run count mismatch against gate99")
    if sum(int(row["length"]) for row in rows if row["type"] == "literal") != int(
        expected["literal_digits"]
    ):
        raise RuntimeError("literal digit count mismatch against gate99")

    contexts = context_families()
    books = sorted(by_book)
    label_count = len({row["label"] for row in rows})
    full_scores = []
    for name, fn in contexts.items():
        grammar = train_grammar(rows, name, fn)
        score = evaluate_grammar(by_book, grammar, fn, books)
        score.update(price_score(score, label_count, len(contexts)))
        full_scores.append(score)
    full_scores.sort(key=score_key, reverse=True)
    best = full_scores[0]
    preq = prequential_rows(by_book, rows, contexts)
    atlas_bits = int(expected["skeleton_atlas_records"]) * math.log2(label_count)
    promotes = (
        best["book_exact_count"] == best["book_total"]
        and all(row["test_exact_books"] == row["test_total_books"] for row in preq)
        and best["total_bits_with_corrections"] < atlas_bits
    )
    weak = best["book_exact_count"] >= 10 or best["op_hits"] > int(0.5 * best["op_total"])
    classification = (
        "source_free_skeleton_grammar_promoted"
        if promotes
        else "source_free_skeleton_grammar_weak_not_promoted"
        if weak
        else "source_free_skeleton_grammar_rejected"
    )
    return {
        "schema": "source_free_skeleton_grammar_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "hard_boundary_ledger": rel(HARD_LEDGER),
            "exact_skeleton_invariance": rel(GATE98),
            "exact_skeleton_dependency_ledger": rel(GATE99),
            "canonical_reconstruction_script": rel(GATE91_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "tests_skeleton_generation_not_source_choice": True,
            "source_free_with_book_lengths_granted": True,
            "target_text_not_used_for_generation": True,
            "copy_sources_not_predicted": True,
            "literal_payload_not_predicted": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_count": len(books),
            "op_count": len(rows),
            "label_count": label_count,
            "context_family_count": len(contexts),
            "atlas_bits_label_only_lower_bound": atlas_bits,
            "best_context": best["context_name"],
            "best_context_count": best["context_count"],
            "best_exact_books": best["book_exact_count"],
            "best_total_books": best["book_total"],
            "best_op_hits": best["op_hits"],
            "best_op_total": best["op_total"],
            "best_total_bits_with_corrections": best["total_bits_with_corrections"],
            "best_net_vs_atlas_label_bits": best["total_bits_with_corrections"] - atlas_bits,
            "prequential_cells": len(preq),
            "prequential_cover_all_test_books_cells": sum(
                1 for row in preq if row["test_exact_books"] == row["test_total_books"]
            ),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "promotes_skeleton_grammar": promotes,
            "weak_skeleton_grammar_clue": weak,
            "interpretation": (
                "The tested source-free grammars can recover pieces of the "
                "operation skeleton, but they do not derive the 261-op atlas "
                "as a generator under prefix/holdout or paid corrections."
            ),
        },
        "full_fit_scoreboard": [
            {key: value for key, value in row.items() if key != "book_rows"}
            for row in full_scores
        ],
        "prequential_rows": preq,
        "best_book_rows": best["book_rows"],
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "skeleton_status": "atlas_retained_not_generated",
            "source_dependency_status": "not_tested_secondary",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Source-Free Skeleton Grammar Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the exact `261`-operation skeleton can be generated by",
        "source-free grammar rules over book length, operation index, remaining",
        "length, phase, and previous operation state. Copy source and literal",
        "payload are deliberately out of scope.",
        "",
        "## Summary",
        "",
        f"- Books: `{s['book_count']}`.",
        f"- Operations: `{s['op_count']}`.",
        f"- Distinct op labels: `{s['label_count']}`.",
        f"- Context families: `{s['context_family_count']}`.",
        f"- Atlas label-only lower bound: `{s['atlas_bits_label_only_lower_bound']:.3f}` bits.",
        f"- Best context: `{s['best_context']}`.",
        f"- Best exact books: `{s['best_exact_books']}/{s['best_total_books']}`.",
        f"- Best op hits: `{s['best_op_hits']}/{s['best_op_total']}`.",
        f"- Best net vs atlas label bits: `{s['best_net_vs_atlas_label_bits']:.3f}` bits.",
        f"- Prefix/holdout cover-all-test-books cells: `{s['prequential_cover_all_test_books_cells']}/{s['prequential_cells']}`.",
        "",
        "## Full-Fit Scoreboard",
        "",
        "| Context | Exact books | Op hits | Contexts | Net vs atlas |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result["full_fit_scoreboard"]:
        net = row["total_bits_with_corrections"] - s["atlas_bits_label_only_lower_bound"]
        lines.append(
            f"| `{row['context_name']}` | `{row['book_exact_count']}/{row['book_total']}` | "
            f"`{row['op_hits']}/{row['op_total']}` | `{row['context_count']}` | "
            f"`{net:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Context | Test exact books | Test op hits | Oracle context |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_context']}` | "
            f"`{row['test_exact_books']}/{row['test_total_books']}` | "
            f"`{row['test_op_hits']}/{row['test_op_total']}` | "
            f"`{row['oracle_context']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes skeleton grammar: `{s['promotes_skeleton_grammar']}`.",
            f"- Weak skeleton grammar clue: `{s['weak_skeleton_grammar_clue']}`.",
            f"- {s['interpretation']}",
            "- Skeleton atlas remains materialized.",
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
