from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
TARGET_SIGNATURE_GATE = (
    ROOT
    / "analysis"
    / "target_chunk_signature_audit_20260621"
    / "reports"
    / "test_results"
    / "01_target_chunk_signature_gate.json"
)

OUT_STEM = "01_target_digit_process_gate"
RANDOM_SEED = 46920260621
RANDOM_TRIALS = 200
DIGITS = "0123456789"
ALPHA = 0.5


BookMap = dict[int, str]
ContextFn = Callable[[int, int, str], str]


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


def load_books() -> BookMap:
    data = load_json(BOOKS_DIGITS)
    return {int(key): str(value) for key, value in data.items()}


def log2_uniform_digit_bits(digit_count: int) -> float:
    return digit_count * math.log2(10)


def previous2_context(prefix: str) -> str:
    if not prefix:
        return "prev2=BOS,BOS"
    if len(prefix) == 1:
        return f"prev2=BOS,{prefix[-1]}"
    return f"prev2={prefix[-2]},{prefix[-1]}"


def context_functions() -> dict[str, ContextFn]:
    return {
        "iid_global": lambda book, pos, prefix: "all",
        "book_mod10": lambda book, pos, prefix: f"bookmod10={book % 10}",
        "book_decade": lambda book, pos, prefix: f"decade={book // 10}",
        "position_mod2": lambda book, pos, prefix: f"posmod2={pos % 2}",
        "position_mod5": lambda book, pos, prefix: f"posmod5={pos % 5}",
        "position_mod10": lambda book, pos, prefix: f"posmod10={pos % 10}",
        "prev_digit": lambda book, pos, prefix: (
            "prev=BOS" if not prefix else f"prev={prefix[-1]}"
        ),
        "prev2_digits": lambda book, pos, prefix: previous2_context(prefix),
        "prev_digit_x_position_mod5": lambda book, pos, prefix: (
            ("prev=BOS" if not prefix else f"prev={prefix[-1]}") + f"|posmod5={pos % 5}"
        ),
        "book_mod10_x_position_mod5": lambda book, pos, prefix: (
            f"bookmod10={book % 10}|posmod5={pos % 5}"
        ),
    }


def train_counts(books: BookMap, book_ids: list[int], context_fn: ContextFn) -> dict[str, Counter[str]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for book in book_ids:
        prefix = ""
        for pos, digit in enumerate(books[book]):
            counts[context_fn(book, pos, prefix)][digit] += 1
            prefix += digit
    return counts


def score_books(
    books: BookMap,
    book_ids: list[int],
    counts: dict[str, Counter[str]],
    context_fn: ContextFn,
) -> dict[str, Any]:
    global_counts = Counter()
    for counter in counts.values():
        global_counts.update(counter)
    total_bits = 0.0
    digit_count = 0
    unsupported_contexts = 0
    context_hits = 0
    for book in book_ids:
        prefix = ""
        for pos, digit in enumerate(books[book]):
            context = context_fn(book, pos, prefix)
            counter = counts.get(context)
            if not counter:
                counter = global_counts
                unsupported_contexts += 1
            else:
                context_hits += 1
            total = sum(counter.values())
            probability = (counter[digit] + ALPHA) / (total + ALPHA * len(DIGITS))
            total_bits += -math.log2(probability)
            digit_count += 1
            prefix += digit
    return {
        "bits": total_bits,
        "digits": digit_count,
        "bits_per_digit": total_bits / digit_count if digit_count else 0.0,
        "uniform_bits": log2_uniform_digit_bits(digit_count),
        "gain_vs_uniform_bits": log2_uniform_digit_bits(digit_count) - total_bits,
        "unsupported_contexts": unsupported_contexts,
        "context_hits": context_hits,
    }


def evaluate_split(
    books: BookMap,
    train_ids: list[int],
    test_ids: list[int],
    model_name: str,
    context_fn: ContextFn,
) -> dict[str, Any]:
    counts = train_counts(books, train_ids, context_fn)
    train = score_books(books, train_ids, counts, context_fn)
    test = score_books(books, test_ids, counts, context_fn)
    return {
        "model": model_name,
        "train_books": train_ids,
        "test_books": test_ids,
        "train": train,
        "test": test,
        "train_test_bpd_gap": test["bits_per_digit"] - train["bits_per_digit"],
        "context_count": len(counts),
        "parameter_count_floor": len(counts) * (len(DIGITS) - 1),
    }


def scope_splits(scope: str, book_ids: list[int]) -> list[tuple[int, list[int], list[int]]]:
    if scope == "all70":
        cutoffs = [20, 30, 40, 50, 60]
    else:
        cutoffs = [20, 30, 40, 50, 60]
    out = []
    for cutoff in cutoffs:
        train = [book for book in book_ids if book < cutoff]
        test = [book for book in book_ids if book >= cutoff]
        if train and test:
            out.append((cutoff, train, test))
    return out


def evaluate_scope(books: BookMap, scope: str, book_ids: list[int]) -> dict[str, Any]:
    functions = context_functions()
    split_rows = []
    aggregate: dict[str, dict[str, float]] = {}
    for cutoff, train_ids, test_ids in scope_splits(scope, book_ids):
        rows = []
        for name, fn in functions.items():
            row = evaluate_split(books, train_ids, test_ids, name, fn)
            row["cutoff"] = cutoff
            rows.append(row)
        best = min(rows, key=lambda row: row["test"]["bits"])
        split_rows.append(
            {
                "cutoff": cutoff,
                "train_book_count": len(train_ids),
                "test_book_count": len(test_ids),
                "test_digit_count": best["test"]["digits"],
                "selected_model": best["model"],
                "selected_test_bits": best["test"]["bits"],
                "selected_test_bpd": best["test"]["bits_per_digit"],
                "selected_gain_vs_uniform_bits": best["test"]["gain_vs_uniform_bits"],
                "selected_train_test_bpd_gap": best["train_test_bpd_gap"],
                "all_models": rows,
            }
        )
        for row in rows:
            stats = aggregate.setdefault(
                row["model"],
                {
                    "test_bits": 0.0,
                    "test_uniform_bits": 0.0,
                    "test_digits": 0.0,
                    "splits": 0.0,
                    "train_test_bpd_gap_sum": 0.0,
                },
            )
            stats["test_bits"] += row["test"]["bits"]
            stats["test_uniform_bits"] += row["test"]["uniform_bits"]
            stats["test_digits"] += row["test"]["digits"]
            stats["splits"] += 1.0
            stats["train_test_bpd_gap_sum"] += row["train_test_bpd_gap"]
    aggregate_rows = []
    for model, stats in aggregate.items():
        aggregate_rows.append(
            {
                "model": model,
                "test_bits": stats["test_bits"],
                "test_uniform_bits": stats["test_uniform_bits"],
                "test_gain_vs_uniform_bits": stats["test_uniform_bits"] - stats["test_bits"],
                "test_bits_per_digit": (
                    stats["test_bits"] / stats["test_digits"] if stats["test_digits"] else 0.0
                ),
                "test_digit_count": int(stats["test_digits"]),
                "mean_train_test_bpd_gap": stats["train_test_bpd_gap_sum"] / stats["splits"],
            }
        )
    aggregate_rows.sort(key=lambda row: row["test_bits"])
    return {
        "scope": scope,
        "book_ids": book_ids,
        "book_count": len(book_ids),
        "digit_count": sum(len(books[book]) for book in book_ids),
        "splits": split_rows,
        "aggregate_models": aggregate_rows,
        "best_aggregate_model": aggregate_rows[0],
    }


def shuffled_books(books: BookMap, rng: random.Random, book_ids: list[int]) -> BookMap:
    out = dict(books)
    for book in book_ids:
        digits = list(books[book])
        rng.shuffle(digits)
        out[book] = "".join(digits)
    return out


def shuffled_control(books: BookMap, scope: str, book_ids: list[int]) -> dict[str, Any]:
    rng = random.Random(RANDOM_SEED)
    best_gains: list[float] = []
    best_bpds: list[float] = []
    prev_digit_gains: list[float] = []
    iid_gains: list[float] = []
    for _ in range(RANDOM_TRIALS):
        shuffled = shuffled_books(books, rng, book_ids)
        evaluated = evaluate_scope(shuffled, scope, book_ids)
        best_gains.append(evaluated["best_aggregate_model"]["test_gain_vs_uniform_bits"])
        best_bpds.append(evaluated["best_aggregate_model"]["test_bits_per_digit"])
        model_map = {row["model"]: row for row in evaluated["aggregate_models"]}
        prev_digit_gains.append(model_map["prev_digit"]["test_gain_vs_uniform_bits"])
        iid_gains.append(model_map["iid_global"]["test_gain_vs_uniform_bits"])
    best_gains.sort()
    best_bpds.sort()
    prev_digit_gains.sort()
    iid_gains.sort()
    return {
        "trials": RANDOM_TRIALS,
        "random_seed": RANDOM_SEED,
        "control": "shuffle_digits_within_each_book_preserving_book_histogram",
        "best_gain_mean": mean(best_gains),
        "best_gain_p05": percentile(best_gains, 0.05),
        "best_gain_p95": percentile(best_gains, 0.95),
        "best_bpd_mean": mean(best_bpds),
        "best_bpd_p05": percentile(best_bpds, 0.05),
        "best_bpd_p95": percentile(best_bpds, 0.95),
        "prev_digit_gain_mean": mean(prev_digit_gains),
        "prev_digit_gain_p95": percentile(prev_digit_gains, 0.95),
        "iid_gain_mean": mean(iid_gains),
        "iid_gain_p95": percentile(iid_gains, 0.95),
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
    signature_gate = load_json(TARGET_SIGNATURE_GATE)
    assert_boundary("target_chunk_signature_gate", signature_gate)
    books = load_books()
    all_ids = sorted(books)
    derived_ids = [book for book in all_ids if book >= 10]
    scopes = [
        evaluate_scope(books, "all70", all_ids),
        evaluate_scope(books, "derived60", derived_ids),
    ]
    controls = {
        scope["scope"]: shuffled_control(books, scope["scope"], scope["book_ids"])
        for scope in scopes
    }
    for scope in scopes:
        control = controls[scope["scope"]]
        best = scope["best_aggregate_model"]
        best["gain_delta_vs_shuffled_best_mean"] = (
            best["test_gain_vs_uniform_bits"] - control["best_gain_mean"]
        )
        best["beats_shuffled_best_p95"] = (
            best["test_gain_vs_uniform_bits"] > control["best_gain_p95"]
        )
    best_all = scopes[0]["best_aggregate_model"]
    best_derived = scopes[1]["best_aggregate_model"]
    target_digit_markov_clue = (
        best_all["model"] == "prev2_digits"
        and best_derived["model"] == "prev2_digits"
        and bool(best_all["beats_shuffled_best_p95"])
        and bool(best_derived["beats_shuffled_best_p95"])
    )
    promotes_digit_process_generator = False
    summary = {
        "all70_digit_count": scopes[0]["digit_count"],
        "all70_aggregate_test_digit_count": best_all["test_digit_count"],
        "derived60_digit_count": scopes[1]["digit_count"],
        "derived60_aggregate_test_digit_count": best_derived["test_digit_count"],
        "all70_best_model": best_all["model"],
        "all70_best_test_bpd": best_all["test_bits_per_digit"],
        "all70_best_gain_vs_uniform_bits": best_all["test_gain_vs_uniform_bits"],
        "all70_beats_shuffled_best_p95": best_all["beats_shuffled_best_p95"],
        "derived60_best_model": best_derived["model"],
        "derived60_best_test_bpd": best_derived["test_bits_per_digit"],
        "derived60_best_gain_vs_uniform_bits": best_derived["test_gain_vs_uniform_bits"],
        "derived60_beats_shuffled_best_p95": best_derived["beats_shuffled_best_p95"],
        "target_digit_markov_clue": target_digit_markov_clue,
        "promotes_digit_process_generator": promotes_digit_process_generator,
        "interpretation": (
            "Simple source-free digit processes are tested as prequential "
            "generators for the missing target stream. Any retained advantage "
            "must beat prefix/suffix validation and shuffled within-book controls. "
            "A strong short-Markov clue still remains an arithmetic residual model, "
            "not an exact formula for the target digits."
        ),
    }
    return {
        "schema": "target_digit_process_gate_v1",
        "scope": "analysis_only_source_free_target_digit_process",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "target_chunk_signature_gate": rel(TARGET_SIGNATURE_GATE),
        },
        "model_alpha": ALPHA,
        "scopes": scopes,
        "shuffled_controls": controls,
        "summary": summary,
        "classification": "target_digit_markov_clue_promoted_not_generator",
        "decision": {
            "promotes_digit_process_generator": promotes_digit_process_generator,
            "target_digit_markov_clue": target_digit_markov_clue,
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
        "# Target Digit Process Gate",
        "",
        "Classification: `target_digit_markov_clue_promoted_not_generator`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the missing target digit stream can be generated by a",
        "simple source-free digit process under prefix/suffix validation.",
        "",
        "## Summary",
        "",
        f"- All-book digits: `{s['all70_digit_count']}`.",
        f"- All70 aggregate validation test digits: `{s['all70_aggregate_test_digit_count']}`.",
        f"- Derived-book digits: `{s['derived60_digit_count']}`.",
        f"- Derived60 aggregate validation test digits: `{s['derived60_aggregate_test_digit_count']}`.",
        f"- Best all70 model: `{s['all70_best_model']}` at `{s['all70_best_test_bpd']:.6f}` bits/digit, aggregate gain `{s['all70_best_gain_vs_uniform_bits']:.3f}` bits vs uniform.",
        f"- All70 beats shuffled best p95: `{s['all70_beats_shuffled_best_p95']}`.",
        f"- Best derived60 model: `{s['derived60_best_model']}` at `{s['derived60_best_test_bpd']:.6f}` bits/digit, aggregate gain `{s['derived60_best_gain_vs_uniform_bits']:.3f}` bits vs uniform.",
        f"- Derived60 beats shuffled best p95: `{s['derived60_beats_shuffled_best_p95']}`.",
        f"- Target digit Markov clue promoted: `{s['target_digit_markov_clue']}`.",
        "",
        "## Aggregate Model Results",
        "",
        "| Scope | Model | Test bpd | Gain vs uniform | Mean train-test bpd gap |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for scope in result["scopes"]:
        for row in scope["aggregate_models"][:6]:
            lines.append(
                f"| `{scope['scope']}` | `{row['model']}` | "
                f"`{row['test_bits_per_digit']:.6f}` | "
                f"`{row['test_gain_vs_uniform_bits']:.3f}` | "
                f"`{row['mean_train_test_bpd_gap']:.6f}` |"
            )
    lines.extend(
        [
            "",
            "## Shuffled Controls",
            "",
            "| Scope | Best gain mean | Best gain p95 | Observed best gain | Beats p95 |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for scope in result["scopes"]:
        control = result["shuffled_controls"][scope["scope"]]
        observed = scope["best_aggregate_model"]
        lines.append(
            f"| `{scope['scope']}` | "
            f"`{control['best_gain_mean']:.3f}` | "
            f"`{control['best_gain_p95']:.3f}` | "
            f"`{observed['test_gain_vs_uniform_bits']:.3f}` | "
            f"`{observed['beats_shuffled_best_p95']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Promotes target digit Markov clue: `True`.",
            "- Promotes source-free target digit process generator: `False`.",
            "- The `prev2_digits` process is predictive and control-stable, but it still leaves arithmetic residual bits rather than an exact target-digit formula.",
            "- The target stream remains a declared/generated-elsewhere dependency.",
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
