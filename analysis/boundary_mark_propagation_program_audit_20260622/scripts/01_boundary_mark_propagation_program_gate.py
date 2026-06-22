#!/usr/bin/env python3
"""Boundary-mark propagation program gate.

Executable v3 derives 29/208 copy intervals from event+surprisal source
boundaries. This gate tests a constructive next step: boundary marks are an
online state that propagates through copies. When a copy is emitted, any
source-side marks inside the copied interval are mapped into the target copy.
Future copies may then derive source+length from those propagated marks.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import bisect
import importlib.util
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "boundary_mark_propagation_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
UNIFIED_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
SOURCE_BOUNDARY_SCRIPT = (
    ROOT
    / "analysis"
    / "source_boundary_candidate_program_audit_20260622"
    / "scripts"
    / "01_source_boundary_candidate_program_gate.py"
)
EXECUTABLE_V3_GATE = (
    ROOT
    / "analysis"
    / "executable_v3_source_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v3_source_boundary_program_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_boundary_mark_propagation_program_gate.json"
MD_OUT = TEST_RESULTS / "01_boundary_mark_propagation_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_boundary_mark_propagation_program_audit.md"

RANDOM_SEED = 46920260622
LOG2_10 = math.log2(10)


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


def load_source_module() -> Any:
    spec = importlib.util.spec_from_file_location("source_boundary_gate", SOURCE_BOUNDARY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE_BOUNDARY_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grouped_ledger_rows() -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
    ledger = load_json(UNIFIED_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        grouped[int(row["book"])].append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }, ledger


def composition_count_for_unknowns(module: Any, unknown_rows: list[dict[str, Any]], remaining_sum: int) -> int:
    return module.composition_count_for_unknowns(unknown_rows, remaining_sum)


def score_candidate_set(module: Any, boundaries: set[int], source: int, length: int, bucket: str, remaining: int) -> dict[str, Any]:
    low, high = module.bucket_bounds(bucket, remaining)
    ordered = sorted(boundaries)
    hit = source in boundaries and source + length in boundaries and low <= length <= high
    count = module.interval_count(ordered, low, high)
    if not hit:
        return {
            "candidate_interval_count": count,
            "hit": False,
            "rank_bits": None,
        }
    module.boundary_set_global = set(ordered)
    rank = module.long_recent_rank(ordered, source, length, low, high)
    return {
        "candidate_interval_count": count,
        "hit": True,
        "rank_bits": math.log2(rank),
    }


def build_mode(mode: str) -> dict[str, Any]:
    module = load_source_module()
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, ledger = grouped_ledger_rows()
    emitted = "".join(books[book] for book in range(10))
    event_boundaries = {0}
    cursor = 0
    for book in range(10):
        cursor += len(books[book])
        event_boundaries.add(cursor)
    propagated_marks: set[int] = set(event_boundaries)
    rows = []
    rows_by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    rng = random.Random(RANDOM_SEED)
    for book in range(10, 70):
        rendered: list[str] = []
        for op in by_book[book]:
            op_index = int(op["op_index"])
            available = emitted + "".join(rendered)
            global_target_start = len(emitted) + int(op["target_start"])
            local_event_boundaries = set(event_boundaries)
            if rendered:
                prefix_cursor = len(emitted)
                acc = 0
                local_event_boundaries.add(prefix_cursor)
                for chunk in rendered:
                    acc += len(chunk)
                    local_event_boundaries.add(prefix_cursor + acc)
            base_systems = module.build_boundary_systems(available, local_event_boundaries)
            base_boundaries = set(base_systems["event_plus_surprisal_top20"])
            active_propagated = {mark for mark in propagated_marks if 0 <= mark <= len(available)}
            if mode == "base_no_propagation":
                boundaries = base_boundaries
            elif mode == "event_only_propagation":
                boundaries = base_boundaries | {
                    mark for mark in active_propagated if mark in event_boundaries
                }
            elif mode == "shuffled_propagation":
                count = len(active_propagated)
                sample = set(rng.sample(range(len(available) + 1), min(count, len(available) + 1)))
                boundaries = base_boundaries | sample
            elif mode == "propagated_marks":
                boundaries = base_boundaries | active_propagated
            else:
                raise KeyError(mode)
            op_type = str(op["op_type"])
            length = int(op["exact_length"])
            if op_type == "copy":
                bucket = str(op["coarse_type_length_bucket"]).split(":", 1)[1]
                source = int(op["copy_source_raw"])
                score = score_candidate_set(
                    module,
                    boundaries,
                    source,
                    length,
                    bucket,
                    int(op["book_length"]) - int(op["target_start"]),
                )
                row = {
                    "book": book,
                    "candidate_interval_count": int(score["candidate_interval_count"]),
                    "copy_hint_rank_bits": float(op["copy_hint_rank_bits"]),
                    "event_kind": "copy",
                    "exact_length": length,
                    "hit": bool(score["hit"]),
                    "mode": mode,
                    "op_index": op_index,
                    "rank_bits": score["rank_bits"],
                    "source": source,
                    "source_end": source + length,
                    "target_start": int(op["target_start"]),
                }
                # Propagation is online state; even fallback copies have paid
                # source/length, so their internal marks can be carried forward.
                source_marks = [
                    mark
                    for mark in boundaries
                    if source <= mark <= source + length
                ]
                if mode in {"propagated_marks", "shuffled_propagation", "event_only_propagation"}:
                    if mode == "event_only_propagation":
                        source_marks = [mark for mark in source_marks if mark in event_boundaries]
                    for mark in source_marks:
                        propagated_marks.add(global_target_start + (mark - source))
            else:
                row = {
                    "book": book,
                    "event_kind": "literal",
                    "exact_length": length,
                    "hit": True,
                    "literal_payload_bits": float(op["literal_payload_bits"]),
                    "mode": mode,
                    "op_index": op_index,
                    "target_start": int(op["target_start"]),
                }
            rows.append(row)
            rows_by_book[book].append(row)
            chunk = books[book][int(op["target_start"]) : int(op["target_start"]) + length]
            rendered.append(chunk)
            event_boundaries.add(global_target_start)
            event_boundaries.add(global_target_start + length)
            propagated_marks.add(global_target_start)
            propagated_marks.add(global_target_start + length)
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            raise RuntimeError({"book": book, "reason": "roundtrip_failed"})
        emitted += rendered_book
    composition_bits_by_book = {}
    baseline_composition_bits_by_book = {}
    for book, scored_rows in rows_by_book.items():
        truth = by_book[book]
        known_sum = 0
        unknown = []
        for scored, op in zip(scored_rows, truth):
            if scored["event_kind"] == "copy" and scored["hit"]:
                known_sum += int(op["exact_length"])
            else:
                unknown.append(op)
        remaining = int(truth[0]["book_length"]) - known_sum
        composition_bits_by_book[book] = math.log2(
            composition_count_for_unknowns(module, unknown, remaining)
        )
        baseline_composition_bits_by_book[book] = sum(
            float(op["composition_index_bits_charged_here"]) for op in truth
        )
    return summarize(rows, composition_bits_by_book, baseline_composition_bits_by_book, ledger, mode)


def summarize(
    rows: list[dict[str, Any]],
    composition_bits_by_book: dict[int, float],
    baseline_composition_bits_by_book: dict[int, float],
    ledger: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    copy_rows = [row for row in rows if row["event_kind"] == "copy"]
    literal_rows = [row for row in rows if row["event_kind"] == "literal"]
    rank_bits = sum(float(row["rank_bits"]) for row in copy_rows if row["hit"])
    fallback_bits = sum(float(row["copy_hint_rank_bits"]) for row in copy_rows if not row["hit"])
    literal_bits = sum(float(row["literal_payload_bits"]) for row in literal_rows)
    composition_bits = sum(composition_bits_by_book.values())
    total = rank_bits + fallback_bits + literal_bits + composition_bits
    v3 = load_json(EXECUTABLE_V3_GATE)["summary"]
    return {
        "baseline_v3_residual_bits": float(v3["source_boundary_residual_bits"]),
        "candidate_interval_count_mean_hit": mean(
            [int(row["candidate_interval_count"]) for row in copy_rows if row["hit"]]
        )
        if any(row["hit"] for row in copy_rows)
        else 0.0,
        "composition_bits": composition_bits,
        "copy_hits": sum(1 for row in copy_rows if row["hit"]),
        "copy_misses": sum(1 for row in copy_rows if not row["hit"]),
        "copy_ops": len(copy_rows),
        "delta_vs_v3_residual_bits": total - float(v3["source_boundary_residual_bits"]),
        "fallback_copy_hint_bits": fallback_bits,
        "literal_payload_bits": literal_bits,
        "mode": mode,
        "rank_bits": rank_bits,
        "residual_bits": total,
        "rows": rows,
    }


def make_result() -> dict[str, Any]:
    v3 = load_json(EXECUTABLE_V3_GATE)
    assert_boundary("executable_v3_source_boundary_program_gate", v3)
    mode_summaries = [
        build_mode(mode)
        for mode in [
            "base_no_propagation",
            "event_only_propagation",
            "shuffled_propagation",
            "propagated_marks",
        ]
    ]
    best = min(mode_summaries, key=lambda row: row["residual_bits"])
    propagated = next(row for row in mode_summaries if row["mode"] == "propagated_marks")
    shuffled = next(row for row in mode_summaries if row["mode"] == "shuffled_propagation")
    event_only = next(row for row in mode_summaries if row["mode"] == "event_only_propagation")
    promoted = (
        propagated["delta_vs_v3_residual_bits"] < 0
        and propagated["copy_hits"] > event_only["copy_hits"]
        and propagated["copy_hits"] > shuffled["copy_hits"]
        and propagated["residual_bits"] < shuffled["residual_bits"]
    )
    compact_modes = [
        {key: value for key, value in row.items() if key != "rows"}
        for row in mode_summaries
    ]
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_BOUNDARY_MARK_PROPAGATION_PROGRAM"
            if promoted
            else "boundary_mark_propagation_not_promoted"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "boundary_mark_propagation_promoted": promoted,
            "next_blocker": (
                "boundary propagation does not explain enough additional "
                "fallback intervals" if not promoted else "remaining fallback intervals after propagated boundary marks"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v3_source_boundary_program_gate": rel(EXECUTABLE_V3_GATE),
            "source_boundary_script": rel(SOURCE_BOUNDARY_SCRIPT),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "mode_summaries": compact_modes,
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "boundary_mark_propagation_program_gate.v1",
        "scope": "analysis_only_boundary_mark_propagation_program",
        "summary": {
            key: value for key, value in propagated.items() if key != "rows"
        }
        | {
            "best_mode": best["mode"],
            "delta_hits_vs_event_only": propagated["copy_hits"] - event_only["copy_hits"],
            "delta_hits_vs_shuffled": propagated["copy_hits"] - shuffled["copy_hits"],
            "promoted": promoted,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Boundary-Mark Propagation Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Do source-side boundary marks propagate through copy events and explain "
        "additional future copy intervals beyond executable v3?",
        "",
        "## Summary",
        "",
        f"- Propagated copy hits/misses: `{s['copy_hits']}/{s['copy_misses']}` out of `{s['copy_ops']}`.",
        f"- Delta hits vs event-only propagation: `{s['delta_hits_vs_event_only']}`.",
        f"- Delta hits vs shuffled propagation: `{s['delta_hits_vs_shuffled']}`.",
        f"- V3 residual baseline: `{s['baseline_v3_residual_bits']:.3f}` bits.",
        f"- Propagated residual bits: `{s['residual_bits']:.3f}`.",
        f"- Delta vs v3 residual: `{s['delta_vs_v3_residual_bits']:.3f}` bits.",
        f"- Rank/fallback/composition/literal bits: `{s['rank_bits']:.3f}` / `{s['fallback_copy_hint_bits']:.3f}` / `{s['composition_bits']:.3f}` / `{s['literal_payload_bits']:.3f}`.",
        "",
        "## Modes",
        "",
        "| Mode | Hits | Residual bits | Delta vs v3 | Rank bits | Fallback bits |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["mode_summaries"]:
        lines.append(
            f"| `{row['mode']}` | `{row['copy_hits']}` | `{row['residual_bits']:.3f}` | "
            f"`{row['delta_vs_v3_residual_bits']:.3f}` | `{row['rank_bits']:.3f}` | "
            f"`{row['fallback_copy_hint_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_BOUNDARY_MARK_PROPAGATION_PROGRAM`: propagated marks "
                "reduce the v3 ledger and beat propagation controls."
                if result["summary"]["promoted"]
                else "`boundary_mark_propagation_not_promoted`: propagated "
                "marks do not improve the executable v3 residual ledger beyond "
                "controls."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Boundary-Mark Propagation Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested whether source-boundary marks are a persistent online "
        "state. When a copy is emitted, source-side marks inside the copied span "
        "are mapped into the target span and can support future source-interval "
        "derivations.",
        "",
        f"With propagated marks, derived copy intervals are `{s['copy_hits']}/208` "
        f"and the residual is `{s['residual_bits']:.3f}` bits versus v3 at "
        f"`{s['baseline_v3_residual_bits']:.3f}`, a delta of "
        f"`{s['delta_vs_v3_residual_bits']:.3f}` bits.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_BOUNDARY_MARK_PROPAGATION_PROGRAM`."
            if result["summary"]["promoted"]
            else "`boundary_mark_propagation_not_promoted`. Boundary marks as "
            "implemented here do not open a stronger generator than v3; the "
            "remaining source intervals still require another origin mechanism."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_boundary_mark_propagation_program_gate.py](../scripts/01_boundary_mark_propagation_program_gate.py)",
        "- [01_boundary_mark_propagation_program_gate.json](test_results/01_boundary_mark_propagation_program_gate.json)",
        "- [01_boundary_mark_propagation_program_gate.md](test_results/01_boundary_mark_propagation_program_gate.md)",
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
