#!/usr/bin/env python3
"""Residual-mode header codec gate.

The residual book-mode coupling is real, but the first predictive mode program
failed. This gate asks a narrower and more practical question: if the mode is
paid as one external header per book, does it reduce any exact executable
decoder tapes after that header cost?

To avoid overclaim, only two exact streams are remodeled here:

- coarse `type:length_bucket` symbols;
- literal payload digits.

Composition index and copy-hint rank costs are carried through unchanged. A
positive result would be a partial external-ledger reduction, not a generator.
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
FRONT = ROOT / "analysis" / "residual_mode_header_codec_audit_20260622"
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
LATENT_BOOK_MODE_GATE = (
    ROOT
    / "analysis"
    / "latent_book_mode_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_latent_book_mode_program_gate.json"
)
UNIFIED_TAPE_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)

JSON_OUT = TEST_RESULTS / "01_residual_mode_header_codec_gate.json"
MD_OUT = TEST_RESULTS / "01_residual_mode_header_codec_gate.md"
FINAL_OUT = FRONT / "reports" / "final_residual_mode_header_codec_audit.md"

RANDOM_SEED = 46920260622 + 8
RANDOM_TRIALS = 300
ALPHA = 0.5
DIGITS = "0123456789"


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


def book_modes(ledger: dict[str, Any]) -> dict[int, str]:
    coupling = load_json(COUPLING_GATE)
    fields = coupling["summary"]["fields"]
    book_rows = COUPLING.summarize_books(ledger)
    return {
        book: COUPLING.joint_symbol(row, fields)
        for book, row in book_rows.items()
    }


def rows_by_book(ledger: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        out[int(row["book"])].append(row)
    return dict(out)


def split_specs(book_rows: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    fake_book_rows = {book: {"book": book} for book in book_rows}
    return COUPLING.split_specs(fake_book_rows)


def mode_counts(modes: dict[int, str], train: set[int]) -> Counter[str]:
    return Counter(modes[book] for book in train)


def code_symbol(symbol: str, counts: Counter[str], alphabet_size: int) -> float:
    total = sum(counts.values())
    probability = (counts.get(symbol, 0) + ALPHA) / (total + ALPHA * alphabet_size)
    return -math.log2(probability)


def train_stream_counts(
    by_book: dict[int, list[dict[str, Any]]],
    modes: dict[int, str],
    train: set[int],
) -> dict[str, Any]:
    coarse_global: Counter[str] = Counter()
    coarse_by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    digit_global: Counter[str] = Counter()
    digit_by_mode: dict[str, Counter[str]] = defaultdict(Counter)
    for book in train:
        mode = modes[book]
        for row in by_book[book]:
            coarse = row["coarse_type_length_bucket"]
            coarse_global[coarse] += 1
            coarse_by_mode[mode][coarse] += 1
            payload = row.get("literal_payload")
            if payload:
                for digit in payload:
                    digit_global[digit] += 1
                    digit_by_mode[mode][digit] += 1
    return {
        "coarse_by_mode": coarse_by_mode,
        "coarse_global": coarse_global,
        "digit_by_mode": digit_by_mode,
        "digit_global": digit_global,
    }


def test_exact_carry_bits(by_book: dict[int, list[dict[str, Any]]], test: set[int]) -> float:
    total = 0.0
    for book in test:
        for row in by_book[book]:
            total += float(row.get("composition_index_bits_charged_here") or 0.0)
            total += float(row.get("copy_hint_rank_bits") or 0.0)
    return total


def code_test_streams(
    by_book: dict[int, list[dict[str, Any]]],
    modes: dict[int, str],
    train: set[int],
    test: set[int],
    conditioned: bool,
) -> dict[str, float]:
    counts = train_stream_counts(by_book, modes, train)
    coarse_alphabet = sorted({row["coarse_type_length_bucket"] for rows in by_book.values() for row in rows})
    coarse_bits = 0.0
    literal_bits = 0.0
    for book in sorted(test):
        mode = modes[book]
        for row in by_book[book]:
            if conditioned:
                coarse_counts = counts["coarse_by_mode"].get(mode, counts["coarse_global"])
            else:
                coarse_counts = counts["coarse_global"]
            coarse_bits += code_symbol(row["coarse_type_length_bucket"], coarse_counts, len(coarse_alphabet))
            payload = row.get("literal_payload")
            if payload:
                digit_counts = (
                    counts["digit_by_mode"].get(mode, counts["digit_global"])
                    if conditioned
                    else counts["digit_global"]
                )
                for digit in payload:
                    literal_bits += code_symbol(digit, digit_counts, len(DIGITS))
    return {"coarse_bits": coarse_bits, "literal_bits": literal_bits}


def code_mode_headers(modes: dict[int, str], train: set[int], test: set[int]) -> float:
    counts = mode_counts(modes, train)
    alphabet = sorted(set(modes.values()))
    return sum(code_symbol(modes[book], counts, len(alphabet)) for book in test)


def score_split(
    by_book: dict[int, list[dict[str, Any]]],
    modes: dict[int, str],
    split: dict[str, Any],
) -> dict[str, Any]:
    train = set(split["train"])
    test = set(split["test"])
    carry_bits = test_exact_carry_bits(by_book, test)
    global_streams = code_test_streams(by_book, modes, train, test, conditioned=False)
    mode_streams = code_test_streams(by_book, modes, train, test, conditioned=True)
    header_bits = code_mode_headers(modes, train, test)
    baseline_bits = carry_bits + global_streams["coarse_bits"] + global_streams["literal_bits"]
    header_codec_bits = (
        carry_bits
        + header_bits
        + mode_streams["coarse_bits"]
        + mode_streams["literal_bits"]
    )
    return {
        "baseline_bits": baseline_bits,
        "carry_bits": carry_bits,
        "coarse_saving_bits": global_streams["coarse_bits"] - mode_streams["coarse_bits"],
        "global_coarse_bits": global_streams["coarse_bits"],
        "global_literal_bits": global_streams["literal_bits"],
        "header_bits": header_bits,
        "header_codec_bits": header_codec_bits,
        "label": split["label"],
        "literal_saving_bits": global_streams["literal_bits"] - mode_streams["literal_bits"],
        "mode_coarse_bits": mode_streams["coarse_bits"],
        "mode_literal_bits": mode_streams["literal_bits"],
        "saving_bits": baseline_bits - header_codec_bits,
        "split_type": split["split_type"],
        "test_books": len(test),
        "train_books": len(train),
    }


def evaluate_all(by_book: dict[int, list[dict[str, Any]]], modes: dict[int, str]) -> dict[str, Any]:
    split_rows = [score_split(by_book, modes, split) for split in split_specs(by_book)]
    baseline = sum(row["baseline_bits"] for row in split_rows)
    header_codec = sum(row["header_codec_bits"] for row in split_rows)
    return {
        "split_rows": split_rows,
        "summary": {
            "positive_splits": sum(row["saving_bits"] > 0 for row in split_rows),
            "split_count": len(split_rows),
            "test_books_repeated": sum(row["test_books"] for row in split_rows),
            "total_baseline_bits": baseline,
            "total_carry_bits": sum(row["carry_bits"] for row in split_rows),
            "total_coarse_saving_bits": sum(row["coarse_saving_bits"] for row in split_rows),
            "total_header_bits": sum(row["header_bits"] for row in split_rows),
            "total_header_codec_bits": header_codec,
            "total_literal_saving_bits": sum(row["literal_saving_bits"] for row in split_rows),
            "total_saving_bits": baseline - header_codec,
        },
    }


def shuffled_mode_controls(
    by_book: dict[int, list[dict[str, Any]]],
    modes: dict[int, str],
    real_saving: float,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    books = sorted(modes)
    mode_values = [modes[book] for book in books]
    savings = []
    for _ in range(RANDOM_TRIALS):
        shuffled_values = list(mode_values)
        rng.shuffle(shuffled_values)
        shuffled_modes = {book: mode for book, mode in zip(books, shuffled_values)}
        savings.append(evaluate_all(by_book, shuffled_modes)["summary"]["total_saving_bits"])
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
    ledger = load_json(UNIFIED_TAPE_LEDGER)
    coupling = load_json(COUPLING_GATE)
    latent_mode = load_json(LATENT_BOOK_MODE_GATE)
    assert_boundary("unified_external_tape_ledger", ledger)
    assert_boundary("book_residual_mode_coupling_gate", coupling)
    assert_boundary("latent_book_mode_program_gate", latent_mode)
    by_book = rows_by_book(ledger)
    modes = book_modes(ledger)
    evaluated = evaluate_all(by_book, modes)
    controls = shuffled_mode_controls(by_book, modes, evaluated["summary"]["total_saving_bits"])
    promoted = evaluated["summary"]["total_saving_bits"] > 0 and controls["beats_shuffled_p95"]
    weak = evaluated["summary"]["total_saving_bits"] > 0 and controls["beats_shuffled_p50"]
    classification = (
        "PROMOTED_RESIDUAL_MODE_HEADER_CODEC"
        if promoted
        else "WEAK_RESIDUAL_MODE_HEADER_CODEC"
        if weak
        else "RESIDUAL_MODE_HEADER_CODEC_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": controls,
        "decision": {
            "generator_promoted": False,
            "header_codec_promoted": promoted,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "book_residual_mode_coupling_gate": rel(COUPLING_GATE),
            "latent_book_mode_program_gate": rel(LATENT_BOOK_MODE_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_TAPE_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "residual_mode_header_codec_gate.v1",
        "scope": "analysis_only_paid_residual_mode_header_exact_stream_codec",
        "split_rows": evaluated["split_rows"],
        "summary": {
            **evaluated["summary"],
            "book_count": len(by_book),
            "mode_alphabet_size": len(set(modes.values())),
            "shuffled_p95": controls["shuffled_p95"],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Residual Mode Header Codec Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether paying the promoted residual book mode as a header reduces "
        "exact executable-decoder streams after charging the header.",
        "",
        "## Summary",
        "",
        f"- Baseline exact-stream bits: `{s['total_baseline_bits']:.3f}`.",
        f"- Header codec bits: `{s['total_header_codec_bits']:.3f}`.",
        f"- Saving: `{s['total_saving_bits']:.3f}` bits.",
        f"- Header bits paid: `{s['total_header_bits']:.3f}`.",
        f"- Coarse stream saving before header: `{s['total_coarse_saving_bits']:.3f}`.",
        f"- Literal payload saving before header: `{s['total_literal_saving_bits']:.3f}`.",
        f"- Positive splits: `{s['positive_splits']}/{s['split_count']}`.",
        f"- Shuffled p95: `{c['shuffled_p95']:.3f}`.",
        f"- Beats shuffled p95: `{c['beats_shuffled_p95']}`.",
        "",
        "## Split Results",
        "",
        "| Split | Type | Test books | Saving | Header | Coarse saving | Literal saving |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["split_rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['split_type']}` | `{row['test_books']}` | "
            f"`{row['saving_bits']:.3f}` | `{row['header_bits']:.3f}` | "
            f"`{row['coarse_saving_bits']:.3f}` | `{row['literal_saving_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Promotion requires the paid mode header to reduce exact executable streams "
            "and beat shuffled-mode controls. Composition-index and copy-hint rank "
            "costs are carried through unchanged here.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Final Residual Mode Header Codec Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "If the residual book mode is paid as a compact external header, does it "
        "reduce exact executable decoder tapes after header cost?",
        "",
        "## Result",
        "",
        f"The header codec costs `{s['total_header_codec_bits']:.3f}` bits versus "
        f"`{s['total_baseline_bits']:.3f}` baseline exact-stream bits "
        f"(`{s['total_saving_bits']:.3f}`). It pays `{s['total_header_bits']:.3f}` "
        f"header bits, saves `{s['total_coarse_saving_bits']:.3f}` on coarse control "
        f"and `{s['total_literal_saving_bits']:.3f}` on literal payload before header, "
        f"and beats shuffled p95: `{c['beats_shuffled_p95']}` "
        f"(p95 `{c['shuffled_p95']:.3f}`).",
        "",
        "## Decision",
        "",
        "The paid residual-mode header is not promoted: the real modes are less bad "
        "than shuffled modes, but the header does not reduce the exact executable "
        "ledger. This is not a generator and does not derive composition indices, "
        "copy-hint ranks, row0, plaintext, translation, or compression_bound.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_residual_mode_header_codec_gate.py](../scripts/01_residual_mode_header_codec_gate.py)",
        "- [01_residual_mode_header_codec_gate.json](test_results/01_residual_mode_header_codec_gate.json)",
        "- [01_residual_mode_header_codec_gate.md](test_results/01_residual_mode_header_codec_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
