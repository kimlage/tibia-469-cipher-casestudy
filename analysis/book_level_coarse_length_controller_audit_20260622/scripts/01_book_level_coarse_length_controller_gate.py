#!/usr/bin/env python3
"""Book-level coarse length controller audit.

This gate integrates the recent factorization:
- exact type:length failed as an observable program;
- type:length_bucket has a coarse-control candidate when op_count is granted;
- within-bucket length residuals remain external.

It tests whether book_length can constrain the residuals and whether a latent
op_count + coarse controller can keep the true coarse sequence in beam without
using target text or exact residuals to select the sequence.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "book_level_coarse_length_controller_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
LEDGER_PATH = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
JSON_OUT = TEST_RESULTS / "01_book_level_coarse_length_controller_gate.json"
MD_OUT = TEST_RESULTS / "01_book_level_coarse_length_controller_gate.md"

CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 100
MAX_OPCOUNT = 16
SEQ_BEAM_WIDTH = 12
BOOK_BEAM_WIDTH = 30
ALPHA = 0.5

BUCKETS = ["len_0008", "len_0016", "len_0032", "len_0064", "len_0128", "len_0256p"]
VOCAB = [f"{kind}:{bucket}" for kind in ["literal", "copy"] for bucket in BUCKETS]
BUCKET_RANGES = {
    "len_0008": (1, 8),
    "len_0016": (9, 16),
    "len_0032": (17, 32),
    "len_0064": (33, 64),
    "len_0128": (65, 128),
    "len_0256p": (129, None),
}

OPCOUNT_FEATURES = {
    "global": tuple(),
    "book_length": ("book_length_bucket",),
    "phase_x_length": ("book_phase", "book_length_bucket"),
}

COARSE_FEATURES = {
    "op_count": ("op_count_bucket",),
    "count_x_pos": ("op_count_bucket", "op_pos_bucket_online"),
}


def log2(value: float) -> float:
    return math.log2(value)


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / math.log(2)


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


def op_pos_bucket(index: int, count: int) -> str:
    if index == 0:
        return "first"
    if index == count - 1:
        return "last"
    if index <= 2:
        return "early"
    return "middle"


def remaining_ops_bucket(remaining_after: int) -> str:
    if remaining_after == 0:
        return "rem_ops_00"
    if remaining_after <= 2:
        return "rem_ops_01_02"
    if remaining_after <= 5:
        return "rem_ops_03_05"
    return "rem_ops_06p"


def bucket_range(symbol: str, book_length: int) -> tuple[int, int]:
    _, bucket = symbol.split(":", 1)
    low, high = BUCKET_RANGES[bucket]
    if high is None:
        high = book_length
    return low, min(high, book_length)


def context(row: dict, features: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(feature, "<NA>")) for feature in features)


def load_books() -> dict[int, list[dict]]:
    rows = json.loads(LEDGER_PATH.read_text())["ledger_rows"]
    by_book: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_book[int(row["book"])].append(row)

    books = {}
    for book, raw_rows in sorted(by_book.items()):
        raw_rows = sorted(raw_rows, key=lambda row: row["op_index"])
        count = len(raw_rows)
        prev = "<BOS>"
        enriched = []
        for row in raw_rows:
            index = int(row["op_index"])
            item = dict(row)
            item["symbol"] = row["type_length_symbol"]
            item["book_phase"] = book_phase(book)
            item["book_length_bucket"] = book_length_bucket(int(row["book_length"]))
            item["op_count"] = count
            item["op_count_bucket"] = op_count_bucket(count)
            item["op_pos_bucket_online"] = op_pos_bucket(index, count)
            item["remaining_ops_bucket"] = remaining_ops_bucket(count - index - 1)
            item["prev_symbol"] = prev
            low, high = bucket_range(item["symbol"], int(row["book_length"]))
            item["bucket_low"] = low
            item["bucket_high"] = high
            item["bucket_width"] = high - low + 1
            item["length_residual_bits_uniform"] = log2(item["bucket_width"])
            enriched.append(item)
            prev = item["symbol"]
        books[book] = enriched
    return books


def count_compositions(sequence: list[str], book_length: int) -> int:
    # Count residual assignments within each bucket whose lengths sum to book_length.
    reachable = Counter({0: 1})
    for symbol in sequence:
        low, high = bucket_range(symbol, book_length)
        next_reachable = Counter()
        for current_sum, ways in reachable.items():
            for length in range(low, high + 1):
                total = current_sum + length
                if total <= book_length:
                    next_reachable[total] += ways
        reachable = next_reachable
        if not reachable:
            return 0
    return reachable[book_length]


def sequence_feasible(sequence: list[str], book_length: int) -> bool:
    low_sum = 0
    high_sum = 0
    for symbol in sequence:
        low, high = bucket_range(symbol, book_length)
        low_sum += low
        high_sum += high
    return low_sum <= book_length <= high_sum


def residual_uniform_bits(rows: list[dict]) -> float:
    return sum(float(row["length_residual_bits_uniform"]) for row in rows)


def residual_composition_audit(books: dict[int, list[dict]]) -> dict:
    rows = []
    total_uniform = 0.0
    total_composition = 0.0
    trivial_books = 0
    nontrivial_books = 0
    for book, book_rows in sorted(books.items()):
        sequence = [row["symbol"] for row in book_rows]
        length = int(book_rows[0]["book_length"])
        ways = count_compositions(sequence, length)
        composition_bits = log2(max(1, ways))
        uniform_bits = residual_uniform_bits(book_rows)
        total_uniform += uniform_bits
        total_composition += composition_bits
        if len(book_rows) == 1:
            trivial_books += 1
        else:
            nontrivial_books += 1
        rows.append(
            {
                "book": book,
                "composition_bits": composition_bits,
                "composition_count": ways,
                "op_count": len(book_rows),
                "saving_bits": uniform_bits - composition_bits,
                "trivial": len(book_rows) == 1,
                "uniform_bits": uniform_bits,
            }
        )
    return {
        "classification": "PROMOTED_RESIDUAL_COMPOSITION_CODEC" if total_uniform > total_composition else "AUDIT_ONLY",
        "rows": rows,
        "summary": {
            "books": len(books),
            "nontrivial_books": nontrivial_books,
            "saving_bits": total_uniform - total_composition,
            "total_composition_bits": total_composition,
            "total_uniform_bits": total_uniform,
            "trivial_books": trivial_books,
        },
    }


@dataclass
class CountModel:
    name: str
    features: tuple[str, ...]
    counts: dict[tuple[str, ...], Counter]
    global_counts: Counter


@dataclass
class CoarseModel:
    name: str
    features: tuple[str, ...]
    counts: dict[tuple[str, ...], Counter]
    global_counts: Counter


def train_count_model(name: str, train_books: dict[int, list[dict]]) -> CountModel:
    counts: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    global_counts = Counter()
    features = OPCOUNT_FEATURES[name]
    for rows in train_books.values():
        value = len(rows)
        row = rows[0]
        counts[context(row, features)][value] += 1
        global_counts[value] += 1
    return CountModel(name, features, dict(counts), global_counts)


def train_coarse_model(name: str, train_books: dict[int, list[dict]]) -> CoarseModel:
    counts: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    global_counts = Counter()
    features = COARSE_FEATURES[name]
    for rows in train_books.values():
        for row in rows:
            counts[context(row, features)][row["symbol"]] += 1
            global_counts[row["symbol"]] += 1
    return CoarseModel(name, features, dict(counts), global_counts)


def count_prob(model: CountModel, row: dict, value: int) -> float:
    selected = model.counts.get(context(row, model.features), model.global_counts)
    total = sum(selected.values())
    return (selected.get(value, 0) + ALPHA) / (total + ALPHA * MAX_OPCOUNT)


def symbol_prob(model: CoarseModel, row: dict, symbol: str) -> float:
    selected = model.counts.get(context(row, model.features), model.global_counts)
    total = sum(selected.values())
    return (selected.get(symbol, 0) + ALPHA) / (total + ALPHA * len(VOCAB))


def candidate_row(book: int, book_length: int, op_count: int, index: int, prev: str) -> dict:
    return {
        "book": book,
        "book_length": book_length,
        "book_length_bucket": book_length_bucket(book_length),
        "book_phase": book_phase(book),
        "op_count": op_count,
        "op_count_bucket": op_count_bucket(op_count),
        "op_index": index,
        "op_pos_bucket_online": op_pos_bucket(index, op_count),
        "prev_symbol": prev,
        "remaining_ops_bucket": remaining_ops_bucket(op_count - index - 1),
        "symbol": VOCAB[0],
    }


def generate_sequences(model: CoarseModel, book: int, book_length: int, op_count: int) -> list[tuple[float, list[str]]]:
    beam = [(0.0, "<BOS>", [])]
    for index in range(op_count):
        expanded = []
        for cost, prev, sequence in beam:
            row = candidate_row(book, book_length, op_count, index, prev)
            ranked = sorted(
                (-log2(max(symbol_prob(model, row, symbol), 1e-300)), symbol) for symbol in VOCAB
            )[: min(SEQ_BEAM_WIDTH, len(VOCAB))]
            for symbol_cost, symbol in ranked:
                expanded.append((cost + symbol_cost, symbol, sequence + [symbol]))
        expanded.sort(key=lambda item: (item[0], item[2]))
        beam = expanded[:SEQ_BEAM_WIDTH]
    return [(cost, sequence) for cost, _, sequence in beam]


def decode_book(count_model: CountModel, coarse_model: CoarseModel, book: int, rows: list[dict]) -> list[dict]:
    length = int(rows[0]["book_length"])
    base = rows[0]
    candidates = []
    for op_count in range(1, MAX_OPCOUNT + 1):
        count_bits = -log2(max(count_prob(count_model, base, op_count), 1e-300))
        for coarse_bits, sequence in generate_sequences(coarse_model, book, length, op_count):
            if not sequence_feasible(sequence, length):
                continue
            candidates.append(
                {
                    "bits": count_bits + coarse_bits,
                    "coarse_bits": coarse_bits,
                    "count_bits": count_bits,
                    "op_count": op_count,
                    "sequence": sequence,
                }
            )
    candidates.sort(key=lambda item: (item["bits"], item["op_count"], item["sequence"]))
    return candidates[:BOOK_BEAM_WIDTH]


def evaluate_pair(count_model: CountModel, coarse_model: CoarseModel, test_books: dict[int, list[dict]]) -> dict:
    metrics = Counter()
    examples = []
    correction_miss_bits = 0.0
    hit_rank_bits = 0.0
    composition_bits = 0.0
    residual_uniform = 0.0
    for book, rows in sorted(test_books.items()):
        true_sequence = [row["symbol"] for row in rows]
        true_count = len(rows)
        decoded = decode_book(count_model, coarse_model, book, rows)
        metrics["test_books"] += 1
        if true_count > 1:
            metrics["nontrivial_books"] += 1
        residual_uniform += residual_uniform_bits(rows)
        composition_bits += log2(max(1, count_compositions(true_sequence, int(rows[0]["book_length"]))))
        sequence_hit_idx = None
        count_hit = False
        for idx, item in enumerate(decoded):
            if item["op_count"] == true_count:
                count_hit = True
            if item["op_count"] == true_count and item["sequence"] == true_sequence:
                sequence_hit_idx = idx
                break
        if count_hit:
            metrics["exact_opcount_in_beam"] += 1
        if decoded and decoded[0]["op_count"] == true_count:
            metrics["top1_exact_opcount"] += 1
        if sequence_hit_idx is not None:
            metrics["exact_sequence_in_beam"] += 1
            if true_count > 1:
                metrics["nontrivial_exact_sequence_in_beam"] += 1
            hit_rank_bits += log2(sequence_hit_idx + 1)
        else:
            # Correction payload: exact op_count plus exact coarse sequence if beam misses.
            correction_miss_bits += log2(MAX_OPCOUNT) + len(rows) * log2(len(VOCAB))
            if len(examples) < 6:
                examples.append(
                    {
                        "book": book,
                        "true_count": true_count,
                        "top_count": decoded[0]["op_count"] if decoded else None,
                        "true_sequence": true_sequence,
                        "top_sequence": decoded[0]["sequence"] if decoded else None,
                    }
                )
    metrics["correction_miss_bits"] = correction_miss_bits
    metrics["hit_rank_bits"] = hit_rank_bits
    metrics["composition_bits"] = composition_bits
    metrics["residual_uniform_bits"] = residual_uniform
    return {"examples": examples, "metrics": dict(metrics)}


def score_true_coarse_with_granted_count(model: CoarseModel, books: dict[int, list[dict]]) -> float:
    bits = 0.0
    for rows in books.values():
        for row in rows:
            bits += -log2(max(symbol_prob(model, row, row["symbol"]), 1e-300))
    return bits


def run_gate() -> dict:
    books = load_books()
    residual = residual_composition_audit(books)
    rng = random.Random(469)
    pair_results = {}
    integrated_rows = []

    for count_name in OPCOUNT_FEATURES:
        for coarse_name in COARSE_FEATURES:
            key = f"{count_name}__{coarse_name}"
            cutoff_rows = []
            totals = Counter()
            random_exact_totals = [0 for _ in range(RANDOM_TRIALS)]
            for cutoff in CUTOFFS:
                train = {book: rows for book, rows in books.items() if book < cutoff}
                test = {book: rows for book, rows in books.items() if book >= cutoff}
                count_model = train_count_model(count_name, train)
                coarse_model = train_coarse_model(coarse_name, train)
                evaluated = evaluate_pair(count_model, coarse_model, test)
                metrics = evaluated["metrics"]
                cutoff_rows.append({"cutoff": cutoff, **metrics, "examples": evaluated["examples"]})
                for name, value in metrics.items():
                    if isinstance(value, (int, float)):
                        totals[name] += value

                decoded_by_book = {
                    book: decode_book(count_model, coarse_model, book, rows) for book, rows in test.items()
                }
                payloads = [(len(rows), [row["symbol"] for row in rows]) for rows in test.values()]
                for trial in range(RANDOM_TRIALS):
                    shuffled = list(payloads)
                    rng.shuffle(shuffled)
                    exact = 0
                    for (book, _), (fake_count, fake_sequence) in zip(test.items(), shuffled):
                        if any(
                            item["op_count"] == fake_count and item["sequence"] == fake_sequence
                            for item in decoded_by_book[book]
                        ):
                            exact += 1
                    random_exact_totals[trial] += exact

                opcount_uniform = len(test) * log2(MAX_OPCOUNT)
                coarse_uniform = sum(len(rows) * log2(len(VOCAB)) for rows in test.values())
                residual_uniform = metrics["residual_uniform_bits"]
                residual_composition = metrics["composition_bits"]
                granted_coarse_bits = score_true_coarse_with_granted_count(coarse_model, test)
                latent_correction = metrics["hit_rank_bits"] + metrics["correction_miss_bits"]
                integrated_rows.append(
                    {
                        "coarse_model": coarse_name,
                        "count_model": count_name,
                        "cutoff": cutoff,
                        "latent_beam_plus_composition": latent_correction + residual_composition,
                        "opcount_coarse_separated_uniform_residual": opcount_uniform + coarse_uniform + residual_uniform,
                        "opcount_granted_coarse_model_plus_composition": granted_coarse_bits + residual_composition,
                    }
                )
            sorted_random = sorted(random_exact_totals)
            p95 = sorted_random[int(0.95 * (len(sorted_random) - 1))]
            promoted = totals["exact_sequence_in_beam"] > p95 and totals["nontrivial_exact_sequence_in_beam"] > 0
            pair_results[key] = {
                "classification": "PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE" if promoted else "REJECTED_LATENT_OPCOUNT_ROUTE",
                "coarse_model": coarse_name,
                "count_model": count_name,
                "cutoff_rows": cutoff_rows,
                "random_exact_sequence_p95": p95,
                "totals": dict(totals),
            }

    best_pair = max(
        pair_results,
        key=lambda key: (
            pair_results[key]["totals"]["exact_sequence_in_beam"],
            pair_results[key]["totals"]["exact_opcount_in_beam"],
            -pair_results[key]["random_exact_sequence_p95"],
        ),
    )
    promoted_pairs = [
        key
        for key, result in pair_results.items()
        if result["classification"] == "PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE"
    ]
    integrated_summary = {}
    best_rows = [
        row for row in integrated_rows if f"{row['count_model']}__{row['coarse_model']}" == best_pair
    ]
    for key in [
        "latent_beam_plus_composition",
        "opcount_coarse_separated_uniform_residual",
        "opcount_granted_coarse_model_plus_composition",
    ]:
        integrated_summary[key] = sum(row[key] for row in best_rows)

    if promoted_pairs and residual["classification"] == "PROMOTED_RESIDUAL_COMPOSITION_CODEC":
        classification = "PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE"
    elif residual["classification"] == "PROMOTED_RESIDUAL_COMPOSITION_CODEC":
        classification = "PROMOTED_RESIDUAL_COMPOSITION_CODEC"
    elif promoted_pairs:
        classification = "WEAK_BOOK_LENGTH_CONSTRAINT_CLUE"
    else:
        classification = "REJECTED_LATENT_OPCOUNT_ROUTE"

    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "best_pair": best_pair,
            "promoted_pairs": promoted_pairs,
            "row0_status": "unchanged_exogenous",
        },
        "inputs": {
            "book_beam_width": BOOK_BEAM_WIDTH,
            "cutoffs": CUTOFFS,
            "ledger": str(LEDGER_PATH.relative_to(ROOT)),
            "max_opcount": MAX_OPCOUNT,
            "random_trials": RANDOM_TRIALS,
            "seq_beam_width": SEQ_BEAM_WIDTH,
        },
        "integrated_cost": {"best_pair_rows": best_rows, "summary": integrated_summary},
        "pair_results": pair_results,
        "plaintext_claim": False,
        "residual_composition": residual,
        "scope": "analysis_only_book_level_coarse_length_controller",
        "translation_delta": "NONE",
    }


def write_markdown(result: dict) -> None:
    residual = result["residual_composition"]["summary"]
    best_key = result["decision"]["best_pair"]
    best = result["pair_results"][best_key]
    integrated = result["integrated_cost"]["summary"]
    lines = [
        "# Book-Level Coarse Length Controller Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test a book-level controller that links known `book_length`, latent `op_count`, "
        "coarse `type:length_bucket` sequence, and within-bucket residual composition. "
        "No target text, plaintext, semantics, row0 origin, or exact residuals are used "
        "to choose the coarse sequence.",
        "",
        "## A. Book-Length Constrained Residual Composition",
        "",
        f"- Books: `{residual['books']}` (`{residual['trivial_books']}` trivial, `{residual['nontrivial_books']}` nontrivial).",
        f"- Independent uniform residual bits: `{residual['total_uniform_bits']:.3f}`.",
        f"- Composition-index bits after true coarse sequence and book_length: `{residual['total_composition_bits']:.3f}`.",
        f"- Saving: `{residual['saving_bits']:.3f}` bits.",
        f"- Classification: `{result['residual_composition']['classification']}`.",
        "",
        "## B. Latent Op-Count Coarse Beam",
        "",
        f"- Best pair: `{best_key}`.",
        f"- Best pair classification: `{best['classification']}`.",
        f"- Exact op_count in beam: `{best['totals']['exact_opcount_in_beam']}/{best['totals']['test_books']}`.",
        f"- Exact coarse sequence in beam: `{best['totals']['exact_sequence_in_beam']}/{best['totals']['test_books']}`.",
        f"- Nontrivial exact coarse sequences: `{best['totals']['nontrivial_exact_sequence_in_beam']}`.",
        f"- Same-multiset shuffled exact-sequence p95: `{best['random_exact_sequence_p95']}`.",
        f"- Promoted pairs: `{result['decision']['promoted_pairs']}`.",
        "",
        "| Cutoff | Test Books | OpCount In Beam | Sequence In Beam | Nontrivial Sequence | Top1 OpCount | Top1 Sequence |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in best["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row.get('test_books', 0)}` | `{row.get('exact_opcount_in_beam', 0)}` | "
            f"`{row.get('exact_sequence_in_beam', 0)}` | `{row.get('nontrivial_exact_sequence_in_beam', 0)}` | "
            f"`{row.get('top1_exact_opcount', 0)}` | `{row.get('top1_exact_sequence', 0)}` |"
        )

    lines.extend(
        [
            "",
            "## C. Integrated Book-Level Cost",
            "",
            "| Model | Bits |",
            "| --- | ---: |",
            f"| op_count + coarse sequence separated, uniform residual | `{integrated['opcount_coarse_separated_uniform_residual']:.3f}` |",
            f"| op_count granted coarse model + residual composition index | `{integrated['opcount_granted_coarse_model_plus_composition']:.3f}` |",
            f"| latent op_count beam + residual composition/corrections | `{integrated['latent_beam_plus_composition']:.3f}` |",
            "",
            "## Decision",
            "",
        ]
    )
    if result["classification"] == "PROMOTED_BOOK_LEVEL_CONTROLLER_CANDIDATE":
        lines.append(
            "A book-level controller candidate is promoted: book-length constrained residual "
            "composition reduces the residual dependency, and the latent op_count coarse "
            "beam keeps true coarse sequences above same-multiset controls."
        )
    elif result["classification"] == "PROMOTED_RESIDUAL_COMPOSITION_CODEC":
        lines.append(
            "The residual composition codec is promoted, but the latent op_count coarse route "
            "is not. This reduces the fine residual field while op_count remains external."
        )
    elif result["classification"] == "WEAK_BOOK_LENGTH_CONSTRAINT_CLUE":
        lines.append(
            "The book-level route has a beam clue, but it is not enough to reduce all external "
            "fields. Treat it as weak controller evidence."
        )
    else:
        lines.append(
            "The latent op_count route is rejected under these controls; only audit-only "
            "book-length constraints remain."
        )
    lines.extend(
        [
            "",
            "`row0`, translation, plaintext, and the compression bound remain unchanged.",
            "",
            "## Remaining External Fields",
            "",
            "- per-book op_count if latent beam is not enough to remove it",
            "- coarse sequence corrections when the true sequence misses beam",
            "- literal innovation tape payload and schedule",
            "- copy-hint rank stream",
            "- seed books `0..9`",
            "- `row0`",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = run_gate()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    best = result["pair_results"][result["decision"]["best_pair"]]
    print(
        json.dumps(
            {
                "best_pair": result["decision"]["best_pair"],
                "classification": result["classification"],
                "exact_sequence_in_beam": best["totals"]["exact_sequence_in_beam"],
                "promoted_pairs": result["decision"]["promoted_pairs"],
                "residual_saving_bits": result["residual_composition"]["summary"]["saving_bits"],
                "report": str(MD_OUT.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
