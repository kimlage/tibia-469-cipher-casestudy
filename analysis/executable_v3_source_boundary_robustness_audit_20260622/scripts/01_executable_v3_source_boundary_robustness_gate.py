#!/usr/bin/env python3
"""Executable v3 source-boundary robustness gate.

The executable v3 ledger used the best full-corpus source-boundary system. This
gate checks the promotion against two stricter requirements:

1. pay an explicit declaration cost for the boundary system and interval policy;
2. select system+policy on prefix books only, freeze it, and score suffix books.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v3_source_boundary_robustness_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

SOURCE_BOUNDARY_SCRIPT = (
    ROOT
    / "analysis"
    / "source_boundary_candidate_program_audit_20260622"
    / "scripts"
    / "01_source_boundary_candidate_program_gate.py"
)
SOURCE_BOUNDARY_GATE = (
    ROOT
    / "analysis"
    / "source_boundary_candidate_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_source_boundary_candidate_program_gate.json"
)
EXECUTABLE_V3_GATE = (
    ROOT
    / "analysis"
    / "executable_v3_source_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v3_source_boundary_program_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_executable_v3_source_boundary_robustness_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v3_source_boundary_robustness_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v3_source_boundary_robustness_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]


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


def filter_meta(meta: dict[str, Any], books: set[int]) -> dict[str, Any]:
    return {
        **meta,
        "baseline_composition_bits_by_book": {
            book: bits
            for book, bits in meta["baseline_composition_bits_by_book"].items()
            if int(book) in books
        },
        "composition_bits_by_book": {
            book: bits
            for book, bits in meta["composition_bits_by_book"].items()
            if int(book) in books
        },
    }


def score_subset(module: Any, rows: list[dict[str, Any]], meta: dict[str, Any], books: set[int], policy: str | None = None) -> dict[str, Any]:
    subset_rows = [row for row in rows if int(row["book"]) in books]
    return module.summarize(subset_rows, filter_meta(meta, books), policy=policy)


def make_result() -> dict[str, Any]:
    source_gate = load_json(SOURCE_BOUNDARY_GATE)
    assert_boundary("source_boundary_candidate_program_gate", source_gate)
    v3_gate = load_json(EXECUTABLE_V3_GATE)
    assert_boundary("executable_v3_source_boundary_program_gate", v3_gate)
    module = load_source_module()

    scored: dict[str, tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]] = {}
    for system in module.SYSTEMS:
        rows, meta = module.score_system(system)
        summary = module.summarize(rows, meta)
        scored[system] = (rows, meta, summary)

    policy_count = 3
    system_count = len(module.SYSTEMS)
    declaration_bits = math.log2(system_count) + math.log2(policy_count)
    v3_delta = float(v3_gate["summary"]["delta_excluding_seed_vs_v2"])
    v3_delta_after_declaration = v3_delta + declaration_bits

    selected_rows = []
    positive_splits = 0
    total_test_delta = 0.0
    train_selected_systems = []
    for cutoff in CUTOFFS:
        train_books = set(range(10, cutoff))
        test_books = set(range(cutoff, 70))
        train_candidates = []
        for system, (rows, meta, _full_summary) in scored.items():
            train_summary = score_subset(module, rows, meta, train_books)
            train_candidates.append(
                {
                    "system": system,
                    "policy": train_summary["selected_policy"],
                    "train_bits": train_summary["source_boundary_program_bits"],
                    "train_delta": train_summary["delta_vs_v2_residual_bits"],
                    "train_hits": train_summary["copy_hits"],
                }
            )
        train_candidates.sort(key=lambda row: (row["train_bits"], row["system"], row["policy"]))
        selected = train_candidates[0]
        train_selected_systems.append(selected["system"])
        rows, meta, _summary = scored[selected["system"]]
        test_summary = score_subset(module, rows, meta, test_books, policy=selected["policy"])
        if test_summary["delta_vs_v2_residual_bits"] < 0:
            positive_splits += 1
        total_test_delta += float(test_summary["delta_vs_v2_residual_bits"])
        selected_rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": selected["policy"],
                "selected_system": selected["system"],
                "test_bits": test_summary["source_boundary_program_bits"],
                "test_delta_vs_v2": test_summary["delta_vs_v2_residual_bits"],
                "test_hits": test_summary["copy_hits"],
                "test_v2_bits": test_summary["baseline_v2_residual_bits"],
                "train_bits": selected["train_bits"],
                "train_delta_vs_v2": selected["train_delta"],
                "train_hits": selected["train_hits"],
            }
        )

    system_histogram = {
        system: train_selected_systems.count(system)
        for system in sorted(set(train_selected_systems))
    }
    robust = (
        v3_delta_after_declaration < 0
        and positive_splits >= 4
        and total_test_delta < 0
    )
    classification = (
        "PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_ROBUST"
        if robust
        else "EXECUTABLE_V3_SOURCE_BOUNDARY_FULLFIT_ONLY"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "robust_promotion_retained": robust,
            "row0_status": "unchanged_exogenous",
            "plaintext_claim": False,
            "translation_delta": "NONE",
            "next_blocker": (
                "179/208 fallback copy intervals remain; next work should derive "
                "additional source-boundary systems or fallback structure without "
                "posthoc full-corpus selection"
            ),
        },
        "inputs": {
            "executable_v3_source_boundary_program_gate": rel(EXECUTABLE_V3_GATE),
            "source_boundary_candidate_program_gate": rel(SOURCE_BOUNDARY_GATE),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "executable_v3_source_boundary_robustness_gate.v1",
        "scope": "analysis_only_executable_v3_source_boundary_robustness",
        "summary": {
            "declaration_bits_system_plus_policy": declaration_bits,
            "fullfit_delta_after_declaration": v3_delta_after_declaration,
            "fullfit_delta_before_declaration": v3_delta,
            "positive_prefix_selected_splits": positive_splits,
            "prefix_selected_system_histogram": system_histogram,
            "robust": robust,
            "systems_tested": system_count,
            "policies_tested": policy_count,
            "total_prefix_selected_test_delta": total_test_delta,
        },
        "prefix_selection_rows": selected_rows,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Executable v3 Source-Boundary Robustness Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Does the executable v3 source-boundary reduction survive explicit "
        "system/policy declaration cost and prefix-only system selection?",
        "",
        "## Summary",
        "",
        f"- Systems tested: `{s['systems_tested']}`.",
        f"- Policies tested: `{s['policies_tested']}`.",
        f"- Declaration bits for system+policy: `{s['declaration_bits_system_plus_policy']:.3f}`.",
        f"- Full-fit v3 delta before declaration: `{s['fullfit_delta_before_declaration']:.3f}` bits.",
        f"- Full-fit v3 delta after declaration: `{s['fullfit_delta_after_declaration']:.3f}` bits.",
        f"- Prefix-selected positive test splits: `{s['positive_prefix_selected_splits']}/5`.",
        f"- Prefix-selected total test delta: `{s['total_prefix_selected_test_delta']:.3f}` bits.",
        f"- Prefix-selected systems: `{s['prefix_selected_system_histogram']}`.",
        "",
        "## Prefix Selection",
        "",
        "| Cutoff | Selected system | Policy | Train delta | Test hits | Test delta |",
        "| ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for row in result["prefix_selection_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_system']}` | `{row['selected_policy']}` | "
            f"`{row['train_delta_vs_v2']:.3f}` | `{row['test_hits']}` | "
            f"`{row['test_delta_vs_v2']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_ROBUST`: the v3 ledger "
                "reduction survives declaration cost and prefix-selected systems."
                if result["summary"]["robust"]
                else "`EXECUTABLE_V3_SOURCE_BOUNDARY_FULLFIT_ONLY`: the reduction "
                "does not survive the robustness gate."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Executable v3 Source-Boundary Robustness Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit checks whether the v3 source-boundary program is more than a "
        "full-corpus selected ledger improvement. It charges the finite "
        "system+policy declaration and repeats the validation with system+policy "
        "selected only from prefix books.",
        "",
        f"After declaring one of `{s['systems_tested']}` systems and one of "
        f"`{s['policies_tested']}` policies, the full-fit v3 delta is still "
        f"`{s['fullfit_delta_after_declaration']:.3f}` bits. Prefix-only system "
        f"selection improves the suffix in `{s['positive_prefix_selected_splits']}/5` "
        f"splits with aggregate delta `{s['total_prefix_selected_test_delta']:.3f}` bits.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_EXECUTABLE_V3_SOURCE_BOUNDARY_ROBUST`. The executable v3 "
            "source-boundary ledger remains promoted under declaration cost and "
            "prefix-selected system/policy validation."
            if result["summary"]["robust"]
            else "`EXECUTABLE_V3_SOURCE_BOUNDARY_FULLFIT_ONLY`."
        ),
        "",
        "The result remains partial: the fallback copy interval ledger, literal "
        "payload, seed payload, and row0 are still external.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_executable_v3_source_boundary_robustness_gate.py](../scripts/01_executable_v3_source_boundary_robustness_gate.py)",
        "- [01_executable_v3_source_boundary_robustness_gate.json](test_results/01_executable_v3_source_boundary_robustness_gate.json)",
        "- [01_executable_v3_source_boundary_robustness_gate.md](test_results/01_executable_v3_source_boundary_robustness_gate.md)",
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
