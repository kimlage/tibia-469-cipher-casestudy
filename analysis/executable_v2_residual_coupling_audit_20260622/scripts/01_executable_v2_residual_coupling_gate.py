#!/usr/bin/env python3
"""Executable v2 residual coupling gate.

The online x64 coarse-control program is the first promoted executable tape
reduction. This front does two things:

1. Compiles the executable ledger v2 by replacing the old uniform coarse-control
   tape with the online x64 rank/correction tape.
2. Tests whether the new online state helps code the still-external exact
   book-level composition index. This is an exact codec test: quantile bucket
   plus within-bucket offset reconstructs the original composition rank.

Scope is analysis-only. It does not touch row0, plaintext, translation,
semantics, or the compression bound.
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
FRONT = ROOT / "analysis" / "executable_v2_residual_coupling_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

MINIMAL_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
ONLINE_X64 = (
    ROOT
    / "analysis"
    / "online_x64_coarse_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_online_x64_coarse_control_program_gate.json"
)
COMPOSITION_GATE = (
    ROOT
    / "analysis"
    / "composition_index_structure_audit_20260622"
    / "reports"
    / "test_results"
    / "01_composition_index_structure_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_executable_v2_residual_coupling_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v2_residual_coupling_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v2_residual_coupling_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
ALPHA = 0.5
RANDOM_TRIALS = 200
RANDOM_SEED = 46920260622 + 364

CONTEXTS = {
    "global": tuple(),
    "book_length": ("book_length_bucket",),
    "op_count": ("op_count_bucket",),
    "online_status": ("online_status",),
    "online_rank": ("online_rank_bucket",),
    "online_status_x_opcount": ("online_status", "op_count_bucket"),
    "online_status_x_length": ("online_status", "book_length_bucket"),
    "online_paid_x_opcount": ("online_paid_bucket", "op_count_bucket"),
}


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
    row0 = data.get("row0_status") or data.get("decision", {}).get("row0_status")
    if row0 not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status: {row0}")


def log2(value: float) -> float:
    return math.log2(value)


def qbucket(fraction: float) -> str:
    return f"q{min(9, max(0, int(float(fraction) * 10))):02d}"


def op_count_bucket(count: int) -> str:
    if count <= 1:
        return "ops_01"
    if count <= 3:
        return "ops_02_03"
    if count <= 6:
        return "ops_04_06"
    if count <= 10:
        return "ops_07_10"
    return "ops_11p"


def paid_bucket(bits: float) -> str:
    if bits == 0:
        return "paid_0000"
    if bits <= 4:
        return "paid_0004"
    if bits <= 8:
        return "paid_0008"
    if bits <= 16:
        return "paid_0016"
    if bits <= 32:
        return "paid_0032"
    return "paid_0032p"


def rank_bucket(rank: int | None) -> str:
    if rank is None:
        return "rank_miss"
    bits = log2(rank)
    if bits <= 1:
        return "rank_0001"
    if bits <= 4:
        return "rank_0004"
    if bits <= 8:
        return "rank_0008"
    if bits <= 10:
        return "rank_0010"
    return "rank_0010p"


def bucket_size(composition_count: int, q: str) -> int:
    if composition_count <= 1:
        return 1 if q == "q00" else 0
    wanted = int(q[1:])
    denominator = composition_count - 1
    low = math.ceil(wanted * denominator / 10)
    if wanted == 9:
        high = denominator
    else:
        high = math.ceil((wanted + 1) * denominator / 10) - 1
    return max(0, high - low + 1)


def context_key(row: dict[str, Any], features: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(feature, "<NA>")) for feature in features)


def train_counts(rows: list[dict[str, Any]], features: tuple[str, ...], label_field: str) -> dict[tuple[str, ...], Counter]:
    counts: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    for row in rows:
        counts[context_key(row, features)][row[label_field]] += 1
    return dict(counts)


def prob(counts: dict[tuple[str, ...], Counter], global_counts: Counter, ctx: tuple[str, ...], label: str) -> float:
    selected = counts.get(ctx, global_counts)
    total = sum(selected.values())
    vocab = 10
    return (selected.get(label, 0) + ALPHA) / (total + ALPHA * vocab)


def make_book_rows(minimal: dict[str, Any], online: dict[str, Any], composition: dict[str, Any]) -> list[dict[str, Any]]:
    ledger_by_book: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in minimal["ledger_rows"]:
        ledger_by_book[int(row["book"])].append(row)
    comp_by_book = {int(row["book"]): row for row in composition["rank_rows"]}
    online_by_book = {int(row["book"]): row for row in online["rows"]}

    rows = []
    for book in range(10, 70):
        ledger_rows = ledger_by_book[book]
        comp = comp_by_book[book]
        online_row = online_by_book[book]
        composition_count = int(comp["composition_count"])
        composition_rank = int(comp["composition_rank"])
        rank_fraction = float(comp["rank_fraction"])
        label = qbucket(rank_fraction)
        literal_bits = sum(float(row["literal_payload_bits"]) for row in ledger_rows)
        copy_hint_bits = sum(float(row["copy_hint_rank_bits"]) for row in ledger_rows)
        rows.append(
            {
                "book": book,
                "book_length": int(comp["book_length"]),
                "book_length_bucket": comp["book_length_bucket"],
                "composition_bits": float(comp["composition_bits_uniform"]),
                "composition_count": composition_count,
                "composition_rank": composition_rank,
                "composition_qbucket": label,
                "copy_hint_bits": copy_hint_bits,
                "hit_rank": online_row["hit_rank"],
                "literal_payload_bits": literal_bits,
                "online_paid_bucket": paid_bucket(float(online_row["online_paid_coarse_bits"])),
                "online_paid_coarse_bits": float(online_row["online_paid_coarse_bits"]),
                "online_rank_bucket": rank_bucket(online_row["hit_rank"]),
                "online_status": "hit" if online_row["sequence_in_beam"] else "miss",
                "op_count": int(comp["op_count"]),
                "op_count_bucket": comp.get("op_count_bucket", op_count_bucket(int(comp["op_count"]))),
                "offset_bits_for_true_qbucket": log2(max(1, bucket_size(composition_count, label))),
                "remaining_residual_bits": float(comp["composition_bits_uniform"]) + literal_bits + copy_hint_bits,
            }
        )
    return rows


def compile_v2_ledger(minimal: dict[str, Any], online: dict[str, Any], book_rows: list[dict[str, Any]]) -> dict[str, Any]:
    old = minimal["summary"]
    online_summary = online["summary"]
    total_excluding_seed = (
        float(online_summary["online_paid_coarse_bits"])
        + float(old["composition_index_bits"])
        + float(old["literal_payload_bits"])
        + float(old["copy_hint_rank_bits"])
    )
    total_including_seed = total_excluding_seed + float(old["seed_payload_bits"])
    return {
        "book_rows": book_rows,
        "summary": {
            "books": 60,
            "copy_hint_rank_bits": float(old["copy_hint_rank_bits"]),
            "literal_payload_bits": float(old["literal_payload_bits"]),
            "old_coarse_control_bits": float(old["coarse_control_bits_uniform"]),
            "old_total_external_tape_bits_excluding_seed": float(old["total_external_tape_bits_excluding_seed"]),
            "old_total_external_tape_bits_including_seed": float(old["total_external_tape_bits_including_seed"]),
            "online_coarse_control_bits": float(online_summary["online_paid_coarse_bits"]),
            "online_coarse_exact_books_without_correction": float(online_summary["online_exact_books_without_correction"]),
            "online_coarse_exact_ops_without_correction": float(online_summary["online_exact_ops_without_correction"]),
            "online_coarse_saving_bits": float(online_summary["saving_vs_minimal_coarse_bits"]),
            "composition_index_bits": float(old["composition_index_bits"]),
            "seed_payload_bits": float(old["seed_payload_bits"]),
            "total_external_tape_bits_excluding_seed": total_excluding_seed,
            "total_external_tape_bits_including_seed": total_including_seed,
        },
    }


def score_model(
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    model_name: str,
    label_override: dict[int, str] | None = None,
) -> dict[str, float]:
    features = CONTEXTS[model_name]
    global_counts = Counter(row["composition_qbucket"] for row in train)
    counts = train_counts(train, features, "composition_qbucket")
    bits = 0.0
    uniform_bits = 0.0
    hits = 0
    for row in test:
        label = label_override.get(row["book"], row["composition_qbucket"]) if label_override else row["composition_qbucket"]
        size = bucket_size(int(row["composition_count"]), label)
        if size <= 0:
            # Invalid quantile for this book count: charge exact fallback.
            bits += float(row["composition_bits"])
        else:
            p = prob(counts, global_counts, context_key(row, features), label)
            bits += -log2(max(p, 1e-300)) + log2(size)
        uniform_bits += float(row["composition_bits"])
        hits += int(label == row["composition_qbucket"])
    return {
        "bits": bits,
        "exact_label_hits": hits,
        "saving_bits": uniform_bits - bits,
        "uniform_bits": uniform_bits,
    }


def composition_coupling_gate(book_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    model_rows = {}
    totals_by_model = {}
    controls_by_model = {}
    for model_name in CONTEXTS:
        rows = []
        totals = Counter()
        shuffled_savings = []
        for cutoff in CUTOFFS:
            train = [row for row in book_rows if row["book"] < cutoff]
            test = [row for row in book_rows if row["book"] >= cutoff]
            scored = score_model(train, test, model_name)
            rows.append({"cutoff": cutoff, **scored})
            for key, value in scored.items():
                totals[key] += value
            labels = [row["composition_qbucket"] for row in train]
            for _ in range(RANDOM_TRIALS):
                shuffled_train = [dict(row) for row in train]
                shuffled_labels = list(labels)
                rng.shuffle(shuffled_labels)
                for row, label in zip(shuffled_train, shuffled_labels):
                    row["composition_qbucket"] = label
                shuffled_savings.append(score_model(shuffled_train, test, model_name)["saving_bits"])
        model_rows[model_name] = rows
        totals_by_model[model_name] = dict(totals)
        controls_by_model[model_name] = {
            "shuffled_train_saving_mean": mean(shuffled_savings) if shuffled_savings else 0.0,
            "shuffled_train_saving_p95": percentile(shuffled_savings, 0.95) if shuffled_savings else 0.0,
        }

    best_model = max(
        totals_by_model,
        key=lambda name: (
            totals_by_model[name]["saving_bits"],
            -totals_by_model[name]["bits"],
        ),
    )
    best = totals_by_model[best_model]
    best_control = controls_by_model[best_model]
    promoted = best["saving_bits"] > 0 and best["saving_bits"] > best_control["shuffled_train_saving_p95"]
    return {
        "classification": (
            "PROMOTED_ONLINE_STATE_COMPOSITION_INDEX_CODEC"
            if promoted
            else "ONLINE_STATE_COMPOSITION_INDEX_CODEC_NOT_PROMOTED"
        ),
        "controls_by_model": controls_by_model,
        "decision": {
            "best_model": best_model,
            "promoted": promoted,
        },
        "model_rows": model_rows,
        "totals_by_model": totals_by_model,
    }


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


def make_result() -> dict[str, Any]:
    minimal = load_json(MINIMAL_LEDGER)
    online = load_json(ONLINE_X64)
    composition = load_json(COMPOSITION_GATE)
    assert_boundary("minimal_ledger", minimal)
    assert_boundary("online_x64", online)
    assert_boundary("composition_gate", composition)
    if online["classification"] != "PROMOTED_ONLINE_X64_MINIMAL_LEDGER_REDUCTION":
        raise RuntimeError("v2 ledger expects promoted online x64 coarse-control reduction")
    book_rows = make_book_rows(minimal, online, composition)
    v2 = compile_v2_ledger(minimal, online, book_rows)
    coupling = composition_coupling_gate(book_rows)
    v2_reduction = (
        v2["summary"]["old_total_external_tape_bits_excluding_seed"]
        - v2["summary"]["total_external_tape_bits_excluding_seed"]
    )
    classification = (
        "PROMOTED_EXECUTABLE_V2_LEDGER_AND_COMPOSITION_CODEC"
        if coupling["classification"] == "PROMOTED_ONLINE_STATE_COMPOSITION_INDEX_CODEC"
        else "PROMOTED_EXECUTABLE_V2_LEDGER_ONLY"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "composition_coupling_gate": coupling,
        "decision": {
            "composition_codec_promoted": coupling["decision"]["promoted"],
            "executable_v2_ledger_promoted": v2_reduction > 0,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "executable_v2_ledger": v2,
        "inputs": {
            "composition_index_gate": rel(COMPOSITION_GATE),
            "minimal_external_tape_ledger": rel(MINIMAL_LEDGER),
            "online_x64_coarse_control_program": rel(ONLINE_X64),
            "random_seed": RANDOM_SEED,
            "random_trials": RANDOM_TRIALS,
        },
        "plaintext_claim": False,
        "schema": "executable_v2_residual_coupling_gate.v1",
        "scope": "analysis_only_executable_v2_ledger_and_online_state_residual_coupling",
        "summary": {
            "classification": classification,
            "composition_codec_classification": coupling["classification"],
            "composition_codec_promoted": coupling["decision"]["promoted"],
            "executable_v2_reduction_excluding_seed_bits": v2_reduction,
            "old_total_excluding_seed": v2["summary"]["old_total_external_tape_bits_excluding_seed"],
            "old_total_including_seed": v2["summary"]["old_total_external_tape_bits_including_seed"],
            "v2_total_excluding_seed": v2["summary"]["total_external_tape_bits_excluding_seed"],
            "v2_total_including_seed": v2["summary"]["total_external_tape_bits_including_seed"],
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any], path: Path) -> None:
    s = result["summary"]
    v2 = result["executable_v2_ledger"]["summary"]
    coupling = result["composition_coupling_gate"]
    best_model = coupling["decision"]["best_model"]
    best = coupling["totals_by_model"][best_model]
    control = coupling["controls_by_model"][best_model]
    lines = [
        "# Executable v2 Residual Coupling Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## A. Executable Ledger v2",
        "",
        "Ledger v2 replaces the old uniform coarse-control tape with the promoted "
        "online x64 rank/correction tape. All other external tapes remain unchanged.",
        "",
        f"- Old external bits excluding seed: `{s['old_total_excluding_seed']:.3f}`.",
        f"- v2 external bits excluding seed: `{s['v2_total_excluding_seed']:.3f}`.",
        f"- Reduction excluding seed: `{s['executable_v2_reduction_excluding_seed_bits']:.3f}` bits.",
        f"- Old external bits including seed: `{s['old_total_including_seed']:.3f}`.",
        f"- v2 external bits including seed: `{s['v2_total_including_seed']:.3f}`.",
        "",
        "| Tape | Bits |",
        "| --- | ---: |",
        f"| online x64 coarse-control rank/correction | `{v2['online_coarse_control_bits']:.3f}` |",
        f"| composition index | `{v2['composition_index_bits']:.3f}` |",
        f"| literal payload | `{v2['literal_payload_bits']:.3f}` |",
        f"| copy-hint rank | `{v2['copy_hint_rank_bits']:.3f}` |",
        f"| seed payload | `{v2['seed_payload_bits']:.3f}` |",
        "",
        "## B. Online-State Composition Index Coupling",
        "",
        f"- Best model: `{best_model}`.",
        f"- Best model bits: `{best['bits']:.3f}`.",
        f"- Uniform composition bits: `{best['uniform_bits']:.3f}`.",
        f"- Saving: `{best['saving_bits']:.3f}` bits.",
        f"- Shuffled-train p95 saving: `{control['shuffled_train_saving_p95']:.3f}` bits.",
        f"- Classification: `{coupling['classification']}`.",
        "",
        "| Model | Bits | Uniform | Saving | Shuffled p95 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for model_name, totals in sorted(
        coupling["totals_by_model"].items(),
        key=lambda item: item[1]["saving_bits"],
        reverse=True,
    ):
        ctrl = coupling["controls_by_model"][model_name]
        lines.append(
            f"| `{model_name}` | `{totals['bits']:.3f}` | `{totals['uniform_bits']:.3f}` | "
            f"`{totals['saving_bits']:.3f}` | `{ctrl['shuffled_train_saving_p95']:.3f}` |"
        )
    lines.extend(["", "## Decision", ""])
    if result["decision"]["composition_codec_promoted"]:
        lines.append(
            "The online x64 state also reduces the exact composition-index tape. "
            "This promotes executable ledger v2 plus a residual composition codec."
        )
    else:
        lines.append(
            "Executable ledger v2 is promoted because it incorporates the online x64 "
            "coarse-control reduction. The online state does not promote a further "
            "composition-index codec; exact fine length composition remains external."
        )
    lines.extend(
        [
            "",
            "Remaining external fields: composition index, literal payload, copy-hint "
            "rank/source, seed payload, and `row0`.",
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
                "classification": result["classification"],
                "composition_codec_classification": result["summary"][
                    "composition_codec_classification"
                ],
                "v2_reduction_bits": result["summary"][
                    "executable_v2_reduction_excluding_seed_bits"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
