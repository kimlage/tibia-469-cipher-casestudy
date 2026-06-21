from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

LEDGER = TEST_RESULTS / "01_book_length_ledger.json"
OUT_STEM = "02_book_length_generation_gate"
PREFIX_CUTOFFS = [10, 20, 30, 40, 50, 60]


Row = dict[str, Any]
PredictFn = Callable[[list[Row], Row], int]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") != "unchanged_exogenous":
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def signed_gamma_bits(delta: int) -> int:
    value = abs(delta) + 1
    return 2 * int(math.floor(math.log2(value))) + 1 + (0 if delta == 0 else 1)


def majority(values: list[int]) -> int:
    counts = Counter(values)
    return min(counts, key=lambda value: (-counts[value], value))


def round_int(value: float) -> int:
    return int(round(value))


def linear_predict(train: list[Row], row: Row) -> int:
    xs = [int(item["book"]) for item in train]
    ys = [int(item["length"]) for item in train]
    if len(xs) < 2:
        return ys[-1]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return round_int(y_mean)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
    intercept = y_mean - slope * x_mean
    return max(1, round_int(intercept + slope * int(row["book"])))


def previous_same_mod(train: list[Row], row: Row) -> int:
    mod = int(row["book"]) % 10
    for item in reversed(train):
        if int(item["book"]) % 10 == mod:
            return int(item["length"])
    return int(train[-1]["length"])


def mod10_majority(train: list[Row], row: Row) -> int:
    mod = int(row["book"]) % 10
    values = [int(item["length"]) for item in train if int(item["book"]) % 10 == mod]
    if not values:
        values = [int(item["length"]) for item in train]
    return majority(values)


def mod10_median(train: list[Row], row: Row) -> int:
    mod = int(row["book"]) % 10
    values = [int(item["length"]) for item in train if int(item["book"]) % 10 == mod]
    if not values:
        values = [int(item["length"]) for item in train]
    return max(1, int(round(median(values))))


def policy_specs() -> dict[str, PredictFn]:
    return {
        "train_median": lambda train, row: max(
            1, int(round(median([int(item["length"]) for item in train])))
        ),
        "train_majority": lambda train, row: majority(
            [int(item["length"]) for item in train]
        ),
        "previous_length": lambda train, row: int(train[-1]["length"]),
        "previous_same_book_mod10": previous_same_mod,
        "book_mod10_majority": mod10_majority,
        "book_mod10_median": mod10_median,
        "linear_index_fit": linear_predict,
        "active_anchor_151": lambda train, row: 151,
    }


def evaluate(rows: list[Row], train: list[Row], name: str, fn: PredictFn) -> dict[str, Any]:
    predictions = []
    residual_bits = 0
    exact = 0
    abs_error = 0
    max_abs_error = 0
    for row in rows:
        predicted = fn(train, row)
        actual = int(row["length"])
        err = actual - predicted
        hit = err == 0
        exact += 1 if hit else 0
        abs_error += abs(err)
        max_abs_error = max(max_abs_error, abs(err))
        residual_bits += signed_gamma_bits(err)
        predictions.append(
            {
                "book": row["book"],
                "actual": actual,
                "predicted": predicted,
                "error": err,
                "exact": hit,
            }
        )
    return {
        "policy": name,
        "row_count": len(rows),
        "exact_lengths": exact,
        "total_abs_error": abs_error,
        "mean_abs_error": abs_error / len(rows) if rows else 0.0,
        "max_abs_error": max_abs_error,
        "signed_gamma_residual_bits": residual_bits,
        "rows": predictions,
    }


def context_lookup_full_fit(rows: list[Row]) -> list[dict[str, Any]]:
    contexts: dict[str, Callable[[Row], str]] = {
        "book_mod10": lambda row: f"bookmod10={int(row['book']) % 10}",
        "book_mod7": lambda row: f"bookmod7={int(row['book']) % 7}",
        "book_decade": lambda row: f"decade={int(row['book']) // 10}",
        "book_parity": lambda row: f"parity={int(row['book']) % 2}",
        "book_index_lookup": lambda row: f"book={row['book']}",
    }
    out = []
    for name, fn in contexts.items():
        groups: dict[str, list[int]] = defaultdict(list)
        for row in rows:
            groups[fn(row)].append(int(row["length"]))
        mapping = {key: majority(values) for key, values in groups.items()}
        scored = []
        for row in rows:
            predicted = mapping[fn(row)]
            scored.append(
                {
                    "book": row["book"],
                    "actual": row["length"],
                    "predicted": predicted,
                    "exact": predicted == int(row["length"]),
                }
            )
        table_length_payloads = len(mapping)
        out.append(
            {
                "context": name,
                "context_count": len(mapping),
                "exact_lengths": sum(1 for row in scored if row["exact"]),
                "row_count": len(scored),
                "length_payloads_carried": table_length_payloads,
                "source_bearing_lookup": table_length_payloads > 1,
            }
        )
    out.sort(key=lambda row: (row["exact_lengths"], -row["context_count"]), reverse=True)
    return out


def prequential(rows: list[Row]) -> list[dict[str, Any]]:
    specs = policy_specs()
    result = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        train_scores = [evaluate(train, train, name, fn) for name, fn in specs.items()]
        selected = max(
            train_scores,
            key=lambda row: (
                row["exact_lengths"],
                -row["mean_abs_error"],
                -row["signed_gamma_residual_bits"],
                row["policy"],
            ),
        )
        selected_fn = specs[selected["policy"]]
        test_score = evaluate(test, train, selected["policy"], selected_fn)
        oracle_scores = [evaluate(test, train, name, fn) for name, fn in specs.items()]
        oracle = max(
            oracle_scores,
            key=lambda row: (
                row["exact_lengths"],
                -row["mean_abs_error"],
                -row["signed_gamma_residual_bits"],
                row["policy"],
            ),
        )
        result.append(
            {
                "cutoff_book": cutoff,
                "selected_policy": selected["policy"],
                "train_exact_lengths": selected["exact_lengths"],
                "train_row_count": selected["row_count"],
                "test_exact_lengths": test_score["exact_lengths"],
                "test_row_count": test_score["row_count"],
                "test_mean_abs_error": test_score["mean_abs_error"],
                "test_signed_gamma_residual_bits": test_score["signed_gamma_residual_bits"],
                "oracle_policy": oracle["policy"],
                "oracle_test_exact_lengths": oracle["exact_lengths"],
                "oracle_test_mean_abs_error": oracle["mean_abs_error"],
                "selected_matches_oracle": (
                    test_score["exact_lengths"] == oracle["exact_lengths"]
                    and test_score["mean_abs_error"] == oracle["mean_abs_error"]
                ),
            }
        )
    return result


def make_result() -> dict[str, Any]:
    ledger = load_json(LEDGER)
    assert_boundary("book_length_ledger", ledger)
    rows = list(ledger["length_rows"])
    specs = policy_specs()
    full_scores = [evaluate(rows, rows, name, fn) for name, fn in specs.items()]
    full_scores.sort(
        key=lambda row: (
            row["exact_lengths"],
            -row["mean_abs_error"],
            -row["signed_gamma_residual_bits"],
            row["policy"],
        ),
        reverse=True,
    )
    lookup_scores = context_lookup_full_fit(rows)
    preq = prequential(rows)
    best = full_scores[0]
    promoted = (
        best["exact_lengths"] == best["row_count"]
        and all(row["test_exact_lengths"] == row["test_row_count"] for row in preq)
    )
    classification = (
        "book_length_generator_promoted"
        if promoted
        else "book_length_generator_rejected"
    )
    return {
        "schema": "book_length_generation_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {"book_length_ledger": str(LEDGER.relative_to(ROOT))},
        "scope": {
            "analysis_only": True,
            "tested_full_fit_simple_policies": True,
            "tested_prefix_holdout": True,
            "context_lookup_marked_source_bearing": True,
            "compression_bound_changed": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "book_count": len(rows),
            "policy_count": len(specs),
            "best_full_policy": best["policy"],
            "best_full_exact_lengths": best["exact_lengths"],
            "best_full_mean_abs_error": best["mean_abs_error"],
            "best_full_residual_bits": best["signed_gamma_residual_bits"],
            "best_lookup_context": lookup_scores[0]["context"],
            "best_lookup_exact_lengths": lookup_scores[0]["exact_lengths"],
            "best_lookup_context_count": lookup_scores[0]["context_count"],
            "best_lookup_source_bearing": lookup_scores[0]["source_bearing_lookup"],
            "prequential_cells": len(preq),
            "prequential_cover_all_cells": sum(
                1 for row in preq if row["test_exact_lengths"] == row["test_row_count"]
            ),
            "prequential_any_exact_cells": sum(
                1 for row in preq if row["test_exact_lengths"] > 0
            ),
            "prequential_selected_matches_oracle_cells": sum(
                1 for row in preq if row["selected_matches_oracle"]
            ),
            "promotes_book_length_generator": promoted,
            "interpretation": (
                "Simple source-free policies do not generate the length sequence. "
                "Context lookups can memorize lengths only by carrying length "
                "payloads, so they are ledgers rather than generators."
            ),
        },
        "full_fit_policy_scoreboard": [
            {key: value for key, value in row.items() if key != "rows"}
            for row in full_scores
        ],
        "full_fit_context_lookup_scoreboard": lookup_scores,
        "prequential_rows": preq,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": classification,
            "book_length_status": "external_after_generation_gate",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["summary"]
    lines = [
        "# Book Length Generation Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the 70 book lengths are generated by source-free policies",
        "or only compressed as a declared residual ledger.",
        "",
        "## Summary",
        "",
        f"- Book count: `{s['book_count']}`.",
        f"- Policies tested: `{s['policy_count']}`.",
        f"- Best full-fit policy: `{s['best_full_policy']}`.",
        f"- Best full-fit exact lengths: `{s['best_full_exact_lengths']}/{s['book_count']}`.",
        f"- Best full-fit mean abs error: `{s['best_full_mean_abs_error']:.3f}`.",
        f"- Best lookup context: `{s['best_lookup_context']}` with `{s['best_lookup_exact_lengths']}/{s['book_count']}` exact lengths and `{s['best_lookup_context_count']}` length-bearing contexts.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout any-exact cells: `{s['prequential_any_exact_cells']}/{s['prequential_cells']}`.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Exact lengths | Mean abs error | Residual bits |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in result["full_fit_policy_scoreboard"]:
        lines.append(
            f"| `{row['policy']}` | `{row['exact_lengths']}/{row['row_count']}` | "
            f"`{row['mean_abs_error']:.3f}` | `{row['signed_gamma_residual_bits']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected policy | Test exact | Test MAE | Oracle policy |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    for row in result["prequential_rows"]:
        lines.append(
            f"| `{row['cutoff_book']}` | `{row['selected_policy']}` | "
            f"`{row['test_exact_lengths']}/{row['test_row_count']}` | "
            f"`{row['test_mean_abs_error']:.3f}` | `{row['oracle_policy']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes book-length generator: `{s['promotes_book_length_generator']}`.",
            f"- {s['interpretation']}",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
