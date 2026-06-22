#!/usr/bin/env python3
"""Residual burden cross-prediction gate.

The book residual mode is a strong joint summary, but a paid header did not
reduce exact executable tapes. This gate asks a more precise question: do the
other book-level residual burdens predict each held-out burden field after
paying the leave-one-field-out mode header?

This is a representation test, not a plaintext/translation test and not a
compression-bound update.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "residual_burden_cross_prediction_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

COUPLING_SCRIPT = (
    ROOT
    / "analysis"
    / "book_residual_mode_coupling_audit_20260622"
    / "scripts"
    / "01_book_residual_mode_coupling_gate.py"
)
COUPLING_GATE = (
    ROOT
    / "analysis"
    / "book_residual_mode_coupling_audit_20260622"
    / "reports"
    / "test_results"
    / "01_book_residual_mode_coupling_gate.json"
)
HEADER_CODEC_GATE = (
    ROOT
    / "analysis"
    / "residual_mode_header_codec_audit_20260622"
    / "reports"
    / "test_results"
    / "01_residual_mode_header_codec_gate.json"
)
UNIFIED_TAPE_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)

JSON_OUT = TEST_RESULTS / "01_residual_burden_cross_prediction_gate.json"
MD_OUT = TEST_RESULTS / "01_residual_burden_cross_prediction_gate.md"
FINAL_OUT = FRONT / "reports" / "final_residual_burden_cross_prediction_audit.md"

FIELDS = [
    "op_count_class",
    "literal_digit_class",
    "literal_op_class",
    "copy_hint_bits_class",
    "composition_bits_class",
]
TARGET_FIELDS = [
    "literal_digit_class",
    "copy_hint_bits_class",
    "composition_bits_class",
]
ALPHA = 0.5
RANDOM_SEED = 46920260622 + 9
RANDOM_TRIALS = 300


def load_module(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("book_residual_mode_coupling_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


COUPLING = load_module(COUPLING_SCRIPT)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def book_rows() -> dict[int, dict[str, Any]]:
    ledger = load_json(UNIFIED_TAPE_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    return COUPLING.summarize_books(ledger)


def mode_without(row: dict[str, Any], target_field: str) -> str:
    return "|".join(str(row[field]) for field in FIELDS if field != target_field)


def split_specs(rows: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    return COUPLING.split_specs(rows)


def code_symbol(symbol: str, counts: Counter[str], alphabet_size: int) -> float:
    total = sum(counts.values())
    probability = (counts.get(symbol, 0) + ALPHA) / (total + ALPHA * alphabet_size)
    return -math.log2(probability)


def target_alphabet(rows: dict[int, dict[str, Any]], target_field: str) -> list[str]:
    return sorted({str(row[target_field]) for row in rows.values()})


def mode_alphabet(rows: dict[int, dict[str, Any]], target_field: str) -> list[str]:
    return sorted({mode_without(row, target_field) for row in rows.values()})


def score_split(rows: dict[int, dict[str, Any]], split: dict[str, Any], target_field: str) -> dict[str, Any]:
    train = set(split["train"])
    test = set(split["test"])
    target_values = target_alphabet(rows, target_field)
    mode_values = mode_alphabet(rows, target_field)
    global_counts = Counter(str(rows[book][target_field]) for book in train)
    mode_counts = Counter(mode_without(rows[book], target_field) for book in train)
    target_by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    for book in train:
        target_by_mode[mode_without(rows[book], target_field)][str(rows[book][target_field])] += 1
    global_bits = 0.0
    conditional_bits = 0.0
    header_bits = 0.0
    exact_header_seen = 0
    for book in sorted(test):
        mode = mode_without(rows[book], target_field)
        target = str(rows[book][target_field])
        global_bits += code_symbol(target, global_counts, len(target_values))
        conditional_bits += code_symbol(
            target,
            target_by_mode.get(mode, global_counts),
            len(target_values),
        )
        header_bits += code_symbol(mode, mode_counts, len(mode_values))
        exact_header_seen += int(mode_counts.get(mode, 0) > 0)
    after_header_bits = conditional_bits + header_bits
    return {
        "after_header_bits": after_header_bits,
        "conditional_bits": conditional_bits,
        "conditional_saving_before_header": global_bits - conditional_bits,
        "exact_header_seen": exact_header_seen,
        "global_bits": global_bits,
        "header_bits": header_bits,
        "label": split["label"],
        "saving_after_header": global_bits - after_header_bits,
        "split_type": split["split_type"],
        "target_field": target_field,
        "test_books": len(test),
        "train_books": len(train),
    }


def evaluate_target(rows: dict[int, dict[str, Any]], target_field: str) -> dict[str, Any]:
    split_rows = [score_split(rows, split, target_field) for split in split_specs(rows)]
    global_bits = sum(row["global_bits"] for row in split_rows)
    conditional_bits = sum(row["conditional_bits"] for row in split_rows)
    header_bits = sum(row["header_bits"] for row in split_rows)
    after_header = sum(row["after_header_bits"] for row in split_rows)
    return {
        "split_rows": split_rows,
        "summary": {
            "conditional_saving_before_header": global_bits - conditional_bits,
            "exact_header_seen": sum(row["exact_header_seen"] for row in split_rows),
            "global_bits": global_bits,
            "header_bits": header_bits,
            "positive_after_header_splits": sum(row["saving_after_header"] > 0 for row in split_rows),
            "positive_conditional_splits": sum(row["conditional_saving_before_header"] > 0 for row in split_rows),
            "saving_after_header": global_bits - after_header,
            "split_count": len(split_rows),
            "target_field": target_field,
            "test_books_repeated": sum(row["test_books"] for row in split_rows),
        },
    }


def shuffled_target_controls(rows: dict[int, dict[str, Any]], target_field: str, real_saving: float) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in target_field))
    books = sorted(rows)
    values = [rows[book][target_field] for book in books]
    savings = []
    for _ in range(RANDOM_TRIALS):
        shuffled_values = list(values)
        rng.shuffle(shuffled_values)
        shuffled = {book: dict(rows[book]) for book in books}
        for book, value in zip(books, shuffled_values):
            shuffled[book][target_field] = value
        savings.append(evaluate_target(shuffled, target_field)["summary"]["saving_after_header"])
    return {
        "beats_shuffled_p05": real_saving > percentile(savings, 5),
        "beats_shuffled_p50": real_saving > percentile(savings, 50),
        "beats_shuffled_p95": real_saving > percentile(savings, 95),
        "shuffled_mean": sum(savings) / len(savings),
        "shuffled_p05": percentile(savings, 5),
        "shuffled_p50": percentile(savings, 50),
        "shuffled_p95": percentile(savings, 95),
        "trials": RANDOM_TRIALS,
    }


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def make_result() -> dict[str, Any]:
    coupling = load_json(COUPLING_GATE)
    header = load_json(HEADER_CODEC_GATE)
    assert_boundary("book_residual_mode_coupling_gate", coupling)
    assert_boundary("residual_mode_header_codec_gate", header)
    rows = book_rows()
    target_results = {}
    promoted = []
    weak = []
    for target_field in TARGET_FIELDS:
        evaluated = evaluate_target(rows, target_field)
        controls = shuffled_target_controls(
            rows,
            target_field,
            evaluated["summary"]["saving_after_header"],
        )
        evaluated["controls"] = controls
        target_results[target_field] = evaluated
        if evaluated["summary"]["saving_after_header"] > 0 and controls["beats_shuffled_p95"]:
            promoted.append(target_field)
        elif evaluated["summary"]["conditional_saving_before_header"] > 0:
            weak.append(target_field)
    classification = (
        "PROMOTED_RESIDUAL_BURDEN_CROSS_PREDICTION"
        if promoted
        else "WEAK_RESIDUAL_BURDEN_CROSS_PREDICTION"
        if weak
        else "RESIDUAL_BURDEN_CROSS_PREDICTION_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "generator_promoted": False,
            "promoted_targets": promoted,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
            "weak_targets": weak,
        },
        "inputs": {
            "book_residual_mode_coupling_gate": rel(COUPLING_GATE),
            "residual_mode_header_codec_gate": rel(HEADER_CODEC_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_TAPE_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "residual_burden_cross_prediction_gate.v1",
        "scope": "analysis_only_leave_one_residual_field_out_prediction",
        "summary": {
            "book_count": len(rows),
            "promoted_targets": promoted,
            "target_summaries": {
                target: {
                    **result["summary"],
                    "beats_shuffled_p95": result["controls"]["beats_shuffled_p95"],
                    "shuffled_p95": result["controls"]["shuffled_p95"],
                }
                for target, result in target_results.items()
            },
            "weak_targets": weak,
        },
        "target_results": target_results,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Residual Burden Cross-Prediction Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether leave-one-field-out residual modes predict each held-out "
        "burden field after paying the mode header.",
        "",
        "## Summary",
        "",
        "| Target | Conditional saving before header | Header bits | Saving after header | Shuffled p95 | Beats p95 |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for target, data in result["target_results"].items():
        summary = data["summary"]
        controls = data["controls"]
        lines.append(
            f"| `{target}` | `{summary['conditional_saving_before_header']:.3f}` | "
            f"`{summary['header_bits']:.3f}` | `{summary['saving_after_header']:.3f}` | "
            f"`{controls['shuffled_p95']:.3f}` | `{controls['beats_shuffled_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Promotion requires positive saving after header and shuffled-target p95. "
            "Conditional savings before header are retained only as weak coupling "
            "diagnostics.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    lines = [
        "# Final Residual Burden Cross-Prediction Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Do the other residual burden fields predict each held-out burden field well "
        "enough to reduce that field after paying a leave-one-field-out mode header?",
        "",
        "## Result",
        "",
        f"Promoted targets: `{result['decision']['promoted_targets']}`. "
        f"Weak targets: `{result['decision']['weak_targets']}`.",
        "",
        "| Target | Before-header saving | After-header saving | Shuffled p95 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for target, data in result["target_results"].items():
        summary = data["summary"]
        controls = data["controls"]
        lines.append(
            f"| `{target}` | `{summary['conditional_saving_before_header']:.3f}` | "
            f"`{summary['saving_after_header']:.3f}` | `{controls['shuffled_p95']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This is not a generator and does not reduce exact executable tapes unless "
            "a target promotes after header cost. Row0, plaintext, translation, and "
            "compression_bound remain unchanged.",
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_residual_burden_cross_prediction_gate.py](../scripts/01_residual_burden_cross_prediction_gate.py)",
            "- [01_residual_burden_cross_prediction_gate.json](test_results/01_residual_burden_cross_prediction_gate.json)",
            "- [01_residual_burden_cross_prediction_gate.md](test_results/01_residual_burden_cross_prediction_gate.md)",
        ]
    )
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
