from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
SCHEDULE_GATE = TEST_RESULTS / "07_innovation_tape_schedule_gate.json"

OUT_STEM = "08_tape_trigger_policy_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 500
MIN_COPY_LEN = 5


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def log2comb(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("inf")
    return (
        math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    ) / math.log(2)


def bucket(value: int, cuts: list[int], prefix: str) -> str:
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut}"
    return f"{prefix}_gt_{cuts[-1]}"


def longest_target_copy(
    source_text: str,
    target: str,
    pos: int,
    min_len: int = MIN_COPY_LEN,
) -> int:
    if pos + min_len > len(target):
        return 0
    needle = target[pos : pos + min_len]
    source = source_text.find(needle)
    best = 0
    while source != -1:
        length = min_len
        cap = min(len(target) - pos, len(source_text) - source)
        while length < cap and source_text[source + length] == target[pos + length]:
            length += 1
        best = max(best, length)
        source = source_text.find(needle, source + 1)
    return best


def canonical_tape(ops_by_book: dict[str, list[dict[str, Any]]]) -> str:
    parts = []
    for book in range(10, 70):
        for op in ops_by_book[str(book)]:
            if op["type"] == "literal":
                parts.append(op.get("payload", ""))
    return "".join(parts)


def build_rows(
    books: dict[int, str],
    ops_by_book: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    tape = canonical_tape(ops_by_book)
    rows: list[dict[str, Any]] = []
    emitted_before_book = "".join(books[book] for book in range(10))
    tape_pos = 0
    last_literal_global_op = -1
    global_op_index = 0
    previous_type = "book_start"
    for book in range(10, 70):
        target = books[book]
        previous_type = "book_start"
        for op_index, op in enumerate(ops_by_book[str(book)]):
            pos = int(op["target_start"])
            source_text = emitted_before_book + target[:pos]
            max_copy = longest_target_copy(source_text, target, pos)
            next_tape_digit = tape[tape_pos] if tape_pos < len(tape) else None
            current_digit = target[pos] if pos < len(target) else None
            label = "literal" if op["type"] == "literal" else "copy"
            rows.append(
                {
                    "book": book,
                    "op_index": op_index,
                    "global_op_index": global_op_index,
                    "target_start": pos,
                    "remaining": len(target) - pos,
                    "length": int(op["length"]),
                    "label": label,
                    "previous_type": previous_type,
                    "age_since_literal_op": (
                        global_op_index - last_literal_global_op
                        if last_literal_global_op >= 0
                        else 999
                    ),
                    "max_target_copy": max_copy,
                    "copy_available": max_copy >= MIN_COPY_LEN,
                    "next_tape_matches_target": next_tape_digit == current_digit,
                }
            )
            previous_type = label
            if label == "literal":
                payload = op.get("payload", "")
                tape_pos += len(payload)
                last_literal_global_op = global_op_index
            global_op_index += 1
        emitted_before_book += target
    return rows


def feature_value(row: dict[str, Any], feature: str) -> str:
    if feature == "global_majority":
        return "all"
    if feature == "copy_available":
        return f"copy_available_{row['copy_available']}"
    if feature == "maxcopy_bucket":
        return bucket(row["max_target_copy"], [0, 4, 5, 8, 20, 60, 160], "max")
    if feature == "target_start_bucket":
        return bucket(row["target_start"], [0, 5, 20, 60, 120], "start")
    if feature == "remaining_bucket":
        return bucket(row["remaining"], [5, 20, 60, 120], "remain")
    if feature == "previous_type":
        return row["previous_type"]
    if feature == "age_since_literal_bucket":
        return bucket(row["age_since_literal_op"], [1, 2, 4, 8, 16, 32, 64], "age")
    if feature == "next_tape_match":
        return f"next_tape_match_{row['next_tape_matches_target']}"
    if feature == "copy_available_x_tape_match":
        return (
            feature_value(row, "copy_available")
            + "|"
            + feature_value(row, "next_tape_match")
        )
    if feature == "copy_available_x_age":
        return (
            feature_value(row, "copy_available")
            + "|"
            + feature_value(row, "age_since_literal_bucket")
        )
    if feature == "start_x_copy_available":
        return (
            feature_value(row, "target_start_bucket")
            + "|"
            + feature_value(row, "copy_available")
        )
    raise KeyError(feature)


FEATURES = [
    "global_majority",
    "copy_available",
    "maxcopy_bucket",
    "target_start_bucket",
    "remaining_bucket",
    "previous_type",
    "age_since_literal_bucket",
    "next_tape_match",
    "copy_available_x_tape_match",
    "copy_available_x_age",
    "start_x_copy_available",
]


def train_table(train_rows: list[dict[str, Any]], feature: str) -> tuple[dict[str, str], str]:
    global_counts = Counter(row["label"] for row in train_rows)
    default = global_counts.most_common(1)[0][0]
    if feature == "global_majority":
        return {}, default
    by_context: dict[str, Counter[str]] = defaultdict(Counter)
    for row in train_rows:
        by_context[feature_value(row, feature)][row["label"]] += 1
    table = {
        context: counts.most_common(1)[0][0]
        for context, counts in by_context.items()
    }
    return table, default


def predict(row: dict[str, Any], feature: str, table: dict[str, str], default: str) -> str:
    if feature == "global_majority":
        return default
    return table.get(feature_value(row, feature), default)


def evaluate_feature(
    rows: list[dict[str, Any]],
    cutoff: int,
    feature: str,
    feature_count: int,
) -> dict[str, Any]:
    train_rows = [row for row in rows if 10 <= row["book"] < cutoff]
    test_rows = [row for row in rows if cutoff <= row["book"] < 70]
    table, default = train_table(train_rows, feature)
    predictions = [predict(row, feature, table, default) for row in test_rows]
    labels = [row["label"] for row in test_rows]
    errors = sum(1 for pred, label in zip(predictions, labels) if pred != label)
    literal_count = sum(1 for label in labels if label == "literal")
    predicted_literals = sum(1 for pred in predictions if pred == "literal")
    literal_hits = sum(
        1
        for pred, label in zip(predictions, labels)
        if pred == "literal" and label == "literal"
    )
    lookup_bits = log2comb(len(test_rows), literal_count)
    correction_bits = log2comb(len(test_rows), errors)
    table_bits = len(table) if feature != "global_majority" else 0.0
    feature_id_bits = math.log2(feature_count) if feature != "global_majority" else 0.0
    total_bits = correction_bits + table_bits + feature_id_bits
    return {
        "cutoff": cutoff,
        "feature": feature,
        "train_ops": len(train_rows),
        "test_ops": len(test_rows),
        "test_literal_ops": literal_count,
        "predicted_literal_ops": predicted_literals,
        "literal_hits": literal_hits,
        "context_count": len(table),
        "errors": errors,
        "exact_ops": len(test_rows) - errors,
        "lookup_bits": lookup_bits,
        "correction_bits": correction_bits,
        "table_bits": table_bits,
        "feature_id_bits": feature_id_bits,
        "total_bits": total_bits,
        "saving_vs_lookup_bits": lookup_bits - total_bits,
    }


def add_global_deltas(rows: list[dict[str, Any]]) -> None:
    global_by_cutoff = {
        row["cutoff"]: row
        for row in rows
        if row["feature"] == "global_majority"
    }
    for row in rows:
        baseline = global_by_cutoff[row["cutoff"]]
        row["delta_bits_vs_global"] = (
            row["saving_vs_lookup_bits"] - baseline["saving_vs_lookup_bits"]
        )
        row["delta_exact_vs_global"] = row["exact_ops"] - baseline["exact_ops"]


def evaluate_all(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for cutoff in PREFIX_CUTOFFS:
        for feature in FEATURES:
            out.append(evaluate_feature(rows, cutoff, feature, len(FEATURES)))
    add_global_deltas(out)
    return out


def random_control(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    labels = [row["label"] for row in rows]
    best_delta_bits = []
    best_delta_exact = []
    best_exact = []
    for _ in range(RANDOM_TRIALS):
        shuffled_labels = labels[:]
        rng.shuffle(shuffled_labels)
        shuffled_rows = [dict(row, label=label) for row, label in zip(rows, shuffled_labels)]
        eval_rows = evaluate_all(shuffled_rows)
        feature_rows = [row for row in eval_rows if row["feature"] != "global_majority"]
        best = max(
            feature_rows,
            key=lambda row: (row["delta_bits_vs_global"], row["delta_exact_vs_global"]),
        )
        best_delta_bits.append(best["delta_bits_vs_global"])
        best_delta_exact.append(best["delta_exact_vs_global"])
        best_exact.append(best["exact_ops"])
    best_delta_bits.sort()
    best_delta_exact.sort()
    best_exact.sort()
    return {
        "trials": RANDOM_TRIALS,
        "best_delta_bits_mean": mean(best_delta_bits),
        "best_delta_bits_p95": percentile(best_delta_bits, 0.95),
        "best_delta_exact_mean": mean(best_delta_exact),
        "best_delta_exact_p95": percentile(best_delta_exact, 0.95),
        "best_exact_mean": mean(best_exact),
        "best_exact_p95": percentile(best_exact, 0.95),
    }


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    frac = index - lower
    return sorted_values[lower] * (1.0 - frac) + sorted_values[upper] * frac


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    schedule = load_json(SCHEDULE_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("innovation_tape_schedule_gate", schedule)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    trigger_rows = build_rows(books, ledger["canonical_ops_by_book"])
    eval_rows = evaluate_all(trigger_rows)
    global_rows = [row for row in eval_rows if row["feature"] == "global_majority"]
    feature_rows = [row for row in eval_rows if row["feature"] != "global_majority"]
    best_global = max(global_rows, key=lambda row: row["saving_vs_lookup_bits"])
    best_feature = max(
        feature_rows,
        key=lambda row: (row["delta_bits_vs_global"], row["delta_exact_vs_global"]),
    )
    best_overall = max(eval_rows, key=lambda row: row["saving_vs_lookup_bits"])
    control = random_control(trigger_rows)
    promotes_trigger = (
        best_feature["delta_bits_vs_global"] > control["best_delta_bits_p95"]
        and best_feature["delta_exact_vs_global"] > control["best_delta_exact_p95"]
        and best_feature["saving_vs_lookup_bits"] > 0
    )
    weak_trigger = (
        not promotes_trigger
        and best_feature["delta_bits_vs_global"] > 0
        and best_feature["delta_exact_vs_global"] > 0
    )
    literal_ops = sum(1 for row in trigger_rows if row["label"] == "literal")
    copy_ops = sum(1 for row in trigger_rows if row["label"] == "copy")
    forced_literal_ops = sum(
        1
        for row in trigger_rows
        if row["label"] == "literal" and not row["copy_available"]
    )
    copy_available_literals = literal_ops - forced_literal_ops
    summary = {
        "op_count": len(trigger_rows),
        "literal_ops": literal_ops,
        "copy_ops": copy_ops,
        "forced_literal_ops_no_copy_available": forced_literal_ops,
        "copy_available_literal_ops": copy_available_literals,
        "best_overall_feature": best_overall["feature"],
        "best_overall_cutoff": best_overall["cutoff"],
        "best_overall_exact_ops": best_overall["exact_ops"],
        "best_overall_test_ops": best_overall["test_ops"],
        "best_overall_saving_vs_lookup_bits": best_overall["saving_vs_lookup_bits"],
        "best_global_cutoff": best_global["cutoff"],
        "best_global_exact_ops": best_global["exact_ops"],
        "best_global_test_ops": best_global["test_ops"],
        "best_global_saving_vs_lookup_bits": best_global["saving_vs_lookup_bits"],
        "best_feature": best_feature["feature"],
        "best_feature_cutoff": best_feature["cutoff"],
        "best_feature_exact_ops": best_feature["exact_ops"],
        "best_feature_test_ops": best_feature["test_ops"],
        "best_feature_literal_hits": best_feature["literal_hits"],
        "best_feature_test_literal_ops": best_feature["test_literal_ops"],
        "best_feature_errors": best_feature["errors"],
        "best_feature_saving_vs_lookup_bits": best_feature["saving_vs_lookup_bits"],
        "best_feature_delta_bits_vs_global": best_feature["delta_bits_vs_global"],
        "best_feature_delta_exact_vs_global": best_feature["delta_exact_vs_global"],
        "random_delta_bits_p95": control["best_delta_bits_p95"],
        "random_delta_exact_p95": control["best_delta_exact_p95"],
        "random_exact_p95": control["best_exact_p95"],
        "promotes_conditional_trigger_clue": promotes_trigger,
        "weak_conditional_trigger_clue": weak_trigger,
        "interpretation": (
            "This gate asks whether the literal/copy trigger can be predicted at "
            "known operation starts under true-prefix, target-conditioned copy "
            "availability. It is a dependency-reduction test for op type, not a "
            "closed-loop generator or skeleton derivation."
        ),
    }
    return {
        "schema": "tape_trigger_policy_gate_v1",
        "scope": "analysis_only_conditional_literal_copy_trigger_at_known_op_starts",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "innovation_tape_schedule_gate": rel(SCHEDULE_GATE),
        },
        "rows": eval_rows,
        "random_control": control,
        "summary": summary,
        "classification": (
            "conditional_tape_trigger_clue_promoted"
            if promotes_trigger
            else (
                "conditional_tape_trigger_clue_weak"
                if weak_trigger
                else "conditional_tape_trigger_policy_rejected"
            )
        ),
        "decision": {
            "promotes_conditional_trigger_clue": promotes_trigger,
            "weak_conditional_trigger_clue": weak_trigger,
            "generator_status": "not_promoted",
            "skeleton_status": "not_derived",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Tape Trigger Policy Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether literal-vs-copy trigger decisions can be predicted at",
        "known operation starts using true-prefix, target-conditioned copy",
        "availability features. This is explicitly not a closed-loop generator.",
        "",
        "## Summary",
        "",
        f"- Operation starts: `{s['op_count']}`.",
        f"- Literal ops: `{s['literal_ops']}`.",
        f"- Copy ops: `{s['copy_ops']}`.",
        f"- Literal ops with no copy available: `{s['forced_literal_ops_no_copy_available']}`.",
        f"- Literal ops despite copy availability: `{s['copy_available_literal_ops']}`.",
        f"- Best overall feature: `{s['best_overall_feature']}`.",
        f"- Best overall cutoff: `{s['best_overall_cutoff']}`.",
        f"- Best overall exact ops: `{s['best_overall_exact_ops']}/{s['best_overall_test_ops']}`.",
        f"- Best overall saving vs literal-site lookup: `{s['best_overall_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best global exact ops: `{s['best_global_exact_ops']}/{s['best_global_test_ops']}`.",
        f"- Best global saving vs literal-site lookup: `{s['best_global_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best feature over global: `{s['best_feature']}`.",
        f"- Best feature cutoff: `{s['best_feature_cutoff']}`.",
        f"- Best feature exact ops: `{s['best_feature_exact_ops']}/{s['best_feature_test_ops']}`.",
        f"- Best feature literal hits: `{s['best_feature_literal_hits']}/{s['best_feature_test_literal_ops']}`.",
        f"- Best feature errors: `{s['best_feature_errors']}`.",
        f"- Best feature saving vs lookup: `{s['best_feature_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best feature delta vs global: `{s['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Best feature exact delta vs global: `{s['best_feature_delta_exact_vs_global']}`.",
        f"- Random delta bits p95: `{s['random_delta_bits_p95']:.3f}`.",
        f"- Random delta exact p95: `{s['random_delta_exact_p95']:.3f}`.",
        f"- Random exact p95: `{s['random_exact_p95']:.3f}`.",
        f"- Promotes conditional trigger clue: `{s['promotes_conditional_trigger_clue']}`.",
        f"- Weak conditional trigger clue: `{s['weak_conditional_trigger_clue']}`.",
        "",
        s["interpretation"],
        "",
        "## Best Rows",
        "",
        "| Cutoff | Feature | Exact | Literals hit | Errors | Lookup bits | Total bits | Saving | Delta bits | Delta exact | Contexts |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(
        result["rows"],
        key=lambda item: (item["delta_bits_vs_global"], item["saving_vs_lookup_bits"]),
        reverse=True,
    )[:12]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['feature']}` | "
            f"`{row['exact_ops']}/{row['test_ops']}` | "
            f"`{row['literal_hits']}/{row['test_literal_ops']}` | "
            f"`{row['errors']}` | `{row['lookup_bits']:.3f}` | "
            f"`{row['total_bits']:.3f}` | `{row['saving_vs_lookup_bits']:.3f}` | "
            f"`{row['delta_bits_vs_global']:.3f}` | "
            f"`{row['delta_exact_vs_global']}` | `{row['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- A trigger policy is promoted only if a non-global feature beats the global copy-majority baseline and shuffled-label controls after table/correction cost.",
            "- The promoted clue is conditional on known operation starts and target-conditioned copy availability.",
            "- It reduces the declared literal/copy trigger dependency under those grants, but does not derive the skeleton, source, length, or closed-loop digit stream.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
