#!/usr/bin/env python3
"""Seed bootstrap transducer program gate.

The seed bootstrap copy-surface audit promoted a strong but target-conditioned
surface clue: books 0..9 have many previous-copy opportunities. This gate asks
the harder generation question: can a target-free online transducer use a
smaller literal innovation tape plus deterministic context-copy policies to
generate the seed stream, or at least reduce the seed payload after paying
corrections?

Inputs granted:
- seed book order and seed book lengths;
- a literal innovation tape extracted from the target-conditioned min_len=4
  surface parse;
- one fixed policy id.

The decoder may emit the next literal tape digit or copy a fixed-length
continuation from a previous occurrence of the current suffix context. It never
looks at the target while choosing actions. Divergence from the true seed stream
is charged as raw suffix correction.

Analysis-only: no row0, plaintext, semantics, or compression-bound change.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "seed_bootstrap_transducer_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
SURFACE_SCRIPT = (
    ROOT
    / "analysis"
    / "seed_bootstrap_copy_surface_audit_20260622"
    / "scripts"
    / "01_seed_bootstrap_copy_surface_gate.py"
)
SURFACE_FINAL = (
    ROOT
    / "analysis"
    / "seed_bootstrap_copy_surface_audit_20260622"
    / "reports"
    / "final_seed_bootstrap_copy_surface_audit.md"
)
EXECUTABLE_V6_GATE = (
    ROOT
    / "analysis"
    / "executable_v6_literal_span_origin_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v6_literal_span_origin_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_seed_bootstrap_transducer_program_gate.json"
MD_OUT = TEST_RESULTS / "01_seed_bootstrap_transducer_program_gate.md"
FINAL_OUT = FRONT / "reports" / "final_seed_bootstrap_transducer_program_audit.md"

LOG2_10 = math.log2(10)
MIN_LEN = 4
MAX_COPY_LEN = 64
RANDOM_SEED = 46920260626
SHUFFLE_TRIALS = 200

CONTEXT_SIZES = [2, 3, 4, 5, 6]
COPY_LENGTHS = [4, 5, 6, 8, 10, 12, 16, 24, 32]
SOURCE_POLICIES = ["latest", "earliest"]


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


def load_surface_module() -> Any:
    spec = importlib.util.spec_from_file_location("seed_bootstrap_surface", SURFACE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SURFACE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_books() -> dict[int, str]:
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    return {book: books[book] for book in range(10)}


def seed_stream() -> tuple[str, list[int]]:
    books = seed_books()
    lengths = [len(books[book]) for book in range(10)]
    return "".join(books[book] for book in range(10)), lengths


def previous_substrings(stream: str, end: int, max_copy_len: int) -> dict[int, set[str]]:
    by_len: dict[int, set[str]] = {}
    for length in range(1, min(max_copy_len, end) + 1):
        values = set()
        for start in range(0, end - length + 1):
            values.add(stream[start : start + length])
        by_len[length] = values
    return by_len


def oracle_surface_parse(stream: str, min_len: int = MIN_LEN) -> dict[str, Any]:
    i = 0
    ops = []
    literal_tape = []
    while i < len(stream):
        by_len = previous_substrings(stream, i, MAX_COPY_LEN)
        best = 0
        for length in range(min(MAX_COPY_LEN, len(stream) - i), min_len - 1, -1):
            if stream[i : i + length] in by_len.get(length, set()):
                best = length
                break
        if best:
            ops.append({"kind": "copy", "length": best, "start": i})
            i += best
        else:
            literal_tape.append(stream[i])
            ops.append({"kind": "literal", "digit": stream[i], "length": 1, "start": i})
            i += 1
    return {
        "copy_digits": sum(int(op["length"]) for op in ops if op["kind"] == "copy"),
        "literal_digits": len(literal_tape),
        "literal_tape": "".join(literal_tape),
        "ops": ops,
    }


def find_context_source(emitted: str, context: str, source_policy: str) -> int | None:
    if not context:
        return None
    positions = []
    search_to = len(emitted) - len(context)
    for start in range(0, search_to + 1):
        if emitted[start : start + len(context)] == context and start + len(context) < len(emitted):
            positions.append(start + len(context))
    if not positions:
        return None
    if source_policy == "latest":
        return positions[-1]
    if source_policy == "earliest":
        return positions[0]
    raise ValueError(source_policy)


def decode_policy(
    literal_tape: str,
    total_len: int,
    *,
    context_size: int,
    copy_len: int,
    source_policy: str,
) -> dict[str, Any]:
    emitted = []
    lit_index = 0
    copy_ops = 0
    literal_ops = 0
    trace = []
    while len(emitted) < total_len:
        prefix = "".join(emitted)
        remaining = total_len - len(emitted)
        source = None
        if len(prefix) >= context_size:
            context = prefix[-context_size:]
            source = find_context_source(prefix, context, source_policy)
        if source is not None and source < len(prefix):
            length = min(copy_len, remaining, len(prefix) - source)
            if length >= MIN_LEN:
                chunk = prefix[source : source + length]
                emitted.extend(chunk)
                copy_ops += 1
                if len(trace) < 80:
                    trace.append(
                        {
                            "kind": "copy",
                            "length": length,
                            "source": source,
                            "start": len(emitted) - length,
                        }
                    )
                continue
        if lit_index >= len(literal_tape):
            break
        emitted.append(literal_tape[lit_index])
        lit_index += 1
        literal_ops += 1
        if len(trace) < 80:
            trace.append({"digit": emitted[-1], "kind": "literal", "start": len(emitted) - 1})
    return {
        "copy_ops": copy_ops,
        "emitted": "".join(emitted),
        "literal_consumed": lit_index,
        "literal_ops": literal_ops,
        "trace_sample": trace,
    }


def exact_prefix_len(generated: str, target: str) -> int:
    limit = min(len(generated), len(target))
    for idx in range(limit):
        if generated[idx] != target[idx]:
            return idx
    return limit


def exact_books_before_correction(generated: str, target: str, book_lengths: list[int]) -> int:
    cursor = 0
    exact = 0
    for length in book_lengths:
        if generated[cursor : cursor + length] == target[cursor : cursor + length]:
            exact += 1
        cursor += length
    return exact


def score_policy(
    target: str,
    book_lengths: list[int],
    literal_tape: str,
    *,
    context_size: int,
    copy_len: int,
    source_policy: str,
) -> dict[str, Any]:
    decoded = decode_policy(
        literal_tape,
        len(target),
        context_size=context_size,
        copy_len=copy_len,
        source_policy=source_policy,
    )
    generated = decoded["emitted"]
    prefix = exact_prefix_len(generated, target)
    raw_bits = len(target) * LOG2_10
    literal_bits = len(literal_tape) * LOG2_10
    correction_digits = len(target) - prefix
    policy_count = len(CONTEXT_SIZES) * len(COPY_LENGTHS) * len(SOURCE_POLICIES)
    policy_bits = math.log2(policy_count)
    corrected_bits = literal_bits + policy_bits + correction_digits * LOG2_10
    return {
        "context_size": context_size,
        "copy_len": copy_len,
        "copy_ops": decoded["copy_ops"],
        "corrected_bits": corrected_bits,
        "correction_digits": correction_digits,
        "delta_corrected_vs_raw_seed": corrected_bits - raw_bits,
        "exact_books_without_correction": exact_books_before_correction(generated, target, book_lengths),
        "exact_prefix_len": prefix,
        "generated_len": len(generated),
        "literal_bits": literal_bits,
        "literal_consumed": decoded["literal_consumed"],
        "literal_ops": decoded["literal_ops"],
        "policy_bits": policy_bits,
        "raw_seed_bits": raw_bits,
        "source_policy": source_policy,
    }


def policy_scoreboard(target: str, book_lengths: list[int], literal_tape: str) -> list[dict[str, Any]]:
    rows = []
    for context_size in CONTEXT_SIZES:
        for copy_len in COPY_LENGTHS:
            for source_policy in SOURCE_POLICIES:
                rows.append(
                    score_policy(
                        target,
                        book_lengths,
                        literal_tape,
                        context_size=context_size,
                        copy_len=copy_len,
                        source_policy=source_policy,
                    )
                )
    rows.sort(key=lambda row: (-row["exact_prefix_len"], row["corrected_bits"]))
    return rows


def shuffled_literal_control(
    target: str,
    book_lengths: list[int],
    literal_tape: str,
    best: dict[str, Any],
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    prefixes = []
    deltas = []
    tape = list(literal_tape)
    for _ in range(SHUFFLE_TRIALS):
        shuffled = list(tape)
        rng.shuffle(shuffled)
        scored = score_policy(
            target,
            book_lengths,
            "".join(shuffled),
            context_size=int(best["context_size"]),
            copy_len=int(best["copy_len"]),
            source_policy=str(best["source_policy"]),
        )
        prefixes.append(scored["exact_prefix_len"])
        deltas.append(scored["delta_corrected_vs_raw_seed"])
    prefixes.sort()
    deltas.sort()
    return {
        "observed_delta": best["delta_corrected_vs_raw_seed"],
        "observed_exact_prefix_len": best["exact_prefix_len"],
        "p05_delta": deltas[int(0.05 * (SHUFFLE_TRIALS - 1))],
        "p50_delta": deltas[int(0.50 * (SHUFFLE_TRIALS - 1))],
        "p95_delta": deltas[int(0.95 * (SHUFFLE_TRIALS - 1))],
        "p05_exact_prefix_len": prefixes[int(0.05 * (SHUFFLE_TRIALS - 1))],
        "p50_exact_prefix_len": prefixes[int(0.50 * (SHUFFLE_TRIALS - 1))],
        "p95_exact_prefix_len": prefixes[int(0.95 * (SHUFFLE_TRIALS - 1))],
        "trials": SHUFFLE_TRIALS,
    }


def make_result() -> dict[str, Any]:
    v6 = load_json(EXECUTABLE_V6_GATE)
    assert_boundary("executable_v6_literal_span_origin_gate", v6)
    target, book_lengths = seed_stream()
    oracle = oracle_surface_parse(target)
    rows = policy_scoreboard(target, book_lengths, str(oracle["literal_tape"]))
    best = rows[0]
    control = shuffled_literal_control(target, book_lengths, str(oracle["literal_tape"]), best)
    exact_promoted = best["exact_prefix_len"] == len(target)
    corrected_reduction = best["delta_corrected_vs_raw_seed"] < 0
    control_beaten = best["exact_prefix_len"] > control["p95_exact_prefix_len"]
    classification = (
        "PROMOTED_SEED_BOOTSTRAP_TRANSDUCER_PROGRAM"
        if exact_promoted and control_beaten
        else "PROMOTED_SEED_BOOTSTRAP_CORRECTION_LEDGER"
        if corrected_reduction and control_beaten
        else "seed_bootstrap_transducer_not_promoted"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "control": control,
        "decision": {
            "generator_status": (
                "target_free_exact" if exact_promoted else "not_promoted_needs_corrections"
            ),
            "next_blocker": (
                "seed copy surface exists, but tested target-free context-copy "
                "policies do not derive enough starts/choices to replace the raw seed payload"
            ),
            "plaintext_claim": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "executable_v6_gate": rel(EXECUTABLE_V6_GATE),
            "surface_audit_final": rel(SURFACE_FINAL),
            "surface_script": rel(SURFACE_SCRIPT),
        },
        "oracle_surface": {
            "copy_digits": oracle["copy_digits"],
            "literal_digits": oracle["literal_digits"],
            "literal_tape_bits": len(str(oracle["literal_tape"])) * LOG2_10,
            "min_len": MIN_LEN,
            "ops": len(oracle["ops"]),
        },
        "plaintext_claim": False,
        "policy_scoreboard": rows[:30],
        "row0_status": "unchanged_exogenous",
        "schema": "seed_bootstrap_transducer_program_gate.v1",
        "scope": "analysis_only_seed_bootstrap_transducer",
        "summary": {
            "best_context_size": best["context_size"],
            "best_copy_len": best["copy_len"],
            "best_corrected_bits": best["corrected_bits"],
            "best_correction_digits": best["correction_digits"],
            "best_delta_corrected_vs_raw_seed": best["delta_corrected_vs_raw_seed"],
            "best_exact_books_without_correction": best["exact_books_without_correction"],
            "best_exact_prefix_len": best["exact_prefix_len"],
            "best_source_policy": best["source_policy"],
            "classification": classification,
            "corrected_reduction": corrected_reduction,
            "exact_promoted": exact_promoted,
            "literal_tape_digits": len(str(oracle["literal_tape"])),
            "raw_seed_bits": len(target) * LOG2_10,
            "seed_digits": len(target),
            "seed_payload_bits_v6": float(v6["summary"]["seed_payload_bits"]),
        },
        "translation_delta": "NONE",
        "validation": {
            "book_lengths": book_lengths,
            "roundtrip_seed_target_len": len(target) == sum(book_lengths),
            "validation_errors": [],
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["control"]
    lines = [
        "# Seed Bootstrap Transducer Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Seed digits: `{s['seed_digits']}`.",
        f"- Literal tape digits from surface parse: `{s['literal_tape_digits']}`.",
        f"- Best policy: context `{s['best_context_size']}`, copy_len `{s['best_copy_len']}`, source `{s['best_source_policy']}`.",
        f"- Exact prefix without correction: `{s['best_exact_prefix_len']}`.",
        f"- Exact seed books without correction: `{s['best_exact_books_without_correction']}/10`.",
        f"- Correction digits: `{s['best_correction_digits']}`.",
        f"- Corrected bits: `{s['best_corrected_bits']:.3f}`.",
        f"- Delta vs raw seed: `{s['best_delta_corrected_vs_raw_seed']:.3f}`.",
        "",
        "## Policy Scoreboard",
        "",
        "| ctx | copy_len | source | prefix | exact books | correction | delta |",
        "| ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in result["policy_scoreboard"][:15]:
        lines.append(
            f"| `{row['context_size']}` | `{row['copy_len']}` | `{row['source_policy']}` | "
            f"`{row['exact_prefix_len']}` | `{row['exact_books_without_correction']}` | "
            f"`{row['correction_digits']}` | `{row['delta_corrected_vs_raw_seed']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Shuffled Literal-Tape Control",
            "",
            f"- Observed exact prefix: `{c['observed_exact_prefix_len']}`.",
            f"- Shuffled p05/p50/p95 exact prefix: `{c['p05_exact_prefix_len']}` / `{c['p50_exact_prefix_len']}` / `{c['p95_exact_prefix_len']}`.",
            f"- Observed delta: `{c['observed_delta']:.3f}`.",
            f"- Shuffled p05/p50/p95 delta: `{c['p05_delta']:.3f}` / `{c['p50_delta']:.3f}` / `{c['p95_delta']:.3f}`.",
            "",
            "## Decision",
            "",
            (
                "`PROMOTED_SEED_BOOTSTRAP_TRANSDUCER_PROGRAM`."
                if s["exact_promoted"]
                else "`seed_bootstrap_transducer_not_promoted`: the target-free policies do not generate enough of the seed stream to reduce the raw seed payload after corrections."
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
        "# Final Seed Bootstrap Transducer Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit converts the promoted seed copy-surface clue into a stricter "
        "target-free decoder test. The decoder receives seed book lengths, a "
        "literal tape extracted from the target-conditioned min_len=4 surface, "
        "and one deterministic context-copy policy. It does not inspect the "
        "target while choosing copy actions.",
        "",
        f"The surface literal tape has `{s['literal_tape_digits']}` digits. The "
        f"best target-free policy uses context `{s['best_context_size']}`, "
        f"copy_len `{s['best_copy_len']}`, source `{s['best_source_policy']}`. "
        f"It matches only the first `{s['best_exact_prefix_len']}` seed digits "
        f"before correction and `0`-indexed exact-book scoring gives "
        f"`{s['best_exact_books_without_correction']}/10` exact seed books. "
        f"After raw suffix correction it costs `{s['best_corrected_bits']:.3f}` "
        f"bits, delta `{s['best_delta_corrected_vs_raw_seed']:.3f}` versus raw seed payload.",
        "",
        f"Shuffled literal-tape controls have p05/p50/p95 exact-prefix lengths "
        f"`{c['p05_exact_prefix_len']}` / `{c['p50_exact_prefix_len']}` / "
        f"`{c['p95_exact_prefix_len']}`.",
        "",
        "## Decision",
        "",
        (
            "`PROMOTED_SEED_BOOTSTRAP_TRANSDUCER_PROGRAM`."
            if s["exact_promoted"]
            else "`seed_bootstrap_transducer_not_promoted`."
        ),
        "",
        "The seed stream has a real previous-copy surface, but these tested "
        "target-free context-copy policies do not convert that surface into a "
        "smaller executable seed generator. The next blocker is the policy that "
        "decides copy starts and source/length choices, not the existence of "
        "repeated seed content.",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_seed_bootstrap_transducer_program_gate.py](../scripts/01_seed_bootstrap_transducer_program_gate.py)",
        "- [01_seed_bootstrap_transducer_program_gate.json](test_results/01_seed_bootstrap_transducer_program_gate.json)",
        "- [01_seed_bootstrap_transducer_program_gate.md](test_results/01_seed_bootstrap_transducer_program_gate.md)",
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
