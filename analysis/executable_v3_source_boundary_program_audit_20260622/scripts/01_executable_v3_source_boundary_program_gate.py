#!/usr/bin/env python3
"""Executable v3 source-boundary program integration gate.

This integrates the promoted partial source-boundary program into the
executable decoder ledger. It is not another local source-boundary search: it
asks whether the promoted program actually reduces the external tapes in the
real decoder contract after preserving roundtrip and paying fallbacks.

Analysis-only. No row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v3_source_boundary_program_audit_20260622"
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
SOURCE_BOUNDARY_GATE = (
    ROOT
    / "analysis"
    / "source_boundary_candidate_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_source_boundary_candidate_program_gate.json"
)
SOURCE_BOUNDARY_SCRIPT = (
    ROOT
    / "analysis"
    / "source_boundary_candidate_program_audit_20260622"
    / "scripts"
    / "01_source_boundary_candidate_program_gate.py"
)

JSON_OUT = TEST_RESULTS / "01_executable_v3_source_boundary_program_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v3_source_boundary_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v3_source_boundary_program_audit.md"

ONLINE_X64_COARSE_BITS = 876.412


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


def load_source_boundary_module() -> Any:
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


def validate_roundtrip(by_book: dict[int, list[dict[str, Any]]]) -> dict[str, Any]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    stream = "".join(books[book] for book in range(10))
    exact = 10
    errors = []
    for book in range(10, 70):
        output = []
        for row in by_book[book]:
            if row["op_type"] == "literal":
                output.append(str(row["literal_payload"]))
            else:
                available = stream + "".join(output)
                source = int(row["copy_source_raw"])
                length = int(row["exact_length"])
                output.append(available[source : source + length])
        rendered = "".join(output)
        if rendered == books[book]:
            exact += 1
        else:
            errors.append(
                {
                    "book": book,
                    "expected_length": len(books[book]),
                    "rendered_length": len(rendered),
                }
            )
        stream += rendered
    return {
        "errors": errors,
        "exact_books": exact,
        "roundtrip_70_70": exact == 70 and not errors,
        "stream_digits": len(stream),
    }


def build_v3_ledger() -> dict[str, Any]:
    source_gate = load_json(SOURCE_BOUNDARY_GATE)
    assert_boundary("source_boundary_candidate_program_gate", source_gate)
    if source_gate["classification"] != "PROMOTED_SOURCE_BOUNDARY_PROGRAM":
        raise RuntimeError("source-boundary program is not promoted")
    module = load_source_boundary_module()
    source_rows, source_meta = module.score_system("event_plus_surprisal_top20")
    source_summary = module.summarize(source_rows, source_meta, policy="long_recent")
    by_book, v2 = grouped_ledger_rows()
    validation = validate_roundtrip(by_book)
    source_by_key = {
        (int(row["book"]), int(row["op_index"])): row
        for row in source_rows
        if row["event_kind"] == "copy"
    }
    v3_rows = []
    for book in range(10, 70):
        for row in by_book[book]:
            key = (book, int(row["op_index"]))
            item = {
                "book": book,
                "op_index": int(row["op_index"]),
                "target_start": int(row["target_start"]),
                "op_type": row["op_type"],
                "exact_length": int(row["exact_length"]),
                "coarse_type_length_bucket": row["coarse_type_length_bucket"],
                "row0_status": "unchanged_exogenous",
                "target_text_dependency": [],
            }
            if row["op_type"] == "literal":
                item.update(
                    {
                        "v3_status": "literal_payload_paid_length_in_residual_composition",
                        "derived_fields": ["target_start", "op_type", "length_bucket"],
                        "paid_fields": ["literal_payload", "residual_length_composition"],
                        "external_fields_remaining": ["literal_payload", "residual_length_composition"],
                        "literal_payload": row["literal_payload"],
                        "literal_payload_bits": float(row["literal_payload_bits"]),
                        "source_boundary_interval_rank_bits": 0.0,
                        "fallback_copy_hint_bits": 0.0,
                    }
                )
            else:
                source_row = source_by_key[key]
                if bool(source_row["hit"]):
                    rank_bits = float(source_row["long_recent_rank_bits"])
                    item.update(
                        {
                            "v3_status": "source_boundary_interval_derived",
                            "derived_fields": [
                                "target_start",
                                "op_type",
                                "length_bucket",
                                "exact_length_from_source_boundary_interval",
                                "copy_source_from_source_boundary_interval",
                            ],
                            "paid_fields": ["source_boundary_interval_rank"],
                            "external_fields_remaining": [],
                            "copy_source_raw": int(row["copy_source_raw"]),
                            "source_boundary_system": "event_plus_surprisal_top20",
                            "source_boundary_policy": "long_recent",
                            "source_boundary_interval_rank_bits": rank_bits,
                            "fallback_copy_hint_bits": 0.0,
                            "candidate_interval_count": int(source_row["candidate_interval_count"]),
                        }
                    )
                else:
                    item.update(
                        {
                            "v3_status": "fallback_copy_hint_paid_length_in_residual_composition",
                            "derived_fields": ["target_start", "op_type", "length_bucket"],
                            "paid_fields": ["fallback_copy_hint_rank", "residual_length_composition"],
                            "external_fields_remaining": [
                                "fallback_copy_hint_rank",
                                "residual_length_composition",
                            ],
                            "copy_source_raw": int(row["copy_source_raw"]),
                            "source_boundary_system": "event_plus_surprisal_top20",
                            "source_boundary_policy": "long_recent",
                            "source_boundary_interval_rank_bits": 0.0,
                            "fallback_copy_hint_bits": float(row["copy_hint_rank_bits"]),
                            "candidate_interval_count": int(source_row["candidate_interval_count"]),
                        }
                    )
            v3_rows.append(item)
    source_boundary_rank_bits = sum(
        float(row["source_boundary_interval_rank_bits"]) for row in v3_rows
    )
    fallback_copy_hint_bits = sum(float(row["fallback_copy_hint_bits"]) for row in v3_rows)
    literal_payload_bits = sum(float(row.get("literal_payload_bits", 0.0)) for row in v3_rows)
    residual_composition_bits = float(source_summary["composition_bits_after_derived_copy_lengths"])
    source_boundary_residual_bits = (
        source_boundary_rank_bits
        + fallback_copy_hint_bits
        + literal_payload_bits
        + residual_composition_bits
    )
    v2_residual_bits = (
        float(v2["summary"]["composition_index_bits"])
        + float(v2["summary"]["copy_hint_rank_bits"])
        + float(v2["summary"]["literal_payload_bits"])
    )
    v2_excluding_seed = ONLINE_X64_COARSE_BITS + v2_residual_bits
    v3_excluding_seed = ONLINE_X64_COARSE_BITS + source_boundary_residual_bits
    seed_bits = float(v2["summary"]["seed_payload_bits"])
    promoted = source_boundary_residual_bits < v2_residual_bits and validation["roundtrip_70_70"]
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_LEDGER"
            if promoted
            else "EXECUTABLE_V3_SOURCE_BOUNDARY_LEDGER_NOT_PROMOTED"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "executable_v3_promoted": promoted,
            "generation_explanation_status": "partial_executable_dependency_reduction"
            if promoted
            else "not_promoted",
            "next_blocker": (
                "179/208 copy intervals still require fallback copy-hint rank; "
                "literal payload and seed payload remain external"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "source_boundary_candidate_program_gate": rel(SOURCE_BOUNDARY_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "executable_v3_source_boundary_program_gate.v1",
        "scope": "analysis_only_executable_v3_source_boundary_program",
        "summary": {
            "copy_ops": int(v2["summary"]["copy_ops"]),
            "copy_intervals_derived": int(source_summary["copy_hits"]),
            "copy_intervals_fallback": int(source_summary["copy_misses"]),
            "delta_excluding_seed_vs_v2": v3_excluding_seed - v2_excluding_seed,
            "delta_including_seed_vs_v2": (v3_excluding_seed + seed_bits)
            - (v2_excluding_seed + seed_bits),
            "fallback_copy_hint_bits": fallback_copy_hint_bits,
            "literal_payload_bits": literal_payload_bits,
            "online_x64_coarse_bits": ONLINE_X64_COARSE_BITS,
            "residual_composition_bits": residual_composition_bits,
            "seed_payload_bits": seed_bits,
            "source_boundary_rank_bits": source_boundary_rank_bits,
            "source_boundary_residual_bits": source_boundary_residual_bits,
            "v2_external_bits_excluding_seed": v2_excluding_seed,
            "v2_external_bits_including_seed": v2_excluding_seed + seed_bits,
            "v2_residual_bits_replaced": v2_residual_bits,
            "v3_external_bits_excluding_seed": v3_excluding_seed,
            "v3_external_bits_including_seed": v3_excluding_seed + seed_bits,
        },
        "translation_delta": "NONE",
        "v3_ledger_rows": v3_rows,
        "validation": validation,
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Executable v3 Source-Boundary Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Does the promoted partial source-boundary program reduce the executable "
        "decoder ledger after preserving roundtrip and paying fallbacks?",
        "",
        "## Summary",
        "",
        f"- Roundtrip: `{result['validation']['exact_books']}/70`.",
        f"- Copy intervals derived by source-boundary program: `{s['copy_intervals_derived']}/{s['copy_ops']}`.",
        f"- Copy intervals still on fallback copy-hint tape: `{s['copy_intervals_fallback']}/{s['copy_ops']}`.",
        f"- V2 residual bits replaced: `{s['v2_residual_bits_replaced']:.3f}`.",
        f"- V3 source-boundary residual bits: `{s['source_boundary_residual_bits']:.3f}`.",
        f"- V2 external bits excluding seed: `{s['v2_external_bits_excluding_seed']:.3f}`.",
        f"- V3 external bits excluding seed: `{s['v3_external_bits_excluding_seed']:.3f}`.",
        f"- Delta excluding seed vs v2: `{s['delta_excluding_seed_vs_v2']:.3f}` bits.",
        f"- V3 external bits including seed: `{s['v3_external_bits_including_seed']:.3f}`.",
        "",
        "## V3 Tape Breakdown",
        "",
        f"- Online x64 coarse-control rank/corrections: `{s['online_x64_coarse_bits']:.3f}`.",
        f"- Source-boundary interval ranks: `{s['source_boundary_rank_bits']:.3f}`.",
        f"- Fallback copy-hint ranks: `{s['fallback_copy_hint_bits']:.3f}`.",
        f"- Residual length composition: `{s['residual_composition_bits']:.3f}`.",
        f"- Literal payload: `{s['literal_payload_bits']:.3f}`.",
        f"- Seed payload: `{s['seed_payload_bits']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_LEDGER`: the promoted "
            "source-boundary program becomes an executable ledger reduction."
            if result["decision"]["executable_v3_promoted"]
            else "`EXECUTABLE_V3_SOURCE_BOUNDARY_LEDGER_NOT_PROMOTED`: the "
            "integration does not reduce the executable ledger."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Executable v3 Source-Boundary Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "The promoted source-boundary program was integrated into the executable "
        "decoder ledger rather than left as a standalone gate. Online x64 coarse "
        "control remains the coarse stream; the source-boundary program derives "
        "source+length for its matched copies; all remaining copies, literal "
        "payload, residual length composition, and seed payload are still paid.",
        "",
        f"The decoder still roundtrips `{result['validation']['exact_books']}/70` "
        f"books. External bits excluding seed fall from `{s['v2_external_bits_excluding_seed']:.3f}` "
        f"to `{s['v3_external_bits_excluding_seed']:.3f}`, a reduction of "
        f"`{-s['delta_excluding_seed_vs_v2']:.3f}` bits. Including seed, the ledger "
        f"falls from `{s['v2_external_bits_including_seed']:.3f}` to "
        f"`{s['v3_external_bits_including_seed']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_LEDGER`. This is real "
            "generation-program progress because it reduces declared external "
            "source/length dependencies inside the executable decoder contract."
            if result["decision"]["executable_v3_promoted"]
            else "`EXECUTABLE_V3_SOURCE_BOUNDARY_LEDGER_NOT_PROMOTED`."
        ),
        "",
        "It is still partial: `179/208` copy intervals require fallback copy hints, "
        "literal payload and seed payload remain external, and `row0`, plaintext, "
        "translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_v3_source_boundary_program_gate.py](../scripts/01_executable_v3_source_boundary_program_gate.py)",
        "- [01_executable_v3_source_boundary_program_gate.json](test_results/01_executable_v3_source_boundary_program_gate.json)",
        "- [01_executable_v3_source_boundary_program_gate.md](test_results/01_executable_v3_source_boundary_program_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = build_v3_ledger()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
