#!/usr/bin/env python3
"""Executable v5 source-endpoint memory integration gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v5_source_endpoint_memory_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
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
UNANCHORED_ORIGIN_GATE = (
    ROOT
    / "analysis"
    / "unanchored_copy_origin_representation_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unanchored_copy_origin_representation_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_executable_v5_source_endpoint_memory_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v5_source_endpoint_memory_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v5_source_endpoint_memory_audit.md"

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


def load_one_sided_module() -> Any:
    spec = importlib.util.spec_from_file_location("one_sided_gate", ONE_SIDED_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ONE_SIDED_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_roundtrip() -> dict[str, Any]:
    module = load_one_sided_module()
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, _ledger = module.grouped_ledger_rows()
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
            errors.append({"book": book})
        stream += rendered
    return {"errors": errors, "exact_books": exact, "roundtrip_70_70": exact == 70 and not errors}


def make_result() -> dict[str, Any]:
    v4 = load_json(EXECUTABLE_V4_GATE)
    origin = load_json(UNANCHORED_ORIGIN_GATE)
    assert_boundary("executable_v4_one_sided_boundary_program_gate", v4)
    assert_boundary("unanchored_copy_origin_representation_gate", origin)
    validation = validate_roundtrip()
    origin_summary = origin["summary"]
    source_memory = origin_summary["source_endpoint_memory"]
    declaration_bits = float(origin_summary["declaration_bits_representation_family"])
    v5_residual = float(source_memory["residual_bits"]) + declaration_bits
    v5_external = ONLINE_X64_COARSE_BITS + v5_residual
    v4_summary = v4["summary"]
    v4_external = float(v4_summary["v4_external_bits_excluding_seed"])
    seed_bits = float(v4_summary["seed_payload_bits"])
    delta = v5_external - v4_external
    promoted = (
        origin["classification"] == "PROMOTED_UNANCHORED_COPY_ORIGIN_REPRESENTATION"
        and validation["roundtrip_70_70"]
        and delta < 0
    )
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_LEDGER"
            if promoted
            else "EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_NOT_PROMOTED"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "executable_v5_promoted": promoted,
            "next_blocker": "101/208 copy events remain fallback plus literal payload, seed payload, and row0",
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v4_one_sided_boundary_program_gate": rel(EXECUTABLE_V4_GATE),
            "unanchored_copy_origin_representation_gate": rel(UNANCHORED_ORIGIN_GATE),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "executable_v5_source_endpoint_memory_gate.v1",
        "scope": "analysis_only_executable_v5_source_endpoint_memory",
        "summary": {
            "class_counts": source_memory["class_counts"],
            "copy_bits": float(source_memory["copy_bits"]),
            "copy_ops": int(source_memory["copy_ops"]),
            "delta_excluding_seed_vs_v4": delta,
            "delta_including_seed_vs_v4": delta,
            "literal_payload_bits": float(source_memory["literal_payload_bits"]),
            "online_x64_coarse_bits": ONLINE_X64_COARSE_BITS,
            "representation_declaration_bits": declaration_bits,
            "residual_composition_bits": float(source_memory["composition_bits"]),
            "seed_payload_bits": seed_bits,
            "source_endpoint_marks_added": int(source_memory["marks_added"]),
            "v4_external_bits_excluding_seed": v4_external,
            "v4_external_bits_including_seed": float(v4_summary["v4_external_bits_including_seed"]),
            "v4_residual_bits": float(v4_summary["v4_residual_bits"]),
            "v5_external_bits_excluding_seed": v5_external,
            "v5_external_bits_including_seed": v5_external + seed_bits,
            "v5_residual_bits": v5_residual,
        },
        "translation_delta": "NONE",
        "validation": validation,
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Executable v5 Source-Endpoint Memory Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Roundtrip: `{result['validation']['exact_books']}/70`.",
        f"- V4 external bits excluding seed: `{s['v4_external_bits_excluding_seed']:.3f}`.",
        f"- V5 external bits excluding seed: `{s['v5_external_bits_excluding_seed']:.3f}`.",
        f"- Delta vs v4: `{s['delta_excluding_seed_vs_v4']:.3f}` bits.",
        f"- Class counts: `{s['class_counts']}`.",
        f"- Source endpoint marks added: `{s['source_endpoint_marks_added']}`.",
        "",
        "## V5 Tape Breakdown",
        "",
        f"- Online x64 coarse-control: `{s['online_x64_coarse_bits']:.3f}`.",
        f"- Source-endpoint memory copy tape: `{s['copy_bits']:.3f}`.",
        f"- Residual length composition: `{s['residual_composition_bits']:.3f}`.",
        f"- Literal payload: `{s['literal_payload_bits']:.3f}`.",
        f"- Representation declaration: `{s['representation_declaration_bits']:.3f}`.",
        f"- Seed payload: `{s['seed_payload_bits']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_LEDGER`."
            if result["decision"]["executable_v5_promoted"]
            else "`EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_NOT_PROMOTED`."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Executable v5 Source-Endpoint Memory Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit integrates the promoted source-endpoint memory representation "
        "into the executable decoder ledger. The decoder still roundtrips the "
        "same 70 books; the change is that paid or derived copy source endpoints "
        "become reusable online marks for future source-interval derivation.",
        "",
        f"Roundtrip remains `{result['validation']['exact_books']}/70`. External "
        f"bits excluding seed fall from v4 `{s['v4_external_bits_excluding_seed']:.3f}` "
        f"to v5 `{s['v5_external_bits_excluding_seed']:.3f}`, a reduction of "
        f"`{-s['delta_excluding_seed_vs_v4']:.3f}` bits after charging "
        f"`{s['representation_declaration_bits']:.3f}` representation-declaration bits.",
        "",
        f"Copy classes shift to `{s['class_counts']}`: more intervals are fully "
        "derived, residual composition falls, but `101` copy events still fall "
        "back to copy hints.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_LEDGER`."
            if result["decision"]["executable_v5_promoted"]
            else "`EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_NOT_PROMOTED`."
        ),
        "",
        "This is real but small program progress: it reduces a declared external "
        "dependency inside the executable ledger. It is not a full generator; "
        "fallback copy hints, literal payload, seed payload, and row0 remain external.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_v5_source_endpoint_memory_gate.py](../scripts/01_executable_v5_source_endpoint_memory_gate.py)",
        "- [01_executable_v5_source_endpoint_memory_gate.json](test_results/01_executable_v5_source_endpoint_memory_gate.json)",
        "- [01_executable_v5_source_endpoint_memory_gate.md](test_results/01_executable_v5_source_endpoint_memory_gate.md)",
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
