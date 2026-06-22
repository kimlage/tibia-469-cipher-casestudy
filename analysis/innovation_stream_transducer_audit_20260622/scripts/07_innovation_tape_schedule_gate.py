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
SEED_WALK_GATE = TEST_RESULTS / "06_seed_walk_source_model_gate.json"

OUT_STEM = "07_innovation_tape_schedule_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_SEED = 46920260622
RANDOM_TRIALS = 1000
ALPHA = 0.5
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


def count_bits(max_value: int) -> float:
    return math.log2(max_value + 1)


def literal_counts_by_book(ops_by_book: dict[str, list[dict[str, Any]]]) -> dict[int, int]:
    out = {}
    for book in range(10, 70):
        total = 0
        for op in ops_by_book[str(book)]:
            if op["type"] == "literal":
                total += int(op["length"])
        out[book] = total
    return out


def longest_match(emitted: str, target: str, pos: int) -> int:
    if pos + MIN_COPY_LEN > len(target):
        return 0
    needle = target[pos : pos + MIN_COPY_LEN]
    source = emitted.find(needle)
    best = 0
    while source != -1:
        length = MIN_COPY_LEN
        cap = min(len(target) - pos, len(emitted) - source)
        while length < cap and emitted[source + length] == target[pos + length]:
            length += 1
        best = max(best, length)
        source = emitted.find(needle, source + 1)
    return best


def greedy_copy_residual_counts(books: dict[int, str]) -> dict[int, int]:
    emitted = "".join(books[book] for book in range(10))
    out = {}
    for book in range(10, 70):
        target = books[book]
        pos = 0
        residual = 0
        while pos < len(target):
            length = longest_match(emitted + target[:pos], target, pos)
            if length >= MIN_COPY_LEN:
                pos += length
            else:
                residual += 1
                pos += 1
        out[book] = residual
        emitted += target
    return out


def bucket(value: int, cuts: list[int], prefix: str) -> str:
    for cut in cuts:
        if value <= cut:
            return f"{prefix}_le_{cut}"
    return f"{prefix}_gt_{cuts[-1]}"


def feature_value(book: int, books: dict[int, str], greedy_residual: dict[int, int], name: str) -> str:
    if name == "book_mod10":
        return f"book_mod10_{book % 10}"
    if name == "book_decade":
        return f"book_decade_{book // 10}"
    if name == "length_bucket":
        return bucket(len(books[book]), [80, 120, 160, 220], "len")
    if name == "greedy_residual_bucket":
        return bucket(greedy_residual[book], [0, 2, 5, 10, 20, 40], "gres")
    if name == "length_x_greedy":
        return (
            feature_value(book, books, greedy_residual, "length_bucket")
            + "|"
            + feature_value(book, books, greedy_residual, "greedy_residual_bucket")
        )
    raise KeyError(name)


FEATURES = [
    "global_majority",
    "book_mod10",
    "book_decade",
    "length_bucket",
    "greedy_residual_bucket",
    "length_x_greedy",
]


def train_predictor(
    train_books: list[int],
    books: dict[int, str],
    greedy_residual: dict[int, int],
    literal_counts: dict[int, int],
    feature: str,
) -> tuple[dict[str, int], int]:
    global_counts = Counter(literal_counts[book] for book in train_books)
    default = global_counts.most_common(1)[0][0] if global_counts else 0
    if feature == "global_majority":
        return {}, default
    by_feature: dict[str, Counter[int]] = defaultdict(Counter)
    for book in train_books:
        by_feature[feature_value(book, books, greedy_residual, feature)][literal_counts[book]] += 1
    table = {
        key: counter.most_common(1)[0][0]
        for key, counter in by_feature.items()
    }
    return table, default


def predict_count(
    book: int,
    books: dict[int, str],
    greedy_residual: dict[int, int],
    table: dict[str, int],
    default: int,
    feature: str,
) -> int:
    if feature == "global_majority":
        return default
    return table.get(feature_value(book, books, greedy_residual, feature), default)


def correction_bits(actual: int, predicted: int, max_value: int) -> float:
    if actual == predicted:
        return 0.0
    return 1.0 + math.log2(max_value + 1)


def evaluate_feature(
    cutoff: int,
    books: dict[int, str],
    greedy_residual: dict[int, int],
    literal_counts: dict[int, int],
    feature: str,
) -> dict[str, Any]:
    train = list(range(10, cutoff))
    test = list(range(cutoff, 70))
    table, default = train_predictor(train, books, greedy_residual, literal_counts, feature)
    table_bits = len(table) * math.log2(max(literal_counts.values()) + 1)
    exact = 0
    baseline_bits = 0.0
    correction = 0.0
    absolute_error = 0
    for book in test:
        max_value = len(books[book])
        baseline_bits += count_bits(max_value)
        predicted = predict_count(book, books, greedy_residual, table, default, feature)
        actual = literal_counts[book]
        exact += int(predicted == actual)
        absolute_error += abs(predicted - actual)
        correction += correction_bits(actual, predicted, max_value)
    total = correction + table_bits
    return {
        "cutoff": cutoff,
        "feature": feature,
        "test_books": len(test),
        "context_count": len(table),
        "table_bits": table_bits,
        "baseline_bits": baseline_bits,
        "correction_bits": correction,
        "total_bits": total,
        "saving_vs_baseline_bits": baseline_bits - total,
        "exact_books": exact,
        "absolute_error": absolute_error,
    }


def random_control(literal_counts: dict[int, int]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    values = []
    books = list(range(10, 70))
    labels = [literal_counts[book] for book in books]
    for _ in range(RANDOM_TRIALS):
        rng.shuffle(labels)
        shuffled = dict(zip(books, labels))
        best = 0
        for cutoff in PREFIX_CUTOFFS:
            train = list(range(10, cutoff))
            test = list(range(cutoff, 70))
            majority = Counter(shuffled[book] for book in train).most_common(1)[0][0]
            exact = sum(1 for book in test if shuffled[book] == majority)
            best = max(best, exact)
        values.append(best)
    values.sort()
    return {
        "trials": RANDOM_TRIALS,
        "exact_mean": mean(values),
        "exact_p95": percentile(values, 0.95),
        "exact_max": values[-1],
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
    seed_walk = load_json(SEED_WALK_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("seed_walk_source_model_gate", seed_walk)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    literal_counts = literal_counts_by_book(ledger["canonical_ops_by_book"])
    greedy_residual = greedy_copy_residual_counts(books)
    rows = []
    for cutoff in PREFIX_CUTOFFS:
        for feature in FEATURES:
            rows.append(evaluate_feature(cutoff, books, greedy_residual, literal_counts, feature))
    global_rows = [row for row in rows if row["feature"] == "global_majority"]
    best_global = max(global_rows, key=lambda row: row["saving_vs_baseline_bits"])
    feature_rows = [row for row in rows if row["feature"] != "global_majority"]
    best_feature = max(
        feature_rows,
        key=lambda row: (
            row["saving_vs_baseline_bits"] - best_global["saving_vs_baseline_bits"],
            row["exact_books"] - best_global["exact_books"],
        ),
    )
    best = max(rows, key=lambda row: (row["saving_vs_baseline_bits"], row["exact_books"]))
    control = random_control(literal_counts)
    feature_delta_bits = best_feature["saving_vs_baseline_bits"] - best_global["saving_vs_baseline_bits"]
    feature_delta_exact = best_feature["exact_books"] - best_global["exact_books"]
    promotes_schedule = (
        feature_delta_bits > 0
        and feature_delta_exact > 0
        and best_feature["exact_books"] > control["exact_p95"]
    )
    weak_schedule = best_global["saving_vs_baseline_bits"] > 0
    literal_total = sum(literal_counts.values())
    summary = {
        "literal_tape_digits": literal_total,
        "books_with_literal_digits": sum(1 for value in literal_counts.values() if value),
        "best_feature": best["feature"],
        "best_cutoff": best["cutoff"],
        "best_exact_books": best["exact_books"],
        "best_test_books": best["test_books"],
        "best_absolute_error": best["absolute_error"],
        "best_baseline_bits": best["baseline_bits"],
        "best_total_bits": best["total_bits"],
        "best_saving_vs_baseline_bits": best["saving_vs_baseline_bits"],
        "best_global_cutoff": best_global["cutoff"],
        "best_global_exact_books": best_global["exact_books"],
        "best_global_test_books": best_global["test_books"],
        "best_global_saving_vs_baseline_bits": best_global["saving_vs_baseline_bits"],
        "best_feature_over_global": best_feature["feature"],
        "best_feature_delta_bits": feature_delta_bits,
        "best_feature_delta_exact": feature_delta_exact,
        "random_exact_p95": control["exact_p95"],
        "promotes_schedule_model": promotes_schedule,
        "weak_schedule_clue": weak_schedule,
        "interpretation": (
            "This gate asks whether the per-book innovation tape consumption "
            "schedule can be predicted from online mechanical features beyond a "
            "global zero-consumption/sparsity baseline."
        ),
    }
    return {
        "schema": "innovation_tape_schedule_gate_v1",
        "scope": "analysis_only_per_book_tape_consumption_schedule",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "seed_walk_source_model_gate": rel(SEED_WALK_GATE),
        },
        "rows": rows,
        "summary": summary,
        "classification": (
            "innovation_tape_schedule_feature_promoted"
            if promotes_schedule
            else (
                "innovation_tape_schedule_sparsity_weak_clue"
                if weak_schedule
                else "innovation_tape_schedule_rejected"
            )
        ),
        "decision": {
            "promotes_schedule_model": promotes_schedule,
            "weak_schedule_clue": weak_schedule,
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
        "# Innovation Tape Schedule Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether per-book consumption counts for the innovation tape can be",
        "predicted from online mechanical features rather than declared as an",
        "external schedule.",
        "",
        "## Summary",
        "",
        f"- Literal tape digits: `{s['literal_tape_digits']}`.",
        f"- Books with literal digits: `{s['books_with_literal_digits']}`.",
        f"- Best feature: `{s['best_feature']}`.",
        f"- Best cutoff: `{s['best_cutoff']}`.",
        f"- Best exact books: `{s['best_exact_books']}/{s['best_test_books']}`.",
        f"- Best absolute error: `{s['best_absolute_error']}`.",
        f"- Best baseline bits: `{s['best_baseline_bits']:.3f}`.",
        f"- Best total bits: `{s['best_total_bits']:.3f}`.",
        f"- Best saving vs baseline: `{s['best_saving_vs_baseline_bits']:.3f}`.",
        f"- Best global-majority exact books: `{s['best_global_exact_books']}/{s['best_global_test_books']}`.",
        f"- Best global-majority saving: `{s['best_global_saving_vs_baseline_bits']:.3f}`.",
        f"- Best feature over global: `{s['best_feature_over_global']}`.",
        f"- Best feature delta bits: `{s['best_feature_delta_bits']:.3f}`.",
        f"- Best feature delta exact: `{s['best_feature_delta_exact']}`.",
        f"- Random exact p95: `{s['random_exact_p95']:.3f}`.",
        f"- Promotes schedule model: `{s['promotes_schedule_model']}`.",
        f"- Weak schedule clue: `{s['weak_schedule_clue']}`.",
        "",
        s["interpretation"],
        "",
        "## Best Rows",
        "",
        "| Cutoff | Feature | Exact | Baseline bits | Total bits | Saving | Abs error | Contexts |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(
        result["rows"],
        key=lambda item: item["saving_vs_baseline_bits"],
        reverse=True,
    )[:10]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['feature']}` | "
            f"`{row['exact_books']}/{row['test_books']}` | "
            f"`{row['baseline_bits']:.3f}` | `{row['total_bits']:.3f}` | "
            f"`{row['saving_vs_baseline_bits']:.3f}` | "
            f"`{row['absolute_error']}` | `{row['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- A schedule feature is promoted only if it improves over global-majority sparsity and beats random exact controls.",
            "- Global sparsity may be retained as a weak clue but does not generate the transducer by itself.",
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
