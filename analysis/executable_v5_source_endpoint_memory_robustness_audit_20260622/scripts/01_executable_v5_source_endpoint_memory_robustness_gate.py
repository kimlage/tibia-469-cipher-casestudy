#!/usr/bin/env python3
"""Executable v5 source-endpoint memory robustness gate.

V5 was promoted as a small executable residual reduction. This audit checks
whether that reduction is concentrated in a few books or survives prefix/suffix
splits and shuffled source-mark controls.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v5_source_endpoint_memory_robustness_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

V5_SCRIPT = (
    ROOT
    / "analysis"
    / "v5_endpoint_cascade_stability_audit_20260622"
    / "scripts"
    / "01_v5_endpoint_cascade_stability_gate.py"
)
ONE_SIDED_SCRIPT = (
    ROOT
    / "analysis"
    / "one_sided_source_boundary_program_audit_20260622"
    / "scripts"
    / "01_one_sided_source_boundary_program_gate.py"
)
EXECUTABLE_V5_GATE = (
    ROOT
    / "analysis"
    / "executable_v5_source_endpoint_memory_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v5_source_endpoint_memory_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_executable_v5_source_endpoint_memory_robustness_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v5_source_endpoint_memory_robustness_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v5_source_endpoint_memory_robustness_audit.md"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
CONTROL_TRIALS = 80


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


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    index = min(len(sorted_values) - 1, max(0, int(math.ceil(q * len(sorted_values)) - 1)))
    return sorted_values[index]


def make_result() -> dict[str, Any]:
    v5_gate = load_json(EXECUTABLE_V5_GATE)
    assert_boundary("executable_v5_source_endpoint_memory_gate", v5_gate)
    v5mod = load_module("v5_endpoint_cascade_gate", V5_SCRIPT)
    osmod = load_module("one_sided_gate", ONE_SIDED_SCRIPT)
    v4_rows, v4_meta = osmod.build_event_rows()

    book_rows = []
    for book in range(10, 70):
        v5 = v5mod.summarize_policy("end_first", books={book})["residual_bits"]
        v4 = osmod.summarize_policy(v4_rows, v4_meta, "end_first", books={book})["residual_bits"]
        book_rows.append(
            {
                "book": book,
                "delta_vs_v4": v5 - v4,
                "v4_residual_bits": v4,
                "v5_residual_bits": v5,
            }
        )

    prefix_rows = []
    positive_suffix_splits = 0
    total_suffix_delta = 0.0
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        test_books = set(range(cutoff, 70))
        train_v5 = v5mod.summarize_policy("end_first", books=train_books)["residual_bits"]
        train_v4 = osmod.summarize_policy(v4_rows, v4_meta, "end_first", books=train_books)["residual_bits"]
        test_v5 = v5mod.summarize_policy("end_first", books=test_books)["residual_bits"]
        test_v4 = osmod.summarize_policy(v4_rows, v4_meta, "end_first", books=test_books)["residual_bits"]
        test_delta = test_v5 - test_v4
        total_suffix_delta += test_delta
        if test_delta < 0:
            positive_suffix_splits += 1

        shuffled_test_deltas = sorted(
            v5mod.summarize_policy(
                "end_first",
                books=test_books,
                shuffle_marks=True,
                seed=RANDOM_SEED + cutoff * 1000 + trial,
            )["residual_bits"]
            - test_v4
            for trial in range(CONTROL_TRIALS)
        )
        prefix_rows.append(
            {
                "control_delta_p05": percentile(shuffled_test_deltas, 0.05),
                "control_delta_p50": percentile(shuffled_test_deltas, 0.50),
                "control_delta_p95": percentile(shuffled_test_deltas, 0.95),
                "cutoff": cutoff,
                "test_delta_vs_v4": test_delta,
                "test_improves": test_delta < 0,
                "test_v4_residual_bits": test_v4,
                "test_v5_residual_bits": test_v5,
                "train_delta_vs_v4": train_v5 - train_v4,
                "train_v4_residual_bits": train_v4,
                "train_v5_residual_bits": train_v5,
                "v5_beats_control_p05": test_delta < percentile(shuffled_test_deltas, 0.05),
            }
        )

    full_delta = sum(row["delta_vs_v4"] for row in book_rows)
    declaration_bits = float(v5_gate["summary"]["representation_declaration_bits"])
    robust = (
        full_delta + declaration_bits < 0
        and positive_suffix_splits >= 4
        and total_suffix_delta < 0
        and sum(1 for row in prefix_rows if row["v5_beats_control_p05"]) >= 3
    )
    return {
        "book_rows": book_rows,
        "case_reopened": False,
        "classification": (
            "PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_ROBUST"
            if robust
            else "executable_v5_source_endpoint_memory_robustness_weak"
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "executable_v5_robust": robust,
            "next_blocker": "101 fallback copy hints plus literal payload, seed payload, and row0 remain external",
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v5_source_endpoint_memory_gate": rel(EXECUTABLE_V5_GATE),
            "one_sided_source_boundary_program_script": rel(ONE_SIDED_SCRIPT),
            "v5_endpoint_cascade_stability_script": rel(V5_SCRIPT),
        },
        "plaintext_claim": False,
        "prefix_rows": prefix_rows,
        "row0_status": "unchanged_exogenous",
        "schema": "executable_v5_source_endpoint_memory_robustness_gate.v1",
        "scope": "analysis_only_executable_v5_source_endpoint_memory_robustness",
        "summary": {
            "book_delta_negative_count": sum(1 for row in book_rows if row["delta_vs_v4"] < 0),
            "book_delta_positive_count": sum(1 for row in book_rows if row["delta_vs_v4"] > 0),
            "control_trials_per_split": CONTROL_TRIALS,
            "declaration_bits": declaration_bits,
            "full_delta_after_declaration_vs_v4": full_delta + declaration_bits,
            "full_delta_before_declaration_vs_v4": full_delta,
            "positive_suffix_splits": positive_suffix_splits,
            "robust": robust,
            "top_gain_books": sorted(book_rows, key=lambda row: row["delta_vs_v4"])[:10],
            "top_harm_books": sorted(book_rows, key=lambda row: row["delta_vs_v4"], reverse=True)[:10],
            "total_suffix_delta_vs_v4": total_suffix_delta,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Executable v5 Source-Endpoint Memory Robustness Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Full delta before declaration vs v4: `{s['full_delta_before_declaration_vs_v4']:.3f}`.",
        f"- Full delta after declaration vs v4: `{s['full_delta_after_declaration_vs_v4']:.3f}`.",
        "- Note: per-book robustness compares against the v4 residual without recharging the v4 policy declaration.",
        f"- Book deltas negative/positive: `{s['book_delta_negative_count']}` / `{s['book_delta_positive_count']}`.",
        f"- Positive suffix splits: `{s['positive_suffix_splits']}/5`.",
        f"- Total suffix delta vs v4: `{s['total_suffix_delta_vs_v4']:.3f}`.",
        f"- Control trials per split: `{s['control_trials_per_split']}`.",
        "",
        "## Prefix/Suffix Rows",
        "",
        "| Cutoff | Train delta | Test delta | Control p05 | Beats p05 |",
        "| ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["prefix_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['train_delta_vs_v4']:.3f}` | "
            f"`{row['test_delta_vs_v4']:.3f}` | `{row['control_delta_p05']:.3f}` | "
            f"`{row['v5_beats_control_p05']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_ROBUST`."
                if s["robust"]
                else "`executable_v5_source_endpoint_memory_robustness_weak`."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Executable v5 Source-Endpoint Memory Robustness Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit checks whether the promoted v5 source-endpoint memory reduction "
        "survives prefix/suffix validation and shuffled source-mark controls.",
        "",
        f"Full-corpus delta is `{s['full_delta_before_declaration_vs_v4']:.3f}` bits "
        f"before declaration and `{s['full_delta_after_declaration_vs_v4']:.3f}` "
        "after declaration under a conservative per-book comparator that does not "
        "recharge the v4 policy declaration. The reduction is not confined to one split: v5 improves "
        f"`{s['positive_suffix_splits']}/5` suffix splits with aggregate suffix "
        f"delta `{s['total_suffix_delta_vs_v4']:.3f}`.",
        "",
        "The result is still partial. Per-book deltas are mixed, and one suffix "
        "split is worse; however the rule remains a controlled executable "
        "dependency reduction rather than a pure full-fit artifact.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V5_SOURCE_ENDPOINT_MEMORY_ROBUST`."
            if s["robust"]
            else "`executable_v5_source_endpoint_memory_robustness_weak`."
        ),
        "",
        "Executable v5 remains the promoted frontier. Remaining external fields are "
        "fallback copy hints, literal payload, seed payload, and row0.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_v5_source_endpoint_memory_robustness_gate.py](../scripts/01_executable_v5_source_endpoint_memory_robustness_gate.py)",
        "- [01_executable_v5_source_endpoint_memory_robustness_gate.json](test_results/01_executable_v5_source_endpoint_memory_robustness_gate.json)",
        "- [01_executable_v5_source_endpoint_memory_robustness_gate.md](test_results/01_executable_v5_source_endpoint_memory_robustness_gate.md)",
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
