#!/usr/bin/env python3
"""V5 near-source-mark offset gate.

Many v5 fallback copies appear close to an existing source mark. This gate
tests whether that is an executable program or only a lower bound that grants
the identity of the nearest mark for free.

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
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "v5_near_source_mark_offset_audit_20260622"
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
EXECUTABLE_V5_GATE = (
    ROOT
    / "analysis"
    / "executable_v5_source_endpoint_memory_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v5_source_endpoint_memory_gate.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

JSON_OUT = TEST_RESULTS / "01_v5_near_source_mark_offset_gate.json"
MD_OUT = TEST_RESULTS / "01_v5_near_source_mark_offset_gate.md"
FINAL_OUT = FRONT / "reports" / "final_v5_near_source_mark_offset_audit.md"

RANDOM_SEED = 46920260622
RANDOM_TRIALS = 200
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


def interval_rank_bits(module: Any, boundaries: set[int], source: int, length: int, low: int, high: int) -> float | None:
    if source not in boundaries or source + length not in boundaries or not (low <= length <= high):
        return None
    ordered = sorted(boundaries)
    module.boundary_set_global = set(ordered)
    return math.log2(module.long_recent_rank(ordered, source, length, low, high))


def nearest_mark(ordered: list[int], value: int) -> tuple[int, int, int]:
    index = bisect.bisect_left(ordered, value)
    candidates = []
    if index < len(ordered):
        candidates.append(ordered[index])
    if index > 0:
        candidates.append(ordered[index - 1])
    mark = min(candidates, key=lambda item: abs(item - value))
    recent_rank = 1 + sum(1 for candidate in ordered if candidate > mark)
    return mark, value - mark, recent_rank


def signed_offset_bits(offset: int) -> float:
    return math.log2(2 * abs(offset) + 1)


def collect_fallback_rows(shuffle_marks: bool = False, seed: int = RANDOM_SEED) -> list[dict[str, Any]]:
    one_sided = load_module("one_sided_gate", ONE_SIDED_SCRIPT)
    source_module = load_module("source_boundary_gate", SOURCE_BOUNDARY_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, _ledger = one_sided.grouped_ledger_rows()
    emitted = "".join(books[book] for book in range(10))
    event_boundaries = {0}
    cursor = 0
    for book in range(10):
        cursor += len(books[book])
        event_boundaries.add(cursor)
    source_marks: set[int] = set()
    rows = []
    rng = random.Random(seed)
    for book in range(10, 70):
        rendered = []
        for op in by_book[book]:
            available = emitted + "".join(rendered)
            local_boundaries = set(event_boundaries)
            if rendered:
                prefix = len(emitted)
                acc = 0
                local_boundaries.add(prefix)
                for chunk in rendered:
                    acc += len(chunk)
                    local_boundaries.add(prefix + acc)
            cache_key = (book, int(op["op_index"]))
            if cache_key not in BASE_SYSTEM_CACHE:
                BASE_SYSTEM_CACHE[cache_key] = source_module.build_boundary_systems(
                    available,
                    local_boundaries,
                )
            active_marks = {mark for mark in source_marks if 0 <= mark <= len(available)}
            if shuffle_marks and active_marks:
                active_marks = set(
                    rng.sample(
                        range(len(available) + 1),
                        min(len(active_marks), len(available) + 1),
                    )
                )
            boundaries = set(BASE_SYSTEM_CACHE[cache_key]["event_plus_surprisal_top20"]) | active_marks
            op_type = str(op["op_type"])
            length = int(op["exact_length"])
            target_start = int(op["target_start"])
            if op_type == "copy":
                source = int(op["copy_source_raw"])
                source_end = source + length
                bucket = str(op["coarse_type_length_bucket"]).split(":", 1)[1]
                low, high = source_module.bucket_bounds(bucket, int(op["book_length"]) - target_start)
                interval_bits = interval_rank_bits(source_module, boundaries, source, length, low, high)
                end_bits = endpoint_rank_bits(boundaries, source_end)
                is_v5_fallback = interval_bits is None and end_bits is None
                if is_v5_fallback:
                    ordered = sorted(boundaries)
                    source_mark, source_offset, source_rank = nearest_mark(ordered, source)
                    end_mark, end_offset, end_rank = nearest_mark(ordered, source_end)
                    source_paid = math.log2(source_rank) + signed_offset_bits(source_offset)
                    end_paid = math.log2(end_rank) + signed_offset_bits(end_offset)
                    rows.append(
                        {
                            "book": book,
                            "copy_hint_rank_bits": float(op["copy_hint_rank_bits"]),
                            "end_mark_recent_rank": end_rank,
                            "end_offset": end_offset,
                            "end_paid_bits": end_paid,
                            "exact_length": length,
                            "mark_count": len(ordered),
                            "op_index": int(op["op_index"]),
                            "source_mark_recent_rank": source_rank,
                            "source_offset": source_offset,
                            "source_paid_bits": source_paid,
                            "target_start": target_start,
                        }
                    )
                source_marks.add(source)
                source_marks.add(source_end)
            chunk = books[book][target_start : target_start + length]
            rendered.append(chunk)
            global_start = len(emitted) + target_start
            event_boundaries.add(global_start)
            event_boundaries.add(global_start + length)
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            raise RuntimeError({"book": book, "reason": "roundtrip_failed"})
        emitted += rendered_book
    return rows


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hint_bits = sum(float(row["copy_hint_rank_bits"]) for row in rows)
    source_offset_only_bits = sum(signed_offset_bits(int(row["source_offset"])) for row in rows)
    end_offset_only_bits = sum(signed_offset_bits(int(row["end_offset"])) for row in rows)
    source_paid_bits = sum(float(row["source_paid_bits"]) for row in rows)
    end_paid_bits = sum(float(row["end_paid_bits"]) for row in rows)
    best_paid_bits = sum(
        1.0 + min(float(row["source_paid_bits"]), float(row["end_paid_bits"]))
        for row in rows
    )
    return {
        "end_offset_abs_median": median([abs(int(row["end_offset"])) for row in rows]),
        "end_offset_only_bits": end_offset_only_bits,
        "end_paid_bits": end_paid_bits,
        "fallback_copy_hint_bits": hint_bits,
        "fallback_count": len(rows),
        "invalid_end_offset_only_delta": end_offset_only_bits - hint_bits,
        "invalid_source_offset_only_delta": source_offset_only_bits - hint_bits,
        "paid_best_endpoint_with_mode_delta": best_paid_bits - hint_bits,
        "paid_best_endpoint_with_mode_bits": best_paid_bits,
        "paid_end_delta": end_paid_bits - hint_bits,
        "paid_source_delta": source_paid_bits - hint_bits,
        "source_offset_abs_median": median([abs(int(row["source_offset"])) for row in rows]),
        "source_offset_exact_mark_count": sum(1 for row in rows if int(row["source_offset"]) == 0),
        "source_offset_only_bits": source_offset_only_bits,
        "source_paid_bits": source_paid_bits,
    }


def make_result() -> dict[str, Any]:
    v5 = load_json(EXECUTABLE_V5_GATE)
    assert_boundary("executable_v5_source_endpoint_memory_gate", v5)
    rows = collect_fallback_rows()
    summary = summarize_rows(rows)
    shuffled_source_paid = sorted(
        summarize_rows(collect_fallback_rows(shuffle_marks=True, seed=RANDOM_SEED + trial))[
            "source_paid_bits"
        ]
        for trial in range(RANDOM_TRIALS)
    )
    promoted = summary["paid_source_delta"] < 0
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_V5_NEAR_SOURCE_MARK_OFFSET_PROGRAM"
            if promoted
            else "V5_NEAR_SOURCE_MARK_OFFSET_NOT_PROMOTED"
        ),
        "compression_bound_status": "unchanged",
        "control": {
            "random_trials": RANDOM_TRIALS,
            "shuffled_source_paid_p05": shuffled_source_paid[int(0.05 * RANDOM_TRIALS)],
            "shuffled_source_paid_p50": shuffled_source_paid[int(0.50 * RANDOM_TRIALS)],
            "shuffled_source_paid_p95": shuffled_source_paid[int(0.95 * RANDOM_TRIALS)],
        },
        "decision": {
            "next_blocker": "nearest-mark offsets are small, but mark identity remains expensive",
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v5_source_endpoint_memory_gate": rel(EXECUTABLE_V5_GATE),
            "one_sided_source_boundary_program_script": rel(ONE_SIDED_SCRIPT),
            "source_boundary_candidate_program_script": rel(SOURCE_BOUNDARY_SCRIPT),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "v5_near_source_mark_offset_gate.v1",
        "scope": "analysis_only_v5_near_source_mark_offset",
        "summary": summary | {
            "promoted": promoted,
            "top_source_offset_examples": sorted(
                rows,
                key=lambda row: (abs(int(row["source_offset"])), -float(row["copy_hint_rank_bits"])),
            )[:20],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# V5 Near-Source-Mark Offset Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- V5 fallback copies tested: `{s['fallback_count']}`.",
        f"- Existing copy-hint bits: `{s['fallback_copy_hint_bits']:.3f}`.",
        f"- Median abs source/end offset: `{s['source_offset_abs_median']}` / `{s['end_offset_abs_median']}`.",
        f"- Exact source-mark count: `{s['source_offset_exact_mark_count']}`.",
        f"- Invalid source-offset-only delta: `{s['invalid_source_offset_only_delta']:.3f}`.",
        f"- Paid source mark+offset delta: `{s['paid_source_delta']:.3f}`.",
        f"- Paid end mark+offset delta: `{s['paid_end_delta']:.3f}`.",
        f"- Paid best endpoint+mode delta: `{s['paid_best_endpoint_with_mode_delta']:.3f}`.",
        f"- Shuffled paid-source p05/p50/p95: `{c['shuffled_source_paid_p05']:.3f}` / `{c['shuffled_source_paid_p50']:.3f}` / `{c['shuffled_source_paid_p95']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_V5_NEAR_SOURCE_MARK_OFFSET_PROGRAM`."
            if s["promoted"]
            else "`V5_NEAR_SOURCE_MARK_OFFSET_NOT_PROMOTED`: offset-only is a lower bound that grants mark identity."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final V5 Near-Source-Mark Offset Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested whether the remaining v5 fallback copy hints can be "
        "replaced by a near-mark offset program. The diagnostic signal is real: "
        f"the median absolute source offset is `{s['source_offset_abs_median']}`, "
        f"and `{s['source_offset_exact_mark_count']}/{s['fallback_count']}` fallback "
        "copies start exactly on an existing v5 mark.",
        "",
        "But the decodable program fails. If mark identity is granted for free, "
        f"source offsets would save `{ -s['invalid_source_offset_only_delta']:.3f}` "
        "bits, but after paying the recent-rank identity of the mark, source "
        f"mark+offset costs `{s['paid_source_delta']:.3f}` bits more than the "
        "existing copy-hint tape. End offsets and best-endpoint mode are also worse.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_V5_NEAR_SOURCE_MARK_OFFSET_PROGRAM`."
            if s["promoted"]
            else "`V5_NEAR_SOURCE_MARK_OFFSET_NOT_PROMOTED`."
        ),
        "",
        "The remaining copy-source blocker is not the local offset; it is selecting "
        "which existing mark/source origin to use without granting target content.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_v5_near_source_mark_offset_gate.py](../scripts/01_v5_near_source_mark_offset_gate.py)",
        "- [01_v5_near_source_mark_offset_gate.json](test_results/01_v5_near_source_mark_offset_gate.json)",
        "- [01_v5_near_source_mark_offset_gate.md](test_results/01_v5_near_source_mark_offset_gate.md)",
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
