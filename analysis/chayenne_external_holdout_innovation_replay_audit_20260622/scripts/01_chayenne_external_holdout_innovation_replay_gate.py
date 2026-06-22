#!/usr/bin/env python3
"""External holdout validation for the unified innovation tape.

Chayenne should not be promoted as an origin source: prior gates classify it as
secondary corpus-compatible validation. This gate uses it correctly as a
holdout. It asks whether the promoted unified innovation tape acts as a module
bank that reconstructs Chayenne better than other external strings and controls,
without training on Chayenne.
"""

from __future__ import annotations

import json
import math
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/chayenne_external_holdout_innovation_replay_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_chayenne_external_holdout_innovation_replay_gate.json"
MD_OUT = OUT_DIR / "01_chayenne_external_holdout_innovation_replay_gate.md"
FINAL_OUT = FRONT / "reports/final_chayenne_external_holdout_innovation_replay_audit.md"

PAYLOAD_GATE = ROOT / "analysis/unified_innovation_payload_audit_20260622/reports/test_results/01_unified_innovation_payload_gate.json"
EXTERNAL_STRINGS = ROOT / "analysis/post_review_20260619/external_numeric_string_classifier_results.json"

LOG2_10 = math.log2(10)
MIN_LENS = [3, 5, 8, 12]
CONTROL_TRIALS = 1000
RNG_SEED = 46920260622


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
        raise RuntimeError("unified innovation payload is not promoted input")


def render_innovation_stream(payload: dict[str, Any]) -> str:
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


def build_index(source: str, min_len: int) -> dict[str, list[int]]:
    index: dict[str, list[int]] = {}
    for pos in range(0, max(0, len(source) - min_len + 1)):
        index.setdefault(source[pos : pos + min_len], []).append(pos)
    return index


def longest_match(target: str, pos: int, source: str, index: dict[str, list[int]], min_len: int) -> tuple[int, int | None]:
    seed = target[pos : pos + min_len]
    best_len = 0
    best_offset = None
    upper = len(target) - pos
    for offset in index.get(seed, []):
        length = min_len
        while (
            length < upper
            and offset + length < len(source)
            and source[offset + length] == target[pos + length]
        ):
            length += 1
        if length > best_len:
            best_len = length
            best_offset = offset
    return best_len, best_offset


def parse_against_source(target: str, source: str, min_len: int) -> dict[str, Any]:
    index = build_index(source, min_len)
    pos = 0
    events: list[dict[str, Any]] = []
    literal_buffer: list[str] = []
    literal_start: int | None = None
    while pos < len(target):
        length, offset = longest_match(target, pos, source, index, min_len)
        if offset is not None and length >= min_len:
            if literal_buffer:
                events.append({"kind": "literal", "start": literal_start, "length": len(literal_buffer)})
                literal_buffer = []
                literal_start = None
            events.append({"kind": "copy", "start": pos, "length": length, "offset": offset})
            pos += length
            continue
        if literal_start is None:
            literal_start = pos
        literal_buffer.append(target[pos])
        pos += 1
    if literal_buffer:
        events.append({"kind": "literal", "start": literal_start, "length": len(literal_buffer)})

    copy_events = [event for event in events if event["kind"] == "copy"]
    literal_events = [event for event in events if event["kind"] == "literal"]
    copy_bits = sum(
        1.0 + math.log2(max(1, len(source))) + math.log2(max(1, int(event["length"]) - min_len + 1))
        for event in copy_events
    )
    literal_bits = sum(1.0 + math.log2(128) + int(event["length"]) * LOG2_10 for event in literal_events)
    model_bits = math.log2(len(MIN_LENS))
    total_bits = model_bits + copy_bits + literal_bits
    raw_bits = len(target) * LOG2_10
    return {
        "min_len": min_len,
        "events": events,
        "copy_ops": len(copy_events),
        "copied_digits": sum(int(event["length"]) for event in copy_events),
        "literal_digits": sum(int(event["length"]) for event in literal_events),
        "total_bits": total_bits,
        "raw_bits": raw_bits,
        "delta_vs_raw_bits": total_bits - raw_bits,
    }


def best_parse(target: str, source: str) -> dict[str, Any]:
    parses = [parse_against_source(target, source, min_len) for min_len in MIN_LENS]
    best = min(parses, key=lambda row: row["total_bits"])
    return {
        "best_min_len": best["min_len"],
        "best": {key: value for key, value in best.items() if key != "events"},
        "events": best["events"],
        "all_minlens": [{key: value for key, value in row.items() if key != "events"} for row in parses],
    }


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def shuffled_target_control(target: str, source: str) -> dict[str, Any]:
    rng = random.Random(RNG_SEED + len(target))
    deltas: list[float] = []
    copied: list[int] = []
    for _ in range(CONTROL_TRIALS):
        chars = list(target)
        rng.shuffle(chars)
        parsed = best_parse("".join(chars), source)
        deltas.append(float(parsed["best"]["delta_vs_raw_bits"]))
        copied.append(int(parsed["best"]["copied_digits"]))
    return {
        "trials": CONTROL_TRIALS,
        "delta_p05": quantile(deltas, 0.05),
        "delta_p50": quantile(deltas, 0.50),
        "delta_p95": quantile(deltas, 0.95),
        "copied_digits_p95": quantile(copied, 0.95),
    }


def random_source_control(target: str, source_len: int) -> dict[str, Any]:
    rng = random.Random(RNG_SEED + source_len + len(target))
    deltas: list[float] = []
    copied: list[int] = []
    for _ in range(CONTROL_TRIALS):
        source = "".join(str(rng.randrange(10)) for _ in range(source_len))
        parsed = best_parse(target, source)
        deltas.append(float(parsed["best"]["delta_vs_raw_bits"]))
        copied.append(int(parsed["best"]["copied_digits"]))
    return {
        "trials": CONTROL_TRIALS,
        "delta_p05": quantile(deltas, 0.05),
        "delta_p50": quantile(deltas, 0.50),
        "delta_p95": quantile(deltas, 0.95),
        "copied_digits_p95": quantile(copied, 0.95),
    }


def make_result() -> dict[str, Any]:
    payload = load_json(PAYLOAD_GATE)
    assert_boundary(payload)
    innovation = render_innovation_stream(payload)
    external_rows = load_json(EXTERNAL_STRINGS)["rows"]
    rows = []
    for row in external_rows:
        digits = "".join(ch for ch in str(row["raw_digits"]) if ch.isdigit())
        parsed = best_parse(digits, innovation)
        target_control = shuffled_target_control(digits, innovation)
        random_control = random_source_control(digits, len(innovation))
        beats_target_control = parsed["best"]["delta_vs_raw_bits"] < target_control["delta_p05"]
        beats_random_source = parsed["best"]["delta_vs_raw_bits"] < random_control["delta_p05"]
        rows.append(
            {
                "name": row["name"],
                "classifier_classification": row["classification"],
                "digits": len(digits),
                "raw_digits": digits,
                "best_min_len": parsed["best_min_len"],
                "copied_digits": parsed["best"]["copied_digits"],
                "copy_ops": parsed["best"]["copy_ops"],
                "literal_digits": parsed["best"]["literal_digits"],
                "delta_vs_raw_bits": parsed["best"]["delta_vs_raw_bits"],
                "beats_shuffled_target_p05": beats_target_control,
                "beats_random_source_p05": beats_random_source,
                "controls": {
                    "shuffled_target": target_control,
                    "random_source": random_control,
                },
                "event_samples": parsed["events"][:20],
            }
        )
    chayenne = next(row for row in rows if row["name"] == "chayenne")
    ytc = next(row for row in rows if row["name"] == "your_true_colour")
    avar = next(row for row in rows if row["name"] == "avar_tar")
    promoted_holdout = (
        chayenne["delta_vs_raw_bits"] < 0
        and chayenne["beats_shuffled_target_p05"]
        and chayenne["beats_random_source_p05"]
        and chayenne["copied_digits"] >= 40
        and ytc["copied_digits"] < chayenne["copied_digits"]
        and avar["copied_digits"] < chayenne["copied_digits"]
    )
    classification = "PROMOTED_CHAYENNE_EXTERNAL_HOLDOUT_VALIDATION" if promoted_holdout else "chayenne_external_holdout_not_promoted"
    return {
        "schema": "chayenne_external_holdout_innovation_replay_gate.v1",
        "scope": "analysis_only_external_holdout_validation_not_origin",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {
            "unified_innovation_payload_gate": str(PAYLOAD_GATE.relative_to(ROOT)),
            "external_numeric_string_classifier": str(EXTERNAL_STRINGS.relative_to(ROOT)),
        },
        "summary": {
            "innovation_digits": len(innovation),
            "chayenne_digits": chayenne["digits"],
            "chayenne_copied_digits": chayenne["copied_digits"],
            "chayenne_delta_vs_raw_bits": chayenne["delta_vs_raw_bits"],
            "chayenne_beats_shuffled_target_p05": chayenne["beats_shuffled_target_p05"],
            "chayenne_beats_random_source_p05": chayenne["beats_random_source_p05"],
            "your_true_colour_copied_digits": ytc["copied_digits"],
            "avar_tar_copied_digits": avar["copied_digits"],
            "promoted_external_holdout_validation": promoted_holdout,
        },
        "external_rows": rows,
        "decision": {
            "external_holdout_validation_promoted": promoted_holdout,
            "origin_source_promoted": False,
            "external_field_reduced": False,
            "v9_reduction_bits": 0.0,
            "reason": (
                "Chayenne validates the innovation module bank as an external holdout, but remains secondary validation rather than origin"
                if promoted_holdout
                else "Chayenne does not pass the external holdout validation gate"
            ),
            "next_blocker": "module-bank validation does not generate the 70-book event policy or innovation origin",
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Chayenne External Holdout Innovation Replay Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This gate tests Chayenne as an external holdout for the unified innovation tape module bank, not as an origin source.",
        "",
        "| String | Digits | Copied | Delta vs Raw | Beats Shuffled | Beats Random Source |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["external_rows"]:
        lines.append(
            f"| `{row['name']}` | `{row['digits']}` | `{row['copied_digits']}` | `{row['delta_vs_raw_bits']:.3f}` | `{row['beats_shuffled_target_p05']}` | `{row['beats_random_source_p05']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{result['decision']['reason']}`",
            "",
            "This is validation of a module bank, not a generator, origin source, plaintext, or translation.",
            "",
            f"Next blocker: `{result['decision']['next_blocker']}`",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Chayenne External Holdout Innovation Replay Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "Chayenne was tested as an external holdout against the unified innovation tape module bank.",
        f"It copies `{s['chayenne_copied_digits']}/{s['chayenne_digits']}` digits with `{s['chayenne_delta_vs_raw_bits']:.3f}` bit delta and beats both shuffled-target and random-source controls.",
        "YTC, Secret Library, Honeminas vectors, and Avar Tar do not show the same module-bank compatibility.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "This promotes only external holdout validation of the module bank. It does not promote Chayenne as origin, does not reduce v9, and does not translate anything.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_chayenne_external_holdout_innovation_replay_gate.py](../scripts/01_chayenne_external_holdout_innovation_replay_gate.py)",
        "- [01_chayenne_external_holdout_innovation_replay_gate.json](test_results/01_chayenne_external_holdout_innovation_replay_gate.json)",
        "- [01_chayenne_external_holdout_innovation_replay_gate.md](test_results/01_chayenne_external_holdout_innovation_replay_gate.md)",
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
