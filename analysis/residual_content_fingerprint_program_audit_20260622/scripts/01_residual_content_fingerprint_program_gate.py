#!/usr/bin/env python3
"""Residual content-fingerprint program gate.

The v6 frontier leaves 90 fallback copy choices external. Lineage signatures
and an online residual content basis did not promote. This audit tests a
different content-origin representation: with exact length already paid by the
current executable ledger, can a small paid fingerprint of the target content
select the copied chunk from prior material more cheaply than the v6 copy-hint
tape?

A fingerprint is not free information. For each fallback copy it pays the
fingerprint digits plus a rank among same-length prior chunks matching that
fingerprint. The selected content then emits the target chunk, while source can
be canonicalized after content selection. Promotion requires a paid ledger
reduction, prefix-selected policy support, and random-content controls.

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
FRONT = ROOT / "analysis" / "residual_content_fingerprint_program_audit_20260622"
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
LINEAGE_SCRIPT = (
    ROOT
    / "analysis"
    / "innovation_lineage_basis_audit_20260622"
    / "scripts"
    / "01_innovation_lineage_basis_gate.py"
)
EXECUTABLE_V6_GATE = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v6_literal_span_origin_gate.json"
)
CONTENT_BASIS_FINAL = (
    ROOT
    / "analysis"
    / "residual_content_basis_program_audit_20260622"
    / "reports"
    / "final_residual_content_basis_program_audit.md"
)
FAMILY_HOLDOUT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "08_recipe_reparse_family_holdout.json"
)

JSON_OUT = TEST_RESULTS / "01_residual_content_fingerprint_program_gate.json"
MD_OUT = TEST_RESULTS / "01_residual_content_fingerprint_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_residual_content_fingerprint_program_audit.md"

LOG2_10 = math.log2(10)
MODEL_DECLARATION_BITS = math.log2(15)
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260624
RANDOM_TRIALS = 200

POLICIES = [
    ("prefix", 1),
    ("prefix", 2),
    ("prefix", 3),
    ("prefix", 4),
    ("suffix", 1),
    ("suffix", 2),
    ("suffix", 3),
    ("suffix", 4),
    ("edge", 2),
    ("edge", 3),
    ("edge", 4),
    ("edge", 5),
    ("edge", 6),
    ("edge", 8),
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


def load_lineage_module() -> Any:
    spec = importlib.util.spec_from_file_location("innovation_lineage_basis", LINEAGE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {LINEAGE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def fingerprint(content: str, kind: str, width: int) -> str:
    width = min(width, len(content))
    if kind == "prefix":
        return content[:width]
    if kind == "suffix":
        return content[-width:]
    if kind == "edge":
        left = (width + 1) // 2
        right = width // 2
        if left + right >= len(content):
            return content
        return content[:left] + content[-right:] if right else content[:left]
    raise ValueError(kind)


def fingerprint_digit_count(content: str, kind: str, width: int) -> int:
    return len(fingerprint(content, kind, width))


def unique_chunks_by_length(available: str, length: int) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    if length <= 0 or length > len(available):
        return counts
    for source in range(0, len(available) - length + 1):
        counts[available[source : source + length]] += 1
    return counts


def random_chunk(available: str, length: int, rng: random.Random) -> str:
    if length > len(available):
        return available
    start = rng.randint(0, len(available) - length)
    return available[start : start + length]


def row_chunk_values(row: dict[str, Any]) -> list[str]:
    values = row.get("_chunk_values")
    if values is None:
        chunks = unique_chunks_by_length(str(row["available"]), int(row["exact_length"]))
        values = list(chunks)
        row["_chunk_values"] = values
    return values


def row_fingerprint_counts(row: dict[str, Any], kind: str, width: int) -> dict[str, int]:
    cache = row.setdefault("_fingerprint_count_cache", {})
    key = f"{kind}_{width}"
    if key not in cache:
        counts: dict[str, int] = defaultdict(int)
        for chunk in row_chunk_values(row):
            counts[fingerprint(chunk, kind, width)] += 1
        cache[key] = dict(counts)
    return cache[key]


def build_fallback_event_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    module = load_lineage_module()
    lineage_rows, validation = module.build_lineage_rows()
    if validation["errors"]:
        raise RuntimeError({"lineage_validation_errors": validation["errors"]})
    v6_classes = {
        (int(row["book"]), int(row["op_index"])): row["v6_class"]
        for row in lineage_rows
    }
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    by_book = grouped_ledger_rows()
    stream = "".join(books[book] for book in range(10))
    events = []
    errors = []
    for book in range(10, 70):
        rendered = []
        for op in by_book[book]:
            op_index = int(op["op_index"])
            op_type = str(op["op_type"])
            start = int(op["target_start"])
            length = int(op["exact_length"])
            available = stream + "".join(rendered)
            if op_type == "literal":
                rendered.append(str(op["literal_payload"]))
                continue
            source = int(op["copy_source_raw"])
            copied = available[source : source + length]
            expected = books[book][start : start + length]
            if copied != expected:
                errors.append({"book": book, "op_index": op_index, "reason": "copy_mismatch"})
            if v6_classes[(book, op_index)] == "fallback":
                chunk_counts = unique_chunks_by_length(available, length)
                if expected not in chunk_counts:
                    errors.append(
                        {
                            "book": book,
                            "op_index": op_index,
                            "reason": "content_not_in_candidate_set",
                        }
                    )
                events.append(
                    {
                        "available": available,
                        "book": book,
                        "candidate_unique_count": len(chunk_counts),
                        "content": expected,
                        "copy_hint_rank_bits": float(op["copy_hint_rank_bits"]),
                        "exact_length": length,
                        "op_index": op_index,
                        "source": source,
                        "target_start": start,
                        "_chunk_values": list(chunk_counts),
                    }
                )
            rendered.append(copied)
        rendered_book = "".join(rendered)
        if rendered_book != books[book]:
            errors.append({"book": book, "reason": "book_roundtrip_mismatch"})
        stream += rendered_book
    return events, validation | {"event_build_errors": errors}


def event_bits(row: dict[str, Any], kind: str, width: int, *, content_override: str | None = None) -> float:
    content = content_override if content_override is not None else str(row["content"])
    fp = fingerprint(content, kind, width)
    fp_digits = len(fp)
    fp_counts = row_fingerprint_counts(row, kind, width)
    match_count = fp_counts.get(fp, 0)
    if content not in row_chunk_values(row) and content_override is None:
        raise RuntimeError({"reason": "true_content_missing_from_fingerprint_matches", "row": row})
    ambiguity_bits = math.log2(max(1, match_count))
    return fp_digits * LOG2_10 + ambiguity_bits


def score_policy(
    rows: list[dict[str, Any]],
    kind: str,
    width: int,
    *,
    include_declaration: bool = True,
    randomize_content: bool = False,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    total = MODEL_DECLARATION_BITS if include_declaration else 0.0
    baseline = sum(float(row["copy_hint_rank_bits"]) for row in rows)
    exact_uniques = 0
    total_match_count = 0
    sample = []
    for row in rows:
        content_override = None
        if randomize_content:
            if rng is None:
                raise RuntimeError("rng is required for randomized content")
            content_override = random_chunk(str(row["available"]), int(row["exact_length"]), rng)
        bits = event_bits(row, kind, width, content_override=content_override)
        total += bits
        fp = fingerprint(content_override or str(row["content"]), kind, width)
        match_count = row_fingerprint_counts(row, kind, width).get(fp, 0)
        if match_count == 1:
            exact_uniques += 1
        total_match_count += match_count
        if len(sample) < 20:
            sample.append(
                {
                    "bits": bits,
                    "book": int(row["book"]),
                    "fingerprint": fp,
                    "match_count": match_count,
                    "op_index": int(row["op_index"]),
                }
            )
    return {
        "average_match_count": total_match_count / len(rows) if rows else 0.0,
        "baseline_copy_hint_bits": baseline,
        "coded_bits": total,
        "delta_vs_copy_hint": total - baseline,
        "fingerprint_kind": kind,
        "fingerprint_width": width,
        "model_declaration_bits": MODEL_DECLARATION_BITS if include_declaration else 0.0,
        "rows": len(rows),
        "sample_events": sample,
        "unique_match_events": exact_uniques,
    }


def score_all(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        f"{kind}_{width}": score_policy(rows, kind, width)
        for kind, width in POLICIES
    }


def prefix_holdouts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        train_scores = {
            f"{kind}_{width}": score_policy(train, kind, width, include_declaration=False)
            for kind, width in POLICIES
        }
        selected_key = min(train_scores, key=lambda key: train_scores[key]["delta_vs_copy_hint"])
        selected = train_scores[selected_key]
        kind = str(selected["fingerprint_kind"])
        width = int(selected["fingerprint_width"])
        test_score = score_policy(test, kind, width)
        out.append(
            {
                "cutoff": cutoff,
                "selected_policy": selected_key,
                "test_delta": test_score["delta_vs_copy_hint"],
                "test_rows": len(test),
                "test_unique_match_events": test_score["unique_match_events"],
                "train_delta": selected["delta_vs_copy_hint"],
                "train_rows": len(train),
            }
        )
    return out


def family_holdouts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = load_json(FAMILY_HOLDOUT)
    out = []
    for family in data["rows"][:20]:
        test_books = {int(book) for book in family["test_books"]}
        train = [row for row in rows if int(row["book"]) not in test_books]
        test = [row for row in rows if int(row["book"]) in test_books]
        if not test:
            continue
        train_scores = {
            f"{kind}_{width}": score_policy(train, kind, width, include_declaration=False)
            for kind, width in POLICIES
        }
        selected_key = min(train_scores, key=lambda key: train_scores[key]["delta_vs_copy_hint"])
        selected = train_scores[selected_key]
        test_score = score_policy(
            test,
            str(selected["fingerprint_kind"]),
            int(selected["fingerprint_width"]),
        )
        out.append(
            {
                "label": str(family["label"]),
                "selected_policy": selected_key,
                "test_delta": test_score["delta_vs_copy_hint"],
                "test_rows": len(test),
                "test_unique_match_events": test_score["unique_match_events"],
            }
        )
    return out


def random_content_control(rows: list[dict[str, Any]], best_kind: str, best_width: int) -> dict[str, Any]:
    observed = score_policy(rows, best_kind, best_width)
    deltas = []
    uniques = []
    rng = random.Random(RANDOM_SEED)
    for _ in range(RANDOM_TRIALS):
        scored = score_policy(
            rows,
            best_kind,
            best_width,
            randomize_content=True,
            rng=rng,
        )
        deltas.append(scored["delta_vs_copy_hint"])
        uniques.append(scored["unique_match_events"])
    deltas.sort()
    uniques.sort()
    return {
        "beats_p05_delta": observed["delta_vs_copy_hint"] < deltas[int(0.05 * RANDOM_TRIALS)],
        "beats_p95_unique": observed["unique_match_events"] > uniques[int(0.95 * RANDOM_TRIALS)],
        "observed_delta": observed["delta_vs_copy_hint"],
        "observed_unique_match_events": observed["unique_match_events"],
        "p05_delta": deltas[int(0.05 * RANDOM_TRIALS)],
        "p50_delta": deltas[int(0.50 * RANDOM_TRIALS)],
        "p95_delta": deltas[int(0.95 * RANDOM_TRIALS)],
        "p05_unique": uniques[int(0.05 * RANDOM_TRIALS)],
        "p50_unique": uniques[int(0.50 * RANDOM_TRIALS)],
        "p95_unique": uniques[int(0.95 * RANDOM_TRIALS)],
        "trials": RANDOM_TRIALS,
    }


def make_result() -> dict[str, Any]:
    v6 = load_json(EXECUTABLE_V6_GATE)
    assert_boundary("executable_v6_literal_span_origin_gate", v6)
    rows, validation = build_fallback_event_rows()
    if validation["event_build_errors"]:
        raise RuntimeError({"event_build_errors": validation["event_build_errors"]})
    policy_scores = score_all(rows)
    best_key = min(policy_scores, key=lambda key: policy_scores[key]["delta_vs_copy_hint"])
    best = policy_scores[best_key]
    prefix = prefix_holdouts(rows)
    family = family_holdouts(rows)
    control = random_content_control(
        rows,
        str(best["fingerprint_kind"]),
        int(best["fingerprint_width"]),
    )
    prefix_positive = sum(1 for row in prefix if row["test_delta"] < 0)
    family_positive = sum(1 for row in family if row["test_delta"] < 0)
    promoted = (
        best["delta_vs_copy_hint"] < 0
        and prefix_positive >= 4
        and control["beats_p05_delta"]
    )
    weak = (
        not promoted
        and best["delta_vs_copy_hint"] < 0
        and prefix_positive >= 3
    )
    classification = (
        "PROMOTED_RESIDUAL_CONTENT_FINGERPRINT_PROGRAM"
        if promoted
        else "WEAK_RESIDUAL_CONTENT_FINGERPRINT_CLUE"
        if weak
        else "residual_content_fingerprint_program_not_promoted"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "control": control,
        "decision": {
            "next_blocker": (
                "paid content fingerprints do not yet establish a compact "
                "content-selection program for the v6 fallback tape"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "family_holdouts": family,
        "inputs": {
            "content_basis_final": rel(CONTENT_BASIS_FINAL),
            "executable_v6_gate": rel(EXECUTABLE_V6_GATE),
            "family_holdout": rel(FAMILY_HOLDOUT),
            "lineage_script": rel(LINEAGE_SCRIPT),
            "unified_external_tape_ledger": rel(UNIFIED_LEDGER),
        },
        "plaintext_claim": False,
        "policy_scores": policy_scores,
        "prefix_holdouts": prefix,
        "row0_status": "unchanged_exogenous",
        "schema": "residual_content_fingerprint_program_gate.v1",
        "scope": "analysis_only_residual_content_fingerprint",
        "summary": {
            "best_delta_vs_copy_hint": best["delta_vs_copy_hint"],
            "best_policy": best_key,
            "best_unique_match_events": best["unique_match_events"],
            "classification": classification,
            "fallback_rows_after_v6": len(rows),
            "family_positive_splits": family_positive,
            "prefix_positive_splits": prefix_positive,
            "promoted": promoted,
            "v6_external_bits_excluding_seed": float(v6["summary"]["v6_external_bits_excluding_seed"]),
        },
        "translation_delta": "NONE",
        "validation": {
            "lineage_atom_count": validation["atom_count"],
            "lineage_digits": validation["lineage_digits"],
            "roundtrip_70_70": validation["roundtrip_70_70"],
            "validation_errors": validation["errors"],
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Residual Content-Fingerprint Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- V6 fallback rows tested: `{s['fallback_rows_after_v6']}`.",
        f"- Best policy: `{s['best_policy']}`.",
        f"- Best unique-match events: `{s['best_unique_match_events']}`.",
        f"- Best delta vs copy-hint: `{s['best_delta_vs_copy_hint']:.3f}` bits.",
        f"- Prefix positive splits: `{s['prefix_positive_splits']}/5`.",
        f"- Family positive splits: `{s['family_positive_splits']}`.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Unique | Avg matches | Coded bits | Delta |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for key, row in sorted(
        result["policy_scores"].items(),
        key=lambda item: item[1]["delta_vs_copy_hint"],
    ):
        lines.append(
            f"| `{key}` | `{row['unique_match_events']}` | `{row['average_match_count']:.3f}` | "
            f"`{row['coded_bits']:.3f}` | `{row['delta_vs_copy_hint']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix Holdout",
            "",
            "| Cutoff | Selected | Test rows | Unique | Test delta |",
            "| ---: | --- | ---: | ---: | ---: |",
        ]
    )
    for row in result["prefix_holdouts"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_policy']}` | `{row['test_rows']}` | "
            f"`{row['test_unique_match_events']}` | `{row['test_delta']:.3f}` |"
        )
    c = result["control"]
    lines.extend(
        [
            "",
            "## Random-Content Control",
            "",
            f"- Observed delta: `{c['observed_delta']:.3f}`.",
            f"- Random p05/p50/p95 delta: `{c['p05_delta']:.3f}` / `{c['p50_delta']:.3f}` / `{c['p95_delta']:.3f}`.",
            f"- Observed unique matches: `{c['observed_unique_match_events']}`.",
            f"- Random p05/p50/p95 unique: `{c['p05_unique']}` / `{c['p50_unique']}` / `{c['p95_unique']}`.",
            f"- Beats p05 delta: `{c['beats_p05_delta']}`.",
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_RESIDUAL_CONTENT_FINGERPRINT_PROGRAM`."
                if s["promoted"]
                else "`residual_content_fingerprint_program_not_promoted`: paid content fingerprints do not replace the remaining v6 fallback copy-hint tape under controls."
            ),
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# Final Residual Content-Fingerprint Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tests whether the remaining v6 fallback copy choices can be "
        "selected by a small paid fingerprint of the copied content. Exact "
        "length is treated as already paid by the executable ledger; the "
        "fingerprint filters same-length prior chunks, and any remaining "
        "ambiguity is paid as a rank.",
        "",
        f"The tested set is the `{s['fallback_rows_after_v6']}` v6 fallback copy "
        f"events. The best policy is `{s['best_policy']}`, with "
        f"`{s['best_unique_match_events']}` unique content selections and delta "
        f"`{s['best_delta_vs_copy_hint']:.3f}` bits versus the existing copy-hint tape.",
        "",
        f"Prefix support is `{s['prefix_positive_splits']}/5` positive splits; "
        f"family support is `{s['family_positive_splits']}` positive splits. "
        "Random-content controls have p05/p50/p95 deltas "
        f"`{c['p05_delta']:.3f}` / `{c['p50_delta']:.3f}` / `{c['p95_delta']:.3f}`; "
        f"observed beats p05 is `{c['beats_p05_delta']}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_RESIDUAL_CONTENT_FINGERPRINT_PROGRAM`."
            if s["promoted"]
            else "`residual_content_fingerprint_program_not_promoted`."
        ),
        "",
        "A paid content fingerprint is not currently a smaller executable "
        "content-selection program than the v6 copy-hint tape. This keeps the "
        "blocker at residual content origin/selection rather than source-address "
        "format.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_residual_content_fingerprint_program_gate.py](../scripts/01_residual_content_fingerprint_program_gate.py)",
        "- [01_residual_content_fingerprint_program_gate.json](test_results/01_residual_content_fingerprint_program_gate.json)",
        "- [01_residual_content_fingerprint_program_gate.md](test_results/01_residual_content_fingerprint_program_gate.md)",
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
