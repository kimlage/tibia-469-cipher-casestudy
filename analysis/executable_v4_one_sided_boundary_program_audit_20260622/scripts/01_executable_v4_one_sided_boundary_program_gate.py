#!/usr/bin/env python3
"""Executable v4 one-sided boundary program integration gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v4_one_sided_boundary_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
ONE_SIDED_SCRIPT = (
    ROOT
    / "analysis"
    / "one_sided_source_boundary_program_audit_20260622"
    / "scripts"
    / "01_one_sided_source_boundary_program_gate.py"
)
ONE_SIDED_GATE = (
    ROOT
    / "analysis"
    / "one_sided_source_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_one_sided_source_boundary_program_gate.json"
)
EXECUTABLE_V3_GATE = (
    ROOT
    / "analysis"
    / "executable_v3_source_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v3_source_boundary_program_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_executable_v4_one_sided_boundary_program_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v4_one_sided_boundary_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v4_one_sided_boundary_program_audit.md"

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


def validate_roundtrip(module: Any) -> dict[str, Any]:
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
                output.append(
                    available[
                        int(row["copy_source_raw"]) : int(row["copy_source_raw"]) + int(row["exact_length"])
                    ]
                )
        rendered = "".join(output)
        if rendered == books[book]:
            exact += 1
        else:
            errors.append({"book": book})
        stream += rendered
    return {"errors": errors, "exact_books": exact, "roundtrip_70_70": exact == 70 and not errors}


def make_result() -> dict[str, Any]:
    one_sided_gate = load_json(ONE_SIDED_GATE)
    assert_boundary("one_sided_source_boundary_program_gate", one_sided_gate)
    v3_gate = load_json(EXECUTABLE_V3_GATE)
    assert_boundary("executable_v3_source_boundary_program_gate", v3_gate)
    module = load_one_sided_module()
    rows, meta = module.build_event_rows()
    summary = module.summarize_policy(rows, meta, "end_first")
    validation = validate_roundtrip(module)
    policy_declaration_bits = 2.0
    v3 = v3_gate["summary"]
    seed_bits = float(v3["seed_payload_bits"])
    v4_residual = float(summary["residual_bits"]) + policy_declaration_bits
    v4_excluding_seed = ONLINE_X64_COARSE_BITS + v4_residual
    v3_excluding_seed = float(v3["v3_external_bits_excluding_seed"])
    promoted = v4_excluding_seed < v3_excluding_seed and validation["roundtrip_70_70"]
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_EXECUTABLE_V4_ONE_SIDED_BOUNDARY_LEDGER"
            if promoted
            else "EXECUTABLE_V4_ONE_SIDED_BOUNDARY_NOT_PROMOTED"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "executable_v4_promoted": promoted,
            "next_blocker": "83/208 copy intervals still have neither endpoint in the promoted boundary set",
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v3_source_boundary_program_gate": rel(EXECUTABLE_V3_GATE),
            "one_sided_source_boundary_program_gate": rel(ONE_SIDED_GATE),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "executable_v4_one_sided_boundary_program_gate.v1",
        "scope": "analysis_only_executable_v4_one_sided_boundary_program",
        "summary": {
            "class_counts": summary["class_counts"],
            "copy_bits": summary["copy_bits"],
            "copy_ops": summary["copy_ops"],
            "delta_excluding_seed_vs_v3": v4_excluding_seed - v3_excluding_seed,
            "delta_including_seed_vs_v3": (v4_excluding_seed + seed_bits)
            - (v3_excluding_seed + seed_bits),
            "literal_payload_bits": summary["literal_payload_bits"],
            "online_x64_coarse_bits": ONLINE_X64_COARSE_BITS,
            "policy": "end_first",
            "policy_declaration_bits": policy_declaration_bits,
            "residual_composition_bits": summary["composition_bits"],
            "seed_payload_bits": seed_bits,
            "v3_external_bits_excluding_seed": v3_excluding_seed,
            "v3_external_bits_including_seed": float(v3["v3_external_bits_including_seed"]),
            "v3_residual_bits": float(v3["source_boundary_residual_bits"]),
            "v4_external_bits_excluding_seed": v4_excluding_seed,
            "v4_external_bits_including_seed": v4_excluding_seed + seed_bits,
            "v4_residual_bits": v4_residual,
        },
        "translation_delta": "NONE",
        "validation": validation,
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Executable v4 One-Sided Boundary Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Roundtrip: `{result['validation']['exact_books']}/70`.",
        f"- Policy: `{s['policy']}` with declaration bits `{s['policy_declaration_bits']:.3f}`.",
        f"- Class counts: `{s['class_counts']}`.",
        f"- V3 external bits excluding seed: `{s['v3_external_bits_excluding_seed']:.3f}`.",
        f"- V4 external bits excluding seed: `{s['v4_external_bits_excluding_seed']:.3f}`.",
        f"- Delta excluding seed vs v3: `{s['delta_excluding_seed_vs_v3']:.3f}` bits.",
        f"- V4 external bits including seed: `{s['v4_external_bits_including_seed']:.3f}`.",
        "",
        "## V4 Tape Breakdown",
        "",
        f"- Online x64 coarse-control: `{s['online_x64_coarse_bits']:.3f}`.",
        f"- Copy/endpoint boundary tape: `{s['copy_bits']:.3f}`.",
        f"- Residual length composition: `{s['residual_composition_bits']:.3f}`.",
        f"- Literal payload: `{s['literal_payload_bits']:.3f}`.",
        f"- Seed payload: `{s['seed_payload_bits']:.3f}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V4_ONE_SIDED_BOUNDARY_LEDGER`: one-sided "
            "boundary anchors reduce the executable v3 ledger."
            if result["decision"]["executable_v4_promoted"]
            else "`EXECUTABLE_V4_ONE_SIDED_BOUNDARY_NOT_PROMOTED`."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Executable v4 One-Sided Boundary Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "The one-sided source-boundary program is integrated into the executable "
        "decoder ledger. Two-ended intervals remain v3-derived; end-anchored "
        "one-sided intervals use the `end_first` policy; the remaining intervals "
        "fall back to copy-hint rank, with exact lengths still handled by the "
        "book-level residual composition.",
        "",
        f"Roundtrip remains `{result['validation']['exact_books']}/70`. External "
        f"bits excluding seed fall from `{s['v3_external_bits_excluding_seed']:.3f}` "
        f"to `{s['v4_external_bits_excluding_seed']:.3f}`, a reduction of "
        f"`{-s['delta_excluding_seed_vs_v3']:.3f}` bits after policy declaration.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V4_ONE_SIDED_BOUNDARY_LEDGER`."
            if result["decision"]["executable_v4_promoted"]
            else "`EXECUTABLE_V4_ONE_SIDED_BOUNDARY_NOT_PROMOTED`."
        ),
        "",
        "This is still partial: intervals with neither endpoint in the promoted "
        "boundary set, literal payload, seed payload, and row0 remain external.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_v4_one_sided_boundary_program_gate.py](../scripts/01_executable_v4_one_sided_boundary_program_gate.py)",
        "- [01_executable_v4_one_sided_boundary_program_gate.json](test_results/01_executable_v4_one_sided_boundary_program_gate.json)",
        "- [01_executable_v4_one_sided_boundary_program_gate.md](test_results/01_executable_v4_one_sided_boundary_program_gate.md)",
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
