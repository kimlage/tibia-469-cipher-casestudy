#!/usr/bin/env python3
"""Start-candidate ranking gate.

The all-position transducer found a decoder-visible content clue, but the
argmax model predicted zero starts because starts are rare. This gate asks the
more useful generative question: can the same kind of prefix/content signal
produce a candidate set that lowers the paid cost of declaring internal starts?

For each held-out book, a prefix-trained scorer ranks every internal digit
position. A budget policy selects top-K positions. The codec then pays:

- which true starts inside the candidate set are active;
- which true starts outside the candidate set remain as missed corrections.

This is compared against the exact true-count composition baseline
`log2(C(N, S))` and random top-K controls. No operation-token sequence, exact
internal starts, or target-conditioned copy availability is granted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "digit_content_boundary_transducer_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
CONTROL_LEDGER = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
ALL_POSITION_GATE = TEST_RESULTS / "01_all_position_boundary_transducer_gate.json"

JSON_OUT = TEST_RESULTS / "02_start_candidate_ranking_gate.json"
MD_OUT = TEST_RESULTS / "02_start_candidate_ranking_gate.md"
FINAL_OUT = FRONT / "reports" / "final_digit_content_boundary_transducer_audit.md"

CUTOFFS = [20, 30, 40, 50, 60]
ALPHA = 0.5
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500
RATE_POLICIES = [0.005, 0.01, 0.02, 0.04, 0.08]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened the case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    if decision.get("translation_delta") not in {None, "NONE"}:
        raise RuntimeError(f"{name} changed translation boundary")


def log2_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    if k == 0 or k == n:
        return 0.0
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / math.log(2)


def bucket_fraction(pos: int, length: int, bins: int, prefix: str) -> str:
    if length <= 1:
        return f"{prefix}_only"
    idx = min(bins - 1, max(0, int((pos / length) * bins)))
    return f"{prefix}_q{idx:02d}"


def length_bucket(length: int) -> str:
    for cut in [80, 120, 180, 260]:
        if length <= cut:
            return f"booklen_le_{cut}"
    return "booklen_gt_260"


def phase(book: int) -> str:
    return f"phase_{(book // 10) * 10}_{(book // 10) * 10 + 9}"


def build_start_labels(ledger: dict[str, Any]) -> dict[int, set[int]]:
    starts: dict[int, set[int]] = defaultdict(set)
    for row in ledger["ledger_rows"]:
        book = int(row["book"])
        start = int(row["target_start"])
        if start:
            starts[book].add(start)
    return starts


def prior_material_for(books: dict[int, str], book: int, pos: int) -> str:
    return "".join(books[idx] for idx in range(book)) + books[book][:pos]


def position_rows(books: dict[int, str], starts: dict[int, set[int]]) -> dict[int, list[dict[str, Any]]]:
    rows_by_book: dict[int, list[dict[str, Any]]] = {}
    for book in range(10, 70):
        text = books[book]
        rows = []
        for pos in range(1, len(text)):
            prefix = text[:pos]
            prev1 = prefix[-1:] or "START"
            prev2 = prefix[-2:] if len(prefix) >= 2 else f"START{prev1}"
            prev3 = prefix[-3:] if len(prefix) >= 3 else f"START{prev2}"
            prior = prior_material_for(books, book, pos)
            prior_without_suffix = prior[:-1]
            suffix2 = prefix[-2:] if len(prefix) >= 2 else ""
            suffix3 = prefix[-3:] if len(prefix) >= 3 else ""
            suffix4 = prefix[-4:] if len(prefix) >= 4 else ""
            rows.append(
                {
                    "book": book,
                    "book_length": len(text),
                    "is_start": pos in starts.get(book, set()),
                    "length_bucket": length_bucket(len(text)),
                    "phase": phase(book),
                    "pos": pos,
                    "pos_bucket": bucket_fraction(pos, len(text), 8, "pos"),
                    "prev1": prev1,
                    "prev2": prev2,
                    "prev3": prev3,
                    "suffix2_seen": "s2_seen" if suffix2 and suffix2 in prior_without_suffix else "s2_new",
                    "suffix3_seen": "s3_seen" if suffix3 and suffix3 in prior_without_suffix else "s3_new",
                    "suffix4_seen": "s4_seen" if suffix4 and suffix4 in prior_without_suffix else "s4_new",
                }
            )
        rows_by_book[book] = rows
    return rows_by_book


FAMILIES = [
    "global",
    "pos_bucket",
    "length_pos",
    "phase_pos",
    "prev1",
    "prev2",
    "prev3",
    "prev2_pos",
    "prev3_pos",
    "suffix2_seen",
    "suffix3_seen",
    "suffix4_seen",
    "suffix3_pos",
    "prev2_suffix3",
    "length_prev2",
]


def feature(row: dict[str, Any], family: str) -> str:
    if family == "global":
        return "global"
    if family == "pos_bucket":
        return row["pos_bucket"]
    if family == "length_pos":
        return f"{row['length_bucket']}|{row['pos_bucket']}"
    if family == "phase_pos":
        return f"{row['phase']}|{row['pos_bucket']}"
    if family == "prev1":
        return row["prev1"]
    if family == "prev2":
        return row["prev2"]
    if family == "prev3":
        return row["prev3"]
    if family == "prev2_pos":
        return f"{row['prev2']}|{row['pos_bucket']}"
    if family == "prev3_pos":
        return f"{row['prev3']}|{row['pos_bucket']}"
    if family == "suffix2_seen":
        return row["suffix2_seen"]
    if family == "suffix3_seen":
        return row["suffix3_seen"]
    if family == "suffix4_seen":
        return row["suffix4_seen"]
    if family == "suffix3_pos":
        return f"{row['suffix3_seen']}|{row['pos_bucket']}"
    if family == "prev2_suffix3":
        return f"{row['prev2']}|{row['suffix3_seen']}"
    if family == "length_prev2":
        return f"{row['length_bucket']}|{row['prev2']}"
    raise KeyError(family)


def train_counts(rows_by_book: dict[int, list[dict[str, Any]]], books: list[int], family: str) -> dict[str, Counter[bool]]:
    counts: dict[str, Counter[bool]] = defaultdict(Counter)
    for book in books:
        for row in rows_by_book[book]:
            counts[feature(row, family)][bool(row["is_start"])] += 1
    return counts


def score_row(row: dict[str, Any], family: str, counts: dict[str, Counter[bool]], global_counts: Counter[bool]) -> float:
    counter = counts.get(feature(row, family)) or global_counts
    total = sum(counter.values())
    return (counter.get(True, 0) + ALPHA) / (total + ALPHA * 2)


def rank_book(rows: list[dict[str, Any]], family: str, counts: dict[str, Counter[bool]]) -> list[dict[str, Any]]:
    global_counts = Counter()
    for counter in counts.values():
        global_counts.update(counter)
    ranked = []
    for row in rows:
        item = dict(row)
        item["score"] = score_row(row, family, counts, global_counts)
        ranked.append(item)
    ranked.sort(key=lambda row: (-row["score"], row["pos"]))
    return ranked


def candidate_cost_for_book(ranked: list[dict[str, Any]], rate: float) -> dict[str, Any]:
    n = len(ranked)
    starts = {row["pos"] for row in ranked if row["is_start"]}
    s = len(starts)
    k = min(n, max(1, int(round(n * rate))))
    candidates = {row["pos"] for row in ranked[:k]}
    hits = len(starts & candidates)
    misses = s - hits
    false_positive = k - hits
    baseline = log2_choose(n, s)
    candidate_bits = log2_choose(k, hits) + log2_choose(n - k, misses)
    return {
        "baseline_bits": baseline,
        "candidate_bits": candidate_bits,
        "false_positive_candidates": false_positive,
        "hits": hits,
        "k": k,
        "misses": misses,
        "n": n,
        "starts": s,
    }


def candidate_cost(
    rows_by_book: dict[int, list[dict[str, Any]]],
    books: list[int],
    family: str,
    counts: dict[str, Counter[bool]],
    rate: float,
) -> dict[str, Any]:
    total = Counter()
    bits = {"baseline_bits": 0.0, "candidate_bits": 0.0}
    for book in books:
        row = candidate_cost_for_book(rank_book(rows_by_book[book], family, counts), rate)
        bits["baseline_bits"] += row["baseline_bits"]
        bits["candidate_bits"] += row["candidate_bits"]
        total.update(
            {
                "false_positive_candidates": row["false_positive_candidates"],
                "hits": row["hits"],
                "k": row["k"],
                "misses": row["misses"],
                "positions": row["n"],
                "starts": row["starts"],
            }
        )
    return {
        **bits,
        **dict(total),
        "delta_vs_baseline": bits["candidate_bits"] - bits["baseline_bits"],
        "recall": total["hits"] / max(1, total["starts"]),
    }


def descriptor_penalty(counts: dict[str, Counter[bool]]) -> float:
    states = len(counts)
    cells = sum(len(counter) for counter in counts.values())
    return math.log2(len(FAMILIES) * len(RATE_POLICIES)) + states + 0.25 * cells


def loo_score(rows_by_book: dict[int, list[dict[str, Any]]], train_books: list[int], family: str, rate: float) -> float:
    if len(train_books) < 2:
        return float("inf")
    total = 0.0
    for heldout in train_books:
        subtrain = [book for book in train_books if book != heldout]
        counts = train_counts(rows_by_book, subtrain, family)
        total += candidate_cost(rows_by_book, [heldout], family, counts, rate)["candidate_bits"]
    return total + descriptor_penalty(train_counts(rows_by_book, train_books, family))


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def random_candidate_controls(
    rows_by_book: dict[int, list[dict[str, Any]]],
    books: list[int],
    rate: float,
    real_baseline_bits: float,
    seed_offset: int,
) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + seed_offset)
    deltas = []
    for _ in range(RANDOM_TRIALS):
        candidate_bits = 0.0
        for book in books:
            rows = rows_by_book[book]
            n = len(rows)
            starts = {row["pos"] for row in rows if row["is_start"]}
            s = len(starts)
            k = min(n, max(1, int(round(n * rate))))
            candidates = set(rng.sample([row["pos"] for row in rows], k))
            hits = len(starts & candidates)
            misses = s - hits
            candidate_bits += log2_choose(k, hits) + log2_choose(n - k, misses)
        deltas.append(candidate_bits - real_baseline_bits)
    return {
        "delta_mean": sum(deltas) / len(deltas),
        "delta_p05": percentile(deltas, 5),
        "delta_p50": percentile(deltas, 50),
        "delta_p95": percentile(deltas, 95),
        "seed": RANDOM_SEED + seed_offset,
        "trials": RANDOM_TRIALS,
    }


def cutoff_gate(cutoff: int, rows_by_book: dict[int, list[dict[str, Any]]], seed_offset: int) -> dict[str, Any]:
    train_books = [book for book in range(10, cutoff)]
    test_books = [book for book in range(cutoff, 70)]
    candidates = []
    for family in FAMILIES:
        for rate in RATE_POLICIES:
            candidates.append(
                {
                    "family": family,
                    "loo_train_mdl_bits": loo_score(rows_by_book, train_books, family, rate),
                    "rate": rate,
                }
            )
    selected = min(candidates, key=lambda row: (row["loo_train_mdl_bits"], row["family"], row["rate"]))
    counts = train_counts(rows_by_book, train_books, selected["family"])
    result = candidate_cost(rows_by_book, test_books, selected["family"], counts, selected["rate"])
    controls = random_candidate_controls(
        rows_by_book,
        test_books,
        selected["rate"],
        result["baseline_bits"],
        seed_offset,
    )
    result.update(
        {
            "beats_random_p05": result["delta_vs_baseline"] < controls["delta_p05"],
            "family": selected["family"],
            "loo_train_mdl_bits": selected["loo_train_mdl_bits"],
            "rate": selected["rate"],
            "random_candidate_controls": controls,
        }
    )
    return {
        "cutoff": cutoff,
        "train_books": train_books,
        "test_books": test_books,
        "selected": result,
    }


def make_result() -> dict[str, Any]:
    previous = load_json(ALL_POSITION_GATE)
    ledger = load_json(CONTROL_LEDGER)
    assert_boundary("all_position_boundary_transducer", previous)
    assert_boundary("unified_residual_control_ledger", ledger)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    starts = build_start_labels(ledger)
    rows_by_book = position_rows(books, starts)
    cutoff_rows = [
        cutoff_gate(cutoff, rows_by_book, seed_offset=index)
        for index, cutoff in enumerate(CUTOFFS)
    ]
    selected_rows = [row["selected"] for row in cutoff_rows]
    total_candidate = sum(row["candidate_bits"] for row in selected_rows)
    total_baseline = sum(row["baseline_bits"] for row in selected_rows)
    total_delta = total_candidate - total_baseline
    beats_random = sum(row["beats_random_p05"] for row in selected_rows)
    total_hits = sum(row["hits"] for row in selected_rows)
    total_starts = sum(row["starts"] for row in selected_rows)
    total_misses = sum(row["misses"] for row in selected_rows)
    total_k = sum(row["k"] for row in selected_rows)
    promoted = total_delta < 0 and beats_random >= 4 and total_misses < total_starts
    weak = total_hits > 0 and beats_random >= 3
    classification = (
        "PROMOTED_START_CANDIDATE_RANKING_CLUE"
        if promoted
        else "WEAK_START_CANDIDATE_RANKING_CLUE"
        if weak
        else "START_CANDIDATE_RANKING_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "cutoff_rows": cutoff_rows,
        "decision": {
            "generator_promoted": False,
            "grants_exact_internal_starts": False,
            "grants_operation_token_sequence": False,
            "grants_target_conditioned_copy_availability": False,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
        },
        "inputs": {
            "all_position_boundary_transducer": rel(ALL_POSITION_GATE),
            "books_digits": rel(BOOKS_DIGITS),
            "unified_residual_control_ledger": rel(CONTROL_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "start_candidate_ranking_gate.v1",
        "scope": "analysis_only_digit_prefix_start_candidate_ranking",
        "summary": {
            "beats_random_p05_cells": beats_random,
            "cutoffs": CUTOFFS,
            "total_baseline_bits": total_baseline,
            "total_candidate_bits": total_candidate,
            "total_candidate_positions": total_k,
            "total_delta_vs_baseline": total_delta,
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_recall": total_hits / max(1, total_starts),
            "total_starts": total_starts,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Start Candidate Ranking Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether decoder-visible prefix/content scores can produce a candidate "
        "set that reduces the cost of declaring internal starts.",
        "",
        "## Summary",
        "",
        f"- Candidate bits: `{s['total_candidate_bits']:.3f}`.",
        f"- Exact start composition baseline bits: `{s['total_baseline_bits']:.3f}`.",
        f"- Delta vs baseline: `{s['total_delta_vs_baseline']:.3f}` bits.",
        f"- Cells beating random top-K p05: `{s['beats_random_p05_cells']}/5`.",
        f"- Candidate positions selected: `{s['total_candidate_positions']}`.",
        f"- Start hits: `{s['total_hits']}/{s['total_starts']}`.",
        f"- Misses requiring correction: `{s['total_misses']}`.",
        f"- Recall: `{s['total_recall']:.3f}`.",
        "",
        "## Prefix Holdouts",
        "",
        "| Cutoff | Family | Rate | K | Hits | Misses | Candidate bits | Baseline bits | Delta | Random p05 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in result["cutoff_rows"]:
        selected = row["selected"]
        lines.append(
            f"| `{row['cutoff']}` | `{selected['family']}` | `{selected['rate']:.3f}` | "
            f"`{selected['k']}` | `{selected['hits']}` | `{selected['misses']}` | "
            f"`{selected['candidate_bits']:.3f}` | `{selected['baseline_bits']:.3f}` | "
            f"`{selected['delta_vs_baseline']:.3f}` | `{selected['beats_random_p05']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Promotion requires candidate+miss-correction bits below the exact "
            "composition baseline and random top-K controls. Candidate enrichment "
            "without net cost reduction remains a diagnostic clue only.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Final Digit Content Boundary Transducer Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Can decoder-visible digit-prefix/content features rank a small candidate set "
        "for internal starts and reduce the paid start-position dependency?",
        "",
        "## Result",
        "",
        f"The candidate ranking codec costs `{s['total_candidate_bits']:.3f}` bits "
        f"versus `{s['total_baseline_bits']:.3f}` exact start-composition bits "
        f"(`{s['total_delta_vs_baseline']:.3f}`). It beats random top-K p05 in "
        f"`{s['beats_random_p05_cells']}/5` cells and captures "
        f"`{s['total_hits']}/{s['total_starts']}` starts, leaving "
        f"`{s['total_misses']}` missed-start corrections.",
        "",
        "## Decision",
        "",
        "This gate is a candidate-set test, not a complete parser. It is promoted "
        "only if the candidate set plus corrections reduces the start ledger under "
        "controls. Row0, plaintext, translation, and compression_bound remain "
        "unchanged.",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_all_position_boundary_transducer_gate.py](../scripts/01_all_position_boundary_transducer_gate.py)",
        "- [02_start_candidate_ranking_gate.py](../scripts/02_start_candidate_ranking_gate.py)",
        "- [01_all_position_boundary_transducer_gate.json](test_results/01_all_position_boundary_transducer_gate.json)",
        "- [02_start_candidate_ranking_gate.json](test_results/02_start_candidate_ranking_gate.json)",
        "- [02_start_candidate_ranking_gate.md](test_results/02_start_candidate_ranking_gate.md)",
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
