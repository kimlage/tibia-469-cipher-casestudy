#!/usr/bin/env python3
"""Online x64 coarse-control program gate.

The x64 internal-start beam is now controlled in prefix holdout, including paid
rank/correction cost. This gate asks the executable-program question directly:
if the decoder walks books 10..69 once, trains only on previous decoded/corrected
books, and knows only book_length, can the x64 controller reduce the external
coarse-control tape?

Two baselines are reported to avoid overclaiming:
- explicit op_count + coarse sequence declaration per book;
- the older minimal external tape ledger, which is more generous because it
  treats op_count/book operation boundaries as already implicit in the tape.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "online_x64_coarse_control_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOK_LEVEL_SCRIPT = (
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
PAID_CONTROL = (
    ROOT
    / "analysis"
    / "internal_start_beam_paid_control_audit_20260622"
    / "reports"
    / "test_results"
    / "01_internal_start_beam_paid_control_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_online_x64_coarse_control_program_gate.json"
MD_OUT = TEST_RESULTS / "01_online_x64_coarse_control_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_online_x64_coarse_control_program_audit.md"

WIDTH_LABEL = "x64"
SEQ_BEAM = 768
BOOK_BEAM = 1920
COUNT_MODEL = "book_length"
COARSE_MODEL = "op_count"
RANDOM_TRIALS = 500
RANDOM_SEED = 46920260622 + 264


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    decision = data.get("decision", {})
    row0 = data.get("row0_status") or decision.get("row0_status") or decision.get("row0_origin_status")
    if row0 not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status: {row0}")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = (len(ordered) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    frac = index - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def sequence_key(sequence: list[str]) -> tuple[str, ...]:
    return tuple(sequence)


def coarse_sequence(rows: list[dict[str, Any]]) -> list[str]:
    return [row["symbol"] for row in rows]


def internal_starts(rows: list[dict[str, Any]]) -> int:
    return max(0, len(rows) - 1)


def explicit_opcount_coarse_bits(bl, sequence: list[str]) -> float:
    return math.log2(bl.MAX_OPCOUNT) + len(sequence) * math.log2(len(bl.VOCAB))


def minimal_coarse_bits(bl, sequence: list[str]) -> float:
    return len(sequence) * math.log2(len(bl.VOCAB))


def composition_bits(bl, rows: list[dict[str, Any]]) -> float:
    sequence = coarse_sequence(rows)
    book_length = int(rows[0]["book_length"])
    return math.log2(max(1, bl.count_compositions(sequence, book_length)))


def decode_online(bl, books: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    old_seq = bl.SEQ_BEAM_WIDTH
    old_book = bl.BOOK_BEAM_WIDTH
    bl.SEQ_BEAM_WIDTH = SEQ_BEAM
    bl.BOOK_BEAM_WIDTH = BOOK_BEAM
    try:
        rows = []
        train: dict[int, list[dict[str, Any]]] = {}
        for book in sorted(books):
            book_rows = books[book]
            sequence = coarse_sequence(book_rows)
            if train:
                count_model = bl.train_count_model(COUNT_MODEL, train)
                coarse_model = bl.train_coarse_model(COARSE_MODEL, train)
                decoded = bl.decode_book(count_model, coarse_model, book, book_rows)
            else:
                decoded = []
            decoded_ranks = {
                sequence_key(item["sequence"]): index + 1
                for index, item in enumerate(decoded)
            }
            rank = decoded_ranks.get(sequence_key(sequence))
            rows.append(
                {
                    "_decoded_ranks": decoded_ranks,
                    "book": book,
                    "book_length": int(book_rows[0]["book_length"]),
                    "composition_bits": composition_bits(bl, book_rows),
                    "decoded_candidates": len(decoded),
                    "explicit_opcount_coarse_bits": explicit_opcount_coarse_bits(bl, sequence),
                    "generated_internal_starts": internal_starts(book_rows) if rank is not None else 0,
                    "hit_rank": rank,
                    "internal_starts": internal_starts(book_rows),
                    "minimal_coarse_bits": minimal_coarse_bits(bl, sequence),
                    "op_count": len(book_rows),
                    "sequence": sequence,
                    "sequence_in_beam": rank is not None,
                    "top_sequence": decoded[0]["sequence"] if decoded else [],
                }
            )
            # A correction tape, when needed, supplies the true sequence before the
            # next book is trained. That keeps the online program executable.
            train[book] = book_rows
    finally:
        bl.SEQ_BEAM_WIDTH = old_seq
        bl.BOOK_BEAM_WIDTH = old_book
    return rows


def score_rows(bl, rows: list[dict[str, Any]], sequences_by_book: dict[int, list[str]] | None = None) -> dict[str, Any]:
    scored_rows = []
    totals = {
        "composition_bits": 0.0,
        "correction_bits": 0.0,
        "explicit_opcount_coarse_bits": 0.0,
        "generated_internal_starts": 0.0,
        "minimal_coarse_bits": 0.0,
        "online_paid_coarse_bits": 0.0,
        "rank_bits": 0.0,
        "sequence_hits": 0.0,
        "test_books": 0.0,
        "test_internal_starts": 0.0,
        "test_ops": 0.0,
    }
    for row in rows:
        sequence = sequences_by_book[row["book"]] if sequences_by_book else row["sequence"]
        explicit_bits = explicit_opcount_coarse_bits(bl, sequence)
        minimal_bits = minimal_coarse_bits(bl, sequence)
        rank = row["_decoded_ranks"].get(sequence_key(sequence))
        if rank is None:
            rank_bits = 0.0
            correction = explicit_bits
        else:
            rank_bits = math.log2(rank)
            correction = 0.0
        paid = rank_bits + correction
        starts = row["internal_starts"] if rank is not None else 0
        totals["composition_bits"] += row["composition_bits"]
        totals["correction_bits"] += correction
        totals["explicit_opcount_coarse_bits"] += explicit_bits
        totals["generated_internal_starts"] += starts
        totals["minimal_coarse_bits"] += minimal_bits
        totals["online_paid_coarse_bits"] += paid
        totals["rank_bits"] += rank_bits
        totals["sequence_hits"] += int(rank is not None)
        totals["test_books"] += 1
        totals["test_internal_starts"] += row["internal_starts"]
        totals["test_ops"] += len(sequence)
        scored_rows.append(
            {
                **{
                    key: value
                    for key, value in row.items()
                    if key not in {"_decoded_ranks", "sequence"}
                },
                "online_paid_coarse_bits": paid,
                "rank_bits": rank_bits,
                "scored_sequence_op_count": len(sequence),
            }
        )
    totals["saving_vs_explicit_opcount_coarse_bits"] = (
        totals["explicit_opcount_coarse_bits"] - totals["online_paid_coarse_bits"]
    )
    totals["saving_vs_minimal_coarse_bits"] = (
        totals["minimal_coarse_bits"] - totals["online_paid_coarse_bits"]
    )
    totals["online_coarse_plus_composition_bits"] = (
        totals["online_paid_coarse_bits"] + totals["composition_bits"]
    )
    totals["minimal_coarse_plus_composition_bits"] = (
        totals["minimal_coarse_bits"] + totals["composition_bits"]
    )
    return {"rows": scored_rows, "summary": totals}


def shuffled_controls(bl, rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    sequences = [row["sequence"] for row in rows]
    saving_explicit = []
    saving_minimal = []
    hits = []
    starts = []
    for _ in range(RANDOM_TRIALS):
        shuffled = list(sequences)
        rng.shuffle(shuffled)
        sequences_by_book = {
            row["book"]: sequence for row, sequence in zip(rows, shuffled)
        }
        scored = score_rows(bl, rows, sequences_by_book)["summary"]
        saving_explicit.append(scored["saving_vs_explicit_opcount_coarse_bits"])
        saving_minimal.append(scored["saving_vs_minimal_coarse_bits"])
        hits.append(scored["sequence_hits"])
        starts.append(scored["generated_internal_starts"])
    return {
        "generated_internal_starts_p95": percentile(starts, 0.95),
        "saving_vs_explicit_opcount_coarse_bits_mean": mean(saving_explicit),
        "saving_vs_explicit_opcount_coarse_bits_p95": percentile(saving_explicit, 0.95),
        "saving_vs_minimal_coarse_bits_mean": mean(saving_minimal),
        "saving_vs_minimal_coarse_bits_p95": percentile(saving_minimal, 0.95),
        "sequence_hits_p95": percentile(hits, 0.95),
        "trials": RANDOM_TRIALS,
    }


def make_result() -> dict[str, Any]:
    minimal = load_json(MINIMAL_LEDGER)
    paid = load_json(PAID_CONTROL)
    assert_boundary("minimal_external_tape_ledger", minimal)
    assert_boundary("internal_start_beam_paid_control", paid)
    if paid["classification"] != "PROMOTED_X64_INTERNAL_START_PAID_CONTROLLED_CANDIDATE":
        raise RuntimeError("online gate expects the paid x64 control candidate")

    bl = load_module("book_level_controller_online_x64", BOOK_LEVEL_SCRIPT)
    books = bl.load_books()
    decoded_rows = decode_online(bl, books)
    scored = score_rows(bl, decoded_rows)
    controls = shuffled_controls(bl, decoded_rows)
    s = scored["summary"]

    beats_explicit_controls = (
        s["saving_vs_explicit_opcount_coarse_bits"]
        > controls["saving_vs_explicit_opcount_coarse_bits_p95"]
    )
    beats_minimal_controls = (
        s["saving_vs_minimal_coarse_bits"]
        > controls["saving_vs_minimal_coarse_bits_p95"]
    )
    reduces_minimal_ledger = s["saving_vs_minimal_coarse_bits"] > 0
    if reduces_minimal_ledger and beats_minimal_controls:
        classification = "PROMOTED_ONLINE_X64_MINIMAL_LEDGER_REDUCTION"
    elif beats_explicit_controls and s["saving_vs_explicit_opcount_coarse_bits"] > 0:
        classification = "PROMOTED_ONLINE_X64_EXPLICIT_COARSE_CONTROL_CANDIDATE"
    else:
        classification = "ONLINE_X64_COARSE_CONTROL_NOT_PROMOTED"

    minimal_summary = minimal["summary"]
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": controls,
        "decision": {
            "beats_explicit_same_multiset_controls": beats_explicit_controls,
            "beats_minimal_same_multiset_controls": beats_minimal_controls,
            "generator_promoted": False,
            "reduces_current_minimal_coarse_ledger": reduces_minimal_ledger,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "book_level_controller_script": rel(BOOK_LEVEL_SCRIPT),
            "minimal_external_tape_ledger": rel(MINIMAL_LEDGER),
            "paid_x64_control_gate": rel(PAID_CONTROL),
            "random_seed": RANDOM_SEED,
            "random_trials": RANDOM_TRIALS,
            "width": WIDTH_LABEL,
        },
        "minimal_ledger_reference": {
            "coarse_control_bits_uniform": minimal_summary["coarse_control_bits_uniform"],
            "coarse_plus_composition_bits": (
                minimal_summary["coarse_control_bits_uniform"]
                + minimal_summary["composition_index_bits"]
            ),
            "composition_index_bits": minimal_summary["composition_index_bits"],
        },
        "plaintext_claim": False,
        "rows": scored["rows"],
        "schema": "online_x64_coarse_control_program_gate.v1",
        "scope": "analysis_only_online_executable_coarse_control_program",
        "summary": {
            **s,
            "classification": classification,
            "online_exact_books_without_correction": s["sequence_hits"],
            "online_exact_ops_without_correction": sum(
                row["op_count"] for row in decoded_rows if row["sequence_in_beam"]
            ),
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    s = result["summary"]
    c = result["controls"]
    m = result["minimal_ledger_reference"]
    lines = [
        "# Online x64 Coarse-Control Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can the x64 book-level controller run as a one-pass executable coarse-control "
        "program for books `10..69`, training only on previous decoded/corrected books?",
        "",
        "## Summary",
        "",
        f"- Sequence hits without correction: `{s['sequence_hits']:.0f}/{s['test_books']:.0f}`.",
        f"- Exact ops without coarse correction: `{s['online_exact_ops_without_correction']:.0f}/{s['test_ops']:.0f}`.",
        f"- Internal starts generated before correction: `{s['generated_internal_starts']:.0f}/{s['test_internal_starts']:.0f}`.",
        f"- Online paid coarse bits: `{s['online_paid_coarse_bits']:.3f}`.",
        f"- Explicit op_count+coarse bits: `{s['explicit_opcount_coarse_bits']:.3f}`.",
        f"- Saving vs explicit op_count+coarse: `{s['saving_vs_explicit_opcount_coarse_bits']:.3f}` bits.",
        f"- Control p95 saving vs explicit: `{c['saving_vs_explicit_opcount_coarse_bits_p95']:.3f}` bits.",
        f"- Current minimal coarse bits: `{m['coarse_control_bits_uniform']:.3f}`.",
        f"- Saving vs current minimal coarse ledger: `{s['saving_vs_minimal_coarse_bits']:.3f}` bits.",
        f"- Control p95 saving vs minimal coarse: `{c['saving_vs_minimal_coarse_bits_p95']:.3f}` bits.",
        f"- Coarse+composition after online program: `{s['online_coarse_plus_composition_bits']:.3f}`.",
        f"- Current minimal coarse+composition ledger: `{m['coarse_plus_composition_bits']:.3f}`.",
        "",
        "## Interpretation",
        "",
    ]
    if result["classification"] == "PROMOTED_ONLINE_X64_MINIMAL_LEDGER_REDUCTION":
        lines.append(
            "The online x64 controller reduces the current minimal executable coarse "
            "ledger after same-multiset controls. This is a real executable-program "
            "dependency reduction, while the fine composition index and other tapes "
            "remain external."
        )
    elif result["classification"] == "PROMOTED_ONLINE_X64_EXPLICIT_COARSE_CONTROL_CANDIDATE":
        lines.append(
            "The online x64 controller reduces an explicit op_count+coarse declaration "
            "and beats same-multiset controls, but it does not reduce the older minimal "
            "ledger where op_count/book operation boundaries are already implicit. "
            "This is a representation-sensitive generation clue, not a full executable "
            "ledger replacement."
        )
    else:
        lines.append(
            "The online x64 controller does not reduce the executable coarse-control "
            "ledger under the charged one-pass program."
        )
    lines.extend(
        [
            "",
            "## Book Rows",
            "",
            "| Book | Ops | Rank | Paid Coarse | Explicit Coarse | Minimal Coarse |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in result["rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['op_count']}` | "
            f"`{row['hit_rank'] if row['hit_rank'] is not None else 'MISS'}` | "
            f"`{row['online_paid_coarse_bits']:.3f}` | "
            f"`{row['explicit_opcount_coarse_bits']:.3f}` | "
            f"`{row['minimal_coarse_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "`row0`, plaintext, translation, and `compression_bound` remain unchanged. "
            "The fine residual composition index, literal payload, copy/source hints, "
            "and seed payload remain external or paid.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result, MD_OUT)
    write_markdown(result, FINAL_OUT)
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "saving_vs_explicit": result["summary"][
                    "saving_vs_explicit_opcount_coarse_bits"
                ],
                "saving_vs_minimal": result["summary"]["saving_vs_minimal_coarse_bits"],
                "sequence_hits": result["summary"]["sequence_hits"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
