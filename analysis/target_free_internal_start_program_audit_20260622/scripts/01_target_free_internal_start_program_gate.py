#!/usr/bin/env python3
"""Target-free internal start program gate.

The parser/decoder frontier synthesis identified internal operation starts as
the active blocker. This gate tests whether the already-promoted book-level
coarse length controller actually reduces that blocker when interpreted as a
start generator:

- grant only book order and book_length;
- train op_count and coarse type:length_bucket controllers on prefix books;
- decode a beam of coarse operation sequences for held-out books;
- if the true coarse sequence is in beam, pay beam-rank plus a per-book
  residual-composition index to recover exact lengths and therefore exact
  internal starts by cumulative sum;
- if the true coarse sequence misses beam, pay an explicit correction.

No target text, plaintext, semantics, fan glosses, or row0-origin evidence is
used to select the sequence.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "target_free_internal_start_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOK_LEVEL_SCRIPT = (
    ROOT
    / "analysis"
    / "book_level_coarse_length_controller_audit_20260622"
    / "scripts"
    / "01_book_level_coarse_length_controller_gate.py"
)
BOOK_LEVEL_GATE = (
    ROOT
    / "analysis"
    / "book_level_coarse_length_controller_audit_20260622"
    / "reports"
    / "test_results"
    / "01_book_level_coarse_length_controller_gate.json"
)
FRONTIER_SYNTHESIS = (
    ROOT
    / "analysis"
    / "parser_decoder_frontier_synthesis_audit_20260622"
    / "reports"
    / "test_results"
    / "01_parser_decoder_frontier_synthesis.json"
)

JSON_OUT = TEST_RESULTS / "01_target_free_internal_start_program_gate.json"
MD_OUT = TEST_RESULTS / "01_target_free_internal_start_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_target_free_internal_start_program_audit.md"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_book_level_module():
    spec = importlib.util.spec_from_file_location("book_level_controller", BOOK_LEVEL_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BOOK_LEVEL_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    ) / math.log(2)


def exact_lengths(rows: list[dict[str, Any]]) -> list[int]:
    return [int(row.get("exact_length", row["length"])) for row in rows]


def exact_types(rows: list[dict[str, Any]]) -> list[str]:
    out = []
    for row in rows:
        if "op_type" in row:
            out.append(str(row["op_type"]))
        else:
            out.append(str(row["type"]))
    return out


def internal_starts_from_lengths(lengths: list[int]) -> list[int]:
    starts = []
    pos = 0
    for length in lengths[:-1]:
        pos += int(length)
        starts.append(pos)
    return starts


def evaluate_cutoff(
    bl,
    books: dict[int, list[dict[str, Any]]],
    cutoff: int,
    count_name: str,
    coarse_name: str,
) -> dict[str, Any]:
    train = {book: rows for book, rows in books.items() if book < cutoff}
    test = {book: rows for book, rows in books.items() if book >= cutoff}
    count_model = bl.train_count_model(count_name, train)
    coarse_model = bl.train_coarse_model(coarse_name, train)

    rows = []
    metrics: Counter[str] = Counter()
    bits = Counter()
    for book, book_rows in sorted(test.items()):
        true_sequence = [row["symbol"] for row in book_rows]
        true_count = len(book_rows)
        book_length = int(book_rows[0]["book_length"])
        lengths = exact_lengths(book_rows)
        types = exact_types(book_rows)
        literal_count = sum(1 for item in types if item == "literal")
        internal_starts = internal_starts_from_lengths(lengths)
        decoded = bl.decode_book(count_model, coarse_model, book, book_rows)

        hit_index = None
        for index, item in enumerate(decoded):
            if item["op_count"] == true_count and item["sequence"] == true_sequence:
                hit_index = index
                break

        composition_count = bl.count_compositions(true_sequence, book_length)
        composition_bits = math.log2(max(1, composition_count))
        opcount_bits = math.log2(bl.MAX_OPCOUNT)
        cutpoint_bits = log2_comb(book_length - 1, true_count - 1)
        type_bits = log2_comb(true_count, literal_count)

        metrics["test_books"] += 1
        metrics["test_ops"] += true_count
        metrics["test_internal_starts"] += max(0, true_count - 1)
        metrics["nontrivial_books"] += int(true_count > 1)
        bits["composition_bits"] += composition_bits
        bits["explicit_opcount_cutpoint_bits"] += opcount_bits + cutpoint_bits
        bits["explicit_opcount_cutpoint_type_bits"] += opcount_bits + cutpoint_bits + type_bits

        if hit_index is None:
            correction_bits = opcount_bits + true_count * math.log2(len(bl.VOCAB))
            rank_bits = 0.0
            generated_internal = 0
            metrics["sequence_miss_books"] += 1
            bits["correction_bits"] += correction_bits
        else:
            correction_bits = 0.0
            rank_bits = math.log2(hit_index + 1)
            generated_internal = max(0, true_count - 1)
            metrics["sequence_hit_books"] += 1
            metrics["generated_internal_starts_before_correction"] += generated_internal
            bits["rank_bits"] += rank_bits

        program_bits = rank_bits + correction_bits + composition_bits
        bits["program_bits"] += program_bits
        rows.append(
            {
                "book": book,
                "book_length": book_length,
                "composition_bits": composition_bits,
                "composition_count": composition_count,
                "correction_bits": correction_bits,
                "cutpoint_bits": cutpoint_bits,
                "generated_internal_starts_before_correction": generated_internal,
                "hit_rank": None if hit_index is None else hit_index + 1,
                "internal_start_count": max(0, true_count - 1),
                "op_count": true_count,
                "program_bits": program_bits,
                "rank_bits": rank_bits,
                "sequence_in_beam": hit_index is not None,
                "top_sequence": decoded[0]["sequence"] if decoded else [],
                "true_sequence": true_sequence,
                "type_bits": type_bits,
            }
        )

    summary = {key: value for key, value in metrics.items()}
    summary.update({key: value for key, value in bits.items()})
    summary["saving_vs_explicit_opcount_cutpoint_bits"] = (
        bits["explicit_opcount_cutpoint_bits"] - bits["program_bits"]
    )
    summary["saving_vs_explicit_opcount_cutpoint_type_bits"] = (
        bits["explicit_opcount_cutpoint_type_bits"] - bits["program_bits"]
    )
    return {
        "cutoff": cutoff,
        "count_model": count_name,
        "coarse_model": coarse_name,
        "rows": rows,
        "summary": summary,
    }


def make_result() -> dict[str, Any]:
    book_level = load_json(BOOK_LEVEL_GATE)
    frontier = load_json(FRONTIER_SYNTHESIS)
    assert_boundary("book_level_controller", book_level)
    assert_boundary("parser_decoder_frontier_synthesis", frontier)
    bl = load_book_level_module()
    books = bl.load_books()
    best_pair = book_level["decision"]["best_pair"]
    count_name, coarse_name = best_pair.split("__", 1)
    cutoff_rows = [
        evaluate_cutoff(bl, books, cutoff, count_name, coarse_name)
        for cutoff in bl.CUTOFFS
    ]
    totals: Counter[str] = Counter()
    examples = []
    for cutoff in cutoff_rows:
        for key, value in cutoff["summary"].items():
            if isinstance(value, (int, float)):
                totals[key] += value
        for row in cutoff["rows"]:
            if not row["sequence_in_beam"] and len(examples) < 8:
                examples.append(
                    {
                        "book": row["book"],
                        "cutoff": cutoff["cutoff"],
                        "op_count": row["op_count"],
                        "top_sequence": row["top_sequence"],
                        "true_sequence": row["true_sequence"],
                    }
                )

    random_p95 = book_level["pair_results"][best_pair]["random_exact_sequence_p95"]
    promotes_candidate = (
        totals["sequence_hit_books"] > random_p95
        and totals["saving_vs_explicit_opcount_cutpoint_type_bits"] > 0
        and totals["generated_internal_starts_before_correction"] > 0
    )
    exact_generator = (
        totals["sequence_hit_books"] == totals["test_books"]
        and totals["sequence_miss_books"] == 0
    )
    classification = (
        "PROMOTED_TARGET_FREE_INTERNAL_START_PROGRAM"
        if exact_generator
        else "PROMOTED_TARGET_FREE_INTERNAL_START_PROGRAM_CANDIDATE"
        if promotes_candidate
        else "WEAK_INTERNAL_START_PROGRAM_CLUE"
        if totals["sequence_hit_books"] > random_p95
        else "TARGET_FREE_INTERNAL_START_PROGRAM_NOT_PROMOTED"
    )

    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "best_pair": best_pair,
            "exact_generator_promoted": exact_generator,
            "program_candidate_promoted": promotes_candidate,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "examples": examples,
        "inputs": {
            "book_level_controller_gate": rel(BOOK_LEVEL_GATE),
            "book_level_controller_script": rel(BOOK_LEVEL_SCRIPT),
            "parser_decoder_frontier_synthesis": rel(FRONTIER_SYNTHESIS),
        },
        "plaintext_claim": False,
        "schema": "target_free_internal_start_program_gate.v1",
        "scope": "analysis_only_internal_start_program_from_book_level_type_length_beam",
        "summary": {
            **dict(totals),
            "best_pair": best_pair,
            "classification": classification,
            "generated_internal_start_fraction": (
                totals["generated_internal_starts_before_correction"]
                / max(1, totals["test_internal_starts"])
            ),
            "random_exact_sequence_p95": random_p95,
            "route_boundary": (
                "program candidate only; exact residual composition index and "
                "coarse-sequence corrections remain external"
            ),
        },
        "cutoff_rows": [
            {
                "cutoff": row["cutoff"],
                "count_model": row["count_model"],
                "coarse_model": row["coarse_model"],
                "summary": row["summary"],
            }
            for row in cutoff_rows
        ],
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    s = result["summary"]
    lines = [
        "# Target-Free Internal Start Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can the promoted book-level coarse length controller reduce the current "
        "internal-operation-start blocker when starts are generated by cumulative "
        "lengths, without using target text to choose the operation sequence?",
        "",
        "## Summary",
        "",
        f"- Best controller pair: `{s['best_pair']}`.",
        f"- Test books across prefix holdouts: `{int(s['test_books'])}`.",
        f"- True coarse sequences in beam: `{int(s['sequence_hit_books'])}/{int(s['test_books'])}`.",
        f"- Random same-multiset exact-sequence p95: `{s['random_exact_sequence_p95']}`.",
        f"- Internal starts generated before correction: `{int(s['generated_internal_starts_before_correction'])}/{int(s['test_internal_starts'])}`.",
        f"- Generated internal-start fraction: `{s['generated_internal_start_fraction']:.3f}`.",
        f"- Program bits: `{s['program_bits']:.3f}`.",
        f"- Rank bits: `{s['rank_bits']:.3f}`.",
        f"- Correction bits: `{s['correction_bits']:.3f}`.",
        f"- Residual composition bits: `{s['composition_bits']:.3f}`.",
        f"- Explicit opcount+cutpoint bits: `{s['explicit_opcount_cutpoint_bits']:.3f}`.",
        f"- Explicit opcount+cutpoint+type bits: `{s['explicit_opcount_cutpoint_type_bits']:.3f}`.",
        f"- Saving vs opcount+cutpoint: `{s['saving_vs_explicit_opcount_cutpoint_bits']:.3f}` bits.",
        f"- Saving vs opcount+cutpoint+type: `{s['saving_vs_explicit_opcount_cutpoint_type_bits']:.3f}` bits.",
        "",
        "## Prefix Rows",
        "",
        "| Cutoff | Books | Sequence hits | Generated starts | Program bits | Explicit start bits | Explicit start+type bits |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["cutoff_rows"]:
        rs = row["summary"]
        lines.append(
            f"| `{row['cutoff']}` | `{int(rs['test_books'])}` | "
            f"`{int(rs['sequence_hit_books'])}` | "
            f"`{int(rs['generated_internal_starts_before_correction'])}/{int(rs['test_internal_starts'])}` | "
            f"`{rs['program_bits']:.3f}` | "
            f"`{rs['explicit_opcount_cutpoint_bits']:.3f}` | "
            f"`{rs['explicit_opcount_cutpoint_type_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
        ]
    )
    if result["decision"]["exact_generator_promoted"]:
        lines.append(
            "The controller is promoted as an exact target-free internal-start program."
        )
    elif result["decision"]["program_candidate_promoted"]:
        lines.append(
            "The controller is promoted only as a target-free internal-start program "
            "candidate: it keeps true coarse sequences in beam above controls and "
            "reduces the paid start/type ledger, but exact residual composition "
            "indices and missed-sequence corrections remain external."
        )
    else:
        lines.append(
            "No target-free internal-start program is promoted. The route remains "
            "a weak clue unless the beam coverage or paid ledger improves."
        )
    lines.extend(
        [
            "",
            f"Boundary: {s['route_boundary']}.",
            "",
            "`row0`, plaintext, translation, and `compression_bound` remain unchanged.",
            "",
            "## Miss Examples",
            "",
            "| Cutoff | Book | Op count |",
            "| ---: | ---: | ---: |",
        ]
    )
    for example in result["examples"]:
        lines.append(
            f"| `{example['cutoff']}` | `{example['book']}` | `{example['op_count']}` |"
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
                "classification": result["classification"],
                "sequence_hits": result["summary"]["sequence_hit_books"],
                "test_books": result["summary"]["test_books"],
                "generated_internal_starts": result["summary"][
                    "generated_internal_starts_before_correction"
                ],
                "test_internal_starts": result["summary"]["test_internal_starts"],
                "program_bits": result["summary"]["program_bits"],
                "saving_vs_start_type": result["summary"][
                    "saving_vs_explicit_opcount_cutpoint_type_bits"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
