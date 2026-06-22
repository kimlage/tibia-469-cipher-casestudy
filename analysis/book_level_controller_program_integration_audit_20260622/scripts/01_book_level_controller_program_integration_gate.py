#!/usr/bin/env python3
"""Integrate the book-level controller into the executable tape program.

The minimal external tape program left `coarse type:length_bucket` and the
book-level composition index as paid external tapes. A previous audit promoted a
book-level controller candidate for that stream. This gate tests whether that
candidate actually reduces the executable program ledger after paying beam-rank
or full-sequence corrections under prefix and public-bookcase family holdout.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "book_level_controller_program_integration_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
SOURCE_SCRIPT = (
    ROOT
    / "analysis"
    / "book_level_coarse_length_controller_audit_20260622"
    / "scripts"
    / "01_book_level_coarse_length_controller_gate.py"
)
MINIMAL_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
FAMILY_HOLDOUT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "08_recipe_reparse_family_holdout.json"
)
JSON_OUT = TEST_RESULTS / "01_book_level_controller_program_integration_gate.json"
MD_OUT = TEST_RESULTS / "01_book_level_controller_program_integration_gate.md"
FINAL_OUT = FRONT / "reports" / "final_book_level_controller_program_integration_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 40
PERMUTED_TRAIN_TRIALS = 8
FROZEN_COUNT_MODEL = "book_length"
FROZEN_COARSE_MODEL = "op_count"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("book_level_controller_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CTRL = load_module(SOURCE_SCRIPT)


def log2(value: float) -> float:
    return math.log2(value)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_families() -> dict[str, set[int]]:
    if not FAMILY_HOLDOUT.exists():
        return {}
    families = {}
    for row in load_json(FAMILY_HOLDOUT).get("rows", []):
        books = {int(book) for book in row.get("test_books", []) if int(book) >= 10}
        if books:
            families[str(row["label"])] = books
    return families


def split_specs(books: dict[int, list[dict]]) -> list[tuple[str, set[int], set[int], str]]:
    all_books = set(books)
    specs = []
    for cutoff in CUTOFFS:
        train = {book for book in all_books if book < cutoff}
        test = {book for book in all_books if book >= cutoff}
        specs.append((f"prefix_{cutoff}", train, test, "prefix"))
    for label, test in sorted(load_families().items()):
        test = {book for book in test if book in all_books}
        train = all_books - test
        if train and test:
            specs.append((f"family_{label}", train, test, "family"))
    return specs


def composition_bits(rows: list[dict]) -> float:
    sequence = [row["symbol"] for row in rows]
    book_length = int(rows[0]["book_length"])
    return log2(max(1, CTRL.count_compositions(sequence, book_length)))


def baseline_bits(rows: list[dict]) -> float:
    return len(rows) * log2(len(CTRL.VOCAB)) + composition_bits(rows)


def sequence_cost_from_beam(decoded: list[dict], rows: list[dict]) -> tuple[float, dict]:
    true_sequence = [row["symbol"] for row in rows]
    true_count = len(rows)
    for index, item in enumerate(decoded):
        if item["op_count"] == true_count and item["sequence"] == true_sequence:
            return log2(index + 1), {
                "sequence_in_beam": True,
                "beam_rank": index + 1,
                "top1_exact": index == 0,
            }
    correction_bits = log2(CTRL.MAX_OPCOUNT) + len(rows) * log2(len(CTRL.VOCAB))
    return correction_bits, {
        "sequence_in_beam": False,
        "beam_rank": None,
        "top1_exact": False,
    }


def decoded_for_split(
    books: dict[int, list[dict]],
    train_ids: set[int],
    test_ids: set[int],
) -> dict[int, list[dict]]:
    train = {book: rows for book, rows in books.items() if book in train_ids}
    test = {book: rows for book, rows in books.items() if book in test_ids}
    count_model = CTRL.train_count_model(FROZEN_COUNT_MODEL, train)
    coarse_model = CTRL.train_coarse_model(FROZEN_COARSE_MODEL, train)
    return {
        book: CTRL.decode_book(count_model, coarse_model, book, rows)
        for book, rows in sorted(test.items())
    }


def score_split(
    books: dict[int, list[dict]],
    train_ids: set[int],
    test_ids: set[int],
    decoded_by_book: dict[int, list[dict]] | None = None,
) -> dict:
    test = {book: rows for book, rows in books.items() if book in test_ids}
    if decoded_by_book is None:
        decoded_by_book = decoded_for_split(books, train_ids, test_ids)
    rows_out = []
    totals = Counter()
    for book, rows in sorted(test.items()):
        decoded = decoded_by_book[book]
        seq_bits, hit = sequence_cost_from_beam(decoded, rows)
        comp_bits = composition_bits(rows)
        base = baseline_bits(rows)
        controller = seq_bits + comp_bits
        totals["baseline_bits"] += base
        totals["controller_bits"] += controller
        totals["saving_bits"] += base - controller
        totals["test_books"] += 1
        totals["test_ops"] += len(rows)
        if hit["sequence_in_beam"]:
            totals["sequence_in_beam"] += 1
            if len(rows) > 1:
                totals["nontrivial_sequence_in_beam"] += 1
        if hit["top1_exact"]:
            totals["top1_exact_books"] += 1
            totals["top1_exact_ops"] += len(rows)
            if len(rows) > 1:
                totals["top1_nontrivial_exact_books"] += 1
        rows_out.append(
            {
                "baseline_bits": base,
                "book": book,
                "composition_bits": comp_bits,
                "controller_bits": controller,
                "op_count": len(rows),
                "saving_bits": base - controller,
                **hit,
            }
        )
    return {"book_rows": rows_out, "totals": dict(totals)}


def shuffled_sequence_control(
    books: dict[int, list[dict]],
    train_ids: set[int],
    test_ids: set[int],
    rng: random.Random,
    decoded_by_book: dict[int, list[dict]],
) -> float:
    test = {book: rows for book, rows in books.items() if book in test_ids}
    payloads = [(len(rows), [row["symbol"] for row in rows], composition_bits(rows), baseline_bits(rows)) for rows in test.values()]
    rng.shuffle(payloads)
    saving = 0.0
    for (book, rows), (fake_count, fake_sequence, fake_comp_bits, fake_baseline) in zip(sorted(test.items()), payloads):
        decoded = decoded_by_book[book]
        seq_bits = None
        for index, item in enumerate(decoded):
            if item["op_count"] == fake_count and item["sequence"] == fake_sequence:
                seq_bits = log2(index + 1)
                break
        if seq_bits is None:
            seq_bits = log2(CTRL.MAX_OPCOUNT) + fake_count * log2(len(CTRL.VOCAB))
        saving += fake_baseline - (seq_bits + fake_comp_bits)
    return saving


def random_trainset_control(books: dict[int, list[dict]], train_size: int, rng: random.Random) -> float:
    ids = sorted(books)
    train_ids = set(rng.sample(ids, train_size))
    test_ids = set(ids) - train_ids
    if not test_ids:
        return 0.0
    return score_split(books, train_ids, test_ids)["totals"]["saving_bits"]


def evaluate() -> dict:
    books = CTRL.load_books()
    rng = random.Random(469)
    split_rows = []
    totals = Counter()
    shuffled_controls = []
    random_train_controls = []
    for label, train_ids, test_ids, split_type in split_specs(books):
        decoded_by_book = decoded_for_split(books, train_ids, test_ids)
        scored = score_split(books, train_ids, test_ids, decoded_by_book)
        for key, value in scored["totals"].items():
            totals[key] += value
        split_rows.append(
            {
                "label": label,
                "split_type": split_type,
                "test_books": len(test_ids),
                "train_books": len(train_ids),
                **scored["totals"],
                "examples": scored["book_rows"][:6],
            }
        )
        for _ in range(RANDOM_TRIALS):
            shuffled_controls.append(shuffled_sequence_control(books, train_ids, test_ids, rng, decoded_by_book))
        if split_type == "prefix":
            for _ in range(PERMUTED_TRAIN_TRIALS):
                random_train_controls.append(random_trainset_control(books, len(train_ids), rng))
    shuffled_p95 = sorted(shuffled_controls)[int(0.95 * (len(shuffled_controls) - 1))]
    random_train_p95 = sorted(random_train_controls)[int(0.95 * (len(random_train_controls) - 1))] if random_train_controls else 0.0
    promoted = totals["saving_bits"] > 0 and totals["saving_bits"] > shuffled_p95
    classification = (
        "PROMOTED_EXECUTABLE_BOOK_LEVEL_CONTROLLER"
        if promoted
        else "book_level_controller_program_integration_not_promoted"
    )
    minimal_summary = load_json(MINIMAL_LEDGER)["summary"]
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": {
            "random_trials": RANDOM_TRIALS,
            "permuted_train_trials_per_prefix": PERMUTED_TRAIN_TRIALS,
            "random_trainset_saving_p95": random_train_p95,
            "same_multiset_shuffled_saving_p95": shuffled_p95,
        },
        "decision": {
            "frozen_count_model": FROZEN_COUNT_MODEL,
            "frozen_coarse_model": FROZEN_COARSE_MODEL,
            "promoted": promoted,
            "row0_status": "unchanged_exogenous",
        },
        "inputs": {
            "controller_script": rel(SOURCE_SCRIPT),
            "family_holdout": rel(FAMILY_HOLDOUT),
            "minimal_external_tape_ledger": rel(MINIMAL_LEDGER),
        },
        "minimal_ledger_reference": {
            "full_corpus_coarse_plus_composition_bits": (
                minimal_summary["coarse_control_bits_uniform"] + minimal_summary["composition_index_bits"]
            ),
        },
        "plaintext_claim": False,
        "rows": split_rows,
        "scope": "analysis_only_book_level_controller_program_integration",
        "summary": dict(totals),
        "translation_delta": "NONE",
    }


def write_markdown(result: dict) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Book-Level Controller Program Integration Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Integrate the previously promoted book-level coarse length controller into "
        "the executable minimal external tape program. The comparison target is "
        "the program ledger's uniform `coarse type:length_bucket` stream plus "
        "book-level composition index.",
        "",
        "## Summary",
        "",
        f"- Frozen controller pair: `{result['decision']['frozen_count_model']}__{result['decision']['frozen_coarse_model']}`.",
        f"- Baseline coarse+composition bits over splits: `{s.get('baseline_bits', 0.0):.3f}`.",
        f"- Controller+correction bits over splits: `{s.get('controller_bits', 0.0):.3f}`.",
        f"- Saving: `{s.get('saving_bits', 0.0):.3f}` bits.",
        f"- True sequence in beam: `{s.get('sequence_in_beam', 0)}/{s.get('test_books', 0)}`.",
        f"- Nontrivial true sequence in beam: `{s.get('nontrivial_sequence_in_beam', 0)}`.",
        f"- Top-1 exact books: `{s.get('top1_exact_books', 0)}`.",
        f"- Top-1 nontrivial exact books: `{s.get('top1_nontrivial_exact_books', 0)}`.",
        f"- Top-1 exact ops: `{s.get('top1_exact_ops', 0)}`.",
        "- Model/grammar descriptor cost charged here: `0.000` bits (generous lower bound).",
        f"- Same-multiset shuffled p95: `{c['same_multiset_shuffled_saving_p95']:.3f}` bits.",
        f"- Random trainset p95: `{c['random_trainset_saving_p95']:.3f}` bits.",
        "",
        "| Split | Test Books | Baseline | Controller | Saving | Sequence In Beam | Top1 Exact |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | `{row.get('baseline_bits', 0.0):.3f}` | "
            f"`{row.get('controller_bits', 0.0):.3f}` | `{row.get('saving_bits', 0.0):.3f}` | "
            f"`{row.get('sequence_in_beam', 0)}` | `{row.get('top1_exact_books', 0)}` |"
        )
    lines.extend(["", "## Decision", ""])
    if result["classification"] == "PROMOTED_EXECUTABLE_BOOK_LEVEL_CONTROLLER":
        lines.append(
            "The controller is promoted inside the executable program: it reduces the "
            "coarse+composition tape after paid beam-rank/full-sequence corrections. "
            "This is generation-program progress, not a new compression bound."
        )
    else:
        lines.append(
            "`book_level_controller_program_integration_not_promoted`: the controller "
            "does not reduce the executable coarse+composition tape after corrections "
            "and controls."
        )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Final Book-Level Controller Program Integration Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can the already-promoted book-level coarse controller reduce an actual "
        "external tape in the executable decoder contract?",
        "",
        "## Evidence",
        "",
        f"- Frozen pair: `{result['decision']['frozen_count_model']}__{result['decision']['frozen_coarse_model']}`.",
        f"- Baseline coarse+composition bits over prefix/family splits: `{s.get('baseline_bits', 0.0):.3f}`.",
        f"- Controller+correction bits: `{s.get('controller_bits', 0.0):.3f}`.",
        f"- Saving: `{s.get('saving_bits', 0.0):.3f}` bits.",
        f"- True sequence in beam: `{s.get('sequence_in_beam', 0)}/{s.get('test_books', 0)}`.",
        f"- Nontrivial beam hits: `{s.get('nontrivial_sequence_in_beam', 0)}`.",
        f"- Top-1 exact books: `{s.get('top1_exact_books', 0)}`.",
        f"- Top-1 nontrivial exact books: `{s.get('top1_nontrivial_exact_books', 0)}`.",
        f"- Top-1 exact ops: `{s.get('top1_exact_ops', 0)}`.",
        "- Model/grammar descriptor cost charged here: `0.000` bits, so the negative result is a generous lower bound.",
        f"- Same-multiset shuffled p95: `{c['same_multiset_shuffled_saving_p95']:.3f}` bits.",
        f"- Random trainset p95: `{c['random_trainset_saving_p95']:.3f}` bits.",
        "",
        "## Decision",
        "",
    ]
    if result["classification"] == "PROMOTED_EXECUTABLE_BOOK_LEVEL_CONTROLLER":
        lines.append(
            "The book-level controller is promoted as an executable-program component: "
            "it reduces the coarse+composition external tape after paid corrections. "
            "Remaining source, literal, seed, and row0 dependencies stay external."
        )
    else:
        lines.append(
            "The integration is not promoted. The previous controller remains a "
            "candidate clue, but it does not reduce the executable ledger under this "
            "charged integration."
        )
    lines.extend(
        [
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_book_level_controller_program_integration_gate.py](../scripts/01_book_level_controller_program_integration_gate.py)",
            "- [01_book_level_controller_program_integration_gate.json](test_results/01_book_level_controller_program_integration_gate.json)",
            "- [01_book_level_controller_program_integration_gate.md](test_results/01_book_level_controller_program_integration_gate.md)",
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
