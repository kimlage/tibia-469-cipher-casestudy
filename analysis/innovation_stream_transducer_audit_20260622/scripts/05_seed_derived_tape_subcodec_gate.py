from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
STRUCTURE_GATE = TEST_RESULTS / "03_innovation_tape_structure_gate.json"
SYNC_GATE = TEST_RESULTS / "04_tape_synchronized_closed_loop_gate.json"

OUT_STEM = "05_seed_derived_tape_subcodec_gate"
SEED_BOOKS = list(range(10))
MIN_LENGTHS = [3, 4, 5]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 1000
DIGIT_BITS = math.log2(10)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def canonical_tape(ops_by_book: dict[str, list[dict[str, Any]]]) -> str:
    parts = []
    for book in range(10, 70):
        for op in ops_by_book[str(book)]:
            if op["type"] == "literal":
                parts.append(op.get("payload", ""))
    return "".join(parts)


def seed_text(books: dict[int, str]) -> str:
    return "".join(books[book] for book in SEED_BOOKS)


def build_index(source: str, min_len: int) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for pos in range(0, len(source) - min_len + 1):
        index.setdefault(source[pos : pos + min_len], []).append(pos)
    return index


def best_match(
    text: str,
    pos: int,
    source: str,
    index: dict[str, list[int]],
    min_len: int,
) -> tuple[int, int] | None:
    if pos + min_len > len(text):
        return None
    key = text[pos : pos + min_len]
    candidates = index.get(key, [])
    best: tuple[int, int] | None = None
    for source_pos in candidates:
        length = min_len
        cap = min(len(text) - pos, len(source) - source_pos)
        while length < cap and text[pos + length] == source[source_pos + length]:
            length += 1
        if best is None or (length, -source_pos) > (best[1], -best[0]):
            best = (source_pos, length)
    return best


def greedy_seed_subcodec(text: str, source: str, min_len: int) -> dict[str, Any]:
    index = build_index(source, min_len)
    pos = 0
    copy_items = 0
    copy_digits = 0
    literal_digits = 0
    source_bits = 0.0
    length_bits = 0.0
    while pos < len(text):
        match = best_match(text, pos, source, index, min_len)
        if match is None:
            literal_digits += 1
            pos += 1
            continue
        source_pos, length = match
        copy_items += 1
        copy_digits += length
        source_bits += math.log2(len(source))
        length_bits += math.log2(max(1, len(text) - pos))
        pos += length
    literal_bits = literal_digits * DIGIT_BITS
    mode_bits = (copy_items + literal_digits) * 1.0
    total_bits = source_bits + length_bits + literal_bits + mode_bits
    raw_bits = len(text) * DIGIT_BITS
    return {
        "min_len": min_len,
        "copy_items": copy_items,
        "copy_digits": copy_digits,
        "literal_digits": literal_digits,
        "source_bits": source_bits,
        "length_bits": length_bits,
        "literal_bits": literal_bits,
        "mode_bits": mode_bits,
        "total_bits": total_bits,
        "raw_bits": raw_bits,
        "saving_vs_raw_bits": raw_bits - total_bits,
        "coverage_fraction": copy_digits / len(text) if text else 0.0,
    }


def shuffled_controls(text: str, source: str, min_len: int) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + min_len)
    chars = list(text)
    savings = []
    coverages = []
    for _ in range(RANDOM_TRIALS):
        rng.shuffle(chars)
        row = greedy_seed_subcodec("".join(chars), source, min_len)
        savings.append(row["saving_vs_raw_bits"])
        coverages.append(row["copy_digits"])
    savings.sort()
    coverages.sort()
    return {
        "trials": RANDOM_TRIALS,
        "saving_mean": mean(savings),
        "saving_p95": percentile(savings, 0.95),
        "saving_max": savings[-1],
        "coverage_mean": mean(coverages),
        "coverage_p95": percentile(coverages, 0.95),
        "coverage_max": coverages[-1],
    }


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    frac = index - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    structure = load_json(STRUCTURE_GATE)
    sync = load_json(SYNC_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("innovation_tape_structure_gate", structure)
    assert_boundary("tape_synchronized_closed_loop_gate", sync)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    tape = canonical_tape(ledger["canonical_ops_by_book"])
    seeds = seed_text(books)
    rows = []
    for min_len in MIN_LENGTHS:
        observed = greedy_seed_subcodec(tape, seeds, min_len)
        control = shuffled_controls(tape, seeds, min_len)
        rows.append(
            {
                **observed,
                "control_saving_p95": control["saving_p95"],
                "control_saving_max": control["saving_max"],
                "control_coverage_p95": control["coverage_p95"],
                "beats_saving_p95": observed["saving_vs_raw_bits"] > control["saving_p95"],
                "beats_coverage_p95": observed["copy_digits"] > control["coverage_p95"],
            }
        )
    best = max(rows, key=lambda row: (row["saving_vs_raw_bits"], row["copy_digits"]))
    promotes_subcodec = best["saving_vs_raw_bits"] > 0 and best["beats_saving_p95"]
    weak_seed_subcodec = best["beats_coverage_p95"] and best["beats_saving_p95"]
    summary = {
        "literal_tape_digits": len(tape),
        "seed_text_digits": len(seeds),
        "best_min_len": best["min_len"],
        "best_total_bits": best["total_bits"],
        "best_raw_bits": best["raw_bits"],
        "best_saving_vs_raw_bits": best["saving_vs_raw_bits"],
        "best_control_saving_p95": best["control_saving_p95"],
        "best_copy_digits": best["copy_digits"],
        "best_literal_digits": best["literal_digits"],
        "best_copy_items": best["copy_items"],
        "best_control_coverage_p95": best["control_coverage_p95"],
        "promotes_seed_subcodec": promotes_subcodec,
        "weak_seed_subcodec_clue": weak_seed_subcodec,
        "interpretation": (
            "This gate prices the promoted seed-coverage structure as a concrete "
            "subcodec for the innovation tape: seed substring references plus "
            "literal residual digits, compared to raw tape bits and shuffled "
            "same-multiset controls."
        ),
    }
    return {
        "schema": "seed_derived_tape_subcodec_gate_v1",
        "scope": "analysis_only_paid_seed_subcodec_for_innovation_tape",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "innovation_tape_structure_gate": rel(STRUCTURE_GATE),
            "tape_synchronized_closed_loop_gate": rel(SYNC_GATE),
        },
        "rows": rows,
        "summary": summary,
        "classification": (
            "seed_derived_tape_subcodec_promoted"
            if promotes_subcodec
            else (
                "seed_derived_tape_subcodec_weak_clue"
                if weak_seed_subcodec
                else "seed_derived_tape_subcodec_rejected"
            )
        ),
        "decision": {
            "promotes_seed_subcodec": promotes_subcodec,
            "weak_seed_subcodec_clue": weak_seed_subcodec,
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Seed Derived Tape Subcodec Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Convert the seed-coverage clue for the innovation tape into a paid",
        "subcodec: references to substrings in seed books plus literal residual",
        "digits. Compare against raw tape bits and shuffled same-multiset controls.",
        "",
        "## Summary",
        "",
        f"- Literal tape digits: `{s['literal_tape_digits']}`.",
        f"- Seed text digits: `{s['seed_text_digits']}`.",
        f"- Best min length: `{s['best_min_len']}`.",
        f"- Best total bits: `{s['best_total_bits']:.3f}`.",
        f"- Best raw bits: `{s['best_raw_bits']:.3f}`.",
        f"- Best saving vs raw: `{s['best_saving_vs_raw_bits']:.3f}`.",
        f"- Best control saving p95: `{s['best_control_saving_p95']:.3f}`.",
        f"- Best copy digits: `{s['best_copy_digits']}`.",
        f"- Best literal digits: `{s['best_literal_digits']}`.",
        f"- Best copy items: `{s['best_copy_items']}`.",
        f"- Best control coverage p95: `{s['best_control_coverage_p95']:.3f}`.",
        f"- Promotes seed subcodec: `{s['promotes_seed_subcodec']}`.",
        f"- Weak seed subcodec clue: `{s['weak_seed_subcodec_clue']}`.",
        "",
        s["interpretation"],
        "",
        "## Rows",
        "",
        "| Min len | Total bits | Raw bits | Saving | Control saving p95 | Copy digits | Literal digits | Copy items | Coverage p95 |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['min_len']}` | `{row['total_bits']:.3f}` | "
            f"`{row['raw_bits']:.3f}` | `{row['saving_vs_raw_bits']:.3f}` | "
            f"`{row['control_saving_p95']:.3f}` | `{row['copy_digits']}` | "
            f"`{row['literal_digits']}` | `{row['copy_items']}` | "
            f"`{row['control_coverage_p95']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- A seed-derived subcodec is promoted only if paid bits beat raw tape and shuffled controls.",
            "- A weak clue may be retained when coverage beats controls but paid bits do not.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
