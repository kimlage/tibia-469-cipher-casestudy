#!/usr/bin/env python3
"""Chunk length-prior integration gate.

The first bucket chunk-origin pilot showed that removing exact copy length makes
candidate sets too broad. This gate tests the most direct rescue: learn a
decoder-visible copy-length prior inside each coarse bucket, then use the
existing same-length copy hint.

The key question is whether this two-stage program reduces the external
copy-length/source ledger under prefix holdout, or whether the apparent full-fit
length structure is only post-hoc.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "chunk_length_prior_integration_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
BUCKET_PILOT = (
    ROOT
    / "analysis"
    / "joint_chunk_origin_beam_pilot_audit_20260622"
    / "reports"
    / "test_results"
    / "01_bucket_chunk_origin_beam_pilot.json"
)

JSON_OUT = TEST_RESULTS / "01_chunk_length_prior_integration_gate.json"
MD_OUT = TEST_RESULTS / "01_chunk_length_prior_integration_gate.md"
FINAL_OUT = FRONT / "reports" / "final_chunk_length_prior_integration_audit.md"

BUCKET_RANGES = {
    "len_0008": (1, 8),
    "len_0016": (9, 16),
    "len_0032": (17, 32),
    "len_0064": (33, 64),
    "len_0128": (65, 128),
    "len_0256p": (129, None),
}
CUTOFFS = [20, 30, 40, 50, 60]
FAMILIES = [
    "bucket",
    "bucket_pos",
    "bucket_booklen_pos",
    "bucket_opcount_pos",
]
ALPHA = 0.5
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500


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
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def book_length_bucket(length: int) -> str:
    if length <= 64:
        return "book_len_0064"
    if length <= 128:
        return "book_len_0128"
    if length <= 256:
        return "book_len_0256"
    return "book_len_0512p"


def op_position_bucket(index: int, count: int) -> str:
    if index == 0:
        return "first"
    if index == count - 1:
        return "last"
    if index <= 2:
        return "early"
    return "middle"


def feasible_length_count(bucket: str, book_length: int, target_start: int) -> int:
    low, high = BUCKET_RANGES[bucket]
    remaining = book_length - target_start
    high = remaining if high is None else min(high, remaining)
    return max(1, high - low + 1)


def family_key(row: dict[str, Any], family: str) -> tuple[Any, ...]:
    if family == "bucket":
        return (row["length_bucket"],)
    if family == "bucket_pos":
        return (row["length_bucket"], row["op_pos_bucket"])
    if family == "bucket_booklen_pos":
        return (row["length_bucket"], row["book_length_bucket"], row["op_pos_bucket"])
    if family == "bucket_opcount_pos":
        return (row["length_bucket"], row["book_op_count"], row["op_pos_bucket"])
    raise KeyError(family)


def copy_rows() -> list[dict[str, Any]]:
    ledger = load_json(LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    rows = []
    for row in ledger["ledger_rows"]:
        if row["op_type"] != "copy":
            continue
        length_bucket = str(row["coarse_type_length_bucket"]).split(":", 1)[1]
        op_count = int(row["book_op_count"])
        op_index = int(row["op_index"])
        item = {
            "book": int(row["book"]),
            "book_length": int(row["book_length"]),
            "book_length_bucket": book_length_bucket(int(row["book_length"])),
            "book_op_count": op_count,
            "copy_hint_rank_bits": float(row["copy_hint_rank_bits"]),
            "exact_length": int(row["exact_length"]),
            "feasible_length_count": feasible_length_count(
                length_bucket,
                int(row["book_length"]),
                int(row["target_start"]),
            ),
            "length_bucket": length_bucket,
            "op_index": op_index,
            "op_pos_bucket": op_position_bucket(op_index, op_count),
            "target_start": int(row["target_start"]),
        }
        # The raw-source comparator is already reported in the bucket pilot and
        # minimal ledger. Here the real comparator is length-prior + copy hint.
        rows.append(item)
    return rows


def train_counts(rows: list[dict[str, Any]], cutoff: int, family: str) -> tuple[dict[tuple[Any, ...], Counter], dict[str, Counter]]:
    counts: dict[tuple[Any, ...], Counter] = defaultdict(Counter)
    bucket_backoff: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        if int(row["book"]) >= cutoff:
            continue
        length = int(row["exact_length"])
        counts[family_key(row, family)][length] += 1
        bucket_backoff[str(row["length_bucket"])][length] += 1
    return counts, bucket_backoff


def score_rows(
    rows: list[dict[str, Any]],
    counts: dict[tuple[Any, ...], Counter],
    bucket_backoff: dict[str, Counter],
    family: str,
) -> dict[str, Any]:
    length_bits = 0.0
    uniform_bits = 0.0
    top1_hits = 0
    events = 0
    for row in rows:
        counter = counts.get(family_key(row, family)) or bucket_backoff.get(
            str(row["length_bucket"]),
            Counter(),
        )
        vocab = int(row["feasible_length_count"])
        total = sum(counter.values())
        length = int(row["exact_length"])
        if total:
            probability = (counter.get(length, 0) + ALPHA) / (total + ALPHA * vocab)
        else:
            probability = 1.0 / vocab
        length_bits += -math.log2(max(probability, 1e-300))
        uniform_bits += math.log2(vocab)
        if counter and counter.most_common(1)[0][0] == length:
            top1_hits += 1
        events += 1
    return {
        "events": events,
        "length_prior_bits": length_bits,
        "top1_length_hits": top1_hits,
        "uniform_length_bits": uniform_bits,
        "saving_vs_uniform_length_bits": uniform_bits - length_bits,
    }


def train_selected_family(rows: list[dict[str, Any]], cutoff: int) -> dict[str, Any]:
    train = [row for row in rows if int(row["book"]) < cutoff]
    scored = []
    for family in FAMILIES:
        counts, backoff = train_counts(rows, cutoff, family)
        score = score_rows(train, counts, backoff, family)
        scored.append({"family": family, **score})
    scored.sort(key=lambda row: (-row["saving_vs_uniform_length_bits"], row["family"]))
    return {"selected_family": scored[0]["family"], "train_scores": scored}


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((p / 100.0) * len(ordered)) - 1))
    return ordered[index]


def random_same_bucket_controls(
    test_rows: list[dict[str, Any]],
    counts: dict[tuple[Any, ...], Counter],
    backoff: dict[str, Counter],
    family: str,
    seed_offset: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    bits = []
    lengths_by_bucket: dict[str, list[int]] = defaultdict(list)
    for row in test_rows:
        low, high = BUCKET_RANGES[str(row["length_bucket"])]
        remaining = int(row["book_length"]) - int(row["target_start"])
        high = remaining if high is None else min(high, remaining)
        lengths_by_bucket[str(row["length_bucket"])].extend(range(low, high + 1))
    for _ in range(RANDOM_TRIALS):
        randomized = []
        for row in test_rows:
            item = dict(row)
            item["exact_length"] = rng.choice(lengths_by_bucket[str(row["length_bucket"])])
            randomized.append(item)
        bits.append(score_rows(randomized, counts, backoff, family)["length_prior_bits"])
    return {
        "random_bits_mean": mean(bits) if bits else 0.0,
        "random_bits_p05": percentile(bits, 5) if bits else 0.0,
        "random_bits_p50": percentile(bits, 50) if bits else 0.0,
        "random_bits_p95": percentile(bits, 95) if bits else 0.0,
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def full_fit_scores(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = []
    for family in FAMILIES:
        counts: dict[tuple[Any, ...], Counter] = defaultdict(Counter)
        backoff: dict[str, Counter] = defaultdict(Counter)
        for row in rows:
            counts[family_key(row, family)][int(row["exact_length"])] += 1
            backoff[str(row["length_bucket"])][int(row["exact_length"])] += 1
        scored.append({"family": family, **score_rows(rows, counts, backoff, family)})
    scored.sort(key=lambda row: (-row["saving_vs_uniform_length_bits"], row["family"]))
    return scored


def prefix_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for index, cutoff in enumerate(CUTOFFS):
        selected = train_selected_family(rows, cutoff)
        family = selected["selected_family"]
        counts, backoff = train_counts(rows, cutoff, family)
        test = [row for row in rows if int(row["book"]) >= cutoff]
        score = score_rows(test, counts, backoff, family)
        controls = random_same_bucket_controls(test, counts, backoff, family, seed_offset=index)
        copy_hint_bits = sum(float(row["copy_hint_rank_bits"]) for row in test)
        integrated_bits = score["length_prior_bits"] + copy_hint_bits
        uniform_integrated_bits = score["uniform_length_bits"] + copy_hint_bits
        out.append(
            {
                "cutoff": cutoff,
                "copy_hint_bits": copy_hint_bits,
                "integrated_length_prior_plus_copy_hint_bits": integrated_bits,
                "random_same_bucket_controls": controls,
                "selected_family": family,
                "test_events": score["events"],
                "test_length_prior_bits": score["length_prior_bits"],
                "test_length_prior_beats_random_p05": score["length_prior_bits"]
                < controls["random_bits_p05"],
                "test_saving_vs_uniform_length_bits": score["saving_vs_uniform_length_bits"],
                "test_top1_length_hits": score["top1_length_hits"],
                "train_scores": selected["train_scores"],
                "uniform_length_plus_copy_hint_bits": uniform_integrated_bits,
            }
        )
    return out


def make_result() -> dict[str, Any]:
    bucket_pilot = load_json(BUCKET_PILOT)
    assert_boundary("bucket_chunk_origin_beam_pilot", bucket_pilot)
    rows = copy_rows()
    ledger = load_json(LEDGER)
    composition_bits = float(ledger["summary"]["composition_index_bits"])
    copy_hint_bits = float(ledger["summary"]["copy_hint_rank_bits"])
    full_scores = full_fit_scores(rows)
    prefix = prefix_rows(rows)
    best_full = full_scores[0]
    full_integrated_bits = best_full["length_prior_bits"] + copy_hint_bits
    current_composition_plus_hint = composition_bits + copy_hint_bits
    holdout_positive = sum(row["test_saving_vs_uniform_length_bits"] > 0 for row in prefix)
    holdout_beats_random = sum(row["test_length_prior_beats_random_p05"] for row in prefix)
    promoted = (
        full_integrated_bits < current_composition_plus_hint
        and holdout_positive >= 4
        and holdout_beats_random >= 4
    )
    classification = (
        "PROMOTED_COPY_LENGTH_PRIOR_INTEGRATION"
        if promoted
        else "POSTHOC_COPY_LENGTH_PRIOR_NOT_PROMOTED"
        if full_integrated_bits < current_composition_plus_hint
        else "COPY_LENGTH_PRIOR_REJECTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "copy_length_prior_promoted": promoted,
            "generator_promoted": False,
            "next_blocker": (
                "copy length has full-fit structure, but the tested prefix-frozen "
                "contexts do not generalize; joint chunk-origin still needs a "
                "non-posthoc target-free length/chunk state"
            ),
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "full_fit_scores": full_scores,
        "inputs": {
            "bucket_chunk_origin_beam_pilot": rel(BUCKET_PILOT),
            "unified_external_tape_ledger": rel(LEDGER),
        },
        "plaintext_claim": False,
        "prefix_rows": prefix,
        "schema": "chunk_length_prior_integration_gate.v1",
        "scope": "analysis_only_copy_length_prior_plus_same_length_chunk_hint",
        "summary": {
            "best_full_family": best_full["family"],
            "best_full_integrated_length_prior_plus_copy_hint_bits": full_integrated_bits,
            "best_full_length_prior_bits": best_full["length_prior_bits"],
            "copy_hint_bits": copy_hint_bits,
            "copy_ops": len(rows),
            "current_composition_index_bits": composition_bits,
            "current_composition_plus_copy_hint_bits": current_composition_plus_hint,
            "full_fit_delta_vs_current_composition_plus_hint": full_integrated_bits
            - current_composition_plus_hint,
            "holdout_beats_random_p05_cells": holdout_beats_random,
            "holdout_positive_saving_cells": holdout_positive,
            "uniform_length_bits": best_full["uniform_length_bits"],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Chunk Length-Prior Integration Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether a prefix-trained copy-length prior inside the granted coarse "
        "bucket can be integrated with the same-length copy hint to replace part "
        "of the external length/source ledger.",
        "",
        "## Full-Fit Lower Bound",
        "",
        f"- Best family: `{s['best_full_family']}`.",
        f"- Full-fit length-prior bits: `{s['best_full_length_prior_bits']:.3f}`.",
        f"- Copy-hint bits: `{s['copy_hint_bits']:.3f}`.",
        f"- Integrated full-fit bits: `{s['best_full_integrated_length_prior_plus_copy_hint_bits']:.3f}`.",
        f"- Current composition-index + copy-hint bits: `{s['current_composition_plus_copy_hint_bits']:.3f}`.",
        f"- Full-fit delta vs current: `{s['full_fit_delta_vs_current_composition_plus_hint']:.3f}` bits.",
        "",
        "## Prefix Holdout",
        "",
        "| Cutoff | Selected family | Test ops | Length bits | Saving vs uniform | Beats random p05 | Integrated bits |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in result["prefix_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_family']}` | "
            f"`{row['test_events']}` | `{row['test_length_prior_bits']:.3f}` | "
            f"`{row['test_saving_vs_uniform_length_bits']:.3f}` | "
            f"`{row['test_length_prior_beats_random_p05']}` | "
            f"`{row['integrated_length_prior_plus_copy_hint_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The apparent full-fit copy-length structure is not promoted. It can "
            "make the full ledger look smaller after seeing the whole corpus, but "
            "prefix-frozen contexts do not beat the uniform feasible-length code. "
            "This keeps the blocker at a target-free length/chunk state, not a "
            "posthoc length-prior table.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Chunk Length-Prior Integration Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can a decoder-visible copy-length prior inside the coarse bucket rescue "
        "the joint chunk-origin route by paying length first and then using the "
        "same-length copy hint?",
        "",
        "## Result",
        "",
        f"Full-fit, the best family `{s['best_full_family']}` costs "
        f"`{s['best_full_length_prior_bits']:.3f}` length-prior bits; combined "
        f"with the `{s['copy_hint_bits']:.3f}`-bit copy hint, it is "
        f"`{s['full_fit_delta_vs_current_composition_plus_hint']:.3f}` bits "
        "relative to the current composition-index + copy-hint ledger.",
        "",
        f"That gain does not generalize: prefix holdout has "
        f"`{s['holdout_positive_saving_cells']}/5` positive-saving cells and "
        f"`{s['holdout_beats_random_p05_cells']}/5` cells beating random p05.",
        "",
        "## Decision",
        "",
        "The length-prior rescue is posthoc under current evidence. It does not "
        "promote an executable generator component and does not change row0, "
        "plaintext, translation, or compression_bound.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_chunk_length_prior_integration_gate.py](../scripts/01_chunk_length_prior_integration_gate.py)",
        "- [01_chunk_length_prior_integration_gate.json](test_results/01_chunk_length_prior_integration_gate.json)",
        "- [01_chunk_length_prior_integration_gate.md](test_results/01_chunk_length_prior_integration_gate.md)",
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
