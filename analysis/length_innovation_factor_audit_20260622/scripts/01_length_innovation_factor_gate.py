#!/usr/bin/env python3
"""Factor exact operation lengths into coarse buckets plus residual innovation.

The stateful exact-action program failed, suggesting that `type:length` is too
fine-grained as a single control symbol. This gate tests whether the exact
length dependency is better understood as a coarse control stream plus a small
within-bucket innovation tape.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "length_innovation_factor_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
LEDGER_PATH = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
UNIFIED_TESTS_PATH = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "02_unified_control_program_tests.json"
)
JSON_OUT = TEST_RESULTS / "01_length_innovation_factor_gate.json"
MD_OUT = TEST_RESULTS / "01_length_innovation_factor_gate.md"

CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 300
ALPHA = 0.5
MIN_TOTAL_FACTOR_SAVING_BITS = 50.0
MIN_RESIDUAL_MODEL_SAVING_BITS = 20.0

BUCKET_RANGES = {
    "len_0008": (1, 8),
    "len_0016": (9, 16),
    "len_0032": (17, 32),
    "len_0064": (33, 64),
    "len_0128": (65, 128),
    "len_0256p": (129, None),
}

FEATURES: dict[str, tuple[str, ...]] = {
    "global": tuple(),
    "op_type": ("op_type",),
    "length_bucket": ("length_bucket",),
    "type_bucket": ("op_type", "length_bucket"),
    "remaining_bucket": ("remaining_bucket",),
    "type_bucket_prev_bucket": ("op_type", "length_bucket", "prev_length_bucket"),
    "type_bucket_remaining": ("op_type", "length_bucket", "remaining_bucket"),
}


def log2(value: float) -> float:
    return math.log2(value)


def remaining_bucket(remaining: int) -> str:
    if remaining <= 8:
        return "rem_0008"
    if remaining <= 16:
        return "rem_0016"
    if remaining <= 32:
        return "rem_0032"
    if remaining <= 64:
        return "rem_0064"
    if remaining <= 128:
        return "rem_0128"
    if remaining <= 256:
        return "rem_0256"
    return "rem_0512p"


def bucket_bounds(bucket: str, remaining: int) -> tuple[int, int]:
    low, high = BUCKET_RANGES[bucket]
    if high is None:
        high = remaining
    return low, min(high, remaining)


def context(row: dict, features: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(feature, "<NA>")) for feature in features)


def load_rows() -> list[dict]:
    data = json.loads(LEDGER_PATH.read_text())
    rows = sorted(data["ledger_rows"], key=lambda r: (r["book"], r["op_index"]))
    prev_by_book: dict[int, str] = {}
    enriched = []
    for row in rows:
        item = dict(row)
        book = int(row["book"])
        low, high = bucket_bounds(row["length_bucket"], int(row["remaining_before_op"]))
        width = high - low + 1
        item["bucket_low"] = low
        item["bucket_high"] = high
        item["bucket_width"] = width
        item["length_residual"] = int(row["length"]) - low
        item["length_residual_bits_uniform"] = log2(width)
        item["remaining_bucket"] = remaining_bucket(int(row["remaining_before_op"]))
        item["prev_length_bucket"] = prev_by_book.get(book, "<BOS>")
        item["residual_fraction_bucket"] = (
            "low" if item["length_residual"] < width / 3 else "mid" if item["length_residual"] < 2 * width / 3 else "high"
        )
        enriched.append(item)
        prev_by_book[book] = row["length_bucket"]
    return enriched


def train_counts(rows: list[dict], feature_name: str) -> tuple[dict[tuple[str, ...], Counter], Counter]:
    features = FEATURES[feature_name]
    counts: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    global_counts: Counter = Counter()
    for row in rows:
        residual = int(row["length_residual"])
        counts[context(row, features)][residual] += 1
        global_counts[residual] += 1
    return dict(counts), global_counts


def residual_bits(
    row: dict,
    counts: dict[tuple[str, ...], Counter],
    global_counts: Counter,
    feature_name: str,
    override_residual: int | None = None,
) -> float:
    residual = int(row["length_residual"] if override_residual is None else override_residual)
    width = int(row["bucket_width"])
    selected = counts.get(context(row, FEATURES[feature_name]))
    if not selected:
        selected = global_counts
    total = sum(selected.values())
    # Dynamic denominator: any residual in the current bucket remains possible.
    probability = (selected.get(residual, 0) + ALPHA) / (total + ALPHA * width)
    return -log2(max(probability, 1e-300))


def score_feature(feature_name: str, train_rows: list[dict], test_rows: list[dict]) -> dict:
    counts, global_counts = train_counts(train_rows, feature_name)
    model_bits = 0.0
    uniform_bits = 0.0
    top1_hits = 0
    fallback_rows = 0
    for row in test_rows:
        model_bits += residual_bits(row, counts, global_counts, feature_name)
        uniform_bits += float(row["length_residual_bits_uniform"])
        selected = counts.get(context(row, FEATURES[feature_name]))
        if not selected:
            selected = global_counts
            fallback_rows += 1
        if selected:
            width = int(row["bucket_width"])
            ranked = sorted(
                range(width),
                key=lambda residual: (
                    residual_bits(row, counts, global_counts, feature_name, residual),
                    residual,
                ),
            )
            if ranked[0] == int(row["length_residual"]):
                top1_hits += 1
    return {
        "fallback_rows": fallback_rows,
        "model_bits": model_bits,
        "saving_bits": uniform_bits - model_bits,
        "top1_hits": top1_hits,
        "uniform_bits": uniform_bits,
    }


def valid_residual_pool(rows: list[dict]) -> dict[str, list[int]]:
    pool: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        pool[row["length_bucket"]].append(int(row["length_residual"]))
    return dict(pool)


def random_residuals_for_rows(rows: list[dict], rng: random.Random) -> list[int]:
    pool = valid_residual_pool(rows)
    generated = []
    for row in rows:
        width = int(row["bucket_width"])
        candidates = [value for value in pool[row["length_bucket"]] if 0 <= value < width]
        if candidates:
            generated.append(rng.choice(candidates))
        else:
            generated.append(rng.randrange(width))
    return generated


def score_override_residuals(
    feature_name: str,
    train_rows: list[dict],
    test_rows: list[dict],
    residuals: list[int],
) -> float:
    counts, global_counts = train_counts(train_rows, feature_name)
    uniform_bits = sum(float(row["length_residual_bits_uniform"]) for row in test_rows)
    model_bits = sum(
        residual_bits(row, counts, global_counts, feature_name, override)
        for row, override in zip(test_rows, residuals)
    )
    return uniform_bits - model_bits


def run_gate() -> dict:
    rows = load_rows()
    unified = json.loads(UNIFIED_TESTS_PATH.read_text())["residual_cost_ledger"]
    op_type_uniform_bits = float(unified["op_type_uniform_bits"])
    raw_length_bits = float(unified["length_uniform_bits"])
    type_bucket_stream_bits = float(unified["type_length_stream_bits"])
    residual_uniform_bits = sum(float(row["length_residual_bits_uniform"]) for row in rows)
    independent_type_exact_length_bits = op_type_uniform_bits + raw_length_bits
    factorized_type_bucket_residual_bits = type_bucket_stream_bits + residual_uniform_bits
    factorized_saving_bits = independent_type_exact_length_bits - factorized_type_bucket_residual_bits

    feature_results = {}
    rng = random.Random(469)
    for feature_name in FEATURES:
        cutoff_rows = []
        observed_saving = 0.0
        observed_model_bits = 0.0
        observed_uniform_bits = 0.0
        observed_top1_hits = 0
        observed_rows = 0
        random_total_savings = [0.0 for _ in range(RANDOM_TRIALS)]
        for cutoff in CUTOFFS:
            train_rows = [row for row in rows if int(row["book"]) < cutoff]
            test_rows = [row for row in rows if int(row["book"]) >= cutoff]
            score = score_feature(feature_name, train_rows, test_rows)
            observed_saving += score["saving_bits"]
            observed_model_bits += score["model_bits"]
            observed_uniform_bits += score["uniform_bits"]
            observed_top1_hits += score["top1_hits"]
            observed_rows += len(test_rows)
            for trial in range(RANDOM_TRIALS):
                random_residuals = random_residuals_for_rows(test_rows, rng)
                random_total_savings[trial] += score_override_residuals(
                    feature_name, train_rows, test_rows, random_residuals
                )
            cutoff_rows.append(
                {
                    "cutoff": cutoff,
                    "train_ops": len(train_rows),
                    "test_ops": len(test_rows),
                    **score,
                }
            )
        random_sorted = sorted(random_total_savings)
        p95 = random_sorted[int(0.95 * (len(random_sorted) - 1))]
        p05 = random_sorted[int(0.05 * (len(random_sorted) - 1))]
        beats_random = observed_saving > p95
        meaningful = observed_saving > MIN_RESIDUAL_MODEL_SAVING_BITS
        if beats_random and meaningful:
            status = "PROMOTED_RESIDUAL_CODEC_CLUE"
        elif beats_random:
            status = "WEAK_RESIDUAL_CODEC_CLUE"
        else:
            status = "REJECTED_RESIDUAL_MODEL"
        feature_results[feature_name] = {
            "beats_random_p95": beats_random,
            "cutoff_rows": cutoff_rows,
            "features": FEATURES[feature_name],
            "observed_model_bits": observed_model_bits,
            "observed_saving_bits": observed_saving,
            "observed_top1_hits": observed_top1_hits,
            "observed_total_rows": observed_rows,
            "observed_uniform_bits": observed_uniform_bits,
            "random_saving_p05": p05,
            "random_saving_p95": p95,
            "status": status,
        }

    promoted_features = [
        name for name, result in feature_results.items() if result["status"] == "PROMOTED_RESIDUAL_CODEC_CLUE"
    ]
    best_feature = min(feature_results.items(), key=lambda item: item[1]["observed_model_bits"])[0]
    factorization_promoted = factorized_saving_bits > MIN_TOTAL_FACTOR_SAVING_BITS
    residual_codec_promoted = bool(promoted_features)
    if factorization_promoted and residual_codec_promoted:
        classification = "length_innovation_factorization_plus_residual_clue"
    elif factorization_promoted:
        classification = "length_innovation_factorization_clue_residual_external"
    else:
        classification = "length_innovation_factorization_not_promoted"

    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "best_residual_feature": best_feature,
            "factorization_promoted": factorization_promoted,
            "promoted_residual_features": promoted_features,
            "residual_codec_promoted": residual_codec_promoted,
            "row0_status": "unchanged_exogenous",
        },
        "feature_results": feature_results,
        "inputs": {
            "ledger": str(LEDGER_PATH.relative_to(ROOT)),
            "unified_tests": str(UNIFIED_TESTS_PATH.relative_to(ROOT)),
            "cutoffs": CUTOFFS,
            "random_trials": RANDOM_TRIALS,
        },
        "plaintext_claim": False,
        "scope": "analysis_only_length_bucket_plus_residual_innovation",
        "summary": {
            "factorized_saving_bits": factorized_saving_bits,
            "factorized_type_bucket_residual_bits": factorized_type_bucket_residual_bits,
            "independent_type_exact_length_bits": independent_type_exact_length_bits,
            "op_type_uniform_bits": op_type_uniform_bits,
            "raw_length_bits": raw_length_bits,
            "residual_uniform_bits": residual_uniform_bits,
            "rows": len(rows),
            "type_bucket_stream_bits": type_bucket_stream_bits,
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict) -> None:
    summary = result["summary"]
    decision = result["decision"]
    best = result["feature_results"][decision["best_residual_feature"]]
    lines = [
        "# Length Innovation Factor Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "This gate tests whether exact operation lengths are better represented as a "
        "coarse `type:length_bucket` control stream plus a within-bucket residual "
        "innovation tape. It is a representation test, not a plaintext or row0 test.",
        "",
        "## Factorization Ledger",
        "",
        f"- Rows: `{summary['rows']}`.",
        f"- Independent `op_type + exact_length` bits: `{summary['independent_type_exact_length_bits']:.3f}`.",
        f"- `type:length_bucket` stream bits: `{summary['type_bucket_stream_bits']:.3f}`.",
        f"- Uniform residual-within-bucket bits: `{summary['residual_uniform_bits']:.3f}`.",
        f"- Factorized total bits: `{summary['factorized_type_bucket_residual_bits']:.3f}`.",
        f"- Factorized saving: `{summary['factorized_saving_bits']:.3f}` bits.",
        "",
        "## Residual Codec Gate",
        "",
        "| Feature | Bits | Saving | Random p95 | Top1 Hits | Status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, row in sorted(result["feature_results"].items()):
        lines.append(
            f"| `{name}` | `{row['observed_model_bits']:.3f}` | "
            f"`{row['observed_saving_bits']:.3f}` | `{row['random_saving_p95']:.3f}` | "
            f"`{row['observed_top1_hits']}/{row['observed_total_rows']}` | `{row['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Best Residual Feature",
            "",
            f"- Best residual feature: `{decision['best_residual_feature']}`.",
            f"- Best residual bits: `{best['observed_model_bits']:.3f}`.",
            f"- Best residual saving vs uniform residual: `{best['observed_saving_bits']:.3f}`.",
            f"- Best residual shuffled p95 saving: `{best['random_saving_p95']:.3f}`.",
            f"- Promoted residual features: `{decision['promoted_residual_features']}`.",
            "",
            "## Decision",
            "",
        ]
    )
    if result["classification"] == "length_innovation_factorization_plus_residual_clue":
        lines.append(
            "The bucket+residual representation is promoted as a useful control-stream "
            "factorization, and at least one residual codec also beats controls. This is "
            "still not a generator unless the residual tape is produced without lookup."
        )
    elif result["classification"] == "length_innovation_factorization_clue_residual_external":
        lines.append(
            "The bucket+residual representation is promoted as a useful dependency "
            "factorization, but the exact residual tape remains external. This narrows "
            "the blocker from exact length as a whole to within-bucket length innovation."
        )
    else:
        lines.append(
            "The bucket+residual representation is not promoted: it does not reduce the "
            "declared exact-length dependency enough after paying the coarse stream."
        )
    lines.extend(
        [
            "",
            "`row0`, translation, plaintext, and the compression bound remain unchanged.",
            "",
            "## Remaining External Fields",
            "",
            "- `type:length_bucket` control stream",
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
    print(
        json.dumps(
            {
                "best_residual_feature": result["decision"]["best_residual_feature"],
                "classification": result["classification"],
                "factorized_saving_bits": result["summary"]["factorized_saving_bits"],
                "promoted_residual_features": result["decision"]["promoted_residual_features"],
                "report": str(MD_OUT.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
