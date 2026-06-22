#!/usr/bin/env python3
"""Paid control gate for the x64 internal-start beam.

The previous same-multiset control showed that the x64 beam contains the real
coarse sequences more often than shuffled payloads. This gate checks the more
important ledger question: does the paid coarse-control stream
(`rank_bits + correction_bits`) beat shuffled payload controls after charging
the same fallback correction used by the executable program?

This deliberately excludes the fine residual composition index from the control
comparison. The composition index remains an external length-residual tape; the
question here is only whether x64 genuinely reduces the coarse control tape.
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
FRONT = ROOT / "analysis" / "internal_start_beam_paid_control_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

CAPACITY_GATE = (
    ROOT
    / "analysis"
    / "internal_start_beam_capacity_audit_20260622"
    / "reports"
    / "test_results"
    / "01_internal_start_beam_capacity_gate.json"
)
CONTROL_GATE = (
    ROOT
    / "analysis"
    / "internal_start_beam_control_audit_20260622"
    / "reports"
    / "test_results"
    / "01_internal_start_beam_control_gate.json"
)
BOOK_LEVEL_SCRIPT = (
    ROOT
    / "analysis"
    / "book_level_coarse_length_controller_audit_20260622"
    / "scripts"
    / "01_book_level_coarse_length_controller_gate.py"
)

JSON_OUT = TEST_RESULTS / "01_internal_start_beam_paid_control_gate.json"
MD_OUT = TEST_RESULTS / "01_internal_start_beam_paid_control_gate.md"
FINAL_OUT = FRONT / "reports" / "final_internal_start_beam_paid_control_audit.md"

WIDTH_LABEL = "x64"
SEQ_BEAM = 768
BOOK_BEAM = 1920
RANDOM_TRIALS = 200
RANDOM_SEED = 46920260622 + 164


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
                        "internal_starts": max(0, len(rows) - 1),
                        "op_count": len(rows),
                        "sequence": true_sequence,
                    }
                )
            cutoff_rows.append({"cutoff": cutoff, "decoded": decoded, "payloads": payloads})
    finally:
        bl.SEQ_BEAM_WIDTH = old_seq
        bl.BOOK_BEAM_WIDTH = old_book
    return cutoff_rows


def literal_count(sequence: list[str]) -> int:
    return sum(1 for symbol in sequence if symbol.startswith("literal:"))


def direct_coarse_bits(bl, payload: dict[str, Any]) -> float:
    return math.log2(bl.MAX_OPCOUNT) + len(payload["sequence"]) * math.log2(len(bl.VOCAB))


def correction_bits(bl, payload: dict[str, Any]) -> float:
    return direct_coarse_bits(bl, payload)


def score_payloads(
    bl,
    decoded_by_book: dict[int, dict[tuple[str, ...], int]],
    payloads: list[dict[str, Any]],
) -> dict[str, float]:
    direct_bits = 0.0
    generated_starts = 0.0
    rank_bits = 0.0
    correction = 0.0
    sequence_hits = 0.0
    literal_ops = 0.0
    for payload in payloads:
        direct_bits += direct_coarse_bits(bl, payload)
        literal_ops += literal_count(payload["sequence"])
        rank = decoded_by_book[payload["book"]].get(sequence_key(payload["sequence"]))
        if rank is None:
            correction += correction_bits(bl, payload)
        else:
            sequence_hits += 1
            generated_starts += payload["internal_starts"]
            rank_bits += math.log2(rank)
    paid_bits = rank_bits + correction
    return {
        "coarse_direct_bits": direct_bits,
        "coarse_paid_bits": paid_bits,
        "coarse_saving_bits": direct_bits - paid_bits,
        "correction_bits": correction,
        "generated_internal_starts": generated_starts,
        "literal_ops": literal_ops,
        "rank_bits": rank_bits,
        "sequence_hits": sequence_hits,
    }


def shuffled_payloads(rng: random.Random, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    books = [payload["book"] for payload in payloads]
    values = [
        {
            "internal_starts": payload["internal_starts"],
            "op_count": payload["op_count"],
            "sequence": payload["sequence"],
        }
        for payload in payloads
    ]
    rng.shuffle(values)
    return [{"book": book, **payload} for book, payload in zip(books, values)]


def make_result() -> dict[str, Any]:
    capacity = load_json(CAPACITY_GATE)
    control = load_json(CONTROL_GATE)
    assert_boundary("internal_start_beam_capacity_gate", capacity)
    assert_boundary("internal_start_beam_control_gate", control)
    if control["classification"] != "PROMOTED_X64_INTERNAL_START_CAPACITY_CONTROLLED_CANDIDATE":
        raise RuntimeError("paid control gate expects the x64 hit/starts control to pass")

    bl = load_module("book_level_controller_for_paid_internal_start_control", BOOK_LEVEL_SCRIPT)
    books = bl.load_books()
    best_pair = capacity["summary"]["best_pair"]
    decoded_cutoffs = decode_x64_by_cutoff(bl, books, best_pair)
    rng = random.Random(RANDOM_SEED)

    real = {
        "coarse_direct_bits": 0.0,
        "coarse_paid_bits": 0.0,
        "coarse_saving_bits": 0.0,
        "correction_bits": 0.0,
        "generated_internal_starts": 0.0,
        "literal_ops": 0.0,
        "rank_bits": 0.0,
        "sequence_hits": 0.0,
    }
    cutoff_rows = []
    for cutoff_row in decoded_cutoffs:
        real_cutoff = score_payloads(bl, cutoff_row["decoded"], cutoff_row["payloads"])
        for key, value in real_cutoff.items():
            real[key] += value
        cutoff_controls = []
        for _ in range(RANDOM_TRIALS):
            cutoff_controls.append(
                score_payloads(
                    bl,
                    cutoff_row["decoded"],
                    shuffled_payloads(rng, cutoff_row["payloads"]),
                )
            )
        cutoff_rows.append(
            {
                "control": {
                    "coarse_saving_bits_mean": mean(
                        row["coarse_saving_bits"] for row in cutoff_controls
                    ),
                    "coarse_saving_bits_p95": percentile(
                        [row["coarse_saving_bits"] for row in cutoff_controls], 0.95
                    ),
                    "sequence_hits_p95": percentile(
                        [row["sequence_hits"] for row in cutoff_controls], 0.95
                    ),
                },
                "cutoff": cutoff_row["cutoff"],
                "real": real_cutoff,
            }
        )

    total_controls = []
    for _ in range(RANDOM_TRIALS):
        total = {
            "coarse_direct_bits": 0.0,
            "coarse_paid_bits": 0.0,
            "coarse_saving_bits": 0.0,
            "correction_bits": 0.0,
            "generated_internal_starts": 0.0,
            "literal_ops": 0.0,
            "rank_bits": 0.0,
            "sequence_hits": 0.0,
        }
        for cutoff_row in decoded_cutoffs:
            scored = score_payloads(
                bl,
                cutoff_row["decoded"],
                shuffled_payloads(rng, cutoff_row["payloads"]),
            )
            for key, value in scored.items():
                total[key] += value
        total_controls.append(total)

    controls = {
        "coarse_paid_bits_mean": mean(row["coarse_paid_bits"] for row in total_controls),
        "coarse_paid_bits_p05": percentile(
            [row["coarse_paid_bits"] for row in total_controls], 0.05
        ),
        "coarse_saving_bits_mean": mean(
            row["coarse_saving_bits"] for row in total_controls
        ),
        "coarse_saving_bits_p95": percentile(
            [row["coarse_saving_bits"] for row in total_controls], 0.95
        ),
        "generated_internal_starts_p95": percentile(
            [row["generated_internal_starts"] for row in total_controls], 0.95
        ),
        "rank_bits_mean": mean(row["rank_bits"] for row in total_controls),
        "sequence_hits_p95": percentile(
            [row["sequence_hits"] for row in total_controls], 0.95
        ),
        "trials": RANDOM_TRIALS,
    }

    beats_paid_controls = (
        real["coarse_saving_bits"] > controls["coarse_saving_bits_p95"]
        and real["coarse_paid_bits"] < controls["coarse_paid_bits_p05"]
    )
    classification = (
        "PROMOTED_X64_INTERNAL_START_PAID_CONTROLLED_CANDIDATE"
        if beats_paid_controls
        else "X64_INTERNAL_START_PAID_LEDGER_DEMOTED_BY_CONTROLS"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": controls,
        "cutoff_rows": cutoff_rows,
        "decision": {
            "beats_paid_same_multiset_controls": beats_paid_controls,
            "generator_promoted": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "book_level_controller_script": rel(BOOK_LEVEL_SCRIPT),
            "internal_start_beam_capacity_gate": rel(CAPACITY_GATE),
            "internal_start_beam_control_gate": rel(CONTROL_GATE),
            "random_seed": RANDOM_SEED,
            "random_trials": RANDOM_TRIALS,
            "width": WIDTH_LABEL,
        },
        "plaintext_claim": False,
        "real": real,
        "schema": "internal_start_beam_paid_control_gate.v1",
        "scope": "analysis_only_paid_same_multiset_control_for_x64_coarse_control_tape",
        "summary": {
            "beats_paid_same_multiset_controls": beats_paid_controls,
            "classification": classification,
            "control_coarse_paid_bits_p05": controls["coarse_paid_bits_p05"],
            "control_coarse_saving_bits_p95": controls["coarse_saving_bits_p95"],
            "real_coarse_paid_bits": real["coarse_paid_bits"],
            "real_coarse_saving_bits": real["coarse_saving_bits"],
            "real_generated_internal_starts": real["generated_internal_starts"],
            "real_sequence_hits": real["sequence_hits"],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Internal Start Beam Paid Control Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Does the x64 internal-start beam reduce the paid coarse-control tape, "
        "not only the hit/start counts, compared with same-multiset shuffled "
        "payload controls?",
        "",
        "## Summary",
        "",
        f"- Real sequence hits: `{s['real_sequence_hits']:.0f}`.",
        f"- Real generated internal starts: `{s['real_generated_internal_starts']:.0f}`.",
        f"- Real coarse paid bits: `{s['real_coarse_paid_bits']:.3f}`.",
        f"- Control coarse paid bits p05: `{s['control_coarse_paid_bits_p05']:.3f}`.",
        f"- Real coarse saving: `{s['real_coarse_saving_bits']:.3f}` bits.",
        f"- Control coarse saving p95: `{s['control_coarse_saving_bits_p95']:.3f}` bits.",
        f"- Beats paid same-multiset controls: `{s['beats_paid_same_multiset_controls']}`.",
        "",
        "## Control Context",
        "",
        f"- Control sequence-hit p95: `{c['sequence_hits_p95']:.3f}`.",
        f"- Control generated-start p95: `{c['generated_internal_starts_p95']:.3f}`.",
        f"- Control coarse saving mean: `{c['coarse_saving_bits_mean']:.3f}` bits.",
        f"- Control rank bits mean: `{c['rank_bits_mean']:.3f}`.",
        "",
        "## Cutoff Rows",
        "",
        "| Cutoff | Real saving | Control p95 saving | Real paid bits | Real hits | Control p95 hits |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['real']['coarse_saving_bits']:.3f}` | "
            f"`{row['control']['coarse_saving_bits_p95']:.3f}` | "
            f"`{row['real']['coarse_paid_bits']:.3f}` | "
            f"`{row['real']['sequence_hits']:.0f}` | "
            f"`{row['control']['sequence_hits_p95']:.3f}` |"
        )
    lines.extend(["", "## Decision", ""])
    if result["decision"]["beats_paid_same_multiset_controls"]:
        lines.append(
            "The x64 route survives the paid control. It is now a controlled "
            "coarse-control tape reduction candidate: the beam plus rank/correction "
            "stream is cheaper for the real payload than for same-multiset shuffles."
        )
    else:
        lines.append(
            "The x64 route is demoted at the paid-control level. Its hit/start "
            "advantage does not translate into a controlled coarse-control tape "
            "reduction."
        )
    lines.extend(
        [
            "",
            "Boundary: this still does not promote an executable generation formula. "
            "The fine residual composition index, missed sequences, literal payload, "
            "copy/source hints, seed payload, and `row0` remain external or paid.",
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
                "beats_paid_controls": result["summary"][
                    "beats_paid_same_multiset_controls"
                ],
                "classification": result["classification"],
                "control_coarse_saving_p95": result["summary"][
                    "control_coarse_saving_bits_p95"
                ],
                "real_coarse_saving": result["summary"]["real_coarse_saving_bits"],
                "real_sequence_hits": result["summary"]["real_sequence_hits"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
