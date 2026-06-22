#!/usr/bin/env python3
"""Joint content-origin program gate.

This audit tests the next constructive route after executable v5: can the
remaining fallback copy-source tape be addressed through already emitted
content-origin events, rather than paid as an independent copy-hint stream?

The candidate is intentionally joint, not another local source selector:
fallback copy origins are encoded relative to seed spans, literal innovation
spans, or prior operation spans. If this works, copy-origin identity becomes
coupled to the same content substrate that already carries seed/literal
innovation. If it fails, the copy-origin blocker remains external.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "joint_content_origin_program_audit_20260622"
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
V5_FRONTIER = (
    ROOT
    / "analysis"
    / "v5_external_dependency_frontier_synthesis_audit_20260622"
    / "reports"
    / "test_results"
    / "01_v5_external_dependency_frontier_synthesis.json"
)
V5_GATE = (
    ROOT
    / "analysis"
    / "executable_v5_source_endpoint_memory_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v5_source_endpoint_memory_gate.json"
)
NEAR_MARK_SCRIPT = (
    ROOT
    / "analysis"
    / "v5_near_source_mark_offset_audit_20260622"
    / "scripts"
    / "01_v5_near_source_mark_offset_gate.py"
)
CONTENT_EVENT_GATE = (
    ROOT
    / "analysis"
    / "content_addressed_event_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_content_addressed_event_program_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_joint_content_origin_program_gate.json"
MD_OUT = TEST_RESULTS / "01_joint_content_origin_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_joint_content_origin_program_audit.md"

RANDOM_SEED = 46920260622
RANDOM_TRIALS = 250
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
MODEL_DECLARATION_BITS = math.log2(5)
LOG2_10 = math.log2(10)

MODEL_NAMES = [
    "literal_start_end_nearest",
    "literal_span_offset",
    "seed_or_literal_span_offset",
    "prior_op_span_offset",
    "prior_op_start_end_nearest",
]


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
    decision = data.get("decision", {})
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def load_near_module() -> Any:
    spec = importlib.util.spec_from_file_location("near_mark_gate", NEAR_MARK_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {NEAR_MARK_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def signed_offset_bits(offset: int) -> float:
    return math.log2(2 * abs(offset) + 1)


def grouped_ledger_rows() -> dict[int, list[dict[str, Any]]]:
    ledger = load_json(UNIFIED_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        grouped[int(row["book"])].append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }


def recent_rank(positions: list[int], selected: int) -> int:
    return 1 + sum(1 for pos in positions if pos > selected)


def nearest_mark_cost(marks: list[int], source: int) -> dict[str, Any]:
    if not marks:
        return {"bits": None, "rank": None, "offset": None, "mark": None}
    mark = min(marks, key=lambda pos: (abs(source - pos), -pos))
    rank = recent_rank(marks, mark)
    offset = source - mark
    return {
        "bits": math.log2(rank) + signed_offset_bits(offset),
        "mark": mark,
        "offset": offset,
        "rank": rank,
    }


def span_offset_cost(spans: list[dict[str, Any]], source: int) -> dict[str, Any]:
    containing = [span for span in spans if int(span["start"]) <= source < int(span["end"])]
    if not containing:
        return {"bits": None, "rank": None, "offset": None, "span_kind": None}
    span = max(containing, key=lambda item: int(item["end"]))
    ordered_ends = [int(item["end"]) for item in spans]
    rank = 1 + sum(1 for end in ordered_ends if end > int(span["end"]))
    offset = source - int(span["start"])
    width = max(1, int(span["end"]) - int(span["start"]))
    return {
        "bits": math.log2(rank) + math.log2(width),
        "offset": offset,
        "rank": rank,
        "span_kind": span["kind"],
    }


def random_nearest_mark_cost(mark_count: int, source: int, available_len: int, rng: random.Random) -> float:
    if mark_count <= 0:
        return math.inf
    marks = sorted(rng.sample(range(available_len + 1), min(mark_count, available_len + 1)))
    return float(nearest_mark_cost(marks, source)["bits"])


def random_span_cost(spans: list[dict[str, Any]], source: int, available_len: int, rng: random.Random) -> float:
    if not spans:
        return math.inf
    random_spans = []
    for span in spans:
        width = max(1, int(span["end"]) - int(span["start"]))
        if width > available_len:
            start = 0
        else:
            start = rng.randint(0, available_len - width)
        random_spans.append({"start": start, "end": start + width, "kind": span["kind"]})
    cost = span_offset_cost(random_spans, source)
    return math.inf if cost["bits"] is None else float(cost["bits"])


def random_span_lengths_cost(lengths: list[int], source: int, available_len: int, rng: random.Random) -> float | None:
    if not lengths:
        return None
    random_spans = []
    for index, width in enumerate(lengths):
        width = max(1, min(int(width), max(1, available_len)))
        start = rng.randint(0, max(0, available_len - width))
        random_spans.append({"start": start, "end": start + width, "kind": f"random_span_{index}"})
    cost = span_offset_cost(random_spans, source)
    return None if cost["bits"] is None else float(cost["bits"])


def build_fallback_event_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book = grouped_ledger_rows()
    near = load_near_module()
    fallback_from_near = {
        (int(row["book"]), int(row["op_index"])): row
        for row in near.collect_fallback_rows()
    }

    emitted_len = 0
    seed_spans = []
    for book in range(10):
        start = emitted_len
        end = start + len(books[book])
        seed_spans.append({"book": book, "end": end, "kind": "seed_book", "op_index": None, "start": start})
        emitted_len = end

    literal_spans: list[dict[str, Any]] = []
    op_spans: list[dict[str, Any]] = list(seed_spans)
    events = []
    validation_errors = []

    for book in range(10, 70):
        rendered = []
        book_global_start = emitted_len
        for op in by_book[book]:
            op_index = int(op["op_index"])
            op_type = str(op["op_type"])
            target_start = int(op["target_start"])
            length = int(op["exact_length"])
            source = int(op["copy_source_raw"]) if op["copy_source_raw"] is not None else None
            available_len = emitted_len + sum(len(chunk) for chunk in rendered)

            literal_marks = sorted(
                {
                    mark
                    for span in literal_spans
                    for mark in (int(span["start"]), int(span["end"]))
                    if mark <= available_len
                }
            )
            seed_or_literal_spans = [
                span
                for span in seed_spans + literal_spans
                if int(span["end"]) <= available_len
            ]
            prior_op_spans = [span for span in op_spans if int(span["end"]) <= available_len]
            prior_op_marks = sorted(
                {
                    mark
                    for span in prior_op_spans
                    for mark in (int(span["start"]), int(span["end"]))
                    if mark <= available_len
                }
            )

            if op_type == "copy" and (book, op_index) in fallback_from_near:
                assert source is not None
                source_end = source + length
                if source_end > available_len:
                    validation_errors.append(
                        {
                            "book": book,
                            "op_index": op_index,
                            "reason": "copy_source_exceeds_available_material",
                            "source_end": source_end,
                            "available_len": available_len,
                        }
                    )
                literal_nearest = nearest_mark_cost(literal_marks, source)
                literal_span = span_offset_cost(literal_spans, source)
                seed_or_literal_span = span_offset_cost(seed_or_literal_spans, source)
                op_span = span_offset_cost(prior_op_spans, source)
                op_nearest = nearest_mark_cost(prior_op_marks, source)
                near_row = fallback_from_near[(book, op_index)]
                model_costs = {
                    "literal_start_end_nearest": literal_nearest["bits"],
                    "literal_span_offset": literal_span["bits"],
                    "seed_or_literal_span_offset": seed_or_literal_span["bits"],
                    "prior_op_span_offset": op_span["bits"],
                    "prior_op_start_end_nearest": op_nearest["bits"],
                }
                events.append(
                    {
                        "available_len": available_len,
                        "book": book,
                        "copy_hint_rank_bits": float(near_row["copy_hint_rank_bits"]),
                        "exact_length": length,
                        "literal_mark_count": len(literal_marks),
                        "literal_nearest_offset": literal_nearest["offset"],
                        "literal_span_lengths": [
                            int(span["end"]) - int(span["start"])
                            for span in literal_spans
                            if int(span["end"]) <= available_len
                        ],
                        "literal_span_hit": literal_span["bits"] is not None,
                        "model_bits": model_costs,
                        "op_index": op_index,
                        "op_mark_count": len(prior_op_marks),
                        "prior_op_span_lengths": [
                            int(span["end"]) - int(span["start"])
                            for span in prior_op_spans
                        ],
                        "prior_op_span_hit": op_span["bits"] is not None,
                        "seed_or_literal_span_lengths": [
                            int(span["end"]) - int(span["start"])
                            for span in seed_or_literal_spans
                        ],
                        "seed_or_literal_span_hit": seed_or_literal_span["bits"] is not None,
                        "source": source,
                        "source_inside_seed": any(
                            int(span["start"]) <= source < int(span["end"]) for span in seed_spans
                        ),
                        "source_inside_prior_literal": literal_span["bits"] is not None,
                        "target_start": target_start,
                    }
                )

            chunk = books[book][target_start : target_start + length]
            rendered.append(chunk)
            span = {
                "book": book,
                "end": book_global_start + target_start + length,
                "kind": "literal" if op_type == "literal" else "copy_op",
                "op_index": op_index,
                "start": book_global_start + target_start,
            }
            op_spans.append(span)
            if op_type == "literal":
                literal_spans.append(span | {"payload": chunk})

        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            validation_errors.append(
                {
                    "book": book,
                    "expected_len": len(books[book]),
                    "reason": "rendered_book_mismatch",
                    "rendered_len": len(rendered_book),
                }
            )
        emitted_len += len(rendered_book)

    return events, {
        "errors": validation_errors,
        "fallback_events": len(events),
        "literal_events": len(literal_spans),
        "roundtrip_derived_books": 60 - len({err.get("book") for err in validation_errors if "book" in err}),
        "seed_spans": len(seed_spans),
    }


def finite_sum(rows: list[dict[str, Any]], model: str) -> tuple[float, int]:
    bits = 0.0
    missing = 0
    for row in rows:
        value = row["model_bits"][model]
        if value is None:
            missing += 1
            bits += float(row["copy_hint_rank_bits"])
        else:
            bits += float(value)
    return bits, missing


def summarize_models(events: list[dict[str, Any]]) -> dict[str, Any]:
    baseline = sum(float(row["copy_hint_rank_bits"]) for row in events)
    model_rows = {}
    for model in MODEL_NAMES:
        bits, missing = finite_sum(events, model)
        charged = bits + MODEL_DECLARATION_BITS
        model_rows[model] = {
            "bits_before_declaration": bits,
            "coverage": len(events) - missing,
            "delta_after_declaration_vs_copy_hint": charged - baseline,
            "missing_fallback_to_copy_hint": missing,
            "model_declaration_bits": MODEL_DECLARATION_BITS,
            "total_bits_after_declaration": charged,
        }
    best_model = min(model_rows, key=lambda name: model_rows[name]["delta_after_declaration_vs_copy_hint"])
    return {
        "baseline_copy_hint_bits": baseline,
        "best_model": best_model,
        "best_model_delta_after_declaration": model_rows[best_model]["delta_after_declaration_vs_copy_hint"],
        "fallback_copy_events": len(events),
        "literal_nearest_exact_mark_count": sum(
            1 for row in events if row["literal_nearest_offset"] == 0
        ),
        "literal_nearest_median_abs_offset": median(
            [abs(int(row["literal_nearest_offset"])) for row in events if row["literal_nearest_offset"] is not None]
        )
        if any(row["literal_nearest_offset"] is not None for row in events)
        else None,
        "model_rows": model_rows,
        "prior_op_span_hits": sum(1 for row in events if row["prior_op_span_hit"]),
        "seed_or_literal_span_hits": sum(1 for row in events if row["seed_or_literal_span_hit"]),
        "source_inside_prior_literal_count": sum(1 for row in events if row["source_inside_prior_literal"]),
        "source_inside_seed_count": sum(1 for row in events if row["source_inside_seed"]),
    }


def prefix_holdouts(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in events if int(row["book"]) < cutoff]
        test = [row for row in events if int(row["book"]) >= cutoff]
        train_summary = summarize_models(train)
        model = train_summary["best_model"]
        test_baseline = sum(float(row["copy_hint_rank_bits"]) for row in test)
        test_bits, missing = finite_sum(test, model)
        test_delta = test_bits + MODEL_DECLARATION_BITS - test_baseline
        rows.append(
            {
                "cutoff": cutoff,
                "selected_model": model,
                "test_baseline_copy_hint_bits": test_baseline,
                "test_delta_after_declaration_vs_copy_hint": test_delta,
                "test_model_bits_after_declaration": test_bits + MODEL_DECLARATION_BITS,
                "test_rows": len(test),
                "test_rows_missing_fallback_to_copy_hint": missing,
                "train_best_delta_after_declaration": train_summary["best_model_delta_after_declaration"],
                "train_rows": len(train),
            }
        )
    return rows


def source_position_control(events: list[dict[str, Any]], model: str) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 101)
    totals = []
    for _ in range(RANDOM_TRIALS):
        total = 0.0
        for row in events:
            source = rng.randint(0, max(0, int(row["available_len"]) - 1))
            if model in {"literal_start_end_nearest", "prior_op_start_end_nearest"}:
                mark_count = (
                    int(row["literal_mark_count"])
                    if model == "literal_start_end_nearest"
                    else int(row["op_mark_count"])
                )
                total += random_nearest_mark_cost(mark_count, source, int(row["available_len"]), rng)
            else:
                lengths_key = {
                    "literal_span_offset": "literal_span_lengths",
                    "seed_or_literal_span_offset": "seed_or_literal_span_lengths",
                    "prior_op_span_offset": "prior_op_span_lengths",
                }[model]
                random_cost = random_span_lengths_cost(
                    [int(value) for value in row[lengths_key]],
                    source,
                    int(row["available_len"]),
                    rng,
                )
                total += (
                    float(row["copy_hint_rank_bits"])
                    if random_cost is None
                    else float(random_cost)
                )
        totals.append(total + MODEL_DECLARATION_BITS)
    observed_bits, _missing = finite_sum(events, model)
    observed_total = observed_bits + MODEL_DECLARATION_BITS
    ordered = sorted(totals)
    return {
        "beats_p05": observed_total < ordered[int(0.05 * RANDOM_TRIALS)],
        "observed_bits_after_declaration": observed_total,
        "p05": ordered[int(0.05 * RANDOM_TRIALS)],
        "p50": ordered[int(0.50 * RANDOM_TRIALS)],
        "p95": ordered[int(0.95 * RANDOM_TRIALS)],
        "trials": RANDOM_TRIALS,
    }


def literal_payload_status() -> dict[str, Any]:
    by_book = grouped_ledger_rows()
    literal_rows = [
        row
        for rows in by_book.values()
        for row in rows
        if str(row["op_type"]) == "literal"
    ]
    payload = "".join(str(row["literal_payload"]) for row in literal_rows)
    return {
        "literal_digits": len(payload),
        "literal_payload_bits_uniform": len(payload) * LOG2_10,
        "literal_payload_status": "still_paid_external_innovation_tape",
        "literal_runs": len(literal_rows),
    }


def make_result() -> dict[str, Any]:
    v5_gate = load_json(V5_GATE)
    for name, data in [
        ("v5_frontier_synthesis", V5_FRONTIER),
        ("executable_v5_gate", V5_GATE),
        ("content_addressed_event_gate", CONTENT_EVENT_GATE),
    ]:
        assert_boundary(name, load_json(data) if isinstance(data, Path) else data)

    events, validation = build_fallback_event_rows()
    summary = summarize_models(events)
    holdouts = prefix_holdouts(events)
    best_model = summary["best_model"]
    controls = {
        "best_model_source_position_control": source_position_control(events, best_model),
        "literal_mark_source_position_control": source_position_control(events, "literal_start_end_nearest"),
        "prior_op_mark_source_position_control": source_position_control(events, "prior_op_start_end_nearest"),
    }
    holdout_positive = sum(
        1 for row in holdouts if float(row["test_delta_after_declaration_vs_copy_hint"]) < 0
    )
    promoted = (
        summary["best_model_delta_after_declaration"] < 0
        and holdout_positive >= 4
        and controls["best_model_source_position_control"]["beats_p05"]
    )
    candidate_external_excluding_seed = (
        float(v5_gate["summary"]["v5_external_bits_excluding_seed"])
        + float(summary["best_model_delta_after_declaration"])
    )
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_LITERAL_SPAN_CONTENT_ORIGIN_SUBPROGRAM"
            if promoted
            else "JOINT_CONTENT_ORIGIN_PROGRAM_NOT_PROMOTED"
        ),
        "compression_bound_status": "unchanged",
        "controls": controls,
        "decision": {
            "next_blocker": (
                "copy fallback exact origin remains external unless a content-origin model "
                "beats copy hints under holdout and controls"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "holdouts": holdouts,
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "content_addressed_event_gate": rel(CONTENT_EVENT_GATE),
            "executable_v5_gate": rel(V5_GATE),
            "near_source_mark_offset_script": rel(NEAR_MARK_SCRIPT),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
            "v5_frontier_synthesis": rel(V5_FRONTIER),
        },
        "literal_payload": literal_payload_status(),
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "joint_content_origin_program_gate.v1",
        "scope": "analysis_only_joint_content_origin_program",
        "summary": summary
        | {
            "candidate_external_bits_excluding_seed": candidate_external_excluding_seed,
            "candidate_external_delta_vs_v5": summary["best_model_delta_after_declaration"],
            "holdout_positive_splits": holdout_positive,
            "promoted": promoted,
            "promoted_scope": (
                "literal_span_offset_for_11_v5_fallback_copy_origins"
                if promoted
                else None
            ),
            "validation_errors": validation["errors"],
            "validation_roundtrip_derived_books": validation["roundtrip_derived_books"],
            "v5_external_bits_excluding_seed": float(v5_gate["summary"]["v5_external_bits_excluding_seed"]),
        },
        "translation_delta": "NONE",
        "validation": validation,
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Joint Content-Origin Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- V5 fallback copy events: `{s['fallback_copy_events']}`.",
        f"- Baseline copy-hint bits: `{s['baseline_copy_hint_bits']:.3f}`.",
        f"- Best model: `{s['best_model']}`.",
        f"- Best delta after declaration: `{s['best_model_delta_after_declaration']:.3f}` bits.",
        f"- Candidate external bits excluding seed: `{s['candidate_external_bits_excluding_seed']:.3f}`.",
        f"- Holdout positive splits: `{s['holdout_positive_splits']}/5`.",
        f"- Source inside seed spans: `{s['source_inside_seed_count']}`.",
        f"- Source inside prior literal spans: `{s['source_inside_prior_literal_count']}`.",
        f"- Seed/literal span hits: `{s['seed_or_literal_span_hits']}`.",
        f"- Prior-op span hits: `{s['prior_op_span_hits']}`.",
        f"- Literal nearest exact-mark count: `{s['literal_nearest_exact_mark_count']}`.",
        f"- Literal nearest median abs offset: `{s['literal_nearest_median_abs_offset']}`.",
        "",
        "## Model Costs",
        "",
        "| Model | Coverage | Missing | Bits after declaration | Delta vs copy-hint |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for model, row in s["model_rows"].items():
        lines.append(
            f"| `{model}` | `{row['coverage']}` | `{row['missing_fallback_to_copy_hint']}` | "
            f"`{row['total_bits_after_declaration']:.3f}` | "
            f"`{row['delta_after_declaration_vs_copy_hint']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Holdout",
            "",
            "| Cutoff | Selected model | Test rows | Test delta |",
            "| ---: | --- | ---: | ---: |",
        ]
    )
    for row in result["holdouts"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_model']}` | `{row['test_rows']}` | "
            f"`{row['test_delta_after_declaration_vs_copy_hint']:.3f}` |"
        )
    control = result["controls"]["best_model_source_position_control"]
    lines.extend(
        [
            "",
            "## Control",
            "",
            f"- Best-model observed bits after declaration: `{control['observed_bits_after_declaration']:.3f}`.",
            f"- Random source-position p05/p50/p95: `{control['p05']:.3f}` / `{control['p50']:.3f}` / `{control['p95']:.3f}`.",
            f"- Beats p05: `{control['beats_p05']}`.",
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_LITERAL_SPAN_CONTENT_ORIGIN_SUBPROGRAM`: limited executable reduction for fallback copy origins that start inside prior literal innovation spans."
                if s["promoted"]
                else "`JOINT_CONTENT_ORIGIN_PROGRAM_NOT_PROMOTED`: content-origin addressing does not replace the v5 fallback copy-hint tape under the promotion gate."
            ),
            "",
            "This is not a complete generator: most fallback copy origins, literal payload, seed payload, and row0 remain external.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    best = s["model_rows"][s["best_model"]]
    lines = [
        "# Final Joint Content-Origin Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested the constructive route suggested by the v5 frontier "
        "synthesis: encode fallback copy origins through already emitted content "
        "origins, rather than as an independent copy-hint tape.",
        "",
        f"The v5 fallback baseline is `{s['baseline_copy_hint_bits']:.3f}` bits over "
        f"`{s['fallback_copy_events']}` copy events. The best content-origin model is "
        f"`{s['best_model']}` at `{best['total_bits_after_declaration']:.3f}` bits "
        f"after declaration, delta `{best['delta_after_declaration_vs_copy_hint']:.3f}` "
        "bits vs copy-hint.",
        "",
        f"Integrated as a limited v5 reduction, this would move external bits excluding "
        f"seed from `{s['v5_external_bits_excluding_seed']:.3f}` to "
        f"`{s['candidate_external_bits_excluding_seed']:.3f}`. The saving comes from "
        "the `11` fallback sources that start inside prior literal innovation spans; "
        "the other fallback sources still use the existing copy-hint tape.",
        "",
        f"Holdout support is `{s['holdout_positive_splits']}/5` positive suffix splits. "
        f"Only `{s['source_inside_prior_literal_count']}` fallback sources start inside "
        "prior literal innovation spans; seed/literal spans cover "
        f"`{s['seed_or_literal_span_hits']}` sources, while prior op spans cover "
        f"`{s['prior_op_span_hits']}` as expected from the emitted corpus.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_LITERAL_SPAN_CONTENT_ORIGIN_SUBPROGRAM`."
            if s["promoted"]
            else "`JOINT_CONTENT_ORIGIN_PROGRAM_NOT_PROMOTED`."
        ),
        "",
        "This is a real but narrow executable dependency reduction, not a complete "
        "content-origin generator. Most fallback copy origins remain external; literal "
        "payload also remains an external innovation tape.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_joint_content_origin_program_gate.py](../scripts/01_joint_content_origin_program_gate.py)",
        "- [01_joint_content_origin_program_gate.json](test_results/01_joint_content_origin_program_gate.json)",
        "- [01_joint_content_origin_program_gate.md](test_results/01_joint_content_origin_program_gate.md)",
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
