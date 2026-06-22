#!/usr/bin/env python3
"""Composition-index structure audit.

The book-level controller reduced fine length residuals to a per-book
composition index once the coarse type:length_bucket sequence and book_length
are known. This gate tests whether that index has prefix-generalizable
structure, or whether it remains external payload.

No target text, plaintext, row0 origin, or exact residuals are used to choose
the coarse sequence. This script only scores the already-defined composition
index field.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "composition_index_structure_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
LEDGER_PATH = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
BOOK_LEVEL_PATH = (
    ROOT
    / "analysis"
    / "book_level_coarse_length_controller_audit_20260622"
    / "reports"
    / "test_results"
    / "01_book_level_coarse_length_controller_gate.json"
)
JSON_OUT = TEST_RESULTS / "01_composition_index_structure_gate.json"
MD_OUT = TEST_RESULTS / "01_composition_index_structure_gate.md"

CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 500
ALPHA = 0.5
PROMOTION_MARGIN_BITS = 10.0

BUCKET_RANGES = {
    "len_0008": (1, 8),
    "len_0016": (9, 16),
    "len_0032": (17, 32),
    "len_0064": (33, 64),
    "len_0128": (65, 128),
    "len_0256p": (129, None),
}

CONTEXTS: dict[str, tuple[str, ...]] = {
    "global": tuple(),
    "book_length_bucket": ("book_length_bucket",),
    "op_count_bucket": ("op_count_bucket",),
    "book_phase": ("book_phase",),
    "phase_x_length": ("book_phase", "book_length_bucket"),
    "count_x_length": ("op_count_bucket", "book_length_bucket"),
    "first_symbol": ("first_symbol",),
    "last_symbol": ("last_symbol",),
}

PARTITIONS = {
    "quantile10": 10,
    "edge10": 10,
    "side_edge5": 10,
}


def log2(value: float) -> float:
    return math.log2(value)


def book_phase(book: int) -> str:
    if book < 20:
        return "phase_10_19"
    if book < 35:
        return "phase_20_34"
    if book < 50:
        return "phase_35_49"
    if book < 60:
        return "phase_50_59"
    return "phase_60_69"


def book_length_bucket(length: int) -> str:
    if length <= 64:
        return "book_len_0064"
    if length <= 128:
        return "book_len_0128"
    if length <= 256:
        return "book_len_0256"
    return "book_len_0512p"


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


def bucket_range(symbol: str, book_length: int) -> tuple[int, int]:
    _, bucket = symbol.split(":", 1)
    low, high = BUCKET_RANGES[bucket]
    if high is None:
        high = book_length
    return low, min(high, book_length)


def context(row: dict, features: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(feature, "<NA>")) for feature in features)


def ceil_div(numerator: int, denominator: int) -> int:
    return -(-numerator // denominator)


def quantile_bucket(rank: int, count: int, bucket_count: int = 10) -> tuple[str, int]:
    bucket = min(bucket_count - 1, (rank * bucket_count) // count)
    start = ceil_div(bucket * count, bucket_count)
    end_exclusive = ceil_div((bucket + 1) * count, bucket_count)
    width = end_exclusive - start
    return f"q{bucket:02d}", width


def edge_bucket(rank: int, count: int, bucket_count: int = 10) -> tuple[str, int]:
    edge_slots = (count + 1) // 2
    edge_rank = min(rank, count - 1 - rank)
    bucket = min(bucket_count - 1, (edge_rank * bucket_count) // max(1, edge_slots))
    start = ceil_div(bucket * edge_slots, bucket_count)
    end_exclusive = ceil_div((bucket + 1) * edge_slots, bucket_count)
    width = 2 * (end_exclusive - start)
    if count % 2 == 1 and start <= count // 2 < end_exclusive:
        width -= 1
    return f"e{bucket:02d}", width


def side_edge_bucket(rank: int, count: int, edge_bucket_count: int = 5) -> tuple[str, int]:
    side = "lo" if rank < count / 2 else "hi"
    edge_slots = (count + 1) // 2
    edge_rank = min(rank, count - 1 - rank)
    bucket = min(edge_bucket_count - 1, (edge_rank * edge_bucket_count) // max(1, edge_slots))
    start = ceil_div(bucket * edge_slots, edge_bucket_count)
    end_exclusive = ceil_div((bucket + 1) * edge_slots, edge_bucket_count)
    width = end_exclusive - start
    if side == "hi" and count % 2 == 1 and start <= count // 2 < end_exclusive:
        width -= 1
    return f"{side}_e{bucket:02d}", width


def partition_symbol(partition: str, rank: int, count: int) -> tuple[str, int]:
    if count <= 1:
        return "only", 1
    if partition == "quantile10":
        return quantile_bucket(rank, count, 10)
    if partition == "edge10":
        return edge_bucket(rank, count, 10)
    if partition == "side_edge5":
        return side_edge_bucket(rank, count, 5)
    raise ValueError(f"unknown partition: {partition}")


def suffix_counts(sequence: list[str], book_length: int) -> list[Counter]:
    suffix: list[Counter] = [Counter() for _ in range(len(sequence) + 1)]
    suffix[len(sequence)][0] = 1
    for index in range(len(sequence) - 1, -1, -1):
        low, high = bucket_range(sequence[index], book_length)
        for remaining_after, ways in suffix[index + 1].items():
            for length in range(low, high + 1):
                total = length + remaining_after
                if total <= book_length:
                    suffix[index][total] += ways
    return suffix


def composition_rank(sequence: list[str], lengths: list[int], book_length: int) -> tuple[int, int]:
    suffix = suffix_counts(sequence, book_length)
    total = suffix[0][book_length]
    rank = 0
    remaining = book_length
    for index, true_length in enumerate(lengths):
        low, high = bucket_range(sequence[index], book_length)
        if not low <= true_length <= high:
            raise ValueError("true length outside coarse bucket")
        for candidate in range(low, true_length):
            rank += suffix[index + 1].get(remaining - candidate, 0)
        remaining -= true_length
    if remaining != 0:
        raise ValueError("operation lengths do not sum to book length")
    if not 0 <= rank < total:
        raise ValueError("composition rank outside feasible range")
    return total, rank


def load_book_rows() -> list[dict]:
    raw_rows = json.loads(LEDGER_PATH.read_text())["ledger_rows"]
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in raw_rows:
        grouped[int(row["book"])].append(row)

    books = []
    for book, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda row: int(row["op_index"]))
        sequence = [row["type_length_symbol"] for row in rows]
        lengths = [int(row["length"]) for row in rows]
        book_length = int(rows[0]["book_length"])
        count, rank = composition_rank(sequence, lengths, book_length)
        op_count = len(rows)
        books.append(
            {
                "book": book,
                "book_length": book_length,
                "book_length_bucket": book_length_bucket(book_length),
                "book_phase": book_phase(book),
                "composition_count": count,
                "composition_bits_uniform": log2(max(1, count)),
                "composition_rank": rank,
                "first_symbol": sequence[0],
                "last_symbol": sequence[-1],
                "nontrivial": op_count > 1,
                "op_count": op_count,
                "op_count_bucket": op_count_bucket(op_count),
                "rank_fraction": 0.0 if count <= 1 else rank / (count - 1),
                "sequence": sequence,
            }
        )
    return books


@dataclass
class RankModel:
    context_name: str
    partition: str
    features: tuple[str, ...]
    counts: dict[tuple[str, ...], Counter]
    global_counts: Counter

    @property
    def vocab_size(self) -> int:
        return PARTITIONS[self.partition] if self.partition != "side_edge5" else 10


def train_model(rows: list[dict], context_name: str, partition: str) -> RankModel:
    features = CONTEXTS[context_name]
    counts: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    global_counts = Counter()
    for row in rows:
        symbol, _ = partition_symbol(partition, int(row["composition_rank"]), int(row["composition_count"]))
        counts[context(row, features)][symbol] += 1
        global_counts[symbol] += 1
    return RankModel(context_name, partition, features, dict(counts), global_counts)


def symbol_bits(model: RankModel, row: dict, symbol: str) -> float:
    selected = model.counts.get(context(row, model.features))
    if not selected:
        selected = model.global_counts
    total = sum(selected.values())
    probability = (selected.get(symbol, 0) + ALPHA) / (total + ALPHA * model.vocab_size)
    return -log2(max(probability, 1e-300))


def rank_code_bits(model: RankModel, row: dict, rank: int | None = None) -> float:
    count = int(row["composition_count"])
    if count <= 1:
        return 0.0
    actual_rank = int(row["composition_rank"] if rank is None else rank)
    symbol, width = partition_symbol(model.partition, actual_rank, count)
    return symbol_bits(model, row, symbol) + log2(width)


def score_model(model: RankModel, test_rows: list[dict]) -> dict:
    model_bits = 0.0
    uniform_bits = 0.0
    nontrivial_model_bits = 0.0
    nontrivial_uniform_bits = 0.0
    symbol_hits = 0
    edge_books = 0
    for row in test_rows:
        bits = rank_code_bits(model, row)
        uniform = float(row["composition_bits_uniform"])
        model_bits += bits
        uniform_bits += uniform
        if row["nontrivial"]:
            nontrivial_model_bits += bits
            nontrivial_uniform_bits += uniform
        symbol, _ = partition_symbol(model.partition, int(row["composition_rank"]), int(row["composition_count"]))
        selected = model.counts.get(context(row, model.features), model.global_counts)
        if selected:
            top_symbol, _ = sorted(selected.items(), key=lambda item: (-item[1], item[0]))[0]
            if top_symbol == symbol:
                symbol_hits += 1
        if int(row["composition_count"]) > 1 and int(row["composition_rank"]) in {0, int(row["composition_count"]) - 1}:
            edge_books += 1
    return {
        "edge_books": edge_books,
        "model_bits": model_bits,
        "nontrivial_model_bits": nontrivial_model_bits,
        "nontrivial_saving_bits": nontrivial_uniform_bits - nontrivial_model_bits,
        "nontrivial_uniform_bits": nontrivial_uniform_bits,
        "saving_bits": uniform_bits - model_bits,
        "symbol_top_hits": symbol_hits,
        "uniform_bits": uniform_bits,
    }


def score_random_ranks(model: RankModel, test_rows: list[dict], rng: random.Random) -> float:
    uniform_bits = sum(float(row["composition_bits_uniform"]) for row in test_rows)
    model_bits = 0.0
    for row in test_rows:
        count = int(row["composition_count"])
        rank = 0 if count <= 1 else rng.randrange(count)
        model_bits += rank_code_bits(model, row, rank)
    return uniform_bits - model_bits


def rank_distribution_summary(rows: list[dict]) -> dict:
    nontrivial = [row for row in rows if row["nontrivial"] and int(row["composition_count"]) > 1]
    edge = [
        row
        for row in nontrivial
        if int(row["composition_rank"]) in {0, int(row["composition_count"]) - 1}
    ]
    low_half = [row for row in nontrivial if row["rank_fraction"] < 0.5]
    deciles = Counter()
    for row in nontrivial:
        symbol, _ = partition_symbol("quantile10", int(row["composition_rank"]), int(row["composition_count"]))
        deciles[symbol] += 1
    return {
        "edge_books": len(edge),
        "low_half_books": len(low_half),
        "nontrivial_books": len(nontrivial),
        "quantile10_counts": dict(sorted(deciles.items())),
    }


def run_gate() -> dict:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    book_rows = load_book_rows()
    rng = random.Random(469)
    model_results = {}

    for context_name in CONTEXTS:
        for partition in PARTITIONS:
            key = f"{context_name}__{partition}"
            cutoff_rows = []
            totals = Counter()
            random_savings = [0.0 for _ in range(RANDOM_TRIALS)]
            for cutoff in CUTOFFS:
                train = [row for row in book_rows if int(row["book"]) < cutoff]
                test = [row for row in book_rows if int(row["book"]) >= cutoff]
                model = train_model(train, context_name, partition)
                scored = score_model(model, test)
                cutoff_rows.append({"cutoff": cutoff, "test_books": len(test), **scored})
                for name, value in scored.items():
                    totals[name] += value
                for trial in range(RANDOM_TRIALS):
                    random_savings[trial] += score_random_ranks(model, test, rng)
            sorted_random = sorted(random_savings)
            random_mean = sum(random_savings) / len(random_savings)
            p95 = sorted_random[int(0.95 * (len(sorted_random) - 1))]
            promoted = totals["saving_bits"] > p95 + PROMOTION_MARGIN_BITS and totals["nontrivial_saving_bits"] > 0
            weak = totals["saving_bits"] > 0 and totals["saving_bits"] > random_mean and totals["nontrivial_saving_bits"] > 0
            if promoted:
                classification = "PROMOTED_COMPOSITION_INDEX_STRUCTURE"
            elif weak:
                classification = "WEAK_COMPOSITION_INDEX_CLUE"
            else:
                classification = "COMPOSITION_INDEX_REMAINS_EXTERNAL"
            model_results[key] = {
                "classification": classification,
                "context": context_name,
                "cutoff_rows": cutoff_rows,
                "partition": partition,
                "random_saving_mean": random_mean,
                "random_saving_p95": p95,
                "totals": dict(totals),
            }

    best_key = max(
        model_results,
        key=lambda key: (
            model_results[key]["totals"]["saving_bits"],
            model_results[key]["totals"]["nontrivial_saving_bits"],
            -model_results[key]["random_saving_p95"],
        ),
    )
    promoted = [
        key
        for key, result in model_results.items()
        if result["classification"] == "PROMOTED_COMPOSITION_INDEX_STRUCTURE"
    ]
    weak = [
        key
        for key, result in model_results.items()
        if result["classification"] == "WEAK_COMPOSITION_INDEX_CLUE"
    ]

    composition_baseline = json.loads(BOOK_LEVEL_PATH.read_text())["residual_composition"]["summary"]
    if promoted:
        classification = "PROMOTED_COMPOSITION_INDEX_STRUCTURE"
    elif weak:
        classification = "WEAK_COMPOSITION_INDEX_CLUE"
    else:
        classification = "COMPOSITION_INDEX_REMAINS_EXTERNAL"

    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "best_model": best_key,
            "promoted_models": promoted,
            "row0_status": "unchanged_exogenous",
            "weak_models": weak,
        },
        "distribution_summary": rank_distribution_summary(book_rows),
        "inputs": {
            "alpha": ALPHA,
            "book_level_controller_gate": str(BOOK_LEVEL_PATH.relative_to(ROOT)),
            "composition_baseline_bits": composition_baseline["total_composition_bits"],
            "cutoffs": CUTOFFS,
            "ledger": str(LEDGER_PATH.relative_to(ROOT)),
            "promotion_margin_bits": PROMOTION_MARGIN_BITS,
            "random_trials": RANDOM_TRIALS,
        },
        "model_results": model_results,
        "plaintext_claim": False,
        "rank_rows": book_rows,
        "scope": "analysis_only_composition_index_structure",
        "translation_delta": "NONE",
    }


def write_markdown(result: dict) -> None:
    best_key = result["decision"]["best_model"]
    best = result["model_results"][best_key]
    dist = result["distribution_summary"]
    lines = [
        "# Composition Index Structure Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "The book-level controller reduced exact within-bucket lengths to one "
        "composition index per book. This gate asks whether the true index has "
        "prefix-generalizable structure or remains external payload.",
        "",
        "No target text, plaintext, semantics, row0 origin, or exact residuals are "
        "used to choose the coarse sequence.",
        "",
        "## Rank Distribution",
        "",
        f"- Nontrivial books: `{dist['nontrivial_books']}`.",
        f"- Edge ranks among nontrivial books: `{dist['edge_books']}`.",
        f"- Low-half ranks among nontrivial books: `{dist['low_half_books']}`.",
        f"- Quantile counts: `{dist['quantile10_counts']}`.",
        "",
        "## Best Prefix-Holdout Model",
        "",
        f"- Best model: `{best_key}`.",
        f"- Best model classification: `{best['classification']}`.",
        f"- Uniform composition-index bits over repeated holdouts: `{best['totals']['uniform_bits']:.3f}`.",
        f"- Model bits: `{best['totals']['model_bits']:.3f}`.",
        f"- Saving: `{best['totals']['saving_bits']:.3f}` bits.",
        f"- Nontrivial saving: `{best['totals']['nontrivial_saving_bits']:.3f}` bits.",
        f"- Random-rank saving mean: `{best['random_saving_mean']:.3f}` bits.",
        f"- Random-rank saving p95: `{best['random_saving_p95']:.3f}` bits.",
        "",
        "| Cutoff | Test Books | Uniform Bits | Model Bits | Saving | Nontrivial Saving | Edge Books | Top Symbol Hits |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in best["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['test_books']}` | `{row['uniform_bits']:.3f}` | "
            f"`{row['model_bits']:.3f}` | `{row['saving_bits']:.3f}` | "
            f"`{row['nontrivial_saving_bits']:.3f}` | `{row['edge_books']}` | "
            f"`{row['symbol_top_hits']}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
        ]
    )
    if result["classification"] == "PROMOTED_COMPOSITION_INDEX_STRUCTURE":
        lines.append(
            "The composition-index field has a promoted prefix-generalizable rank "
            "structure. This reduces a remaining book-level residual dependency, "
            "but does not change row0, plaintext, translation, or the compression bound."
        )
    elif result["classification"] == "WEAK_COMPOSITION_INDEX_CLUE":
        lines.append(
            "The true composition index shows a weak rank bias, but it does not clear "
            "the random-rank p95 plus promotion margin. Keep the composition index as "
            "an external field with a weak clue only."
        )
    else:
        lines.append(
            "The composition-index field is not promoted. The book-length constrained "
            "composition codec remains useful, but the exact index inside that "
            "composition stays external payload under current evidence."
        )
    lines.extend(
        [
            "",
            "## Remaining External Fields",
            "",
            "- coarse sequence corrections when the true sequence misses beam",
            "- book-level composition index for exact residual lengths",
            "- literal innovation tape payload and schedule",
            "- copy-hint rank stream",
            "- seed books `0..9`",
            "- `row0`",
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_composition_index_structure_gate.py](../../scripts/01_composition_index_structure_gate.py)",
            "- [01_composition_index_structure_gate.json](01_composition_index_structure_gate.json)",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    result = run_gate()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)


if __name__ == "__main__":
    main()
