#!/usr/bin/env python3
"""Executable v6 literal-span origin integration gate.

This audit integrates the promoted literal-span content-origin subprogram into
the executable ledger after v5. It is not a new search: it checks that the
subprogram can be used inside the decoder contract, preserves 70/70 roundtrip,
and updates the external dependency ledger without blurring the remaining
external tapes.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v6_literal_span_origin_audit_20260622"
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
EXECUTABLE_V5_GATE = (
    ROOT
    / "analysis"
    / "executable_v5_source_endpoint_memory_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v5_source_endpoint_memory_gate.json"
)
JOINT_CONTENT_ORIGIN_GATE = (
    ROOT
    / "analysis"
    / "joint_content_origin_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_joint_content_origin_program_gate.json"
)
JOINT_CONTENT_ORIGIN_SCRIPT = (
    ROOT
    / "analysis"
    / "joint_content_origin_program_audit_20260622"
    / "scripts"
    / "01_joint_content_origin_program_gate.py"
)

JSON_OUT = TEST_RESULTS / "01_executable_v6_literal_span_origin_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v6_literal_span_origin_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v6_literal_span_origin_audit.md"


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


def load_joint_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "joint_content_origin_gate",
        JOINT_CONTENT_ORIGIN_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {JOINT_CONTENT_ORIGIN_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grouped_ledger_rows() -> dict[int, list[dict[str, Any]]]:
    ledger = load_json(UNIFIED_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in ledger["ledger_rows"]:
        grouped.setdefault(int(row["book"]), []).append(row)
    return {
        book: sorted(rows, key=lambda item: int(item["op_index"]))
        for book, rows in grouped.items()
    }


def literal_span_source_events() -> dict[tuple[int, int], dict[str, Any]]:
    joint = load_joint_module()
    events, validation = joint.build_fallback_event_rows()
    if validation["errors"]:
        raise RuntimeError({"joint_content_origin_validation_errors": validation["errors"]})
    selected = {}
    for event in events:
        bits = event["model_bits"]["literal_span_offset"]
        if bits is not None:
            selected[(int(event["book"]), int(event["op_index"]))] = {
                "copy_hint_rank_bits_before": float(event["copy_hint_rank_bits"]),
                "literal_span_offset_bits": float(bits),
                "source": int(event["source"]),
            }
    return selected


def validate_v6_roundtrip(selected: dict[tuple[int, int], dict[str, Any]]) -> dict[str, Any]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book = grouped_ledger_rows()
    stream = "".join(books[book] for book in range(10))
    exact = 10
    errors = []
    event_rows = []
    for book in range(10, 70):
        rendered = []
        for row in by_book[book]:
            op_index = int(row["op_index"])
            op_type = str(row["op_type"])
            start = int(row["target_start"])
            length = int(row["exact_length"])
            available = stream + "".join(rendered)
            if op_type == "literal":
                payload = str(row["literal_payload"])
                rendered.append(payload)
                continue
            raw_source = int(row["copy_source_raw"])
            event_key = (book, op_index)
            if event_key in selected:
                source = int(selected[event_key]["source"])
                source_status = "derived_literal_span_offset"
                source_bits = float(selected[event_key]["literal_span_offset_bits"])
            else:
                source = raw_source
                source_status = "paid_existing_v5_copy_hint_or_derived_boundary"
                source_bits = float(row["copy_hint_rank_bits"] or 0.0)
            copied = available[source : source + length]
            expected = books[book][start : start + length]
            if copied != expected:
                errors.append(
                    {
                        "book": book,
                        "copied": copied,
                        "expected": expected,
                        "op_index": op_index,
                        "reason": "copy_payload_mismatch",
                        "source": source,
                        "source_status": source_status,
                    }
                )
            rendered.append(copied)
            event_rows.append(
                {
                    "book": book,
                    "exact_length": length,
                    "op_index": op_index,
                    "raw_source": raw_source,
                    "source": source,
                    "source_bits": source_bits,
                    "source_matches_raw": source == raw_source,
                    "source_status": source_status,
                    "target_start": start,
                }
            )
        rendered_book = "".join(rendered)
        if rendered_book == books[book]:
            exact += 1
        else:
            errors.append(
                {
                    "book": book,
                    "expected_len": len(books[book]),
                    "reason": "rendered_book_mismatch",
                    "rendered_len": len(rendered_book),
                }
            )
        stream += rendered_book
    return {
        "copy_event_rows": event_rows,
        "errors": errors,
        "exact_books": exact,
        "literal_span_source_events": len(selected),
        "roundtrip_70_70": exact == 70 and not errors,
    }


def make_result() -> dict[str, Any]:
    v5 = load_json(EXECUTABLE_V5_GATE)
    joint = load_json(JOINT_CONTENT_ORIGIN_GATE)
    assert_boundary("executable_v5_source_endpoint_memory_gate", v5)
    assert_boundary("joint_content_origin_program_gate", joint)
    if joint["classification"] != "PROMOTED_LITERAL_SPAN_CONTENT_ORIGIN_SUBPROGRAM":
        raise RuntimeError("joint content-origin subprogram is not promoted")
    selected = literal_span_source_events()
    validation = validate_v6_roundtrip(selected)

    v5_summary = v5["summary"]
    joint_summary = joint["summary"]
    fallback_copy_hint_bits = float(joint_summary["baseline_copy_hint_bits"])
    literal_span_bits = float(joint_summary["model_rows"]["literal_span_offset"]["total_bits_after_declaration"])
    selected_copy_hint_bits_before = sum(
        float(item["copy_hint_rank_bits_before"]) for item in selected.values()
    )
    selected_literal_span_bits_before_declaration = sum(
        float(item["literal_span_offset_bits"]) for item in selected.values()
    )
    fallback_copy_hint_bits_remaining = fallback_copy_hint_bits - selected_copy_hint_bits_before
    delta_vs_v5 = literal_span_bits - fallback_copy_hint_bits
    v6_external = float(v5_summary["v5_external_bits_excluding_seed"]) + delta_vs_v5
    seed_bits = float(v5_summary["seed_payload_bits"])
    v6_copy_bits = float(v5_summary["copy_bits"]) + delta_vs_v5

    class_counts = dict(v5_summary["class_counts"])
    class_counts["literal_span_source"] = len(selected)
    class_counts["fallback"] = int(class_counts["fallback"]) - len(selected)
    if sum(int(value) for value in class_counts.values()) != int(v5_summary["copy_ops"]):
        raise RuntimeError({"reason": "copy class counts do not sum", "class_counts": class_counts})

    promoted = validation["roundtrip_70_70"] and delta_vs_v5 < 0
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_LEDGER"
            if promoted
            else "EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_NOT_PROMOTED"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "executable_v6_promoted": promoted,
            "next_blocker": (
                "90 v5 fallback copy origins, literal payload, residual composition, "
                "seed payload, and row0 remain external"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v5_gate": rel(EXECUTABLE_V5_GATE),
            "joint_content_origin_gate": rel(JOINT_CONTENT_ORIGIN_GATE),
            "joint_content_origin_script": rel(JOINT_CONTENT_ORIGIN_SCRIPT),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "executable_v6_literal_span_origin_gate.v1",
        "scope": "analysis_only_executable_v6_literal_span_origin",
        "summary": {
            "class_counts": class_counts,
            "copy_bits": v6_copy_bits,
            "copy_ops": int(v5_summary["copy_ops"]),
            "delta_excluding_seed_vs_v5": delta_vs_v5,
            "delta_including_seed_vs_v5": delta_vs_v5,
            "fallback_copy_hint_bits_before": fallback_copy_hint_bits,
            "fallback_copy_hint_bits_replaced": selected_copy_hint_bits_before,
            "fallback_copy_hint_bits_remaining": fallback_copy_hint_bits_remaining,
            "literal_payload_bits": float(v5_summary["literal_payload_bits"]),
            "literal_span_origin_bits": literal_span_bits,
            "literal_span_origin_bits_before_declaration": selected_literal_span_bits_before_declaration,
            "literal_span_source_events": len(selected),
            "online_x64_coarse_bits": float(v5_summary["online_x64_coarse_bits"]),
            "residual_composition_bits": float(v5_summary["residual_composition_bits"]),
            "seed_payload_bits": seed_bits,
            "v5_external_bits_excluding_seed": float(v5_summary["v5_external_bits_excluding_seed"]),
            "v5_external_bits_including_seed": float(v5_summary["v5_external_bits_including_seed"]),
            "v6_external_bits_excluding_seed": v6_external,
            "v6_external_bits_including_seed": v6_external + seed_bits,
        },
        "translation_delta": "NONE",
        "validation": {
            "derived_literal_span_sources_match_raw": sum(
                1
                for row in validation["copy_event_rows"]
                if row["source_status"] == "derived_literal_span_offset" and row["source_matches_raw"]
            ),
            "errors": validation["errors"],
            "exact_books": validation["exact_books"],
            "literal_span_source_events": validation["literal_span_source_events"],
            "roundtrip_70_70": validation["roundtrip_70_70"],
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    v = result["validation"]
    lines = [
        "# Executable v6 Literal-Span Origin Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Roundtrip: `{v['exact_books']}/70`.",
        f"- V5 external bits excluding seed: `{s['v5_external_bits_excluding_seed']:.3f}`.",
        f"- V6 external bits excluding seed: `{s['v6_external_bits_excluding_seed']:.3f}`.",
        f"- Delta vs v5: `{s['delta_excluding_seed_vs_v5']:.3f}` bits.",
        f"- Literal-span source events: `{s['literal_span_source_events']}`.",
        f"- Derived literal-span sources matching raw: `{v['derived_literal_span_sources_match_raw']}`.",
        f"- Copy-hint bits replaced: `{s['fallback_copy_hint_bits_replaced']:.3f}`.",
        f"- Copy-hint bits remaining: `{s['fallback_copy_hint_bits_remaining']:.3f}`.",
        f"- Class counts: `{s['class_counts']}`.",
        "",
        "## V6 Tape Breakdown",
        "",
        f"- Online x64 coarse-control: `{s['online_x64_coarse_bits']:.3f}`.",
        f"- Copy tape after v6: `{s['copy_bits']:.3f}`.",
        f"- Literal-span origin program: `{s['literal_span_origin_bits']:.3f}` "
        f"(`{s['literal_span_origin_bits_before_declaration']:.3f}` before declaration plus remaining fallback copy-hints).",
        f"- Residual length composition: `{s['residual_composition_bits']:.3f}`.",
        f"- Literal payload: `{s['literal_payload_bits']:.3f}`.",
        f"- Seed payload: `{s['seed_payload_bits']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_LEDGER`."
            if result["decision"]["executable_v6_promoted"]
            else "`EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_NOT_PROMOTED`."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    v = result["validation"]
    lines = [
        "# Final Executable v6 Literal-Span Origin Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit integrates the promoted `literal_span_offset` content-origin "
        "subprogram into the executable decoder ledger after v5.",
        "",
        f"Roundtrip remains `{v['exact_books']}/70`. External bits excluding seed "
        f"fall from v5 `{s['v5_external_bits_excluding_seed']:.3f}` to v6 "
        f"`{s['v6_external_bits_excluding_seed']:.3f}`, a reduction of "
        f"`{-s['delta_excluding_seed_vs_v5']:.3f}` bits. Including the unchanged "
        f"seed payload, the ledger moves from `{s['v5_external_bits_including_seed']:.3f}` "
        f"to `{s['v6_external_bits_including_seed']:.3f}`.",
        "",
        f"Copy classes are now `{s['class_counts']}`. The new class derives "
        f"`{s['literal_span_source_events']}` fallback copy sources from prior "
        "literal spans; all derived sources match the raw source in the validation "
        f"ledger (`{v['derived_literal_span_sources_match_raw']}`/"
        f"`{s['literal_span_source_events']}`).",
        "",
        f"The replaced subset previously cost `{s['fallback_copy_hint_bits_replaced']:.3f}` "
        f"copy-hint bits and is now addressed by `{s['literal_span_origin_bits_before_declaration']:.3f}` "
        "literal-span offset bits plus the model declaration. The remaining fallback "
        f"copy-hint tape is `{s['fallback_copy_hint_bits_remaining']:.3f}` bits.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_LEDGER`."
            if result["decision"]["executable_v6_promoted"]
            else "`EXECUTABLE_V6_LITERAL_SPAN_ORIGIN_NOT_PROMOTED`."
        ),
        "",
        "This is a small executable dependency reduction, not a complete generator. "
        "`90` v5 fallback copy origins, residual composition, literal payload, seed "
        "payload, and row0 remain external.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_v6_literal_span_origin_gate.py](../scripts/01_executable_v6_literal_span_origin_gate.py)",
        "- [01_executable_v6_literal_span_origin_gate.json](test_results/01_executable_v6_literal_span_origin_gate.json)",
        "- [01_executable_v6_literal_span_origin_gate.md](test_results/01_executable_v6_literal_span_origin_gate.md)",
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
