#!/usr/bin/env python3
"""Executable v2 remaining-tape coupling gate.

After the online x64 program reduced the executable coarse-control tape, this
gate checks whether that new online state also helps code the remaining external
tapes:

- exact composition-index quantile, book-level;
- copy-hint rank bucket, copy-operation level;
- literal payload digits, digit level.

This is deliberately a joint residual-coupling audit, not three new local
fronts. Promotion here would mean "the x64 online state opens a next residual
route"; it would not by itself promote plaintext, row0 origin, or a full
generator.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "executable_v2_remaining_tape_coupling_audit_20260622"
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
COMPOSITION = (
    ROOT
    / "analysis"
    / "composition_index_structure_audit_20260622"
    / "reports"
    / "test_results"
    / "01_composition_index_structure_gate.json"
)
EXECUTABLE_V2 = (
    ROOT
    / "analysis"
    / "executable_v2_residual_coupling_audit_20260622"
    / "reports"
    / "test_results"
    / "01_executable_v2_residual_coupling_gate.json"
)

JSON_OUT = TEST_RESULTS / "01_executable_v2_remaining_tape_coupling_gate.json"
MD_OUT = TEST_RESULTS / "01_executable_v2_remaining_tape_coupling_gate.md"
FINAL_OUT = FRONT / "reports" / "final_executable_v2_remaining_tape_coupling_audit.md"

PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
ALPHA = 0.5
RANDOM_TRIALS = 100
RANDOM_SEED = 46920260622 + 464
DIGITS = "0123456789"

BASE_FEATURES = [
    "global",
    "coarse",
    "op_pos",
    "book_length",
    "op_count",
    "online_status",
    "online_rank",
    "online_paid",
    "online_status_x_coarse",
    "online_status_x_opcount",
    "online_rank_x_pos",
    "online_paid_x_coarse",
]
LITERAL_FEATURES = BASE_FEATURES + ["prev_digit", "online_status_x_prev_digit", "coarse_x_prev_digit"]

TARGETS = {
    "composition_quantile10": {"features": BASE_FEATURES, "level": "book"},
    "copy_hint_rank_bucket": {"features": BASE_FEATURES, "level": "copy"},
    "literal_payload_digits": {"features": LITERAL_FEATURES, "level": "digit"},
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


def bucket_count(value: int, cuts: list[int], prefix: str) -> str:
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut}"
    return f"{prefix}_gt_{cuts[-1]}"


def qbucket(fraction: float) -> str:
    return f"compq_{min(9, max(0, int(float(fraction) * 10))):02d}"


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


def online_rank_bucket(rank: int | None) -> str:
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
    if feature == "online_status":
        return row["online_status"]
    if feature == "online_rank":
        return row["online_rank_bucket"]
    if feature == "online_paid":
        return row["online_paid_bucket"]
    if feature == "online_status_x_coarse":
        return f"{row['online_status']}|{row['coarse_type_length_bucket']}"
    if feature == "online_status_x_opcount":
        return f"{row['online_status']}|{row['book_op_count_bucket']}"
    if feature == "online_rank_x_pos":
        return f"{row['online_rank_bucket']}|{row['op_pos_bucket']}"
    if feature == "online_paid_x_coarse":
        return f"{row['online_paid_bucket']}|{row['coarse_type_length_bucket']}"
    if feature == "prev_digit":
        return prev_digit
    if feature == "online_status_x_prev_digit":
        return f"{row['online_status']}|{prev_digit}"
    if feature == "coarse_x_prev_digit":
        return f"{row['coarse_type_length_bucket']}|{prev_digit}"
    raise KeyError(feature)


def make_rows() -> list[dict[str, Any]]:
    minimal = load_json(MINIMAL_LEDGER)
    online = load_json(ONLINE_X64)
    composition = load_json(COMPOSITION)
    executable_v2 = load_json(EXECUTABLE_V2)
    for name, data in [
        ("minimal_ledger", minimal),
        ("online_x64", online),
        ("composition", composition),
        ("executable_v2", executable_v2),
    ]:
        assert_boundary(name, data)
    if executable_v2["classification"] != "PROMOTED_EXECUTABLE_V2_LEDGER_ONLY":
        raise RuntimeError("remaining-tape gate expects executable v2 ledger")

    online_by_book = {int(row["book"]): row for row in online["rows"]}
    comp_by_book = {int(row["book"]): row for row in composition["rank_rows"]}
    out = []
    for row in minimal["ledger_rows"]:
        book = int(row["book"])
        online_row = online_by_book[book]
        comp = comp_by_book[book]
        item = dict(row)
        item["book"] = book
        item["book_op_count_bucket"] = bucket_count(int(row["book_op_count"]), [1, 2, 4, 8], "ops")
        item["composition_quantile10"] = qbucket(float(comp["rank_fraction"]))
        item["online_paid_bucket"] = paid_bucket(float(online_row["online_paid_coarse_bits"]))
        item["online_rank_bucket"] = online_rank_bucket(online_row["hit_rank"])
        item["online_status"] = "hit" if online_row["sequence_in_beam"] else "miss"
        item["online_sequence_hit_rank"] = online_row["hit_rank"]
        out.append(item)
    return out


def split_specs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    books = {row["book"] for row in rows}
    return [
        {
            "label": f"prefix_{cutoff}",
            "train": {book for book in books if book < cutoff},
            "test": {book for book in books if book >= cutoff},
        }
        for cutoff in PREFIX_CUTOFFS
    ]


def target_pairs(rows: list[dict[str, Any]], books: set[int], target: str, feature: str) -> list[tuple[str, str]]:
    pairs = []
    if target == "composition_quantile10":
        seen = set()
        for row in rows:
            if row["book"] in books and row["book"] not in seen:
                seen.add(row["book"])
                if int(row["composition_count"]) > 1:
                    pairs.append((feature_value(row, feature), row["composition_quantile10"]))
        return pairs
    if target == "copy_hint_rank_bucket":
        for row in rows:
            if row["book"] in books and row.get("copy_hint_rank_bucket") is not None:
                pairs.append((feature_value(row, feature), row["copy_hint_rank_bucket"]))
        return pairs
    if target == "literal_payload_digits":
        for row in rows:
            if row["book"] not in books or not row.get("literal_payload"):
                continue
            prev = "BOS"
            for digit in row["literal_payload"]:
                pairs.append((feature_value(row, feature, prev), digit))
                prev = digit
        return pairs
    raise KeyError(target)


def infer_alphabet(rows: list[dict[str, Any]], target: str) -> list[str]:
    if target == "literal_payload_digits":
        return list(DIGITS)
    books = {row["book"] for row in rows}
    return sorted({symbol for _, symbol in target_pairs(rows, books, target, "global")})


def train_counts(pairs: list[tuple[str, str]]) -> tuple[Counter[str], dict[str, Counter[str]]]:
    global_counts: Counter[str] = Counter()
    context_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for context, symbol in pairs:
        global_counts[symbol] += 1
        context_counts[context][symbol] += 1
    return global_counts, dict(context_counts)


def code_symbol(symbol: str, counts: Counter[str], alphabet: list[str]) -> float:
    total = sum(counts.values())
    probability = (counts.get(symbol, 0) + ALPHA) / (total + ALPHA * len(alphabet))
    return -log2(probability)


def score_pairs(train_pairs: list[tuple[str, str]], test_pairs: list[tuple[str, str]], alphabet: list[str]) -> float:
    global_counts, context_counts = train_counts(train_pairs)
    bits = 0.0
    for context, symbol in test_pairs:
        bits += code_symbol(symbol, context_counts.get(context, global_counts), alphabet)
    return bits


def loo_feature_score(rows: list[dict[str, Any]], train_books: set[int], target: str, feature: str, alphabet: list[str]) -> float:
    if len(train_books) < 2:
        return float("inf")
    bits = 0.0
    for heldout in sorted(train_books):
        subtrain = set(train_books) - {heldout}
        train_pairs = target_pairs(rows, subtrain, target, feature)
        test_pairs = target_pairs(rows, {heldout}, target, feature)
        if test_pairs:
            bits += score_pairs(train_pairs, test_pairs, alphabet)
    return bits + log2(len(TARGETS[target]["features"]))


def select_feature(rows: list[dict[str, Any]], train_books: set[int], target: str, alphabet: list[str]) -> str:
    return min(
        TARGETS[target]["features"],
        key=lambda feature: (loo_feature_score(rows, train_books, target, feature, alphabet), feature),
    )


def score_split(rows: list[dict[str, Any]], split: dict[str, Any], target: str, alphabet: list[str]) -> dict[str, Any]:
    feature = select_feature(rows, split["train"], target, alphabet)
    global_train = target_pairs(rows, split["train"], target, "global")
    global_test = target_pairs(rows, split["test"], target, "global")
    feature_train = target_pairs(rows, split["train"], target, feature)
    feature_test = target_pairs(rows, split["test"], target, feature)
    global_bits = score_pairs(global_train, global_test, alphabet)
    feature_bits = score_pairs(feature_train, feature_test, alphabet) + log2(len(TARGETS[target]["features"]))
    return {
        "feature": feature,
        "feature_bits": feature_bits,
        "global_bits": global_bits,
        "label": split["label"],
        "saving_bits": global_bits - feature_bits,
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


def percentile(values: list[float], p: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(p / 100 * len(ordered)) - 1))
    return ordered[index]


def shuffled_controls(rows: list[dict[str, Any]], target: str, real_saving: float) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED + sum(ord(ch) for ch in target))
    savings = [
        evaluate_target(shuffle_target(rows, target, rng), target)["summary"]["saving_bits"]
        for _ in range(RANDOM_TRIALS)
    ]
    return {
        "beats_shuffled_p95": real_saving > percentile(savings, 95),
        "shuffled_mean": sum(savings) / len(savings),
        "shuffled_p05": percentile(savings, 5),
        "shuffled_p50": percentile(savings, 50),
        "shuffled_p95": percentile(savings, 95),
        "trials": RANDOM_TRIALS,
    }


def make_result() -> dict[str, Any]:
    rows = make_rows()
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
        "PROMOTED_EXECUTABLE_V2_REMAINING_TAPE_COUPLING"
        if promoted
        else "WEAK_EXECUTABLE_V2_REMAINING_TAPE_COUPLING"
        if weak
        else "EXECUTABLE_V2_REMAINING_TAPES_STILL_EXTERNAL"
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
            "composition_index_gate": rel(COMPOSITION),
            "executable_v2_ledger_gate": rel(EXECUTABLE_V2),
            "minimal_external_tape_ledger": rel(MINIMAL_LEDGER),
            "online_x64_coarse_control_program": rel(ONLINE_X64),
            "random_trials": RANDOM_TRIALS,
        },
        "plaintext_claim": False,
        "schema": "executable_v2_remaining_tape_coupling_gate.v1",
        "scope": "analysis_only_online_x64_state_coupling_for_remaining_external_tapes",
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


def write_markdown(result: dict[str, Any], path: Path) -> None:
    lines = [
        "# Executable v2 Remaining-Tape Coupling Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "Does the promoted online x64 coarse-control state help code the remaining "
        "external tapes inside executable ledger v2?",
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
        ]
    )
    if result["decision"]["promoted_targets"]:
        lines.append(
            "At least one remaining tape shows controlled coupling to the online x64 "
            "state. This opens a follow-up route, but does not yet remove the exact "
            "external tape unless an exact codec is built."
        )
    elif result["decision"]["weak_targets"]:
        lines.append(
            "Only weak positive coupling appears. Treat it as diagnostic, not as an "
            "executable ledger reduction."
        )
    else:
        lines.append(
            "No remaining tape shows positive controlled coupling to the online x64 "
            "state. The v2 improvement appears localized to coarse control; the "
            "next generator route needs a different representation for composition, "
            "literal payload, and copy hints."
        )
    lines.extend(
        [
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
                "promoted_targets": result["decision"]["promoted_targets"],
                "weak_targets": result["decision"]["weak_targets"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
