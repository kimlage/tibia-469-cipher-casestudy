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
SEED_SUBCODEC_GATE = TEST_RESULTS / "05_seed_derived_tape_subcodec_gate.json"

OUT_STEM = "06_seed_walk_source_model_gate"
SEED_BOOKS = list(range(10))
MIN_LENGTHS = [3, 4, 5]
RICE_KS = [2, 4, 6, 8]
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


def greedy_segments(text: str, source: str, min_len: int) -> list[dict[str, Any]]:
    index = build_index(source, min_len)
    pos = 0
    segments = []
    while pos < len(text):
        match = best_match(text, pos, source, index, min_len)
        if match is None:
            segments.append({"type": "literal", "target_pos": pos, "length": 1})
            pos += 1
            continue
        source_pos, length = match
        segments.append(
            {
                "type": "copy",
                "target_pos": pos,
                "source_pos": source_pos,
                "length": length,
            }
        )
        pos += length
    return segments


def signed_to_unsigned(delta: int) -> int:
    if delta >= 0:
        return delta * 2
    return -delta * 2 - 1


def rice_bits(value: int, k: int) -> int:
    q = value >> k
    return q + 1 + k


def segment_costs(segments: list[dict[str, Any]], source_len: int, tape_len: int) -> dict[str, Any]:
    copy_segments = [segment for segment in segments if segment["type"] == "copy"]
    literal_digits = sum(segment["length"] for segment in segments if segment["type"] == "literal")
    literal_bits = literal_digits * DIGIT_BITS
    length_bits = sum(
        math.log2(max(1, tape_len - segment["target_pos"]))
        for segment in copy_segments
    )
    mode_bits = len(segments)
    absolute_source_bits = len(copy_segments) * math.log2(source_len)
    absolute_total_bits = absolute_source_bits + length_bits + literal_bits + mode_bits
    best_walk = None
    for k in RICE_KS:
        if not copy_segments:
            source_bits = 0.0
            negative_deltas = 0
            abs_delta_sum = 0
        else:
            source_bits = math.log2(source_len)
            prev = copy_segments[0]["source_pos"]
            negative_deltas = 0
            abs_delta_sum = 0
            for segment in copy_segments[1:]:
                delta = segment["source_pos"] - prev
                negative_deltas += int(delta < 0)
                abs_delta_sum += abs(delta)
                source_bits += rice_bits(signed_to_unsigned(delta), k)
                prev = segment["source_pos"]
            source_bits += math.log2(len(RICE_KS))
        total = source_bits + length_bits + literal_bits + mode_bits
        row = {
            "rice_k": k,
            "walk_source_bits": source_bits,
            "walk_total_bits": total,
            "walk_saving_vs_absolute_bits": absolute_total_bits - total,
            "negative_deltas": negative_deltas,
            "abs_delta_sum": abs_delta_sum,
        }
        if best_walk is None or row["walk_total_bits"] < best_walk["walk_total_bits"]:
            best_walk = row
    raw_bits = tape_len * DIGIT_BITS
    copy_digits = sum(segment["length"] for segment in copy_segments)
    return {
        "copy_items": len(copy_segments),
        "copy_digits": copy_digits,
        "literal_digits": literal_digits,
        "length_bits": length_bits,
        "literal_bits": literal_bits,
        "mode_bits": mode_bits,
        "absolute_source_bits": absolute_source_bits,
        "absolute_total_bits": absolute_total_bits,
        "absolute_saving_vs_raw_bits": raw_bits - absolute_total_bits,
        "raw_bits": raw_bits,
        **(best_walk or {}),
        "walk_saving_vs_raw_bits": raw_bits - (best_walk or {"walk_total_bits": 0})["walk_total_bits"],
    }


def evaluate(text: str, source: str, min_len: int) -> dict[str, Any]:
    segments = greedy_segments(text, source, min_len)
    return {
        "min_len": min_len,
        **segment_costs(segments, len(source), len(text)),
    }


def shuffled_controls(text: str, source: str, min_len: int) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + min_len)
    chars = list(text)
    walk_savings = []
    walk_vs_absolute = []
    copy_digits = []
    for _ in range(RANDOM_TRIALS):
        rng.shuffle(chars)
        row = evaluate("".join(chars), source, min_len)
        walk_savings.append(row["walk_saving_vs_raw_bits"])
        walk_vs_absolute.append(row["walk_saving_vs_absolute_bits"])
        copy_digits.append(row["copy_digits"])
    walk_savings.sort()
    walk_vs_absolute.sort()
    copy_digits.sort()
    return {
        "trials": RANDOM_TRIALS,
        "walk_saving_vs_raw_mean": mean(walk_savings),
        "walk_saving_vs_raw_p95": percentile(walk_savings, 0.95),
        "walk_saving_vs_raw_max": walk_savings[-1],
        "walk_saving_vs_absolute_mean": mean(walk_vs_absolute),
        "walk_saving_vs_absolute_p95": percentile(walk_vs_absolute, 0.95),
        "copy_digits_mean": mean(copy_digits),
        "copy_digits_p95": percentile(copy_digits, 0.95),
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
    seed_subcodec = load_json(SEED_SUBCODEC_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("seed_derived_tape_subcodec_gate", seed_subcodec)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    tape = canonical_tape(ledger["canonical_ops_by_book"])
    seeds = seed_text(books)
    rows = []
    for min_len in MIN_LENGTHS:
        observed = evaluate(tape, seeds, min_len)
        control = shuffled_controls(tape, seeds, min_len)
        rows.append(
            {
                **observed,
                "control_walk_saving_vs_raw_p95": control["walk_saving_vs_raw_p95"],
                "control_walk_saving_vs_absolute_p95": control[
                    "walk_saving_vs_absolute_p95"
                ],
                "control_copy_digits_p95": control["copy_digits_p95"],
                "beats_walk_raw_p95": observed["walk_saving_vs_raw_bits"]
                > control["walk_saving_vs_raw_p95"],
                "beats_walk_absolute_p95": observed["walk_saving_vs_absolute_bits"]
                > control["walk_saving_vs_absolute_p95"],
            }
        )
    best = max(rows, key=lambda row: (row["walk_saving_vs_raw_bits"], row["copy_digits"]))
    promotes_walk = best["walk_saving_vs_raw_bits"] > 0 and best["beats_walk_raw_p95"]
    weak_walk = (
        best["walk_saving_vs_absolute_bits"] > 0
        and best["beats_walk_absolute_p95"]
    )
    summary = {
        "literal_tape_digits": len(tape),
        "seed_text_digits": len(seeds),
        "best_min_len": best["min_len"],
        "best_rice_k": best["rice_k"],
        "best_walk_total_bits": best["walk_total_bits"],
        "best_absolute_total_bits": best["absolute_total_bits"],
        "best_raw_bits": best["raw_bits"],
        "best_walk_saving_vs_raw_bits": best["walk_saving_vs_raw_bits"],
        "best_walk_saving_vs_absolute_bits": best["walk_saving_vs_absolute_bits"],
        "best_control_walk_saving_vs_raw_p95": best["control_walk_saving_vs_raw_p95"],
        "best_control_walk_saving_vs_absolute_p95": best[
            "control_walk_saving_vs_absolute_p95"
        ],
        "best_copy_digits": best["copy_digits"],
        "best_copy_items": best["copy_items"],
        "best_negative_deltas": best["negative_deltas"],
        "promotes_seed_walk_subcodec": promotes_walk,
        "weak_seed_walk_clue": weak_walk,
        "interpretation": (
            "This gate asks whether seed references in the innovation tape form "
            "a cheaper source-position walk than absolute source declarations, "
            "and whether that walk becomes a paid subcodec against raw tape and "
            "shuffled controls. Coverage can still beat controls while the walk "
            "itself is rejected if it costs more than absolute source positions."
        ),
    }
    return {
        "schema": "seed_walk_source_model_gate_v1",
        "scope": "analysis_only_seed_reference_source_walk_for_innovation_tape",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "seed_derived_tape_subcodec_gate": rel(SEED_SUBCODEC_GATE),
        },
        "rows": rows,
        "summary": summary,
        "classification": (
            "seed_walk_tape_subcodec_promoted"
            if promotes_walk
            else (
                "seed_walk_source_model_weak_clue"
                if weak_walk
                else "seed_walk_source_model_rejected"
            )
        ),
        "decision": {
            "promotes_seed_walk_subcodec": promotes_walk,
            "weak_seed_walk_clue": weak_walk,
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
        "# Seed Walk Source Model Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether seed-derived references in the innovation tape can use a",
        "source-position walk instead of paying absolute source addresses for every",
        "copy item.",
        "",
        "## Summary",
        "",
        f"- Literal tape digits: `{s['literal_tape_digits']}`.",
        f"- Seed text digits: `{s['seed_text_digits']}`.",
        f"- Best min length: `{s['best_min_len']}`.",
        f"- Best Rice k: `{s['best_rice_k']}`.",
        f"- Best walk total bits: `{s['best_walk_total_bits']:.3f}`.",
        f"- Best absolute total bits: `{s['best_absolute_total_bits']:.3f}`.",
        f"- Best raw bits: `{s['best_raw_bits']:.3f}`.",
        f"- Best walk saving vs raw: `{s['best_walk_saving_vs_raw_bits']:.3f}`.",
        f"- Best walk saving vs absolute: `{s['best_walk_saving_vs_absolute_bits']:.3f}`.",
        f"- Best control walk-vs-raw p95: `{s['best_control_walk_saving_vs_raw_p95']:.3f}`.",
        f"- Best control walk-vs-absolute p95: `{s['best_control_walk_saving_vs_absolute_p95']:.3f}`.",
        f"- Best copy digits: `{s['best_copy_digits']}`.",
        f"- Best copy items: `{s['best_copy_items']}`.",
        f"- Best negative deltas: `{s['best_negative_deltas']}`.",
        f"- Promotes seed-walk subcodec: `{s['promotes_seed_walk_subcodec']}`.",
        f"- Weak seed-walk clue: `{s['weak_seed_walk_clue']}`.",
        "",
        s["interpretation"],
        "",
        "## Rows",
        "",
        "| Min len | k | Walk bits | Absolute bits | Raw bits | Walk saving raw | Walk saving abs | Control raw p95 | Control abs p95 | Copy digits | Copy items |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['min_len']}` | `{row['rice_k']}` | "
            f"`{row['walk_total_bits']:.3f}` | `{row['absolute_total_bits']:.3f}` | "
            f"`{row['raw_bits']:.3f}` | `{row['walk_saving_vs_raw_bits']:.3f}` | "
            f"`{row['walk_saving_vs_absolute_bits']:.3f}` | "
            f"`{row['control_walk_saving_vs_raw_p95']:.3f}` | "
            f"`{row['control_walk_saving_vs_absolute_p95']:.3f}` | "
            f"`{row['copy_digits']}` | `{row['copy_items']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- A seed-walk subcodec is promoted only if it beats raw tape and shuffled controls.",
            "- A weak clue is retained only if the walk improves over absolute source positions and beats controls.",
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
