#!/usr/bin/env python3
"""Internal-start beam control gate.

The x64 capacity gate reduced the paid opcount+cutpoint+type ledger, but that
promotion is only useful if the x64 beam preferentially contains the true
coarse sequences rather than any same-multiset sequence. This gate performs
that missing control with the same decoder settings.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "internal_start_beam_control_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

CAPACITY_GATE = (
    ROOT
    / "analysis"
    / "internal_start_beam_capacity_audit_20260622"
    / "reports"
    / "test_results"
    / "01_internal_start_beam_capacity_gate.json"
)
BOOK_LEVEL_SCRIPT = (
    ROOT
    / "analysis"
    / "book_level_coarse_length_controller_audit_20260622"
    / "scripts"
    / "01_book_level_coarse_length_controller_gate.py"
)

JSON_OUT = TEST_RESULTS / "01_internal_start_beam_control_gate.json"
MD_OUT = TEST_RESULTS / "01_internal_start_beam_control_gate.md"
FINAL_OUT = FRONT / "reports" / "final_internal_start_beam_control_audit.md"

WIDTH_LABEL = "x64"
SEQ_BEAM = 768
BOOK_BEAM = 1920
RANDOM_TRIALS = 200
RANDOM_SEED = 46920260622 + 64


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    decision = data.get("decision", {})
    row0 = decision.get("row0_status") or decision.get("row0_origin_status")
    if row0 not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status: {row0}")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = (len(ordered) - 1) * q
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    frac = index - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def sequence_key(sequence: list[str]) -> tuple[str, ...]:
    return tuple(sequence)


def decode_x64_by_cutoff(bl, books: dict[int, list[dict[str, Any]]], best_pair: str):
    old_seq = bl.SEQ_BEAM_WIDTH
    old_book = bl.BOOK_BEAM_WIDTH
    bl.SEQ_BEAM_WIDTH = SEQ_BEAM
    bl.BOOK_BEAM_WIDTH = BOOK_BEAM
    try:
        count_name, coarse_name = best_pair.split("__", 1)
        cutoff_rows = []
        for cutoff in bl.CUTOFFS:
            train = {book: rows for book, rows in books.items() if book < cutoff}
            test = {book: rows for book, rows in books.items() if book >= cutoff}
            count_model = bl.train_count_model(count_name, train)
            coarse_model = bl.train_coarse_model(coarse_name, train)
            decoded = {}
            payloads = []
            for book, rows in sorted(test.items()):
                true_sequence = [row["symbol"] for row in rows]
                decoded[book] = {
                    sequence_key(item["sequence"]): index + 1
                    for index, item in enumerate(
                        bl.decode_book(count_model, coarse_model, book, rows)
                    )
                }
                payloads.append(
                    {
                        "book": book,
                        "op_count": len(rows),
                        "sequence": true_sequence,
                        "internal_starts": max(0, len(rows) - 1),
                    }
                )
            cutoff_rows.append({"cutoff": cutoff, "decoded": decoded, "payloads": payloads})
    finally:
        bl.SEQ_BEAM_WIDTH = old_seq
        bl.BOOK_BEAM_WIDTH = old_book
    return cutoff_rows


def score_payloads(decoded_by_book: dict[int, dict[tuple[str, ...], int]], payloads: list[dict[str, Any]]) -> dict[str, float]:
    hits = 0
    generated_starts = 0
    rank_bits = 0.0
    for payload in payloads:
        rank = decoded_by_book[payload["book"]].get(sequence_key(payload["sequence"]))
        if rank is not None:
            hits += 1
            generated_starts += payload["internal_starts"]
            rank_bits += math.log2(rank)
    return {
        "generated_internal_starts": generated_starts,
        "rank_bits_for_hits": rank_bits,
        "sequence_hits": hits,
    }


def make_result() -> dict[str, Any]:
    capacity = load_json(CAPACITY_GATE)
    assert_boundary("internal_start_beam_capacity_gate", capacity)
    if capacity["classification"] != "PROMOTED_INTERNAL_START_CAPACITY_LEDGER_REDUCTION_CANDIDATE":
        raise RuntimeError("control gate expects the x64 capacity candidate to be promoted")
    bl = load_module("book_level_controller_for_internal_start_control", BOOK_LEVEL_SCRIPT)
    books = bl.load_books()
    best_pair = capacity["summary"]["best_pair"]
    decoded_cutoffs = decode_x64_by_cutoff(bl, books, best_pair)
    rng = random.Random(RANDOM_SEED)

    real = {"generated_internal_starts": 0.0, "rank_bits_for_hits": 0.0, "sequence_hits": 0.0}
    control_totals = []
    cutoff_rows = []
    for cutoff_row in decoded_cutoffs:
        real_cutoff = score_payloads(cutoff_row["decoded"], cutoff_row["payloads"])
        for key in real:
            real[key] += real_cutoff[key]
        control_rows = []
        for _ in range(RANDOM_TRIALS):
            books = [payload["book"] for payload in cutoff_row["payloads"]]
            payload_values = [
                {
                    "internal_starts": payload["internal_starts"],
                    "op_count": payload["op_count"],
                    "sequence": payload["sequence"],
                }
                for payload in cutoff_row["payloads"]
            ]
            rng.shuffle(payload_values)
            shuffled = [
                {"book": book, **payload}
                for book, payload in zip(books, payload_values)
            ]
            control_rows.append(score_payloads(cutoff_row["decoded"], shuffled))
        cutoff_control = {
            "generated_internal_starts_p95": percentile(
                [row["generated_internal_starts"] for row in control_rows], 0.95
            ),
            "sequence_hits_p95": percentile(
                [row["sequence_hits"] for row in control_rows], 0.95
            ),
        }
        cutoff_rows.append(
            {
                "control": cutoff_control,
                "cutoff": cutoff_row["cutoff"],
                "real": real_cutoff,
            }
        )
        control_totals.extend(control_rows)

    # Total controls preserve the same per-cutoff decoded beams but shuffle each
    # cutoff independently, matching the real prefix-holdout aggregation.
    total_controls = []
    for trial in range(RANDOM_TRIALS):
        total = {"generated_internal_starts": 0.0, "rank_bits_for_hits": 0.0, "sequence_hits": 0.0}
        for cutoff_row in decoded_cutoffs:
            books = [payload["book"] for payload in cutoff_row["payloads"]]
            payload_values = [
                {
                    "internal_starts": payload["internal_starts"],
                    "op_count": payload["op_count"],
                    "sequence": payload["sequence"],
                }
                for payload in cutoff_row["payloads"]
            ]
            rng.shuffle(payload_values)
            shuffled = [
                {"book": book, **payload}
                for book, payload in zip(books, payload_values)
            ]
            scored = score_payloads(cutoff_row["decoded"], shuffled)
            for key in total:
                total[key] += scored[key]
        total_controls.append(total)

    controls = {
        "generated_internal_starts_mean": mean(
            row["generated_internal_starts"] for row in total_controls
        ),
        "generated_internal_starts_p95": percentile(
            [row["generated_internal_starts"] for row in total_controls], 0.95
        ),
        "rank_bits_for_hits_mean": mean(row["rank_bits_for_hits"] for row in total_controls),
        "sequence_hits_mean": mean(row["sequence_hits"] for row in total_controls),
        "sequence_hits_p95": percentile(
            [row["sequence_hits"] for row in total_controls], 0.95
        ),
        "trials": RANDOM_TRIALS,
    }
    beats_controls = (
        real["sequence_hits"] > controls["sequence_hits_p95"]
        and real["generated_internal_starts"] > controls["generated_internal_starts_p95"]
    )
    classification = (
        "PROMOTED_X64_INTERNAL_START_CAPACITY_CONTROLLED_CANDIDATE"
        if beats_controls
        else "X64_INTERNAL_START_CAPACITY_CANDIDATE_DEMOTED_BY_CONTROLS"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": controls,
        "cutoff_rows": cutoff_rows,
        "decision": {
            "beats_same_multiset_controls": beats_controls,
            "generator_promoted": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "book_level_controller_script": rel(BOOK_LEVEL_SCRIPT),
            "internal_start_beam_capacity_gate": rel(CAPACITY_GATE),
            "random_seed": RANDOM_SEED,
            "random_trials": RANDOM_TRIALS,
        },
        "plaintext_claim": False,
        "real": real,
        "schema": "internal_start_beam_control_gate.v1",
        "scope": "analysis_only_same_multiset_control_for_x64_internal_start_capacity",
        "summary": {
            "beats_same_multiset_controls": beats_controls,
            "classification": classification,
            "real_generated_internal_starts": real["generated_internal_starts"],
            "real_sequence_hits": real["sequence_hits"],
            "x64_capacity_saving_bits": capacity["rows"][-1][
                "saving_vs_explicit_opcount_cutpoint_type_bits_with_width_id"
            ],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Internal Start Beam Control Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Does the x64 internal-start capacity candidate beat same-multiset shuffled "
        "coarse-sequence controls under the same decoded beams?",
        "",
        "## Summary",
        "",
        f"- Real sequence hits: `{s['real_sequence_hits']:.0f}`.",
        f"- Control sequence-hit p95: `{c['sequence_hits_p95']:.3f}`.",
        f"- Real generated internal starts: `{s['real_generated_internal_starts']:.0f}`.",
        f"- Control generated-start p95: `{c['generated_internal_starts_p95']:.3f}`.",
        f"- x64 capacity saving: `{s['x64_capacity_saving_bits']:.3f}` bits.",
        f"- Beats same-multiset controls: `{s['beats_same_multiset_controls']}`.",
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Real hits | Control p95 hits | Real starts | Control p95 starts |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['real']['sequence_hits']:.0f}` | "
            f"`{row['control']['sequence_hits_p95']:.3f}` | "
            f"`{row['real']['generated_internal_starts']:.0f}` | "
            f"`{row['control']['generated_internal_starts_p95']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
        ]
    )
    if result["decision"]["beats_same_multiset_controls"]:
        lines.append(
            "The x64 capacity candidate survives same-multiset controls. It remains "
            "a capacity-ledger candidate, not an exact generator, because misses "
            "and residual corrections are still paid."
        )
    else:
        lines.append(
            "The x64 capacity candidate is demoted by same-multiset controls. The "
            "paid ledger reduction is not enough without evidence that the true "
            "coarse sequences are preferentially preserved."
        )
    lines.extend(
        [
            "",
            "`row0`, plaintext, translation, and `compression_bound` remain unchanged.",
        ]
    )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result, MD_OUT)
    write_markdown(result, FINAL_OUT)
    print(
        json.dumps(
            {
                "beats_controls": result["summary"]["beats_same_multiset_controls"],
                "classification": result["classification"],
                "control_generated_start_p95": result["controls"][
                    "generated_internal_starts_p95"
                ],
                "control_sequence_hit_p95": result["controls"]["sequence_hits_p95"],
                "real_generated_internal_starts": result["summary"][
                    "real_generated_internal_starts"
                ],
                "real_sequence_hits": result["summary"]["real_sequence_hits"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
