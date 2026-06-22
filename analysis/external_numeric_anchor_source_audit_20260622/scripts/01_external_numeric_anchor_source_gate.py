#!/usr/bin/env python3
"""Test known external numeric anchors as content sources for innovation tape.

This is a constructive external-source gate. It uses the already classified
external numeric strings (Chayenne, Your True Colour, Secret Library, Honeminas
vectors, Avar Tar negative control) as a tiny source bank and asks whether any
of them can reduce the promoted unified innovation tape after paid
source/offset/length costs.

Promotion is provenance-gated: a secondary/corpus-compatible Chayenne overlap
can be a mechanical clue, but not an origin formula. Only primary/confirmed
external anchors may qualify as a content-source candidate, and they still need
paid savings plus controls.
"""

from __future__ import annotations

import json
import math
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/external_numeric_anchor_source_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_external_numeric_anchor_source_gate.json"
MD_OUT = OUT_DIR / "01_external_numeric_anchor_source_gate.md"
FINAL_OUT = FRONT / "reports/final_external_numeric_anchor_source_audit.md"

PAYLOAD_GATE = ROOT / "analysis/unified_innovation_payload_audit_20260622/reports/test_results/01_unified_innovation_payload_gate.json"
EXTERNAL_CLASSIFIER = ROOT / "analysis/post_review_20260619/external_numeric_string_classifier_results.json"

LOG2_10 = math.log2(10)
MIN_LENS = [5, 8, 12]
RANDOM_SEED = 46920260622
CONTROL_TRIALS = 200
PREFIX_CUTOFFS = [512, 1024, 1536]

PROMOTABLE_CLASSES = {
    "official_primary_external",
    "confirmed_external_numeric_anchor",
}

CLASS_OVERRIDES = {
    "chayenne": "secondary_validation_corpus_compatible_not_origin",
    "your_true_colour": "official_primary_external",
    "secret_library_74032_45331": "confirmed_external_numeric_anchor",
    "honeminas_primary_vectors": "lore_selector_hypothesis_not_content_source",
    "avar_tar": "negative_control",
}


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
            continue
        current = "".join(out)
        source = int(event["source"])
        length = int(event["length"])
        out.append(current[source : source + length])
    return "".join(out)


def load_sources() -> list[dict[str, Any]]:
    data = load_json(EXTERNAL_CLASSIFIER)
    sources = []
    for row in data["rows"]:
        sources.append(
            {
                "source_id": row["name"],
                "digits": "".join(ch for ch in str(row["raw_digits"]) if ch.isdigit()),
                "classifier_classification": row["classification"],
                "provenance_class": CLASS_OVERRIDES.get(row["name"], row["classification"]),
                "evidence": row["evidence"],
                "promotable_as_origin": CLASS_OVERRIDES.get(row["name"], row["classification"]) in PROMOTABLE_CLASSES,
            }
        )
    return sources


def source_index(sources: list[dict[str, Any]], min_len: int) -> list[tuple[dict[str, Any], dict[str, list[int]]]]:
    out = []
    for source in sources:
        idx: dict[str, list[int]] = {}
        digits = source["digits"]
        for pos in range(0, max(0, len(digits) - min_len + 1)):
            idx.setdefault(digits[pos : pos + min_len], []).append(pos)
        out.append((source, idx))
    return out


def longest_match(target: str, pos: int, indexed: list[tuple[dict[str, Any], dict[str, list[int]]]], min_len: int) -> tuple[int, dict[str, Any] | None, int | None]:
    seed = target[pos : pos + min_len]
    best_len = 0
    best_source = None
    best_offset = None
    upper = min(128, len(target) - pos)
    for source, idx in indexed:
        digits = source["digits"]
        for offset in idx.get(seed, []):
            length = min_len
            while (
                length < upper
                and offset + length < len(digits)
                and digits[offset + length] == target[pos + length]
            ):
                length += 1
            if length > best_len:
                best_len = length
                best_source = source
                best_offset = offset
    return best_len, best_source, best_offset


def parse_with_sources(target: str, sources: list[dict[str, Any]], min_len: int) -> dict[str, Any]:
    indexed = source_index(sources, min_len)
    pos = 0
    events: list[dict[str, Any]] = []
    literal_start: int | None = None
    literal_buffer: list[str] = []
    while pos < len(target):
        length, source, offset = longest_match(target, pos, indexed, min_len)
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
                literal_start = None
                literal_buffer = []
            events.append(
                {
                    "kind": "external_copy",
                    "start": pos,
                    "length": length,
                    "source_id": source["source_id"],
                    "provenance_class": source["provenance_class"],
                    "promotable_as_origin": source["promotable_as_origin"],
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

    source_count = max(1, len(sources))
    max_source_len = max(1, max(len(source["digits"]) for source in sources))
    model_bits = math.log2(len(MIN_LENS)) + math.log2(source_count)
    copy_events = [event for event in events if event["kind"] == "external_copy"]
    literal_events = [event for event in events if event["kind"] == "literal"]
    copy_bits = sum(
        1.0
        + math.log2(source_count)
        + math.log2(max_source_len)
        + math.log2(max(1, int(event["length"]) - min_len + 1))
        for event in copy_events
    )
    literal_bits = sum(1.0 + math.log2(128) + int(event["length"]) * LOG2_10 for event in literal_events)
    total_bits = model_bits + copy_bits + literal_bits
    raw_bits = len(target) * LOG2_10
    promotable_copy_digits = sum(int(event["length"]) for event in copy_events if event["promotable_as_origin"])
    secondary_copy_digits = sum(int(event["length"]) for event in copy_events if not event["promotable_as_origin"])
    return {
        "min_len": min_len,
        "events": events,
        "copy_ops": len(copy_events),
        "copied_digits": sum(int(event["length"]) for event in copy_events),
        "promotable_copy_digits": promotable_copy_digits,
        "secondary_or_control_copy_digits": secondary_copy_digits,
        "literal_digits": sum(int(event["length"]) for event in literal_events),
        "literal_runs": len(literal_events),
        "model_bits": model_bits,
        "copy_bits": copy_bits,
        "literal_bits": literal_bits,
        "total_bits": total_bits,
        "raw_bits": raw_bits,
        "delta_vs_raw_bits": total_bits - raw_bits,
    }


def best_parse(target: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    parses = [parse_with_sources(target, sources, min_len) for min_len in MIN_LENS]
    best = min(parses, key=lambda row: row["total_bits"])
    return {
        "best_min_len": best["min_len"],
        "best": {key: value for key, value in best.items() if key != "events"},
        "all_minlens": [{key: value for key, value in row.items() if key != "events"} for row in parses],
        "event_samples": best["events"][:30],
    }


def per_source_results(target: str, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for source in sources:
        parsed = best_parse(target, [source])
        rows.append(
            {
                "source_id": source["source_id"],
                "provenance_class": source["provenance_class"],
                "promotable_as_origin": source["promotable_as_origin"],
                "digits": len(source["digits"]),
                **parsed["best"],
            }
        )
    return sorted(rows, key=lambda row: (row["delta_vs_raw_bits"], -row["copied_digits"]))


def shuffled_source_controls(target: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 1)
    deltas = []
    copied = []
    for _ in range(CONTROL_TRIALS):
        shuffled_sources = []
        for source in sources:
            chars = list(source["digits"])
            rng.shuffle(chars)
            copied_source = dict(source)
            copied_source["digits"] = "".join(chars)
            shuffled_sources.append(copied_source)
        parsed = best_parse(target, shuffled_sources)
        deltas.append(float(parsed["best"]["delta_vs_raw_bits"]))
        copied.append(int(parsed["best"]["copied_digits"]))
    ordered = sorted(deltas)
    copied_sorted = sorted(copied)
    return {
        "trials": CONTROL_TRIALS,
        "delta_p05": ordered[int(0.05 * (CONTROL_TRIALS - 1))],
        "delta_p50": ordered[int(0.50 * (CONTROL_TRIALS - 1))],
        "delta_p95": ordered[int(0.95 * (CONTROL_TRIALS - 1))],
        "copied_digits_p95": copied_sorted[int(0.95 * (CONTROL_TRIALS - 1))],
    }


def random_source_controls(target: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + 2)
    lengths = [len(source["digits"]) for source in sources]
    deltas = []
    copied = []
    for trial in range(CONTROL_TRIALS):
        random_sources = [
            {
                "source_id": f"random_{trial}_{idx}",
                "digits": "".join(str(rng.randrange(10)) for _ in range(length)),
                "provenance_class": "random_control",
                "promotable_as_origin": False,
            }
            for idx, length in enumerate(lengths)
        ]
        parsed = best_parse(target, random_sources)
        deltas.append(float(parsed["best"]["delta_vs_raw_bits"]))
        copied.append(int(parsed["best"]["copied_digits"]))
    ordered = sorted(deltas)
    copied_sorted = sorted(copied)
    return {
        "trials": CONTROL_TRIALS,
        "delta_p05": ordered[int(0.05 * (CONTROL_TRIALS - 1))],
        "delta_p50": ordered[int(0.50 * (CONTROL_TRIALS - 1))],
        "delta_p95": ordered[int(0.95 * (CONTROL_TRIALS - 1))],
        "copied_digits_p95": copied_sorted[int(0.95 * (CONTROL_TRIALS - 1))],
    }


def prefix_holdouts(target: str, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        train = best_parse(target[:cutoff], sources)
        min_len = int(train["best_min_len"])
        test = parse_with_sources(target[cutoff:], sources, min_len)
        rows.append(
            {
                "cutoff": cutoff,
                "selected_min_len": min_len,
                "train_delta_vs_raw_bits": train["best"]["delta_vs_raw_bits"],
                "test_delta_vs_raw_bits": test["delta_vs_raw_bits"],
                "test_copied_digits": test["copied_digits"],
                "test_promotable_copy_digits": test["promotable_copy_digits"],
            }
        )
    return rows


def make_result() -> dict[str, Any]:
    payload = load_json(PAYLOAD_GATE)
    assert_boundary(payload)
    target = render_innovation_stream(payload)
    sources = load_sources()
    all_source_parse = best_parse(target, sources)
    promotable_sources = [source for source in sources if source["promotable_as_origin"]]
    promotable_parse = best_parse(target, promotable_sources)
    per_source = per_source_results(target, sources)
    shuffled = shuffled_source_controls(target, sources)
    random_controls = random_source_controls(target, sources)
    holdouts = prefix_holdouts(target, sources)
    positive_holdouts = sum(1 for row in holdouts if row["test_delta_vs_raw_bits"] < 0)
    all_best = all_source_parse["best"]
    promotable_best = promotable_parse["best"]
    chayenne_row = next(row for row in per_source if row["source_id"] == "chayenne")
    promoted = (
        promotable_best["delta_vs_raw_bits"] < 0
        and positive_holdouts == len(holdouts)
        and all_best["delta_vs_raw_bits"] < shuffled["delta_p05"]
        and all_best["delta_vs_raw_bits"] < random_controls["delta_p05"]
    )
    weak_chayenne_clue = chayenne_row["copied_digits"] > 0 and chayenne_row["delta_vs_raw_bits"] < 0
    classification = (
        "PROMOTED_EXTERNAL_NUMERIC_ANCHOR_CONTENT_SOURCE"
        if promoted
        else (
            "chayenne_secondary_overlap_weak_clue_not_origin"
            if weak_chayenne_clue
            else "external_numeric_anchor_source_not_promoted"
        )
    )
    return {
        "schema": "external_numeric_anchor_source_gate.v1",
        "scope": "analysis_only_known_external_numeric_anchor_content_source",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {
            "unified_innovation_payload_gate": str(PAYLOAD_GATE.relative_to(ROOT)),
            "external_numeric_string_classifier": str(EXTERNAL_CLASSIFIER.relative_to(ROOT)),
        },
        "source_bank": {
            "source_count": len(sources),
            "promotable_source_count": len(promotable_sources),
            "sources": [
                {
                    "source_id": source["source_id"],
                    "digits": len(source["digits"]),
                    "classifier_classification": source["classifier_classification"],
                    "provenance_class": source["provenance_class"],
                    "promotable_as_origin": source["promotable_as_origin"],
                    "evidence": source["evidence"],
                }
                for source in sources
            ],
        },
        "summary": {
            "innovation_digits": len(target),
            "all_sources_delta_vs_raw_bits": all_best["delta_vs_raw_bits"],
            "all_sources_copied_digits": all_best["copied_digits"],
            "all_sources_promotable_copy_digits": all_best["promotable_copy_digits"],
            "promotable_sources_delta_vs_raw_bits": promotable_best["delta_vs_raw_bits"],
            "promotable_sources_copied_digits": promotable_best["copied_digits"],
            "chayenne_delta_vs_raw_bits": chayenne_row["delta_vs_raw_bits"],
            "chayenne_copied_digits": chayenne_row["copied_digits"],
            "weak_chayenne_clue": weak_chayenne_clue,
            "positive_holdouts": positive_holdouts,
            "holdout_count": len(holdouts),
            "promoted": promoted,
        },
        "all_source_parse": all_source_parse,
        "promotable_source_parse": promotable_parse,
        "per_source_results": per_source,
        "controls": {
            "shuffled_sources": shuffled,
            "random_sources": random_controls,
        },
        "holdouts": holdouts,
        "decision": {
            "external_numeric_anchor_source_promoted": promoted,
            "external_field_reduced": False,
            "v9_reduction_bits": 0.0,
            "reason": (
                "known external numeric anchors do not provide a promotable innovation content source; Chayenne overlap is secondary validation, not origin"
                if weak_chayenne_clue and not promoted
                else (
                    "known external numeric anchors do not reduce the innovation tape after paid costs and controls"
                    if not promoted
                    else "promotable external numeric anchors reduce innovation content and need executable integration"
                )
            ),
            "next_blocker": (
                "innovation content origin remains external; known short external anchors are not sufficient"
                if not promoted
                else "integrate external numeric anchor references into the executable decoder with provenance caveats"
            ),
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    controls = result["controls"]
    lines = [
        "# External Numeric Anchor Source Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This gate tests known external numeric strings as sources for the unified innovation tape.",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Innovation digits | `{s['innovation_digits']}` |",
        f"| All-source copied digits | `{s['all_sources_copied_digits']}` |",
        f"| All-source delta vs raw | `{s['all_sources_delta_vs_raw_bits']:.3f}` |",
        f"| Promotable-source copied digits | `{s['promotable_sources_copied_digits']}` |",
        f"| Promotable-source delta vs raw | `{s['promotable_sources_delta_vs_raw_bits']:.3f}` |",
        f"| Chayenne copied digits | `{s['chayenne_copied_digits']}` |",
        f"| Chayenne delta vs raw | `{s['chayenne_delta_vs_raw_bits']:.3f}` |",
        f"| Positive holdouts | `{s['positive_holdouts']}/{s['holdout_count']}` |",
        "",
        "## Per-Source Results",
        "",
        "| Source | Provenance Class | Promotable | Copied Digits | Delta vs Raw |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in result["per_source_results"]:
        lines.append(
            f"| `{row['source_id']}` | `{row['provenance_class']}` | `{row['promotable_as_origin']}` | `{row['copied_digits']}` | `{row['delta_vs_raw_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Control | Delta p05 | Delta p50 | Delta p95 | Copied p95 |",
            "| --- | ---: | ---: | ---: | ---: |",
            f"| Shuffled sources | `{controls['shuffled_sources']['delta_p05']:.3f}` | `{controls['shuffled_sources']['delta_p50']:.3f}` | `{controls['shuffled_sources']['delta_p95']:.3f}` | `{controls['shuffled_sources']['copied_digits_p95']}` |",
            f"| Random sources | `{controls['random_sources']['delta_p05']:.3f}` | `{controls['random_sources']['delta_p50']:.3f}` | `{controls['random_sources']['delta_p95']:.3f}` | `{controls['random_sources']['copied_digits_p95']}` |",
            "",
            "## Decision",
            "",
            f"`{result['decision']['reason']}`",
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
        "# Final External Numeric Anchor Source Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "Known external numeric strings were tested as content sources for the unified innovation tape.",
        f"Promotable external anchors copy only `{s['promotable_sources_copied_digits']}` digits and cost `{s['promotable_sources_delta_vs_raw_bits']:.3f}` bits versus raw declaration.",
        f"Chayenne alone copies `{s['chayenne_copied_digits']}` digits with `{s['chayenne_delta_vs_raw_bits']:.3f}` bit delta, but it remains secondary corpus-compatible validation rather than a primary origin source.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        "No external numeric anchor is integrated as an origin source, no v9 field is reduced, and no formula is promoted.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_external_numeric_anchor_source_gate.py](../scripts/01_external_numeric_anchor_source_gate.py)",
        "- [01_external_numeric_anchor_source_gate.json](test_results/01_external_numeric_anchor_source_gate.json)",
        "- [01_external_numeric_anchor_source_gate.md](test_results/01_external_numeric_anchor_source_gate.md)",
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
