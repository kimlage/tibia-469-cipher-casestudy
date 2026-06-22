#!/usr/bin/env python3
"""Book multiset/order factorization gate.

The HMM and schedule-state pilots both reduced multistream coding cost but
failed same-book shuffle controls. That is a precise clue: the signal may be
book-level composition, not operation order. This gate decomposes the current
external operation stream into:

- a per-book multiset/count vector of joint operation tokens;
- an exact within-book order index given that multiset.

It then tests whether prefix-trained book metadata predicts the multiset above
permuted-feature controls. The order index is charged explicitly, so this gate
cannot silently promote a shuffled bag as a generator.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "book_multiset_order_factorization_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

CONTROL_LEDGER = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
SCHEDULE_PILOT = (
    ROOT
    / "analysis"
    / "schedule_state_multistream_pilot_audit_20260622"
    / "reports"
    / "test_results"
    / "01_schedule_state_multistream_pilot.json"
)

JSON_OUT = TEST_RESULTS / "01_book_multiset_order_factorization_gate.json"
MD_OUT = TEST_RESULTS / "01_book_multiset_order_factorization_gate.md"
FINAL_OUT = FRONT / "reports" / "final_book_multiset_order_factorization_audit.md"

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
    return fraction_bucket(start / max(1, max_tape_end), 6, "lit_tape")


def behavior_symbol(row: dict[str, Any], max_tape_end: int) -> str:
    if row["op_type"] == "literal":
        return f"lit:{row['length_bucket']}:{literal_tape_bucket(row, max_tape_end)}"
    rank_bucket = row.get("copy_hint_rank_bucket") or "rank_none"
    return f"copy:{row['length_bucket']}:{rank_bucket}:{occ_bucket(row.get('copy_hint_source_occurrences'))}"


def load_book_rows() -> dict[int, list[dict[str, Any]]]:
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
        row["control_symbol"] = row["type_length_symbol"]
        row["behavior_symbol"] = behavior_symbol(row, max_tape_end)
        row["joint_token"] = f"{row['control_symbol']}|{row['behavior_symbol']}"
        grouped[int(row["book"])].append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }


def book_summary(rows_by_book: dict[int, list[dict[str, Any]]]) -> dict[int, dict[str, Any]]:
    out = {}
    for book, rows in rows_by_book.items():
        book_length = int(rows[0]["book_length"])
        op_count = len(rows)
        literal_count = sum(row["op_type"] == "literal" for row in rows)
        copy_count = op_count - literal_count
        out[book] = {
            "book": book,
            "book_phase": rows[0]["book_phase"],
            "book_length": book_length,
            "book_length_bucket": numeric_bucket(book_length, [80, 120, 180, 260], "booklen"),
            "op_count": op_count,
            "op_count_bucket": numeric_bucket(op_count, [2, 4, 6, 8], "opcount"),
            "literal_count": literal_count,
            "literal_count_bucket": numeric_bucket(literal_count, [0, 1, 2, 3], "litcount"),
            "copy_count": copy_count,
            "joint_counts": Counter(row["joint_token"] for row in rows),
            "control_counts": Counter(row["control_symbol"] for row in rows),
            "behavior_counts": Counter(row["behavior_symbol"] for row in rows),
        }
    return out


def feature_value(summary: dict[str, Any], family: str) -> str:
    if family == "global":
        return "global"
    if family == "book_phase":
        return summary["book_phase"]
    if family == "book_length_bucket":
        return summary["book_length_bucket"]
    if family == "op_count_bucket":
        return summary["op_count_bucket"]
    if family == "literal_count_bucket":
        return summary["literal_count_bucket"]
    if family == "booklen_opcount":
        return f"{summary['book_length_bucket']}|{summary['op_count_bucket']}"
    if family == "phase_opcount":
        return f"{summary['book_phase']}|{summary['op_count_bucket']}"
    if family == "phase_litcount":
        return f"{summary['book_phase']}|{summary['literal_count_bucket']}"
    raise KeyError(family)


FAMILIES = [
    "global",
    "book_phase",
    "book_length_bucket",
    "op_count_bucket",
    "literal_count_bucket",
    "booklen_opcount",
    "phase_opcount",
    "phase_litcount",
]

GRANTED_FEATURES = {"op_count_bucket", "literal_count_bucket", "booklen_opcount", "phase_opcount", "phase_litcount"}


def log2_multinomial(counts: Counter[str]) -> float:
    total = sum(counts.values())
    value = math.lgamma(total + 1)
    for count in counts.values():
        value -= math.lgamma(count + 1)
    return value / math.log(2)


def train_state_counts(
    summaries: dict[int, dict[str, Any]],
    books: list[int],
    family: str,
    field: str,
    feature_override: dict[int, str] | None = None,
) -> dict[str, Counter[str]]:
    state_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for book in books:
        state = feature_override[book] if feature_override else feature_value(summaries[book], family)
        state_counts[state].update(summaries[book][field])
    return state_counts


def score_bag_bits(
    summaries: dict[int, dict[str, Any]],
    train_books: list[int],
    score_books: list[int],
    family: str,
    field: str,
    vocab: set[str],
    feature_override: dict[int, str] | None = None,
) -> tuple[float, float, float]:
    state_counts = train_state_counts(summaries, train_books, family, field, feature_override)
    global_counts = Counter()
    for counter in state_counts.values():
        global_counts.update(counter)
    global_total = sum(global_counts.values())
    vocab_size = max(1, len(vocab))
    bag_bits = 0.0
    order_bits = 0.0
    sequence_bits = 0.0
    for book in score_books:
        counts = summaries[book][field]
        state = feature_override[book] if feature_override else feature_value(summaries[book], family)
        probs = state_counts.get(state)
        if probs:
            total = sum(probs.values())
        else:
            probs = global_counts
            total = global_total
        coeff = log2_multinomial(counts)
        emission_bits = 0.0
        for token, count in counts.items():
            prob = (probs.get(token, 0) + ALPHA) / (total + ALPHA * vocab_size)
            emission_bits += -count * math.log2(prob)
        bag_bits += emission_bits - coeff
        order_bits += coeff
        sequence_bits += emission_bits
    return bag_bits, order_bits, sequence_bits


def descriptor_penalty(summaries: dict[int, dict[str, Any]], books: list[int], family: str, field: str) -> float:
    states = {feature_value(summaries[book], family) for book in books}
    cells = 0
    for state in states:
        tokens = set()
        for book in books:
            if feature_value(summaries[book], family) == state:
                tokens.update(summaries[book][field])
        cells += len(tokens)
    return math.log2(len(FAMILIES)) + len(states) + 0.25 * cells


def loo_train_score(summaries: dict[int, dict[str, Any]], books: list[int], family: str, field: str, vocab: set[str]) -> float:
    if len(books) < 2:
        return float("inf")
    total = 0.0
    for heldout in books:
        train = [book for book in books if book != heldout]
        bag, order, _ = score_bag_bits(summaries, train, [heldout], family, field, vocab)
        total += bag + order
    return total + descriptor_penalty(summaries, books, family, field)


def factorized_sequence_bits(summaries: dict[int, dict[str, Any]], train_books: list[int], score_books: list[int]) -> float:
    total = 0.0
    for field in ["control_counts", "behavior_counts"]:
        vocab = {token for summary in summaries.values() for token in summary[field]}
        _, _, sequence = score_bag_bits(summaries, train_books, score_books, "global", field, vocab)
        total += sequence
    return total


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100.0 * len(ordered)) - 1))
    return ordered[index]


def permuted_feature_controls(
    summaries: dict[int, dict[str, Any]],
    train_books: list[int],
    test_books: list[int],
    family: str,
    field: str,
    vocab: set[str],
    global_bag_bits: float,
    seed_offset: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    books = train_books + test_books
    observed = [feature_value(summaries[book], family) for book in books]
    savings = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(observed)
        rng.shuffle(shuffled)
        override = {book: state for book, state in zip(books, shuffled)}
        bag, _, _ = score_bag_bits(
            summaries, train_books, test_books, family, field, vocab, feature_override=override
        )
        savings.append(global_bag_bits - bag)
    return {
        "saving_mean": sum(savings) / len(savings),
        "saving_p05": percentile(savings, 5),
        "saving_p50": percentile(savings, 50),
        "saving_p95": percentile(savings, 95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def cutoff_gate(cutoff: int, summaries: dict[int, dict[str, Any]], seed_offset: int) -> dict[str, Any]:
    books = sorted(summaries)
    train_books = [book for book in books if book < cutoff]
    test_books = [book for book in books if book >= cutoff]
    field = "joint_counts"
    vocab = {token for summary in summaries.values() for token in summary[field]}

    family_rows = []
    for family in FAMILIES:
        train_mdl = loo_train_score(summaries, train_books, family, field, vocab)
        bag, order, sequence = score_bag_bits(summaries, train_books, test_books, family, field, vocab)
        family_rows.append(
            {
                "family": family,
                "grants_control_counts": family in GRANTED_FEATURES,
                "loo_train_mdl_bits": train_mdl,
                "test_bag_bits": bag,
                "test_order_index_bits": order,
                "test_sequence_bits": sequence,
                "test_books": len(test_books),
                "test_ops": sum(summaries[book]["op_count"] for book in test_books),
            }
        )
    selected = min(family_rows, key=lambda row: (row["loo_train_mdl_bits"], row["grants_control_counts"], row["family"]))
    global_row = next(row for row in family_rows if row["family"] == "global")
    controls = permuted_feature_controls(
        summaries,
        train_books,
        test_books,
        selected["family"],
        field,
        vocab,
        global_row["test_bag_bits"],
        seed_offset,
    )
    selected["test_bag_saving_vs_global"] = global_row["test_bag_bits"] - selected["test_bag_bits"]
    selected["beats_permuted_p95"] = selected["test_bag_saving_vs_global"] > controls["saving_p95"]
    factorized = factorized_sequence_bits(summaries, train_books, test_books)
    return {
        "cutoff": cutoff,
        "train_books": train_books,
        "test_books": test_books,
        "global_joint_bag_bits": global_row["test_bag_bits"],
        "global_joint_order_bits": global_row["test_order_index_bits"],
        "global_joint_sequence_bits": global_row["test_sequence_bits"],
        "global_factorized_sequence_bits": factorized,
        "selected": selected,
        "permuted_feature_controls": controls,
        "family_rows": family_rows,
    }


def make_result() -> dict[str, Any]:
    schedule = load_json(SCHEDULE_PILOT)
    assert_boundary("schedule_state_multistream_pilot", schedule)
    rows_by_book = load_book_rows()
    summaries = book_summary(rows_by_book)
    cutoff_rows = [
        cutoff_gate(cutoff, summaries, seed_offset=index)
        for index, cutoff in enumerate(CUTOFFS)
    ]
    selected_rows = [row["selected"] for row in cutoff_rows]
    total_selected_bag = sum(row["test_bag_bits"] for row in selected_rows)
    total_selected_order = sum(row["test_order_index_bits"] for row in selected_rows)
    total_selected_sequence = sum(row["test_sequence_bits"] for row in selected_rows)
    total_global_bag = sum(row["global_joint_bag_bits"] for row in cutoff_rows)
    total_global_order = sum(row["global_joint_order_bits"] for row in cutoff_rows)
    total_global_sequence = sum(row["global_joint_sequence_bits"] for row in cutoff_rows)
    total_factorized = sum(row["global_factorized_sequence_bits"] for row in cutoff_rows)
    beats_permuted = sum(row["selected"]["beats_permuted_p95"] for row in cutoff_rows)
    selected_with_granted_counts = sum(row["selected"]["grants_control_counts"] for row in cutoff_rows)
    bag_saving = total_global_bag - total_selected_bag
    sequence_saving = total_global_sequence - total_selected_sequence
    promoted = (
        bag_saving > 0
        and beats_permuted >= 4
        and selected_with_granted_counts == 0
        and total_selected_order < 0.25 * total_selected_sequence
    )
    weak = bag_saving > 0 and beats_permuted >= 3
    classification = (
        "PROMOTED_BOOK_MULTISET_GENERATOR_CANDIDATE"
        if promoted
        else "BOOK_MULTISET_COMPOSITION_CLUE_NOT_GENERATOR"
        if weak
        else "BOOK_MULTISET_ORDER_FACTORIZATION_AUDIT_ONLY"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "cutoff_rows": cutoff_rows,
        "decision": {
            "generator_promoted": promoted,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
            "why_not_generator": (
                "A book multiset factorization must reduce bag/composition cost above "
                "permuted-feature controls while keeping the exact order index small or "
                "separately generated. Otherwise it reorganizes the external tape but does "
                "not remove it."
            ),
        },
        "inputs": {
            "schedule_state_multistream_pilot": rel(SCHEDULE_PILOT),
            "unified_residual_control_ledger": rel(CONTROL_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "book_multiset_order_factorization_gate.v1",
        "scope": "analysis_only_book_level_joint_token_multiset_and_order_decomposition",
        "summary": {
            "bag_saving_vs_global": bag_saving,
            "beats_permuted_p95_cells": beats_permuted,
            "cutoffs": CUTOFFS,
            "selected_with_granted_count_features": selected_with_granted_counts,
            "sequence_saving_vs_global": sequence_saving,
            "total_factorized_sequence_bits": total_factorized,
            "total_global_bag_bits": total_global_bag,
            "total_global_order_bits": total_global_order,
            "total_global_sequence_bits": total_global_sequence,
            "total_selected_bag_bits": total_selected_bag,
            "total_selected_order_bits": total_selected_order,
            "total_selected_order_share": total_selected_order / max(1e-12, total_selected_sequence),
            "total_selected_sequence_bits": total_selected_sequence,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Book Multiset/Order Factorization Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Decompose the current joint operation-token stream into a per-book multiset "
        "and an exact within-book order index. This directly tests the clue left by "
        "HMM/schedule gates that failed same-book shuffle controls.",
        "",
        "## Summary",
        "",
        f"- Selected bag bits: `{s['total_selected_bag_bits']:.3f}`.",
        f"- Selected order-index bits: `{s['total_selected_order_bits']:.3f}`.",
        f"- Selected total sequence bits: `{s['total_selected_sequence_bits']:.3f}`.",
        f"- Order share of selected representation: `{s['total_selected_order_share']:.3f}`.",
        f"- Global bag bits: `{s['total_global_bag_bits']:.3f}`.",
        f"- Bag saving vs global: `{s['bag_saving_vs_global']:.3f}` bits.",
        f"- Cells beating permuted-feature p95: `{s['beats_permuted_p95_cells']}/5`.",
        f"- Selected models using granted count features: `{s['selected_with_granted_count_features']}/5`.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | Selected family | Test ops | Bag bits | Order bits | Bag saving | Beats permuted p95 | Grants count feature |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in result["cutoff_rows"]:
        selected = row["selected"]
        lines.append(
            f"| `{row['cutoff']}` | `{selected['family']}` | `{selected['test_ops']}` | "
            f"`{selected['test_bag_bits']:.3f}` | `{selected['test_order_index_bits']:.3f}` | "
            f"`{selected['test_bag_saving_vs_global']:.3f}` | "
            f"`{selected['beats_permuted_p95']}` | `{selected['grants_control_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This gate can promote only if book-level composition is predicted above "
            "permuted-feature controls and the remaining exact order index is small or "
            "handled by a separate generator. Otherwise the result is a useful ledger "
            "factorization, not a mechanical generation program.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Book Multiset/Order Factorization Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Does the recent multistream signal primarily live in book-level token "
        "composition rather than within-book order, and can that composition be "
        "predicted by prefix-trained metadata above controls?",
        "",
        "## Result",
        "",
        f"The train-selected book-level factorization costs "
        f"`{s['total_selected_bag_bits']:.3f}` bag bits plus "
        f"`{s['total_selected_order_bits']:.3f}` exact order-index bits. Bag saving "
        f"versus the global bag model is `{s['bag_saving_vs_global']:.3f}` bits, "
        f"with `{s['beats_permuted_p95_cells']}/5` cells beating permuted-feature p95. "
        f"The exact order index is `{s['total_selected_order_share']:.3f}` of the "
        "selected representation.",
        "",
        "## Decision",
        "",
        "The result is a generator only if the multiset can be predicted above "
        "controls and the order field is no longer a large external tape. Row0, "
        "plaintext, translation, and compression_bound remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_book_multiset_order_factorization_gate.py](../scripts/01_book_multiset_order_factorization_gate.py)",
        "- [01_book_multiset_order_factorization_gate.json](test_results/01_book_multiset_order_factorization_gate.json)",
        "- [01_book_multiset_order_factorization_gate.md](test_results/01_book_multiset_order_factorization_gate.md)",
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
