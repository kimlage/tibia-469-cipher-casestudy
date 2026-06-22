#!/usr/bin/env python3
"""Schedule-state multistream pilot.

The previous latent HMM pilot found a strong multistream compression clue but
failed same-multiset order controls. This gate asks whether that clue can be
anchored to visible schedule states instead of a hidden/post-hoc state.

Promotion is deliberately strict:

- train only on prefix books, then score suffix books;
- select decoder-visible schedule families using training MDL only;
- compare against factorized stream coding and same-book shuffled controls;
- keep diagnostic-conditioned states separate because they grant exact
  skeleton/target-position information.

No plaintext, semantics, row0-origin, or compression-bound claim is made here.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "schedule_state_multistream_pilot_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

CONTROL_LEDGER = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
LATENT_HMM = (
    ROOT
    / "analysis"
    / "latent_nonlocal_state_program_pilot_audit_20260622"
    / "reports"
    / "test_results"
    / "01_latent_nonlocal_state_program_pilot.json"
)

JSON_OUT = TEST_RESULTS / "01_schedule_state_multistream_pilot.json"
MD_OUT = TEST_RESULTS / "01_schedule_state_multistream_pilot.md"
FINAL_OUT = FRONT / "reports" / "final_schedule_state_multistream_pilot_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
ALPHA = 0.5
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def numeric_bucket(value: int, cuts: list[int], prefix: str) -> str:
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut:04d}"
    return f"{prefix}_gt_{cuts[-1]:04d}"


def fraction_bucket(value: float | None, bins: int, prefix: str) -> str:
    if value is None:
        return f"{prefix}_none"
    index = min(bins - 1, max(0, int(value * bins)))
    return f"{prefix}_q{index:02d}"


def occ_bucket(value: int | None) -> str:
    if value is None:
        return "occ_none"
    if value <= 1:
        return "occ_1"
    if value <= 3:
        return "occ_2_3"
    return "occ_4p"


def literal_tape_bucket(row: dict[str, Any], max_tape_end: int) -> str:
    start = row.get("literal_tape_start")
    if start is None:
        return "lit_tape_none"
    frac = start / max(1, max_tape_end)
    return fraction_bucket(frac, 6, "lit_tape")


def behavior_symbol(row: dict[str, Any], max_tape_end: int) -> str:
    if row["op_type"] == "literal":
        return f"lit:{row['length_bucket']}:{literal_tape_bucket(row, max_tape_end)}"
    rank_bucket = row.get("copy_hint_rank_bucket") or "rank_none"
    return f"copy:{row['length_bucket']}:{rank_bucket}:{occ_bucket(row.get('copy_hint_source_occurrences'))}"


def family_scope(family: str) -> str:
    diagnostic = {"remaining_bucket", "target_fraction", "phase_remaining", "booklen_remaining"}
    return "diagnostic_conditioned" if family in diagnostic else "decoder_visible"


def load_rows() -> dict[int, list[dict[str, Any]]]:
    ledger = load_json(CONTROL_LEDGER)
    assert_boundary("unified_residual_control_ledger", ledger)
    max_tape_end = max(
        int(row["literal_tape_end"])
        for row in ledger["ledger_rows"]
        if row.get("literal_tape_end") is not None
    )
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for raw in ledger["ledger_rows"]:
        row = dict(raw)
        book_length = int(row["book_length"])
        target_start = int(row["target_start"])
        remaining = int(row["remaining_before_op"])
        row["control_symbol"] = row["type_length_symbol"]
        row["behavior_symbol"] = behavior_symbol(row, max_tape_end)
        row["joint_token"] = f"{row['control_symbol']}|{row['behavior_symbol']}"
        row["book_length_bucket"] = numeric_bucket(book_length, [80, 120, 180, 260], "booklen")
        row["remaining_bucket"] = fraction_bucket(remaining / max(1, book_length), 6, "rem")
        row["target_fraction"] = fraction_bucket(target_start / max(1, book_length), 6, "target")
        grouped[int(row["book"])].append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }


def schedule_key(row: dict[str, Any], family: str) -> str:
    if family == "global":
        return "global"
    if family == "op_pos":
        return row["op_pos_bucket"]
    if family == "book_phase":
        return row["book_phase"]
    if family == "booklen":
        return row["book_length_bucket"]
    if family == "phase_op_pos":
        return f"{row['book_phase']}|{row['op_pos_bucket']}"
    if family == "booklen_op_pos":
        return f"{row['book_length_bucket']}|{row['op_pos_bucket']}"
    if family == "remaining_bucket":
        return row["remaining_bucket"]
    if family == "target_fraction":
        return row["target_fraction"]
    if family == "phase_remaining":
        return f"{row['book_phase']}|{row['remaining_bucket']}"
    if family == "booklen_remaining":
        return f"{row['book_length_bucket']}|{row['remaining_bucket']}"
    raise KeyError(family)


FAMILIES = [
    "global",
    "op_pos",
    "book_phase",
    "booklen",
    "phase_op_pos",
    "booklen_op_pos",
    "remaining_bucket",
    "target_fraction",
    "phase_remaining",
    "booklen_remaining",
]


def train_counts(rows_by_book: dict[int, list[dict[str, Any]]], books: list[int], family: str, field: str) -> tuple[dict[str, Counter[str]], set[str], set[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    states: set[str] = set()
    vocab: set[str] = set()
    for book in books:
        for row in rows_by_book[book]:
            state = schedule_key(row, family)
            token = row[field]
            counts[state][token] += 1
            states.add(state)
            vocab.add(token)
    return counts, states, vocab


def score_counts(
    rows_by_book: dict[int, list[dict[str, Any]]],
    books: list[int],
    family: str,
    field: str,
    counts: dict[str, Counter[str]],
    train_states: set[str],
    global_vocab: set[str],
) -> float:
    global_counts = Counter()
    for counter in counts.values():
        global_counts.update(counter)
    global_total = sum(global_counts.values())
    vocab_size = max(1, len(global_vocab))
    bits = 0.0
    for book in books:
        for row in rows_by_book[book]:
            state = schedule_key(row, family)
            token = row[field]
            counter = counts.get(state)
            if counter:
                total = sum(counter.values())
                prob = (counter.get(token, 0) + ALPHA) / (total + ALPHA * vocab_size)
            else:
                # Unseen schedule state: fall back to the prefix global model.
                prob = (global_counts.get(token, 0) + ALPHA) / (
                    global_total + ALPHA * vocab_size
                )
            bits += -math.log2(prob)
    return bits


def model_bits(
    rows_by_book: dict[int, list[dict[str, Any]]],
    train_books: list[int],
    score_books: list[int],
    family: str,
    field: str,
    global_vocab: set[str],
) -> tuple[float, int, int]:
    counts, states, _ = train_counts(rows_by_book, train_books, family, field)
    bits = score_counts(rows_by_book, score_books, family, field, counts, states, global_vocab)
    return bits, len(states), sum(len(counter) for counter in counts.values())


def field_vocab(rows_by_book: dict[int, list[dict[str, Any]]], field: str) -> set[str]:
    return {row[field] for rows in rows_by_book.values() for row in rows}


def descriptor_penalty(states: int, populated_cells: int, family_count: int) -> float:
    # Conservative MDL-style penalty for selecting a family plus populated
    # state/token cells. It is only used for train-time model selection.
    return math.log2(family_count) + states + 0.25 * populated_cells


def factorized_bits(
    rows_by_book: dict[int, list[dict[str, Any]]],
    train_books: list[int],
    score_books: list[int],
) -> float:
    total = 0.0
    for field in ["control_symbol", "behavior_symbol"]:
        vocab = field_vocab(rows_by_book, field)
        bits, _, _ = model_bits(rows_by_book, train_books, score_books, "global", field, vocab)
        total += bits
    return total


def same_book_shuffle_controls(
    rows_by_book: dict[int, list[dict[str, Any]]],
    train_books: list[int],
    test_books: list[int],
    family: str,
    global_vocab: set[str],
    seed_offset: int,
) -> dict[str, Any]:
    counts, states, _ = train_counts(rows_by_book, train_books, family, "joint_token")
    rng = random.Random(RANDOM_SEED + seed_offset)
    bits: list[float] = []
    for _ in range(RANDOM_TRIALS):
        shuffled: dict[int, list[dict[str, Any]]] = {book: [dict(row) for row in rows] for book, rows in rows_by_book.items()}
        for book in test_books:
            tokens = [row["joint_token"] for row in rows_by_book[book]]
            rng.shuffle(tokens)
            for row, token in zip(shuffled[book], tokens):
                row["joint_token"] = token
        bits.append(score_counts(shuffled, test_books, family, "joint_token", counts, states, global_vocab))
    ordered = sorted(bits)
    def pct(p: float) -> float:
        index = min(len(ordered) - 1, max(0, math.ceil(p / 100.0 * len(ordered)) - 1))
        return ordered[index]
    return {
        "bits_mean": sum(bits) / len(bits),
        "bits_p05": pct(5),
        "bits_p50": pct(50),
        "bits_p95": pct(95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def cutoff_gate(cutoff: int, rows_by_book: dict[int, list[dict[str, Any]]], seed_offset: int) -> dict[str, Any]:
    books = sorted(rows_by_book)
    train_books = [book for book in books if book < cutoff]
    test_books = [book for book in books if book >= cutoff]
    family_count = len([family for family in FAMILIES if family_scope(family) == "decoder_visible"])
    joint_vocab = field_vocab(rows_by_book, "joint_token")
    joint_unigram_bits, _, _ = model_bits(rows_by_book, train_books, test_books, "global", "joint_token", joint_vocab)
    baseline_factorized_bits = factorized_bits(rows_by_book, train_books, test_books)

    family_rows = []
    for family in FAMILIES:
        joint_train, states, cells = model_bits(rows_by_book, train_books, train_books, family, "joint_token", joint_vocab)
        joint_test, _, _ = model_bits(rows_by_book, train_books, test_books, family, "joint_token", joint_vocab)
        schedule_factorized_test = 0.0
        for field in ["control_symbol", "behavior_symbol"]:
            vocab = field_vocab(rows_by_book, field)
            bits, _, _ = model_bits(rows_by_book, train_books, test_books, family, field, vocab)
            schedule_factorized_test += bits
        controls = same_book_shuffle_controls(
            rows_by_book, train_books, test_books, family, joint_vocab, seed_offset * 100 + FAMILIES.index(family)
        )
        family_rows.append(
            {
                "family": family,
                "scope": family_scope(family),
                "states": states,
                "populated_cells": cells,
                "train_joint_bits": joint_train,
                "train_selection_mdl": joint_train + descriptor_penalty(states, cells, family_count),
                "test_joint_bits": joint_test,
                "test_delta_vs_factorized": joint_test - baseline_factorized_bits,
                "test_delta_vs_joint_unigram": joint_test - joint_unigram_bits,
                "test_delta_vs_schedule_factorized": joint_test - schedule_factorized_test,
                "beats_factorized": joint_test < baseline_factorized_bits,
                "beats_joint_unigram": joint_test < joint_unigram_bits,
                "beats_shuffle_p05": joint_test < controls["bits_p05"],
                "same_book_shuffle": controls,
            }
        )

    decoder_rows = [row for row in family_rows if row["scope"] == "decoder_visible"]
    selected = min(decoder_rows, key=lambda row: (row["train_selection_mdl"], row["states"], row["family"]))
    diagnostic_best = min(
        [row for row in family_rows if row["scope"] == "diagnostic_conditioned"],
        key=lambda row: row["test_joint_bits"],
    )
    return {
        "cutoff": cutoff,
        "train_books": train_books,
        "test_books": test_books,
        "train_ops": sum(len(rows_by_book[book]) for book in train_books),
        "test_ops": sum(len(rows_by_book[book]) for book in test_books),
        "baseline_factorized_bits": baseline_factorized_bits,
        "joint_unigram_bits": joint_unigram_bits,
        "selected_decoder_visible": selected,
        "best_diagnostic_conditioned": diagnostic_best,
        "family_rows": family_rows,
    }


def make_result() -> dict[str, Any]:
    hmm = load_json(LATENT_HMM)
    assert_boundary("latent_nonlocal_state_program_pilot", hmm)
    rows_by_book = load_rows()
    cutoff_rows = [
        cutoff_gate(cutoff, rows_by_book, seed_offset=index)
        for index, cutoff in enumerate(CUTOFFS)
    ]
    selected_rows = [row["selected_decoder_visible"] for row in cutoff_rows]
    total_schedule = sum(row["test_joint_bits"] for row in selected_rows)
    total_factorized = sum(row["baseline_factorized_bits"] for row in cutoff_rows)
    total_unigram = sum(row["joint_unigram_bits"] for row in cutoff_rows)
    beats_factorized = sum(row["beats_factorized"] for row in selected_rows)
    beats_unigram = sum(row["beats_joint_unigram"] for row in selected_rows)
    beats_shuffle = sum(row["beats_shuffle_p05"] for row in selected_rows)

    promoted = (
        total_schedule < total_factorized
        and beats_factorized >= 4
        and beats_unigram >= 4
        and beats_shuffle >= 4
    )
    weak_clue = total_schedule < total_factorized and beats_factorized >= 4
    classification = (
        "PROMOTED_SCHEDULE_STATE_MULTISTREAM_CLUE"
        if promoted
        else "SCHEDULE_STATE_MULTISTREAM_CLUE_NOT_GENERATOR"
        if weak_clue
        else "REJECTED_SCHEDULE_STATE_MULTISTREAM_ROUTE"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "cutoff_rows": cutoff_rows,
        "decision": {
            "generator_promoted": False,
            "row0_status": "unchanged_exogenous",
            "schedule_state_clue_promoted": promoted,
            "translation_delta": "NONE",
            "why_not_generator": (
                "decoder-visible schedule states must reduce factorized external streams "
                "and beat same-book shuffled controls in holdout; diagnostic-conditioned "
                "states grant skeleton/target-position information and cannot promote a generator"
            ),
        },
        "inputs": {
            "latent_nonlocal_state_program_pilot": rel(LATENT_HMM),
            "unified_residual_control_ledger": rel(CONTROL_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "schedule_state_multistream_pilot.v1",
        "scope": "analysis_only_schedule_conditioned_multistream_external_ledger",
        "summary": {
            "beats_factorized_cells": beats_factorized,
            "beats_joint_unigram_cells": beats_unigram,
            "beats_shuffle_p05_cells": beats_shuffle,
            "cutoffs": CUTOFFS,
            "selected_decoder_visible_total_bits": total_schedule,
            "total_delta_vs_factorized": total_schedule - total_factorized,
            "total_delta_vs_joint_unigram": total_schedule - total_unigram,
            "total_factorized_bits": total_factorized,
            "total_joint_unigram_bits": total_unigram,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Schedule-State Multistream Pilot",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether the HMM multistream clue can be attached to visible schedule "
        "states rather than hidden order-sensitive state. Decoder-visible families "
        "are selected by prefix training only; diagnostic-conditioned families are "
        "reported separately and are not promotable as generators.",
        "",
        "## Summary",
        "",
        f"- Selected decoder-visible schedule bits: `{s['selected_decoder_visible_total_bits']:.3f}`.",
        f"- Factorized external stream bits: `{s['total_factorized_bits']:.3f}`.",
        f"- Delta vs factorized: `{s['total_delta_vs_factorized']:.3f}` bits.",
        f"- Delta vs joint unigram: `{s['total_delta_vs_joint_unigram']:.3f}` bits.",
        f"- Cells beating factorized: `{s['beats_factorized_cells']}/5`.",
        f"- Cells beating joint unigram: `{s['beats_joint_unigram_cells']}/5`.",
        f"- Cells beating same-book shuffled p05: `{s['beats_shuffle_p05_cells']}/5`.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | Selected family | Test ops | Schedule bits | Factorized bits | Delta | Beats shuffle p05 | Diagnostic best |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in result["cutoff_rows"]:
        selected = row["selected_decoder_visible"]
        diagnostic = row["best_diagnostic_conditioned"]
        lines.append(
            f"| `{row['cutoff']}` | `{selected['family']}` | `{row['test_ops']}` | "
            f"`{selected['test_joint_bits']:.3f}` | `{row['baseline_factorized_bits']:.3f}` | "
            f"`{selected['test_delta_vs_factorized']:.3f}` | "
            f"`{selected['beats_shuffle_p05']}` | "
            f"`{diagnostic['family']}:{diagnostic['test_joint_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This gate promotes only if decoder-visible schedule states reduce the "
            "external ledger under holdout and beat same-book shuffled controls. "
            "Diagnostic-conditioned wins are useful localization clues only, because "
            "they grant exact remaining/target-position structure.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Schedule-State Multistream Pilot Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can the HMM multistream signal be converted into a visible schedule-state "
        "program over the executable external ledger?",
        "",
        "## Result",
        "",
        f"The train-selected decoder-visible schedule models cost "
        f"`{s['selected_decoder_visible_total_bits']:.3f}` bits versus "
        f"`{s['total_factorized_bits']:.3f}` factorized bits "
        f"(`{s['total_delta_vs_factorized']:.3f}`). They beat factorized streams in "
        f"`{s['beats_factorized_cells']}/5` cells, joint unigram in "
        f"`{s['beats_joint_unigram_cells']}/5` cells, and same-book shuffled p05 in "
        f"`{s['beats_shuffle_p05_cells']}/5` cells.",
        "",
        "## Decision",
        "",
        "The result is a generator only if the schedule program reduces the external "
        "ledger and survives shuffled-order controls. Diagnostic-conditioned states "
        "are reported as localization clues, not as generation rules. Row0, "
        "plaintext, translation, and compression_bound remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_schedule_state_multistream_pilot.py](../scripts/01_schedule_state_multistream_pilot.py)",
        "- [01_schedule_state_multistream_pilot.json](test_results/01_schedule_state_multistream_pilot.json)",
        "- [01_schedule_state_multistream_pilot.md](test_results/01_schedule_state_multistream_pilot.md)",
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
