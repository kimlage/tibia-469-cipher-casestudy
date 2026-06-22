#!/usr/bin/env python3
"""Unanchored copy-origin representation gate.

Executable v4 leaves 83 copy intervals with neither source endpoint anchored.
This gate tests two representation changes for that class:

1. source_endpoint_memory: once a copy source has been paid or derived, its
   source-side endpoints become online marks for future source intervals.
2. within_prior_span_interval: encode an unanchored copy as an interval inside a
   previously emitted operation/book span.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "unanchored_copy_origin_representation_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

ONE_SIDED_SCRIPT = (
    ROOT
    / "analysis"
    / "one_sided_source_boundary_program_audit_20260622"
    / "scripts"
    / "01_one_sided_source_boundary_program_gate.py"
)
SOURCE_BOUNDARY_SCRIPT = (
    ROOT
    / "analysis"
    / "source_boundary_candidate_program_audit_20260622"
    / "scripts"
    / "01_source_boundary_candidate_program_gate.py"
)
EXECUTABLE_V4_GATE = (
    ROOT
    / "analysis"
    / "executable_v4_one_sided_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v4_one_sided_boundary_program_gate.json"
)
UNANCHORED_LEDGER = (
    ROOT
    / "analysis"
    / "v4_unanchored_copy_residual_audit_20260622"
    / "reports"
    / "test_results"
    / "01_v4_unanchored_copy_residual_ledger.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

JSON_OUT = TEST_RESULTS / "01_unanchored_copy_origin_representation_gate.json"
MD_OUT = TEST_RESULTS / "01_unanchored_copy_origin_representation_gate.md"
FINAL_OUT = FRONT / "reports" / "final_unanchored_copy_origin_representation_audit.md"

RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300
ONLINE_X64_COARSE_BITS = 876.412
BASE_SYSTEM_CACHE: dict[tuple[int, int], dict[str, set[int]]] = {}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def endpoint_rank_bits(boundaries: set[int], endpoint: int) -> float | None:
    if endpoint not in boundaries:
        return None
    return math.log2(1 + sum(1 for mark in boundaries if mark > endpoint))


def score_interval(module: Any, boundaries: set[int], source: int, length: int, low: int, high: int) -> float | None:
    if source not in boundaries or source + length not in boundaries or not (low <= length <= high):
        return None
    ordered = sorted(boundaries)
    module.boundary_set_global = set(ordered)
    return math.log2(module.long_recent_rank(ordered, source, length, low, high))


def composition_count(module: Any, unknown_rows: list[dict[str, Any]], remaining_sum: int) -> int:
    return module.composition_count_for_unknowns(unknown_rows, remaining_sum)


def grouped_rows(one_sided: Any) -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
    return one_sided.grouped_ledger_rows()


def base_event_boundaries(books: dict[int, str]) -> tuple[str, set[int]]:
    emitted = ""
    boundaries = {0}
    cursor = 0
    for book in range(10):
        emitted += books[book]
        cursor += len(books[book])
        boundaries.add(cursor)
    return emitted, boundaries


def summarize_source_endpoint_mode(mode: str, shuffle: bool = False, seed: int = RANDOM_SEED) -> dict[str, Any]:
    one_sided = load_module("one_sided_gate", ONE_SIDED_SCRIPT)
    source_module = load_module("source_boundary_gate", SOURCE_BOUNDARY_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, _ledger = grouped_rows(one_sided)
    emitted, event_boundaries = base_event_boundaries(books)
    source_marks: set[int] = set()
    rows = []
    rows_by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    rng = random.Random(seed)
    marks_added = 0
    for book in range(10, 70):
        rendered: list[str] = []
        for op in by_book[book]:
            available = emitted + "".join(rendered)
            local_event_boundaries = set(event_boundaries)
            if rendered:
                prefix_cursor = len(emitted)
                acc = 0
                local_event_boundaries.add(prefix_cursor)
                for chunk in rendered:
                    acc += len(chunk)
                    local_event_boundaries.add(prefix_cursor + acc)
            cache_key = (book, int(op["op_index"]))
            if cache_key not in BASE_SYSTEM_CACHE:
                BASE_SYSTEM_CACHE[cache_key] = source_module.build_boundary_systems(
                    available,
                    local_event_boundaries,
                )
            base_systems = BASE_SYSTEM_CACHE[cache_key]
            active_marks = {mark for mark in source_marks if 0 <= mark <= len(available)}
            if shuffle and active_marks:
                active_marks = set(
                    rng.sample(
                        range(len(available) + 1),
                        min(len(active_marks), len(available) + 1),
                    )
                )
            boundaries = set(base_systems["event_plus_surprisal_top20"]) | active_marks
            op_type = str(op["op_type"])
            length = int(op["exact_length"])
            target_start = int(op["target_start"])
            if op_type == "copy":
                source = int(op["copy_source_raw"])
                end = source + length
                bucket = str(op["coarse_type_length_bucket"]).split(":", 1)[1]
                low, high = source_module.bucket_bounds(bucket, int(op["book_length"]) - target_start)
                interval_bits = score_interval(source_module, boundaries, source, length, low, high)
                end_bits = endpoint_rank_bits(boundaries, end)
                if interval_bits is not None:
                    paid_bits = interval_bits
                    row_class = "both_endpoint_interval"
                    known_length = True
                elif end_bits is not None:
                    paid_bits = end_bits
                    row_class = "end_only"
                    known_length = False
                else:
                    paid_bits = float(op["copy_hint_rank_bits"])
                    row_class = "fallback"
                    known_length = False
                row = {
                    "book": book,
                    "copy_hint_rank_bits": float(op["copy_hint_rank_bits"]),
                    "event_kind": "copy",
                    "exact_length": length,
                    "known_length": known_length,
                    "op_index": int(op["op_index"]),
                    "paid_bits": paid_bits,
                    "row_class": row_class,
                    "source": source,
                    "source_end": end,
                    "target_start": target_start,
                }
                if mode == "source_endpoint_memory":
                    source_marks.add(source)
                    source_marks.add(end)
                    marks_added += 2
                elif mode == "source_endpoint_hit_only" and interval_bits is not None:
                    source_marks.add(source)
                    source_marks.add(end)
                    marks_added += 2
            else:
                row = {
                    "book": book,
                    "event_kind": "literal",
                    "exact_length": length,
                    "known_length": False,
                    "literal_payload_bits": float(op["literal_payload_bits"]),
                    "op_index": int(op["op_index"]),
                    "paid_bits": 0.0,
                    "row_class": "literal",
                    "target_start": target_start,
                }
            rows.append(row)
            rows_by_book[book].append(row)
            chunk = books[book][target_start : target_start + length]
            rendered.append(chunk)
            global_start = len(emitted) + target_start
            event_boundaries.add(global_start)
            event_boundaries.add(global_start + length)
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            raise RuntimeError({"book": book, "reason": "roundtrip_failed"})
        emitted += rendered_book

    composition_bits = 0.0
    for book, scored_rows in rows_by_book.items():
        truth = by_book[book]
        known_sum = 0
        unknown = []
        for scored, op in zip(scored_rows, truth):
            if scored["event_kind"] == "copy" and scored["known_length"]:
                known_sum += int(op["exact_length"])
            else:
                unknown.append(op)
        remaining = int(truth[0]["book_length"]) - known_sum
        composition_bits += math.log2(composition_count(source_module, unknown, remaining))

    copy_rows = [row for row in rows if row["event_kind"] == "copy"]
    literal_rows = [row for row in rows if row["event_kind"] == "literal"]
    class_counts: dict[str, int] = defaultdict(int)
    for row in copy_rows:
        class_counts[str(row["row_class"])] += 1
    copy_bits = sum(float(row["paid_bits"]) for row in copy_rows)
    literal_bits = sum(float(row["literal_payload_bits"]) for row in literal_rows)
    residual_bits = copy_bits + composition_bits + literal_bits
    return {
        "class_counts": dict(class_counts),
        "composition_bits": composition_bits,
        "copy_bits": copy_bits,
        "copy_ops": len(copy_rows),
        "literal_payload_bits": literal_bits,
        "marks_added": marks_added,
        "mode": mode + ("_shuffled" if shuffle else ""),
        "residual_bits": residual_bits,
        "rows": copy_rows,
    }


def summarize_within_span() -> dict[str, Any]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    one_sided = load_module("one_sided_gate", ONE_SIDED_SCRIPT)
    by_book, _ledger = grouped_rows(one_sided)
    spans = []
    position = 0
    for book in range(10):
        length = len(books[book])
        spans.append(
            {
                "book": book,
                "end": position + length,
                "kind": "seed_book",
                "length": length,
                "op_index": None,
                "start": position,
            }
        )
        position += length
    rows = []
    for book in range(10, 70):
        rendered = []
        for op in by_book[book]:
            length = int(op["exact_length"])
            target_start = int(op["target_start"])
            global_start = position + target_start
            if op["op_type"] == "copy":
                source = int(op["copy_source_raw"])
                end = source + length
                containing = [
                    span
                    for span in spans
                    if int(span["start"]) <= source and end <= int(span["end"])
                ]
                span = containing[-1] if containing else None
                if span is not None:
                    recent_rank = len(spans) - spans.index(span)
                    # Choose start/end offsets inside the containing span.
                    offset_count = int(span["length"]) * (int(span["length"]) + 1) // 2
                    paid_bits = math.log2(recent_rank) + math.log2(max(1, offset_count))
                    delta = paid_bits - float(op["copy_hint_rank_bits"])
                else:
                    paid_bits = None
                    delta = None
                rows.append(
                    {
                        "book": book,
                        "copy_hint_rank_bits": float(op["copy_hint_rank_bits"]),
                        "delta_vs_copy_hint": delta,
                        "fits_single_prior_span": span is not None,
                        "op_index": int(op["op_index"]),
                        "paid_bits": paid_bits,
                        "source": source,
                        "source_end": end,
                        "span_length": int(span["length"]) if span is not None else None,
                        "span_recent_rank": recent_rank if span is not None else None,
                    }
                )
            chunk = books[book][target_start : target_start + length]
            rendered.append(chunk)
            spans.append(
                {
                    "book": book,
                    "end": global_start + length,
                    "kind": "op",
                    "length": length,
                    "op_index": int(op["op_index"]),
                    "start": global_start,
                }
            )
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            raise RuntimeError({"book": book, "reason": "roundtrip_failed"})
        position += len(books[book])
    fitting = [row for row in rows if row["fits_single_prior_span"]]
    return {
        "copy_ops": len(rows),
        "delta_vs_copy_hint_on_fitting": sum(float(row["delta_vs_copy_hint"]) for row in fitting),
        "fitting_copy_hint_bits": sum(float(row["copy_hint_rank_bits"]) for row in fitting),
        "fitting_count": len(fitting),
        "fitting_paid_bits": sum(float(row["paid_bits"]) for row in fitting),
        "mean_delta_on_fitting": mean([float(row["delta_vs_copy_hint"]) for row in fitting]) if fitting else 0.0,
        "mode": "within_prior_span_interval",
    }


def make_result() -> dict[str, Any]:
    v4 = load_json(EXECUTABLE_V4_GATE)
    unanchored = load_json(UNANCHORED_LEDGER)
    assert_boundary("executable_v4_one_sided_boundary_program_gate", v4)
    assert_boundary("v4_unanchored_copy_residual_ledger", unanchored)
    v4_residual = float(v4["summary"]["v4_residual_bits"])
    source_memory = summarize_source_endpoint_mode("source_endpoint_memory")
    hit_only = summarize_source_endpoint_mode("source_endpoint_hit_only")
    shuffled = [
        summarize_source_endpoint_mode(
            "source_endpoint_memory",
            shuffle=True,
            seed=RANDOM_SEED + trial,
        )
        for trial in range(RANDOM_TRIALS)
    ]
    shuffled_residuals = sorted(float(row["residual_bits"]) for row in shuffled)
    shuffled_hits = sorted(int(row["class_counts"].get("both_endpoint_interval", 0)) for row in shuffled)
    within_span = summarize_within_span()
    declaration_bits = math.log2(3)
    delta_source_memory = float(source_memory["residual_bits"]) - v4_residual
    delta_hit_only = float(hit_only["residual_bits"]) - v4_residual
    promoted = (
        delta_source_memory + declaration_bits < 0
        and float(source_memory["residual_bits"]) + declaration_bits
        < shuffled_residuals[int(0.05 * RANDOM_TRIALS)]
    )
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_UNANCHORED_COPY_ORIGIN_REPRESENTATION"
            if promoted
            else "UNANCHORED_COPY_ORIGIN_REPRESENTATION_NOT_PROMOTED"
        ),
        "compression_bound_status": "unchanged",
        "control": {
            "random_trials": RANDOM_TRIALS,
            "shuffled_hit_p95": shuffled_hits[int(0.95 * RANDOM_TRIALS)],
            "shuffled_residual_p05": shuffled_residuals[int(0.05 * RANDOM_TRIALS)],
            "source_memory_beats_shuffled_p05": float(source_memory["residual_bits"])
            + declaration_bits
            < shuffled_residuals[int(0.05 * RANDOM_TRIALS)],
        },
        "decision": {
            "next_blocker": "source_endpoint_memory_and_within_span_do_not_reduce_v4",
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v4_one_sided_boundary_program_gate": rel(EXECUTABLE_V4_GATE),
            "one_sided_source_boundary_program_script": rel(ONE_SIDED_SCRIPT),
            "source_boundary_candidate_program_script": rel(SOURCE_BOUNDARY_SCRIPT),
            "v4_unanchored_copy_residual_ledger": rel(UNANCHORED_LEDGER),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "unanchored_copy_origin_representation_gate.v1",
        "scope": "analysis_only_unanchored_copy_origin_representation",
        "summary": {
            "delta_hit_only_vs_v4": delta_hit_only,
            "delta_source_endpoint_memory_after_declaration_vs_v4": delta_source_memory
            + declaration_bits,
            "delta_source_endpoint_memory_vs_v4": delta_source_memory,
            "declaration_bits_representation_family": declaration_bits,
            "hit_only": {key: value for key, value in hit_only.items() if key != "rows"},
            "promoted": promoted,
            "source_endpoint_memory": {key: value for key, value in source_memory.items() if key != "rows"},
            "source_endpoint_memory_residual_with_declaration": float(source_memory["residual_bits"])
            + declaration_bits,
            "v4_residual_bits": v4_residual,
            "within_prior_span_interval": within_span,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    sem = s["source_endpoint_memory"]
    hit = s["hit_only"]
    span = s["within_prior_span_interval"]
    lines = [
        "# Unanchored Copy-Origin Representation Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can the v4 neither-endpoint copy blocker be reduced by changing the source "
        "origin representation, rather than tuning endpoint activation?",
        "",
        "## Source Endpoint Memory",
        "",
        f"- V4 residual bits: `{s['v4_residual_bits']:.3f}`.",
        f"- Source-endpoint memory residual bits: `{sem['residual_bits']:.3f}`.",
        f"- Representation declaration bits: `{s['declaration_bits_representation_family']:.3f}`.",
        f"- Delta vs v4: `{s['delta_source_endpoint_memory_vs_v4']:.3f}`.",
        f"- Delta after declaration vs v4: `{s['delta_source_endpoint_memory_after_declaration_vs_v4']:.3f}`.",
        f"- Class counts: `{sem['class_counts']}`.",
        f"- Shuffled residual p05: `{c['shuffled_residual_p05']:.3f}`.",
        f"- Shuffled interval-hit p95: `{c['shuffled_hit_p95']}`.",
        f"- Beats shuffled p05: `{c['source_memory_beats_shuffled_p05']}`.",
        "",
        "## Hit-Only Source Endpoint Memory",
        "",
        f"- Residual bits: `{hit['residual_bits']:.3f}`.",
        f"- Delta vs v4: `{s['delta_hit_only_vs_v4']:.3f}`.",
        f"- Class counts: `{hit['class_counts']}`.",
        "",
        "## Within Prior Span Interval",
        "",
        f"- Fitting copy ops: `{span['fitting_count']}/{span['copy_ops']}`.",
        f"- Paid bits on fitting ops: `{span['fitting_paid_bits']:.3f}`.",
        f"- Copy-hint bits on fitting ops: `{span['fitting_copy_hint_bits']:.3f}`.",
        f"- Delta on fitting ops: `{span['delta_vs_copy_hint_on_fitting']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_UNANCHORED_COPY_ORIGIN_REPRESENTATION`."
            if s["promoted"]
            else "`UNANCHORED_COPY_ORIGIN_REPRESENTATION_NOT_PROMOTED`."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    sem = s["source_endpoint_memory"]
    span = s["within_prior_span_interval"]
    lines = [
        "# Final Unanchored Copy-Origin Representation Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested two representation changes for the v4 neither-endpoint "
        "copy blocker. `source_endpoint_memory` records paid/derived source "
        "endpoints as future boundary marks. `within_prior_span_interval` encodes "
        "a copy as offsets inside a previous generated span.",
        "",
        f"Source-endpoint memory costs `{sem['residual_bits']:.3f}` residual bits "
        f"versus v4 at `{s['v4_residual_bits']:.3f}`, a delta of "
        f"`{s['delta_source_endpoint_memory_vs_v4']:.3f}` before declaration and "
        f"`{s['delta_source_endpoint_memory_after_declaration_vs_v4']:.3f}` after "
        f"charging `{s['declaration_bits_representation_family']:.3f}` bits. The shuffled-control "
        f"residual p05 is `{c['shuffled_residual_p05']:.3f}`.",
        "",
        f"Within-span origin is worse on its own terms: `{span['fitting_count']}` "
        f"copy ops fit inside one prior span, but span+offset coding is "
        f"`{span['delta_vs_copy_hint_on_fitting']:.3f}` bits worse than the "
        "existing copy-hint tape on those same ops.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_UNANCHORED_COPY_ORIGIN_REPRESENTATION`."
            if s["promoted"]
            else "`UNANCHORED_COPY_ORIGIN_REPRESENTATION_NOT_PROMOTED`."
        ),
        "",
        (
            "Source-endpoint memory is promoted as a small executable residual "
            "reduction. It is still partial: fallback copy hints, literal payload, "
            "seed payload, and row0 remain external."
            if s["promoted"]
            else "The v4 neither-endpoint blocker remains. The tested representation changes "
            "do not supply a smaller executable source-origin program."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_unanchored_copy_origin_representation_gate.py](../scripts/01_unanchored_copy_origin_representation_gate.py)",
        "- [01_unanchored_copy_origin_representation_gate.json](test_results/01_unanchored_copy_origin_representation_gate.json)",
        "- [01_unanchored_copy_origin_representation_gate.md](test_results/01_unanchored_copy_origin_representation_gate.md)",
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
