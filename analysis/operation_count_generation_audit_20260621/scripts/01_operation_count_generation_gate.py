from __future__ import annotations

import importlib.util
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

SKELETON_SCRIPT = (
    ROOT
    / "analysis"
    / "source_free_skeleton_generation_audit_20260621"
    / "scripts"
    / "02_source_free_skeleton_grammar_gate.py"
)
RECURSIVE_GATE = (
    ROOT
    / "analysis"
    / "operation_recursive_partition_audit_20260621"
    / "reports"
    / "test_results"
    / "01_operation_recursive_partition_gate.json"
)

OUT_STEM = "01_operation_count_generation_gate"
PREFIX_CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 1000
RANDOM_SEED = 4692026062103


Row = dict[str, Any]
Predictor = Callable[[Row], int]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def reconstruct() -> dict[int, list[dict[str, Any]]]:
    module = load_module("source_free_skeleton_for_op_count", SKELETON_SCRIPT)
    return module.reconstruct_canonical_skeleton()


def make_rows(by_book: dict[int, list[dict[str, Any]]]) -> list[Row]:
    rows = []
    for book in sorted(by_book):
        lengths = [int(op["length"]) for op in by_book[book]]
        rows.append(
            {
                "book": book,
                "book_length": sum(lengths),
                "op_count": len(lengths),
            }
        )
    return rows


def bucket(value: int) -> str:
    if value <= 80:
        return "le80"
    if value <= 120:
        return "le120"
    if value <= 160:
        return "le160"
    if value <= 220:
        return "le220"
    return "gt220"


def round_count(value: float) -> int:
    return max(1, int(round(value)))


def mode(values: list[int]) -> int:
    counts = Counter(values)
    return min(counts, key=lambda value: (-counts[value], value))


def affine_params(rows: list[Row], x_name: str) -> tuple[float, float]:
    xs = [float(row[x_name]) for row in rows]
    ys = [float(row["op_count"]) for row in rows]
    x_mean = mean(xs)
    y_mean = mean(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return y_mean, 0.0
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
    intercept = y_mean - slope * x_mean
    return intercept, slope


def context_model(rows: list[Row], key_fn: Callable[[Row], str]) -> dict[str, int]:
    groups: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        groups[key_fn(row)].append(int(row["op_count"]))
    return {key: mode(values) for key, values in groups.items()}


def train_models(rows: list[Row]) -> list[dict[str, Any]]:
    values = [int(row["op_count"]) for row in rows]
    models: list[dict[str, Any]] = []

    def add(name: str, predictor: Predictor, parameters: dict[str, Any], payload_records: int) -> None:
        models.append(
            {
                "name": name,
                "predict": predictor,
                "parameters": parameters,
                "payload_records": payload_records,
            }
        )

    global_mode = mode(values)
    global_median = round_count(median(values))
    global_mean = round_count(mean(values))
    add("constant_mode", lambda _row, v=global_mode: v, {"value": global_mode}, 1)
    add("constant_median", lambda _row, v=global_median: v, {"value": global_median}, 1)
    add("constant_mean", lambda _row, v=global_mean: v, {"value": global_mean}, 1)

    for divisor in range(8, 81):
        add(
            f"book_length_round_div_{divisor}",
            lambda row, d=divisor: max(1, int(round(int(row["book_length"]) / d))),
            {"divisor": divisor, "rounding": "round"},
            1,
        )
        add(
            f"book_length_floor_div_{divisor}",
            lambda row, d=divisor: max(1, int(math.floor(int(row["book_length"]) / d))),
            {"divisor": divisor, "rounding": "floor"},
            1,
        )
        add(
            f"book_length_ceil_div_{divisor}",
            lambda row, d=divisor: max(1, int(math.ceil(int(row["book_length"]) / d))),
            {"divisor": divisor, "rounding": "ceil"},
            1,
        )

    for x_name in ["book", "book_length"]:
        intercept, slope = affine_params(rows, x_name)
        add(
            f"affine_{x_name}",
            lambda row, a=intercept, b=slope, x=x_name: round_count(a + b * int(row[x])),
            {"intercept": intercept, "slope": slope, "x": x_name},
            2,
        )

    context_specs: list[tuple[str, Callable[[Row], str]]] = [
        ("book_mod10", lambda row: str(int(row["book"]) % 10)),
        ("book_mod5", lambda row: str(int(row["book"]) % 5)),
        ("book_decade", lambda row: str(int(row["book"]) // 10)),
        ("book_length_bucket", lambda row: bucket(int(row["book_length"]))),
        (
            "book_mod10_x_length_bucket",
            lambda row: f"{int(row['book']) % 10}|{bucket(int(row['book_length']))}",
        ),
    ]
    fallback = global_mode
    for name, key_fn in context_specs:
        mapping = context_model(rows, key_fn)
        add(
            f"context_{name}",
            lambda row, mapping=mapping, key_fn=key_fn, fallback=fallback: mapping.get(
                key_fn(row),
                fallback,
            ),
            {"context_count": len(mapping), "fallback": fallback, "mapping": mapping},
            1 + len(mapping),
        )
    return models


def score_model(rows: list[Row], model: dict[str, Any]) -> dict[str, Any]:
    predictions = []
    exact = 0
    absolute_error = 0
    squared_error = 0
    for row in rows:
        predicted = int(model["predict"](row))
        truth = int(row["op_count"])
        error = predicted - truth
        exact += int(error == 0)
        absolute_error += abs(error)
        squared_error += error * error
        predictions.append(
            {
                "book": int(row["book"]),
                "book_length": int(row["book_length"]),
                "truth": truth,
                "predicted": predicted,
                "error": error,
            }
        )
    correction_records = len(rows) - exact
    paid_records = int(model["payload_records"]) + correction_records
    return {
        "model": model["name"],
        "payload_records": int(model["payload_records"]),
        "book_count": len(rows),
        "exact_books": exact,
        "absolute_error": absolute_error,
        "mean_absolute_error": absolute_error / len(rows) if rows else 0.0,
        "rmse": math.sqrt(squared_error / len(rows)) if rows else 0.0,
        "correction_records": correction_records,
        "paid_records": paid_records,
        "parameters": model["parameters"],
        "predictions": predictions,
    }


def choose_best(scored: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        scored,
        key=lambda item: (
            int(item["exact_books"]),
            -int(item["absolute_error"]),
            -int(item["paid_records"]),
            -int(item["payload_records"]),
            str(item["model"]),
        ),
    )


def random_control(rows: list[Row], values: list[int], *, trials: int, seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    exact_values = []
    ae_values = []
    for _ in range(trials):
        exact = 0
        absolute_error = 0
        for row in rows:
            predicted = rng.choice(values)
            truth = int(row["op_count"])
            exact += int(predicted == truth)
            absolute_error += abs(predicted - truth)
        exact_values.append(exact)
        ae_values.append(absolute_error)
    exact_sorted = sorted(exact_values)
    ae_sorted = sorted(ae_values)
    p95_index = int(0.95 * (trials - 1))
    p05_index = int(0.05 * (trials - 1))
    return {
        "trials": trials,
        "mean_exact_books": mean(exact_values),
        "p95_exact_books": exact_sorted[p95_index],
        "max_exact_books": max(exact_values),
        "mean_absolute_error": mean(ae_values),
        "p05_absolute_error": ae_sorted[p05_index],
        "min_absolute_error": min(ae_values),
    }


def evaluate(rows: list[Row]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    models = train_models(rows)
    scored = [score_model(rows, model) for model in models]
    return scored, choose_best(scored)


def prequential(rows: list[Row]) -> list[dict[str, Any]]:
    cells = []
    for cutoff in PREFIX_CUTOFFS:
        train = [row for row in rows if int(row["book"]) < cutoff]
        test = [row for row in rows if int(row["book"]) >= cutoff]
        train_models_list = train_models(train)
        train_scored = [score_model(train, model) for model in train_models_list]
        best_train = choose_best(train_scored)
        selected_model = next(model for model in train_models_list if model["name"] == best_train["model"])
        test_score = score_model(test, selected_model)
        control = random_control(
            test,
            [int(row["op_count"]) for row in train],
            trials=RANDOM_TRIALS,
            seed=RANDOM_SEED + cutoff * 100003,
        )
        cells.append(
            {
                "cutoff": cutoff,
                "train_books": len(train),
                "test_books": len(test),
                "selected_model": selected_model["name"],
                "train_exact_books": int(best_train["exact_books"]),
                "train_absolute_error": int(best_train["absolute_error"]),
                "test_exact_books": int(test_score["exact_books"]),
                "test_absolute_error": int(test_score["absolute_error"]),
                "test_mean_absolute_error": test_score["mean_absolute_error"],
                "test_random_mean_exact_books": control["mean_exact_books"],
                "test_random_p95_exact_books": control["p95_exact_books"],
                "test_random_max_exact_books": control["max_exact_books"],
                "test_random_mean_absolute_error": control["mean_absolute_error"],
                "beats_random_p95_exact": int(test_score["exact_books"]) > control["p95_exact_books"],
                "beats_random_p05_error": int(test_score["absolute_error"]) < control["p05_absolute_error"],
                "covers_all_test_books": int(test_score["exact_books"]) == len(test),
            }
        )
    return cells


def compact_model(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "predictions"}


def write_markdown(out: Path, data: dict[str, Any]) -> None:
    s = data["summary"]
    top = data["top_models"]
    cells = data["prequential"]
    lines = [
        "# Operation Count Generation Gate",
        "",
        f"Classification: `{data['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the per-book operation count in the source-free skeleton",
        "can be generated from book id and book length, before any cutpoint",
        "or source choice is considered.",
        "",
        "## Summary",
        "",
        f"- Books tested: `{s['book_count']}`.",
        f"- Operation total: `{s['operation_count']}`.",
        f"- Model candidates: `{s['model_count']}`.",
        f"- Best model: `{s['best_model']}`.",
        f"- Best exact books: `{s['best_exact_books']}/{s['book_count']}`.",
        f"- Best absolute error: `{s['best_absolute_error']}`.",
        f"- Best paid records: `{s['best_paid_records']}` vs exact atlas `{s['exact_atlas_records']}`.",
        f"- Paid-record delta vs exact atlas: `{s['paid_record_delta_vs_exact_atlas']:+d}`.",
        f"- Random mean/p95/max exact books: `{s['random_mean_exact_books']:.3f}` / `{s['random_p95_exact_books']}` / `{s['random_max_exact_books']}`.",
        f"- Prefix/holdout cover-all cells: `{s['prequential_cover_all_cells']}/{s['prequential_cells']}`.",
        f"- Prefix/holdout beats-random-p95 exact cells: `{s['prequential_beats_random_p95_exact_cells']}/{s['prequential_cells']}`.",
        "",
        "## Top Models",
        "",
        "| Model | Exact books | Abs error | Paid records | Payload |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in top:
        lines.append(
            "| "
            f"`{item['model']}` | "
            f"`{item['exact_books']}/{item['book_count']}` | "
            f"`{item['absolute_error']}` | "
            f"`{item['paid_records']}` | "
            f"`{item['payload_records']}` |"
        )
    lines.extend(
        [
            "",
            "## Prefix/Holdout",
            "",
            "| Cutoff | Selected model | Test exact | Test abs error | Random mean exact | Random p95 exact | Beats p95 | Cover all |",
            "| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for cell in cells:
        lines.append(
            "| "
            f"`{cell['cutoff']}` | "
            f"`{cell['selected_model']}` | "
            f"`{cell['test_exact_books']}/{cell['test_books']}` | "
            f"`{cell['test_absolute_error']}` | "
            f"`{cell['test_random_mean_exact_books']:.3f}` | "
            f"`{cell['test_random_p95_exact_books']}` | "
            f"`{cell['beats_random_p95_exact']}` | "
            f"`{cell['covers_all_test_books']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Promotes operation-count generator: `{s['promotes_operation_count_generator']}`.",
            f"- Audit-only paid-record reduction: `{s['audit_only_paid_record_reduction']}`.",
            "- The operation-count field remains a retained skeleton dependency unless a later gate derives it jointly with cutpoints.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    recursive = load_json(RECURSIVE_GATE)
    assert_boundary("operation_recursive_partition_gate", recursive)
    rows = make_rows(reconstruct())
    scored, best = evaluate(rows)
    cells = prequential(rows)
    control = random_control(
        rows,
        [int(row["op_count"]) for row in rows],
        trials=RANDOM_TRIALS,
        seed=RANDOM_SEED,
    )
    promotes = (
        int(best["exact_books"]) == len(rows)
        and int(best["paid_records"]) < len(rows)
        and all(cell["covers_all_test_books"] for cell in cells)
    )
    classification = (
        "operation_count_generator_promoted"
        if promotes
        else "operation_count_generator_rejected"
    )
    top = sorted(
        scored,
        key=lambda item: (
            int(item["exact_books"]),
            -int(item["absolute_error"]),
            -int(item["paid_records"]),
            -int(item["payload_records"]),
            str(item["model"]),
        ),
        reverse=True,
    )[:12]
    summary = {
        "book_count": len(rows),
        "operation_count": sum(int(row["op_count"]) for row in rows),
        "model_count": len(scored),
        "best_model": best["model"],
        "best_exact_books": int(best["exact_books"]),
        "best_absolute_error": int(best["absolute_error"]),
        "best_mean_absolute_error": best["mean_absolute_error"],
        "best_paid_records": int(best["paid_records"]),
        "best_payload_records": int(best["payload_records"]),
        "exact_atlas_records": len(rows),
        "random_trials": RANDOM_TRIALS,
        "random_mean_exact_books": control["mean_exact_books"],
        "random_p95_exact_books": control["p95_exact_books"],
        "random_max_exact_books": control["max_exact_books"],
        "prequential_cells": len(cells),
        "prequential_cover_all_cells": sum(1 for cell in cells if cell["covers_all_test_books"]),
        "prequential_beats_random_p95_exact_cells": sum(
            1 for cell in cells if cell["beats_random_p95_exact"]
        ),
        "audit_only_paid_record_reduction": int(best["paid_records"]) < len(rows),
        "paid_record_delta_vs_exact_atlas": int(best["paid_records"]) - len(rows),
        "promotes_operation_count_generator": promotes,
        "interpretation": (
            "Simple source-free models do not generate the per-book operation "
            "count exactly under full-fit and prefix holdout."
        ),
    }
    data = {
        "schema": "operation_count_generation_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_free_skeleton_script": rel(SKELETON_SCRIPT),
            "operation_recursive_partition_gate": rel(RECURSIVE_GATE),
        },
        "parameters": {
            "prefix_cutoffs": PREFIX_CUTOFFS,
            "random_trials": RANDOM_TRIALS,
            "random_seed": RANDOM_SEED,
        },
        "summary": summary,
        "top_models": [compact_model(row) for row in top],
        "best_model_predictions": best["predictions"],
        "prequential": cells,
        "decision": {
            "operation_count_status": "retained_after_simple_generation_gate",
            "operation_length_status": "atlas_retained",
            "row0_origin_status": "unchanged_exogenous",
            "compression_bound_status": "unchanged_8154_676268",
            "translation_or_plaintext_status": "NONE",
        },
    }
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_out = TEST_RESULTS / f"{OUT_STEM}.json"
    md_out = TEST_RESULTS / f"{OUT_STEM}.md"
    json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_out, data)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
