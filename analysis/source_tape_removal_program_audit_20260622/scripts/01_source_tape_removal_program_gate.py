#!/usr/bin/env python3
"""Decoder-visible source tape removal audit.

The minimal external tape program made copy source/hint one explicit external
tape. This gate tests whether that tape can be removed by a decoder-visible
source policy plus paid exceptions while keeping an executable decoder.

This is not a local rank selector: sources are chosen during execution from the
already emitted digit stream. A miss changes output unless repaired by a paid
exception address.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "source_tape_removal_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_PATH = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
LEDGER_PATH = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
FAMILY_HOLDOUT_PATH = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "08_recipe_reparse_family_holdout.json"
)

JSON_OUT = TEST_RESULTS / "01_source_tape_removal_program_gate.json"
MD_OUT = TEST_RESULTS / "01_source_tape_removal_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_source_tape_removal_program_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 200
ALPHA = 0.5


def log2(value: float) -> float:
    return math.log2(value)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_books() -> dict[str, str]:
    return {str(key): value for key, value in load_json(BOOKS_PATH).items()}


def load_rows() -> dict[int, list[dict]]:
    rows = load_json(LEDGER_PATH)["ledger_rows"]
    by_book: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_book[int(row["book"])].append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in by_book.items()
    }


def load_families() -> dict[str, set[int]]:
    if not FAMILY_HOLDOUT_PATH.exists():
        return {}
    families = {}
    for row in load_json(FAMILY_HOLDOUT_PATH).get("rows", []):
        books = {int(book) for book in row.get("test_books", []) if int(book) >= 10}
        if books:
            families[str(row["label"])] = books
    return families


class State:
    def __init__(self) -> None:
        self.previous_copy_source: int | None = None
        self.previous_copy_length: int | None = None
        self.previous_op_start: int | None = None
        self.op_boundaries: list[int] = []
        self.book_starts: list[int] = []


def valid_count(available_length: int, length: int) -> int:
    return max(0, available_length - length + 1)


def clamp_source(source: int, available_length: int, length: int) -> int:
    count = valid_count(available_length, length)
    if count <= 0:
        return 0
    return max(0, min(source, count - 1))


def earliest_policy(_available: str, length: int, _state: State, _row: dict) -> int:
    return 0


def latest_policy(available: str, length: int, _state: State, _row: dict) -> int:
    return max(0, len(available) - length)


def previous_source_policy(available: str, length: int, state: State, _row: dict) -> int:
    if state.previous_copy_source is not None:
        return clamp_source(state.previous_copy_source, len(available), length)
    return latest_policy(available, length, state, _row)


def previous_end_policy(available: str, length: int, state: State, _row: dict) -> int:
    if state.previous_copy_source is not None and state.previous_copy_length is not None:
        return clamp_source(state.previous_copy_source + state.previous_copy_length, len(available), length)
    return latest_policy(available, length, state, _row)


def latest_op_boundary_policy(available: str, length: int, state: State, _row: dict) -> int:
    limit = valid_count(len(available), length)
    for boundary in reversed(state.op_boundaries):
        if boundary < limit:
            return boundary
    return latest_policy(available, length, state, _row)


def latest_book_start_policy(available: str, length: int, state: State, _row: dict) -> int:
    limit = valid_count(len(available), length)
    for boundary in reversed(state.book_starts):
        if boundary < limit:
            return boundary
    return latest_policy(available, length, state, _row)


def length_mod_policy(available: str, length: int, _state: State, row: dict) -> int:
    count = valid_count(len(available), length)
    if count <= 0:
        return 0
    return (int(row["book"]) * 31 + int(row["op_index"]) * 17 + length) % count


POLICIES: dict[str, Callable[[str, int, State, dict], int]] = {
    "earliest": earliest_policy,
    "latest": latest_policy,
    "previous_source": previous_source_policy,
    "previous_source_end": previous_end_policy,
    "latest_op_boundary": latest_op_boundary_policy,
    "latest_book_start": latest_book_start_policy,
    "length_mod": length_mod_policy,
}


def exception_flag_bits(train_exception_rate: float, is_exception: bool) -> float:
    probability = train_exception_rate if is_exception else 1.0 - train_exception_rate
    return -log2(max(probability, 1e-300))


def train_exception_rate(books: dict[str, str], rows_by_book: dict[int, list[dict]], train_books: set[int], policy_name: str) -> float:
    policy = POLICIES[policy_name]
    stream = "".join(books[str(book)] for book in range(10))
    state = State()
    state.book_starts = [0]
    exceptions = 0
    total = 0
    for book in range(10, 70):
        book_start = len(stream)
        if book in rows_by_book:
            current = []
            state.book_starts.append(book_start)
            for row in rows_by_book[book]:
                state.previous_op_start = book_start + int(row["target_start"])
                state.op_boundaries.append(state.previous_op_start)
                if row["op_type"] == "literal":
                    current.append(row["literal_payload"] or "")
                    continue
                length = int(row["exact_length"])
                available = stream + "".join(current)
                source = policy(available, length, state, row)
                predicted = available[source : source + length]
                target = books[str(book)][int(row["target_start"]) : int(row["target_start"]) + length]
                if book in train_books:
                    total += 1
                    if predicted != target:
                        exceptions += 1
                canonical_source = int(row["copy_source_raw"])
                current.append(available[canonical_source : canonical_source + length])
                state.previous_copy_source = canonical_source
                state.previous_copy_length = length
            stream += "".join(current)
        else:
            stream += books[str(book)]
    return (exceptions + ALPHA) / (total + 2 * ALPHA) if total else 0.5


def execute_policy(
    *,
    books: dict[str, str],
    rows_by_book: dict[int, list[dict]],
    test_books: set[int],
    train_books: set[int],
    policy_name: str,
    repair_exceptions: bool,
) -> dict:
    policy = POLICIES[policy_name]
    rate = train_exception_rate(books, rows_by_book, train_books, policy_name)
    stream = "".join(books[str(book)] for book in range(10))
    state = State()
    state.book_starts = [0]
    metrics = Counter()
    examples = []
    rendered_books: dict[int, str] = {}
    for book in range(10, 70):
        book_start = len(stream)
        state.book_starts.append(book_start)
        current: list[str] = []
        for row in rows_by_book[book]:
            target_start = int(row["target_start"])
            state.previous_op_start = book_start + target_start
            state.op_boundaries.append(state.previous_op_start)
            if row["op_type"] == "literal":
                current.append(row["literal_payload"] or "")
                continue
            length = int(row["exact_length"])
            available = stream + "".join(current)
            target = books[str(book)][target_start : target_start + length]
            predicted_source = policy(available, length, state, row)
            predicted = available[predicted_source : predicted_source + length]
            is_test = book in test_books
            if is_test:
                metrics["test_copy_ops"] += 1
                metrics["baseline_copy_hint_bits"] += float(row["copy_hint_rank_bits"])
                if predicted == target:
                    metrics["default_copy_hits"] += 1
                    metrics["policy_bits"] += exception_flag_bits(rate, False)
                    emitted = predicted
                else:
                    metrics["default_copy_misses"] += 1
                    source_candidates = valid_count(len(available), length)
                    metrics["exception_source_bits"] += log2(max(1, source_candidates))
                    metrics["policy_bits"] += exception_flag_bits(rate, True) + log2(max(1, source_candidates))
                    if len(examples) < 8:
                        examples.append(
                            {
                                "book": book,
                                "op_index": int(row["op_index"]),
                                "length": length,
                                "predicted_source": predicted_source,
                                "canonical_source": int(row["copy_source_raw"]),
                                "valid_source_count": source_candidates,
                            }
                        )
                    if repair_exceptions:
                        canonical_source = int(row["copy_source_raw"])
                        emitted = available[canonical_source : canonical_source + length]
                    else:
                        emitted = predicted
            else:
                canonical_source = int(row["copy_source_raw"])
                emitted = available[canonical_source : canonical_source + length]
            current.append(emitted)
            # The state visible to later decisions follows the emitted program.
            if repair_exceptions or not is_test or predicted == target:
                state.previous_copy_source = int(row["copy_source_raw"]) if (is_test and predicted != target) else predicted_source
            else:
                state.previous_copy_source = predicted_source
            state.previous_copy_length = length
        rendered = "".join(current)
        rendered_books[book] = rendered
        if book in test_books:
            metrics["test_books"] += 1
            if rendered == books[str(book)]:
                metrics["exact_books"] += 1
        stream += rendered if book in test_books and not repair_exceptions else books[str(book)]
    metrics["saving_vs_copy_hint_bits"] = metrics["baseline_copy_hint_bits"] - metrics["policy_bits"]
    return {
        "examples": examples,
        "metrics": dict(metrics),
        "repair_exceptions": repair_exceptions,
        "train_exception_rate": rate,
    }


def split_specs(rows_by_book: dict[int, list[dict]]) -> list[tuple[str, set[int], set[int]]]:
    all_books = set(rows_by_book)
    specs = []
    for cutoff in CUTOFFS:
        train = {book for book in all_books if book < cutoff}
        test = {book for book in all_books if book >= cutoff}
        specs.append((f"prefix_{cutoff}", train, test))
    for label, test in sorted(load_families().items()):
        test = {book for book in test if book in all_books}
        train = all_books - test
        if train and test:
            specs.append((f"family_{label}", train, test))
    return specs


def random_policy_score(books: dict[str, str], rows_by_book: dict[int, list[dict]], test_books: set[int], rng: random.Random) -> float:
    baseline = 0.0
    correction = 0.0
    stream = "".join(books[str(book)] for book in range(10))
    for book in range(10, 70):
        current = []
        for row in rows_by_book[book]:
            if row["op_type"] == "literal":
                current.append(row["literal_payload"] or "")
                continue
            length = int(row["exact_length"])
            available = stream + "".join(current)
            canonical_source = int(row["copy_source_raw"])
            emitted = available[canonical_source : canonical_source + length]
            if book in test_books:
                baseline += float(row["copy_hint_rank_bits"])
                target_start = int(row["target_start"])
                target = books[str(book)][target_start : target_start + length]
                count = valid_count(len(available), length)
                source = rng.randrange(max(1, count))
                if available[source : source + length] != target:
                    correction += 1.0 + log2(max(1, count))
                else:
                    correction += 1.0
            current.append(emitted)
        stream += "".join(current)
    return baseline - correction


def evaluate() -> dict:
    books = load_books()
    rows_by_book = load_rows()
    rng = random.Random(469)
    policy_results = {}
    for policy_name in POLICIES:
        rows = []
        totals = Counter()
        random_savings = []
        for label, train, test in split_specs(rows_by_book):
            repaired = execute_policy(
                books=books,
                rows_by_book=rows_by_book,
                test_books=test,
                train_books=train,
                policy_name=policy_name,
                repair_exceptions=True,
            )
            unrepaired = execute_policy(
                books=books,
                rows_by_book=rows_by_book,
                test_books=test,
                train_books=train,
                policy_name=policy_name,
                repair_exceptions=False,
            )
            metrics = repaired["metrics"]
            for key, value in metrics.items():
                totals[key] += value
            totals["unrepaired_exact_books"] += unrepaired["metrics"].get("exact_books", 0)
            rows.append(
                {
                    "label": label,
                    "test_books": len(test),
                    "train_books": len(train),
                    "repaired": repaired,
                    "unrepaired_exact_books": unrepaired["metrics"].get("exact_books", 0),
                }
            )
            for _ in range(RANDOM_TRIALS):
                random_savings.append(random_policy_score(books, rows_by_book, test, rng))
        p95 = sorted(random_savings)[int(0.95 * (len(random_savings) - 1))]
        promoted = totals["saving_vs_copy_hint_bits"] > 0 and totals["saving_vs_copy_hint_bits"] > p95
        policy_results[policy_name] = {
            "classification": "PROMOTED_DECODER_VISIBLE_SOURCE_TAPE_REMOVAL" if promoted else "source_tape_removal_not_promoted",
            "random_policy_saving_p95": p95,
            "rows": rows,
            "totals": dict(totals),
        }
    best_policy = max(
        policy_results,
        key=lambda name: (
            policy_results[name]["totals"].get("saving_vs_copy_hint_bits", 0.0),
            policy_results[name]["totals"].get("default_copy_hits", 0),
        ),
    )
    promoted = [
        name for name, result in policy_results.items()
        if result["classification"] == "PROMOTED_DECODER_VISIBLE_SOURCE_TAPE_REMOVAL"
    ]
    classification = "PROMOTED_DECODER_VISIBLE_SOURCE_TAPE_REMOVAL" if promoted else "source_tape_removal_not_promoted"
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "best_policy": best_policy,
            "promoted_policies": promoted,
            "row0_status": "unchanged_exogenous",
        },
        "inputs": {
            "books": rel(BOOKS_PATH),
            "ledger": rel(LEDGER_PATH),
            "family_holdout": rel(FAMILY_HOLDOUT_PATH),
            "random_trials": RANDOM_TRIALS,
        },
        "plaintext_claim": False,
        "policy_results": policy_results,
        "scope": "analysis_only_decoder_visible_source_tape_removal",
        "translation_delta": "NONE",
    }


def write_markdown(result: dict) -> None:
    best_name = result["decision"]["best_policy"]
    best = result["policy_results"][best_name]
    t = best["totals"]
    lines = [
        "# Decoder-Visible Source Tape Removal Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Try to remove the copy source/hint tape from the executable decoder. The "
        "decoder receives seed books, coarse controls, exact lengths, and literal "
        "payloads. A decoder-visible policy chooses copy sources; misses are repaired "
        "by paid uniform source-address exceptions.",
        "",
        "## Best Policy",
        "",
        f"- Best policy: `{best_name}`.",
        f"- Best policy classification: `{best['classification']}`.",
        f"- Default copy hits: `{t.get('default_copy_hits', 0)}/{t.get('test_copy_ops', 0)}`.",
        f"- Unrepaired exact books over repeated holdouts: `{t.get('unrepaired_exact_books', 0)}`.",
        f"- Baseline copy-hint bits: `{t.get('baseline_copy_hint_bits', 0.0):.3f}`.",
        f"- Policy+exception bits: `{t.get('policy_bits', 0.0):.3f}`.",
        f"- Saving vs copy-hint tape: `{t.get('saving_vs_copy_hint_bits', 0.0):.3f}`.",
        f"- Random visible-source p95 saving: `{best['random_policy_saving_p95']:.3f}`.",
        "",
        "| Split | Test Books | Copy Ops | Default Hits | Exact Books Without Repairs | Saving |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in best["rows"]:
        metrics = row["repaired"]["metrics"]
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | `{metrics.get('test_copy_ops', 0)}` | "
            f"`{metrics.get('default_copy_hits', 0)}` | `{row['unrepaired_exact_books']}` | "
            f"`{metrics.get('saving_vs_copy_hint_bits', 0.0):.3f}` |"
        )
    lines.extend(["", "## Decision", ""])
    if result["classification"] == "PROMOTED_DECODER_VISIBLE_SOURCE_TAPE_REMOVAL":
        lines.append(
            "A decoder-visible source policy removes part of the source tape after paid "
            "exceptions and controls. This is generation progress but not a row0 or "
            "plaintext claim."
        )
    else:
        lines.append(
            "`source_tape_removal_not_promoted`: decoder-visible policies do not beat "
            "the existing copy-hint/source tape after exception costs. The source tape "
            "remains external in the minimal program."
        )
    lines.extend(
        [
            "",
            "## Remaining External Fields",
            "",
            "- copy source/hint tape",
            "- coarse control stream when macro/template program misses",
            "- book-level composition index",
            "- literal innovation payload tape",
            "- seed books `0..9`",
            "- `row0`",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict) -> None:
    best_name = result["decision"]["best_policy"]
    best = result["policy_results"][best_name]
    t = best["totals"]
    lines = [
        "# Final Source Tape Removal Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can the executable decoder remove the copy source/hint tape using only "
        "decoder-visible source policies plus paid exceptions?",
        "",
        "## Evidence",
        "",
        f"- Best policy: `{best_name}`.",
        f"- Default copy hits: `{t.get('default_copy_hits', 0)}/{t.get('test_copy_ops', 0)}`.",
        f"- Unrepaired exact books over repeated holdouts: `{t.get('unrepaired_exact_books', 0)}`.",
        f"- Baseline copy-hint bits: `{t.get('baseline_copy_hint_bits', 0.0):.3f}`.",
        f"- Policy+exception bits: `{t.get('policy_bits', 0.0):.3f}`.",
        f"- Saving vs copy-hint tape: `{t.get('saving_vs_copy_hint_bits', 0.0):.3f}`.",
        f"- Random visible-source p95 saving: `{best['random_policy_saving_p95']:.3f}`.",
        "",
        "## Decision",
        "",
    ]
    if result["classification"] == "PROMOTED_DECODER_VISIBLE_SOURCE_TAPE_REMOVAL":
        lines.append(
            "The source tape has a promoted decoder-visible reduction. It still does "
            "not affect row0, plaintext, translation, or the compression bound."
        )
    else:
        lines.append(
            "`source_tape_removal_not_promoted`. The copy source/hint tape remains "
            "external: simple decoder-visible source policies either emit wrong books "
            "or cost more after uniform source-address exceptions."
        )
    lines.extend(
        [
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_source_tape_removal_program_gate.py](../scripts/01_source_tape_removal_program_gate.py)",
            "- [01_source_tape_removal_program_gate.json](test_results/01_source_tape_removal_program_gate.json)",
            "- [01_source_tape_removal_program_gate.md](test_results/01_source_tape_removal_program_gate.md)",
        ]
    )
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = evaluate()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
