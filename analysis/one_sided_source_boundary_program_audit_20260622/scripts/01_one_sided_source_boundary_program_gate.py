#!/usr/bin/env python3
"""One-sided source-boundary program gate.

Executable v3 derives copy source+length only when both source interval
endpoints are in the promoted boundary set. This gate asks whether the fallback
ledger can be reduced when exactly one endpoint is anchored. The anchored
endpoint is rank-coded; exact length remains in the book-level residual
composition, so decoding stays explicit.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "one_sided_source_boundary_program_audit_20260622"
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

JSON_OUT = TEST_RESULTS / "01_one_sided_source_boundary_program_gate.json"
MD_OUT = TEST_RESULTS / "01_one_sided_source_boundary_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_one_sided_source_boundary_program_audit.md"

POLICIES = ["none", "start_first", "end_first", "best_with_mode_bit"]


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


def endpoint_rank_bits(boundaries: set[int], endpoint: int) -> float | None:
    if endpoint not in boundaries:
        return None
    # Recent-first endpoint rank: later source-side boundaries are cheaper.
    return math.log2(1 + sum(1 for mark in boundaries if mark > endpoint))


def build_event_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    module = load_source_module()
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, ledger = grouped_ledger_rows()
    emitted = "".join(books[book] for book in range(10))
    event_boundaries = {0}
    cursor = 0
    for book in range(10):
        cursor += len(books[book])
        event_boundaries.add(cursor)
    rows = []
    rows_by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for book in range(10, 70):
        rendered = []
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
            boundaries = module.build_boundary_systems(
                available,
                local_event_boundaries,
            )["event_plus_surprisal_top20"]
            op_type = str(op["op_type"])
            length = int(op["exact_length"])
            target_start = int(op["target_start"])
            if op_type == "copy":
                source = int(op["copy_source_raw"])
                end = source + length
                bucket = str(op["coarse_type_length_bucket"]).split(":", 1)[1]
                low, high = module.bucket_bounds(bucket, int(op["book_length"]) - target_start)
                both_hit = source in boundaries and end in boundaries and low <= length <= high
                module.boundary_set_global = set(boundaries)
                if both_hit:
                    interval_rank = module.long_recent_rank(sorted(boundaries), source, length, low, high)
                    interval_rank_bits = math.log2(interval_rank)
                else:
                    interval_rank_bits = None
                row = {
                    "book": book,
                    "bucket": bucket,
                    "both_hit": both_hit,
                    "copy_hint_rank_bits": float(op["copy_hint_rank_bits"]),
                    "end_hit": end in boundaries,
                    "end_rank_bits": endpoint_rank_bits(boundaries, end),
                    "event_kind": "copy",
                    "exact_length": length,
                    "interval_rank_bits": interval_rank_bits,
                    "op_index": int(op["op_index"]),
                    "source": source,
                    "source_end": end,
                    "start_hit": source in boundaries,
                    "start_rank_bits": endpoint_rank_bits(boundaries, source),
                    "target_start": target_start,
                }
            else:
                row = {
                    "book": book,
                    "event_kind": "literal",
                    "exact_length": length,
                    "literal_payload_bits": float(op["literal_payload_bits"]),
                    "op_index": int(op["op_index"]),
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
    return rows, {"ledger": ledger, "rows_by_book": rows_by_book, "truth_by_book": by_book}


def composition_count(module: Any, unknown_rows: list[dict[str, Any]], remaining_sum: int) -> int:
    return module.composition_count_for_unknowns(unknown_rows, remaining_sum)


def summarize_policy(
    rows: list[dict[str, Any]],
    meta: dict[str, Any],
    policy: str,
    books: set[int] | None = None,
) -> dict[str, Any]:
    module = load_source_module()
    scoped_rows = [row for row in rows if books is None or int(row["book"]) in books]
    copy_rows = [row for row in scoped_rows if row["event_kind"] == "copy"]
    literal_rows = [row for row in scoped_rows if row["event_kind"] == "literal"]
    copy_bits = 0.0
    v3_copy_bits = 0.0
    known_by_key = set()
    v3_known_by_key = set()
    class_counts = defaultdict(int)
    for row in copy_rows:
        key = (int(row["book"]), int(row["op_index"]))
        if row["both_hit"]:
            copy_bits += float(row["interval_rank_bits"])
            v3_copy_bits += float(row["interval_rank_bits"])
            known_by_key.add(key)
            v3_known_by_key.add(key)
            class_counts["both"] += 1
            continue
        v3_copy_bits += float(row["copy_hint_rank_bits"])
        start_bits = row["start_rank_bits"]
        end_bits = row["end_rank_bits"]
        chosen = None
        if policy == "start_first" and start_bits is not None:
            chosen = ("start", float(start_bits))
        elif policy == "end_first" and end_bits is not None:
            chosen = ("end", float(end_bits))
        elif policy == "best_with_mode_bit":
            options = []
            if start_bits is not None:
                options.append(("start", float(start_bits) + 1.0))
            if end_bits is not None:
                options.append(("end", float(end_bits) + 1.0))
            if options:
                chosen = min(options, key=lambda item: item[1])
        if chosen is not None and policy != "none":
            copy_bits += chosen[1]
            class_counts[f"one_sided_{chosen[0]}"] += 1
            # The endpoint is known, but exact length remains in composition.
        else:
            copy_bits += float(row["copy_hint_rank_bits"])
            class_counts["fallback"] += 1
    composition_bits = 0.0
    v3_composition_bits = 0.0
    for book, scored_rows in meta["rows_by_book"].items():
        if books is not None and int(book) not in books:
            continue
        truth = meta["truth_by_book"][book]
        known_sum = 0
        unknown = []
        for scored, op in zip(scored_rows, truth):
            key = (int(scored["book"]), int(scored["op_index"]))
            if scored["event_kind"] == "copy" and key in known_by_key:
                known_sum += int(op["exact_length"])
            else:
                unknown.append(op)
        v3_known_sum = 0
        v3_unknown = []
        for scored, op in zip(scored_rows, truth):
            key = (int(scored["book"]), int(scored["op_index"]))
            if scored["event_kind"] == "copy" and key in v3_known_by_key:
                v3_known_sum += int(op["exact_length"])
            else:
                v3_unknown.append(op)
        remaining = int(truth[0]["book_length"]) - known_sum
        composition_bits += math.log2(composition_count(module, unknown, remaining))
        v3_remaining = int(truth[0]["book_length"]) - v3_known_sum
        v3_composition_bits += math.log2(composition_count(module, v3_unknown, v3_remaining))
    literal_bits = sum(float(row["literal_payload_bits"]) for row in literal_rows)
    total = copy_bits + composition_bits + literal_bits
    v3_subset_total = v3_copy_bits + v3_composition_bits + literal_bits
    return {
        "class_counts": dict(class_counts),
        "composition_bits": composition_bits,
        "copy_bits": copy_bits,
        "copy_ops": len(copy_rows),
        "delta_vs_v3_residual_bits": total - v3_subset_total,
        "literal_payload_bits": literal_bits,
        "policy": policy,
        "residual_bits": total,
        "v3_residual_bits": v3_subset_total,
    }


def make_result() -> dict[str, Any]:
    v3 = load_json(EXECUTABLE_V3_GATE)
    assert_boundary("executable_v3_source_boundary_program_gate", v3)
    rows, meta = build_event_rows()
    policy_summaries = [
        summarize_policy(rows, meta, policy)
        for policy in POLICIES
    ]
    best = min(policy_summaries, key=lambda row: row["residual_bits"])
    declaration_bits = math.log2(len(POLICIES))
    prefix_rows = []
    positive_splits = 0
    total_prefix_delta = 0.0
    for cutoff in [20, 30, 40, 50, 60]:
        train_books = set(range(10, cutoff))
        test_books = set(range(cutoff, 70))
        train_scored = [
            summarize_policy(rows, meta, policy, books=train_books)
            for policy in POLICIES
        ]
        selected = min(train_scored, key=lambda item: item["residual_bits"])
        test = summarize_policy(rows, meta, selected["policy"], books=test_books)
        if test["delta_vs_v3_residual_bits"] < 0:
            positive_splits += 1
        total_prefix_delta += float(test["delta_vs_v3_residual_bits"])
        prefix_rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": selected["policy"],
                "test_delta_vs_v3": test["delta_vs_v3_residual_bits"],
                "test_residual_bits": test["residual_bits"],
                "test_class_counts": test["class_counts"],
                "train_delta_vs_v3": selected["delta_vs_v3_residual_bits"],
                "train_residual_bits": selected["residual_bits"],
            }
        )
    one_sided_counts = {
        "start_hit_only": sum(
            1 for row in rows
            if row.get("event_kind") == "copy"
            and not row["both_hit"]
            and row["start_hit"]
            and not row["end_hit"]
        ),
        "end_hit_only": sum(
            1 for row in rows
            if row.get("event_kind") == "copy"
            and not row["both_hit"]
            and row["end_hit"]
            and not row["start_hit"]
        ),
        "both_missing": sum(
            1 for row in rows
            if row.get("event_kind") == "copy"
            and not row["both_hit"]
            and not row["start_hit"]
            and not row["end_hit"]
        ),
        "both_hit": sum(1 for row in rows if row.get("event_kind") == "copy" and row["both_hit"]),
    }
    promoted = (
        best["delta_vs_v3_residual_bits"] + declaration_bits < 0
        and positive_splits >= 4
        and total_prefix_delta < 0
    )
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_ONE_SIDED_SOURCE_BOUNDARY_PROGRAM"
            if promoted
            else "one_sided_source_boundary_not_promoted"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "one_sided_source_boundary_promoted": promoted,
            "next_blocker": (
                "one-sided source boundary anchors are insufficient to reduce v3"
                if not promoted
                else "remaining intervals without useful one-sided anchors"
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
        "one_sided_counts": one_sided_counts,
        "plaintext_claim": False,
        "policy_summaries": policy_summaries,
        "prefix_selection_rows": prefix_rows,
        "row0_status": "unchanged_exogenous",
        "schema": "one_sided_source_boundary_program_gate.v1",
        "scope": "analysis_only_one_sided_source_boundary_program",
        "summary": best | {
            "declaration_bits_policy": declaration_bits,
            "delta_after_policy_declaration": best["delta_vs_v3_residual_bits"] + declaration_bits,
            "positive_prefix_selected_splits": positive_splits,
            "promoted": promoted,
            "total_prefix_selected_delta": total_prefix_delta,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    counts = result["one_sided_counts"]
    lines = [
        "# One-Sided Source-Boundary Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can fallback copy intervals be reduced when only one source-side endpoint "
        "is in the promoted boundary set?",
        "",
        "## Endpoint Coverage",
        "",
        f"- Both endpoints hit: `{counts['both_hit']}`.",
        f"- Start-only hits: `{counts['start_hit_only']}`.",
        f"- End-only hits: `{counts['end_hit_only']}`.",
        f"- Both endpoints missing: `{counts['both_missing']}`.",
        f"- Best-policy delta after declaration: `{s['delta_after_policy_declaration']:.3f}` bits.",
        f"- Prefix-selected positive splits: `{s['positive_prefix_selected_splits']}/5`.",
        f"- Prefix-selected aggregate delta: `{s['total_prefix_selected_delta']:.3f}` bits.",
        "",
        "## Policy Costs",
        "",
        "| Policy | Residual bits | Delta vs v3 | Copy bits | Composition bits | Classes |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["policy_summaries"]:
        lines.append(
            f"| `{row['policy']}` | `{row['residual_bits']:.3f}` | "
            f"`{row['delta_vs_v3_residual_bits']:.3f}` | `{row['copy_bits']:.3f}` | "
            f"`{row['composition_bits']:.3f}` | `{row['class_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Selection",
            "",
            "| Cutoff | Selected policy | Train delta | Test delta | Test classes |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["prefix_selection_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_policy']}` | "
            f"`{row['train_delta_vs_v3']:.3f}` | `{row['test_delta_vs_v3']:.3f}` | "
            f"`{row['test_class_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_ONE_SIDED_SOURCE_BOUNDARY_PROGRAM`: one-sided anchors "
                "reduce the v3 ledger."
                if s["promoted"]
                else "`one_sided_source_boundary_not_promoted`: one-sided anchors "
                "are available, but paying endpoint ranks without deriving length "
                "does not reduce the v3 ledger."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    counts = result["one_sided_counts"]
    lines = [
        "# Final One-Sided Source-Boundary Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested a decodable partial-anchor extension to v3. If one "
        "source endpoint is in the promoted boundary set, that endpoint can be "
        "rank-coded while exact length remains in the residual composition.",
        "",
        f"Endpoint coverage is `{counts['both_hit']}` both-endpoint hits, "
        f"`{counts['start_hit_only']}` start-only hits, `{counts['end_hit_only']}` "
        f"end-only hits, and `{counts['both_missing']}` intervals with neither "
        "endpoint in the boundary set.",
        "",
        f"The best policy is `{s['policy']}` at `{s['residual_bits']:.3f}` bits, "
        f"delta `{s['delta_vs_v3_residual_bits']:.3f}` versus v3. After charging "
        f"`{s['declaration_bits_policy']:.3f}` bits to declare one of `{len(POLICIES)}` "
        f"policies, the delta remains `{s['delta_after_policy_declaration']:.3f}`. "
        f"Prefix-only policy selection improves `{s['positive_prefix_selected_splits']}/5` "
        f"splits with aggregate delta `{s['total_prefix_selected_delta']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_ONE_SIDED_SOURCE_BOUNDARY_PROGRAM`."
            if s["promoted"]
            else "`one_sided_source_boundary_not_promoted`. One-sided anchors "
            "do not reduce the executable v3 ledger because length remains a "
            "separate residual and endpoint ranks cost more than they save."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_one_sided_source_boundary_program_gate.py](../scripts/01_one_sided_source_boundary_program_gate.py)",
        "- [01_one_sided_source_boundary_program_gate.json](test_results/01_one_sided_source_boundary_program_gate.json)",
        "- [01_one_sided_source_boundary_program_gate.md](test_results/01_one_sided_source_boundary_program_gate.md)",
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
