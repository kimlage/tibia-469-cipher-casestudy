#!/usr/bin/env python3
"""Latent nonlocal state program pilot.

This gate tests the route selected by the latent-state synthesis: a small hidden
state program over multistream operation tokens. It is intentionally modest but
structurally different from local length/content/source priors:

- each operation is represented by a joint token over control and literal/copy
  behavior;
- a prefix-trained hidden Markov model scores future books without seeing their
  answers during training;
- the result is compared against factorized stream coding, composite unigram
  coding, and same-multiset order controls.

The gate promotes only if the latent state model reduces the combined external
stream under holdout and survives controls. It does not search plaintext or row0.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "latent_nonlocal_state_program_pilot_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

CONTROL_LEDGER = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
ROUTE_SYNTHESIS = (
    ROOT
    / "analysis"
    / "latent_state_route_synthesis_audit_20260622"
    / "reports"
    / "test_results"
    / "01_latent_state_route_synthesis.json"
)

JSON_OUT = TEST_RESULTS / "01_latent_nonlocal_state_program_pilot.json"
MD_OUT = TEST_RESULTS / "01_latent_nonlocal_state_program_pilot.md"
FINAL_OUT = FRONT / "reports" / "final_latent_nonlocal_state_program_pilot_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
STATE_COUNTS = [2, 3, 4, 5, 6]
INIT_MODES = ["hash", "position", "book_phase"]
HARD_EM_ITERS = 10
ALPHA = 0.5
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 300


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
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def qbucket(value: float | None, bins: int = 5) -> str:
    if value is None:
        return "none"
    return f"q{min(bins - 1, max(0, int(value * bins))):02d}"


def digit_signature(payload: str | None) -> str:
    if not payload:
        return "none"
    digits = [int(ch) for ch in payload]
    return f"len{len(payload)}:first{payload[0]}:sum{sum(digits) % 10}"


def behavior_symbol(row: dict[str, Any]) -> str:
    if row["op_type"] == "literal":
        return f"lit:{row['length_bucket']}:{digit_signature(row.get('literal_payload'))}"
    rank_bucket = row.get("copy_hint_rank_bucket") or "rank_none"
    occ = int(row.get("copy_hint_source_occurrences") or 0)
    occ_bucket = "occ1" if occ <= 1 else "occ2_3" if occ <= 3 else "occ4p"
    return f"copy:{row['length_bucket']}:{rank_bucket}:{occ_bucket}"


def sequence_rows() -> dict[int, list[dict[str, Any]]]:
    ledger = load_json(CONTROL_LEDGER)
    assert_boundary("unified_residual_control_ledger", ledger)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        item = dict(row)
        item["control_symbol"] = row["type_length_symbol"]
        item["behavior_symbol"] = behavior_symbol(row)
        item["joint_token"] = f"{item['control_symbol']}|{item['behavior_symbol']}"
        item["comp_bucket"] = qbucket(
            None if int(row["op_index"]) else float(row.get("composition_rank_fraction", 0.0))
            if "composition_rank_fraction" in row
            else None
        )
        grouped[int(row["book"])].append(item)
    return {
        book: sorted(rows, key=lambda row: int(row["op_index"]))
        for book, rows in grouped.items()
    }


def book_sequences(grouped: dict[int, list[dict[str, Any]]]) -> dict[int, list[str]]:
    return {book: [row["joint_token"] for row in rows] for book, rows in grouped.items()}


def train_vocab(seqs: list[list[str]]) -> list[str]:
    return sorted({token for seq in seqs for token in seq})


def map_sequence(seq: list[str], vocab_index: dict[str, int]) -> list[int]:
    unk = vocab_index["<UNK>"]
    return [vocab_index.get(token, unk) for token in seq]


def initial_states(seq: list[int], book: int, k: int, mode: str) -> list[int]:
    if mode == "position":
        return [index % k for index, _ in enumerate(seq)]
    if mode == "book_phase":
        return [((book // 10) + index) % k for index, _ in enumerate(seq)]
    return [((token * 1315423911 + index * 2654435761) & 0xFFFFFFFF) % k for index, token in enumerate(seq)]


def estimate_params(seqs: list[list[int]], states: list[list[int]], k: int, vocab_size: int) -> dict[str, list[list[float]] | list[float]]:
    start = [ALPHA] * k
    trans = [[ALPHA for _ in range(k)] for _ in range(k)]
    emit = [[ALPHA for _ in range(vocab_size)] for _ in range(k)]
    for seq, path in zip(seqs, states):
        if not seq:
            continue
        start[path[0]] += 1.0
        for state, token in zip(path, seq):
            emit[state][token] += 1.0
        for left, right in zip(path, path[1:]):
            trans[left][right] += 1.0
    start_total = sum(start)
    trans_norm = []
    for row in trans:
        total = sum(row)
        trans_norm.append([value / total for value in row])
    emit_norm = []
    for row in emit:
        total = sum(row)
        emit_norm.append([value / total for value in row])
    return {
        "start": [value / start_total for value in start],
        "trans": trans_norm,
        "emit": emit_norm,
    }


def viterbi(seq: list[int], params: dict[str, Any]) -> list[int]:
    if not seq:
        return []
    start = params["start"]
    trans = params["trans"]
    emit = params["emit"]
    k = len(start)
    scores = [math.log(start[state]) + math.log(emit[state][seq[0]]) for state in range(k)]
    back: list[list[int]] = []
    for token in seq[1:]:
        new_scores = []
        new_back = []
        for state in range(k):
            choices = [
                scores[prev] + math.log(trans[prev][state]) + math.log(emit[state][token])
                for prev in range(k)
            ]
            best_prev = max(range(k), key=lambda prev: choices[prev])
            new_scores.append(choices[best_prev])
            new_back.append(best_prev)
        scores = new_scores
        back.append(new_back)
    last = max(range(k), key=lambda state: scores[state])
    path = [last]
    for step in reversed(back):
        last = step[last]
        path.append(last)
    return list(reversed(path))


def train_hmm(train: list[tuple[int, list[int]]], k: int, mode: str, vocab_size: int) -> dict[str, Any]:
    states = [initial_states(seq, book, k, mode) for book, seq in train]
    seqs = [seq for _, seq in train]
    params = estimate_params(seqs, states, k, vocab_size)
    for _ in range(HARD_EM_ITERS):
        states = [viterbi(seq, params) for seq in seqs]
        params = estimate_params(seqs, states, k, vocab_size)
    return params


def forward_bits(seq: list[int], params: dict[str, Any]) -> float:
    if not seq:
        return 0.0
    start = params["start"]
    trans = params["trans"]
    emit = params["emit"]
    k = len(start)
    alpha = [start[state] * emit[state][seq[0]] for state in range(k)]
    scale = sum(alpha)
    if scale <= 0:
        return float("inf")
    log_prob = math.log(scale)
    alpha = [value / scale for value in alpha]
    for token in seq[1:]:
        nxt = []
        for state in range(k):
            value = sum(alpha[prev] * trans[prev][state] for prev in range(k)) * emit[state][token]
            nxt.append(value)
        scale = sum(nxt)
        if scale <= 0:
            return float("inf")
        log_prob += math.log(scale)
        alpha = [value / scale for value in nxt]
    return -log_prob / math.log(2)


def score_hmm(seqs: list[list[int]], params: dict[str, Any]) -> float:
    return sum(forward_bits(seq, params) for seq in seqs)


def smoothed_token_bits(test: list[list[str]], train: list[list[str]]) -> float:
    counts = Counter(token for seq in train for token in seq)
    vocab = set(counts) | {token for seq in test for token in seq}
    total = sum(counts.values())
    vocab_size = max(1, len(vocab))
    bits = 0.0
    for seq in test:
        for token in seq:
            prob = (counts.get(token, 0) + ALPHA) / (total + ALPHA * vocab_size)
            bits += -math.log2(prob)
    return bits


def factorized_bits(test_rows: list[list[dict[str, Any]]], train_rows: list[list[dict[str, Any]]]) -> float:
    fields = ["control_symbol", "behavior_symbol"]
    bits = 0.0
    for field in fields:
        counts = Counter(row[field] for seq in train_rows for row in seq)
        vocab = set(counts) | {row[field] for seq in test_rows for row in seq}
        total = sum(counts.values())
        vocab_size = max(1, len(vocab))
        for seq in test_rows:
            for row in seq:
                prob = (counts.get(row[field], 0) + ALPHA) / (total + ALPHA * vocab_size)
                bits += -math.log2(prob)
    return bits


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil((p / 100.0) * len(ordered)) - 1))
    return ordered[index]


def shuffled_controls(test_tokens: list[list[str]], params: dict[str, Any], vocab_index: dict[str, int], seed_offset: int) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    bits = []
    for _ in range(RANDOM_TRIALS):
        shuffled = []
        for seq in test_tokens:
            copy = list(seq)
            rng.shuffle(copy)
            shuffled.append(map_sequence(copy, vocab_index))
        bits.append(score_hmm(shuffled, params))
    return {
        "shuffle_bits_mean": sum(bits) / len(bits),
        "shuffle_bits_p05": percentile(bits, 5),
        "shuffle_bits_p50": percentile(bits, 50),
        "shuffle_bits_p95": percentile(bits, 95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def cutoff_gate(cutoff: int, grouped: dict[int, list[dict[str, Any]]], tokens_by_book: dict[int, list[str]], seed_offset: int) -> dict[str, Any]:
    train_books = [book for book in sorted(tokens_by_book) if book < cutoff]
    test_books = [book for book in sorted(tokens_by_book) if book >= cutoff]
    train_tokens = [tokens_by_book[book] for book in train_books]
    test_tokens = [tokens_by_book[book] for book in test_books]
    train_rows = [grouped[book] for book in train_books]
    test_rows = [grouped[book] for book in test_books]
    vocab = train_vocab(train_tokens) + ["<UNK>"]
    vocab_index = {token: index for index, token in enumerate(vocab)}
    train_mapped = [(book, map_sequence(tokens_by_book[book], vocab_index)) for book in train_books]
    test_mapped = [map_sequence(tokens_by_book[book], vocab_index) for book in test_books]

    candidates = []
    for k in STATE_COUNTS:
        for mode in INIT_MODES:
            params = train_hmm(train_mapped, k, mode, len(vocab))
            train_bits = score_hmm([seq for _, seq in train_mapped], params)
            candidates.append({"k": k, "mode": mode, "params": params, "train_bits": train_bits})
    candidates.sort(key=lambda row: (row["train_bits"], row["k"], row["mode"]))
    best = candidates[0]
    hmm_bits = score_hmm(test_mapped, best["params"])
    factor_bits = factorized_bits(test_rows, train_rows)
    unigram_bits = smoothed_token_bits(test_tokens, train_tokens)
    controls = shuffled_controls(test_tokens, best["params"], vocab_index, seed_offset)
    return {
        "cutoff": cutoff,
        "factorized_bits": factor_bits,
        "hmm_bits": hmm_bits,
        "hmm_delta_vs_factorized": hmm_bits - factor_bits,
        "hmm_delta_vs_unigram": hmm_bits - unigram_bits,
        "hmm_beats_factorized": hmm_bits < factor_bits,
        "hmm_beats_shuffle_p05": hmm_bits < controls["shuffle_bits_p05"],
        "selected_k": best["k"],
        "selected_mode": best["mode"],
        "shuffle_controls": controls,
        "test_books": len(test_books),
        "test_ops": sum(len(seq) for seq in test_tokens),
        "train_books": len(train_books),
        "train_ops": sum(len(seq) for seq in train_tokens),
        "unigram_bits": unigram_bits,
    }


def make_result() -> dict[str, Any]:
    route = load_json(ROUTE_SYNTHESIS)
    assert_boundary("latent_state_route_synthesis", route)
    grouped = sequence_rows()
    tokens_by_book = book_sequences(grouped)
    cutoff_rows = [
        cutoff_gate(cutoff, grouped, tokens_by_book, seed_offset=index)
        for index, cutoff in enumerate(CUTOFFS)
    ]
    total_hmm = sum(row["hmm_bits"] for row in cutoff_rows)
    total_factorized = sum(row["factorized_bits"] for row in cutoff_rows)
    total_unigram = sum(row["unigram_bits"] for row in cutoff_rows)
    beats_factorized_cells = sum(row["hmm_beats_factorized"] for row in cutoff_rows)
    beats_shuffle_cells = sum(row["hmm_beats_shuffle_p05"] for row in cutoff_rows)
    promoted = total_hmm < total_factorized and beats_factorized_cells >= 4 and beats_shuffle_cells >= 4
    classification = (
        "PROMOTED_LATENT_NONLOCAL_STATE_CLUE"
        if promoted
        else "LATENT_NONLOCAL_STATE_PILOT_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "cutoff_rows": cutoff_rows,
        "decision": {
            "generator_promoted": False,
            "latent_state_clue_promoted": promoted,
            "next_blocker": (
                "small HMM-style latent states over current operation tokens are "
                "insufficient unless they reduce factorized streams under holdout "
                "and order controls"
            ),
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "latent_state_route_synthesis": rel(ROUTE_SYNTHESIS),
            "unified_residual_control_ledger": rel(CONTROL_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "latent_nonlocal_state_program_pilot.v1",
        "scope": "analysis_only_hmm_multistream_operation_tokens",
        "summary": {
            "beats_factorized_cells": beats_factorized_cells,
            "beats_shuffle_p05_cells": beats_shuffle_cells,
            "cutoffs": CUTOFFS,
            "state_counts": STATE_COUNTS,
            "total_factorized_bits": total_factorized,
            "total_hmm_bits": total_hmm,
            "total_hmm_delta_vs_factorized": total_hmm - total_factorized,
            "total_hmm_delta_vs_unigram": total_hmm - total_unigram,
            "total_unigram_bits": total_unigram,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Latent Nonlocal State Program Pilot",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test a small hidden-state program over multistream operation tokens. This "
        "is the first pilot of the `latent_nonlocal_state_program_pilot` route.",
        "",
        "## Summary",
        "",
        f"- Total HMM bits: `{s['total_hmm_bits']:.3f}`.",
        f"- Total factorized stream bits: `{s['total_factorized_bits']:.3f}`.",
        f"- Delta vs factorized: `{s['total_hmm_delta_vs_factorized']:.3f}` bits.",
        f"- Cells beating factorized: `{s['beats_factorized_cells']}/5`.",
        f"- Cells beating shuffled p05: `{s['beats_shuffle_p05_cells']}/5`.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | K | Init | Test ops | HMM bits | Factorized bits | Delta | Beats shuffle p05 |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['selected_k']}` | `{row['selected_mode']}` | "
            f"`{row['test_ops']}` | `{row['hmm_bits']:.3f}` | "
            f"`{row['factorized_bits']:.3f}` | `{row['hmm_delta_vs_factorized']:.3f}` | "
            f"`{row['hmm_beats_shuffle_p05']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The small latent-state program is promoted only if it beats the factorized "
            "stream model and same-multiset order controls under holdout. Otherwise "
            "the route remains open but requires richer state than this HMM pilot.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Latent Nonlocal State Program Pilot Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can a small prefix-trained hidden-state program over joint operation tokens "
        "reduce the current factorized external streams under holdout?",
        "",
        "## Result",
        "",
        f"Total HMM cost is `{s['total_hmm_bits']:.3f}` bits versus "
        f"`{s['total_factorized_bits']:.3f}` factorized bits "
        f"(`{s['total_hmm_delta_vs_factorized']:.3f}`). It beats the factorized "
        f"baseline in `{s['beats_factorized_cells']}/5` prefix cells and beats "
        f"same-multiset shuffled order p05 in `{s['beats_shuffle_p05_cells']}/5` cells.",
        "",
        "## Decision",
        "",
        "This is not a generator unless both reductions hold. Row0, plaintext, "
        "translation, and compression_bound remain unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_latent_nonlocal_state_program_pilot.py](../scripts/01_latent_nonlocal_state_program_pilot.py)",
        "- [01_latent_nonlocal_state_program_pilot.json](test_results/01_latent_nonlocal_state_program_pilot.json)",
        "- [01_latent_nonlocal_state_program_pilot.md](test_results/01_latent_nonlocal_state_program_pilot.md)",
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
