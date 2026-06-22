#!/usr/bin/env python3
"""Nonlocal event-policy program gate for the v9 innovation replay.

This audit tests the internal route that remains after the external-surface
frontier: can a sequence program over replay events explain copy/literal and
coarse source-length choices in holdout? It does not try another local field
codec. It treats the innovation replay as an event stream and compares
nonlocal sequence models against independent declaration baselines and shuffled
controls.
"""

from __future__ import annotations

import heapq
import json
import math
import random
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis/nonlocal_event_policy_program_audit_20260622"
OUT_DIR = FRONT / "reports/test_results"
JSON_OUT = OUT_DIR / "01_nonlocal_event_policy_program_gate.json"
MD_OUT = OUT_DIR / "01_nonlocal_event_policy_program_gate.md"
FINAL_OUT = FRONT / "reports/final_nonlocal_event_policy_program_audit.md"

PAYLOAD_GATE = ROOT / "analysis/unified_innovation_payload_audit_20260622/reports/test_results/01_unified_innovation_payload_gate.json"
V9_GATE = ROOT / "analysis/executable_v9_innovation_copy_continuation_audit_20260622/reports/test_results/01_executable_v9_innovation_copy_continuation_gate.json"

ALPHA = 0.5
MODEL_COST_BITS = 8.0
EVENT_PREFIX_CUTOFFS = [20, 35, 50]
BEAM_WIDTHS = [16, 64, 256]
SHUFFLE_TRIALS = 100
RANDOM_SEED = 46920260622 + 910


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


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


def length_bucket(kind: str, length: int) -> str:
    if kind == "copy" and length >= 64:
        return "cap64"
    if length <= 1:
        return "l01"
    if length <= 3:
        return "l02_03"
    if length <= 7:
        return "l04_07"
    if length <= 11:
        return "l08_11"
    if length <= 15:
        return "l12_15"
    if length <= 31:
        return "l16_31"
    if length <= 63:
        return "l32_63"
    if length <= 127:
        return "l64_127"
    return "l128_plus"


def source_bucket(event: dict[str, Any], previous: dict[str, Any] | None) -> str:
    if event["kind"] != "copy":
        return "na"
    source = int(event["source"])
    start = int(event["start"])
    length = int(event["length"])
    if previous and previous["kind"] == "copy":
        if source == int(previous["source"]) + int(previous["length"]):
            return "cont_prev_source"
        if start == int(previous["start"]) + int(previous["length"]):
            return "copy_after_copy_noncont"
    if source == 0:
        return "source_zero"
    age = start - source
    if age <= 64:
        return "age_le64"
    if age <= 256:
        return "age_le256"
    if age <= 768:
        return "age_le768"
    return "age_gt768"


def event_symbols(events: list[dict[str, Any]]) -> dict[str, list[str]]:
    streams = {"type_length": [], "type_length_sourcebucket": []}
    previous: dict[str, Any] | None = None
    for event in events:
        kind = str(event["kind"])
        length = int(event["length"])
        type_symbol = "C" if kind == "copy" else "L"
        lb = length_bucket(kind, length)
        streams["type_length"].append(f"{type_symbol}:{lb}")
        if kind == "copy":
            streams["type_length_sourcebucket"].append(f"{type_symbol}:{lb}:{source_bucket(event, previous)}")
        else:
            streams["type_length_sourcebucket"].append(f"{type_symbol}:{lb}:literal")
        previous = event
    return streams


def contexts_for(sequence: list[str], model: str, index: int) -> tuple[str, ...]:
    if model == "unigram":
        return ("*",)
    if model == "markov1":
        return (sequence[index - 1],) if index >= 1 else ("<BOS>",)
    if model == "markov2":
        if index >= 2:
            return (sequence[index - 2], sequence[index - 1])
        if index == 1:
            return ("<BOS>", sequence[index - 1])
        return ("<BOS>", "<BOS>")
    if model == "phase4_markov1":
        previous = sequence[index - 1] if index >= 1 else "<BOS>"
        return (f"phase{index % 4}", previous)
    if model == "phase8_markov1":
        previous = sequence[index - 1] if index >= 1 else "<BOS>"
        return (f"phase{index % 8}", previous)
    raise KeyError(model)


MODELS = ["markov1", "markov2", "phase4_markov1", "phase8_markov1"]


def fit_counts(sequence: list[str], model: str) -> tuple[Counter[str], dict[tuple[str, ...], Counter[str]]]:
    global_counts: Counter[str] = Counter()
    context_counts: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for index, symbol in enumerate(sequence):
        global_counts[symbol] += 1
        context_counts[contexts_for(sequence, model, index)][symbol] += 1
    return global_counts, context_counts


def code_sequence(train: list[str], test: list[str], model: str, alphabet: list[str]) -> float:
    global_counts, context_counts = fit_counts(train, model)
    vocab = max(1, len(alphabet))
    combined = list(train) + list(test)
    bits = 0.0
    for index in range(len(train), len(combined)):
        symbol = combined[index]
        context = contexts_for(combined, model, index)
        counter = context_counts.get(context, global_counts)
        total = sum(counter.values())
        probability = (counter.get(symbol, 0) + ALPHA) / (total + ALPHA * vocab)
        bits += -math.log2(probability)
    return bits


def train_prequential_bits(train: list[str], model: str, alphabet: list[str]) -> float:
    if len(train) <= 1:
        return float("inf")
    bits = 0.0
    for cutoff in range(1, len(train)):
        bits += code_sequence(train[:cutoff], [train[cutoff]], model, alphabet)
    return bits + MODEL_COST_BITS


def select_model(train: list[str], alphabet: list[str]) -> str:
    scored = [(train_prequential_bits(train, model, alphabet), model) for model in MODELS]
    return min(scored)[1]


def baseline_bits(train: list[str], test: list[str], alphabet: list[str]) -> float:
    return code_sequence(train, test, "unigram", alphabet)


def evaluate_split(sequence: list[str], cutoff: int, forced_model: str | None = None) -> dict[str, Any]:
    alphabet = sorted(set(sequence))
    train = sequence[:cutoff]
    test = sequence[cutoff:]
    model = forced_model or select_model(train, alphabet)
    independent = baseline_bits(train, test, alphabet)
    program = code_sequence(train, test, model, alphabet) + MODEL_COST_BITS
    return {
        "baseline_unigram_bits": independent,
        "cutoff": cutoff,
        "model": model,
        "program_bits": program,
        "saving_bits": independent - program,
        "test_events": len(test),
        "train_events": len(train),
    }


def next_symbol_distribution(prefix: list[str], model: str, alphabet: list[str]) -> list[tuple[float, str]]:
    global_counts, context_counts = fit_counts(prefix, model)
    context = contexts_for(prefix + ["<X>"], model, len(prefix))
    counter = context_counts.get(context, global_counts)
    total = sum(counter.values())
    vocab = max(1, len(alphabet))
    scored = []
    for symbol in alphabet:
        probability = (counter.get(symbol, 0) + ALPHA) / (total + ALPHA * vocab)
        scored.append((-math.log2(probability), symbol))
    return sorted(scored)


def beam_contains_true(train: list[str], test: list[str], model: str, alphabet: list[str], width: int) -> dict[str, Any]:
    beam: list[tuple[float, list[str]]] = [(0.0, [])]
    true_survives_until = 0
    true_tuple = tuple(test)
    for step in range(len(test)):
        candidates: list[tuple[float, list[str]]] = []
        for cost, suffix in beam:
            prefix = train + suffix
            for symbol_cost, symbol in next_symbol_distribution(prefix, model, alphabet):
                candidates.append((cost + symbol_cost, suffix + [symbol]))
        beam = heapq.nsmallest(width, candidates, key=lambda item: item[0])
        prefixes = {tuple(suffix) for _, suffix in beam}
        if true_tuple[: step + 1] in prefixes:
            true_survives_until = step + 1
    final_sequences = [tuple(suffix) for _, suffix in beam]
    exact = true_tuple in final_sequences
    rank = None
    if exact:
        rank = final_sequences.index(true_tuple) + 1
    return {
        "exact_suffix_in_beam": exact,
        "true_rank": rank,
        "true_survives_events": true_survives_until,
        "width": width,
    }


def shuffled_controls(sequence: list[str], cutoff: int, model: str, real_saving: float, rng: random.Random) -> dict[str, Any]:
    train = sequence[:cutoff]
    test = sequence[cutoff:]
    alphabet = sorted(set(sequence))
    values = []
    for _ in range(SHUFFLE_TRIALS):
        shuffled = list(test)
        rng.shuffle(shuffled)
        independent = baseline_bits(train, shuffled, alphabet)
        program = code_sequence(train, shuffled, model, alphabet) + MODEL_COST_BITS
        values.append(independent - program)
    ordered = sorted(values)
    return {
        "beats_shuffle_p95": real_saving > ordered[int(0.95 * (len(ordered) - 1))],
        "shuffle_mean": sum(values) / len(values),
        "shuffle_p05": ordered[int(0.05 * (len(ordered) - 1))],
        "shuffle_p50": ordered[int(0.50 * (len(ordered) - 1))],
        "shuffle_p95": ordered[int(0.95 * (len(ordered) - 1))],
        "trials": SHUFFLE_TRIALS,
    }


def evaluate_stream(name: str, sequence: list[str]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in name))
    splits = []
    for cutoff in EVENT_PREFIX_CUTOFFS:
        evaluated = evaluate_split(sequence, cutoff)
        alphabet = sorted(set(sequence))
        train = sequence[:cutoff]
        test = sequence[cutoff:]
        evaluated["beam"] = [
            beam_contains_true(train, test, evaluated["model"], alphabet, width)
            for width in BEAM_WIDTHS
        ]
        evaluated["shuffle_controls"] = shuffled_controls(
            sequence, cutoff, evaluated["model"], evaluated["saving_bits"], rng
        )
        splits.append(evaluated)
    return {
        "alphabet_size": len(set(sequence)),
        "event_count": len(sequence),
        "sequence": sequence,
        "splits": splits,
        "summary": {
            "exact_suffix_beam_hits": sum(any(row["exact_suffix_in_beam"] for row in split["beam"]) for split in splits),
            "positive_splits": sum(split["saving_bits"] > 0 for split in splits),
            "shuffle_p95_wins": sum(split["shuffle_controls"]["beats_shuffle_p95"] for split in splits),
            "split_count": len(splits),
            "total_baseline_bits": sum(split["baseline_unigram_bits"] for split in splits),
            "total_program_bits": sum(split["program_bits"] for split in splits),
            "total_saving_bits": sum(split["saving_bits"] for split in splits),
        },
    }


def make_result() -> dict[str, Any]:
    payload = load_json(PAYLOAD_GATE)
    v9 = load_json(V9_GATE)
    for name, data in [("payload", payload), ("v9", v9)]:
        assert_boundary(name, data)
    if payload["classification"] != "PROMOTED_UNIFIED_INNOVATION_PAYLOAD_LEDGER":
        raise RuntimeError("payload ledger is not promoted")
    if v9["classification"] != "PROMOTED_EXECUTABLE_V9_INNOVATION_COPY_CONTINUATION_LEDGER":
        raise RuntimeError("v9 ledger is not promoted")

    streams = event_symbols(payload["event_ledger"])
    results = {name: evaluate_stream(name, seq) for name, seq in streams.items()}
    main = results["type_length_sourcebucket"]["summary"]
    promoted = (
        main["total_saving_bits"] > 0
        and main["positive_splits"] >= 2
        and main["shuffle_p95_wins"] >= 2
        and main["exact_suffix_beam_hits"] >= 1
    )
    classification = (
        "PROMOTED_NONLOCAL_EVENT_POLICY_PROGRAM_CANDIDATE"
        if promoted
        else "nonlocal_event_policy_program_not_promoted"
    )
    return {
        "schema": "nonlocal_event_policy_program_gate.v1",
        "scope": "analysis_only_nonlocal_event_policy_program",
        "classification": classification,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "row0_status": "unchanged_exogenous",
        "compression_bound_status": "unchanged",
        "inputs": {
            "payload_gate": rel(PAYLOAD_GATE),
            "v9_gate": rel(V9_GATE),
        },
        "models": MODELS,
        "event_prefix_cutoffs": EVENT_PREFIX_CUTOFFS,
        "beam_widths": BEAM_WIDTHS,
        "streams": results,
        "decision": {
            "nonlocal_event_policy_promoted": promoted,
            "main_stream": "type_length_sourcebucket",
            "v9_reduction_bits": 0.0,
            "reason": (
                "nonlocal sequence model predicts coarse replay event policy in holdout"
                if promoted
                else "nonlocal sequence models do not generate or reduce the joint event policy stream in holdout after model cost"
            ),
            "next_blocker": (
                "event schedule and copy/literal/source-length policy remain external"
                if not promoted
                else "candidate still needs executable decoder integration with paid corrections"
            ),
        },
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Nonlocal Event Policy Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This gate tests replay events as a joint sequence, not as separate source/length/literal subcodecs.",
        "",
        "| Stream | Events | Alphabet | Splits | Positive | Shuffle p95 wins | Beam exact hits | Total Saving Bits |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, evaluated in result["streams"].items():
        s = evaluated["summary"]
        lines.append(
            f"| `{name}` | {evaluated['event_count']} | {evaluated['alphabet_size']} | {s['split_count']} | {s['positive_splits']} | {s['shuffle_p95_wins']} | {s['exact_suffix_beam_hits']} | {s['total_saving_bits']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"`{result['decision']['reason']}`",
            "",
            "No v9 reduction is integrated in this run.",
            "",
            "`row0`, plaintext, translation, semantics, and `compression_bound` remain unchanged.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    main = result["streams"]["type_length_sourcebucket"]["summary"]
    lines = [
        "# Final Nonlocal Event Policy Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        "This audit follows the live internal route from the generator decision ledger: a nonlocal event-policy program over the v9 innovation replay.",
        "It codes the replay event sequence under train-prefix holdout and checks whether the true suffix remains in finite beams.",
        "",
        f"For the main joint stream `type_length_sourcebucket`, total saving is `{main['total_saving_bits']:.3f}` bits across `{main['split_count']}` splits, with `{main['positive_splits']}` positive splits, `{main['shuffle_p95_wins']}` shuffle-p95 wins, and `{main['exact_suffix_beam_hits']}` exact suffix beam hits.",
        "",
        "## Decision",
        "",
        f"`{result['classification']}`.",
        "",
        result["decision"]["reason"].capitalize() + ".",
        "",
        "This does not change v9, row0, plaintext, semantics, or the compression bound.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_nonlocal_event_policy_program_gate.py](../scripts/01_nonlocal_event_policy_program_gate.py)",
        "- [01_nonlocal_event_policy_program_gate.json](test_results/01_nonlocal_event_policy_program_gate.json)",
        "- [01_nonlocal_event_policy_program_gate.md](test_results/01_nonlocal_event_policy_program_gate.md)",
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
