#!/usr/bin/env python3
"""Deterministic endpoint-cascade boundary program gate.

Executable v4 promotes an `end_first` one-sided boundary program, but leaves
start-only anchors unused. This gate tests whether a fixed endpoint cascade can
use both one-sided anchor classes without paying a per-copy mode bit.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "endpoint_cascade_boundary_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

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
EXECUTABLE_V4_GATE = (
    ROOT
    / "analysis"
    / "executable_v4_one_sided_boundary_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v4_one_sided_boundary_program_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_endpoint_cascade_boundary_program_gate.json"
MD_OUT = TEST_RESULTS / "01_endpoint_cascade_boundary_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_endpoint_cascade_boundary_program_audit.md"

POLICIES = [
    "none",
    "start_first",
    "end_first",
    "best_with_mode_bit",
    "end_then_start",
    "start_then_end",
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


def load_one_sided_module() -> Any:
    spec = importlib.util.spec_from_file_location("one_sided_gate", ONE_SIDED_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {ONE_SIDED_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def choose_endpoint(row: dict[str, Any], policy: str) -> tuple[str, float] | None:
    start_bits = row["start_rank_bits"]
    end_bits = row["end_rank_bits"]
    if policy == "start_first" and start_bits is not None:
        return ("start", float(start_bits))
    if policy == "end_first" and end_bits is not None:
        return ("end", float(end_bits))
    if policy == "end_then_start":
        if end_bits is not None:
            return ("end", float(end_bits))
        if start_bits is not None:
            return ("start", float(start_bits))
    if policy == "start_then_end":
        if start_bits is not None:
            return ("start", float(start_bits))
        if end_bits is not None:
            return ("end", float(end_bits))
    if policy == "best_with_mode_bit":
        options = []
        if start_bits is not None:
            options.append(("start", float(start_bits) + 1.0))
        if end_bits is not None:
            options.append(("end", float(end_bits) + 1.0))
        if options:
            return min(options, key=lambda item: item[1])
    return None


def summarize_policy(
    module: Any,
    rows: list[dict[str, Any]],
    meta: dict[str, Any],
    policy: str,
    books: set[int] | None = None,
) -> dict[str, Any]:
    source_module = module.load_source_module()
    scoped_rows = [row for row in rows if books is None or int(row["book"]) in books]
    copy_rows = [row for row in scoped_rows if row["event_kind"] == "copy"]
    literal_rows = [row for row in scoped_rows if row["event_kind"] == "literal"]
    copy_bits = 0.0
    v3_copy_bits = 0.0
    v4_copy_bits = 0.0
    known_by_key = set()
    v3_known_by_key = set()
    class_counts: dict[str, int] = defaultdict(int)
    for row in copy_rows:
        key = (int(row["book"]), int(row["op_index"]))
        if row["both_hit"]:
            interval_bits = float(row["interval_rank_bits"])
            copy_bits += interval_bits
            v3_copy_bits += interval_bits
            v4_copy_bits += interval_bits
            known_by_key.add(key)
            v3_known_by_key.add(key)
            class_counts["both"] += 1
            continue

        fallback_bits = float(row["copy_hint_rank_bits"])
        v3_copy_bits += fallback_bits
        v4_choice = choose_endpoint(row, "end_first")
        v4_copy_bits += v4_choice[1] if v4_choice is not None else fallback_bits

        chosen = choose_endpoint(row, policy)
        if chosen is not None and policy != "none":
            copy_bits += chosen[1]
            class_counts[f"one_sided_{chosen[0]}"] += 1
        else:
            copy_bits += fallback_bits
            class_counts["fallback"] += 1

    composition_bits = 0.0
    v3_composition_bits = 0.0
    for book, scored_rows in meta["rows_by_book"].items():
        if books is not None and int(book) not in books:
            continue
        truth = meta["truth_by_book"][book]
        known_sum = 0
        unknown = []
        v3_known_sum = 0
        v3_unknown = []
        for scored, op in zip(scored_rows, truth):
            key = (int(scored["book"]), int(scored["op_index"]))
            if scored["event_kind"] == "copy" and key in known_by_key:
                known_sum += int(op["exact_length"])
            else:
                unknown.append(op)
            if scored["event_kind"] == "copy" and key in v3_known_by_key:
                v3_known_sum += int(op["exact_length"])
            else:
                v3_unknown.append(op)
        remaining = int(truth[0]["book_length"]) - known_sum
        composition_bits += math.log2(module.composition_count(source_module, unknown, remaining))
        v3_remaining = int(truth[0]["book_length"]) - v3_known_sum
        v3_composition_bits += math.log2(
            module.composition_count(source_module, v3_unknown, v3_remaining)
        )

    literal_bits = sum(float(row["literal_payload_bits"]) for row in literal_rows)
    residual_bits = copy_bits + composition_bits + literal_bits
    v3_residual_bits = v3_copy_bits + v3_composition_bits + literal_bits
    v4_residual_bits_without_declaration = v4_copy_bits + composition_bits + literal_bits
    return {
        "class_counts": dict(class_counts),
        "composition_bits": composition_bits,
        "copy_bits": copy_bits,
        "copy_ops": len(copy_rows),
        "delta_vs_v3_residual_bits": residual_bits - v3_residual_bits,
        "delta_vs_v4_residual_without_declaration_bits": residual_bits
        - v4_residual_bits_without_declaration,
        "literal_payload_bits": literal_bits,
        "policy": policy,
        "residual_bits": residual_bits,
        "v3_residual_bits": v3_residual_bits,
        "v4_residual_without_declaration_bits": v4_residual_bits_without_declaration,
    }


def make_result() -> dict[str, Any]:
    one_sided_gate = load_json(ONE_SIDED_GATE)
    executable_v4_gate = load_json(EXECUTABLE_V4_GATE)
    assert_boundary("one_sided_source_boundary_program_gate", one_sided_gate)
    assert_boundary("executable_v4_one_sided_boundary_program_gate", executable_v4_gate)
    module = load_one_sided_module()
    rows, meta = module.build_event_rows()
    policy_summaries = [
        summarize_policy(module, rows, meta, policy)
        for policy in POLICIES
    ]
    best = min(policy_summaries, key=lambda row: row["residual_bits"])
    declaration_bits = math.log2(len(POLICIES))
    v4 = executable_v4_gate["summary"]
    v4_residual = float(v4["v4_residual_bits"])
    best_with_declaration = best["residual_bits"] + declaration_bits
    prefix_rows = []
    positive_vs_v4_splits = 0
    total_prefix_delta_vs_v4 = 0.0
    for cutoff in [20, 30, 40, 50, 60]:
        train_books = set(range(10, cutoff))
        test_books = set(range(cutoff, 70))
        train_scored = [
            summarize_policy(module, rows, meta, policy, books=train_books)
            for policy in POLICIES
        ]
        selected = min(train_scored, key=lambda item: item["residual_bits"])
        test = summarize_policy(module, rows, meta, selected["policy"], books=test_books)
        test_v4_delta = test["delta_vs_v4_residual_without_declaration_bits"]
        if test_v4_delta < 0:
            positive_vs_v4_splits += 1
        total_prefix_delta_vs_v4 += float(test_v4_delta)
        prefix_rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": selected["policy"],
                "test_class_counts": test["class_counts"],
                "test_delta_vs_v3": test["delta_vs_v3_residual_bits"],
                "test_delta_vs_v4_without_declaration": test_v4_delta,
                "test_residual_bits": test["residual_bits"],
                "train_delta_vs_v3": selected["delta_vs_v3_residual_bits"],
                "train_delta_vs_v4_without_declaration": selected[
                    "delta_vs_v4_residual_without_declaration_bits"
                ],
                "train_residual_bits": selected["residual_bits"],
            }
        )

    full_fit_positive = (
        best["policy"] in {"end_then_start", "start_then_end"}
        and best_with_declaration < v4_residual
    )
    promoted = (
        best["policy"] in {"end_then_start", "start_then_end"}
        and best_with_declaration < v4_residual
        and positive_vs_v4_splits >= 4
        and total_prefix_delta_vs_v4 < 0
    )
    weak_candidate = full_fit_positive and not promoted
    online_x64_bits = float(v4["online_x64_coarse_bits"])
    seed_bits = float(v4["seed_payload_bits"])
    executable_external_excluding_seed = online_x64_bits + best_with_declaration
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_ENDPOINT_CASCADE_BOUNDARY_PROGRAM"
            if promoted
            else (
                "WEAK_ENDPOINT_CASCADE_BOUNDARY_CANDIDATE"
                if weak_candidate
                else "endpoint_cascade_boundary_program_not_promoted"
            )
        ),
        "compression_bound_status": "unchanged",
        "decision": {
            "endpoint_cascade_promoted": promoted,
            "next_blocker": (
                "83/208 copy intervals still have neither source endpoint anchored"
                if promoted
                else "deterministic endpoint cascade does not reduce executable v4"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v4_one_sided_boundary_program_gate": rel(EXECUTABLE_V4_GATE),
            "one_sided_source_boundary_program_gate": rel(ONE_SIDED_GATE),
            "one_sided_source_boundary_script": rel(ONE_SIDED_SCRIPT),
        },
        "plaintext_claim": False,
        "policy_summaries": policy_summaries,
        "prefix_selection_rows": prefix_rows,
        "row0_status": "unchanged_exogenous",
        "schema": "endpoint_cascade_boundary_program_gate.v1",
        "scope": "analysis_only_endpoint_cascade_boundary_program",
        "summary": best | {
            "declaration_bits_policy": declaration_bits,
            "delta_after_declaration_vs_v4": best_with_declaration - v4_residual,
            "executable_external_bits_excluding_seed": executable_external_excluding_seed,
            "executable_external_bits_including_seed": executable_external_excluding_seed + seed_bits,
            "full_fit_positive_after_declaration": full_fit_positive,
            "positive_prefix_selected_splits_vs_v4": positive_vs_v4_splits,
            "promoted": promoted,
            "weak_candidate": weak_candidate,
            "total_prefix_selected_delta_vs_v4": total_prefix_delta_vs_v4,
            "v4_external_bits_excluding_seed": float(v4["v4_external_bits_excluding_seed"]),
            "v4_residual_bits": v4_residual,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Endpoint-Cascade Boundary Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can a fixed endpoint cascade use both end-only and start-only anchors "
        "without paying a per-copy mode bit?",
        "",
        "## Policy Costs",
        "",
        "| Policy | Residual bits | Delta vs v3 | Delta vs v4 no-decl | Copy bits | Composition bits | Classes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["policy_summaries"]:
        lines.append(
            f"| `{row['policy']}` | `{row['residual_bits']:.3f}` | "
            f"`{row['delta_vs_v3_residual_bits']:.3f}` | "
            f"`{row['delta_vs_v4_residual_without_declaration_bits']:.3f}` | "
            f"`{row['copy_bits']:.3f}` | `{row['composition_bits']:.3f}` | "
            f"`{row['class_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Selection",
            "",
            "| Cutoff | Selected policy | Train delta vs v4 no-decl | Test delta vs v4 no-decl | Test classes |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["prefix_selection_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_policy']}` | "
            f"`{row['train_delta_vs_v4_without_declaration']:.3f}` | "
            f"`{row['test_delta_vs_v4_without_declaration']:.3f}` | "
            f"`{row['test_class_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Best policy: `{s['policy']}`.",
            f"- Declaration bits for `{len(POLICIES)}` tested policies: `{s['declaration_bits_policy']:.3f}`.",
            f"- Delta after declaration vs v4 residual: `{s['delta_after_declaration_vs_v4']:.3f}` bits.",
            f"- Prefix-selected positive splits vs v4: `{s['positive_prefix_selected_splits_vs_v4']}/5`.",
            f"- Prefix-selected aggregate delta vs v4: `{s['total_prefix_selected_delta_vs_v4']:.3f}` bits.",
            "",
            (
                "`PROMOTED_ENDPOINT_CASCADE_BOUNDARY_PROGRAM`: a fixed cascade "
                "reduces the executable v4 ledger without a per-event mode bit."
                if s["promoted"]
                else (
                    "`WEAK_ENDPOINT_CASCADE_BOUNDARY_CANDIDATE`: full-fit cost "
                    "falls, but prefix holdout is not stable enough to promote."
                    if s["weak_candidate"]
                    else "`endpoint_cascade_boundary_program_not_promoted`."
                )
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Endpoint-Cascade Boundary Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested deterministic endpoint cascades after executable v4. "
        "The promoted v4 `end_first` policy uses end-only source-boundary anchors "
        "but leaves start-only anchors in fallback. The cascade policies try to "
        "use both classes through fixed precedence, so no per-copy mode bit is paid.",
        "",
        f"The best policy is `{s['policy']}`. After charging "
        f"`{s['declaration_bits_policy']:.3f}` bits to declare one of "
        f"`{len(POLICIES)}` tested policies, residual cost changes versus v4 by "
        f"`{s['delta_after_declaration_vs_v4']:.3f}` bits. Prefix-only selection "
        f"improves `{s['positive_prefix_selected_splits_vs_v4']}/5` suffix splits "
        f"with aggregate delta `{s['total_prefix_selected_delta_vs_v4']:.3f}` bits.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_ENDPOINT_CASCADE_BOUNDARY_PROGRAM`."
            if s["promoted"]
            else (
                "`WEAK_ENDPOINT_CASCADE_BOUNDARY_CANDIDATE`. Full-fit cost falls, "
                "but prefix holdout is not stable enough to replace executable v4."
                if s["weak_candidate"]
                else "`endpoint_cascade_boundary_program_not_promoted`."
            )
        ),
        "",
        (
            "The endpoint cascade is still partial: copy intervals with neither "
            "endpoint anchored, literal payload, seed payload, and row0 remain external."
            if s["promoted"]
            else "The executable v4 ledger remains the current promoted endpoint-boundary program."
        ),
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_endpoint_cascade_boundary_program_gate.py](../scripts/01_endpoint_cascade_boundary_program_gate.py)",
        "- [01_endpoint_cascade_boundary_program_gate.json](test_results/01_endpoint_cascade_boundary_program_gate.json)",
        "- [01_endpoint_cascade_boundary_program_gate.md](test_results/01_endpoint_cascade_boundary_program_gate.md)",
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
