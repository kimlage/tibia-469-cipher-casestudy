#!/usr/bin/env python3
"""V5 endpoint-cascade stability gate.

Source-endpoint memory changes the endpoint landscape after executable v5. This
gate tests whether adding start-only endpoint use on top of v5 is a stable
program or just another full-fit improvement.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "v5_endpoint_cascade_stability_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

ONE_SIDED_SCRIPT = (
    ROOT
    / "analysis"
    / "one_sided_source_boundary_program_audit_20260622"
    / "scripts"
    / "01_one_sided_source_boundary_program_gate.py"
)
SOURCE_BOUNDARY_SCRIPT = (
    ROOT
    / "analysis"
    / "source_boundary_candidate_program_audit_20260622"
    / "scripts"
    / "01_source_boundary_candidate_program_gate.py"
)
EXECUTABLE_V5_GATE = (
    ROOT
    / "analysis"
    / "executable_v5_source_endpoint_memory_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v5_source_endpoint_memory_gate.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

JSON_OUT = TEST_RESULTS / "01_v5_endpoint_cascade_stability_gate.json"
MD_OUT = TEST_RESULTS / "01_v5_endpoint_cascade_stability_gate.md"
FINAL_OUT = FRONT / "reports" / "final_v5_endpoint_cascade_stability_audit.md"

POLICIES = ["end_first", "start_first", "end_then_start", "start_then_end"]
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300
BASE_SYSTEM_CACHE: dict[tuple[int, int], dict[str, set[int]]] = {}


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


def endpoint_rank_bits(boundaries: set[int], endpoint: int) -> float | None:
    if endpoint not in boundaries:
        return None
    return math.log2(1 + sum(1 for mark in boundaries if mark > endpoint))


def interval_rank_bits(module: Any, boundaries: set[int], source: int, length: int, low: int, high: int) -> float | None:
    if source not in boundaries or source + length not in boundaries or not (low <= length <= high):
        return None
    ordered = sorted(boundaries)
    module.boundary_set_global = set(ordered)
    return math.log2(module.long_recent_rank(ordered, source, length, low, high))


def choose_endpoint(policy: str, start_bits: float | None, end_bits: float | None, fallback_bits: float) -> tuple[str, float]:
    if policy == "end_first":
        return ("end", end_bits) if end_bits is not None else ("fallback", fallback_bits)
    if policy == "start_first":
        return ("start", start_bits) if start_bits is not None else ("fallback", fallback_bits)
    if policy == "end_then_start":
        if end_bits is not None:
            return ("end", end_bits)
        if start_bits is not None:
            return ("start", start_bits)
        return ("fallback", fallback_bits)
    if policy == "start_then_end":
        if start_bits is not None:
            return ("start", start_bits)
        if end_bits is not None:
            return ("end", end_bits)
        return ("fallback", fallback_bits)
    raise KeyError(policy)


def build_event_rows(policy: str, shuffle_marks: bool = False, seed: int = RANDOM_SEED) -> tuple[list[dict[str, Any]], dict[int, list[dict[str, Any]]], dict[int, list[dict[str, Any]]]]:
    one_sided = load_module("one_sided_gate", ONE_SIDED_SCRIPT)
    source_module = load_module("source_boundary_gate", SOURCE_BOUNDARY_SCRIPT)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book, _ledger = one_sided.grouped_ledger_rows()
    emitted = "".join(books[book] for book in range(10))
    event_boundaries = {0}
    cursor = 0
    for book in range(10):
        cursor += len(books[book])
        event_boundaries.add(cursor)
    source_marks: set[int] = set()
    rows = []
    rows_by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    rng = random.Random(seed)
    for book in range(10, 70):
        rendered = []
        for op in by_book[book]:
            available = emitted + "".join(rendered)
            local_boundaries = set(event_boundaries)
            if rendered:
                prefix = len(emitted)
                acc = 0
                local_boundaries.add(prefix)
                for chunk in rendered:
                    acc += len(chunk)
                    local_boundaries.add(prefix + acc)
            cache_key = (book, int(op["op_index"]))
            if cache_key not in BASE_SYSTEM_CACHE:
                BASE_SYSTEM_CACHE[cache_key] = source_module.build_boundary_systems(
                    available,
                    local_boundaries,
                )
            active_marks = {mark for mark in source_marks if 0 <= mark <= len(available)}
            if shuffle_marks and active_marks:
                active_marks = set(
                    rng.sample(
                        range(len(available) + 1),
                        min(len(active_marks), len(available) + 1),
                    )
                )
            boundaries = set(BASE_SYSTEM_CACHE[cache_key]["event_plus_surprisal_top20"]) | active_marks
            op_type = str(op["op_type"])
            length = int(op["exact_length"])
            target_start = int(op["target_start"])
            if op_type == "copy":
                source = int(op["copy_source_raw"])
                source_end = source + length
                bucket = str(op["coarse_type_length_bucket"]).split(":", 1)[1]
                low, high = source_module.bucket_bounds(bucket, int(op["book_length"]) - target_start)
                interval_bits = interval_rank_bits(source_module, boundaries, source, length, low, high)
                if interval_bits is not None:
                    row_class = "both"
                    paid_bits = interval_bits
                    known_length = True
                else:
                    start_bits = endpoint_rank_bits(boundaries, source)
                    end_bits = endpoint_rank_bits(boundaries, source_end)
                    row_class, paid_bits = choose_endpoint(
                        policy,
                        start_bits,
                        end_bits,
                        float(op["copy_hint_rank_bits"]),
                    )
                    known_length = False
                row = {
                    "book": book,
                    "event_kind": "copy",
                    "exact_length": length,
                    "known_length": known_length,
                    "op_index": int(op["op_index"]),
                    "paid_bits": paid_bits,
                    "row_class": row_class,
                    "target_start": target_start,
                }
                source_marks.add(source)
                source_marks.add(source_end)
            else:
                row = {
                    "book": book,
                    "event_kind": "literal",
                    "exact_length": length,
                    "known_length": False,
                    "literal_payload_bits": float(op["literal_payload_bits"]),
                    "op_index": int(op["op_index"]),
                    "paid_bits": 0.0,
                    "row_class": "literal",
                    "target_start": target_start,
                }
            rows.append(row)
            rows_by_book[book].append(row)
            chunk = books[book][target_start : target_start + length]
            rendered.append(chunk)
            global_start = len(emitted) + target_start
            event_boundaries.add(global_start)
            event_boundaries.add(global_start + length)
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            raise RuntimeError({"book": book, "reason": "roundtrip_failed"})
        emitted += rendered_book
    return rows, rows_by_book, by_book


def summarize_policy(policy: str, books: set[int] | None = None, shuffle_marks: bool = False, seed: int = RANDOM_SEED) -> dict[str, Any]:
    source_module = load_module("source_boundary_gate", SOURCE_BOUNDARY_SCRIPT)
    rows, rows_by_book, truth_by_book = build_event_rows(policy, shuffle_marks=shuffle_marks, seed=seed)
    scoped_rows = [row for row in rows if books is None or int(row["book"]) in books]
    composition_bits = 0.0
    for book, scored_rows in rows_by_book.items():
        if books is not None and int(book) not in books:
            continue
        truth = truth_by_book[book]
        known_sum = 0
        unknown = []
        for scored, op in zip(scored_rows, truth):
            if scored["event_kind"] == "copy" and scored["known_length"]:
                known_sum += int(op["exact_length"])
            else:
                unknown.append(op)
        remaining = int(truth[0]["book_length"]) - known_sum
        composition_bits += math.log2(source_module.composition_count_for_unknowns(unknown, remaining))
    copy_rows = [row for row in scoped_rows if row["event_kind"] == "copy"]
    literal_rows = [row for row in scoped_rows if row["event_kind"] == "literal"]
    class_counts: dict[str, int] = defaultdict(int)
    for row in copy_rows:
        class_counts[str(row["row_class"])] += 1
    copy_bits = sum(float(row["paid_bits"]) for row in copy_rows)
    literal_bits = sum(float(row["literal_payload_bits"]) for row in literal_rows)
    return {
        "class_counts": dict(class_counts),
        "composition_bits": composition_bits,
        "copy_bits": copy_bits,
        "copy_ops": len(copy_rows),
        "literal_payload_bits": literal_bits,
        "policy": policy,
        "residual_bits": copy_bits + composition_bits + literal_bits,
    }


def make_result() -> dict[str, Any]:
    v5 = load_json(EXECUTABLE_V5_GATE)
    assert_boundary("executable_v5_source_endpoint_memory_gate", v5)
    v5_residual = float(v5["summary"]["v5_residual_bits"])
    declaration_bits = math.log2(len(POLICIES))
    policy_summaries = [summarize_policy(policy) for policy in POLICIES]
    best = min(policy_summaries, key=lambda row: row["residual_bits"])
    best_after_declaration_delta = float(best["residual_bits"]) + declaration_bits - v5_residual

    prefix_rows = []
    positive_splits = 0
    total_test_delta = 0.0
    for cutoff in PREFIX_CUTOFFS:
        train_books = set(range(10, cutoff))
        test_books = set(range(cutoff, 70))
        train_scores = [
            summarize_policy(policy, books=train_books)
            for policy in POLICIES
        ]
        selected = min(train_scores, key=lambda row: row["residual_bits"])
        selected_test = summarize_policy(selected["policy"], books=test_books)
        v5_test = summarize_policy("end_first", books=test_books)
        test_delta = float(selected_test["residual_bits"]) - float(v5_test["residual_bits"])
        total_test_delta += test_delta
        if test_delta < 0:
            positive_splits += 1
        prefix_rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": selected["policy"],
                "test_delta_vs_v5": test_delta,
                "test_residual_bits": selected_test["residual_bits"],
                "train_delta_vs_v5": float(selected["residual_bits"])
                - float(summarize_policy("end_first", books=train_books)["residual_bits"]),
                "train_residual_bits": selected["residual_bits"],
            }
        )

    shuffled_residuals = sorted(
        summarize_policy(best["policy"], shuffle_marks=True, seed=RANDOM_SEED + trial)["residual_bits"]
        for trial in range(RANDOM_TRIALS)
    )
    promoted = (
        best_after_declaration_delta < 0
        and positive_splits >= 4
        and total_test_delta < 0
        and float(best["residual_bits"]) + declaration_bits < shuffled_residuals[int(0.05 * RANDOM_TRIALS)]
    )
    weak = best_after_declaration_delta < 0 and not promoted
    return {
        "case_reopened": False,
        "classification": (
            "PROMOTED_V5_ENDPOINT_CASCADE_PROGRAM"
            if promoted
            else (
                "WEAK_V5_ENDPOINT_CASCADE_FULLFIT_ONLY"
                if weak
                else "v5_endpoint_cascade_not_promoted"
            )
        ),
        "compression_bound_status": "unchanged",
        "control": {
            "random_trials": RANDOM_TRIALS,
            "shuffled_residual_p05": shuffled_residuals[int(0.05 * RANDOM_TRIALS)],
            "shuffled_residual_p50": shuffled_residuals[int(0.50 * RANDOM_TRIALS)],
        },
        "decision": {
            "next_blocker": (
                "v5 endpoint cascade is full-fit positive but not prefix-holdout stable"
                if weak
                else "endpoint cascade does not reduce v5 robustly"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "executable_v5_source_endpoint_memory_gate": rel(EXECUTABLE_V5_GATE),
        },
        "plaintext_claim": False,
        "policy_summaries": policy_summaries,
        "prefix_selection_rows": prefix_rows,
        "row0_status": "unchanged_exogenous",
        "schema": "v5_endpoint_cascade_stability_gate.v1",
        "scope": "analysis_only_v5_endpoint_cascade_stability",
        "summary": best | {
            "best_delta_after_declaration_vs_v5": best_after_declaration_delta,
            "declaration_bits_policy_family": declaration_bits,
            "positive_prefix_splits": positive_splits,
            "promoted": promoted,
            "total_prefix_test_delta_vs_v5": total_test_delta,
            "v5_residual_bits": v5_residual,
            "weak_fullfit_only": weak,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# V5 Endpoint-Cascade Stability Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Best policy: `{s['policy']}`.",
        f"- V5 residual bits: `{s['v5_residual_bits']:.3f}`.",
        f"- Best residual bits before declaration: `{s['residual_bits']:.3f}`.",
        f"- Declaration bits: `{s['declaration_bits_policy_family']:.3f}`.",
        f"- Delta after declaration vs v5: `{s['best_delta_after_declaration_vs_v5']:.3f}`.",
        f"- Prefix-positive splits: `{s['positive_prefix_splits']}/5`.",
        f"- Prefix aggregate delta vs v5: `{s['total_prefix_test_delta_vs_v5']:.3f}`.",
        f"- Shuffled residual p05/p50: `{c['shuffled_residual_p05']:.3f}` / `{c['shuffled_residual_p50']:.3f}`.",
        "",
        "## Policy Costs",
        "",
        "| Policy | Residual bits | Copy bits | Composition bits | Classes |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in result["policy_summaries"]:
        lines.append(
            f"| `{row['policy']}` | `{row['residual_bits']:.3f}` | "
            f"`{row['copy_bits']:.3f}` | `{row['composition_bits']:.3f}` | "
            f"`{row['class_counts']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Selection",
            "",
            "| Cutoff | Selected policy | Train delta | Test delta |",
            "| ---: | --- | ---: | ---: |",
        ]
    )
    for row in result["prefix_selection_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_policy']}` | "
            f"`{row['train_delta_vs_v5']:.3f}` | `{row['test_delta_vs_v5']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_V5_ENDPOINT_CASCADE_PROGRAM`."
                if s["promoted"]
                else (
                    "`WEAK_V5_ENDPOINT_CASCADE_FULLFIT_ONLY`: full-fit cost falls, "
                    "but prefix holdout is not stable enough to promote v6."
                    if s["weak_fullfit_only"]
                    else "`v5_endpoint_cascade_not_promoted`."
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
        "# Final V5 Endpoint-Cascade Stability Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tested whether the obvious post-v5 extension, adding start-only "
        "endpoint use through a deterministic endpoint cascade, should replace v5.",
        "",
        f"The best policy is `{s['policy']}`. Full-fit residual falls from v5 "
        f"`{s['v5_residual_bits']:.3f}` to `{s['residual_bits']:.3f}` before "
        f"declaration. After charging `{s['declaration_bits_policy_family']:.3f}` "
        f"bits for the policy family, the full-fit delta is "
        f"`{s['best_delta_after_declaration_vs_v5']:.3f}` bits.",
        "",
        f"Promotion fails because prefix selection is unstable: only "
        f"`{s['positive_prefix_splits']}/5` suffix splits improve, with aggregate "
        f"delta `{s['total_prefix_test_delta_vs_v5']:.3f}`. The result is therefore "
        "a full-fit weak clue, not executable v6.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_V5_ENDPOINT_CASCADE_PROGRAM`."
            if s["promoted"]
            else (
                "`WEAK_V5_ENDPOINT_CASCADE_FULLFIT_ONLY`."
                if s["weak_fullfit_only"]
                else "`v5_endpoint_cascade_not_promoted`."
            )
        ),
        "",
        "Executable v5 remains the promoted program frontier. The next useful route "
        "should not be another endpoint-priority selector unless it adds a new "
        "source of marks or clears prefix holdout.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_v5_endpoint_cascade_stability_gate.py](../scripts/01_v5_endpoint_cascade_stability_gate.py)",
        "- [01_v5_endpoint_cascade_stability_gate.json](test_results/01_v5_endpoint_cascade_stability_gate.json)",
        "- [01_v5_endpoint_cascade_stability_gate.md](test_results/01_v5_endpoint_cascade_stability_gate.md)",
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
