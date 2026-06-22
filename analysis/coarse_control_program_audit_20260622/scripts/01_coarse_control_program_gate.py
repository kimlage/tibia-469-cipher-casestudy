#!/usr/bin/env python3
"""Test a target-free program for the coarse type:length_bucket stream.

Exact `type:length` failed as a stateful program, and length factorization split
that dependency into a coarse control stream plus fine residual innovation. This
gate asks whether the coarse stream itself can be encoded or generated from
source-free sequential state when per-book operation count is granted.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "coarse_control_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
LEDGER_PATH = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
JSON_OUT = TEST_RESULTS / "01_coarse_control_program_gate.json"
MD_OUT = TEST_RESULTS / "01_coarse_control_program_gate.md"

CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 500
ALPHA = 0.5
BEAM_WIDTHS = [1, 5, 20]
MIN_PROMOTION_SAVING_BITS = 20.0

BUCKETS = ["len_0008", "len_0016", "len_0032", "len_0064", "len_0128", "len_0256p"]
VOCAB = [f"{op_type}:{bucket}" for op_type in ["literal", "copy"] for bucket in BUCKETS]

FEATURES: dict[str, tuple[str, ...]] = {
    "global": tuple(),
    "prev_symbol": ("prev_symbol",),
    "op_pos": ("op_pos_bucket_online",),
    "remaining_ops": ("remaining_ops_bucket",),
    "book_length": ("book_length_bucket",),
    "op_count": ("op_count_bucket",),
    "prev_x_pos": ("prev_symbol", "op_pos_bucket_online"),
    "prev_x_remaining_ops": ("prev_symbol", "remaining_ops_bucket"),
    "phase_x_pos": ("book_phase", "op_pos_bucket_online"),
    "count_x_pos": ("op_count_bucket", "op_pos_bucket_online"),
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


def op_pos_bucket(op_index: int, op_count: int) -> str:
    if op_index == 0:
        return "first"
    if op_index == op_count - 1:
        return "last"
    if op_index <= 2:
        return "early"
    return "middle"


def remaining_ops_bucket(remaining_after_current: int) -> str:
    if remaining_after_current == 0:
        return "rem_ops_00"
    if remaining_after_current <= 2:
        return "rem_ops_01_02"
    if remaining_after_current <= 5:
        return "rem_ops_03_05"
    return "rem_ops_06p"


def context(row: dict, features: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(feature, "<NA>")) for feature in features)


def load_rows() -> tuple[list[dict], dict[int, list[dict]]]:
    data = json.loads(LEDGER_PATH.read_text())
    raw_rows = sorted(data["ledger_rows"], key=lambda r: (r["book"], r["op_index"]))
    by_book: dict[int, list[dict]] = defaultdict(list)
    for row in raw_rows:
        by_book[int(row["book"])].append(row)

    rows: list[dict] = []
    for book, book_rows in sorted(by_book.items()):
        op_count = len(book_rows)
        prev_symbol = "<BOS>"
        for row in book_rows:
            op_index = int(row["op_index"])
            item = dict(row)
            item["symbol"] = row["type_length_symbol"]
            item["prev_symbol"] = prev_symbol
            item["op_count"] = op_count
            item["op_count_bucket"] = op_count_bucket(op_count)
            item["op_pos_bucket_online"] = op_pos_bucket(op_index, op_count)
            item["remaining_ops_bucket"] = remaining_ops_bucket(op_count - op_index - 1)
            item["book_phase"] = book_phase(book)
            item["book_length_bucket"] = book_length_bucket(int(row["book_length"]))
            rows.append(item)
            prev_symbol = item["symbol"]
    return rows, {book: rows for book, rows in sorted(by_book.items())}


@dataclass
class Model:
    name: str
    features: tuple[str, ...]
    counts: dict[tuple[str, ...], Counter]
    global_counts: Counter


def train_model(name: str, train_rows: list[dict]) -> Model:
    features = FEATURES[name]
    counts: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    global_counts: Counter = Counter()
    for row in train_rows:
        symbol = row["symbol"]
        counts[context(row, features)][symbol] += 1
        global_counts[symbol] += 1
    return Model(name=name, features=features, counts=dict(counts), global_counts=global_counts)


def symbol_prob(model: Model, row: dict, symbol: str) -> float:
    selected = model.counts.get(context(row, model.features), model.global_counts)
    total = sum(selected.values())
    return (selected.get(symbol, 0) + ALPHA) / (total + ALPHA * len(VOCAB))


def symbol_bits(model: Model, row: dict, symbol: str | None = None) -> float:
    target = row["symbol"] if symbol is None else symbol
    return -log2(max(symbol_prob(model, row, target), 1e-300))


def score_model(model: Model, rows: list[dict], override_symbols: list[str] | None = None) -> dict:
    model_bits = 0.0
    uniform_bits = len(rows) * log2(len(VOCAB))
    top1_hits = 0
    fallback_rows = 0
    for idx, row in enumerate(rows):
        symbol = row["symbol"] if override_symbols is None else override_symbols[idx]
        model_bits += symbol_bits(model, row, symbol)
        selected = model.counts.get(context(row, model.features))
        if not selected:
            selected = model.global_counts
            fallback_rows += 1
        top_symbol = min(VOCAB, key=lambda candidate: (symbol_bits(model, row, candidate), candidate))
        if top_symbol == symbol:
            top1_hits += 1
    return {
        "fallback_rows": fallback_rows,
        "model_bits": model_bits,
        "saving_bits": uniform_bits - model_bits,
        "top1_hits": top1_hits,
        "uniform_bits": uniform_bits,
    }


def generation_row(
    *,
    book: int,
    book_length: int,
    op_count: int,
    op_index: int,
    prev_symbol: str,
) -> dict:
    return {
        "book": book,
        "book_length": book_length,
        "book_length_bucket": book_length_bucket(book_length),
        "book_phase": book_phase(book),
        "op_count": op_count,
        "op_count_bucket": op_count_bucket(op_count),
        "op_index": op_index,
        "op_pos_bucket_online": op_pos_bucket(op_index, op_count),
        "prev_symbol": prev_symbol,
        "remaining_ops_bucket": remaining_ops_bucket(op_count - op_index - 1),
        "symbol": VOCAB[0],
    }


def generate_greedy(model: Model, book_rows: list[dict]) -> list[str]:
    book = int(book_rows[0]["book"])
    book_len = int(book_rows[0]["book_length"])
    op_count = len(book_rows)
    prev = "<BOS>"
    out = []
    for op_index in range(op_count):
        row = generation_row(
            book=book, book_length=book_len, op_count=op_count, op_index=op_index, prev_symbol=prev
        )
        symbol = min(VOCAB, key=lambda candidate: (symbol_bits(model, row, candidate), candidate))
        out.append(symbol)
        prev = symbol
    return out


def generate_beam(model: Model, book_rows: list[dict], width: int) -> list[list[str]]:
    book = int(book_rows[0]["book"])
    book_len = int(book_rows[0]["book_length"])
    op_count = len(book_rows)
    beam = [(0.0, "<BOS>", [])]
    for op_index in range(op_count):
        expanded = []
        for cost, prev, seq in beam:
            row = generation_row(
                book=book, book_length=book_len, op_count=op_count, op_index=op_index, prev_symbol=prev
            )
            ranked = sorted((symbol_bits(model, row, symbol), symbol) for symbol in VOCAB)[: min(width, len(VOCAB))]
            for step_cost, symbol in ranked:
                expanded.append((cost + step_cost, symbol, seq + [symbol]))
        expanded.sort(key=lambda item: (item[0], item[2]))
        beam = expanded[:width]
    return [seq for _, _, seq in beam]


def common_prefix(left: list[str], right: list[str]) -> int:
    count = 0
    for a, b in zip(left, right):
        if a != b:
            break
        count += 1
    return count


def generation_eval(model: Model, test_rows: list[dict]) -> dict:
    by_book: dict[int, list[dict]] = defaultdict(list)
    for row in test_rows:
        by_book[int(row["book"])].append(row)

    greedy_exact = 0
    greedy_prefix_ops = 0
    beam_exact = {str(width): 0 for width in BEAM_WIDTHS}
    beam_nontrivial_exact = {str(width): 0 for width in BEAM_WIDTHS}
    beam_prefix_ops = {str(width): 0 for width in BEAM_WIDTHS}
    examples = []
    for book, rows in sorted(by_book.items()):
        rows = sorted(rows, key=lambda row: row["op_index"])
        truth = [row["symbol"] for row in rows]
        greedy = generate_greedy(model, rows)
        prefix = common_prefix(greedy, truth)
        greedy_prefix_ops += prefix
        if greedy == truth:
            greedy_exact += 1
        elif len(examples) < 6:
            examples.append({"book": book, "truth": truth, "greedy": greedy, "prefix": prefix})
        for width in BEAM_WIDTHS:
            beam = generate_beam(model, rows, width)
            if truth in beam:
                beam_exact[str(width)] += 1
                if len(truth) > 1:
                    beam_nontrivial_exact[str(width)] += 1
            beam_prefix_ops[str(width)] += max((common_prefix(seq, truth) for seq in beam), default=0)
    return {
        "beam_exact_books": beam_exact,
        "beam_nontrivial_exact_books": beam_nontrivial_exact,
        "beam_prefix_ops": beam_prefix_ops,
        "examples": examples,
        "greedy_exact_books": greedy_exact,
        "greedy_prefix_ops": greedy_prefix_ops,
        "test_books": len(by_book),
    }


def run_gate() -> dict:
    rows, _ = load_rows()
    rng = random.Random(469)
    models = {}
    for model_name in FEATURES:
        cutoff_rows = []
        total_uniform = 0.0
        total_model = 0.0
        total_saving = 0.0
        total_top1 = 0
        total_rows = 0
        random_savings = [0.0 for _ in range(RANDOM_TRIALS)]
        for cutoff in CUTOFFS:
            train_rows = [row for row in rows if int(row["book"]) < cutoff]
            test_rows = [row for row in rows if int(row["book"]) >= cutoff]
            model = train_model(model_name, train_rows)
            score = score_model(model, test_rows)
            generation = generation_eval(model, test_rows)
            total_uniform += score["uniform_bits"]
            total_model += score["model_bits"]
            total_saving += score["saving_bits"]
            total_top1 += score["top1_hits"]
            total_rows += len(test_rows)
            test_symbols = [row["symbol"] for row in test_rows]
            for trial in range(RANDOM_TRIALS):
                random_symbols = list(test_symbols)
                rng.shuffle(random_symbols)
                random_savings[trial] += score_model(model, test_rows, random_symbols)["saving_bits"]
            cutoff_rows.append(
                {
                    "cutoff": cutoff,
                    "test_ops": len(test_rows),
                    "train_ops": len(train_rows),
                    **score,
                    "generation": generation,
                }
            )
        sorted_random = sorted(random_savings)
        p95 = sorted_random[int(0.95 * (len(sorted_random) - 1))]
        p05 = sorted_random[int(0.05 * (len(sorted_random) - 1))]
        beats_random = total_saving > p95
        meaningful = total_saving > MIN_PROMOTION_SAVING_BITS
        exact_nontrivial = sum(
            row["generation"]["beam_nontrivial_exact_books"]["20"] for row in cutoff_rows
        )
        if beats_random and meaningful and exact_nontrivial > 0:
            status = "PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE"
        elif beats_random and meaningful:
            status = "PROMOTED_COARSE_CONTROL_CODEC_CLUE"
        elif beats_random:
            status = "WEAK_COARSE_CONTROL_CLUE"
        else:
            status = "REJECTED_COARSE_CONTROL_PROGRAM"
        models[model_name] = {
            "beats_random_p95": beats_random,
            "cutoff_rows": cutoff_rows,
            "features": FEATURES[model_name],
            "meaningful_saving": meaningful,
            "observed_model_bits": total_model,
            "observed_saving_bits": total_saving,
            "observed_top1_hits": total_top1,
            "observed_total_rows": total_rows,
            "observed_uniform_bits": total_uniform,
            "random_saving_p05": p05,
            "random_saving_p95": p95,
            "status": status,
        }

    best_model = min(models.items(), key=lambda item: item[1]["observed_model_bits"])[0]
    promoted = [
        name
        for name, model in models.items()
        if model["status"]
        in {"PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE", "PROMOTED_COARSE_CONTROL_CODEC_CLUE"}
    ]
    generator_promoted = [
        name for name, model in models.items() if model["status"] == "PROMOTED_COARSE_CONTROL_PROGRAM_CANDIDATE"
    ]
    if generator_promoted:
        classification = "coarse_control_program_candidate"
    elif promoted:
        classification = "coarse_control_codec_clue_not_generator"
    else:
        classification = "coarse_control_program_not_promoted"

    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "best_model": best_model,
            "generator_promoted": generator_promoted,
            "promoted_models": promoted,
            "row0_status": "unchanged_exogenous",
        },
        "inputs": {
            "cutoffs": CUTOFFS,
            "granted_dependencies": ["book_length", "op_count"],
            "ledger": str(LEDGER_PATH.relative_to(ROOT)),
            "random_trials": RANDOM_TRIALS,
            "vocab": VOCAB,
        },
        "models": models,
        "plaintext_claim": False,
        "scope": "analysis_only_target_free_coarse_type_length_bucket_control",
        "translation_delta": "NONE",
    }


def write_markdown(result: dict) -> None:
    best_name = result["decision"]["best_model"]
    best = result["models"][best_name]
    lines = [
        "# Coarse Control Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether the coarse `type:length_bucket` control stream can be encoded or "
        "generated from target-free sequential state after granting per-book operation "
        "count. This follows the length factor audit: exact length is no longer treated "
        "as one symbol.",
        "",
        "## Model Summary",
        "",
        "| Model | Features | Bits | Saving | Random p95 | Top1 Hits | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, model in sorted(result["models"].items()):
        lines.append(
            f"| `{name}` | `{'+'.join(model['features']) or 'global'}` | "
            f"`{model['observed_model_bits']:.3f}` | `{model['observed_saving_bits']:.3f}` | "
            f"`{model['random_saving_p95']:.3f}` | "
            f"`{model['observed_top1_hits']}/{model['observed_total_rows']}` | `{model['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Best Model",
            "",
            f"- Best model: `{best_name}`.",
            f"- Best model bits: `{best['observed_model_bits']:.3f}`.",
            f"- Saving vs uniform coarse control: `{best['observed_saving_bits']:.3f}`.",
            f"- Random p95 saving: `{best['random_saving_p95']:.3f}`.",
            f"- Promoted models: `{result['decision']['promoted_models']}`.",
            f"- Generator-promoted models: `{result['decision']['generator_promoted']}`.",
            "",
            "## Generation Check For Best Model",
            "",
            "| Cutoff | Test Books | Greedy Exact | Beam20 Exact | Beam20 Nontrivial | Greedy Prefix Ops |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in best["cutoff_rows"]:
        generation = row["generation"]
        lines.append(
            f"| `{row['cutoff']}` | `{generation['test_books']}` | `{generation['greedy_exact_books']}` | "
            f"`{generation['beam_exact_books']['20']}` | `{generation['beam_nontrivial_exact_books']['20']}` | "
            f"`{generation['greedy_prefix_ops']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
        ]
    )
    if result["classification"] == "coarse_control_program_candidate":
        lines.append(
            "A coarse control program candidate is promoted: the stream beats controls "
            "and generates at least one nontrivial held-out coarse sequence in beam."
        )
    elif result["classification"] == "coarse_control_codec_clue_not_generator":
        lines.append(
            "A coarse control codec clue is promoted, but not a generator. The stream "
            "has prefix-holdout structure, yet exact coarse book generation remains "
            "insufficient."
        )
    else:
        lines.append(
            "No coarse control program is promoted. The bucketed representation alone "
            "does not become a reliable source-free controller under these features."
        )
    lines.extend(
        [
            "",
            "`row0`, translation, plaintext, and the compression bound remain unchanged.",
            "",
            "## Remaining External Fields",
            "",
            "- `type:length_bucket` control stream, unless covered only as a codec clue",
            "- within-bucket length residual innovation tape",
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
    best = result["models"][result["decision"]["best_model"]]
    print(
        json.dumps(
            {
                "best_model": result["decision"]["best_model"],
                "classification": result["classification"],
                "observed_saving": best["observed_saving_bits"],
                "promoted_models": result["decision"]["promoted_models"],
                "generator_promoted": result["decision"]["generator_promoted"],
                "report": str(MD_OUT.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
