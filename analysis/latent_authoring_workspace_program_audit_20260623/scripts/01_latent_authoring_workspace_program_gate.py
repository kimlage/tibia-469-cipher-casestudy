#!/usr/bin/env python3
"""Latent authoring workspace program audit.

This gate tests a constructive program class instead of another local residual
codec. A workspace state has emitted text, reusable endpoint/source marks, a
source cursor, copy-continuation, and an innovation-tape pointer. Candidate
events are generated from that state without target-text lookup. The true v9
operation path is then scored in prefix/holdout and against controls.

Analysis-only: row0, plaintext, semantics, and compression_bound are unchanged.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "latent_authoring_workspace_program_audit_20260623"
OUT_DIR = FRONT / "reports" / "test_results"
JSON_OUT = OUT_DIR / "01_latent_authoring_workspace_program_gate.json"
MD_OUT = OUT_DIR / "01_latent_authoring_workspace_program_gate.md"
IR_OUT = OUT_DIR / "01_latent_authoring_workspace_ir.json"
FINAL_OUT = FRONT / "reports" / "final_latent_authoring_workspace_program_audit.md"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
UNIFIED_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
UNIFIED_PAYLOAD = (
    ROOT
    / "analysis"
    / "unified_innovation_payload_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_innovation_payload_gate.json"
)
EXECUTABLE_V9 = (
    ROOT
    / "analysis"
    / "executable_v9_innovation_copy_continuation_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v9_innovation_copy_continuation_gate.json"
)

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260623
CONTROL_TRIALS = 80
BEAM_WIDTH = 128
DECLARATION_BITS = math.log2(7)  # action families below
ACTION_FAMILIES = [
    "literal_consume",
    "copy_continuation",
    "source_cursor_same",
    "source_cursor_advance",
    "nearest_start_mark",
    "nearest_end_mark",
    "copy_between_marks",
]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0")


@dataclass(frozen=True)
class Op:
    book: int
    op_index: int
    target_start: int
    op_type: str
    length: int
    source: int | None
    literal_payload: str | None
    literal_tape_start: int | None
    literal_tape_end: int | None
    coarse: str
    composition_bits: float
    copy_hint_bits: float
    literal_payload_bits: float
    minimal_external_bits: float

    @property
    def token(self) -> tuple[str, int | None, int]:
        return (self.op_type, self.source, self.length)


@dataclass
class Workspace:
    emitted_len: int
    marks: set[int]
    source_cursor: int | None
    previous_copy_source: int | None
    previous_copy_length: int | None
    literal_pointer: int


def grouped_ops(ledger: dict[str, Any]) -> dict[int, list[Op]]:
    by_book: dict[int, list[Op]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        op = Op(
            book=int(row["book"]),
            op_index=int(row["op_index"]),
            target_start=int(row["target_start"]),
            op_type=str(row["op_type"]),
            length=int(row["exact_length"]),
            source=int(row["copy_source_raw"]) if row["copy_source_raw"] is not None else None,
            literal_payload=str(row["literal_payload"]) if row.get("literal_payload") is not None else None,
            literal_tape_start=int(row["literal_tape_start"]) if row.get("literal_tape_start") is not None else None,
            literal_tape_end=int(row["literal_tape_end"]) if row.get("literal_tape_end") is not None else None,
            coarse=str(row["coarse_type_length_bucket"]),
            composition_bits=float(row["composition_index_bits_charged_here"]),
            copy_hint_bits=float(row["copy_hint_rank_bits"]),
            literal_payload_bits=float(row["literal_payload_bits"]),
            minimal_external_bits=float(row["total_external_bits_charged_here"]),
        )
        by_book[op.book].append(op)
    return {book: sorted(ops, key=lambda op: op.op_index) for book, ops in by_book.items()}


def seed_length(books: dict[int, str]) -> int:
    return sum(len(books[i]) for i in range(10))


def literal_stream(payload: dict[str, Any]) -> str:
    return "".join(str(event["text"]) for event in payload["event_ledger"] if event["kind"] == "literal")


def build_ir(books: dict[int, str], by_book: dict[int, list[Op]], payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    global_book_start = seed_length(books)
    literal_text = literal_stream(payload)
    for book in range(10, 70):
        for op in by_book[book]:
            target_global_start = global_book_start + op.target_start
            lineage = ["literal_innovation"] if op.op_type == "literal" else ["copy_from_emitted_material"]
            rows.append(
                {
                    "book": book,
                    "op_index": op.op_index,
                    "target_span": [target_global_start, target_global_start + op.length],
                    "target_start": op.target_start,
                    "op_type": op.op_type,
                    "source_span": [op.source, op.source + op.length] if op.source is not None else None,
                    "length": op.length,
                    "coarse_type_length_bucket": op.coarse,
                    "lineage": lineage,
                    "literal_tape_position": [op.literal_tape_start, op.literal_tape_end]
                    if op.literal_tape_start is not None
                    else None,
                    "literal_payload_matches_tape": (
                        literal_text[op.literal_tape_start : op.literal_tape_end] == op.literal_payload
                        if op.literal_tape_start is not None and op.literal_tape_end is not None
                        else None
                    ),
                    "minimal_external_bits": op.minimal_external_bits,
                }
            )
        global_book_start += len(books[book])
    return rows


def bucket_bounds(coarse: str, remaining: int) -> tuple[int, int]:
    bucket = coarse.split(":", 1)[1]
    ranges = {
        "len_0008": (1, 8),
        "len_0016": (9, 16),
        "len_0032": (17, 32),
        "len_0064": (33, 64),
        "len_0128": (65, 128),
        "len_0256p": (129, remaining),
    }
    low, high = ranges[bucket]
    return low, min(high, remaining)


def candidate_actions(ws: Workspace, op: Op, remaining: int, train_lengths: dict[str, list[int]], randomized_marks: bool = False) -> list[dict[str, Any]]:
    low, high = bucket_bounds(op.coarse, remaining)
    marks = sorted(value for value in ws.marks if 0 <= value <= ws.emitted_len)
    if randomized_marks:
        rng = random.Random(RANDOM_SEED + op.book * 1000 + op.op_index)
        marks = sorted(rng.sample(range(ws.emitted_len + 1), min(len(marks), ws.emitted_len + 1))) if ws.emitted_len else [0]
    candidates: dict[tuple[str, int | None, int], dict[str, Any]] = {}

    def add(kind: str, source: int | None, length: int, rank_hint: int) -> None:
        if length < low or length > high:
            return
        if source is not None and (source < 0 or source + length > ws.emitted_len):
            return
        key = ("copy" if source is not None else "literal", source, length)
        current = candidates.get(key)
        row = {"op_type": key[0], "source": source, "length": length, "family": kind, "rank_hint": rank_hint}
        if current is None or row["rank_hint"] < current["rank_hint"]:
            candidates[key] = row

    if op.op_type == "literal" or op.coarse.startswith("literal:"):
        learned = train_lengths.get(op.coarse, [])
        literal_lengths = list(dict.fromkeys(learned[:8]))
        literal_lengths += [low, high]
        for idx, length in enumerate(dict.fromkeys(length for length in literal_lengths if low <= length <= high), start=1):
            add("literal_consume", None, length, idx)

    if op.coarse.startswith("copy:"):
        preferred_lengths = train_lengths.get(op.coarse, [])
        lengths = []
        lengths.extend(preferred_lengths[:8])
        lengths.extend([low, high])
        lengths = list(dict.fromkeys(length for length in lengths if low <= length <= high))

        if ws.previous_copy_source is not None and ws.previous_copy_length is not None:
            source = ws.previous_copy_source + ws.previous_copy_length
            for idx, length in enumerate(lengths, start=1):
                add("copy_continuation", source, length, idx)

        cursor_sources = []
        if ws.source_cursor is not None:
            cursor_sources.extend([ws.source_cursor, ws.source_cursor + (ws.previous_copy_length or 0)])
        for sidx, source in enumerate(dict.fromkeys(cursor_sources), start=1):
            for lidx, length in enumerate(lengths, start=1):
                add("source_cursor_same" if sidx == 1 else "source_cursor_advance", source, length, sidx * 10 + lidx)

        if marks:
            nearest_starts = sorted(marks, key=lambda mark: abs(mark - (ws.source_cursor or ws.emitted_len)))[:24]
            for midx, source in enumerate(nearest_starts, start=1):
                for lidx, length in enumerate(lengths, start=1):
                    add("nearest_start_mark", source, length, midx * 10 + lidx)
            for midx, end in enumerate(nearest_starts, start=1):
                for lidx, length in enumerate(lengths, start=1):
                    add("nearest_end_mark", end - length, length, midx * 10 + lidx)
            for sidx, source in enumerate(marks[-48:], start=1):
                for end in marks:
                    length = end - source
                    if low <= length <= high:
                        add("copy_between_marks", source, length, sidx)

    return sorted(candidates.values(), key=lambda row: (row["rank_hint"], row["family"], row["source"] if row["source"] is not None else -1, row["length"]))


def update_workspace(ws: Workspace, op: Op) -> None:
    start = ws.emitted_len
    end = ws.emitted_len + op.length
    ws.marks.add(start)
    ws.marks.add(end)
    if op.op_type == "copy" and op.source is not None:
        ws.marks.add(op.source)
        ws.marks.add(op.source + op.length)
        ws.source_cursor = op.source + op.length
        ws.previous_copy_source = op.source
        ws.previous_copy_length = op.length
    else:
        if op.literal_tape_end is not None:
            ws.literal_pointer = op.literal_tape_end
        ws.previous_copy_source = None
        ws.previous_copy_length = None
    ws.emitted_len = end


def train_length_priors(by_book: dict[int, list[Op]], train_books: set[int]) -> dict[str, list[int]]:
    counts: dict[str, Counter[int]] = defaultdict(Counter)
    for book in sorted(train_books):
        for op in by_book.get(book, []):
            counts[op.coarse][op.length] += 1
    return {
        key: [length for length, _count in counter.most_common()]
        for key, counter in counts.items()
    }


def score_books(
    books: dict[int, str],
    by_book: dict[int, list[Op]],
    test_books: list[int],
    train_lengths: dict[str, list[int]],
    randomized_marks: bool = False,
    event_shuffle: bool = False,
    literal_shuffle: bool = False,
) -> dict[str, Any]:
    ws = Workspace(emitted_len=seed_length(books), marks={0, seed_length(books)}, source_cursor=0, previous_copy_source=None, previous_copy_length=None, literal_pointer=0)
    cursor = 0
    for book in range(10):
        cursor += len(books[book])
        ws.marks.add(cursor)
    exact_events = 0
    exact_books_without_correction = 0
    books_true_path_in_beam = 0
    total_events = 0
    rank_bits = 0.0
    correction_bits = 0.0
    rows = []
    rng = random.Random(RANDOM_SEED + 99)
    for book in range(10, 70):
        ops = list(by_book[book])
        if event_shuffle and book in test_books:
            shuffled = ops[:]
            rng.shuffle(shuffled)
            ops = [
                Op(
                    book=op.book,
                    op_index=idx,
                    target_start=sum(item.length for item in shuffled[:idx]),
                    op_type=op.op_type,
                    length=op.length,
                    source=op.source,
                    literal_payload=op.literal_payload,
                    literal_tape_start=op.literal_tape_start,
                    literal_tape_end=op.literal_tape_end,
                    coarse=op.coarse,
                    composition_bits=op.composition_bits,
                    copy_hint_bits=op.copy_hint_bits,
                    literal_payload_bits=op.literal_payload_bits,
                    minimal_external_bits=op.minimal_external_bits,
                )
                for idx, op in enumerate(shuffled)
            ]
        book_all_in_beam = True
        rendered_len = 0
        for op in ops:
            remaining = max(1, len(books[book]) - rendered_len)
            candidates = candidate_actions(ws, op, remaining, train_lengths, randomized_marks=randomized_marks)
            token_to_rank = {("copy" if c["source"] is not None else "literal", c["source"], c["length"]): idx for idx, c in enumerate(candidates[:BEAM_WIDTH], start=1)}
            true_token = op.token
            rank = token_to_rank.get(true_token)
            total_events += 1
            if rank is not None:
                exact_events += 1
                rank_bits += math.log2(rank)
            else:
                book_all_in_beam = False
                fallback = op.composition_bits + op.copy_hint_bits + (op.literal_payload_bits if op.op_type == "literal" else 0.0)
                correction_bits += fallback
            rows.append(
                {
                    "book": book,
                    "op_index": op.op_index,
                    "op_type": op.op_type,
                    "length": op.length,
                    "source": op.source,
                    "candidate_count": len(candidates),
                    "rank_in_beam": rank,
                    "in_beam": rank is not None,
                    "correction_bits_if_miss": 0.0
                    if rank is not None
                    else op.composition_bits + op.copy_hint_bits + (op.literal_payload_bits if op.op_type == "literal" else 0.0),
                }
            )
            update_workspace(ws, op)
            rendered_len += op.length
        if book in test_books and book_all_in_beam and ops:
            books_true_path_in_beam += 1
        if book in test_books and book_all_in_beam and len(ops) > 1:
            exact_books_without_correction += 1
    program_bits = DECLARATION_BITS + rank_bits + correction_bits
    return {
        "book_true_path_in_beam": books_true_path_in_beam,
        "correction_bits": correction_bits,
        "event_rows": rows,
        "events_in_beam": exact_events,
        "exact_nontrivial_books_without_correction": exact_books_without_correction,
        "program_bits": program_bits,
        "rank_bits": rank_bits,
        "total_events": total_events,
    }


def prefix_holdouts(books: dict[int, str], by_book: dict[int, list[Op]]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        test_books = list(range(cutoff, 70))
        train_lengths = train_length_priors(by_book, train_books)
        scored = score_books(books, by_book, test_books, train_lengths)
        test_rows = [row for row in scored["event_rows"] if row["book"] in test_books]
        test_events = len(test_rows)
        test_hits = sum(1 for row in test_rows if row["in_beam"])
        rows.append(
            {
                "cutoff": cutoff,
                "test_books": len(test_books),
                "test_events": test_events,
                "test_events_in_beam": test_hits,
                "test_event_beam_fraction": test_hits / test_events if test_events else 0.0,
                "true_path_books_in_beam": scored["book_true_path_in_beam"],
                "exact_nontrivial_books_without_correction": scored["exact_nontrivial_books_without_correction"],
                "program_bits": scored["program_bits"],
                "rank_bits": scored["rank_bits"],
                "correction_bits": scored["correction_bits"],
            }
        )
    return rows


def controls(books: dict[int, str], by_book: dict[int, list[Op]]) -> dict[str, Any]:
    cutoff = 40
    train_lengths = train_length_priors(by_book, set(range(10, cutoff)))
    test_books = list(range(cutoff, 70))
    real = score_books(books, by_book, test_books, train_lengths)
    control_rows = []
    for trial in range(CONTROL_TRIALS):
        random.seed(RANDOM_SEED + trial)
        randomized_marks = trial % 2 == 0
        event_shuffle = trial % 2 == 1
        scored = score_books(books, by_book, test_books, train_lengths, randomized_marks=randomized_marks, event_shuffle=event_shuffle)
        test_rows = [row for row in scored["event_rows"] if row["book"] in test_books]
        control_rows.append(
            {
                "events_in_beam": sum(1 for row in test_rows if row["in_beam"]),
                "true_path_books_in_beam": scored["book_true_path_in_beam"],
                "program_bits": scored["program_bits"],
            }
        )
    hit_values = sorted(row["events_in_beam"] for row in control_rows)
    path_values = sorted(row["true_path_books_in_beam"] for row in control_rows)
    bit_values = sorted(row["program_bits"] for row in control_rows)
    real_test_hits = sum(1 for row in real["event_rows"] if row["book"] in test_books and row["in_beam"])
    return {
        "control_trials": CONTROL_TRIALS,
        "cutoff": cutoff,
        "real_events_in_beam": real_test_hits,
        "real_true_path_books_in_beam": real["book_true_path_in_beam"],
        "real_program_bits": real["program_bits"],
        "events_in_beam_p95": hit_values[math.ceil(0.95 * len(hit_values)) - 1],
        "true_path_books_in_beam_p95": path_values[math.ceil(0.95 * len(path_values)) - 1],
        "program_bits_p05": bit_values[math.ceil(0.05 * len(bit_values)) - 1],
        "beats_event_beam_p95": real_test_hits > hit_values[math.ceil(0.95 * len(hit_values)) - 1],
        "beats_true_path_p95": real["book_true_path_in_beam"] > path_values[math.ceil(0.95 * len(path_values)) - 1],
        "beats_program_bits_p05": real["program_bits"] < bit_values[math.ceil(0.05 * len(bit_values)) - 1],
    }


def make_result() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ledger = load_json(UNIFIED_LEDGER)
    payload = load_json(UNIFIED_PAYLOAD)
    v9 = load_json(EXECUTABLE_V9)
    for name, data in [("unified_ledger", ledger), ("unified_payload", payload), ("executable_v9", v9)]:
        assert_boundary(name, data)
    if v9["classification"] != "PROMOTED_EXECUTABLE_V9_INNOVATION_COPY_CONTINUATION_LEDGER":
        raise RuntimeError("v9 baseline not promoted")
    by_book = grouped_ops(ledger)
    ir = build_ir(books, by_book, payload)
    holdouts = prefix_holdouts(books, by_book)
    ctrl = controls(books, by_book)
    exact_books = sum(row["exact_nontrivial_books_without_correction"] for row in holdouts)
    any_positive_generation = exact_books > 0
    beam_advantage = ctrl["beats_true_path_p95"] and sum(row["true_path_books_in_beam"] for row in holdouts) > 0
    # This gate still grants true coarse buckets/op positions while testing the
    # workspace action surface, so its bits are a lower bound and cannot reduce
    # v9 by themselves.
    cost_advantage = False
    promoted = any_positive_generation or beam_advantage
    classification = (
        "PROMOTED_LATENT_AUTHORING_WORKSPACE_PROGRAM_CANDIDATE"
        if promoted
        else "latent_authoring_workspace_program_not_promoted"
    )
    result = {
        "schema": "latent_authoring_workspace_program_gate.v1",
        "scope": "analysis_only_workspace_program_candidate",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "baseline": {
            "v9_classification": v9["classification"],
            "v9_external_bits_total_content_included": v9["summary"]["v9_external_bits_total_content_included"],
        },
        "workspace_program": {
            "action_families": ACTION_FAMILIES,
            "beam_width": BEAM_WIDTH,
            "inputs_granted": ["book_order", "book_lengths", "seed_books", "unified_innovation_tape"],
            "state": ["emitted_text", "source_cursor", "endpoint_marks", "previous_copy", "literal_pointer"],
        },
        "summary": {
            "holdout_count": len(holdouts),
            "total_test_events": sum(row["test_events"] for row in holdouts),
            "total_test_events_in_beam": sum(row["test_events_in_beam"] for row in holdouts),
            "total_true_path_books_in_beam": sum(row["true_path_books_in_beam"] for row in holdouts),
            "exact_nontrivial_books_without_correction": exact_books,
            "workspace_lower_bound_bits": min(row["program_bits"] for row in holdouts),
            "v9_bits": v9["summary"]["v9_external_bits_total_content_included"],
            "net_reduction_vs_v9_bits": None,
            "cost_comparison_status": "not_comparable_lower_bound_grants_coarse_and_op_positions",
        },
        "holdouts": holdouts,
        "controls": ctrl,
        "decision": {
            "workspace_program_promoted": promoted,
            "external_field_reduced": cost_advantage,
            "event_policy_promoted": any_positive_generation or beam_advantage,
            "origin_source_promoted": False,
            "reason": (
                "workspace program meets at least one promotion criterion"
                if promoted
                else "Workspace candidates do not generate nontrivial books or preserve true paths above controls; lower-bound bits do not reduce v9"
            ),
            "next_route_if_failed": "stop internal route as mainline; require clean primary authoring surface acquisition/test",
        },
    }
    return result, ir


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Latent Authoring Workspace Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Baseline v9 bits: `{s['v9_bits']:.3f}`.",
        f"- Workspace lower-bound bits: `{s['workspace_lower_bound_bits']:.3f}`.",
        f"- Cost comparison status: `{s['cost_comparison_status']}`.",
        f"- Test events in beam: `{s['total_test_events_in_beam']}/{s['total_test_events']}`.",
        f"- True-path books in beam: `{s['total_true_path_books_in_beam']}`.",
        f"- Exact nontrivial books without correction: `{s['exact_nontrivial_books_without_correction']}`.",
        "",
        "## Control Gate",
        "",
        f"- Cutoff: `{c['cutoff']}`.",
        f"- Real events in beam: `{c['real_events_in_beam']}`; control p95 `{c['events_in_beam_p95']}`.",
        f"- Real true-path books in beam: `{c['real_true_path_books_in_beam']}`; control p95 `{c['true_path_books_in_beam_p95']}`.",
        f"- Real program bits: `{c['real_program_bits']:.3f}`; control p05 `{c['program_bits_p05']:.3f}`.",
        f"- Beats event-beam p95: `{c['beats_event_beam_p95']}`.",
        f"- Beats true-path p95: `{c['beats_true_path_p95']}`.",
        f"- Beats program-bits p05: `{c['beats_program_bits_p05']}`.",
        "",
        "## Decision",
        "",
        f"`{result['decision']['reason']}`.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Latent Authoring Workspace Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit converts the v9 frontier into a latent workspace program test.",
        "The program uses emitted text, reusable endpoint/source marks, a source cursor, copy-continuation, and a unified innovation-tape pointer.",
        "Candidate events are generated from workspace state rather than target-text lookup, then the true path is scored with rank/corrections in prefix holdout and controls.",
        "",
        f"The best workspace lower-bound cost is `{s['workspace_lower_bound_bits']:.3f}` bits versus v9 `{s['v9_bits']:.3f}`, but this is not counted as a v9 reduction because it still grants true coarse buckets/op positions.",
        f"It keeps `{s['total_test_events_in_beam']}/{s['total_test_events']}` held-out events in beam, but generates `{s['exact_nontrivial_books_without_correction']}` nontrivial books without correction.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        result["decision"]["reason"],
        "Because this is not promoted, the internal route should stop as the main front; the next aligned route is clean primary authoring-surface acquisition/test using the existing object-layer contract.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_latent_authoring_workspace_program_gate.py](../scripts/01_latent_authoring_workspace_program_gate.py)",
        "- [01_latent_authoring_workspace_program_gate.json](test_results/01_latent_authoring_workspace_program_gate.json)",
        "- [01_latent_authoring_workspace_ir.json](test_results/01_latent_authoring_workspace_ir.json)",
        "- [01_latent_authoring_workspace_program_gate.md](test_results/01_latent_authoring_workspace_program_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result, ir = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    IR_OUT.write_text(json.dumps({"schema": "latent_authoring_workspace_ir.v1", "rows": ir}, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
