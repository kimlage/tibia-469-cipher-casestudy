#!/usr/bin/env python3
"""Test whether Chayenne seed subspans are used as copy-source intervals.

Previous gates showed that Chayenne validates subspans inside seed books, but
not replay-event boundaries. This gate tests the next more causal question:
do those subspans actually act as source intervals in the executable decoder's
copy operations, above same-length random seed subspans?
"""

from __future__ import annotations

import json
import math
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/chayenne_copy_source_overlap_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_chayenne_copy_source_overlap_gate.json"
MD_OUT = OUT_DIR / "01_chayenne_copy_source_overlap_gate.md"
FINAL_OUT = FRONT / "reports/final_chayenne_copy_source_overlap_audit.md"

BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
UNIFIED_LEDGER = ROOT / "analysis/minimal_external_tape_program_audit_20260622/reports/test_results/02_unified_external_tape_ledger.json"
REUSE_GATE = ROOT / "analysis/chayenne_seed_subspan_reuse_audit_20260622/reports/test_results/01_chayenne_seed_subspan_reuse_gate.json"

RNG_SEED = 46920260622
CONTROL_TRIALS = 5000


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
    if data.get("row0_status") != "unchanged_exogenous":
        raise RuntimeError(f"{name} changed row0")


def seed_stream_len(books: dict[int, str]) -> int:
    return sum(len(books[index]) for index in range(10))


def overlap_len(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start))


def copy_source_rows(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in ledger["ledger_rows"]:
        if row["op_type"] != "copy":
            continue
        source = int(row["copy_source_raw"])
        length = int(row["exact_length"])
        rows.append(
            {
                "book": int(row["book"]),
                "op_index": int(row["op_index"]),
                "source_start": source,
                "source_end": source + length,
                "length": length,
                "target_start": int(row["target_start"]),
            }
        )
    return rows


def score_spans(copy_rows: list[dict[str, Any]], spans: list[dict[str, Any]]) -> dict[str, Any]:
    hit_rows = []
    total_overlap = 0
    fully_contained = 0
    starts_inside = 0
    for copy in copy_rows:
        overlaps = []
        for span in spans:
            amount = overlap_len(copy["source_start"], copy["source_end"], span["start"], span["end"])
            if amount:
                overlaps.append(
                    {
                        "span_label": span["label"],
                        "span_start": span["start"],
                        "span_end": span["end"],
                        "overlap_digits": amount,
                    }
                )
        if not overlaps:
            continue
        total = sum(item["overlap_digits"] for item in overlaps)
        total_overlap += total
        if any(copy["source_start"] >= span["start"] and copy["source_end"] <= span["end"] for span in spans):
            fully_contained += 1
        if any(span["start"] <= copy["source_start"] < span["end"] for span in spans):
            starts_inside += 1
        hit_rows.append({**copy, "overlaps": overlaps, "total_overlap_digits": total})
    return {
        "copy_rows_with_overlap": len(hit_rows),
        "total_overlap_digits": total_overlap,
        "fully_contained_copy_rows": fully_contained,
        "source_starts_inside_spans": starts_inside,
        "hit_rows": hit_rows,
    }


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def random_spans(seed_len: int, lengths: list[int], rng: random.Random) -> list[dict[str, Any]]:
    spans = []
    for index, length in enumerate(lengths):
        start = rng.randrange(0, seed_len - length + 1)
        spans.append({"label": f"random_{index}", "start": start, "end": start + length})
    return spans


def control(copy_rows: list[dict[str, Any]], seed_len: int, lengths: list[int]) -> dict[str, Any]:
    rng = random.Random(RNG_SEED)
    rows = []
    for _ in range(CONTROL_TRIALS):
        spans = random_spans(seed_len, lengths, rng)
        rows.append(score_spans(copy_rows, spans))
    return {
        "trials": CONTROL_TRIALS,
        "copy_rows_with_overlap_p95": quantile([row["copy_rows_with_overlap"] for row in rows], 0.95),
        "copy_rows_with_overlap_p99": quantile([row["copy_rows_with_overlap"] for row in rows], 0.99),
        "total_overlap_digits_p95": quantile([row["total_overlap_digits"] for row in rows], 0.95),
        "total_overlap_digits_p99": quantile([row["total_overlap_digits"] for row in rows], 0.99),
        "source_starts_inside_spans_p95": quantile([row["source_starts_inside_spans"] for row in rows], 0.95),
        "fully_contained_copy_rows_p95": quantile([row["fully_contained_copy_rows"] for row in rows], 0.95),
    }


def make_result() -> dict[str, Any]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    ledger = load_json(UNIFIED_LEDGER)
    reuse = load_json(REUSE_GATE)
    assert_boundary("ledger", ledger)
    assert_boundary("reuse", reuse)
    if reuse["classification"] != "chayenne_seed_subspan_external_cover_clue_not_reuse_program":
        raise RuntimeError("Chayenne seed subspan reuse gate not in expected state")

    spans = []
    for row in reuse["observed"]["span_rows"]:
        start = int(row["seed_global_start"])
        spans.append(
            {
                "label": row["label"],
                "start": start,
                "end": start + int(row["length"]),
                "length": int(row["length"]),
                "seed_location": row["seed_location"],
            }
        )
    copy_rows = copy_source_rows(ledger)
    observed = score_spans(copy_rows, spans)
    controls = control(copy_rows, seed_stream_len(books), [span["length"] for span in spans])

    promoted = (
        observed["copy_rows_with_overlap"] > controls["copy_rows_with_overlap_p95"]
        and observed["total_overlap_digits"] > controls["total_overlap_digits_p95"]
    )
    classification = (
        "PROMOTED_CHAYENNE_COPY_SOURCE_OVERLAP_CLUE"
        if promoted
        else "chayenne_copy_source_overlap_not_promoted"
    )
    return {
        "schema": "chayenne_copy_source_overlap_gate.v1",
        "scope": "analysis_only_copy_source_overlap_for_external_holdout_spans",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {
            "books_digits": str(BOOKS_DIGITS.relative_to(ROOT)),
            "unified_external_tape_ledger": str(UNIFIED_LEDGER.relative_to(ROOT)),
            "chayenne_seed_subspan_reuse": str(REUSE_GATE.relative_to(ROOT)),
        },
        "summary": {
            "copy_rows": len(copy_rows),
            "chayenne_spans": len(spans),
            "copy_rows_with_overlap": observed["copy_rows_with_overlap"],
            "total_overlap_digits": observed["total_overlap_digits"],
            "source_starts_inside_spans": observed["source_starts_inside_spans"],
            "fully_contained_copy_rows": observed["fully_contained_copy_rows"],
            "promoted": promoted,
        },
        "chayenne_spans": spans,
        "observed": observed,
        "controls": controls,
        "decision": {
            "copy_source_overlap_clue_promoted": promoted,
            "event_policy_promoted": False,
            "origin_source_promoted": False,
            "external_field_reduced": False,
            "v9_reduction_bits": 0.0,
            "reason": (
                "Chayenne seed subspans are overrepresented as copy-source intervals"
                if promoted
                else "Chayenne seed subspans are not overrepresented as copy-source intervals after same-length controls"
            ),
            "next_blocker": "copy-source overlap alone does not derive source choice, event policy, or innovation origin",
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Chayenne Copy Source Overlap Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "| Metric | Observed | Control |",
        "| --- | ---: | ---: |",
        f"| Copy rows with overlap | `{s['copy_rows_with_overlap']}` | p95 `{c['copy_rows_with_overlap_p95']}`, p99 `{c['copy_rows_with_overlap_p99']}` |",
        f"| Total overlap digits | `{s['total_overlap_digits']}` | p95 `{c['total_overlap_digits_p95']}`, p99 `{c['total_overlap_digits_p99']}` |",
        f"| Source starts inside spans | `{s['source_starts_inside_spans']}` | p95 `{c['source_starts_inside_spans_p95']}` |",
        f"| Fully contained copy rows | `{s['fully_contained_copy_rows']}` | p95 `{c['fully_contained_copy_rows_p95']}` |",
        "",
        "## Hit Rows",
        "",
        "| Book | Op | Source Span | Length | Overlap Digits |",
        "| ---: | ---: | --- | ---: | ---: |",
    ]
    for row in result["observed"]["hit_rows"][:30]:
        lines.append(
            f"| `{row['book']}` | `{row['op_index']}` | `{row['source_start']}-{row['source_end']}` | `{row['length']}` | `{row['total_overlap_digits']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{result['decision']['reason']}`",
            "",
            f"Next blocker: `{result['decision']['next_blocker']}`",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Chayenne Copy Source Overlap Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "The Chayenne seed subspans were tested against executable decoder copy-source intervals.",
        f"They overlap `{s['copy_rows_with_overlap']}` copy-source rows for `{s['total_overlap_digits']}` source digits.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "No source-choice rule, event policy, origin source, v9 reduction, plaintext, or translation is promoted.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_chayenne_copy_source_overlap_gate.py](../scripts/01_chayenne_copy_source_overlap_gate.py)",
        "- [01_chayenne_copy_source_overlap_gate.json](test_results/01_chayenne_copy_source_overlap_gate.json)",
        "- [01_chayenne_copy_source_overlap_gate.md](test_results/01_chayenne_copy_source_overlap_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
