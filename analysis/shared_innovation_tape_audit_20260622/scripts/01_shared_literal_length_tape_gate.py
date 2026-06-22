#!/usr/bin/env python3
"""Test whether the literal innovation tape can also drive length residuals.

The length factor audit narrowed exact operation length to a coarse
type:length_bucket stream plus a within-bucket residual tape. The literal
payload already forms a 266-digit innovation tape, close to the 261 operation
count. This gate tests the constructive hypothesis that one already-paid
literal-tape digit per operation can predict the within-bucket length residual,
with paid corrections.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "shared_innovation_tape_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
LEDGER_PATH = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
JSON_OUT = TEST_RESULTS / "01_shared_literal_length_tape_gate.json"
MD_OUT = TEST_RESULTS / "01_shared_literal_length_tape_gate.md"

CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 300
OFFSETS = range(0, 6)
AFFINE_A = [1, 3, 7, 9]
MIN_PROMOTION_SAVING_BITS = 20.0

BUCKET_RANGES = {
    "len_0008": (1, 8),
    "len_0016": (9, 16),
    "len_0032": (17, 32),
    "len_0064": (33, 64),
    "len_0128": (65, 128),
    "len_0256p": (129, None),
}


@dataclass(frozen=True)
class Policy:
    name: str
    offset: int
    a: int = 1
    b: int = 0


def log2(value: float) -> float:
    return math.log2(value)


def log2_comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)) / math.log(2)


def bucket_bounds(bucket: str, remaining: int) -> tuple[int, int]:
    low, high = BUCKET_RANGES[bucket]
    if high is None:
        high = remaining
    return low, min(high, remaining)


def load_rows_and_tape() -> tuple[list[dict], str]:
    data = json.loads(LEDGER_PATH.read_text())
    rows = sorted(data["ledger_rows"], key=lambda r: (r["book"], r["op_index"]))
    literal_tape = "".join(row["literal_payload"] for row in rows if row["op_type"] == "literal")
    enriched = []
    for row in rows:
        item = dict(row)
        low, high = bucket_bounds(row["length_bucket"], int(row["remaining_before_op"]))
        width = high - low + 1
        item["bucket_low"] = low
        item["bucket_high"] = high
        item["bucket_width"] = width
        item["length_residual"] = int(row["length"]) - low
        item["length_residual_bits_uniform"] = log2(width)
        enriched.append(item)
    return enriched, literal_tape


def policies() -> list[Policy]:
    items: list[Policy] = []
    for offset in OFFSETS:
        items.append(Policy("digit_mod", offset))
        items.append(Policy("digit_scaled_floor", offset))
        items.append(Policy("digit_scaled_round", offset))
        items.append(Policy("digit_inverted_scaled_floor", offset))
        for a in AFFINE_A:
            for b in range(10):
                items.append(Policy("digit_affine_mod", offset, a, b))
    return items


def tape_digit(tape: str, row: dict, offset: int) -> int | None:
    idx = int(row["global_op_index"]) + offset
    if idx < 0 or idx >= len(tape):
        return None
    return int(tape[idx])


def predict(policy: Policy, digit: int, width: int) -> int:
    if policy.name == "digit_mod":
        return digit % width
    if policy.name == "digit_affine_mod":
        return ((policy.a * digit) + policy.b) % width
    if policy.name == "digit_scaled_floor":
        return min(width - 1, int((digit / 10.0) * width))
    if policy.name == "digit_scaled_round":
        if width == 1:
            return 0
        return min(width - 1, round((digit / 9.0) * (width - 1)))
    if policy.name == "digit_inverted_scaled_floor":
        return min(width - 1, int(((9 - digit) / 10.0) * width))
    raise ValueError(policy)


def score_policy(policy: Policy, rows: list[dict], tape: str) -> dict:
    n = len(rows)
    mismatches = []
    hits = 0
    missing = 0
    uniform_bits = 0.0
    for idx, row in enumerate(rows):
        width = int(row["bucket_width"])
        uniform_bits += float(row["length_residual_bits_uniform"])
        digit = tape_digit(tape, row, policy.offset)
        if digit is None:
            mismatches.append(idx)
            missing += 1
            continue
        pred = predict(policy, digit, width)
        if pred == int(row["length_residual"]):
            hits += 1
        else:
            mismatches.append(idx)
    correction_payload_bits = sum(float(rows[idx]["length_residual_bits_uniform"]) for idx in mismatches)
    site_bits = log2_comb(n, len(mismatches))
    correction_bits = site_bits + correction_payload_bits
    return {
        "correction_bits": correction_bits,
        "correction_payload_bits": correction_payload_bits,
        "hit_rate": hits / n if n else 0.0,
        "hits": hits,
        "mismatches": len(mismatches),
        "missing_digits": missing,
        "saving_vs_uniform_bits": uniform_bits - correction_bits,
        "site_bits": site_bits,
        "uniform_bits": uniform_bits,
    }


def select_best_policy(train_rows: list[dict], tape: str) -> tuple[Policy, dict]:
    best_policy = None
    best_score = None
    for policy in policies():
        score = score_policy(policy, train_rows, tape)
        if best_score is None or score["correction_bits"] < best_score["correction_bits"]:
            best_policy = policy
            best_score = score
    assert best_policy is not None and best_score is not None
    return best_policy, best_score


def shuffle_tape_same_multiset(tape: str, rng: random.Random) -> str:
    digits = list(tape)
    rng.shuffle(digits)
    return "".join(digits)


def run_gate() -> dict:
    rows, literal_tape = load_rows_and_tape()
    rng = random.Random(469)
    cutoff_rows = []
    observed_total_uniform = 0.0
    observed_total_correction = 0.0
    observed_total_hits = 0
    observed_total_rows = 0
    selected_policies = []
    random_total_savings = [0.0 for _ in range(RANDOM_TRIALS)]

    for cutoff in CUTOFFS:
        train_rows = [row for row in rows if int(row["book"]) < cutoff]
        test_rows = [row for row in rows if int(row["book"]) >= cutoff]
        policy, train_score = select_best_policy(train_rows, literal_tape)
        test_score = score_policy(policy, test_rows, literal_tape)
        observed_total_uniform += test_score["uniform_bits"]
        observed_total_correction += test_score["correction_bits"]
        observed_total_hits += test_score["hits"]
        observed_total_rows += len(test_rows)
        selected_policies.append(policy)

        for trial in range(RANDOM_TRIALS):
            shuffled = shuffle_tape_same_multiset(literal_tape, rng)
            shuffled_policy, _ = select_best_policy(train_rows, shuffled)
            shuffled_score = score_policy(shuffled_policy, test_rows, shuffled)
            random_total_savings[trial] += shuffled_score["saving_vs_uniform_bits"]

        cutoff_rows.append(
            {
                "cutoff": cutoff,
                "selected_policy": policy.__dict__,
                "test_ops": len(test_rows),
                "train_ops": len(train_rows),
                "train_score": train_score,
                "test_score": test_score,
            }
        )

    observed_saving = observed_total_uniform - observed_total_correction
    random_sorted = sorted(random_total_savings)
    random_p95 = random_sorted[int(0.95 * (len(random_sorted) - 1))]
    random_p05 = random_sorted[int(0.05 * (len(random_sorted) - 1))]
    beats_random = observed_saving > random_p95
    meaningful = observed_saving > MIN_PROMOTION_SAVING_BITS
    if beats_random and meaningful:
        classification = "shared_literal_length_tape_promoted"
        status = "PROMOTED_SHARED_INNOVATION_TAPE"
    elif beats_random:
        classification = "shared_literal_length_tape_weak_clue"
        status = "WEAK_SHARED_INNOVATION_TAPE"
    else:
        classification = "shared_literal_length_tape_not_promoted"
        status = "REJECTED_SHARED_INNOVATION_TAPE"

    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "decision": {
            "beats_random_p95": beats_random,
            "meaningful_saving": meaningful,
            "row0_status": "unchanged_exogenous",
            "status": status,
        },
        "inputs": {
            "cutoffs": CUTOFFS,
            "ledger": str(LEDGER_PATH.relative_to(ROOT)),
            "literal_tape_digits": len(literal_tape),
            "policies_tested": len(policies()),
            "random_trials": RANDOM_TRIALS,
            "residual_events": len(rows),
        },
        "plaintext_claim": False,
        "rows": cutoff_rows,
        "scope": "analysis_only_shared_literal_tape_to_length_residual",
        "summary": {
            "observed_hit_rate": observed_total_hits / observed_total_rows,
            "observed_saving_vs_uniform_bits": observed_saving,
            "observed_total_correction_bits": observed_total_correction,
            "observed_total_hits": observed_total_hits,
            "observed_total_rows": observed_total_rows,
            "observed_total_uniform_bits": observed_total_uniform,
            "random_saving_p05": random_p05,
            "random_saving_p95": random_p95,
            "selected_policy_counts": {
                str(policy.__dict__): selected_policies.count(policy) for policy in set(selected_policies)
            },
        },
        "translation_delta": "NONE",
    }


def write_markdown(result: dict) -> None:
    summary = result["summary"]
    lines = [
        "# Shared Literal-Length Innovation Tape Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether the already-paid literal innovation tape can also drive the "
        "within-bucket length residual tape. Each operation reads one literal-tape "
        "digit at a prefix-selected offset and applies a small arithmetic policy; "
        "mismatches are paid as correction sites plus residual payload.",
        "",
        "## Summary",
        "",
        f"- Literal tape digits: `{result['inputs']['literal_tape_digits']}`.",
        f"- Length residual events: `{result['inputs']['residual_events']}`.",
        f"- Policies tested: `{result['inputs']['policies_tested']}`.",
        f"- Observed uniform residual bits: `{summary['observed_total_uniform_bits']:.3f}`.",
        f"- Observed correction bits after tape prediction: `{summary['observed_total_correction_bits']:.3f}`.",
        f"- Observed saving vs uniform residual: `{summary['observed_saving_vs_uniform_bits']:.3f}`.",
        f"- Shuffled literal-tape p95 saving: `{summary['random_saving_p95']:.3f}`.",
        f"- Hits: `{summary['observed_total_hits']}/{summary['observed_total_rows']}` "
        f"(`{summary['observed_hit_rate']:.6f}`).",
        f"- Selected policies: `{summary['selected_policy_counts']}`.",
        "",
        "## Prefix-Holdout Rows",
        "",
        "| Cutoff | Policy | Train Ops | Test Ops | Test Hits | Test Correction Bits | Test Saving |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["rows"]:
        policy = row["selected_policy"]
        policy_label = f"{policy['name']}:off{policy['offset']}:a{policy['a']}:b{policy['b']}"
        test = row["test_score"]
        lines.append(
            f"| `{row['cutoff']}` | `{policy_label}` | `{row['train_ops']}` | `{row['test_ops']}` | "
            f"`{test['hits']}` | `{test['correction_bits']:.3f}` | "
            f"`{test['saving_vs_uniform_bits']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "## Decision",
            "",
        ]
    )
    if result["classification"] == "shared_literal_length_tape_promoted":
        lines.append(
            "The literal innovation tape is promoted as a shared driver for length "
            "residuals under this policy family. This reduces an external residual "
            "stream, but still requires paid corrections."
        )
    elif result["classification"] == "shared_literal_length_tape_weak_clue":
        lines.append(
            "The literal tape beats shuffled controls but does not save enough bits to "
            "replace the residual tape. It remains a weak clue only."
        )
    else:
        lines.append(
            "The literal innovation tape is not promoted as a shared length-residual "
            "driver. It fails to beat shuffled same-multiset tape controls after "
            "prefix selection and paid corrections."
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
                "classification": result["classification"],
                "observed_saving": result["summary"]["observed_saving_vs_uniform_bits"],
                "random_p95": result["summary"]["random_saving_p95"],
                "status": result["decision"]["status"],
                "report": str(MD_OUT.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
