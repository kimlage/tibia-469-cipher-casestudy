#!/usr/bin/env python3
"""Paid-control context payload codec gate.

Recent residual-mode tests showed that new book-mode headers are too expensive.
This gate tests only contexts already present in the executable decoder ledger:
coarse type:length bucket, operation position, book length/op-count classes,
and combinations of those paid/derived fields.

Targets:

- literal payload digits;
- copy-hint rank buckets;
- composition-index quantile buckets.

This is a payload/context codec audit, not a translation or generator claim.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "paid_control_context_payload_codec_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

UNIFIED_TAPE_LEDGER = (
    ROOT
    / "analysis"
    / "minimal_external_tape_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_external_tape_ledger.json"
)
RESIDUAL_BURDEN_GATE = (
    ROOT
    / "analysis"
    / "residual_burden_cross_prediction_audit_20260622"
    / "reports"
    / "test_results"
    / "01_residual_burden_cross_prediction_gate.json"
)
FAMILY_HOLDOUT = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "08_recipe_reparse_family_holdout.json"
)

JSON_OUT = TEST_RESULTS / "01_paid_control_context_payload_codec_gate.json"
MD_OUT = TEST_RESULTS / "01_paid_control_context_payload_codec_gate.md"
FINAL_OUT = FRONT / "reports" / "final_paid_control_context_payload_codec_audit.md"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
ALPHA = 0.5
RANDOM_SEED = 46920260622 + 10
RANDOM_TRIALS = 50
DIGITS = "0123456789"
FEATURES = [
    "global",
    "coarse",
    "op_pos",
    "book_length",
    "op_count",
    "coarse_x_pos",
    "coarse_x_book_length",
]
LITERAL_FEATURES = FEATURES + ["prev_digit", "coarse_x_prev_digit"]


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
    if data.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")
    decision = data.get("decision", {})
    if decision.get("row0_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 status")


def bucket_count(value: int, cuts: list[int], prefix: str) -> str:
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut}"
    return f"{prefix}_gt_{cuts[-1]}"


def quantile_bucket(value: float, buckets: int, prefix: str) -> str:
    if value <= 0:
        idx = 0
    elif value >= 1:
        idx = buckets - 1
    else:
        idx = min(buckets - 1, int(value * buckets))
    return f"{prefix}_{idx:02d}"


def load_rows() -> list[dict[str, Any]]:
    ledger = load_json(UNIFIED_TAPE_LEDGER)
    assert_boundary("unified_external_tape_ledger", ledger)
    burden = load_json(RESIDUAL_BURDEN_GATE)
    assert_boundary("residual_burden_cross_prediction_gate", burden)
    out = []
    for row in ledger["ledger_rows"]:
        item = dict(row)
        item["book"] = int(row["book"])
        item["book_op_count_bucket"] = bucket_count(int(row["book_op_count"]), [1, 2, 4, 8], "ops")
        item["composition_quantile10"] = quantile_bucket(float(row["composition_rank_fraction"]), 10, "compq")
        out.append(item)
    return out


def load_family_splits(books: set[int]) -> list[dict[str, Any]]:
    if not FAMILY_HOLDOUT.exists():
        return []
    out = []
    for row in load_json(FAMILY_HOLDOUT).get("rows", []):
        test = {int(book) for book in row.get("test_books", []) if int(book) in books}
        train = books - test
        if train and test:
            out.append({"label": f"family_{row['label']}", "split_type": "family", "train": train, "test": test})
    return out


def split_specs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    books = {row["book"] for row in rows}
    specs = []
    for cutoff in PREFIX_CUTOFFS:
        train = {book for book in books if book < cutoff}
        test = {book for book in books if book >= cutoff}
        if train and test:
            specs.append({"label": f"prefix_{cutoff}", "split_type": "prefix", "train": train, "test": test})
    specs.extend(load_family_splits(books))
    return specs


def feature_value(row: dict[str, Any], feature: str, prev_digit: str = "BOS") -> str:
    if feature == "global":
        return "global"
    if feature == "coarse":
        return row["coarse_type_length_bucket"]
    if feature == "op_pos":
        return row["op_pos_bucket"]
    if feature == "book_length":
        return row["book_length_bucket"]
    if feature == "op_count":
        return row["book_op_count_bucket"]
    if feature == "coarse_x_pos":
        return f"{row['coarse_type_length_bucket']}|{row['op_pos_bucket']}"
    if feature == "coarse_x_book_length":
        return f"{row['coarse_type_length_bucket']}|{row['book_length_bucket']}"
    if feature == "prev_digit":
        return prev_digit
    if feature == "coarse_x_prev_digit":
        return f"{row['coarse_type_length_bucket']}|{prev_digit}"
    raise KeyError(feature)


def code_symbol(symbol: str, counts: Counter[str], alphabet: list[str]) -> float:
    total = sum(counts.values())
    probability = (counts.get(symbol, 0) + ALPHA) / (total + ALPHA * len(alphabet))
    return -math.log2(probability)


def train_counts(pairs: list[tuple[str, str]]) -> tuple[Counter[str], dict[str, Counter[str]]]:
    global_counts: Counter[str] = Counter()
    context_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for context, symbol in pairs:
        global_counts[symbol] += 1
        context_counts[context][symbol] += 1
    return global_counts, context_counts


def literal_pairs(rows: list[dict[str, Any]], books: set[int], feature: str) -> list[tuple[str, str]]:
    pairs = []
    for row in rows:
        if row["book"] not in books:
            continue
        payload = row.get("literal_payload")
        if not payload:
            continue
        prev = "BOS"
        for digit in payload:
            pairs.append((feature_value(row, feature, prev), digit))
            prev = digit
    return pairs


def copy_hint_pairs(rows: list[dict[str, Any]], books: set[int], feature: str) -> list[tuple[str, str]]:
    pairs = []
    for row in rows:
        if row["book"] not in books:
            continue
        bucket = row.get("copy_hint_rank_bucket")
        if bucket is not None:
            pairs.append((feature_value(row, feature), bucket))
    return pairs


def composition_pairs(rows: list[dict[str, Any]], books: set[int], feature: str) -> list[tuple[str, str]]:
    seen_books = set()
    pairs = []
    for row in rows:
        if row["book"] not in books or row["book"] in seen_books:
            continue
        seen_books.add(row["book"])
        if int(row["composition_count"]) > 1:
            pairs.append((feature_value(row, feature), row["composition_quantile10"]))
    return pairs


TARGETS = {
    "literal_payload_digits": {
        "alphabet": list(DIGITS),
        "features": LITERAL_FEATURES,
        "pair_fn": literal_pairs,
    },
    "copy_hint_rank_bucket": {
        "alphabet": None,
        "features": FEATURES,
        "pair_fn": copy_hint_pairs,
    },
    "composition_quantile10": {
        "alphabet": None,
        "features": FEATURES,
        "pair_fn": composition_pairs,
    },
}


def infer_alphabet(rows: list[dict[str, Any]], target: str) -> list[str]:
    config = TARGETS[target]
    if config["alphabet"] is not None:
        return config["alphabet"]
    values = set()
    for _, symbol in config["pair_fn"](rows, {row["book"] for row in rows}, "global"):
        values.add(symbol)
    return sorted(values)


def score_pairs(train_pairs: list[tuple[str, str]], test_pairs: list[tuple[str, str]], alphabet: list[str]) -> float:
    global_counts, context_counts = train_counts(train_pairs)
    bits = 0.0
    for context, symbol in test_pairs:
        bits += code_symbol(symbol, context_counts.get(context, global_counts), alphabet)
    return bits


def loo_feature_score(rows: list[dict[str, Any]], train_books: set[int], target: str, feature: str, alphabet: list[str]) -> float:
    if len(train_books) < 2:
        return float("inf")
    pair_fn = TARGETS[target]["pair_fn"]
    bits = 0.0
    for heldout in sorted(train_books):
        subtrain = set(train_books) - {heldout}
        train_pairs = pair_fn(rows, subtrain, feature)
        test_pairs = pair_fn(rows, {heldout}, feature)
        if test_pairs:
            bits += score_pairs(train_pairs, test_pairs, alphabet)
    return bits + math.log2(len(TARGETS[target]["features"]))


def select_feature(rows: list[dict[str, Any]], train_books: set[int], target: str, alphabet: list[str]) -> dict[str, Any]:
    candidates = [
        {
            "feature": feature,
            "loo_bits": loo_feature_score(rows, train_books, target, feature, alphabet),
        }
        for feature in TARGETS[target]["features"]
    ]
    return min(candidates, key=lambda item: (item["loo_bits"], item["feature"]))


def score_split(rows: list[dict[str, Any]], split: dict[str, Any], target: str, alphabet: list[str]) -> dict[str, Any]:
    selected = select_feature(rows, split["train"], target, alphabet)
    pair_fn = TARGETS[target]["pair_fn"]
    global_train = pair_fn(rows, split["train"], "global")
    global_test = pair_fn(rows, split["test"], "global")
    feature_train = pair_fn(rows, split["train"], selected["feature"])
    feature_test = pair_fn(rows, split["test"], selected["feature"])
    global_bits = score_pairs(global_train, global_test, alphabet)
    feature_bits = score_pairs(feature_train, feature_test, alphabet) + math.log2(len(TARGETS[target]["features"]))
    return {
        "feature": selected["feature"],
        "feature_bits": feature_bits,
        "global_bits": global_bits,
        "label": split["label"],
        "saving_bits": global_bits - feature_bits,
        "split_type": split["split_type"],
        "symbol_count": len(global_test),
        "target": target,
        "test_books": len(split["test"]),
    }


def evaluate_target(rows: list[dict[str, Any]], target: str) -> dict[str, Any]:
    alphabet = infer_alphabet(rows, target)
    split_rows = [score_split(rows, split, target, alphabet) for split in split_specs(rows)]
    global_bits = sum(row["global_bits"] for row in split_rows)
    feature_bits = sum(row["feature_bits"] for row in split_rows)
    return {
        "alphabet_size": len(alphabet),
        "split_rows": split_rows,
        "summary": {
            "feature_bits": feature_bits,
            "global_bits": global_bits,
            "positive_splits": sum(row["saving_bits"] > 0 for row in split_rows),
            "saving_bits": global_bits - feature_bits,
            "split_count": len(split_rows),
            "symbol_count": sum(row["symbol_count"] for row in split_rows),
            "target": target,
        },
    }


def shuffle_target(rows: list[dict[str, Any]], target: str, rng: random.Random) -> list[dict[str, Any]]:
    shuffled = [dict(row) for row in rows]
    if target == "literal_payload_digits":
        payloads = [row.get("literal_payload") for row in rows]
        rng.shuffle(payloads)
        for row, payload in zip(shuffled, payloads):
            row["literal_payload"] = payload
    elif target == "copy_hint_rank_bucket":
        values = [row.get("copy_hint_rank_bucket") for row in rows]
        rng.shuffle(values)
        for row, value in zip(shuffled, values):
            row["copy_hint_rank_bucket"] = value
    elif target == "composition_quantile10":
        by_book = {}
        for row in rows:
            by_book.setdefault(row["book"], row["composition_quantile10"])
        books = sorted(by_book)
        values = [by_book[book] for book in books]
        rng.shuffle(values)
        mapped = dict(zip(books, values))
        for row in shuffled:
            row["composition_quantile10"] = mapped[row["book"]]
    else:
        raise KeyError(target)
    return shuffled


def shuffled_controls(rows: list[dict[str, Any]], target: str, real_saving: float) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in target))
    savings = []
    for _ in range(RANDOM_TRIALS):
        savings.append(evaluate_target(shuffle_target(rows, target, rng), target)["summary"]["saving_bits"])
    return {
        "beats_shuffled_p05": real_saving > percentile(savings, 5),
        "beats_shuffled_p50": real_saving > percentile(savings, 50),
        "beats_shuffled_p95": real_saving > percentile(savings, 95),
        "shuffled_mean": sum(savings) / len(savings),
        "shuffled_p05": percentile(savings, 5),
        "shuffled_p50": percentile(savings, 50),
        "shuffled_p95": percentile(savings, 95),
        "trials": RANDOM_TRIALS,
    }


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def make_result() -> dict[str, Any]:
    rows = load_rows()
    target_results = {}
    promoted = []
    weak = []
    for target in TARGETS:
        evaluated = evaluate_target(rows, target)
        controls = shuffled_controls(rows, target, evaluated["summary"]["saving_bits"])
        evaluated["controls"] = controls
        target_results[target] = evaluated
        if evaluated["summary"]["saving_bits"] > 0 and controls["beats_shuffled_p95"]:
            promoted.append(target)
        elif evaluated["summary"]["saving_bits"] > 0:
            weak.append(target)
    classification = (
        "PROMOTED_PAID_CONTROL_CONTEXT_PAYLOAD_CODEC"
        if promoted
        else "WEAK_PAID_CONTROL_CONTEXT_PAYLOAD_CODEC"
        if weak
        else "PAID_CONTROL_CONTEXT_PAYLOAD_CODEC_NOT_PROMOTED"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "generator_promoted": False,
            "promoted_targets": promoted,
            "row0_status": "unchanged_exogenous",
            "translation_delta": "NONE",
            "weak_targets": weak,
        },
        "inputs": {
            "residual_burden_cross_prediction_gate": rel(RESIDUAL_BURDEN_GATE),
            "unified_external_tape_ledger": rel(UNIFIED_TAPE_LEDGER),
        },
        "plaintext_claim": False,
        "schema": "paid_control_context_payload_codec_gate.v1",
        "scope": "analysis_only_context_codec_over_already_paid_control_fields",
        "summary": {
            "promoted_targets": promoted,
            "target_summaries": {
                target: {
                    **data["summary"],
                    "beats_shuffled_p95": data["controls"]["beats_shuffled_p95"],
                    "shuffled_p95": data["controls"]["shuffled_p95"],
                }
                for target, data in target_results.items()
            },
            "weak_targets": weak,
        },
        "target_results": target_results,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    lines = [
        "# Paid-Control Context Payload Codec Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether already-paid/derived control contexts reduce residual payload "
        "streams without adding a new book-mode header.",
        "",
        "## Summary",
        "",
        "| Target | Saving | Global bits | Context bits | Positive splits | Shuffled p95 | Beats p95 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for target, data in result["target_results"].items():
        summary = data["summary"]
        controls = data["controls"]
        lines.append(
            f"| `{target}` | `{summary['saving_bits']:.3f}` | `{summary['global_bits']:.3f}` | "
            f"`{summary['feature_bits']:.3f}` | `{summary['positive_splits']}/{summary['split_count']}` | "
            f"`{controls['shuffled_p95']:.3f}` | `{controls['beats_shuffled_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Promotion requires positive context-code savings and shuffled-target p95. "
            "A promoted target reduces a residual payload stream only under already-paid "
            "control context; it does not generate the stream from scratch.",
        ]
    )
    MD_OUT.write_text("\n".join(lines) + "\n")


def write_final(result: dict[str, Any]) -> None:
    lines = [
        "# Final Paid-Control Context Payload Codec Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Do already-paid control contexts reduce literal payload, copy-hint bucket, "
        "or composition-index bucket streams without adding a new residual-mode header?",
        "",
        "## Result",
        "",
        f"Promoted targets: `{result['decision']['promoted_targets']}`. "
        f"Weak targets: `{result['decision']['weak_targets']}`.",
        "",
        "| Target | Saving | Shuffled p95 |",
        "| --- | ---: | ---: |",
    ]
    for target, data in result["target_results"].items():
        summary = data["summary"]
        controls = data["controls"]
        lines.append(
            f"| `{target}` | `{summary['saving_bits']:.3f}` | `{controls['shuffled_p95']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "This is a context-code audit over already-paid fields, not a generator. "
            "Row0, plaintext, translation, and compression_bound remain unchanged.",
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_paid_control_context_payload_codec_gate.py](../scripts/01_paid_control_context_payload_codec_gate.py)",
            "- [01_paid_control_context_payload_codec_gate.json](test_results/01_paid_control_context_payload_codec_gate.json)",
            "- [01_paid_control_context_payload_codec_gate.md](test_results/01_paid_control_context_payload_codec_gate.md)",
        ]
    )
    FINAL_OUT.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    JSON_OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    write_markdown(result)
    write_final(result)


if __name__ == "__main__":
    main()
