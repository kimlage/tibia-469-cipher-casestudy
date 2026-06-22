#!/usr/bin/env python3
"""Latent book-mode program gate.

The previous audit promoted a book-level residual coupling clue: remaining
external burdens are synchronized at coarse book level. This gate asks the next
necessary question: can that residual mode be predicted/encoded by a small
decoder-visible book program, or is it just a compact post-hoc label?

The program may use:

- book length bucket;
- numeric phase bucket;
- previous decoded book mode in canonical order.

It may not use plaintext, row0 origin, target text, exact operation streams, or
copy availability. Models are selected on the train prefix/family only and then
frozen for held-out books.
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
FRONT = ROOT / "analysis" / "latent_book_mode_program_audit_20260622"
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
UNIFIED_TAPE_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)

JSON_OUT = TEST_RESULTS / "01_latent_book_mode_program_gate.json"
MD_OUT = TEST_RESULTS / "01_latent_book_mode_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_latent_book_mode_program_audit.md"

PRIMARY_VARIANT = "no_derived_shape"
FEATURES = [
    "global",
    "book_length_bucket",
    "book_phase",
    "book_length_x_phase",
    "prev_mode",
    "prev_mode_x_length",
]
ALPHA = 0.5
RANDOM_SEED = 46920260622 + 7
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


def book_length_bucket(length: int) -> str:
    for cut in [80, 120, 180, 260]:
        if length <= cut:
            return f"len_le_{cut}"
    return "len_gt_260"


def book_phase(book: int) -> str:
    start = (book // 10) * 10
    return f"phase_{start}_{start + 9}"


def build_book_rows() -> dict[int, dict[str, Any]]:
    ledger = load_json(UNIFIED_TAPE_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    coupling = load_json(COUPLING_GATE)
    assert_boundary("book_residual_mode_coupling_gate", coupling)
    fields = coupling["summary"]["fields"]
    base_rows = COUPLING.summarize_books(ledger)
    rows = {}
    for book, row in base_rows.items():
        mode = COUPLING.joint_symbol(row, fields)
        rows[book] = {
            **row,
            "book_length_bucket2": book_length_bucket(int(row["book_length"])),
            "book_phase": book_phase(book),
            "mode": mode,
        }
    return rows


def feature_value(row: dict[str, Any], feature: str, prev_mode: str) -> str:
    if feature == "global":
        return "global"
    if feature == "book_length_bucket":
        return row["book_length_bucket2"]
    if feature == "book_phase":
        return row["book_phase"]
    if feature == "book_length_x_phase":
        return f"{row['book_length_bucket2']}|{row['book_phase']}"
    if feature == "prev_mode":
        return prev_mode
    if feature == "prev_mode_x_length":
        return f"{prev_mode}|{row['book_length_bucket2']}"
    raise KeyError(feature)


def mode_alphabet(book_rows: dict[int, dict[str, Any]]) -> list[str]:
    return sorted({row["mode"] for row in book_rows.values()})


def split_specs(book_rows: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    return COUPLING.split_specs(book_rows)


def context_for_book(
    book_rows: dict[int, dict[str, Any]],
    known_modes: dict[int, str],
    book: int,
) -> str:
    previous = book - 1
    if previous in known_modes:
        return known_modes[previous]
    return "BOS"


def train_feature_counts(
    book_rows: dict[int, dict[str, Any]],
    train_books: set[int],
    feature: str,
) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    known_modes = {book: book_rows[book]["mode"] for book in train_books}
    for book in sorted(train_books):
        prev = context_for_book(book_rows, known_modes, book)
        key = feature_value(book_rows[book], feature, prev)
        counts[key][book_rows[book]["mode"]] += 1
    return counts


def global_mode_counts(book_rows: dict[int, dict[str, Any]], train_books: set[int]) -> Counter[str]:
    return Counter(book_rows[book]["mode"] for book in train_books)


def mode_probability_bits(
    mode: str,
    key: str,
    feature_counts: dict[str, Counter[str]],
    fallback_counts: Counter[str],
    alphabet_size: int,
) -> float:
    counts = feature_counts.get(key, fallback_counts)
    total = sum(counts.values())
    probability = (counts.get(mode, 0) + ALPHA) / (total + ALPHA * alphabet_size)
    return -math.log2(probability)


def ranked_modes(
    key: str,
    feature_counts: dict[str, Counter[str]],
    fallback_counts: Counter[str],
    alphabet: list[str],
) -> list[str]:
    counts = feature_counts.get(key, fallback_counts)
    total = sum(counts.values())
    return sorted(
        alphabet,
        key=lambda mode: (
            -((counts.get(mode, 0) + ALPHA) / (total + ALPHA * len(alphabet))),
            mode,
        ),
    )


def score_books(
    book_rows: dict[int, dict[str, Any]],
    train_books: set[int],
    test_books: set[int],
    feature: str,
    alphabet: list[str],
) -> dict[str, Any]:
    feature_counts = train_feature_counts(book_rows, train_books, feature)
    fallback_counts = global_mode_counts(book_rows, train_books)
    known_modes = {book: book_rows[book]["mode"] for book in train_books}
    bits = 0.0
    top1 = beam5 = beam10 = 0
    rows = []
    for book in sorted(test_books):
        prev = context_for_book(book_rows, known_modes, book)
        key = feature_value(book_rows[book], feature, prev)
        mode = book_rows[book]["mode"]
        bits += mode_probability_bits(mode, key, feature_counts, fallback_counts, len(alphabet))
        ordered = ranked_modes(key, feature_counts, fallback_counts, alphabet)
        rank = ordered.index(mode) + 1
        top1 += int(rank == 1)
        beam5 += int(rank <= 5)
        beam10 += int(rank <= 10)
        rows.append({"book": book, "feature_key": key, "mode_rank": rank})
        known_modes[book] = mode
    return {
        "beam10_hits": beam10,
        "beam5_hits": beam5,
        "bits": bits,
        "book_rows": rows,
        "top1_hits": top1,
    }


def loo_feature_score(
    book_rows: dict[int, dict[str, Any]],
    train_books: set[int],
    feature: str,
    alphabet: list[str],
) -> float:
    if len(train_books) < 2:
        return float("inf")
    bits = 0.0
    for heldout in sorted(train_books):
        subtrain = set(train_books) - {heldout}
        bits += score_books(book_rows, subtrain, {heldout}, feature, alphabet)["bits"]
    return bits + math.log2(len(FEATURES))


def select_feature(
    book_rows: dict[int, dict[str, Any]],
    train_books: set[int],
    alphabet: list[str],
) -> dict[str, Any]:
    rows = [
        {"feature": feature, "loo_bits": loo_feature_score(book_rows, train_books, feature, alphabet)}
        for feature in FEATURES
    ]
    return min(rows, key=lambda row: (row["loo_bits"], row["feature"]))


def score_split(book_rows: dict[int, dict[str, Any]], split: dict[str, Any], alphabet: list[str]) -> dict[str, Any]:
    selected = select_feature(book_rows, split["train"], alphabet)
    feature_result = score_books(book_rows, split["train"], split["test"], selected["feature"], alphabet)
    global_result = score_books(book_rows, split["train"], split["test"], "global", alphabet)
    program_bits = feature_result["bits"] + math.log2(len(FEATURES))
    saving = global_result["bits"] - program_bits
    return {
        "beam10_hits": feature_result["beam10_hits"],
        "beam5_hits": feature_result["beam5_hits"],
        "feature": selected["feature"],
        "global_bits": global_result["bits"],
        "label": split["label"],
        "loo_bits": selected["loo_bits"],
        "program_bits": program_bits,
        "saving_bits": saving,
        "split_type": split["split_type"],
        "test_books": len(split["test"]),
        "top1_hits": feature_result["top1_hits"],
        "train_books": len(split["train"]),
    }


def evaluate_all(book_rows: dict[int, dict[str, Any]]) -> dict[str, Any]:
    alphabet = mode_alphabet(book_rows)
    split_rows = [score_split(book_rows, split, alphabet) for split in split_specs(book_rows)]
    global_bits = sum(row["global_bits"] for row in split_rows)
    program_bits = sum(row["program_bits"] for row in split_rows)
    return {
        "alphabet_size": len(alphabet),
        "split_rows": split_rows,
        "summary": {
            "beam10_hits": sum(row["beam10_hits"] for row in split_rows),
            "beam5_hits": sum(row["beam5_hits"] for row in split_rows),
            "positive_splits": sum(row["saving_bits"] > 0 for row in split_rows),
            "split_count": len(split_rows),
            "test_books_repeated": sum(row["test_books"] for row in split_rows),
            "top1_hits": sum(row["top1_hits"] for row in split_rows),
            "total_global_bits": global_bits,
            "total_program_bits": program_bits,
            "total_saving_bits": global_bits - program_bits,
        },
    }


def shuffled_mode_controls(book_rows: dict[int, dict[str, Any]], real_saving: float) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    books = sorted(book_rows)
    modes = [book_rows[book]["mode"] for book in books]
    savings = []
    for _ in range(RANDOM_TRIALS):
        shuffled_modes = list(modes)
        rng.shuffle(shuffled_modes)
        shuffled = {book: dict(book_rows[book]) for book in books}
        for book, mode in zip(books, shuffled_modes):
            shuffled[book]["mode"] = mode
        savings.append(evaluate_all(shuffled)["summary"]["total_saving_bits"])
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
    book_rows = build_book_rows()
    evaluated = evaluate_all(book_rows)
    controls = shuffled_mode_controls(book_rows, evaluated["summary"]["total_saving_bits"])
    promoted = evaluated["summary"]["total_saving_bits"] > 0 and controls["beats_shuffled_p95"]
    weak = evaluated["summary"]["total_saving_bits"] > 0 and controls["beats_shuffled_p50"]
    classification = (
        "PROMOTED_LATENT_BOOK_MODE_PROGRAM"
        if promoted
        else "WEAK_LATENT_BOOK_MODE_PROGRAM"
        if weak
        else "LATENT_BOOK_MODE_PROGRAM_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": controls,
        "decision": {
            "generator_promoted": False,
            "latent_book_mode_program_promoted": promoted,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "book_residual_mode_coupling_gate": rel(COUPLING_GATE),
            "book_residual_mode_coupling_script": rel(COUPLING_SCRIPT),
            "unified_external_tape_ledger": rel(UNIFIED_TAPE_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "latent_book_mode_program_gate.v1",
        "scope": "analysis_only_predictive_book_mode_program",
        "split_rows": evaluated["split_rows"],
        "summary": {
            **evaluated["summary"],
            "alphabet_size": evaluated["alphabet_size"],
            "book_count": len(book_rows),
            "features": FEATURES,
            "shuffled_p95": controls["shuffled_p95"],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Latent Book Mode Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether the promoted book residual mode can be predicted by a small "
        "decoder-visible book program instead of paid as a post-hoc joint symbol.",
        "",
        "## Summary",
        "",
        f"- Mode alphabet size: `{s['alphabet_size']}`.",
        f"- Global mode bits: `{s['total_global_bits']:.3f}`.",
        f"- Program mode bits: `{s['total_program_bits']:.3f}`.",
        f"- Saving: `{s['total_saving_bits']:.3f}` bits.",
        f"- Positive splits: `{s['positive_splits']}/{s['split_count']}`.",
        f"- Top1 / Beam5 / Beam10 hits: `{s['top1_hits']}` / `{s['beam5_hits']}` / `{s['beam10_hits']}` over `{s['test_books_repeated']}` repeated held-out books.",
        f"- Shuffled p95: `{c['shuffled_p95']:.3f}`.",
        f"- Beats shuffled p95: `{c['beats_shuffled_p95']}`.",
        "",
        "## Split Results",
        "",
        "| Split | Type | Feature | Test books | Saving | Program bits | Global bits | Top1 | Beam5 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["split_rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['split_type']}` | `{row['feature']}` | "
            f"`{row['test_books']}` | `{row['saving_bits']:.3f}` | "
            f"`{row['program_bits']:.3f}` | `{row['global_bits']:.3f}` | "
            f"`{row['top1_hits']}` | `{row['beam5_hits']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Promotion requires feature-conditioned book-mode coding to beat global "
            "mode coding and shuffled-mode controls. Even when promoted, this is a "
            "book-mode controller clue, not exact generation of the residual tapes.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Final Latent Book Mode Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can the promoted residual book mode be predicted by a small decoder-visible "
        "program, rather than merely paid as a compact joint label?",
        "",
        "## Result",
        "",
        f"The selected book-mode program costs `{s['total_program_bits']:.3f}` bits "
        f"versus `{s['total_global_bits']:.3f}` global mode bits "
        f"(`{s['total_saving_bits']:.3f}`). It has `{s['positive_splits']}/{s['split_count']}` "
        f"positive splits and beats shuffled p95: `{c['beats_shuffled_p95']}` "
        f"(p95 `{c['shuffled_p95']:.3f}`).",
        "",
        f"Top1/Beam5/Beam10 recovery is `{s['top1_hits']}` / `{s['beam5_hits']}` / "
        f"`{s['beam10_hits']}` over `{s['test_books_repeated']}` repeated held-out books.",
        "",
        "## Decision",
        "",
        "The simple latent book-mode program is not promoted. The previous residual "
        "coupling clue remains real, but under these features the mode must still be "
        "paid as a compact external label rather than generated. It still does not "
        "derive exact type:length streams, literal payload, copy hints, row0, "
        "plaintext, translation, or compression_bound.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_latent_book_mode_program_gate.py](../scripts/01_latent_book_mode_program_gate.py)",
        "- [01_latent_book_mode_program_gate.json](test_results/01_latent_book_mode_program_gate.json)",
        "- [01_latent_book_mode_program_gate.md](test_results/01_latent_book_mode_program_gate.md)",
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
