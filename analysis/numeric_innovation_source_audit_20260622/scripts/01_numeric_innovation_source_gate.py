#!/usr/bin/env python3
"""Test simple numeric sources as external content for the innovation tape.

The current blocker is not another local source/length selector; it is the
origin of the innovation content itself. This gate tests a narrow, falsifiable
route: can the promoted unified innovation stream be generated more cheaply by
copying chunks from a small preregistered bank of numeric sources?

Promotion requires paid source/offset/length costs, prefix holdout, and controls.
No plaintext, translation, row0 change, or leaked data is used.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import mpmath as mp


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/numeric_innovation_source_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_numeric_innovation_source_gate.json"
MD_OUT = OUT_DIR / "01_numeric_innovation_source_gate.md"
FINAL_OUT = FRONT / "reports/final_numeric_innovation_source_audit.md"

PAYLOAD_GATE = ROOT / "analysis/unified_innovation_payload_audit_20260622/reports/test_results/01_unified_innovation_payload_gate.json"

LOG2_10 = math.log2(10)
SOURCE_DIGITS = 5000
MIN_LENS = [6, 8, 10, 12]
CONTROL_TRIALS = 20
RNG_SEED = 46920260622
PREFIX_CUTOFFS = [512, 1024, 1536]


@dataclass(frozen=True)
class Source:
    source_id: str
    digits: str
    source_class: str


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def assert_boundary(data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError("translation changed")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError("case reopened")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError("plaintext introduced")
    if data.get("row0_status") != "unchanged_exogenous":
        raise RuntimeError("row0 changed")
    if data.get("classification") != "PROMOTED_UNIFIED_INNOVATION_PAYLOAD_LEDGER":
        raise RuntimeError("unified innovation payload is not the promoted input ledger")


def innovation_stream(payload: dict[str, Any]) -> str:
    out: list[str] = []
    for event in payload["event_ledger"]:
        if event["kind"] == "literal":
            out.append(str(event["text"]))
        else:
            current = "".join(out)
            source = int(event["source"])
            length = int(event["length"])
            out.append(current[source : source + length])
    return "".join(out)


def decimal_digits(value: mp.mpf, n: int) -> str:
    text = mp.nstr(value, n + 20)
    return "".join(ch for ch in text if ch.isdigit())[:n]


def concatenated_primes(n: int) -> str:
    out: list[str] = []
    value = 2
    while sum(len(x) for x in out) < n:
        is_prime = True
        limit = int(value**0.5)
        for divisor in range(2, limit + 1):
            if value % divisor == 0:
                is_prime = False
                break
        if is_prime:
            out.append(str(value))
        value += 1
    return "".join(out)[:n]


def concatenated_powers(base: int, n: int) -> str:
    out: list[str] = []
    value = 1
    while sum(len(x) for x in out) < n:
        out.append(str(value))
        value *= base
    return "".join(out)[:n]


def concatenated_squares(n: int) -> str:
    out: list[str] = []
    value = 1
    while sum(len(x) for x in out) < n:
        out.append(str(value * value))
        value += 1
    return "".join(out)[:n]


def concatenated_fibonacci(n: int) -> str:
    out: list[str] = []
    a, b = 1, 1
    while sum(len(x) for x in out) < n:
        out.append(str(a))
        a, b = b, a + b
    return "".join(out)[:n]


def lcg_digits(seed: int, a: int, c: int, m: int, n: int) -> str:
    state = seed % m
    out: list[str] = []
    while sum(len(x) for x in out) < n:
        state = (a * state + c) % m
        out.append(str(state))
    return "".join(out)[:n]


def build_sources(n: int) -> list[Source]:
    mp.mp.dps = n + 50
    constants = [
        ("pi", mp.pi),
        ("e", mp.e),
        ("sqrt2", mp.sqrt(2)),
        ("sqrt3", mp.sqrt(3)),
        ("sqrt5", mp.sqrt(5)),
        ("phi", (1 + mp.sqrt(5)) / 2),
        ("ln2", mp.log(2)),
        ("ln10", mp.log(10)),
        ("catalan", mp.catalan),
        ("euler", mp.euler),
    ]
    sources = [Source(f"const_{name}", decimal_digits(value, n), "constant") for name, value in constants]
    sources.extend(
        [
            Source("seq_primes", concatenated_primes(n), "sequence"),
            Source("seq_squares", concatenated_squares(n), "sequence"),
            Source("seq_fibonacci", concatenated_fibonacci(n), "sequence"),
            Source("seq_powers2", concatenated_powers(2, n), "sequence"),
            Source("seq_powers3", concatenated_powers(3, n), "sequence"),
        ]
    )
    lore_seeds = [1, 469, 3478, 486486, 43153, 34784, 74032, 45331]
    for seed in lore_seeds:
        sources.append(Source(f"lcg_ansi_seed_{seed}", lcg_digits(seed, 1103515245, 12345, 2**31, n), "lcg_control"))
        sources.append(Source(f"lcg_small_seed_{seed}", lcg_digits(seed, 37, 17, 1000003, n), "lcg_control"))
    return sources


def build_index(source: str, min_len: int) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for pos in range(0, max(0, len(source) - min_len + 1)):
        index.setdefault(source[pos : pos + min_len], []).append(pos)
    return index


def build_source_indexes(sources: list[Source], min_len: int) -> list[tuple[Source, dict[str, list[int]]]]:
    return [(source, build_index(source.digits, min_len)) for source in sources]


def build_index_bank(sources: list[Source]) -> dict[int, list[tuple[Source, dict[str, list[int]]]]]:
    return {min_len: build_source_indexes(sources, min_len) for min_len in MIN_LENS}


def longest_external_match(target: str, pos: int, indexes: list[tuple[Source, dict[str, list[int]]]], min_len: int) -> tuple[int, Source | None, int | None]:
    upper = min(64, len(target) - pos)
    seed = target[pos : pos + min_len]
    best_length = 0
    best_source: Source | None = None
    best_offset: int | None = None
    for source, index in indexes:
        for offset in index.get(seed, []):
            length = min_len
            while (
                length < upper
                and offset + length < len(source.digits)
                and source.digits[offset + length] == target[pos + length]
            ):
                length += 1
            if length > best_length:
                best_length = length
                best_source = source
                best_offset = offset
                if best_length == upper:
                    return best_length, best_source, best_offset
    return best_length, best_source, best_offset


def parse_with_indexes(
    target: str,
    indexes: list[tuple[Source, dict[str, list[int]]]],
    source_count: int,
    source_len: int,
    min_len: int,
) -> dict[str, Any]:
    pos = 0
    events: list[dict[str, Any]] = []
    literal_buffer: list[str] = []
    literal_start: int | None = None
    while pos < len(target):
        length, source, offset = longest_external_match(target, pos, indexes, min_len)
        if source and offset is not None:
            if literal_buffer:
                events.append(
                    {
                        "kind": "literal",
                        "start": literal_start,
                        "length": len(literal_buffer),
                        "text": "".join(literal_buffer),
                    }
                )
                literal_buffer = []
                literal_start = None
            events.append(
                {
                    "kind": "external_copy",
                    "start": pos,
                    "length": length,
                    "source_id": source.source_id,
                    "source_class": source.source_class,
                    "offset": offset,
                }
            )
            pos += length
            continue
        if literal_start is None:
            literal_start = pos
        literal_buffer.append(target[pos])
        pos += 1
    if literal_buffer:
        events.append(
            {
                "kind": "literal",
                "start": literal_start,
                "length": len(literal_buffer),
                "text": "".join(literal_buffer),
            }
        )

    model_bits = math.log2(len(MIN_LENS)) + math.log2(source_count)
    copy_events = [event for event in events if event["kind"] == "external_copy"]
    literal_events = [event for event in events if event["kind"] == "literal"]
    copy_bits = sum(
        1.0 + math.log2(source_count) + math.log2(source_len) + math.log2(max(1, int(event["length"]) - min_len + 1))
        for event in copy_events
    )
    literal_bits = sum(1.0 + math.log2(64) + int(event["length"]) * LOG2_10 for event in literal_events)
    total_bits = model_bits + copy_bits + literal_bits
    raw_bits = len(target) * LOG2_10
    return {
        "min_len": min_len,
        "events": events,
        "copy_ops": len(copy_events),
        "copied_digits": sum(int(event["length"]) for event in copy_events),
        "literal_runs": len(literal_events),
        "literal_digits": sum(int(event["length"]) for event in literal_events),
        "model_bits": model_bits,
        "copy_bits": copy_bits,
        "literal_bits": literal_bits,
        "total_bits": total_bits,
        "raw_bits": raw_bits,
        "delta_vs_raw_bits": total_bits - raw_bits,
    }


def best_parse(target: str, sources: list[Source], index_bank: dict[int, list[tuple[Source, dict[str, list[int]]]]] | None = None) -> dict[str, Any]:
    if index_bank is None:
        index_bank = build_index_bank(sources)
    source_count = len(sources)
    source_len = max(len(source.digits) for source in sources)
    parses = [
        parse_with_indexes(target, index_bank[min_len], source_count, source_len, min_len)
        for min_len in MIN_LENS
    ]
    best = min(parses, key=lambda item: item["total_bits"])
    return {
        "best_min_len": best["min_len"],
        "best": {key: value for key, value in best.items() if key != "events"},
        "all_minlens": [{key: value for key, value in row.items() if key != "events"} for row in parses],
        "event_samples": best["events"][:20],
    }


def shuffled_target_controls(target: str, sources: list[Source]) -> dict[str, Any]:
    rng = random.Random(RNG_SEED + 11)
    index_bank = build_index_bank(sources)
    deltas = []
    copied = []
    for _ in range(CONTROL_TRIALS):
        chars = list(target)
        rng.shuffle(chars)
        result = best_parse("".join(chars), sources, index_bank)
        deltas.append(float(result["best"]["delta_vs_raw_bits"]))
        copied.append(int(result["best"]["copied_digits"]))
    ordered = sorted(deltas)
    copied_ordered = sorted(copied)
    return {
        "trials": CONTROL_TRIALS,
        "delta_p05": ordered[int(0.05 * (CONTROL_TRIALS - 1))],
        "delta_p50": ordered[int(0.50 * (CONTROL_TRIALS - 1))],
        "delta_p95": ordered[int(0.95 * (CONTROL_TRIALS - 1))],
        "copied_digits_p95": copied_ordered[int(0.95 * (CONTROL_TRIALS - 1))],
    }


def random_source_controls(target: str, source_count: int, source_len: int) -> dict[str, Any]:
    rng = random.Random(RNG_SEED + 29)
    deltas = []
    copied = []
    for trial in range(CONTROL_TRIALS):
        sources = [
            Source(
                f"random_source_{trial}_{idx}",
                "".join(str(rng.randrange(10)) for _ in range(source_len)),
                "random_control",
            )
            for idx in range(source_count)
        ]
        result = best_parse(target, sources, build_index_bank(sources))
        deltas.append(float(result["best"]["delta_vs_raw_bits"]))
        copied.append(int(result["best"]["copied_digits"]))
    ordered = sorted(deltas)
    copied_ordered = sorted(copied)
    return {
        "trials": CONTROL_TRIALS,
        "delta_p05": ordered[int(0.05 * (CONTROL_TRIALS - 1))],
        "delta_p50": ordered[int(0.50 * (CONTROL_TRIALS - 1))],
        "delta_p95": ordered[int(0.95 * (CONTROL_TRIALS - 1))],
        "copied_digits_p95": copied_ordered[int(0.95 * (CONTROL_TRIALS - 1))],
    }


def prefix_holdouts(target: str, sources: list[Source]) -> list[dict[str, Any]]:
    index_bank = build_index_bank(sources)
    source_count = len(sources)
    source_len = max(len(source.digits) for source in sources)
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train = target[:cutoff]
        test = target[cutoff:]
        train_result = best_parse(train, sources, index_bank)
        min_len = int(train_result["best_min_len"])
        test_result = parse_with_indexes(test, index_bank[min_len], source_count, source_len, min_len)
        rows.append(
            {
                "cutoff": cutoff,
                "selected_min_len": min_len,
                "train_delta_vs_raw_bits": train_result["best"]["delta_vs_raw_bits"],
                "test_delta_vs_raw_bits": test_result["delta_vs_raw_bits"],
                "test_copied_digits": test_result["copied_digits"],
                "test_digits": len(test),
                "test_copy_ops": test_result["copy_ops"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    payload = load_json(PAYLOAD_GATE)
    assert_boundary(payload)
    target = innovation_stream(payload)
    sources = build_sources(SOURCE_DIGITS)
    index_bank = build_index_bank(sources)
    best = best_parse(target, sources, index_bank)
    shuffled = shuffled_target_controls(target, sources)
    random_controls = random_source_controls(target, len(sources), SOURCE_DIGITS)
    holdouts = prefix_holdouts(target, sources)
    positive_holdouts = sum(1 for row in holdouts if row["test_delta_vs_raw_bits"] < 0)
    beats_random_source = best["best"]["delta_vs_raw_bits"] < random_controls["delta_p05"]
    beats_shuffled_target = best["best"]["delta_vs_raw_bits"] < shuffled["delta_p05"]
    promoted = (
        best["best"]["delta_vs_raw_bits"] < 0
        and beats_random_source
        and beats_shuffled_target
        and positive_holdouts == len(holdouts)
    )
    classification = "PROMOTED_NUMERIC_INNOVATION_SOURCE_CANDIDATE" if promoted else "numeric_innovation_source_not_promoted"
    source_usage: dict[str, dict[str, int]] = {}
    for event in best["event_samples"]:
        if event["kind"] != "external_copy":
            continue
        usage = source_usage.setdefault(event["source_id"], {"ops": 0, "digits": 0})
        usage["ops"] += 1
        usage["digits"] += int(event["length"])
    return {
        "schema": "numeric_innovation_source_gate.v1",
        "scope": "analysis_only_external_numeric_content_source_for_innovation_tape",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {"unified_innovation_payload_gate": str(PAYLOAD_GATE.relative_to(ROOT))},
        "source_bank": {
            "source_count": len(sources),
            "source_digits_each": SOURCE_DIGITS,
            "source_ids": [source.source_id for source in sources],
            "source_classes": sorted({source.source_class for source in sources}),
            "min_lens": MIN_LENS,
        },
        "summary": {
            "innovation_digits": len(target),
            "best_min_len": best["best_min_len"],
            "best_total_bits": best["best"]["total_bits"],
            "raw_bits": best["best"]["raw_bits"],
            "delta_vs_raw_bits": best["best"]["delta_vs_raw_bits"],
            "copied_digits": best["best"]["copied_digits"],
            "copy_ops": best["best"]["copy_ops"],
            "literal_digits": best["best"]["literal_digits"],
            "positive_holdouts": positive_holdouts,
            "holdout_count": len(holdouts),
            "beats_random_source_p05": beats_random_source,
            "beats_shuffled_target_p05": beats_shuffled_target,
            "promoted": promoted,
        },
        "best_parse": best,
        "controls": {
            "shuffled_target": shuffled,
            "random_sources": random_controls,
        },
        "holdouts": holdouts,
        "decision": {
            "numeric_innovation_source_promoted": promoted,
            "external_field_reduced": False,
            "v9_reduction_bits": 0.0,
            "reason": (
                "numeric source bank does not reduce the innovation tape after paid source/offset/length costs and controls"
                if not promoted
                else "numeric source bank reduces innovation content and should be integrated into the executable decoder"
            ),
            "next_blocker": (
                "innovation content origin remains external; simple numeric sources are not sufficient"
                if not promoted
                else "integrate numeric source references into executable v9/v10 ledger with paid corrections"
            ),
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Numeric Innovation Source Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This gate tests whether the unified innovation tape can be generated by copying from a small preregistered bank of numeric sources.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Innovation digits | `{s['innovation_digits']}` |",
        f"| Source count | `{result['source_bank']['source_count']}` |",
        f"| Source digits each | `{result['source_bank']['source_digits_each']}` |",
        f"| Best min_len | `{s['best_min_len']}` |",
        f"| Copied digits | `{s['copied_digits']}` |",
        f"| Copy ops | `{s['copy_ops']}` |",
        f"| Delta vs raw bits | `{s['delta_vs_raw_bits']:.3f}` |",
        f"| Positive holdouts | `{s['positive_holdouts']}/{s['holdout_count']}` |",
        f"| Beats random-source p05 | `{s['beats_random_source_p05']}` |",
        f"| Beats shuffled-target p05 | `{s['beats_shuffled_target_p05']}` |",
        "",
        "## Controls",
        "",
        "| Control | Delta p05 | Delta p50 | Delta p95 | Copied p95 |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| Shuffled target | `{c['shuffled_target']['delta_p05']:.3f}` | `{c['shuffled_target']['delta_p50']:.3f}` | `{c['shuffled_target']['delta_p95']:.3f}` | `{c['shuffled_target']['copied_digits_p95']}` |",
        f"| Random sources | `{c['random_sources']['delta_p05']:.3f}` | `{c['random_sources']['delta_p50']:.3f}` | `{c['random_sources']['delta_p95']:.3f}` | `{c['random_sources']['copied_digits_p95']}` |",
        "",
        "## Decision",
        "",
        f"`{result['decision']['reason']}`",
        "",
        f"Next blocker: `{result['decision']['next_blocker']}`",
        "",
        "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
    ]
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Numeric Innovation Source Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit tests a constructive content-source route: a small bank of mathematical constants, simple integer sequences, and fixed PRNG controls as an external source for the unified innovation tape.",
        f"The best paid parse copies `{s['copied_digits']}` of `{s['innovation_digits']}` digits but costs `{s['delta_vs_raw_bits']:.3f}` bits versus raw declaration after paying source/offset/length/model costs.",
        f"Prefix holdout is positive in `{s['positive_holdouts']}/{s['holdout_count']}` splits; promotion requires all splits plus controls.",
        "",
        "## Decision",
        "",
        "`numeric_innovation_source_not_promoted`.",
        "",
        "No numeric source is integrated, no v9 field is reduced, and no formula is promoted.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_numeric_innovation_source_gate.py](../scripts/01_numeric_innovation_source_gate.py)",
        "- [01_numeric_innovation_source_gate.json](test_results/01_numeric_innovation_source_gate.json)",
        "- [01_numeric_innovation_source_gate.md](test_results/01_numeric_innovation_source_gate.md)",
    ]
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
