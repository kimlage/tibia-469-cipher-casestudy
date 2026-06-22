#!/usr/bin/env python3
"""Executable v4 unanchored-copy residual ledger.

This audit does not try a new selector. It consolidates the post-v4 copy
residual: which copy events are solved by both endpoints, which by end-only
anchors, which are start-only weak clues, and which have neither source endpoint
anchored. The purpose is to decide whether the next constructive route should
keep tuning endpoint activation or change representation.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "v4_unanchored_copy_residual_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

ONE_SIDED_SCRIPT = (
    ROOT
    / "analysis"
    / "one_sided_source_boundary_program_audit_20260622"
    / "scripts"
    / "01_one_sided_source_boundary_program_gate.py"
)
EXECUTABLE_V4_GATE = (
    ROOT
    / "analysis"
    / "executable_v4_one_sided_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v4_one_sided_boundary_program_gate.json"
)
CASCADE_GATE = (
    ROOT
    / "analysis"
    / "endpoint_cascade_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_endpoint_cascade_boundary_program_gate.json"
)
OPCOUNT_START_GATE = (
    ROOT
    / "analysis"
    / "book_opcount_start_anchor_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_book_opcount_start_anchor_program_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_v4_unanchored_copy_residual_ledger.json"
MD_OUT = TEST_RESULTS / "01_v4_unanchored_copy_residual_ledger.md"
FINAL_OUT = FRONT / "reports" / "final_v4_unanchored_copy_residual_audit.md"


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


def load_one_sided_module() -> Any:
    spec = importlib.util.spec_from_file_location("one_sided_gate", ONE_SIDED_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ONE_SIDED_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_class(row: dict[str, Any]) -> str:
    if row["both_hit"]:
        return "both_endpoints_anchored"
    if row["end_hit"]:
        return "end_only_promoted_v4"
    if row["start_hit"]:
        return "start_only_weak_not_promoted"
    return "neither_endpoint_anchored"


def summarize_values(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "max": 0.0, "mean": 0.0, "median": 0.0, "sum": 0.0}
    return {
        "count": len(values),
        "max": max(values),
        "mean": mean(values),
        "median": median(values),
        "sum": sum(values),
    }


def top_counter(counter: Counter[Any], n: int = 12) -> list[dict[str, Any]]:
    return [
        {"key": key, "value": value}
        for key, value in counter.most_common(n)
    ]


def make_result() -> dict[str, Any]:
    v4 = load_json(EXECUTABLE_V4_GATE)
    cascade = load_json(CASCADE_GATE)
    opcount_start = load_json(OPCOUNT_START_GATE)
    assert_boundary("executable_v4_one_sided_boundary_program_gate", v4)
    assert_boundary("endpoint_cascade_boundary_program_gate", cascade)
    assert_boundary("book_opcount_start_anchor_program_gate", opcount_start)

    module = load_one_sided_module()
    rows, meta = module.build_event_rows()
    copy_rows = [row for row in rows if row["event_kind"] == "copy"]
    class_counts: Counter[str] = Counter()
    copy_bits_by_class: dict[str, float] = defaultdict(float)
    raw_hint_bits_by_class: dict[str, float] = defaultdict(float)
    length_buckets: dict[str, Counter[str]] = defaultdict(Counter)
    books_by_class: dict[str, Counter[int]] = defaultdict(Counter)
    burden_by_book: dict[int, float] = defaultdict(float)
    unanchored_ledger = []
    start_weak_ledger = []

    for row in copy_rows:
        cls = copy_class(row)
        class_counts[cls] += 1
        raw_hint = float(row["copy_hint_rank_bits"])
        raw_hint_bits_by_class[cls] += raw_hint
        if cls == "both_endpoints_anchored":
            paid = float(row["interval_rank_bits"])
        elif cls == "end_only_promoted_v4":
            paid = float(row["end_rank_bits"])
        else:
            paid = raw_hint
        copy_bits_by_class[cls] += paid
        books_by_class[cls][int(row["book"])] += 1
        length_buckets[cls][str(row["bucket"])] += 1
        if cls in {"start_only_weak_not_promoted", "neither_endpoint_anchored"}:
            burden_by_book[int(row["book"])] += raw_hint
            item = {
                "book": int(row["book"]),
                "bucket": str(row["bucket"]),
                "copy_hint_rank_bits": raw_hint,
                "exact_length": int(row["exact_length"]),
                "op_index": int(row["op_index"]),
                "source": int(row["source"]),
                "source_end": int(row["source_end"]),
                "target_start": int(row["target_start"]),
            }
            if cls == "start_only_weak_not_promoted":
                item["start_rank_bits"] = float(row["start_rank_bits"])
                item["delta_if_start_enabled"] = float(row["start_rank_bits"]) - raw_hint
                start_weak_ledger.append(item)
            else:
                unanchored_ledger.append(item)

    neither_bits = raw_hint_bits_by_class["neither_endpoint_anchored"]
    start_bits = raw_hint_bits_by_class["start_only_weak_not_promoted"]
    fallback_bits = neither_bits + start_bits
    v4_summary = v4["summary"]
    start_gate_summary = opcount_start["summary"]
    route_decision = (
        "representation_change_required_for_unanchored_copy_origin"
        if class_counts["neither_endpoint_anchored"] > class_counts["start_only_weak_not_promoted"]
        and neither_bits > start_bits
        else "start_anchor_activation_remains_primary"
    )

    result = {
        "case_reopened": False,
        "classification": "V4_UNANCHORED_COPY_RESIDUAL_BLOCKER_LEDGER",
        "compression_bound_status": "unchanged",
        "decision": {
            "next_constructive_route": route_decision,
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "book_opcount_start_anchor_program_gate": rel(OPCOUNT_START_GATE),
            "endpoint_cascade_boundary_program_gate": rel(CASCADE_GATE),
            "executable_v4_one_sided_boundary_program_gate": rel(EXECUTABLE_V4_GATE),
            "one_sided_source_boundary_program_script": rel(ONE_SIDED_SCRIPT),
        },
        "ledger": {
            "start_only_weak_not_promoted": sorted(
                start_weak_ledger,
                key=lambda item: item["copy_hint_rank_bits"],
                reverse=True,
            ),
            "neither_endpoint_anchored": sorted(
                unanchored_ledger,
                key=lambda item: item["copy_hint_rank_bits"],
                reverse=True,
            ),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "v4_unanchored_copy_residual_ledger.v1",
        "scope": "analysis_only_v4_unanchored_copy_residual",
        "summary": {
            "book_opcount_start_anchor_classification": opcount_start["classification"],
            "class_counts": dict(class_counts),
            "copy_bits_by_class": dict(copy_bits_by_class),
            "copy_ops": len(copy_rows),
            "fallback_copy_hint_bits_total": fallback_bits,
            "length_bucket_counts_by_class": {
                cls: dict(counter)
                for cls, counter in length_buckets.items()
            },
            "neither_endpoint_copy_hint_bits": neither_bits,
            "neither_endpoint_count": class_counts["neither_endpoint_anchored"],
            "neither_endpoint_hint_bits_summary": summarize_values(
                [item["copy_hint_rank_bits"] for item in unanchored_ledger]
            ),
            "promoted_v4_external_bits_excluding_seed": float(
                v4_summary["v4_external_bits_excluding_seed"]
            ),
            "promoted_v4_residual_bits": float(v4_summary["v4_residual_bits"]),
            "route_decision": route_decision,
            "start_anchor_random_control_cleared": bool(
                opcount_start["control"]["observed_beats_random_p95"]
            ),
            "start_only_count": class_counts["start_only_weak_not_promoted"],
            "start_only_hint_bits": start_bits,
            "start_only_if_enabled_delta_after_declaration": float(
                cascade["summary"]["delta_after_declaration_vs_v4"]
            ),
            "start_only_opcount_le_3_delta_after_declaration": float(
                start_gate_summary["delta_after_declaration_vs_v4"]
            ),
            "top_books_by_remaining_copy_hint_burden": [
                {"book": book, "copy_hint_bits": bits}
                for book, bits in sorted(
                    burden_by_book.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:15]
            ],
            "top_books_neither_endpoint": top_counter(
                books_by_class["neither_endpoint_anchored"]
            ),
            "top_books_start_only": top_counter(
                books_by_class["start_only_weak_not_promoted"]
            ),
        },
        "translation_delta": "NONE",
    }
    return result


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# V4 Unanchored Copy Residual Ledger",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "After executable v4 and the weak start-anchor gates, where is the copy "
        "residual actually concentrated?",
        "",
        "## Summary",
        "",
        f"- Copy ops: `{s['copy_ops']}`.",
        f"- Class counts: `{s['class_counts']}`.",
        f"- Copy bits by class: `{s['copy_bits_by_class']}`.",
        f"- Remaining fallback copy-hint bits: `{s['fallback_copy_hint_bits_total']:.3f}`.",
        f"- Start-only weak count/bits: `{s['start_only_count']}` / `{s['start_only_hint_bits']:.3f}`.",
        f"- Neither-endpoint count/bits: `{s['neither_endpoint_count']}` / `{s['neither_endpoint_copy_hint_bits']:.3f}`.",
        f"- Start-anchor random control cleared: `{s['start_anchor_random_control_cleared']}`.",
        f"- Route decision: `{s['route_decision']}`.",
        "",
        "## Top Remaining Copy-Hint Burden By Book",
        "",
        "| Book | Copy-hint bits |",
        "| ---: | ---: |",
    ]
    for row in s["top_books_by_remaining_copy_hint_burden"]:
        lines.append(f"| `{row['book']}` | `{row['copy_hint_bits']:.3f}` |")
    lines.extend(
        [
            "",
            "## Length Buckets By Class",
            "",
            "```json",
            json.dumps(s["length_bucket_counts_by_class"], indent=2, sort_keys=True),
            "```",
            "",
            "## Decision",
            "",
            "`V4_UNANCHORED_COPY_RESIDUAL_BLOCKER_LEDGER`: v4 remains promoted; "
            "start-only activation remains a weak clue, and the dominant remaining "
            "copy blocker is the neither-endpoint class.",
            "",
            "The next constructive route should not be another endpoint activation "
            "selector. It needs a representation that creates or derives source-side "
            "boundary/chunk-origin marks for neither-endpoint copy intervals, or it "
            "must attack the still-external literal/seed payloads.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final V4 Unanchored Copy Residual Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit consolidates the post-v4 copy residual instead of testing "
        "another selector. Executable v4 solves copy events when both source "
        "endpoints are anchored or when the end endpoint is anchored. The remaining "
        "copy-hint burden splits into start-only weak clues and intervals with "
        "neither endpoint anchored.",
        "",
        f"Class counts are `{s['class_counts']}`. Remaining fallback copy-hint "
        f"cost is `{s['fallback_copy_hint_bits_total']:.3f}` bits: "
        f"`{s['start_only_hint_bits']:.3f}` from start-only weak intervals and "
        f"`{s['neither_endpoint_copy_hint_bits']:.3f}` from neither-endpoint intervals.",
        "",
        "The start-anchor route remains weak: full-fit and op_count-gated variants "
        "reduce v4, but the op_count gate did not beat the random-opcount p95 control. "
        "The dominant remaining copy blocker is therefore not endpoint activation; "
        "it is deriving source-side boundary or chunk-origin structure for the "
        "neither-endpoint class.",
        "",
        "## Decision",
        "",
        "`V4_UNANCHORED_COPY_RESIDUAL_BLOCKER_LEDGER`.",
        "",
        "Next aligned route: representation change for unanchored copy origin. "
        "Do not keep tuning start-only activation unless it adds a new source of "
        "boundary marks or beats controls.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_v4_unanchored_copy_residual_ledger.py](../scripts/01_v4_unanchored_copy_residual_ledger.py)",
        "- [01_v4_unanchored_copy_residual_ledger.json](test_results/01_v4_unanchored_copy_residual_ledger.json)",
        "- [01_v4_unanchored_copy_residual_ledger.md](test_results/01_v4_unanchored_copy_residual_ledger.md)",
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
